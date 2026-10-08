package com.brasshaven.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.config.BrasshavenClientConfig;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.client.event.RenderLivingEvent;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Health bars floating above creatures (with a yellow "recent damage" trail and a star for elites) and
 * floating damage numbers. Bosses keep their big bar at the bottom of the screen instead.
 */
public final class MobHealthBars {
    private static final float SCALE = 0.025F;
    private static final int BAR_W = 40;
    private static final int FULL_BRIGHT = 0xF000F0;

    /** Per entity id: last seen health, trailing health, tick of last damage, floating numbers. */
    private static final Map<Integer, Track> TRACKS = new HashMap<>();
    /** Some tracked creature has damage numbers floating (lets the NEVER-bars mode skip every other creature). */
    private static boolean anyNumbers;

    private MobHealthBars() {}

    private static final class Track {
        float health;
        float trail;
        long lastHurt = -1000;
        final List<float[]> numbers = new ArrayList<>(); // {amount, ageTicks}
    }

    public static void register() {
        RenderLivingEvent.Post.BUS.addListener(MobHealthBars::onRender);
        TickEvent.ClientTickEvent.Post.BUS.addListener(e -> tick());
    }

    private static void tick() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null || !enabled()) {
            TRACKS.clear();
            anyNumbers = false;
            return;
        }
        long now = mc.level.getGameTime();
        AABB box = mc.player.getBoundingBox().inflate(range());
        Set<Integer> seen = new HashSet<>();
        boolean numbers = false;
        for (LivingEntity e : mc.level.getEntitiesOfClass(LivingEntity.class, box, e -> e != mc.player)) {
            seen.add(e.getId());
            Track t = TRACKS.computeIfAbsent(e.getId(), id -> {
                Track nt = new Track();
                nt.health = e.getHealth();
                nt.trail = e.getHealth();
                return nt;
            });
            float h = e.getHealth();
            if (h < t.health - 0.01F) {
                t.lastHurt = now;
                if (BrasshavenClientConfig.DAMAGE_NUMBERS.get()) {
                    t.numbers.add(new float[] {t.health - h, 0});
                }
            }
            t.health = h;
            // the trail waits a moment, then slides down to the real health
            if (now - t.lastHurt > 10) {
                t.trail = Math.max(h, t.trail - Math.max(0.15F, (t.trail - h) * 0.12F));
            }
            if (t.trail < h) {
                t.trail = h;
            }
            for (Iterator<float[]> it = t.numbers.iterator(); it.hasNext(); ) {
                float[] n = it.next();
                n[1] += 1;
                if (n[1] > 24) {
                    it.remove();
                }
            }
            numbers |= !t.numbers.isEmpty();
        }
        TRACKS.keySet().removeIf(id -> !seen.contains(id));
        anyNumbers = numbers;
    }

    private static boolean enabled() {
        return BrasshavenClientConfig.HEALTH_BARS.get() != BrasshavenClientConfig.HealthBars.NEVER
                || BrasshavenClientConfig.DAMAGE_NUMBERS.get();
    }

    private static int range() {
        return BrasshavenClientConfig.HEALTH_BAR_RANGE.get();
    }

    private static void onRender(RenderLivingEvent.Post<?, ?, ?> event) {
        BrasshavenClientConfig.HealthBars mode = BrasshavenClientConfig.HEALTH_BARS.get();
        LivingEntityRenderState state = event.getState();
        Minecraft mc = Minecraft.getInstance();
        int range = range();
        if (mode == BrasshavenClientConfig.HealthBars.NEVER && (!BrasshavenClientConfig.DAMAGE_NUMBERS.get() || !anyNumbers)
                || mc.level == null || mc.player == null || state.isInvisible || state.distanceToCameraSq > range * range
                || state.entityType == EntityTypes.PLAYER) {
            return; // cheap checks first: finding the entity behind a render state is an entity search
        }
        LivingEntity entity = find(mc, state);
        if (entity == null || entity instanceof Player || entity instanceof WayfarerBoss || !entity.isAlive()
                || entity instanceof net.minecraft.world.entity.decoration.ArmorStand) {
            return;
        }
        Track t = TRACKS.get(entity.getId());
        long now = mc.level.getGameTime();
        boolean hurt = entity.getHealth() < entity.getMaxHealth();
        boolean recent = t != null && now - t.lastHurt < 200;
        boolean aimed = mc.crosshairPickEntity == entity;
        boolean showBar = switch (mode) {
            case ALWAYS -> true;
            case DAMAGED -> recent || aimed || hurt && entity.distanceTo(mc.player) < 12;
            case NEVER -> false;
        };

        PoseStack ps = event.getPoseStack();
        SubmitNodeCollector out = event.getNodeCollector();
        ps.pushPose();
        // above the name tag when the creature has one (they used to be drawn on top of each other)
        ps.translate(0.0F, state.boundingBoxHeight + (state.nameTag != null ? 0.8F : 0.5F), 0.0F);
        ps.mulPose(event.getCameraState().orientation);
        ps.scale(SCALE, -SCALE, SCALE);
        Font font = mc.font;
        if (showBar) {
            float max = Math.max(1F, entity.getMaxHealth());
            float frac = clamp01(entity.getHealth() / max);
            float trail = t == null ? frac : Math.max(frac, clamp01(t.trail / max));
            float half = BAR_W / 2.0F;
            int fill = frac > 0.5F ? 0xFF5BD14A : frac > 0.25F ? 0xFFF2C744 : 0xFFE0483B;
            int shine = frac > 0.5F ? 0xFF9BEA8C : frac > 0.25F ? 0xFFF9DE8A : 0xFFF08A80;
            boolean elite = isElite(entity);
            int frame = elite ? 0xFFF6C343 : 0xFF17120F;
            float fx = -half + BAR_W * frac;
            float tx = -half + BAR_W * trail;
            // Side by side, never on top of each other: the text background render type writes depth and sorts its
            // quads by distance, so stacked layers (the old frame / background / trail / fill at -0.1 .. -0.5) left
            // only the frame visible, the one nearest the camera (+z faces the camera here, Font draws its own
            // background at -0.01 behind the glyphs). One plane, no overlap: no depth fight at any angle or view.
            out.submitCustomGeometry(ps, RenderTypes.textBackground(), (pose, buf) -> {
                // the frame: four strips around the bar
                quad(buf, pose, -half - 1, -1, half + 1, 0, frame);
                quad(buf, pose, -half - 1, 3, half + 1, 4, frame);
                quad(buf, pose, -half - 1, 0, -half, 3, frame);
                quad(buf, pose, half, 0, half + 1, 3, frame);
                // health (a lighter top row), then the yellow trail of recent damage, then the empty part
                quad(buf, pose, -half, 0, fx, 1, shine);
                quad(buf, pose, -half, 1, fx, 3, fill);
                quad(buf, pose, fx, 0, tx, 3, 0xFFF6E27A);
                quad(buf, pose, tx, 0, half, 3, 0xFF2B2320);
            });
            if (elite || aimed) {
                String label = (elite ? "★ " : "") + (int) Math.ceil(entity.getHealth()) + "/" + (int) Math.ceil(max);
                FormattedCharSequence seq = Component.literal(label).getVisualOrderText();
                ps.pushPose();
                ps.scale(0.5F, 0.5F, 0.5F);
                // a dark outline all around (the shadow alone vanished against bright skies and snow)
                out.order(1).submitText(ps, -font.width(seq) / 2.0F, -12, seq, false, Font.DisplayMode.NORMAL, FULL_BRIGHT,
                        elite ? 0xFFF6C343 : 0xFFFFF5DC, 0, 0xFF1A120C);
                ps.popPose();
            }
        }
        if (t != null && !t.numbers.isEmpty() && BrasshavenClientConfig.DAMAGE_NUMBERS.get()) {
            for (float[] n : t.numbers) {
                float age = n[1];
                String s = n[0] >= 10 ? String.valueOf((int) n[0]) : String.format(java.util.Locale.ROOT, "%.1f", n[0]);
                FormattedCharSequence seq = Component.literal(s).getVisualOrderText();
                int alpha = (int) (255 * Math.max(0F, 1F - age / 24F));
                int color = (alpha << 24) | (n[0] >= 8 ? 0xFF8A3D : 0xFFE27A);
                ps.pushPose();
                ps.translate(12 + age * 0.4F, -10 - age * 1.1F, -0.02F);
                out.order(2).submitText(ps, 0, 0, seq, false, Font.DisplayMode.NORMAL, FULL_BRIGHT, color, 0,
                        (alpha << 24) | 0x1A120C);
                ps.popPose();
            }
        }
        ps.popPose();
    }

    private static float clamp01(float v) {
        return v > 0F ? Math.min(1F, v) : 0F; // NaN too
    }

    /** One flat quad in the bar's plane (z 0); nothing when it is empty. Same winding as vanilla's text backgrounds. */
    private static void quad(com.mojang.blaze3d.vertex.VertexConsumer buf, PoseStack.Pose pose, float x0, float y0,
                             float x1, float y1, int color) {
        if (x1 - x0 < 0.01F || y1 - y0 < 0.01F) {
            return;
        }
        buf.addVertex(pose, x0, y0, 0F).setColor(color).setLight(FULL_BRIGHT);
        buf.addVertex(pose, x0, y1, 0F).setColor(color).setLight(FULL_BRIGHT);
        buf.addVertex(pose, x1, y1, 0F).setColor(color).setLight(FULL_BRIGHT);
        buf.addVertex(pose, x1, y0, 0F).setColor(color).setLight(FULL_BRIGHT);
    }

    /** Elites are named "Elite ..." in gold by the server (DangerEvents). */
    private static boolean isElite(LivingEntity e) {
        Component name = e.getCustomName();
        if (name == null) {
            return false;
        }
        TextColor c = name.getStyle().getColor();
        return c != null && c.equals(TextColor.fromLegacyFormat(ChatFormatting.GOLD));
    }

    /** The render state has no entity reference: find the living entity of that type at that spot. */
    private static LivingEntity find(Minecraft mc, LivingEntityRenderState state) {
        Vec3 p = new Vec3(state.x, state.y, state.z);
        LivingEntity best = null;
        double bestD = 1.0;
        for (LivingEntity e : mc.level.getEntitiesOfClass(LivingEntity.class, AABB.ofSize(p, 1.5, 1.5, 1.5),
                e -> e.getType() == state.entityType)) {
            double d = e.position().distanceToSqr(p);
            if (d < bestD) {
                bestD = d;
                best = e;
            }
        }
        return best;
    }
}

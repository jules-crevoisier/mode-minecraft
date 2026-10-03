package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.boss.WayfarerBoss;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.BossHealthOverlay;
import net.minecraft.client.gui.components.LerpingBossEvent;
import net.minecraft.client.sounds.MusicManager;
import net.minecraft.network.chat.contents.TranslatableContents;
import net.minecraft.sounds.Musics;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import org.jetbrains.annotations.Nullable;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Elden Ring style boss bars for Wayfarers bosses: a long thin bar at the bottom of the screen with the name above
 * it, a yellow trail showing recent damage, and the damage dealt in the current flurry. Other bosses (vanilla or
 * other mods) keep the vanilla bar at the top. While a Wayfarers bar is visible, the boss battle music plays.
 */
public final class EldenBossBar {
    private static final String KEY_PREFIX = "entity." + Wayfarers.MODID + ".";
    private static final Map<UUID, Bar> BARS = new HashMap<>();
    private static @Nullable Field eventsField;
    private static boolean fieldResolved;
    private static boolean musicStarted;

    private static final class Bar {
        float progress = 1.0F;
        float trail = 1.0F;
        long lastHit = -1000;
        float damage;
    }

    private EldenBossBar() {}

    public static void register(AddGuiOverlayLayersEvent event) {
        if (field() != null) {
            event.getLayeredDraw().replace(ForgeLayeredDraw.PRE_SLEEP_STACK, ForgeLayeredDraw.BOSS_OVERLAY, EldenBossBar::extract);
        }
    }

    private static @Nullable Field field() {
        if (!fieldResolved) {
            fieldResolved = true;
            try {
                eventsField = ObfuscationReflectionHelper.findField(BossHealthOverlay.class, "events");
            } catch (RuntimeException e) {
                Wayfarers.LOGGER.warn("Wayfarers boss bars disabled: cannot access the boss overlay ({})", e.toString());
                eventsField = null;
            }
        }
        return eventsField;
    }

    @SuppressWarnings("unchecked")
    private static @Nullable Map<UUID, LerpingBossEvent> events(BossHealthOverlay overlay) {
        Field f = field();
        if (f == null) {
            return null;
        }
        try {
            return (Map<UUID, LerpingBossEvent>) f.get(overlay);
        } catch (IllegalAccessException e) {
            return null;
        }
    }

    private static boolean isOurs(LerpingBossEvent event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level != null) {
            Entity e = mc.level.getEntity(event.getId());
            if (e instanceof WayfarerBoss) {
                return true;
            }
        }
        return event.getName().getContents() instanceof TranslatableContents tc && tc.getKey().startsWith(KEY_PREFIX);
    }

    private static List<LerpingBossEvent> ours(Map<UUID, LerpingBossEvent> events) {
        List<LerpingBossEvent> list = new ArrayList<>();
        for (LerpingBossEvent e : events.values()) {
            if (isOurs(e)) {
                list.add(e);
            }
        }
        return list;
    }

    /** Layer: vanilla bars for everyone else, then our bars at the bottom. */
    private static void extract(GuiGraphicsExtractor gg, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        BossHealthOverlay overlay = mc.gui.hud.getBossOverlay();
        Map<UUID, LerpingBossEvent> events = events(overlay);
        if (events == null) {
            overlay.extractRenderState(gg);
            return;
        }
        List<LerpingBossEvent> mine = ours(events);
        if (mine.isEmpty()) {
            overlay.extractRenderState(gg);
            return;
        }
        Map<UUID, LerpingBossEvent> saved = new LinkedHashMap<>(events);
        for (LerpingBossEvent e : mine) {
            events.remove(e.getId());
        }
        try {
            overlay.extractRenderState(gg);
        } finally {
            events.clear();
            events.putAll(saved);
        }
        drawBars(gg, mc, mine);
    }

    private static void drawBars(GuiGraphicsExtractor gg, Minecraft mc, List<LerpingBossEvent> mine) {
        Font font = mc.font;
        int width = gg.guiWidth();
        int barW = Math.min(360, (int) (width * 0.62F));
        int x = (width - barW) / 2;
        int y = gg.guiHeight() - 64;
        long now = mc.level == null ? 0 : mc.level.getGameTime();
        for (LerpingBossEvent event : mine) {
            Bar bar = BARS.computeIfAbsent(event.getId(), id -> new Bar());
            float progress = Math.max(0.0F, Math.min(1.0F, event.getProgress()));
            int fill = Math.round(barW * progress);
            int trail = Math.round(barW * Math.max(progress, bar.trail));
            // frame: dark shadow box, thin gold rules above and below
            gg.fill(x - 3, y - 3, x + barW + 3, y + 8, 0xB0000000);
            gg.horizontalLine(x - 3, x + barW + 2, y - 3, 0xFF6E5A30);
            gg.horizontalLine(x - 3, x + barW + 2, y + 7, 0xFF6E5A30);
            gg.fill(x, y, x + barW, y + 5, 0xFF2A0B09);
            if (trail > fill) {
                gg.fill(x + fill, y, x + trail, y + 5, 0xFFD8A63A);
            }
            if (fill > 0) {
                gg.fillGradient(x, y, x + fill, y + 5, 0xFFC2281E, 0xFF6A0E0B);
                gg.horizontalLine(x, x + fill - 1, y, 0xFFE0473A);
            }
            gg.text(font, event.getName(), x, y - 12, 0xFFF2EAD8, true);
            if (bar.damage >= 1.0F && now - bar.lastHit < 70) {
                String dmg = Integer.toString(Math.round(bar.damage));
                gg.text(font, dmg, x + barW - font.width(dmg), y - 12, 0xFFF2EAD8, true);
            }
            y -= 26;
        }
    }

    /** Client tick: damage trail, damage counter, boss music. */
    public static void tick() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.gui == null) {
            BARS.clear();
            stopMusic(mc);
            return;
        }
        Map<UUID, LerpingBossEvent> events = events(mc.gui.hud.getBossOverlay());
        List<LerpingBossEvent> mine = events == null ? List.of() : ours(events);
        long now = mc.level.getGameTime();
        Map<UUID, Bar> alive = new HashMap<>();
        for (LerpingBossEvent event : mine) {
            Bar bar = BARS.computeIfAbsent(event.getId(), id -> new Bar());
            float p = event.getProgress();
            if (p < bar.progress - 1.0E-4F) {
                Entity e = mc.level.getEntity(event.getId());
                float max = e instanceof WayfarerBoss boss ? boss.getMaxHealth() : 100.0F;
                if (now - bar.lastHit > 70) {
                    bar.damage = 0;
                }
                bar.damage += (bar.progress - p) * max;
                bar.lastHit = now;
            } else if (p > bar.progress + 1.0E-4F) {
                bar.trail = p;
                bar.damage = 0;
            }
            bar.progress = p;
            if (now - bar.lastHit > 18) {
                bar.trail = Math.max(p, bar.trail - 0.012F);
            }
            alive.put(event.getId(), bar);
        }
        BARS.clear();
        BARS.putAll(alive);
        if (!mine.isEmpty()) {
            MusicManager music = mc.getMusicManager();
            if (!music.isPlayingMusic(Musics.END_BOSS)) {
                music.startPlaying(Musics.END_BOSS);
            }
            musicStarted = true;
        } else {
            stopMusic(mc);
        }
    }

    private static void stopMusic(Minecraft mc) {
        if (musicStarted) {
            musicStarted = false;
            mc.getMusicManager().stopPlaying(Musics.END_BOSS);
        }
    }
}

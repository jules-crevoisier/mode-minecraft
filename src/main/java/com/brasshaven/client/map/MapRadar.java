package com.brasshaven.client.map;

import com.brasshaven.Brasshaven;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.config.BrasshavenClientConfig;
import com.brasshaven.entity.BossZombie;
import com.brasshaven.entity.WayfarerNpc;
import com.brasshaven.entity.ocean.SeaSerpent;
import com.mojang.logging.LogUtils;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.NeutralMob;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Npc;
import net.minecraft.world.level.Level;
import org.slf4j.Logger;

import java.util.Arrays;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;

/**
 * The entity radar of the maps (like the minimap mods' radars): creatures around the player as small icons, read from
 * the client's own level, so nothing is sent over the network (players come from {@link ClientMap#markers()}).
 *
 * <p>Cheap by design: the level is scanned at most five times a second (one pass, no sorting), keeping the
 * {@value #CAP} nearest within the reach the maps asked for; the icons then follow the creatures smoothly every frame
 * from the kept references. The kinds are worked out once per entity class. Icons: a dot coloured by kind (hostile
 * red, animals green, neutral yellow, NPCs a villager badge, bosses a crowned skull, items grey), or the creature's
 * face cut from its own texture for the common vanilla creatures (adults; the others keep their dot). A creature well
 * above or below gets a small up / down tick and fades a little.
 */
public final class MapRadar {
    private static final Logger LOGGER = LogUtils.getLogger();
    /** Kinds, in drawing order (bosses on top). */
    public static final byte PASSIVE = 0;
    public static final byte NEUTRAL = 1;
    public static final byte ITEM = 2;
    public static final byte NPC = 3;
    public static final byte HOSTILE = 4;
    public static final byte BOSS = 5;
    private static final int KINDS = 6;
    private static final byte IGNORED = -1;
    /** Dot colours per kind (the dot sprite is white with a dark rim). */
    static final int[] COLORS = {0xFF7CE35A, 0xFFF6C343, 0xFFB9B2A6, 0xFFE8D7AE, 0xFFE0483B, 0xFFB46CFF};
    private static final int CAP = 160;
    private static final long SCAN_NS = 200_000_000L;
    /** The client only knows the creatures it tracks anyway: never look further than this. */
    private static final double MAX_REACH = 160.0;
    /** Height difference (blocks) from which an icon gets its up / down tick. */
    private static final double TIER = 6.0;
    private static final Identifier DOT = Brasshaven.id("map/radar/dot");
    private static final Identifier BOSS_ICON = Brasshaven.id("map/radar/boss");
    private static final Identifier NPC_ICON = Brasshaven.id("map/radar/npc");

    private static final Entity[] FOUND = new Entity[CAP];
    private static final byte[] KIND = new byte[CAP];
    private static final double[] DIST = new double[CAP];
    /** Indices of FOUND in drawing order (counting sort by kind). */
    private static final int[] ORDER = new int[CAP];
    private static final int[] BUCKET = new int[KINDS + 1];
    private static int count;
    private static long lastScan;
    private static double wanted;
    private static Level scanned;
    /** Faces rather than dots (the setting, read once per frame by {@link #update()}). */
    private static boolean heads = true;
    private static final Map<Class<?>, Byte> KIND_OF = new IdentityHashMap<>();
    private static final Map<EntityType<?>, Face> FACES = new IdentityHashMap<>();
    private static final Face NO_FACE = new Face(null, 0, 0, 0, 0, 0, 0);
    private static Map<EntityType<?>, float[]> faceUv;

    /** A face cut from an entity texture: region (u, v, w, h) of a texW x texH texture. */
    private record Face(Identifier tex, float u, float v, int w, int h, int texW, int texH) {}

    private MapRadar() {}

    // ------------------------------------------------------------------ scanning
    /** Asks for the creatures within {@code reach} blocks of the player (several maps: the largest wins). */
    static void want(double reach) {
        wanted = Math.max(wanted, Math.min(MAX_REACH, reach));
    }

    /** Scans the level again when the last scan is older than 200 ms. Call once per frame before drawing. */
    static void update() {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer player = mc.player;
        heads = BrasshavenClientConfig.RADAR_ICONS.get() == BrasshavenClientConfig.RadarIcons.HEADS;
        if (mc.level != scanned) {
            Arrays.fill(FOUND, null);
            count = 0;
            scanned = mc.level;
            lastScan = 0;
        }
        long now = System.nanoTime();
        if (player == null || mc.level == null || now - lastScan < SCAN_NS) {
            return;
        }
        lastScan = now;
        double reach = Math.max(16.0, wanted);
        wanted = 0;
        boolean hostile = BrasshavenClientConfig.RADAR_HOSTILE.get();
        boolean passive = BrasshavenClientConfig.RADAR_PASSIVE.get();
        boolean npcs = BrasshavenClientConfig.RADAR_NPCS.get();
        boolean items = BrasshavenClientConfig.RADAR_ITEMS.get();
        double px = player.getX();
        double pz = player.getZ();
        double r2 = reach * reach;
        int n = 0;
        int far = -1; // when full: the farthest kept, replaced by anything nearer
        for (Entity e : mc.level.entitiesForRendering()) {
            if (e == player || e.isRemoved() || e.isInvisible()) {
                continue;
            }
            byte kind = kindOf(e);
            boolean show = switch (kind) {
                case HOSTILE -> hostile;
                case PASSIVE, NEUTRAL -> passive;
                case NPC -> npcs;
                case ITEM -> items;
                case BOSS -> true;
                default -> false;
            };
            if (!show) {
                continue;
            }
            double dx = e.getX() - px;
            double dz = e.getZ() - pz;
            double d = dx * dx + dz * dz;
            if (d > r2) {
                continue;
            }
            int slot;
            if (n < CAP) {
                slot = n++;
            } else {
                if (far < 0) {
                    far = farthest(n);
                }
                if (d >= DIST[far]) {
                    continue;
                }
                slot = far;
                far = -1;
            }
            FOUND[slot] = e;
            KIND[slot] = kind;
            DIST[slot] = d;
        }
        if (n < count) {
            Arrays.fill(FOUND, n, count, null); // let go of the creatures no longer kept
        }
        count = n;
        // drawing order: by kind (passive first, bosses last), no sort
        Arrays.fill(BUCKET, 0);
        for (int i = 0; i < n; i++) {
            BUCKET[KIND[i] + 1]++;
        }
        for (int k = 1; k <= KINDS; k++) {
            BUCKET[k] += BUCKET[k - 1];
        }
        for (int i = 0; i < n; i++) {
            ORDER[BUCKET[KIND[i]]++] = i;
        }
    }

    private static int farthest(int n) {
        int best = 0;
        for (int i = 1; i < n; i++) {
            if (DIST[i] > DIST[best]) {
                best = i;
            }
        }
        return best;
    }

    /** Number of creatures kept by the last scan. */
    public static int count() {
        return count;
    }

    /** The k-th creature in drawing order (may have been removed since the scan: check {@link Entity#isRemoved()}). */
    static Entity entity(int k) {
        return FOUND[ORDER[k]];
    }

    static byte kind(int k) {
        return KIND[ORDER[k]];
    }

    /** What an entity is on the radar (worked out once per class); IGNORED for players, armour stands, projectiles... */
    static byte kindOf(Entity e) {
        Byte cached = KIND_OF.get(e.getClass());
        if (cached == null) {
            cached = classify(e);
            KIND_OF.put(e.getClass(), cached);
        }
        byte k = cached;
        // a neutral creature that is angry (attacking) shows as hostile
        if (k == NEUTRAL && e instanceof Mob m && m.isAggressive()) {
            return HOSTILE;
        }
        return k;
    }

    private static byte classify(Entity e) {
        if (e instanceof ItemEntity) {
            return ITEM;
        }
        if (!(e instanceof Mob)) {
            return IGNORED;
        }
        if (e instanceof WayfarerBoss || e instanceof SeaSerpent || e instanceof BossZombie || e instanceof EnderDragon
                || e instanceof WitherBoss) {
            return BOSS;
        }
        if (e instanceof Npc || e instanceof WayfarerNpc) {
            return NPC;
        }
        if (e instanceof NeutralMob) {
            return NEUTRAL;
        }
        return e instanceof Enemy ? HOSTILE : PASSIVE;
    }

    // ------------------------------------------------------------------ drawing
    /** Icon size (GUI px) next to the map's marker size: a little smaller, so markers stay readable on top. */
    static float iconSize(float markerSize) {
        return Math.max(4.0F, markerSize * 0.8F);
    }

    /** Interpolated position of a creature for this frame. */
    static double x(Entity e, float pt) {
        return Mth.lerp(pt, e.xo, e.getX());
    }

    static double y(Entity e, float pt) {
        return Mth.lerp(pt, e.yo, e.getY());
    }

    static double z(Entity e, float pt) {
        return Mth.lerp(pt, e.zo, e.getZ());
    }

    /**
     * One radar icon centred on (x, y), about {@code size} GUI px wide, drawn at the screen's own resolution so it is
     * crisp at every size and GUI scale. {@code dy}: the creature's height above the player (negative: below).
     */
    static void icon(GuiGraphicsExtractor g, Entity e, byte kind, float x, float y, float size, double dy) {
        boolean tier = Math.abs(dy) >= TIER;
        int alpha = tier ? 0xA8 : 0xFF;
        if (kind == BOSS) {
            MapRenderer.spriteCrisp(g, BOSS_ICON, 9, x, y, size * 1.2F, alpha << 24 | 0xFFFFFF, true);
        } else if (!(heads && face(g, e, kind, x, y, size, alpha))) {
            if (kind == NPC) {
                MapRenderer.spriteCrisp(g, NPC_ICON, 9, x, y, size, alpha << 24 | 0xFFFFFF, true);
            } else {
                float dot = kind == ITEM ? size * 0.5F : size * 0.72F;
                MapRenderer.spriteCrisp(g, DOT, 7, x, y, dot, alpha << 24 | (COLORS[kind] & 0xFFFFFF), false);
            }
        }
        if (tier) {
            caret(g, x, y + (dy > 0 ? -size * 0.5F - 1.5F : size * 0.5F + 1.5F), dy > 0);
        }
    }

    /** A tiny up (above) or down (below) tick: a 3-row cream triangle with a dark rim. */
    private static void caret(GuiGraphicsExtractor g, float x, float y, boolean up) {
        int gs = MapRenderer.guiScale();
        int k = Math.max(1, (gs * 2 + 1) / 3);
        g.pose().pushMatrix();
        g.pose().translate(Math.round(x * gs) / (float) gs, Math.round(y * gs) / (float) gs);
        g.pose().scale(1.0F / gs, 1.0F / gs);
        for (int row = 0; row < 3; row++) {
            int half = ((up ? row : 2 - row) + 1) * k;
            int ry = (row - 1) * k;
            g.fill(-half - k, ry - k, half + k, ry + 2 * k, 0xFF100C0A);
        }
        for (int row = 0; row < 3; row++) {
            int half = ((up ? row : 2 - row) + 1) * k;
            int ry = (row - 1) * k;
            g.fill(-half, ry, half, ry + k, 0xFFFFF4DC);
        }
        g.pose().popMatrix();
    }

    /** Draws the creature's face with a rim of its kind's colour; false when no face is known for it. */
    private static boolean face(GuiGraphicsExtractor g, Entity e, byte kind, float x, float y, float size, int alpha) {
        Face f = faceOf(e);
        if (f == null || f == NO_FACE) {
            return false;
        }
        int gs = MapRenderer.guiScale();
        int k = Math.max(1, Math.round(size * gs / Math.max(f.w(), f.h())));
        int w = f.w() * k;
        int h = f.h() * k;
        int rim = Math.max(1, gs / 2);
        int x0 = -w / 2;
        int y0 = -h / 2;
        g.pose().pushMatrix();
        g.pose().translate(Math.round(x * gs) / (float) gs, Math.round(y * gs) / (float) gs);
        g.pose().scale(1.0F / gs, 1.0F / gs);
        g.fill(x0, y0, x0 + w + rim * 2, y0 + h + rim * 2, (alpha * 0x50 / 255) << 24); // soft shadow
        g.fill(x0 - rim, y0 - rim, x0 + w + rim, y0 + h + rim, alpha << 24 | (COLORS[kind] & 0xFFFFFF));
        g.blit(RenderPipelines.GUI_TEXTURED, f.tex(), x0, y0, f.u(), f.v(), w, h, f.w(), f.h(), f.texW(), f.texH(),
                alpha << 24 | 0xFFFFFF);
        g.pose().popMatrix();
        return true;
    }

    /**
     * The face of this creature's kind: its texture from its renderer (asked once per type, from an adult: the
     * babies have their own models), cut where the front of the head is for that model. Null when not known yet,
     * NO_FACE when the type has none.
     */
    private static Face faceOf(Entity e) {
        EntityType<?> type = e.getType();
        Face f = FACES.get(type);
        if (f != null) {
            return f;
        }
        float[] uv = uvTable().get(type);
        if (uv == null || !(e instanceof LivingEntity living)) {
            FACES.put(type, NO_FACE);
            return NO_FACE;
        }
        if (living.isBaby()) {
            return null; // wait for an adult of this kind
        }
        try {
            EntityRenderer<? super Entity, ?> renderer = Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(e);
            Face face = NO_FACE;
            if (renderer instanceof LivingEntityRenderer<?, ?, ?> lr) {
                EntityRenderState state = renderer.createRenderState(e, 1.0F);
                @SuppressWarnings({"unchecked", "rawtypes"})
                Identifier tex = ((LivingEntityRenderer) lr).getTextureLocation((LivingEntityRenderState) state);
                if (tex != null) {
                    face = new Face(tex, uv[0], uv[1], (int) uv[2], (int) uv[3], (int) uv[4], (int) uv[5]);
                }
            }
            FACES.put(type, face);
            return face;
        } catch (RuntimeException | LinkageError ex) {
            LOGGER.debug("Brasshaven radar: no face for {}: {}", type, ex.toString());
            FACES.put(type, NO_FACE);
            return NO_FACE;
        }
    }

    /**
     * Front of the head (u, v, w, h) and texture size for the common vanilla creatures, from their 26.2 models: a box
     * at texture offset (U, V) of size (W, H, D) has its front face at (U + D, V + D), W x H.
     */
    private static Map<EntityType<?>, float[]> uvTable() {
        if (faceUv == null) {
            Map<EntityType<?>, float[]> m = new HashMap<>();
            float[] humanoid64 = {8, 8, 8, 8, 64, 64};
            float[] humanoid32 = {8, 8, 8, 8, 64, 32};
            float[] villager = {8, 8, 8, 10, 64, 64};
            for (EntityType<?> t : new EntityType<?>[] {EntityTypes.ZOMBIE, EntityTypes.HUSK, EntityTypes.DROWNED}) {
                m.put(t, humanoid64);
            }
            for (EntityType<?> t : new EntityType<?>[] {EntityTypes.SKELETON, EntityTypes.STRAY, EntityTypes.WITHER_SKELETON,
                    EntityTypes.BOGGED, EntityTypes.CREEPER, EntityTypes.ENDERMAN, EntityTypes.BLAZE, EntityTypes.SLIME}) {
                m.put(t, humanoid32);
            }
            for (EntityType<?> t : new EntityType<?>[] {EntityTypes.VILLAGER, EntityTypes.WANDERING_TRADER, EntityTypes.ZOMBIE_VILLAGER,
                    EntityTypes.PILLAGER, EntityTypes.VINDICATOR, EntityTypes.EVOKER, EntityTypes.ILLUSIONER}) {
                m.put(t, villager);
            }
            m.put(EntityTypes.WITCH, new float[] {8, 8, 8, 10, 64, 128});
            m.put(EntityTypes.IRON_GOLEM, new float[] {8, 8, 8, 10, 128, 128});
            m.put(EntityTypes.SPIDER, new float[] {40, 12, 8, 8, 64, 32});
            m.put(EntityTypes.CAVE_SPIDER, new float[] {40, 12, 8, 8, 64, 32});
            m.put(EntityTypes.PIGLIN, new float[] {8, 8, 10, 8, 64, 64});
            m.put(EntityTypes.PIGLIN_BRUTE, new float[] {8, 8, 10, 8, 64, 64});
            m.put(EntityTypes.ZOMBIFIED_PIGLIN, new float[] {8, 8, 10, 8, 64, 64});
            m.put(EntityTypes.COW, new float[] {6, 6, 8, 8, 64, 64});
            m.put(EntityTypes.PIG, new float[] {8, 8, 8, 8, 64, 64});
            m.put(EntityTypes.SHEEP, new float[] {8, 8, 6, 6, 64, 32});
            m.put(EntityTypes.CHICKEN, new float[] {3, 3, 4, 6, 64, 32});
            m.put(EntityTypes.WOLF, new float[] {4, 4, 6, 6, 64, 32});
            m.put(EntityTypes.FOX, new float[] {7, 11, 8, 6, 48, 32});
            m.put(EntityTypes.RABBIT, new float[] {5, 21, 5, 5, 64, 64});
            faceUv = m;
        }
        return faceUv;
    }
}

package com.brasshaven.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** config/brasshaven-client.toml — per-player display preferences. */
public final class BrasshavenClientConfig {
    public enum HealthBars { ALWAYS, DAMAGED, NEVER }
    public enum Corner { TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT }
    /**
     * Minimap presets, by their size on screen in GUI pixels, frame included (the map inside is 12 px less). The size
     * itself is {@link #MINIMAP_PIXELS}; a preset only sets it (and old configs that only have a preset keep it).
     */
    public enum MinimapSize {
        SMALL(56), MEDIUM(68), LARGE(96), XLARGE(128);

        public final int outer;

        MinimapSize(int outer) {
            this.outer = outer;
        }
    }
    public enum MinimapShape { ROUND, SQUARE }
    /** Hill-shading of the maps: FLAT (plain colours), NORMAL, STRONG. */
    public enum MapRelief { FLAT, NORMAL, STRONG }
    /** Entity radar icons: HEADS (the creature's face when known, else a dot) or DOTS (coloured by kind). */
    public enum RadarIcons { HEADS, DOTS }

    /** Range of the minimap's exact size (GUI pixels, frame included) and the step of its slider. */
    public static final int MINIMAP_MIN = 48;
    public static final int MINIMAP_MAX = 160;
    public static final int MINIMAP_STEP = 4;

    private static final ForgeConfigSpec.Builder B = new ForgeConfigSpec.Builder();

    public static final ForgeConfigSpec.ConfigValue<String> TRACKED_QUEST = B
            .comment("Quest shown in the on-screen tracker (set from the quest journal).")
            .define("quests.tracked", "");
    public static final ForgeConfigSpec.BooleanValue QUEST_TRACKER = B
            .comment("Show the tracked quest in the top-right corner of the screen.")
            .define("quests.showTracker", true);
    public static final ForgeConfigSpec.EnumValue<HealthBars> HEALTH_BARS = B
            .comment("Health bars above creatures: ALWAYS, DAMAGED (hurt or targeted) or NEVER.")
            .defineEnum("hud.healthBars", HealthBars.DAMAGED);
    public static final ForgeConfigSpec.IntValue HEALTH_BAR_RANGE = B
            .comment("Health bars and damage numbers are drawn for creatures up to this many blocks away.",
                    "Lower it to save frames in crowded places (mob farms, big fights).")
            .defineInRange("hud.healthBarRange", 24, 4, 64);
    public static final ForgeConfigSpec.BooleanValue DAMAGE_NUMBERS = B
            .comment("Floating damage numbers when you hit a creature.")
            .define("hud.damageNumbers", true);
    public static final ForgeConfigSpec.BooleanValue TIPS = B
            .comment("One-time tips that explain a system the first time you meet it.")
            .define("hud.tips", true);

    public static final ForgeConfigSpec.BooleanValue MINIMAP = B
            .comment("Show the minimap (toggle in game with H; Shift + H changes its size).")
            .define("map.minimap", true);
    public static final ForgeConfigSpec.EnumValue<Corner> MINIMAP_CORNER = B
            .comment("Screen corner of the minimap: TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT or BOTTOM_RIGHT.")
            .defineEnum("map.corner", Corner.TOP_LEFT);
    public static final ForgeConfigSpec.EnumValue<MinimapSize> MINIMAP_SIZE = B
            .comment("Minimap size on screen, frame included: SMALL (56 px), MEDIUM (68 px), LARGE (96 px) or XLARGE (128 px).",
                    "Cycle it in game with Shift + H, or in the mod's settings (Mods > Brasshaven > Config).")
            .defineEnum("map.size", MinimapSize.MEDIUM);
    public static final ForgeConfigSpec.IntValue MINIMAP_PIXELS = B
            .comment("Exact minimap size on screen in GUI pixels, frame included, from 48 to 160 (0: the map.size preset).",
                    "Set it in game with the size slider of the world map's options (M, then the gear button).")
            .defineInRange("map.sizePixels", 0, 0, 160);
    public static final ForgeConfigSpec.EnumValue<MinimapShape> MINIMAP_SHAPE = B
            .comment("Minimap shape: ROUND (brass porthole) or SQUARE.")
            .defineEnum("map.shape", MinimapShape.ROUND);
    public static final ForgeConfigSpec.BooleanValue MINIMAP_ROTATE = B
            .comment("Turn the minimap with you (your facing is always up). Off: north is always up.")
            .define("map.rotate", false);
    public static final ForgeConfigSpec.IntValue MINIMAP_ZOOM = B
            .comment("Minimap zoom level, 0 (widest) to 3 (closest). Cycle it in game with Z.")
            .defineInRange("map.zoom", 1, 0, 3);
    public static final ForgeConfigSpec.BooleanValue MINIMAP_COORDS = B
            .comment("Show your coordinates and the biome under the minimap.")
            .define("map.showCoordinates", true);
    public static final ForgeConfigSpec.IntValue MINIMAP_OPACITY = B
            .comment("Opacity of the minimap's terrain, in percent (lower it to see the world through the map).")
            .defineInRange("map.opacity", 100, 30, 100);
    public static final ForgeConfigSpec.EnumValue<MapRelief> MAP_RELIEF = B
            .comment("Relief on the maps, shaded from the explored heights (light from the north-west, darker valleys):",
                    "FLAT (plain colours), NORMAL or STRONG.")
            .defineEnum("map.relief", MapRelief.NORMAL);
    public static final ForgeConfigSpec.BooleanValue MAP_CONTOURS = B
            .comment("Thin contour lines every 16 blocks of height on the maps (a bolder one every 64).")
            .define("map.contours", false);
    public static final ForgeConfigSpec.BooleanValue MAP_3D = B
            .comment("The world map opens in its tilted 3D view (relief raised from the explored heights) instead of seen from above.")
            .define("map.worldMap3d", false);
    public static final ForgeConfigSpec.BooleanValue CAVE_MAP = B
            .comment("Underground, map the cave around you (a slice at your height) instead of the surface far above.")
            .define("map.caveMode", true);
    public static final ForgeConfigSpec.BooleanValue MAP_PLAYERS = B
            .comment("Show other players on the maps: the ones the server shares (its own map.showPlayers) and those near enough",
                    "for your client to see them. Their head, and on the minimap an arrow on its edge for those further away.")
            .define("map.showPlayers", true);
    public static final ForgeConfigSpec.BooleanValue RADAR = B
            .comment("Entity radar: creatures around you as small icons on the minimap (and on the world map zoomed in near you).",
                    "Client side only: it shows what your game already knows, nothing more is sent by the server.")
            .define("map.radar", true);
    public static final ForgeConfigSpec.EnumValue<RadarIcons> RADAR_ICONS = B
            .comment("Radar icons: HEADS (the creature's face when it is known, else a dot) or DOTS (coloured by kind).")
            .defineEnum("map.radarIcons", RadarIcons.HEADS);
    public static final ForgeConfigSpec.BooleanValue RADAR_HOSTILE = B
            .comment("Radar: hostile creatures (red). Bosses always show while the radar is on.")
            .define("map.radarHostile", true);
    public static final ForgeConfigSpec.BooleanValue RADAR_PASSIVE = B
            .comment("Radar: animals (green) and neutral creatures (yellow, red once angry).")
            .define("map.radarPassive", true);
    public static final ForgeConfigSpec.BooleanValue RADAR_NPCS = B
            .comment("Radar: villagers, wandering traders and the mod's NPCs.")
            .define("map.radarNpcs", true);
    public static final ForgeConfigSpec.BooleanValue RADAR_ITEMS = B
            .comment("Radar: items lying on the ground (small grey dots).")
            .define("map.radarItems", false);

    public static final ForgeConfigSpec.BooleanValue RECIPE_VIEWER = B
            .comment("Built-in recipe viewer: in any inventory, R over an item shows its recipes and U its uses (keys rebindable).")
            .define("recipes.enabled", true);
    public static final ForgeConfigSpec.BooleanValue RECIPE_PANEL = B
            .comment("The item list beside inventories, crafting tables, furnaces... (show / hide it in game with I).")
            .define("recipes.panel", true);
    public static final ForgeConfigSpec.BooleanValue RECIPE_MOD_ONLY = B
            .comment("The item list shows only Brasshaven items (its filter button). Off: Brasshaven items first, then every other.")
            .define("recipes.modItemsOnly", false);
    public static final ForgeConfigSpec.BooleanValue RECIPE_WITH_JEI = B
            .comment("When JEI is installed the built-in viewer steps aside (no item list, no R / U keys of its own).",
                    "Set to true to keep both.")
            .define("recipes.alongsideJei", false);

    public static final ForgeConfigSpec.BooleanValue UPDATE_CHECK = B
            .comment("Look for a newer Brasshaven release (GitHub, in the background) and show a notice with the changelog link.",
                    "Nothing is ever downloaded.")
            .define("updates.checkForUpdates", true);

    public static final ForgeConfigSpec SPEC = B.build();

    private BrasshavenClientConfig() {}

    /** The minimap's size on screen (GUI pixels, frame included): the exact size if set, else the preset's. */
    public static int minimapPixels() {
        int px = MINIMAP_PIXELS.get();
        return Math.max(MINIMAP_MIN, Math.min(MINIMAP_MAX, px > 0 ? px : MINIMAP_SIZE.get().outer));
    }

    /** Sets the exact size (snapped to the slider's steps) and the preset it equals, if any; saved at once. */
    public static void setMinimapPixels(int px) {
        int v = Math.max(MINIMAP_MIN, Math.min(MINIMAP_MAX, px));
        MINIMAP_PIXELS.set(v);
        MINIMAP_PIXELS.save();
        for (MinimapSize s : MinimapSize.values()) {
            if (s.outer == v && MINIMAP_SIZE.get() != s) {
                MINIMAP_SIZE.set(s);
                MINIMAP_SIZE.save();
            }
        }
    }
}

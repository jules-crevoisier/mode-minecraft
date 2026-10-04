package com.wayfarers.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** config/wayfarers-client.toml — per-player display preferences. */
public final class WayfarersClientConfig {
    public enum HealthBars { ALWAYS, DAMAGED, NEVER }
    public enum Corner { TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT }
    /** Minimap presets, by their size on screen in GUI pixels, frame included (the map inside is 12 px less). */
    public enum MinimapSize {
        SMALL(56), MEDIUM(68), LARGE(96), XLARGE(128);

        public final int outer;

        MinimapSize(int outer) {
            this.outer = outer;
        }
    }
    public enum MinimapShape { ROUND, SQUARE }

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
                    "Cycle it in game with Shift + H, or in the mod's settings (Mods > Wayfarers > Config).")
            .defineEnum("map.size", MinimapSize.MEDIUM);
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
    public static final ForgeConfigSpec.BooleanValue CAVE_MAP = B
            .comment("Underground, map the cave around you (a slice at your height) instead of the surface far above.")
            .define("map.caveMode", true);
    public static final ForgeConfigSpec.BooleanValue MAP_PLAYERS = B
            .comment("Show other players on the maps (only those your client can see, within view distance).")
            .define("map.showPlayers", true);

    public static final ForgeConfigSpec SPEC = B.build();

    private WayfarersClientConfig() {}
}

package com.wayfarers.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** config/wayfarers-common.toml — every difficulty knob can be tuned or switched off by the server owner. */
public final class WayfarersConfig {
    private static final ForgeConfigSpec.Builder B = new ForgeConfigSpec.Builder();

    public static final ForgeConfigSpec.BooleanValue STRUCTURE_FIT = B
            .comment("Wayfarers structures only start where the terrain suits them: flat enough dry ground for buildings,",
                    "a shore for the lighthouse, open sea floor for wrecks, clear sky under floating isles. A site that does not",
                    "fit is skipped like one with the wrong biome (/locate looks further). False: build wherever the grid says.")
            .define("world.structureFit", true);
    public static final ForgeConfigSpec.BooleanValue CUSTOM_BIOMES = B
            .comment("New worlds get the Wayfarers biomes: Crimson Mire (in the wettest swamps), Volcanic Highlands (in",
                    "badlands mountains) and Pale Dunes (in the driest deserts). Minecraft's terrain is kept: a built-in data",
                    "pack (\"wayfarers:custom_biomes\") only hands these climate slices to the new biomes. Minecraft shows its",
                    "\"experimental settings\" warning when a world is created with it; that is expected. False: new worlds",
                    "keep the vanilla biomes (the pack stays available, unticked, in the Data Packs screen). Existing worlds",
                    "keep whatever they were created with.")
            .define("world.customBiomes", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_BOULDERS = B
            .comment("Terrain touches in vanilla biomes (read when the server starts; new chunks only). Mossy boulders in",
                    "plains, meadows, forests, taigas and windswept hills.")
            .define("world.terrain.boulders", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_FALLEN_LOGS = B
            .comment("Fallen logs in dark forests, savannas and cherry groves.")
            .define("world.terrain.fallenLogs", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_ROCK_SPIRES = B
            .comment("Small rock spires in stony peaks and windswept hills.")
            .define("world.terrain.rockSpires", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_WILDFLOWERS = B
            .comment("Wildflower patches in plains and forests.")
            .define("world.terrain.wildflowers", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_MOSS_CARPETS = B
            .comment("Moss carpets in dark forests and old-growth taigas.")
            .define("world.terrain.mossCarpets", true);
    public static final ForgeConfigSpec.BooleanValue TERRAIN_HOT_SPRINGS = B
            .comment("Hot-spring terraces in windswept savannas and savanna plateaus.")
            .define("world.terrain.hotSprings", true);
    public static final ForgeConfigSpec.BooleanValue DANGER_SCALING = B
            .comment("Monsters get stronger the further you travel from world spawn, and in the Nether/End.")
            .define("danger.enabled", true);
    public static final ForgeConfigSpec.IntValue DANGER_DISTANCE = B
            .comment("Blocks of distance from spawn per danger level in the Overworld.")
            .defineInRange("danger.blocksPerLevel", 900, 100, 100000);
    public static final ForgeConfigSpec.IntValue DANGER_MAX = B
            .comment("Highest danger level.")
            .defineInRange("danger.maxLevel", 7, 1, 20);
    public static final ForgeConfigSpec.DoubleValue HEALTH_PER_LEVEL = B
            .comment("Extra max health per danger level (0.15 = +15%).")
            .defineInRange("danger.healthPerLevel", 0.15, 0.0, 5.0);
    public static final ForgeConfigSpec.DoubleValue DAMAGE_PER_LEVEL = B
            .comment("Extra attack damage per danger level (0.12 = +12%).")
            .defineInRange("danger.damagePerLevel", 0.12, 0.0, 5.0);
    public static final ForgeConfigSpec.DoubleValue ELITE_CHANCE = B
            .comment("Base chance for a monster to spawn as an Elite (+2% per danger level).")
            .defineInRange("elite.baseChance", 0.03, 0.0, 1.0);
    public static final ForgeConfigSpec.BooleanValue BLOOD_MOON = B
            .comment("Every few nights a Blood Moon rises: much stronger monsters and many more Elites.")
            .define("bloodMoon.enabled", true);
    public static final ForgeConfigSpec.IntValue BLOOD_MOON_INTERVAL = B
            .comment("A Blood Moon happens every N nights.")
            .defineInRange("bloodMoon.interval", 7, 2, 100);
    public static final ForgeConfigSpec.IntValue TERMINAL_RANGE = B
            .comment("Guild Terminal reach, in blocks around it (horizontally): every chest, barrel, shulker box, sorting",
                    "chest and compacting crate in that square is part of its storage network.")
            .defineInRange("storage.terminalRange", 48, 8, 128);
    public static final ForgeConfigSpec.IntValue TERMINAL_HEIGHT = B
            .comment("Guild Terminal and Storage Relay reach up and down, in blocks (384 = the whole height of the world).")
            .defineInRange("storage.terminalHeight", 32, 4, 384);
    public static final ForgeConfigSpec.IntValue RELAY_RANGE = B
            .comment("Storage Relay reach, in blocks around it (horizontally). A relay joins the network when it is within",
                    "reach of the terminal or of another relay of the network.")
            .defineInRange("storage.relayRange", 32, 8, 128);
    public static final ForgeConfigSpec.IntValue MAX_CONTAINERS = B
            .comment("Most containers one terminal network can link (protects the server on huge bases).")
            .defineInRange("storage.maxContainers", 2048, 64, 16384);

    public static final ForgeConfigSpec.BooleanValue MAP_SHARED = B
            .comment("World map: everyone sees what anyone explored. False: each player only sees the places they saw themselves",
                    "(the server keeps track of both, so this can be switched at any time).")
            .define("map.sharedExploration", true);
    public static final ForgeConfigSpec.BooleanValue MAP_PLAYERS = B
            .comment("Show online players on each other's minimap and world map (same dimension).")
            .define("map.showPlayers", true);

    public static final ForgeConfigSpec SPEC = B.build();

    private WayfarersConfig() {}

    /** The world.terrain.&lt;toggle&gt; switch of a terrain touch (world/ToggledFeaturesModifier), null if unknown. */
    public static Boolean terrainTouch(String toggle) {
        ForgeConfigSpec.BooleanValue v = switch (toggle) {
            case "boulders" -> TERRAIN_BOULDERS;
            case "fallenLogs" -> TERRAIN_FALLEN_LOGS;
            case "rockSpires" -> TERRAIN_ROCK_SPIRES;
            case "wildflowers" -> TERRAIN_WILDFLOWERS;
            case "mossCarpets" -> TERRAIN_MOSS_CARPETS;
            case "hotSprings" -> TERRAIN_HOT_SPRINGS;
            default -> null;
        };
        return v == null ? null : v.get();
    }
}

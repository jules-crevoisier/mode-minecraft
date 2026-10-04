package com.wayfarers.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** config/wayfarers-common.toml — every difficulty knob can be tuned or switched off by the server owner. */
public final class WayfarersConfig {
    private static final ForgeConfigSpec.Builder B = new ForgeConfigSpec.Builder();

    public static final ForgeConfigSpec.BooleanValue WORLD_OVERHAUL = B
            .comment("New worlds use the Wayfarers terrain, caves and biomes (a built-in data pack, \"wayfarers:world_overhaul\").",
                    "Set to false to keep the vanilla Overworld; the pack then stays available, unticked, in the Data Packs screen.",
                    "Existing worlds keep whatever they were created with.")
            .define("world.overhaul", true);
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

    public static final ForgeConfigSpec.BooleanValue MAP_SHARED = B
            .comment("World map: everyone sees what anyone explored. False: each player only sees the places they saw themselves",
                    "(the server keeps track of both, so this can be switched at any time).")
            .define("map.sharedExploration", true);
    public static final ForgeConfigSpec.BooleanValue MAP_PLAYERS = B
            .comment("Show online players on each other's minimap and world map (same dimension).")
            .define("map.showPlayers", true);

    public static final ForgeConfigSpec SPEC = B.build();

    private WayfarersConfig() {}
}

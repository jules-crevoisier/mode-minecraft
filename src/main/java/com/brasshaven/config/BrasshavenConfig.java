package com.brasshaven.config;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * config/brasshaven-common.toml — every difficulty knob can be tuned or switched off by the server owner, plus the
 * server administration options (anti-grief, anti-exploit, load limits) described in docs/SERVER_ADMIN.md.
 */
public final class BrasshavenConfig {
    private static final ForgeConfigSpec.Builder B = new ForgeConfigSpec.Builder();

    public static final ForgeConfigSpec.BooleanValue STRUCTURE_FIT = B
            .comment("Brasshaven structures only start where the terrain suits them: flat enough dry ground for buildings,",
                    "a shore for the lighthouse, open sea floor for wrecks, clear sky under floating isles. A site that does not",
                    "fit is skipped like one with the wrong biome (/locate looks further). False: build wherever the grid says.")
            .define("world.structureFit", true);
    public static final ForgeConfigSpec.BooleanValue CUSTOM_BIOMES = B
            .comment("New Default worlds get the Brasshaven biomes: Crimson Mire (in the wettest swamps), Volcanic Highlands",
                    "(in badlands mountains) and Pale Dunes (in the driest deserts). Minecraft's terrain is kept: a built-in data",
                    "pack (\"brasshaven:custom_biomes\") only hands these climate slices to the new biomes. Minecraft shows its",
                    "\"experimental settings\" warning when a world is created with it; that is expected. False: new worlds",
                    "keep the vanilla biomes (the pack stays available, unticked, in the Data Packs screen). Superflat,",
                    "Amplified and Large Biomes worlds, and existing worlds, are never changed.")
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

    public static final ForgeConfigSpec.BooleanValue REQUIRE_SAME_VERSION = B
            .comment("Refuse players whose Brasshaven version differs from the server's, with a message naming both versions",
                    "and the download page. False: only an incompatible network protocol or missing blocks/items refuse them.")
            .define("compat.requireSameVersion", true);
    public static final ForgeConfigSpec.ConfigValue<String> DOWNLOAD_URL = B
            .comment("Download page given to refused players (your modpack page, for example). Empty: the mod's own page.")
            .define("compat.downloadUrl", "");
    public static final ForgeConfigSpec.BooleanValue UPDATE_CHECK = B
            .comment("Dedicated server: look for a newer Brasshaven release at start-up (GitHub, in the background) and log it.",
                    "Nothing is ever downloaded.")
            .define("updates.checkForUpdates", true);

    // ------------------------------------------------------------------ server administration (docs/SERVER_ADMIN.md)
    // Defaults are the safe ones for a public server; a small group of friends can loosen them.

    public static final ForgeConfigSpec.BooleanValue WAYSTONE_CROSS_DIMENSION = B
            .comment("Waystones may send players to a waystone of another dimension (Nether, End...).")
            .define("waystones.crossDimension", true);
    public static final ForgeConfigSpec.IntValue WAYSTONE_COOLDOWN = B
            .comment("Seconds a player waits between two waystone journeys (each journey loads the chunks at the arrival).",
                    "0 = no wait. Operators are never held back.")
            .defineInRange("waystones.cooldownSeconds", 5, 0, 3600);
    public static final ForgeConfigSpec.IntValue WAYSTONE_COST = B
            .comment("Experience levels a waystone journey costs (0 = free). A journey to another dimension costs twice as much.")
            .defineInRange("waystones.costLevels", 0, 0, 100);
    public static final ForgeConfigSpec.IntValue WAYSTONE_MAX = B
            .comment("Most waystones the server remembers (each is listed to everyone): further ones can't be activated.")
            .defineInRange("waystones.maxTotal", 1000, 16, 20000);
    public static final ForgeConfigSpec.BooleanValue WAYSTONE_RENAME_HERE_ONLY = B
            .comment("Players may rename or pin only the waystone they stand at (true), or any waystone of the list (false).",
                    "Waystones are shared by the whole server: true stops anyone from renaming everybody's stones. Operators may always.")
            .define("waystones.renameOnlyHere", true);

    public static final ForgeConfigSpec.BooleanValue BREAKER_ENABLED = B
            .comment("The Block Breaker machine works (false: it stays idle).")
            .define("machines.breakerEnabled", true);
    public static final ForgeConfigSpec.BooleanValue PLACER_ENABLED = B
            .comment("The Block Placer machine works (false: it stays idle).")
            .define("machines.placerEnabled", true);
    public static final ForgeConfigSpec.BooleanValue MACHINES_ACT_AS_OWNER = B
            .comment("Block Breakers and Placers act as the player who placed them: spawn protection and claim / protection",
                    "mods (through Forge's break and place events) apply to them, and they wait while that player is offline.",
                    "Machines placed before this option existed have no owner and keep working as before.")
            .define("machines.actAsOwner", true);
    public static final ForgeConfigSpec.IntValue WIRELESS_RANGE = B
            .comment("Wireless Redstone reach in blocks: a receiver only hears transmitters this close (0 = the whole dimension).",
                    "Keeps one player's transmitter from switching other bases' receivers across the map.")
            .defineInRange("machines.wirelessRange", 128, 0, 30000000);
    public static final ForgeConfigSpec.IntValue MACHINES_PER_CHUNK = B
            .comment("Most Brasshaven machines one chunk may hold (0 = no limit). Placing more is refused.")
            .defineInRange("machines.maxPerChunk", 32, 0, 4096);

    public static final ForgeConfigSpec.DoubleValue MAGNET_RANGE = B
            .comment("Magnet Ring reach in blocks (0 = the ring does nothing).")
            .defineInRange("items.magnetRange", 7.0, 0.0, 16.0);
    public static final ForgeConfigSpec.BooleanValue STORM_STAFF_GRIEF = B
            .comment("Storm Staff lightning acts like real lightning: it sets fires and hits players, pets and villagers.",
                    "false: the bolt only hurts monsters and starts no fire.")
            .define("items.stormStaffRealLightning", false);
    public static final ForgeConfigSpec.IntValue QUICK_STACK_RANGE = B
            .comment("Reach in blocks of the quick-stack button (stores your items into nearby chests that hold them). 0 = off.")
            .defineInRange("storage.quickStackRange", 8, 0, 16);

    public static final ForgeConfigSpec.IntValue GRAVE_PROTECTION = B
            .comment("Minutes during which only its owner (and operators) can open a grave. 0 = anyone at once, -1 = only the owner, always.")
            .defineInRange("graves.ownerOnlyMinutes", -1, -1, 100000);

    public static final ForgeConfigSpec.BooleanValue QUESTS_SHARED = B
            .comment("A quest step reached by one player is reached by everyone online (the quest is shared by the server).",
                    "Each player still receives the step's rewards once.")
            .define("quests.shareProgress", true);
    public static final ForgeConfigSpec.BooleanValue QUESTS_CATCH_UP = B
            .comment("Players who join later (or were offline) receive, when they log in, every quest step the server already",
                    "reached (with its rewards).",
                    "On a public server, false stops new (or alt) accounts from collecting every reward at once.")
            .define("quests.catchUpOnJoin", true);

    public static final ForgeConfigSpec.BooleanValue SPAWNS_ENABLED = B
            .comment("Brasshaven creatures spawn naturally (monsters and ocean life). Structures and altars still place theirs.")
            .define("spawns.natural", true);
    public static final ForgeConfigSpec.IntValue SPAWNS_MAX_PER_TYPE = B
            .comment("Most loaded creatures of one Brasshaven kind per dimension before natural spawning of that kind pauses.")
            .defineInRange("spawns.maxLoadedPerType", 60, 0, 10000);

    public static final ForgeConfigSpec.IntValue LOCATE_PER_MINUTE = B
            .comment("Structure Compass / Airship Compass searches the whole server may run per minute (each one can take",
                    "a while on the server thread). Answers are remembered, so repeated uses near the same place are free.")
            .defineInRange("compass.searchesPerMinute", 30, 1, 1200);

    /** Multiplayer features (com.brasshaven.social), in their own "social" section. */
    public static final SocialConfig SOCIAL = new SocialConfig(B);

    public static final ForgeConfigSpec SPEC = B.build();

    private BrasshavenConfig() {}

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

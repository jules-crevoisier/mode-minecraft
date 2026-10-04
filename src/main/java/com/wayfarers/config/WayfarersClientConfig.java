package com.wayfarers.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** config/wayfarers-client.toml — per-player display preferences. */
public final class WayfarersClientConfig {
    public enum HealthBars { ALWAYS, DAMAGED, NEVER }

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

    public static final ForgeConfigSpec SPEC = B.build();

    private WayfarersClientConfig() {}
}

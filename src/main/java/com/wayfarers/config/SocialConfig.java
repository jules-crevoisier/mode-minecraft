package com.wayfarers.config;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * The multiplayer features (com.wayfarers.social), in the "social" section of config/wayfarers-common.toml. Every
 * feature has its own switch: a disabled feature refuses its commands, packets, blocks and screens on the server
 * (clients learn the switches when they join, so the buttons grey out).
 */
public final class SocialConfig {
    // ---- the Company (parties)
    public final ForgeConfigSpec.BooleanValue companyEnabled;
    public final ForgeConfigSpec.IntValue companyMaxSize;
    public final ForgeConfigSpec.IntValue companyXpRange;
    public final ForgeConfigSpec.IntValue companyJoinCost;
    public final ForgeConfigSpec.IntValue companyJoinCooldown;
    // ---- secure trade
    public final ForgeConfigSpec.BooleanValue tradeEnabled;
    public final ForgeConfigSpec.IntValue tradeDistance;
    // ---- pneumatic post
    public final ForgeConfigSpec.BooleanValue postEnabled;
    public final ForgeConfigSpec.ConfigValue<String> postageItem;
    public final ForgeConfigSpec.IntValue postageBase;
    public final ForgeConfigSpec.IntValue postagePerStack;
    public final ForgeConfigSpec.IntValue inboxLimit;
    public final ForgeConfigSpec.IntValue sendsPerMinute;
    // ---- guild contracts
    public final ForgeConfigSpec.BooleanValue contractsEnabled;
    public final ForgeConfigSpec.IntValue contractsPerPlayer;
    public final ForgeConfigSpec.IntValue contractDays;
    // ---- emotes
    public final ForgeConfigSpec.BooleanValue emotesEnabled;
    public final ForgeConfigSpec.IntValue emoteCooldown;
    // ---- duels
    public final ForgeConfigSpec.BooleanValue duelsEnabled;
    public final ForgeConfigSpec.IntValue duelRadius;
    public final ForgeConfigSpec.IntValue duelSeconds;
    public final ForgeConfigSpec.BooleanValue duelAnnounce;

    SocialConfig(ForgeConfigSpec.Builder b) {
        b.comment("Multiplayer features: the Company (parties), secure trade, pneumatic post, guild contracts, emotes and",
                "duels. Each one can be switched off; everything is checked by the server.").push("social");

        companyEnabled = b.comment("Companies (parties): invite, company chat, friendly-fire and XP-sharing switches, companions",
                "on the HUD and the maps, travel to a companion from a waystone.").define("company.enabled", true);
        companyMaxSize = b.comment("Most members in one company.").defineInRange("company.maxSize", 8, 2, 32);
        companyXpRange = b.comment("Shared experience goes to companions within this many blocks (same dimension).")
                .defineInRange("company.xpShareRange", 48, 8, 256);
        companyJoinCost = b.comment("Experience levels paid to travel from a waystone to a companion (creative players pay nothing).")
                .defineInRange("company.joinCostLevels", 2, 0, 30);
        companyJoinCooldown = b.comment("Seconds between two trips to a companion.")
                .defineInRange("company.joinCooldownSeconds", 120, 0, 3600);

        tradeEnabled = b.comment("Secure trade between two players: both confirm, a 3 s countdown, then the items swap at once.")
                .define("trade.enabled", true);
        tradeDistance = b.comment("Both traders must stay within this many blocks of each other.")
                .defineInRange("trade.maxDistance", 8, 2, 64);

        postEnabled = b.comment("Pneumatic Post: letters and parcels to any player who ever joined, even offline.")
                .define("post.enabled", true);
        postageItem = b.comment("Item paid as postage (an item id; empty = free post).")
                .define("post.postageItem", "wayfarers:brass_nugget");
        postageBase = b.comment("Postage for every letter or parcel.").defineInRange("post.postageBase", 1, 0, 64);
        postagePerStack = b.comment("Extra postage for each stack of items in the parcel.").defineInRange("post.postagePerStack", 1, 0, 64);
        inboxLimit = b.comment("Letters waiting in one inbox before the post refuses more (contract deliveries and returns",
                "always get through).").defineInRange("post.inboxLimit", 40, 5, 500);
        sendsPerMinute = b.comment("Letters one player may send per minute.").defineInRange("post.sendsPerMinute", 6, 1, 120);

        contractsEnabled = b.comment("Guild contracts on the Contract Board: post a request with an escrowed reward, anyone",
                "delivers the goods and is paid at once; the goods go to the poster's Pneumatic Post inbox.")
                .define("contracts.enabled", true);
        contractsPerPlayer = b.comment("Open contracts per player.").defineInRange("contracts.maxPerPlayer", 5, 1, 50);
        contractDays = b.comment("Days (real time) before an open contract expires; its reward goes back to the poster's inbox.")
                .defineInRange("contracts.expiryDays", 7, 1, 90);

        emotesEnabled = b.comment("Emotes (wave, bow, cheer...) seen by the players around.").define("emotes.enabled", true);
        emoteCooldown = b.comment("Ticks between two emotes of one player (20 ticks = 1 s).").defineInRange("emotes.cooldownTicks", 40, 10, 1200);

        duelsEnabled = b.comment("Duels: challenge, accept, 3 s countdown, nobody dies and nothing is lost.").define("duels.enabled", true);
        duelRadius = b.comment("Radius of the duel ring around its centre; leaving it forfeits.").defineInRange("duels.radius", 20, 6, 64);
        duelSeconds = b.comment("Longest duel, in seconds (then it is a draw).").defineInRange("duels.maxSeconds", 180, 30, 1800);
        duelAnnounce = b.comment("Announce the winner of each duel to the whole server.").define("duels.announce", true);
        b.pop();
    }
}

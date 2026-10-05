package com.brasshaven.client;

import com.brasshaven.network.SkillSyncMsg;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Client copy of the player's talents and mana (pushed by the server). */
public final class ClientSkills {
    public static int points;
    public static int earned;
    public static final Set<String> UNLOCKED = new HashSet<>();
    public static String active = "";
    public static float mana = 100;
    public static float maxMana = 100;
    public static long cooldownTicks;
    public static long syncedAt;

    private ClientSkills() {}

    public static void update(SkillSyncMsg msg) {
        points = msg.points();
        earned = msg.earned();
        UNLOCKED.clear();
        UNLOCKED.addAll(msg.unlocked());
        active = msg.active();
        mana = msg.mana();
        maxMana = msg.maxMana();
        cooldownTicks = msg.cooldownTicks();
        syncedAt = System.currentTimeMillis();
    }

    public static boolean has(String skill) {
        return UNLOCKED.contains(skill);
    }

    public static boolean canUnlock(String skill, int cost, List<String> requires) {
        return !has(skill) && points >= cost && (requires.isEmpty() || requires.stream().anyMatch(UNLOCKED::contains));
    }
}

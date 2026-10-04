package com.wayfarers.skill;

import com.wayfarers.Wayfarers;
import com.wayfarers.generated.GeneratedContent;
import com.wayfarers.generated.GeneratedSkills;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;

import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Optional;
import java.util.Set;

/**
 * A player's talents and mana, stored in the player's persistent data (kept across deaths).
 * Talent points: 1 per completed quest, +2 more per boss quest, and 1 per 10 experience levels earned.
 */
public final class PlayerSkills {
    private static final String KEY = "wayfarers_skills";
    public static final float BASE_MANA = 100F;
    public static final float BASE_REGEN = 2.5F; // mana per second

    private PlayerSkills() {}

    // ------------------------------------------------------------------ storage
    private static CompoundTag data(ServerPlayer player) {
        CompoundTag root = player.getPersistentData();
        CompoundTag persisted = root.getCompoundOrEmpty("PlayerPersisted");
        CompoundTag tag = persisted.getCompoundOrEmpty(KEY);
        persisted.put(KEY, tag);
        root.put("PlayerPersisted", persisted);
        return tag;
    }

    public static Set<String> unlocked(ServerPlayer player) {
        Set<String> out = new LinkedHashSet<>();
        ListTag list = data(player).getListOrEmpty("unlocked");
        for (Tag t : list) {
            t.asString().ifPresent(out::add);
        }
        return out;
    }

    private static void setUnlocked(ServerPlayer player, Set<String> skills) {
        ListTag list = new ListTag();
        for (String s : skills) {
            list.add(StringTag.valueOf(s));
        }
        data(player).put("unlocked", list);
    }

    public static float mana(ServerPlayer player) {
        return data(player).getFloatOr("mana", BASE_MANA);
    }

    public static void setMana(ServerPlayer player, float mana) {
        setMana(player, mana, maxMana(player));
    }

    /** Same as {@link #setMana(ServerPlayer, float)} with an already computed maximum; returns the stored value. */
    public static float setMana(ServerPlayer player, float mana, float max) {
        float stored = Math.max(0, Math.min(max, mana));
        data(player).putFloat("mana", stored);
        return stored;
    }

    public static int lifetimeLevels(ServerPlayer player) {
        return data(player).getIntOr("levels", 0);
    }

    public static void addLevels(ServerPlayer player, int levels) {
        data(player).putInt("levels", lifetimeLevels(player) + levels);
    }

    public static String active(ServerPlayer player) {
        return data(player).getStringOr("active", "");
    }

    public static void setActive(ServerPlayer player, String ability) {
        data(player).putString("active", ability);
    }

    public static long cooldownUntil(ServerPlayer player, String ability) {
        return data(player).getLongOr("cd_" + ability, 0L);
    }

    public static void setCooldown(ServerPlayer player, String ability, long until) {
        data(player).putLong("cd_" + ability, until);
    }

    // ------------------------------------------------------------------ points
    public static int earnedPoints(ServerPlayer player) {
        int points = lifetimeLevels(player) / 10;
        var server = player.level().getServer();
        for (GeneratedContent.Chapter chapter : GeneratedContent.CHAPTERS) {
            for (String quest : chapter.quests()) {
                AdvancementHolder holder = server.getAdvancements().get(Wayfarers.id(quest));
                if (holder != null && player.getAdvancements().getOrStartProgress(holder).isDone()) {
                    points += isBossQuest(quest) ? 3 : 1;
                }
            }
        }
        return points;
    }

    private static boolean isBossQuest(String quest) {
        String name = quest.substring(quest.indexOf('/') + 1);
        return name.startsWith("boss_") || name.equals("drowned_warden") || name.equals("void_warden");
    }

    public static int spentPoints(Set<String> unlocked) {
        int n = 0;
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            if (unlocked.contains(s.id())) {
                n += s.cost();
            }
        }
        return n;
    }

    public static int availablePoints(ServerPlayer player) {
        return earnedPoints(player) - spentPoints(unlocked(player));
    }

    public static Optional<GeneratedSkills.Skill> skill(String id) {
        return GeneratedSkills.SKILLS.stream().filter(s -> s.id().equals(id)).findFirst();
    }

    /** Unlocks a talent if the player has the points and every required talent. */
    public static boolean unlock(ServerPlayer player, String id) {
        Optional<GeneratedSkills.Skill> opt = skill(id);
        Set<String> have = unlocked(player);
        if (opt.isEmpty() || have.contains(id)) {
            return false;
        }
        GeneratedSkills.Skill s = opt.get();
        if (!s.requires().isEmpty() && s.requires().stream().noneMatch(have::contains)) {
            return false; // any one of the parents is enough (the tree branches back together)
        }
        if (availablePoints(player) < s.cost()) {
            return false;
        }
        have.add(id);
        setUnlocked(player, have);
        if (s.kind().equals("active")) {
            setActive(player, s.ability());
        }
        apply(player);
        return true;
    }

    public static void reset(ServerPlayer player) {
        setUnlocked(player, new HashSet<>());
        setActive(player, "");
        apply(player);
    }

    // ------------------------------------------------------------------ effects
    private static double sum(Set<String> unlocked, String kind) {
        double total = 0;
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            if (unlocked.contains(s.id()) && s.kind().equals(kind)) {
                total += s.amount();
            }
        }
        return total;
    }

    public static float maxMana(ServerPlayer player) {
        return BASE_MANA + (float) sum(unlocked(player), "mana") + ManaItems.bonusMana(player);
    }

    public static float regenPerSecond(ServerPlayer player) {
        return BASE_REGEN * (1F + (float) sum(unlocked(player), "regen") + ManaItems.bonusRegen(player));
    }

    public static float spellPower(ServerPlayer player) {
        return 1F + (float) sum(unlocked(player), "power") + ManaItems.bonusPower(player);
    }

    public static float costMultiplier(ServerPlayer player) {
        return Math.max(0.3F, 1F - (float) sum(unlocked(player), "thrift"));
    }

    public static float lifesteal(ServerPlayer player) {
        return (float) sum(unlocked(player), "lifesteal");
    }

    /** Fastest repair interval in seconds among unlocked repair talents, or 0. */
    public static int repairInterval(ServerPlayer player) {
        int best = 0;
        Set<String> have = unlocked(player);
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            if (have.contains(s.id()) && s.kind().equals("repair")) {
                int sec = (int) s.amount();
                best = best == 0 ? sec : Math.min(best, sec);
            }
        }
        return best;
    }

    /** (Re)applies every passive attribute bonus as transient modifiers (called on login, respawn, unlock). */
    public static void apply(ServerPlayer player) {
        Set<String> have = unlocked(player);
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            if (!s.kind().equals("attr")) {
                continue;
            }
            Holder<Attribute> attr = attribute(s.attribute());
            AttributeInstance inst = attr == null ? null : player.getAttribute(attr);
            if (inst == null) {
                continue;
            }
            Identifier id = Wayfarers.id("skill/" + s.id());
            inst.removeModifier(id);
            if (have.contains(s.id())) {
                inst.addTransientModifier(new AttributeModifier(id, s.amount(), AttributeModifier.Operation.valueOf(s.operation())));
            }
        }
        if (player.getHealth() > player.getMaxHealth()) {
            player.setHealth(player.getMaxHealth());
        }
    }

    private static Holder<Attribute> attribute(String field) {
        Identifier id = Identifier.withDefaultNamespace(field.toLowerCase(java.util.Locale.ROOT));
        return BuiltInRegistries.ATTRIBUTE.get(id).map(h -> (Holder<Attribute>) h).orElse(null);
    }
}

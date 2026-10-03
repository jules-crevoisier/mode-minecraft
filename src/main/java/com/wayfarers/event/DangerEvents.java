package com.wayfarers.event;

import com.wayfarers.Wayfarers;
import com.wayfarers.config.WayfarersConfig;
import com.wayfarers.entity.BossZombie;
import com.wayfarers.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.fml.LogicalSide;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Difficulty layer: monsters scale with the "danger level" of where they spawn (distance from
 * world spawn, Nether/End bonus, Blood Moon), some spawn as Elites with better loot, and players
 * see the danger level of the area on their action bar when it changes.
 */
public final class DangerEvents {
    private static final String SCALED = "wayfarers_scaled";
    public static final String ELITE = "wayfarers_elite";
    private static final Identifier HEALTH_ID = Wayfarers.id("danger_health");
    private static final Identifier DAMAGE_ID = Wayfarers.id("danger_damage");
    private static final Identifier ARMOR_ID = Wayfarers.id("danger_armor");
    private static final Identifier SPEED_ID = Wayfarers.id("elite_speed");
    private static final Map<UUID, Integer> SHOWN_LEVEL = new HashMap<>();
    private static boolean bloodMoon;

    private DangerEvents() {}

    public static void register() {
        EntityJoinLevelEvent.BUS.addListener((Consumer<EntityJoinLevelEvent>) DangerEvents::onJoin);
        LivingDropsEvent.BUS.addListener((Consumer<LivingDropsEvent>) DangerEvents::onDrops);
        TickEvent.LevelTickEvent.Post.BUS.addListener(DangerEvents::onLevelTick);
        TickEvent.PlayerTickEvent.Post.BUS.addListener(DangerEvents::onPlayerTick);
    }

    public static boolean isBloodMoon() {
        return bloodMoon;
    }

    /** Danger level of a position: 0 near spawn, rising with distance; Nether +2, End +3. */
    public static int dangerAt(ServerLevel level, BlockPos pos) {
        if (!WayfarersConfig.DANGER_SCALING.get()) {
            return 0;
        }
        int perLevel = WayfarersConfig.DANGER_DISTANCE.get();
        double dist;
        int base = 0;
        if (level.dimension() == Level.NETHER) {
            dist = Math.hypot(pos.getX(), pos.getZ()) * 8.0;
            base = 2;
        } else if (level.dimension() == Level.END) {
            dist = Math.hypot(pos.getX(), pos.getZ());
            base = 3;
        } else {
            BlockPos spawn = level.getRespawnData().pos();
            dist = Math.hypot(pos.getX() - spawn.getX(), pos.getZ() - spawn.getZ());
            if (pos.getY() < 0) {
                base = 1; // the deep dark is never safe
            }
        }
        int lvl = base + (int) (dist / perLevel);
        if (bloodMoon && level.dimension() == Level.OVERWORLD) {
            lvl += 2;
        }
        return Math.min(lvl, WayfarersConfig.DANGER_MAX.get());
    }

    private static void onJoin(EntityJoinLevelEvent event) {
        Entity entity = event.getEntity();
        if (!(event.getLevel() instanceof ServerLevel level) || !(entity instanceof Mob mob) || !(entity instanceof Enemy)
                || entity instanceof BossZombie || entity instanceof com.wayfarers.boss.WayfarerBoss || entity.entityTags().contains(SCALED)) {
            return;
        }
        entity.addTag(SCALED);
        int danger = dangerAt(level, entity.blockPosition());
        if (danger > 0) {
            add(mob, Attributes.MAX_HEALTH, HEALTH_ID, WayfarersConfig.HEALTH_PER_LEVEL.get() * danger,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
            add(mob, Attributes.ATTACK_DAMAGE, DAMAGE_ID, WayfarersConfig.DAMAGE_PER_LEVEL.get() * danger,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
            add(mob, Attributes.ARMOR, ARMOR_ID, danger, AttributeModifier.Operation.ADD_VALUE);
        }
        double eliteChance = WayfarersConfig.ELITE_CHANCE.get() + 0.02 * danger;
        if (bloodMoon) {
            eliteChance *= 3;
        }
        if (level.getRandom().nextDouble() < eliteChance) {
            makeElite(mob);
        }
        mob.setHealth(mob.getMaxHealth());
    }

    public static void makeElite(Mob mob) {
        mob.addTag(ELITE);
        add(mob, Attributes.MAX_HEALTH, Wayfarers.id("elite_health"), 1.0, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        add(mob, Attributes.ATTACK_DAMAGE, Wayfarers.id("elite_damage"), 0.5, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        add(mob, Attributes.MOVEMENT_SPEED, SPEED_ID, 0.15, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        add(mob, Attributes.KNOCKBACK_RESISTANCE, Wayfarers.id("elite_knockback"), 0.5, AttributeModifier.Operation.ADD_VALUE);
        mob.setCustomName(Component.translatable("message.wayfarers.elite", mob.getType().getDescription())
                .withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
        mob.setHealth(mob.getMaxHealth());
    }

    private static void add(Mob mob, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attr,
                            Identifier id, double amount, AttributeModifier.Operation op) {
        AttributeInstance inst = mob.getAttribute(attr);
        if (inst != null && !inst.hasModifier(id)) {
            inst.addPermanentModifier(new AttributeModifier(id, amount, op));
        }
    }

    /** Elites drop the progression material of their dimension, emeralds and extra experience. */
    private static void onDrops(LivingDropsEvent event) {
        if (!(event.getEntity() instanceof Mob mob) || !mob.entityTags().contains(ELITE)
                || !(mob.level() instanceof ServerLevel level)) {
            return;
        }
        Item material = level.dimension() == Level.NETHER ? ModItems.ANCIENT_EMBER.get()
                : level.dimension() == Level.END ? ModItems.VOID_SHARD.get()
                : mob.getY() < 0 ? ModItems.LITHITE_SHARD.get() : ModItems.MAP_FRAGMENT.get();
        int n = 1 + level.getRandom().nextInt(3);
        event.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY() + 0.5, mob.getZ(), new ItemStack(material, n)));
        event.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY() + 0.5, mob.getZ(),
                new ItemStack(Items.EMERALD, 1 + level.getRandom().nextInt(3))));
        if (level.getRandom().nextFloat() < 0.15F) {
            event.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY() + 0.5, mob.getZ(),
                    new ItemStack(ModItems.RECALL_SCROLL.get())));
        }
        ExperienceOrb.award(level, mob.position(), 20 + 5 * dangerAt(level, mob.blockPosition()));
    }

    // ------------------------------------------------------------------ blood moon
    private static void onLevelTick(TickEvent.LevelTickEvent.Post event) {
        if (event.side() != LogicalSide.SERVER || !(event.level() instanceof ServerLevel level)
                || level.dimension() != Level.OVERWORLD || level.getGameTime() % 100 != 0) {
            return;
        }
        boolean now = false;
        if (WayfarersConfig.BLOOD_MOON.get()) {
            long clock = level.getOverworldClockTime();
            long day = clock / 24000L;
            long time = clock % 24000L;
            int interval = WayfarersConfig.BLOOD_MOON_INTERVAL.get();
            now = day % interval == interval - 1 && time >= 13000 && time <= 23000;
        }
        if (now != bloodMoon) {
            bloodMoon = now;
            MinecraftServer server = level.getServer();
            server.getPlayerList().broadcastSystemMessage(Component.translatable(now
                    ? "message.wayfarers.blood_moon.rise" : "message.wayfarers.blood_moon.end")
                    .withStyle(now ? ChatFormatting.DARK_RED : ChatFormatting.GOLD), false);
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                player.level().playSound(null, player, now ? SoundEvents.WITHER_SPAWN : SoundEvents.BELL_BLOCK,
                        SoundSource.AMBIENT, 0.6F, now ? 0.5F : 1.0F);
            }
        }
    }

    private static void onPlayerTick(TickEvent.PlayerTickEvent.Post event) {
        Player player = event.player();
        if (event.side() != LogicalSide.SERVER || player.tickCount % 40 != 0
                || !(player.level() instanceof ServerLevel level) || !(player instanceof ServerPlayer serverPlayer)) {
            return;
        }
        int danger = dangerAt(level, player.blockPosition());
        Integer last = SHOWN_LEVEL.put(player.getUUID(), danger);
        if (last != null && last != danger) {
            ChatFormatting color = danger <= 1 ? ChatFormatting.GREEN : danger <= 3 ? ChatFormatting.YELLOW
                    : danger <= 5 ? ChatFormatting.RED : ChatFormatting.DARK_PURPLE;
            serverPlayer.sendOverlayMessage(Component.translatable("message.wayfarers.danger",
                    Component.translatable("message.wayfarers.danger." + Math.min(danger, 7))).withStyle(color));
        }
    }
}

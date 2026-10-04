package com.wayfarers.event;

import com.wayfarers.Wayfarers;
import com.wayfarers.generated.GeneratedMetals;
import com.wayfarers.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingFallEvent;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.fml.LogicalSide;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Predicate;

/** Armor set bonuses, the 3x3 Excavator Pickaxe, the tree-felling Lumber Axe and void rescue. */
public final class EquipmentEvents {
    private static final Map<UUID, BlockPos> LAST_SAFE = new HashMap<>();
    private static boolean breakingArea;

    private EquipmentEvents() {}

    public static void register() {
        TickEvent.PlayerTickEvent.Post.BUS.addListener(EquipmentEvents::onPlayerTick);
        LivingFallEvent.BUS.addListener((Predicate<LivingFallEvent>) EquipmentEvents::onFall);
        BlockEvent.BreakEvent.BUS.addListener((Consumer<BlockEvent.BreakEvent>) EquipmentEvents::onBreak);
    }

    public enum ArmorSet { EXPLORER, EMBER, VOID, BRASS, MITHRIL, AETHER, ARCANE, NONE }

    private static final Identifier MITHRIL_HEALTH = Wayfarers.id("set/mithril_health");
    private static final Identifier MITHRIL_SPEED = Wayfarers.id("set/mithril_speed");

    private static boolean wearing(Item head, Item chest, Item legs, Item feet, Item h, Item c, Item l, Item f) {
        return head == h && chest == c && legs == l && feet == f;
    }

    public static ArmorSet fullSet(Player player) {
        Item head = player.getItemBySlot(EquipmentSlot.HEAD).getItem();
        Item chest = player.getItemBySlot(EquipmentSlot.CHEST).getItem();
        Item legs = player.getItemBySlot(EquipmentSlot.LEGS).getItem();
        Item feet = player.getItemBySlot(EquipmentSlot.FEET).getItem();
        if (head == ModItems.EXPLORER_HELMET.get() && chest == ModItems.EXPLORER_CHESTPLATE.get()
                && legs == ModItems.EXPLORER_LEGGINGS.get() && feet == ModItems.EXPLORER_BOOTS.get()) {
            return ArmorSet.EXPLORER;
        }
        if (head == ModItems.EMBER_HELMET.get() && chest == ModItems.EMBER_CHESTPLATE.get()
                && legs == ModItems.EMBER_LEGGINGS.get() && feet == ModItems.EMBER_BOOTS.get()) {
            return ArmorSet.EMBER;
        }
        if (head == ModItems.VOID_HELMET.get() && chest == ModItems.VOID_CHESTPLATE.get()
                && legs == ModItems.VOID_LEGGINGS.get() && feet == ModItems.VOID_BOOTS.get()) {
            return ArmorSet.VOID;
        }
        if (wearing(head, chest, legs, feet, GeneratedMetals.BRASS_HELMET.get(), GeneratedMetals.BRASS_CHESTPLATE.get(),
                GeneratedMetals.BRASS_LEGGINGS.get(), GeneratedMetals.BRASS_BOOTS.get())) {
            return ArmorSet.BRASS;
        }
        if (wearing(head, chest, legs, feet, GeneratedMetals.MITHRIL_HELMET.get(), GeneratedMetals.MITHRIL_CHESTPLATE.get(),
                GeneratedMetals.MITHRIL_LEGGINGS.get(), GeneratedMetals.MITHRIL_BOOTS.get())) {
            return ArmorSet.MITHRIL;
        }
        if (wearing(head, chest, legs, feet, GeneratedMetals.AETHER_HELMET.get(), GeneratedMetals.AETHER_CHESTPLATE.get(),
                GeneratedMetals.AETHER_LEGGINGS.get(), GeneratedMetals.AETHER_BOOTS.get())) {
            return ArmorSet.AETHER;
        }
        if (wearing(head, chest, legs, feet, GeneratedMetals.ARCANE_HELMET.get(), GeneratedMetals.ARCANE_CHESTPLATE.get(),
                GeneratedMetals.ARCANE_LEGGINGS.get(), GeneratedMetals.ARCANE_BOOTS.get())) {
            return ArmorSet.ARCANE;
        }
        return ArmorSet.NONE;
    }

    // ------------------------------------------------------------------ set bonuses
    private static void onPlayerTick(TickEvent.PlayerTickEvent.Post event) {
        Player player = event.player();
        if (event.side() != LogicalSide.SERVER || !(player.level() instanceof ServerLevel level)) {
            return;
        }
        if (player.onGround() && !player.isSpectator()) {
            LAST_SAFE.put(player.getUUID(), player.blockPosition());
        }
        boolean inVoid = player.getY() < level.getMinY() - 6;
        if (!inVoid && player.tickCount % 20 != 0) {
            return; // the armour set only matters for a void rescue (every tick) or the bonuses (every second)
        }
        ArmorSet set = fullSet(player);
        if (set == ArmorSet.VOID && inVoid && player instanceof ServerPlayer serverPlayer) {
            rescueFromVoid(level, serverPlayer);
            return;
        }
        if (player.tickCount % 20 != 0) {
            return;
        }
        mithrilModifiers(player, set == ArmorSet.MITHRIL);
        switch (set) {
            case EXPLORER -> {
                player.addEffect(new MobEffectInstance(MobEffects.SPEED, 60, 0, true, false, true));
                if (player.getY() < 50 && !level.canSeeSky(player.blockPosition())) {
                    player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, true));
                }
            }
            case EMBER -> {
                player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 60, 0, true, false, true));
                if (player.isInLava()) {
                    player.addEffect(new MobEffectInstance(MobEffects.SPEED, 40, 2, true, false, true));
                }
            }
            case VOID -> {
                if (!player.onGround() && player.getDeltaMovement().y < -0.6 && !player.isShiftKeyDown()) {
                    player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 40, 0, true, false, true));
                }
            }
            case BRASS -> {
                // the goggles: see in the dark, and the clockwork gauntlets dig faster
                player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, true));
                player.addEffect(new MobEffectInstance(MobEffects.HASTE, 60, 0, true, false, true));
            }
            default -> {
            }
        }
    }

    /** Mithril's +4 health and +10% speed, as modifiers that come and go with the full set. */
    private static void mithrilModifiers(Player player, boolean on) {
        AttributeInstance health = player.getAttribute(Attributes.MAX_HEALTH);
        AttributeInstance speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (health == null || speed == null || health.hasModifier(MITHRIL_HEALTH) == on) {
            return;
        }
        if (on) {
            health.addTransientModifier(new AttributeModifier(MITHRIL_HEALTH, 4.0, AttributeModifier.Operation.ADD_VALUE));
            speed.addTransientModifier(new AttributeModifier(MITHRIL_SPEED, 0.10, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        } else {
            health.removeModifier(MITHRIL_HEALTH);
            speed.removeModifier(MITHRIL_SPEED);
            if (player.getHealth() > player.getMaxHealth()) {
                player.setHealth(player.getMaxHealth());
            }
        }
    }

    private static void rescueFromVoid(ServerLevel level, ServerPlayer player) {
        BlockPos safe = LAST_SAFE.getOrDefault(player.getUUID(), level.getRespawnData().pos());
        player.teleportTo(level, safe.getX() + 0.5, safe.getY() + 1, safe.getZ() + 0.5, Set.of(), player.getYRot(), player.getXRot(), true);
        player.setDeltaMovement(0, 0, 0);
        player.resetFallDistance();
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, player.getX(), player.getY() + 1, player.getZ(), 60, 0.4, 0.8, 0.4, 0.1);
        player.sendSystemMessage(Component.translatable("message.wayfarers.void_saved").withStyle(ChatFormatting.LIGHT_PURPLE));
    }

    private static boolean onFall(LivingFallEvent event) {
        if (!(event.getEntity() instanceof Player player)) {
            return false;
        }
        ArmorSet set = fullSet(player);
        if (set == ArmorSet.AETHER) {
            return true;
        }
        if (set == ArmorSet.EXPLORER) {
            if (event.getDistance() < 8) {
                return true;
            }
            event.setDamageMultiplier(event.getDamageMultiplier() * 0.5F);
        }
        return false;
    }

    // ------------------------------------------------------------------ area tools
    private static void onBreak(BlockEvent.BreakEvent event) {
        if (breakingArea || !(event.getPlayer() instanceof ServerPlayer player) || player.isShiftKeyDown()
                || !(player.level() instanceof ServerLevel level)) {
            return;
        }
        ItemStack tool = player.getMainHandItem();
        BlockPos origin = event.getPos();
        BlockState state = event.getState();
        breakingArea = true;
        try {
            if (tool.is(ModItems.EXCAVATOR_PICKAXE.get()) && tool.isCorrectToolForDrops(state)) {
                mine3x3(level, player, origin, tool);
            } else if (tool.is(ModItems.LUMBER_AXE.get()) && state.is(BlockTags.LOGS)) {
                fellTree(level, player, origin);
            }
        } finally {
            breakingArea = false;
        }
    }

    private static void mine3x3(ServerLevel level, ServerPlayer player, BlockPos origin, ItemStack tool) {
        HitResult hit = player.pick(player.blockInteractionRange(), 1.0F, false);
        Direction face = hit instanceof BlockHitResult bhr ? bhr.getDirection() : Direction.UP;
        for (int a = -1; a <= 1; a++) {
            for (int b = -1; b <= 1; b++) {
                if (a == 0 && b == 0) {
                    continue;
                }
                BlockPos p = switch (face.getAxis()) {
                    case X -> origin.offset(0, a, b);
                    case Y -> origin.offset(a, 0, b);
                    case Z -> origin.offset(a, b, 0);
                };
                BlockState s = level.getBlockState(p);
                if (!s.isAir() && s.getDestroySpeed(level, p) >= 0 && tool.isCorrectToolForDrops(s)) {
                    player.gameMode.destroyBlock(p);
                }
                if (tool.isEmpty()) {
                    return;
                }
            }
        }
    }

    private static void fellTree(ServerLevel level, ServerPlayer player, BlockPos origin) {
        Deque<BlockPos> queue = new ArrayDeque<>();
        Set<BlockPos> seen = new HashSet<>();
        queue.add(origin);
        seen.add(origin);
        int felled = 0;
        while (!queue.isEmpty() && felled < 128) {
            BlockPos p = queue.poll();
            for (int dx = -1; dx <= 1; dx++) {
                for (int dy = 0; dy <= 1; dy++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        BlockPos n = p.offset(dx, dy, dz);
                        if (seen.add(n) && level.getBlockState(n).is(BlockTags.LOGS)) {
                            queue.add(n);
                            player.gameMode.destroyBlock(n);
                            felled++;
                            if (player.getMainHandItem().isEmpty()) {
                                return;
                            }
                        }
                    }
                }
            }
        }
    }
}

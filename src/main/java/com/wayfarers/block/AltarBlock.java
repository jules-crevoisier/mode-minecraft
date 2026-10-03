package com.wayfarers.block;

import com.wayfarers.Wayfarers;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.entity.BossZombie;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import com.wayfarers.registry.ModEntities;
import com.wayfarers.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;

import java.util.function.Supplier;

/** Unbreakable altar placed in boss arenas; offering the right item awakens the boss. */
public class AltarBlock extends Block {
    public enum Boss {
        DROWNED_WARDEN(() -> ModEntities.DROWNED_WARDEN.get(), () -> ModItems.MAP_FRAGMENT.get()),
        VOID_WARDEN(() -> ModEntities.VOID_WARDEN.get(), () -> ModItems.VOID_SHARD.get());

        final Supplier<? extends EntityType<? extends Mob>> type;
        final Supplier<Item> offering;

        Boss(Supplier<? extends EntityType<? extends Mob>> type, Supplier<Item> offering) {
            this.type = type;
            this.offering = offering;
        }
    }

    private final Boss boss;

    public AltarBlock(Properties properties, Boss boss) {
        super(properties);
        this.boss = boss;
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (!(level instanceof ServerLevel serverLevel)) {
            return InteractionResult.SUCCESS;
        }
        Item offering = boss.offering.get();
        if (!stack.is(offering)) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.altar.need",
                    Component.translatable(offering.getDescriptionId())).withStyle(ChatFormatting.GRAY));
            return InteractionResult.SUCCESS;
        }
        EntityType<? extends Mob> type = boss.type.get();
        if (!serverLevel.getEntitiesOfClass(Mob.class, new AABB(pos).inflate(48),
                e -> e instanceof BossZombie || e instanceof WayfarerBoss).isEmpty()) {
            return InteractionResult.FAIL;
        }
        Mob entity = type.create(serverLevel, EntitySpawnReason.TRIGGERED);
        if (entity == null) {
            return InteractionResult.FAIL;
        }
        entity.snapTo(pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 3.5, 180.0F, 0.0F);
        entity.finalizeSpawn(serverLevel, serverLevel.getCurrentDifficultyAt(pos), EntitySpawnReason.TRIGGERED, null);
        entity.setTarget(player);
        if (entity instanceof WayfarerBoss wb) {
            wb.setArena(pos.above(), 24, null);
        }
        // co-op scaling: +60% health per extra player in the arena
        int players = serverLevel.getEntitiesOfClass(Player.class, new AABB(pos).inflate(48), p -> !p.isSpectator()).size();
        if (players > 1) {
            AttributeInstance health = entity.getAttribute(Attributes.MAX_HEALTH);
            if (health != null) {
                health.addPermanentModifier(new AttributeModifier(Wayfarers.id("coop_health"), 0.6 * (players - 1),
                        AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
                entity.setHealth(entity.getMaxHealth());
            }
        }
        serverLevel.addFreshEntity(entity);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        serverLevel.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, pos.getX() + 0.5, pos.getY() + 1.5, pos.getZ() + 0.5,
                80, 0.6, 1.0, 0.6, 0.05);
        serverLevel.playSound(null, pos, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5F, 0.8F);
        serverLevel.getServer().getPlayerList().broadcastSystemMessage(
                Component.translatable("message.wayfarers.altar.awake", entity.getDisplayName()).withStyle(ChatFormatting.RED), false);
        return InteractionResult.SUCCESS;
    }
}

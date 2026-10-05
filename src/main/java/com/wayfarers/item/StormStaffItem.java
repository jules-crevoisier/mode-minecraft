package com.wayfarers.item;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Calls a lightning bolt on the block the player is looking at (up to 48 blocks away). */
public class StormStaffItem extends AbilityItem {
    public StormStaffItem(Properties properties) {
        super(properties, 80, 1);
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        HitResult hit = player.pick(48.0, 1.0F, false);
        if (hit.getType() == HitResult.Type.MISS) {
            noTarget(player);
            return false;
        }
        Vec3 at = hit.getLocation();
        LightningBolt bolt = EntityTypes.LIGHTNING_BOLT.create(level, EntitySpawnReason.TRIGGERED);
        if (bolt == null) {
            return false;
        }
        bolt.snapTo(Vec3.atBottomCenterOf(BlockPos.containing(at)));
        if (player instanceof ServerPlayer serverPlayer) {
            bolt.setCause(serverPlayer);
        }
        BlockPos strike = BlockPos.containing(at);
        if (com.wayfarers.config.WayfarersConfig.STORM_STAFF_GRIEF.get()) {
            if (!level.mayInteract(player, strike)) { // spawn protection: no fire there
                noTarget(player);
                return false;
            }
            level.addFreshEntity(bolt);
            return true;
        }
        // server default: the bolt is only light and sound; it strikes the monsters around (like every other
        // ability, never players, pets or villagers) and starts no fire
        bolt.setVisualOnly(true);
        level.addFreshEntity(bolt);
        for (net.minecraft.world.entity.LivingEntity e : level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class,
                new net.minecraft.world.phys.AABB(strike).inflate(3.0, 6.0, 3.0), e -> com.wayfarers.util.Targets.foe(player, e))) {
            e.hurtServer(level, level.damageSources().lightningBolt(), 5.0F);
        }
        return true;
    }
}

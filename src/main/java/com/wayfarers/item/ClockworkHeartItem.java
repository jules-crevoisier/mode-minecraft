package com.wayfarers.item;

import com.wayfarers.entity.automaton.BrassGolem;
import com.wayfarers.generated.GeneratedMetals;
import com.wayfarers.registry.ModEntities;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Clockwork Heart: right-click a pillar of two Blocks of Brass (either block) to wind it into a Brass Golem that
 * follows its builder. The blocks and the heart are consumed.
 */
public class ClockworkHeartItem extends TooltipItem {
    public ClockworkHeartItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos clicked = context.getClickedPos();
        Block brass = GeneratedMetals.BRASS_BLOCK.get();
        BlockPos bottom;
        if (level.getBlockState(clicked).is(brass) && level.getBlockState(clicked.below()).is(brass)) {
            bottom = clicked.below();
        } else if (level.getBlockState(clicked).is(brass) && level.getBlockState(clicked.above()).is(brass)) {
            bottom = clicked;
        } else {
            if (level.getBlockState(clicked).is(brass) && context.getPlayer() != null && !level.isClientSide()) {
                context.getPlayer().sendOverlayMessage(Component.translatable("message.wayfarers.brass_golem.need")
                        .withStyle(ChatFormatting.GOLD));
            }
            return InteractionResult.PASS;
        }
        Player player = context.getPlayer();
        if (player != null && !player.mayBuild()) {
            return InteractionResult.PASS; // adventure mode: it would break the blocks
        }
        // the golem is wider than a block (and 2.3 tall): find a spot where it does not stand in a wall, or it
        // would suffocate; slide it a little away from a neighbouring wall if needed
        Vec3 spot = null;
        for (double[] o : NUDGES) {
            Vec3 p = new Vec3(bottom.getX() + 0.5 + o[0], bottom.getY(), bottom.getZ() + 0.5 + o[1]);
            if (hasRoom(level, ModEntities.BRASS_GOLEM.get().getDimensions().makeBoundingBox(p), bottom)) {
                spot = p;
                break;
            }
        }
        if (spot == null) {
            if (player != null && !level.isClientSide()) {
                player.sendOverlayMessage(Component.translatable("message.wayfarers.brass_golem.room").withStyle(ChatFormatting.GOLD));
            }
            return InteractionResult.FAIL;
        }
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        BrassGolem golem = ModEntities.BRASS_GOLEM.get().create(server, EntitySpawnReason.TRIGGERED);
        if (golem == null) {
            return InteractionResult.FAIL;
        }
        level.setBlock(bottom.above(), Blocks.AIR.defaultBlockState(), 3);
        level.setBlock(bottom, Blocks.AIR.defaultBlockState(), 3);
        float yaw = player == null ? 0.0F : player.getYRot() + 180.0F;
        golem.snapTo(spot.x, spot.y, spot.z, yaw, 0.0F);
        server.addFreshEntity(golem);
        if (player != null) {
            golem.setBuilder(player);
            player.sendSystemMessage(Component.translatable("message.wayfarers.brass_golem.built").withStyle(ChatFormatting.GOLD));
        }
        context.getItemInHand().consume(1, player);
        server.sendParticles(ParticleTypes.CLOUD, golem.getX(), golem.getY() + 1.2, golem.getZ(), 30, 0.5, 0.8, 0.5, 0.05);
        server.sendParticles(ParticleTypes.ELECTRIC_SPARK, golem.getX(), golem.getY() + 1.2, golem.getZ(), 30, 0.5, 0.8, 0.5, 0.2);
        server.playSound(null, bottom, SoundEvents.PISTON_EXTEND, SoundSource.NEUTRAL, 1.0F, 0.7F);
        server.playSound(null, bottom, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.NEUTRAL, 1.0F, 1.2F);
        server.playSound(null, bottom, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.NEUTRAL, 1.0F, 0.8F);
        return InteractionResult.SUCCESS;
    }

    private static final double[][] NUDGES = {{0, 0}, {0.16, 0}, {-0.16, 0}, {0, 0.16}, {0, -0.16},
            {0.16, 0.16}, {0.16, -0.16}, {-0.16, 0.16}, {-0.16, -0.16}};

    /** No block collides with {@code box}, except the two Blocks of Brass the golem is made of. */
    private static boolean hasRoom(Level level, AABB box, BlockPos bottom) {
        AABB lower = new AABB(bottom);
        AABB upper = new AABB(bottom.above());
        for (VoxelShape shape : level.getBlockCollisions(null, box)) {
            AABB bounds = shape.bounds();
            if (!bounds.equals(lower) && !bounds.equals(upper)) {
                return false;
            }
        }
        return true;
    }
}

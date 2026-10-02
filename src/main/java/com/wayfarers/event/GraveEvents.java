package com.wayfarers.event;

import com.wayfarers.block.GraveBlock;
import com.wayfarers.block.GraveBlockEntity;
import com.wayfarers.registry.ModBlocks;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.entity.living.LivingDropsEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/** Death no longer scatters your items: they are stored in a grave at the place of death. */
public final class GraveEvents {
    private GraveEvents() {}

    public static void register() {
        LivingDropsEvent.BUS.addListener((Predicate<LivingDropsEvent>) GraveEvents::onDrops);
    }

    private static boolean onDrops(LivingDropsEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || event.getDrops().isEmpty()
                || !(player.level() instanceof ServerLevel level)) {
            return false;
        }
        BlockPos pos = findSpot(level, player.blockPosition());
        if (pos == null) {
            return false;
        }
        BlockState state = ModBlocks.GRAVE.get().defaultBlockState()
                .setValue(GraveBlock.FACING, Direction.fromYRot(player.getYRot()).getOpposite());
        level.setBlock(pos, state, Block.UPDATE_ALL);
        if (!(level.getBlockEntity(pos) instanceof GraveBlockEntity grave)) {
            return false;
        }
        List<ItemStack> stacks = new ArrayList<>();
        for (ItemEntity drop : event.getDrops()) {
            stacks.add(drop.getItem());
        }
        grave.fill(player, stacks);
        player.sendSystemMessage(Component.translatable("message.wayfarers.grave", pos.getX(), pos.getY(), pos.getZ(),
                level.dimension().identifier().getPath()).withStyle(ChatFormatting.YELLOW));
        return true; // cancel the vanilla drops: everything is in the grave
    }

    private static BlockPos findSpot(ServerLevel level, BlockPos death) {
        int y = Math.max(level.getMinY() + 1, Math.min(level.getMaxY() - 1, death.getY()));
        BlockPos start = new BlockPos(death.getX(), y, death.getZ());
        for (int dy = 0; dy < 24; dy++) {
            for (int sign : new int[]{1, -1}) {
                BlockPos p = start.above(dy * sign);
                if (p.getY() <= level.getMinY() || p.getY() >= level.getMaxY()) {
                    continue;
                }
                BlockState s = level.getBlockState(p);
                if (s.isAir() || s.canBeReplaced()) {
                    return p;
                }
            }
        }
        return null;
    }
}

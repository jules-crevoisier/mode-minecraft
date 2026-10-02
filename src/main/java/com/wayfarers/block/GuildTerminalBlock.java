package com.wayfarers.block;

import com.mojang.serialization.MapCodec;
import com.wayfarers.util.InventoryUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;

import java.util.ArrayList;
import java.util.List;

/**
 * "Quick stack to nearby chests": every item of the main inventory that already exists in a
 * chest within range goes there. Sneak-use sorts every chest in range instead.
 */
public class GuildTerminalBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<GuildTerminalBlock> CODEC = simpleCodec(GuildTerminalBlock::new);
    public static final int RANGE = 10;

    public GuildTerminalBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!(level instanceof ServerLevel serverLevel)) {
            return InteractionResult.SUCCESS;
        }
        List<Container> chests = nearbyStorage(serverLevel, pos);
        if (chests.isEmpty()) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.terminal.nothing", RANGE)
                    .withStyle(ChatFormatting.GRAY));
            return InteractionResult.SUCCESS;
        }
        if (player.isShiftKeyDown()) {
            chests.forEach(InventoryUtil::sortContainer);
            player.sendSystemMessage(Component.translatable("message.wayfarers.terminal.sorted", chests.size())
                    .withStyle(ChatFormatting.GOLD));
        } else {
            int[] result = deposit(player, chests);
            player.sendSystemMessage(Component.translatable("message.wayfarers.terminal.deposit", result[0], result[1])
                    .withStyle(ChatFormatting.GOLD));
        }
        serverLevel.sendParticles(ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5,
                12, 0.3, 0.2, 0.3, 0.0);
        level.playSound(null, pos, SoundEvents.BARREL_CLOSE, SoundSource.BLOCKS, 0.8F, 1.2F);
        return InteractionResult.SUCCESS;
    }

    /** Moves main-inventory items (not hotbar/armor) into chests that already hold them. */
    public static int[] deposit(Player player, List<Container> chests) {
        NonNullList<ItemStack> inv = player.getInventory().getNonEquipmentItems();
        int moved = 0;
        java.util.Set<Container> touched = new java.util.HashSet<>();
        for (int slot = 9; slot < inv.size(); slot++) {
            ItemStack stack = inv.get(slot);
            if (stack.isEmpty()) {
                continue;
            }
            for (Container chest : chests) {
                if (!InventoryUtil.contains(chest, stack)) {
                    continue;
                }
                ItemStack rest = InventoryUtil.insert(chest, stack, false);
                if (rest.getCount() != stack.getCount()) {
                    moved += stack.getCount() - rest.getCount();
                    touched.add(chest);
                    stack = rest;
                    inv.set(slot, rest);
                }
                if (stack.isEmpty()) {
                    break;
                }
            }
        }
        player.getInventory().setChanged();
        return new int[]{moved, touched.size()};
    }

    public static List<Container> nearbyStorage(ServerLevel level, BlockPos center) {
        List<Container> result = new ArrayList<>();
        for (BlockPos p : BlockPos.betweenClosed(center.offset(-RANGE, -RANGE / 2, -RANGE), center.offset(RANGE, RANGE / 2, RANGE))) {
            BlockEntity be = level.getBlockEntity(p);
            if (be instanceof BaseContainerBlockEntity container && container.getContainerSize() >= 27) {
                result.add(container);
            }
        }
        return result;
    }
}

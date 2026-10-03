package com.wayfarers.block;

import com.mojang.serialization.MapCodec;
import com.wayfarers.util.InventoryUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Compacting Crate, used like a Storage Drawer: right-click with an item to put it in (right-click again quickly
 * to put in every one you carry), left-click to take a stack (sneak: one item), empty-hand right-click to read
 * the count.
 */
public class CrateBlock extends BaseEntityBlock {
    public static final MapCodec<CrateBlock> CODEC = simpleCodec(CrateBlock::new);
    private static final Map<UUID, Long> LAST_INSERT = new HashMap<>();

    public CrateBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(HorizontalDirectionalBlock.FACING, Direction.NORTH));
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(HorizontalDirectionalBlock.FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new CrateBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    private static void tell(Player player, CrateBlockEntity crate) {
        if (player instanceof ServerPlayer sp) {
            ItemStack kind = crate.kind();
            Component msg = kind.isEmpty() ? Component.translatable("message.wayfarers.crate.empty")
                    : Component.translatable("message.wayfarers.crate.count", kind.getHoverName(), crate.total(),
                    CrateBlockEntity.SIZE * kind.getMaxStackSize());
            sp.sendOverlayMessage(msg.copy().withStyle(ChatFormatting.GOLD));
        }
    }

    @Override
    protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          InteractionHand hand, BlockHitResult hit) {
        if (stack.isEmpty()) {
            return InteractionResult.TRY_WITH_EMPTY_HAND;
        }
        if (!level.isClientSide() && level.getBlockEntity(pos) instanceof CrateBlockEntity crate) {
            if (!crate.canPlaceItem(0, stack)) {
                tell(player, crate);
                return InteractionResult.SUCCESS;
            }
            long now = level.getGameTime();
            Long last = LAST_INSERT.put(player.getUUID(), now);
            ItemStack kind = stack.copyWithCount(1);
            player.setItemInHand(hand, InventoryUtil.insert(crate, stack, false));
            if (last != null && now - last <= 10) {
                // double-click: every matching stack of the inventory goes in
                Inventory inv = player.getInventory();
                for (int i = 0; i < inv.getContainerSize(); i++) {
                    ItemStack s = inv.getItem(i);
                    if (ItemStack.isSameItemSameComponents(s, kind)) {
                        inv.setItem(i, InventoryUtil.insert(crate, s, false));
                    }
                }
            }
            level.playSound(null, pos, SoundEvents.BUNDLE_INSERT, SoundSource.BLOCKS, 0.8F, 1.0F);
            tell(player, crate);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!level.isClientSide() && level.getBlockEntity(pos) instanceof CrateBlockEntity crate) {
            tell(player, crate);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    protected void attack(BlockState state, Level level, BlockPos pos, Player player) {
        if (level.isClientSide() || !(level.getBlockEntity(pos) instanceof CrateBlockEntity crate)) {
            return;
        }
        ItemStack kind = crate.kind();
        if (kind.isEmpty()) {
            return;
        }
        int want = player.isShiftKeyDown() ? 1 : kind.getMaxStackSize();
        ItemStack taken = ItemStack.EMPTY;
        for (int i = CrateBlockEntity.SIZE - 1; i >= 0 && want > 0; i--) {
            ItemStack part = crate.removeItem(i, want);
            if (!part.isEmpty()) {
                want -= part.getCount();
                taken = taken.isEmpty() ? part : taken.copyWithCount(taken.getCount() + part.getCount());
            }
        }
        if (!taken.isEmpty()) {
            player.getInventory().placeItemBackInInventory(taken);
            level.playSound(null, pos, SoundEvents.BUNDLE_REMOVE_ONE, SoundSource.BLOCKS, 0.8F, 1.0F);
            tell(player, crate);
        }
    }
}

package com.wayfarers.item;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Builder's Wand (Construction Wand style): right-click a block face to extend that face by up to
 * {@code maxBlocks} copies of the block (same orientation), using blocks from your inventory. Holding it
 * shows an outline of where the blocks will go. Sneak-right-click in the air undoes the last use.
 */
public class BuilderWandItem extends TooltipItem {
    private record Undo(ResourceKey<Level> dimension, List<BlockPos> positions, BlockState state) {}

    private static final Map<UUID, Undo> UNDO = new HashMap<>();

    private final int maxBlocks;

    public BuilderWandItem(Properties properties, int maxBlocks) {
        super(properties);
        this.maxBlocks = maxBlocks;
    }

    public int maxBlocks() {
        return maxBlocks;
    }

    /** Where the wand would place blocks when used on {@code pos}/{@code face} (shared by preview and use). */
    public static List<BlockPos> targets(Level level, Player player, BlockPos pos, Direction face, int max) {
        BlockState source = level.getBlockState(pos);
        Item item = source.getBlock().asItem();
        if (source.isAir() || !(item instanceof BlockItem) || source.hasBlockEntity()) {
            return List.of();
        }
        int budget = player.isCreative() ? max : Math.min(max, count(player.getInventory(), item));
        List<BlockPos> out = new ArrayList<>();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(pos);
        seen.add(pos);
        Direction[] spread = java.util.Arrays.stream(Direction.values()).filter(d -> d.getAxis() != face.getAxis())
                .toArray(Direction[]::new);
        while (!queue.isEmpty() && out.size() < budget) {
            BlockPos p = queue.poll();
            BlockPos target = p.relative(face);
            if (!level.getBlockState(p).is(source.getBlock()) || !level.getBlockState(target).canBeReplaced()
                    || !level.getEntitiesOfClass(net.minecraft.world.entity.LivingEntity.class, new AABB(target)).isEmpty()) {
                continue;
            }
            out.add(target);
            for (Direction d : spread) {
                BlockPos n = p.relative(d);
                if (seen.add(n) && n.distManhattan(pos) <= max) {
                    queue.add(n);
                }
            }
        }
        return out;
    }

    private static int count(Inventory inv, Item item) {
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (inv.getItem(i).is(item)) {
                n += inv.getItem(i).getCount();
            }
        }
        return n;
    }

    private static void consume(Inventory inv, Item item, int amount) {
        for (int i = 0; i < inv.getContainerSize() && amount > 0; i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(item)) {
                int take = Math.min(amount, s.getCount());
                s.shrink(take);
                amount -= take;
            }
        }
    }

    @Override
    public InteractionResult useOn(UseOnContext ctx) {
        Level level = ctx.getLevel();
        Player player = ctx.getPlayer();
        if (player == null) {
            return InteractionResult.PASS;
        }
        BlockPos pos = ctx.getClickedPos();
        List<BlockPos> targets = targets(level, player, pos, ctx.getClickedFace(), maxBlocks);
        if (targets.isEmpty()) {
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server) {
            BlockState state = level.getBlockState(pos);
            for (BlockPos t : targets) {
                server.setBlock(t, state, Block.UPDATE_ALL);
            }
            if (!player.isCreative()) {
                consume(player.getInventory(), state.getBlock().asItem(), targets.size());
                ctx.getItemInHand().hurtAndBreak(1, player, ctx.getHand() == InteractionHand.MAIN_HAND
                        ? net.minecraft.world.entity.EquipmentSlot.MAINHAND : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
            }
            UNDO.put(player.getUUID(), new Undo(level.dimension(), List.copyOf(targets), state));
            var sound = state.getSoundType().getPlaceSound();
            level.playSound(null, pos, sound, SoundSource.BLOCKS, 1.0F, 0.9F);
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!player.isShiftKeyDown()) {
            return InteractionResult.PASS;
        }
        if (level instanceof ServerLevel server) {
            Undo undo = UNDO.remove(player.getUUID());
            if (undo == null || !undo.dimension().equals(level.dimension())) {
                player.sendOverlayMessage(Component.translatable("message.wayfarers.wand.nothing").withStyle(ChatFormatting.GRAY));
                return InteractionResult.SUCCESS;
            }
            int restored = 0;
            for (BlockPos p : undo.positions()) {
                if (server.getBlockState(p) == undo.state()) {
                    server.removeBlock(p, false);
                    restored++;
                }
            }
            if (!player.isCreative() && restored > 0) {
                player.getInventory().placeItemBackInInventory(new ItemStack(undo.state().getBlock().asItem(), restored));
            }
            player.sendOverlayMessage(Component.translatable("message.wayfarers.wand.undone", restored).withStyle(ChatFormatting.GOLD));
        }
        return InteractionResult.SUCCESS;
    }
}

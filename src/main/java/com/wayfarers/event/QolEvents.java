package com.wayfarers.event;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CocoaBlock;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.NetherWartBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingEntityUseItemEvent;
import net.minecraftforge.event.entity.player.PlayerDestroyItemEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.fml.LogicalSide;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * "Vanilla Enhanced" quality of life:
 * <ul>
 *     <li>Hotbar refill: when the stack in your hand runs out (last block placed, last food eaten, tool
 *     broken), the next stack of the same item from your inventory takes its place.</li>
 *     <li>Right-click harvest: right-click a ripe crop to harvest it and replant it in one go.</li>
 * </ul>
 */
public final class QolEvents {
    private record Pending(int slot, Item item) {}

    private static final Map<UUID, List<Pending>> PENDING = new HashMap<>();

    private QolEvents() {}

    public static void register() {
        PlayerDestroyItemEvent.BUS.addListener(QolEvents::onBreakTool);
        LivingEntityUseItemEvent.Finish.BUS.addListener(QolEvents::onFinishUse);
        BlockEvent.EntityPlaceEvent.BUS.addListener((Consumer<BlockEvent.EntityPlaceEvent>) QolEvents::onPlace);
        TickEvent.PlayerTickEvent.Post.BUS.addListener(QolEvents::onPlayerTick);
        PlayerInteractEvent.RightClickBlock.BUS.addListener((Predicate<PlayerInteractEvent.RightClickBlock>) QolEvents::onRightClick);
    }

    // ------------------------------------------------------------------ hotbar refill
    private static int handSlot(Player player, InteractionHand hand) {
        return hand == InteractionHand.OFF_HAND ? Inventory.SLOT_OFFHAND : player.getInventory().getSelectedSlot();
    }

    private static void watch(Player player, InteractionHand hand, Item item) {
        if (player instanceof ServerPlayer && item != Items.AIR) {
            PENDING.computeIfAbsent(player.getUUID(), k -> new ArrayList<>()).add(new Pending(handSlot(player, hand), item));
        }
    }

    private static void onBreakTool(PlayerDestroyItemEvent event) {
        Player player = event.getEntity();
        if (event.getSlot() == net.minecraft.world.entity.EquipmentSlot.MAINHAND) {
            watch(player, InteractionHand.MAIN_HAND, event.getOriginal().getItem());
        } else if (event.getSlot() == net.minecraft.world.entity.EquipmentSlot.OFFHAND) {
            watch(player, InteractionHand.OFF_HAND, event.getOriginal().getItem());
        }
    }

    private static void onFinishUse(LivingEntityUseItemEvent.Finish event) {
        if (event.getEntity() instanceof Player player) {
            watch(player, player.getUsedItemHand(), event.getItem().getItem());
        }
    }

    private static void onPlace(BlockEvent.EntityPlaceEvent event) {
        if (event.getEntity() instanceof Player player && !com.wayfarers.util.ServerGuard.probing()) {
            for (InteractionHand hand : InteractionHand.values()) {
                ItemStack held = player.getItemInHand(hand);
                if (held.getItem() instanceof BlockItem bi && bi.getBlock() == event.getPlacedBlock().getBlock()) {
                    watch(player, hand, held.getItem());
                    return;
                }
            }
        }
    }

    private static void onPlayerTick(TickEvent.PlayerTickEvent.Post event) {
        if (event.side() != LogicalSide.SERVER || !(event.player() instanceof ServerPlayer player)) {
            return;
        }
        List<Pending> pending = PENDING.remove(player.getUUID());
        if (pending == null) {
            return;
        }
        Inventory inv = player.getInventory();
        for (Pending p : pending) {
            if (!inv.getItem(p.slot()).isEmpty()) {
                continue;
            }
            for (int i = Inventory.getSelectionSize(); i < 36; i++) {
                ItemStack candidate = inv.getItem(i);
                if (!candidate.isEmpty() && candidate.getItem() == p.item()) {
                    inv.setItem(p.slot(), candidate);
                    inv.setItem(i, ItemStack.EMPTY);
                    player.level().playSound(null, player, SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 0.3F, 1.6F);
                    break;
                }
            }
        }
    }

    // ------------------------------------------------------------------ right-click harvest
    private static boolean onRightClick(PlayerInteractEvent.RightClickBlock event) {
        Player player = event.getEntity();
        if (player.isShiftKeyDown() || event.getHand() != InteractionHand.MAIN_HAND || player.isSpectator()) {
            return false;
        }
        ItemStack held = player.getMainHandItem();
        if (held.is(Items.BONE_MEAL)) {
            return false;
        }
        BlockPos pos = event.getPos();
        BlockState state = event.getLevel().getBlockState(pos);
        BlockState replant = replanted(state);
        if (replant == null) {
            return false;
        }
        // like breaking the crop by hand: adventure mode, spawn protection and claim mods apply
        if (!player.mayBuild() || !event.getLevel().mayInteract(player, pos)
                || player instanceof ServerPlayer sp && !com.wayfarers.util.ServerGuard.mayBreak(sp.level(), pos, sp)) {
            return false;
        }
        if (event.getLevel() instanceof ServerLevel level) {
            List<ItemStack> drops = Block.getDrops(state, level, pos, level.getBlockEntity(pos), player, held);
            Item seed = state.getBlock().asItem();
            boolean seedTaken = false;
            for (ItemStack drop : drops) {
                if (!seedTaken && drop.getItem() == seed) {
                    drop.shrink(1);
                    seedTaken = true;
                }
                if (!drop.isEmpty()) {
                    Block.popResource(level, pos, drop);
                }
            }
            level.setBlock(pos, replant, Block.UPDATE_ALL);
            level.playSound(null, pos, SoundEvents.CROP_BREAK, SoundSource.BLOCKS, 1.0F, 1.0F);
        }
        event.setCancellationResult(InteractionResult.SUCCESS);
        return true;
    }

    /** The young state to replant if this block is a ripe crop, else null. */
    public static BlockState replanted(BlockState state) {
        Block block = state.getBlock();
        if (block instanceof CropBlock crop && crop.isMaxAge(state)) {
            return crop.getStateForAge(0);
        }
        if (block == Blocks.NETHER_WART && state.getValue(NetherWartBlock.AGE) >= 3) {
            return state.setValue(NetherWartBlock.AGE, 0);
        }
        if (block == Blocks.COCOA && state.getValue(CocoaBlock.AGE) >= 2) {
            return state.setValue(CocoaBlock.AGE, 0);
        }
        return null;
    }
}

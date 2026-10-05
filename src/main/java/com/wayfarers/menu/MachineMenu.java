package com.wayfarers.menu;

import com.wayfarers.block.MachineBlock;
import com.wayfarers.block.MachineBlockEntity;
import com.wayfarers.registry.ModMenus;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * The screen of every machine. Settings and live status travel as data slots ({@link #D_RADIUS}...); the client
 * changes a setting with a menu button click ({@link #button}), which the server validates
 * ({@link MachineBlockEntity#applySetting}) after the vanilla distance check ({@link #stillValid}).
 * Slots: the 9-slot buffer (machines that store items), the Vacuum Hopper's ghost filter, the Breaker / Placer
 * preview of what comes next (read-only), then the player inventory.
 */
public class MachineMenu extends AbstractContainerMenu {
    // ---- data slots (shorts on the wire)
    public static final int D_RADIUS = 0;
    public static final int D_REDSTONE = 1;
    public static final int D_STATUS = 2;
    public static final int D_STATUS_ARG = 3;
    public static final int D_CHANNEL = 4;
    /** bits: 1 replant, 2 collect XP, 4 whitelist, 8 inverted, 16 redstone input, 32 output / powered. */
    public static final int D_FLAGS = 5;
    public static final int D_TARGET = 6;
    public static final int D_OUTPUT = 7;
    public static final int D_INTERVAL = 8;
    public static final int D_PULSE = 9;
    public static final int D_COUNTDOWN = 10;
    public static final int D_XP = 11;
    /** Detector: creatures in range; transmitter / receiver: transmitters on the channel. */
    public static final int D_COUNT_A = 12;
    /** Transmitter / receiver: receivers on the channel. */
    public static final int D_COUNT_B = 13;
    /** Neighbouring containers, one bit per Direction.get3DDataValue(). */
    public static final int D_SIDES = 14;
    public static final int DATA_COUNT = 15;

    // ---- button actions: id = action * 100 + value
    public static final int A_RADIUS = 1;
    public static final int A_REDSTONE = 2;
    public static final int A_CHANNEL = 3;
    public static final int A_TOGGLE = 4;
    public static final int A_TARGET = 5;
    public static final int A_OUTPUT = 6;
    public static final int A_INTERVAL = 7;
    public static final int A_PULSE = 8;
    public static final int A_TAKE_XP = 9;
    public static final int T_REPLANT = 0;
    public static final int T_COLLECT_XP = 1;
    public static final int T_WHITELIST = 2;
    public static final int T_INVERTED = 3;

    // ---- layout (GUI pixels from the window's top-left; slot positions are the 18x18 frames)
    public static final int W = 252;
    public static final int STATUS_Y = 36;
    public static final int ROW_Y0 = 55;
    public static final int ROW_H = 20;
    public static final int LABEL_X = 10;
    /** Where the controls of a settings row start (labels get the 56 px before). */
    public static final int CX = 66;
    public static final int BUF_X = W - 10 - 54;
    public static final int BUF_Y = 67;
    public static final int INV_X = (W - 162) / 2;
    public static final int FILTER_ROW = 2;
    public static final int FILTER_X = CX + 22;

    public final MachineBlock.Kind kind;
    public final BlockPos pos;
    private final @Nullable MachineBlockEntity machine;
    private final ContainerData data;
    private final Container filter;
    private final SimpleContainer preview = new SimpleContainer(1);
    private int bufferStart = -1;
    private int filterStart = -1;
    private int previewSlot = -1;
    private int invStart;

    /** Client side, from the open-screen packet. */
    public MachineMenu(int id, Inventory inv, FriendlyByteBuf buf) {
        this(id, inv, buf.readBlockPos(), MachineBlock.Kind.byId(buf.readVarInt()), null, new SimpleContainer(MachineBlockEntity.SIZE),
                new SimpleContainer(MachineBlockEntity.FILTER_SIZE), new SimpleContainerData(DATA_COUNT));
    }

    /** Server side. */
    public MachineMenu(int id, Inventory inv, MachineBlockEntity machine) {
        this(id, inv, machine.getBlockPos(), machine.kind(), machine, machine, machine.filter, machine.data);
    }

    private MachineMenu(int id, Inventory inv, BlockPos pos, MachineBlock.Kind kind, @Nullable MachineBlockEntity machine,
                        Container buffer, Container filter, ContainerData data) {
        super(ModMenus.MACHINE.get(), id);
        this.kind = kind;
        this.pos = pos;
        this.machine = machine;
        this.data = data;
        this.filter = filter;
        if (kind.hasInventory) {
            bufferStart = slots.size();
            for (int i = 0; i < MachineBlockEntity.SIZE; i++) {
                addSlot(new Slot(buffer, i, BUF_X + 1 + (i % 3) * 18, BUF_Y + 1 + (i / 3) * 18));
            }
        }
        if (kind == MachineBlock.Kind.VACUUM) {
            filterStart = slots.size();
            int y = ROW_Y0 + FILTER_ROW * ROW_H + 1;
            for (int i = 0; i < MachineBlockEntity.FILTER_SIZE; i++) {
                addSlot(new GhostSlot(filter, i, FILTER_X + 1 + i * 18, y));
            }
        }
        if (kind == MachineBlock.Kind.BREAKER || kind == MachineBlock.Kind.PLACER) {
            previewSlot = slots.size();
            addSlot(new GhostSlot(preview, 0, CX + 1, ROW_Y0 + 1));
        }
        invStart = slots.size();
        if (kind.hasInventory) {
            addStandardInventorySlots(inv, INV_X + 1, invY(kind) + 1);
        }
        addDataSlots(data);
    }

    /** Settings rows of each machine's screen. */
    public static int rows(MachineBlock.Kind kind) {
        return switch (kind) {
            case HARVESTER, VACUUM, TIMER -> 4;
            case SPRINKLER -> 2;
            default -> 3;
        };
    }

    public static int rowY(int row) {
        return ROW_Y0 + row * ROW_H;
    }

    private static int contentBottom(MachineBlock.Kind kind) {
        int rows = rowY(rows(kind));
        return kind.hasInventory ? Math.max(rows, BUF_Y + 54) : rows;
    }

    /** Top of the player inventory frames. */
    public static int invY(MachineBlock.Kind kind) {
        return contentBottom(kind) + 8;
    }

    public static int height(MachineBlock.Kind kind) {
        return kind.hasInventory ? invY(kind) + 76 + 7 : contentBottom(kind) + 5;
    }

    public static int button(int action, int value) {
        return action * 100 + value;
    }

    public int get(int index) {
        return data.get(index);
    }

    public boolean flag(int bit) {
        return (data.get(D_FLAGS) & bit) != 0;
    }

    public MachineBlockEntity.Status status() {
        return MachineBlockEntity.Status.byId(data.get(D_STATUS));
    }

    public ItemStack preview() {
        return preview.getItem(0);
    }

    public boolean isFilterSlot(Slot slot) {
        return filterStart >= 0 && slot.index >= filterStart && slot.index < filterStart + MachineBlockEntity.FILTER_SIZE;
    }

    public boolean isPreviewSlot(Slot slot) {
        return slot.index == previewSlot;
    }

    public boolean isBufferSlot(Slot slot) {
        return bufferStart >= 0 && slot.index >= bufferStart && slot.index < bufferStart + MachineBlockEntity.SIZE;
    }

    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (machine == null || !(player instanceof ServerPlayer sp) || id < 0
                || !com.wayfarers.util.ServerGuard.allow(sp, "machine_button", 10, 10.0)) {
            return false;
        }
        return machine.applySetting(sp, id / 100, id % 100);
    }

    @Override
    public void broadcastChanges() {
        if (machine != null && machine.getLevel() instanceof ServerLevel level) {
            if (level.getGameTime() % 10 == 0) {
                machine.refreshStatus(level);
            }
            if (!ItemStack.matches(preview.getItem(0), machine.preview())) {
                preview.setItem(0, machine.preview().copy());
            }
        }
        super.broadcastChanges();
    }

    @Override
    public void clicked(int slotIndex, int button, ContainerInput action, Player player) {
        if (slotIndex >= 0 && slotIndex < slots.size()) {
            Slot slot = slots.get(slotIndex);
            if (isPreviewSlot(slot)) {
                return;
            }
            if (isFilterSlot(slot)) {
                // ghost slot: holds a copy of the carried item (never the item itself); an empty hand clears it
                if (action == ContainerInput.PICKUP || action == ContainerInput.QUICK_MOVE) {
                    ItemStack carried = getCarried();
                    filter.setItem(slot.getContainerSlot(),
                            carried.isEmpty() || action == ContainerInput.QUICK_MOVE ? ItemStack.EMPTY : carried.copyWithCount(1));
                }
                return;
            }
        }
        super.clicked(slotIndex, button, action, player);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem() || isFilterSlot(slot) || isPreviewSlot(slot)) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (isBufferSlot(slot)) {
            if (!moveItemStackTo(stack, invStart, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (bufferStart < 0 || !moveItemStackTo(stack, bufferStart, bufferStart + MachineBlockEntity.SIZE, false)) {
            // buffer full: shuffle between main inventory and hotbar like vanilla
            int hotbar = slots.size() - 9;
            if (index < hotbar ? !moveItemStackTo(stack, hotbar, slots.size(), false)
                    : !moveItemStackTo(stack, invStart, hotbar, false)) {
                return ItemStack.EMPTY;
            }
        }
        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        if (stack.getCount() == copy.getCount()) {
            return ItemStack.EMPTY;
        }
        slot.onTake(player, stack);
        return copy;
    }

    @Override
    public boolean canTakeItemForPickAll(ItemStack carried, Slot target) {
        return !isFilterSlot(target) && !isPreviewSlot(target) && super.canTakeItemForPickAll(carried, target);
    }

    @Override
    public boolean canDragTo(Slot slot) {
        return !isFilterSlot(slot) && !isPreviewSlot(slot);
    }

    @Override
    public boolean stillValid(Player player) {
        return machine == null || machine.stillValid(player);
    }

    /** A display-only slot: never gives or takes a real item (filter copies, previews). */
    private static final class GhostSlot extends Slot {
        GhostSlot(Container container, int index, int x, int y) {
            super(container, index, x, y);
        }

        @Override
        public boolean mayPlace(ItemStack stack) {
            return false;
        }

        @Override
        public boolean mayPickup(Player player) {
            return false;
        }

        @Override
        public int getMaxStackSize() {
            return 1;
        }
    }
}

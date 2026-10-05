package com.wayfarers.social;

import com.wayfarers.registry.ModSocial;
import net.minecraft.network.FriendlyByteBuf;
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

/**
 * One side of a trade: your offer (9 real slots, held by the trade session, not by you), the other player's offer
 * (9 slots you can look at but never touch), your inventory, and two buttons (accept / cancel) sent as vanilla
 * menu-button clicks. The state (who accepted, the countdown, a problem) is synced with data slots.
 */
public class TradeMenu extends AbstractContainerMenu {
    public static final int W = 212;
    public static final int H = 214;
    public static final int MY_X = 14;
    public static final int THEIR_X = W - 14 - 54;
    public static final int GRID_Y = 34;
    public static final int INV_X = (W - 162) / 2;
    public static final int INV_Y = 132;
    public static final int OFFER = 9;
    public static final int BUTTON_ACCEPT = 0;
    public static final int BUTTON_CANCEL = 1;
    /** Data slots: 0 you accepted, 1 they accepted, 2 countdown ticks left (0: none), 3 problem (0 none, 1 your bag, 2 theirs). */
    public static final int DATA = 4;

    private final Container mine;
    private final Container theirs;
    private final ContainerData state;
    private final Trade.Session session;
    private final int side;
    public final String partner;

    /** Client side. */
    public TradeMenu(int id, Inventory inv, FriendlyByteBuf buf) {
        this(id, inv, new SimpleContainer(OFFER), new SimpleContainer(OFFER), new SimpleContainerData(DATA), null, 0,
                buf.readUtf(32));
    }

    TradeMenu(int id, Inventory inv, Container mine, Container theirs, ContainerData state, Trade.Session session, int side,
              String partner) {
        super(ModSocial.TRADE.get(), id);
        this.mine = mine;
        this.theirs = theirs;
        this.state = state;
        this.session = session;
        this.side = side;
        this.partner = partner;
        for (int i = 0; i < OFFER; i++) {
            addSlot(new Slot(mine, i, MY_X + (i % 3) * 18, GRID_Y + (i / 3) * 18));
        }
        for (int i = 0; i < OFFER; i++) {
            addSlot(new Slot(theirs, i, THEIR_X + (i % 3) * 18, GRID_Y + (i / 3) * 18) {
                @Override
                public boolean mayPlace(ItemStack stack) {
                    return false;
                }

                @Override
                public boolean mayPickup(Player player) {
                    return false;
                }
            });
        }
        addStandardInventorySlots(inv, INV_X, INV_Y);
        addDataSlots(state);
    }

    public boolean isTheirs(Slot slot) {
        return slot.index >= OFFER && slot.index < 2 * OFFER;
    }

    public boolean isMine(Slot slot) {
        return slot.index < OFFER;
    }

    public boolean meAccepted() {
        return state.get(0) != 0;
    }

    public boolean theyAccepted() {
        return state.get(1) != 0;
    }

    public int countdown() {
        return state.get(2);
    }

    public int problem() {
        return state.get(3);
    }

    @Override
    public void clicked(int slotIndex, int button, ContainerInput action, Player player) {
        // the other side's offer is display only, whatever the click (swap keys, throw, double-click collect...)
        if (slotIndex >= OFFER && slotIndex < 2 * OFFER) {
            return;
        }
        super.clicked(slotIndex, button, action, player);
    }

    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (session == null || !(player instanceof ServerPlayer sp)) {
            return false;
        }
        session.button(sp, side, id);
        return true;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem() || isTheirs(slot)) {
            return ItemStack.EMPTY;
        }
        ItemStack stack = slot.getItem();
        ItemStack copy = stack.copy();
        if (isMine(slot)) {
            if (!moveItemStackTo(stack, 2 * OFFER, slots.size(), true)) {
                return ItemStack.EMPTY;
            }
        } else if (!moveItemStackTo(stack, 0, OFFER, false)) {
            return ItemStack.EMPTY;
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
        return !isTheirs(target) && super.canTakeItemForPickAll(carried, target);
    }

    @Override
    public boolean canDragTo(Slot slot) {
        return !isTheirs(slot);
    }

    @Override
    public boolean stillValid(Player player) {
        return session == null || session.valid(side);
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        if (session != null) {
            session.menuClosed(side);
        }
    }
}

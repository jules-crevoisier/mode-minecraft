package com.brasshaven.accessory;

import com.brasshaven.Brasshaven;
import com.brasshaven.data.DataVersions;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.RegistryOps;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import org.jetbrains.annotations.Nullable;

import java.lang.reflect.Method;
import java.util.function.Predicate;

/**
 * Accessory slots (back, two rings, amulet, belt), added to every player's own inventory menu right after the vanilla
 * slots (menu indices 46..50), on both sides, so the vanilla menu sync carries them to the client and every click is
 * checked by the server like any other slot.
 *
 * <p>The worn items are saved in the player's persistent data ({@value #KEY}, outside "PlayerPersisted": on death they
 * follow the keepInventory rule, see {@link AccessoryEvents}). An accessory only works while worn: callers ask
 * {@link #wears} / {@link #find} instead of searching the inventory.
 */
public final class Accessories {
    public static final String KEY = "brasshaven_accessories";
    /** Where the slots sit in the survival inventory screen (relative to its corner): a column left of the armour. */
    public static final int INV_X = -22;
    public static final int INV_Y = 8;

    private static final Method ADD_SLOT = ObfuscationReflectionHelper.findMethod(AbstractContainerMenu.class, "addSlot", Slot.class);

    private Accessories() {}

    /** Adds the accessory slots to this player's inventory menu (once per player object); returns its container. */
    public static AccessoryContainer ensure(Player player) {
        AccessoryContainer found = lookup(player);
        if (found != null) {
            return found;
        }
        AccessoryContainer container = new AccessoryContainer(player);
        if (player instanceof ServerPlayer sp) {
            load(sp, container);
        }
        InventoryMenu menu = player.inventoryMenu;
        try {
            for (int i = 0; i < container.getContainerSize(); i++) {
                ADD_SLOT.invoke(menu, new AccessorySlot(container, i, INV_X, INV_Y + i * 18));
            }
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("Brasshaven: cannot add the accessory slots", e);
        }
        return container;
    }

    private static @Nullable AccessoryContainer lookup(Player player) {
        InventoryMenu menu = player.inventoryMenu;
        if (menu == null) {
            return null;
        }
        int n = menu.slots.size();
        if (n > InventoryMenu.SHIELD_SLOT + 1 && menu.slots.get(InventoryMenu.SHIELD_SLOT + 1) instanceof AccessorySlot s) {
            return s.accessories;
        }
        for (Slot slot : menu.slots) {
            if (slot instanceof AccessorySlot s) {
                return s.accessories;
            }
        }
        return null;
    }

    public static AccessoryContainer get(Player player) {
        return ensure(player);
    }

    /** Index of accessory slot {@code i} in the player's inventory menu. */
    public static int menuIndex(Player player, int i) {
        ensure(player);
        for (Slot slot : player.inventoryMenu.slots) {
            if (slot instanceof AccessorySlot s && s.getContainerSlot() == i) {
                return slot.index;
            }
        }
        return -1;
    }

    /** The first worn accessory matching the test, or EMPTY. */
    public static ItemStack find(Player player, Predicate<ItemStack> test) {
        AccessoryContainer c = get(player);
        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack s = c.getItem(i);
            if (!s.isEmpty() && test.test(s)) {
                return s;
            }
        }
        return ItemStack.EMPTY;
    }

    public static ItemStack worn(Player player, Item item) {
        return find(player, s -> s.is(item));
    }

    public static boolean wears(Player player, Item item) {
        return !worn(player, item).isEmpty();
    }

    /** The first empty slot this item can be worn in, or -1. */
    public static int freeSlotFor(Player player, ItemStack stack) {
        AccessoryContainer c = get(player);
        for (int i = 0; i < c.getContainerSize(); i++) {
            if (c.getItem(i).isEmpty() && c.canPlaceItem(i, stack)) {
                return i;
            }
        }
        return -1;
    }

    /** A worn stack was changed in place (durability, on/off): save it and let the menu sync it. */
    public static void changed(Player player) {
        get(player).setChanged();
    }

    // ------------------------------------------------------------------ saving (server)
    static void save(ServerPlayer player, AccessoryContainer c) {
        RegistryOps<Tag> ops = player.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        ListTag list = new ListTag();
        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack stack = c.getItem(i);
            if (stack.isEmpty()) {
                continue;
            }
            int slot = i;
            ItemStack.CODEC.encodeStart(ops, stack).result().ifPresent(t -> {
                CompoundTag e = new CompoundTag();
                e.putInt("slot", slot);
                e.put("item", t);
                list.add(e);
            });
        }
        CompoundTag tag = new CompoundTag();
        tag.putInt(DataVersions.FIELD, DataVersions.ACCESSORIES);
        tag.put("items", list);
        player.getPersistentData().put(KEY, tag);
    }

    static void load(ServerPlayer player, AccessoryContainer c) {
        CompoundTag root = player.getPersistentData();
        c.loading = true;
        try {
            c.clearContent();
            if (!root.contains(KEY)) {
                return;
            }
            CompoundTag tag = root.getCompoundOrEmpty(KEY);
            // version 0 -> 1: nothing to convert (version 1 is the first layout)
            DataVersions.check("accessories", tag.getIntOr(DataVersions.FIELD, 0), DataVersions.ACCESSORIES);
            RegistryOps<Tag> ops = player.registryAccess().createSerializationContext(NbtOps.INSTANCE);
            ListTag list = tag.getListOrEmpty("items");
            for (int i = 0; i < list.size(); i++) {
                CompoundTag e = list.getCompoundOrEmpty(i);
                int slot = e.getIntOr("slot", -1);
                Tag item = e.get("item");
                if (slot < 0 || slot >= c.getContainerSize() || item == null) {
                    continue;
                }
                ItemStack.CODEC.parse(ops, item)
                        .resultOrPartial(err -> Brasshaven.LOGGER.warn("Brasshaven: dropped an unreadable accessory: {}", err))
                        .ifPresent(stack -> c.setItem(slot, stack));
            }
        } finally {
            c.loading = false;
        }
    }

    /** Re-reads the saved accessories (after the persistent data was copied over from an older player object). */
    static void reload(ServerPlayer player) {
        AccessoryContainer c = lookup(player);
        if (c != null) {
            load(player, c);
        }
    }

    /** Saves now if the slots exist (worn stacks change in place: durability, on/off). */
    static void flush(ServerPlayer player) {
        AccessoryContainer c = lookup(player);
        if (c != null) {
            save(player, c);
        }
    }
}

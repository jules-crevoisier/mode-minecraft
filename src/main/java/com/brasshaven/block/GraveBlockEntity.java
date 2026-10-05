package com.brasshaven.block;

import com.brasshaven.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.UUIDUtil;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import java.util.Collection;
import java.util.Optional;
import java.util.UUID;

/**
 * Holds the belongings of a player who died. Who may open it is the server's choice (graves.ownerOnlyMinutes): only
 * its owner for a while (or always), then anyone.
 */
public class GraveBlockEntity extends BlockEntity {
    public static final int CAPACITY = 160;
    private NonNullList<ItemStack> items = NonNullList.withSize(CAPACITY, ItemStack.EMPTY);
    private UUID owner = UUIDUtil.uuidFromIntArray(new int[]{0, 0, 0, 0});
    private String ownerName = "";
    /** Game time the grave was filled (for graves.ownerOnlyMinutes); 0 for graves made before it was kept. */
    private long createdAt;

    public GraveBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.GRAVE.get(), pos, state);
    }

    /** Stores the stacks; returns those that did not fit (more than {@link #CAPACITY}), never dropping any. */
    public java.util.List<ItemStack> fill(Player player, Collection<ItemStack> stacks) {
        owner = player.getUUID();
        ownerName = player.getName().getString();
        createdAt = level != null ? level.getGameTime() : 0;
        java.util.List<ItemStack> overflow = new java.util.ArrayList<>();
        int i = 0;
        for (ItemStack stack : stacks) {
            if (stack.isEmpty()) {
                continue;
            }
            if (i >= CAPACITY) {
                overflow.add(stack);
            } else {
                items.set(i++, stack.copy());
            }
        }
        setChanged();
        return overflow;
    }

    /**
     * Minutes left during which only the owner may open the grave: 0 when anyone may, -1 when only the owner ever
     * may. Graves of unknown owners (made before owners were kept) are open to all.
     */
    public long lockedMinutes() {
        int setting = com.brasshaven.config.BrasshavenConfig.GRAVE_PROTECTION.get();
        if (setting == 0 || owner.getMostSignificantBits() == 0 && owner.getLeastSignificantBits() == 0) {
            return 0;
        }
        if (setting < 0) {
            return -1;
        }
        long now = level != null ? level.getGameTime() : 0;
        long left = createdAt + setting * 1200L - now;
        return left <= 0 || now < createdAt ? 0 : (left + 1199) / 1200;
    }

    public NonNullList<ItemStack> takeAll() {
        NonNullList<ItemStack> copy = items;
        items = NonNullList.withSize(CAPACITY, ItemStack.EMPTY);
        setChanged();
        return copy;
    }

    public String ownerName() {
        return ownerName;
    }

    public UUID owner() {
        return owner;
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        output.store("owner", UUIDUtil.CODEC, owner);
        output.putString("owner_name", ownerName);
        output.putLong("created_at", createdAt);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(CAPACITY, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        Optional<UUID> stored = input.read("owner", UUIDUtil.CODEC);
        stored.ifPresent(uuid -> owner = uuid);
        ownerName = input.getStringOr("owner_name", "");
        createdAt = input.getLongOr("created_at", 0L);
    }
}

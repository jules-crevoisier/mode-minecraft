package com.wayfarers.block;

import com.wayfarers.registry.ModBlockEntities;
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

/** Holds the belongings of a player who died. Any group member can recover them. */
public class GraveBlockEntity extends BlockEntity {
    public static final int CAPACITY = 160;
    private NonNullList<ItemStack> items = NonNullList.withSize(CAPACITY, ItemStack.EMPTY);
    private UUID owner = UUIDUtil.uuidFromIntArray(new int[]{0, 0, 0, 0});
    private String ownerName = "";

    public GraveBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.GRAVE.get(), pos, state);
    }

    public void fill(Player player, Collection<ItemStack> stacks) {
        owner = player.getUUID();
        ownerName = player.getName().getString();
        int i = 0;
        for (ItemStack stack : stacks) {
            if (i >= CAPACITY) {
                break;
            }
            if (!stack.isEmpty()) {
                items.set(i++, stack.copy());
            }
        }
        setChanged();
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
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(CAPACITY, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        Optional<UUID> stored = input.read("owner", UUIDUtil.CODEC);
        stored.ifPresent(uuid -> owner = uuid);
        ownerName = input.getStringOr("owner_name", "");
    }
}

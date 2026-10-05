package com.wayfarers.item;

import com.wayfarers.Wayfarers;
import com.wayfarers.block.FurnitureBlock;
import com.wayfarers.block.MachineBlock;
import com.wayfarers.block.MachineBlockEntity;
import com.wayfarers.generated.ModDecor;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.NetherPortalBlock;
import net.minecraft.world.level.block.piston.MovingPistonBlock;
import net.minecraft.world.level.block.piston.PistonHeadBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.ChestType;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.block.state.properties.SlabType;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * Brass Wrench. Right-click a block: turn it (facing, axis or sign rotation), keeping vanilla rules: double blocks
 * (beds, doors, tall plants, double chests, extended pistons) and unbreakable blocks are left alone, and a block only
 * takes a direction it can survive in. Sneak-right-click: a Wayfarers machine changes its setting, a Wayfarers
 * decoration or furniture block comes back to your inventory; any other block turns the other way.
 * Runs before the block's own right-click (Forge {@code onItemUseFirst}), so chests and furnaces turn too.
 */
public class BrassWrenchItem extends GadgetItem {
    public BrassWrenchItem(Properties properties) {
        super(properties);
    }

    /** Forge IForgeItem#onItemUseFirst (no @Override: the API stubs used for type-checking are unpatched vanilla). */
    public InteractionResult onItemUseFirst(ItemStack stack, UseOnContext context) {
        Player player = context.getPlayer();
        if (player == null) {
            return InteractionResult.PASS;
        }
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        BlockState state = level.getBlockState(pos);
        if (state.isAir()) {
            return InteractionResult.PASS;
        }
        boolean sneaking = player.isShiftKeyDown();
        if (sneaking && state.getBlock() instanceof MachineBlock) {
            if (!canEdit(player, level, pos, context.getClickedFace(), stack)) {
                tell(player, "message.wayfarers.wrench.protected");
                return InteractionResult.FAIL;
            }
            // quick setting change without opening the screen (radius, interval, detector target...)
            if (player instanceof ServerPlayer sp && level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
                machine.quickCycle(sp);
            }
            return InteractionResult.SUCCESS;
        }
        if (sneaking && isModDecor(state.getBlock())) {
            if (!canEdit(player, level, pos, context.getClickedFace(), stack)) {
                tell(player, "message.wayfarers.wrench.protected");
                return InteractionResult.FAIL;
            }
            if (level instanceof ServerLevel server) {
                pickUp(server, player, pos, state);
            }
            return InteractionResult.SUCCESS;
        }
        BlockState turned = turned(state, level, pos, context.getClickedFace(), sneaking);
        if (turned == null) {
            // nothing to turn: let the block react normally (crafting table, door...); useOn explains otherwise
            return InteractionResult.PASS;
        }
        if (!canEdit(player, level, pos, context.getClickedFace(), stack)) {
            tell(player, "message.wayfarers.wrench.protected");
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server) {
            server.setBlock(pos, turned, Block.UPDATE_ALL);
            server.playSound(null, pos, SoundEvents.ITEM_FRAME_ROTATE_ITEM, SoundSource.BLOCKS, 1.0F, 0.6F);
            server.sendParticles(ParticleTypes.WAX_OFF, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
                    6, 0.35, 0.35, 0.35, 0.0);
            stack.hurtAndBreak(1, player, context.getHand().asEquipmentSlot());
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        if (context.getPlayer() != null) {
            tell(context.getPlayer(), "message.wayfarers.wrench.cannot");
        }
        return InteractionResult.FAIL;
    }

    private static boolean canEdit(Player player, Level level, BlockPos pos, Direction face, ItemStack stack) {
        return player.mayBuild() && level.mayInteract(player, pos) && player.mayUseItemAt(pos, face, stack);
    }

    private static void tell(Player player, String key) {
        if (player instanceof ServerPlayer sp) {
            sp.sendOverlayMessage(Component.translatable(key).withStyle(ChatFormatting.GRAY));
        }
    }

    /** Furniture and the decoration blocks of tools/wf/decor.py (never machines, waystones, altars or ores). */
    public static boolean isModDecor(Block block) {
        if (!Wayfarers.MODID.equals(BuiltInRegistries.BLOCK.getKey(block).getNamespace())) {
            return false;
        }
        if (block instanceof FurnitureBlock) {
            return true;
        }
        for (var item : ModDecor.ITEMS) {
            if (item.get() instanceof BlockItem blockItem && blockItem.getBlock() == block) {
                return true;
            }
        }
        return false;
    }

    private static void pickUp(ServerLevel level, Player player, BlockPos pos, BlockState state) {
        int count = state.hasProperty(BlockStateProperties.SLAB_TYPE)
                && state.getValue(BlockStateProperties.SLAB_TYPE) == SlabType.DOUBLE ? 2 : 1;
        ItemStack drop = new ItemStack(state.getBlock().asItem(), count);
        level.removeBlock(pos, false);
        level.levelEvent(null, LevelEvent.PARTICLES_DESTROY_BLOCK, pos, Block.getId(state));
        if (!drop.isEmpty() && !player.getInventory().add(drop)) {
            player.drop(drop, false);
        }
        level.playSound(null, player.blockPosition(), SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 0.5F, 1.2F);
    }

    // ------------------------------------------------------------------ rotation
    /** The block turned one step, or null when it has nothing to turn or must not be turned. */
    public static @Nullable BlockState turned(BlockState state, Level level, BlockPos pos, Direction face, boolean reverse) {
        Block block = state.getBlock();
        if (state.getDestroySpeed(level, pos) < 0 || block instanceof PistonHeadBlock || block instanceof MovingPistonBlock
                || block instanceof NetherPortalBlock
                || state.hasProperty(BlockStateProperties.BED_PART)
                || state.hasProperty(BlockStateProperties.DOUBLE_BLOCK_HALF)
                || (state.hasProperty(BlockStateProperties.CHEST_TYPE) && state.getValue(BlockStateProperties.CHEST_TYPE) != ChestType.SINGLE)
                || (state.hasProperty(BlockStateProperties.EXTENDED) && state.getValue(BlockStateProperties.EXTENDED))) {
            return null;
        }
        for (Property<?> property : state.getProperties()) {
            List<BlockState> candidates = candidates(state, property, face, reverse,
                    block instanceof MachineBlock machine && !machine.kind().anyFacing);
            if (candidates == null) {
                continue;
            }
            for (BlockState candidate : candidates) {
                BlockState updated = Block.updateFromNeighbourShapes(candidate, level, pos);
                if (updated.getBlock() == block && updated.canSurvive(level, pos)) {
                    return updated;
                }
            }
            return null;
        }
        return null;
    }

    /** Next states to try for one turnable property, best first; null when the property is not a turnable one. */
    @SuppressWarnings("unchecked")
    private static @Nullable List<BlockState> candidates(BlockState state, Property<?> property, Direction face, boolean reverse,
                                                         boolean horizontalOnly) {
        List<BlockState> out = new ArrayList<>();
        if (property.getName().equals("facing") && property.getValueClass() == Direction.class) {
            EnumProperty<Direction> facing = (EnumProperty<Direction>) property;
            Direction current = state.getValue(facing);
            List<Direction> order = new ArrayList<>();
            boolean sixWay = facing.getPossibleValues().contains(Direction.UP) || facing.getPossibleValues().contains(Direction.DOWN);
            if (sixWay && !horizontalOnly) {
                // point it at the clicked face (or away from it when it already does), then try the rest
                order.add(current == face ? face.getOpposite() : face);
                for (Direction d : Direction.values()) {
                    order.add(reverse ? d.getOpposite() : d);
                }
            } else {
                Direction d = current.getAxis().isHorizontal() ? current : Direction.NORTH;
                for (int i = 0; i < 4; i++) {
                    d = reverse ? d.getCounterClockWise() : d.getClockWise();
                    order.add(d);
                }
            }
            for (Direction d : order) {
                if (d != current && facing.getPossibleValues().contains(d)) {
                    out.add(state.setValue(facing, d));
                }
            }
            return out;
        }
        if (property.getName().equals("axis") && property.getValueClass() == Direction.Axis.class) {
            EnumProperty<Direction.Axis> axis = (EnumProperty<Direction.Axis>) property;
            List<Direction.Axis> values = axis.getPossibleValues();
            int i = values.indexOf(state.getValue(axis));
            for (int step = 1; step < values.size(); step++) {
                out.add(state.setValue(axis, values.get(Math.floorMod(i + (reverse ? -step : step), values.size()))));
            }
            return out;
        }
        if (property.getName().equals("rotation") && property instanceof IntegerProperty rotation) {
            List<Integer> values = rotation.getPossibleValues();
            int i = values.indexOf(state.getValue(rotation));
            out.add(state.setValue(rotation, values.get(Math.floorMod(i + (reverse ? -2 : 2), values.size()))));
            return out;
        }
        return null;
    }
}

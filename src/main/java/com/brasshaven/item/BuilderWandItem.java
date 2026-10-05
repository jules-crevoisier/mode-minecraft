package com.brasshaven.item;

import com.brasshaven.registry.ModDataComponents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.phys.AABB;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Builder's Wand (Construction Wand style): right-click a block face to extend that face by up to
 * {@code maxBlocks} copies of the block (same orientation), using blocks from your inventory. Holding it
 * shows an outline of where the blocks will go. Sneak-right-click in the air undoes the last use.
 *
 * <p>Symmetry: sneak-right-click a block to put the mirror centre there; the wand-mode key (G) or sneak-using the
 * centre again cycles off → mirror X → mirror Z → both (4-way). Every placement is then copied across the
 * mirror plane(s) through the centre block, with mirrored orientation, under the same cost and safety rules.
 */
public class BuilderWandItem extends TooltipItem {
    /** Mirror planes through the centre block: X flips east/west, Z flips north/south. */
    public enum Symmetry {
        OFF, X, Z, XZ;

        public Symmetry next() {
            return values()[(ordinal() + 1) % values().length];
        }

        public Component label() {
            return Component.translatable("message.brasshaven.wand.symmetry." + name().toLowerCase(java.util.Locale.ROOT));
        }

        /** The mirrors to apply to each placement (each gives one extra copy). */
        List<Mirror[]> mirrors() {
            return switch (this) {
                case OFF -> List.of();
                case X -> List.<Mirror[]>of(new Mirror[]{Mirror.FRONT_BACK});
                case Z -> List.<Mirror[]>of(new Mirror[]{Mirror.LEFT_RIGHT});
                case XZ -> List.of(new Mirror[]{Mirror.FRONT_BACK}, new Mirror[]{Mirror.LEFT_RIGHT},
                        new Mirror[]{Mirror.FRONT_BACK, Mirror.LEFT_RIGHT});
            };
        }
    }

    /** One block the wand will place. */
    public record Placement(BlockPos pos, BlockState state) {}

    /** What one use places: the copies of the clicked face, then their mirrored copies. */
    public record Plan(List<Placement> primary, List<Placement> mirrored) {
        public static final Plan EMPTY = new Plan(List.of(), List.of());

        public boolean isEmpty() {
            return primary.isEmpty();
        }

        public List<Placement> all() {
            List<Placement> out = new ArrayList<>(primary);
            out.addAll(mirrored);
            return out;
        }
    }

    /** The last use of a player's wand; {@code paid}: its blocks came from the inventory (not in creative). */
    private record Undo(ResourceKey<Level> dimension, List<Placement> placed, boolean paid) {}

    private static final Map<UUID, Undo> UNDO = new HashMap<>();
    /** Mirrored copies further than this from the player are skipped (keeps far chunks untouched). */
    public static final int MIRROR_RANGE = 96;

    private final int maxBlocks;

    public BuilderWandItem(Properties properties, int maxBlocks) {
        super(properties);
        this.maxBlocks = maxBlocks;
    }

    /** Forgets a player's undo when they leave (see ServerGuard). */
    public static void forget(UUID id) {
        UNDO.remove(id);
    }

    public int maxBlocks() {
        return maxBlocks;
    }

    // ------------------------------------------------------------------ symmetry settings (item components)
    public static Symmetry symmetry(ItemStack wand) {
        int i = wand.getOrDefault(ModDataComponents.WAND_SYMMETRY.get(), 0);
        return Symmetry.values()[Math.floorMod(i, Symmetry.values().length)];
    }

    /** The mirror centre if symmetry is on and the centre is in {@code level}'s dimension, else null. */
    @Nullable
    public static BlockPos mirrorCentre(Level level, ItemStack wand) {
        GlobalPos g = wand.get(ModDataComponents.WAND_MIRROR.get());
        if (symmetry(wand) == Symmetry.OFF || g == null || !g.dimension().equals(level.dimension())) {
            return null;
        }
        return g.pos();
    }

    /** Cycles the symmetry mode (wand-mode key or sneak-use on the centre) and tells the player. */
    public static void cycleSymmetry(Player player, ItemStack wand) {
        Symmetry next = symmetry(wand).next();
        wand.set(ModDataComponents.WAND_SYMMETRY.get(), next.ordinal());
        GlobalPos g = wand.get(ModDataComponents.WAND_MIRROR.get());
        if (next != Symmetry.OFF && (g == null || !g.dimension().equals(player.level().dimension()))) {
            // no centre yet (or in another dimension): start from the block under the player
            g = GlobalPos.of(player.level().dimension(), player.blockPosition().below());
            wand.set(ModDataComponents.WAND_MIRROR.get(), g);
        }
        if (next == Symmetry.OFF) {
            player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.symmetry", next.label())
                    .withStyle(ChatFormatting.GRAY));
        } else {
            BlockPos c = g.pos();
            player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.symmetry_at", next.label(),
                    c.getX(), c.getY(), c.getZ()).withStyle(ChatFormatting.AQUA));
            if (player.level() instanceof ServerLevel server) {
                showCentre(server, c, next);
            }
        }
        player.level().playSound(null, player.blockPosition(), SoundEvents.UI_BUTTON_CLICK.value(), SoundSource.PLAYERS, 0.4F,
                next == Symmetry.OFF ? 0.8F : 1.2F + next.ordinal() * 0.1F);
    }

    /** Particles on the centre block and along the mirror plane(s). */
    private static void showCentre(ServerLevel level, BlockPos c, Symmetry symmetry) {
        double cx = c.getX() + 0.5, cy = c.getY() + 0.5, cz = c.getZ() + 0.5;
        level.sendParticles(ParticleTypes.END_ROD, cx, cy, cz, 16, 0.35, 0.35, 0.35, 0.01);
        for (int i = -6; i <= 6; i++) {
            if (symmetry == Symmetry.X || symmetry == Symmetry.XZ) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, cx, cy + 0.6, cz + i, 1, 0.0, 0.0, 0.0, 0.0);
            }
            if (symmetry == Symmetry.Z || symmetry == Symmetry.XZ) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, cx + i, cy + 0.6, cz, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
    }

    /** {@code pos} mirrored across the plane(s) through the centre block. */
    public static BlockPos mirror(BlockPos pos, BlockPos centre, Mirror[] mirrors) {
        int x = pos.getX(), z = pos.getZ();
        for (Mirror m : mirrors) {
            if (m == Mirror.FRONT_BACK) {
                x = 2 * centre.getX() - x;
            } else if (m == Mirror.LEFT_RIGHT) {
                z = 2 * centre.getZ() - z;
            }
        }
        return new BlockPos(x, pos.getY(), z);
    }

    private static BlockState mirror(BlockState state, Mirror[] mirrors) {
        for (Mirror m : mirrors) {
            state = state.mirror(m);
        }
        return state;
    }

    // ------------------------------------------------------------------ placement rules
    /** Block properties that count items in one block (sea pickles, candles, petals, snow layers...). */
    private static final List<IntegerProperty> AMOUNTS = List.of(BlockStateProperties.PICKLES, BlockStateProperties.CANDLES,
            BlockStateProperties.FLOWER_AMOUNT, BlockStateProperties.SEGMENT_AMOUNT, BlockStateProperties.EGGS,
            BlockStateProperties.LAYERS);
    /**
     * Block properties that grow or fill up with time or work (crop age, sapling stage, berries, composter level,
     * respawn anchor charges, egg hatching...): copies start fresh, so the wand never hands out a free harvest.
     */
    private static final Set<String> FRESH = Set.of("age", "stage", "berries", "level", "charges", "hatch", "hydration");

    /** Items one copy of this block costs (a double slab is two slabs, four candles are four candles). */
    private static int cost(BlockState state) {
        if (state.hasProperty(BlockStateProperties.SLAB_TYPE) && state.getValue(BlockStateProperties.SLAB_TYPE) == SlabType.DOUBLE) {
            return 2;
        }
        for (IntegerProperty amount : AMOUNTS) {
            if (state.hasProperty(amount)) {
                return state.getValue(amount);
            }
        }
        return 1;
    }

    /**
     * The state the wand places: the clicked block's, minus water (no free water from waterlogged blocks) and with
     * its growth reset (see {@link #FRESH}).
     */
    private static BlockState placed(BlockState state) {
        BlockState fresh = state.getBlock().defaultBlockState();
        for (Property<?> property : state.getProperties()) {
            if (FRESH.contains(property.getName())) {
                state = copyValue(fresh, state, property);
            }
        }
        return state.hasProperty(BlockStateProperties.WATERLOGGED) ? state.setValue(BlockStateProperties.WATERLOGGED, false) : state;
    }

    private static <T extends Comparable<T>> BlockState copyValue(BlockState from, BlockState to, Property<T> property) {
        return to.setValue(property, from.getValue(property));
    }

    /** Whether the wand may put {@code state} at {@code target}: free, allowed, loaded, supported, nobody standing there. */
    private static boolean canPlaceAt(Level level, Player player, BlockPos target, BlockState state) {
        return level.isInWorldBounds(target) && level.isLoaded(target) && level.getBlockState(target).canBeReplaced()
                && level.mayInteract(player, target) && state.canSurvive(level, target)
                && level.getEntitiesOfClass(LivingEntity.class, new AABB(target)).isEmpty();
    }

    /** Where the wand would place blocks when used on {@code pos}/{@code face} (shared by the preview and the use). */
    public static Plan plan(Level level, Player player, ItemStack wand, BlockPos pos, Direction face, int max) {
        BlockState source = level.getBlockState(pos);
        Item item = source.getBlock().asItem();
        // two-block things (doors, beds, tall plants) would only get one half; a block whose item places another
        // block (wall torch, water or lava cauldron, cave vines...) is not what that item buys
        if (source.isAir() || !(item instanceof BlockItem blockItem) || blockItem.getBlock() != source.getBlock()
                || source.hasBlockEntity() || !player.mayBuild()
                || source.hasProperty(BlockStateProperties.DOUBLE_BLOCK_HALF) || source.hasProperty(BlockStateProperties.BED_PART)) {
            return Plan.EMPTY;
        }
        BlockState state = placed(source);
        int unit = cost(state);
        int budget = player.isCreative() ? Integer.MAX_VALUE : count(player.getInventory(), item) / unit;
        BlockPos centre = mirrorCentre(level, wand);
        List<Mirror[]> mirrors = centre == null ? List.of() : symmetry(wand).mirrors();

        List<Placement> primary = new ArrayList<>();
        List<Placement> mirrored = new ArrayList<>();
        Set<BlockPos> claimed = new HashSet<>();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(pos);
        seen.add(pos);
        Direction[] spread = java.util.Arrays.stream(Direction.values()).filter(d -> d.getAxis() != face.getAxis())
                .toArray(Direction[]::new);
        while (!queue.isEmpty() && primary.size() < max && budget > 0) {
            BlockPos p = queue.poll();
            BlockPos target = p.relative(face);
            if (!level.getBlockState(p).is(source.getBlock())) {
                continue;
            }
            if (claimed.contains(target)) {
                // already filled as the mirror image of another block: keep spreading past it
                spread(p, pos, spread, max, seen, queue);
                continue;
            }
            if (!canPlaceAt(level, player, target, state)) {
                continue;
            }
            // the block and its mirrored copies go in together, or not at all, so the build stays symmetric
            List<Placement> copies = new ArrayList<>();
            for (Mirror[] m : mirrors) {
                BlockPos mp = mirror(target, centre, m);
                BlockState ms = mirror(state, m);
                if (!mp.equals(target) && !claimed.contains(mp) && copies.stream().noneMatch(c -> c.pos().equals(mp))
                        && mp.distSqr(player.blockPosition()) <= MIRROR_RANGE * MIRROR_RANGE && canPlaceAt(level, player, mp, ms)) {
                    copies.add(new Placement(mp, ms));
                }
            }
            if (1 + copies.size() > budget) {
                break;
            }
            budget -= 1 + copies.size();
            primary.add(new Placement(target, state));
            claimed.add(target);
            for (Placement c : copies) {
                mirrored.add(c);
                claimed.add(c.pos());
            }
            spread(p, pos, spread, max, seen, queue);
        }
        return primary.isEmpty() ? Plan.EMPTY : new Plan(primary, mirrored);
    }

    /** Queues the neighbours of {@code p} along the clicked face (flood fill of the face, within {@code max}). */
    private static void spread(BlockPos p, BlockPos origin, Direction[] directions, int max, Set<BlockPos> seen,
                               ArrayDeque<BlockPos> queue) {
        for (Direction d : directions) {
            BlockPos n = p.relative(d);
            if (seen.add(n) && n.distManhattan(origin) <= max) {
                queue.add(n);
            }
        }
    }

    /** Slots the wand takes blocks from: the main inventory and the off hand, never what is worn (a carved pumpkin...). */
    private static boolean isSupply(int slot) {
        return slot < Inventory.INVENTORY_SIZE || slot == Inventory.SLOT_OFFHAND;
    }

    private static int count(Inventory inv, Item item) {
        int n = 0;
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (isSupply(i) && inv.getItem(i).is(item)) {
                n += inv.getItem(i).getCount();
            }
        }
        return n;
    }

    private static void consume(Inventory inv, Item item, int amount) {
        for (int i = 0; i < inv.getContainerSize() && amount > 0; i++) {
            ItemStack s = inv.getItem(i);
            if (isSupply(i) && s.is(item)) {
                int take = Math.min(amount, s.getCount());
                s.shrink(take);
                amount -= take;
            }
        }
    }

    // ------------------------------------------------------------------ use
    @Override
    public InteractionResult useOn(UseOnContext ctx) {
        Level level = ctx.getLevel();
        Player player = ctx.getPlayer();
        if (player == null) {
            return InteractionResult.PASS;
        }
        BlockPos pos = ctx.getClickedPos();
        ItemStack wand = ctx.getItemInHand();
        if (player.isShiftKeyDown()) {
            return setCentre(level, player, wand, pos);
        }
        Plan plan = plan(level, player, wand, pos, ctx.getClickedFace(), maxBlocks);
        if (plan.isEmpty()) {
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server) {
            List<Placement> all = plan.all();
            BlockState state = plan.primary().get(0).state();
            // protection mods (claims) hear about every block, like a hand placement; one refusal stops the whole use
            if (player instanceof net.minecraft.server.level.ServerPlayer sp) {
                for (Placement p : all) {
                    if (!com.brasshaven.util.ServerGuard.mayPlace(server, p.pos(), sp)) {
                        player.sendOverlayMessage(Component.translatable("message.brasshaven.wrench.protected")
                                .withStyle(ChatFormatting.GRAY));
                        return InteractionResult.FAIL;
                    }
                }
            }
            for (Placement p : all) {
                server.setBlock(p.pos(), p.state(), Block.UPDATE_ALL);
            }
            if (!player.isCreative()) {
                consume(player.getInventory(), state.getBlock().asItem(), all.size() * cost(state));
                wand.hurtAndBreak(1, player, ctx.getHand() == InteractionHand.MAIN_HAND
                        ? net.minecraft.world.entity.EquipmentSlot.MAINHAND : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
            }
            UNDO.put(player.getUUID(), new Undo(level.dimension(), List.copyOf(all), !player.isCreative()));
            var sound = state.getSoundType().getPlaceSound();
            level.playSound(null, pos, sound, SoundSource.BLOCKS, 1.0F, 0.9F);
            if (!plan.mirrored().isEmpty()) {
                for (Placement p : plan.mirrored()) {
                    server.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.pos().getX() + 0.5, p.pos().getY() + 0.5,
                            p.pos().getZ() + 0.5, 2, 0.3, 0.3, 0.3, 0.0);
                }
                player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.placed_mirrored",
                        plan.primary().size(), plan.mirrored().size()).withStyle(ChatFormatting.AQUA));
            }
        }
        return InteractionResult.SUCCESS;
    }

    /** Sneak-use on a block: put the mirror centre there, or cycle the mode if it already is the centre. */
    private InteractionResult setCentre(Level level, Player player, ItemStack wand, BlockPos pos) {
        if (level instanceof ServerLevel server) {
            GlobalPos current = wand.get(ModDataComponents.WAND_MIRROR.get());
            GlobalPos here = GlobalPos.of(level.dimension(), pos);
            if (here.equals(current)) {
                cycleSymmetry(player, wand);
                return InteractionResult.SUCCESS;
            }
            wand.set(ModDataComponents.WAND_MIRROR.get(), here);
            Symmetry symmetry = symmetry(wand);
            if (symmetry == Symmetry.OFF) {
                symmetry = Symmetry.X;
                wand.set(ModDataComponents.WAND_SYMMETRY.get(), symmetry.ordinal());
            }
            showCentre(server, pos, symmetry);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.4F);
            player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.centre", pos.getX(), pos.getY(), pos.getZ(),
                    symmetry.label()).withStyle(ChatFormatting.AQUA));
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
                player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.nothing").withStyle(ChatFormatting.GRAY));
                return InteractionResult.SUCCESS;
            }
            int restored = 0;
            Item item = null;
            for (Placement p : undo.placed()) {
                // same block and same worth: its shape may have changed since (stair corners, fences and walls joining)
                BlockState now = server.getBlockState(p.pos());
                // only near the player, and only where they may still break blocks (a claim made since, spawn...)
                if (now.is(p.state().getBlock()) && cost(now) == cost(p.state())
                        && p.pos().distSqr(player.blockPosition()) <= MIRROR_RANGE * MIRROR_RANGE
                        && player instanceof net.minecraft.server.level.ServerPlayer sp
                        && com.brasshaven.util.ServerGuard.mayBreak(server, p.pos(), sp)) {
                    server.removeBlock(p.pos(), false);
                    restored += cost(p.state());
                    item = p.state().getBlock().asItem();
                }
            }
            // only blocks that were paid for come back (a creative use undone in survival gives nothing), in whole stacks
            if (undo.paid() && restored > 0 && item != null) {
                int maxStack = new ItemStack(item).getMaxStackSize();
                for (int left = restored; left > 0; left -= maxStack) {
                    player.getInventory().placeItemBackInInventory(new ItemStack(item, Math.min(left, maxStack)));
                }
            }
            player.sendOverlayMessage(Component.translatable("message.brasshaven.wand.undone", restored).withStyle(ChatFormatting.GOLD));
        }
        return InteractionResult.SUCCESS;
    }

    @Override
    @SuppressWarnings("deprecation")
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> builder,
                                TooltipFlag flag) {
        super.appendHoverText(stack, context, display, builder, flag);
        Symmetry s = symmetry(stack);
        GlobalPos g = stack.get(ModDataComponents.WAND_MIRROR.get());
        if (s == Symmetry.OFF || g == null) {
            builder.accept(Component.translatable("tooltip.brasshaven.wand.symmetry", s.label()).withStyle(ChatFormatting.DARK_AQUA));
        } else {
            builder.accept(Component.translatable("tooltip.brasshaven.wand.symmetry_at", s.label(), g.pos().getX(), g.pos().getY(),
                    g.pos().getZ()).withStyle(ChatFormatting.DARK_AQUA));
        }
    }
}

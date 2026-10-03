package com.wayfarers.block;

import com.wayfarers.event.QolEvents;
import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.util.InventoryUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.DispenserMenu;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.FarmlandBlock;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Predicate;

/** State and behaviour of every {@link MachineBlock}: a 9-slot buffer, one setting, a colour channel. */
public class MachineBlockEntity extends BaseContainerBlockEntity {
    public static final int SIZE = 9;
    private static final int[] HARVEST_RADIUS = {2, 3, 4};
    private static final int[] SPRINKLER_RADIUS = {1, 2, 3};
    private static final int[] VACUUM_RADIUS = {3, 5, 8};
    private static final int[] TIMER_SECONDS = {1, 2, 5, 10, 30, 60};
    private static final int[] DETECTOR_RADIUS = {2, 4, 8, 16};
    private static final String[] DETECTOR_MODES = {"players", "monsters", "animals", "items", "living"};

    /** Powered transmitters per dimension and channel (an index only: each hit is re-checked in the world). */
    private static final Map<String, Set<BlockPos>> TRANSMITTERS = new HashMap<>();

    private NonNullList<ItemStack> items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
    private int setting = -1;
    private int mode;
    private int channel;
    private int xp;
    private int signal;
    private long ticker;
    private long pulseEnd;

    public MachineBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.MACHINE.get(), pos, state);
    }

    private MachineBlock.Kind kind() {
        return getBlockState().getBlock() instanceof MachineBlock m ? m.kind() : MachineBlock.Kind.TIMER;
    }

    public int signal() {
        return signal;
    }

    // ------------------------------------------------------------------ container plumbing
    @Override
    protected Component getDefaultName() {
        return getBlockState().getBlock().getName();
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> newItems) {
        items = newItems;
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return new DispenserMenu(containerId, inventory, this);
    }

    @Override
    public int getContainerSize() {
        return SIZE;
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        output.putInt("setting", setting);
        output.putInt("mode", mode);
        output.putInt("channel", channel);
        output.putInt("xp", xp);
        output.putInt("signal", signal);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        setting = input.getIntOr("setting", -1);
        mode = input.getIntOr("mode", 0);
        channel = input.getIntOr("channel", 0);
        xp = input.getIntOr("xp", 0);
        signal = input.getIntOr("signal", 0);
    }

    // ------------------------------------------------------------------ settings
    private int[] options() {
        return switch (kind()) {
            case HARVESTER -> HARVEST_RADIUS;
            case SPRINKLER -> SPRINKLER_RADIUS;
            case VACUUM -> VACUUM_RADIUS;
            case TIMER -> TIMER_SECONDS;
            case DETECTOR -> DETECTOR_RADIUS;
            default -> new int[] {0};
        };
    }

    private int value() {
        int[] opts = options();
        int i = setting < 0 ? Math.min(1, opts.length - 1) : setting % opts.length;
        return opts[i];
    }

    private void cycle() {
        int[] opts = options();
        int i = setting < 0 ? Math.min(1, opts.length - 1) : setting % opts.length;
        setting = (i + 1) % opts.length;
        setChanged();
    }

    private static void tell(Player player, Component message) {
        if (player instanceof ServerPlayer sp) {
            sp.sendOverlayMessage(message.copy().withStyle(ChatFormatting.GOLD));
        }
    }

    private Component area() {
        int size = value() * 2 + 1;
        return Component.translatable("message.wayfarers.machine.area", size, size);
    }

    private Component channelName() {
        DyeColor color = DyeColor.byId(channel);
        return Component.translatable("color.minecraft." + color.getName()).withColor(color.getTextColor());
    }

    /** Right-click with an empty hand (sneak-click changes the setting of machines that also have a buffer). */
    public void use(Player player) {
        MachineBlock.Kind kind = kind();
        switch (kind) {
            case HARVESTER, VACUUM -> {
                if (player.isShiftKeyDown()) {
                    cycle();
                    tell(player, area());
                    return;
                }
                if (kind == MachineBlock.Kind.VACUUM && xp > 0) {
                    player.giveExperiencePoints(xp);
                    tell(player, Component.translatable("message.wayfarers.machine.xp", xp));
                    xp = 0;
                    setChanged();
                }
                player.openMenu(this);
            }
            case BREAKER, PLACER -> player.openMenu(this);
            case SPRINKLER -> {
                cycle();
                tell(player, area());
            }
            case TIMER -> {
                cycle();
                tell(player, Component.translatable("message.wayfarers.machine.interval", value()));
            }
            case TRANSMITTER, RECEIVER -> tell(player, Component.translatable("message.wayfarers.machine.channel", channelName()));
            case DETECTOR -> {
                if (player.isShiftKeyDown()) {
                    mode = (mode + 1) % DETECTOR_MODES.length;
                    setChanged();
                } else {
                    cycle();
                }
                tell(player, Component.translatable("message.wayfarers.machine.detector",
                        Component.translatable("message.wayfarers.machine.detector." + DETECTOR_MODES[mode]), value()));
            }
        }
        if (level != null) {
            level.playSound(null, worldPosition, SoundEvents.COMPARATOR_CLICK, SoundSource.BLOCKS, 0.4F, 1.2F);
        }
    }

    public void setChannel(Player player, int newChannel) {
        if (level instanceof ServerLevel server && kind() == MachineBlock.Kind.TRANSMITTER) {
            TRANSMITTERS.getOrDefault(key(server, channel), Set.of()).remove(worldPosition);
        }
        channel = newChannel;
        setChanged();
        tell(player, Component.translatable("message.wayfarers.machine.channel", channelName()));
        if (level != null) {
            level.playSound(null, worldPosition, SoundEvents.DYE_USE, SoundSource.BLOCKS, 0.8F, 1.0F);
        }
    }

    // ------------------------------------------------------------------ ticking
    void serverTick(ServerLevel level, BlockState state) {
        ticker++;
        switch (kind()) {
            case HARVESTER -> {
                if (ticker % 40 == 0) {
                    harvest(level);
                }
            }
            case SPRINKLER -> {
                if (ticker % 20 == 0) {
                    sprinkle(level);
                }
            }
            case VACUUM -> {
                if (ticker % 5 == 0) {
                    vacuum(level);
                }
                if (ticker % 10 == 0) {
                    pushDown(level);
                }
            }
            case TIMER -> {
                if (state.getValue(MachineBlock.POWERED) && ticker >= pulseEnd) {
                    setPowered(level, state, false);
                } else if (!state.getValue(MachineBlock.POWERED) && ticker % (value() * 20L) == 0) {
                    pulseEnd = ticker + 4;
                    setPowered(level, state, true);
                }
            }
            case TRANSMITTER -> {
                if (ticker % 5 == 0) {
                    Set<BlockPos> set = TRANSMITTERS.computeIfAbsent(key(level, channel), k -> new HashSet<>());
                    if (state.getValue(MachineBlock.POWERED)) {
                        set.add(worldPosition.immutable());
                    } else {
                        set.remove(worldPosition);
                    }
                }
            }
            case RECEIVER -> {
                if (ticker % 5 == 0) {
                    boolean on = anyTransmitter(level);
                    if (on != state.getValue(MachineBlock.POWERED)) {
                        setPowered(level, state, on);
                    }
                }
            }
            case DETECTOR -> {
                if (ticker % 10 == 0) {
                    detect(level, state);
                }
            }
            default -> {
            }
        }
    }

    private void setPowered(ServerLevel level, BlockState state, boolean on) {
        level.setBlock(worldPosition, state.setValue(MachineBlock.POWERED, on), Block.UPDATE_ALL);
    }

    // ------------------------------------------------------------------ harvester
    private void harvest(ServerLevel level) {
        int r = value();
        int done = 0;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -1, -r), worldPosition.offset(r, 1, r))) {
            if (done >= 16) {
                break;
            }
            BlockState s = level.getBlockState(p);
            BlockState replant = QolEvents.replanted(s);
            if (replant != null) {
                List<ItemStack> drops = Block.getDrops(s, level, p, null);
                Block seedBlock = s.getBlock();
                boolean seedTaken = false;
                for (ItemStack drop : drops) {
                    if (!seedTaken && drop.getItem() == seedBlock.asItem()) {
                        drop.shrink(1);
                        seedTaken = true;
                    }
                }
                level.setBlock(p, replant, Block.UPDATE_ALL);
                collect(level, drops, p);
                done++;
            } else if ((s.is(Blocks.MELON) || s.is(Blocks.PUMPKIN)) && besideAttachedStem(level, p)) {
                List<ItemStack> drops = Block.getDrops(s, level, p, null);
                level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                collect(level, drops, p);
                done++;
            } else if ((s.is(Blocks.SUGAR_CANE) || s.is(Blocks.CACTUS) || s.is(Blocks.BAMBOO))
                    && level.getBlockState(p.below()).is(s.getBlock()) && !level.getBlockState(p.below(2)).is(s.getBlock())) {
                // cut the stalk above the bottom block, top first so nothing pops
                BlockPos top = p;
                while (level.getBlockState(top.above()).is(s.getBlock())) {
                    top = top.above();
                }
                for (BlockPos q = top; q.getY() >= p.getY(); q = q.below()) {
                    List<ItemStack> drops = Block.getDrops(level.getBlockState(q), level, q, null);
                    level.setBlock(q, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                    collect(level, drops, q);
                }
                done++;
            }
        }
        if (done > 0) {
            level.playSound(null, worldPosition, SoundEvents.CROP_BREAK, SoundSource.BLOCKS, 0.7F, 1.0F);
        }
    }

    private static boolean besideAttachedStem(ServerLevel level, BlockPos p) {
        for (Direction d : Direction.Plane.HORIZONTAL) {
            BlockState n = level.getBlockState(p.relative(d));
            if (n.is(Blocks.ATTACHED_MELON_STEM) || n.is(Blocks.ATTACHED_PUMPKIN_STEM)) {
                return true;
            }
        }
        return false;
    }

    private void collect(ServerLevel level, List<ItemStack> drops, BlockPos at) {
        level.sendParticles(ParticleTypes.HAPPY_VILLAGER, at.getX() + 0.5, at.getY() + 0.6, at.getZ() + 0.5, 3, 0.25, 0.2, 0.25, 0.0);
        for (ItemStack drop : drops) {
            ItemStack rest = store(level, drop, null);
            if (!rest.isEmpty()) {
                Block.popResource(level, worldPosition.above(), rest);
            }
        }
    }

    /** Puts a stack into a neighbouring container (preferring {@code preferred}), then into the buffer. */
    private ItemStack store(ServerLevel level, ItemStack stack, Direction preferred) {
        List<Direction> order = new ArrayList<>();
        if (preferred != null) {
            order.add(preferred);
        } else {
            order.add(Direction.DOWN);
            order.addAll(Direction.Plane.HORIZONTAL.stream().toList());
            order.add(Direction.UP);
        }
        ItemStack rest = stack;
        for (Direction d : order) {
            if (rest.isEmpty()) {
                break;
            }
            BlockPos np = worldPosition.relative(d);
            if (level.getBlockEntity(np) instanceof MachineBlockEntity) {
                continue;
            }
            Container target = HopperBlockEntity.getContainerAt(level, np);
            if (target != null) {
                rest = HopperBlockEntity.addItem(this, target, rest, d.getOpposite());
            }
        }
        if (!rest.isEmpty()) {
            rest = InventoryUtil.insert(this, rest, false);
        }
        return rest;
    }

    // ------------------------------------------------------------------ sprinkler
    private void sprinkle(ServerLevel level) {
        int r = value();
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -2, -r), worldPosition.offset(r, 0, r))) {
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof FarmlandBlock && s.getValue(FarmlandBlock.MOISTURE) < FarmlandBlock.MAX_MOISTURE) {
                level.setBlock(p, s.setValue(FarmlandBlock.MOISTURE, FarmlandBlock.MAX_MOISTURE), Block.UPDATE_CLIENTS);
            } else if (s.isRandomlyTicking() && (s.getBlock() instanceof BonemealableBlock || s.is(Blocks.SUGAR_CANE)
                    || s.is(Blocks.CACTUS) || s.is(Blocks.NETHER_WART)) && !s.is(Blocks.GRASS_BLOCK)
                    && level.getRandom().nextInt(3) == 0) {
                s.randomTick(level, p.immutable(), level.getRandom());
            }
        }
        for (int i = 0; i < 6; i++) {
            double a = level.getRandom().nextDouble() * Math.PI * 2;
            double d = level.getRandom().nextDouble() * (r + 0.5);
            level.sendParticles(ParticleTypes.SPLASH, worldPosition.getX() + 0.5 + Math.cos(a) * d, worldPosition.getY() + 1.0,
                    worldPosition.getZ() + 0.5 + Math.sin(a) * d, 2, 0.1, 0.0, 0.1, 0.0);
        }
    }

    // ------------------------------------------------------------------ vacuum hopper
    private void vacuum(ServerLevel level) {
        AABB area = new AABB(worldPosition).inflate(value());
        for (ItemEntity drop : level.getEntitiesOfClass(ItemEntity.class, area, e -> e.isAlive() && !e.hasPickUpDelay())) {
            ItemStack before = drop.getItem();
            ItemStack rest = InventoryUtil.insert(this, before, false);
            if (rest.getCount() != before.getCount()) {
                level.sendParticles(ParticleTypes.PORTAL, drop.getX(), drop.getY() + 0.2, drop.getZ(), 4, 0.1, 0.1, 0.1, 0.2);
                if (rest.isEmpty()) {
                    drop.discard();
                } else {
                    drop.setItem(rest);
                }
            }
        }
        for (ExperienceOrb orb : level.getEntitiesOfClass(ExperienceOrb.class, area, Entity::isAlive)) {
            xp += orb.getValue();
            orb.discard();
            setChanged();
        }
    }

    private void pushDown(ServerLevel level) {
        if (level.getBlockEntity(worldPosition.below()) instanceof MachineBlockEntity) {
            return;
        }
        Container below = HopperBlockEntity.getContainerAt(level, worldPosition.below());
        if (below == null) {
            return;
        }
        for (int i = 0; i < SIZE; i++) {
            ItemStack stack = items.get(i);
            if (!stack.isEmpty()) {
                ItemStack rest = HopperBlockEntity.addItem(this, below, stack.copy(), Direction.UP);
                if (rest.getCount() != stack.getCount()) {
                    items.set(i, rest);
                    setChanged();
                    return;
                }
            }
        }
    }

    // ------------------------------------------------------------------ breaker / placer (on a redstone pulse)
    void pulse(ServerLevel level) {
        BlockState state = getBlockState();
        Direction facing = state.getValue(MachineBlock.FACING);
        BlockPos front = worldPosition.relative(facing);
        BlockState target = level.getBlockState(front);
        if (kind() == MachineBlock.Kind.BREAKER) {
            if (target.isAir() || target.getBlock() instanceof LiquidBlock || target.getDestroySpeed(level, front) < 0
                    || target.getBlock() instanceof MachineBlock) {
                return;
            }
            List<ItemStack> drops = Block.getDrops(target, level, front, level.getBlockEntity(front), null,
                    new ItemStack(Items.DIAMOND_PICKAXE));
            level.destroyBlock(front, false);
            for (ItemStack drop : drops) {
                ItemStack rest = store(level, drop, facing.getOpposite());
                if (!rest.isEmpty()) {
                    Block.popResource(level, front, rest);
                }
            }
        } else if (kind() == MachineBlock.Kind.PLACER) {
            if (!target.canBeReplaced()) {
                return;
            }
            Container behind = level.getBlockEntity(worldPosition.relative(facing.getOpposite())) instanceof MachineBlockEntity
                    ? null : HopperBlockEntity.getContainerAt(level, worldPosition.relative(facing.getOpposite()));
            if (placeFrom(level, behind, front) || placeFrom(level, this, front)) {
                level.sendParticles(ParticleTypes.CLOUD, front.getX() + 0.5, front.getY() + 0.5, front.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.01);
            }
        }
    }

    private static boolean placeFrom(ServerLevel level, Container from, BlockPos front) {
        if (from == null) {
            return false;
        }
        for (int i = 0; i < from.getContainerSize(); i++) {
            ItemStack stack = from.getItem(i);
            if (stack.getItem() instanceof BlockItem bi) {
                BlockState place = bi.getBlock().defaultBlockState();
                if (place.canSurvive(level, front)) {
                    level.setBlock(front, place, Block.UPDATE_ALL);
                    level.playSound(null, front, place.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1.0F, 0.9F);
                    from.removeItem(i, 1);
                    from.setChanged();
                    return true;
                }
            }
        }
        return false;
    }

    // ------------------------------------------------------------------ wireless redstone
    private static String key(ServerLevel level, int channel) {
        return level.dimension().identifier() + "#" + channel;
    }

    private boolean anyTransmitter(ServerLevel level) {
        Set<BlockPos> set = TRANSMITTERS.get(key(level, channel));
        if (set == null || set.isEmpty()) {
            return false;
        }
        set.removeIf(p -> !level.isLoaded(p) || !(level.getBlockEntity(p) instanceof MachineBlockEntity m)
                || m.kind() != MachineBlock.Kind.TRANSMITTER || m.channel != channel);
        for (BlockPos p : set) {
            if (level.getBlockState(p).getValue(MachineBlock.POWERED)) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------ detector
    private void detect(ServerLevel level, BlockState state) {
        AABB area = new AABB(worldPosition).inflate(value());
        Predicate<Entity> filter = switch (DETECTOR_MODES[mode % DETECTOR_MODES.length]) {
            case "players" -> e -> e instanceof Player p && !p.isSpectator();
            case "monsters" -> e -> e instanceof Enemy;
            case "animals" -> e -> e instanceof Animal;
            case "items" -> e -> e instanceof ItemEntity;
            default -> e -> e instanceof LivingEntity && !(e instanceof Player p && p.isSpectator());
        };
        int count = level.getEntitiesOfClass(Entity.class, area, e -> e.isAlive() && filter.test(e)).size();
        int newSignal = Math.min(15, count);
        if (newSignal != signal) {
            signal = newSignal;
            setChanged();
            boolean on = signal > 0;
            if (on != state.getValue(MachineBlock.POWERED)) {
                setPowered(level, state, on);
            } else {
                level.updateNeighborsAt(worldPosition, state.getBlock(), null);
            }
        }
    }
}

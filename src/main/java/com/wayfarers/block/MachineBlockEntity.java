package com.wayfarers.block;

import com.wayfarers.event.QolEvents;
import com.wayfarers.menu.MachineMenu;
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
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.DirectionalPlaceContext;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.FarmlandBlock;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
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

/**
 * State and behaviour of every {@link MachineBlock}: a 9-slot buffer, its settings (area, redstone mode, channel,
 * timer interval, detector target...) and a live status shown by its screen ({@link MachineMenu}).
 */
public class MachineBlockEntity extends BaseContainerBlockEntity {
    public static final int SIZE = 9;
    public static final int FILTER_SIZE = 5;
    public static final int[] HARVEST_RADIUS = {2, 3, 4};
    public static final int[] SPRINKLER_RADIUS = {1, 2, 3};
    public static final int[] VACUUM_RADIUS = {3, 5, 8};
    public static final int[] DETECTOR_RADIUS = {2, 4, 8, 16};
    /** Timer interval and pulse length choices, in ticks. */
    public static final int[] TIMER_INTERVALS = {10, 20, 40, 60, 100, 200, 300, 600, 1200};
    public static final int[] PULSE_LENGTHS = {2, 4, 10, 20};
    private static final int[] OLD_TIMER_SECONDS = {1, 2, 5, 10, 30, 60};
    public static final String[] DETECTOR_MODES = {"players", "monsters", "animals", "items", "living"};
    /** Harvester output: 0 = any neighbouring container, 1..6 = only the one on side Direction.from3DDataValue(i - 1), 7 = keep. */
    public static final int OUTPUT_AUTO = 0;
    public static final int OUTPUT_KEEP = 7;
    /** Redstone modes: run always, only with a signal, only without one. */
    public static final int RS_ALWAYS = 0;
    public static final int RS_HIGH = 1;
    public static final int RS_LOW = 2;
    /** How long after its last job a machine still reads as "working", in ticks. */
    private static final int RECENT = 60;

    /** What the machine is doing, shown on the status line of its screen (lamp: 0 green, 1 amber, 2 red). */
    public enum Status {
        HARVESTING(0), NO_RIPE_CROPS(1), WATERING(0), NO_PLANTS(1), COLLECTING(0), WAITING_ITEMS(1), OUTPUT_FULL(2),
        NEEDS_SIGNAL(1), STOPPED_BY_SIGNAL(1), READY_BREAK(0), NOTHING_TO_BREAK(1), CANT_BREAK(2), READY_PLACE(0),
        FRONT_BLOCKED(2), NO_BLOCKS(2), COUNTDOWN(0), PULSE(0), BROADCASTING(0), SILENT(1), RECEIVING(0),
        NO_TRANSMITTER(1), DETECTED(0), NOTHING_NEAR(1);

        public final int lamp;

        Status(int lamp) {
            this.lamp = lamp;
        }

        public static Status byId(int id) {
            Status[] all = values();
            return all[Math.floorMod(id, all.length)];
        }
    }

    /** Transmitters and receivers per dimension and channel (an index only: each hit is re-checked in the world). */
    private static final Map<String, Set<BlockPos>> TRANSMITTERS = new HashMap<>();
    private static final Map<String, Set<BlockPos>> RECEIVERS = new HashMap<>();

    private NonNullList<ItemStack> items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
    /** Vacuum Hopper item filter: ghost copies, never real items. */
    public final SimpleContainer filter = new SimpleContainer(FILTER_SIZE) {
        @Override
        public void setChanged() {
            super.setChanged();
            MachineBlockEntity.this.setChanged();
        }
    };
    private int setting = -1;
    private int mode;
    private int channel;
    private int xp;
    private int signal;
    private int redstone = RS_ALWAYS;
    private boolean replant = true;
    private boolean collectXp = true;
    private boolean whitelist = true;
    private boolean inverted;
    private int output = OUTPUT_AUTO;
    private int interval = 4;
    private int pulse = 1;
    private long ticker;
    private int countdown = -1;
    private int pulseLeft;
    private int quiet;
    private boolean timerAllowed = true;
    private boolean lastInput;
    private boolean outputFull;
    private long lastWork = -1000;
    private int detected;
    // live status, refreshed while a screen is open
    private Status status = Status.WAITING_ITEMS;
    private int statusArg;
    private int countA;
    private int countB;
    private int sides;
    private ItemStack preview = ItemStack.EMPTY;

    /** Server-side view of the settings and status for the open screens (see MachineMenu.D_*). */
    public final ContainerData data = new ContainerData() {
        @Override
        public int get(int i) {
            return switch (i) {
                case MachineMenu.D_RADIUS -> settingIndex();
                case MachineMenu.D_REDSTONE -> redstone;
                case MachineMenu.D_STATUS -> status.ordinal();
                case MachineMenu.D_STATUS_ARG -> clampShort(statusArg);
                case MachineMenu.D_CHANNEL -> channel;
                case MachineMenu.D_FLAGS -> (replant ? 1 : 0) | (collectXp ? 2 : 0) | (whitelist ? 4 : 0) | (inverted ? 8 : 0)
                        | (lastInput ? 16 : 0) | (getBlockState().getValue(MachineBlock.POWERED) ? 32 : 0);
                case MachineMenu.D_TARGET -> mode;
                case MachineMenu.D_OUTPUT -> output;
                case MachineMenu.D_INTERVAL -> interval;
                case MachineMenu.D_PULSE -> pulse;
                case MachineMenu.D_COUNTDOWN -> clampShort(Math.max(0, countdown));
                case MachineMenu.D_XP -> clampShort(xp);
                case MachineMenu.D_COUNT_A -> clampShort(countA);
                case MachineMenu.D_COUNT_B -> clampShort(countB);
                case MachineMenu.D_SIDES -> sides;
                default -> 0;
            };
        }

        @Override
        public void set(int i, int value) {
        }

        @Override
        public int getCount() {
            return MachineMenu.DATA_COUNT;
        }
    };

    public MachineBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.MACHINE.get(), pos, state);
    }

    public MachineBlock.Kind kind() {
        return getBlockState().getBlock() instanceof MachineBlock m ? m.kind() : MachineBlock.Kind.TIMER;
    }

    public int signal() {
        return signal;
    }

    public ItemStack preview() {
        return preview;
    }

    private static int clampShort(int v) {
        return Math.max(Short.MIN_VALUE, Math.min(Short.MAX_VALUE, v));
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
        return new MachineMenu(containerId, inventory, this);
    }

    @Override
    public int getContainerSize() {
        return SIZE;
    }

    /** Machines without a buffer (timer, sprinkler...) don't swallow what a hopper pushes into them. */
    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        return kind().hasInventory;
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        ContainerHelper.saveAllItems(output.child("filter"), filter.getItems());
        output.putInt("setting", setting);
        output.putInt("mode", mode);
        output.putInt("channel", channel);
        output.putInt("xp", xp);
        output.putInt("signal", signal);
        output.putInt("redstone", redstone);
        output.putBoolean("replant", replant);
        output.putBoolean("collect_xp", collectXp);
        output.putBoolean("whitelist", whitelist);
        output.putBoolean("inverted", inverted);
        output.putInt("output", this.output);
        output.putInt("interval", interval);
        output.putInt("pulse", pulse);
        output.putInt("countdown", countdown);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        filter.clearContent();
        ContainerHelper.loadAllItems(input.childOrEmpty("filter"), filter.getItems());
        setting = input.getIntOr("setting", -1);
        mode = Math.floorMod(input.getIntOr("mode", 0), DETECTOR_MODES.length);
        channel = Math.floorMod(input.getIntOr("channel", 0), 16);
        xp = Math.max(0, input.getIntOr("xp", 0));
        signal = input.getIntOr("signal", 0);
        redstone = Math.floorMod(input.getIntOr("redstone", RS_ALWAYS), 3);
        replant = input.getBooleanOr("replant", true);
        collectXp = input.getBooleanOr("collect_xp", true);
        whitelist = input.getBooleanOr("whitelist", true);
        inverted = input.getBooleanOr("inverted", false);
        output = Math.floorMod(input.getIntOr("output", OUTPUT_AUTO), 8);
        int savedInterval = input.getIntOr("interval", -1);
        if (savedInterval < 0 && setting >= 0) {
            // worlds from before the screen: "setting" was an index into 1, 2, 5, 10, 30, 60 seconds
            interval = closest(TIMER_INTERVALS, OLD_TIMER_SECONDS[setting % OLD_TIMER_SECONDS.length] * 20);
        } else {
            interval = Math.floorMod(savedInterval < 0 ? 4 : savedInterval, TIMER_INTERVALS.length);
        }
        pulse = Math.floorMod(input.getIntOr("pulse", 1), PULSE_LENGTHS.length);
        countdown = input.getIntOr("countdown", -1);
    }

    private static int closest(int[] options, int value) {
        int best = 0;
        for (int i = 1; i < options.length; i++) {
            if (Math.abs(options[i] - value) < Math.abs(options[best] - value)) {
                best = i;
            }
        }
        return best;
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level instanceof ServerLevel server) {
            unregister(server);
        }
    }

    // ------------------------------------------------------------------ settings
    /** The radius choices of this machine (empty for machines without an area). */
    public static int[] radii(MachineBlock.Kind kind) {
        return switch (kind) {
            case HARVESTER -> HARVEST_RADIUS;
            case SPRINKLER -> SPRINKLER_RADIUS;
            case VACUUM -> VACUUM_RADIUS;
            case DETECTOR -> DETECTOR_RADIUS;
            default -> new int[0];
        };
    }

    private int settingIndex() {
        int[] opts = radii(kind());
        if (opts.length == 0) {
            return 0;
        }
        return setting < 0 ? Math.min(1, opts.length - 1) : setting % opts.length;
    }

    private int radius() {
        int[] opts = radii(kind());
        return opts.length == 0 ? 0 : opts[settingIndex()];
    }

    /** The block area a machine works in, for its radius (shared by the server and the client's area preview). */
    public static AABB workArea(MachineBlock.Kind kind, BlockPos pos, int radius) {
        return switch (kind) {
            case HARVESTER -> new AABB(pos.getX() - radius, pos.getY() - 1, pos.getZ() - radius,
                    pos.getX() + radius + 1, pos.getY() + 2, pos.getZ() + radius + 1);
            case SPRINKLER -> new AABB(pos.getX() - radius, pos.getY() - 2, pos.getZ() - radius,
                    pos.getX() + radius + 1, pos.getY() + 1, pos.getZ() + radius + 1);
            default -> new AABB(pos).inflate(radius);
        };
    }

    public static int intervalTicks(int index) {
        return TIMER_INTERVALS[Math.floorMod(index, TIMER_INTERVALS.length)];
    }

    /** Pulse length in ticks, never longer than the interval allows. */
    public static int pulseTicks(int pulseIndex, int intervalIndex) {
        return Math.max(1, Math.min(PULSE_LENGTHS[Math.floorMod(pulseIndex, PULSE_LENGTHS.length)], intervalTicks(intervalIndex) - 2));
    }

    private static void tell(Player player, Component message) {
        if (player instanceof ServerPlayer sp) {
            sp.sendOverlayMessage(message.copy().withStyle(ChatFormatting.GOLD));
        }
    }

    private Component area() {
        int size = radius() * 2 + 1;
        return Component.translatable("message.wayfarers.machine.area", size, size);
    }

    private Component channelName() {
        DyeColor color = DyeColor.byId(channel);
        return Component.translatable("color.minecraft." + color.getName()).withColor(color.getTextColor());
    }

    private void click() {
        if (level != null) {
            level.playSound(null, worldPosition, SoundEvents.COMPARATOR_CLICK, SoundSource.BLOCKS, 0.4F, 1.2F);
        }
    }

    /** Right-click: the machine's screen. */
    public void openScreen(ServerPlayer player) {
        if (level instanceof ServerLevel server) {
            refreshStatus(server);
        }
        ((net.minecraftforge.common.extensions.IForgeServerPlayer) player).openMenu(this, buf -> {
            buf.writeBlockPos(worldPosition);
            buf.writeVarInt(kind().ordinal());
        });
    }

    /** Sneak-click with the Brass Wrench: the main setting, one step, without opening the screen. */
    public void quickCycle(ServerPlayer player) {
        MachineBlock.Kind kind = kind();
        switch (kind) {
            case HARVESTER, VACUUM, SPRINKLER -> {
                setting = (settingIndex() + 1) % radii(kind).length;
                tell(player, area());
            }
            case TIMER -> {
                interval = (interval + 1) % TIMER_INTERVALS.length;
                countdown = Math.min(countdown, intervalTicks(interval));
                tell(player, Component.translatable("message.wayfarers.machine.interval", seconds(intervalTicks(interval))));
            }
            case DETECTOR -> {
                mode = (mode + 1) % DETECTOR_MODES.length;
                tell(player, Component.translatable("message.wayfarers.machine.detector",
                        Component.translatable("message.wayfarers.machine.detector." + DETECTOR_MODES[mode]), radius()));
            }
            case TRANSMITTER, RECEIVER -> tell(player, Component.translatable("message.wayfarers.machine.channel", channelName()));
            case BREAKER, PLACER -> {
                openScreen(player);
                return;
            }
        }
        setChanged();
        click();
    }

    /** "1", "0.5", "2.5": seconds for messages. */
    public static String seconds(int ticks) {
        return ticks % 20 == 0 ? String.valueOf(ticks / 20) : String.valueOf(ticks / 20.0);
    }

    public void setChannel(Player player, int newChannel, boolean announce) {
        if (level instanceof ServerLevel server) {
            unregister(server);
        }
        channel = Math.floorMod(newChannel, 16);
        setChanged();
        if (announce) {
            tell(player, Component.translatable("message.wayfarers.machine.channel", channelName()));
        }
        if (level instanceof ServerLevel server) {
            register(server);
        }
        if (level != null) {
            level.playSound(null, worldPosition, SoundEvents.DYE_USE, SoundSource.BLOCKS, 0.8F, 1.0F);
        }
    }

    /**
     * A setting changed from the screen ({@link MachineMenu#clickMenuButton}). Everything is validated here: the
     * value range and whether this kind of machine has that setting at all. Returns whether it was accepted.
     */
    public boolean applySetting(ServerPlayer player, int action, int value) {
        MachineBlock.Kind kind = kind();
        switch (action) {
            case MachineMenu.A_RADIUS -> {
                if (value < 0 || value >= radii(kind).length) {
                    return false;
                }
                setting = value;
            }
            case MachineMenu.A_REDSTONE -> {
                if (!kind.hasRedstoneMode() || value < 0 || value > 2) {
                    return false;
                }
                redstone = value;
            }
            case MachineMenu.A_CHANNEL -> {
                if ((kind != MachineBlock.Kind.TRANSMITTER && kind != MachineBlock.Kind.RECEIVER) || value < 0 || value > 15) {
                    return false;
                }
                setChannel(player, value, false);
            }
            case MachineMenu.A_TOGGLE -> {
                switch (value) {
                    case MachineMenu.T_REPLANT -> {
                        if (kind != MachineBlock.Kind.HARVESTER) {
                            return false;
                        }
                        replant = !replant;
                    }
                    case MachineMenu.T_COLLECT_XP -> {
                        if (kind != MachineBlock.Kind.VACUUM) {
                            return false;
                        }
                        collectXp = !collectXp;
                    }
                    case MachineMenu.T_WHITELIST -> {
                        if (kind != MachineBlock.Kind.VACUUM) {
                            return false;
                        }
                        whitelist = !whitelist;
                    }
                    case MachineMenu.T_INVERTED -> {
                        if (kind != MachineBlock.Kind.DETECTOR) {
                            return false;
                        }
                        inverted = !inverted;
                        if (level instanceof ServerLevel server) {
                            detect(server, getBlockState()); // flip the output right away
                        }
                    }
                    default -> {
                        return false;
                    }
                }
            }
            case MachineMenu.A_TARGET -> {
                if (kind != MachineBlock.Kind.DETECTOR || value < 0 || value >= DETECTOR_MODES.length) {
                    return false;
                }
                mode = value;
            }
            case MachineMenu.A_OUTPUT -> {
                if (kind != MachineBlock.Kind.HARVESTER || value < 0 || value > OUTPUT_KEEP) {
                    return false;
                }
                output = value;
                outputFull = false;
            }
            case MachineMenu.A_INTERVAL -> {
                if (kind != MachineBlock.Kind.TIMER || value < 0 || value >= TIMER_INTERVALS.length) {
                    return false;
                }
                interval = value;
                countdown = Math.min(countdown, intervalTicks(interval));
            }
            case MachineMenu.A_PULSE -> {
                if (kind != MachineBlock.Kind.TIMER || value < 0 || value >= PULSE_LENGTHS.length) {
                    return false;
                }
                pulse = value;
            }
            case MachineMenu.A_TAKE_XP -> {
                if (kind != MachineBlock.Kind.VACUUM || xp <= 0) {
                    return false;
                }
                player.giveExperiencePoints(xp);
                tell(player, Component.translatable("message.wayfarers.machine.xp", xp));
                xp = 0;
                player.level().playSound(null, player.blockPosition(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, 0.5F, 1.0F);
            }
            default -> {
                return false;
            }
        }
        setChanged();
        if (action != MachineMenu.A_CHANNEL && action != MachineMenu.A_TAKE_XP) {
            click();
        }
        if (level instanceof ServerLevel server) {
            refreshStatus(server);
        }
        return true;
    }

    // ------------------------------------------------------------------ redstone mode
    private boolean redstoneAllows(ServerLevel level) {
        if (!kind().hasRedstoneMode()) {
            return true;
        }
        lastInput = level.hasNeighborSignal(worldPosition);
        return switch (redstone) {
            case RS_HIGH -> lastInput;
            case RS_LOW -> !lastInput;
            default -> true;
        };
    }

    private Status gatedStatus() {
        return redstone == RS_HIGH ? Status.NEEDS_SIGNAL : Status.STOPPED_BY_SIGNAL;
    }

    // ------------------------------------------------------------------ ticking
    void serverTick(ServerLevel level, BlockState state) {
        ticker++;
        switch (kind()) {
            case HARVESTER -> {
                if (ticker % 40 == 0 && redstoneAllows(level)) {
                    harvest(level);
                }
            }
            case SPRINKLER -> {
                if (ticker % 20 == 0 && redstoneAllows(level)) {
                    sprinkle(level);
                }
            }
            case VACUUM -> {
                if (ticker % 5 == 0 && redstoneAllows(level)) {
                    vacuum(level);
                }
                if (ticker % 10 == 0) {
                    pushDown(level);
                }
            }
            case TIMER -> timerTick(level, state);
            case TRANSMITTER, RECEIVER -> {
                if (ticker % 5 == 0) {
                    register(level);
                    if (kind() == MachineBlock.Kind.RECEIVER) {
                        boolean on = anyTransmitter(level);
                        if (on != state.getValue(MachineBlock.POWERED)) {
                            setPowered(level, state, on);
                        }
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

    private void timerTick(ServerLevel level, BlockState state) {
        boolean on = state.getValue(MachineBlock.POWERED);
        if (on && --pulseLeft <= 0) {
            setPowered(level, state, false);
            state = getBlockState();
            on = false;
            quiet = 2;
        }
        if (quiet > 0) {
            // our own pulse is still fading out of the wires around: keep the last reading of the input
            quiet--;
        } else if (!on) {
            timerAllowed = redstoneAllows(level);
        }
        if (!timerAllowed) {
            return; // paused: the countdown waits where it is
        }
        if (countdown < 0 || countdown > intervalTicks(interval)) {
            countdown = intervalTicks(interval);
        }
        if (--countdown <= 0) {
            // exactly one pulse per interval: the countdown keeps running while a pulse is on
            countdown = intervalTicks(interval);
            if (!on) {
                pulseLeft = pulseTicks(pulse, interval);
                setPowered(level, state, true);
            }
        }
    }

    private void setPowered(ServerLevel level, BlockState state, boolean on) {
        level.setBlock(worldPosition, state.setValue(MachineBlock.POWERED, on), Block.UPDATE_ALL);
    }

    // ------------------------------------------------------------------ live status (while a screen is open)
    /** Recomputes the status line, the channel counts, the neighbour containers and the preview slot. */
    public void refreshStatus(ServerLevel level) {
        MachineBlock.Kind kind = kind();
        BlockState state = getBlockState();
        sides = 0;
        for (Direction d : Direction.values()) {
            BlockPos np = worldPosition.relative(d);
            if (!(level.getBlockEntity(np) instanceof MachineBlockEntity) && HopperBlockEntity.getContainerAt(level, np) != null) {
                sides |= 1 << d.get3DDataValue();
            }
        }
        boolean recent = level.getGameTime() - lastWork < RECENT;
        statusArg = 0;
        preview = ItemStack.EMPTY;
        switch (kind) {
            case HARVESTER -> {
                int ripe = countRipe(level);
                statusArg = ripe;
                if (!redstoneAllows(level)) {
                    status = gatedStatus();
                } else if (outputFull && bufferFull()) {
                    status = Status.OUTPUT_FULL;
                } else {
                    status = ripe > 0 || recent ? Status.HARVESTING : Status.NO_RIPE_CROPS;
                }
            }
            case SPRINKLER -> {
                int plants = countPlants(level);
                statusArg = plants;
                status = !redstoneAllows(level) ? gatedStatus() : plants > 0 ? Status.WATERING : Status.NO_PLANTS;
            }
            case VACUUM -> {
                if (!redstoneAllows(level)) {
                    status = gatedStatus();
                } else if (outputFull && bufferFull()) {
                    status = Status.OUTPUT_FULL;
                } else {
                    status = recent ? Status.COLLECTING : Status.WAITING_ITEMS;
                }
            }
            case BREAKER -> {
                Direction facing = state.getValue(MachineBlock.FACING);
                BlockPos front = worldPosition.relative(facing);
                BlockState target = level.getBlockState(front);
                if (target.isAir() || target.getBlock() instanceof LiquidBlock) {
                    status = Status.NOTHING_TO_BREAK;
                } else {
                    preview = new ItemStack(target.getBlock());
                    status = breakable(level, front, target) ? Status.READY_BREAK : Status.CANT_BREAK;
                }
                if (status == Status.READY_BREAK && bufferFull() && (sides & (1 << facing.getOpposite().get3DDataValue())) == 0) {
                    status = Status.OUTPUT_FULL;
                }
            }
            case PLACER -> {
                Direction facing = state.getValue(MachineBlock.FACING);
                BlockPos front = worldPosition.relative(facing);
                preview = nextBlock(level, facing);
                if (!level.getBlockState(front).canBeReplaced()) {
                    status = Status.FRONT_BLOCKED;
                } else {
                    status = preview.isEmpty() ? Status.NO_BLOCKS : Status.READY_PLACE;
                }
            }
            case TIMER -> {
                if (state.getValue(MachineBlock.POWERED)) {
                    status = Status.PULSE;
                } else if (!timerAllowed) {
                    status = gatedStatus();
                } else {
                    status = Status.COUNTDOWN;
                }
            }
            case TRANSMITTER, RECEIVER -> {
                register(level);
                countA = channelCount(level, TRANSMITTERS, MachineBlock.Kind.TRANSMITTER);
                countB = channelCount(level, RECEIVERS, MachineBlock.Kind.RECEIVER);
                boolean on = state.getValue(MachineBlock.POWERED);
                if (kind == MachineBlock.Kind.TRANSMITTER) {
                    status = on ? Status.BROADCASTING : Status.SILENT;
                } else {
                    status = on ? Status.RECEIVING : Status.NO_TRANSMITTER;
                }
            }
            case DETECTOR -> {
                countA = detected;
                statusArg = detected;
                status = detected > 0 ? Status.DETECTED : Status.NOTHING_NEAR;
            }
        }
    }

    private boolean bufferFull() {
        for (ItemStack stack : items) {
            if (stack.isEmpty() || stack.getCount() < stack.getMaxStackSize()) {
                return false;
            }
        }
        return true;
    }

    // ------------------------------------------------------------------ harvester
    private int countRipe(ServerLevel level) {
        int r = radius();
        int n = 0;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -1, -r), worldPosition.offset(r, 1, r))) {
            BlockState s = level.getBlockState(p);
            if (QolEvents.replanted(s) != null || ((s.is(Blocks.MELON) || s.is(Blocks.PUMPKIN)) && besideAttachedStem(level, p))) {
                n++;
            }
        }
        return n;
    }

    private void harvest(ServerLevel level) {
        int r = radius();
        int done = 0;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -1, -r), worldPosition.offset(r, 1, r))) {
            if (done >= 16) {
                break;
            }
            BlockState s = level.getBlockState(p);
            BlockState replanted = QolEvents.replanted(s);
            if (replanted != null) {
                List<ItemStack> drops = Block.getDrops(s, level, p, null);
                if (replant) {
                    Block seedBlock = s.getBlock();
                    boolean seedTaken = false;
                    for (ItemStack drop : drops) {
                        if (!seedTaken && drop.getItem() == seedBlock.asItem()) {
                            drop.shrink(1);
                            seedTaken = true;
                        }
                    }
                    level.setBlock(p, replanted, Block.UPDATE_ALL);
                } else {
                    level.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                }
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
            lastWork = level.getGameTime();
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
        boolean full = false;
        for (ItemStack drop : drops) {
            ItemStack rest = switch (output) {
                case OUTPUT_AUTO -> store(level, drop, null);
                case OUTPUT_KEEP -> InventoryUtil.insert(this, drop, false);
                default -> store(level, drop, Direction.from3DDataValue(output - 1));
            };
            if (!rest.isEmpty()) {
                full = true;
                Block.popResource(level, worldPosition.above(), rest);
            }
        }
        outputFull = full;
    }

    /** Puts a stack into a neighbouring container (only {@code only} when given), then into the buffer. */
    private ItemStack store(ServerLevel level, ItemStack stack, Direction only) {
        List<Direction> order = new ArrayList<>();
        if (only != null) {
            order.add(only);
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
    private static boolean growable(BlockState s) {
        return s.isRandomlyTicking() && (s.getBlock() instanceof BonemealableBlock || s.is(Blocks.SUGAR_CANE)
                || s.is(Blocks.CACTUS) || s.is(Blocks.NETHER_WART)) && !s.is(Blocks.GRASS_BLOCK);
    }

    private int countPlants(ServerLevel level) {
        int r = radius();
        int n = 0;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -2, -r), worldPosition.offset(r, 0, r))) {
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof FarmlandBlock || growable(s)) {
                n++;
            }
        }
        return n;
    }

    private void sprinkle(ServerLevel level) {
        int r = radius();
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -2, -r), worldPosition.offset(r, 0, r))) {
            BlockState s = level.getBlockState(p);
            if (s.getBlock() instanceof FarmlandBlock && s.getValue(FarmlandBlock.MOISTURE) < FarmlandBlock.MAX_MOISTURE) {
                level.setBlock(p, s.setValue(FarmlandBlock.MOISTURE, FarmlandBlock.MAX_MOISTURE), Block.UPDATE_CLIENTS);
            } else if (growable(s) && level.getRandom().nextInt(3) == 0) {
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
    /** Whether the filter lets this item in: an empty filter takes everything. */
    public boolean passesFilter(ItemStack stack) {
        boolean any = false;
        boolean match = false;
        for (ItemStack f : filter.getItems()) {
            if (!f.isEmpty()) {
                any = true;
                match |= f.is(stack.getItem());
            }
        }
        return !any || match == whitelist;
    }

    private void vacuum(ServerLevel level) {
        AABB area = new AABB(worldPosition).inflate(radius());
        boolean full = false;
        for (ItemEntity drop : level.getEntitiesOfClass(ItemEntity.class, area,
                e -> e.isAlive() && !e.hasPickUpDelay() && passesFilter(e.getItem()))) {
            ItemStack before = drop.getItem();
            ItemStack rest = InventoryUtil.insert(this, before, false);
            if (rest.getCount() != before.getCount()) {
                lastWork = level.getGameTime();
                level.sendParticles(ParticleTypes.PORTAL, drop.getX(), drop.getY() + 0.2, drop.getZ(), 4, 0.1, 0.1, 0.1, 0.2);
                if (rest.isEmpty()) {
                    drop.discard();
                } else {
                    drop.setItem(rest);
                }
            }
            full |= !rest.isEmpty();
        }
        outputFull = full;
        if (collectXp) {
            for (ExperienceOrb orb : level.getEntitiesOfClass(ExperienceOrb.class, area, Entity::isAlive)) {
                xp += orb.getValue();
                orb.discard();
                lastWork = level.getGameTime();
                setChanged();
            }
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
    private static boolean breakable(ServerLevel level, BlockPos front, BlockState target) {
        return !target.isAir() && !(target.getBlock() instanceof LiquidBlock) && target.getDestroySpeed(level, front) >= 0
                && !(target.getBlock() instanceof MachineBlock);
    }

    void pulse(ServerLevel level) {
        BlockState state = getBlockState();
        Direction facing = state.getValue(MachineBlock.FACING);
        BlockPos front = worldPosition.relative(facing);
        BlockState target = level.getBlockState(front);
        if (kind() == MachineBlock.Kind.BREAKER) {
            if (!breakable(level, front, target)) {
                return;
            }
            // a door, tall plant or bed only drops from one of its halves; the other half goes with it
            BlockPos dropPos = front;
            if (target.hasProperty(BlockStateProperties.DOUBLE_BLOCK_HALF)
                    && target.getValue(BlockStateProperties.DOUBLE_BLOCK_HALF) == DoubleBlockHalf.UPPER) {
                dropPos = front.below();
            } else if (target.hasProperty(BlockStateProperties.BED_PART)
                    && target.getValue(BlockStateProperties.BED_PART) == BedPart.FOOT) {
                dropPos = front.relative(BedBlock.getConnectedDirection(target));
            }
            BlockState dropState = level.getBlockState(dropPos);
            if (!dropState.is(target.getBlock())) {
                dropPos = front;
                dropState = target;
            }
            List<ItemStack> drops = Block.getDrops(dropState, level, dropPos, level.getBlockEntity(dropPos), null,
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
            if (placeFrom(level, behind(level, facing), front, facing) || placeFrom(level, this, front, facing)) {
                level.sendParticles(ParticleTypes.CLOUD, front.getX() + 0.5, front.getY() + 0.5, front.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.01);
            }
        }
    }

    private Container behind(ServerLevel level, Direction facing) {
        BlockPos back = worldPosition.relative(facing.getOpposite());
        return level.getBlockEntity(back) instanceof MachineBlockEntity ? null : HopperBlockEntity.getContainerAt(level, back);
    }

    /** The block the Placer would place next (from the chest behind first, then its own slots), or empty. */
    private ItemStack nextBlock(ServerLevel level, Direction facing) {
        for (Container from : new Container[] {behind(level, facing), this}) {
            if (from == null) {
                continue;
            }
            for (int i = 0; i < from.getContainerSize(); i++) {
                ItemStack stack = from.getItem(i);
                if (stack.getItem() instanceof BlockItem) {
                    return stack.copyWithCount(1);
                }
            }
        }
        return ItemStack.EMPTY;
    }

    /**
     * Places the first block item of {@code from} that can go at {@code front}, the way a dispenser places a shulker
     * box: the item's own placement (both halves of doors and beds, contents of shulker boxes, waystone names...)
     * and the item is used up by it.
     */
    private static boolean placeFrom(ServerLevel level, Container from, BlockPos front, Direction facing) {
        if (from == null) {
            return false;
        }
        Direction clickedFace = level.isEmptyBlock(front.below()) ? facing : Direction.UP;
        for (int i = 0; i < from.getContainerSize(); i++) {
            ItemStack stack = from.getItem(i);
            if (stack.getItem() instanceof BlockItem bi
                    && bi.place(new DirectionalPlaceContext(level, front, facing, stack, clickedFace)).consumesAction()) {
                from.setChanged();
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------ wireless redstone
    private static String key(ServerLevel level, int channel) {
        return level.dimension().identifier() + "#" + channel;
    }

    private Map<String, Set<BlockPos>> index() {
        return kind() == MachineBlock.Kind.TRANSMITTER ? TRANSMITTERS : kind() == MachineBlock.Kind.RECEIVER ? RECEIVERS : null;
    }

    private void register(ServerLevel level) {
        Map<String, Set<BlockPos>> index = index();
        if (index != null) {
            index.computeIfAbsent(key(level, channel), k -> new HashSet<>()).add(worldPosition.immutable());
        }
    }

    private void unregister(ServerLevel level) {
        Map<String, Set<BlockPos>> index = index();
        if (index != null) {
            // (not getOrDefault(..., Set.of()): removing from an immutable set throws)
            Set<BlockPos> old = index.get(key(level, channel));
            if (old != null) {
                old.remove(worldPosition);
            }
        }
    }

    /** Machines of {@code kind} on this machine's channel in this dimension (loaded ones only). */
    private int channelCount(ServerLevel level, Map<String, Set<BlockPos>> index, MachineBlock.Kind kind) {
        Set<BlockPos> set = index.get(key(level, channel));
        if (set == null) {
            return 0;
        }
        set.removeIf(p -> !level.isLoaded(p) || !(level.getBlockEntity(p) instanceof MachineBlockEntity m)
                || m.kind() != kind || m.channel != channel);
        return set.size();
    }

    private boolean anyTransmitter(ServerLevel level) {
        if (channelCount(level, TRANSMITTERS, MachineBlock.Kind.TRANSMITTER) == 0) {
            return false;
        }
        for (BlockPos p : TRANSMITTERS.get(key(level, channel))) {
            if (level.getBlockState(p).getValue(MachineBlock.POWERED)) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------------ detector
    private void detect(ServerLevel level, BlockState state) {
        AABB area = new AABB(worldPosition).inflate(radius());
        Predicate<Entity> filter = switch (DETECTOR_MODES[mode % DETECTOR_MODES.length]) {
            case "players" -> e -> e instanceof Player p && !p.isSpectator();
            case "monsters" -> e -> e instanceof Enemy;
            case "animals" -> e -> e instanceof Animal;
            case "items" -> e -> e instanceof ItemEntity;
            default -> e -> e instanceof LivingEntity && !(e instanceof Player p && p.isSpectator());
        };
        detected = level.getEntitiesOfClass(Entity.class, area, e -> e.isAlive() && filter.test(e)).size();
        int newSignal = inverted ? (detected == 0 ? 15 : 0) : Math.min(15, detected);
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

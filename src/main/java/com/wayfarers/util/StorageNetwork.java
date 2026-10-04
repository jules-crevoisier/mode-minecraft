package com.wayfarers.util;

import com.wayfarers.block.CrateBlockEntity;
import com.wayfarers.block.GuildTerminalBlockEntity;
import com.wayfarers.block.MachineBlockEntity;
import com.wayfarers.block.SortingChestBlockEntity;
import com.wayfarers.block.StorageRelayBlockEntity;
import com.wayfarers.config.WayfarersConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.block.entity.DispenserBlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.entity.ShulkerBoxBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.ChestType;
import net.minecraft.world.level.chunk.LevelChunk;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * The storage a Guild Terminal sees. No cables, no power: every real storage container (chest, barrel, shulker box,
 * sorting chest, compacting crate, other mods' chests) within the terminal's reach is linked, plus everything within
 * reach of a Storage Relay that is itself within reach of the terminal or of another linked relay.
 *
 * <p>Scanning walks the block entities of the loaded chunks in reach (never every block position), and the terminal
 * caches the result for a few seconds. Machine buffers, hoppers, dispensers, crafters and unopened loot chests are
 * never linked. Unloaded chunks are simply not part of the network.
 */
public final class StorageNetwork {
    /** Most relays one network follows (bounds a scan). */
    public static final int MAX_RELAYS = 64;

    /** An item type and how many of it the network holds. */
    public record Entry(ItemStack type, int count) {}

    /** One linked container: a single block entity, or both halves of a double chest (key = the lower position). */
    public static final class Link {
        public final BlockPos key;
        public final List<BaseContainerBlockEntity> parts = new ArrayList<>(2);
        public final double distSqr;

        Link(BlockPos key, double distSqr) {
            this.key = key;
            this.distSqr = distSqr;
        }

        /** A container that was broken or unloaded since the scan must never be touched (that would dupe items). */
        public boolean valid() {
            for (BaseContainerBlockEntity be : parts) {
                if (be.isRemoved()) {
                    return false;
                }
            }
            return !parts.isEmpty();
        }

        public BaseContainerBlockEntity first() {
            return parts.get(0);
        }

        public int slots() {
            int n = 0;
            for (BaseContainerBlockEntity be : parts) {
                n += be.getContainerSize();
            }
            return n;
        }
    }

    /** Result of a scan: the linked containers, closest to the terminal first, and how many relays took part. */
    public record Scan(List<Link> links, int relays, boolean capped) {
        public static final Scan EMPTY = new Scan(List.of(), 0, false);
    }

    private record Node(BlockPos pos, int range) {}

    private record Key(ItemStack stack) {
        @Override
        public boolean equals(Object o) {
            return o instanceof Key k && ItemStack.isSameItemSameComponents(stack, k.stack);
        }

        @Override
        public int hashCode() {
            return ItemStack.hashItemAndComponents(stack);
        }
    }

    private StorageNetwork() {}

    public static int terminalRange() {
        return WayfarersConfig.TERMINAL_RANGE.get();
    }

    /** Is this block entity real storage (and not a machine buffer, a hopper or an unopened loot chest)? */
    public static boolean isStorage(BlockEntity be) {
        if (!(be instanceof BaseContainerBlockEntity c) || be instanceof MachineBlockEntity || be.isRemoved()) {
            return false;
        }
        // reading a loot chest would roll its loot remotely: it joins once a player has opened it
        if (be instanceof RandomizableContainerBlockEntity r && r.getLootTable() != null) {
            return false;
        }
        if (be instanceof ChestBlockEntity || be instanceof BarrelBlockEntity || be instanceof ShulkerBoxBlockEntity
                || be instanceof SortingChestBlockEntity || be instanceof CrateBlockEntity) {
            return true;
        }
        // other mods' chests; never dispensers, droppers, hoppers or crafters
        return be instanceof RandomizableContainerBlockEntity && !(be instanceof DispenserBlockEntity)
                && !(be instanceof HopperBlockEntity) && !(be instanceof CrafterBlockEntity) && c.getContainerSize() >= 27;
    }

    /**
     * The block entities of the loaded chunks within {@code horizontal} blocks (and {@code vertical} up and down) of
     * {@code center}. {@code getChunkNow} never loads or generates a chunk: unloaded parts of a base are left out.
     */
    public static List<BlockEntity> blockEntitiesAround(ServerLevel level, BlockPos center, int horizontal, int vertical) {
        int minY = Math.max(level.getMinY(), center.getY() - vertical);
        int maxY = Math.min(level.getMaxY(), center.getY() + vertical);
        int minX = center.getX() - horizontal, maxX = center.getX() + horizontal;
        int minZ = center.getZ() - horizontal, maxZ = center.getZ() + horizontal;
        List<BlockEntity> out = new ArrayList<>();
        for (int cx = minX >> 4; cx <= maxX >> 4; cx++) {
            for (int cz = minZ >> 4; cz <= maxZ >> 4; cz++) {
                LevelChunk chunk = level.getChunkSource().getChunkNow(cx, cz);
                if (chunk == null) {
                    continue;
                }
                for (BlockEntity be : chunk.getBlockEntities().values()) {
                    BlockPos p = be.getBlockPos();
                    if (p.getX() >= minX && p.getX() <= maxX && p.getZ() >= minZ && p.getZ() <= maxZ
                            && p.getY() >= minY && p.getY() <= maxY && !be.isRemoved()) {
                        out.add(be);
                    }
                }
            }
        }
        return out;
    }

    /** Every storage container linked to a terminal at {@code origin}: its own reach, then relay after relay. */
    public static Scan scan(ServerLevel level, BlockPos origin) {
        int height = WayfarersConfig.TERMINAL_HEIGHT.get();
        int relayRange = WayfarersConfig.RELAY_RANGE.get();
        int max = WayfarersConfig.MAX_CONTAINERS.get();
        Map<BlockPos, Link> links = new HashMap<>();
        Set<BlockPos> nodesSeen = new HashSet<>();
        ArrayDeque<Node> queue = new ArrayDeque<>();
        queue.add(new Node(origin, terminalRange()));
        nodesSeen.add(origin);
        int relays = 0;
        boolean capped = false;
        while (!queue.isEmpty()) {
            Node node = queue.poll();
            for (BlockEntity be : blockEntitiesAround(level, node.pos, node.range, height)) {
                BlockPos p = be.getBlockPos();
                if (be instanceof StorageRelayBlockEntity) {
                    if (relays < MAX_RELAYS && nodesSeen.add(p.immutable())) {
                        relays++;
                        queue.add(new Node(p.immutable(), relayRange));
                    }
                    continue;
                }
                if (!isStorage(be)) {
                    continue;
                }
                BlockPos key = linkKey(be);
                Link link = links.get(key);
                if (link == null) {
                    if (links.size() >= max) {
                        capped = true;
                        continue;
                    }
                    link = new Link(key, key.distSqr(origin));
                    links.put(key, link);
                }
                if (!link.parts.contains(be)) {
                    link.parts.add((BaseContainerBlockEntity) be);
                }
            }
        }
        List<Link> list = new ArrayList<>(links.values());
        list.sort(Comparator.comparingDouble(l -> l.distSqr));
        return new Scan(list, relays, capped);
    }

    /**
     * The Guild Terminal whose network a relay at {@code relay} belongs to, or null. Reach is symmetric, so this walks
     * the relay chain from the relay's side.
     */
    public static @Nullable BlockPos findTerminal(ServerLevel level, BlockPos relay) {
        int height = WayfarersConfig.TERMINAL_HEIGHT.get();
        int relayRange = WayfarersConfig.RELAY_RANGE.get();
        int terminalRange = terminalRange();
        Set<BlockPos> seen = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        queue.add(relay.immutable());
        seen.add(relay.immutable());
        while (!queue.isEmpty() && seen.size() <= MAX_RELAYS) {
            BlockPos node = queue.poll();
            BlockPos best = null;
            for (BlockEntity be : blockEntitiesAround(level, node, Math.max(terminalRange, relayRange), height)) {
                BlockPos p = be.getBlockPos();
                int dx = Math.abs(p.getX() - node.getX()), dz = Math.abs(p.getZ() - node.getZ());
                if (be instanceof GuildTerminalBlockEntity && dx <= terminalRange && dz <= terminalRange
                        && (best == null || p.distSqr(node) < best.distSqr(node))) {
                    best = p.immutable();
                } else if (be instanceof StorageRelayBlockEntity && dx <= relayRange && dz <= relayRange
                        && seen.add(p.immutable())) {
                    queue.add(p.immutable());
                }
            }
            if (best != null) {
                return best;
            }
        }
        return null;
    }

    /** Both halves of a double chest share one key (the lower of the two positions), so they count as one. */
    public static BlockPos linkKey(BlockEntity be) {
        BlockPos p = be.getBlockPos().immutable();
        BlockState state = be.getBlockState();
        if (be instanceof ChestBlockEntity && state.getBlock() instanceof ChestBlock
                && state.hasProperty(ChestBlock.TYPE) && state.getValue(ChestBlock.TYPE) != ChestType.SINGLE) {
            BlockPos other = p.relative(ChestBlock.getConnectedDirection(state));
            return other.compareTo(p) < 0 ? other.immutable() : p;
        }
        return p;
    }

    /** Storage containers within {@code range} blocks (a cube) of {@code center}, closest first; no relays. */
    public static List<Container> nearby(ServerLevel level, BlockPos center, int range) {
        List<BaseContainerBlockEntity> found = new ArrayList<>();
        for (BlockEntity be : blockEntitiesAround(level, center, range, range)) {
            if (isStorage(be)) {
                found.add((BaseContainerBlockEntity) be);
            }
        }
        found.sort(Comparator.comparingDouble(be -> be.getBlockPos().distSqr(center)));
        return new ArrayList<>(found);
    }

    /** Every item type in the network with its total count, most plentiful first. */
    public static List<Entry> contents(List<Container> containers) {
        // runs every half second per viewer on networks of thousands of slots: look up with the live stack and copy
        // it only for a new item type (the stored key must never be a live, mutable stack)
        Map<Key, int[]> totals = new LinkedHashMap<>();
        for (Container c : containers) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                ItemStack s = c.getItem(i);
                if (!s.isEmpty()) {
                    int[] total = totals.get(new Key(s));
                    if (total == null) {
                        totals.put(new Key(s.copyWithCount(1)), new int[] {s.getCount()});
                    } else {
                        total[0] = (int) Math.min(Integer.MAX_VALUE, (long) total[0] + s.getCount());
                    }
                }
            }
        }
        List<Entry> list = new ArrayList<>(totals.size());
        totals.forEach((k, v) -> list.add(new Entry(k.stack, v[0])));
        list.sort(Comparator.comparingInt(Entry::count).reversed());
        return list;
    }

    public static int freeSlots(List<Container> containers) {
        int n = 0;
        for (Container c : containers) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                if (c.getItem(i).isEmpty()) {
                    n++;
                }
            }
        }
        return n;
    }

    public static int count(List<Container> containers, ItemStack type) {
        int n = 0;
        for (Container c : containers) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                ItemStack s = c.getItem(i);
                if (ItemStack.isSameItemSameComponents(s, type)) {
                    n += s.getCount();
                }
            }
        }
        return n;
    }

    /** Removes up to {@code amount} items like {@code type} from the network and returns them as one stack. */
    public static ItemStack extract(List<Container> containers, ItemStack type, int amount) {
        int want = Math.min(amount, type.getMaxStackSize());
        ItemStack out = ItemStack.EMPTY;
        if (type.isEmpty() || want <= 0) {
            return out;
        }
        // take from the far end of the list first: the closest containers are where new items go
        for (int ci = containers.size() - 1; ci >= 0 && want > 0; ci--) {
            Container c = containers.get(ci);
            boolean touched = false;
            for (int i = 0; i < c.getContainerSize() && want > 0; i++) {
                ItemStack s = c.getItem(i);
                if (!s.isEmpty() && ItemStack.isSameItemSameComponents(s, type)) {
                    int take = Math.min(want, s.getCount());
                    if (out.isEmpty()) {
                        out = s.copyWithCount(take);
                    } else {
                        out.grow(take);
                    }
                    ItemStack left = s.copy();
                    left.shrink(take);
                    c.setItem(i, left.isEmpty() ? ItemStack.EMPTY : left);
                    want -= take;
                    touched = true;
                }
            }
            if (touched) {
                c.setChanged();
            }
        }
        return out;
    }

    /** Puts {@code stack} into the network; returns what is left. See {@link Inserter} for where items go. */
    public static ItemStack insert(List<Container> containers, ItemStack stack) {
        return new Inserter(containers).insert(stack);
    }

    /**
     * Stores items in a network, in this order: containers that already hold the same item (closest first), then
     * sorting chests, then any free slot (empty compacting crates last, so they are not claimed by random items).
     * Indexes the network once, so storing a whole inventory costs one pass over the network.
     */
    public static final class Inserter {
        private final List<Container> containers;
        private Map<Key, List<Container>> holders;

        public Inserter(List<Container> containers) {
            this.containers = containers;
        }

        private Map<Key, List<Container>> holders() {
            if (holders == null) {
                holders = new HashMap<>();
                for (Container c : containers) {
                    for (int i = 0; i < c.getContainerSize(); i++) {
                        ItemStack s = c.getItem(i);
                        if (!s.isEmpty()) {
                            List<Container> list = holders.get(new Key(s));
                            if (list == null) {
                                list = new ArrayList<>(2);
                                holders.put(new Key(s.copyWithCount(1)), list);
                            }
                            if (list.isEmpty() || list.get(list.size() - 1) != c) {
                                list.add(c);
                            }
                        }
                    }
                }
            }
            return holders;
        }

        /** Does any linked container already hold this item? */
        public boolean holds(ItemStack like) {
            return !like.isEmpty() && holders().containsKey(new Key(like));
        }

        public ItemStack insert(ItemStack stack) {
            if (stack.isEmpty()) {
                return ItemStack.EMPTY;
            }
            Key key = new Key(stack.copyWithCount(1));
            ItemStack rest = stack;
            List<Container> same = holders().get(key);
            Set<Container> done = Collections.newSetFromMap(new IdentityHashMap<>());
            if (same != null) {
                for (Container c : List.copyOf(same)) {
                    done.add(c);
                    rest = into(c, rest);
                    if (rest.isEmpty()) {
                        return ItemStack.EMPTY;
                    }
                }
            }
            for (int pass = 0; pass < 3; pass++) {
                for (Container c : containers) {
                    boolean sorting = c instanceof SortingChestBlockEntity;
                    boolean emptyCrate = c instanceof CrateBlockEntity crate && crate.kind().isEmpty();
                    boolean match = switch (pass) {
                        case 0 -> sorting;
                        case 1 -> !sorting && !emptyCrate;
                        default -> emptyCrate;
                    };
                    if (!match || done.contains(c)) {
                        continue;
                    }
                    int before = rest.getCount();
                    rest = into(c, rest);
                    if (rest.getCount() != before && done.add(c)) {
                        holders().computeIfAbsent(key, k -> new ArrayList<>(2)).add(c);
                    }
                    if (rest.isEmpty()) {
                        return ItemStack.EMPTY;
                    }
                }
            }
            return rest;
        }

        private static ItemStack into(Container c, ItemStack stack) {
            // no shulker boxes (or other container items) inside shulker boxes
            if (c instanceof ShulkerBoxBlockEntity && !stack.getItem().canFitInsideContainerItems()) {
                return stack;
            }
            return InventoryUtil.insert(c, stack, false);
        }
    }
}

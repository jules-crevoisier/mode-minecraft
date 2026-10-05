package com.brasshaven.chisel;

import com.mojang.serialization.Codec;
import com.brasshaven.Brasshaven;
import com.brasshaven.network.ChiselSyncMsg;
import com.brasshaven.network.BrasshavenNet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.Identifier;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimpleJsonResourceReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraftforge.event.AddReloadListenerEvent;
import net.minecraftforge.event.OnDatapackSyncEvent;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Chisel families: loops of blocks the Engraver's Chisel and the Chisel Table turn into each other.
 *
 * <p>Data-driven: every {@code data/<namespace>/chisel/<family>.json} file holds {@code {"blocks": [ids...]}}
 * (generated from tools/wf/chisel.py; datapacks can add more). Loaded on the server with the other data
 * (so {@code /reload} picks up changes) and sent to each client, which uses it to predict chisel clicks
 * and to show variants in the Chisel Table.
 */
public final class ChiselFamilies {
    /** One family: its id and member blocks, in cycling order. */
    public record Family(String id, List<Block> blocks) {
        public int indexOf(Block block) {
            return blocks.indexOf(block);
        }

        /** The member {@code step} places after {@code state}'s block (wrapping), keeping the shared properties. */
        public BlockState step(BlockState state, int step) {
            int i = indexOf(state.getBlock());
            int n = blocks.size();
            return convert(state, blocks.get(Math.floorMod(i + step, n)));
        }
    }

    /** A family as written in the data files, unknown ids already dropped. */
    public record Data(String id, List<String> blocks) {}

    private static final Codec<List<String>> FILE_CODEC = Codec.STRING.listOf().fieldOf("blocks").codec();

    private static Map<Block, Family> server = Map.of();
    private static Map<Block, Family> client = Map.of();
    private static List<Data> serverData = List.of();

    private ChiselFamilies() {}

    public static void register() {
        AddReloadListenerEvent.BUS.addListener(event -> event.addListener(new Loader()));
        OnDatapackSyncEvent.BUS.addListener(event -> {
            ChiselSyncMsg msg = new ChiselSyncMsg(serverData);
            event.getPlayers().forEach(p -> BrasshavenNet.toPlayer(p, msg));
        });
    }

    /** The family {@code block} belongs to on this side, or null. */
    @Nullable
    public static Family family(Level level, Block block) {
        return (level.isClientSide() ? client : server).get(block);
    }

    /** The family of the block an item places, or null. */
    @Nullable
    public static Family family(Level level, ItemStack stack) {
        return stack.getItem() instanceof BlockItem item ? family(level, item.getBlock()) : null;
    }

    /** {@code to}'s default state with every property it shares with {@code from} copied over (stairs keep facing...). */
    public static BlockState convert(BlockState from, Block to) {
        return to.withPropertiesOf(from);
    }

    /** Client side: replaces the families with the server's (ChiselSyncMsg). */
    public static void setClient(List<Data> data) {
        client = build(data);
    }

    private static Map<Block, Family> build(List<Data> data) {
        Map<Block, Family> out = new IdentityHashMap<>();
        for (Data d : data) {
            List<Block> blocks = new ArrayList<>();
            for (String id : d.blocks()) {
                resolve(id).filter(b -> !blocks.contains(b)).ifPresent(blocks::add);
            }
            if (blocks.size() < 2) {
                continue;
            }
            Family family = new Family(d.id(), List.copyOf(blocks));
            for (Block b : blocks) {
                Family previous = out.putIfAbsent(b, family);
                if (previous != null) {
                    Brasshaven.LOGGER.warn("Chisel: {} is in families {} and {}; keeping {}",
                            BuiltInRegistries.BLOCK.getKey(b), previous.id(), d.id(), previous.id());
                }
            }
        }
        return out;
    }

    private static Optional<Block> resolve(String id) {
        Identifier rl = Identifier.tryParse(id);
        return rl == null ? Optional.empty() : BuiltInRegistries.BLOCK.getOptional(rl).filter(b -> b != Blocks.AIR);
    }

    /** Reads data/<ns>/chisel/*.json with the server's data packs. */
    static final class Loader extends SimpleJsonResourceReloadListener<List<String>> {
        Loader() {
            super(FILE_CODEC, FileToIdConverter.json("chisel"));
        }

        @Override
        protected void apply(Map<Identifier, List<String>> files, ResourceManager manager, ProfilerFiller profiler) {
            List<Data> data = new ArrayList<>();
            files.entrySet().stream().sorted(Comparator.comparing(e -> e.getKey().toString())).forEach(e -> {
                List<String> known = e.getValue().stream().filter(id -> resolve(id).isPresent()).toList();
                if (known.size() < e.getValue().size()) {
                    Brasshaven.LOGGER.debug("Chisel family {}: {} unknown block(s) skipped", e.getKey(),
                            e.getValue().size() - known.size());
                }
                if (known.size() >= 2) {
                    data.add(new Data(e.getKey().toString(), known));
                }
            });
            serverData = List.copyOf(data);
            server = build(serverData);
            Brasshaven.LOGGER.info("Loaded {} chisel families ({} blocks)", data.size(), server.size());
        }
    }
}

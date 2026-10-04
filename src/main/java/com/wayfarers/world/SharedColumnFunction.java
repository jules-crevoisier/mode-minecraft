package com.wayfarers.world;

import com.mojang.serialization.MapCodec;
import net.minecraft.util.KeyDispatchDataCodec;
import net.minecraft.world.level.levelgen.DensityFunction;

/**
 * {@code "type": "wayfarers:shared_2d"}: a named 2D stage of the overhaul terrain (tools/wf/terrain.py wraps every
 * {@code flat_cache} function in it) that is computed once per column and walked once per tree, however many
 * functions read it.
 *
 * <p>Why: the terrain is built in stages (base height, terraces, mires, fjords, islands) and a stage reads the one
 * before it several times ({@code lerp} reads its input twice, {@code min(x, f(x))} twice...). Vanilla only caches a
 * named function inside a chunk's {@code NoiseChunk} ({@code flat_cache}, {@code cache_2d}); two other paths see the
 * stages as a tree in which every read is a full copy of the stage below:
 * <ul>
 *   <li>the climate sampler of {@code RandomState} (biome lookups: /locate biome, structure biome checks, the spawn
 *   search, carver biomes) strips every cache marker, so one {@code depth} sample evaluated the base height ~36
 *   times (68 000 nodes);</li>
 *   <li>{@code DensityFunction.mapAll} (each {@code NoiseChunk}, including the one-column chunks of
 *   {@code getBaseHeight}) rebuilds the router by walking it as a tree: ~680 000 nodes per chunk or column.</li>
 * </ul>
 * This node fixes both without changing a single value: {@link #mapChildren} remembers what it returned to the walk
 * in progress on this thread (the same visitor walks the same node again: same answer), and {@link #compute}
 * remembers the last column it computed on this thread (the argument must not depend on y, like any
 * {@code flat_cache} function). Both caches are per thread because the sampler is shared by all worldgen threads.
 */
public final class SharedColumnFunction implements DensityFunction {
    public static final MapCodec<SharedColumnFunction> MAP_CODEC = DensityFunction.CODEC.fieldOf("argument")
            .xmap(SharedColumnFunction::new, SharedColumnFunction::argument);
    public static final KeyDispatchDataCodec<SharedColumnFunction> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

    private final DensityFunction argument;
    private final ThreadLocal<State> state = ThreadLocal.withInitial(State::new);
    private int hash;

    /** What this thread last asked of this node. */
    private static final class State {
        boolean has;
        int x;
        int z;
        double value;
        Visitor visitor;
        DensityFunction mapped;
    }

    public SharedColumnFunction(DensityFunction argument) {
        this.argument = argument;
    }

    public DensityFunction argument() {
        return this.argument;
    }

    @Override
    public double compute(FunctionContext context) {
        State s = this.state.get();
        int x = context.blockX();
        int z = context.blockZ();
        if (s.has && s.x == x && s.z == z) {
            return s.value;
        }
        double v = this.argument.compute(context);
        s.x = x;
        s.z = z;
        s.value = v;
        s.has = true;
        return v;
    }

    @Override
    public void fillArray(double[] output, ContextProvider contextProvider) {
        this.argument.fillArray(output, contextProvider);
    }

    @Override
    public DensityFunction mapChildren(Visitor visitor) {
        State s = this.state.get();
        if (s.visitor == visitor && s.mapped != null) {
            return s.mapped;
        }
        DensityFunction mapped = new SharedColumnFunction(visitor.apply(this.argument));
        // holds the last walk's visitor and result (one per thread): a new walk has a new visitor, so a stale
        // answer is never handed out, and the reference keeps that visitor's identity from being reused
        s.visitor = visitor;
        s.mapped = mapped;
        return mapped;
    }

    @Override
    public double minValue() {
        return this.argument.minValue();
    }

    @Override
    public double maxValue() {
        return this.argument.maxValue();
    }

    @Override
    public KeyDispatchDataCodec<? extends DensityFunction> codec() {
        return CODEC;
    }

    /*
     * Equal by argument, like the vanilla records, so the walks that wire the noises and build each NoiseChunk
     * (they deduplicate by equality) share one instance, and one flat cache, between the router's fields. The hash
     * is kept: hashing the argument reaches the stages below, which keep theirs.
     */
    @Override
    public boolean equals(Object o) {
        return this == o || o instanceof SharedColumnFunction other && other.hashCode() == this.hashCode()
                && this.argument.equals(other.argument);
    }

    @Override
    public int hashCode() {
        int h = this.hash;
        if (h == 0) {
            h = this.argument.hashCode() * 31 + 0x5A2D;
            this.hash = h == 0 ? 1 : h;
        }
        return this.hash;
    }

    @Override
    public String toString() {
        // not the argument: printed whole, the stages below would be a tree again
        return "SharedColumn@" + Integer.toHexString(this.hashCode());
    }
}

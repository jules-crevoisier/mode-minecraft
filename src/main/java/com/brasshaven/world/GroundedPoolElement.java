package com.brasshaven.world;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.brasshaven.registry.ModWorldgen;
import net.minecraft.core.Holder;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.structure.pools.SinglePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElementType;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorList;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.util.Optional;

/**
 * A {@code single_pool_element} that says how deep its ground layer is ({@code "element_type":
 * "brasshaven:grounded_single"}, written by tools/wf/village.py).
 *
 * <p>Vanilla elements always report a ground level delta of 1 (their lowest layer is the ground), so a start piece
 * with a foundation under its ground layer would be lifted by the foundation's depth and the beard would flatten
 * the terrain at the foundation's bottom. Our village plaza sits in the vanilla {@code town_centers} pools and needs
 * its street jigsaws, which {@link ChunkedPoolElement} does not expose; this keeps every behaviour of the vanilla
 * element (jigsaws, placement, processors) and only changes {@link #getGroundLevelDelta()}.
 */
public class GroundedPoolElement extends SinglePoolElement {
    public static final MapCodec<GroundedPoolElement> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            GroundedPoolElement.<GroundedPoolElement>templateCodec(),
            GroundedPoolElement.<GroundedPoolElement>processorsCodec(),
            projectionCodec(),
            GroundedPoolElement.<GroundedPoolElement>overrideLiquidSettingsCodec(),
            Codec.intRange(0, 4096).optionalFieldOf("ground_level_delta", 1).forGetter(e -> e.groundLevelDelta)
    ).apply(i, GroundedPoolElement::new));

    private final int groundLevelDelta;

    protected GroundedPoolElement(Either<Identifier, StructureTemplate> template, Holder<StructureProcessorList> processors,
                                  StructureTemplatePool.Projection projection,
                                  Optional<LiquidSettings> overrideLiquidSettings, int groundLevelDelta) {
        super(template, processors, projection, overrideLiquidSettings);
        this.groundLevelDelta = groundLevelDelta;
    }

    @Override
    public int getGroundLevelDelta() {
        return this.groundLevelDelta;
    }

    @Override
    public StructurePoolElementType<?> getType() {
        return ModWorldgen.GROUNDED_SINGLE.get();
    }

    @Override
    public String toString() {
        return "Grounded[" + this.template + ", ground " + this.groundLevelDelta + "]";
    }
}

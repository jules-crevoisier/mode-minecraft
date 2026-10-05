package com.brasshaven.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.brasshaven.item.BuilderWandItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraftforge.client.event.RenderHighlightEvent;

import java.util.function.Consumer;

/**
 * While holding a Builder's Wand, outlines every block it would place on the face you look at: gold for the
 * copies of the face, aether blue for their mirrored copies. With symmetry on, the mirror centre block is
 * framed in amber and each mirror plane is drawn as a thin frame through it. Sneaking shows where a sneak-click
 * would put the centre.
 */
public final class WandPreview {
    private static final int GOLD = 0xFFF6C343;
    private static final int MIRRORED = 0xFF3FD0FF;
    private static final int CENTRE = 0xFFFFB347;
    private static final int PLANE = 0x993FD0FF;
    /** Half size of the drawn mirror planes, in blocks. */
    private static final int PLANE_HALF = 5;

    // the plan flood-fills the face and checks entities per block: compute it once per tick, not once per frame
    private static BuilderWandItem.Plan cachedPlan = BuilderWandItem.Plan.EMPTY;
    private static Object cacheKey;

    private WandPreview() {}

    public static void register() {
        RenderHighlightEvent.Block.BUS.addListener((Consumer<RenderHighlightEvent.Block>) WandPreview::onHighlight);
    }

    private static void onHighlight(RenderHighlightEvent.Block event) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) {
            return;
        }
        ItemStack held = mc.player.getMainHandItem();
        if (!(held.getItem() instanceof BuilderWandItem wand)) {
            return;
        }
        BlockPos pos = event.getTarget().getBlockPos();
        BlockPos centre = BuilderWandItem.mirrorCentre(mc.level, held);
        BuilderWandItem.Symmetry symmetry = BuilderWandItem.symmetry(held);
        boolean settingCentre = mc.player.isShiftKeyDown();
        BuilderWandItem.Plan plan = BuilderWandItem.Plan.EMPTY;
        if (!settingCentre) {
            Object key = java.util.List.of(pos, event.getTarget().getDirection(), mc.level.getGameTime());
            if (!key.equals(cacheKey)) {
                cacheKey = key;
                cachedPlan = BuilderWandItem.plan(mc.level, mc.player, held, pos, event.getTarget().getDirection(), wand.maxBlocks());
            }
            plan = cachedPlan;
        }
        BuilderWandItem.Plan shown = plan;
        event.setCustomRenderer((collector, poseStack, state) -> {
            Vec3 cam = state.cameraRenderState.pos;
            if (settingCentre) {
                outline(collector, poseStack, pos, Shapes.block(), cam, CENTRE);
            } else {
                outline(collector, poseStack, pos, Shapes.block(), cam, 0x66000000);
            }
            for (BuilderWandItem.Placement p : shown.primary()) {
                outline(collector, poseStack, p.pos(), Shapes.block(), cam, GOLD);
            }
            for (BuilderWandItem.Placement p : shown.mirrored()) {
                outline(collector, poseStack, p.pos(), Shapes.block(), cam, MIRRORED);
            }
            if (centre != null) {
                outline(collector, poseStack, centre, Shapes.box(-0.02, -0.02, -0.02, 1.02, 1.02, 1.02), cam, CENTRE);
                double lo = -PLANE_HALF, hi = PLANE_HALF + 1;
                if (symmetry == BuilderWandItem.Symmetry.X || symmetry == BuilderWandItem.Symmetry.XZ) {
                    outline(collector, poseStack, centre, Shapes.box(0.49, lo + 2, lo, 0.51, hi - 2, hi), cam, PLANE);
                }
                if (symmetry == BuilderWandItem.Symmetry.Z || symmetry == BuilderWandItem.Symmetry.XZ) {
                    outline(collector, poseStack, centre, Shapes.box(lo, lo + 2, 0.49, hi, hi - 2, 0.51), cam, PLANE);
                }
            }
        });
    }

    private static void outline(SubmitNodeCollector collector, PoseStack ps, BlockPos p, VoxelShape shape, Vec3 cam, int color) {
        ps.pushPose();
        ps.translate(p.getX() - cam.x, p.getY() - cam.y, p.getZ() - cam.z);
        collector.submitShapeOutline(ps, shape, RenderTypes.lines(), color, 2.0F, false);
        ps.popPose();
    }
}

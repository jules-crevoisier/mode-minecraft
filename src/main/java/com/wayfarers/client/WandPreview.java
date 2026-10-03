package com.wayfarers.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.wayfarers.item.BuilderWandItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraftforge.client.event.RenderHighlightEvent;

import java.util.List;
import java.util.function.Consumer;

/** While holding a Builder's Wand, outlines every block it would place on the face you look at. */
public final class WandPreview {
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
        List<BlockPos> targets = BuilderWandItem.targets(mc.level, mc.player, pos, event.getTarget().getDirection(), wand.maxBlocks());
        event.setCustomRenderer((collector, poseStack, state) -> {
            Vec3 cam = state.cameraRenderState.pos;
            outline(collector, poseStack, pos, cam, 0x66000000);
            for (BlockPos t : targets) {
                outline(collector, poseStack, t, cam, 0xFFF6C343);
            }
        });
    }

    private static void outline(net.minecraft.client.renderer.SubmitNodeCollector collector, PoseStack ps, BlockPos p,
                                Vec3 cam, int color) {
        ps.pushPose();
        ps.translate(p.getX() - cam.x, p.getY() - cam.y, p.getZ() - cam.z);
        collector.submitShapeOutline(ps, Shapes.block(), RenderTypes.lines(), color, 2.0F, false);
        ps.popPose();
    }
}

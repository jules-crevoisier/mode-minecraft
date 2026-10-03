package com.wayfarers.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.wayfarers.block.CrateBlockEntity;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.item.ItemModelResolver;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/** Draws the stored item and its count on the front of a Compacting Crate (like a Storage Drawer). */
public class CrateRenderer implements BlockEntityRenderer<CrateBlockEntity, CrateRenderer.State> {
    public static class State extends BlockEntityRenderState {
        public Direction facing = Direction.NORTH;
        public final ItemStackRenderState item = new ItemStackRenderState();
        public FormattedCharSequence count = FormattedCharSequence.EMPTY;
        public float countWidth;
    }

    private final ItemModelResolver itemModelResolver;
    private final Font font;

    public CrateRenderer(BlockEntityRendererProvider.Context context) {
        this.itemModelResolver = context.itemModelResolver();
        this.font = context.font();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(CrateBlockEntity crate, State state, float partialTicks, Vec3 cameraPosition,
                                   ModelFeatureRenderer.@Nullable CrumblingOverlay breakProgress) {
        BlockEntityRenderer.super.extractRenderState(crate, state, partialTicks, cameraPosition, breakProgress);
        state.facing = crate.getBlockState().getValue(HorizontalDirectionalBlock.FACING);
        itemModelResolver.updateForTopItem(state.item, crate.kind(), ItemDisplayContext.FIXED, crate.getLevel(), null,
                (int) crate.getBlockPos().asLong());
        int total = crate.total();
        String text = total >= 10000 ? (total / 1000) + "k" : String.valueOf(total);
        state.count = total > 0 ? Component.literal(text).getVisualOrderText() : FormattedCharSequence.EMPTY;
        state.countWidth = font.width(state.count);
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (state.item.isEmpty()) {
            return;
        }
        poseStack.pushPose();
        poseStack.translate(0.5F, 0.5F, 0.5F);
        poseStack.mulPose(Axis.YP.rotationDegrees(-state.facing.toYRot()));
        poseStack.translate(0.0F, 0.06F, 0.505F);
        poseStack.pushPose();
        poseStack.scale(0.5F, 0.5F, 0.02F);
        state.item.submit(poseStack, collector, state.lightCoords, OverlayTexture.NO_OVERLAY, 0);
        poseStack.popPose();
        poseStack.translate(0.0F, -0.33F, 0.01F);
        poseStack.scale(0.012F, -0.012F, 0.012F);
        collector.submitText(poseStack, -state.countWidth / 2, 0, state.count, false, Font.DisplayMode.NORMAL,
                state.lightCoords, 0xFFF2E6C8, 0, 0);
        poseStack.popPose();
    }
}

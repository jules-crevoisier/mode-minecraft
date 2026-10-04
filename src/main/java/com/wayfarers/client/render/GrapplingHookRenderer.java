package com.wayfarers.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.wayfarers.entity.GrapplingHookEntity;
import com.wayfarers.item.GrapplingHookItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.item.ItemModelResolver;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.phys.Vec3;

/**
 * The grappling claw (the hook item's "claw" model, turned along its flight like an arrow) and the chain back to
 * the owner's hand, drawn like a fishing line but taut, in alternating iron and brass links.
 */
public class GrapplingHookRenderer extends EntityRenderer<GrapplingHookEntity, GrapplingHookRenderer.State> {
    private static final int LINKS = 24;
    private static final int IRON = 0xFF3C3A3A;
    private static final int BRASS = 0xFFB08D57;
    private final ItemModelResolver itemModelResolver;

    public static class State extends EntityRenderState {
        public final ItemStackRenderState item = new ItemStackRenderState();
        public Vec3 lineOriginOffset = Vec3.ZERO;
        public boolean hasOwner;
        public float xRot;
        public float yRot;
    }

    public GrapplingHookRenderer(EntityRendererProvider.Context context) {
        super(context);
        this.itemModelResolver = context.getItemModelResolver();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    protected boolean affectedByCulling(GrapplingHookEntity entity) {
        // the chain must show even when the claw itself is off screen
        return false;
    }

    @Override
    public void extractRenderState(GrapplingHookEntity entity, State state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        itemModelResolver.updateForNonLiving(state.item, entity.getItem(), ItemDisplayContext.NONE, entity);
        state.xRot = entity.getXRot(partialTicks);
        state.yRot = entity.getYRot(partialTicks);
        Player owner = entity.playerOwner();
        state.hasOwner = owner != null;
        if (owner == null) {
            state.lineOriginOffset = Vec3.ZERO;
        } else {
            float swing = Mth.sin(Mth.sqrt(owner.getAttackAnim(partialTicks)) * (float) Math.PI);
            state.lineOriginOffset = handPos(owner, swing, partialTicks).subtract(entity.getPosition(partialTicks));
        }
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.mulPose(Axis.YP.rotationDegrees(state.yRot - 90.0F));
        poseStack.mulPose(Axis.ZP.rotationDegrees(state.xRot));
        state.item.submit(poseStack, collector, state.lightCoords, OverlayTexture.NO_OVERLAY, state.outlineColor);
        poseStack.popPose();
        if (state.hasOwner) {
            float dx = (float) state.lineOriginOffset.x;
            float dy = (float) state.lineOriginOffset.y;
            float dz = (float) state.lineOriginOffset.z;
            float width = Minecraft.getInstance().gameRenderer.gameRenderState().windowRenderState.appropriateLineWidth * 1.6F;
            collector.submitCustomGeometry(poseStack, RenderTypes.lines(), (pose, buffer) -> {
                for (int i = 0; i < LINKS; i++) {
                    int color = i % 2 == 0 ? IRON : BRASS;
                    link(buffer, pose, dx, dy, dz, (float) i / LINKS, (float) (i + 1) / LINKS, color, width);
                }
            });
        }
        super.submit(state, poseStack, collector, camera);
    }

    private static void link(VertexConsumer buffer, PoseStack.Pose pose, float dx, float dy, float dz, float a0, float a1,
                             int color, float width) {
        float nx = dx * (a1 - a0);
        float ny = dy * (a1 - a0);
        float nz = dz * (a1 - a0);
        float length = Mth.sqrt(nx * nx + ny * ny + nz * nz);
        if (length < 1.0E-5F) {
            return;
        }
        nx /= length;
        ny /= length;
        nz /= length;
        buffer.addVertex(pose, dx * a0, dy * a0, dz * a0).setColor(color).setNormal(pose, nx, ny, nz).setLineWidth(width);
        buffer.addVertex(pose, dx * a1, dy * a1, dz * a1).setColor(color).setNormal(pose, nx, ny, nz).setLineWidth(width);
    }

    /** Where the chain leaves the gun: same maths as the fishing line (first person follows the camera). */
    private Vec3 handPos(Player owner, float swing, float partialTicks) {
        HumanoidArm arm = owner.getMainHandItem().getItem() instanceof GrapplingHookItem ? owner.getMainArm()
                : owner.getMainArm().getOpposite();
        int invert = arm == HumanoidArm.RIGHT ? 1 : -1;
        if (entityRenderDispatcher.options.getCameraType().isFirstPerson() && owner == Minecraft.getInstance().player) {
            float fov = entityRenderDispatcher.options.fov().get().intValue();
            double viewBobbingScale = 960.0 / fov;
            Vec3 viewVec = entityRenderDispatcher.camera.getNearPlane(fov).getPointOnPlane(invert * 0.525F, -0.1F)
                    .scale(viewBobbingScale).yRot(swing * 0.5F).xRot(-swing * 0.7F);
            return owner.getEyePosition(partialTicks).add(viewVec);
        }
        float bodyYaw = Mth.lerp(partialTicks, owner.yBodyRotO, owner.yBodyRot) * Mth.DEG_TO_RAD;
        double sin = Mth.sin(bodyYaw);
        double cos = Mth.cos(bodyYaw);
        float scale = owner.getScale();
        double right = invert * 0.35 * scale;
        double forward = 0.8 * scale;
        float crouch = owner.isCrouching() ? -0.1875F : 0.0F;
        return owner.getEyePosition(partialTicks)
                .add(-cos * right - sin * forward, crouch - 0.45 * scale, -sin * right + cos * forward);
    }
}

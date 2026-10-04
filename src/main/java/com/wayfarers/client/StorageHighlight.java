package com.wayfarers.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.wayfarers.network.TerminalLinksMsg;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.ChestType;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraftforge.client.event.RenderHighlightEvent;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.function.Consumer;

/**
 * "Show in world" from the Guild Terminal's Network page: for a few seconds every linked container is outlined in
 * gold (excluded ones in red) and sparkles, so the player sees what the terminal reaches.
 */
public final class StorageHighlight {
    private static final int DURATION = 200;
    private static final int MAX_SHOWN = 512;
    private static final int GOLD = 0xFFF6C343;
    private static final int RED = 0xFFE0483B;
    private static final VoxelShape BOX = Shapes.box(-0.03, -0.03, -0.03, 1.03, 1.03, 1.03);

    private record Mark(BlockPos pos, boolean excluded) {}

    private static List<Mark> marks = List.of();
    private static int ticksLeft;
    private static ResourceKey<Level> dimension;

    private StorageHighlight() {}

    public static void register() {
        RenderHighlightEvent.Block.BUS.addListener((Consumer<RenderHighlightEvent.Block>) StorageHighlight::onHighlight);
        TickEvent.ClientTickEvent.Post.BUS.addListener(event -> tick());
    }

    public static void show(TerminalLinksMsg links) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return;
        }
        List<Mark> list = new ArrayList<>();
        for (TerminalLinksMsg.Info info : links.links()) {
            list.add(new Mark(info.pos(), info.excluded()));
            if (info.doubled()) {
                BlockState state = mc.level.getBlockState(info.pos());
                if (state.getBlock() instanceof ChestBlock && state.getValue(ChestBlock.TYPE) != ChestType.SINGLE) {
                    list.add(new Mark(info.pos().relative(ChestBlock.getConnectedDirection(state)), info.excluded()));
                }
            }
        }
        Vec3 eye = mc.player.position();
        list.sort(Comparator.comparingDouble(m -> m.pos.distToCenterSqr(eye)));
        marks = list.size() > MAX_SHOWN ? List.copyOf(list.subList(0, MAX_SHOWN)) : List.copyOf(list);
        ticksLeft = DURATION;
        dimension = mc.level.dimension();
        long count = links.links().stream().filter(i -> !i.excluded()).count();
        mc.player.sendOverlayMessage(Component.translatable("message.wayfarers.terminal.showing", count, DURATION / 20));
    }

    private static boolean active() {
        Minecraft mc = Minecraft.getInstance();
        return ticksLeft > 0 && mc.level != null && mc.level.dimension() == dimension;
    }

    private static void tick() {
        if (ticksLeft <= 0) {
            return;
        }
        ticksLeft--;
        Minecraft mc = Minecraft.getInstance();
        if (!active() || ticksLeft % 8 != 0) {
            return;
        }
        for (Mark m : marks) {
            DustParticleOptions dust = new DustParticleOptions(m.excluded ? RED & 0xFFFFFF : GOLD & 0xFFFFFF, 1.4F);
            for (int i = 0; i < 2; i++) {
                double x = m.pos.getX() + mc.level.getRandom().nextDouble();
                double z = m.pos.getZ() + mc.level.getRandom().nextDouble();
                mc.level.addAlwaysVisibleParticle(dust, true, x, m.pos.getY() + 1.1, z, 0.0, 0.02, 0.0);
            }
        }
    }

    private static void onHighlight(RenderHighlightEvent.Block event) {
        if (!active()) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        BlockPos target = event.getTarget().getBlockPos();
        RenderHighlightEvent.Callback previous = event.getCustomRenderer();
        VoxelShape targetShape = mc.level.getBlockState(target).getShape(mc.level, target);
        List<Mark> shown = marks;
        event.setCustomRenderer((collector, poseStack, state) -> {
            Vec3 cam = state.cameraRenderState.pos;
            if (previous != null) {
                previous.render(collector, poseStack, state);
            } else if (!targetShape.isEmpty()) {
                outline(collector, poseStack, target, targetShape, cam, 0x66000000);
            }
            for (Mark m : shown) {
                outline(collector, poseStack, m.pos, BOX, cam, m.excluded ? RED : GOLD);
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

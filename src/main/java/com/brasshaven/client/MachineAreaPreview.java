package com.brasshaven.client;

import com.brasshaven.block.MachineBlock;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.gizmos.GizmoStyle;
import net.minecraft.gizmos.Gizmos;
import net.minecraft.world.phys.AABB;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * "Show area" of the machine screens: outlines a machine's work area in the world, like a structure block's box,
 * until switched off in its screen, the machine is gone or the player wanders more than 96 blocks away.
 * Client only; drawn as per-tick gizmos from the client tick.
 */
public final class MachineAreaPreview {
    private record Shown(AABB box, int color) {}

    private static final Map<BlockPos, Shown> SHOWN = new HashMap<>();
    /**
     * The client level the shown areas belong to: changing dimension (or server) makes a new one, and the outlines
     * of the old world must not be drawn at the same coordinates in the new one.
     */
    private static Object shownIn;

    private MachineAreaPreview() {}

    public static boolean isShown(BlockPos pos) {
        return SHOWN.containsKey(pos);
    }

    public static void toggle(BlockPos pos, MachineBlock.Kind kind, AABB box) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level != shownIn) {
            SHOWN.clear();
            shownIn = mc.level;
        }
        if (SHOWN.remove(pos) == null) {
            SHOWN.put(pos.immutable(), new Shown(box, color(kind)));
        }
    }

    /** Follows the area while its screen changes the radius. */
    public static void update(BlockPos pos, AABB box) {
        Shown s = SHOWN.get(pos);
        if (s != null && !s.box().equals(box)) {
            SHOWN.put(pos, new Shown(box, s.color()));
        }
    }

    private static int color(MachineBlock.Kind kind) {
        return switch (kind) {
            case HARVESTER -> 0xFFF6C343;
            case SPRINKLER -> 0xFF3FD0FF;
            case VACUUM -> 0xFFB98BE8;
            default -> 0xFFFF6A4A;
        };
    }

    public static void tick() {
        if (SHOWN.isEmpty()) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null || mc.level != shownIn) {
            SHOWN.clear();
            shownIn = null;
            return;
        }
        Iterator<Map.Entry<BlockPos, Shown>> it = SHOWN.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<BlockPos, Shown> e = it.next();
            BlockPos pos = e.getKey();
            if (!pos.closerToCenterThan(mc.player.position(), 96)
                    || (mc.level.isLoaded(pos) && !(mc.level.getBlockState(pos).getBlock() instanceof MachineBlock))) {
                it.remove();
                continue;
            }
            int color = e.getValue().color();
            try {
                Gizmos.cuboid(e.getValue().box().inflate(0.01), GizmoStyle.strokeAndFill(color, 3.0F, (color & 0xFFFFFF) | 0x1C000000));
                Gizmos.cuboid(new AABB(pos).inflate(0.03), GizmoStyle.stroke(color, 2.0F));
            } catch (IllegalStateException ignored) {
                // no gizmo collector outside the client tick: nothing to draw this time
            }
        }
    }
}

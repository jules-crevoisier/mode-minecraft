package com.brasshaven.entity;

import com.brasshaven.generated.MobAnims;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Mob;

/**
 * A creature with a generated keyframe model (tools/wf/mobs). Actions (attacks, roars, staggers) are
 * started on the server with {@link #playAction}, which broadcasts entity event 100 + index; the client
 * starts the matching {@link AnimationState} and the generated model plays it.
 */
public interface AnimatedMob {
    int ACTION_EVENT_BASE = 100;

    /** One state per action, in the order of the generated MobAnims constants. */
    AnimationState[] actionStates();

    /** Action lengths in ticks (MobAnims.X.TICKS), used to stop finished actions on the client. */
    int[] actionTicks();

    /** Colour variant drawn by the renderer (textures of the model's variants, in order). */
    default int modelVariant() {
        return 0;
    }

    /** Box the renderer uses to skip creatures out of view; long ones inflate it to cover their whole body. */
    default net.minecraft.world.phys.AABB cullingBox(net.minecraft.world.phys.AABB hitbox) {
        return hitbox;
    }

    static AnimationState[] createStates() {
        AnimationState[] states = new AnimationState[MobAnims.MAX_ACTIONS];
        for (int i = 0; i < states.length; i++) {
            states[i] = new AnimationState();
        }
        return states;
    }

    /** Server side: play an action animation for every client tracking the mob. */
    static void playAction(Mob mob, int action) {
        if (!mob.level().isClientSide() && action >= 0 && action < MobAnims.MAX_ACTIONS) {
            mob.level().broadcastEntityEvent(mob, (byte) (ACTION_EVENT_BASE + action));
        }
    }

    /** Client side, from handleEntityEvent: returns true when the event was an action. */
    default boolean handleActionEvent(Mob mob, byte id) {
        int action = id - ACTION_EVENT_BASE;
        if (action < 0 || action >= MobAnims.MAX_ACTIONS) {
            return false;
        }
        AnimationState[] states = actionStates();
        for (AnimationState state : states) {
            state.stop();
        }
        states[action].start(mob.tickCount);
        return true;
    }

    /** Client side, every tick: stop actions whose animation has finished. */
    default void tickActionStates(Mob mob) {
        AnimationState[] states = actionStates();
        int[] ticks = actionTicks();
        for (int i = 0; i < ticks.length && i < states.length; i++) {
            if (states[i].isStarted() && states[i].getTimeInMillis(mob.tickCount) > ticks[i] * 50L + 100L) {
                states[i].stop();
            }
        }
    }
}

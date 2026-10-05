package com.brasshaven.entity.mob;

import com.brasshaven.entity.AnimatedMob;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Shared plumbing of the creatures of the places (tools/wf/denizens.py): one action at a time, played on every client
 * with {@link AnimatedMob#playAction}, and a server-side tick counter the attack goals read to land their blows on the
 * frame the animation shows them.
 */
public abstract class ActionMonster extends Monster implements AnimatedMob {
    private final AnimationState[] actionStates = AnimatedMob.createStates();
    /** The action playing on the server (-1: none) and the ticks since it started. */
    protected int action = -1;
    protected int actionTick;

    protected ActionMonster(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    protected void begin(int anim) {
        action = anim;
        actionTick = 0;
        AnimatedMob.playAction(this, anim);
    }

    /** One tick of the current action: the tick index, or -1 once it is over (the action is then cleared). */
    protected int step() {
        if (action < 0) {
            return -1;
        }
        int k = actionTick++;
        if (k >= actionTicks()[action]) {
            action = -1;
            return -1;
        }
        return k;
    }

    /** Horizontal unit vector from this creature to ``e``. */
    protected Vec3 toward(LivingEntity e) {
        Vec3 d = e.position().subtract(position()).multiply(1, 0, 1);
        return d.lengthSqr() < 1.0E-4 ? Vec3.ZERO : d.normalize();
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
        }
    }
}

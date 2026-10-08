package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Mite de rouille (Rust Mite): the brood of the {@link RustMiteMother} (model tools/wf/mobs/rust_mite.py). Tiny, fast,
 * 4 health: it rears and spreads its mandibles before biting (lands at 5 ticks), and crumbles to rust after a minute
 * (60 s) unless it was placed in the world for good.
 */
public class RustMite extends ActionMonster {
    public static final float WIDTH = 0.4F;
    public static final float HEIGHT = 0.3F;
    private static final int BITE_HIT = 5;      // 0.25 s, matches rust_mite.py
    private static final int LIFE = 1200;

    private int biteCooldown;

    public RustMite(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 1;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.FOLLOW_RANGE, 16.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MiteGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RustMite.TICKS;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (tickCount > LIFE && !isPersistenceRequired()) {
            level.sendParticles(new DustParticleOptions(0xA4502A, 1.0F), getX(), getY() + 0.15, getZ(), 8, 0.15, 0.1, 0.15, 0.0);
            level.playSound(null, this, SoundEvents.SILVERFISH_DEATH, SoundSource.HOSTILE, 0.5F, 1.6F);
            discard();
        }
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.SILVERFISH_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SILVERFISH_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SILVERFISH_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SILVERFISH_STEP, 0.15F, 1.4F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.4F;
    }

    /** Rush and bite. */
    static final class MiteGoal extends Goal {
        private final RustMite m;
        private int repath;

        MiteGoal(RustMite m) {
            this.m = m;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = m.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return m.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            if (!(m.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = m.getTarget();
            if (m.action >= 0) {
                int k = m.step();
                m.getNavigation().stop();
                if (k == BITE_HIT && t != null && t.isAlive() && m.distanceToSqr(t) <= 1.4 * 1.4) {
                    m.doHurtTarget(level, t);
                }
                return;
            }
            if (t == null) {
                return;
            }
            m.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (m.distanceToSqr(t) <= 1.1 * 1.1 && m.biteCooldown == 0) {
                m.biteCooldown = 20;
                m.begin(MobAnims.RustMite.BITE);
                return;
            }
            if (--repath <= 0) {
                repath = 6;
                m.getNavigation().moveTo(t, 1.2);
            }
        }
    }
}

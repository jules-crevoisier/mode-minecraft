package com.wayfarers.entity.mob;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Void Larva (Larve du vide): a segmented End grub of the Void Crypt.
 * <ul>
 *     <li><b>Bite</b> (under 1.9 blocks): rears for 10 ticks, lunges and snaps its mandibles (attack damage 4).</li>
 *     <li><b>Burrow</b> (4 to 14 blocks, every 6-8 s, or 35% when hurt): dives into the ground (12 ticks, then hidden
 *     and invulnerable), reappears 2 to 3.5 blocks from its target in a ring of reverse-portal motes and bursts out
 *     at tick 20 (3 damage and a toss if the target stands on it).</li>
 *     <li><b>Split</b>: dies into 2 or 3 endermites.</li>
 * </ul>
 */
public class VoidLarva extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 0.7F;
    private static final int BITE_WINDUP = 10;
    private static final int HIDE_AT = 12;
    private static final int EMERGE_AT = 20;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int biteCooldown;
    private int burrowCooldown = 60;
    private boolean hidden;
    private boolean burrowWhenHurt;

    public VoidLarva(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 5;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 16.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.28)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new GnawGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.ENDERMITE_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.ENDERMITE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ENDERMITE_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SILVERFISH_STEP, 0.15F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.6F;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (hidden) {
            return false; // underground
        }
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && isAlive() && random.nextFloat() < 0.35F) {
            burrowWhenHurt = true;
        }
        return hurt;
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            int n = 2 + random.nextInt(2);
            for (int i = 0; i < n; i++) {
                Mob mite = EntityTypes.ENDERMITE.create(level, EntitySpawnReason.MOB_SUMMONED);
                if (mite == null) {
                    continue;
                }
                double a = Math.PI * 2 * i / n + random.nextDouble();
                mite.snapTo(getX() + Math.cos(a) * 0.3, getY() + 0.1, getZ() + Math.sin(a) * 0.3, random.nextFloat() * 360F, 0);
                mite.setDeltaMovement(Math.cos(a) * 0.25, 0.3, Math.sin(a) * 0.25);
                if (getTarget() != null) {
                    mite.setTarget(getTarget());
                }
                level.addFreshEntity(mite);
            }
            level.sendParticles(ParticleTypes.PORTAL, getX(), getY() + 0.4, getZ(), 30, 0.4, 0.3, 0.4, 0.4);
            level.playSound(null, this, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.0F, 0.6F);
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (burrowCooldown > 0) {
            burrowCooldown--;
        }
        if (tickCount % 10 == 0 && !hidden) {
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 0.5, getZ(), 1, 0.3, 0.2, 0.3, 0.0);
        }
    }

    private void setHidden(boolean h) {
        hidden = h;
        setInvisible(h);
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.VoidLarva.TICKS;
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

    // ------------------------------------------------------------------ brain

    private Vec3 facing() {
        float r = getYRot() * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    /** Crawl in, bite, burrow under the target's feet. */
    static final class GnawGoal extends Goal {
        private final VoidLarva l;
        private int action = -1;
        private int tick;
        private float yaw;

        GnawGoal(VoidLarva l) {
            this.l = l;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = l.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            action = -1;
            l.setHidden(false);
            l.getNavigation().stop();
        }

        private void begin(int which, LivingEntity t) {
            action = which;
            tick = 0;
            float y = (float) (Mth.atan2(t.getZ() - l.getZ(), t.getX() - l.getX()) * Mth.RAD_TO_DEG) - 90.0F;
            yaw = y;
            lock();
            l.getNavigation().stop();
            AnimatedMob.playAction(l, which);
        }

        private void lock() {
            l.setYRot(yaw);
            l.yBodyRot = yaw;
            l.yHeadRot = yaw;
        }

        @Override
        public void tick() {
            if (!(l.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = l.getTarget();
            if (action == MobAnims.VoidLarva.BITE) {
                tickBite(level, t);
                return;
            }
            if (action == MobAnims.VoidLarva.BURROW) {
                tickBurrow(level, t);
                return;
            }
            if (t == null) {
                return;
            }
            l.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(l.distanceToSqr(t));
            boolean canBurrow = l.burrowCooldown == 0 && l.onGround() && (dist >= 4.0 && dist <= 14.0 || l.burrowWhenHurt);
            if (canBurrow) {
                l.burrowWhenHurt = false;
                begin(MobAnims.VoidLarva.BURROW, t);
                level.playSound(null, l, SoundEvents.WARDEN_DIG, SoundSource.HOSTILE, 0.5F, 1.9F);
                return;
            }
            if (dist < 1.9 && l.biteCooldown == 0) {
                begin(MobAnims.VoidLarva.BITE, t);
                return;
            }
            if (l.tickCount % 5 == 0) {
                l.getNavigation().moveTo(t, 1.0);
            }
        }

        private void tickBite(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            l.getNavigation().stop();
            lock();
            if (k == BITE_WINDUP) {
                Vec3 fwd = l.facing();
                l.setDeltaMovement(fwd.scale(0.3));
                if (t != null && l.distanceToSqr(t) < 2.4 * 2.4) {
                    Vec3 to = t.position().subtract(l.position()).multiply(1, 0, 1);
                    if (to.length() < 0.7 || to.normalize().dot(fwd) > 0.4) {
                        l.doHurtTarget(level, t);
                    }
                }
                level.playSound(null, l, SoundEvents.PHANTOM_BITE, SoundSource.HOSTILE, 0.8F, 1.3F);
            }
            if (k >= MobAnims.VoidLarva.TICKS[MobAnims.VoidLarva.BITE]) {
                action = -1;
                l.biteCooldown = 14;
            }
        }

        private void tickBurrow(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            l.getNavigation().stop();
            lock();
            if (k < HIDE_AT && k % 2 == 0) {
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, l.getX(), l.getY() + 0.1, l.getZ(), 6, 0.4, 0.05, 0.4, 0.05);
                level.sendParticles(ParticleTypes.SMOKE, l.getX(), l.getY() + 0.1, l.getZ(), 2, 0.3, 0.05, 0.3, 0.01);
            } else if (k == HIDE_AT) {
                l.setHidden(true);
                if (t != null) {
                    for (int attempt = 0; attempt < 8; attempt++) {
                        double a = l.random.nextDouble() * Math.PI * 2;
                        double r = 2.0 + l.random.nextDouble() * 1.5;
                        if (l.randomTeleport(t.getX() + Math.cos(a) * r, t.getY() + 1, t.getZ() + Math.sin(a) * r, false)) {
                            break;
                        }
                    }
                    yaw = (float) (Mth.atan2(t.getZ() - l.getZ(), t.getX() - l.getX()) * Mth.RAD_TO_DEG) - 90.0F;
                    lock();
                }
                level.playSound(null, l, SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.HOSTILE, 0.6F, 0.7F);
            } else if (k < EMERGE_AT) {
                for (int i = 0; i < 8; i++) {
                    double a = Math.PI * 2 * i / 8 + k * 0.2;
                    level.sendParticles(ParticleTypes.REVERSE_PORTAL, l.getX() + Math.cos(a) * 0.8, l.getY() + 0.1,
                            l.getZ() + Math.sin(a) * 0.8, 1, 0, 0.02, 0, 0.0);
                }
            } else if (k == EMERGE_AT) {
                l.setHidden(false);
                level.sendParticles(ParticleTypes.PORTAL, l.getX(), l.getY() + 0.3, l.getZ(), 30, 0.4, 0.3, 0.4, 0.6);
                level.playSound(null, l, SoundEvents.WARDEN_DIG, SoundSource.HOSTILE, 0.6F, 1.6F);
                if (t != null && l.distanceToSqr(t) < 1.7 * 1.7
                        && t.hurtServer(level, l.damageSources().mobAttack(l), 3.0F)) {
                    t.push(0, 0.45, 0);
                    t.hurtMarked = true;
                }
            }
            if (k >= MobAnims.VoidLarva.TICKS[MobAnims.VoidLarva.BURROW]) {
                action = -1;
                l.setHidden(false);
                l.burrowCooldown = 120 + l.random.nextInt(41);
            }
        }
    }
}

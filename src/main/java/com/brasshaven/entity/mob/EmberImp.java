package com.brasshaven.entity.mob;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.hurtingprojectile.SmallFireball;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Ember Imp (Imp de braise): a small Nether fire imp for the Nether structures. Fire immune (registry).
 * <ul>
 *     <li>Moves in little hops and flutters down slowly (falling speed x0.6 in the air, no fall damage).</li>
 *     <li>Keeps 5 to 10 blocks from its target. <b>Throw</b> (3.5 to 16 blocks, line of sight, every 2.5-3.5 s):
 *     a 10-tick wind-up while the orb swells in its hand, then a vanilla {@link SmallFireball} (5 damage + fire),
 *     35% chance of a second one 4 ticks later.</li>
 *     <li>When hurt (70%), it <b>hops</b> back with a wing beat and flees for 2.5 s, then <b>cackles</b> and comes
 *     back for more. It also cackles sometimes after a throw.</li>
 * </ul>
 */
public class EmberImp extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 0.95F;
    private static final int THROW_WINDUP = 10;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int throwCooldown = 30;
    private int fleeTicks;
    private boolean cackleAfterFlee;

    public EmberImp(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 6;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MischiefGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.BLAZE_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.BLAZE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.BLAZE_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.6F;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    public void aiStep() {
        super.aiStep();
        Vec3 v = getDeltaMovement();
        if (!onGround() && v.y < 0) {
            setDeltaMovement(v.multiply(1.0, 0.6, 1.0)); // flutters down on its wings
        }
        if (level().isClientSide() && random.nextInt(4) == 0) {
            level().addParticle(ParticleTypes.SMALL_FLAME, getRandomX(0.4), getY() + 0.3 + random.nextDouble() * 0.5,
                    getRandomZ(0.4), 0, 0.01, 0);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && isAlive() && fleeTicks == 0 && random.nextFloat() < 0.7F) {
            fleeTicks = 50;
            cackleAfterFlee = true;
            Vec3 away = source.getEntity() != null
                    ? position().subtract(source.getEntity().position()).multiply(1, 0, 1).normalize()
                    : Vec3.ZERO;
            setDeltaMovement(away.x * 0.7, 0.55, away.z * 0.7);
            hurtMarked = true;
            AnimatedMob.playAction(this, MobAnims.EmberImp.HOP);
            level.playSound(null, this, SoundEvents.BAT_TAKEOFF, SoundSource.HOSTILE, 0.7F, 1.5F);
        }
        return hurt;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (throwCooldown > 0) {
            throwCooldown--;
        }
        if (fleeTicks > 0) {
            fleeTicks--;
        }
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.EmberImp.TICKS;
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

    private void shoot(ServerLevel level, LivingEntity t, double spread) {
        Vec3 hand = new Vec3(getX(), getY(0.8), getZ());
        Vec3 dir = new Vec3(t.getX() - hand.x, t.getY(0.5) - hand.y, t.getZ() - hand.z);
        double d = dir.length();
        dir = new Vec3(random.triangle(dir.x, spread * d * 0.1), dir.y, random.triangle(dir.z, spread * d * 0.1)).normalize();
        SmallFireball ball = new SmallFireball(level, this, dir);
        ball.setPos(hand.x + dir.x * 0.5, hand.y, hand.z + dir.z * 0.5);
        level.addFreshEntity(ball);
        level.playSound(null, this, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 0.8F, 1.4F);
    }

    /** Keep a mischievous distance, throw fireballs, flee when hurt and cackle. */
    static final class MischiefGoal extends Goal {
        private final EmberImp imp;
        private int action = -1;
        private int tick;
        private boolean doubleThrow;

        MischiefGoal(EmberImp imp) {
            this.imp = imp;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = imp.getTarget();
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
            imp.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            imp.getNavigation().stop();
            AnimatedMob.playAction(imp, which);
        }

        @Override
        public void tick() {
            if (!(imp.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = imp.getTarget();
            if (action == MobAnims.EmberImp.THROW) {
                int k = tick++;
                imp.getNavigation().stop();
                if (t != null) {
                    imp.getLookControl().setLookAt(t, 40.0F, 40.0F);
                }
                if (k < THROW_WINDUP && k % 2 == 0) {
                    Vec3 p = imp.position().add(0, 1.25, 0);
                    level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 2, 0.15, 0.15, 0.15, 0.01);
                }
                if (t != null && (k == THROW_WINDUP || doubleThrow && k == THROW_WINDUP + 4)) {
                    imp.shoot(level, t, k == THROW_WINDUP ? 0.6 : 1.4);
                }
                if (k >= MobAnims.EmberImp.TICKS[MobAnims.EmberImp.THROW]) {
                    action = -1;
                    imp.throwCooldown = 50 + imp.random.nextInt(21);
                    if (imp.random.nextFloat() < 0.25F) {
                        begin(MobAnims.EmberImp.CACKLE);
                        level.playSound(null, imp, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 0.9F, 1.7F);
                    }
                }
                return;
            }
            if (action == MobAnims.EmberImp.CACKLE) {
                imp.getNavigation().stop();
                if (++tick >= MobAnims.EmberImp.TICKS[MobAnims.EmberImp.CACKLE]) {
                    action = -1;
                }
                return;
            }
            if (t == null) {
                return;
            }
            if (imp.fleeTicks > 0) {
                if (imp.fleeTicks % 10 == 0 || imp.getNavigation().isDone()) {
                    Vec3 away = DefaultRandomPos.getPosAway(imp, 10, 4, t.position());
                    if (away != null) {
                        imp.getNavigation().moveTo(away.x, away.y, away.z, 1.4);
                    }
                }
                hop();
                return;
            }
            if (imp.cackleAfterFlee) {
                imp.cackleAfterFlee = false;
                begin(MobAnims.EmberImp.CACKLE);
                level.playSound(null, imp, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 1.0F, 1.6F);
                return;
            }
            imp.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(imp.distanceToSqr(t));
            if (dist >= 3.5 && dist <= 16.0 && imp.throwCooldown == 0 && imp.hasLineOfSight(t)) {
                doubleThrow = imp.random.nextFloat() < 0.35F;
                begin(MobAnims.EmberImp.THROW);
                level.playSound(null, imp, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.5F, 1.8F);
                return;
            }
            if (imp.tickCount % 10 == 0) {
                if (dist > 10.0 || !imp.hasLineOfSight(t)) {
                    imp.getNavigation().moveTo(t, 1.0);
                } else if (dist < 5.0) {
                    Vec3 away = DefaultRandomPos.getPosAway(imp, 6, 3, t.position());
                    if (away != null) {
                        imp.getNavigation().moveTo(away.x, away.y, away.z, 1.1);
                    }
                } else {
                    imp.getNavigation().stop();
                }
            }
            if (!imp.getNavigation().isDone()) {
                hop();
            }
        }

        /** Little hops while moving. */
        private void hop() {
            if (imp.onGround() && imp.tickCount % 9 == 0) {
                imp.getJumpControl().jump();
            }
        }
    }
}

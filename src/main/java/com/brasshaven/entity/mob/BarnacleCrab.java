package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Crabe à bernacles (Barnacle Crab): the scuttling guardian of the sunken temples, citadels and wrecks.
 * <ul>
 *     <li>Amphibious: it breathes anywhere, walks on the sea floor instead of swimming (currents do not push it) and
 *     <b>climbs walls</b>, under water too, to drop on its prey.</li>
 *     <li><b>Snap</b> (within 2 blocks): a jab of the small claw (lands at 6 ticks).</li>
 *     <li><b>Clamp</b> (within 2.6 blocks, every 8 s): the great claw rears up and gapes for 12 ticks, then slams
 *     shut. Caught, its prey is held in place (heavy Slowness) and squeezed (2 damage a second) for up to 3 s; any hit
 *     on the crab makes it let go.</li>
 *     <li><b>Hide</b>: hurt below half health, it pulls into its shell for 3 s (once every 20 s): projectiles bounce off,
 *     other blows do 20% damage, and it mends a little.</li>
 * </ul>
 */
public class BarnacleCrab extends ActionMonster {
    public static final float WIDTH = 1.2F;
    public static final float HEIGHT = 0.85F;
    private static final EntityDataAccessor<Boolean> DATA_CLIMBING = SynchedEntityData.defineId(BarnacleCrab.class, EntityDataSerializers.BOOLEAN);
    private static final int SNAP_HIT = 6;     // 0.3 s, matches barnacle_crab.py
    private static final int CLAMP_SHUT = 12;  // 0.6 s

    private int snapCooldown;
    private int clampCooldown = 60;
    private int hideCooldown;
    private int hidden;
    private int holding;
    private @Nullable LivingEntity held;

    public BarnacleCrab(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 8;
        setPathfindingMalus(PathType.WATER, 0.0F);
        setPathfindingMalus(PathType.WATER_BORDER, 0.0F);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    /** In water (structure spawns under the sea); any light level, not in peaceful. */
    public static boolean checkSpawnRules(EntityType<BarnacleCrab> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                          BlockPos pos, RandomSource random) {
        return level.getDifficulty() != Difficulty.PEACEFUL && level.getFluidState(pos).is(FluidTags.WATER);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(2, new CrabGoal(this));
        goalSelector.addGoal(5, new RandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    // ------------------------------------------------------------------ amphibious wall-climber

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CLIMBING, false);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WallClimberNavigation(this, level);
    }

    @Override
    public boolean onClimbable() {
        return entityData.get(DATA_CLIMBING);
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!level().isClientSide()) {
            entityData.set(DATA_CLIMBING, horizontalCollision && hidden == 0);
            // under water, a wall in front: climb it (the water physics ignore ladders and climbers)
            if (isInWater() && horizontalCollision && hidden == 0 && getTarget() != null && getTarget().getY() > getY() + 0.5) {
                setDeltaMovement(getDeltaMovement().x, 0.18, getDeltaMovement().z);
            } else if (isInWater() && !onGround() && getDeltaMovement().y > -0.15) {
                setDeltaMovement(getDeltaMovement().add(0, -0.03, 0)); // heavy shell: it sinks to the floor
            }
        } else if (isInWater() && random.nextInt(20) == 0) {
            level().addParticle(ParticleTypes.BUBBLE, getRandomX(0.5), getY() + 0.8, getRandomZ(0.5), 0, 0.05, 0);
        }
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BarnacleCrab.TICKS;
    }

    // ------------------------------------------------------------------ the shell

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (hidden > 0) {
            if (source.is(DamageTypeTags.IS_PROJECTILE)) {
                level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 0.8F, 1.4F);
                return false;
            }
            if (!source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
                damage *= 0.2F;
            }
        }
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && held != null) {
            letGo();
        }
        if (hurt && isAlive() && hidden == 0 && hideCooldown == 0 && getHealth() < getMaxHealth() * 0.5F) {
            hidden = 60;
            hideCooldown = 400;
            action = -1;
            begin(MobAnims.BarnacleCrab.HIDE);
            getNavigation().stop();
            level.playSound(null, this, SoundEvents.SHULKER_CLOSE, SoundSource.HOSTILE, 1.0F, 0.8F);
        }
        return hurt;
    }

    private void letGo() {
        if (held != null) {
            held.removeEffect(MobEffects.SLOWNESS);
        }
        held = null;
        holding = 0;
    }

    @Override
    public void die(DamageSource source) {
        letGo();
        super.die(source);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (snapCooldown > 0) {
            snapCooldown--;
        }
        if (clampCooldown > 0) {
            clampCooldown--;
        }
        if (hideCooldown > 0) {
            hideCooldown--;
        }
        if (hidden > 0) {
            hidden--;
            getNavigation().stop();
            setDeltaMovement(getDeltaMovement().multiply(0, 1, 0));
            if (hidden % 20 == 0) {
                heal(1.0F);
            }
            if (hidden == 0) {
                level.playSound(null, this, SoundEvents.SHULKER_OPEN, SoundSource.HOSTILE, 1.0F, 0.8F);
            }
        }
        if (held != null) {
            LivingEntity h = held;
            if (!h.isAlive() || --holding <= 0 || distanceToSqr(h) > 4.0 * 4.0 || hidden > 0) {
                letGo();
            } else {
                h.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 15, 5), this);
                h.setDeltaMovement(h.getDeltaMovement().multiply(0.2, 1.0, 0.2));
                if (holding % 10 == 0) {
                    begin(MobAnims.BarnacleCrab.HOLD);
                }
                if (holding % 20 == 0) {
                    h.hurtServer(level, damageSources().mobAttack(this), 2.0F);
                    level.playSound(null, this, SoundEvents.TURTLE_HURT, SoundSource.HOSTILE, 0.6F, 0.6F);
                }
            }
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.TURTLE_AMBIENT_LAND;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.TURTLE_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.TURTLE_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
        playSound(SoundEvents.SPIDER_STEP, 0.15F, 1.4F);
    }

    /** Scuttle up, snap, clamp; nothing while hidden in the shell. */
    static final class CrabGoal extends Goal {
        private final BarnacleCrab c;
        private int repath;

        CrabGoal(BarnacleCrab c) {
            this.c = c;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = c.getTarget();
            return t != null && t.isAlive() || c.hidden > 0;
        }

        @Override
        public boolean canContinueToUse() {
            return c.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            c.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(c.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = c.getTarget();
            if (c.hidden > 0) {
                c.step();
                return;
            }
            if (c.action >= 0) {
                int a = c.action;
                int k = c.step();
                c.getNavigation().stop();
                if (t == null || !t.isAlive()) {
                    return;
                }
                c.getLookControl().setLookAt(t, 30.0F, 30.0F);
                if (a == MobAnims.BarnacleCrab.SNAP && k == SNAP_HIT && c.distanceToSqr(t) <= 2.6 * 2.6) {
                    c.doHurtTarget(level, t);
                } else if (a == MobAnims.BarnacleCrab.CLAMP) {
                    if (k < CLAMP_SHUT && k % 3 == 0) {
                        level.sendParticles(c.isInWater() ? ParticleTypes.BUBBLE : ParticleTypes.SPLASH,
                                c.getX(), c.getY() + 0.6, c.getZ(), 4, 0.4, 0.2, 0.4, 0.05);
                    }
                    if (k == CLAMP_SHUT) {
                        level.playSound(null, c, SoundEvents.SHULKER_CLOSE, SoundSource.HOSTILE, 1.0F, 1.6F);
                        if (c.distanceToSqr(t) <= 2.9 * 2.9 && c.doHurtTarget(level, t)
                                && !(t instanceof Player p && (p.isCreative() || p.isSpectator()))) {
                            c.held = t;
                            c.holding = 60;
                        }
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(c.distanceToSqr(t));
            if (dist <= 2.6 && c.clampCooldown == 0 && c.held == null) {
                c.clampCooldown = 160;
                c.begin(MobAnims.BarnacleCrab.CLAMP);
                level.playSound(null, c, SoundEvents.SHULKER_OPEN, SoundSource.HOSTILE, 1.0F, 1.4F);
                return;
            }
            if (dist <= 2.0 && c.snapCooldown == 0) {
                c.snapCooldown = 20;
                c.begin(MobAnims.BarnacleCrab.SNAP);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                c.getNavigation().moveTo(t, 1.2);
            }
        }
    }
}

package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
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
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Tireur bandit (Bandit Marksman): the sharpshooter of the bandit camps and the ruined watchtowers.
 * <ul>
 *     <li>Keeps 7 to 14 blocks from its prey, strafing, and <b>draws</b> its recurve bow (15 ticks: the bow rises, the
 *     string comes to the cheek) before loosing a well-aimed arrow, every 2-3 s.</li>
 *     <li>When its prey closes within 3.5 blocks it throws a <b>smoke bomb</b> at its own feet (released at 7 ticks):
 *     a cloud of smoke, Blindness 3 s and Slowness 2 s within 3.5 blocks, and it leaps back out of the cloud. 10 s
 *     cooldown: corner it while the smoke recharges.</li>
 *     <li>Without a bomb, up close it can only <b>kick</b> (lands at 5 ticks, a strong push).</li>
 * </ul>
 */
public class BanditMarksman extends ActionMonster {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.95F;
    private static final int DRAW_LOOSE = 15;   // 0.75 s, matches bandit_marksman.py
    private static final int THROW_RELEASE = 7; // 0.35 s
    private static final int KICK_IMPACT = 5;   // 0.25 s

    private int shotCooldown = 30;
    private int smokeCooldown;
    private int kickCooldown;

    public BanditMarksman(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 8;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MarksmanGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BanditMarksman.TICKS;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (shotCooldown > 0) {
            shotCooldown--;
        }
        if (smokeCooldown > 0) {
            smokeCooldown--;
        }
        if (kickCooldown > 0) {
            kickCooldown--;
        }
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.PILLAGER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PILLAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PILLAGER_DEATH;
    }

    // ------------------------------------------------------------------ moves

    private void loose(ServerLevel level, LivingEntity t) {
        Arrow arrow = new Arrow(level, this, new ItemStack(Items.ARROW), null);
        Vec3 from = getEyePosition().add(toward(t).scale(0.4));
        arrow.setPos(from.x, from.y - 0.1, from.z);
        arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
        arrow.setBaseDamage(2.0 + 0.5 * level.getDifficulty().getId());
        double dx = t.getX() - from.x;
        double dy = t.getY(0.33) - from.y;
        double dz = t.getZ() - from.z;
        double flat = Math.sqrt(dx * dx + dz * dz);
        arrow.shoot(dx, dy + flat * 0.17, dz, 1.8F, 10 - level.getDifficulty().getId() * 3);
        level.addFreshEntity(arrow);
        level.playSound(null, this, SoundEvents.SKELETON_SHOOT, SoundSource.HOSTILE, 1.0F, 0.9F + random.nextFloat() * 0.2F);
    }

    private void smoke(ServerLevel level, @Nullable LivingEntity t) {
        Vec3 c = position();
        level.sendParticles(ParticleTypes.LARGE_SMOKE, c.x, c.y + 0.6, c.z, 40, 1.4, 0.7, 1.4, 0.02);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, c.x, c.y + 0.4, c.z, 12, 1.0, 0.3, 1.0, 0.01);
        level.sendParticles(ParticleTypes.POOF, c.x, c.y + 0.3, c.z, 16, 0.6, 0.2, 0.6, 0.08);
        level.playSound(null, this, SoundEvents.SPLASH_POTION_BREAK, SoundSource.HOSTILE, 1.0F, 0.7F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 1.0F, 0.5F);
        for (Player p : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(3.5), Player::isAlive)) {
            if (!p.isCreative() && !p.isSpectator()) {
                p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), this);
                p.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0), this);
            }
        }
        // leap back out of the cloud
        Vec3 away = t != null ? toward(t).scale(-1.0) : Vec3.ZERO;
        setDeltaMovement(away.x * 0.9, 0.45, away.z * 0.9);
        hurtMarked = true;
    }

    /** Keep a sniper's distance, shoot, smoke out whoever gets close, kick when cornered. */
    static final class MarksmanGoal extends Goal {
        private final BanditMarksman b;
        private int repath;
        private boolean strafeLeft;

        MarksmanGoal(BanditMarksman b) {
            this.b = b;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = b.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return b.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            b.getNavigation().stop();
            b.action = -1;
        }

        @Override
        public void tick() {
            if (!(b.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = b.getTarget();
            if (b.action >= 0) {
                int a = b.action;
                int k = b.step();
                if (t != null) {
                    b.getLookControl().setLookAt(t, 40.0F, 40.0F);
                }
                if (a != MobAnims.BanditMarksman.DODGE) {
                    b.getNavigation().stop();
                }
                if (a == MobAnims.BanditMarksman.DRAW && k == DRAW_LOOSE && t != null && t.isAlive()) {
                    b.loose(level, t);
                } else if (a == MobAnims.BanditMarksman.THROW && k == THROW_RELEASE) {
                    b.smoke(level, t);
                    b.begin(MobAnims.BanditMarksman.DODGE);
                } else if (a == MobAnims.BanditMarksman.KICK && k == KICK_IMPACT && t != null && t.isAlive()
                        && b.distanceToSqr(t) <= 2.6 * 2.6) {
                    if (b.doHurtTarget(level, t)) {
                        Vec3 push = b.toward(t).scale(1.1);
                        t.push(push.x, 0.3, push.z);
                        t.hurtMarked = true;
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            b.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(b.distanceToSqr(t));
            boolean sees = b.getSensing().hasLineOfSight(t);
            if (dist < 3.5) {
                if (b.smokeCooldown == 0) {
                    b.smokeCooldown = 200;
                    b.begin(MobAnims.BanditMarksman.THROW);
                    level.playSound(null, b, SoundEvents.SNOWBALL_THROW, SoundSource.HOSTILE, 0.8F, 0.6F);
                    return;
                }
                if (b.kickCooldown == 0 && dist < 2.4) {
                    b.kickCooldown = 24;
                    b.begin(MobAnims.BanditMarksman.KICK);
                    return;
                }
            }
            if (dist >= 3.5 && dist <= 16.0 && sees && b.shotCooldown == 0) {
                b.shotCooldown = 40 + b.random.nextInt(16);
                b.begin(MobAnims.BanditMarksman.DRAW);
                level.playSound(null, b, SoundEvents.CROSSBOW_LOADING_MIDDLE.value(), SoundSource.HOSTILE, 0.6F, 0.8F);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                if (dist > 14.0 || !sees) {
                    b.getNavigation().moveTo(t, 1.0);
                } else if (dist < 7.0) {
                    Vec3 away = DefaultRandomPos.getPosAway(b, 8, 3, t.position());
                    if (away != null) {
                        b.getNavigation().moveTo(away.x, away.y, away.z, 1.15);
                    }
                } else {
                    // strafe around the prey, changing side now and then
                    if (b.random.nextInt(4) == 0) {
                        strafeLeft = !strafeLeft;
                    }
                    Vec3 side = b.toward(t).yRot(strafeLeft ? 1.57F : -1.57F).scale(3.0);
                    b.getNavigation().moveTo(b.getX() + side.x, b.getY(), b.getZ() + side.z, 0.8);
                }
            }
        }
    }
}

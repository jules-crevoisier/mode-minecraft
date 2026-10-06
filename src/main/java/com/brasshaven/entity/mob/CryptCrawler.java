package com.brasshaven.entity.mob;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
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
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.EnumSet;

/**
 * Rampant des cryptes (Crypt Crawler): a low, wide spider of fused bones with a skull head and mandibles.
 * <ul>
 *     <li>Climbs walls like a spider (wall-climber navigation + climbing flag, same logic as vanilla {@code Spider}),
 *     ignores cobwebs and takes no fall damage.</li>
 *     <li><b>Bite</b> (within 1.9 blocks): rears up for 0.3 s, snaps: attack damage + Slowness I for 3 s.</li>
 *     <li><b>Pounce</b> (3 to 7 blocks, on the ground, every 4 s): crouches for 0.4 s, then leaps at the target;
 *     the first contact in flight deals 1.5x damage.</li>
 * </ul>
 * Kept on {@link Monster} rather than {@code Spider} so the skeleton-jockey spawn and the spider's daylight
 * neutrality do not apply; the climbing logic is reimplemented here.
 */
public class CryptCrawler extends Monster implements AnimatedMob {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 0.9F;
    private static final EntityDataAccessor<Boolean> DATA_CLIMBING = SynchedEntityData.defineId(CryptCrawler.class, EntityDataSerializers.BOOLEAN);

    private static final int BITE_IMPACT = 6;     // 0.3 s, matches crypt_crawler.py
    private static final int POUNCE_LAUNCH = 8;   // 0.4 s

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int action = -1;
    private int actionTimer;
    private boolean actionHit;
    private int biteCooldown;
    private int pounceCooldown = 40;

    public CryptCrawler(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ARMOR, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 32.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new CrawlerAttackGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    // ------------------------------------------------------------------ climbing (as vanilla Spider)

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CLIMBING, false);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WallClimberNavigation(this, level);
    }

    public boolean isClimbing() {
        return entityData.get(DATA_CLIMBING);
    }

    @Override
    public boolean onClimbable() {
        return isClimbing();
    }

    @Override
    public void makeStuckInBlock(BlockState state, Vec3 speedMultiplier) {
        if (!state.is(Blocks.COBWEB)) {
            super.makeStuckInBlock(state, speedMultiplier);
        }
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.CryptCrawler.TICKS;
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
        } else {
            entityData.set(DATA_CLIMBING, horizontalCollision);
        }
    }

    // ------------------------------------------------------------------ sounds: a spider's chitter, a skeleton's rattle

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SPIDER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SKELETON_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SKELETON_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SPIDER_STEP, 0.15F, 0.7F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.75F;
    }

    // ------------------------------------------------------------------ attacks

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (pounceCooldown > 0) {
            pounceCooldown--;
        }
    }

    private void startAction(int anim) {
        action = anim;
        actionTimer = 0;
        actionHit = false;
        AnimatedMob.playAction(this, anim);
    }

    private void tickAction(ServerLevel level, LivingEntity target) {
        int t = actionTimer++;
        if (action == MobAnims.CryptCrawler.BITE) {
            if (t == BITE_IMPACT && target.isAlive() && distanceToSqr(target) <= 2.3 * 2.3) {
                level.playSound(null, this, SoundEvents.SPIDER_HURT, SoundSource.HOSTILE, 0.6F, 1.6F);
                if (doHurtTarget(level, target)) {
                    target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 0), this);
                }
            }
        } else if (action == MobAnims.CryptCrawler.POUNCE) {
            if (t < POUNCE_LAUNCH) {
                getNavigation().stop();
                if (t % 2 == 0) {
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, getBlockStateOn()), getX(), getY() + 0.1, getZ(),
                            3, 0.4, 0.05, 0.4, 0.05);
                }
            } else if (t == POUNCE_LAUNCH) {
                Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
                double d = Math.max(0.1, to.length());
                Vec3 v = to.scale(Math.min(1.25, 0.2 + d * 0.16) / d);
                setDeltaMovement(v.x, 0.45, v.z);
                hurtMarked = true;
                level.playSound(null, this, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.6F);
            } else if (!actionHit && target.isAlive() && distanceToSqr(target) <= 1.8 * 1.8) {
                actionHit = true;
                float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.5F;
                if (target.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                    Vec3 push = getDeltaMovement().multiply(1, 0, 1).normalize().scale(0.6);
                    target.push(push.x, 0.2, push.z);
                    target.hurtMarked = true;
                }
                setDeltaMovement(getDeltaMovement().multiply(0.2, 1, 0.2));
            }
        }
        if (actionTimer >= actionTicks()[action]) {
            action = -1;
        }
    }

    /** Chase (climbing if needed), bite in reach, pounce from mid range. */
    static final class CrawlerAttackGoal extends Goal {
        private final CryptCrawler crawler;
        private int repath;

        CrawlerAttackGoal(CryptCrawler crawler) {
            this.crawler = crawler;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = crawler.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse() || crawler.action >= 0;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            crawler.getNavigation().stop();
        }

        @Override
        public void tick() {
            LivingEntity target = crawler.getTarget();
            if (target == null || !(crawler.level() instanceof ServerLevel level)) {
                return;
            }
            crawler.getLookControl().setLookAt(target, 30.0F, 30.0F);
            if (crawler.action >= 0) {
                if (crawler.action == MobAnims.CryptCrawler.BITE) {
                    crawler.getNavigation().stop();
                }
                crawler.tickAction(level, target);
                return;
            }
            double dist = Math.sqrt(crawler.distanceToSqr(target));
            if (dist <= 1.9 && crawler.biteCooldown == 0) {
                crawler.biteCooldown = 22;
                crawler.getNavigation().stop();
                crawler.startAction(MobAnims.CryptCrawler.BITE);
                return;
            }
            if (dist >= 3.0 && dist <= 7.0 && crawler.onGround() && crawler.pounceCooldown == 0
                    && Math.abs(target.getY() - crawler.getY()) < 2.5 && crawler.getSensing().hasLineOfSight(target)) {
                crawler.pounceCooldown = 80 + crawler.getRandom().nextInt(30);
                crawler.getNavigation().stop();
                float yaw = (float) (Mth.atan2(target.getZ() - crawler.getZ(), target.getX() - crawler.getX()) * Mth.RAD_TO_DEG) - 90.0F;
                crawler.setYRot(yaw);
                crawler.yBodyRot = yaw;
                crawler.startAction(MobAnims.CryptCrawler.POUNCE);
                return;
            }
            if (--repath <= 0) {
                repath = 6;
                crawler.getNavigation().moveTo(target, 1.15);
            }
        }
    }
}

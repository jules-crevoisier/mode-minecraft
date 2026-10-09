package com.brasshaven.entity.mob;

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
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Scarabée solaire (Sun Scarab): the sacred beetle of the Sun-Engine Ziggurat (model tools/wf/mobs/sun_scarab.py).
 * <ul>
 *     <li><b>Burrow</b> (standing on sand or sandstone, prey 5 to 16 blocks away, every 10 s): digs in nose first and
 *     is gone. Under the sand it cannot be hurt; a furrow of churning sand runs toward its prey.</li>
 *     <li><b>Eruption</b> (burrowed, once under its prey or after 6 s): it stops and the sand boils and rumbles over it
 *     for 12 ticks (the telegraph: step off the boiling patch), then it bursts out: everything within 1.6 blocks is hurt
 *     and thrown into the air.</li>
 *     <li><b>Sun bite</b> (within 2 blocks, every 1 s): the head rears back, mandibles spread, snaps at 9 ticks; in
 *     daylight under open sky its sun disc flares during the wind-up and the bite sets you on fire.</li>
 * </ul>
 */
public class SunScarab extends ActionMonster {
    public static final float WIDTH = 1.0F;
    public static final float HEIGHT = 0.9F;
    private static final EntityDataAccessor<Boolean> DATA_BURROWED = SynchedEntityData.defineId(SunScarab.class, EntityDataSerializers.BOOLEAN);
    private static final int BITE_HIT = 9;       // 0.45 s, matches sun_scarab.py
    private static final int BURROW_DONE = 19;   // 1.0 s (the last tick of the dig)
    private static final int ERUPT_AT = 12;      // 0.6 s
    private static final int TUNNEL_MAX = 120;

    private int biteCooldown;
    private int burrowCooldown = 80;
    private int tunnelTicks;

    public SunScarab(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.4)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new ScarabGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SunScarab.TICKS;
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_BURROWED, false);
    }

    public boolean isBurrowed() {
        return entityData.get(DATA_BURROWED);
    }

    private void setBurrowed(boolean b) {
        entityData.set(DATA_BURROWED, b);
        setInvisible(b);
        tunnelTicks = 0;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Burrowed", isBurrowed());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        setBurrowed(input.getBooleanOr("Burrowed", false));
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** Sand and sandstone: what it can dig through. */
    static boolean diggable(BlockState s) {
        return s.is(Blocks.SAND) || s.is(Blocks.RED_SAND) || s.is(Blocks.SUSPICIOUS_SAND) || s.is(Blocks.SANDSTONE)
                || s.is(Blocks.SMOOTH_SANDSTONE) || s.is(Blocks.CUT_SANDSTONE) || s.is(Blocks.CHISELED_SANDSTONE)
                || s.is(Blocks.RED_SANDSTONE) || s.is(Blocks.SMOOTH_RED_SANDSTONE) || s.is(Blocks.CUT_RED_SANDSTONE);
    }

    private boolean inDaylight() {
        return level().isBrightOutside() && level().canSeeSky(BlockPos.containing(getX(), getY() + 1.0, getZ()));
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (isBurrowed() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;                                                    // under the sand
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    public boolean isPushable() {
        return !isBurrowed() && super.isPushable();
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
        if (isBurrowed() && action < 0) {
            tunnelTicks++;
            BlockState under = getBlockStateOn();
            if (tickCount % 2 == 0) {
                // the furrow of churning sand running along the floor
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, diggable(under) ? under : Blocks.SAND.defaultBlockState()),
                        getX(), getY() + 0.1, getZ(), 4, 0.3, 0.05, 0.3, 0.05);
            }
            if (tickCount % 8 == 0) {
                level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 0.6F, 0.7F);
            }
        }
        if (inDaylight() && tickCount % 20 == 0 && !isBurrowed()) {
            Vec3 p = position().add(forward().scale(0.2)).add(0, 1.2, 0);
            level.sendParticles(ParticleTypes.WAX_ON, p.x, p.y, p.z, 1, 0.2, 0.2, 0.2, 0.0);   // the sun disc glints
        }
    }

    // ------------------------------------------------------------------ sounds: clicking chitin

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return isBurrowed() ? null : SoundEvents.SILVERFISH_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SPIDER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SPIDER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        if (!isBurrowed()) {
            playSound(SoundEvents.SPIDER_STEP, 0.3F, 0.7F);
        }
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    /** Bite up close; from afar, dive into the sand and erupt under the prey. */
    static final class ScarabGoal extends Goal {
        private final SunScarab s;
        private int repath;

        ScarabGoal(SunScarab s) {
            this.s = s;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (s.isBurrowed()) {
                return true;
            }
            LivingEntity t = s.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return s.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            s.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(s.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = s.getTarget();
            if (s.action >= 0) {
                int a = s.action;
                int k = s.step();
                s.getNavigation().stop();
                if (a == MobAnims.SunScarab.BITE) {
                    boolean sun = s.inDaylight();
                    if (sun && k > 0 && k < BITE_HIT && k % 2 == 0) {
                        Vec3 p = s.position().add(s.forward().scale(0.2)).add(0, 1.3, 0);
                        level.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 2, 0.2, 0.2, 0.05, 0.0);
                    }
                    if (t != null && k < BITE_HIT) {
                        s.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    }
                    if (k == BITE_HIT) {
                        level.playSound(null, s, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.HOSTILE, 0.8F, 1.4F);
                        if (t != null && t.isAlive() && s.distanceToSqr(t) <= 2.6 * 2.6 && inFront(t, 0.3) && s.doHurtTarget(level, t) && sun) {
                            t.igniteForSeconds(4.0F);
                            level.sendParticles(ParticleTypes.FLAME, t.getX(), t.getY() + 1.0, t.getZ(), 8, 0.3, 0.4, 0.3, 0.02);
                        }
                    }
                } else if (a == MobAnims.SunScarab.BURROW) {
                    if (k >= 0 && k % 2 == 0) {
                        BlockState under = s.getBlockStateOn();
                        Vec3 p = s.position().add(s.forward().scale(0.6));
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), p.x, p.y + 0.2, p.z, 6, 0.3, 0.2, 0.3, 0.15);
                    }
                    if (k == BURROW_DONE) {
                        s.setBurrowed(true);
                        level.playSound(null, s, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F);
                    }
                } else if (a == MobAnims.SunScarab.ERUPT) {
                    if (k >= 0 && k < ERUPT_AT) {
                        // the telegraph: the sand boils and rumbles over it
                        BlockState under = s.getBlockStateOn();
                        BlockState sand = diggable(under) ? under : Blocks.SAND.defaultBlockState();
                        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, sand), s.getX(), s.getY() + 0.1, s.getZ(),
                                6, 0.7, 0.05, 0.7, 0.08);
                        level.sendParticles(ParticleTypes.DUST_PLUME, s.getX(), s.getY() + 0.1, s.getZ(), 2, 0.6, 0.0, 0.6, 0.02);
                        if (k % 4 == 0) {
                            level.playSound(null, s, SoundEvents.SAND_FALL, SoundSource.HOSTILE, 1.0F, 0.5F);
                        }
                    }
                    if (k == ERUPT_AT) {
                        erupt(level);
                    }
                }
                return;
            }
            if (s.isBurrowed()) {
                tunnel(level, t);
                return;
            }
            if (t == null) {
                return;
            }
            s.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(s.distanceToSqr(t));
            if (dist >= 5.0 && dist <= 16.0 && s.burrowCooldown == 0 && s.onGround() && diggable(s.getBlockStateOn())
                    && s.random.nextInt(4) == 0) {
                s.burrowCooldown = 200;
                s.begin(MobAnims.SunScarab.BURROW);
                level.playSound(null, s, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.0F, 0.8F);
                return;
            }
            if (dist <= 2.0 && s.biteCooldown == 0) {
                s.biteCooldown = 20;
                s.begin(MobAnims.SunScarab.BITE);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                s.getNavigation().moveTo(t, 1.1);
            }
        }

        /** Burrowed: run under the sand toward the prey, erupt once under it (or when the sand runs out). */
        private void tunnel(ServerLevel level, @Nullable LivingEntity t) {
            boolean under = t != null && t.isAlive() && s.distanceToSqr(t.getX(), s.getY(), t.getZ()) <= 1.2 * 1.2;
            boolean sandGone = s.onGround() && !diggable(s.getBlockStateOn()) && s.tunnelTicks > 10;
            if (under || sandGone || s.tunnelTicks > TUNNEL_MAX || t == null || !t.isAlive()) {
                s.getNavigation().stop();
                s.setInvisible(false);                                       // the model plays the eruption from under the floor
                s.begin(MobAnims.SunScarab.ERUPT);
                level.playSound(null, s, SoundEvents.SAND_FALL, SoundSource.HOSTILE, 1.2F, 0.4F);
                return;
            }
            if (--repath <= 0) {
                repath = 5;
                s.getNavigation().moveTo(t.getX(), t.getY(), t.getZ(), 1.5);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(s.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.6 || to.normalize().dot(s.forward()) >= minDot;
        }

        private void erupt(ServerLevel level) {
            s.setBurrowed(false);
            level.playSound(null, s, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.6F, 1.6F);
            level.playSound(null, s, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.4F, 0.5F);
            BlockState under = s.getBlockStateOn();
            BlockState sand = diggable(under) ? under : Blocks.SAND.defaultBlockState();
            level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, sand), s.getX(), s.getY() + 0.4, s.getZ(), 40, 0.8, 0.6, 0.8, 0.3);
            level.sendParticles(ParticleTypes.DUST_PLUME, s.getX(), s.getY() + 0.4, s.getZ(), 10, 0.8, 0.4, 0.8, 0.05);
            float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.4F;
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, s.getBoundingBox().inflate(1.6, 1.0, 1.6),
                    e -> e != s && e.isAlive() && !(e instanceof SunScarab))) {
                if (s.distanceToSqr(e) > 2.0 * 2.0) {
                    continue;
                }
                if (e.hurtServer(level, s.damageSources().mobAttack(s), dmg)) {
                    e.setDeltaMovement(e.getDeltaMovement().x, 0.75, e.getDeltaMovement().z);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 1), s);
                }
            }
        }
    }
}

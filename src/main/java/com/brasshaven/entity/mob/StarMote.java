package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Poussière d'astre (Star Mote): a spark of starlight called down by the {@link StarMoteCaller} (model
 * tools/wf/mobs/star_mote.py). Tiny, quick and frail; it fades away after a minute.
 * <ul>
 *     <li><b>Dart</b> (within 5 blocks, every 1.5 s): pulls back and spins up while its point flares (8 ticks), then
 *     darts straight at where its prey was: hurts what it touches on the way.</li>
 * </ul>
 */
public class StarMote extends ActionMonster {
    public static final float WIDTH = 0.4F;
    public static final float HEIGHT = 0.4F;
    private static final int DART_AT = 8;        // 0.4 s, matches star_mote.py
    private static final int DART_END = 14;
    private static final int LIFE = 1200;

    private int dartCooldown = 20;
    private int age;
    private boolean struck;
    private Vec3 dartDir = Vec3.ZERO;

    public StarMote(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 1;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.45)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    public void travel(Vec3 input) {
        travelFlying(input, getSpeed());
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(2, new MoteGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.8));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StarMote.TICKS;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (dartCooldown > 0) {
            dartCooldown--;
        }
        if (++age > LIFE) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 0.2, getZ(), 8, 0.2, 0.2, 0.2, 0.02);
            level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 0.8F, 1.8F);
            discard();
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(3) == 0) {
            level().addParticle(ParticleTypes.END_ROD, getX(), getY() + 0.2, getZ(), 0, 0, 0);
        }
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.AMETHYST_BLOCK_CHIME;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.AMETHYST_BLOCK_HIT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.AMETHYST_CLUSTER_BREAK;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.6F;
    }

    /** Circle the prey and dart into it. */
    static final class MoteGoal extends Goal {
        private final StarMote m;
        private int repath;

        MoteGoal(StarMote m) {
            this.m = m;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
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
        public void stop() {
            m.getNavigation().stop();
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
                if (k >= 0 && k < DART_AT) {
                    m.setDeltaMovement(m.getDeltaMovement().scale(0.5));
                    if (t != null) {
                        m.getLookControl().setLookAt(t, 30.0F, 30.0F);
                        Vec3 d = t.getEyePosition().add(0, -0.4, 0).subtract(m.position());
                        m.dartDir = d.lengthSqr() < 1.0E-4 ? Vec3.ZERO : d.normalize();
                    }
                    if (k % 2 == 0) {
                        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, m.getX(), m.getY() + 0.2, m.getZ(), 2, 0.1, 0.1, 0.1, 0.0);
                    }
                } else if (k >= DART_AT && k < DART_END) {
                    if (k == DART_AT) {
                        level.playSound(null, m, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 0.8F, 2.0F);
                        m.struck = false;
                    }
                    m.setDeltaMovement(m.dartDir.scale(0.8));
                    level.sendParticles(ParticleTypes.END_ROD, m.getX(), m.getY() + 0.2, m.getZ(), 1, 0.0, 0.0, 0.0, 0.0);
                    if (!m.struck) {
                        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, m.getBoundingBox().inflate(0.5),
                                e -> e != m && e.isAlive() && !(e instanceof StarMote) && !(e instanceof StarMoteCaller))) {
                            if (e.hurtServer(level, m.damageSources().mobAttack(m), (float) m.getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                                m.struck = true;
                                m.setDeltaMovement(m.dartDir.scale(-0.3));
                                break;
                            }
                        }
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            m.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(m.distanceToSqr(t));
            if (dist <= 5.0 && dist >= 1.0 && m.dartCooldown == 0 && m.getSensing().hasLineOfSight(t)) {
                m.dartCooldown = 30 + m.random.nextInt(10);
                m.begin(MobAnims.StarMote.DART);
                return;
            }
            if (--repath <= 0) {
                repath = 6;
                // swirl round the prey at head height
                double a = (m.tickCount * 0.15) + m.getId();
                Vec3 spot = t.position().add(Math.cos(a) * 3.0, t.getBbHeight() * 0.8, Math.sin(a) * 3.0);
                m.getNavigation().moveTo(spot.x, spot.y, spot.z, 1.2);
            }
        }
    }
}

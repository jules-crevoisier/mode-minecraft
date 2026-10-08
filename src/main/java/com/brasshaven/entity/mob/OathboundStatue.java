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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Chevalier-statue du serment (Oathbound Statue-Knight): the stone guardians of the Kneeling Gate (model
 * tools/wf/mobs/oathbound_statue.py, texture variants "dormant" and "awake").
 * <ul>
 *     <li><b>Dormant</b>: it kneels on its sword where it was placed, does not move or turn and takes a quarter of the
 *     damage. A player (not in creative) coming within 6 blocks in its sight, or any blow, <b>wakes</b> it: its
 *     cracks light up gold and it rises (1.6 s) before it fights.</li>
 *     <li><b>Crushing blow</b> (within 3.5 blocks, every 4 s): the greatsword raised over the crown, lands at 22 ticks:
 *     1.4x damage to the prey in front, and a shockwave 2 blocks ahead that throws everything within 3 blocks up.</li>
 *     <li><b>Sweep</b> (within 3.8 blocks, every 5 s): the sword carried out to the side, lands at 17 ticks: hits the
 *     whole half-circle in front.</li>
 *     <li><b>Oath charge</b> (5 to 10 blocks, every 8 s): the point levelled at the hip, the line locked at 14 ticks,
 *     then from 18 to 30 ticks it strides 4 blocks along it: 1.5x damage and a heavy shove to the first one it meets.</li>
 *     <li>Slow and unshakeable (no knockback). With no prey for 10 s it walks back to its place and kneels again.</li>
 * </ul>
 */
public class OathboundStatue extends ActionMonster {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 2.6F;
    private static final EntityDataAccessor<Boolean> DATA_AWAKE = SynchedEntityData.defineId(OathboundStatue.class,
            EntityDataSerializers.BOOLEAN);
    private static final int SLAM_HIT = 22;      // 1.1 s, matches oathbound_statue.py
    private static final int SWEEP_HIT = 17;     // 0.85 s
    private static final int CHARGE_LOCK = 14;
    private static final int CHARGE_GO = 18;     // 0.9 s
    private static final int CHARGE_END = 30;    // 1.5 s
    private static final int DORMANT_RESTART = 70;

    private @Nullable BlockPos home;
    private float homeYaw;
    private int slamCooldown = 20;
    private int sweepCooldown = 40;
    private int chargeCooldown = 80;
    private int idleTicks;
    private boolean chargeHit;
    private Vec3 chargeDir = Vec3.ZERO;

    public OathboundStatue(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 16;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 60.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 11.0)
                .add(Attributes.MOVEMENT_SPEED, 0.18)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new StatueGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                (e, level) -> awake()));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_AWAKE, false);
    }

    public boolean awake() {
        return entityData.get(DATA_AWAKE);
    }

    private void setAwake(boolean v) {
        entityData.set(DATA_AWAKE, v);
    }

    @Override
    public int modelVariant() {
        return awake() ? 1 : 0;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.OathboundStatue.TICKS;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Awake", awake());
        if (home != null) {
            output.putLong("Home", home.asLong());
            output.putFloat("HomeYaw", homeYaw);
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        setAwake(input.getBooleanOr("Awake", false));
        long h = input.getLongOr("Home", Long.MIN_VALUE);
        home = h == Long.MIN_VALUE ? null : BlockPos.of(h);
        homeYaw = input.getFloatOr("HomeYaw", getYRot());
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return awake() && super.removeWhenFarAway(distance);
    }

    @Override
    public boolean isPushable() {
        return awake() && super.isPushable();
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ waking

    private void wake(ServerLevel level) {
        if (awake()) {
            return;
        }
        setAwake(true);
        idleTicks = 0;
        begin(MobAnims.OathboundStatue.WAKE);
        level.playSound(null, this, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.4F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.0F, 0.6F);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState()),
                getX(), getY() + 1.2, getZ(), 40, 0.5, 0.8, 0.5, 0.1);
        level.sendParticles(ParticleTypes.WAX_OFF, getX(), getY() + 1.6, getZ(), 20, 0.5, 0.8, 0.5, 0.2);
    }

    private void sleep(ServerLevel level) {
        setAwake(false);
        setTarget(null);
        getNavigation().stop();
        if (home != null) {
            setYRot(homeYaw);
            yBodyRot = homeYaw;
            yHeadRot = homeYaw;
        }
        begin(MobAnims.OathboundStatue.DORMANT);
        level.playSound(null, this, SoundEvents.STONE_PLACE, SoundSource.HOSTILE, 1.2F, 0.5F);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (!awake() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            amount *= 0.25F;
            boolean hurt = super.hurtServer(level, source, amount);
            if (isAlive()) {
                wake(level);
            }
            return hurt;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (home == null) {
            home = blockPosition();
            homeYaw = getYRot();
        }
        if (slamCooldown > 0) {
            slamCooldown--;
        }
        if (sweepCooldown > 0) {
            sweepCooldown--;
        }
        if (chargeCooldown > 0) {
            chargeCooldown--;
        }
        if (!awake()) {
            // kneel, still as stone, until someone comes too close
            getNavigation().stop();
            setDeltaMovement(0, getDeltaMovement().y, 0);
            setYRot(homeYaw);
            yBodyRot = homeYaw;
            yHeadRot = homeYaw;
            if (action != MobAnims.OathboundStatue.DORMANT || actionTick >= DORMANT_RESTART) {
                begin(MobAnims.OathboundStatue.DORMANT);
            } else {
                actionTick++;
            }
            if (tickCount % 5 == 0) {
                Player p = level.getNearestPlayer(this, 6.0);
                if (p != null && !p.isCreative() && !p.isSpectator() && getSensing().hasLineOfSight(p)) {
                    wake(level);
                    setTarget(p);
                }
            }
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && awake() && random.nextInt(8) == 0) {
            level().addParticle(ParticleTypes.WAX_OFF, getRandomX(0.6), getY() + 0.4 + random.nextDouble() * 2.0,
                    getRandomZ(0.6), 0, 0.02, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return awake() ? SoundEvents.IRON_GOLEM_STEP : null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.STONE_HIT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.STONE_BREAK;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.8F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.6F;
    }

    /** Wake, fight slowly and heavily, go back to its place and kneel when nobody is left. */
    static final class StatueGoal extends Goal {
        private final OathboundStatue s;
        private int repath;

        StatueGoal(OathboundStatue s) {
            this.s = s;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            return s.awake();
        }

        @Override
        public boolean canContinueToUse() {
            return s.awake();
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
                if (a != MobAnims.OathboundStatue.CHARGE) {
                    s.getNavigation().stop();
                }
                if (a == MobAnims.OathboundStatue.SLAM && k == SLAM_HIT) {
                    slam(level, t);
                } else if (a == MobAnims.OathboundStatue.SWEEP && k == SWEEP_HIT) {
                    sweep(level);
                } else if (a == MobAnims.OathboundStatue.CHARGE) {
                    charge(level, t, k);
                }
                return;
            }
            if (t == null || !t.isAlive()) {
                // nobody left: walk home and kneel again
                s.setTarget(null);
                if (++s.idleTicks > 200 && s.home != null) {
                    if (s.home.distToCenterSqr(s.position()) <= 2.5) {
                        s.sleep(level);
                    } else if (--repath <= 0) {
                        repath = 20;
                        s.getNavigation().moveTo(s.home.getX() + 0.5, s.home.getY(), s.home.getZ() + 0.5, 0.9);
                    }
                }
                return;
            }
            s.idleTicks = 0;
            s.getLookControl().setLookAt(t, 15.0F, 30.0F);
            double dist = Math.sqrt(s.distanceToSqr(t));
            boolean sees = s.getSensing().hasLineOfSight(t);
            if (dist <= 3.8 && s.sweepCooldown == 0 && s.random.nextInt(3) == 0) {
                s.sweepCooldown = 100;
                s.begin(MobAnims.OathboundStatue.SWEEP);
                return;
            }
            if (dist <= 3.5 && s.slamCooldown == 0) {
                s.slamCooldown = 80;
                s.begin(MobAnims.OathboundStatue.SLAM);
                level.playSound(null, s, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 1.0F, 0.5F);
                return;
            }
            if (sees && dist >= 5.0 && dist <= 10.0 && s.chargeCooldown == 0 && s.onGround()
                    && Math.abs(t.getY() - s.getY()) < 1.5) {
                s.chargeCooldown = 160;
                s.chargeHit = false;
                s.chargeDir = s.toward(t);
                s.begin(MobAnims.OathboundStatue.CHARGE);
                level.playSound(null, s, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 1.0F, 1.2F);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                s.getNavigation().moveTo(t, 1.0);
            }
        }

        private void slam(ServerLevel level, @Nullable LivingEntity t) {
            Vec3 c = s.position().add(s.forward().scale(2.0));
            level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.8F, 0.7F);
            level.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.0F, 0.5F);
            BlockState under = level.getBlockState(BlockPos.containing(c.x, c.y - 0.5, c.z));
            if (!under.isAir()) {
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), c.x, c.y + 0.1, c.z, 40, 1.2, 0.1, 1.2, 0.2);
            }
            level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 1, 0, 0, 0, 0);
            float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE);
            if (t != null && t.isAlive() && s.distanceToSqr(t) <= 3.6 * 3.6) {
                Vec3 to = t.position().subtract(s.position()).multiply(1, 0, 1);
                if (to.lengthSqr() < 0.5 || to.normalize().dot(s.forward()) > 0.3) {
                    t.hurtServer(level, s.damageSources().mobAttack(s), dmg * 1.4F);
                }
            }
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(c.x - 3, c.y - 1, c.z - 3,
                    c.x + 3, c.y + 2, c.z + 3), e -> e != s && e.isAlive() && !(e instanceof OathboundStatue))) {
                if (e.distanceToSqr(c) > 9.0 || !e.onGround()) {
                    continue;                                          // jump to dodge the shockwave
                }
                if (e != t) {
                    e.hurtServer(level, s.damageSources().mobAttack(s), dmg * 0.6F);
                }
                e.push(0, 0.55, 0);
                e.hurtMarked = true;
            }
        }

        private void sweep(ServerLevel level) {
            level.playSound(null, s, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.4F, 0.5F);
            Vec3 fwd = s.forward();
            for (int i = -4; i <= 4; i++) {
                double a = i * 0.38;
                Vec3 d = new Vec3(fwd.x * Math.cos(a) - fwd.z * Math.sin(a), 0, fwd.x * Math.sin(a) + fwd.z * Math.cos(a));
                Vec3 p = s.position().add(d.scale(2.6));
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.1, p.z, 1, 0, 0, 0, 0);
            }
            float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE);
            Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, s.getBoundingBox().inflate(4.0, 1.0, 4.0),
                    e -> e != s && e.isAlive() && !(e instanceof OathboundStatue))) {
                Vec3 to = e.position().subtract(s.position()).multiply(1, 0, 1);
                if (to.lengthSqr() > 4.0 * 4.0 || (to.lengthSqr() > 0.5 && to.normalize().dot(fwd) < -0.1)) {
                    continue;
                }
                if (e.hurtServer(level, s.damageSources().mobAttack(s), dmg)) {
                    e.push(side.x * 0.8 + fwd.x * 0.3, 0.25, side.z * 0.8 + fwd.z * 0.3);
                    e.hurtMarked = true;
                }
            }
        }

        private void charge(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < CHARGE_GO) {
                s.getNavigation().stop();
                if (t != null && k <= CHARGE_LOCK) {
                    s.chargeDir = s.toward(t);
                }
                float yaw = (float) (Mth.atan2(s.chargeDir.z, s.chargeDir.x) * Mth.RAD_TO_DEG) - 90.0F;
                s.setYRot(yaw);
                s.yBodyRot = yaw;
                s.yHeadRot = yaw;
                if (k % 3 == 0) {
                    // the telegraph: a line of dust along the path it will take
                    for (double d = 1.0; d <= 5.5; d += 1.0) {
                        Vec3 p = s.position().add(s.chargeDir.scale(d));
                        level.sendParticles(ParticleTypes.WAX_OFF, p.x, p.y + 0.1, p.z, 1, 0.05, 0.0, 0.05, 0.0);
                    }
                }
                return;
            }
            if (k > CHARGE_END) {
                s.setDeltaMovement(s.getDeltaMovement().multiply(0.4, 1, 0.4));
                return;
            }
            if (s.horizontalCollision) {
                return;
            }
            s.setDeltaMovement(s.chargeDir.x * 0.35, s.getDeltaMovement().y, s.chargeDir.z * 0.35);
            if (k % 2 == 0) {
                BlockState under = level.getBlockState(s.blockPosition().below());
                if (!under.isAir()) {
                    level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, under), s.getX(), s.getY() + 0.1, s.getZ(),
                            6, 0.3, 0.05, 0.3, 0.1);
                }
            }
            if (!s.chargeHit) {
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, s.getBoundingBox().inflate(0.6),
                        e -> e != s && e.isAlive() && !(e instanceof OathboundStatue))) {
                    s.chargeHit = true;
                    float dmg = (float) s.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.5F;
                    if (e.hurtServer(level, s.damageSources().mobAttack(s), dmg)) {
                        e.push(s.chargeDir.x * 1.4, 0.4, s.chargeDir.z * 1.4);
                        e.hurtMarked = true;
                    }
                    level.playSound(null, s, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.8F, 0.7F);
                    break;
                }
            }
        }
    }
}

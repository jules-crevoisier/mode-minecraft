package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Appeleur d'astres (Star Mote Swarm-Caller): a floating star crystal of the Starfall Library (model
 * tools/wf/mobs/star_mote_caller.py). It hovers at head height and keeps about six blocks from its prey.
 * <ul>
 *     <li><b>Star beam</b> (3 to 10 blocks, in sight, every 2.5 s): its satellite shards swing round in front of it
 *     while a thin line of starlight traces where it aims; the aim <b>locks at 12 ticks</b> and a short beam (8 blocks,
 *     stopped by blocks) fires at 15: magic damage to everything on the line. Step off the traced line after the lock.</li>
 *     <li><b>Call the motes</b> (once, when hurt below 70% or after 5 s of fighting, prey within 12 blocks): the shards
 *     fly out on a wide ring and the crystal swells and flares for a second, then two {@link StarMote}s fall out of
 *     the dark. Hit it during the flare to stop the call (it is not lost: it comes back later).</li>
 *     <li><b>Repel</b> (prey within 2.5 blocks, every 5 s): draws in tight, then at 12 ticks a nova throws everything
 *     within 3.5 blocks back and hurts a little.</li>
 * </ul>
 */
public class StarMoteCaller extends ActionMonster {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.0F;
    private static final int BEAM_LOCK = 12;
    private static final int BEAM_FIRE = 15;     // 0.75 s, matches star_mote_caller.py
    private static final int CALL_AT = 20;       // 1.0 s
    private static final int PULSE_AT = 12;      // 0.6 s
    private static final double BEAM_RANGE = 8.0;

    private int beamCooldown = 30;
    private int pulseCooldown = 40;
    private int fightTicks;
    private int callCooldown;
    private boolean called;
    private boolean callHurt;
    private Vec3 aim = Vec3.ZERO;

    public StarMoteCaller(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 10;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.22)
                .add(Attributes.FLYING_SPEED, 0.28)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5)
                .add(Attributes.FOLLOW_RANGE, 24.0);
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
        goalSelector.addGoal(2, new CallerGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.5));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StarMoteCaller.TICKS;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Called", called);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        called = input.getBooleanOr("Called", false);
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private Vec3 core() {
        return position().add(0, 0.55, 0);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && action == MobAnims.StarMoteCaller.CALL && actionTick < CALL_AT) {
            callHurt = true;                                                // the flare broken: no motes this time
        }
        return hurt;
    }

    private void callMotes(ServerLevel level) {
        if (callHurt) {
            callHurt = false;
            called = false;                                                  // it will try again later
            callCooldown = 200;
            level.playSound(null, this, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.0F, 1.4F);
            level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 0.6, getZ(), 12, 0.4, 0.4, 0.4, 0.2);
            return;
        }
        called = true;
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 1.4F, 1.6F);
        level.playSound(null, this, SoundEvents.ILLUSIONER_CAST_SPELL, SoundSource.HOSTILE, 1.0F, 1.4F);
        for (int i = 0; i < 2; i++) {
            StarMote mote = ModEntities.STAR_MOTE.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mote == null) {
                continue;
            }
            double a = Math.PI * i + random.nextDouble();
            Vec3 p = position().add(Math.cos(a) * 1.2, 1.4, Math.sin(a) * 1.2);
            mote.snapTo(p.x, p.y, p.z, random.nextFloat() * 360F, 0);
            if (getTarget() != null) {
                mote.setTarget(getTarget());
            }
            level.addFreshEntity(mote);
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 2.0, p.z, 10, 0.05, 1.0, 0.05, 0.0);
            level.sendParticles(ParticleTypes.FIREWORK, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.05);
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (beamCooldown > 0) {
            beamCooldown--;
        }
        if (pulseCooldown > 0) {
            pulseCooldown--;
        }
        if (callCooldown > 0) {
            callCooldown--;
        }
        fightTicks = getTarget() != null ? fightTicks + 1 : 0;
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 0.05, getZ(), 1, 0.08, 0.0, 0.08, 0.0);
        }
    }

    // ------------------------------------------------------------------ sounds: crystal chimes

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
        return super.getVoicePitch() * 1.2F;
    }

    /** Hang back and beam, call the motes once, push away anyone who comes close. */
    static final class CallerGoal extends Goal {
        private final StarMoteCaller c;
        private int repath;

        CallerGoal(StarMoteCaller c) {
            this.c = c;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = c.getTarget();
            return t != null && t.isAlive();
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
            if (c.action >= 0) {
                int a = c.action;
                int k = c.step();
                c.getNavigation().stop();
                c.setDeltaMovement(c.getDeltaMovement().scale(0.5));
                if (a == MobAnims.StarMoteCaller.BEAM) {
                    beam(level, t, k);
                } else if (a == MobAnims.StarMoteCaller.CALL) {
                    if (k >= 0 && k < CALL_AT && k % 2 == 0) {
                        // the telegraph: starlight swirling in to the swelling crystal
                        double ang = k * 0.6;
                        for (int i = 0; i < 4; i++) {
                            double b = ang + i * Math.PI / 2;
                            Vec3 p = c.core().add(Math.cos(b) * 1.6, 0.2 * Math.sin(k), Math.sin(b) * 1.6);
                            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.0, 0.0, 0.0, 0.0);
                        }
                        if (k % 6 == 0) {
                            level.playSound(null, c, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 1.2F, 0.6F + k * 0.05F);
                        }
                    }
                    if (k == CALL_AT) {
                        c.callMotes(level);
                    }
                } else if (a == MobAnims.StarMoteCaller.PULSE) {
                    if (k >= 0 && k < PULSE_AT && k % 3 == 0) {
                        Vec3 p = c.core();
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y, p.z, 6, 0.6, 0.6, 0.6, 0.02);
                    }
                    if (k == PULSE_AT) {
                        pulse(level);
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(c.distanceToSqr(t));
            boolean sees = c.getSensing().hasLineOfSight(t);
            if (!c.called && c.callCooldown == 0 && dist <= 12.0 && sees && (c.getHealth() < c.getMaxHealth() * 0.7F || c.fightTicks > 100)
                    && c.random.nextInt(10) == 0) {
                c.called = true;                                            // set again in callMotes; cleared by a broken flare
                c.callHurt = false;
                c.begin(MobAnims.StarMoteCaller.CALL);
                return;
            }
            if (dist <= 2.5 && c.pulseCooldown == 0) {
                c.pulseCooldown = 100;
                c.begin(MobAnims.StarMoteCaller.PULSE);
                level.playSound(null, c, SoundEvents.BEACON_DEACTIVATE, SoundSource.HOSTILE, 1.0F, 1.8F);
                return;
            }
            if (dist >= 3.0 && dist <= 10.0 && sees && c.beamCooldown == 0) {
                c.beamCooldown = 50;
                c.aim = t.getEyePosition().add(0, -0.4, 0);
                c.begin(MobAnims.StarMoteCaller.BEAM);
                level.playSound(null, c, SoundEvents.BEACON_AMBIENT, SoundSource.HOSTILE, 1.2F, 1.8F);
                return;
            }
            if (--repath <= 0) {
                repath = 12;
                // hover about six blocks off, a little above the prey's eyes
                Vec3 away = c.position().subtract(t.position()).multiply(1, 0, 1);
                away = away.lengthSqr() < 1.0E-4 ? c.forward().scale(-1) : away.normalize();
                Vec3 spot = t.position().add(away.scale(6.0)).add(0, t.getBbHeight() + 0.5, 0);
                if (dist > 8.0 || dist < 4.0 || !sees) {
                    c.getNavigation().moveTo(spot.x, spot.y, spot.z, 1.0);
                }
            }
        }

        private void beam(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                return;
            }
            if (k <= BEAM_LOCK && t != null && t.isAlive()) {
                c.aim = t.getEyePosition().add(0, -0.4, 0);
                c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            }
            Vec3 from = c.core();
            Vec3 dir = c.aim.subtract(from);
            dir = dir.lengthSqr() < 1.0E-4 ? c.forward() : dir.normalize();
            Vec3 end = from.add(dir.scale(BEAM_RANGE));
            HitResult hit = level.clip(new ClipContext(from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, c));
            if (hit.getType() != HitResult.Type.MISS) {
                end = hit.getLocation();
            }
            if (k < BEAM_FIRE) {
                // the telegraph: a thin trace of starlight along the aim (denser once locked)
                if (k % 2 == 0) {
                    Vec3 step = end.subtract(from);
                    int n = Math.max(3, (int) (step.length() * (k > BEAM_LOCK ? 3 : 1.2)));
                    for (int i = 1; i <= n; i++) {
                        Vec3 p = from.add(step.scale(i / (double) n));
                        level.sendParticles(k > BEAM_LOCK ? ParticleTypes.ELECTRIC_SPARK : ParticleTypes.END_ROD, p.x, p.y, p.z, 1,
                                0.0, 0.0, 0.0, 0.0);
                    }
                }
                if (k == BEAM_LOCK) {
                    level.playSound(null, c, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 1.0F, 2.0F);
                }
                return;
            }
            if (k == BEAM_FIRE) {
                level.playSound(null, c, SoundEvents.GUARDIAN_ATTACK, SoundSource.HOSTILE, 0.8F, 2.0F);
                Vec3 step = end.subtract(from);
                int n = Math.max(4, (int) (step.length() * 4));
                for (int i = 1; i <= n; i++) {
                    Vec3 p = from.add(step.scale(i / (double) n));
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                    level.sendParticles(ParticleTypes.GLOW, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
                }
                float dmg = (float) c.getAttributeValue(Attributes.ATTACK_DAMAGE);
                AABB box = new AABB(from, end).inflate(0.8);
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box,
                        e -> e != c && e.isAlive() && !(e instanceof StarMoteCaller) && !(e instanceof StarMote))) {
                    if (e.getBoundingBox().inflate(0.3).clip(from, end).isPresent()) {
                        e.hurtServer(level, c.damageSources().indirectMagic(c, c), dmg);
                    }
                }
            }
        }

        private void pulse(ServerLevel level) {
            level.playSound(null, c, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 1.4F, 0.8F);
            level.playSound(null, c, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 1.0F, 1.2F);
            Vec3 p = c.core();
            for (int i = 0; i < 24; i++) {
                double ang = i * Math.PI * 2 / 24;
                level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 0, Math.cos(ang), 0.05, Math.sin(ang), 0.35);
            }
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 6, 0.2, 0.2, 0.2, 0.05);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, c.getBoundingBox().inflate(3.5),
                    e -> e != c && e.isAlive() && !(e instanceof StarMoteCaller) && !(e instanceof StarMote))) {
                if (c.distanceToSqr(e) > 3.5 * 3.5) {
                    continue;
                }
                if (e.hurtServer(level, c.damageSources().indirectMagic(c, c), 2.0F)) {
                    Vec3 push = e.position().subtract(c.position()).multiply(1, 0, 1);
                    push = push.lengthSqr() < 1.0E-4 ? c.forward() : push.normalize();
                    e.push(push.x * 1.3, 0.45, push.z * 1.3);
                    e.hurtMarked = true;
                }
            }
        }
    }
}

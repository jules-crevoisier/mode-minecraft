package com.wayfarers.entity.ocean;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.boat.AbstractBoat;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Serpent de mer (Sea Serpent): a rare mini-boss of the deep oceans. It rises at night under lone boats and swimmers
 * (see OceanEvents), and dives away at dawn if nobody fought it.
 * <ul>
 *     <li><b>Bite</b> (close): rears back for 6 ticks and snaps (9 damage). A rider is knocked out of their boat.</li>
 *     <li><b>Lunge</b> (6 to 18 blocks, every 7 s): coils for 8 ticks, then shoots forward with its jaw open;
 *     whatever it hits takes 11 damage and is thrown, and a boat in its way is smashed.</li>
 *     <li><b>Whirlpool</b> (every 15 s, below half health every 10 s): rears up out of the swell and roars; for 2
 *     seconds the sea turns around it, dragging swimmers and boats in, tipping riders into the water.</li>
 * </ul>
 * 120 health, armoured scales, a boss bar for the players fighting it. Drops Serpent Scales (Diving Helmet).
 */
public class SeaSerpent extends Monster implements AnimatedMob {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 1.5F;
    private static final int BITE_HIT = 8;
    private static final int LUNGE_WINDUP = 8;
    private static final int ROAR_PULL_START = 12;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private @Nullable ServerBossEvent bossBar;
    private int biteCooldown;
    private int lungeCooldown = 80;
    private int roarCooldown = 200;
    private int idleTicks;
    /** Risen from the deep by OceanEvents: sinks back at dawn if nobody fought it (spawn eggs and summons stay). */
    private boolean risen;

    public SeaSerpent(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new SmoothSwimmingMoveControl<>(this, 85, 10, 0.1F, 0.5F, false);
        this.lookControl = new SmoothSwimmingLookControl(this, 10);
        this.setPathfindingMalus(PathType.WATER, 0.0F);
        this.xpReward = 40;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 120.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 9.0)
                .add(Attributes.ATTACK_KNOCKBACK, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 1.1)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.FOLLOW_RANGE, 40.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(1, new SerpentAttackGoal(this));
        goalSelector.addGoal(5, new RandomSwimmingGoal(this, 0.8, 40));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, false));
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WaterBoundPathNavigation(this, level);
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
    protected void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
        moveRelative(getSpeed(), input);
        move(MoverType.SELF, getDeltaMovement());
        setDeltaMovement(getDeltaMovement().scale(0.9));
    }

    @Override
    public AABB cullingBox(AABB hitbox) {
        return hitbox.inflate(9.0, 3.0, 9.0);
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return !hasCustomName();
    }

    /** Called by OceanEvents for a serpent that rises at night: it will dive away at dawn. */
    public void markRisen() {
        risen = true;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Risen", risen);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        risen = input.getBooleanOr("Risen", false);
    }

    // ------------------------------------------------------------------ sounds: a deep, wet growl

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.ELDER_GUARDIAN_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.ELDER_GUARDIAN_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.ELDER_GUARDIAN_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.55F + random.nextFloat() * 0.1F;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;
    }

    // ------------------------------------------------------------------ boss bar and dawn

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (lungeCooldown > 0) {
            lungeCooldown--;
        }
        if (roarCooldown > 0) {
            roarCooldown--;
        }
        updateBossBar(level);
        // nobody to fight in daylight: it sinks back into the deep
        idleTicks = getTarget() == null ? idleTicks + 1 : 0;
        if (risen && idleTicks > 400 && level.isBrightOutside() && !isPersistenceRequired() && !hasCustomName()) {
            level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, getX(), getY() + 0.5, getZ(), 30, 1.0, 0.5, 1.0, 0.1);
            discard();
        }
    }

    private void updateBossBar(ServerLevel level) {
        if (bossBar == null) {
            bossBar = new ServerBossEvent(getUUID(), getDisplayName(), BossEvent.BossBarColor.BLUE,
                    BossEvent.BossBarOverlay.NOTCHED_6);
        }
        bossBar.setProgress(getHealth() / getMaxHealth());
        if (tickCount % 10 != 0) {
            return;
        }
        Set<ServerPlayer> near = new HashSet<>();
        if (getTarget() != null || getHealth() < getMaxHealth()) {
            for (Player p : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(32), Player::isAlive)) {
                if (p instanceof ServerPlayer sp) {
                    near.add(sp);
                }
            }
        }
        for (ServerPlayer p : List.copyOf(bossBar.getPlayers())) {
            if (!near.contains(p)) {
                bossBar.removePlayer(p);
            }
        }
        near.forEach(bossBar::addPlayer);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        if (bossBar != null) {
            bossBar.removePlayer(player);
        }
    }

    @Override
    public void remove(Entity.RemovalReason reason) {
        if (bossBar != null) {
            bossBar.removeAllPlayers();
        }
        super.remove(reason);
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        if (bossBar != null) {
            bossBar.setName(getDisplayName());
        }
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SeaSerpent.TICKS;
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
            if (isInWater() && random.nextInt(5) == 0) {
                level().addParticle(ParticleTypes.BUBBLE, getRandomX(0.8), getRandomY(), getRandomZ(0.8), 0, 0.05, 0);
            }
        }
    }

    // ------------------------------------------------------------------ brain

    private Vec3 facing() {
        float r = getYRot() * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    /** A rider is thrown into the water (and a boat hit hard enough breaks). */
    private static void capsize(ServerLevel level, LivingEntity victim, float boatDamage, DamageSource source) {
        if (victim.getVehicle() instanceof AbstractBoat boat) {
            victim.stopRiding();
            victim.push(0, 0.4, 0);
            victim.hurtMarked = true;
            if (boatDamage > 0) {
                boat.hurtServer(level, source, boatDamage);
            }
            level.playSound(null, boat, SoundEvents.WOOD_BREAK, SoundSource.HOSTILE, 1.0F, 0.7F);
        }
    }

    /** Bite up close, lunge from afar, whirlpool now and then; otherwise swim at the prey. */
    static final class SerpentAttackGoal extends Goal {
        private final SeaSerpent s;
        private int action = -1;
        private int tick;
        private boolean hit;
        private Vec3 lungeDir = Vec3.ZERO;

        SerpentAttackGoal(SeaSerpent s) {
            this.s = s;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = s.getTarget();
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
            s.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            hit = false;
            s.getNavigation().stop();
            AnimatedMob.playAction(s, which);
        }

        @Override
        public void tick() {
            if (!(s.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = s.getTarget();
            if (action == MobAnims.SeaSerpent.BITE) {
                tickBite(level, t);
                return;
            }
            if (action == MobAnims.SeaSerpent.LUNGE) {
                tickLunge(level, t);
                return;
            }
            if (action == MobAnims.SeaSerpent.ROAR) {
                tickRoar(level);
                return;
            }
            if (t == null) {
                return;
            }
            s.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(s.distanceToSqr(t));
            double reach = s.getBbWidth() * 0.5 + t.getBbWidth() * 0.5 + 2.2;
            if (s.roarCooldown == 0 && dist < 14.0) {
                begin(MobAnims.SeaSerpent.ROAR);
                level.playSound(null, s, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 0.5F);
                return;
            }
            if (dist <= reach && s.biteCooldown == 0) {
                begin(MobAnims.SeaSerpent.BITE);
                return;
            }
            if (dist >= 6.0 && dist <= 18.0 && s.lungeCooldown == 0 && s.isInWater()) {
                begin(MobAnims.SeaSerpent.LUNGE);
                level.playSound(null, s, SoundEvents.ELDER_GUARDIAN_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.4F);
                return;
            }
            if (s.tickCount % 8 == 0 || s.getNavigation().isDone()) {
                s.getNavigation().moveTo(t.getX(), Math.min(t.getY(), s.level().getSeaLevel() - 1.2), t.getZ(), 1.2);
            }
        }

        private void tickBite(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            s.setDeltaMovement(s.getDeltaMovement().scale(0.8));
            if (t != null) {
                s.getLookControl().setLookAt(t, 60.0F, 60.0F);
                if (k == BITE_HIT) {
                    Vec3 mouth = s.position().add(s.facing().scale(2.0)).add(0, s.getBbHeight() * 0.5, 0);
                    if (t.getBoundingBox().inflate(1.6).contains(mouth) || s.distanceToSqr(t) < 12.0) {
                        if (s.doHurtTarget(level, t)) {
                            capsize(level, t, 0.0F, s.damageSources().mobAttack(s));
                        }
                    }
                    level.playSound(null, s, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.HOSTILE, 1.2F, 0.6F);
                }
            }
            if (k >= MobAnims.SeaSerpent.TICKS[MobAnims.SeaSerpent.BITE]) {
                action = -1;
                s.biteCooldown = 24 + s.random.nextInt(12);
            }
        }

        private void tickLunge(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            if (k < LUNGE_WINDUP) {
                s.setDeltaMovement(s.getDeltaMovement().scale(0.6));
                if (t != null) {
                    s.getLookControl().setLookAt(t, 90.0F, 90.0F);
                    lungeDir = t.position().add(0, t.getBbHeight() * 0.5, 0).subtract(s.position()).normalize();
                }
            } else if (k < LUNGE_WINDUP + 14) {
                Vec3 v = lungeDir.scale(1.1);
                if (!s.isInWater()) {
                    v = v.multiply(1, 0, 1).add(0, -0.1, 0);
                }
                s.setDeltaMovement(v);
                if (k % 2 == 0) {
                    level.sendParticles(ParticleTypes.BUBBLE, s.getX(), s.getY() + 0.7, s.getZ(), 6, 0.5, 0.4, 0.5, 0.05);
                }
                if (!hit) {
                    AABB jaws = s.getBoundingBox().inflate(0.8);
                    for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, jaws, e -> e != s && e.isAlive()
                            && !(e instanceof SeaSerpent) && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e))) {
                        hit = true;
                        DamageSource src = s.damageSources().mobAttack(s);
                        if (e.hurtServer(level, src, 11.0F)) {
                            e.push(lungeDir.x * 1.2, 0.5, lungeDir.z * 1.2);
                            e.hurtMarked = true;
                        }
                        capsize(level, e, 40.0F, src);
                    }
                    for (AbstractBoat boat : level.getEntitiesOfClass(AbstractBoat.class, jaws)) {
                        hit = true;
                        boat.hurtServer(level, s.damageSources().mobAttack(s), 40.0F);
                    }
                    if (hit) {
                        level.playSound(null, s, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.HOSTILE, 1.5F, 0.5F);
                        s.setDeltaMovement(s.getDeltaMovement().scale(-0.2));
                    }
                }
            } else {
                s.setDeltaMovement(s.getDeltaMovement().scale(0.7));
            }
            if (k >= MobAnims.SeaSerpent.TICKS[MobAnims.SeaSerpent.LUNGE]) {
                action = -1;
                s.lungeCooldown = 140 + s.random.nextInt(40);
            }
        }

        private void tickRoar(ServerLevel level) {
            int k = tick++;
            s.setDeltaMovement(s.getDeltaMovement().scale(0.5));
            if (k >= ROAR_PULL_START && k < ROAR_PULL_START + 40) {
                Vec3 c = s.position();
                // a ring of bubbles turning around the serpent
                double a = k * 0.45;
                for (int i = 0; i < 3; i++) {
                    double r = 3.0 + i * 2.5;
                    double ang = a + i * 2.1;
                    level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, c.x + Math.cos(ang) * r, c.y + 0.5,
                            c.z + Math.sin(ang) * r, 4, 0.3, 0.6, 0.3, 0.05);
                    level.sendParticles(ParticleTypes.SPLASH, c.x + Math.cos(ang + 1) * r, s.level().getSeaLevel(),
                            c.z + Math.sin(ang + 1) * r, 6, 0.5, 0.1, 0.5, 0.2);
                }
                AABB area = s.getBoundingBox().inflate(11.0, 6.0, 11.0);
                for (Entity e : level.getEntities(s, area, e -> e.isAlive() && !(e instanceof SeaSerpent)
                        && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e) && (e.isInWater() || e instanceof AbstractBoat))) {
                    Vec3 to = c.subtract(e.position());
                    double d = Math.max(1.0, to.horizontalDistance());
                    Vec3 in = new Vec3(to.x / d, 0, to.z / d);
                    Vec3 swirl = new Vec3(-in.z, 0, in.x);
                    e.setDeltaMovement(e.getDeltaMovement().add(in.scale(0.06)).add(swirl.scale(0.08)).add(0, -0.02, 0));
                    e.hurtMarked = true;
                    if (e instanceof LivingEntity le) {
                        if ((k - ROAR_PULL_START) % 10 == 0) { // (each refresh is an effect packet: not every tick)
                            le.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), s);
                        }
                        if (k == ROAR_PULL_START + 10) {
                            capsize(level, le, 0.0F, s.damageSources().mobAttack(s));
                        }
                    }
                }
                if (k % 10 == 0) {
                    level.playSound(null, s, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.7F);
                }
            }
            if (k >= MobAnims.SeaSerpent.TICKS[MobAnims.SeaSerpent.ROAR] + 30) {
                action = -1;
                s.roarCooldown = s.getHealth() < s.getMaxHealth() / 2 ? 200 : 300;
            }
        }
    }
}

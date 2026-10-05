package com.brasshaven.boss;

import com.brasshaven.block.BossSealBlockEntity;
import com.brasshaven.entity.AnimatedMob;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Base of every Brasshaven boss, built for Elden Ring style fights:
 * <ul>
 *     <li>telegraphed moves ({@link BossAttack}: wind-up, active frames, recovery window),</li>
 *     <li>a staged second phase (invulnerable roar, shockwave, new moveset),</li>
 *     <li>posture: enough damage in a short time staggers the boss, which then takes +50% damage,</li>
 *     <li>an arena: the boss never leaves it, and resets (full health, mist reopens) when everyone leaves or dies,</li>
 *     <li>a boss bar shown only to the players inside the arena, drawn by the client as a long bottom bar,</li>
 *     <li>"ENEMY FELLED" in gold for every player around when it dies.</li>
 * </ul>
 */
public abstract class WayfarerBoss extends Monster implements AnimatedMob {
    public static final String MINION_TAG = "brasshaven_minion";
    private static final EntityDataAccessor<Integer> DATA_PHASE = SynchedEntityData.defineId(WayfarerBoss.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> DATA_STAGGERED = SynchedEntityData.defineId(WayfarerBoss.class, EntityDataSerializers.BOOLEAN);

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private final List<BossAttack> attacks = new ArrayList<>();
    private final Map<String, Integer> cooldowns = new HashMap<>();
    private final List<Effect> effects = new ArrayList<>();
    private @Nullable ServerBossEvent bossBar;
    private @Nullable BossAttack current;
    private int attackTick;
    private float lockedYaw;
    private int idleDelay = 30;
    private float poise = -1;
    private int staggerTicks;
    private int lastHurtTick;
    private int roarTicks;
    private int emptyTicks;
    private boolean fightStarted;
    private @Nullable BlockPos home;
    private int arenaRadius = 24;
    private @Nullable BlockPos seal;

    protected WayfarerBoss(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setPersistenceRequired();
        this.xpReward = 250;
    }

    // ------------------------------------------------------------------ definition hooks

    /** Register the moveset (called once, on the first server tick). */
    protected abstract void defineAttacks(List<BossAttack> out);

    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.RED;
    }

    /** Damage needed (from players, without a 5 s pause) to break the boss's posture. */
    protected float maxPoise() {
        return 60.0F;
    }

    /** Health fraction at which phase 2 starts. */
    protected float phaseTwoAt() {
        return 0.5F;
    }

    /** Action index of the phase-change roar animation, or -1. */
    protected int roarAction() {
        return -1;
    }

    /** Action index of the stagger animation, or -1. */
    protected int staggerAction() {
        return -1;
    }

    /** How close the boss walks before choosing a move. */
    protected double preferredRange() {
        return 3.0;
    }

    protected void onPhaseTwo(ServerLevel level) {}

    protected void onDefeated(ServerLevel level) {}

    /** Ambient particles etc., every server tick while alive. */
    protected void bossTick(ServerLevel level) {}

    // ------------------------------------------------------------------ state

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_PHASE, 1);
        builder.define(DATA_STAGGERED, false);
    }

    public int phase() {
        return entityData.get(DATA_PHASE);
    }

    public boolean isStaggered() {
        return entityData.get(DATA_STAGGERED);
    }

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    public @Nullable BossAttack currentAttack() {
        return current;
    }

    /** Arena: centre, radius (blocks) and the seal that summoned the boss (may be null). */
    public void setArena(BlockPos center, int radius, @Nullable BlockPos sealPos) {
        this.home = center.immutable();
        this.arenaRadius = radius;
        this.seal = sealPos == null ? null : sealPos.immutable();
    }

    /** Co-op: +60% health per extra player, like the altars. */
    public void scaleForPlayers(int players) {
        if (players > 1) {
            var health = getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH);
            if (health != null) {
                health.setBaseValue(health.getBaseValue() * (1.0 + 0.6 * (players - 1)));
                setHealth(getMaxHealth());
            }
        }
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new ChaseGoal(this));
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 16.0F));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("BossPhase", phase());
        if (home != null) {
            output.putLong("BossHome", home.asLong());
        }
        output.putInt("BossArena", arenaRadius);
        if (seal != null) {
            output.putLong("BossSeal", seal.asLong());
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        entityData.set(DATA_PHASE, input.getIntOr("BossPhase", 1));
        long h = input.getLongOr("BossHome", Long.MIN_VALUE);
        home = h == Long.MIN_VALUE ? null : BlockPos.of(h);
        arenaRadius = input.getIntOr("BossArena", 24);
        long s = input.getLongOr("BossSeal", Long.MIN_VALUE);
        seal = s == Long.MIN_VALUE ? null : BlockPos.of(s);
    }

    // ------------------------------------------------------------------ client

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

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (attacks.isEmpty()) {
            defineAttacks(attacks);
        }
        if (home == null) {
            home = blockPosition();
        }
        if (poise < 0) {
            poise = maxPoise();
        }
        updateBossBar(level);
        tickEffects(level);
        cooldowns.replaceAll((k, v) -> Math.max(0, v - 1));
        bossTick(level);

        if (!arenaOccupied(level)) {
            if (fightStarted && ++emptyTicks > 400) {
                resetFight(level);
            }
            return;
        }
        emptyTicks = 0;
        if (home != null && distanceToSqr(Vec3.atBottomCenterOf(home)) > Mth.square(arenaRadius + 10)) {
            teleportHome(level);
        }
        LivingEntity target = getTarget();
        if (target != null && !fightStarted) {
            fightStarted = true;
        }
        if (roarTicks > 0) {
            roarTicks--;
            holdStill();
            return;
        }
        if (staggerTicks > 0) {
            if (--staggerTicks == 0) {
                entityData.set(DATA_STAGGERED, false);
            }
            holdStill();
            return;
        }
        if (phase() == 1 && getHealth() <= getMaxHealth() * phaseTwoAt()) {
            enterPhaseTwo(level);
            return;
        }
        if (tickCount - lastHurtTick > 100) {
            poise = Math.min(maxPoise(), poise + 0.5F);
        }
        if (current != null) {
            tickAttack(level, target);
            return;
        }
        if (idleDelay > 0) {
            idleDelay--;
            return;
        }
        if (target != null && target.isAlive()) {
            chooseAttack(level, target);
        }
    }

    private void chooseAttack(ServerLevel level, LivingEntity target) {
        double dist = Math.sqrt(distanceToSqr(target));
        List<BossAttack> eligible = new ArrayList<>();
        int total = 0;
        for (BossAttack a : attacks) {
            if (a.allowedIn(phase()) && dist >= a.minRange && dist <= a.maxRange && cooldowns.getOrDefault(a.name, 0) == 0) {
                eligible.add(a);
                total += a.weight;
            }
        }
        if (eligible.isEmpty()) {
            return;
        }
        int roll = random.nextInt(total);
        for (BossAttack a : eligible) {
            roll -= a.weight;
            if (roll < 0) {
                startAttack(level, a, target);
                return;
            }
        }
    }

    /** Start a move right away (also usable for combos from another move's end step). */
    public void startAttack(ServerLevel level, BossAttack attack, @Nullable LivingEntity target) {
        current = attack;
        attackTick = 0;
        lockedYaw = getYRot();
        cooldowns.put(attack.name, attack.cooldown);
        getNavigation().stop();
        if (attack.anim >= 0) {
            AnimatedMob.playAction(this, attack.anim);
        }
        attack.onStart.run(this, level, target, 0);
    }

    /** Start a move by name (combos). */
    public void chain(ServerLevel level, String name) {
        for (BossAttack a : attacks) {
            if (a.name.equals(name)) {
                startAttack(level, a, getTarget());
                return;
            }
        }
    }

    private void tickAttack(ServerLevel level, @Nullable LivingEntity target) {
        BossAttack a = current;
        int t = attackTick++;
        getNavigation().stop();
        if (t < a.windup) {
            if (a.track && target != null) {
                faceTarget(target, 25.0F);
            } else {
                lockRotation();
            }
            a.onWindup.run(this, level, target, t);
        } else if (t < a.windup + a.active) {
            if (t == a.windup) {
                lockedYaw = getYRot();
                a.onImpact.run(this, level, target, 0);
            }
            lockRotation();
            a.onActive.run(this, level, target, t - a.windup);
        } else if (t < a.length()) {
            lockRotation();
        } else {
            current = null;
            idleDelay = phase() == 1 ? 8 + random.nextInt(16) : 4 + random.nextInt(10);
            a.onEnd.run(this, level, target, 0);
        }
    }

    private void holdStill() {
        getNavigation().stop();
        setDeltaMovement(getDeltaMovement().multiply(0.0, 1.0, 0.0));
        lockRotation();
    }

    private void faceTarget(LivingEntity target, float maxTurn) {
        double dx = target.getX() - getX();
        double dz = target.getZ() - getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        float newYaw = Mth.approachDegrees(getYRot(), yaw, maxTurn);
        setYRot(newYaw);
        yBodyRot = newYaw;
        yHeadRot = newYaw;
        lockedYaw = newYaw;
    }

    /** Turn to {@code yaw} at once and keep facing it for the rest of the move (after a teleport, for instance). */
    public void snapFacing(float yaw) {
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
        lockedYaw = yaw;
    }

    private void lockRotation() {
        setYRot(lockedYaw);
        yBodyRot = lockedYaw;
        yHeadRot = lockedYaw;
    }

    private void enterPhaseTwo(ServerLevel level) {
        entityData.set(DATA_PHASE, 2);
        current = null;
        int roar = roarAction();
        roarTicks = roar >= 0 && roar < actionTicks().length ? actionTicks()[roar] : 40;
        lockedYaw = getYRot();
        if (roar >= 0) {
            AnimatedMob.playAction(this, roar);
        }
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 3.0F, 0.7F);
        for (LivingEntity e : victims(level, position(), 7.0)) {
            Vec3 push = e.position().subtract(position()).normalize().scale(1.8);
            e.push(push.x, 0.5, push.z);
            e.hurtMarked = true;
        }
        level.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 1, getZ(), 6, 1.5, 0.5, 1.5, 0.0);
        onPhaseTwo(level);
    }

    // ------------------------------------------------------------------ damage, posture

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (roarTicks > 0) {
            return false;
        }
        if (isStaggered()) {
            amount *= 1.5F;
        }
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && source.getEntity() instanceof Player) {
            lastHurtTick = tickCount;
            poise -= amount;
            if (poise <= 0 && staggerTicks == 0) {
                stagger(level);
            }
        }
        return hurt;
    }

    private void stagger(ServerLevel level) {
        current = null;
        staggerTicks = 50;
        poise = maxPoise();
        lockedYaw = getYRot();
        entityData.set(DATA_STAGGERED, true);
        if (staggerAction() >= 0) {
            AnimatedMob.playAction(this, staggerAction());
        }
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.5F);
        level.sendParticles(ParticleTypes.CRIT, getX(), getY() + getBbHeight() * 0.7, getZ(), 40, 0.6, 0.6, 0.6, 0.4);
    }

    // ------------------------------------------------------------------ arena, boss bar

    private AABB arenaBox() {
        BlockPos c = home != null ? home : blockPosition();
        return new AABB(c).inflate(arenaRadius + 4, 16, arenaRadius + 4);
    }

    /** Runs every tick: walks the player list rather than every entity section of the (large) arena box. */
    private boolean arenaOccupied(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.any(level, arenaBox(), p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    private void updateBossBar(ServerLevel level) {
        if (bossBar == null) {
            bossBar = new ServerBossEvent(getUUID(), getDisplayName(), barColor(), BossEvent.BossBarOverlay.PROGRESS);
        }
        bossBar.setProgress(getHealth() / getMaxHealth());
        if (tickCount % 10 != 0) {
            return;
        }
        Set<ServerPlayer> inside = new HashSet<>();
        if (fightStarted) {
            for (Player p : com.brasshaven.util.NearbyPlayers.in(level, arenaBox(), Player::isAlive)) {
                if (p instanceof ServerPlayer sp) {
                    inside.add(sp);
                }
            }
        }
        for (ServerPlayer p : List.copyOf(bossBar.getPlayers())) {
            if (!inside.contains(p)) {
                bossBar.removePlayer(p);
            }
        }
        for (ServerPlayer p : inside) {
            bossBar.addPlayer(p);
        }
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        if (bossBar != null) {
            bossBar.removePlayer(player);
        }
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        if (bossBar != null) {
            bossBar.setName(getDisplayName());
        }
    }

    private void teleportHome(ServerLevel level) {
        if (home != null) {
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1, getZ(), 20, 0.5, 1, 0.5, 0.05);
            teleportTo(home.getX() + 0.5, home.getY(), home.getZ() + 0.5);
            getNavigation().stop();
        }
    }

    /** Everyone left or died: the boss returns to full health and waits again (the mist reopens). */
    private void resetFight(ServerLevel level) {
        fightStarted = false;
        emptyTicks = 0;
        current = null;
        roarTicks = 0;
        staggerTicks = 0;
        effects.clear();
        cooldowns.clear();
        poise = maxPoise();
        entityData.set(DATA_PHASE, 1);
        entityData.set(DATA_STAGGERED, false);
        setTarget(null);
        // phase 2 speed-ups (onPhaseTwo) are permanent modifiers: back in phase 1, the boss walks at its base pace again
        var speed = getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            for (var modifier : List.copyOf(speed.getPermanentModifiers())) {
                if (modifier.id().getNamespace().equals(com.brasshaven.Brasshaven.MODID)) {
                    speed.removeModifier(modifier.id());
                }
            }
        }
        setHealth(getMaxHealth());
        teleportHome(level);
        if (bossBar != null) {
            bossBar.removeAllPlayers();
        }
        if (seal != null && level.getBlockEntity(seal) instanceof BossSealBlockEntity be) {
            be.onBossReset(this);
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (bossBar != null) {
            bossBar.removeAllPlayers();
        }
        if (level() instanceof ServerLevel level) {
            Component felled = Component.translatable("title.brasshaven.enemy_felled").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD);
            for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, arenaBox().inflate(16), ServerPlayer::isAlive)) {
                p.connection.send(new ClientboundSetTitlesAnimationPacket(10, 80, 30));
                p.connection.send(new ClientboundSetTitleTextPacket(felled));
                p.connection.send(new ClientboundSetSubtitleTextPacket(getDisplayName().copy().withStyle(ChatFormatting.YELLOW)));
            }
            level.playSound(null, this, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.HOSTILE, 2.0F, 0.8F);
            level.getServer().getPlayerList().broadcastSystemMessage(
                    Component.translatable("message.brasshaven.boss.defeated", getDisplayName()).withStyle(ChatFormatting.GOLD), false);
            onDefeated(level);
            if (seal != null && level.getBlockEntity(seal) instanceof BossSealBlockEntity be) {
                be.onBossDefeated(this);
            }
        }
    }

    // ------------------------------------------------------------------ helpers for movesets

    /** Unit vector the boss faces (locked during active frames). */
    public Vec3 forward() {
        float yaw = lockedYaw * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** A point on the ground {@code dist} blocks in front of the boss. */
    public Vec3 ahead(double dist) {
        return position().add(forward().scale(dist));
    }

    /** Players (not creative/spectator) and non-hostile creatures within radius, never the boss's own side. */
    public List<LivingEntity> victims(ServerLevel level, Vec3 center, double radius) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(center, center).inflate(radius, 4, radius), e -> {
            if (e == this || !e.isAlive() || e.entityTags().contains(MINION_TAG) || e instanceof WayfarerBoss) {
                return false;
            }
            if (e instanceof Player p) {
                return !p.isCreative() && !p.isSpectator();
            }
            return !(e instanceof Enemy);
        });
    }

    /** Damage + knockback away from the boss; {@code lift} adds an upward push. */
    public void strike(ServerLevel level, LivingEntity e, float damage, double knockback, double lift) {
        if (e.hurtServer(level, damageSources().mobAttack(this), damage) && knockback > 0) {
            Vec3 push = e.position().subtract(position()).multiply(1, 0, 1).normalize().scale(knockback);
            e.push(push.x, lift, push.z);
            e.hurtMarked = true;
        }
    }

    /** Hit everything in a circle. */
    public void hitCircle(ServerLevel level, Vec3 center, double radius, float damage, double knockback, double lift) {
        for (LivingEntity e : victims(level, center, radius)) {
            if (e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1)) <= radius) {
                strike(level, e, damage, knockback, lift);
            }
        }
    }

    /** Hit everything in front within {@code range} and {@code halfAngle} degrees of the facing. */
    public void hitArc(ServerLevel level, double range, double halfAngle, float damage, double knockback) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        for (LivingEntity e : victims(level, position(), range + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                strike(level, e, damage, knockback, 0.25);
            }
        }
    }

    /** Hit everything along a straight line in front of the boss. */
    public void hitLine(ServerLevel level, double length, double halfWidth, float damage, double knockback) {
        Vec3 fwd = forward();
        for (LivingEntity e : victims(level, position(), length + 1)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double along = to.dot(fwd);
            double side = to.subtract(fwd.scale(along)).length();
            if (along >= 0 && along <= length && side <= halfWidth + e.getBbWidth() / 2) {
                strike(level, e, damage, knockback, 0.2);
            }
        }
    }

    /** Ground telegraph: a ring of particles (call during the wind-up). */
    public void telegraphRing(ServerLevel level, Vec3 center, double radius, ParticleOptions particle) {
        int n = Math.max(12, (int) (radius * 7));
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / n;
            level.sendParticles(particle, center.x + Math.cos(a) * radius, center.y + 0.15, center.z + Math.sin(a) * radius,
                    1, 0, 0, 0, 0);
        }
    }

    /** Ground telegraph: the outline of the arc that {@link #hitArc} will cover. */
    public void telegraphArc(ServerLevel level, double range, double halfAngle, ParticleOptions particle) {
        float base = lockedYaw;
        for (double a = -halfAngle; a <= halfAngle; a += Math.max(6, halfAngle / 6)) {
            float yaw = (float) (base + a) * Mth.DEG_TO_RAD;
            Vec3 dir = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
            Vec3 p = position().add(dir.scale(range));
            level.sendParticles(particle, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    /** Launch the boss forward (lunges, charges, leaps). */
    public void lunge(double speed, double up) {
        Vec3 f = forward().scale(speed);
        setDeltaMovement(f.x, up, f.z);
        hurtMarked = true;
    }

    /** Summon helpers around the boss; they target the boss's target and never hurt it. */
    public void summon(ServerLevel level, EntityType<? extends Mob> type, int count, double radius) {
        for (int i = 0; i < count; i++) {
            Mob minion = type.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (minion == null) {
                continue;
            }
            double angle = random.nextDouble() * Math.PI * 2;
            minion.snapTo(getX() + Math.cos(angle) * radius, getY(), getZ() + Math.sin(angle) * radius, getYRot(), 0);
            minion.addTag(MINION_TAG);
            minion.setTarget(getTarget());
            level.addFreshEntity(minion);
            level.sendParticles(ParticleTypes.POOF, minion.getX(), minion.getY() + 1, minion.getZ(), 15, 0.3, 0.5, 0.3, 0.05);
        }
    }

    // ------------------------------------------------------------------ timed effects (waves, eruptions)

    /** Something that plays out over several ticks after a move (expanding waves, delayed eruptions). */
    public interface Effect {
        /** @return true when finished */
        boolean tick(WayfarerBoss boss, ServerLevel level);
    }

    public void addEffect(Effect effect) {
        effects.add(effect);
    }

    private void tickEffects(ServerLevel level) {
        if (effects.isEmpty()) {
            return;
        }
        for (Effect e : new ArrayList<>(effects)) { // effects may queue more effects while ticking
            if (e.tick(this, level)) {
                effects.remove(e);
            }
        }
    }

    /**
     * A shockwave ring expanding from {@code center}: it hits once whoever stands on its edge at ground level.
     * Jump over it to dodge.
     */
    public static Effect wave(Vec3 center, double maxRadius, double speed, float damage, ParticleOptions particle) {
        Set<UUID> hit = new HashSet<>();
        double[] radius = {0.5};
        return (boss, level) -> {
            radius[0] += speed;
            double r = radius[0];
            int n = Math.max(16, (int) (r * 6));
            for (int i = 0; i < n; i++) {
                double a = Math.PI * 2 * i / n;
                level.sendParticles(particle, center.x + Math.cos(a) * r, center.y + 0.2, center.z + Math.sin(a) * r, 1, 0, 0.05, 0, 0);
            }
            for (LivingEntity e : boss.victims(level, center, r + 1.5)) {
                double d = e.position().multiply(1, 0, 1).distanceTo(center.multiply(1, 0, 1));
                boolean grounded = e.getY() - center.y < 0.9;
                if (Math.abs(d - r) <= 1.0 && grounded && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.8, 0.45);
                }
            }
            return r >= maxRadius;
        };
    }

    /** A ground eruption: warning particles for {@code delay} ticks, then a burst that hurts and throws up. */
    public static Effect eruption(Vec3 pos, int delay, double radius, float damage, ParticleOptions warn, ParticleOptions burst) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    level.sendParticles(warn, pos.x, pos.y + 0.1, pos.z, 6, radius * 0.5, 0.05, radius * 0.5, 0.01);
                }
            } else {
                level.sendParticles(burst, pos.x, pos.y + 0.5, pos.z, 30, radius * 0.4, 1.0, radius * 0.4, 0.15);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                        boss.strike(level, e, damage, 0.3, 0.9);
                    }
                }
                return true;
            }
            t[0]++;
            return false;
        };
    }

    // ------------------------------------------------------------------ movement goal

    /** Walk toward the target when not busy with a move; stop at the preferred range. */
    static final class ChaseGoal extends Goal {
        private final WayfarerBoss boss;

        ChaseGoal(WayfarerBoss boss) {
            this.boss = boss;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private boolean busy() {
            return boss.current != null || boss.staggerTicks > 0 || boss.roarTicks > 0;
        }

        @Override
        public boolean canUse() {
            LivingEntity t = boss.getTarget();
            return t != null && t.isAlive() && !busy();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity t = boss.getTarget();
            if (t == null) {
                return;
            }
            boss.getLookControl().setLookAt(t, 30.0F, 30.0F);
            if (boss.distanceToSqr(t) > boss.preferredRange() * boss.preferredRange()) {
                if (boss.tickCount % 5 == 0) {
                    boss.getNavigation().moveTo(t, 1.0);
                }
            } else {
                boss.getNavigation().stop();
            }
        }

        @Override
        public void stop() {
            boss.getNavigation().stop();
        }
    }
}

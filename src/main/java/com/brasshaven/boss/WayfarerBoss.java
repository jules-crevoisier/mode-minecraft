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
    // difficulty: co-op scaling and NG+ cycles (see tools/BOSSES.md, "Difficulty")
    private boolean difficultyApplied;
    private int cycle = -1;
    private int scaledPlayers = 1;
    private int playerHint = 1;
    private int enrageTimer;
    private int effWindup;
    private int effRecovery;
    private int windupDone;

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

    /**
     * Co-op hint from whoever spawns the boss (seal, altar): the boss scales for at least this many players. The
     * scaling itself happens on the boss's first server tick ({@link #applyDifficulty}), for every spawn path.
     */
    public void scaleForPlayers(int players) {
        playerHint = Math.max(playerHint, players);
        if (difficultyApplied && players > scaledPlayers) {
            scalePlayers(players);
        }
    }

    // ------------------------------------------------------------------ difficulty: co-op scaling, NG+ cycles

    /** NG+ cycle of this fight (0 = first time), or -1 before the first tick. */
    public int cycle() {
        return Math.max(0, cycle);
    }

    /** Players this boss is scaled for (never goes down mid-fight). */
    public int scaledPlayers() {
        return scaledPlayers;
    }

    /** Admin/command: force the cycle before (or after) the boss spawns. */
    public void setCycle(int c) {
        this.cycle = Mth.clamp(c, 0, BossCycles.MAX);
        if (difficultyApplied) {
            applyCycleModifiers();
            refreshBarName();
        }
    }

    public String bossTypeId() {
        return net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(getType()).toString();
    }

    /** Multiplier on every hit the boss deals (applied by {@link BossDifficulty} on LivingHurtEvent). */
    public float damageMultiplier() {
        return (float) ((1.0 + 0.10 * (scaledPlayers - 1)) * (1.0 + 0.15 * cycle()));
    }

    /** Minion count for {@code base} summoned helpers: +1 per 2 extra players (0 stays 0). */
    public int scaledCount(int base) {
        return base <= 0 ? base : base + (scaledPlayers - 1) / 2;
    }

    /** Cooldown multiplier: co-op (-10% per extra player, min 60%) times the cycle speed-up. */
    protected double cooldownScale() {
        double coop = scaledPlayers >= 2 ? Math.max(0.6, 1.0 - 0.10 * (scaledPlayers - 1)) : 1.0;
        return coop * cycleSpeed();
    }

    /** Timing multiplier of NG+ cycles: wind-ups, recoveries and pauses get up to 25% shorter. */
    protected double cycleSpeed() {
        return Math.max(0.75, 1.0 - 0.04 * cycle());
    }

    /** Readable minimum: a wind-up never drops below 10 ticks (nor below its authored length if shorter). */
    private int scaledWindup(int windup) {
        return Math.max(Math.min(windup, 10), (int) Math.round(windup * cycleSpeed()));
    }

    private int scaledRecovery(int recovery) {
        return Math.max(Math.min(recovery, 4), (int) Math.round(recovery * cycleSpeed()));
    }

    /** Poise with the co-op bonus (+25% per extra player). */
    protected float effectiveMaxPoise() {
        return maxPoise() * (1.0F + 0.25F * (scaledPlayers - 1));
    }

    private AABB leashBox() {
        BlockPos c = home != null ? home : blockPosition();
        return new AABB(c).inflate(arenaRadius, 12, arenaRadius);
    }

    private int countFighters(ServerLevel level) {
        return com.brasshaven.util.NearbyPlayers.in(level, leashBox(),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative()).size();
    }

    /** First server tick: read the world's NG+ cycle for this boss and scale for the players in the arena. */
    private void applyDifficulty(ServerLevel level) {
        difficultyApplied = true;
        if (cycle < 0) {
            cycle = BossCycles.get(level.getServer()).cycle(bossTypeId());
        }
        applyCycleModifiers();
        int players = Math.max(Math.max(1, playerHint), countFighters(level));
        scaledPlayers = 1;
        scalePlayers(players);
        refreshBarName();
    }

    /** The world's cycle went up since this boss spawned (it waited in its lair): catch up, never down. */
    private void refreshCycle(ServerLevel level) {
        int c = BossCycles.get(level.getServer()).cycle(bossTypeId());
        if (c > cycle()) {
            setCycle(c);
        }
    }

    private void applyCycleModifiers() {
        int c = cycle();
        setModifier(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH, "ng_health", 0.35 * c,
                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        setModifier(net.minecraft.world.entity.ai.attributes.Attributes.ARMOR, "ng_armor", 2.0 * c,
                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE);
    }

    /** Scale up for {@code players} (never down): HP x (1 + 0.75 per extra player), keeping the health fraction. */
    private void scalePlayers(int players) {
        if (players <= scaledPlayers && players > 1) {
            return;
        }
        scaledPlayers = Math.max(scaledPlayers, Math.max(1, players));
        setModifier(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH, "coop_health", 0.75 * (scaledPlayers - 1),
                net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        if (poise >= 0) {
            poise = effectiveMaxPoise();
        }
        refreshBarName();
    }

    private void setModifier(net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, String name,
                             double amount, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation op) {
        var inst = getAttribute(attribute);
        if (inst == null) {
            return;
        }
        float fraction = getMaxHealth() > 0 ? getHealth() / getMaxHealth() : 1.0F;
        var id = com.brasshaven.Brasshaven.id(name);
        inst.removeModifier(id);
        if (amount != 0) {
            inst.addPermanentModifier(new net.minecraft.world.entity.ai.attributes.AttributeModifier(id, amount, op));
        }
        if (attribute == net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH) {
            setHealth(Math.max(1.0F, getMaxHealth() * fraction));
        }
    }

    /** Boss bar title: name, "+c" from cycle 1, and the player count in co-op. */
    private Component barName() {
        var name = getDisplayName().copy();
        if (cycle() > 0) {
            name.append(Component.literal(" +" + cycle()).withStyle(ChatFormatting.GOLD));
        }
        if (scaledPlayers > 1) {
            name.append(Component.literal(" · ").withStyle(ChatFormatting.GRAY))
                    .append(Component.translatable("message.brasshaven.boss.players", scaledPlayers).withStyle(ChatFormatting.GRAY));
        }
        return name;
    }

    private void refreshBarName() {
        if (bossBar != null) {
            bossBar.setName(barName());
        }
    }

    /**
     * NG+ phase-2 rage (cycle 2+, every boss): every few seconds a telegraphed soul shockwave rolls out from the
     * boss (jump it), stronger and more frequent with each cycle.
     */
    private void tickEnrage(ServerLevel level) {
        if (cycle() < 2 || phase() != 2 || current != null || staggerTicks > 0 || roarTicks > 0) {
            return;
        }
        if (++enrageTimer < Math.max(100, 220 - 15 * cycle())) {
            return;
        }
        enrageTimer = 0;
        Vec3 center = position();
        int c = cycle();
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 1.5F, 1.4F);
        int[] t = {0};
        addEffect((boss, lvl) -> {
            if (t[0] < 20) {
                if (t[0] % 2 == 0) {
                    boss.telegraphRing(lvl, center, 1.5 + t[0] * 0.1, ParticleTypes.SOUL_FIRE_FLAME);
                }
                t[0]++;
                return false;
            }
            boss.addEffect(wave(center, 9.0 + c, 0.6, 4.0F + c, ParticleTypes.SOUL_FIRE_FLAME));
            return true;
        });
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
        output.putBoolean("BossScaled", difficultyApplied);
        output.putInt("BossCycle", cycle);
        output.putInt("BossPlayers", scaledPlayers);
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
        difficultyApplied = input.getBooleanOr("BossScaled", false);
        cycle = input.getIntOr("BossCycle", -1);
        scaledPlayers = Math.max(1, input.getIntOr("BossPlayers", 1));
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
        if (!difficultyApplied) {
            applyDifficulty(level);
        }
        if (poise < 0) {
            poise = effectiveMaxPoise();
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
            refreshCycle(level);
        }
        if (tickCount % 20 == 0) {
            int fighters = countFighters(level);
            if (fighters > scaledPlayers) {
                scalePlayers(fighters); // someone joined mid-fight: scale up once, never down
            }
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
            poise = Math.min(effectiveMaxPoise(), poise + 0.5F);
        }
        tickEnrage(level);
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
        effWindup = scaledWindup(attack.windup);
        effRecovery = scaledRecovery(attack.recovery);
        windupDone = 0;
        cooldowns.put(attack.name, (int) Math.round(attack.cooldown * cooldownScale()));
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
        if (t < effWindup) {
            if (a.track && target != null) {
                faceTarget(target, 25.0F);
            } else {
                lockRotation();
            }
            // NG+ wind-ups are compressed: every authored wind-up tick still runs (a few per tick when shorter)
            int upTo = effWindup == a.windup ? t : (int) ((long) (t + 1) * a.windup / effWindup) - 1;
            while (windupDone <= upTo && windupDone < a.windup && current == a) {
                a.onWindup.run(this, level, target, windupDone++);
            }
        } else if (t < effWindup + a.active) {
            if (t == effWindup) {
                lockedYaw = getYRot();
                a.onImpact.run(this, level, target, 0);
            }
            lockRotation();
            a.onActive.run(this, level, target, t - effWindup);
        } else if (t < effWindup + a.active + effRecovery) {
            lockRotation();
        } else {
            current = null;
            int idle = phase() == 1 ? 8 + random.nextInt(16) : 4 + random.nextInt(10);
            idleDelay = (int) Math.round(idle * cycleSpeed());
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
        // NG+ cycle 2+: the boss shakes off a stagger faster in phase 2
        staggerTicks = phase() == 2 && cycle() >= 2 ? Math.max(34, 50 - 3 * cycle()) : 50;
        poise = effectiveMaxPoise();
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
            bossBar = new ServerBossEvent(getUUID(), barName(), barColor(), BossEvent.BossBarOverlay.PROGRESS);
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
        refreshBarName();
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
        enrageTimer = 0;
        poise = effectiveMaxPoise();
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
            if (getLastHurtByPlayer() != null || source.getEntity() instanceof Player) {
                int before = cycle();
                int next = BossCycles.get(level.getServer()).defeated(bossTypeId());
                if (next > before) {
                    level.getServer().getPlayerList().broadcastSystemMessage(Component.translatable(
                            "message.brasshaven.boss.cycle_up", getDisplayName(), next).withStyle(ChatFormatting.DARK_RED), false);
                }
            }
            if (seal != null && level.getBlockEntity(seal) instanceof BossSealBlockEntity be) {
                be.onBossDefeated(this);
            }
        }
    }

    /**
     * NG+ loot: at cycle c the boss's loot table is rolled c more times (without its Remembrance, which stays
     * unique), and from cycle 3 an Ember of Ascension may drop (15% per cycle above 2).
     */
    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean killedByPlayer) {
        super.dropCustomDeathLoot(level, source, killedByPlayer);
        int c = cycle();
        if (c <= 0) {
            return;
        }
        getLootTable().ifPresent(key -> {
            for (int i = 0; i < c; i++) {
                dropFromLootTable(level, source, killedByPlayer, key, stack -> {
                    var id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem());
                    if (!id.getPath().startsWith("remembrance_")) {
                        spawnAtLocation(level, stack);
                    }
                });
            }
        });
        if (c >= 3 && random.nextFloat() < 0.15F * (c - 2)) {
            spawnAtLocation(level, new net.minecraft.world.item.ItemStack(com.brasshaven.registry.ModItems.EMBER_OF_ASCENSION.get()));
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
        count = scaledCount(count); // co-op: +1 helper per 2 extra players
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

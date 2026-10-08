package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.BogHierophant.FIRELINES;
import static com.brasshaven.generated.MobAnims.BogHierophant.KINDLE;
import static com.brasshaven.generated.MobAnims.BogHierophant.LEECHES;
import static com.brasshaven.generated.MobAnims.BogHierophant.LURE;
import static com.brasshaven.generated.MobAnims.BogHierophant.MIRE;
import static com.brasshaven.generated.MobAnims.BogHierophant.REAP;
import static com.brasshaven.generated.MobAnims.BogHierophant.ROAR;
import static com.brasshaven.generated.MobAnims.BogHierophant.SLAM;
import static com.brasshaven.generated.MobAnims.BogHierophant.STAGGER;
import static com.brasshaven.generated.MobAnims.BogHierophant.STOMP;
import static com.brasshaven.generated.MobAnims.BogHierophant.STRIDE;
import static com.brasshaven.generated.MobAnims.BogHierophant.SWARM;
import static com.brasshaven.generated.MobAnims.BogHierophant.SWEEP;
import static com.brasshaven.generated.MobAnims.BogHierophant.WISP;

/**
 * Le Hiérophante des tourbières (The Bog Hierophant), the rotting bishop of the Mire Stilt-City: a 5.9-block prelate on
 * two stilt legs bound in mangrove roots, a mantle of living moss, a crooked mitre, a lantern-crozier of black mangrove
 * wood and a cloud of marsh-flies. He holds court in the witch-queen's hall, 34 blocks over the swamp.
 * <p>A deliberately hard fight: 600 health, armour 12, poise 110, hits of 2 to 19. Three phases:
 * <ul>
 *     <li>Phase 1: <b>crozier sweep</b> (200 degrees), <b>lantern slam</b> (a line; the bog opens where the lantern
 *     lands), <b>lantern lure</b> (the swamp-fire marks you; 2.5 s later it bursts into a poison bloom where you stand:
 *     get away from your friends), <b>sinking mud</b> (circles of real, temporary mud open round the hall: they slow,
 *     then root whoever stays in them), <b>stilt stomp</b> (anti-hug), <b>stride</b> (a long-legged lunge) and, every
 *     28 s, his <b>leech brood</b> (silverfish, two at most, more in co-op).</li>
 *     <li>Phase 2 (a roar at 65%): eight bog lanterns kindle round the hall; faster, combos, <b>reap</b> (two sweeps),
 *     the <b>marsh-fly swarm</b> (a cloud that hunts you for 2 s) and the <b>will-o'-wisp</b>: he burns away into a
 *     marsh-light that flits from lantern to lantern, then rises behind his prey and strikes. The lure marks everyone.
 *     </li>
 *     <li>Phase 3 (at 30%): he kneels (invulnerable) and the swamp gas <b>kindles</b>; every 11 s rolling <b>fire
 *     lines</b> cross the hall (too tall to jump: cross through the gaps), after which he is spent for 2.5 s. Mud
 *     circles burst into flame when they close.</li>
 * </ul>
 * Every block he places (the mud, the lanterns) is temporary: restored when it expires, when the fight resets or the
 * arena empties, when he dies or is removed, and on the first tick after a reload.
 */
public class BogHierophant extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.6F;
    private static final float PHASE_THREE_AT = 0.3F;
    private static final double SWEEP_RANGE = 7.0;
    private static final double SWEEP_HALF = 100;
    private static final double MIRE_R = 3.0;
    private static final int MIRE_LIFE = 100;
    private static final double GAP_HALF = 1.8;
    private static final double LINE_HEIGHT = 3.0;
    private static final int LEECHES_EVERY = 560;
    private static final int FIRELINES_EVERY = 220;
    private static final int MAX_MUD = 400;
    private static final DustParticleOptions SWAMPFIRE = new DustParticleOptions(0xC4F460, 1.3F);
    private static final DustParticleOptions MUDDUST = new DustParticleOptions(0x5A4632, 1.6F);
    private static final DustParticleOptions FLIES = new DustParticleOptions(0x22221E, 0.8F);
    private static final DustParticleOptions BLOOM = new DustParticleOptions(0x7FB23C, 1.5F);
    private static final DustParticleOptions GAS = new DustParticleOptions(0x9FBF5A, 1.8F);

    private @Nullable Vec3 centre;
    private int radius = 16;
    /** Phase 3 has started (the swamp gas kindled). */
    private boolean kindled;
    private int guard;
    private int roarUntil = -1;
    private int leechTimer = 260;
    private int firelinesTimer;
    private int firePattern;
    private int spentUntil = -1;
    /** The will-o'-wisp: hidden and intangible while it flits between the lanterns. */
    private boolean wisping;
    private final List<Vec3> anchors = new ArrayList<>();
    private final List<Vec3> wispPath = new ArrayList<>();
    private @Nullable Vec3 wispStrike;
    /** Bog lanterns he placed (into air): removed when the fight ends. */
    private final Set<BlockPos> lanterns = new LinkedHashSet<>();
    private final Set<BlockPos> staleLanterns = new HashSet<>();
    /** Floor blocks turned to mud: the original state and the tick it is restored. */
    private final Map<BlockPos, BlockState> mudOrig = new HashMap<>();
    private final Map<BlockPos, Integer> mudUntil = new HashMap<>();
    private boolean staleMud;
    private final List<Vec3> spots = new ArrayList<>();
    private final Set<UUID> struck = new HashSet<>();

    public BogHierophant(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 12.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BogHierophant.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.GREEN;
    }

    @Override
    protected int roarAction() {
        return ROAR;
    }

    @Override
    protected int staggerAction() {
        return STAGGER;
    }

    @Override
    protected float maxPoise() {
        return 110.0F;
    }

    @Override
    protected float phaseTwoAt() {
        return 0.65F;
    }

    @Override
    protected double preferredRange() {
        return 5.0;
    }

    public boolean isKindled() {
        return kindled;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    // ------------------------------------------------------------------ arena memory

    @Override
    public void setArena(BlockPos c, int r, @Nullable BlockPos sealPos) {
        super.setArena(c, r, sealPos);
        this.centre = Vec3.atBottomCenterOf(c);
        this.radius = r;
        anchors.clear();
    }

    private Vec3 centre() {
        if (centre == null) {
            centre = position();
        }
        return centre;
    }

    /** Usable floor radius: the hall's 17.5 blocks, never more than the seal says. */
    private double reach() {
        return Math.min(16.0, radius + 1.0);
    }

    /** Eight lantern spots round the hall, between the posts (at radius 10, pulled in if blocked). */
    private List<Vec3> anchors(ServerLevel level) {
        if (anchors.isEmpty()) {
            Vec3 c = centre();
            for (int k = 0; k < 8; k++) {
                double a = Math.toRadians(k * 45);
                Vec3 best = null;
                for (double r = Math.min(10.0, reach() - 3); r >= 5.0; r -= 1.0) {
                    Vec3 p = c.add(Math.sin(a) * r, 0, -Math.cos(a) * r);
                    BlockPos bp = BlockPos.containing(p);
                    if (level.getBlockState(bp).isAir() && level.getBlockState(bp.above()).isAir()
                            && level.getBlockState(bp.below()).isFaceSturdy(level, bp.below(), Direction.UP)) {
                        best = Vec3.atBottomCenterOf(bp);
                        break;
                    }
                }
                anchors.add(best != null ? best : c.add(Math.sin(a) * 8, 0, -Math.cos(a) * 8));
            }
        }
        return anchors;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // crozier sweep: drawn back over his right shoulder (0.8 s, the arc traced in swamp-fire), swept over 200 degrees
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SWAMPFIRE);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.WITCH_AMBIENT, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.sweepBlow(level, 16.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) < 6.5 ? "reap" : "lure");
                    }
                })
                .build());
        // lantern slam: the crozier lifted high in both hands (1.0 s, the line marked in mud), brought down: the
        // lantern smashes 7 blocks ahead and the bog opens round it
        out.add(BossAttack.of("slam").anim(SLAM).timing(20, 3, 16).range(0, 9.0).cooldown(80).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 8.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(MUDDUST, p.x, p.y + 0.15, p.z, 1, 0.3, 0, 0.3, 0);
                        }
                        b.telegraphRing(level, b.ahead(7.0), 2.5, SWAMPFIRE);
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_BLINDNESS, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    b.hitLine(level, 8.0, 1.4, 19.0F, 0.6);
                    Vec3 tip = b.ahead(7.0);
                    level.sendParticles(MUDDUST, tip.x, tip.y + 0.4, tip.z, 40, 1.4, 0.3, 1.4, 0.05);
                    level.sendParticles(SWAMPFIRE, tip.x, tip.y + 0.6, tip.z, 20, 0.8, 0.5, 0.8, 0.05);
                    level.playSound(null, tip.x, tip.y, tip.z, SoundEvents.MUD_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 2.5F, 0.6F);
                    b.addEffect(h.mireCircle(h.clampToArena(tip), 2.5, MIRE_LIFE, 0));
                })
                .build());
        // lantern lure: the lantern held out toward his prey (0.9 s); the swamp-fire leaps to them and marks them
        // (phase 2: every player); 2.5 s later the mark blooms into poison where they stand
        out.add(BossAttack.of("lure").anim(LURE).timing(18, 10, 14).range(3.0, 22.0).cooldown(160).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0 && t != null) {
                        Vec3 from = b.ahead(2.0).add(0, 3.0, 0);
                        Vec3 to = t.position().add(0, 1.0, 0);
                        double len = from.distanceTo(to);
                        for (double d = 0; d < len; d += 1.2) {
                            Vec3 p = from.lerp(to, d / Math.max(0.01, len));
                            level.sendParticles(SWAMPFIRE, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.LANTERN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    List<LivingEntity> marked = new ArrayList<>();
                    if (b.phase() == 2) {
                        for (LivingEntity e : b.victims(level, h.centre(), h.reach() + 4)) {
                            if (e instanceof Player && marked.size() < 4) {
                                marked.add(e);
                            }
                        }
                    }
                    if (marked.isEmpty() && t != null) {
                        marked.add(t);
                    }
                    for (LivingEntity e : marked) {
                        b.addEffect(h.lureMark(e, 50, 12, 3.0, 12.0F));
                    }
                })
                .build());
        // sinking mud: the crozier planted, his claw drawn toward the floor (1.0 s; rings of mud dust close on the
        // target and on the others); the bog opens in circles of real mud that slow, then root
        out.add(BossAttack.of("mire").anim(MIRE).timing(20, 30, 14).range(0, 22.0).cooldown(200).weight(8).track(false)
                .start((b, level, t, tick) -> {
                    spots.clear();
                    level.playSound(null, b, SoundEvents.MUD_STEP, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    if (tick <= 12) {
                        h.pickMireSpots(level, t);
                    }
                    if (tick % 3 == 0) {
                        for (Vec3 p : spots) {
                            b.telegraphRing(level, p, MIRE_R, tick > 12 ? SWAMPFIRE : MUDDUST);
                            level.sendParticles(ParticleTypes.BUBBLE_POP, p.x, p.y + 0.2, p.z, 3, 1.2, 0, 1.2, 0);
                        }
                    }
                    if (tick == 10) {
                        level.playSound(null, b, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    level.playSound(null, b, SoundEvents.MUD_PLACE, SoundSource.HOSTILE, 3.0F, 0.4F);
                    for (Vec3 p : spots) {
                        b.addEffect(h.mireCircle(p, MIRE_R, MIRE_LIFE, 8.0F));
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 10 == 0) {
                        level.sendParticles(MUDDUST, b.getX(), b.getY() + 0.2, b.getZ(), 10, 1.2, 0.1, 1.2, 0);
                    }
                })
                .build());
        // stilt stomp: a stilt raised high (0.6 s, a ring of mud at his feet), stamped down: anti-hug.
        // Phase 2: a ring of mud rolls out (jump it)
        out.add(BossAttack.of("stomp").anim(STOMP).timing(12, 3, 12).range(0, 4.5).cooldown(70).weight(9).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.5, MUDDUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.5, 12.0F, 1.3, 0.3);
                    for (LivingEntity e : b.victims(level, b.position(), 5.0)) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), b);
                    }
                    if (b.phase() == 2) {
                        b.addEffect(WayfarerBoss.wave(b.position(), 9, 0.5, 8.0F, MUDDUST));
                    }
                    level.sendParticles(MUDDUST, b.getX(), b.getY() + 0.3, b.getZ(), 50, 2.2, 0.2, 2.2, 0.05);
                    level.playSound(null, b, SoundEvents.MUD_FALL, SoundSource.HOSTILE, 3.0F, 0.4F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0F, 1.4F);
                })
                .build());
        // stride: he leans in on his long legs (0.7 s, a line of mud dust), then strides 10 blocks through you
        out.add(BossAttack.of("stride").anim(STRIDE).timing(14, 10, 12).range(6.0, 18.0).cooldown(110).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 1.5; d <= 10.0; d += 1.0) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(MUDDUST, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                    if (tick == 4) {
                        level.playSound(null, b, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.strideStep(level, 1.0, 15.0F);
                    }
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (b.phase() == 2 && t != null && b.distanceTo(t) < 7.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "sweep");
                    }
                })
                .build());
        // leech brood: never rolled; bossTick chains it every 28 s while there is room. He shudders (0.8 s, rings of
        // mud where they will drop), then shakes the leeches off his robe
        out.add(BossAttack.of("leeches").anim(LEECHES).timing(16, 4, 14).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.pickLeechSpots(level);
                    }
                    level.playSound(null, b, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (Vec3 p : spots) {
                            b.telegraphRing(level, p, 1.0, MUDDUST);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.dropLeeches(level);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // reap: forehand sweep at the impact, a turn toward the target, the arc re-drawn, backhand 0.6 s later
        out.add(BossAttack.of("reap").anim(REAP).phaseTwo().timing(16, 16, 14).range(0, 7.5).cooldown(140).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SWAMPFIRE);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    if (tick == 0 || tick == 12) {
                        h.sweepBlow(level, 15.0F);
                    }
                    if (tick == 3 && t != null) {
                        h.turnToward(t, 35.0F);
                    }
                    if (tick > 3 && tick < 12 && tick % 2 == 0) {
                        b.telegraphArc(level, SWEEP_RANGE, SWEEP_HALF, SWAMPFIRE);
                    }
                })
                .build());
        // marsh-fly swarm: arms spread, jaw open (0.9 s, the flies boil round him); the swarm pours out and hunts
        // the target for 2 s, a little slower than a sprint
        out.add(BossAttack.of("swarm").anim(SWARM).phaseTwo().timing(18, 40, 14).range(0, 16.0).cooldown(220).weight(7)
                .track(false)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(FLIES, b.getX(), b.getY() + 4.0, b.getZ(), 6, 1.6, 1.0, 1.6, 0.05);
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BEE_LOOP_AGGRESSIVE, SoundSource.HOSTILE, 2.5F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h && t != null) {
                        b.addEffect(h.flySwarm(t, 40, h.kindled ? 0.27 : 0.23));
                        if (b.scaledPlayers() >= 3) {           // a second swarm in big groups
                            for (LivingEntity e : b.victims(level, h.centre(), h.reach() + 4)) {
                                if (e instanceof Player && e != t) {
                                    b.addEffect(h.flySwarm(e, 40, 0.21));
                                    break;
                                }
                            }
                        }
                    }
                })
                .build());
        // will-o'-wisp: he sags and burns away into a marsh-light (0.9 s); hidden and untouchable, the wisp flits to
        // three lanterns round the hall; then a ring of swamp-fire and a lantern's chime mark the spot behind his prey
        // (0.8 s), he rises there (0.4 s) and strikes (17, 120 degrees, 4.5 out)
        out.add(BossAttack.of("wisp").anim(WISP).phaseTwo().timing(18, 70, 16).range(0, 30.0).cooldown(320).weight(7)
                .track(false)
                .start((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(SWAMPFIRE, b.getX(), b.getY() + 2.0 + tick * 0.05, b.getZ(), 4, 0.7, 1.4, 0.7, 0.02);
                    level.sendParticles(ParticleTypes.SMOKE, b.getX(), b.getY() + 2.0, b.getZ(), 2, 0.7, 1.4, 0.7, 0.01);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.startWisp(level);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.wispStep(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.endWisp();
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // kindle: he kneels, the lantern lifted (1.5 s, invulnerable; the swamp gas bubbles up over the whole floor),
        // then dashes it on the floor: the gas ignites in a ring of fire (jump it)
        out.add(BossAttack.of("kindle").anim(KINDLE).phaseTwo().timing(30, 20, 20).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    guard = 52;
                    level.playSound(null, b, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 3.0F, 0.4F);
                })
                .windup((b, level, t, tick) -> {
                    if (!(b instanceof BogHierophant h)) {
                        return;
                    }
                    Vec3 c = h.centre();
                    double r = h.reach();
                    level.sendParticles(GAS, c.x, c.y + 0.4, c.z, 14, r * 0.5, 0.2, r * 0.5, 0.01);
                    level.sendParticles(ParticleTypes.BUBBLE_POP, c.x, c.y + 0.2, c.z, 8, r * 0.5, 0, r * 0.5, 0);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 2.0 + tick * 0.4, SWAMPFIRE);
                    }
                    if (tick % 10 == 0) {
                        level.playSound(null, b, SoundEvents.BREWING_STAND_BREW, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.kindle(level);
                    }
                })
                .build());
        // fire lines: the lantern swung round his head (1.0 s, the plan drawn on the floor), flung down: lines of
        // burning swamp gas roll across the hall (too tall to jump: cross through the gaps). Then he is spent for 2.5 s
        out.add(BossAttack.of("firelines").anim(FIRELINES).phaseTwo().timing(20, 50, 14).range(999, 999).cooldown(0)
                .weight(0).track(false)
                .start((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 3.0F, 0.5F);
                    if (b instanceof BogHierophant h) {
                        h.planFirelines(level, t);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                    level.sendParticles(ParticleTypes.FLAME, b.getX(), b.getY() + 5.5, b.getZ(), 3, 0.8, 0.3, 0.8, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof BogHierophant h) {
                        h.spentUntil = h.tickCount + 50;
                        level.sendParticles(ParticleTypes.LARGE_SMOKE, b.getX(), b.getY() + 3, b.getZ(), 20, 0.8, 1.2, 0.8, 0.02);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private void sweepBlow(ServerLevel level, float damage) {
        for (LivingEntity e : arcVictims(this, level, SWEEP_RANGE, SWEEP_HALF)) {
            strike(level, e, damage, 1.3, 0.25);
        }
        for (double a = -SWEEP_HALF; a <= SWEEP_HALF; a += 10) {
            Vec3 p = position().add(rotate(forward(), a).scale(SWEEP_RANGE - 1.5));
            level.sendParticles(SWAMPFIRE, p.x, p.y + 1.4, p.z, 3, 0.2, 0.3, 0.2, 0.02);
            level.sendParticles(MUDDUST, p.x, p.y + 0.4, p.z, 2, 0.2, 0.2, 0.2, 0.02);
        }
        Vec3 c = ahead(3.5);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.5, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    private static List<LivingEntity> arcVictims(WayfarerBoss b, ServerLevel level, double range, double halfAngle) {
        Vec3 fwd = b.forward();
        double cos = Math.cos(Math.toRadians(halfAngle));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.victims(level, b.position(), range + 1)) {
            Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= range + e.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cos)) {
                out.add(e);
            }
        }
        return out;
    }

    private void strideStep(ServerLevel level, double speed, float damage) {
        Vec3 f = forward().scale(speed);
        setDeltaMovement(f.x, getDeltaMovement().y, f.z);
        hurtMarked = true;
        level.sendParticles(MUDDUST, getX(), getY() + 0.2, getZ(), 6, 0.6, 0.1, 0.6, 0.02);
        if (tickCount % 3 == 0) {
            level.playSound(null, this, SoundEvents.MUD_STEP, SoundSource.HOSTILE, 2.0F, 0.6F);
        }
        for (LivingEntity e : victims(level, position(), 2.8)) {
            if (flatDist(e.position(), position()) <= 2.2 + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, 1.2, 0.35);
            }
        }
        if (horizontalCollision) {
            setDeltaMovement(0, getDeltaMovement().y, 0);
        }
    }

    private void turnToward(LivingEntity target, float maxTurn) {
        double dx = target.getX() - getX();
        double dz = target.getZ() - getZ();
        float yaw = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        snapFacing(Mth.approachDegrees(getYRot(), yaw, maxTurn));
    }

    private Vec3 clampToArena(Vec3 p) {
        Vec3 c = centre();
        Vec3 off = p.subtract(c).multiply(1, 0, 1);
        double max = Math.max(3.0, reach() - 2.0);
        if (off.length() > max) {
            off = off.normalize().scale(max);
        }
        return new Vec3(c.x + off.x, c.y, c.z + off.z);
    }

    private Vec3 randomSpot() {
        double a = getRandom().nextDouble() * Math.PI * 2;
        double r = 2 + getRandom().nextDouble() * Math.max(3, reach() - 4);
        return centre().add(Math.cos(a) * r, 0, Math.sin(a) * r);
    }

    /** The lure's mark: a ring of swamp-fire follows {@code e}, locks {@code lock} ticks before the bloom, then blooms. */
    private Effect lureMark(LivingEntity e, int life, int lock, double r, float damage) {
        int[] t = {0};
        Vec3[] at = {null};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < life - lock) {
                if (!e.isAlive()) {
                    return true;
                }
                if (k % 2 == 0) {
                    boss.telegraphRing(level, new Vec3(e.getX(), floorY(e), e.getZ()), r, BLOOM);
                    level.sendParticles(SWAMPFIRE, e.getX(), e.getY() + e.getBbHeight() + 0.4, e.getZ(), 2, 0.2, 0.1, 0.2, 0.01);
                }
                if (k % 10 == 0) {
                    level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 1.0F, 1.6F);
                }
                return false;
            }
            if (at[0] == null) {
                at[0] = new Vec3(e.getX(), floorY(e), e.getZ());
            }
            Vec3 p = at[0];
            if (k < life) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, p, r, SWAMPFIRE);
                }
                return false;
            }
            if (k == life) {
                level.sendParticles(BLOOM, p.x, p.y + 1.0, p.z, 60, r * 0.4, 0.8, r * 0.4, 0.05);
                level.sendParticles(ParticleTypes.SPORE_BLOSSOM_AIR, p.x, p.y + 1.0, p.z, 40, r * 0.4, 0.8, r * 0.4, 0.02);
                level.playSound(null, p.x, p.y, p.z, SoundEvents.PUFFER_FISH_BLOW_UP, SoundSource.HOSTILE, 2.0F, 0.5F);
                for (LivingEntity v : boss.victims(level, p, r + 1)) {
                    if (flatDist(v.position(), p) <= r + v.getBbWidth() / 2 && Math.abs(v.getY() - p.y) < 2.5) {
                        boss.strike(level, v, damage, 0.4, 0.3);
                        v.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1), boss);
                    }
                }
                return false;
            }
            // the bloom lingers 2 s: 2 and a little poison every half second
            if (k % 3 == 0) {
                level.sendParticles(BLOOM, p.x, p.y + 0.6, p.z, 4, r * 0.4, 0.3, r * 0.4, 0.005);
            }
            if (k % 10 == 0) {
                for (LivingEntity v : boss.victims(level, p, r)) {
                    if (flatDist(v.position(), p) <= r * 0.8 && Math.abs(v.getY() - p.y) < 2.0
                            && v.hurtServer(level, boss.damageSources().mobAttack(boss), 2.0F)) {
                        v.addEffect(new MobEffectInstance(MobEffects.POISON, 40, 0), boss);
                    }
                }
            }
            return k >= life + 40;
        };
    }

    private double floorY(LivingEntity e) {
        return Math.abs(e.getY() - centre().y) < 4.0 ? centre().y : e.getY();
    }

    /** Mire spots: on the target (it follows during the first 12 wind-up ticks), on every other player, strays. */
    private void pickMireSpots(ServerLevel level, @Nullable LivingEntity target) {
        spots.clear();
        int want = kindled ? 5 : phase() == 2 ? 4 : 3;
        if (target != null) {
            spots.add(clampToArena(target.position()));
        }
        for (LivingEntity e : victims(level, centre(), reach() + 4)) {
            if (e instanceof Player && e != target && spots.size() < want) {
                spots.add(clampToArena(e.position()));
            }
        }
        long seed = getUUID().getLeastSignificantBits() + tickCount / 40;
        java.util.Random r = new java.util.Random(seed);
        int tries = 0;
        while (spots.size() < want && tries++ < 30) {
            double a = r.nextDouble() * Math.PI * 2;
            double d = 3 + r.nextDouble() * Math.max(3, reach() - 5);
            Vec3 p = centre().add(Math.cos(a) * d, 0, Math.sin(a) * d);
            boolean ok = true;
            for (Vec3 s : spots) {
                ok &= flatDist(s, p) >= MIRE_R * 2;
            }
            if (ok) {
                spots.add(p);
            }
        }
    }

    /**
     * A circle of sinking mud: the floor blocks under it turn to real mud for {@code life} ticks (restored after);
     * whoever stands in it is slowed, after a second rooted (and sinks, 2 a second). In phase 3 the gas trapped in it
     * bursts into flame when it closes.
     */
    private Effect mireCircle(Vec3 pos, double r, int life, float openDamage) {
        int[] t = {0};
        Map<UUID, Integer> inside = new HashMap<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (k == 0) {
                if (boss instanceof BogHierophant h) {
                    h.mudOver(level, pos, r, life);
                }
                level.sendParticles(MUDDUST, pos.x, pos.y + 0.3, pos.z, 30, r * 0.5, 0.2, r * 0.5, 0.05);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.MUD_BREAK, SoundSource.HOSTILE, 1.5F, 0.6F);
                if (openDamage > 0) {
                    for (LivingEntity e : boss.victims(level, pos, r + 1)) {
                        if (flatDist(e.position(), pos) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.0) {
                            boss.strike(level, e, openDamage, 0.0, 0.1);
                        }
                    }
                }
            }
            if (k % 4 == 0) {
                level.sendParticles(ParticleTypes.BUBBLE_POP, pos.x, pos.y + 0.1, pos.z, 2, r * 0.5, 0, r * 0.5, 0);
                level.sendParticles(MUDDUST, pos.x, pos.y + 0.1, pos.z, 2, r * 0.5, 0, r * 0.5, 0);
            }
            if (k % 5 == 0) {
                Set<UUID> now = new HashSet<>();
                for (LivingEntity e : boss.victims(level, pos, r + 1)) {
                    if (!(e instanceof Player) || flatDist(e.position(), pos) > r || Math.abs(e.getY() - pos.y) > 1.5) {
                        continue;
                    }
                    now.add(e.getUUID());
                    int in = inside.merge(e.getUUID(), 5, Integer::sum);
                    boolean rooted = in >= 20;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 12, rooted ? 6 : 2), boss);
                    if (rooted) {
                        e.setDeltaMovement(0, Math.min(0, e.getDeltaMovement().y), 0);
                        e.hurtMarked = true;
                        if (in % 20 == 0) {
                            e.hurtServer(level, boss.damageSources().mobAttack(boss), 2.0F);
                            level.sendParticles(MUDDUST, e.getX(), e.getY() + 0.3, e.getZ(), 8, 0.3, 0.2, 0.3, 0.02);
                        }
                    }
                }
                inside.keySet().retainAll(now);
            }
            if (k >= life) {
                if (boss instanceof BogHierophant h) {
                    if (h.kindled) {                     // the trapped gas flares as the bog closes
                        level.sendParticles(ParticleTypes.FLAME, pos.x, pos.y + 0.6, pos.z, 40, r * 0.45, 0.5, r * 0.45, 0.05);
                        level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.5F, 0.7F);
                        for (LivingEntity e : boss.victims(level, pos, r + 1)) {
                            if (flatDist(e.position(), pos) <= r + e.getBbWidth() / 2 && Math.abs(e.getY() - pos.y) < 2.0) {
                                boss.strike(level, e, 8.0F, 0.2, 0.4);
                                e.igniteForSeconds(3.0F);
                            }
                        }
                    }
                    h.restoreMud(level, false);
                }
                return true;
            }
            return false;
        };
    }

    /** Turns the floor under a circle to mud (only plain full blocks with air over them), remembering each block. */
    private void mudOver(ServerLevel level, Vec3 pos, double r, int life) {
        int fy = BlockPos.containing(pos).getY() - 1;
        int cx = Mth.floor(pos.x);
        int cz = Mth.floor(pos.z);
        int ir = (int) Math.ceil(r);
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -ir; dx <= ir; dx++) {
            for (int dz = -ir; dz <= ir; dz++) {
                if (mudOrig.size() >= MAX_MUD) {
                    return;
                }
                if (Math.hypot(cx + 0.5 + dx - pos.x, cz + 0.5 + dz - pos.z) > r) {
                    continue;
                }
                p.set(cx + dx, fy, cz + dz);
                if (flatDist(Vec3.atCenterOf(p), centre()) > reach() + 0.5) {
                    continue;
                }
                BlockPos at = p.immutable();
                if (mudOrig.containsKey(at)) {
                    mudUntil.put(at, Math.max(mudUntil.getOrDefault(at, 0), tickCount + life));
                    continue;
                }
                BlockState s = level.getBlockState(at);
                if (s.isAir() || s.is(Blocks.MUD) || s.hasBlockEntity() || !s.isCollisionShapeFullBlock(level, at)
                        || !level.getBlockState(at.above()).isAir()) {
                    continue;
                }
                mudOrig.put(at, s);
                mudUntil.put(at, tickCount + life);
                level.setBlock(at, Blocks.MUD.defaultBlockState(), 3);
            }
        }
    }

    /** Restores mud blocks whose time is up (or all of them); only blocks that are still mud are put back. */
    private void restoreMud(ServerLevel level, boolean all) {
        if (mudOrig.isEmpty()) {
            return;
        }
        List<BlockPos> done = new ArrayList<>();
        for (Map.Entry<BlockPos, BlockState> en : mudOrig.entrySet()) {
            BlockPos p = en.getKey();
            if (!all && mudUntil.getOrDefault(p, 0) > tickCount) {
                continue;
            }
            if (level.isLoaded(p) && level.getBlockState(p).is(Blocks.MUD)) {
                level.setBlock(p, en.getValue(), 3);
            }
            done.add(p);
        }
        for (BlockPos p : done) {
            mudOrig.remove(p);
            mudUntil.remove(p);
        }
    }

    /** The bog lanterns of phase 2: placed into air on the eight wisp anchors. */
    private void placeLanterns(ServerLevel level) {
        for (Vec3 a : anchors(level)) {
            BlockPos p = BlockPos.containing(a);
            if (lanterns.contains(p)) {
                continue;
            }
            if (level.getBlockState(p).isAir() && level.getBlockState(p.below()).isFaceSturdy(level, p.below(), Direction.UP)) {
                level.setBlock(p, Blocks.LANTERN.defaultBlockState(), 3);
                lanterns.add(p);
                level.sendParticles(SWAMPFIRE, a.x, a.y + 0.6, a.z, 12, 0.2, 0.3, 0.2, 0.02);
            }
        }
        level.playSound(null, this, SoundEvents.LANTERN_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void removeLanterns(ServerLevel level, Set<BlockPos> set) {
        for (BlockPos p : set) {
            if (level.isLoaded(p) && level.getBlockState(p).is(Blocks.LANTERN)) {
                level.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
            }
        }
        set.clear();
    }

    private int minions(ServerLevel level) {
        return level.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(centre())).inflate(radius + 12, 12, radius + 12),
                e -> e.isAlive() && e.entityTags().contains(MINION_TAG)).size();
    }

    private int leechCap() {
        return scaledCount(phase() == 2 ? 3 : 2);
    }

    private void pickLeechSpots(ServerLevel level) {
        spots.clear();
        int n = Math.min(Math.max(0, leechCap() - minions(level)), scaledCount(2));
        double base = getRandom().nextDouble() * Math.PI * 2;
        for (int i = 0; i < n; i++) {
            double a = base + Math.PI * 2 * i / Math.max(1, n);
            spots.add(clampToArena(position().add(Math.cos(a) * 3.5, 0, Math.sin(a) * 3.5)));
        }
    }

    private void dropLeeches(ServerLevel level) {
        level.playSound(null, this, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 2.5F, 0.5F);
        for (Vec3 p : spots) {
            Mob m = net.minecraft.world.entity.EntityTypes.SILVERFISH.create(level, EntitySpawnReason.MOB_SUMMONED);
            if (m == null) {
                continue;
            }
            m.snapTo(p.x, p.y, p.z, getYRot(), 0);
            m.addTag(MINION_TAG);
            m.setTarget(getTarget());
            level.addFreshEntity(m);
            level.sendParticles(MUDDUST, p.x, p.y + 0.4, p.z, 20, 0.3, 0.3, 0.3, 0.05);
        }
        spots.clear();
    }

    /** The marsh-fly swarm: a cloud that drifts after {@code target}; 3 and a little poison every half second. */
    private Effect flySwarm(LivingEntity target, int life, double speed) {
        int[] t = {0};
        Vec3[] at = {position().add(forward().scale(1.5)).add(0, 2.5, 0)};
        Set<UUID> poisoned = new HashSet<>();
        return (boss, level) -> {
            int k = t[0]++;
            if (target.isAlive()) {
                Vec3 goal = target.position().add(0, 1.0, 0);
                Vec3 to = goal.subtract(at[0]);
                if (to.length() > 0.1) {
                    at[0] = at[0].add(to.normalize().scale(Math.min(speed, to.length())));
                }
            }
            Vec3 p = at[0];
            level.sendParticles(FLIES, p.x, p.y, p.z, 12, 0.9, 0.7, 0.9, 0.06);
            if (k % 3 == 0) {
                level.sendParticles(ParticleTypes.FIREFLY, p.x, p.y, p.z, 1, 0.6, 0.5, 0.6, 0);
            }
            if (k % 8 == 0) {
                level.playSound(null, p.x, p.y, p.z, SoundEvents.BEE_LOOP_AGGRESSIVE, SoundSource.HOSTILE, 1.4F, 0.6F);
            }
            if (k % 10 == 5) {
                for (LivingEntity e : boss.victims(level, p, 2.6)) {
                    if (e.position().add(0, 1.0, 0).distanceTo(p) <= 2.0
                            && e.hurtServer(level, boss.damageSources().mobAttack(boss), 3.0F) && poisoned.add(e.getUUID())) {
                        e.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), boss);
                        e.addEffect(new MobEffectInstance(MobEffects.HUNGER, 100, 1), boss);
                    }
                }
            }
            return k >= life;
        };
    }

    // ------------------------------------------------------------------ the will-o'-wisp

    private void startWisp(ServerLevel level) {
        wisping = true;
        setInvisible(true);
        wispStrike = null;
        wispPath.clear();
        List<Vec3> pool = new ArrayList<>(anchors(level));
        java.util.Collections.shuffle(pool, new java.util.Random(getRandom().nextLong()));
        for (int i = 0; i < 3 && i < pool.size(); i++) {
            wispPath.add(pool.get(i));
        }
        level.sendParticles(SWAMPFIRE, getX(), getY() + 2, getZ(), 50, 0.8, 1.5, 0.8, 0.05);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 2, getZ(), 20, 0.6, 1.2, 0.6, 0.02);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 2.0F, 0.5F);
    }

    /**
     * One tick of the wisp: hops to a lantern at ticks 0, 15 and 30 (the lantern flares), locks the spot behind the
     * target at 44 (a ring and a chime there), rises there at 52, strikes at 60.
     */
    private void wispStep(ServerLevel level, int tick) {
        LivingEntity target = getTarget();
        if (tick < 44) {
            int hop = tick / 15;
            if (tick % 15 == 0 && hop < wispPath.size()) {
                Vec3 a = wispPath.get(hop);
                teleportTo(a.x, a.y, a.z);
                level.sendParticles(SWAMPFIRE, a.x, a.y + 1.0, a.z, 30, 0.3, 0.6, 0.3, 0.04);
                level.sendParticles(ParticleTypes.FLAME, a.x, a.y + 0.8, a.z, 10, 0.2, 0.3, 0.2, 0.02);
                level.playSound(null, a.x, a.y, a.z, SoundEvents.LANTERN_PLACE, SoundSource.HOSTILE, 2.5F, 0.7F + hop * 0.15F);
            }
            // the wisp itself: a mote of swamp-fire bobbing over the lantern
            level.sendParticles(SWAMPFIRE, getX(), getY() + 1.6 + 0.3 * Math.sin(tick * 0.5), getZ(), 3, 0.15, 0.15, 0.15, 0.01);
            level.sendParticles(FLIES, getX(), getY() + 1.6, getZ(), 2, 0.6, 0.4, 0.6, 0.02);
            return;
        }
        if (tick == 44) {
            Vec3 spot;
            if (target != null && target.isAlive()) {
                Vec3 look = Vec3.directionFromRotation(0, target.getYRot()).multiply(1, 0, 1);
                spot = null;
                for (int k = 0; k < 9 && spot == null; k++) {       // behind it, else a little round to its side
                    double turn = (k + 1) / 2 * 30.0 * (k % 2 == 0 ? 1 : -1);
                    Vec3 p = clampToArena(target.position().subtract(rotate(look, turn).scale(2.6)));
                    if (clear(level, p)) {
                        spot = p;
                    }
                }
                if (spot == null) {
                    spot = clampToArena(target.position());
                }
            } else {
                spot = clampToArena(position());
            }
            wispStrike = spot;
            level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
            level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.LANTERN_PLACE, SoundSource.HOSTILE, 3.0F, 0.5F);
        }
        Vec3 spot = wispStrike != null ? wispStrike : position();
        if (tick < 60 && tick % 2 == 0) {
            telegraphRing(level, spot, 1.4, SWAMPFIRE);
            telegraphArcAt(level, spot, target, 4.5, 60);
        }
        if (tick == 52) {
            teleportTo(spot.x, spot.y, spot.z);
            if (target != null) {
                double dx = target.getX() - spot.x;
                double dz = target.getZ() - spot.z;
                snapFacing((float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F);
            }
            setInvisible(false);
            wisping = false;
            level.sendParticles(SWAMPFIRE, spot.x, spot.y + 2, spot.z, 60, 0.8, 1.6, 0.8, 0.05);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, spot.x, spot.y + 2, spot.z, 20, 0.6, 1.4, 0.6, 0.02);
            level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
        if (tick == 60) {
            for (LivingEntity e : arcVictims(this, level, 4.5, 60)) {
                strike(level, e, 17.0F, 1.2, 0.3);
                e.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), this);
            }
            Vec3 c = ahead(2.5);
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x, c.y + 1.5, c.z, 1, 0, 0, 0, 0);
            level.sendParticles(SWAMPFIRE, c.x, c.y + 1.4, c.z, 20, 1.2, 0.4, 1.2, 0.02);
            level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
        }
    }

    /** Room for him to stand at {@code p}: three blocks of air over a sturdy floor. */
    private static boolean clear(ServerLevel level, Vec3 p) {
        BlockPos b = BlockPos.containing(p);
        for (int y = 0; y < 3; y++) {
            if (!level.getBlockState(b.above(y)).getCollisionShape(level, b.above(y)).isEmpty()) {
                return false;
            }
        }
        return level.getBlockState(b.below()).isFaceSturdy(level, b.below(), Direction.UP);
    }

    /** The arc he will strike from {@code from} toward the target, traced on the floor before he rises. */
    private void telegraphArcAt(ServerLevel level, Vec3 from, @Nullable LivingEntity target, double range, double half) {
        Vec3 dir = target != null ? target.position().subtract(from).multiply(1, 0, 1) : forward();
        if (dir.lengthSqr() < 1.0E-4) {
            dir = forward();
        }
        dir = dir.normalize();
        for (double a = -half; a <= half; a += 15) {
            Vec3 p = from.add(rotate(dir, a).scale(range));
            level.sendParticles(SWAMPFIRE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    private void endWisp() {
        wisping = false;
        wispStrike = null;
        setInvisible(false);
    }

    // ------------------------------------------------------------------ phase 3: the swamp gas burns

    private void kindle(ServerLevel level) {
        kindled = true;
        firelinesTimer = 100;
        Vec3 c = position();
        addEffect(WayfarerBoss.wave(c, 14, 0.55, 12.0F, ParticleTypes.FLAME));
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("bog_hierophant_kindled"), 0.12,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 h = centre();
        level.sendParticles(ParticleTypes.FLAME, h.x, h.y + 0.5, h.z, 200, reach() * 0.5, 0.3, reach() * 0.5, 0.05);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, h.x, h.y + 1.5, h.z, 60, reach() * 0.5, 0.6, reach() * 0.5, 0.02);
        level.playSound(null, this, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.GHAST_SHOOT, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /**
     * Plans the next fire lines, the patterns in turn: three parallel lines from one side (gaps shifting), two lines
     * at right angles, and a ring closing in from the walls with two gaps.
     */
    private void planFirelines(ServerLevel level, @Nullable LivingEntity target) {
        int pattern = firePattern++ % 3;
        Vec3 dir = forward();
        if (target != null) {
            Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
            if (to.lengthSqr() > 1.0E-3) {
                dir = to.normalize();
            }
        }
        double lat = target != null ? target.position().subtract(centre()).dot(new Vec3(-dir.z, 0, dir.x)) : 0;
        int warn = 20;
        switch (pattern) {
            case 0 -> {
                double g = Mth.clamp(lat, -reach() + 3, reach() - 3);
                for (int i = 0; i < 3; i++) {
                    List<Double> gaps = new ArrayList<>();
                    gaps.add(g);
                    if (scaledPlayers() >= 2) {
                        gaps.add(clampLat(g + (getRandom().nextBoolean() ? 8 : -8)));
                    }
                    addEffect(fireLine(dir, gaps, warn + i * 16, 0.5, 12.0F));
                    g = clampLat(g + (getRandom().nextBoolean() ? 1 : -1) * (5 + getRandom().nextDouble() * 3));
                }
            }
            case 1 -> {
                addEffect(fireLine(dir, pickGaps(2, lat), warn, 0.5, 12.0F));
                Vec3 across = rotate(dir, getRandom().nextBoolean() ? 90 : -90);
                double lat2 = target != null ? target.position().subtract(centre()).dot(new Vec3(-across.z, 0, across.x)) : 0;
                addEffect(fireLine(across, pickGaps(2, lat2), warn + 24, 0.5, 12.0F));
            }
            default -> {
                double a0 = getRandom().nextDouble() * 360;
                addEffect(fireRing(new double[] {a0, a0 + 150 + getRandom().nextDouble() * 60}, warn, 0.32, 12.0F));
            }
        }
    }

    private double clampLat(double g) {
        double m = reach() - 3;
        return Mth.clamp(g, -m, m);
    }

    /** {@code n} gap centres across a line, at least 5 apart; the first within 7 blocks of {@code lat}. */
    private List<Double> pickGaps(int n, double lat) {
        List<Double> out = new ArrayList<>();
        out.add(clampLat(lat + (getRandom().nextDouble() * 2 - 1) * 7));
        for (int tries = 0; out.size() < n && tries < 40; tries++) {
            double g = clampLat((getRandom().nextDouble() * 2 - 1) * reach());
            boolean ok = true;
            for (double o : out) {
                ok &= Math.abs(o - g) >= 5.0;
            }
            if (ok) {
                out.add(g);
            }
        }
        return out;
    }

    private static boolean inGap(double lat, List<Double> gaps) {
        for (double g : gaps) {
            if (Math.abs(lat - g) <= GAP_HALF) {
                return true;
            }
        }
        return false;
    }

    /**
     * A line of burning swamp gas: after {@code warn} ticks (its start line and gaps drawn on the floor) it rolls
     * across the hall along {@code dir}; whoever it meets outside the gaps takes {@code damage} once and burns.
     */
    private Effect fireLine(Vec3 dir, List<Double> gaps, int warn, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        int[] t = {0};
        double reach = reach();
        Vec3 c = centre();
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    for (double lat = -reach; lat <= reach; lat += 1.0) {
                        double span = Math.sqrt(Math.max(0, reach * reach - lat * lat));
                        if (span <= 0 || inGap(lat, gaps)) {
                            continue;
                        }
                        Vec3 p = c.add(side.scale(lat)).add(dir.scale(-span));
                        level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
                    }
                    for (double g : gaps) {
                        for (double edge : new double[] {g - GAP_HALF, g + GAP_HALF}) {
                            double span = Math.sqrt(Math.max(0, reach * reach - edge * edge));
                            for (double s = -span; s <= span; s += 1.5) {
                                Vec3 p = c.add(side.scale(edge)).add(dir.scale(s));
                                level.sendParticles(SWAMPFIRE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                }
                return false;
            }
            double s = -reach + (k - warn) * speed;
            double span = Math.sqrt(Math.max(0, reach * reach - s * s));
            for (double lat = -span; lat <= span; lat += 0.9) {
                if (inGap(lat, gaps)) {
                    continue;
                }
                Vec3 p = c.add(side.scale(lat)).add(dir.scale(s));
                level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.6, p.z, 2, 0.2, 0.6, 0.2, 0.01);
                if (((int) Math.floor(lat)) % 2 == 0) {
                    level.sendParticles(GAS, p.x, p.y + 1.8, p.z, 1, 0.2, 0.5, 0.2, 0);
                    level.sendParticles(ParticleTypes.SMOKE, p.x, p.y + 2.6, p.z, 1, 0.2, 0.2, 0.2, 0.01);
                }
            }
            if (k % 6 == 0) {
                Vec3 m = c.add(dir.scale(s));
                level.playSound(null, m.x, m.y, m.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 2.5F, 0.6F);
            }
            for (LivingEntity e : boss.victims(level, c, reach + 2)) {
                Vec3 rel = e.position().subtract(c).multiply(1, 0, 1);
                if (Math.abs(rel.dot(dir) - s) <= 0.9 && !inGap(rel.dot(side), gaps) && e.getY() - c.y < LINE_HEIGHT
                        && hit.add(e.getUUID())) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                        e.igniteForSeconds(4.0F);
                        e.push(dir.x * 0.6, 0.25, dir.z * 0.6);
                        e.hurtMarked = true;
                    }
                }
            }
            return s >= reach;
        };
    }

    /** A ring of burning gas closing in from the walls toward the centre, with gaps (radial lanes) at {@code gapAngles}. */
    private Effect fireRing(double[] gapAngles, int warn, double speed, float damage) {
        Set<UUID> hit = new HashSet<>();
        int[] t = {0};
        double reach = reach();
        Vec3 c = centre();
        return (boss, level) -> {
            int k = t[0]++;
            double r = k < warn ? reach : reach - (k - warn) * speed;
            if (k < warn) {
                if (k % 3 == 0) {
                    for (double ga : gapAngles) {
                        Vec3 d = rotate(new Vec3(0, 0, 1), ga);
                        Vec3 s = new Vec3(-d.z, 0, d.x);
                        for (double rr = 1.5; rr <= reach; rr += 1.5) {
                            for (int sgn = -1; sgn <= 1; sgn += 2) {
                                Vec3 p = c.add(d.scale(rr)).add(s.scale(GAP_HALF * sgn));
                                level.sendParticles(SWAMPFIRE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                            }
                        }
                    }
                    telegraphRingFrom(level, c, reach - 0.5, gapAngles);
                }
                return false;
            }
            int n = Math.max(8, (int) (r * 7));
            for (int i = 0; i < n; i++) {
                double a = 360.0 * i / n;
                if (inRingGap(a, r, gapAngles)) {
                    continue;
                }
                Vec3 p = c.add(rotate(new Vec3(0, 0, 1), a).scale(r));
                level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.6, p.z, 1, 0.15, 0.6, 0.15, 0.01);
                if (i % 3 == 0) {
                    level.sendParticles(GAS, p.x, p.y + 1.8, p.z, 1, 0.15, 0.4, 0.15, 0);
                }
            }
            if (k % 6 == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.FIRE_AMBIENT, SoundSource.HOSTILE, 3.0F, 0.5F);
            }
            for (LivingEntity e : boss.victims(level, c, reach + 2)) {
                Vec3 rel = e.position().subtract(c).multiply(1, 0, 1);
                double d = rel.length();
                double a = Math.toDegrees(Math.atan2(-rel.x, rel.z));
                if (Math.abs(d - r) <= 0.8 && !inRingGap(a, Math.max(d, 0.5), gapAngles) && e.getY() - c.y < LINE_HEIGHT
                        && hit.add(e.getUUID())) {
                    if (e.hurtServer(level, boss.damageSources().mobAttack(boss), damage)) {
                        e.igniteForSeconds(4.0F);
                        Vec3 in = rel.lengthSqr() > 1.0E-4 ? rel.normalize().scale(-0.5) : Vec3.ZERO;
                        e.push(in.x, 0.25, in.z);
                        e.hurtMarked = true;
                    }
                }
            }
            return r <= 1.5;
        };
    }

    /** Is angle {@code a} (degrees, same convention as {@link #rotate} of +z) inside a lane at radius r? */
    private static boolean inRingGap(double a, double r, double[] gapAngles) {
        for (double ga : gapAngles) {
            double diff = Math.abs(Mth.wrapDegrees(a - ga));
            double lateral = Math.sin(Math.toRadians(Math.min(90, diff))) * r;
            if (diff < 90 && lateral <= GAP_HALF) {
                return true;
            }
        }
        return false;
    }

    private void telegraphRingFrom(ServerLevel level, Vec3 c, double r, double[] gapAngles) {
        int n = Math.max(8, (int) (r * 4));
        for (int i = 0; i < n; i++) {
            double a = 360.0 * i / n;
            if (inRingGap(a, r, gapAngles)) {
                continue;
            }
            Vec3 p = c.add(rotate(new Vec3(0, 0, 1), a).scale(r));
            level.sendParticles(ParticleTypes.SMALL_FLAME, p.x, p.y + 0.2, p.z, 1, 0, 0, 0, 0);
        }
    }

    private static double flatDist(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    // ------------------------------------------------------------------ damage, ticking, cleanup

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (guard > 0) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 2.5, getZ(), 8, 0.6, 1.0, 0.6, 0.02);
            return false;
        }
        if (wisping) {
            return false;
        }
        if (tickCount < spentUntil) {
            amount *= 1.25F;
        }
        return super.hurtServer(level, source, amount);
    }

    /** Puts back everything he placed: the mud and the lanterns. */
    private void cleanUp(ServerLevel level) {
        restoreMud(level, true);
        removeLanterns(level, lanterns);
        removeLanterns(level, staleLanterns);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        if (staleMud) {                         // saved by an unload: restored on the first tick
            staleMud = false;
            restoreMud(level, true);
        }
        if (!staleLanterns.isEmpty()) {
            removeLanterns(level, staleLanterns);
        }
        if (guard > 0) {
            guard--;
        }
        restoreMud(level, false);               // expired circles (even if their effect was lost)
        BossAttack cur = currentAttack();
        if ((wisping || isInvisible()) && (cur == null || !"wisp".equals(cur.name))) {
            endWisp();                          // the wisp was cut short (reset, stagger): he is seen again
        }
        LivingEntity target = getTarget();
        boolean fighting = target != null && target.isAlive();
        boolean anyone = com.brasshaven.util.NearbyPlayers.any(level,
                new AABB(BlockPos.containing(centre())).inflate(radius + 14, 16, radius + 14),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (!anyone && (!mudOrig.isEmpty() || !lanterns.isEmpty())) {
            cleanUp(level);                     // the arena emptied (death, flight)
        }
        if (phase() == 1 && (kindled || !lanterns.isEmpty())) {      // the fight was reset
            kindled = false;
            roarUntil = -1;
            spentUntil = -1;
            cleanUp(level);
            var speed = getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(com.brasshaven.Brasshaven.id("bog_hierophant_kindled"));
                speed.removeModifier(com.brasshaven.Brasshaven.id("bog_hierophant_wrath"));
            }
        }
        if (phase() == 2 && anyone && fighting && lanterns.isEmpty() && tickCount > roarUntil && tickCount % 20 == 0) {
            placeLanterns(level);               // players came back after the arena emptied
        }
        boolean free = fighting && cur == null && !isStaggered() && tickCount > roarUntil;
        if (fighting && --leechTimer <= 0 && free && leechCap() - minions(level) > 0) {
            leechTimer = (int) Math.round(LEECHES_EVERY * cooldownScale());
            chain(level, "leeches");
            free = false;
        }
        if (phase() == 2 && free) {
            if (!kindled && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "kindle");
            } else if (kindled && --firelinesTimer <= 0) {
                firelinesTimer = (int) Math.round(FIRELINES_EVERY * cooldownScale());
                chain(level, "firelines");
            }
        }
        // ambience: the marsh-flies round his head, the lantern's glow, the gas round him once kindled
        if (!wisping) {
            if (tickCount % 3 == 0) {
                level.sendParticles(FLIES, getX(), getY() + 5.0, getZ(), 2, 0.9, 0.6, 0.9, 0.03);
            }
            float yaw = yBodyRot * Mth.DEG_TO_RAD;
            if (tickCount % 5 == 0) {
                double lx = getX() - Mth.cos(yaw) * 1.1 - Mth.sin(yaw) * 0.9;
                double lz = getZ() - Mth.sin(yaw) * 1.1 + Mth.cos(yaw) * 0.9;
                level.sendParticles(SWAMPFIRE, lx, getY() + 4.6, lz, 1, 0.1, 0.1, 0.1, 0.005);
            }
            if (kindled && tickCount % 4 == 0) {
                level.sendParticles(ParticleTypes.SMALL_FLAME, getX(), getY() + 1.5, getZ(), 2, 0.7, 1.0, 0.7, 0.01);
            }
            if (tickCount % 100 == 0) {
                level.playSound(null, this, SoundEvents.WITCH_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.4F);
            }
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        int roar = ROAR >= 0 && ROAR < actionTicks().length ? actionTicks()[ROAR] : 40;
        roarUntil = tickCount + roar + 10;
        endWisp();
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("bog_hierophant_wrath"), 0.10,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        placeLanterns(level);
        level.sendParticles(FLIES, getX(), getY() + 4, getZ(), 120, 2.5, 1.5, 2.5, 0.1);
        level.playSound(null, this, SoundEvents.BEE_LOOP_AGGRESSIVE, SoundSource.HOSTILE, 3.0F, 0.4F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        endWisp();
        cleanUp(level);
        for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(blockPosition()).inflate(40),
                m -> m.entityTags().contains(MINION_TAG))) {
            level.sendParticles(MUDDUST, m.getX(), m.getY() + 0.5, m.getZ(), 10, 0.3, 0.3, 0.3, 0.05);
            m.discard();
        }
        level.sendParticles(SWAMPFIRE, getX(), getY() + 3, getZ(), 120, 1.2, 2.0, 1.2, 0.05);
        level.sendParticles(FLIES, getX(), getY() + 3, getZ(), 150, 2.0, 2.0, 2.0, 0.15);
        level.playSound(null, this, SoundEvents.WITCH_CELEBRATE, SoundSource.HOSTILE, 3.0F, 0.3F);
        level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy() && level() instanceof ServerLevel level) {
            cleanUp(level);
        }
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (centre != null) {
            output.putLong("HierophantCentre", BlockPos.containing(centre).asLong());
        }
        output.putInt("HierophantRadius", radius);
        output.putBoolean("HierophantKindled", kindled);
        List<Long> lamps = new ArrayList<>();
        lanterns.forEach(p -> lamps.add(p.asLong()));
        staleLanterns.forEach(p -> lamps.add(p.asLong()));
        output.store("HierophantLanterns", Codec.LONG.listOf(), lamps);
        List<Long> mudPos = new ArrayList<>();
        List<BlockState> mudStates = new ArrayList<>();
        for (Map.Entry<BlockPos, BlockState> en : mudOrig.entrySet()) {
            mudPos.add(en.getKey().asLong());
            mudStates.add(en.getValue());
        }
        output.store("HierophantMudPos", Codec.LONG.listOf(), mudPos);
        output.store("HierophantMudStates", BlockState.CODEC.listOf(), mudStates);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long c = input.getLongOr("HierophantCentre", Long.MIN_VALUE);
        centre = c == Long.MIN_VALUE ? null : Vec3.atBottomCenterOf(BlockPos.of(c));
        radius = input.getIntOr("HierophantRadius", 16);
        kindled = input.getBooleanOr("HierophantKindled", false) && phase() == 2;
        anchors.clear();
        lanterns.clear();
        staleLanterns.clear();
        input.read("HierophantLanterns", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> staleLanterns.add(BlockPos.of(p))));
        mudOrig.clear();
        mudUntil.clear();
        List<Long> pos = input.read("HierophantMudPos", Codec.LONG.listOf()).orElse(List.of());
        List<BlockState> states = input.read("HierophantMudStates", BlockState.CODEC.listOf()).orElse(List.of());
        for (int i = 0; i < Math.min(pos.size(), states.size()); i++) {
            BlockPos p = BlockPos.of(pos.get(i));
            mudOrig.put(p, states.get(i));
            mudUntil.put(p, 0);
        }
        staleMud = !mudOrig.isEmpty();
        wisping = false;
        setInvisible(false);
    }
}

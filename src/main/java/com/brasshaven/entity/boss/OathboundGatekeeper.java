package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.BASH;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.BROKEN;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.FURY;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.KEYFALL;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.KEYSWING;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.KNEEL;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.OVERHEAD;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.ROAR;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.RUSH;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.STAGGER;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.STOMP;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.SWEEP;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.THRUST;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.TOLL;
import static com.brasshaven.generated.MobAnims.OathboundGatekeeper.WHEEL;

/**
 * Le Gardien du Serment (The Oathbound Gatekeeper), the living knight of the Kneeling Gate: one of the two stone giants
 * above the pass come down to fight size, pale limestone plate, red-granite cloak, open helm and braided beard, a tower
 * shield carved with the gold key of the toll on his left arm, a stone greatsword in his right hand and the gate's key
 * on a chain at his hip. He waits in the domed hall under the gate.
 * <p>A hard underground fight: 480 health, armour 14, poise 110, hits of 9 to 22, and a shield that matters:
 * <ul>
 *     <li><b>Oath guard</b> (phases 1-2): while he walks and during his sword and shield moves, every hit from his front
 *     (about 145 degrees) clangs off the shield: flank him and strike his back or sides. Three blocked hits in a row and
 *     he answers with a shield bash; stay behind him too long and he wheels round. His key moves, the overhead and the
 *     toll leave the guard open.</li>
 *     <li>Phase 1: <b>sweep</b>, <b>thrust</b> (lunge), <b>bash</b>, <b>stomp</b> (all round him, a ring to jump),
 *     <b>keyfall</b> (the key hurled onto a ring that follows you), <b>wheel</b> (a full turn, the anti-flank move).</li>
 *     <li>Phase 2 (a roar at 65%, the gate's bell answers): <b>keyswing</b> (deadly at mid range), <b>overhead</b> (hands
 *     burst along the blade's line), <b>rush</b> (a shield charge) and the <b>toll</b>: he strikes his shield like the
 *     gate's bell, and walls of stone hands punch up across the whole hall in two sweeps, each with one open lane.</li>
 *     <li>Phase 3 (at 30%, handled here like the Chained Jailer's): he <b>kneels</b> behind his planted shield like the
 *     statues above (10 s): no damage reaches him, the gate heals him and the bell tolls hand sweeps; every hit on him
 *     goes to the <b>Oath Shield</b> (its own bar). Break it and he reels (3 s, +50% damage taken), loses the guard for
 *     good and fights two-handed (<b>fury</b> combo, the toll every 15 s). Fail and he rises healed and kneels again
 *     30 s later.</li>
 * </ul>
 */
public class OathboundGatekeeper extends WayfarerBoss {
    public static final float WIDTH = 2.6F;
    public static final float HEIGHT = 5.6F;
    private static final EntityDataAccessor<Boolean> DATA_BROKEN =
            SynchedEntityData.defineId(OathboundGatekeeper.class, EntityDataSerializers.BOOLEAN);
    private static final float PHASE_THREE_AT = 0.3F;
    private static final int KNEEL_TICKS = 200;
    private static final int KNEEL_EVERY = 600;
    private static final int TOLL_EVERY = 300;
    private static final int FURY_EVERY = 170;
    /** Half width of the open lane in a sweep of hands. */
    private static final double LANE = 1.8;
    /** Half extent of a sweep of hands (the hall is 17.5 blocks in radius). */
    private static final double SWEEP_HALF = 18.0;
    /** Moves during which the oath guard stays up (frontal hits are blocked). */
    private static final Set<String> GUARDED = Set.of("sweep", "thrust", "bash", "stomp", "wheel", "rush");
    private static final DustParticleOptions OATH = new DustParticleOptions(0x6EE8EC, 1.2F);
    private static final DustParticleOptions GOLD = new DustParticleOptions(0xF0C450, 1.2F);
    private static final DustParticleOptions STONE = new DustParticleOptions(0xB8B0A0, 1.4F);

    /** Phase 3 started (the first kneel). */
    private boolean phaseThree;
    /** The oath shield was broken: no more guard, two-handed fury. */
    private boolean shieldBroken;
    /** Kneeling behind the planted shield: hits go to the shield, he heals. */
    private boolean kneeling;
    private float shieldHp;
    private float shieldMax;
    private ServerBossEvent shieldBar;
    private int phaseTwoTick = -1;
    private int kneelTimer;
    private int tollTimer;
    private int furyTimer;
    private int blockedHits;
    private int lastBlockTick;
    private int behindTicks;
    private int wheelReady;
    private Vec3 hall;
    private Vec3 keyTarget;
    private final Set<UUID> struck = new HashSet<>();

    public OathboundGatekeeper(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 480.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 16.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_BROKEN, false);
    }

    /** Texture variant 1 (tools/wf/mobs/oathbound_gatekeeper.py "broken") paints the shield away. */
    @Override
    public int modelVariant() {
        return entityData.get(DATA_BROKEN) ? 1 : 0;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.OathboundGatekeeper.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.BLUE;
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
        return 4.5;
    }

    public boolean isKneeling() {
        return kneeling;
    }

    public boolean isShieldBroken() {
        return shieldBroken;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sweep: the greatsword drawn far back to his right (0.8 s, the arc is outlined in stone dust), then swept
        // flat over 200 degrees in front of him
        out.add(BossAttack.of("sweep").anim(SWEEP).timing(16, 4, 14).range(0, 7.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 7.4, 100, STONE);
                    }
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_NETHERITE.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 7.5, 100)) {
                        b.strike(level, e, 16.0F, 1.4, 0.25);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                    for (int a = -100; a <= 100; a += 10) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(5.5));
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 1, 0, 0, 0, 0);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.35F) {
                        b.chain(level, b.distanceTo(t) > 4.0 ? "thrust" : "stomp");
                    }
                })
                .build());
        // thrust: the blade drawn back level behind the shield (0.7 s, a line of dust shows the lunge), then he lunges
        // ten blocks point first
        out.add(BossAttack.of("thrust").anim(THRUST).timing(14, 8, 14).range(4.0, 14.0).cooldown(90).weight(9)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 2; d <= 11; d += 1.5) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(STONE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) ->
                        level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.4F))
                .active((b, level, t, tick) -> {
                    if (tick < 6) {
                        Vec3 f = b.forward().scale(1.2);
                        b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                        b.hurtMarked = true;
                    } else {
                        b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    }
                    if (b instanceof OathboundGatekeeper g) {
                        g.hitAhead(level, 2.6, 2.0, 15.0F, 1.3);
                    }
                    Vec3 tip = b.ahead(3.0);
                    level.sendParticles(ParticleTypes.CRIT, tip.x, tip.y + 2.0, tip.z, 3, 0.2, 0.2, 0.2, 0.1);
                })
                .end((b, level, t, tick) -> b.setDeltaMovement(0, b.getDeltaMovement().y, 0))
                .build());
        // bash: the shield drawn in (0.6 s, a short arc of sparks), then rammed out: whoever stands in front is hurled
        // back and dazed. His answer to players beating on the shield.
        out.add(BossAttack.of("bash").anim(BASH).timing(12, 3, 11).range(0, 4.5).cooldown(60).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 4.4, 60, ParticleTypes.CRIT);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ARMOR_EQUIP_NETHERITE.value(), SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 4.5, 60)) {
                        b.strike(level, e, 10.0F, 2.6, 0.5);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), b);
                    }
                    level.playSound(null, b, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 1.5F, 0.6F);
                })
                .build());
        // stomp: the right foot raised high (0.9 s, a ring marks its reach), stamped down: 13 all round him and a ring
        // of force to jump (two in phase 2). It punishes flankers who hug his back.
        out.add(BossAttack.of("stomp").anim(STOMP).timing(18, 3, 13).range(0, 6.0).cooldown(100).weight(8).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 4.0, STONE);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 4.0, 13.0F, 1.4, 0.6);
                    b.addEffect(WayfarerBoss.wave(b.position(), 10, 0.5, 9.0F, ParticleTypes.CRIT));
                    if (b.phase() == 2) {
                        b.addEffect(delayed(10, WayfarerBoss.wave(b.position(), 10, 0.5, 9.0F, ParticleTypes.CRIT)));
                    }
                    level.sendParticles(dust(), b.getX(), b.getY() + 0.2, b.getZ(), 50, 2.0, 0.2, 2.0, 0.1);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .build());
        // keyfall: the key swung up over his helm on its chain (0.9 s, a gold ring follows the target), then hurled:
        // the ring locks where the target stood and the key crashes down on it 0.9 s later. His guard is open.
        out.add(BossAttack.of("keyfall").anim(KEYFALL).timing(18, 20, 12).range(7.0, 22.0).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    if (t != null && tick % 2 == 0) {
                        b.telegraphRing(level, t.position(), 2.4, GOLD);
                    }
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_HIT, SoundSource.HOSTILE, 2.0F, 0.6F + tick * 0.02F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof OathboundGatekeeper g) {
                        g.keyTarget = t != null ? t.position() : b.ahead(10.0);
                        b.addEffect(g.keyCrash(g.keyTarget, 18));
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .build());
        // wheel: feet set and shoulder turned (0.7 s, a ring of dust), then a full turn, blade out. Picked rarely on its
        // own; mostly the answer when a player stays behind him (bossTick).
        out.add(BossAttack.of("wheel").anim(WHEEL).timing(14, 4, 14).range(0, 5.5).cooldown(90).weight(4).track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 5.5, ParticleTypes.CRIT);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_HURT, SoundSource.HOSTILE, 1.5F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 5.5, 14.0F, 1.6, 0.3);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.4F);
                    for (int a = 0; a < 360; a += 20) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(4.5));
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 1, 0, 0, 0, 0);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // keyswing: the key whirled round his hip on its chain (0.9 s; two rings show the deadly band, 3.6 to 9.8
        // blocks), then swung out in a full circle at chest height: hug him or get far away
        out.add(BossAttack.of("keyswing").anim(KEYSWING).phaseTwo().timing(18, 4, 14).range(3.0, 11.0).cooldown(140).weight(8)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 3.6, GOLD);
                        b.telegraphRing(level, b.position(), 9.8, GOLD);
                    }
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 2.0F, 0.5F + tick * 0.03F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : b.victims(level, b.position(), 10.5)) {
                        double d = flatDist(e.position(), b.position());
                        if (d >= 3.6 && d <= 9.8 + e.getBbWidth() / 2) {
                            b.strike(level, e, 12.0F, 1.0, 0.3);
                            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), b);
                        }
                    }
                    for (int a = 0; a < 360; a += 10) {
                        Vec3 p = b.position().add(rotate(b.forward(), a).scale(7.0));
                        level.sendParticles(GOLD, p.x, p.y + 1.4, p.z, 2, 0.2, 0.1, 0.2, 0);
                    }
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.4F);
                })
                .build());
        // overhead: the greatsword heaved over the helm (1.1 s, the landing ring and a line of dust), crashed 3.5
        // ahead (22); stone hands burst up one after another along the blade's line out to 15 blocks. Guard open.
        out.add(BossAttack.of("overhead").anim(OVERHEAD).phaseTwo().timing(22, 4, 18).range(0, 9.0).cooldown(100).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 2.8, STONE);
                        for (double d = 5; d <= 15; d += 1.5) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(OATH, p.x, p.y + 0.1, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 6) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.HOSTILE, 2.0F, 0.4F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(3.5);
                    b.hitCircle(level, c, 2.8, 22.0F, 1.2, 0.6);
                    int i = 0;
                    for (double d = 5; d <= 15; d += 1.5, i++) {
                        b.addEffect(hand(b.ahead(d), 4 + i * 2, 1.4, 13.0F));
                    }
                    level.sendParticles(dust(), c.x, c.y + 0.3, c.z, 40, 1.2, 0.2, 1.2, 0.1);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .build());
        // toll: the spectacle. He raises the greatsword (1.2 s, the bell of the gate hums) and strikes his own shield;
        // the toll rolls through the floor and a wall of stone hands sweeps the whole hall, row after row, with one
        // open lane (marked by two lines of soul light); 2.2 s later a second wall sweeps across the first.
        out.add(BossAttack.of("toll").anim(TOLL).phaseTwo().timing(24, 40, 16).range(0, 30.0).cooldown(360).weight(6)
                .track(false)
                .windup((b, level, t, tick) -> {
                    if (tick % 6 == 0) {
                        level.playSound(null, b, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                    level.sendParticles(OATH, b.getX(), b.getY() + 5.5, b.getZ(), 3, 0.8, 0.5, 0.8, 0);
                })
                .impact((b, level, t, tick) -> {
                    if (b instanceof OathboundGatekeeper g) {
                        g.toll(level, b.forward(), 0, 10.0);
                        g.toll(level, rotate(b.forward(), 90), 44, 10.0);
                    }
                })
                .build());
        // rush: the shield set and the head lowered (0.8 s, a line of sparks shows the path), then a charge behind the
        // shield: whoever it meets is trampled and thrown; 40% chains into the overhead
        out.add(BossAttack.of("rush").anim(RUSH).phaseTwo().timing(16, 16, 12).range(6.0, 18.0).cooldown(140).weight(8)
                .start((b, level, t, tick) -> struck.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        for (double d = 2; d <= 16; d += 2) {
                            Vec3 p = b.ahead(d);
                            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    Vec3 f = b.forward().scale(tick < 13 && !b.horizontalCollision ? 1.0 : 0.0);
                    b.setDeltaMovement(f.x, b.getDeltaMovement().y, f.z);
                    b.hurtMarked = true;
                    if (b instanceof OathboundGatekeeper g) {
                        g.hitAhead(level, 2.6, 2.4, 16.0F, 2.2);
                    }
                    if (tick % 3 == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_STEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                        level.sendParticles(dust(), b.getX(), b.getY() + 0.2, b.getZ(), 10, 1.0, 0.1, 1.0, 0.05);
                    }
                })
                .end((b, level, t, tick) -> {
                    b.setDeltaMovement(0, b.getDeltaMovement().y, 0);
                    if (t != null && b.distanceTo(t) < 7.0 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "overhead");
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 3 (started from bossTick only)
        // kneel: he sinks onto one knee behind his planted shield (1 s), like the statues above, and holds the oath for
        // 10 s: no damage reaches him, every hit goes to the Oath Shield; the gate heals him and its bell tolls three
        // sweeps of hands. Break the shield and he reels (broken); fail and he rises.
        out.add(BossAttack.of("kneel").anim(KNEEL).phaseTwo().timing(20, KNEEL_TICKS, 24).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .start((b, level, t, tick) -> {
                    if (b instanceof OathboundGatekeeper g) {
                        g.startKneel(level);
                    }
                })
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, b.position(), 4.0 - tick * 0.12, OATH);
                    }
                })
                .impact((b, level, t, tick) -> {
                    level.playSound(null, b, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.5F);
                    level.playSound(null, b, SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 2.0F, 0.4F);
                    level.sendParticles(dust(), b.getX(), b.getY() + 0.2, b.getZ(), 40, 1.5, 0.2, 1.5, 0.1);
                })
                .active((b, level, t, tick) -> {
                    if (b instanceof OathboundGatekeeper g) {
                        g.tickKneel(level, tick);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b instanceof OathboundGatekeeper g) {
                        g.endKneel(level);
                    }
                })
                .build());
        // broken: the shield shatters out of his grip; he reels, open (3 s, +50% damage taken)
        out.add(BossAttack.of("broken").anim(BROKEN).phaseTwo().timing(6, 4, 50).range(999, 999).cooldown(0).weight(0)
                .track(false)
                .active((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.sendParticles(ParticleTypes.CRIT, b.getX(), b.getY() + 3.5, b.getZ(), 30, 0.6, 0.6, 0.6, 0.4);
                    }
                })
                .build());
        // fury (shield broken, scheduled): both hands on the hilt; a sweep (0.7 s, arc outlined), a backhand 0.6 s later,
        // then an overhead crash with a ring to jump
        out.add(BossAttack.of("fury").anim(FURY).phaseTwo().timing(14, 30, 16).range(999, 999).cooldown(0).weight(0)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 7.0, 70, OATH);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.IRON_GOLEM_HURT, SoundSource.HOSTILE, 2.0F, 0.3F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (LivingEntity e : arcVictims(b, level, 7.0, 70)) {
                        b.strike(level, e, 15.0F, 1.2, 0.2);
                    }
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    if (tick > 0 && tick < 12 && tick % 3 == 0) {
                        b.telegraphArc(level, 7.0, 70, OATH);
                    }
                    if (tick == 12) {
                        for (LivingEntity e : arcVictims(b, level, 7.0, 70)) {
                            b.strike(level, e, 15.0F, 1.2, 0.2);
                        }
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                    if (tick > 12 && tick < 24 && tick % 3 == 0) {
                        b.telegraphRing(level, b.ahead(3.5), 3.0, OATH);
                    }
                    if (tick == 24) {
                        Vec3 c = b.ahead(3.5);
                        b.hitCircle(level, c, 3.0, 20.0F, 1.2, 0.6);
                        b.addEffect(WayfarerBoss.wave(c, 9, 0.5, 9.0F, ParticleTypes.SOUL_FIRE_FLAME));
                        level.sendParticles(dust(), c.x, c.y + 0.3, c.z, 40, 1.2, 0.2, 1.2, 0.1);
                        level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ move helpers

    private static BlockParticleOption dust() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.CALCITE.defaultBlockState());
    }

    private static BlockParticleOption tuff() {
        return new BlockParticleOption(ParticleTypes.BLOCK, Blocks.TUFF.defaultBlockState());
    }

    /** Living targets inside the arc that {@link #hitArc} covers. */
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

    /** Lunges and charges: whoever is within {@code radius} of the point {@code reach} ahead is hit once per move. */
    private void hitAhead(ServerLevel level, double reach, double radius, float damage, double knockback) {
        Vec3 c = ahead(reach);
        for (LivingEntity e : victims(level, c, radius)) {
            if (flatDist(e.position(), c) <= radius + e.getBbWidth() / 2 && struck.add(e.getUUID())) {
                strike(level, e, damage, knockback, 0.45);
            }
        }
    }

    /** A stone hand punching up from the floor: dust for {@code warn} ticks, then a fist that hurts and throws up. */
    private static Effect hand(Vec3 pos, int warn, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 3 == 0) {
                    level.sendParticles(STONE, pos.x, pos.y + 0.1, pos.z, 3, radius * 0.4, 0.02, radius * 0.4, 0);
                }
                return false;
            }
            fist(level, pos);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (flatDist(e.position(), pos) <= radius && e.getY() - pos.y < 2.0) {
                    boss.strike(level, e, damage, 0.3, 0.85);
                }
            }
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F);
            return true;
        };
    }

    /** The look of a fist bursting out of the floor: a column of stone chips, a puff of dust. */
    private static void fist(ServerLevel level, Vec3 p) {
        level.sendParticles(tuff(), p.x, p.y + 0.6, p.z, 8, 0.25, 0.6, 0.25, 0.1);
        level.sendParticles(dust(), p.x, p.y + 1.4, p.z, 4, 0.2, 0.4, 0.2, 0.05);
        level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.8, p.z, 2, 0.1, 0.2, 0.1, 0.1);
    }

    /**
     * A sweep of stone hands across the hall: rows perpendicular to {@code dir}, 2 blocks apart, from 18 blocks behind
     * the hall's centre to 18 in front; each row warned for {@code warn} ticks by stone dust, then its fists burst up
     * ({@code step} ticks after the previous row). One lane, {@code gap} blocks to the side, stays open, marked by two
     * lines of soul light. Hits each creature once, too tall to jump.
     */
    private Effect handSweep(Vec3 centre, Vec3 dir, double gap, int warn, int step, float damage) {
        Vec3 lat = new Vec3(-dir.z, 0, dir.x);
        int rows = (int) (SWEEP_HALF * 2 / 2.0) + 1;
        Set<UUID> hit = new HashSet<>();
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            for (int r = 0; r < rows; r++) {
                int fire = warn + r * step;
                if (k < fire - warn || k > fire) {
                    continue;
                }
                Vec3 row = centre.add(dir.scale(-SWEEP_HALF + r * 2.0));
                if (k < fire) {
                    if ((k + r) % 4 == 0) {
                        for (double s = -SWEEP_HALF; s <= SWEEP_HALF; s += 2.0) {
                            if (Math.abs(s - gap) < LANE) {
                                continue;
                            }
                            Vec3 p = row.add(lat.scale(s));
                            if (flatDist(p, centre) <= SWEEP_HALF + 1) {
                                level.sendParticles(STONE, p.x, p.y + 0.1, p.z, 1, 0.3, 0, 0.3, 0);
                            }
                        }
                        for (int side = -1; side <= 1; side += 2) {       // the open lane's edges
                            Vec3 p = row.add(lat.scale(gap + side * LANE));
                            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.15, p.z, 1, 0, 0.02, 0, 0);
                        }
                    }
                    continue;
                }
                for (double s = -SWEEP_HALF; s <= SWEEP_HALF; s += 2.0) {
                    Vec3 p = row.add(lat.scale(s));
                    if (Math.abs(s - gap) >= LANE && flatDist(p, centre) <= SWEEP_HALF + 1 && (r + (int) s) % 2 == 0) {
                        fist(level, p);
                    }
                }
                for (LivingEntity e : boss.victims(level, row, SWEEP_HALF + 2)) {
                    Vec3 rel = e.position().subtract(row).multiply(1, 0, 1);
                    double along = rel.dot(dir);
                    double side = rel.dot(lat);
                    if (Math.abs(along) <= 1.15 && Math.abs(side) <= SWEEP_HALF + 1 && Math.abs(side - gap) >= LANE - 0.4
                            && e.getY() - row.y < 2.2 && hit.add(e.getUUID())) {
                        boss.strike(level, e, damage, 0.3, 0.85);
                    }
                }
                if (r % 2 == 0) {
                    level.playSound(null, row.x, row.y, row.z, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.6F, 0.5F);
                }
                if (r % 4 == 0) {
                    level.playSound(null, row.x, row.y, row.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.HOSTILE, 1.2F, 0.6F);
                }
            }
            return k >= warn + (rows - 1) * step;
        };
    }

    /**
     * The bell of the gate tolls: after {@code delay} ticks, one sweep of hands along {@code dir}. The open lane is
     * picked within {@code spread} blocks of the lane through the knight himself.
     */
    private void toll(ServerLevel level, Vec3 dir, int delay, double spread) {
        Vec3 centre = hall != null ? hall : position();
        Vec3 lat = new Vec3(-dir.z, 0, dir.x);
        double self = position().subtract(centre).dot(lat);
        double gap = Mth.clamp(self + (random.nextDouble() * 2 - 1) * spread, -12.0, 12.0);
        int[] t = {0};
        Effect sweep = handSweep(centre, dir, gap, 18, 2, 13.0F);
        addEffect((boss, lvl) -> {
            if (t[0]++ < delay) {
                return false;
            }
            if (t[0] == delay + 1) {
                lvl.playSound(null, boss, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0F, 0.5F);
                lvl.playSound(null, boss, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                lvl.sendParticles(OATH, boss.getX(), boss.getY() + 3.0, boss.getZ(), 40, 2.0, 1.5, 2.0, 0.05);
            }
            return sweep.tick(boss, lvl);
        });
    }

    /** The key falls on the locked ring {@code warn} ticks after the throw: 14, held fast ("locked") 1.5 s. */
    private Effect keyCrash(Vec3 pos, int warn) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < warn) {
                if (k % 2 == 0) {
                    boss.telegraphRing(level, pos, 2.4 - k * 0.04, GOLD);
                    double h = 8.0 * (1.0 - (double) k / warn);
                    level.sendParticles(GOLD, pos.x, pos.y + 1.5 + h, pos.z, 4, 0.3, 0.3, 0.3, 0);
                }
                return false;
            }
            for (LivingEntity e : boss.victims(level, pos, 2.4)) {
                if (flatDist(e.position(), pos) <= 2.4) {
                    boss.strike(level, e, 14.0F, 0.4, 0.4);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 3), boss);
                }
            }
            if (boss.phase() == 2) {
                for (int i = 0; i < 6; i++) {
                    double a = Math.PI * 2 * i / 6;
                    boss.addEffect(hand(pos.add(Math.cos(a) * 3.5, 0, Math.sin(a) * 3.5), 10, 1.2, 11.0F));
                }
            }
            level.sendParticles(GOLD, pos.x, pos.y + 0.5, pos.z, 30, 1.0, 0.4, 1.0, 0.05);
            level.sendParticles(dust(), pos.x, pos.y + 0.3, pos.z, 30, 1.0, 0.2, 1.0, 0.1);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.0F, 0.5F);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.CHAIN_PLACE, SoundSource.HOSTILE, 2.0F, 0.5F);
            return true;
        };
    }

    // ------------------------------------------------------------------ the oath shield (phase 3)

    private void startKneel(ServerLevel level) {
        kneeling = true;
        phaseThree = true;
        shieldMax = 60.0F * (1.0F + 0.6F * (scaledPlayers() - 1)) * (1.0F + 0.25F * cycle());
        shieldHp = shieldMax;
        if (shieldBar == null) {
            shieldBar = new ServerBossEvent(UUID.randomUUID(), Component.translatable("message.brasshaven.boss.oath_shield"),
                    BossEvent.BossBarColor.WHITE, BossEvent.BossBarOverlay.NOTCHED_10);
        }
        shieldBar.setProgress(1.0F);
        for (ServerPlayer p : level.getEntitiesOfClass(ServerPlayer.class, getBoundingBox().inflate(32), ServerPlayer::isAlive)) {
            shieldBar.addPlayer(p);
        }
        level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    private void tickKneel(ServerLevel level, int tick) {
        if (!kneeling) {
            return;
        }
        if (tick % 20 == 10) {           // the gate heals its knight
            heal(getMaxHealth() * 0.008F);
            level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 2.5, getZ(), 4, 0.8, 1.0, 0.8, 0);
        }
        if (tick == 10 || tick == 75 || tick == 140) {
            Vec3 dir = tick == 75 ? rotate(forward(), 90) : forward();
            toll(level, dir, 0, 4.0);      // the lane passes near him: the shield stays in reach
        }
        if (tick % 4 == 0) {
            Vec3 s = ahead(1.8);
            for (double y = 0.3; y < 3.0; y += 0.6) {
                level.sendParticles(OATH, s.x, getY() + y, s.z, 1, 0.6, 0.1, 0.6, 0);
            }
            telegraphRing(level, position(), 2.2, OATH);
        }
    }

    private void endKneel(ServerLevel level) {
        if (kneeling) {                  // the oath held: he rises, shield whole
            kneeling = false;
            level.playSound(null, this, SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 3.0F, 0.6F);
            level.playSound(null, this, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.HOSTILE, 2.0F, 0.5F);
        }
        kneelTimer = (int) Math.round(KNEEL_EVERY * cooldownScale());
        clearShieldBar();
    }

    private void damageShield(ServerLevel level, float amount) {
        shieldHp -= amount;
        Vec3 p = ahead(1.8);
        level.sendParticles(dust(), p.x, getY() + 1.6, p.z, 8, 0.5, 0.6, 0.5, 0.1);
        level.sendParticles(OATH, p.x, getY() + 1.6, p.z, 4, 0.5, 0.6, 0.5, 0.05);
        level.playSound(null, this, SoundEvents.STONE_HIT, SoundSource.HOSTILE, 2.0F, 0.6F + random.nextFloat() * 0.2F);
        if (shieldBar != null) {
            shieldBar.setProgress(Math.max(0.0F, shieldHp / shieldMax));
        }
        if (shieldHp <= 0) {
            breakShield(level);
        }
    }

    private void breakShield(ServerLevel level) {
        kneeling = false;
        shieldBroken = true;
        entityData.set(DATA_BROKEN, true);
        clearShieldBar();
        tollTimer = 200;
        furyTimer = 80;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("oathbound_gatekeeper_oathbroken"),
                    0.18, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        Vec3 p = ahead(1.8);
        level.sendParticles(dust(), p.x, getY() + 1.8, p.z, 120, 1.0, 1.4, 1.0, 0.3);
        level.sendParticles(OATH, p.x, getY() + 1.8, p.z, 60, 1.0, 1.4, 1.0, 0.2);
        level.sendParticles(GOLD, p.x, getY() + 1.8, p.z, 30, 0.8, 1.0, 0.8, 0.2);
        level.playSound(null, this, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.ANVIL_DESTROY, SoundSource.HOSTILE, 2.5F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 4.0F, 0.3F);
        chain(level, "broken");
    }

    private void clearShieldBar() {
        if (shieldBar != null) {
            shieldBar.removeAllPlayers();
        }
    }

    // ------------------------------------------------------------------ the guard

    /** Facing of the body as drawn (the guard follows the shield, which follows the body). */
    private Vec3 bodyForward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private boolean guardUp() {
        if (shieldBroken || kneeling || isStaggered()) {
            return false;
        }
        BossAttack a = currentAttack();
        return a == null || GUARDED.contains(a.name);
    }

    private boolean isFrontal(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null) {
            return false;
        }
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        BossAttack a = currentAttack();
        Vec3 face = a != null ? forward() : bodyForward();
        return to.lengthSqr() > 1.0E-4 && to.normalize().dot(face) >= 0.3;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return super.hurtServer(level, source, amount);
        }
        if (kneeling) {
            if (source.getEntity() instanceof Player) {
                damageShield(level, amount);
            }
            return false;
        }
        if (guardUp() && isFrontal(source) && !source.is(DamageTypeTags.BYPASSES_SHIELD)) {
            if (tickCount - lastBlockTick > 40) {
                blockedHits = 0;
            }
            blockedHits++;
            lastBlockTick = tickCount;
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 2.0F, 0.5F + random.nextFloat() * 0.2F);
            Vec3 p = position().add(bodyForward().scale(1.6));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 2.2, p.z, 10, 0.4, 0.6, 0.4, 0.3);
            level.sendParticles(OATH, p.x, p.y + 2.2, p.z, 4, 0.4, 0.6, 0.4, 0.05);
            if (source.getDirectEntity() instanceof LivingEntity attacker && attacker.distanceTo(this) < 5.0) {
                Vec3 push = attacker.position().subtract(position()).multiply(1, 0, 1).normalize().scale(0.5);
                attacker.push(push.x, 0.1, push.z);
                attacker.hurtMarked = true;
            }
            return false;
        }
        BossAttack a = currentAttack();
        if (a != null && a.name.equals("broken")) {
            amount *= 1.5F;
        }
        return super.hurtServer(level, source, amount);
    }

    // ------------------------------------------------------------------ brain, ambience

    @Override
    protected void bossTick(ServerLevel level) {
        if (hall == null) {
            hall = position();
        }
        if (wheelReady > 0) {
            wheelReady--;
        }
        BossAttack a = currentAttack();
        if (kneeling && (a == null || !a.name.equals("kneel"))) {
            kneeling = false;    // interrupted (fight reset)
            clearShieldBar();
        }
        if (phase() == 1) {
            if (phaseThree || shieldBroken) {   // the fight was reset: the oath is whole again
                phaseThree = false;
                shieldBroken = false;
                entityData.set(DATA_BROKEN, false);
                phaseTwoTick = -1;
            }
        }
        LivingEntity target = getTarget();
        boolean free = a == null && !isStaggered() && target != null && target.isAlive();
        // reactions: three blocked hits get a bash, a player lingering behind him gets the wheel
        if (free && !shieldBroken && blockedHits >= 3 && tickCount - lastBlockTick < 40 && distanceTo(target) < 5.0) {
            blockedHits = 0;
            chain(level, "bash");
            return;
        }
        if (free && distanceTo(target) < 6.0) {
            Vec3 to = target.position().subtract(position()).multiply(1, 0, 1);
            behindTicks = to.lengthSqr() > 0.01 && to.normalize().dot(bodyForward()) < -0.25 ? behindTicks + 1 : 0;
            if (behindTicks >= Math.round(20 * cycleSpeed()) && wheelReady <= 0) {
                behindTicks = 0;
                wheelReady = (int) Math.round(80 * cooldownScale());
                chain(level, "wheel");
                return;
            }
        } else if (a != null) {
            behindTicks = 0;
        }
        if (phase() == 2 && phaseTwoTick >= 0 && tickCount - phaseTwoTick > 50 && free) {
            if (!phaseThree && getHealth() <= getMaxHealth() * PHASE_THREE_AT) {
                chain(level, "kneel");
            } else if (phaseThree && !shieldBroken && --kneelTimer <= 0) {
                chain(level, "kneel");
            } else if (shieldBroken && --tollTimer <= 0) {
                tollTimer = (int) Math.round(TOLL_EVERY * cooldownScale());
                chain(level, "toll");
            } else if (shieldBroken && --furyTimer <= 0 && distanceTo(target) < 7.0) {
                furyTimer = (int) Math.round(FURY_EVERY * cooldownScale());
                chain(level, "fury");
            }
        }
        // ambience: the oath light in his eyes, dust off the stone, the key's chain
        if (tickCount % 10 == 0) {
            Vec3 face = position().add(bodyForward().scale(0.6));
            level.sendParticles(OATH, face.x, getY() + 5.0, face.z, 1, 0.2, 0.05, 0.2, 0);
        }
        if (shieldBroken && tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX(), getY() + 3.0, getZ(), 1, 0.7, 1.2, 0.7, 0.01);
        }
        if (tickCount % 70 == 0) {
            level.playSound(null, this, SoundEvents.CHAIN_STEP, SoundSource.HOSTILE, 1.0F, 0.5F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        phaseTwoTick = tickCount;
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("oathbound_gatekeeper_toll"),
                    0.1, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0F, 0.5F);
        level.playSound(null, this, SoundEvents.BELL_RESONATE, SoundSource.HOSTILE, 4.0F, 0.5F);
        level.sendParticles(OATH, getX(), getY() + 3.0, getZ(), 60, 1.2, 1.8, 1.2, 0.05);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        clearShieldBar();
        level.sendParticles(dust(), getX(), getY() + 2.5, getZ(), 120, 1.4, 2.0, 1.4, 0.2);
        level.sendParticles(OATH, getX(), getY() + 3.0, getZ(), 60, 1.0, 2.0, 1.0, 0.1);
        level.sendParticles(GOLD, getX(), getY() + 1.5, getZ(), 30, 0.8, 0.8, 0.8, 0.1);
        level.playSound(null, this, SoundEvents.BELL_BLOCK, SoundSource.HOSTILE, 5.0F, 0.4F);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_DEATH, SoundSource.HOSTILE, 3.0F, 0.4F);
        level.playSound(null, this, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    @Override
    public void remove(RemovalReason reason) {
        clearShieldBar();
        super.remove(reason);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("OathBroken", shieldBroken);
        output.putBoolean("OathPhaseThree", phaseThree);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        shieldBroken = input.getBooleanOr("OathBroken", false);
        phaseThree = input.getBooleanOr("OathPhaseThree", false);
        entityData.set(DATA_BROKEN, shieldBroken);
    }

    // ------------------------------------------------------------------ geometry

    private static double flatDist(Vec3 a, Vec3 b) {
        return a.multiply(1, 0, 1).distanceTo(b.multiply(1, 0, 1));
    }

    /** Horizontal vector rotated by {@code degrees} around the vertical axis. */
    private static Vec3 rotate(Vec3 v, double degrees) {
        double r = Math.toRadians(degrees);
        double c = Math.cos(r);
        double s = Math.sin(r);
        Vec3 out = new Vec3(v.x * c - v.z * s, 0, v.x * s + v.z * c);
        return out.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : out.normalize();
    }

    /** Runs {@code inner} after {@code delay} ticks. */
    private static Effect delayed(int delay, Effect inner) {
        int[] t = {0};
        return (boss, level) -> t[0]++ >= delay && inner.tick(boss, level);
    }
}

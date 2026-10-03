package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModBlocks;
import com.wayfarers.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
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
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.WeepingLady.CLAW;
import static com.wayfarers.generated.MobAnims.WeepingLady.ERUPT;
import static com.wayfarers.generated.MobAnims.WeepingLady.RAKE;
import static com.wayfarers.generated.MobAnims.WeepingLady.ROAR;
import static com.wayfarers.generated.MobAnims.WeepingLady.STAGGER;
import static com.wayfarers.generated.MobAnims.WeepingLady.SUMMON;
import static com.wayfarers.generated.MobAnims.WeepingLady.SWOOP;
import static com.wayfarers.generated.MobAnims.WeepingLady.VEIL;
import static com.wayfarers.generated.MobAnims.WeepingLady.WAIL;

/**
 * La Dame en pleurs (The Weeping Lady): champion at the bottom of the Lithite Well, a 3.8-block banshee matriarch
 * veiled in lace, crowned with lithite, weeping crystal tears. She floats: her model hovers over the floor, she
 * glides down slowly (falling speed x0.7) and never takes fall damage.
 * <ul>
 *     <li><b>Phase 1</b> (300 hp): <i>claw</i> (12-tick raise, 70 degree rake, 12 dmg), <i>rake</i> (left/right combo
 *     at 11 and 20 ticks, 9 + 12 dmg), <i>wail</i> (18-tick wind-up with a soul cone on the floor, 11-block 40 degree
 *     cone: 10 dmg, Slowness II, Weakness, knockback, then a 1 s scream that pushes), <i>tear eruptions</i> (she
 *     weeps, then lithite spikes burst under every player and at 4 random spots 18 ticks later: 13 dmg + toss) and
 *     <i>summon</i> (2 banshees).</li>
 *     <li><b>Phase 2</b> (after a roar, +20% speed, 2 banshees at once): claw chains into rake, the wail pulses twice,
 *     eruptions add two expanding rings (5 blocks at 18 ticks, 9 blocks at 30 ticks), plus <i>blinding veil</i>
 *     (16-tick wind-up, Blindness 3 s + Darkness 5 s within 8 blocks, she reappears behind her target and claws) and
 *     <i>swoop</i> (5 to 16 blocks: a 14-tick lean back, then a gliding lunge, 13 dmg).</li>
 * </ul>
 */
public class WeepingLady extends WayfarerBoss {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 3.8F;
    private static final double WAIL_RANGE = 11.0;
    private static final double WAIL_HALF_ANGLE = 40.0;

    private final Set<UUID> swoopHits = new HashSet<>();
    private boolean blinked;

    public WeepingLady(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 380.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.WeepingLady.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.WHITE;
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
        return 65.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    // ------------------------------------------------------------------ private helpers

    /** Soul-fire outline of the wail cone on the floor (call during the wind-up). */
    private void drawCone(ServerLevel level) {
        Vec3 f = forward();
        float base = (float) (Mth.atan2(f.z, f.x) * Mth.RAD_TO_DEG);
        for (double a = -WAIL_HALF_ANGLE; a <= WAIL_HALF_ANGLE; a += 8) {
            double r = Math.toRadians(base + a);
            for (double d : new double[]{4.0, 7.5, WAIL_RANGE}) {
                if (d < WAIL_RANGE && Math.abs(a) < WAIL_HALF_ANGLE - 1) {
                    continue;
                }
                level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, getX() + Math.cos(r) * d, getY() + 0.15,
                        getZ() + Math.sin(r) * d, 1, 0, 0, 0, 0);
            }
        }
    }

    /** Everyone inside the wail cone (and in sight). */
    private List<LivingEntity> inCone(ServerLevel level) {
        Vec3 fwd = forward();
        double cos = Math.cos(Math.toRadians(WAIL_HALF_ANGLE));
        return victims(level, position(), WAIL_RANGE + 1).stream().filter(e -> {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            return d <= WAIL_RANGE + e.getBbWidth() / 2 && (d < 1.2 || to.normalize().dot(fwd) >= cos) && hasLineOfSight(e);
        }).toList();
    }

    private void wailPulse(ServerLevel level, float damage) {
        for (LivingEntity e : inCone(level)) {
            strike(level, e, damage, 1.6, 0.35);
            e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 1), this);
            e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 140, 0), this);
        }
        Vec3 fwd = forward();
        for (int i = 1; i <= 5; i++) {
            Vec3 p = position().add(fwd.scale(i * 2.0));
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, getY() + 3.0 - i * 0.35, p.z, 1, 0, 0, 0, 0);
        }
        level.playSound(null, this, SoundEvents.GHAST_SCREAM, SoundSource.HOSTILE, 3.0F, 0.75F);
        level.playSound(null, this, SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 3.0F, 0.5F);
    }

    /** A lithite tear-spike: mint warning motes on the floor, then crystals burst up (13 dmg, toss). */
    private static Effect tearSpike(Vec3 pos, int delay) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 3 == 0) {
                    level.sendParticles(ParticleTypes.GLOW, pos.x, pos.y + 0.1, pos.z, 4, 0.7, 0.02, 0.7, 0.0);
                    level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.1, pos.z, 1, 0.5, 0.0, 0.5, 0.0);
                }
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.8, pos.z, 24, 0.5, 1.2, 0.5, 0.08);
            level.sendParticles(ParticleTypes.GLOW, pos.x, pos.y + 1.0, pos.z, 20, 0.6, 1.0, 0.6, 0.1);
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 1.6F, 0.7F);
            for (LivingEntity e : boss.victims(level, pos, 1.8)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= 1.8) {
                    boss.strike(level, e, 13.0F, 0.3, 0.9);
                }
            }
            return true;
        };
    }

    /** Floor height under a point near the boss (eruptions sit on the arena floor). */
    private Vec3 onFloor(double x, double z) {
        return new Vec3(x, getY(), z);
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        out.add(BossAttack.of("claw").anim(CLAW).timing(12, 3, 13).range(0, 5.0).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.8, 70, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(0.6, 0.0);
                    b.hitArc(level, 5.0, 70, 12.0F, 1.0);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 2.0, p.z, 2, 1.0, 0.5, 1.0, 0);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.VEX_CHARGE, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "rake");
                    }
                })
                .build());
        out.add(BossAttack.of("rake").anim(RAKE).timing(11, 10, 13).range(0, 5.0).cooldown(70).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 4.6, 65, ParticleTypes.SOUL_FIRE_FLAME);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 4.8, 65, 9.0F, 0.4);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.7F);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 9) { // the second, heavier claw at 20 ticks
                        b.lunge(0.5, 0.0);
                        b.hitArc(level, 5.0, 70, 12.0F, 1.3);
                        Vec3 p = b.ahead(2.5);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 2.0, p.z, 2, 1.0, 0.5, 1.0, 0);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .build());
        out.add(BossAttack.of("wail").anim(WAIL).timing(18, 20, 10).range(0, WAIL_RANGE).cooldown(140).weight(8)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.GHAST_WARN, SoundSource.HOSTILE, 2.5F, 0.6F))
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        ((WeepingLady) b).drawCone(level);
                    }
                    level.sendParticles(ParticleTypes.SCULK_SOUL, b.getX(), b.getY() + 3.2, b.getZ(), 2, 0.4, 0.3, 0.4, 0.02);
                })
                .impact((b, level, t, tick) -> ((WeepingLady) b).wailPulse(level, 10.0F))
                .active((b, level, t, tick) -> {
                    WeepingLady w = (WeepingLady) b;
                    if (tick % 4 == 0) {
                        for (LivingEntity e : w.inCone(level)) { // the scream keeps pushing
                            Vec3 push = e.position().subtract(b.position()).multiply(1, 0, 1).normalize().scale(0.25);
                            e.push(push.x, 0, push.z);
                            e.hurtMarked = true;
                        }
                        Vec3 p = b.ahead(4 + tick * 0.3);
                        level.sendParticles(ParticleTypes.SCULK_SOUL, p.x, p.y + 1.5, p.z, 6, 1.5, 0.6, 1.5, 0.02);
                    }
                    if (b.phase() == 2 && tick == 10) {
                        w.wailPulse(level, 8.0F); // phase 2: the scream breaks a second time
                    }
                })
                .build());
        out.add(BossAttack.of("erupt").anim(ERUPT).timing(20, 2, 18).range(0, 22).cooldown(150).weight(8)
                .start((b, level, t, tick) -> level.playSound(null, b, SoundEvents.ALLAY_HURT, SoundSource.HOSTILE, 2.5F, 0.4F))
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) { // she weeps: crystal tears fall from her face
                        level.sendParticles(ParticleTypes.FALLING_WATER, b.getX(), b.getY() + 3.0, b.getZ(), 3, 0.3, 0.1, 0.3, 0);
                        level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 3.0, b.getZ(), 1, 0.3, 0.1, 0.3, 0.01);
                    }
                })
                .impact((b, level, t, tick) -> {
                    WeepingLady w = (WeepingLady) b;
                    for (LivingEntity e : b.victims(level, b.position(), 22)) {
                        b.addEffect(tearSpike(w.onFloor(e.getX(), e.getZ()), 18));
                    }
                    for (int i = 0; i < 4; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2;
                        double r = 3 + b.getRandom().nextDouble() * 7;
                        b.addEffect(tearSpike(w.onFloor(b.getX() + Math.cos(a) * r, b.getZ() + Math.sin(a) * r), 18));
                    }
                    if (b.phase() == 2) { // two rings of crystals ripple outward
                        for (int i = 0; i < 8; i++) {
                            double a = Math.PI * 2 * i / 8;
                            b.addEffect(tearSpike(w.onFloor(b.getX() + Math.cos(a) * 5, b.getZ() + Math.sin(a) * 5), 18));
                        }
                        for (int i = 0; i < 12; i++) {
                            double a = Math.PI * 2 * (i + 0.5) / 12;
                            b.addEffect(tearSpike(w.onFloor(b.getX() + Math.cos(a) * 9, b.getZ() + Math.sin(a) * 9), 30));
                        }
                    }
                    level.sendParticles(ParticleTypes.GLOW, b.getX(), b.getY() + 0.3, b.getZ(), 40, 2.0, 0.1, 2.0, 0.1);
                    level.playSound(null, b, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.5F);
                })
                .build());
        out.add(BossAttack.of("summon").anim(SUMMON).timing(12, 1, 23).range(0, 30).cooldown(500).weight(4)
                .impact((b, level, t, tick) -> {
                    b.summon(level, ModEntities.BANSHEE.get(), b.phase() == 2 ? 3 : 2, 4.0);
                    level.playSound(null, b, SoundEvents.GHAST_SCREAM, SoundSource.HOSTILE, 2.0F, 1.3F);
                })
                .build());
        out.add(BossAttack.of("veil").anim(VEIL).phaseTwo().timing(16, 2, 18).range(0, 10).cooldown(220).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 8.0, ParticleTypes.WHITE_ASH);
                    }
                    level.sendParticles(ParticleTypes.WHITE_ASH, b.getX(), b.getY() + 2.5, b.getZ(), 6, 0.8, 0.8, 0.8, 0.02);
                })
                .impact((b, level, t, tick) -> {
                    WeepingLady w = (WeepingLady) b;
                    for (LivingEntity e : b.victims(level, b.position(), 8.0)) {
                        e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), b);
                        e.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0), b);
                    }
                    level.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 2, b.getZ(), 60, 3.0, 1.5, 3.0, 0.15);
                    level.playSound(null, b, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 2.0F, 1.4F);
                    w.blinked = false;
                    if (t != null) { // fade away and reappear behind the target
                        Vec3 back = t.getLookAngle().multiply(1, 0, 1).normalize().scale(-2.8);
                        if (b.randomTeleport(t.getX() + back.x, t.getY(), t.getZ() + back.z, true)) {
                            w.blinked = true;
                            level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 2, b.getZ(), 30, 0.6, 1.2, 0.6, 0.05);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    if (((WeepingLady) b).blinked) {
                        b.chain(level, "claw");
                    }
                })
                .build());
        out.add(BossAttack.of("swoop").anim(SWOOP).phaseTwo().timing(14, 8, 10).range(5, 16).cooldown(90).weight(8)
                .start((b, level, t, tick) -> ((WeepingLady) b).swoopHits.clear())
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 12; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.5, 0.05);
                    level.playSound(null, b, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    WeepingLady w = (WeepingLady) b;
                    if (tick < 6) {
                        b.lunge(1.3, 0.0);
                    }
                    for (LivingEntity e : b.victims(level, b.position(), 2.6)) {
                        if (w.swoopHits.add(e.getUUID())) {
                            b.strike(level, e, 13.0F, 1.2, 0.3);
                        }
                    }
                    level.sendParticles(ParticleTypes.SOUL, b.getX(), b.getY() + 1.5, b.getZ(), 4, 0.6, 0.8, 0.6, 0.02);
                })
                .build());
    }

    // ------------------------------------------------------------------ ambience, phases

    @Override
    protected void bossTick(ServerLevel level) {
        Vec3 v = getDeltaMovement();
        if (!onGround() && v.y < 0) {
            setDeltaMovement(v.multiply(1.0, 0.7, 1.0)); // she glides, she does not fall
        }
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.FALLING_WATER, getX(), getY() + 3.0, getZ() - 0.3, 1, 0.15, 0, 0.15, 0);
            level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 0.3, getZ(), 1, 0.7, 0.1, 0.7, 0.01);
        }
        if (tickCount % 9 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 4.2, getZ(), 1, 0.3, 0.2, 0.3, 0.005);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("phase_two_speed"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        summon(level, ModEntities.BANSHEE.get(), 2, 5.0);
        level.playSound(null, this, SoundEvents.GHAST_SCREAM, SoundSource.HOSTILE, 3.0F, 0.6F);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3.5, getZ(), 80, 2.5, 2.0, 2.5, 0.1);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        BlockPos center = blockPosition();
        for (BlockPos pos : BlockPos.betweenClosed(center.offset(-40, -12, -40), center.offset(40, 12, 40))) {
            if (level.getBlockState(pos).is(ModBlocks.SEALED_BARS.get())) {
                level.destroyBlock(pos, false);
            }
        }
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 120, 1.5, 2.0, 1.5, 0.15);
        level.playSound(null, this, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 3.0F, 0.6F);
    }
}

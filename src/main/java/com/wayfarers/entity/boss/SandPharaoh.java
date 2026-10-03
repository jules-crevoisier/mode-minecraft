package com.wayfarers.entity.boss;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
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
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.SandPharaoh.BURROW;
import static com.wayfarers.generated.MobAnims.SandPharaoh.CURSE;
import static com.wayfarers.generated.MobAnims.SandPharaoh.FLAIL;
import static com.wayfarers.generated.MobAnims.SandPharaoh.FLURRY;
import static com.wayfarers.generated.MobAnims.SandPharaoh.HOOK;
import static com.wayfarers.generated.MobAnims.SandPharaoh.PILLARS;
import static com.wayfarers.generated.MobAnims.SandPharaoh.ROAR;
import static com.wayfarers.generated.MobAnims.SandPharaoh.SANDSTORM;
import static com.wayfarers.generated.MobAnims.SandPharaoh.SARCOPHAGUS;
import static com.wayfarers.generated.MobAnims.SandPharaoh.SCARABS;
import static com.wayfarers.generated.MobAnims.SandPharaoh.STAGGER;

/**
 * Le Pharaon ensablé (The Sand Pharaoh): boss of the Desert Oasis, waiting in the great burial hall under the tomb.
 * <ul>
 *     <li>Phase 1: flail lash (arc), crook hook (a line that drags you to him, sometimes followed by a lash),
 *     sand pillars (warned eruptions under every player), scarab swarm (a crawling cloud that hunts you plus
 *     silverfish), burrow (sinks into the floor and bursts out under you).</li>
 *     <li>Phase 2 (after a roar): faster, the lash chains into a second lash, pillars also run in a line, plus the
 *     curse (a glyph circle you must leave: weakness, hunger, slowness), the sandstorm (blinding pulses that drag
 *     you toward his grinding core), the falling sarcophagus (a real stone-and-gold lid dropped on you) and a
 *     four-blow crook-and-flail flurry.</li>
 * </ul>
 */
public class SandPharaoh extends WayfarerBoss {
    public static final float WIDTH = 2.0F;
    public static final float HEIGHT = 5.4F;

    private static final BlockParticleOption SAND_DUST = new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.SAND.defaultBlockState());
    private static final BlockParticleOption SAND_PILLAR = new BlockParticleOption(ParticleTypes.DUST_PILLAR, Blocks.SAND.defaultBlockState());
    private static final BlockParticleOption SAND_BLOCK = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.SAND.defaultBlockState());
    private static final DustParticleOptions SCARAB = new DustParticleOptions(0x1C3A30, 1.4F);
    private static final DustParticleOptions SCARAB_GOLD = new DustParticleOptions(0xD8A93A, 1.1F);
    private static final DustParticleOptions CURSE_GLYPH = new DustParticleOptions(0x3AF0D8, 1.6F);

    /** Victims caught by the crook's hook, pulled in on the yank. */
    private final List<LivingEntity> hooked = new ArrayList<>();
    /** Where the burrow ends (locked when he sinks). */
    private Vec3 burrowTo = Vec3.ZERO;
    /** Under the sand: no damage between these ticks. */
    private int submergedFrom = -1;
    private int submergedTo = -1;
    /** Target of the curse glyph (follows the victim during the wind-up). */
    private Vec3 curseAt = Vec3.ZERO;
    private Vec3 lidAt = Vec3.ZERO;

    public SandPharaoh(EntityType<? extends Monster> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.MOVEMENT_SPEED, 0.23)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.SandPharaoh.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.YELLOW;
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
        return 75.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // flail lash: the left arm rears behind the shoulder (0.75 s), then whips across a wide arc
        out.add(BossAttack.of("flail").anim(FLAIL).timing(15, 3, 12).range(0, 5.5).cooldown(30).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.0, 75, SAND_DUST);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.5, 80, 12.0F, 1.2);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.6F);
                    level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 1.5F, 0.7F);
                    Vec3 p = b.ahead(2.5);
                    level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 3, 1.5, 0.3, 1.5, 0);
                    level.sendParticles(SAND_BLOCK, p.x, p.y + 0.3, p.z, 30, 2.0, 0.2, 2.0, 0.1);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "flail_again");
                    }
                })
                .build());
        // the second lash of a phase 2 combo: same swing, no telegraph beyond the animation
        out.add(BossAttack.of("flail_again").anim(FLAIL).phaseTwo().timing(15, 3, 14).range(99, 100).cooldown(0).weight(1)
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 5.5, 80, 11.0F, 1.4);
                    level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.0F, 0.5F);
                    for (LivingEntity e : b.victims(level, b.position(), 6)) {
                        e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 0));
                    }
                })
                .build());
        // crook hook: drawn back (0.8 s), thrust in a long line, then the hook yanks whoever it caught
        out.add(BossAttack.of("hook").anim(HOOK).timing(16, 6, 10).range(3.0, 9.0).cooldown(70).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 2; i <= 8; i += 2) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(SAND_DUST, p.x, p.y + 0.2, p.z, 2, 0.2, 0, 0.2, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    self.hooked.clear();
                    Vec3 fwd = b.forward();
                    for (LivingEntity e : b.victims(level, b.position(), 9)) {
                        Vec3 to = e.position().subtract(b.position()).multiply(1, 0, 1);
                        double along = to.dot(fwd);
                        double side = to.subtract(fwd.scale(along)).length();
                        if (along >= 0 && along <= 8.5 && side <= 1.4 + e.getBbWidth() / 2) {
                            b.strike(level, e, 9.0F, 0, 0);
                            self.hooked.add(e);
                        }
                    }
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .active((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    if (tick == 3) {
                        for (LivingEntity e : self.hooked) {
                            Vec3 pull = b.position().subtract(e.position()).multiply(1, 0, 1);
                            double d = pull.length();
                            if (d > 2.0) {
                                pull = pull.normalize().scale(Math.min(1.6, 0.25 * d));
                                e.push(pull.x, 0.35, pull.z);
                                e.hurtMarked = true;
                            }
                            level.sendParticles(SAND_BLOCK, e.getX(), e.getY() + 1, e.getZ(), 20, 0.3, 0.5, 0.3, 0.1);
                        }
                        if (!self.hooked.isEmpty()) {
                            level.playSound(null, b, SoundEvents.CHAIN_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
                        }
                    }
                })
                .end((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    boolean caught = !self.hooked.isEmpty();
                    self.hooked.clear();
                    if (caught && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "flail");
                    }
                })
                .build());
        // sand pillars: the crook raised over the head (0.95 s) and driven into the floor; the sand answers under
        // every player around after a warning, and in phase 2 a running line of pillars follows
        out.add(BossAttack.of("pillars").anim(PILLARS).timing(19, 2, 19).range(0, 22).cooldown(130).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.ahead(1.5), 2.5, SAND_DUST);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 1.8F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    Vec3 c = b.ahead(1.5);
                    b.hitCircle(level, c, 2.5, 12.0F, 0.8, 0.4);
                    level.sendParticles(SAND_PILLAR, c.x, c.y + 0.2, c.z, 40, 1.2, 0.2, 1.2, 0.2);
                    level.playSound(null, b, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 2.0F, 0.6F);
                    int delay = b.phase() == 2 ? 14 : 18;
                    for (LivingEntity e : b.victims(level, b.position(), 22)) {
                        b.addEffect(sandPillar(ground(level, e.position()), delay, 1.7, 13.0F));
                    }
                    if (b.phase() == 2) {
                        for (int i = 1; i <= 6; i++) {
                            b.addEffect(sandPillar(ground(level, b.ahead(2.0 + i * 2.2)), 8 + i * 4, 1.5, 11.0F));
                        }
                    }
                })
                .build());
        // scarab swarm: arms flung wide (0.8 s), a black-gold swarm pours from the sun ring and crawls after the target
        out.add(BossAttack.of("scarabs").anim(SCARABS).timing(16, 4, 20).range(0, 26).cooldown(320).weight(5)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(SCARAB, b.getX(), b.getY() + 4.6, b.getZ(), 6, 1.2, 1.2, 0.4, 0.05);
                    if (tick % 5 == 0) {
                        level.playSound(null, b, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.summon(level, EntityTypes.SILVERFISH, b.phase() == 2 ? 4 : 3, 2.5);
                    b.addEffect(scarabSwarm(b.position().add(b.forward().scale(1.5)), b.phase() == 2 ? 140 : 110));
                    level.playSound(null, b, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .build());
        // burrow: sinks into the sand (0.8 s), the ground churns under the victim, he bursts out at 1.4 s
        out.add(BossAttack.of("burrow").anim(BURROW).timing(16, 12, 20).range(7.0, 26).cooldown(220).weight(7)
                .start((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    self.submergedFrom = b.tickCount + 12;
                    self.submergedTo = b.tickCount + 27;
                    level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .windup((b, level, t, tick) -> {
                    level.sendParticles(SAND_BLOCK, b.getX(), b.getY() + 0.2, b.getZ(), 12, 1.0, 0.1, 1.0, 0.15);
                    if (tick % 4 == 0) {
                        level.playSound(null, b, SoundEvents.SAND_FALL, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    Vec3 dest = t != null ? ground(level, t.position()) : b.position();
                    self.burrowTo = dest;
                    b.teleportTo(dest.x, dest.y, dest.z);
                })
                .active((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    Vec3 d = self.burrowTo;
                    if (tick < 11) {
                        b.telegraphRing(level, d, 3.0, SAND_DUST);
                        level.sendParticles(SAND_BLOCK, d.x, d.y + 0.1, d.z, 8, 1.2, 0.05, 1.2, 0.1);
                        if (tick % 3 == 0) {
                            level.playSound(null, d.x, d.y, d.z, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 1.5F, 0.5F);
                        }
                    } else if (tick == 11) {
                        b.hitCircle(level, d, 3.0, 15.0F, 0.8, 1.0);
                        level.sendParticles(SAND_PILLAR, d.x, d.y + 0.3, d.z, 80, 1.5, 0.5, 1.5, 0.3);
                        level.sendParticles(ParticleTypes.EXPLOSION, d.x, d.y + 1, d.z, 2, 0.5, 0.5, 0.5, 0);
                        level.playSound(null, d.x, d.y, d.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.5F, 0.7F);
                    }
                })
                .build());

        // ---------------------------------------------------------------- phase 2
        // curse: the flail points at the victim (0.9 s) and a glyph circle locks under them; whoever is still
        // inside when it closes is cursed (weakness, hunger, slowness) and hurt
        out.add(BossAttack.of("curse").anim(CURSE).phaseTwo().timing(18, 14, 12).range(0, 24).cooldown(200).weight(6)
                .windup((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    if (t != null) {
                        self.curseAt = ground(level, t.position());
                    }
                    if (tick % 2 == 0) {
                        b.telegraphRing(level, self.curseAt, 3.0, CURSE_GLYPH);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_BLINDNESS, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .active((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    Vec3 c = self.curseAt;
                    double r = 3.0 - tick * 0.15;
                    b.telegraphRing(level, c, Math.max(0.5, r), CURSE_GLYPH);
                    b.telegraphRing(level, c, 3.0, ParticleTypes.SOUL_FIRE_FLAME);
                    if (tick == 13) {
                        level.sendParticles(ParticleTypes.SOUL, c.x, c.y + 0.5, c.z, 40, 1.5, 0.8, 1.5, 0.05);
                        level.playSound(null, c.x, c.y, c.z, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 1.5F, 0.7F);
                        for (LivingEntity e : b.victims(level, c, 3.0)) {
                            if (e.position().multiply(1, 0, 1).distanceTo(c.multiply(1, 0, 1)) <= 3.0) {
                                b.strike(level, e, 8.0F, 0, 0.2);
                                e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 0));
                                e.addEffect(new MobEffectInstance(MobEffects.HUNGER, 200, 1));
                                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
                            }
                        }
                    }
                })
                .build());
        // sandstorm: arms raised (0.6 s), a storm turns around him for two seconds: blinding pulses, a pull toward
        // the grinding core, then a long punish window while the sand settles
        out.add(BossAttack.of("sandstorm").anim(SANDSTORM).phaseTwo().timing(12, 40, 14).range(0, 12).cooldown(260).weight(6)
                .windup((b, level, t, tick) -> {
                    b.telegraphRing(level, b.position(), 2.6, SAND_DUST);
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 11.0, SAND_DUST);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ELYTRA_FLYING, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .active((b, level, t, tick) -> {
                    double a0 = tick * 0.35;
                    for (int i = 0; i < 18; i++) {
                        double r = 1.5 + (i % 6) * 1.7;
                        double a = a0 + i * 2.1 + r * 0.2;
                        level.sendParticles(SAND_BLOCK, b.getX() + Math.cos(a) * r, b.getY() + 0.3 + (i % 4) * 0.9,
                                b.getZ() + Math.sin(a) * r, 2, 0.2, 0.2, 0.2, 0.05);
                    }
                    level.sendParticles(SAND_DUST, b.getX(), b.getY() + 3, b.getZ(), 10, 6.0, 2.0, 6.0, 0.02);
                    for (LivingEntity e : b.victims(level, b.position(), 12)) {
                        Vec3 to = b.position().subtract(e.position()).multiply(1, 0, 1);
                        if (to.length() > 1.0) {
                            Vec3 pull = to.normalize().scale(0.075);
                            Vec3 swirl = new Vec3(-to.z, 0, to.x).normalize().scale(0.04);
                            e.push(pull.x + swirl.x, 0, pull.z + swirl.z);
                            e.hurtMarked = true;
                        }
                        if (tick % 12 == 0) {
                            e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
                        }
                    }
                    if (tick % 8 == 0) {
                        b.hitCircle(level, b.position(), 2.8, 6.0F, 0.5, 0.2);
                        level.playSound(null, b, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .build());
        // sarcophagus: both arms call it from the sky (1.0 s) and pull it down: a real lid of sandstone and gold
        // falls on the victim's shadow (about a second to run), then a ring of sand rolls out
        out.add(BossAttack.of("sarcophagus").anim(SARCOPHAGUS).phaseTwo().timing(20, 2, 26).range(4.0, 24).cooldown(240).weight(6)
                .windup((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    if (t != null) {
                        self.lidAt = ground(level, t.position());
                    }
                    if (tick % 3 == 0) {
                        telegraphLid(level, self.lidAt, b.forward(), SAND_DUST);
                    }
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    SandPharaoh self = (SandPharaoh) b;
                    b.addEffect(fallingLid(level, self.lidAt, b.forward()));
                    level.playSound(null, b, SoundEvents.WITHER_SHOOT, SoundSource.HOSTILE, 1.5F, 0.5F);
                })
                .build());
        // flurry: crook, flail, crook, flail, a step forward with each blow (blows at 0.7 s, then every 0.35 s)
        out.add(BossAttack.of("flurry").anim(FLURRY).phaseTwo().timing(12, 24, 16).range(0, 5.5).cooldown(110).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphArc(level, 4.5, 60, SAND_DUST);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 7 == 2) {
                        boolean last = tick == 23;
                        b.lunge(0.35, 0.0);
                        b.hitArc(level, 4.8, 65, last ? 12.0F : 8.0F, last ? 1.5 : 0.5);
                        level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.8F, 0.6F + tick * 0.02F);
                        Vec3 p = b.ahead(2.2);
                        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.5, p.z, 1, 0, 0, 0, 0);
                        level.sendParticles(SAND_BLOCK, p.x, p.y + 0.2, p.z, 14, 1.2, 0.1, 1.2, 0.1);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private effects

    /** The floor under a point (up to 8 blocks down). */
    private static Vec3 ground(ServerLevel level, Vec3 p) {
        BlockPos pos = BlockPos.containing(p.x, p.y + 0.5, p.z);
        for (int i = 0; i < 9; i++) {
            if (level.getBlockState(pos.below()).blocksMotion()) {
                return new Vec3(p.x, pos.getY(), p.z);
            }
            pos = pos.below();
        }
        return p;
    }

    /** A warned sand eruption: dust swirls on the spot, then a pillar of sand throws the victim up. */
    private static Effect sandPillar(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                if (t[0] % 2 == 0) {
                    level.sendParticles(SAND_DUST, pos.x, pos.y + 0.1, pos.z, 5, radius * 0.5, 0.05, radius * 0.5, 0.01);
                    boss.telegraphRing(level, pos, radius, SAND_DUST);
                }
                if (t[0] == 0) {
                    level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.SAND_FALL, SoundSource.HOSTILE, 1.5F, 0.6F);
                }
                t[0]++;
                return false;
            }
            for (int i = 0; i < 6; i++) {
                level.sendParticles(SAND_PILLAR, pos.x, pos.y + 0.4 + i * 0.7, pos.z, 12, radius * 0.3, 0.3, radius * 0.3, 0.12);
            }
            level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 2.0F, 0.5F);
            for (LivingEntity e : boss.victims(level, pos, radius + 0.5)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                    boss.strike(level, e, damage, 0.2, 1.0);
                }
            }
            return true;
        };
    }

    /** The scarab swarm: a low crawling cloud that hunts the nearest victim and bites whoever it covers. */
    private static Effect scarabSwarm(Vec3 start, int life) {
        Vec3[] at = {start};
        int[] t = {0};
        return (boss, level) -> {
            t[0]++;
            LivingEntity prey = null;
            double best = 1e9;
            for (LivingEntity e : boss.victims(level, at[0], 24)) {
                double d = e.distanceToSqr(at[0]);
                if (d < best) {
                    best = d;
                    prey = e;
                }
            }
            if (prey != null) {
                Vec3 to = prey.position().subtract(at[0]).multiply(1, 0, 1);
                if (to.length() > 0.2) {
                    at[0] = at[0].add(to.normalize().scale(0.17));
                }
                at[0] = new Vec3(at[0].x, ground(level, new Vec3(at[0].x, prey.getY() + 1, at[0].z)).y, at[0].z);
            }
            Vec3 c = at[0];
            level.sendParticles(SCARAB, c.x, c.y + 0.25, c.z, 14, 0.9, 0.15, 0.9, 0.02);
            level.sendParticles(SCARAB_GOLD, c.x, c.y + 0.3, c.z, 3, 0.8, 0.2, 0.8, 0.02);
            if (t[0] % 10 == 0) {
                level.playSound(null, c.x, c.y, c.z, SoundEvents.SILVERFISH_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.5F + boss.getRandom().nextFloat() * 0.3F);
                for (LivingEntity e : boss.victims(level, c, 1.8)) {
                    if (e.position().multiply(1, 0, 1).distanceTo(c.multiply(1, 0, 1)) <= 1.6 && Math.abs(e.getY() - c.y) < 1.5) {
                        e.hurtServer(level, boss.damageSources().mobAttack(boss), 3.0F);
                        e.addEffect(new MobEffectInstance(MobEffects.POISON, 40, 0));
                    }
                }
            }
            return t[0] >= life;
        };
    }

    /** Outline of the sarcophagus lid (2 x 4 blocks along the boss's facing). */
    private static void telegraphLid(ServerLevel level, Vec3 c, Vec3 fwd, ParticleOptions particle) {
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        for (double u = -2.2; u <= 2.2; u += 0.55) {
            for (double s : new double[]{-1.3, 1.3}) {
                Vec3 p = c.add(fwd.scale(u)).add(side.scale(s));
                level.sendParticles(particle, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
        for (double s = -1.3; s <= 1.3; s += 0.45) {
            for (double u : new double[]{-2.2, 2.2}) {
                Vec3 p = c.add(fwd.scale(u)).add(side.scale(s));
                level.sendParticles(particle, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    /**
     * The falling sarcophagus lid: eight falling blocks (sandstone rim, gold and lapis heart) dropped from up to nine
     * blocks above the target. They are removed just before they land, so the arena floor is never changed; the
     * crash hurts everyone under the lid and rolls a ring of sand outward.
     */
    private static Effect fallingLid(ServerLevel level, Vec3 c, Vec3 fwd) {
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        int groundY = Mth.floor(c.y + 0.01);
        int height = 2;
        while (height < 9) {   // stay under the ceiling: every cell up the column must be open
            BlockPos probe = BlockPos.containing(c.x, groundY + height + 1, c.z);
            if (!level.getBlockState(probe).isAir()) {
                break;
            }
            height++;
        }
        List<FallingBlockEntity> lid = new ArrayList<>();
        List<BlockPos> cells = new ArrayList<>();
        Set<BlockPos> used = new HashSet<>();
        for (int u = -2; u <= 1; u++) {
            for (int s = -1; s <= 0; s++) {
                Vec3 p = c.add(fwd.scale(u + 0.5)).add(side.scale(s + 0.5));
                BlockPos pos = BlockPos.containing(p.x, groundY + height, p.z);
                if (!used.add(pos) || !level.getBlockState(pos).isAir()) {
                    continue;
                }
                boolean heart = (u == -1 || u == 0);
                BlockState state = heart ? (s == -1 ? Blocks.GOLD_BLOCK : Blocks.LAPIS_BLOCK).defaultBlockState()
                        : Blocks.CHISELED_SANDSTONE.defaultBlockState();
                FallingBlockEntity fb = FallingBlockEntity.fall(level, pos, state);
                fb.disableDrop();
                fb.time = 1;
                lid.add(fb);
                cells.add(pos);
            }
        }
        int[] t = {0};
        boolean[] crashed = {false};
        Set<UUID> hit = new HashSet<>();
        return (boss, lvl) -> {
            t[0]++;
            if (!crashed[0]) {
                telegraphLid(lvl, c, fwd, ParticleTypes.CRIT);
                boolean landing = t[0] > 40;
                for (FallingBlockEntity fb : lid) {
                    if (!fb.isAlive() || fb.getY() + fb.getDeltaMovement().y * 2.0 <= groundY + 0.2) {
                        landing = true;
                    }
                }
                if (!landing) {
                    return false;
                }
                crashed[0] = true;
                for (FallingBlockEntity fb : lid) {
                    fb.discard();
                }
                for (BlockPos cell : cells) {  // a lid block that slipped through anyway is cleared again
                    for (int dy = 0; dy <= 1; dy++) {
                        BlockPos p = new BlockPos(cell.getX(), groundY + dy, cell.getZ());
                        BlockState st = lvl.getBlockState(p);
                        if (st.is(Blocks.GOLD_BLOCK) || st.is(Blocks.LAPIS_BLOCK) || st.is(Blocks.CHISELED_SANDSTONE)) {
                            lvl.removeBlock(p, false);
                        }
                    }
                }
                lvl.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 4, 1.2, 0.3, 1.2, 0);
                lvl.sendParticles(SAND_PILLAR, c.x, c.y + 0.3, c.z, 120, 1.5, 0.4, 2.5, 0.3);
                lvl.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 2.5F, 0.4F);
                lvl.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 2.0F, 0.6F);
                for (LivingEntity e : boss.victims(lvl, c, 3.5)) {
                    Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                    double along = Math.abs(to.dot(fwd));
                    double across = Math.abs(to.dot(side));
                    if (along <= 2.6 && across <= 1.6 && hit.add(e.getUUID())) {
                        boss.strike(lvl, e, 20.0F, 0.6, 0.5);
                    }
                }
                boss.addEffect(WayfarerBoss.wave(c, 8, 0.4, 7.0F, SAND_PILLAR));
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ hooks

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (tickCount >= submergedFrom && tickCount <= submergedTo) {
            return false;   // under the sand
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    protected void bossTick(ServerLevel level) {
        int every = phase() == 2 ? 3 : 6;
        if (tickCount % every == 0) {
            // sand trickles from the torn wrappings; the sun ring smoulders
            level.sendParticles(SAND_DUST, getX(), getY() + 2.5, getZ(), 3, 0.6, 1.2, 0.6, 0.0);
            double a = tickCount * 0.12;
            level.sendParticles(ParticleTypes.SMALL_FLAME, getX() - forward().x * 0.8 + Math.cos(a) * 1.3, getY() + 4.9 + Math.sin(a) * 1.3,
                    getZ() - forward().z * 0.8, 1, 0, 0, 0, 0);
        }
        if (phase() == 2 && tickCount % 40 == 0) {
            level.playSound(null, this, SoundEvents.SAND_IDLE, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("sand_pharaoh_phase_two"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.sendParticles(SAND_PILLAR, getX(), getY() + 0.5, getZ(), 200, 4.0, 0.5, 4.0, 0.3);
        level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.2F, 0.7F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        level.sendParticles(SAND_PILLAR, getX(), getY() + 1, getZ(), 300, 1.5, 2.5, 1.5, 0.2);
        level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 4, getZ(), 40, 1.0, 1.0, 1.0, 0.05);
        level.playSound(null, this, SoundEvents.SAND_BREAK, SoundSource.HOSTILE, 3.0F, 0.4F);
    }
}

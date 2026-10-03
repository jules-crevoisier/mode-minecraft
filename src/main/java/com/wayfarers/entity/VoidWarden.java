package com.wayfarers.entity;

import com.wayfarers.boss.BossAttack;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ShulkerBullet;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static com.wayfarers.generated.MobAnims.VoidWarden.BLINK;
import static com.wayfarers.generated.MobAnims.VoidWarden.COMBO;
import static com.wayfarers.generated.MobAnims.VoidWarden.DIVE;
import static com.wayfarers.generated.MobAnims.VoidWarden.ORBS;
import static com.wayfarers.generated.MobAnims.VoidWarden.PULSE;
import static com.wayfarers.generated.MobAnims.VoidWarden.ROAR;
import static com.wayfarers.generated.MobAnims.VoidWarden.STAGGER;
import static com.wayfarers.generated.MobAnims.VoidWarden.STARRAIN;
import static com.wayfarers.generated.MobAnims.VoidWarden.SUMMON;
import static com.wayfarers.generated.MobAnims.VoidWarden.WAVES;
import static com.wayfarers.generated.MobAnims.VoidWarden.WELL;

/**
 * Gardien du vide (The Void Warden): the final boss, a void knight with a curved greatsword, guarding the Void
 * Nest on the outer End islands.
 * <ul>
 *     <li>Phase 1: three-cut sword combo with a delayed leaping overhead, blink strike (vanishes, reappears
 *     behind the target, cuts), levitation pulse, void orbs (homing shulker bullets), gravity well (pull, then
 *     implosion), void stalkers.</li>
 *     <li>Phase 2 (wings torn open): faster, the combo chains into a blink, aerial dive onto a marked spot,
 *     star rain (falling stars on and around every player), and void slash waves (two crescents along the floor,
 *     the second one re-aimed).</li>
 * </ul>
 */
public class VoidWarden extends WayfarerBoss {
    public static final float WIDTH = 1.8F;
    public static final float HEIGHT = 4.9F;

    private @Nullable Vec3 diveSpot;

    public VoidWarden(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 500;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 760.0)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0)
                .add(Attributes.STEP_HEIGHT, 1.5);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.VoidWarden.TICKS;
    }

    @Override
    protected BossEvent.BossBarColor barColor() {
        return BossEvent.BossBarColor.PURPLE;
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
        return 95.0F;
    }

    @Override
    protected double preferredRange() {
        return 3.5;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float multiplier, net.minecraft.world.damagesource.DamageSource source) {
        return false; // lands from its dives on purpose
    }

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // sword combo: right-to-left (0.6 s), backhand (1.1 s), a delayed leaping overhead (1.75 s)
        out.add(BossAttack.of("combo").anim(COMBO).timing(12, 24, 12).range(0, 5.5).cooldown(50).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphArc(level, 5.5, 85, ParticleTypes.REVERSE_PORTAL);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick == 0 || tick == 10) {
                        b.lunge(0.35, 0.0);
                        b.hitArc(level, 5.5, 85, tick == 0 ? 14.0F : 12.0F, 1.0);
                        slashFx(level, 2.5);
                    } else if (tick == 15) {
                        b.lunge(0.55, 0.35);   // the leap before the overhead
                    } else if (tick == 23) {
                        b.hitLine(level, 6.0, 1.4, 18.0F, 1.3);
                        Vec3 p = b.ahead(3.5);
                        level.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.3, p.z, 2, 0.6, 0.1, 0.6, 0);
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.3, p.z, 40, 1.2, 0.2, 1.2, 0.2);
                        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.4F, 0.7F);
                    } else if (tick > 15 && tick < 23 && tick % 2 == 0) {
                        Vec3 p = b.ahead(3.5);
                        b.telegraphRing(level, p, 1.4, ParticleTypes.END_ROD);
                    }
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && t != null && b.getRandom().nextFloat() < 0.4F) {
                        b.chain(level, "blink");
                    }
                })
                .build());
        // blink strike: dissolves, reappears behind the target and cuts down (impact 0.75 s)
        out.add(BossAttack.of("blink").anim(BLINK).timing(15, 3, 14).range(2.5, 22).cooldown(110).weight(8)
                .start((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.PORTAL, b.getX(), b.getY() + 2, b.getZ(), 60, 0.6, 1.5, 0.6, 0.4);
                    level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.0F, 0.6F);
                })
                .windup((b, level, t, tick) -> {
                    if (tick == 6 && t != null) {
                        Vec3 look = t.getLookAngle().multiply(1, 0, 1);
                        if (look.lengthSqr() < 1.0E-4) {
                            look = t.position().subtract(b.position()).multiply(1, 0, 1);
                        }
                        Vec3 dest = t.position().subtract(look.normalize().scale(3.0));
                        if (!b.randomTeleport(dest.x, t.getY(), dest.z, false)) {
                            b.randomTeleport(t.getX() + (b.getRandom().nextBoolean() ? 3 : -3), t.getY(), t.getZ(), false);
                        }
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 2, b.getZ(), 60, 0.6, 1.5, 0.6, 0.2);
                        level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.0F, 0.9F);
                    }
                    if (tick > 6 && tick % 2 == 0) {
                        b.telegraphArc(level, 4.5, 70, ParticleTypes.END_ROD);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitArc(level, 4.8, 70, 16.0F, 1.2);
                    slashFx(level, 2.2);
                })
                .build());
        // levitation pulse: plants the sword, the void heaves everyone around into the air (impact 0.9 s)
        out.add(BossAttack.of("pulse").anim(PULSE).timing(18, 4, 16).range(0, 8.5).cooldown(170).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        b.telegraphRing(level, b.position(), 8.0, ParticleTypes.END_ROD);
                        level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX(), b.getY() + 0.2, b.getZ(), 20, 3.0, 0.1, 3.0, 0.05);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.ILLUSIONER_PREPARE_BLINDNESS, SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 8.0, 9.0F, 0.4, 0.3);
                    for (LivingEntity e : b.victims(level, b.position(), 8.0)) {
                        if (e.distanceTo(b) <= 8.5) {
                            e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, b.phase() == 2 ? 40 : 30, 0), b);
                        }
                    }
                    for (int r = 2; r <= 8; r += 2) {
                        b.telegraphRing(level, b.position().add(0, 0.5, 0), r, ParticleTypes.REVERSE_PORTAL);
                    }
                    level.playSound(null, this, SoundEvents.SHULKER_BULLET_HIT, SoundSource.HOSTILE, 3.0F, 0.5F);
                    level.playSound(null, this, SoundEvents.END_PORTAL_FRAME_FILL, SoundSource.HOSTILE, 2.5F, 0.5F);
                })
                .end((b, level, t, tick) -> {
                    if (b.phase() == 2 && b.getRandom().nextFloat() < 0.5F) {
                        b.chain(level, "orbs");   // the floating are easy prey
                    }
                })
                .build());
        // void orbs: the free hand conjures homing orbs (cast at 0.8 s)
        out.add(BossAttack.of("orbs").anim(ORBS).timing(16, 2, 14).range(5.0, 28).cooldown(120).weight(8)
                .windup((b, level, t, tick) -> {
                    Vec3 h = handPos();
                    level.sendParticles(ParticleTypes.WITCH, h.x, h.y, h.z, 3, 0.3, 0.3, 0.3, 0.02);
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.EVOKER_PREPARE_ATTACK, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    List<Player> players = foes(level);
                    int count = b.phase() == 2 ? 5 : 3;
                    for (int i = 0; i < count && !players.isEmpty(); i++) {
                        Player p = players.get(i % players.size());
                        ShulkerBullet orb = new ShulkerBullet(level, b, p, Direction.Axis.values()[i % 3]);
                        level.addFreshEntity(orb);
                    }
                    level.playSound(null, this, SoundEvents.SHULKER_SHOOT, SoundSource.HOSTILE, 2.5F, 0.6F);
                })
                .build());
        // gravity well: drives the sword into the floor; the void pulls everything in, then implodes
        out.add(BossAttack.of("well").anim(WELL).timing(17, 27, 12).range(0, 13).cooldown(230).weight(6)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 12.0, ParticleTypes.PORTAL);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.hitCircle(level, b.position(), 2.5, 10.0F, 0.5, 0.3);
                    level.playSound(null, this, SoundEvents.END_PORTAL_SPAWN, SoundSource.HOSTILE, 1.5F, 1.4F);
                })
                .active((b, level, t, tick) -> {
                    double strength = 0.06 + tick * 0.002;
                    for (LivingEntity e : b.victims(level, b.position(), 14)) {
                        Vec3 pull = b.position().subtract(e.position()).multiply(1, 0, 1);
                        if (pull.length() > 1.5) {
                            pull = pull.normalize().scale(strength);
                            e.push(pull.x, 0, pull.z);
                            e.hurtMarked = true;
                        }
                    }
                    if (tick % 2 == 0) {
                        double a = tick * 0.6;
                        for (int i = 0; i < 6; i++) {
                            double r = 12.0 - (tick % 12);
                            double ang = a + i * Math.PI / 3;
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX() + Math.cos(ang) * r, b.getY() + 0.3,
                                    b.getZ() + Math.sin(ang) * r, 2, 0.1, 0.1, 0.1, 0.0);
                        }
                        b.telegraphRing(level, b.position(), 4.5, ParticleTypes.WITCH);
                    }
                    if (tick == 26) {
                        b.hitCircle(level, b.position(), 4.5, 16.0F, 1.8, 0.6);
                        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, b.getX(), b.getY() + 1, b.getZ(), 1, 0, 0, 0, 0);
                        level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 1, b.getZ(), 60, 2.0, 1.0, 2.0, 0.3);
                        level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.5F, 0.6F);
                    }
                })
                .build());
        // void stalkers step out of the dark around it
        out.add(BossAttack.of("summon").anim(SUMMON).timing(12, 2, 22).range(0, 30).cooldown(520).weight(4)
                .windup((b, level, t, tick) -> {
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.summon(level, ModEntities.VOID_STALKER.get(), b.phase() == 2 ? 3 : 2, 4.5);
                    level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .build());
        // ---- phase 2
        // aerial dive: wings open, it rises, marks a spot under the target and plunges sword-first (1.75 s)
        out.add(BossAttack.of("dive").anim(DIVE).phaseTwo().timing(35, 3, 14).range(6.0, 24).cooldown(150).weight(8)
                .windup((b, level, t, tick) -> {
                    if (tick == 10) {
                        b.setNoGravity(true);
                        b.setDeltaMovement(0, 0.95, 0);
                        b.hurtMarked = true;
                        level.playSound(null, this, SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 3.0F, 0.7F);
                    } else if (tick > 10 && tick < 30) {
                        b.setDeltaMovement(b.getDeltaMovement().scale(0.75));
                        b.hurtMarked = true;
                    }
                    if (tick == 18 && t != null) {
                        diveSpot = t.position();
                    }
                    if (diveSpot != null && tick >= 18 && tick % 2 == 0) {
                        b.telegraphRing(level, diveSpot, 4.0, ParticleTypes.END_ROD);
                    }
                    if (tick == 30 && diveSpot != null) {
                        Vec3 v = diveSpot.subtract(b.position()).scale(0.2);
                        b.setDeltaMovement(v);
                        b.hurtMarked = true;
                        level.playSound(null, this, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 3.0F, 0.5F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.setNoGravity(false);
                    Vec3 c = diveSpot != null ? diveSpot : b.position();
                    b.teleportTo(c.x, c.y, c.z);
                    b.setDeltaMovement(Vec3.ZERO);
                    b.hitCircle(level, c, 4.0, 20.0F, 1.5, 0.6);
                    b.addEffect(WayfarerBoss.wave(c, 10, 0.5, 9.0F, ParticleTypes.REVERSE_PORTAL));
                    level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y + 0.5, c.z, 1, 0, 0, 0, 0);
                    level.sendParticles(ParticleTypes.END_ROD, c.x, c.y + 0.5, c.z, 50, 2.0, 0.5, 2.0, 0.25);
                    level.playSound(null, this, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0F, 0.6F);
                    diveSpot = null;
                })
                .build());
        // star rain: sword to the sky; stars fall on and around every player (cast at 0.9 s)
        out.add(BossAttack.of("starrain").anim(STARRAIN).phaseTwo().timing(18, 24, 10).range(0, 30).cooldown(210).weight(7)
                .windup((b, level, t, tick) -> {
                    if (tick % 2 == 0) {
                        level.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + 6, b.getZ(), 4, 0.3, 1.5, 0.3, 0.1);
                    }
                    if (tick == 0) {
                        level.playSound(null, this, SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 3.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> {
                    for (Player p : foes(level)) {
                        b.addEffect(starfall(p.position(), 18, 2.0, 13.0F));
                        for (int i = 0; i < 4; i++) {
                            double a = b.getRandom().nextDouble() * Math.PI * 2;
                            double r = 2.5 + b.getRandom().nextDouble() * 3.5;
                            b.addEffect(starfall(p.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 22 + i * 5, 2.0, 11.0F));
                        }
                    }
                })
                .build());
        // void slash waves: two crescents race along the floor (0.7 s, then 1.3 s re-aimed)
        out.add(BossAttack.of("waves").anim(WAVES).phaseTwo().timing(14, 13, 15).range(3.0, 20).cooldown(100).weight(9)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (double s = 2; s <= 18; s += 2) {
                            Vec3 p = b.ahead(s);
                            level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.addEffect(slashWave(b.position().add(0, 0.1, 0), b.forward(), 20, 13.0F));
                    slashFx(level, 2.5);
                })
                .active((b, level, t, tick) -> {
                    if (tick == 12) {
                        Vec3 dir = t != null ? t.position().subtract(b.position()).multiply(1, 0, 1) : b.forward();
                        if (dir.lengthSqr() < 1.0E-4) {
                            dir = b.forward();
                        }
                        b.addEffect(slashWave(b.position().add(0, 0.1, 0), dir.normalize(), 20, 13.0F));
                        slashFx(level, 2.5);
                    }
                })
                .build());
    }

    // ------------------------------------------------------------------ private helpers

    private List<Player> foes(ServerLevel level) {
        return level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(28, 12, 28),
                p -> p.isAlive() && !p.isCreative() && !p.isSpectator());
    }

    private Vec3 handPos() {
        float yaw = getYRot() * Mth.DEG_TO_RAD;
        Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
        return position().add(left.scale(0.9)).add(0, 4.2, 0);
    }

    private void slashFx(ServerLevel level, double dist) {
        Vec3 p = ahead(dist);
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.6, p.z, 3, 1.4, 0.3, 1.4, 0);
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 1.6, p.z, 20, 1.4, 0.4, 1.4, 0.05);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 2.5F, 0.5F);
    }

    /** A crescent of void that races along the floor and cuts whoever it crosses (jump or sidestep). */
    private static Effect slashWave(Vec3 start, Vec3 dir, double length, float damage) {
        Set<UUID> hit = new HashSet<>();
        double[] s = {1.0};
        Vec3 side = new Vec3(-dir.z, 0, dir.x);
        return (boss, level) -> {
            s[0] += 0.9;
            Vec3 c = start.add(dir.scale(s[0]));
            for (double w = -2.0; w <= 2.0; w += 0.5) {
                double back = 0.35 * w * w;   // crescent: the tips trail behind
                Vec3 p = c.add(side.scale(w)).subtract(dir.scale(back));
                level.sendParticles(ParticleTypes.REVERSE_PORTAL, p.x, p.y + 0.3, p.z, 1, 0.05, 0.2, 0.05, 0.0);
                if (Math.abs(w) < 1.1) {
                    level.sendParticles(ParticleTypes.END_ROD, p.x, p.y + 0.5, p.z, 1, 0.05, 0.1, 0.05, 0.0);
                }
            }
            for (LivingEntity e : boss.victims(level, c, 3.0)) {
                Vec3 to = e.position().subtract(c).multiply(1, 0, 1);
                double along = to.dot(dir);
                double across = to.dot(side);
                if (Math.abs(along) < 1.0 && Math.abs(across) < 2.2 && e.getY() - c.y < 1.2 && hit.add(e.getUUID())) {
                    boss.strike(level, e, damage, 0.9, 0.3);
                }
            }
            return s[0] >= length;
        };
    }

    /** A falling star: a shaft of light descends for {@code delay} ticks, then bursts where it lands. */
    private static Effect starfall(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            if (t[0] < delay) {
                double y = pos.y + 14.0 * (1.0 - (double) t[0] / delay);
                level.sendParticles(ParticleTypes.END_ROD, pos.x, y, pos.z, 2, 0.1, 0.2, 0.1, 0.0);
                if (t[0] % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, ParticleTypes.REVERSE_PORTAL);
                }
                t[0]++;
                return false;
            }
            level.sendParticles(ParticleTypes.END_ROD, pos.x, pos.y + 0.5, pos.z, 30, radius * 0.4, 0.8, radius * 0.4, 0.2);
            level.sendParticles(ParticleTypes.EXPLOSION, pos.x, pos.y + 0.5, pos.z, 1, 0, 0, 0, 0);
            level.playSound(null, BlockPos.containing(pos), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 2.0F, 0.5F);
            level.playSound(null, BlockPos.containing(pos), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.8F, 1.4F);
            for (LivingEntity e : boss.victims(level, pos, radius)) {
                if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                    boss.strike(level, e, damage, 0.6, 0.5);
                }
            }
            return true;
        };
    }

    // ------------------------------------------------------------------ ambience, phase change

    @Override
    protected void bossTick(ServerLevel level) {
        BossAttack a = currentAttack();
        if (isNoGravity() && (a == null || !a.name.equals("dive"))) {
            setNoGravity(false);   // a dive cut short by a stagger or a reset
            diveSpot = null;
        }
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.REVERSE_PORTAL, getX(), getY() + 2.5, getZ(), 2, 0.6, 1.4, 0.6, 0.01);
        }
        if (phase() == 2 && tickCount % 6 == 0) {
            level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 4.6, getZ(), 1, 0.8, 0.4, 0.8, 0.01);
        }
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.wayfarers.Wayfarers.id("phase_two_speed"), 0.2,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        level.playSound(null, this, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 2.0F, 0.8F);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 3, getZ(), 120, 3.0, 2.0, 3.0, 0.3);
        summon(level, ModEntities.VOID_STALKER.get(), 2, 5.0);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        setNoGravity(false);
        level.sendParticles(ParticleTypes.END_ROD, getX(), getY() + 2, getZ(), 200, 2.0, 2.0, 2.0, 0.2);
        level.playSound(null, this, SoundEvents.ENDER_DRAGON_DEATH, SoundSource.HOSTILE, 1.5F, 1.2F);
    }
}

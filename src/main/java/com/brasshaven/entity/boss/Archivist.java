package com.brasshaven.entity.boss;

import com.brasshaven.boss.BossAttack;
import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.entity.MapWraith;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ItemParticleOption;
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
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.List;

import static com.brasshaven.generated.MobAnims.Archivist.BARRAGE;
import static com.brasshaven.generated.MobAnims.Archivist.BLINK;
import static com.brasshaven.generated.MobAnims.Archivist.INK_POOL;
import static com.brasshaven.generated.MobAnims.Archivist.INK_STORM;
import static com.brasshaven.generated.MobAnims.Archivist.MIRROR;
import static com.brasshaven.generated.MobAnims.Archivist.QUILL_STAB;
import static com.brasshaven.generated.MobAnims.Archivist.ROAR;
import static com.brasshaven.generated.MobAnims.Archivist.STAGGER;
import static com.brasshaven.generated.MobAnims.Archivist.SUMMON;
import static com.brasshaven.generated.MobAnims.Archivist.VOLLEY;

/**
 * L'Archiviste (The Archivist), boss of the Forgotten Library's Forbidden Archive: a spectral scholar of parchment
 * and ink that hovers above the floor, keeps its distance and fights with what it has written.
 * <ul>
 *     <li>Phase 1: page volleys (a fan of homing pages), ink pools that erupt under the target and blind, a quill
 *     lunge, a blink away when cornered, and map wraiths called out of the margins.</li>
 *     <li>Phase 2: the ink storm (a spinning spiral of pages and ink rain), book barrages (three fast bursts),
 *     mirror images (two ink phantoms that fire with it; find the real one), wider volleys and more pools.</li>
 * </ul>
 * It moves on its own: no pathfinding, a gentle hover at {@link #HOVER} blocks above the floor, drifting to keep
 * mid range and strafing around its target. When its posture breaks it sinks to the floor.
 */
public class Archivist extends WayfarerBoss {
    public static final float WIDTH = 1.6F;
    public static final float HEIGHT = 4.2F;
    private static final double HOVER = 0.9;
    private static final int MAX_WRAITHS = 4;

    private static final ParticleOptions INK = new DustParticleOptions(0x1C1830, 1.8F);
    private static final ParticleOptions RUNE = new DustParticleOptions(0x78E8FF, 1.0F);
    private static @Nullable ParticleOptions page;

    /** Flying paper bits (built on first use, once the item registry is surely ready). */
    private static ParticleOptions page() {
        if (page == null) {
            page = new ItemParticleOption(ParticleTypes.ITEM, Items.PAPER);
        }
        return page;
    }

    private @Nullable BlockPos arenaCenter;
    private int arenaRadius = 16;
    private int strafe = 1;

    public Archivist(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 360.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ARMOR_TOUGHNESS, 2.0)
                .add(Attributes.ATTACK_DAMAGE, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 48.0);
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Archivist.TICKS;
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
        return 55.0F;
    }

    @Override
    protected double preferredRange() {
        return 8.0;
    }

    /** No pathfinding goal: {@link #hover} moves the Archivist itself. */
    @Override
    protected void registerGoals() {
        goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 16.0F));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public void setArena(BlockPos center, int radius, @Nullable BlockPos sealPos) {
        super.setArena(center, radius, sealPos);
        arenaCenter = center.immutable();
        arenaRadius = radius;
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        long h = input.getLongOr("BossHome", Long.MIN_VALUE);
        arenaCenter = h == Long.MIN_VALUE ? null : BlockPos.of(h);
        arenaRadius = input.getIntOr("BossArena", 16);
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    // ------------------------------------------------------------------ moveset

    @Override
    protected void defineAttacks(List<BossAttack> out) {
        // volley: the tomes drawn in, then thrust open: a fan of homing pages
        out.add(BossAttack.of("volley").anim(VOLLEY).timing(14, 2, 10).range(3.0, 26).cooldown(40).weight(12)
                .windup((b, level, t, tick) -> {
                    if (tick % 4 == 0) {
                        fanTelegraph(b, level, b.phase() == 2 ? 7 : 5, 12);
                    }
                    tomeSparks(b, level);
                    if (tick == 2) {
                        level.playSound(null, b, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 2.0F, 0.6F);
                    }
                })
                .impact((b, level, t, tick) -> volley(b, level, t, b.phase() == 2 ? 7 : 5, 12, 0.7, 0.035, 8.0F))
                .build());
        // ink pool: the quill slashes the floor; ink wells up under the target and bursts (blinding)
        out.add(BossAttack.of("ink_pool").anim(INK_POOL).timing(16, 2, 14).range(0, 20).cooldown(70).weight(10)
                .start((b, level, t, tick) -> {
                    if (t == null) {
                        return;
                    }
                    int pools = b.phase() == 2 ? 4 : 2;
                    b.addEffect(inkPool(t.position(), 22, 2.2, 11.0F));
                    for (int i = 0; i < pools; i++) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2, r = 2.5 + b.getRandom().nextDouble() * 3.0;
                        b.addEffect(inkPool(t.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 26 + i * 4, 2.0, 10.0F));
                    }
                    level.playSound(null, b, SoundEvents.SQUID_SQUIRT, SoundSource.HOSTILE, 2.0F, 0.5F);
                })
                .impact((b, level, t, tick) -> level.playSound(null, b, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE,
                        1.5F, 1.4F))
                .build());
        // quill stab: the great quill levelled and driven forward in a long lunge
        out.add(BossAttack.of("quill_stab").anim(QUILL_STAB).timing(12, 4, 10).range(2.0, 9.0).cooldown(50).weight(10)
                .windup((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        for (int i = 1; i <= 8; i++) {
                            Vec3 p = b.ahead(i);
                            level.sendParticles(ParticleTypes.ENCHANTED_HIT, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
                        }
                    }
                })
                .impact((b, level, t, tick) -> {
                    b.lunge(1.2, 0.0);
                    b.hitLine(level, 8.0, 1.0, 14.0F, 1.0);
                    level.playSound(null, b, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 2.0F, 1.2F);
                    level.sendParticles(INK, b.getX(), b.getY() + 1.5, b.getZ(), 20, 0.5, 0.5, 0.5, 0);
                })
                .build());
        // blink: folds into its pages when cornered and unfolds far away; the pages it leaves behind cut
        out.add(BossAttack.of("blink").anim(BLINK).timing(10, 2, 14).range(0, 4.5).cooldown(100).weight(9)
                .windup((b, level, t, tick) -> b.telegraphRing(level, b.position(), 2.5, RUNE))
                .impact((b, level, t, tick) -> {
                    Vec3 from = b.position();
                    b.hitCircle(level, from, 2.6, 7.0F, 0.9, 0.3);
                    level.sendParticles(page(), from.x, from.y + 2, from.z, 40, 0.8, 1.2, 0.8, 0.15);
                    ((Archivist) b).blinkAway(level, t, 9.0 + b.getRandom().nextDouble() * 3.0);
                })
                .build());
        // summon: every arm raised; map wraiths step out of the margins
        out.add(BossAttack.of("summon").anim(SUMMON).timing(18, 2, 18).range(0, 30).cooldown(400).weight(5)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.ENCHANT, b.getX(), b.getY() + 3, b.getZ(), 6, 1.5, 1.0, 1.5, 0.5);
                    if (tick % 4 == 0) {
                        b.telegraphRing(level, b.position(), 3.5, RUNE);
                    }
                })
                .impact((b, level, t, tick) -> ((Archivist) b).callWraiths(level, b.phase() == 2 ? 3 : 2))
                .build());

        // ---------------------------------------------------------- phase 2
        // ink storm: a spinning spiral of pages and a rain of ink pools around the target
        out.add(BossAttack.of("ink_storm").anim(INK_STORM).phaseTwo().timing(16, 28, 12).range(0, 14).cooldown(200).weight(7)
                .windup((b, level, t, tick) -> {
                    b.telegraphRing(level, b.position(), 4.0 + tick * 0.4, INK);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_BLINDNESS, SoundSource.HOSTILE, 2.0F, 0.7F);
                    }
                })
                .active((b, level, t, tick) -> {
                    if (tick % 3 == 0) {
                        double a = Math.toRadians(tick * 26.0);
                        for (int k = 0; k < 3; k++) {
                            double ak = a + k * Math.PI * 2 / 3;
                            Vec3 dir = new Vec3(Math.cos(ak), 0, Math.sin(ak));
                            b.addEffect(new Page(b.position().add(0, 2.6, 0).add(dir.scale(1.2)), dir.scale(0.5), null, 7.0F, 0, 50));
                        }
                        level.playSound(null, b, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 1.5F, 0.8F + tick * 0.02F);
                    }
                    if (t != null && tick % 7 == 0) {
                        double a = b.getRandom().nextDouble() * Math.PI * 2, r = b.getRandom().nextDouble() * 4.0;
                        b.addEffect(inkPool(t.position().add(Math.cos(a) * r, 0, Math.sin(a) * r), 16, 2.0, 10.0F));
                    }
                    level.sendParticles(ParticleTypes.SQUID_INK, b.getX(), b.getY() + 1.5, b.getZ(), 6, 2.0, 1.0, 2.0, 0.05);
                })
                .build());
        // barrage: three fast bursts from alternating tomes
        out.add(BossAttack.of("barrage").anim(BARRAGE).phaseTwo().timing(12, 13, 11).range(4.0, 26).cooldown(60).weight(11)
                .windup((b, level, t, tick) -> {
                    tomeSparks(b, level);
                    if (tick % 4 == 0) {
                        fanTelegraph(b, level, 3, 8);
                    }
                })
                .impact((b, level, t, tick) -> volley(b, level, t, 3, 8, 0.9, 0.03, 7.0F))
                .active((b, level, t, tick) -> {
                    if (tick == 6 || tick == 12) {
                        volley(b, level, t, 3, 8, 0.95, 0.03, 7.0F);
                    }
                })
                .build());
        // mirror: two ink phantoms split away; all three fire a volley, only one can be hurt
        out.add(BossAttack.of("mirror").anim(MIRROR).phaseTwo().timing(16, 2, 14).range(0, 20).cooldown(240).weight(7)
                .windup((b, level, t, tick) -> {
                    level.sendParticles(ParticleTypes.SQUID_INK, b.getX(), b.getY() + 2, b.getZ(), 4, 0.6, 1.0, 0.6, 0.02);
                    if (tick == 0) {
                        level.playSound(null, b, SoundEvents.ILLUSIONER_PREPARE_MIRROR, SoundSource.HOSTILE, 2.0F, 0.8F);
                    }
                })
                .impact((b, level, t, tick) -> ((Archivist) b).mirror(level, t))
                .end((b, level, t, tick) -> b.chain(level, "volley"))
                .build());
    }

    // ------------------------------------------------------------------ attacks

    /** Fan of page projectiles from the two tomes toward the target. */
    private static void volley(WayfarerBoss b, ServerLevel level, @Nullable LivingEntity t, int count, double spreadDeg,
                               double speed, double homing, float damage) {
        Vec3 fwd = b.forward();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        Vec3 aim = t != null ? t.position().add(0, t.getBbHeight() * 0.6, 0) : b.ahead(10).add(0, 1.5, 0);
        for (int i = 0; i < count; i++) {
            Vec3 origin = b.position().add(0, 3.0, 0).add(side.scale(i % 2 == 0 ? 1.4 : -1.4)).add(fwd.scale(0.8));
            Vec3 dir = aim.subtract(origin).normalize();
            double off = Math.toRadians((i - (count - 1) / 2.0) * spreadDeg);
            dir = new Vec3(dir.x * Math.cos(off) - dir.z * Math.sin(off), dir.y, dir.x * Math.sin(off) + dir.z * Math.cos(off));
            b.addEffect(new Page(origin, dir.scale(speed), t, damage, homing, 60));
        }
        level.playSound(null, b, SoundEvents.BOOK_PUT, SoundSource.HOSTILE, 2.0F, 0.5F);
        level.playSound(null, b, SoundEvents.EVOKER_CAST_SPELL, SoundSource.HOSTILE, 1.5F, 1.3F);
    }

    /** Wind-up telegraph: the fan of lines the pages will follow, drawn on the floor. */
    private static void fanTelegraph(WayfarerBoss b, ServerLevel level, int count, double spreadDeg) {
        LivingEntity t = b.getTarget();
        Vec3 to = t != null ? t.position().subtract(b.position()).multiply(1, 0, 1).normalize() : b.forward();
        for (int i = 0; i < count; i++) {
            double off = Math.toRadians((i - (count - 1) / 2.0) * spreadDeg);
            Vec3 dir = new Vec3(to.x * Math.cos(off) - to.z * Math.sin(off), 0, to.x * Math.sin(off) + to.z * Math.cos(off));
            for (int d = 2; d <= 8; d += 2) {
                Vec3 p = b.position().add(dir.scale(d));
                level.sendParticles(RUNE, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
            }
        }
    }

    private static void tomeSparks(WayfarerBoss b, ServerLevel level) {
        Vec3 fwd = b.forward();
        Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
        for (int s = -1; s <= 1; s += 2) {
            Vec3 p = b.position().add(0, 3.0, 0).add(side.scale(1.4 * s)).add(fwd.scale(0.6));
            level.sendParticles(ParticleTypes.ENCHANT, p.x, p.y, p.z, 3, 0.3, 0.3, 0.3, 0.6);
        }
    }

    /** An ink pool: wells up for {@code delay} ticks, bursts (damage + blindness), then lingers and slows. */
    private static Effect inkPool(Vec3 pos, int delay, double radius, float damage) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            if (k < delay) {
                if (k % 3 == 0) {
                    boss.telegraphRing(level, pos, radius, INK);
                    level.sendParticles(ParticleTypes.SQUID_INK, pos.x, pos.y + 0.1, pos.z, 3, radius * 0.4, 0.02, radius * 0.4, 0.01);
                }
                return false;
            }
            if (k == delay) {
                level.sendParticles(ParticleTypes.SQUID_INK, pos.x, pos.y + 0.6, pos.z, 50, radius * 0.4, 1.2, radius * 0.4, 0.15);
                level.sendParticles(ParticleTypes.GLOW_SQUID_INK, pos.x, pos.y + 0.6, pos.z, 8, radius * 0.4, 1.0, radius * 0.4, 0.05);
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.GLOW_SQUID_SQUIRT, SoundSource.HOSTILE, 2.0F, 0.6F);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius) {
                        boss.strike(level, e, damage, 0.2, 0.8);
                        e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), boss);
                    }
                }
                return false;
            }
            if (k % 5 == 0) { // the spilled ink lingers and clings to the feet
                level.sendParticles(INK, pos.x, pos.y + 0.1, pos.z, 6, radius * 0.45, 0.01, radius * 0.45, 0);
                for (LivingEntity e : boss.victims(level, pos, radius)) {
                    if (e.position().multiply(1, 0, 1).distanceTo(pos.multiply(1, 0, 1)) <= radius && e.getY() - pos.y < 0.6) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 25, 0), boss);
                    }
                }
            }
            return k >= delay + 70;
        };
    }

    /** Called from {@code summon}: map wraiths, never more than {@link #MAX_WRAITHS} at once. */
    private void callWraiths(ServerLevel level, int wanted) {
        int alive = level.getEntitiesOfClass(MapWraith.class, getBoundingBox().inflate(40),
                w -> w.isAlive() && w.entityTags().contains(MINION_TAG)).size();
        int n = Math.min(wanted, MAX_WRAITHS - alive);
        if (n > 0) {
            summon(level, ModEntities.MAP_WRAITH.get(), n, 4.0);
        }
        level.playSound(null, this, SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.HOSTILE, 2.0F, 0.7F);
        level.playSound(null, this, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 2.0F, 0.4F);
    }

    /** Teleport to a spot about {@code dist} blocks from the target (or from itself), inside the arena. */
    private void blinkAway(ServerLevel level, @Nullable LivingEntity target, double dist) {
        Vec3 around = target != null ? target.position() : position();
        for (int attempt = 0; attempt < 12; attempt++) {
            double a = random.nextDouble() * Math.PI * 2;
            Vec3 spot = findSpot(level, around.add(Math.cos(a) * dist, 0, Math.sin(a) * dist));
            if (spot != null) {
                teleportTo(spot.x, spot.y + HOVER, spot.z);
                level.sendParticles(page(), spot.x, spot.y + 2, spot.z, 40, 0.8, 1.2, 0.8, 0.15);
                level.playSound(null, this, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.5F, 0.6F);
                return;
            }
        }
    }

    /** Two ink phantoms appear 120 degrees apart around the target; the real Archivist takes one of the 3 places. */
    private void mirror(ServerLevel level, @Nullable LivingEntity target) {
        Vec3 around = target != null ? target.position() : position();
        Vec3 rel = position().subtract(around).multiply(1, 0, 1);
        double r = Math.max(6.0, Math.min(10.0, rel.length()));
        double base = Math.atan2(rel.z, rel.x);
        int real = random.nextInt(3);
        for (int i = 0; i < 3; i++) {
            double a = base + i * Math.PI * 2 / 3;
            Vec3 spot = findSpot(level, around.add(Math.cos(a) * r, 0, Math.sin(a) * r));
            if (spot == null) {
                continue;
            }
            if (i == real) {
                teleportTo(spot.x, spot.y + HOVER, spot.z);
            } else {
                addEffect(phantom(spot.add(0, HOVER, 0), target, 30));
            }
            level.sendParticles(page(), spot.x, spot.y + 2, spot.z, 25, 0.6, 1.0, 0.6, 0.12);
        }
        level.playSound(null, this, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.0F, 0.8F);
    }

    /** An ink phantom: a column of ink and runes shaped like the Archivist that fires one volley and dissolves. */
    private static Effect phantom(Vec3 pos, @Nullable LivingEntity target, int fireAt) {
        int[] t = {0};
        return (boss, level) -> {
            int k = t[0]++;
            level.sendParticles(ParticleTypes.SQUID_INK, pos.x, pos.y + 1.6, pos.z, 4, 0.35, 0.9, 0.35, 0.01);
            level.sendParticles(INK, pos.x, pos.y + 2.0, pos.z, 6, 0.6, 1.3, 0.6, 0);
            level.sendParticles(RUNE, pos.x, pos.y + 3.6, pos.z, 2, 0.25, 0.25, 0.25, 0);
            if (k == fireAt && target != null && target.isAlive()) {
                Vec3 aim = target.position().add(0, target.getBbHeight() * 0.6, 0);
                for (int i = -1; i <= 1; i++) {
                    Vec3 origin = pos.add(0, 3.0, 0);
                    Vec3 dir = aim.subtract(origin).normalize();
                    double off = Math.toRadians(i * 10.0);
                    dir = new Vec3(dir.x * Math.cos(off) - dir.z * Math.sin(off), dir.y, dir.x * Math.sin(off) + dir.z * Math.cos(off));
                    boss.addEffect(new Page(origin, dir.scale(0.7), target, 7.0F, 0.03, 60));
                }
                level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.BOOK_PUT, SoundSource.HOSTILE, 2.0F, 0.5F);
            }
            if (k >= fireAt + 4) {
                level.sendParticles(ParticleTypes.SQUID_INK, pos.x, pos.y + 2, pos.z, 30, 0.6, 1.2, 0.6, 0.1);
                return true;
            }
            return false;
        };
    }

    /** A free spot on the arena floor near {@code p} (x, floor y, z), or null. */
    private @Nullable Vec3 findSpot(ServerLevel level, Vec3 p) {
        if (arenaCenter != null) {
            Vec3 c = Vec3.atBottomCenterOf(arenaCenter);
            Vec3 off = p.subtract(c).multiply(1, 0, 1);
            double max = Math.max(3, arenaRadius - 3);
            if (off.length() > max) {
                p = c.add(off.normalize().scale(max));
            }
        }
        BlockPos start = BlockPos.containing(p.x, getY() + 3, p.z);
        for (int dy = 0; dy < 10; dy++) {
            BlockPos floor = start.below(dy);
            if (level.getBlockState(floor).blocksMotion() && !level.getBlockState(floor.above()).blocksMotion()
                    && !level.getBlockState(floor.above(2)).blocksMotion() && !level.getBlockState(floor.above(3)).blocksMotion()
                    && !level.getBlockState(floor.above(4)).blocksMotion()) {
                return new Vec3(p.x, floor.getY() + 1, p.z);
            }
        }
        return null;
    }

    // ------------------------------------------------------------------ hover movement, ambience

    @Override
    protected void bossTick(ServerLevel level) {
        hover(level);
        if (tickCount % 3 == 0) {
            level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 0.2, getZ(), 1, 0.2, 0.1, 0.2, 0.0);
            level.sendParticles(RUNE, getX(), getY() + 2.4, getZ(), 1, 0.8, 0.8, 0.8, 0.0);
        }
        if (tickCount % 12 == 0) {
            level.sendParticles(ParticleTypes.ENCHANT, getX(), getY() + 4.2, getZ(), 4, 0.6, 0.4, 0.6, 0.4);
        }
        if (phase() == 2 && tickCount % 5 == 0) {
            level.sendParticles(page(), getX(), getY() + 2.0, getZ(), 1, 1.4, 1.2, 1.4, 0.02);
        }
    }

    /**
     * Floats {@link #HOVER} blocks over the floor with a slow bob (sinks to the floor while staggered); between
     * moves it drifts to mid range of its target and circles it, turning to face it.
     */
    private void hover(ServerLevel level) {
        double floor = floorBelow(level);
        double wantY = isStaggered() ? floor : floor + HOVER + 0.25 * Math.sin(tickCount * 0.07);
        double vy = Mth.clamp((wantY - getY()) * 0.2, -0.3, 0.25);
        Vec3 v = getDeltaMovement();
        double vx = v.x * 0.8, vz = v.z * 0.8;   // lunges and blinks glide to a halt instead of sailing off
        LivingEntity t = getTarget();
        if (currentAttack() == null && !isStaggered() && t != null && t.isAlive()) {
            Vec3 to = t.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            Vec3 dir = d > 1.0E-3 ? to.scale(1.0 / d) : Vec3.ZERO;
            Vec3 side = new Vec3(-dir.z, 0, dir.x).scale(strafe);
            double approach = d > 11 ? 0.13 : d < 6 ? -0.09 : 0.0;
            double pace = phase() == 2 ? 1.3 : 1.0;
            Vec3 move = dir.scale(approach).add(side.scale(0.05)).scale(pace);
            if (arenaCenter != null) { // never drift out of the arena: lean back toward the centre near the wall
                Vec3 out = position().subtract(Vec3.atBottomCenterOf(arenaCenter)).multiply(1, 0, 1);
                if (out.length() > arenaRadius - 4) {
                    move = move.subtract(out.normalize().scale(0.08));
                    strafe = -strafe;
                }
            }
            vx = move.x;
            vz = move.z;
            if (random.nextInt(90) == 0) {
                strafe = -strafe;
            }
            float yaw = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90.0F;
            setYRot(Mth.approachDegrees(getYRot(), yaw, 12.0F));
            yBodyRot = getYRot();
            yHeadRot = getYRot();
            getLookControl().setLookAt(t, 30.0F, 30.0F);
        }
        setDeltaMovement(vx, vy, vz);
    }

    /** Y of the first solid floor under the Archivist (within 12 blocks), or its own feet. */
    private double floorBelow(ServerLevel level) {
        BlockPos p = BlockPos.containing(getX(), getY() + 0.5, getZ());
        for (int i = 0; i < 12; i++) {
            BlockPos q = p.below(i);
            if (level.getBlockState(q).blocksMotion()) {
                return q.getY() + 1.0;
            }
        }
        return getY();
    }

    @Override
    protected void onPhaseTwo(ServerLevel level) {
        var speed = getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.addOrReplacePermanentModifier(new AttributeModifier(com.brasshaven.Brasshaven.id("archivist_fury"), 0.3,
                    AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
        }
        callWraiths(level, 2);
        for (int i = 0; i < 16; i++) { // the halo bursts: a ring of pages flies out in every direction
            double a = Math.PI * 2 * i / 16;
            Vec3 dir = new Vec3(Math.cos(a), 0, Math.sin(a));
            addEffect(new Page(position().add(0, 2.8, 0).add(dir.scale(1.2)), dir.scale(0.45), null, 6.0F, 0, 40));
        }
        level.playSound(null, this, SoundEvents.ILLUSIONER_CAST_SPELL, SoundSource.HOSTILE, 3.0F, 0.6F);
    }

    @Override
    protected void onDefeated(ServerLevel level) {
        for (MapWraith w : level.getEntitiesOfClass(MapWraith.class, getBoundingBox().inflate(48),
                w -> w.entityTags().contains(MINION_TAG))) {
            level.sendParticles(page(), w.getX(), w.getY() + 1, w.getZ(), 20, 0.3, 0.6, 0.3, 0.1);
            w.discard();
        }
        level.sendParticles(page(), getX(), getY() + 2, getZ(), 120, 1.5, 2.0, 1.5, 0.25);
        level.sendParticles(ParticleTypes.SQUID_INK, getX(), getY() + 1, getZ(), 60, 1.0, 1.5, 1.0, 0.1);
        level.playSound(null, this, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 3.0F, 0.3F);
    }

    // ------------------------------------------------------------------ the page projectile

    /**
     * A flying page: particles only (paper bits and enchanting glyphs), optionally homing a little; hits the first
     * victim it touches, crumbles on walls.
     */
    private static final class Page implements Effect {
        private Vec3 pos;
        private Vec3 vel;
        private final @Nullable LivingEntity target;
        private final float damage;
        private final double homing;
        private int life;

        Page(Vec3 pos, Vec3 vel, @Nullable LivingEntity target, float damage, double homing, int life) {
            this.pos = pos;
            this.vel = vel;
            this.target = target;
            this.damage = damage;
            this.homing = homing;
            this.life = life;
        }

        @Override
        public boolean tick(WayfarerBoss boss, ServerLevel level) {
            if (target != null && homing > 0 && target.isAlive()) {
                Vec3 want = target.position().add(0, target.getBbHeight() * 0.6, 0).subtract(pos).normalize().scale(vel.length());
                vel = vel.add(want.subtract(vel).scale(homing));
            }
            Vec3 next = pos.add(vel);
            if (level.getBlockState(BlockPos.containing(next)).blocksMotion()) {
                level.sendParticles(page(), pos.x, pos.y, pos.z, 6, 0.1, 0.1, 0.1, 0.08);
                return true;
            }
            pos = next;
            level.sendParticles(page(), pos.x, pos.y, pos.z, 2, 0.08, 0.08, 0.08, 0.01);
            level.sendParticles(RUNE, pos.x, pos.y, pos.z, 1, 0.05, 0.05, 0.05, 0);
            for (LivingEntity e : boss.victims(level, pos, 1.5)) {
                if (e.getBoundingBox().inflate(0.3).contains(pos)) {
                    boss.strike(level, e, damage, 0.35, 0.1);
                    level.sendParticles(ParticleTypes.ENCHANTED_HIT, pos.x, pos.y, pos.z, 8, 0.2, 0.2, 0.2, 0.2);
                    return true;
                }
            }
            return --life <= 0;
        }
    }
}

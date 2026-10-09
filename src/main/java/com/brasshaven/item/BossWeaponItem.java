package com.brasshaven.item;

import com.brasshaven.util.Targets;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * A weapon forged from a boss's Remembrance. Its right-click ability is one of a few shapes (ring, beam, dash,
 * eruptions, snare, poison cloud, leap, sweep, blink, chain hook, halo shards, frost breath, breaking tide, pressure vent, cannon broadside), tuned per weapon by power, size, particle and flags.
 * Abilities only ever hurt non-player creatures.
 */
public class BossWeaponItem extends AbilityItem {
    public enum Ability { WAVE, BEAM, DASH, ERUPT, ROOT, CLOUD, LEAP, ARC, BLINK, HOOK, SHARDS, BREATH, RIFT, WARD, TEMPEST, TIDE, JET, PRESSURE, MIRE, PLUMB, BROADSIDE, PRISM, CAGE, SCARAB, MAGNET, TONGS, ZENITH, FUSE, DRAGON, SHRIEK, GRAPPLE, STOKE, REWIND }

    public static final int FIRE = 1;
    public static final int SLOW = 2;
    public static final int WEAK = 4;
    public static final int BLIND = 8;
    public static final int POISON = 16;
    public static final int LIFT = 32;
    public static final int LIFESTEAL = 64;

    private final Ability ability;
    private final float power;
    private final float size;
    private final ParticleOptions particle;
    private final int flags;

    public BossWeaponItem(Properties properties, Ability ability, float power, float size, int cooldown,
                          ParticleOptions particle, int flags) {
        super(properties, cooldown, 3);
        this.ability = ability;
        this.power = power;
        this.size = size;
        this.particle = particle;
        this.flags = flags;
    }

    @Override
    public void facts(ItemStack stack, List<net.minecraft.network.chat.Component> facts,
                      List<net.minecraft.network.chat.Component> details) {
        String shape = ability.name().toLowerCase(java.util.Locale.ROOT);
        boolean radius = switch (ability) {
            case WAVE, ROOT, CLOUD, LEAP, ARC, WARD, TEMPEST, PRESSURE, MAGNET -> true;
            default -> false;
        };
        facts.add(BrassTooltip.heading(net.minecraft.network.chat.Component.translatable("tooltip.brasshaven.ability",
                net.minecraft.network.chat.Component.translatable("tooltip.brasshaven.ability." + shape))));
        facts.add(BrassTooltip.rule(net.minecraft.network.chat.Component.translatable("tooltip.brasshaven.ability.stats",
                BrassTooltip.number(power),
                net.minecraft.network.chat.Component.translatable(radius ? "tooltip.brasshaven.ability.radius"
                        : "tooltip.brasshaven.ability.range", BrassTooltip.number(size)),
                BrassTooltip.seconds(cooldownTicks()))));
        String[] names = {"fire", "slow", "weak", "blind", "poison", "lift", "lifesteal"};
        net.minecraft.network.chat.MutableComponent effects = null;
        for (int bit = 0; bit < names.length; bit++) {
            if ((flags & (1 << bit)) != 0) {
                net.minecraft.network.chat.Component e = net.minecraft.network.chat.Component.translatable(
                        "tooltip.brasshaven.ability.effect." + names[bit]);
                effects = effects == null ? e.copy() : effects.append(", ").append(e);
            }
        }
        if (effects != null) {
            details.add(BrassTooltip.detail(net.minecraft.network.chat.Component.translatable("tooltip.brasshaven.ability.effects", effects)));
        }
        details.add(BrassTooltip.detail(net.minecraft.network.chat.Component.translatable("tooltip.brasshaven.ability.foes")));
    }

    private static List<LivingEntity> foes(ServerLevel level, Player player, AABB box) {
        return level.getEntitiesOfClass(LivingEntity.class, box, e -> Targets.foe(player, e));
    }

    private void hit(ServerLevel level, Player player, LivingEntity e, float damage, double knock) {
        if (e.hurtServer(level, level.damageSources().playerAttack(player), damage)) {
            Vec3 push = e.position().subtract(player.position()).multiply(1, 0, 1).normalize().scale(knock);
            e.push(push.x, (flags & LIFT) != 0 ? 0.9 : 0.2, push.z);
            e.hurtMarked = true;
            if ((flags & FIRE) != 0) {
                e.igniteForSeconds(5.0F);
            }
            if ((flags & SLOW) != 0) {
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
            }
            if ((flags & WEAK) != 0) {
                e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 120, 1));
            }
            if ((flags & BLIND) != 0) {
                e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
            }
            if ((flags & POISON) != 0) {
                e.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1));
            }
            if ((flags & LIFESTEAL) != 0) {
                player.heal(damage * 0.25F);
            }
        }
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        Vec3 look = player.getLookAngle();
        Vec3 flat = look.multiply(1, 0, 1).normalize();
        Vec3 origin = player.position();
        switch (ability) {
            case WAVE -> {
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    if (e.distanceTo(player) <= size) {
                        hit(level, player, e, power, 1.2);
                    }
                }
                ring(level, origin, size);
                level.playSound(null, player, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.7F, 0.8F);
            }
            case BEAM -> {
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                for (int i = 1; i <= reach; i++) {
                    Vec3 p = eye.add(look.scale(i));
                    level.sendParticles(particle, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0.0);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.0))) {
                        hit(level, player, e, power, 0.4);
                    }
                }
                level.playSound(null, player, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 0.8F, 1.3F);
            }
            case DASH -> {
                Vec3 v = flat.scale(size * 0.32);
                player.setDeltaMovement(v.x, 0.15, v.z);
                player.hurtMarked = true;
                for (int i = 1; i <= size; i++) {
                    Vec3 p = origin.add(flat.scale(i));
                    level.sendParticles(particle, p.x, p.y + 1, p.z, 3, 0.3, 0.4, 0.3, 0.0);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.2, 1.5, 1.2))) {
                        hit(level, player, e, power, 0.6);
                    }
                }
                level.playSound(null, player, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.0F, 1.4F);
            }
            case ERUPT -> {
                for (int i = 2; i <= size; i += 2) {
                    Vec3 p = origin.add(flat.scale(i));
                    level.sendParticles(particle, p.x, p.y + 0.5, p.z, 20, 0.5, 1.0, 0.5, 0.05);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.5, 2, 1.5))) {
                        hit(level, player, e, power, 0.2);
                        e.push(0, 0.7, 0);
                    }
                }
                level.playSound(null, player, SoundEvents.EVOKER_FANGS_ATTACK, SoundSource.PLAYERS, 1.0F, 0.8F);
            }
            case ROOT -> {
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    hit(level, player, e, power, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 5));
                    level.sendParticles(particle, e.getX(), e.getY() + 0.5, e.getZ(), 15, 0.4, 0.6, 0.4, 0.02);
                }
                ring(level, origin, size);
                level.playSound(null, player, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.PLAYERS, 1.5F, 0.6F);
            }
            case CLOUD -> {
                BlockHitResult hitResult = level.clip(new ClipContext(player.getEyePosition(),
                        player.getEyePosition().add(look.scale(12)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
                Vec3 at = hitResult.getType() == HitResult.Type.MISS ? player.getEyePosition().add(look.scale(12)) : hitResult.getLocation();
                AreaEffectCloud cloud = new AreaEffectCloud(level, at.x, at.y, at.z);
                cloud.setOwner(player);
                cloud.setRadius(size);
                cloud.setDuration(120);
                cloud.setRadiusPerTick(-size / 140.0F);
                // the cloud is only the look: poison goes to foes directly, never to the wielder or friends
                level.addFreshEntity(cloud);
                for (LivingEntity e : foes(level, player, new AABB(at, at).inflate(size, 2, size))) {
                    hit(level, player, e, power, 0.0);
                    e.addEffect(new MobEffectInstance(MobEffects.POISON, 120, 1), player);
                }
                level.playSound(null, player, SoundEvents.SPLASH_POTION_BREAK, SoundSource.PLAYERS, 1.0F, 0.7F);
            }
            case LEAP -> {
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    hit(level, player, e, power, 1.5);
                }
                Vec3 v = flat.scale(1.4);
                player.setDeltaMovement(v.x, 0.9, v.z);
                player.hurtMarked = true;
                player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 40, 0));
                ring(level, origin, size);
                level.playSound(null, player, SoundEvents.PHANTOM_FLAP, SoundSource.PLAYERS, 1.5F, 0.8F);
            }
            case ARC -> {
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    Vec3 to = e.position().subtract(origin).multiply(1, 0, 1);
                    if (to.length() <= size && (to.length() < 1 || to.normalize().dot(flat) > 0.2)) {
                        hit(level, player, e, power, 1.0);
                    }
                }
                for (int a = -70; a <= 70; a += 10) {
                    double r = Math.toRadians(a);
                    Vec3 d = new Vec3(flat.x * Math.cos(r) - flat.z * Math.sin(r), 0, flat.x * Math.sin(r) + flat.z * Math.cos(r));
                    Vec3 p = origin.add(d.scale(size * 0.7));
                    level.sendParticles(particle, p.x, p.y + 1.1, p.z, 3, 0.2, 0.2, 0.2, 0.01);
                }
                level.playSound(null, player, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.2F, 0.6F);
            }
            case BLINK -> {
                BlockHitResult hitResult = level.clip(new ClipContext(player.getEyePosition(),
                        player.getEyePosition().add(flat.scale(size)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
                Vec3 target = hitResult.getLocation().subtract(flat.scale(1.0));
                level.sendParticles(particle, player.getX(), player.getY() + 1, player.getZ(), 30, 0.4, 0.8, 0.4, 0.1);
                player.teleportTo(target.x, player.getY(), target.z);
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(3.5, 2, 3.5))) {
                    hit(level, player, e, power, 1.0);
                }
                level.sendParticles(particle, target.x, player.getY() + 1, target.z, 30, 0.4, 0.8, 0.4, 0.1);
                level.playSound(null, player, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1.0F, 0.8F);
            }
            case HOOK -> {
                // the Chained Jailer's chain: thrown along the look line (stops on walls), the first foe it meets is
                // hurt and dragged to the wielder's feet
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                LivingEntity caught = null;
                double best = reach + 1;
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
                    double along = to.dot(look);
                    if (along > 0 && along <= reach && to.subtract(look.scale(along)).length() <= 0.9 + e.getBbWidth() / 2
                            && along < best) {
                        caught = e;
                        best = along;
                    }
                }
                double shown = caught != null ? best : reach;
                for (double d = 1; d <= shown; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.3, 0);
                    level.sendParticles(d % 1.0 == 0 ? particle : net.minecraft.core.particles.ParticleTypes.CRIT,
                            p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                }
                level.playSound(null, player, SoundEvents.CHAIN_BREAK, SoundSource.PLAYERS, 1.2F, 0.6F);
                if (caught != null) {
                    hit(level, player, caught, power, 0.0);
                    Vec3 pull = origin.add(flat.scale(1.5)).subtract(caught.position()).multiply(1, 0, 1);
                    double dist = pull.length();
                    Vec3 v = dist > 0.1 ? pull.normalize().scale(Math.min(2.2, 0.3 + dist * 0.16)) : Vec3.ZERO;
                    caught.setDeltaMovement(v.x, 0.4, v.z);
                    caught.hurtMarked = true;
                    level.sendParticles(particle, caught.getX(), caught.getY() + 1, caught.getZ(), 20, 0.3, 0.5, 0.3, 0.05);
                    level.playSound(null, caught, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.5F, 0.5F);
                }
            }
            case WARD -> {
                // the Oathbound Gatekeeper's key: turned in the floor, stone hands punch up in a ring of eight around
                // the wielder (each throws its foes up), and the oath wards the wielder (Resistance II, 4 s)
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    if (e.distanceTo(player) <= size) {
                        hit(level, player, e, power, 0.6);
                    }
                }
                var stone = new net.minecraft.core.particles.BlockParticleOption(net.minecraft.core.particles.ParticleTypes.BLOCK,
                        net.minecraft.world.level.block.Blocks.CALCITE.defaultBlockState());
                for (int k = 0; k < 8; k++) {
                    double r = Math.PI * 2 * k / 8;
                    for (double d : new double[]{size * 0.45, size * 0.9}) {
                        Vec3 p = origin.add(Math.cos(r + d * 0.2) * d, 0, Math.sin(r + d * 0.2) * d);
                        level.sendParticles(stone, p.x, p.y + 0.6, p.z, 8, 0.25, 0.6, 0.25, 0.1);
                        level.sendParticles(particle, p.x, p.y + 1.2, p.z, 2, 0.2, 0.3, 0.2, 0.01);
                    }
                }
                player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 80, 1));
                ring(level, origin, size);
                level.playSound(null, player, SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 1.2F, 0.6F);
                level.playSound(null, player, SoundEvents.STONE_BREAK, SoundSource.PLAYERS, 1.2F, 0.6F);
            }
            case SHARDS -> {
                // the Fallen Seraph's halo shards: a fan of five piercing lines along the look direction (each stops on
                // walls), every foe they pass through is hurt once
                Vec3 eye = player.getEyePosition();
                java.util.Set<LivingEntity> hitOnce = new java.util.HashSet<>();
                for (int k = -2; k <= 2; k++) {
                    double r = Math.toRadians(k * 9.0);
                    Vec3 dir = new Vec3(look.x * Math.cos(r) - look.z * Math.sin(r), look.y,
                            look.x * Math.sin(r) + look.z * Math.cos(r)).normalize();
                    BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(dir.scale(size)), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                    for (double d = 1; d <= reach; d += 0.75) {
                        Vec3 p = eye.add(dir.scale(d)).add(0, -0.2, 0);
                        level.sendParticles(particle, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                        for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(0.8))) {
                            if (hitOnce.add(e)) {
                                hit(level, player, e, power, 0.3);
                            }
                        }
                    }
                }
                level.playSound(null, player, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 1.2F, 1.3F);
            }
            case BREATH -> {
                // the Frost Jarl's breath: a cone of frost (35 degrees each side of the look line, stopped by walls at
                // its centre); every foe inside is hurt and frozen solid for 2 s
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye) + 1.0;
                double cos = Math.cos(Math.toRadians(35));
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
                    double d = to.length();
                    if (d <= reach && d > 0.1 && to.normalize().dot(look) >= cos) {
                        hit(level, player, e, power, 0.3);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 6));
                        e.setTicksFrozen(Math.max(e.getTicksFrozen(), e.getTicksRequiredToFreeze() + 100));
                        level.sendParticles(net.minecraft.core.particles.ParticleTypes.ITEM_SNOWBALL,
                                e.getX(), e.getY() + e.getBbHeight() / 2, e.getZ(), 12, 0.3, 0.5, 0.3, 0.05);
                    }
                }
                for (double d = 1; d <= reach; d += 0.75) {
                    double spread = 0.1 + d * 0.22;
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.3, 0);
                    level.sendParticles(particle, p.x, p.y, p.z, 3, spread, spread * 0.6, spread, 0.02);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.CLOUD, p.x, p.y, p.z, 1, spread * 0.6,
                            spread * 0.4, spread * 0.6, 0.01);
                }
                level.playSound(null, player, SoundEvents.POWDER_SNOW_BREAK, SoundSource.PLAYERS, 1.2F, 0.6F);
                level.playSound(null, player, SoundEvents.PLAYER_BREATH, SoundSource.PLAYERS, 1.0F, 0.5F);
            }
            case TEMPEST -> {
                // the Storm Ascetic's staff: struck on the ground, a gust hurls every foe around the wielder away, then
                // lightning falls on the (up to) three nearest of them
                List<LivingEntity> caught = new java.util.ArrayList<>();
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 2, size))) {
                    if (e.distanceTo(player) <= size) {
                        Vec3 away = e.position().subtract(origin).multiply(1, 0, 1);
                        away = away.lengthSqr() < 1.0E-4 ? flat : away.normalize();
                        e.push(away.x * 1.3, 0.45, away.z * 1.3);
                        e.hurtMarked = true;
                        caught.add(e);
                    }
                }
                caught.sort(java.util.Comparator.comparingDouble(e -> e.distanceToSqr(player)));
                for (LivingEntity e : caught.subList(0, Math.min(3, caught.size()))) {
                    var bolt = net.minecraft.world.entity.EntityTypes.LIGHTNING_BOLT.create(level,
                            net.minecraft.world.entity.EntitySpawnReason.TRIGGERED);
                    if (bolt != null) {
                        bolt.snapTo(e.getX(), e.getY(), e.getZ());
                        bolt.setVisualOnly(true);
                        level.addFreshEntity(bolt);
                    }
                    hit(level, player, e, power, 0.0);
                    level.sendParticles(particle, e.getX(), e.getY() + 1, e.getZ(), 20, 0.3, 0.8, 0.3, 0.2);
                }
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.GUST_EMITTER_SMALL, origin.x, origin.y + 0.5,
                        origin.z, 1, 0, 0, 0, 0);
                ring(level, origin, size);
                level.playSound(null, player, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 1.2F, 0.7F);
                level.playSound(null, player, SoundEvents.BELL_RESONATE, SoundSource.PLAYERS, 0.8F, 1.2F);
            }
            case MIRE -> {
                // the Bog Hierophant's lantern-crozier: the bog opens where the wielder looks (up to `size` blocks, short
                // of walls); every foe within 4 blocks of it is dragged into its heart, held fast (Slowness VII, 3 s)
                // and a poison bloom bursts on it
                Vec3 eye = player.getEyePosition();
                BlockHitResult aim = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                Vec3 spot = aim.getType() == HitResult.Type.MISS ? eye.add(look.scale(size)) : aim.getLocation();
                spot = spot.subtract(look.scale(0.3));
                for (LivingEntity e : foes(level, player, new AABB(spot, spot).inflate(4.0, 3.0, 4.0))) {
                    Vec3 in = spot.subtract(e.position()).multiply(1, 0, 1);
                    if (in.length() > 4.0 + e.getBbWidth() / 2) {
                        continue;
                    }
                    hit(level, player, e, power, 0.0);
                    if (in.lengthSqr() > 1.0E-4) {
                        Vec3 pull = in.normalize().scale(Math.min(1.2, in.length() * 0.35));
                        e.setDeltaMovement(pull.x, -0.1, pull.z);
                        e.hurtMarked = true;
                    }
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 6));
                    e.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1));
                    level.sendParticles(particle, e.getX(), e.getY() + 1, e.getZ(), 12, 0.4, 0.6, 0.4, 0.02);
                }
                for (int a = 0; a < 360; a += 15) {
                    double r = Math.toRadians(a);
                    for (double d = 1.0; d <= 4.0; d += 1.5) {
                        level.sendParticles(net.minecraft.core.particles.ParticleTypes.BUBBLE_POP, spot.x + Math.cos(r) * d,
                                spot.y + 0.2, spot.z + Math.sin(r) * d, 1, 0.1, 0.0, 0.1, 0.0);
                    }
                }
                level.sendParticles(particle, spot.x, spot.y + 0.8, spot.z, 40, 1.5, 0.6, 1.5, 0.02);
                for (double d = 1; d <= eye.distanceTo(spot); d += 0.8) {
                    Vec3 p = eye.add(look.scale(d));
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SMALL_FLAME, p.x, p.y - 0.3, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                }
                level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.MUD_BREAK, SoundSource.PLAYERS, 1.4F, 0.6F);
                level.playSound(null, player, SoundEvents.LANTERN_PLACE, SoundSource.PLAYERS, 1.0F, 0.6F);
            }
            case TIDE -> {
                // the Abbess of the Tides' crozier: struck on the ground, a breaking wave rolls ahead in a 5-block band
                // (stopped by walls); every foe in it is hurt once and swept along, and the sea carries the wielder
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(flat.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye) + 0.5;
                Vec3 side = new Vec3(-flat.z, 0, flat.x);
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1, 2, reach + 1))) {
                    Vec3 rel = e.position().subtract(origin).multiply(1, 0, 1);
                    double along = rel.dot(flat);
                    if (along > 0 && along <= reach && Math.abs(rel.dot(side)) <= 2.5 + e.getBbWidth() / 2) {
                        hit(level, player, e, power, 0.2);
                        e.push(flat.x * 1.4, 0.3, flat.z * 1.4);
                        e.hurtMarked = true;
                    }
                }
                for (double d = 1; d <= reach; d += 0.8) {
                    for (double l = -2.5; l <= 2.5; l += 1.0) {
                        Vec3 p = origin.add(flat.scale(d)).add(side.scale(l));
                        level.sendParticles(particle, p.x, p.y + 0.4 + d * 0.05, p.z, 2, 0.2, 0.3, 0.2, 0.1);
                    }
                    Vec3 c = origin.add(flat.scale(d));
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.FALLING_WATER, c.x, c.y + 1.8, c.z, 3, 1.5, 0.3, 1.5, 0);
                }
                player.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 120, 0));
                level.playSound(null, player, SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS, 1.2F, 0.6F);
                level.playSound(null, player, SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 0.8F, 0.9F);
            }
            case PRESSURE -> {
                // the Turbine Tyrant's valve-wrench: the valve opened, scalding steam bursts round the wielder; it
                // reaches only the foes the wielder can see (walls shield them), full force within 3 blocks, half at
                // the edge, hurling them away; the overload speeds the wielder up for 3 s
                Vec3 eye = player.getEyePosition();
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 3, size))) {
                    double d = e.distanceTo(player);
                    if (d > size) {
                        continue;
                    }
                    Vec3 to = e.position().add(0, e.getBbHeight() * 0.5, 0);
                    if (level.clip(new ClipContext(eye, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player))
                            .getType() != HitResult.Type.MISS) {
                        continue;                                   // behind a wall: shielded
                    }
                    float falloff = d <= 3 ? 1.0F : (float) (1.0 - 0.5 * (d - 3) / Math.max(0.1, size - 3));
                    hit(level, player, e, power * falloff, 1.4 * falloff);
                    level.sendParticles(particle, e.getX(), e.getY() + 1, e.getZ(), 10, 0.3, 0.5, 0.3, 0.1);
                }
                for (int a = 0; a < 360; a += 15) {
                    double r = Math.toRadians(a);
                    for (double d = 1.5; d <= size; d += 2.0) {
                        level.sendParticles(particle, origin.x + Math.cos(r) * d, origin.y + 0.6, origin.z + Math.sin(r) * d,
                                1, 0.2, 0.2, 0.2, 0.02);
                    }
                }
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK, origin.x, origin.y + 1, origin.z,
                        20, 0.6, 0.8, 0.6, 0.2);
                player.addEffect(new MobEffectInstance(MobEffects.SPEED, 60, 1));
                level.playSound(null, player, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 1.2F, 0.5F);
                level.playSound(null, player, SoundEvents.LAVA_EXTINGUISH, SoundSource.PLAYERS, 1.0F, 0.6F);
            }
            case JET -> {
                // the Lock-Master's pressure-lance: a high-pressure jet of water along the look line (stopped by walls);
                // every foe in it is hurt once and hurled to the far end of the jet, and the recoil pushes the wielder
                // a step back
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                java.util.Set<LivingEntity> soaked = new java.util.HashSet<>();
                for (double d = 1; d <= reach; d += 0.6) {
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.3, 0);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SPLASH, p.x, p.y, p.z, 3, 0.08, 0.08, 0.08, 0.05);
                    if (((int) (d * 10)) % 18 == 0) {
                        level.sendParticles(particle, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
                    }
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(0.9))) {
                        if (soaked.add(e)) {
                            hit(level, player, e, power, 0.0);
                            double left = Math.max(1.0, reach - d);
                            e.setDeltaMovement(look.x * Math.min(2.4, 0.4 + left * 0.18), 0.35, look.z * Math.min(2.4, 0.4 + left * 0.18));
                            e.hurtMarked = true;
                            e.clearFire();
                        }
                    }
                }
                Vec3 end = eye.add(look.scale(reach));
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.CLOUD, end.x, end.y, end.z, 6, 0.3, 0.3, 0.3, 0.05);
                player.push(-flat.x * 0.45, 0.05, -flat.z * 0.45);
                player.hurtMarked = true;
                player.clearFire();
                level.playSound(null, player, SoundEvents.BUCKET_EMPTY, SoundSource.PLAYERS, 1.2F, 0.6F);
                level.playSound(null, player, SoundEvents.PISTON_EXTEND, SoundSource.PLAYERS, 1.0F, 0.7F);
            }
            case PLUMB -> {
                // the Abyssal Architect's plumb: the bob is let fall from on high onto the spot you aim at (up to size
                // blocks away): every foe within 2.5 blocks of it is hurt and pinned to the ground for 2 s
                Vec3 eye = player.getEyePosition();
                BlockHitResult aim = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                Vec3 spot = aim.getType() == HitResult.Type.MISS ? eye.add(look.scale(size)) : aim.getLocation();
                BlockHitResult floor = level.clip(new ClipContext(spot.add(0, 0.5, 0), spot.add(0, -8, 0), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                if (floor.getType() != HitResult.Type.MISS) {
                    spot = floor.getLocation();
                }
                Vec3 at = spot;
                for (LivingEntity e : foes(level, player, new AABB(at, at).inflate(3.5, 2.5, 3.5))) {
                    if (e.position().multiply(1, 0, 1).distanceTo(at.multiply(1, 0, 1)) <= 2.5 + e.getBbWidth() / 2) {
                        hit(level, player, e, power, 0.1);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 3));
                        e.setDeltaMovement(e.getDeltaMovement().multiply(0.2, 0, 0.2).add(0, -0.4, 0));
                        e.hurtMarked = true;
                    }
                }
                for (double h = 0; h < 8; h += 0.5) {
                    level.sendParticles(particle, at.x, at.y + h, at.z, 2, 0.15, 0.1, 0.15, 0.0);
                }
                level.sendParticles(new net.minecraft.core.particles.BlockParticleOption(net.minecraft.core.particles.ParticleTypes.BLOCK,
                        net.minecraft.world.level.block.Blocks.DEEPSLATE_BRICKS.defaultBlockState()), at.x, at.y + 0.3, at.z, 40, 1.0, 0.2, 1.0, 0.15);
                ring(level, at, 2.5);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 1.0F, 0.5F);
                level.playSound(null, player, SoundEvents.CHAIN_FALL, SoundSource.PLAYERS, 1.0F, 0.7F);
            }
            case BROADSIDE -> {
                // the Drowned Admiral's cutlass: the deck cannon fires along the look line; the shell bursts on the
                // first foe or wall it meets (up to `size` blocks): full damage within 1 block of the burst, half at
                // 3.5, foes hurled away from it; the recoil kicks the wielder a step back
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                Vec3 burst = eye.add(look.scale(reach));
                outer:
                for (double d = 1; d <= reach; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d));
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(0.8))) {
                        if (e.getBoundingBox().inflate(0.4).contains(p)) {
                            burst = p;
                            break outer;
                        }
                    }
                    if (((int) (d * 2)) % 3 == 0) {
                        level.sendParticles(net.minecraft.core.particles.ParticleTypes.SMOKE, p.x, p.y - 0.2, p.z, 1, 0.03, 0.03, 0.03, 0.0);
                    }
                }
                for (LivingEntity e : foes(level, player, new AABB(burst, burst).inflate(4.5, 3.5, 4.5))) {
                    double dist = e.position().add(0, e.getBbHeight() * 0.5, 0).distanceTo(burst);
                    if (dist > 3.5 + e.getBbWidth() / 2) {
                        continue;
                    }
                    float k = dist <= 1.0 ? 1.0F : (float) (1.0 - 0.5 * Math.min(1.0, (dist - 1.0) / 2.5));
                    if (e.hurtServer(level, level.damageSources().playerAttack(player), power * k)) {
                        Vec3 away = e.position().subtract(burst).multiply(1, 0, 1);
                        away = away.lengthSqr() < 1.0E-4 ? flat : away.normalize();
                        e.push(away.x * 1.2 * k, 0.45, away.z * 1.2 * k);
                        e.hurtMarked = true;
                        if ((flags & FIRE) != 0) {
                            e.igniteForSeconds(4.0F);
                        }
                    }
                }
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.EXPLOSION, burst.x, burst.y, burst.z, 2, 0.6, 0.4, 0.6, 0.0);
                level.sendParticles(particle, burst.x, burst.y, burst.z, 16, 1.0, 0.6, 1.0, 0.03);
                Vec3 m = eye.add(look.scale(1.2));
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.CLOUD, m.x, m.y - 0.3, m.z, 6, 0.15, 0.15, 0.15, 0.05);
                player.push(-flat.x * 0.5, 0.05, -flat.z * 0.5);
                player.hurtMarked = true;
                level.playSound(null, burst.x, burst.y, burst.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.2F, 0.9F);
                level.playSound(null, player, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 1.2F, 0.5F);
            }
            case PRISM -> {
                // the Solar Hierarch's sun-staff: a ray of focused sunlight runs along the aim and glances off block
                // faces like light off a mirror (up to 3 bounces, `size` blocks in all); every foe it crosses is hurt
                // once, and each bounce adds a quarter to its heat
                java.util.Set<LivingEntity> lit = new java.util.HashSet<>();
                Vec3 from = player.getEyePosition();
                Vec3 dir = look;
                double left = size;
                float heat = power;
                for (int bounce = 0; bounce <= 3 && left > 0.5; bounce++) {
                    BlockHitResult wall = level.clip(new ClipContext(from, from.add(dir.scale(left)), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    boolean struck = wall.getType() != HitResult.Type.MISS;
                    double len = struck ? wall.getLocation().distanceTo(from) : left;
                    for (double d = 0.5; d <= len; d += 0.5) {
                        Vec3 p = from.add(dir.scale(d));
                        level.sendParticles(particle, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                        for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(0.9))) {
                            if (e.getBoundingBox().inflate(0.5).contains(p) && lit.add(e)) {
                                hit(level, player, e, heat, 0.3);
                                level.sendParticles(net.minecraft.core.particles.ParticleTypes.FLAME, p.x, p.y, p.z, 8, 0.2, 0.2, 0.2, 0.04);
                            }
                        }
                    }
                    left -= len;
                    if (!struck) {
                        break;
                    }
                    net.minecraft.core.Direction face = wall.getDirection();
                    Vec3 hitAt = wall.getLocation();
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.WAX_OFF, hitAt.x, hitAt.y, hitAt.z, 6, 0.15, 0.15, 0.15, 0.4);
                    dir = switch (face.getAxis()) {
                        case X -> new Vec3(-dir.x, dir.y, dir.z);
                        case Y -> new Vec3(dir.x, -dir.y, dir.z);
                        case Z -> new Vec3(dir.x, dir.y, -dir.z);
                    };
                    from = hitAt.add(face.getStepX() * 0.05, face.getStepY() * 0.05, face.getStepZ() * 0.05);
                    heat *= 1.25F;
                    level.playSound(null, hitAt.x, hitAt.y, hitAt.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.4F + bounce * 0.2F);
                }
                level.playSound(null, player, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.8F, 1.8F);
            }
            case CAGE -> {
                // the Strangler Fig Queen's macuahuitl: a lash of living root runs along the look line (stops on
                // walls); the first foe it meets is caged where it stands (held fast, weakened) and the cage's thorns
                // whip every other foe within 3 blocks of it, dragging them against the bars
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                LivingEntity caged = null;
                double best = reach + 1;
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
                    double along = to.dot(look);
                    if (along > 0 && along <= reach && to.subtract(look.scale(along)).length() <= 1.0 + e.getBbWidth() / 2
                            && along < best) {
                        caged = e;
                        best = along;
                    }
                }
                double shown = caged != null ? best : reach;
                for (double d = 1; d <= shown; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.4, 0);
                    level.sendParticles(particle, p.x, p.y, p.z, 1, 0.05, 0.05, 0.05, 0.0);
                }
                level.playSound(null, player, SoundEvents.VINE_BREAK, SoundSource.PLAYERS, 1.2F, 0.6F);
                if (caged != null) {
                    hit(level, player, caged, power, 0.0);
                    caged.setDeltaMovement(0, Math.min(0, caged.getDeltaMovement().y), 0);
                    caged.hurtMarked = true;
                    caged.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 6));
                    caged.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
                    Vec3 c = caged.position();
                    double r = Math.max(1.0, caged.getBbWidth() / 2 + 0.6);
                    net.minecraft.core.particles.ParticleOptions bark = new net.minecraft.core.particles.BlockParticleOption(
                            net.minecraft.core.particles.ParticleTypes.BLOCK,
                            net.minecraft.world.level.block.Blocks.MANGROVE_ROOTS.defaultBlockState());
                    double tall = caged.getBbHeight() + 0.5;
                    for (int a = 0; a < 360; a += 45) {
                        double rad = Math.toRadians(a);
                        for (double h = 0; h <= tall; h += 0.4) {
                            level.sendParticles(bark, c.x + Math.cos(rad) * r, c.y + h, c.z + Math.sin(rad) * r, 1, 0.02, 0.02, 0.02, 0.0);
                        }
                    }
                    level.sendParticles(particle, c.x, c.y + tall, c.z, 20, r * 0.6, 0.1, r * 0.6, 0.02);
                    level.playSound(null, caged, SoundEvents.MANGROVE_ROOTS_PLACE, SoundSource.PLAYERS, 1.5F, 0.6F);
                    for (LivingEntity e : foes(level, player, new AABB(c, c).inflate(3.5, 2.0, 3.5))) {
                        if (e == caged || e.position().distanceTo(c) > 3.0 + e.getBbWidth() / 2) {
                            continue;
                        }
                        hit(level, player, e, power * 0.5F, 0.0);
                        Vec3 pull = c.subtract(e.position()).multiply(1, 0, 1);
                        if (pull.length() > 0.1) {
                            Vec3 v = pull.normalize().scale(Math.min(0.9, 0.2 + pull.length() * 0.2));
                            e.setDeltaMovement(v.x, 0.2, v.z);
                            e.hurtMarked = true;
                        }
                        Vec3 m2 = e.position().add(c).scale(0.5);
                        level.sendParticles(particle, m2.x, m2.y + 1, m2.z, 6, 0.4, 0.3, 0.4, 0.02);
                    }
                }
            }
            case SCARAB -> {
                // the Fourth King's sceptre: a scarab flies along the aim and bursts into a swarm on the first foe or
                // wall it meets (up to `size` blocks); the swarm then leaps from foe to foe (up to 4 leaps within 5
                // blocks, a fifth weaker each leap), every bite poisons and starves, and the wielder drinks 1 health
                // for each foe bitten
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                LivingEntity first = null;
                double best = reach + 1;
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
                    double along = to.dot(look);
                    if (along > 0 && along <= reach && to.subtract(look.scale(along)).length() <= 0.8 + e.getBbWidth() / 2
                            && along < best) {
                        first = e;
                        best = along;
                    }
                }
                double flown = first != null ? best : reach;
                net.minecraft.core.particles.DustParticleOptions shell = new net.minecraft.core.particles.DustParticleOptions(0x1E2A4A, 1.0F);
                for (double d = 1; d <= flown; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.3, 0);
                    level.sendParticles(shell, p.x, p.y, p.z, 1, 0.03, 0.03, 0.03, 0.0);
                    level.sendParticles(particle, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                }
                level.playSound(null, player, SoundEvents.SILVERFISH_AMBIENT, SoundSource.PLAYERS, 1.2F, 0.6F);
                Vec3 burst = first != null ? first.getBoundingBox().getCenter() : eye.add(look.scale(Math.max(0.5, flown - 0.3)));
                level.sendParticles(shell, burst.x, burst.y, burst.z, 24, 0.5, 0.4, 0.5, 0.0);
                level.playSound(null, burst.x, burst.y, burst.z, SoundEvents.SILVERFISH_HURT, SoundSource.PLAYERS, 1.0F, 0.5F);
                LivingEntity bitten = first;
                if (bitten == null) {
                    // burst on a wall: the swarm springs at the nearest foe within 5 blocks of the burst
                    double near = 25.0;
                    for (LivingEntity e : foes(level, player, new AABB(burst, burst).inflate(5.0))) {
                        double d2 = e.getBoundingBox().getCenter().distanceToSqr(burst);
                        if (d2 < near) {
                            near = d2;
                            bitten = e;
                        }
                    }
                }
                java.util.Set<LivingEntity> fed = new java.util.HashSet<>();
                float bite = power;
                Vec3 from = burst;
                for (int leap = 0; leap <= 4 && bitten != null; leap++) {
                    fed.add(bitten);
                    Vec3 at = bitten.getBoundingBox().getCenter();
                    double gap = at.distanceTo(from);
                    for (double d = 0; d <= gap; d += 0.4) {
                        Vec3 p = from.add(at.subtract(from).scale(gap < 0.01 ? 0 : d / gap));
                        level.sendParticles(shell, p.x, p.y + Math.sin(d * 2.5) * 0.25, p.z, 1, 0.08, 0.08, 0.08, 0.0);
                    }
                    hit(level, player, bitten, bite, 0.1);
                    bitten.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
                    bitten.addEffect(new MobEffectInstance(MobEffects.HUNGER, 160, 1));
                    level.sendParticles(particle, at.x, at.y, at.z, 10, 0.35, 0.4, 0.35, 0.02);
                    level.playSound(null, bitten, SoundEvents.SILVERFISH_STEP, SoundSource.PLAYERS, 1.0F, 0.7F + leap * 0.1F);
                    player.heal(1.0F);
                    bite *= 0.8F;
                    from = at;
                    LivingEntity next = null;
                    double near = 25.0;
                    for (LivingEntity e : foes(level, player, bitten.getBoundingBox().inflate(5.0))) {
                        double d2 = e.getBoundingBox().getCenter().distanceToSqr(at);
                        if (!fed.contains(e) && d2 < near) {
                            near = d2;
                            next = e;
                        }
                    }
                    bitten = next;
                }
            }
            case MAGNET -> {
                // the Colossus's Heart's lodeblade: the engine-heart in the pommel beats once and every foe the wielder
                // can see within `size` blocks is dragged to within a step and a half of them; metal-clad foes (by
                // their armour) are hurt harder, every foe pulled is slowed 2 s, and loose items and experience in
                // reach fly to the wielder's feet
                Vec3 eye = player.getEyePosition();
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 4, size))) {
                    double d = e.distanceTo(player);
                    if (d > size) {
                        continue;
                    }
                    Vec3 to = e.getBoundingBox().getCenter();
                    if (level.clip(new ClipContext(eye, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player))
                            .getType() != HitResult.Type.MISS) {
                        continue;                                   // out of sight: the pull does not reach
                    }
                    float metal = (float) Math.min(6.0, e.getArmorValue() * 0.4);
                    hit(level, player, e, power + metal, 0.0);
                    Vec3 pull = origin.subtract(e.position()).multiply(1, 0, 1);
                    double gap = Math.max(0.0, pull.length() - 1.5);
                    Vec3 dir = pull.lengthSqr() < 1.0E-4 ? Vec3.ZERO : pull.normalize();
                    double speed = Math.min(1.8, 0.25 + gap * 0.2);
                    e.setDeltaMovement(dir.x * speed, 0.25, dir.z * speed);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1));
                    for (double t = 0; t <= 1.0; t += 0.12) {
                        Vec3 p = to.add(eye.add(0, -0.5, 0).subtract(to).scale(t));
                        level.sendParticles(particle, p.x, p.y, p.z, 1, 0.04, 0.04, 0.04, 0.0);
                    }
                }
                AABB reachBox = player.getBoundingBox().inflate(size, 3, size);
                for (net.minecraft.world.entity.Entity loose : level.getEntities((net.minecraft.world.entity.Entity) null, reachBox,
                        x -> x instanceof net.minecraft.world.entity.item.ItemEntity || x instanceof net.minecraft.world.entity.ExperienceOrb)) {
                    Vec3 pull = origin.subtract(loose.position());
                    loose.setDeltaMovement(pull.scale(0.18).add(0, 0.2, 0));
                    loose.hurtMarked = true;
                }
                ring(level, origin, size * 0.5);
                ring(level, origin, size);
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK, origin.x, origin.y + 1.1, origin.z,
                        16, 0.4, 0.5, 0.4, 0.15);
                level.playSound(null, player, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.4F, 0.6F);
                level.playSound(null, player, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.7F, 1.6F);
            }
            case TONGS -> {
                // the Anvil Warden's tongs: the nearest foe in front (within 4.5 blocks, 50 degrees either side of the
                // aim) is seized and hurled along the aim (up to `size` blocks, walls stop it); every other foe it
                // crashes through takes three quarters, and it slams down at the end: full damage, ablaze, and half to
                // every foe within 2.5 blocks of the impact. Bosses and huge creatures are not lifted, only seared
                LivingEntity seized = null;
                double best = 99;
                double cos = Math.cos(Math.toRadians(50));
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(4.5, 2.0, 4.5))) {
                    Vec3 to = e.position().subtract(origin).multiply(1, 0, 1);
                    double d = to.length();
                    if (d <= 4.5 + e.getBbWidth() / 2 && (d < 0.8 || to.normalize().dot(flat) >= cos) && d < best) {
                        seized = e;
                        best = d;
                    }
                }
                if (seized == null) {
                    noTarget(player);
                    return false;
                }
                boolean heavy = seized instanceof com.brasshaven.boss.WayfarerBoss || seized.getBbWidth() > 2.0F;
                Vec3 dir = new Vec3(flat.x, Math.max(-0.2, Math.min(0.35, look.y)), flat.z).normalize();
                Vec3 start = seized.position().add(0, seized.getBbHeight() * 0.5, 0);
                BlockHitResult wall = level.clip(new ClipContext(start, start.add(dir.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = heavy ? 0 : Math.max(0, (wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(start)) - 0.8);
                Vec3 end = start.add(dir.scale(reach));
                java.util.Set<LivingEntity> bowled = new java.util.HashSet<>();
                for (double d = 0.5; d <= reach; d += 0.5) {
                    Vec3 p = start.add(dir.scale(d));
                    level.sendParticles(particle, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0.01);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.2))) {
                        if (e != seized && bowled.add(e)) {
                            hit(level, player, e, power * 0.75F, 0.9);
                        }
                    }
                }
                if (!heavy) {
                    BlockHitResult floor = level.clip(new ClipContext(end, end.add(0, -6, 0), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    Vec3 land = floor.getType() == HitResult.Type.MISS ? end.add(0, -seized.getBbHeight() * 0.5, 0) : floor.getLocation();
                    seized.teleportTo(land.x, land.y, land.z);
                    seized.setDeltaMovement(0, -0.3, 0);
                    seized.hurtMarked = true;
                }
                hit(level, player, seized, power, 0.0);
                seized.igniteForSeconds(5.0F);
                Vec3 at = seized.position();
                for (LivingEntity e : foes(level, player, new AABB(at, at).inflate(3.0, 2.0, 3.0))) {
                    if (e != seized && e.position().distanceTo(at) <= 2.5 + e.getBbWidth() / 2) {
                        hit(level, player, e, power * 0.5F, 0.6);
                    }
                }
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.LAVA, at.x, at.y + 0.3, at.z, 10, 0.8, 0.2, 0.8, 0.0);
                level.sendParticles(new net.minecraft.core.particles.BlockParticleOption(net.minecraft.core.particles.ParticleTypes.BLOCK,
                        net.minecraft.world.level.block.Blocks.BASALT.defaultBlockState()), at.x, at.y + 0.3, at.z, 30, 1.0, 0.2, 1.0, 0.15);
                ring(level, at, 2.5);
                level.playSound(null, player, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.2F, 0.6F);
                level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 1.0F, 0.6F);
            }
            case ZENITH -> {
                // the Star-Eater Curator's astrolabe: gravity turns over at the spot the wielder aims at (up to `size`
                // blocks, short of walls); every foe within 4 blocks of it is hurt, drawn toward its heart and hurled
                // upward, floating helpless (Levitation III, 1.5 s) and glowing 4 s before it falls back down
                Vec3 eye = player.getEyePosition();
                BlockHitResult aim = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                Vec3 spot = aim.getType() == HitResult.Type.MISS ? eye.add(look.scale(size)) : aim.getLocation();
                spot = spot.subtract(look.scale(0.4));
                for (LivingEntity e : foes(level, player, new AABB(spot, spot).inflate(4.0, 3.0, 4.0))) {
                    Vec3 in = spot.subtract(e.position()).multiply(1, 0, 1);
                    if (in.length() > 4.0 + e.getBbWidth() / 2) {
                        continue;
                    }
                    hit(level, player, e, power, 0.0);
                    Vec3 pull = in.lengthSqr() > 1.0E-4 ? in.normalize().scale(Math.min(0.5, in.length() * 0.2)) : Vec3.ZERO;
                    e.setDeltaMovement(pull.x, 0.6, pull.z);
                    e.hurtMarked = true;
                    e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 30, 2));
                    e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 80, 0));
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.REVERSE_PORTAL, e.getX(), e.getY() + 0.5,
                            e.getZ(), 16, 0.3, 0.5, 0.3, 0.05);
                }
                for (int a = 0; a < 360; a += 15) {
                    double r = Math.toRadians(a);
                    level.sendParticles(particle, spot.x + Math.cos(r) * 4.0, spot.y + 0.2, spot.z + Math.sin(r) * 4.0,
                            1, 0.0, 0.3, 0.0, 0.02);
                }
                level.sendParticles(net.minecraft.core.particles.ParticleTypes.REVERSE_PORTAL, spot.x, spot.y + 0.5, spot.z,
                        40, 1.8, 0.3, 1.8, 0.08);
                for (double d = 1; d <= eye.distanceTo(spot); d += 0.8) {
                    Vec3 p = eye.add(look.scale(d));
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANT, p.x, p.y - 0.3, p.z, 1, 0.02, 0.02, 0.02, 0.1);
                }
                level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 1.2F, 1.4F);
                level.playSound(null, player, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.2F, 0.8F);
            }
            case FUSE -> {
                // the Mine Baron's drill-pick: a bundle of lit dynamite flung along the aim (up to `size` blocks); it
                // sticks to the first foe it meets or lies where it lands, its fuse burns 1.5 s, then it blows: full
                // damage near the heart of the blast down to half at 3.5 blocks, foes hurled away, the foe it stuck to
                // takes half again. It never breaks a block
                Vec3 eye = player.getEyePosition();
                BlockHitResult aim = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = aim.getType() == HitResult.Type.MISS ? size : aim.getLocation().distanceTo(eye);
                LivingEntity stuck = null;
                Vec3 spot = eye.add(look.scale(Math.max(0, reach - 0.3)));
                for (double d = 1.0; d <= reach && stuck == null; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d));
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SMOKE, p.x, p.y - 0.2, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(0.8))) {
                        stuck = e;
                        spot = p;
                        break;
                    }
                }
                if (stuck == null && aim.getType() != HitResult.Type.MISS) {
                    BlockHitResult floor = level.clip(new ClipContext(spot, spot.add(0, -4, 0), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    if (floor.getType() != HitResult.Type.MISS) {
                        spot = floor.getLocation().add(0, 0.2, 0);
                    }
                }
                BlastCharges.light(level, spot, stuck, 30, power, 3.5, particle, (e, dmg, knock) -> {
                    if (Targets.foe(player, e)) {
                        hit(level, player, e, dmg, knock);
                    }
                });
                level.playSound(null, player, SoundEvents.TNT_PRIMED, SoundSource.PLAYERS, 1.0F, 1.2F);
                level.playSound(null, player, SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS, 1.0F, 0.5F);
            }
            case SHRIEK -> {
                // the Hollow Cantor's baton: the fork struck, a shriek loosed in a cone ahead (35 degrees either side,
                // up to `size` blocks); walls stop it (line of sight from the eye). Every foe in it is hurt, thrown
                // back and weakened (flag), and where the shriek's axis meets a wall its echo bursts: half the damage
                // to every foe within 3 blocks of that spot
                Vec3 eye = player.getEyePosition();
                double cos = Math.cos(Math.toRadians(35));
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(size, 3, size))) {
                    Vec3 to = e.position().add(0, e.getBbHeight() * 0.5, 0).subtract(eye);
                    double d = to.length();
                    if (d > size + e.getBbWidth() / 2 || (d > 1.0 && to.normalize().dot(look) < cos)) {
                        continue;
                    }
                    BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(to), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    if (wall.getType() != HitResult.Type.MISS && wall.getLocation().distanceTo(eye) < d - 0.5) {
                        continue;
                    }
                    hit(level, player, e, power, 1.1);
                }
                BlockHitResult axis = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = axis.getType() == HitResult.Type.MISS ? size : axis.getLocation().distanceTo(eye);
                for (double d = 1.5; d <= reach; d += 1.5) {
                    double r = d * Math.tan(Math.toRadians(35));
                    for (int k = -2; k <= 2; k++) {
                        Vec3 side = new Vec3(-look.z, 0, look.x);
                        side = side.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : side.normalize();
                        Vec3 p = eye.add(look.scale(d)).add(side.scale(r * k / 2.0));
                        level.sendParticles(particle, p.x, p.y - 0.2, p.z, 1, 0.05, 0.05, 0.05, 0.5);
                    }
                    if (((int) (d / 1.5)) % 3 == 1) {
                        Vec3 p = eye.add(look.scale(d));
                        level.sendParticles(net.minecraft.core.particles.ParticleTypes.SONIC_BOOM, p.x, p.y - 0.2, p.z, 1, 0, 0, 0, 0);
                    }
                }
                if (axis.getType() != HitResult.Type.MISS) {
                    Vec3 echo = axis.getLocation().subtract(look.scale(0.5));
                    for (LivingEntity e : foes(level, player, new AABB(echo, echo).inflate(3.0))) {
                        if (e.position().distanceTo(echo) <= 3.0 + e.getBbWidth() / 2) {
                            hit(level, player, e, power * 0.5F, 0.5);
                        }
                    }
                    ring(level, echo.subtract(0, 1.0, 0), 3.0);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SONIC_BOOM, echo.x, echo.y, echo.z, 1, 0, 0, 0, 0);
                    level.playSound(null, echo.x, echo.y, echo.z, SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 1.0F, 1.4F);
                }
                level.playSound(null, player, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 0.8F, 1.6F);
                level.playSound(null, player, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2F, 1.0F);
            }
            case GRAPPLE -> {
                // the Corsair Captain's harpoon gun: a harpoon fired along the aim (up to `size` blocks, walls stop it);
                // if it bites a foe, the foe is cut (hurt and slowed) and the line hauls the wielder to it; if it bites
                // a wall, it hauls the wielder there. The rotor lets the wielder down softly (Slow Falling 3 s)
                Vec3 eye = player.getEyePosition();
                BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = wall.getType() == HitResult.Type.MISS ? size : wall.getLocation().distanceTo(eye);
                LivingEntity caught = null;
                double best = reach + 1;
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
                    Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
                    double along = to.dot(look);
                    if (along > 0 && along <= reach && to.subtract(look.scale(along)).length() <= 0.9 + e.getBbWidth() / 2
                            && along < best) {
                        caught = e;
                        best = along;
                    }
                }
                double shown = caught != null ? best : reach;
                for (double d = 1; d <= shown; d += 0.5) {
                    Vec3 p = eye.add(look.scale(d)).add(0, -0.3, 0);
                    level.sendParticles(d % 1.0 == 0 ? particle : net.minecraft.core.particles.ParticleTypes.CRIT,
                            p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
                }
                level.playSound(null, player, SoundEvents.CROSSBOW_SHOOT, SoundSource.PLAYERS, 1.2F, 0.6F);
                Vec3 dest = null;
                if (caught != null) {
                    hit(level, player, caught, power, 0.0);
                    Vec3 back = caught.position().subtract(origin).multiply(1, 0, 1);
                    dest = caught.position().subtract(back.lengthSqr() > 1.0E-4 ? back.normalize().scale(1.5) : Vec3.ZERO);
                    level.playSound(null, caught, SoundEvents.TRIDENT_HIT, SoundSource.PLAYERS, 1.2F, 0.8F);
                } else if (wall.getType() != HitResult.Type.MISS) {
                    dest = wall.getLocation().subtract(look.scale(0.8)).add(0, -1.0, 0);
                    level.playSound(null, dest.x, dest.y, dest.z, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.2F, 0.7F);
                }
                if (dest != null) {
                    Vec3 pull = dest.subtract(origin);
                    double dist = pull.length();
                    if (dist > 0.5) {
                        Vec3 v = pull.normalize().scale(Math.min(2.4, 0.5 + dist * 0.16));
                        player.setDeltaMovement(v.x, Math.max(0.35, v.y + 0.3), v.z);
                        player.hurtMarked = true;
                    }
                    player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0));
                    player.fallDistance = 0;
                }
            }
            case STOKE -> {
                // the Soul Stoker's shovel: a shovelful of soul embers flung in a fan along the aim (five embers, 12
                // degrees apart, up to `size` blocks, walls stop them); each bursts on the first foe it meets or where
                // it lands, 1.6 blocks round. A foe caught by several bursts takes one hit, the stronger the more
                // embers caught it (60% of the power for one, +20% for each more, at most 140%), set ablaze (flag fire)
                Vec3 eye = player.getEyePosition();
                java.util.Map<LivingEntity, Integer> caught = new java.util.HashMap<>();
                for (int k = -2; k <= 2; k++) {
                    double r = Math.toRadians(k * 12.0);
                    Vec3 dir = new Vec3(look.x * Math.cos(r) - look.z * Math.sin(r), look.y, look.x * Math.sin(r) + look.z * Math.cos(r)).normalize();
                    BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(dir.scale(size)), ClipContext.Block.COLLIDER,
                            ClipContext.Fluid.NONE, player));
                    double reach = wall.getType() == HitResult.Type.MISS ? size : Math.max(0.5, wall.getLocation().distanceTo(eye) - 0.3);
                    Vec3 spot = eye.add(dir.scale(reach));
                    boolean struck = false;
                    for (double d = 1.0; d <= reach && !struck; d += 0.5) {
                        Vec3 p = eye.add(dir.scale(d)).add(0, -0.3 - d * d * 0.004, 0);
                        if (((int) (d * 2)) % 2 == 0) {
                            level.sendParticles(particle, p.x, p.y, p.z, 1, 0.03, 0.03, 0.03, 0.0);
                        }
                        if (!foes(level, player, new AABB(p, p).inflate(0.8)).isEmpty()) {
                            spot = p;
                            struck = true;
                        }
                    }
                    if (!struck && wall.getType() == HitResult.Type.MISS) {
                        BlockHitResult floor = level.clip(new ClipContext(spot, spot.add(0, -5, 0), ClipContext.Block.COLLIDER,
                                ClipContext.Fluid.NONE, player));
                        if (floor.getType() != HitResult.Type.MISS) {
                            spot = floor.getLocation().add(0, 0.2, 0);
                        }
                    }
                    for (LivingEntity e : foes(level, player, new AABB(spot, spot).inflate(1.6, 1.6, 1.6))) {
                        if (e.getBoundingBox().getCenter().distanceTo(spot) <= 1.6 + e.getBbWidth() / 2 + e.getBbHeight() / 2) {
                            caught.merge(e, 1, Integer::sum);
                        }
                    }
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SOUL_FIRE_FLAME, spot.x, spot.y, spot.z, 10, 0.5, 0.3, 0.5, 0.04);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SOUL, spot.x, spot.y, spot.z, 2, 0.3, 0.2, 0.3, 0.02);
                }
                for (java.util.Map.Entry<LivingEntity, Integer> e : caught.entrySet()) {
                    hit(level, player, e.getKey(), power * Math.min(1.4F, 0.6F + 0.2F * (e.getValue() - 1)), 0.4);
                }
                level.playSound(null, player, SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 1.0F, 0.8F);
                level.playSound(null, player, SoundEvents.SOUL_ESCAPE.value(), SoundSource.PLAYERS, 1.2F, 0.7F);
            }
            case REWIND -> {
                // the Asylum Director's bone-saw: the wielder rips forward along the aim (up to `size` blocks, stopped by
                // walls), sawing every foe passed (flag slow); the pocket watch remembers the starting spot, and 2 s
                // later the wielder is snapped back to it (sneak to stay), the saw's echo cutting the foes round it for
                // half the power
                Vec3 feet = origin;
                double run = 0;
                for (double d = 0.5; d <= size; d += 0.5) {
                    Vec3 p = origin.add(flat.scale(d));
                    net.minecraft.core.BlockPos at = net.minecraft.core.BlockPos.containing(p.add(0, 0.2, 0));
                    if (!level.getBlockState(at).getCollisionShape(level, at).isEmpty()
                            || !level.getBlockState(at.above()).getCollisionShape(level, at.above()).isEmpty()) {
                        break;
                    }
                    run = d;
                    feet = p;
                }
                java.util.Set<LivingEntity> cut = new java.util.HashSet<>();
                for (double d = 0.5; d <= run; d += 0.5) {
                    Vec3 p = origin.add(flat.scale(d));
                    level.sendParticles(particle, p.x, p.y + 1.0, p.z, 2, 0.25, 0.4, 0.25, 0.0);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.3, 1.5, 1.3))) {
                        if (cut.add(e)) {
                            hit(level, player, e, power, 0.4);
                            level.sendParticles(net.minecraft.core.particles.ParticleTypes.SWEEP_ATTACK, e.getX(), e.getY() + 1.0,
                                    e.getZ(), 1, 0, 0, 0, 0);
                        }
                    }
                }
                if (run > 0.5) {
                    Vec3 v = flat.scale(Math.min(2.6, run * 0.32));
                    player.setDeltaMovement(v.x, 0.12, v.z);
                    player.hurtMarked = true;
                }
                if (player instanceof net.minecraft.server.level.ServerPlayer sp) {
                    Rewinds.mark(level, sp, origin, 40, (lvl, who, spot) -> {
                        for (LivingEntity e : foes(lvl, who, new AABB(spot, spot).inflate(2.5, 1.5, 2.5))) {
                            if (e.position().distanceTo(spot) <= 2.5 + e.getBbWidth() / 2) {
                                hit(lvl, who, e, power * 0.5F, 0.6);
                            }
                        }
                        ring(lvl, spot, 2.5);
                        lvl.playSound(null, spot.x, spot.y, spot.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.0F, 1.3F);
                    });
                }
                level.playSound(null, player, SoundEvents.GRINDSTONE_USE, SoundSource.PLAYERS, 1.0F, 1.5F);
                level.playSound(null, player, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.8F, 0.7F);
            }
            case DRAGON -> {
                // the Chime Abbot's dragon staff: the brass dragon's spirit rushes along the aim (up to `size` blocks,
                // stopped by walls); every foe it passes is hurt, flung aside out of its lane and blinded (flag blind);
                // the chimes in its jaws ring where it ends, slowing every foe within 3 blocks
                Vec3 eye = player.getEyePosition();
                BlockHitResult aim = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, player));
                double reach = aim.getType() == HitResult.Type.MISS ? size : Math.max(1.0, aim.getLocation().distanceTo(eye) - 0.3);
                Vec3 side = new Vec3(-look.z, 0, look.x);
                side = side.lengthSqr() < 1.0E-6 ? new Vec3(1, 0, 0) : side.normalize();
                java.util.Set<LivingEntity> swept = new java.util.HashSet<>();
                Vec3 end = eye;
                for (double d = 1.0; d <= reach; d += 0.75) {
                    Vec3 p = eye.add(look.scale(d)).subtract(0, 0.4, 0);
                    end = p;
                    level.sendParticles(particle, p.x, p.y, p.z, 2, 0.3, 0.3, 0.3, 0.0);
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y, p.z, 1, 0.2, 0.2, 0.2, 0.01);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.5, 1.5, 1.5))) {
                        if (swept.add(e)) {
                            hit(level, player, e, power, 0.2);
                            double s = e.position().subtract(p).dot(side) >= 0 ? 1.0 : -1.0;
                            e.push(side.x * s * 0.8, 0.35, side.z * s * 0.8);
                            e.hurtMarked = true;
                        }
                    }
                }
                for (LivingEntity e : foes(level, player, new AABB(end, end).inflate(3.0, 2.0, 3.0))) {
                    if (e.position().distanceTo(end) <= 3.5) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1));
                    }
                }
                ring(level, end, 3.0);
                level.playSound(null, player, SoundEvents.ENDER_DRAGON_SHOOT, SoundSource.PLAYERS, 0.8F, 1.3F);
                level.playSound(null, end.x, end.y, end.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.5F, 1.2F);
                level.playSound(null, end.x, end.y, end.z, SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 0.8F, 1.4F);
            }
            case RIFT -> {
                // the Castellan of the Caldera's halberd: driven into the ground, it opens a molten rift that runs
                // along the ground ahead (stops on walls) and forks in two at its end; every foe on it is hurt once
                java.util.Set<LivingEntity> seared = new java.util.HashSet<>();
                java.util.List<Vec3> path = new java.util.ArrayList<>();
                Vec3 end = origin;
                for (double d = 1; d <= size; d += 0.75) {
                    Vec3 p = riftGround(level, origin.add(flat.scale(d)));
                    if (p == null) {
                        break;
                    }
                    path.add(p);
                    end = p;
                }
                for (int side = -1; side <= 1; side += 2) {
                    double r = Math.toRadians(35 * side);
                    Vec3 dir = new Vec3(flat.x * Math.cos(r) - flat.z * Math.sin(r), 0, flat.x * Math.sin(r) + flat.z * Math.cos(r));
                    for (double d = 0.75; d <= size * 0.35; d += 0.75) {
                        Vec3 p = riftGround(level, end.add(dir.scale(d)));
                        if (p == null) {
                            break;
                        }
                        path.add(p);
                    }
                }
                for (Vec3 p : path) {
                    level.sendParticles(net.minecraft.core.particles.ParticleTypes.LAVA, p.x, p.y + 0.1, p.z, 1, 0.15, 0.0, 0.15, 0.0);
                    level.sendParticles(particle, p.x, p.y + 0.3, p.z, 3, 0.2, 0.3, 0.2, 0.02);
                    for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.2, 1.5, 1.2))) {
                        if (seared.add(e)) {
                            hit(level, player, e, power, 0.2);
                            e.push(0, 0.35, 0);
                        }
                    }
                }
                level.playSound(null, player, SoundEvents.MACE_SMASH_GROUND, SoundSource.PLAYERS, 1.0F, 0.6F);
                level.playSound(null, player, SoundEvents.LAVA_POP, SoundSource.PLAYERS, 1.2F, 0.7F);
            }
        }
        return true;
    }

    /** The rift's footing near {@code p}: the top of the ground within a block and a half, or null at a wall or a drop. */
    private static Vec3 riftGround(ServerLevel level, Vec3 p) {
        net.minecraft.core.BlockPos base = net.minecraft.core.BlockPos.containing(p);
        for (int dy = 1; dy >= -2; dy--) {
            net.minecraft.core.BlockPos at = base.above(dy);
            if (level.getBlockState(at).isAir() && level.getBlockState(at.below()).isFaceSturdy(level, at.below(),
                    net.minecraft.core.Direction.UP) && level.getBlockState(at.above()).isAir()) {
                return new Vec3(p.x, at.getY(), p.z);
            }
        }
        return null;
    }

    private void ring(ServerLevel level, Vec3 c, double radius) {
        for (int a = 0; a < 360; a += 12) {
            double r = Math.toRadians(a);
            level.sendParticles(particle, c.x + Math.cos(r) * radius, c.y + 0.2, c.z + Math.sin(r) * radius, 2, 0.1, 0.1, 0.1, 0.0);
        }
    }
}

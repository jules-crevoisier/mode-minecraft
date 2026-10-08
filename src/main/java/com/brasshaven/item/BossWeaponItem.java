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
 * eruptions, snare, poison cloud, leap, sweep, blink, chain hook, halo shards), tuned per weapon by power, size, particle and flags.
 * Abilities only ever hurt non-player creatures.
 */
public class BossWeaponItem extends AbilityItem {
    public enum Ability { WAVE, BEAM, DASH, ERUPT, ROOT, CLOUD, LEAP, ARC, BLINK, HOOK, SHARDS }

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
            case WAVE, ROOT, CLOUD, LEAP, ARC -> true;
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
        }
        return true;
    }

    private void ring(ServerLevel level, Vec3 c, double radius) {
        for (int a = 0; a < 360; a += 12) {
            double r = Math.toRadians(a);
            level.sendParticles(particle, c.x + Math.cos(r) * radius, c.y + 0.2, c.z + Math.sin(r) * radius, 2, 0.1, 0.1, 0.1, 0.0);
        }
    }
}

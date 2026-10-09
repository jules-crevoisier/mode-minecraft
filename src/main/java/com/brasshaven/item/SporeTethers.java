package com.brasshaven.item;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/**
 * Spore flasks of the Spore Alchemist's staff (the TETHER ability): the flask flies out along the aim (1.5 blocks a
 * tick, walls stop it) and shatters on the first foe it meets or where its flight ends: every foe within 2.5 blocks
 * takes the full power. Mycelium threads then tether every foe within 4 blocks of the spot to it for 3 s: a tethered
 * foe that strays more than 2.5 blocks from it is dragged back and stays slowed; when the threads snap the spores burst
 * again, half the power to every tethered foe still within 6. Ticked from the server tick, registered on first use
 * (like {@link AnchorThrows}).
 */
public final class SporeTethers {
    /** Deals a hit to a foe. */
    @FunctionalInterface
    public interface Hit {
        void apply(ServerLevel level, LivingEntity foe, float damage);
    }

    private static final DustParticleOptions THREAD = new DustParticleOptions(0xECEADE, 0.8F);
    private static final DustParticleOptions SPORE = new DustParticleOptions(0x78EC60, 1.4F);
    private static final int HOLD = 60;
    private static final double BURST = 2.5;
    private static final double SNARE = 4.0;
    private static final double LEASH = 2.5;

    private static final class Flask {
        final ServerLevel level;
        final Player player;
        final Vec3 dir;
        final double reach;
        final float power;
        final ParticleOptions particle;
        final Hit hit;
        final Predicate<LivingEntity> foe;
        final List<LivingEntity> held = new ArrayList<>();
        Vec3 at;
        double out;
        int hold = -1;

        Flask(ServerLevel level, Player player, Vec3 dir, double reach, float power, ParticleOptions particle, Hit hit,
              Predicate<LivingEntity> foe) {
            this.level = level;
            this.player = player;
            this.dir = dir;
            this.reach = reach;
            this.power = power;
            this.particle = particle;
            this.hit = hit;
            this.foe = foe;
            this.at = player.getEyePosition().subtract(0, 0.3, 0);
        }
    }

    private static final List<Flask> FLASKS = new ArrayList<>();
    private static boolean registered;

    private SporeTethers() {}

    /** Flings a spore flask from {@code player} along {@code look}, up to {@code size} blocks. */
    public static void fling(ServerLevel level, Player player, Vec3 look, float size, float power, ParticleOptions particle,
                             Hit hit, Predicate<LivingEntity> foe) {
        if (!registered) {
            registered = true;
            TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick());
        }
        Vec3 eye = player.getEyePosition();
        BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player));
        double reach = wall.getType() == HitResult.Type.MISS ? size : Math.max(1.0, wall.getLocation().distanceTo(eye) - 0.3);
        FLASKS.removeIf(f -> f.player == player);
        if (FLASKS.size() < 64) {
            FLASKS.add(new Flask(level, player, look.normalize(), reach, power, particle, hit, foe));
        }
    }

    private static void tick() {
        if (FLASKS.isEmpty()) {
            return;
        }
        FLASKS.removeIf(SporeTethers::step);
    }

    /** One tick of a flask; true when it is over. */
    private static boolean step(Flask f) {
        Player p = f.player;
        if (!p.isAlive() || p.isRemoved() || p.level() != f.level) {
            return true;
        }
        ServerLevel level = f.level;
        if (f.hold < 0) {
            Vec3 eye = p.getEyePosition().subtract(0, 0.3, 0);
            f.out = Math.min(f.reach, f.out + 1.5);
            f.at = eye.add(f.dir.scale(f.out));
            level.sendParticles(SPORE, f.at.x, f.at.y, f.at.z, 2, 0.08, 0.08, 0.08, 0.0);
            level.sendParticles(ParticleTypes.WITCH, f.at.x, f.at.y, f.at.z, 1, 0.05, 0.05, 0.05, 0.0);
            boolean struck = !level.getEntitiesOfClass(LivingEntity.class, new AABB(f.at, f.at).inflate(0.8), f.foe).isEmpty();
            if (!struck && f.out < f.reach) {
                return false;
            }
            shatter(f);
            return false;
        }
        int k = f.hold++;
        f.held.removeIf(e -> !e.isAlive() || e.level() != level);
        for (LivingEntity e : f.held) {
            Vec3 to = f.at.subtract(e.position());
            double d = Math.hypot(to.x, to.z);
            if (d > LEASH) {
                Vec3 pull = new Vec3(to.x, 0, to.z).normalize().scale(Math.min(0.35, (d - LEASH) * 0.2 + 0.1));
                e.push(pull.x, 0, pull.z);
                e.hurtMarked = true;
            }
            if (k % 2 == 0) {
                Vec3 a = f.at;
                Vec3 b = e.position().add(0, e.getBbHeight() * 0.5, 0);
                Vec3 link = b.subtract(a);
                double ll = link.length();
                for (double s = 0.5; s < ll; s += 0.5) {
                    Vec3 q = a.add(link.scale(s / ll));
                    level.sendParticles(THREAD, q.x, q.y, q.z, 1, 0, 0, 0, 0);
                }
            }
        }
        if (k % 6 == 0) {
            level.sendParticles(ParticleTypes.MYCELIUM, f.at.x, f.at.y, f.at.z, 6, 0.8, 0.1, 0.8, 0.0);
        }
        if (k < HOLD) {
            return false;
        }
        // the threads snap: the second burst
        for (LivingEntity e : f.held) {
            if (e.position().distanceTo(f.at) <= 6.0) {
                f.hit.apply(level, e, f.power * 0.5F);
            }
        }
        level.sendParticles(SPORE, f.at.x, f.at.y + 0.5, f.at.z, 30, 1.5, 0.6, 1.5, 0.0);
        level.sendParticles(f.particle, f.at.x, f.at.y + 0.5, f.at.z, 20, 1.5, 0.6, 1.5, 0.02);
        level.playSound(null, f.at.x, f.at.y, f.at.z, SoundEvents.FUNGUS_BREAK, SoundSource.PLAYERS, 1.2F, 0.8F);
        return true;
    }

    private static void shatter(Flask f) {
        ServerLevel level = f.level;
        BlockHitResult floor = level.clip(new ClipContext(f.at, f.at.add(0, -4, 0), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, f.player));
        if (floor.getType() != HitResult.Type.MISS && floor.getLocation().distanceTo(f.at) < 1.5) {
            f.at = floor.getLocation().add(0, 0.2, 0);
        }
        Vec3 c = f.at;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(SNARE, 2.5, SNARE), f.foe)) {
            double d = e.getBoundingBox().getCenter().distanceTo(c);
            if (d <= BURST + e.getBbWidth() / 2 + e.getBbHeight() / 2) {
                f.hit.apply(level, e, f.power);
            }
            if (d <= SNARE + e.getBbWidth() / 2 && e.isAlive()) {
                f.held.add(e);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, HOLD + 10, 1));
            }
        }
        level.sendParticles(SPORE, c.x, c.y + 0.4, c.z, 30, 1.2, 0.5, 1.2, 0.0);
        level.sendParticles(f.particle, c.x, c.y + 0.4, c.z, 20, 1.2, 0.5, 1.2, 0.02);
        level.sendParticles(ParticleTypes.SPLASH, c.x, c.y + 0.3, c.z, 20, 0.8, 0.2, 0.8, 0.1);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.SPLASH_POTION_BREAK, SoundSource.PLAYERS, 1.0F, 0.8F);
        f.hold = 0;
    }
}

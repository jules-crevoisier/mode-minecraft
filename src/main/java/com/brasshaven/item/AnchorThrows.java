package com.brasshaven.item;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;

/**
 * Thrown ice anchors of the Frozen Commodore's weapon (the ANCHOR ability): the anchor flies out along the aim on its
 * chain (2 blocks a tick, walls stop it) and bites the first foe it meets or the end of its throw (the first foe takes
 * the full power, frost bursts for half the power within 2 blocks of the bite), lies a few ticks, then the chain drags
 * it back to the wielder (1.5 blocks a tick): every foe within 1.3 of its way back is hit for 70% of the power, hauled
 * toward the wielder and slowed. Ticked from the server tick, registered on first use (like {@link Rewinds}).
 */
public final class AnchorThrows {
    /** Deals a hit to a foe; {@code pull} is the haul toward the wielder (null on the way out). */
    @FunctionalInterface
    public interface Hit {
        void apply(ServerLevel level, LivingEntity foe, float damage, @Nullable Vec3 pull);
    }

    private static final DustParticleOptions CHAIN = new DustParticleOptions(0x9AA4B4, 0.9F);
    private static final int BITE = 5;

    private static final class Throw {
        final ServerLevel level;
        final Player player;
        final Vec3 dir;
        final double reach;
        final float power;
        final ParticleOptions particle;
        final Hit hit;
        final Predicate<LivingEntity> foe;
        final Set<LivingEntity> outHit = new HashSet<>();
        final Set<LivingEntity> backHit = new HashSet<>();
        Vec3 at;
        double out;
        int bite = -1;
        boolean returning;

        Throw(ServerLevel level, Player player, Vec3 dir, double reach, float power, ParticleOptions particle, Hit hit,
              Predicate<LivingEntity> foe) {
            this.level = level;
            this.player = player;
            this.dir = dir;
            this.reach = reach;
            this.power = power;
            this.particle = particle;
            this.hit = hit;
            this.foe = foe;
            this.at = player.getEyePosition().subtract(0, 0.4, 0);
        }
    }

    private static final List<Throw> THROWS = new ArrayList<>();
    private static boolean registered;

    private AnchorThrows() {}

    /** Hurls an anchor from {@code player} along {@code look}, up to {@code size} blocks. */
    public static void hurl(ServerLevel level, Player player, Vec3 look, float size, float power, ParticleOptions particle,
                            Hit hit, Predicate<LivingEntity> foe) {
        if (!registered) {
            registered = true;
            TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick());
        }
        Vec3 eye = player.getEyePosition();
        BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(size)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player));
        double reach = wall.getType() == HitResult.Type.MISS ? size : Math.max(1.0, wall.getLocation().distanceTo(eye) - 0.4);
        THROWS.removeIf(t -> t.player == player);
        if (THROWS.size() < 64) {
            THROWS.add(new Throw(level, player, look.normalize(), reach, power, particle, hit, foe));
        }
    }

    private static void tick() {
        if (THROWS.isEmpty()) {
            return;
        }
        THROWS.removeIf(AnchorThrows::step);
    }

    /** One tick of a throw; true when it is over. */
    private static boolean step(Throw t) {
        Player p = t.player;
        if (!p.isAlive() || p.isRemoved() || p.level() != t.level) {
            return true;
        }
        ServerLevel level = t.level;
        Vec3 hand = p.getEyePosition().subtract(0, 0.5, 0);
        if (!t.returning && t.bite < 0) {
            t.out = Math.min(t.reach, t.out + 2.0);
            t.at = hand.add(t.dir.scale(t.out));
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(t.at, t.at).inflate(1.0), t.foe)) {
                if (t.outHit.add(e)) {
                    t.hit.apply(level, e, t.power, null);
                    t.bite = 0;
                }
            }
            if (t.out >= t.reach) {
                t.bite = 0;
            }
            if (t.bite == 0) {
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(t.at, t.at).inflate(2.0), t.foe)) {
                    if (!t.outHit.contains(e) && e.getBoundingBox().getCenter().distanceTo(t.at) <= 2.0 + e.getBbWidth() / 2) {
                        t.hit.apply(level, e, t.power * 0.5F, null);
                    }
                }
                level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), t.at.x, t.at.y,
                        t.at.z, 20, 0.6, 0.4, 0.6, 0.1);
                level.sendParticles(t.particle, t.at.x, t.at.y, t.at.z, 12, 1.0, 0.5, 1.0, 0.02);
                level.playSound(null, t.at.x, t.at.y, t.at.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 1.0F, 0.8F);
            }
        } else if (!t.returning) {
            if (++t.bite >= BITE) {
                t.returning = true;
                level.playSound(null, p, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.0F, 0.7F);
            }
        } else {
            Vec3 to = hand.subtract(t.at);
            double d = to.length();
            Vec3 prev = t.at;
            t.at = d <= 1.5 ? hand : t.at.add(to.scale(1.5 / d));
            Vec3 mid = prev.lerp(t.at, 0.5);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(mid, mid).inflate(1.3 + 0.75), t.foe)) {
                if (e.getBoundingBox().inflate(1.3).clip(prev, t.at).isPresent() || e.getBoundingBox().inflate(1.3).contains(t.at)) {
                    if (t.backHit.add(e)) {
                        Vec3 pull = p.position().subtract(e.position()).multiply(1, 0, 1);
                        pull = pull.length() < 2.0 ? Vec3.ZERO : pull.normalize().scale(0.8);
                        t.hit.apply(level, e, t.power * 0.7F, pull);
                    }
                }
            }
            if (d <= 1.5) {
                level.playSound(null, p, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.5F, 1.4F);
                return true;
            }
        }
        // the anchor and its chain back to the hand
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.PACKED_ICE.defaultBlockState()), t.at.x, t.at.y, t.at.z,
                3, 0.2, 0.2, 0.2, 0.0);
        level.sendParticles(t.particle, t.at.x, t.at.y, t.at.z, 2, 0.15, 0.15, 0.15, 0.0);
        Vec3 link = t.at.subtract(hand);
        double ll = link.length();
        for (double s = 0.6; s < ll; s += 0.7) {
            Vec3 q = hand.add(link.scale(s / ll));
            level.sendParticles(CHAIN, q.x, q.y, q.z, 1, 0, 0, 0, 0);
        }
        return false;
    }
}

package com.brasshaven.item;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * Lit charges thrown by the Mine Baron's drill-pick (the FUSE ability): each one sits where it landed, or rides the
 * foe it stuck to, while its fuse burns, then blows. The blast never breaks a block: it only hurts and hurls the
 * foes around it, through the {@link Blast} the weapon hands over. Ticked from the server tick, registered on first use.
 */
public final class BlastCharges {
    /** What the blast does to one foe: the weapon's own hit (damage, knockback), so its flags apply. */
    @FunctionalInterface
    public interface Blast {
        void hit(LivingEntity foe, float damage, double knock);
    }

    private static final class Charge {
        final ServerLevel level;
        Vec3 pos;
        final LivingEntity stuck;
        int fuse;
        final float power;
        final double radius;
        final ParticleOptions particle;
        final Blast blast;

        Charge(ServerLevel level, Vec3 pos, LivingEntity stuck, int fuse, float power, double radius,
               ParticleOptions particle, Blast blast) {
            this.level = level;
            this.pos = pos;
            this.stuck = stuck;
            this.fuse = fuse;
            this.power = power;
            this.radius = radius;
            this.particle = particle;
            this.blast = blast;
        }
    }

    private static final List<Charge> CHARGES = new ArrayList<>();
    private static boolean registered;

    private BlastCharges() {}

    /** Lights a charge at {@code pos} (riding {@code stuck} when not null) that blows after {@code fuse} ticks. */
    public static void light(ServerLevel level, Vec3 pos, LivingEntity stuck, int fuse, float power, double radius,
                             ParticleOptions particle, Blast blast) {
        if (!registered) {
            registered = true;
            TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick());
        }
        if (CHARGES.size() < 64) {
            CHARGES.add(new Charge(level, pos, stuck, fuse, power, radius, particle, blast));
        }
    }

    private static void tick() {
        if (CHARGES.isEmpty()) {
            return;
        }
        List<Charge> due = new ArrayList<>();
        CHARGES.removeIf(c -> {
            if (c.stuck != null && c.stuck.isAlive() && c.stuck.level() == c.level) {
                c.pos = c.stuck.position().add(0, c.stuck.getBbHeight() * 0.6, 0);
            }
            if (!c.level.isLoaded(BlockPos.containing(c.pos))) {
                return true;
            }
            c.fuse--;
            c.level.sendParticles(ParticleTypes.SMOKE, c.pos.x, c.pos.y + 0.3, c.pos.z, 1, 0.02, 0.02, 0.02, 0.01);
            c.level.sendParticles(ParticleTypes.FLAME, c.pos.x, c.pos.y + 0.35, c.pos.z, 1, 0.02, 0.05, 0.02, 0.01);
            if (c.fuse % 6 == 0 && c.fuse > 0) {
                c.level.playSound(null, c.pos.x, c.pos.y, c.pos.z, SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 0.3F, 2.0F);
            }
            if (c.fuse <= 0) {
                due.add(c);
                return true;
            }
            return false;
        });
        for (Charge c : due) {
            blow(c);
        }
    }

    private static void blow(Charge c) {
        ServerLevel level = c.level;
        Vec3 at = c.pos;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class,
                new net.minecraft.world.phys.AABB(at, at).inflate(c.radius + 1.0))) {
            double d = e.position().add(0, e.getBbHeight() * 0.5, 0).distanceTo(at);
            if (e != c.stuck && d > c.radius + e.getBbWidth() / 2) {
                continue;
            }
            float falloff = e == c.stuck ? 1.5F : (float) Math.max(0.5, 1.0 - 0.5 * d / c.radius);
            c.blast.hit(e, c.power * falloff, 1.2);
        }
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y, at.z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.FLAME, at.x, at.y, at.z, 24, c.radius * 0.3, 0.4, c.radius * 0.3, 0.06);
        level.sendParticles(c.particle, at.x, at.y, at.z, 20, c.radius * 0.3, 0.4, c.radius * 0.3, 0.05);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.4F, 1.1F);
    }
}

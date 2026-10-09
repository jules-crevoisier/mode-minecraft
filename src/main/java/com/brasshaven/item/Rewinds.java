package com.brasshaven.item;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Pocket-watch rewinds of the Asylum Director's bone-saw (the REWIND ability): the spot the wielder rushed from is
 * remembered as a clock ghost; when its time runs out the wielder is snapped back to it (unless sneaking, or dead, gone
 * to another level or more than 32 blocks away) and the {@link Echo} the weapon handed over plays there. Ticked from the
 * server tick, registered on first use.
 */
public final class Rewinds {
    /** What happens at the ghost when the wielder comes back (the weapon's echo cut). */
    @FunctionalInterface
    public interface Echo {
        void at(ServerLevel level, ServerPlayer player, Vec3 spot);
    }

    private static final DustParticleOptions GHOST = new DustParticleOptions(0xB8F0FF, 1.1F);

    private static final class Mark {
        final ServerLevel level;
        final ServerPlayer player;
        final Vec3 spot;
        int left;
        final Echo echo;

        Mark(ServerLevel level, ServerPlayer player, Vec3 spot, int left, Echo echo) {
            this.level = level;
            this.player = player;
            this.spot = spot;
            this.left = left;
            this.echo = echo;
        }
    }

    private static final List<Mark> MARKS = new ArrayList<>();
    private static boolean registered;

    private Rewinds() {}

    /** Remembers {@code spot} for {@code player}; {@code delay} ticks later they are snapped back to it. */
    public static void mark(ServerLevel level, ServerPlayer player, Vec3 spot, int delay, Echo echo) {
        if (!registered) {
            registered = true;
            TickEvent.ServerTickEvent.Post.BUS.addListener(e -> tick());
        }
        MARKS.removeIf(m -> m.player == player);
        if (MARKS.size() < 64) {
            MARKS.add(new Mark(level, player, spot, delay, echo));
        }
    }

    private static void tick() {
        if (MARKS.isEmpty()) {
            return;
        }
        List<Mark> due = new ArrayList<>();
        MARKS.removeIf(m -> {
            if (!m.player.isAlive() || m.player.level() != m.level || m.player.isRemoved()) {
                return true;
            }
            m.left--;
            if (m.left % 2 == 0) {
                double turn = m.left * 0.3;
                for (int h = 0; h < 12; h++) {
                    double a = h * Math.PI / 6;
                    m.level.sendParticles(GHOST, m.spot.x + Math.cos(a) * 0.9, m.spot.y + 0.15, m.spot.z + Math.sin(a) * 0.9,
                            1, 0, 0, 0, 0);
                }
                for (double d = 0.2; d <= 0.7; d += 0.25) {
                    m.level.sendParticles(ParticleTypes.END_ROD, m.spot.x + Math.cos(turn) * d, m.spot.y + 0.15,
                            m.spot.z + Math.sin(turn) * d, 1, 0, 0, 0, 0);
                }
                m.level.sendParticles(GHOST, m.spot.x, m.spot.y + 1.0, m.spot.z, 1, 0.15, 0.5, 0.15, 0.0);
            }
            if (m.left % 10 == 0 && m.left > 0) {
                m.level.playSound(null, m.spot.x, m.spot.y, m.spot.z, SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.PLAYERS, 0.6F, 1.8F);
            }
            if (m.left <= 0) {
                due.add(m);
                return true;
            }
            return false;
        });
        for (Mark m : due) {
            ServerPlayer p = m.player;
            if (p.isShiftKeyDown() || p.position().distanceTo(m.spot) > 32.0) {
                m.level.playSound(null, p, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.8F, 0.6F);
                continue;
            }
            Vec3 from = p.position();
            for (double f = 0; f <= 1.0; f += 0.1) {
                Vec3 q = from.lerp(m.spot, f);
                m.level.sendParticles(GHOST, q.x, q.y + 1.0, q.z, 1, 0.05, 0.05, 0.05, 0.0);
            }
            p.teleportTo(m.level, m.spot.x, m.spot.y, m.spot.z, Set.of(), p.getYRot(), p.getXRot(), false);
            p.setDeltaMovement(Vec3.ZERO);
            p.hurtMarked = true;
            p.fallDistance = 0;
            m.level.playSound(null, m.spot.x, m.spot.y, m.spot.z, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 1.0F, 1.2F);
            m.echo.at(m.level, p, m.spot);
        }
    }
}

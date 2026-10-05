package com.wayfarers.social;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * Emotes: a gesture everyone around sees, with no client mod code on their side beyond vanilla: the server swings
 * the player's arms (vanilla arm animation packets), makes them crouch for a bow or hop for a cheer, spawns
 * particles and plays a sound, and writes "Alice waves" above the hotbar of the players within 24 blocks.
 * One emote per {@code emotes.cooldownTicks}; an emote in progress is a few timed steps run on the server tick.
 */
public final class Emotes {
    public enum Emote { WAVE, BOW, CHEER, CLAP, POINT, LAUGH, THANKS, RALLY }

    private static final double SEEN = 24;

    /** An emote being played: its steps run on the ticks after it started. */
    private record Playing(ServerPlayer player, Emote emote, long start) {}

    private static final List<Playing> PLAYING = new ArrayList<>();

    private Emotes() {}

    static void register() {
        TickEvent.ServerTickEvent.Post.BUS.addListener(e -> {
            if (!PLAYING.isEmpty()) {
                tick(e.server().getTickCount());
            }
        });
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> PLAYING.removeIf(p -> p.player() == e.getEntity()));
    }

    static void play(ServerPlayer player, int index) {
        if (index < 0 || index >= Emote.values().length || !player.isAlive() || player.isSpectator()) {
            return;
        }
        if (!Social.require(player, Social.Feature.EMOTES)) {
            return;
        }
        if (!Social.cooldown(player, "emote", Social.config().emoteCooldown.get())) {
            return;
        }
        Emote emote = Emote.values()[index];
        PLAYING.removeIf(p -> p.player() == player);
        PLAYING.add(new Playing(player, emote, player.level().getServer().getTickCount()));
        Component line = Component.translatable("message.wayfarers.emote." + emote.name().toLowerCase(java.util.Locale.ROOT),
                player.getName()).withStyle(ChatFormatting.YELLOW);
        for (ServerPlayer p : player.level().players()) {
            if (p.distanceToSqr(player) < SEEN * SEEN) {
                p.sendOverlayMessage(line);
            }
        }
        com.wayfarers.util.Tips.show(player, "emotes");
    }

    private static void tick(long now) {
        for (Playing pl : new ArrayList<>(PLAYING)) {
            int t = (int) (now - pl.start());
            ServerPlayer p = pl.player();
            if (!p.isAlive() || p.hasDisconnected()) {
                PLAYING.remove(pl);
                continue;
            }
            if (step(p, pl.emote(), t)) {
                PLAYING.remove(pl);
            }
        }
    }

    /** One tick of an emote; true when it is over. */
    private static boolean step(ServerPlayer p, Emote emote, int t) {
        ServerLevel level = p.level();
        Vec3 eye = p.getEyePosition();
        Vec3 look = p.getLookAngle();
        Vec3 hand = eye.add(look.scale(0.6)).add(0, -0.3, 0);
        switch (emote) {
            case WAVE -> {
                if (t % 6 == 0) {
                    p.swing(InteractionHand.MAIN_HAND, true);
                    particles(level, ParticleTypes.HAPPY_VILLAGER, hand.add(0, 0.6, 0), 2, 0.15);
                }
                return t >= 24;
            }
            case BOW -> {
                if (t == 0) {
                    p.setShiftKeyDown(true);
                    sound(level, p, SoundEvents.ARMOR_EQUIP_LEATHER.value(), 0.9F);
                }
                if (t >= 25) {
                    p.setShiftKeyDown(p.getLastClientInput().shift());
                    return true;
                }
                return false;
            }
            case CHEER -> {
                if (t == 0) {
                    if (p.onGround()) {
                        p.setDeltaMovement(p.getDeltaMovement().x, 0.42, p.getDeltaMovement().z);
                        p.hurtMarked = true;
                    }
                    sound(level, p, SoundEvents.FIREWORK_ROCKET_TWINKLE, 1.2F);
                }
                if (t % 5 == 0) {
                    p.swing(t % 10 == 0 ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND, true);
                    particles(level, ParticleTypes.FIREWORK, eye.add(0, 0.7, 0), 4, 0.3);
                }
                return t >= 20;
            }
            case CLAP -> {
                if (t % 5 == 0) {
                    p.swing(t % 10 == 0 ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND, true);
                    sound(level, p, SoundEvents.WOODEN_BUTTON_CLICK_ON, 1.6F + (t % 10) * 0.02F);
                    particles(level, ParticleTypes.CRIT, hand, 3, 0.1);
                }
                return t >= 30;
            }
            case POINT -> {
                if (t == 0) {
                    p.swing(InteractionHand.MAIN_HAND, true);
                    for (int i = 1; i <= 16; i++) {
                        Vec3 at = eye.add(look.scale(i * 0.5));
                        level.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 1, 0, 0, 0, 0);
                    }
                    sound(level, p, SoundEvents.AMETHYST_BLOCK_CHIME, 1.4F);
                }
                return true;
            }
            case LAUGH -> {
                if (t % 4 == 0) {
                    level.sendParticles(ParticleTypes.NOTE, eye.x, eye.y + 0.7, eye.z, 1, 0.3, 0.1, 0.3, 1.0);
                }
                if (t == 0) {
                    sound(level, p, SoundEvents.VILLAGER_CELEBRATE, 1.5F);
                }
                return t >= 20;
            }
            case THANKS -> {
                if (t == 0) {
                    p.setShiftKeyDown(true);
                    particles(level, ParticleTypes.HEART, eye.add(0, 0.6, 0), 4, 0.4);
                    sound(level, p, SoundEvents.AMETHYST_BLOCK_RESONATE, 1.6F);
                }
                if (t >= 12) {
                    p.setShiftKeyDown(p.getLastClientInput().shift());
                    return true;
                }
                return false;
            }
            case RALLY -> {
                // a steam whistle: puffs of steam above the head and a horn everyone around hears
                if (t == 0) {
                    p.swing(InteractionHand.MAIN_HAND, true);
                    level.playSound(null, p.blockPosition(), SoundEvents.NOTE_BLOCK_DIDGERIDOO.value(), SoundSource.PLAYERS, 1.5F, 1.2F);
                }
                if (t % 3 == 0) {
                    level.sendParticles(ParticleTypes.CLOUD, eye.x, eye.y + 0.8, eye.z, 3, 0.15, 0.3, 0.15, 0.04);
                }
                return t >= 18;
            }
        }
        return true;
    }

    private static void particles(ServerLevel level, ParticleOptions type, Vec3 at, int n, double spread) {
        level.sendParticles(type, at.x, at.y, at.z, n, spread, spread, spread, 0.02);
    }

    private static void sound(ServerLevel level, ServerPlayer p, SoundEvent sound, float pitch) {
        level.playSound(null, p.getX(), p.getY(), p.getZ(), sound, SoundSource.PLAYERS, 0.7F, pitch);
    }
}

package com.brasshaven.item;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Util;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.MoonPhase;

import java.util.Locale;

/**
 * Pocket Watch: its hand follows the sun like a clock. Use: time (hh:mm), day number, moon phase and the biome you
 * stand in, above the hotbar. A mechanical watch keeps Overworld time in every dimension.
 */
public class PocketWatchItem extends GadgetItem {
    public PocketWatchItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
            return InteractionResult.SUCCESS;
        }
        long ticks = server.getOverworldClockTime();
        long day = ticks / 24000L;
        long inDay = Math.floorMod(ticks, 24000L);
        // tick 0 is 06:00
        int minutes = (int) ((inDay + 6000L) % 24000L * 1440L / 24000L);
        String time = String.format(Locale.ROOT, "%02d:%02d", minutes / 60, minutes % 60);
        MoonPhase moon = MoonPhase.values()[(int) Math.floorMod(day, (long) MoonPhase.COUNT)];
        Component biome = server.getBiome(player.blockPosition()).unwrapKey()
                .map(key -> (Component) Component.translatable(Util.makeDescriptionId("biome", key.identifier())))
                .orElse(Component.literal("?"));
        sp.sendOverlayMessage(Component.translatable("message.brasshaven.watch",
                Component.literal(time).withStyle(ChatFormatting.WHITE), day + 1,
                Component.translatable("message.brasshaven.watch.moon." + moon.getSerializedName()),
                biome.copy().withStyle(ChatFormatting.AQUA)).withStyle(ChatFormatting.GOLD));
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.NOTE_BLOCK_HAT.value(),
                SoundSource.PLAYERS, 0.35F, 1.8F);
        player.getCooldowns().addCooldown(player.getItemInHand(hand), 10);
        return InteractionResult.SUCCESS;
    }
}

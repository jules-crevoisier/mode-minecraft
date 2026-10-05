package com.brasshaven.event;

import com.brasshaven.entity.ocean.SeaSerpent;
import com.brasshaven.registry.ModEntities;
import com.brasshaven.registry.ModOcean;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.vehicle.boat.AbstractBoat;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.brewing.BrewingRecipeRegisterEvent;
import net.minecraftforge.fml.LogicalSide;

/**
 * Living oceans: the Sea Serpent rises at night under players boating or swimming over deep water, and Glow Jelly
 * brews into Night Vision.
 */
public final class OceanEvents {
    /** Seconds between two rolls for each player, and the chance of each roll. */
    private static final int CHECK_TICKS = 200;
    private static final int CHANCE = 30;

    private OceanEvents() {}

    public static void register() {
        TickEvent.PlayerTickEvent.Post.BUS.addListener(OceanEvents::onPlayerTick);
        BrewingRecipeRegisterEvent.BUS.addListener(event ->
                event.getBuilder().addMix(Potions.AWKWARD, ModOcean.GLOW_JELLY.get(), Potions.NIGHT_VISION));
    }

    private static void onPlayerTick(TickEvent.PlayerTickEvent.Post event) {
        if (event.side() != LogicalSide.SERVER || !(event.player() instanceof ServerPlayer player)
                || player.tickCount % CHECK_TICKS != 0 || player.isCreative() || player.isSpectator()) {
            return;
        }
        ServerLevel level = player.level();
        if (!com.brasshaven.config.BrasshavenConfig.SPAWNS_ENABLED.get()) {
            return;
        }
        if (level.dimension() != Level.OVERWORLD || level.getDifficulty() == Difficulty.PEACEFUL || level.isBrightOutside()) {
            return;
        }
        boolean afloat = player.getVehicle() instanceof AbstractBoat || player.isInWater();
        if (!afloat || level.getRandom().nextInt(CHANCE) != 0) {
            return;
        }
        BlockPos at = player.blockPosition();
        if (!level.getBiome(at).is(BiomeTags.IS_DEEP_OCEAN) || waterDepth(level, at) < 18) {
            return;
        }
        if (!level.getEntitiesOfClass(SeaSerpent.class, player.getBoundingBox().inflate(96)).isEmpty()) {
            return;
        }
        // rise from the deep, 20 to 28 blocks away, a few blocks under the surface
        for (int attempt = 0; attempt < 8; attempt++) {
            float angle = level.getRandom().nextFloat() * Mth.TWO_PI;
            double r = 20 + level.getRandom().nextInt(9);
            BlockPos pos = BlockPos.containing(player.getX() + Mth.cos(angle) * r, level.getSeaLevel() - 6,
                    player.getZ() + Mth.sin(angle) * r);
            if (!level.isLoaded(pos) || waterDepth(level, pos) < 14) {
                continue;
            }
            SeaSerpent serpent = ModEntities.SEA_SERPENT.get().create(level, EntitySpawnReason.EVENT);
            if (serpent == null) {
                return;
            }
            serpent.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, angle * Mth.RAD_TO_DEG + 90.0F, 0.0F);
            if (!level.noCollision(serpent)) {
                continue;
            }
            serpent.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.EVENT, null);
            serpent.markRisen();
            serpent.setTarget(player);
            level.addFreshEntity(serpent);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ELDER_GUARDIAN_CURSE,
                    SoundSource.HOSTILE, 0.8F, 0.4F);
            player.sendOverlayMessage(Component.translatable("message.brasshaven.sea_serpent.rises")
                    .withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC));
            return;
        }
    }

    /** How many water blocks lie under {@code pos} (counting from the surface down, at most 64). */
    private static int waterDepth(ServerLevel level, BlockPos pos) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(pos.getX(), level.getSeaLevel() - 1, pos.getZ());
        int depth = 0;
        while (depth < 64 && level.getFluidState(p).is(FluidTags.WATER)) {
            depth++;
            p.move(0, -1, 0);
        }
        return depth;
    }
}

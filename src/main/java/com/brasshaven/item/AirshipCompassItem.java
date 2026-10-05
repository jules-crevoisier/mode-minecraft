package com.brasshaven.item;

import com.brasshaven.generated.GeneratedContent;
import com.brasshaven.util.StructureLocator;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/**
 * Airship Compass: use it to find the nearest Sky Harbour (the Void Ship Wreck in the End); its aether needle then keeps
 * pointing there, like a lodestone compass (the item model reads the lodestone target component).
 */
public class AirshipCompassItem extends GadgetItem {
    public AirshipCompassItem(Properties properties) {
        super(properties);
    }

    private static String targetFor(ServerLevel level) {
        return level.dimension() == Level.END ? "void_ship" : "sky_harbour";
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        String target = targetFor(server);
        int index = -1;
        for (int i = 0; i < GeneratedContent.STRUCTURES.size(); i++) {
            GeneratedContent.StructureInfo info = GeneratedContent.STRUCTURES.get(i);
            if (info.id().equals(target) && server.dimension().identifier().getPath().replace("the_", "").equals(info.dimension())) {
                index = i;
            }
        }
        player.getCooldowns().addCooldown(stack, 60);
        Component name = Component.translatable("structure.brasshaven." + target);
        StructureLocator.Found found = index < 0 ? null : StructureLocator.nearestBudgeted(server, player.blockPosition(), index, 100);
        if (found == StructureLocator.BUSY) {
            player.sendSystemMessage(Component.translatable("message.brasshaven.compass.busy").withStyle(ChatFormatting.GRAY));
            return InteractionResult.SUCCESS;
        }
        if (found == null) {
            stack.remove(DataComponents.LODESTONE_TRACKER);
            player.sendSystemMessage(Component.translatable("message.brasshaven.compass.none", name).withStyle(ChatFormatting.GRAY));
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS,
                    0.5F, 0.8F);
            return InteractionResult.SUCCESS;
        }
        BlockPos from = player.blockPosition();
        BlockPos to = found.pos();
        stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(GlobalPos.of(server.dimension(), to)), false));
        int distance = (int) Math.sqrt(from.distSqr(new BlockPos(to.getX(), from.getY(), to.getZ())));
        player.sendSystemMessage(Component.translatable("message.brasshaven.compass.found", name, distance,
                StructureLocator.compassDirection(from, to), to.getX(), to.getZ()).withStyle(ChatFormatting.AQUA));
        Vec3 dir = new Vec3(to.getX() - from.getX(), 0, to.getZ() - from.getZ()).normalize();
        for (int i = 1; i <= 10; i++) {
            server.sendParticles(ParticleTypes.ELECTRIC_SPARK, player.getX() + dir.x * i * 0.8, player.getEyeY() - 0.3,
                    player.getZ() + dir.z * i * 0.8, 1, 0, 0, 0, 0);
        }
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS,
                1.0F, 1.3F);
        return InteractionResult.SUCCESS;
    }
}

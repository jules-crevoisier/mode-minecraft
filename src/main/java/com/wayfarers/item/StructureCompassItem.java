package com.wayfarers.item;

import com.wayfarers.generated.GeneratedContent;
import com.wayfarers.registry.ModDataComponents;
import com.wayfarers.util.StructureLocator;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Locates the nearest Wayfarers structure. Sneak-use cycles the target through every
 * structure (or "any"); use prints distance and heading and draws a short particle trail.
 */
public class StructureCompassItem extends TooltipItem {
    public StructureCompassItem(Properties properties) {
        super(properties);
    }

    public static Component targetName(int index) {
        if (index < 0) {
            return Component.translatable("message.wayfarers.compass.any");
        }
        return Component.translatable("structure.wayfarers." + GeneratedContent.STRUCTURES.get(index).id());
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel serverLevel)) {
            return InteractionResult.SUCCESS;
        }
        int target = stack.getOrDefault(ModDataComponents.COMPASS_TARGET.get(), -1);
        if (player.isShiftKeyDown()) {
            target = target + 1 >= GeneratedContent.STRUCTURES.size() ? -1 : target + 1;
            stack.set(ModDataComponents.COMPASS_TARGET.get(), target);
            player.sendSystemMessage(Component.translatable("message.wayfarers.compass.target", targetName(target))
                    .withStyle(ChatFormatting.AQUA));
            return InteractionResult.SUCCESS;
        }
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.FAIL;
        }
        player.getCooldowns().addCooldown(stack, 60);
        BlockPos from = player.blockPosition();
        StructureLocator.Found found = StructureLocator.nearestBudgeted(serverLevel, from, target, 100);
        if (found == StructureLocator.BUSY) {
            player.getCooldowns().addCooldown(stack, 20);
            player.sendSystemMessage(Component.translatable("message.wayfarers.compass.busy").withStyle(ChatFormatting.GRAY));
            return InteractionResult.SUCCESS;
        }
        if (found == null) {
            player.sendSystemMessage(Component.translatable("message.wayfarers.compass.none", targetName(target))
                    .withStyle(ChatFormatting.GRAY));
            return InteractionResult.SUCCESS;
        }
        int distance = (int) Math.sqrt(from.distSqr(new BlockPos(found.pos().getX(), from.getY(), found.pos().getZ())));
        player.sendSystemMessage(Component.translatable("message.wayfarers.compass.found",
                Component.translatable("structure.wayfarers." + found.structureId()), distance,
                StructureLocator.compassDirection(from, found.pos()), found.pos().getX(), found.pos().getZ())
                .withStyle(ChatFormatting.GOLD));
        Vec3 dir = new Vec3(found.pos().getX() - from.getX(), 0, found.pos().getZ() - from.getZ()).normalize();
        for (int i = 1; i <= 12; i++) {
            serverLevel.sendParticles(ParticleTypes.END_ROD, player.getX() + dir.x * i * 0.8, player.getEyeY() - 0.3,
                    player.getZ() + dir.z * i * 0.8, 1, 0, 0, 0, 0);
        }
        level.playSound(null, player, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 1.0F, 1.0F);
        return InteractionResult.SUCCESS;
    }
}

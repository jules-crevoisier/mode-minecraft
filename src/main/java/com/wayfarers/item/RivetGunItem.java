package com.wayfarers.item;

import com.wayfarers.entity.RivetEntity;
import com.wayfarers.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Rivet Gun: each use fires one rivet (5 damage), taken from your inventory: Rivets first, then iron nuggets.
 * Short cooldown, no ammo needed in creative.
 */
public class RivetGunItem extends GadgetItem {
    public static final int COOLDOWN = 14;

    public RivetGunItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack gun = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(gun)) {
            return InteractionResult.FAIL;
        }
        int ammo = findAmmo(player);
        if (ammo < 0 && !player.getAbilities().instabuild) {
            if (player instanceof ServerPlayer sp) {
                sp.sendOverlayMessage(Component.translatable("message.wayfarers.rivet_gun.empty").withStyle(ChatFormatting.GRAY));
                level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS,
                        0.6F, 1.4F);
            }
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server) {
            RivetEntity rivet = new RivetEntity(level, player);
            rivet.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 3.4F, 0.6F);
            level.addFreshEntity(rivet);
            if (!player.getAbilities().instabuild && ammo >= 0) {
                player.getInventory().getItem(ammo).shrink(1);
            }
            Vec3 look = player.getLookAngle();
            server.sendParticles(ParticleTypes.SMOKE, player.getX() + look.x * 0.9, player.getEyeY() - 0.15 + look.y * 0.9,
                    player.getZ() + look.z * 0.9, 4, 0.04, 0.04, 0.04, 0.02);
            server.sendParticles(ParticleTypes.CLOUD, player.getX() + look.x * 0.8, player.getEyeY() - 0.2 + look.y * 0.8,
                    player.getZ() + look.z * 0.8, 2, 0.05, 0.05, 0.05, 0.01);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CROSSBOW_SHOOT, SoundSource.PLAYERS,
                    0.9F, 1.7F);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PISTON_EXTEND, SoundSource.PLAYERS,
                    0.35F, 1.9F);
            gun.hurtAndBreak(1, player, hand.asEquipmentSlot());
            player.getCooldowns().addCooldown(gun, COOLDOWN);
        }
        return InteractionResult.SUCCESS;
    }

    /** Inventory slot of the next rivet (or iron nugget), -1 when there is none. */
    private static int findAmmo(Player player) {
        Inventory inv = player.getInventory();
        int nugget = -1;
        for (int i = 0; i < inv.getContainerSize(); i++) {
            ItemStack s = inv.getItem(i);
            if (s.is(ModItems.RIVET.get())) {
                return i;
            }
            if (nugget < 0 && s.is(Items.IRON_NUGGET)) {
                nugget = i;
            }
        }
        return nugget;
    }
}

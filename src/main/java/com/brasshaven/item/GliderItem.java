package com.brasshaven.item;

import com.brasshaven.event.GadgetEvents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Brass Glider: worn in the back accessory slot, or held (either hand), it opens while falling. The fall is capped to
 * a slow sink and you drift forward where you look. Nothing to click.
 *
 * <p>Player movement is client-authoritative, so the glide itself runs on the player's own client
 * ({@link #glideClient}, before the movement of that tick). The server keeps the fall damage at zero, wears the
 * glider down, and shows the wing-tip trails to everyone ({@link #glideServer}).
 */
public class GliderItem extends GadgetItem {
    public static final double SINK = -0.08;
    public static final double GLIDE_SPEED = 0.5;
    /** Client: the local player's glider is open. */
    private static boolean open;
    private static final Map<UUID, Double> LAST_Y = new HashMap<>();
    private static final Set<UUID> GLIDING = new HashSet<>();

    public GliderItem(Properties properties) {
        super(properties);
    }

    public static @Nullable InteractionHand heldHand(Player player) {
        if (player.getMainHandItem().getItem() instanceof GliderItem) {
            return InteractionHand.MAIN_HAND;
        }
        return player.getOffhandItem().getItem() instanceof GliderItem ? InteractionHand.OFF_HAND : null;
    }

    /** The glider in use: held (either hand) first, else worn on the back; EMPTY when there is none. */
    public static ItemStack glider(Player player) {
        InteractionHand hand = heldHand(player);
        if (hand != null) {
            return player.getItemInHand(hand);
        }
        return com.brasshaven.accessory.Accessories.find(player, s -> s.getItem() instanceof GliderItem);
    }

    private static boolean airborne(Player player) {
        return !player.onGround() && !player.isInWater() && !player.isInLava() && !player.isFallFlying()
                && !player.isAutoSpinAttack() && !player.getAbilities().flying && !player.isPassenger()
                && !player.onClimbable() && !player.isSpectator();
    }

    /** Local player, before its movement: sink slowly and glide forward. */
    public static void glideClient(Player player) {
        if (glider(player).isEmpty() || !airborne(player)) {
            open = false;
            return;
        }
        Vec3 v = player.getDeltaMovement();
        if (!open) {
            // open only in a real fall, not at the top of every jump
            boolean groundBelow = !player.level().noCollision(player, player.getBoundingBox().move(0.0, -2.0, 0.0));
            if (v.y > -0.25 || groundBelow) {
                return;
            }
            open = true;
        }
        Vec3 look = player.getLookAngle();
        double h = Math.sqrt(look.x * look.x + look.z * look.z);
        double tx = h < 1.0E-4 ? 0.0 : look.x / h * GLIDE_SPEED;
        double tz = h < 1.0E-4 ? 0.0 : look.z / h * GLIDE_SPEED;
        player.setDeltaMovement(Mth.lerp(0.2, v.x, tx), Math.max(v.y, SINK), Mth.lerp(0.2, v.z, tz));
        player.resetFallDistance();
    }

    /**
     * Server side. Any fall with the glider in hand is soft (so a late or missed "open" can never hurt); once the
     * fall is real (no ground just below) the glider counts as open: flap sound, wing-tip trails, wear.
     */
    public static void glideServer(ServerPlayer player) {
        UUID id = player.getUUID();
        Double lastY = LAST_Y.put(id, player.getY());
        InteractionHand hand = heldHand(player);
        ItemStack glider = glider(player);
        if (glider.isEmpty() || !airborne(player)) {
            GLIDING.remove(id);
            return;
        }
        double dy = lastY == null ? 0.0 : player.getY() - lastY;
        if (dy < -0.02) {
            player.resetFallDistance();
            GadgetEvents.softLanding(player, 10);
        }
        ServerLevel level = player.level();
        if (!GLIDING.contains(id)) {
            boolean groundBelow = !level.noCollision(player, player.getBoundingBox().move(0.0, -2.0, 0.0));
            if (dy > -0.15 || groundBelow) {
                return;
            }
            GLIDING.add(id);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PHANTOM_FLAP, SoundSource.PLAYERS,
                    0.5F, 1.4F);
        }
        if (player.tickCount % 3 == 0) {
            float yaw = player.getYRot() * Mth.DEG_TO_RAD;
            double rx = Math.cos(yaw), rz = Math.sin(yaw);
            for (int side = -1; side <= 1; side += 2) {
                level.sendParticles(ParticleTypes.CLOUD, player.getX() + rx * side * 1.1, player.getY() + 2.0,
                        player.getZ() + rz * side * 1.1, 1, 0.02, 0.02, 0.02, 0.0);
            }
        }
        if (player.tickCount % 40 == 0 && !player.getAbilities().instabuild) {
            if (hand != null) {
                glider.hurtAndBreak(1, player, hand.asEquipmentSlot());
            } else { // worn on the back
                glider.hurtAndBreak(1, level, player, item -> level.playSound(null, player.getX(), player.getY(),
                        player.getZ(), SoundEvents.ITEM_BREAK.value(), SoundSource.PLAYERS, 0.8F, 1.0F));
                com.brasshaven.accessory.Accessories.changed(player);
            }
        }
    }

    public static void forget(UUID id) {
        LAST_Y.remove(id);
        GLIDING.remove(id);
    }
}

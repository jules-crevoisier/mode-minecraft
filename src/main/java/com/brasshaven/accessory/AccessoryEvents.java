package com.brasshaven.accessory;

import com.brasshaven.item.MagnetRingItem;
import com.brasshaven.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.EnchantmentEffectComponents;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.listener.Priority;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

/**
 * Accessory life cycle: the slots are added when a player object enters a level (both sides), worn items follow the
 * keepInventory rule on death (kept, or dropped with the rest of the inventory, so into the grave), and the effects
 * that act every tick (Magnet Ring, Pocket Watch) run here, only for worn items.
 */
public final class AccessoryEvents {
    /** Player -> time of day (0..23999) at the last Pocket Watch check. */
    private static final Map<UUID, Long> WATCH = new HashMap<>();

    private AccessoryEvents() {}

    public static void register() {
        EntityJoinLevelEvent.BUS.addListener((Predicate<EntityJoinLevelEvent>) e -> {
            if (e.getEntity() instanceof Player p) {
                Accessories.ensure(p);
            }
            return false;
        });
        PlayerEvent.Clone.BUS.addListener(AccessoryEvents::onClone);
        // before the grave (GraveEvents) collects the drops
        LivingDropsEvent.BUS.addListener(Priority.HIGH, (Predicate<LivingDropsEvent>) AccessoryEvents::onDrops);
        TickEvent.PlayerTickEvent.Post.BUS.addListener(AccessoryEvents::onTick);
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer sp) {
                Accessories.flush(sp);
            }
            WATCH.remove(e.getEntity().getUUID());
        });
    }

    private static void onClone(PlayerEvent.Clone e) {
        if (!(e.getEntity() instanceof ServerPlayer now) || !(e.getOriginal() instanceof ServerPlayer old)) {
            return;
        }
        Accessories.flush(old);
        boolean keep = !e.isWasDeath() || old.isSpectator() || now.level().getGameRules().get(GameRules.KEEP_INVENTORY);
        if (keep && old.getPersistentData().contains(Accessories.KEY)) {
            now.getPersistentData().put(Accessories.KEY, old.getPersistentData().getCompoundOrEmpty(Accessories.KEY).copy());
        } else {
            now.getPersistentData().remove(Accessories.KEY);
        }
        Accessories.reload(now);
    }

    private static boolean onDrops(LivingDropsEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer player) || player.isSpectator()
                || !(player.level() instanceof ServerLevel level) || level.getGameRules().get(GameRules.KEEP_INVENTORY)) {
            return false;
        }
        AccessoryContainer c = Accessories.get(player);
        for (int i = 0; i < c.getContainerSize(); i++) {
            ItemStack stack = c.removeItemNoUpdate(i);
            if (stack.isEmpty() || EnchantmentHelper.has(stack, EnchantmentEffectComponents.PREVENT_EQUIPMENT_DROP)) {
                continue;
            }
            ItemEntity item = new ItemEntity(level, player.getX(), player.getEyeY() - 0.3, player.getZ(), stack);
            item.setDefaultPickUpDelay();
            e.getDrops().add(item);
        }
        c.setChanged();
        return false;
    }

    private static void onTick(TickEvent.PlayerTickEvent.Post event) {
        if (!(event.player() instanceof ServerPlayer player) || !(player.level() instanceof ServerLevel level)) {
            return;
        }
        long t = level.getGameTime() + player.getId();
        if (t % 4 == 0) { // staggered: not every player on the same tick
            ItemStack magnet = Accessories.worn(player, ModItems.MAGNET_RING.get());
            if (!magnet.isEmpty() && MagnetRingItem.isEnabled(magnet)) {
                MagnetRingItem.pull(player, level);
            }
        }
        if (t % 20 == 0) {
            watch(player, level);
        }
        if (t % 600 == 0) { // worn stacks change in place (durability): keep the saved copy fresh
            Accessories.flush(player);
        }
    }

    /** A Pocket Watch on the belt chimes when night is near (17:30) and when a new day starts (06:00). */
    private static void watch(ServerPlayer player, ServerLevel level) {
        if (!Accessories.wears(player, ModItems.POCKET_WATCH.get())) {
            WATCH.remove(player.getUUID());
            return;
        }
        long now = Math.floorMod(level.getOverworldClockTime(), 24000L);
        Long last = WATCH.put(player.getUUID(), now);
        if (last == null) {
            return;
        }
        String msg = null;
        if (last < 11500L && now >= 11500L) {
            msg = "message.brasshaven.watch.dusk";
        } else if (now < last) { // past midnight of the clock: 06:00, or a night slept through
            msg = "message.brasshaven.watch.dawn";
        }
        if (msg != null) {
            player.sendOverlayMessage(Component.translatable(msg).withStyle(ChatFormatting.GOLD));
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.NOTE_BLOCK_BELL.value(),
                    SoundSource.PLAYERS, 0.5F, 1.6F);
        }
    }
}

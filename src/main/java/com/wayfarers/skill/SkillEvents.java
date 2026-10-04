package com.wayfarers.skill;

import com.wayfarers.network.SkillSyncMsg;
import com.wayfarers.network.WayfarersNet;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerXpEvent;
import net.minecraftforge.fml.LogicalSide;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/** Talents and mana at runtime: apply passives, regenerate mana, lifesteal, self-repair, active abilities. */
public final class SkillEvents {
    private static final Map<UUID, Integer> LAST_SYNC = new HashMap<>();

    private SkillEvents() {}

    public static void register() {
        PlayerEvent.PlayerLoggedInEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                PlayerSkills.apply(p);
                sync(p);
            }
        });
        PlayerEvent.PlayerRespawnEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                PlayerSkills.apply(p);
                sync(p);
            }
        });
        PlayerEvent.PlayerChangedDimensionEvent.BUS.addListener(e -> {
            if (e.getEntity() instanceof ServerPlayer p) {
                PlayerSkills.apply(p);
            }
        });
        PlayerXpEvent.LevelChange.BUS.addListener((Consumer<PlayerXpEvent.LevelChange>) e -> {
            if (e.getEntity() instanceof ServerPlayer p && e.getLevels() > 0) {
                int before = PlayerSkills.availablePoints(p);
                PlayerSkills.addLevels(p, e.getLevels());
                if (PlayerSkills.availablePoints(p) > before) {
                    p.sendSystemMessage(Component.translatable("message.wayfarers.skill.point", Component.keybind("key.wayfarers.skills"))
                            .withStyle(ChatFormatting.LIGHT_PURPLE));
                }
                sync(p);
            }
        });
        LivingDamageEvent.BUS.addListener((Consumer<LivingDamageEvent>) e -> {
            if (e.getSource().getEntity() instanceof ServerPlayer p && e.getSource().getDirectEntity() == p) {
                float steal = PlayerSkills.lifesteal(p);
                if (steal > 0) {
                    p.heal(e.getAmount() * steal);
                }
            }
        });
        TickEvent.PlayerTickEvent.Post.BUS.addListener(SkillEvents::onTick);
        PlayerEvent.PlayerLoggedOutEvent.BUS.addListener(e -> LAST_SYNC.remove(e.getEntity().getUUID()));
    }

    private static void onTick(TickEvent.PlayerTickEvent.Post event) {
        if (event.side() != LogicalSide.SERVER || !(event.player() instanceof ServerPlayer p) || p.tickCount % 10 != 0) {
            return;
        }
        // maxMana scans the inventory and parses the talent list: compute it once per check, not three times
        float max = PlayerSkills.maxMana(p);
        float mana = PlayerSkills.mana(p);
        if (mana < max) {
            mana = PlayerSkills.setMana(p, mana + PlayerSkills.regenPerSecond(p) * 0.5F, max);
        } else if (mana > max) {
            mana = PlayerSkills.setMana(p, max, max);
        }
        int repair = PlayerSkills.repairInterval(p);
        if (repair > 0 && p.tickCount % (repair * 20) < 10) {
            ItemStack held = p.getMainHandItem();
            if (held.isDamaged()) {
                held.setDamageValue(held.getDamageValue() - 1);
            }
        }
        // keep the client's mana bar fresh while it changes
        int key = (int) mana * 1000 + (int) max;
        Integer last = LAST_SYNC.put(p.getUUID(), key);
        if (last == null || last != key) {
            sync(p);
        }
    }

    public static void sync(ServerPlayer p) {
        WayfarersNet.toPlayer(p, new SkillSyncMsg(PlayerSkills.availablePoints(p), PlayerSkills.earnedPoints(p),
                java.util.List.copyOf(PlayerSkills.unlocked(p)), PlayerSkills.active(p), PlayerSkills.mana(p),
                PlayerSkills.maxMana(p), Math.max(0L, PlayerSkills.cooldownUntil(p, PlayerSkills.active(p)) - p.level().getGameTime())));
    }

    /** Uses the selected capstone ability (V key). */
    public static void useActive(ServerPlayer p) {
        String ability = PlayerSkills.active(p);
        if (ability.isEmpty()) {
            p.sendOverlayMessage(Component.translatable("message.wayfarers.skill.no_active").withStyle(ChatFormatting.GRAY));
            return;
        }
        long now = p.level().getGameTime();
        long until = PlayerSkills.cooldownUntil(p, ability);
        if (now < until) {
            p.sendOverlayMessage(Component.translatable("message.wayfarers.skill.cooldown", (until - now + 19) / 20)
                    .withStyle(ChatFormatting.GRAY));
            return;
        }
        int cooldown;
        switch (ability) {
            case "fury" -> {
                p.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 200, 1));
                p.addEffect(new MobEffectInstance(MobEffects.SPEED, 200, 0));
                p.level().playSound(null, p, SoundEvents.RAVAGER_ROAR, SoundSource.PLAYERS, 0.6F, 1.4F);
                cooldown = 60;
            }
            case "dash" -> {
                Vec3 look = p.getLookAngle().multiply(1, 0, 1).normalize().scale(2.6);
                p.setDeltaMovement(look.x, 0.25, look.z);
                p.hurtMarked = true;
                p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20, 0));
                p.level().playSound(null, p, SoundEvents.BREEZE_WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 0.8F, 1.3F);
                cooldown = 8;
            }
            case "shield" -> {
                p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 300, 2));
                p.level().playSound(null, p, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0F, 1.0F);
                cooldown = 45;
            }
            case "overdrive" -> {
                p.addEffect(new MobEffectInstance(MobEffects.HASTE, 300, 2));
                p.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 300, 0));
                p.level().playSound(null, p, SoundEvents.PISTON_EXTEND, SoundSource.PLAYERS, 1.0F, 0.6F);
                cooldown = 60;
            }
            default -> {
                return;
            }
        }
        PlayerSkills.setCooldown(p, ability, now + cooldown * 20L);
        sync(p);
    }

    @SuppressWarnings("unused")
    private static boolean isPlayer(Object o) {
        return o instanceof Player;
    }
}

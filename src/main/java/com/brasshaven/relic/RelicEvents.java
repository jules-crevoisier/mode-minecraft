package com.brasshaven.relic;

import com.brasshaven.Brasshaven;
import com.brasshaven.accessory.Accessories;
import com.brasshaven.util.Targets;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingFallEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

import java.util.function.Consumer;
import java.util.function.Predicate;

/**
 * Set bonuses of the four relic armour sets and the worn effects of the relic accessories (tools/wf/relics.py writes
 * the same rules into the tooltips). Effects refresh once a second, staggered per player; attribute bonuses are
 * transient modifiers that come and go with the gear.
 */
public final class RelicEvents {
    public enum RelicSet { FROSTPLATE, MAGMAGUARD, TIDEWARDEN, WINDROBE, NONE }

    private static final Identifier WINDROBE_SPEED = Brasshaven.id("relic/windrobe_speed");
    private static final Identifier BAND_SPEED = Brasshaven.id("relic/pilgrim_band_speed");
    private static final Identifier GIRDLE_HEALTH = Brasshaven.id("relic/oath_girdle_health");
    private static final Identifier GIRDLE_KNOCKBACK = Brasshaven.id("relic/oath_girdle_knockback");
    /** Biomes at or below this base temperature count as "cold lands" (snowy plains 0.0, taiga 0.25 not). */
    private static final float COLD = 0.15F;
    private static final int LOCKET_COOLDOWN = 90 * 20;

    private RelicEvents() {}

    public static void register() {
        TickEvent.PlayerTickEvent.Post.BUS.addListener(RelicEvents::onTick);
        LivingAttackEvent.BUS.addListener((Predicate<LivingAttackEvent>) RelicEvents::onAttack);
        LivingHurtEvent.BUS.addListener((Consumer<LivingHurtEvent>) RelicEvents::onHurt);
        LivingDamageEvent.BUS.addListener((Consumer<LivingDamageEvent>) RelicEvents::onDamage);
        LivingFallEvent.BUS.addListener((Predicate<LivingFallEvent>) RelicEvents::onFall);
    }

    public static RelicSet fullSet(Player player) {
        Item head = player.getItemBySlot(EquipmentSlot.HEAD).getItem();
        Item chest = player.getItemBySlot(EquipmentSlot.CHEST).getItem();
        Item legs = player.getItemBySlot(EquipmentSlot.LEGS).getItem();
        Item feet = player.getItemBySlot(EquipmentSlot.FEET).getItem();
        if (head == RelicGear.FROSTPLATE_HELMET.get() && chest == RelicGear.FROSTPLATE_CHESTPLATE.get()
                && legs == RelicGear.FROSTPLATE_LEGGINGS.get() && feet == RelicGear.FROSTPLATE_BOOTS.get()) {
            return RelicSet.FROSTPLATE;
        }
        if (head == RelicGear.MAGMAGUARD_HELMET.get() && chest == RelicGear.MAGMAGUARD_CHESTPLATE.get()
                && legs == RelicGear.MAGMAGUARD_LEGGINGS.get() && feet == RelicGear.MAGMAGUARD_BOOTS.get()) {
            return RelicSet.MAGMAGUARD;
        }
        if (head == RelicGear.TIDEWARDEN_HELMET.get() && chest == RelicGear.TIDEWARDEN_CHESTPLATE.get()
                && legs == RelicGear.TIDEWARDEN_LEGGINGS.get() && feet == RelicGear.TIDEWARDEN_BOOTS.get()) {
            return RelicSet.TIDEWARDEN;
        }
        if (head == RelicGear.WINDROBE_HELMET.get() && chest == RelicGear.WINDROBE_CHESTPLATE.get()
                && legs == RelicGear.WINDROBE_LEGGINGS.get() && feet == RelicGear.WINDROBE_BOOTS.get()) {
            return RelicSet.WINDROBE;
        }
        return RelicSet.NONE;
    }

    private static MobEffectInstance quiet(Holder<MobEffect> effect, int ticks, int amplifier) {
        return new MobEffectInstance(effect, ticks, amplifier, true, false, true);
    }

    private static boolean cold(ServerLevel level, Player player) {
        return level.getBiome(player.blockPosition()).value().getBaseTemperature() <= COLD;
    }

    // ------------------------------------------------------------------ every second
    private static void onTick(TickEvent.PlayerTickEvent.Post event) {
        if (!(event.player() instanceof ServerPlayer player) || !(player.level() instanceof ServerLevel level)
                || player.isSpectator()) {
            return;
        }
        long t = level.getGameTime() + player.getId() * 7L;
        if (t % 20 != 0) {
            return;
        }
        RelicSet set = fullSet(player);
        boolean mantle = Accessories.wears(player, RelicGear.JARL_MANTLE.get());
        if (set == RelicSet.FROSTPLATE || mantle) {
            player.setTicksFrozen(0);
            if (cold(level, player)) {
                player.addEffect(quiet(MobEffects.RESISTANCE, 60, 0));
            }
        }
        switch (set) {
            case MAGMAGUARD -> {
                if (player.isOnFire() || player.isInLava()) {
                    player.addEffect(quiet(MobEffects.STRENGTH, 60, 0));
                }
            }
            case TIDEWARDEN -> {
                if (player.isUnderWater()) {
                    player.addEffect(quiet(MobEffects.WATER_BREATHING, 60, 0));
                }
                if (player.isInWater()) {
                    player.addEffect(quiet(MobEffects.DOLPHINS_GRACE, 60, 0));
                }
                if (t % 80 == 0 && player.isInWaterOrRain() && player.getHealth() < player.getMaxHealth()) {
                    player.heal(1.0F);
                }
            }
            case WINDROBE -> player.addEffect(quiet(MobEffects.JUMP_BOOST, 60, 0));
            default -> {
            }
        }
        if (player.isUnderWater() && Accessories.wears(player, RelicGear.TIDE_PENDANT.get())) {
            player.addEffect(quiet(MobEffects.WATER_BREATHING, 60, 0));
            player.addEffect(quiet(MobEffects.CONDUIT_POWER, 60, 0));
        }
        modifier(player, Attributes.MOVEMENT_SPEED, WINDROBE_SPEED, set == RelicSet.WINDROBE, 0.10,
                AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        modifier(player, Attributes.MOVEMENT_SPEED, BAND_SPEED, Accessories.wears(player, RelicGear.PILGRIM_BAND.get()), 0.10,
                AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        boolean girdle = Accessories.wears(player, RelicGear.OATH_GIRDLE.get());
        modifier(player, Attributes.MAX_HEALTH, GIRDLE_HEALTH, girdle, 4.0, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.KNOCKBACK_RESISTANCE, GIRDLE_KNOCKBACK, girdle, 0.3, AttributeModifier.Operation.ADD_VALUE);
    }

    /** Adds or removes one transient modifier so it matches {@code on}. */
    private static void modifier(Player player, Holder<Attribute> attribute, Identifier id, boolean on, double amount,
                                 AttributeModifier.Operation op) {
        AttributeInstance inst = player.getAttribute(attribute);
        if (inst == null || inst.hasModifier(id) == on) {
            return;
        }
        if (on) {
            inst.addTransientModifier(new AttributeModifier(id, amount, op));
        } else {
            inst.removeModifier(id);
            if (player.getHealth() > player.getMaxHealth()) {
                player.setHealth(player.getMaxHealth());
            }
        }
    }

    // ------------------------------------------------------------------ combat
    /** Magmaguard: magma blocks never burn the wearer (returning true cancels the hit). */
    private static boolean onAttack(LivingAttackEvent e) {
        return e.getEntity() instanceof Player p && e.getSource().is(DamageTypes.HOT_FLOOR) && fullSet(p) == RelicSet.MAGMAGUARD;
    }

    private static void onHurt(LivingHurtEvent e) {
        DamageSource src = e.getSource();
        LivingEntity victim = e.getEntity();
        if (victim.level().isClientSide()) {
            return;
        }
        // a melee blow on a relic armour wearer
        if (victim instanceof Player p && src.getEntity() instanceof LivingEntity attacker && src.getDirectEntity() == attacker
                && attacker != p) {
            RelicSet set = fullSet(p);
            if (set == RelicSet.FROSTPLATE) {
                attacker.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), p);
            } else if (set == RelicSet.MAGMAGUARD) {
                attacker.igniteForSeconds(4.0F);
            }
        }
        // the Ember Signet: the wearer's own melee blows set foes ablaze
        if (src.getEntity() instanceof Player p && src.getDirectEntity() == p && Targets.foe(p, victim)
                && Accessories.wears(p, RelicGear.EMBER_SIGNET.get())) {
            victim.igniteForSeconds(3.0F);
        }
    }

    /** The Halo Locket: a blow that leaves the wearer under 3 hearts calls the halo (90 s cooldown on the locket). */
    private static void onDamage(LivingDamageEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !(p.level() instanceof ServerLevel level)) {
            return;
        }
        float after = p.getHealth() - e.getAmount();
        if (after <= 0 || after >= 6.0F) {
            return;
        }
        ItemStack locket = Accessories.worn(p, RelicGear.HALO_LOCKET.get());
        if (locket.isEmpty() || p.getCooldowns().isOnCooldown(locket)) {
            return;
        }
        p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 160, 1));
        p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 160, 1));
        p.getCooldowns().addCooldown(locket, LOCKET_COOLDOWN);
        level.sendParticles(ParticleTypes.END_ROD, p.getX(), p.getY() + 1.0, p.getZ(), 30, 0.5, 0.8, 0.5, 0.05);
        level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.2F, 1.4F);
        p.sendOverlayMessage(Component.translatable("message.brasshaven.relic.halo_locket").withStyle(ChatFormatting.GOLD));
    }

    /** Windrobes: no fall damage below 12 blocks, half above; the Wind Band takes off another third. */
    private static boolean onFall(LivingFallEvent e) {
        if (!(e.getEntity() instanceof Player p)) {
            return false;
        }
        if (fullSet(p) == RelicSet.WINDROBE) {
            if (e.getDistance() < 12) {
                return true;
            }
            e.setDamageMultiplier(e.getDamageMultiplier() * 0.5F);
        }
        if (Accessories.wears(p, RelicGear.PILGRIM_BAND.get())) {
            e.setDamageMultiplier(e.getDamageMultiplier() * 0.67F);
        }
        return false;
    }
}

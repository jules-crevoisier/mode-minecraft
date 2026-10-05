package com.brasshaven.item;

import com.brasshaven.skill.ManaItems;
import com.brasshaven.skill.PlayerSkills;
import com.brasshaven.util.Targets;
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
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * A staff, wand or orb holding one spell. Right-click to cast it for mana (no cooldown bar to manage,
 * just the mana bar). Spell power and mana cost improve with the Arcanist talents.
 */
public class SpellItem extends TooltipItem {
    public enum Spell { FIRE_BOLT, FROST_NOVA, CHAIN_LIGHTNING, HEALING, LEVITATION, WARD, STEAM_BLAST }

    private final Spell spell;
    private final float cost;
    private final int cooldown;

    public SpellItem(Properties properties, Spell spell, float cost, int cooldown) {
        super(properties);
        this.spell = spell;
        this.cost = cost;
        this.cooldown = cooldown;
    }

    public float cost() {
        return cost;
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.getCooldowns().isOnCooldown(stack)) {
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
            if (!ManaItems.spend(sp, cost)) {
                sp.sendOverlayMessage(Component.translatable("message.brasshaven.mana.low").withStyle(ChatFormatting.BLUE));
                level.playSound(null, player, SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 0.4F, 1.6F);
                return InteractionResult.FAIL;
            }
            cast(server, sp, PlayerSkills.spellPower(sp));
            player.getCooldowns().addCooldown(stack, cooldown);
        }
        return InteractionResult.SUCCESS;
    }

    private void cast(ServerLevel level, ServerPlayer player, float power) {
        Vec3 eye = player.getEyePosition();
        Vec3 look = player.getLookAngle();
        switch (spell) {
            case FIRE_BOLT -> {
                LivingEntity hit = beam(level, player, 24, ParticleTypes.FLAME);
                if (hit != null) {
                    hurt(level, player, hit, 7F * power);
                    hit.igniteForSeconds(5F);
                    level.sendParticles(ParticleTypes.LAVA, hit.getX(), hit.getY() + 1, hit.getZ(), 8, 0.3, 0.4, 0.3, 0.0);
                }
                sound(level, player, SoundEvents.BLAZE_SHOOT, 1.1F);
            }
            case FROST_NOVA -> {
                double r = 5.5;
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(r, 2, r))) {
                    if (e.distanceTo(player) <= r) {
                        hurt(level, player, e, 4F * power);
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 2));
                        e.setTicksFrozen(Math.max(e.getTicksFrozen(), 160));
                    }
                }
                for (int a = 0; a < 360; a += 8) {
                    double rad = Math.toRadians(a);
                    level.sendParticles(ParticleTypes.SNOWFLAKE, player.getX() + Math.cos(rad) * r, player.getY() + 0.3,
                            player.getZ() + Math.sin(rad) * r, 2, 0.1, 0.1, 0.1, 0.01);
                }
                sound(level, player, SoundEvents.GLASS_BREAK, 0.7F);
            }
            case CHAIN_LIGHTNING -> {
                LivingEntity target = beam(level, player, 20, ParticleTypes.ELECTRIC_SPARK);
                Set<LivingEntity> struck = new HashSet<>();
                float damage = 8F * power;
                Vec3 from = eye;
                for (int i = 0; i < 4 && target != null; i++) {
                    struck.add(target);
                    arc(level, from, target.position().add(0, target.getBbHeight() / 2, 0));
                    hurt(level, player, target, damage);
                    damage *= 0.7F;
                    from = target.position().add(0, target.getBbHeight() / 2, 0);
                    LivingEntity next = null;
                    double best = 6 * 6;
                    for (LivingEntity e : foes(level, player, target.getBoundingBox().inflate(6))) {
                        double d = e.distanceToSqr(target);
                        if (!struck.contains(e) && d < best) {
                            best = d;
                            next = e;
                        }
                    }
                    target = next;
                }
                sound(level, player, SoundEvents.TRIDENT_THUNDER.value(), 1.6F);
            }
            case HEALING -> {
                float amount = 6F * power;
                for (Player p : level.getEntitiesOfClass(Player.class, player.getBoundingBox().inflate(6))) {
                    p.heal(amount);
                    p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 0));
                    level.sendParticles(ParticleTypes.HEART, p.getX(), p.getY() + 1.8, p.getZ(), 4, 0.4, 0.3, 0.4, 0.0);
                }
                sound(level, player, SoundEvents.AMETHYST_BLOCK_CHIME, 1.2F);
            }
            case LEVITATION -> {
                if (player.isShiftKeyDown()) {
                    player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 240, 0));
                    level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY(), player.getZ(), 15, 0.4, 0.1, 0.4, 0.02);
                } else {
                    LivingEntity hit = beam(level, player, 20, ParticleTypes.END_ROD);
                    if (hit != null) {
                        hit.addEffect(new MobEffectInstance(MobEffects.LEVITATION, (int) (50 * power), 1));
                    }
                }
                sound(level, player, SoundEvents.SHULKER_SHOOT, 1.2F);
            }
            case WARD -> {
                player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 600, (int) Math.min(3, power)));
                player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 0));
                level.sendParticles(ParticleTypes.ENCHANT, player.getX(), player.getY() + 1, player.getZ(), 40, 0.6, 0.8, 0.6, 0.6);
                sound(level, player, SoundEvents.BEACON_POWER_SELECT, 1.4F);
            }
            case STEAM_BLAST -> {
                Vec3 flat = look.multiply(1, 0, 1).normalize();
                for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(6, 2, 6))) {
                    Vec3 to = e.position().subtract(player.position()).multiply(1, 0, 1);
                    if (to.length() < 6 && (to.length() < 1 || to.normalize().dot(flat) > 0.5)) {
                        hurt(level, player, e, 3F * power);
                        Vec3 push = to.normalize().scale(1.8 * power);
                        e.push(push.x, 0.5, push.z);
                        e.hurtMarked = true;
                        e.clearFire();
                    }
                }
                for (int i = 1; i <= 6; i++) {
                    Vec3 p = player.position().add(flat.scale(i));
                    level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 1, p.z, 6, 0.3 * i / 3, 0.3, 0.3 * i / 3, 0.02);
                }
                player.clearFire();
                sound(level, player, SoundEvents.FIRE_EXTINGUISH, 0.6F);
            }
        }
    }

    // ------------------------------------------------------------------ helpers
    private static List<LivingEntity> foes(ServerLevel level, Player player, AABB box) {
        return level.getEntitiesOfClass(LivingEntity.class, box, e -> Targets.foe(player, e));
    }

    private static void hurt(ServerLevel level, ServerPlayer player, LivingEntity e, float amount) {
        e.hurtServer(level, level.damageSources().indirectMagic(player, player), amount);
    }

    private static void sound(ServerLevel level, Player player, SoundEvent sound, float pitch) {
        level.playSound(null, player, sound, SoundSource.PLAYERS, 0.9F, pitch);
    }

    /** Traces a bolt from the eyes (stopped by blocks), with particles; returns the first creature hit. */
    private static LivingEntity beam(ServerLevel level, ServerPlayer player, double range, ParticleOptions particle) {
        Vec3 eye = player.getEyePosition();
        Vec3 look = player.getLookAngle();
        HitResult block = level.clip(new ClipContext(eye, eye.add(look.scale(range)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player));
        double max = block.getType() == HitResult.Type.MISS ? range : block.getLocation().distanceTo(eye);
        for (double d = 1; d <= max; d += 0.5) {
            Vec3 p = eye.add(look.scale(d));
            if (((int) (d * 2)) % 2 == 0) {
                level.sendParticles(particle, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
            }
            List<LivingEntity> hits = foes(level, player, new AABB(p, p).inflate(0.6));
            if (!hits.isEmpty()) {
                return hits.get(0);
            }
        }
        return null;
    }

    private static void arc(ServerLevel level, Vec3 a, Vec3 b) {
        List<Vec3> points = new ArrayList<>();
        int n = (int) Math.max(4, a.distanceTo(b) * 3);
        for (int i = 0; i <= n; i++) {
            points.add(a.lerp(b, i / (double) n).add((level.getRandom().nextDouble() - 0.5) * 0.3,
                    (level.getRandom().nextDouble() - 0.5) * 0.3, (level.getRandom().nextDouble() - 0.5) * 0.3));
        }
        for (Vec3 p : points) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }
}

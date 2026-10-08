package com.brasshaven.colossal;

import com.brasshaven.entity.automaton.HotRivetEntity;
import com.brasshaven.item.AbilityItem;
import com.brasshaven.item.BrassTooltip;
import com.brasshaven.util.Targets;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/**
 * A vault weapon or tool of the colossal structures: one small right-click each (a grappling hook, a fan of rivets, a
 * flaring lantern, a sun flash, a boarding rush, a poisoned dart); the passives (poison, sunfire, water bonus) live in
 * {@link ColossalEvents}. Abilities never hurt players or tame and friendly creatures ({@link Targets#foe}).
 */
public class ColossalWeaponItem extends AbilityItem {
    public enum Kind { SLUICE_HOOK, RIVET_CANNON, BOG_LANTERN, SOLAR_KHOPESH, BOARDING_AXE, JADE_BLOWPIPE }

    private static final double HOOK_RANGE = 14;

    private final Kind kind;
    private final String structure;

    public ColossalWeaponItem(Properties properties, Kind kind, int cooldown, String structure) {
        super(properties, cooldown, 1);
        this.kind = kind;
        this.structure = structure;
    }

    public Kind kind() {
        return kind;
    }

    @Override
    public void facts(ItemStack stack, List<Component> facts, List<Component> details) {
        super.facts(stack, facts, details);
        details.add(BrassTooltip.detail(Component.translatable("tooltip.brasshaven.ability.foes")));
        details.add(BrassTooltip.detail(Component.translatable("tooltip.brasshaven.relic",
                Component.translatable("tooltip.brasshaven.relic." + structure))));
    }

    private static List<LivingEntity> foes(ServerLevel level, Player player, AABB box) {
        return level.getEntitiesOfClass(LivingEntity.class, box, e -> Targets.foe(player, e));
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        return switch (kind) {
            case SLUICE_HOOK -> hook(level, player);
            case RIVET_CANNON -> rivets(level, player);
            case BOG_LANTERN -> lantern(level, player);
            case SOLAR_KHOPESH -> flash(level, player);
            case BOARDING_AXE -> rush(level, player);
            case JADE_BLOWPIPE -> dart(level, player);
        };
    }

    /** The hook flies along the look: the first foe it meets is hurt and dragged in; else, if it bites a block, the
     *  wielder is hauled to it. Nothing in reach: no cooldown. */
    private static boolean hook(ServerLevel level, Player player) {
        Vec3 eye = player.getEyePosition();
        Vec3 look = player.getLookAngle();
        BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(HOOK_RANGE)), ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE, player));
        double reach = wall.getType() == HitResult.Type.MISS ? HOOK_RANGE : wall.getLocation().distanceTo(eye);
        LivingEntity caught = null;
        double best = reach + 1;
        for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(reach + 1))) {
            Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
            double along = to.dot(look);
            if (along > 0 && along <= reach && to.subtract(look.scale(along)).length() <= 0.8 + e.getBbWidth() / 2
                    && along < best) {
                caught = e;
                best = along;
            }
        }
        double shown = caught != null ? best : reach;
        if (caught == null && wall.getType() == HitResult.Type.MISS) {
            noTarget(player);
            return false;
        }
        for (double d = 1; d <= shown; d += 0.6) {
            Vec3 p = eye.add(look.scale(d));
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y - 0.2, p.z, 1, 0, 0, 0, 0);
        }
        if (caught != null) {
            caught.hurtServer(level, level.damageSources().playerAttack(player), 4.0F);
            Vec3 pull = player.position().subtract(caught.position());
            Vec3 v = pull.normalize().scale(Math.min(2.2, 0.35 + pull.length() * 0.16));
            caught.setDeltaMovement(v.x, 0.35 + Math.max(0, pull.y) * 0.08, v.z);
            caught.hurtMarked = true;
            level.playSound(null, player, SoundEvents.CHAIN_HIT, SoundSource.PLAYERS, 1.0F, 0.8F);
        } else {
            Vec3 pull = wall.getLocation().subtract(player.position());
            Vec3 v = pull.normalize().scale(Math.min(2.0, 0.4 + pull.length() * 0.15));
            player.setDeltaMovement(v.x, v.y + 0.35, v.z);
            player.hurtMarked = true;
            player.resetFallDistance();
            player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 30, 0, true, false, true));
            level.playSound(null, player, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.0F, 0.7F);
        }
        return true;
    }

    /** Five red-hot rivets in a fan, a puff of steam, a small recoil. */
    private static boolean rivets(ServerLevel level, Player player) {
        for (int i = -2; i <= 2; i++) {
            HotRivetEntity rivet = new HotRivetEntity(level, player, false, 4.0F);
            rivet.shootFromRotation(player, player.getXRot() + Math.abs(i) * 1.5F, player.getYRot() + i * 6.0F, 0.0F, 2.6F, 1.0F);
            level.addFreshEntity(rivet);
        }
        Vec3 look = player.getLookAngle();
        level.sendParticles(ParticleTypes.CLOUD, player.getX() + look.x, player.getEyeY() - 0.2 + look.y, player.getZ() + look.z,
                6, 0.1, 0.1, 0.1, 0.03);
        level.sendParticles(ParticleTypes.FLAME, player.getX() + look.x, player.getEyeY() - 0.2 + look.y, player.getZ() + look.z,
                4, 0.05, 0.05, 0.05, 0.02);
        Vec3 back = look.multiply(1, 0, 1).normalize().scale(-0.45);
        player.push(back.x, 0.05, back.z);
        player.hurtMarked = true;
        level.playSound(null, player, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.5F, 1.8F);
        level.playSound(null, player, SoundEvents.PISTON_EXTEND, SoundSource.PLAYERS, 0.6F, 1.6F);
        return true;
    }

    /** The bog lantern flares: foes around glow and choke, the wielder sees in the dark. */
    private static boolean lantern(ServerLevel level, Player player) {
        for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(6, 3, 6))) {
            if (e.distanceTo(player) <= 6.5) {
                e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0), player);
                e.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 0), player);
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 0), player);
            }
        }
        player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 600, 0, false, false, true));
        for (int i = 0; i < 24; i++) {
            double a = i * Math.PI / 12;
            level.sendParticles(ParticleTypes.SCULK_SOUL, player.getX() + Math.cos(a) * 3, player.getY() + 1.0,
                    player.getZ() + Math.sin(a) * 3, 1, 0.3, 0.3, 0.3, 0.02);
        }
        level.sendParticles(ParticleTypes.HAPPY_VILLAGER, player.getX(), player.getY() + 1.4, player.getZ(), 12, 1.5, 0.6, 1.5, 0);
        level.playSound(null, player, SoundEvents.SOUL_ESCAPE.value(), SoundSource.PLAYERS, 1.2F, 0.7F);
        return true;
    }

    /** A flash of sunlight from the blade: foes in a cone ahead are blinded and glow; undead among them burn. */
    private static boolean flash(ServerLevel level, Player player) {
        Vec3 look = player.getLookAngle();
        Vec3 eye = player.getEyePosition();
        for (LivingEntity e : foes(level, player, player.getBoundingBox().inflate(8, 3, 8))) {
            Vec3 to = e.getEyePosition().subtract(eye);
            if (to.length() > 8.5 || to.normalize().dot(look) < 0.6 || !player.hasLineOfSight(e)) {
                continue;
            }
            e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), player);
            e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 120, 0), player);
            if (e.is(EntityTypeTags.UNDEAD)) {
                e.hurtServer(level, level.damageSources().indirectMagic(player, player), 6.0F);
                e.igniteForSeconds(4.0F);
            }
        }
        for (int i = 1; i <= 8; i++) {
            Vec3 p = eye.add(look.scale(i));
            level.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 2, 0.15 * i, 0.1 * i, 0.15 * i, 0.01);
        }
        level.playSound(null, player, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.5F, 1.6F);
        level.playSound(null, player, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.4F, 2.0F);
        return true;
    }

    /** Boarding rush: a burst along the ground that hacks every foe on the way. */
    private static boolean rush(ServerLevel level, Player player) {
        Vec3 flat = player.getLookAngle().multiply(1, 0, 1).normalize();
        Vec3 origin = player.position();
        Vec3 v = flat.scale(1.9);
        player.setDeltaMovement(v.x, 0.2, v.z);
        player.hurtMarked = true;
        player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 60, 0, false, false, true));
        java.util.Set<LivingEntity> struck = new java.util.HashSet<>();
        for (int i = 1; i <= 6; i++) {
            Vec3 p = origin.add(flat.scale(i));
            level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1, p.z, 1, 0.2, 0.2, 0.2, 0);
            for (LivingEntity e : foes(level, player, new AABB(p, p).inflate(1.2, 1.6, 1.2))) {
                if (struck.add(e) && e.hurtServer(level, level.damageSources().playerAttack(player), 7.0F)) {
                    e.push(flat.x * 0.8, 0.3, flat.z * 0.8);
                    e.hurtMarked = true;
                }
            }
        }
        level.playSound(null, player, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.0F, 0.7F);
        level.playSound(null, player, SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.PLAYERS, 0.8F, 0.6F);
        return true;
    }

    @Override
    protected void activateClient(Player player, ItemStack stack) {
        if (kind == Kind.BOARDING_AXE && !player.getCooldowns().isOnCooldown(stack)) {
            // predict the rush locally so it feels instant (the server sends the same push)
            Vec3 v = player.getLookAngle().multiply(1, 0, 1).normalize().scale(1.9);
            player.setDeltaMovement(v.x, 0.2, v.z);
        }
    }

    /** A silent poisoned dart: a weak arrow carrying Poison II and Slowness, never picked up. */
    private static boolean dart(ServerLevel level, Player player) {
        Arrow dart = new Arrow(level, player, new ItemStack(Items.ARROW), null);
        dart.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
        dart.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 0));
        dart.setBaseDamage(1.0);
        dart.pickup = AbstractArrow.Pickup.CREATIVE_ONLY;
        dart.shootFromRotation(player, player.getXRot(), player.getYRot(), 0.0F, 2.8F, 0.4F);
        level.addFreshEntity(dart);
        level.playSound(null, player, SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS, 0.25F, 2.0F);
        return true;
    }
}

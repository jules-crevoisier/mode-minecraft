package com.brasshaven.colossal;

import com.brasshaven.Brasshaven;
import com.brasshaven.util.Targets;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.Result;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.living.MobEffectEvent;
import net.minecraftforge.event.entity.player.CriticalHitEvent;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Set bonuses of the six vault armour sets (2 and 4 pieces) and the passives of the vault weapons
 * (tools/wf/colossal_gear.py writes the same rules into the tooltips). Effects refresh once a second, staggered per
 * player; attribute bonuses are transient modifiers that come and go with the gear. The steam dash and the leaf climb
 * move the player, so they run on the client for the local player (whose movement the client owns); the server only
 * shows the steam and forgives the fall.
 */
public final class ColossalEvents {
    private static final Identifier ENGINEER_SPEED = Brasshaven.id("colossal/turbine_engineer_speed");
    private static final Identifier LOCK_MINING = Brasshaven.id("colossal/lockkeeper_mining");
    private static final Identifier BOG_EFFICIENCY = Brasshaven.id("colossal/bog_pilgrim_efficiency");
    private static final Identifier IRON_KNOCKBACK = Brasshaven.id("colossal/ironclad_knockback");
    private static final Identifier IRON_BLAST = Brasshaven.id("colossal/ironclad_blast");
    private static final Identifier STALKER_SAFE_FALL = Brasshaven.id("colossal/canopy_stalker_safe_fall");
    private static final Identifier STALKER_FALL = Brasshaven.id("colossal/canopy_stalker_fall");
    private static final int DASH_COOLDOWN = 80;

    /** Client side (the local player): ground state last tick and when the next steam dash is ready. */
    private static boolean clientGrounded = true;
    private static long clientDashReady;
    /** Server side: ground state per player last tick, and when the steam was last shown. */
    private static final Map<UUID, Boolean> GROUNDED = new HashMap<>();
    private static final Map<UUID, Long> STEAM_SHOWN = new HashMap<>();

    private ColossalEvents() {}

    public static void register() {
        TickEvent.PlayerTickEvent.Post.BUS.addListener(ColossalEvents::onTick);
        LivingHurtEvent.BUS.addListener((Consumer<LivingHurtEvent>) ColossalEvents::onHurt);
        MobEffectEvent.Applicable.BUS.addListener(ColossalEvents::onEffect);
        CriticalHitEvent.BUS.addListener(ColossalEvents::onCrit);
    }

    private static MobEffectInstance quiet(Holder<MobEffect> effect, int ticks) {
        return new MobEffectInstance(effect, ticks, 0, true, false, true);
    }

    private static boolean sunlit(Level level, LivingEntity e) {
        return level.isBrightOutside() && level.canSeeSky(BlockPos.containing(e.getEyePosition()));
    }

    // ------------------------------------------------------------------ every tick (movement) / every second (effects)
    private static void onTick(TickEvent.PlayerTickEvent.Post event) {
        Player player = event.player();
        if (player.isSpectator()) {
            return;
        }
        Level level = player.level();
        if (level.isClientSide()) {
            if (player.isLocalPlayer()) {
                clientMove(player, level);
            }
            return;
        }
        if (!(player instanceof ServerPlayer sp) || !(level instanceof ServerLevel server)) {
            return;
        }
        serverMove(sp, server);
        long t = server.getGameTime() + player.getId() * 7L;
        if (t % 20 != 0) {
            return;
        }
        int lock = ColossalSet.LOCKKEEPER.worn(player);
        if (lock >= 2 && player.isUnderWater()) {
            player.addEffect(quiet(MobEffects.WATER_BREATHING, 60));
        }
        if (lock >= 4 && player.isInWater()) {
            player.addEffect(quiet(MobEffects.DOLPHINS_GRACE, 60));
        }
        int bog = ColossalSet.BOG_PILGRIM.worn(player);
        if (bog >= 2 && player.hasEffect(MobEffects.POISON)) {
            player.removeEffect(MobEffects.POISON);
        }
        if (bog >= 4 && player.hasEffect(MobEffects.SLOWNESS)) {
            player.removeEffect(MobEffects.SLOWNESS);
        }
        if (ColossalSet.SUN_PRIEST.worn(player) >= 2) {
            player.addEffect(quiet(MobEffects.FIRE_RESISTANCE, 60));
        }
        int iron = ColossalSet.IRONCLAD.worn(player);
        int stalker = ColossalSet.CANOPY_STALKER.worn(player);
        modifier(player, Attributes.SUBMERGED_MINING_SPEED, LOCK_MINING, lock >= 4, 0.8, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.MOVEMENT_SPEED, ENGINEER_SPEED, ColossalSet.TURBINE_ENGINEER.worn(player) >= 2, 0.10,
                AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        modifier(player, Attributes.MOVEMENT_EFFICIENCY, BOG_EFFICIENCY, bog >= 4, 1.0, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.KNOCKBACK_RESISTANCE, IRON_KNOCKBACK, iron >= 2, 0.3, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.EXPLOSION_KNOCKBACK_RESISTANCE, IRON_BLAST, iron >= 4, 1.0, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.SAFE_FALL_DISTANCE, STALKER_SAFE_FALL, stalker >= 2, 4.0, AttributeModifier.Operation.ADD_VALUE);
        modifier(player, Attributes.FALL_DAMAGE_MULTIPLIER, STALKER_FALL, stalker >= 2, -0.33,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
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
        }
    }

    /** Is the player pressing against a leaf block (feet or head height)? */
    private static boolean againstLeaves(Player player, Level level) {
        if (!player.horizontalCollision) {
            return false;
        }
        AABB box = player.getBoundingBox().inflate(0.12, 0, 0.12);
        for (BlockPos pos : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY + 0.1, box.minZ),
                BlockPos.containing(box.maxX, box.minY + 1.4, box.maxZ))) {
            if (level.getBlockState(pos).is(BlockTags.LEAVES)) {
                return true;
            }
        }
        return false;
    }

    /** The local player: the Turbine Engineer's steam dash on a sprint-jump, the Canopy Stalker's leaf climb. */
    private static void clientMove(Player player, Level level) {
        boolean grounded = player.onGround();
        Vec3 v = player.getDeltaMovement();
        if (clientGrounded && !grounded && v.y > 0.2 && player.isSprinting() && level.getGameTime() >= clientDashReady
                && !player.isInWater() && ColossalSet.TURBINE_ENGINEER.worn(player) >= 4) {
            Vec3 flat = player.getLookAngle().multiply(1, 0, 1).normalize();
            player.setDeltaMovement(v.x + flat.x * 0.95, v.y + 0.08, v.z + flat.z * 0.95);
            clientDashReady = level.getGameTime() + DASH_COOLDOWN;
            for (int i = 0; i < 10; i++) {
                level.addParticle(ParticleTypes.CLOUD, player.getX() - flat.x * 0.5, player.getY() + 1.1, player.getZ() - flat.z * 0.5,
                        -flat.x * 0.15 + (player.getRandom().nextDouble() - 0.5) * 0.1, 0.03, -flat.z * 0.15);
            }
        }
        clientGrounded = grounded;
        if (againstLeaves(player, level) && ColossalSet.CANOPY_STALKER.worn(player) >= 4) {
            v = player.getDeltaMovement();
            double y = player.isShiftKeyDown() ? Math.max(v.y, 0.0) : 0.2;
            player.setDeltaMovement(v.x, y, v.z);
            player.resetFallDistance();
        }
    }

    /** The server side of the movement bonuses: steam for the onlookers, and no fall damage from a leaf climb. */
    private static void serverMove(ServerPlayer player, ServerLevel level) {
        if (ColossalSet.CANOPY_STALKER.worn(player) >= 4 && againstLeaves(player, level)) {
            player.resetFallDistance();
        }
        boolean grounded = player.onGround();
        Boolean was = GROUNDED.put(player.getUUID(), grounded);
        if (was == null || !was || grounded || !player.isSprinting() || player.isInWater()
                || ColossalSet.TURBINE_ENGINEER.worn(player) < 4) {
            return;
        }
        long now = level.getGameTime();
        if (now < STEAM_SHOWN.getOrDefault(player.getUUID(), 0L) + DASH_COOLDOWN) {
            return;
        }
        STEAM_SHOWN.put(player.getUUID(), now);
        level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1.0, player.getZ(), 12, 0.3, 0.3, 0.3, 0.04);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 0.6F, 1.4F);
    }

    // ------------------------------------------------------------------ effects, combat
    /** Bog Pilgrim: poison (2 pieces) and slowness (4 pieces) never take hold. */
    private static void onEffect(MobEffectEvent.Applicable e) {
        if (!(e.getEntity() instanceof Player p)) {
            return;
        }
        Holder<MobEffect> effect = e.getEffectInstance().getEffect();
        if (effect.is(MobEffects.POISON) && ColossalSet.BOG_PILGRIM.worn(p) >= 2
                || effect.is(MobEffects.SLOWNESS) && ColossalSet.BOG_PILGRIM.worn(p) >= 4) {
            e.setResult(Result.DENY);
        }
    }

    /** Sun-Priest (4 pieces): a critical hit in daylight under the sky calls down a sun-ray. */
    private static void onCrit(CriticalHitEvent e) {
        Player p = e.getEntity();
        boolean crit = e.getResult() == Result.ALLOW || e.getResult() == Result.DEFAULT && e.isVanillaCritical();
        if (!crit || !(p.level() instanceof ServerLevel level) || !(e.getTarget() instanceof LivingEntity target)
                || ColossalSet.SUN_PRIEST.worn(p) < 4 || !sunlit(level, p)) {
            return;
        }
        e.setDamageModifier(e.getDamageModifier() * 1.33F);
        target.igniteForSeconds(4.0F);
        for (int i = 0; i < 12; i++) {
            level.sendParticles(ParticleTypes.END_ROD, target.getX(), target.getY() + i * 0.5, target.getZ(), 2, 0.12, 0.1, 0.12, 0.0);
        }
        level.sendParticles(ParticleTypes.FLAME, target.getX(), target.getY() + 0.2, target.getZ(), 10, 0.4, 0.1, 0.4, 0.02);
        level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.BLAZE_SHOOT, SoundSource.PLAYERS, 0.6F, 1.5F);
    }

    private static void onHurt(LivingHurtEvent e) {
        DamageSource src = e.getSource();
        LivingEntity victim = e.getEntity();
        if (victim.level().isClientSide()) {
            return;
        }
        // Ironclad (4 pieces): explosions deal half damage
        if (victim instanceof Player p && src.is(DamageTypeTags.IS_EXPLOSION) && ColossalSet.IRONCLAD.worn(p) >= 4) {
            e.setAmount(e.getAmount() * 0.5F);
        }
        // the weapon passives: the wielder's own melee blows
        if (!(src.getEntity() instanceof Player p) || src.getDirectEntity() != p || !Targets.foe(p, victim)) {
            return;
        }
        Item held = p.getMainHandItem().getItem();
        if (!(held instanceof ColossalWeaponItem weapon)) {
            return;
        }
        switch (weapon.kind()) {
            case SLUICE_HOOK -> {
                if (victim.isInWater()) {
                    e.setAmount(e.getAmount() + 3.0F);
                }
            }
            case BOG_LANTERN -> victim.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), p);
            case SOLAR_KHOPESH -> {
                if (sunlit(victim.level(), p)) {
                    victim.igniteForSeconds(3.0F);
                    if (victim.is(EntityTypeTags.UNDEAD)) {
                        e.setAmount(e.getAmount() + 3.0F);
                    }
                }
            }
            default -> {
            }
        }
    }
}

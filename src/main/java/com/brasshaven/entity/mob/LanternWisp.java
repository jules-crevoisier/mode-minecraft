package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Feu follet (Lantern Wisp): a flame trapped in an old iron lantern, the light thief of the catacombs and the tombs.
 * <ul>
 *     <li><b>Snuff</b> (every 2 s while a player is within 16 blocks): it leans toward a lit candle or campfire within 8
 *     blocks and drinks its flame (the block goes out). Each stolen flame (up to 5) makes it shine brighter (its
 *     texture goes dim, lit, blazing) and adds 1 damage to its blows.</li>
 *     <li><b>Lunge</b> (within 2.5 blocks): a cold-flame dash (contact at 7 ticks).</li>
 *     <li><b>Pulse</b> (3 stolen flames or more, within 7 blocks, every 10 s): it gathers the light and lets out a wave of
 *     darkness at 10 ticks: Darkness 5 s and Blindness 1.5 s.</li>
 *     <li>It <b>shies away</b> from a player holding a torch or a lantern (it keeps 6 blocks away).</li>
 *     <li>When it dies, every flame it stole lights up again.</li>
 * </ul>
 */
public class LanternWisp extends ActionMonster {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.1F;
    private static final EntityDataAccessor<Integer> DATA_CHARGES = SynchedEntityData.defineId(LanternWisp.class, EntityDataSerializers.INT);
    private static final int LUNGE_HIT = 7;    // 0.35 s, matches lantern_wisp.py
    private static final int PULSE_AT = 10;    // 0.5 s
    private static final int MAX_CHARGES = 5;

    private final List<BlockPos> stolen = new ArrayList<>();
    private int snuffCooldown = 40;
    private int pulseCooldown = 100;
    private int lungeCooldown;
    private @Nullable BlockPos snuffing;

    public LanternWisp(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 7;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.ATTACK_DAMAGE, 3.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FLYING_SPEED, 0.12)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        FlyingPathNavigation nav = new FlyingPathNavigation(this, level);
        nav.setCanOpenDoors(false);
        nav.setCanFloat(true);
        return nav;
    }

    @Override
    public void travel(Vec3 input) {
        travelFlying(input, getSpeed());
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new WispGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CHARGES, 0);
    }

    public int charges() {
        return entityData.get(DATA_CHARGES);
    }

    @Override
    public int modelVariant() {
        int c = charges();
        return c == 0 ? 0 : c < 3 ? 1 : 2;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.LanternWisp.TICKS;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.store("Stolen", Codec.LONG.listOf(), stolen.stream().map(BlockPos::asLong).toList());
        output.putInt("Charges", charges());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        stolen.clear();
        input.read("Stolen", Codec.LONG.listOf()).ifPresent(l -> l.forEach(p -> stolen.add(BlockPos.of(p))));
        entityData.set(DATA_CHARGES, Math.min(MAX_CHARGES, input.getIntOr("Charges", 0)));
    }

    // ------------------------------------------------------------------ light thief

    private static boolean litFlame(BlockState s) {
        return (s.is(BlockTags.CANDLES) || s.is(BlockTags.CANDLE_CAKES) || s.is(BlockTags.CAMPFIRES))
                && s.hasProperty(BlockStateProperties.LIT) && s.getValue(BlockStateProperties.LIT);
    }

    private @Nullable BlockPos findFlame(ServerLevel level) {
        BlockPos me = blockPosition();
        BlockPos best = null;
        double bestD = Double.MAX_VALUE;
        for (BlockPos p : BlockPos.betweenClosed(me.offset(-8, -4, -8), me.offset(8, 4, 8))) {
            if (litFlame(level.getBlockState(p))) {
                double d = p.distSqr(me);
                if (d < bestD) {
                    bestD = d;
                    best = p.immutable();
                }
            }
        }
        return best;
    }

    private void drink(ServerLevel level, BlockPos at) {
        BlockState s = level.getBlockState(at);
        if (!litFlame(s)) {
            return;
        }
        level.setBlock(at, s.setValue(BlockStateProperties.LIT, false), 3);
        level.playSound(null, at, SoundEvents.CANDLE_EXTINGUISH, SoundSource.HOSTILE, 1.0F, 0.8F);
        Vec3 from = Vec3.atCenterOf(at);
        Vec3 to = position().add(0, 0.6, 0);
        for (int i = 0; i <= 8; i++) {
            Vec3 p = from.lerp(to, i / 8.0);
            level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
        }
        if (stolen.size() < 32) {
            stolen.add(at);
        }
        entityData.set(DATA_CHARGES, Math.min(MAX_CHARGES, charges() + 1));
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            for (BlockPos p : stolen) {
                BlockState s = level.getBlockState(p);
                if ((s.is(BlockTags.CANDLES) || s.is(BlockTags.CANDLE_CAKES) || s.is(BlockTags.CAMPFIRES))
                        && s.hasProperty(BlockStateProperties.LIT) && !s.getValue(BlockStateProperties.LIT)
                        && !(s.hasProperty(BlockStateProperties.WATERLOGGED) && s.getValue(BlockStateProperties.WATERLOGGED))) {
                    level.setBlock(p, s.setValue(BlockStateProperties.LIT, true), 3);
                    level.sendParticles(ParticleTypes.FLAME, p.getX() + 0.5, p.getY() + 0.7, p.getZ() + 0.5, 4, 0.1, 0.1, 0.1, 0.01);
                }
            }
            stolen.clear();
            level.sendParticles(ParticleTypes.SOUL, getX(), getY() + 0.6, getZ(), 12, 0.3, 0.3, 0.3, 0.05);
        }
    }

    private static boolean holdsLight(Player p) {
        for (ItemStack s : new ItemStack[] {p.getMainHandItem(), p.getOffhandItem()}) {
            if (s.is(Items.TORCH) || s.is(Items.SOUL_TORCH) || s.is(Items.LANTERN) || s.is(Items.SOUL_LANTERN)
                    || s.is(Items.REDSTONE_TORCH)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (snuffCooldown > 0) {
            snuffCooldown--;
        }
        if (pulseCooldown > 0) {
            pulseCooldown--;
        }
        if (lungeCooldown > 0) {
            lungeCooldown--;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(3) == 0) {
            level().addParticle(charges() >= 3 ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.SMOKE,
                    getRandomX(0.3), getY() + 0.1 + random.nextDouble() * 0.3, getRandomZ(0.3), 0, -0.02, 0);
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.SOUL_ESCAPE.value();
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.FIRE_EXTINGUISH;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SOUL_ESCAPE.value();
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.3F;
    }

    /** Drink the flames around, lunge, pulse darkness; shy away from a torch held in hand. */
    static final class WispGoal extends Goal {
        private final LanternWisp w;
        private int repath;

        WispGoal(LanternWisp w) {
            this.w = w;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (w.action >= 0) {
                return true;
            }
            LivingEntity t = w.getTarget();
            if (t != null && t.isAlive()) {
                return true;
            }
            // idle: drink the nearby flames when a player is around (no scans in an empty crypt)
            return w.snuffCooldown == 0 && w.charges() < MAX_CHARGES
                    && w.level().getNearestPlayer(w, 16.0) != null;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            w.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(w.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = w.getTarget();
            if (w.action >= 0) {
                int a = w.action;
                int k = w.step();
                if (a == MobAnims.LanternWisp.SNUFF) {
                    w.getNavigation().stop();
                    if (w.snuffing != null) {
                        w.getLookControl().setLookAt(Vec3.atCenterOf(w.snuffing));
                        if (k == 12) {
                            w.drink(level, w.snuffing);
                            w.snuffing = null;
                        }
                    }
                } else if (a == MobAnims.LanternWisp.LUNGE && t != null) {
                    if (k < LUNGE_HIT) {
                        w.setDeltaMovement(t.getEyePosition().subtract(w.position()).normalize().scale(0.45));
                    }
                    if (k == LUNGE_HIT && w.getBoundingBox().inflate(1.0).intersects(t.getBoundingBox())) {
                        // the stolen flames burn cold: +1 damage each
                        float dmg = (float) w.getAttributeValue(Attributes.ATTACK_DAMAGE) + w.charges();
                        if (t.hurtServer(level, w.damageSources().mobAttack(w), dmg)) {
                            w.setLastHurtMob(t);
                        }
                    }
                } else if (a == MobAnims.LanternWisp.PULSE && k == PULSE_AT) {
                    level.sendParticles(ParticleTypes.SQUID_INK, w.getX(), w.getY() + 0.6, w.getZ(), 40, 2.5, 1.0, 2.5, 0.02);
                    level.playSound(null, w, SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.HOSTILE, 0.8F, 1.8F);
                    for (Player p : level.getEntitiesOfClass(Player.class, w.getBoundingBox().inflate(7.0), Player::isAlive)) {
                        if (!p.isCreative() && !p.isSpectator()) {
                            p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0), w);
                            p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0), w);
                        }
                    }
                }
                return;
            }
            // drink a flame nearby
            if (w.snuffCooldown == 0 && w.charges() < MAX_CHARGES) {
                w.snuffCooldown = 40;
                BlockPos flame = w.findFlame(level);
                if (flame != null) {
                    w.snuffing = flame;
                    w.begin(MobAnims.LanternWisp.SNUFF);
                    return;
                }
                w.snuffCooldown = 100; // nothing left to drink here: look again later
            }
            if (t == null || !t.isAlive()) {
                return;
            }
            w.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(w.distanceToSqr(t));
            if (t instanceof Player p && holdsLight(p) && dist < 6.0) {
                if (--repath <= 0) {
                    repath = 10;
                    Vec3 away = DefaultRandomPos.getPosAway(w, 8, 4, t.position());
                    if (away != null) {
                        w.getNavigation().moveTo(away.x, away.y, away.z, 1.3);
                    }
                }
                return;
            }
            if (w.charges() >= 3 && dist <= 7.0 && w.pulseCooldown == 0) {
                w.pulseCooldown = 200;
                w.begin(MobAnims.LanternWisp.PULSE);
                return;
            }
            if (dist <= 2.5 && w.lungeCooldown == 0) {
                w.lungeCooldown = 25;
                w.begin(MobAnims.LanternWisp.LUNGE);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                w.getNavigation().moveTo(t.getX(), t.getEyeY() - 0.4, t.getZ(), 1.1);
            }
        }
    }
}

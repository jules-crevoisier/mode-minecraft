package com.wayfarers.entity.ocean;

import com.wayfarers.entity.AnimatedMob;
import com.wayfarers.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.fish.WaterAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.boat.AbstractBoat;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

/**
 * Méduse lumineuse (Glow Jellyfish): a see-through bell that drifts in every non-frozen sea, glowing softly at
 * night. It moves in pulses (a push every two seconds or so, then a slow sink), never leaves the water by itself,
 * and stings whoever bumps into it: 1 damage and a short poison. Four colours (rose, azure, amber, violet), picked
 * by the sea it is born in. Drops Glow Jelly.
 */
public class GlowJellyfish extends WaterAnimal implements AnimatedMob {
    public static final float WIDTH = 0.75F;
    public static final float HEIGHT = 1.0F;
    public static final int VARIANTS = 4;
    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(GlowJellyfish.class,
            EntityDataSerializers.INT);

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int pulseTimer;
    private int stingCooldown;
    private Vec3 drift = Vec3.ZERO;

    public GlowJellyfish(EntityType<? extends WaterAnimal> type, Level level) {
        super(type, level);
        this.pulseTimer = random.nextInt(48);
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 6.0).add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    /** In water, anywhere from the surface down to 40 blocks below sea level. */
    public static boolean checkSpawnRules(EntityType<? extends GlowJellyfish> type, LevelAccessor level,
                                          EntitySpawnReason reason, BlockPos pos, RandomSource random) {
        int sea = level.getSeaLevel();
        return pos.getY() <= sea - 1 && pos.getY() >= sea - 40 && level.getFluidState(pos).is(FluidTags.WATER)
                && level.getFluidState(pos.below()).is(FluidTags.WATER) && level.getBlockState(pos.above()).is(Blocks.WATER);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_VARIANT, 0);
    }

    public int getVariant() {
        return entityData.get(DATA_VARIANT);
    }

    public void setVariant(int variant) {
        entityData.set(DATA_VARIANT, Math.floorMod(variant, VARIANTS));
    }

    @Override
    public int modelVariant() {
        return getVariant();
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putInt("Variant", getVariant());
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        setVariant(input.getIntOr("Variant", 0));
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                  EntitySpawnReason reason, @Nullable SpawnGroupData groupData) {
        // warm seas: rose and amber, cold seas: azure and violet, elsewhere any colour
        float temperature = level.getBiome(blockPosition()).value().getBaseTemperature();
        boolean warm = temperature >= 0.75F;
        boolean cold = temperature <= 0.3F;
        int v = random.nextInt(VARIANTS);
        if (warm && random.nextInt(3) > 0) {
            v = random.nextBoolean() ? 0 : 2;
        } else if (cold && random.nextInt(3) > 0) {
            v = random.nextBoolean() ? 1 : 3;
        }
        setVariant(v);
        return super.finalizeSpawn(level, difficulty, reason, groupData);
    }

    // ------------------------------------------------------------------ movement: pulses and a slow sink

    @Override
    public void travel(Vec3 input) {
        if (isInWater()) {
            move(MoverType.SELF, getDeltaMovement());
        } else {
            super.travel(input);
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (level().isClientSide()) {
            return;
        }
        if (stingCooldown > 0) {
            stingCooldown--;
        }
        if (!isInWater()) {
            return;
        }
        if (--pulseTimer <= 0) {
            pulseTimer = 40 + random.nextInt(24);
            float angle = random.nextFloat() * Mth.TWO_PI;
            double up = 0.06 + random.nextDouble() * 0.05;
            // stay under the surface: no push up when the water above is shallow
            if (!level().getFluidState(blockPosition().above(2)).is(FluidTags.WATER)) {
                up = -0.03;
            }
            drift = new Vec3(Mth.cos(angle) * 0.035, up, Mth.sin(angle) * 0.035);
            setDeltaMovement(getDeltaMovement().add(drift));
        } else {
            setDeltaMovement(getDeltaMovement().scale(0.93).add(0, -0.0025, 0));
        }
        Vec3 v = getDeltaMovement();
        if (v.horizontalDistanceSqr() > 1.0E-5) {
            yBodyRot += (-(float) Mth.atan2(v.x, v.z) * Mth.RAD_TO_DEG - yBodyRot) * 0.05F;
            setYRot(yBodyRot);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
            if (isInWater() && random.nextInt(14) == 0) {
                level().addParticle(ParticleTypes.GLOW, getRandomX(0.5), getY() + 0.3 + random.nextDouble() * 0.6,
                        getRandomZ(0.5), 0, 0.01, 0);
            }
        }
    }

    // ------------------------------------------------------------------ the sting

    @Override
    public void playerTouch(Player player) {
        // a player in a boat touches whatever drifts under the hull (the touch box spans the boat): the hull shields them
        if (!(level() instanceof ServerLevel level) || stingCooldown > 0 || player.isCreative() || player.isSpectator()
                || !player.isAlive() || player.getVehicle() instanceof AbstractBoat) {
            return;
        }
        // playerTouch fires for anything within a block of the player: only a real brush with the bell stings
        if (!player.getBoundingBox().intersects(getBoundingBox().inflate(0.15))) {
            return;
        }
        stingCooldown = 30;
        if (player.hurtServer(level, damageSources().mobAttack(this), 1.0F)) {
            player.addEffect(new MobEffectInstance(MobEffects.POISON, 50, 0), this);
            level.sendParticles(ParticleTypes.GLOW, player.getX(), player.getY(0.5), player.getZ(), 6, 0.3, 0.3, 0.3, 0.02);
            level.playSound(null, this, SoundEvents.SLIME_ATTACK, SoundSource.NEUTRAL, 0.6F, 1.6F);
        }
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && source.getEntity() != null) {
            Vec3 away = position().subtract(source.getEntity().position()).normalize().scale(0.15);
            setDeltaMovement(getDeltaMovement().add(away.x, Math.abs(away.y) + 0.05, away.z));
        }
        return hurt;
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return null;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SLIME_HURT_SMALL;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SLIME_DEATH_SMALL;
    }

    @Override
    protected float getSoundVolume() {
        return 0.5F;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.GlowJellyfish.TICKS;
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }
}

package com.brasshaven.entity.ocean;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModOcean;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.animal.fish.AbstractFish;
import net.minecraft.world.entity.animal.fish.AbstractSchoolingFish;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jetbrains.annotations.Nullable;

/**
 * Poisson de récif (Reef Fish): small fish of warm seas that swim in schools of up to ten (vanilla
 * {@link AbstractSchoolingFish}: a leader wanders, the others follow it). Three liveries, one per school: sunburst,
 * clown and azure. They can be caught in a bucket (the livery is kept) and flop on land like any fish.
 */
public class ReefFish extends AbstractSchoolingFish implements AnimatedMob {
    public static final float WIDTH = 0.5F;
    public static final float HEIGHT = 0.45F;
    public static final int VARIANTS = 3;
    private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(ReefFish.class,
            EntityDataSerializers.INT);

    private final AnimationState[] actionStates = AnimatedMob.createStates();

    public ReefFish(EntityType<? extends ReefFish> type, Level level) {
        super(type, level);
    }

    public static AttributeSupplier.Builder attributes() {
        return AbstractFish.createAttributes();
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
    public int getMaxSchoolSize() {
        return 10;
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
        // a whole school shares the livery of its leader
        if (groupData instanceof SchoolSpawnGroupData school && school.leader instanceof ReefFish leader) {
            setVariant(leader.getVariant());
        } else {
            setVariant(random.nextInt(VARIANTS));
        }
        return super.finalizeSpawn(level, difficulty, reason, groupData);
    }

    // ------------------------------------------------------------------ bucket

    @Override
    public ItemStack getBucketItemStack() {
        return new ItemStack(ModOcean.REEF_FISH_BUCKET.get());
    }

    @Override
    public void saveToBucketTag(ItemStack bucket) {
        super.saveToBucketTag(bucket);
        int variant = getVariant();
        CustomData.update(DataComponents.BUCKET_ENTITY_DATA, bucket, tag -> tag.putInt("Variant", variant));
    }

    @Override
    public void loadFromBucketTag(CompoundTag tag) {
        super.loadFromBucketTag(tag);
        tag.getInt("Variant").ifPresent(this::setVariant);
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.TROPICAL_FISH_AMBIENT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.TROPICAL_FISH_DEATH;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.TROPICAL_FISH_HURT;
    }

    @Override
    protected SoundEvent getFlopSound() {
        return SoundEvents.TROPICAL_FISH_FLOP;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.ReefFish.TICKS;
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
        }
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }
}

package com.wayfarers.entity;

import com.wayfarers.generated.GeneratedNpcs;
import com.wayfarers.generated.MobAnims;
import com.wayfarers.util.NpcQuests;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A quest giver of the Wayfarers (Guild Agent, Scholar, Tinkerer, Druid, Dwarf Elder: {@link GeneratedNpcs#ROLES}).
 * <ul>
 *     <li>Right-click: the contracts screen ({@link NpcQuests#open}), with a wave.</li>
 *     <li>Stays at its post: it never wanders, walks back home when pushed away, cannot be pushed by players,
 *     never despawns and cannot be hurt (only {@code /kill} and the void reach it). Monsters ignore it.</li>
 *     <li>Its name tag shows a given name and its title ("Mira, Guild Agent"), chosen when it first spawns.</li>
 *     <li>Placed by structure templates ({@code {id: "wayfarers:wayfarer_npc", Role: "druid"}}), moved or removed
 *     by operators with {@code /wayfarers npc}.</li>
 * </ul>
 */
public class WayfarerNpc extends PathfinderMob implements AnimatedMob {
    public static final float WIDTH = 0.6F;
    public static final float HEIGHT = 1.95F;
    private static final EntityDataAccessor<Integer> DATA_ROLE = SynchedEntityData.defineId(WayfarerNpc.class, EntityDataSerializers.INT);
    /** How far it may be pushed from its post before walking back. */
    private static final int HOME_RADIUS = 2;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private int nameIndex = -1;
    private int talkCooldown;
    /** First server tick on the ground seen (not saved: a loaded NPC is checked again, which is harmless). */
    private boolean landed;

    public WayfarerNpc(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 20.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 16.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new MoveTowardsRestrictionGoal(this, 0.6));
        goalSelector.addGoal(2, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(3, new RandomLookAroundGoal(this));
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ROLE, 0);
    }

    // ------------------------------------------------------------------ role, name, home

    public String role() {
        List<String> roles = GeneratedNpcs.ROLES;
        return roles.get(Math.floorMod(entityData.get(DATA_ROLE), roles.size()));
    }

    public void setRole(String role) {
        int i = GeneratedNpcs.ROLES.indexOf(role);
        entityData.set(DATA_ROLE, Math.max(0, i));
        if (!level().isClientSide()) {
            refreshName();
        }
    }

    /** "Mira, Guild Agent": the given name is picked once, the title follows the role (translated on the client). */
    private void refreshName() {
        int r = Math.floorMod(entityData.get(DATA_ROLE), GeneratedNpcs.ROLES.size());
        List<String> names = GeneratedNpcs.NAMES.get(r);
        if (nameIndex < 0) {
            nameIndex = Math.floorMod(getUUID().hashCode(), names.size());
        }
        setCustomName(Component.translatable("npc.wayfarers.display", names.get(nameIndex % names.size()),
                Component.translatable("npc.wayfarers.role." + role())));
        setCustomNameVisible(true);
    }

    /** Its post: where it was placed (it walks back there when pushed away). */
    public void setPost(BlockPos pos) {
        setHomeTo(pos, HOME_RADIUS);
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                  EntitySpawnReason reason, @Nullable SpawnGroupData groupData) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, groupData);
        setPost(blockPosition());
        refreshName();
        return data;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putString("Role", role());
        output.putInt("NameIndex", nameIndex);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        nameIndex = input.getIntOr("NameIndex", -1);
        String role = input.getStringOr("Role", GeneratedNpcs.ROLES.get(0));
        int i = GeneratedNpcs.ROLES.indexOf(role);
        entityData.set(DATA_ROLE, Math.max(0, i));
    }

    @Override
    public int modelVariant() {
        return Math.floorMod(entityData.get(DATA_ROLE), GeneratedNpcs.ROLES.size());
    }

    // ------------------------------------------------------------------ talking

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (!isAlive()) {
            return InteractionResult.PASS;
        }
        if (player instanceof ServerPlayer sp) {
            getLookControl().setLookAt(player);
            if (talkCooldown <= 0) {
                AnimatedMob.playAction(this, MobAnims.WayfarerNpc.GREET);
                playSound(SoundEvents.VILLAGER_AMBIENT, 1.0F, getVoicePitch());
                talkCooldown = 60;
            }
            NpcQuests.open(sp, this);
        }
        return InteractionResult.SUCCESS;
    }

    /** A nod when a contract is accepted or handed in. */
    public void nod() {
        AnimatedMob.playAction(this, MobAnims.WayfarerNpc.NOD);
        playSound(SoundEvents.VILLAGER_YES, 1.0F, getVoicePitch());
    }

    // ------------------------------------------------------------------ a fixture of its post

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (!source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false; // players, monsters, fire, falls: nothing harms a quest giver (/kill and the void do)
        }
        return super.hurtServer(level, source, damage);
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(Entity entity) {
        // it does not shove its visitors around either
    }

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    public boolean requiresCustomPersistence() {
        return true;
    }

    @Override
    protected int decreaseAirSupply(int currentSupply) {
        return currentSupply;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.VILLAGER_AMBIENT;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 400;
    }

    @Override
    protected @Nullable SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VILLAGER_HURT;
    }

    @Override
    protected @Nullable SoundEvent getDeathSound() {
        return SoundEvents.VILLAGER_DEATH;
    }

    // ------------------------------------------------------------------ animation

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.WayfarerNpc.TICKS;
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
            return;
        }
        if (talkCooldown > 0) {
            talkCooldown--;
        }
        if (!hasHome()) {
            setPost(blockPosition()); // summoned without finalizeSpawn (a command with NBT, an old save)
        }
        if (!landed && onGround()) {
            landed = true;
            if (!getHomePosition().closerThan(blockPosition(), 4.0)) {
                setPost(blockPosition()); // summoned in the air: its post is where it lands
            }
        }
        if (getCustomName() == null) {
            refreshName();
        }
    }
}

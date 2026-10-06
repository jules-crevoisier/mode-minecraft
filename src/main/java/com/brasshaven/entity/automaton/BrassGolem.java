package com.brasshaven.entity.automaton;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.GeneratedMetals;
import com.brasshaven.generated.MobAnims;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.animal.golem.AbstractGolem;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;
import java.util.List;
import java.util.UUID;

/**
 * Golem de laiton (Brass Golem): a friendly automaton. Built by right-clicking the top of two stacked Blocks of
 * Brass with a Clockwork Heart ({@link com.brasshaven.item.ClockworkHeartItem}).
 * <ul>
 *     <li>Follows the player who built it (teleports back to them past 28 blocks), or guards a spot: sneak-use it
 *     with an empty hand to switch between <i>follow</i> and <i>guard here</i>.</li>
 *     <li>Fights every monster (never creepers, never players, villagers or pets) within 16 blocks, defends its
 *     owner and nearby villagers: <b>piston punch</b> (12 damage, throws the foe back and up) and, when three
 *     monsters crowd it, a two-fisted <b>ground slam</b> (9 damage around it).</li>
 *     <li>Repaired with brass: an ingot heals 20, a nugget 3 (it whistles and cheers). 80 health, 10 armour.</li>
 *     <li>Drops its Clockwork Heart and some brass when destroyed, so it can be rebuilt.</li>
 * </ul>
 */
public class BrassGolem extends AbstractGolem implements AnimatedMob {
    public static final float WIDTH = 1.3F;
    public static final float HEIGHT = 2.3F;
    private static final int PUNCH_IMPACT = 8;    // 0.4 s, matches brass_golem.py
    private static final int SLAM_IMPACT = 12;    // 0.6 s
    /** Never strays further than this from its owner (or guarded spot) to chase a foe. */
    private static final double LEASH = 24.0;

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private @Nullable UUID owner;
    private boolean guarding;
    private @Nullable BlockPos guardPos;
    private int punchCooldown;
    private int slamCooldown = 60;
    private int whistle;

    public BrassGolem(EntityType<? extends AbstractGolem> type, Level level) {
        super(type, level);
        setPersistenceRequired();
    }

    public static AttributeSupplier.Builder attributes() {
        return Mob.createMobAttributes()
                .add(Attributes.MAX_HEALTH, 80.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.MOVEMENT_SPEED, 0.27)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
                .add(Attributes.ATTACK_DAMAGE, 12.0)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new GolemFightGoal(this));
        goalSelector.addGoal(3, new KeepCloseGoal(this));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.5));
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new DefendOwnerGoal(this));
        targetSelector.addGoal(2, new HurtByTargetGoal(this));
        targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Mob.class, 5, false, false,
                (target, level) -> target instanceof Enemy && !(target instanceof Creeper) && nearAnchor(target, LEASH - 8.0)));
    }

    // ------------------------------------------------------------------ owner, modes, saving

    /** Called when a player builds it: remembers the builder and cheers. */
    public void setBuilder(Player player) {
        owner = player.getUUID();
        AnimatedMob.playAction(this, MobAnims.BrassGolem.CHEER);
        whistle = 30;
    }

    public @Nullable UUID getOwnerUUID() {
        return owner;
    }

    /** The player who built it, when online in this dimension. */
    public @Nullable Player getOwner() {
        return owner == null ? null : level().getPlayerByUUID(owner);
    }

    /** Where it belongs: the guarded spot, or its owner (alive, in this dimension); null when neither. */
    private @Nullable Vec3 anchor() {
        if (guarding) {
            if (guardPos == null && !level().isClientSide()) {
                guardPos = blockPosition(); // placed by a structure template: guard the spot it stands on
            }
            return guardPos == null ? null : Vec3.atBottomCenterOf(guardPos);
        }
        Player o = getOwner();
        return o != null && o.isAlive() && !o.isSpectator() ? o.position() : null;
    }

    private boolean nearAnchor(LivingEntity e, double radius) {
        Vec3 a = anchor();
        return a == null || e.position().distanceToSqr(a) <= radius * radius;
    }

    /** Gives up the current foe (also ends the target goals, which would otherwise pick it up again). */
    private void dropTarget() {
        for (WrappedGoal goal : targetSelector.getAvailableGoals()) {
            if (goal.isRunning()) {
                goal.stop();
            }
        }
        setTarget(null);
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        if (owner != null) {
            output.putString("Owner", owner.toString());
        }
        output.putBoolean("Guarding", guarding);
        if (guardPos != null) {
            output.putLong("GuardPos", guardPos.asLong());
        }
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        String o = input.getStringOr("Owner", "");
        try {
            owner = o.isEmpty() ? null : UUID.fromString(o);
        } catch (IllegalArgumentException e) {
            owner = null;
        }
        guarding = input.getBooleanOr("Guarding", false);
        long g = input.getLongOr("GuardPos", Long.MIN_VALUE);
        guardPos = g == Long.MIN_VALUE ? null : BlockPos.of(g);
    }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        boolean ingot = stack.is(GeneratedMetals.BRASS_INGOT.get());
        if (ingot || stack.is(GeneratedMetals.BRASS_NUGGET.get())) {
            if (getHealth() >= getMaxHealth()) {
                return InteractionResult.PASS;
            }
            if (!level().isClientSide()) {
                heal(ingot ? 20.0F : 3.0F);
                stack.consume(1, player);
                playSound(SoundEvents.IRON_GOLEM_REPAIR, 1.0F, 1.2F + random.nextFloat() * 0.2F);
                if (ingot) {
                    AnimatedMob.playAction(this, MobAnims.BrassGolem.CHEER);
                    whistle = 20;
                }
                if (level() instanceof ServerLevel level) {
                    level.sendParticles(ParticleTypes.HEART, getX(), getY() + 2.4, getZ(), 2, 0.3, 0.1, 0.3, 0);
                }
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.isEmpty() && player.isSecondaryUseActive()) {
            if (owner != null && !owner.equals(player.getUUID())) {
                return InteractionResult.PASS; // only its builder gives it orders
            }
            if (!level().isClientSide()) {
                if (owner == null) {
                    owner = player.getUUID();
                }
                guarding = !guarding;
                guardPos = guarding ? blockPosition() : null;
                getNavigation().stop();
                player.sendOverlayMessage(Component.translatable(guarding ? "message.brasshaven.brass_golem.guard"
                        : "message.brasshaven.brass_golem.follow").withStyle(ChatFormatting.GOLD));
                playSound(SoundEvents.NOTE_BLOCK_CHIME.value(), 0.8F, guarding ? 0.8F : 1.4F);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    /** Never fights players, villagers, other golems or anyone's pets. */
    @Override
    public boolean canAttack(LivingEntity target) {
        if (target instanceof Player || target instanceof AbstractGolem || target instanceof AbstractVillager
                || target instanceof Creeper || target instanceof OwnableEntity o && o.getOwnerReference() != null) {
            return false;
        }
        return super.canAttack(target);
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.IRON_GOLEM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.IRON_GOLEM_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.IRON_GOLEM_STEP, 0.8F, 1.3F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 1.2F;
    }

    @Override
    protected int decreaseAirSupply(int currentSupply) {
        return currentSupply; // no lungs, only a boiler
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1.2, getZ(), 20, 0.4, 0.6, 0.4, 0.03);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 1.2, getZ(), 30, 0.5, 0.6, 0.5, 0.2);
            level.playSound(null, this, SoundEvents.FIRE_EXTINGUISH, SoundSource.NEUTRAL, 1.0F, 0.6F);
        }
    }

    // ------------------------------------------------------------------ animation plumbing and ambience

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.BrassGolem.TICKS;
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
            if (random.nextInt(12) == 0) { // the two shoulder smokestacks
                float yaw = yBodyRot * Mth.DEG_TO_RAD;
                double side = random.nextBoolean() ? 0.25 : -0.25;
                double bx = Mth.cos(yaw) * side + Mth.sin(yaw) * 0.12;
                double bz = Mth.sin(yaw) * side - Mth.cos(yaw) * 0.12;
                level().addParticle(ParticleTypes.SMOKE, getX() + bx, getY() + 2.45, getZ() + bz, 0, 0.03, 0);
            }
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (punchCooldown > 0) {
            punchCooldown--;
        }
        if (slamCooldown > 0) {
            slamCooldown--;
        }
        if (whistle > 0 && --whistle == 0) {
            level.playSound(null, this, SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.NEUTRAL, 0.9F, 1.6F);
            level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.6, getZ(), 6, 0.1, 0.2, 0.1, 0.03);
        }
        // never chase a foe far from its owner or post: it would be left behind (or lured away) for good
        LivingEntity target = getTarget();
        if (target != null && tickCount % 10 == 0 && (!nearAnchor(this, LEASH) || !nearAnchor(target, LEASH))) {
            dropTarget();
        }
        if (tickCount % 20 == 0 && getHealth() < getMaxHealth() * 0.3F) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1.6, getZ(), 2, 0.3, 0.3, 0.3, 0.01);
        }
    }

    // ------------------------------------------------------------------ attacks

    private Vec3 facing() {
        float r = getYRot() * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    private List<Mob> crowd(ServerLevel level, double radius) {
        return level.getEntitiesOfClass(Mob.class, crowdBox(radius), BrassGolem::crowding);
    }

    private AABB crowdBox(double radius) {
        return new AABB(position(), position()).inflate(radius, 2, radius);
    }

    private static boolean crowding(Mob e) {
        return e.isAlive() && e instanceof Enemy && !(e instanceof Creeper);
    }

    /**
     * Whether at least {@code count} foes stand within {@code radius}: the same answer as {@code crowd(...).size() >=
     * count}, but the search stops at the {@code count}-th foe (the fight goal asks every tick).
     */
    private boolean crowded(ServerLevel level, double radius, int count) {
        List<Mob> found = new java.util.ArrayList<>(count);
        level.getEntities(net.minecraft.world.level.entity.EntityTypeTest.forClass(Mob.class), crowdBox(radius),
                BrassGolem::crowding, found, count);
        return found.size() >= count;
    }

    private void punch(ServerLevel level, LivingEntity target) {
        float damage = (float) getAttributeValue(Attributes.ATTACK_DAMAGE);
        if (target.hurtServer(level, damageSources().mobAttack(this), damage)) {
            double resist = target.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE);
            double k = Math.max(0.0, 1.0 - resist);
            Vec3 push = target.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.3 * k);
            target.push(push.x, 0.45 * k, push.z);
            target.hurtMarked = true;
        }
        Vec3 p = position().add(facing().scale(1.4)).add(0, 1.2, 0);
        level.sendParticles(ParticleTypes.CLOUD, p.x, p.y, p.z, 6, 0.2, 0.2, 0.2, 0.05);
        level.playSound(null, this, SoundEvents.PISTON_EXTEND, SoundSource.NEUTRAL, 1.0F, 0.8F);
        level.playSound(null, this, SoundEvents.IRON_GOLEM_ATTACK, SoundSource.NEUTRAL, 1.0F, 1.1F);
    }

    private void slam(ServerLevel level) {
        Vec3 c = position().add(facing().scale(1.0));
        for (Mob e : crowd(level, 3.6)) {
            if (e.position().distanceTo(c) <= 3.8 && e.hurtServer(level, damageSources().mobAttack(this), 9.0F)) {
                Vec3 push = e.position().subtract(position()).multiply(1, 0, 1).normalize().scale(0.9);
                e.push(push.x, 0.5, push.z);
                e.hurtMarked = true;
            }
        }
        for (int i = 0; i < 16; i++) {
            double a = Math.PI * 2 * i / 16;
            level.sendParticles(ParticleTypes.CLOUD, c.x + Math.cos(a) * 2.5, c.y + 0.2, c.z + Math.sin(a) * 2.5, 1, 0, 0.05, 0, 0.02);
        }
        level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.ANVIL_LAND, SoundSource.NEUTRAL, 0.8F, 0.8F);
        level.playSound(null, this, SoundEvents.PISTON_EXTEND, SoundSource.NEUTRAL, 1.0F, 0.6F);
    }

    /** Close in on the target, piston punch, or slam the ground when crowded. */
    static final class GolemFightGoal extends Goal {
        private final BrassGolem g;
        private int action = -1;
        private int tick;

        GolemFightGoal(BrassGolem g) {
            this.g = g;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = g.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            action = -1;
            g.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            g.getNavigation().stop();
            AnimatedMob.playAction(g, which);
        }

        @Override
        public void tick() {
            if (!(g.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = g.getTarget();
            if (action >= 0) {
                int k = tick++;
                g.getNavigation().stop();
                if (t != null) {
                    g.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (action == MobAnims.BrassGolem.PUNCH && k == PUNCH_IMPACT && t != null && t.isAlive()
                        && g.distanceToSqr(t) <= 3.4 * 3.4) {
                    g.punch(level, t);
                } else if (action == MobAnims.BrassGolem.SLAM && k == SLAM_IMPACT) {
                    g.slam(level);
                } else if (k == 2 && action == MobAnims.BrassGolem.PUNCH) {
                    level.playSound(null, g, SoundEvents.PISTON_CONTRACT, SoundSource.NEUTRAL, 0.8F, 0.9F);
                }
                if (k >= MobAnims.BrassGolem.TICKS[action]) {
                    action = -1;
                }
                return;
            }
            if (t == null) {
                return;
            }
            g.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double reach = 2.4 + t.getBbWidth() / 2;
            double dist = Math.sqrt(g.distanceToSqr(t));
            if (g.slamCooldown == 0 && g.crowded(level, 3.0, 3)) {
                g.slamCooldown = 160;
                begin(MobAnims.BrassGolem.SLAM);
                return;
            }
            if (dist <= reach && g.punchCooldown == 0) {
                g.punchCooldown = 22;
                float yaw = (float) (Mth.atan2(t.getZ() - g.getZ(), t.getX() - g.getX()) * Mth.RAD_TO_DEG) - 90.0F;
                g.setYRot(yaw);
                g.yBodyRot = yaw;
                begin(MobAnims.BrassGolem.PUNCH);
                return;
            }
            if (dist > reach - 0.6 && g.tickCount % 5 == 0) {
                g.getNavigation().moveTo(t, 1.1);
            }
        }
    }

    /** Follow the owner (teleporting back when far behind), or walk back to the guarded spot. */
    static final class KeepCloseGoal extends Goal {
        private final BrassGolem g;

        KeepCloseGoal(BrassGolem g) {
            this.g = g;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            Vec3 a = g.anchor();
            return a != null && g.getTarget() == null && g.position().distanceTo(a) > (g.guarding ? 6.0 : 9.0);
        }

        @Override
        public boolean canContinueToUse() {
            Vec3 a = g.anchor();
            return a != null && g.getTarget() == null && g.position().distanceTo(a) > 3.5;
        }

        @Override
        public void stop() {
            g.getNavigation().stop();
        }

        @Override
        public void tick() {
            Vec3 a = g.anchor();
            if (a == null) {
                return;
            }
            double d = g.position().distanceTo(a);
            if (!g.guarding && d > 28.0 && g.tickCount % 10 == 0) {
                for (int i = 0; i < 10; i++) {
                    double ang = g.random.nextDouble() * Math.PI * 2;
                    double r = 2.0 + g.random.nextDouble() * 2.0;
                    if (g.randomTeleport(a.x + Math.cos(ang) * r, a.y, a.z + Math.sin(ang) * r, true)) {
                        g.getNavigation().stop();
                        g.playSound(SoundEvents.FIRE_EXTINGUISH, 0.8F, 1.2F);
                        return;
                    }
                }
                // no room near the owner (a narrow tunnel, open water): keep walking after them
            }
            if (g.tickCount % 10 == 0) {
                g.getNavigation().moveTo(a.x, a.y, a.z, d > 14.0 ? 1.2 : 0.9);
            }
        }
    }

    /**
     * Strike whoever hurts the owner, or whoever the owner strikes (never a player or a pet). A target goal, so the
     * usual checks drop the foe once it is out of range or can no longer be attacked.
     */
    static final class DefendOwnerGoal extends TargetGoal {
        private final BrassGolem g;
        private @Nullable LivingEntity pending;
        private int lastHurtBy;
        private int lastHurt;

        DefendOwnerGoal(BrassGolem g) {
            super(g, false);
            this.g = g;
            setFlags(EnumSet.of(Flag.TARGET));
        }

        private @Nullable LivingEntity candidate() {
            Player o = g.getOwner();
            if (o == null || g.distanceToSqr(o) > LEASH * LEASH) {
                return null;
            }
            LivingEntity by = o.getLastHurtByMob();
            if (by != null && o.getLastHurtByMobTimestamp() != lastHurtBy && g.canAttack(by)) {
                lastHurtBy = o.getLastHurtByMobTimestamp();
                return by;
            }
            LivingEntity hit = o.getLastHurtMob();
            if (hit != null && o.getLastHurtMobTimestamp() != lastHurt && g.canAttack(hit)) {
                lastHurt = o.getLastHurtMobTimestamp();
                return hit;
            }
            return null;
        }

        @Override
        public boolean canUse() {
            LivingEntity c = candidate();
            pending = c != null && c.isAlive() ? c : null;
            return pending != null;
        }

        @Override
        public void start() {
            g.setTarget(pending);
            targetMob = pending;
            pending = null;
            super.start();
        }
    }
}

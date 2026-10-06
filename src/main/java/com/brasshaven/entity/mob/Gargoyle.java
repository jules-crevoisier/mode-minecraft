package com.brasshaven.entity.mob;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Gargoyle (Gargouille): a stone grotesque that is a statue as long as someone watches it.
 * <ul>
 *     <li><b>Statue:</b> while any survival player within 40 blocks has it in view (a 45 degree cone around the
 *     look direction, line of sight, the same {@code isLookingAtMe} test the enderman uses for stares) it freezes
 *     completely, cancels any wind-up, and its stone skin halves incoming damage. Blindness or Darkness on a
 *     player means that player sees nothing.</li>
 *     <li><b>Unseen</b> it lopes fast (speed 0.38) and attacks: <b>swipe</b> combo (two claws at 12 and 20 ticks,
 *     7 + 8 damage in a 2.8-block, 75 degree arc, the second knocks back), <b>dive</b> (4 to 13 blocks away or 2.5+
 *     blocks above the target: 10-tick crouch with a dust ring at the landing spot, a winged leap, 9 damage in a
 *     2.3-block crash), and <b>wings</b>: it spreads its wings and screeches when it first acquires a target.</li>
 * </ul>
 */
public class Gargoyle extends Monster implements AnimatedMob {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 1.8F;
    private static final double VIEW_CONE = 0.3; // isLookingAtMe: dot > 1 - 0.3 (about 45 degrees)

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private boolean frozen;
    private boolean committed; // mid-leap or past the first claw: finishes even if seen
    private float frozenYaw;
    private int swipeCooldown;
    private int diveCooldown = 60;
    private @Nullable LivingEntity lastTarget;

    public Gargoyle(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 40.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.38)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.6)
                .add(Attributes.FOLLOW_RANGE, 32.0)
                .add(Attributes.STEP_HEIGHT, 1.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new StatueGoal(this));
        goalSelector.addGoal(2, new StalkGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, false));
    }

    public boolean isFrozen() {
        return frozen;
    }

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return null; // a statue makes no sound
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.STONE_HIT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.STONE_BREAK;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void checkFallDamage(double ya, boolean onGround, BlockState onState, BlockPos pos) {
    }

    @Override
    public boolean isPushable() {
        return !frozen && super.isPushable();
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        if (frozen) {
            damage *= 0.5F; // stone skin
            level.sendParticles(ParticleTypes.CRIT, getX(), getY() + 1.0, getZ(), 6, 0.3, 0.4, 0.3, 0.1);
        }
        return super.hurtServer(level, source, damage);
    }

    /** True when a survival player can see this gargoyle (enderman-style gaze test, wider cone). */
    private boolean watched(ServerLevel level) {
        // every tick for every gargoyle: walk the player list, not every entity section of an 80-block box
        for (Player p : com.brasshaven.util.NearbyPlayers.in(level, getBoundingBox().inflate(40.0),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative())) {
            if (p.hasEffect(MobEffects.BLINDNESS) || p.hasEffect(MobEffects.DARKNESS)) {
                continue;
            }
            if (p.isLookingAtMe(this, VIEW_CONE, false, true, getEyeY(), getY() + 0.5)) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (swipeCooldown > 0) {
            swipeCooldown--;
        }
        if (diveCooldown > 0) {
            diveCooldown--;
        }
        boolean seen = watched(level);
        if (seen && !frozen) {
            frozenYaw = getYRot();
            level.playSound(null, this, SoundEvents.GRINDSTONE_USE, SoundSource.HOSTILE, 0.5F, 0.5F);
            level.sendParticles(ParticleTypes.WHITE_ASH, getX(), getY() + 1.0, getZ(), 12, 0.4, 0.6, 0.4, 0.0);
        }
        frozen = seen;
        if (frozen && !committed) {
            getNavigation().stop();
            setDeltaMovement(0, Math.min(0, getDeltaMovement().y), 0);
            setYRot(frozenYaw);
            yBodyRot = frozenYaw;
            yHeadRot = frozenYaw;
        }
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.Gargoyle.TICKS;
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
        }
    }

    // ------------------------------------------------------------------ helpers

    private boolean isVictim(LivingEntity e) {
        if (e == this || !e.isAlive()) {
            return false;
        }
        if (e instanceof Player p) {
            return !p.isCreative() && !p.isSpectator();
        }
        return !(e instanceof Enemy);
    }

    private Vec3 facing(float yaw) {
        float r = yaw * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
    }

    private void face(LivingEntity t) {
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * Mth.RAD_TO_DEG) - 90.0F;
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
    }

    private void lock(float yaw) {
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
    }

    private void claw(ServerLevel level, float yaw, float damage, double knockback) {
        Vec3 fwd = facing(yaw);
        double cos = Math.cos(Math.toRadians(75));
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(3.5), this::isVictim)) {
            Vec3 to = e.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d <= 2.8 + e.getBbWidth() / 2 && (d < 0.8 || to.normalize().dot(fwd) >= cos)) {
                if (e.hurtServer(level, damageSources().mobAttack(this), damage) && knockback > 0) {
                    Vec3 push = d > 0.01 ? to.normalize().scale(knockback) : fwd.scale(knockback);
                    e.push(push.x, 0.3, push.z);
                    e.hurtMarked = true;
                }
            }
        }
        Vec3 p = position().add(fwd.scale(1.5));
        level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.0, p.z, 1, 0, 0, 0, 0);
        level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 0.7F);
        level.playSound(null, this, SoundEvents.STONE_HIT, SoundSource.HOSTILE, 1.0F, 0.6F);
    }

    // ------------------------------------------------------------------ brain

    /** While watched, nothing else may move or turn the statue. */
    static final class StatueGoal extends Goal {
        private final Gargoyle g;

        StatueGoal(Gargoyle g) {
            this.g = g;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            return g.frozen && !g.committed;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void start() {
            g.getNavigation().stop();
        }

        @Override
        public void tick() {
            g.getNavigation().stop();
            g.lock(g.frozenYaw);
        }
    }

    /** Unseen: close in fast, claw combos, winged dives. */
    static final class StalkGoal extends Goal {
        private final Gargoyle g;
        private int action = -1;
        private int tick;
        private float yaw;
        private Vec3 landing = Vec3.ZERO;
        private boolean landed;

        StalkGoal(Gargoyle g) {
            this.g = g;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = g.getTarget();
            return !g.frozen && t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            if (g.frozen) {
                return g.committed; // a wind-up is cancelled the moment it is seen
            }
            return action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            action = -1;
            g.committed = false;
            g.getNavigation().stop();
        }

        private void begin(int which) {
            action = which;
            tick = 0;
            g.committed = false;
            yaw = g.getYRot();
            g.getNavigation().stop();
            AnimatedMob.playAction(g, which);
        }

        @Override
        public void tick() {
            if (!(g.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = g.getTarget();
            if (action == MobAnims.Gargoyle.SWIPE) {
                tickSwipe(level, t);
                return;
            }
            if (action == MobAnims.Gargoyle.DIVE) {
                tickDive(level, t);
                return;
            }
            if (action == MobAnims.Gargoyle.WINGS) {
                g.lock(yaw);
                g.getNavigation().stop();
                if (tick == 8) {
                    level.playSound(null, g, SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 1.0F, 1.6F);
                    level.sendParticles(ParticleTypes.WHITE_ASH, g.getX(), g.getY() + 1.4, g.getZ(), 30, 1.2, 0.6, 1.2, 0.02);
                }
                if (++tick >= MobAnims.Gargoyle.TICKS[MobAnims.Gargoyle.WINGS]) {
                    action = -1;
                }
                return;
            }
            if (t == null) {
                return;
            }
            if (g.lastTarget != t) {
                g.lastTarget = t;
                g.face(t);
                begin(MobAnims.Gargoyle.WINGS);
                return;
            }
            g.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(g.distanceToSqr(t));
            double above = g.getY() - t.getY();
            if (dist < 2.8 && g.swipeCooldown == 0) {
                g.face(t);
                begin(MobAnims.Gargoyle.SWIPE);
                return;
            }
            boolean diveRange = dist >= 4.0 && dist <= 13.0 || above >= 2.5 && dist <= 14.0;
            if (diveRange && g.diveCooldown == 0 && g.onGround() && g.getSensing().hasLineOfSight(t)) {
                g.face(t);
                begin(MobAnims.Gargoyle.DIVE);
                landing = t.position();
                landed = false;
                level.playSound(null, g, SoundEvents.BAT_TAKEOFF, SoundSource.HOSTILE, 1.0F, 0.5F);
                return;
            }
            if (g.tickCount % 4 == 0) {
                g.getNavigation().moveTo(t, 1.0);
            }
        }

        private void tickSwipe(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            if (t != null && (k < 9 || k > 12 && k < 17)) {
                g.face(t);
                yaw = g.getYRot();
            }
            g.lock(yaw);
            g.getNavigation().stop();
            if (k == 12) {
                g.committed = true;
                g.claw(level, yaw, 7.0F, 0.25);
                g.setDeltaMovement(g.facing(yaw).scale(0.3));
            } else if (k == 20) {
                g.claw(level, yaw, 8.0F, 1.1);
                g.setDeltaMovement(g.facing(yaw).scale(0.35));
            }
            if (k >= MobAnims.Gargoyle.TICKS[MobAnims.Gargoyle.SWIPE]) {
                action = -1;
                g.committed = false;
                g.swipeCooldown = 24;
            }
        }

        private void tickDive(ServerLevel level, @Nullable LivingEntity t) {
            int k = tick++;
            g.getNavigation().stop();
            if (k < 10) {
                if (t != null && k < 7) {
                    landing = t.position();
                    g.face(t);
                    yaw = g.getYRot();
                }
                g.lock(yaw);
                if (k % 2 == 0) {
                    for (int i = 0; i < 14; i++) {
                        double a = Math.PI * 2 * i / 14;
                        level.sendParticles(ParticleTypes.WHITE_ASH, landing.x + Math.cos(a) * 2.3, landing.y + 0.15,
                                landing.z + Math.sin(a) * 2.3, 1, 0, 0, 0, 0);
                    }
                }
            } else if (k == 10) {
                g.committed = true;
                Vec3 to = landing.subtract(g.position());
                double h = Math.sqrt(to.x * to.x + to.z * to.z);
                double flight = 14.0;
                double hs = Math.min(1.5, h / flight * 1.15);
                Vec3 dir = h > 0.01 ? new Vec3(to.x / h, 0, to.z / h) : g.facing(yaw);
                double vy = Mth.clamp(0.55 + to.y * 0.06, 0.25, 0.9);
                g.setDeltaMovement(dir.x * hs, vy, dir.z * hs);
                g.hurtMarked = true;
                level.playSound(null, g, SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 1.2F, 0.6F);
            } else if (!landed && (k > 13 && g.onGround() || k >= 34)) {
                landed = true;
                double r = 2.3;
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(g.position(), g.position()).inflate(r, 2, r),
                        g::isVictim)) {
                    if (e.position().distanceTo(g.position()) <= r + 0.5
                            && e.hurtServer(level, g.damageSources().mobAttack(g), 9.0F)) {
                        Vec3 push = e.position().subtract(g.position()).multiply(1, 0, 1).normalize().scale(0.8);
                        e.push(push.x, 0.4, push.z);
                        e.hurtMarked = true;
                    }
                }
                level.sendParticles(ParticleTypes.CLOUD, g.getX(), g.getY() + 0.2, g.getZ(), 24, 1.2, 0.1, 1.2, 0.05);
                level.sendParticles(ParticleTypes.EXPLOSION, g.getX(), g.getY() + 0.3, g.getZ(), 1, 0, 0, 0, 0);
                level.playSound(null, g, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.8F, 1.3F);
                level.playSound(null, g, SoundEvents.STONE_BREAK, SoundSource.HOSTILE, 1.2F, 0.6F);
            }
            if (k > 10) {
                g.lock(yaw);
            }
            if (k >= MobAnims.Gargoyle.TICKS[MobAnims.Gargoyle.DIVE] && (landed || k > 40)) {
                action = -1;
                g.committed = false;
                g.diveCooldown = 140;
            }
        }
    }
}

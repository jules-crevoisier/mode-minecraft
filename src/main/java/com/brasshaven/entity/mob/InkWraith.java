package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.FlyingMoveControl;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomFlyingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Spectre d'encre (Ink Wraith): the spilt ink of the Starfall Library risen into a shape (model tools/wf/mobs/ink_wraith.py).
 * <ul>
 *     <li>Floats and flies; <b>glides through bookshelves</b> as if they were not there (no collision with bookshelves,
 *     no suffocation inside them) and flies straight at its prey when only shelves stand between them.</li>
 *     <li><b>Nib rake</b> (within 2.5 blocks, every 1.3 s): the right hand drawn back high, lands at 8 ticks.</li>
 *     <li><b>Ink splash</b> (3 to 11 blocks, in sight, every 4 s): an orb of ink swells between its cupped hands (ink
 *     drips gather there), the aim locks at 10 ticks, it is flung at 14: whoever it hits is blinded for 3 s and hurt a
 *     little. Sidestep after the lock.</li>
 *     <li><b>Shelf dive</b> (prey 4 to 16 blocks away, a bookshelf next to the wraith and one near the prey, every
 *     8 s): it melts into a shelf; ink bubbles out of another shelf close to its prey (the telegraph), it slips out of
 *     that one at 18 ticks nibs first: hits and blinds whatever is right in front of the shelf.</li>
 * </ul>
 */
public class InkWraith extends ActionMonster {
    public static final float WIDTH = 0.7F;
    public static final float HEIGHT = 2.0F;
    private static final int CLAW_HIT = 8;       // 0.4 s, matches ink_wraith.py
    private static final int SPLASH_LOCK = 10;
    private static final int SPLASH_THROW = 14;  // 0.7 s
    private static final int DIVE_GONE = 10;     // 0.5 s: melted into the shelf
    private static final int DIVE_OUT = 17;
    private static final int DIVE_HIT = 18;      // 0.9 s
    private static final double BLOB_SPEED = 0.8;

    private static final class Blob {
        Vec3 p;
        final Vec3 v;
        int life = 20;

        Blob(Vec3 p, Vec3 v) {
            this.p = p;
            this.v = v;
        }
    }

    private final List<Blob> blobs = new ArrayList<>();
    private int clawCooldown;
    private int splashCooldown = 40;
    private int diveCooldown = 100;
    private Vec3 aim = Vec3.ZERO;
    private @Nullable Vec3 diveTo;
    private @Nullable BlockPos diveShelf;

    public InkWraith(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.moveControl = new FlyingMoveControl<>(this, 20, true);
        this.xpReward = 10;
        setNoGravity(true);
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 26.0)
                .add(Attributes.ARMOR, 0.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.25)
                .add(Attributes.FLYING_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 24.0);
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
        goalSelector.addGoal(2, new InkGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomFlyingGoal(this, 0.6));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.InkWraith.TICKS;
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ through the bookshelves

    static boolean isShelf(BlockState s) {
        return s.is(Blocks.BOOKSHELF) || s.is(Blocks.CHISELED_BOOKSHELF);
    }

    /** True when every solid block the box touches is a bookshelf, and at least one is. */
    private boolean onlyShelves(AABB box) {
        Level level = level();
        boolean any = false;
        for (BlockPos p : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ),
                BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
            BlockState s = level.getBlockState(p);
            if (isShelf(s)) {
                any = true;
            } else if (!s.getCollisionShape(level, p).isEmpty()) {
                return false;
            }
        }
        return any;
    }

    /** Only air or bookshelves on the straight line from here to ``to`` (at the wraith's height and its middle). */
    private boolean clearThroughShelves(Vec3 to) {
        Level level = level();
        Vec3 from = position();
        Vec3 d = to.subtract(from);
        int n = Math.max(2, (int) (d.length() * 2.5));
        for (int i = 1; i <= n; i++) {
            Vec3 p = from.add(d.scale(i / (double) n));
            for (double dy : new double[] {0.3, 1.5}) {
                BlockPos b = BlockPos.containing(p.x, p.y + dy, p.z);
                BlockState s = level.getBlockState(b);
                if (!isShelf(s) && !s.getCollisionShape(level, b).isEmpty()) {
                    return false;
                }
            }
        }
        return true;
    }

    @Override
    public void tick() {
        if (!level().isClientSide()) {
            Vec3 v = getDeltaMovement();
            AABB next = getBoundingBox().move(v).inflate(0.05);
            noPhysics = onlyShelves(next) || onlyShelves(getBoundingBox().inflate(-0.05));
        }
        super.tick();
        if (level().isClientSide() && random.nextInt(4) == 0) {
            level().addParticle(ParticleTypes.SQUID_INK, getRandomX(0.4), getY() + 0.2 + random.nextDouble() * 0.4, getRandomZ(0.4),
                    0, -0.02, 0);
        }
    }

    @Override
    public boolean isInWall() {
        BlockPos eye = BlockPos.containing(getX(), getEyeY(), getZ());
        return !isShelf(level().getBlockState(eye)) && super.isInWall();
    }

    // ------------------------------------------------------------------ ink blobs

    private void tickBlobs(ServerLevel level) {
        for (int i = blobs.size() - 1; i >= 0; i--) {
            Blob b = blobs.get(i);
            Vec3 next = b.p.add(b.v);
            boolean burst = --b.life <= 0;
            LivingEntity victim = null;
            HitResult hit = level.clip(new ClipContext(b.p, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
            if (hit.getType() != HitResult.Type.MISS) {
                next = hit.getLocation();
                burst = true;
            }
            AABB sweep = new AABB(b.p, next).inflate(0.5);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, sweep, e -> e != this && e.isAlive() && !(e instanceof InkWraith))) {
                if (e.getBoundingBox().inflate(0.35).clip(b.p, next).isPresent()) {
                    victim = e;
                    burst = true;
                    break;
                }
            }
            b.p = next;
            level.sendParticles(ParticleTypes.SQUID_INK, b.p.x, b.p.y, b.p.z, 2, 0.05, 0.05, 0.05, 0.0);
            if (burst) {
                level.sendParticles(ParticleTypes.SQUID_INK, b.p.x, b.p.y, b.p.z, 16, 0.4, 0.4, 0.4, 0.05);
                level.playSound(null, b.p.x, b.p.y, b.p.z, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.0F, 0.7F);
                if (victim != null) {
                    if (victim.hurtServer(level, damageSources().mobProjectile(this, this), 3.0F)) {
                        victim.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0), this);
                    }
                }
                blobs.remove(i);
            }
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (clawCooldown > 0) {
            clawCooldown--;
        }
        if (splashCooldown > 0) {
            splashCooldown--;
        }
        if (diveCooldown > 0) {
            diveCooldown--;
        }
        tickBlobs(level);
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (isInvisible() && action == MobAnims.InkWraith.DIVE) {
            return false;                                                    // inside the shelf: nothing to hit
        }
        return super.hurtServer(level, source, amount);
    }

    // ------------------------------------------------------------------ sounds: whispers and wet pages

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.BOOK_PAGE_TURN;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SQUID_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SQUID_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    /** Rake up close, splash from afar, dive through the shelves to come out behind its prey. */
    static final class InkGoal extends Goal {
        private final InkWraith w;
        private int repath;

        InkGoal(InkWraith w) {
            this.w = w;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = w.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return w.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            w.getNavigation().stop();
            w.setInvisible(false);
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
                w.getNavigation().stop();
                w.setDeltaMovement(w.getDeltaMovement().scale(0.6));
                if (a == MobAnims.InkWraith.CLAW) {
                    if (t != null && k < CLAW_HIT) {
                        w.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    }
                    if (k == CLAW_HIT) {
                        level.playSound(null, w, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.8F, 1.3F);
                        if (t != null && t.isAlive() && w.distanceToSqr(t) <= 3.0 * 3.0 && inFront(t, 0.2)) {
                            w.doHurtTarget(level, t);
                        }
                    }
                } else if (a == MobAnims.InkWraith.SPLASH) {
                    if (k >= 0 && k <= SPLASH_LOCK && t != null && t.isAlive()) {
                        w.aim = t.getEyePosition().add(0, -0.3, 0);
                        w.getLookControl().setLookAt(t, 30.0F, 30.0F);
                    }
                    if (k > 0 && k < SPLASH_THROW && k % 2 == 0) {
                        // the telegraph: ink drips gathering between its hands
                        Vec3 p = w.position().add(w.forward().scale(0.5)).add(0, 1.3, 0);
                        level.sendParticles(ParticleTypes.SQUID_INK, p.x, p.y, p.z, 3, 0.2, 0.2, 0.2, 0.0);
                    }
                    if (k == SPLASH_LOCK) {
                        level.playSound(null, w, SoundEvents.BUCKET_FILL, SoundSource.HOSTILE, 0.8F, 0.6F);
                    }
                    if (k == SPLASH_THROW) {
                        Vec3 from = w.position().add(w.forward().scale(0.6)).add(0, 1.3, 0);
                        Vec3 dir = w.aim.subtract(from);
                        dir = dir.lengthSqr() < 1.0E-4 ? w.forward() : dir.normalize();
                        w.blobs.add(new Blob(from, dir.scale(BLOB_SPEED)));
                        level.playSound(null, w, SoundEvents.SQUID_SQUIRT, SoundSource.HOSTILE, 1.2F, 0.8F);
                    }
                } else if (a == MobAnims.InkWraith.DIVE) {
                    dive(level, t, k);
                }
                return;
            }
            if (t == null) {
                return;
            }
            w.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(w.distanceToSqr(t));
            boolean sees = w.getSensing().hasLineOfSight(t);
            if (dist >= 4.0 && dist <= 16.0 && w.diveCooldown == 0 && w.random.nextInt(4) == 0 && planDive(level, t)) {
                w.diveCooldown = 160;
                w.begin(MobAnims.InkWraith.DIVE);
                level.playSound(null, w, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 1.2F, 0.5F);
                return;
            }
            if (dist <= 2.5 && w.clawCooldown == 0) {
                w.clawCooldown = 26;
                w.begin(MobAnims.InkWraith.CLAW);
                return;
            }
            if (dist >= 3.0 && dist <= 11.0 && sees && w.splashCooldown == 0) {
                w.splashCooldown = 80;
                w.aim = t.getEyePosition();
                w.begin(MobAnims.InkWraith.SPLASH);
                return;
            }
            Vec3 goal = new Vec3(t.getX(), t.getY() + 0.2, t.getZ());
            if (dist > 1.8 && dist < 14.0 && w.clearThroughShelves(goal)) {
                // straight through the shelves
                w.getNavigation().stop();
                w.getMoveControl().setWantedPosition(goal.x, goal.y, goal.z, 1.0);
            } else if (--repath <= 0) {
                repath = 10;
                if (dist > 1.8) {
                    w.getNavigation().moveTo(goal.x, goal.y, goal.z, 1.0);
                }
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(w.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.8 || to.normalize().dot(w.forward()) >= minDot;
        }

        /** A shelf right next to the wraith to melt into, and one near the prey (the far side, preferably) to come
         * out of, with a free 2-block-high cell in front of it. */
        private boolean planDive(ServerLevel level, LivingEntity t) {
            BlockPos me = w.blockPosition();
            boolean near = false;
            for (BlockPos p : BlockPos.betweenClosed(me.offset(-2, -1, -2), me.offset(2, 2, 2))) {
                if (isShelf(level.getBlockState(p))) {
                    near = true;
                    break;
                }
            }
            if (!near) {
                return false;
            }
            BlockPos tp = t.blockPosition();
            Vec3 best = null;
            BlockPos bestShelf = null;
            double bestScore = -1;
            for (BlockPos p : BlockPos.betweenClosed(tp.offset(-4, -1, -4), tp.offset(4, 2, 4))) {
                if (!isShelf(level.getBlockState(p))) {
                    continue;
                }
                for (Direction dir : Direction.Plane.HORIZONTAL) {
                    BlockPos c = p.relative(dir);
                    if (!level.getBlockState(c).getCollisionShape(level, c).isEmpty()
                            || !level.getBlockState(c.above()).getCollisionShape(level, c.above()).isEmpty()) {
                        continue;
                    }
                    Vec3 out = Vec3.atBottomCenterOf(c);
                    double toPrey = out.distanceTo(t.position());
                    if (toPrey < 1.0 || toPrey > 4.0) {
                        continue;
                    }
                    double score = out.distanceTo(w.position()) - toPrey;            // far from the wraith, close to the prey
                    if (score > bestScore) {
                        bestScore = score;
                        best = out;
                        bestShelf = p.immutable();
                    }
                }
            }
            w.diveTo = best;
            w.diveShelf = bestShelf;
            return best != null;
        }

        private void dive(ServerLevel level, @Nullable LivingEntity t, int k) {
            if (k < 0) {
                w.setInvisible(false);
                return;
            }
            if (w.diveTo == null || w.diveShelf == null) {
                return;
            }
            Vec3 out = w.diveTo;
            if (k < DIVE_HIT && k % 2 == 0) {
                // the telegraph: ink bubbling out of the shelf it will come out of
                Vec3 s = Vec3.atCenterOf(w.diveShelf);
                Vec3 face = s.add(out.subtract(s).multiply(1, 0, 1).normalize().scale(0.55));
                level.sendParticles(ParticleTypes.SQUID_INK, face.x, face.y + 0.5, face.z, 4, 0.2, 0.4, 0.2, 0.01);
                if (k % 6 == 0) {
                    level.playSound(null, face.x, face.y, face.z, SoundEvents.BUBBLE_COLUMN_UPWARDS_INSIDE, SoundSource.HOSTILE, 0.8F, 0.6F);
                }
            }
            if (k < DIVE_GONE) {
                Vec3 p = w.position();
                level.sendParticles(ParticleTypes.SQUID_INK, p.x, p.y + 0.6, p.z, 3, 0.3, 0.4, 0.3, 0.0);
            }
            if (k == DIVE_GONE) {
                w.setInvisible(true);
                float yaw = t != null ? (float) (Mth.atan2(t.getZ() - out.z, t.getX() - out.x) * Mth.RAD_TO_DEG) - 90.0F : w.getYRot();
                w.snapTo(out.x, out.y, out.z, yaw, 0.0F);
                w.setYHeadRot(yaw);
                w.yBodyRot = yaw;
                w.setDeltaMovement(Vec3.ZERO);
                level.playSound(null, w, SoundEvents.BOOK_PAGE_TURN, SoundSource.HOSTILE, 1.2F, 0.6F);
            }
            if (k == DIVE_OUT) {
                w.setInvisible(false);
                level.sendParticles(ParticleTypes.SQUID_INK, out.x, out.y + 1.0, out.z, 20, 0.4, 0.6, 0.4, 0.05);
            }
            if (k == DIVE_HIT) {
                level.playSound(null, w, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 1.1F);
                float dmg = (float) w.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.2F;
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, w.getBoundingBox().inflate(2.0, 0.5, 2.0),
                        e -> e != w && e.isAlive() && !(e instanceof InkWraith))) {
                    if (w.distanceToSqr(e) > 2.6 * 2.6 || !inFront(e, 0.0)) {
                        continue;
                    }
                    if (e.hurtServer(level, w.damageSources().mobAttack(w), dmg)) {
                        e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0), w);
                    }
                }
                w.diveTo = null;
                w.diveShelf = null;
            }
        }
    }
}

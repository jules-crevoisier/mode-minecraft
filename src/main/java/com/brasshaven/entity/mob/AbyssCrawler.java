package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
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
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Rampant de l'abîme (Abyss Crawler): the pale, eyeless climber of the Inverted Spire (model
 * tools/wf/mobs/abyss_crawler.py).
 * <ul>
 *     <li>Climbs walls like a spider (wall-climber navigation, climbing flag as vanilla {@code Spider}), ignores
 *     cobwebs, takes no fall damage.</li>
 *     <li><b>Ceiling ambush</b>: with no prey in reach it seeks a wall and climbs it; when its back meets a ceiling it
 *     <b>clings</b> there without gravity. A player passing within 2.5 blocks beneath it (in sight, up to 12 blocks
 *     down) sets off the <b>drop</b>: it curls up while grit trickles down (10 ticks), then lets go and falls; landing
 *     within 1.8 blocks of anyone deals 1.6x damage and slows. A blow knocks it off the ceiling at once.</li>
 *     <li><b>Rake</b> (within 2 blocks, every 1.25 s): rears and lifts both forelegs, lands at 7 ticks.</li>
 *     <li><b>Screech</b> (within 6 blocks, every 10 s): rears up while its four-way jaw peels open, screeches at 14
 *     ticks: Darkness for 5 s, a short slowness and a little damage to every player within 7 blocks.</li>
 * </ul>
 */
public class AbyssCrawler extends ActionMonster {
    public static final float WIDTH = 1.2F;
    public static final float HEIGHT = 0.7F;
    private static final EntityDataAccessor<Boolean> DATA_CLIMBING = SynchedEntityData.defineId(AbyssCrawler.class, EntityDataSerializers.BOOLEAN);
    private static final int RAKE_HIT = 7;       // 0.35 s, matches abyss_crawler.py
    private static final int SCREECH_AT = 14;    // 0.7 s
    private static final int DROP_AT = 10;       // 0.5 s

    private int rakeCooldown;
    private int screechCooldown = 60;
    private int clingCooldown = 40;
    private boolean clinging;
    private boolean dropping;

    public AbyssCrawler(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 9;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 24.0)
                .add(Attributes.ARMOR, 3.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 28.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new CrawlerGoal(this));
        goalSelector.addGoal(4, new SeekCeilingGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.AbyssCrawler.TICKS;
    }

    // ------------------------------------------------------------------ climbing (as vanilla Spider)

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_CLIMBING, false);
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        return new WallClimberNavigation(this, level);
    }

    public boolean isClimbing() {
        return entityData.get(DATA_CLIMBING);
    }

    @Override
    public boolean onClimbable() {
        return isClimbing() && !clinging;
    }

    @Override
    public void makeStuckInBlock(BlockState state, Vec3 speedMultiplier) {
        if (!state.is(Blocks.COBWEB)) {
            super.makeStuckInBlock(state, speedMultiplier);
        }
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource damageSource) {
        return false;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("Clinging", clinging);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        clinging = input.getBooleanOr("Clinging", false);
        setNoGravity(clinging);
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ the ceiling

    private boolean ceilingAbove(Level level) {
        BlockPos up = BlockPos.containing(getX(), getBoundingBox().maxY + 0.2, getZ());
        return level.getBlockState(up).isFaceSturdy(level, up, Direction.DOWN);
    }

    private void cling() {
        clinging = true;
        setNoGravity(true);
        setDeltaMovement(Vec3.ZERO);
        getNavigation().stop();
    }

    private void letGo() {
        clinging = false;
        setNoGravity(false);
        clingCooldown = 200;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && clinging) {
            letGo();                                                         // knocked off the ceiling
        }
        return hurt;
    }

    @Override
    public void tick() {
        super.tick();
        if (!level().isClientSide()) {
            entityData.set(DATA_CLIMBING, horizontalCollision || clinging);
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (rakeCooldown > 0) {
            rakeCooldown--;
        }
        if (screechCooldown > 0) {
            screechCooldown--;
        }
        if (clingCooldown > 0) {
            clingCooldown--;
        }
        if (clinging) {
            setDeltaMovement(Vec3.ZERO);
            if (!ceilingAbove(level)) {
                letGo();                                                     // the ceiling is gone
            }
        } else if (action < 0 && clingCooldown == 0 && isClimbing() && !onGround() && ceilingAbove(level)
                && (getTarget() == null || distanceToSqr(getTarget()) > 5.0 * 5.0)) {
            cling();
        }
        if (dropping && onGround()) {
            dropping = false;
            land(level);
        }
    }

    private void land(ServerLevel level) {
        level.playSound(null, this, SoundEvents.SPIDER_HURT, SoundSource.HOSTILE, 1.0F, 0.5F);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, getBlockStateOn()), getX(), getY() + 0.1, getZ(),
                16, 0.6, 0.05, 0.6, 0.1);
        float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.6F;
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(1.2, 1.0, 1.2),
                e -> e != this && e.isAlive() && !(e instanceof AbyssCrawler))) {
            if (distanceToSqr(e) > 1.8 * 1.8 + 1.0) {
                continue;
            }
            if (e.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), this);
            }
        }
    }

    // ------------------------------------------------------------------ sounds: chitter and click

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return clinging ? null : SoundEvents.SPIDER_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SPIDER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SPIDER_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SPIDER_STEP, 0.15F, 1.3F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.6F;
    }

    /** With nothing to hunt: find a wall with a ceiling over it and climb up to wait there. */
    static final class SeekCeilingGoal extends Goal {
        private final AbyssCrawler c;
        private @Nullable Vec3 wall;
        private int time;

        SeekCeilingGoal(AbyssCrawler c) {
            this.c = c;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            if (c.clinging || c.getTarget() != null || c.clingCooldown > 0 || c.random.nextInt(60) != 0) {
                return false;
            }
            Level level = c.level();
            BlockPos me = c.blockPosition();
            for (Direction dir : Direction.Plane.HORIZONTAL.shuffledCopy(c.random)) {
                for (int i = 1; i <= 6; i++) {
                    BlockPos p = me.relative(dir, i);
                    if (level.getBlockState(p).isFaceSturdy(level, p, dir.getOpposite())) {
                        // a wall: is there a ceiling above the cell in front of it, within 10 blocks?
                        BlockPos front = p.relative(dir.getOpposite());
                        for (int dy = 2; dy <= 10; dy++) {
                            BlockPos up = front.above(dy);
                            if (level.getBlockState(up).isFaceSturdy(level, up, Direction.DOWN)) {
                                wall = Vec3.atBottomCenterOf(p);
                                return true;
                            }
                        }
                        break;
                    }
                    if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty()) {
                        break;
                    }
                }
            }
            return false;
        }

        @Override
        public void start() {
            time = 200;
        }

        @Override
        public boolean canContinueToUse() {
            return wall != null && !c.clinging && c.getTarget() == null && time > 0;
        }

        @Override
        public void tick() {
            time--;
            if (wall != null) {
                // pressing into the wall makes it climb (onClimbable while it collides horizontally)
                c.getMoveControl().setWantedPosition(wall.x, c.getY() + 1.0, wall.z, 0.9);
            }
        }

        @Override
        public void stop() {
            wall = null;
        }
    }

    /** Drop from the ceiling onto prey below; rake and screech on the ground. */
    static final class CrawlerGoal extends Goal {
        private final AbyssCrawler c;
        private int repath;

        CrawlerGoal(AbyssCrawler c) {
            this.c = c;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (c.clinging) {
                return true;
            }
            LivingEntity t = c.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return c.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            c.getNavigation().stop();
        }

        /** A player right beneath the clinging crawler, or null. */
        private @Nullable Player preyBelow(ServerLevel level) {
            for (Player p : level.getEntitiesOfClass(Player.class, c.getBoundingBox().inflate(2.5, 12.0, 2.5),
                    p -> p.isAlive() && !p.isCreative() && !p.isSpectator())) {
                double dx = p.getX() - c.getX();
                double dz = p.getZ() - c.getZ();
                double dy = c.getY() - p.getY();
                if (dx * dx + dz * dz <= 2.5 * 2.5 && dy >= 1.5 && dy <= 12.0 && c.getSensing().hasLineOfSight(p)) {
                    return p;
                }
            }
            return null;
        }

        @Override
        public void tick() {
            if (!(c.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = c.getTarget();
            if (c.action >= 0) {
                int a = c.action;
                int k = c.step();
                c.getNavigation().stop();
                if (a == MobAnims.AbyssCrawler.DROP) {
                    if (k >= 0 && k < DROP_AT && k % 2 == 0) {
                        // the telegraph: grit trickling down from where it clings
                        BlockPos up = BlockPos.containing(c.getX(), c.getBoundingBox().maxY + 0.2, c.getZ());
                        BlockState s = level.getBlockState(up);
                        level.sendParticles(new BlockParticleOption(ParticleTypes.FALLING_DUST, s.isAir() ? Blocks.STONE.defaultBlockState() : s),
                                c.getX(), c.getY() - 0.1, c.getZ(), 4, 0.4, 0.0, 0.4, 0.0);
                        if (k == 0) {
                            level.playSound(null, c, SoundEvents.GRAVEL_FALL, SoundSource.HOSTILE, 1.0F, 0.6F);
                        }
                    } else if (k == DROP_AT) {
                        c.letGo();
                        c.dropping = true;
                        Vec3 push = t != null ? c.toward(t).scale(0.2) : Vec3.ZERO;
                        c.setDeltaMovement(push.x, -0.6, push.z);
                        c.hurtMarked = true;
                        level.playSound(null, c, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 1.2F, 0.5F);
                    }
                } else if (a == MobAnims.AbyssCrawler.RAKE && k == RAKE_HIT) {
                    level.playSound(null, c, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.7F, 1.4F);
                    if (t != null && t.isAlive() && c.distanceToSqr(t) <= 2.6 * 2.6 && inFront(t, 0.2)) {
                        c.doHurtTarget(level, t);
                    }
                } else if (a == MobAnims.AbyssCrawler.SCREECH) {
                    if (k > 0 && k < SCREECH_AT && k % 3 == 0) {
                        Vec3 p = c.position().add(c.forward().scale(0.9)).add(0, 0.9, 0);
                        level.sendParticles(ParticleTypes.GLOW, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0.0);
                    }
                    if (k == SCREECH_AT) {
                        screech(level);
                    }
                }
                return;
            }
            if (c.clinging) {
                c.getNavigation().stop();
                Player p = preyBelow(level);
                if (p != null) {
                    c.setTarget(p);
                    c.begin(MobAnims.AbyssCrawler.DROP);
                }
                return;
            }
            if (t == null) {
                return;
            }
            c.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(c.distanceToSqr(t));
            if (dist <= 6.0 && c.screechCooldown == 0 && c.onGround() && c.random.nextInt(4) == 0) {
                c.screechCooldown = 200;
                c.begin(MobAnims.AbyssCrawler.SCREECH);
                level.playSound(null, c, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE, 1.0F, 0.4F);
                return;
            }
            if (dist <= 2.0 && c.rakeCooldown == 0) {
                c.rakeCooldown = 25;
                c.begin(MobAnims.AbyssCrawler.RAKE);
                return;
            }
            if (--repath <= 0) {
                repath = 8;
                c.getNavigation().moveTo(t, 1.1);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(c.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.8 || to.normalize().dot(c.forward()) >= minDot;
        }

        private void screech(ServerLevel level) {
            level.playSound(null, c, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.HOSTILE, 1.6F, 1.3F);
            Vec3 p = c.position().add(c.forward().scale(0.9)).add(0, 0.6, 0);
            level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            level.sendParticles(ParticleTypes.SCULK_SOUL, c.getX(), c.getY() + 0.6, c.getZ(), 10, 1.5, 0.4, 1.5, 0.02);
            for (Player pl : level.getEntitiesOfClass(Player.class, c.getBoundingBox().inflate(7.0),
                    e -> e.isAlive() && !e.isCreative() && !e.isSpectator())) {
                if (c.distanceToSqr(pl) > 7.0 * 7.0) {
                    continue;
                }
                pl.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0), c);
                pl.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0), c);
                pl.hurtServer(level, c.damageSources().mobAttack(c), 2.0F);
            }
        }
    }
}

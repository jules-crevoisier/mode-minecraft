package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import com.brasshaven.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;

/**
 * Mère des mites de rouille (Rust Mite Swarm-Mother): the brood-tick of the Fallen Colossus (model
 * tools/wf/mobs/rust_mite_mother.py).
 * <ul>
 *     <li><b>Corroding bite</b> (within 1.8 blocks, every 1.25 s): rears and spreads its chelicerae, snaps at 6 ticks:
 *     damage, and every piece of armour the prey wears loses 3 durability.</li>
 *     <li><b>Rust spit</b> (3 to 10 blocks, in sight, every 5 s): its abdomen pumps three times while it rears, spits at
 *     12 ticks: a gobbet of rust flies in a shallow arc; on a hit, 3 damage, Slowness II and Weakness for 4 s.</li>
 *     <li><b>Brood burst</b> (once in its life, when its prey is within 8 blocks and it is below 75% health, or after a
 *     while in a fight): plants its legs while its abdomen swells and shudders, pores glowing (20 ticks), then two or
 *     three {@link RustMite}s spill out. Killing it during the swelling stops the brood.</li>
 * </ul>
 */
public class RustMiteMother extends ActionMonster {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 0.75F;
    private static final int BITE_HIT = 6;      // 0.3 s, matches rust_mite_mother.py
    private static final int SPIT_AT = 12;      // 0.6 s
    private static final int BROOD_AT = 20;     // 1.0 s
    private static final DustParticleOptions RUST = new DustParticleOptions(0xA4502A, 1.2F);
    private static final double GLOB_SPEED = 0.65;

    private static final class Glob {
        Vec3 p;
        Vec3 v;
        int life = 40;

        Glob(Vec3 p, Vec3 v) {
            this.p = p;
            this.v = v;
        }
    }

    private final List<Glob> globs = new ArrayList<>();
    private int biteCooldown = 10;
    private int spitCooldown = 40;
    private int fightTicks;
    private boolean broodDone;

    public RustMiteMother(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 30.0)
                .add(Attributes.ARMOR, 5.0)
                .add(Attributes.ATTACK_DAMAGE, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.FOLLOW_RANGE, 20.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new MotherGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.RustMiteMother.TICKS;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putBoolean("BroodDone", broodDone);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        broodDone = input.getBooleanOr("BroodDone", false);
    }

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    // ------------------------------------------------------------------ rust globs

    private void tickGlobs(ServerLevel level) {
        for (int i = globs.size() - 1; i >= 0; i--) {
            Glob g = globs.get(i);
            if (--g.life <= 0) {
                splat(level, g.p);
                globs.remove(i);
                continue;
            }
            g.v = g.v.add(0, -0.03, 0);
            Vec3 next = g.p.add(g.v);
            BlockPos bp = BlockPos.containing(next);
            if (!level.getBlockState(bp).getCollisionShape(level, bp).isEmpty()) {
                splat(level, g.p);
                globs.remove(i);
                continue;
            }
            g.p = next;
            level.sendParticles(RUST, g.p.x, g.p.y, g.p.z, 3, 0.06, 0.06, 0.06, 0.0);
            AABB box = new AABB(g.p.x - 0.3, g.p.y - 0.3, g.p.z - 0.3, g.p.x + 0.3, g.p.y + 0.3, g.p.z + 0.3);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box.inflate(0.3),
                    e -> e != this && e.isAlive() && !(e instanceof RustMiteMother) && !(e instanceof RustMite))) {
                if (e.getBoundingBox().intersects(box)) {
                    if (e.hurtServer(level, damageSources().mobProjectile(this, this), 3.0F)) {
                        e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1), this);
                        e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 0), this);
                    }
                    splat(level, g.p);
                    globs.remove(i);
                    break;
                }
            }
        }
    }

    private void splat(ServerLevel level, Vec3 p) {
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.RED_SAND.defaultBlockState()),
                p.x, p.y, p.z, 10, 0.2, 0.2, 0.2, 0.1);
        level.playSound(null, p.x, p.y, p.z, SoundEvents.SLIME_SQUISH_SMALL, SoundSource.HOSTILE, 0.8F, 0.6F);
    }

    /** Corrodes every piece of armour ``e`` wears. */
    private static void corrode(LivingEntity e) {
        for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
            ItemStack stack = e.getItemBySlot(slot);
            if (!stack.isEmpty() && stack.isDamageableItem()) {
                stack.hurtAndBreak(3, e, slot);
            }
        }
    }

    private void brood(ServerLevel level) {
        broodDone = true;
        level.playSound(null, this, SoundEvents.TURTLE_EGG_CRACK, SoundSource.HOSTILE, 1.2F, 0.6F);
        level.playSound(null, this, SoundEvents.SLIME_SQUISH, SoundSource.HOSTILE, 1.2F, 0.5F);
        level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.RED_SAND.defaultBlockState()),
                getX(), getY() + 0.6, getZ(), 24, 0.4, 0.3, 0.4, 0.15);
        level.sendParticles(RUST, getX(), getY() + 0.6, getZ(), 20, 0.5, 0.3, 0.5, 0.0);
        int n = 2 + random.nextInt(2);
        Vec3 back = forward().scale(-0.6);
        for (int i = 0; i < n; i++) {
            RustMite mite = ModEntities.RUST_MITE.get().create(level, EntitySpawnReason.MOB_SUMMONED);
            if (mite == null) {
                continue;
            }
            double a = Math.PI * 2 * i / n + random.nextDouble();
            mite.snapTo(getX() + back.x + Math.cos(a) * 0.3, getY() + 0.4, getZ() + back.z + Math.sin(a) * 0.3,
                    random.nextFloat() * 360F, 0);
            mite.setDeltaMovement(Math.cos(a) * 0.25, 0.35, Math.sin(a) * 0.25);
            if (getTarget() != null) {
                mite.setTarget(getTarget());
            }
            level.addFreshEntity(mite);
        }
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (biteCooldown > 0) {
            biteCooldown--;
        }
        if (spitCooldown > 0) {
            spitCooldown--;
        }
        fightTicks = getTarget() != null ? fightTicks + 1 : 0;
        tickGlobs(level);
    }

    // ------------------------------------------------------------------ sounds: clicking iron, a wet rasp

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.SILVERFISH_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.SILVERFISH_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SILVERFISH_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.SILVERFISH_STEP, 0.3F, 0.6F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.5F;
    }

    /** Spit from afar, bite up close, and once let the brood out. */
    static final class MotherGoal extends Goal {
        private final RustMiteMother m;
        private int repath;

        MotherGoal(RustMiteMother m) {
            this.m = m;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = m.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return m.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            m.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(m.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = m.getTarget();
            if (m.action >= 0) {
                int a = m.action;
                int k = m.step();
                m.getNavigation().stop();
                if (t != null && a != MobAnims.RustMiteMother.BROOD) {
                    m.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (a == MobAnims.RustMiteMother.BITE && k == BITE_HIT) {
                    level.playSound(null, m, SoundEvents.SPIDER_HURT, SoundSource.HOSTILE, 0.6F, 1.5F);
                    if (t != null && t.isAlive() && m.distanceToSqr(t) <= 2.3 * 2.3 && inFront(t)) {
                        if (m.doHurtTarget(level, t)) {
                            corrode(t);
                            level.sendParticles(RUST, t.getX(), t.getY() + t.getBbHeight() * 0.5, t.getZ(), 8, 0.3, 0.3, 0.3, 0.0);
                        }
                    }
                } else if (a == MobAnims.RustMiteMother.SPIT) {
                    if (k > 0 && k < SPIT_AT && k % 4 == 0) {
                        level.playSound(null, m, SoundEvents.SLIME_SQUISH_SMALL, SoundSource.HOSTILE, 0.7F, 0.5F + k * 0.04F);
                    }
                    if (k == SPIT_AT && t != null) {
                        Vec3 mouth = m.position().add(m.forward().scale(0.8)).add(0, 0.5, 0);
                        Vec3 aim = t.position().add(0, t.getBbHeight() * 0.5, 0).subtract(mouth);
                        double flat = Math.sqrt(aim.x * aim.x + aim.z * aim.z);
                        // a shallow arc: aim a little above the prey to make up for the fall
                        Vec3 v = new Vec3(aim.x, aim.y + flat * 0.12, aim.z).normalize().scale(GLOB_SPEED);
                        m.globs.add(new Glob(mouth, v));
                        level.playSound(null, m, SoundEvents.LLAMA_SPIT, SoundSource.HOSTILE, 1.0F, 0.6F);
                    }
                } else if (a == MobAnims.RustMiteMother.BROOD) {
                    if (k > 0 && k < BROOD_AT && k % 3 == 0) {
                        level.sendParticles(RUST, m.getX(), m.getY() + 0.7, m.getZ(), 4, 0.4, 0.3, 0.4, 0.0);
                        level.playSound(null, m, SoundEvents.SLIME_SQUISH_SMALL, SoundSource.HOSTILE, 0.6F, 0.4F);
                    }
                    if (k == BROOD_AT) {
                        m.brood(level);
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            m.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(m.distanceToSqr(t));
            if (!m.broodDone && dist <= 8.0 && (m.getHealth() < m.getMaxHealth() * 0.75F || m.fightTicks > 200)) {
                m.begin(MobAnims.RustMiteMother.BROOD);
                return;
            }
            if (dist >= 3.0 && dist <= 10.0 && m.spitCooldown == 0 && m.getSensing().hasLineOfSight(t)) {
                m.spitCooldown = 100;
                m.begin(MobAnims.RustMiteMother.SPIT);
                return;
            }
            if (dist <= 1.8 && m.biteCooldown == 0) {
                m.biteCooldown = 25;
                m.begin(MobAnims.RustMiteMother.BITE);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                m.getNavigation().moveTo(t, 1.0);
            }
        }

        private boolean inFront(LivingEntity t) {
            Vec3 to = t.position().subtract(m.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.6 || to.normalize().dot(m.forward()) >= 0.2;
        }
    }
}

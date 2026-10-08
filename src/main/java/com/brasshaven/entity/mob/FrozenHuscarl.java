package com.brasshaven.entity.mob;

import com.brasshaven.generated.MobAnims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.ItemTags;
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
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.EnumSet;

/**
 * Huscarl gelé (Frozen Huscarl): the dead house-guard of the Glacier Hall (model tools/wf/mobs/frozen_huscarl.py).
 * <ul>
 *     <li><b>Shield wall</b>: blows coming from in front of him (about 140 degrees) glance off his round shield (no
 *     damage, a short block animation, melee attackers are shoved back), except while he swings the cleave or reels.
 *     He turns slowly: circle round him and strike the flanks or the back. An axe blow on the shield <b>splits his
 *     guard</b>: he reels for 1.2 s and cannot block for 6 s.</li>
 *     <li><b>Chop</b> (within 2.8 blocks, every 2 s): the axe raised high behind the head, lands at 14 ticks: 1.25x
 *     damage and frost.</li>
 *     <li><b>Shield bash</b> (within 2.2 blocks, every 3 s): the shield drawn back, lands at 7 ticks: knocks the prey
 *     back and slows it.</li>
 *     <li><b>Freezing cleave</b> (within 3.5 blocks, every 7 s): he turns away with the axe out behind him (rime
 *     gathering), lands at 19 ticks: hits everything in a wide arc in front of him and freezes it.</li>
 *     <li>Never freezes; burns a little more (fire deals +50%).</li>
 * </ul>
 */
public class FrozenHuscarl extends ActionMonster {
    public static final float WIDTH = 0.75F;
    public static final float HEIGHT = 2.1F;
    private static final int CHOP_HIT = 14;     // 0.7 s, matches frozen_huscarl.py
    private static final int BASH_HIT = 7;      // 0.35 s
    private static final int CLEAVE_HIT = 19;   // 0.95 s

    private int chopCooldown = 20;
    private int bashCooldown;
    private int cleaveCooldown = 80;
    private int guardBroken;

    public FrozenHuscarl(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 10;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 34.0)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ATTACK_DAMAGE, 7.0)
                .add(Attributes.MOVEMENT_SPEED, 0.24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.5)
                .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(2, new HuscarlGoal(this));
        goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.7));
        goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 10.0F));
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.FrozenHuscarl.TICKS;
    }

    @Override
    public boolean canFreeze() {
        return false;
    }

    // ------------------------------------------------------------------ the shield

    private Vec3 forward() {
        float yaw = yBodyRot * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    /** True when the blow comes from within ~70 degrees of where he faces. */
    private boolean frontal(DamageSource source) {
        Vec3 from = source.getSourcePosition();
        if (from == null) {
            return false;
        }
        Vec3 to = from.subtract(position()).multiply(1, 0, 1);
        return to.lengthSqr() > 1.0E-4 && to.normalize().dot(forward()) >= 0.34;
    }

    private boolean shieldUp() {
        return guardBroken == 0 && action != MobAnims.FrozenHuscarl.CLEAVE && action != MobAnims.FrozenHuscarl.STAGGER;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (source.is(DamageTypeTags.IS_FIRE)) {
            amount *= 1.5F;
        }
        if (shieldUp() && frontal(source) && !source.is(DamageTypeTags.BYPASSES_SHIELD)) {
            Vec3 p = position().add(forward().scale(0.7));
            boolean melee = source.getEntity() != null && source.getDirectEntity() == source.getEntity();
            if (melee && source.getEntity() instanceof LivingEntity attacker && attacker.getMainHandItem().is(ItemTags.AXES)) {
                // an axe splits the guard: he reels and the shield stays down for a while
                guardBroken = 120;
                level.playSound(null, this, SoundEvents.SHIELD_BREAK.value(), SoundSource.HOSTILE, 1.0F, 0.8F);
                level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.2, p.z, 16, 0.3, 0.4, 0.3, 0.08);
                begin(MobAnims.FrozenHuscarl.STAGGER);
                return super.hurtServer(level, source, amount * 0.5F);
            }
            level.playSound(null, this, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.0F, 0.8F + random.nextFloat() * 0.2F);
            level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.2, p.z, 6, 0.25, 0.3, 0.25, 0.04);
            level.sendParticles(ParticleTypes.CRIT, p.x, p.y + 1.2, p.z, 5, 0.2, 0.3, 0.2, 0.2);
            if (melee && source.getEntity() instanceof LivingEntity attacker) {
                Vec3 push = attacker.position().subtract(position()).multiply(1, 0, 1);
                if (push.lengthSqr() > 1.0E-4) {
                    push = push.normalize().scale(0.45);
                    attacker.push(push.x, 0.1, push.z);
                    attacker.hurtMarked = true;
                }
            }
            if (action < 0) {
                begin(MobAnims.FrozenHuscarl.BLOCK);
            }
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    // ------------------------------------------------------------------ server brain

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (chopCooldown > 0) {
            chopCooldown--;
        }
        if (bashCooldown > 0) {
            bashCooldown--;
        }
        if (cleaveCooldown > 0) {
            cleaveCooldown--;
        }
        if (guardBroken > 0) {
            guardBroken--;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide() && random.nextInt(6) == 0) {
            level().addParticle(ParticleTypes.SNOWFLAKE, getRandomX(0.6), getY() + 0.5 + random.nextDouble() * 1.5,
                    getRandomZ(0.6), 0, -0.02, 0);
        }
    }

    private static void chill(LivingEntity e, int ticks) {
        if (e.canFreeze()) {
            e.setTicksFrozen(Math.min(e.getTicksRequiredToFreeze() + 120, e.getTicksFrozen() + ticks));
        }
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return SoundEvents.STRAY_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.STRAY_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.STRAY_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        playSound(SoundEvents.CHAIN_STEP, 0.4F, 0.7F);
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * 0.7F;
    }

    /** Close in shield first, chop, bash, cleave; turns slowly so the prey can flank him. */
    static final class HuscarlGoal extends Goal {
        private final FrozenHuscarl h;
        private int repath;

        HuscarlGoal(FrozenHuscarl h) {
            this.h = h;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = h.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return h.action >= 0 || canUse();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            h.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (!(h.level() instanceof ServerLevel level)) {
                return;
            }
            LivingEntity t = h.getTarget();
            if (h.action >= 0) {
                int a = h.action;
                int k = h.step();
                h.getNavigation().stop();
                if (a == MobAnims.FrozenHuscarl.CHOP && k == CHOP_HIT) {
                    level.playSound(null, h, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.HOSTILE, 1.0F, 0.6F);
                    if (t != null && t.isAlive() && h.distanceToSqr(t) <= 3.2 * 3.2 && inFront(t, 0.2)) {
                        float dmg = (float) h.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.25F;
                        if (t.hurtServer(level, h.damageSources().mobAttack(h), dmg)) {
                            chill(t, 60);
                        }
                    }
                } else if (a == MobAnims.FrozenHuscarl.BASH && k == BASH_HIT) {
                    level.playSound(null, h, SoundEvents.SHIELD_BLOCK.value(), SoundSource.HOSTILE, 1.2F, 0.5F);
                    if (t != null && t.isAlive() && h.distanceToSqr(t) <= 2.8 * 2.8 && inFront(t, 0.2)) {
                        float dmg = (float) h.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.6F;
                        if (t.hurtServer(level, h.damageSources().mobAttack(h), dmg)) {
                            Vec3 push = h.toward(t).scale(1.3);
                            t.push(push.x, 0.35, push.z);
                            t.hurtMarked = true;
                            t.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), h);
                        }
                    }
                } else if (a == MobAnims.FrozenHuscarl.CLEAVE) {
                    if (k > 0 && k < CLEAVE_HIT && k % 3 == 0) {
                        // the telegraph: rime gathering on the axe held out behind him
                        Vec3 back = h.forward().scale(-0.9);
                        Vec3 side = new Vec3(-back.z, 0, back.x);
                        Vec3 p = h.position().add(back).add(side.scale(0.6));
                        level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.2, p.z, 4, 0.2, 0.2, 0.2, 0.01);
                    }
                    if (k == CLEAVE_HIT) {
                        cleave(level);
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            // a slow turn: the shield follows the prey, but a quick player can get round it
            h.getLookControl().setLookAt(t, 8.0F, 30.0F);
            double dist = Math.sqrt(h.distanceToSqr(t));
            if (dist <= 3.5 && h.cleaveCooldown == 0 && h.random.nextInt(3) == 0) {
                h.cleaveCooldown = 140;
                h.begin(MobAnims.FrozenHuscarl.CLEAVE);
                level.playSound(null, h, SoundEvents.POWDER_SNOW_STEP, SoundSource.HOSTILE, 1.5F, 0.5F);
                return;
            }
            if (dist <= 2.2 && h.bashCooldown == 0 && h.chopCooldown > 10) {
                h.bashCooldown = 60;
                h.begin(MobAnims.FrozenHuscarl.BASH);
                return;
            }
            if (dist <= 2.8 && h.chopCooldown == 0) {
                h.chopCooldown = 40;
                h.begin(MobAnims.FrozenHuscarl.CHOP);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                h.getNavigation().moveTo(t, dist > 6.0 ? 1.15 : 0.95);
            }
        }

        private boolean inFront(LivingEntity t, double minDot) {
            Vec3 to = t.position().subtract(h.position()).multiply(1, 0, 1);
            return to.lengthSqr() < 0.5 || to.normalize().dot(h.forward()) >= minDot;
        }

        private void cleave(ServerLevel level) {
            level.playSound(null, h, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.4F, 0.6F);
            level.playSound(null, h, SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 0.8F, 1.4F);
            Vec3 fwd = h.forward();
            for (int i = -4; i <= 4; i++) {
                double a = i * 0.32;
                Vec3 d = new Vec3(fwd.x * Math.cos(a) - fwd.z * Math.sin(a), 0, fwd.x * Math.sin(a) + fwd.z * Math.cos(a));
                Vec3 p = h.position().add(d.scale(2.4));
                level.sendParticles(ParticleTypes.SNOWFLAKE, p.x, p.y + 1.0, p.z, 3, 0.2, 0.2, 0.2, 0.02);
                level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y + 1.0, p.z, 1, 0, 0, 0, 0);
            }
            float dmg = (float) h.getAttributeValue(Attributes.ATTACK_DAMAGE);
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, h.getBoundingBox().inflate(3.6, 1.0, 3.6),
                    e -> e != h && e.isAlive() && !(e instanceof FrozenHuscarl))) {
                if (h.distanceToSqr(e) > 3.8 * 3.8 || !inFront(e, -0.25)) {
                    continue;
                }
                if (e.hurtServer(level, h.damageSources().mobAttack(h), dmg)) {
                    chill(e, 140);
                    e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), h);
                    Vec3 push = h.toward(e).scale(0.6);
                    e.push(push.x, 0.2, push.z);
                    e.hurtMarked = true;
                }
            }
        }
    }
}

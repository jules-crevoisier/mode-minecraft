package com.brasshaven.entity.boss;

import com.brasshaven.boss.WayfarerBoss;
import com.brasshaven.entity.mob.ActionMonster;
import com.brasshaven.generated.MobAnims;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.Comparator;
import java.util.UUID;

/**
 * A jaguar spirit of the Strangler Fig Queen (model tools/wf/mobs/strangler_queen.py, {@code build_spirit}): a
 * see-through jade cat she drops from the sun-disc during her canopy phase. It stalks the nearest player, claws at
 * close range and pounces from mid range. Killing every spirit drops the Queen early and leaves her exposed. Its blows
 * never push outward, so it cannot shove anyone off the summit. It fades when its mistress dies, leaves or resets,
 * after 45 s, and it is never saved with the world.
 */
public class JaguarSpirit extends ActionMonster {
    public static final float WIDTH = 0.9F;
    public static final float HEIGHT = 1.1F;
    private static final int LIFE = 900;
    private static final int CLAW_HIT = 8;          // 0.4 s in the claw animation
    private static final int POUNCE_LEAP = 10;      // 0.5 s in the pounce animation
    private static final int POUNCE_END = 20;

    private @Nullable UUID owner;
    private int life = LIFE;
    private int clawCooldown = 20;
    private int pounceCooldown = 40;
    private boolean pounceHit;
    private float lockedYaw;

    public JaguarSpirit(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 0;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 22.0)
                .add(Attributes.ATTACK_DAMAGE, 6.0)
                .add(Attributes.MOVEMENT_SPEED, 0.34)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.4)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.2);
    }

    public void setOwner(WayfarerBoss boss) {
        this.owner = boss.getUUID();
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.JaguarSpirit.TICKS;
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    public boolean causeFallDamage(double fallDistance, float damageModifier, DamageSource source) {
        return false;
    }

    @Override
    protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean killedByPlayer) {}

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        Entity by = source.getEntity();
        if (by instanceof WayfarerBoss || by instanceof JaguarSpirit || (by != null && by.entityTags().contains(WayfarerBoss.MINION_TAG))) {
            return false;
        }
        return super.hurtServer(level, source, amount);
    }

    @Override
    public void die(DamageSource source) {
        if (level() instanceof ServerLevel level) {
            burst(level);
        }
        super.die(source);
    }

    private void burst(ServerLevel level) {
        level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 0.6, getZ(), 20, 0.5, 0.5, 0.5, 0.1);
        level.sendParticles(ParticleTypes.FALLING_SPORE_BLOSSOM, getX(), getY() + 1.0, getZ(), 12, 0.5, 0.5, 0.5, 0.0);
        level.playSound(null, this, SoundEvents.OCELOT_HURT, SoundSource.HOSTILE, 1.5F, 0.6F);
    }

    /** Fades without a death: its mistress is gone or its time is up. */
    public void fade(ServerLevel level) {
        burst(level);
        discard();
    }

    private @Nullable Player nearest(ServerLevel level) {
        return level.getEntitiesOfClass(Player.class, new AABB(blockPosition()).inflate(32, 12, 32),
                        p -> p.isAlive() && !p.isCreative() && !p.isSpectator())
                .stream().min(Comparator.comparingDouble(this::distanceToSqr)).orElse(null);
    }

    private Vec3 forward() {
        float yaw = lockedYaw * Mth.DEG_TO_RAD;
        return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
    }

    private void face(LivingEntity t) {
        float yaw = (float) (Mth.atan2(t.getZ() - getZ(), t.getX() - getX()) * (180.0 / Math.PI)) - 90.0F;
        lockedYaw = yaw;
        setYRot(yaw);
        yBodyRot = yaw;
        yHeadRot = yaw;
    }

    private void hold() {
        setYRot(lockedYaw);
        yBodyRot = lockedYaw;
        yHeadRot = lockedYaw;
        getNavigation().stop();
    }

    /** Hits players in front within ``reach``; no outward push, only a small hop. */
    private boolean claw(ServerLevel level, double reach, double cosHalf, float dmg) {
        boolean any = false;
        Vec3 fwd = forward();
        for (Player p : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(reach + 1, 2, reach + 1),
                p -> p.isAlive() && !p.isCreative() && !p.isSpectator())) {
            Vec3 to = p.position().subtract(position()).multiply(1, 0, 1);
            double d = to.length();
            if (d > reach + p.getBbWidth() / 2 || (d > 0.8 && to.normalize().dot(fwd) < cosHalf)) {
                continue;
            }
            if (p.hurtServer(level, damageSources().mobAttack(this), dmg)) {
                any = true;
                p.setDeltaMovement(p.getDeltaMovement().multiply(0.4, 1, 0.4));
                p.hurtMarked = true;
            }
        }
        return any;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        Entity mistress = owner == null ? null : level.getEntity(owner);
        if (--life <= 0 || !(mistress instanceof StranglerQueen queen) || !queen.isAlive() || queen.phase() < 2) {
            fade(level);
            return;
        }
        if (tickCount % 5 == 0) {
            level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + 0.5, getZ(), 1, 0.3, 0.3, 0.3, 0.0);
        }
        Player t = nearest(level);
        if (t != null) {
            setTarget(t);
        }
        if (clawCooldown > 0) {
            clawCooldown--;
        }
        if (pounceCooldown > 0) {
            pounceCooldown--;
        }
        float dmg = (float) getAttributeValue(Attributes.ATTACK_DAMAGE);
        int k = step();
        if (k >= 0) {
            if (action == MobAnims.JaguarSpirit.CLAW) {
                hold();
                if (k == CLAW_HIT) {
                    claw(level, 2.6, Math.cos(Math.toRadians(70)), dmg);
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.0F, 1.4F);
                }
            } else if (action == MobAnims.JaguarSpirit.POUNCE) {
                if (k < POUNCE_LEAP) {
                    hold();
                    if (t != null && k < POUNCE_LEAP - 3) {
                        face(t);
                    }
                    if (k % 2 == 0) {
                        Vec3 p = position().add(forward().scale(1.5));
                        level.sendParticles(ParticleTypes.HAPPY_VILLAGER, p.x, getY() + 0.2, p.z, 2, 0.3, 0.05, 0.3, 0);
                    }
                } else if (k == POUNCE_LEAP) {
                    double dist = t == null ? 6 : Math.min(9, distanceTo(t));
                    Vec3 v = forward().scale(0.22 * dist);
                    setDeltaMovement(v.x, 0.42, v.z);
                    hurtMarked = true;
                    pounceHit = false;
                    level.playSound(null, this, SoundEvents.OCELOT_AMBIENT, SoundSource.HOSTILE, 1.5F, 0.5F);
                } else if (k <= POUNCE_END && !pounceHit) {
                    if (claw(level, 1.6, -1, dmg + 2)) {
                        pounceHit = true;
                        setDeltaMovement(getDeltaMovement().multiply(0.2, 1, 0.2));
                    }
                }
            }
            return;
        }
        if (t == null) {
            getNavigation().stop();
            return;
        }
        double dist = distanceTo(t);
        if (dist <= 2.8 && clawCooldown == 0) {
            face(t);
            clawCooldown = 22 + random.nextInt(14);
            begin(MobAnims.JaguarSpirit.CLAW);
            return;
        }
        if (dist >= 4 && dist <= 9 && pounceCooldown == 0 && onGround()) {
            face(t);
            pounceCooldown = 80 + random.nextInt(40);
            begin(MobAnims.JaguarSpirit.POUNCE);
            return;
        }
        getLookControl().setLookAt(t, 30.0F, 30.0F);
        if (tickCount % 5 == 0) {
            getNavigation().moveTo(t, 1.0);
        }
    }
}

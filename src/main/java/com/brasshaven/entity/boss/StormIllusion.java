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
 * A mirror image of the Storm Ascetic (model tools/wf/mobs/storm_ascetic.py, {@code build_illusion}): a pale, slightly
 * see-through copy of him that walks at the players and swings the same staff combo (weaker), or calls a single bolt
 * of lightning on a marked spot. Any blow pops it in a gust of wind. It fades after 16 s, when its master dies or
 * leaves, and it is never saved with the world.
 */
public class StormIllusion extends ActionMonster {
    public static final float WIDTH = 1.4F;
    public static final float HEIGHT = 4.4F;
    private static final int LIFE = 320;
    private static final int STAFF_HIT = 14;        // 0.7 s in the staff animation
    private static final int THRUST_HIT = 24;       // 1.2 s
    private static final int BOLT_HIT = 22;         // 1.1 s in the lightning animation

    private @Nullable UUID owner;
    private int life = LIFE;
    private int staffCooldown = 30;
    private int boltCooldown = 60;
    private float lockedYaw;
    private @Nullable Vec3 boltAt;

    public StormIllusion(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 0;
    }

    public static AttributeSupplier.Builder attributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 1.0)
                .add(Attributes.ATTACK_DAMAGE, 8.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 40.0)
                .add(Attributes.STEP_HEIGHT, 1.2);
    }

    public void setOwner(WayfarerBoss boss) {
        this.owner = boss.getUUID();
    }

    @Override
    public int[] actionTicks() {
        return MobAnims.StormIllusion.TICKS;
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

    /** Any blow but its master's side pops it. */
    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        Entity by = source.getEntity();
        if (by instanceof WayfarerBoss || by instanceof StormIllusion || (by != null && by.entityTags().contains(WayfarerBoss.MINION_TAG))) {
            return false;
        }
        pop(level);
        return true;
    }

    public void pop(ServerLevel level) {
        level.sendParticles(ParticleTypes.GUST, getX(), getY() + 2.0, getZ(), 3, 0.6, 1.0, 0.6, 0.0);
        level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 2.0, getZ(), 40, 0.6, 1.4, 0.6, 0.06);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + 2.0, getZ(), 20, 0.6, 1.4, 0.6, 0.2);
        level.playSound(null, this, SoundEvents.ILLUSIONER_MIRROR_MOVE, SoundSource.HOSTILE, 2.0F, 1.2F);
        level.playSound(null, this, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.HOSTILE, 1.5F, 1.0F);
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

    private void hurtPlayers(ServerLevel level, Vec3 c, double reach, double cosHalf, double lineHalf, float dmg) {
        Vec3 fwd = forward();
        for (Player p : level.getEntitiesOfClass(Player.class, new AABB(c, c).inflate(reach + 1, 4, reach + 1),
                p -> p.isAlive() && !p.isCreative() && !p.isSpectator())) {
            Vec3 to = p.position().subtract(c).multiply(1, 0, 1);
            double d = to.length();
            boolean in;
            if (lineHalf > 0) {
                double along = to.dot(fwd);
                in = along >= 0 && along <= reach && to.subtract(fwd.scale(along)).length() <= lineHalf + p.getBbWidth() / 2;
            } else {
                in = d <= reach + p.getBbWidth() / 2 && (d < 1.0 || to.normalize().dot(fwd) >= cosHalf);
            }
            if (in && p.hurtServer(level, damageSources().mobAttack(this), dmg) && d > 0.1) {
                Vec3 push = to.normalize().scale(0.35);
                p.push(push.x, 0.15, push.z);
                p.hurtMarked = true;
            }
        }
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        Entity master = owner == null ? null : level.getEntity(owner);
        if (--life <= 0 || !(master instanceof StormAscetic boss) || !boss.isAlive() || boss.phase() != 2) {
            pop(level);
            return;
        }
        if (tickCount % 4 == 0) {
            level.sendParticles(ParticleTypes.SMALL_GUST, getX(), getY() + 0.3, getZ(), 1, 0.5, 0.1, 0.5, 0.0);
        }
        Player t = nearest(level);
        if (t != null) {
            setTarget(t);
        }
        if (staffCooldown > 0) {
            staffCooldown--;
        }
        if (boltCooldown > 0) {
            boltCooldown--;
        }
        int k = step();
        if (k >= 0) {
            hold();
            if (action == MobAnims.StormIllusion.STAFF) {
                if (k < STAFF_HIT && k % 3 == 0) {
                    arcDust(level, 6.0, 60);
                } else if (k == STAFF_HIT) {
                    hurtPlayers(level, position(), 6.0, Math.cos(Math.toRadians(60)), 0, 8.0F);
                    level.playSound(null, this, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 1.5F, 0.8F);
                } else if (k > STAFF_HIT && k < THRUST_HIT && k % 2 == 0) {
                    for (double d = 1; d <= 7.5; d += 1) {
                        Vec3 p = position().add(forward().scale(d));
                        level.sendParticles(ParticleTypes.SMALL_GUST, p.x, getY() + 0.15, p.z, 1, 0, 0, 0, 0);
                    }
                } else if (k == THRUST_HIT) {
                    hurtPlayers(level, position(), 7.5, 0, 0.9, 7.0F);
                    level.playSound(null, this, SoundEvents.TRIDENT_THROW.value(), SoundSource.HOSTILE, 1.5F, 0.8F);
                }
            } else if (action == MobAnims.StormIllusion.LIGHTNING) {
                if (k < 12 && t != null) {
                    boltAt = t.position();
                }
                if (boltAt != null && k < BOLT_HIT && k % 2 == 0) {
                    telegraph(level, boltAt, 1.6);
                }
                if (k == BOLT_HIT && boltAt != null) {
                    StormAscetic.bolt(level, this, boltAt, 1.6, 9.0F);
                    boltAt = null;
                }
            }
            return;
        }
        if (t == null) {
            getNavigation().stop();
            return;
        }
        double dist = distanceTo(t);
        if (dist <= 5.5 && staffCooldown == 0) {
            face(t);
            staffCooldown = 70 + random.nextInt(30);
            begin(MobAnims.StormIllusion.STAFF);
            return;
        }
        if (dist > 7 && dist < 22 && boltCooldown == 0) {
            face(t);
            boltCooldown = 120 + random.nextInt(40);
            begin(MobAnims.StormIllusion.LIGHTNING);
            return;
        }
        getLookControl().setLookAt(t, 30.0F, 30.0F);
        if (tickCount % 5 == 0) {
            getNavigation().moveTo(t, 1.0);
        }
    }

    private void arcDust(ServerLevel level, double range, double half) {
        for (double a = -half; a <= half; a += 12) {
            float yaw = (float) (lockedYaw + a) * Mth.DEG_TO_RAD;
            Vec3 p = position().add(new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw)).scale(range));
            level.sendParticles(ParticleTypes.CLOUD, p.x, p.y + 0.15, p.z, 1, 0, 0, 0, 0);
        }
    }

    private static void telegraph(ServerLevel level, Vec3 c, double r) {
        int n = Math.max(12, (int) (r * 7));
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / n;
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x + Math.cos(a) * r, c.y + 0.15, c.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
    }
}

package com.brasshaven.boss;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import org.jetbrains.annotations.Nullable;

/**
 * One boss move, Elden Ring style: a readable wind-up (the telegraph), a short active window where it hurts,
 * then a recovery where the boss is open to punishment.
 *
 * <pre>
 * BossAttack.of("slam").anim(MobAnims.X.SLAM).timing(21, 3, 18).range(0, 6).cooldown(80)
 *         .windup((boss, level, target, t) -> boss.telegraphRing(boss.ahead(3), 4.5, ...))
 *         .impact((boss, level, target, t) -> boss.hitCircle(boss.ahead(3), 4.5, 16, 1.2, 0.4))
 *         .build();
 * </pre>
 */
public final class BossAttack {
    /** Called with the tick counted from the start of the current stage. */
    @FunctionalInterface
    public interface Step {
        void run(WayfarerBoss boss, ServerLevel level, @Nullable LivingEntity target, int tick);
    }

    private static final Step NOTHING = (boss, level, target, tick) -> {};

    public final String name;
    public final int anim;
    public final int windup;
    public final int active;
    public final int recovery;
    public final double minRange;
    public final double maxRange;
    public final int cooldown;
    public final int weight;
    public final int phases;
    public final boolean track;
    final Step onStart;
    final Step onWindup;
    final Step onImpact;
    final Step onActive;
    final Step onEnd;

    private BossAttack(Builder b) {
        this.name = b.name;
        this.anim = b.anim;
        this.windup = b.windup;
        this.active = b.active;
        this.recovery = b.recovery;
        this.minRange = b.minRange;
        this.maxRange = b.maxRange;
        this.cooldown = b.cooldown;
        this.weight = b.weight;
        this.phases = b.phases;
        this.track = b.track;
        this.onStart = b.onStart;
        this.onWindup = b.onWindup;
        this.onImpact = b.onImpact;
        this.onActive = b.onActive;
        this.onEnd = b.onEnd;
    }

    public int length() {
        return windup + active + recovery;
    }

    public boolean allowedIn(int phase) {
        return (phases & (1 << (phase - 1))) != 0;
    }

    public static Builder of(String name) {
        return new Builder(name);
    }

    public static final class Builder {
        private final String name;
        private int anim = -1;
        private int windup = 15;
        private int active = 3;
        private int recovery = 12;
        private double minRange;
        private double maxRange = 4.0;
        private int cooldown = 40;
        private int weight = 10;
        private int phases = 0b11;
        private boolean track = true;
        private Step onStart = NOTHING;
        private Step onWindup = NOTHING;
        private Step onImpact = NOTHING;
        private Step onActive = NOTHING;
        private Step onEnd = NOTHING;

        private Builder(String name) {
            this.name = name;
        }

        /** Action animation index (generated MobAnims constant), or -1 for none. */
        public Builder anim(int anim) {
            this.anim = anim;
            return this;
        }

        /** Wind-up ticks (telegraph), active ticks (hurts), recovery ticks (punish window). */
        public Builder timing(int windup, int active, int recovery) {
            this.windup = windup;
            this.active = active;
            this.recovery = recovery;
            return this;
        }

        /** Distance to the target (blocks) at which the boss may start this move. */
        public Builder range(double min, double max) {
            this.minRange = min;
            this.maxRange = max;
            return this;
        }

        public Builder cooldown(int ticks) {
            this.cooldown = ticks;
            return this;
        }

        public Builder weight(int weight) {
            this.weight = weight;
            return this;
        }

        /** Only in phase 1. */
        public Builder phaseOne() {
            this.phases = 0b01;
            return this;
        }

        /** Only in phase 2. */
        public Builder phaseTwo() {
            this.phases = 0b10;
            return this;
        }

        /** Keep turning toward the target during the wind-up (default true); the direction locks on impact. */
        public Builder track(boolean track) {
            this.track = track;
            return this;
        }

        public Builder start(Step step) {
            this.onStart = step;
            return this;
        }

        public Builder windup(Step step) {
            this.onWindup = step;
            return this;
        }

        public Builder impact(Step step) {
            this.onImpact = step;
            return this;
        }

        public Builder active(Step step) {
            this.onActive = step;
            return this;
        }

        public Builder end(Step step) {
            this.onEnd = step;
            return this;
        }

        public BossAttack build() {
            return new BossAttack(this);
        }
    }
}

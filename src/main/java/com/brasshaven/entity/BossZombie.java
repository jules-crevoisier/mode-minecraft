package com.brasshaven.entity;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.UUID;

/** Boss bar, three health phases, persistence and a defeat hook shared by both bosses. */
public abstract class BossZombie extends WayfarerZombie {
    protected final ServerBossEvent bossBar;
    private int phase = 1;

    protected BossZombie(EntityType<? extends Zombie> type, Level level, BossEvent.BossBarColor color) {
        super(type, level);
        this.bossBar = new ServerBossEvent(UUID.randomUUID(), getDisplayName(), color, BossEvent.BossBarOverlay.NOTCHED_10);
        bossBar.setDarkenScreen(true);
        setPersistenceRequired();
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bossBar.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossBar.removePlayer(player);
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        bossBar.setName(getDisplayName());
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        float ratio = getHealth() / getMaxHealth();
        bossBar.setProgress(ratio);
        int newPhase = ratio > 0.66F ? 1 : ratio > 0.33F ? 2 : 3;
        if (newPhase != phase) {
            phase = newPhase;
            onPhaseChange(level, phase);
        }
        bossTick(level, phase);
    }

    protected abstract void bossTick(ServerLevel level, int phase);

    protected void onPhaseChange(ServerLevel level, int phase) {}

    protected abstract void onDefeated(ServerLevel level);

    protected List<Player> nearbyPlayers(ServerLevel level, double radius) {
        return level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(radius),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        if (level() instanceof ServerLevel level) {
            bossBar.removeAllPlayers();
            onDefeated(level);
            level.getServer().getPlayerList().broadcastSystemMessage(
                    Component.translatable("message.brasshaven.boss.defeated", getDisplayName()).withStyle(ChatFormatting.GOLD), false);
        }
    }
}

package com.brasshaven.entity;

import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import org.jetbrains.annotations.Nullable;

/**
 * Base for the mod's humanoid creatures: reuses the zombie AI (melee, door breaking,
 * target selection) but never spawns as a baby, never drowns into another mob and
 * only burns in daylight when the subclass says so.
 */
public abstract class WayfarerZombie extends Zombie {
    protected WayfarerZombie(EntityType<? extends Zombie> type, Level level) {
        super(type, level);
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                  EntitySpawnReason reason, @Nullable SpawnGroupData data) {
        SpawnGroupData result = super.finalizeSpawn(level, difficulty, reason, data);
        setBaby(false);
        return result;
    }

    /** Zombies may call copies of themselves as reinforcements: never for bosses and custom mobs. */
    @Override
    protected void handleAttributes(float difficultyModifier, EntitySpawnReason spawnReason) {
        super.handleAttributes(difficultyModifier, spawnReason);
        AttributeInstance reinforcements = getAttribute(Attributes.SPAWN_REINFORCEMENTS_CHANCE);
        if (reinforcements != null) {
            reinforcements.removeModifiers();
            reinforcements.setBaseValue(0.0);
        }
    }

    @Override
    protected boolean convertsInWater() {
        return false;
    }

    @Override
    protected boolean isSunSensitive() {
        return false;
    }
}

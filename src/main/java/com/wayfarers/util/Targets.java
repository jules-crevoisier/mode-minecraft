package com.wayfarers.util;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.allay.Allay;
import net.minecraft.world.entity.animal.equine.AbstractHorse;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.animal.golem.SnowGolem;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;

/** Who area abilities, spells and boss weapons may hit: monsters yes; players, pets, villagers, golems and farm animals no. */
public final class Targets {
    private Targets() {}

    public static boolean friendly(Entity e) {
        return e instanceof Player || e instanceof ArmorStand || e instanceof AbstractVillager || e instanceof IronGolem
                || e instanceof SnowGolem || e instanceof Allay || e instanceof com.wayfarers.entity.WayfarerNpc
                || (e instanceof OwnableEntity owned && owned.getOwnerReference() != null)
                || (e instanceof AbstractHorse horse && horse.isTamed());
    }

    /** A living creature the player's abilities should hurt. */
    public static boolean foe(Player player, Entity e) {
        return e != player && e.isAlive() && e instanceof LivingEntity && !friendly(e)
                && !(e instanceof Animal && !(e instanceof Enemy));
    }
}

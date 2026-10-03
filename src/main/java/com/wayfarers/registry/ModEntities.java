package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.entity.BasaltGuard;
import com.wayfarers.entity.BoomerangEntity;
import com.wayfarers.entity.DrownedWarden;
import com.wayfarers.entity.MapWraith;
import com.wayfarers.entity.RuinWalker;
import com.wayfarers.entity.VoidStalker;
import com.wayfarers.entity.VoidWarden;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.SpawnPlacementRegisterEvent;

import java.util.List;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, Wayfarers.MODID);

    public static final RegistryObject<EntityType<RuinWalker>> RUIN_WALKER = ENTITIES.register("ruin_walker",
            () -> EntityType.Builder.<RuinWalker>of(RuinWalker::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8).build(ENTITIES.key("ruin_walker")));
    public static final RegistryObject<EntityType<MapWraith>> MAP_WRAITH = ENTITIES.register("map_wraith",
            () -> EntityType.Builder.<MapWraith>of(MapWraith::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8).build(ENTITIES.key("map_wraith")));
    public static final RegistryObject<EntityType<BasaltGuard>> BASALT_GUARD = ENTITIES.register("basalt_guard",
            () -> EntityType.Builder.<BasaltGuard>of(BasaltGuard::new, MobCategory.MONSTER)
                    .sized(0.7F, 2.4F).fireImmune().clientTrackingRange(8).build(ENTITIES.key("basalt_guard")));
    public static final RegistryObject<EntityType<VoidStalker>> VOID_STALKER = ENTITIES.register("void_stalker",
            () -> EntityType.Builder.<VoidStalker>of(VoidStalker::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8).build(ENTITIES.key("void_stalker")));
    public static final RegistryObject<EntityType<DrownedWarden>> DROWNED_WARDEN = ENTITIES.register("drowned_warden",
            () -> EntityType.Builder.<DrownedWarden>of(DrownedWarden::new, MobCategory.MONSTER)
                    .sized(1.6F, 4.2F).clientTrackingRange(10).build(ENTITIES.key("drowned_warden")));
    public static final RegistryObject<EntityType<VoidWarden>> VOID_WARDEN = ENTITIES.register("void_warden",
            () -> EntityType.Builder.<VoidWarden>of(VoidWarden::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).fireImmune().clientTrackingRange(10).build(ENTITIES.key("void_warden")));
    public static final RegistryObject<EntityType<BoomerangEntity>> BOOMERANG = ENTITIES.register("boomerang",
            () -> EntityType.Builder.<BoomerangEntity>of(BoomerangEntity::new, MobCategory.MISC)
                    .sized(0.4F, 0.4F).clientTrackingRange(6).updateInterval(2).build(ENTITIES.key("boomerang")));

    public static void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(RUIN_WALKER.get(), RuinWalker.attributes().build());
        event.put(MAP_WRAITH.get(), MapWraith.attributes().build());
        event.put(BASALT_GUARD.get(), BasaltGuard.attributes().build());
        event.put(VOID_STALKER.get(), VoidStalker.attributes().build());
        event.put(DROWNED_WARDEN.get(), DrownedWarden.attributes().build());
        event.put(VOID_WARDEN.get(), VoidWarden.attributes().build());
    }

    /** Natural/structure spawning rules: on the ground, in the dark, like vanilla monsters. */
    public static void registerSpawnPlacements(SpawnPlacementRegisterEvent event) {
        for (EntityType<? extends Monster> type : List.of(RUIN_WALKER.get(), MAP_WRAITH.get(), BASALT_GUARD.get(), VOID_STALKER.get())) {
            register(event, type);
        }
    }

    private static <T extends Monster> void register(SpawnPlacementRegisterEvent event, EntityType<T> type) {
        event.register(type, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkMonsterSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }

    private ModEntities() {}
}

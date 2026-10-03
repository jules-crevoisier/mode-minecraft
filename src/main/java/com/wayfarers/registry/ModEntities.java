package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.entity.BasaltGuard;
import com.wayfarers.entity.BoomerangEntity;
import com.wayfarers.entity.DrownedWarden;
import com.wayfarers.entity.MapWraith;
import com.wayfarers.entity.RuinWalker;
import com.wayfarers.entity.VoidStalker;
import com.wayfarers.entity.VoidWarden;
import com.wayfarers.entity.boss.BellKeeper;
import com.wayfarers.entity.boss.Archivist;
import com.wayfarers.entity.boss.SandPharaoh;
import com.wayfarers.entity.boss.JadeJaguar;
import com.wayfarers.entity.boss.RootMother;
import com.wayfarers.entity.boss.SwampCrone;
import com.wayfarers.entity.boss.GryphonKnight;
import com.wayfarers.entity.boss.RuneColossus;
import com.wayfarers.entity.boss.ForgeKing;
import com.wayfarers.entity.boss.CrystalSpider;
import com.wayfarers.entity.boss.SculkSpawn;
import com.wayfarers.entity.boss.AshLord;
import com.wayfarers.entity.boss.PiglinKing;
import com.wayfarers.entity.boss.SoulReaper;
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
                    .sized(VoidWarden.WIDTH, VoidWarden.HEIGHT).fireImmune().clientTrackingRange(10).build(ENTITIES.key("void_warden")));
    // ---- bosses (one per great structure)
    public static final RegistryObject<EntityType<BellKeeper>> BELL_KEEPER = ENTITIES.register("bell_keeper",
            () -> EntityType.Builder.<BellKeeper>of(BellKeeper::new, MobCategory.MONSTER)
                    .sized(BellKeeper.WIDTH, BellKeeper.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("bell_keeper")));
    public static final RegistryObject<EntityType<Archivist>> ARCHIVIST = ENTITIES.register("archivist",
            () -> EntityType.Builder.<Archivist>of(Archivist::new, MobCategory.MONSTER)
                    .sized(Archivist.WIDTH, Archivist.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("archivist")));
    public static final RegistryObject<EntityType<SandPharaoh>> SAND_PHARAOH = ENTITIES.register("sand_pharaoh",
            () -> EntityType.Builder.<SandPharaoh>of(SandPharaoh::new, MobCategory.MONSTER)
                    .sized(SandPharaoh.WIDTH, SandPharaoh.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("sand_pharaoh")));
    public static final RegistryObject<EntityType<JadeJaguar>> JADE_JAGUAR = ENTITIES.register("jade_jaguar",
            () -> EntityType.Builder.<JadeJaguar>of(JadeJaguar::new, MobCategory.MONSTER)
                    .sized(JadeJaguar.WIDTH, JadeJaguar.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("jade_jaguar")));
    public static final RegistryObject<EntityType<RootMother>> ROOT_MOTHER = ENTITIES.register("root_mother",
            () -> EntityType.Builder.<RootMother>of(RootMother::new, MobCategory.MONSTER)
                    .sized(RootMother.WIDTH, RootMother.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("root_mother")));
    public static final RegistryObject<EntityType<SwampCrone>> SWAMP_CRONE = ENTITIES.register("swamp_crone",
            () -> EntityType.Builder.<SwampCrone>of(SwampCrone::new, MobCategory.MONSTER)
                    .sized(SwampCrone.WIDTH, SwampCrone.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("swamp_crone")));
    public static final RegistryObject<EntityType<GryphonKnight>> GRYPHON_KNIGHT = ENTITIES.register("gryphon_knight",
            () -> EntityType.Builder.<GryphonKnight>of(GryphonKnight::new, MobCategory.MONSTER)
                    .sized(GryphonKnight.WIDTH, GryphonKnight.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("gryphon_knight")));
    public static final RegistryObject<EntityType<RuneColossus>> RUNE_COLOSSUS = ENTITIES.register("rune_colossus",
            () -> EntityType.Builder.<RuneColossus>of(RuneColossus::new, MobCategory.MONSTER)
                    .sized(RuneColossus.WIDTH, RuneColossus.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("rune_colossus")));
    public static final RegistryObject<EntityType<ForgeKing>> FORGE_KING = ENTITIES.register("forge_king",
            () -> EntityType.Builder.<ForgeKing>of(ForgeKing::new, MobCategory.MONSTER)
                    .sized(ForgeKing.WIDTH, ForgeKing.HEIGHT).fireImmune().clientTrackingRange(10).build(ENTITIES.key("forge_king")));
    public static final RegistryObject<EntityType<CrystalSpider>> CRYSTAL_SPIDER = ENTITIES.register("crystal_spider",
            () -> EntityType.Builder.<CrystalSpider>of(CrystalSpider::new, MobCategory.MONSTER)
                    .sized(CrystalSpider.WIDTH, CrystalSpider.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("crystal_spider")));
    public static final RegistryObject<EntityType<SculkSpawn>> SCULK_SPAWN = ENTITIES.register("sculk_spawn",
            () -> EntityType.Builder.<SculkSpawn>of(SculkSpawn::new, MobCategory.MONSTER)
                    .sized(SculkSpawn.WIDTH, SculkSpawn.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("sculk_spawn")));
    public static final RegistryObject<EntityType<AshLord>> ASH_LORD = ENTITIES.register("ash_lord",
            () -> EntityType.Builder.<AshLord>of(AshLord::new, MobCategory.MONSTER)
                    .sized(AshLord.WIDTH, AshLord.HEIGHT).fireImmune().clientTrackingRange(10).build(ENTITIES.key("ash_lord")));
    public static final RegistryObject<EntityType<PiglinKing>> PIGLIN_KING = ENTITIES.register("piglin_king",
            () -> EntityType.Builder.<PiglinKing>of(PiglinKing::new, MobCategory.MONSTER)
                    .sized(PiglinKing.WIDTH, PiglinKing.HEIGHT).fireImmune().clientTrackingRange(10).build(ENTITIES.key("piglin_king")));
    public static final RegistryObject<EntityType<SoulReaper>> SOUL_REAPER = ENTITIES.register("soul_reaper",
            () -> EntityType.Builder.<SoulReaper>of(SoulReaper::new, MobCategory.MONSTER)
                    .sized(SoulReaper.WIDTH, SoulReaper.HEIGHT).fireImmune().clientTrackingRange(10).build(ENTITIES.key("soul_reaper")));
    public static final RegistryObject<EntityType<BoomerangEntity>> BOOMERANG = ENTITIES.register("boomerang",
            () -> EntityType.Builder.<BoomerangEntity>of(BoomerangEntity::new, MobCategory.MISC)
                    .sized(0.4F, 0.4F).clientTrackingRange(6).updateInterval(2).build(ENTITIES.key("boomerang")));

    /** Every boss with an Elden Ring style fight (demo command, quests). */
    public static List<RegistryObject<? extends EntityType<? extends com.wayfarers.boss.WayfarerBoss>>> bosses() {
        return List.of(DROWNED_WARDEN, BELL_KEEPER, ARCHIVIST, SAND_PHARAOH, JADE_JAGUAR, ROOT_MOTHER, SWAMP_CRONE, GRYPHON_KNIGHT, RUNE_COLOSSUS, FORGE_KING, CRYSTAL_SPIDER, SCULK_SPAWN, ASH_LORD, PIGLIN_KING, SOUL_REAPER);
    }

    public static void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(RUIN_WALKER.get(), RuinWalker.attributes().build());
        event.put(MAP_WRAITH.get(), MapWraith.attributes().build());
        event.put(BASALT_GUARD.get(), BasaltGuard.attributes().build());
        event.put(VOID_STALKER.get(), VoidStalker.attributes().build());
        event.put(DROWNED_WARDEN.get(), DrownedWarden.attributes().build());
        event.put(VOID_WARDEN.get(), VoidWarden.attributes().build());
        event.put(BELL_KEEPER.get(), BellKeeper.attributes().build());
        event.put(ARCHIVIST.get(), Archivist.attributes().build());
        event.put(SAND_PHARAOH.get(), SandPharaoh.attributes().build());
        event.put(JADE_JAGUAR.get(), JadeJaguar.attributes().build());
        event.put(ROOT_MOTHER.get(), RootMother.attributes().build());
        event.put(SWAMP_CRONE.get(), SwampCrone.attributes().build());
        event.put(GRYPHON_KNIGHT.get(), GryphonKnight.attributes().build());
        event.put(RUNE_COLOSSUS.get(), RuneColossus.attributes().build());
        event.put(FORGE_KING.get(), ForgeKing.attributes().build());
        event.put(CRYSTAL_SPIDER.get(), CrystalSpider.attributes().build());
        event.put(SCULK_SPAWN.get(), SculkSpawn.attributes().build());
        event.put(ASH_LORD.get(), AshLord.attributes().build());
        event.put(PIGLIN_KING.get(), PiglinKing.attributes().build());
        event.put(SOUL_REAPER.get(), SoulReaper.attributes().build());
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

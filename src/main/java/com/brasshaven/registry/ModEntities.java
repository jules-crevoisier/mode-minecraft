package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.entity.BasaltGuard;
import com.brasshaven.entity.BoomerangEntity;
import com.brasshaven.entity.DrownedWarden;
import com.brasshaven.entity.MapWraith;
import com.brasshaven.entity.RuinWalker;
import com.brasshaven.entity.VoidStalker;
import com.brasshaven.entity.VoidWarden;
import com.brasshaven.entity.mob.SkeletonKnight;
import com.brasshaven.entity.mob.CryptCrawler;
import com.brasshaven.entity.mob.Banshee;
import com.brasshaven.entity.mob.Gargoyle;
import com.brasshaven.entity.mob.EmberImp;
import com.brasshaven.entity.mob.VoidLarva;
import com.brasshaven.entity.boss.GraveKnight;
import com.brasshaven.entity.boss.BoneMatriarch;
import com.brasshaven.entity.boss.WeepingLady;
import com.brasshaven.entity.boss.LarvaMother;
import com.brasshaven.entity.boss.BellKeeper;
import com.brasshaven.entity.boss.Archivist;
import com.brasshaven.entity.boss.SandPharaoh;
import com.brasshaven.entity.boss.JadeJaguar;
import com.brasshaven.entity.boss.RootMother;
import com.brasshaven.entity.boss.SwampCrone;
import com.brasshaven.entity.boss.GryphonKnight;
import com.brasshaven.entity.boss.RuneColossus;
import com.brasshaven.entity.boss.ForgeKing;
import com.brasshaven.entity.boss.CrystalSpider;
import com.brasshaven.entity.boss.SculkSpawn;
import com.brasshaven.entity.boss.AshLord;
import com.brasshaven.entity.boss.PiglinKing;
import com.brasshaven.entity.boss.SoulReaper;
import com.brasshaven.entity.boss.GrandClockmaker;
import com.brasshaven.entity.automaton.BrassGolem;
import com.brasshaven.entity.automaton.ClockworkSpider;
import com.brasshaven.entity.automaton.HotRivetEntity;
import com.brasshaven.entity.automaton.SteamDrone;
import com.brasshaven.entity.ocean.GlowJellyfish;
import com.brasshaven.entity.ocean.MantaRay;
import com.brasshaven.entity.ocean.ReefFish;
import com.brasshaven.entity.ocean.SeaSerpent;
import com.brasshaven.entity.ocean.Whale;
import com.brasshaven.entity.folk.ClockworkCitizen;
import com.brasshaven.entity.folk.Dwarf;
import com.brasshaven.entity.folk.Monk;
import com.brasshaven.entity.folk.Sylvan;
import com.brasshaven.entity.mob.BanditMarksman;
import com.brasshaven.entity.mob.BarnacleCrab;
import com.brasshaven.entity.mob.CinderHound;
import com.brasshaven.entity.mob.LanternWisp;
import com.brasshaven.entity.mob.RiftSentinel;
import com.brasshaven.entity.mob.SkyRaider;
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
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, Brasshaven.MODID);

    public static final RegistryObject<EntityType<RuinWalker>> RUIN_WALKER = ENTITIES.register("ruin_walker",
            () -> EntityType.Builder.<RuinWalker>of(RuinWalker::new, MobCategory.MONSTER)
                    .sized(0.98F, 2.3F).clientTrackingRange(8).build(ENTITIES.key("ruin_walker")));
    public static final RegistryObject<EntityType<MapWraith>> MAP_WRAITH = ENTITIES.register("map_wraith",
            () -> EntityType.Builder.<MapWraith>of(MapWraith::new, MobCategory.MONSTER)
                    .sized(0.7F, 1.9F).clientTrackingRange(8).build(ENTITIES.key("map_wraith")));
    public static final RegistryObject<EntityType<BasaltGuard>> BASALT_GUARD = ENTITIES.register("basalt_guard",
            () -> EntityType.Builder.<BasaltGuard>of(BasaltGuard::new, MobCategory.MONSTER)
                    .sized(0.9F, 2.6F).fireImmune().clientTrackingRange(8).build(ENTITIES.key("basalt_guard")));
    public static final RegistryObject<EntityType<VoidStalker>> VOID_STALKER = ENTITIES.register("void_stalker",
            () -> EntityType.Builder.<VoidStalker>of(VoidStalker::new, MobCategory.MONSTER)
                    .sized(0.7F, 2.7F).clientTrackingRange(8).build(ENTITIES.key("void_stalker")));
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
    // ---- dungeon creatures
    public static final RegistryObject<EntityType<SkeletonKnight>> SKELETON_KNIGHT = ENTITIES.register("skeleton_knight",
            () -> EntityType.Builder.<SkeletonKnight>of(SkeletonKnight::new, MobCategory.MONSTER)
                    .sized(SkeletonKnight.WIDTH, SkeletonKnight.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("skeleton_knight")));
    public static final RegistryObject<EntityType<CryptCrawler>> CRYPT_CRAWLER = ENTITIES.register("crypt_crawler",
            () -> EntityType.Builder.<CryptCrawler>of(CryptCrawler::new, MobCategory.MONSTER)
                    .sized(CryptCrawler.WIDTH, CryptCrawler.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("crypt_crawler")));
    public static final RegistryObject<EntityType<Banshee>> BANSHEE = ENTITIES.register("banshee",
            () -> EntityType.Builder.<Banshee>of(Banshee::new, MobCategory.MONSTER)
                    .sized(Banshee.WIDTH, Banshee.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("banshee")));
    public static final RegistryObject<EntityType<Gargoyle>> GARGOYLE = ENTITIES.register("gargoyle",
            () -> EntityType.Builder.<Gargoyle>of(Gargoyle::new, MobCategory.MONSTER)
                    .sized(Gargoyle.WIDTH, Gargoyle.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("gargoyle")));
    public static final RegistryObject<EntityType<EmberImp>> EMBER_IMP = ENTITIES.register("ember_imp",
            () -> EntityType.Builder.<EmberImp>of(EmberImp::new, MobCategory.MONSTER)
                    .sized(EmberImp.WIDTH, EmberImp.HEIGHT).fireImmune().clientTrackingRange(8).build(ENTITIES.key("ember_imp")));
    public static final RegistryObject<EntityType<VoidLarva>> VOID_LARVA = ENTITIES.register("void_larva",
            () -> EntityType.Builder.<VoidLarva>of(VoidLarva::new, MobCategory.MONSTER)
                    .sized(VoidLarva.WIDTH, VoidLarva.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("void_larva")));
    // ---- dungeon champions
    public static final RegistryObject<EntityType<GraveKnight>> GRAVE_KNIGHT = ENTITIES.register("grave_knight",
            () -> EntityType.Builder.<GraveKnight>of(GraveKnight::new, MobCategory.MONSTER)
                    .sized(GraveKnight.WIDTH, GraveKnight.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("grave_knight")));
    public static final RegistryObject<EntityType<BoneMatriarch>> BONE_MATRIARCH = ENTITIES.register("bone_matriarch",
            () -> EntityType.Builder.<BoneMatriarch>of(BoneMatriarch::new, MobCategory.MONSTER)
                    .sized(BoneMatriarch.WIDTH, BoneMatriarch.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("bone_matriarch")));
    public static final RegistryObject<EntityType<WeepingLady>> WEEPING_LADY = ENTITIES.register("weeping_lady",
            () -> EntityType.Builder.<WeepingLady>of(WeepingLady::new, MobCategory.MONSTER)
                    .sized(WeepingLady.WIDTH, WeepingLady.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("weeping_lady")));
    public static final RegistryObject<EntityType<LarvaMother>> LARVA_MOTHER = ENTITIES.register("larva_mother",
            () -> EntityType.Builder.<LarvaMother>of(LarvaMother::new, MobCategory.MONSTER)
                    .sized(LarvaMother.WIDTH, LarvaMother.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("larva_mother")));
    public static final RegistryObject<EntityType<BoomerangEntity>> BOOMERANG = ENTITIES.register("boomerang",
            () -> EntityType.Builder.<BoomerangEntity>of(BoomerangEntity::new, MobCategory.MISC)
                    .sized(0.4F, 0.4F).clientTrackingRange(6).updateInterval(2).build(ENTITIES.key("boomerang")));

    public static final RegistryObject<EntityType<com.brasshaven.entity.GrapplingHookEntity>> GRAPPLING_HOOK = ENTITIES.register("grappling_hook",
            () -> EntityType.Builder.<com.brasshaven.entity.GrapplingHookEntity>of(com.brasshaven.entity.GrapplingHookEntity::new, MobCategory.MISC)
                    .sized(0.3F, 0.3F).clientTrackingRange(8).updateInterval(1).build(ENTITIES.key("grappling_hook")));
    public static final RegistryObject<EntityType<com.brasshaven.entity.RivetEntity>> RIVET = ENTITIES.register("rivet",
            () -> EntityType.Builder.<com.brasshaven.entity.RivetEntity>of(com.brasshaven.entity.RivetEntity::new, MobCategory.MISC)
                    .sized(0.2F, 0.2F).clientTrackingRange(4).updateInterval(5).build(ENTITIES.key("rivet")));
    // ---- automatons (Clockwork Citadel, badlands and savanna highlands, Undercity)
    public static final RegistryObject<EntityType<ClockworkSpider>> CLOCKWORK_SPIDER = ENTITIES.register("clockwork_spider",
            () -> EntityType.Builder.<ClockworkSpider>of(ClockworkSpider::new, MobCategory.MONSTER)
                    .sized(ClockworkSpider.WIDTH, ClockworkSpider.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("clockwork_spider")));
    public static final RegistryObject<EntityType<SteamDrone>> STEAM_DRONE = ENTITIES.register("steam_drone",
            () -> EntityType.Builder.<SteamDrone>of(SteamDrone::new, MobCategory.MONSTER)
                    .sized(SteamDrone.WIDTH, SteamDrone.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("steam_drone")));
    public static final RegistryObject<EntityType<BrassGolem>> BRASS_GOLEM = ENTITIES.register("brass_golem",
            () -> EntityType.Builder.<BrassGolem>of(BrassGolem::new, MobCategory.MISC)
                    .sized(BrassGolem.WIDTH, BrassGolem.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("brass_golem")));
    public static final RegistryObject<EntityType<GrandClockmaker>> GRAND_CLOCKMAKER = ENTITIES.register("grand_clockmaker",
            () -> EntityType.Builder.<GrandClockmaker>of(GrandClockmaker::new, MobCategory.MONSTER)
                    .sized(GrandClockmaker.WIDTH, GrandClockmaker.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("grand_clockmaker")));
    public static final RegistryObject<EntityType<HotRivetEntity>> HOT_RIVET = ENTITIES.register("hot_rivet",
            () -> EntityType.Builder.<HotRivetEntity>of(HotRivetEntity::new, MobCategory.MISC)
                    .sized(0.25F, 0.25F).clientTrackingRange(6).updateInterval(2).build(ENTITIES.key("hot_rivet")));

    // ---- quest givers (villages, guild outposts, Clockwork Citadel, World Tree, Dwarven City: tools/wf/npcs.py)
    public static final RegistryObject<EntityType<com.brasshaven.entity.WayfarerNpc>> WAYFARER_NPC = ENTITIES.register("wayfarer_npc",
            () -> EntityType.Builder.<com.brasshaven.entity.WayfarerNpc>of(com.brasshaven.entity.WayfarerNpc::new, MobCategory.MISC)
                    .sized(com.brasshaven.entity.WayfarerNpc.WIDTH, com.brasshaven.entity.WayfarerNpc.HEIGHT).fireImmune()
                    .clientTrackingRange(10).build(ENTITIES.key("wayfarer_npc")));

    // ---- living oceans (spawns: tools/wf/ocean.py biome modifiers; the Sea Serpent rises near boats, OceanEvents)
    public static final RegistryObject<EntityType<GlowJellyfish>> GLOW_JELLYFISH = ENTITIES.register("glow_jellyfish",
            () -> EntityType.Builder.<GlowJellyfish>of(GlowJellyfish::new, MobCategory.WATER_AMBIENT)
                    .sized(GlowJellyfish.WIDTH, GlowJellyfish.HEIGHT).clientTrackingRange(6).build(ENTITIES.key("glow_jellyfish")));
    public static final RegistryObject<EntityType<ReefFish>> REEF_FISH = ENTITIES.register("reef_fish",
            () -> EntityType.Builder.<ReefFish>of(ReefFish::new, MobCategory.WATER_AMBIENT)
                    .sized(ReefFish.WIDTH, ReefFish.HEIGHT).clientTrackingRange(4).build(ENTITIES.key("reef_fish")));
    public static final RegistryObject<EntityType<MantaRay>> MANTA_RAY = ENTITIES.register("manta_ray",
            () -> EntityType.Builder.<MantaRay>of(MantaRay::new, MobCategory.WATER_CREATURE)
                    .sized(MantaRay.WIDTH, MantaRay.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("manta_ray")));
    public static final RegistryObject<EntityType<SeaSerpent>> SEA_SERPENT = ENTITIES.register("sea_serpent",
            () -> EntityType.Builder.<SeaSerpent>of(SeaSerpent::new, MobCategory.MONSTER)
                    .sized(SeaSerpent.WIDTH, SeaSerpent.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("sea_serpent")));
    public static final RegistryObject<EntityType<Whale>> WHALE = ENTITIES.register("whale",
            () -> EntityType.Builder.<Whale>of(Whale::new, MobCategory.WATER_CREATURE)
                    .sized(Whale.WIDTH, Whale.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("whale")));

    // ---- peoples of the places (tools/wf/denizens.py): residents with roles, trades and guards
    public static final RegistryObject<EntityType<Dwarf>> DWARF = ENTITIES.register("dwarf",
            () -> EntityType.Builder.<Dwarf>of(Dwarf::new, MobCategory.MISC)
                    .sized(Dwarf.WIDTH, Dwarf.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("dwarf")));
    public static final RegistryObject<EntityType<Sylvan>> SYLVAN = ENTITIES.register("sylvan",
            () -> EntityType.Builder.<Sylvan>of(Sylvan::new, MobCategory.MISC)
                    .sized(Sylvan.WIDTH, Sylvan.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("sylvan")));
    public static final RegistryObject<EntityType<ClockworkCitizen>> CLOCKWORK_CITIZEN = ENTITIES.register("clockwork_citizen",
            () -> EntityType.Builder.<ClockworkCitizen>of(ClockworkCitizen::new, MobCategory.MISC)
                    .sized(ClockworkCitizen.WIDTH, ClockworkCitizen.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("clockwork_citizen")));
    public static final RegistryObject<EntityType<Monk>> MONK = ENTITIES.register("monk",
            () -> EntityType.Builder.<Monk>of(Monk::new, MobCategory.MISC)
                    .sized(Monk.WIDTH, Monk.HEIGHT).clientTrackingRange(10).build(ENTITIES.key("monk")));
    // ---- creatures of the hostile places (tools/wf/denizens.py)
    public static final RegistryObject<EntityType<BanditMarksman>> BANDIT_MARKSMAN = ENTITIES.register("bandit_marksman",
            () -> EntityType.Builder.<BanditMarksman>of(BanditMarksman::new, MobCategory.MONSTER)
                    .sized(BanditMarksman.WIDTH, BanditMarksman.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("bandit_marksman")));
    public static final RegistryObject<EntityType<SkyRaider>> SKY_RAIDER = ENTITIES.register("sky_raider",
            () -> EntityType.Builder.<SkyRaider>of(SkyRaider::new, MobCategory.MONSTER)
                    .sized(SkyRaider.WIDTH, SkyRaider.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("sky_raider")));
    public static final RegistryObject<EntityType<BarnacleCrab>> BARNACLE_CRAB = ENTITIES.register("barnacle_crab",
            () -> EntityType.Builder.<BarnacleCrab>of(BarnacleCrab::new, MobCategory.MONSTER)
                    .sized(BarnacleCrab.WIDTH, BarnacleCrab.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("barnacle_crab")));
    public static final RegistryObject<EntityType<LanternWisp>> LANTERN_WISP = ENTITIES.register("lantern_wisp",
            () -> EntityType.Builder.<LanternWisp>of(LanternWisp::new, MobCategory.MONSTER)
                    .sized(LanternWisp.WIDTH, LanternWisp.HEIGHT).fireImmune().clientTrackingRange(8).build(ENTITIES.key("lantern_wisp")));
    public static final RegistryObject<EntityType<CinderHound>> CINDER_HOUND = ENTITIES.register("cinder_hound",
            () -> EntityType.Builder.<CinderHound>of(CinderHound::new, MobCategory.MONSTER)
                    .sized(CinderHound.WIDTH, CinderHound.HEIGHT).fireImmune().clientTrackingRange(8).build(ENTITIES.key("cinder_hound")));
    public static final RegistryObject<EntityType<RiftSentinel>> RIFT_SENTINEL = ENTITIES.register("rift_sentinel",
            () -> EntityType.Builder.<RiftSentinel>of(RiftSentinel::new, MobCategory.MONSTER)
                    .sized(RiftSentinel.WIDTH, RiftSentinel.HEIGHT).clientTrackingRange(8).build(ENTITIES.key("rift_sentinel")));

    /** Every boss with an Elden Ring style fight (demo command, quests). */
    public static List<RegistryObject<? extends EntityType<? extends com.brasshaven.boss.WayfarerBoss>>> bosses() {
        return List.of(DROWNED_WARDEN, VOID_WARDEN, GRAVE_KNIGHT, BONE_MATRIARCH, WEEPING_LADY, LARVA_MOTHER, BELL_KEEPER, ARCHIVIST, SAND_PHARAOH, JADE_JAGUAR, ROOT_MOTHER, SWAMP_CRONE, GRYPHON_KNIGHT, RUNE_COLOSSUS, FORGE_KING, CRYSTAL_SPIDER, SCULK_SPAWN, ASH_LORD, PIGLIN_KING, SOUL_REAPER, GRAND_CLOCKMAKER);
    }

    public static void registerAttributes(EntityAttributeCreationEvent event) {
        event.put(WAYFARER_NPC.get(), com.brasshaven.entity.WayfarerNpc.attributes().build());
        event.put(RUIN_WALKER.get(), RuinWalker.attributes().build());
        event.put(MAP_WRAITH.get(), MapWraith.attributes().build());
        event.put(BASALT_GUARD.get(), BasaltGuard.attributes().build());
        event.put(VOID_STALKER.get(), VoidStalker.attributes().build());
        event.put(DROWNED_WARDEN.get(), DrownedWarden.attributes().build());
        event.put(VOID_WARDEN.get(), VoidWarden.attributes().build());
        event.put(SKELETON_KNIGHT.get(), SkeletonKnight.attributes().build());
        event.put(CRYPT_CRAWLER.get(), CryptCrawler.attributes().build());
        event.put(BANSHEE.get(), Banshee.attributes().build());
        event.put(GARGOYLE.get(), Gargoyle.attributes().build());
        event.put(EMBER_IMP.get(), EmberImp.attributes().build());
        event.put(VOID_LARVA.get(), VoidLarva.attributes().build());
        event.put(GRAVE_KNIGHT.get(), GraveKnight.attributes().build());
        event.put(BONE_MATRIARCH.get(), BoneMatriarch.attributes().build());
        event.put(WEEPING_LADY.get(), WeepingLady.attributes().build());
        event.put(LARVA_MOTHER.get(), LarvaMother.attributes().build());
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
        event.put(CLOCKWORK_SPIDER.get(), ClockworkSpider.attributes().build());
        event.put(STEAM_DRONE.get(), SteamDrone.attributes().build());
        event.put(BRASS_GOLEM.get(), BrassGolem.attributes().build());
        event.put(GRAND_CLOCKMAKER.get(), GrandClockmaker.attributes().build());
        event.put(GLOW_JELLYFISH.get(), GlowJellyfish.attributes().build());
        event.put(REEF_FISH.get(), ReefFish.attributes().build());
        event.put(MANTA_RAY.get(), MantaRay.attributes().build());
        event.put(SEA_SERPENT.get(), SeaSerpent.attributes().build());
        event.put(WHALE.get(), Whale.attributes().build());
        event.put(DWARF.get(), Dwarf.attributes().build());
        event.put(SYLVAN.get(), Sylvan.attributes().build());
        event.put(CLOCKWORK_CITIZEN.get(), ClockworkCitizen.attributes().build());
        event.put(MONK.get(), Monk.attributes().build());
        event.put(BANDIT_MARKSMAN.get(), BanditMarksman.attributes().build());
        event.put(SKY_RAIDER.get(), SkyRaider.attributes().build());
        event.put(BARNACLE_CRAB.get(), BarnacleCrab.attributes().build());
        event.put(LANTERN_WISP.get(), LanternWisp.attributes().build());
        event.put(CINDER_HOUND.get(), CinderHound.attributes().build());
        event.put(RIFT_SENTINEL.get(), RiftSentinel.attributes().build());
    }

    /** Natural/structure spawning rules: on the ground, in the dark, like vanilla monsters. */
    public static void registerSpawnPlacements(SpawnPlacementRegisterEvent event) {
        for (EntityType<? extends Monster> type : List.of(RUIN_WALKER.get(), MAP_WRAITH.get(), BASALT_GUARD.get(), VOID_STALKER.get(),
                SKELETON_KNIGHT.get(), CRYPT_CRAWLER.get(), BANSHEE.get(), GARGOYLE.get(), EMBER_IMP.get(), VOID_LARVA.get(), CLOCKWORK_SPIDER.get(), STEAM_DRONE.get(),
                BANDIT_MARKSMAN.get(), SKY_RAIDER.get(), LANTERN_WISP.get(), CINDER_HOUND.get(), RIFT_SENTINEL.get())) {
            register(event, type);
        }
        // the Barnacle Crab spawns under water (the sunken structures' spawn lists)
        event.register(BARNACLE_CRAB.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.OCEAN_FLOOR,
                BarnacleCrab::checkSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        // sea creatures: in water, each with its own depth rules
        event.register(GLOW_JELLYFISH.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                GlowJellyfish::checkSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(REEF_FISH.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                net.minecraft.world.entity.animal.fish.WaterAnimal::checkSurfaceWaterAnimalSpawnRules,
                SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(MANTA_RAY.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                MantaRay::checkSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        event.register(WHALE.get(), SpawnPlacementTypes.IN_WATER, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Whale::checkSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
        // server limits (spawns.natural, spawns.maxLoadedPerType) on top of every creature's own rules
        for (EntityType<?> type : List.of(RUIN_WALKER.get(), MAP_WRAITH.get(), BASALT_GUARD.get(), VOID_STALKER.get(),
                SKELETON_KNIGHT.get(), CRYPT_CRAWLER.get(), BANSHEE.get(), GARGOYLE.get(), EMBER_IMP.get(), VOID_LARVA.get(),
                CLOCKWORK_SPIDER.get(), STEAM_DRONE.get(), GLOW_JELLYFISH.get(), REEF_FISH.get(), MANTA_RAY.get(), WHALE.get(),
                BANDIT_MARKSMAN.get(), SKY_RAIDER.get(), BARNACLE_CRAB.get(), LANTERN_WISP.get(), CINDER_HOUND.get(), RIFT_SENTINEL.get())) {
            capped(event, type);
        }
    }

    private static <T extends net.minecraft.world.entity.Entity> void capped(SpawnPlacementRegisterEvent event, EntityType<T> type) {
        event.register(type, (t, level, reason, pos, random) -> com.brasshaven.util.SpawnCaps.allow(t, level, reason),
                SpawnPlacementRegisterEvent.Operation.AND);
    }

    private static <T extends Monster> void register(SpawnPlacementRegisterEvent event, EntityType<T> type) {
        event.register(type, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                Monster::checkMonsterSpawnRules, SpawnPlacementRegisterEvent.Operation.REPLACE);
    }

    private ModEntities() {}
}

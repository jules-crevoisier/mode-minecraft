package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.item.BoomerangItem;
import com.brasshaven.item.CartographerBladeItem;
import com.brasshaven.item.EmberScytheItem;
import com.brasshaven.item.FrostBladeItem;
import com.brasshaven.item.LightStaffItem;
import com.brasshaven.item.MagnetRingItem;
import com.brasshaven.item.RecallScrollItem;
import com.brasshaven.item.StormStaffItem;
import com.brasshaven.item.StructureCompassItem;
import com.brasshaven.item.TelluricHammerItem;
import com.brasshaven.item.TooltipBlockItem;
import com.brasshaven.item.TooltipItem;
import com.brasshaven.item.TravelBackpackItem;
import com.brasshaven.item.VoidSpearItem;
import com.brasshaven.item.WayfarerAtlasItem;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.level.block.Block;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import java.util.function.Supplier;

public final class ModItems {
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, Brasshaven.MODID);
    /** Every item in creative-tab order. */
    public static final List<RegistryObject<? extends Item>> ALL = new ArrayList<>();
    /** Brass ingots: repair material of the steam gadgets. */
    public static final net.minecraft.tags.TagKey<Item> GADGET_REPAIR = net.minecraft.tags.TagKey.create(
            net.minecraft.core.registries.Registries.ITEM, Brasshaven.id("gadget_repair_materials"));

    // ---- progression materials
    public static final RegistryObject<Item> MAP_FRAGMENT = simple("map_fragment", p -> p);
    public static final RegistryObject<Item> LITHITE_SHARD = simple("lithite_shard", p -> p);
    public static final RegistryObject<Item> ANCIENT_EMBER = simple("ancient_ember", p -> p.fireResistant());
    public static final RegistryObject<Item> VOID_SHARD = simple("void_shard", p -> p.rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> WARDEN_SCALE = simple("warden_scale", p -> p.rarity(Rarity.RARE));
    public static final RegistryObject<Item> VOID_HEART = simple("void_heart", p -> p.rarity(Rarity.EPIC).fireResistant());
    /** NG+ boss drop (cycle 3+): on an anvil, +1 attack damage for a boss weapon (boss/BossDifficulty). */
    public static final RegistryObject<Item> EMBER_OF_ASCENSION = simple("ember_of_ascension", p -> p.rarity(Rarity.EPIC).fireResistant());
    // ---- automatons
    public static final RegistryObject<Item> BRASS_GEAR = simple("brass_gear", p -> p);
    public static final RegistryObject<Item> CLOCKWORK_HEART = register("clockwork_heart", com.brasshaven.item.ClockworkHeartItem::new,
            p -> p.stacksTo(16).rarity(Rarity.UNCOMMON));

    // ---- explorer utilities
    public static final RegistryObject<Item> WAYFARER_ATLAS = register("wayfarer_atlas", WayfarerAtlasItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> WAYFARER_MANUAL = register("wayfarer_manual", com.brasshaven.item.WayfarerManualItem::new,
            p -> p.stacksTo(1));
    public static final RegistryObject<Item> STRUCTURE_COMPASS = register("structure_compass", StructureCompassItem::new,
            p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> TRAVEL_BACKPACK = register("travel_backpack", TravelBackpackItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> EXPLORER_BACKPACK = register("explorer_backpack", p -> new TravelBackpackItem(p, 6),
            p -> p.stacksTo(1));
    public static final RegistryObject<Item> MAGNET_RING = register("magnet_ring", MagnetRingItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> RECALL_SCROLL = register("recall_scroll", RecallScrollItem::new, p -> p.stacksTo(16));
    // ---- magic (mana)
    public static final RegistryObject<Item> FIRE_STAFF = spell("fire_staff", com.brasshaven.item.SpellItem.Spell.FIRE_BOLT, 15, 10);
    public static final RegistryObject<Item> FROST_STAFF = spell("frost_staff", com.brasshaven.item.SpellItem.Spell.FROST_NOVA, 25, 20);
    public static final RegistryObject<Item> THUNDER_STAFF = spell("thunder_staff", com.brasshaven.item.SpellItem.Spell.CHAIN_LIGHTNING, 35, 30);
    public static final RegistryObject<Item> HEALING_STAFF = spell("healing_staff", com.brasshaven.item.SpellItem.Spell.HEALING, 30, 40);
    public static final RegistryObject<Item> LEVITATION_WAND = spell("levitation_wand", com.brasshaven.item.SpellItem.Spell.LEVITATION, 20, 20);
    public static final RegistryObject<Item> WARD_ORB = spell("ward_orb", com.brasshaven.item.SpellItem.Spell.WARD, 40, 100);
    public static final RegistryObject<Item> STEAM_CANE = spell("steam_cane", com.brasshaven.item.SpellItem.Spell.STEAM_BLAST, 20, 16);
    public static final RegistryObject<Item> ARCANE_RING = register("arcane_ring", TooltipItem::new, p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> MANA_AMULET = register("mana_amulet", TooltipItem::new, p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> OBLIVION_VIAL = register("oblivion_vial", com.brasshaven.item.OblivionVialItem::new,
            p -> p.stacksTo(16).rarity(Rarity.RARE));

    public static final RegistryObject<Item> BUILDER_WAND = register("builder_wand",
            p -> new com.brasshaven.item.BuilderWandItem(p, 16), p -> p.durability(1024));
    public static final RegistryObject<Item> MASTER_BUILDER_WAND = register("master_builder_wand",
            p -> new com.brasshaven.item.BuilderWandItem(p, 64), p -> p.durability(4096).rarity(Rarity.RARE));
    public static final RegistryObject<Item> CHISEL = register("chisel", com.brasshaven.item.ChiselItem::new, p -> p.durability(640));

    // ---- steam gadgets (repaired with brass ingots)
    public static final RegistryObject<Item> BRASS_WRENCH = register("brass_wrench", com.brasshaven.item.BrassWrenchItem::new,
            p -> p.durability(512).repairable(GADGET_REPAIR));
    public static final RegistryObject<Item> GRAPPLING_HOOK = register("grappling_hook", com.brasshaven.item.GrapplingHookItem::new,
            p -> p.durability(320).repairable(GADGET_REPAIR).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> BRASS_GLIDER = register("brass_glider", com.brasshaven.item.GliderItem::new,
            p -> p.durability(900).repairable(GADGET_REPAIR).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> RIVET_GUN = register("rivet_gun", com.brasshaven.item.RivetGunItem::new,
            p -> p.durability(465).repairable(GADGET_REPAIR));
    public static final RegistryObject<Item> RIVET = simple("rivet", p -> p);
    public static final RegistryObject<Item> POCKET_WATCH = register("pocket_watch", com.brasshaven.item.PocketWatchItem::new,
            p -> p.stacksTo(1));
    public static final RegistryObject<Item> AIRSHIP_COMPASS = register("airship_compass", com.brasshaven.item.AirshipCompassItem::new,
            p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));

    // ---- weapons
    public static final RegistryObject<Item> CARTOGRAPHER_BLADE = register("cartographer_blade", CartographerBladeItem::new,
            p -> p.sword(ModMaterials.CARTOGRAPHER, 3.0F, -2.4F));
    public static final RegistryObject<Item> TELLURIC_HAMMER = register("telluric_hammer", TelluricHammerItem::new,
            p -> p.sword(ModMaterials.LITHITE, 6.0F, -3.2F));
    public static final RegistryObject<Item> FROST_BLADE = register("frost_blade", FrostBladeItem::new,
            p -> p.sword(ModMaterials.LITHITE, 3.0F, -2.2F));
    public static final RegistryObject<Item> BOOMERANG = register("boomerang", BoomerangItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> EMBER_SCYTHE = register("ember_scythe", EmberScytheItem::new,
            p -> p.sword(ModMaterials.EMBER, 5.0F, -2.8F).fireResistant());
    public static final RegistryObject<Item> STORM_STAFF = register("storm_staff", StormStaffItem::new,
            p -> p.durability(320).rarity(Rarity.RARE));
    public static final RegistryObject<Item> VOID_SPEAR = register("void_spear", VoidSpearItem::new,
            p -> p.sword(ModMaterials.VOID, 4.0F, -2.6F).rarity(Rarity.RARE));
    public static final RegistryObject<Item> LIGHT_STAFF = register("light_staff", LightStaffItem::new,
            p -> p.durability(400).rarity(Rarity.RARE));

    // ---- area tools (behaviour lives in EquipmentEvents)
    public static final RegistryObject<Item> EXCAVATOR_PICKAXE = register("excavator_pickaxe", TooltipItem::new,
            p -> p.pickaxe(ModMaterials.LITHITE, 1.0F, -3.0F));
    public static final RegistryObject<Item> LUMBER_AXE = register("lumber_axe",
            p -> new LumberAxe(p), p -> p);

    // ---- armor sets
    public static final RegistryObject<Item> EXPLORER_HELMET = armor("explorer_helmet", ModMaterials.EXPLORER_ARMOR, ArmorType.HELMET);
    public static final RegistryObject<Item> EXPLORER_CHESTPLATE = armor("explorer_chestplate", ModMaterials.EXPLORER_ARMOR, ArmorType.CHESTPLATE);
    public static final RegistryObject<Item> EXPLORER_LEGGINGS = armor("explorer_leggings", ModMaterials.EXPLORER_ARMOR, ArmorType.LEGGINGS);
    public static final RegistryObject<Item> EXPLORER_BOOTS = armor("explorer_boots", ModMaterials.EXPLORER_ARMOR, ArmorType.BOOTS);
    public static final RegistryObject<Item> EMBER_HELMET = armor("ember_helmet", ModMaterials.EMBER_ARMOR, ArmorType.HELMET);
    public static final RegistryObject<Item> EMBER_CHESTPLATE = armor("ember_chestplate", ModMaterials.EMBER_ARMOR, ArmorType.CHESTPLATE);
    public static final RegistryObject<Item> EMBER_LEGGINGS = armor("ember_leggings", ModMaterials.EMBER_ARMOR, ArmorType.LEGGINGS);
    public static final RegistryObject<Item> EMBER_BOOTS = armor("ember_boots", ModMaterials.EMBER_ARMOR, ArmorType.BOOTS);
    public static final RegistryObject<Item> VOID_HELMET = armor("void_helmet", ModMaterials.VOID_ARMOR, ArmorType.HELMET);
    public static final RegistryObject<Item> VOID_CHESTPLATE = armor("void_chestplate", ModMaterials.VOID_ARMOR, ArmorType.CHESTPLATE);
    public static final RegistryObject<Item> VOID_LEGGINGS = armor("void_leggings", ModMaterials.VOID_ARMOR, ArmorType.LEGGINGS);
    public static final RegistryObject<Item> VOID_BOOTS = armor("void_boots", ModMaterials.VOID_ARMOR, ArmorType.BOOTS);

    // ---- blocks
    public static final RegistryObject<Item> WAYSTONE = block("waystone", ModBlocks.WAYSTONE, p -> p.rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> SORTING_CHEST = block("sorting_chest", ModBlocks.SORTING_CHEST, p -> p);
    public static final RegistryObject<Item> GUILD_TERMINAL = block("guild_terminal", ModBlocks.GUILD_TERMINAL, p -> p);
    public static final RegistryObject<Item> COMPACTING_CRATE = block("compacting_crate", ModBlocks.COMPACTING_CRATE, p -> p);
    public static final RegistryObject<Item> STORAGE_RELAY = block("storage_relay", ModBlocks.STORAGE_RELAY, p -> p);
    public static final RegistryObject<Item> CHISEL_TABLE = block("chisel_table", ModBlocks.CHISEL_TABLE, p -> p);
    public static final RegistryObject<Item> GRAVE = block("grave", ModBlocks.GRAVE, p -> p);
    public static final RegistryObject<Item> SEALED_BARS = block("sealed_bars", ModBlocks.SEALED_BARS, p -> p);
    public static final RegistryObject<Item> WARDEN_ALTAR = block("warden_altar", ModBlocks.WARDEN_ALTAR, p -> p.rarity(Rarity.RARE));
    public static final RegistryObject<Item> VOID_ALTAR = block("void_altar", ModBlocks.VOID_ALTAR, p -> p.rarity(Rarity.RARE));
    public static final RegistryObject<Item> MIST_GATE = block("mist_gate", ModBlocks.MIST_GATE, p -> p);
    public static final RegistryObject<Item> BOSS_SEAL = block("boss_seal", ModBlocks.BOSS_SEAL, p -> p.rarity(Rarity.EPIC));
    public static final RegistryObject<Item> LITHITE_ORE = block("lithite_ore", ModBlocks.LITHITE_ORE, p -> p);
    public static final RegistryObject<Item> DEEPSLATE_LITHITE_ORE = block("deepslate_lithite_ore", ModBlocks.DEEPSLATE_LITHITE_ORE, p -> p);

    // ---- spawn eggs
    public static final RegistryObject<Item> RUIN_WALKER_SPAWN_EGG = egg("ruin_walker_spawn_egg", ModEntities.RUIN_WALKER);
    public static final RegistryObject<Item> MAP_WRAITH_SPAWN_EGG = egg("map_wraith_spawn_egg", ModEntities.MAP_WRAITH);
    public static final RegistryObject<Item> BASALT_GUARD_SPAWN_EGG = egg("basalt_guard_spawn_egg", ModEntities.BASALT_GUARD);
    public static final RegistryObject<Item> VOID_STALKER_SPAWN_EGG = egg("void_stalker_spawn_egg", ModEntities.VOID_STALKER);
    public static final RegistryObject<Item> DROWNED_WARDEN_SPAWN_EGG = egg("drowned_warden_spawn_egg", ModEntities.DROWNED_WARDEN);
    public static final RegistryObject<Item> VOID_WARDEN_SPAWN_EGG = egg("void_warden_spawn_egg", ModEntities.VOID_WARDEN);
    public static final RegistryObject<Item> SKELETON_KNIGHT_SPAWN_EGG = egg("skeleton_knight_spawn_egg", ModEntities.SKELETON_KNIGHT);
    public static final RegistryObject<Item> CRYPT_CRAWLER_SPAWN_EGG = egg("crypt_crawler_spawn_egg", ModEntities.CRYPT_CRAWLER);
    public static final RegistryObject<Item> BANSHEE_SPAWN_EGG = egg("banshee_spawn_egg", ModEntities.BANSHEE);
    public static final RegistryObject<Item> GARGOYLE_SPAWN_EGG = egg("gargoyle_spawn_egg", ModEntities.GARGOYLE);
    public static final RegistryObject<Item> EMBER_IMP_SPAWN_EGG = egg("ember_imp_spawn_egg", ModEntities.EMBER_IMP);
    public static final RegistryObject<Item> VOID_LARVA_SPAWN_EGG = egg("void_larva_spawn_egg", ModEntities.VOID_LARVA);
    public static final RegistryObject<Item> GRAVE_KNIGHT_SPAWN_EGG = egg("grave_knight_spawn_egg", ModEntities.GRAVE_KNIGHT);
    public static final RegistryObject<Item> BONE_MATRIARCH_SPAWN_EGG = egg("bone_matriarch_spawn_egg", ModEntities.BONE_MATRIARCH);
    public static final RegistryObject<Item> WEEPING_LADY_SPAWN_EGG = egg("weeping_lady_spawn_egg", ModEntities.WEEPING_LADY);
    public static final RegistryObject<Item> LARVA_MOTHER_SPAWN_EGG = egg("larva_mother_spawn_egg", ModEntities.LARVA_MOTHER);
    public static final RegistryObject<Item> BELL_KEEPER_SPAWN_EGG = egg("bell_keeper_spawn_egg", ModEntities.BELL_KEEPER);
    public static final RegistryObject<Item> ARCHIVIST_SPAWN_EGG = egg("archivist_spawn_egg", ModEntities.ARCHIVIST);
    public static final RegistryObject<Item> SAND_PHARAOH_SPAWN_EGG = egg("sand_pharaoh_spawn_egg", ModEntities.SAND_PHARAOH);
    public static final RegistryObject<Item> JADE_JAGUAR_SPAWN_EGG = egg("jade_jaguar_spawn_egg", ModEntities.JADE_JAGUAR);
    public static final RegistryObject<Item> ROOT_MOTHER_SPAWN_EGG = egg("root_mother_spawn_egg", ModEntities.ROOT_MOTHER);
    public static final RegistryObject<Item> SWAMP_CRONE_SPAWN_EGG = egg("swamp_crone_spawn_egg", ModEntities.SWAMP_CRONE);
    public static final RegistryObject<Item> GRYPHON_KNIGHT_SPAWN_EGG = egg("gryphon_knight_spawn_egg", ModEntities.GRYPHON_KNIGHT);
    public static final RegistryObject<Item> RUNE_COLOSSUS_SPAWN_EGG = egg("rune_colossus_spawn_egg", ModEntities.RUNE_COLOSSUS);
    public static final RegistryObject<Item> FORGE_KING_SPAWN_EGG = egg("forge_king_spawn_egg", ModEntities.FORGE_KING);
    public static final RegistryObject<Item> CRYSTAL_SPIDER_SPAWN_EGG = egg("crystal_spider_spawn_egg", ModEntities.CRYSTAL_SPIDER);
    public static final RegistryObject<Item> SCULK_SPAWN_SPAWN_EGG = egg("sculk_spawn_spawn_egg", ModEntities.SCULK_SPAWN);
    public static final RegistryObject<Item> ASH_LORD_SPAWN_EGG = egg("ash_lord_spawn_egg", ModEntities.ASH_LORD);
    public static final RegistryObject<Item> PIGLIN_KING_SPAWN_EGG = egg("piglin_king_spawn_egg", ModEntities.PIGLIN_KING);
    public static final RegistryObject<Item> SOUL_REAPER_SPAWN_EGG = egg("soul_reaper_spawn_egg", ModEntities.SOUL_REAPER);
    public static final RegistryObject<Item> CLOCKWORK_SPIDER_SPAWN_EGG = egg("clockwork_spider_spawn_egg", ModEntities.CLOCKWORK_SPIDER);
    public static final RegistryObject<Item> STEAM_DRONE_SPAWN_EGG = egg("steam_drone_spawn_egg", ModEntities.STEAM_DRONE);
    public static final RegistryObject<Item> BRASS_GOLEM_SPAWN_EGG = egg("brass_golem_spawn_egg", ModEntities.BRASS_GOLEM);
    public static final RegistryObject<Item> GRAND_CLOCKMAKER_SPAWN_EGG = egg("grand_clockmaker_spawn_egg", ModEntities.GRAND_CLOCKMAKER);
    public static final RegistryObject<Item> IRON_HELMSMAN_SPAWN_EGG = egg("iron_helmsman_spawn_egg", ModEntities.IRON_HELMSMAN);
    public static final RegistryObject<Item> BRONZE_SENTINEL_SPAWN_EGG = egg("bronze_sentinel_spawn_egg", ModEntities.BRONZE_SENTINEL);
    public static final RegistryObject<Item> DUNE_KING_SPAWN_EGG = egg("dune_king_spawn_egg", ModEntities.DUNE_KING);
    public static final RegistryObject<Item> FALLEN_SERAPH_SPAWN_EGG = egg("fallen_seraph_spawn_egg", ModEntities.FALLEN_SERAPH);
    public static final RegistryObject<Item> CHAINED_JAILER_SPAWN_EGG = egg("chained_jailer_spawn_egg", ModEntities.CHAINED_JAILER);
    public static final RegistryObject<Item> CALDERA_CASTELLAN_SPAWN_EGG = egg("caldera_castellan_spawn_egg", ModEntities.CALDERA_CASTELLAN);
    public static final RegistryObject<Item> FROST_JARL_SPAWN_EGG = egg("frost_jarl_spawn_egg", ModEntities.FROST_JARL);
    public static final RegistryObject<Item> OATHBOUND_GATEKEEPER_SPAWN_EGG = egg("oathbound_gatekeeper_spawn_egg", ModEntities.OATHBOUND_GATEKEEPER);
    public static final RegistryObject<Item> STORM_ASCETIC_SPAWN_EGG = egg("storm_ascetic_spawn_egg", ModEntities.STORM_ASCETIC);
    public static final RegistryObject<Item> TIDE_ABBESS_SPAWN_EGG = egg("tide_abbess_spawn_egg", ModEntities.TIDE_ABBESS);
    public static final RegistryObject<Item> ABYSSAL_ARCHITECT_SPAWN_EGG = egg("abyssal_architect_spawn_egg", ModEntities.ABYSSAL_ARCHITECT);
    public static final RegistryObject<Item> LOCK_MASTER_SPAWN_EGG = egg("lock_master_spawn_egg", ModEntities.LOCK_MASTER);
    public static final RegistryObject<Item> BOG_HIEROPHANT_SPAWN_EGG = egg("bog_hierophant_spawn_egg", ModEntities.BOG_HIEROPHANT);
    public static final RegistryObject<Item> STRANGLER_QUEEN_SPAWN_EGG = egg("strangler_queen_spawn_egg", ModEntities.STRANGLER_QUEEN);
    public static final RegistryObject<Item> STAR_CURATOR_SPAWN_EGG = egg("star_curator_spawn_egg", ModEntities.STAR_CURATOR);
    public static final RegistryObject<Item> FOURTH_KING_SPAWN_EGG = egg("fourth_king_spawn_egg", ModEntities.FOURTH_KING);
    public static final RegistryObject<Item> DROWNED_ADMIRAL_SPAWN_EGG = egg("drowned_admiral_spawn_egg", ModEntities.DROWNED_ADMIRAL);
    public static final RegistryObject<Item> TURBINE_TYRANT_SPAWN_EGG = egg("turbine_tyrant_spawn_egg", ModEntities.TURBINE_TYRANT);
    public static final RegistryObject<Item> ANVIL_WARDEN_SPAWN_EGG = egg("anvil_warden_spawn_egg", ModEntities.ANVIL_WARDEN);
    public static final RegistryObject<Item> COLOSSUS_HEART_SPAWN_EGG = egg("colossus_heart_spawn_egg", ModEntities.COLOSSUS_HEART);
    public static final RegistryObject<Item> MINE_BARON_SPAWN_EGG = egg("mine_baron_spawn_egg", ModEntities.MINE_BARON);
    public static final RegistryObject<Item> CHIME_ABBOT_SPAWN_EGG = egg("chime_abbot_spawn_egg", ModEntities.CHIME_ABBOT);
    public static final RegistryObject<Item> CORSAIR_CAPTAIN_SPAWN_EGG = egg("corsair_captain_spawn_egg", ModEntities.CORSAIR_CAPTAIN);
    public static final RegistryObject<Item> HOLLOW_CANTOR_SPAWN_EGG = egg("hollow_cantor_spawn_egg", ModEntities.HOLLOW_CANTOR);
    public static final RegistryObject<Item> SOUL_STOKER_SPAWN_EGG = egg("soul_stoker_spawn_egg", ModEntities.SOUL_STOKER);
    public static final RegistryObject<Item> ASYLUM_DIRECTOR_SPAWN_EGG = egg("asylum_director_spawn_egg", ModEntities.ASYLUM_DIRECTOR);
    public static final RegistryObject<Item> FROST_COMMODORE_SPAWN_EGG = egg("frost_commodore_spawn_egg", ModEntities.FROST_COMMODORE);
    public static final RegistryObject<Item> SPORE_ALCHEMIST_SPAWN_EGG = egg("spore_alchemist_spawn_egg", ModEntities.SPORE_ALCHEMIST);
    public static final RegistryObject<Item> THORN_GARDENER_SPAWN_EGG = egg("thorn_gardener_spawn_egg", ModEntities.THORN_GARDENER);
    public static final RegistryObject<Item> LUMBER_JARL_SPAWN_EGG = egg("lumber_jarl_spawn_egg", ModEntities.LUMBER_JARL);
    public static final RegistryObject<Item> ABYSS_DIVER_SPAWN_EGG = egg("abyss_diver_spawn_egg", ModEntities.ABYSS_DIVER);
    public static final RegistryObject<Item> MOON_WARDEN_SPAWN_EGG = egg("moon_warden_spawn_egg", ModEntities.MOON_WARDEN);
    public static final RegistryObject<Item> RINGMASTER_SPAWN_EGG = egg("ringmaster_spawn_egg", ModEntities.RINGMASTER);
    public static final RegistryObject<Item> GILDED_CHAMPION_SPAWN_EGG = egg("gilded_champion_spawn_egg", ModEntities.GILDED_CHAMPION);
    public static final RegistryObject<Item> TESLA_ARCHON_SPAWN_EGG = egg("tesla_archon_spawn_egg", ModEntities.TESLA_ARCHON);
    public static final RegistryObject<Item> DROWNED_KEEPER_SPAWN_EGG = egg("drowned_keeper_spawn_egg", ModEntities.DROWNED_KEEPER);
    public static final RegistryObject<Item> MERCHANT_PRINCE_SPAWN_EGG = egg("merchant_prince_spawn_egg", ModEntities.MERCHANT_PRINCE);
    public static final RegistryObject<Item> MYCELIUM_ABBOT_SPAWN_EGG = egg("mycelium_abbot_spawn_egg", ModEntities.MYCELIUM_ABBOT);
    public static final RegistryObject<Item> SOLAR_HIERARCH_SPAWN_EGG = egg("solar_hierarch_spawn_egg", ModEntities.SOLAR_HIERARCH);
    // peoples and creatures of the places (tools/wf/denizens.py)
    public static final RegistryObject<Item> DWARF_SPAWN_EGG = egg("dwarf_spawn_egg", ModEntities.DWARF);
    public static final RegistryObject<Item> SYLVAN_SPAWN_EGG = egg("sylvan_spawn_egg", ModEntities.SYLVAN);
    public static final RegistryObject<Item> CLOCKWORK_CITIZEN_SPAWN_EGG = egg("clockwork_citizen_spawn_egg", ModEntities.CLOCKWORK_CITIZEN);
    public static final RegistryObject<Item> MONK_SPAWN_EGG = egg("monk_spawn_egg", ModEntities.MONK);
    public static final RegistryObject<Item> BANDIT_MARKSMAN_SPAWN_EGG = egg("bandit_marksman_spawn_egg", ModEntities.BANDIT_MARKSMAN);
    public static final RegistryObject<Item> SKY_RAIDER_SPAWN_EGG = egg("sky_raider_spawn_egg", ModEntities.SKY_RAIDER);
    public static final RegistryObject<Item> BARNACLE_CRAB_SPAWN_EGG = egg("barnacle_crab_spawn_egg", ModEntities.BARNACLE_CRAB);
    public static final RegistryObject<Item> LANTERN_WISP_SPAWN_EGG = egg("lantern_wisp_spawn_egg", ModEntities.LANTERN_WISP);
    public static final RegistryObject<Item> CINDER_HOUND_SPAWN_EGG = egg("cinder_hound_spawn_egg", ModEntities.CINDER_HOUND);
    public static final RegistryObject<Item> RIFT_SENTINEL_SPAWN_EGG = egg("rift_sentinel_spawn_egg", ModEntities.RIFT_SENTINEL);
    public static final RegistryObject<Item> FROZEN_HUSCARL_SPAWN_EGG = egg("frozen_huscarl_spawn_egg", ModEntities.FROZEN_HUSCARL);
    public static final RegistryObject<Item> MAGMA_SENTRY_SPAWN_EGG = egg("magma_sentry_spawn_egg", ModEntities.MAGMA_SENTRY);
    public static final RegistryObject<Item> OATHBOUND_STATUE_SPAWN_EGG = egg("oathbound_statue_spawn_egg", ModEntities.OATHBOUND_STATUE);
    public static final RegistryObject<Item> TIDE_WRAITH_SPAWN_EGG = egg("tide_wraith_spawn_egg", ModEntities.TIDE_WRAITH);
    public static final RegistryObject<Item> BELL_MONK_SPAWN_EGG = egg("bell_monk_spawn_egg", ModEntities.BELL_MONK);
    public static final RegistryObject<Item> VOID_ACOLYTE_SPAWN_EGG = egg("void_acolyte_spawn_egg", ModEntities.VOID_ACOLYTE);
    public static final RegistryObject<Item> SLUICE_DROWNED_SPAWN_EGG = egg("sluice_drowned_spawn_egg", ModEntities.SLUICE_DROWNED);
    public static final RegistryObject<Item> TURBINE_AUTOMATON_SPAWN_EGG = egg("turbine_automaton_spawn_egg", ModEntities.TURBINE_AUTOMATON);
    public static final RegistryObject<Item> BOG_LEECH_MAN_SPAWN_EGG = egg("bog_leech_man_spawn_egg", ModEntities.BOG_LEECH_MAN);
    public static final RegistryObject<Item> ABYSS_CRAWLER_SPAWN_EGG = egg("abyss_crawler_spawn_egg", ModEntities.ABYSS_CRAWLER);
    public static final RegistryObject<Item> RUST_MITE_MOTHER_SPAWN_EGG = egg("rust_mite_mother_spawn_egg", ModEntities.RUST_MITE_MOTHER);
    public static final RegistryObject<Item> RUST_MITE_SPAWN_EGG = egg("rust_mite_spawn_egg", ModEntities.RUST_MITE);
    public static final RegistryObject<Item> BOILER_GUNNER_SPAWN_EGG = egg("boiler_gunner_spawn_egg", ModEntities.BOILER_GUNNER);
    public static final RegistryObject<Item> SLAG_GOLEM_SPAWN_EGG = egg("slag_golem_spawn_egg", ModEntities.SLAG_GOLEM);
    public static final RegistryObject<Item> INK_WRAITH_SPAWN_EGG = egg("ink_wraith_spawn_egg", ModEntities.INK_WRAITH);
    public static final RegistryObject<Item> STAR_MOTE_CALLER_SPAWN_EGG = egg("star_mote_caller_spawn_egg", ModEntities.STAR_MOTE_CALLER);
    public static final RegistryObject<Item> STAR_MOTE_SPAWN_EGG = egg("star_mote_spawn_egg", ModEntities.STAR_MOTE);
    public static final RegistryObject<Item> SUN_SCARAB_SPAWN_EGG = egg("sun_scarab_spawn_egg", ModEntities.SUN_SCARAB);
    public static final RegistryObject<Item> DART_FROG_ASSASSIN_SPAWN_EGG = egg("dart_frog_assassin_spawn_egg", ModEntities.DART_FROG_ASSASSIN);
    public static final RegistryObject<Item> DROWNED_MARINE_SPAWN_EGG = egg("drowned_marine_spawn_egg", ModEntities.DROWNED_MARINE);

    /** Axe subclass keeps vanilla stripping behaviour; tree felling is handled in EquipmentEvents. */
    public static final class LumberAxe extends AxeItem implements com.brasshaven.item.BrassTooltip.Styled {
        public LumberAxe(Item.Properties properties) {
            super(ModMaterials.LITHITE, 6.0F, -3.1F, properties);
        }

        @Override
        @SuppressWarnings("deprecation")
        public void appendHoverText(net.minecraft.world.item.ItemStack stack, TooltipContext context,
                                    net.minecraft.world.item.component.TooltipDisplay display,
                                    java.util.function.Consumer<net.minecraft.network.chat.Component> builder,
                                    net.minecraft.world.item.TooltipFlag flag) {
            super.appendHoverText(stack, context, display, builder, flag);
            com.brasshaven.item.BrassTooltip.append(stack, builder);
        }
    }

    private static RegistryObject<Item> simple(String name, Function<Item.Properties, Item.Properties> props) {
        return register(name, TooltipItem::new, props);
    }

    private static RegistryObject<Item> spell(String name, com.brasshaven.item.SpellItem.Spell spell, float cost, int cooldown) {
        return register(name, p -> new com.brasshaven.item.SpellItem(p, spell, cost, cooldown), p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));
    }

    private static RegistryObject<Item> register(String name, Function<Item.Properties, ? extends Item> factory,
                                                 Function<Item.Properties, Item.Properties> props) {
        RegistryObject<Item> obj = ITEMS.register(name, () -> factory.apply(props.apply(new Item.Properties().setId(ITEMS.key(name)))));
        ALL.add(obj);
        return obj;
    }

    private static RegistryObject<Item> armor(String name, ArmorMaterial material, ArmorType type) {
        return register(name, TooltipItem::new, p -> p.humanoidArmor(material, type));
    }

    private static RegistryObject<Item> block(String name, Supplier<? extends Block> block, Function<Item.Properties, Item.Properties> props) {
        RegistryObject<Item> obj = ITEMS.register(name,
                () -> new TooltipBlockItem(block.get(), props.apply(new Item.Properties().setId(ITEMS.key(name)).useBlockDescriptionPrefix())));
        ALL.add(obj);
        return obj;
    }

    private static RegistryObject<Item> egg(String name, Supplier<? extends EntityType<?>> type) {
        RegistryObject<Item> obj = ITEMS.register(name,
                () -> new SpawnEggItem(new Item.Properties().setId(ITEMS.key(name)).spawnEgg(type.get())));
        ALL.add(obj);
        return obj;
    }

    private ModItems() {}
}

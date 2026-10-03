package com.wayfarers.registry;

import com.wayfarers.Wayfarers;
import com.wayfarers.item.BoomerangItem;
import com.wayfarers.item.CartographerBladeItem;
import com.wayfarers.item.EmberScytheItem;
import com.wayfarers.item.FrostBladeItem;
import com.wayfarers.item.LightStaffItem;
import com.wayfarers.item.MagnetRingItem;
import com.wayfarers.item.RecallScrollItem;
import com.wayfarers.item.StormStaffItem;
import com.wayfarers.item.StructureCompassItem;
import com.wayfarers.item.TelluricHammerItem;
import com.wayfarers.item.TooltipBlockItem;
import com.wayfarers.item.TooltipItem;
import com.wayfarers.item.TravelBackpackItem;
import com.wayfarers.item.VoidSpearItem;
import com.wayfarers.item.WayfarerAtlasItem;
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
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, Wayfarers.MODID);
    /** Every item in creative-tab order. */
    public static final List<RegistryObject<? extends Item>> ALL = new ArrayList<>();

    // ---- progression materials
    public static final RegistryObject<Item> MAP_FRAGMENT = simple("map_fragment", p -> p);
    public static final RegistryObject<Item> LITHITE_SHARD = simple("lithite_shard", p -> p);
    public static final RegistryObject<Item> ANCIENT_EMBER = simple("ancient_ember", p -> p.fireResistant());
    public static final RegistryObject<Item> VOID_SHARD = simple("void_shard", p -> p.rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> WARDEN_SCALE = simple("warden_scale", p -> p.rarity(Rarity.RARE));
    public static final RegistryObject<Item> VOID_HEART = simple("void_heart", p -> p.rarity(Rarity.EPIC).fireResistant());

    // ---- explorer utilities
    public static final RegistryObject<Item> WAYFARER_ATLAS = register("wayfarer_atlas", WayfarerAtlasItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> WAYFARER_MANUAL = register("wayfarer_manual", com.wayfarers.item.WayfarerManualItem::new,
            p -> p.stacksTo(1));
    public static final RegistryObject<Item> STRUCTURE_COMPASS = register("structure_compass", StructureCompassItem::new,
            p -> p.stacksTo(1).rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> TRAVEL_BACKPACK = register("travel_backpack", TravelBackpackItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> MAGNET_RING = register("magnet_ring", MagnetRingItem::new, p -> p.stacksTo(1));
    public static final RegistryObject<Item> RECALL_SCROLL = register("recall_scroll", RecallScrollItem::new, p -> p.stacksTo(16));
    public static final RegistryObject<Item> BUILDER_WAND = register("builder_wand",
            p -> new com.wayfarers.item.BuilderWandItem(p, 16), p -> p.durability(1024));
    public static final RegistryObject<Item> MASTER_BUILDER_WAND = register("master_builder_wand",
            p -> new com.wayfarers.item.BuilderWandItem(p, 64), p -> p.durability(4096).rarity(Rarity.RARE));

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

    /** Axe subclass keeps vanilla stripping behaviour; tree felling is handled in EquipmentEvents. */
    public static final class LumberAxe extends AxeItem {
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
            builder.accept(net.minecraft.network.chat.Component.translatable(getDescriptionId() + ".desc")
                    .withStyle(net.minecraft.ChatFormatting.GRAY));
        }
    }

    private static RegistryObject<Item> simple(String name, Function<Item.Properties, Item.Properties> props) {
        return register(name, TooltipItem::new, props);
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

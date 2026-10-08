package com.brasshaven.colossal;

import com.brasshaven.Brasshaven;
import com.brasshaven.registry.ModItems;
import com.brasshaven.registry.ModMaterials;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Supplier;
import java.util.function.UnaryOperator;

/**
 * Vault gear of the six newer colossal structures (tools/wf/colossal_gear.py: names, art, loot): six armour sets with
 * a 2-piece and a 4-piece bonus ({@link ColossalSet}, effects in {@link ColossalEvents}) and six weapons / tools with
 * a small right-click or passive identity ({@link ColossalWeaponItem}). All loot-only, from the deep chests and vaults.
 */
public final class ColossalGear {
    // ---- armour materials (repaired with the tag brasshaven:<set>_repair)
    public static final ArmorMaterial LOCKKEEPER_ARMOR = new ArmorMaterial(32, defense(3, 5, 7, 3), 16,
            SoundEvents.ARMOR_EQUIP_IRON, 1.5F, 0.0F, repair("lockkeeper"), asset("lockkeeper"));
    public static final ArmorMaterial TURBINE_ENGINEER_ARMOR = new ArmorMaterial(30, defense(2, 5, 7, 2), 16,
            SoundEvents.ARMOR_EQUIP_IRON, 1.0F, 0.0F, repair("turbine_engineer"), asset("turbine_engineer"));
    public static final ArmorMaterial BOG_PILGRIM_ARMOR = new ArmorMaterial(28, defense(2, 5, 6, 2), 18,
            SoundEvents.ARMOR_EQUIP_LEATHER, 1.0F, 0.0F, repair("bog_pilgrim"), asset("bog_pilgrim"));
    public static final ArmorMaterial SUN_PRIEST_ARMOR = new ArmorMaterial(28, defense(2, 5, 7, 2), 24,
            SoundEvents.ARMOR_EQUIP_GOLD, 1.0F, 0.0F, repair("sun_priest"), asset("sun_priest"));
    public static final ArmorMaterial IRONCLAD_ARMOR = new ArmorMaterial(36, defense(3, 6, 8, 3), 12,
            SoundEvents.ARMOR_EQUIP_NETHERITE, 2.5F, 0.05F, repair("ironclad"), asset("ironclad"));
    public static final ArmorMaterial CANOPY_STALKER_ARMOR = new ArmorMaterial(26, defense(2, 4, 6, 2), 20,
            SoundEvents.ARMOR_EQUIP_LEATHER, 0.5F, 0.0F, repair("canopy_stalker"), asset("canopy_stalker"));

    // ---- Lock-Keeper's Brass (Great Aqueduct)
    public static final RegistryObject<Item> LOCKKEEPER_HELMET = armor("lockkeeper_helmet", LOCKKEEPER_ARMOR, ArmorType.HELMET, ColossalSet.LOCKKEEPER);
    public static final RegistryObject<Item> LOCKKEEPER_CHESTPLATE = armor("lockkeeper_chestplate", LOCKKEEPER_ARMOR, ArmorType.CHESTPLATE, ColossalSet.LOCKKEEPER);
    public static final RegistryObject<Item> LOCKKEEPER_LEGGINGS = armor("lockkeeper_leggings", LOCKKEEPER_ARMOR, ArmorType.LEGGINGS, ColossalSet.LOCKKEEPER);
    public static final RegistryObject<Item> LOCKKEEPER_BOOTS = armor("lockkeeper_boots", LOCKKEEPER_ARMOR, ArmorType.BOOTS, ColossalSet.LOCKKEEPER);
    // ---- Turbine Engineer's Rig (Dam of the Drowned Valley)
    public static final RegistryObject<Item> TURBINE_ENGINEER_HELMET = armor("turbine_engineer_helmet", TURBINE_ENGINEER_ARMOR, ArmorType.HELMET, ColossalSet.TURBINE_ENGINEER);
    public static final RegistryObject<Item> TURBINE_ENGINEER_CHESTPLATE = armor("turbine_engineer_chestplate", TURBINE_ENGINEER_ARMOR, ArmorType.CHESTPLATE, ColossalSet.TURBINE_ENGINEER);
    public static final RegistryObject<Item> TURBINE_ENGINEER_LEGGINGS = armor("turbine_engineer_leggings", TURBINE_ENGINEER_ARMOR, ArmorType.LEGGINGS, ColossalSet.TURBINE_ENGINEER);
    public static final RegistryObject<Item> TURBINE_ENGINEER_BOOTS = armor("turbine_engineer_boots", TURBINE_ENGINEER_ARMOR, ArmorType.BOOTS, ColossalSet.TURBINE_ENGINEER);
    // ---- Bog Pilgrim's Wraps (Mire Stilt-City)
    public static final RegistryObject<Item> BOG_PILGRIM_HELMET = armor("bog_pilgrim_helmet", BOG_PILGRIM_ARMOR, ArmorType.HELMET, ColossalSet.BOG_PILGRIM);
    public static final RegistryObject<Item> BOG_PILGRIM_CHESTPLATE = armor("bog_pilgrim_chestplate", BOG_PILGRIM_ARMOR, ArmorType.CHESTPLATE, ColossalSet.BOG_PILGRIM);
    public static final RegistryObject<Item> BOG_PILGRIM_LEGGINGS = armor("bog_pilgrim_leggings", BOG_PILGRIM_ARMOR, ArmorType.LEGGINGS, ColossalSet.BOG_PILGRIM);
    public static final RegistryObject<Item> BOG_PILGRIM_BOOTS = armor("bog_pilgrim_boots", BOG_PILGRIM_ARMOR, ArmorType.BOOTS, ColossalSet.BOG_PILGRIM);
    // ---- Sun-Priest's Regalia (Sun-Engine Ziggurat)
    public static final RegistryObject<Item> SUN_PRIEST_HELMET = armor("sun_priest_helmet", SUN_PRIEST_ARMOR, ArmorType.HELMET, ColossalSet.SUN_PRIEST);
    public static final RegistryObject<Item> SUN_PRIEST_CHESTPLATE = armor("sun_priest_chestplate", SUN_PRIEST_ARMOR, ArmorType.CHESTPLATE, ColossalSet.SUN_PRIEST);
    public static final RegistryObject<Item> SUN_PRIEST_LEGGINGS = armor("sun_priest_leggings", SUN_PRIEST_ARMOR, ArmorType.LEGGINGS, ColossalSet.SUN_PRIEST);
    public static final RegistryObject<Item> SUN_PRIEST_BOOTS = armor("sun_priest_boots", SUN_PRIEST_ARMOR, ArmorType.BOOTS, ColossalSet.SUN_PRIEST);
    // ---- Ironclad Officer's Plate (Leviathan Dreadnought Wreck)
    public static final RegistryObject<Item> IRONCLAD_HELMET = armor("ironclad_helmet", IRONCLAD_ARMOR, ArmorType.HELMET, ColossalSet.IRONCLAD);
    public static final RegistryObject<Item> IRONCLAD_CHESTPLATE = armor("ironclad_chestplate", IRONCLAD_ARMOR, ArmorType.CHESTPLATE, ColossalSet.IRONCLAD);
    public static final RegistryObject<Item> IRONCLAD_LEGGINGS = armor("ironclad_leggings", IRONCLAD_ARMOR, ArmorType.LEGGINGS, ColossalSet.IRONCLAD);
    public static final RegistryObject<Item> IRONCLAD_BOOTS = armor("ironclad_boots", IRONCLAD_ARMOR, ArmorType.BOOTS, ColossalSet.IRONCLAD);
    // ---- Canopy Stalker's Leathers (Canopy Temple-City)
    public static final RegistryObject<Item> CANOPY_STALKER_HELMET = armor("canopy_stalker_helmet", CANOPY_STALKER_ARMOR, ArmorType.HELMET, ColossalSet.CANOPY_STALKER);
    public static final RegistryObject<Item> CANOPY_STALKER_CHESTPLATE = armor("canopy_stalker_chestplate", CANOPY_STALKER_ARMOR, ArmorType.CHESTPLATE, ColossalSet.CANOPY_STALKER);
    public static final RegistryObject<Item> CANOPY_STALKER_LEGGINGS = armor("canopy_stalker_leggings", CANOPY_STALKER_ARMOR, ArmorType.LEGGINGS, ColossalSet.CANOPY_STALKER);
    public static final RegistryObject<Item> CANOPY_STALKER_BOOTS = armor("canopy_stalker_boots", CANOPY_STALKER_ARMOR, ArmorType.BOOTS, ColossalSet.CANOPY_STALKER);

    // ---- weapons and tools: kind, cooldown (ticks), structure
    public static final RegistryObject<Item> SLUICE_HOOK = weapon("sluice_hook", ColossalWeaponItem.Kind.SLUICE_HOOK, 70, "ga",
            p -> p.sword(ModMaterials.LITHITE, 4.0F, -2.8F).rarity(Rarity.RARE));
    public static final RegistryObject<Item> RIVET_CANNON = weapon("rivet_cannon", ColossalWeaponItem.Kind.RIVET_CANNON, 40, "dd",
            p -> p.durability(640).rarity(Rarity.RARE));
    public static final RegistryObject<Item> BOG_LANTERN_FLAIL = weapon("bog_lantern_flail", ColossalWeaponItem.Kind.BOG_LANTERN, 240, "mire",
            p -> p.sword(ModMaterials.LITHITE, 5.0F, -3.0F).rarity(Rarity.RARE));
    public static final RegistryObject<Item> SOLAR_KHOPESH = weapon("solar_khopesh", ColossalWeaponItem.Kind.SOLAR_KHOPESH, 240, "sz",
            p -> p.sword(ModMaterials.LITHITE, 4.5F, -2.5F).rarity(Rarity.RARE));
    public static final RegistryObject<Item> BOARDING_AXE = weapon("boarding_axe", ColossalWeaponItem.Kind.BOARDING_AXE, 100, "dw",
            p -> p.axe(ModMaterials.LITHITE, 6.0F, -3.1F).rarity(Rarity.RARE));
    public static final RegistryObject<Item> JADE_BLOWPIPE = weapon("jade_blowpipe", ColossalWeaponItem.Kind.JADE_BLOWPIPE, 20, "cc",
            p -> p.durability(480).rarity(Rarity.RARE));

    private ColossalGear() {}

    /** Loads the class so every item is queued on ModItems.ITEMS (call before the register is attached). */
    public static void init() {}

    private static TagKey<Item> repair(String set) {
        return TagKey.create(Registries.ITEM, Brasshaven.id(set + "_repair"));
    }

    private static ResourceKey<EquipmentAsset> asset(String set) {
        return ResourceKey.create(EquipmentAssets.ROOT_ID, Brasshaven.id(set));
    }

    private static Map<ArmorType, Integer> defense(int boots, int legs, int chest, int helmet) {
        Map<ArmorType, Integer> map = new EnumMap<>(ArmorType.class);
        map.put(ArmorType.BOOTS, boots);
        map.put(ArmorType.LEGGINGS, legs);
        map.put(ArmorType.CHESTPLATE, chest);
        map.put(ArmorType.HELMET, helmet);
        map.put(ArmorType.BODY, chest);
        return map;
    }

    private static RegistryObject<Item> armor(String name, ArmorMaterial material, ArmorType type, ColossalSet set) {
        return add(name, () -> {
            Item.Properties p = new Item.Properties().setId(ModItems.ITEMS.key(name)).humanoidArmor(material, type).rarity(Rarity.RARE);
            return new ColossalArmorItem(set == ColossalSet.SUN_PRIEST ? p.fireResistant() : p, set);
        });
    }

    private static RegistryObject<Item> weapon(String name, ColossalWeaponItem.Kind kind, int cooldown, String structure,
                                               UnaryOperator<Item.Properties> props) {
        return add(name, () -> new ColossalWeaponItem(props.apply(new Item.Properties().setId(ModItems.ITEMS.key(name))),
                kind, cooldown, structure));
    }

    private static RegistryObject<Item> add(String name, Supplier<Item> factory) {
        RegistryObject<Item> obj = ModItems.ITEMS.register(name, factory);
        ModItems.ALL.add(obj);
        return obj;
    }
}

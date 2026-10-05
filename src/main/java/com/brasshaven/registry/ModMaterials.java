package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;

import java.util.EnumMap;
import java.util.Map;

/** Tool and armor tiers. Each tier is repaired with the material of its dimension. */
public final class ModMaterials {
    public static final TagKey<Item> MAP_MATERIALS = TagKey.create(Registries.ITEM, Brasshaven.id("map_materials"));
    public static final TagKey<Item> LITHITE_MATERIALS = TagKey.create(Registries.ITEM, Brasshaven.id("lithite_materials"));
    public static final TagKey<Item> EMBER_MATERIALS = TagKey.create(Registries.ITEM, Brasshaven.id("ember_materials"));
    public static final TagKey<Item> VOID_MATERIALS = TagKey.create(Registries.ITEM, Brasshaven.id("void_materials"));

    public static final ToolMaterial CARTOGRAPHER = new ToolMaterial(BlockTags.INCORRECT_FOR_IRON_TOOL, 900, 7.0F, 3.0F, 18, MAP_MATERIALS);
    public static final ToolMaterial LITHITE = new ToolMaterial(BlockTags.INCORRECT_FOR_DIAMOND_TOOL, 1500, 8.5F, 3.5F, 16, LITHITE_MATERIALS);
    public static final ToolMaterial EMBER = new ToolMaterial(BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 1900, 9.0F, 4.5F, 18, EMBER_MATERIALS);
    public static final ToolMaterial VOID = new ToolMaterial(BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 2400, 10.0F, 5.0F, 22, VOID_MATERIALS);

    public static final ResourceKey<EquipmentAsset> EXPLORER_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Brasshaven.id("explorer"));
    public static final ResourceKey<EquipmentAsset> EMBER_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Brasshaven.id("ember"));
    public static final ResourceKey<EquipmentAsset> VOID_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Brasshaven.id("void"));

    public static final ArmorMaterial EXPLORER_ARMOR = new ArmorMaterial(22, defense(2, 5, 6, 2), 18,
            SoundEvents.ARMOR_EQUIP_LEATHER, 1.0F, 0.0F, MAP_MATERIALS, EXPLORER_ASSET);
    public static final ArmorMaterial EMBER_ARMOR = new ArmorMaterial(34, defense(3, 6, 8, 3), 16,
            SoundEvents.ARMOR_EQUIP_NETHERITE, 2.5F, 0.05F, EMBER_MATERIALS, EMBER_ASSET);
    public static final ArmorMaterial VOID_ARMOR = new ArmorMaterial(38, defense(3, 7, 8, 3), 22,
            SoundEvents.ARMOR_EQUIP_DIAMOND, 3.0F, 0.1F, VOID_MATERIALS, VOID_ASSET);

    private static Map<ArmorType, Integer> defense(int boots, int legs, int chest, int helmet) {
        Map<ArmorType, Integer> map = new EnumMap<>(ArmorType.class);
        map.put(ArmorType.BOOTS, boots);
        map.put(ArmorType.LEGGINGS, legs);
        map.put(ArmorType.CHESTPLATE, chest);
        map.put(ArmorType.HELMET, helmet);
        map.put(ArmorType.BODY, chest);
        return map;
    }

    private ModMaterials() {}
}

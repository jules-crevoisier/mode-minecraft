package com.brasshaven.registry;

import com.brasshaven.Brasshaven;
import com.brasshaven.block.GlowAnemoneBlock;
import com.brasshaven.block.PearlOysterBlock;
import com.brasshaven.item.DivingHelmetItem;
import com.brasshaven.item.TooltipBlockItem;
import com.brasshaven.item.TooltipItem;
import com.brasshaven.world.BubbleVentFeature;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.MobBucketItem;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;

/**
 * Living oceans: the blocks, items, spawn eggs and the world feature of the sea update (creatures are declared in
 * ModEntities with the others). Names, textures and recipes come from tools/wf/ocean.py.
 */
public final class ModOcean {
    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(ForgeRegistries.FEATURES, Brasshaven.MODID);

    // ---- materials of the diving gear
    public static final TagKey<Item> DIVING_REPAIR = TagKey.create(Registries.ITEM, Brasshaven.id("diving_repair_materials"));
    public static final ResourceKey<EquipmentAsset> DIVING_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, Brasshaven.id("diving"));
    public static final ArmorMaterial DIVING_ARMOR = new ArmorMaterial(20, defense(1, 0, 0, 3), 12,
            SoundEvents.ARMOR_EQUIP_IRON, 0.5F, 0.0F, DIVING_REPAIR, DIVING_ASSET);

    // ---- blocks
    public static final RegistryObject<Block> GLOW_ANEMONE = block("glow_anemone", GlowAnemoneBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PINK).noCollision().instabreak()
                    .sound(SoundType.WET_GRASS).lightLevel(s -> 10).pushReaction(PushReaction.DESTROY));
    public static final RegistryObject<Block> PEARL_OYSTER = block("pearl_oyster", PearlOysterBlock::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.TERRACOTTA_LIGHT_GRAY).strength(1.0F)
                    .sound(SoundType.BONE_BLOCK).noOcclusion().randomTicks());
    public static final RegistryObject<Block> JELLY_LAMP = block("jelly_lamp", Block::new,
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_LIGHT_BLUE).strength(0.4F)
                    .sound(SoundType.HONEY_BLOCK).lightLevel(s -> 15).noOcclusion()
                    .isViewBlocking((s, l, p) -> false));

    // ---- items
    public static final RegistryObject<Item> GLOW_JELLY = item("glow_jelly", TooltipItem::new, p -> p);
    public static final RegistryObject<Item> PEARL = item("pearl", TooltipItem::new, p -> p.rarity(Rarity.UNCOMMON));
    public static final RegistryObject<Item> SERPENT_SCALE = item("serpent_scale", TooltipItem::new, p -> p.rarity(Rarity.RARE));
    public static final RegistryObject<Item> DIVING_HELMET = item("diving_helmet", DivingHelmetItem::new,
            p -> p.humanoidArmor(DIVING_ARMOR, ArmorType.HELMET).rarity(Rarity.UNCOMMON)
                    .attributes(DIVING_ARMOR.createAttributes(ArmorType.HELMET).withModifierAdded(Attributes.SUBMERGED_MINING_SPEED,
                            new AttributeModifier(Brasshaven.id("diving_helmet"), 0.8, AttributeModifier.Operation.ADD_VALUE),
                            EquipmentSlotGroup.HEAD)));
    public static final RegistryObject<Item> FLIPPERS = item("flippers", TooltipItem::new,
            p -> p.humanoidArmor(DIVING_ARMOR, ArmorType.BOOTS)
                    .attributes(DIVING_ARMOR.createAttributes(ArmorType.BOOTS).withModifierAdded(Attributes.WATER_MOVEMENT_EFFICIENCY,
                            new AttributeModifier(Brasshaven.id("flippers"), 0.66, AttributeModifier.Operation.ADD_VALUE),
                            EquipmentSlotGroup.FEET)));
    public static final RegistryObject<Item> REEF_FISH_BUCKET = item("reef_fish_bucket",
            p -> new MobBucketItem(ModEntities.REEF_FISH.get(), Fluids.WATER, SoundEvents.BUCKET_EMPTY_FISH, p),
            p -> p.stacksTo(1));

    // ---- spawn eggs
    public static final RegistryObject<Item> GLOW_JELLYFISH_SPAWN_EGG = egg("glow_jellyfish_spawn_egg", ModEntities.GLOW_JELLYFISH);
    public static final RegistryObject<Item> REEF_FISH_SPAWN_EGG = egg("reef_fish_spawn_egg", ModEntities.REEF_FISH);
    public static final RegistryObject<Item> MANTA_RAY_SPAWN_EGG = egg("manta_ray_spawn_egg", ModEntities.MANTA_RAY);
    public static final RegistryObject<Item> SEA_SERPENT_SPAWN_EGG = egg("sea_serpent_spawn_egg", ModEntities.SEA_SERPENT);
    public static final RegistryObject<Item> WHALE_SPAWN_EGG = egg("whale_spawn_egg", ModEntities.WHALE);

    // ---- world features
    public static final RegistryObject<Feature<NoneFeatureConfiguration>> BUBBLE_VENT = FEATURES.register("bubble_vent",
            () -> new BubbleVentFeature(NoneFeatureConfiguration.CODEC));

    private ModOcean() {}

    /** Forces class initialisation so every entry is queued on the deferred registers. */
    public static void init() {}

    private static Map<ArmorType, Integer> defense(int boots, int legs, int chest, int helmet) {
        Map<ArmorType, Integer> map = new EnumMap<>(ArmorType.class);
        map.put(ArmorType.BOOTS, boots);
        map.put(ArmorType.LEGGINGS, legs);
        map.put(ArmorType.CHESTPLATE, chest);
        map.put(ArmorType.HELMET, helmet);
        map.put(ArmorType.BODY, chest);
        return map;
    }

    private static <B extends Block> RegistryObject<Block> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                                BlockBehaviour.Properties props) {
        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> factory.apply(props.setId(ModBlocks.BLOCKS.key(name))));
        RegistryObject<Item> item = ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),
                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix()));
        ModItems.ALL.add(item);
        return block;
    }

    private static RegistryObject<Item> item(String name, Function<Item.Properties, ? extends Item> factory,
                                             Function<Item.Properties, Item.Properties> props) {
        RegistryObject<Item> obj = ModItems.ITEMS.register(name,
                () -> factory.apply(props.apply(new Item.Properties().setId(ModItems.ITEMS.key(name)))));
        ModItems.ALL.add(obj);
        return obj;
    }

    private static RegistryObject<Item> egg(String name, Supplier<? extends EntityType<?>> type) {
        RegistryObject<Item> obj = ModItems.ITEMS.register(name,
                () -> new SpawnEggItem(new Item.Properties().setId(ModItems.ITEMS.key(name)).spawnEgg(type.get())));
        ModItems.ALL.add(obj);
        return obj;
    }
}

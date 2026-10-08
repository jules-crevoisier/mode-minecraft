package com.brasshaven.relic;

import com.brasshaven.Brasshaven;
import com.brasshaven.item.BossWeaponItem;
import com.brasshaven.registry.ModItems;
import com.brasshaven.registry.ModMaterials;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraftforge.registries.RegistryObject;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import java.util.function.UnaryOperator;

/**
 * Relic gear of the colossal structures (tools/wf/relics.py: names, art, loot): four armour sets, eight weapons with a
 * right-click ability (the boss weapon machinery plus a signature effect, {@link RelicWeaponItem}) and six accessories.
 * All loot-only. Set bonuses and worn effects live in {@link RelicEvents}.
 */
public final class RelicGear {
    // ---- armour materials (repaired with the tag brasshaven:<set>_repair)
    public static final ArmorMaterial FROSTPLATE_ARMOR = new ArmorMaterial(36, defense(3, 6, 8, 3), 14,
            SoundEvents.ARMOR_EQUIP_IRON, 2.5F, 0.1F, repair("frostplate"), asset("frostplate"));
    public static final ArmorMaterial MAGMAGUARD_ARMOR = new ArmorMaterial(36, defense(3, 6, 8, 3), 12,
            SoundEvents.ARMOR_EQUIP_NETHERITE, 2.0F, 0.15F, repair("magmaguard"), asset("magmaguard"));
    public static final ArmorMaterial TIDEWARDEN_ARMOR = new ArmorMaterial(30, defense(2, 5, 7, 3), 18,
            SoundEvents.ARMOR_EQUIP_CHAIN, 1.5F, 0.0F, repair("tidewarden"), asset("tidewarden"));
    public static final ArmorMaterial WINDROBE_ARMOR = new ArmorMaterial(24, defense(2, 4, 5, 2), 22,
            SoundEvents.ARMOR_EQUIP_LEATHER, 0.0F, 0.0F, repair("windrobe"), asset("windrobe"));

    // ---- Jarl's Frostplate (Glacier Hall)
    public static final RegistryObject<Item> FROSTPLATE_HELMET = armor("frostplate_helmet", FROSTPLATE_ARMOR, ArmorType.HELMET, "glacier");
    public static final RegistryObject<Item> FROSTPLATE_CHESTPLATE = armor("frostplate_chestplate", FROSTPLATE_ARMOR, ArmorType.CHESTPLATE, "glacier");
    public static final RegistryObject<Item> FROSTPLATE_LEGGINGS = armor("frostplate_leggings", FROSTPLATE_ARMOR, ArmorType.LEGGINGS, "glacier");
    public static final RegistryObject<Item> FROSTPLATE_BOOTS = armor("frostplate_boots", FROSTPLATE_ARMOR, ArmorType.BOOTS, "glacier");
    // ---- Caldera Magmaguard (Caldera Ringwall)
    public static final RegistryObject<Item> MAGMAGUARD_HELMET = armor("magmaguard_helmet", MAGMAGUARD_ARMOR, ArmorType.HELMET, "caldera");
    public static final RegistryObject<Item> MAGMAGUARD_CHESTPLATE = armor("magmaguard_chestplate", MAGMAGUARD_ARMOR, ArmorType.CHESTPLATE, "caldera");
    public static final RegistryObject<Item> MAGMAGUARD_LEGGINGS = armor("magmaguard_leggings", MAGMAGUARD_ARMOR, ArmorType.LEGGINGS, "caldera");
    public static final RegistryObject<Item> MAGMAGUARD_BOOTS = armor("magmaguard_boots", MAGMAGUARD_ARMOR, ArmorType.BOOTS, "caldera");
    // ---- Tidewarden (Tidal Abbey)
    public static final RegistryObject<Item> TIDEWARDEN_HELMET = armor("tidewarden_helmet", TIDEWARDEN_ARMOR, ArmorType.HELMET, "abbey");
    public static final RegistryObject<Item> TIDEWARDEN_CHESTPLATE = armor("tidewarden_chestplate", TIDEWARDEN_ARMOR, ArmorType.CHESTPLATE, "abbey");
    public static final RegistryObject<Item> TIDEWARDEN_LEGGINGS = armor("tidewarden_leggings", TIDEWARDEN_ARMOR, ArmorType.LEGGINGS, "abbey");
    public static final RegistryObject<Item> TIDEWARDEN_BOOTS = armor("tidewarden_boots", TIDEWARDEN_ARMOR, ArmorType.BOOTS, "abbey");
    // ---- Pilgrim's Windrobes (Pilgrim's Ascent)
    public static final RegistryObject<Item> WINDROBE_HELMET = armor("windrobe_helmet", WINDROBE_ARMOR, ArmorType.HELMET, "ascent");
    public static final RegistryObject<Item> WINDROBE_CHESTPLATE = armor("windrobe_chestplate", WINDROBE_ARMOR, ArmorType.CHESTPLATE, "ascent");
    public static final RegistryObject<Item> WINDROBE_LEGGINGS = armor("windrobe_leggings", WINDROBE_ARMOR, ArmorType.LEGGINGS, "ascent");
    public static final RegistryObject<Item> WINDROBE_BOOTS = armor("windrobe_boots", WINDROBE_ARMOR, ArmorType.BOOTS, "ascent");

    // ---- weapons: ability, power, size, cooldown, particle, flags, then the signature
    public static final RegistryObject<Item> MAGMA_MAUL = weapon("magma_maul", "caldera",
            p -> p.sword(ModMaterials.EMBER, 7.0F, -3.3F).rarity(Rarity.EPIC).fireResistant(),
            BossWeaponItem.Ability.ERUPT, 11F, 10F, 90, () -> ParticleTypes.FLAME, BossWeaponItem.FIRE,
            sig(false, false, () -> new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 120, 0)));
    public static final RegistryObject<Item> BASTION_CANNON = weapon("bastion_cannon", "caldera",
            p -> p.sword(ModMaterials.LITHITE, 4.0F, -2.8F).rarity(Rarity.RARE),
            BossWeaponItem.Ability.BEAM, 12F, 18F, 80, () -> ParticleTypes.LARGE_SMOKE, BossWeaponItem.LIFT,
            sig(false, true));
    public static final RegistryObject<Item> RIMEFANG_SPEAR = weapon("rimefang_spear", "glacier",
            p -> p.sword(ModMaterials.LITHITE, 5.0F, -2.7F).rarity(Rarity.EPIC),
            BossWeaponItem.Ability.ROOT, 8F, 6F, 90, () -> ParticleTypes.SNOWFLAKE, BossWeaponItem.SLOW,
            sig(true, false));
    public static final RegistryObject<Item> OATHBREAKER = weapon("oathbreaker", "kg",
            p -> p.sword(ModMaterials.LITHITE, 7.0F, -3.0F).rarity(Rarity.EPIC),
            BossWeaponItem.Ability.LEAP, 11F, 4.5F, 70, () -> ParticleTypes.ENCHANTED_HIT, BossWeaponItem.WEAK,
            sig(false, false, () -> new MobEffectInstance(MobEffects.STRENGTH, 100, 0)));
    public static final RegistryObject<Item> TOLL_BILLHOOK = weapon("toll_billhook", "kg",
            p -> p.sword(ModMaterials.LITHITE, 5.0F, -2.8F).rarity(Rarity.RARE),
            BossWeaponItem.Ability.HOOK, 8F, 14F, 70, () -> ParticleTypes.WAX_ON, BossWeaponItem.LIFESTEAL,
            sig(false, false, () -> new MobEffectInstance(MobEffects.ABSORPTION, 120, 0)));
    public static final RegistryObject<Item> UNDERTOW_GLAIVE = weapon("undertow_glaive", "abbey",
            p -> p.sword(ModMaterials.LITHITE, 5.0F, -2.6F).rarity(Rarity.EPIC),
            BossWeaponItem.Ability.DASH, 9F, 9F, 60, () -> ParticleTypes.SPLASH, BossWeaponItem.SLOW,
            sig(false, false, () -> new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 200, 0),
                    () -> new MobEffectInstance(MobEffects.WATER_BREATHING, 200, 0)));
    public static final RegistryObject<Item> GALE_STAFF = weapon("gale_staff", "ascent",
            p -> p.durability(700).rarity(Rarity.EPIC),
            BossWeaponItem.Ability.BLINK, 7F, 10F, 50, () -> ParticleTypes.CLOUD, BossWeaponItem.LIFT,
            sig(false, false, () -> new MobEffectInstance(MobEffects.SLOW_FALLING, 80, 0),
                    () -> new MobEffectInstance(MobEffects.JUMP_BOOST, 100, 1)));
    public static final RegistryObject<Item> STARFALL_LANCE = weapon("starfall_lance", "halo",
            p -> p.sword(ModMaterials.VOID, 5.0F, -2.7F).rarity(Rarity.EPIC).fireResistant(),
            BossWeaponItem.Ability.WAVE, 10F, 6.5F, 75, () -> ParticleTypes.END_ROD, BossWeaponItem.BLIND,
            sig(false, false, () -> new MobEffectInstance(MobEffects.SPEED, 100, 0)));

    // ---- accessories (slot tags from tools/wf/accessories.py; effects in RelicEvents)
    public static final RegistryObject<Item> JARL_MANTLE = accessory("jarl_mantle", "glacier", Rarity.RARE);
    public static final RegistryObject<Item> EMBER_SIGNET = accessory("ember_signet", "caldera", Rarity.RARE);
    public static final RegistryObject<Item> PILGRIM_BAND = accessory("pilgrim_band", "ascent", Rarity.UNCOMMON);
    public static final RegistryObject<Item> TIDE_PENDANT = accessory("tide_pendant", "abbey", Rarity.RARE);
    public static final RegistryObject<Item> HALO_LOCKET = accessory("halo_locket", "halo", Rarity.EPIC);
    public static final RegistryObject<Item> OATH_GIRDLE = accessory("oath_girdle", "kg", Rarity.RARE);

    private RelicGear() {}

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

    @SafeVarargs
    private static RelicWeaponItem.Signature sig(boolean freeze, boolean recoil, Supplier<MobEffectInstance>... self) {
        return new RelicWeaponItem.Signature(List.of(self), freeze, recoil);
    }

    private static RegistryObject<Item> armor(String name, ArmorMaterial material, ArmorType type, String structure) {
        boolean hot = structure.equals("caldera");
        return add(name, () -> {
            Item.Properties p = new Item.Properties().setId(ModItems.ITEMS.key(name)).humanoidArmor(material, type).rarity(Rarity.RARE);
            return new RelicItem(hot ? p.fireResistant() : p, structure);
        });
    }

    private static RegistryObject<Item> weapon(String name, String structure, UnaryOperator<Item.Properties> props,
                                               BossWeaponItem.Ability ability, float power, float size, int cooldown,
                                               Supplier<ParticleOptions> particle, int flags, RelicWeaponItem.Signature sig) {
        return add(name, () -> new RelicWeaponItem(props.apply(new Item.Properties().setId(ModItems.ITEMS.key(name))),
                ability, power, size, cooldown, particle.get(), flags, structure, sig));
    }

    private static RegistryObject<Item> accessory(String name, String structure, Rarity rarity) {
        return add(name, () -> new RelicItem(new Item.Properties().setId(ModItems.ITEMS.key(name)).stacksTo(1).rarity(rarity)
                .fireResistant(), structure));
    }

    private static RegistryObject<Item> add(String name, Supplier<Item> factory) {
        RegistryObject<Item> obj = ModItems.ITEMS.register(name, factory);
        ModItems.ALL.add(obj);
        return obj;
    }
}

"""Metals, gems and their gear: one table drives Java registration, textures, models, recipes, loot,
tags, worldgen and translations (like decor.py for building blocks).

Steampunk: zinc + copper make brass. Fantasy: mithril (deep), aether crystal (magic), orichalcum (Nether).
"""

# palette: (light, mid, dark, outline) like sprites.MATERIALS
PALETTES = {
    "zinc": ((206, 214, 220), (160, 170, 180), (110, 118, 130), (46, 50, 58)),
    "brass": ((246, 214, 122), (200, 158, 70), (138, 100, 40), (58, 40, 16)),
    "mithril": ((214, 240, 255), (150, 200, 232), (86, 132, 176), (30, 50, 78)),
    "orichalcum": ((255, 190, 140), (226, 120, 70), (150, 66, 40), (64, 24, 14)),
    "aether": ((200, 255, 250), (80, 230, 220), (30, 150, 170), (12, 60, 76)),
    "arcane": ((176, 140, 232), (118, 82, 186), (72, 44, 128), (30, 16, 56)),
}

# id -> spec
#   ore: None | dict(hosts=[stone|deepslate|netherrack], y=(min, max), shape=uniform|trapezoid, count, size,
#                    drop=raw|gem, xp=(a, b), tool=stone|iron|diamond)
#   items: which item forms exist; tools: ToolMaterial numbers or None; armor: ArmorMaterial numbers or None
METALS = {
    "zinc": dict(
        en="Zinc", fr="zinc", palette="zinc",
        ore=dict(hosts=["stone", "deepslate"], y=(-16, 96), shape="trapezoid", count=12, size=9, drop="raw", tool="stone"),
        items=["raw", "ingot", "nugget"], blocks=["block", "raw_block"], tools=None, armor=None),
    "brass": dict(
        en="Brass", fr="laiton", palette="brass", ore=None,
        items=["ingot", "nugget"], blocks=["block"],
        # alloy: 3 copper + 1 zinc -> 4 brass (crafting) ; also smelted in a blast furnace from the mix
        tools=dict(incorrect="INCORRECT_FOR_IRON_TOOL", durability=620, speed=7.0, damage=2.5, enchant=20),
        armor=dict(durability=20, defense=(2, 5, 6, 2), enchant=20, toughness=0.5, knockback=0.0,
                   sound="ARMOR_EQUIP_IRON",
                   bonus=("Set: night vision and +20% mining speed (brass goggles).",
                          "Ensemble : vision nocturne et +20 % de vitesse de minage (lunettes en laiton).")),
        names=dict(helmet=("Brass Goggles", "Lunettes en laiton"))),
    "mithril": dict(
        en="Mithril", fr="mithril", palette="mithril",
        ore=dict(hosts=["deepslate"], y=(-64, -8), shape="trapezoid", count=5, size=6, drop="raw", tool="iron"),
        items=["raw", "ingot", "nugget"], blocks=["block", "raw_block"],
        tools=dict(incorrect="INCORRECT_FOR_DIAMOND_TOOL", durability=2100, speed=9.5, damage=3.5, enchant=22),
        armor=dict(durability=40, defense=(3, 6, 8, 3), enchant=22, toughness=2.5, knockback=0.05,
                   sound="ARMOR_EQUIP_CHAIN",
                   bonus=("Set: +4 max health and +10% speed; feather-light.",
                          "Ensemble : +4 points de vie max et +10 % de vitesse ; léger comme une plume."))),
    "orichalcum": dict(
        en="Orichalcum", fr="orichalque", palette="orichalcum",
        ore=dict(hosts=["netherrack"], y=(10, 110), shape="uniform", count=10, size=6, drop="raw", tool="iron"),
        items=["raw", "ingot", "nugget"], blocks=["block", "raw_block"], tools=None, armor=None),
    "aether": dict(
        en="Aether", fr="d'éther", palette="aether", gem_name=("Aether Crystal", "Cristal d'éther"),
        ore=dict(hosts=["stone", "deepslate"], y=(-48, 32), shape="trapezoid", count=4, size=5, drop="gem",
                 xp=(3, 7), tool="iron", light=7),
        items=["gem"], blocks=["block"], tools=None,
        armor=dict(durability=36, defense=(3, 7, 8, 3), enchant=24, toughness=2.0, knockback=0.0,
                   sound="ARMOR_EQUIP_DIAMOND",
                   bonus=("Set: +75 max mana, mana regenerates twice as fast, no fall damage.",
                          "Ensemble : +75 de mana max, recharge deux fois plus rapide, aucun dégât de chute."))),
    "arcane": dict(
        en="Arcanist", fr="d'arcaniste", palette="arcane", ore=None, cloth=True,
        items=["cloth"], blocks=[], tools=None,
        armor=dict(durability=16, defense=(1, 3, 4, 1), enchant=30, toughness=0.0, knockback=0.0,
                   sound="ARMOR_EQUIP_LEATHER",
                   bonus=("Set: +100 max mana and spells 25% stronger.",
                          "Ensemble : +100 de mana max et sorts 25 % plus puissants.")),
        names=dict(helmet=("Arcanist Hood", "Capuche d'arcaniste"), chestplate=("Arcanist Robe", "Robe d'arcaniste"),
                   leggings=("Arcanist Breeches", "Chausses d'arcaniste"), boots=("Arcanist Slippers", "Chaussons d'arcaniste"))),
}

TOOL_KINDS = {  # kind -> (damage, speed)
    "sword": (3.0, -2.4), "pickaxe": (1.0, -2.8), "axe": (6.0, -3.1), "shovel": (1.5, -3.0), "hoe": (-2.0, -1.0),
}
TOOL_NAMES = {"sword": ("Sword", "Épée"), "pickaxe": ("Pickaxe", "Pioche"), "axe": ("Axe", "Hache"),
              "shovel": ("Shovel", "Pelle"), "hoe": ("Hoe", "Houe")}
ARMOR_PIECES = {"helmet": ("Helmet", "Casque"), "chestplate": ("Chestplate", "Plastron"),
                "leggings": ("Leggings", "Jambières"), "boots": ("Boots", "Bottes")}


def item_ids(mid):
    m = METALS[mid]
    out = {}
    for form in m["items"]:
        if form == "raw":
            out[f"raw_{mid}"] = ("raw", (f"Raw {m['en']}", f"{m['fr'].capitalize()} brut" if m['fr'][0] != 'd' else f"{m['en']} brut"))
        elif form == "ingot":
            out[f"{mid}_ingot"] = ("ingot", (f"{m['en']} Ingot", f"Lingot de {m['fr']}"))
        elif form == "nugget":
            out[f"{mid}_nugget"] = ("nugget", (f"{m['en']} Nugget", f"Pépite de {m['fr']}"))
        elif form == "gem":
            out[f"{mid}_crystal"] = ("gem", m["gem_name"])
        elif form == "cloth":
            out[f"{mid}_cloth"] = ("cloth", ("Arcane Cloth", "Étoffe arcanique"))
    return out


def raw_name(mid):
    m = METALS[mid]
    names = {"zinc": ("Raw Zinc", "Zinc brut"), "mithril": ("Raw Mithril", "Mithril brut"),
             "orichalcum": ("Raw Orichalcum", "Orichalque brut")}
    return names.get(mid, (f"Raw {m['en']}", f"{m['en']} brut"))


def block_ids(mid):
    m = METALS[mid]
    out = {}
    ore = m.get("ore")
    if ore:
        for host in ore["hosts"]:
            bid = f"{mid}_ore" if host == "stone" else f"{host}_{mid}_ore" if host == "deepslate" else f"nether_{mid}_ore"
            label = {"stone": (f"{m['en']} Ore", f"Minerai de {m['fr']}"),
                     "deepslate": (f"Deepslate {m['en']} Ore", f"Minerai de {m['fr']} des abîmes"),
                     "netherrack": (f"Nether {m['en']} Ore", f"Minerai de {m['fr']} du Nether")}[host]
            out[bid] = ("ore", host, label)
    for b in m["blocks"]:
        if b == "block":
            out[f"{mid}_block"] = ("storage", None, (f"Block of {m['en']}", f"Bloc de {m['fr']}"))
        elif b == "raw_block":
            out[f"raw_{mid}_block"] = ("raw_storage", None, (f"Block of Raw {m['en']}", f"Bloc de {m['fr']} brut"))
    return out


def gear_ids(mid):
    m = METALS[mid]
    out = {}
    if m.get("tools"):
        for kind, (en, fr) in TOOL_NAMES.items():
            out[f"{mid}_{kind}"] = ("tool", kind, (f"{m['en']} {en}", f"{fr} en {m['fr']}"))
    if m.get("armor"):
        names = m.get("names", {})
        for piece, (en, fr) in ARMOR_PIECES.items():
            label = names.get(piece, (f"{m['en']} {en}", f"{fr} en {m['fr']}" if mid not in ("aether", "arcane")
                                      else f"{fr} {m['fr']}"))
            out[f"{mid}_{piece}"] = ("armor", piece, label)
    return out


def all_item_ids():
    ids = set()
    for mid in METALS:
        ids |= set(item_ids(mid)) | set(block_ids(mid)) | set(gear_ids(mid))
    return ids


def lang():
    en, fr = {}, {}
    for mid, m in METALS.items():
        for iid, (form, (ne, nf)) in item_ids(mid).items():
            if form == "raw":
                ne, nf = raw_name(mid)
            en[f"item.brasshaven.{iid}"], fr[f"item.brasshaven.{iid}"] = ne, nf
        for bid, (_kind, _host, (ne, nf)) in block_ids(mid).items():
            en[f"block.brasshaven.{bid}"], fr[f"block.brasshaven.{bid}"] = ne, nf
        for gid, (_kind, _what, (ne, nf)) in gear_ids(mid).items():
            en[f"item.brasshaven.{gid}"], fr[f"item.brasshaven.{gid}"] = ne, nf
            if m.get("armor") and _kind == "armor":
                be, bf = m["armor"]["bonus"]
                en[f"item.brasshaven.{gid}.desc"], fr[f"item.brasshaven.{gid}.desc"] = be, bf
    return en, fr


def java():
    L = ["package com.brasshaven.generated;", "",
         "import com.brasshaven.Brasshaven;",
         "import com.brasshaven.item.TooltipItem;",
         "import com.brasshaven.item.TooltipBlockItem;",
         "import com.brasshaven.registry.ModBlocks;",
         "import com.brasshaven.registry.ModItems;",
         "import net.minecraft.core.registries.Registries;",
         "import net.minecraft.resources.ResourceKey;",
         "import net.minecraft.sounds.SoundEvents;",
         "import net.minecraft.tags.BlockTags;",
         "import net.minecraft.tags.TagKey;",
         "import net.minecraft.util.valueproviders.UniformInt;",
         "import net.minecraft.world.item.AxeItem;",
         "import net.minecraft.world.item.HoeItem;",
         "import net.minecraft.world.item.Item;",
         "import net.minecraft.world.item.ShovelItem;",
         "import net.minecraft.world.item.ToolMaterial;",
         "import net.minecraft.world.item.equipment.ArmorMaterial;",
         "import net.minecraft.world.item.equipment.ArmorType;",
         "import net.minecraft.world.item.equipment.EquipmentAsset;",
         "import net.minecraft.world.item.equipment.EquipmentAssets;",
         "import net.minecraft.world.level.block.Block;",
         "import net.minecraft.world.level.block.DropExperienceBlock;",
         "import net.minecraft.world.level.block.SoundType;",
         "import net.minecraft.world.level.block.state.BlockBehaviour;",
         "import net.minecraft.world.level.material.MapColor;",
         "import net.minecraftforge.registries.RegistryObject;", "",
         "import java.util.EnumMap;",
         "import java.util.Map;",
         "import java.util.function.Function;", "",
         "/** GENERATED by tools/gen_java.py from tools/wf/metals.py — do not edit by hand. */",
         "public final class GeneratedMetals {"]
    host_props = {
        "stone": "BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3.0F, 3.0F).requiresCorrectToolForDrops()",
        "deepslate": "BlockBehaviour.Properties.of().mapColor(MapColor.DEEPSLATE).strength(4.5F, 3.0F).sound(SoundType.DEEPSLATE).requiresCorrectToolForDrops()",
        "netherrack": "BlockBehaviour.Properties.of().mapColor(MapColor.NETHER).strength(3.0F, 3.0F).sound(SoundType.NETHER_ORE).requiresCorrectToolForDrops()",
    }
    for mid, m in METALS.items():
        C = mid.upper()
        if m.get("tools") or m.get("armor"):
            L.append(f'    public static final TagKey<Item> {C}_REPAIR = TagKey.create(Registries.ITEM, Brasshaven.id("{mid}_repair"));')
        t = m.get("tools")
        if t:
            L.append(f'    public static final ToolMaterial {C}_TOOLS = new ToolMaterial(BlockTags.{t["incorrect"]}, '
                     f'{t["durability"]}, {t["speed"]}F, {t["damage"]}F, {t["enchant"]}, {C}_REPAIR);')
        a = m.get("armor")
        if a:
            b, l, c, h = a["defense"]
            L.append(f'    public static final ResourceKey<EquipmentAsset> {C}_ASSET = ResourceKey.create(EquipmentAssets.ROOT_ID, '
                     f'Brasshaven.id("{mid}"));')
            L.append(f'    public static final ArmorMaterial {C}_ARMOR = new ArmorMaterial({a["durability"]}, defense({b}, {l}, {c}, {h}), '
                     f'{a["enchant"]}, SoundEvents.{a["sound"]}, {a["toughness"]}F, {a["knockback"]}F, {C}_REPAIR, {C}_ASSET);')
        light = m.get("ore", {}).get("light", 0) if m.get("ore") else 0
        for bid, (kind, host, _label) in block_ids(mid).items():
            const = bid.upper()
            if kind == "ore":
                props = host_props[host] + (f".lightLevel(s -> {light})" if light else "")
                if m["ore"].get("xp"):
                    xa, xb = m["ore"]["xp"]
                    L.append(f'    public static final RegistryObject<Block> {const} = block("{bid}", '
                             f'p -> new DropExperienceBlock(UniformInt.of({xa}, {xb}), p), {props});')
                else:
                    L.append(f'    public static final RegistryObject<Block> {const} = block("{bid}", Block::new, {props});')
            else:
                color = {"zinc": "METAL", "brass": "GOLD", "mithril": "COLOR_LIGHT_BLUE", "orichalcum": "COLOR_ORANGE",
                         "aether": "DIAMOND"}.get(mid, "METAL")
                sound = "METAL" if kind == "storage" and mid != "aether" else "AMETHYST" if mid == "aether" else "STONE"
                lv = ".lightLevel(s -> 10)" if mid == "aether" else ""
                L.append(f'    public static final RegistryObject<Block> {const} = block("{bid}", Block::new, '
                         f'BlockBehaviour.Properties.of().mapColor(MapColor.{color}).strength(5.0F, 6.0F)'
                         f'.sound(SoundType.{sound}).requiresCorrectToolForDrops(){lv});')
        for iid in item_ids(mid):
            L.append(f'    public static final RegistryObject<Item> {iid.upper()} = item("{iid}", p -> p);')
        for gid, (kind, what, _label) in gear_ids(mid).items():
            const = gid.upper()
            if kind == "tool":
                dmg, spd = TOOL_KINDS[what]
                if what in ("sword", "pickaxe"):
                    L.append(f'    public static final RegistryObject<Item> {const} = gear("{gid}", TooltipItem::new, '
                             f'p -> p.{what}({C}_TOOLS, {dmg}F, {spd}F));')
                else:
                    cls = {"axe": "AxeItem", "shovel": "ShovelItem", "hoe": "HoeItem"}[what]
                    L.append(f'    public static final RegistryObject<Item> {const} = gear("{gid}", '
                             f'p -> new {cls}({C}_TOOLS, {dmg}F, {spd}F, p), p -> p);')
            else:
                L.append(f'    public static final RegistryObject<Item> {const} = gear("{gid}", TooltipItem::new, '
                         f'p -> p.humanoidArmor({C}_ARMOR, ArmorType.{what.upper()}));')
    L += ["",
          "    /** Forces class initialisation so every block/item is queued on the deferred registers. */",
          "    public static void init() {}", "",
          "    private static Map<ArmorType, Integer> defense(int boots, int legs, int chest, int helmet) {",
          "        Map<ArmorType, Integer> map = new EnumMap<>(ArmorType.class);",
          "        map.put(ArmorType.BOOTS, boots);",
          "        map.put(ArmorType.LEGGINGS, legs);",
          "        map.put(ArmorType.CHESTPLATE, chest);",
          "        map.put(ArmorType.HELMET, helmet);",
          "        map.put(ArmorType.BODY, chest);",
          "        return map;",
          "    }", "",
          "    private static RegistryObject<Block> block(String name, Function<BlockBehaviour.Properties, Block> factory,",
          "                                               BlockBehaviour.Properties props) {",
          "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> factory.apply(props.setId(ModBlocks.BLOCKS.key(name))));",
          "        ModItems.ALL.add(ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),",
          "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
          "        return block;",
          "    }", "",
          "    private static RegistryObject<Item> item(String name, Function<Item.Properties, Item.Properties> props) {",
          "        return gear(name, TooltipItem::new, props);",
          "    }", "",
          "    private static RegistryObject<Item> gear(String name, Function<Item.Properties, ? extends Item> factory,",
          "                                             Function<Item.Properties, Item.Properties> props) {",
          "        RegistryObject<Item> obj = ModItems.ITEMS.register(name, () -> factory.apply(props.apply(",
          "                new Item.Properties().setId(ModItems.ITEMS.key(name)))));",
          "        ModItems.ALL.add(obj);",
          "        return obj;",
          "    }", "",
          "    private GeneratedMetals() {}",
          "}", ""]
    return "\n".join(L)

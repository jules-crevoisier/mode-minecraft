#!/usr/bin/env python3
"""Generate recipes, tags, block/entity loot tables and the lithite ore worldgen."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "src", "main", "resources", "data")
NS = "wayfarers"


def write(rel, obj):
    path = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def rid(x):
    if x.startswith("#"):
        return x if ":" in x else "#minecraft:" + x[1:]
    return x if ":" in x else f"{NS}:{x}" if x in MOD_ITEMS else f"minecraft:{x}"


MOD_ITEMS = {"map_fragment", "lithite_shard", "ancient_ember", "void_shard", "warden_scale", "void_heart",
             "sorting_chest", "waystone", "guild_terminal", "compacting_crate", "explorer_backpack",
             "chisel", "chisel_table", "brass_gear",
             "clockwork_heart"}
MOD_ITEMS |= {f"remembrance_{row[0]}" for row in __import__("wf.bossgear", fromlist=["BOSS_GEAR"]).BOSS_GEAR}
MOD_ITEMS |= __import__("wf.metals", fromlist=["all_item_ids"]).all_item_ids()
MOD_ITEMS |= set(__import__("wf.machines", fromlist=["MACHINES"]).MACHINES)
MOD_ITEMS |= set(__import__("wf.furniture", fromlist=["FURNITURE"]).FURNITURE)
MOD_ITEMS |= __import__("wf.gadgets", fromlist=["MOD_ITEMS"]).MOD_ITEMS
MOD_ITEMS |= {"builder_wand", "master_builder_wand", "wayfarer_manual", "fire_staff", "frost_staff", "thunder_staff",
              "healing_staff", "levitation_wand", "ward_orb", "steam_cane", "arcane_ring", "mana_amulet", "oblivion_vial"}


def shaped(name, pattern, key, count=1, category="misc"):
    write(f"{NS}/recipe/{name}.json", {
        "type": "minecraft:crafting_shaped",
        "category": category,
        "pattern": pattern,
        "key": {k: rid(v) for k, v in key.items()},
        "result": {"id": f"{NS}:{name}", "count": count},
    })


def shapeless(name, ingredients, count=1, category="misc"):  # noqa: F811
    write(f"{NS}/recipe/{name}.json", {
        "type": "minecraft:crafting_shapeless",
        "category": category,
        "ingredients": [rid(i) for i in ingredients],
        "result": {"id": f"{NS}:{name}", "count": count},
    })


def armor_set(prefix, material, extra=None):
    m = {"M": material}
    if extra:
        m.update(extra)
    pats = {
        "helmet": ["MXM", "M M"] if extra else ["MMM", "M M"],
        "chestplate": ["M M", "MXM", "MMM"] if extra else ["M M", "MMM", "MMM"],
        "leggings": ["MXM", "M M", "M M"] if extra else ["MMM", "M M", "M M"],
        "boots": ["M M", "X X"] if extra else ["M M", "M M"],
    }
    for piece, pat in pats.items():
        shaped(f"{prefix}_{piece}", pat, m, category="equipment")


def recipes():
    # automatons: brass gears, and the Clockwork Heart that wakes a Brass Golem (two stacked Blocks of Brass)
    shaped("brass_gear", [" N ", "NIN", " N "], {"N": "brass_nugget", "I": "brass_ingot"}, count=2)
    shaped("clockwork_heart", [" G ", "IRI", " C "], {"G": "brass_gear", "I": "brass_ingot", "R": "redstone_block",
                                                      "C": "clock"})
    shaped("waystone", [" E ", "MCM", "SSS"], {"E": "ender_pearl", "M": "map_fragment", "C": "compass", "S": "stone_bricks"})
    shaped("sorting_chest", ["PHP", "PCP", "PPP"], {"P": "#planks", "H": "hopper", "C": "chest"})
    shaped("compacting_crate", ["PIP", "IBI", "PIP"], {"P": "#planks", "I": "iron_ingot", "B": "barrel"})
    shaped("guild_terminal", ["GMG", "PCP", "PRP"], {"G": "gold_ingot", "M": "map_fragment", "P": "#planks",
                                                    "C": "chest", "R": "redstone"})
    shaped("travel_backpack", ["LSL", "LCL", "LLL"], {"L": "leather", "S": "string", "C": "chest"}, category="equipment")
    # transmute keeps the bag's contents (container component) when it is upgraded
    write(f"{NS}/recipe/explorer_backpack.json", {"type": "minecraft:crafting_transmute", "category": "equipment",
                                                 "input": f"{NS}:travel_backpack", "material": f"{NS}:brass_ingot",
                                                 "result": {"id": f"{NS}:explorer_backpack"}})
    shaped("magnet_ring", ["MRM", "I I", " I "], {"M": "map_fragment", "R": "redstone", "I": "iron_ingot"}, category="equipment")
    shaped("structure_compass", [" M ", "MCM", " M "], {"M": "map_fragment", "C": "compass"}, category="equipment")
    shapeless("recall_scroll", ["paper", "map_fragment", "ender_pearl"], count=2)
    shapeless("wayfarer_atlas", ["book", "map_fragment"])
    shapeless("wayfarer_manual", ["book", "feather"])
    shapeless("builder_wand", ["stick", "gold_ingot", "gold_ingot", "amethyst_shard"])
    shapeless("fire_staff", ["stick", "blaze_powder", "blaze_powder", "amethyst_shard", "gold_ingot"])
    shapeless("frost_staff", ["stick", "packed_ice", "snowball", "amethyst_shard", "gold_ingot"])
    shapeless("thunder_staff", ["stick", "copper_ingot", "copper_ingot", "lightning_rod", "amethyst_shard"])
    shapeless("healing_staff", ["stick", "glistering_melon_slice", "ghast_tear", "amethyst_shard", "gold_ingot"])
    shapeless("levitation_wand", ["stick", "phantom_membrane", "feather", "amethyst_shard"])
    shapeless("ward_orb", ["amethyst_shard", "amethyst_shard", "iron_ingot", "lapis_lazuli", "lithite_shard"])
    shapeless("steam_cane", ["stick", "copper_ingot", "copper_ingot", "campfire", "iron_ingot"])
    shapeless("arcane_ring", ["gold_ingot", "gold_ingot", "amethyst_shard", "lapis_lazuli"])
    shapeless("mana_amulet", ["gold_ingot", "string", "amethyst_shard", "amethyst_shard", "lithite_shard"])
    shapeless("oblivion_vial", ["glass_bottle", "ghast_tear", "amethyst_shard"])
    shapeless("master_builder_wand", ["builder_wand", "lithite_shard", "lithite_shard", "diamond"])
    # building tools (Lot 2e): the chisel cycles block variants (wf/chisel.py), the table converts whole stacks
    shaped("chisel", ["  I", " B ", "S  "], {"I": "iron_ingot", "B": "brass_ingot", "S": "stick"}, category="equipment")
    shaped("chisel_table", ["BCB", "PPP", "P P"], {"B": "brass_ingot", "C": "chisel", "P": "#planks"})
    # tier 1 — map fragments (Overworld)
    shaped("cartographer_blade", [" I ", "MIM", " S "], {"I": "iron_ingot", "M": "map_fragment", "S": "stick"}, category="equipment")
    armor_set("explorer", "leather", {"X": "map_fragment"})
    # tier 2 — lithite (underground)
    shaped("telluric_hammer", ["LLL", "LSL", " S "], {"L": "lithite_shard", "S": "stick"}, category="equipment")
    shaped("frost_blade", [" L ", "PLP", " S "], {"L": "lithite_shard", "P": "packed_ice", "S": "stick"}, category="equipment")
    shaped("boomerang", ["PPL", "  P"], {"P": "#planks", "L": "lithite_shard"}, category="equipment")
    shaped("excavator_pickaxe", ["LLL", " S ", " S "], {"L": "lithite_shard", "S": "stick"}, category="equipment")
    shaped("lumber_axe", ["LL", "LS", " S"], {"L": "lithite_shard", "S": "stick"}, category="equipment")
    shaped("light_staff", [" G ", " L ", " S "], {"G": "glowstone", "L": "lithite_shard", "S": "stick"}, category="equipment")
    # tier 3 — ancient ember (Nether)
    shaped("ember_scythe", ["EEE", " BE", "B  "], {"E": "ancient_ember", "B": "blaze_rod"}, category="equipment")
    shaped("storm_staff", [" T ", "EBE", " B "], {"T": "lightning_rod", "E": "ancient_ember", "B": "blaze_rod"}, category="equipment")
    armor_set("ember", "ancient_ember")
    # tier 4 — void shards (End)
    shaped("void_spear", ["  V", " R ", "R  "], {"V": "void_shard", "R": "end_rod"}, category="equipment")
    armor_set("void", "void_shard")
    # steam gadgets (wf/gadgets.py)
    from wf import gadgets
    gadgets.recipes(shaped, shapeless)
    # boss weapons: remembrance + four tier materials + two diamonds
    from wf.bossgear import BOSS_GEAR, TIER_MATERIAL, remembrance_id
    for row in BOSS_GEAR:
        boss, tier, wid = row[:3]
        shapeless(wid, [remembrance_id(boss)] + [TIER_MATERIAL[tier]] * 4 + ["diamond", "diamond"], category="equipment")


def tags():
    write(f"{NS}/tags/item/map_materials.json", {"values": [f"{NS}:map_fragment"]})
    write(f"{NS}/tags/item/lithite_materials.json", {"values": [f"{NS}:lithite_shard"]})
    write(f"{NS}/tags/item/ember_materials.json", {"values": [f"{NS}:ancient_ember"]})
    write(f"{NS}/tags/item/void_materials.json", {"values": [f"{NS}:void_shard"]})
    from wf.bossgear import BOSS_GEAR
    swords = ["cartographer_blade", "telluric_hammer", "frost_blade", "ember_scythe", "void_spear"] + \
        [row[2] for row in BOSS_GEAR if row[6] is not None]
    write("minecraft/tags/item/swords.json", {"replace": False, "values": [f"{NS}:{s}" for s in swords]})
    __import__("wf.gadgets", fromlist=["tags"]).tags(write)
    write("minecraft/tags/item/pickaxes.json", {"replace": False, "values": [f"{NS}:excavator_pickaxe"]})
    write("minecraft/tags/item/axes.json", {"replace": False, "values": [f"{NS}:lumber_axe"]})
    for slot, piece in (("head", "helmet"), ("chest", "chestplate"), ("leg", "leggings"), ("foot", "boots")):
        write(f"minecraft/tags/item/{slot}_armor.json", {"replace": False,
                                                        "values": [f"{NS}:{s}_{piece}" for s in ("explorer", "ember", "void")]})
    from wf import decor
    axe_decor = [f"{NS}:{i}" for bid, d in decor.DECOR.items() if d.get("tool") == "axe"
                 for i in [bid] + [decor.variant_id(bid, v) for v in d["variants"]]]
    write("minecraft/tags/block/mineable/axe.json", {"replace": False, "values": [f"{NS}:sorting_chest", f"{NS}:guild_terminal", f"{NS}:compacting_crate",
                                                                                f"{NS}:chisel_table"]
                                                                               + axe_decor})
    write("minecraft/tags/block/needs_iron_tool.json", {"replace": False, "values": [
        f"{NS}:lithite_ore", f"{NS}:deepslate_lithite_ore"]})


def block_loot():
    for b in ("waystone", "sorting_chest", "guild_terminal", "compacting_crate", "chisel_table"):
        write(f"{NS}/loot_table/blocks/{b}.json", {
            "type": "minecraft:block",
            "pools": [{"rolls": 1.0, "bonus_rolls": 0.0,
                       "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": f"{NS}:{b}"}]}],
            "random_sequence": f"{NS}:blocks/{b}",
        })
    for b in ("lithite_ore", "deepslate_lithite_ore"):
        write(f"{NS}/loot_table/blocks/{b}.json", {
            "type": "minecraft:block",
            "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{
                "type": "minecraft:item", "name": f"{NS}:lithite_shard",
                "functions": [
                    {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                    {"function": "minecraft:explosion_decay"},
                ]}]}],
            "random_sequence": f"{NS}:blocks/{b}",
        })


def entity_loot():
    def entry(name, lo=1, hi=1, chance=None):
        e = {"type": "minecraft:item", "name": rid(name)}
        if (lo, hi) != (1, 1):
            e["functions"] = [{"function": "minecraft:set_count",
                               "count": {"type": "minecraft:uniform", "min": lo, "max": hi}, "add": False}]
        pool = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [e]}
        if chance is not None:
            pool["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance}]
        return pool

    tables = {
        "ruin_walker": [entry("rotten_flesh", 0, 2), entry("mossy_cobblestone", 0, 2), entry("map_fragment", chance=0.25)],
        "map_wraith": [entry("paper", 1, 3), entry("ink_sac", 0, 1), entry("map_fragment", chance=0.35)],
        "basalt_guard": [entry("coal", 0, 2), entry("bone", 0, 2), entry("ancient_ember", chance=0.15)],
        "void_stalker": [entry("ender_pearl", 0, 1), entry("void_shard", chance=0.2)],
        "drowned_warden": [entry("warden_scale", 3, 5), entry("heart_of_the_sea"), entry("trident"),
                           entry("map_fragment", 6, 10), entry("lithite_shard", 4, 8)],
        "void_warden": [entry("void_heart"), entry("void_shard", 6, 10), entry("elytra", chance=0.35)],
        "skeleton_knight": [entry("bone", 1, 3), entry("iron_nugget", 1, 4), entry("map_fragment", chance=0.2)],
        "crypt_crawler": [entry("bone", 1, 4), entry("spider_eye", 0, 1), entry("string", 0, 2)],
        "banshee": [entry("phantom_membrane", 0, 1), entry("ghast_tear", chance=0.15), entry("lithite_shard", chance=0.25)],
        "gargoyle": [entry("cobblestone", 1, 3), entry("flint", 0, 2), entry("lithite_shard", chance=0.3)],
        "ember_imp": [entry("blaze_powder", 0, 2), entry("magma_cream", 0, 1), entry("ancient_ember", chance=0.2)],
        "void_larva": [entry("ender_pearl", 0, 1), entry("chorus_fruit", 0, 2), entry("void_shard", chance=0.2)],
        "grave_knight": [entry("map_fragment", 4, 7), entry("emerald", 3, 6), entry("experience_bottle", 2, 5), entry("golden_apple")],
        "bone_matriarch": [entry("map_fragment", 4, 7), entry("emerald", 3, 6), entry("experience_bottle", 2, 5), entry("golden_apple")],
        "weeping_lady": [entry("lithite_shard", 4, 7), entry("emerald", 3, 6), entry("experience_bottle", 2, 5), entry("golden_apple")],
        "larva_mother": [entry("void_shard", 4, 7), entry("emerald", 3, 6), entry("experience_bottle", 2, 5), entry("golden_apple")],
        "bell_keeper": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "archivist": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "sand_pharaoh": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "jade_jaguar": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "root_mother": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "swamp_crone": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "gryphon_knight": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "rune_colossus": [entry("map_fragment", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "forge_king": [entry("lithite_shard", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "crystal_spider": [entry("lithite_shard", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "sculk_spawn": [entry("lithite_shard", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "ash_lord": [entry("ancient_ember", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "piglin_king": [entry("ancient_ember", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        "soul_reaper": [entry("ancient_ember", 6, 10), entry("emerald", 4, 8), entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2)],
        # automatons
        "clockwork_spider": [entry("brass_nugget", 1, 3), entry("brass_gear", chance=0.35), entry("redstone", 0, 1)],
        "steam_drone": [entry("brass_nugget", 1, 3), entry("copper_ingot", 0, 2), entry("brass_gear", chance=0.3),
                        entry("coal", 0, 1)],
        "brass_golem": [entry("clockwork_heart"), entry("brass_ingot", 3, 6)],
        "grand_clockmaker": [entry("brass_gear", 4, 8), entry("map_fragment", 6, 10), entry("emerald", 4, 8),
                             entry("experience_bottle", 3, 6), entry("golden_apple", 1, 2), entry("clockwork_heart"),
                             entry("clock")],
    }
    from wf.bossgear import BOSS_GEAR, remembrance_id
    for row in BOSS_GEAR:  # every great boss always drops its remembrance
        tables[row[0]] = [entry(remembrance_id(row[0]))] + tables[row[0]]
    for name, pools in tables.items():
        write(f"{NS}/loot_table/entities/{name}.json", {"type": "minecraft:entity", "pools": pools,
                                                        "random_sequence": f"{NS}:entities/{name}"})


# biomes where automatons roam: the overhaul's Rustlands and Cogwork Valley, and the vanilla biomes they replace
# (so the mobs exist with or without the world overhaul pack)
AUTOMATON_BIOMES = ["minecraft:windswept_savanna", "minecraft:wooded_badlands", f"{NS}:rustlands", f"{NS}:cogwork_valley"]


def automaton_spawns():
    """Clockwork Spiders and Steam Drones join the monster spawns of the steampunk biomes (at night or in the dark, like
    any monster); the Clockwork Citadel and the Undercity add their own through their structure spawn lists."""
    write(f"{NS}/tags/worldgen/biome/spawns_automatons.json", {
        "replace": False, "values": [{"id": b, "required": False} for b in AUTOMATON_BIOMES]})
    write(f"{NS}/forge/biome_modifier/add_automatons.json", {
        "type": "forge:add_spawns",
        "biomes": f"#{NS}:spawns_automatons",
        "spawners": [
            {"type": f"{NS}:clockwork_spider", "weight": 45, "minCount": 2, "maxCount": 4},
            {"type": f"{NS}:steam_drone", "weight": 20, "minCount": 1, "maxCount": 2},
        ],
    })


def ore_worldgen():
    write(f"{NS}/worldgen/configured_feature/lithite_ore.json", {
        "type": "minecraft:ore",
        "config": {
            "size": 5,
            "discard_chance_on_air_exposure": 0.4,
            "targets": [
                {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
                 "state": {"Name": f"{NS}:lithite_ore"}},
                {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"},
                 "state": {"Name": f"{NS}:deepslate_lithite_ore"}},
            ],
        },
    })
    write(f"{NS}/worldgen/placed_feature/lithite_ore.json", {
        "feature": f"{NS}:lithite_ore",
        "placement": [
            {"type": "minecraft:count", "count": 6},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:height_range", "height": {
                "type": "minecraft:trapezoid", "min_inclusive": {"above_bottom": 0}, "max_inclusive": {"absolute": 8}}},
            {"type": "minecraft:biome"},
        ],
    })
    write(f"{NS}/forge/biome_modifier/add_lithite_ore.json", {
        "type": "forge:add_features",
        "biomes": "#minecraft:is_overworld",
        "features": f"{NS}:lithite_ore",
        "step": "underground_ores",
    })


def metal_tags():
    """Tag values contributed by metals.py: {tag file: [ids]}."""
    from wf import metals
    out = {}

    def add(tag, value):
        out.setdefault(tag, []).append(f"{NS}:{value}")
    for mid, m in metals.METALS.items():
        for bid, (kind, host, _l) in metals.block_ids(mid).items():
            add("minecraft/tags/block/mineable/pickaxe.json", bid)
            tool = m["ore"]["tool"] if kind == "ore" else ("iron" if mid in ("mithril", "aether") else "stone")
            add(f"minecraft/tags/block/needs_{tool}_tool.json", bid)
        for gid, (kind, what, _l) in metals.gear_ids(mid).items():
            if kind == "tool":
                add(f"minecraft/tags/item/{what if what != 'pickaxe' else 'pickaxes'}{'s' if what in ('sword', 'axe', 'shovel', 'hoe') else ''}.json", gid)
            else:
                slot = {"helmet": "head", "chestplate": "chest", "leggings": "leg", "boots": "foot"}[what]
                add(f"minecraft/tags/item/{slot}_armor.json", gid)
    return out


def metals_data():
    """Recipes, smelting, loot, repair tags and ore worldgen for every metal of metals.py."""
    from wf import metals
    items_of = {mid: metals.item_ids(mid) for mid in metals.METALS}

    def cook(name, ingredient, result, xp=0.7, blast=True):
        write(f"{NS}/recipe/{name}_from_smelting.json", {"type": "minecraft:smelting", "category": "misc",
              "ingredient": rid(ingredient), "result": {"id": rid(result)}, "experience": xp, "cookingtime": 200})
        if blast:
            write(f"{NS}/recipe/{name}_from_blasting.json", {"type": "minecraft:blasting", "category": "misc",
                  "ingredient": rid(ingredient), "result": {"id": rid(result)}, "experience": xp, "cookingtime": 100})

    for mid, m in metals.METALS.items():
        forms = {form: iid for iid, (form, _n) in items_of[mid].items()}
        ingot = forms.get("ingot") or forms.get("gem") or forms.get("cloth")
        blocks = metals.block_ids(mid)
        if "nugget" in forms:
            shapeless_named(f"{forms['nugget']}_from_ingot", forms["nugget"], [ingot], 9)
            write(f"{NS}/recipe/{ingot}_from_nuggets.json", {"type": "minecraft:crafting_shaped", "category": "misc",
                  "pattern": ["XXX", "XXX", "XXX"], "key": {"X": rid(forms["nugget"])}, "result": {"id": rid(ingot), "count": 1}})
        if f"{mid}_block" in blocks:
            write(f"{NS}/recipe/{mid}_block.json", {"type": "minecraft:crafting_shaped", "category": "building",
                  "pattern": ["XXX", "XXX", "XXX"], "key": {"X": rid(ingot)}, "result": {"id": rid(f"{mid}_block"), "count": 1}})
            shapeless_named(f"{ingot}_from_block", ingot, [f"{mid}_block"], 9)
        if "raw" in forms:
            raw = forms["raw"]
            cook(ingot, raw, ingot)
            if f"raw_{mid}_block" in blocks:
                write(f"{NS}/recipe/raw_{mid}_block.json", {"type": "minecraft:crafting_shaped", "category": "building",
                      "pattern": ["XXX", "XXX", "XXX"], "key": {"X": rid(raw)}, "result": {"id": rid(f"raw_{mid}_block"), "count": 1}})
                shapeless_named(f"{raw}_from_block", raw, [f"raw_{mid}_block"], 9)
        # ores: loot + smelting + worldgen
        ore = m.get("ore")
        ore_ids = [bid for bid, (k, _h, _l) in blocks.items() if k == "ore"]
        for bid in ore_ids:
            drop = forms.get("raw") or forms.get("gem")
            write(f"{NS}/loot_table/blocks/{bid}.json", {"type": "minecraft:block", "random_sequence": f"{NS}:blocks/{bid}",
                  "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{"type": "minecraft:alternatives", "children": [
                      {"type": "minecraft:item", "name": f"{NS}:{bid}", "conditions": [{"condition": "minecraft:match_tool",
                       "predicate": {"predicates": {"minecraft:enchantments": [{"enchantments": "minecraft:silk_touch",
                                                                                 "levels": {"min": 1}}]}}}]},
                      {"type": "minecraft:item", "name": rid(drop), "functions": [
                          {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                          {"function": "minecraft:explosion_decay"}]}]}]}]})
            cook(f"{ingot}_from_{bid}", bid, ingot, xp=1.0)
        if ore:
            targets = []
            for bid, (k, host, _l) in blocks.items():
                if k != "ore":
                    continue
                tag = {"stone": "minecraft:stone_ore_replaceables", "deepslate": "minecraft:deepslate_ore_replaceables",
                       "netherrack": "minecraft:base_stone_nether"}[host]
                targets.append({"target": {"predicate_type": "minecraft:tag_match", "tag": tag}, "state": {"Name": f"{NS}:{bid}"}})
            write(f"{NS}/worldgen/configured_feature/{mid}_ore.json", {"type": "minecraft:ore", "config": {
                "size": ore["size"], "discard_chance_on_air_exposure": 0.3 if ore["drop"] == "gem" else 0.0, "targets": targets}})
            lo, hi = ore["y"]
            write(f"{NS}/worldgen/placed_feature/{mid}_ore.json", {"feature": f"{NS}:{mid}_ore", "placement": [
                {"type": "minecraft:count", "count": ore["count"]}, {"type": "minecraft:in_square"},
                {"type": "minecraft:height_range", "height": {"type": f"minecraft:{ore['shape']}",
                 "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
                {"type": "minecraft:biome"}]})
            nether = "netherrack" in ore["hosts"]
            write(f"{NS}/forge/biome_modifier/add_{mid}_ore.json", {"type": "forge:add_features",
                  "biomes": "#minecraft:is_nether" if nether else "#minecraft:is_overworld",
                  "features": f"{NS}:{mid}_ore", "step": "underground_decoration" if nether else "underground_ores"})
        # storage block loot
        for bid, (k, _h, _l) in blocks.items():
            if k != "ore":
                write(f"{NS}/loot_table/blocks/{bid}.json", {"type": "minecraft:block", "random_sequence": f"{NS}:blocks/{bid}",
                      "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                                 "entries": [{"type": "minecraft:item", "name": f"{NS}:{bid}"}]}]})
        # repair tag, tools, armor
        if m.get("tools") or m.get("armor"):
            write(f"{NS}/tags/item/{mid}_repair.json", {"values": [rid(ingot)]})
        if m.get("tools"):
            pats = {"sword": ["X", "X", "S"], "pickaxe": ["XXX", " S ", " S "], "axe": ["XX", "XS", " S"],
                    "shovel": ["X", "S", "S"], "hoe": ["XX", " S", " S"]}
            for kind, pat in pats.items():
                shaped(f"{mid}_{kind}", pat, {"X": ingot, "S": "stick"}, category="equipment")
        if m.get("armor"):
            armor_set(mid, ingot)
    # alloys and cloth
    shapeless_named("brass_ingot_from_alloy", "brass_ingot", ["copper_ingot", "copper_ingot", "copper_ingot", "zinc_ingot"], 4)
    shapeless_named("arcane_cloth", "arcane_cloth", ["purple_wool", "aether_crystal", "string"], 2)


def shapeless_named(name, result, ingredients, count=1, category="misc"):
    write(f"{NS}/recipe/{name}.json", {"type": "minecraft:crafting_shapeless", "category": category,
          "ingredients": [rid(i) for i in ingredients], "result": {"id": rid(result), "count": count}})


def decor_data():
    from wf import decor
    pick, stairs, slabs, walls = [], [], [], []
    for bid, d in decor.DECOR.items():
        ids = [bid] + [decor.variant_id(bid, v) for v in d["variants"]]
        if d.get("tool", "pickaxe") == "pickaxe":
            pick += [f"{NS}:{i}" for i in ids]
        for i in ids:
            pool = {"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                    "entries": [{"type": "minecraft:item", "name": f"{NS}:{i}"}]}
            if i.endswith("_slab"):
                pool["entries"][0]["functions"] = [{
                    "function": "minecraft:set_count", "count": 2.0, "add": False,
                    "conditions": [{"condition": "minecraft:block_state_property", "block": f"{NS}:{i}",
                                    "properties": {"type": "double"}}]}]
            write(f"{NS}/loot_table/blocks/{i}.json", {"type": "minecraft:block", "pools": [pool],
                                                      "random_sequence": f"{NS}:blocks/{i}"})
        for v in d["variants"]:
            vid = decor.variant_id(bid, v)
            {"stairs": stairs, "slab": slabs, "wall": walls}[v].append(f"{NS}:{vid}")
            pattern, count = {"stairs": (["X  ", "XX ", "XXX"], 4), "slab": (["XXX"], 6),
                              "wall": (["XXX", "XXX"], 6)}[v]
            write(f"{NS}/recipe/{vid}.json", {"type": "minecraft:crafting_shaped", "category": "building",
                                             "pattern": pattern, "key": {"X": f"{NS}:{bid}"},
                                             "result": {"id": f"{NS}:{vid}", "count": count}})
            write(f"{NS}/recipe/{vid}_from_stonecutting.json", {
                "type": "minecraft:stonecutting", "ingredient": f"{NS}:{bid}",
                "result": {"id": f"{NS}:{vid}", "count": 2 if v == "slab" else 1}})
    write("minecraft/tags/block/mineable/pickaxe.json", {"replace": False, "values": [
        f"{NS}:waystone", f"{NS}:lithite_ore", f"{NS}:deepslate_lithite_ore"] + pick})
    write("minecraft/tags/block/stairs.json", {"replace": False, "values": stairs})
    write("minecraft/tags/block/slabs.json", {"replace": False, "values": slabs})
    write("minecraft/tags/block/walls.json", {"replace": False, "values": walls})
    write("minecraft/tags/item/stairs.json", {"replace": False, "values": stairs})
    write("minecraft/tags/item/slabs.json", {"replace": False, "values": slabs})
    write("minecraft/tags/item/walls.json", {"replace": False, "values": walls})

    def craft(name, pattern, key, count):
        write(f"{NS}/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building",
                                          "pattern": pattern, "key": {k: rid(v) for k, v in key.items()},
                                          "result": {"id": f"{NS}:{name}", "count": count}})
    craft("guild_bricks", ["SA", "AS"], {"S": "stone_bricks", "A": "sandstone"}, 4)
    shapeless("mossy_guild_bricks", ["wayfarers:guild_bricks", "vine"], category="building")
    write(f"{NS}/recipe/cracked_guild_bricks.json", {"type": "minecraft:smelting", "category": "blocks",
                                                    "ingredient": f"{NS}:guild_bricks",
                                                    "result": {"id": f"{NS}:cracked_guild_bricks"},
                                                    "experience": 0.1, "cookingtime": 200})
    craft("polished_guild_stone", ["XX", "XX"], {"X": "wayfarers:guild_bricks"}, 4)
    craft("carved_guild_stone", ["X", "X"], {"X": "wayfarers:polished_guild_stone_slab"}, 1)
    craft("guild_roof_tiles", ["XX", "XX"], {"X": "cyan_terracotta"}, 4)
    craft("crimson_roof_tiles", ["XX", "XX"], {"X": "red_terracotta"}, 4)
    craft("slate_roof_tiles", ["XX", "XX"], {"X": "deepslate_tiles"}, 4)
    craft("rune_lamp", ["GMG", "MLM", "GMG"], {"G": "wayfarers:guild_bricks", "M": "map_fragment", "L": "glowstone"}, 4)
    craft("lithite_block", ["XXX", "XXX", "XXX"], {"X": "lithite_shard"}, 1)
    craft("lithite_bricks", ["LS", "SL"], {"L": "lithite_shard", "S": "stone_bricks"}, 4)
    craft("ember_bricks", ["NM", "MN"], {"N": "polished_blackstone_bricks", "M": "magma_cream"}, 4)
    craft("ember_lamp", [" B ", "BGB", " B "], {"B": "wayfarers:ember_bricks", "G": "glowstone"}, 2)
    craft("gilded_trim", ["G", "B"], {"G": "gold_ingot", "B": "polished_blackstone"}, 2)
    craft("void_bricks", ["OE", "EO"], {"O": "obsidian", "E": "end_stone_bricks"}, 4)
    craft("starlight_block", [" R ", "RCR", " R "], {"R": "end_rod", "C": "amethyst_block"}, 2)
    # steampunk
    craft("brass_plating", ["XX", "XX"], {"X": "wayfarers:brass_ingot"}, 8)
    craft("copper_plating", ["XX", "XX"], {"X": "copper_ingot"}, 8)
    shapeless("verdigris_plating", ["wayfarers:copper_plating", "clay_ball"], category="building")
    craft("dark_iron_plating", ["IC", "CI"], {"I": "iron_ingot", "C": "coal"}, 8)
    craft("diamond_plate", ["IN", "NI"], {"I": "iron_ingot", "N": "iron_nugget"}, 4)
    craft("gear_panel", ["B", "D"], {"B": "wayfarers:brass_ingot", "D": "wayfarers:dark_iron_plating"}, 2)
    craft("copper_pipes", ["C C", "C C", "C C"], {"C": "copper_ingot"}, 4)
    craft("pressure_gauge", ["G", "D"], {"G": "clock", "D": "wayfarers:dark_iron_plating"}, 2)
    craft("edison_lamp", ["N", "G", "L"], {"N": "wayfarers:brass_nugget", "G": "glass", "L": "glowstone_dust"}, 1)
    craft("aether_conduit", ["D", "A", "D"], {"D": "wayfarers:dark_iron_plating", "A": "wayfarers:aether_crystal"}, 2)
    craft("mahogany_panelling", ["PS", "SP"], {"P": "dark_oak_planks", "S": "stick"}, 4)
    craft("leather_padding", ["LW", "WL"], {"L": "leather", "W": "red_wool"}, 4)
    craft("smokestack_bricks", ["BC", "CB"], {"B": "brick", "C": "coal"}, 4)


def chisel_data():
    """data/wayfarers/chisel/<family>.json, one file per family of tools/wf/chisel.py (old files removed)."""
    from wf import chisel
    folder = os.path.join(DATA, NS, "chisel")
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
    for rel, obj in chisel.data_files().items():
        write(rel, obj)


def machines_data():
    """Recipes and loot for machines.py; returns their pickaxe tag values."""
    from wf import machines
    for mid, m in machines.MACHINES.items():
        pattern, key, count = m["recipe"]
        write(f"{NS}/recipe/{mid}.json", {"type": "minecraft:crafting_shaped", "category": "redstone",
                                         "pattern": pattern, "key": {k: rid(v) for k, v in key.items()},
                                         "result": {"id": f"{NS}:{mid}", "count": count}})
        write(f"{NS}/loot_table/blocks/{mid}.json", {
            "type": "minecraft:block", "random_sequence": f"{NS}:blocks/{mid}",
            "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": f"{NS}:{mid}"}]}]})
    out = {"minecraft/tags/block/mineable/pickaxe.json": [f"{NS}:{mid}" for mid in machines.MACHINES]}
    from wf import furniture
    for fid, f in furniture.FURNITURE.items():
        pattern, key, count = f["recipe"]
        write(f"{NS}/recipe/{fid}.json", {"type": "minecraft:crafting_shaped", "category": "building",
                                         "pattern": pattern, "key": {k: rid(v) for k, v in key.items()},
                                         "result": {"id": f"{NS}:{fid}", "count": count}})
        write(f"{NS}/loot_table/blocks/{fid}.json", {
            "type": "minecraft:block", "random_sequence": f"{NS}:blocks/{fid}",
            "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": f"{NS}:{fid}"}]}]})
        tag = "axe" if f.get("tool") == "axe" else "pickaxe"
        out.setdefault(f"minecraft/tags/block/mineable/{tag}.json", []).append(f"{NS}:{fid}")
    return out


def main():
    decor_data()
    recipes()
    tags()
    chisel_data()
    block_loot()
    entity_loot()
    automaton_spawns()
    ore_worldgen()
    metals_data()
    # merge the metals' tag values into tag files written above (or create them)
    extra_tags = metal_tags()
    for rel, values in machines_data().items():
        extra_tags.setdefault(rel, []).extend(values)
    for rel, values in extra_tags.items():
        path = os.path.join(DATA, rel)
        tag = json.load(open(path)) if os.path.exists(path) else {"replace": False, "values": []}
        tag["values"] = tag["values"] + [v for v in values if v not in tag["values"]]
        write(rel, tag)
    print("data written")


if __name__ == "__main__":
    main()

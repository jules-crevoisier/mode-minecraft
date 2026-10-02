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
             "sorting_chest", "waystone", "guild_terminal"}


def shaped(name, pattern, key, count=1, category="misc"):
    write(f"{NS}/recipe/{name}.json", {
        "type": "minecraft:crafting_shaped",
        "category": category,
        "pattern": pattern,
        "key": {k: rid(v) for k, v in key.items()},
        "result": {"id": f"{NS}:{name}", "count": count},
    })


def shapeless(name, ingredients, count=1, category="misc"):
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
    shaped("waystone", [" E ", "MCM", "SSS"], {"E": "ender_pearl", "M": "map_fragment", "C": "compass", "S": "stone_bricks"})
    shaped("sorting_chest", ["PHP", "PCP", "PPP"], {"P": "#planks", "H": "hopper", "C": "chest"})
    shaped("guild_terminal", ["GMG", "PCP", "PRP"], {"G": "gold_ingot", "M": "map_fragment", "P": "#planks",
                                                    "C": "chest", "R": "redstone"})
    shaped("travel_backpack", ["LSL", "LCL", "LLL"], {"L": "leather", "S": "string", "C": "chest"}, category="equipment")
    shaped("magnet_ring", ["MRM", "I I", " I "], {"M": "map_fragment", "R": "redstone", "I": "iron_ingot"}, category="equipment")
    shaped("structure_compass", [" M ", "MCM", " M "], {"M": "map_fragment", "C": "compass"}, category="equipment")
    shapeless("recall_scroll", ["paper", "map_fragment", "ender_pearl"], count=2)
    shapeless("wayfarer_atlas", ["book", "map_fragment"])
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


def tags():
    write(f"{NS}/tags/item/map_materials.json", {"values": [f"{NS}:map_fragment"]})
    write(f"{NS}/tags/item/lithite_materials.json", {"values": [f"{NS}:lithite_shard"]})
    write(f"{NS}/tags/item/ember_materials.json", {"values": [f"{NS}:ancient_ember"]})
    write(f"{NS}/tags/item/void_materials.json", {"values": [f"{NS}:void_shard"]})
    swords = ["cartographer_blade", "telluric_hammer", "frost_blade", "ember_scythe", "void_spear"]
    write("minecraft/tags/item/swords.json", {"replace": False, "values": [f"{NS}:{s}" for s in swords]})
    write("minecraft/tags/item/pickaxes.json", {"replace": False, "values": [f"{NS}:excavator_pickaxe"]})
    write("minecraft/tags/item/axes.json", {"replace": False, "values": [f"{NS}:lumber_axe"]})
    for slot, piece in (("head", "helmet"), ("chest", "chestplate"), ("leg", "leggings"), ("foot", "boots")):
        write(f"minecraft/tags/item/{slot}_armor.json", {"replace": False,
                                                        "values": [f"{NS}:{s}_{piece}" for s in ("explorer", "ember", "void")]})
    write("minecraft/tags/block/mineable/pickaxe.json", {"replace": False, "values": [
        f"{NS}:waystone", f"{NS}:lithite_ore", f"{NS}:deepslate_lithite_ore"]})
    write("minecraft/tags/block/mineable/axe.json", {"replace": False, "values": [f"{NS}:sorting_chest", f"{NS}:guild_terminal"]})
    write("minecraft/tags/block/needs_iron_tool.json", {"replace": False, "values": [
        f"{NS}:lithite_ore", f"{NS}:deepslate_lithite_ore"]})


def block_loot():
    for b in ("waystone", "sorting_chest", "guild_terminal"):
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
    }
    for name, pools in tables.items():
        write(f"{NS}/loot_table/entities/{name}.json", {"type": "minecraft:entity", "pools": pools,
                                                        "random_sequence": f"{NS}:entities/{name}"})


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


def main():
    recipes()
    tags()
    block_loot()
    entity_loot()
    ore_worldgen()
    print("data written")


if __name__ == "__main__":
    main()

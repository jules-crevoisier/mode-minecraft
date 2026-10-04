#!/usr/bin/env python3
"""Generate chest loot tables for every Wayfarers structure.

Each table = shared tier pools (supplies / explorer gear / treasure) + a themed pool.
Mod items (progression materials) are added once the Java side registers them.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf.parts import USE_MOD_BLOCKS  # noqa: E402  (same switch for blocks and items)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "src", "main", "resources", "data", "wayfarers", "loot_table", "chests")


def item(name, weight=10, count=(1, 1), enchant=None):
    e = {"type": "minecraft:item", "name": name if ":" in name else f"minecraft:{name}", "weight": weight}
    fns = []
    if count != (1, 1):
        fns.append({"function": "minecraft:set_count",
                    "count": {"type": "minecraft:uniform", "min": count[0], "max": count[1]}, "add": False})
    if enchant == "random":
        fns.append({"function": "minecraft:enchant_randomly"})
    elif enchant:
        fns.append({"function": "minecraft:enchant_with_levels",
                    "levels": {"type": "minecraft:uniform", "min": enchant[0], "max": enchant[1]}})
    if fns:
        e["functions"] = fns
    return e


def pool(rolls, entries, empty=0):
    if empty:
        entries = entries + [{"type": "minecraft:empty", "weight": empty}]
    return {"rolls": {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]}, "bonus_rolls": 0.0,
            "entries": entries}


SUPPLIES = [item("bread", 15, (2, 6)), item("cooked_beef", 10, (2, 5)), item("baked_potato", 10, (2, 6)),
            item("torch", 15, (8, 24)), item("arrow", 10, (6, 16)), item("coal", 10, (3, 10)),
            item("string", 8, (2, 6)), item("leather", 8, (2, 5)), item("paper", 8, (3, 9)),
            item("iron_ingot", 8, (1, 4)), item("golden_carrot", 5, (2, 6)), item("rail", 4, (4, 12)),
            item("oak_sapling", 4, (1, 3)), item("bone", 6, (2, 5)), item("feather", 6, (2, 6))]

EXPLORER = [item("map", 10), item("compass", 8), item("spyglass", 6), item("name_tag", 5),
            item("saddle", 6), item("lead", 6, (1, 2)), item("iron_pickaxe", 6, enchant="random"),
            item("iron_sword", 6, enchant="random"), item("bow", 6, enchant="random"),
            item("iron_helmet", 4, enchant="random"), item("iron_boots", 4, enchant="random"),
            item("bundle", 4), item("experience_bottle", 8, (2, 6)), item("ender_pearl", 5, (1, 3)),
            item("book", 6, (1, 3), enchant=(5, 15)), item("firework_rocket", 5, (3, 8)),
            item("cartography_table", 2), item("recovery_compass", 1)]

TREASURE = [item("diamond", 8, (1, 3)), item("emerald", 10, (2, 6)), item("gold_ingot", 12, (2, 6)),
            item("golden_apple", 6), item("enchanted_golden_apple", 1), item("diamond_pickaxe", 3, enchant=(20, 30)),
            item("diamond_sword", 3, enchant=(20, 30)), item("book", 6, enchant=(20, 30)),
            item("totem_of_undying", 1), item("music_disc_otherside", 1), item("music_disc_pigstep", 1),
            item("netherite_upgrade_smithing_template", 2), item("heart_of_the_sea", 1),
            item("trident", 1, enchant="random")]

THEMES = {
    "guild": [item("map", 20, (1, 2)), item("compass", 10), item("writable_book", 10),
              item("cartography_table", 4), item("lantern", 8, (1, 3)), item("spyglass", 8)],
    "tower": [item("arrow", 20, (8, 24)), item("crossbow", 8, enchant="random"), item("shield", 8),
              item("iron_helmet", 6), item("chainmail_chestplate", 6), item("bell", 2)],
    "library": [item("book", 20, (1, 2), enchant=(10, 30)), item("bookshelf", 10, (1, 4)), item("ink_sac", 10, (2, 5)),
                item("writable_book", 10), item("lapis_lazuli", 15, (4, 12)), item("experience_bottle", 10, (4, 10)),
                item("enchanting_table", 2)],
    "monastery": [item("honey_bottle", 10, (1, 3)), item("candle", 15, (2, 6)), item("bell", 3),
                  item("cherry_sapling", 8, (1, 3)), item("glow_berries", 10, (3, 8)), item("golden_apple", 4)],
    "desert": [item("gold_ingot", 20, (3, 8)), item("gold_block", 4), item("emerald", 12, (2, 6)),
               item("sandstone", 10, (8, 16)), item("rotten_flesh", 10, (3, 8)), item("diamond", 5, (1, 2)),
               item("brush", 8), item("dune_armor_trim_smithing_template", 3)],
    "ocean": [item("prismarine_shard", 20, (4, 12)), item("prismarine_crystals", 15, (4, 10)),
              item("nautilus_shell", 8, (1, 3)), item("heart_of_the_sea", 2), item("trident", 2, enchant="random"),
              item("turtle_helmet", 3), item("sponge", 6, (1, 3)), item("tide_armor_trim_smithing_template", 2)],
    "witch": [item("glowstone_dust", 15, (3, 8)), item("redstone", 15, (4, 12)), item("spider_eye", 10, (2, 5)),
              item("sugar", 10, (2, 6)), item("nether_wart", 8, (2, 6)), item("blaze_powder", 5, (1, 3)),
              item("brewing_stand", 3), item("glass_bottle", 10, (3, 8)), item("phantom_membrane", 5, (1, 3))],
    "forest": [item("apple", 20, (2, 6)), item("oak_sapling", 10, (2, 4)), item("dark_oak_sapling", 8, (2, 4)),
               item("honeycomb", 10, (2, 6)), item("mushroom_stew", 5), item("bow", 8, enchant="random"),
               item("golden_apple", 4)],
    "sky": [item("feather", 20, (6, 16)), item("phantom_membrane", 10, (2, 4)), item("amethyst_shard", 15, (4, 10)),
            item("elytra", 1), item("firework_rocket", 15, (8, 16)), item("diamond", 6, (1, 3))],
    "mine": [item("iron_ingot", 20, (4, 10)), item("raw_gold", 12, (3, 8)), item("redstone", 15, (6, 16)),
             item("lapis_lazuli", 12, (4, 10)), item("diamond", 6, (1, 3)), item("iron_pickaxe", 8, enchant=(10, 20)),
             item("tnt", 5, (1, 3)), item("rail", 10, (8, 16)), item("powered_rail", 5, (2, 6))],
    "clockwork": [item("wayfarers:brass_ingot", 20, (3, 9)), item("wayfarers:zinc_ingot", 12, (2, 6)),
                  item("wayfarers:mithril_ingot", 5, (1, 3)), item("wayfarers:aether_crystal", 5, (1, 3)),
                  item("wayfarers:redstone_timer", 6), item("wayfarers:wireless_transmitter", 3),
                  item("wayfarers:wireless_receiver", 3), item("wayfarers:auto_harvester", 2),
                  item("wayfarers:steam_cane", 2), item("clock", 8), item("redstone", 14, (4, 12)),
                  item("copper_ingot", 14, (4, 12)), item("spyglass", 4)],
    "foundry": [item("wayfarers:brass_ingot", 20, (4, 10)), item("wayfarers:zinc_ingot", 14, (3, 8)),
                item("wayfarers:raw_zinc", 10, (3, 9)), item("iron_ingot", 16, (4, 12)), item("gold_ingot", 8, (2, 6)),
                item("raw_iron", 10, (4, 10)), item("coal", 12, (6, 16)), item("wayfarers:mithril_ingot", 4, (1, 3)),
                item("wayfarers:brass_pickaxe", 5, enchant="random"), item("wayfarers:brass_axe", 4, enchant="random"),
                item("wayfarers:brass_sword", 4, enchant="random"), item("wayfarers:brass_helmet", 3),
                item("wayfarers:mithril_pickaxe", 1, enchant=(15, 25)), item("anvil", 3), item("blast_furnace", 3),
                item("lava_bucket", 4), item("magma_cream", 6, (2, 5)), item("fire_charge", 6, (2, 6)),
                item("netherite_scrap", 1)],
    "aether": [item("wayfarers:aether_crystal", 16, (1, 4)), item("wayfarers:arcane_cloth", 10, (1, 3)),
               item("amethyst_shard", 14, (3, 9)), item("lapis_lazuli", 12, (4, 12)), item("glowstone_dust", 10, (3, 9)),
               item("redstone", 10, (4, 12)), item("copper_ingot", 10, (4, 10)), item("lightning_rod", 6, (1, 3)),
               item("end_rod", 6, (2, 6)), item("spyglass", 6), item("clock", 5), item("compass", 5),
               item("experience_bottle", 10, (3, 8)), item("book", 8, enchant=(15, 30)),
               item("wayfarers:light_staff", 2), item("wayfarers:storm_staff", 1), item("wayfarers:thunder_staff", 1),
               item("wayfarers:levitation_wand", 2), item("wayfarers:mana_amulet", 2), item("wayfarers:arcane_ring", 2)],
    "cathedral": [item("amethyst_shard", 20, (4, 12)), item("wayfarers:aether_crystal", 8, (1, 3)),
                  item("quartz", 12, (6, 16)), item("candle", 10, (2, 6)), item("lapis_lazuli", 12, (4, 12)),
                  item("book", 14, enchant=(20, 30)), item("experience_bottle", 12, (4, 10)),
                  item("echo_shard", 3, (1, 2)), item("golden_apple", 5), item("diamond", 5, (1, 3)),
                  item("amethyst_block", 6, (2, 6)), item("tinted_glass", 6, (2, 6)), item("totem_of_undying", 1),
                  item("wayfarers:arcane_ring", 2), item("wayfarers:light_staff", 2)],
    "dwarf": [item("iron_block", 10, (1, 3)), item("gold_block", 8, (1, 2)), item("diamond", 8, (2, 4)),
              item("anvil", 3), item("diamond_pickaxe", 4, enchant=(20, 30)), item("netherite_scrap", 2),
              item("smithing_table", 4), item("rib_armor_trim_smithing_template", 1)],
    "bandit": [item("emerald", 15, (2, 8)), item("crossbow", 10, enchant="random"), item("arrow", 15, (8, 16)),
               item("iron_axe", 8, enchant="random"), item("goat_horn", 4), item("totem_of_undying", 1),
               item("sentry_armor_trim_smithing_template", 2)],
    "lighthouse": [item("cod", 15, (3, 8)), item("salmon", 15, (3, 8)), item("fishing_rod", 8, enchant="random"),
                   item("oak_boat", 6), item("glowstone", 6, (2, 6)), item("sea_lantern", 5, (1, 3))],
    "jungle": [item("cocoa_beans", 15, (3, 8)), item("bamboo", 15, (6, 16)), item("emerald", 12, (2, 6)),
               item("gold_ingot", 12, (2, 6)), item("diamond", 5, (1, 3)), item("melon_seeds", 8, (2, 6)),
               item("wild_armor_trim_smithing_template", 2)],
    "ice": [item("blue_ice", 12, (2, 6)), item("packed_ice", 12, (4, 12)), item("snowball", 15, (8, 16)),
            item("spyglass", 8), item("powder_snow_bucket", 4), item("leather_boots", 6, enchant="random"),
            item("clock", 6), item("compass", 6)],
    "rune": [item("amethyst_shard", 15, (3, 8)), item("echo_shard", 3, (1, 2)), item("experience_bottle", 15, (4, 10)),
             item("book", 10, enchant=(15, 30)), item("candle", 10, (2, 6)), item("skeleton_skull", 2)],
    "ship": [item("gunpowder", 15, (3, 10)), item("map", 10), item("gold_nugget", 15, (6, 20)),
             item("emerald", 10, (2, 6)), item("compass", 6), item("diamond", 4, (1, 2)),
             item("coast_armor_trim_smithing_template", 2)],
    "crystal": [item("amethyst_shard", 25, (6, 16)), item("calcite", 10, (6, 16)), item("tinted_glass", 8, (2, 6)),
                item("spyglass", 8), item("copper_ingot", 12, (4, 12)), item("diamond", 6, (1, 3))],
    "lab": [item("redstone_block", 10, (1, 3)), item("observer", 8, (1, 3)), item("comparator", 8, (1, 3)),
            item("echo_shard", 8, (1, 3)), item("sculk_catalyst", 3), item("disc_fragment_5", 6, (1, 3)),
            item("book", 6, enchant=(25, 30)), item("ward_armor_trim_smithing_template", 2),
            item("silence_armor_trim_smithing_template", 1)],
    "nether": [item("gold_ingot", 15, (3, 9)), item("quartz", 15, (6, 16)), item("magma_cream", 8, (2, 6)),
               item("blaze_rod", 10, (1, 4)), item("ghast_tear", 4, (1, 2)), item("netherite_scrap", 3),
               item("crying_obsidian", 8, (2, 6)), item("snout_armor_trim_smithing_template", 2)],
    "fortress": [item("netherite_scrap", 6, (1, 2)), item("ancient_debris", 4), item("wither_skeleton_skull", 2),
                 item("diamond", 8, (2, 4)), item("gold_block", 6, (1, 2)), item("blaze_rod", 10, (2, 5)),
                 item("netherite_upgrade_smithing_template", 3), item("rib_armor_trim_smithing_template", 2)],
    "piglin": [item("gold_block", 10, (1, 3)), item("golden_apple", 8), item("gilded_blackstone", 10, (2, 5)),
               item("crossbow", 8, enchant=(10, 20)), item("piglin_banner_pattern", 4),
               item("music_disc_pigstep", 1), item("ender_pearl", 10, (2, 4))],
    "soul": [item("soul_sand", 10, (4, 12)), item("bone_block", 10, (2, 6)), item("soul_lantern", 10, (1, 3)),
             item("blaze_rod", 8, (1, 3)), item("book", 8, enchant=(20, 30)), item("ghast_tear", 5)],
    "end": [item("ender_pearl", 15, (2, 6)), item("chorus_fruit", 15, (4, 10)), item("end_rod", 10, (2, 6)),
            item("shulker_shell", 6, (1, 2)), item("popped_chorus_fruit", 10, (4, 8)), item("diamond", 8, (2, 5)),
            item("elytra", 2), item("dragon_breath", 4, (1, 3)), item("spire_armor_trim_smithing_template", 2)],
    "citadel": [item("prismarine_shard", 10, (6, 16)), item("heart_of_the_sea", 4), item("trident", 4, enchant=(20, 30)),
                item("diamond", 10, (2, 5)), item("diamond_chestplate", 3, enchant=(20, 30)),
                item("enchanted_golden_apple", 2), item("tide_armor_trim_smithing_template", 3)],
}

# Progression materials from the Java side, by tier.
MOD_ITEMS = {
    "overworld": [item("wayfarers:map_fragment", 25, (1, 3)), item("wayfarers:structure_compass", 2)],
    "deep": [item("wayfarers:lithite_shard", 25, (1, 3)), item("wayfarers:map_fragment", 10, (1, 2))],
    "nether": [item("wayfarers:ancient_ember", 25, (1, 3)), item("wayfarers:lithite_shard", 8, (1, 2))],
    "end": [item("wayfarers:void_shard", 25, (1, 3)), item("wayfarers:ancient_ember", 8, (1, 2))],
}

# table -> (theme, supplies rolls, explorer rolls, treasure rolls, mod tier)
TABLES = {
    "guild_outpost": ("guild", (3, 6), (1, 3), (0, 1), "overworld"),
    "watchtower": ("tower", (2, 5), (1, 2), (0, 1), "overworld"),
    "monastery": ("monastery", (3, 6), (1, 2), (0, 1), "overworld"),
    "monastery_library": ("library", (1, 3), (1, 2), (1, 1), "overworld"),
    "oasis": ("desert", (2, 4), (1, 2), (0, 1), "overworld"),
    "desert_tomb": ("desert", (2, 4), (1, 3), (1, 2), "overworld"),
    "desert_tomb_secret": ("desert", (1, 2), (1, 2), (2, 3), "overworld"),
    "sunken_temple": ("ocean", (1, 3), (1, 2), (1, 2), "overworld"),
    "witch_hut": ("witch", (2, 4), (1, 2), (0, 1), "overworld"),
    "giant_tree": ("forest", (2, 5), (1, 2), (0, 1), "overworld"),
    "giant_tree_top": ("forest", (1, 3), (1, 3), (1, 2), "overworld"),
    "sky_island": ("sky", (1, 3), (1, 3), (1, 2), "overworld"),
    "library": ("library", (1, 4), (1, 3), (0, 1), "overworld"),
    "library_secret": ("library", (1, 2), (2, 3), (1, 2), "overworld"),
    "dwarven_mine": ("mine", (3, 6), (1, 2), (0, 1), "deep"),
    "bandit_camp": ("bandit", (2, 5), (1, 3), (0, 1), "overworld"),
    "lighthouse": ("lighthouse", (3, 6), (1, 2), (0, 1), "overworld"),
    "ziggurat": ("jungle", (2, 4), (1, 3), (1, 2), "overworld"),
    "ice_observatory": ("ice", (3, 5), (1, 2), (0, 1), "overworld"),
    "ice_observatory_lab": ("ice", (1, 3), (1, 2), (1, 1), "overworld"),
    "rune_circle": ("rune", (1, 3), (1, 2), (1, 2), "overworld"),
    "galleon_captain": ("ship", (1, 3), (2, 3), (1, 2), "overworld"),
    "galleon_cargo": ("ship", (3, 6), (0, 1), (0, 1), "overworld"),
    "dwarven_vault": ("dwarf", (1, 2), (1, 2), (1, 3), "deep"),
    "clockwork_workshop": ("clockwork", (2, 4), (0, 1), (0, 1), "overworld"),
    "clockwork_vault": ("clockwork", (1, 2), (1, 3), (2, 3), "overworld"),
    "sky_harbour": ("clockwork", (1, 3), (1, 2), (1, 2), "overworld"),
    "undercity": ("clockwork", (2, 4), (1, 2), (0, 1), "deep"),
    "undercity_vault": ("dwarf", (1, 2), (1, 3), (2, 3), "deep"),
    "crystal_grotto": ("crystal", (1, 3), (1, 2), (1, 2), "deep"),
    "foundry_forge": ("foundry", (2, 4), (1, 2), (0, 1), "overworld"),
    "foundry_vault": ("foundry", (1, 2), (1, 3), (2, 3), "overworld"),
    "observatory_study": ("aether", (1, 3), (1, 2), (0, 1), "overworld"),
    "observatory_lab": ("aether", (1, 3), (1, 2), (1, 1), "overworld"),
    "observatory_vault": ("aether", (1, 2), (1, 3), (2, 3), "overworld"),
    "tesla_tower": ("aether", (1, 3), (1, 2), (1, 2), "overworld"),
    "crystal_cathedral": ("cathedral", (1, 3), (1, 3), (1, 2), "deep"),
    "crystal_cathedral_vault": ("cathedral", (1, 2), (1, 3), (3, 4), "deep"),
    "sealed_lab": ("lab", (1, 3), (1, 3), (1, 2), "deep"),
    "basalt_fortress": ("fortress", (1, 3), (1, 2), (1, 2), "nether"),
    "basalt_fortress_keep": ("fortress", (1, 2), (1, 2), (2, 3), "nether"),
    "chain_bridge": ("nether", (2, 4), (1, 2), (0, 1), "nether"),
    "piglin_sanctuary": ("piglin", (1, 3), (1, 2), (1, 2), "nether"),
    "lava_foundry": ("nether", (2, 5), (1, 2), (0, 1), "nether"),
    "soul_tower": ("soul", (2, 4), (1, 2), (1, 2), "nether"),
    "piglin_market": ("piglin", (2, 4), (1, 2), (0, 1), "nether"),
    "void_observatory": ("end", (1, 3), (1, 2), (1, 2), "end"),
    "chorus_garden": ("end", (2, 4), (1, 2), (0, 1), "end"),
    "end_archive": ("end", (1, 3), (1, 3), (1, 2), "end"),
    "end_archive_top": ("end", (1, 2), (1, 2), (2, 3), "end"),
    "void_ship": ("end", (2, 4), (1, 2), (1, 2), "end"),
    "void_nest": ("end", (1, 2), (1, 2), (2, 4), "end"),
    "citadel_common": ("citadel", (3, 6), (1, 2), (0, 1), "overworld"),
    "citadel_armory": ("citadel", (1, 3), (2, 4), (0, 1), "overworld"),
    "citadel_library": ("library", (1, 3), (1, 3), (1, 1), "overworld"),
    "citadel_shrine": ("ocean", (1, 2), (1, 2), (1, 2), "overworld"),
    "citadel_arena": ("citadel", (1, 2), (1, 2), (1, 2), "overworld"),
    "citadel_vault": ("citadel", (1, 2), (1, 2), (3, 5), "overworld"),
    # standalone dungeons: common rooms, treasure rooms / secret chambers, the reward vault past the boss
    "catacombs": ("monastery", (2, 4), (1, 2), (0, 1), "overworld"),
    "catacombs_treasure": ("monastery", (1, 2), (1, 3), (1, 2), "overworld"),
    "catacombs_reward": ("monastery", (1, 2), (1, 2), (3, 4), "overworld"),
    "hypogeum": ("desert", (2, 4), (1, 2), (0, 1), "overworld"),
    "hypogeum_treasure": ("desert", (1, 2), (1, 3), (1, 2), "overworld"),
    "hypogeum_reward": ("desert", (1, 2), (1, 2), (3, 4), "overworld"),
    "lithite_well": ("dwarf", (2, 4), (1, 2), (0, 1), "deep"),
    "lithite_well_treasure": ("dwarf", (1, 2), (1, 3), (1, 2), "deep"),
    "lithite_well_reward": ("dwarf", (1, 2), (1, 2), (3, 4), "deep"),
    "void_crypt": ("end", (2, 4), (1, 2), (0, 1), "end"),
    "void_crypt_treasure": ("end", (1, 2), (1, 3), (1, 2), "end"),
    "void_crypt_reward": ("end", (1, 2), (1, 2), (3, 5), "end"),
}


def table(name, spec):
    theme, sup, exp, tre, tier = spec
    pools = [pool((2, 4), THEMES[theme])]
    if sup[1]:
        pools.append(pool(sup, SUPPLIES))
    if exp[1]:
        pools.append(pool(exp, EXPLORER))
    if tre[1]:
        pools.append(pool(tre, TREASURE))
    if USE_MOD_BLOCKS:
        pools.append(pool((1, 2), MOD_ITEMS[tier]))
    return {"type": "minecraft:chest", "pools": pools, "random_sequence": f"wayfarers:chests/{name}"}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, spec in TABLES.items():
        with open(os.path.join(OUT, f"{name}.json"), "w") as f:
            json.dump(table(name, spec), f, indent=2)
            f.write("\n")
    print(f"{len(TABLES)} loot tables written")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the Brasshaven quest line as an advancement tab + reward loot tables.

Five chapters guide the group from the first Guild Outpost to the End. Every
structure has a discovery quest; materials found there unlock the next tier of
gear, so the world has to be explored step by step. The Java side shares every
Brasshaven advancement with all players on the server (coop progression).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf import defs  # noqa: E402
import wf.structures  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "src", "main", "resources", "data", "brasshaven")
NS = "brasshaven"

ADV = {}
LANG_EN, LANG_FR = {}, {}
REWARDS = {}
INFO = {}
REWARD_ITEMS = {}


def text(key):
    return {"translate": key}


def quest(qid, parent, icon, title, desc, criteria, frame="task", reward=None, xp=0, hidden=False,
          requirements=None):
    key = f"advancements.{NS}.{qid.replace('/', '.')}"
    LANG_EN[key + ".title"], LANG_FR[key + ".title"] = title
    LANG_EN[key + ".description"], LANG_FR[key + ".description"] = desc
    adv = {
        "display": {
            "icon": {"id": icon if ":" in icon else f"minecraft:{icon}"},
            "title": text(key + ".title"),
            "description": text(key + ".description"),
            "frame": frame,
            "show_toast": True,
            "announce_to_chat": True,
            "hidden": hidden,
        },
        "criteria": criteria,
    }
    if parent:
        adv["parent"] = f"{NS}:{parent}"
    else:
        adv["display"]["background"] = "minecraft:gui/advancements/backgrounds/stone"
    if requirements:
        adv["requirements"] = requirements
    rewards = {}
    if xp:
        rewards["experience"] = xp
    if reward:
        rewards["loot"] = [f"{NS}:rewards/{reward}"]
    if rewards:
        adv["rewards"] = rewards
    ADV[qid] = adv
    INFO[qid] = {"xp": xp, "reward": reward}


def in_structure(sid):
    return {"trigger": "minecraft:location", "conditions": {"player": [{
        "condition": "minecraft:entity_properties", "entity": "this",
        "predicate": {"location": {"structures": f"{NS}:{sid}"}}}]}}


def has_items(*items):
    return {"trigger": "minecraft:inventory_changed", "conditions": {
        "items": [{"items": i if ":" in i else f"{NS}:{i}"} for i in items]}}


def killed(entity):
    return {"trigger": "minecraft:player_killed_entity", "conditions": {"entity": [{
        "condition": "minecraft:entity_properties", "entity": "this",
        "predicate": {"entity_type": entity if ":" in entity else f"{NS}:{entity}"}}]}}


def entered(dim):
    return {"trigger": "minecraft:changed_dimension", "conditions": {"to": f"minecraft:{dim}"}}


def reward(name, *entries):
    REWARD_ITEMS[name] = [(i if ":" in i else f"{NS}:{i}", c) for i, c in entries]
    REWARDS[name] = {
        "type": "minecraft:advancement_reward",
        "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": [{
            "type": "minecraft:item", "name": i if ":" in i else f"{NS}:{i}",
            **({"functions": [{"function": "minecraft:set_count", "count": c, "add": False}]} if c > 1 else {})
        }]} for i, c in entries],
        "random_sequence": f"{NS}:rewards/{name}",
    }


STRUCTURE_ICONS = {
    "guild_outpost": "cartography_table", "ruined_watchtower": "stone_bricks", "mountain_monastery": "bell",
    "desert_oasis": "sandstone", "sunken_temple": "prismarine", "witch_huts": "cauldron", "giant_tree": "oak_log",
    "sky_island": "feather", "forgotten_library": "bookshelf", "dwarven_mine": "rail", "bandit_camp": "crossbow",
    "coastal_lighthouse": "sea_lantern", "jungle_ziggurat": "mossy_stone_bricks", "ice_observatory": "spyglass",
    "rune_circle": "chiseled_stone_bricks", "galleon_wreck": "dark_oak_planks", "dwarven_forge": "anvil",
    "crystal_grotto": "amethyst_cluster", "sealed_lab": "sculk_catalyst", "basalt_fortress": "polished_basalt",
    "chain_bridge": "iron_chain", "piglin_sanctuary": "gold_block", "lava_foundry": "blast_furnace",
    "soul_tower": "soul_lantern", "piglin_market": "gilded_blackstone", "void_observatory": "end_rod",
    "chorus_garden": "chorus_flower", "end_archive": "purpur_pillar", "void_ship": "dragon_head",
    "void_nest": "crying_obsidian", "sunken_citadel": "conduit",
    "forgotten_catacombs": "skeleton_skull", "sand_hypogeum": "chiseled_sandstone",
    "lithite_well": "deepslate_bricks", "void_crypt": "purpur_pillar",
    "clockwork_citadel": "clock", "sky_harbour": "scaffolding", "undercity": "copper_lantern",
    "dwarven_city": "brasshaven:mithril_block", "sylvan_palace": "flowering_azalea_leaves",
    "inventor_manor": "brasshaven:redstone_timer", "sky_isles": "brasshaven:aether_crystal",
    "geothermal_foundry": "magma_block", "walking_fortress": "brasshaven:gear_panel", "rock_necropolis": "chiseled_red_sandstone", "fallen_colossus": "oxidized_copper", "tesla_observatory": "lightning_rod", "crystal_cathedral": "amethyst_block",
    "sunken_submarine": "brasshaven:diving_helmet", "diving_bell": "bell", "coral_shrine": "brain_coral_block",
    "shipwreck_debris": "barrel",
    "chained_bastion": "gilded_blackstone",
    "shattered_halo": "end_crystal",
    "pilgrims_ascent": "bell",
    "tidal_abbey": "prismarine_bricks",
    "caldera_ringwall": "lodestone",
    "glacier_hall": "packed_ice",
    "kneeling_gate": "bell",
    "drowned_dam": "brasshaven:valve_wheel",
    "inverted_spire": "iron_chain",
    "great_aqueduct": "cut_sandstone",
    "mire_stilt_city": "mangrove_roots",
}
# where each boss lives (its quest follows the discovery of that structure)
BOSS_HOME = {
    "bell_keeper": "mountain_monastery", "archivist": "forgotten_library", "sand_pharaoh": "desert_oasis",
    "jade_jaguar": "jungle_ziggurat", "root_mother": "giant_tree", "swamp_crone": "witch_huts",
    "gryphon_knight": "sky_island", "rune_colossus": "rune_circle", "forge_king": "dwarven_forge",
    "crystal_spider": "crystal_grotto", "sculk_spawn": "sealed_lab", "ash_lord": "basalt_fortress",
    "piglin_king": "piglin_sanctuary", "soul_reaper": "soul_tower",
    "grave_knight": "forgotten_catacombs", "bone_matriarch": "sand_hypogeum", "weeping_lady": "lithite_well",
    "larva_mother": "void_crypt",
    "grand_clockmaker": "clockwork_citadel",
    "iron_helmsman": "walking_fortress",
    "bronze_sentinel": "fallen_colossus",
    "dune_king": "rock_necropolis",
    "fallen_seraph": "shattered_halo",
    "chained_jailer": "chained_bastion",
    "caldera_castellan": "caldera_ringwall",
    "oathbound_gatekeeper": "kneeling_gate",
    "frost_jarl": "glacier_hall",
    "storm_ascetic": "pilgrims_ascent",
    "tide_abbess": "tidal_abbey",
}
CHAPTER = {}
for s in defs.STRUCTURES:
    if s.dimension == "nether":
        CHAPTER[s.id] = "nether"
    elif s.dimension == "end":
        CHAPTER[s.id] = "end"
    elif s.step == "underground_structures" or s.id in ("dwarven_mine", "sunken_citadel", "lithite_well"):
        CHAPTER[s.id] = "depths"
    else:
        CHAPTER[s.id] = "explorer"


def build():
    # ---------------------------------------------------------------- root
    quest("root", None, f"{NS}:wayfarer_atlas", ("Brasshaven", "Brasshaven"),
          ("Explore every corner of every dimension, together.",
           "Explore chaque recoin de chaque dimension, ensemble."),
          {"start": {"trigger": "minecraft:tick"}})
    # ---------------------------------------------------------------- chapter 1
    # the first step of the progression ladder (wf/progression.py): the nearest Guild Outpost is marked on the new
    # player's map. Talking to any Guild Agent (a village's Guild Post or square) counts too: "met_agent" is granted
    # by Java (Progression.metAgent). No Structure Compass here: the Guild Agent's second contract gives it.
    reward("first_outpost", ("map_fragment", 3))
    quest("first_steps/guild_outpost", "root", "cartography_table",
          ("I. The Guild Outpost", "I. L'avant-poste de la Guilde"),
          ("Meet a Guild Agent: the nearest Guild Outpost is marked on your map (M). Village Guild Posts have one too.",
           "Rencontre un agent de la Guilde : l'avant-poste le plus proche est marqué sur ta carte (M). Les Relais de "
           "la Guilde des villages en ont un aussi."),
          {"found": in_structure("guild_outpost"), "met_agent": {"trigger": "minecraft:impossible"}},
          frame="goal", reward="first_outpost", xp=50, requirements=[["found", "met_agent"]])
    quest("first_steps/map_fragment", "first_steps/guild_outpost", f"{NS}:map_fragment",
          ("Pieces of the Map", "Morceaux de carte"),
          ("Get a Map Fragment from any Overworld structure.",
           "Récupère un fragment de carte dans une structure de la Surface."),
          {"item": has_items("map_fragment")}, xp=20)
    reward("waystone", ("map_fragment", 2))
    quest("first_steps/waystone", "first_steps/map_fragment", f"{NS}:waystone",
          ("Never Walk Twice", "Plus jamais à pied"),
          ("Craft a Waystone and place it at your base.",
           "Fabrique une pierre de voyage et pose-la à ta base."),
          {"item": has_items("waystone")}, reward="waystone", xp=30)
    quest("first_steps/sorting_chest", "first_steps/map_fragment", f"{NS}:sorting_chest",
          ("Tidy Base, Happy Guild", "Base rangée, guilde heureuse"),
          ("Craft a Sorting Chest.", "Fabrique un coffre de tri."),
          {"item": has_items("sorting_chest")}, xp=20)
    quest("first_steps/guild_terminal", "first_steps/sorting_chest", f"{NS}:guild_terminal",
          ("One Click Storage", "Rangement en un clic"),
          ("Craft a Guild Terminal to empty your bags into every chest around.",
           "Fabrique un terminal de guilde pour vider ton sac dans tous les coffres autour."),
          {"item": has_items("guild_terminal")}, xp=30)
    quest("first_steps/backpack", "first_steps/map_fragment", f"{NS}:travel_backpack",
          ("Pack Light, Carry Lots", "Voyager léger, porter lourd"),
          ("Craft a Travel Backpack.", "Fabrique un sac du voyageur."),
          {"item": has_items("travel_backpack")}, xp=20)
    quest("first_steps/blade", "first_steps/map_fragment", f"{NS}:cartographer_blade",
          ("Drawn Swords, Drawn Maps", "Épées tirées, cartes tracées"),
          ("Forge the Cartographer's Blade.", "Forge la lame du Cartographe."),
          {"item": has_items("cartographer_blade")}, xp=30)
    quest("first_steps/explorer_armor", "first_steps/blade", f"{NS}:explorer_chestplate",
          ("Dressed for the Road", "Paré pour la route"),
          ("Wear the full Explorer set.", "Porte l'ensemble d'explorateur complet."),
          {"armor": has_items("explorer_helmet", "explorer_chestplate", "explorer_leggings", "explorer_boots")},
          frame="goal", xp=60)
    # ---------------------------------------------------------------- chapter 2: overworld structures
    reward("discovery", ("map_fragment", 2))
    explorer_ids = [s.id for s in defs.STRUCTURES if CHAPTER[s.id] == "explorer" and s.id != "guild_outpost"]
    for sid in explorer_ids:
        s = next(x for x in defs.STRUCTURES if x.id == sid)
        quest(f"explorer/{sid}", "first_steps/guild_outpost", STRUCTURE_ICONS[sid],
              (s.title_en, s.title_fr),
              (f"Discover a {s.title_en}.", f"Découvre : {s.title_fr}."),
              {"found": in_structure(sid)}, reward="discovery", xp=40)
    reward("cartographer", ("structure_compass", 1), ("magnet_ring", 1), ("map_fragment", 8))
    quest("explorer/master_cartographer", "explorer/" + explorer_ids[-1], "filled_map",
          ("II. Master Cartographer", "II. Maître cartographe"),
          ("Discover every kind of Overworld surface structure.",
           "Découvre tous les types de structures de la Surface."),
          {sid: in_structure(sid) for sid in explorer_ids}, frame="challenge", reward="cartographer", xp=300)
    # ---------------------------------------------------------------- chapter 3: depths
    quest("depths/lithite", "first_steps/map_fragment", f"{NS}:lithite_shard",
          ("III. Into the Depths", "III. Dans les profondeurs"),
          ("Find Lithite, the crystal of the deep. Mine it below y=0 or loot it underground.",
           "Trouve de la lithite, le cristal des profondeurs. Mine-la sous y=0 ou pille-la sous terre."),
          {"item": has_items("lithite_shard")}, frame="goal", xp=50)
    for sid in [s.id for s in defs.STRUCTURES if CHAPTER[s.id] == "depths" and s.id != "sunken_citadel"]:
        s = next(x for x in defs.STRUCTURES if x.id == sid)
        quest(f"depths/{sid}", "depths/lithite", STRUCTURE_ICONS[sid], (s.title_en, s.title_fr),
              (f"Discover a {s.title_en}.", f"Découvre : {s.title_fr}."),
              {"found": in_structure(sid)}, reward="discovery", xp=50)
    for iid, (en, fr) in {"telluric_hammer": ("Earthshaker", "Fait trembler la terre"),
                          "excavator_pickaxe": ("Tunnel Vision", "Vision tunnel"),
                          "lumber_axe": ("Timber!", "Attention, ça tombe !"),
                          "frost_blade": ("Cold Steel", "Acier glacé"),
                          "boomerang": ("It Always Comes Back", "Il revient toujours")}.items():
        quest(f"depths/{iid}", "depths/lithite", f"{NS}:{iid}", (en, fr),
              (f"Craft the {iid.replace('_', ' ').title()}.", "Fabrique cet équipement de lithite."),
              {"item": has_items(iid)}, xp=30)
    quest("depths/sunken_citadel", "depths/lithite", "conduit",
          ("The Sunken Citadel", "La Citadelle engloutie"),
          ("Find the Sunken Citadel: look for a tower rising from deep ocean waters.",
           "Trouve la Citadelle engloutie : cherche une tour qui sort des océans profonds."),
          {"found": in_structure("sunken_citadel")}, frame="goal", reward="discovery", xp=80)
    reward("drowned_warden", ("warden_scale", 2), ("void_shard", 1))
    quest("depths/drowned_warden", "depths/sunken_citadel", f"{NS}:warden_scale",
          ("Warden of the Deep", "Le Gardien des abysses"),
          ("Defeat the Drowned Warden at the heart of the Citadel.",
           "Vaincs le Gardien englouti au cœur de la Citadelle."),
          {"kill": killed("drowned_warden")}, frame="challenge", reward="drowned_warden", xp=500)
    # ---------------------------------------------------------------- chapter 4: nether
    quest("nether/enter", "depths/lithite", "netherrack", ("IV. Into the Fire", "IV. Dans les flammes"),
          ("Enter the Nether. The guild's maps end here.", "Entre dans le Nether. Les cartes de la guilde s'arrêtent ici."),
          {"enter": entered("the_nether")}, frame="goal", xp=50)
    nether_ids = [s.id for s in defs.STRUCTURES if CHAPTER[s.id] == "nether"]
    for sid in nether_ids:
        s = next(x for x in defs.STRUCTURES if x.id == sid)
        quest(f"nether/{sid}", "nether/enter", STRUCTURE_ICONS[sid], (s.title_en, s.title_fr),
              (f"Discover a {s.title_en}.", f"Découvre : {s.title_fr}."),
              {"found": in_structure(sid)}, reward="discovery", xp=60)
    quest("nether/ancient_ember", "nether/enter", f"{NS}:ancient_ember", ("Ancient Ember", "Braise ancienne"),
          ("Recover an Ancient Ember from a Nether structure.", "Récupère une braise ancienne dans une structure du Nether."),
          {"item": has_items("ancient_ember")}, xp=50)
    for iid, (en, fr) in {"ember_scythe": ("Reaper of Embers", "Faucheur de braises"),
                          "storm_staff": ("Thunderstruck", "Foudroyé")}.items():
        quest(f"nether/{iid}", "nether/ancient_ember", f"{NS}:{iid}", (en, fr),
              ("Craft this ember weapon.", "Fabrique cette arme de braise."), {"item": has_items(iid)}, xp=40)
    quest("nether/ember_armor", "nether/ancient_ember", f"{NS}:ember_chestplate",
          ("Fireproof", "Ignifugé"), ("Wear the full Ember set.", "Porte l'ensemble de braise complet."),
          {"armor": has_items("ember_helmet", "ember_chestplate", "ember_leggings", "ember_boots")},
          frame="goal", xp=100)
    quest("nether/all", "nether/ancient_ember", "nether_star",
          ("Lord of the Underworld", "Seigneur des enfers"),
          ("Discover every Nether structure.", "Découvre toutes les structures du Nether."),
          {sid: in_structure(sid) for sid in nether_ids}, frame="challenge", reward="cartographer", xp=300)
    # ---------------------------------------------------------------- chapter 5: end
    quest("end/enter", "nether/ancient_ember", "end_stone", ("V. Beyond the Void", "V. Au-delà du vide"),
          ("Reach the End.", "Atteins l'End."), {"enter": entered("the_end")}, frame="goal", xp=80)
    end_ids = [s.id for s in defs.STRUCTURES if CHAPTER[s.id] == "end"]
    for sid in end_ids:
        s = next(x for x in defs.STRUCTURES if x.id == sid)
        quest(f"end/{sid}", "end/enter", STRUCTURE_ICONS[sid], (s.title_en, s.title_fr),
              (f"Discover a {s.title_en} among the outer islands.", f"Découvre parmi les îles extérieures : {s.title_fr}."),
              {"found": in_structure(sid)}, reward="discovery", xp=80)
    quest("end/void_shard", "end/enter", f"{NS}:void_shard", ("Shards of Nothing", "Éclats de néant"),
          ("Recover a Void Shard.", "Récupère un éclat du vide."), {"item": has_items("void_shard")}, xp=60)
    quest("end/void_spear", "end/void_shard", f"{NS}:void_spear", ("Blink", "Clignement"),
          ("Craft the Void Spear.", "Fabrique la lance du vide."), {"item": has_items("void_spear")}, xp=50)
    quest("end/void_armor", "end/void_shard", f"{NS}:void_chestplate", ("Void Walker", "Marcheur du vide"),
          ("Wear the full Void set.", "Porte l'ensemble du vide complet."),
          {"armor": has_items("void_helmet", "void_chestplate", "void_leggings", "void_boots")},
          frame="goal", xp=150)
    reward("void_warden", ("void_heart", 1), ("void_shard", 4))
    quest("end/void_warden", "end/void_nest", f"{NS}:void_heart", ("Heart of the Void", "Cœur du vide"),
          ("Defeat the Void Warden in its nest.", "Vaincs le Gardien du vide dans son nid."),
          {"kill": killed("void_warden")}, frame="challenge", reward="void_warden", xp=800)
    # ---------------------------------------------------------------- the legends: one quest per boss
    from wf import content
    from wf.bossgear import BOSS_GEAR
    weapon_of = {row[0]: row[2] for row in BOSS_GEAR}
    for boss, home in BOSS_HOME.items():
        chapter = CHAPTER[home]
        en, fr = content.ENTITIES[boss]
        champion = boss not in weapon_of
        quest(f"{chapter}/boss_{boss}", f"{chapter}/{home}",
              "wither_skeleton_skull" if champion else f"{NS}:{weapon_of[boss]}",
              (f"Felled: {en}", f"Vaincu : {fr}"),
              (f"Defeat {en[0].lower() + en[1:]} in its lair.", f"Vaincs {fr[0].lower() + fr[1:]} dans son antre."),
              {"kill": killed(boss)}, frame="goal" if champion else "challenge", xp=250 if champion else 500)
    great = ["drowned_warden", "void_warden"] + [b for b in BOSS_HOME if b in weapon_of]
    quest("end/legends_bane", "end/void_warden", "nether_star", ("Bane of Legends", "Fléau des Légendes"),
          ("Defeat every great boss of the Brasshaven.", "Vaincs tous les grands boss des Voyageurs."),
          {b: killed(b) for b in great}, frame="challenge", xp=3000)
    all_ids = [s.id for s in defs.STRUCTURES]
    quest("end/legend", "end/void_warden", "dragon_egg", ("Legend of the Brasshaven", "Légende des Voyageurs"),
          ("Discover every single Brasshaven structure in every dimension.",
           "Découvre absolument toutes les structures Brasshaven, dans toutes les dimensions."),
          {sid: in_structure(sid) for sid in all_ids}, frame="challenge", xp=2000)


def main():
    build()
    # the quest givers' contracts (wf/npcs.py): their texts, and their rewards for the journal's Contracts tab
    from wf import npcs
    npcs.check()
    en, fr = npcs.lang()
    LANG_EN.update(en)
    LANG_FR.update(fr)
    out = os.path.join(DATA, "advancement")
    for qid, adv in ADV.items():
        path = os.path.join(out, qid + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(adv, f, indent=2, ensure_ascii=False)
            f.write("\n")
    for name, table in REWARDS.items():
        path = os.path.join(DATA, "loot_table", "rewards", name + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(table, f, indent=2)
            f.write("\n")
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    with open(os.path.join(ROOT, "build", "quest_lang.json"), "w", encoding="utf-8") as f:
        json.dump({"en_us": LANG_EN, "fr_fr": LANG_FR}, f, ensure_ascii=False)
    chapters = {}
    for qid in ADV:
        chapters.setdefault(qid.split("/")[0], []).append(qid)
    # gen_java bakes the rewards into GeneratedContent for the quest journal
    info = {q: {"xp": v["xp"], "items": REWARD_ITEMS.get(v["reward"], []) if v["reward"] else []} for q, v in INFO.items()}
    info.update(npcs.journal_rewards())
    with open(os.path.join(ROOT, "build", "quest_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=1)
    # Java reads this to print chapter progress from the Atlas item
    with open(os.path.join(DATA, "quests.json"), "w", encoding="utf-8") as f:
        json.dump({c: v for c, v in chapters.items() if c != "root"}, f, indent=2)
        f.write("\n")
    print(f"{len(ADV)} quests, {len(REWARDS)} reward tables")


if __name__ == "__main__":
    main()

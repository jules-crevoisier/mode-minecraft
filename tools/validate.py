#!/usr/bin/env python3
"""Static validation of every generated resource, without needing the game.

Checks block ids/states in structure templates (against 1.20 data, the version the
templates are stamped with; DataFixerUpper upgrades them), item ids in loot tables
and biome ids (against 26.1 data, the closest release to 26.2), plus every
cross-reference between worldgen files, textures, models and translations.
Exit code is non-zero when anything is wrong.
"""
import functools
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf import nbt, chunking  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
DATA = os.path.join(RES, "data")
ASSETS = os.path.join(RES, "assets")
MC_TEMPLATE = json.load(open(os.path.join(ROOT, "tools", "data", "mc_26.1.json")))
MC_GAME = json.load(open(os.path.join(ROOT, "tools", "data", "mc_26.1.json")))
VANILLA_BIOME_TAGS = {
    "is_overworld", "is_nether", "is_end", "is_ocean", "is_deep_ocean", "is_beach", "is_river", "is_mountain",
    "is_badlands", "is_hill", "is_taiga", "is_jungle", "is_forest", "is_savanna",
}
# vanilla village and outpost pools (they live in the game jar; our overrides copy them, wf/vanilla_pools.py)
VANILLA_POOLS = json.load(open(os.path.join(ROOT, "tools", "wf", "vanilla_village_pools.json")))
VANILLA_PROCESSORS = {e["element"]["processors"] for p in VANILLA_POOLS.values() for e in p["elements"]
                      if isinstance(e["element"].get("processors"), str)}
# Blocks renamed after 1.20 that DataFixerUpper converts (old -> new)
UPGRADED = {"grass": "short_grass", "chain": "iron_chain"}

errors = []
warnings = []
TEMPLATES = {}  # "ns:path" -> (size, number of block entries), filled by check_templates
TEMPLATE_BLOCKS = set()  # every block id in a structure template palette, filled by check_templates


def err(msg):
    errors.append(msg)


def res_path(rl, kind, ext):
    ns, path = rl.split(":", 1)
    return os.path.join(DATA, ns, kind, path + ext)


@functools.lru_cache(maxsize=None)
def mod_ids(kind):
    """Ids registered by the Java side, read straight from the registry classes."""
    import re
    java = os.path.join(ROOT, "src", "main", "java", "com", "brasshaven")
    files = {"blocks": ["registry/ModBlocks.java", "generated/ModDecor.java", "generated/GeneratedMetals.java",
                        "generated/GeneratedMachines.java", "generated/GeneratedFurniture.java",
                        "generated/GeneratedWorldBlocks.java"],
             "items": ["registry/ModItems.java", "generated/ModDecor.java", "generated/BossGear.java",
                       "generated/GeneratedMetals.java", "generated/GeneratedMachines.java",
                       "generated/GeneratedFurniture.java", "generated/GeneratedWorldBlocks.java"],
             "entities": ["registry/ModEntities.java"]}[kind] + ["registry/ModOcean.java"] * (kind != "entities") \
        + ["registry/ModSocial.java"] * (kind != "entities")
    ids = set()
    for f in files:
        text = open(os.path.join(java, f), encoding="utf-8").read()
        if f.endswith("ModOcean.java"):  # living oceans: block(...) registers a block and its item
            ids |= set(re.findall(r'\b(?:block)\("([a-z0-9_]+)"' if kind == "blocks"
                                  else r'\b(?:block|item|egg)\("([a-z0-9_]+)"', text))
            continue
        if kind == "blocks" and f.endswith("GeneratedMetals.java"):
            ids |= set(re.findall(r'\bblock\("([a-z0-9_]+)"', text))
            continue
        ids |= set(re.findall(r'(?:register|simple|armor|block|pillar|door|egg|stairs|slab|wall|weapon|remembrance|spell|item|gear|machine|furniture)\("([a-z0-9_]+)"', text))
    return ids


HORIZONTAL = ["north", "south", "east", "west"]


def _mod_states():
    """Block-state properties of the mod's machines, furniture and crate (wf tables)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import furniture, machines, ocean, social
    out = {"compacting_crate": {"facing": HORIZONTAL}, "chisel_table": {"facing": HORIZONTAL}}
    out.update(ocean.MOD_STATES)
    out.update(social.MOD_STATES)
    for mid in machines.MACHINES:
        out[mid] = {"facing": HORIZONTAL + ["up", "down"], "powered": ["false", "true"]}
    for fid, f in furniture.FURNITURE.items():
        out[fid] = {} if f["mount"] == "none" else {"axis": ["x", "y", "z"]} if f["mount"] == "axis" else {"facing": HORIZONTAL}
    return out


MOD_STATES = _mod_states()


CONTAINER_BLOCKS = ("minecraft:barrel", "minecraft:chest", "minecraft:trapped_chest")


def check_templates():
    mod_blocks = mod_ids("blocks")
    loot_refs = set()
    barrels = {"stocked": 0, "empty": 0}
    for path in sorted(glob.glob(os.path.join(DATA, "*", "structure", "**", "*.nbt"), recursive=True)):
        rel = os.path.relpath(path, DATA)
        d = nbt.load(path)
        size = d["size"]
        ns_dir, sub = rel.split(os.sep, 2)[0], rel.split(os.sep, 2)[2]
        TEMPLATES[f"{ns_dir}:{sub[:-4].replace(os.sep, '/')}"] = (size, len(d["blocks"]))
        TEMPLATE_BLOCKS.update(e["Name"] for e in d["palette"])
        for entry in d["palette"]:
            ns, name = entry["Name"].split(":")
            props = entry.get("Properties", {})
            if ns == "brasshaven":
                if mod_blocks and name not in mod_blocks:
                    err(f"{rel}: unknown mod block {entry['Name']}")
                analog = ("stone_brick_stairs" if name.endswith("_stairs") else "stone_brick_slab"
                          if name.endswith("_slab") else "stone_brick_wall" if name.endswith("_wall") else None)
                if name in ("grave", "guild_terminal"):
                    analog = "furnace"
                states = MC_TEMPLATE["blocks"].get(analog, {}) if analog else {}
                if name == "mist_gate":
                    states = {"sealed": ["false", "true"]}
                own = MOD_STATES.get(name)
                if own is not None:
                    for k, v in props.items():
                        if k not in own or v not in own[k]:
                            err(f"{rel}: {name}[{k}={v}] invalid")
                    continue
                for k, v in props.items():
                    if k not in states or (k != "facing" and v not in states[k]) or \
                            (k == "facing" and v not in ("north", "south", "east", "west")):
                        err(f"{rel}: {name}[{k}={v}] invalid")
                continue
            states = MC_TEMPLATE["blocks"].get(name)
            if states is None:
                err(f"{rel}: unknown block {entry['Name']}")
                continue
            for k, v in props.items():
                if k not in states:
                    err(f"{rel}: {name} has no property '{k}'")
                elif v not in states[k]:
                    err(f"{rel}: {name}[{k}={v}] invalid (allowed {states[k]})")
            if name not in MC_GAME["blocks"] and name not in UPGRADED:
                warnings.append(f"{rel}: {name} no longer exists in 26.1")
        for b in d["blocks"]:
            if not all(0 <= c < s for c, s in zip(b["pos"], size)):
                err(f"{rel}: block outside template bounds at {b['pos']}")
            data = b.get("nbt")
            bname = d["palette"][b["state"]]["Name"]
            if bname == "minecraft:barrel":
                barrels["stocked" if data and "LootTable" in data else "empty"] += 1
            if not data:
                continue
            if "LootTable" in data:
                loot_refs.add((data["LootTable"], rel))
                if not (bname in CONTAINER_BLOCKS or bname.endswith("shulker_box") or bname in (
                        "minecraft:suspicious_sand", "minecraft:suspicious_gravel", "minecraft:decorated_pot",
                        "minecraft:dispenser", "minecraft:dropper", "minecraft:hopper")):
                    err(f"{rel}: {bname} is not a container but has a LootTable")
            for stack in data.get("Items", []) if isinstance(data.get("Items"), list) else []:
                ins, _, iid = str(stack.get("id", "")).rpartition(":")
                if (ins == "minecraft" and iid not in MC_GAME["items"]) or (ins == "brasshaven" and iid not in mod_ids("items")):
                    err(f"{rel}: container item {stack.get('id')} unknown (the game rejects the whole template)")
            if "SpawnData" in data:
                ens, eid = data["SpawnData"]["entity"]["id"].split(":")
                if (ens == "minecraft" and eid not in MC_GAME["entities"]) or (ens == "brasshaven" and eid not in mod_ids("entities")):
                    err(f"{rel}: spawner entity {eid} unknown")
            if "pool" in data and data["pool"] != "minecraft:empty" and data["pool"] not in VANILLA_POOLS:
                if not os.path.exists(res_path(data["pool"], "worldgen/template_pool", ".json")):
                    err(f"{rel}: jigsaw pool {data['pool']} missing")
        for e in d["entities"]:
            check_template_entity(rel, e, err)
            if "LootTable" in e["nbt"]:  # chest minecarts
                loot_refs.add((e["nbt"]["LootTable"], rel))
    for ref, rel in sorted(loot_refs):
        if ref.startswith("brasshaven:") and not os.path.exists(res_path(ref, "loot_table", ".json")):
            err(f"{rel}: loot table {ref} missing")
    # the barrels of the rooms hold supplies (wf/barrels.py): most of them, not all, so it feels natural
    total = barrels["stocked"] + barrels["empty"]
    if total and not 0.55 <= barrels["stocked"] / total <= 0.85:
        err(f"barrels: {barrels['stocked']} of {total} barrels hold supplies (wf/barrels.py aims at about two in three)")


# vanilla 26.2 registries (VillagerProfession / VillagerType keys)
PROFESSIONS = {"none", "armorer", "butcher", "cartographer", "cleric", "farmer", "fisherman", "fletcher", "leatherworker",
               "librarian", "mason", "nitwit", "shepherd", "toolsmith", "weaponsmith"}
VILLAGER_TYPES = {"desert", "jungle", "plains", "savanna", "snow", "swamp", "taiga"}
# block-attached entities keep an absolute block_pos: copied from a template it no longer matches their position
# and the game logs "Block-attached entity at invalid position" (an ERROR the CI smoke test fails on)
HANGING = {"item_frame", "glow_item_frame", "painting", "leash_knot"}


def check_template_entity(rel, e, err):
    """Entities saved in structure templates: known ids, no block-attached ones, sane villager data."""
    data = e["nbt"]
    ns, eid = data["id"].split(":")
    known = eid in MC_GAME["entities"] if ns == "minecraft" else ns == "brasshaven" and eid in mod_ids("entities")
    if not known:
        err(f"{rel}: entity {data['id']} unknown")
    if eid in HANGING:
        err(f"{rel}: {eid} in a template (its absolute block_pos makes the game log an error)")
    if len(e.get("pos", ())) != 3 or len(e.get("blockPos", ())) != 3:
        err(f"{rel}: entity {eid} without pos/blockPos")
    if "Rotation" in data and len(data["Rotation"]) != 2:
        err(f"{rel}: entity {eid} rotation must be [yaw, pitch]")
    if ns == "brasshaven":
        from wf import denizens
        if eid in denizens.PEOPLES and data.get("Role") not in denizens.ROLE_ORDER[eid]:
            err(f"{rel}: {eid} role {data.get('Role')} unknown (wf/denizens.py PEOPLES)")
    if ns == "brasshaven" and eid == "wayfarer_npc":
        from wf import npcs
        if data.get("Role") not in npcs.ROLES:
            err(f"{rel}: quest giver role {data.get('Role')} unknown (wf/npcs.py ROLES)")
        return
    if eid != "villager":
        return
    vd = data.get("VillagerData", {})
    prof = vd.get("profession", "minecraft:none").split(":")[-1]
    vtype = vd.get("type", "minecraft:plains").split(":")[-1]
    level = vd.get("level", 1)
    if prof not in PROFESSIONS:
        err(f"{rel}: villager profession {prof} unknown")
    if vtype not in VILLAGER_TYPES:
        err(f"{rel}: villager type {vtype} unknown")
    if not 1 <= level <= 5:
        err(f"{rel}: villager level {level} out of 1..5")
    if prof not in ("none", "nitwit") and level <= 1 and not data.get("Xp"):
        err(f"{rel}: a level-1 villager with no xp loses its {prof} profession until it finds a job site")


# blocks placed only by the game itself (graves, boss arenas): no loot table, no survival source
TECHNICAL_BLOCKS = {"grave", "sealed_bars", "warden_altar", "void_altar", "mist_gate", "boss_seal"}


def check_tags():
    for path in glob.glob(os.path.join(DATA, "*", "tags", "item", "**", "*.json"), recursive=True):
        for v in json.load(open(path))["values"]:
            v = v["id"] if isinstance(v, dict) else v
            if not v.startswith("#"):
                check_item_id(os.path.relpath(path, DATA), v)
    for path in glob.glob(os.path.join(DATA, "*", "tags", "block", "**", "*.json"), recursive=True):
        for v in json.load(open(path))["values"]:
            v = v["id"] if isinstance(v, dict) else v
            if v.startswith("brasshaven:") and v.split(":")[1] not in mod_ids("blocks"):
                err(f"{os.path.relpath(path, DATA)}: unknown mod block {v}")
    for b in mod_ids("blocks"):
        if b not in TECHNICAL_BLOCKS and \
                not os.path.exists(os.path.join(DATA, "brasshaven", "loot_table", "blocks", b + ".json")):
            err(f"block {b} has no loot table (would drop nothing)")


def check_barrel_tables():
    """The barrel supplies (wf/barrels.py): every kind has its table, small and modest: no strong reward, nothing that
    skips a step of the progression ladder, no enchantment, small stacks."""
    from wf import barrels
    for kind in barrels.KINDS:
        path = res_path(barrels.PREFIX + kind, "loot_table", ".json")
        if not os.path.exists(path):
            err(f"barrels: table {barrels.PREFIX}{kind} missing (tools/gen_loot.py)")
            continue
        table = json.load(open(path))
        for p in table["pools"]:
            for e in p["entries"]:
                if e["type"] != "minecraft:item":
                    continue
                short = e["name"].split(":")[1]
                if any(f in short for f in barrels.FORBIDDEN):
                    err(f"barrels: {kind} gives {e['name']} (keep strong or progression items in the chests)")
                for fn in e.get("functions", []):
                    if "enchant" in fn["function"]:
                        err(f"barrels: {kind} enchants {e['name']}")
                    if fn["function"] == "minecraft:set_count" and fn["count"].get("max", 0) > 12:
                        err(f"barrels: {kind} gives up to {fn['count']['max']} {e['name']} (a barrel is a larder)")
    # every barrel table on disk is one of the kinds
    for path in glob.glob(os.path.join(DATA, "brasshaven", "loot_table", "chests", "barrel_*.json")):
        kind = os.path.basename(path)[len("barrel_"):-5]
        if kind not in barrels.KINDS:
            err(f"barrels: stale table {os.path.basename(path)} (not in wf/barrels.py)")


def check_loot():
    mod_items = mod_ids("items")
    for path in glob.glob(os.path.join(DATA, "brasshaven", "loot_table", "**", "*.json"), recursive=True):
        rel = os.path.relpath(path, DATA)
        table = json.load(open(path))
        for p in table["pools"]:
            for e in p["entries"]:
                if e["type"] != "minecraft:item":
                    continue
                ns, name = e["name"].split(":")
                if ns == "minecraft" and name not in MC_GAME["items"]:
                    err(f"{rel}: unknown item {e['name']}")
                if ns == "brasshaven" and mod_items and name not in mod_items:
                    err(f"{rel}: unknown mod item {e['name']}")


def check_worldgen():
    ns_dir = os.path.join(DATA, "brasshaven")
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "structure", "*.json")):
        s = json.load(open(path))
        sid = os.path.basename(path)[:-5]
        if not os.path.exists(res_path(s["start_pool"], "worldgen/template_pool", ".json")):
            err(f"structure {sid}: start pool missing")
        tag = s["biomes"].lstrip("#")
        if not os.path.exists(res_path(tag, "tags/worldgen/biome", ".json")):
            err(f"structure {sid}: biome tag {tag} missing")
    # structure sets: every structure in exactly one family set, spacing minima, wonders' exclusion zones,
    # no avoid cycle (wf/placement.py)
    from wf import defs, placement
    import wf.structures  # noqa: F401  (registers every structure)
    for msg in placement.check(DATA):
        err(msg)
    # site fit: every structure is a fitted_jigsaw whose terrain check suits how and where it is placed
    for msg in placement.check_fit(DATA):
        err(msg)
    for sid in placement.unassigned():
        warnings.append(f"structure {sid} has no family in tools/wf/placement.py (fallback set)")
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "structure", "*.json")):
        s = json.load(open(path))
        if s.get("project_start_to_heightmap"):
            pool = json.load(open(res_path(s["start_pool"], "worldgen/template_pool", ".json")))
            for el in pool["elements"]:
                if el["element"].get("ground_level_delta") is None:
                    err(f"{path}: heightmap-projected start piece without ground_level_delta (the beard would "
                        f"flatten the terrain at the template's lowest layer)")
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "template_pool", "**", "*.json"), recursive=True):
        pool = json.load(open(path))
        for el in pool["elements"]:
            e = el["element"]
            if e["element_type"] == chunking.ELEMENT_TYPE:
                check_chunked(path, e)
            elif e["element_type"] != "minecraft:single_pool_element":
                err(f"{path}: unexpected element type {e['element_type']}")
            elif e["location"] not in TEMPLATES:
                err(f"{path}: template {e['location']} missing")
            elif not chunking.cell_ok(*TEMPLATES[e["location"]]):
                err(f"{path}: template {e['location']} {TEMPLATES[e['location']]} is over the chunking threshold "
                    f"({chunking.SPLIT_AXIS} blocks wide / {chunking.SPLIT_ENTRIES} entries): gen_structures should split it")
            if not os.path.exists(res_path(e["processors"], "worldgen/processor_list", ".json")):
                err(f"{path}: processor list {e['processors']} missing")
    check_biome_refs()
    # codec ranges the game enforces when it loads features (a value out of range stops the server from starting)
    def walk(node, path):
        if isinstance(node, dict):
            off = node.get("offset")
            if isinstance(off, list) and len(off) == 3 and any(abs(v) > 15 for v in off if isinstance(v, int)):
                err(f"{path}: block predicate offset {off} outside -15..15")
            if node.get("type") == "minecraft:random_offset":
                for k in ("xz_spread", "y_spread"):
                    v = node.get(k)
                    if isinstance(v, int) and abs(v) > 16:
                        err(f"{path}: random_offset {k} {v} outside -16..16")
            for v in node.values():
                walk(v, path)
        elif isinstance(node, list):
            for v in node:
                walk(v, path)
    for path in glob.glob(os.path.join(DATA, "*", "worldgen", "*_feature", "*.json")):
        walk(json.load(open(path)), path)
    sets = {}
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "structure_set", "*.json")):
        salt = json.load(open(path))["placement"]["salt"]
        if salt in sets:
            err(f"duplicate structure_set salt {salt}: {path} / {sets[salt]}")
        sets[salt] = path


def check_biome_refs():
    """Every biome a data file names (biome tags, Forge biome modifiers, structures, predicates) is a vanilla biome, one
    of the mod's own biomes (data/brasshaven/worldgen/biome, tools/wf/worldbiomes.py: Crimson Mire, Volcanic Highlands,
    Pale Dunes) or a tag that exists. Any other brasshaven: biome id is an error."""
    biomes = set(MC_GAME["biomes"])
    ours = {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(DATA, "brasshaven", "worldgen", "biome", "*.json"))}

    def check(where, rid):
        if rid.startswith("#"):
            ns, path = rid[1:].split(":", 1)
            if ns == "minecraft":
                if path not in VANILLA_BIOME_TAGS:
                    err(f"{where}: unknown biome tag {rid}")
            elif not os.path.exists(os.path.join(DATA, ns, "tags", "worldgen", "biome", path + ".json")):
                err(f"{where}: biome tag {rid} missing")
        elif rid.startswith("brasshaven:"):
            if rid.split(":", 1)[1] not in ours:
                err(f"{where}: biome {rid} is neither vanilla nor one of the mod's biomes ({sorted(ours)})")
        elif ":" in rid and not rid.startswith("minecraft:"):
            err(f"{where}: biome {rid} is not a vanilla biome")
        elif rid.split(":")[-1] not in biomes:
            err(f"{where}: unknown biome {rid}")

    def values(v):
        v = v if isinstance(v, list) else [v]
        return [x.get("id") if isinstance(x, dict) else x for x in v]
    for path in glob.glob(os.path.join(DATA, "*", "tags", "worldgen", "biome", "**", "*.json"), recursive=True):
        for rid in values(json.load(open(path))["values"]):
            check(path, rid)
    # every "biome" / "biomes" field of every other data file: Forge biome modifiers, structures, advancement and
    # loot location predicates...
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("biome", "biomes") and (isinstance(v, str) or isinstance(v, list)
                                                 and all(isinstance(x, (str, dict)) for x in v)):
                    for rid in values(v):
                        if isinstance(rid, str):
                            check(path, rid)
                else:
                    walk(v, path)
        elif isinstance(node, list):
            for v in node:
                walk(v, path)
    for path in glob.glob(os.path.join(DATA, "**", "*.json"), recursive=True):
        if os.sep + os.path.join("tags", "worldgen", "biome") + os.sep not in path:
            walk(json.load(open(path)), path)
    # and the biome lists the structure tags are written from
    from wf import defs
    import wf.structures  # noqa: F401
    for sdef in defs.STRUCTURES:
        for b in sdef.biomes:
            if b.startswith("brasshaven:") and b.split(":", 1)[1] not in ours:
                err(f"structure {sdef.id}: biome {b} is neither vanilla nor one of the mod's biomes "
                    f"(tools/wf/structures, tools/wf/placement.py)")


def check_vanilla_overrides():
    """Our copies of vanilla village/outpost pools (wf/village.py) keep every vanilla element with its weight, and
    every element we add points at an existing template and processor list."""
    root = os.path.join(DATA, "minecraft", "worldgen", "template_pool")
    for path in glob.glob(os.path.join(root, "**", "*.json"), recursive=True):
        pid = "minecraft:" + os.path.relpath(path, root)[:-5].replace(os.sep, "/")
        pool = json.load(open(path))
        vanilla = VANILLA_POOLS.get(pid)
        if vanilla is None:
            err(f"{path}: overrides {pid}, which is not a vanilla 26.2 pool (wf/vanilla_village_pools.json)")
            continue
        if pool.get("fallback") != vanilla["fallback"]:
            err(f"{path}: fallback {pool.get('fallback')} differs from vanilla {vanilla['fallback']}")
        mine = list(pool["elements"])
        for v in vanilla["elements"]:
            if v in mine:
                mine.remove(v)
            else:
                err(f"{path}: vanilla element {v['element'].get('location') or v['element']['element_type']} "
                    f"(weight {v['weight']}) missing or changed")
        for el in mine:
            e = el["element"]
            if not 1 <= el["weight"] <= 150:
                err(f"{path}: weight {el['weight']} outside 1..150")
            if e["element_type"] not in ("minecraft:single_pool_element", "brasshaven:grounded_single"):
                err(f"{path}: unexpected element type {e['element_type']} for an added piece")
                continue
            if e["location"] not in TEMPLATES:
                err(f"{path}: template {e['location']} missing")
            procs = e["processors"]
            if isinstance(procs, str) and procs not in VANILLA_PROCESSORS and \
                    not os.path.exists(res_path(procs, "worldgen/processor_list", ".json")):
                err(f"{path}: processor list {procs} missing")
            if e["element_type"] == "brasshaven:grounded_single" and not isinstance(e.get("ground_level_delta"), int):
                err(f"{path}: grounded element without an integer ground_level_delta")


def check_chunked(path, e):
    """A brasshaven:chunked_template element (wf/chunking.py, ChunkedPoolElement.java): every column exists, matches
    the size and entry count the element declares, stays under the threshold, lies inside the piece and no two
    columns overlap."""
    size, cells = e.get("size"), e.get("cells") or []
    if not (isinstance(size, list) and len(size) == 3 and all(isinstance(v, int) and v > 0 for v in size)):
        err(f"{path}: chunked element with a bad size {size}")
        return
    if not cells:
        err(f"{path}: chunked element without columns")
    for key in ("projection", "processors"):
        if key not in e:
            err(f"{path}: chunked element without {key}")
    boxes = []
    for c in cells:
        loc, off, sz = c.get("location"), c.get("offset"), c.get("size")
        if loc not in TEMPLATES:
            err(f"{path}: column template {loc} missing")
            continue
        real_size, entries = TEMPLATES[loc]
        if list(real_size) != sz or entries != c.get("blocks"):
            err(f"{path}: column {loc} is {real_size} / {entries} entries, the element says {sz} / {c.get('blocks')}")
        if not chunking.cell_ok(real_size, entries):
            err(f"{path}: column {loc} {real_size} / {entries} entries is over the chunking threshold")
        if any(off[k] < 0 or off[k] + sz[k] > size[k] for k in range(3)):
            err(f"{path}: column {loc} at {off} sticks out of the piece {size}")
        boxes.append((off, sz, loc))
    for i, (o1, s1, l1) in enumerate(boxes):
        for o2, s2, l2 in boxes[i + 1:]:
            if all(o1[k] < o2[k] + s2[k] and o2[k] < o1[k] + s1[k] for k in (0, 2)):
                err(f"{path}: columns {l1} and {l2} overlap")


def check_item_id(where, rid):
    ns, name = rid.split(":") if ":" in rid else ("minecraft", rid)
    if ns == "minecraft" and name not in MC_GAME["items"]:
        err(f"{where}: unknown item {rid}")
    elif ns == "brasshaven" and name not in mod_ids("items"):
        err(f"{where}: unknown mod item {rid}")


def check_advancements():
    adv_dir = os.path.join(DATA, "brasshaven", "advancement")
    ids = set()
    for path in glob.glob(os.path.join(adv_dir, "**", "*.json"), recursive=True):
        ids.add("brasshaven:" + os.path.relpath(path, adv_dir)[:-5].replace(os.sep, "/"))
    for path in glob.glob(os.path.join(adv_dir, "**", "*.json"), recursive=True):
        rel = os.path.relpath(path, DATA)
        adv = json.load(open(path))
        if "parent" in adv and adv["parent"] not in ids:
            err(f"{rel}: parent {adv['parent']} missing")
        check_item_id(rel, adv["display"]["icon"]["id"])
        for crit in adv["criteria"].values():
            cond = crit.get("conditions", {})
            for it in cond.get("items", []):
                check_item_id(rel, it["items"])
            for e in cond.get("entity", []):
                if "type" in e["predicate"]:
                    err(f"{rel}: 26.2 entity predicates use 'entity_type', not 'type'")
                    continue
                t = e["predicate"]["entity_type"]
                ns, name = t.split(":")
                if (ns == "brasshaven" and name not in mod_ids("entities")) or (ns == "minecraft" and name not in MC_GAME["entities"]):
                    err(f"{rel}: unknown entity {t}")
            for p in cond.get("player", []):
                sid = p["predicate"]["location"]["structures"]
                if not os.path.exists(res_path(sid, "worldgen/structure", ".json")):
                    err(f"{rel}: unknown structure {sid}")
        for loot in adv.get("rewards", {}).get("loot", []):
            if not os.path.exists(res_path(loot, "loot_table", ".json")):
                err(f"{rel}: reward table {loot} missing")
    for path in glob.glob(os.path.join(DATA, "brasshaven", "recipe", "*.json")):
        r = json.load(open(path))
        rel = os.path.relpath(path, DATA)
        check_item_id(rel, r["result"]["id"])
        for v in list(r.get("key", {}).values()) + r.get("ingredients", []):
            if isinstance(v, str) and not v.startswith("#"):
                check_item_id(rel, v)


def check_chisel():
    """Chisel families (wf/chisel.py): known blocks, one family per block, data files in sync."""
    from wf import chisel
    for problem in chisel.check(set(MC_GAME["blocks"]), mod_ids("blocks")):
        err(problem)
    folder = os.path.join(DATA, "brasshaven", "chisel")
    expected = {os.path.basename(rel) for rel in chisel.data_files()}
    present = set(os.listdir(folder)) if os.path.isdir(folder) else set()
    for f in sorted(expected ^ present):
        err(f"chisel data file {f} out of date: run gen_data.py")


def check_lang():
    """Every registered id has a translation in both languages."""
    a = os.path.join(ASSETS, "brasshaven", "lang")
    for lang in ("en_us", "fr_fr"):
        table = json.load(open(os.path.join(a, lang + ".json"), encoding="utf-8"))
        for i in mod_ids("items"):
            if f"item.brasshaven.{i}" not in table and f"block.brasshaven.{i}" not in table:
                err(f"{lang}: missing name for item {i}")
        for e in mod_ids("entities"):
            if f"entity.brasshaven.{e}" not in table:
                err(f"{lang}: missing name for entity {e}")
        java = open(os.path.join(ROOT, "src", "main", "java", "com", "brasshaven", "registry", "ModItems.java")).read()
        import re
        for root, _, files in os.walk(os.path.join(ROOT, "src", "main", "java")):
            for f in files:
                text = open(os.path.join(root, f), encoding="utf-8").read()
                for key in re.findall(r'"((?:message|tooltip|key|chapter|itemGroup)\.[a-z0-9_.]+)"', text):
                    if not key.endswith(".") and key not in table:
                        err(f"{lang}: missing key {key} (used in {f})")


def check_model_bounds():
    """Minecraft refuses a model whose elements leave the -16..32 box (the item then shows as missing)."""
    for path in glob.glob(os.path.join(ASSETS, "*", "models", "**", "*.json"), recursive=True):
        for el in json.load(open(path, encoding="utf-8")).get("elements", []):
            for key in ("from", "to"):
                if any(v < -16 or v > 32 for v in el.get(key, [])):
                    err(f"{path}: element '{key}' {el[key]} outside -16..32")
                    break


def check_assets():
    """Models -> textures, items/blocks -> models, lang keys (only once assets exist)."""
    a = os.path.join(ASSETS, "brasshaven")
    if not os.path.isdir(a):
        return
    for path in glob.glob(os.path.join(a, "models", "**", "*.json"), recursive=True):
        model = json.load(open(path))
        for tex in model.get("textures", {}).values():
            if tex.startswith("#"):
                continue
            ns, p = tex.split(":") if ":" in tex else ("minecraft", tex)
            if ns == "brasshaven" and not os.path.exists(os.path.join(a, "textures", p + ".png")):
                err(f"{os.path.relpath(path, a)}: texture {tex} missing")
        parent = model.get("parent", "")
        if parent.startswith("brasshaven:"):
            if not os.path.exists(os.path.join(a, "models", parent.split(":")[1] + ".json")):
                err(f"{os.path.relpath(path, a)}: parent {parent} missing")


def check_guide():
    """The Wayfarer's Manual (wf/guide.py): known items and icons, translations, and an estimate of each page's
    length. GuideScreen splits a page that does not fit into continuation sheets, so a long page is never cut; this
    only warns when a page needs more than two sheets at the smallest book size (it would read better split in two)."""
    from wf import guide
    cats = {c for c, _i, _t in guide.CATEGORIES}
    items = mod_ids("items")
    seen = set()

    def item_ok(where, rid):
        ns, name = rid.split(":")
        if (ns == "minecraft" and name not in MC_GAME["items"]) or (ns == "brasshaven" and name not in items):
            err(f"{where}: unknown item {rid}")

    for c, icon, _t in guide.CATEGORIES:
        item_ok(f"guide category {c}", icon)
    for pid, cat, icon, _t, paras, related in guide.PAGES:
        if pid in seen:
            err(f"guide: duplicate page id {pid}")
        seen.add(pid)
        if cat not in cats:
            err(f"guide page {pid}: unknown category {cat}")
        if not paras:
            err(f"guide page {pid}: no text")
        item_ok(f"guide page {pid}", icon)
        for rid in related:
            item_ok(f"guide page {pid}", rid)
    for tid, icon, _t, page in guide.TIPS:
        item_ok(f"tip {tid}", icon)
        if page not in seen:
            err(f"tip {tid}: unknown manual page {page}")
    for lang in ("en_us", "fr_fr"):
        table = json.load(open(os.path.join(ASSETS, "brasshaven", "lang", lang + ".json"), encoding="utf-8"))
        keys = list(guide.UI) + [f"guide.brasshaven.cat.{c}" for c in cats]
        for pid, _c, _i, _t, paras, _r in guide.PAGES:
            keys += [f"guide.brasshaven.{pid}.title"] + [f"guide.brasshaven.{pid}.p{i}" for i in range(len(paras))]
        for k in keys:
            if k not in table:
                err(f"{lang}: missing manual text {k}: run gen_assets.py")
    for pid, (en, fr) in guide.sheet_counts().items():
        if max(en, fr) > 2:
            warnings.append(f"manual page {pid} needs {en} sheets in English, {fr} in French (1 page + "
                            f"{max(en, fr) - 1} continuations): consider splitting it into two pages")


def check_screen_fit(sw=427, sh=240):
    """Every mod screen fits a 427 x 240 GUI (1280 x 720 at the automatic GUI scale 3), title plate (5 px above the
    window) and hint line (13 px under it) included. The sizes are read from the Java constants, so a screen made
    bigger fails here instead of in the next in-game screenshot."""
    import re
    java = os.path.join(ROOT, "src", "main", "java", "com", "brasshaven")

    def consts(*rels):
        """``int NAME = expr;`` constants of these files, evaluated (expressions may use earlier constants)."""
        out = {}
        for rel in rels:
            src = open(os.path.join(java, rel), encoding="utf-8").read()
            for name, expr in re.findall(r"\bint ([A-Z][A-Z0-9_]*) = ([^;]+);", src):
                try:
                    out[name] = eval(re.sub(r"\b\w+\.(?=[A-Z])", "", expr).replace("/", "//"), {}, dict(out))
                except Exception:
                    pass
        return out

    def size(rel, pattern):
        """Width and height passed to an AbstractContainerScreen constructor (literals or constants)."""
        src = open(os.path.join(java, rel), encoding="utf-8").read()
        m = re.search(pattern, src)
        if not m:
            err(f"screen fit: no size found in {rel}: update check_screen_fit")
            return None
        c = consts("menu/TerminalMenu.java", rel)
        return [int(v) if v.isdigit() else c.get(v, 10 ** 6) for v in m.groups()]

    def fits(name, w, h, below=0):
        if w > sw or h + 5 + below > sh:
            err(f"screen fit: {name} is {w} x {h} (+5 px title plate, +{below} px hint): it does not fit {sw} x {sh}")

    gui = "client/gui/"
    c = consts(gui + "WaystoneScreen.java")
    fits("waystone screen", c["W"], c["H"], 13)
    c = consts(gui + "SettingsScreen.java")
    fits("settings screen", c["W"], c["H"])
    for rel, label in (("ChiselTableScreen.java", "chisel table"), ("TerminalScreen.java", "guild terminal")):
        wh = size(gui + rel, r"super\(menu, inv, title, (\w+), (\w+)\)")
        if wh:
            fits(label, *wh)
    # machines: MachineMenu.height() of the tallest kind (4 settings rows, buffer and player inventory)
    c = consts("menu/MachineMenu.java")
    content = max(c["ROW_Y0"] + 4 * c["ROW_H"], c["BUF_Y"] + 54)
    fits("machine screen", c["W"], content + 8 + 76 + 7)
    # screens that shrink to the screen: what they become at sw x sh must still hold their content
    c = consts(gui + "QuestJournalScreen.java")
    h = min(c["MAX_H"], sh - 20)
    fits("quest journal", c["W"], h, 13)
    chapters = open(os.path.join(java, "generated", "GeneratedContent.java"), encoding="utf-8").read().count("new Chapter(")
    if 22 + chapters * (c["TAB_H"] + 4) > h - 6:
        err(f"screen fit: the quest journal's {chapters} chapter tabs do not fit its {h} px window")
    c = consts(gui + "SkillTreeScreen.java")
    w, h = min(c["MAX_W"], sw - 8), min(c["MAX_H"], sh - 10)
    fits("talent tree", w, h)
    skills = open(os.path.join(java, "generated", "GeneratedSkills.java"), encoding="utf-8").read()
    cells = re.findall(r'new Skill\("[^"]+", "[^"]+", (\d+), (\d+),', skills)
    cols = max(int(x) for x, _ in cells) + 1
    rows = max(int(y) for _, y in cells) + 1
    branch_w = (w - 2 * c["MARGIN"] + c["GAP"]) // max(1, skills.count("new Branch("))
    col_w = min(c["MAX_COL_W"], (branch_w - c["GAP"] - 8 - c["NODE"]) // max(1, cols - 1))
    row_h = min(c["MAX_ROW_H"], (h - c["FOOTER"] - 5 - c["NODES_Y"] - c["NODE"]) // max(1, rows - 1))
    # talents side by side need room for the 3 px ring of an active talent
    if min(col_w, row_h) < c["NODE"] + 6:
        err(f"screen fit: talent tree cells are {col_w} x {row_h} px at {sw} x {sh}, under {c['NODE'] + 6}")
    c = consts(gui + "GuideScreen.java")
    fits("manual", c["MIN_W"], c["MIN_H"] + 3)  # its top is at least 8 px down, 3 more than the plate needs
    # the world map's options panel floats beside the live minimap (at most 160 px + its 4 px margin)
    c = consts("client/map/WorldMapScreen.java")
    fits("world map options panel", c["OPT_W"], c["OPT_H"] - 5)  # no title plate above it
    cc = consts("config/BrasshavenClientConfig.java")
    if 4 + cc["MINIMAP_MAX"] + 6 + c["OPT_W"] + 6 > sw:
        err(f"screen fit: the world map's options panel ({c['OPT_W']} px) covers a {cc['MINIMAP_MAX']} px minimap at {sw} px")
    if cc["MINIMAP_MAX"] + 21 + 8 > sh:
        err(f"screen fit: a {cc['MINIMAP_MAX']} px minimap and its plate do not fit {sh} px")
    # multiplayer screens (com.brasshaven.social, client/social)
    c = consts("social/TradeMenu.java")
    fits("trade screen", c["W"], c["H"])
    c = consts("social/PostMenu.java")
    fits("pneumatic post", c["W"], c["H"])
    if c["INV_Y"] + 76 > c["H"]:
        err(f"screen fit: the pneumatic post inventory ends at {c['INV_Y'] + 76}, past its {c['H']} px window")
    c = consts("social/PostMenu.java", "social/ContractMenu.java")
    if c["REWARD_Y"] + 36 > c["INV_Y"] or c["WANT_Y"] + 18 > c["INV_Y"]:
        err("screen fit: the contract board slots overlap the inventory")
    for rel, label in (("CompanyScreen.java", "company screen"), ("PlayerCardScreen.java", "player card")):
        c = consts("client/social/" + rel)
        fits(label, c["W"], c["H"], 13)
    c = consts("client/social/EmoteWheelScreen.java")
    if 2 * (c["RADIUS"] + c["CELL"] // 2) > sh or 2 * (c["RADIUS"] + c["CELL"] // 2) > sw:
        err("screen fit: the emote wheel does not fit")


def check_pack_meta():
    """Without a readable pack.mcmeta Forge skips the mod's assets and data entirely (missing models,
    and a LootModifierManager crash on the first block drop). 26.2: resources 88.0, data 107.1."""
    path = os.path.join(RES, "pack.mcmeta")
    if not os.path.exists(path):
        err("pack.mcmeta missing")
        return
    pack = json.load(open(path)).get("pack", {})
    if not isinstance(pack.get("description"), str):
        err("pack.mcmeta: description must be a plain string")
    if not (pack.get("min_format", 999) <= 88 and pack.get("max_format", 0) >= 107):
        err("pack.mcmeta: min_format/max_format must cover 88 (resources) to 107 (data)")


# ------------------------------------------------------------------ recipes: conflicts and survival obtainability
VANILLA_RECIPES = os.path.join(ROOT, "tools", "data", "vanilla_recipes_26.2.json")
# vanilla items a survival player can never get
CREATIVE_ONLY = {"bedrock", "barrier", "command_block", "chain_command_block", "repeating_command_block",
                 "command_block_minecart", "structure_block", "structure_void", "jigsaw", "light", "debug_stick",
                 "knowledge_book", "spawner", "trial_spawner", "vault", "end_portal_frame", "reinforced_deepslate",
                 "test_block", "test_instance_block", "petrified_oak_slab", "player_head", "budding_amethyst"}
# mod items handed out by Java code rather than a recipe or a loot table
JAVA_SOURCES = {
    "pearl": "right-click an open Pearl Oyster (PearlOysterBlock)",
    "reef_fish_bucket": "a water bucket on a Reef Fish",
    "wayfarer_manual": "given on first join",
    "wayfarer_atlas": "given on first join",
    "structure_compass": "the Guild Agent's survey contract (NpcQuests, wf/progression.py)",
}
# vanilla item tags used by recipes: a test telling whether an item id belongs to the tag (no tag files for vanilla)
VANILLA_TAGS = {
    "planks": lambda i: i.endswith("_planks"), "wooden_slabs": lambda i: i.endswith("_slab") and "planks" not in i,
    "logs": lambda i: i.endswith(("_log", "_wood", "_stem", "_hyphae")), "wool": lambda i: i.endswith("_wool"),
    "coals": lambda i: i in ("coal", "charcoal"), "candles": lambda i: i.endswith("candle"),
    "stone_tool_materials": lambda i: i in ("cobblestone", "cobbled_deepslate", "blackstone"),
    "stone_crafting_materials": lambda i: i in ("cobblestone", "cobbled_deepslate", "blackstone"),
    "wooden_tool_materials": lambda i: i.endswith("_planks"),
    "copper_tool_materials": lambda i: i == "copper_ingot", "iron_tool_materials": lambda i: i == "iron_ingot",
    "gold_tool_materials": lambda i: i == "gold_ingot", "diamond_tool_materials": lambda i: i == "diamond",
}


def _short(i):
    """Canonical ingredient id: vanilla ids without namespace, mod ids with it, tags with a leading #."""
    if i.startswith("#"):
        return "#" + _short(i[1:])
    return i[len("minecraft:"):] if i.startswith("minecraft:") else i


def _options(v):
    """A recipe ingredient (string, tag, list or legacy dict) as a tuple of canonical ids."""
    if isinstance(v, list):
        return tuple(o for x in v for o in _options(x))
    if isinstance(v, dict):
        return _options(v.get("item") or ("#" + v["tag"]))
    return (_short(v),)


@functools.lru_cache(maxsize=None)
def _mod_tag(tag):
    """Members of one of our item tags (brasshaven namespace or vanilla tags we add to), recursively."""
    ns, path = tag.split(":") if ":" in tag else ("minecraft", tag)
    out = set()
    p = os.path.join(DATA, ns, "tags", "item", path + ".json")
    if os.path.exists(p):
        for v in json.load(open(p))["values"]:
            v = v["id"] if isinstance(v, dict) else v
            out |= _mod_tag(v[1:]) if v.startswith("#") else {_short(v)}
    return out


def _overlap(a, b):
    """Can one item satisfy both ingredient options a and b (tuples)?"""
    def members_test(x):
        if not x.startswith("#"):
            return lambda i: i == x
        name = x[1:]
        test = VANILLA_TAGS.get(name)
        mod = _mod_tag(name)
        return lambda i: i in mod or (test is not None and test(i)) or i == x
    for x in a:
        for y in b:
            if x == y:
                return True
            if x.startswith("#") and y.startswith("#"):
                tx, ty = members_test(x), members_test(y)
                if any(tx(m) for m in _mod_tag(y[1:])) or any(ty(m) for m in _mod_tag(x[1:])) or \
                        (x[1:] in VANILLA_TAGS and y[1:] in VANILLA_TAGS and x[1:].split("_")[0] == y[1:].split("_")[0]):
                    return True
            elif x.startswith("#") and members_test(x)(y) or y.startswith("#") and members_test(y)(x):
                return True
    return False


def _shrink(pattern):
    rows = [r for r in pattern if r.strip()]
    if not rows:
        return []
    w = max(len(r) for r in rows)
    rows = [r.ljust(w) for r in rows]
    cols = [c for c in range(w) if any(r[c] != " " for r in rows)]
    return [r[cols[0]:cols[-1] + 1] for r in rows]


def _crafting_shape(r):
    """("shaped", grid of option tuples or None) or ("shapeless", [option tuples]) or None (not a crafting recipe)."""
    t = r["type"].split(":")[-1]
    if t == "crafting_shaped" or r["type"] == "shaped":
        pat = _shrink(r["pattern"])
        key = {k: _options(v) for k, v in r["key"].items()}
        return "shaped", [[key[c] if c != " " else None for c in row] for row in pat]
    if t == "crafting_shapeless" or r["type"] == "shapeless":
        return "shapeless", [_options(v) for v in r["ingredients"]]
    if t == "crafting_transmute":
        return "shapeless", [_options(r["input"]), _options(r["material"])]
    return None


def _match_multiset(xs, ys):
    if len(xs) != len(ys):
        return False
    if not xs:
        return True
    for j, y in enumerate(ys):
        if _overlap(xs[0], y) and _match_multiset(xs[1:], ys[:j] + ys[j + 1:]):
            return True
    return False


def _conflict(a, b):
    """Could one crafting grid match both shapes a and b (shaped recipes also match mirrored)?"""
    (ka, ga), (kb, gb) = a, b
    if ka == "shaped" and kb == "shaped":
        if len(ga) != len(gb) or len(ga[0]) != len(gb[0]):
            return False
        for cand in (gb, [row[::-1] for row in gb]):
            if all((x is None) == (y is None) and (x is None or _overlap(x, y))
                   for ra, rb in zip(ga, cand) for x, y in zip(ra, rb)):
                return True
        return False
    flat = lambda k, g: [c for row in g for c in row if c is not None] if k == "shaped" else g  # noqa: E731
    return _match_multiset(flat(ka, ga), flat(kb, gb))


def _all_recipes():
    out = {}
    for path in sorted(glob.glob(os.path.join(DATA, "brasshaven", "recipe", "*.json"))):
        out[os.path.basename(path)[:-5]] = json.load(open(path))
    return out


def check_recipe_conflicts(recipes):
    """Two crafting recipes that one grid can match: ours against ours, and ours against vanilla 26.2 (a shapeless
    recipe that steals a shaped pattern counts). Two cooking recipes of one input in one kind of furnace."""
    shapes = {n: _crafting_shape(r) for n, r in recipes.items()}
    shapes = {n: s for n, s in shapes.items() if s}
    names = sorted(shapes)
    res = lambda r: _short(r["result"]["id"] if isinstance(r["result"], dict) else r["result"])  # noqa: E731
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if _conflict(shapes[a], shapes[b]):
                (err if res(recipes[a]) != res(recipes[b]) else warnings.append)(
                    f"recipe {a} and recipe {b} match the same crafting grid")
    vanilla = json.load(open(VANILLA_RECIPES))["recipes"] if os.path.exists(VANILLA_RECIPES) else []
    for v in vanilla:
        sv = _crafting_shape(v)
        for n in names:
            if _conflict(shapes[n], sv) and res(recipes[n]) != v["result"]:
                err(f"recipe {n} matches the same grid as vanilla {v['result']}")
    cooked = {}
    for n, r in recipes.items():
        t = r["type"].split(":")[-1]
        if t in ("smelting", "blasting", "smoking", "campfire_cooking"):
            for o in _options(r["ingredient"]):
                if (t, o) in cooked:
                    err(f"recipes {cooked[(t, o)]} and {n}: two {t} results for {o}")
                cooked[(t, o)] = n


def _ingredient_groups(r):
    """[option tuples] every one of which must be obtainable to use recipe r."""
    t = r["type"].split(":")[-1]
    if t == "crafting_shaped":
        return [_options(v) for v in r["key"].values()]
    if t == "crafting_shapeless":
        return [_options(v) for v in r["ingredients"]]
    if t == "crafting_transmute":
        return [_options(r["input"]), _options(r["material"])]
    return [_options(r[k]) for k in ("template", "base", "addition", "ingredient") if r.get(k)]


def _loot_names(obj):
    """Every item a loot table (or any JSON) can give: the "name" of item entries, nested anywhere."""
    out = set()
    if isinstance(obj, dict):
        if obj.get("type") == "minecraft:item" and "name" in obj:
            out.add(_short(obj["name"]))
        for v in obj.values():
            out |= _loot_names(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= _loot_names(v)
    return out


def check_obtainable(recipes):
    """Dependency graph of every recipe: each mod item an ingredient needs must have a survival source (a loot table
    that is not a block's, a block placed by worldgen or a structure, a Java hand-out, or a recipe whose own
    ingredients are obtainable). Reports what is left, and cycles of items that only make each other."""
    have = {i for i in MC_GAME["items"] if i not in CREATIVE_ONLY}
    have |= {f"brasshaven:{i}" for i in JAVA_SOURCES}
    block_drops, placed = {}, set()
    for path in glob.glob(os.path.join(DATA, "*", "loot_table", "**", "*.json"), recursive=True):
        rel = os.path.relpath(path, DATA).replace(os.sep, "/")
        names = _loot_names(json.load(open(path)))
        if "/loot_table/blocks/" in "/" + rel:
            block_drops["brasshaven:" + os.path.basename(path)[:-5] if rel.startswith("brasshaven/") else rel] = names
        else:
            have |= names
    # blocks a feature places: only features some biome modifier adds to the world count (a feature no biome
    # uses, like a tree only a sapling grows, is not a source)
    used = set()
    for path in glob.glob(os.path.join(DATA, "*", "forge", "biome_modifier", "*.json")):
        f = json.load(open(path)).get("features", [])
        used |= set([f] if isinstance(f, str) else f)
    for fid in sorted(used):
        ns, name_ = fid.split(":", 1)
        pf = os.path.join(DATA, ns, "worldgen", "placed_feature", name_ + ".json")
        if not os.path.exists(pf):
            continue
        text = open(pf).read()
        for cf in re.findall(r'"feature": "([a-z0-9_]+:[a-z0-9_/]+)"', text):
            cns, cname = cf.split(":", 1)
            cpath = os.path.join(DATA, cns, "worldgen", "configured_feature", cname + ".json")
            if os.path.exists(cpath):
                text += open(cpath).read()
        placed |= set(re.findall(r'"Name": "(brasshaven:[a-z0-9_]+)"', text))
    # a sapling grows its tree (configured_feature <wood>_tree, GeneratedWorldBlocks)
    trees = {}
    for path in glob.glob(os.path.join(DATA, "brasshaven", "worldgen", "configured_feature", "*_tree.json")):
        sapling = "brasshaven:" + os.path.basename(path)[:-len("_tree.json")] + "_sapling"
        trees[sapling] = set(re.findall(r'"Name": "(brasshaven:[a-z0-9_]+)"', open(path).read()))
    if not TEMPLATE_BLOCKS:  # run on its own, without check_templates() having read the templates
        for path in glob.glob(os.path.join(DATA, "*", "structure", "**", "*.nbt"), recursive=True):
            TEMPLATE_BLOCKS.update(e["Name"] for e in nbt.load(path)["palette"])
    placed |= {b for b in TEMPLATE_BLOCKS if b.startswith("brasshaven:")}
    # in-world conversions: the Engraver's Chisel turns any block of a family into the others; an axe strips logs
    families = [{_short(b) for b in json.load(open(p))["blocks"]}
                for p in glob.glob(os.path.join(DATA, "*", "chisel", "*.json"))]
    java = os.path.join(ROOT, "src", "main", "java", "com", "brasshaven", "generated", "GeneratedWorldBlocks.java")
    strips = re.findall(r'block\("([a-z0-9_]+)", p -> new WoodBlocks\.Log\(GeneratedWorldBlocks\.([A-Z0-9_]+),',
                        open(java).read()) if os.path.exists(java) else []
    strips = [(f"brasshaven:{a}", f"brasshaven:{b.lower()}") for a, b in strips]
    tag_cache = {}

    def ok(options):
        for o in options:
            if o.startswith("#"):
                if o[1:] in VANILLA_TAGS or ":" not in o[1:]:
                    return True
                members = tag_cache.setdefault(o, _mod_tag(o[1:]))
                if any(m in have for m in members):
                    return True
            elif o in have:
                return True
        return False
    changed = True
    while changed:
        changed = False
        for fam in families:
            if fam & have and not fam <= have:
                have |= fam
                changed = True
        for sapling, blocks in trees.items():
            if sapling in have and not blocks <= placed:
                placed |= blocks
                changed = True
        for log, stripped in strips:
            if log in have and stripped not in have:
                have.add(stripped)
                changed = True
        for b, drops in block_drops.items():
            if (b in placed or b in have) and not drops <= have:
                have |= drops
                changed = True
        for r in recipes.values():
            out = _short(r["result"]["id"] if isinstance(r["result"], dict) else r["result"])
            if out not in have and all(ok(g) for g in _ingredient_groups(r)):
                have.add(out)
                changed = True
    needs = {}  # unobtainable ingredient -> recipes needing it
    edges = {}  # result -> its unobtainable ingredients
    for n, r in sorted(recipes.items()):
        out = _short(r["result"]["id"] if isinstance(r["result"], dict) else r["result"])
        for g in _ingredient_groups(r):
            if not ok(g):
                needs.setdefault(" or ".join(g), []).append(n)
                edges.setdefault(out, set()).update(g)
    for ing, users in sorted(needs.items()):
        err(f"{ing} has no survival source (no loot, worldgen, recipe chain); needed by {', '.join(users)}")
    # cycles among the unobtainable: items that only come from recipes needing each other
    index, low, stack, on, sccs = {}, {}, [], set(), []

    def visit(v):
        index[v] = low[v] = len(index)
        stack.append(v)
        on.add(v)
        for w in edges.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in edges.get(v, ()):
                sccs.append(sorted(comp))
    for v in list(edges):
        if v not in index:
            visit(v)
    for comp in sccs:
        err(f"recipe cycle without a base source: {' -> '.join(comp + comp[:1])}")
    return have


def check_recipes():
    recipes = _all_recipes()
    check_recipe_conflicts(recipes)
    have = check_obtainable(recipes)
    for i in sorted(mod_ids("items")):
        if f"brasshaven:{i}" not in have and not i.endswith("_spawn_egg") and i not in TECHNICAL_BLOCKS:
            warnings.append(f"brasshaven:{i} cannot be obtained in survival (creative or commands only)")


REGISTRY_IDS = os.path.join(ROOT, "tools", "data", "registry_ids.json")
REGISTRY_KINDS = ("block", "item", "entity_type", "block_entity_type", "menu")
REGISTRY_DOC = [
    "Every registry id the mod ever shipped (worlds and players' inventories keep them). tools/validate.py records new",
    "ids here by itself and refuses an id that disappears: a renamed id needs an entry in 'aliases' (old -> new, the",
    "world's blocks/items/creatures become the new one: release/RegistryRemap, Forge MissingMappingsEvent), a deleted",
    "one an entry in 'removed' (old -> why; the world drops it). Never delete an id from 'ids'.",
]


def current_registry_ids():
    """{kind: ids registered by the current sources}: the Java registry scan, plus the generated assets of each id."""
    a = os.path.join(ASSETS, "brasshaven")
    lang = json.load(open(os.path.join(a, "lang", "en_us.json"), encoding="utf-8"))
    java = ""
    for base, _dirs, files in os.walk(os.path.join(ROOT, "src", "main", "java")):
        for f in files:
            if f.endswith(".java"):
                java += open(os.path.join(base, f), encoding="utf-8").read()
    listing = lambda d: {f[:-5] for f in os.listdir(os.path.join(a, d)) if f.endswith(".json")} \
        if os.path.isdir(os.path.join(a, d)) else set()
    return {
        "block": set(mod_ids("blocks")) | listing("blockstates"),
        "item": set(mod_ids("items")) | listing("items"),
        "entity_type": set(mod_ids("entities")) | {k.split(".")[2] for k in lang
                                                  if k.startswith("entity.brasshaven.") and k.count(".") == 2},
        "block_entity_type": set(re.findall(r'BLOCK_ENTITIES\.register\(\s*"([a-z0-9_/]+)"', java)),
        "menu": set(re.findall(r'MENUS\.register\(\s*"([a-z0-9_/]+)"', java)),
    }


def check_registry_ids(record=True):
    """World compatibility across updates: no registry id silently removed or renamed (tools/data/registry_ids.json)."""
    data = json.load(open(REGISTRY_IDS, encoding="utf-8")) if os.path.isfile(REGISTRY_IDS) else {}
    ids, aliases, removed = (data.get(k) or {} for k in ("ids", "aliases", "removed"))
    current = current_registry_ids()
    changed = not os.path.isfile(REGISTRY_IDS)
    for kind in REGISTRY_KINDS:
        known = set(ids.get(kind, []))
        cur = current[kind]
        al, rm = aliases.get(kind, {}), removed.get(kind, {})
        for old in sorted(known - cur):
            if old in al:
                continue
            if old not in rm:
                err(f"registry id brasshaven:{old} ({kind}) is gone: worlds and inventories still hold it. Put it back, "
                    f"or add it to tools/data/registry_ids.json, under \"aliases\" -> \"{kind}\" (\"{old}\": \"new_id\", "
                    f"remapped in old worlds) or \"removed\" -> \"{kind}\" (\"{old}\": \"why\", dropped from old worlds)")
        for old, new in sorted(al.items()):
            target = new.split(":", 1)[1] if new.startswith("brasshaven:") else new
            if old in cur:
                err(f"registry_ids.json: alias {kind} {old} -> {new}, but {old} is still registered")
            elif ":" not in target and target not in cur:
                err(f"registry_ids.json: alias {kind} {old} -> {new}, but {new} is not registered")
            if old in rm:
                err(f"registry_ids.json: {kind} {old} is both an alias and removed")
        for old in rm:
            if old in cur:
                err(f"registry_ids.json: {kind} {old} is listed as removed but is still registered")
        if not cur <= known:
            changed = True
        ids[kind] = sorted(known | cur)
    if changed and record and not errors:
        out = {"_doc": REGISTRY_DOC,
               "aliases": {k: dict(sorted(aliases.get(k, {}).items())) for k in REGISTRY_KINDS},
               "removed": {k: dict(sorted(removed.get(k, {}).items())) for k in REGISTRY_KINDS},
               "ids": {k: ids[k] for k in REGISTRY_KINDS}}
        with open(REGISTRY_IDS, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print("recorded the new registry ids in tools/data/registry_ids.json")
    elif changed and not record:
        warnings.append("new registry ids are not in tools/data/registry_ids.json yet (python3 tools/validate.py records them)")


def check_progression():
    """The progression ladder (wf/progression.py): every step is a quest or a contract, the first-join kit holds no
    Structure Compass, the compass comes from its contract and from no earlier reward, its recipe needs Lithite, and
    docs/PROGRESSION.md names every step."""
    from wf import progression, npcs
    adv_dir = os.path.join(DATA, "brasshaven", "advancement")
    quests = json.load(open(os.path.join(DATA, "brasshaven", "quests.json")))
    in_chapters = {q for qs in quests.values() for q in qs}
    items = mod_ids("items")
    for i in progression.STARTER_KIT:
        if i not in items:
            err(f"progression: starter kit item {i} is not registered")
    if "structure_compass" in progression.STARTER_KIT:
        err("progression: the Structure Compass must be earned, not in the starter kit")
    steps = progression.steps()
    if len(set(steps)) != len(steps):
        err("progression: a ladder step is listed twice")
    for step in steps:
        if step.startswith("npc/"):
            if step[4:] not in npcs.BY_ID:
                err(f"progression: unknown contract {step}")
        elif not os.path.exists(os.path.join(adv_dir, step + ".json")) or step not in in_chapters:
            err(f"progression: unknown quest {step}")
    compass = "brasshaven:structure_compass"
    q = npcs.BY_ID.get(progression.COMPASS_CONTRACT)
    if q is None or (compass, 1) not in q.rewards:
        err(f"progression: contract {progression.COMPASS_CONTRACT} must give the Structure Compass")
    if "npc/" + progression.COMPASS_CONTRACT not in steps:
        err("progression: the compass contract is not on the ladder")
    else:
        # nothing on the ladder before the compass step hands out a compass
        for step in steps[:steps.index("npc/" + progression.COMPASS_CONTRACT)]:
            if step.startswith("npc/"):
                if any(i == compass for i, _c in npcs.BY_ID[step[4:]].rewards):
                    err(f"progression: {step} gives a Structure Compass before the compass step")
            else:
                adv = json.load(open(os.path.join(adv_dir, step + ".json")))
                for table in adv.get("rewards", {}).get("loot", []):
                    path = res_path(table, "loot_table", ".json")
                    if os.path.exists(path) and compass in open(path).read():
                        err(f"progression: quest {step} gives a Structure Compass before the compass step")
    recipe = os.path.join(DATA, "brasshaven", "recipe", "structure_compass.json")
    if os.path.exists(recipe) and "brasshaven:lithite_shard" not in json.dumps(json.load(open(recipe))):
        err("progression: the Structure Compass recipe must need a Lithite Shard (a later material)")
    doc = os.path.join(ROOT, "docs", "PROGRESSION.md")
    if not os.path.exists(doc):
        err("progression: docs/PROGRESSION.md missing")
    else:
        text = open(doc, encoding="utf-8").read()
        for step in steps:
            if f"`{step}`" not in text:
                warnings.append(f"docs/PROGRESSION.md does not name the ladder step `{step}`")

def check_denizens():
    """The peoples' trades name real items, every people and creature has a model, a spawn egg and a loot table."""
    from wf import denizens, mobs
    known = {f"minecraft:{i}" for i in MC_GAME["items"]} | {f"brasshaven:{i}" for i in mod_ids("items")}
    for e in denizens.check_trades(known):
        err(f"denizens: {e}")
    models = {b.__module__.rsplit(".", 1)[1] for b in mobs.MODELS}
    for eid in denizens.ALL_IDS:
        if eid not in models:
            err(f"denizens: {eid} has no model in tools/wf/mobs")
        if eid not in mod_ids("entities"):
            err(f"denizens: {eid} is not registered in ModEntities")
        if f"{eid}_spawn_egg" not in mod_ids("items"):
            err(f"denizens: {eid} has no spawn egg")
        if not os.path.exists(res_path(f"brasshaven:entities/{eid}", "loot_table", ".json")):
            err(f"denizens: {eid} has no loot table")


def check_release_files():
    """Recommended configs of the packs follow the config classes (tools/make_modpack.py)."""
    import make_modpack
    for p in make_modpack.check_configs():
        err(p)


def main():
    if "--registry-ids" in sys.argv:
        # CI: only the world-compatibility check, nothing written
        check_registry_ids(record=False)
        for w in sorted(set(warnings)):
            print("warning:", w)
        for e in errors:
            print("ERROR:", e)
        print(f"{len(errors)} errors")
        sys.exit(1 if errors else 0)
    check_pack_meta()
    check_templates()
    check_recipes()
    check_loot()
    check_barrel_tables()
    check_worldgen()
    check_vanilla_overrides()
    check_assets()
    check_model_bounds()
    check_advancements()
    check_lang()
    check_tags()
    check_chisel()
    check_guide()
    check_progression()
    check_screen_fit()
    check_denizens()
    import validate_world  # the Brasshaven biomes and terrain touches (tools/gen_world.py)
    for e in validate_world.check():
        err(f"world: {e}")
    from wf import machines
    for e in machines.check_gui():
        err(e)
    check_release_files()
    check_registry_ids()
    for w in sorted(set(warnings)):
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(set(warnings))} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Static validation of every generated resource, without needing the game.

Checks block ids/states in structure templates (against 1.20 data, the version the
templates are stamped with; DataFixerUpper upgrades them), item ids in loot tables
and biome ids (against 26.1 data, the closest release to 26.2), plus every
cross-reference between worldgen files, textures, models and translations.
Exit code is non-zero when anything is wrong.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf import nbt  # noqa: E402

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
# Blocks renamed after 1.20 that DataFixerUpper converts (old -> new)
UPGRADED = {"grass": "short_grass", "chain": "iron_chain"}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def res_path(rl, kind, ext):
    ns, path = rl.split(":", 1)
    return os.path.join(DATA, ns, kind, path + ext)


def mod_ids(kind):
    """Ids registered by the Java side, read straight from the registry classes."""
    import re
    java = os.path.join(ROOT, "src", "main", "java", "com", "wayfarers")
    files = {"blocks": ["registry/ModBlocks.java", "generated/ModDecor.java", "generated/GeneratedMetals.java",
                        "generated/GeneratedMachines.java", "generated/GeneratedFurniture.java",
                        "generated/GeneratedWorldBlocks.java"],
             "items": ["registry/ModItems.java", "generated/ModDecor.java", "generated/BossGear.java",
                       "generated/GeneratedMetals.java", "generated/GeneratedMachines.java",
                       "generated/GeneratedFurniture.java", "generated/GeneratedWorldBlocks.java"],
             "entities": ["registry/ModEntities.java"]}[kind]
    ids = set()
    for f in files:
        text = open(os.path.join(java, f), encoding="utf-8").read()
        if kind == "blocks" and f.endswith("GeneratedMetals.java"):
            ids |= set(re.findall(r'\bblock\("([a-z0-9_]+)"', text))
            continue
        ids |= set(re.findall(r'(?:register|simple|armor|block|pillar|door|egg|stairs|slab|wall|weapon|remembrance|spell|item|gear|machine|furniture)\("([a-z0-9_]+)"', text))
    return ids


HORIZONTAL = ["north", "south", "east", "west"]


def _mod_states():
    """Block-state properties of the mod's machines, furniture and crate (wf tables)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from wf import furniture, machines
    out = {"compacting_crate": {"facing": HORIZONTAL}, "chisel_table": {"facing": HORIZONTAL}}
    for mid in machines.MACHINES:
        out[mid] = {"facing": HORIZONTAL + ["up", "down"], "powered": ["false", "true"]}
    for fid, f in furniture.FURNITURE.items():
        out[fid] = {} if f["mount"] == "none" else {"axis": ["x", "y", "z"]} if f["mount"] == "axis" else {"facing": HORIZONTAL}
    return out


MOD_STATES = _mod_states()


def check_templates():
    mod_blocks = mod_ids("blocks")
    loot_refs = set()
    for path in sorted(glob.glob(os.path.join(DATA, "*", "structure", "**", "*.nbt"), recursive=True)):
        rel = os.path.relpath(path, DATA)
        d = nbt.load(path)
        size = d["size"]
        for entry in d["palette"]:
            ns, name = entry["Name"].split(":")
            props = entry.get("Properties", {})
            if ns == "wayfarers":
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
            if not data:
                continue
            if "LootTable" in data:
                loot_refs.add((data["LootTable"], rel))
            if "SpawnData" in data:
                ens, eid = data["SpawnData"]["entity"]["id"].split(":")
                if (ens == "minecraft" and eid not in MC_GAME["entities"]) or (ens == "wayfarers" and eid not in mod_ids("entities")):
                    err(f"{rel}: spawner entity {eid} unknown")
            if "pool" in data and data["pool"] != "minecraft:empty":
                if not os.path.exists(res_path(data["pool"], "worldgen/template_pool", ".json")):
                    err(f"{rel}: jigsaw pool {data['pool']} missing")
        for e in d["entities"]:
            eid = e["nbt"]["id"].split(":")[1]
            if eid not in MC_GAME["entities"]:
                err(f"{rel}: entity {eid} unknown")
    for ref, rel in sorted(loot_refs):
        if ref.startswith("wayfarers:") and not os.path.exists(res_path(ref, "loot_table", ".json")):
            err(f"{rel}: loot table {ref} missing")


def check_tags():
    for path in glob.glob(os.path.join(DATA, "*", "tags", "item", "**", "*.json"), recursive=True):
        for v in json.load(open(path))["values"]:
            v = v["id"] if isinstance(v, dict) else v
            if not v.startswith("#"):
                check_item_id(os.path.relpath(path, DATA), v)
    for path in glob.glob(os.path.join(DATA, "*", "tags", "block", "**", "*.json"), recursive=True):
        for v in json.load(open(path))["values"]:
            v = v["id"] if isinstance(v, dict) else v
            if v.startswith("wayfarers:") and v.split(":")[1] not in mod_ids("blocks"):
                err(f"{os.path.relpath(path, DATA)}: unknown mod block {v}")
    for b in mod_ids("blocks"):
        if b not in ("grave", "sealed_bars", "warden_altar", "void_altar", "mist_gate", "boss_seal") and \
                not os.path.exists(os.path.join(DATA, "wayfarers", "loot_table", "blocks", b + ".json")):
            err(f"block {b} has no loot table (would drop nothing)")


def check_loot():
    mod_items = mod_ids("items")
    for path in glob.glob(os.path.join(DATA, "wayfarers", "loot_table", "**", "*.json"), recursive=True):
        rel = os.path.relpath(path, DATA)
        table = json.load(open(path))
        for p in table["pools"]:
            for e in p["entries"]:
                if e["type"] != "minecraft:item":
                    continue
                ns, name = e["name"].split(":")
                if ns == "minecraft" and name not in MC_GAME["items"]:
                    err(f"{rel}: unknown item {e['name']}")
                if ns == "wayfarers" and mod_items and name not in mod_items:
                    err(f"{rel}: unknown mod item {e['name']}")


def check_worldgen():
    ns_dir = os.path.join(DATA, "wayfarers")
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "structure", "*.json")):
        s = json.load(open(path))
        sid = os.path.basename(path)[:-5]
        if not os.path.exists(res_path(s["start_pool"], "worldgen/template_pool", ".json")):
            err(f"structure {sid}: start pool missing")
        tag = s["biomes"].lstrip("#")
        if not os.path.exists(res_path(tag, "tags/worldgen/biome", ".json")):
            err(f"structure {sid}: biome tag {tag} missing")
        if not os.path.exists(os.path.join(ns_dir, "worldgen", "structure_set", sid + ".json")):
            err(f"structure {sid}: no structure_set")
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "template_pool", "**", "*.json"), recursive=True):
        pool = json.load(open(path))
        for el in pool["elements"]:
            e = el["element"]
            if not os.path.exists(res_path(e["location"], "structure", ".nbt")):
                err(f"{path}: template {e['location']} missing")
            if not os.path.exists(res_path(e["processors"], "worldgen/processor_list", ".json")):
                err(f"{path}: processor list {e['processors']} missing")
    biomes = set(MC_GAME["biomes"])
    for path in glob.glob(os.path.join(ns_dir, "tags", "worldgen", "biome", "**", "*.json"), recursive=True):
        for v in json.load(open(path))["values"]:
            rid = v["id"] if isinstance(v, dict) else v
            if rid.startswith("#minecraft:"):
                if rid[11:] not in VANILLA_BIOME_TAGS:
                    err(f"{path}: unknown biome tag {rid}")
            elif rid.startswith("minecraft:") and rid[10:] not in biomes:
                err(f"{path}: unknown biome {rid}")
    sets = {}
    for path in glob.glob(os.path.join(ns_dir, "worldgen", "structure_set", "*.json")):
        salt = json.load(open(path))["placement"]["salt"]
        if salt in sets:
            err(f"duplicate structure_set salt {salt}: {path} / {sets[salt]}")
        sets[salt] = path


def check_item_id(where, rid):
    ns, name = rid.split(":") if ":" in rid else ("minecraft", rid)
    if ns == "minecraft" and name not in MC_GAME["items"]:
        err(f"{where}: unknown item {rid}")
    elif ns == "wayfarers" and name not in mod_ids("items"):
        err(f"{where}: unknown mod item {rid}")


def check_advancements():
    adv_dir = os.path.join(DATA, "wayfarers", "advancement")
    ids = set()
    for path in glob.glob(os.path.join(adv_dir, "**", "*.json"), recursive=True):
        ids.add("wayfarers:" + os.path.relpath(path, adv_dir)[:-5].replace(os.sep, "/"))
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
                if (ns == "wayfarers" and name not in mod_ids("entities")) or (ns == "minecraft" and name not in MC_GAME["entities"]):
                    err(f"{rel}: unknown entity {t}")
            for p in cond.get("player", []):
                sid = p["predicate"]["location"]["structures"]
                if not os.path.exists(res_path(sid, "worldgen/structure", ".json")):
                    err(f"{rel}: unknown structure {sid}")
        for loot in adv.get("rewards", {}).get("loot", []):
            if not os.path.exists(res_path(loot, "loot_table", ".json")):
                err(f"{rel}: reward table {loot} missing")
    for path in glob.glob(os.path.join(DATA, "wayfarers", "recipe", "*.json")):
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
    folder = os.path.join(DATA, "wayfarers", "chisel")
    expected = {os.path.basename(rel) for rel in chisel.data_files()}
    present = set(os.listdir(folder)) if os.path.isdir(folder) else set()
    for f in sorted(expected ^ present):
        err(f"chisel data file {f} out of date: run gen_data.py")


def check_lang():
    """Every registered id has a translation in both languages."""
    a = os.path.join(ASSETS, "wayfarers", "lang")
    for lang in ("en_us", "fr_fr"):
        table = json.load(open(os.path.join(a, lang + ".json"), encoding="utf-8"))
        for i in mod_ids("items"):
            if f"item.wayfarers.{i}" not in table and f"block.wayfarers.{i}" not in table:
                err(f"{lang}: missing name for item {i}")
        for e in mod_ids("entities"):
            if f"entity.wayfarers.{e}" not in table:
                err(f"{lang}: missing name for entity {e}")
        java = open(os.path.join(ROOT, "src", "main", "java", "com", "wayfarers", "registry", "ModItems.java")).read()
        import re
        for root, _, files in os.walk(os.path.join(ROOT, "src", "main", "java")):
            for f in files:
                text = open(os.path.join(root, f), encoding="utf-8").read()
                for key in re.findall(r'"((?:message|tooltip|key|chapter|itemGroup)\.[a-z0-9_.]+)"', text):
                    if not key.endswith(".") and key not in table:
                        err(f"{lang}: missing key {key} (used in {f})")


def check_assets():
    """Models -> textures, items/blocks -> models, lang keys (only once assets exist)."""
    a = os.path.join(ASSETS, "wayfarers")
    if not os.path.isdir(a):
        return
    for path in glob.glob(os.path.join(a, "models", "**", "*.json"), recursive=True):
        model = json.load(open(path))
        for tex in model.get("textures", {}).values():
            if tex.startswith("#"):
                continue
            ns, p = tex.split(":") if ":" in tex else ("minecraft", tex)
            if ns == "wayfarers" and not os.path.exists(os.path.join(a, "textures", p + ".png")):
                err(f"{os.path.relpath(path, a)}: texture {tex} missing")
        parent = model.get("parent", "")
        if parent.startswith("wayfarers:"):
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
        if (ns == "minecraft" and name not in MC_GAME["items"]) or (ns == "wayfarers" and name not in items):
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
        table = json.load(open(os.path.join(ASSETS, "wayfarers", "lang", lang + ".json"), encoding="utf-8"))
        keys = list(guide.UI) + [f"guide.wayfarers.cat.{c}" for c in cats]
        for pid, _c, _i, _t, paras, _r in guide.PAGES:
            keys += [f"guide.wayfarers.{pid}.title"] + [f"guide.wayfarers.{pid}.p{i}" for i in range(len(paras))]
        for k in keys:
            if k not in table:
                err(f"{lang}: missing manual text {k}: run gen_assets.py")
    for pid, (en, fr) in guide.sheet_counts().items():
        if max(en, fr) > 2:
            warnings.append(f"manual page {pid} needs {en} sheets in English, {fr} in French (1 page + "
                            f"{max(en, fr) - 1} continuations): consider splitting it into two pages")


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


def main():
    check_pack_meta()
    check_templates()
    check_loot()
    check_worldgen()
    check_assets()
    check_advancements()
    check_lang()
    check_tags()
    check_chisel()
    check_guide()
    from wf import machines
    for e in machines.check_gui():
        err(e)
    import validate_world
    if validate_world.main() != 0:
        err("world overhaul pack: see the errors above")
    for w in sorted(set(warnings)):
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(set(warnings))} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

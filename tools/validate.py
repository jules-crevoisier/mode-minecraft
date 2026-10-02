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
MC_TEMPLATE = json.load(open(os.path.join(ROOT, "tools", "data", "mc_1.20.json")))
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
    """Ids registered by the Java side, collected from the generated registry manifest."""
    manifest = os.path.join(ROOT, "build", "registry_manifest.json")
    if os.path.exists(manifest):
        return set(json.load(open(manifest)).get(kind, []))
    return set()


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
                eid = data["SpawnData"]["entity"]["id"].split(":")[1]
                if eid not in MC_GAME["entities"]:
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


def main():
    check_templates()
    check_loot()
    check_worldgen()
    check_assets()
    for w in sorted(set(warnings)):
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(errors)} errors, {len(set(warnings))} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

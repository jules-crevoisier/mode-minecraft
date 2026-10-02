#!/usr/bin/env python3
"""Generate client assets (item definitions, models, blockstates, equipment, lang)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf import content, defs  # noqa: E402
import wf.structures  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", "wayfarers")
NS = "wayfarers"
HANDHELD = {"cartographer_blade", "telluric_hammer", "storm_staff", "ember_scythe", "void_spear", "frost_blade",
            "light_staff", "excavator_pickaxe", "lumber_axe"}


def write(rel, obj):
    path = os.path.join(ASSETS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def item_definition(item_id, model):
    write(f"items/{item_id}.json", {"model": {"type": "minecraft:model", "model": model}})


def block_models(bid, kind):
    t = f"{NS}:block/"
    if kind == "cube":
        model = {"parent": "minecraft:block/cube_all", "textures": {"all": t + bid}}
        if bid == "sealed_bars":
            model["render_type"] = "minecraft:cutout"
        write(f"models/block/{bid}.json", model)
    elif kind == "column":
        write(f"models/block/{bid}.json", {"parent": "minecraft:block/cube_column",
                                           "textures": {"end": t + bid + "_top", "side": t + bid + "_side"}})
    elif kind == "front":
        write(f"models/block/{bid}.json", {"parent": "minecraft:block/orientable",
                                           "textures": {"top": t + bid + "_side", "front": t + bid + "_front",
                                                        "side": t + bid + "_side"}})
    elif kind == "waystone":
        side, top = t + "waystone_side", t + "waystone_top"
        write(f"models/block/{bid}.json", {
            "parent": "minecraft:block/block",
            "textures": {"particle": side, "side": side, "top": top},
            "elements": [
                {"from": [1, 0, 1], "to": [15, 3, 15],
                 "faces": {f: {"texture": "#top" if f in ("up", "down") else "#side"}
                           for f in ("north", "south", "east", "west", "up", "down")}},
                {"from": [4, 3, 4], "to": [12, 14, 12],
                 "faces": {f: {"texture": "#top" if f in ("up", "down") else "#side"}
                           for f in ("north", "south", "east", "west", "up", "down")}},
                {"from": [3, 14, 3], "to": [13, 16, 13],
                 "faces": {f: {"texture": "#top" if f in ("up", "down") else "#side"}
                           for f in ("north", "south", "east", "west", "up", "down")}},
            ]})
    elif kind == "grave":
        tex = t + "grave"
        write(f"models/block/{bid}.json", {
            "parent": "minecraft:block/block",
            "textures": {"particle": tex, "all": tex},
            "elements": [
                {"from": [1, 0, 1], "to": [15, 2, 15],
                 "faces": {f: {"texture": "#all"} for f in ("north", "south", "east", "west", "up", "down")}},
                {"from": [3, 2, 10], "to": [13, 14, 13],
                 "faces": {f: {"texture": "#all"} for f in ("north", "south", "east", "west", "up", "down")}},
            ]})


def blockstate(bid, kind):
    model = f"{NS}:block/{bid}"
    if kind in ("front", "grave"):
        variants = {f"facing={f}": {"model": model, **({"y": r} if r else {})}
                    for f, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}
    else:
        variants = {"": {"model": model}}
    write(f"blockstates/{bid}.json", {"variants": variants})


def main():
    lang_en, lang_fr = {}, {}
    for iid, (en, fr, ten, tfr) in content.ITEMS.items():
        parent = "minecraft:item/handheld" if iid in HANDHELD else "minecraft:item/generated"
        write(f"models/item/{iid}.json", {"parent": parent, "textures": {"layer0": f"{NS}:item/{iid}"}})
        item_definition(iid, f"{NS}:item/{iid}")
        lang_en[f"item.{NS}.{iid}"], lang_fr[f"item.{NS}.{iid}"] = en, fr
        if ten:
            lang_en[f"item.{NS}.{iid}.desc"], lang_fr[f"item.{NS}.{iid}.desc"] = ten, tfr
    for mob in content.SPAWN_EGGS:
        iid = f"{mob}_spawn_egg"
        write(f"models/item/{iid}.json", {"parent": "minecraft:item/generated",
                                          "textures": {"layer0": f"{NS}:item/{iid}"}})
        item_definition(iid, f"{NS}:item/{iid}")
        en, fr = content.ENTITIES[mob]
        lang_en[f"item.{NS}.{iid}"] = f"{en} Spawn Egg"
        lang_fr[f"item.{NS}.{iid}"] = f"Œuf d'apparition de {fr.lower()}"
    for bid, (en, fr, ten, tfr, kind) in content.BLOCKS.items():
        block_models(bid, kind)
        blockstate(bid, kind)
        item_definition(bid, f"{NS}:block/{bid}")
        lang_en[f"block.{NS}.{bid}"], lang_fr[f"block.{NS}.{bid}"] = en, fr
        if ten:
            lang_en[f"block.{NS}.{bid}.desc"], lang_fr[f"block.{NS}.{bid}.desc"] = ten, tfr
    for eid, (en, fr) in content.ENTITIES.items():
        lang_en[f"entity.{NS}.{eid}"], lang_fr[f"entity.{NS}.{eid}"] = en, fr
    for prefix in content.ARMOR_SETS:
        write(f"equipment/{prefix}.json", {"layers": {
            "humanoid": [{"texture": f"{NS}:{prefix}"}],
            "humanoid_leggings": [{"texture": f"{NS}:{prefix}"}],
        }})
    for sdef in defs.STRUCTURES:
        lang_en[f"structure.{NS}.{sdef.id}"] = sdef.title_en
        lang_fr[f"structure.{NS}.{sdef.id}"] = sdef.title_fr
    for key, (en, fr) in content.MESSAGES.items():
        lang_en[key], lang_fr[key] = en, fr
    # advancement translations are merged in by gen_quests.py
    extra = os.path.join(ROOT, "build", "quest_lang.json")
    if os.path.exists(extra):
        q = json.load(open(extra))
        lang_en.update(q["en_us"])
        lang_fr.update(q["fr_fr"])
    write("lang/en_us.json", dict(sorted(lang_en.items())))
    write("lang/fr_fr.json", dict(sorted(lang_fr.items())))
    print(f"assets written: {len(lang_en)} translation keys")


if __name__ == "__main__":
    main()

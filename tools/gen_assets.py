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
HANDHELD = {"builder_wand", "master_builder_wand", "fire_staff", "frost_staff", "thunder_staff", "healing_staff",
            "levitation_wand", "steam_cane", "cartographer_blade", "telluric_hammer", "storm_staff", "ember_scythe", "void_spear", "frost_blade",
            "light_staff", "excavator_pickaxe", "lumber_axe"}
HANDHELD |= {row[2] for row in __import__("wf.bossgear", fromlist=["BOSS_GEAR"]).BOSS_GEAR}


def _de(name):
    """French "de" + a creature name, with the article contracted: du Grand Horloger, de la Dame, d'araignée."""
    low = name[0].lower() + name[1:]
    for art, de in (("le ", "du "), ("la ", "de la "), ("les ", "des "), ("l'", "de l'")):
        if low.startswith(art):
            return de + low[len(art):]
    return ("d'" if low[0] in "aeiouyàâéèêîïôûœh" else "de ") + low


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
    elif kind == "mist":
        write(f"models/block/{bid}.json", {"parent": "minecraft:block/cube_all", "render_type": "minecraft:translucent",
                                           "textures": {"all": t + bid}})
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
    if kind == "mist":
        variants = {f"sealed={v}": {"model": model} for v in ("false", "true")}
    elif kind in ("front", "grave"):
        variants = {f"facing={f}": {"model": model, **({"y": r} if r else {})}
                    for f, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}
    else:
        variants = {"": {"model": model}}
    write(f"blockstates/{bid}.json", {"variants": variants})


def metal_assets():
    """Models, blockstates, item definitions and equipment layers for metals.py (lang comes from metals.lang())."""
    from wf import metals
    for mid, m in metals.METALS.items():
        for bid in metals.block_ids(mid):
            block_models(bid, "cube")
            blockstate(bid, "cube")
            item_definition(bid, f"{NS}:block/{bid}")
        for iid in metals.item_ids(mid):
            write(f"models/item/{iid}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{iid}"}})
            item_definition(iid, f"{NS}:item/{iid}")
        for gid, (kind, _what, _l) in metals.gear_ids(mid).items():
            parent = "minecraft:item/handheld" if kind == "tool" else "minecraft:item/generated"
            write(f"models/item/{gid}.json", {"parent": parent, "textures": {"layer0": f"{NS}:item/{gid}"}})
            item_definition(gid, f"{NS}:item/{gid}")
        if m.get("armor"):
            write(f"equipment/{mid}.json", {"layers": {
                "humanoid": [{"texture": f"{NS}:{mid}"}],
                "humanoid_leggings": [{"texture": f"{NS}:{mid}"}]}})


def machine_assets():
    """Models (off/on) and facing x powered blockstates for machines.py."""
    from wf import machines
    rot = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}
    for mid in machines.MACHINES:
        for suffix in ("", "_on"):
            write(f"models/block/{mid}{suffix}.json", {"parent": "minecraft:block/orientable", "textures": {
                "top": f"{NS}:block/machine_top", "front": f"{NS}:block/{mid}_front{suffix}",
                "side": f"{NS}:block/machine_side"}})
        write(f"blockstates/{mid}.json", {"variants": {
            f"facing={f},powered={p}": {"model": f"{NS}:block/{mid}{'_on' if p == 'true' else ''}", **r}
            for f, r in rot.items() for p in ("false", "true")}})
        item_definition(mid, f"{NS}:block/{mid}")


def held_assets():
    """3D in-hand models (wf/held3d.py): the item definition switches between the sprite and the 3D model."""
    from wf import held3d
    for iid in held3d.HELD:
        write(f"models/item/{iid}_3d.json", held3d.model(iid))
        write(f"items/{iid}.json", held3d.item_definition(iid))


def furniture_assets():
    from wf import furniture
    for fid in furniture.FURNITURE:
        write(f"models/block/{fid}.json", furniture.model(fid))
        write(f"blockstates/{fid}.json", furniture.blockstate(fid))
        item_definition(fid, f"{NS}:block/{fid}")


def decor_assets(lang_en, lang_fr):
    from wf import decor
    VNAMES = {"stairs": ("Stairs", "Escalier en "), "slab": ("Slab", "Dalle en "), "wall": ("Wall", "Muret en ")}
    for bid, d in decor.DECOR.items():
        tn = decor.texture_names(bid)
        top = f"{NS}:block/{tn.get('top', tn.get('all'))}"
        side = f"{NS}:block/{tn.get('side', tn.get('all'))}"
        if "all" in tn:
            write(f"models/block/{bid}.json", {"parent": "minecraft:block/cube_all", "textures": {"all": top}})
        else:
            write(f"models/block/{bid}.json", {"parent": "minecraft:block/cube_column", "textures": {"end": top, "side": side}})
        write(f"blockstates/{bid}.json", {"variants": {"": {"model": f"{NS}:block/{bid}"}}})
        item_definition(bid, f"{NS}:block/{bid}")
        lang_en[f"block.{NS}.{bid}"], lang_fr[f"block.{NS}.{bid}"] = d["en"], d["fr"]
        tex3 = {"bottom": top, "top": top, "side": side}
        for v in d["variants"]:
            vid = decor.variant_id(bid, v)
            base_en = d["en"][:-1] if d["en"].endswith("s") else d["en"]
            lang_en[f"block.{NS}.{vid}"] = f"{base_en} {VNAMES[v][0]}"
            lang_fr[f"block.{NS}.{vid}"] = VNAMES[v][1] + d["fr"][0].lower() + d["fr"][1:]
            m = f"{NS}:block/{vid}"
            if v == "stairs":
                for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
                    write(f"models/block/{vid}{suffix}.json", {"parent": f"minecraft:block/{parent}", "textures": tex3})
                write(f"blockstates/{vid}.json", stairs_blockstate(m))
                item_definition(vid, m)
            elif v == "slab":
                write(f"models/block/{vid}.json", {"parent": "minecraft:block/slab", "textures": tex3})
                write(f"models/block/{vid}_top.json", {"parent": "minecraft:block/slab_top", "textures": tex3})
                write(f"blockstates/{vid}.json", {"variants": {
                    "type=bottom": {"model": m}, "type=top": {"model": m + "_top"},
                    "type=double": {"model": f"{NS}:block/{bid}"}}})
                item_definition(vid, m)
            elif v == "wall":
                for suffix, parent in (("_post", "template_wall_post"), ("_side", "template_wall_side"),
                                       ("_side_tall", "template_wall_side_tall"), ("_inventory", "wall_inventory")):
                    write(f"models/block/{vid}{suffix}.json", {"parent": f"minecraft:block/{parent}", "textures": {"wall": side}})
                write(f"blockstates/{vid}.json", wall_blockstate(m))
                item_definition(vid, m + "_inventory")


def stairs_blockstate(m):
    variants = {}
    rot = {"east": 0, "south": 90, "west": 180, "north": 270}
    for facing in ("east", "north", "south", "west"):
        for half in ("bottom", "top"):
            for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                model = m + ("" if shape == "straight" else "_inner" if "inner" in shape else "_outer")
                y = rot[facing]
                if shape in ("inner_left", "outer_left"):
                    y = (y + 270) % 360
                x = 0
                if half == "top":
                    x = 180
                    if shape in ("inner_left", "outer_left"):
                        y = (y + 90) % 360
                    elif shape in ("inner_right", "outer_right"):
                        y = (y + 90) % 360
                v = {"model": model}
                if x:
                    v["x"] = x
                if y:
                    v["y"] = y
                if x or y:
                    v["uvlock"] = True
                variants[f"facing={facing},half={half},shape={shape}"] = v
    return {"variants": variants}


def wall_blockstate(m):
    parts = [{"when": {"up": "true"}, "apply": {"model": m + "_post"}}]
    for d, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for h, suffix in (("low", "_side"), ("tall", "_side_tall")):
            apply = {"model": m + suffix, "uvlock": True}
            if y:
                apply["y"] = y
            parts.append({"when": {d: h}, "apply": apply})
    return {"multipart": parts}


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
        lang_fr[f"item.{NS}.{iid}"] = f"Œuf d'apparition {_de(fr)}"
    for bid, (en, fr, ten, tfr, kind) in content.BLOCKS.items():
        block_models(bid, kind)
        blockstate(bid, kind)
        item_definition(bid, f"{NS}:block/{bid}")
        lang_en[f"block.{NS}.{bid}"], lang_fr[f"block.{NS}.{bid}"] = en, fr
        if ten:
            lang_en[f"block.{NS}.{bid}.desc"], lang_fr[f"block.{NS}.{bid}.desc"] = ten, tfr
    decor_assets(lang_en, lang_fr)
    metal_assets()
    machine_assets()
    furniture_assets()
    held_assets()
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
    from wf import guide, skills, metals, machines, furniture, biomes
    for mod in (guide, skills, metals, machines, furniture, biomes):
        g_en, g_fr = mod.lang()
        lang_en.update(g_en)
        lang_fr.update(g_fr)
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

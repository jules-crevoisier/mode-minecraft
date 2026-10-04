#!/usr/bin/env python3
"""Build the illustrated French wiki of the mod: build/wiki/index.html + img/ + gif/.

Everything is read from the data tables and generated resources (lang files, guide pages, machines, metals,
talents, boss gear, biomes, structures, recipes, loot tables, quests, Java key bindings / commands / config),
so new content shows up by re-running the script. French explanations that the data does not carry live in
tools/wf/wiki_text.py.

Slow (3D renders): it is not part of generate_all.py. Renders are cached in build/wiki_cache, so a second run
only re-renders what changed.

Usage:
    python3 tools/gen_wiki.py                 # -> build/wiki/
    python3 tools/gen_wiki.py --jobs 4 --out /tmp/wiki --no-cache
    python3 tools/gen_wiki.py --worldmap DIR  # folder with wayfarers-worldmap{,-caves,-slice}.png and .txt
"""
import argparse
import glob
import hashlib
import html
import json
import multiprocessing
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.request

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
ROOT = os.path.dirname(TOOLS)
RES = os.path.join(ROOT, "src", "main", "resources")
ASSETS = os.path.join(RES, "assets", "wayfarers")
DATA = os.path.join(RES, "data", "wayfarers")
JAVA = os.path.join(ROOT, "src", "main", "java", "com", "wayfarers")
CACHE = os.path.join(ROOT, "build", "wiki_cache")
RENDER_VERSION = "3"
WORLDMAP_URL = ("https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/"
                "wayfarers-worldmap{}")
VANILLA_LANG_URL = "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/{}/assets/minecraft/lang/fr_fr.json"

from PIL import Image  # noqa: E402

from wf import wiki_text as TXT  # noqa: E402

E = html.escape


def log(*a):
    print(*a, flush=True)


def sha(*parts):
    h = hashlib.sha1()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode())
    return h.hexdigest()[:16]


def file_bytes(*paths):
    out = b""
    for p in paths:
        if os.path.exists(p):
            out += open(p, "rb").read()
    return out


def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# =============================================================================================== names
def load_json(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


FR = load_json(os.path.join(ASSETS, "lang", "fr_fr.json"), {})
EN = load_json(os.path.join(ASSETS, "lang", "en_us.json"), {})
VFR = {}


def load_vanilla_lang():
    path = os.path.join(CACHE, "mc_fr_fr.json")
    if not os.path.exists(path):
        for ver in ("26.2", "26.1", "1.21.11"):
            try:
                data = urllib.request.urlopen(VANILLA_LANG_URL.format(ver), timeout=30).read()
                json.loads(data)
                os.makedirs(CACHE, exist_ok=True)
                open(path, "wb").write(data)
                log(f"vanilla French names: {ver}")
                break
            except Exception as e:  # noqa: BLE001
                log(f"vanilla lang {ver}: {e}")
    VFR.update(load_json(path, {}))


def manifest():
    from wf import render3d
    return render3d._manifest_map()


_READABLE = {}


def readable(mid):
    if not _READABLE:
        from wf import render3d
        for d in render3d._ICON_DIRS:
            p = os.path.join(d, "manifest", "26.2.json") if d else ""
            if p and os.path.exists(p):
                for it in json.load(open(p))["items"]:
                    _READABLE[it["id"]] = it.get("readable", "")
                break
    return _READABLE.get(mid)


def pretty(s):
    return s.split(":")[-1].replace("_", " ").capitalize()


def name(rid):
    """French name of an item/block/entity id (with or without namespace)."""
    if ":" not in rid:
        rid = "wayfarers:" + rid
    ns, path = rid.split(":", 1)
    if ns == "wayfarers":
        for k in (f"item.wayfarers.{path}", f"block.wayfarers.{path}", f"entity.wayfarers.{path}"):
            if k in FR:
                return FR[k]
        return pretty(path)
    for k in (f"item.minecraft.{path}", f"block.minecraft.{path}", f"entity.minecraft.{path}"):
        if k in VFR:
            return VFR[k]
    return readable(rid) or pretty(path)


def desc(rid):
    path = rid.split(":")[-1]
    out = []
    for kind in ("item", "block"):
        for suf in ("desc", "desc2", "desc3", "desc4"):
            k = f"{kind}.wayfarers.{path}.{suf}"
            if k in FR:
                out.append(FR[k])
    return out


def vname(kind, path):
    return VFR.get(f"{kind}.minecraft.{path}") or pretty(path)


# =============================================================================================== icon atlas
CELL = 64
COLS = 32


class Atlas:
    def __init__(self):
        from wf import wikirender
        self.J = wikirender.JsonModels()
        self.cells = {}
        self.images = []
        self.extra = {}  # key -> PIL image provided from outside (mob portraits)

    def _placeholder(self):
        im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        return im

    def _make(self, key):
        if key in self.extra:
            return self.extra[key]
        ns, path = key.split(":", 1) if ":" in key else ("wayfarers", key)
        if ns == "wayfarers":
            gui, _hand = self.J.item_model(path)
            if gui is None:
                bs = os.path.join(ASSETS, "blockstates", path + ".json")
                if os.path.exists(bs):
                    gui = f"wayfarers:block/{path}"
            if gui is None:
                return None
            md = self.J.load(gui)
            if md["kind"] == "flat" and md.get("layer0"):
                tex = self.J.texture(md["layer0"])
                return tex.resize((CELL, CELL), Image.NEAREST)
            if md["kind"] == "elements":
                return self.J.render(md, size=CELL, ss=1)
            return None
        p = manifest().get(f"{ns}:{path}")
        if p and os.path.exists(p):
            return Image.open(p).convert("RGBA").resize((CELL, CELL), Image.NEAREST)
        return None

    def has(self, key):
        key = key if ":" in key else "wayfarers:" + key
        if key not in self.cells:
            try:
                im = self._make(key)
            except Exception as e:  # noqa: BLE001
                log(f"icon {key}: {e}")
                im = None
            self.cells[key] = None if im is None else len(self.images)
            if im is not None:
                self.images.append(im)
        return self.cells[key] is not None

    def icon(self, key, size=40, label=None, cls=""):
        key = key if ":" in key else "wayfarers:" + key
        title = E(label if label is not None else name(key), quote=True)
        if not self.has(key):
            short = E(name(key)[:3])
            return f'<i class="ic ic-none {cls}" style="--s:{size}px" title="{title}" role="img" aria-label="{title}">{short}</i>'
        i = self.cells[key]
        return (f'<i class="ic {cls}" style="--s:{size}px;--x:{i % COLS};--y:{i // COLS}" title="{title}" '
                f'role="img" aria-label="{title}"></i>')

    def save(self, path):
        rows = max(1, (len(self.images) + COLS - 1) // COLS)
        sheet = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
        for i, im in enumerate(self.images):
            sheet.alpha_composite(im.convert("RGBA").resize((CELL, CELL)), ((i % COLS) * CELL, (i // COLS) * CELL))
        sheet.save(path, optimize=True)
        return rows


# =============================================================================================== data
def lang_ids(kind):
    out = []
    for k in FR:
        parts = k.split(".")
        if len(parts) == 3 and parts[0] == kind and parts[1] == "wayfarers":
            out.append(parts[2])
    return out


def item_entries():
    """Every item/block of the mod with a French name, in registry-ish order."""
    seen, out = set(), []
    for kind in ("item", "block"):
        for i in lang_ids(kind):
            if i not in seen and not i.endswith("_spawn_egg"):
                seen.add(i)
                out.append(i)
    return out


def ingredient_ids(ing):
    """Recipe ingredient -> list of ids ('#tag' kept as is)."""
    if ing is None:
        return []
    if isinstance(ing, str):
        return [ing]
    if isinstance(ing, list):
        out = []
        for x in ing:
            out += ingredient_ids(x)
        return out
    if isinstance(ing, dict):
        if "item" in ing:
            return [ing["item"]]
        if "tag" in ing:
            return ["#" + ing["tag"]]
        if "items" in ing:
            return ingredient_ids(ing["items"])
    return []


def load_recipes():
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "recipe", "*.json"))):
        d = load_json(f)
        if not d:
            continue
        res = d.get("result", {})
        rid = res.get("id") if isinstance(res, dict) else res
        if not rid:
            continue
        out.append(dict(file=os.path.basename(f)[:-5], type=d.get("type", ""), data=d, result=rid,
                        count=res.get("count", 1) if isinstance(res, dict) else 1,
                        category=d.get("category", "misc")))
    return out


def loot_items(table, depth=0):
    """[(id, weight, is_mod)] of a loot table (resource id like wayfarers:chests/x), nested tables followed."""
    if depth > 4 or not table:
        return []
    ns, path = table.split(":", 1)
    d = load_json(os.path.join(RES, "data", ns, "loot_table", path + ".json"))
    if not d:
        return []
    out = []

    def walk(entries):
        for e in entries:
            t = e.get("type", "")
            if t.endswith("item") and "name" in e:
                out.append((e["name"], e.get("weight", 1)))
            elif t.endswith("loot_table"):
                out.extend(loot_items(e.get("value") or e.get("name"), depth + 1))
            if "children" in e:
                walk(e["children"])
    for pool in d.get("pools", []):
        walk(pool.get("entries", []))
    return out


def top_loot(tables, n=10):
    best = {}
    for t in tables:
        for iid, w in loot_items(t):
            best[iid] = min(best.get(iid, 1e9), w if isinstance(w, (int, float)) else 1)
    order = sorted(best.items(), key=lambda kv: (not kv[0].startswith("wayfarers:"), kv[1], kv[0]))
    return [k for k, _ in order[:n]]


def java_keys():
    out = []
    src = open(os.path.join(JAVA, "client", "WayfarersClient.java"), encoding="utf-8").read()
    for key, glfw in re.findall(r'new KeyMapping\("([\w.]+)",\s*InputConstants\.Type\.KEYSYM,\s*GLFW\.GLFW_KEY_(\w+)', src):
        out.append((glfw, FR.get(key, key)))
    for f in glob.glob(os.path.join(JAVA, "client", "*.java")):
        s = open(f, encoding="utf-8").read()
        for k in re.findall(r"isKeyDown\(.*?GLFW\.GLFW_KEY_(\w+)\)", s):
            if k not in [o[0] for o in out]:
                out.append((k, None))
    return [(k, TXT.KEY_TEXT.get(k) or v or k) for k, v in out]


def java_commands():
    """Top-level /wayfarers sub-commands: (name, [arguments], [sub-literals], op only)."""
    src = open(os.path.join(JAVA, "command", "WayfarersCommand.java"), encoding="utf-8").read()
    start = src.find('literal("wayfarers")')
    if start < 0:
        return []
    depth, base, tops = 0, None, []
    i = start
    while i < len(src):
        c = src[i]
        if src.startswith(".then(", i):
            if base is None:
                base = depth
            if depth == base:
                tops.append(i)
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if base is not None and depth < base:
                break
        elif c == ";" and base is not None and depth <= base:
            break
        i += 1
    out = []
    for k, pos in enumerate(tops):
        seg = src[pos:tops[k + 1] if k + 1 < len(tops) else i]
        lits = re.findall(r'literal\("(\w+)"\)', seg)
        if not lits:
            continue
        out.append((lits[0], re.findall(r'argument\("(\w+)"', seg), lits[1:], "requires(" in seg))
    return out


def java_config():
    out = []
    for fname, file_label in (("WayfarersConfig.java", "wayfarers-common.toml"),
                              ("WayfarersClientConfig.java", "wayfarers-client.toml")):
        src = open(os.path.join(JAVA, "config", fname), encoding="utf-8").read()
        jstr = r'"(?:[^"\\]|\\.)*"'
        for m in re.finditer(r'\.comment\(((?:' + jstr + r'\s*,?\s*)+)\)\s*\.define(\w*)\("([\w.]+)",\s*([^;]+?)\);', src):
            comment = " ".join(x[1:-1].replace('\\"', '"') for x in re.findall(jstr, m.group(1)))
            key = m.group(3)
            default = m.group(4).split(",")[0].strip()
            default = default.replace("HealthBars.", "")
            out.append((key, default, TXT.CONFIG_FR.get(key, comment), file_label))
    return out


def entity_stats(eid):
    camel = "".join(p.capitalize() for p in eid.split("_"))
    for f in glob.glob(os.path.join(JAVA, "entity", "**", camel + ".java"), recursive=True):
        s = open(f, encoding="utf-8").read()
        hp = re.search(r"MAX_HEALTH,\s*([\d.]+)", s)
        dmg = re.search(r"ATTACK_DAMAGE,\s*([\d.]+)", s)
        boss = "extends WayfarerBoss" in s or "extends BossZombie" in s
        doc = re.search(r"/\*\*(.*?)\*/\s*public class", s, re.S)
        text = ""
        if doc:
            text = re.sub(r"<[^>]+>|\{@\w+ ([^}]*)\}", r"\1", doc.group(1))
            text = re.sub(r"\s*\*\s?", " ", text).strip()
            text = text.split(". ")[0] + "."
        return dict(hp=float(hp.group(1)) if hp else None, dmg=float(dmg.group(1)) if dmg else None, boss=boss, doc=text)
    return dict(hp=None, dmg=None, boss=False, doc="")


def surface_blocks(surface_key):
    from wf import biomes as B
    fn = B.SURFACES.get(surface_key) or B.CAVE_SURFACES.get(surface_key)
    if not fn:
        return []
    names = []

    def walk(o):
        if isinstance(o, dict):
            if "Name" in o and isinstance(o["Name"], str):
                if o["Name"] not in names:
                    names.append(o["Name"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(fn())
    if not names and surface_key == "badlands":
        names = ["minecraft:red_sand", "minecraft:terracotta"]
    return names


# =============================================================================================== render jobs
UNDERGROUND_ROCK = {"stone", "deepslate", "tuff", "granite", "diorite", "andesite", "dirt", "gravel", "cobbled_deepslate",
                    "calcite", "smooth_basalt", "netherrack", "end_stone", "coarse_dirt", "clay", "sand", "sandstone"}


def _nbt_str(v):
    return str(getattr(v, "value", v))


def _structure_blocks(sdef, piece, xray):
    from gen_structures import build_piece
    bp = build_piece(sdef, piece, start=piece in sdef.pieces)
    bp.resolve_shapes()
    size, blocks, _, (mx, my, mz) = bp.normalized()
    view = blocks
    if xray:
        view = {p: b for p, b in blocks.items() if b[0].split(":")[1] not in UNDERGROUND_ROCK}
    return size, blocks, view, my


def structure_job(args):
    sid, out, use_cache, wonder = args
    from wf import defs, render3d, wikirender as W
    import wf.structures  # noqa: F401
    W.patch_render3d()
    sdef = next(s for s in defs.STRUCTURES if s.id == sid)
    xray = sdef.step == "underground_structures"
    info = dict(id=sid, bosses=[], spawners=[], loot=[], waystones=0, variants=len(sdef.pieces))
    pieces = list(sdef.pieces) + [p for ps in sdef.extra_pools.values() for p in ps]
    main = None
    for i, piece in enumerate(pieces):
        size, blocks, view, my = _structure_blocks(sdef, piece, xray)
        if i == 0:
            main = (size, blocks, view, my)
        for (name_, props, nbt) in blocks.values():
            if not nbt:
                continue
            if name_ == "wayfarers:boss_seal" and "boss" in nbt:
                b = _nbt_str(nbt["boss"])
                if b not in info["bosses"]:
                    info["bosses"].append(b)
            elif name_ == "minecraft:spawner":
                try:
                    e = _nbt_str(nbt["SpawnData"]["entity"]["id"])
                    if e not in info["spawners"]:
                        info["spawners"].append(e)
                except (KeyError, TypeError):
                    pass
            if "LootTable" in nbt:
                t = _nbt_str(nbt["LootTable"])
                if t not in info["loot"]:
                    info["loot"].append(t)
        if i == 0:
            info["waystones"] = sum(1 for b in blocks.values() if b[0] == "wayfarers:waystone")
    size, blocks, view, my = main
    info["size"] = list(size)
    info["blocks"] = len(blocks)
    key = sha(RENDER_VERSION, "s2", sid, wonder, xray, repr(sorted((p, b[0], tuple(sorted((b[1] or {}).items()))) for p, b in view.items())))
    cdir = os.path.join(CACHE, "structures", sid + "-" + key)
    files = {"static": f"img/s/{sid}.webp", "gif": f"gif/s/{sid}.gif"}
    if wonder:
        files.update(cut=f"img/s/{sid}_cut.webp", back=f"img/s/{sid}_back.webp")
    if not (use_cache and all(os.path.exists(os.path.join(cdir, os.path.basename(f))) for f in files.values())):
        os.makedirs(cdir, exist_ok=True)
        tmp = os.path.join(cdir, "tmp.png")
        render3d.render(view, tmp, max_side=1100 if wonder else 860)
        Image.open(tmp).save(os.path.join(cdir, f"{sid}.webp"), quality=82, method=5)
        if wonder:
            render3d.render(view, tmp, max_side=1100, angle=2)
            Image.open(tmp).save(os.path.join(cdir, f"{sid}_back.webp"), quality=82, method=5)
            cut = sdef.ground - my + 2
            if xray:
                ys = sorted(p[1] for p in view)
                cut = ys[int(len(ys) * 0.55)]
            render3d.render(view, tmp, max_side=1100, max_y=cut)
            Image.open(tmp).save(os.path.join(cdir, f"{sid}_cut.webp"), quality=82, method=5)
        os.remove(tmp)
        frames = W.voxel_frames(view, n=24 if wonder else 16, size=440 if wonder else 300)
        frames = W.crop_frames(frames)
        W.save_gif(frames, os.path.join(cdir, f"{sid}.gif"), ms=110 if wonder else 130)
    for f in files.values():
        dst = os.path.join(out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(cdir, os.path.basename(f)), dst)
    info["files"] = files
    return info


def mob_job(args):
    idx, out, use_cache = args
    from wf import mobs, wikirender as W, models, model_render
    builder = mobs.MODELS[idx]
    mod = sys.modules[builder.__module__]
    key = sha(RENDER_VERSION, file_bytes(mod.__file__, models.__file__, model_render.__file__, W.__file__))
    m = builder()
    name_ = m.name
    cdir = os.path.join(CACHE, "mobs", name_ + "-" + key)
    if not (use_cache and os.path.exists(os.path.join(cdir, name_ + ".gif"))):
        m.pack()
        tex, glow = m.textures()
        os.makedirs(cdir, exist_ok=True)
        frames = W.mob_frames(m, tex, glow, n=24, size=260)
        W.save_gif(frames, os.path.join(cdir, name_ + ".gif"), ms=90)
        W.mob_still(m, tex, glow, size=CELL).save(os.path.join(cdir, name_ + "_icon.png"))
    os.makedirs(os.path.join(out, "gif", "m"), exist_ok=True)
    shutil.copyfile(os.path.join(cdir, name_ + ".gif"), os.path.join(out, "gif", "m", name_ + ".gif"))
    return dict(id=name_, gif=f"gif/m/{name_}.gif", icon=os.path.join(cdir, name_ + "_icon.png"),
                cubes=len(m.all_cubes()))


def sheet_job(args):
    """Turntable sprite sheet (one GIF) of several JSON models, all spinning in sync."""
    kind, refs, out, use_cache, cell = args
    from wf import wikirender as W
    J = W.JsonModels()
    blobs = []
    for _iid, ref in refs:
        md = J.load(ref)
        blobs.append(repr(md))
        for t in md.get("textures", {}).values():
            if isinstance(t, str) and not t.startswith("#"):
                blobs.append(file_bytes(W._tex_path(t)))
    key = sha(RENDER_VERSION, "fixed-fit", cell, file_bytes(W.__file__), *blobs)
    cdir = os.path.join(CACHE, "sheets", f"{kind}-{key}")
    fname = f"{kind}.gif"
    cols = min(8, max(1, len(refs)))
    rows = (len(refs) + cols - 1) // cols
    if not (use_cache and os.path.exists(os.path.join(cdir, fname))):
        os.makedirs(cdir, exist_ok=True)
        n = 20
        frames = []
        import math
        import numpy as np
        models_ = [J.load(r) for _, r in refs]
        fits = []  # one scale per model for the whole turn (no breathing)
        for md in models_:
            if md["kind"] != "elements":
                fits.append((None, None))
                continue
            pts = np.concatenate([f[0] for f in J.faces(md)])
            centre = (pts.min(0) + pts.max(0)) / 2
            r = max(np.linalg.norm((pts - centre)[:, [0, 2]], axis=1).max() / 16, 0.05)
            h = np.ptp(pts[:, 1]) / 16
            span = max(2 * r, h * math.cos(math.radians(22)) + 2 * r * math.sin(math.radians(22)))
            fits.append((centre, cell * 0.9 / span))
        for k in range(n):
            sheet = Image.new("RGB", (cols * cell, rows * cell), W.BG)
            yaw = 30 + 360.0 * k / n
            for i, md in enumerate(models_):
                if md["kind"] != "elements":
                    continue
                im = J.render(md, size=cell, yaw=yaw, pitch=22, bg=W.BG, ss=2, centre=fits[i][0], ppb=fits[i][1])
                sheet.paste(im, ((i % cols) * cell, (i // cols) * cell))
            frames.append(sheet)
        W.save_gif(frames, os.path.join(cdir, fname), ms=100, colors=224)
    os.makedirs(os.path.join(out, "gif"), exist_ok=True)
    shutil.copyfile(os.path.join(cdir, fname), os.path.join(out, "gif", fname))
    return dict(kind=kind, file=f"gif/{fname}", cols=cols, rows=rows, cell=cell, ids=[i for i, _ in refs])


# =============================================================================================== world map
def find_worldmap(arg):
    cands = [arg] if arg else []
    cands += [os.environ.get("WAYFARERS_WORLDMAP", ""), os.path.join(ROOT, "build", "worldmap"),
              os.path.join(CACHE, "worldmap")]
    for d in cands:
        if d and os.path.exists(os.path.join(d, "wayfarers-worldmap.png")):
            return d
    d = os.path.join(CACHE, "worldmap")
    os.makedirs(d, exist_ok=True)
    try:
        for suf in (".png", "-caves.png", "-slice.png", ".txt"):
            data = urllib.request.urlopen(WORLDMAP_URL.format(suf), timeout=40).read()
            open(os.path.join(d, "wayfarers-worldmap" + suf), "wb").write(data)
        log("world map downloaded from the CI release")
        return d
    except Exception as e:  # noqa: BLE001
        log(f"world map not available: {e}")
        return None


def map_caption(head):
    m = re.search(r"area (\d+) x (\d+) blocks around ([-\d]+),([-\d]+) \(1 px = (\d+) blocks\)(?:; height ([-\d]+)\.\.([-\d]+))?", head)
    if not m:
        return head
    t = f"Zone de {m.group(1)} × {m.group(2)} blocs autour de {m.group(3)}, {m.group(4)} (1 pixel = {m.group(5)} blocs)"
    if m.group(6):
        t += f", relief de y {m.group(6)} à y {m.group(7)}"
    return t + "."


def parse_worldmap_txt(path):
    head, legend = "", []
    if not path or not os.path.exists(path):
        return head, legend
    for line in open(path, encoding="utf-8"):
        m = re.match(r"(#[0-9a-fA-F]{6})\s+([\w:]+)\s+([\d.]+)%", line.strip())
        if m:
            legend.append((m.group(1), m.group(2), float(m.group(3))))
        elif line.strip() and not head:
            head = line.strip()
    return head, legend


# =============================================================================================== HTML helpers
SVG = {
    "heart": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 14 2 8.2A3.6 3.6 0 0 1 8 3.6a3.6 3.6 0 0 1 6 4.6Z"/></svg>',
    "sword": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13.5 1.5 15 1l-.5 1.5L7 10l-1-1zM5 8.5l2.5 2.5-1 1-.8-.8-2.2 2.2-1.4-1.4 2.2-2.2-.8-.8z"/></svg>',
    "pin": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1a5 5 0 0 1 5 5c0 3.5-5 9-5 9S3 9.5 3 6a5 5 0 0 1 5-5Zm0 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z"/></svg>',
    "cog": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10.3 1h3.4l.5 3a8 8 0 0 1 2 .9l2.5-1.8 2.4 2.4-1.8 2.5c.4.6.7 1.3.9 2l3 .5v3.4l-3 .5a8 8 0 0 1-.9 2l1.8 2.5-2.4 2.4-2.5-1.8a8 8 0 0 1-2 .9l-.5 3h-3.4l-.5-3a8 8 0 0 1-2-.9l-2.5 1.8-2.4-2.4 1.8-2.5a8 8 0 0 1-.9-2l-3-.5v-3.4l3-.5c.2-.7.5-1.4.9-2L3.1 5.5l2.4-2.4L8 4.9c.6-.4 1.3-.7 2-.9ZM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/></svg>',
    "stone": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2h6l1 3v9H4V5zM6 6v6h4V6z"/></svg>',
    "search": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M7 1.5a5.5 5.5 0 0 1 4.4 8.8l3.4 3.4-1.1 1.1-3.4-3.4A5.5 5.5 0 1 1 7 1.5Zm0 1.6a3.9 3.9 0 1 0 0 7.8 3.9 3.9 0 0 0 0-7.8Z"/></svg>',
    "moon": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10.5 1.5A6.5 6.5 0 1 0 14.5 11 5.5 5.5 0 0 1 10.5 1.5Z"/></svg>',
}


class Index:
    def __init__(self):
        self.rows = []

    def add(self, title, kind, anchor, extra=""):
        self.rows.append([title, kind, anchor, extra])


def chips(atlas, ids, size=28, link=None):
    out = []
    for i in ids:
        nm = name(i)
        a = link(i) if link else None
        inner = f'{atlas.icon(i, size)}<span>{E(nm)}</span>'
        out.append(f'<a class="chip" href="#{a}">{inner}</a>' if a else f'<span class="chip">{inner}</span>')
    return '<span class="chips">' + "".join(out) + "</span>"


def plaque(sid, kicker, title, intro=""):
    return (f'<header class="plaque" id="{sid}"><span class="kicker">{E(kicker)}</span><h2>{E(title)}</h2>'
            + (f'<p class="lede">{intro}</p>' if intro else "") + "</header>")


def climate(b):
    t = b["temp"]
    word = "glacial" if t < 0.15 else "froid" if t < 0.45 else "tempéré" if t < 0.95 else "chaud" if t < 1.5 else "torride"
    wet = ("neige" if t < 0.15 else "pluie") if b["rain"] else "sec"
    return f"{word}, {wet}"


def fmt_num(v):
    if v is None:
        return "?"
    return str(int(v)) if float(v).is_integer() else f"{v:g}".replace(".", ",")


def anchor_item(i):
    return "i-" + i.split(":")[-1]


# =============================================================================================== main build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "wiki"))
    ap.add_argument("--jobs", type=int, default=max(1, min(6, os.cpu_count() or 2)))
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--worldmap", default=None)
    args = ap.parse_args()
    t0 = time.time()
    out = os.path.abspath(args.out)
    use_cache = not args.no_cache
    os.makedirs(CACHE, exist_ok=True)
    if os.path.exists(out):
        if os.listdir(out) and not os.path.exists(os.path.join(out, "index.html")):
            sys.exit(f"{out} is not empty and is not a previous wiki build: choose another --out")
        shutil.rmtree(out)
    for d in ("img", "img/s", "gif", "gif/s", "gif/m"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    load_vanilla_lang()

    from wf import (content, guide, machines, metals, skills, bossgear, biomes as B, decor, furniture, defs, mobs,
                    worldfeatures as WF, wikirender as W)
    import wf.structures  # noqa: F401

    # ------------------------------------------------------------------ renders (parallel)
    wonder_ids = set(TXT.WONDERS)
    wonder_text = ""
    for pid, _cat, _icon, _title, paras, _items in guide.PAGES:
        if pid == "wonders":
            wonder_text = " ".join(e for e, _f in paras)
    for s in defs.STRUCTURES:
        if s.title_en and s.title_en in wonder_text:
            wonder_ids.add(s.id)
    J = W.JsonModels()
    held, furn = [], []
    for iid in item_entries():
        gui, hand = J.item_model(iid)
        if hand:
            held.append((iid, hand))
        elif gui and gui.startswith("wayfarers:block/"):
            # explicit elements in the mod's own model (furniture, fittings, special blocks)
            p = os.path.join(ASSETS, "models", "block", gui.split("/", 1)[1] + ".json")
            d = load_json(p, {})
            if "elements" in d:
                furn.append((iid, gui))
    log(f"{len(defs.STRUCTURES)} structures, {len(mobs.MODELS)} creatures, {len(held)} 3D held items, "
        f"{len(furn)} 3D blocks")
    s_jobs = [(s.id, out, use_cache, s.id in wonder_ids) for s in defs.STRUCTURES]
    m_jobs = [(i, out, use_cache) for i in range(len(mobs.MODELS))]
    sh_jobs = [("held", held, out, use_cache, 132), ("furniture", furn, out, use_cache, 120)]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(args.jobs) as pool:
        r_mobs = pool.map_async(mob_job, m_jobs)
        r_sheets = pool.map_async(sheet_job, sh_jobs)
        r_structs = pool.map_async(structure_job, s_jobs, chunksize=1)
        mob_info = {m["id"]: m for m in r_mobs.get()}
        log(f"creatures rendered ({time.time() - t0:.0f}s)")
        sheet_info = {s["kind"]: s for s in r_sheets.get()}
        log(f"3D sheets rendered ({time.time() - t0:.0f}s)")
        struct_info = {s["id"]: s for s in r_structs.get()}
        log(f"structures rendered ({time.time() - t0:.0f}s)")

    # ------------------------------------------------------------------ data
    atlas = Atlas()
    for mid, m in mob_info.items():
        atlas.extra["wayfarers:" + mid] = Image.open(m["icon"]).convert("RGBA")
    idx = Index()
    recipes = load_recipes()
    by_result = {}
    for r in recipes:
        by_result.setdefault(r["result"], []).append(r)
    entries = item_entries()
    all_ids = set(entries)

    def item_link(i):
        p = i.split(":")[-1]
        return anchor_item(p) if i.startswith("wayfarers:") and p in all_ids else None

    # boss gear
    gear = {row[0]: row for row in bossgear.BOSS_GEAR}
    weapon_of = {row[0]: row[2] for row in bossgear.BOSS_GEAR}
    remembrance_of = {row[0]: bossgear.remembrance_id(row[0]) for row in bossgear.BOSS_GEAR}

    # where each creature lives (structures scan + structure spawn lists)
    lives = {}
    for s in defs.STRUCTURES:
        si = struct_info.get(s.id, {})
        for e in si.get("bosses", []) + si.get("spawners", []) + [sp[0] for sp in s.spawns]:
            lives.setdefault(e, [])
            if s.id not in lives[e]:
                lives[e].append(s.id)

    sec = []  # html sections

    # ================================================================== ACCUEIL
    n_items = sum(1 for i in entries if f"item.wayfarers.{i}" in FR)
    n_blocks = sum(1 for i in entries if f"block.wayfarers.{i}" in FR)
    stats = [(len(defs.STRUCTURES), "structures"), (len(mob_info), "créatures et boss"), (len(B.BIOMES), "biomes"),
             (n_items, "objets"), (n_blocks, "blocs"), (len(recipes), "recettes"), (len(skills.SKILLS), "talents"),
             (sum(len(json.load(open(os.path.join(DATA, "quests.json")))[c]) for c in json.load(open(os.path.join(DATA, "quests.json")))), "quêtes")]
    steps = []
    for n, (title, text, ids) in enumerate(TXT.FIRST_HOUR, 1):
        steps.append(f'<li class="step"><span class="num">{n}</span><div><h4>{E(title)}</h4><p>{E(text)}</p>'
                     f'{chips(atlas, ["wayfarers:" + i for i in ids], 28, item_link)}</div></li>')
    keys = "".join(f'<tr><td><kbd>{E(k)}</kbd></td><td>{E(v)}</td></tr>'
                   for k, v in java_keys())
    keys += f'<tr><td><kbd>Clic molette</kbd></td><td>{E(TXT.KEY_TEXT["Clic molette"])}</td></tr>'
    cmds = []
    for sub, a, subs, op in java_commands():
        who, text = TXT.COMMANDS.get(sub, ("op" if op else "tous", ""))
        usage = "/wayfarers " + sub + "".join(f" &lt;{E(x)}&gt;" for x in a) + (f" {'|'.join(subs)}" if subs else "")
        cmds.append(f'<tr><td><code>{usage}</code></td><td><span class="who {"op" if op else ""}">{"op" if op else "tous"}'
                    f'</span></td><td>{E(text)}</td></tr>')
        idx.add("/wayfarers " + sub, "Commande", "commandes", text)
    cfg = "".join(f'<tr><td><code>{E(k)}</code></td><td><code>{E(d)}</code></td><td>{E(c)}<br><small>{E(f)}</small></td></tr>'
                  for k, d, c, f in java_config())
    tiles = [("quetes", "Quêtes", "wayfarers:wayfarer_atlas"), ("manuel", "Le Manuel", "wayfarers:wayfarer_manual"),
             ("talents", "Talents & magie", "wayfarers:fire_staff"), ("machines", "Machines", "wayfarers:auto_harvester"),
             ("metaux", "Métaux & armures", "wayfarers:brass_ingot"), ("deco", "Déco steampunk", "wayfarers:gear_panel"),
             ("armes3d", "Armes en 3D", "wayfarers:bell_hammer"), ("bestiaire", "Bestiaire", "minecraft:skeleton_skull"),
             ("structures", "Structures", "wayfarers:structure_compass"), ("monde", "Nouveau Monde", "minecraft:grass_block"),
             ("objets", "Tous les objets", "wayfarers:travel_backpack"), ("recettes", "Recettes", "minecraft:crafting_table")]
    tile_html = "".join(f'<a class="tile" href="#{a}">{atlas.icon(ic, 40)}<span>{E(t)}</span></a>' for a, t, ic in tiles)
    sec.append(f'''
<section class="hero" id="accueil">
  <div class="hero-text">
    <span class="kicker">Minecraft 26.2 · Forge 65.1 · mod coopératif</span>
    <h1>Wayfarers</h1>
    <p class="lede">{E(TXT.TAGLINE)}</p>
    <ul class="stats">{"".join(f"<li><b>{n}</b><span>{E(l)}</span></li>" for n, l in stats)}</ul>
  </div>
  <figure class="vitrine hero-fig"><img src="{struct_info[sorted(wonder_ids & set(struct_info))[0]]["files"]["gif"] if wonder_ids & set(struct_info) else ""}" alt="Une merveille du mod en rotation" loading="eager"></figure>
</section>
<nav class="tiles" aria-label="Sections">{tile_html}</nav>
<section class="block" id="commencer">
  {plaque("commencer-h", "La première heure", "Par où commencer", "Huit étapes, dans l'ordre, pour bien démarrer une partie à plusieurs.")}
  <ol class="steps">{"".join(steps)}</ol>
</section>
<section class="block two" id="touches">
  <div>{plaque("touches-h", "Clavier", "Les touches")}
  <table class="tbl keys"><tbody>{keys}</tbody></table>
  <p class="note">Toutes les touches se changent dans Options → Commandes → Wayfarers.</p></div>
  <div id="commandes">{plaque("commandes-h", "Chat", "Les commandes")}
  <div class="scroll"><table class="tbl"><thead><tr><th>Commande</th><th>Qui</th><th>Effet</th></tr></thead><tbody>{"".join(cmds)}</tbody></table></div></div>
</section>
<section class="block" id="config">
  {plaque("config-h", "Réglages", "Options de configuration", "Dans le dossier <code>config/</code> de l'instance. Les options communes se règlent côté serveur, les options client chez chaque joueur.")}
  <div class="scroll"><table class="tbl"><thead><tr><th>Option</th><th>Défaut</th><th>Effet</th></tr></thead><tbody>{cfg}</tbody></table></div>
</section>''')

    # ================================================================== QUESTS
    quests = load_json(os.path.join(DATA, "quests.json"), {})
    qhtml = []
    for ci, (chap, qids) in enumerate(quests.items()):
        rows = []
        for q in qids:
            adv = load_json(os.path.join(DATA, "advancement", q + ".json"), {})
            disp = adv.get("display", {})
            tkey = disp.get("title", {}).get("translate", "")
            dkey = disp.get("description", {}).get("translate", "")
            title = FR.get(tkey, q)
            dtext = FR.get(dkey, "")
            icon = disp.get("icon", {}).get("id", "minecraft:book")
            frame = disp.get("frame", "task")
            xp = adv.get("rewards", {}).get("experience")
            rows.append(f'<li class="quest {E(frame)}" id="q-{slug(q)}">{atlas.icon(icon, 36)}<div><b>{E(title)}</b>'
                        f'<span>{E(dtext)}</span>{f"<small>+{xp} XP</small>" if xp else ""}</div></li>')
            idx.add(title, "Quête", f"q-{slug(q)}", dtext)
        cname = FR.get(f"chapter.wayfarers.{chap}", chap)
        qhtml.append(f'<details class="chapter" {"open" if ci == 0 else ""}><summary><span>{E(cname)}</span>'
                     f'<small>{len(qids)} étapes</small></summary><ul class="quests">{"".join(rows)}</ul></details>')
    sec.append(f'''<section class="block" id="quetes">
  {plaque("quetes-h", "Système", "Quêtes et journal", "Touche <kbd>J</kbd> ou clic droit avec l'Atlas. Chaque étape réussie par un joueur est accordée à tout le groupe, même aux absents. Les quêtes donnent de l'expérience, du butin et des points de talent.")}
  {"".join(qhtml)}
</section>''')

    # ================================================================== MANUAL (all guide pages)
    cats = {c: (icon, t) for c, icon, t in guide.CATEGORIES}
    by_cat = {}
    for pid, cat, icon, (ten, tfr), paras, items in guide.PAGES:
        by_cat.setdefault(cat, []).append((pid, icon, tfr, paras, items))
    mhtml = []
    for cat, pages in by_cat.items():
        icon, (cen, cfr) = cats.get(cat, ("minecraft:book", (cat, cat)))
        cards = []
        for pid, picon, tfr, paras, items in pages:
            body = "".join(f"<p>{E(pf)}</p>" for _pe, pf in paras)
            rel = chips(atlas, items, 26, item_link) if items else ""
            cards.append(f'<article class="card page" id="m-{pid}"><h4>{atlas.icon(picon, 32)}{E(tfr)}</h4>{body}{rel}</article>')
            idx.add(tfr, "Manuel", f"m-{pid}", " ".join(pf for _pe, pf in paras))
        mhtml.append(f'<h3 class="subhead">{atlas.icon(icon, 28)}{E(cfr)}</h3><div class="grid pages">{"".join(cards)}</div>')
    qol = "".join(f'<article class="card mini"><h4>{E(t)}</h4><p>{E(x)}</p></article>' for t, x in TXT.QOL)
    for t, x in TXT.QOL:
        idx.add(t, "Confort", "confort", x)
    sec.append(f'''<section class="block" id="manuel">
  {plaque("manuel-h", "Le Manuel du Voyageur", "Chaque système, page par page", "Le texte du Manuel en jeu, avec les objets concernés. Clique sur un objet pour voir sa fiche et sa recette.")}
  {"".join(mhtml)}
  <h3 class="subhead" id="confort">Le confort de jeu, sans objet à fabriquer</h3>
  <div class="grid minis">{qol}</div>
</section>''')

    # ================================================================== TALENTS
    branches = []
    for bid, bicon, color, (ben, bfr) in skills.BRANCHES:
        col = f"#{color & 0xFFFFFF:06x}"
        sk = [s for s in skills.SKILLS if s[1] == bid]
        maxr = max(s[2][1] for s in sk) + 1
        pos = {s[0]: s[2] for s in sk}
        lines = []
        for s in sk:
            for req in s[4]:
                if req in pos:
                    (c1, r1), (c2, r2) = pos[req], s[2]
                    lines.append(f'<line x1="{c1 * 100 + 50}" y1="{r1 * 100 + 50}" x2="{c2 * 100 + 50}" y2="{r2 * 100 + 50}"/>')
        nodes, legend = [], []
        for sid_, _b, (c, r), cost, req, icon, (nen, nfr), (den, dfr), eff in sk:
            active = eff[0] == "active"
            nodes.append(f'<div class="node{" active" if active else ""}" style="left:{(c * 100 + 50) / 3:.3f}%;top:{(r * 100 + 50) / maxr:.3f}%" '
                         f'title="{E(dfr, quote=True)}" id="t-{sid_}">{atlas.icon(icon, 30)}<b>{E(nfr)}</b><small>{"●" * cost}</small></div>')
            legend.append(f'<li><b>{E(nfr)}</b> <small>({cost} pt{"s" if cost > 1 else ""})</small> — {E(dfr)}</li>')
            idx.add(nfr, "Talent", f"t-{sid_}", dfr)
        branches.append(f'''<article class="branch" style="--branch:{col}">
  <h4>{atlas.icon(bicon, 30)}{E(bfr)}</h4>
  <div class="tree" style="aspect-ratio:3/{maxr * 1.12:.2f}"><svg viewBox="0 0 300 {maxr * 100}" preserveAspectRatio="none" aria-hidden="true">{"".join(lines)}</svg>{"".join(nodes)}</div>
  <ul class="legend">{"".join(legend)}</ul>
</article>''')
    spells = []
    for pid, cat, icon, t, paras, items in guide.PAGES:
        if pid == "magic":
            for i in items:
                ii = i.split(":")[1]
                spells.append(f'<li>{atlas.icon(i, 36)}<div><b>{E(name(i))}</b><span>{E(" ".join(desc(ii)))}</span></div></li>')
    sec.append(f'''<section class="block" id="talents">
  {plaque("talents-h", "Système", "Talents, mana et sorts", "Touche <kbd>K</kbd>. Un point par quête, trois par boss, un tous les 10 niveaux d'expérience. Chaque talent demande un des talents reliés au-dessus. Le talent du bas de chaque branche est un pouvoir actif : clique dessus pour l'équiper, puis <kbd>V</kbd> pour le lancer. La Fiole d'oubli rend tous les points.")}
  <div class="branches">{"".join(branches)}</div>
  <h3 class="subhead">Les sorts (clic droit, coûtent du mana)</h3>
  <p>Le mana s'affiche dans la barre bleue au-dessus de l'expérience et se recharge tout seul. Chaque bâton contient un seul sort.</p>
  <ul class="rows">{"".join(spells)}</ul>
</section>''')

    # ================================================================== MACHINES
    mcards = []
    for mid, m in machines.MACHINES.items():
        lines = "".join(f"<li>{E(f)}</li>" for _e, f in m["desc"])
        rec = by_result.get("wayfarers:" + mid, [])
        mcards.append(f'''<article class="card machine" id="{anchor_item(mid)}x">
  <div class="mhead">{atlas.icon(mid, 64)}<h4>{E(name(mid))}</h4></div>
  <ul class="ticks">{lines}</ul>
  {render_recipe(atlas, rec[0], item_link) if rec else ""}
</article>''')
        idx.add(name(mid), "Machine", anchor_item(mid) + "x", " ".join(f for _e, f in m["desc"]))
    farm = ""
    for pid, icon, (ten, tfr), paras, items in machines.GUIDE:
        farm += f'<article class="card page"><h4>{atlas.icon(icon, 32)}{E(tfr)}</h4>{"".join(f"<p>{E(f)}</p>" for _e, f in paras)}</article>'
    sec.append(f'''<section class="block" id="machines">
  {plaque("machines-h", "Système", "Machines simples", "Ni câble, ni énergie : chaque machine est un bloc qui fait une seule chose. Elles se fabriquent presque toutes avec du laiton.")}
  <div class="grid machines">{"".join(mcards)}</div>
  <div class="grid pages">{farm}</div>
</section>''')

    # ================================================================== METALS & ARMOUR
    mt = []
    for mid, m in metals.METALS.items():
        ids = list(metals.item_ids(mid)) + list(metals.block_ids(mid))
        gear_ids = list(metals.gear_ids(mid))
        ore = m.get("ore")
        where = ""
        if ore:
            hosts = {"stone": "pierre", "deepslate": "ardoise des abîmes", "netherrack": "netherrack (Nether)"}
            tool = {"stone": "pioche en pierre", "iron": "pioche en fer", "diamond": "pioche en diamant"}.get(ore.get("tool"), "")
            where = (f'<p class="where">{SVG["pin"]} Minerai dans la {", ".join(hosts.get(h, h) for h in ore["hosts"])}, '
                     f'entre y {ore["y"][0]} et y {ore["y"][1]}' + (f" ; il faut une {tool}" if tool else "") + ".</p>")
        elif mid == "brass":
            where = f'<p class="where">{SVG["cog"]} Alliage : 3 lingots de cuivre + 1 lingot de zinc = 4 lingots de laiton.</p>'
        elif m.get("cloth"):
            where = f'<p class="where">{SVG["cog"]} Tissé : laine violette, ficelle et cristal d\'éther.</p>'
        bonus = ""
        if m.get("armor"):
            bonus = f'<p class="bonus"><b>Bonus d\'ensemble :</b> {E(m["armor"]["bonus"][1].replace("Ensemble : ", ""))}</p>'
        stats_ = ""
        if m.get("tools"):
            t = m["tools"]
            stats_ += f'<p class="small">Outils : durabilité {t["durability"]}, vitesse {fmt_num(t["speed"])}, enchantabilité {t["enchant"]}.</p>'
        if m.get("armor"):
            a = m["armor"]
            stats_ += f'<p class="small">Armure : défense {"/".join(str(x) for x in a["defense"])} (casque/plastron/jambières/bottes), robustesse {fmt_num(a["toughness"])}.</p>'
        title = (m.get("gem_name") or (m["en"], m["fr"]))[1] if m.get("gem_name") else m["fr"].replace("d'", "").capitalize()
        mt.append(f'''<article class="card metal" id="metal-{mid}">
  <h4>{atlas.icon(ids[0] if ids else gear_ids[0], 36)}{E(title)}</h4>{where}
  {chips(atlas, ["wayfarers:" + i for i in ids], 26, item_link)}
  {chips(atlas, ["wayfarers:" + i for i in gear_ids], 26, item_link) if gear_ids else ""}
  {bonus}{stats_}
</article>''')
        idx.add(title, "Métal", f"metal-{mid}", m["en"])
    sets = []
    for sid_, (en, fr, ten, tfr) in content.ARMOR_SETS.items():
        pieces = [f"wayfarers:{sid_}_{p}" for p in content.PIECES]
        mat = {"explorer": "fragments de carte", "ember": "braises anciennes", "void": "éclats du vide"}.get(sid_, "")
        sets.append(f'''<article class="card metal" id="set-{sid_}"><h4>{atlas.icon(pieces[1], 36)}Armure {E(fr)}</h4>
  {chips(atlas, pieces, 26, item_link)}<p class="bonus"><b>Bonus d'ensemble :</b> {E(tfr.replace("Ensemble : ", ""))}</p>
  {f'<p class="small">Fabriquée avec des {mat}.</p>' if mat else ""}</article>''')
        idx.add(f"Armure {fr}", "Armure", f"set-{sid_}", tfr)
    tiers = "".join(f'<li>{atlas.icon("wayfarers:" + mat, 32)}<b>{E(name(mat))}</b><span>{E(lbl)}</span></li>'
                    for (tier, mat), lbl in zip(bossgear.TIER_MATERIAL.items(),
                                                ["Palier 1 · ruines de la Surface", "Palier 2 · sous terre (minerai sous y 8)",
                                                 "Palier 3 · Nether", "Palier 4 · End"]))
    sec.append(f'''<section class="block" id="metaux">
  {plaque("metaux-h", "Équipement", "Métaux, minerais et armures", "Porte les quatre pièces d'un ensemble pour activer son bonus. Chaque palier d'équipement demande le matériau de sa dimension : on explore dans l'ordre.")}
  <ul class="tiers">{tiers}</ul>
  <div class="grid metals">{"".join(mt)}{"".join(sets)}</div>
</section>''')

    # ================================================================== DECOR + FURNITURE
    dgroups = {"Guilde et régions": [], "Steampunk": []}
    steam = False
    for bid, d in decor.DECOR.items():
        if bid == "brass_plating":
            steam = True
        variants = [decor.variant_id(bid, v) for v in d["variants"]]
        g = "Steampunk" if steam else "Guilde et régions"
        light = f'<small class="glow">lumière {d["light"]}</small>' if d.get("light") else ""
        dgroups[g].append(f'''<article class="deco" id="{anchor_item(bid)}d">{atlas.icon(bid, 64)}<div><b>{E(name(bid))}</b>{light}
  <span class="vars">{"".join(atlas.icon(v, 30) for v in variants)}</span></div></article>''')
        idx.add(name(bid), "Bloc déco", anchor_item(bid) + "d", " ".join(name(v) for v in variants))
    fsheet = sheet_info.get("furniture")
    fcards = []
    if fsheet:
        for i, iid in enumerate(fsheet["ids"]):
            c, r = i % fsheet["cols"], i // fsheet["cols"]
            fd = furniture.FURNITURE.get(iid)
            extra = ""
            if fd:
                mount = {"wall": "se pose contre un mur", "player": "se tourne vers toi", "axis": "se pose dans les 3 axes",
                         "away": "se pose au bord", "none": ""}.get(fd["mount"], "")
                extra = (mount + (f" · lumière {fd['light']}" if fd.get("light") else "")).strip(" ·")
            fcards.append(f'''<figure class="spin" id="{anchor_item(iid)}f"><div class="vitrine sprite" style="--w:{fsheet["cell"]}px;--sheet:url({fsheet["file"]});--cx:{c};--cy:{r};--cols:{fsheet["cols"]};--rows:{fsheet["rows"]}"></div>
  <figcaption><b>{E(name(iid))}</b>{f"<small>{E(extra)}</small>" if extra else ""}</figcaption></figure>''')
            idx.add(name(iid), "Bloc 3D", anchor_item(iid) + "f", extra)
    sec.append(f'''<section class="block" id="deco">
  {plaque("deco-h", "Construction", "Blocs de déco et meubles", "Les blocs qui bâtissent les structures du mod, utilisables pour ta base. La plupart existent en escaliers, dalles et murets (petites icônes). Astuce steampunk : le laiton pour les finitions, le fer sombre et l'acajou pour la masse, des lampes Edison pour la lumière.")}
  {"".join(f'<h3 class="subhead">{E(g)}</h3><div class="grid decos">{"".join(v)}</div>' for g, v in dgroups.items() if v)}
  <h3 class="subhead">Meubles et blocs en 3D</h3>
  <div class="grid spins">{"".join(fcards)}</div>
</section>''')

    # ================================================================== HELD 3D
    hsheet = sheet_info.get("held")
    hcards = []
    if hsheet:
        for i, iid in enumerate(hsheet["ids"]):
            c, r = i % hsheet["cols"], i // hsheet["cols"]
            d_ = desc(iid)
            hcards.append(f'''<figure class="spin" id="{anchor_item(iid)}h"><div class="vitrine sprite" style="--w:{hsheet["cell"]}px;--sheet:url({hsheet["file"]});--cx:{c};--cy:{r};--cols:{hsheet["cols"]};--rows:{hsheet["rows"]}"></div>
  <figcaption><a href="#{anchor_item(iid)}">{atlas.icon(iid, 24)}<b>{E(name(iid))}</b></a>{f"<small>{E(d_[0])}</small>" if d_ else ""}</figcaption></figure>''')
            idx.add(name(iid), "Arme 3D", anchor_item(iid) + "h", " ".join(d_))
    bg_rows = []
    for row in bossgear.BOSS_GEAR:
        boss, tier, wid = row[0], row[1], row[2]
        bg_rows.append(f'<tr><td>{atlas.icon("wayfarers:" + boss, 32)} {E(name(boss))}</td><td>{atlas.icon(remembrance_of[boss], 32)}</td>'
                       f'<td><a href="#{anchor_item(wid)}">{atlas.icon(wid, 32)} {E(name(wid))}</a></td><td>{E(row[4][1])}</td></tr>')
    sec.append(f'''<section class="block" id="armes3d">
  {plaque("armes-h", "Équipement", "Armes, bâtons et outils en 3D", "Ces objets s'affichent en 3D quand on les tient en main (icône plate dans l'inventaire). Chaque arme spéciale a un pouvoir au clic droit, avec un temps de recharge.")}
  <div class="grid spins">{"".join(hcards)}</div>
  <h3 class="subhead">Souvenirs de boss et armes forgées</h3>
  <p>Chaque grand boss lâche son Souvenir. Avec quatre matériaux de son palier et deux diamants, il devient une arme unique.</p>
  <div class="scroll"><table class="tbl gear"><thead><tr><th>Boss</th><th>Souvenir</th><th>Arme</th><th>Pouvoir</th></tr></thead><tbody>{"".join(bg_rows)}</tbody></table></div>
</section>''')

    # ================================================================== BESTIARY
    groups = {"boss": [], "champion": [], "creature": []}
    for mid in list(content.ENTITIES) + [m for m in mob_info if m not in content.ENTITIES]:
        if mid not in mob_info:
            continue
        st = entity_stats(mid)
        kind = "boss" if mid in gear else ("champion" if st["boss"] else "creature")
        where = lives.get("wayfarers:" + mid, [])
        where_html = ", ".join(f'<a href="#s-{w}">{E(FR.get("structure.wayfarers." + w, w))}</a>' for w in where) or "—"
        loot = top_loot([f"wayfarers:entities/{mid}"], 8)
        text = TXT.MOBS.get(mid) or st["doc"]
        badge = {"boss": "Boss", "champion": "Champion de donjon", "creature": "Créature"}[kind]
        weapon = ""
        if mid in weapon_of:
            weapon = f'<p class="small">Son Souvenir forge : <a href="#{anchor_item(weapon_of[mid])}">{E(name(weapon_of[mid]))}</a>.</p>'
        groups[kind].append(f'''<article class="card mob {kind}" id="b-{mid}">
  <figure class="vitrine"><img src="{mob_info[mid]["gif"]}" alt="{E(name(mid), quote=True)} en rotation" width="260" height="260" loading="lazy"></figure>
  <div class="mob-body"><span class="badge {kind}">{badge}</span><h4>{E(name(mid))}</h4>
  <p class="statline"><span title="Points de vie">{SVG["heart"]}{fmt_num(st["hp"])} PV</span><span title="Dégâts au corps à corps">{SVG["sword"]}{fmt_num(st["dmg"])}</span></p>
  <p>{E(text)}</p>
  <p class="where">{SVG["pin"]} {where_html}</p>
  {('<div class="drops"><small>Butin</small>' + chips(atlas, loot, 24, item_link) + '</div>') if loot else ""}
  {weapon}</div>
</article>''')
        idx.add(name(mid), badge, f"b-{mid}", text)
    sec.append(f'''<section class="block" id="bestiaire">
  {plaque("bestiaire-h", "Danger", "Bestiaire", "Toutes les créatures du mod, avec leur vrai modèle 3D. Les boss ont deux phases : à mi-vie ils rugissent puis changent de rythme. Chaque attaque est annoncée (animation ou cercle au sol) : observe, esquive, punis. Frapper fort et souvent brise leur posture (+50 % de dégâts). En coop, leur vie augmente de 60 % par joueur.")}
  <h3 class="subhead">Les grands boss</h3><div class="grid mobs">{"".join(groups["boss"])}</div>
  <h3 class="subhead">Les champions de donjon</h3><div class="grid mobs">{"".join(groups["champion"])}</div>
  <h3 class="subhead">Les créatures</h3><div class="grid mobs">{"".join(groups["creature"])}</div>
</section>''')

    # ================================================================== STRUCTURES
    def biome_label(b):
        if b.startswith("#"):
            t = b[1:].split(":")[-1].replace("is_", "")
            return {"forest": "forêts", "hill": "collines", "taiga": "taïgas", "ocean": "océans", "beach": "plages",
                    "mountain": "montagnes", "badlands": "badlands", "overworld": "partout sous terre",
                    "jungle": "jungles", "savanna": "savanes", "river": "rivières"}.get(t, t.replace("_", " ")).capitalize()
        return vname("biome", b.split(":")[-1]) if VFR else pretty(b)

    wcards, scards = [], {"overworld": [], "nether": [], "end": []}
    order = sorted(defs.STRUCTURES, key=lambda s: (s.id not in wonder_ids, ["overworld", "nether", "end"].index(s.dimension)
                                                   if s.dimension in ("overworld", "nether", "end") else 9))
    for s in order:
        si = struct_info.get(s.id)
        if not si:
            continue
        title = FR.get(f"structure.wayfarers.{s.id}", s.title_fr or s.id)
        text = TXT.STRUCTURES.get(s.id) or (sys.modules[type(s).__module__].__doc__ or "")
        sx, sy, sz = si["size"]
        dim = TXT.DIMENSIONS.get(s.dimension, s.dimension)
        biomes_ = ", ".join(dict.fromkeys(biome_label(b) for b in s.biomes))
        if s.step == "underground_structures":
            dim = "Profondeurs · sous terre"
        elif s.heightmap.startswith("OCEAN"):
            dim += " · sous l'eau"
        who = list(dict.fromkeys(si["bosses"] + si["spawners"] + [sp[0] for sp in s.spawns]))
        who_html = "".join(f'<a class="chip" href="#b-{w.split(":")[1]}">{atlas.icon(w, 24)}<span>{E(name(w))}</span></a>'
                           if w.startswith("wayfarers:") and w.split(":")[1] in mob_info else
                           f'<span class="chip">{atlas.icon(w + "_spawn_egg", 24, label=name(w))}<span>{E(name(w))}</span></span>'
                           for w in who)
        loot = top_loot(si["loot"], 10)
        facts = [f'{sx} × {sy} × {sz} blocs', f'{si["blocks"]:,} blocs posés'.replace(",", " ")]
        if si["variants"] > 1:
            facts.append(f'{si["variants"]} variantes')
        if si["waystones"]:
            facts.append("pierre de voyage")
        f = si["files"]
        common = f'''<p class="dim">{E(dim)}</p><p>{E(text.strip())}</p>
  <p class="where">{SVG["pin"]} {E(biomes_)}</p>
  <p class="facts">{"".join(f"<span>{E(x)}</span>" for x in facts)}</p>
  {('<div class="inhab"><small>Habitants</small><span class="chips">' + who_html + '</span></div>') if who else ""}
  {('<div class="drops"><small>Dans les coffres</small>' + chips(atlas, loot, 24, item_link) + '</div>') if loot else ""}'''
        if s.id in wonder_ids:
            wcards.append(f'''<article class="wonder" id="s-{s.id}">
  <figure class="vitrine big"><img src="{f["gif"]}" alt="{E(title, quote=True)}, rotation à 360°" loading="lazy"><figcaption>Rotation 360°</figcaption></figure>
  <div class="wonder-body"><span class="badge wb">Merveille</span><h3>{E(title)}</h3>{common}
  <div class="views">
    <figure class="vitrine"><img src="{f["static"]}" alt="{E(title, quote=True)}, vue détaillée" loading="lazy"><figcaption>Vue détaillée</figcaption></figure>
    <figure class="vitrine"><img src="{f["back"]}" alt="{E(title, quote=True)}, vue de l'autre côté" loading="lazy"><figcaption>De l'autre côté</figcaption></figure>
    <figure class="vitrine"><img src="{f["cut"]}" alt="{E(title, quote=True)}, vue en coupe" loading="lazy"><figcaption>En coupe</figcaption></figure>
  </div></div>
</article>''')
        else:
            scards[s.dimension if s.dimension in scards else "overworld"].append(f'''<article class="card struct" id="s-{s.id}">
  <div class="vitrine flip"><img src="{f["gif"]}" alt="{E(title, quote=True)}, rotation" loading="lazy"><img class="detail" src="{f["static"]}" alt="{E(title, quote=True)}, vue détaillée" loading="lazy"></div>
  <div class="struct-body"><h4>{E(title)}</h4>{common}</div>
</article>''')
        idx.add(title, "Structure", f"s-{s.id}", text + " " + biomes_)
    sec.append(f'''<section class="block" id="structures">
  {plaque("structures-h", "Exploration", "Structures et merveilles", "Elles n'apparaissent que dans les régions jamais générées : le plus simple est un nouveau monde. La boussole des structures (accroupi + clic droit pour choisir la cible) donne la distance et la direction. Survole ou touche une image pour passer de la rotation à la vue détaillée.")}
  <h3 class="subhead">Les merveilles du monde</h3>
  {"".join(wcards)}
  {"".join(f'<h3 class="subhead">{E(t)}</h3><div class="grid structs">{"".join(scards[k])}</div>' for k, t in (("overworld", "Surface et profondeurs"), ("nether", "Nether"), ("end", "End")) if scards[k])}
</section>''')

    # ================================================================== NEW WORLD
    wm = find_worldmap(args.worldmap)
    head, legend = parse_worldmap_txt(os.path.join(wm, "wayfarers-worldmap.txt") if wm else None)
    map_html = ""
    share = {b.split(":")[-1]: (c, p) for c, b, p in legend}
    if wm:
        imgs = []
        for suf, cap in (("", "Surface : les biomes vus du ciel"), ("-caves", "Grottes : les biomes souterrains"),
                         ("-slice", "Coupe verticale : relief, grottes et méga-cavernes")):
            p = os.path.join(wm, f"wayfarers-worldmap{suf}.png")
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(out, "img", f"worldmap{suf}.png"))
                imgs.append(f'<figure class="map"><img src="img/worldmap{suf}.png" alt="{E(cap, quote=True)}" loading="lazy"><figcaption>{E(cap)}</figcaption></figure>')
        leg = "".join(f'<li><a href="#bi-{b.split(":")[-1]}"><i style="background:{c}"></i>{E(FR.get("biome." + b.replace(":", "."), pretty(b)))}</a><small>{fmt_num(p)} %</small></li>'
                      for c, b, p in sorted(legend, key=lambda x: -x[2]))
        map_html = f'''<div class="maps">{"".join(imgs)}</div>
  <p class="note">{E(map_caption(head))} Carte générée en jeu par <code>/wayfarers worldmap</code>.</p>
  <details class="legend-box"><summary>Légende des couleurs de la carte ({len(legend)} biomes)</summary><ul class="maplegend">{leg}</ul></details>'''
    inv = {}
    for v, o in B.VANILLA_TO_OURS.items():
        inv.setdefault(o, []).append(v)
    bgroups = {k: [] for k, _ in TXT.BIOME_GROUPS}
    for bid, b in B.BIOMES.items():
        src = inv.get(bid, [])
        if b["cave"] or bid in [c[0] for c in B.EXTRA_CAVES]:
            g = "cave"
        elif any(w in v for v in src for w in ("ocean", "beach", "river", "shore", "mushroom")):
            g = "ocean"
        elif b["temp"] < 0.3:
            g = "cold"
        elif b["temp"] >= 1.0:
            g = "warm"
        else:
            g = "temperate"
        sw = [("carte", share.get(bid, (None,))[0]), ("herbe", b.get("grass")), ("feuillage", b.get("foliage")),
              ("eau", b.get("water")), ("ciel", b.get("sky")), ("brume", b.get("fog"))]
        swatch = "".join(f'<i style="background:{c}" title="{l}"></i>' for l, c in sw if c)
        surf = surface_blocks(b["surface"])[:5]
        decor_ = ", ".join(dict.fromkeys(TXT.DECOR.get(d, d.replace("_", " ")) for d in b["decor"]))
        animals = []
        try:
            sp = WF.spawners(b["mobs"])
            for cat in (("water_creature", "creature") if g == "ocean" else ("creature",)):
                for e in sp.get(cat, []):
                    nm = vname("entity", e["type"].split(":")[-1])
                    if nm not in animals:
                        animals.append(nm)
        except Exception:  # noqa: BLE001
            pass
        monsters = []
        try:
            for e in WF.spawners(b["mobs"]).get("monster", []):
                nm = vname("entity", e["type"].split(":")[-1])
                if nm not in monsters:
                    monsters.append(nm)
        except Exception:  # noqa: BLE001
            pass
        replaces = ", ".join(vname("biome", v) for v in src) or ("biome de grotte en plus" if g == "cave" else "")
        pct = share.get(bid, (None, None))[1]
        bgroups[g].append(f'''<article class="biome" id="bi-{bid}">
  <div class="swatch">{swatch}</div>
  <h4>{E(b["fr"])}<small>{E(b["en"])}</small></h4>
  <p>{E(TXT.BIOMES.get(bid, ""))}</p>
  <dl>
    {f"<dt>Remplace</dt><dd>{E(replaces)}</dd>" if replaces else ""}
    {f'<dt>Sol</dt><dd class="icons">{"".join(atlas.icon(x, 26) for x in surf)}</dd>' if surf else ""}
    {f"<dt>Décor</dt><dd>{E(decor_)}</dd>" if decor_ else ""}
    {f"<dt>Animaux</dt><dd>{E(', '.join(animals[:8]))}</dd>" if animals else ""}
    {f"<dt>Monstres</dt><dd>{E(', '.join(monsters[:8]))}</dd>" if monsters and g != "ocean" else ""}
    <dt>Climat</dt><dd>{climate(b)}{f" · {fmt_num(pct)} % de la carte" if pct else ""}</dd>
  </dl>
</article>''')
        idx.add(b["fr"], "Biome", f"bi-{bid}", TXT.BIOMES.get(bid, "") + " " + b["en"])
    sec.append(f'''<section class="block" id="monde">
  {plaque("monde-h", "Le Nouveau Monde", "Relief, grottes et 41 biomes", "Le pack intégré <code>wayfarers:world_overhaul</code> remplace la génération de la Surface des <b>nouveaux</b> mondes : montagnes environ 65 % plus hautes (pics vers y 300), méga-cavernes entre y −40 et 10, et des biomes propres au mod. Villages, forteresses et structures apparaissent comme avant.")}
  <div class="callout"><b>Le désactiver :</b> mets <code>world.overhaul = false</code> dans <code>config/wayfarers-common.toml</code>, ou décoche le pack « Wayfarers : nouveau monde » dans l'écran Packs de données à la création du monde. Minecraft affiche un avertissement « expérimental » : c'est normal. Pour vérifier qu'il est actif : F3 affiche <code>wayfarers:…</code> comme biome, ou <code>/locate biome wayfarers:enchanted_forest</code>.</div>
  {map_html}
  {"".join(f'<h3 class="subhead">{E(t)}</h3><div class="grid biomes">{"".join(bgroups[k])}</div>' for k, t in TXT.BIOME_GROUPS if bgroups[k])}
</section>''')

    # ================================================================== ITEMS CATALOGUE
    deco_ids = set(decor.all_block_ids())
    furn_ids = set(furniture.FURNITURE)
    mach_ids = set(machines.MACHINES)
    metal_ids = metals.all_item_ids()
    boss_ids = set(weapon_of.values()) | set(remembrance_of.values())
    cats_order = [("Objets du voyageur", []), ("Armes et magie", []), ("Armes de boss et souvenirs", []),
                  ("Armures", []), ("Métaux et minerais", []), ("Machines", []), ("Blocs de construction", []),
                  ("Meubles", []), ("Blocs spéciaux", [])]
    cat_map = dict(cats_order)
    for iid in entries:
        is_block = f"block.wayfarers.{iid}" in FR
        d_ = desc(iid)
        if iid in boss_ids:
            c = "Armes de boss et souvenirs"
        elif iid in mach_ids:
            c = "Machines"
        elif iid in furn_ids:
            c = "Meubles"
        elif iid in deco_ids:
            c = "Blocs de construction"
        elif iid.endswith(("_helmet", "_chestplate", "_leggings", "_boots")):
            c = "Armures"
        elif iid in metal_ids:
            c = "Métaux et minerais"
        elif is_block:
            c = "Blocs spéciaux"
        elif any(w in " ".join(d_).lower() for w in ("mana", "sort", "clic droit : ruée", "onde", "foudre", "lancer")) or \
                iid.endswith(("_staff", "_blade", "_scythe", "_spear", "_hammer", "_wand")):
            c = "Armes et magie"
        else:
            c = "Objets du voyageur"
        rec = by_result.get("wayfarers:" + iid, [])
        how = ""
        if rec:
            how = f'<a class="how" href="#r-{rec[0]["file"]}">Recette{"s" if len(rec) > 1 else ""}</a>'
        elif iid in remembrance_of.values():
            boss = next(b for b, r in remembrance_of.items() if r == iid)
            how = f'<a class="how" href="#b-{boss}">Lâché par {E(name(boss))}</a>'
        cat_map[c].append(f'''<article class="item" id="{anchor_item(iid)}">{atlas.icon(iid, 48)}<div><b>{E(name(iid))}</b>
  {"".join(f"<span>{E(x)}</span>" for x in d_)}{how}</div></article>''')
        idx.add(name(iid), "Bloc" if is_block else "Objet", anchor_item(iid), " ".join(d_) + " " + EN.get(f"item.wayfarers.{iid}", EN.get(f"block.wayfarers.{iid}", "")))
    sec.append(f'''<section class="block" id="objets">
  {plaque("objets-h", "Catalogue", "Tous les objets et blocs", "Chaque objet du mod avec sa description en jeu. « Recette » mène à sa fabrication.")}
  {"".join(f'<details class="cat" {"open" if i < 2 else ""}><summary><span>{E(c)}</span><small>{len(v)}</small></summary><div class="grid items">{"".join(v)}</div></details>' for i, (c, v) in enumerate(cats_order) if v)}
</section>''')

    # ================================================================== RECIPES
    rgroups = {}
    for r in recipes:
        rgroups.setdefault(TXT.RECIPE_CATEGORIES.get(r["category"], r["category"].capitalize()), []).append(r)
    rhtml = []
    for gi, (g, rs) in enumerate(sorted(rgroups.items(), key=lambda kv: -len(kv[1]))):
        rs.sort(key=lambda r: (r["type"] == "minecraft:stonecutting", r["type"] != "minecraft:crafting_shaped", name(r["result"])))
        cards = "".join(f'<article class="recipe-card" id="r-{r["file"]}"><h5><a href="#{item_link(r["result"]) or ""}">{E(name(r["result"]))}</a>'
                        f'<small>{E(TXT.RECIPE_TYPES.get(r["type"], r["type"].split(":")[-1]))}</small></h5>{render_recipe(atlas, r, item_link)}</article>'
                        for r in rs)
        rhtml.append(f'<details class="cat" {"open" if gi == 0 else ""}><summary><span>{E(g)}</span><small>{len(rs)}</small></summary><div class="grid recipes">{cards}</div></details>')
    sec.append(f'''<section class="block" id="recettes">
  {plaque("recettes-h", "Fabrication", "Toutes les recettes", "Générées depuis les fichiers de recettes du mod : établi, four, haut fourneau et tailleur de pierre.")}
  {"".join(rhtml)}
</section>''')

    # ------------------------------------------------------------------ write
    rows = atlas.save(os.path.join(out, "img", "atlas.png"))
    page = render_page(sec, idx, rows)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    files = [os.path.join(dp, f) for dp, _dn, fs in os.walk(out) for f in fs]
    total = sum(os.path.getsize(f) for f in files)
    log(f"wiki: {out}/index.html  {len(files)} files, {total / 1e6:.1f} MB, {time.time() - t0:.0f}s")


# =============================================================================================== recipes
TAG_ICON = {"planks": "minecraft:oak_planks", "logs": "minecraft:oak_log", "wool": "minecraft:white_wool",
            "stone_tool_materials": "minecraft:cobblestone", "stone_crafting_materials": "minecraft:cobblestone",
            "coals": "minecraft:coal", "wooden_slabs": "minecraft:oak_slab", "sand": "minecraft:sand",
            "candles": "minecraft:candle", "leaves": "minecraft:oak_leaves", "saplings": "minecraft:oak_sapling",
            "copper_ores": "minecraft:copper_ore", "iron_ores": "minecraft:iron_ore", "chests": "minecraft:chest"}


def slot(atlas, ids, item_link, count=None):
    if not ids:
        return '<span class="slot"></span>'
    i = ids[0]
    if i.startswith("#"):
        tag = i[1:].split(":")[-1].split("/")[-1]
        rep = TAG_ICON.get(tag)
        label = f"n'importe quel(le) {tag.replace('_', ' ')}"
        inner = atlas.icon(rep, 32, label=label) if rep else f'<i class="ic ic-none" style="--s:32px" title="{E(label, quote=True)}">#</i>'
        return f'<span class="slot tag" title="{E(label, quote=True)}">{inner}</span>'
    if ":" not in i:
        i = "minecraft:" + i
    a = item_link(i)
    c = f'<b class="count">{count}</b>' if count and count > 1 else ""
    inner = atlas.icon(i, 32) + c
    return f'<a class="slot" href="#{a}">{inner}</a>' if a else f'<span class="slot">{inner}</span>'


def render_recipe(atlas, r, item_link):
    d, t = r["data"], r["type"]
    res = slot(atlas, [r["result"]], item_link, r["count"])
    arrow = '<span class="arrow" aria-hidden="true"></span>'
    if t.endswith("crafting_shaped"):
        pat = d["pattern"]
        cells = []
        for row in range(3):
            for col in range(3):
                ch = pat[row][col] if row < len(pat) and col < len(pat[row]) else " "
                cells.append(slot(atlas, ingredient_ids(d["key"].get(ch)) if ch != " " else [], item_link))
        return f'<div class="recipe"><div class="grid3">{"".join(cells)}</div>{arrow}{res}</div>'
    if t.endswith("crafting_shapeless"):
        ings = d.get("ingredients", [])
        cells = [slot(atlas, ingredient_ids(x), item_link) for x in ings] + ['<span class="slot"></span>'] * (9 - len(ings))
        return f'<div class="recipe"><div class="grid3">{"".join(cells[:9])}</div>{arrow}{res}</div>'
    if t.endswith("crafting_transmute"):
        cells = [slot(atlas, ingredient_ids(d.get("input")), item_link), slot(atlas, ingredient_ids(d.get("material")), item_link)]
        return f'<div class="recipe"><div class="row">{"".join(cells)}</div>{arrow}{res}<small class="rnote">le contenu est gardé</small></div>'
    if t.endswith(("smelting", "blasting", "smoking", "campfire_cooking")):
        ic = {"smelting": "minecraft:furnace", "blasting": "minecraft:blast_furnace", "smoking": "minecraft:smoker"}.get(t.split(":")[-1], "minecraft:campfire")
        return (f'<div class="recipe"><div class="row">{slot(atlas, ingredient_ids(d.get("ingredient")), item_link)}'
                f'<span class="station">{atlas.icon(ic, 28)}</span></div>{arrow}{res}<small class="rnote">{d.get("cookingtime", 200) / 20:g} s · {d.get("experience", 0)} XP</small></div>')
    if t.endswith(("stonecutting", "smithing_transform")):
        ings = [ingredient_ids(d.get(k)) for k in ("template", "base", "addition", "ingredient") if d.get(k)]
        st = atlas.icon("minecraft:stonecutter" if "stone" in t else "minecraft:smithing_table", 28)
        return f'<div class="recipe"><div class="row">{"".join(slot(atlas, x, item_link) for x in ings)}<span class="station">{st}</span></div>{arrow}{res}</div>'
    return f'<div class="recipe">{res}</div>'


# =============================================================================================== page
FONTS = ("https://fonts.googleapis.com/css2?family=Zilla+Slab:ital,wght@0,500;0,700;1,500&family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400"
         "&family=JetBrains+Mono:wght@400;600&family=Pixelify+Sans:wght@500;700&display=swap")


def render_page(sections, idx, atlas_rows):
    nav = [("accueil", "Accueil"), ("commencer", "Par où commencer"), ("touches", "Touches & commandes"),
           ("quetes", "Quêtes"), ("manuel", "Le Manuel"), ("talents", "Talents & magie"), ("machines", "Machines"),
           ("metaux", "Métaux & armures"), ("deco", "Déco & meubles"), ("armes3d", "Armes en 3D"),
           ("bestiaire", "Bestiaire"), ("structures", "Structures"), ("monde", "Nouveau Monde"),
           ("objets", "Tous les objets"), ("recettes", "Recettes")]
    nav_html = "".join(f'<a href="#{a}">{E(t)}</a>' for a, t in nav)
    data = json.dumps(idx.rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<title>Wayfarers Wiki</title>
<meta name="description" content="Le guide illustré du mod Wayfarers : systèmes, bestiaire, structures, biomes et recettes.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{CSS.replace("__ATLAS_COLS__", str(COLS)).replace("__ATLAS_ROWS__", str(atlas_rows))}</style>
<a class="skip" href="#main">Aller au contenu</a>
<header class="top">
  <a class="brand" href="#accueil">{SVG["cog"]}<span><b>Wayfarers</b><small>le grand manuel illustré</small></span></a>
  <div class="search" role="search">
    {SVG["search"]}<input id="q" type="search" placeholder="Chercher un objet, un boss, un biome…" autocomplete="off" aria-label="Rechercher dans le wiki">
    <div id="results" class="results" role="listbox" hidden></div>
  </div>
  <button id="theme" class="theme" type="button" aria-label="Changer de thème">{SVG["moon"]}</button>
</header>
<div class="layout">
  <nav class="side" aria-label="Sommaire">{nav_html}</nav>
  <main id="main">
{"".join(sections)}
<footer class="foot"><p>Page générée par <code>python3 tools/gen_wiki.py</code> à partir des données du mod — {time.strftime("%d/%m/%Y %H:%M")}.</p></footer>
  </main>
</div>
<script type="application/json" id="wiki-index">{data}</script>
<script>{JS}</script>
"""


CSS = r"""
:root{
  --paper:#ece3cf;--paper-2:#e2d5b8;--card:#f6f0e2;--card-2:#efe6d1;--ink:#231c14;--ink-2:#5d4c38;--ink-3:#8a7558;
  --rule:#cdb98f;--brass:#a8761f;--brass-hi:#e4b75a;--brass-lo:#6e4b12;--verd:#2f7d6d;--verd-2:#d6e9e2;
  --rust:#a4472b;--case:#181b1f;--case-rim:#3a3226;--link:#1f6a5c;--shadow:0 1px 0 rgba(255,255,255,.6) inset,0 2px 10px rgba(60,40,10,.12);
  --plate-ink:#2a1d08;--kbd:#fbf6ea;--chip:#efe5cd;--focus:#1f6a5c;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#121416;--paper-2:#181b1e;--card:#1d2024;--card-2:#23272c;--ink:#ece2cc;--ink-2:#b9ab90;--ink-3:#8c8068;
  --rule:#3b352a;--brass:#d6a64b;--brass-hi:#f0c977;--brass-lo:#8a6320;--verd:#62bba7;--verd-2:#1d3530;
  --rust:#d77452;--case:#181b1f;--case-rim:#4a4030;--link:#7fcfbd;--shadow:0 2px 14px rgba(0,0,0,.45);
  --plate-ink:#22180a;--kbd:#2a2e33;--chip:#262a2f;--focus:#f0c977;color-scheme:dark}}
:root[data-theme="dark"]{
  --paper:#121416;--paper-2:#181b1e;--card:#1d2024;--card-2:#23272c;--ink:#ece2cc;--ink-2:#b9ab90;--ink-3:#8c8068;
  --rule:#3b352a;--brass:#d6a64b;--brass-hi:#f0c977;--brass-lo:#8a6320;--verd:#62bba7;--verd-2:#1d3530;
  --rust:#d77452;--case:#181b1f;--case-rim:#4a4030;--link:#7fcfbd;--shadow:0 2px 14px rgba(0,0,0,.45);
  --plate-ink:#22180a;--kbd:#2a2e33;--chip:#262a2f;--focus:#f0c977;color-scheme:dark}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:84px}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 "Alegreya Sans",system-ui,sans-serif;
  background-image:radial-gradient(circle at 20% 0,rgba(168,118,31,.07),transparent 40%),repeating-linear-gradient(0deg,transparent 0 31px,rgba(140,110,60,.05) 31px 32px);}
img{max-width:100%;height:auto}
a{color:var(--link);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
code{font:0.86em "JetBrains Mono",ui-monospace,monospace;background:var(--card-2);border:1px solid var(--rule);border-radius:4px;padding:.05em .35em;overflow-wrap:anywhere}
kbd{font:600 .85em "Pixelify Sans","JetBrains Mono",monospace;display:inline-block;white-space:nowrap;min-width:1.9em;text-align:center;padding:.1em .45em;
  background:var(--kbd);border:1px solid var(--rule);border-bottom-width:3px;border-radius:5px;color:var(--ink)}
.skip{position:absolute;left:-999px}.skip:focus{left:12px;top:12px;z-index:99;background:var(--card);padding:6px 10px}
/* top bar */
.top{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:16px;padding:10px 24px;
  background:linear-gradient(180deg,#2b2620,#1c1a17);color:#efe3c8;border-bottom:3px solid var(--brass);box-shadow:0 4px 16px rgba(0,0,0,.25)}
.brand{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none;flex:none}
.brand svg{width:34px;height:34px;fill:var(--brass-hi);animation:spin 18s linear infinite}
.brand b{display:block;font:700 22px/1 "Zilla Slab",serif;letter-spacing:.06em;text-transform:uppercase;color:#f3d48a}
.brand small{display:block;font-size:12px;color:#c9b88f;letter-spacing:.04em}
@keyframes spin{to{transform:rotate(360deg)}}
.search{position:relative;flex:1;max-width:560px;margin-left:auto}
.search svg{position:absolute;left:12px;top:50%;width:16px;height:16px;transform:translateY(-50%);fill:#b8a780}
.search input{width:100%;font:inherit;font-size:16px;padding:9px 12px 9px 36px;border-radius:999px;border:1px solid #6b5a3b;
  background:#100f0d;color:#f1e6cc}
.search input::placeholder{color:#9b8c6c}
.results{position:absolute;left:0;right:0;top:calc(100% + 6px);max-height:min(70vh,520px);overflow:auto;background:var(--card);
  color:var(--ink);border:1px solid var(--rule);border-radius:10px;box-shadow:0 12px 32px rgba(0,0,0,.3);padding:6px}
.results a{display:flex;gap:10px;align-items:baseline;padding:7px 10px;border-radius:6px;text-decoration:none;color:var(--ink)}
.results a small{flex:none;font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--brass-lo);background:var(--chip);border-radius:4px;padding:1px 6px}
.results a span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink-3);font-size:14px}
.results a b{flex:none;font-weight:700}
.results a[aria-selected="true"],.results a:hover{background:var(--card-2)}
.results p{margin:8px 10px;color:var(--ink-3)}
.theme{flex:none;width:38px;height:38px;border-radius:50%;border:1px solid #6b5a3b;background:#100f0d;cursor:pointer;display:grid;place-items:center}
.theme svg{width:18px;height:18px;fill:#f0c977}
/* layout */
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:32px;max-width:1360px;margin:0 auto;padding:0 24px}
.side{position:sticky;top:84px;align-self:start;display:flex;flex-direction:column;gap:2px;padding:20px 0;max-height:calc(100vh - 90px);overflow:auto}
.side a{color:var(--ink-2);text-decoration:none;padding:6px 12px;border-left:3px solid transparent;font-weight:500;border-radius:0 6px 6px 0}
.side a:hover{color:var(--ink);background:var(--card-2)}
.side a.on{color:var(--ink);border-left-color:var(--brass);background:var(--card)}
main{min-width:0;padding-bottom:60px}
/* icons */
.ic{--s:40px;display:inline-block;flex:none;width:var(--s);height:var(--s);vertical-align:middle;image-rendering:pixelated;
  background-image:url(img/atlas.png);background-repeat:no-repeat;
  background-size:calc(var(--s) * __ATLAS_COLS__) calc(var(--s) * __ATLAS_ROWS__);
  background-position:calc(var(--x) * var(--s) * -1) calc(var(--y) * var(--s) * -1)}
.ic-none{background:var(--chip);border:1px dashed var(--rule);border-radius:4px;font:700 11px/1 "Pixelify Sans",monospace;
  color:var(--ink-3);display:inline-grid;place-items:center;overflow:hidden}
/* hero */
.hero{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:28px;align-items:center;padding:36px 0 18px}
.kicker{display:inline-block;font:600 12px/1.2 "Pixelify Sans",monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--verd)}
h1{font:700 clamp(46px,8vw,92px)/.95 "Zilla Slab",serif;margin:10px 0 14px;letter-spacing:.01em;
  background:linear-gradient(180deg,var(--brass-hi),var(--brass) 55%,var(--brass-lo));-webkit-background-clip:text;background-clip:text;color:transparent}
.lede{font-size:19px;color:var(--ink-2);max-width:62ch;margin:6px 0 0}
.stats{list-style:none;padding:0;margin:22px 0 0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.stats li{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px 10px;box-shadow:var(--shadow)}
.stats b{display:block;font:700 26px/1 "Pixelify Sans",monospace;color:var(--brass-lo)}
:root[data-theme="dark"] .stats b{color:var(--brass-hi)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .stats b{color:var(--brass-hi)}}
.stats span{font-size:13px;color:var(--ink-3)}
.vitrine{position:relative;margin:0;background:var(--case);border-radius:10px;border:3px solid var(--case-rim);
  box-shadow:0 0 0 1px var(--brass-lo),0 6px 18px rgba(0,0,0,.25),inset 0 0 30px rgba(0,0,0,.6);overflow:hidden;display:grid;place-items:center}
.vitrine::before,.vitrine::after{content:"";position:absolute;width:7px;height:7px;border-radius:50%;top:6px;left:6px;
  background:radial-gradient(circle at 35% 35%,#f6d98e,#8a6320 70%);z-index:2}
.vitrine::after{left:auto;right:6px}
.vitrine figcaption{position:absolute;left:8px;bottom:6px;font:600 11px "Pixelify Sans",monospace;color:#d8c69c;background:rgba(0,0,0,.55);padding:2px 7px;border-radius:4px}
.hero-fig{aspect-ratio:1/1;max-height:520px}
.hero-fig img{width:100%;height:100%;object-fit:contain}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:18px 0 8px}
.tile{display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--card);border:1px solid var(--rule);border-radius:10px;
  color:var(--ink);text-decoration:none;font-weight:600;box-shadow:var(--shadow);transition:transform .15s}
.tile:hover{transform:translateY(-2px);border-color:var(--brass)}
/* section plaques */
.block{padding:30px 0 10px;border-top:1px solid var(--rule);margin-top:24px}
.plaque{position:relative;margin:0 0 20px;padding:16px 22px 16px;border-radius:8px;
  background:linear-gradient(172deg,#f0d084 0%,#d6a74a 38%,#c0903a 70%,#d9ad55 100%);color:var(--plate-ink);
  box-shadow:inset 0 1px 0 rgba(255,250,220,.7),inset 0 -2px 0 rgba(80,50,10,.4),0 3px 10px rgba(60,40,10,.25)}
.plaque::before,.plaque::after{content:"";position:absolute;top:10px;width:9px;height:9px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#fff3c4,#7a5418 75%)}
.plaque::before{left:9px}.plaque::after{right:9px}
.plaque .kicker{color:#4a3510}
.plaque h2{font:700 clamp(26px,3.4vw,38px)/1.05 "Zilla Slab",serif;margin:4px 0 0;letter-spacing:.01em;text-shadow:0 1px 0 rgba(255,240,200,.6)}
.plaque .lede{color:#3d2c0e;font-size:17px;margin-top:8px}
.plaque .lede code{background:rgba(255,245,220,.5);border-color:rgba(80,50,10,.3)}
.plaque .lede kbd{background:#fbf3dc;color:#2a1d08}
.subhead{display:flex;align-items:center;gap:10px;font:700 22px/1.2 "Zilla Slab",serif;margin:28px 0 12px;color:var(--ink)}
.subhead::after{content:"";flex:1;height:2px;background:linear-gradient(90deg,var(--rule),transparent)}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:28px}
.note{color:var(--ink-3);font-size:15px}
.callout{border-left:4px solid var(--verd);background:var(--verd-2);padding:12px 16px;border-radius:0 8px 8px 0;margin:0 0 18px}
/* steps */
.steps{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;counter-reset:s}
.step{display:flex;gap:14px;background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:14px;box-shadow:var(--shadow)}
.step .num{flex:none;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;font:700 18px "Pixelify Sans",monospace;
  color:#2a1d08;background:radial-gradient(circle at 35% 30%,#f6d98e,#b98a2e 70%);box-shadow:inset 0 -2px 0 rgba(0,0,0,.25)}
.step h4{margin:2px 0 4px;font:700 18px "Zilla Slab",serif}
.step p{margin:0 0 8px;color:var(--ink-2);font-size:15.5px}
/* tables */
.tbl{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--rule);border-radius:8px;overflow:hidden;font-size:15px}
.tbl th{text-align:left;font:700 13px "Zilla Slab",serif;text-transform:uppercase;letter-spacing:.06em;background:var(--card-2);color:var(--ink-2)}
.tbl th,.tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.tbl small{color:var(--ink-3)}
.tbl.keys td:first-child{width:120px}.tbl td:first-child code{white-space:nowrap}
.who{font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;padding:1px 6px;border-radius:4px;background:var(--verd-2);color:var(--verd)}
.who.op{background:rgba(164,71,43,.15);color:var(--rust)}
.scroll{overflow-x:auto}
/* chips */
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 0}
.chip{display:inline-flex;align-items:center;gap:6px;padding:2px 9px 2px 3px;background:var(--chip);border:1px solid var(--rule);border-radius:999px;
  color:var(--ink);text-decoration:none;font-size:14px;line-height:1.3;max-width:100%}
.chip span{overflow:hidden;text-overflow:ellipsis}
a.chip:hover{border-color:var(--brass)}
/* cards */
.grid{display:grid;gap:14px}
.pages{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.minis{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
.card{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:16px;box-shadow:var(--shadow);min-width:0}
.card h4{display:flex;align-items:center;gap:10px;margin:0 0 8px;font:700 19px/1.2 "Zilla Slab",serif}
.card p{margin:0 0 8px}
.card.mini h4{font-size:17px}
.card.mini p{font-size:15px;color:var(--ink-2)}
.small,.card .small{font-size:14px;color:var(--ink-3)}
:target{animation:flash 1.6s ease-out}
@keyframes flash{0%{box-shadow:0 0 0 4px var(--brass-hi)}100%{box-shadow:var(--shadow)}}
/* quests */
.chapter,.cat{background:var(--card);border:1px solid var(--rule);border-radius:10px;margin:0 0 10px;box-shadow:var(--shadow)}
.chapter summary,.cat summary{cursor:pointer;display:flex;justify-content:space-between;align-items:center;padding:12px 16px;font:700 19px "Zilla Slab",serif;list-style:none}
.chapter summary::-webkit-details-marker,.cat summary::-webkit-details-marker{display:none}
.chapter summary::before,.cat summary::before{content:"";width:10px;height:10px;border-right:3px solid var(--brass);border-bottom:3px solid var(--brass);transform:rotate(-45deg);margin-right:12px;transition:transform .2s}
.chapter[open] summary::before,.cat[open] summary::before{transform:rotate(45deg)}
.chapter summary span,.cat summary span{flex:1}
.chapter summary small,.cat summary small{font:600 12px "Pixelify Sans",monospace;color:var(--ink-3)}
.quests{list-style:none;margin:0;padding:0 16px 14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px}
.quest{display:flex;gap:10px;align-items:flex-start;padding:8px;border-radius:8px;background:var(--card-2)}
.quest b{display:block}.quest span{display:block;font-size:14.5px;color:var(--ink-2)}
.quest small{font:600 11px "Pixelify Sans",monospace;color:var(--verd)}
.quest.challenge{outline:2px solid var(--brass)}.quest.goal{outline:1px dashed var(--brass)}
.cat > .grid{padding:0 16px 16px}
/* talents */
.branches{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:14px}
.branch{background:var(--card);border:1px solid var(--rule);border-top:4px solid var(--branch);border-radius:10px;padding:14px;box-shadow:var(--shadow);min-width:0}
.branch h4{display:flex;align-items:center;gap:8px;margin:0 0 6px;font:700 20px "Zilla Slab",serif}
.tree{position:relative;width:100%;background:var(--case);border-radius:8px;border:2px solid var(--case-rim);margin:6px 0 10px}
.tree svg{position:absolute;inset:0;width:100%;height:100%}
.tree line{stroke:var(--branch);stroke-width:3;opacity:.65;vector-effect:non-scaling-stroke}
.node{position:absolute;transform:translate(-50%,-50%);width:31%;display:flex;flex-direction:column;align-items:center;text-align:center;
  background:#24282d;border:1px solid #4b4334;border-radius:8px;padding:4px 2px;color:#efe3c8;cursor:help}
.node b{font-size:11.5px;line-height:1.1;margin-top:2px;hyphens:auto}
.node small{color:var(--branch);font-size:9px;letter-spacing:1px}
.node.active{border:2px solid var(--branch);box-shadow:0 0 12px var(--branch)}
.legend{margin:0;padding-left:18px;font-size:14px;color:var(--ink-2)}
.legend li{margin:2px 0}
.rows{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:8px}
.rows li{display:flex;gap:10px;align-items:center;background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px}
.rows li span{display:block;font-size:14.5px;color:var(--ink-2)}
/* machines, metals */
.machines{grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.mhead{display:flex;align-items:center;gap:12px}.mhead h4{margin:0}
.ticks{margin:8px 0;padding-left:18px;font-size:15px;color:var(--ink-2)}
.metals{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.where{display:flex;gap:6px;align-items:flex-start;font-size:15px;color:var(--ink-2)}
.where svg{flex:none;width:15px;height:15px;margin-top:3px;fill:var(--verd)}
.bonus{margin-top:10px!important;padding:8px 10px;background:var(--verd-2);border-radius:6px;font-size:15px}
.tiers{list-style:none;padding:0;margin:0 0 16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}
.tiers li{display:grid;grid-template-columns:auto 1fr;column-gap:10px;align-items:center;background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px}
.tiers li .ic{grid-row:span 2}.tiers li span{font-size:13.5px;color:var(--ink-3)}
/* decor */
.decos{grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.deco{display:flex;gap:12px;align-items:center;background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:10px;box-shadow:var(--shadow)}
.deco b{display:block;line-height:1.2}.deco .glow{font:600 11px "Pixelify Sans",monospace;color:var(--brass)}
.vars{display:flex;gap:2px;margin-top:4px}
.spins{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
.spin{margin:0;min-width:0}
.sprite{aspect-ratio:1/1;width:100%;background-image:var(--sheet);background-repeat:no-repeat;
  background-size:calc(var(--cols) * 100%) calc(var(--rows) * 100%);
  background-position:calc(var(--cx) * 100% / max(1, var(--cols) - 1)) calc(var(--cy) * 100% / max(1, var(--rows) - 1));
  background-color:var(--case)}
.spin figcaption{padding:6px 2px 0;font-size:14px;line-height:1.25}
.spin figcaption a{display:flex;align-items:center;gap:6px;color:var(--ink);text-decoration:none}
.spin figcaption small{display:block;color:var(--ink-3);font-size:13px;margin-top:2px}
.gear td{vertical-align:middle}.gear a{text-decoration:none;color:var(--ink)}
/* bestiary */
.mobs{grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.mob{padding:0;overflow:hidden;display:flex;flex-direction:column}
.mob .vitrine{border-radius:0;border-width:0 0 3px;aspect-ratio:1/1}
.mob .vitrine img{width:100%;height:100%;object-fit:contain}
.mob-body{padding:12px 16px 16px}
.mob-body h4{margin:4px 0 4px}
.badge{display:inline-block;font:700 11px "Pixelify Sans",monospace;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;border-radius:4px;background:var(--chip);color:var(--ink-2)}
.badge.boss{background:var(--rust);color:#fff4e6}.badge.champion{background:var(--brass);color:#24180a}.badge.wb{background:var(--verd);color:#effaf6}
.statline{display:flex;gap:16px;font:700 15px "Pixelify Sans",monospace}
.statline span{display:inline-flex;align-items:center;gap:5px}
.statline svg{width:15px;height:15px}
.statline span:first-child svg{fill:var(--rust)}.statline span:last-child svg{fill:var(--ink-2)}
.drops,.inhab{margin-top:8px}.drops small,.inhab small{display:block;font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--ink-3)}
/* structures */
.structs{grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.struct{padding:0;overflow:hidden}
.struct .vitrine{border-radius:0;border-width:0 0 3px;aspect-ratio:4/3}
.flip img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;transition:opacity .35s}
.flip .detail{opacity:0}
.flip:hover .detail,.flip.on .detail{opacity:1}
.struct-body{padding:12px 16px 16px}
.dim{font:600 12px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--verd);margin:0 0 4px!important}
.facts{display:flex;flex-wrap:wrap;gap:6px}.facts span{font-size:13px;background:var(--card-2);border:1px solid var(--rule);border-radius:4px;padding:1px 7px}
.wonder{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.05fr);gap:22px;background:var(--card);border:1px solid var(--rule);
  border-radius:12px;padding:16px;margin:0 0 18px;box-shadow:var(--shadow)}
.wonder .big{aspect-ratio:1/1}
.wonder .big img{width:100%;height:100%;object-fit:contain}
.wonder h3{font:700 30px/1.1 "Zilla Slab",serif;margin:6px 0 4px}
.views{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:12px}
.views .vitrine{aspect-ratio:1/1}.views img{width:100%;height:100%;object-fit:contain;cursor:zoom-in}
/* world */
.maps{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin:14px 0}
.map{margin:0;background:var(--case);border:3px solid var(--case-rim);border-radius:10px;padding:8px}
.map img{width:100%;image-rendering:pixelated;display:block;border-radius:4px}
.map figcaption{color:#d8c69c;font-size:14px;padding:6px 2px 0}
.legend-box{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:10px 14px;margin:0 0 10px}
.legend-box summary{cursor:pointer;font-weight:700}
.maplegend{list-style:none;padding:0;margin:10px 0 0;columns:220px;column-gap:18px;font-size:14.5px}
.maplegend li{display:flex;align-items:center;gap:8px;break-inside:avoid;padding:2px 0}
.maplegend a{display:flex;align-items:center;gap:8px;color:var(--ink);text-decoration:none;flex:1}
.maplegend i{width:14px;height:14px;border-radius:3px;flex:none;border:1px solid rgba(0,0,0,.3)}
.maplegend small{color:var(--ink-3)}
.biomes{grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.biome{background:var(--card);border:1px solid var(--rule);border-radius:10px;overflow:hidden;box-shadow:var(--shadow);min-width:0}
.swatch{display:flex;height:16px}.swatch i{flex:1}
.biome h4{margin:10px 14px 2px;font:700 19px "Zilla Slab",serif;display:flex;flex-wrap:wrap;align-items:baseline;gap:8px}
.biome h4 small{font:500 13px "Alegreya Sans",sans-serif;color:var(--ink-3)}
.biome p{margin:0 14px 6px;font-size:15px;color:var(--ink-2)}
.biome dl{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;margin:6px 14px 14px;font-size:14px}
.biome dt{font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--ink-3);padding-top:3px}
.biome dd{margin:0}.biome dd.icons{display:flex;gap:3px}
/* items */
.items{grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.item{display:flex;gap:10px;align-items:flex-start;background:var(--card-2);border:1px solid var(--rule);border-radius:8px;padding:8px;min-width:0}
.item b{display:block;line-height:1.2}.item span{display:block;font-size:14px;color:var(--ink-2)}
.how{display:inline-block;margin-top:4px;font:600 12px "Pixelify Sans",monospace;text-transform:uppercase}
/* recipes */
.recipes{grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.recipe-card{background:var(--card-2);border:1px solid var(--rule);border-radius:8px;padding:10px}
.recipe-card h5{margin:0 0 8px;font:700 16px "Zilla Slab",serif;display:flex;justify-content:space-between;gap:8px}
.recipe-card h5 a{color:var(--ink);text-decoration:none}
.recipe-card h5 small{font:500 12px "Alegreya Sans",sans-serif;color:var(--ink-3);text-align:right}
.recipe{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px}
.grid3{display:grid;grid-template-columns:repeat(3,40px);gap:2px;background:#8b8b8b;padding:3px;border-radius:3px}
.row{display:flex;gap:4px;align-items:center}
.slot{position:relative;width:40px;height:40px;display:grid;place-items:center;background:#8b8b8b;
  box-shadow:inset 2px 2px 0 #373737,inset -2px -2px 0 #fff;text-decoration:none}
.grid3 .slot{box-shadow:inset 2px 2px 0 #373737,inset -2px -2px 0 #fff}
.slot .count{position:absolute;right:2px;bottom:0;font:700 13px "Pixelify Sans",monospace;color:#fff;text-shadow:2px 2px 0 #3f3f3f}
.slot.tag::after{content:"#";position:absolute;left:3px;top:0;font:700 11px monospace;color:#fff;text-shadow:1px 1px 0 #333}
.arrow{width:30px;height:20px;background:linear-gradient(90deg,var(--ink-3),var(--ink-3)) left center/20px 6px no-repeat;position:relative}
.arrow::after{content:"";position:absolute;right:0;top:0;border:10px solid transparent;border-left:10px solid var(--ink-3);border-right:0}
.station{display:grid;place-items:center;width:34px}
.rnote{width:100%;color:var(--ink-3);font-size:13px}
.machine .recipe{margin-top:10px}
.foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--rule);color:var(--ink-3);font-size:14px}
/* responsive */
@media (max-width:1060px){
  .layout{grid-template-columns:minmax(0,1fr);padding:0 16px;gap:0}
  .side{position:sticky;top:60px;z-index:20;flex-direction:row;overflow-x:auto;max-height:none;padding:8px 0;margin:0 -16px;padding-left:16px;
    background:var(--paper);border-bottom:1px solid var(--rule);scrollbar-width:none}
  .side a{white-space:nowrap;border-left:0;border-bottom:3px solid transparent;border-radius:6px 6px 0 0;padding:6px 10px;font-size:15px}
  .side a.on{border-bottom-color:var(--brass)}
  html{scroll-padding-top:120px}
  .wonder{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:760px){
  .top{padding:8px 16px;gap:10px}
  .results{position:fixed;left:8px;right:8px;top:60px}
  .brand small{display:none}.brand b{font-size:18px}.brand svg{width:28px;height:28px}
  .hero{grid-template-columns:minmax(0,1fr);padding-top:20px}
  .stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  .two{grid-template-columns:minmax(0,1fr)}
  .plaque{padding:14px 16px}
  .tbl{font-size:14px}.tbl th,.tbl td{padding:6px 7px}
  .tbl td:first-child code{white-space:normal;word-break:break-word}
  .steps,.pages,.minis,.quests,.branches,.rows,.machines,.metals,.decos,.mobs,.structs,.biomes,.items,.recipes{grid-template-columns:minmax(0,1fr)}
  .spins{grid-template-columns:repeat(2,minmax(0,1fr))}
  .views{grid-template-columns:repeat(3,minmax(0,1fr))}
  body{font-size:16px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""

JS = r"""
(function(){
  var root=document.documentElement;
  try{var t=localStorage.getItem('wf-theme');if(t)root.setAttribute('data-theme',t);}catch(e){}
  document.getElementById('theme').addEventListener('click',function(){
    var dark=root.getAttribute('data-theme')?root.getAttribute('data-theme')==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
    var next=dark?'light':'dark';root.setAttribute('data-theme',next);try{localStorage.setItem('wf-theme',next);}catch(e){}
  });
  // search
  var rows=JSON.parse(document.getElementById('wiki-index').textContent);
  var norm=function(s){return (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();};
  rows.forEach(function(r){r.n=norm(r[0]);r.x=norm(r[3]);});
  var q=document.getElementById('q'),box=document.getElementById('results'),sel=-1;
  function esc(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function run(){
    var v=norm(q.value.trim());sel=-1;
    if(v.length<2){box.hidden=true;return;}
    var words=v.split(/\s+/);
    var hits=rows.map(function(r){var s=0;for(var i=0;i<words.length;i++){var w=words[i];
        if(r.n.indexOf(w)===0)s+=5;else if(r.n.indexOf(w)>=0)s+=3;else if(r.x.indexOf(w)>=0)s+=1;else return null;}
        return [s,r];}).filter(Boolean).sort(function(a,b){return b[0]-a[0]||a[1][0].length-b[1][0].length;}).slice(0,40);
    box.innerHTML=hits.length?hits.map(function(h,i){var r=h[1];return '<a role="option" href="#'+r[2]+'" data-i="'+i+'"><small>'+esc(r[1])+'</small><b>'+esc(r[0])+'</b><span>'+esc((r[3]||'').slice(0,90))+'</span></a>';}).join('')
      :'<p>Rien trouvé pour « '+esc(q.value)+' ».</p>';
    box.hidden=false;
  }
  q.addEventListener('input',run);
  q.addEventListener('focus',run);
  q.addEventListener('keydown',function(e){
    var links=box.querySelectorAll('a');if(!links.length)return;
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();sel=(sel+(e.key==='ArrowDown'?1:-1)+links.length)%links.length;
      links.forEach(function(a,i){a.setAttribute('aria-selected',i===sel);});links[sel].scrollIntoView({block:'nearest'});}
    else if(e.key==='Enter'){e.preventDefault();(links[sel>=0?sel:0]).click();}
    else if(e.key==='Escape'){box.hidden=true;}
  });
  box.addEventListener('click',function(e){var a=e.target.closest('a');if(a){box.hidden=true;q.blur();openTarget(a.getAttribute('href').slice(1));}});
  document.addEventListener('click',function(e){if(!e.target.closest('.search'))box.hidden=true;});
  document.addEventListener('keydown',function(e){if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
  // open <details> around a hash target
  function openTarget(id){var el=document.getElementById(id);if(!el)return;var d=el.closest('details');while(d){d.open=true;d=d.parentElement.closest('details');}}
  window.addEventListener('hashchange',function(){openTarget(location.hash.slice(1));});
  if(location.hash)openTarget(location.hash.slice(1));
  document.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');if(a)openTarget(a.getAttribute('href').slice(1));});
  // tap to flip structure views on touch screens
  document.querySelectorAll('.flip').forEach(function(f){f.addEventListener('click',function(){f.classList.toggle('on');});});
  // nav highlight
  var links=[].slice.call(document.querySelectorAll('.side a'));
  var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){var i=secs.indexOf(en.target);
    links.forEach(function(a,j){a.classList.toggle('on',j===i);});if(links[i]&&links[i].scrollIntoView&&innerWidth<1060){
      var nav=links[i].parentElement;nav.scrollTo({left:links[i].offsetLeft-40,behavior:'smooth'});}}});},{rootMargin:'-30% 0px -65% 0px'});
  secs.forEach(function(s){if(s)io.observe(s);});
})();
"""


if __name__ == "__main__":
    main()

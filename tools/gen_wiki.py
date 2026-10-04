#!/usr/bin/env python3
"""Build the illustrated French wiki of the mod: build/wiki/index.html + img/ + gif/.

Everything is read from the data tables and generated resources (lang files, guide pages, machines, metals,
talents, boss gear, biomes, structures, recipes, loot tables, quests, Java key bindings / commands / config),
so new content shows up by re-running the script. French explanations that the data does not carry live in
tools/wf/wiki_text.py.

Slow (3D renders): it is not part of generate_all.py. Renders are cached in build/wiki_cache, so a second run
only re-renders what changed. The world map, the biome renders and the real in-game screenshots
(wayfarers-shot-<name>.png, or a local folder in $WAYFARERS_SHOTS / build/shots) come from the CI pre-release.

Usage:
    python3 tools/gen_wiki.py                 # -> build/wiki/
    python3 tools/gen_wiki.py --jobs 4 --out /tmp/wiki --no-cache
    python3 tools/gen_wiki.py --worldmap DIR  # folder with wayfarers-worldmap{,-caves,-slice}.png and .txt
                                              # (and optionally wayfarers-biomes.txt + wayfarers-biome-<id>.png)
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
import types
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
RENDER_VERSION = "4"
WORLDMAP_URL = ("https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/"
                "wayfarers-worldmap{}")
PREVIEWS_URL = "https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/{}"
BIOME_CELL = (480, 360)  # one biome render in the packed sheets (the CI renders are 672 x 504)
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
        if path.endswith(".webp"):  # lossless: about 40 % lighter than the PNG, same pixels
            sheet.save(path, "WEBP", lossless=True, method=6)
        else:
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
            default = re.sub(r"^[A-Z]\w*\.(?=[A-Z_]+$)", "", default)  # HealthBars.DAMAGED -> DAMAGED
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


def wonders(guide, defs):
    """Wonder ids, in display order: TXT.WONDERS first, then every structure named in a "wonders*" manual page."""
    text = " ".join(e for pid, _c, _i, _t, paras, _it in guide.PAGES if pid.startswith("wonders") for e, _f in paras)
    out = [w for w in TXT.WONDERS if any(s.id == w for s in defs.STRUCTURES)]
    for s in defs.STRUCTURES:
        names = [n for n in (s.title_en, s.title_en.replace("The ", "")) if n]
        if s.id not in out and any(n in text for n in names):
            out.append(s.id)
    return out


def start_height(sid):
    """(min, max) absolute start height of a structure placed at a fixed height (underground, sky), else None."""
    d = load_json(os.path.join(DATA, "worldgen", "structure", sid + ".json"), {})
    h = d.get("start_height", {})
    try:
        return h["min_inclusive"]["absolute"], h["max_inclusive"]["absolute"]
    except (KeyError, TypeError):
        return None


def biome_spawns():
    """{entity id: [biome ids]} from the Forge biome modifiers that add spawns (tags resolved one level)."""
    out = {}
    for f in glob.glob(os.path.join(DATA, "forge", "biome_modifier", "*.json")):
        d = load_json(f, {})
        if not d.get("type", "").endswith("add_spawns"):
            continue
        biomes = d.get("biomes", [])
        biomes = [biomes] if isinstance(biomes, str) else biomes
        ids = []
        for b in biomes:
            if b.startswith("#"):
                ns, path = b[1:].split(":", 1)
                tag = load_json(os.path.join(RES, "data", ns, "tags", "worldgen", "biome", path + ".json"), {})
                ids += [v["id"] if isinstance(v, dict) else v for v in tag.get("values", [])]
            else:
                ids.append(b)
        sp = d.get("spawners", [])
        for s in ([sp] if isinstance(sp, dict) else sp):
            out.setdefault(s["type"], [])
            out[s["type"]] += [i for i in ids if i not in out[s["type"]]]
    return out


def biome_name(bid):
    ns, path = bid.split(":", 1) if ":" in bid else ("minecraft", bid)
    if ns == "wayfarers":
        return FR.get(f"biome.wayfarers.{path}", pretty(path))
    return vname("biome", path)


def new_ids_since(ref):
    """Lang keys (item/block/entity/structure) added since a git commit: {"item": [...], ...}. Empty without git."""
    import subprocess
    try:
        old = subprocess.run(["git", "-C", ROOT, "show", f"{ref}:src/main/resources/assets/wayfarers/lang/fr_fr.json"],
                             capture_output=True, timeout=20, check=True).stdout
        old = json.loads(old)
    except Exception as e:  # noqa: BLE001
        log(f"new since {ref}: {e}")
        return {}
    out = {}
    for k in FR:
        parts = k.split(".")
        if len(parts) == 3 and parts[1] == "wayfarers" and k not in old and parts[0] in ("item", "block", "entity", "structure"):
            out.setdefault(parts[0], []).append(parts[2])
    return out


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


SHELL_ROCK = UNDERGROUND_ROCK | {"mud", "smooth_basalt", "basalt", "blackstone", "amethyst_block", "budding_amethyst",
                                 "cobblestone", "mossy_cobblestone", "moss_block", "rooted_dirt", "dripstone_block",
                                 "magma_block", "packed_ice", "red_sand", "terracotta", "obsidian", "soul_sand",
                                 "soul_soil"}


def _is_rock(name):
    n = name.split(":")[-1]
    return n in SHELL_ROCK or n.endswith("_ore") or n == "raw_iron_block"


def cutaway(blocks, floor_y):
    """Underground structures carve their own cavern inside a thick shell of natural rock, so a plain render is a
    lump of stone. Remove that shell: every natural-rock block above the floor that is connected (through other
    rock) to the outside of the template, i.e. to the bounding box or to a position the template leaves to the
    world. The floor and what is under it stay, like a diorama base; built walls, statues and crystals stay."""
    if not blocks:
        return blocks
    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    zs = [p[2] for p in blocks]
    x0, x1, y1, z0, z1 = min(xs), max(xs), max(ys), min(zs), max(zs)
    rock = {p for p, b in blocks.items() if p[1] > floor_y and _is_rock(b[0])}
    nbrs = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    stack = []
    for p in rock:
        x, y, z = p
        if x in (x0, x1) or z in (z0, z1) or y == y1 or any((x + dx, y + dy, z + dz) not in blocks for dx, dy, dz in nbrs):
            stack.append(p)
    shell = set(stack)
    while stack:
        x, y, z = stack.pop()
        for dx, dy, dz in nbrs:
            q = (x + dx, y + dy, z + dz)
            if q in rock and q not in shell:
                shell.add(q)
                stack.append(q)
    # loose rock left floating once the shell is gone (ores, pebbles) goes too
    view = {p: b for p, b in blocks.items() if p not in shell}
    solid = {p for p, b in view.items() if b[0] not in ("minecraft:air", "minecraft:cave_air")}
    for p in [p for p in solid if p[1] > floor_y and _is_rock(view[p][0])]:
        x, y, z = p
        if not any((x + dx, y + dy, z + dz) in solid for dx, dy, dz in nbrs):
            del view[p]
    return view


def _nbt_str(v):
    return str(getattr(v, "value", v))


def _structure_blocks(sdef, piece, xray):
    from gen_structures import build_piece
    bp = build_piece(sdef, piece, start=piece in sdef.pieces)
    bp.resolve_shapes()
    size, blocks, _, (mx, my, mz) = bp.normalized()
    view = blocks
    if xray:
        view = cutaway(blocks, sdef.ground - my)
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
    # GIF frame side: wonders are shown big; small structures (the sea-floor wrecks...) get smaller frames, which
    # keeps the whole wiki under the artifact size budget without touching the slow turn
    foot = max(size[0], size[2])
    gif_side = 440 if wonder else 220 if foot <= 40 else 250 if foot <= 64 else 270
    key = sha(RENDER_VERSION, "s3", sid, wonder, xray, gif_side,
              repr(sorted((p, b[0], tuple(sorted((b[1] or {}).items()))) for p, b in view.items())))
    cdir = os.path.join(CACHE, "structures", sid + "-" + key)
    files = {"static": f"img/s/{sid}.webp", "gif": f"gif/s/{sid}.gif"}
    if wonder:
        files.update(cut=f"img/s/{sid}_cut.webp", back=f"img/s/{sid}_back.webp")
    if not (use_cache and all(os.path.exists(os.path.join(cdir, os.path.basename(f))) for f in files.values())):
        os.makedirs(cdir, exist_ok=True)
        tmp = os.path.join(cdir, "tmp.png")
        render3d.render(view, tmp, max_side=1100 if wonder else 860, bg=W.BG + (255,))
        Image.open(tmp).save(os.path.join(cdir, f"{sid}.webp"), quality=82, method=5)
        if wonder:
            render3d.render(view, tmp, max_side=1100, angle=2, bg=W.BG + (255,))
            Image.open(tmp).save(os.path.join(cdir, f"{sid}_back.webp"), quality=82, method=5)
            cut = sdef.ground - my + 2
            if xray:
                ys = sorted(p[1] for p in view)
                cut = ys[int(len(ys) * 0.55)]
            render3d.render(view, tmp, max_side=1100, max_y=cut, bg=W.BG + (255,))
            Image.open(tmp).save(os.path.join(cdir, f"{sid}_cut.webp"), quality=82, method=5)
        os.remove(tmp)
        frames = W.voxel_frames(view, n=24 if wonder else 20, size=gif_side)
        frames = W.crop_frames(frames)
        # a slow turntable (about 10 s per turn): faster spins were tiring to watch
        W.save_gif(frames, os.path.join(cdir, f"{sid}.gif"), ms=420 if wonder else 480)
    for f in files.values():
        dst = os.path.join(out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(cdir, os.path.basename(f)), dst)
    info["files"] = files
    return info


# camera pitch of the turntables (degrees above the horizon): long or flat sea creatures read better from above
MOB_PITCH = {"sea_serpent": 38, "manta_ray": 34, "whale": 22}


def mob_job(args):
    idx, out, use_cache = args
    from wf import mobs, wikirender as W, models, model_render
    builder = mobs.MODELS[idx]
    mod = sys.modules[builder.__module__]
    m = builder()
    name_ = m.name
    pitch = MOB_PITCH.get(name_, 12)
    key = sha(RENDER_VERSION, pitch, file_bytes(mod.__file__, models.__file__, model_render.__file__, W.__file__))
    cdir = os.path.join(CACHE, "mobs", name_ + "-" + key)
    if not (use_cache and os.path.exists(os.path.join(cdir, name_ + ".gif"))):
        m.pack()
        tex, glow = m.textures()
        os.makedirs(cdir, exist_ok=True)
        frames = W.mob_frames(m, tex, glow, n=24, size=260, pitch=pitch)
        W.save_gif(frames, os.path.join(cdir, name_ + ".gif"), ms=340)
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
        W.save_gif(frames, os.path.join(cdir, fname), ms=340, colors=224)
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


# =============================================================================================== biome renders
def parse_biomeshots_txt(path):
    """{biome: (kind, x, z, y0, y1)} for each biome the CI drew (lines of wayfarers-biomes.txt, /wayfarers biomeshots)."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        m = re.match(r"wayfarers:(\w+)\s+(surface|cave)\s+at\s+(-?\d+)\s+(-?\d+)\s+y\s+(-?\d+)\.\.(-?\d+)", line.strip())
        if m:
            out[m.group(1)] = (m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
    return out


def find_biomeshots(arg):
    """Folder holding wayfarers-biomes.txt and the wayfarers-biome-<id>.png renders: a local folder when given, else
    the CI pre-release (cached in build/wiki_cache/biomeshots, the legend re-checked every 3 hours). None if absent."""
    for d in (arg, os.environ.get("WAYFARERS_BIOMESHOTS", ""), os.path.join(ROOT, "build", "worldmap"),
              os.path.join(ROOT, "build", "biomeshots")):
        if d and os.path.exists(os.path.join(d, "wayfarers-biomes.txt")):
            return d
    d = os.path.join(CACHE, "biomeshots")
    os.makedirs(d, exist_ok=True)
    txt = os.path.join(d, "wayfarers-biomes.txt")
    if not os.path.exists(txt) or time.time() - os.path.getmtime(txt) > 3 * 3600:
        try:
            data = urllib.request.urlopen(PREVIEWS_URL.format("wayfarers-biomes.txt"), timeout=40).read()
            old = open(txt, "rb").read() if os.path.exists(txt) else None
            open(txt, "wb").write(data)
            if old != data:  # a new CI run: drop the old renders so they are fetched again
                for f in glob.glob(os.path.join(d, "wayfarers-biome-*.png")):
                    os.remove(f)
        except Exception as e:  # noqa: BLE001
            if not os.path.exists(txt):
                log(f"biome renders not available: {e}")
                return None
            os.utime(txt)
    got = 0
    for bid in parse_biomeshots_txt(txt):
        png = os.path.join(d, f"wayfarers-biome-{bid}.png")
        if not os.path.exists(png):
            try:
                data = urllib.request.urlopen(PREVIEWS_URL.format(f"wayfarers-biome-{bid}.png"), timeout=40).read()
                open(png, "wb").write(data)
            except Exception as e:  # noqa: BLE001
                log(f"biome render {bid} not available: {e}")
                continue
        got += 1
    log(f"biome renders: {got} available")
    return d


def biome_sheets(shot_dir, order, out):
    """Packs the renders of each group of biomes into one webp strip (img/biomes-<group>.webp), to keep the number
    of files down. order: {group: [biome ids in card order]}. Returns {biome: (file, index, count)}."""
    res = {}
    if not shot_dir:
        return res
    cdir = os.path.join(CACHE, "biomesheets")
    os.makedirs(cdir, exist_ok=True)
    cw, ch = BIOME_CELL
    for g, ids in order.items():
        pngs = [(b, os.path.join(shot_dir, f"wayfarers-biome-{b}.png")) for b in ids]
        pngs = [(b, p) for b, p in pngs if os.path.exists(p)]
        if not pngs:
            continue
        key = sha(RENDER_VERSION, cw, ch, *[b for b, _ in pngs], file_bytes(*[p for _, p in pngs]))
        cached = os.path.join(cdir, f"{g}-{key}.webp")
        if not os.path.exists(cached):
            sheet = Image.new("RGBA", (cw * len(pngs), ch), (0, 0, 0, 0))
            for k, (b, p) in enumerate(pngs):
                im = Image.open(p).convert("RGBA").convert("RGBa").resize((cw, ch), Image.LANCZOS).convert("RGBA")
                sheet.paste(im, (k * cw, 0))
            sheet.save(cached, "WEBP", quality=80, method=6)
        name_ = f"img/biomes-{g}.webp"
        shutil.copyfile(cached, os.path.join(out, name_))
        for k, (b, _) in enumerate(pngs):
            res[b] = (name_, k, len(pngs))
    return res


# =============================================================================================== in-game screenshots
SHOT_MAX_W = 960  # published width of the real client screenshots (1280 x 720 from the CI)
SHOT_REFRESH = 3 * 3600  # seconds between two checks of the same screenshot on the CI release


def find_ingame_shots(arg):
    """Folder holding the real client screenshots wayfarers-shot-<name>.png (tools/ci_client.py, CiDriver), and
    {name: date of the capture or ""}. A local folder when given, else the CI pre-release, cached in
    build/wiki_cache/ingame: each screenshot is fetched again when its copy is more than 3 hours old (kept when the
    release cannot be reached). Missing screenshots are skipped. (None, {}) when there is none."""
    names = [n for n, *_ in TXT.INGAME_SHOTS]
    for d in (arg, os.environ.get("WAYFARERS_SHOTS", ""), os.path.join(ROOT, "build", "shots")):
        if d and any(os.path.exists(os.path.join(d, f"wayfarers-shot-{n}.png")) for n in names):
            return d, {n: "" for n in names}
    d = os.path.join(CACHE, "ingame")
    os.makedirs(d, exist_ok=True)
    meta_path = os.path.join(d, "shots.json")
    meta = load_json(meta_path, {})
    got = 0
    for n in names:
        png = os.path.join(d, f"wayfarers-shot-{n}.png")
        m = meta.setdefault(n, {})
        if not os.path.exists(png) or time.time() - m.get("checked", 0) > SHOT_REFRESH:
            try:
                r = urllib.request.urlopen(PREVIEWS_URL.format(f"wayfarers-shot-{n}.png"), timeout=40)
                data = r.read()
                if data[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError("not a PNG")
                open(png, "wb").write(data)
                m["date"] = r.headers.get("Last-Modified", "")
            except Exception as e:  # noqa: BLE001
                if not os.path.exists(png):
                    log(f"in-game screenshot {n} not available: {e}")
            m["checked"] = time.time()
        if os.path.exists(png):
            got += 1
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    log(f"in-game screenshots: {got} of {len(names)} available")
    return (d, {n: meta.get(n, {}).get("date", "") for n in names}) if got else (None, {})


def ingame_images(shot_dir, out):
    """Converts each real screenshot to WebP (quality 80, at most SHOT_MAX_W wide) into img/jeu/<name>.webp; the
    WebP is cached by the PNG's bytes. Returns {name: (published path, width, height)}."""
    res = {}
    if not shot_dir:
        return res
    cdir = os.path.join(CACHE, "ingameweb")
    os.makedirs(cdir, exist_ok=True)
    os.makedirs(os.path.join(out, "img", "jeu"), exist_ok=True)
    for n, *_ in TXT.INGAME_SHOTS:
        png = os.path.join(shot_dir, f"wayfarers-shot-{n}.png")
        if not os.path.exists(png):
            continue
        cached = os.path.join(cdir, f"{n}-{sha(SHOT_MAX_W, file_bytes(png))}.webp")
        try:
            if not os.path.exists(cached):
                im = Image.open(png).convert("RGB")
                if im.width > SHOT_MAX_W:
                    im = im.resize((SHOT_MAX_W, round(im.height * SHOT_MAX_W / im.width)), Image.LANCZOS)
                im.save(cached, "WEBP", quality=80, method=6)
                for old in glob.glob(os.path.join(cdir, f"{n}-*.webp")):
                    if old != cached:
                        os.remove(old)
            w, h = Image.open(cached).size
        except Exception as e:  # noqa: BLE001
            log(f"in-game screenshot {n} unreadable: {e}")
            continue
        rel = f"img/jeu/{n}.webp"
        shutil.copyfile(cached, os.path.join(out, rel))
        res[n] = (rel, w, h)
    return res


def shot_date(dates):
    """The most recent capture date, in French ("" when unknown)."""
    from email.utils import parsedate_to_datetime
    best = None
    for v in dates.values():
        try:
            t = parsedate_to_datetime(v)
        except (TypeError, ValueError):
            continue
        best = t if best is None or t > best else best
    if not best:
        return ""
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
            "novembre", "décembre"]
    return f"{best.day} {mois[best.month - 1]} {best.year} à {best:%H:%M} UTC"


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
    wonder_ids = wonders(guide, defs)
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

    # where each creature lives (structures scan + structure spawn lists), and in which biomes it spawns
    lives = {}
    for s in defs.STRUCTURES:
        si = struct_info.get(s.id, {})
        for e in si.get("bosses", []) + si.get("spawners", []) + [sp[0] for sp in s.spawns]:
            lives.setdefault(e, [])
            if s.id not in lives[e]:
                lives[e].append(s.id)
    spawn_biomes = biome_spawns()

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
    def azerty(k):
        a = TXT.KEY_AZERTY.get(k)
        return f'<kbd class="az">{E(a)}</kbd>' if a else '<span class="same">idem</span>'
    keys = "".join(f'<tr><td><kbd>{E(k)}</kbd></td><td>{azerty(k)}</td><td>{E(v)}</td></tr>'
                   for k, v in java_keys())
    keys += f'<tr><td><kbd>Maj + H</kbd></td><td><span class="same">idem</span></td><td>{E(TXT.KEY_TEXT["Maj + H"])}</td></tr>'
    keys += f'<tr><td colspan="2"><kbd>Clic molette</kbd></td><td>{E(TXT.KEY_TEXT["Clic molette"])}</td></tr>'
    cmds = []
    for sub, a, subs, op in java_commands():
        who, text = TXT.COMMANDS.get(sub, ("op" if op else "tous", ""))
        usage = "/wayfarers " + sub + "".join(f" &lt;{E(x)}&gt;" for x in a) + (f" {'|'.join(subs)}" if subs else "")
        cmds.append(f'<tr><td><code>{usage}</code></td><td><span class="who {"op" if op else ""}">{"op" if op else "tous"}'
                    f'</span></td><td>{E(text)}</td></tr>')
        idx.add("/wayfarers " + sub, "Commande", "commandes", text)
    cfg = "".join(f'<tr id="cfg-{slug(k)}-{f.split("-")[1][:6]}"><td><code>{E(k)}</code></td><td><code>{E(d)}</code></td><td>{E(c)}<br><small>{E(f)}</small></td></tr>'
                  for k, d, c, f in java_config())
    hero = wonder_ids[0] if wonder_ids and wonder_ids[0] in struct_info else None
    hero_name = FR.get(f"structure.wayfarers.{hero}", "Une merveille du mod") if hero else ""
    sec.append(f'''
<section class="hero" id="accueil">
  <div class="hero-text">
    <span class="kicker">Minecraft 26.2 · Forge 65.1 · mod coopératif</span>
    <h1>Wayfarers</h1>
    <p class="lede">{E(TXT.TAGLINE)}</p>
    <ul class="stats">{"".join(f"<li><b>{n}</b><span>{E(l)}</span></li>" for n, l in stats)}</ul>
  </div>
  {f'<figure class="vitrine hero-fig"><img src="{struct_info[hero]["files"]["gif"]}" alt="{E(hero_name, quote=True)}, rotation à 360°" loading="eager"><figcaption>{E(hero_name)}</figcaption></figure>' if hero else ""}
</section>
<nav class="tiles" aria-label="Sections">__TILES__</nav>''')
    # biome groups and the real in-game biome renders (CI), used by the biome cards and the world-block cards
    inv = {}
    for v, o in B.VANILLA_TO_OURS.items():
        inv.setdefault(o, []).append(v)

    def biome_group(bid, b):
        src = inv.get(bid, [])
        if b["cave"] or bid in [c[0] for c in B.EXTRA_CAVES]:
            return "cave"
        if any(w in v for v in src for w in ("ocean", "beach", "river", "shore", "mushroom")):
            return "ocean"
        if b["temp"] < 0.3:
            return "cold"
        if b["temp"] >= 1.0:
            return "warm"
        return "temperate"

    shot_dir = find_biomeshots(args.worldmap)
    shots = parse_biomeshots_txt(os.path.join(shot_dir, "wayfarers-biomes.txt") if shot_dir else None)
    sheet_order = {}
    for bid, b in B.BIOMES.items():
        if bid in shots:
            sheet_order.setdefault(biome_group(bid, b), []).append(bid)
    sheets = biome_sheets(shot_dir, sheet_order, out)

    def biome_shot(bid, caption=True):
        """The biome's render (one cell of its group's strip), or "" when the CI render is missing."""
        if bid not in sheets:
            return ""
        b = B.BIOMES[bid]
        fname, k, n = sheets[bid]
        kind, sx_, sz_ = shots[bid][0], shots[bid][1], shots[bid][2]
        alt = f"{b['fr']} : rendu 3D d'un coin du biome généré en jeu" + (" (vue en écorché)" if kind == "cave" else "")
        where_ = f"x {sx_}, z {sz_}".replace("-", "−") + (" · écorché" if kind == "cave" else "")
        pos = k * 100 / (n - 1) if n > 1 else 0
        return (f'<div class="shot{" cave" if kind == "cave" else ""}"><i role="img" aria-label="{E(alt, quote=True)}" '
                f'style="background-image:url({fname});background-size:{n * 100}% 100%;'
                f'background-position:{pos:.4f}% 0"></i>{f"<small>{E(where_)}</small>" if caption else ""}</div>')

    gui = gui_images(out)
    shot_dir, shot_dates = find_ingame_shots(None)
    ingame = ingame_images(shot_dir, out)
    ctx = types.SimpleNamespace(atlas=atlas, idx=idx, item_link=item_link, by_result=by_result, mob_info=mob_info,
                                struct_info=struct_info, sheet_info=sheet_info, all_ids=all_ids, lives=lives,
                                gear=gear, weapon_of=weapon_of, remembrance_of=remembrance_of, defs=defs,
                                wonder_ids=wonder_ids, recipes=recipes, spawn_biomes=spawn_biomes,
                                biome_shot=biome_shot, gui=gui, biomes=B.BIOMES, shots=ingame, shot_dates=shot_dates)
    sec.append(section_news(ctx))
    sec.append(section_ingame(ctx))
    sec.append(section_tests(ctx))
    sec.append(f'''
<section class="block" id="commencer">
  {plaque("commencer-h", "La première heure", "Par où commencer", "Huit étapes, dans l'ordre, pour bien démarrer une partie à plusieurs.")}
  <ol class="steps">{"".join(steps)}</ol>
</section>
<section class="block two" id="touches">
  <div>{plaque("touches-h", "Clavier", "Les touches")}
  <table class="tbl keys"><thead><tr><th>QWERTY</th><th>AZERTY</th><th>Effet</th></tr></thead><tbody>{keys}</tbody></table>
  <p class="note">{E(TXT.KEYS_NOTE)}</p>
  {screen_fig(gui, "settings", "L'écran Réglages Wayfarers (Mods → Wayfarers → Config)", "reglages")}
  <p class="small">{E(TXT.SETTINGS_TEXT)}</p></div>
  <div id="commandes">{plaque("commandes-h", "Chat", "Les commandes")}
  <div class="scroll"><table class="tbl"><thead><tr><th>Commande</th><th>Qui</th><th>Effet</th></tr></thead><tbody>{"".join(cmds)}</tbody></table></div></div>
</section>
<section class="block" id="config">
  {plaque("config-h", "Réglages", "Options de configuration", "Dans le dossier <code>config/</code> de l'instance. Les options communes se règlent côté serveur, les options client chez chaque joueur.")}
  <div class="scroll"><table class="tbl"><thead><tr><th>Option</th><th>Défaut</th><th>Effet</th></tr></thead><tbody>{cfg}</tbody></table></div>
</section>''')
    sec.append(section_perf(ctx))

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
  {ingame_feature(ctx, "quest_journal")}
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
        shot = ingame_feature(ctx, "waystone") if cat == "travel" else ""
        mhtml.append(f'<h3 class="subhead">{atlas.icon(icon, 28)}{E(cfr)}</h3>{shot}<div class="grid pages">{"".join(cards)}</div>')
    qol = "".join(f'<article class="card mini"><h4>{E(t)}</h4><p>{E(x)}</p></article>' for t, x in TXT.QOL)
    for t, x in TXT.QOL:
        idx.add(t, "Confort", "confort", x)
    sec.append(f'''<section class="block" id="manuel">
  {plaque("manuel-h", "Le Manuel du Voyageur", "Chaque système, page par page", "Le texte du Manuel en jeu, avec les objets concernés. Clique sur un objet pour voir sa fiche et sa recette.")}
  {('<div class="ingame-pair">' + shot_fig(ctx, "manual_welcome") + shot_fig(ctx, "manual_machines") + '</div>') if any(n in ctx.shots for n in ("manual_welcome", "manual_machines")) else ""}
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
  {ingame_feature(ctx, "talent_tree")}
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
        screen = screen_fig(gui, MACHINE_SCREENS.get(mid, ""), f"L'écran de : {name(mid)}", cls="mscreen")
        mcards.append(f'''<article class="card machine" id="{anchor_item(mid)}x">
  <div class="mhead">{atlas.icon(mid, 64)}<h4>{E(name(mid))}</h4></div>
  <ul class="ticks">{lines}</ul>
  {screen}
  {render_recipe(atlas, rec[0], item_link) if rec else ""}
</article>''')
        idx.add(name(mid), "Machine", anchor_item(mid) + "x", " ".join(f for _e, f in m["desc"]))
    farm = ""
    for pid, icon, (ten, tfr), paras, items in machines.GUIDE:
        farm += f'<article class="card page"><h4>{atlas.icon(icon, 32)}{E(tfr)}</h4>{"".join(f"<p>{E(f)}</p>" for _e, f in paras)}</article>'
    sec.append(section_map(ctx))
    sec.append(f'''<section class="block" id="machines">
  {plaque("machines-h", "Système", "Machines simples", "Ni câble, ni énergie : chaque machine est un bloc qui fait une seule chose. Elles se fabriquent presque toutes avec du laiton.")}
  <div class="callout" id="ecrans-machines"><b>Nouveau : un écran pour chaque machine.</b> {E(TXT.MACHINE_SCREENS_INTRO)}</div>
  {ingame_feature(ctx, "machine_harvester")}
  <div class="grid machines">{"".join(mcards)}</div>
  <div class="grid pages">{farm}</div>
</section>''')
    sec.append(section_terminal(ctx))
    sec.append(section_gadgets(ctx))
    sec.append(section_construction(ctx))
    sec.append(section_automatons(ctx))

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

    # ================================================================== WORLD BLOCKS, DECOR + FURNITURE
    sec.append(section_worldblocks(ctx))
    dgroups ={"Guilde et régions": [], "Steampunk": [], "Pierres du nouveau monde": [], "Au burin seulement": []}
    steam = False
    chisel_only = set(getattr(decor, "CHISEL_ONLY", {}))
    from wf import worldblocks as WB
    world_stones = {s for base, forms in WB.STONE_SETS.items() for s in [base] + forms}
    for bid, d in decor.DECOR.items():
        if bid == "brass_plating":
            steam = True
        variants = [decor.variant_id(bid, v) for v in d["variants"]]
        g = ("Pierres du nouveau monde" if bid in world_stones else "Au burin seulement" if bid in chisel_only
             else "Steampunk" if steam else "Guilde et régions")
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
  {"".join(f'<h3 class="subhead">{E(g)}</h3>' + (f'<p class="note">{E(TXT.CHISEL_ONLY_TEXT)} <a href="#construction">Voir le burin</a>.</p>' if g == "Au burin seulement" else '<p class="note">Où les trouver et comment les fabriquer : <a href="#pierres">les pierres du nouveau monde</a>.</p>' if g == "Pierres du nouveau monde" else "") + f'<div class="grid decos">{"".join(v)}</div>' for g, v in dgroups.items() if v)}
  <h3 class="subhead">Meubles et blocs en 3D</h3>
  <div class="grid spins">{"".join(fcards)}</div>
</section>''')

    # ================================================================== HELD 3D
    hsheet = sheet_info.get("held")
    hcards = []
    new3d = new_held_ids(TXT.NEW_SINCE, hsheet["ids"]) if hsheet else set()
    if hsheet:
        for i, iid in enumerate(hsheet["ids"]):
            c, r = i % hsheet["cols"], i // hsheet["cols"]
            d_ = desc(iid)
            tag = '<span class="newtag">nouveau</span>' if iid in new3d else ""
            hcards.append(f'''<figure class="spin" id="{anchor_item(iid)}h"><div class="vitrine sprite" style="--w:{hsheet["cell"]}px;--sheet:url({hsheet["file"]});--cx:{c};--cy:{r};--cols:{hsheet["cols"]};--rows:{hsheet["rows"]}">{tag}</div>
  <figcaption><a href="#{anchor_item(iid)}">{atlas.icon(iid, 24)}<b>{E(name(iid))}</b></a>{f"<small>{E(d_[0])}</small>" if d_ else ""}</figcaption></figure>''')
            idx.add(name(iid), "Arme 3D", anchor_item(iid) + "h", " ".join(d_))
    bg_rows = []
    for row in bossgear.BOSS_GEAR:
        boss, tier, wid = row[0], row[1], row[2]
        bg_rows.append(f'<tr><td>{atlas.icon("wayfarers:" + boss, 32)} {E(name(boss))}</td><td>{atlas.icon(remembrance_of[boss], 32)}</td>'
                       f'<td><a href="#{anchor_item(wid)}">{atlas.icon(wid, 32)} {E(name(wid))}</a></td><td>{E(row[4][1])}</td></tr>')
    sec.append(f'''<section class="block" id="armes3d">
  {plaque("armes-h", "Équipement", "Armes, bâtons et outils en 3D", "Ces objets s'affichent en 3D quand on les tient en main (icône plate dans l'inventaire). Chaque arme spéciale a un pouvoir au clic droit, avec un temps de recharge.")}
  {f'<p class="callout"><b>Nouveau cette nuit :</b> {len(new3d)} objets passent en 3D (marqués « nouveau »), et beaucoup d’icônes ont été redessinées à la main : bâtons, marteaux, armures, sacs, outils… Elles sont partout dans ce wiki.</p>' if new3d else ""}
  <div class="grid spins">{"".join(hcards)}</div>
  <h3 class="subhead">Souvenirs de boss et armes forgées</h3>
  <p>Chaque grand boss lâche son Souvenir. Avec quatre matériaux de son palier et deux diamants, il devient une arme unique.</p>
  <div class="scroll"><table class="tbl gear"><thead><tr><th>Boss</th><th>Souvenir</th><th>Arme</th><th>Pouvoir</th></tr></thead><tbody>{"".join(bg_rows)}</tbody></table></div>
</section>''')

    # ================================================================== BESTIARY
    from wf import ocean as OC
    groups = {"boss": [], "champion": [], "creature": [], "sea": [], "companion": []}
    for mid in list(content.ENTITIES) + [m for m in mob_info if m not in content.ENTITIES]:
        if mid not in mob_info:
            continue
        st = entity_stats(mid)
        if st["hp"] is None and mid in TXT.MOB_HP:
            st["hp"] = TXT.MOB_HP[mid]
        kind = ("boss" if mid in gear else "champion" if st["boss"] else
                "companion" if mid in TXT.COMPANIONS else "sea" if mid in OC.ENTITIES else "creature")
        text = TXT.MOBS.get(mid) or st["doc"]
        badge = TXT.MOB_BADGE.get(mid) or {"boss": "Boss", "champion": "Champion de donjon", "creature": "Créature",
                                           "sea": "Créature marine", "companion": "Compagnon"}[kind]
        groups[kind].append(mob_card(ctx, mid, kind, badge, st, text))
        idx.add(name(mid), badge, f"b-{mid}", text)
    sec.append(section_oceans(ctx))
    sec.append(f'''<section class="block" id="bestiaire">
  {plaque("bestiaire-h", "Danger", "Bestiaire", "Toutes les créatures du mod, avec leur vrai modèle 3D. Les boss ont deux phases : à mi-vie ils rugissent puis changent de rythme. Chaque attaque est annoncée (animation ou cercle au sol) : observe, esquive, punis. Frapper fort et souvent brise leur posture (+50 % de dégâts). En coop, leur vie augmente de 60 % par joueur.")}
  {"".join(f'<h3 class="subhead" id="bestiaire-{k}">{t}</h3><div class="grid mobs">{"".join(groups[k])}</div>' for k, t in (("boss", "Les grands boss"), ("champion", "Les champions de donjon"), ("creature", "Les créatures"), ("sea", "Les créatures marines"), ("companion", "Les compagnons")) if groups[k])}
</section>''')

    # ================================================================== STRUCTURES
    def biome_label(b):
        if b.startswith("#"):
            t = b[1:].split(":")[-1].replace("is_", "")
            return {"forest": "forêts", "hill": "collines", "taiga": "taïgas", "ocean": "océans", "beach": "plages",
                    "mountain": "montagnes", "badlands": "badlands", "overworld": "partout sous terre",
                    "jungle": "jungles", "savanna": "savanes", "river": "rivières"}.get(t, t.replace("_", " ")).capitalize()
        return vname("biome", b.split(":")[-1]) if VFR else pretty(b)

    wcards, scards = [], {"overworld": [], "sea": [], "nether": [], "end": []}
    order = sorted(defs.STRUCTURES, key=lambda s: (wonder_ids.index(s.id) if s.id in wonder_ids else len(wonder_ids),
                                                   ["overworld", "nether", "end"].index(s.dimension)
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
        sh = start_height(s.id)
        if sh:
            facts.append(f"base vers y {sh[0]} à {sh[1]}".replace("-", "−"))
        under = s.step == "underground_structures"
        f = si["files"]
        common = f'''<p class="dim">{E(dim)}</p><p>{E(text.strip())}</p>
  <p class="where">{SVG["pin"]} {E(biomes_)}</p>
  <p class="facts">{"".join(f"<span>{E(x)}</span>" for x in facts)}</p>
  {('<div class="inhab"><small>Habitants</small><span class="chips">' + who_html + '</span></div>') if who else ""}
  {('<div class="drops"><small>Dans les coffres</small>' + chips(atlas, loot, 24, item_link) + '</div>') if loot else ""}'''
        if s.id in wonder_ids:
            wcards.append(f'''<article class="wonder" id="s-{s.id}">
  <figure class="vitrine big"><img src="{f["gif"]}" alt="{E(title, quote=True)}, rotation à 360°" loading="lazy"><figcaption>{"Rotation 360° · roche retirée" if under else "Rotation 360°"}</figcaption></figure>
  <div class="wonder-body"><span class="badge wb">Merveille</span><h3>{E(title)}</h3>{common}
  <div class="views">
    <figure class="vitrine"><img src="{f["static"]}" alt="{E(title, quote=True)}, vue détaillée" loading="lazy"><figcaption>Vue détaillée</figcaption></figure>
    <figure class="vitrine"><img src="{f["back"]}" alt="{E(title, quote=True)}, vue de l'autre côté" loading="lazy"><figcaption>De l'autre côté</figcaption></figure>
    <figure class="vitrine"><img src="{f["cut"]}" alt="{E(title, quote=True)}, vue en coupe" loading="lazy"><figcaption>En coupe</figcaption></figure>
  </div>{'<p class="note">Vues en écorché : la roche naturelle qui entoure la caverne est retirée pour montrer l’intérieur. En jeu, tout est enfoui.</p>' if under else ""}</div>
</article>''')
        else:
            grp = "sea" if s.heightmap.startswith("OCEAN") else s.dimension if s.dimension in scards else "overworld"
            scards[grp].append(f'''<article class="card struct" id="s-{s.id}">
  <div class="vitrine flip"><img src="{f["gif"]}" alt="{E(title, quote=True)}, rotation" loading="lazy"><img class="detail" src="{f["static"]}" alt="{E(title, quote=True)}, vue détaillée" loading="lazy">{'<span class="cutnote">roche retirée</span>' if under else ""}</div>
  <div class="struct-body"><h4>{E(title)}</h4>{common}</div>
</article>''')
        idx.add(title, "Structure", f"s-{s.id}", text + " " + biomes_)
    sec.append(f'''<section class="block" id="structures">
  {plaque("structures-h", "Exploration", "Structures et merveilles", "Elles n'apparaissent que dans les régions jamais générées : le plus simple est un nouveau monde. La boussole des structures (accroupi + clic droit pour choisir la cible) donne la distance et la direction. Survole ou touche une image pour passer de la rotation à la vue détaillée.")}
  <h3 class="subhead">Les merveilles du monde</h3>
  {ingame_feature(ctx, "mega_structure")}
  {"".join(wcards)}
  {"".join(f'<h3 class="subhead">{E(t)}</h3><div class="grid structs">{"".join(scards[k])}</div>' for k, t in (("overworld", "Surface et profondeurs"), ("sea", "Sous les mers"), ("nether", "Nether"), ("end", "End")) if scards[k])}
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
    bgroups = {k: [] for k, _ in TXT.BIOME_GROUPS}
    if sheets:
        map_html += ('\n  <p class="note">Chaque biome ci-dessous est dessiné bloc par bloc à partir d’un vrai coin de '
                     'monde de 80 × 80 blocs généré par le serveur de test (commande <code>/wayfarers biomeshots</code>) : '
                     'arbres, plantes, minerais et structures compris. Pour les grottes, la roche au-dessus du sol des '
                     'cavernes est retirée ; les coupes dans la roche sont plus sombres.</p>')
    for bid, b in B.BIOMES.items():
        src = inv.get(bid, [])
        g = biome_group(bid, b)
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
        # the mod's own creatures added by biome modifiers (sea life), first
        animals = [name(e) for e, bl in spawn_biomes.items()
                   if e.startswith("wayfarers:") and "wayfarers:" + bid in bl and name(e) not in animals] + animals
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
        shot_html = ctx.biome_shot(bid)
        bgroups[g].append(f'''<article class="biome" id="bi-{bid}">
  {shot_html}<div class="swatch">{swatch}</div>
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
    from wf import gadgets as GD
    gadget_ids = set(GD.GADGETS)
    tool_ids = {"chisel", "chisel_table", "builder_wand", "master_builder_wand"}
    automaton_ids = {"clockwork_heart", "brass_gear"}
    cats_order = [("Objets du voyageur", []), ("Gadgets à vapeur", []), ("Outils de construction", []),
                  ("Automates", []), ("Armes et magie", []), ("Armes de boss et souvenirs", []),
                  ("Armures", []), ("Métaux et minerais", []), ("Machines", []), ("Blocs de construction", []),
                  ("Meubles", []), ("Blocs spéciaux", [])]
    cat_map = dict(cats_order)
    for iid in entries:
        is_block = f"block.wayfarers.{iid}" in FR
        d_ = desc(iid)
        if iid in gadget_ids:
            c = "Gadgets à vapeur"
        elif iid in tool_ids:
            c = "Outils de construction"
        elif iid in automaton_ids:
            c = "Automates"
        elif iid in boss_ids:
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
  {"".join(f'<details class="cat" {"open" if i < 4 else ""}><summary><span>{E(c)}</span><small>{len(v)}</small></summary><div class="grid items">{"".join(v)}</div></details>' for i, (c, v) in enumerate(cats_order) if v)}
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
    present = re.findall(r'<section class="[^"]*" id="([\w-]+)"', "".join(sec))
    nav = [(a, SECTIONS[a][0]) for a in present if a in SECTIONS]
    for a in present:
        if a not in SECTIONS:
            log(f"section #{a} has no entry in SECTIONS: not in the menu")
    tiles = "".join(f'<a class="tile{" new" if a in NEW_SECTIONS else ""}" href="#{a}">{atlas.icon(SECTIONS[a][2], 40)}'
                    f'<span>{E(SECTIONS[a][1])}</span></a>' for a in present if a in SECTIONS and SECTIONS[a][1])
    sec = [s.replace("__TILES__", tiles) for s in sec]
    rows = atlas.save(os.path.join(out, "img", "atlas.webp"))
    page = render_page(sec, idx, rows, nav)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    files = [os.path.join(dp, f) for dp, _dn, fs in os.walk(out) for f in fs]
    total = sum(os.path.getsize(f) for f in files)
    log(f"wiki: {out}/index.html  {len(files)} files, {total / 1e6:.1f} MB, {time.time() - t0:.0f}s")


# =============================================================================================== shared cards
def spin_sprite(sheet, iid, link=False):
    """3D turntable cell of a sprite-sheet GIF (held items, furniture), or "" when the item is not on the sheet."""
    if not sheet or iid not in sheet["ids"]:
        return ""
    i = sheet["ids"].index(iid)
    return (f'<div class="vitrine sprite" style="--w:{sheet["cell"]}px;--sheet:url({sheet["file"]});--cx:{i % sheet["cols"]};'
            f'--cy:{i // sheet["cols"]};--cols:{sheet["cols"]};--rows:{sheet["rows"]}" role="img" '
            f'aria-label="{E(name(iid), quote=True)} en 3D"></div>')


def recipe_block(ctx, iid, label="Comment l'obtenir"):
    rec = ctx.by_result.get(iid if ":" in iid else "wayfarers:" + iid, [])
    if not rec:
        return ""
    r = rec[0]
    return (f'<div class="how-get"><small>{E(label)} · {E(TXT.RECIPE_TYPES.get(r["type"], r["type"].split(":")[-1]))}</small>'
            f'{render_recipe(ctx.atlas, r, ctx.item_link)}</div>')


def manual_paras(pid=None, item=None):
    """French paragraphs of a manual page, by id or by the first page listing an item."""
    from wf import guide
    for p, _cat, _icon, _t, paras, items in guide.PAGES:
        if (pid and p == pid) or (item and item in items):
            return [f for _e, f in paras]
    return []


def mob_where(ctx, mid):
    """HTML list of the structures and biomes a creature lives in."""
    parts = [f'<a href="#s-{w}">{E(FR.get("structure.wayfarers." + w, w))}</a>' for w in ctx.lives.get("wayfarers:" + mid, [])]
    for b in ctx.spawn_biomes.get("wayfarers:" + mid, []):
        bid = b.split(":")[-1]
        nm = E(biome_name(b))
        parts.append(f'<a href="#bi-{bid}">{nm}</a>' if b.startswith("wayfarers:") else nm)
    return ", ".join(parts)


def moves_table(mid):
    rows = TXT.BOSS_MOVES.get(mid, [])
    if not rows:
        return ""
    body = "".join(f'<tr><td><b>{E(n)}</b></td><td><span class="phase p{"2" if ph.strip() == "2" else "1"}">{E(ph)}</span></td>'
                   f'<td>{E(t)}</td></tr>' for n, ph, t in rows)
    return (f'<div class="scroll"><table class="tbl moves"><thead><tr><th>Attaque</th><th>Phase</th><th>À faire</th></tr>'
            f'</thead><tbody>{body}</tbody></table></div>')


def mob_card(ctx, mid, kind, badge, st, text):
    where_html = E(TXT.MOB_WHERE[mid]) if mid in TXT.MOB_WHERE else mob_where(ctx, mid)
    if not where_html and mid in TXT.COMPANIONS:
        where_html = '<a href="#golem">Se construit : voir Automates</a>'
    loot = top_loot([f"wayfarers:entities/{mid}"], 8)
    weapon = ""
    if mid in ctx.weapon_of:
        w = ctx.weapon_of[mid]
        weapon = f'<p class="small">Son Souvenir forge : <a href="#{anchor_item(w)}">{E(name(w))}</a>.</p>'
    moves = ""
    if mid in TXT.BOSS_MOVES:
        moves = (f'<details class="moves-box"><summary>Ses attaques, phase par phase</summary>'
                 f'<p class="small">{E(TXT.BOSS_FACTS.get(mid, ""))}</p>{moves_table(mid)}</details>')
    return f'''<article class="card mob {kind}" id="b-{mid}">
  <figure class="vitrine"><img src="{ctx.mob_info[mid]["gif"]}" alt="{E(name(mid), quote=True)} en rotation" width="260" height="260" loading="lazy"></figure>
  <div class="mob-body"><span class="badge {kind}">{badge}</span><h4>{E(name(mid))}</h4>
  <p class="statline"><span title="Points de vie">{SVG["heart"]}{fmt_num(st["hp"])} PV</span><span title="Dégâts au corps à corps">{SVG["sword"]}{fmt_num(st["dmg"])}</span></p>
  <p>{E(text)}</p>
  <p class="where">{SVG["pin"]}<span>{where_html or "—"}</span></p>
  {('<div class="drops"><small>Butin</small>' + chips(ctx.atlas, loot, 24, ctx.item_link) + '</div>') if loot else ""}
  {weapon}{moves}</div>
</article>'''


# =============================================================================================== new sections
def thumb(ctx, spec, label):
    kind, _, ref = spec.partition(":")
    if kind == "mob" and ref in ctx.mob_info:
        return f'<img src="{ctx.mob_info[ref]["gif"]}" alt="{E(label, quote=True)}" loading="lazy">'
    if kind == "struct" and ref in ctx.struct_info:
        return f'<img src="{ctx.struct_info[ref]["files"]["gif"]}" alt="{E(label, quote=True)}" loading="lazy">'
    if kind == "biome" and ctx.biome_shot(ref, caption=False):
        return ctx.biome_shot(ref, caption=False)
    if kind == "img" and ref in ctx.gui.values():
        return f'<img src="{ref}" alt="{E(label, quote=True)}" loading="lazy">'
    if kind == "items":
        ids = [i for i in ref.split(",") if i]
        size = 56 if len(ids) <= 2 else 44 if len(ids) <= 4 else 40
        return '<span class="icons">' + "".join(ctx.atlas.icon(i, size) for i in ids) + "</span>"
    return ""


def section_news(ctx):
    blocks, toc = [], []
    for gi, (gtitle, gtext, cards_) in enumerate(TXT.NEW_GROUPS):
        places = gtitle.startswith("Merveilles")
        out = []
        for ci, (title, text, anchor, spec) in enumerate(cards_):
            wide = " wide" if places and ci == 0 else ""
            out.append(f'''<a class="news-card{wide}" href="#{anchor}"><span class="news-thumb vitrine{" shotthumb" if spec.startswith("img:") else ""}">{thumb(ctx, spec, title)}</span>
  <span class="news-body"><b>{E(title)}</b><span>{E(text)}</span><em>Voir la section</em></span></a>''')
            ctx.idx.add(title, "Nouveauté", anchor, text)
        gid = f"nouv-{slug(gtitle)}"
        toc.append(f'<a href="#{gid}">{E(gtitle)}<small>{len(cards_)}</small></a>')
        blocks.append(f'<h3 class="subhead news-theme" id="{gid}"><span class="theme-n">{gi + 1}</span>{E(gtitle)}</h3>'
                      f'<p class="theme-lede">{E(gtext)}</p>'
                      f'<div class="news-grid{" places" if places else ""}">{"".join(out)}</div>')
    cards = f'<nav class="news-toc" aria-label="Thèmes de la nuit">{"".join(toc)}</nav>' + "".join(blocks)
    new = new_ids_since(TXT.NEW_SINCE)
    lists = []
    items = [i for i in new.get("item", []) + new.get("block", []) if not i.endswith("_spawn_egg")
             and not i.endswith(("_slab", "_stairs", "_wall"))]
    if items:
        lists.append(f'<div class="newlist"><small>Objets et blocs ({len(items)}, sans les escaliers et dalles)</small>'
                     f'{chips(ctx.atlas, ["wayfarers:" + i for i in items], 26, ctx.item_link)}</div>')
    mobs = [m for m in new.get("entity", []) if m in ctx.mob_info]
    if mobs:
        lists.append('<div class="newlist"><small>Créatures</small><span class="chips">' + "".join(
            f'<a class="chip" href="#b-{m}">{ctx.atlas.icon("wayfarers:" + m, 26)}<span>{E(name(m))}</span></a>' for m in mobs)
            + "</span></div>")
    structs = [s for s in new.get("structure", []) if s in ctx.struct_info]
    if structs:
        lists.append('<div class="newlist"><small>Structures</small><span class="chips">' + "".join(
            f'<a class="chip" href="#s-{s}">{ctx.atlas.icon("wayfarers:structure_compass", 26)}<span>{E(FR.get("structure.wayfarers." + s, s))}</span></a>'
            for s in structs) + "</span></div>")
    return f'''<section class="block news" id="nouveautes">
  {plaque("nouveautes-h", "Mise à jour de la nuit", TXT.NEW_TITLE, E(TXT.NEW_INTRO))}
  {cards}
  {('<details class="cat newall"><summary><span>Toute la liste des ajouts</span><small>' + str(len(items) + len(mobs) + len(structs)) + '</small></summary><div class="newlists">' + "".join(lists) + '</div></details>') if lists else ""}
</section>'''


def check_command(ctx, cmd, subs):
    """Warn about a test command that names an unknown sub-command, item, entity or structure."""
    parts = cmd.split()
    sids = {s.id for s in ctx.defs.STRUCTURES}
    if parts[0] == "/wayfarers":
        if len(parts) < 2 or parts[1] not in subs:
            log(f"test checklist: unknown command {cmd}")
        elif parts[1] in ("tp", "locate") and (len(parts) < 3 or parts[2] not in sids):
            log(f"test checklist: unknown structure in {cmd}")
        elif parts[1] == "boss" and (len(parts) < 3 or parts[2] not in ctx.gear):
            log(f"test checklist: unknown boss in {cmd}")
    for p in parts:
        if p.startswith("wayfarers:"):
            i = p.split(":", 1)[1]
            if parts[0] == "/give":
                ok = i in ctx.all_ids
            elif parts[0] == "/summon":
                ok = i in ctx.mob_info
            elif parts[:2] == ["/locate", "biome"]:
                ok = i in ctx.biomes
            else:
                ok = i in sids
            if not ok:
                log(f"test checklist: unknown id in {cmd}")


def section_tests(ctx):
    subs = {c[0] for c in java_commands()}
    items = []
    for n, (title, cmds, expect) in enumerate(TXT.TEST_CHECKLIST, 1):
        for c in cmds:
            check_command(ctx, c, subs)
        key = slug(title)
        items.append(f'''<li class="check" id="t-{key}"><label><input type="checkbox" data-k="{key}"><span class="box" aria-hidden="true"></span><b>{n}. {E(title)}</b></label>
  <div class="cmds">{"".join(f'<code class="cmd">{E(c)}</code>' for c in cmds)}</div>
  <p>{E(expect)}</p></li>''')
        ctx.idx.add(title, "Test", f"t-{key}", " ".join(cmds) + " " + expect)
    return f'''<section class="block" id="tester">
  {plaque("tester-h", "Check-list", "Tester en jeu", E(TXT.TEST_INTRO))}
  <ol class="checks">{"".join(items)}</ol>
  <p class="note">Les commandes <code>/wayfarers</code> demandent les droits d'opérateur (sauf atlas, waystones, sort et magnet). Clique une commande pour la sélectionner, puis copie-la.</p>
</section>'''


def section_gadgets(ctx):
    from wf import gadgets as GD
    held = ctx.sheet_info.get("held")
    cards = []
    # ammunition (an item that is only listed on another gadget's manual page) joins that gadget's card
    page_of = {p[1].split(":")[-1]: p for p in GD.PAGES}
    ammo = {}
    for gid in GD.GADGETS:
        if gid not in page_of:
            owner = next((p[1].split(":")[-1] for p in GD.PAGES if "wayfarers:" + gid in p[4]), None)
            if owner:
                ammo.setdefault(owner, []).append(gid)
    for gid, (_en, fr, _ten, tfr) in GD.GADGETS.items():
        if any(gid in v for v in ammo.values()):
            continue
        sprite = spin_sprite(held, gid)
        visual = sprite or f'<div class="vitrine big-icon">{ctx.atlas.icon(gid, 96)}</div>'
        paras = [f for _e, f in page_of[gid][3]] if gid in page_of else []
        tips = [TXT.GADGET_TIPS.get(g, "") for g in [gid] + ammo.get(gid, [])]
        extra = "".join(recipe_block(ctx, a, name(a)) for a in ammo.get(gid, []))
        summary = "" if paras else f'<p>{E(" ".join(tfr))}</p>'
        cards.append(f'''<article class="card gadget" id="g-{gid}">
  <div class="g-visual">{visual}</div>
  <div class="g-body"><h4>{ctx.atlas.icon(gid, 32)}{E(fr)}</h4>{summary}
  {('<div class="g-use"><small>Comment s’en servir</small>' + "".join(f"<p>{E(p)}</p>" for p in paras) + '</div>') if paras else ""}
  {f'<p class="tip"><b>Astuce :</b> {E(" ".join(t for t in tips if t))}</p>' if any(tips) else ""}
  {recipe_block(ctx, gid)}{extra}</div>
</article>''')
        for a in ammo.get(gid, []):
            ctx.idx.add(name(a), "Gadget", f"g-{gid}", " ".join(GD.GADGETS[a][3]))
        ctx.idx.add(fr, "Gadget", f"g-{gid}", " ".join(tfr + paras))
    return f'''<section class="block" id="gadgets">
  {plaque("gadgets-h", "Nouveau · laiton et vapeur", "Gadgets à vapeur", E(TXT.GADGETS_INTRO))}
  <div class="grid gadgets">{"".join(cards)}</div>
</section>'''


def sym_svg(mode):
    """Top view of the wand symmetry: your blocks in gold, mirrored copies in blue, the centre in amber."""
    c = 14
    mine = [(5, 1), (5, 2), (4, 1)]
    cells = []
    for x, z in mine:
        cells.append((x, z, "m"))
        if mode in ("x", "xz"):
            cells.append((6 - x, z, "b"))
        if mode in ("z", "xz"):
            cells.append((x, 6 - z, "b"))
        if mode == "xz":
            cells.append((6 - x, 6 - z, "b"))
    grid = "".join(f'<rect x="{i * c}" y="{j * c}" width="{c}" height="{c}" class="sg"/>' for i in range(7) for j in range(7))
    planes = ""
    if mode in ("x", "xz"):
        planes += f'<line x1="{3.5 * c}" y1="0" x2="{3.5 * c}" y2="{7 * c}" class="sp"/>'
    if mode in ("z", "xz"):
        planes += f'<line x1="0" y1="{3.5 * c}" x2="{7 * c}" y2="{3.5 * c}" class="sp"/>'
    blocks = "".join(f'<rect x="{x * c + 1}" y="{z * c + 1}" width="{c - 2}" height="{c - 2}" class="s{k}"/>' for x, z, k in cells)
    return (f'<svg viewBox="-2 -2 {7 * c + 4} {7 * c + 4}" role="img" aria-label="Vue du dessus">{grid}{planes}'
            f'<rect x="{3 * c + 3}" y="{3 * c + 3}" width="{c - 6}" height="{c - 6}" class="sc"/>{blocks}</svg>')


def section_construction(ctx):
    from wf import chisel as CH, decor
    atlas, held, furn = ctx.atlas, ctx.sheet_info.get("held"), ctx.sheet_info.get("furniture")

    def tool_card(iid, pid, anchor, extra=""):
        visual = spin_sprite(held, iid) or spin_sprite(furn, iid) or f'<div class="vitrine big-icon">{atlas.icon(iid, 96)}</div>'
        paras = manual_paras(pid=pid)
        ctx.idx.add(name(iid), "Construction", anchor, " ".join(paras))
        return f'''<article class="card tool" id="{anchor}">
  <div class="g-visual">{visual}</div>
  <div class="g-body"><h4>{atlas.icon(iid, 32)}{E(name(iid))}</h4>
  {"".join(f"<p>{E(p)}</p>" for p in paras)}{extra}
  {recipe_block(ctx, iid)}</div>
</article>'''

    full = {k: v for k, v in CH.FAMILIES.items() if not k.endswith(("_stairs", "_slabs", "_walls"))}
    n_shape = len(CH.FAMILIES) - len(full)
    fams = "".join(f'<li><span class="fam-icons">{"".join(atlas.icon(b, 30) for b in fam)}</span>'
                   f'<small>{E(name(fam[0]))} · {len(fam)} variantes</small></li>' for fam in full.values())
    only = []
    for bid in getattr(decor, "CHISEL_ONLY", {}):
        fam = next((f for f in CH.FAMILIES.values() if "wayfarers:" + bid in f), [])
        src = [b for b in fam if b.split(":")[1] not in decor.CHISEL_ONLY]
        only.append(f'<li><a href="#{anchor_item(bid)}">{atlas.icon(bid, 48)}</a><div><b>{E(name(bid))}</b>'
                    f'<small>depuis : {E(", ".join(name(b) for b in src[:3]))}</small></div></li>')
    sym_steps = manual_paras(pid="symmetry")
    modes = "".join(f'<figure class="sym">{sym_svg(m)}<figcaption><b>{E(t)}</b><span>{E(x)}</span></figcaption></figure>'
                    for m, t, x in TXT.SYMMETRY_MODES)
    wand_extra = f'<div class="chips">{chips(atlas, ["wayfarers:master_builder_wand"], 26, ctx.item_link)}</div>'
    return f'''<section class="block" id="construction">
  {plaque("construction-h", "Nouveau · outils de bâtisseur", "Burin, table de taille et baguette", E(TXT.CONSTRUCTION_INTRO))}
  <div class="grid tools">
    {tool_card("wayfarers:chisel", "chisel", "burin")}
    {tool_card("wayfarers:chisel_table", "chisel_table", "table-taille")}
  </div>
  <h3 class="subhead" id="burin-seul">{len(only)} blocs qu'on n'obtient qu'au burin</h3>
  <p>{E(TXT.CHISEL_ONLY_TEXT)}</p>
  <ul class="only">{"".join(only)}</ul>
  <details class="cat fams"><summary><span>Les {len(full)} familles du burin</span><small>+ {n_shape} familles d'escaliers, dalles et murets</small></summary>
  <p class="note">Dans l'ordre du burin : clic droit passe à l'icône suivante, accroupi revient à la précédente. Les familles sont des fichiers de données (<code>data/&lt;ns&gt;/chisel/*.json</code>) : un pack de données peut en ajouter.</p>
  <ul class="fam-list">{fams}</ul></details>
  <h3 class="subhead" id="baguette">La baguette du bâtisseur</h3>
  <div class="grid tools">{tool_card("wayfarers:builder_wand", "wand", "baguette-carte", wand_extra)}
  <article class="card sym-card" id="symetrie"><h4>{atlas.icon("wayfarers:master_builder_wand", 32)}La symétrie (touche <kbd>G</kbd>)</h4>
  <ol class="sym-steps">{"".join(f"<li>{E(re.sub(r'^[0-9]+[.] ', '', p))}</li>" for p in sym_steps)}</ol>
  <p class="tip"><b>Astuce :</b> pose le centre au milieu de ta future tour ou de ta façade, choisis X + Z, puis construis un seul quart : les trois autres se posent tout seuls.</p></article></div>
  <div class="sym-grid">{modes}</div>
  <p class="note">Vue du dessus : le carré ambré est le centre du miroir, en doré les blocs que tu poses, en bleu les copies. Chaque copie coûte un bloc ; les copies à plus de 96 blocs sont ignorées ; annuler (accroupi dans le vide) retire tout.</p>
</section>'''


def section_automatons(ctx):
    atlas = ctx.atlas
    gst = entity_stats("brass_golem")
    golem_gif = ctx.mob_info.get("brass_golem", {}).get("gif", "")
    steps = []
    for n, (t, x) in enumerate(TXT.GOLEM_STEPS, 1):
        extra = ""
        if n == 1:
            extra = recipe_block(ctx, "wayfarers:clockwork_heart", "Recette") + recipe_block(ctx, "wayfarers:brass_gear", "L'engrenage")
        elif n == 2:
            extra = recipe_block(ctx, "wayfarers:brass_block", "Recette")
        steps.append(f'<li class="step"><span class="num">{n}</span><div><h4>{E(t)}</h4><p>{E(x)}</p>{extra}</div></li>')
    orders = "".join(f'<li><b>{E(t)}</b><span>{E(x)}</span></li>' for t, x in TXT.GOLEM_ORDERS)
    foes = []
    for mid in ("clockwork_spider", "steam_drone"):
        if mid not in ctx.mob_info:
            continue
        st = entity_stats(mid)
        foes.append(f'''<article class="card foe"><figure class="vitrine"><img src="{ctx.mob_info[mid]["gif"]}" alt="{E(name(mid), quote=True)} en rotation" loading="lazy"></figure>
  <div><h4><a href="#b-{mid}">{E(name(mid))}</a></h4>
  <p class="statline"><span>{SVG["heart"]}{fmt_num(st["hp"])} PV</span><span>{SVG["sword"]}{fmt_num(st["dmg"])}</span></p>
  <p>{E(TXT.MOBS.get(mid, st["doc"]))}</p><p class="where">{SVG["pin"]}<span>{mob_where(ctx, mid)}</span></p></div></article>''')
    boss = "grand_clockmaker"
    boss_html = ""
    if boss in ctx.mob_info:
        bst = entity_stats(boss)
        lair = "".join(f'<li><b>{E(t)}</b><span>{E(x)}</span></li>' for t, x in TXT.LAIRS.get(boss, []))
        loot = top_loot([f"wayfarers:entities/{boss}"], 8)
        weapon = ctx.weapon_of.get(boss)
        boss_html = f'''<h3 class="subhead" id="horloger">Le Grand Horloger, boss de la Citadelle</h3>
  <div class="bossbox">
    <figure class="vitrine boss-fig"><img src="{ctx.mob_info[boss]["gif"]}" alt="Le Grand Horloger en rotation" loading="lazy"><figcaption>4,4 blocs de haut</figcaption></figure>
    <div class="boss-body">
      <p class="statline"><span>{SVG["heart"]}{fmt_num(bst["hp"])} PV</span><span>{SVG["sword"]}{fmt_num(bst["dmg"])}</span></p>
      <p>{E(TXT.MOBS.get(boss, ""))} {E(TXT.BOSS_FACTS.get(boss, ""))}</p>
      <h4>La descente vers son repaire</h4>
      <ol class="lair">{lair}</ol>
      {('<div class="drops"><small>Il lâche</small>' + chips(atlas, loot, 24, ctx.item_link) + '</div>') if loot else ""}
      {f'<p class="small">Son Souvenir se forge (4 matériaux de palier + 2 diamants) en <a href="#{anchor_item(weapon)}">{E(name(weapon))}</a> : {E(desc(weapon)[0] if desc(weapon) else "")}</p>' if weapon else ""}
    </div>
  </div>
  <h4 class="movehead">Ses attaques</h4>
  {moves_table(boss)}'''
        ctx.idx.add("Le Grand Horloger : attaques et repaire", "Boss", "horloger", " ".join(t for t, _p, _x in TXT.BOSS_MOVES.get(boss, [])))
    ctx.idx.add("Construire le golem de laiton", "Automate", "golem", " ".join(x for _t, x in TXT.GOLEM_STEPS))
    return f'''<section class="block" id="automates">
  {plaque("automates-h", "Nouveau · mécanique vivante", "Automates", E(TXT.AUTOMATONS_INTRO))}
  {ingame_feature(ctx, "creatures")}
  <h3 class="subhead" id="golem">Le golem de laiton, ton compagnon</h3>
  <div class="golem">
    <figure class="vitrine golem-fig"><img src="{golem_gif}" alt="Le golem de laiton en rotation" loading="lazy"><figcaption>{fmt_num(gst["hp"])} PV · coup de {fmt_num(gst["dmg"])}</figcaption></figure>
    <div><h4 class="minihead">Le construire en 3 étapes</h4><ol class="steps golem-steps">{"".join(steps)}</ol></div>
  </div>
  <h4 class="minihead">Ses ordres</h4>
  <ul class="orders">{orders}</ul>
  <h3 class="subhead">Les automates ennemis</h3>
  <div class="grid foes">{"".join(foes)}</div>
  {boss_html}
</section>'''


# =============================================================================================== screens (gen_gui mockups)
# machine id -> mockup name (tools/gen_gui.py --mockup draws them with the real GUI sprites, in French)
MACHINE_SCREENS = {"auto_harvester": "machine_harvester", "sprinkler": "machine_sprinkler",
                   "vacuum_hopper": "machine_vacuum", "block_breaker": "machine_breaker",
                   "block_placer": "machine_placer", "redstone_timer": "machine_timer",
                   "wireless_transmitter": "machine_transmitter", "wireless_receiver": "machine_receiver",
                   "entity_detector": "machine_detector"}
GUI_SHOTS = ["worldmap", "minimap", "settings"] + list(MACHINE_SCREENS.values())
PREVIEW_GUI = os.path.join(ROOT, "build", "previews", "gui")
_GUI_SIZE = {}


def gui_images(out):
    """Copies the GUI mockups into img/gui/ as lossless WebP (about a third of the PNG). Runs gen_gui.py --mockup
    when they are missing. Returns {mockup name: published path}."""
    if any(not os.path.exists(os.path.join(PREVIEW_GUI, n + ".png")) for n in GUI_SHOTS):
        import subprocess
        log("GUI mockups missing: running tools/gen_gui.py --mockup")
        try:
            subprocess.run([sys.executable, os.path.join(TOOLS, "gen_gui.py"), "--mockup"], check=True,
                           capture_output=True, timeout=600)
        except Exception as e:  # noqa: BLE001
            log(f"gen_gui.py --mockup failed: {e}")
    os.makedirs(os.path.join(out, "img", "gui"), exist_ok=True)
    res = {}
    for n in GUI_SHOTS:
        src = os.path.join(PREVIEW_GUI, n + ".png")
        if not os.path.exists(src):
            log(f"GUI mockup {n}.png not found: its image is left out")
            continue
        rel = f"img/gui/{n}.webp"
        im = Image.open(src).convert("RGB")
        im.save(os.path.join(out, rel), "WEBP", lossless=True, method=6)
        _GUI_SIZE[rel] = im.size
        res[n] = rel
    return res


def screen_fig(gui, key, caption, anchor=None, cls=""):
    """<figure> of one GUI mockup, or "" when it is missing."""
    rel = gui.get(key)
    if not rel:
        return ""
    w, h = _GUI_SIZE.get(rel, (0, 0))
    aid = f' id="{anchor}"' if anchor else ""
    return (f'<figure class="screen {cls}"{aid}><img src="{rel}" alt="{E(caption, quote=True)}" width="{w}" height="{h}" '
            f'loading="lazy"><figcaption>{E(caption)}</figcaption></figure>')


INGAME = {n: (t, x, a) for n, t, x, a in TXT.INGAME_SHOTS}


def shot_fig(ctx, n, caption=None, cls="", tag=True, eager=False):
    """<figure> of one real in-game screenshot (opens large on click), or "" when the CI did not publish it."""
    if n not in ctx.shots:
        return ""
    rel, w, h = ctx.shots[n]
    t, x, _a = INGAME[n]
    cap = caption if caption is not None else f"{t} : {x}"
    alt = f"Capture en jeu · {t} : {x}"
    return (f'<figure class="screen ingame {cls}">{"<span class=livetag>Capture en jeu</span>" if tag else ""}'
            f'<img src="{rel}" alt="{E(alt, quote=True)}" width="{w}" height="{h}" tabindex="0" '
            f'loading="{"eager" if eager else "lazy"}">'
            f'{f"<figcaption>{cap}</figcaption>" if cap else ""}</figure>')


def ingame_feature(ctx, n, anchor=None):
    """A real screenshot beside a short note on what it shows, for the top of a section. "" when it is missing."""
    fig = shot_fig(ctx, n, caption="", tag=True)
    if not fig:
        return ""
    t, x, _a = INGAME[n]
    aid = f' id="{anchor}"' if anchor else ""
    return (f'<div class="ingame-row"{aid}>{fig}<div class="ingame-note"><span class="kicker">Vu en jeu</span>'
            f'<h4>{E(t)}</h4><p>{E(x)}</p><p class="small">Vraie capture du client de test, prise toute seule à chaque '
            f'compilation (jeu en anglais). <a href="#en-jeu">Toutes les captures</a>.</p></div></div>')


def section_ingame(ctx):
    if not ctx.shots:
        return ""
    figs = []
    for k, (n, t, x, a) in enumerate(TXT.INGAME_SHOTS):
        if n not in ctx.shots:
            continue
        cap = (f'<b>{E(t)}</b><span>{E(x)}</span>'
               + (f'<a href="#{a}">Voir la section</a>' if a else ""))
        figs.append(shot_fig(ctx, n, caption=cap, cls="lead" if not figs else "", tag=False, eager=k < 3))
        ctx.idx.add(f"En jeu : {t}", "Capture", "en-jeu", x)
    when = shot_date(ctx.shot_dates)
    return f'''<section class="block ingame-sec" id="en-jeu">
  {plaque("en-jeu-h", "Captures réelles · serveur de test", TXT.INGAME_TITLE, E(TXT.INGAME_INTRO))}
  <div class="gallery">{"".join(figs)}</div>
  <p class="note">{E(TXT.INGAME_NOTE)}{f" Dernières captures : {E(when)}." if when else ""}</p>
</section>'''


def new_held_ids(ref, ids):
    """Items whose 3D in-hand model is new since a git commit (their item definition had no display-context
    switch then). Empty without git."""
    import subprocess
    try:
        subprocess.run(["git", "-C", ROOT, "rev-parse", ref], capture_output=True, timeout=20, check=True)
    except Exception:  # noqa: BLE001
        return set()
    out = set()
    for i in ids:
        r = subprocess.run(["git", "-C", ROOT, "show", f"{ref}:src/main/resources/assets/wayfarers/items/{i}.json"],
                           capture_output=True, timeout=20)
        if r.returncode != 0 or b"display_context" not in r.stdout:
            out.add(i)
    return out


def azerty_kbd(k):
    a = TXT.KEY_AZERTY.get(k)
    return f'<kbd>{E(k)}</kbd>' + (f'<small class="az">AZERTY <kbd>{E(a)}</kbd></small>' if a else "")


# =============================================================================================== tonight's sections
def section_map(ctx):
    atlas, gui = ctx.atlas, ctx.gui
    what = "".join(f'<div class="map-what"><h4>{E(t)}</h4><p>{E(x)}</p></div>' for t, x in TXT.MAP_WHAT)
    keyrow = "".join(f'<li>{azerty_kbd(k)}<span>{E(TXT.KEY_TEXT[k])}</span></li>' for k in ("M", "H", "Z", "B"))
    controls = "".join(f'<tr><td><b>{E(g)}</b></td><td>{E(x)}</td></tr>' for g, x in TXT.MAP_CONTROLS)
    feats = "".join(f'<article class="card feat" id="{a}"><h4>{atlas.icon(ic, 32)}{E(t)}</h4><p>{E(x)}</p></article>'
                    for a, t, x, ic in TXT.MAP_FEATURES)
    opts = [(k, d, c, f) for k, d, c, f in java_config() if k.startswith("map.")]
    orows = "".join(f'<tr><td><code>{E(k)}</code></td><td><code>{E(d)}</code></td><td>{E(c)}<br><small>{E(f)}</small></td></tr>'
                    for k, d, c, f in opts)
    for a, t, x, _ic in TXT.MAP_FEATURES:
        ctx.idx.add(t, "Carte", a, x)
    ctx.idx.add("Carte du monde", "Carte", "carte", " ".join(x for _t, x in TXT.MAP_WHAT))
    ctx.idx.add("Mini-carte", "Carte", "mini-carte", " ".join(TXT.MINIMAP_TEXT))
    return f'''<section class="block" id="carte">
  {plaque("carte-h", "Nouveau · se repérer", "Carte du monde et mini-carte", E(TXT.MAP_INTRO))}
  <div class="map-hero">
    {shot_fig(ctx, "world_map", cls="big") or screen_fig(gui, "worldmap", "La carte du monde : un repère partagé ouvert, la légende et tes repères à droite", cls="big")}
    <div class="map-side">{what}</div>
  </div>
  <ul class="keyrow">{keyrow}</ul>
  <div class="grid feats">{feats}</div>
  <h3 class="subhead" id="mini-carte">La mini-carte</h3>
  <div class="mini-row"><div>{shot_fig(ctx, "hud_minimap")}{screen_fig(gui, "minimap", "Maquette : le hublot rond (par défaut) et le cadre carré" if "hud_minimap" in ctx.shots else "Le hublot rond (par défaut) et le cadre carré")}</div>
    <div>{"".join(f"<p>{E(p)}</p>" for p in TXT.MINIMAP_TEXT)}
    <h4 class="minihead">Sur l'écran de la carte</h4>
    <div class="scroll"><table class="tbl ctl"><tbody>{controls}</tbody></table></div></div>
  </div>
  <details class="cat opts"><summary><span>Les options de la carte</span><small>{len(opts)}</small></summary>
  <div class="scroll pad"><table class="tbl"><thead><tr><th>Option</th><th>Défaut</th><th>Effet</th></tr></thead><tbody>{orows}</tbody></table></div></details>
</section>'''


def reach_svg():
    """Top view of a Guild Terminal network: the terminal's 48-block square, a chain of two relays (32 each), linked
    chests in gold and out-of-reach chests in grey. Drawn in block units around the terminal."""
    s, x0, y0 = 1.6, 82.0, 96.0  # px per block, terminal position in px

    def P(bx, bz):
        return x0 + bx * s, y0 + bz * s
    relays = [(44, -10), (74, 12)]
    sq = ['<rect class="rt" x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" rx="3"/>'.format(*P(-48, -48), 96 * s, 96 * s)]
    for bx, bz in relays:
        sq.append('<rect class="rr" x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" rx="3"/>'.format(
            *P(bx - 32, bz - 32), 64 * s, 64 * s))
    pts = [P(0, 0)] + [P(*r) for r in relays]
    links = "".join(f'<line class="rl" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>'
                    for a, b in zip(pts, pts[1:]))
    chests = [(-30, -24, 1), (-20, 30, 1), (18, 22, 1), (60, -30, 1), (96, 30, 1), (100, -6, 1),
              (144, -26, 0), (152, 24, 0)]
    ch = "".join('<rect class="{}" x="{:.1f}" y="{:.1f}" width="9" height="9" rx="1"/>'.format(
        "cl" if on else "co", P(bx, bz)[0] - 4.5, P(bx, bz)[1] - 4.5) for bx, bz, on in chests)
    nodes = ('<rect class="tm" x="{:.1f}" y="{:.1f}" width="16" height="16" rx="2"/>'.format(x0 - 8, y0 - 8)
             + "".join(f'<circle class="rn" cx="{x:.1f}" cy="{y:.1f}" r="6"/>' for x, y in pts[1:]))
    tl = P(-48, -48)
    rx, ry = P(relays[1][0], relays[1][1] + 32)
    ox, oy = P(149, 0)
    labels = (f'<text x="{x0:.1f}" y="{y0 + 24:.1f}" text-anchor="middle">Terminal</text>'
              f'<text x="{tl[0] + 6:.1f}" y="{tl[1] + 14:.1f}">48 blocs</text>'
              f'<text x="{rx:.1f}" y="{ry + 12:.1f}" text-anchor="middle">relais · 32 blocs</text>'
              f'<text x="{ox:.1f}" y="{oy + 4:.1f}" text-anchor="middle">hors de portée</text>')
    w, h = P(149, 0)[0] + 48, P(0, 48)[1] + 22
    return (f'<svg class="reach" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Portée du terminal et des relais, '
            f'vue du dessus">{"".join(sq)}{links}{ch}{nodes}{labels}</svg>')


def section_terminal(ctx):
    atlas = ctx.atlas

    def card(iid, pid, anchor):
        paras = manual_paras(pid=pid)
        ctx.idx.add(name(iid), "Rangement", anchor, " ".join(paras))
        return f'''<article class="card tool" id="{anchor}">
  <div class="g-visual"><div class="vitrine big-icon">{atlas.icon(iid, 96)}</div></div>
  <div class="g-body"><h4>{atlas.icon(iid, 32)}{E(name(iid))}</h4>
  {"".join(f"<p>{E(p)}</p>" for p in paras)}
  {recipe_block(ctx, iid)}</div>
</article>'''
    network = manual_paras(pid="terminal_network")
    ctx.idx.add("Réseau du terminal : exclure un coffre, Montrer", "Rangement", "terminal-reseau", " ".join(network))
    return f'''<section class="block" id="terminal">
  {plaque("terminal-h", "Nouveau · rangement", "Le terminal de guilde, pour toute la base", E(TXT.TERMINAL_INTRO))}
  {ingame_feature(ctx, "guild_terminal")}
  <div class="grid tools">
    {card("wayfarers:guild_terminal", "guild_terminal", "terminal-carte")}
    {card("wayfarers:storage_relay", "storage_relay", "relais")}
  </div>
  <div class="reach-row" id="terminal-reseau">
    <figure class="reach-fig">{reach_svg()}<figcaption>{E(TXT.TERMINAL_DIAGRAM)}</figcaption></figure>
    <div class="card"><h4>{atlas.icon("wayfarers:guild_terminal", 32)}Réseau, tri et exclusions</h4>
    {"".join(f"<p>{E(p)}</p>" for p in network)}
    <p class="small">Portées réglables côté serveur : <a href="#performances">options storage.*</a>.</p></div>
  </div>
</section>'''


def section_oceans(ctx):
    from wf import ocean as OC
    atlas = ctx.atlas
    faune = []
    for mid in OC.ENTITIES:
        if mid not in ctx.mob_info:
            continue
        st = entity_stats(mid)
        hp = st["hp"] if st["hp"] is not None else TXT.MOB_HP.get(mid)
        dmg = f'<span>{SVG["sword"]}{fmt_num(st["dmg"])}</span>' if st["dmg"] else ""
        faune.append(f'''<article class="card foe"><figure class="vitrine"><img src="{ctx.mob_info[mid]["gif"]}" alt="{E(name(mid), quote=True)} en rotation" loading="lazy"></figure>
  <div><h4><a href="#b-{mid}">{E(name(mid))}</a></h4>
  <p class="statline"><span>{SVG["heart"]}{fmt_num(hp)} PV</span>{dmg}</p>
  <p>{E(TXT.MOBS.get(mid, st["doc"]))}</p><p class="where">{SVG["pin"]}<span>{E(TXT.MOB_WHERE.get(mid, ""))}</span></p></div></article>''')
    floor = "".join(f'''<article class="floor">{atlas.icon(ic, 48)}<div><b>{E(t)}</b><span>{E(x)}</span><small>{SVG["pin"]}{E(w)}</small></div></article>'''
                    for t, x, ic, w in TXT.OCEAN_FLOOR)
    for t, x, _ic, _w in TXT.OCEAN_FLOOR:
        ctx.idx.add(t, "Océans", "fonds-marins", x)
    wrecks = []
    for sid in TXT.OCEAN_STRUCTS:
        si = ctx.struct_info.get(sid)
        if not si:
            continue
        title = FR.get(f"structure.wayfarers.{sid}", sid)
        sx, sy, sz = si["size"]
        loot = top_loot(si["loot"], 6)
        wrecks.append(f'''<article class="card wreck"><a class="vitrine" href="#s-{sid}"><img src="{si["files"]["gif"]}" alt="{E(title, quote=True)}, rotation" loading="lazy"></a>
  <div class="struct-body"><h4><a href="#s-{sid}">{E(title)}</a></h4><p>{E(TXT.STRUCTURES.get(sid, ""))}</p>
  <p class="facts"><span>{sx} × {sy} × {sz} blocs</span></p>
  {('<div class="drops"><small>Dans les coffres</small>' + chips(atlas, loot, 24, ctx.item_link) + '</div>') if loot else ""}</div></article>''')
    gear = []
    for iid, text in TXT.DIVING_TEXT.items():
        recs = ctx.by_result.get("wayfarers:" + iid, [])
        rh = "".join(f'<div class="how-get"><small>{"Recette" if k == 0 else "Ou bien"} · {E(TXT.RECIPE_TYPES.get(r["type"], ""))}</small>'
                     f'{render_recipe(atlas, r, ctx.item_link)}</div>' for k, r in enumerate(recs))
        gear.append(f'''<article class="card tool" id="g-{iid}">
  <div class="g-visual"><div class="vitrine big-icon">{atlas.icon(iid, 96)}</div></div>
  <div class="g-body"><h4>{atlas.icon(iid, 32)}{E(name(iid))}</h4><p>{E(text)}</p>{rh}</div></article>''')
        ctx.idx.add(name(iid), "Plongée", "plongee", text)
    extras = []
    for res, label in (("wayfarers:jelly_lamp", "Lampe de gelée (gelée des méduses)"),
                       ("minecraft:emerald", "Quatre perles = une émeraude")):
        r = next((r for r in ctx.recipes if r["result"] == res and r["file"] in ("jelly_lamp", "emerald_from_pearls")), None)
        if r:
            extras.append(f'<div class="card mini"><h4>{E(label)}</h4>{render_recipe(atlas, r, ctx.item_link)}</div>')
    ctx.idx.add("Océans vivants", "Océans", "oceans", TXT.OCEANS_INTRO + " " + TXT.OCEANS_WHERE)
    return f'''<section class="block" id="oceans">
  {plaque("oceans-h", "Nouveau · sous la surface", "Océans vivants", E(TXT.OCEANS_INTRO))}
  <div class="callout"><b>Où ?</b> {E(TXT.OCEANS_WHERE)}</div>
  <h3 class="subhead" id="oceans-faune">Qui vit sous l'eau</h3>
  <div class="grid foes">{"".join(faune)}</div>
  <h3 class="subhead" id="fonds-marins">Les fonds marins</h3>
  <div class="grid floors">{floor}</div>
  <h3 class="subhead" id="epaves">Épaves et refuges</h3>
  <p>Quatre petites structures posées sur le fond, chacune avec son coffre. La boussole des structures les trouve ; touche une image pour voir sa fiche complète.</p>
  <div class="grid wrecks">{"".join(wrecks)}</div>
  <h3 class="subhead" id="plongee">Équipement de plongée</h3>
  <div class="grid tools">{"".join(gear)}</div>
  <div class="grid minis extras">{"".join(extras)}</div>
</section>'''


def section_worldblocks(ctx):
    from wf import worldblocks as WB
    atlas = ctx.atlas

    def where(biomes):
        return ", ".join(f'<a href="#bi-{b}">{E(biome_name("wayfarers:" + b))}</a>' for b in biomes if b in ctx.biomes)

    def shot(biomes):
        for b in biomes:
            h = ctx.biome_shot(b, caption=False)
            if h:
                return h.replace('<div class="shot', '<div class="shot wbshot', 1) + f'<span class="shotcap">{E(biome_name("wayfarers:" + b))}</span>'
        return ""
    woods = []
    for w, (biomes, text) in TXT.WOODS.items():
        if w not in WB.WOODS:
            continue
        ids = list(WB.ids(w))
        fr = WB.WOODS[w]["fr"]
        sap = f"{w}_sapling"
        woods.append(f'''<article class="card wb" id="bois-{w}">
  <div class="wb-shot">{shot(biomes)}</div>
  <div class="wb-body"><h4>{atlas.icon(w + "_log", 36)}{E(fr[0].upper() + fr[1:])}</h4><p>{E(text)}</p>
  <p class="where">{SVG["pin"]}<span>{where(biomes)}</span></p>
  <div class="wb-icons">{"".join(f'<a href="#{anchor_item(i)}">{atlas.icon(i, 40)}</a>' for i in ids)}</div>
  {recipe_block(ctx, sap, "Sans nouveau monde : la pousse")}</div>
</article>''')
        ctx.idx.add(fr.capitalize(), "Bois", f"bois-{w}", text)
    stones = []
    for base, (biomes, text) in TXT.STONES.items():
        forms = [base] + WB.STONE_SETS.get(base, [])
        stones.append(f'''<article class="card wb" id="pierre-{base}">
  <div class="wb-shot">{shot(biomes)}</div>
  <div class="wb-body"><h4>{atlas.icon(base, 36)}{E(name(base))}</h4><p>{E(text)}</p>
  <p class="where">{SVG["pin"]}<span>{where(biomes)}</span></p>
  <div class="wb-icons">{"".join(f'<a href="#{anchor_item(i)}d">{atlas.icon(i, 40)}</a>' for i in forms)}</div>
  {recipe_block(ctx, base, "Sans nouveau monde")}</div>
</article>''')
        ctx.idx.add(name(base), "Pierre", f"pierre-{base}", text)
    return f'''<section class="block" id="blocs-monde">
  {plaque("blocs-monde-h", "Nouveau · matériaux", "Bois et pierres du nouveau monde", E(TXT.WORLDBLOCKS_INTRO))}
  <h3 class="subhead" id="bois">Deux bois</h3>
  <p>{E(TXT.WOOD_HOW)}</p>
  <div class="grid wbs">{"".join(woods)}</div>
  <h3 class="subhead" id="pierres">Trois pierres</h3>
  <p>{E(TXT.STONE_HOW)}</p>
  <div class="grid wbs three">{"".join(stones)}</div>
</section>'''


def section_perf(ctx):
    cfg = {k: (d, f) for k, d, _c, f in java_config()}
    cards = "".join(f'<article class="card perf"><h4>{E(t)}</h4><ul class="ticks">{"".join(f"<li>{E(p)}</li>" for p in pts)}</ul></article>'
                    for t, pts in TXT.PERF_POINTS)
    rows = "".join(f'<tr><td><code>{E(k)}</code></td><td><code>{E(cfg.get(k, ("?", ""))[0])}</code></td><td>{E(x)}'
                   f'<br><small>{E(cfg.get(k, ("", ""))[1])}</small></td></tr>' for k, x in TXT.PERF_OPTIONS)
    ctx.idx.add("Serveur et performances", "Serveur", "performances", " ".join(p for _t, pts in TXT.PERF_POINTS for p in pts))
    return f'''<section class="block" id="performances">
  {plaque("perf-h", "Nouveau · serveur", "Serveur et performances", E(TXT.PERF_INTRO))}
  <div class="grid perfs">{cards}</div>
  <h3 class="subhead">Les options utiles</h3>
  <div class="scroll"><table class="tbl"><thead><tr><th>Option</th><th>Défaut</th><th>À quoi elle sert</th></tr></thead><tbody>{rows}</tbody></table></div>
  <p class="note">Toutes les options : <a href="#config">Options de configuration</a>.</p>
</section>'''


# =============================================================================================== recipes
TAG_ICON ={"planks": "minecraft:oak_planks", "logs": "minecraft:oak_log", "wool": "minecraft:white_wool",
            "stone_tool_materials": "minecraft:cobblestone", "stone_crafting_materials": "minecraft:cobblestone",
            "coals": "minecraft:coal", "wooden_slabs": "minecraft:oak_slab", "sand": "minecraft:sand",
            "candles": "minecraft:candle", "leaves": "minecraft:oak_leaves", "saplings": "minecraft:oak_sapling",
            "copper_ores": "minecraft:copper_ore", "iron_ores": "minecraft:iron_ore", "chests": "minecraft:chest"}


def tag_icon(tag):
    """A readable item for an item tag: a known vanilla stand-in, else the first value of the tag file."""
    ns, path = tag.split(":", 1) if ":" in tag else ("minecraft", tag)
    rep = TAG_ICON.get(path.split("/")[-1]) if ns in ("minecraft", "c") else None
    if rep:
        return rep
    d = load_json(os.path.join(RES, "data", ns, "tags", "item", path + ".json")) or {}
    for v in d.get("values", []):
        v = v["id"] if isinstance(v, dict) else v
        return tag_icon(v[1:]) if v.startswith("#") else v
    return None


def slot(atlas, ids, item_link, count=None):
    if not ids:
        return '<span class="slot"></span>'
    i = ids[0]
    if i.startswith("#"):
        tag = i[1:].split(":")[-1].split("/")[-1]
        rep = tag_icon(i[1:])
        label = f"n'importe quel(le) {tag.replace('_', ' ')}"
        inner = atlas.icon(rep, 32, label=label) if rep else f'<i class="ic ic-none" style="--s:32px" title="{E(label, quote=True)}">#</i>'
        return f'<span class="slot tag" title="{E(label, quote=True)}">{inner}</span>'
    if ":" not in i:
        i = "minecraft:" + i
    a = item_link(i)
    c = f'<b class="count">{count}</b>' if count and count > 1 else ""
    inner = atlas.icon(i, 32) + c
    return f'<a class="slot" href="#{a}">{inner}</a>' if a else f'<span class="slot">{inner}</span>'


def placed_pattern(pattern, size=3):
    """A shaped pattern as the 3x3 crafting grid shows it: the game trims empty rows and columns
    (ShapedRecipePattern), then the recipe book centres a pattern narrower or shorter than half the grid
    (PlaceRecipeHelper: a 1-wide pattern goes in the middle column, a 1-high one in the middle row) and puts the
    rest in the top-left corner."""
    rows = [r for r in pattern if r.strip()]
    if not rows:
        return [" " * size] * size
    width = max(len(r) for r in rows)
    rows = [r.ljust(width) for r in rows]
    cols = [c for c in range(width) if any(r[c] != " " for r in rows)]
    rows = [r[cols[0]:cols[-1] + 1] for r in rows]
    h, w = len(rows), len(rows[0])
    top = (size - h) // 2 if h < size / 2 else 0
    left = (size - w) // 2 if w < size / 2 else 0
    grid = [[" "] * size for _ in range(size)]
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            grid[top + y][left + x] = ch
    return ["".join(r) for r in grid]


def render_recipe(atlas, r, item_link):
    d, t = r["data"], r["type"]
    res = slot(atlas, [r["result"]], item_link, r["count"])
    arrow = '<span class="arrow" aria-hidden="true"></span>'
    if t.endswith("crafting_shaped"):
        grid = placed_pattern(d["pattern"])
        cells = [slot(atlas, ingredient_ids(d["key"].get(ch)) if ch != " " else [], item_link) for row in grid for ch in row]
        return f'<div class="recipe"><div class="grid3">{"".join(cells)}</div>{arrow}{res}</div>'
    if t.endswith(("crafting_shapeless", "crafting_transmute")):
        ings = d.get("ingredients") or [d.get("input"), d.get("material")]
        cells = [slot(atlas, ingredient_ids(x), item_link) for x in ings] + ['<span class="slot"></span>'] * (9 - len(ings))
        note = '<small class="rnote">le contenu est gardé</small>' if t.endswith("transmute") else ""
        return f'<div class="recipe"><div class="grid3">{"".join(cells[:9])}</div>{arrow}{res}{note}</div>'
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


# Top-level sections: anchor -> (menu label, tile label or None, tile icon). Menu and tiles list the sections the
# page really has, in page order.
SECTIONS = {
    "accueil": ("Accueil", None, None),
    "nouveautes": ("Nouveautés de la nuit", "Nouveautés", "wayfarers:pocket_watch"),
    "en-jeu": ("En jeu (captures)", "En jeu", "minecraft:spyglass"),
    "tester": ("Tester en jeu", "Tester en jeu", "minecraft:command_block"),
    "commencer": ("Par où commencer", None, None),
    "touches": ("Touches & commandes", None, None),
    "config": ("Configuration", None, None),
    "performances": ("Serveur & performances", None, None),
    "quetes": ("Quêtes", "Quêtes", "wayfarers:wayfarer_atlas"),
    "manuel": ("Le Manuel", "Le Manuel", "wayfarers:wayfarer_manual"),
    "talents": ("Talents & magie", "Talents & magie", "wayfarers:fire_staff"),
    "carte": ("Carte & mini-carte", "Carte du monde", "minecraft:filled_map"),
    "machines": ("Machines", "Machines", "wayfarers:auto_harvester"),
    "terminal": ("Terminal de guilde", "Terminal de guilde", "wayfarers:guild_terminal"),
    "gadgets": ("Gadgets à vapeur", "Gadgets à vapeur", "wayfarers:grappling_hook"),
    "construction": ("Burin & baguette", "Construction", "wayfarers:chisel"),
    "automates": ("Automates", "Automates", "wayfarers:clockwork_heart"),
    "metaux": ("Métaux & armures", "Métaux & armures", "wayfarers:brass_ingot"),
    "blocs-monde": ("Bois & pierres", "Bois & pierres", "wayfarers:glowwood_log"),
    "deco": ("Déco & meubles", "Déco steampunk", "wayfarers:gear_panel"),
    "armes3d": ("Armes en 3D", "Armes en 3D", "wayfarers:bell_hammer"),
    "oceans": ("Océans vivants", "Océans vivants", "wayfarers:diving_helmet"),
    "bestiaire": ("Bestiaire", "Bestiaire", "minecraft:skeleton_skull"),
    "structures": ("Structures", "Structures", "wayfarers:structure_compass"),
    "monde": ("Nouveau Monde", "Nouveau Monde", "minecraft:grass_block"),
    "objets": ("Tous les objets", "Tous les objets", "wayfarers:travel_backpack"),
    "recettes": ("Recettes", "Recettes", "minecraft:crafting_table"),
}


# sections marked with a dot in the menu and the tiles (what changed tonight)
NEW_SECTIONS = {"nouveautes", "en-jeu", "tester", "carte", "terminal", "oceans", "blocs-monde", "performances"}


def render_page(sections, idx, atlas_rows, nav):
    nav_html = "".join(f'<a href="#{a}"{" class=new" if a in NEW_SECTIONS else ""}>{E(t)}</a>' for a, t in nav)
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
  --sky-a:#d3e3ec;--sky-b:#f1eadb;--deep-a:#3b3631;--deep-b:#1f1c19;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#121416;--paper-2:#181b1e;--card:#1d2024;--card-2:#23272c;--ink:#ece2cc;--ink-2:#b9ab90;--ink-3:#8c8068;
  --rule:#3b352a;--brass:#d6a64b;--brass-hi:#f0c977;--brass-lo:#8a6320;--verd:#62bba7;--verd-2:#1d3530;
  --rust:#d77452;--case:#181b1f;--case-rim:#4a4030;--link:#7fcfbd;--shadow:0 2px 14px rgba(0,0,0,.45);
  --plate-ink:#22180a;--kbd:#2a2e33;--chip:#262a2f;--focus:#f0c977;
  --sky-a:#22313b;--sky-b:#1d2024;--deep-a:#141416;--deep-b:#0c0c0e;color-scheme:dark}}
:root[data-theme="dark"]{
  --paper:#121416;--paper-2:#181b1e;--card:#1d2024;--card-2:#23272c;--ink:#ece2cc;--ink-2:#b9ab90;--ink-3:#8c8068;
  --rule:#3b352a;--brass:#d6a64b;--brass-hi:#f0c977;--brass-lo:#8a6320;--verd:#62bba7;--verd-2:#1d3530;
  --rust:#d77452;--case:#181b1f;--case-rim:#4a4030;--link:#7fcfbd;--shadow:0 2px 14px rgba(0,0,0,.45);
  --plate-ink:#22180a;--kbd:#2a2e33;--chip:#262a2f;--focus:#f0c977;
  --sky-a:#22313b;--sky-b:#1d2024;--deep-a:#141416;--deep-b:#0c0c0e;color-scheme:dark}
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
  background-image:url(img/atlas.webp);background-repeat:no-repeat;
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
.shot{position:relative;aspect-ratio:4/3;background:linear-gradient(var(--sky-a),var(--sky-b))}
.shot.cave{background:linear-gradient(var(--deep-a),var(--deep-b))}
.shot i{position:absolute;inset:0;background-repeat:no-repeat}
.shot small{position:absolute;right:8px;bottom:6px;padding:1px 7px;border-radius:4px;background:var(--card);color:var(--ink-3);font:600 11px "Pixelify Sans",monospace;opacity:.92}
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
/* new tonight */
.side a.new,.tile.new{position:relative}
.side a.new::after{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--rust);margin-left:7px;vertical-align:middle}
.tile.new{border-color:var(--brass);background:linear-gradient(160deg,var(--card),var(--card-2))}
.news-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px}
.news-card{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--rule);border-radius:10px;overflow:hidden;
  color:var(--ink);text-decoration:none;box-shadow:var(--shadow);transition:transform .15s,border-color .15s;min-width:0}
.news-card:hover{transform:translateY(-2px);border-color:var(--brass)}
.news-thumb{aspect-ratio:16/9;border-radius:0;border-width:0 0 3px}
.news-thumb img{position:absolute;inset:6px;width:calc(100% - 12px);height:calc(100% - 12px);object-fit:contain}
.news-grid.places{grid-template-columns:repeat(4,minmax(0,1fr))}
.news-grid.places .wide{grid-column:span 2}
.news-grid.places .wide .news-thumb{aspect-ratio:auto;height:0;flex:1 1 auto;min-height:160px}
.news-grid.places .wide .news-body b{font-size:22px}
@media (max-width:1060px){.news-grid.places{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:760px){.news-grid.places{grid-template-columns:minmax(0,1fr)}.news-grid.places .wide{grid-column:auto}}
.news-thumb .icons{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;padding:10px;max-width:92%}
.news-body{display:flex;flex-direction:column;gap:4px;padding:10px 14px 12px;flex:1}
.news-body b{font:700 18px/1.2 "Zilla Slab",serif}
.news-body span{font-size:15px;color:var(--ink-2)}
.news-body em{margin-top:auto;padding-top:4px;font:600 12px "Pixelify Sans",monospace;font-style:normal;text-transform:uppercase;color:var(--link)}
.newall{margin-top:14px}.newlists{padding:0 16px 14px}.newlist{margin:6px 0 10px}
.newlist small{display:block;font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--ink-3)}
/* test checklist */
.checks{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:10px}
.check{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:12px 14px;box-shadow:var(--shadow);min-width:0}
.check label{display:flex;align-items:center;gap:10px;cursor:pointer;font:700 17px/1.2 "Zilla Slab",serif}
.check input{position:absolute;opacity:0;width:1px;height:1px}
.check .box{flex:none;width:22px;height:22px;border-radius:5px;border:2px solid var(--brass);background:var(--card-2);display:grid;place-items:center}
.check input:checked + .box{background:var(--verd);border-color:var(--verd)}
.check input:checked + .box::after{content:"";width:6px;height:11px;border:solid #fff;border-width:0 3px 3px 0;transform:rotate(45deg) translate(-1px,-1px)}
.check input:focus-visible + .box{outline:2px solid var(--focus);outline-offset:2px}
.check.done{opacity:.62}.check.done b{text-decoration:line-through;text-decoration-color:var(--verd)}
.cmds{display:flex;flex-direction:column;gap:4px;margin:8px 0 6px}
.cmd{display:block;user-select:all;-webkit-user-select:all;cursor:text;padding:4px 8px;background:var(--case);color:#e9d9ae;border-color:var(--case-rim);font-size:13.5px;overflow-wrap:anywhere}
.check p{margin:0;font-size:15px;color:var(--ink-2)}
/* gadgets, tools */
.gadgets,.tools{grid-template-columns:repeat(auto-fill,minmax(min(100%,460px),1fr))}
.gadget,.tool{display:grid;grid-template-columns:150px minmax(0,1fr);gap:16px;align-items:start}
.g-visual .vitrine{aspect-ratio:1/1;width:100%}
.big-icon .ic{image-rendering:pixelated}
.g-body h4{margin-bottom:6px}
.g-use small,.how-get small{display:block;font:600 11px "Pixelify Sans",monospace;text-transform:uppercase;color:var(--ink-3);margin-top:8px}
.g-use p{margin:2px 0 6px;font-size:15.5px}
.tip{padding:7px 10px;background:var(--verd-2);border-radius:6px;font-size:15px}
.how-get{margin-top:8px}.how-get .recipe{margin-top:4px}
.only{list-style:none;padding:0;margin:8px 0 14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}
.only li{display:flex;gap:10px;align-items:center;background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px}
.only b{display:block;line-height:1.2}.only small{display:block;color:var(--ink-3);font-size:13px}
.fams > p,.fam-list{margin-left:16px;margin-right:16px}
.fam-list{list-style:none;padding:0 0 14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px 14px}
.fam-list li{min-width:0}.fam-icons{display:flex;flex-wrap:wrap;gap:2px}.fam-list small{color:var(--ink-3);font-size:13px}
.sym-steps{margin:0 0 12px;padding-left:22px;max-width:80ch}.sym-steps li{margin:4px 0}
.sym-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.sym{margin:0;background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:10px;display:flex;flex-direction:column;gap:6px;min-width:0}
.sym svg{width:100%;max-width:150px;align-self:center}
.sym figcaption b{display:block;font:700 16px "Zilla Slab",serif}.sym figcaption span{font-size:14px;color:var(--ink-2)}
.sg{fill:var(--card-2);stroke:var(--rule);stroke-width:1}
.sp{stroke:var(--rust);stroke-width:2;stroke-dasharray:4 3}
.sc{fill:#e8a33a;stroke:#7a4e10;stroke-width:1}
.sm{fill:#e4b75a;stroke:#6e4b12;stroke-width:1}
.sb{fill:#58a6e0;stroke:#1f5f8f;stroke-width:1}
/* automatons */
.golem{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:20px;align-items:start}
.golem-fig,.boss-fig{aspect-ratio:1/1}.golem-fig img,.boss-fig img,.foe img{width:100%;height:100%;object-fit:contain}
.golem-steps{grid-template-columns:minmax(0,1fr)}
.minihead{font:700 19px "Zilla Slab",serif;margin:14px 0 8px}
.orders{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px}
.orders li{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--brass);border-radius:8px;padding:8px 12px}
.orders b{display:block}.orders span{font-size:15px;color:var(--ink-2)}
.foes{grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr))}
.foe{display:grid;grid-template-columns:140px minmax(0,1fr);gap:14px;align-items:start}
.foe .vitrine{aspect-ratio:1/1}.foe h4 a{color:var(--ink)}
.bossbox{display:grid;grid-template-columns:minmax(0,340px) minmax(0,1fr);gap:22px;background:var(--card);border:1px solid var(--rule);border-top:4px solid var(--rust);
  border-radius:12px;padding:16px;box-shadow:var(--shadow)}
.boss-body h4{font:700 19px "Zilla Slab",serif;margin:12px 0 6px}
.lair{list-style:none;counter-reset:l;padding:0;margin:0;border-left:3px solid var(--brass);margin-left:10px}
.lair li{counter-increment:l;position:relative;padding:4px 0 10px 22px}
.lair li::before{content:counter(l);position:absolute;left:-13px;top:4px;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;
  font:700 12px "Pixelify Sans",monospace;color:#2a1d08;background:radial-gradient(circle at 35% 30%,#f6d98e,#b98a2e 70%)}
.lair b{display:block}.lair span{font-size:15px;color:var(--ink-2)}
.movehead{font:700 19px "Zilla Slab",serif;margin:16px 0 8px}
.moves td:first-child{white-space:nowrap}
.phase{font:600 11px "Pixelify Sans",monospace;padding:1px 6px;border-radius:4px;white-space:nowrap;background:var(--chip);color:var(--ink-2)}
.phase.p2{background:var(--rust);color:#fff4e6}
.moves-box{margin-top:8px;border-top:1px dashed var(--rule);padding-top:6px}
.moves-box summary{cursor:pointer;font-weight:700;color:var(--link)}
.moves-box .tbl{font-size:14px}
.cutnote{position:absolute;right:8px;bottom:6px;z-index:2;font:600 11px "Pixelify Sans",monospace;color:#d8c69c;background:rgba(0,0,0,.55);padding:2px 7px;border-radius:4px}
.hero-fig figcaption{left:auto;right:8px}
/* tonight: keys, news themes */
.tbl.keys{table-layout:fixed}
.tbl.keys td:first-child{width:auto;white-space:nowrap}.tbl.keys td:nth-child(2){white-space:nowrap}
.tbl.keys th:nth-child(1){width:84px}.tbl.keys th:nth-child(2){width:78px}
.tbl.keys td{overflow-wrap:anywhere}
.same{font-size:13px;color:var(--ink-3)}
.tile.new::after{content:"";width:7px;height:7px;border-radius:50%;background:var(--rust);margin-left:auto;flex:none}
.news-toc{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}
.news-toc a{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border:1px solid var(--rule);border-radius:999px;
  background:var(--card);color:var(--ink);text-decoration:none;font-weight:600;font-size:15px}
.news-toc a small{font:600 11px "Pixelify Sans",monospace;color:var(--ink-3)}
.news-toc a:hover{border-color:var(--brass)}
.news-theme{margin-top:26px}
.theme-n{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;flex:none;font:700 15px "Pixelify Sans",monospace;
  color:#2a1d08;background:radial-gradient(circle at 35% 30%,#f6d98e,#b98a2e 70%)}
.theme-lede{margin:-6px 0 12px;color:var(--ink-2)}
.news-thumb .shot{position:absolute;inset:0;aspect-ratio:auto}
.news-thumb .shot i{inset:0 auto;left:50%;height:100%;aspect-ratio:4/3;transform:translateX(-50%)}
.news-thumb.shotthumb img{inset:0;width:100%;height:100%;object-fit:cover;object-position:top left;image-rendering:auto}
.newtag{position:absolute;right:6px;top:6px;z-index:3;font:700 10px "Pixelify Sans",monospace;text-transform:uppercase;letter-spacing:.05em;
  padding:1px 6px;border-radius:4px;background:var(--rust);color:#fff4e6}
/* screens (GUI mockups) */
.screen{margin:12px 0 0;min-width:0}
.screen img{display:block;width:100%;height:auto;border-radius:8px;border:2px solid var(--case-rim);box-shadow:0 4px 14px rgba(0,0,0,.2);background:var(--case)}
.screen figcaption{font-size:14px;color:var(--ink-3);padding-top:6px}
.screen img{cursor:zoom-in}
.lightbox{position:fixed;inset:0;z-index:100;background:rgba(10,8,6,.9);display:grid;place-items:center;padding:16px;cursor:zoom-out}
.lightbox[hidden]{display:none}
.lightbox figure{margin:0;max-width:100%}
.lightbox img{display:block;max-width:100%;max-height:calc(100vh - 90px);margin:0 auto;border-radius:6px}
.lightbox figcaption{color:#efe3c8;margin-top:8px;text-align:center;font-size:15px}
.mscreen{margin:10px 0 4px}
.mscreen img{max-height:330px;width:auto;max-width:100%}
/* real in-game screenshots (CI client) */
.ingame{position:relative}
.ingame img{aspect-ratio:16/9;object-fit:cover;border-color:var(--brass-lo)}
.livetag{position:absolute;left:10px;top:10px;z-index:2;pointer-events:none;display:inline-flex;align-items:center;gap:6px;
  font:700 11px/1 "Pixelify Sans",monospace;letter-spacing:.06em;text-transform:uppercase;color:#f6e7c2;
  background:rgba(20,16,12,.78);border:1px solid rgba(228,183,90,.6);border-radius:4px;padding:4px 7px}
.livetag::before{content:"";width:7px;height:7px;border-radius:50%;background:#d9563a;box-shadow:0 0 0 2px rgba(217,86,58,.3)}
.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:0 0 6px}
.gallery .screen{margin:0;display:flex;flex-direction:column;background:var(--card);border:1px solid var(--rule);border-radius:10px;
  padding:8px;box-shadow:var(--shadow)}
.gallery .screen img{border-radius:6px}
.gallery .lead{grid-column:span 2;grid-row:span 2}
.gallery .lead img{flex:1;min-height:0;object-position:left center}
.gallery figcaption{display:flex;flex-direction:column;gap:2px;padding:8px 4px 2px;color:var(--ink-2);font-size:14.5px;line-height:1.4}
.gallery figcaption b{font:700 17px/1.2 "Zilla Slab",serif;color:var(--ink)}
.gallery .lead figcaption b{font-size:21px}
.gallery figcaption a{font-size:13.5px;font-weight:600;margin-top:2px}
.ingame-row{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(0,1fr);gap:18px;align-items:center;margin:0 0 20px}
.ingame-row .screen{margin:0}
.ingame-note{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--rust);border-radius:8px;padding:12px 16px;box-shadow:var(--shadow)}
.ingame-note .kicker{color:var(--rust)}
.ingame-note h4{margin:4px 0 6px;font:700 20px/1.2 "Zilla Slab",serif}
.ingame-note p{margin:0 0 6px;color:var(--ink-2)}
.ingame-note .small{font-size:14px;color:var(--ink-3);margin:0}
.ingame-pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:0 0 8px}
.ingame-pair .screen{margin:0}
.mini-row .screen+.screen{margin-top:14px}
@media (max-width:1060px){.gallery{grid-template-columns:repeat(2,minmax(0,1fr))}.gallery .lead{grid-row:auto}
  .gallery .screen:last-child:nth-child(even){grid-column:span 2}
  .ingame-row{grid-template-columns:minmax(0,1fr)}}
@media (max-width:560px){.gallery{gap:8px}.gallery .screen{padding:5px}.gallery figcaption{font-size:13px;padding:6px 2px 0}
  .gallery figcaption b{font-size:15px}.gallery .lead figcaption b{font-size:17px}.gallery figcaption span{display:none}
  .gallery .lead figcaption span{display:block}.ingame-pair{grid-template-columns:minmax(0,1fr)}.livetag{left:6px;top:6px;font-size:10px}}
/* world map */
.map-hero{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:20px;align-items:start}
.map-hero .screen{margin:0}
.map-what{background:var(--card);border:1px solid var(--rule);border-left:4px solid var(--brass);border-radius:8px;padding:10px 14px;margin:0 0 10px}
.map-what h4{margin:0 0 4px;font:700 18px "Zilla Slab",serif}.map-what p{margin:0;font-size:15.5px;color:var(--ink-2)}
.keyrow{list-style:none;padding:0;margin:16px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}
.keyrow li{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:8px 12px}
.keyrow li span{flex:1 1 100%;font-size:15px;color:var(--ink-2)}
.az{font:600 11px "Pixelify Sans",monospace;color:var(--ink-3);display:inline-flex;align-items:center;gap:4px}
.az kbd{font-size:12px}
.feats{grid-template-columns:repeat(auto-fill,minmax(min(100%,215px),1fr))}
.feat p{font-size:15.5px;color:var(--ink-2)}
.mini-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:20px;align-items:start}
.mini-row .screen{margin:0}
.tbl.ctl td:first-child{white-space:nowrap;width:1%}
.opts{margin-top:16px}.pad{padding:0 16px 16px}
/* terminal */
.reach-row{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:18px;align-items:start;margin-top:14px}
.reach-fig{margin:0;background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:12px;box-shadow:var(--shadow)}
.reach-fig figcaption{font-size:14px;color:var(--ink-3);margin-top:8px}
.reach{width:100%;height:auto;display:block;font:600 10px "Pixelify Sans",monospace}
.reach text{fill:var(--ink-2)}
.reach .rt{fill:rgba(214,166,75,.18);stroke:var(--brass);stroke-width:1.5}
.reach .rr{fill:rgba(47,125,109,.12);stroke:var(--verd);stroke-width:1.2;stroke-dasharray:4 3}
.reach .rl{stroke:var(--verd);stroke-width:1.5}
.reach .tm{fill:var(--brass-hi);stroke:var(--brass-lo);stroke-width:1.5}
.reach .rn{fill:var(--verd);stroke:var(--card);stroke-width:1.5}
.reach .cl{fill:#b5803a;stroke:#5a3a12}
.reach .co{fill:var(--ink-3);opacity:.55}
/* oceans */
.floors{grid-template-columns:repeat(auto-fill,minmax(min(100%,280px),1fr));gap:10px}
.floor{display:flex;gap:12px;align-items:flex-start;background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:10px 12px;box-shadow:var(--shadow);min-width:0}
.floor b{display:block;font:700 17px "Zilla Slab",serif}.floor span{display:block;font-size:15px;color:var(--ink-2)}
.floor small{display:flex;gap:5px;align-items:center;margin-top:4px;font-size:13px;color:var(--verd)}
.floor small svg{width:13px;height:13px;fill:var(--verd);flex:none}
.wrecks{grid-template-columns:repeat(auto-fill,minmax(min(100%,210px),1fr))}
.wreck{padding:0;overflow:hidden}
.wreck .vitrine{border-radius:0;border-width:0 0 3px;aspect-ratio:4/3}
.wreck .vitrine img{width:100%;height:100%;object-fit:contain}
.wreck h4 a{color:var(--ink);text-decoration:none}
.wreck p{font-size:15px}
.serpent{margin-top:14px;border-left-color:var(--rust);background:rgba(164,71,43,.1)}
.extras{margin-top:12px}.extras .recipe{margin-top:4px}
.badge.sea{background:#2c6f8f;color:#eef8ff}
/* world blocks */
.wbs{grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr))}
.wbs.three{grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr))}
.wb{padding:0;overflow:hidden;display:flex;flex-direction:column}
.wb-shot{position:relative}
.wb-shot .shot{border-bottom:3px solid var(--case-rim)}
.shotcap{position:absolute;left:8px;bottom:8px;padding:1px 8px;border-radius:4px;background:rgba(0,0,0,.6);color:#f1e4c4;font:600 12px "Pixelify Sans",monospace}
.wb-body{padding:12px 16px 16px}
.wb-icons{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0}
.wb-icons a{display:inline-flex;border-radius:6px;padding:2px;background:var(--card-2);border:1px solid var(--rule)}
/* performance */
.perfs{grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}
.perf .ticks{margin:0}
/* responsive */
@media (max-width:1060px){
  .layout{grid-template-columns:minmax(0,1fr);padding:0 16px;gap:0}
  .side{position:sticky;top:60px;z-index:20;flex-direction:row;overflow-x:auto;max-height:none;padding:8px 0;margin:0 -16px;padding-left:16px;
    background:var(--paper);border-bottom:1px solid var(--rule);scrollbar-width:none}
  .side a{white-space:nowrap;border-left:0;border-bottom:3px solid transparent;border-radius:6px 6px 0 0;padding:6px 10px;font-size:15px}
  .side a.on{border-bottom-color:var(--brass)}
  html{scroll-padding-top:120px}
  .wonder{grid-template-columns:minmax(0,1fr)}
  .map-hero,.reach-row{grid-template-columns:minmax(0,1fr)}
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
  .news-grid,.checks,.only,.fam-list,.orders{grid-template-columns:minmax(0,1fr)}
  .golem,.bossbox{grid-template-columns:minmax(0,1fr)}
  .golem-fig,.boss-fig{max-width:320px;width:100%;justify-self:center}
  .sym-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .foe{grid-template-columns:110px minmax(0,1fr)}
  .mini-row{grid-template-columns:minmax(0,1fr)}
  .keyrow,.floors,.wrecks{grid-template-columns:minmax(0,1fr)}
  .tbl.keys td:nth-child(3){min-width:0}
}
@media (max-width:560px){
  .gadget,.tool{grid-template-columns:minmax(0,1fr)}
  .g-visual{width:150px}
  .news-thumb{aspect-ratio:2/1}
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
  // test checklist: ticks remembered on this device only (storage may be unavailable)
  document.querySelectorAll('.check input[data-k]').forEach(function(cb){
    var k='wf-test-'+cb.getAttribute('data-k'),li=cb.closest('.check');
    try{if(localStorage.getItem(k)==='1'){cb.checked=true;li.classList.add('done');}}catch(e){}
    cb.addEventListener('change',function(){li.classList.toggle('done',cb.checked);
      try{if(cb.checked)localStorage.setItem(k,'1');else localStorage.removeItem(k);}catch(e){}});
  });
  document.querySelectorAll('.cmd').forEach(function(c){c.addEventListener('click',function(){
    try{var r=document.createRange();r.selectNodeContents(c);var s=getSelection();s.removeAllRanges();s.addRange(r);}catch(e){}});});
  // screenshots and structure views open full size (click or Escape to close)
  var lb=document.createElement('div');lb.className='lightbox';lb.hidden=true;lb.setAttribute('role','dialog');
  lb.innerHTML='<figure><img alt=""><figcaption></figcaption></figure>';document.body.appendChild(lb);
  document.addEventListener('click',function(e){
    var i=e.target.closest('.screen img,.views img');
    if(i){var im=lb.querySelector('img');im.src=i.currentSrc||i.src;im.alt=i.alt;lb.querySelector('figcaption').textContent=i.alt;lb.hidden=false;return;}
    if(e.target.closest('.lightbox'))lb.hidden=true;});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')lb.hidden=true;
    if(e.key==='Enter'&&document.activeElement&&document.activeElement.matches('.ingame img'))document.activeElement.click();});
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

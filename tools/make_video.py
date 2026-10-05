#!/usr/bin/env python3
"""Brasshaven presentation videos, rebuilt from scratch by one command:

    python3 tools/make_video.py --fetch     # CI screenshots, biome renders and showcase clips of the previews release
    python3 tools/make_video.py             # build/video/brasshaven-guide.mp4 (+ -discord.mp4, .jpg)

The "Guide de démarrage" (about 3 minutes): installing (Minecraft 26.2, Forge 65.1.0, the CurseForge modpack, the jar
in mods/, the server pack), first steps (the Manual, the keys, the quest journal, the minimap), then the world, quests
and travel, machines and fights, playing together (every multiplayer screen), and where to download.
brasshaven-guide.mp4 is the 1920x1080 master; brasshaven-guide-discord.mp4 is the same at 1280x720 in two-pass H.264,
sized to stay under Discord's 20 MB upload limit (DISCORD_MB).

Footage: the real client filmed by the `showcase` CI job (tools/ci_client.py --showcase, client/CiShowcase.java),
whose clips --fetch puts in build/video/clips/ (brasshaven-showcase-<scene>.mp4 and brasshaven-showcase-scenes.json,
with the recorded cursor drawn over them). A scene without its clip falls back to stills with motion: the CI client
screenshots (build/video/src/shot-*.png), the biome renders of the world test, the structure renders of the wiki
(build/wiki/img/s, tools/gen_wiki.py), the model sheets (build/previews/models) and a simulated cursor.

Sound: an original score synthesized by tools/videoaudio.py (no sample, no third-party music), with the UI sounds in
the same key, normalised to -16 LUFS.

Every text shown comes from the mod (README.md, docs/PUBLISHING.md, docs/SERVER_ADMIN.md, the key bindings of
client/BrasshavenClient.java and client/social/ClientSocial.java, the French language file).

Options: --stills (frames of every segment and transition to build/video/stills, no encoding),
--jobs N (parallel segment encoders), --fetch.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import videoaudio as A  # noqa: E402
import videokit as K  # noqa: E402
from videokit import W, H, FPS  # noqa: E402

PREVIEWS = "https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/"
RELEASES = "github.com/jules-crevoisier/mode-minecraft/releases"
SHOTS = ["hud_minimap", "world_map", "world_map_options", "world_map_3d", "quest_journal", "talent_tree",
         "manual_welcome", "manual_machines", "machine_harvester", "guild_terminal", "waystone", "company",
         "player_card", "emote_wheel", "pneumatic_post", "contract_board", "trade", "creative_tab", "creatures",
         "mega_structure"]
BIOMES = ["crimson_mire", "volcanic_highlands", "pale_dunes"]
SCENES = ["citadel", "sylvan_palace", "world_tree", "sky_harbour", "quest_journal", "hud_explore", "npc_contract",
          "world_map", "waystone", "talents", "magic", "machines", "machine_screen", "guild_terminal", "creatures",
          "boss", "company", "emotes", "pneumatic_post", "contract_board", "trade", "manual",
          "biome_crimson_mire", "biome_volcanic_highlands", "biome_pale_dunes"]

GUIDE_BPM = 96
DISCORD_MB = 19.0  # Discord's upload limit is 20 MB: keep a margin for the container


def log(*a):
    print("[make_video]", *a, flush=True)


# ------------------------------------------------------------------ fetching the material

def download(url, dst):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "brasshaven-make-video"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dst + ".part", "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(dst + ".part", dst)
        return True
    except Exception:
        if os.path.exists(dst + ".part"):
            os.remove(dst + ".part")
        if shutil.which("curl"):
            return subprocess.run(["curl", "-sfL", "-o", dst, url]).returncode == 0
        return False


def fetch():
    os.makedirs(K.SRC, exist_ok=True)
    os.makedirs(K.CLIPS, exist_ok=True)
    for name in SHOTS:
        dst = os.path.join(K.SRC, f"shot-{name}.png")
        ok = download(PREVIEWS + f"brasshaven-shot-{name}.png", dst) or download(PREVIEWS + f"wayfarers-shot-{name}.png", dst)
        log(("got " if ok else "missing ") + f"shot {name}")
    for b in BIOMES:
        dst = os.path.join(K.SRC, f"biome-{b}.png")
        ok = download(PREVIEWS + f"brasshaven-biome-{b}.png", dst) or download(PREVIEWS + f"wayfarers-biome-{b}.png", dst)
        log(("got " if ok else "missing ") + f"biome {b}")
    index = os.path.join(K.CLIPS, "brasshaven-showcase-scenes.json")
    if download(PREVIEWS + "brasshaven-showcase-scenes.json", index):
        with open(index, encoding="utf-8") as f:
            data = json.load(f)
        for s in data.get("scenes", []):
            ok = download(PREVIEWS + s["clip"], os.path.join(K.CLIPS, s["clip"]))
            log(("got " if ok else "missing ") + f"clip {s['clip']} ({s.get('duration')} s, {s.get('status')})")
    else:
        log("no showcase clips on the previews release yet: the videos use stills")
    if not os.path.isdir(K.RENDERS):
        log("no structure renders in build/wiki/img/s: run python3 tools/gen_wiki.py (after tools/generate_all.py)")


# ------------------------------------------------------------------ sources: real clips or stills

CLIPS, CLIP_WINDOW = {}, [1280, 720]


def load_clips():
    global CLIPS, CLIP_WINDOW
    CLIPS, window = K.scenes_index()
    CLIP_WINDOW = window or [1280, 720]
    return CLIPS


def clip(name, dur, start=None, max_speed=1.6, min_speed=0.7, gui=False):
    """A part played from a showcase clip, fitted to `dur` (sped up or slowed a little, else trimmed)."""
    c = CLIPS.get(name)
    if not c:
        return None
    length = c["duration"]
    if start is None:
        start = 0.0
    avail = max(0.5, length - start)
    speed = K.clamp(avail / dur, min_speed, 1.0) if avail < dur else 1.0
    if avail > dur * max_speed and start == 0.0:
        speed = 1.0
    return {"type": "clip", "name": name, "path": c["path"], "start": start, "speed": speed, "cursor": c.get("cursor", []),
            "gui": gui}


def still(name, kb=(1.0, 1.05, (0.5, 0.5), (0.5, 0.5)), cursor=None, then=None, gui=False):
    """A CI screenshot with a slow zoom (full frame, or framed when gui); cursor: ([(t, x, y)], [click times]) in
    shot pixels."""
    p = K.shot(name)
    if not p:
        return None
    return {"type": "still", "path": p, "kb": kb, "cursor": cursor, "then": then, "gui": gui}


def panel(name, cursor=None):
    """One of the French GUI renders of build/previews/gui (tools/gen_gui.py) on the backdrop."""
    p = os.path.join(K.GUI, name + ".png")
    return {"type": "panel", "path": p, "cursor": cursor} if os.path.exists(p) else None


def diorama(render, label=None, zoom=(1.0, 1.07), drift=(-30, 30), height=0.8):
    """A structure render cut out of its background, floating over the brass backdrop."""
    if not K.render_exists(render):
        return None
    return {"type": "diorama", "render": render, "zoom": zoom, "drift": drift, "height": height}


def biome_still(b):
    p = os.path.join(K.SRC, f"biome-{b}.png")
    return {"type": "biome", "path": p} if os.path.exists(p) else None


def first(*options):
    for o in options:
        if o:
            return o
    return {"type": "backdrop"}


# ------------------------------------------------------------------ frame renderers

# GUI screens are shown in a brass frame above the caption band, so captions never hide the interface
FRAME_RECT = (230, 28, 1460, 821)


def render_source(src, t, dur, state):
    kind = src["type"]
    if kind in ("clip", "still"):
        rect = FRAME_RECT if src.get("gui") else (0, 0, W, H)
        content = clip_or_still(src, t, dur, state, (rect[2], rect[3]))
        if rect[2] == W and rect[3] == H:
            return content
        img = K.backdrop(t)
        img.alpha_composite(framed_cached(content), (rect[0] - 6, rect[1] - 6))
        return img
    if kind == "panel":
        img = K.backdrop(t)
        glow_layer(img, 0.5, 0.45, 0.4)
        panel = K.fit(K.load(src["path"]), 1400, 780)
        u = K.ease(t / dur)
        z = K.lerp(0.97, 1.03, u)
        p = panel.resize((int(panel.width * z), int(panel.height * z)), Image.BICUBIC)
        img.alpha_composite(p, (int((W - p.width) / 2), int(440 - p.height / 2)))
        if src.get("cursor"):
            keys, clicks = src["cursor"]
            sx = p.width / K.load(src["path"]).width
            ox, oy = (W - p.width) / 2, 440 - p.height / 2
            K.CursorPath([(k[0], ox + k[1] * sx, oy + k[2] * sx) for k in keys], clicks).draw(img, t)
        return img
    if kind == "roles":
        return roles_frame(t, dur, src["rows"])
    if kind == "diorama":
        img = K.backdrop(t)
        glow_layer(img, 0.5, 0.55, 0.42)
        cut = K.cutout(src["render"], int(H * src["height"]))
        u = K.ease(t / dur)
        z = K.lerp(src["zoom"][0], src["zoom"][1], u)
        c = cut.resize((int(cut.width * z), int(cut.height * z)), Image.BICUBIC)
        x = (W - c.width) / 2 + K.lerp(src["drift"][0], src["drift"][1], u)
        y = H * 0.5 - c.height / 2
        img.alpha_composite(c, (int(x), int(y)))
        return img
    if kind == "biome":
        img = K.backdrop(t, gears=False)
        glow_layer(img, 0.5, 0.5, 0.45)
        cut = biome_cut(src["path"])
        u = K.ease(t / dur)
        z = K.lerp(0.98, 1.07, u)
        c = K.fit(cut, W * 0.8 * z, H * 0.8 * z)
        img.alpha_composite(c, (int((W - c.width) / 2 + K.lerp(20, -20, u)), int(H * 0.47 - c.height / 2)))
        return img
    if kind == "bosses":
        return bosses_frame(t, dur, src["names"])
    return K.backdrop(t)


def framed_cached(content):
    """The brass frame around a GUI shot (content changes every frame, the frame does not)."""
    w, h = content.size
    key = ("frame", w, h)
    base = _TAGS.get(key)
    if base is None:
        base = K.framed(Image.new("RGBA", (w, h), (0, 0, 0, 255)), 6)
        _TAGS[key] = base
    out = base.copy()
    out.paste(content, (6, 6))
    return out


def clip_or_still(src, t, dur, state, size):
    sw_, sh_ = size
    if src["type"] == "clip":
        reader = state.get(id(src))
        if reader is None:
            # opened when the part first shows: at its start in a render, anywhere for an inspection still
            reader = K.ClipReader(src["path"], src["start"] + t * src["speed"], src["speed"], size)
            state[id(src)] = reader
        img = reader.next()
        if src.get("cursor"):
            tc = state.get(("tc", id(src)))
            if tc is None:
                tc = K.TrackCursor(src["cursor"], CLIP_WINDOW, src["speed"], src["start"], size)
                state[("tc", id(src))] = tc
            tc.draw(img, t)
        return img
    base = K.load(src["path"], "RGB")
    then = src.get("then")
    if then and t >= then[0]:
        nxt = K.load(K.shot(then[1]), "RGB")
        u = K.clamp((t - then[0]) / 0.18)
        base = Image.blend(base, nxt, u) if u < 1 else nxt
    kb = src["kb"]
    img = K.kenburns(base, t, dur, kb[0], kb[1], kb[2], kb[3], size=size).convert("RGBA")
    if src.get("cursor"):
        keys, clicks = src["cursor"]
        # the cursor is given in shot pixels: follow the Ken Burns transform
        u = K.ease(t / dur)
        z = K.lerp(kb[0], kb[1], u)
        cx, cy = K.lerp(kb[2][0], kb[3][0], u), K.lerp(kb[2][1], kb[3][1], u)
        bw, bh = base.size
        scale = max(sw_ / bw, sh_ / bh) * z
        vw, vh = sw_ / scale, sh_ / scale
        x0 = K.clamp(cx * bw - vw / 2, 0, bw - vw)
        y0 = K.clamp(cy * bh - vh / 2, 0, bh - vh)
        K.CursorPath([(k[0], (k[1] - x0) * scale, (k[2] - y0) * scale) for k in keys], clicks).draw(img, t)
    return img


def roles_frame(t, dur, rows):
    """The quest givers and where they live (README), when the showcase has no footage of one."""
    img = K.backdrop(t)
    glow_layer(img, 0.5, 0.42, 0.42)
    y = 190
    for i, (name, where) in enumerate(rows):
        t0 = 0.2 + i * 0.3
        a = K.ease_out((t - t0) / 0.45)
        n = K.text_sprite(name, K.SERIF_BOLD, 50, fill=K.BRASS)
        w_ = K.text_sprite(where, K.SANS, 36, fill=K.CREAM, width=1000)
        x = 150 - (1 - a) * 60
        K.paste(img, n, x, y - 12, a)
        K.paste(img, w_, x + 600, y - 2, a)
        y += 128
    return img


def biome_cut(path):
    cache = os.path.join(K.WORK, "cut-" + os.path.basename(path))
    if os.path.exists(cache):
        return K.load(cache)
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, np.int32)
    bg = arr[2, 2]
    mask = Image.fromarray(np.where(np.abs(arr - bg).sum(axis=2) > 18, 255, 0).astype(np.uint8), "L")
    out = img.convert("RGBA")
    out.putalpha(mask)
    out = out.crop(mask.getbbox())
    os.makedirs(K.WORK, exist_ok=True)
    out.save(cache)
    return out


def glow_layer(img, fx, fy, r, colour=(255, 179, 71), strength=70):
    key = (fx, fy, r, colour, strength)
    g = _GLOWS.get(key)
    if g is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((xx - fx * W) / (r * W)) ** 2 + ((yy - fy * H) / (r * W * 0.8)) ** 2
        a = np.exp(-d * 2.2) * strength
        g = Image.new("RGBA", (W, H), colour + (0,))
        g.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
        _GLOWS[key] = g
    img.alpha_composite(g)


_GLOWS = {}


def name_plate(img, text, t, t0=0.15, t1=None, sub=None, corner="tl"):
    """Name of a place in a brass plate, top left."""
    spr = _plate_sprite(text, sub)
    u = K.ease_out((t - t0) / 0.4)
    a = u if t1 is None else min(u, K.ease((t1 - t) / 0.3))
    if a <= 0:
        return
    x = 56 - (1 - u) * 60
    K.paste(img, spr, x, 50, a)


_PLATES = {}


def _plate_sprite(text, sub):
    key = (text, sub)
    if key not in _PLATES:
        title = K.text_sprite(text, K.SERIF_BOLD, 50, fill=K.BRASS, shadow=False)
        s = K.text_sprite(sub, K.SANS, 30, fill=K.CREAM, shadow=False, width=900) if sub else None
        w = max(title.width, s.width if s else 0) + 60
        h = title.height + (s.height - 6 if s else 0) + 30
        p = K.plate(w, h, alpha=210).copy()
        p.alpha_composite(title, (28, 14))
        if s:
            p.alpha_composite(s, (30, 14 + title.height - 8))
        _PLATES[key] = p
    return _PLATES[key]


def chapter_tag(img, text):
    spr = _TAGS.get(text)
    if spr is None:
        t = K.text_sprite(text.upper(), K.SANS_BOLD, 22, fill=K.BRASS, shadow=False)
        spr = K.plate(t.width + 40, t.height + 22, alpha=190, radius=10).copy()
        spr.alpha_composite(t, (18, 9))
        _TAGS[text] = spr
    img.alpha_composite(spr, (W - spr.width - 40, 40))


_TAGS = {}


# ---- the card layouts

def card_title(img, t, title, sub=None):
    spr = K.brass_title(title, 78)
    u = K.ease_out(t / 0.5)
    K.paste(img, spr, 120 - (1 - u) * 50, 70, u)
    if sub:
        s = K.text_sprite(sub, K.SANS, 34, fill=K.PARCHMENT, width=1500)
        K.paste(img, s, 126, 70 + spr.height - 22, K.ease((t - 0.25) / 0.4))
    d = ImageDraw.Draw(img)
    lw = int(560 * K.ease_out((t - 0.15) / 0.6))
    if lw > 0:
        d.line([(146, 70 + spr.height + (40 if sub else -6)), (146 + lw, 70 + spr.height + (40 if sub else -6))],
               fill=K.BRASS_DARK + (255,), width=3)


def badge(label, colour=K.BRASS):
    key = ("badge", label, colour)
    if key not in _TAGS:
        f = K.font(K.SERIF_BOLD, 40 if len(label) <= 6 else 30)
        img = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([6, 10, 144, 148], fill=(60, 40, 16, 255))
        d.ellipse([6, 4, 144, 142], fill=K.BRASS_DARK + (255,))
        d.ellipse([16, 14, 134, 132], fill=colour + (255,))
        d.ellipse([24, 20, 126, 80], fill=tuple(min(255, c + 25) for c in colour) + (255,))
        tw = f.getlength(label)
        d.text(((150 - tw) / 2, 73 - f.size * 0.62), label, font=f, fill=K.INK + (255,))
        _TAGS[key] = img
    return _TAGS[key]


def render_card(seg, t):
    img = K.backdrop(t)
    kind = seg["kind"]
    if kind == "chapter":
        return chapter_frame(img, seg, t)
    if kind == "outro":
        return outro_frame(img, seg, t)
    card_title(img, t, seg["title"], seg.get("sub"))
    if kind == "list":
        if seg.get("art"):
            art = K.cutout(seg["art"], 560)
            a = K.ease_out((t - 0.3) / 0.8)
            glow_layer(img, 0.78, 0.6, 0.3)
            K.paste(img, art, 1500 - art.width / 2, 300 + (1 - a) * 40 + math.sin(t * 1.2) * 6, a)
        y = 330
        for i, (b, text, note) in enumerate(seg["rows"]):
            t0 = 0.5 + i * seg.get("stagger", 0.55)
            u = K.ease_out((t - t0) / 0.45)
            if u <= 0:
                y += 165
                continue
            bx = 150 - (1 - u) * 80
            K.paste(img, badge(b), bx, y - 8, u)
            s = K.text_sprite(text, K.SANS_BOLD, 46, fill=K.CREAM, width=1300)
            K.paste(img, s, bx + 175, y + 4, u)
            if note:
                n = K.text_sprite(note, K.SANS, 32, fill=K.PARCHMENT, width=1300)
                K.paste(img, n, bx + 177, y + 4 + s.height - 30, u)
            y += 165
        return img
    if kind == "steps":
        illu_right = seg.get("illustration")
        width = 760 if illu_right else 1560
        y = 300
        for i, text in enumerate(seg["steps"]):
            t0 = 0.6 + i * seg.get("stagger", 0.9)
            u = K.ease_out((t - t0) / 0.45)
            s = K.text_sprite(text, K.SANS, 39, fill=K.CREAM, width=width)
            if u > 0:
                bx = 150 - (1 - u) * 80
                n = badge(str(i + 1))
                small = n.resize((96, 96), Image.LANCZOS)
                K.paste(img, small, bx, y - 4, u)
                K.paste(img, s, bx + 125, y - 2, u)
            y += max(112, s.height + 22)
        if illu_right:
            ILLUSTRATIONS[illu_right](img, t, seg)
        return img
    if kind == "keys":
        keys = seg["keys"]
        cols = 7
        cw, ch = 252, 300
        x0 = (W - cols * cw) / 2 + 10
        for i, (k, label, az) in enumerate(keys):
            r, c = divmod(i, cols)
            t0 = 0.45 + i * 0.16
            u = K.back_out((t - t0) / 0.45)
            a = K.clamp((t - t0) / 0.25)
            if a <= 0:
                continue
            cap = K.keycap(k, 140, az, wide=1.0 if len(k) <= 2 else 1.9)
            x = x0 + c * cw + (cw - cap.width) / 2
            y = 280 + r * ch + (1 - K.clamp(u, 0, 1.2)) * 30
            K.paste(img, cap, x, y, a)
            lab = K.text_sprite(label, K.SANS_BOLD, 32, fill=K.CREAM, width=cw - 10, align="center")
            K.paste(img, lab, x0 + c * cw + (cw - lab.width) / 2, y + cap.height - 8, a)
        if seg.get("note"):
            t0 = 0.45 + len(keys) * 0.16 + 0.3
            n = K.text_sprite(seg["note"], K.SANS, 32, fill=K.PARCHMENT, width=1640, align="center")
            K.paste(img, n, (W - n.width) / 2, H - n.height - 46, K.ease((t - t0) / 0.4))
        return img
    if kind == "outro":
        return outro_frame(img, seg, t)
    return img


def chapter_frame(img, seg, t):
    glow_layer(img, 0.5, 0.5, 0.35)
    g = K.gear_sprite(250, 12, K.BRASS, 60).rotate(-t * 22 - 20 * K.ease_out(t / 0.8), resample=Image.BICUBIC)
    img.alpha_composite(g, (int(W / 2 - g.width / 2), int(H / 2 - g.height / 2 - 40)))
    num = K.text_sprite(seg["number"], K.SERIF_BOLD, 150, fill=K.CREAM)
    u = K.ease_out(t / 0.5)
    K.paste(img, num, (W - num.width) / 2, H / 2 - num.height / 2 - 52 - (1 - u) * 40, u)
    title = K.brass_title(seg["title"], 96)
    title = K.sweep(title, (t - 0.4) / 1.2)
    u2 = K.ease_out((t - 0.2) / 0.5)
    K.paste(img, title, (W - title.width) / 2, H / 2 + 120 + (1 - u2) * 40, u2)
    if seg.get("sub"):
        s = K.text_sprite(seg["sub"], K.SANS, 36, fill=K.PARCHMENT, width=1400, align="center")
        K.paste(img, s, (W - s.width) / 2, H / 2 + 120 + title.height - 18, K.ease((t - 0.45) / 0.4))
    return img


def outro_frame(img, seg, t):
    glow_layer(img, 0.72, 0.5, 0.4)
    cut = K.cutout("clockwork_citadel", int(H * 0.86))
    u = K.ease_out(t / 1.2)
    z = K.lerp(1.0, 1.05, K.ease(t / seg["dur"]))
    c = cut.resize((int(cut.width * z), int(cut.height * z)), Image.BICUBIC)
    K.paste(img, c, W * 0.74 - c.width / 2, H - c.height + 30 + (1 - u) * 60, u)
    title = K.sweep(K.brass_title("Brasshaven", 130), (t - 0.6) / 1.4)
    K.paste(img, title, 90, 70, K.ease_out(t / 0.6))
    y = 300
    for i, (kick, text) in enumerate(seg["rows"]):
        t0 = 0.6 + i * 0.5
        a = K.ease_out((t - t0) / 0.4)
        k = K.kicker_sprite(kick)
        s = K.text_sprite(text, K.SANS_BOLD, 40, fill=K.CREAM, width=980)
        K.paste(img, k, 124, y, a)
        K.paste(img, s, 96, y + k.height - 18, a)
        y += 118
    if seg.get("final"):
        t0 = seg.get("final_at", 3.5)
        f = K.brass_title(seg["final"], 120)
        u3 = K.back_out((t - t0) / 0.6)
        a = K.clamp((t - t0) / 0.3)
        if a > 0:
            s = 0.8 + 0.2 * K.clamp(u3, 0, 1.2)
            f2 = f.resize((int(f.width * s), int(f.height * s)), Image.BICUBIC)
            K.paste(img, f2, 90 + (f.width - f2.width) / 2, 760 + (f.height - f2.height) / 2, a)
    return img


# ---- illustrations of the install steps (generic, no third-party app drawn)

def _window(w, h, title):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 6, w - 1, h - 1], 14, fill=(0, 0, 0, 110))
    d.rounded_rectangle([0, 0, w - 6, h - 8], 14, fill=(33, 28, 24, 255), outline=K.BRASS_DARK + (255,), width=3)
    d.rounded_rectangle([0, 0, w - 6, 52], 14, fill=(58, 44, 30, 255))
    d.rectangle([0, 30, w - 6, 52], fill=(58, 44, 30, 255))
    for i, c in enumerate(((200, 90, 60), (220, 180, 80), (110, 170, 90))):
        d.ellipse([20 + i * 28, 17, 38 + i * 28, 35], fill=c + (255,))
    f = K.font(K.SANS_BOLD, 24)
    d.text((120, 13), title, font=f, fill=K.CREAM + (255,))
    return img


def _file_icon(label, colour, ext):
    img = Image.new("RGBA", (150, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(10, 4), (100, 4), (140, 44), (140, 172), (10, 172)], fill=(235, 226, 205, 255), outline=(90, 70, 40, 255))
    d.polygon([(100, 4), (100, 44), (140, 44)], fill=(200, 188, 160, 255), outline=(90, 70, 40, 255))
    d.rounded_rectangle([18, 96, 132, 140], 8, fill=colour + (255,))
    f = K.font(K.SANS_BOLD, 28)
    d.text((75 - f.getlength(ext) / 2, 101), ext, font=f, fill=(255, 250, 235, 255))
    return img


def illu_mods_folder(img, t, seg):
    win = _window(640, 460, ".minecraft / mods")
    d = ImageDraw.Draw(win)
    f = K.font(K.SANS, 26)
    for i, name in enumerate(("config", "mods", "saves", "options.txt")):
        y = 80 + i * 44
        d.text((40, y), ("▸ " if i < 3 else "  ") + name, font=f, fill=(200, 188, 160, 255) if i != 1 else K.BRASS + (255,))
    x0, y0 = 1200, 330
    a = K.ease_out((t - 0.4) / 0.5)
    K.paste(img, win, x0, y0, a)
    # the jar slides into the window on the third step
    tj = 0.6 + 2 * seg.get("stagger", 0.9)
    u = K.ease_out((t - tj) / 0.9)
    icon = _file_icon("jar", (176, 96, 40), ".jar")
    if t >= tj - 0.3:
        x = K.lerp(x0 + 520, x0 + 360, u)
        y = K.lerp(y0 - 260, y0 + 220, u)
        K.paste(img, icon, x, y, K.clamp((t - tj + 0.3) / 0.3))
        lab = K.text_sprite("brasshaven-<version>.jar", K.MONO_BOLD, 22, fill=K.CREAM, shadow=True)
        K.paste(img, lab, x + 75 - lab.width / 2, y + 180, K.clamp((t - tj) / 0.3))


def illu_modpack(img, t, seg):
    a = K.ease_out((t - 0.5) / 0.5)
    zip_icon = _file_icon("zip", (90, 120, 150), ".zip")
    K.paste(img, zip_icon, 1160, 400, a)
    lab = K.text_sprite("brasshaven-modpack-<version>.zip", K.MONO_BOLD, 19, fill=K.CREAM)
    K.paste(img, lab, 1255 - lab.width / 2, 590, a)
    u = K.ease_out((t - 1.6) / 0.8)
    d = ImageDraw.Draw(img)
    if u > 0:
        x1 = 1330 + 100 * u
        d.line([(1330, 495), (x1, 495)], fill=K.BRASS + (255,), width=8)
        if u > 0.95:
            d.polygon([(x1, 475), (x1 + 30, 495), (x1, 515)], fill=K.BRASS + (255,))
    card = _window(330, 300, "Profil")
    dc = ImageDraw.Draw(card)
    f = K.font(K.SANS_BOLD, 30)
    f2 = K.font(K.SANS, 26)
    dc.text((28, 80), "Minecraft 26.2", font=f, fill=K.CREAM + (255,))
    dc.text((28, 124), "Forge 65.1.0", font=f, fill=K.CREAM + (255,))
    dc.text((28, 176), "+ Brasshaven", font=f2, fill=K.BRASS + (255,))
    dc.text((28, 214), "+ réglages conseillés", font=f2, fill=K.PARCHMENT + (255,))
    K.paste(img, card, 1490, 345, K.ease_out((t - 2.4) / 0.6))


def illu_server(img, t, seg):
    win = _window(700, 470, "serveur")
    # the prompts of serverpack/start.sh
    lines = ["$ unzip brasshaven-server-<version>.zip", "$ java -version", '  openjdk version "25"', "$ ./start.sh",
             "== Installation de Forge 26.2-65.1.0", "Acceptes-tu le CLUF de Minecraft ? [o/y/N] o", 'Done! For help, type "help"']
    f = K.font(K.MONO_BOLD, 22)
    d = ImageDraw.Draw(win)
    shown = (t - 0.8) / 0.55
    for i, l in enumerate(lines):
        if shown <= i:
            break
        part = l if shown >= i + 1 else l[: int(len(l) * (shown - i))]
        colour = K.BRASS if l.startswith("$") else K.CREAM
        d.text((30, 80 + i * 50), part, font=f, fill=colour + (255,))
    K.paste(img, win, 1170, 340, K.ease_out((t - 0.4) / 0.5))


ILLUSTRATIONS = {"mods": illu_mods_folder, "modpack": illu_modpack, "server": illu_server}


def bosses_frame(t, dur, names):
    img = K.backdrop(t)
    glow_layer(img, 0.5, 0.42, 0.45, colour=(200, 60, 40), strength=55)
    n = len(names)
    cw = 440
    x0 = (W - n * cw) / 2
    for i, (model, label) in enumerate(names):
        t0 = 0.2 + i * 0.35
        a = K.ease_out((t - t0) / 0.5)
        if a <= 0:
            continue
        view = K.model_view(model)
        frame = K.framed(view.resize((390, 364), Image.LANCZOS), 6)
        bob = math.sin((t + i) * 1.6) * 6
        x = x0 + i * cw + (cw - frame.width) / 2 + 12
        y = 150 + (1 - a) * 60 + bob
        K.paste(img, frame, x, y, a)
        lab = K.text_sprite(label, K.SERIF_BOLD, 34, fill=K.BRASS, width=cw - 20, align="center")
        K.paste(img, lab, x0 + i * cw + (cw - lab.width) / 2 + 12, y + frame.height - 10, a)
    return img


# ------------------------------------------------------------------ segments

def render_frame(seg, t, state):
    kind = seg["kind"]
    if kind == "scene":
        parts = seg["parts"]
        acc = 0.0
        idx = 0
        for i, (pd, _) in enumerate(parts):
            if t < acc + pd or i == len(parts) - 1:
                idx = i
                break
            acc += pd
        pd, src = parts[idx]
        tl = t - acc
        img = render_source(src, tl, pd, state)
        # a quick dip between parts
        if len(parts) > 1 and seg.get("part_dip", 0.16) > 0:
            dip = seg.get("part_dip", 0.16)
            a = 1.0
            if idx > 0 and tl < dip:
                a = tl / dip
            if idx < len(parts) - 1 and pd - tl < dip:
                a = min(a, (pd - tl) / dip)
            if a < 1:
                img = Image.blend(Image.new("RGBA", (W, H), K.DIP + (255,)), img, K.ease(a))
        plates = seg.get("plates") or []
        if idx < len(plates) and plates[idx]:
            p = plates[idx]
            name_plate(img, p[0], tl, 0.25, pd - 0.05 if len(parts) > 1 else None, p[1] if len(p) > 1 else None)
        if seg.get("plate"):
            name_plate(img, seg["plate"][0], t, 0.3, None, seg["plate"][1] if len(seg["plate"]) > 1 else None)
        for c in seg.get("captions", []):
            K.place_caption(img, t, c[0], c[1], c[2], c[3] if len(c) > 3 else None, c[4] if len(c) > 4 else "bottom")
        for b in seg.get("bigtext", []):
            big_text(img, t, *b)
    elif kind == "hero":
        img = hero_frame(seg, t, state)
    else:
        img = render_card(seg, t)
    if seg.get("chapter"):
        chapter_tag(img, seg["chapter"])
    fin, fout = seg.get("fin", 0.3), seg.get("fout", 0.3)
    a = 1.0
    if fin > 0 and t < fin:
        a = t / fin
    if fout > 0 and seg["dur"] - t < fout:
        a = min(a, (seg["dur"] - t) / fout)
    if a < 1:
        img = Image.blend(Image.new("RGBA", (W, H), K.DIP + (255,)), img, K.ease(max(0.0, a)))
    if seg.get("flash_at") is not None:
        ft = t - seg["flash_at"]
        if 0 <= ft < 0.35:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 236, 190, 255)), 0.55 * (1 - ft / 0.35))
    return img


def big_text(img, t, t0, t1, line1, line2=None, pos=0.5):
    """Teaser type: a huge brass line, settled for its whole window, on a dark band."""
    if t < t0 or t > t1:
        return
    u = K.ease_out((t - t0) / 0.3)
    a = min(u, K.ease((t1 - t) / 0.2))
    title = K.brass_title(line1, 104)
    band_h = title.height + (70 if line2 else 10)
    y = int(H * pos - band_h / 2)
    band = Image.new("RGBA", (W, band_h + 40), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(band.height):
        edge = min(i, band.height - i) / 30
        bd.line([(0, i), (W, i)], fill=(12, 10, 9, int(170 * K.clamp(edge))))
    K.paste(img, band, 0, y - 20, a)
    K.paste(img, title, (W - title.width) / 2 + (1 - u) * 60, y - 10, a)
    if line2:
        s = K.text_sprite(line2, K.SANS_BOLD, 40, fill=K.CREAM, width=1600, align="center")
        K.paste(img, s, (W - s.width) / 2, y + title.height - 32, a)


def hero_frame(seg, t, state):
    src = seg["src"]
    img = render_source(src, t, seg["dur"], state)
    if src["type"] in ("clip", "still"):
        # darken the left for the title
        img.alpha_composite(_left_shade())
    title = K.sweep(K.brass_title(seg["title"], seg.get("size", 170)), (t - seg.get("sweep_at", 0.9)) / 1.4)
    u = K.ease_out((t - seg.get("title_at", 0.3)) / 0.6)
    K.paste(img, title, 90 - (1 - u) * 70, seg.get("title_y", 300), u)
    y = seg.get("title_y", 300) + title.height - 20
    for i, (text, size, colour) in enumerate(seg.get("lines", [])):
        t0 = seg.get("lines_at", 1.0) + i * 0.45
        s = K.text_sprite(text, K.SANS_BOLD if i == 0 else K.SANS, size, fill=colour, width=1100)
        K.paste(img, s, 104, y, K.ease_out((t - t0) / 0.45))
        y += s.height - 6
    return img


_SHADE = []


def _left_shade():
    if not _SHADE:
        x = np.linspace(0, 1, W)[None, :]
        a = np.clip(1.0 - x / 0.62, 0, 1) ** 1.4 * 200
        a = np.repeat(a, H, axis=0).astype(np.uint8)
        s = Image.new("RGBA", (W, H), (10, 8, 8, 0))
        s.putalpha(Image.fromarray(a, "L"))
        _SHADE.append(s)
    return _SHADE[0]


# ------------------------------------------------------------------ the guide

def guide_segments():
    """The guide, chapter by chapter. Each scene uses its real clip when the showcase job filmed it."""
    S = []
    beat = 60.0 / GUIDE_BPM

    def add(seg):
        S.append(seg)
        return seg

    # ---- opening
    add({"kind": "hero", "dur": 5.625, "fin": 0.6, "fout": 0.4, "bell": (0.5, 74),
         "src": first(clip("citadel", 5.625, 1.0), diorama("clockwork_citadel", zoom=(1.0, 1.08), drift=(540, 570))),
         "title": "Brasshaven", "size": 160, "title_y": 300,
         "lines": [("Guide de démarrage", 56, K.CREAM),
                   ("Le mod d'exploration coop pour Minecraft 26.2 · Forge 65.1.0", 34, K.PARCHMENT)],
         "lines_at": 1.2})

    # ---- 1. Installer
    ch = "1 · Installer"
    add({"kind": "chapter", "dur": 2.5, "number": "1", "title": "Installer", "sub": "Ce qu'il te faut, et comment l'installer",
         "hit": True})
    add({"kind": "list", "dur": 6.875, "chapter": ch, "title": "Ce qu'il te faut", "stagger": 0.55, "art": "sky_harbour",
         "rows": [("26.2", "Minecraft Java Edition 26.2", None),
                  ("65.1.0", "Forge 65.1.0", "l'installeur forge-26.2-65.1.0"),
                  ("25", "Java 25", "obligatoire pour un serveur"),
                  (".jar", "Le mod : brasshaven-<version>.jar", "un seul fichier, aucune autre bibliothèque")]})
    add({"kind": "steps", "dur": 7.5, "chapter": ch, "title": "Le plus simple : l'app CurseForge", "illustration": "modpack",
         "stagger": 1.0,
         "steps": ["Télécharge brasshaven-modpack-<version>.zip (Releases GitHub).",
                   "Dans CurseForge : Create Custom Profile, puis Import, et choisis le zip.",
                   "Profil Minecraft 26.2 + Forge 65.1.0 prêt, mod et réglages compris."]})
    add({"kind": "steps", "dur": 8.75, "chapter": ch, "title": "À la main, avec le launcher", "illustration": "mods",
         "stagger": 0.9,
         "steps": ["Lance forge-26.2-65.1.0-installer.jar : « Install client ».",
                   "Ouvre le dossier mods de ton jeu (.minecraft/mods).",
                   "Dépose brasshaven-<version>.jar dedans : un seul jar du mod.",
                   "Lance le profil Forge dans le launcher."]})
    add({"kind": "steps", "dur": 9.375, "chapter": ch, "title": "Pour un serveur", "illustration": "server", "stagger": 0.9,
         "steps": ["Décompresse brasshaven-server-<version>.zip dans un dossier vide.",
                   "Installe Java 25, lance ./start.sh (ou start.bat) et accepte le CLUF.",
                   "Même version du mod sur le serveur et chez chaque joueur.",
                   "Crée un nouveau monde : les structures n'apparaissent que là où rien n'a été généré."]})

    # ---- 2. Premiers pas
    ch = "2 · Premiers pas"
    add({"kind": "chapter", "dur": 2.5, "number": "2", "title": "Premiers pas", "sub": "Le manuel, les touches, ta première quête",
         "hit": True})
    add({"kind": "scene", "dur": 8.75, "chapter": ch,
         "parts": [(8.75, first(clip("manual", 8.75, gui=True),
                              still("manual_welcome", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.5, 900, 560), (2.6, 1100, 648), (6.0, 1100, 648), (7.0, 175, 254)], [2.8, 7.2]),
                                    gui=True)))],
         "captions": [(0.3, 4.55, "Première connexion : l'Atlas, le Manuel du Voyageur et la boussole des structures.",
                       "Bienvenue"),
                      (4.7, 8.65, "Survole un objet, maintiens W (Z en AZERTY) : sa page s'ouvre.",
                       "Astuce")]})
    add({"kind": "keys", "dur": 9.375, "chapter": ch, "title": "Les touches à connaître",
         "keys": [("J", "Journal de quêtes", None), ("K", "Talents", None), ("V", "Capacité active", None),
                  ("M", "Carte du monde", ","), ("H", "Mini-carte", None), ("Z", "Zoom mini-carte", "W"),
                  ("B", "Signal", None), ("O", "Compagnie", None), ("U", "Fiche d'un joueur", None),
                  ("Y", "Gestes", None), ("R", "Trier l'inventaire", None), ("N", "Anneau aimanté", None),
                  ("G", "Symétrie", None), ("W", "Page du manuel (maintenu)", "Z")],
         "note": "Touches d'un clavier QWERTY. Toutes se changent dans Options, Commandes, rubrique Brasshaven."})
    add({"kind": "scene", "dur": 8.125, "chapter": ch,
         "parts": [(8.125, first(clip("quest_journal", 8.125, gui=True),
                              still("quest_journal", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.6, 700, 450), (1.6, 580, 322), (3.2, 580, 322), (4.4, 1010, 598)], [1.8, 4.7]),
                                    gui=True)))],
         "captions": [(0.3, 4.85, "Touche J : le journal de quêtes, cinq chapitres partagés par tout le serveur.", "Quêtes"),
                      (5.05, 8.0, "« Suivre » épingle l'objectif en haut de l'écran.", "Suivi")]})
    add({"kind": "scene", "dur": 6.25, "chapter": ch,
         "parts": [(6.25, first(clip("hud_explore", 6.25), still("hud_minimap", (1.0, 1.10, (0.3, 0.3), (0.2, 0.2)))))],
         "captions": [(0.3, 6.1, "La mini-carte : terrain, coordonnées, biome, repères. H la masque, Maj + H change sa taille.",
                       "Mini-carte")]})

    # ---- 3. Explorer
    ch = "3 · Explorer"
    add({"kind": "chapter", "dur": 2.5, "number": "3", "title": "Explorer", "sub": "Des merveilles faites à la main", "hit": True})
    add({"kind": "scene", "dur": 6.875, "chapter": ch,
         "parts": [(6.875, first(clip("citadel", 6.875, 5.0), diorama("clockwork_citadel", zoom=(0.98, 1.08), drift=(-20, 20))))],
         "plate": ("Citadelle d'horlogerie",),
         "captions": [(0.8, 6.7, "71 × 71 blocs, une tour-horloge de 75 blocs, sept étages meublés.", "Méga-structure")]})
    add({"kind": "scene", "dur": 7.5, "chapter": ch,
         "parts": [(2.5, first(clip("sylvan_palace", 2.5, 2.0), diorama("sylvan_palace"))),
                   (2.5, first(clip("world_tree", 2.5, 2.0), diorama("giant_tree"))),
                   (2.5, first(clip("sky_harbour", 2.5, 1.0), diorama("sky_harbour")))],
         "plates": [("Palais sylvain",), ("Arbre-monde",), ("Port céleste",)],
         "captions": [(0.4, 7.35, "Des dizaines de structures : palais, cités, donjons, épaves… chacune avec ses secrets.", None)]})
    add({"kind": "scene", "dur": 8.125, "chapter": ch, "part_dip": 0.14,
         "parts": [(2.7, first(clip("biome_crimson_mire", 2.7), biome_still("crimson_mire"))),
                   (2.7, first(clip("biome_volcanic_highlands", 2.7), biome_still("volcanic_highlands"))),
                   (2.7, first(clip("biome_pale_dunes", 2.7), biome_still("pale_dunes")))],
         "plates": [("Marais pourpre", "eau rouge sombre, champignons géants"),
                    ("Hautes terres volcaniques", "falaises ocre, magma, évents fumants"),
                    ("Dunes pâles", "sable pâle strié d'or, cheminées de fée")]})

    # ---- 4. Quêtes et voyages
    ch = "4 · Quêtes et voyages"
    add({"kind": "chapter", "dur": 2.5, "number": "4", "title": "Quêtes et voyages", "sub": "Contrats, carte, pierres de voyage, talents",
         "hit": True})
    add({"kind": "scene", "dur": 6.875, "chapter": ch,
         "parts": [(6.875, first(clip("npc_contract", 6.875),
                              {"type": "roles", "rows": [("Agent de la Guilde", "villages et avant-postes de la Guilde"),
                                                         ("Érudite", "auberges, Bibliothèque oubliée"),
                                                         ("Bricoleur", "ateliers, Citadelle d'horlogerie"),
                                                         ("Druidesse", "Arbre-monde creux"),
                                                         ("Ancien nain", "Cité naine des profondeurs")]}))],
         "captions": [(0.3, 4.4, "Les donneurs de quêtes proposent des contrats : apporter, chasser, trouver, livrer.", "Contrats"),
                      (4.6, 6.75, "Clic droit pour leur parler.", None)]})
    add({"kind": "scene", "dur": 7.5, "chapter": ch,
         "parts": [(7.5, first(clip("world_map", 7.5, gui=True),
                              still("world_map", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.4, 600, 330), (1.8, 420, 300), (3.6, 824, 392)], [4.0]), then=(4.15, "world_map_3d"),
                                    gui=True)))],
         "captions": [(0.3, 4.2, "Touche M : la carte du monde. Glisse, zoome, pose des repères.", "Carte"),
                      (4.35, 7.4, "Et la même carte en relief, en 3D.", None)]})
    add({"kind": "scene", "dur": 6.25, "chapter": ch,
         "parts": [(6.25, first(clip("waystone", 6.25),
                              still("waystone", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.5, 700, 500), (1.6, 440, 238), (3.4, 908, 398)], [3.8]), gui=True)))],
         "captions": [(0.3, 6.15, "Pierres de voyage : découvertes pour tout le groupe, on voyage de l'une à l'autre.",
                       "Voyage")]})
    add({"kind": "scene", "dur": 8.125, "chapter": ch,
         "parts": [(4.6, first(clip("talents", 4.6, gui=True),
                              still("talent_tree", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.3, 640, 500), (1.2, 192, 180), (2.6, 488, 180), (3.8, 786, 260)], [1.5, 2.9]),
                                    gui=True))),
                   (3.525, first(clip("magic", 3.525), still("talent_tree", (1.04, 1.12, (0.62, 0.5), (0.72, 0.5)))))],
         "captions": [(0.3, 4.5, "Touche K : 36 talents en 4 branches. V lance ta capacité active.", "Talents"),
                      (4.7, 8.0, "Et 7 bâtons de sort, qui consomment du mana.", "Magie")]})

    # ---- 5. Machines et combats
    ch = "5 · Machines et combats"
    add({"kind": "chapter", "dur": 2.5, "number": "5", "title": "Machines et combats", "sub": "Fermes, stockage, créatures et boss",
         "hit": True})
    add({"kind": "scene", "dur": 7.5, "chapter": ch,
         "parts": [(4.4, first(clip("machines", 4.4, 2.0),
                              still("machine_harvester", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.4, 600, 520), (1.6, 684, 212), (3.2, 500, 272)], [2.0, 3.5]), gui=True))),
                   (3.1, first(clip("machine_screen", 3.1, 1.0, gui=True),
                               still("machine_harvester", (1.3, 1.36, (0.5, 0.3), (0.5, 0.3)),
                                     ([(0.3, 760, 420), (1.3, 684, 212), (2.4, 772, 212)], [1.6, 2.7]), gui=True)))],
         "captions": [(0.3, 4.25, "Neuf machines simples, sans câble ni énergie : moissonneuse, arroseur, casseur…", "Machines"),
                      (4.4, 7.4, "Chaque machine a son écran : zone, sortie, redstone.", None)]})
    add({"kind": "scene", "dur": 6.25, "chapter": ch,
         "parts": [(6.25, first(clip("guild_terminal", 6.25, gui=True),
                              still("guild_terminal", (1.0, 1.02, (0.5, 0.5), (0.5, 0.5)),
                                    ([(0.4, 800, 500), (1.4, 540, 76), (3.8, 490, 442)], [1.7, 4.1]), gui=True)))],
         "captions": [(0.3, 6.15, "Terminal de guilde : tous les coffres de la base dans une seule grille, avec recherche et tri.",
                       "Rangement")]})
    add({"kind": "scene", "dur": 9.375, "chapter": ch,
         "parts": [(3.4, first(clip("creatures", 3.4, 1.0), still("creatures", (1.0, 1.08, (0.45, 0.5), (0.5, 0.55))))),
                   (5.975, first(clip("boss", 5.975, 2.0),
                                 {"type": "bosses", "names": [("forge_king", "Le Roi-Forgeron"), ("root_mother", "La Mère-Racine"),
                                                              ("gryphon_knight", "Le Chevalier-griffon"),
                                                              ("void_warden", "Gardien du vide")]}))],
         "captions": [(0.3, 3.3, "Automates et créatures, avec leur barre de vie.", "Créatures"),
                      (3.5, 9.25, "20 boss façon Elden Ring. À leur mort : « ENNEMI ABATTU » et un Souvenir.", "Boss")]})

    # ---- 6. Entre amis: every multiplayer screen gets its own scene
    ch = "6 · Entre amis"
    add({"kind": "chapter", "dur": 2.5, "number": "6", "title": "Entre amis", "sub": "Le multijoueur de Brasshaven", "hit": True})
    add({"kind": "scene", "dur": 10.0, "chapter": ch,
         "parts": [(10.0, first(clip("company", 10.0, gui=True), still("company", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                                                      ([(0.3, 900, 500), (2.0, 764, 222), (5.0, 640, 420)],
                                                                       [2.6, 5.6]), gui=True)))],
         "captions": [(0.3, 4.4, "Touche O : ta compagnie, jusqu'à 8 joueurs.", "Compagnie"),
                      (4.55, 9.9, "XP partagée, chat de compagnie (/cc) et tes compagnons en or sur la carte.",
                       "Compagnie")]})
    add({"kind": "scene", "dur": 10.625, "chapter": ch,
         "parts": [(10.625, first(still("player_card", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                       ([(0.3, 900, 600), (2.2, 700, 520), (5.6, 820, 520)], [3.0, 6.2]), gui=True),
                                 clip("company", 10.625, gui=True)))],
         "captions": [(0.3, 5.45, "Accroupi + clic droit sur un joueur, main vide, ou vise-le et appuie sur U.",
                       "Fiche du joueur"),
                      (5.6, 10.5, "Sa fiche : sa compagnie, ses duels, et Échanger, Duel, Inviter, Saluer.",
                       "Fiche du joueur")]})
    add({"kind": "scene", "dur": 6.25, "chapter": ch,
         "parts": [(6.25, first(clip("emotes", 6.25, 2.0), still("emote_wheel", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                                                 ([(0.2, 900, 420), (1.6, 636, 170), (3.4, 820, 344)],
                                                                  [2.2, 4.0]), gui=True)))],
         "captions": [(0.3, 6.15, "Touche Y : huit gestes animés, que tout le monde autour de toi voit.", "Gestes")]})
    add({"kind": "scene", "dur": 9.375, "chapter": ch,
         "parts": [(9.375, first(clip("trade", 9.375, gui=True), still("trade", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                                                      ([(0.2, 700, 500), (2.0, 442, 346), (5.4, 900, 600)],
                                                                       [2.6, 6.0]), gui=True)))],
         "captions": [(0.3, 4.6, "Échange sécurisé : chacun pose son offre, en face à face.", "Échange"),
                      (4.75, 9.25, "Les deux acceptent, 3 secondes, et c'est fait. Le moindre changement annule.",
                       "Échange")]})
    add({"kind": "scene", "dur": 9.375, "chapter": ch,
         "parts": [(9.375, first(clip("pneumatic_post", 9.375, gui=True),
                                 still("pneumatic_post", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                       ([(0.2, 600, 400), (2.0, 320, 160), (5.2, 700, 500)], [2.4, 5.8]), gui=True)))],
         "captions": [(0.3, 4.6, "Poste pneumatique : écris à n'importe quel joueur, même absent.", "Poste"),
                      (4.75, 9.25, "Une lettre et jusqu'à 6 piles d'objets, payées en pépites de laiton.", "Poste")]})
    add({"kind": "scene", "dur": 9.375, "chapter": ch,
         "parts": [(9.375, first(clip("contract_board", 9.375, gui=True),
                                 still("contract_board", (1.0, 1.04, (0.5, 0.5), (0.5, 0.5)),
                                       ([(0.2, 700, 400), (2.0, 420, 156), (5.2, 760, 520)], [2.4, 5.8]), gui=True)))],
         "captions": [(0.3, 4.6, "Tableau des contrats : « 32 fer contre 3 diamants ».", "Contrats"),
                      (4.75, 9.25, "La récompense attend le livreur, la marchandise arrive par la poste.", "Contrats")]})
    add({"kind": "scene", "dur": 6.875, "chapter": ch,
         "parts": [(6.875, first(still("player_card", (1.04, 1.1, (0.55, 0.6), (0.55, 0.65)),
                                       ([(0.3, 800, 600), (2.0, 820, 520)], [2.6]), gui=True),
                                 clip("company", 6.875, gui=True)))],
         "captions": [(0.3, 6.75, "Duels : 3-2-1 dans un cercle rouge. Personne ne meurt, le dernier coup laisse un "
                                  "demi-cœur.", "Duels")]})

    # ---- outro
    add({"kind": "outro", "dur": 8.125, "fout": 1.2, "hit": True, "bell": (3.4, 69),
         "rows": [("Télécharger", RELEASES), ("Bientôt", "sur CurseForge et Modrinth"),
                  ("Pour", "Minecraft 26.2 · Forge 65.1.0 · Java 25")],
         "final": "Bon jeu !", "final_at": 3.4})
    return snap(S, beat)


def snap(segments, beat):
    """Durations rounded to whole beats, so cuts land on the music."""
    for s in segments:
        s["dur"] = max(beat, math.ceil(s["dur"] / beat - 0.05) * beat)
        if s["kind"] == "scene":
            total = sum(p[0] for p in s["parts"])
            k = s["dur"] / total
            s["parts"] = [(p[0] * k, p[1]) for p in s["parts"]]
    return segments


# ------------------------------------------------------------------ checks

def check_reading(segments, name):
    """Every caption stays settled for at least 0.3 s per word (from the moment it is fully in)."""
    problems = []
    for i, s in enumerate(segments):
        for c in s.get("captions", []):
            settled = (c[1] - 0.3) - (c[0] + 0.35)
            need = 0.3 * K.words(c[2])
            if settled + 0.05 < need:
                problems.append(f"{name} #{i}: '{c[2][:50]}…' settled {settled:.1f}s < {need:.1f}s")
        for b in s.get("bigtext", []):
            settled = (b[1] - 0.2) - (b[0] + 0.3)
            need = 0.3 * (K.words(b[2]) + K.words(b[3] or ""))
            if settled + 0.05 < need:
                problems.append(f"{name} #{i}: '{b[2]}' settled {settled:.1f}s < {need:.1f}s")
    for p in problems:
        log("READING", p)
    return problems


# ------------------------------------------------------------------ rendering

def seg_frames(seg):
    return int(round(seg["dur"] * FPS))


def render_segment(job):
    idx, seg, out, poster = job
    load_clips()
    n = seg_frames(seg)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    state = {}
    try:
        for f in range(n):
            if f == 0 and poster:
                img = Image.open(poster).convert("RGB")
            else:
                img = render_frame(seg, f / FPS, state).convert("RGB")
            enc.stdin.write(img.tobytes())
    finally:
        for v in state.values():
            if isinstance(v, K.ClipReader):
                v.close()
        enc.stdin.close()
        enc.wait()
    return out


def render_still(seg, t):
    state = {}
    try:
        return render_frame(seg, t, state).convert("RGB")
    finally:
        for v in state.values():
            if isinstance(v, K.ClipReader):
                v.close()


def timeline(segments):
    t, out = 0.0, []
    for s in segments:
        out.append(t)
        t += seg_frames(s) / FPS
    return out, t


def audio_events(segments, starts):
    hits, clicks, whooshes, bells, risers = [], [], [], [], []
    for s, t0 in zip(segments, starts):
        if s.get("hit"):
            hits.append(t0 + 0.05)
        if s.get("hit_at") is not None:
            hits.append(t0 + s["hit_at"])
        if s.get("whoosh"):
            whooshes.append(t0)
        if s.get("bell"):
            bells.append((t0 + s["bell"][0], s["bell"][1]))
        if s.get("riser"):
            risers.append((t0 + s["dur"], s["riser"]))
        if s["kind"] == "scene":
            acc = 0.0
            for pd, src in s["parts"]:
                if src.get("type") == "still" and src.get("cursor"):
                    clicks += [t0 + acc + c for c in src["cursor"][1] if c < pd]
                if src.get("type") == "clip" and src.get("cursor"):
                    tc = K.TrackCursor(src["cursor"], CLIP_WINDOW, src["speed"], src["start"])
                    clicks += [t0 + acc + c for c in tc.clicks() if 0 <= c < pd]
                acc += pd
    return hits, clicks, whooshes, bells, risers


def make_audio(segments, starts, total, bpm, sections, path, seed):
    hits, clicks, whooshes, bells, risers = audio_events(segments, starts)
    log(f"music: {total:.1f}s at {bpm} bpm, {len(hits)} hits, {len(clicks)} clicks, {len(whooshes)} whooshes")
    mix = A.compose(total, bpm, sections, hits, clicks, whooshes, bells, risers, seed=seed)
    A.write_wav(path, mix)


def loudnorm(video, wav, out):
    """Two-pass EBU R128 normalisation to -16 LUFS, true peak -1.5 dB, muxed with the video."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    txt = r.stderr
    m = json.loads(txt[txt.rindex("{"): txt.rindex("}") + 1])
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", af + ",aresample=48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out],
                   check=True)


def build(name, segments, bpm, sections_fn, jobs, poster=None, seed=0):
    os.makedirs(K.WORK, exist_ok=True)
    starts, total = timeline(segments)
    log(f"{name}: {len(segments)} segments, {total:.1f} s")
    work = os.path.join(K.WORK, name)
    os.makedirs(work, exist_ok=True)
    job_list = [(i, s, os.path.join(work, f"seg{i:03d}.mp4"), poster if i == 0 else None) for i, s in enumerate(segments)]
    t0 = time.time()
    # longest first, so the pool ends together
    order = sorted(job_list, key=lambda j: -seg_frames(j[1]) * (3 if j[1]["kind"] in ("scene", "hero") else 1))
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for out in pool.map(render_segment, order):
            log(f"  {os.path.basename(out)} ({time.time() - t0:.0f}s)")
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for _, _, out, _ in job_list:
            f.write(f"file '{out}'\n")
    silent = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    wav = os.path.join(work, "music.wav")
    make_audio(segments, starts, total, bpm, sections_fn(segments, starts, total), wav, seed)
    out = os.path.join(K.VIDEO, f"brasshaven-{name}.mp4")
    loudnorm(silent, wav, out)
    log(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB) in {time.time() - t0:.0f}s")
    return out


def discord(src, out):
    """The guide at 1280x720 in two-pass H.264, at the bitrate that lands just under DISCORD_MB."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True, check=True).stdout)
    audio_k = 80
    target = DISCORD_MB * 1e6
    for attempt in range(3):
        video_k = int(target * 8 / dur / 1000 * 0.97) - audio_k  # 3 % for the container
        passlog = os.path.join(K.WORK, "discord-pass")
        common = ["-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_k}k",
                  "-maxrate", f"{int(video_k * 1.8)}k", "-bufsize", f"{video_k * 4}k", "-pix_fmt", "yuv420p",
                  "-r", str(FPS), "-passlogfile", passlog]
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + common + ["-pass", "1", "-an", "-f", "mp4", os.devnull],
                       check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + common +
                       ["-pass", "2", "-c:a", "aac", "-b:a", f"{audio_k}k", "-movflags", "+faststart", out], check=True)
        size = os.path.getsize(out)
        log(f"wrote {out} ({size / 1e6:.1f} MB, video {video_k} kb/s)")
        if size <= DISCORD_MB * 1e6:
            return out
        target *= DISCORD_MB * 1e6 / size * 0.98
    sys.exit(f"{out} is still over {DISCORD_MB} MB")


def guide_sections(segments, starts, total):
    """Music levels: calm under the install chapter, full under the gameplay."""
    sec = []
    for s, t0 in zip(segments, starts):
        ch = s.get("chapter") or ""
        lvl = 1 if ch.startswith("1") or s["kind"] in ("hero",) else 2
        if s["kind"] == "outro":
            lvl = 1
        sec.append((t0, t0 + s["dur"], lvl))
    return sec


def stills(name, segments):
    out = os.path.join(K.VIDEO, "stills")
    os.makedirs(out, exist_ok=True)
    for i, s in enumerate(segments):
        times = sorted({0.12, min(s["dur"] - 0.05, max(0.4, s["dur"] * 0.5)), s["dur"] - 0.12})
        if s["kind"] == "scene" and len(s["parts"]) > 1:
            acc = 0
            for pd, _ in s["parts"][:-1]:
                acc += pd
                times.append(acc - 0.06)
                times.append(acc + 0.4)
        for c in s.get("captions", []):
            times.append(min(s["dur"] - 0.05, c[0] + 0.8))
        for t in sorted(set(round(x, 2) for x in times)):
            img = render_still(s, t)
            img.save(os.path.join(out, f"{name}-{i:02d}-{s['kind']}-{t:05.2f}.png"))
    log(f"stills in {out}")


def poster_frame(segments, path, which=-1, t=None):
    seg = segments[which]
    t = seg["dur"] - 1.2 if t is None else t
    img = render_still(seg, t)
    img.save(path, quality=92)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true", help="download the CI screenshots, biome renders and showcase clips")
    ap.add_argument("--stills", action="store_true", help="only render inspection frames to build/video/stills")
    ap.add_argument("--jobs", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    args = ap.parse_args()
    if args.fetch:
        fetch()
        return
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} is needed")
    os.makedirs(K.VIDEO, exist_ok=True)
    clips = load_clips()
    log(f"real footage: {len(clips)} clips ({', '.join(sorted(clips)) or 'none: stills only'})")
    if not os.path.isdir(K.RENDERS):
        log("warning: no build/wiki/img/s (python3 tools/gen_wiki.py): the structure stills are missing")
    videos = [("guide", guide_segments(), GUIDE_BPM, guide_sections, 1)]
    for name, segs, bpm, sections, seed in videos:
        check_reading(segs, name)
        if args.stills:
            stills(name, segs)
            continue
        poster_frame(segs, os.path.join(K.VIDEO, "brasshaven-guide.jpg"), which=0, t=3.0)
        full = build(name, segs, bpm, sections, args.jobs, seed=seed)
        discord(full, os.path.join(K.VIDEO, "brasshaven-guide-discord.mp4"))


if __name__ == "__main__":
    main()

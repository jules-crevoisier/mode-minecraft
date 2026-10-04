"""World map and minimap: UI text (FR/EN), the brass frame / marker sprites, and review mockups.

gen_gui.py calls sprites() to draw the GUI-atlas sprites under textures/gui/sprites/map/ and, with --mockup,
mockups() to render build/previews/gui/minimap.png and worldmap.png with a fake terrain. gen_assets.py merges
lang() into the lang files. The Java side lives in client/map (drawing) and map/ (server: shared exploration,
waypoints, pings).
"""
import json
import math
import os
import random

# ------------------------------------------------------------------ text
UI = {
    "key.wayfarers.world_map": ("World map", "Carte du monde"),
    "key.wayfarers.toggle_minimap": ("Show/hide the minimap (Shift: its size)", "Afficher/masquer la mini-carte (Maj : sa taille)"),
    "message.wayfarers.minimap.size": ("Minimap: %s (%s px) - Shift + %s again: next size",
                                       "Mini-carte : %s (%s px) - Maj + %s encore : taille suivante"),
    "message.wayfarers.minimap.shown": ("Minimap shown - Shift + %s: change its size",
                                        "Mini-carte affichée - Maj + %s : changer sa taille"),
    "message.wayfarers.minimap.hidden": ("Minimap hidden - %s to show it again", "Mini-carte masquée - %s pour la réafficher"),
    "message.wayfarers.minimap.zoom": ("Minimap zoom: %s", "Zoom de la mini-carte : %s"),
    "key.wayfarers.minimap_zoom": ("Minimap zoom", "Zoom de la mini-carte"),
    "key.wayfarers.map_ping": ("Ping the spot you look at", "Signaler l'endroit visé"),
    "message.wayfarers.map.ping": ("%s marked a point (%s, %s)", "%s a signalé un point (%s, %s)"),
    "message.wayfarers.map.too_many": ("You already have %s waypoints: delete some first.",
                                       "Tu as déjà %s repères : supprimes-en d'abord."),
    "gui.wayfarers.map.title": ("World Map", "Carte du monde"),
    "gui.wayfarers.map.spawn": ("World spawn", "Point d'apparition du monde"),
    "gui.wayfarers.map.death": ("Last death", "Dernière mort"),
    "gui.wayfarers.map.grave": ("Your grave", "Ta tombe"),
    "gui.wayfarers.map.structure": ("Found with a compass", "Trouvée à la boussole"),
    "gui.wayfarers.map.target": ("Compass target", "Cible de la boussole"),
    "gui.wayfarers.map.shared": ("Shared", "Partagé"),
    "gui.wayfarers.map.by": ("Shared by %s", "Partagé par %s"),
    "gui.wayfarers.map.cave_view": ("Cave view", "Vue des grottes"),
    "gui.wayfarers.map.center": ("Centre on me (Space)", "Centrer sur moi (Espace)"),
    "gui.wayfarers.map.zoom_in": ("Zoom in (wheel, +)", "Zoomer (molette, +)"),
    "gui.wayfarers.map.zoom_out": ("Zoom out (wheel, -)", "Dézoomer (molette, -)"),
    "gui.wayfarers.map.cave_on": ("Cave view when underground: on", "Vue des grottes sous terre : activée"),
    "gui.wayfarers.map.cave_off": ("Cave view when underground: off", "Vue des grottes sous terre : désactivée"),
    "gui.wayfarers.map.sidebar": ("Legend and waypoints", "Légende et repères"),
    "gui.wayfarers.map.cursor": ("X %s  Y %s  Z %s  -  %s", "X %s  Y %s  Z %s  -  %s"),
    "gui.wayfarers.map.cursor_unknown": ("X %s  Z %s  -  unexplored", "X %s  Z %s  -  inexploré"),
    "gui.wayfarers.map.hint": ("Drag: move - Wheel: zoom - Right-click: waypoint - Middle-click: ping",
                               "Glisser : déplacer - Molette : zoom - Clic droit : repère - Clic molette : signal"),
    "gui.wayfarers.map.scale_in": ("1 block = %s px", "1 bloc = %s px"),
    "gui.wayfarers.map.scale_out": ("1 px = %s blocks", "1 px = %s blocs"),
    "gui.wayfarers.map.legend": ("Legend", "Légende"),
    "gui.wayfarers.map.waypoints": ("Waypoints", "Repères"),
    "gui.wayfarers.map.no_waypoints": ("No waypoint here yet: right-click the map to add one.",
                                       "Aucun repère ici : clic droit sur la carte pour en poser un."),
    "gui.wayfarers.map.add_here": ("+ Waypoint here", "+ Repère ici"),
    "gui.wayfarers.map.edit": ("Edit", "Modifier"),
    "gui.wayfarers.map.share": ("Share", "Partager"),
    "gui.wayfarers.map.make_private": ("Private", "Privé"),
    "gui.wayfarers.map.delete": ("Delete", "Supprimer"),
    "gui.wayfarers.map.add_waypoint": ("Add a waypoint here", "Poser un repère ici"),
    "gui.wayfarers.map.ping": ("Ping this spot for everyone", "Signaler cet endroit à tous"),
    "gui.wayfarers.map.copy": ("Copy the coordinates", "Copier les coordonnées"),
    "gui.wayfarers.map.name": ("Name", "Nom"),
    "gui.wayfarers.map.default_name": ("Waypoint %s, %s", "Repère %s, %s"),
    "gui.wayfarers.map.new_waypoint": ("New waypoint", "Nouveau repère"),
    "gui.wayfarers.map.edit_waypoint": ("Edit waypoint", "Modifier le repère"),
    "gui.wayfarers.map.share_toggle": ("Share with everyone", "Partager avec tout le monde"),
    "gui.wayfarers.map.save": ("Save", "Enregistrer"),
}
KINDS = {
    # kind: (legend en, legend fr, card en, card fr)
    "player": ("Players", "Joueurs", "Player", "Joueur"),
    "waypoint": ("Waypoints", "Repères", "Waypoint", "Repère"),
    "waystone": ("Waystones", "Pierres de voyage", "Waystone", "Pierre de voyage"),
    "ping": ("Pings", "Signaux", "Ping", "Signal"),
    "target": ("Compass target", "Cible de boussole", "Compass target", "Cible de boussole"),
    "structure": ("Structures", "Structures", "Structure", "Structure"),
    "grave": ("Graves", "Tombes", "Grave", "Tombe"),
    "death": ("Last death", "Dernière mort", "Last death", "Dernière mort"),
    "spawn": ("Spawn", "Apparition", "World spawn", "Apparition du monde"),
}


def lang():
    en = {k: v[0] for k, v in UI.items()}
    fr = {k: v[1] for k, v in UI.items()}
    for k, (le, lf, ce, cf) in KINDS.items():
        en[f"gui.wayfarers.map.kind.{k}"], fr[f"gui.wayfarers.map.kind.{k}"] = le, lf
        en[f"gui.wayfarers.map.one.{k}"], fr[f"gui.wayfarers.map.one.{k}"] = ce, cf
    return en, fr


# ------------------------------------------------------------------ sprites
# Map diameters inside the frame of WayfarersClientConfig.MinimapSize (56, 68, 96 and 128 px on screen with the
# 6 px frame): one round frame sprite per size, drawn pixel for pixel so it stays crisp at any GUI scale.
MINIMAP_SIZES = (44, 56, 84, 116)
BORDER = 6


def _save_tile(g, s, name):
    s.save(name)
    path = os.path.join(g.OUT, name + ".png.mcmeta")
    with open(path, "w") as f:
        json.dump({"gui": {"scaling": {"type": "tile", "width": s.w, "height": s.h}}}, f, indent=2)


def _round_frame(g, size):
    """Square riveted iron plate with a round brass porthole of diameter ``size`` (the map shows through)."""
    n = size + BORDER * 2
    s = g.Sprite(n, n)
    c = (n - 1) / 2.0
    r = size / 2.0
    rng = random.Random(size)
    lx, ly = -0.70710678, -0.70710678  # light from the top left
    for y in range(n):
        for x in range(n):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            if d < r - 0.35:
                continue  # the hole
            nx, ny = (dx / d, dy / d) if d else (0, 0)
            lit = nx * lx + ny * ly  # 1 = faces the light
            if d < r + 0.65:
                col = g.SOOT
            elif d < r + 1.65:
                # inner lip: lit on the far side (it is a hole)
                col = g.mix(g.BRASS_SH, g.BRASS_DK, 0.5 - lit * 0.5)
            elif d < r + 4.6:
                t = (d - r - 1.65) / 3.0  # 0 inner .. 1 outer
                base = g.mix(g.BRASS_LT, g.BRASS, t)
                col = g.mix(base, g.BRASS_HI if lit > 0 else g.BRASS_DK, abs(lit) * 0.55)
            elif d < r + 5.6:
                col = g.SOOT
            else:
                # iron plate
                v = rng.random()
                col = g.IRON if v > 0.2 else g.mix(g.IRON, g.IRON_LT if v > 0.1 else g.IRON_DK, 0.6)
            s.set(x, y, col)
    # ticks on the ring every 30 degrees (cardinal studs sit on 0/90/180/270)
    for k in range(12):
        if k % 3 == 0:
            continue
        a = k * math.pi / 6
        for rr in (r + 2.6, r + 3.6):
            s.set(int(round(c + math.sin(a) * rr)), int(round(c - math.cos(a) * rr)), g.BRASS_SH)
    # plate edge and rivets
    s.frame(0, 0, n - 1, n - 1, g.SOOT)
    s.bevel(1, 1, n - 2, n - 2, g.IRON_LT, g.IRON_DK)
    for x, y in ((2, 2), (n - 4, 2), (2, n - 4), (n - 4, n - 4)):
        s.rivet(x, y)
    s.save(f"map/frame_round_{size}")


def _square_frame(g):
    s = g.Sprite(32, 32)
    s.frame(0, 0, 31, 31, g.SOOT)
    g.brass_band(s, 1, 1, 30, 30, 4)
    s.frame(5, 5, 26, 26, g.SOOT)
    for x, y in ((1, 1), (29, 1), (1, 29), (29, 29)):
        s.rivet(x, y)
    s.save("map/frame_square", nine=6)


def _plate(g):
    s = g.Sprite(16, 12)
    s.rect(0, 0, 15, 11, g.hexc("1D1714", 228))
    s.frame(0, 0, 15, 11, g.BRASS_DK)
    s.bevel(1, 1, 14, 10, g.hexc("3E3430", 228), g.hexc("120E0C", 228))
    s.save("map/plate", nine=3)


def _parchment(g):
    """Tileable parchment for the unexplored world, with faint fibres and stains (wrapping around the edges)."""
    n = 64
    s = g.Sprite(n, n)
    rng = random.Random(7)
    base = [[0.0] * n for _ in range(n)]
    for _ in range(9):
        cx, cy, rad, k = rng.random() * n, rng.random() * n, 5 + rng.random() * 12, 0.08 + rng.random() * 0.1
        for y in range(n):
            for x in range(n):
                dx = min(abs(x - cx), n - abs(x - cx))
                dy = min(abs(y - cy), n - abs(y - cy))
                d = math.hypot(dx, dy)
                if d < rad:
                    base[y][x] += k * (1 - d / rad)
    for y in range(n):
        for x in range(n):
            t = min(0.9, base[y][x] + (rng.random() * 0.12))
            col = g.mix(g.hexc("E8D7AE"), g.hexc("C9B184"), t)
            s.set(x, y, col)
    for _ in range(22):  # fibres
        x, y = rng.randrange(n), rng.randrange(n)
        length = rng.randint(2, 6)
        horiz = rng.random() < 0.6
        for i in range(length):
            xx, yy = (x + i) % n if horiz else x, y if horiz else (y + i) % n
            s.set(xx, yy, g.mix(s.px[xx, yy], g.PARCH_EDGE, 0.35))
    _save_tile(g, s, "map/parchment")


def _art(g, name, rows, colors):
    w, h = len(rows[0]), len(rows)
    s = g.Sprite(w, h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set(x, y, colors[ch])
    s.save(name)


ARROW = [
    "......o......",
    ".....owo.....",
    ".....owr.....",
    "....owwro....",
    "....owwro....",
    "...owwwrro...",
    "...owwwrro...",
    "..owwwwrrro..",
    "..owwwwrrro..",
    ".owwwwwrrrro.",
    ".owwwoooorro.",
    "owwoo...oorro",
    "ooo.......ooo",
]
MARKERS = {
    "waystone": ([
        "....o....",
        "...ohc...",
        "..ohhcc..",
        "..ohccd..",
        ".ohhccdd.",
        "..occdd..",
        "..ocddo..",
        "...odo...",
        "...ooo...",
    ], {"o": "0F0C0A", "h": "E8FBFF", "c": "6FD8FF", "d": "2F7FA8"}),
    "ping": ([
        "...ooo...",
        "..oyyyo..",
        ".oyywyyo.",
        "oyyywyyyo",
        "oyyywyyyo",
        "oyyyyyyyo",
        ".oyywyyo.",
        "..oyyyo..",
        "...ooo...",
    ], {"o": "0F0C0A", "y": "FF7A3C", "w": "FFF4E8"}),
    "target": ([
        "...ooo...",
        "..obbbo..",
        ".ob.w.bo.",
        "ob..w..bo",
        "obwwwwwbo",
        "ob..w..bo",
        ".ob.w.bo.",
        "..obbbo..",
        "...ooo...",
    ], {"o": "0F0C0A", "b": "3FD0FF", "w": "E8FBFF"}),
    "structure": ([
        "o.o.o.o..",
        "oyoyoyo..",
        "oyyyyyo..",
        ".oyddo...",
        ".oydyo...",
        ".oyddo...",
        ".oydyo...",
        "oyyyyyo..",
        "ooooooo..",
    ], {"o": "0F0C0A", "y": "F6C343", "d": "8C5A1A"}),
    "grave": ([
        "..ooooo..",
        ".ohhhhgo.",
        ".ohhdhgo.",
        ".ohdddgo.",
        ".ohhdhgo.",
        ".ohhdhgo.",
        ".ohhhhgo.",
        "ooggggggo",
        "ooooooooo",
    ], {"o": "0F0C0A", "h": "C8C2B8", "g": "8A8378", "d": "4A443C"}),
    "death": ([
        "..ooooo..",
        ".owwwwwo.",
        "owwwwwwwo",
        "owkkwkkwo",
        "owkkwkkwo",
        "owwwkwwwo",
        ".owwwwwo.",
        "..owkwo..",
        "..ooooo..",
    ], {"o": "0F0C0A", "w": "F4F1E8", "k": "C0392B"}),
    "spawn": ([
        "....o....",
        "...oro...",
        "..orrro..",
        ".orrrrro.",
        "ooooooooo",
        ".owwwwwo.",
        ".owwdwwo.",
        ".owwdwwo.",
        ".ooooooo.",
    ], {"o": "0F0C0A", "r": "E0483B", "w": "F3E3C0", "d": "6E5A40"}),
    "player": ([
        "..ooooo..",
        ".owwwwwo.",
        "owwwwwwwo",
        "owwwwwwwo",
        "owwwwwwwo",
        "owwwwwwwo",
        "owwwwwwwo",
        ".owwwwwo.",
        "..ooooo..",
    ], {"o": "0F0C0A", "w": "9FE6FF"}),
}
# white art, tinted with the waypoint colour in game (dark outlines stay dark)
WAYPOINT_ICONS = {
    "flag": [
        ".oo......",
        ".owooooo.",
        ".owwwwwwo",
        ".owwhwwwo",
        ".owwwwwwo",
        ".owooooo.",
        ".oo......",
        ".oo......",
        "oooo.....",
    ],
    "house": [
        "....o....",
        "...owo...",
        "..owwwo..",
        ".owwwwwo.",
        "ooooooooo",
        ".owwwwwo.",
        ".owwowwo.",
        ".owwowwo.",
        ".ooooooo.",
    ],
    "star": [
        "....o....",
        "...owo...",
        "ooowwwooo",
        "owwwwwwwo",
        ".owwwwwo.",
        "..owwwo..",
        ".owwowwo.",
        ".owo.owo.",
        ".oo...oo.",
    ],
    "mine": [
        "..oooo...",
        ".owwwwo..",
        "owoooowo.",
        "oo..odowo",
        "...odo.oo",
        "..odo....",
        ".odo.....",
        "odo......",
        "oo.......",
    ],
    "skull": [
        "..ooooo..",
        ".owwwwwo.",
        "owwwwwwwo",
        "owoowoowo",
        "owoowoowo",
        "owwwowwwo",
        ".owwwwwo.",
        "..owowo..",
        "..ooooo..",
    ],
    "chest": [
        ".......  ",
        "ooooooooo",
        "owwwwwwwo",
        "owwwwwwwo",
        "oooowoooo",
        "owwoyowwo",
        "owwwwwwwo",
        "owwwwwwwo",
        "ooooooooo",
    ],
}
CARDINALS = {
    "n": ["o..o", "oo.o", "o.oo", "o..o", "o..o"],
    "e": ["ooo", "o..", "oo.", "o..", "ooo"],
    "s": [".oo", "o..", ".o.", "..o", "oo."],
    "w": ["o...o", "o...o", "o.o.o", "o.o.o", ".o.o."],
}
GLYPHS = {
    "center": [
        "....kk....",
        "....kk....",
        "..kkkkkk..",
        "..k....k..",
        "kkk.kk.kkk",
        "kkk.kk.kkk",
        "..k....k..",
        "..kkkkkk..",
        "....kk....",
        "....kk....",
    ],
    "zoom_in": [
        "..........",
        "....kk....",
        "....kk....",
        "....kk....",
        ".kkkkkkkk.",
        ".kkkkkkkk.",
        "....kk....",
        "....kk....",
        "....kk....",
        "..........",
    ],
    "zoom_out": [
        "..........",
        "..........",
        "..........",
        "..........",
        ".kkkkkkkk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
        "..........",
        "..........",
    ],
    "cave": [
        "..........",
        "...kkkk...",
        "..kk..kk..",
        ".kk....kk.",
        ".k......k.",
        "kk..kk..kk",
        "k..kkkk..k",
        "k.kkkkkk.k",
        "kkkkkkkkkk",
        "..........",
    ],
    "list": [
        "..........",
        "kk.kkkkkkk",
        "..........",
        "kk.kkkkkkk",
        "..........",
        "kk.kkkkkkk",
        "..........",
        "kk.kkkkkkk",
        "..........",
        "..........",
    ],
}


def sprites(g):
    """Draws every map sprite with gen_gui's helpers (``g`` is the gen_gui module)."""
    for size in MINIMAP_SIZES:
        _round_frame(g, size)
    _square_frame(g)
    _plate(g)
    _parchment(g)
    _art(g, "map/arrow", ARROW, {"o": g.SOOT, "w": g.hexc("FFF8EC"), "r": g.hexc("E0483B")})
    for name, (rows, cols) in MARKERS.items():
        _art(g, "map/marker/" + name, rows, {k: g.hexc(v) for k, v in cols.items()})
    for name, rows in WAYPOINT_ICONS.items():
        _art(g, "map/wp/" + name, rows, {"o": g.hexc("1A1410"), "w": g.hexc("FFFFFF"), "h": g.hexc("D8D8D8"),
                                         "d": g.hexc("8A7A66"), "y": g.hexc("F6C343")})
    for name, rows in CARDINALS.items():
        s = g.Sprite(9, 9)
        disc = ["..ooooo..", ".obbbbbo.", "obbbbbbbo", "obbbbbbbo", "obbbbbbbo", "obbbbbbbo", "obbbbbbbo", ".obbbbbo.",
                "..ooooo.."]
        for y, row in enumerate(disc):
            for x, ch in enumerate(row):
                if ch == "o":
                    s.set(x, y, g.SOOT)
                elif ch == "b":
                    s.set(x, y, g.mix(g.BRASS_HI, g.BRASS, (x + y) / 16))
        ink = g.hexc("C0392B") if name == "n" else g.hexc("2B1B0C")
        if name == "n":
            for y, row in enumerate(disc):
                for x, ch in enumerate(row):
                    if ch == "b":
                        s.set(x, y, g.mix(g.hexc("FFE9A8"), g.BRASS_LT, (x + y) / 16))
        ox = (9 - len(rows[0])) // 2
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "o":
                    s.set(x + ox, y + 2, ink)
        s.save("map/cardinal_" + name)
    for name, rows in GLYPHS.items():
        _art(g, "map/glyph/" + name, rows, {"k": g.hexc("2B1B0C")})


# ------------------------------------------------------------------ mockups (fake terrain)
def _noise(seed, w, h, cell):
    rng = random.Random(seed)
    gw, gh = w // cell + 2, h // cell + 2
    grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def at(x, y):
        gx, gy = x / cell, y / cell
        x0, y0 = int(gx), int(gy)
        tx, ty = gx - x0, gy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = grid[y0][x0] * (1 - tx) + grid[y0][x0 + 1] * tx
        b = grid[y0 + 1][x0] * (1 - tx) + grid[y0 + 1][x0 + 1] * tx
        return a * (1 - ty) + b * ty
    return at


def fake_world(w, h, seed=3):
    """{(x, z): (rgb, height, depth)} for a w x h block area: sea, beaches, plains, forest, hills, snow."""
    n1, n2, n3 = _noise(seed, w, h, 64), _noise(seed + 1, w, h, 24), _noise(seed + 2, w, h, 9)
    forest = _noise(seed + 3, w, h, 30)
    out = {}
    for z in range(h):
        for x in range(w):
            e = n1(x, z) * 0.62 + n2(x, z) * 0.28 + n3(x, z) * 0.10
            hgt = int(40 + e * 70)
            if hgt < 62:
                depth = 62 - hgt
                water = (0x3F, 0x76, 0xE4)
                water = tuple(int(c * 0.86) for c in water)
                if depth <= 2:
                    sand = (0xF7, 0xE9, 0xA3)
                    water = tuple(int(water[i] * 0.66 + sand[i] * 0.34) for i in range(3))
                out[(x, z)] = (water, 62, depth)
            elif hgt < 64:
                out[(x, z)] = ((0xF7, 0xE9, 0xA3), hgt, 0)
            elif hgt < 90:
                if forest(x, z) > 0.58 and (x * 7 + z * 13) % 5:
                    out[(x, z)] = ((0x36, 0x86, 0x12), hgt + 5, 0)
                else:
                    out[(x, z)] = ((0x7D, 0xA2, 0x4C), hgt, 0)
            elif hgt < 100:
                out[(x, z)] = ((0x70, 0x70, 0x70), hgt, 0)
            else:
                out[(x, z)] = ((0xFF, 0xFF, 0xFF), hgt, 0)
    return out


def shade(world, x, z):
    rgb, hgt, depth = world[(x, z)]
    if depth:
        f = 1 - min(depth, 24) * 0.016 - (0.02 if depth > 1 and (x + z) % 2 == 0 else 0)
    else:
        hn = world.get((x, z - 1), (None, hgt, 0))[1]
        hw = world.get((x - 1, z), (None, hgt, 0))[1]
        slope = (hgt - hn) * 2 + (hgt - hw)
        f = 1 + max(-0.34, min(0.24, slope * 0.045))
    return tuple(max(0, min(255, int(c * f))) for c in rgb) + (255,)


def mockups(g):
    from PIL import Image
    os.makedirs(g.PREVIEW, exist_ok=True)
    world = fake_world(420, 300)
    _mock_minimap(g, world, Image)
    _mock_worldmap(g, world, Image)


def _terrain(world, Image, x0, z0, w, h, scale, known=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for sy in range(h):
        for sx in range(w):
            wx, wz = int(x0 + sx / scale), int(z0 + sy / scale)
            if (wx, wz) in world and (known is None or known(wx, wz)):
                px[sx, sy] = shade(world, wx, wz)
    return im


def draw_minimap(g, m, world, x, y, size, square=False, coords=("212, 71, -148", "Plaines"), right=False, zoom=1.0,
                 opacity=1.0):
    """The minimap as MinimapHud draws it, on mockup ``m`` at (x, y): ``size`` is the map inside the 6 px frame.
    Returns the height taken (frame and coordinates plate)."""
    from PIL import Image, ImageChops
    outer = size + BORDER * 2
    back = Image.new("RGBA", (size, size), (0x2A, 0x22, 0x1C, int(255 * opacity)))
    terr = _terrain(world, Image, 210 - size / 2 / zoom, 150 - size / 2 / zoom, size, size, zoom)
    if opacity < 1:
        terr.putalpha(terr.getchannel("A").point(lambda a: int(a * opacity)))
    m.im.alpha_composite(back, (x + BORDER, y + BORDER))
    m.im.alpha_composite(terr, (x + BORDER, y + BORDER))
    cx, cy = x + BORDER + size // 2, y + BORDER + size // 2
    k = size / 96
    for name, dx, dy in (("waystone", -20, -30), ("ping", 26, 14), ("spawn", -36, 22), ("grave", 10, -12)):
        dx, dy = int(dx * k), int(dy * k)
        m.im.alpha_composite(Image.open(g.sp("map/marker/" + name)).convert("RGBA"), (cx + dx - 4, cy + dy - 4))
    arrow = Image.open(g.sp("map/arrow")).convert("RGBA").rotate(-35, resample=Image.NEAREST)
    m.im.alpha_composite(arrow, (cx - 6, cy - 6))
    if square:
        m.nine("map/frame_square", x, y, outer, outer, 6)
    else:
        m.im.alpha_composite(Image.open(g.sp(f"map/frame_round_{size}")).convert("RGBA"), (x, y))
    for i, n in enumerate("nesw"):
        a = i * math.pi / 2
        dx, dy = math.sin(a), -math.cos(a)
        r = size / 2 + 3
        if square:
            r /= max(abs(dx), abs(dy))
        m.im.alpha_composite(Image.open(g.sp("map/cardinal_" + n)).convert("RGBA"),
                             (int(round(x + BORDER + size / 2 + dx * r)) - 4, int(round(y + BORDER + size / 2 + dy * r)) - 4))
    if not coords:
        return outer
    # the compact plate: as wide as its text (at least the map), on the screen-edge side
    ty = y + outer + 1
    tw = max(outer, max(g.text_width(coords[0]), g.text_width(coords[1])) + 8)
    tx = x + outer - tw if right else x
    m.nine("map/plate", tx, ty, tw, 20, 3)
    m.text(coords[0], tx + tw // 2, ty + 2, g.CREAM, center=True)
    m.text(coords[1], tx + tw // 2, ty + 11, g.CREAM_SOFT, center=True)
    return outer + 21


def _mock_minimap(g, world, Image):
    """minimap.png: the four sizes side by side (56, 68 by default, 96 and 128 px on screen), the square frame and
    a faded one (opacity 60 %), over a stand-in game view."""
    W, H = 470, 180
    m = g.Mock(W, H)
    for y in range(H):
        for x in range(W):
            m.im.putpixel((x, y), (int(110 + y * 0.3), int(160 + y * 0.2), 220, 255) if y < 80 else (70, 104, 50, 255))
    x = 4
    labels = ("Petite 56", "Moyenne 68", "Grande 96", "Énorme 128")
    for size, label in zip(MINIMAP_SIZES, labels):
        draw_minimap(g, m, world, x, 4, size)
        m.text(label, x + (size + 12) // 2, H - 12, g.CREAM, center=True)
        x += size + 12 + 10
    m.save("minimap")
    m = g.Mock(200, 110)
    for y in range(110):
        for x in range(200):
            m.im.putpixel((x, y), (int(110 + y * 0.3), int(160 + y * 0.2), 220, 255) if y < 50 else (70, 104, 50, 255))
    draw_minimap(g, m, world, 4, 4, 56, square=True, zoom=2.0)
    draw_minimap(g, m, world, 100, 4, 56, opacity=0.6, coords=("-1732, 129, -461", "Champs fleuris"))
    m.save("minimap_variants")


def _mock_worldmap(g, world, Image):
    from PIL import ImageChops
    W, H = 480, 270
    m = g.Mock(W, H)
    m.im.paste((26, 20, 16, 255), (0, 0, W, H))
    m.nine("panel", 4, 6, W - 8, H - 10, 9)
    m.nine("title_plate", W // 2 - 50, 1, 100, 18, 6)
    m.text("Carte du monde", W // 2, 6, g.PLATE_INK, shadow=False, center=True, bold=True)
    sb = 116
    mx0, my0, mx1, my1 = 18, 24, W - 18 - sb - 6, H - 30
    par = Image.open(g.sp("map/parchment")).convert("RGBA")
    for yy in range(my0, my1, 64):
        for xx in range(mx0, mx1, 64):
            piece = par.crop((0, 0, min(64, mx1 - xx), min(64, my1 - yy)))
            m.im.alpha_composite(piece, (xx, yy))
    # explored: a blob around the centre
    cxw, czw = 210, 150
    scale = 1.0

    def known(x, z):
        return math.hypot(x - cxw, (z - czw) * 1.3) < 120 + 25 * math.sin(x * 0.05) or abs(z - 150) < 8
    terr = _terrain(world, Image, cxw - (mx1 - mx0) / 2 / scale, czw - (my1 - my0) / 2 / scale, mx1 - mx0, my1 - my0, scale, known)
    m.im.alpha_composite(terr, (mx0, my0))
    for gx in range(mx0 + 40, mx1, 128):
        for yy in range(my0, my1):
            m.im.alpha_composite(Image.new("RGBA", (1, 1), (0, 0, 0, 40)), (gx, yy))
    cx, cy = (mx0 + mx1) // 2, (my0 + my1) // 2
    marks = [("waystone", -60, -40, "Avant-poste de la Guilde"), ("structure", 70, 30, "Monastère des cimes"),
             ("spawn", -20, 60, None), ("ping", 40, -50, None), ("player", 30, 10, None)]
    for name, dx, dy, label in marks:
        m.im.alpha_composite(Image.open(g.sp("map/marker/" + name)).convert("RGBA"), (cx + dx - 4, cy + dy - 4))
        if label and name == "waystone":
            w_ = g.text_width(label)
            m.im.alpha_composite(Image.new("RGBA", (int(w_) + 4, 10), (16, 12, 10, 144)), (int(cx + dx - w_ / 2 - 2), cy + dy + 6))
            m.text(label, cx + dx, cy + dy + 7, g.AETHER_TXT, center=True)
    for icon, col, dx, dy, label in (("house", (0xF6, 0xC3, 0x43), -100, 20, "Base"), ("mine", (0x3F, 0xA9, 0xFF), 90, -70, "Mine de fer")):
        wp = Image.open(g.sp("map/wp/" + icon)).convert("RGBA")
        m.im.alpha_composite(ImageChops.multiply(wp, Image.new("RGBA", wp.size, col + (255,))), (cx + dx - 4, cy + dy - 4))
        w_ = g.text_width(label)
        m.im.alpha_composite(Image.new("RGBA", (int(w_) + 4, 10), (16, 12, 10, 144)), (int(cx + dx - w_ / 2 - 2), cy + dy + 6))
        m.text(label, cx + dx, cy + dy + 7, col + (255,), center=True)
    m.im.alpha_composite(Image.open(g.sp("map/arrow")).convert("RGBA"), (cx - 6, cy - 6))
    m.nine("map/frame_square", mx0 - 4, my0 - 4, mx1 - mx0 + 8, my1 - my0 + 8, 6)
    for i, glyph in enumerate(("center", "zoom_in", "zoom_out", "cave", "list")):
        bx, by = mx1 - 20, my0 + 4 + i * 19
        m.nine("button_small", bx, by, 16, 16, 3)
        m.im.alpha_composite(Image.open(g.sp("map/glyph/" + glyph)).convert("RGBA"), (bx + 3, by + 3))
    m.text("X 231  Y 68  Z -164  -  Forêt", mx0, my1 + 7, g.INK, shadow=False)
    m.text("1 bloc = 1 px", mx1, my1 + 7, g.INK_SOFT, shadow=False, right=True)
    # sidebar
    sx, sw = mx1 + 6, W - 18 - (mx1 + 6)
    m.nine("inset", sx, my0 - 4, sw, my1 - my0 + 8, 4)
    m.text("Légende", sx + 6, my0 + 1, g.GOLD, bold=True)
    rows_ = [("player", "Joueurs"), ("waypoint", "Repères"), ("waystone", "Pierres de voyage"), ("ping", "Signaux"),
             ("target", "Cible de boussole"), ("structure", "Structures"), ("grave", "Tombes"), ("death", "Dernière mort"),
             ("spawn", "Apparition")]
    ly = my0 + 12
    for name, label in rows_:
        path = g.sp("map/wp/flag") if name == "waypoint" else g.sp("map/marker/" + name)
        ic = Image.open(path).convert("RGBA")
        if name == "waypoint":
            ic = ImageChops.multiply(ic, Image.new("RGBA", ic.size, (0xE0, 0x48, 0x3B, 255)))
        m.im.alpha_composite(ic, (sx + 6, ly + 1))
        m.text(label, sx + 18, ly + 2, g.CREAM if name != "grave" else g.MUTED)
        ly += 11
    ly += 8
    m.text("Repères", sx + 6, ly, g.GOLD, bold=True)
    ly += 11
    for icon, col, label, dist in (("house", (0xF6, 0xC3, 0x43), "Base", "112 m"), ("mine", (0x3F, 0xA9, 0xFF), "Mine de fer", "340 m"),
                                   ("star", (0x7C, 0xE3, 0x5A), "Village", "1.2 km")):
        wp = Image.open(g.sp("map/wp/" + icon)).convert("RGBA")
        m.im.alpha_composite(ImageChops.multiply(wp, Image.new("RGBA", wp.size, col + (255,))), (sx + 5, ly + 1))
        m.text(label, sx + 17, ly + 2, g.CREAM)
        m.text(dist, sx + sw - 6, ly + 2, g.CREAM_SOFT, right=True)
        ly += 12
    m.nine("button", sx + 4, my1 - 14, sw - 8, 14, 4)
    m.text("+ Repère ici", sx + sw // 2, my1 - 11, g.hexc("FFFFFF"), center=True)
    # card
    m.nine("card", mx0 + 6, my1 - 72, 168, 66, 4)
    wp = Image.open(g.sp("map/wp/mine")).convert("RGBA")
    m.im.alpha_composite(ImageChops.multiply(wp, Image.new("RGBA", wp.size, (0x3F, 0xA9, 0xFF, 255))), (mx0 + 12, my1 - 66))
    m.text("Mine de fer", mx0 + 25, my1 - 66, g.INK, shadow=False, bold=True)
    m.text("Repère - Partagé", mx0 + 12, my1 - 54, g.INK_SOFT, shadow=False)
    m.text("301, 12, -412   340 m", mx0 + 12, my1 - 42, g.INK_SOFT, shadow=False)
    for i, label in enumerate(("Modifier", "Privé", "Supprimer")):
        m.nine("button", mx0 + 11 + i * 53, my1 - 25, 50, 14, 4)
        m.text(label, mx0 + 36 + i * 53, my1 - 22, g.hexc("FFFFFF"), center=True)
    m.save("worldmap")

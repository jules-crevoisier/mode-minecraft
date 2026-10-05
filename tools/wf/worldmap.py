"""World map and minimap: UI text (FR/EN), the brass frame / marker sprites, and review mockups.

gen_gui.py calls sprites() to draw the GUI-atlas sprites under textures/gui/sprites/map/ and, with --mockup,
mockups() to render build/previews/gui/minimap*.png and worldmap*.png with a fake terrain: the same relief shading
(MapShade.java), round frame (MapFrames.java), vector arrow and marker sizes (MapRenderer.java), options panel and
3D view (WorldMapScreen.java, MapView3D.java) as the game. gen_assets.py merges lang() into the lang files. The Java
side lives in client/map (drawing) and map/ (server: shared exploration, waypoints, pings).
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
    "gui.wayfarers.map.view_3d": ("3D view", "Vue 3D"),
    "gui.wayfarers.map.view3d_on": ("3D view (tilted relief): on", "Vue 3D (relief incliné) : activée"),
    "gui.wayfarers.map.view3d_off": ("3D view (tilted relief): off", "Vue 3D (relief incliné) : désactivée"),
    "gui.wayfarers.map.options": ("Options: minimap size and look, map relief", "Options : taille et aspect de la mini-carte, relief des cartes"),
    "gui.wayfarers.map.options.title": ("Minimap", "Mini-carte"),
    "gui.wayfarers.map.options.size.tip": ("Its exact size on screen, frame included: 48 to 160 px. The minimap shows "
                                           "live in its corner while this panel is open.",
                                           "Sa taille exacte à l'écran, cadre compris : de 48 à 160 px. La mini-carte "
                                           "s'affiche en direct dans son coin tant que ce panneau est ouvert."),
    "gui.wayfarers.map.options.shown": ("Shown", "Affichée"),
    "gui.wayfarers.map.options.presets": ("Presets", "Préréglages"),
    "gui.wayfarers.map.options.rotate": ("Rotation", "Rotation"),
    "gui.wayfarers.map.options.relief_title": ("Map relief", "Relief des cartes"),
    "gui.wayfarers.map.options.relief": ("Relief", "Relief"),
    "gui.wayfarers.map.options.relief.flat": ("Flat", "Plat"),
    "gui.wayfarers.map.options.relief.flat.tip": ("Plain colours, no shading (water still darkens with depth).",
                                                  "Couleurs simples, sans ombrage (l'eau fonce toujours avec la profondeur)."),
    "gui.wayfarers.map.options.relief.normal": ("Normal", "Normal"),
    "gui.wayfarers.map.options.relief.normal.tip": ("Hills lit from the north-west, darker valleys, paler high ground.",
                                                    "Collines éclairées du nord-ouest, vallées plus sombres, hauteurs plus pâles."),
    "gui.wayfarers.map.options.relief.strong": ("Strong", "Fort"),
    "gui.wayfarers.map.options.relief.strong.tip": ("The same, deeper: every slope stands out.",
                                                    "Pareil, en plus marqué : chaque pente ressort."),
    "gui.wayfarers.map.options.contours": ("Contours", "Courbes"),
    "gui.wayfarers.map.options.contours.tip": ("Contour lines every 16 blocks of height, a bolder one every 64.",
                                               "Courbes de niveau tous les 16 blocs de hauteur, une plus marquée tous les 64."),
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
# Map diameters inside the 6 px frame for the presets of WayfarersClientConfig.MinimapSize (56, 68, 96 and 128 px on
# screen); the slider allows any outer size from 48 to 160 px in steps of 4. The round frame is not a sprite: the game
# draws it for the exact size (MapFrames.java), round_frame() below is the same drawing for the mockups.
MINIMAP_SIZES = (44, 56, 84, 116)
BORDER = 6


def _save_tile(g, s, name):
    s.save(name)
    path = os.path.join(g.OUT, name + ".png.mcmeta")
    with open(path, "w") as f:
        json.dump({"gui": {"scaling": {"type": "tile", "width": s.w, "height": s.h}}}, f, indent=2)


def round_frame(g, size):
    """Square riveted iron plate with a round brass porthole of diameter ``size`` (the map shows through): the
    same drawing as MapFrames.build() (the iron grain differs: Java hashes, this draws random numbers)."""
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
    return s


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


# the player arrow (MapRenderer.ARROW): tip, right barb, notch, left barb, in half-lengths, pointing up
ARROW = ((0.0, -1.0), (0.76, 0.92), (0.0, 0.44), (-0.76, 0.92))
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
    # 3D view: a block seen from above at a slant
    "view3d": [
        "....kk....",
        "..kk..kk..",
        "kk......kk",
        "kkkk..kkkk",
        "k..kkkk..k",
        "k...kk...k",
        "k...kk...k",
        "kk..kk..kk",
        "..kkkkkk..",
        "....kk....",
    ],
    # options: a gear
    "options": [
        "....kk....",
        ".k.kkkk.k.",
        "..kkkkkk..",
        ".kkk..kkk.",
        "kkk....kkk",
        "kkk....kkk",
        ".kkk..kkk.",
        "..kkkkkk..",
        ".k.kkkk.k.",
        "....kk....",
    ],
}


def sprites(g):
    """Draws every map sprite with gen_gui's helpers (``g`` is the gen_gui module)."""
    _square_frame(g)
    _plate(g)
    _parchment(g)
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


# vanilla map colours (MapColor) and default biome tints, as MapPalette.java gives them
GRASS = (0x7C, 0xA2, 0x4C)       # grass tint 0x91BD59 x 0.86
FOLIAGE = (0x58, 0x7E, 0x22)     # foliage tint 0x77AB2F x 0.74
SAND = (0xF7, 0xE9, 0xA3)
STONE = (0x70, 0x70, 0x70)
SNOW = (0xFF, 0xFF, 0xFF)
WATER_TINT = (0x3F, 0x76, 0xE4)


def _scale(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def water_colour(tint, depth, bed=None):
    """MapPalette.water(): light over the shallows (the bed shows through), deep navy far down."""
    f = math.sqrt(max(0, min(30, depth - 1)) / 30.0)
    shallow = _mix(tint, (255, 255, 255), 0.12)
    deep = _mix(_scale(tint, 0.52), (0x0B, 0x1C, 0x3E), 0.32)
    c = _mix(shallow, deep, f)
    if bed and depth <= 4:
        c = _mix(c, bed, (0.55, 0.38, 0.22, 0.10)[max(1, depth) - 1])
    return c


def fake_world(w, h, seed=3):
    """{(x, z): (kind, colour, height, depth)} for a w x h block area: a sea with its shelf, beaches, plains, forest,
    rolling hills and a snowy ridge. ``kind``: land, tree or water (MapShade's kinds); water's height is its surface."""
    n1, n2, n3 = _noise(seed, w, h, 64), _noise(seed + 1, w, h, 24), _noise(seed + 2, w, h, 9)
    forest = _noise(seed + 3, w, h, 30)
    ridge = _noise(seed + 4, w, h, 48)
    out = {}
    for z in range(h):
        for x in range(w):
            e = n1(x, z) * 0.62 + n2(x, z) * 0.28 + n3(x, z) * 0.10
            r = max(0.0, 1 - abs(ridge(x, z) - 0.5) * 4) * max(0.0, e - 0.45) * 2
            hgt = int(34 + e * 64 + r * 70)
            if hgt < 62:
                depth = 62 - hgt
                out[(x, z)] = ("water", water_colour(WATER_TINT, depth, SAND), 62, depth)
            elif hgt < 64:
                out[(x, z)] = ("land", SAND, hgt, 0)
            elif hgt < 92:
                if forest(x, z) > 0.58 and (x * 7 + z * 13) % 5:
                    out[(x, z)] = ("tree", FOLIAGE, hgt + 5, 0)
                else:
                    out[(x, z)] = ("land", GRASS, hgt, 0)
            elif hgt < 118:
                out[(x, z)] = ("land", STONE, hgt, 0)
            else:
                out[(x, z)] = ("land", SNOW, hgt, 0)
    return out


RELIEF = {"flat": 0.0, "normal": 0.6, "strong": 1.0}


def _light(h, west, east, north, south, step=1):
    k = 1.5 if step > 1 else 1.0
    gx = (east - west) / (2.0 * step) * k
    gz = (south - north) / (2.0 * step) * k
    dot = (0.5 * gx + 0.70710678 + 0.5 * gz) / math.sqrt(gx * gx + 1 + gz * gz)
    return max(0.0, dot) / 0.70710678


def shade(world, x, z, relief="normal", contours=False, surface=True):
    """MapShade.shade() on the fake world: hill-shading from the north-west, valleys, height tint, sea bed relief,
    shore rim and contour lines. Returns RGBA."""
    strength = RELIEF[relief]
    kind, base, h, depth = world[(x, z)]
    get = world.get
    f = 1.0
    if kind == "water":
        if strength > 0:
            fh = h - depth

            def bed(dx, dz):
                c = get((x + dx, z + dz))
                return c[2] - c[3] if c and c[0] == "water" else fh
            light = _light(fh, bed(-1, 0), bed(1, 0), bed(0, -1), bed(0, 1))
            f += strength * 0.35 * max(0.0, 1 - depth / 24.0) * (light - 1)
            if any((c := get((x + dx, z + dz))) and c[0] in ("land", "tree") for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                return _mix(_scale(base, f), (0xEF, 0xF6, 0xEE), 0.22 * strength + 0.06) + (255,)
        return _scale(base, f) + (255,)

    def at(dx, dz):
        c = get((x + dx, z + dz))
        return c[2] if c else h
    if strength > 0:
        f += strength * 0.62 * (_light(h, at(-1, 0), at(1, 0), at(0, -1), at(0, 1)) - 1)
        far = [c[2] for c in (get((x - 4, z)), get((x + 4, z)), get((x, z - 4)), get((x, z + 4))) if c]
        if far:
            curve = max(-0.6, min(1.0, (sum(far) / len(far) - h) / 10.0))
            f *= 1 - (0.16 if curve > 0 else 0.08) * strength * curve
        f = max(0.42, min(1.36, f))
    c = _scale(base, f)
    if surface and strength > 0:
        if h > 68:
            c = _mix(c, (0xF3, 0xEB, 0xDA), min(1.0, (h - 68) / 150.0) * 0.34)
        elif h < 62:
            c = _scale(c, 1 - min(1.0, (62 - h) / 40.0) * 0.14)
    if contours and kind == "land":
        line = 0
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = get((x + dx, z + dz))
            if q and q[0] in ("land", "water") and q[2] // 16 < h // 16:
                line = max(line, 2 if q[2] // 64 < h // 64 else 1)
        if line:
            c = _scale(c, 0.66 if line == 2 else 0.80)
    return c + (255,)


def _terrain(world, Image, x0, z0, w, h, scale, known=None, relief="normal", contours=False):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    cache = {}
    for sy in range(h):
        for sx in range(w):
            wx, wz = int(math.floor(x0 + sx / scale)), int(math.floor(z0 + sy / scale))
            if (wx, wz) in world and (known is None or known(wx, wz)):
                if (wx, wz) not in cache:
                    cache[(wx, wz)] = shade(world, wx, wz, relief, contours)
                px[sx, sy] = cache[(wx, wz)]
    return im


# ------------------------------------------------------------------ the arrow and markers (MapRenderer.java)
def _round_half(v):
    return int(math.floor(v + 0.5))


def minimap_marker(outer):
    return max(6.0, min(11.0, outer / 8.5))


def minimap_arrow(outer):
    return max(7.0, min(13.0, 7.0 + (outer - 56) * 0.085))


def world_marker(zoom):
    return max(7.0, min(13.0, 9.0 + zoom * 0.7))


def world_arrow(zoom):
    return max(8.0, min(16.0, 11.0 + zoom * 0.9))


def _polygon(big, pts, color, dx=0.0, dy=0.0):
    """MapRenderer.polygon(): the pixels whose centre is inside, row by row (alpha composited)."""
    from PIL import Image, ImageDraw
    layer = Image.new("RGBA", big.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ys = [p[1] + dy for p in pts]
    n = len(pts)
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x0, y0 = pts[i][0] + dx, pts[i][1] + dy
            x1, y1 = pts[(i + 1) % n][0] + dx, pts[(i + 1) % n][1] + dy
            if (y0 <= yc) != (y1 <= yc):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a, b = int(math.ceil(xs[k] - 0.5)), int(math.ceil(xs[k + 1] - 0.5))
            if b > a:
                d.rectangle((a, y, b - 1, y), fill=color)
    big.alpha_composite(layer)


def draw_arrow(big, gs, x, y, angle, size):
    """MapRenderer.arrow() on the upscaled image (``gs`` px per GUI px): shadow, soot outline, cream and red halves."""
    r = size * gs / 2.0
    cos, sin = math.cos(angle), math.sin(angle)
    edge = max(1.0, gs * 0.6)
    grow = (r + edge * 1.8) / r
    ox, oy = _round_half(x * gs), _round_half(y * gs)
    pin = [(px * r * cos - py * r * sin + ox, px * r * sin + py * r * cos + oy) for px, py in ARROW]
    pout = [(ox + (px - ox) * grow, oy + (py - oy) * grow) for px, py in pin]
    sh = max(1.0, gs * 0.7)
    _polygon(big, pout, (0, 0, 0, 0x60), sh, sh)
    _polygon(big, pout, (0x0F, 0x0C, 0x0A, 255))
    _polygon(big, [pin[0], pin[2], pin[3]], (0xFF, 0xF8, 0xEC, 255))
    _polygon(big, [pin[0], pin[1], pin[2]], (0xE0, 0x48, 0x3B, 255))


def draw_crisp(big, gs, path, x, y, size, tint=None, shadow=True, texels=9):
    """MapRenderer.spriteCrisp(): a whole number of screen px per texel, centred on (x, y), with a drop shadow."""
    from PIL import Image, ImageChops
    k = max(1, _round_half(size * gs / texels))
    real = texels * k
    im = Image.open(path).convert("RGBA").resize((real, real), Image.NEAREST)
    if tint:
        im = ImageChops.multiply(im, Image.new("RGBA", im.size, tuple(tint[:3]) + (255,)))
    o = -(real // 2)
    bx, by = _round_half(x * gs) + o, _round_half(y * gs) + o
    if shadow:
        a = im.getchannel("A").point(lambda v: v * 0x70 // 255)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(a)
        big.alpha_composite(sh, (bx + k, by + k))
    big.alpha_composite(im, (bx, by))


# ------------------------------------------------------------------ the mockups
def mockups(g):
    from PIL import Image
    os.makedirs(g.PREVIEW, exist_ok=True)
    world = fake_world(420, 300)
    _mock_minimap(g, world, Image)
    _mock_worldmap(g, world, Image)
    _mock_options(g, world, Image)
    _mock_options(g, world, Image, li=0)
    _mock_worldmap(g, world, Image, tilted=True)


def draw_minimap(g, m, world, x, y, size, square=False, coords=("212, 71, -148", "Plaines"), right=False, zoom=1.0,
                 opacity=1.0, relief="normal", contours=False, yaw=-35):
    """The minimap as MinimapHud draws it, on mockup ``m`` at (x, y): ``size`` is the map inside the 6 px frame.
    Markers and the arrow are sized to the map and drawn at screen resolution. Returns the height taken."""
    from PIL import Image
    outer = size + BORDER * 2
    back = Image.new("RGBA", (size, size), (0x2A, 0x22, 0x1C, int(255 * opacity)))
    terr = _terrain(world, Image, 210 - size / 2 / zoom, 150 - size / 2 / zoom, size, size, zoom, relief=relief,
                    contours=contours)
    if opacity < 1:
        terr.putalpha(terr.getchannel("A").point(lambda a: int(a * opacity)))
    m.im.alpha_composite(back, (x + BORDER, y + BORDER))
    m.im.alpha_composite(terr, (x + BORDER, y + BORDER))
    cx, cy = x + BORDER + size / 2, y + BORDER + size / 2
    k = size / 96
    ms = minimap_marker(outer)
    marks = (("waystone", -20, -30), ("ping", 26, 14), ("spawn", -36, 22), ("grave", 10, -12))

    def overlay(big, gs):
        for name, dx, dy in marks:
            draw_crisp(big, gs, g.sp("map/marker/" + name), int(cx + dx * k), int(cy + dy * k), ms)
        draw_arrow(big, gs, cx, cy, math.radians(yaw), minimap_arrow(outer))
    m.overlays.append(overlay)
    if square:
        m.nine("map/frame_square", x, y, outer, outer, 6)
    else:
        m.im.alpha_composite(round_frame(g, size).im, (x, y))
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


def _sky(m, w, h, horizon):
    for y in range(h):
        for x in range(w):
            m.im.putpixel((x, y), (int(110 + y * 0.3), int(160 + y * 0.2), 220, 255) if y < horizon else (70, 104, 50, 255))


def _mock_minimap(g, world, Image):
    """minimap.png: five sizes side by side (48, 56, 68 by default, 96 and 128 px on screen: the arrow and markers grow
    with the map) over a stand-in game view; minimap_variants.png: the square frame, a faded one (opacity 60 %), and
    the relief flat / strong with contour lines."""
    W, H = 474, 180
    m = g.Mock(W, H)
    _sky(m, W, H, 80)
    x = 4
    for outer in (48, 56, 68, 96, 128):
        size = outer - BORDER * 2
        draw_minimap(g, m, world, x, 4, size, coords=None)
        m.text(f"{outer} px", x + outer // 2, H - 12, g.CREAM, center=True)
        x += outer + 10
    m.save("minimap")
    W, H = 400, 110
    m = g.Mock(W, H)
    _sky(m, W, H, 50)
    draw_minimap(g, m, world, 4, 4, 56, square=True, zoom=2.0, yaw=0)
    draw_minimap(g, m, world, 100, 4, 56, opacity=0.6, coords=("-1732, 129, -461", "Champs fleuris"))
    draw_minimap(g, m, world, 196, 4, 56, relief="flat", coords=None)
    m.text("Plat", 196 + 34, 74, g.CREAM, center=True)
    draw_minimap(g, m, world, 292, 4, 84, relief="strong", contours=True, coords=None, zoom=0.5)
    m.text("Fort + courbes", 292 + 48, 100, g.CREAM, center=True)
    m.save("minimap_variants")


# MapView3D.java
DEPTH = 0.72
RISE = 0.9


def render3d(world, colour, cx, cz, s, w, h, ref, known=None):
    """MapView3D.render() on the fake world: each screen column near to far, the top of every cell then the darker
    wall under it down to the cell in front. ``colour(x, z)``: the shaded colour (RGBA)."""
    from PIL import Image
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    mid = h / 2.0
    depth, rise = s * DEPTH, s * RISE
    z_near = int(math.ceil(cz + (mid + 128 * rise) / depth))
    z_far = int(math.floor(cz - (mid + 96 * rise) / depth))
    step = max(1, int(1.0 / depth))
    z_near = (z_near // step) * step
    for sx in range(w):
        bx = int(math.floor(cx + (sx + 0.5 - w / 2.0) / s))
        top = h
        near_h = None
        bz = z_near
        while bz >= z_far and top > 0:
            cell = world.get((bx, bz))
            if cell is None or (known and not known(bx, bz)):
                near_h = None
                bz -= step
                continue
            hh = cell[2]
            c = colour(bx, bz)
            y_far = mid + (bz - cz) * depth - (hh + 1 - ref) * rise
            y0 = _round_half(y_far)
            y_face = max(y0 + 1, _round_half(y_far + step * depth))
            base = hh - 3 if near_h is None else min(hh, near_h)
            y_base = _round_half(mid + (bz + step - cz) * depth - (base + 1 - ref) * rise)
            fr, to = max(0, y0), min(top, max(y_face, y_base))
            if fr < to:
                wall = _scale(c, 0.7) if cell[0] == "water" else _scale(_mix(c, (0x5B, 0x46, 0x30), 0.28), 0.6)
                for yy in range(fr, to):
                    if yy < y_face:
                        px[sx, yy] = c[:3] + (255,)
                    else:
                        kk = min(1.0, (yy - y_face) / max(4.0, rise * 10))
                        px[sx, yy] = _scale(wall, 1 - 0.22 * kk) + (255,)
                top = fr
            near_h = hh
            bz -= step
    return im


def _parchment_fill(g, m, Image, x0, y0, x1, y1):
    par = Image.open(g.sp("map/parchment")).convert("RGBA")
    for yy in range(y0, y1, 64):
        for xx in range(x0, x1, 64):
            m.im.alpha_composite(par.crop((0, 0, min(64, x1 - xx), min(64, y1 - yy))), (xx, yy))


def _mock_worldmap(g, world, Image, tilted=False):
    """worldmap.png (seen from above, relief shading) or worldmap_3d.png (the tilted 3D view): the screen at 480 x 270
    GUI px with the legend and waypoints on the right."""
    from PIL import ImageChops
    W, H = 480, 270
    m = g.Mock(W, H)
    m.im.paste((26, 20, 16, 255), (0, 0, W, H))
    m.nine("panel", 4, 6, W - 8, H - 10, 9)
    m.nine("title_plate", W // 2 - 50, 1, 100, 18, 6)
    m.text("Carte du monde", W // 2, 6, g.PLATE_INK, shadow=False, center=True, bold=True)
    sb = 116
    mx0, my0, mx1, my1 = 18, 24, W - 18 - sb - 6, H - 30
    _parchment_fill(g, m, Image, mx0, my0, mx1, my1)
    # explored: a blob around the centre
    cxw, czw = 210, 150
    zoom = 0
    scale = 1.0

    def known(x, z):
        return math.hypot(x - cxw, (z - czw) * 1.3) < 120 + 25 * math.sin(x * 0.05) or abs(z - 150) < 8
    cx, cy = (mx0 + mx1) / 2, (my0 + my1) / 2
    mw, mh = mx1 - mx0, my1 - my0
    if tilted:
        cache = {}

        def colour(x, z):
            if (x, z) not in cache:
                cache[(x, z)] = shade(world, x, z)
            return cache[(x, z)]
        ref = world[(cxw, czw)][2]
        m.im.alpha_composite(render3d(world, colour, cxw, czw, scale, mw, mh, ref, known), (mx0, my0))

        def at(dx, dz):
            wx, wz = cxw + dx, czw + dz
            y = world.get((wx, wz), (0, 0, 64))[2] + 1
            return cx + dx * scale, cy + dz * scale * DEPTH - (y - ref) * scale * RISE
    else:
        terr = _terrain(world, Image, cxw - mw / 2 / scale, czw - mh / 2 / scale, mw, mh, scale, known)
        m.im.alpha_composite(terr, (mx0, my0))
        for gx in range(mx0 + 40, mx1, 128):
            for yy in range(my0, my1):
                m.im.alpha_composite(Image.new("RGBA", (1, 1), (0, 0, 0, 40)), (gx, yy))

        def at(dx, dz):
            return cx + dx * scale, cy + dz * scale
    ms = world_marker(zoom)
    marks = [("waystone", -60, -40, "Avant-poste de la Guilde"), ("structure", 70, 30, "Monastère des cimes"),
             ("spawn", -20, 60, None), ("ping", 40, -50, None), ("player", 30, 10, None)]
    wps = (("house", (0xF6, 0xC3, 0x43), -100, 20, "Base"), ("mine", (0x3F, 0xA9, 0xFF), 90, -70, "Mine de fer"))
    below = _round_half(ms / 2) + 2
    pos = {}
    for name, dx, dy, label in marks:
        pos[name] = tuple(int(round(v)) for v in at(dx, dy))
        if label and name == "waystone":
            sx, sy = pos[name]
            w_ = g.text_width(label)
            m.im.alpha_composite(Image.new("RGBA", (int(w_) + 4, 10), (16, 12, 10, 144)), (int(sx - w_ / 2 - 2), sy + below))
            m.text(label, sx, sy + below + 1, g.AETHER_TXT, center=True)
    for icon, col, dx, dy, label in wps:
        sx, sy = (int(round(v)) for v in at(dx, dy))
        pos[icon] = (sx, sy)
        w_ = g.text_width(label)
        m.im.alpha_composite(Image.new("RGBA", (int(w_) + 4, 10), (16, 12, 10, 144)), (int(sx - w_ / 2 - 2), sy + below))
        m.text(label, sx, sy + below + 1, col + (255,), center=True)
    me = at(0, 0)

    def overlay(big, gs):
        for name, _dx, _dy, _l in marks:
            if not tilted and mx0 + 6 <= pos[name][0] < mx0 + 174 and pos[name][1] >= my1 - 72:
                continue  # under the marker card
            draw_crisp(big, gs, g.sp("map/marker/" + name), pos[name][0], pos[name][1], ms)
        for icon, col, _dx, _dy, _l in wps:
            draw_crisp(big, gs, g.sp("map/wp/" + icon), pos[icon][0], pos[icon][1], ms, tint=col)
        draw_arrow(big, gs, me[0], me[1], math.radians(150), world_arrow(zoom))
    m.overlays.append(overlay)
    m.nine("map/frame_square", mx0 - 4, my0 - 4, mx1 - mx0 + 8, my1 - my0 + 8, 6)
    if tilted:
        cw = g.text_width("Vue 3D") + 10
        m.nine("map/plate", mx0 + 4, my0 + 4, cw, 13, 3)
        m.text("Vue 3D", mx0 + 9, my0 + 7, g.AETHER_TXT, shadow=False)
    for i, glyph in enumerate(("center", "zoom_in", "zoom_out", "cave", "list", "view3d", "options")):
        bx, by = mx1 - 20, my0 + 4 + i * 19
        m.nine("button_small_hover" if glyph == "view3d" and tilted else "button_small", bx, by, 16, 16, 3)
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
    if not tilted:
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
    m.save("worldmap_3d" if tilted else "worldmap")


# WorldMapScreen's options panel
OPT_W, OPT_LABEL, OPT_ROW, OPT_ROWS, OPT_HEAD, OPT_SECTION, OPT_PAD = 210, 82, 16, 10, 24, 14, 12
OPT_H = OPT_HEAD + OPT_ROWS * OPT_ROW + OPT_SECTION + 10


def _mock_options(g, world, Image, li=1):
    """worldmap_options.png: the world map at the smallest supported screen (427 x 240 GUI px, 1280 x 720) with the
    options panel open and the minimap shown live in its corner at 96 px (set with the slider)."""
    from wf import content, guide, machines
    W, H = 427, 240
    m = g.Mock(W, H)
    m.im.paste((26, 20, 16, 255), (0, 0, W, H))
    m.nine("panel", 4, 6, W - 8, H - 10, 9)
    m.nine("title_plate", W // 2 - 50, 1, 100, 18, 6)
    m.text("Carte du monde", W // 2, 6, g.PLATE_INK, shadow=False, center=True, bold=True)
    mx0, my0, mx1, my1 = 18, 24, W - 18 - 116 - 6, H - 30
    _parchment_fill(g, m, Image, mx0, my0, mx1, my1)
    mw, mh = mx1 - mx0, my1 - my0
    m.im.alpha_composite(_terrain(world, Image, 210 - mw / 2, 150 - mh / 2, mw, mh, 1.0), (mx0, my0))
    m.nine("map/frame_square", mx0 - 4, my0 - 4, mw + 8, mh + 8, 6)
    m.nine("inset", mx1 + 6, my0 - 4, W - 18 - mx1 - 6, mh + 8, 4)
    # the live minimap, top left, 96 px
    outer = 96
    draw_minimap(g, m, world, 4, 4, outer - BORDER * 2, coords=("212, 71, -148", "Plaines"))
    # the panel, on the other side
    k, o = "gui.wayfarers.settings.", "gui.wayfarers.map.options."

    def tr(key):
        if key in content.MESSAGES:
            return content.MESSAGES[key][li]
        return UI[key][li]
    ox, oy = W - OPT_W - 6, max(2, (H - OPT_H) // 2)
    m.nine("panel", ox, oy, OPT_W, OPT_H, 9)
    m.text(tr(o + "title"), ox + OPT_W // 2, oy + 10, g.INK, shadow=False, center=True, bold=True)
    m.text("x", ox + OPT_W - 18, oy + 9, g.INK_SOFT, shadow=False)

    def row(i):
        return oy + OPT_HEAD + i * OPT_ROW + (OPT_SECTION if i >= 8 else 0)
    labels = [o + "shown", k + "minimap_size", o + "presets", k + "minimap_corner", k + "minimap_shape", o + "rotate",
              k + "minimap_coords", k + "minimap_opacity", o + "relief", o + "contours"]
    for i, key in enumerate(labels):
        m.text(tr(key), ox + OPT_PAD, row(i) + 4, g.INK, shadow=False)
        assert guide.text_width(tr(key)) <= OPT_LABEL - OPT_PAD - 2, tr(key)
    cx, cw = ox + OPT_LABEL, OPT_W - OPT_LABEL - OPT_PAD

    def choice(x, y, w, h, label, on, icon=None):
        m.nine("button_on" if on else "button", x, y, w, h, 4)
        if icon:
            m.im.alpha_composite(Image.open(g.sp(icon)).convert("RGBA"), (x + (w - 12 + 1) // 2, y + (h - 12) // 2))
        else:
            assert guide.text_width(label) <= w - 2, label
            m.text(label, x + (w - guide.text_width(label) + 1) // 2, y + (h - 8) // 2, g.GOLD if on else g.hexc("FFFFFF"))

    def toggle(i, on):
        m.im.alpha_composite(Image.open(g.sp("toggle_on" if on else "toggle_off")).convert("RGBA"), (cx, row(i) + 1))
        m.text(machines.GUI["on" if on else "off"][li], cx + 30, row(i) + 4, g.INK_SOFT, shadow=False)

    def slider(i, steps, step, marks=None):
        sx, sy, sw = cx, row(i) - 1, cw - 32
        m.nine("slider_track", sx, sy + 6, sw, 6, 2)
        for s_ in range(steps):
            if marks is not None and s_ != step and s_ not in marks:
                continue
            tx = sx + 4 + round(s_ * (sw - 8) / (steps - 1))
            m.d.rectangle((tx, sy + 14, tx, sy + 15), fill=g.GOLD if s_ == step else g.BRASS_DK)
        m.im.alpha_composite(Image.open(g.sp("slider_knob")).convert("RGBA"), (sx + int(step / (steps - 1) * (sw - 8)), sy + 2))
    toggle(0, True)
    slider(1, 29, (outer - 48) // 4, marks=[(p - 48) // 4 for p in (56, 68, 96, 128)])
    m.text(f"{outer} px", cx + cw - 29, row(1) + 4, g.INK_SOFT, shadow=False)
    bw = (cw - 6) // 4
    for i, p in enumerate((56, 68, 96, 128)):
        choice(cx + i * (bw + 2), row(2), bw, 14, str(p), p == outer)
    for j, corner in enumerate(["top_left", "top_right", "bottom_left", "bottom_right"]):
        choice(cx + j * 24, row(3), 22, 14, "", j == 0, icon="glyph/corner_" + corner)
    sw_ = (cw - 2) // 2
    for j, shape in enumerate(["round", "square"]):
        choice(cx + j * (sw_ + 2), row(4), sw_, 14, tr(k + "minimap_shape." + shape), j == 0)
    toggle(5, False)
    toggle(6, True)
    slider(7, 8, 7)
    m.text("100 %", cx + cw - 29, row(7) + 4, g.INK_SOFT, shadow=False)
    sy = row(8) - OPT_SECTION
    m.d.rectangle((ox + OPT_PAD, sy + 3, ox + OPT_W - OPT_PAD - 1, sy + 3), fill=g.BRASS_DK)
    m.text(tr(o + "relief_title"), ox + OPT_W // 2, sy + 5, g.INK, shadow=False, center=True, bold=True)
    rw = (cw - 4) // 3
    for j, r in enumerate(["flat", "normal", "strong"]):
        choice(cx + j * (rw + 2), row(8), rw, 14, tr(o + "relief." + r), j == 1)
    toggle(9, False)
    assert ox > 4 + outer + 4, "the options panel covers the live minimap"
    assert oy + OPT_H <= H, "the options panel does not fit 240 px"
    m.save("worldmap_options" + ("" if li else "_en"))

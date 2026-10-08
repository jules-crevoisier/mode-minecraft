"""Block-face overhaul: ores, raw-ore blocks, metal storage blocks (and, via blocktex_*.py, plating, machinery and
decorative stone), drawn so they sit next to vanilla blocks instead of looking like recoloured vanilla.

gen_textures.py calls ``textures(written)`` last: it only repaints faces that already exist (same paths, same ids).

House rules (tools/STYLE_STEAMPUNK.md):
- host stones use the vanilla stone / deepslate / netherrack tones and the same kind of structure (stone: short
  horizontal dashes; deepslate and netherrack: rounded cobbles with dark crevices), so an ore matches its neighbours;
- every mineral has its own silhouette: zinc stacked platelets, aether hexagonal prisms, lithite geode pockets,
  mithril a branching seam that runs on into the next block, orichalcum fat glowing nuggets;
- a material is a ramp of 4-6 flat tones, shadows cooler, highlights warmer; light from the top-left, a dark socket
  bottom-right of every raised shape; no per-pixel random speckle.
"""
import math
import random

from .png import Canvas
from . import texkit as K

# ------------------------------------------------------------------ host stones (vanilla tones)
STONE = [(104, 104, 104), (116, 116, 116), (127, 127, 127), (143, 143, 143)]
DEEPSLATE = [(47, 47, 55), (61, 61, 67), (81, 81, 81), (100, 100, 100), (121, 121, 121)]
NETHERRACK = [(65, 22, 22), (80, 27, 27), (101, 40, 40), (114, 50, 50), (133, 66, 66)]


def _grid(v):
    return [[v] * 16 for _ in range(16)]


def stone_idx(seed):
    """Vanilla-like stone: a mid field broken by short horizontal light dashes, each with a shade dash under it,
    and a few darker flecks. Tileable."""
    rng = random.Random(f"stone{seed}")
    g = _grid(2)
    for _ in range(9):  # lit dashes with their shadow
        x, y, n = rng.randrange(16), rng.randrange(16), rng.randint(2, 5)
        for i in range(n):
            g[y][(x + i) % 16] = 3
        if rng.random() < 0.6:
            for i in range(rng.randint(1, n - 1)):
                g[(y - 1) % 16][(x + 1 + i) % 16] = 3
        for i in range(1, n + 1):
            if g[(y + 1) % 16][(x + i) % 16] == 2:
                g[(y + 1) % 16][(x + i) % 16] = 1
    for _ in range(18):  # shade dashes
        x, y, n = rng.randrange(16), rng.randrange(16), rng.randint(2, 6)
        for i in range(n):
            if g[y][(x + i) % 16] == 2:
                g[y][(x + i) % 16] = 1
    for _ in range(40):  # dark flecks at the ends of shade dashes
        x, y = rng.randrange(16), rng.randrange(16)
        if g[y][x] == 1 and sum(row.count(0) for row in g) < 16:
            g[y][x] = 0
            if rng.random() < 0.5 and g[y][(x + 1) % 16] == 1:
                g[y][(x + 1) % 16] = 0
    return g


def _cells(seed, n, jitter, stretch=1.0):
    """Jittered grid of Voronoi seeds over a 16x16 torus (``n`` x ``n`` cells)."""
    rng = random.Random(f"cells{seed}")
    step = 16 / n
    return [((i + 0.5) * step + rng.uniform(-jitter, jitter) * step, (j + 0.5) * step + rng.uniform(-jitter, jitter) * step,
             rng.random()) for i in range(n) for j in range(n)]


def _near(pts, x, y, sx=1.0):
    best = []
    for px, py, t in pts:
        dx = min(abs(x - px), 16 - abs(x - px)) * sx
        dy = min(abs(y - py), 16 - abs(y - py))
        best.append((dx * dx + dy * dy, t, px, py))
    best.sort()
    return best[0], best[1]


def cobble_idx(seed, n=3, tones=(2, 3, 2, 1, 3, 2), crev=0, rim=1.15, sx=0.8):
    """Rounded cobbles (deepslate, netherrack): each cell one tone, lit on its top-left edge, shaded on the
    bottom-right, dark crevices between cells."""
    pts = _cells(seed, n, 0.32)
    rng = random.Random(f"cob{seed}")
    tone_of = {}
    for p in pts:
        tone_of[p[2]] = rng.choice(tones)
    g = _grid(0)
    own = [[None] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            (d1, t1, _, _), (d2, _, _, _) = _near(pts, x + 0.5, y + 0.5, sx)
            own[y][x] = t1
            g[y][x] = crev if math.sqrt(d2) - math.sqrt(d1) < rim else tone_of[t1]
    out = [r[:] for r in g]
    top = max(tones) + 1
    for y in range(16):
        for x in range(16):
            if g[y][x] == crev:
                continue
            up, left = g[(y - 1) % 16][x], g[y][(x - 1) % 16]
            down, right = g[(y + 1) % 16][x], g[y][(x + 1) % 16]
            if up == crev or left == crev:
                out[y][x] = min(top, g[y][x] + 1)
            elif down == crev or right == crev:
                out[y][x] = max(crev + 1, g[y][x] - 1)
    return out


def host(name, seed):
    if name == "stone":
        return K.paint(stone_idx(seed), STONE), STONE
    if name == "deepslate":
        return K.paint(cobble_idx(seed, 3, (1, 2, 2, 1, 2, 3), 0, 0.45), DEEPSLATE), DEEPSLATE
    return K.paint(cobble_idx(seed, 4, (2, 3, 2, 1, 3, 2), 0, 0.36, 1.0), NETHERRACK), NETHERRACK


# ------------------------------------------------------------------ stamps
def draw(cv, rows, pal, host_tones, ox=0, oy=0, socket=True, glow=None):
    """ASCII layer over a host: '.' host, '1'..'6' the mineral ramp (dark -> light), 'g' glint, 'o' glow halo
    blended into the host, 'k' socket (darkest host), 'l' lit host. With ``socket`` every host pixel right of /
    below a mineral pixel turns to the darkest host tone, so the mineral sits in the rock."""
    pts = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                pts[((ox + x) % 16, (oy + y) % 16)] = ch
    mineral = {p for p, ch in pts.items() if ch in "123456g"}
    if socket:
        for (x, y) in list(mineral):
            for q in (((x + 1) % 16, y), (x, (y + 1) % 16), ((x + 1) % 16, (y + 1) % 16)):
                if q not in pts:
                    pts[q] = "k"
    for (x, y), ch in pts.items():
        if ch == "k":
            cv.set(x, y, host_tones[0])
        elif ch == "l":
            cv.set(x, y, host_tones[-1])
        elif ch == "o":
            if glow:
                cv.set(x, y, K.mix(cv.get(x, y), glow, 0.38))
        elif ch == "g":
            cv.set(x, y, pal["g"])
        else:
            cv.set(x, y, pal[int(ch)])


def glow_halo(cv, mask, glow, strength=0.3, r=1.6):
    """Tint host pixels near a glowing mineral."""
    for y in range(16):
        for x in range(16):
            if (x, y) in mask:
                continue
            d = min((math.hypot(x - mx, y - my) for mx, my in mask), default=99)
            if d <= r:
                cv.set(x, y, K.mix(cv.get(x, y), glow, strength * (1.25 - d / r * 0.75)))


def mineral_pal(base, glint, lo=-0.72, hi=0.72, n=6):
    tones = K.ramp(base, n, lo, hi)
    pal = {i + 1: t for i, t in enumerate(tones)}
    pal["g"] = glint
    return pal


def _rows(s):
    return s.strip("\n").split("\n")


# ------------------------------------------------------------------ ores
# zinc: flat platelets stacked like shale, each a slanted bar with a bright top edge and a dark lower lip
ZINC = _rows("""
................
....g5556.......
...5444432......
..443332........
.3222211........
................
..........g556..
.........544432.
....g556443332..
...5444432221...
..443332........
.3222211........
................
.......g5556....
......54444321..
.....4433322....
""")
# aether: hexagonal prisms standing in clusters, a lit left face, a shaded right face, a pale tip
AETHER = _rows("""
......g.........
......6.........
...6..54..6.....
...54.53.54.....
...53.53.53.....
....4354343.....
....3343332.....
.....22222......
................
...........g....
...........6..g.
........6..54.6.
........54.5354.
........53.4343.
.........43332..
.........2222...
""")
# lithite: geode pockets cut open - a pale crust ring, teal teeth lit on the far (lower-right) wall, dark hollow
LITHITE = _rows("""
................
..cccc..........
.cK112cc........
.c1d2456c.......
.cd345566c......
..c45666cK......
...cccccKK......
................
..........ccc...
.........cK12c..
..5......c1d45c.
..43.....cd456cK
..........c56cK.
.....6.....cKK..
.....4..........
................
""")
# orichalcum: fat rounded nuggets with a molten core glowing through
ORICHALCUM = _rows("""
................
..o55o..........
.o56664.....o5o.
.5666643...o5664
.4664332...45543
.4443322....3322
..33222.....222.
...222..........
................
......o55o......
.....o56654.....
.....5666443....
.....4643332....
.....44432222...
......322222....
.......2222.....
""")
LITHITE_KEYS = {"c": "crust", "K": "crust_dk", "d": "hollow"}


def ore_zinc(host_name, seed):
    cv, ht = host(host_name, seed)
    pal = mineral_pal((150, 164, 186), (250, 252, 255), -0.78, 0.74)
    draw(cv, ZINC, pal, ht)
    return cv


def ore_aether(host_name, seed):
    cv, ht = host(host_name, seed)
    pal = mineral_pal((52, 206, 226), (240, 255, 255), -0.74, 0.78)
    mask = {(x, y) for y, r in enumerate(AETHER) for x, c in enumerate(r) if c != "."}
    glow_halo(cv, mask, (90, 230, 255), 0.28, 1.6)
    draw(cv, AETHER, pal, ht)
    return cv


def ore_lithite(host_name, seed):
    cv, ht = host(host_name, seed)
    pal = mineral_pal((54, 196, 160), (232, 255, 240), -0.7, 0.72)
    crust = K.ramp((148, 160, 156), 3, -0.5, 0.3)
    pal.update({"c": crust[2], "K": crust[0], "d": K.shift(pal[1], -0.3)})
    rows = [r for r in LITHITE]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in "cKd":
                cv.set(x, y, pal[ch])
            elif ch in "123456g":
                cv.set(x, y, pal[int(ch)] if ch != "g" else pal["g"])
    # the crust's lower-right lip catches the socket shadow of the host
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in "K123456":
                for q in ((x + 1, y), (x, y + 1)):
                    if 0 <= q[0] < 16 and 0 <= q[1] < 16 and rows[q[1]][q[0]] == ".":
                        cv.set(q[0], q[1], ht[0])
    return cv


def ore_orichalcum(host_name, seed):
    cv, ht = host(host_name, seed)
    pal = mineral_pal((226, 116, 52), (255, 246, 196), -0.72, 0.8)
    pal[6] = (255, 226, 120)  # molten core
    mask = {(x, y) for y, r in enumerate(ORICHALCUM) for x, c in enumerate(r) if c not in ".o"}
    glow_halo(cv, mask, (255, 120, 40), 0.22, 1.5)
    draw(cv, ORICHALCUM, pal, ht, glow=(255, 150, 60))
    return cv


# mithril: a lumpy seam leaving the right edge where it enters the left one, a branch, two nodules, star glints
SEAM_Y = [9, 9, 8, 8, 7, 7, 7, 6, 6, 7, 7, 8, 8, 9, 9, 9]
SEAM_T = [2, 2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2]
BRANCH = [(8, 5), (9, 4), (10, 3), (10, 2), (11, 1), (4, 10), (3, 11), (3, 12), (2, 13)]
NODULES = [(13.0, 13.0, 1.8), (3.5, 3.5, 1.6)]
STARS = [(9, 6), (11, 1), (13, 12), (2, 13)]


def ore_mithril(host_name, seed):
    cv, ht = host(host_name, seed)
    pal = mineral_pal((136, 190, 236), (246, 252, 255), -0.74, 0.8)
    occ = {}
    for x in range(16):
        y0, t = SEAM_Y[x], SEAM_T[x]
        for k in range(t):
            occ[(x, y0 + k)] = 5 if k == 0 else 2 if k == t - 1 else 4
    for x, y in BRANCH:
        occ.setdefault((x, y), 4)
    for cx, cy, r in NODULES:
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                if dx * dx + dy * dy <= r * r:
                    k = (dx + dy) / (r * 1.41)
                    occ[(x, y)] = 6 if k < -0.45 else 5 if k < 0.0 else 4 if k < 0.45 else 2
    for (x, y) in list(occ):
        for q in (((x + 1) % 16, (y + 1) % 16), (x, (y + 1) % 16)):
            if q not in occ:
                cv.set(q[0], q[1], ht[0])
    for (x, y), t in occ.items():
        cv.set(x, y, pal[t])
    for x, y in STARS:  # four-point twinkles
        cv.set(x, y, pal["g"])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = ((x + dx) % 16, (y + dy) % 16)
            cv.set(q[0], q[1], K.mix(cv.get(*q), pal["g"], 0.55))
    return cv


ORES = {"zinc": ore_zinc, "aether": ore_aether, "lithite": ore_lithite, "orichalcum": ore_orichalcum,
        "mithril": ore_mithril}


def ore(metal, host_name, seed=0):
    return ORES[metal](host_name, seed)


ORE_FACES = {
    "zinc_ore": ("zinc", "stone"), "deepslate_zinc_ore": ("zinc", "deepslate"),
    "aether_ore": ("aether", "stone"), "deepslate_aether_ore": ("aether", "deepslate"),
    "lithite_ore": ("lithite", "stone"), "deepslate_lithite_ore": ("lithite", "deepslate"),
    "deepslate_mithril_ore": ("mithril", "deepslate"), "nether_orichalcum_ore": ("orichalcum", "netherrack"),
}


# ------------------------------------------------------------------ metal shading helpers
def mramp(mid, n=6, lo=-0.76, hi=0.7):
    """Six hue-shifted tones (0 deepest .. 5 brightest) around a metal's mid tone."""
    return K.ramp(tuple(mid[:3]), n, lo, hi)


def fill(c):
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, c)
    return cv


def bevel(cv, r, x0=0, y0=0, x1=15, y1=15, hi=5, hi2=4, lo=0, lo2=1, double=True):
    """Lit top/left rim, shaded bottom/right rim (and an inner rim one tone softer)."""
    for x in range(x0, x1 + 1):
        cv.set(x, y0, r[hi])
        cv.set(x, y1, r[lo])
    for y in range(y0, y1 + 1):
        cv.set(x0, y, r[hi])
        cv.set(x1, y, r[lo])
    cv.set(x1, y0, r[(hi + lo) // 2 + 1])
    cv.set(x0, y1, r[(hi + lo) // 2])
    if double:
        for x in range(x0 + 1, x1):
            cv.set(x, y0 + 1, r[hi2])
            cv.set(x, y1 - 1, r[lo2])
        for y in range(y0 + 1, y1):
            cv.set(x0 + 1, y, r[hi2])
            cv.set(x1 - 1, y, r[lo2])


def emboss(cv, mask, r, base=3, raised=True, socket=True):
    """Shade a pixel set as a raised (or sunk) shape lit from the top-left: top/left edge pixels light, bottom/right
    edge pixels dark (inverted when sunk), a socket shadow cast bottom-right of raised shapes."""
    for (x, y) in mask:
        tl = (x, y - 1) not in mask or (x - 1, y) not in mask
        br = (x, y + 1) not in mask or (x + 1, y) not in mask
        if tl and not br:
            t = base + 2 if raised else base - 2
        elif br and not tl:
            t = base - 2 if raised else base + 2
        elif tl and br:
            t = base + 1 if raised else base - 1
        else:
            t = base
        cv.set(x, y, r[max(0, min(5, t))])
    if socket and raised:
        for (x, y) in mask:
            for q in ((x + 1, y + 1), (x + 1, y), (x, y + 1)):
                if q not in mask and 0 <= q[0] < 16 and 0 <= q[1] < 16:
                    cv.set(q[0], q[1], r[max(0, base - 2)])


def rivet(cv, x, y, r):
    """2x2 domed rivet: bright cap, mid sides, deep pixel bottom-right."""
    cv.set(x, y, r[5])
    cv.set(x + 1, y, r[3])
    cv.set(x, y + 1, r[3])
    cv.set(x + 1, y + 1, r[0])


def rivet1(cv, x, y, r):
    """1px rivet with its shadow."""
    cv.set(x, y, r[5])
    cv.set(x + 1, y + 1, r[0])
    cv.set(x + 1, y, r[1])
    cv.set(x, y + 1, r[2])


# ------------------------------------------------------------------ storage blocks
PAL = {  # mid tones (wf/metals.py PALETTES, warmed or cooled a touch so each metal has its own hue)
    "zinc": (156, 168, 182), "brass": (204, 156, 64), "mithril": (148, 198, 234),
    "orichalcum": (222, 112, 62), "aether": (62, 214, 222),
}


def block_zinc():
    """Galvanised corrugated sheet: rounded vertical ribs lit on their left flank, a lapped seam with rivets."""
    r = mramp(PAL["zinc"])
    rib = [4, 5, 4, 2]
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, r[rib[x % 4]])
    for x in range(16):  # lap seam: the upper sheet's edge overlaps the lower one
        cv.set(x, 7, r[rib[x % 4] - 1])
        cv.set(x, 8, r[0])
        cv.set(x, 9, r[min(5, rib[x % 4] + 1)] if x % 4 < 2 else r[rib[x % 4]])
        cv.set(x, 0, r[min(5, rib[x % 4] + 1)])
        cv.set(x, 15, r[max(0, rib[x % 4] - 2)])
    for x in (2, 10):
        rivet1(cv, x, 5, r)
    for x in (6, 14):
        rivet1(cv, x, 11, r)
    # galvanised spangle: two soft frost flakes
    for x, y in ((5, 2), (6, 2), (6, 3), (12, 12), (13, 13), (12, 13)):
        cv.set(x, y, K.mix(cv.get(x, y), (240, 248, 255), 0.4))
    return cv


def _gear_mask(cx, cy, r_out, r_tooth, teeth, hole):
    m = set()
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            tooth = math.cos(math.atan2(dy, dx) * teeth) > 0.3
            if hole < d <= r_out or (tooth and d <= r_tooth):
                m.add((x, y))
    return m


COG = _rows("""
....####....
.##.####.##.
.##########.
..###oo###..
####oooo####
####oooo####
####oooo####
####oooo####
..###oo###..
.##########.
.##.####.##.
....####....
""")


def block_brass():
    """Polished brass: a bevelled plate with corner rivets and an embossed cog in the middle."""
    r = mramp(PAL["brass"], lo=-0.74, hi=0.9)
    cv = fill(r[2])
    # brushed bands: two long horizontal lighter runs
    cv = fill(r[2])
    bevel(cv, r)
    gear = {(2 + x, 2 + y) for y, row in enumerate(COG) for x, ch in enumerate(row) if ch == "#"}
    for (x, y) in gear:  # cast shadow first, then the cog face over it
        for q in ((x + 1, y), (x, y + 1), (x + 1, y + 1), (x - 1, y), (x, y - 1)):
            if q not in gear and 2 <= q[0] <= 13 and 2 <= q[1] <= 13:
                cv.set(q[0], q[1], r[0] if q[0] > x or q[1] > y else r[1])
    for (x, y) in gear:
        tl = (x, y - 1) not in gear or (x - 1, y) not in gear
        br = (x, y + 1) not in gear or (x + 1, y) not in gear
        cv.set(x, y, r[5] if tl and not br else r[3] if br and not tl else r[4])
    for y, row in enumerate(COG):  # the axle hole shows the plate a step down, shadowed on its top-left
        for x, ch in enumerate(row):
            if ch == "o":
                cv.set(2 + x, 2 + y, r[0] if (1 + x, 2 + y) in gear or (2 + x, 1 + y) in gear else r[2])
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        cv.set(x, y, r[5])
        cv.set(x + 1 if x < 8 else x - 1, y, r[3])
    return cv


def block_mithril():
    """Pale mithril plate under a raised diagonal lattice of filigree, a star-cut stud at every crossing."""
    r = mramp(PAL["mithril"], lo=-0.74, hi=0.76)
    cv = fill(r[3])
    for y in range(16):
        for x in range(16):
            u, v = (x + y) % 8, (x - y) % 8
            if u == 0 or v == 0:
                cv.set(x, y, r[5] if u == 0 else r[4])
            elif u == 1 or v == 1:
                cv.set(x, y, r[0] if u == 1 else r[1])
            elif u == 7 or v == 7:
                cv.set(x, y, r[3])
    for x, y in ((0, 0), (8, 0), (4, 4), (12, 4), (0, 8), (8, 8), (4, 12), (12, 12)):
        cv.set(x, y, (255, 255, 255))
        cv.set((x + 1) % 16, y, r[5])
        cv.set(x, (y + 1) % 16, r[4])
    return cv


def block_orichalcum():
    """Hammered orichalcum: four big round hammer dents (shadow on the upper-left wall, light caught on the
    lower-right wall) inside a heavy rim."""
    r = mramp(PAL["orichalcum"], lo=-0.74, hi=0.72)
    cv = fill(r[3])
    for cx, cy in ((5.0, 5.0), (11.0, 5.0), (5.0, 11.0), (11.0, 11.0)):
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                if d <= 2.9:
                    k = (dx + dy) / (max(d, 0.01) * 1.41)
                    if d > 1.9:
                        cv.set(x, y, r[1] if k < -0.35 else r[5] if k > 0.35 else r[2])
                    else:
                        cv.set(x, y, r[2] if k < -0.2 else r[4] if k > 0.5 else r[3])
    bevel(cv, r)
    return cv


def block_aether():
    """Aether crystal columns seen end-on: a honeycomb of hexagonal faces, each lit on its top-left facets, with
    glowing seams between them."""
    r = mramp(PAL["aether"], lo=-0.74, hi=0.78)
    seam = (196, 255, 252)
    pts = [(0, 0), (8, 0), (4, 8), (12, 8)]
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            best = []
            for px, py in pts:
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        dx, dy = x + 0.5 - (px + 0.5 + ox), y + 0.5 - (py + 0.5 + oy)
                        # hex metric (pointy cells)
                        d = max(abs(dx) * 0.87 + abs(dy) * 0.5, abs(dy))
                        best.append((d, dx, dy))
            best.sort()
            d, dx, dy = best[0]
            if best[1][0] - d < 0.75:
                cv.set(x, y, seam if (x + y) % 3 else r[5])
                continue
            k = (dx + dy * 1.2) / max(d, 0.01)
            if d < 1.6:
                cv.set(x, y, r[4] if k < 0 else r[3])
            else:
                cv.set(x, y, r[5] if k < -0.9 else r[4] if k < -0.2 else r[2] if k < 0.8 else r[1])
    return cv


# ------------------------------------------------------------------ raw-ore blocks
def raw_zinc():
    """Raw zinc: the ore's slanted platelets packed tight, each with a bright top edge and a dark lip."""
    r = mramp(PAL["zinc"], lo=-0.8, hi=0.72)
    cv = fill(r[0])
    plate = ["..55554", ".434443", "3332221", "11111.."]  # slanted plate, lit top edge, dark lower lip
    spots = [(0, 0), (8, 1), (4, 4), (12, 5), (0, 8), (9, 9), (4, 12), (13, 13), (-2, 4), (6, -2)]
    for ox, oy in spots:
        for y, row in enumerate(plate):
            for x, ch in enumerate(row):
                if ch != ".":
                    cv.set((ox + x) % 16, (oy + y) % 16, r[int(ch)])
    return cv


def raw_mithril():
    """Raw mithril: smooth pale pebbles in dark seams with a few star glints."""
    r = mramp(PAL["mithril"], lo=-0.82, hi=0.74)
    idx = cobble_idx("rawmith", 3, (2, 3, 3, 2, 4), 0, 1.0, 0.9)
    cv = K.paint(idx, r)
    for x, y in ((3, 2), (12, 6), (6, 12)):
        cv.set(x, y, (255, 255, 255))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = ((x + dx) % 16, (y + dy) % 16)
            cv.set(q[0], q[1], K.mix(cv.get(*q), (240, 252, 255), 0.5))
    return cv


def raw_orichalcum():
    """Raw orichalcum: fat rounded nuggets packed together with molten light glowing in the cracks."""
    r = mramp(PAL["orichalcum"], lo=-0.7, hi=0.72)
    hot = [(255, 214, 96), (255, 156, 52)]
    pts = _cells("rawori", 3, 0.28)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            (d1, t, px, py), (d2, _, _, _) = _near(pts, x + 0.5, y + 0.5)
            gap = math.sqrt(d2) - math.sqrt(d1)
            if gap < 0.8:
                cv.set(x, y, hot[0] if (x * 7 + y * 3) % 5 == 0 else hot[1])
                continue
            dx = (x + 0.5 - px + 8) % 16 - 8
            dy = (y + 0.5 - py + 8) % 16 - 8
            d = math.hypot(dx, dy)
            k = (dx + dy) / max(d, 0.01) * min(1.0, d / 3.0)
            cv.set(x, y, r[5] if k < -0.7 else r[4] if k < -0.25 else r[3] if k < 0.3 else r[2] if gap > 1.6 else r[1])
    return cv


BLOCK_FACES = {
    "zinc_block": block_zinc, "brass_block": block_brass, "mithril_block": block_mithril,
    "orichalcum_block": block_orichalcum, "aether_block": block_aether,
    "raw_zinc_block": raw_zinc, "raw_mithril_block": raw_mithril, "raw_orichalcum_block": raw_orichalcum,
}


def faces():
    out = {}
    for name, (metal, h) in ORE_FACES.items():
        out[name] = ore(metal, h, 3 if h == "stone" else 5)
    for name, fn in BLOCK_FACES.items():
        out[name] = fn()
    from . import blocktex_plate, blocktex_stone
    for mod in (blocktex_plate, blocktex_stone):
        for name, fn in mod.FACES.items():
            out[name] = fn()
    return out


def textures(written):
    """Repaint the faces this module owns; never adds a path that the other generators did not write."""
    out = {}
    for name, cv in faces().items():
        key = f"block/{name}"
        if key in written:
            out[key] = cv
    return out

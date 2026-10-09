"""The Clockwork Carnival (La Fête foraine mécanique): an abandoned steam-powered carnival in a flowering birch wood.
Colossal tier (tools/BUILDING.md §1, §12 concept 33, §10 legacy-dungeon template, §15), steampunk accents
(tools/STYLE_STEAMPUNK.md: a brass ferris wheel driven by a chain from a steam engine house, brass automaton horses,
a steam calliope, a coaster on white trestles, edison lamps and lanterns strung on chains).

Silhouette (one noun phrase, §15.1): a colossal 70-high brass ferris wheel beside a red-and-white striped big top,
a white-trestled roller coaster looping round the whole fairground, a domed carousel and a clown's head the size of
a house, among birches and flowers.

Layout, ground y = 0 (feet 1), x east, z south. Big top centre (0, -56); wheel axle (-70, 37), wheel planes z -9/-3.
  * the approach (south-east, outside the fence): the performers' camp and its waystone (painted wagons round a
    fire), a path west through a birch grove (the wheel's crown above the trees), then north to the ticket gate
    (two domed towers, a lit arch, ticket booths); the arch frames the wheel and the big top (the reveal);
  * the midway (lamp posts, string lights, eight game stalls), under the coaster's trestle bridge, to the plaza
    (hub, waystone) round the steam calliope wagon;
  * branches: the carousel of brass automaton horses under its ribbed dome (east), the hall of mirrors (a glass and
    tinted-glass maze, north-east), the haunted funhouse behind a giant clown-automaton face (west: the mouth, the
    barrel of fun, the tilting room, the automaton gallery, the dressing room, the stair hall, the haunted attic, the
    slide and its one-way exit door), the engine house that drives the wheel (boiler, engine, flywheel and the drive
    chain up to the axle), the ringmaster's caravan (north-west, optional);
  * the climb: from the coaster station, up the lift hill (stairs either side of the rail, landings every ten) to
    the summit platform; or from the engine house up the wheel's maintenance ladder tower to the axle platform and
    along the high catwalk to the summit; down the first drop to the brake platform beside the big top (site of
    grace);
  * the boss: through the canvas gangway (mist) into the big top's upper gallery, down the aisle into the circus
    ring (36 wide, six tiers of benches round it, 25+ headroom; the Clockwork Ringmaster);
  * the treasury: the ringmaster's strongbox wagon backstage, behind sealed bars at the performers' gate;
  * shortcuts (§10.4): the helter-skelter's drop from the summit into its pool by the plaza, the wheel's
    bubble-column maintenance lift (engine house yard -> axle platform), the funhouse's one-way exit door; after the
    boss, the big top's front door and the backstage door open only from inside.
Loot gradient (§15.6): camp, gate and stalls tier 1; plaza, carousel, mirrors 1-2; funhouse, engine house, caravan
2; summit, axle platform 2-3; brake house 3; the strongbox wagon 3-5.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, IRON, MAHOGANY, PIPES, TABLE, TREAD, VERD, W,
                       fbm, hash01, hash3, vnoise)
from ..parts import LOOT, MOD
from .cloud_pagoda import Ctx, candle, carpet, hang, slab
from .verdant_arboretum import light_map

# the champion of the big top: the Clockwork Ringmaster (entity/boss/Ringmaster.java, tools/BOSSES.md)
BOSS = "brasshaven:ringmaster"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_AUTO = W + "turbine_automaton"
MOB_GUNNER = W + "boiler_gunner"
MOB_MITE = W + "rust_mite"
MOB_WISP = W + "lantern_wisp"
MOB_BANSHEE = W + "banshee"
MOB_MARKS = W + "bandit_marksman"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
GRASS = "grass_block[snowy=false]"
BLOG, BLOGX, BLOGZ = "birch_log[axis=y]", "birch_log[axis=x]", "birch_log[axis=z]"
SBLOG, SBLOGX, SBLOGZ = "stripped_birch_log[axis=y]", "stripped_birch_log[axis=x]", "stripped_birch_log[axis=z]"
BPL, BP_ST, BP_SL, BP_FENCE = "birch_planks", "birch_stairs", "birch_slab", "birch_fence"
SP, SP_ST, SP_SL, SP_FENCE = "spruce_planks", "spruce_stairs", "spruce_slab", "spruce_fence"
DO, DO_ST, DO_SL, DO_FENCE = "dark_oak_planks", "dark_oak_stairs", "dark_oak_slab", "dark_oak_fence"
DLOG, DLOGX, DLOGZ = "dark_oak_log[axis=y]", "dark_oak_log[axis=x]", "dark_oak_log[axis=z]"
BRICK, SB, MSB = "bricks", "stone_bricks", "mossy_stone_bricks"
SMK, SSMK = W + "smokestack_bricks", W + "sooty_smokestack_bricks"
DIB = W + "dark_iron_bricks"
GILD, BTILE = W + "gilded_trim", W + "brass_tiles"
PARQ = W + "mahogany_parquet"
BLEAVES = "birch_leaves[distance=1,persistent=true,waterlogged=false]"
GLASS, GLASSB, TINT = "glass_pane", "glass", "tinted_glass"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SLANT_H = "soul_lantern[hanging=true,waterlogged=false]"
CLANT_H = "copper_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CCHAIN = "copper_chain[axis=y,waterlogged=false]"
FROG = "ochre_froglight[axis=y]"
RED, WHITE, YEL = "red_wool", "white_wool", "yellow_wool"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FLOWERS = ("poppy", "dandelion", "cornflower", "allium", "oxeye_daisy", "azure_bluet", "lily_of_the_valley",
           "red_tulip", "orange_tulip", "pink_tulip", "white_tulip")
TALL = ("lilac", "rose_bush", "peony")

# ------------------------------------------------------------------ dimensions
GC = (0, -8)                                     # ground and fence centre
TX, TZ, TR = 0, -56, 34                          # big top centre and wall radius
RING = 18                                        # ring floor radius (36 wide)
WX, WY, WR = -70, 37, 30                         # wheel axle x, y, rim radius
WZ0, WZ1 = -9, -3                                # the wheel's two rim planes
FZ0, FZ1 = -12, 0                                # the A-frames
PLAT_Y = 31                                      # coaster summit platform deck
BRAKE_Y = 12                                     # brake platform deck (= the big top's gallery floor)
AXLE_DECK = 36                                   # axle platform deck
HUB = (0, 10)                                    # plaza centre (r 15)
CAMP = (68, 100)
FUN = (-64, 12, -38, 38)                         # funhouse walls (x0, z0, x1, z1)
MIR = (20, -20, 46, -4)                          # hall of mirrors walls
CAR = (34, 14)                                   # carousel centre
ENG = (-88, -42, -62, -26)                       # engine house walls
HS = (-15, -12)                                  # helter-skelter tower centre
LIFT = (-70, -22)                                # bubble lift column
LADDER = (-70, -17)                              # maintenance ladder column (spine at z + 1)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def sup(x, z, rx, rz, c=GC, n=4.0):
    return abs((x - c[0]) / rx) ** n + abs((z - c[1]) / rz) ** n


def in_ground(x, z):
    return sup(x, z, 104, 102) <= 1.0 or (-12 <= x <= 88 and 78 <= z <= 108)


def face_of(dx, dz):
    if abs(dz) >= abs(dx):
        return "south" if dz > 0 else "north"
    return "east" if dx > 0 else "west"


def tent_r(x, z):
    return math.hypot(x - TX, z - TZ)


# ------------------------------------------------------------------ small helpers
def fp(C, x, y, z, spec):
    if (x, y, z) in C.keep:
        return False
    C.set(x, y, z, spec)
    return True


def spawner(C, x, y, z, mob):
    C.keep.discard((x, y, z))
    C.bp.spawner(x, y, z, mob)


def chest(C, x, y, z, facing, table):
    C.keep.discard((x, y, z))
    C.bp.chest(x, y, z, facing, loot=LOOT + table)


def barrel(C, x, y, z):
    C.keep.discard((x, y, z))
    C.bp.barrel(x, y, z)


def waystone(C, x, y, z):
    C.keep.discard((x, y, z))
    C.set(x, y, z, MOD["waystone"])


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{W}brass_railing[facing={facing}]")


def lever_on(C, x, y, z, facing):
    C.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def box(C, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def carve(C, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.clear(x, y, z)


def room(C, x0, y0, z0, x1, y1, z1, pred=None):
    """Register an interior volume (lit to 8 by the lighting pass); ``pred(x, z)`` narrows it."""
    C.rooms.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), pred))


def oneway_door(C, x, y, z, side, wall):
    """An iron door at (x, y, z) in a wall; its lever sits beside it on the ``side`` face only (the one side it opens
    from)."""
    dx, dz = DV[side]
    C.keep.discard((x, y, z))
    C.keep.discard((x, y + 1, z))
    C.bp.door(x, y, z, side, wood="iron")
    px, pz = (1, 0) if dx == 0 else (0, 1)
    wx, wz = x + px, z + pz
    for yy in (y, y + 1, y + 2):
        C.set(wx, yy, wz, wall)
    C.set(x, y + 2, z, wall)
    C.clear(wx + dx, y + 1, wz + dz)
    lever_on(C, wx + dx, y + 1, wz + dz, side)
    for s in (1, -1):
        C.clear(x + dx * s, y, z + dz * s)
        C.clear(x + dx * s, y + 1, z + dz * s)


def lamp_post(C, x, y, z, h=4, top=LANT):
    """A dark-iron lamp post with a lantern on top; feet y."""
    C.set(x, y, z, IRON)
    for yy in range(y + 1, y + h):
        C.set(x, yy, z, f"{W}dark_iron_plating_wall")
    C.set(x, y + h, z, top)


def line3(C, p0, p1, spec, keep_free=False):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1)
    out = []
    for i in range(n + 1):
        t = i / float(n)
        p = (int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), int(round(z0 + (z1 - z0) * t)))
        if not out or out[-1] != p:
            out.append(p)
    for p in out:
        if keep_free and not C.free(*p):
            continue
        C.set(*p, spec(p) if callable(spec) else spec)
    return out


def string_lights(C, a, b, every=4, lamp=LANT_H):
    """A sagging wire of chain between two points (x, y, z), lanterns hung every few blocks from vertical chain
    knots (a lantern can only hang from an upright chain)."""
    (x0, y0, z0), (x1, y1, z1) = a, b
    n = max(abs(x1 - x0), abs(z1 - z0), 1)
    ax = "x" if abs(x1 - x0) >= abs(z1 - z0) else "z"
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        sag = 1.6 * math.sin(math.pi * t)
        p = (int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t - sag)), int(round(z0 + (z1 - z0) * t)))
        if not pts or pts[-1] != p:
            pts.append(p)
    for i, p in enumerate(pts):
        if not C.free(*p):
            continue
        if 0 < i < len(pts) - 1 and i % every == every // 2 and C.free(p[0], p[1] - 1, p[2]):
            C.set(*p, CHAIN)
            C.set(p[0], p[1] - 1, p[2], lamp)
        else:
            C.set(*p, f"iron_chain[axis={ax},waterlogged=false]")


def birch(C, x, z, y0, h, seed):
    """A birch: a white trunk h high, a rounded crown of persistent leaves, sometimes a second leader."""
    for yy in range(y0, y0 + h):
        C.put(x, yy, z, BLOG)
    top = y0 + h
    r0 = 2.3 + hash01(x, z, seed) * 0.8
    for yy in range(top - 4, top + 2):
        t = (yy - (top - 1)) / 3.0
        r = r0 * math.sqrt(max(0.0, 1.0 - t * t * 0.7)) if yy < top + 1 else 1.0
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d > r or (dx == 0 and dz == 0 and yy < top):
                    continue
                if hash3(x + dx, yy, z + dz, seed) < 0.15 * d / max(r, 1.0):
                    continue
                if yy < y0 + 3:
                    continue
                if C.get(x + dx, yy, z + dz) in (None, AIR) and (x + dx, yy, z + dz) not in C.keep:
                    C.bp.set(x + dx, yy, z + dz, BLEAVES)


# ------------------------------------------------------------------ ground and paths
def path_seg(C, a, b, hw, kind):
    (ax, az), (bx, bz) = a, b
    L = max(1.0, math.hypot(bx - ax, bz - az))
    x0, x1 = int(min(ax, bx) - hw - 2), int(max(ax, bx) + hw + 2)
    z0, z1 = int(min(az, bz) - hw - 2), int(max(az, bz) + hw + 2)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            vx, vz = bx - ax, bz - az
            t = max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / (L * L)))
            d = math.hypot(x - ax - vx * t, z - az - vz * t)
            w = hw + (vnoise(x, z, 5.0, 61) - 0.5) * 1.4
            if d <= w:
                C.paths.setdefault((x, z), kind)


def path_poly(C, pts, hw, kind):
    for i in range(len(pts) - 1):
        path_seg(C, pts[i], pts[i + 1], hw, kind)


def plan_paths(C):
    # the approach: camp -> west through the birches -> north to the gate
    path_poly(C, [CAMP, (54, 101), (36, 98), (20, 101), (6, 97), (0, 92), (0, 88)], 2.2, "track")
    # the midway (main avenue) and the plaza
    for x in range(-5, 6):
        for z in range(24, 90):
            C.paths[(x, z)] = "midway"
    for x in range(-16, 17):
        for z in range(-6, 27):
            if math.hypot(x - HUB[0], z - HUB[1]) <= 15.3:
                C.paths[(x, z)] = "plaza"
    lanes = [
        [(-13, 17), (-18, 28), (-22, 38)],                       # station
        [(-14, 12), (-26, 20), (-36, 25)],                       # funhouse mouth
        [(-6, -4), (-7, -20), (-24, -23), (-46, -24), (-58, -32), (-62, -34)],  # engine house
        [(-74, -43), (-74, -52)],                                # caravan
        [(0, -5), (0, -18)],                                     # big top front
        [(-9, -2), (-15, -7)],                                   # helter-skelter door
        [(14, 13), (21, 14)],                                    # carousel
        [(9, -3), (17, -10), (19, -12)],                         # mirrors
        [(48, 14), (56, 4), (53, -8), (47, -10)],                # carousel -> mirrors' back door
        [(-38, 14), (-30, 8), (-16, 6)],                         # funhouse exit -> plaza
        [(-70, -25), (-70, -24)],                                # lift foot
        [(-58, -24), (-66, -24), (-70, -20)],                    # ladder foot
    ]
    for pts in lanes:
        path_poly(C, pts, 1.6, "lane")
    # the ring path round the big top
    for x in range(TX - 40, TX + 41):
        for z in range(TZ - 40, TZ + 41):
            r = tent_r(x, z)
            if 35.5 <= r <= 37.8 + (vnoise(x, z, 6.0, 62) - 0.5):
                C.paths.setdefault((x, z), "lane")


def path_block(x, z, kind):
    h = hash01(x, z, 71)
    v = vnoise(x, z, 6.0, 72)
    if kind == "midway":
        if x in (-5, 5):
            return "polished_andesite" if h < 0.8 else "andesite"
        if x == 0 and z % 2 == 0:
            return BTILE
        return "packed_mud" if v > 0.55 else ("mud_bricks" if h < 0.3 else "dirt_path")
    if kind == "plaza":
        r = math.hypot(x - HUB[0], z - HUB[1])
        a = math.atan2(z - HUB[1], x - HUB[0])
        if r < 2.5:
            return GILD
        if 14.3 < r:
            return "polished_andesite"
        if int(r) % 5 == 0:
            return BTILE
        return "smooth_sandstone" if int((a + math.pi) / (2 * math.pi) * 16) % 2 else "cut_sandstone"
    if kind == "lane":
        return "dirt_path" if h < 0.55 else ("gravel" if h < 0.8 else "coarse_dirt")
    return "dirt_path" if h < 0.5 else ("coarse_dirt" if h < 0.75 else "gravel")


def ground(C):
    """The site's own ground: a flowering birch meadow on three layers (six at the edge), paths written into it, one
    layer of air over it (terrain bumps vanish)."""
    xs = range(-106, 107)
    zs = range(-112, 111)
    cols = [(x, z) for x in xs for z in zs if in_ground(x, z)]
    S = set(cols)
    C.ground = S
    for (x, z) in cols:
        edge = any((x + dx, z + dz) not in S for dx, dz in N4)
        for y in range(-6 if edge else -2, 0):
            C.bp.set(x, y, z, "dirt" if y > -3 else "stone")
        k = C.paths.get((x, z))
        if k:
            spec = path_block(x, z, k)
        else:
            h = hash01(x, z, 81)
            v = fbm(x, z, 14.0, 82)
            spec = GRASS
            if v > 0.68 and h < 0.4:
                spec = "moss_block"
            elif h < 0.04:
                spec = "coarse_dirt"
            elif h < 0.06:
                spec = "rooted_dirt"
        C.bp.set(x, 0, z, spec)
        C.bp.set(x, 1, z, AIR)
        if k:
            C.bp.set(x, 2, z, AIR)


def meadow(C):
    """Flowers in patches (wildflowers under the birches, tulip and poppy drifts, lilacs and rose bushes), leaf
    litter and birches outside everything else; dense round the approach (the grove that hides the fairground)."""
    placed = []
    for (x, z) in sorted(C.ground):
        if (x, z) in C.paths or (x, z) in C.busy or C.bp.get(x, 0, z) != "minecraft:grass_block":
            continue
        if C.bp.get(x, 1, z) != AIR or in_busy(C, x, z):
            continue
        h = hash01(x, z, 91)
        v = vnoise(x, z, 9.0, 92)
        f = fbm(x, z, 22.0, 93)
        if v > 0.55 and h < 0.55:
            k = int(vnoise(x, z, 13.0, 94) * len(FLOWERS)) % len(FLOWERS)
            C.bp.set(x, 1, z, FLOWERS[k] if h < 0.42 else FLOWERS[(k + 3) % len(FLOWERS)])
        elif f > 0.55 and h < 0.5:
            C.bp.set(x, 1, z, f"wildflowers[facing={('north', 'east', 'south', 'west')[int(h * 8) % 4]},"
                              f"flower_amount={1 + int(h * 8) % 4}]")
        elif v < 0.25 and h < 0.06:
            t = TALL[int(h * 100) % 3]
            C.bp.set(x, 1, z, f"{t}[half=lower]")
            C.bp.set(x, 2, z, f"{t}[half=upper]")
        elif h < 0.07:
            C.bp.set(x, 1, z, "short_grass")
        elif h < 0.085:
            C.bp.set(x, 1, z, "bush")
    # birches
    cand = sorted(C.ground, key=lambda p: hash01(p[0], p[1], 95))
    for (x, z) in cand:
        if len(placed) > 260:
            break
        inside = sup(x, z, 96, 94) <= 1.0
        grove = (x > -14 and z > 84) or not inside
        dens = 0.035 if grove else 0.008
        if hash01(x, z, 96) > dens * 18:
            continue
        if (x, z) in C.paths or in_busy(C, x, z, 3) or C.bp.get(x, 0, z) not in ("minecraft:grass_block",
                                                                                   "minecraft:moss_block"):
            continue
        if any(abs(x - px) + abs(z - pz) < (5 if grove else 7) for (px, pz) in placed):
            continue
        if any((x + dx, z + dz) not in C.ground for dx in (-3, 3) for dz in (-3, 3)):
            continue
        placed.append((x, z))
        birch(C, x, z, 1, 6 + int(hash01(x, z, 97) * 6), 98 + x * 7 + z)
        C.bp.set(x, 0, z, "rooted_dirt" if hash01(x, z, 99) < 0.5 else GRASS)
        for dx, dz in N4:
            if C.bp.get(x + dx, 1, z + dz) == AIR and hash01(x + dx, z + dz, 100) < 0.5:
                C.bp.set(x + dx, 1, z + dz, "leaf_litter[facing=north,segment_amount=3]")


def in_busy(C, x, z, m=0):
    for (x0, z0, x1, z1) in C.boxes:
        if x0 - m <= x <= x1 + m and z0 - m <= z <= z1 + m:
            return True
    return (x, z) in C.busy


def reserve(C, x0, z0, x1, z1):
    C.boxes.append((min(x0, x1), min(z0, z1), max(x0, x1), max(z0, z1)))


# ------------------------------------------------------------------ the roller coaster
START = (-28, 50)
SEGS = [
    ("north", [(16, 0)]),                                                                   # A station
    ("north", [(10, 1), (3, 0), (10, 1), (3, 0), (11, 1)]),                                  # B lift hill
    ("north", [(16, 0)]),                                                                   # C summit
    ("north", [(6, -1), (3, 0)]),                                                           # D first drop
    ("west", [(2, 0), (13, -1), (7, 0)]),                                                   # F second drop
    ("north", [(4, 0), (4, -1), (10, 0), (4, 1), (16, 0)]),                                 # G dip, brake platform
    ("north", [(4, 0), (8, 1), (18, 0)]),                                                   # H
    ("east", [(12, 0), (8, -1), (14, 0), (12, 1), (12, 0), (14, -1), (10, 0), (6, 1), (25, 0)]),  # I
    ("south", [(6, 0), (8, -1), (12, 0), (10, 1), (16, 0), (12, -1), (14, 0), (8, 1), (12, 0), (8, -1), (40, 0)]),
    ("west", [(10, 0), (2, 1), (60, 0), (8, -1), (10, 0)]),                                  # K
]


def track_cells():
    """[(x, z, y, dir_in, dir_out)] round the closed loop; START is the corner the loop closes on."""
    pts = [(START[0], START[1], 0)]
    dirs = []
    x, z = START
    y = 0
    for d, runs in SEGS:
        dx, dz = DV[d]
        for n, dy in runs:
            for _ in range(n):
                x += dx
                z += dz
                y += dy
                pts.append((x, z, y))
                dirs.append(d)
    assert (x, z) == (START[0] + 1, START[1]) and y == 0, (x, z, y)
    pts = pts[1:] + pts[:1]                    # START last: it closes the loop
    dirs = dirs + [SEGS[0][0]]
    out = []
    n = len(pts)
    for i in range(n):
        d_in = dirs[i]
        d_out = dirs[(i + 1) % n]
        out.append((pts[i][0], pts[i][1], pts[i][2], d_in, d_out))
    return out


def perp(d):
    dx, dz = DV[d]
    return -dz, dx


def coaster(C):
    """The coaster: a 5-wide deck (rail in the middle on an iron spine, walkable treads either side, a log edge with
    brass railings), stairs on every slope, flat 5 x 5 squares on the corners, white birch trestle bents every four
    blocks (never on a path), solid embankment where the deck runs low."""
    T = track_cells()
    n = len(T)
    roles = {}

    def put_role(x, z, role, y, info):
        pri = {"rail": 3, "walk": 2, "edge": 1}
        old = roles.get((x, z))
        if old is None or pri[role] > pri[old[0]]:
            roles[(x, z)] = (role, y, info)

    for i, (x, z, y, d_in, d_out) in enumerate(T):
        yp = T[i - 1][2]
        yn = T[(i + 1) % n][2]
        if d_in != d_out:
            for a in range(-2, 3):
                for b in range(-2, 3):
                    m = max(abs(a), abs(b))
                    if m == 0:
                        put_role(x, z, "rail", y, ("curve", d_in, d_out))
                    elif m == 1:
                        put_role(x + a, z + b, "walk", y, None)
                    else:
                        put_role(x + a, z + b, "edge", y, face_of(a, b))
            continue
        d = d_in
        px, pz = perp(d)
        if yp == y - 1:
            side = ("stair", d)
        elif yn == y - 1:
            side = ("stair", OPP[d])
        else:
            side = None
        if yn == y + 1:
            rail = ("asc", d)
        elif yp == y + 1:
            rail = ("asc", OPP[d])
        else:
            rail = ("flat", d)
        put_role(x, z, "rail", y, rail)
        for o in (-1, 1):
            put_role(x + px * o, z + pz * o, "walk", y, side)
        for o in (-2, 2):
            put_role(x + px * o, z + pz * o, "edge", y, ("side", face_of(px * o, pz * o), side))
    C.track = roles
    curve = {frozenset(("north", "east")): "north_east", frozenset(("north", "west")): "north_west",
             frozenset(("south", "east")): "south_east", frozenset(("south", "west")): "south_west"}
    for (x, z), (role, y, info) in roles.items():
        if y <= 0:
            base = y
        else:
            base = y
        # the deck block
        if role == "rail":
            C.set(x, y, z, IRON if y > 0 else "polished_andesite")
            if info[0] == "curve":
                shape = curve[frozenset((OPP[info[1]], info[2]))]
                C.set(x, y + 1, z, f"rail[shape={shape},waterlogged=false]")
            elif info[0] == "asc":
                C.set(x, y + 1, z, f"powered_rail[powered=false,shape=ascending_{info[1]},waterlogged=false]")
            else:
                shape = "north_south" if info[1] in ("north", "south") else "east_west"
                C.set(x, y + 1, z, f"rail[shape={shape},waterlogged=false]")
            for yy in range(y + 2, y + 5):
                if C.free(x, yy, z):
                    C.clear(x, yy, z)
        elif role == "walk":
            if info and info[0] == "stair":
                C.set(x, y, z, stair(SP_ST, info[1]))
                if y > 0:
                    C.set(x, y - 1, z, SP)
            else:
                C.set(x, y, z, SP if y > 0 else "spruce_planks")
            for yy in range(y + 1, y + 5):
                if C.free(x, yy, z) or C.get(x, yy, z) in (BLEAVES,):
                    C.clear(x, yy, z)
        else:
            C.set(x, y, z, SBLOG if y > 0 else "polished_andesite")
            if (x, z) not in C.norail:
                fc = info if isinstance(info, str) else info[1]
                if y > 0 or (x, z) not in C.paths:
                    railing(C, x, y + 1, z, fc)
            else:
                for yy in range(y + 1, y + 4):
                    if C.free(x, yy, z):
                        C.clear(x, yy, z)
        # low deck: an embankment down to the ground
        if 0 < y <= 2:
            for yy in range(1, y if role != "walk" else y - (1 if info and info[0] == "stair" else 0)):
                C.set(x, yy, z, "packed_mud" if role != "edge" else "mud_bricks")
        elif y > 4 and role != "walk":
            C.set(x, y - 1, z, IRON if role == "rail" else SBLOG)
        C.busy.add((x, z))
    # trestle bents every four cells
    for i, (x, z, y, d_in, d_out) in enumerate(T):
        if y < 3 or i % 6 or d_in != d_out:
            continue
        px, pz = perp(d_in)
        posts = [(x + px * o, z + pz * o) for o in (-2, 2)]
        if any((c in C.paths or c in C.nobent) for c in posts + [(x, z)]):
            continue
        for (bx, bz) in posts:
            for yy in range(1, y - 1):
                C.set(bx, yy, bz, SBLOG)
            C.set(bx, 0, bz, "polished_andesite")
        for yy in range(6, y - 1, 6):
            for o in (-1, 0, 1):
                C.set(x + px * o, yy, z + pz * o, SBLOGX if px else SBLOGZ)
            # an X of fences under each tie on every other bent
            if i % 12 == 0:
                for k, o in enumerate((-1, 0, 1)):
                    for yb in (yy - 1 - k, yy - 5 + k):
                        if 0 < yb < yy and C.free(x + px * o, yb, z + pz * o):
                            C.set(x + px * o, yb, z + pz * o, BP_FENCE)
    # lamps on the edge posts every twelve cells along the climb and the high run
    for i, (x, z, y, d_in, d_out) in enumerate(T):
        if i % 12 or d_in != d_out or y < 4:
            continue
        px, pz = perp(d_in)
        for o in (-2, 2):
            ex, ez = x + px * o, z + pz * o
            if (ex, ez) in C.norail:
                continue
            C.set(ex, y + 1, ez, f"{W}dark_iron_plating_wall")
            C.set(ex, y + 2, ez, LANT)


def track_y(x, z):
    """Deck y of the centre-line cell (x, z) (None off the track)."""
    for (tx, tz, y, _, _) in track_cells():
        if (tx, tz) == (x, z):
            return y
    return None


def station(C):
    """The coaster station on the ground east of the rail: a long roof on brass columns, the boarding platform,
    the operator's booth with its lever bank, benches, three cars waiting on the rail."""
    x0, x1, z0, z1 = -25, -19, 34, 48
    reserve(C, x0, z0, x1, z1)
    for z in range(33, 50):
        C.norail.add((-26, z))
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 0, z, SP if (z % 3) else DO)
            for y in range(1, 6):
                if C.free(x, y, z) or (x, y, z) not in C.keep:
                    C.clear(x, y, z)
    # roof over the platform and the rail: a striped canopy
    for x in range(-31, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            y = 6 if x in (-31, x1 + 1) else 7
            C.set(x, y, z, RED if (z // 2) % 2 else WHITE)
            if x in (-31, x1 + 1) and z % 2 == 0:
                C.set(x, 5, z, stair(BP_ST, "east" if x < 0 else "west", "top") if False else slab(BP_SL, "top"))
    for z in range(z0, z1 + 1, 4):
        for x in (x0 + 0, x1):
            for y in range(1, 6):
                C.set(x, y, z, BRASS if y in (1, 5) else f"{W}dark_iron_plating_wall")
        C.set(-31, 0, z, "polished_andesite")
        for y in range(1, 6):
            C.set(-31, y, z, BRASS if y in (1, 5) else f"{W}dark_iron_plating_wall")
    # the operator's booth (north end)
    for x in range(x1 - 3, x1 + 1):
        for y in range(1, 5):
            for z in (z0, z0 + 3):
                C.set(x, y, z, BPL if (x + y) % 3 else BLOG)
        for y in range(1, 5):
            C.set(x1, y, z0 + 1, BPL)
            C.set(x1, y, z0 + 2, BPL if y != 2 else GLASS)
    for z in (z0 + 1, z0 + 2):
        C.set(x1 - 3, 1, z, slab(DO_SL, "top"))
        C.set(x1 - 3, 2, z, AIR) if False else None
    fp(C, x1 - 1, 1, z0 + 1, f"{W}mahogany_chair[facing=west]")
    lever_on(C, x1 - 1, 2, z0 + 3, "north")
    lever_on(C, x1 - 2, 2, z0 + 3, "north")
    fp(C, x1 - 2, 1, z0 + 2, GAUGE)
    chest(C, x1 - 1, 1, z0 + 2, "west", "fair_coaster")
    # benches along the platform
    for z in range(z0 + 6, z1, 3):
        fp(C, x1, 1, z, stair(BP_ST, "east"))
        fp(C, x1, 1, z + 1, stair(BP_ST, "east"))
    for z in range(z0 + 2, z1, 4):
        hang(C, x0 + 2, 5, z, LANT_H, reach=3)
        hang(C, -28, 5, z + 1, LANT_H, reach=3)
    room(C, -31, 1, z0, x1, 5, z1)
    # cars on the rail
    for z in (40, 42, 44):
        C.bp.entity(-28, 1, z, {"id": "minecraft:minecart"})
    # signboard on the canopy end
    for x in range(x0, x1 + 1):
        C.set(x, 8, z1 + 1, GILD if x in (x0, x1) else BRASS)


# ------------------------------------------------------------------ gate, fence, approach and camp
def fence(C):
    """The fairground's ornamental fence: iron bars between dark-iron posts with lanterns, broken in places,
    stepping aside for the gate, the paths and the coaster."""
    cells = []
    for x in range(-100, 101):
        for z in range(-106, 90):
            if sup(x, z, 96, 94) > 1.0:
                continue
            if any(sup(x + dx, z + dz, 96, 94) > 1.0 for dx, dz in N4):
                cells.append((x, z))
    for (x, z) in cells:
        if (x, z) in C.paths and C.paths[(x, z)] in ("track", "midway", "lane"):
            continue
        if -24 <= x <= 24 and z > 76:
            continue
        if any((x + dx, z + dz) in C.track for dx in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2)):
            continue
        if in_busy(C, x, z, 1):
            continue
        h = hash01(x, z, 111)
        if hash01(x // 5, z // 5, 112) < 0.12:
            if h < 0.4:
                C.set(x, 1, z, "iron_bars")
            continue
        if (x * 3 + z * 7) % 9 == 0:
            C.set(x, 1, z, IRON)
            C.set(x, 2, z, f"{W}dark_iron_plating_wall")
            C.set(x, 3, z, LANT if h < 0.6 else f"{W}dark_iron_plating_wall")
        else:
            C.set(x, 1, z, "iron_bars")
            C.set(x, 2, z, "iron_bars")
        if h < 0.2:
            C.put(x, 3, z, "vine[east=false,north=false,south=false,up=true,west=false]") if False else None


def onion_dome(C, cx, cz, y0, r, stripe=(RED, WHITE)):
    """An onion dome on a drum: bulges to r + 1, tapers to a gilded finial and a pennant."""
    H = int(r * 2.6) + 2
    top = y0
    for k in range(H):
        t = k / float(H)
        rr = (r + 0.9) * math.sin(math.pi * min(1.0, 0.25 + t * 0.95)) * (1.0 - t) ** 0.35
        ri = int(math.ceil(rr))
        y = y0 + k
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d > rr + 0.3:
                    continue
                if d > rr - 1.2 or k == H - 1:
                    a = math.atan2(dz, dx)
                    C.set(cx + dx, y, cz + dz, stripe[int((a + math.pi) / (2 * math.pi) * 8) % 2])
        top = y
    C.set(cx, top + 1, cz, GILD)
    C.set(cx, top + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    C.set(cx, top + 3, cz, f"{W}dark_iron_plating_wall")
    C.set(cx, top + 4, cz, "red_banner[rotation=4]")
    return top


def gate(C):
    """The ticket gate: two round towers in brass and cream with onion domes, a lit arch with a clock-face sunburst
    between them, three turnstile lanes, a ticket booth either side."""
    zc = 86
    reserve(C, -28, 82, 28, 91)
    for side in (-1, 1):
        cx = side * 15
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz)
                if d > 4.2:
                    continue
                x, z = cx + dx, zc + dz
                for y in range(0, 15):
                    if d > 3.1:
                        if y in (0, 1) or y == 14:
                            spec = BRASS
                        elif y in (6, 7) and (dx == 0 or dz == 0):
                            spec = GLASSB if y == 6 else "yellow_stained_glass"
                        else:
                            a = math.atan2(dz, dx)
                            spec = RED if int((a + math.pi) / (2 * math.pi) * 10) % 2 and 2 <= y <= 12 else \
                                "white_terracotta"
                        C.set(x, y, z, spec)
                    else:
                        C.set(x, y, z, "white_terracotta" if y in (0, 14) else AIR) if y in (0, 14) else C.clear(x, y, z)
        # a balcony ring with railings at the top
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = math.hypot(dx, dz)
                if 4.2 < d <= 5.3:
                    C.set(cx + dx, 14, zc + dz, GILD)
                    railing(C, cx + dx, 15, zc + dz, face_of(dx, dz))
        onion_dome(C, cx, zc, 15, 3)
        # the tower doors (inside the gate passage) and a lamp inside
        for y in (1, 2, 3):
            C.clear(cx - side * 4, y, zc)
            C.clear(cx - side * 3, y, zc)
        hang(C, cx, 12, zc, LANT_H, reach=3)
        fp(C, cx + side, 1, zc - 2, "barrel[facing=up,open=false]")
        chest(C, cx + side * 2, 1, zc, "west" if side > 0 else "east", "fair_gate")
        room(C, cx - 3, 1, zc - 3, cx + 3, 13, zc + 3)
    # the arch: a deep band at y 10..13 with a sunburst
    for x in range(-11, 12):
        for z in range(zc - 2, zc + 3):
            for y in range(10, 14):
                edge = z in (zc - 2, zc + 2)
                if y == 10:
                    spec = stair(BRASS_ST, "east" if x < 0 else "west", "top") if abs(x) > 8 else BRASS
                elif y == 13:
                    spec = GILD
                elif edge:
                    spec = RED if (x + y) % 4 == 0 else "white_terracotta"
                else:
                    spec = IRON
                C.set(x, y, z, spec)
        if x % 3 == 0:
            for z in (zc - 3, zc + 3):
                C.set(x, 11, z, EDISON)
    # the sunburst: a brass disc over the centre with rays and a clock face
    for dx in range(-5, 6):
        for dy in range(0, 6):
            d = math.hypot(dx, dy)
            if d > 5.4:
                continue
            a = math.atan2(dy, dx)
            ray = int((a / math.pi) * 10) % 2 == 0
            spec = GILD if d < 1.5 else ("white_terracotta" if d < 3.3 else (BRASS if ray else COPPER))
            C.set(dx, 14 + dy, zc - 2, spec)
            C.set(dx, 14 + dy, zc - 1, IRON)
    C.set(0, 16, zc - 3, f"{W}wall_cog[facing=south]")
    # turnstile lanes
    for x in (-4, 4):
        for z in range(zc - 1, zc + 2):
            C.set(x, 1, z, IRON if z == zc else f"{W}dark_iron_plating_wall")
    for x in (-8, 8):
        C.set(x, 1, zc, GEAR)
    # ticket booths
    for side in (-1, 1):
        booth(C, side * 24, zc + 1, side)


BRASS_ST = W + "brass_plating_stairs"


def booth(C, cx, cz, side):
    """A ticket booth: an octagonal kiosk with a ticket window to the south, a candy-striped pyramid roof and a
    pennant; a stool, the cash box and rolls of tickets inside."""
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if abs(dx) + abs(dz) > 5:
                continue
            x, z = cx + dx, cz + dz
            C.set(x, 0, z, PARQ)
            edge = abs(dx) == 3 or abs(dz) == 3 or abs(dx) + abs(dz) == 5
            for y in range(1, 6):
                if edge:
                    if y == 5:
                        spec = GILD
                    elif dz == 3 and abs(dx) <= 1 and y in (2, 3):
                        spec = GLASS if y == 3 else slab(BP_SL, "top")
                    elif dz == -3 and dx == 0 and y in (1, 2):
                        spec = None
                    else:
                        spec = BPL if (dx + dz) % 2 else "red_terracotta"
                    if spec:
                        C.set(x, y, z, spec)
                    else:
                        C.clear(x, y, z)
                else:
                    C.clear(x, y, z)
    C.bp.door(cx, 1, cz - 3, "north", wood="birch")
    for k in range(5):
        r = 4 - k
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if max(abs(dx), abs(dz)) == r:
                    C.set(cx + dx, 6 + k, cz + dz, RED if (dx + dz) % 2 else WHITE)
    C.set(cx, 11, cz, GILD)
    C.set(cx, 12, cz, BP_FENCE)
    C.set(cx, 13, cz, "yellow_banner[rotation=0]")
    fp(C, cx, 1, cz + 1, f"{W}mahogany_chair[facing=south]")
    chest(C, cx - 2, 1, cz + 1, "east", "fair_gate")
    fp(C, cx + 2, 1, cz + 1, "barrel[facing=up,open=false]")
    fp(C, cx + 2, 1, cz - 1, "white_carpet")
    fp(C, cx - 1, 1, cz - 1, "lectern[facing=south,has_book=false,powered=false]")
    hang(C, cx, 4, cz, LANT_H, reach=3)
    room(C, cx - 2, 1, cz - 2, cx + 2, 4, cz + 2)


def caravan(C, x0, z0, axis, colour, roof, seed, inside=None):
    """A painted showman's wagon (vardo): a 4 x 7 body on spoked wheels, a bowed roof, a door and steps at the back,
    a window either side; ``inside`` furnishes it (bed, stove, wardrobe...). Returns the body box."""
    L, Wd = 7, 4
    if axis == "x":
        cells = [(x0 + i, z0 + j) for i in range(L) for j in range(Wd)]
    else:
        cells = [(x0 + j, z0 + i) for i in range(L) for j in range(Wd)]
    xs = [c[0] for c in cells]
    zs = [c[1] for c in cells]
    bx0, bx1, bz0, bz1 = min(xs), max(xs), min(zs), max(zs)
    reserve(C, bx0 - 1, bz0 - 1, bx1 + 1, bz1 + 1)
    for (x, z) in cells:
        C.set(x, 1, z, DO)
        edge = x in (bx0, bx1) or z in (bz0, bz1)
        for y in (2, 3, 4):
            if edge:
                C.set(x, y, z, colour if (x + z + y) % 3 else GILD if y == 4 else colour)
            else:
                C.clear(x, y, z)
        # the bowed roof
        if axis == "x":
            k = min(z - bz0, bz1 - z)
        else:
            k = min(x - bx0, bx1 - x)
        C.set(x, 5 + (1 if k >= 1 else 0), z, roof)
        if k == 0:
            C.set(x, 5, z, roof)
    # wheels: spoked, at both ends of each side
    if axis == "x":
        wheels = [(bx0 + 1, bz0 - 1), (bx1 - 1, bz0 - 1), (bx0 + 1, bz1 + 1), (bx1 - 1, bz1 + 1)]
        back = (bx1 + 1, (bz0 + bz1) // 2)
        door = (bx1, (bz0 + bz1) // 2)
        dface = "east"
    else:
        wheels = [(bx0 - 1, bz0 + 1), (bx0 - 1, bz1 - 1), (bx1 + 1, bz0 + 1), (bx1 + 1, bz1 - 1)]
        back = ((bx0 + bx1) // 2, bz1 + 1)
        door = ((bx0 + bx1) // 2, bz1)
        dface = "south"
    for (x, z) in wheels:
        C.set(x, 1, z, "red_terracotta")
        C.set(x, 2, z, BP_FENCE)
    C.clear(door[0], 2, door[1])
    C.clear(door[0], 3, door[1])
    C.bp.door(door[0], 2, door[1], dface, wood="dark_oak")
    C.set(back[0], 1, back[1], stair(DO_ST, OPP[dface]))
    C.set(back[0], 0, back[1], C.get(back[0], 0, back[1]) or "dirt_path")
    # windows
    if axis == "x":
        for z in (bz0, bz1):
            C.set((bx0 + bx1) // 2, 3, z, "yellow_stained_glass_pane")
    else:
        for x in (bx0, bx1):
            C.set(x, 3, (bz0 + bz1) // 2, "yellow_stained_glass_pane")
    if inside:
        inside(bx0 + 1, bz0 + 1, bx1 - 1, bz1 - 1)
    room(C, bx0 + 1, 2, bz0 + 1, bx1 - 1, 4, bz1 - 1)
    return bx0, bz0, bx1, bz1


def camp(C):
    """The travelling performers' camp outside the fence: three painted wagons round a fire, the waystone, a juggler's
    rack, a washing line and a tethering post."""
    cx, cz = CAMP
    reserve(C, cx - 12, cz - 9, cx + 14, cz + 8)
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            if math.hypot(x - cx, z - cz) <= 3.3:
                C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 121) < 0.6 else "dirt_path")
    C.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((-2, 0, "east"), (2, 0, "west"), (0, 2, "north")):
        C.set(cx + dx, 1, cz + dz, stair(SP_ST, OPP[f]))
    waystone(C, cx - 1, 1, cz - 3)

    def bedroom(x0, z0, x1, z1):
        C.bp.bed(x0, 2, z0, "east", color="red")
        fp(C, x1, 2, z0, "barrel[facing=up,open=false]")
        fp(C, x1, 2, z1, "smoker[facing=west,lit=true]")
        candle(C, x0, 2, z1, 3)

    def costume(x0, z0, x1, z1):
        fp(C, x0, 2, z0, "red_wool")
        fp(C, x0, 2, z1, "yellow_wool")
        chest(C, x1, 2, z0, "west", "fair_camp")
        fp(C, x1, 2, z1, "cauldron")
        candle(C, x0 + 1, 2, z1, 2, "orange")

    caravan(C, cx - 11, cz - 8, "x", "green_terracotta", DO, 1, bedroom)
    caravan(C, cx + 5, cz - 7, "z", "blue_terracotta", "red_terracotta", 2, costume)
    caravan(C, cx - 9, cz + 4, "x", "yellow_terracotta", DO, 3, None)
    # juggler's rack and tethering post
    for x in range(cx + 3, cx + 7):
        C.set(x, 1, cz + 5, SP_FENCE)
    C.set(cx + 3, 2, cz + 5, "white_candle[candles=3,lit=false,waterlogged=false]")
    C.set(cx + 6, 2, cz + 5, "red_candle[candles=2,lit=false,waterlogged=false]")
    # a washing line between two posts, coloured costumes on it
    for x in (cx - 6, cx + 1):
        for y in (1, 2, 3):
            C.set(x, y, cz - 1 if False else cz + 1, SP_FENCE)
    # a hay pile and a cart wheel
    C.set(cx + 8, 1, cz + 1, "hay_block[axis=y]")
    C.set(cx + 8, 1, cz + 2, "hay_block[axis=x]")
    C.set(cx + 9, 1, cz + 1, "hay_block[axis=z]")
    lamp_post(C, cx + 2, 1, cz - 4, 3)
    lamp_post(C, cx - 4, 1, cz + 3, 3)


# ------------------------------------------------------------------ midway, stalls, plaza
STALLS = [  # (x0, z0, side, game); stalls span 6 deep (x) and 7 long (z)
    (-14, 70, -1, "ring_toss"), (-14, 60, -1, "fortune"), (-14, 36, -1, "shooting"), (-14, 27, -1, "candy"),
    (9, 70, 1, "striker"), (9, 60, 1, "ducks"), (9, 36, 1, "coconut"), (9, 27, 1, "wheel"),
]


def stall(C, x0, z0, side, game, k):
    """A game stall facing the midway: plank floor, a back wall and side walls, a front counter, a striped awning
    with a scalloped valance and a gilded sign; each game has its own back wall and props; a lantern inside."""
    x1, z1 = x0 + 5, z0 + 6
    reserve(C, x0, z0, x1, z1)
    front = x1 if side < 0 else x0                  # the counter faces the midway
    back = x0 if side < 0 else x1
    out = "east" if side < 0 else "west"
    col = ("red", "blue", "green", "purple", "orange", "cyan", "magenta", "yellow")[k % 8]
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 0, z, BPL if (x + z) % 2 else SP)
            for y in range(1, 6):
                if x == back or z in (z0, z1):
                    if z in (z0, z1) and x != back and y <= 4 and x != front:
                        spec = BPL if y < 4 else f"{col}_terracotta"
                    elif x == back:
                        spec = f"{col}_terracotta" if y in (1, 5) else BPL
                    else:
                        spec = BLOG
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
    for z in (z0, z1):
        for y in range(1, 6):
            C.set(front, y, z, BLOG)
    # the counter, opening at one end
    for z in range(z0 + 1, z1):
        if z == z1 - 1:
            continue
        C.set(front, 1, z, slab(DO_SL, "top") if z % 2 else "barrel[facing=up,open=false]")
    # awning: two courses sloping down over the counter, stripes along z, a valance
    for z in range(z0 - 1, z1 + 2):
        stripe = RED if (z // 1) % 2 else WHITE
        if col in ("blue", "cyan"):
            stripe = "blue_wool" if z % 2 else WHITE
        if col in ("green",):
            stripe = "lime_wool" if z % 2 else WHITE
        for x in range(x0, x1 + 1):
            yy = 6 if (x - x0 if side > 0 else x1 - x) < 3 else 5
            yy = 6 if abs(x - back) < 3 else 5
            C.set(x, yy, z, stripe)
        C.set(front - side * -1 if False else front + (1 if side < 0 else -1), 5, z, stripe)
        if z % 2 == 0:
            C.set(front + (1 if side < 0 else -1), 4, z, stair(BP_ST, OPP[out], "top"))
    # gilded sign over the back wall
    for z in range(z0 + 1, z1):
        C.set(back, 7, z, GILD if z in (z0 + 1, z1 - 1) else f"{col}_wool")
        C.set(back, 6, z, BRASS)
    hang(C, (x0 + x1) // 2, 4, (z0 + z1) // 2, LANT_H, reach=2)
    room(C, x0 + 1, 1, z0 + 1, x1 - 1, 4, z1 - 1)
    bx = back + (1 if side < 0 else -1)            # the cell in front of the back wall
    face = out
    if game == "ring_toss":
        for z in range(z0 + 1, z1):
            fp(C, bx, 1, z, slab(DO_SL, "top"))
            fp(C, bx, 2, z, "decorated_pot[cracked=false,facing=%s,waterlogged=false]" % face if z % 2 else
               "green_stained_glass")
            fp(C, bx + (1 if side < 0 else -1), 1, z, "brown_stained_glass" if z % 2 == 0 else AIR)
        chest(C, bx, 1, z1 - 1, face, "fair_midway")
    elif game == "fortune":
        for z in range(z0 + 1, z1):
            C.set(back, 2, z, "purple_wool")
            C.set(back, 3, z, "purple_wool")
        fp(C, bx, 1, (z0 + z1) // 2, TABLE)
        fp(C, bx, 2, (z0 + z1) // 2, "amethyst_cluster[facing=up,waterlogged=false]")
        fp(C, bx, 1, (z0 + z1) // 2 + 1, f"copper_golem_statue[copper_golem_pose=sitting,facing={face},waterlogged=false]")
        candle(C, bx, 1, z0 + 1, 3, "purple")
        candle(C, bx, 1, z1 - 1, 2, "purple")
    elif game == "shooting":
        for z in range(z0 + 1, z1):
            C.set(back, 3, z, "target[power=0]")
            C.set(back, 2, z, "yellow_terracotta" if z % 2 else "white_terracotta")
        for z in range(z0 + 1, z1, 2):
            fp(C, bx, 1, z, f"{W}copper_pipe[axis=z]")
        chest(C, bx, 1, z0 + 2, face, "fair_midway")
    elif game == "candy":
        fp(C, bx, 1, z0 + 2, "cauldron")
        fp(C, bx, 1, z0 + 3, COPPER)
        fp(C, bx, 2, z0 + 3, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
        for z in (z0 + 4, z0 + 5):
            fp(C, bx, 1, z, "end_rod[facing=up]")
            fp(C, bx, 2, z, "pink_wool")
    elif game == "striker":
        # the high striker stands outside the stall on the midway side
        sx, sz = front + (2 if side < 0 else -2), z0 - 1
        sx = x0 - 2 if side > 0 else x1 + 2
        C.set(sx, 1, sz, IRON)
        for y in range(2, 12):
            C.set(sx, y, sz, BP_FENCE if y % 2 else "red_terracotta")
        C.set(sx, 12, sz, "bell[attachment=floor,facing=north,powered=false]")
        C.set(sx, 2, sz + 1, "stone_pressure_plate[powered=false]")
        C.busy.add((sx, sz))
        for z in range(z0 + 1, z1):
            fp(C, bx, 1, z, "yellow_wool" if z % 2 else "red_wool")
        chest(C, bx, 1, z1 - 1, face, "fair_midway")
    elif game == "ducks":
        for z in range(z0 + 1, z1 - 1):
            for xx in (bx, bx + (1 if side < 0 else -1)):
                C.set(xx, 0, z, COPPER)
                C.water(xx, 1, z) if False else C.set(xx, 1, z, "water_cauldron[level=3]")
        candle(C, bx, 2, z0 + 2, 1, "yellow") if False else None
        fp(C, bx, 1, z1 - 1, "barrel[facing=up,open=false]")
    elif game == "coconut":
        for z in range(z0 + 1, z1, 2):
            fp(C, bx, 1, z, BP_FENCE)
            fp(C, bx, 2, z, "brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
        chest(C, bx, 1, z0 + 2, face, "fair_midway")
    elif game == "wheel":
        cz, cy = (z0 + z1) // 2, 3
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cols = ("red", "yellow", "blue", "lime", "white", "orange", "purple", "cyan", "magenta")
                C.set(back, cy + dy, cz + dz, f"{cols[(dz + 1) * 3 + dy + 1]}_concrete")
        C.set(bx, cy + 2, cz, f"{W}wall_cog[facing={face}]")
        fp(C, bx, 1, z0 + 1, f"copper_golem_statue[copper_golem_pose=star,facing={face},waterlogged=false]")
    # prizes on a shelf
    fp(C, bx, 3, z0 + 1, f"birch_shelf[facing={face},powered=false,side_chain=unconnected,waterlogged=false]")


def midway(C):
    """Lamp posts every eight blocks on both kerbs, string lights across the avenue, the stalls."""
    for k, (x0, z0, side, game) in enumerate(STALLS):
        stall(C, x0, z0, side, game, k)
    for z in range(80, 25, -8):
        if 46 <= z <= 54:
            continue
        for x in (-6, 6):
            for y in range(1, 7):
                C.set(x, y, z, BP_FENCE if y < 6 else DLOG)
            C.set(x, 7, z, LANT)
            C.busy.add((x, z))
        string_lights(C, (-6, 6, z), (6, 6, z), every=3)
        if z - 8 > 25 and not (46 <= z - 8 <= 54):
            string_lights(C, (-6, 6, z), (6, 6, z - 8), every=4)
    # the coaster bridge over the midway: an iron truss under the deck and a sign
    for x in range(-7, 8):
        for z in (48, 52):
            C.set(x, 7, z, IRON if x % 3 else BRASS)
        if x % 3 == 0:
            for z in range(49, 52):
                C.set(x, 7, z, IRON)
    for x in range(-4, 5):
        C.set(x, 6, 52, GILD if x in (-4, 4) else "red_wool")
        C.set(x, 6, 48, GILD if x in (-4, 4) else "red_wool")
    for x in (-3, 0, 3):
        hang(C, x, 5, 50, LANT_H, reach=3)


def plaza(C):
    """The plaza (hub): the steam calliope wagon on the west side, the waystone on the east, a maypole of string
    lights in the middle with eight lamp posts round the rim, benches."""
    cx, cz = HUB
    calliope(C)
    # maypole
    C.set(cx, 1, cz, IRON)
    for y in range(2, 13):
        C.set(cx, y, cz, f"{W}dark_iron_plating_wall" if y % 4 else BRASS)
    C.set(cx, 13, cz, GILD)
    C.set(cx, 14, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    C.busy.add((cx, cz))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        px, pz = cx + int(round(math.cos(a) * 14)), cz + int(round(math.sin(a) * 14))
        if in_busy(C, px, pz, 1):
            continue
        lamp_post(C, px, 1, pz, 6)
        C.busy.add((px, pz))
        string_lights(C, (cx, 12, cz), (px, 7, pz), every=3)
    # benches facing the maypole
    for k in range(4):
        a = k * math.pi / 2
        bx, bz = cx + int(round(math.cos(a) * 9)), cz + int(round(math.sin(a) * 9))
        f = face_of(-(bx - cx), -(bz - cz))
        f = face_of(bx - cx, bz - cz)
        if (bx, bz) in ((cx, cz + 9), (cx - 9, cz)):
            continue
        px, pz = perp(f)
        for o in (-1, 0, 1):
            fp(C, bx + px * o, 1, bz + pz * o, stair(DO_ST, f))
    waystone(C, cx + 7, 1, cz + 5)


def calliope(C):
    """The steam calliope organ wagon: a red-and-gold wagon on four wheels, a copper boiler and firebox at the back,
    a rank of brass and copper pipes rising in steps, a keyboard and a stool, a gauge and a whistle; smoke rises from
    the firebox."""
    x0, z0, x1, z1 = -13, 3, -9, 13
    reserve(C, x0 - 1, z0 - 1, x1 + 1, z1 + 1)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 1, z, "red_terracotta" if x in (x0, x1) or z in (z0, z1) else DO)
            C.set(x, 2, z, slab(DO_SL) if (x in (x0, x1) and z % 2 == 0) else AIR) if x in (x0, x1) else None
    for (x, z) in ((x0 - 1, z0 + 1), (x0 - 1, z1 - 1), (x1 + 1, z0 + 1), (x1 + 1, z1 - 1)):
        C.set(x, 1, z, "red_terracotta")
        C.set(x, 0, z, "polished_andesite")
    # the boiler at the south end, a firebox under it
    for z in range(z1 - 3, z1 + 1):
        for x in range(x0 + 1, x1):
            for y in (2, 3, 4):
                if (x - (x0 + 2)) ** 2 + (y - 3) ** 2 <= 2:
                    C.set(x, y, z, COPPER if z != z1 - 2 else BRASS)
    C.set(x0 + 2, 2, z1, "blast_furnace[facing=south,lit=true]")
    C.set(x0 + 2, 5, z1 - 2, f"{W}copper_pipe[axis=y]")
    C.set(x0 + 2, 6, z1 - 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    C.set(x0 + 2, 5, z1 - 1, GAUGE)
    # the rank of pipes, stepping up toward the north
    for i, z in enumerate(range(z0 + 1, z1 - 4)):
        h = 3 + (i % 4) + i // 2
        for x in (x0 + 1, x0 + 3):
            for y in range(2, 2 + h):
                C.set(x, y, z, BRASS if (x == x0 + 1) == (i % 2 == 0) else f"{W}copper_pipe[axis=y]")
            C.set(x, 2 + h, z, GILD)
        C.set(x0 + 2, 2, z, IRON)
        C.set(x0 + 2, 3, z, f"{W}copper_pipe[axis=y]" if i % 2 else BRASS)
    # keyboard and stool on the east side, facing the plaza
    for z in range(z0 + 2, z0 + 6):
        C.set(x1, 2, z, "quartz_slab[type=bottom,waterlogged=false]" if z % 2 else "polished_blackstone_slab[type=bottom,waterlogged=false]")
    C.set(x1 + 1, 1, z0 + 3, f"{W}mahogany_chair[facing=west]")
    C.set(x1 + 1, 0, z0 + 3, "polished_andesite")
    chest(C, x1, 2, z0 + 7, "east", "fair_hub")
    C.set(x0 + 2, 2, z0, "note_block[instrument=flute,note=12,powered=false]")
    C.set(x0 + 2, 3, z0, LANT)
    for z in (z0, z1):
        for x in (x0, x1):
            C.set(x, 2, z, BP_FENCE)
            C.set(x, 3, z, LANT)


# ------------------------------------------------------------------ the big top
def roof_y(r):
    return 17.0 + 22.0 * max(0.0, 1.0 - r / 34.6) ** 1.25


def tier_of(r):
    """Seating tier k (0..5) at radius r, and whether the cell is the bench row (front) of the tier."""
    if r < 19.0 or r >= 31.0:
        return None, False
    k = int((r - 19.0) // 2)
    return k, (r - 19.0 - 2 * k) < 1.0


def big_top(C):
    """The big top: a 68-wide red-and-white striped tent (a 17-high wall, a concave roof rising to a cupola at 39,
    four king poles piercing it with pennants), a scalloped valance; inside, the circus ring (36 wide), six tiers of
    benches with east and west aisles, the gallery round the top, the performers' gate (north) and the front
    tunnel (south), chandeliers, trapezes and footlights."""
    reserve(C, TX - 37, TZ - 37, TX + 37, TZ + 37)
    R = TR
    top = {}
    for x in range(TX - R - 2, TX + R + 3):
        for z in range(TZ - R - 2, TZ + R + 3):
            r = tent_r(x, z)
            if r < R + 0.5:
                top[(x, z)] = int(round(roof_y(r)))
    for (x, z), h in top.items():
        r = tent_r(x, z)
        a = math.atan2(z - TZ, x - TX)
        gore = int((a + math.pi) / (2 * math.pi) * 24) % 2
        wool = RED if gore else WHITE
        nb = [top.get((x + dx, z + dz), 16) for dx, dz in N4]
        lo = min([h] + nb)
        for y in range(min(lo, h), h + 1):
            C.set(x, y, z, YEL if r < 4.5 else wool)
        # floor and furniture by ring
        if r < RING - 0.5:
            C.set(x, 0, z, "smooth_sandstone" if (int(r) % 4 == 0) else ("sand" if hash01(x, z, 131) < 0.6
                                                                          else "sandstone"))
            floor_top = 0
        elif r < 19.0:
            k = int((a + math.pi) / (2 * math.pi) * 48)
            C.set(x, 0, z, "red_concrete" if k % 2 else "white_concrete")
            floor_top = 0
        elif r < 31.0:
            k, front = tier_of(r)
            T = 2 * k + 2
            for y in range(0, T - 1):
                C.set(x, y, z, "dirt")
            C.set(x, T - 1, z, SP if not front else ("red_terracotta" if k % 2 else "white_terracotta"))
            C.set(x, T, z, BPL if not front else ("red_terracotta" if k % 2 else "white_terracotta"))
            if front:
                f = face_of(x - TX, z - TZ)
                C.set(x, T + 1, z, stair(DO_ST, f))
                floor_top = T + 1
            else:
                floor_top = T
        elif r < R - 0.5:
            for y in range(0, 11):
                C.set(x, y, z, "dirt")
            C.set(x, 11, z, SP)
            C.set(x, 12, z, BPL if hash01(x, z, 132) < 0.8 else SP)
            floor_top = 12
        else:
            # the wall
            for y in range(0, 17):
                C.set(x, y, z, wool if y > 1 else ("red_terracotta" if gore else "white_terracotta"))
            floor_top = None
        if floor_top is not None:
            for y in range(floor_top + 1, h):
                C.clear(x, y, z)
    # the valance: a yellow band with scallops outside the wall top
    for x in range(TX - R - 2, TX + R + 3):
        for z in range(TZ - R - 2, TZ + R + 3):
            r = tent_r(x, z)
            if R + 0.5 <= r < R + 1.5:
                a = math.atan2(z - TZ, x - TX)
                C.set(x, 17, z, YEL)
                if int((a + math.pi) / (2 * math.pi) * 72) % 3 != 1:
                    C.set(x, 16, z, YEL)
                if int((a + math.pi) / (2 * math.pi) * 36) % 6 == 0:
                    C.set(x, 15, z, GILD)
    # the cupola and its flag
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            d = math.hypot(dx, dz)
            if d > 3.3:
                continue
            for y in range(39, 43):
                if d > 2.3:
                    C.set(TX + dx, y, TZ + dz, GLASSB if y in (40, 41) and (dx + dz) % 2 == 0 else
                          (RED if (dx + dz) % 2 else WHITE))
            C.set(TX + dx, 43, TZ + dz, GILD if d > 2.3 else YEL)
            if d <= 2.3:
                for y in range(int(round(roof_y(d))) + 1, 43):
                    C.set(TX + dx, y, TZ + dz, YEL)
    for y in range(44, 52):
        C.set(TX, y, TZ, f"{W}dark_iron_plating_wall")
    for k in range(4):
        C.set(TX + 1 + k, 51 - k // 2, TZ, RED if k % 2 else YEL)
        C.set(TX + 1 + k, 50 - k // 2, TZ, YEL if k % 2 else RED)
    # king poles at the ring edge, piercing the roof
    for (sx, sz) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        px, pz = TX + sx * 13, TZ + sz * 13
        h = top[(px, pz)]
        for y in range(1, h + 9):
            C.set(px, y, pz, SBLOG if y % 7 else BRASS)
        C.set(px, h + 9, pz, GILD)
        for k in range(3):
            C.set(px, h + 8 - k, pz + sz, RED if k % 2 else YEL)
        C.set(px, 0, pz, IRON)
        # lamps on the pole
        for y in (8, 16):
            for dx, dz in N4:
                if C.free(px + dx, y, pz + dz):
                    C.set(px + dx, y, pz + dz, EDISON) if (dx, dz) == (0, 0) else None
            C.set(px - sx, y, pz, f"{W}wall_cog[facing={'west' if sx > 0 else 'east'}]") if False else None
        C.set(px, 9, pz, EDISON)
        C.set(px, 17, pz, EDISON)
        C.busy.add((px, pz))
    # chandeliers on chains over the ring and the seats
    for k in range(6):
        a = k * math.pi / 3
        cx, cz = TX + int(round(math.cos(a) * 9)), TZ + int(round(math.sin(a) * 9))
        chandelier(C, cx, 19, cz)
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        cx, cz = TX + int(round(math.cos(a) * 25)), TZ + int(round(math.sin(a) * 25))
        hang(C, cx, int(roof_y(25)) - 6, cz, LANT_H, reach=8)
    chandelier(C, TX, 24, TZ, big=True)
    # trapezes between two king poles, a safety net is long gone
    for (sz,) in ((1,), (-1,)):
        z = TZ + sz * 13
        for x in range(TX - 12, TX + 13):
            if x in (TX - 4, TX + 4):
                for y in range(18, 24):
                    C.set(x, y, z, CHAIN)
                C.set(x, 17, z, f"iron_chain[axis=x,waterlogged=false]")
            if TX - 4 <= x <= TX + 4:
                C.set(x, 17, z, f"iron_chain[axis=x,waterlogged=false]")
            C.set(x, 24, z, f"iron_chain[axis=x,waterlogged=false]") if C.free(x, 24, z) else None
    # footlights in the ring curb and a star of lights in the sawdust
    for x in range(TX - 19, TX + 20):
        for z in range(TZ - 19, TZ + 20):
            r = tent_r(x, z)
            if RING - 0.5 <= r < 19.0 and (x * 5 + z * 3) % 7 == 0:
                C.set(x, 0, z, FROG)
    for k in range(8):
        a = k * math.pi / 4
        for rr in (6, 12):
            C.set(TX + int(round(math.cos(a) * rr)), 0, TZ + int(round(math.sin(a) * rr)), FROG)
    aisles(C)
    ring_gates(C)
    room(C, TX - R, 1, TZ - R, TX + R, 38, TZ + R, pred=lambda x, z: tent_r(x, z) < 33.4)


def chandelier(C, x, y, z, big=False):
    """A brass chandelier: a chain from the roof, a gilded boss, four arms with lanterns."""
    top = y + 1
    while top < y + 22 and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return
    for yy in range(y + 1, top):
        C.set(x, yy, z, CHAIN)
    C.set(x, y, z, CHANDELIER if not big else GILD)
    r = 2 if big else 1
    for dx, dz in N4:
        for k in range(1, r + 1):
            C.set(x + dx * k, y, z + dz * k, f"{W}dark_iron_plating_wall" if k < r or not big else BRASS)
        C.set(x + dx * (r + 1), y, z + dz * (r + 1), CHAIN if big else LANT_H) if big else None
        C.set(x + dx * r, y - 1, z + dz * r, LANT_H)
    if big:
        C.set(x, y - 1, z, CHANDELIER)


def aisles(C):
    """East and west aisles: stairs from the ring up to the gallery (3 wide), cut through the tiers."""
    for sgn in (-1, 1):
        for j in range(12):
            x = TX + sgn * (19 + j)
            for z in (TZ - 1, TZ, TZ + 1):
                for y in range(1, j + 1):
                    C.set(x, y, z, SP)
                C.set(x, j + 1, z, stair(SP_ST, "east" if sgn > 0 else "west"))
                for y in range(j + 2, j + 6):
                    C.clear(x, y, z)
        # newel lamps at the aisle foot
        for z in (TZ - 2, TZ + 2):
            x = TX + sgn * 19
            C.set(x, 3, z, BP_FENCE) if C.free(x, 3, z) else None
            C.set(x, 4, z, LANT) if C.free(x, 4, z) else None


def tunnel(C, zs, x0=-1, x1=1, h=4, wall=SP):
    """A boxed tunnel along z through the seating, carved and walled, ceiling at h + 1."""
    for z in zs:
        for x in range(TX + x0 - 1, TX + x1 + 2):
            for y in range(0, h + 2):
                if x in (TX + x0 - 1, TX + x1 + 1) or y == h + 1:
                    C.set(x, y, z, wall if y > 0 else "polished_andesite")
                elif y == 0:
                    C.set(x, 0, z, SP)
                else:
                    C.clear(x, y, z)


def ring_gates(C):
    """South: the front tunnel to the front door (mist at its ring end, the iron door opens only from inside).
    North: the performers' gate behind sealed bars, the backstage room with the ringmaster's strongbox wagon, the
    back door (opens only from inside). The gangway from the brake platform (west) with its mist."""
    # proscenium arches over both tunnel mouths, covering the trench in the tiers
    for sgn in (1, -1):
        zs = range(TZ + sgn * 19, TZ + sgn * 34, sgn)
        tunnel(C, zs)
        zm = TZ + sgn * 19
        for x in range(TX - 3, TX + 4):
            for y in range(1, 9):
                if abs(x - TX) <= 1 and y <= 4:
                    continue
                spec = GILD if (abs(x - TX) == 3 or y == 8) else ("red_wool" if y <= 6 else BRASS)
                C.set(x, y, zm, spec)
        for z in range(TZ + sgn * 20, TZ + sgn * 25, sgn):
            for x in range(TX - 2, TX + 3):
                C.set(x, 5, z, BPL)
                C.set(x, 6, z, SP)
        hang(C, TX, 4, TZ + sgn * 22, LANT_H, reach=2)
        hang(C, TX, 4, TZ + sgn * 28, LANT_H, reach=2)
    # south: mist at the ring end, the front door in the wall
    C.bp.mist(TX - 1, 1, TZ + 19, TX + 1, 4, TZ + 19)
    oneway_door(C, TX, 1, TZ + 34, "north", "red_terracotta")
    for x in (TX - 1, TX + 1):
        for y in (1, 2, 3, 4):
            C.set(x, y, TZ + 34, "red_terracotta" if y < 3 else RED)
    # the front marquee outside
    for x in range(TX - 5, TX + 6):
        for z in range(TZ + 35, TZ + 40):
            C.set(x, 0, z, "polished_andesite" if abs(x) < 3 else C.get(x, 0, z))
            edge = abs(x - TX) == 5
            if edge and z in (TZ + 36, TZ + 39):
                for y in range(1, 6):
                    C.set(x, y, z, BRASS if y in (1, 5) else f"{W}dark_iron_plating_wall")
            C.set(x, 6, z, RED if (x + z) % 2 else YEL)
        C.set(x, 7, TZ + 39, GILD)
        C.set(x, 8, TZ + 39, GILD if abs(x) in (0, 5) else "red_wool")
    for x in (TX - 4, TX + 4):
        hang(C, x, 5, TZ + 37, LANT_H, reach=2)
    # north: sealed bars at the ring end, the backstage room
    for x in range(TX - 1, TX + 2):
        for y in range(1, 5):
            C.set(x, y, TZ - 19, MOD["vault_bars"])
    backstage(C)
    # west: the gangway from the brake platform through the wall (mist in the wall opening); the valance never
    # hangs into it
    for z in range(TZ - 1, TZ + 2):
        for x in range(TX - 36, TX - 32):
            for y in range(BRAKE_Y + 1, BRAKE_Y + 4):
                C.clear(x, y, z)
        C.set(TX - 34, BRAKE_Y, z, SP)
    C.bp.mist(TX - 34, BRAKE_Y + 1, TZ - 1, TX - 34, BRAKE_Y + 3, TZ + 1)
    for z in (TZ - 2, TZ + 2):
        for y in range(BRAKE_Y + 1, BRAKE_Y + 5):
            C.set(TX - 34, y, z, GILD)


def backstage(C):
    """The ringmaster's backstage under the north seats: costume racks, a lion cage, a make-up table, the
    strongbox wagon (iron-bound chests, a gilded strongbox, barrels), the back door to the outside."""
    x0, x1, z0, z1 = TX - 6, TX + 6, TZ - 31, TZ - 24
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(0, 6):
                if y == 0:
                    C.set(x, 0, z, PARQ if not edge else "polished_andesite")
                elif y == 5 or edge:
                    if edge and z == z1 + 1 and abs(x - TX) <= 1 and y <= 4:
                        continue
                    C.set(x, y, z, DO if y == 5 else ("red_wool" if (x + y) % 3 else SP))
                else:
                    C.clear(x, y, z)
    # beams
    for x in range(x0, x1 + 1, 3):
        for z in range(z0, z1 + 1):
            C.set(x, 5, z, DLOGZ)
    # the back door: a short passage to the tent wall
    for z in range(TZ - 33, z0):
        for x in range(TX - 1, TX + 2):
            for y in range(0, 5):
                if x == TX and 1 <= y <= 3:
                    C.clear(x, y, z)
                elif y == 0:
                    C.set(x, 0, z, SP)
                else:
                    C.set(x, y, z, SP)
    oneway_door(C, TX, 1, TZ - 34, "south", "red_terracotta")
    # the strongbox wagon (gilded, iron bound) along the north wall
    # (west of the back passage, which enters at the centre of the north wall)
    wx0, wz = TX - 6, z0
    for x in range(wx0, wx0 + 5):
        C.set(x, 1, wz, "red_terracotta" if x in (wx0, wx0 + 4) else DO)
        C.set(x, 2, wz, IRON if x in (wx0, wx0 + 4) else GILD)
    chest(C, wx0 + 1, 3, wz, "south", "fair_vault")
    chest(C, wx0 + 3, 3, wz, "south", "fair_vault")
    C.set(wx0 + 2, 3, wz, f"{W}engraved_brass")
    C.set(wx0 + 2, 4, wz, CANDLE_GOLD)
    for x in (wx0, wx0 + 4):
        barrel(C, x, 3, wz)
    # costume racks (armour stands) and a mirror table on the west
    for z in (z0 + 3, z0 + 5):
        C.bp.entity(x0, 1, z, {"id": "minecraft:armor_stand", "Rotation": [270.0, 0.0], "ShowArms": True})
    fp(C, x0, 1, z1, f"{W}mahogany_table")
    fp(C, x0, 2, z1, "candle[candles=3,lit=true,waterlogged=false]")
    for y in (2, 3):
        C.set(x0 - 1, y, z1, GLASS)
    fp(C, x0 + 1, 1, z1, f"{W}mahogany_chair[facing=west]")
    # the lion cage on the east
    for z in range(z0 + 1, z0 + 5):
        for x in (x1 - 2, x1):
            C.set(x, 1, z, "iron_bars")
            C.set(x, 2, z, "iron_bars")
        C.set(x1 - 1, 3, z, IRON)
        C.set(x1, 3, z, IRON)
        C.set(x1 - 2, 3, z, IRON)
    for x in (x1 - 2, x1 - 1, x1):
        C.set(x, 1, z0 + 5, "iron_bars")
        C.set(x, 2, z0 + 5, "iron_bars")
    C.set(x1 - 1, 1, z0 + 2, "bone_block[axis=x]")
    C.set(x1 - 1, 1, z0 + 3, "hay_block[axis=y]")
    hang(C, TX - 3, 4, TZ - 27, LANT_H, reach=1)
    hang(C, TX + 3, 4, TZ - 27, LANT_H, reach=1)
    room(C, x0, 1, z0, x1, 4, z1)


CANDLE_GOLD = "yellow_candle[candles=4,lit=true,waterlogged=false]"


# ------------------------------------------------------------------ the brake platform (site of grace) and summit
def brake_platform(C):
    """West of the big top at the gallery's height: a plank deck on trestles east of the rail, the brake house with
    its lever bank, the waystone, and the canvas gangway (8 long, 3 wide, 4 high) across to the tent wall."""
    x0, x1, z0, z1 = -47, -43, TZ - 5, TZ + 5
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, BRAKE_Y, z, TREAD if x == x1 else SP)
            for y in range(BRAKE_Y + 1, BRAKE_Y + 5):
                C.clear(x, y, z)
            if x in (x0, x1) and (z - z0) % 5 == 0:
                for y in range(1, BRAKE_Y):
                    C.set(x, y, z, SBLOG)
                C.set(x, 0, z, "polished_andesite")
    for y in range(4, BRAKE_Y, 4):
        for z in range(z0, z1 + 1, 5):
            for x in range(x0 + 1, x1):
                C.put(x, y, z, SBLOGX)
    for z in range(z0 - 2, z1 + 3):
        C.norail.add((-48, z))
    for x in range(x0, x1 + 1):
        railing(C, x, BRAKE_Y + 1, z0 - 1, "north")
        railing(C, x, BRAKE_Y + 1, z1 + 1, "south")
    for z in range(z0, z1 + 1):
        if abs(z - TZ) > 1:
            railing(C, x1 + 1, BRAKE_Y + 1, z, "east")
    # the gangway (a canvas tunnel) east to the tent wall
    for x in range(x1 + 1, TX - 34):
        for z in range(TZ - 2, TZ + 3):
            C.set(x, BRAKE_Y, z, SP if abs(z - TZ) <= 1 else SBLOG)
            for y in range(BRAKE_Y + 1, BRAKE_Y + 5):
                if abs(z - TZ) == 2:
                    C.set(x, y, z, RED if (x + y) % 2 else WHITE)
                elif y == BRAKE_Y + 4:
                    C.set(x, y, z, RED if x % 2 else WHITE)
                else:
                    C.clear(x, y, z)
            C.set(x, BRAKE_Y + 5, z, YEL if abs(z - TZ) < 2 else stair(W + "brass_plating_stairs",
                                                                      "south" if z < TZ else "north"))
    for z in (TZ - 2, TZ + 2):
        for y in range(1, BRAKE_Y):
            C.set(x1 + 2, y, z, SBLOG)
        C.set(x1 + 2, 0, z, "polished_andesite")
    hang(C, x1 + 3, BRAKE_Y + 3, TZ, LANT_H, reach=1)
    hang(C, x1 + 6, BRAKE_Y + 3, TZ, LANT_H, reach=1)
    # the brake house at the north end
    hx0, hx1, hz0, hz1 = x0, x1 - 1, z0, z0 + 3
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            edge = x in (hx0, hx1) or z in (hz0, hz1)
            for y in range(BRAKE_Y + 1, BRAKE_Y + 5):
                door = z == hz1 and x in (hx0 + 1, hx0 + 2) and y <= BRAKE_Y + 3
                if edge and not door:
                    C.set(x, y, z, (BPL if (x + z) % 3 else BLOG) if y < BRAKE_Y + 4 else GILD)
                    if y == BRAKE_Y + 2 and x == hx0 and z in (hz0 + 1, hz0 + 2):
                        C.set(x, y, z, GLASS)
            C.set(x, BRAKE_Y + 5, z, RED if (x + z) % 2 else WHITE)
    lever_on(C, hx0 + 2, BRAKE_Y + 2, hz0 + 1, "south")
    lever_on(C, hx0 + 1, BRAKE_Y + 2, hz0 + 1, "south")
    fp(C, hx1 - 1, BRAKE_Y + 1, hz0 + 1, GAUGE)
    chest(C, hx0 + 1, BRAKE_Y + 1, hz0 + 1, "south", "fair_grace")
    hang(C, hx0 + 2, BRAKE_Y + 3, hz0 + 2, LANT_H, reach=1)
    waystone(C, x0 + 2, BRAKE_Y + 1, TZ + 3)
    lamp_post(C, x0, BRAKE_Y + 1, z1, 2)
    lamp_post(C, x1, BRAKE_Y + 1, z1, 2)
    room(C, x0, BRAKE_Y + 1, z0, x1, BRAKE_Y + 3, z1)
    room(C, x1 + 1, BRAKE_Y + 1, TZ - 1, TX - 35, BRAKE_Y + 3, TZ + 1)


def summit(C):
    """The summit platform round the top of the lift hill: plank decks either side of the rail, the winch house
    (lift motor, levers, the summit chest), railings and lamps; a bridge east to the helter-skelter; stairs west up
    to the high catwalk from the wheel."""
    y = PLAT_Y
    zs = range(-20, -3)
    for z in zs:
        for x in list(range(-37, -30)) + list(range(-25, -20)):
            C.set(x, y, z, SP if (x + z) % 5 else DO)
            for yy in range(y + 1, y + 5):
                C.clear(x, yy, z)
            C.busy.add((x, z))
        for x in (-30, -26):
            C.norail.add((x, z))
    for z in zs:
        if z not in (-13, -12, -11):
            railing(C, -21, y + 1, z, "east")
        if z not in (-20, -19, -18):
            railing(C, -37, y + 1, z, "west")
    for x in list(range(-37, -30)) + list(range(-25, -20)):
        railing(C, x, y + 1, -21, "north") if C.free(x, y + 1, -21) else None
        railing(C, x, y + 1, -3, "south") if C.free(x, y + 1, -3) else None
    # trestle columns under the deck
    for z in range(-20, -3, 4):
        for x in (-37, -33, -23, -21):
            if (x, z) in C.paths:
                continue
            for yy in range(1, y):
                C.set(x, yy, z, SBLOG)
            C.set(x, 0, z, "polished_andesite")
            for yy in range(6, y, 6):
                for xx in range(x - 1, x + 2):
                    C.put(xx, yy, z, SBLOGX)
    # the winch house on the west deck
    for x in range(-37, -32):
        for z in range(-9, -4):
            edge = x in (-37, -33) or z in (-9, -5)
            for yy in range(y + 1, y + 5):
                if edge and not (x == -33 and z in (-7, -6) and yy < y + 4):
                    C.set(x, yy, z, BPL if yy < y + 4 else GILD)
            C.set(x, y + 5, z, RED if (x + z) % 2 else WHITE)
    for z in (-8, -7):
        fp(C, -36, y + 1, z, COPPER)
        fp(C, -36, y + 2, z, GEAR)
    fp(C, -35, y + 1, -6, f"{W}mahogany_chair[facing=east]")
    lever_on(C, -35, y + 2, -8, "south")
    chest(C, -34, y + 1, -8, "west", "fair_coaster")
    hang(C, -35, y + 3, -7, LANT_H, reach=1)
    room(C, -36, y + 1, -8, -34, y + 3, -6)
    # lamps
    for (x, z) in ((-25, -19), (-25, -4), (-21, -4)):
        lamp_post(C, x, y + 1, z, 2)
    spawner(C, -23, y + 1, -16, MOB_DRONE)
    # the bridge to the helter-skelter
    for z in (-13, -12, -11):
        C.set(-20, y, z, TREAD)
        for yy in range(y + 1, y + 4):
            C.clear(-20, yy, z)
    railing(C, -20, y + 1, -14, "north")
    railing(C, -20, y + 1, -10, "south")


# ------------------------------------------------------------------ helter-skelter
def helter_skelter(C):
    """A striped tower beside the summit: a top room with a drop hole (the slide's chute) falling into a deep pool
    at the foot, a door out to the plaza; a decorative spiral slide wound round the outside."""
    cx, cz = HS
    reserve(C, cx - 6, cz - 6, cx + 6, cz + 6)
    y_top = PLAT_Y
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d = math.hypot(dx, dz)
            if d > 4.4:
                continue
            x, z = cx + dx, cz + dz
            wall = d > 3.4
            for y in range(-4, y_top + 5):
                if wall:
                    if y < 0:
                        C.set(x, y, z, "stone_bricks")
                        continue
                    band = (y // 3) % 2
                    spec = RED if band else WHITE
                    if y == y_top or y == 0:
                        spec = GILD
                    if y_top < y <= y_top + 3 and (dx == 0 or dz == 0):
                        spec = GLASS if y > y_top + 1 else spec
                    C.set(x, y, z, spec)
                else:
                    pool = max(abs(dx), abs(dz)) <= 1
                    if y < -3:
                        C.set(x, y, z, "stone_bricks")
                    elif y <= 0:
                        if pool:
                            C.water(x, y, z)
                        else:
                            C.set(x, y, z, "stone_bricks" if y < 0 else BTILE)
                    elif y == y_top:
                        if not pool:
                            C.set(x, y, z, SP)
                        else:
                            C.clear(x, y, z)
                    else:
                        C.clear(x, y, z)
            # cone roof
    for k in range(7):
        r = 5 - k * 0.7
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = math.hypot(dx, dz)
                if r - 1.0 < d <= r:
                    a = math.atan2(dz, dx)
                    C.set(cx + dx, y_top + 5 + k, cz + dz, RED if int((a + math.pi) / (2 * math.pi) * 8) % 2 else YEL)
    C.set(cx, y_top + 12, cz, GILD)
    C.set(cx, y_top + 13, cz, f"{W}dark_iron_plating_wall")
    C.set(cx, y_top + 14, cz, "red_banner[rotation=8]")
    # entrance from the summit bridge (west), door at the foot (south)
    for z in (cz - 1, cz, cz + 1):
        for y in range(y_top + 1, y_top + 4):
            C.clear(cx - 4, y, z)
            C.clear(cx - 3, y, z)
        C.set(cx - 4, y_top, z, TREAD)
        C.set(cx - 3, y_top, z, TREAD)
    # a ring of railing round the drop hole, open toward the bridge
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and dx != -2:
                railing(C, cx + dx, y_top + 1, cz + dz, face_of(-dx, -dz)) if False else None
    for y in (1, 2):
        C.clear(cx, y, cz + 4)
        C.clear(cx, y, cz + 3)
    C.bp.door(cx, 1, cz + 4, "south", wood="birch")
    C.set(cx, 0, cz + 3, BTILE)
    # steps out of the pool
    C.set(cx - 2, 0, cz + 1, BTILE)
    C.set(cx, 0, cz + 2, BTILE)
    hang(C, cx + 2, y_top + 3, cz + 2, LANT_H, reach=2)
    hang(C, cx - 2, 4, cz - 2, LANT_H, reach=30) if False else None
    for (dx, dz) in ((2, 2), (-2, -2), (2, -2), (-2, 2)):
        C.set(cx + dx, 6, cz + dz, EDISON) if False else None
    # lamps on the inner wall over the pool (set into the wall)
    for y in (3, 10, 18, 26):
        for (dx, dz) in ((4, 0), (-4, 0), (0, -4)):
            C.set(cx + dx, y, cz + dz, EDISON)
    room(C, cx - 3, 1, cz - 3, cx + 3, 4, cz + 3, pred=lambda x, z: math.hypot(x - cx, z - cz) < 3.4)
    room(C, cx - 3, y_top + 1, cz - 3, cx + 3, y_top + 3, cz + 3, pred=lambda x, z: math.hypot(x - cx, z - cz) < 3.4)
    # the decorative spiral slide outside
    for i in range(0, 4 * 36):
        a = i * 2 * math.pi / 36
        y = y_top - 1 - i * (y_top - 3) / (4 * 36.0)
        x = cx + int(round(math.cos(a) * 5.4))
        z = cz + int(round(math.sin(a) * 5.4))
        yy = int(y)
        if (x, z) in C.paths or (abs(x - cx) <= 1 and z > cz):
            continue
        if C.free(x, yy, z):
            C.set(x, yy, z, "smooth_quartz_slab[type=bottom,waterlogged=false]" if i % 6 else YEL)


# ------------------------------------------------------------------ the ferris wheel
def wheel(C):
    """The colossal brass ferris wheel: two rims (r 30) braced to an inner ring (r 26), sixteen spokes a side, a
    brass hub on an iron axle through two A-frames, a sprocket on the axle's north end, sixteen gondolas hung
    between the rims, a boarding deck at the foot."""
    reserve(C, WX - 24, FZ0 - 2, WX + 24, FZ1 + 2)
    for z in (WZ0, WZ1):
        for x in range(WX - WR - 1, WX + WR + 2):
            for y in range(WY - WR - 1, WY + WR + 2):
                d = math.hypot(x - WX, y - WY)
                if abs(d - WR) < 0.55:
                    C.set(x, y, z, IRON if int(math.degrees(math.atan2(y - WY, x - WX)) // 15) % 2 else BRASS)
                elif abs(d - 26) < 0.5:
                    C.set(x, y, z, IRON)
                elif d < 4.5:
                    C.set(x, y, z, GEAR if d < 2.5 else BRASS)
        # spokes and the zigzag truss between the rings
        for k in range(16):
            a = k * math.pi / 8
            line3(C, (int(round(WX + 4 * math.cos(a))), int(round(WY + 4 * math.sin(a))), z),
                  (int(round(WX + 26 * math.cos(a))), int(round(WY + 26 * math.sin(a))), z),
                  BRASS if k % 2 else IRON)
            a2 = a + math.pi / 16
            line3(C, (int(round(WX + 26 * math.cos(a))), int(round(WY + 26 * math.sin(a))), z),
                  (int(round(WX + 30 * math.cos(a2))), int(round(WY + 30 * math.sin(a2))), z), IRON)
            a3 = a + math.pi / 8
            line3(C, (int(round(WX + 30 * math.cos(a2))), int(round(WY + 30 * math.sin(a2))), z),
                  (int(round(WX + 26 * math.cos(a3))), int(round(WY + 26 * math.sin(a3))), z), IRON)
        # edison lamps round the rim face
        for k in range(32):
            a = k * math.pi / 16 + math.pi / 32
            x, y = int(round(WX + (WR + 0) * math.cos(a))), int(round(WY + (WR + 0) * math.sin(a)))
            C.set(x, y, z + (-1 if z == WZ0 else 1), EDISON) if C.free(x, y, z + (-1 if z == WZ0 else 1)) else None
    # the axle through both frames, gilded caps, the hub drum between the rims
    for z in range(FZ0, FZ1 + 1):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if abs(dx) + abs(dy) <= 1 or WZ0 < z < WZ1:
                    C.set(WX + dx, WY + dy, z, GILD if z in (FZ0, FZ1) and dx == dy == 0 else IRON)
    for z in range(WZ0 + 1, WZ1):
        for x in range(WX - 3, WX + 4):
            for y in range(WY - 3, WY + 4):
                if math.hypot(x - WX, y - WY) < 3.3:
                    C.set(x, y, z, BRASS if (x + y) % 2 else COPPER)
    # sprocket on the north end
    for x in range(WX - 4, WX + 5):
        for y in range(WY - 4, WY + 5):
            d = math.hypot(x - WX, y - WY)
            if d < 4.4 and (d > 3.4 or d < 1.5):
                C.set(x, y, FZ0 - 1, GEAR if d > 3.4 and (x + y) % 2 else IRON)
    # A-frames
    for z in (FZ0, FZ1):
        for sx in (-1, 1):
            foot = (WX + sx * 22, 0, z)
            line3(C, (WX + sx, WY - 1, z), foot, lambda p: IRON if p[1] % 8 else BRASS)
            line3(C, (WX + sx * 2, WY - 1, z), (foot[0] + sx, 0, z), lambda p: DIB if p[1] % 8 else BRASS)
            C.set(foot[0], 0, z, "polished_andesite")
            C.set(foot[0] + sx, 0, z, "polished_andesite")
            for k in range(1, 3):
                C.busy.add((foot[0] + sx * k, z))
        for yy in (12, 24):
            half = int(round(22 * (WY - yy) / float(WY)))
            for x in range(WX - half + 1, WX + half):
                C.set(x, yy, z, IRON if x % 4 else BRASS)
        # X braces in the lower bay
        line3(C, (WX - 15, 12, z), (WX - 8, 24, z), IRON)
        line3(C, (WX + 15, 12, z), (WX + 8, 24, z), IRON)
    # gondolas
    cols = ((COPPER, "copper_plating_stairs"), (VERD, "verdigris_plating_stairs"), (BRASS, "brass_plating_stairs"),
            ("red_terracotta", "red_nether_brick_stairs"))
    zc = (WZ0 + WZ1) // 2
    for k in range(16):
        a = k * math.pi / 8
        ax, ay = int(round(WX + WR * math.cos(a))), int(round(WY + WR * math.sin(a)))
        body, st = cols[k % 4]
        st = W + st if "plating" in st else st
        for z in range(WZ0 + 1, WZ1):
            C.set(ax, ay, z, IRON)
        C.set(ax, ay - 1, zc, CHAIN)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                x, z = ax + dx, zc + dz
                C.set(x, ay - 2, z, body if (dx == 0 or dz == 0) and not (dx == 0 and dz == 0) else
                      (GILD if dx == 0 and dz == 0 else st and stair(st, face_of(-dx, 0) if dx else
                                                                      face_of(0, -dz))))
                if abs(dx) == 1 and abs(dz) == 1:
                    C.set(x, ay - 3, z, BP_FENCE)
                    C.set(x, ay - 4, z, BP_FENCE)
                elif not (dx == 0 and dz == 0):
                    C.clear(x, ay - 3, z) if C.free(x, ay - 3, z) else None
                C.set(x, ay - 5, z, body if abs(dx) + abs(dz) == 2 else DO)
        C.set(ax - 1, ay - 4, zc, stair(DO_ST, "west"))
        C.set(ax + 1, ay - 4, zc, stair(DO_ST, "east"))
        C.set(ax, ay - 3, zc, LANT_H) if k % 2 == 0 else None
    # the boarding deck at the foot
    for x in range(WX - 6, WX + 7):
        for z in range(WZ0 - 1, WZ1 + 2):
            if C.free(x, 1, z) or C.get(x, 1, z) is None:
                C.set(x, 1, z, slab(SP_SL) if abs(x - WX) == 6 or z in (WZ0 - 1, WZ1 + 1) else SP)
    for x in (WX - 6, WX + 6):
        lamp_post(C, x, 2, WZ0 - 1, 3)
        lamp_post(C, x, 2, WZ1 + 1, 3)
    C.set(WX + 3, 2, WZ1 + 1, f"{W}mahogany_chair[facing=south]") if False else None


def wheel_service(C):
    """The maintenance ladder tower (landings every 12), the axle platform, the bubble-column lift beside it, the
    high catwalk east to the coaster summit, the drive chain from the engine house up to the sprocket."""
    lx, lz = LADDER
    reserve(C, lx - 3, lz - 7, lx + 4, lz + 1)
    for y in range(0, AXLE_DECK):
        C.set(lx, y, lz + 1, IRON if y % 6 else BRASS)
        C.set(lx, y, lz, f"ladder[facing=north,waterlogged=false]") if y >= 1 else None
    C.set(lx, AXLE_DECK, lz, "ladder[facing=north,waterlogged=false]")
    # lattice corner posts round the ladder cage
    for (dx, dz) in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        for y in range(1, AXLE_DECK):
            if dz < 0 and y % 12 in (11, 0, 1):
                pass
            C.set(lx + dx, y, lz + dz if dz > 0 else lz - 1, IRON if y % 4 else BRASS) if dz > 0 else None
    for y in range(4, AXLE_DECK, 4):
        C.set(lx - 1, y, lz + 1, IRON)
        C.set(lx + 1, y, lz + 1, IRON)
    # landings at 12 and 24
    for ly in (11, 23):
        for x in range(lx - 2, lx + 3):
            for z in range(lz - 3, lz):
                C.set(x, ly, z, TREAD)
                for y in range(ly + 1, ly + 4):
                    C.clear(x, y, z)
        for x in range(lx - 2, lx + 3):
            railing(C, x, ly + 1, lz - 4, "north")
        for z in range(lz - 3, lz):
            railing(C, lx - 3, ly + 1, z, "west")
            railing(C, lx + 3, ly + 1, z, "east")
        for (dx, dz) in ((-2, -3), (2, -3)):
            for y in range(1, ly):
                C.set(lx + dx, y, lz + dz, IRON)
        hang(C, lx, ly + 3, lz - 2, LANT_H, reach=1) if False else None
        lamp_post(C, lx + 2, ly + 1, lz - 1, 2)
    # the axle platform (deck 36) north of the north frame
    px0, px1, pz0, pz1 = WX - 3, WX + 4, FZ0 - 8, FZ0 - 2
    for x in range(px0, px1 + 1):
        for z in range(pz0, pz1 + 1):
            if (x, z) == (lx, lz):
                continue
            C.set(x, AXLE_DECK, z, TREAD if (x + z) % 2 else IRON)
            for y in range(AXLE_DECK + 1, AXLE_DECK + 5):
                if C.free(x, y, z) or True:
                    C.clear(x, y, z)
    for x in range(px0, px1 + 1):
        railing(C, x, AXLE_DECK + 1, pz1 + 1, "south") if C.free(x, AXLE_DECK + 1, pz1 + 1) else None
    for z in range(pz0, pz1 + 1):
        if z not in (pz0, pz0 + 1, pz0 + 2):
            railing(C, px1 + 1, AXLE_DECK + 1, z, "east")
        railing(C, px0 - 1, AXLE_DECK + 1, z, "west")
    for x in range(px0, px1 + 1):
        if x != LIFT[0]:
            railing(C, x, AXLE_DECK + 1, pz0 - 1, "north")
    for (x, z) in ((px0, pz1), (px1, pz1)):
        C.set(x, AXLE_DECK + 1, z, f"{W}dark_iron_plating_wall")
        C.set(x, AXLE_DECK + 2, z, LANT)
    chest(C, px0, AXLE_DECK + 1, pz0 + 3, "east", "fair_wheel")
    fp(C, px0, AXLE_DECK + 1, pz0 + 4, f"{W}valve_wheel[facing=east]") if False else None
    fp(C, px0, AXLE_DECK + 1, pz0 + 5, COPPER)
    fp(C, px0, AXLE_DECK + 2, pz0 + 5, GAUGE)
    spawner(C, px1, AXLE_DECK + 1, pz0 + 4, MOB_DRONE)
    # platform legs
    for (x, z) in ((px0, pz0), (px1, pz0), (px1, pz1)):
        for y in range(1, AXLE_DECK):
            C.set(x, y, z, IRON if y % 6 else BRASS)
    # the bubble-column lift north of the platform
    cx, cz = LIFT
    C.set(cx, -1, cz, "soul_sand")
    C.set(cx, 0, cz, "bubble_column[drag=false]")
    for y in range(1, AXLE_DECK + 1):
        C.water(cx, y, cz, "bubble_column[drag=false]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx or dz:
                    if y == AXLE_DECK:
                        C.set(cx + dx, y, cz + dz, BRASS)
                    elif dx and dz:
                        C.set(cx + dx, y, cz + dz, BRASS if y % 6 else EDISON)
                    else:
                        C.set(cx + dx, y, cz + dz, GLASSB if y % 6 else BRASS)
    C.set(cx, 0, cz - 1, BRASS)
    for y in (1, 2):
        C.set(cx, y, cz - 1, f"spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
    C.set(cx, 3, cz - 1, BRASS)
    # the top: open to the platform (south)
    for y in (AXLE_DECK + 1, AXLE_DECK + 2):
        C.clear(cx, y, cz + 1)
        for dx in (-1, 1):
            C.set(cx + dx, y, cz + 1, BRASS)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if (dx, dz) != (0, 1):
                C.set(cx + dx, AXLE_DECK + 3, cz + dz, BRASS if (dx, dz) != (0, 0) else EDISON)
                if (dx, dz) != (0, 0):
                    C.set(cx + dx, AXLE_DECK + 1, cz + dz, GLASSB) if dz != 1 else None
                    C.set(cx + dx, AXLE_DECK + 2, cz + dz, GLASSB) if dz != 1 else None
    C.clear(cx, AXLE_DECK + 1, cz)
    C.clear(cx, AXLE_DECK + 2, cz)
    C.set(cx, AXLE_DECK + 3, cz, BRASS)
    # the high catwalk east to the summit stairs
    cz0, cz1 = pz0, pz0 + 2
    for x in range(px1 + 1, -41):
        for z in range(cz0, cz1 + 1):
            C.set(x, AXLE_DECK, z, TREAD if z == cz0 + 1 else IRON)
            for y in range(AXLE_DECK + 1, AXLE_DECK + 4):
                C.clear(x, y, z)
        railing(C, x, AXLE_DECK + 1, cz0 - 1, "north")
        railing(C, x, AXLE_DECK + 1, cz1 + 1, "south")
        if x % 12 == 0:
            for z in (cz0 - 1, cz1 + 1):
                C.set(x, AXLE_DECK + 1, z, f"{W}dark_iron_plating_wall")
                C.set(x, AXLE_DECK + 2, z, LANT)
    # its lattice tower halfway
    tx = -54
    for (dx, dz) in ((0, cz0), (0, cz1)):
        for y in range(1, AXLE_DECK):
            C.set(tx, y, dz, IRON if y % 5 else BRASS)
            C.set(tx + 1, y, dz, IRON if y % 5 else BRASS)
        C.set(tx, 0, dz, "polished_andesite")
    for y in range(5, AXLE_DECK, 5):
        for z in range(cz0, cz1 + 1):
            C.set(tx, y, z, IRON)
    # stairs down to the summit deck (y 31)
    for i, x in enumerate(range(-41, -37)):
        t = AXLE_DECK - 1 - i
        for z in range(cz0, cz1 + 1):
            C.set(x, t, z, stair(SP_ST, "west"))
            for y in range(t - 1, t - 3, -1):
                C.put(x, y, z, SP) if y > PLAT_Y else None
            for y in range(t + 1, t + 5):
                C.clear(x, y, z)
        railing(C, x, t + 1, cz0 - 1, "north")
        railing(C, x, t + 1, cz1 + 1, "south")
    for x in range(-41, -37):
        for y in range(PLAT_Y + 1, AXLE_DECK - 4):
            pass
    # the drive chain from the engine house's sprocket up to the axle's sprocket
    line3(C, (WX - 4, 13, -31), (WX - 4, WY, FZ0 - 1), "copper_chain[axis=z,waterlogged=false]")
    line3(C, (WX - 4, 9, -31), (WX - 4, WY - 4, FZ0 - 1), "copper_chain[axis=z,waterlogged=false]", keep_free=True)


# ------------------------------------------------------------------ the engine house
def engine_house(C):
    """A brick engine house with a monitor roof and a tall smokestack: the boiler and its firebox, the beam-less
    horizontal engine (cylinder, crosshead, connecting rod), the 11-high flywheel and the drive sprocket whose chain
    leaves through the roof for the wheel; coal bunker, workbench, gauge wall, the engineer's desk."""
    x0, z0, x1, z1 = ENG
    reserve(C, x0, z0, x1, z1)
    H = 11
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, "polished_andesite" if (x + z) % 2 else "andesite" if edge else TREAD if
                  (x - x0) % 6 == 0 else "polished_andesite")
            for y in range(1, H + 1):
                if edge:
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    if u % 6 == 0 or y in (1, H):
                        spec = DIB if y < H else BRASS
                    elif y in (4, 5, 6, 7) and u % 6 in (2, 3, 4):
                        spec = "yellow_stained_glass_pane" if y in (5, 6, 7) else slab("stone_brick_slab", "top")
                    else:
                        spec = BRICK if hash3(x, y, z, 141) < 0.85 else "cracked_stone_bricks"
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
    # roof: low slate pitches along x with a glazed monitor
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            k = min(z - (z0 - 1), (z1 + 1) - z)
            y = H + 1 + min(k, 4)
            if k < 4:
                f = "south" if z < (z0 + z1) / 2 else "north"
                C.set(x, y, z, stair(W + "slate_roof_tile_stairs", f))
            else:
                C.set(x, y, z, W + "slate_roof_tiles" if not (x0 < x < x1) else
                      ("glass" if (x - x0) % 3 else W + "slate_roof_tiles"))
            if x0 <= x <= x1 and z0 < z < z1:
                for yy in range(H + 1, y):
                    C.set(x, yy, z, BRICK if x in (x0, x1) else (AIR if C.free(x, yy, z) else C.get(x, yy, z)))
    for x in range(x0 + 1, x1, 4):
        for z in range(z0 + 1, z1):
            C.set(x, H, z, DLOGZ)
    # doors: east (hub lane), south (lift), north (caravan)
    for z in (-35, -34, -33):
        for y in (1, 2, 3):
            C.clear(x1, y, z)
    for x in (WX - 1, WX, WX + 1):
        for y in (1, 2, 3):
            C.clear(x, y, z1)
    for x in (-75, -74, -73):
        for y in (1, 2, 3):
            C.clear(x, y, z0)
    # the smokestack at the west end
    sx, sz = x0 + 3, z0 + 4
    for y in range(1, 44):
        r = 2.4 if y < 30 else 2.0
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                d = math.hypot(dx, dz)
                if r - 1.0 < d <= r:
                    C.set(sx + dx, y, sz + dz, BRASS if y % 10 == 0 else (SSMK if y > 36 else SMK))
                elif d <= r - 1.0:
                    C.set(sx + dx, y, sz + dz, SMK)
    C.set(sx, 44, sz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # the boiler: a horizontal copper drum along x with a firebox
    by, bz = 4, z0 + 4
    for x in range(x0 + 6, x0 + 15):
        for z in range(bz - 2, bz + 3):
            for y in range(1, 8):
                if (z - bz) ** 2 + (y - by) ** 2 <= 6.5:
                    C.set(x, y, z, BRASS if x in (x0 + 6, x0 + 10, x0 + 14) else COPPER)
                elif y < by:
                    C.set(x, y, z, BRICK)
    for z in (bz - 1, bz + 1):
        C.set(x0 + 5, 1, z, "blast_furnace[facing=east,lit=true]")
    C.set(x0 + 5, 2, bz, GAUGE)
    for x in range(x0 + 7, x0 + 14, 3):
        C.set(x, 8, bz, f"{W}copper_pipe[axis=y]")
        C.set(x, 9, bz, f"{W}copper_pipe[axis=y]")
    for x in range(x0 + 7, x1 - 8):
        C.set(x, 10, bz, f"{W}copper_pipe[axis=x]")
    # the engine: cylinder, crosshead guide, rod, flywheel (in the y-z plane at x = WX - 4)
    fx, fy, fz = WX - 4, 6, -32
    for z in range(fz - 6, fz + 7):
        for y in range(0, 13):
            d = math.hypot(z - fz, y - fy)
            if 4.4 < d < 5.6:
                C.set(fx, y, z, IRON)
            elif d < 1.4:
                C.set(fx, y, z, GILD)
            elif d < 4.5 and (int(math.degrees(math.atan2(y - fy, z - fz))) // 30) % 3 == 0:
                C.set(fx, y, z, DIB)
    for z in range(fz - 6, fz + 7):
        C.set(fx, 0, z, IRON)
    for x in (fx - 1, fx + 1):
        for y in range(1, fy):
            C.set(x, y, fz, DIB)
        C.set(x, fy, fz, IRON)
    C.set(fx - 2, fy, fz, IRON)
    # the drive sprocket next to the flywheel, carrying the chain up through the roof
    for z in range(fz - 2, fz + 3):
        for y in range(fy + 4, fy + 9):
            d = math.hypot(z - (fz + 1), y - (fy + 6))
            if d < 2.4:
                C.set(fx, y, z, GEAR if d > 1.2 else IRON)
    for y in range(H + 1, 18):
        for z in range(-31, -26):
            if C.get(fx, y, z) not in (None, AIR) and "chain" not in (C.get(fx, y, z) or ""):
                pass
    # cylinder and guide on the floor east of the flywheel
    for x in range(fx + 2, fx + 8):
        for y in range(1, 4):
            for z in (fz - 1, fz, fz + 1):
                if x >= fx + 5:
                    if (y - 2) ** 2 + (z - fz) ** 2 <= 2:
                        C.set(x, y, z, BRASS if x in (fx + 5, fx + 7) else COPPER)
                elif y == 1:
                    C.set(x, y, z, IRON if z != fz else TREAD)
        C.set(x, 2, fz, IRON) if x < fx + 5 else None
    C.set(fx + 2, 2, fz, f"{W}copper_pipe[axis=x]")
    C.set(fx + 3, 3, fz, f"{W}copper_pipe[axis=x]")
    # coal bunker, workbench, gauge wall, desk
    for x in range(x0 + 1, x0 + 5):
        for z in range(z1 - 4, z1):
            for y in range(1, 2 + (x - x0) % 3):
                C.set(x, y, z, "coal_block")
    for x in range(x0 + 1, x0 + 6):
        C.set(x, 1, z1 - 5, "stone_brick_wall") if False else None
    for z in range(z0 + 1, z0 + 8, 2):
        C.set(x1 - 1, 3, z, GAUGE)
        C.set(x1 - 1, 2, z + 1, f"{W}valve_wheel[facing=west]")
    fp(C, x1 - 1, 1, z0 + 2, "crafting_table")
    fp(C, x1 - 1, 1, z0 + 3, "smithing_table")
    fp(C, x1 - 1, 1, z0 + 4, "anvil[facing=north]")
    fp(C, x1 - 3, 1, z1 - 2, TABLE)
    fp(C, x1 - 4, 1, z1 - 2, f"{W}mahogany_chair[facing=east]")
    fp(C, x1 - 3, 2, z1 - 2, "lantern[hanging=false,waterlogged=false]")
    chest(C, x1 - 2, 1, z1 - 1, "north", "fair_engine")
    barrel(C, x0 + 1, 1, z0 + 1)
    barrel(C, x0 + 2, 1, z0 + 1)
    spawner(C, x0 + 16, 1, z1 - 3, MOB_AUTO)
    for x in range(x0 + 3, x1 - 1, 5):
        for z in (z0 + 5, z1 - 5):
            hang(C, x, H - 3, z, LANT_H, reach=5)
    room(C, x0 + 1, 1, z0 + 1, x1 - 1, H - 1, z1 - 1)


# ------------------------------------------------------------------ the ringmaster's caravan
def ringmaster(C):
    """The ringmaster's caravan: the grandest wagon (purple and gold), a canopy over a table and chairs, a campfire;
    inside his bed, desk, wardrobe and a mirror. Optional."""
    def fit(x0, z0, x1, z1):
        C.bp.bed(x0, 2, z0, "east", color="purple")
        fp(C, x1, 2, z0, f"{W}mahogany_table")
        fp(C, x1, 3, z0, CANDLE_GOLD)
        chest(C, x1, 2, z1, "west", "fair_caravan")
        fp(C, x0, 2, z1, "chiseled_bookshelf[facing=east,slot_0_occupied=true,slot_1_occupied=false,"
                         "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")

    bx0, bz0, bx1, bz1 = caravan(C, -82, -60, "x", "purple_terracotta", "yellow_terracotta", 7, fit)
    # canopy and table
    for x in range(bx0, bx1 + 1):
        for z in range(bz1 + 2, bz1 + 6):
            C.set(x, 5, z, "purple_wool" if (x + z) % 2 else YEL)
    for (x, z) in ((bx0, bz1 + 5), (bx1, bz1 + 5)):
        for y in range(1, 5):
            C.set(x, y, z, BP_FENCE)
    fp(C, bx0 + 3, 1, bz1 + 3, f"{W}mahogany_table")
    fp(C, bx0 + 2, 1, bz1 + 3, f"{W}mahogany_chair[facing=east]")
    fp(C, bx0 + 4, 1, bz1 + 3, f"{W}mahogany_chair[facing=west]")
    fp(C, bx0 + 3, 2, bz1 + 3, "candle[candles=2,lit=true,waterlogged=false]")
    hang(C, bx0 + 3, 4, bz1 + 4, LANT_H, reach=1)
    C.set(bx1 + 3, 1, bz1 + 3, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    spawner(C, bx1 + 4, 1, bz0 - 2, MOB_MARKS)
    reserve(C, bx0 - 1, bz1 + 1, bx1 + 5, bz1 + 6)


# ------------------------------------------------------------------ the carousel
def carousel(C):
    """The carousel: a round platform (r 11) of parquet and brass, a mirrored centre column holding the band organ,
    three rings of brass automaton horses on copper poles at two heights, eight brass columns, a striped canopy
    with a rounding board of mirrors and edison lamps, a ribbed brass and verdigris dome with a cupola."""
    cx, cz = CAR
    reserve(C, cx - 14, cz - 14, cx + 14, cz + 14)
    for x in range(cx - 14, cx + 15):
        for z in range(cz - 14, cz + 15):
            d = math.hypot(x - cx, z - cz)
            a = math.atan2(z - cz, x - cx)
            if d <= 11.4:
                C.set(x, 1, z, PARQ if int(d) % 3 else BTILE)
                C.set(x, 0, z, "polished_andesite")
                for y in range(2, 9):
                    C.clear(x, y, z)
            elif d <= 12.5:
                C.set(x, 1, z, slab(W + "brass_plating_slab"))
                for y in range(2, 9):
                    C.clear(x, y, z)
            if d <= 13.5:
                # the canopy ceiling and the rounding board
                if d <= 12.5:
                    k = int((a + math.pi) / (2 * math.pi) * 24) % 2
                    C.set(x, 9, z, "red_concrete" if k else "white_concrete")
                else:
                    for y in (7, 8, 9):
                        if y == 8 and int((a + math.pi) / (2 * math.pi) * 40) % 2:
                            C.set(x, y, z, GLASSB)
                        elif y == 8:
                            C.set(x, y, z, EDISON)
                        else:
                            C.set(x, y, z, GILD)
            # the dome
            if d <= 13.9:
                h = 10 + int(round(7.5 * math.sqrt(max(0.0, 1.0 - (d / 14.0) ** 2))))
                rib = int((a + math.pi) / (2 * math.pi) * 16 + 0.5) % 2 == 0 and abs(
                    ((a + math.pi) / (2 * math.pi) * 16) % 1.0 - 0.0) < 0.2
                C.set(x, h, z, BRASS if rib else VERD)
                for y in range(10, h):
                    C.set(x, y, z, (BRASS if rib else VERD) if d > 12.6 else "white_concrete")
    # cupola
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3:
                for y in (18, 19):
                    C.set(cx + dx, y, cz + dz, GLASSB if (y == 18 and abs(dx) + abs(dz) == 3) else BRASS)
    C.set(cx, 20, cz, GILD)
    C.set(cx, 21, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # centre column: mirror panels, the band organ (pipes, drum, cogs)
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            d = math.hypot(x - cx, z - cz)
            if d > 3.3:
                continue
            for y in range(2, 9):
                edge = d > 2.3
                if edge:
                    a = math.atan2(z - cz, x - cx)
                    k = int((a + math.pi) / (2 * math.pi) * 8)
                    if y in (2, 8):
                        spec = GILD
                    elif k % 2 == 0:
                        spec = GLASSB if y in (4, 5, 6) else BRASS
                    else:
                        spec = f"{W}copper_pipe[axis=y]" if y < 7 else GEAR
                    C.set(x, y, z, spec)
                else:
                    C.set(x, y, z, IRON)
    for (dx, dz, f) in ((0, -4, "north"), (0, 4, "south"), (-4, 0, "west"), (4, 0, "east")):
        C.set(cx + dx, 7, cz + dz, f"{W}wall_cog[facing={f}]")
        C.set(cx + dx, 2, cz + dz, "note_block[instrument=bell,note=7,powered=false]")
    # eight brass columns at the platform rim
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = cx + int(round(math.cos(a) * 11)), cz + int(round(math.sin(a) * 11))
        for y in range(2, 9):
            C.set(x, y, z, BRASS if y in (2, 8) else f"{W}dark_iron_plating_wall")
    # horses
    hcols = ((BRASS, W + "brass_plating_stairs"), (COPPER, W + "copper_plating_stairs"),
             ("white_terracotta", "smooth_quartz_stairs"), (VERD, W + "verdigris_plating_stairs"))
    for ring, (rr, nh) in enumerate(((5.5, 8), (8.0, 12), (10.2, 16))):
        for k in range(nh):
            a = (k + 0.5 * ring) * 2 * math.pi / nh
            px, pz = cx + int(round(math.cos(a) * rr)), cz + int(round(math.sin(a) * rr))
            tx, tz = -math.sin(a), math.cos(a)
            t = face_of(tx, tz)
            dx, dz = DV[t]
            body, st = hcols[(k + ring) % 4]
            hy = 3 + (k + ring) % 2
            # pole
            for y in range(2, 9):
                C.set(px, y, pz, CCHAIN)
            C.set(px, hy, pz, body)
            C.set(px + dx, hy, pz + dz, body)
            C.set(px + dx, hy + 1, pz + dz, stair(st, t))
            C.set(px - dx, hy, pz - dz, stair(st, OPP[t], "top"))
            C.set(px + dx, hy - 1, pz + dz, BP_FENCE if hy > 3 else C.get(px + dx, hy - 1, pz + dz) or AIR)
            C.set(px - dx, hy - 1, pz - dz, BP_FENCE if hy > 3 else AIR)
            C.set(px, hy + 1, pz, "red_carpet") if False else None
    # lamps hung from the canopy between the horse rings
    for k in range(8):
        a = k * math.pi / 4
        for rr in (4.0, 9.2):
            x, z = cx + int(round(math.cos(a) * rr)), cz + int(round(math.sin(a) * rr))
            if C.free(x, 8, z):
                C.set(x, 8, z, LANT_H)
    chest(C, cx + 4, 2, cz, "east", "fair_carousel") if C.free(cx + 4, 2, cz) else chest(C, cx, 2, cz + 4, "south",
                                                                                         "fair_carousel")
    spawner(C, cx - 7, 2, cz + 6, MOB_SPIDER) if C.free(cx - 7, 2, cz + 6) else None
    room(C, cx - 11, 2, cz - 11, cx + 11, 8, cz + 11, pred=lambda x, z: math.hypot(x - cx, z - cz) < 11.4)


# ------------------------------------------------------------------ the hall of mirrors
def hall_of_mirrors(C):
    """The hall of mirrors: a purple-and-gold pavilion with a mirrored façade on the plaza side; inside, a maze of
    glass and tinted glass (2-wide corridors) on a black-and-white checkered floor under a lit ceiling; a mirror
    chest at the deepest dead end; a back door east."""
    x0, z0, x1, z1 = MIR
    reserve(C, x0 - 1, z0, x1, z1)
    H = 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, ("black_concrete" if (x + z) % 2 else "white_concrete") if not edge else "polished_andesite")
            for y in range(1, H + 1):
                if edge:
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    if u % 5 == 0 or y == H:
                        spec = GILD if y == H else BRASS
                    elif y in (3, 4):
                        spec = TINT if u % 5 == 2 else "purple_terracotta"
                    else:
                        spec = "purple_terracotta"
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
            # ceiling with light panels
            if not edge:
                C.set(x, H, z, FROG if ((x - x0) % 3 == 2 and (z - z0) % 3 == 2) else "purple_concrete")
    # a barrel roof over it
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            k = min(z - (z0 - 1), (z1 + 1) - z)
            y = H + 1 + int(round(3.5 * math.sin(math.pi * k / (z1 - z0 + 2))))
            C.set(x, y, z, "purple_terracotta" if (x % 4) else GILD)
            for yy in range(H + 1, y):
                C.set(x, yy, z, "purple_terracotta")
    # the façade on the west: a tall mirrored frontispiece
    fz = (z0 + z1) // 2
    for z in range(fz - 6, fz + 7):
        for y in range(1, 15):
            top = 14 - int(abs(z - fz) * 0.9)
            if y > top:
                continue
            edge = abs(z - fz) == 6 or y == top
            spec = GILD if edge else (GLASSB if (y in range(4, 11) and abs(z - fz) <= 4 and (z + y) % 3) else
                                      "purple_terracotta")
            C.set(x0 - 1, y, z, spec)
    # entrance (corridor row 2) and back door (east, corridor row 3)
    ent = z0 + 1 + 3 * 2
    for z in (ent, ent + 1):
        for x in (x0 - 1, x0):
            for y in (1, 2, 3):
                C.clear(x, y, z)
    bk = z0 + 1 + 3 * 3
    for z in (bk, bk + 1):
        for y in (1, 2, 3):
            C.clear(x1, y, z)
    for z in (ent - 1, ent + 2):
        C.set(x0 - 2, 1, z, f"{W}dark_iron_plating_wall")
        C.set(x0 - 2, 2, z, LANT)
    # the maze: cells 3 apart (2-wide corridors), seeded depth-first
    nx, nz = 8, 5
    walls = set()
    for i in range(nx):
        for j in range(nz):
            walls.add((i, j, "e"))
            walls.add((i, j, "s"))
    seen = {(0, 2)}
    stack = [(0, 2)]
    order = []
    step = 0
    depth = {(0, 2): 0}
    while stack:
        i, j = stack[-1]
        nbrs = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= i + di < nx and 0 <= j + dj < nz and (i + di, j + dj) not in seen]
        if not nbrs:
            stack.pop()
            continue
        step += 1
        ni, nj = sorted(nbrs, key=lambda p: hash01(p[0] * 7 + step, p[1] * 13, 151))[0]
        if ni > i:
            walls.discard((i, j, "e"))
        elif ni < i:
            walls.discard((ni, nj, "e"))
        elif nj > j:
            walls.discard((i, j, "s"))
        else:
            walls.discard((ni, nj, "s"))
        seen.add((ni, nj))
        depth[(ni, nj)] = depth[(i, j)] + 1
        stack.append((ni, nj))
    # a couple of loops so it is not a pure tree
    for (i, j, s) in ((3, 1, "e"), (5, 3, "s"), (1, 3, "e"), (nx - 1, 3, "e")):
        walls.discard((i, j, s))

    def wall_spec(x, y, z):
        h = hash3(x, y, z, 152)
        return TINT if h < 0.35 else (GLASSB if h < 0.75 else "light_blue_stained_glass")

    for i in range(nx):
        for j in range(nz):
            bx, bz = x0 + 1 + 3 * i, z0 + 1 + 3 * j
            # post at the corner
            for y in range(1, H):
                C.set(bx + 2, y, bz + 2, GILD if y == 1 else wall_spec(bx + 2, y, bz + 2)) if bx + 2 < x1 and \
                    bz + 2 < z1 else None
            if (i, j, "e") in walls and bx + 2 < x1:
                for dz in (0, 1):
                    for y in range(1, H):
                        C.set(bx + 2, y, bz + dz, wall_spec(bx + 2, y, bz + dz))
            if (i, j, "s") in walls and bz + 2 < z1:
                for dx in (0, 1):
                    for y in range(1, H):
                        C.set(bx + dx, y, bz + 2, wall_spec(bx + dx, y, bz + 2))
    # the unused strip along the east and south walls: solid mirror
    for z in range(z0 + 1, z1):
        if x0 + 1 + 3 * nx <= x1 - 1:
            for x in range(x0 + 1 + 3 * nx, x1):
                for y in range(1, H):
                    if not (z in (bk, bk + 1) and y <= 3):
                        C.set(x, y, z, wall_spec(x, y, z))
                    else:
                        C.clear(x, y, z)
    # the deepest dead end gets the chest, another the wisp spawner
    deep = sorted(depth.items(), key=lambda kv: -kv[1])
    (di, dj), _ = deep[0]
    chest(C, x0 + 1 + 3 * di, 1, z0 + 1 + 3 * dj, "south", "fair_mirrors")
    (si, sj), _ = deep[len(deep) // 3]
    spawner(C, x0 + 2 + 3 * si, 1, z0 + 2 + 3 * sj, MOB_WISP)
    room(C, x0 + 1, 1, z0 + 1, x1 - 1, H - 1, z1 - 1)


# ------------------------------------------------------------------ the funhouse
def funhouse(C):
    """The haunted funhouse: a two-storey timber-and-plaster house, crooked turrets, and on its east front a giant
    clown-automaton face whose mouth is the way in. Ground floor: the mouth tunnel, the barrel of fun, the tilting
    room, the automaton gallery, the dressing room, the stair hall. Upper floor: the haunted attic and the crooked
    corridor to the slide. The slide drops back to the exit hall, whose iron door opens only from inside."""
    x0, z0, x1, z1 = FUN
    reserve(C, x0, z0, x1 + 3, z1)
    F2 = 7
    H = 13
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, "polished_andesite" if edge else ("black_concrete" if (x + z) % 2 else "white_concrete"))
            for y in range(1, H + 1):
                if edge:
                    u = (x - x0) if z in (z0, z1) else (z - z0)
                    if u % 5 == 0 or y in (F2, H):
                        spec = DLOG if u % 5 == 0 else DO
                    elif y in (3, 4, 10, 11) and u % 5 == 2:
                        spec = "magenta_stained_glass_pane" if y < 8 else "lime_stained_glass_pane"
                    else:
                        spec = ("lime_terracotta" if y < F2 else "magenta_terracotta") if (u // 5) % 2 else \
                            ("yellow_terracotta" if y < F2 else "cyan_terracotta")
                    C.set(x, y, z, spec)
                elif y == F2:
                    C.set(x, y, z, SP if (x + z) % 3 else DO)
                else:
                    C.clear(x, y, z)
    # roof: a crooked mansard
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            k = min(x - (x0 - 1), (x1 + 1) - x, z - (z0 - 1), (z1 + 1) - z)
            y = H + 1 + min(k, 5) + (1 if hash01(x // 4, z // 4, 161) < 0.3 and k > 2 else 0)
            C.set(x, y, z, "purple_terracotta" if k < 5 else "magenta_terracotta")
            if x0 <= x <= x1 and z0 <= z <= z1:
                for yy in range(H + 1, y):
                    if x in (x0, x1) or z in (z0, z1):
                        C.set(x, yy, z, "purple_terracotta")
    # crooked turrets on the west corners
    for (tx, tz) in ((x0 + 2, z0 + 2), (x0 + 2, z1 - 2)):
        for y in range(H + 1, H + 12):
            lean = (y - H) // 4
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    C.set(tx + dx + lean, y, tz + dz, "purple_terracotta" if (dx or dz) else DO)
        C.set(tx + 3, H + 12, tz, "magenta_terracotta")
        C.set(tx + 3, H + 13, tz, GILD)
        C.set(tx + 3, H + 14, tz, "red_banner[rotation=4]")
    clown_face(C)
    fun_rooms(C)
    room(C, x0 + 1, 1, z0 + 1, x1 - 1, F2 - 1, z1 - 1)
    room(C, x0 + 1, F2 + 1, z0 + 1, x1 - 1, H - 1, z1 - 1)


def clown_face(C):
    """The clown-automaton face on the east front: 17 wide, a white plaster face rising above the roof, orange hair
    tufts, a cone hat, blue diamond eye paint with amber lens eyes, a red bulb nose, cheek cogs, the mouth (3 wide,
    4 high) with brass teeth as the entrance and a red tongue carpet."""
    x0, z0, x1, z1 = FUN
    fx = x1 + 1
    zc = (z0 + z1) // 2                            # 25
    for z in range(zc - 9, zc + 10):
        for y in range(0, 22):
            dz = z - zc
            e = (dz / 8.6) ** 2 + ((y - 10) / 11.0) ** 2
            if e > 1.0:
                continue
            C.set(fx, y, z, "white_concrete" if y > 0 else "polished_andesite")
            if e > 0.82:
                C.set(fx, y, z, "white_terracotta")
            # a second layer for depth on the lower half
            C.set(fx + 1, y, z, "white_concrete") if e < 0.55 and y < 9 else None
    # hair tufts
    for sgn in (-1, 1):
        for k in range(14):
            a = k * 0.45
            z = zc + sgn * (8 + int(round(2 * math.sin(a))))
            y = 6 + k
            for dz in (0, sgn):
                C.set(fx, y, z + dz, "orange_wool")
                C.set(fx - 1, y, z + dz, "orange_wool")
    # the cone hat
    for k in range(10):
        r = 5 - k // 2
        for dz in range(-r, r + 1):
            C.set(fx, 21 + k, zc + dz, ("blue_wool" if (k // 2) % 2 else "yellow_wool") if abs(dz) < r else GILD)
            C.set(fx - 1, 21 + k, zc + dz, "blue_wool")
    C.set(fx, 31, zc, "red_wool")
    C.set(fx, 32, zc, "red_wool")
    # eyes: blue diamond paint, amber lens with a dark pupil
    for sgn in (-1, 1):
        ez, ey = zc + sgn * 4, 13
        for dz in range(-3, 4):
            for dy in range(-3, 4):
                if abs(dz) + abs(dy) <= 3:
                    C.set(fx + 1, ey + dy, ez + dz, "blue_concrete")
        for dz in (-1, 0, 1):
            for dy in (-1, 0, 1):
                C.set(fx + 1, ey + dy, ez + dz, "yellow_stained_glass" if (dz or dy) else "black_concrete")
                C.set(fx, ey + dy, ez + dz, "glowstone" if (dz or dy) else "black_concrete")
        C.set(fx + 1, ey + 4, ez, "black_concrete")
        C.set(fx + 1, ey + 4, ez + sgn, "black_concrete")
        # cheek cogs
        C.set(fx + 2, 7, zc + sgn * 6, f"{W}wall_cog[facing=east]")
        C.set(fx + 1, 7, zc + sgn * 6, "pink_concrete")
    # the nose
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dz) + abs(dy) <= 1:
                C.set(fx + 2, 9 + dy, zc + dz, "red_concrete")
    C.set(fx + 3, 9, zc, "red_concrete")
    # the mouth: a red smile ring, brass teeth, the opening
    for dz in range(-5, 6):
        y = 4 - int(round(2.2 * (1 - (dz / 5.5) ** 2)))
        C.set(fx + 1, y + 1, zc + dz, "red_concrete")
        C.set(fx + 1, y, zc + dz, "red_concrete")
    for z in range(zc - 1, zc + 2):
        for y in range(1, 5):
            for x in range(fx - 1, fx + 3):
                C.clear(x, y, z)
        C.set(fx + 1, 4, z, f"{W}brass_plating_slab[type=top,waterlogged=false]")
        for x in range(fx - 1, fx + 4):
            C.set(x, 0, z, "red_concrete")
    for z in (zc - 2, zc + 2):
        for y in range(1, 5):
            C.set(fx + 1, y, z, "red_concrete")
    C.set(fx + 2, 1, zc - 2, LANT)
    C.set(fx + 2, 1, zc + 2, LANT)


def fun_rooms(C):
    x0, z0, x1, z1 = FUN
    F2 = 7
    zc = (z0 + z1) // 2
    P = W + "mahogany_panelling"

    def wall_x(x, za, zb, y0, y1, spec=P, gaps=()):
        for z in range(za, zb + 1):
            for y in range(y0, y1 + 1):
                if (z, y) in gaps or any(z == g and y <= y0 + 2 for g in gaps if isinstance(g, int)):
                    C.clear(x, y, z)
                else:
                    C.set(x, y, z, spec)

    def wall_z(z, xa, xb, y0, y1, spec=P, gaps=()):
        for x in range(xa, xb + 1):
            for y in range(y0, y1 + 1):
                if any(x == g and y <= y0 + 2 for g in gaps):
                    C.clear(x, y, z)
                else:
                    C.set(x, y, z, spec)

    # ground floor partitions (x: -56 / -46; z: 22 / 28)
    wall_x(-46, z0 + 1, z1 - 1, 1, F2 - 1, gaps=(zc - 1, zc, zc + 1, 17, 33))
    wall_x(-56, z0 + 1, z1 - 1, 1, F2 - 1, gaps=(zc - 1, zc, zc + 1, 18, 33))
    wall_z(22, x0 + 1, -57, 1, F2 - 1, gaps=(-60,))
    wall_z(28, x0 + 1, -57, 1, F2 - 1, gaps=(-60,))
    wall_z(22, -55, -47, 1, F2 - 1)
    wall_z(28, -55, -47, 1, F2 - 1)
    wall_z(22, -45, x1 - 1, 1, F2 - 1, gaps=())
    wall_z(28, -45, x1 - 1, 1, F2 - 1, gaps=())
    # 1. the mouth tunnel (x -45..-39, z 23..27): red walls, a tongue carpet, hanging tonsil lamps
    for x in range(-45, x1):
        for z in range(23, 28):
            if z in (23, 27):
                for y in range(1, F2):
                    C.set(x, y, z, "red_terracotta" if y < 5 else "pink_terracotta")
            else:
                fp(C, x, 1, z, "red_carpet") if z == zc else None
        C.set(x, F2 - 1, 23, "pink_terracotta")
    for x in (-43, -40):
        hang(C, x, 5, zc, LANT_H, reach=2)
    # 2. the barrel of fun (x -55..-47, z 23..27): striped rings round a 3-wide walk
    for x in range(-55, -46):
        for z in range(23, 28):
            for y in range(1, F2):
                dz, dy = z - zc, y - 3
                d = math.hypot(dz * 1.0, dy * 1.2)
                if d > 2.3 and (abs(dz) <= 2):
                    col = ("red", "yellow", "blue", "white")[(x + int(math.degrees(math.atan2(dy, dz)) // 45)) % 4]
                    C.set(x, y, z, f"{col}_concrete")
                elif abs(dz) <= 1 and 1 <= y <= 4:
                    C.clear(x, y, z)
        C.set(x, 0, zc - 1, "blue_concrete")
        C.set(x, 0, zc + 1, "blue_concrete")
    for z in (zc - 1, zc + 1):
        for y in (1, 2, 3):
            C.clear(-46, y, z)
            C.clear(-56, y, z)
    C.set(-51, 5, zc, FROG)
    C.set(-51, 4, zc, AIR)
    C.clear(-51, 4, zc)
    # 3. the tilting room (x -63..-57, z 13..21): checker floor, crooked furniture, a slanted ceiling line
    for x in range(-63, -56):
        for z in range(13, 22):
            C.set(x, 0, z, "black_concrete" if (x + z) % 2 else "yellow_concrete")
            yy = F2 - 1 - (x + 63) // 3
            if yy < F2 - 1:
                for y in range(yy + 1, F2):
                    C.set(x, y, z, P)
    fp(C, -62, 1, 14, stair(DO_ST, "east"))
    fp(C, -62, 1, 15, TABLE)
    fp(C, -61, 1, 15, stair(DO_ST, "west", "top"))
    fp(C, -60, 1, 19, "flower_pot")
    fp(C, -63, 1, 20, "barrel[facing=east,open=false]")
    fp(C, -63, 2, 20, "lantern[hanging=false,waterlogged=false]")
    chest(C, -63, 1, 13, "east", "fair_funhouse")
    fp(C, -58, 3, 13, "clock") if False else None
    # 4. the automaton gallery (x -63..-57, z 29..37): copper golem statues on brass pedestals, a band
    poses = ("standing", "running", "star", "sitting")
    for i, (x, z) in enumerate(((-62, 30), (-62, 33), (-62, 36), (-59, 36), (-58, 30))):
        C.set(x, 1, z, BRASS)
        fp(C, x, 2, z, f"copper_golem_statue[copper_golem_pose={poses[i % 4]},facing=east,waterlogged=false]")
    fp(C, -60, 1, 33, "note_block[instrument=snare,note=3,powered=false]")
    fp(C, -59, 1, 33, "note_block[instrument=bell,note=9,powered=false]")
    fp(C, -58, 1, 34, f"{W}copper_pipe[axis=y]")
    fp(C, -58, 2, 34, f"{W}copper_pipe[axis=y]")
    spawner(C, -60, 1, 31, MOB_SPIDER)
    # 5. the dressing room (x -55..-47, z 13..21): mirrors with bulbs, a make-up table, costume racks
    for x in range(-54, -48, 2):
        C.set(x, 2, 13, GLASS) if False else None
        C.set(x, 2, 14, GLASSB) if False else None
    for x in range(-54, -47):
        C.set(x, 4, 13, GLASSB if x % 2 else EDISON)
        fp(C, x, 1, 14, f"{W}mahogany_table" if x % 3 else f"{W}mahogany_chair[facing=north]")
    for z in (17, 19):
        C.bp.entity(-54, 1, z, {"id": "minecraft:armor_stand", "Rotation": [270.0, 0.0], "ShowArms": True})
    fp(C, -48, 1, 20, "red_wool")
    fp(C, -48, 2, 20, "yellow_carpet")
    chest(C, -48, 1, 18, "west", "fair_funhouse")
    # 6. the stair hall (x -55..-47, z 29..37): a spiral disc floor, the stair up along the north wall
    for x in range(-55, -46):
        for z in range(29, 38):
            a = math.atan2(z - 33, x + 51)
            d = math.hypot(z - 33, x + 51)
            C.set(x, 0, z, ("red_concrete" if int(math.degrees(a) / 30 + d) % 2 else "white_concrete"))
    for i in range(7):
        x = -48 - i
        for z in (35, 36, 37):
            C.set(x, 1 + i, z, stair(SP_ST, "west"))
            for y in range(1, 1 + i):
                C.set(x, y, z, SP)
            for y in range(2 + i, 2 + i + 4):
                C.clear(x, y, z)
    for z in (35, 36, 37):
        C.set(-55, F2, z, SP)       # landing
        C.clear(-55, F2 + 1, z)
        C.clear(-55, F2 + 2, z)
    for x in range(-54, -47):
        C.set(x, F2 + 1, 34, SP_FENCE)
    for z in (35, 36, 37):
        C.set(-47, F2 + 1, z, SP_FENCE)
    hang(C, -51, 5, 31, LANT_H, reach=2)
    # 7. the exit hall (x -45..-39, z 13..21): the slide lands here, the iron door out (south-east)
    for x in range(-45, x1):
        for z in range(13, 22):
            C.set(x, 0, z, "red_concrete" if (x // 2 + z // 2) % 2 else "yellow_concrete")
    oneway_door(C, x1, 1, 15, "west", "lime_terracotta")
    hang(C, -42, 5, 17, LANT_H, reach=2)
    # the haunted attic upstairs (x -63..-48, z 13..37): coffins, cobwebs, soul lanterns, a banshee
    wall_x(-47, z0 + 1, z1 - 1, F2 + 1, 12, spec=SP, gaps=(14, 15))
    for (cx_, cz_) in ((-61, 16), (-58, 16), (-61, 30), (-58, 30)):
        for dz in range(3):
            C.set(cx_, F2 + 1, cz_ + dz, "spruce_slab[type=bottom,waterlogged=false]" if dz else
                  "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for (x, z) in ((-62, 24), (-55, 20), (-50, 34), (-60, 36), (-52, 14)):
        C.set(x, 12, z, "cobweb")
    for (x, z) in ((-55, 24), (-55, 32), (-55, 16), (-61, 24)):
        hang(C, x, 11, z, SLANT_H, reach=2)
    for x in range(-62, -48, 4):
        C.set(x, F2 + 1, 37, "skeleton_skull[powered=false,rotation=8]")
        C.set(x, F2 + 1, 36, "bone_block[axis=y]") if False else None
    spawner(C, -53, F2 + 1, 26, MOB_BANSHEE)
    chest(C, -62, F2 + 1, 26, "east", "fair_funhouse")
    for z in range(13, 38, 4):
        C.set(-56, 12, z, DLOGX) if False else None
    # the crooked corridor (x -46..-39, z 13..37) runs south to the slide
    for z in range(z0 + 1, z1):
        for x in range(-46, x1):
            if x == -46:
                continue
    for (x, z) in ((-44, 34), (-41, 30), (-44, 26), (-41, 22)):
        C.set(x, F2 + 1, z, f"copper_golem_statue[copper_golem_pose=star,facing=west,waterlogged=false]")
    for z in range(16, 37, 5):
        hang(C, -42, 11, z, LANT_H, reach=2)
    C.set(x1 - 1, 10, 33, "observer[facing=west,powered=false]")
    # the slide: a polished chute from the upper floor down into the exit hall, striped side walls
    for i in range(7):
        z = 20 - i
        for x in (-44, -43, -42):
            C.set(x, F2 - i, z, stair("smooth_quartz_stairs", "south"))
            for y in range(F2 - i + 1, F2 - i + 5):
                C.clear(x, y, z)
    for x in (-45, -41):
        for i in range(5):
            for y in range(F2 - i + 1, F2 - i + 3):
                C.set(x, y, 20 - i, "red_concrete" if (y + i) % 2 else "yellow_concrete")
    for x in (-45, -41):
        C.set(x, F2 + 1, 21, SP_FENCE)
    # the laughing-heads room (x -63..-57, z 23..27): carved faces on shelves, a bell, a barrel organ
    for z in range(23, 28):
        C.set(-63, 3, z, "carved_pumpkin[facing=east]" if z % 2 else "jack_o_lantern[facing=east]")
        C.set(-63, 2, z, slab(DO_SL, "top"))
        C.set(-63, 1, z, "dark_oak_planks")
    for x in range(-62, -57):
        C.set(x, 4, 22, "jack_o_lantern[facing=south]" if x % 2 else "carved_pumpkin[facing=south]")
        C.set(x, 4, 28, "jack_o_lantern[facing=north]" if x % 2 else "carved_pumpkin[facing=north]")
    fp(C, -60, 1, 25, "note_block[instrument=bit,note=5,powered=false]")
    fp(C, -59, 1, 25, "bell[attachment=floor,facing=east,powered=false]")
    # the automaton workshop (x -45..-39, z 29..37): workbench, spare heads and arms, cogs, the tinker's chest
    for z in range(29, 38):
        fp(C, -39, 1, z, slab(DO_SL, "top") if z % 3 else "crafting_table")
        if z % 2:
            C.set(-39 + 0, 3, z, f"{W}wall_cog[facing=west]") if False else None
    for z in (30, 33, 36):
        C.set(x1 - 0, 3, z, GEAR) if False else None
        fp(C, -39, 2, z, f"copper_golem_statue[copper_golem_pose=sitting,facing=west,waterlogged=false]")
    fp(C, -44, 1, 37, "anvil[facing=west]")
    fp(C, -43, 1, 37, "grindstone[face=floor,facing=north]")
    fp(C, -45, 1, 30, COPPER)
    fp(C, -45, 2, 30, GEAR)
    chest(C, -45, 1, 34, "east", "fair_funhouse")
    hang(C, -42, 5, 33, LANT_H, reach=2)


# ------------------------------------------------------------------ lighting
PLAIN = {"minecraft:" + n for n in ("grass_block", "dirt_path", "gravel", "coarse_dirt", "packed_mud", "polished_andesite",
                                    "andesite", "sand", "sandstone", "smooth_sandstone", "spruce_planks", "birch_planks",
                                    "dark_oak_planks", "black_concrete", "white_concrete", "yellow_concrete",
                                    "red_concrete", "blue_concrete", "stone_bricks", "cut_sandstone", "mud_bricks")} | {
    PARQ, TREAD, BTILE, IRON}


def lighting(C, rounds=5):
    """Block light 8 on every walkable floor inside the registered rooms: a froglight set into a plain floor, else a
    lantern hung from the ceiling, else a lantern on a fence post."""
    from ..blueprint import is_solid
    bp = C.bp
    cells = set()
    for (x0, y0, z0, x1, y1, z1, pred) in C.rooms:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if pred and not pred(x, z):
                    continue
                for y in range(y0, y1 + 1):
                    cells.add((x, y, z))
    for r in range(rounds):
        L, (ox, oy, oz), _ = light_map(bp)
        dark = []
        B = bp.blocks
        for (x, y, z) in cells:
            b = B.get((x, y, z))
            if b is None or b[0] != AIR:
                continue
            below = B.get((x, y - 1, z))
            head = B.get((x, y + 1, z))
            if below is None or head is None or head[0] != AIR:
                continue
            sb = below[0].split(":")[1]
            if not (is_solid(below[0]) or sb.endswith("_slab") or sb.endswith("_stairs")):
                continue
            if "glass" in sb or "fence" in sb or "chain" in sb or "lantern" in sb or sb.endswith("_wall"):
                continue
            if L[x - ox, y - oy, z - oz] < 8:
                dark.append((x, y, z))
        if not dark:
            break
        dark.sort(key=lambda p: (L[p[0] - ox, p[1] - oy, p[2] - oz], p))
        placed = []
        for (x, y, z) in dark:
            if any(abs(x - a) + abs(y - b) + abs(z - c) < 5 for (a, b, c) in placed):
                continue
            fb = bp.get(x, y - 1, z)
            if fb in PLAIN and (x, y, z) not in C.keep_lit:
                bp.set(x, y - 1, z, FROG)
                placed.append((x, y, z))
                continue
            t = y + 2
            while t < y + 16 and C.free(x, t, z):
                t += 1
            if t < y + 16 and t - y >= 3 and not C.free(x, t, z) and "water" not in (bp.get(x, t, z) or ""):
                for yy in range(y + 3, t):
                    bp.set(x, yy, z, CHAIN)
                bp.set(x, y + 2, z, LANT_H)
                placed.append((x, y, z))
                continue
            if C.free(x, y + 1, z) and (x, y, z) not in C.keep:
                bp.set(x, y, z, BP_FENCE)
                bp.set(x, y + 1, z, LANT)
                placed.append((x, y, z))
        if not placed:
            break


# ------------------------------------------------------------------ the builder
def clockwork_carnival(bp):
    C = Ctx(bp)
    C.paths = {}
    C.busy = set()
    C.boxes = []
    C.rooms = []
    C.track = {}
    C.norail = set()
    C.nobent = set()
    C.keep_lit = set()
    plan_paths(C)
    ground(C)
    # columns the coaster bents must not land on: buildings and their doorsteps
    for (x0, z0, x1, z1) in (FUN, MIR, ENG, (CAR[0] - 14, CAR[1] - 14, CAR[0] + 14, CAR[1] + 14),
                             (HS[0] - 6, HS[1] - 6, HS[0] + 6, HS[1] + 6), (-16, -6, 16, 26),
                             (LIFT[0] - 2, LIFT[1] - 2, LIFT[0] + 2, LIFT[1] + 2)):
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                C.nobent.add((x, z))
    for x in range(-47, -34):
        for z in range(TZ - 8, TZ + 9):
            C.nobent.add((x, z))
    brake_platform(C)
    summit(C)
    station(C)
    coaster(C)
    big_top(C)
    wheel(C)
    wheel_service(C)
    engine_house(C)
    ringmaster(C)
    helter_skelter(C)
    funhouse(C)
    hall_of_mirrors(C)
    carousel(C)
    plaza(C)
    midway(C)
    gate(C)
    camp(C)
    fence(C)
    C.bp.boss_seal(TX, 0, TZ, BOSS, 22)
    meadow(C)
    lighting(C)


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("midway", (0, 1, 64), (0, 6, 40)),
    ("carousel", (30, 2, 6), (34, 7, 10)),
    ("hall_of_mirrors", (22, 1, -13), (32, 2, -13)),
    ("funhouse_barrel", (-44, 1, 25), (-56, 3, 25)),
    ("engine_house", (-64, 1, -40), (-74, 6, -32)),
    ("coaster_summit", (-25, 32, -15), (0, 46, -56)),
    ("big_top_ring", (-32, 13, -56), (0, 4, -56)),
    ("strongbox_wagon", (0, 1, -81), (-4, 3, -87)),
]

register(StructureDef(
    "clockwork_carnival", "overworld", ["flower_forest", "birch_forest", "old_growth_birch_forest"],
    [Piece("carnival", clockwork_carnival, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_SPIDER, 5, 1, 2), (MOB_WISP, 3, 1, 1), (MOB_DRONE, 2, 1, 1), (MOB_MITE, 3, 1, 3)],
    title_fr="La Fête foraine mécanique", title_en="The Clockwork Carnival"))

"""The Cloud Pagoda (La Pagode des nuages): a nine-tiered pagoda of cherry wood and white plaster, 111 blocks from its
floor to the finial, on a terraced mountain garden in a cherry grove or a meadow. Colossal tier (tools/BUILDING.md §1,
§12 concept 23, §10 legacy-dungeon template, §15), steampunk accents (tools/STYLE_STEAMPUNK.md: brass hip ornaments
and clockwork wind-chimes on every eave, a counterweight lift, the brass skeleton of a clockwork dragon).

Silhouette (one noun phrase, §15.1): a slender nine-roofed pagoda with flaring blue-slate eaves and a brass spire,
standing on three stepped garden terraces, a brass dragon skeleton coiled round its lower tiers.

Layout, ground y = 0 (feet 1), x east, z south; the pagoda's axis is (0, PZ = -20).
  * the massif: L1 (top y 8) is a natural rocky hill with grass on top (superellipse r 56, two-octave noisy face);
    L2 (top 18, r 40) and L3 (top 28, r 27) are battered stone retaining walls with azalea hedges and stone
    balustrades. L3 is the paved pagoda court;
  * the approach (south, ground): the pilgrims' camp and its waystone, a path through a moon gate in a white
    plaster wall (it frames the pagoda: the reveal), the lower koi pond crossed by a zig-zag bridge, the forecourt
    and the grand stair up the L1 face; stone lanterns all the way;
  * the garden route: the axial stair L1 -> L2, then round L2: the bell pavilion (east), the dragon's skull lying
    before its shrine (north: torii, purification basin, the shrine hall, site of grace = the hub), the monks' dojo
    (west, the guardians) and the west stair to the L3 court and the pagoda's south door. Optional: the upper koi
    pond and the tea house on L1 east (a stair up to L2 east: a loop), the monks' garden, the bamboo grove and the
    hermit's grotto (secret, a hidden passage into the L2 wall) on L1 west, with the side route up from the ground;
  * the pagoda: eight closed tiers round a central pillar, each a room of its own, linked by stairs that climb along
    alternate walls (every room is crossed): 1 the prayer hall (altar, colonnade, the lift lobby), 2 the scroll
    library, 3 the armoury of practice weapons (padded sparring floor), 4 the meditation hall round a raked sand
    garden (site of grace), 5 the mechanical orrery of the seasons, 6 the abbot's quarters, 7 the chime engine that
    drives the wind-chimes, 8 the last stair hall (site of grace) and, behind a wall, the vault. Every upper tier has
    a door onto its balcony (vistas);
  * the boss (feet 108): the open top tier, a 33-wide deck under the ninth roof on four posts, the mist at the head
    of the stair from tier 8; the stair down to the vault behind sealed bars;
  * shortcuts (§10.4): the counterweight lift in the central pillar (a 71-block drop well into a pool beside a
    bubble-column tube) from the vault to the lift lobby of the prayer hall, whose iron door opens from inside only;
    the prayer hall's east iron door onto the court (toward the north stair and the hub); the axial gate at the head
    of the L2 -> L3 stair (opens from the court); the grotto's passage; terrace stairs give each terrace two links.
Loot gradient (§15.6): camp and gardens tier 1; tea house, bell pavilion, prayer hall 1-2; dojo, shrine, library 2;
armoury, meditation 2; orrery, grotto (secret) 2-3; abbot and chime engine 3; the vault 3-4.
Height budget: the finial stands 148 above the ground layer, so it stays under the build limit wherever the ground is
below y ~170 (cherry groves and meadows).
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, IRON, PIPES, TABLE, VERD, W, fbm, hash01, hash3,
                       vnoise)
from ..parts import LOOT, MOD

# the champion of the open top tier: the Chime Abbot (entity/boss/ChimeAbbot.java, tools/BOSSES.md)
BOSS = "brasshaven:chime_abbot"
MOB_MONK = W + "bell_monk"
MOB_KNIGHT = W + "skeleton_knight"
MOB_WISP = W + "lantern_wisp"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_GARGOYLE = W + "gargoyle"

# ------------------------------------------------------------------ dimensions
PZ = -20                                   # pagoda axis z (x = 0)
L1, L2, L3 = 8, 18, 28                     # terrace top blocks (feet +1)
R1, R2, R3 = 56, 40, 27                    # terrace radii (superellipse exponents 2.4 / 3 / 3)
TIERS = ((18, 14), (17, 10), (16, 10), (15, 10), (14, 9), (13, 9), (12, 9), (11, 8))   # (half width, height)


def _tiers():
    out, f = [], L3 + 1
    for j, (hw, h) in enumerate(TIERS):
        out.append({"j": j + 1, "hw": hw, "H": h, "f": f, "ceil": f + h - 3, "top": f + h - 1})
        f += h
    return out


T = [None] + _tiers()                      # T[1] .. T[8]
FA = T[8]["top"] + 1                       # arena feet (108)
DECK = 16                                  # arena deck half width
POSTS = 12                                 # the top roof's posts (3 x 3, centred on +-12)
ROOF9 = FA + 13                            # first block layer of the ninth roof (arena air FA .. ROOF9 - 1)

# materials
AIR = "minecraft:air"
WATER = "water[level=0]"
PL1, PL2 = "white_concrete", "calcite"     # white plaster (light -> slightly warmer)
POST = "stripped_cherry_log[axis=y]"
BEAM_X, BEAM_Z = "cherry_log[axis=x]", "cherry_log[axis=z]"
CH, CH_ST, CH_SL = "cherry_planks", "cherry_stairs", "cherry_slab"
CH_FENCE, CH_TRAP = "cherry_fence", "cherry_trapdoor"
ROOF, ROOF_ST, ROOF_SL = W + "blue_slate_tiles", W + "blue_slate_tile_stairs", W + "blue_slate_tile_slab"
SLATE, SLATE_ST = W + "slate_roof_tiles", W + "slate_roof_tile_stairs"
RED, RED_ST = W + "crimson_roof_tiles", W + "crimson_roof_tile_stairs"
BTILE, BTILE_ST = W + "brass_tiles", W + "brass_tile_stairs"
GILD, ENGR = W + "gilded_trim", W + "engraved_brass"
TORII, TORII_P = "stripped_mangrove_log", "mangrove_planks"
PANE = "white_stained_glass_pane"
GRILLE = W + "brass_grille"
SB, MSB, CSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"
PAND, AND_ = "polished_andesite", "andesite"
PAND_SL = "polished_andesite_slab"
SB_ST, SB_WALL = "stone_brick_stairs", "stone_brick_wall"
GRASS = "grass_block[snowy=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
BELL_C = "bell[attachment=ceiling,facing=north,powered=false]"
ROD_D = "lightning_rod[facing=down,powered=false,waterlogged=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
CH_LEAF = "cherry_leaves[distance=1,persistent=true,waterlogged=false]"
AZ_LEAF = "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]"
AZ_LEAF2 = "azalea_leaves[distance=1,persistent=true,waterlogged=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def cheb(x, z):
    return max(abs(x), abs(z - PZ))


def toward_centre(x, z):
    """Horizontal direction from (x, z) toward the pagoda axis along the dominant axis."""
    dx, dz = -x, PZ - z
    if abs(dz) >= abs(dx):
        return "south" if dz > 0 else "north"
    return "east" if dx > 0 else "west"


# ------------------------------------------------------------------ the site context
class Ctx:
    """Blueprint wrapper: ``keep`` holds reserved air (walkways, headroom, balconies) that later decoration (``put``)
    never fills; ``wet`` the water the build places."""

    def __init__(self, bp):
        self.bp = bp
        self.keep = set()
        self.wet = set()
        self.top = {}          # massif column -> top block y

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))

    def put(self, x, y, z, spec):
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def clear(self, x, y, z):
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def water(self, x, y, z, spec=WATER):
        self.bp.set(x, y, z, spec)
        self.wet.add((x, y, z))
        self.keep.discard((x, y, z))

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b and "bubble" not in b

    def free(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR


def carve(C, x0, y0, z0, x1, y1, z1):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.clear(x, y, z)


def fill(C, x0, y0, z0, x1, y1, z1, spec):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for z in range(min(z0, z1), max(z0, z1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def hang(C, x, y, z, lamp=LANT_H, reach=14):
    """A lamp on a chain from the first solid block above (x, y, z)."""
    top = y + 1
    while top < y + reach and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return
    for yy in range(y + 1, top):
        C.set(x, yy, z, CHAIN)
    C.set(x, y, z, lamp)


def lever(C, x, y, z, facing):
    C.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{W}brass_railing[facing={facing}]")


def candle(C, x, y, z, n=3, color=""):
    name = f"{color}_candle" if color else "candle"
    C.set(x, y, z, f"{name}[candles={n},lit=true,waterlogged=false]")


def carpet(C, x, y, z, color):
    C.set(x, y, z, f"{color}_carpet")


def stone_lantern(C, x, y, z, tall=False):
    """A toro: plinth, shaft, fire box (a lantern under a hat), a hat with a knob; feet y."""
    C.set(x, y, z, PAND)
    C.set(x, y + 1, z, "andesite_wall")
    if tall:
        C.set(x, y + 2, z, "andesite_wall")
    k = y + (3 if tall else 2)
    C.set(x, k, z, PAND)
    C.set(x, k + 1, z, LANT)
    C.set(x, k + 2, z, slab("andesite_slab", "top"))
    C.set(x, k + 3, z, "stone_button[face=floor,facing=north,powered=false]")


def cherry_tree(C, x, y, z, h=5, seed=0, spread=4):
    """A cherry: a leaning trunk, two or three branches, flat wide clouds of blossom and petals on the ground below;
    feet y (the trunk starts at y)."""
    rng = hash01(x, z, 400 + seed)
    lx, lz = (1, 0) if rng < 0.25 else (-1, 0) if rng < 0.5 else (0, 1) if rng < 0.75 else (0, -1)
    tx, tz = x, z
    for i in range(h):
        if i == h // 2:
            tx, tz = tx + lx, tz + lz
        C.put(tx, y + i, tz, "cherry_log[axis=y]")
    crowns = [(tx, y + h, tz, spread)]
    for k, (bx, bz) in enumerate(((1, 1), (-1, -1), (1, -1), (-1, 1))):
        if hash01(x + k, z - k, 410 + seed) < 0.6:
            n = 2 + int(hash01(x, z + k, 420 + seed) * 2)
            px, py, pz = tx, y + h - 2, tz
            for s in range(1, n + 1):
                px, pz = tx + bx * s, tz + bz * s
                py = y + h - 2 + (s + 1) // 2
                C.put(px, py, pz, "cherry_log[axis=x]" if s % 2 else "cherry_log[axis=z]")
            crowns.append((px, py + 1, pz, spread - 1))
    for (cx, cy, cz, r) in crowns:
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in (-1, 0, 1):
                    rr = r - (1 if dy == 1 else 0) - (1 if dy == -1 else 0)
                    d = math.hypot(dx, dz)
                    if d <= rr + 0.3 and hash3(cx + dx, cy + dy, cz + dz, 430 + seed) < (0.92 if d < rr - 0.7 else 0.55):
                        if C.free(cx + dx, cy + dy, cz + dz):
                            C.put(cx + dx, cy + dy, cz + dz, CH_LEAF)
    # petals on the grass below the crown
    for dx in range(-spread, spread + 1):
        for dz in range(-spread, spread + 1):
            if hash01(x + dx, z + dz, 440 + seed) < 0.35:
                gx, gz = x + dx, z + dz
                gy = y - 1
                if C.get(gx, gy, gz) == "minecraft:grass_block" or (C.get(gx, gy, gz) or "").startswith(
                        "minecraft:grass_block"):
                    if C.free(gx, y, gz) and (gx, y, gz) not in C.keep:
                        n = 1 + int(hash01(gx, gz, 441) * 4)
                        C.put(gx, y, gz, f"pink_petals[facing=north,flower_amount={n}]")


# ------------------------------------------------------------------ the terraced massif
def rse(x, z, p):
    return (abs(x) ** p + abs(z - PZ) ** p) ** (1.0 / p)


def r1_edge(x, z):
    """The natural L1 edge: two-octave noise, calmed on the south axis where the grand stair lands."""
    n = 7.0 * (fbm(x, z, 24.0, 31) - 0.5) + 2.6 * (vnoise(x, z, 5.0, 32) - 0.5)
    calm = 1.0
    if z > PZ + 30:
        calm = min(1.0, abs(x) / 16.0)
    return R1 + n * (0.2 + 0.8 * calm)


def column(x, z):
    """(top block y, level) of the massif column at (x, z), or (None, 0). Level 1 natural rock, 2 / 3 masonry."""
    rr1 = rse(x, z, 2.4)
    e = r1_edge(x, z)
    t1 = L1 if rr1 <= e else L1 - int((rr1 - e) * 2.4 + 0.5)
    t, lev = (t1, 1) if t1 >= 0 else (None, 0)
    for (R, top, base, levn) in ((R2, L2, L1, 2), (R3, L3, L2, 3)):
        rr = rse(x, z, 3.0)
        tt = top if rr <= R else top - int(math.ceil((rr - R) * 3.0))
        if tt > base and (t is None or tt > t):
            t, lev = tt, levn
    return t, lev


def rock(x, y, z):
    """Natural L1 rock: jittered strata of stone, andesite and tuff; moss near the ground and on the north."""
    j = int((hash01(x // 4, z // 4, 51) - 0.5) * 3)
    band = (y + j) % 7
    h = hash3(x, y, z, 52)
    if y <= 1 and h < 0.45:
        return "mossy_cobblestone"
    if z < PZ - 40 and h < 0.18:
        return "mossy_cobblestone"
    if band in (0, 1):
        return AND_ if h < 0.8 else "stone"
    if band == 4:
        return "tuff" if h < 0.7 else AND_
    return "stone" if h < 0.85 else "cobblestone"


def wall_stone(x, y, z, base):
    """Retaining wall masonry: dark and mossy in its bottom courses, stone bricks above, a few cracked."""
    h = hash3(x, y, z, 61)
    d = y - base
    if d <= 1:
        return MSB if h < 0.6 else "mossy_cobblestone"
    if d <= 3:
        return MSB if h < 0.3 else SB
    return CSB if h < 0.12 else SB


def court_pave(x, z):
    """The L3 court: polished andesite flags in a square grid round the pagoda, stone-brick borders."""
    r = cheb(x, z)
    if r % 5 == 0:
        return SB
    return PAND if hash01(x, z, 71) < 0.8 else "smooth_stone"


def massif(C):
    for x in range(-64, 65):
        for z in range(-86, 46):
            t, lev = column(x, z)
            if t is None:
                continue
            C.top[(x, z)] = t
            edge1 = rse(x, z, 2.4) > r1_edge(x, z) - 3
            r2, r3 = rse(x, z, 3.0), rse(x, z, 3.0)
            for y in range(-3 if edge1 else 0, t + 1):
                if lev == 1:
                    if y == t:
                        spec = GRASS if t >= L1 - 1 else rock(x, y, z)
                    elif y >= t - 2 and t >= L1 - 1:
                        spec = "dirt"
                    else:
                        spec = rock(x, y, z) if (edge1 or y <= 1) else "stone"
                elif y <= L1:
                    spec = "stone"
                elif lev == 2 or y <= L2:
                    if lev == 3:
                        spec = "stone"
                    elif r2 > R2 - 1.5:
                        spec = PAND if (y == t == L2 and r2 <= R2) else wall_stone(x, y, z, L1)
                    elif y == t:
                        spec = GRASS
                    elif y >= t - 2:
                        spec = "dirt"
                    else:
                        spec = "stone"
                else:
                    if r3 > R3 - 1.5:
                        if y == t == L3 and r3 <= R3:
                            spec = PAND                                   # the coping
                        else:
                            spec = PAND if y == L3 - 5 else wall_stone(x, y, z, L2)
                    elif y == t:
                        spec = court_pave(x, z)
                    else:
                        spec = "stone"
                C.set(x, y, z, spec)


def terrace_edges(C, top, mat_fn, skip=()):
    """Cells on a terrace's rim (column top == top with a lower 4-neighbour): a parapet one block above."""
    out = []
    for (x, z), t in C.top.items():
        if t != top:
            continue
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            tn = C.top.get((x + dx, z + dz))
            if tn is None or tn < top:
                out.append((x, z))
                break
    for (x, z) in out:
        if any(f(x, z) for f in skip):
            continue
        spec = mat_fn(x, z)
        if spec:
            C.put(x, top + 1, z, spec)
    return out


def parapets(C):
    """Azalea hedges on the L2 rim, a stone balustrade with lanterns on the L3 rim."""
    def hedge(x, z):
        return AZ_LEAF if hash01(x, z, 81) < 0.45 else AZ_LEAF2
    terrace_edges(C, L2, hedge)

    def balustrade(x, z):
        if (x * 7 + z * 3) % 9 == 0:
            return None
        return SB_WALL
    edge = terrace_edges(C, L3, balustrade)
    for (x, z) in edge:
        if (x + 2 * z) % 11 == 0 and (x, L3 + 1, z) not in C.keep and C.get(x, L3 + 1, z) == "minecraft:" + SB_WALL:
            C.put(x, L3 + 2, z, LANT)


# ------------------------------------------------------------------ stairs, paths, ground
def climb(C, x0, z0, d, n, y0, width, mat=SB_ST, support=SB, rails=SB_WALL, landing=PAND, head=4, lamps=True,
          land_max=10):
    """A stair of ``n`` treads climbing toward ``d`` from (x0, z0) (the first tread), ``width`` wide centred on that
    line: tread i (0..n-1) is a stair block at y0 + i. Then a landing at y0 + n, carried on in ``d`` until it meets a
    column of the terrace (top >= y0 + n) or ``land_max`` cells. Treads and landing are filled down to the first solid
    block; balustrades on both sides; headroom reserved. Returns the landing cells."""
    dx, dz = DV[d]
    lx, lz = -dz, dx
    hw = width // 2
    ytop = y0 + n

    def column_down(x, y, z, spec):
        for yy in range(y, -4, -1):
            if C.solid(x, yy, z):
                return
            C.set(x, yy, z, spec)

    cells = []
    for i in range(n):
        for k in range(-hw - 1, hw + 2):
            x, z = x0 + dx * i + lx * k, z0 + dz * i + lz * k
            y = y0 + i
            if abs(k) == hw + 1:
                column_down(x, y, z, support)
                if rails:
                    C.set(x, y + 1, z, rails)
                continue
            column_down(x, y - 1, z, support)
            C.set(x, y, z, stair(mat, d))
            for hh in range(1, head + 1):
                C.clear(x, y + hh, z)
            cells.append((x, y, z))
    land = []
    for s in range(land_max):
        i = n + s
        done = True
        for k in range(-hw, hw + 1):
            x, z = x0 + dx * i + lx * k, z0 + dz * i + lz * k
            t = C.top.get((x, z))
            if t is None or t < ytop or s == 0:
                done = False
        for k in range(-hw - 1, hw + 2):
            x, z = x0 + dx * i + lx * k, z0 + dz * i + lz * k
            column_down(x, ytop - 1, z, support)
            if abs(k) == hw + 1:
                if C.top.get((x, z), -99) < ytop and rails:
                    C.set(x, ytop, z, support)
                    C.set(x, ytop + 1, z, rails)
                continue
            C.set(x, ytop, z, landing)
            for hh in range(1, head + 1):
                C.clear(x, ytop + hh, z)
            land.append((x, ytop, z))
        if done:
            break
    if lamps:
        for k in (-hw - 1, hw + 1):
            x, z = x0 + lx * k, z0 + lz * k
            if C.get(x, y0 + 1, z) == "minecraft:" + rails:
                C.set(x, y0 + 2, z, LANT)
    return land


def seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    L2_ = vx * vx + vz * vz
    t = 0.0 if L2_ == 0 else max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / L2_))
    cx, cz = ax + vx * t, az + vz * t
    return math.hypot(px - cx, pz - cz), t


def path_cells(pts, w):
    hw = w / 2.0
    x0 = int(min(p[0] for p in pts) - hw - 1)
    x1 = int(max(p[0] for p in pts) + hw + 1)
    z0 = int(min(p[1] for p in pts) - hw - 1)
    z1 = int(max(p[1] for p in pts) + hw + 1)
    out = []
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            d = min(seg_dist(x, z, pts[i], pts[i + 1])[0] for i in range(len(pts) - 1))
            if d <= hw:
                out.append((x, z, d))
    return out


def path(C, pts, y, w, mat, head=3, only_top=True):
    """A walk along a polyline at surface y: the surface block becomes ``mat`` (a function of x, z, distance to the
    centre line), the cells above it are reserved air."""
    for (x, z, d) in path_cells(pts, w):
        t = C.top.get((x, z))
        if only_top and y > 0 and t != y:
            continue
        if only_top and y == 0 and t is not None:
            continue
        b = C.get(x, y, z)
        if b is not None and ("water" in b or "stairs" in b or "slab" in b):
            continue
        C.set(x, y, z, mat(x, z, d) if callable(mat) else mat)
        for hh in range(1, head + 1):
            if C.free(x, y + hh, z):
                C.clear(x, y + hh, z)


def flag(x, z, d):
    """The main path: pale polished andesite flags, mossier toward the edges."""
    h = hash01(x, z, 91)
    if d > 1.4 and h < 0.35:
        return "mossy_cobblestone" if h < 0.15 else AND_
    return PAND if h < 0.7 else ("smooth_stone" if h < 0.9 else AND_)


def gravel(x, z, d):
    """Optional paths: gravel and coarse dirt with stepping stones."""
    h = hash01(x, z, 92)
    if (x + z) % 3 == 0 and d < 0.8:
        return PAND
    return "gravel" if h < 0.6 else "coarse_dirt"


GARDEN = (-44, 36, 44, 97)        # the ground-level garden (x0, z0, x1, z1)


def ground(C):
    """The ground-level garden south of the massif (and a strip to the west side stair): grass on two layers of
    dirt, air cleared above it so no hill buries it; a skirt of grass and scree round the foot of the hill."""
    x0, z0, x1, z1 = GARDEN
    cols = set()
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            cols.add((x, z))
    for (x, z, d) in path_cells([(-44, 40), (-58, 30), (-66, 12), (-66, 2)], 9):
        cols.add((x, z))
    for (x, z) in cols:
        if (x, z) in C.top:
            continue
        C.set(x, 0, z, GRASS if hash01(x, z, 101) < 0.93 else "moss_block")
        C.set(x, -1, z, "dirt")
        C.set(x, -2, z, "dirt" if hash01(x, z, 102) < 0.7 else "stone")
        for y in range(1, 5):
            if C.get(x, y, z) is None:
                C.bp.set(x, y, z, AIR)
    # the skirt: grass and scree at the foot of L1 elsewhere (no air: the hill meets the terrain as it is)
    for (x, z), t in list(C.top.items()):
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, z + dz)
            if q in C.top or C.get(q[0], 0, q[1]) is not None:
                continue
            C.set(q[0], 0, q[1], "mossy_cobblestone" if hash01(*q, 103) < 0.3 else ("gravel" if hash01(*q, 104) < 0.5
                                                                                     else GRASS))
            C.set(q[0], -1, q[1], "stone")


def pond(C, cx, cz, rx, rz, y, seed, deep=2, lilies=0.06):
    """A koi pond: a noisy ellipse of water ``deep`` blocks deep with its surface at y, a clay and gravel bed, mossy
    stones on the rim, lily pads and a few lit sea pickles."""
    cells = set()
    for x in range(int(cx - rx) - 3, int(cx + rx) + 4):
        for z in range(int(cz - rz) - 3, int(cz + rz) + 4):
            e = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 + 0.5 * (fbm(x, z, 7.0, seed) - 0.5)
            if e <= 1.0:
                cells.add((x, z))
    for (x, z) in cells:
        for k in range(deep):
            C.water(x, y - k, z)
        h = hash01(x, z, seed + 1)
        C.set(x, y - deep, z, "clay" if h < 0.4 else ("gravel" if h < 0.75 else "sand"))
        C.set(x, y - deep - 1, z, "dirt")
        for yy in range(y + 1, y + 4):
            if C.get(x, yy, z) not in (None, AIR) and (x, yy, z) not in C.keep:
                C.bp.set(x, yy, z, AIR)
        if h > 1 - lilies and C.free(x, y + 1, z):
            C.put(x, y + 1, z, "lily_pad")
        elif h < 0.03:
            C.set(x, y - deep + 1, z, "sea_pickle[pickles=3,waterlogged=true]")
    for (x, z) in cells:
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, z + dz)
            if q in cells:
                continue
            # rim: solid at the water's level, a stone now and then
            for k in range(deep):
                if not C.solid(q[0], y - k, q[1]):
                    C.set(q[0], y - k, q[1], "mossy_cobblestone" if k == 0 else "dirt")
            if C.get(q[0], y, q[1]) in (None, "minecraft:air") or hash01(*q, seed + 2) < 0.12:
                C.set(q[0], y, q[1], "mossy_cobblestone" if hash01(*q, seed + 3) < 0.5 else AND_)
    return cells


def zigzag(C, pts, y, w=3):
    """A yatsuhashi bridge: straight plank decks of cherry slabs at y (bottom half) offset at every turn, posts down
    into the water at the joints."""
    hw = w // 2
    for i in range(len(pts) - 1):
        (ax, az), (bx, bz) = pts[i], pts[i + 1]
        xs = range(min(ax, bx) - (hw if ax == bx else 0), max(ax, bx) + (hw if ax == bx else 0) + 1)
        zs = range(min(az, bz) - (hw if az == bz else 0), max(az, bz) + (hw if az == bz else 0) + 1)
        for x in xs:
            for z in zs:
                C.set(x, y, z, slab(CH_SL))
                for hh in range(1, 4):
                    C.clear(x, y + hh, z)
                b = C.get(x, y - 1, z)
                if b is not None and "water" in b and (x in (xs[0], xs[-1]) and z in (zs[0], zs[-1])):
                    for yy in range(y - 1, y - 4, -1):
                        bb = C.get(x, yy, z)
                        if bb is None or "water" in bb:
                            C.set(x, yy, z, "stripped_cherry_log[axis=y]")
                        else:
                            break


def approach(C):
    """Camp -> moon gate -> lower koi pond and its zig-zag bridge -> forecourt -> grand stair up the L1 face."""
    # the lower koi pond first (the paths skip its water)
    pond(C, 0, 55, 27, 9, 0, 111)
    path(C, [(28, 88), (14, 87), (5, 82), (0, 75), (0, 67)], 0, 4, flag)
    path(C, [(0, 44), (0, 37)], 0, 7, flag)
    zigzag(C, [(0, 67), (0, 61), (6, 61), (6, 55), (-5, 55), (-5, 49), (0, 49), (0, 43)], 1)
    # forecourt: stone lanterns and a pair of cherries
    for s in (-1, 1):
        stone_lantern(C, s * 6, 1, 41, tall=True)
        for z in (78, 84):
            stone_lantern(C, s * 5 + (4 if z == 84 else 0), 1, z)
    # the side route along the foot of the hill to the west stair
    path(C, [(-4, 40), (-44, 40), (-58, 30), (-66, 12), (-66, 2)], 0, 3, gravel)
    # grand stair (5 wide) from the forecourt to L1
    climb(C, 0, 44, "north", 7, 1, 5)
    moon_gate(C)
    camp(C)


def moon_gate(C):
    """A white plaster wall across the garden with a round moon gate on the axis; the pagoda appears through it."""
    zw = 70
    cy, rr = 4.6, 4.3
    for x in range(-26, 27):
        ax = abs(x)
        for y in range(-1, 9):
            d = math.hypot(x, y - cy)
            if d <= rr:
                if y >= 1:
                    C.clear(x, y, zw)
                    C.clear(x, y, zw - 1)
                    C.clear(x, y, zw + 1)
                else:
                    C.set(x, y, zw, PAND)
                continue
            if y <= 0:
                spec = PAND if y == 0 else SB
            elif d <= rr + 1.0:
                spec = CH if hash01(x, y, 121) < 0.85 else "stripped_cherry_wood[axis=y]"
            elif y == 1:
                spec = AND_
            elif ax % 9 == 8:
                spec = POST
            else:
                spec = PL1 if hash3(x, y, zw, 122) < 0.75 else PL2
            C.set(x, y, zw, spec)
        # the tiled cap (both sides) and a ridge
        C.set(x, 9, zw, ROOF)
        C.set(x, 9, zw - 1, stair(ROOF_ST, "south"))
        C.set(x, 9, zw + 1, stair(ROOF_ST, "north"))
        C.set(x, 10, zw, slab(ROOF_SL))
    for s in (-1, 1):
        for y in range(0, 10):
            C.set(s * 27, y, zw, SB if y < 2 else POST)
        C.set(s * 27, 10, zw, BRASS)
        C.set(s * 27, 11, zw, ROD_U)
        cherry_tree(C, s * 31, 1, zw + 2, h=6, seed=3 + s)
    # the path passes under the ring: a pale threshold
    for x in range(-2, 3):
        C.set(x, 0, zw, PAND)


def camp(C):
    """The pilgrims' camp at the start of the approach: two tents, a fire, packs and the entrance waystone."""
    cx, cz = 30, 87
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 6, cz + 8):
            if (x, z) in C.top:
                continue
            C.set(x, 0, z, GRASS if hash01(x, z, 131) < 0.7 else "coarse_dirt")
            C.set(x, -1, z, "dirt")
            for y in range(1, 5):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)
    for (tx, tz, col) in ((cx - 6, cz - 4, "white"), (cx + 2, cz + 1, "pink")):
        for z in range(tz, tz + 5):
            C.set(tx, 1, z, "spruce_fence")
            C.set(tx + 4, 1, z, "spruce_fence")
            C.set(tx, 2, z, f"{col}_wool")
            C.set(tx + 4, 2, z, f"{col}_wool")
            for x in range(tx + 1, tx + 4):
                C.set(x, 3 if x != tx + 2 else 4, z, f"{col if z % 2 else 'light_gray'}_wool")
            C.set(tx + 1, 3, z, f"{col}_wool")
            C.set(tx + 3, 3, z, f"{col}_wool")
    C.bp.chest(cx - 5, 1, cz - 3, "east", loot=LOOT + "cp_camp")
    C.bp.barrel(cx + 5, 1, cz + 6)
    C.set(cx + 6, 1, cz + 6, "barrel[facing=up,open=false]")
    C.set(cx, 1, cz + 5, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (cx - 1, cx + 1):
        C.set(x, 1, cz + 6, stair("spruce_stairs", "south"))
    C.set(22, 1, 90, MOD["waystone"])
    C.set(22, 0, 90, PAND)
    stone_lantern(C, 20, 1, 92)


# ------------------------------------------------------------------ small buildings
def hip_roof(C, x0, z0, x1, z1, y, st, full, over=2, soffit=CH, tips=True, finial=GILD):
    """A hipped roof of stair rings stepping in one block per block of rise, from an eave ``over`` blocks outside
    the rectangle at y; soffit planks under the overhang, upturned brass-tipped corners, a ridge of full blocks."""
    i, yy = -over, y
    while True:
        ax0, az0, ax1, az1 = x0 + i, z0 + i, x1 - i, z1 - i
        if ax0 > ax1 or az0 > az1:
            break
        if ax0 == ax1 or az0 == az1:
            for x in range(ax0, ax1 + 1):
                for z in range(az0, az1 + 1):
                    C.set(x, yy, z, full)
            for (x, z) in ((ax0, az0), (ax1, az1)):
                C.set(x, yy + 1, z, finial)
            break
        for x in range(ax0, ax1 + 1):
            for z in range(az0, az1 + 1):
                if x not in (ax0, ax1) and z not in (az0, az1):
                    continue
                if z == az0:
                    f = "south"
                elif z == az1:
                    f = "north"
                elif x == ax0:
                    f = "east"
                else:
                    f = "west"
                C.set(x, yy, z, stair(st, f))
                if i < 0:
                    C.set(x, yy - 1, z, soffit)
        for x in range(ax0 + 1, ax1):
            for z in range(az0 + 1, az1):
                C.set(x, yy, z, full)                     # a solid core: no sealed void inside the roof
        if i == -over and tips:
            for (x, z) in ((ax0, az0), (ax0, az1), (ax1, az0), (ax1, az1)):
                C.set(x, yy, z, full)
                C.set(x, yy + 1, z, finial)
                C.set(x, yy - 1, z, GILD)
        i += 1
        yy += 1
    return yy


def frame_walls(C, x0, z0, x1, z1, y0, y1, plaster=True, posts_every=3, base=SB):
    """Cherry-framed walls round a rectangle: posts at corners and every few cells, a sill of stone, a head beam,
    white plaster (or open, when ``plaster`` is False) between."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x not in (x0, x1) and z not in (z0, z1):
                continue
            u = (x - x0) if z in (z0, z1) else (z - z0)
            corner = x in (x0, x1) and z in (z0, z1)
            for y in range(y0, y1 + 1):
                if corner or u % posts_every == 0:
                    spec = POST
                elif y == y0:
                    spec = base
                elif y == y1:
                    spec = BEAM_X if z in (z0, z1) else BEAM_Z
                elif plaster:
                    spec = PL1 if hash3(x, y, z, 141) < 0.8 else PL2
                else:
                    continue
                C.set(x, y, z, spec)


def foundation(C, x0, z0, x1, z1, ytop, spec=SB):
    """Masonry under a building's footprint down to the first solid block (or y -2)."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(ytop, -3, -1):
                if y < ytop and C.solid(x, y, z):
                    break
                C.set(x, y, z, spec if (x in (x0, x1) or z in (z0, z1)) else "stone")


def shrine(C):
    """The dragon shrine on the north terrace (L2): a stone podium, a cherry-and-plaster hall facing the pagoda with
    the clockwork dragon's heart on its altar, a red torii over the path, the purification basin, the hub's grace."""
    f = L2 + 2
    foundation(C, -7, -60, 7, -52, f - 1, PAND)
    for x in range(-7, 8):
        C.set(x, f - 1, -51, slab(PAND_SL))
        for hh in range(0, 3):
            C.clear(x, f + hh, -51) if C.free(x, f + hh, -51) else None
    frame_walls(C, -6, -59, 6, -53, f, f + 4)
    carve(C, -5, f, -58, 5, f + 3, -54)
    for x in range(-5, 6):
        for z in range(-58, -53):
            C.set(x, f - 1, z, "bamboo_planks" if (x + z) % 4 else "dark_oak_planks")
            C.set(x, f + 4, z, CH)
    # the open front: a three-bay screen of lattice doors folded back
    for x in range(-5, 6):
        for y in range(f, f + 4):
            C.clear(x, y, -53)
    for x in (-2, 2):
        for y in range(f, f + 4):
            C.set(x, y, -53, POST)
    hip_roof(C, -6, -59, 6, -53, f + 5, RED_ST, RED, over=2)
    # the altar: a gilded table, the dragon's heart-gear in a brass ring, candles, an offering chest
    for x in range(-3, 4):
        C.set(x, f, -58, GILD if abs(x) == 3 else BRASS)
    for (dx, dy) in ((-1, 1), (0, 1), (1, 1), (-1, 2), (1, 2), (-1, 3), (0, 3), (1, 3)):
        C.set(dx, f + dy, -58, GEAR)
    C.set(0, f + 2, -58, "ochre_froglight")
    for x in (-3, 3):
        candle(C, x, f + 1, -58, 4)
    C.bp.chest(-4, f, -57, "east", loot=LOOT + "cp_shrine")
    C.bp.barrel(4, f, -57)
    hang(C, 0, f + 3, -55, LANT_H)
    # the hub's site of grace beside the podium steps
    C.set(9, L2 + 1, -54, MOD["waystone"])
    stone_lantern(C, 9, L2 + 1, -51)
    # the torii over the path (posts outside the 5-wide walk)
    for s in (-1, 1):
        for y in range(L2 + 1, L2 + 8):
            C.set(s * 5, y, -48, f"{TORII}[axis=y]")
        C.set(s * 5, L2 + 1, -48, "polished_blackstone")
    for x in range(-7, 8):
        C.set(x, L2 + 8, -48, TORII_P if abs(x) < 7 else stair(SLATE_ST, "west" if x > 0 else "east"))
        C.set(x, L2 + 9, -48, slab(W + "slate_roof_tile_slab") if abs(x) < 6 else SLATE)
    for x in range(-5, 6):
        C.set(x, L2 + 6, -48, f"{TORII}[axis=x]")
    C.set(0, L2 + 7, -48, GILD)
    # purification basin under a little roof
    for (x, z) in ((-18, -58), (-14, -58), (-18, -55), (-14, -55)):
        for y in range(L2 + 1, L2 + 5):
            C.set(x, y, z, POST)
    hip_roof(C, -18, -58, -14, -55, L2 + 5, SLATE_ST, SLATE, over=1)
    for x in range(-17, -14):
        C.set(x, L2 + 1, -57, SB)
        C.set(x, L2 + 1, -56, "water_cauldron[level=3]")
    C.set(-16, L2 + 2, -57, "stripped_bamboo_block[axis=z]")


def bell_pavilion(C):
    """The bell pavilion on the east terrace: four posts on a stone platform under a crimson hipped roof; a great
    bronze bell with brass bands hangs from a beam, a striking log on chains beside it."""
    x0, z0, x1, z1 = 28, -24, 36, -16
    f = L2 + 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, L2, z, PAND if (x + z) % 2 else SB)
    for (px, pz) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
        for y in range(f, f + 7):
            C.set(px, y, pz, POST)
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            C.set(x, f + 7, z, BEAM_X)
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            C.set(x, f + 7, z, BEAM_Z)
    for x in range(x0, x1 + 1):
        C.set(x, f + 7, -20, BEAM_X)
    hip_roof(C, x0, z0, x1, z1, f + 8, RED_ST, RED, over=2)
    # the bell: a hollow bronze shell, rim at f + 2
    cx, cz = 32, -20
    prof = {f + 6: 1.0, f + 5: 1.6, f + 4: 2.0, f + 3: 2.3, f + 2: 2.7}
    for y, r in prof.items():
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.2:
                    C.set(x, y, z, BRASS if y in (f + 2, f + 5) else VERD)
    C.set(cx, f + 7, cz, CHAIN.replace("axis=y", "axis=y"))
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if math.hypot(x - cx, z - cz) <= 2.9:
                C.set(x, L2, z, PAND)
                C.set(x, f, z, PAND)
    # striking log on chains (east, over the walk)
    for y in (f + 4, f + 5, f + 6):
        C.set(35, y, cz, CHAIN)
        C.set(37, y, cz, CHAIN)
    for x in range(34, 39):
        C.set(x, f + 3, cz, "stripped_spruce_log[axis=x]")
    C.set(37, f + 7, cz, BEAM_X)
    C.set(38, f + 7, cz, BEAM_X)
    C.bp.chest(29, f, -23, "south", loot=LOOT + "cp_bell")
    stone_lantern(C, x0 - 1, f, z0 - 1)
    stone_lantern(C, x0 - 1, f, z1 + 1)


def dojo(C):
    """The monks' dojo on the west terrace (the guardians' hall the route crosses): stone base, cherry frame, white
    plaster, a polished floor with a padded sparring square, racks of practice weapons, training dummies."""
    x0, z0, x1, z1 = -39, -44, -29, -28
    f = L2 + 1
    foundation(C, x0, z0, x1, z1, L2, SB)
    frame_walls(C, x0, z0, x1, z1, f, f + 6, posts_every=4)
    carve(C, x0 + 1, f, z0 + 1, x1 - 1, f + 5, z1 - 1)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            spar = x0 + 3 <= x <= x1 - 3 and z0 + 5 <= z <= z1 - 5
            C.set(x, L2, z, W + "leather_padding" if spar else ("spruce_planks" if (z % 3) else CH))
            C.set(x, f + 6, z, CH if (x + z) % 4 else "stripped_cherry_wood[axis=y]")
    hip_roof(C, x0, z0, x1, z1, f + 7, SLATE_ST, SLATE, over=2)
    # doors (north and south, 3 wide) and windows
    for x in range(-35, -32):
        for (z, zo) in ((z0, z0 - 1), (z1, z1 + 1)):
            for y in range(f, f + 3):
                C.clear(x, y, z)
            C.set(x, L2, z, PAND)
    for z in range(z0 + 2, z1 - 1, 4):
        for y in (f + 2, f + 3):
            C.set(x0, y, z + 1, PANE)
            C.set(x1, y, z + 1, PANE)
    # racks: fence frames with staves (rods) along the walls; dummies; a dais with the master's mat
    for z in range(z0 + 2, z1 - 1, 3):
        C.set(x0 + 1, f, z, CH_FENCE)
        C.set(x0 + 1, f + 1, z, ROD_U)
        C.set(x0 + 1, f, z + 1, W + "wall_shelf[facing=east]")
    for z in (z0 + 3, z1 - 3):
        for x in (x1 - 2,):
            C.set(x, f, z, CH_FENCE)
            C.set(x, f + 1, z, "hay_block[axis=y]")
            C.set(x, f + 2, z, "carved_pumpkin[facing=west]")
    C.set(-34, f, z0 + 2, "red_carpet")
    C.set(-33, f, z0 + 2, "red_carpet")
    for x in (-37, -31):
        hang(C, x, f + 4, -40, LANT_H)
        hang(C, x, f + 4, -32, LANT_H)
    hang(C, -34, f + 3, -36, CHANDELIER)
    C.bp.chest(x0 + 1, f, z1 - 1, "east", loot=LOOT + "cp_dojo")
    C.bp.barrel(x1 - 1, f, z0 + 1)
    C.bp.spawner(-36, f, -36, MOB_MONK)
    C.bp.spawner(-31, f, -38, MOB_MONK)
    C.bp.spawner(-32, f, -33, MOB_KNIGHT)


def tea_house(C):
    """The tea house on L1 east beside the upper koi pond: a raised floor on a stone base, a veranda round it, shoji
    walls and a slate roof; tatami, a low table, a kettle, cushions."""
    x0, z0, x1, z1 = 44, -36, 52, -30
    f = L1 + 2
    foundation(C, x0 - 1, z0 - 1, x1 + 1, z1 + 1, f - 1, SB)
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            C.set(x, f - 1, z, CH if (x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)) else "bamboo_planks")
    frame_walls(C, x0, z0, x1, z1, f, f + 3, posts_every=2, base=CH)
    carve(C, x0 + 1, f, z0 + 1, x1 - 1, f + 2, z1 - 1)
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            C.set(x, f - 1, z, "bamboo_planks" if (x - x0) % 3 and (z - z0) % 3 else "dark_oak_planks")
            C.set(x, f + 3, z, CH)
    for x in range(x0 + 1, x1):
        if (x - x0) % 2:
            for y in (f + 1, f + 2):
                C.set(x, y, z0, PANE)
    # door (south) and a step down
    for y in range(f, f + 3):
        C.clear(48, y, z1)
        C.clear(48, y, z1 + 1)
    C.set(48, f - 1, z1 + 1, CH)
    C.set(48, f - 2, z1 + 2, CH)
    C.set(48, f - 1, z1 + 2, slab(CH_SL))
    C.set(47, f - 1, z1 + 2, SB)
    C.set(49, f - 1, z1 + 2, SB)
    hip_roof(C, x0, z0, x1, z1, f + 4, SLATE_ST, SLATE, over=2)
    C.set(48, f, -33, W + "mahogany_table")
    for (x, z) in ((47, -33), (49, -33), (48, -34)):
        carpet(C, x, f, z, "red")
    C.set(46, f, -35, "water_cauldron[level=3]")
    C.set(46, f + 1, -35, "potted_flowering_azalea_bush")
    C.set(51, f, -35, "flower_pot")
    C.bp.chest(51, f, -31, "west", loot=LOOT + "cp_garden")
    hang(C, 48, f + 2, -33, LANT_H)


def monks_garden(C):
    """L1 west: vegetable beds watered by a channel, a scarecrow, a bamboo grove hiding the hermit's grotto and a
    row of stone stupas."""
    y = L1
    for x in range(-53, -43):
        for z in range(-30, -17):
            if C.top.get((x, z)) != L1:
                continue
            if z == -24:
                C.water(x, y, z)
            elif x in (-53, -44) or z in (-30, -18):
                C.set(x, y, z, "coarse_dirt")
            else:
                C.set(x, y, z, "farmland[moisture=7]")
                crop = ("wheat[age=7]", "carrots[age=7]", "beetroots[age=3]", "potatoes[age=7]")[(z + 30) // 3 % 4]
                C.set(x, y + 1, z, crop)
    C.set(-48, y + 1, -30, "spruce_fence")
    C.set(-48, y + 2, -30, "hay_block[axis=y]")
    C.set(-48, y + 3, -30, "carved_pumpkin[facing=east]")
    C.set(-42, y + 1, -27, "composter[level=4]")
    C.bp.barrel(-42, y + 1, -26)
    # the grove
    for x in range(-52, -43):
        for z in range(-16, -6):
            if C.top.get((x, z)) != L1 or (x, y + 1, z) in C.keep:
                continue
            if hash01(x, z, 151) < 0.42:
                h = 6 + int(hash01(x, z, 152) * 6)
                C.set(x, y, z, "podzol[snowy=false]")
                for k in range(1, h + 1):
                    C.set(x, y + k, z, f"bamboo[age=1,leaves={'large' if k > h - 2 else ('small' if k > h - 4 else 'none')},stage=0]")
    # stupas
    for i, z in enumerate((-2, 2, 6)):
        x = -50
        if C.top.get((x, z)) == L1:
            C.set(x, y + 1, z, PAND)
            C.set(x, y + 2, z, "andesite_wall")
            C.set(x, y + 3, z, slab("andesite_slab"))
            candle(C, x + 1, y + 1, z, 2)


def grotto(C):
    """The hermit's grotto (a secret): a 2-high passage behind the bamboo into the L2 wall, a mossy cave with a brass
    seated sage, a spring, a bedroll and the hermit's chest."""
    f = L1 + 1
    for x in range(-44, -37):
        for y in (f, f + 1):
            C.clear(x, y, -12)
        C.set(x, f - 1, -12, "mossy_cobblestone")
        C.set(x, f + 2, -12, AND_) if x > -43 else None
    x0, z0, x1, z1 = -38, -15, -33, -9
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 1, f + 5):
                ins = x0 <= x <= x1 and z0 <= z <= z1
                if ins and f <= y <= f + 3:
                    C.clear(x, y, z)
                elif ins and y == f - 1:
                    C.set(x, y, z, "moss_block" if hash01(x, z, 161) < 0.5 else "mossy_cobblestone")
                else:
                    C.set(x, y, z, rock(x, y, z))
    for x in (-39, -38):
        C.clear(x, f, -12)
        C.clear(x, f + 1, -12)
        C.set(x, f - 1, -12, "mossy_cobblestone")
    for (x, z) in ((-33, -15), (-33, -14)):
        C.set(x, f, z, BRASS)
    C.set(-33, f, -12, BRASS)
    C.set(-33, f + 1, -12, ENGR)
    C.set(-33, f + 2, -12, "ochre_froglight")
    candle(C, -34, f, -13, 3)
    candle(C, -34, f, -11, 2)
    C.set(-37, f, -9, "water_cauldron[level=3]")
    carpet(C, -36, f, -14, "brown")
    carpet(C, -35, f, -14, "brown")
    C.bp.chest(-33, f, -10, "west", loot=LOOT + "cp_grotto")
    hang(C, -36, f + 2, -11, LANT_H)
    for (x, z) in ((-38, -15), (-38, -9), (-34, -9)):
        C.set(x, f + 3, z, "glow_lichen[down=false,east=false,north=false,south=false,up=true,west=false,waterlogged=false]")


def upper_pond(C):
    pond(C, 48, -14, 5, 4, L1, 171)
    zigzag(C, [(48, -7), (48, -11), (51, -11), (51, -16), (47, -16), (47, -21)], L1 + 1)
    for s in (-1, 1):
        stone_lantern(C, 48 + s * 4, L1 + 1, -7)


def terraces(C):
    """Stairs between the terraces, the walks on them and their lanterns."""
    climb(C, 0, 29, "north", 9, L1 + 1, 5)                       # L1 -> L2 (axis)
    land = climb(C, 0, 16, "north", 9, L2 + 1, 5)                # L2 -> L3 (axis, gated at the top)
    climb(C, -36, PZ, "east", 9, L2 + 1, 3)                      # L2 -> L3 west (main route)
    climb(C, -10, -56, "south", 9, L2 + 1, 3)                    # L2 -> L3 north (from the shrine)
    climb(C, 46, 5, "west", 9, L1 + 1, 3)                        # L1 -> L2 east (tea house side)
    climb(C, -46, 5, "east", 9, L1 + 1, 3)                       # L1 -> L2 west (monks' garden side)
    climb(C, -63, 2, "east", 7, 1, 3)      # ground -> L1 west (side route)
    # the axial gate: a karamon at the head of the L2 -> L3 stair; its iron door opens from the court
    zg = 5
    for x in range(-3, 4):
        for y in range(L3 + 1, L3 + 5):
            if x == 0 and y < L3 + 3:
                continue
            C.set(x, y, zg, POST if abs(x) == 3 else (PL1 if y < L3 + 4 else BEAM_X))
    C.bp.door(0, L3 + 1, zg, "south", wood="iron")
    lever(C, 1, L3 + 2, zg - 1, "north")
    hip_roof(C, -3, zg, 3, zg, L3 + 5, ROOF_ST, ROOF, over=1)
    for y in range(L3 + 1, L3 + 4):
        C.clear(0, y, zg - 1)
        C.clear(0, y, zg + 1)
    # walks
    path(C, [(0, 36), (0, 30)], L1, 5, flag)
    path(C, [(3, 33), (30, 31), (44, 19), (47, 8), (49, -6)], L1, 3, gravel)
    path(C, [(47, -22), (48, -28)], L1, 3, gravel)
    path(C, [(-3, 33), (-30, 31), (-44, 19), (-48, 6), (-55, 2)], L1, 3, gravel)
    path(C, [(-48, 6), (-47, -10), (-44, -12)], L1, 2, gravel)
    path(C, [(0, 19), (0, 18), (20, 17), (31, 9), (37, -4), (38, -36), (30, -48), (-22, -50), (-34, -46)], L2, 3,
         flag)
    path(C, [(-34, -27), (-37, -22), (-37, -18)], L2, 3, flag)
    path(C, [(-3, 18), (-24, 16), (-36, 6), (-38, -4), (-38, -17)], L2, 3, gravel)
    # lanterns along the axis and the walks
    for (x, z, y) in ((-4, 31, L1 + 1), (4, 31, L1 + 1), (-4, 22, L1 + 1), (4, 22, L1 + 1),
                      (-4, 18, L2 + 1), (4, 18, L2 + 1), (24, 14, L2 + 1), (35, 0, L2 + 1), (35, -40, L2 + 1),
                      (20, -46, L2 + 1), (-20, -46, L2 + 1), (-40, -24, L2 + 1), (-26, 13, L2 + 1)):
        if C.top.get((x, z)) == y - 1 and C.free(x, y, z) and (x, y, z) not in C.keep:
            stone_lantern(C, x, y, z)


# ------------------------------------------------------------------ the pagoda: shells, eaves, balconies
def posts_for(hw):
    n = max(1, int(round((hw - 3) / 5.5)))
    ps = {3, hw}
    for i in range(1, n):
        ps.add(int(round(3 + i * (hw - 3) / n)))
    return ps


BALCONY_DOOR = {2: "south", 3: "north", 4: "east", 5: "south", 6: "west", 7: "north", 8: "east"}


def wall_cell(x, z, hw):
    dz = z - PZ
    if abs(dz) == hw:
        return ("south" if dz > 0 else "north"), x
    return ("east" if x > 0 else "west"), dz


def wall_spec(j, face, u, y):
    t = T[j]
    hw, f, ceil = t["hw"], t["f"], t["ceil"]
    au = abs(u)
    hy, hmax = y - f, ceil - f
    beam = BEAM_X if face in ("north", "south") else BEAM_Z
    if au == hw or au in posts_for(hw):
        if j == 1 and hy == 0:
            return PAND
        return POST
    if hy == 0:
        return PAND if j == 1 else beam
    if hy == hmax - 1:
        return beam
    if j == 1 and hy == 6:
        return beam                                           # the mid rail (nageshi) of the tall hall
    if hy == 1 or (j == 1 and hy == 2):
        return AND_ if j == 1 and hy == 1 else CH             # wainscot
    if au <= 2:
        yc = f + (4 if j == 1 else hmax // 2)
        rr = 2.3 if j == 1 else (1.6 if hmax >= 6 else 1.2)
        d = math.hypot(u, y - yc)
        if d <= rr:
            return GRILLE
        if d <= rr + 0.9:
            return CH
    else:
        ps = sorted(posts_for(hw))
        lo = max(p for p in ps if p < au) if any(p < au for p in ps) else 0
        hi = min(p for p in ps if p > au)
        if lo + 1 < au < hi - 1:
            wy = (3, 5) if j == 1 else (2, max(2, hmax - 3))
            if wy[0] <= hy <= wy[1]:
                return PANE
            if j == 1 and 7 <= hy <= 9:
                return PANE
    return PL1 if hash3(face == "north", y, u, 181) < 0.78 else PL2


def tier_shell(C, j):
    t = T[j]
    hw, f, ceil, top = t["hw"], t["f"], t["ceil"], t["top"]
    for x in range(-hw, hw + 1):
        for z in range(PZ - hw, PZ + hw + 1):
            r = cheb(x, z)
            if j == 1:
                C.set(x, f - 1, z, CH)
            if r == hw:
                face, u = wall_cell(x, z, hw)
                for y in range(f, ceil):
                    C.set(x, y, z, wall_spec(j, face, u, y))
                C.set(x, ceil, z, BEAM_X if face in ("north", "south") else BEAM_Z)
                C.set(x, ceil + 1, z, CH)
                C.set(x, top, z, CH)
            else:
                for y in range(f, ceil):
                    C.clear(x, y, z)
                coffer = (x % 4 == 0) or ((z - PZ) % 4 == 0)
                C.set(x, ceil, z, "stripped_cherry_wood[axis=y]" if coffer else CH)
                C.set(x, ceil + 1, z, CH)
                C.set(x, top, z, CH)
    # the balcony door of this tier (a 3-wide opening in the centre bay of one face)
    face = BALCONY_DOOR.get(j)
    if face:
        dx, dz = DV[face]
        for u in (-1, 0, 1):
            x, z = (u, PZ + dz * hw) if face in ("north", "south") else (dx * hw, PZ + u)
            for y in range(f, f + 3):
                C.clear(x, y, z)
            ix, iz = x - dx, z - dz
            for y in range(f, f + 3):
                C.clear(ix, y, iz)
        for u in (-2, 2):
            x, z = (u, PZ + dz * hw) if face in ("north", "south") else (dx * hw, PZ + u)
            for y in range(f, f + 3):
                C.set(x, y, z, POST)
        for u in (-2, -1, 0, 1, 2):
            x, z = (u, PZ + dz * hw) if face in ("north", "south") else (dx * hw, PZ + u)
            C.set(x, f + 3, z, BEAM_X if face in ("north", "south") else BEAM_Z)


def roof_height(j, adx, adz):
    t = T[j]
    hw, top = t["hw"], t["top"]
    r, m = max(adx, adz), min(adx, adz)
    h = top - (r - (hw + 2)) * 0.67
    if m >= hw + 2:
        h += (m - (hw + 1)) * 0.55
    return int(round(h))


def eave(C, j):
    """The balcony of the tier above on top of this tier's wall, and this tier's flaring roof: four rows of slate
    stairs down to an eave lip four blocks out, upturned corners with brass hip tiles and tips, cherry soffits, and
    clockwork wind-chimes (a bell at each tip, chime rods along the lip)."""
    t = T[j]
    hw, top = t["hw"], t["top"]
    for x in range(-hw - 5, hw + 6):
        for z in range(PZ - hw - 5, PZ + hw + 6):
            adx, adz = abs(x), abs(z - PZ)
            r = max(adx, adz)
            if r <= hw or r > hw + 5:
                continue
            if r == hw + 1:
                C.set(x, top, z, CH if (x + z) % 2 else "stripped_cherry_wood[axis=y]")
                C.set(x, top - 1, z, stair(CH_ST, toward_centre(x, z), "top"))
                if j < 8:
                    railing(C, x, top + 1, z, OPP[toward_centre(x, z)])
                continue
            y = roof_height(j, adx, adz)
            base = top - (r - (hw + 2)) * 0.67
            hip = adx == adz
            if hip:
                C.set(x, y, z, stair(BTILE_ST, toward_centre(x, z)))
            else:
                C.set(x, y, z, stair(ROOF_ST, toward_centre(x, z)))
            # fill under raised corner cells, then the soffit / fascia
            yb = int(round(base))
            for yy in range(min(y - 1, yb), y):
                C.set(x, yy, z, ROOF)
            low = min(y, yb) - 1
            if r == hw + 5:
                C.set(x, low, z, GILD if min(adx, adz) >= hw + 3 else "stripped_cherry_wood[axis=y]")
            else:
                C.set(x, low, z, CH)
    # tips: a brass finial on each upturned corner, a bell hanging under it
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (hw + 5), PZ + sz * (hw + 5)
            y = roof_height(j, hw + 5, hw + 5)
            C.set(x, y, z, ENGR)
            C.set(x, y + 1, z, ROD_U)
            yb = min(y, int(round(top - 3 * 0.67))) - 1
            C.set(x, yb, z, GILD)
            C.set(x, yb - 1, z, CHAIN)
            C.set(x, yb - 2, z, BELL_C)
            # the clockwork: a little brass cog behind the bell
            C.set(x - sx, yb, z - sz, GILD)
    # chime rods hanging from the lip along each face
    lip = hw + 5
    for u in range(-(hw + 2), hw + 3):
        if u % 4 != 0 or abs(u) > hw + 1:
            continue
        for (x, z) in ((u, PZ - lip), (u, PZ + lip), (-lip, PZ + u), (lip, PZ + u)):
            y = roof_height(j, abs(x), abs(z - PZ))
            yb = min(y, int(round(top - 3 * 0.67))) - 2
            if C.free(x, yb, z):
                C.set(x, yb, z, CHAIN)
                C.set(x, yb - 1, z, ROD_D)


# ------------------------------------------------------------------ the pagoda: inner stairs
STAIRS = {1: (1, "north"), 2: (-1, "south"), 3: (1, "north"), 4: (-1, "south"), 5: (1, "north"), 6: (-1, "south"),
          7: (1, "south")}
BUSY = {j: set() for j in range(1, 9)}


def stair_layout(j):
    """(side, d, xs, z of the exit row, [(kind, block y)], [z per position]) of the stair from tier j to j + 1: three
    wide along the side wall of the tier above, climbing toward d; tier 1's has a landing half way."""
    side, d = STAIRS[j]
    t, tn = T[j], T[j + 1]
    hwn = tn["hw"]
    xs = [side * (hwn - 4), side * (hwn - 3), side * (hwn - 2)]
    dz = DV[d][1]
    ze = PZ - (hwn - 1) + 3 if dz < 0 else PZ + (hwn - 1) - 3
    pos = []
    if t["H"] > 13:
        n1 = 7
        pos += [("s", t["f"] + i) for i in range(n1)]
        pos += [("l", t["f"] + n1 - 1)] * 3
        pos += [("s", t["f"] + n1 + i) for i in range(t["H"] - 1 - n1)]
    else:
        pos = [("s", t["f"] + i) for i in range(t["H"] - 1)]
    zs = [ze - dz * (len(pos) - p) for p in range(len(pos))]
    return side, d, xs, ze, pos, zs


def run_stair(C, j, axis, d, lats, runs, pos, exit_run, approach_run, rails_lat, head_into):
    """Build a stair run in tier j: position p at run coordinate runs[p] (x when axis == "x", else z), three cells
    at lateral coordinates ``lats``; treads are cherry stairs facing d on a solid cherry mass. Where a tread's
    headroom would hit the ceiling the floor above is opened (a stairwell); railings guard the stairwell in the room
    above (lateral sides ``rails_lat`` and the far end) at y ``head_into``. Returns the opened run coordinates."""
    t = T[j]
    f, ceil, top = t["f"], t["ceil"], t["top"]

    def cell(r, l):
        return (r, l) if axis == "x" else (l, r)

    opened = []
    for p, (kind, y) in enumerate(pos):
        op = (y + 1) + 2 >= ceil
        for l in lats:
            x, z = cell(runs[p], l)
            C.set(x, y, z, stair(CH_ST, d) if kind == "s" else CH)
            post = l in (lats[0], lats[-1]) and p % 4 == 0
            for yy in range(f, y):
                if y - f <= 3 or yy == y - 1:
                    C.set(x, yy, z, CH)
                elif post:
                    C.set(x, yy, z, POST)
            for yy in range(y + 1, (top + 1) if op else min(y + 4, ceil)):
                C.clear(x, yy, z)
            BUSY[j].add((x, z))
            if j < 8:
                BUSY[j + 1].add((x, z))
        if op:
            opened.append(runs[p])
    for l in lats:
        x, z = cell(exit_run, l)
        C.set(x, top, z, stair(CH_ST, d))
        for yy in range(top + 1, top + 4):
            C.clear(x, yy, z)
        if j < 8:
            BUSY[j + 1].add((x, z))
        x, z = cell(approach_run, l)
        for yy in range(f, f + 3):
            C.clear(x, yy, z)
        BUSY[j].add((x, z))
    # railings round the stairwell
    dr = 1 if runs[-1] > runs[0] else -1
    for r in opened:
        for (lr, fac) in rails_lat:
            x, z = cell(r, lr)
            railing(C, x, head_into, z, fac)
            if j < 8:
                BUSY[j + 1].add((x, z))
    if opened:
        r_end = opened[0] - dr
        fac = d
        for l in lats:
            x, z = cell(r_end, l)
            railing(C, x, head_into, z, fac)
            if j < 8:
                BUSY[j + 1].add((x, z))
    return opened


def tier_stair(C, j):
    side, d, xs, ze, pos, zs = stair_layout(j)
    hwn = T[j + 1]["hw"]
    dz = DV[d][1]
    inner = side * (hwn - 5)
    outer = side * (hwn - 1)
    rails = [(inner, "east" if side > 0 else "west"), (outer, "west" if side > 0 else "east")]
    run_stair(C, j, "z", d, xs, zs, pos, ze, zs[0] - dz, rails, T[j + 1]["f"])
    # a railing on the inner edge of the high treads (in the tread cells, thin)
    for p, (kind, y) in enumerate(pos):
        if y >= T[j]["f"] + 3:
            railing(C, xs[0], y + 1, zs[p], "west" if side > 0 else "east")


def arena_stairs(C):
    """Tier 8: the stair up to the deck (mist at its head) and the vault stair (sealed bars at its head)."""
    t = T[8]
    f = t["f"]
    pos = [("s", f + i) for i in range(7)]
    lats = [PZ + 8, PZ + 9, PZ + 10]
    run_stair(C, 8, "x", "west", lats, [3 - p for p in range(7)], pos, -4, 4,
              [(PZ + 7, "south"), (PZ + 11, "north")], FA)
    C.bp.mist(-4, FA, PZ + 8, -4, FA + 2, PZ + 10)
    lats = [PZ - 10, PZ - 9, PZ - 8]
    run_stair(C, 8, "x", "east", lats, [-3 + p for p in range(7)], pos, 4, -4,
              [(PZ - 11, "south"), (PZ - 7, "north")], FA)
    for z in lats:
        for y in range(FA, FA + 3):
            C.set(4, y, z, MOD["vault_bars"])


# ------------------------------------------------------------------ the central pillar and its counterweight lift
def pillar_skin(u, v, y):
    j = next((k for k in range(1, 9) if T[k]["f"] - 1 <= y <= T[k]["top"]), 1)
    t = T[j]
    if abs(u) == 3 and abs(v) == 3:
        return POST
    if y < t["f"] or y >= t["ceil"]:
        return CH
    if y == t["f"]:
        return BEAM_X if abs(v) == 3 else BEAM_Z
    if y == t["ceil"] - 1:
        return GILD
    if (u == 0 or v == 0) and t["f"] + 2 <= y <= t["f"] + 3:
        return GRILLE
    return PL1 if hash3(u, y, v, 191) < 0.8 else PL2


def pillar(C):
    """The central pillar, 7 x 7, from the pool under the prayer hall to the ceiling of tier 8. Inside: the drop well
    (west), an iron cage, the counterweight on its chains (east) and the bubble tube (south-east) in a glass sleeve.
    The tube is fed from the pool: swim under the glass to rise; jump into the well from tier 8 to fall into the
    pool."""
    yb, yt = 25, T[8]["ceil"]
    top8 = T[8]["top"]
    for u in range(-3, 4):
        for v in range(-3, 4):
            x, z = u, PZ + v
            edge = abs(u) == 3 or abs(v) == 3
            for y in range(yb, yt + 1):
                if edge:
                    C.set(x, y, z, pillar_skin(u, v, y) if y >= T[1]["f"] else SB)
                elif y >= 29:
                    C.clear(x, y, z)
            C.set(x, yt, z, CH)
            C.set(x, yt + 1, z, CH)
            C.set(x, top8, z, CH)
    for j in range(1, 9):
        for x in range(-4, 5):
            for z in range(PZ - 4, PZ + 5):
                BUSY[j].add((x, z))
    # the pool (west half) and the solid bed east of it
    for u in range(-2, 3):
        for v in range(-2, 3):
            C.set(u, 25, PZ + v, SB)
            for y in (26, 27, 28):
                if u < 0:
                    C.water(u, y, PZ + v)
                else:
                    C.set(u, y, PZ + v, SB)
    # the tube at (1, 2): soul sand, bubbles to the top, fed by a channel under (0, 2)
    C.set(1, 25, PZ + 2, "soul_sand")
    for y in range(26, top8 - 7):
        C.water(1, y, PZ + 2, "bubble_column[drag=false]")
    for y in (26, 27):
        C.water(0, y, PZ + 2)
    for (u, v) in ((0, 1), (0, 2), (2, 2), (1, 1), (2, 1)):
        for y in range(26, top8 - 7):
            if (u, v) == (0, 2) and y < 28:
                continue
            C.set(u, y, PZ + v, "glass" if y >= 29 else SB)
    # the iron cage between the well and the machinery
    for v in (-2, -1, 0):
        for y in range(29, top8 - 8):
            C.set(0, y, PZ + v, "iron_bars")
    # the counterweight: chains from the underside of the top landing, a dark iron weight with brass bands
    for u in (1, 2):
        for v in (-2, -1, 0):
            for y in range(60, 65):
                C.set(u, y, PZ + v, BRASS if y in (60, 64) else IRON)
        for y in range(65, top8 - 8):
            C.set(u, y, PZ - 1, CHAIN)
        for y in range(30, 60):
            C.set(u, y, PZ - 1, CHAIN) if u == 1 else None
        C.set(u, 29, PZ - 1, COPPER)
    # lamps down the shaft (on the cage side of the walls)
    for y in range(34, top8 - 8, 9):
        C.set(-2, y, PZ - 3, EDISON) if C.get(-2, y, PZ - 3) not in (None,) else None
    # tier 8: the landing over the shaft, the well's mouth open, the door north into the vault
    y8 = top8 - 8                      # 99: floor of tier 8
    for u in range(-2, 3):
        for v in range(-2, 3):
            if u < 0 and v >= 0:
                C.clear(u, y8, PZ + v)              # the well's mouth
            elif (u, v) in ((0, 1), (0, 2), (2, 2), (1, 1), (2, 1)):
                C.set(u, y8, PZ + v, "glass")
            elif (u, v) == (1, 2):
                pass
            else:
                C.set(u, y8, PZ + v, CH if (u + v) % 2 else "stripped_cherry_wood[axis=y]")
            for y in range(y8 + 1, yt):
                C.clear(u, y, PZ + v)
    for u in (-1, 0, 1):
        for y in range(y8 + 1, y8 + 4):
            C.clear(u, y, PZ - 3)
    railing(C, 0, y8 + 1, PZ + 1, "west")
    railing(C, 0, y8 + 1, PZ + 2, "west")
    hang(C, 1, y8 + 3, PZ - 1, LANT_H)


def lift_lobby(C):
    """The lift lobby of the prayer hall, against the south face of the pillar: the pool's exit and the tube's
    mouth inside; its iron door opens only from within (the lever is inside), so the lift is a way back, not in."""
    f = T[1]["f"]
    for x in range(-4, 5):
        for z in range(PZ + 3, PZ + 8):
            edge = abs(x) == 4 or z == PZ + 7
            for y in range(f, f + 4):
                if z == PZ + 3:
                    continue
                if edge:
                    C.set(x, y, z, POST if (abs(x) == 4 and z in (PZ + 3, PZ + 7)) or (z == PZ + 7 and x == 0 and
                                                                                     False) else
                          (CH if y == f else (PL1 if y < f + 3 else BEAM_X)))
                else:
                    C.clear(x, y, z)
            C.set(x, f + 4, z, CH if not edge else BEAM_X)
            C.set(x, f - 1, z, PAND if not edge else CH)
            if edge:
                railing(C, x, f + 5, z, "south" if z == PZ + 7 else ("east" if x > 0 else "west"))
    # pool exit through the pillar's south wall (x -2..-1)
    for x in (-2, -1):
        for y in (f, f + 1):
            C.clear(x, y, PZ + 3)
        C.set(x, f - 1, PZ + 3, PAND)
    C.bp.door(0, f, PZ + 7, "south", wood="iron")
    lever(C, -1, f + 1, PZ + 6, "north")
    C.set(1, f + 2, PZ + 6, EDISON)
    hang(C, 2, f + 2, PZ + 5, LANT_H)
    C.set(3, f, PZ + 4, "cherry_sign[rotation=8,waterlogged=false]")
    for x in range(-4, 5):
        for z in range(PZ + 3, PZ + 9):
            BUSY[1].add((x, z))


# ------------------------------------------------------------------ the open top tier: deck, roof, spire
def deck(C):
    t = T[8]
    top = t["top"]
    for x in range(-DECK, DECK + 1):
        for z in range(PZ - DECK, PZ + DECK + 1):
            r = cheb(x, z)
            b = C.get(x, top, z) or ""
            if b == "minecraft:air" or ("stairs" in b and r < 12):
                continue                                     # the stairwells and their last treads
            if r <= 2:
                spec = BTILE
            elif r == 8 or r == 15:
                spec = BTILE
            elif (x + z) % 2:
                spec = PAND
            else:
                spec = "smooth_stone"
            if r <= 2 and (x == 0 or z == PZ):
                spec = GILD
            C.set(x, top, z, spec)
            if r >= 12:
                C.set(x, top - 1, z, "stripped_cherry_wood[axis=y]" if r == DECK else CH)
                if r == 12:
                    C.set(x, top - 2, z, stair(CH_ST, toward_centre(x, z), "top"))
                if r == DECK:
                    C.set(x, top - 1, z, GILD)
                    railing(C, x, top + 1, z, OPP[toward_centre(x, z)])
            for y in range(top + 1 + (1 if r == DECK else 0), ROOF9):
                C.clear(x, y, z)
    C.bp.boss_seal(0, top, PZ, BOSS, 16)
    # chimes under the deck corners
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * DECK, PZ + sz * DECK
            C.set(x, top - 2, z, CHAIN)
            C.set(x, top - 3, z, BELL_C)
    # the four posts of the ninth roof and the lintels between them
    for sx in (-1, 1):
        for sz in (-1, 1):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    x, z = sx * POSTS + dx, PZ + sz * POSTS + dz
                    for y in range(FA, ROOF9):
                        spec = POST
                        if y == FA:
                            spec = PAND
                        elif (y - FA) % 4 == 3:
                            spec = GILD
                        C.set(x, y, z, spec)
    for x in range(-DECK - 2, DECK + 3):
        for z in range(PZ - DECK - 2, PZ + DECK + 3):
            r = cheb(x, z)
            if r == POSTS and not (abs(x) >= POSTS - 1 and abs(z - PZ) >= POSTS - 1):
                C.set(x, ROOF9 - 2, z, BEAM_X if abs(z - PZ) == POSTS else BEAM_Z)
                C.set(x, ROOF9 - 1, z, CH)
    # lamps from the ceiling
    for (x, z) in ((-6, PZ - 6), (6, PZ - 6), (-6, PZ + 6), (6, PZ + 6)):
        hang(C, x, ROOF9 - 5, z, CHANDELIER)


def roof9_height(adx, adz):
    r, m = max(adx, adz), min(adx, adz)
    h = ROOF9 + (18 - r) * 0.42
    if m >= 14:
        h += (m - 13) * 0.6
    return int(round(h))


def top_roof(C):
    """The ninth roof: a coffered ceiling over the arena, slate rows rising from a lip 18 out, brass hips, upturned
    corners with bells; then the spire: a brass base, nine rings on a mast, a jewel."""
    for x in range(-18, 19):
        for z in range(PZ - 18, PZ + 19):
            adx, adz = abs(x), abs(z - PZ)
            r = max(adx, adz)
            y = roof9_height(adx, adz)
            if r <= 12:
                coffer = x % 3 == 0 or (z - PZ) % 3 == 0
                spec = GEAR if r <= 2 else ("stripped_cherry_wood[axis=y]" if coffer else CH)
                C.set(x, ROOF9, z, spec)
            else:
                C.set(x, ROOF9, z, GILD if r == 18 else CH)
            for yy in range(ROOF9 + 1, y):
                C.set(x, yy, z, ROOF)
            if r <= 2:
                C.set(x, y, z, BRASS)
            elif adx == adz:
                C.set(x, y, z, stair(BTILE_ST, toward_centre(x, z)))
            else:
                C.set(x, y, z, stair(ROOF_ST, toward_centre(x, z)))
    C.set(0, ROOF9, PZ, "gold_block")
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 18, PZ + sz * 18
            y = roof9_height(18, 18)
            C.set(x, y, z, ENGR)
            C.set(x, y + 1, z, ROD_U)
            C.set(x, ROOF9 - 1, z, CHAIN)
            C.set(x, ROOF9 - 2, z, BELL_C)
    # the spire
    yb = roof9_height(2, 2)
    for x in range(-2, 3):
        for z in range(PZ - 2, PZ + 3):
            for y in range(yb, yb + 3):
                C.set(x, y, z, GILD if (abs(x) == 2 or abs(z - PZ) == 2) and y == yb + 2 else BRASS)
    ym = yb + 3
    for k in range(9):
        y = ym + 2 * k
        rr = 2.2 - k * 0.13
        for x in range(-3, 4):
            for z in range(PZ - 3, PZ + 4):
                if math.hypot(x, z - PZ) <= rr:
                    C.set(x, y, z, BTILE if k % 2 == 0 else GILD)
        C.set(0, y + 1, PZ, BRASS)
    yj = ym + 18
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(dx, yj, PZ + dz, stair(BTILE_ST, OPP[toward_centre(dx, PZ + dz)], "top"))
    C.set(0, yj, PZ, "gold_block")
    C.set(0, yj + 1, PZ, "glowstone")
    C.set(0, yj + 2, PZ, ROD_U)


# ------------------------------------------------------------------ the rooms of the tiers
def reserve_doors():
    """Keep the approach of every balcony door (and the prayer hall's doors) clear of furniture."""
    for j, face in BALCONY_DOOR.items():
        hw = T[j]["hw"]
        dx, dz = DV[face]
        for u in range(-2, 3):
            for k in range(1, 4):
                if face in ("north", "south"):
                    BUSY[j].add((u, PZ + dz * (hw - k)))
                else:
                    BUSY[j].add((dx * (hw - k), PZ + u))
    for x in range(-3, 4):
        for z in range(-6, -2):
            BUSY[1].add((x, z))
    for x in range(14, 18):
        for z in range(-12, -8):
            BUSY[1].add((x, z))


def inside(j, x, z, m=1):
    return cheb(x, z) <= T[j]["hw"] - m


def fp(C, j, x, y, z, spec):
    """Furniture: only inside tier j, off its stairs, stairwells, pillar and door approaches."""
    if inside(j, x, z) and (x, z) not in BUSY[j]:
        C.set(x, y, z, spec)
        return True
    return False


def prayer_hall(C):
    """Tier 1: the prayer hall. A colonnade of red-lacquered columns, a long carpet from the south portal to the
    altar of the clockwork dragon (a brass dragon head over a gear mandala), rows of prayer mats, incense."""
    j, t = 1, T[1]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    # the south portal: a tall opening in the centre bay, a karamon porch over it
    for x in range(-2, 3):
        for y in range(f, f + 6):
            C.clear(x, y, PZ + hw)
        C.set(x, f - 1, PZ + hw, PAND)
        C.set(x, f + 6, PZ + hw, GILD if x == 0 else BEAM_X)
    for x in (-3, 3):
        for y in range(f, f + 6):
            C.set(x, y, PZ + hw, "stripped_mangrove_log[axis=y]")
    for x in (-4, 4):
        for z in (PZ + hw + 1, PZ + hw + 3):
            for y in range(f, f + 8):
                C.set(x, y, z, "stripped_mangrove_log[axis=y]")
            C.set(x, f - 1, z, PAND)
    hip_roof(C, -4, PZ + hw + 1, 4, PZ + hw + 3, f + 8, ROOF_ST, ROOF, over=1)
    for x in range(-3, 4):
        for z in range(PZ + hw + 1, PZ + hw + 4):
            C.set(x, f - 1, z, PAND if (x + z) % 2 else "smooth_stone")
            for y in range(f, f + 8):
                C.clear(x, y, z)
    hang(C, 0, f + 5, PZ + hw + 2, LANT_H)
    # the colonnade: 2 x 2 red columns with brass capitals
    cols = [(sx * 9, PZ + dz) for sx in (-1, 1) for dz in (-11, 0, 11)]
    for (cx, cz) in cols:
        for dx in (0, 1 if cx > 0 else -1):
            for dz in (0, 1):
                x, z = cx + dx, cz + dz
                if (x, z) in BUSY[1]:
                    continue
                C.set(x, f - 1, z, PAND)
                for y in range(f, ceil):
                    spec = "stripped_mangrove_log[axis=y]"
                    if y == f:
                        spec = PAND
                    elif y >= ceil - 2:
                        spec = GILD if y == ceil - 1 else BRASS
                    C.set(x, y, z, spec)
    # the floor: polished cherry, a red runner from the portal to the altar
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[1] and cheb(x, z) <= 4:
                continue
            if C.get(x, f - 1, z) == "minecraft:" + CH or C.get(x, f - 1, z) == CH:
                C.set(x, f - 1, z, "stripped_cherry_wood[axis=y]" if (x % 6 == 0 or (z - PZ) % 6 == 0) else CH)
    for z in range(PZ + 8, PZ + hw):
        for x in (-1, 0, 1):
            fp(C, 1, x, f, z, "red_carpet")
    for z in range(PZ - hw + 5, PZ - 4):
        for x in (-1, 0, 1):
            fp(C, 1, x, f, z, "red_carpet")
    # prayer mats in rows either side of the runner (south half and north half)
    for z in list(range(PZ + 9, PZ + 15, 2)) + list(range(PZ - 12, PZ - 6, 2)):
        for x in list(range(-7, -2, 2)) + list(range(3, 8, 2)):
            fp(C, 1, x, f, z, "white_carpet" if (x + z) % 4 else "pink_carpet")
    # the altar: a stepped dais on the north wall, a brass dragon head over a gear mandala, candles, incense
    zA = PZ - hw + 1
    for x in range(-5, 6):
        for z in range(zA, zA + 4):
            C.set(x, f, z, PAND if z < zA + 3 else slab(PAND_SL))
            if z < zA + 2:
                C.set(x, f + 1, z, slab(PAND_SL) if z == zA + 1 else PAND)
    for x in range(-4, 5):
        for y in range(f + 2, f + 9):
            d = math.hypot(x, y - (f + 5))
            if d <= 3.6:
                C.set(x, y, zA - 1 + 1, GEAR if d > 2.4 else (BRASS if d > 1.2 else "ochre_froglight"))
    # the dragon head: snout, jaw, horns of rods, eyes
    hx, hy, hz = 0, f + 5, zA + 1
    for (dx, dy, dz, spec) in ((0, 0, 0, BRASS), (-1, 0, 0, BRASS), (1, 0, 0, BRASS), (0, 1, 0, BTILE),
                               (0, -1, 1, stair(BTILE_ST, "north", "top")), (0, 0, 1, stair(BTILE_ST, "south")),
                               (-1, 1, 0, "redstone_lamp[lit=true]"), (1, 1, 0, "redstone_lamp[lit=true]"),
                               (-2, 2, 0, ROD_U), (2, 2, 0, ROD_U), (0, 0, 2, ROD_D.replace("down", "south"))):
        C.set(hx + dx, hy + dy, hz + dz, spec)
    for x in (-4, 4):
        candle(C, x, f + 2, zA, 4)
        candle(C, x, f + 1, zA + 2, 3, "white")
    for x in (-2, 2):
        C.set(x, f + 2, zA + 1, "campfire[lit=false,facing=south,signal_fire=false,waterlogged=false]")
    C.bp.chest(5, f + 1, zA, "south", loot=LOOT + "cp_hall")
    # offering boxes and the monk-guardians
    for x in (-7, 7):
        fp(C, 1, x, f, zA + 2, "cherry_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    C.bp.spawner(-13, f, -30, MOB_MONK)
    C.bp.spawner(6, f, -24 + 12, MOB_MONK)
    # the east door onto the court (an iron door that opens from inside) and its lever
    C.bp.door(hw, f, -10, "east", wood="iron")
    lever(C, hw - 1, f + 1, -11, "west")
    # lamps: chandeliers down the nave, lanterns at the columns
    for z in (PZ - 10, PZ + 11):
        hang(C, 0, ceil - 3, z, CHANDELIER, reach=4)
    for (cx, cz) in cols:
        x = cx + (-1 if cx > 0 else 1)
        if (x, cz) not in BUSY[1]:
            hang(C, x, ceil - 3, cz, LANT_H, reach=4)
    # a gallery feel: brass grilles in the nageshi band, banners of the seasons between the windows
    for z in (PZ - 8, PZ + 8):
        for x in (-hw + 1, hw - 1):
            if (x, z) not in BUSY[1]:
                C.set(x, f + 7, z, "pink_wall_banner[facing=" + ("east" if x < 0 else "west") + "]")


def library(C):
    """Tier 2: the scroll library. Stacks of bookshelves in ranks east-west, scroll shelves on the walls, reading
    desks with lecterns under the windows, a reading circle by the balcony."""
    j, t = 2, T[2]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) not in BUSY[2] and inside(2, x, z):
                C.set(x, f - 1, z, "dark_oak_planks" if (x + z) % 5 == 0 else "spruce_planks")
    # the stacks (north half): ranks of shelves 3 high, a wall-shelf of scrolls on the ends
    for z in range(PZ - hw + 3, PZ - 5, 3):
        for x in list(range(-10, -5)) + list(range(5, 11)):
            if (x, z) in BUSY[2]:
                continue
            for y in range(f, f + 3):
                fp(C, 2, x, y, z, "chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=false,"
                                  "slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,"
                                  "slot_5_occupied=false]" if (x + y) % 3 == 0 else "bookshelf")
            fp(C, 2, x, f + 3, z, slab(CH_SL))
    # scroll shelves on the walls (between the windows)
    for u in range(-hw + 2, hw - 1):
        for (x, z, fac) in ((u, PZ - hw + 1, "south"), (-hw + 1, PZ + u, "east"), (hw - 1, PZ + u, "west")):
            if u % 4 == 1:
                fp(C, 2, x, f + 1, z, f"{W}wall_shelf[facing={fac}]")
    # reading desks (south half) with lecterns and lamps
    for (x, z) in ((5, PZ + 8), (9, PZ + 8), (5, PZ + 12), (9, PZ + 12), (-5, PZ + 12), (-9, PZ + 12)):
        if fp(C, 2, x, f, z, TABLE):
            fp(C, 2, x, f + 1, z, "candle[candles=2,lit=true,waterlogged=false]")
            fp(C, 2, x, f, z + 1, f"{W}mahogany_chair[facing=north]")
    for (x, z) in ((-7, PZ + 7), (7, PZ + 15)):
        fp(C, 2, x, f, z, "lectern[facing=south,has_book=true,powered=false]")
    # the reading circle by the balcony door: cushions round a brazier of brass
    for (x, z) in ((-3, PZ + 10), (3, PZ + 10), (0, PZ + 8), (0, PZ + 12)):
        fp(C, 2, x, f, z, "cyan_carpet")
    fp(C, 2, 0, f, PZ + 10, W + "brass_tile_slab[type=bottom,waterlogged=false]")
    fp(C, 2, 0, f + 1, PZ + 10, "candle[candles=4,lit=true,waterlogged=false]")
    C.bp.chest(-hw + 1, f, PZ - hw + 2, "east", loot=LOOT + "cp_library")
    C.bp.chest(hw - 4, f, PZ + hw - 1, "north", loot=LOOT + "cp_library")
    C.bp.barrel(-hw + 1, f, PZ + hw - 1)
    C.bp.spawner(-8, f, PZ - 8, MOB_WISP)
    for (x, z) in ((-8, PZ - 12), (8, PZ - 12), (-8, PZ + 10), (8, PZ + 10)):
        hang(C, x, ceil - 2, z, LANT_H, reach=4)


def armoury(C):
    """Tier 3: the armoury of practice weapons. A padded sparring floor, racks of wooden staves and blunt spears
    (fences and rods), straw dummies, archery targets, a smithy corner (grindstone, anvil, smithing table)."""
    j, t = 3, T[3]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[3] or not inside(3, x, z):
                continue
            spar = abs(x) <= 8 and PZ + 6 <= z <= PZ + 13
            C.set(x, f - 1, z, W + "leather_padding" if spar else ("spruce_planks" if (x + z) % 2 else CH))
    for x in range(-9, 10):
        for z in (PZ + 5, PZ + 14):
            fp(C, 3, x, f - 1, z, "stripped_cherry_wood[axis=y]")
    # racks along the north wall and the east wall: fence frames holding staves
    for u in range(-hw + 2, hw - 1):
        if u % 3 == 0:
            continue
        for (x, z) in ((u, PZ - hw + 1),):
            if fp(C, 3, x, f, z, CH_FENCE):
                fp(C, 3, x, f + 1, z, ROD_U if u % 3 == 1 else "end_rod[facing=up]")
                fp(C, 3, x, f + 2, z, CH_FENCE)
    for z in range(PZ - 6, PZ + 4, 2):
        x = -hw + 1
        if fp(C, 3, x, f, z, f"{W}wall_shelf[facing=east]"):
            fp(C, 3, x, f + 1, z, f"{W}wall_shelf[facing=east]")
    # dummies and targets
    for (x, z) in ((-6, PZ - 9), (-3, PZ - 9), (3, PZ - 10)):
        if fp(C, 3, x, f, z, CH_FENCE):
            fp(C, 3, x, f + 1, z, "hay_block[axis=y]")
            fp(C, 3, x, f + 2, z, "carved_pumpkin[facing=south]")
    for x in (-6, -4, 4, 6):
        fp(C, 3, x, f, PZ + hw - 1, "target[power=0]")
        fp(C, 3, x, f + 1, PZ + hw - 1, "target[power=0]")
    # the smithy corner (south-west, off the arrival stair's lane)
    fp(C, 3, -hw + 2, f, PZ + 3, "grindstone[face=floor,facing=east]")
    fp(C, 3, -hw + 2, f, PZ + 1, "anvil[facing=north]")
    fp(C, 3, -hw + 2, f, PZ - 1, "smithing_table")
    fp(C, 3, -hw + 2, f, PZ - 3, "blast_furnace[facing=east,lit=false]")
    # the master's dais in the sparring square: a gong (bell on a frame)
    for x in (-1, 1):
        for y in range(f, f + 4):
            fp(C, 3, x, y, PZ + hw - 2, CH_FENCE)
    fp(C, 3, 0, f + 3, PZ + hw - 2, BEAM_X)
    fp(C, 3, 0, f + 2, PZ + hw - 2, BELL_C)
    C.bp.chest(hw - 1, f, PZ + 6, "west", loot=LOOT + "cp_armoury")
    C.bp.barrel(hw - 1, f, PZ + 8)
    C.bp.spawner(0, f, PZ + 9, MOB_KNIGHT)
    C.bp.spawner(-8, f, PZ - 10, MOB_MONK)
    for (x, z) in ((-8, PZ - 8), (8, PZ - 8), (-6, PZ + 9), (6, PZ + 9)):
        hang(C, x, ceil - 2, z, LANT_H, reach=4)


def meditation(C):
    """Tier 4: the meditation hall round a raked sand garden. White sand raked in rings round the pillar, three
    mossy boulders, cushions round the edge, incense; the site of grace in the north-west corner."""
    j, t = 4, T[4]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[4] and cheb(x, z) <= 4:
                continue
            if not inside(4, x, z) or (x, z) in BUSY[4]:
                continue
            d = math.hypot(x, z - PZ)
            if abs(x) <= 9 and abs(z - PZ) <= 9:
                spec = "white_concrete_powder" if int(d) % 2 else "sand"
                if abs(x) == 9 or abs(z - PZ) == 9:
                    spec = "stripped_cherry_wood[axis=y]"
            else:
                spec = "bamboo_planks" if (x + z) % 3 else "stripped_bamboo_block[axis=x]"
            C.set(x, f - 1, z, spec)
    for (x, z, h) in ((-6, PZ - 6, 2), (6, PZ + 5, 1), (-5, PZ + 6, 1)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1)):
            for y in range(f, f + h):
                fp(C, 4, x + dx, y, z + dz, "mossy_cobblestone" if (dx + y) % 2 else "andesite")
        fp(C, 4, x, f + h, z, "moss_carpet")
    # cushions round the garden (facing in), incense
    for u in range(-7, 8, 3):
        for (x, z) in ((u, PZ - 11), (u, PZ + 11), (-11, PZ + u), (11, PZ + u)):
            fp(C, 4, x, f, z, "orange_carpet" if u % 2 else "brown_carpet")
    for (x, z) in ((-11, PZ - 11), (11, PZ - 11), (-11, PZ + 11), (11, PZ + 11)):
        if fp(C, 4, x, f, z, "potted_bamboo"):
            pass
    fp(C, 4, 0, f, PZ - hw + 1, PAND)
    fp(C, 4, 0, f + 1, PZ - hw + 1, "candle[candles=3,lit=true,waterlogged=false]")
    # the site of grace
    C.set(-10, f, PZ - 12, MOD["waystone"])
    fp(C, 4, -12, f, PZ - 12, "potted_cherry_sapling")
    C.bp.chest(hw - 1, f, PZ - hw + 1, "west", loot=LOOT + "cp_meditation")
    for (x, z) in ((-7, PZ - 7), (7, PZ - 7), (-7, PZ + 7), (7, PZ + 7)):
        hang(C, x, ceil - 2, z, LANT_H, reach=4)


SEASONS = (("pink", CH_LEAF), ("lime", "moss_block"), ("orange", "orange_terracotta"), ("light_blue", "packed_ice"))


def orrery(C):
    """Tier 5: the mechanical orrery of the seasons. A brass ring round the pillar on gilded arms, four season
    globes (blossom, moss, autumn, ice) hanging from it over floor quadrants of their colours, a gilded sun on the
    pillar, wall cogs and gauges driving it."""
    j, t = 5, T[5]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    yr = f + 5
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[5] or not inside(5, x, z):
                continue
            q = (0 if z < PZ else 2) + (0 if x < 0 else 1)
            q = (0, 1, 3, 2)[q]
            col = SEASONS[q][0]
            C.set(x, f - 1, z, f"{col}_terracotta" if (x + z) % 2 or (x * z) % 3 else "smooth_stone")
    # the ring and its arms
    for x in range(-8, 9):
        for z in range(PZ - 8, PZ + 9):
            d = math.hypot(x, z - PZ)
            if 6.0 <= d <= 7.1:
                C.set(x, yr, z, BTILE if (x + z) % 3 else GILD)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(4, 7):
            C.set(dx * k, yr, PZ + dz * k, GILD)
    # the globes (at the diagonals, under the ring)
    for q, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        col, mat = SEASONS[q]
        gx, gz = sx * 5, PZ + sz * 5
        C.set(gx, yr, gz, GILD)
        for (dx, dy, dz) in ((0, -1, 0), (0, -2, 0), (1, -2, 0), (-1, -2, 0), (0, -2, 1), (0, -2, -1)):
            C.set(gx + dx, yr + dy, gz + dz, mat)
        C.set(gx, yr - 2, gz, "glowstone" if q != 3 else "sea_lantern")
    # the sun on the pillar: a gilded disc on each face
    for v in (-3, 3):
        for u in (-1, 0, 1):
            for y in (f + 2, f + 3, f + 4):
                C.set(u, y, PZ + v, GILD if (u, y) != (0, f + 3) else "ochre_froglight")
    for u in (-3, 3):
        for v in (-1, 0, 1):
            for y in (f + 2, f + 3, f + 4):
                C.set(u, y, PZ + v, GILD if (v, y) != (0, f + 3) else "ochre_froglight")
    # wall cogs and gauges
    for u in range(-hw + 2, hw - 1, 3):
        for (x, z, fac) in ((u, PZ - hw + 1, "south"), (-hw + 1, PZ + u, "east"), (hw - 1, PZ + u, "west"),
                            (u, PZ + hw - 1, "north")):
            fp(C, 5, x, f + 3, z, f"{W}wall_cog[facing={fac}]")
    for (x, z) in ((-hw + 1, PZ - hw + 1), (hw - 1, PZ + hw - 1)):
        fp(C, 5, x, f, z, PIPES)
        fp(C, 5, x, f + 1, z, GAUGE)
    fp(C, 5, -9, f, PZ + 10, TABLE)
    C.bp.chest(-hw + 1, f, PZ + 9, "east", loot=LOOT + "cp_orrery")
    C.bp.spawner(-8, f, PZ - 9, MOB_SPIDER)
    for (x, z) in ((-9, PZ - 9), (9, PZ + 9), (-9, PZ + 9)):
        hang(C, x, ceil - 1, z, LANT_H, reach=3)


def abbot(C):
    """Tier 6: the abbot's quarters. A sleeping corner behind folding screens, a study with a desk and scroll
    shelves, a tea table on tatami, a little house shrine, the abbot's closet (his chest)."""
    j, t = 6, T[6]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[6] or not inside(6, x, z):
                continue
            tat = (x // 2 + (z - PZ) // 3) % 2
            C.set(x, f - 1, z, "bamboo_planks" if tat else "stripped_bamboo_block[axis=x]")
    # screens (north-east sleeping corner): cherry trapdoor panels on fences
    for x in range(5, 12):
        fp(C, 6, x, f, PZ - 5, "white_stained_glass_pane") if x % 2 else fp(C, 6, x, f, PZ - 5, CH_FENCE)
        fp(C, 6, x, f + 1, PZ - 5, "white_stained_glass_pane") if x % 2 else fp(C, 6, x, f + 1, PZ - 5, CH_FENCE)
    C.bp.bed(9, f, PZ - 10, "north", color="white") if hasattr(C.bp, "bed") else None
    fp(C, 6, 11, f, PZ - 11, "potted_flowering_azalea_bush")
    fp(C, 6, 7, f, PZ - 11, TABLE)
    fp(C, 6, 7, f + 1, PZ - 11, "candle[candles=1,lit=true,waterlogged=false]")
    # the study (north-west): desk, lectern, scroll shelves
    for x in range(-11, -5):
        fp(C, 6, x, f, PZ - hw + 1, "bookshelf")
        fp(C, 6, x, f + 1, PZ - hw + 1, f"{W}wall_shelf[facing=south]")
    fp(C, 6, -8, f, PZ - 9, TABLE)
    fp(C, 6, -7, f, PZ - 9, TABLE)
    fp(C, 6, -8, f + 1, PZ - 9, "lantern[hanging=false,waterlogged=false]")
    fp(C, 6, -8, f, PZ - 8, f"{W}mahogany_chair[facing=north]")
    fp(C, 6, -11, f, PZ - 7, "lectern[facing=east,has_book=true,powered=false]")
    # the tea room (south-east): low table, cushions, kettle on a brazier
    fp(C, 6, 7, f, PZ + 8, TABLE)
    for (x, z) in ((6, PZ + 8), (8, PZ + 8), (7, PZ + 7), (7, PZ + 9)):
        fp(C, 6, x, f, z, "red_carpet")
    fp(C, 6, 10, f, PZ + 10, "campfire[lit=false,facing=north,signal_fire=false,waterlogged=false]")
    fp(C, 6, 10, f + 1, PZ + 10, "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # the house shrine (south wall, west) and the closet with his chest
    fp(C, 6, -6, f, PZ + hw - 1, GILD)
    fp(C, 6, -6, f + 1, PZ + hw - 1, GEAR)
    fp(C, 6, -5, f, PZ + hw - 1, "candle[candles=3,lit=true,waterlogged=false]")
    fp(C, 6, -7, f, PZ + hw - 1, "candle[candles=2,lit=true,waterlogged=false]")
    for z in range(PZ + 8, PZ + 13):
        fp(C, 6, -11, f, z, CH)
        fp(C, 6, -11, f + 1, z, CH)
    C.bp.chest(-12, f, PZ + 10, "east", loot=LOOT + "cp_abbot")
    C.bp.barrel(-12, f, PZ + 12)
    C.bp.spawner(0, f, PZ + 8, MOB_WISP)
    for (x, z) in ((-7, PZ - 7), (7, PZ - 7), (7, PZ + 7), (-6, PZ + 7)):
        hang(C, x, ceil - 1, z, LANT_H, reach=3)


def chime_engine(C):
    """Tier 7: the chime engine. A great cog on the pillar's faces, drive shafts along the ceiling to each wall
    (the chime rods outside hang from them), bells hung in rows, pipes and gauges, a bellows of copper."""
    j, t = 7, T[7]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[7] or not inside(7, x, z):
                continue
            C.set(x, f - 1, z, W + "diamond_plate" if (x + z) % 4 == 0 else "spruce_planks")
    # gear discs on the pillar's four faces
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for a in range(-2, 3):
            for y in range(f + 1, f + 6):
                d = math.hypot(a, y - (f + 3))
                if d <= 2.6:
                    x, z = (dx * 3, PZ + a) if dx else (a, PZ + dz * 3)
                    C.set(x, y, z, GEAR if d > 1.2 else BRASS)
    # shafts along the ceiling from the pillar to each wall
    for k in range(4, hw):
        for (x, z, ax) in ((k, PZ, "x"), (-k, PZ, "x"), (0, PZ + k, "z"), (0, PZ - k, "z")):
            if (x, z) in BUSY[7] and cheb(x, z) > 4:
                continue
            C.set(x, ceil - 1, z, f"iron_chain[axis={ax},waterlogged=false]")
            if k % 3 == 0:
                C.set(x, ceil - 1, z, GILD)
    # bells in rows (from the ceiling), with striker rods beside them
    for (x, z) in ((-6, PZ - 8), (-3, PZ - 8), (3, PZ - 8), (6, PZ - 8), (-8, PZ + 6), (8, PZ + 6), (-5, PZ + 9),
                   (5, PZ + 9)):
        if (x, z) in BUSY[7]:
            continue
        C.set(x, ceil - 1, z, CHAIN)
        C.set(x, ceil - 2, z, BELL_C)
    # pipes and gauges on the walls, a copper bellows
    for u in range(-hw + 2, hw - 1, 4):
        for (x, z) in ((-hw + 1, PZ + u), (hw - 1, PZ + u)):
            for y in range(f, ceil):
                fp(C, 7, x, y, z, PIPES)
            fp(C, 7, x, f + 1, z, GAUGE)
    for (x, z) in ((-8, PZ - 10), (-7, PZ - 10), (-8, PZ - 9)):
        fp(C, 7, x, f, z, COPPER)
    fp(C, 7, -7, f + 1, PZ - 10, W + "valve_wheel[facing=south]")
    C.bp.chest(hw - 1, f, PZ - hw + 1 + 1, "west", loot=LOOT + "cp_chimes")
    C.bp.spawner(-6, f, PZ + 8, MOB_DRONE)
    C.bp.spawner(5, f, PZ - 6, MOB_SPIDER)
    for (x, z) in ((-8, PZ), (8, PZ - 6), (0, PZ + 8), (0, PZ - 8)):
        hang(C, x, ceil - 2, z, LANT_H, reach=3)


def stair_hall(C):
    """Tier 8: the last stair hall (site of grace) south of a plaster divider; the vault north of it, reached only
    from the deck (its stair behind sealed bars) and opening onto the lift well."""
    j, t = 8, T[8]
    f, ceil, hw = t["f"], t["ceil"], t["hw"]
    for x in range(-hw + 1, hw):
        for z in range(PZ - hw + 1, PZ + hw):
            if (x, z) in BUSY[8] or not inside(8, x, z):
                continue
            vault = z < PZ - 3
            C.set(x, f - 1, z, (BTILE if (x + z) % 2 else GILD) if vault else
                  ("smooth_stone" if (x + z) % 2 else PAND))
    # the divider (z = PZ - 2 on both sides of the pillar, and round the pillar's side to z = PZ - 3)
    for x in list(range(-hw + 1, -3)) + list(range(4, hw)):
        for y in range(f, ceil):
            C.set(x, y, PZ - 3, POST if x in (-hw + 1, -4, 4, hw - 1, -7, 7) else
                  (BEAM_X if y in (f, ceil - 1) else PL1))
    # the hall: the waystone, lamps
    C.set(-8, f, PZ + 5, MOD["waystone"])
    for (x, z) in ((-7, PZ + 2), (7, PZ + 2), (-1, PZ + 6)):
        hang(C, x, ceil - 1, z, LANT_H, reach=3)
    fp(C, 8, -10, f, PZ + 2, "potted_cherry_sapling")
    # the vault: chests on gilded plinths, gold, a reliquary
    C.bp.chest(-8, f, PZ - 6, "south", loot=LOOT + "cp_vault")
    C.bp.chest(8, f, PZ - 6, "south", loot=LOOT + "cp_vault")
    C.bp.chest(-8, f, PZ - 9, "south", loot=LOOT + "cp_vault")
    for (x, z) in ((-6, PZ - 6), (6, PZ - 6), (8, PZ - 8)):
        fp(C, 8, x, f, z, "gold_block" if x < 0 else "raw_gold_block")
    fp(C, 8, 6, f + 1, PZ - 6, "candle[candles=4,lit=true,waterlogged=false]")
    for (x, z) in ((-6, PZ - 5), (6, PZ - 9)):
        hang(C, x, ceil - 1, z, CHANDELIER, reach=3)


# ------------------------------------------------------------------ the clockwork dragon's skeleton
def catmull(pts, step=0.4):
    """Points along a Catmull-Rom spline through ``pts`` roughly ``step`` apart."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = math.dist(p1, p2)
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in range(3)))
    out.append(tuple(pts[-1]))
    return out


def dragon_ok(C, x, y, z):
    if 42 <= y <= 101 and cheb(x, z) <= 20:
        return False
    for k in (1, 2, 3):
        b = C.get(x, y - k, z) or ""
        if "stairs" in b or "slab" in b or "railing" in b:
            return False
    return C.free(x, y, z) and (x, y, z) not in C.keep


def dragon_skull(C):
    """The skull lies on the north terrace before the shrine, its jaw agape toward the torii (west): a brass
    cranium with empty sockets (a dim glow inside), rod fangs, swept-back horns."""
    y0 = L2 + 1
    for x in range(13, 24):
        for z in range(-60, -51):
            for y in range(y0, y0 + 7):
                dz = z + 56
                if x >= 18:                                       # cranium: an ellipsoid shell
                    e = ((x - 20.5) / 3.6) ** 2 + (dz / 3.4) ** 2 + ((y - (y0 + 3)) / 3.0) ** 2
                    if e <= 1.0:
                        C.put(x, y, z, BRASS if hash3(x, y, z, 501) < 0.8 else VERD)
                else:                                             # upper snout and lower jaw
                    if abs(dz) <= 2 and y in (y0 + 3, y0 + 4) and (y == y0 + 3 or abs(dz) <= 1):
                        C.put(x, y, z, BTILE if y == y0 + 4 else BRASS)
                    if abs(dz) <= 2 and y == y0 and x >= 14 and (abs(dz) == 2 or x >= 17):
                        C.put(x, y, z, BRASS)
    # fangs, sockets, nostrils, horns
    for x in range(13, 18):
        for dz in (-2, 2):
            C.put(x, y0 + 2, -56 + dz, ROD_D) if x % 2 else None
            C.put(x, y0 + 1, -56 + dz, ROD_U) if x % 2 == 0 else None
    for dz in (-2, 2):
        C.set(18, y0 + 4, -56 + dz, AIR)
        C.set(19, y0 + 4, -56 + dz, "ochre_froglight")
    C.set(13, y0 + 4, -55, AIR)
    C.set(13, y0 + 4, -57, AIR)
    for s in (-1, 1):
        for k in range(5):
            C.put(22 + k, y0 + 5 + k // 2, -56 + s * (2 + k // 2), ENGR if k < 4 else ROD_U)
    # the heart-gear socket: a gilded ring under the cranium
    for x in range(19, 23):
        C.put(x, y0 - 0, -56, GILD) if C.free(x, y0, -56) else None


def dragon(C):
    """The spine: from the skull up the neck and round the pagoda, two and a half coils climbing from y 37 to 71 on
    a near-square superellipse 24 out (clear of every eave lip); vertebrae of brass, ribs of gear plate, dorsal
    spikes, and gilded claws that grip the eaves where the coil passes them."""
    dragon_skull(C)
    pts = [(22, L2 + 4, -56), (25, L2 + 7, -56), (27, L2 + 12, -53), (27, L2 + 16, -48)]
    a0, a1 = -45.0, -570.0
    n = 54
    for k in range(1, n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        c, s = math.cos(a), math.sin(a)
        p = 10.0
        rr = 24.0 / ((abs(c) ** p + abs(s) ** p) ** (1.0 / p))
        y = 37 + (71 - 37) * k / n
        pts.append((rr * c, y, PZ + rr * s))
    spine = catmull(pts)
    total = len(spine)
    claws = 0
    last_rib = -99
    acc = 0.0
    for i, (px, py, pz) in enumerate(spine):
        frac = i / total
        rad = 2.4 - 1.7 * frac
        # tangent and frame
        q = spine[min(total - 1, i + 1)]
        o = spine[max(0, i - 1)]
        tx, ty, tz = q[0] - o[0], q[1] - o[1], q[2] - o[2]
        tl = math.sqrt(tx * tx + ty * ty + tz * tz) or 1.0
        tx, ty, tz = tx / tl, ty / tl, tz / tl
        sx, sz = -tz, tx                                          # side = t x up (horizontal)
        sl = math.hypot(sx, sz) or 1.0
        sx, sz = sx / sl, sz / sl
        # vertebra core
        X, Y, Z = int(round(px)), int(round(py)), int(round(pz))
        if dragon_ok(C, X, Y, Z):
            C.put(X, Y, Z, ENGR if i % 6 < 2 else BRASS)
        if i > 0:
            acc += math.dist(spine[i], spine[i - 1])
        if acc - last_rib >= 2.6:
            last_rib = acc
            # a rib: an arc over the top and down both sides (open below)
            for deg in range(-110, 111, 12):
                th = math.radians(deg)
                rx = px + rad * (math.sin(th) * sx)
                ry = py + rad * math.cos(th) * 0.9
                rz = pz + rad * (math.sin(th) * sz)
                X, Y, Z = int(round(rx)), int(round(ry)), int(round(rz))
                if dragon_ok(C, X, Y, Z):
                    C.put(X, Y, Z, GEAR if abs(deg) < 80 else VERD)
            X, Y, Z = int(round(px)), int(round(py + rad + 0.8)), int(round(pz))
            if dragon_ok(C, X, Y, Z):
                C.put(X, Y, Z, ROD_U)
            # claws: every few ribs on the coil, a gilded strut inward to the pagoda (stops at the first solid)
            if py > 38 and int(acc / 2.6) % 9 == 4:
                ax, az = -px, PZ - pz
                al = math.hypot(ax, az) or 1.0
                ax, az = ax / al, az / al
                for k in range(1, 9):
                    X, Y, Z = int(round(px + ax * k)), int(round(py - 1 - k * 0.35)), int(round(pz + az * k))
                    if not dragon_ok(C, X, Y, Z):
                        break
                    C.put(X, Y, Z, GILD)
                claws += 1
    # the tail: a brass blade at the end
    px, py, pz = spine[-1]
    for k in range(1, 4):
        X, Y, Z = int(round(px)) - k, int(round(py)), int(round(pz)) - (k // 2)
        if dragon_ok(C, X, Y, Z):
            C.put(X, Y, Z, stair(BTILE_ST, "west") if k == 3 else GILD)


# ------------------------------------------------------------------ cherry trees
def trees(C):
    """Cherry trees on the terraces and the garden where there is room (off the paths, buildings and stairs)."""
    placed = []
    for x in range(-62, 63, 3):
        for z in range(-84, 98, 3):
            jx = x + int(hash01(x, z, 601) * 3) - 1
            jz = z + int(hash01(x, z, 602) * 3) - 1
            if hash01(jx, jz, 603) > 0.34:
                continue
            t = C.top.get((jx, jz))
            if t is None:
                gx0, gz0, gx1, gz1 = GARDEN
                if C.get(jx, 0, jz) not in ("minecraft:grass_block", GRASS) and not (
                        C.get(jx, 0, jz) or "").startswith("minecraft:grass_block"):
                    continue
                t = 0
            elif t not in (L1, L2):
                continue
            if any(abs(jx - a) + abs(jz - b) < 7 for (a, b) in placed):
                continue
            ok = True
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    b = C.get(jx + dx, t, jz + dz) or ""
                    if not b.startswith("minecraft:grass_block") and not b.startswith("grass_block"):
                        ok = False
                    for y in range(t + 1, t + 8):
                        if (jx + dx, y, jz + dz) in C.keep or not C.free(jx + dx, y, jz + dz):
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                continue
            if t == L2 and cheb(jx, jz) < 30:
                continue
            placed.append((jx, jz))
            cherry_tree(C, jx, t + 1, jz, h=4 + int(hash01(jx, jz, 604) * 3), seed=len(placed),
                        spread=3 + int(hash01(jx, jz, 605) * 2))


# ------------------------------------------------------------------ the builder
def cloud_pagoda(bp):
    C = Ctx(bp)
    for j in range(1, 9):
        BUSY[j].clear()
    massif(C)
    ground(C)
    approach(C)
    upper_pond(C)
    terraces(C)
    parapets(C)
    shrine(C)
    bell_pavilion(C)
    dojo(C)
    tea_house(C)
    monks_garden(C)
    grotto(C)
    # the pagoda
    for j in range(1, 9):
        tier_shell(C, j)
    for j in range(1, 8):
        eave(C, j)
    pillar(C)
    lift_lobby(C)
    for j in range(1, 8):
        tier_stair(C, j)
    arena_stairs(C)
    deck(C)
    top_roof(C)
    reserve_doors()
    prayer_hall(C)
    library(C)
    armoury(C)
    meditation(C)
    orrery(C)
    abbot(C)
    chime_engine(C)
    stair_hall(C)
    dragon(C)
    trees(C)


VIEWS = [
    ("prayer_hall", (12, 29, -26), (-3, 33, -37)),
    ("scroll_library", (-2, 43, -7), (-10, 45, -30)),
    ("armoury", (10, 53, -6), (-8, 54, -12)),
    ("meditation_hall", (8, 63, -33), (-8, 62, -26)),
    ("orrery", (11, 73, -8), (-6, 77, -13)),
    ("abbots_quarters", (-2, 82, -30), (10, 83, -30)),
    ("boss_arena", (0, 108, -5), (0, 112, -20)),
]

register(StructureDef(
    "cloud_pagoda", "overworld", ["cherry_grove", "meadow"],
    [Piece("pagoda", cloud_pagoda, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_MONK, 6, 1, 2), (MOB_KNIGHT, 3, 1, 1), (MOB_WISP, 3, 1, 1)],
    title_fr="La Pagode des nuages", title_en="The Cloud Pagoda"))

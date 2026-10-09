"""The Brass Caravanserai (Le Caravansérail de laiton): a walled trading city ~230 blocks across on a caravan route in
desert or savanna, crowned by the ribbed brass-and-azure dome of its great bazaar. Colossal tier (tools/BUILDING.md §1,
§12 concept 36, §10 legacy-dungeon template, §15), steampunk accents (tools/STYLE_STEAMPUNK.md: brass sand-crawlers,
minaret chimneys venting the cistern pumps, brass clockwork in the palace, a money-changer's lift shaft).

Silhouette (one noun phrase, §15.1): a sand-gold walled city of drum towers whose skyline is one great pointed dome of
azure tiles and brass ribs, flanked by four smoking minaret chimneys, with giant brass sand-crawlers parked and wrecked
outside its walls.

Layout, ground y = 0 (feet 1), x east, z south. The great dome's axis is (0, BCZ = -16).
  * outside the walls (south): the caravan camp and its waystone (east), a road that runs behind a parked brass
    sand-crawler (it hides the gate) and turns round its nose to the gatehouse: the pishtaq frames the dome (the
    reveal). A wrecked crawler rammed into the south-west wall made a breach (the side route, over its deck);
  * the gatehouse: a great brass gate with a wicket, the toll tunnel (compression) into the Caravan Court (the hub,
    waystone): two storeys of arcades round a fountain kiosk, lodgings, coffee house, stores; stair halls to the upper
    gallery; the north gate is barred from the bazaar side (a shortcut back);
  * branches: west to the camel and crawler stables (stalls, hay loft, the crawler garage with its gantry); east into
    the covered souk (three vaulted alleys of stalls and a domed crossroads, the dyers' yard and its stair to the wall
    walk, the spice warehouse lane); the lanes of houses in every quarter (wind-catchers, roof parapets);
  * the main route: the souk's west alley enters the Great Bazaar by its east iwan: the ambulatory of stalls round the
    sunken auction pit (seen through iron grilles, the boss arena), the corner newel stairs to the roof terrace, the
    gallery inside the drum (vista down into the pit), the north roof and the Prince's Bridge on arches over the
    garden to the palace roof; the palace library and observatory, the Divan's east gallery and its stair down to the
    hall of the merchant prince (garden waystone outside), the Garden of Four Rivers and its fountain, the well-head
    stair down into the cistern undercroft (columns, water channels), the conduit south to the lot hall under the
    bazaar (site of grace), the auctioneers' stair, the mist;
  * the boss: the auction pit under the dome (35 wide, tiers, 80 blocks of headroom); behind sealed bars in its south
    wall, the merchant prince's treasury; its ladder shaft rises to the money-changer's booth in the ambulatory
    (iron door, lever inside);
  * shortcuts (§10.4): the treasury shaft; the porters' stair from the cistern ring to the ambulatory (iron door, lever
    on the stair side); the garden gate to the bazaar's north iwan (lever on the garden side); the court's north gate
    (lever on the bazaar side). Optional: the stables, the souk's side lanes, the dyers' yard and the wall walk, the
    climbable minaret (balcony vista), the hammam, the apartments, the crawlers' cabins and holds, the houses.
Loot gradient (§15.6): camp, houses, souk 1; court, stables, crawlers 1-2; bazaar, warehouse, dyers 2; palace rooms,
cistern 2-3; minaret balcony 3; the treasury 3-5.
Height budget: the dome's finial stands 90 above the ground layer.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, PIPES, SMOKE, TABLE, TREAD, TREAD_SLAB,
                       TREAD_STAIRS, VERD, W, fbm, hash01, hash3, out_facing, vnoise)
from ..parts import LOOT, MOD
from .airship_graveyard import Frame, raster
from .caldera_ringwall import newel

# the champion of the auction pit: the Brass Merchant Prince (tools/BOSSES.md)
BOSS = "brasshaven:merchant_prince"
MOB_BANDIT = W + "bandit_marksman"
MOB_RAIDER = W + "sky_raider"
MOB_SCARAB = W + "sun_scarab"
MOB_MITE = W + "rust_mite"
MOB_DRONE = W + "steam_drone"
MOB_SPIDER = W + "clockwork_spider"
MOB_GUNNER = W + "boiler_gunner"
MOB_CRAWLER = W + "crypt_crawler"
MOB_HUSK = "minecraft:husk"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
GB, GB_ST, GB_SL, GB_WALL = W + "guild_bricks", W + "guild_brick_stairs", W + "guild_brick_slab", W + "guild_brick_wall"
MGB, CGB = W + "mossy_guild_bricks", W + "cracked_guild_bricks"
PGS, PGS_ST, PGS_SL = W + "polished_guild_stone", W + "polished_guild_stone_stairs", W + "polished_guild_stone_slab"
CGS, GTILE = W + "carved_guild_stone", W + "guild_tiles"
AZ, AZ_ST, AZ_SL = W + "guild_roof_tiles", W + "guild_roof_tile_stairs", W + "guild_roof_tile_slab"
TERRA, TERRA_ST, TERRA_SL = W + "crimson_roof_tiles", W + "crimson_roof_tile_stairs", W + "crimson_roof_tile_slab"
BTILE, BTILE_ST, BTILE_SL = W + "brass_tiles", W + "brass_tile_stairs", W + "brass_tile_slab"
CTILE = W + "copper_tiles"
ENGR, GRILLE, GILD = W + "engraved_brass", W + "brass_grille", W + "gilded_trim"
DIB, DIB_ST, DIB_SL = W + "dark_iron_bricks", W + "dark_iron_brick_stairs", W + "dark_iron_brick_slab"
PARQ = W + "mahogany_parquet"
MARBLE, PMARBLE = W + "marble", W + "polished_marble"
RAIL, VALVE, COG, SHELF, CHAIR = (W + "brass_railing", W + "valve_wheel", W + "wall_cog", W + "wall_shelf",
                                  W + "mahogany_chair")
PIPE_Y = W + "copper_pipe[axis=y]"
MUD, MUD_ST, MUD_SL, MUD_WALL = "mud_bricks", "mud_brick_stairs", "mud_brick_slab", "mud_brick_wall"
PMUD = "packed_mud"
SST, SST_ST, SST_SL = "smooth_sandstone", "smooth_sandstone_stairs", "smooth_sandstone_slab"
CUT_SS = "cut_sandstone"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
BARS = "iron_bars"
GLASS = "glass"
PANE = "glass_pane"
SEA = "sea_lantern"
BUBBLE = "bubble_column[drag=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
PALM_LEAF = "jungle_leaves[distance=1,persistent=true,waterlogged=false]"
PALM_LOG = "jungle_log[axis=y]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
CARPETS = ("red", "orange", "yellow", "light_blue", "cyan", "brown", "magenta", "purple")

# ------------------------------------------------------------------ the plan
# the city wall: a closed polygon (vertices), the gate at its south vertex
WALL = [(0, 98), (44, 95), (84, 76), (100, 36), (102, -20), (88, -70), (52, -102), (0, -112), (-52, -102),
        (-88, -70), (-102, -20), (-100, 36), (-84, 76), (-44, 95)]
WALL_T = 4                     # wall thickness (inside the polygon)
WALK = 14                      # wall-walk floor block y (feet 15)
BREACH = (-68, 84)             # where the wrecked crawler rammed the south-west wall
BCZ = -16                      # the great dome's axis z (x = 0)
BH = 32                        # bazaar base half size (walls at |u|, |v| = 31 .. 32)
ROOF_B = 24                    # bazaar roof terrace floor y (feet 25)
PIT_F = -9                     # auction pit floor block y (feet -8)
CIS_F = -12                    # cistern walkway floor y (feet -11)
CAMP = (106, 110)
AIR_TOP = 4                    # explicit air only up to here (higher interiors stay unset: natural air)
COURT = (-32, 24, 32, 82)      # caravan court outer walls x0, z0, x1, z1
GARDEN = (-30, -81, 30, -54)   # garden walls
PAL_Z1 = -82                   # palace front (south) wall
SOUK_A = (51, 54)              # alley A z range (x 33 .. 61)
SOUK_B = (66, 69)              # alley B x range (z -13 .. 45)
SOUK_C = (-17, -14)            # alley C z range (x 33 .. 69)
CROSS = (62, 46, 75, 59)       # the domed crossroads
MINARETS = [(-38, 22), (38, 22), (-38, -54), (38, -54)]


def rng(a, b):
    return range(min(a, b), max(a, b) + 1)


class Ctx:
    """Blueprint wrapper: ``keep`` holds reserved air (walkways, headroom) that decoration (``put``) never fills."""

    def __init__(self, bp):
        self.bp = bp
        self.keep = set()
        self.city = set()      # columns inside the wall polygon
        self.ground = set()    # columns of the site's own ground layer
        self.busy = set()      # columns taken by buildings (streets, palms and lamps avoid them)

    def set(self, x, y, z, spec, data=None):
        self.bp.set(x, y, z, spec, data)
        self.keep.discard((x, y, z))

    def put(self, x, y, z, spec):
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def air(self, x, y, z):
        """Reserved empty cell: explicit air up to AIR_TOP (terrain bumps never fill a room), left unset (natural air,
        no template entry) higher up."""
        if y > AIR_TOP:
            self.bp.remove(x, y, z)
        else:
            self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b and "bubble" not in b and "mist" not in b

    def free(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR


def box(C, x0, y0, z0, x1, y1, z1, spec):
    for x in rng(x0, x1):
        for z in rng(z0, z1):
            for y in rng(y0, y1):
                C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def carve(C, x0, y0, z0, x1, y1, z1):
    for x in rng(x0, x1):
        for z in rng(z0, z1):
            for y in rng(y0, y1):
                C.air(x, y, z)


def busy(C, x0, z0, x1, z1, pad=0):
    for x in rng(x0 - pad, x1 + pad):
        for z in rng(z0 - pad, z1 + pad):
            C.busy.add((x, z))


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def wood_door(C, x, y, z, facing, wood="acacia", hinge="left", open_=False):
    for half, dy in (("lower", 0), ("upper", 1)):
        C.set(x, y + dy, z, f"{wood}_door[facing={facing},half={half},hinge={hinge},open={'true' if open_ else 'false'},"
                            f"powered=false]")


def iron_door(C, x, y, z, facing, hinge="left"):
    for half, dy in (("lower", 0), ("upper", 1)):
        C.set(x, y + dy, z, f"iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def lever(C, x, y, z, facing, face="wall"):
    C.set(x, y, z, f"lever[face={face},facing={facing},powered=false]")


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def candle(C, x, y, z, n=3, color="white"):
    C.set(x, y, z, f"{color}_candle[candles={n},lit=true,waterlogged=false]")


def hang(C, x, y, z, lamp=LANT_H, reach=24):
    """A lamp at (x, y, z) on a chain up to the first solid block above; nothing if there is none."""
    top = y + 1
    while top < y + reach and not C.solid(x, top, z):
        top += 1
    if not C.solid(x, top, z):
        return False
    for yy in range(y + 1, top):
        C.set(x, yy, z, CHAIN)
    C.set(x, y, z, lamp)
    return True


def lamp_grid(C, x0, z0, x1, z1, f, lamp=LANT_H, h=3, step=5, pred=None, reach=24):
    """Lamps hung over a floor (feet f) about every ``step`` blocks, each from the ceiling above it, set out from the
    middle of the area; spots where something stands or nothing hangs are skipped."""
    w, d = x1 - x0 + 1, z1 - z0 + 1
    nx = max(1, int(round(w / float(step))))
    nz = max(1, int(round(d / float(step))))
    for i in range(nx):
        for j in range(nz):
            x = x0 + int((i + 0.5) * w / nx)
            z = z0 + int((j + 0.5) * d / nz)
            if pred is not None and not pred(x, z):
                continue
            if not all(C.free(x, y, z) for y in range(f, f + h + 1)):
                continue
            hang(C, x, f + h, z, lamp, reach=reach)


def chest(C, x, y, z, facing, table):
    C.keep.discard((x, y, z))
    C.bp.chest(x, y, z, facing, loot=LOOT + table)
    if C.solid(x, y + 1, z):
        C.bp.set(x, y + 1, z, AIR)


def barrel(C, x, y, z, facing="up"):
    C.keep.discard((x, y, z))
    C.bp.barrel(x, y, z, facing)


def spawner(C, x, y, z, mob):
    C.keep.discard((x, y, z))
    C.bp.spawner(x, y, z, mob)


def waystone(C, x, y, z):
    C.keep.discard((x, y, z))
    C.set(x, y - 1, z, CGS)
    C.set(x, y, z, MOD["waystone"])


def lamp_post(C, x, y, z, h=3):
    C.set(x, y, z, PGS)
    for k in range(1, h):
        C.set(x, y + k, z, IRON_WALL)
    C.set(x, y + h, z, LANT)


# ------------------------------------------------------------------ materials as functions
def stone(x, y, z, y0=0, y1=14, seed=0):
    """Guild-brick masonry: a dark mud-brick base, cracked patches round damage clusters, a sun-bleached crown;
    band edges jittered so no course is a straight line."""
    h = hash3(x, y, z, 11 + seed)
    j = (vnoise(x * 0.7 + z * 0.4, y * 0.3, 3.0, 12 + seed) - 0.5) * 3.0
    t = (y - y0 + j) / max(1.0, float(y1 - y0))
    if t < 0.1:
        return MUD if h < 0.6 else (PMUD if h < 0.8 else CGB)
    if t < 0.2:
        return CGB if h < 0.4 else GB
    if t > 0.88:
        return PGS if h < 0.55 else GB
    if vnoise(x + z * 0.5, y, 6.0, 13 + seed) > 0.74 and h < 0.55:
        return CGB
    return GB


def house_stone(x, y, z, seed=0):
    """Plastered mud houses: packed mud and mud bricks, sandstone corners left to the builders."""
    h = hash3(x, y, z, 21 + seed)
    if y <= 1:
        return MUD if h < 0.7 else PMUD
    if vnoise(x * 0.8 + z * 0.6, y, 4.0, 22 + seed) > 0.6:
        return MUD if h < 0.8 else GB
    return PMUD if h < 0.85 else MUD


def street(x, z):
    """Everyday paving: packed mud, mud bricks and terracotta in coherent patches, a little sand blown in."""
    n = fbm(x, z, 11.0, 31)
    h = hash01(x, z, 32)
    if h < 0.06:
        return "sand"
    if n > 0.6:
        return MUD if h < 0.7 else "terracotta"
    if n < 0.35:
        return "terracotta" if h < 0.5 else PMUD
    return PMUD if h < 0.75 else MUD


def main_pave(x, z):
    """The main ways: polished guild stone with guild-tile borders every few blocks."""
    if (x + z) % 7 == 0 or (x - z) % 7 == 0:
        return GTILE
    return PGS if hash01(x, z, 33) < 0.85 else GB


# ------------------------------------------------------------------ polygon geometry
def seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    ll = vx * vx + vz * vz
    t = 0.0 if ll == 0 else max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / ll))
    return math.hypot(px - ax - vx * t, pz - az - vz * t), t


def inside_poly(x, z, poly=WALL):
    c = False
    n = len(poly)
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        if (az > z) != (bz > z):
            xi = ax + (z - az) * (bx - ax) / (bz - az)
            if x < xi:
                c = not c
    return c


def wall_d(x, z):
    n = len(WALL)
    return min(seg_dist(x, z, WALL[i], WALL[(i + 1) % n])[0] for i in range(n))


def towers():
    """Drum towers: every vertex but the gate's, and enough between them that no curtain runs over 38 blocks."""
    out = []
    n = len(WALL)
    for i in range(n):
        a, b = WALL[i], WALL[(i + 1) % n]
        if i != 0:
            out.append((a, True))
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(math.ceil(L / 38.0))
        for j in range(1, k):
            t = j / k
            p = (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))
            if abs(p[0]) < 26 and p[1] > 80:
                continue                                    # the gatehouse stands there
            out.append((p, False))
    return out


TOWERS = towers()


def near_gate(x, z):
    return abs(x) <= 19 and z > 84


def near_breach(x, z):
    return math.hypot(x - BREACH[0], z - BREACH[1]) < 7.5


# ------------------------------------------------------------------ the ground
def in_ground(x, z):
    if 86 <= z <= 118 and -104 <= x <= 114:
        return True
    if inside_poly(x, z):
        return True
    return wall_d(x, z) <= 7


def ground(C):
    """The site's own ground: the city floor (streets) inside the walls, desert hardpan and drifts outside; three layers
    (six at the rim), air above (two layers in the city) so a dune never buries a street."""
    for x in range(-112, 117):
        for z in range(-122, 119):
            if not in_ground(x, z):
                continue
            C.ground.add((x, z))
            if inside_poly(x, z):
                C.city.add((x, z))
    for (x, z) in C.ground:
        edge = any((x + dx, z + dz) not in C.ground for dx, dz in N4)
        city = (x, z) in C.city
        for y in range(-6 if edge else (0 if city else -1), 0):
            C.bp.set(x, y, z, "sandstone")
        if city:
            spec = street(x, z)
        else:
            n = fbm(x, z, 16.0, 41)
            h = hash01(x, z, 42)
            spec = ("sand" if n > 0.6 else "coarse_dirt" if n < 0.3 else
                    PMUD if h < 0.45 else "terracotta" if h < 0.7 else "gravel" if h < 0.85 else "sand")
        C.bp.set(x, 0, z, spec)
        if city:
            C.bp.set(x, 1, z, AIR)
            C.bp.set(x, 2, z, AIR)


def pave(C, pts, w, fn=main_pave, y=0):
    """Re-surface a polyline way (inside the ground) with ``fn``."""
    hw = w / 2.0
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    for x in range(int(min(xs) - hw - 1), int(max(xs) + hw + 2)):
        for z in range(int(min(zs) - hw - 1), int(max(zs) + hw + 2)):
            d = min(seg_dist(x, z, pts[i], pts[i + 1])[0] for i in range(len(pts) - 1))
            if d <= hw and (x, z) in C.ground and (x, z) not in C.busy:
                C.set(x, y, z, fn(x, z))
                for yy in (1, 2, 3):
                    if C.free(x, y + yy, z):
                        C.bp.set(x, y + yy, z, AIR)


def track(x, z):
    """The caravan road outside: trodden hardpan and gravel, crawler ruts."""
    h = hash01(x, z, 51)
    return "gravel" if h < 0.35 else ("coarse_dirt" if h < 0.6 else (PMUD if h < 0.85 else "terracotta"))


# ------------------------------------------------------------------ the city wall
def city_wall(C):
    """Curtain walls 4 thick (outer face 1, a battered plinth, the walk on top, an inner face; the core is left to the
    terrain), crenels on the outer edge, a low parapet inside, lanterns on the walk; drum towers flush with the walk,
    the vertex towers crowned with little azure domes."""
    for x in range(-110, 111):
        for z in range(-120, 108):
            if near_gate(x, z):
                continue
            d = wall_d(x, z)
            if d > 6.5:
                continue
            ins = inside_poly(x, z)
            if not ins:
                if d < 1.3:                                    # the battered plinth
                    for y in range(-3, 3):
                        C.set(x, y, z, stone(x, y, z, -6, WALK))
                continue
            if d > WALL_T:
                continue
            br = near_breach(x, z)
            top = WALK
            if br:
                top = 6 + int(max(0.0, math.hypot(x - BREACH[0], z - BREACH[1]) - 2.5) * 1.4)
            if d < 1.2:                                        # outer face
                for y in range(-3, min(top, WALK) + 1):
                    C.set(x, y, z, stone(x, y, z, -6, WALK + 2))
                if not br:
                    C.set(x, WALK + 1, z, stone(x, WALK + 1, z, -6, WALK + 2))
                    if ((x + 2 * z) // 2) % 2 == 0:
                        C.set(x, WALK + 2, z, PGS)
            elif d > WALL_T - 1.0:                             # inner face
                for y in range(-2, min(top, WALK) + 1):
                    C.set(x, y, z, stone(x, y, z, -2, WALK + 2))
                if not br:
                    C.set(x, WALK + 1, z, GB_WALL)
            else:                                              # the core: footing, the walk
                for y in (-2, -1, 0):
                    C.set(x, y, z, stone(x, y, z, -6, WALK))
                if br:
                    for y in range(1, top + 1):
                        C.set(x, y, z, CGB if hash3(x, y, z, 61) < 0.5 else GB)
                else:
                    C.set(x, WALK, z, PGS if hash01(x, z, 62) < 0.8 else GTILE)
                    for y in range(WALK + 1, WALK + 4):
                        C.air(x, y, z)
    # lanterns on the inner parapet every ~10 blocks along the walk
    for x in range(-108, 109, 3):
        for z in range(-118, 104, 3):
            if near_gate(x, z) or near_breach(x, z) or not inside_poly(x, z):
                continue
            d = wall_d(x, z)
            if WALL_T - 1.0 < d <= WALL_T and hash01(x, z, 63) < 0.28 and C.get(x, WALK + 1, z) == "brasshaven:guild_brick_wall":
                C.set(x, WALK + 2, z, LANT)
    for (p, vertex) in TOWERS:
        tower(C, p[0], p[1], vertex)
    breach(C)


def tower(C, cx, cz, vertex):
    r = 6.2
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d > r:
                continue
            ins = inside_poly(x, z)
            wd = wall_d(x, z)
            walk = ins and 1.0 <= wd <= WALL_T - 0.8
            if d > r - 1.3:
                for y in range(-2, WALK + 5):
                    if WALK < y <= WALK + 3 and walk:
                        C.air(x, y, z)                         # the walk passes through
                        continue
                    C.set(x, y, z, stone(x, y, z, -6, WALK + 6, seed=3))
                if not walk and (math.degrees(math.atan2(z - cz, x - cx)) // 22) % 2 == 0:
                    C.set(x, WALK + 5, z, PGS)
                if WALK + 2 <= WALK + 3 and not walk and hash01(x, z, 64) < 0.12:
                    C.set(x, WALK + 2, z, BARS)                # arrow slits
            else:
                for y in (-2, -1, 0):
                    C.set(x, y, z, stone(x, y, z, -6, WALK))
                C.set(x, WALK, z, PGS if (x + z) % 3 else GTILE)
                for y in range(WALK + 1, WALK + 5):
                    C.air(x, y, z)
    C.set(cx, WALK + 1, cz, LANT)
    if vertex:
        # an azure dome on a brass ring, a brass finial
        for x in range(cx - 7, cx + 8):
            for z in range(cz - 7, cz + 8):
                for y in range(WALK + 5, WALK + 12):
                    d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2 + ((y - WALK - 5) * 1.25) ** 2)
                    if r - 1.0 < d <= r + 0.2:
                        C.set(x, y, z, BRASS if y == WALK + 5 else AZ)
                    elif d <= r - 1.0:
                        C.air(x, y, z)
        C.set(cx, WALK + 12, cz, GILD)
        C.set(cx, WALK + 13, cz, ROD_U)
        hang(C, cx, WALK + 4, cz, LANT_H)


def breach(C):
    """Rubble spilling into the city from the breach: a walkable slope of cracked masonry and stairs down to the
    yard by the stables."""
    bx, bz = BREACH
    for x in range(bx - 8, bx + 9):
        for z in range(bz - 14, bz + 1):
            if not inside_poly(x, z) or wall_d(x, z) <= WALL_T:
                continue
            dd = math.hypot(x - bx, (z - bz) * 0.8)
            # height falls off with distance from the breach mouth
            h = int(round(6.5 - (bz - 2 - z) * 0.55 - abs(x - bx) * 0.35 + (hash01(x, z, 71) - 0.5)))
            if dd > 9 or h < 1:
                continue
            for y in range(1, h):
                C.set(x, y, z, CGB if hash3(x, y, z, 72) < 0.5 else (GB if hash3(x, y, z, 73) < 0.7 else MUD))
            C.set(x, h, z, stair(GB_ST, "south") if hash01(x, z, 74) < 0.8 else slab(GB_SL))
            for y in range(h + 1, h + 4):
                if C.free(x, y, z):
                    C.air(x, y, z)


# ------------------------------------------------------------------ furnishing
def perimeter(x0, z0, x1, z1):
    """Interior perimeter cells of a room, each with the direction of the wall behind it, walked round the room."""
    out = []
    for x in range(x0, x1 + 1):
        out.append((x, z0, "north"))
    for z in range(z0 + 1, z1 + 1):
        out.append((x1, z, "east"))
    for x in range(x1 - 1, x0 - 1, -1):
        out.append((x, z1, "south"))
    for z in range(z1 - 1, z0, -1):
        out.append((x0, z, "west"))
    return out


# what stands along the walls of each kind of room (cycled), and what goes in the middle
KINDS = {
    "lodging": ["bed:red", "chest", "barrel", "shelf", "flower", "bed:orange", "pot", "candle", "wool:white"],
    "dormitory": ["bed:brown", "bed:white", "barrel", "bed:light_gray", "chest", "bed:brown", "shelf"],
    "coffee": ["barrel", "brew", "cauldron", "shelf", "smoker", "chair", "pot", "chair", "barrel"],
    "warehouse": ["hay", "wool:white", "barrel", "crate", "wool:brown", "chest", "hay", "crate", "wool:orange"],
    "smithy": ["anvil", "blast", "grind", "smith", "cauldron", "chest", "barrel", "furnace"],
    "scribe": ["bookshelf", "lectern", "bookshelf", "chair", "cart", "chest", "bookshelf", "candle"],
    "kitchen": ["smoker", "furnace", "barrel", "cauldron", "craft", "barrel", "pot", "chest", "hay"],
    "prayer": ["candle", "pot", "candle", "shelf", "candle", "flower"],
    "weaver": ["loom", "wool:red", "wool:yellow", "loom", "chest", "wool:light_blue", "barrel", "wool:magenta"],
    "potter": ["pot", "furnace", "pot", "craft", "flower", "pot", "chest", "barrel"],
    "apothecary": ["brew", "cauldron", "shelf", "flower", "brew", "chest", "barrel", "candle"],
    "office": ["lectern", "chest", "barrel", "bookshelf", "chair", "shelf", "cart"],
    "armoury": ["anvil", "rack", "rack", "grind", "chest", "rack", "barrel"],
    "money": ["gold", "chest", "lectern", "brass", "chest", "gold", "candle"],
    "saddlery": ["wool:brown", "hay", "rack", "chest", "barrel", "loom", "anvil"],
    "workshop": ["gauge", "cog", "craft", "pipes", "chest", "valve", "smith", "barrel"],
    "spices": ["barrel", "pot", "barrel", "crate", "pot", "chest", "barrel", "flower"],
}
CENTRE = {"coffee": "tables", "scribe": "desk", "office": "desk", "warehouse": "stack", "lodging": "rug",
          "prayer": "rug", "money": "desk", "kitchen": "table", "apothecary": "table", "weaver": "rug",
          "dormitory": "rug", "workshop": "table", "potter": "table"}


def put_item(C, x, y, z, wall, tok, table, seed):
    inward = OPP[wall]
    if tok.startswith("bed:"):
        return False                       # handled by the caller
    if tok == "chest":
        chest(C, x, y, z, inward, table)
    elif tok == "barrel":
        barrel(C, x, y, z)
        if hash01(x, z, seed) < 0.4:
            barrel(C, x, y + 1, z)
    elif tok == "crate":
        barrel(C, x, y, z, inward)
        C.set(x, y + 1, z, "barrel[facing=up,open=false]" if hash01(x, z, seed + 1) < 0.5 else slab("spruce_slab"))
    elif tok == "hay":
        C.set(x, y, z, "hay_block[axis=y]")
        if hash01(x, z, seed + 2) < 0.6:
            C.set(x, y + 1, z, "hay_block[axis=x]")
    elif tok.startswith("wool:"):
        col = tok[5:]
        C.set(x, y, z, f"{col}_wool")
        if hash01(x, z, seed + 3) < 0.5:
            C.set(x, y + 1, z, f"{CARPETS[int(hash01(x, z, seed + 4) * 8)]}_wool")
    elif tok == "shelf":
        C.set(x, y + 1, z, f"{SHELF}[facing={inward}]")
        C.set(x, y, z, "flower_pot" if hash01(x, z, seed + 5) < 0.3 else slab("spruce_slab"))
    elif tok == "flower":
        C.set(x, y, z, ("potted_cactus", "potted_dead_bush", "potted_azalea_bush", "potted_fern")[int(hash01(x, z, seed) * 4)])
    elif tok == "pot":
        C.set(x, y, z, f"decorated_pot[cracked=false,facing={inward},waterlogged=false]")
    elif tok == "candle":
        C.set(x, y, z, slab(PGS_SL, "bottom"))
        candle(C, x, y + 1, z, 1 + int(hash01(x, z, seed) * 3), ("white", "yellow", "orange")[int(hash01(z, x, seed) * 3)])
        C.keep.discard((x, y + 1, z))
        C.set(x, y + 1, z, f"{('white', 'yellow', 'orange')[int(hash01(z, x, seed) * 3)]}_candle"
                            f"[candles={1 + int(hash01(x, z, seed) * 3)},lit=true,waterlogged=false]")
    elif tok == "bookshelf":
        C.set(x, y, z, "bookshelf")
        C.set(x, y + 1, z, "chiseled_bookshelf[facing=%s]" % inward if hash01(x, z, seed) < 0.3 else "bookshelf")
    elif tok == "lectern":
        C.set(x, y, z, f"lectern[facing={inward},has_book=false,powered=false]")
    elif tok == "anvil":
        C.set(x, y, z, f"anvil[facing={'east' if wall in ('north', 'south') else 'north'}]")
    elif tok == "furnace":
        C.set(x, y, z, f"furnace[facing={inward},lit=false]")
    elif tok == "blast":
        C.set(x, y, z, f"blast_furnace[facing={inward},lit=true]")
    elif tok == "smoker":
        C.set(x, y, z, f"smoker[facing={inward},lit=true]")
    elif tok == "grind":
        C.set(x, y, z, f"grindstone[face=floor,facing={inward}]")
    elif tok == "smith":
        C.set(x, y, z, "smithing_table")
    elif tok == "cauldron":
        C.set(x, y, z, "water_cauldron[level=3]")
    elif tok == "brew":
        C.set(x, y, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    elif tok == "loom":
        C.set(x, y, z, f"loom[facing={inward}]")
    elif tok == "cart":
        C.set(x, y, z, "cartography_table")
    elif tok == "craft":
        C.set(x, y, z, "crafting_table")
    elif tok == "chair":
        C.set(x, y, z, f"{CHAIR}[facing={inward}]")
    elif tok == "gold":
        C.set(x, y, z, "gold_block" if hash01(x, z, seed) < 0.5 else "raw_gold_block")
    elif tok == "brass":
        C.set(x, y, z, BRASS)
        C.set(x, y + 1, z, "lantern[hanging=false,waterlogged=false]")
    elif tok == "gauge":
        C.set(x, y, z, IRON)
        C.set(x, y + 1, z, GAUGE)
    elif tok == "cog":
        C.set(x, y + 1, z, f"{COG}[facing={inward}]")
        C.set(x, y, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    elif tok == "valve":
        C.set(x, y, z, PIPES)
        C.set(x, y + 1, z, f"{VALVE}[facing={inward}]")
    elif tok == "pipes":
        C.set(x, y, z, PIPES)
        C.set(x, y + 1, z, PIPES)
    elif tok == "rack":
        C.set(x, y, z, "spruce_fence")
        C.set(x, y + 1, z, ROD_U if hash01(x, z, seed) < 0.6 else "spruce_fence")
    return True


def furnish(C, x0, z0, x1, z1, f, kind, table, clear=(), seed=0, lamps=True, lamp=LANT_H):
    """Furniture of ``kind`` along the walls of the room (interior x0..x1, z0..z1, feet f), cells in ``clear`` (and next
    to them) left free; a centre piece; lamps hung from the ceiling."""
    toks = KINDS[kind]
    cells = perimeter(x0, z0, x1, z1)
    keepfree = set()
    for (cx, cz) in clear:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                keepfree.add((cx + dx, cz + dz))
    i = int(hash01(x0, z0, seed) * len(toks))
    used = set()
    chests = 0
    for k, (x, z, wall) in enumerate(cells):
        if (x, z) in keepfree or (x, z) in used or not C.free(x, f, z):
            continue
        if hash01(x, z, seed + 9) < 0.18:
            continue
        tok = toks[i % len(toks)]
        i += 1
        if tok == "chest":
            if chests >= 1 or table is None:
                tok = "barrel"
            chests += 1
        if tok.startswith("bed:"):
            if k + 1 < len(cells):
                nx, nz, nw = cells[k + 1]
                if nw == wall and (nx, nz) not in keepfree and C.free(nx, f, nz):
                    fc = out_facing(nx - x, nz - z)
                    C.bp.bed(x, f, z, fc, color=tok[4:])
                    used.add((nx, nz))
                    continue
            tok = "barrel"
        put_item(C, x, f, z, wall, tok, table, seed)
        used.add((x, z))
    w, d = x1 - x0 + 1, z1 - z0 + 1
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    centre = CENTRE.get(kind)
    if centre and w >= 5 and d >= 5:
        if centre == "rug":
            col = CARPETS[int(hash01(x0, z1, seed) * 8)]
            col2 = CARPETS[int(hash01(z0, x1, seed) * 8)]
            for x in range(x0 + 1, x1):
                for z in range(z0 + 1, z1):
                    if C.free(x, f, z) and (x, z) not in keepfree:
                        edge = x in (x0 + 1, x1 - 1) or z in (z0 + 1, z1 - 1)
                        C.set(x, f, z, f"{col2 if edge else col}_carpet")
        elif centre in ("tables", "table", "desk"):
            spots = [(cx, cz)]
            if centre == "tables" and w >= 9:
                spots = [(x0 + 2, cz), (x1 - 2, cz)]
            for (tx, tz) in spots:
                if (tx, tz) in keepfree:
                    continue
                C.set(tx, f, tz, TABLE)
                C.set(tx, f + 1, tz, ("lantern[hanging=false,waterlogged=false]" if centre == "desk" else
                                      "flower_pot"))
                for (dx, dz, fc) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
                    if centre == "desk" and dz != 1:
                        continue
                    if centre != "desk" and ((w >= d and dz) or (w < d and dx)):
                        continue                                  # chairs along the long axis: a way round
                    if C.free(tx + dx, f, tz + dz) and (tx + dx, tz + dz) not in keepfree:
                        C.set(tx + dx, f, tz + dz, f"{CHAIR}[facing={fc}]")
        elif centre == "stack":
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 1):
                    if (x, z) not in keepfree and C.free(x, f, z):
                        C.set(x, f, z, "hay_block[axis=y]" if (x + z) % 2 else f"{CARPETS[(x * 3 + z) % 8]}_wool")
    if lamps:
        # one lamp per ~5 x 5 of floor, set out along the room's long axis (a row, or two rows in a wide room)
        nl = max(1, int(round(w / 5.0)))
        nd = max(1, int(round(d / 5.0)))
        xs = [x0 + int((i + 0.5) * w / nl) for i in range(nl)]
        zs = [z0 + int((j + 0.5) * d / nd) for j in range(nd)]
        for lx in xs:
            for lz in zs:
                if not C.free(lx, f + 2, lz):
                    continue
                y = f + 2
                while C.free(lx, y + 1, lz) and y < f + 12:
                    y += 1
                hang(C, lx, min(max(f + 2, y - 1), f + 3), lz, lamp)


# ------------------------------------------------------------------ the gatehouse
def pointed(half_w, h):
    """Pointed-arch intrados: for |u| <= half_w, the height (above the springing) under the arch."""
    R = half_w * 1.6
    c = R - half_w

    def height(u):
        v = R * R - (abs(u) + c) ** 2
        if v <= 0:
            return 0.0
        return math.sqrt(v) * h / math.sqrt(R * R - c * c)
    return height


def gatehouse(C):
    """The south gatehouse: a body astride the wall with the guard room and the toll house, two square towers, the
    pishtaq with its tiled frame, the brass clock gear and the iwan; the great brass gate and its wicket; the toll
    tunnel north into the court."""
    busy(C, -20, 83, 20, 109)
    # body x -19 .. 19, z 88 .. 99: masonry shell, roof flush with the wall walk
    for x in range(-19, 20):
        for z in range(88, 100):
            edge = x in (-19, 19) or z in (88, 99)
            for y in range(-6 if edge else -2, WALK + 1):
                if edge or y <= 0 or y >= 7:
                    if not edge and 8 <= y < WALK:
                        continue                                   # hidden core
                    C.set(x, y, z, stone(x, y, z, -6, WALK + 2, seed=5))
            if edge:
                C.set(x, WALK + 1, z, stone(x, WALK + 1, z, -6, WALK + 2, seed=5))
                if (x + z) % 2 == 0:
                    C.set(x, WALK + 2, z, PGS)
            else:
                C.set(x, WALK, z, PGS if (x + z) % 4 else GTILE)
                for y in range(WALK + 1, WALK + 4):
                    C.air(x, y, z)
    # the passage x -1 .. 1 from the gate (z 98) to the court (z 70), and its walls in the street gap
    for z in range(70, 100):
        for x in range(-1, 2):
            C.set(x, 0, z, main_pave(x, z))
            for y in range(1, 5):
                C.air(x, y, z)
            if x == 0:
                C.air(x, 5, z)
        if 82 <= z <= 99:
            for x in (-3, -2, 2, 3):
                for y in range(-1, 7):
                    C.set(x, y, z, stone(x, y, z, -2, 8, seed=6))
            for x in range(-1, 2):
                C.set(x, 6, z, PGS)
                if x != 0:
                    C.set(x, 5, z, stair(PGS_ST, "east" if x < 0 else "west", "top"))
            for x in range(-3, 4):
                C.set(x, 7, z, GB if 83 <= z <= 87 else C.get(x, 7, z) or GB)
        if z % 5 == 0 and 72 <= z <= 97:
            hang(C, 0, 4, z, LANT_H)
    # guard room (west) and toll house (east)
    for (x0, x1, kind, door_x, face) in ((-17, -4, "armoury", -3, "west"), (4, 17, "office", 3, "east")):
        for x in range(x0, x1 + 1):
            for z in range(89, 98):
                C.set(x, 0, z, "spruce_planks" if kind == "armoury" else PARQ)
                for y in range(1, 7):
                    C.air(x, y, z)
                C.set(x, 7, z, "spruce_planks" if (x % 4) else "stripped_spruce_log[axis=z]")
        sx = -1 if door_x < 0 else 1
        C.air(door_x - sx, 1, 93)
        C.air(door_x - sx, 2, 93)
        wood_door(C, door_x, 1, 93, face)
        C.air(door_x + sx, 1, 93)
        C.air(door_x + sx, 2, 93)
        furnish(C, x0, 89, x1, 97, 1, kind, "bcv_gate", clear=[(door_x + sx, 93)], seed=x0)
    # murder slits from the guard room into the passage
    for z in (90, 96):
        C.set(-2, 2, z, BARS)
        C.set(-3, 2, z, BARS)
    spawner(C, -12, 1, 92, MOB_BANDIT)
    # the towers (x 9 .. 19 / -19 .. -9, z 99 .. 108): chamfered shells to y 30
    for s in (-1, 1):
        xa, xb = (9, 19) if s > 0 else (-19, -9)
        for x in range(xa, xb + 1):
            for z in range(99, 109):
                corner = (x in (xa, xb)) and (z in (99, 108))
                if corner:
                    continue
                edge = x in (xa, xb, xa + 1 if (z in (99, 108)) else xa) or z in (99, 108) or \
                    (x in (xa + 1, xb - 1) and z in (99, 108))
                edge = x in (xa, xb) or z in (99, 108) or (abs(x - xa) + abs(z - 99) == 1) or \
                    (abs(x - xb) + abs(z - 108) == 1) or (abs(x - xa) + abs(z - 108) == 1) or \
                    (abs(x - xb) + abs(z - 99) == 1)
                top = 30
                for y in range(-6 if edge else -2, top + 1):
                    if not edge and 1 <= y < top:
                        continue
                    if y in (15, 16):
                        spec = AZ if edge else PGS
                    elif y == 28:
                        spec = GILD
                    else:
                        spec = stone(x, y, z, -6, top, seed=7)
                    C.set(x, y, z, spec)
                if edge and (x + z) % 2 == 0:
                    C.set(x, top + 1, z, PGS)
                    C.set(x, top + 2, z, slab(PGS_SL))
                elif edge:
                    C.set(x, top + 1, z, GB_WALL)
        # slit windows, a lantern on the front corner
        for y in (8, 20, 24):
            C.set(s * 14, y, 108, BARS)
        C.set(s * 14, 18, 109, LANT)
        C.set(s * 14, 17, 109, stair(PGS_ST, "north", "top"))
    pishtaq(C)
    # the street gap between the court and the gatehouse: paving under the tunnel's sides
    pave(C, [(-30, 85), (30, 85)], 3, street)


def pishtaq(C):
    """The gate's portal screen (x -8 .. 8, z 104 .. 108, to y 34): a tiled frame round the pointed iwan (11 wide, 18
    high, recessed to the great gate at z 99), muqarnas under the arch, the brass clock gear above it."""
    arch = pointed(5.5, 17.0)
    for x in range(-8, 9):
        for z in range(99, 109):
            for y in range(-2, 35):
                inner = abs(x) <= 5 and z >= 100 and 1 <= y <= int(arch(x)) and y >= 1
                if inner:
                    C.air(x, y, z)
                    continue
                if abs(x) <= 6 and z >= 100 and y <= int(arch(min(abs(x), 5.5))) + 1 and abs(x) <= 5:
                    pass
                front = z == 108
                side = abs(x) == 8
                if not (front or side or y <= 0 or y >= 33 or (abs(x) <= 6 and y <= 20)):
                    continue                                       # hidden core of the screen
                if y <= 0:
                    spec = stone(x, y, z, -6, 34, seed=8)
                elif front:
                    ax = abs(x)
                    au = abs(ax - 0)
                    rim = arch(min(ax, 5.5))
                    if ax <= 7 and y <= rim + 2.5 and ax >= 5 and y >= 1:
                        spec = AZ if (y + ax) % 2 else "light_blue_glazed_terracotta[facing=south]"
                    elif ax in (7, 8) or y in (32, 33, 34):
                        spec = AZ if ax == 7 or y == 32 else PGS
                    elif y >= 21 and ax <= 6:
                        spec = PGS
                    else:
                        spec = CGS if (y % 4 == 0) else GB
                else:
                    spec = stone(x, y, z, -6, 34, seed=8)
                C.set(x, y, z, spec)
    # the recess side walls and the vault over the iwan (muqarnas: upside-down stairs stepping in)
    for z in range(100, 108):
        for x in range(-6, 7):
            if abs(x) == 6:
                for y in range(1, 18):
                    C.set(x, y, z, PGS if y % 5 else CGS)
            else:
                top = int(arch(x))
                C.set(x, top + 1, z, AZ if (x + z) % 2 else GB)
                if 0 < abs(x) < 6 and top >= 2:
                    C.set(x, top, z, stair(PGS_ST, "east" if x < 0 else "west", "top")) if z % 2 else None
    # crown: merlons and two brass finials
    for x in range(-8, 9):
        if x % 2 == 0:
            C.set(x, 35, 108, PGS)
    for s in (-1, 1):
        C.set(s * 8, 35, 108, BRASS)
        C.set(s * 8, 36, 108, GILD)
        C.set(s * 8, 37, 108, ROD_U)
    # the brass clock gear in the tympanum (centre y 26)
    for x in range(-5, 6):
        for y in range(21, 32):
            d = math.hypot(x, y - 26)
            if d <= 4.6:
                spec = GEAR if d > 3.4 else (BTILE if d > 1.2 else GILD)
                if d > 4.0 and (round(math.degrees(math.atan2(y - 26, x))) // 30) % 2 == 0:
                    spec = BRASS
                C.set(x, y, 109, spec)
                C.set(x, y, 108, PGS)
    for (dx, dy) in ((0, 1), (0, 2), (1, 0), (2, 0)):
        C.set(dx, 26 + dy, 110, f"{IRON_WALL}")
    # the great gate (z 99, x -4 .. 4, y 1 .. 14) with the wicket (x -1 .. 1, y 1 .. 4)
    for x in range(-5, 6):
        for y in range(1, 17):
            if abs(x) <= 1 and y <= 4:
                C.air(x, y, 99)
                continue
            if abs(x) == 5 or y >= 15:
                spec = DIB
            elif y in (1, 14) or abs(x) == 4 or x == 0:
                spec = ENGR
            else:
                spec = BRASS if (x + y) % 3 else GILD
            C.set(x, y, 99, spec)
    for x in range(-1, 2):
        C.set(x, 0, 99, main_pave(x, 99))
        C.set(x, 5, 99, DIB)
    # the iwan floor and steps out to the road
    for x in range(-5, 6):
        for z in range(100, 109):
            C.set(x, 0, z, main_pave(x, z))
    C.set(-2, 1, 100, LANT)
    C.set(2, 1, 100, LANT)
    for s in (-1, 1):
        hang(C, s * 3, 8, 104, LANT_H)


# ------------------------------------------------------------------ the caravan court (hub)
CX0, CZ0, CX1, CZ1 = COURT


def court_pier(axis_coord, along):
    """Is this cell of a pier line a pier (the 5-wide openings between them, one centred on each passage)?"""
    if along == "x":
        return abs(axis_coord) >= 19 or (axis_coord - 3) % 7 in (0, 1)
    return axis_coord in (35, 36, 69, 70) or (axis_coord - 55) % 7 in (0, 1)


def court_rooms():
    """(x0, z0, x1, z1, door (x, z, facing), arcade side) of every room of the four ranges (both storeys)."""
    rooms = []
    for (xa, xb) in ((-31, -20), (-18, -5), (5, 18), (20, 31)):
        xm = (xa + xb) // 2
        rooms.append((xa, 76, xb, 81, (xm, 75, "north"), "S"))
        rooms.append((xa, 25, xb, 29, (xm, 30, "south"), "N"))
    for (za, zb) in ((31, 40), (42, 49), (56, 63), (65, 74)):
        zm = (za + zb) // 2
        rooms.append((-31, za, -27, zb, (-26, zm, "east"), "W"))
        rooms.append((27, za, 31, zb, (26, zm, "west"), "E"))
    return rooms


GROUND_KINDS = ["lodging", "coffee", "warehouse", "smithy", "saddlery", "kitchen", "spices", "office", "weaver",
                "apothecary", "money", "lodging", "potter", "warehouse", "workshop", "lodging"]
UPPER_KINDS = ["dormitory", "lodging", "scribe", "prayer", "lodging", "office", "weaver", "lodging", "dormitory",
               "apothecary", "lodging", "scribe", "lodging", "coffee", "lodging", "lodging"]


def court(C):
    """Two storeys of arcades round a 41 x 34 court: lodgings and stores behind, two stair halls up to the gallery,
    the fountain kiosk, palms and bales; the passages to the gate (south), the stables (west), the souk (east) and the
    barred north gate (lever outside)."""
    busy(C, CX0, CZ0, CX1, CZ1)
    ranges = [(-32, 70, 32, 82), (-32, 24, 32, 35), (-32, 36, -21, 69), (21, 36, 32, 69)]
    for (x0, z0, x1, z1) in ranges:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                outer = x in (CX0, CX1) or z in (CZ0, CZ1)
                for y in range(-6 if outer else -1, 14):
                    C.set(x, y, z, stone(x, y, z, -6, 15, seed=9) if outer or y in (13, -1) else GB)
                if outer:
                    C.set(x, 14, z, stone(x, 14, z, -6, 15, seed=9))
                    if (x + z) % 2 == 0:
                        C.set(x, 15, z, PGS)
    # arcades, both storeys
    arcades = [(-25, 71, 25, 74), (-25, 31, 25, 34), (-25, 31, -22, 74), (22, 31, 25, 74)]
    for (x0, z0, x1, z1) in arcades:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                C.set(x, 0, z, GTILE if (x + z) % 2 else PGS)
                for y in range(1, 6):
                    C.air(x, y, z)
                C.set(x, 6, z, PGS)
                C.set(x, 7, z, "spruce_planks" if (x + z) % 3 else "stripped_spruce_log[axis=x]")
                for y in range(8, 13):
                    C.air(x, y, z)
    # pier lines: openings with pointed heads, railings on the gallery, a carved band at the floor line
    lines = [("x", 70, "south"), ("x", 35, "north"), ("z", -21, "west"), ("z", 21, "east")]
    for (along, k, side) in lines:
        span = range(-21, 22) if along == "x" else range(35, 71)
        for u in span:
            x, z = (u, k) if along == "x" else (k, u)
            if court_pier(u, along):
                for y in range(1, 13):
                    C.set(x, y, z, PGS if y not in (5, 12) else CGS)
                continue
            # the opening: find its extent to shape the head
            a = u
            while not court_pier(a - 1, along):
                a -= 1
            b = u
            while not court_pier(b + 1, along):
                b += 1
            mid = (a + b) / 2.0
            off = abs(u - mid)
            hw = (b - a) / 2.0
            for (y0, top) in ((1, 4), (8, 11)):
                for y in range(y0, top + 1):
                    if y == top and off > hw - 1.0:
                        C.set(x, y, z, stair(GB_ST, OPP[side] if False else side, "top") if False else GB)
                        continue
                    C.air(x, y, z)
            C.set(x, 5, z, AZ if off < 1 else GB)
            C.set(x, 12, z, AZ if off < 1 else GB)
            inward = {"south": "north", "north": "south", "west": "east", "east": "west"}[side]
            railing(C, x, 8, z, inward)
        # cornice and parapet on the court face
        for u in span:
            x, z = (u, k) if along == "x" else (k, u)
            C.set(x, 6, z, CGS)
            C.set(x, 13, z, PGS)
            C.set(x, 14, z, GB_WALL if u % 3 else PGS)
    # rooms (both storeys), doors, windows, furnishing
    for i, (x0, z0, x1, z1, door, side) in enumerate(court_rooms()):
        for (f, kinds) in ((1, GROUND_KINDS), (8, UPPER_KINDS)):
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    C.set(x, f - 1, z, PARQ if f == 8 else ("terracotta" if (x + z) % 2 else PMUD))
                    for y in range(f, f + 5):
                        C.air(x, y, z)
                    if f == 1:
                        C.set(x, 6, z, "stripped_spruce_log[axis=%s]" % ("x" if side in "NS" else "z")
                              if (x + z) % 3 == 0 else "spruce_planks")
            dx, dz, face = door
            wood_door(C, dx, f, dz, face, wood="acacia" if f == 1 else "jungle")
            ix, iz = dx - DV[face][0], dz - DV[face][1]
            # a window beside the door onto the arcade, and barred slits on the outer wall
            wx, wz = (dx + 3, dz) if side in "NS" else (dx, dz + 3)
            if C.get(wx, f + 1, wz) is not None and (x0 <= wx <= x1 or z0 <= wz <= z1):
                C.set(wx, f + 1, wz, PANE)
                C.set(wx, f + 2, wz, PANE)
            kind = kinds[i % len(kinds)]
            stair_room = (side == "W" and z0 == 65) or (side == "E" and z0 == 31)
            if stair_room:
                court_stair(C, side, f)
                lx = x1 if side == "E" else x0
                hang(C, lx, 4 if f == 1 else 11, (z0 + z1) // 2 + (2 if f == 1 else -2), LANT_H)
                continue
            furnish(C, x0, z0, x1, z1, f, kind, "bcv_court", clear=[(ix, iz)], seed=i * 7 + f)
        # barred windows in the outer wall
        if side in "NS":
            wz = CZ1 if side == "S" else CZ0
            for wx in range(x0 + 2, x1 - 1, 4):
                for f in (2, 9):
                    C.set(wx, f, wz, BARS)
                    C.set(wx, f + 1, wz, BARS)
        else:
            wx = CX0 if side == "W" else CX1
            for wz in range(z0 + 2, z1 - 1, 4):
                for f in (2, 9):
                    C.set(wx, f, wz, BARS)
                    C.set(wx, f + 1, wz, BARS)
    spawner(C, 12, 8, 79, MOB_RAIDER)
    # the passages: gate vestibule (S), north gate vestibule (N), stables (W), souk (E)
    for (x0, z0, x1, z1) in ((-3, 76, 3, 81), (-3, 25, 3, 29)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                C.set(x, 0, z, main_pave(x, z))
                for y in range(1, 6):
                    C.air(x, y, z)
        for s in (-1, 1):
            C.set(s * 3, 1, (z0 + z1) // 2, stair(PGS_ST, "west" if s > 0 else "east"))
            C.set(s * 3, 1, (z0 + z1) // 2 + 1, stair(PGS_ST, "west" if s > 0 else "east"))
        hang(C, 0, 4, (z0 + z1) // 2, CHANDELIER)
    for zz in (75, 30):
        for x in range(-2, 3):
            for y in range(1, 5):
                C.air(x, y, zz)
    for x in range(-1, 2):
        for y in range(1, 5):
            C.air(x, y, CZ1)
    # the north gate: one iron door, its lever on the outside only (the bazaar side)
    for x in range(-1, 2):
        for y in range(1, 4):
            C.set(x, y, CZ0, stone(x, y, CZ0, -6, 15, seed=9))
    iron_door(C, 0, 1, CZ0, "north")
    lever(C, 1, 2, CZ0 - 1, "north")
    for (xo, xi) in ((CX0, -26), (CX1, 26)):
        lo, hi = (xo, xi) if xo < xi else (xi, xo)
        for x in range(lo, hi + 1):
            for z in range(51, 55):
                C.set(x, 0, z, main_pave(x, z))
                for y in range(1, 5 if x in (xo, xi) else 6):
                    C.air(x, y, z)
        hang(C, (xo + xi) // 2, 4, 52, LANT_H)
    # lamps along both storeys of the arcades, between the piers
    for (x0, z0, x1, z1) in arcades:
        along_x = (x1 - x0) > (z1 - z0)
        mid = (z0 + z1) // 2 if along_x else (x0 + x1) // 2
        for t in range((x0 if along_x else z0) + 3, (x1 if along_x else z1) - 1, 6):
            x, z = (t, mid) if along_x else (mid, t)
            for y in (4, 11):
                if C.free(x, y, z) and C.free(x, y - 1, z):
                    hang(C, x, y, z, LANT_H)
    yard(C)


def court_stair(C, side, f):
    """The stair halls: a straight 3-wide flight of 7 up to the upper storey (W climbs north, E climbs south), the hole
    railed on the upper floor."""
    if side == "W":
        xs, z_first, step = range(-30, -27), 73, -1
    else:
        xs, z_first, step = range(28, 31), 32, 1
    face = "north" if step < 0 else "south"
    if f == 1:
        for i in range(7):
            z = z_first + step * i
            for x in xs:
                C.set(x, i + 1, z, stair(GB_ST, face))
                for y in range(1, i + 1):
                    C.set(x, y, z, GB)
                for y in range(i + 2, i + 6):
                    C.air(x, y, z)
        # the landing at the top (upper floor level)
        for k in (7, 8):
            z = z_first + step * k
            for x in xs:
                C.set(x, 7, z, PARQ)
    else:
        for i in range(7):
            z = z_first + step * i
            for x in xs:
                C.keep.discard((x, 7, z))
                if C.get(x, 7, z) != "minecraft:" + GB_ST.split(":")[-1] and "stairs" not in (C.get(x, 7, z) or ""):
                    C.air(x, 7, z)
        # a railing round the hole on the side away from the wall
        rx = xs[-1] + 1 if side == "W" else xs[0] - 1
        for i in range(0, 6):
            z = z_first + step * i
            railing(C, rx, 8, z, "east" if side == "W" else "west")


def palm(C, x, y, z, h=7, seed=0):
    """A date palm: a slightly leaning ringed trunk, a crown of drooping fronds, dates (cocoa) under it."""
    lx, lz = DV[("north", "east", "south", "west")[int(hash01(x, z, seed + 1) * 4)]]
    tx, tz = x, z
    for i in range(h):
        if i == h // 2 + 1:
            tx, tz = tx + lx, tz + lz
        C.set(tx, y + i, tz, PALM_LOG if i % 3 else "stripped_jungle_log[axis=y]")
    top = y + h
    C.set(tx, top, tz, PALM_LEAF)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        n = 3 if dx and dz else 4
        for s in range(1, n + 1):
            yy = top - (1 if s >= n - 1 else 0) - (1 if s == n else 0)
            C.put(tx + dx * s, yy, tz + dz * s, PALM_LEAF)
    for (dx, dz, fc) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north")):
        if C.free(tx + dx, top - 1, tz + dz):
            C.set(tx + dx, top - 1, tz + dz, f"cocoa[age=2,facing={fc}]")


def planter_palm(C, x, z, h=7, seed=0):
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            C.set(x + dx, 0, z + dz, CGS if (dx or dz) else "coarse_dirt")
            if dx or dz:
                C.set(x + dx, 1, z + dz, slab(PGS_SL))
    C.set(x, 1, z, "rooted_dirt")
    palm(C, x, 2, z, h, seed)


def kiosk(C, cx, cz, r=5.5, y0=1, pool=True):
    """A domed fountain kiosk (sabil): eight columns on a round step, an onion dome of azure tiles with brass ribs, a
    brass jet in a round pool."""
    for x in range(int(cx - r - 2), int(cx + r + 3)):
        for z in range(int(cz - r - 2), int(cz + r + 3)):
            d = math.hypot(x - cx, z - cz)
            if d <= r + 1.2:
                C.set(x, y0 - 1, z, GTILE if d > r else PGS)
            if pool and d <= 3.3:
                C.set(x, y0 - 2, z, PGS)
                C.set(x, y0 - 1, z, WATER)
            elif pool and d <= 4.2:
                C.set(x, y0, z, CGS)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        px, pz = int(round(cx + math.cos(a) * r)), int(round(cz + math.sin(a) * r))
        for y in range(y0, y0 + 6):
            C.set(px, y, pz, PGS if y < y0 + 5 else CGS)
    prof = {6: r + 0.2, 7: r + 0.2, 8: r + 0.5, 9: r + 0.3, 10: r - 0.4, 11: r - 1.4, 12: r - 2.6, 13: r - 3.8,
            14: 0.9}
    for x in range(int(cx - r - 2), int(cx + r + 3)):
        for z in range(int(cz - r - 2), int(cz + r + 3)):
            d = math.hypot(x - cx, z - cz)
            a = math.degrees(math.atan2(z - cz, x - cx)) % 45
            for dy, rr in prof.items():
                y = y0 + dy
                if rr - 1.0 < d <= rr + 0.3:
                    C.set(x, y, z, GB if dy in (6, 7) else (BRASS if a < 6 or a > 39 else AZ))
                elif d <= rr - 1.0:
                    C.air(x, y, z)
    C.set(int(cx), y0 + 15, int(cz), GILD)
    C.set(int(cx), y0 + 16, int(cz), ROD_U)
    if pool:
        C.set(int(cx), y0 - 1, int(cz), BRASS)
        C.set(int(cx), y0, int(cz), ENGR)
        C.set(int(cx), y0 + 1, int(cz), "waxed_copper_bulb[lit=true,powered=false]")
        for (dx, dz) in ((2, 1), (-2, -1), (1, -2)):
            C.set(int(cx) + dx, y0, int(cz) + dz, "lily_pad")
    hang(C, int(cx), y0 + 4, int(cz), LANT_H)


def yard(C):
    """The court floor: tiled cross walks, the fountain kiosk, four palms, the hub waystone, merchants' bales."""
    for x in range(-20, 21):
        for z in range(36, 70):
            if abs(x) <= 2 or abs(z - 53) <= 1:
                spec = GTILE if (x + z) % 2 else PGS
            else:
                spec = "terracotta" if (x * 3 + z) % 5 == 0 else (PMUD if hash01(x, z, 81) < 0.7 else MUD)
            C.set(x, 0, z, spec)
            for y in range(1, 4):
                C.air(x, y, z)
    kiosk(C, 0, 53)
    for (x, z) in ((-14, 42), (14, 42), (-14, 64), (14, 64)):
        planter_palm(C, x, z, 7 + int(hash01(x, z, 82) * 3), seed=x + z)
    waystone(C, 6, 1, 62)
    lamp_post(C, -6, 1, 62)
    # bales and crates at the arcade feet
    for (x, z) in ((-18, 38), (-17, 38), (-18, 39), (18, 67), (17, 67), (18, 66), (-18, 67), (18, 39)):
        C.set(x, 1, z, "hay_block[axis=x]" if (x + z) % 2 else "barrel[facing=up,open=false]")
    for (x, z) in ((-18, 38), (18, 67)):
        C.set(x, 2, z, f"{CARPETS[(x + z) % 8]}_wool")
    # a steam handcart
    for x in range(8, 12):
        C.set(x, 1, 44, BRASS_SLAB + "[type=top,waterlogged=false]" if x < 11 else IRON)
    for x in (8, 10):
        C.set(x, 1, 45, f"{COG}[facing=south]")
    C.set(11, 2, 44, SMOKE)
    C.set(9, 2, 44, "barrel[facing=up,open=false]")


# ------------------------------------------------------------------ the great bazaar (dominant)
PIERS = [math.radians(22.5 + 45 * k) for k in range(8)]
DRUM_IN, DRUM_OUT = 22.5, 25.3
DOME_Y = 38                                   # dome springing (drum top 37)
DOME_R = 25.3
DOME_RHO = DOME_R * 1.4
DOME_H = math.sqrt(DOME_RHO ** 2 - (DOME_RHO - DOME_R) ** 2)


def dB(x, z):
    return math.hypot(x, z - BCZ)


def dome_r(y):
    t = y - DOME_Y
    if t < 0 or t > DOME_H:
        return -1.0
    return (DOME_R - DOME_RHO) + math.sqrt(DOME_RHO ** 2 - t * t)


def pier_at(x, z):
    v = z - BCZ
    for a in PIERS:
        px, pz = math.cos(a) * 24.0, math.sin(a) * 24.0
        if math.hypot(x - px, v - pz) <= 2.3:
            return True
    return False


def arch_top(x, z):
    """Intrados height of the ring arcade at (x, z) (between two piers, apex 16 on the axes and diagonals)."""
    v = z - BCZ
    a = math.degrees(math.atan2(v, x)) % 45.0
    off = min(a, 45.0 - a)                       # degrees from the opening centre
    s = math.radians(off) * dB(x, z)
    return 8 + pointed(7.6, 8.0)(min(s, 7.6))


def in_treasury_zone(u, v):
    return v >= 12 and -13 <= u <= 18


def in_ring(u, v):
    """The cistern ring under the ambulatory (a horseshoe open to the south, where the treasury is)."""
    return math.hypot(u, v) >= 22.6 and max(abs(u), abs(v)) <= 30 and not in_treasury_zone(u, v)


def newel_boxes():
    # (x0, z0, start corner, clockwise): k = 5, box 11 x 11 in the north corners of the base
    return [(20, BCZ - 30, 3, True), (-30, BCZ - 30, 2, False)]


def in_newel(x, z, pad=0):
    for (x0, z0, _s, _c) in newel_boxes():
        if x0 - pad <= x <= x0 + 10 + pad and z0 - pad <= z <= z0 + 10 + pad:
            return True
    return False


def bazaar(C):
    """The great bazaar: a 65-wide square base with four iwans, the ambulatory of stalls round the sunken auction pit
    (iron grilles on its rim), eight piers carrying a windowed drum and the 34-high pointed dome of azure tiles and
    sixteen brass ribs with its lantern; the gallery inside the drum, the roof terrace, the corner newel stairs; the
    cistern ring, the lot hall and the auctioneers' stair under it; the treasury and its lift; the porters' stair."""
    busy(C, -34, BCZ - 34, 34, BCZ + 34)
    for x in range(-32, 33):
        for z in range(BCZ - 32, BCZ + 33):
            u, v = x, z - BCZ
            d = math.hypot(u, v)
            m = max(abs(u), abs(v))
            if m >= 31:                                              # outer walls
                for y in range(-14 if m == 31 else -3, ROOF_B + 2):
                    C.set(x, y, z, stone(x, y, z, -14, ROOF_B + 2, seed=13))
                if (x + z) % 2 == 0:
                    C.set(x, ROOF_B + 2, z, PGS)
                continue
            if d <= 22.6:
                continue                                             # the pit and its wall: below
            # floor slab over the cistern, the ambulatory, its vault, the roof
            C.set(x, 0, z, GTILE if (x + z) % 3 == 0 else PGS)
            C.set(x, -1, z, GB)
            C.set(x, -2, z, GB)
            if pier_at(x, z):
                for y in range(1, ROOF_B + 1):
                    C.set(x, y, z, PGS if y % 6 else CGS)
                continue
            if d < 26.0:                                             # the ring arcade
                top = int(arch_top(x, z))
                for y in range(1, top + 1):
                    C.air(x, y, z)
                for y in range(top + 1, ROOF_B + 1):
                    C.set(x, y, z, GB if y != top + 1 else AZ)
                continue
            if in_newel(x, z):
                continue
            for y in range(1, 12):
                C.air(x, y, z)
            C.set(x, 12, z, PGS if (x + z) % 4 else GTILE)
            C.set(x, ROOF_B, z, PGS if (x * 3 + z) % 5 else GTILE)
            C.set(x, ROOF_B - 1, z, GB)
    pit(C)
    drum_and_dome(C)
    iwans(C)
    newels(C)
    ambulatory(C)
    undercroft(C)
    treasury(C)
    porters_stair(C)


def pit(C):
    """The auction pit: a 35-wide floor of brass, azure and polished stone (a compass of the caravan roads, sea-lantern
    studs), two tiers of bidders' steps, a wall with inset Edison lamps, the rim balustrade with iron grilles."""
    for x in range(-23, 24):
        for z in range(BCZ - 23, BCZ + 24):
            u, v = x, z - BCZ
            d = math.hypot(u, v)
            if d > 22.6:
                continue
            a = math.degrees(math.atan2(v, u)) % 360
            if d <= 17.5:
                top = PIT_F
                if d < 1.5:
                    spec = GILD
                elif (8.0 <= d < 9.0) or (16.5 <= d):
                    spec = BTILE
                elif 12.0 <= d < 13.0:
                    spec = AZ
                elif min(a % 45, 45 - a % 45) * math.pi / 180 * d < 0.6:
                    spec = BTILE if a % 90 < 1 or a % 90 > 89 else ENGR
                elif d < 6:
                    spec = CGS if (u + v) % 2 else PGS
                else:
                    spec = PGS if hash01(x, z, 91) < 0.9 else GTILE
                lamp_ring = (abs(d - 13.0) < 0.5 or abs(d - 4.5) < 0.5) and min(a % 45, 45 - a % 45) < 6
                C.set(x, top, z, SEA if lamp_ring else spec)
            elif d <= 19.0:
                top = PIT_F + 1
                C.set(x, top, z, CGS if (int(a) // 10) % 2 else PGS)
            elif d <= 20.5:
                top = PIT_F + 2
                C.set(x, top, z, PGS)
            else:
                top = None
            if top is not None:
                for y in range(top - 3, top):
                    C.set(x, y, z, GB if y > top - 3 else "sandstone")
                for y in range(top + 1, AIR_TOP + 1):
                    C.air(x, y, z)
                continue
            # the pit wall (20.5 .. 22.6): faced inside, the rim and the grille on top
            for y in range(-14, 1):
                inner = d <= 21.6
                if inner and y in (PIT_F + 3, PIT_F + 7) and min(a % 20, 20 - a % 20) < 3:
                    spec = EDISON
                elif inner and y == PIT_F + 5:
                    spec = AZ
                elif inner and y == -1:
                    spec = GILD
                else:
                    spec = stone(x, y, z, -14, 2, seed=14) if not inner else (PGS if y % 3 else GB)
                C.set(x, y, z, spec)
            if d <= 21.6:
                C.set(x, 1, z, CGS)
                C.set(x, 2, z, BARS)
                C.set(x, 3, z, BARS)
                C.set(x, 4, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
            else:
                C.set(x, 0, z, PGS)
                for y in range(1, AIR_TOP + 1):
                    C.air(x, y, z)
    # the aisles through the tiers to the north door (the arena's way in) and the south door (the treasury)
    for v in list(range(-23, -16)) + list(range(17, 24)):
        for u in range(-1, 2):
            x, z = u, BCZ + v
            d = math.hypot(u, v)
            if d > 17.5:
                C.set(x, PIT_F, z, GTILE)
            for y in range(PIT_F + 1, PIT_F + 4):
                C.air(x, y, z)
            if d > 20.4:
                C.set(x, PIT_F + 4, z, CGS)
                C.set(x, PIT_F + 5, z, GILD)
    # the sealed bars of the treasury door (opened when the boss falls)
    for u in range(-1, 2):
        for y in range(PIT_F + 1, PIT_F + 4):
            C.set(u, y, BCZ + 21, MOD["vault_bars"])
    # the mist across the north door (in the wall)
    C.bp.mist(-1, PIT_F + 1, BCZ - 21, 1, PIT_F + 3, BCZ - 21)
    # the auctioneer's lectern and the block (a brass podium) by the north door, out of the fight's way
    C.set(-4, PIT_F + 2, BCZ - 19, f"lectern[facing=south,has_book=false,powered=false]")
    C.set(4, PIT_F + 2, BCZ - 19, BRASS)
    C.set(4, PIT_F + 3, BCZ - 19, "bell[attachment=floor,facing=south,powered=false]")
    C.bp.boss_seal(0, PIT_F, BCZ, BOSS, 15)


def drum_and_dome(C):
    """Drum (windows, four doors onto the gallery from the roof), the gallery ring inside it on corbels, the pointed
    dome (azure tiles, sixteen brass ribs, a polished lining with gilded rings), the lantern and the finial; the great
    chandelier ring hung over the pit."""
    for x in range(-27, 28):
        for z in range(BCZ - 27, BCZ + 28):
            u, v = x, z - BCZ
            d = math.hypot(u, v)
            a = math.degrees(math.atan2(v, u)) % 360
            # the gallery (floor y 24, inside the drum) on corbels
            if 18.6 < d <= DRUM_IN:
                C.set(x, ROOF_B, z, PGS if (int(a) // 8) % 2 else GTILE)
                if d <= 19.7:
                    C.set(x, ROOF_B - 1, z, stair(PGS_ST, out_facing(u, v), "top"))
                    railing(C, x, ROOF_B + 1, z, out_facing(-u, -v))
                else:
                    C.set(x, ROOF_B - 1, z, GB)
            # the drum
            if DRUM_IN < d <= DRUM_OUT:
                door = min(abs(a - k) for k in (45, 135, 225, 315)) * math.pi / 180 * d < 1.6
                win = (a % 22.5) * math.pi / 180 * d
                win = 1.2 < win < 3.6
                for y in range(ROOF_B, DOME_Y):
                    if door and ROOF_B + 1 <= y <= ROOF_B + 3:
                        C.air(x, y, z)
                        continue
                    if win and 28 <= y <= 33 and not door:
                        C.set(x, y, z, "light_blue_stained_glass" if d > 24.3 else AIR)
                        continue
                    if y in (ROOF_B, DOME_Y - 1):
                        spec = BRASS
                    elif y in (27, 34):
                        spec = GILD if d > 24.3 else PGS
                    elif d > 24.3 and (a % 22.5) * math.pi / 180 * d < 1.0:
                        spec = BRASS
                    else:
                        spec = AZ if d > 24.3 and 28 <= y <= 33 else (GB if d > 24.3 else PGS)
                    C.set(x, y, z, spec)
                if door:
                    C.set(x, ROOF_B + 4, z, GILD)
                    C.set(x, ROOF_B, z, PGS)
    # the dome
    top = int(DOME_Y + DOME_H) + 1
    for y in range(DOME_Y, top + 1):
        ro = dome_r(y)
        if ro < 0:
            continue
        ri = ro - 2.0
        for x in range(-27, 28):
            for z in range(BCZ - 27, BCZ + 28):
                u, v = x, z - BCZ
                d = math.hypot(u, v)
                if d > ro + 0.35 or d <= ri - 0.35:
                    continue
                a = math.degrees(math.atan2(v, u)) % 22.5
                rib = min(a, 22.5 - a) * math.pi / 180 * max(d, 1) < 0.75
                outer = d > ro - 0.8
                if outer:
                    spec = BRASS if rib or y == DOME_Y else (BTILE if (y - DOME_Y) % 9 == 8 else AZ)
                else:
                    spec = GILD if (y - DOME_Y) % 8 == 4 else (AZ if rib else PGS)
                C.set(x, y, z, spec)
    # the lantern: a glazed drum on the crown, a small dome, a gilded orb and a rod
    ly0 = 68
    for x in range(-5, 6):
        for z in range(BCZ - 5, BCZ + 6):
            d = math.hypot(x, z - BCZ)
            for y in range(ly0, ly0 + 10):
                if 2.6 < d <= 3.7:
                    spec = (GLASS if 71 <= y <= 74 and (x + z) % 2 else BRASS if y in (ly0, ly0 + 9) else GB)
                    C.set(x, y, z, spec)
            for y in range(ly0 + 10, ly0 + 14):
                rr = 3.7 - (y - ly0 - 10) * 1.1
                if rr - 1.0 < d <= rr + 0.3:
                    C.set(x, y, z, VERD)
    for y in range(ly0 + 14, ly0 + 16):
        C.set(0, y, BCZ, BRASS)
    for (dx, dy, dz) in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
        C.set(dx, ly0 + 17 + dy, BCZ + dz, GILD)
    for y in range(ly0 + 19, ly0 + 22):
        C.set(0, y, BCZ, ROD_U if y == ly0 + 21 else IRON_WALL)
    # the great chandelier ring over the pit (y 30, radius 9), each lamp on a chain from the dome lining
    for k in range(12):
        a = math.radians(30 * k + 15)
        x, z = int(round(math.cos(a) * 9)), int(round(BCZ + math.sin(a) * 9))
        hang(C, x, 30, z, CHANDELIER, reach=60)
    for k in range(24):
        a = math.radians(15 * k)
        x, z = int(round(math.cos(a) * 9)), int(round(BCZ + math.sin(a) * 9))
        if C.free(x, 31, z):
            C.set(x, 31, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    hang(C, 0, 36, BCZ, SEA, reach=60)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(dx, 36, BCZ + dz, GILD)
        C.set(dx, 35, BCZ + dz, f"{CHAIN}")
        C.set(dx, 34, BCZ + dz, CHANDELIER)
    # lamps round the gallery
    for k in range(16):
        a = math.radians(22.5 * k + 11.25)
        x, z = int(round(math.cos(a) * 22.0)), int(round(BCZ + math.sin(a) * 22.0))
        C.set(x, ROOF_B + 2, z, EDISON) if C.solid(x, ROOF_B + 2, z) else None


def iwans(C):
    """Four iwans: a pishtaq projecting from each face (15 wide, to y 30) with a tiled frame round a pointed opening
    7 wide and 12 high that leads into the ambulatory; muqarnas in the hood."""
    arch = pointed(3.5, 11.0)
    for (fx, fz) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        for w in range(-8, 9):
            for k in range(29, 35):                    # depth from the axis (the face is at 32)
                x, z = (w, BCZ + fz * k) if fx == 0 else (fx * k, BCZ + w)
                for y in range(-2, 31):
                    opening = abs(w) <= 3 and 1 <= y <= int(arch(w)) and k <= 34
                    if opening:
                        if k >= 31:
                            C.air(x, y, z)
                        continue
                    if k <= 32:
                        if k >= 31 and abs(w) <= 4 and y <= int(arch(min(abs(w), 3.5))) + 1:
                            C.set(x, y, z, AZ if (y + w) % 2 else CGS)
                        continue                       # inside the base: already built
                    front = k == 34
                    if not (front or abs(w) == 8 or y <= 0 or y >= 29):
                        continue
                    aw = abs(w)
                    if y <= 0:
                        spec = stone(x, y, z, -6, 30, seed=15)
                    elif front and 4 <= aw <= 5 and y <= arch(min(aw, 3.5)) + 2.5:
                        spec = AZ if (y + aw) % 2 else "cyan_glazed_terracotta[facing=north]"
                    elif front and aw in (6, 7):
                        spec = AZ if aw == 7 else (GILD if y % 6 == 0 else CGS)
                    elif front and y in (28, 29, 30):
                        spec = PGS if y == 30 else AZ
                    elif front and y >= 17:
                        spec = "light_blue_glazed_terracotta[facing=north]" if (w + y) % 4 == 0 else PGS
                    else:
                        spec = stone(x, y, z, -6, 30, seed=15)
                    C.set(x, y, z, spec)
                if k >= 31:
                    C.set(x, 0, z, main_pave(x, z)) if abs(w) <= 3 else None
            # merlons on the crown
            x, z = (w, BCZ + fz * 34) if fx == 0 else (fx * 34, BCZ + w)
            if w % 2 == 0:
                C.set(x, 31, z, PGS)
        # muqarnas: upside-down stairs under the hood, lamps in the opening
        for k in range(31, 35):
            for w in range(-3, 4):
                x, z = (w, BCZ + fz * k) if fx == 0 else (fx * k, BCZ + w)
                t = int(arch(w))
                if abs(w) >= 1 and k % 2 == 0:
                    face = (("east" if w < 0 else "west") if fx == 0 else ("south" if w < 0 else "north"))
                    C.set(x, t, z, stair(PGS_ST, face, "top"))
        x, z = (0, BCZ + fz * 31) if fx == 0 else (fx * 31, BCZ)
        hang(C, x, 8, z, LANT_H)


def newel_write(C, cells, core, f0, tread=GB_ST, floor=PGS, fill=GB):
    top = max(f for f, _, _ in cells.values())
    for (x, z), (f, fc, _) in cells.items():
        for y in range(f, f + 4):
            C.air(x, y, z)
    for (x, z), (f, fc, _) in cells.items():
        C.set(x, f - 1, z, stair(tread, fc) if fc else floor)
        lo = f0 - 1 if f - 2 - f0 < 3 else f - 2
        for y in range(lo, f - 1):
            C.set(x, y, z, fill)
    cx0, cz0, cx1, cz1 = core
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(f0 - 1, top + 4):
                C.set(x, y, z, GB if (x in (cx0, cx1) or z in (cz0, cz1)) else GB)
    return top


def newels(C):
    """The corner newel stairs (NE climbs clockwise, NW anticlockwise) from the ambulatory to the roof terrace, each
    in its tower with a domed stair-house on the roof; Edison lamps set in the core."""
    for (x0, z0, start, cw) in newel_boxes():
        # the tower walls round the box (the base walls on the outside)
        for x in range(x0 - 1, x0 + 12):
            for z in range(z0 - 1, z0 + 12):
                if x0 <= x <= x0 + 10 and z0 <= z <= z0 + 10:
                    continue
                if max(abs(x), abs(z - BCZ)) >= 31:
                    for y in range(ROOF_B + 2, ROOF_B + 6):
                        C.set(x, y, z, stone(x, y, z, 0, ROOF_B + 8, seed=16))
                    continue
                for y in range(1, ROOF_B + 6):
                    C.set(x, y, z, stone(x, y, z, 0, ROOF_B + 8, seed=16))
        c, f = start, 1
        flights = [5, 5, 5, 5, 4]
        cells, core, c1, f1 = newel(x0, z0, 5, 1, flights[:3], c, cw)
        newel_write(C, cells, core, 1)
        cells2, core2, c2, f2 = newel(x0, z0, 5, f1, flights[3:], c1, cw)
        newel_write(C, cells2, core2, f1)
        # lamps on the core faces at the landings
        cx0, cz0, cx1, cz1 = core
        for y in (4, 9, 14, 19, 24):
            for (x, z) in ((cx0, (cz0 + cz1) // 2), (cx1, (cz0 + cz1) // 2), ((cx0 + cx1) // 2, cz0),
                           ((cx0 + cx1) // 2, cz1)):
                C.set(x, y, z, EDISON)
        # the stair-house roof over the box, a small azure dome
        for x in range(x0 - 1, x0 + 12):
            for z in range(z0 - 1, z0 + 12):
                C.set(x, ROOF_B + 6, z, PGS)
        cxh, czh = x0 + 5, z0 + 5
        for x in range(x0 - 1, x0 + 12):
            for z in range(z0 - 1, z0 + 12):
                for y in range(ROOF_B + 7, ROOF_B + 12):
                    dd = math.sqrt((x - cxh) ** 2 + (z - czh) ** 2 + ((y - ROOF_B - 7) * 1.3) ** 2)
                    if 4.6 < dd <= 5.8:
                        C.set(x, y, z, AZ)
        C.set(cxh, ROOF_B + 12, czh, GILD)
        C.set(cxh, ROOF_B + 13, czh, ROD_U)
        # bottom door (from the ambulatory) and top door (onto the roof)
        bx, bz = {0: (x0, z0), 1: (x0 + 8, z0), 2: (x0 + 8, z0 + 8), 3: (x0, z0 + 8)}[start]
        tx, tz = {0: (x0, z0), 1: (x0 + 8, z0), 2: (x0 + 8, z0 + 8), 3: (x0, z0 + 8)}[c2]
        # the bottom landing opens south (onto v = -19)
        for x in range(bx, bx + 3):
            for y in range(1, 4):
                C.air(x, y, z0 + 11)
        # the top landing opens toward the dome side (x0 - 1 for the NE box, x0 + 11 for the NW box)
        ox = x0 - 1 if cw else x0 + 11
        for z in range(tz, tz + 3):
            for y in range(f2, f2 + 3):
                C.air(ox, y, z)
            C.set(ox, f2 - 1, z, PGS)
        for x in range(bx, bx + 3):
            C.set(x, 0, z0 + 11, PGS)


def stall(C, x0, z0, x1, z1, face, goods, seed):
    """A bazaar stall: four posts, a striped awning, a counter on the front (``face``) with a gap, goods behind, a
    lantern under the awning."""
    col = CARPETS[int(hash01(x0, z0, seed) * 8)]
    col2 = ("white", "yellow", "light_gray")[int(hash01(z0, x0, seed) * 3)]
    for (x, z) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
        for y in range(1, 4):
            C.set(x, y, z, "spruce_fence")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 4, z, f"{col if (x + z) % 2 else col2}_wool")
    dx, dz = DV[face]
    if face in ("north", "south"):
        zc = z0 if face == "north" else z1
        cells = [(x, zc) for x in range(x0 + 1, x1)]
        back = [(x, z1 if face == "north" else z0) for x in range(x0 + 1, x1)]
    else:
        xc = x0 if face == "west" else x1
        cells = [(xc, z) for z in range(z0 + 1, z1)]
        back = [(x1 if face == "west" else x0, z) for z in range(z0 + 1, z1)]
    for i, (x, z) in enumerate(cells):
        if i == len(cells) // 2:
            continue
        C.set(x, 1, z, slab("spruce_slab", "top"))
    goods_at(C, back, goods, seed)
    hang(C, (x0 + x1) // 2, 3, (z0 + z1) // 2, LANT_H)


GOODS = {
    "carpets": lambda x, z, i: [f"{CARPETS[(i * 3) % 8]}_wool", f"{CARPETS[(i * 5 + 1) % 8]}_wool"],
    "lamps": lambda x, z, i: [BRASS, LANT],
    "spices": lambda x, z, i: [("barrel[facing=up,open=true]", "orange_terracotta", "yellow_terracotta",
                                "red_terracotta", "brown_terracotta")[i % 5], "flower_pot"],
    "pots": lambda x, z, i: [f"decorated_pot[cracked=false,facing=north,waterlogged=false]", None],
    "brass": lambda x, z, i: [("cauldron", BRASS, "bell[attachment=floor,facing=north,powered=false]", COPPER)[i % 4],
                              None],
    "fruit": lambda x, z, i: [("melon", "pumpkin", "hay_block[axis=y]", "cocoa_beans_block")[i % 3], None],
    "cloth": lambda x, z, i: [f"{CARPETS[(i * 7) % 8]}_wool", f"{CARPETS[(i * 2 + 3) % 8]}_carpet"],
    "gadgets": lambda x, z, i: [GEAR if i % 2 else GAUGE, f"{COG}[facing=north]" if False else None],
    "books": lambda x, z, i: ["bookshelf", "lectern[facing=north,has_book=false,powered=false]" if False else None],
    "potions": lambda x, z, i: ["brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]", None],
    "jewels": lambda x, z, i: ["gold_block" if i % 2 else "amethyst_block",
                               "amethyst_cluster[facing=up,waterlogged=false]"],
    "weapons": lambda x, z, i: ["spruce_fence", ROD_U],
}
GOOD_KINDS = list(GOODS)


def goods_at(C, cells, goods, seed):
    fn = GOODS[goods]
    for i, (x, z) in enumerate(cells):
        a, b = fn(x, z, i + seed)
        if a:
            C.set(x, 1, z, a)
        if b:
            C.set(x, 2, z, b)


def ambulatory(C):
    """Stalls round the ambulatory, chandeliers under its vault, lanterns under the ring arches, the money-changer's
    booth (the treasury lift's head), spawners."""
    stalls = [
        (22, BCZ + 22, 26, BCZ + 26, "west", "carpets"), (22, BCZ + 27, 26, BCZ + 30, "west", "lamps"),
        (27, BCZ + 22, 30, BCZ + 26, "north", "brass"),
        (-25, BCZ + 22, -22, BCZ + 26, "east", "jewels"),
        (27, BCZ - 12, 30, BCZ - 6, "west", "spices"), (27, BCZ + 6, 30, BCZ + 12, "west", "cloth"),
        (-30, BCZ - 12, -27, BCZ - 6, "east", "pots"), (-30, BCZ + 5, -27, BCZ + 10, "east", "gadgets"),
        (-14, BCZ - 30, -8, BCZ - 27, "south", "books"), (8, BCZ - 30, 14, BCZ - 27, "south", "potions"),
        (-12, BCZ + 27, -6, BCZ + 30, "north", "fruit"), (5, BCZ + 27, 11, BCZ + 30, "north", "weapons"),
    ]
    for i, (x0, z0, x1, z1, face, goods) in enumerate(stalls):
        stall(C, x0, z0, x1, z1, face, goods, i * 5)
    chest(C, 29, 1, BCZ + 29, "west", "bcv_bazaar")
    chest(C, -29, 1, BCZ - 9, "east", "bcv_bazaar")
    chest(C, 11, 1, BCZ - 29, "south", "bcv_bazaar")
    # lamps: chandeliers under the outer vault, lanterns from the arch crowns
    for k in range(32):
        a = math.radians(11.25 * k + 5.6)
        x, z = int(round(math.cos(a) * 28.3)), int(round(BCZ + math.sin(a) * 28.3))
        if C.free(x, 6, z) and C.free(x, 5, z) and C.free(x, 4, z):
            hang(C, x, 6, z, CHANDELIER if k % 2 else LANT_H)
    for k in range(8):
        a = math.radians(45 * k)
        x, z = int(round(math.cos(a) * 24.0)), int(round(BCZ + math.sin(a) * 24.0))
        if C.free(x, 10, z):
            hang(C, x, 10, z, LANT_H)
    for (x, z) in ((28, BCZ + 28), (-28, BCZ + 28), (0, BCZ + 28), (28, BCZ), (-28, BCZ), (0, BCZ - 28),
                   (28, BCZ - 28), (-28, BCZ - 28)):
        if C.free(x, 6, z) and C.free(x, 5, z):
            hang(C, x, 6, z, HANG_LAMP)
    # the money-changer's booth over the treasury lift (x 14 .. 19, z BCZ + 25 .. 30)
    bz0 = BCZ + 24
    for x in range(13, 21):
        for z in range(bz0, BCZ + 31):
            wall = x in (13, 20) or z == bz0
            for y in range(1, 6):
                if wall:
                    C.set(x, y, z, MAHOGANY if y < 5 else BTILE)
                elif y == 5:
                    C.set(x, y, z, BTILE)
                else:
                    C.air(x, y, z)
    iron_door(C, 17, 1, bz0, "north")
    lever(C, 18, 2, bz0 + 1, "south")
    C.set(16, 3, bz0, GRILLE)
    C.set(18, 3, bz0, GRILLE)
    C.set(19, 1, BCZ + 29, "gold_block")
    C.set(19, 1, BCZ + 28, f"{CHAIR}[facing=west]")
    C.set(18, 1, BCZ + 30, BRASS)
    C.set(18, 2, BCZ + 30, "lantern[hanging=false,waterlogged=false]")
    C.set(14, 1, BCZ + 30, f"lectern[facing=east,has_book=false,powered=false]")
    lamp_grid(C, -30, BCZ - 30, 30, BCZ + 30, 1, LANT_H, h=3, step=5,
              pred=lambda x, z: dB(x, z) > 27.0 and not in_newel(x, z, 1)
              and not (12 <= x <= 21 and z >= BCZ + 23) and not (-31 <= x <= -25 and BCZ + 12 <= z))
    spawner(C, -24, 1, BCZ + 8, MOB_BANDIT)
    spawner(C, 24, 1, BCZ - 9, MOB_RAIDER)
    spawner(C, 0, 1, BCZ - 28, MOB_BANDIT)
    # the gallery's guard
    spawner(C, -20, ROOF_B + 1, BCZ + 4, MOB_DRONE)


def undercroft(C):
    """The cistern ring under the ambulatory: a walkway round the pit wall, a water channel lit from below, columns
    under the piers, the lot hall to the north (cages, the site of grace), the auctioneers' stair up to the pit's north
    door, the conduit north to the garden cistern."""
    for x in range(-30, 31):
        for z in range(BCZ - 30, BCZ + 31):
            u, v = x, z - BCZ
            if not in_ring(u, v):
                continue
            d = math.hypot(u, v)
            for y in range(-14, CIS_F):
                C.set(x, y, z, "sandstone" if y < CIS_F - 1 else GB)
            chan = 25.4 <= d <= 27.2 and not (v < -16 and abs(u) < 14) and abs(v) > 2 and abs(u) > 2
            if chan:
                C.set(x, CIS_F - 2, z, SEA if (x + z) % 7 == 0 else GB)
                C.set(x, CIS_F - 1, z, WATER)
                C.set(x, CIS_F, z, WATER)
            else:
                C.set(x, CIS_F, z, PGS if (x + z) % 5 else GTILE)
            for y in range(CIS_F + 1, -2):
                C.air(x, y, z)
            C.set(x, -2, z, GB)
    # columns: under each pier and on a second ring
    pts = [(math.cos(a) * 24.0, math.sin(a) * 24.0) for a in PIERS]
    pts += [(math.cos(math.radians(45 * k)) * 28.6, math.sin(math.radians(45 * k)) * 28.6) for k in range(8)
            if k != 6]                                   # not on the north axis: the lot hall and its stair
    for (pu, pv) in pts:
        for x in range(int(pu) - 2, int(pu) + 3):
            for z in range(int(pv) - 2, int(pv) + 3):
                if math.hypot(x - pu, z - pv) <= 1.5 and in_ring(x, z):
                    for y in range(CIS_F + 1, -2):
                        C.set(x, y, BCZ + z, MARBLE if y not in (CIS_F + 1, -3) else CGS)
                    C.set(x, CIS_F + 3, BCZ + z, EDISON) if math.hypot(x - pu, z - pv) > 1.0 else None
    # lamps hung from the vault between the columns
    for k in range(16):
        a = math.radians(22.5 * k)
        x, z = int(round(math.cos(a) * 26.0)), int(round(math.sin(a) * 26.0))
        if in_ring(x, z) and C.free(x, -8, BCZ + z):
            hang(C, x, -8, BCZ + z, LANT_H)
    for k in range(16):
        a = math.radians(22.5 * k + 11.25)
        x, z = int(round(math.cos(a) * 23.6)), int(round(math.sin(a) * 23.6))
        if in_ring(x, z) and C.free(x, -8, BCZ + z):
            hang(C, x, -8, BCZ + z, LANT_H)
    for (u, v) in ((-24, 26), (-27, 20), (25, 22), (27, 27), (-20, 28), (-28, 28), (28, -28), (-28, -28)):
        if in_ring(u, v) and C.free(u, -8, BCZ + v):
            hang(C, u, -8, BCZ + v, LANT_H)
    # the lot hall (north, v -30 .. -23): cages of auction goods along the walls, crates, the site of grace
    for u in range(-12, 13, 4):
        if abs(u) <= 2:
            continue
        for y in range(CIS_F + 1, CIS_F + 4):
            C.set(u, y, BCZ - 30, BARS)
        C.set(u, CIS_F + 1, BCZ - 29, ("hay_block[axis=y]", "barrel[facing=up,open=false]", BRASS,
                                       "decorated_pot[cracked=false,facing=south,waterlogged=false]")[(u // 4) % 4])
    waystone(C, -6, CIS_F + 1, BCZ - 26)
    hang(C, -6, CIS_F + 4, BCZ - 24, LANT_H)
    hang(C, 6, CIS_F + 4, BCZ - 26, LANT_H)
    for u in (-11, 11):
        hang(C, u, CIS_F + 4, BCZ - 27, LANT_H)
    chest(C, 9, CIS_F + 1, BCZ - 29, "south", "bcv_cistern")
    # the auctioneers' stair: three treads up to the pit door (feet -8), side walls, a low ceiling (compression)
    for u in range(-2, 3):
        for v in range(-27, -22):
            x, z = u, BCZ + v
            if abs(u) == 2:
                for y in range(CIS_F + 1, PIT_F + 5):
                    C.set(x, y, z, DIB if y % 3 else BRASS)
                continue
            i = -27 + 3 - v                 # v -24 -> 0 ... no: computed below
    for k, v in enumerate((-26, -25, -24)):
        for u in range(-1, 2):
            x, z = u, BCZ + v
            top = CIS_F + 1 + k
            for y in range(CIS_F, top):
                C.set(x, y, z, GB)
            C.set(x, top, z, stair(GB_ST, "south"))
            for y in range(top + 1, top + 4):
                C.air(x, y, z)
            C.set(x, top + 4, z, PGS)
    for v in (-23, -22):
        for u in range(-1, 2):
            x, z = u, BCZ + v
            for y in range(CIS_F, PIT_F + 1):
                C.set(x, y, z, PGS)
            for y in range(PIT_F + 1, PIT_F + 4):
                C.air(x, y, z)
            C.set(x, PIT_F + 4, z, PGS)
        for u in (-2, 2):
            for y in range(PIT_F + 1, PIT_F + 5):
                C.set(u, y, BCZ + v, DIB)
    C.set(-2, PIT_F + 2, BCZ - 23, EDISON)
    C.set(2, PIT_F + 2, BCZ - 23, EDISON)
    # the conduit north to the garden cistern (x -2 .. 2), through the base wall and under the street
    for z in range(-57, BCZ - 29):
        for x in range(-2, 3):
            for y in range(-14, CIS_F):
                C.set(x, y, z, "sandstone")
            C.set(x, CIS_F, z, PGS if x else GTILE)
            for y in range(CIS_F + 1, CIS_F + 5):
                C.air(x, y, z)
            C.set(x, CIS_F + 5, z, GB)
        for x in (-3, 3):
            for y in range(CIS_F, CIS_F + 6):
                C.set(x, y, z, GB)
        if z % 4 == 0:
            C.set(-3, CIS_F + 3, z, EDISON)
    lamp_grid(C, -30, BCZ - 30, 30, BCZ + 30, CIS_F + 1, LANT_H, h=3, step=6,
              pred=lambda x, z: in_ring(x, z - BCZ) and not (abs(x) <= 2 and z - BCZ < -22))
    spawner(C, 26, CIS_F + 1, BCZ - 4, MOB_CRAWLER)
    spawner(C, -27, CIS_F + 1, BCZ + 8, MOB_MITE)


def treasury(C):
    """The merchant prince's strongroom behind the pit's sealed south door: gold, chests, a brass safe, carpets on
    racks, gem cases; the lift corridor east to the ladder shaft that rises to the money-changer's booth."""
    for x in range(-10, 11):
        for z in range(BCZ + 22, BCZ + 31):
            wall = abs(x) == 10 or z == BCZ + 22
            for y in range(-13, -1):
                if wall or y < PIT_F or y == -2:
                    if wall and z == BCZ + 22 and abs(x) <= 1 and PIT_F < y <= PIT_F + 3:
                        continue
                    C.set(x, y, z, DIB if wall or y == -2 else "sandstone")
                elif y == PIT_F:
                    C.set(x, y, z, BTILE if (x + z) % 2 else ENGR)
                else:
                    C.air(x, y, z)
    f = PIT_F + 1
    for x in (-8, -5, 5, 8):
        chest(C, x, f, BCZ + 30, "north", "bcv_treasury")
    for (x, z) in ((-9, 24), (-9, 25), (-8, 24), (9, 23), (8, 23), (9, 24), (-3, 30), (3, 30), (0, 30)):
        C.set(x, f, BCZ + z, "gold_block" if (x + z) % 3 else "raw_gold_block")
    for (x, z) in ((-9, 24), (9, 23)):
        C.set(x, f + 1, BCZ + z, "gold_block")
    # the safe: a brass block with a valve wheel, dark iron round it
    for x in range(-2, 3):
        for y in range(f, f + 4):
            C.set(x, y, BCZ + 30, DIB if abs(x) == 2 or y == f + 3 else BRASS)
    C.set(0, f + 1, BCZ + 29, f"{VALVE}[facing=north]")
    # gem cases and carpet racks along the side walls
    for z in range(BCZ + 24, BCZ + 30, 2):
        C.set(-9, f, z, "glass")
        C.set(-9, f + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
        if z + 1 != BCZ + 27:
            C.set(9, f, z + 1, f"{CARPETS[z % 8]}_wool")
            C.set(9, f + 1, z + 1, f"{CARPETS[(z + 3) % 8]}_wool")
    for (x, z) in ((-5, 26), (5, 26)):
        hang(C, x, f + 3, BCZ + z, CHANDELIER)
    # the lift corridor (x 10 .. 14, z BCZ + 27), the door holding the water, the column
    zc = BCZ + 27
    for x in range(10, 15):
        for z in (zc - 1, zc, zc + 1):
            for y in range(-13, 0):
                C.set(x, y, z, DIB)
        C.set(x, PIT_F, zc, BTILE)
        for y in range(PIT_F + 1, PIT_F + 4):
            C.air(x, y, zc)
    # the shaft: a ladder up to a hatch in the money-changer's booth floor
    for y in range(-13, 2):
        for (x, z) in ((16, zc), (15, zc - 1), (15, zc + 1), (16, zc - 1), (16, zc + 1), (14, zc - 1),
                       (14, zc + 1)):
            if y <= 0:
                C.set(x, y, z, DIB if y < -2 or y == 0 else "glass")
    C.set(16, 1, zc, BRASS)
    C.set(15, PIT_F, zc, BTILE)
    for y in range(PIT_F + 4, 1):
        C.set(14, y, zc, DIB)
    for y in range(PIT_F + 1, 2):
        C.set(15, y, zc, "ladder[facing=west,waterlogged=false]")
    C.set(12, f + 2, zc + 1, EDISON)


def porters_stair(C):
    """The porters' stair from the cistern ring's south-west end up to the ambulatory, in a stair-house whose iron door
    opens from the stair side only (a shortcut back from the undercroft)."""
    xs = range(-29, -26)
    for i in range(12):
        z = BCZ + 28 - i
        top = CIS_F + 1 + i
        for x in xs:
            for y in range(-14, top):
                C.set(x, y, z, GB)
            C.set(x, top, z, stair(GB_ST, "north"))
            for y in range(top + 1, top + 5):
                C.air(x, y, z)
    for z in (BCZ + 29, BCZ + 30):
        for x in xs:
            C.set(x, CIS_F, z, PGS)
            for y in range(CIS_F + 1, CIS_F + 5):
                C.air(x, y, z)
    for z in range(BCZ + 14, BCZ + 17):
        for x in xs:
            C.set(x, 0, z, PGS)
            for y in range(1, 5):
                C.air(x, y, z)
    # the stair-house round the top: walls x -30 / -26, z BCZ + 13 .. 30, a roof at y 5
    for x in range(-30, -25):
        for z in range(BCZ + 13, BCZ + 31):
            edge = x in (-30, -26) or z == BCZ + 13
            for y in range(1, 6):
                if edge or y == 5:
                    C.set(x, y, z, PGS if y == 5 else (GB if y < 4 else AZ))
            for y in range(-2, 1):
                if edge and C.free(x, y, z):
                    C.set(x, y, z, GB)
    iron_door(C, -28, 1, BCZ + 13, "north")
    lever(C, -27, 2, BCZ + 14, "south")
    hang(C, -28, 3, BCZ + 18, LANT_H)
    C.set(-30, -4, BCZ + 22, EDISON)
    C.set(-26, -6, BCZ + 25, EDISON)


# ------------------------------------------------------------------ the garden of four rivers
GX0, GZ0, GX1, GZ1 = GARDEN


def garden(C):
    """The prince's walled garden (x -30 .. 30, z -81 .. -54): cloisters east and west, the four rivers (cross
    channels) meeting at the brass fountain, beds of flowers and citrus under four palms, the well-head over the stair to
    the cistern, the garden waystone by the hall door; the gate to the bazaar opens from this side only."""
    busy(C, GX0, PAL_Z1, GX1, GZ1)
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            edge = x in (GX0, GX1) or z == GZ1
            if edge:
                for y in range(-2, 10):
                    C.set(x, y, z, stone(x, y, z, -2, 10, seed=17))
                C.set(x, 10, z, PGS if (x + z) % 2 == 0 else slab(PGS_SL))
                continue
            ax, az = abs(x), z
            cloister = ax >= 26
            if cloister:
                C.set(x, 0, z, GTILE if (x + z) % 2 else PGS)
                for y in range(1, 6):
                    C.air(x, y, z)
                C.set(x, 6, z, PGS)
                C.set(x, 7, z, AZ_SL + "[type=bottom,waterlogged=false]")
                if ax == 26:
                    pier = (z - GZ0) % 4 == 0
                    for y in range(1, 6):
                        if pier:
                            C.set(x, y, z, PGS if y < 5 else CGS)
                        elif y == 5:
                            C.set(x, y, z, stair(GB_ST, "east" if x < 0 else "west", "top"))
                    C.set(x, 7, z, stair(AZ_ST, "east" if x > 0 else "west"))
                continue
            # the parterre: paths, beds, the cross channels
            chan_ns = abs(x) <= 1 and -79 <= z <= -56
            chan_ew = abs(z + 68) <= 1 and abs(x) <= 21
            if chan_ns or chan_ew:
                C.set(x, -1, z, PGS)
                C.set(x, 0, z, WATER)
                for y in range(1, 4):
                    C.air(x, y, z)
                continue
            rim = abs(x) == 2 or (abs(z + 68) == 2 and abs(x) <= 21) or z in (GZ0, GZ1 - 1) or ax == 25
            path = rim or abs(x) in (3, 4) or abs(z + 68) in (3, 4) or z in (GZ0 + 1, GZ1 - 2) or ax in (23, 24)
            if rim:
                C.set(x, 0, z, CGS)
            elif path:
                C.set(x, 0, z, PGS if hash01(x, z, 101) < 0.8 else GTILE)
            else:
                C.set(x, 0, z, "grass_block[snowy=false]" if hash01(x, z, 102) < 0.85 else "moss_block")
                h = hash01(x, z, 103)
                if h < 0.32:
                    C.set(x, 1, z, ("red_tulip", "orange_tulip", "poppy", "dandelion", "allium", "cornflower",
                                    "oxeye_daisy", "azure_bluet")[int(h * 25) % 8])
                elif h < 0.38:
                    C.set(x, 1, z, "flowering_azalea")
            for y in range(1, 4):
                if C.free(x, y, z) and (x, y, z) not in C.keep:
                    C.air(x, y, z)
    # the fountain at the crossing: a round basin, a three-tier brass jet, lily pads
    fx, fz = 0, -68
    for x in range(-5, 6):
        for z in range(fz - 5, fz + 6):
            d = math.hypot(x - fx, z - fz)
            if d <= 3.6:
                C.set(x, -1, z, PGS)
                C.set(x, 0, z, WATER)
            elif d <= 4.6:
                C.set(x, 0, z, CGS)
                C.set(x, 1, z, slab(PGS_SL))
    C.set(fx, 0, fz, BRASS)
    C.set(fx, 1, fz, ENGR)
    C.set(fx, 2, fz, BRASS_SLAB + "[type=top,waterlogged=false]")
    C.set(fx, 3, fz, GILD)
    C.set(fx, 4, fz, "waxed_copper_bulb[lit=true,powered=false]")
    for (dx, dz) in ((2, 1), (-2, -1), (1, -2), (-1, 2)):
        C.set(fx + dx, 1, fz + dz, "lily_pad")
    # citrus and palms in the four beds; lamp posts at the path corners
    for (x, z) in ((-11, -75), (11, -75), (-11, -61), (11, -61)):
        planter_palm(C, x, z, 7 + int(hash01(x, z, 104) * 3), seed=x - z)
    for (x, z) in ((-7, -77), (7, -59), (-19, -62), (-7, -59), (7, -77), (-19, -76)):
        C.set(x, 1, z, "oak_log[axis=y]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                C.put(x + dx, 2, z + dz, "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
        C.put(x, 3, z, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    for (x, z) in ((-3, -71), (3, -71), (-3, -65), (3, -65), (-3, -79), (3, -79), (-3, -57), (3, -57),
                   (-23, -65), (23, -71), (-23, -79), (23, -57)):
        lamp_post(C, x, 1, z)
    for z in range(GZ0 + 2, GZ1 - 1, 8):
        for s in (-1, 1):
            hang(C, s * 28, 4, z, LANT_H)
    # benches in the cloisters
    for z in range(GZ0 + 2, GZ1 - 1, 4):
        for s in (-1, 1):
            C.set(s * 29, 1, z, stair(PGS_ST, "west" if s > 0 else "east"))
    # footbridges of brass over the north-south river
    for z in (-75, -61):
        for x in (-1, 0, 1):
            C.set(x, 1, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    # the gate to the bazaar street (z -54): iron door, lever on the garden side
    for x in range(-1, 2):
        for y in range(1, 4):
            C.air(x, y, GZ1)
    C.set(-1, 1, GZ1, stone(-1, 1, GZ1, -2, 10, seed=17))
    C.set(1, 1, GZ1, stone(1, 1, GZ1, -2, 10, seed=17))
    C.set(-1, 2, GZ1, stone(-1, 2, GZ1, -2, 10, seed=17))
    C.set(1, 2, GZ1, stone(1, 2, GZ1, -2, 10, seed=17))
    C.set(0, 3, GZ1, CGS)
    iron_door(C, 0, 1, GZ1, "south")
    lever(C, 1, 2, GZ1 - 1, "north")
    for x in range(-2, 3):
        C.set(x, 0, GZ1 - 1, PGS)
        C.set(x, 0, GZ1 + 1, PGS)
    # lamps under the bridge's arches
    for z in (-77, -67, -57):
        lamp_post(C, 16, 1, z, h=4)
    # the garden waystone by the hall door
    waystone(C, 5, 1, -79)
    chest(C, -29, 1, -60, "east", "bcv_garden")
    well_head(C)


def well_head(C):
    """The well-head (x -25 .. -21, z -75 .. -71): a copper canopy on four brass posts over the stair that drops 12
    to the cistern walkway, railed round its mouth."""
    for x in range(-26, -19):
        for z in range(-76, -59):
            C.set(x, 0, z, PGS if (x + z) % 3 else CGS)
            for y in range(1, 4):
                C.air(x, y, z)
    for k in range(12):
        z = -72 + k
        top = -1 - k
        for x in range(-24, -21):
            for y in range(CIS_F - 2, top):
                C.set(x, y, z, GB)
            C.set(x, top, z, stair(GB_ST, "north"))
            for y in range(top + 1, top + 5):
                C.air(x, y, z)
            if top + 5 <= 0:
                C.set(x, top + 5, z, GB)
        for x in (-25, -21):
            for y in range(top - 1, 1):
                C.set(x, y, z, GB if y % 4 else CGS)
            railing(C, x, 1, z, "west" if x == -25 else "east")
        if k in (4, 9):
            C.set(-25, top + 2, z, EDISON)
    for x in range(-25, -20):
        railing(C, x, 1, -60, "south")
        for y in range(CIS_F + 1, 1):
            if C.free(x, y, -60) and y > CIS_F + 4:
                C.set(x, y, -60, GB)
    for (x, z) in ((-25, -75), (-21, -75), (-25, -73), (-21, -73)):
        for y in range(1, 5):
            C.set(x, y, z, BRASS if y < 4 else ENGR)
    for x in range(-26, -19):
        for z in range(-76, -71):
            C.set(x, 5, z, slab("waxed_cut_copper_slab") if x in (-26, -20) or z in (-76, -72) else "waxed_cut_copper")
    hang(C, -23, 3, -74, LANT_H)
    C.set(-23, 6, -74, "waxed_lightning_rod[facing=up,powered=false,waterlogged=false]")
    # a bucket rope over the shaft: a chain from the canopy beam
    C.set(-23, 4, -73, CHAIN) if C.free(-23, 4, -73) else None


def garden_cistern(C):
    """The cistern under the garden (x -26 .. 26, z -80 .. -56): a hypostyle hall of marble columns standing in still
    water, causeways along the axes and walls, lamps on the columns; the conduit to the bazaar opens in its south
    wall."""
    x0, x1, z0, z1 = -26, 26, -80, -56
    cols = [(x, z) for x in (-20, -14, -8, 8, 14, 20) for z in (-76, -71, -64, -60)]
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(-14, CIS_F):
                C.set(x, y, z, "sandstone")
            if edge:
                for y in range(CIS_F, -1):
                    if not (z == z1 + 1 and abs(x) <= 2 and CIS_F < y <= CIS_F + 4):
                        C.set(x, y, z, GB if y % 5 else CGS)
                continue
            walk = (abs(x) <= 2 or abs(z + 68) <= 1 or x <= x0 + 1 or x >= x1 - 1 or z <= z0 + 1 or z >= z1 - 1
                    or (-24 <= x <= -22 and z >= -61))
            near_col = any(abs(x - cx) <= 1 and abs(z - cz) <= 1 for (cx, cz) in cols)
            if walk or near_col:
                C.set(x, CIS_F, z, PGS if (x + z) % 4 else GTILE)
                C.set(x, CIS_F - 1, z, GB)
            else:
                C.set(x, CIS_F - 2, z, SEA if hash01(x, z, 111) < 0.05 else GB)
                C.set(x, CIS_F - 1, z, WATER)
                C.set(x, CIS_F, z, WATER)
            for y in range(CIS_F + 1, -2):
                C.air(x, y, z)
            C.set(x, -2, z, GB)
    for (cx, cz) in cols:
        for y in range(CIS_F + 1, -2):
            C.set(cx, y, cz, MARBLE if y not in (CIS_F + 1, -3) else CGS)
        # an Edison lamp on the column's face toward the nearest causeway
        fx = 1 if abs(cx) < 26 and cx < 0 else -1
        C.set(cx, CIS_F + 3, cz, EDISON)
    for (x, z) in ((0, -76), (0, -70), (0, -64), (0, -58), (-6, -68), (6, -68), (-12, -68), (12, -68),
                   (-19, -68), (19, -68), (-25, -78), (25, -78), (25, -58), (-11, -79), (11, -79), (-11, -57),
                   (11, -57), (-25, -64), (25, -64), (-25, -72), (25, -72), (-18, -79), (18, -79), (-18, -57),
                   (18, -57)):
        hang(C, x, -8, z, LANT_H)
    for z in range(-79, -56, 6):
        C.set(-27, -9, z, EDISON)
        C.set(27, -9, z, EDISON)
    chest(C, 25, CIS_F + 1, -79, "west", "bcv_cistern")
    spawner(C, 18, CIS_F + 1, -68, MOB_CRAWLER)
    spawner(C, -12, CIS_F + 1, -68, MOB_MITE)
    # the pump: copper pipes rising from the water into the vault (toward the minaret chimneys)
    for y in range(CIS_F + 1, -2):
        C.set(24, y, -57, PIPE_Y)
    C.set(24, CIS_F + 1, -58, GAUGE)


# ------------------------------------------------------------------ the prince's bridge
BRX0, BRX1 = 13, 19


def bridge(C):
    """The Prince's Bridge: from the bazaar's north roof (deck y 24) north on three arches over the garden, then a
    flight down to the palace's east roof (y 15); railed, under a brass canopy on posts with hanging lamps."""
    def deck_y(z):
        if z >= -66:
            return ROOF_B
        if z >= -75:
            return ROOF_B + 67 + z                 # tread tops 24 .. 16
        return 15
    piers = [(-52, -51), (-62, -61), (-73, -72)]
    for z in range(-81, -46):
        dy = deck_y(z)
        tread = -75 <= z <= -67
        for x in range(BRX0, BRX1 + 1):
            edge = x in (BRX0, BRX1)
            if tread and not edge:
                C.set(x, dy, z, stair(BTILE_ST, "south"))
            else:
                C.set(x, dy, z, BTILE if not edge else ENGR)
            C.set(x, dy - 1, z, GB)
            for y in range(dy + 1, dy + 4):
                C.air(x, y, z)
            if edge:
                railing(C, x, dy + 1, z, "west" if x == BRX0 else "east")
            # piers, and the arch soffits between them
            pier = any(a <= z <= b for (a, b) in piers)
            if pier and z > -80:
                for y in range(0 if z > -54 else 1, dy - 1):
                    C.set(x, y, z, stone(x, y, z, 0, dy, seed=18) if not (edge and y % 6 == 3) else CGS)
            elif z > -80:
                spans = [(-50, -47), (-60, -53), (-71, -63), (-79, -74)]
                for (a, b) in spans:
                    if a <= z <= b:
                        half = (b - a + 1) / 2.0
                        off = abs(z - (a + b) / 2.0) / max(half, 1)
                        t = 1 + int(5 * off ** 2)
                        for y in range(dy - 1 - t, dy - 1):
                            C.set(x, y, z, GB if y > dy - 1 - t else AZ)
        # the canopy: brass posts every 4, a ribbed roof
        if (z + 81) % 4 == 0:
            for x in (BRX0, BRX1):
                for y in range(dy + 1, dy + 5):
                    C.set(x, y, z, BRASS if y < dy + 4 else ENGR)
        for x in range(BRX0, BRX1 + 1):
            cy = dy + 5 + (1 if BRX0 < x < BRX1 else 0) + (1 if x == (BRX0 + BRX1) // 2 else 0)
            C.set(x, cy, z, BTILE_SL + "[type=bottom,waterlogged=false]" if x in (BRX0, BRX1) else BTILE)
    for z in range(-79, -46, 3):
        dy = deck_y(z)
        hang(C, (BRX0 + BRX1) // 2 + (1 if z % 2 else -1), dy + 3, z, LANT_H)
    # break the bazaar parapet and the palace parapet where the bridge meets them
    for x in range(BRX0 + 1, BRX1):
        for z in (-48, -47):
            for y in range(ROOF_B + 1, ROOF_B + 4):
                C.air(x, y, z)
            C.set(x, ROOF_B, z, BTILE)
    busy(C, BRX0, -81, BRX1, -47)


# ------------------------------------------------------------------ the merchant prince's palace
PAL_Z0 = -104                 # the Divan's north wall
WING_Z0 = -98                 # the wings' north wall
UP_F = 8                      # wings' upper floor block y (feet 9)
WROOF = 15                    # wings' roof y (feet 16)
DIV_TOP = 21                  # the Divan's roof y
DIV_C = (0, -93)              # the Divan dome's axis


def ogive(R, y0, y):
    """Outer radius at y of a pointed dome of base radius R springing at y0 (-1 above the apex)."""
    rho = R * 1.4
    H = math.sqrt(rho ** 2 - (rho - R) ** 2)
    t = y - y0
    if t < 0 or t > H:
        return -1.0
    return (R - rho) + math.sqrt(rho * rho - t * t)


def palace(C):
    """The palace: the Divan (a domed audience hall with side galleries and imperial stairs, the throne under its
    brass clock), its tiled front on the garden; two wings of two storeys (east: counting house, kitchen, library,
    observatory; west: hammam, changing room, bedchamber, salon with its loggia); twin towers; the roof terraces where
    the Prince's Bridge lands."""
    busy(C, -53, PAL_Z0 - 2, 53, PAL_Z1)
    # --- shells
    for x in range(-44, 45):
        for z in range(PAL_Z0, PAL_Z1 + 1):
            ax = abs(x)
            if ax <= 13:
                edge = ax == 13 or z in (PAL_Z0, PAL_Z1)
                top = DIV_TOP
            else:
                if z < WING_Z0:
                    continue
                edge = ax == 44 or z in (WING_Z0, PAL_Z1) or ax == 28
                top = WROOF
            for y in range(-2 if edge else -1, top + 1):
                if edge or y <= 0 or y == top or (ax > 13 and y == UP_F):
                    C.set(x, y, z, stone(x, y, z, -6, top + 2, seed=19) if edge else
                          (PMARBLE if ax <= 13 and y == 0 else
                           PARQ if (y == UP_F + 0 and ax > 13 and False) else GB))
                elif not edge:
                    C.air(x, y, z)
            if ax > 13 and not edge:
                C.set(x, 0, z, "terracotta" if (x + z) % 2 else PMUD)
                C.set(x, UP_F, z, PARQ)
                C.set(x, WROOF, z, PGS if (x + z) % 5 else GTILE)
            if ax <= 13 and not edge:
                C.set(x, 0, z, PMARBLE if (x + z) % 2 else MARBLE)
                C.set(x, DIV_TOP, z, PGS)
            # parapets
            outer = (ax <= 13 and edge and ax != 28) or (ax > 13 and (ax == 44 or z in (WING_Z0, PAL_Z1)))
            if outer:
                C.set(x, top + 1, z, stone(x, top + 1, z, -6, top + 2, seed=19))
                if (x + z) % 2 == 0:
                    C.set(x, top + 2, z, PGS)
    # the Divan's hall: its roof opens into the drum and dome
    cx, cz = DIV_C
    for x in range(-12, 13):
        for z in range(PAL_Z0 + 1, PAL_Z1):
            if math.hypot(x - cx, z - cz) <= 9.5:
                C.air(x, DIV_TOP, z)
    divan(C)
    divan_dome(C)
    divan_front(C)
    east_wing(C)
    west_wing(C)
    for s in (-1, 1):
        palace_tower(C, s * 48, -88)
    # the bridge's landing: break the parapet of the east wing front
    for x in range(BRX0 + 1, BRX1):
        for y in (WROOF + 1, WROOF + 2):
            C.air(x, y, PAL_Z1)
        C.set(x, WROOF, PAL_Z1, BTILE)
    # lamps on the roof terraces
    for (x, z) in ((24, -84), (40, -96), (-24, -84), (-40, -96), (24, -96), (-24, -96)):
        lamp_post(C, x, WROOF + 1, z)


def divan(C):
    cx, cz = DIV_C
    # galleries (floor y 8) along the side walls, on columns, and the imperial stairs down from their south ends
    for s in (-1, 1):
        for z in range(PAL_Z0 + 1, -92):
            for ax in range(9, 13):
                x = s * ax
                C.set(x, UP_F, z, PARQ if ax > 9 else CGS)
                C.set(x, UP_F - 1, z, stair(PGS_ST, "west" if s > 0 else "east", "top") if ax == 9 else MAHOGANY)
                for y in range(UP_F + 1, UP_F + 4):
                    C.air(x, y, z)
            railing(C, s * 9, UP_F + 1, z, "west" if s > 0 else "east")
            if z in (-101, -97, -94):
                for y in range(1, UP_F - 1):
                    C.set(s * 9, y, z, PMARBLE if y not in (1, UP_F - 2) else CGS)
        for i in range(8):
            z = -92 + i
            top = UP_F - 1 - i
            for ax in range(10, 13):
                x = s * ax
                for y in range(1, top):
                    C.set(x, y, z, GB)
                C.set(x, top, z, stair(PGS_ST, "north") if top > 0 else PMARBLE)
                for y in range(top + 1, top + 4):
                    C.air(x, y, z)
            C.set(s * 9, top, z, slab(PGS_SL, "top") if top > 1 else PGS) if top > 0 else None
            railing(C, s * 9, top + 1, z, "west" if s > 0 else "east") if top > 0 else None
        # doors: gallery -> upper wing, hall -> ground wing
        C.air(s * 13, UP_F + 1, -96)
        C.air(s * 13, UP_F + 2, -96)
        wood_door(C, s * 13, UP_F + 1, -96, "east" if s > 0 else "west", wood="dark_oak")
        wood_door(C, s * 13, 1, -96, "east" if s > 0 else "west", wood="dark_oak")
        # lamps under the galleries and on the walls
        for z in (-102, -99, -95):
            hang(C, s * 11, UP_F - 3, z, LANT_H)
        for z in (-101, -97, -94):
            hang(C, s * 11, UP_F + 4, z, LANT_H, reach=20)
        for z in (-101, -91, -86):
            C.set(s * 13, 4, z, EDISON)
        for z in range(-101, -84, 4):
            for y in (16, 17, 18):
                C.set(s * 13, y, z, "light_blue_stained_glass_pane" if y != 17 else PANE)
    # the throne dais and the brass clock
    for x in range(-5, 6):
        for z in range(PAL_Z0 + 1, -98):
            C.set(x, 1, z, PGS if z < -99 else stair(PGS_ST, "north"))
            if z < -99:
                C.set(x, 2, z, slab(PGS_SL) if abs(x) > 1 else f"{CARPETS[0]}_carpet")
    C.set(0, 2, -102, GILD)
    C.set(0, 3, -102, f"{CHAIR}[facing=south]")
    for (x, z) in ((-2, -101), (2, -101)):
        for y in range(2, 7):
            C.set(x, y, z, IRON_WALL if y < 6 else BRASS)
    for x in range(-2, 3):
        for z in range(-103, -100):
            C.set(x, 7, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    for x in range(-7, 8):
        for y in range(4, 19):
            d = math.hypot(x, y - 11)
            if d <= 7.2:
                spec = GEAR if d > 5.8 else (BTILE if d > 2.0 else GILD)
                if 5.8 < d and (round(math.degrees(math.atan2(y - 11, x))) // 20) % 2 == 0:
                    spec = BRASS
                C.set(x, y, PAL_Z0, spec)
    for k in range(5):
        C.set(0, 12 + k, PAL_Z0 + 1, IRON_WALL) if False else None
    for (x, y) in ((0, 12), (0, 13), (0, 14), (1, 11), (2, 11), (3, 11)):
        C.set(x, y, PAL_Z0 + 1, IRON_WALL if (x, y) != (0, 14) else ENGR) if False else None
    C.set(0, 11, PAL_Z0 + 1, f"{COG}[facing=south]")
    for (x, z) in ((-4, -102), (4, -102)):
        C.set(x, 2, z, BRASS)
        C.set(x, 3, z, LANT)
    # the carpet runner, standing lamps along it, the prince's petitioners' benches
    for z in range(-98, PAL_Z1):
        for x in range(-2, 3):
            C.set(x, 1, z, ("yellow_carpet" if abs(x) == 2 else "red_carpet"))
    for z in (-96, -90, -85):
        for s in (-1, 1):
            C.set(s * 4, 1, z, CGS)
            C.set(s * 4, 2, z, LANT)
    for z in range(-97, -86, 3):
        for s in (-1, 1):
            C.set(s * 7, 1, z, stair(MAHOGANY_ST, "east" if s > 0 else "west"))
            C.set(s * 7, 1, z + 1, stair(MAHOGANY_ST, "east" if s > 0 else "west"))
    # chandeliers down from the dome on long chains
    for k in range(6):
        a = math.radians(60 * k)
        hang(C, int(round(cx + math.cos(a) * 5)), 6, int(round(cz + math.sin(a) * 5)), CHANDELIER, reach=40)
    hang(C, cx, 8, cz, CHANDELIER, reach=40)
    for z in (-101, -97, -94, -90, -86):
        for s in (-1, 1):
            if C.free(s * 6, 4, z) and C.free(s * 6, 5, z):
                hang(C, s * 6, 4, z, LANT_H, reach=40)
    spawner(C, 11, UP_F + 1, -102, MOB_GUNNER)
    spawner(C, -6, 1, -100, MOB_BANDIT)


MAHOGANY_ST = W + "mahogany_panelling_stairs"


def divan_dome(C):
    """The drum (windows) and the pointed dome of the Divan: azure tiles, brass ribs, a gilded lantern."""
    cx, cz = DIV_C
    R = 10.5
    for x in range(-12, 13):
        for z in range(cz - 12, cz + 13):
            d = math.hypot(x - cx, z - cz)
            a = math.degrees(math.atan2(z - cz, x - cx))
            for y in range(DIV_TOP + 1, DIV_TOP + 7):
                if 9.5 < d <= R + 0.3:
                    win = (a % 30) * math.pi / 180 * d
                    if 2.0 < win < 4.0 and DIV_TOP + 2 <= y <= DIV_TOP + 5:
                        C.set(x, y, z, "light_blue_stained_glass")
                    else:
                        C.set(x, y, z, BRASS if y in (DIV_TOP + 1, DIV_TOP + 6) else GB)
            y0 = DIV_TOP + 7
            for y in range(y0, y0 + 16):
                ro = ogive(R, y0, y)
                if ro < 0:
                    continue
                if ro - 1.5 < d <= ro + 0.35:
                    rib = (a % 30 < 2.5 * 30 / max(d * 2.0, 1)) or y == y0
                    C.set(x, y, z, BRASS if rib else (BTILE if (y - y0) % 6 == 5 else AZ))
    top = DIV_TOP + 7 + int(10.5 * math.sqrt(1.96 - 0.16))
    for y in range(top, top + 3):
        C.set(cx, y, cz, GILD if y == top + 1 else BRASS)
    C.set(cx, top + 3, cz, ROD_U)


def divan_front(C):
    """The Divan's front on the garden (z -82): a tiled pishtaq to y 32 with a pointed blind arch, a window grille and
    the hall door; brass lamps either side."""
    arch = pointed(6.5, 20.0)
    z = PAL_Z1
    for x in range(-13, 14):
        ax = abs(x)
        for y in range(1, 33):
            rim = arch(min(ax, 6.5))
            inside = ax <= 6 and y <= rim
            if inside:
                if ax <= 1 and y <= 5:
                    C.air(x, y, z)
                    continue
                if ax <= 4 and 9 <= y <= 15:
                    spec = GRILLE
                elif y == 6 or y == 7 and ax <= 2:
                    spec = CGS
                else:
                    spec = "light_blue_glazed_terracotta[facing=north]" if (x + y) % 3 == 0 else PGS
            elif ax <= 8 and y <= rim + 2:
                spec = AZ if (y + ax) % 2 else "cyan_glazed_terracotta[facing=north]"
            elif ax in (11, 12) or y >= 30:
                spec = AZ if (ax == 11 or y == 30) else PGS
            else:
                spec = GB if y % 6 else CGS
            C.set(x, y, z, spec)
        if ax % 2 == 0:
            C.set(x, 33, z, PGS)
    for s in (-1, 1):
        C.set(s * 13, 33, z, BRASS)
        C.set(s * 13, 34, z, GILD)
        C.set(s * 13, 35, z, ROD_U)
        C.set(s * 3, 4, z + 1, EDISON)
    for x in (-1, 1):
        for y in range(1, 6):
            C.set(x, y, z, GRILLE if y > 2 else CGS)
    for y in range(3, 6):
        C.set(0, y, z, GRILLE)
    wood_door(C, 0, 1, z, "south", wood="dark_oak")
    for x in range(-2, 3):
        C.set(x, 0, z, PGS)


def wing_shell_windows(C, s):
    """Windows: grilles on the ground floor, panes upstairs, in both long walls."""
    for x in range(16, 43, 4):
        if x == 28:
            continue
        X = s * x
        for (y0, spec) in ((2, GRILLE), (10, PANE)):
            if (X, y0, PAL_Z1) in C.keep:
                continue
            C.set(X, y0, PAL_Z1, spec)
            C.set(X, y0 + 1, PAL_Z1, spec)
            C.set(X, y0, WING_Z0, spec if y0 > 2 else C.get(X, y0, WING_Z0))


def east_wing(C):
    s = 1
    wing_shell_windows(C, s)
    for y in (1, UP_F + 1):
        wood_door(C, 28, y, -90, "east", wood="dark_oak")
    # the roof stair: from the bridge landing (z -83) down to the library floor (z -90)
    for k in range(7):
        z = -84 - k
        top = WROOF - k
        for x in range(15, 18):
            for y in range(UP_F + 1, top):
                C.set(x, y, z, GB)
            C.set(x, top, z, stair(GB_ST, "south"))
            for y in range(top + 1, top + 5):
                C.air(x, y, z)
        for x in (14, 18):
            for y in range(UP_F + 1, WROOF + 5):
                C.set(x, y, z, GB if y <= WROOF else (PGS if y == WROOF + 4 else GB))
    for x in range(14, 19):
        for y in range(WROOF + 1, WROOF + 5):
            C.set(x, y, -89, GB if y < WROOF + 4 else PGS)
        for z in range(-89, -82):
            C.set(x, WROOF + 5, z, AZ_SL + "[type=bottom,waterlogged=false]")
            if 14 < x < 18 and z <= -83:
                C.set(x, WROOF + 4, z, PGS) if z == -89 else None
    for x in (14, 18):
        for y in range(WROOF + 1, WROOF + 5):
            C.set(x, y, -83, GB)
    for x in range(15, 18):
        C.set(x, WROOF + 4, -83, PGS)
        for y in range(WROOF + 1, WROOF + 4):
            C.air(x, y, -83)
        C.set(x, WROOF, -83, PGS)
        C.set(x, UP_F, -91, PARQ)
        for y in range(UP_F + 1, UP_F + 4):
            C.air(x, y, -91)
    hang(C, 16, WROOF + 3, -86, LANT_H)
    for z in (-85, -88):
        C.set(14, WROOF - 2, z, EDISON) if False else None
    C.set(18, 12, -86, EDISON)
    C.set(14, 12, -88, EDISON)
    # counting house (ground, x 14 .. 27)
    furnish(C, 14, -97, 27, -83, 1, "money", "bcv_counting", clear=[(14, -96), (27, -90)], seed=301)
    for z in (-93, -87):
        for x in (18, 23):
            C.set(x, 1, z, TABLE)
            C.set(x, 2, z, "candle[candles=2,lit=true,waterlogged=false]")
            C.set(x, 1, z + 1, f"{CHAIR}[facing=north]")
    for x in range(19, 23):
        C.set(x, 1, -90, GOLD_COUNTER)
    spawner(C, 21, 1, -95, MOB_BANDIT)
    # kitchen (ground, x 29 .. 43)
    furnish(C, 29, -97, 43, -83, 1, "kitchen", "bcv_palace", clear=[(29, -90)], seed=302)
    for x in range(34, 39):
        C.set(x, 1, -90, slab("spruce_slab", "top") if x % 2 else TABLE)
    for (x, z) in ((32, -96), (40, -96)):
        for y in range(1, WROOF):
            if C.free(x, y, z) or y in (UP_F,):
                C.set(x, y, z, SMOKE if y != UP_F else SMOKE)
    # library (upper, x 14 .. 27)
    library(C)
    observatory(C)


GOLD_COUNTER = BRASS_SLAB + "[type=top,waterlogged=false]"


def library(C):
    f = UP_F + 1
    x0, x1, z0, z1 = 19, 27, -97, -83
    for z in range(z0, z1 + 1):
        for x in (x1,):
            if z in (-90,):
                continue
            for y in range(f, f + 5):
                C.set(x, y, z, "bookshelf" if y < f + 4 else MAHOGANY)
    for x in range(14, x1):
        if x == 16:
            continue
        for y in range(f, f + 5):
            C.set(x, y, z0, "bookshelf" if y < f + 4 else MAHOGANY)
    for z in range(-97, -91):
        if z == -96:
            continue
        for y in range(f, f + 4):
            C.set(14, y, z, "chiseled_bookshelf[facing=east]" if (y + z) % 3 == 0 else "bookshelf")
    # two reading tables, lecterns, a brass celestial globe, a ladder up the stacks
    for (tx, tz) in ((21, -94), (21, -86)):
        for x in range(tx, tx + 4):
            C.set(x, f, tz, TABLE)
            C.set(x, f, tz - 1, f"{CHAIR}[facing=south]")
            C.set(x, f, tz + 1, f"{CHAIR}[facing=north]")
        candle(C, tx + 1, f + 1, tz, 3, "yellow")
        C.set(tx + 3, f + 1, tz, "lantern[hanging=false,waterlogged=false]")
    C.set(25, f, -90, "lectern[facing=west,has_book=false,powered=false]")
    C.set(20, f, -90, "lectern[facing=east,has_book=false,powered=false]")
    C.set(23, f, -90, IRON)
    C.set(23, f + 1, -90, BRASS)
    for (dx, dy, dz) in ((1, 2, 0), (-1, 2, 0), (0, 2, 1), (0, 2, -1), (0, 3, 0)):
        C.set(23 + dx, f + dy, -90 + dz, VERD if (dx + dz) % 2 else COPPER)
    C.set(23, f + 2, -90, GILD)
    for y in range(f, f + 4):
        C.set(26, y, -84, "ladder[facing=west,waterlogged=false]") if False else None
    chest(C, 26, f, -96, "west", "bcv_library")
    lamp_grid(C, 19, -97, 27, -83, f, CHANDELIER, h=3, step=5)
    spawner(C, 25, f, -87, MOB_SPIDER)


def observatory(C):
    f = UP_F + 1
    ocx, ocz = 36, -90
    # open the ceiling into a dome on the roof
    for x in range(29, 44):
        for z in range(-97, -82):
            d = math.hypot(x - ocx, z - ocz)
            if d <= 5.5:
                C.air(x, WROOF, z)
    for x in range(28, 45):
        for z in range(-99, -81):
            d = math.hypot(x - ocx, z - ocz)
            a = math.degrees(math.atan2(z - ocz, x - ocx))
            for y in range(WROOF + 1, WROOF + 12):
                rr = math.sqrt(max(0.0, d * d + max(0, y - WROOF - 3) ** 2 * 1.0))
                if y <= WROOF + 3:
                    if 5.5 < d <= 6.7:
                        C.set(x, y, z, BRASS if y == WROOF + 3 else GB)
                    elif d <= 5.5:
                        C.air(x, y, z)
                    continue
                if 5.6 < rr <= 6.8:
                    slit = abs(x - ocx) <= 0 and z > ocz
                    C.set(x, y, z, AIR if slit else (VERD if (int(a) // 30) % 2 else COPPER))
                elif rr <= 5.6:
                    C.air(x, y, z)
    # the telescope: a brass tube on an iron mount, aimed through the slit
    C.set(36, f, -90, IRON)
    C.set(36, f + 1, -90, IRON_WALL)
    C.set(36, f + 2, -90, GEAR)
    for i in range(-3, 6):
        x, y, z = 36, f + 3 + int(i * 0.8), -90 + i
        C.set(x, y, z, BRASS if i not in (-3, 5) else ENGR)
    # star tables, an orrery of gears on the wall, a chart chest
    for (x, z) in ((31, -95), (31, -85), (41, -95), (41, -85)):
        C.set(x, f, z, "cartography_table")
    C.set(41, f, -90, "lectern[facing=west,has_book=false,powered=false]")
    for (dy, dz, spec) in ((2, 0, GEAR), (3, 1, f"{COG}[facing=east]"), (1, -1, f"{COG}[facing=east]")):
        C.set(30, f + dy, -90 + dz, spec) if False else None
    for (x, z) in ((43, -93), (43, -87)):
        for y in (f + 1, f + 2):
            C.set(x + 1, y, z, GEAR) if False else None
    for (y, z) in ((f + 2, -91), (f + 3, -89), (f + 1, -88)):
        C.set(43, y, z, f"{COG}[facing=west]")
    chest(C, 42, f, -96, "north", "bcv_library")
    for y in range(f, f + 3):
        C.set(29, y, -97, "bookshelf")
        C.set(30, y, -97, "bookshelf")
    for (x, z) in ((31, -90), (41, -88), (36, -95), (36, -85), (31, -95), (41, -95), (31, -85), (41, -85)):
        if C.free(x, f + 3, z):
            hang(C, x, f + 3, z, HANG_LAMP)
    spawner(C, 39, f, -93, MOB_DRONE)


def west_wing(C):
    s = -1
    wing_shell_windows(C, s)
    for y in (1, UP_F + 1):
        wood_door(C, -28, y, -90, "west", wood="dark_oak")
    hammam(C)
    # changing room (ground, x -43 .. -29): benches, towels, a fountain basin
    f = 1
    for x in range(-43, -28):
        for z in (-97, -83):
            if x % 3:
                C.set(x, f, z, stair(PGS_ST, "south" if z == -97 else "north"))
    for z in range(-96, -83):
        if z % 3:
            C.set(-43, f, z, stair(PGS_ST, "east"))
    for (x, z) in ((-41, -96), (-40, -96), (-41, -84), (-35, -84)):
        C.set(x, f, z, "white_wool")
        C.set(x, f + 1, z, "white_carpet")
    C.set(-36, f, -90, PMARBLE)
    C.set(-36, f + 1, -90, "water_cauldron[level=3]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(-36 + dx, f, -90 + dz, slab(PGS_SL))
    lamp_grid(C, -43, -97, -29, -83, f, CHANDELIER, h=3, step=5)
    chest(C, -30, f, -96, "east", "bcv_hammam")
    for x in (-38, -33):
        C.set(x, 3, -98, EDISON)
    # bedchamber (upper, x -27 .. -14)
    f = UP_F + 1
    bx, bz = -21, -95
    for x in range(bx - 2, bx + 3):
        for z in range(bz - 2, bz + 4):
            C.set(x, f, z, f"{'purple' if abs(x - bx) == 2 or z in (bz - 2, bz + 3) else 'magenta'}_carpet")
    C.bp.bed(bx, f, bz + 1, "north", color="red")
    C.bp.bed(bx + 1, f, bz + 1, "north", color="red")
    for (x, z) in ((bx - 1, bz - 1), (bx + 2, bz - 1), (bx - 1, bz + 2), (bx + 2, bz + 2)):
        for y in range(f, f + 4):
            C.set(x, y, z, "dark_oak_fence" if y < f + 3 else BRASS)
    for x in range(bx - 1, bx + 3):
        for z in range(bz - 1, bz + 3):
            C.set(x, f + 4, z, "red_wool" if (x + z) % 2 else "yellow_wool")
    for (x, z, tok) in ((-26, -96, "barrel"), (-26, -95, "bookshelf"), (-26, -94, "barrel"), (-15, -96, "shelf"),
                        (-15, -84, "flower"), (-26, -84, "pot"), (-15, -94, "candle"), (-26, -88, "chest")):
        put_item(C, x, f, z, "west" if x == -26 else "east", tok, "bcv_apartments", 303)
    C.set(-17, f, -88, TABLE)
    C.set(-17, f + 1, -88, "lantern[hanging=false,waterlogged=false]")
    C.set(-18, f, -88, f"{CHAIR}[facing=east]")
    lamp_grid(C, -27, -97, -14, -83, f, CHANDELIER, h=3, step=5)
    # salon with its loggia (upper, x -43 .. -29)
    for x in range(-42, -29):
        pier = (x + 42) % 4 == 0
        for y in range(f, f + 5):
            if pier:
                C.set(x, y, PAL_Z1, PMARBLE if y < f + 4 else CGS)
            elif y == f + 4:
                C.set(x, y, PAL_Z1, stair(PGS_ST, "south", "top"))
            else:
                C.air(x, y, PAL_Z1)
        if not pier:
            railing(C, x, f, PAL_Z1, "south")
    for x in range(-42, -29):
        if x % 4:
            C.set(x, f, -96, stair(MAHOGANY_ST, "south"))
    for z in range(-95, -85):
        if z % 4:
            C.set(-43, f, z, stair(MAHOGANY_ST, "east"))
    for (x, z) in ((-38, -90), (-33, -90)):
        C.set(x, f, z, TABLE)
        C.set(x, f + 1, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            C.set(x + dx, f, z + dz, f"{CARPETS[(x + dx * 3 + dz) % 8]}_carpet")
    lamp_grid(C, -43, -97, -29, -84, f, CHANDELIER, h=3, step=5)
    C.set(-30, f, -96, "jukebox[has_record=false]")
    spawner(C, -36, f, -86, MOB_BANDIT)


def hammam(C):
    """The hot room (x -27 .. -14, ground): a polished marble floor, the heated octagon in the middle, marble basins
    along the walls, a cold plunge pool, copper pipes from the boiler, steam vents."""
    f = 1
    cxh, czh = -20, -90
    for x in range(-27, -13):
        for z in range(-97, -82):
            C.set(x, 0, z, PMARBLE if (x + z) % 2 else MARBLE)
            d = math.hypot(x - cxh, z - czh)
            if d <= 3.2:
                C.set(x, f, z, PMARBLE if d > 1.0 else GILD)
    for z in range(-94, -84, 3):
        for x in (-27, -14):
            C.set(x, f, z, "water_cauldron[level=3]")
    for x in range(-26, -22):
        for z in range(-96, -93):
            C.set(x, 0, z, WATER)
            C.set(x, -1, z, MARBLE)
    for x in range(-27, -21):
        for z in (-97, -92):
            if C.get(x, 0, z) != WATER and C.free(x, f, z):
                C.set(x, f, z, slab(PGS_SL))
    for y in range(f, UP_F):
        C.set(-15, y, -97, PIPE_Y)
        C.set(-15, y, -83, PIPE_Y)
    C.set(-16, f, -97, GAUGE)
    for (x, z) in ((-24, -86), (-17, -86), (-17, -93)):
        C.set(x, f, z, f"{W}copper_grate" if False else "waxed_copper_grate")
    lamp_grid(C, -27, -97, -14, -83, f, LANT_H, h=3, step=5)
    for (x, z) in ((-27, -90), (-14, -88)):
        C.set(x, 4, z, "waxed_copper_bulb[lit=true,powered=false]") if C.solid(x, 4, z) else None
    spawner(C, -20, f, -84, MOB_SCARAB)


def palace_tower(C, cx, cz):
    """A slender corner tower: a round shaft with banded tiles and lancet windows to y 34, a gilded balcony ring, an
    azure onion cap and a brass finial."""
    r = 4.2
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            a = math.degrees(math.atan2(z - cz, x - cx))
            if d <= r + 0.3:
                for y in range(-4, 35):
                    if d > r - 1.0:
                        win = y in (8, 9, 18, 19, 27, 28) and (int(a + 360) // 45) % 2 == 0 and d > r - 0.5
                        spec = (PANE if win else AZ if y % 9 == 0 else GB if y > 2 else MUD)
                        C.set(x, y, z, spec)
                    elif y <= 0:
                        C.set(x, y, z, GB)
                    elif y < 34:
                        C.air(x, y, z)
            if r - 0.5 < d <= r + 1.4:
                C.set(x, 34, z, GILD if d > r + 0.5 else BRASS)
                if d > r + 0.5:
                    railing(C, x, 35, z, out_facing(x - cx, z - cz))
            for y in range(35, 45):
                rr = r * (1.0 + 0.25 * math.sin(min(1.0, (y - 35) / 3.0) * math.pi / 2)) * (
                    1.0 if y < 38 else max(0.0, 1.0 - ((y - 38) / 6.5) ** 1.6))
                if rr - 1.0 < d <= rr + 0.3 and d <= r + 1.2 and not (y < 36):
                    C.set(x, y, z, AZ if (int(a + 360) // 30) % 2 else BRASS)
    C.set(cx, 45, cz, GILD)
    C.set(cx, 46, cz, ROD_U)


# ------------------------------------------------------------------ the covered souk
LANE = (43, 45)               # the open lane between alleys C and A (x range)


def AB(axis, a, b):
    return (a, b) if axis == "x" else (b, a)


def souk_floor(x, z):
    h = hash01(x, z, 121)
    if (x + z) % 9 == 0:
        return GTILE
    return PGS if h < 0.55 else ("terracotta" if h < 0.8 else MUD)


def alley(C, axis, a0, a1, b0, b1):
    """A vaulted alley (interior b0 .. b1 across, a0 .. a1 along): paving, a pointed vault on stepped stairs, a tiled
    roof, a skylight every ten blocks, lanterns from the crown."""
    lo_face, hi_face = ("north", "south") if axis == "x" else ("west", "east")
    for a in range(a0, a1 + 1):
        for b in range(b0, b1 + 1):
            x, z = AB(axis, a, b)
            C.set(x, 0, z, souk_floor(x, z))
            edge = b in (b0, b1)
            for y in range(1, 6 if edge else 7):
                C.air(x, y, z)
            if edge:
                C.set(x, 6, z, stair(PGS_ST, hi_face if b == b0 else lo_face, "top"))
                C.set(x, 7, z, GB)
            else:
                C.set(x, 7, z, GLASS if (a - a0) % 10 == 5 else (CGS if (a - a0) % 5 == 0 else PGS))
            C.set(x, 8, z, TERRA_SL + "[type=bottom,waterlogged=false]" if edge else TERRA)
        if (a - a0) % 6 == 2:
            x, z = AB(axis, a, (b0 + b1) // 2)
            hang(C, x, 5, z, LANT_H)
    busy(C, *(AB(axis, a0, b0) + AB(axis, a1, b1)))


def shop(C, axis, a0, side, bf, kind, seed, table=None, mob=None):
    """A shop 4 wide (a0 .. a0 + 3) and 4 deep from its open front row bf (side +1 / -1 away from the alley): walls,
    a counter with a gap, goods along the back, a lantern; a chest or a spawner in a few."""
    bb = bf + side * 4                      # back wall
    cells = []
    for a in range(a0 - 1, a0 + 5):
        for k in range(0, 5):
            b = bf + side * k
            x, z = AB(axis, a, b)
            wall = a in (a0 - 1, a0 + 4) or b == bb
            for y in range(-1, 8):
                if wall and y <= 5:
                    C.set(x, y, z, house_stone(x, y, z, seed) if y > 0 else GB)
                elif y == 0:
                    C.set(x, y, z, PMUD if (x + z) % 2 else "terracotta")
                elif y <= 4 and not wall:
                    C.air(x, y, z)
                elif y == 5:
                    C.set(x, y, z, "spruce_planks" if (a + b) % 3 else "stripped_spruce_log[axis=y]")
                elif y == 6:
                    C.set(x, y, z, GB)
                elif y == 7:
                    C.set(x, y, z, TERRA_SL + "[type=bottom,waterlogged=false]")
            if not wall:
                cells.append((a, k))
    busy(C, *(AB(axis, a0 - 1, bf) + AB(axis, a0 + 4, bb)))
    # the front: an awning lintel and a counter with a gap
    for a in range(a0, a0 + 4):
        x, z = AB(axis, a, bf)
        C.set(x, 4, z, f"{CARPETS[(seed + a) % 8]}_wool" if (a + seed) % 2 else "white_wool")
        if a != a0 + 1:
            C.set(x, 1, z, slab("spruce_slab", "top"))
    back = [AB(axis, a, bf + side * 3) for a in range(a0, a0 + 4)]
    goods_at(C, back, kind, seed)
    # side shelves
    for (a, fc_side) in ((a0, a0 - 1), (a0 + 3, a0 + 4)):
        x, z = AB(axis, a, bf + side * 2)
        wx, wz = AB(axis, fc_side, bf + side * 2)
        C.set(x, 2, z, f"{SHELF}[facing={out_facing(x - wx, z - wz)}]")
    if table:
        x, z = AB(axis, a0 + 3, bf + side * 2)
        chest(C, x, 1, z, "west" if axis == "x" else "north", table)
    if mob:
        x, z = AB(axis, a0 + 1, bf + side * 2)
        spawner(C, x, 1, z, mob)
    x, z = AB(axis, a0 + 2, bf + side * 2)
    hang(C, x, 3, z, LANT_H)


def shop_row(C, axis, a0, a1, bf, side, gaps=(), seed=0, chests=(), mobs=()):
    """Shops along an alley side from a0 to a1, skipping the a ranges in ``gaps`` (lanes), each 4 wide with shared
    walls."""
    a = a0 + 1
    i = 0
    while a + 3 <= a1 - 1:
        if any(g0 - 1 <= aa <= g1 + 1 for (g0, g1) in gaps for aa in range(a - 1, a + 5)):
            a += 1
            continue
        kind = GOOD_KINDS[(seed + i * 5) % len(GOOD_KINDS)]
        shop(C, axis, a, side, bf, kind, seed + i * 7, table="bcv_souk" if i in chests else None,
             mob=mobs[i] if i < len(mobs) and mobs[i] else None)
        a += 5
        i += 1


def souk(C):
    """Three vaulted alleys of shops (A from the court east to the crossroads, B north to the corner, C west to the
    bazaar's east iwan), the domed crossroads, the open lane, the spice warehouse, the dyers' yard and its tower."""
    A0, A1 = 33, 61
    alley(C, "x", A0, A1, SOUK_A[0], SOUK_A[1])
    alley(C, "z", -17, 45, SOUK_B[0], SOUK_B[1])
    alley(C, "x", 35, 65, SOUK_C[0], SOUK_C[1])
    for x in range(66, 70):
        for z in range(SOUK_C[0], SOUK_C[1] + 1):
            C.set(x, 0, z, souk_floor(x, z))
    shop_row(C, "x", A0, A1, SOUK_A[0] - 1, -1, gaps=[LANE], seed=1, chests=(1,), mobs=(None, None, None, MOB_BANDIT))
    shop_row(C, "x", A0, A1, SOUK_A[1] + 1, 1, seed=2, mobs=(None, MOB_MITE))
    shop_row(C, "z", -8, 45, SOUK_B[0] - 1, -1, seed=3, chests=(4,), mobs=(None, None, MOB_SCARAB))
    shop_row(C, "z", -17, 45, SOUK_B[1] + 1, 1, seed=4, chests=(8,), mobs=(None, None, None, None, None, MOB_BANDIT))
    shop_row(C, "x", 35, 70, SOUK_C[0] - 1, -1, seed=5, chests=(3,))
    shop_row(C, "x", 35, 65, SOUK_C[1] + 1, 1, gaps=[LANE], seed=6, mobs=(None, MOB_RAIDER))
    crossroads(C)
    lane(C)
    warehouse(C)
    dyers(C)


def crossroads(C):
    """The domed crossroads (x 62 .. 75, z 46 .. 59): four arches, a dome on squinches with an oculus, the brass water
    clock in its basin."""
    X0, Z0, X1, Z1 = CROSS
    cx, cz = (X0 + X1) / 2.0, (Z0 + Z1) / 2.0
    busy(C, X0, Z0, X1, Z1)
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            edge = x in (X0, X1) or z in (Z0, Z1)
            opening = ((x in (X0, X1) and SOUK_A[0] <= z <= SOUK_A[1]) or
                       (z in (Z0, Z1) and SOUK_B[0] <= x <= SOUK_B[1]))
            C.set(x, 0, z, souk_floor(x, z) if not edge or opening else GB)
            for y in range(1, 10):
                if edge and not (opening and y <= 5):
                    C.set(x, y, z, PGS if y in (6, 9) else GB)
                elif not edge:
                    C.air(x, y, z)
            d = math.hypot(x - cx, z - cz)
            if not edge and d > 6.4:
                C.set(x, 10, z, PGS)
            elif edge:
                C.set(x, 10, z, GB)
                if (x + z) % 2 == 0:
                    C.set(x, 11, z, PGS)
            for y in range(10, 18):
                dd = math.sqrt(d * d + (y - 10) ** 2 * 1.1)
                if 6.4 < dd <= 7.6 and d <= 7.4:
                    oc = d < 1.6
                    a = math.degrees(math.atan2(z - cz, x - cx)) % 45
                    C.set(x, y, z, GLASS if oc else (BRASS if a < 5 or a > 40 else AZ))
                elif dd <= 6.4 and y > 10:
                    C.air(x, y, z)
            if d < 1.0:
                C.set(x, 17, z, GLASS)
    # the water clock: a round basin, a brass column with gears, a copper bulb
    for x in range(X0 + 1, X1):
        for z in range(Z0 + 1, Z1):
            d = math.hypot(x - cx, z - cz)
            if d <= 2.2:
                C.set(x, 0, z, WATER)
                C.set(x, -1, z, PGS)
            elif d <= 3.0:
                C.set(x, 1, z, slab(PGS_SL))
    for (x, z) in ((68, 52), (69, 53), (68, 53), (69, 52)):
        C.set(x, 0, z, BRASS)
        C.set(x, 1, z, ENGR if (x + z) % 2 else BRASS)
        C.set(x, 2, z, GEAR if (x + z) % 2 else BRASS)
    for (x, z) in ((68, 52), (69, 53)):
        C.set(x, 3, z, "waxed_copper_bulb[lit=true,powered=false]")
    for (x, z) in ((64, 48), (73, 48), (64, 57), (73, 57)):
        hang(C, x, 7, z, CHANDELIER)
    for (x, z) in ((63, 47), (74, 58)):
        C.set(x, 1, z, "barrel[facing=up,open=false]")
    chest(C, 74, 1, 47, "west", "bcv_souk")
    # the south way out of the crossroads into the quarter
    for x in range(SOUK_B[0], SOUK_B[1] + 1):
        for z in range(Z1 + 1, Z1 + 4):
            C.set(x, 0, z, main_pave(x, z))
            for y in range(1, 4):
                if C.free(x, y, z):
                    C.air(x, y, z)


def lane(C):
    """The open lane between alleys C and A: paving, lamp posts, awnings."""
    for x in range(LANE[0], LANE[1] + 1):
        for z in range(SOUK_C[1] + 1, SOUK_A[0]):
            C.set(x, 0, z, main_pave(x, z) if x == LANE[0] + 1 else street(x, z))
            for y in range(1, 6):
                C.air(x, y, z)
    for z in range(-4, 44, 8):
        C.set(LANE[1] + (1 if (z // 8) % 2 else -2) if False else LANE[0], 1, z, PGS) if False else None
    busy(C, LANE[0], SOUK_C[1] + 1, LANE[1], SOUK_A[0] - 1)
    for z in range(-5, 44, 9):
        lamp_post(C, LANE[1], 1, z)


def warehouse(C):
    """The spice warehouse (x 47 .. 60, z 24 .. 42): a tall hall of open sacks and crates, a brass weighing scale, a
    hoist beam with its hook, a loft on the north side."""
    x0, z0, x1, z1 = 47, 24, 60, 42
    busy(C, x0, z0, x1, z1)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(-1, 11):
                if edge or y in (-1, 0, 10):
                    C.set(x, y, z, (house_stone(x, y, z, 31) if edge else
                                    ("spruce_planks" if y == 0 else GB if y == -1 else
                                     "stripped_spruce_log[axis=x]" if z % 4 == 0 else "spruce_planks")))
                else:
                    C.air(x, y, z)
            if edge and (x + z) % 2 == 0:
                C.set(x, 11, z, PGS)
    for z in (32, 33):
        for y in (1, 2, 3):
            C.air(x0, y, z)
    wood_door(C, x0, 1, 32, "west", wood="spruce", hinge="left")
    wood_door(C, x0, 1, 33, "west", wood="spruce", hinge="right")
    # the loft (y 5) along the north wall, a ladder
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z0 + 5):
            C.set(x, 5, z, "spruce_planks")
        railing(C, x, 6, z0 + 4, "south")
    for y in range(1, 6):
        C.set(x1 - 1, y, z0 + 5, "ladder[facing=south,waterlogged=false]")
    for x in range(x0 + 1, x1 - 1, 2):
        C.set(x, 6, z0 + 1, "barrel[facing=up,open=true]")
        C.set(x + 1, 6, z0 + 1, ("orange_wool", "yellow_wool", "brown_wool", "red_wool")[x % 4])
    # rows of sacks and spice heaps
    for (zr, cols) in ((29, range(x0 + 2, x1 - 1)), (36, range(x0 + 2, x1 - 1))):
        for x in cols:
            if x in (53, 54):
                continue
            spec = ("barrel[facing=up,open=true]", "orange_terracotta", "yellow_terracotta", "red_terracotta",
                    "brown_wool")[(x * 7 + zr) % 5]
            C.set(x, 1, zr, spec)
            C.set(x, 1, zr + 1, "barrel[facing=up,open=false]" if x % 3 else "hay_block[axis=x]")
            if x % 2:
                C.set(x, 2, zr + 1, f"{CARPETS[x % 8]}_wool")
    # the scale and the hoist
    C.set(53, 1, 40, IRON)
    C.set(53, 2, 40, IRON_WALL)
    C.set(53, 3, 40, BRASS_SLAB + "[type=top,waterlogged=false]")
    C.set(52, 3, 40, "brass_slab" if False else BRASS_SLAB + "[type=bottom,waterlogged=false]")
    C.set(54, 3, 40, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    for x in range(x0 + 1, x1):
        C.set(x, 9, 33, "stripped_spruce_log[axis=x]")
    for y in range(5, 9):
        C.set(55, y, 33, CHAIN)
    C.set(55, 4, 33, f"{W}gear_panel" if False else IRON_WALL)
    chest(C, x1 - 1, 1, z1 - 1, "west", "bcv_spice")
    spawner(C, 50, 1, 34, MOB_SCARAB)
    lamp_grid(C, x0 + 1, z0 + 5, x1 - 1, z1 - 1, 1, CHANDELIER, h=4, step=5)
    for z in range(z0 + 6, z1, 4):
        C.set(x1, 3, z, EDISON)
        if z not in (32, 33):
            C.set(x0, 3, z, EDISON)
    lamp_grid(C, x0 + 1, z0 + 1, x1 - 1, z0 + 3, 6, LANT_H, h=2, step=5)


def dyers(C):
    """The dyers' yard (east of the crossroads, under the wall): dye vats, coloured pools, cloth on drying lines, the
    dyer's shed, and the dyers' tower whose newel stair climbs to a bridge onto the wall walk."""
    cells = [(x, z) for x in range(76, 92) for z in range(28, 60)
             if inside_poly(x, z) and wall_d(x, z) >= WALL_T + 1.5 and (x, z) not in C.busy]
    cellset = set(cells)
    for (x, z) in cells:
        C.set(x, 0, z, ("terracotta", PMUD, "orange_terracotta", MUD)[int(hash01(x, z, 131) * 4)])
        for y in range(1, 4):
            C.air(x, y, z)
    for z in range(SOUK_A[0], SOUK_A[1] + 1):
        for y in range(1, 6):
            C.air(CROSS[2], y, z)
        C.set(CROSS[2], 0, z, souk_floor(CROSS[2], z))
    # vats: cauldrons on brick bases, colour pools
    for (i, (x, z)) in enumerate(((79, 33), (82, 33), (85, 33), (77, 53), (81, 56), (79, 56))):
        if (x, z) not in cellset:
            continue
        C.set(x, 0, z, MUD)
        C.set(x, 1, z, "water_cauldron[level=3]")
    for (x0, z0, col) in ((77, 50, "blue"), (81, 50, "red"), (85, 49, "yellow")):
        for x in range(x0, x0 + 3):
            for z in range(z0, z0 + 3):
                if (x, z) in cellset:
                    C.set(x, 0, z, f"{col}_terracotta" if x in (x0, x0 + 2) or z in (z0, z0 + 2) else f"{col}_concrete")
    # drying lines: fence posts with cloth hung between
    for z in (30, 36):
        for x in range(77, 88):
            if (x, z) not in cellset:
                continue
            if x in (77, 87) or x == 82:
                for y in range(1, 4):
                    C.set(x, y, z, "spruce_fence")
            else:
                C.set(x, 3, z, f"{CARPETS[(x + z) % 8]}_wool")
    # the dyer's shed (x 86 .. 90, z 52 .. 57 where it fits) with its chest
    shed = [(x, z) for x in range(84, 91) for z in range(53, 58) if (x, z) in cellset]
    if shed:
        xs = [p[0] for p in shed]
        zs = [p[1] for p in shed]
        sx0, sx1, sz0, sz1 = min(xs), max(xs), min(zs), max(zs)
        for x in range(sx0, sx1 + 1):
            for z in range(sz0, sz1 + 1):
                if (x, z) not in cellset:
                    continue
                edge = x in (sx0, sx1) or z in (sz0, sz1)
                for y in range(1, 5):
                    C.set(x, y, z, house_stone(x, y, z, 41)) if edge else C.air(x, y, z)
                C.set(x, 5, z, "spruce_planks" if not edge else PGS)
        wood_door(C, sx0, 1, (sz0 + sz1) // 2, "west", wood="spruce")
        chest(C, sx1 - 1, 1, sz0 + 1, "west", "bcv_dyers")
        C.set(sx1 - 1, 1, sz1 - 1, "loom[facing=west]")
        hang(C, (sx0 + sx1) // 2, 3, (sz0 + sz1) // 2, LANT_H)
    dyers_tower(C)
    for (x, z) in ((80, 44), (85, 36), (80, 53)):
        if (x, z) in cellset:
            lamp_post(C, x, 1, z)


def dyers_tower(C):
    x0, z0 = 79, 39                              # box 9 x 9 (k = 3): x 79 .. 87, z 39 .. 47
    busy(C, x0 - 1, z0 - 1, x0 + 9, z0 + 9)
    for x in range(x0 - 1, x0 + 10):
        for z in range(z0 - 1, z0 + 10):
            edge = x in (x0 - 1, x0 + 9) or z in (z0 - 1, z0 + 9)
            for y in range(0, 19):
                if edge:
                    C.set(x, y, z, house_stone(x, y, z, 51) if y < 18 else PGS)
                elif y == 0:
                    C.set(x, y, z, PGS)
    cells, core, c1, f1 = newel(x0, z0, 3, 1, [3, 3, 3], 0, True)
    newel_write(C, cells, core, 1, tread=MUD_ST, floor=PGS, fill=MUD)
    cells2, core2, c2, f2 = newel(x0, z0, 3, f1, [3, 2], c1, True)
    newel_write(C, cells2, core2, f1, tread=MUD_ST, floor=PGS, fill=MUD)
    # windows and lamps in the core
    cx0, cz0, cx1, cz1 = core
    for y in (3, 8, 13):
        C.set(cx0, y, cz0, EDISON)
        C.set(cx1, y + 2, cz1, EDISON)
    for y in (5, 11):
        C.set(x0 - 1, y, z0 + 4, BARS)
        C.set(x0 + 9, y, z0 + 4, BARS)
    # door at the bottom (west), opening at the top (east) onto the bridge
    C.air(x0 - 1, 1, z0 + 1)
    C.air(x0 - 1, 2, z0 + 1)
    wood_door(C, x0 - 1, 1, z0 + 1, "west", wood="spruce")
    for z in range(z0, z0 + 3):
        for y in range(f2, f2 + 3):
            C.air(x0 + 9, y, z)
    # the bridge to the wall walk (feet 15)
    for x in range(x0 + 9, 100):
        if not inside_poly(x, z0 + 1) or wall_d(x, z0 + 1) < 1.5:
            break
        for z in range(z0, z0 + 3):
            C.set(x, WALK, z, PGS if z == z0 + 1 else GTILE)
            for y in range(WALK + 1, WALK + 4):
                C.air(x, y, z)
        if wall_d(x, z0 + 1) > WALL_T:
            C.set(x, WALK - 1, z0 + 1, GB)
            C.set(x, WALK + 1, z0 - 1, GB_WALL) if C.free(x, WALK + 1, z0 - 1) else None
            C.set(x, WALK + 1, z0 + 3, GB_WALL) if C.free(x, WALK + 1, z0 + 3) else None
    for y in range(0, WALK - 1):
        C.set(x0 + 11, y, z0 + 1, house_stone(x0 + 11, y, z0 + 1, 52))


# ------------------------------------------------------------------ the stables and the crawler garage
STX0, STZ0, STX1, STZ1 = -80, 28, -40, 66


def stables(C):
    """Camel stables (east half: stalls either side of an aisle, troughs, saddles, the hay loft) and the crawler garage
    (west half: a scout crawler under a gantry crane, the fitters' benches, fuel barrels), one long hall under a roof
    of timber and tiles; doors east (the court street) and south (the breach yard)."""
    busy(C, STX0, STZ0, STX1, STZ1)
    for x in range(STX0, STX1 + 1):
        for z in range(STZ0, STZ1 + 1):
            edge = x in (STX0, STX1) or z in (STZ0, STZ1)
            part = x == -60 and not (44 <= z <= 50)
            for y in range(-6 if edge else -1, 12):
                if edge or part:
                    if y <= 11:
                        C.set(x, y, z, stone(x, y, z, -6, 12, seed=23) if edge else GB)
                elif y == 0:
                    C.set(x, y, z, (TREAD if x < -60 and (x + z) % 2 else IRON if x < -60 else
                                    "coarse_dirt" if hash01(x, z, 141) < 0.3 else PMUD))
                elif y == -1:
                    C.set(x, y, z, GB)
                elif y == 11:
                    C.set(x, y, z, "spruce_planks" if x % 5 else "stripped_spruce_log[axis=z]")
                else:
                    C.air(x, y, z)
            if edge:
                C.set(x, 12, z, TERRA_SL + "[type=bottom,waterlogged=false]" if (x + z) % 2 else PGS)
            else:
                C.set(x, 12, z, TERRA)
    # the clerestory: a raised lantern roof along the hall's spine, barred windows, a tiled ridge
    for x in range(STX0 + 2, STX1 - 1):
        for z in range(45, 50):
            if z in (45, 49):
                for y in range(12, 15):
                    C.set(x, y, z, BARS if y == 13 and x % 3 else stone(x, y, z, -6, 15, seed=23))
                C.set(x, 15, z, stair(TERRA_ST, "south" if z == 45 else "north"))
            else:
                for y in (11, 12):
                    C.bp.remove(x, y, z)
                    C.keep.add((x, y, z))
                C.set(x, 16 if z == 47 else 15, z, TERRA if z == 47 else TERRA_SL + "[type=bottom,waterlogged=false]")
    for x in (STX0 + 1, STX1 - 1):
        for z in range(45, 50):
            for y in range(12, 16):
                C.set(x, y, z, stone(x, y, z, -6, 15, seed=23))
    # high windows
    for x in range(STX0 + 3, STX1 - 1, 5):
        for z in (STZ0, STZ1):
            for y in (7, 8):
                C.set(x, y, z, BARS)
    # the doors: east (z 51 .. 54) and south (x -72 .. -68)
    for z in range(51, 55):
        for y in range(1, 6):
            C.air(STX1, y, z)
        C.set(STX1, 0, z, main_pave(STX1, z))
    for x in range(-72, -67):
        for y in range(1, 6):
            C.air(x, y, STZ1)
        C.set(x, 0, STZ1, PGS)
    for y in range(1, 6):
        C.set(STX1, y, 50, CGS)
        C.set(STX1, y, 55, CGS)
    # camel stalls: fenced bays 4 wide along the north and south walls of the east half
    for (zw, zf, step) in ((STZ0 + 1, STZ0 + 5, 1), (STZ1 - 1, STZ1 - 5, -1)):
        for x in range(-59, -40):
            C.set(x, 1, zf, "spruce_fence" if (x + 59) % 4 != 2 else "spruce_fence_gate[facing=north,in_wall=false,open=false,powered=false]")
            if (x + 59) % 4 == 0:
                for z in rng(zw, zf):
                    C.set(x, 1, z, "spruce_fence")
                    C.set(x, 2, z, "spruce_fence") if z == zf else None
            else:
                C.set(x, 1, zw, "composter[level=7]" if (x + 59) % 4 == 2 else "hay_block[axis=y]")
                for z in rng(zw + step, zf - step):
                    C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 142) < 0.6 else "rooted_dirt")
        for x in range(-57, -40, 8):
            C.set(x, 1, zw + step, "water_cauldron[level=3]")
    # the hay loft (floor y 6) over the north stalls, a ladder up
    for x in range(-59, -40):
        for z in range(STZ0 + 1, STZ0 + 8):
            C.set(x, 6, z, "spruce_planks" if z < STZ0 + 7 else "spruce_slab[type=bottom,waterlogged=false]")
        railing(C, x, 7, STZ0 + 7, "south") if x % 3 else None
        for z in range(STZ0 + 1, STZ0 + 4):
            if hash01(x, z, 143) < 0.7:
                C.set(x, 7, z, "hay_block[axis=x]")
                if hash01(x, z, 144) < 0.4:
                    C.set(x, 8, z, "hay_block[axis=z]")
    for y in range(1, 7):
        C.set(-42, y, STZ0 + 8, "ladder[facing=south,waterlogged=false]") if False else None
    for y in range(1, 7):
        C.set(-41, y, STZ0 + 8, "ladder[facing=west,waterlogged=false]")
    for x in (-56, -50, -45):
        C.set(x, 7, STZ0 + 5, LANT)
    C.set(-41, 0, STZ0 + 8, PMUD)
    for x in range(-42, -40):
        C.air(x, 7, STZ0 + 7)
        C.set(x, 6, STZ0 + 7, "spruce_planks")
    # saddles and tack on the partition, a chest
    for z in range(36, 44, 2):
        C.set(-59, 2, z, f"{SHELF}[facing=east]")
        C.set(-59, 1, z, LEATHER if z % 4 else "brown_wool")
    for z in range(52, 60, 2):
        C.set(-59, 1, z, "barrel[facing=up,open=false]")
        C.set(-59, 2, z, "saddle" if False else "brown_carpet")
    chest(C, -42, 1, 47, "west", "bcv_stables")
    lamp_grid(C, -59, STZ0 + 9, -41, STZ1 - 1, 1, LANT_H, h=3, step=5)
    lamp_grid(C, -59, STZ0 + 1, -41, STZ0 + 6, 1, LANT_H, h=3, step=5, reach=6)
    for z in range(STZ0 + 3, STZ1 - 1, 5):
        C.set(STX1, 3, z, EDISON) if not 50 <= z <= 55 else None
        C.set(STX0, 3, z, EDISON)
    spawner(C, -52, 1, 47, MOB_SCARAB)
    garage(C)


def garage(C):
    """The crawler garage (x -79 .. -61): the scout crawler (axis z) on its treads, the gantry on two rails, a hook,
    benches and racks, fuel and spare treads."""
    # the gantry rails (y 9) along z on brass columns, the bridge beam and hook
    for x in (-78, -62):
        for z in range(STZ0 + 1, STZ1):
            C.set(x, 9, z, IRON)
        for z in (STZ0 + 2, 47, STZ1 - 2):
            for y in range(1, 9):
                C.set(x, y, z, BRASS if y % 4 else ENGR)
    for x in range(-77, -62):
        C.set(x, 9, 44, IRON_SLAB + "[type=top,waterlogged=false]" if x != -70 else IRON)
    for y in range(5, 9):
        C.set(-70, y, 44, CHAIN)
    C.set(-70, 4, 44, IRON_WALL)
    # the scout crawler: treads, a brass hull, a cab, a funnel (x -75 .. -65, z 50 .. 62)
    cx0, cx1, cz0, cz1 = -75, -65, 50, 62
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            track = x in (cx0, cx0 + 1, cx1 - 1, cx1)
            end = z in (cz0, cz1)
            if track:
                for y in range(1, 4):
                    if end and y == 3:
                        continue
                    C.set(x, y, z, TREAD if x in (cx0, cx1) or y != 2 else IRON)
                if x in (cx0, cx1) and z % 3 == 0:
                    C.set(x, 2, z, f"{COG}[facing={'west' if x == cx0 else 'east'}]")
            else:
                C.set(x, 1, z, IRON)
                C.set(x, 2, z, IRON)
                if not end:
                    C.set(x, 3, z, BRASS if z > cz0 + 3 else ENGR)
                    C.set(x, 4, z, (BTILE if z > cz0 + 4 else "glass_pane") if x in (cx0 + 2, cx1 - 2) or z == cz0 + 1
                          else (BTILE if z <= cz0 + 4 else AIR))
    for x in range(cx0 + 2, cx1 - 1):
        for z in range(cz0 + 1, cz0 + 5):
            C.set(x, 5, z, BTILE_SL + "[type=bottom,waterlogged=false]")
    for x in range(cx0 + 3, cx1 - 2):
        for z in range(cz0 + 2, cz0 + 4):
            C.air(x, 4, z)
    for y in range(4, 8):
        C.set(-70, y, cz1 - 3, SMOKE)
    for x in (-68, -72):
        C.set(x, 4, cz1 - 2, "barrel[facing=up,open=false]")
    # benches and racks along the west wall, fuel barrels, spare treads
    for z in range(STZ0 + 2, STZ1 - 1):
        tok = ("craft", "smith", "anvil", "grind", "pipes", "valve", "gauge", "cog")[(z - STZ0) % 8]
        if z in (47,):
            continue
        if z % 2 == 0:
            put_item(C, -79, 1, z, "west", tok, None, 151)
    for (x, z) in ((-66, 31), (-65, 31), (-66, 32), (-64, 31), (-64, 32)):
        C.set(x, 1, z, "barrel[facing=up,open=false]")
        if (x + z) % 2:
            C.set(x, 2, z, "barrel[facing=up,open=false]")
    for z in range(34, 40):
        C.set(-62, 1, z, TREAD_SLAB + "[type=bottom,waterlogged=false]")
    chest(C, -77, 1, 33, "east", "bcv_stables")
    lamp_grid(C, -79, STZ0 + 1, -61, STZ1 - 1, 1, HANG_LAMP, h=3, step=5)
    spawner(C, -64, 1, 42, MOB_SPIDER)


# ------------------------------------------------------------------ the minaret chimneys
def minaret(C, cx, cz, climb=False, seed=0):
    """A minaret that is also the chimney of the cistern pumps: a round banded shaft to y 56, two balconies on
    corbels (y 30, 44), a smoking brass cap; a copper pipe climbs its side. The south-west one is open: a ladder to
    the first balcony."""
    r = 3.6
    top = 56
    busy(C, cx - 6, cz - 6, cx + 6, cz + 6)
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            a = math.degrees(math.atan2(z - cz, x - cx)) % 360
            if d <= r + 0.3:
                for y in range(-4, top + 1):
                    if d > r - 1.0:
                        if y % 10 == 0 or y in (29, 43):
                            spec = AZ
                        elif y in (31, 45):
                            spec = GILD
                        elif 12 <= y <= 24 and (y + int(a // 30)) % 4 == 0:
                            spec = "light_blue_glazed_terracotta[facing=north]"
                        else:
                            spec = stone(x, y, z, -4, top, seed=25 + seed)
                        C.set(x, y, z, spec)
                    elif y <= 0 or y == top:
                        C.set(x, y, z, GB)
                    elif climb and y <= 33:
                        C.air(x, y, z)
            for (by, k) in ((30, 0), (44, 1)):
                if r - 0.6 < d <= r + 1.7:
                    C.set(x, by, z, PGS if d <= r + 0.4 else GTILE)
                    if d > r + 0.4:
                        C.set(x, by - 1, z, stair(PGS_ST, out_facing(cx - x, cz - z), "top"))
                        railing(C, x, by + 1, z, out_facing(x - cx, z - cz))
                    elif d > r - 0.6:
                        pass
            # the cap: a brass ring, a smokestack crown
            if d <= r + 0.8:
                if d > r - 0.2:
                    C.set(x, top + 1, z, BRASS)
                if d <= 2.4:
                    for y in range(top + 1, top + 5):
                        if d > 1.3:
                            C.set(x, y, z, SMOKE if y < top + 4 else IRON)
                        elif y == top + 1:
                            C.set(x, y, z, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # lancet windows lighting the shaft and balcony doors
    for y in (8, 18, 38, 50):
        C.set(cx, y, cz + 3, BARS)
        C.set(cx, y + 1, cz + 3, BARS)
    for (y, _) in ((31, 0), (45, 1)):
        C.set(cx, y, cz + 3, BARS) if not climb or y == 45 else None
    # the pipe up the north face
    for y in range(1, top):
        C.set(cx, y, cz - 4, PIPE_Y) if C.free(cx, y, cz - 4) else None
    if climb:
        for y in range(1, 31):
            C.set(cx, y, cz - 2, "ladder[facing=south,waterlogged=false]")
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if math.hypot(x - cx, z - cz) <= r - 1.0 and (x, z) != (cx, cz - 2):
                    C.set(x, 30, z, PGS)
        for y in (31, 32):
            C.air(cx, y, cz + 3)
            C.air(cx, y, cz + 2)
        C.air(cx, 1, cz + 3)
        C.air(cx, 2, cz + 3)
        wood_door(C, cx, 1, cz + 3, "south", wood="acacia")
        for y in (6, 13, 20, 26):
            C.set(cx + 2, y, cz, EDISON)
            C.set(cx - 2, y + 3, cz, EDISON)
        chest(C, cx + 4, 31, cz + 1, "west", "bcv_minaret")
        C.set(cx - 4, 31, cz + 1, LANT)


# ------------------------------------------------------------------ houses
HOUSE_KINDS = ["lodging", "kitchen", "weaver", "potter", "apothecary", "scribe", "workshop", "prayer", "dormitory",
               "coffee", "smithy", "spices"]


def house(C, x0, z0, x1, z1, seed):
    """A mud-brick house: one or two storeys, a roof terrace with a parapet, a door on its street side, windows,
    furnished rooms (a ladder up), sometimes a wind-catcher or an awning."""
    two = hash01(x0, z0, seed) < 0.55
    top = 10 if two else 5
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(-1, top + 1):
                if edge or y in (-1, 0, top) or (two and y == 5):
                    if edge:
                        spec = house_stone(x, y, z, seed)
                        if (x in (x0, x1)) and (z in (z0, z1)) and y > 0:
                            spec = CUT_SS if y % 3 else SST
                    elif y == 0:
                        spec = "terracotta" if (x + z) % 2 else PMUD
                    elif y == -1:
                        spec = MUD
                    elif y == top:
                        spec = PMUD
                    else:
                        spec = "spruce_planks"
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            if edge:
                C.set(x, top + 1, z, MUD_WALL if (x + z) % 3 else house_stone(x, top + 1, z, seed))
    busy(C, x0, z0, x1, z1, pad=1)
    # the door: on the first side whose outside is open street
    cxm, czm = (x0 + x1) // 2, (z0 + z1) // 2
    sides = [("south", cxm, z1, cxm, z1 + 1), ("north", cxm, z0, cxm, z0 - 1), ("east", x1, czm, x1 + 1, czm),
             ("west", x0, czm, x0 - 1, czm)]
    k = int(hash01(x1, z1, seed) * 4)
    sides = sides[k:] + sides[:k]
    door = None
    for (face, dx, dz, ox, oz) in sides:
        if (ox, oz) in C.city and C.free(ox, 1, oz) and C.free(ox, 2, oz) and not C.solid(ox, 0, oz) is False:
            door = (face, dx, dz)
            break
    if door is None:
        door = sides[0][:3]
    face, dx, dz = door
    wood_door(C, dx, 1, dz, face, wood=("acacia", "jungle", "spruce")[int(hash01(dx, dz, seed) * 3)])
    ox, oz = dx + DV[face][0], dz + DV[face][1]
    C.air(ox, 1, oz)
    C.air(ox, 2, oz)
    ix, iz = dx - DV[face][0], dz - DV[face][1]
    # windows
    for (wx, wz) in ((x0, czm + 1), (x1, czm - 1), (cxm - 1, z0), (cxm + 1, z1)):
        if (wx, wz) == (dx, dz):
            continue
        for f in ((2, 7) if two else (2,)):
            C.set(wx, f, wz, "spruce_trapdoor[facing=%s,half=bottom,open=true,powered=false,waterlogged=false]" % (
                out_facing(wx - cxm, wz - czm)) if False else BARS if f == 2 else PANE)
    kinds = HOUSE_KINDS
    kind = kinds[int(hash01(x0, z1, seed) * len(kinds))]
    # a ladder in the corner opposite the door, through the upper floor and to the roof
    lx, lz = (x0 + 1, z0 + 1) if face in ("south", "east") else (x1 - 1, z1 - 1)
    lf = "south" if lz == z0 + 1 else "north"
    for y in range(1, top + 1):
        C.set(lx, y, lz, f"ladder[facing={lf},waterlogged=false]")
    furnish(C, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 1, kind, "bcv_house", clear=[(ix, iz), (lx, lz)], seed=seed)
    if two:
        kind2 = kinds[int(hash01(x1, z0, seed) * len(kinds))]
        furnish(C, x0 + 1, z0 + 1, x1 - 1, z1 - 1, 6, kind2, "bcv_house" if hash01(z0, x0, seed) < 0.5 else None,
                clear=[(lx, lz)], seed=seed + 1)
    # roof: a wind-catcher or an awning and some pots
    if hash01(x0, z0, seed + 3) < 0.35:
        wx, wz = (x1 - 1, z0 + 1) if (lx, lz) != (x1 - 1, z0 + 1) else (x0 + 1, z1 - 1)
        for y in range(top + 1, top + 5):
            for (ax_, az_) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                X, Z = wx + ax_ - (1 if wx == x1 - 1 else 0), wz + az_ - (1 if wz == z1 - 1 else 0)
                C.set(X, y, Z, (BARS if y == top + 3 and (ax_ + az_) % 2 else house_stone(X, y, Z, seed)))
    else:
        for (x, z) in ((x0 + 2, z1 - 2), (x1 - 2, z0 + 2)):
            if (x, z) != (lx, lz):
                C.set(x, top + 1, z, ("decorated_pot[cracked=false,facing=north,waterlogged=false]", "potted_cactus",
                                      "barrel[facing=up,open=false]")[int(hash01(x, z, seed) * 3)])


def houses(C):
    """Fill the free quarters with houses on a jittered grid: each plot must be inside the city, clear of the wall and
    of every other building, with a street left round it."""
    n = 0
    for gx in range(-104, 104, 12):
        for gz in range(-116, 96, 12):
            j = hash01(gx, gz, 161)
            w = 7 + int(hash01(gx, gz, 162) * 4)
            d = 7 + int(hash01(gx, gz, 163) * 4)
            x0 = gx + int(j * 3)
            z0 = gz + int(hash01(gz, gx, 164) * 3)
            x1, z1 = x0 + w - 1, z0 + d - 1
            ok = True
            for x in range(x0 - 2, x1 + 3):
                for z in range(z0 - 2, z1 + 3):
                    if (x, z) in C.busy or (x, z) not in C.city:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            if min(wall_d(x, z) for x in (x0, x1) for z in (z0, z1)) < WALL_T + 3 or \
                    min(wall_d(x, z) for x in (x0, x1, (x0 + x1) // 2) for z in (z0, z1, (z0 + z1) // 2)) < WALL_T + 3:
                continue
            if any(near_breach(x, z) or math.hypot(x - BREACH[0], z - BREACH[1]) < 18 for x in (x0, x1) for z in (z0, z1)):
                continue
            house(C, x0, z0, x1, z1, seed=n * 13 + 7)
            n += 1
    return n


def street_lamps(C):
    """Lamp posts and a few palms along the open streets (never against a building or in a doorway)."""
    for x in range(-100, 101, 7):
        for z in range(-110, 96, 7):
            xx = x + int(hash01(x, z, 171) * 3) - 1
            zz = z + int(hash01(z, x, 172) * 3) - 1
            if (xx, zz) not in C.city or wall_d(xx, zz) < WALL_T + 2:
                continue
            if any((xx + dx, zz + dz) in C.busy for dx in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2)):
                continue
            if not (C.free(xx, 1, zz) and C.free(xx, 2, zz)):
                continue
            h = hash01(xx, zz, 173)
            if h < 0.45:
                lamp_post(C, xx, 1, zz)
                C.busy.add((xx, zz))
            elif h < 0.58 and all((xx + dx, zz + dz) not in C.busy for dx in range(-4, 5) for dz in range(-4, 5)):
                planter_palm(C, xx, zz, 6 + int(h * 10) % 3, seed=xx * 3 + zz)
                busy(C, xx - 1, zz - 1, xx + 1, zz + 1)


# ------------------------------------------------------------------ the sand-crawlers
def crawler(C, F, L=44.0, Wh=8.0, wreck=False, seed=0):
    """A giant brass sand-crawler in its local frame (u stern -> nose, v right, h up from the tread bottoms): two
    tread units, a riveted hull with a hold (floor h 5, deck h 9), the wheelhouse forward, two funnels and a boiler
    dome, a ploughing prow, a stern ramp door. Wrecked: holed, half full of sand."""
    def fn(u, v, h, x, y, z):
        av = abs(v)
        hole = wreck and vnoise(u * 0.6 + v * 0.3, h * 0.6, 3.0, 181 + seed) > 0.7 and h > 5.5
        # treads
        if av >= Wh - 3.0 and h <= 4.5:
            uu = min(max(u, 2.25), L - 2.25)
            if math.hypot(u - uu, h - 2.25) <= 2.25:
                surf = av >= Wh - 0.7 or h < 0.7 or h > 3.8 or u < 1.2 or u > L - 1.2 or av < Wh - 2.4
                if surf:
                    if av >= Wh - 0.7 and abs(h - 2.25) < 0.6 and int(u) % 4 == 0:
                        return GEAR
                    return TREAD
                return IRON
            return None
        # chassis between the treads
        if av < Wh - 3.0 and 1.0 <= h < 4.5 and 2.0 <= u <= L - 4.0:
            return DIB if (h > 3.6 or av > Wh - 4.0 or u < 3.0) else IRON
        # the hull: h 4.5 .. 9.5, prow sloping forward
        prow = L - 1.0 - max(0.0, 9.5 - h) * 0.45
        if 4.5 <= h <= 9.5 and 0.0 <= u <= prow and av <= Wh:
            shell = av > Wh - 1.0 or u < 1.0 or u > prow - 1.0 or h < 5.5 or h > 8.5
            if not shell:
                if wreck and h < 6.6 and vnoise(u * 0.4, v * 0.4, 4.0, 183 + seed) > 0.45:
                    return "sand"
                return AIR
            if hole and av > Wh - 1.0:
                return AIR
            if h > 8.5:
                return TREAD if av <= Wh - 1.0 else BRASS
            if h < 5.5:
                return IRON if av <= Wh - 1.0 else DIB
            if u > prow - 1.0:
                return DIB if h < 7.0 else ENGR
            if abs(h - 7.0) < 0.5:
                return ENGR if int(u) % 6 else GILD
            return BRASS if (int(u) + int(h)) % 7 else BTILE
        # the plough below the prow
        if h < 4.5 and L - 4.0 < u <= L - 1.0 + (4.5 - h) * 0.2 and av <= Wh - 3.0:
            return DIB
        # the wheelhouse forward
        if L - 13.0 <= u <= L - 4.0 and av <= Wh - 2.5 and 9.5 < h <= 14.5:
            shell = av > Wh - 3.5 or u < L - 12.0 or u > L - 5.0 or h > 13.5
            if not shell:
                return AIR
            if hole:
                return AIR
            if h > 13.5:
                return BTILE
            if 11.0 <= h <= 12.5 and (u > L - 5.0 or (av > Wh - 3.5 and int(u) % 3 != 0)):
                return "glass_pane" if not wreck else ("glass_pane" if hash3(x, y, z, 184) < 0.4 else AIR)
            return BRASS if h > 10.0 else DIB
        # funnels and the boiler dome
        for fv in (-3.0, 3.0):
            if math.hypot(u - L * 0.36, v - fv) <= 1.4 and 9.5 < h <= (13.0 if wreck else 18.5):
                return SMOKE if math.hypot(u - L * 0.36, v - fv) > 0.6 else (AIR if h < 18.0 else None)
        if math.sqrt((u - L * 0.18) ** 2 + v * v + (h - 9.5) ** 2) <= 3.0 and h > 9.5:
            return COPPER if not wreck else VERD
        return None
    raster(C, F, (0.0, L, -Wh, Wh, 0.0, 19.0), fn, ymin=-6)


def parked_crawler(C):
    """The caravan crawler parked across the road outside the gate (nose west, x 50 .. 94): its hold of bales and
    chests, bunks, the wheelhouse with its levers and gauges, the stern ramp down to the road."""
    L, Wh = 44.0, 8.0
    F = Frame((94.0, 1.0, 104.0), 180.0)
    crawler(C, F, L, Wh, seed=1)
    busy(C, 49, 95, 101, 113)
    # deck railings and a hatch with a ladder down to the hold
    for u in range(1, int(L) - 1):
        for s in (-1, 1):
            x, y, z = F.iworld(u, s * Wh, 10)
            if C.free(x, y, z):
                railing(C, x, y, z, "north" if z < 104 else "south")
    hx, hy, hz = F.iworld(22, 0, 9)
    C.air(hx, hy, hz)
    for y in range(hy - 3, hy + 1):
        C.set(hx, y, hz - 1, IRON) if y == hy else None
    for y in range(hy - 3, hy + 1):
        C.set(hx, y, hz, "ladder[facing=south,waterlogged=false]")
    # the stern door and ramp (x 95 .. 99)
    for v in (-1, 0, 1):
        for h in (6, 7, 8):
            x, y, z = F.iworld(0, v, h)
            C.air(x, y, z)
        for k in range(1, 6):
            x, y, z = F.iworld(-k, v, 5 - k)
    for k in range(0, 6):
        for v in (-1, 0, 1):
            x, y, z = F.iworld(-1 - k, v, 0)
            top = 6 - k                                   # world y 6 .. 1
            for yy in range(1, top + 1):
                C.set(x, yy, z, IRON if yy < top else TREAD_STAIRS + "[facing=west,half=bottom,shape=straight,waterlogged=false]")
            for yy in range(top + 1, top + 4):
                C.air(x, yy, z)
    # the hold: bales, crates, chests, lamps; bunks forward
    for u in range(3, 30):
        for s in (-1, 1):
            x, y, z = F.iworld(u, s * (Wh - 1.6), 6)
            if u % 5 == 0:
                continue
            spec = ("hay_block[axis=x]", "barrel[facing=up,open=false]", "white_wool", "orange_wool", "barrel[facing=up,open=false]")[(u + s) % 5]
            C.set(x, y, z, spec)
            if u % 3 == 0:
                C.set(x, y + 1, z, f"{CARPETS[u % 8]}_wool")
    for (u, s, t) in ((10, -1, "bcv_crawler"), (26, 1, "bcv_crawler")):
        x, y, z = F.iworld(u, s * (Wh - 1.6), 6)
        chest(C, x, y, z, "south" if s < 0 else "north", t)
    for u in (32, 35):
        x, y, z = F.iworld(u, -(Wh - 2.0), 6)
        C.bp.bed(x, y, z, "west", color="brown")
    x, y, z = F.iworld(37, Wh - 2.0, 6)
    C.set(x, y, z, "crafting_table")
    for u in (5, 11, 17, 23, 29, 35):
        for v in (-3, 3):
            x, y, z = F.iworld(u, v, 8)
            if C.free(x, y, z) and C.free(x, y - 1, z):
                hang(C, x, y, z, LANT_H)
    # the wheelhouse: helm levers on a gauge desk, chairs, a chart table; a ladder up from the deck
    for v in (-2, 0, 2):
        x, y, z = F.iworld(L - 6, v, 10)
        C.set(x, y, z, GAUGE if v == 0 else IRON)
        x2, y2, z2 = F.iworld(L - 7, v, 10)
        C.set(x2, y2, z2, f"{CHAIR}[facing=west]") if v != 0 else C.set(x2, y2, z2, "lever[face=floor,facing=west,powered=false]")
    x, y, z = F.iworld(L - 10, 2, 10)
    C.set(x, y, z, "cartography_table")
    x, y, z = F.iworld(L - 11, -2, 10)
    C.set(x, y, z, "barrel[facing=up,open=false]")
    x, y, z = F.iworld(L - 9, 0, 13)
    hang(C, x, y - 1, z, LANT_H)
    for h in (10, 11):
        x, y, z = F.iworld(L - 13, 0, h)
        C.air(x, y, z)
    x, y, z = F.iworld(L - 13, 0, 10)
    wood_door(C, x, y, z, "east", wood="dark_oak")
    spawner(C, *F.iworld(18, 0, 6), MOB_BANDIT)
    # boiler smoke
    for fv in (-3, 3):
        x, y, z = F.iworld(L * 0.36, fv, 18)
        C.set(x, y, z, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


def wrecked_crawler(C):
    """The crawler that rammed the south-west wall: listing, half buried, holed, its hold full of sand; its deck
    climbs to the breach (the side route in); a sand drift up to its stern."""
    L, Wh = 34.0, 7.0
    yaw = math.degrees(math.atan2(86.5 - 113.0, -68.8 + 90.0))
    F = Frame((-90.0, -3.0, 113.0), yaw, pitch=0.0, roll=6.0)
    crawler(C, F, L, Wh, wreck=True, seed=2)
    # the drift: a sand slope up to the deck along the stern quarter
    for u in range(-8, 4):
        for v in range(-int(Wh) - 1, int(Wh) + 2):
            x, y, z = F.iworld(u, v, 0)
            hgt = int(round(6.0 - max(0, -u) * 0.75))
            if hgt < 1 or (x, z) not in C.ground:
                continue
            for yy in range(1, hgt + 1):
                if C.free(x, yy, z):
                    C.set(x, yy, z, "sand" if yy < hgt else ("sandstone_slab[type=bottom,waterlogged=false]"
                                                              if hash01(x, z, 191) < 0.3 else "sand"))
    for u in range(4, int(L)):
        x, y, z = F.iworld(u, 0, 9)
        if u % 6 == 0:
            for (vv, hh) in ((0, 10),):
                X, Y, Z = F.iworld(u, vv, hh)
                if C.free(X, Y, Z) and hash01(X, Z, 192) < 0.6:
                    C.set(X, Y, Z, "sand") if False else None
    # a hole in the right side over the drift: into the hold
    for u in range(12, 16):
        for h in (6, 7):
            x, y, z = F.iworld(u, Wh - 0.5, h)
            C.air(x, y, z)
    x, y, z = F.iworld(16, 2, 6)
    chest(C, x, y + (1 if C.solid(x, y, z) else 0), z, "north", "bcv_wreck")
    spawner(C, *F.iworld(20, -2, 7), MOB_HUSK)
    for u in (5, 10, 15, 20, 25):
        for v in (-3, 2):
            x, y, z = F.iworld(u, v, 8)
            if C.free(x, y, z) and C.free(x, y - 1, z):
                hang(C, x, y, z, LANT_H)
    busy(C, -100, 80, -60, 118)


# ------------------------------------------------------------------ the camp and the road
def tent(C, cx, cz, axis, col, seed):
    """A caravan tent: an A-frame of wool (4 high at the ridge) on a back pole, open at the front (+a), a bedroll and
    a lantern inside."""
    for a in range(-2, 3):
        for b in range(-2, 3):
            x, z = (cx + a, cz + b) if axis == "x" else (cx + b, cz + a)
            ry = 2 + (2 - abs(b))
            C.set(x, ry, z, f"{col}_wool")
            C.set(x, 0, z, "coarse_dirt" if (a + b) % 2 else PMUD)
            for y in range(1, ry):
                if a == -2:
                    C.set(x, y, z, f"{col}_wool")
                else:
                    C.air(x, y, z)
    x, z = (cx - 3, cz) if axis == "x" else (cx, cz - 3)
    for y in range(1, 5):
        C.set(x, y, z, "spruce_fence")
    x, z = (cx, cz - 1) if axis == "x" else (cx - 1, cz)
    C.bp.bed(x, 1, z, "west" if axis == "x" else "north", color=("brown", "light_gray", "red")[seed % 3])
    x, z = (cx - 1, cz + 1) if axis == "x" else (cx + 1, cz - 1)
    C.set(x, 1, z, LANT)
    busy(C, cx - 3, cz - 3, cx + 3, cz + 3)


def camp(C):
    """The caravan camp east of the parked crawler: tents round a fire, bales and crates, a brass handcart, the camp
    waystone and its lamp, the trail post pointing to the gate."""
    cx, cz = CAMP
    for x in range(cx - 9, cx + 9):
        for z in range(cz - 12, cz + 9):
            if (x, z) in C.ground and math.hypot(x - cx, (z - cz) * 0.8) < 10:
                C.set(x, 0, z, track(x, z) if hash01(x, z, 201) < 0.6 else "coarse_dirt")
                for y in (1, 2, 3):
                    if C.free(x, y, z):
                        C.air(x, y, z)
    tent(C, cx + 4, cz - 7, "z", "white", 0)
    tent(C, cx + 5, cz + 3, "x", "orange", 1)
    tent(C, cx - 3, cz + 5, "z", "light_gray", 2)
    C.set(cx, 1, cz - 1, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, ax) in ((2, -1, "z"), (-2, -1, "z"), (0, 1, "x"), (0, -3, "x")):
        C.set(cx + dx, 1, cz - 1 + dz - (0 if dz else 0), f"stripped_spruce_log[axis={ax}]") if (dx, dz) != (0, 1) else \
            C.set(cx + dx, 1, cz + dz, f"stripped_spruce_log[axis={ax}]")
    waystone(C, cx - 4, 1, cz - 4)
    lamp_post(C, cx - 5, 1, cz - 2)
    for (x, z) in ((cx + 7, cz - 2), (cx + 7, cz - 1), (cx + 8, cz - 2)):
        C.set(x, 1, z, "barrel[facing=up,open=false]" if (x + z) % 2 else "hay_block[axis=z]")
    chest(C, cx + 8, 1, cz - 1, "west", "bcv_camp")
    # the brass handcart
    for z in range(cz - 10, cz - 7):
        C.set(cx - 6, 1, z, BRASS_SLAB + "[type=top,waterlogged=false]")
        C.set(cx - 7, 1, z, f"{COG}[facing=west]") if z != cz - 9 else C.set(cx - 7, 1, z, IRON)
    C.set(cx - 6, 2, cz - 9, "barrel[facing=up,open=false]")
    busy(C, cx - 8, cz - 11, cx - 5, cz - 6)
    # the trail post
    C.set(cx - 8, 1, cz + 2, "spruce_fence")
    C.set(cx - 8, 2, cz + 2, "spruce_fence")
    C.set(cx - 8, 3, cz + 2, LANT)


def roads(C):
    """The caravan road from the camp, south of the parked crawler, then round its nose to the gate; the street
    paving inside: the gate street, the bazaar ring streets and the north street under the bridge."""
    pave(C, [(104, 112), (96, 116), (60, 116), (44, 115), (24, 112), (8, 110), (0, 109)], 5, track)
    pave(C, [(0, 109), (0, 118)], 3, track)
    for x in range(-34, 35):
        for z in range(19, 24):
            if (x, z) in C.busy:
                continue
            C.set(x, 0, z, main_pave(x, z) if abs(x) <= 3 else street(x, z))
            for y in (1, 2, 3):
                if C.free(x, y, z):
                    C.air(x, y, z)
    for x in range(-30, 31):
        for z in range(-53, -48):
            if (x, z) in C.busy and not (BRX0 <= x <= BRX1):
                continue
            if C.solid(x, 1, z) and not (BRX0 <= x <= BRX1):
                continue
            if BRX0 <= x <= BRX1 and z in (-52, -51):
                continue
            C.set(x, 0, z, main_pave(x, z))


# ------------------------------------------------------------------ the builder
def brass_caravanserai(bp):
    C = Ctx(bp)
    ground(C)
    city_wall(C)
    gatehouse(C)
    court(C)
    bazaar(C)
    garden(C)
    garden_cistern(C)
    well_head(C)
    palace(C)
    bridge(C)
    souk(C)
    stables(C)
    for i, (x, z) in enumerate(MINARETS):
        minaret(C, x, z, climb=(i == 0), seed=i)
    parked_crawler(C)
    wrecked_crawler(C)
    camp(C)
    roads(C)
    houses(C)
    street_lamps(C)
    # the camera spots: explicit air at feet and head (higher interiors are otherwise left to natural air)
    for (_n, (x, y, z), _l) in VIEWS:
        for yy in (y, y + 1):
            if bp.get(x, yy, z) is None:
                bp.set(x, yy, z, AIR)


VIEWS = [
    ("caravan_court", (-14, 1, 66), (6, 3, 45)),
    ("souk_crossroads", (64, 1, 56), (68, 2, 52)),
    ("auction_pit", (0, PIT_F + 1, BCZ + 12), (0, PIT_F + 3, BCZ - 19)),
    ("drum_gallery", (19, ROOF_B + 1, BCZ + 8), (-10, 10, BCZ - 6)),
    ("divan", (5, 1, -84), (0, 3, -102)),
    ("hammam", (-16, 1, -85), (-20, 2, -90)),
    ("garden_cistern", (0, CIS_F + 1, -58), (0, CIS_F + 2, -78)),
    ("library", (25, UP_F + 1, -84), (15, UP_F + 2, -94)),
]

register(StructureDef(
    "brass_caravanserai", "overworld", ["desert", "savanna", "savanna_plateau"],
    [Piece("city", brass_caravanserai, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_BANDIT, 6, 1, 2), (MOB_RAIDER, 4, 1, 1), (MOB_HUSK, 6, 1, 2)],
    title_fr="Le Caravansérail de laiton", title_en="The Brass Caravanserai"))

"""Tidal Abbey (Abbaye des marées): a Mont-Saint-Michel. A rocky tidal island rising from the sea off a beach, girdled
by ramparts and towers with a sea gate, a town of stone houses under slate roofs climbing round the rock, and on the
summit a gothic abbey whose spire stands 90 blocks over the abbey floor. Colossal tier (tools/BUILDING.md §1, §12
concept 5, §15).

Silhouette (one noun phrase, §15.1): a stepped cone of rock and roofs in the sea, crowned by a church and one needle
spire, with a long causeway running out to the shore.

Placement: fit mode ``coast`` (wf/placement.py): the template's south side is the sea, the north end of the causeway
reaches the shore; the ground layer (blueprint y = 0) lands one block above the sea surface (sea water top = y -1),
so the waterline of every part is exact. Nothing carved lies under the sea surface.

Layout (x east, z south, island centre at 0, 0; compass angles from north, clockwise):
  * the causeway (north): 60 blocks from the shore to the barbican, its middle under a hand of water and broken
    (swim across), a wayside cross and a waystone at the shore end;
  * the sea gate: barbican, the king's gate between two towers in the ramparts, the gate court and its site of
    grace. Ramparts with round towers wrap the island from north-west round by the east to the south-west, where
    the Gabriel tower guards the little harbour;
  * the Grande Rue is the route: it winds east and south round the rock past the well square to the parvis of the
    rock-cut parish church (hub, site of grace), turns back on itself twice (hairpins), runs under the abbey's south
    flank to the Chatelet gate and climbs the Grand Degre to the west terrace. Ruelles join it to the rampart walk
    (two loops);
  * on the summit platform: the abbey church (nave 27 high, transepts, choir and apse) under a crossing tower and
    its spire (open from the floor to the tip). West of the terrace, La Merveille: three storeys built against the
    west cliff: the cloister on top (garden open to the sky, rock-cut on its east side), the knights' hall, the
    almonry, linked by a stair tower;
  * the crypt inside the rock: Notre-Dame-sous-Terre (site of grace), the ossuary, a narrow stair down to the boss
    arena at the heart of the island (radius 16, 19 high, pillars, sea light through grates), the reward vault
    behind sealed bars, and a tunnel out to the harbour through a one-way iron door (back to the start along the
    strand).
Loot gradient (§15.6): ramparts and town tier 1, cloister / knights' hall / treasury tier 2, the reliquary (secret,
down the cloister well) and the vault tier 3.
"""
import math

from ..arch import Palette, oak, slab, spruce, stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..megakit import fbm, hash01, hash3
from ..parts import LOOT, MOD

# placeholder boss until the abbey gets its own: the warden of the drowned citadel
# the abbey's own saint: the Abbess of the Tides (entity/boss/TideAbbess.java, tools/BOSSES.md)
BOSS = "brasshaven:tide_abbess"

# ------------------------------------------------------------------ dimensions
R0, RK = 42.0, 0.55          # rock radius at height y: R0 - RK * y (plus noise)
ROCK_TOP = 40
STRAND_R = 60                # the strand (y = 0) round the island
RING0, RING1 = 51.5, 55.5    # rampart ring (inner / outer face)
RING_C = 53.5
WALK = 9                     # rampart walk floor block (feet 10)
TOWERS = (330, 26, 56, 86, 116, 146, 196)
GABRIEL = 216                # the last tower: the harbour light
CH_F = 42                    # abbey floor (feet)
PLAT = (-31, -12, 35, 12)    # summit platform x0, z0, x1, z1 (top block y = CH_F - 1)
MV = (-52, -16, -32, 12)     # La Merveille outer x0, z0, x1, z1
MV_IN = (-50, -14, -34, 10)  # its rooms
ALMONRY_F, HALL_F = 12, 22   # feet of the two lower storeys (the cloister is at CH_F)
STAIR_T = (-46, -24, -38, -17)  # Merveille stair tower outer box
ARENA_C, ARENA_R, ARENA_F = (8, 0), 16, 3
CRYPT_F = 12
VAULT = (2, 20, 14, 27)

SLATE, SLATE_ST, SLATE_SL = "brasshaven:slate_roof_tiles", "brasshaven:slate_roof_tile_stairs", \
    "brasshaven:slate_roof_tile_slab"
WALL = Palette({"stone_bricks": 4, "cobblestone": 2, "andesite": 2, "tuff": 1, "mossy_stone_bricks": 1}, seed=611,
               scale=2.5)
ABBEY = Palette({"stone_bricks": 6, "polished_andesite": 2, "tuff_bricks": 1, "cracked_stone_bricks": 1}, seed=612,
                scale=3.0)
CRYPT = Palette({"tuff_bricks": 3, "stone_bricks": 2, "deepslate_bricks": 1, "polished_tuff": 1}, seed=613, scale=2.0)
SUPPORT = Palette({"stone_bricks": 3, "cobblestone": 3, "andesite": 1, "mossy_cobblestone": 1}, seed=614, scale=2.0)

LANTERN = "lantern[hanging=false,waterlogged=false]"
HLANTERN = "lantern[hanging=true,waterlogged=false]"


def P(r, phi):
    """Polar (compass degrees from north, clockwise) to (x, z)."""
    a = math.radians(phi)
    return r * math.sin(a), -r * math.cos(a)


def phi_of(x, z):
    return math.degrees(math.atan2(x, -z)) % 360


def empty(b):
    return b is None or b in ("minecraft:air", "minecraft:cave_air")


def rock_R(phi, y):
    n = fbm(phi * 0.9, y * 1.2, 9.0, 5) - 0.5
    m = fbm(phi * 2.6, y * 2.1, 4.0, 9) - 0.5
    return R0 - RK * y + n * 8 + m * 3


def rock_block(x, y, z):
    j = fbm(x * 0.6 + z * 0.4, y * 1.3 + x * 0.1, 6.0, 41)
    band = int((y + j * 5) // 4) % 5
    base = ("stone", "andesite", "stone", "tuff", "andesite")[band]
    h = hash3(x, y, z, 7)
    if y < 5 and h < 0.4 - y * 0.07:
        return "mossy_cobblestone"
    if h < 0.1:
        return "cobblestone"
    return base


# ------------------------------------------------------------------ the site
class Site:
    def __init__(self, bp):
        self.bp = bp
        self.rock = set()
        self.claims = {}     # (x, z) -> [dist, t, path id]
        self.paths = {}      # path id -> options
        self.t = {}          # (x, z) -> feet height of the walkway (halves)
        self.cols = set()    # walkway columns
        self.boxes = []      # reserved volumes (x0, y0, z0, x1, y1, z1)
        self.house_cols = set()
        self.houses = []
        self.fails = {}

    def why(self, reason):
        self.fails[reason] = self.fails.get(reason, 0) + 1
        return False

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.rock.discard((x, y, z))

    def air(self, x, y, z):
        self.bp.set(x, y, z, "air")
        self.rock.discard((x, y, z))

    def blocked_box(self, x0, y0, z0, x1, y1, z1):
        for b in self.boxes:
            if x0 <= b[3] and x1 >= b[0] and y0 <= b[4] and y1 >= b[1] and z0 <= b[5] and z1 >= b[2]:
                return True
        return False


def in_ramparts(phi):
    return phi >= 330 or phi <= GABRIEL


def reserve(S):
    """Volumes the town houses keep out of (built later, carved into the rock or standing on it)."""
    S.boxes += [
        (PLAT[0] - 1, 0, PLAT[1] - 3, PLAT[2] + 3, 160, PLAT[3] + 1),     # summit platform and church
        (MV[0] - 4, 0, STAIR_T[1] - 1, MV[2] + 1, 60, MV[3] + 3),         # La Merveille and its stair tower
        (-31, CRYPT_F - 2, -19, -18, CRYPT_F + 9, 10),                    # crypt chapel and ossuary
        (-20, ARENA_F - 2, -3, -8, CRYPT_F + 4, 3),                       # crypt stair
        (-12, 0, -20, 27, 24, 20),                                         # arena
        (0, 0, 15, 16, 10, 29),                                            # vault
        (-37, 0, 22, 2, 8, 28),                                            # tunnel to the harbour
        (-25, 26, 11, -11, 48, 21),                                        # Chatelet and Grand Degre
        (-55, -6, 17, -33, 8, 46),                                         # harbour
        (3, 11, 19, 16, 22, 31),                                           # rock-cut parish church
        (-11, -8, -70, 11, 14, -50),                                       # barbican and gate
    ]
    for phi in TOWERS + (GABRIEL,):
        cx, cz = P(RING_C, phi)
        r = 6.5 if phi == GABRIEL else 5.5
        S.boxes.append((round(cx - r), -3, round(cz - r), round(cx + r), 30, round(cz + r)))
    for sx in (-6, 6):
        S.boxes.append((sx - 5, -3, -59, sx + 5, 24, -48))


# ------------------------------------------------------------------ terrain: rock, strand, talus
def strand_r(phi):
    return STRAND_R + (fbm(phi * 2.1, 3, 6.0, 23) - 0.5) * 6


def terrain(S):
    bp = S.bp
    for x in range(-70, 71):
        for z in range(-70, 71):
            r = math.hypot(x, z)
            if r > 72:
                continue
            phi = phi_of(x, z)
            for y in range(0, ROCK_TOP + 1):
                if r <= rock_R(phi, y):
                    S.rock.add((x, y, z))
                    bp.set(x, y, z, rock_block(x, y, z))
                elif y > 0:
                    break
            sr = strand_r(phi)
            if (x, 0, z) not in S.rock and r <= sr:
                h = hash01(x, z, 31)
                edge = r > sr - 2.5
                spec = ("mossy_cobblestone" if h < 0.25 else "cobblestone" if h < 0.45 else "gravel" if edge and h < 0.7
                        else "sand" if h < 0.8 else "andesite")
                if spec == "gravel":
                    bp.set(x, -1, z, "cobblestone")
                bp.set(x, 0, z, spec)
            # talus under the sea: a rock skirt widening down to the sea floor (a shell: the inside stays sea bed)
            for y in range(-1, -13, -1):
                tr = sr + (-y) * 0.75 + (fbm(phi * 3.0, y * 1.5, 5.0, 29) - 0.5) * 4
                if tr - 3.2 <= r <= tr:
                    h = hash3(x, y, z, 33)
                    bp.set(x, y, z, "gravel" if h < 0.12 and y < -2 and bp.get(x, y - 1, z) else
                           "mossy_cobblestone" if h < 0.35 else "stone" if h < 0.7 else "andesite")
    # the gravel needs a floor: cobble under any gravel on the talus
    for (x, y, z), b in list(bp.blocks.items()):
        if b[0] == "minecraft:gravel" and empty(bp.get(x, y - 1, z)):
            bp.set(x, y, z, "cobblestone")


# ------------------------------------------------------------------ walkways
PAVE = {
    "main": (("stone_bricks", "stone_brick_slab"), ("polished_andesite", "polished_andesite_slab"),
             ("cobblestone", "cobblestone_slab"), ("andesite", "andesite_slab"), ("stone_bricks", "stone_brick_slab")),
    "side": (("cobblestone", "cobblestone_slab"), ("mossy_cobblestone", "mossy_cobblestone_slab"),
             ("stone", "stone_slab"), ("cobblestone", "cobblestone_slab")),
    "abbey": (("polished_andesite", "polished_andesite_slab"), ("stone_bricks", "stone_brick_slab"),
              ("polished_andesite", "polished_andesite_slab")),
    "crypt": (("tuff_bricks", "tuff_brick_slab"), ("polished_tuff", "polished_tuff_slab"),
              ("tuff_bricks", "tuff_brick_slab")),
}


def raster(S, pid, pts, hw, sky=True, mat="main", clear=5):
    """Claim the cells within hw of the polyline pts [(x, z, feet)]: the walkway's feet height is the one of the
    nearest centreline point (a cell keeps the first path that claimed it)."""
    S.paths[pid] = dict(sky=sky, mat=mat, clear=clear)
    dense = []
    for (x0, z0, t0), (x1, z1, t1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) / 0.25))
        for i in range(n):
            f = i / n
            dense.append((x0 + (x1 - x0) * f, z0 + (z1 - z0) * f, t0 + (t1 - t0) * f))
    dense.append(pts[-1])
    for px, pz, t in dense:
        for x in range(math.floor(px - hw), math.ceil(px + hw) + 1):
            for z in range(math.floor(pz - hw), math.ceil(pz + hw) + 1):
                d = math.hypot(x - px, z - pz)
                if d <= hw:
                    c = S.claims.get((x, z))
                    if c is None or (c[2] == pid and d < c[0]):
                        S.claims[(x, z)] = [d, t, pid]
    return dense


def square(S, pid, cells, t, sky=True, mat="main", clear=5):
    S.paths[pid] = dict(sky=sky, mat=mat, clear=clear)
    for c in cells:
        S.claims[c] = [0.0, t, pid]


def disk(cx, cz, r):
    return [(x, z) for x in range(math.floor(cx - r), math.ceil(cx + r) + 1)
            for z in range(math.floor(cz - r), math.ceil(cz + r) + 1) if math.hypot(x - cx, z - cz) <= r]


def rect(x0, z0, x1, z1):
    return [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]


def walk_cell(S, x, z, t, mat, clear=5, sky=False):
    """Floor (full block, or a bottom slab for a half height), headroom above, support below."""
    bp = S.bp
    n = math.floor(t)
    half = t - n > 0.25
    k = int(hash01(x, z, 51) * len(PAVE[mat]))
    full, sl = PAVE[mat][k]
    S.set(x, n - 1, z, full)
    top = n
    if half:
        S.set(x, n, z, slab(sl))
        top = n + 1
    for y in range(top, n + clear + (1 if half else 0)):
        S.air(x, y, z)
    if sky:
        for y in range(n + clear + 1, 72):
            if (x, y, z) in S.rock:
                bp.remove(x, y, z)
                S.rock.discard((x, y, z))
    y = n - 2
    while y >= -6 and empty(bp.get(x, y, z)):
        S.set(x, y, z, SUPPORT.pick(x, y, z))
        y -= 1


def lay_paths(S):
    for (x, z), (d, t, pid) in S.claims.items():
        t = round(t * 2) / 2
        S.t[(x, z)] = t
        S.cols.add((x, z))
        o = S.paths[pid]
        walk_cell(S, x, z, t, o["mat"], o["clear"], o["sky"])


# the route: Grande Rue (A), first hairpin, upper street (B), second hairpin, abbey street (C) under the platform
LEG_A = [(44, 4, 1), (43, 20, 1.5), (42, 40, 2.5), (42, 58, 3.5), (42, 74, 3.5), (41, 95, 5.5), (40, 120, 8.5),
         (39, 140, 11), (38, 156, 12.5), (38, 174, 12.5), (36, 192, 14), (34, 208, 15.5)]
HAIR_1 = [(32, 216, 16.5), (29, 220, 17.5), (26, 215, 18.5)]
LEG_B = [(26, 205, 19.5), (26, 175, 22), (26, 152, 24)]
HAIR_2 = [(24, 146, 25), (21, 148, 25.8)]
LEG_C = [(8, 16, 27), (-20, 16, 35)]
GRAND_DEGRE = [(-20, 16, 35), (-22, 14, 36), (-22, 2, 42), (-22, 0, 42)]
WELL_SQ = P(43, 66)
PARVIS = P(38, 165)


def polar(lst):
    return [(*P(r, a), t) for r, a, t in lst]


def route(S):
    """Rasterise every walkway (squares first, they win), then lay them."""
    square(S, "court", rect(-9, -51, 9, -42), 1)
    square(S, "barbican", rect(-6, -66, 6, -57), 1, mat="side")
    square(S, "gate", rect(-2, -56, 2, -52), 1, sky=False, clear=4)
    square(S, "outer_gate", rect(-2, -68, 2, -67), 1, sky=False, clear=4)
    square(S, "well", disk(*WELL_SQ, 5.2), 3.5)
    square(S, "parvis", disk(*PARVIS, 6.6), 12.5)
    square(S, "quay", rect(-49, 21, -36, 32), 1, mat="side")
    S.main = polar(LEG_A + HAIR_1 + LEG_B + HAIR_2) + LEG_C
    S.main_dense = raster(S, "main", S.main, 2.5)
    raster(S, "degre", GRAND_DEGRE, 1.5, mat="abbey")
    # ruelles from the street to the rampart walk (loops) and the stair from the gate court up to the walk
    for phi, t0 in ((120, 8.5), (172, 12.5)):
        a, b = P(42.5, phi), P(53.0, phi)
        raster(S, f"ruelle{phi}", [(a[0], a[1], t0), (b[0], b[1], WALK + 1)], 1.5, mat="side")
    raster(S, "rampart_stair", [(-6, -47.5, 1), (-24, -48, 10), (-27, -48, 10)], 1.5, mat="side")
    # the strand path from the barbican's postern round the west to the harbour (the way back from the vault)
    pts = [(-9, -62), (-15, -63)] + [P(61, a) for a in (338, 318, 298, 278, 258)] + [(-46, 30)]
    raster(S, "strand", [(x, z, 1) for x, z in pts], 1.5, mat="side")
    lay_paths(S)


# ------------------------------------------------------------------ ramparts, towers, gate, barbican
def ramparts(S):
    bp = S.bp
    for x in range(-58, 59):
        for z in range(-58, 59):
            r = math.hypot(x, z)
            phi = phi_of(x, z)
            if not in_ramparts(phi) or not RING0 <= r <= RING1 + 1.2:
                continue
            batter = r > RING1
            top = 2 if batter else WALK
            for y in range(0, top + 1):
                S.set(x, y, z, WALL.pick(x, y, z) if y > 1 else "mossy_stone_bricks" if hash3(x, y, z) < 0.4
                      else "cobblestone")
            if batter:
                S.set(x, 3, z, stair("stone_brick_stairs", facing_to(x, z)))
                continue
            S.set(x, WALK, z, "stone_bricks" if hash01(x, z, 3) < 0.6 else "polished_andesite")
            if r > RING1 - 0.9:
                k = int(math.radians(phi) * RING_C) // 2
                if k % 2 == 0:
                    S.set(x, WALK + 1, z, "stone_bricks")
                    S.set(x, WALK + 2, z, "stone_brick_slab[type=bottom,waterlogged=false]")
                else:
                    S.set(x, WALK + 1, z, "stone_brick_slab[type=bottom,waterlogged=false]")
            # machicolation corbels under the parapet
            if r > RING1 - 0.9:
                ox, oz = round(x + (x / r)), round(z + (z / r))
                if empty(bp.get(ox, WALK - 1, oz)) and math.hypot(ox, oz) > RING1 + 0.4:
                    S.set(ox, WALK - 1, oz, stair("stone_brick_stairs", facing_to(ox, oz, out=False), "top"))
    for phi in TOWERS:
        tower(S, phi, RING_C, 4.5, WALK + 5)
    tower(S, GABRIEL, RING_C + 0.5, 5.5, 20, light=True)
    # the king's gate: a passage through the ring between two towers
    for sx in (-6, 6):
        tower(S, None, None, 3.5, 16, at=(sx, -53))
    for x in range(-2, 3):
        for z in range(-56, -51):
            for y in range(1, 6):
                if y < 5 or abs(x) < 2:
                    S.air(x, y, z)
            S.set(x, 0, z, "stone_bricks")
        S.set(x, 5, -56, "iron_bars")
    for z in (-56, -51):
        for x in (-2, 2):
            S.set(x, 5, z, stair("stone_brick_stairs", "east" if x < 0 else "west", "top"))
    S.set(0, 7, -56, "chiseled_stone_bricks")
    banner = with_props("blue_wall_banner", facing="north")
    S.set(-1, 7, -57, banner)
    S.set(1, 7, -57, banner)
    barbican(S)


def facing_to(x, z, out=True):
    """Horizontal facing pointing away from (out) or toward the island centre."""
    dx, dz = (x, z) if out else (-x, -z)
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def tower(S, phi, r_c, r, top, light=False, at=None):
    bp = S.bp
    if at:
        cx, cz = at
    else:
        cx, cz = P(r_c, phi)
        cx, cz = round(cx), round(cz)
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if d > r + 1.3:
                continue
            for y in range(-2, top + 1):
                if d > r + 0.4:
                    if y <= 2:
                        S.set(x, y, z, "cobblestone" if y < 2 else stair("stone_brick_stairs", facing_to(x - cx, z - cz)))
                    continue
                inner = d <= r - 1.1
                if inner and WALK + 1 <= y <= top - 1:
                    S.air(x, y, z)
                elif inner and y == WALK:
                    S.set(x, y, z, "spruce_planks")
                else:
                    S.set(x, y, z, WALL.pick(x, y, z) if y > 1 else "mossy_stone_bricks")
            # corbelled crown
            if r - 0.6 < d <= r + 0.4:
                S.set(x, top, z, "stone_bricks")
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            d = math.hypot(x - cx, z - cz)
            if r + 0.4 < d <= r + 1.4:
                S.set(x, top - 1, z, stair("stone_brick_stairs", facing_to(x - cx, z - cz, out=False), "top"))
    # arrow slits and walk doorways
    for k in range(4):
        dx, dz = ((1, 0), (0, 1), (-1, 0), (0, -1))[k]
        x, z = round(cx + dx * r), round(cz + dz * r)
        S.set(x, WALK + 3, z, "air")
        S.set(x, WALK + 2, z, "air")
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            rr = math.hypot(x, z)
            if RING0 + 0.3 <= rr <= RING1 - 1.0 and math.hypot(x - cx, z - cz) <= r + 0.5 and at is None:
                for y in (WALK + 1, WALK + 2, WALK + 3):
                    S.air(x, y, z)
                S.set(x, WALK, z, "stone_bricks")
    if light:
        for y in range(top + 1, top + 4):
            for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
                S.set(x, y, z, "stone_brick_wall")
        S.set(cx, top + 1, cz, "sea_lantern")
        S.set(cx, top + 2, cz, "sea_lantern")
        bp.cone_roof(cx, top + 4, cz, 3, SLATE_ST, cap="lightning_rod[facing=up,powered=false,waterlogged=false]")
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if max(abs(x - cx), abs(z - cz)) == 2:
                    S.set(x, top + 3, z, "stone_bricks")
    else:
        bp.cone_roof(cx, top + 1, cz, round(r) + 1, SLATE_ST, cap="lightning_rod[facing=up,powered=false,waterlogged=false]")
    # a lantern inside at the walk
    S.set(cx, top - 1, cz, HLANTERN)


def barbican(S):
    for x in range(-8, 9):
        for z in range(-68, -55):
            wall = x <= -7 or x >= 7 or z <= -67
            for y in range(-6, 8 if wall else 1):
                S.set(x, y, z, WALL.pick(x, y, z) if y > 0 else "cobblestone")
            if wall:
                k = (x + z) % 2
                S.set(x, 8, z, "stone_bricks" if k == 0 else "stone_brick_slab[type=bottom,waterlogged=false]")
    # the outer gate (north) and the postern to the strand (west)
    for x in range(-2, 3):
        for y in range(1, 6):
            if y < 5 or abs(x) < 2:
                S.air(x, y, -67)
                S.air(x, y, -68)
    for z in range(-63, -60):
        for y in range(1, 4):
            S.air(-8, y, z)
            S.air(-7, y, z)
        S.set(-8, 0, z, "cobblestone")
        S.set(-7, 0, z, "cobblestone")
    S.set(0, 6, -69, "chiseled_stone_bricks")
    for x in (-3, 3):
        S.set(x, 6, -69, LANTERN)


# ------------------------------------------------------------------ houses
def place_houses(S, pts, side, seed, rng_w=(5, 8), rng_d=(5, 7), storeys=(2, 3), chests=0, skip=()):
    """Stone houses along a walkway, fronts on the street, on the outer (away from the island centre) or inner side.
    Each one is skipped when it would touch another walkway, a reserved volume or another house."""
    dense = []
    for (x0, z0, t0), (x1, z1, t1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0)))
        for i in range(n):
            f = i / n
            dense.append((x0 + (x1 - x0) * f, z0 + (z1 - z0) * f))
    i = 2
    k = 0
    placed = 0
    chested = 0
    while i < len(dense) - 2:
        px, pz = dense[i]
        tx, tz = dense[i + 1][0] - dense[i - 1][0], dense[i + 1][1] - dense[i - 1][1]
        nx, nz = tz, -tx
        if (nx * px + nz * pz > 0) != (side == "outer"):
            nx, nz = -nx, -nz
        if abs(nx) >= abs(nz):
            sx, sz = (1 if nx > 0 else -1), 0
        else:
            sx, sz = 0, (1 if nz > 0 else -1)
        cx, cz = round(px), round(pz)
        h = hash01(cx, cz, seed + k)
        w = rng_w[0] + int(h * (rng_w[1] - rng_w[0] + 1))
        d = rng_d[0] + int(hash01(cz, cx, seed + 3) * (rng_d[1] - rng_d[0] + 1))
        st = storeys[int(hash01(cx + 5, cz, seed) * len(storeys))]
        ok = False
        if any(math.hypot(cx - a, cz - b) < 6 for a, b in skip):
            i += 2
            continue
        for ww, dd in ((w, d), (w - 1, d), (w - 2, d), (5, d), (4, d)):
            r = try_house(S, cx, cz, sx, sz, ww, dd, st, seed + k)
            if r:
                ok = True
                k += 1
                if chested < chests and "chest_at" in S.houses[-1]:
                    S.houses[-1]["chest"] = True
                    chested += 1
                placed += 1
                i += ww + 1
                break
        if not ok:
            i += 1
    return placed


def try_house(S, cx, cz, sx, sz, w, d, st, seed):
    """Fit a house of width w (along the street) and depth up to d (away from it) whose front follows the street
    edge; the cells between a ragged street edge and the front become a paved forecourt."""
    if w < 4:
        return S.why("narrow")
    ux, uz = (0, 1) if sx else (1, 0)
    us = range(-(w // 2), -(w // 2) + w)

    def cell(u, k):
        return (cx + ux * u + sx * k, cz + uz * u + sz * k)

    fronts = []
    for u in us:
        k = 0
        while cell(u, k) in S.cols and k < 8:
            k += 1
        fronts.append(k)
    front = max(fronts)
    if fronts[w // 2] == 0 or front >= 8 or front - min(fronts) > 3:
        return S.why("front")
    door_out = cell(0, fronts[w // 2] - 1)
    if door_out not in S.t:
        return S.why("door")
    t0 = S.t[door_out]
    f = math.ceil(t0)
    bp = S.bp
    for dd in range(d, 3, -1):
        a0, a1 = front, front + dd - 1
        c0, c1 = cell(us[0], a0), cell(us[-1], a1)
        x0, x1 = sorted((c0[0], c1[0]))
        z0, z1 = sorted((c0[1], c1[1]))
        top = f + 5 * st - 1
        roof_top = top + 2 + (min(x1 - x0, z1 - z0) + 3) // 2
        lowest = f
        bad = None
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                ring = x < x0 or x > x1 or z < z0 or z > z1
                if ring:
                    if (x, z) in S.cols and top + 1 - S.t[(x, z)] < 4 and S.t[(x, z)] <= roof_top:
                        bad = "ring street"
                    continue
                if (x, z) in S.cols:
                    bad = "street"
                elif (x, z) in S.house_cols:
                    bad = "house"
                elif math.hypot(x, z) > RING0 - 0.3 and in_ramparts(phi_of(x, z)):
                    bad = "rampart"
                else:
                    y = f - 2
                    while y > -6 and empty(bp.get(x, y, z)):
                        y -= 1
                    lowest = min(lowest, y)
            if bad:
                break
        if not bad and S.blocked_box(x0, lowest, z0, x1, roof_top, z1):
            bad = "box"
        if bad:
            S.why(bad)
            continue
        # forecourt: pave the gap between the street edge and the front at the door's level
        for i, u in enumerate(us):
            for k in range(fronts[i], front):
                c = cell(u, k)
                pid = S.claims[door_out][2]
                S.claims[c] = [0.0, t0, pid]
                S.t[c] = t0
                S.cols.add(c)
                walk_cell(S, c[0], c[1], t0, "main", 5)
        facing = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(sx, sz)]
        door = cell(0, front)
        S.houses.append(dict(box=(x0, z0, x1, z1), f=f, st=st, facing=facing, door=door, seed=seed))
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                S.house_cols.add((x, z))
        build_house(S, x0, z0, x1, z1, f, st, facing, door, seed)
        return True
    return False


def build_house(S, x0, z0, x1, z1, f, st, facing, door, seed):
    bp = S.bp
    timber = hash01(x0, z0, seed) < 0.3
    top = f + 5 * st - 1
    pal = Palette({"stone_bricks": 3, "cobblestone": 3, "andesite": 2, "tuff": 1, "mossy_cobblestone": 1},
                  seed=seed, scale=2.2)
    gable_x = (x1 - x0) >= (z1 - z0)
    if hash01(z0, x0, seed + 9) < 0.35:
        gable_x = not gable_x
    lad = None
    for cand in ((x0 + 1, z0 + 1), (x1 - 1, z1 - 1), (x0 + 1, z1 - 1), (x1 - 1, z0 + 1)):
        if abs(cand[0] - door[0]) + abs(cand[1] - door[1]) > 2:
            lad = cand
            break
    if lad is None:
        lad = (x0 + 1, z0 + 1)
        st = 1
        top = f + 4
    lad_face = "east" if lad[0] == x0 + 1 else "west"
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            y = f - 2
            while y > -7 and empty(bp.get(x, y, z)):
                S.set(x, y, z, SUPPORT.pick(x, y, z))
                y -= 1
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            S.set(x, f - 1, z, pal.pick(x, f - 1, z) if edge else "spruce_planks")
            for y in range(f, top + 1):
                k = (y - f) // 5
                lvl = (y - f) % 5
                if edge:
                    if corner:
                        spec = "stone_bricks" if (y + x + z) % 2 else "polished_andesite"
                    elif timber and k >= 1:
                        spec = "stripped_dark_oak_log[axis=y]" if (x + z) % 3 == 0 or lvl == 4 else "calcite"
                        if lvl == 4:
                            spec = "stripped_dark_oak_log[axis=x]" if z in (z0, z1) else "stripped_dark_oak_log[axis=z]"
                    else:
                        spec = pal.pick(x, y, z)
                    if lvl == 4 and not timber:
                        spec = "stone_bricks"
                    S.set(x, y, z, spec)
                else:
                    if lvl == 4 and k < st - 1 and (x, z) != lad:
                        S.set(x, y, z, "spruce_planks")
                    else:
                        S.air(x, y, z)
    # windows: where the outside is open
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)) or (x in (x0, x1) and z in (z0, z1)):
                continue
            ox = x + (-1 if x == x0 else 1 if x == x1 else 0)
            oz = z + (-1 if z == z0 else 1 if z == z1 else 0)
            if (x + z) % 3 != 0:
                continue
            for k in range(st):
                yy = f + 5 * k + 1
                if k == 0 and (abs(x - door[0]) + abs(z - door[1]) < 2):
                    continue
                if empty(bp.get(ox, yy, oz)) and empty(bp.get(ox, yy + 1, oz)):
                    S.set(x, yy, z, "glass_pane")
                    S.set(x, yy + 1, z, "glass_pane")
    # door to the street, a lantern beside it
    dx, dz = door
    S.air(dx, f, dz)
    S.air(dx, f + 1, dz)
    bp.door(dx, f, dz, facing, wood="spruce")
    S.set(dx, f + 2, dz, "stone_bricks")
    # ladder to the upper floors
    for k in range(st - 1):
        bp.ladder(lad[0], f + 5 * k, lad[1], f + 5 * k + 4, lad_face)
    # roof
    house_roof(S, x0, z0, x1, z1, top + 1, "x" if gable_x else "z", "stone_bricks" if not timber else "calcite")
    # chimney on one gable
    chx, chz = (x0, (z0 + z1) // 2 + 1) if not gable_x else ((x0 + x1) // 2 + 1, z0)
    if gable_x:
        chx, chz = x1, (z0 + z1) // 2
    ridge = top + 2 + (min(x1 - x0, z1 - z0) + 2) // 2
    for y in range(top + 1, ridge + 2):
        S.set(chx, y, chz, "cobblestone" if y < ridge + 1 else "cobblestone_wall")
    # furnishing
    inner = [(x, z) for x in range(x0 + 1, x1) for z in range(z0 + 1, z1)
             if (x, z) != lad and abs(x - dx) + abs(z - dz) > 1]
    budget = (x1 - x0 - 1) * (z1 - z0 - 1) - (1 if st > 1 else 0) - 5
    if inner and budget >= 3:
        tx, tz = inner[len(inner) // 2]
        S.set(tx, f, tz, "spruce_fence")
        S.set(tx, f + 1, tz, LANTERN)
        bx, bz = inner[0]
        S.bp.barrel(bx, f, bz, "up")
        S.houses[-1]["chest_at"] = inner[-1]
        if st > 1 and len(inner) > 2:
            ux, uz = inner[-1]
            S.set(ux, f + 5, uz, "white_wool")
        hx, hz = inner[-1]
        if (hx, hz) != (bx, bz) and (hx, hz) != (tx, tz):
            S.set(hx, f, hz, "furnace[facing=north,lit=false]")
    S.set(dx - (1 if facing in ("north", "south") else 0), f + 2, dz - (1 if facing in ("east", "west") else 0),
          "air")
    out = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
    lx, lz = dx + out[0], dz + out[1]
    if empty(bp.get(lx, f + 2, lz)):
        S.set(lx, f + 2, lz, with_props("wall_torch", facing=facing))


def house_roof(S, x0, z0, x1, z1, y, axis, fill):
    """Slate gable with a one-block overhang, kept off the neighbours' footprints (terraced houses share walls),
    a dark eave line under the overhang."""
    own = {(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)}

    def put(x, yy, z, spec):
        if (x, z) in own or (x, z) not in S.house_cols:
            S.set(x, yy, z, spec)

    if axis == "x":
        lo, hi, a0, a1 = z0 - 1, z1 + 1, x0 - 1, x1 + 1
    else:
        lo, hi, a0, a1 = x0 - 1, x1 + 1, z0 - 1, z1 + 1
    layer = 0
    while lo + layer <= hi - layer:
        yy = y + layer
        for a in range(a0, a1 + 1):
            for b, fc in ((lo + layer, "south" if axis == "x" else "east"), (hi - layer, "north" if axis == "x" else "west")):
                x, z = (a, b) if axis == "x" else (b, a)
                if lo + layer == hi - layer:
                    put(x, yy, z, SLATE_SL + "[type=bottom,waterlogged=false]")
                else:
                    put(x, yy, z, stair(SLATE_ST, fc))
                if layer == 0 and (x, z) not in own:
                    put(x, yy - 1, z, stair("spruce_stairs", {"south": "north", "north": "south", "east": "west",
                                                              "west": "east"}[fc], "top"))
        for b in range(lo + layer + 1, hi - layer):
            for a in (a0 + 1, a1 - 1):
                x, z = (a, b) if axis == "x" else (b, a)
                put(x, yy, z, fill)
        layer += 1


def town(S):
    A = polar(LEG_A)
    B = polar(LEG_B)
    place_houses(S, A, "outer", 101, chests=2, skip=(WELL_SQ,))
    place_houses(S, A, "inner", 211, storeys=(2, 1, 2))
    place_houses(S, A, "inner", 213, storeys=(1,), rng_w=(4, 6), rng_d=(4, 5))
    place_houses(S, B, "inner", 307, storeys=(2, 3))
    place_houses(S, B, "outer", 311, storeys=(1,), rng_w=(4, 6), rng_d=(4, 5))
    place_houses(S, A, "outer", 103, storeys=(2, 1), rng_w=(4, 6), rng_d=(4, 6))
    place_houses(S, LEG_C, "outer", 401, rng_w=(5, 7), rng_d=(4, 5), storeys=(1, 2))
    for hs in S.houses:
        if hs.get("chest") and "chest_at" in hs:
            x, z = hs["chest_at"]
            S.bp.chest(x, hs["f"], z, "north", loot=LOOT + "abbey_town")


# ------------------------------------------------------------------ the summit: platform, church, spire
NAVE = (-18, 4)        # nave x (west facade wall at -18)
CROSS = (5, 17)        # crossing tower x (walls z -6..6)
CHOIR = (18, 27)       # choir x, apse centre (27, 0)
NAVE_TOP = CH_F + 26   # last air of the nave vault (27 high)
TOWER_TOP = 96
SPIRE_TOP = 130


def platform(S):
    bp = S.bp
    x0, z0, x1, z1 = PLAT
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if (x, z) in S.cols:
                continue
            S.set(x, CH_F - 1, z, "polished_andesite" if (x + z) % 2 else "stone_bricks")
            y = CH_F - 2
            while y >= 0 and (empty(bp.get(x, y, z)) or (x, y, z) in S.rock and y > ROCK_TOP - 1):
                edge = x in (x0, x1) or z in (z0, z1)
                S.set(x, y, z, ABBEY.pick(x, y, z) if edge else SUPPORT.pick(x, y, z))
                y -= 1
            # buttresses on the substructure walls, every 6 blocks
            for (ex, ez, ox, oz) in ((x, z0, 0, -1), (x, z1, 0, 1), (x0, z, -1, 0), (x1, z, 1, 0)):
                if (ex, ez) != (x, z) or (ex == x0 and ox == -1):
                    continue
                k = (x if oz else z) % 6
                if k not in (0, 1):
                    continue
                for dep in (1, 2):
                    bx, bz = x + ox * dep, z + oz * dep
                    if (bx, bz) in S.cols or (bx, bz) in S.house_cols:
                        break
                    yy = CH_F - 3 - dep * 2
                    S.set(bx, yy + 1, bz, stair("stone_brick_stairs", facing_to(-ox, -oz)))
                    while yy >= 0 and (empty(bp.get(bx, yy, bz)) or (bx, yy, bz) in S.rock):
                        if (bx, yy, bz) in S.rock and hash3(bx, yy, bz) < 0.5:
                            break
                        S.set(bx, yy, bz, "stone_bricks")
                        yy -= 1
    # parapet round the platform edge
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)) or x == x0 or (x, z) in S.cols:
                continue
            S.set(x, CH_F, z, "stone_brick_wall")
            if (x + z) % 8 == 0:
                S.set(x, CH_F + 1, z, LANTERN)


def church(S):
    bp = S.bp
    f = CH_F

    def inside_plan(x, z):
        """0 outside, 1 wall, 2 inside (air), with the part name."""
        if 7 <= x <= 15 and 5 < abs(z) <= 11:
            return 2, "transept"
        if NAVE[0] <= x <= CHOIR[1]:
            if abs(z) <= 5 and x >= NAVE[0] + 2:
                return 2, "nave"
            if abs(z) == 6 or (x in (NAVE[0], NAVE[0] + 1) and abs(z) <= 6):
                return 1, "nave"
        if CHOIR[1] < x and math.hypot(x - CHOIR[1], z) <= 6.4:
            return (2 if math.hypot(x - CHOIR[1], z) <= 5.4 else 1), "apse"
        if 6 <= x <= 16 and abs(z) <= 12:
            if 7 <= x <= 15 and abs(z) <= 11:
                return 2, "transept"
            return 1, "transept"
        return 0, None

    for x in range(NAVE[0] - 3, CHOIR[1] + 9):
        for z in range(-14, 15):
            k, part = inside_plan(x, z)
            if not k:
                continue
            top = f + (21 if part == "transept" and abs(z) > 5 else 26)
            S.set(x, f - 1, z, ("polished_andesite" if (x + z) % 2 else "polished_diorite") if k == 2 else "stone_bricks")
            for y in range(f, top + 2):
                if k == 2 and y <= top:
                    S.air(x, y, z)
                else:
                    S.set(x, y, z, ABBEY.pick(x, y, z) if y > f + 1 else "stone_bricks")
    # the nave walls stand on arches over the transept arms (clerestory above the transept vaults)
    for x in range(7, 16):
        for z in (-6, 6):
            for y in range(f + 22, f + 28):
                S.set(x, y, z, ABBEY.pick(x, y, z))
    # crossing: open from the floor into the tower and the spire
    for x in range(7, 16):
        for z in range(-4, 5):
            for y in range(f, TOWER_TOP + 1):
                S.air(x, y, z)
    # tower walls from the roofs up
    for x in range(CROSS[0], CROSS[1] + 1):
        for z in range(-6, 7):
            wall = x <= CROSS[0] + 1 or x >= CROSS[1] - 1 or abs(z) >= 5
            if not wall:
                continue
            for y in range(NAVE_TOP - 4, TOWER_TOP + 1):
                S.set(x, y, z, ABBEY.pick(x, y, z))
    # belfry lancets, string courses, corner pinnacles
    for u in (-3, -2, 2, 3):
        for y in range(TOWER_TOP - 12, TOWER_TOP - 2):
            for x in (CROSS[0], CROSS[0] + 1, CROSS[1] - 1, CROSS[1]):
                S.air(x, y, u)
    for u in (8, 9, 13, 14):
        for y in range(TOWER_TOP - 12, TOWER_TOP - 2):
            for z in (-6, -5, 5, 6):
                S.air(u, y, z)
    for y in (NAVE_TOP + 3, TOWER_TOP - 13, TOWER_TOP):
        for x in range(CROSS[0] - 1, CROSS[1] + 2):
            for z in range(-7, 8):
                if (x in (CROSS[0] - 1, CROSS[1] + 1) or abs(z) == 7) and empty(bp.get(x, y, z)):
                    S.set(x, y, z, stair("stone_brick_stairs", facing_to(x - 11, z, out=False), "top"))
    for cx, cz in ((CROSS[0], -6), (CROSS[1], -6), (CROSS[0], 6), (CROSS[1], 6)):
        for y in range(TOWER_TOP + 1, TOWER_TOP + 8):
            S.set(cx, y, cz, "stone_bricks" if y < TOWER_TOP + 5 else "stone_brick_wall")
        S.set(cx, TOWER_TOP + 8, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # bells under a beam in the belfry
    for x in range(7, 16):
        S.set(x, TOWER_TOP - 3, 0, "stripped_dark_oak_log[axis=x]")
    for x in (9, 13):
        S.set(x, TOWER_TOP - 4, 0, "bell[attachment=ceiling,facing=north,powered=false]")
    # the spire: octagonal, crockets on its ridges, gilded archangel at the tip
    cx, cz = 11, 0
    h = SPIRE_TOP - TOWER_TOP
    for y in range(TOWER_TOP + 1, SPIRE_TOP + 1):
        rr = 6.2 * (1 - (y - TOWER_TOP - 1) / h) + 0.4
        for x in range(cx - 7, cx + 8):
            for z in range(cz - 7, cz + 8):
                dx, dz = abs(x - cx), abs(z - cz)
                d = max(dx, dz, (dx + dz) / 1.414)
                if rr - 1.0 < d <= rr:
                    ridge = abs(dx - dz) <= 0.5 or dx == 0 or dz == 0
                    S.set(x, y, z, "stone_bricks" if ridge else SLATE)
                    if ridge and (y - TOWER_TOP) % 4 == 0 and d > 1.5:
                        ox, oz = x + (1 if x > cx else -1 if x < cx else 0), z + (1 if z > cz else -1 if z < cz else 0)
                        if empty(bp.get(ox, y, oz)):
                            S.set(ox, y, oz, stair("stone_brick_stairs", facing_to(ox - cx, oz - cz, out=False)))
    # lucarnes at the spire foot
    for (x, z, fc) in ((cx, cz - 6, "north"), (cx, cz + 6, "south"), (cx - 6, cz, "west"), (cx + 6, cz, "east")):
        for y in range(TOWER_TOP + 2, TOWER_TOP + 5):
            S.air(x, y, z)
    S.set(cx, SPIRE_TOP + 1, cz, "gold_block")
    S.set(cx, SPIRE_TOP + 2, cz, "gold_block")
    S.set(cx, SPIRE_TOP + 3, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # nave and choir roofs: steep slate gables; transept roofs across
    for x in range(NAVE[0], CHOIR[1] + 1):
        if CROSS[0] <= x <= CROSS[1]:
            continue
        steep_gable(S, x, "z", -7, 7, NAVE_TOP + 2, 1.6)
    for z in list(range(-13, -6)) + list(range(7, 14)):
        steep_gable(S, z, "x", 5, 17, f + 23, 1.6)
    # apse roof: a half cone
    for y in range(NAVE_TOP + 2, NAVE_TOP + 12):
        rr = 7.4 - (y - NAVE_TOP - 2) * 0.8
        for x in range(CHOIR[1], CHOIR[1] + 9):
            for z in range(-8, 9):
                d = math.hypot(x - CHOIR[1], z)
                if d <= rr and (d > rr - 1.6 or y == NAVE_TOP + 2):
                    S.set(x, y, z, SLATE if d < rr - 0.6 else stair(SLATE_ST, facing_to(x - CHOIR[1], z, out=False)))
    # buttresses with pinnacles along nave and choir
    for x in (-15, -10, -5, 0, 20, 24):
        for sz in (-1, 1):
            for dep in (1, 2, 3):
                z = sz * (6 + dep)
                ytop = NAVE_TOP - 2 - dep * 4
                for y in range(f - 1, ytop + 1):
                    S.set(x, y, z, "stone_bricks")
                S.set(x, ytop + 1, z, stair("stone_brick_stairs", "north" if sz > 0 else "south"))
            z = sz * 9
            S.set(x, NAVE_TOP - 13, z, "stone_brick_wall")
            S.set(x, NAVE_TOP - 12, z, "stone_brick_wall")
            S.set(x, NAVE_TOP - 11, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # lancet windows
    glass = ("light_blue_stained_glass_pane", "white_stained_glass_pane", "blue_stained_glass_pane")
    for xc in (-13, -8, -3, 2, 22):
        for z in (-6, 6):
            for x in (xc, xc + 1):
                for y in range(f + 6, f + 22):
                    if y == f + 21 and x == xc + 1:
                        continue
                    S.set(x, y, z, glass[(y // 3 + x) % 3])
                S.set(x, f + 5, z, stair("stone_brick_stairs", "north" if z < 0 else "south", "top"))
    for a in (-60, -30, 0, 30, 60):
        x, z = round(CHOIR[1] + 6 * math.cos(math.radians(a))), round(6 * math.sin(math.radians(a)))
        for y in range(f + 6, f + 21):
            S.set(x, y, z, glass[(y // 3) % 3])
    for z in (-12, 12):
        for x in (10, 11, 12):
            for y in range(f + 4, f + 18):
                S.set(x, y, z, glass[(y + x) % 3])
    facade(S)
    church_interior(S)


def steep_gable(S, a, axis, lo, hi, y0, k):
    """One slice of a steep gable roof (ridge along the other axis) at coordinate a: slate over the vault."""
    mid = (lo + hi) / 2
    half = (hi - lo) / 2
    for u in range(lo, hi + 1):
        h = y0 + int((half - abs(u - mid)) * k)
        for y in range(y0, h + 1):
            x, z = (a, u) if axis == "z" else (u, a)
            if y == h and u != mid:
                fc = ("south" if u < mid else "north") if axis == "z" else ("east" if u < mid else "west")
                S.set(x, y, z, stair(SLATE_ST, fc))
            else:
                S.set(x, y, z, SLATE if y >= h - 1 else "stone_bricks")
        if u == lo or u == hi:
            x, z = (a, u) if axis == "z" else (u, a)
            S.set(x, y0 - 1, z, stair(SLATE_ST, ("north" if u == lo else "south") if axis == "z" else
                                      ("west" if u == lo else "east"), "top"))


def facade(S):
    """West front: portal with a wicket door, a rose window, twin turrets."""
    f = CH_F
    x = NAVE[0]
    for z in range(-7, 8):
        for y in range(NAVE_TOP + 2, NAVE_TOP + 14):
            if abs(z) <= 7 - (y - NAVE_TOP - 2) * 0.6:
                S.set(x, y, z, ABBEY.pick(x, y, z))
                S.set(x + 1, y, z, ABBEY.pick(x + 1, y, z))
    # portal: recessed arch 5 x 9, a timber infill with the wicket door
    for z in range(-2, 3):
        for y in range(f, f + 9):
            if y == f + 8 and abs(z) == 2:
                continue
            S.air(x, y, z)
            S.set(x + 1, y, z, "dark_oak_planks")
    for z in (-3, 3):
        for y in range(f, f + 9):
            S.set(x - 1, y, z, "polished_andesite")
    for z in range(-3, 4):
        S.set(x - 1, f + 9, z, stair("stone_brick_stairs", "east", "top"))
    for z in (-1, 0):
        S.air(x + 1, f, z)
        S.air(x + 1, f + 1, z)
    S.bp.door(x + 1, f, -1, "west", wood="dark_oak", hinge="left")
    S.bp.door(x + 1, f, 0, "west", wood="dark_oak", hinge="right")
    S.set(x, f + 7, 0, "chiseled_stone_bricks")
    # rose window
    cols = ("blue_stained_glass_pane", "red_stained_glass_pane", "yellow_stained_glass_pane", "light_blue_stained_glass_pane")
    for z in range(-5, 6):
        for y in range(f + 12, f + 23):
            d = math.hypot(z, y - (f + 17))
            if d <= 4.2:
                S.air(x, y, z)
                S.set(x + 1, y, z, cols[int(d * 1.2) % 4] if d < 3.6 else "stone_bricks")
            elif d <= 5.0:
                S.set(x, y, z, "polished_andesite")
    # twin turrets on the corners
    for sz in (-1, 1):
        for xx in range(x - 1, x + 2):
            for zz in (sz * 6, sz * 7, sz * 8):
                for y in range(f - 1, NAVE_TOP + 8):
                    S.set(xx, y, zz, "stone_bricks" if (xx + zz) % 2 else ABBEY.pick(xx, y, zz))
        S.bp.pyramid_roof(x - 1, sz * 6 if sz < 0 else 6, x + 1, sz * 8 if sz < 0 else 8, NAVE_TOP + 8, SLATE_ST,
                          overhang=0, cap=SLATE_SL + "[type=bottom,waterlogged=false]")
        S.set(x, NAVE_TOP + 10, sz * 7, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def church_interior(S):
    f = CH_F
    bp = S.bp
    # pews facing the altar, an aisle down the middle
    for x in range(-14, 2, 2):
        for z in list(range(-5, -1)) + list(range(2, 6)):
            S.set(x, f, z, stair("spruce_stairs", "west"))
    # transverse ribs of the vault
    for x in (-15, -10, -5, 0, 20, 24):
        for z in range(-5, 6):
            ry = NAVE_TOP - int((abs(z) / 5.5) ** 2 * 5)
            for y in range(ry, NAVE_TOP + 1):
                S.set(x, y, z, "stone_bricks")
            if ry > NAVE_TOP - 5:
                S.set(x, ry - 1, z, stair("stone_brick_stairs", "north" if z < 0 else "south", "top"))
    # chandeliers
    for x in (-12, -7, -2, 22):
        for y in range(NAVE_TOP - 7, NAVE_TOP + 1):
            S.set(x, y, 0, "iron_chain[axis=y]")
        S.set(x, NAVE_TOP - 8, 0, HLANTERN)
    for y in range(f + 18, TOWER_TOP - 3):
        S.set(11, y, 0, "iron_chain[axis=y]")
    S.set(11, f + 17, 0, HLANTERN)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        S.set(11 + dx, f + 18, dz, "iron_chain[axis=y]")
        S.set(11 + dx, f + 17, dz, HLANTERN)
    # the choir: altar in the apse, candles, the treasury chest
    for z in (-1, 0, 1):
        S.set(CHOIR[1] + 1, f, z, "chiseled_stone_bricks")
        S.set(CHOIR[1] + 1, f + 1, z, "white_candle[candles=3,lit=true,waterlogged=false]" if z else "gold_block")
    for x in range(CHOIR[0], CHOIR[1] + 1):
        S.set(x, f, 0, "red_carpet")
    S.set(CHOIR[1] + 3, f, 0, "air")
    bp.chest(CHOIR[1] + 3, f, 0, "west", loot=LOOT + "abbey_treasury")
    for z in (-4, 4):
        S.set(CHOIR[0] + 1, f, z, "spruce_fence")
        S.set(CHOIR[0] + 1, f + 1, z, LANTERN)
        S.set(-15, f, z, "lantern[hanging=false,waterlogged=false]")
    # a lectern and statues in the transepts
    S.set(11, f, -9, "lectern[facing=south,has_book=false,powered=false]")
    S.set(11, f, 9, "lectern[facing=north,has_book=false,powered=false]")
    for z in (-11, 11):
        for x in (8, 14):
            S.set(x, f, z, "polished_andesite")
            S.set(x, f + 1, z, "stone_brick_wall")
            S.set(x, f + 2, z, "lantern[hanging=false,waterlogged=false]")
    # the transepts open east onto the choir terrace
    for z in (-9, 9):
        for y in (f, f + 1):
            S.air(16, y, z)
            S.air(17, y, z)
        S.set(16, f - 1, z, "polished_andesite")
        bp.door(16, f, z, "east", wood="spruce")


# ------------------------------------------------------------------ La Merveille: almonry, knights' hall, cloister
def merveille(S):
    bp = S.bp
    x0, z0, x1, z1 = MV
    ix0, iz0, ix1, iz1 = MV_IN
    top = CH_F + 5
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = not (ix0 <= x <= ix1 and iz0 <= z <= iz1)
            for y in range(-1, top + 1):
                if wall:
                    S.set(x, y, z, SUPPORT.pick(x, y, z) if y < 6 else ABBEY.pick(x, y, z))
                elif y < ALMONRY_F or ALMONRY_F + 8 <= y < HALL_F or HALL_F + 14 <= y < CH_F:
                    S.set(x, y, z, SUPPORT.pick(x, y, z) if y < ALMONRY_F - 1 else "stone_bricks")
                else:
                    S.air(x, y, z)
        # batter at the foot of the walls
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x0 <= x <= x1 and z0 <= z <= z1:
                continue
            if (x, z) in S.cols or (x, z) in S.house_cols or x > x1:
                continue
            for y in range(-1, 3):
                S.set(x, y, z, "mossy_stone_bricks" if hash3(x, y, z) < 0.4 else "stone_bricks")
            S.set(x, 3, z, stair("stone_brick_stairs", facing_to(x - (x0 + x1) / 2, z - (z0 + z1) / 2)))
    # buttresses: west face (sea), north and south faces, stepping back as they rise
    for zb in (-14, -8, -2, 4, 10):
        for dep in (1, 2, 3):
            for z in (zb, zb + 1):
                ytop = top - 4 - (dep - 1) * 14
                for y in range(-1, ytop + 1):
                    S.set(x0 - dep, y, z, "stone_bricks" if y > 3 else "mossy_stone_bricks")
                S.set(x0 - dep, ytop + 1, z, stair("stone_brick_stairs", "east"))
    for (xb, zf, d) in ((-50, z0, -1), (-35, z0, -1), (-49, z1, 1), (-43, z1, 1), (-37, z1, 1)):
        for dep in (1, 2):
            for x in (xb, xb + 1):
                z = zf + d * dep
                if (x, z) in S.cols:
                    continue
                ytop = top - 6 - (dep - 1) * 16
                for y in range(-1, ytop + 1):
                    S.set(x, y, z, "stone_bricks")
                S.set(x, ytop + 1, z, stair("stone_brick_stairs", "south" if d < 0 else "north"))
    # windows: almonry slits, tall hall lancets, cloister lights (glazed: the drop is 45 blocks)
    for zc in (-11, -5, 1, 7):
        for y in range(ALMONRY_F + 2, ALMONRY_F + 5):
            S.set(x0, y, zc, "air")
            S.set(x0 + 1, y, zc, "glass_pane")
        for z in (zc, zc + 1):
            for y in range(HALL_F + 3, HALL_F + 11):
                S.set(x0, y, z, "air")
                S.set(x0 + 1, y, z, "white_stained_glass_pane" if y < HALL_F + 10 else "stone_bricks")
            for y in (CH_F + 1, CH_F + 2):
                S.set(x0, y, z, "air")
                S.set(x0 + 1, y, z, "glass_pane")
    for xc in (-46, -40):
        for x in (xc, xc + 1):
            for y in range(HALL_F + 3, HALL_F + 11):
                S.set(x, y, z1, "air")
                S.set(x, y, z1 - 1, "white_stained_glass_pane")
    almonry(S)
    knights_hall(S)
    cloister(S)
    stair_tower(S)


def almonry(S):
    f = ALMONRY_F
    ix0, iz0, ix1, iz1 = MV_IN
    for x in range(ix0, ix1 + 1):
        for z in range(iz0, iz1 + 1):
            S.set(x, f - 1, z, "stone_bricks" if (x + z) % 3 else "cobblestone")
    for x in (-46, -40):
        for z in (-6, 2):
            for y in range(f, f + 8):
                S.set(x, y, z, "stone_bricks" if y < f + 6 else "polished_andesite")
                S.set(x + 1, y, z, "stone_bricks" if y < f + 6 else "polished_andesite")
    for x in range(ix0, ix1 + 1, 3):
        for z in (iz0, iz1):
            S.bp.barrel(x, f, z, "up")
    for x in (-43, -37):
        S.set(x, f + 7, -2, "iron_chain[axis=y]")
        S.set(x, f + 6, -2, HLANTERN)
    S.set(-49, f, -2, "crafting_table")
    S.set(-49, f, 0, "smoker[facing=east,lit=false]")
    # the doorway east into the rock: the way to the crypt
    for x in (-33, -32, -31, -30):
        for z in (-1, 0, 1):
            walk_cell(S, x, z, f, "crypt", 4)


def knights_hall(S):
    f = HALL_F
    bp = S.bp
    ix0, iz0, ix1, iz1 = MV_IN
    for x in range(ix0, ix1 + 1):
        for z in range(iz0, iz1 + 1):
            S.set(x, f - 1, z, "spruce_planks" if 2 < x - ix0 < ix1 - ix0 - 2 and 2 < z - iz0 < iz1 - iz0 - 2
                  else "stone_bricks")
    # two rows of columns with capitals; ribs across the vault
    for x in (-46, -42, -38):
        for z in (-6, 2):
            for dx in (0, 1):
                for dz in (0, 1):
                    for y in range(f, f + 14):
                        S.set(x + dx, y, z + dz, "polished_andesite" if y in (f, f + 10) else "stone_bricks")
            for (ox, oz, fc) in ((-1, 0, "east"), (2, 0, "west"), (0, -1, "south"), (0, 2, "north")):
                for k in (0, 1):
                    xx = x + ox + (k if oz else 0)
                    zz = z + oz + (k if ox else 0)
                    S.set(xx, f + 10, zz, stair("stone_brick_stairs", fc, "top"))
    for z in range(iz0, iz1 + 1):
        for x in (-46, -42, -38):
            S.set(x, f + 13, z, "stone_bricks")
    # two great fireplaces on the west wall
    for zc in (-9, 5):
        for z in range(zc - 2, zc + 3):
            for y in range(f, f + 8):
                if abs(z - zc) == 2 or y >= f + 3:
                    S.set(ix0 + 1, y, z, "stone_bricks")
        for z in range(zc - 1, zc + 2):
            S.set(ix0, f, z, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
            S.set(ix0 + 1, f + 3, z, stair("stone_brick_stairs", "west", "top"))
    # long tables with benches
    for z in (-11, -2, 7):
        for x in range(-48, -35):
            if x in (-46, -45, -42, -41, -38, -37) and z == -2:
                continue
            S.set(x, f, z, "spruce_slab[type=top,waterlogged=false]")
            if x % 2 == 0:
                S.set(x, f, z - 1, stair("spruce_stairs", "north"))
                S.set(x, f + 1, z, LANTERN if x % 6 == 0 else "air")
    for x in (-44, -40, -36):
        for y in range(f + 9, f + 13):
            S.set(x, y, -2, "iron_chain[axis=y]")
        S.set(x, f + 8, -2, HLANTERN)
    for (x, z) in ((-49, -13), (-35, -13), (-49, 9), (-35, 9)):
        S.set(x, f + 4, z, with_props("red_wall_banner", facing="east" if x < -40 else "west"))
    bp.chest(-35, f, -6, "west", loot=LOOT + "abbey_knights")
    bp.spawner(-44, f, -2, "brasshaven:tide_wraith")


def cloister(S):
    f = CH_F
    bp = S.bp
    ix0, iz0, ix1, iz1 = MV_IN
    gx0, gz0, gx1, gz1 = ix0 + 4, iz0 + 4, ix1 - 4, iz1 - 4        # garden
    for x in range(ix0, ix1 + 1):
        for z in range(iz0, iz1 + 1):
            garden = gx0 <= x <= gx1 and gz0 <= z <= gz1
            colline = (x in (gx0 - 1, gx1 + 1) and gz0 - 1 <= z <= gz1 + 1) or \
                      (z in (gz0 - 1, gz1 + 1) and gx0 - 1 <= x <= gx1 + 1)
            S.set(x, f - 1, z, "grass_block[snowy=false]" if garden else "polished_andesite" if (x + z) % 2
                  else "stone_bricks")
            if garden:
                for y in range(f, f + 8):
                    S.air(x, y, z)
                continue
            if colline and (x + z) % 2 == 0:
                S.set(x, f, z, "polished_andesite")
                S.set(x, f + 1, z, "calcite")
                S.set(x, f + 2, z, "calcite")
            elif colline:
                S.air(x, f, z)
                S.air(x, f + 1, z)
                S.air(x, f + 2, z)
            if colline:
                S.set(x, f + 3, z, "stone_bricks")
                inner_face = "south" if z == gz0 - 1 else "north" if z == gz1 + 1 else "east" if x == gx0 - 1 else "west"
                S.set(x, f + 4, z, stair(SLATE_ST, {"south": "north", "north": "south", "east": "west",
                                                     "west": "east"}[inner_face]))
            else:
                # gallery roof: slate rising to the outer wall
                d = min(x - ix0, ix1 - x, z - iz0, iz1 - z)
                y = f + 6 - d // 2 if d < 3 else f + 4
                for yy in range(f, y):
                    S.air(x, yy, z)
                S.set(x, y, z, SLATE)
    # garden: paths, beds, a well hiding the way to the reliquary, a little tree
    cx, cz = (gx0 + gx1) // 2, (gz0 + gz1) // 2
    for x in range(gx0, gx1 + 1):
        S.set(x, f - 1, cz, "dirt_path")
    for z in range(gz0, gz1 + 1):
        S.set(cx, f - 1, z, "dirt_path")
    flowers = ("lily_of_the_valley", "cornflower", "allium", "oxeye_daisy", "azure_bluet")
    for x in range(gx0, gx1 + 1):
        for z in range(gz0, gz1 + 1):
            if x in (cx,) or z in (cz,):
                continue
            edge = x in (gx0, gx1) or z in (gz0, gz1)
            if edge and (x + z) % 2 == 0:
                S.set(x, f, z, "oak_leaves[distance=7,persistent=true,waterlogged=false]")
            elif not edge and hash01(x, z, 71) < 0.4:
                S.set(x, f, z, flowers[int(hash01(z, x, 72) * len(flowers))])
    oak(bp, gx0 + 1, f, gz1 - 1, h=4, seed=5)
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            S.set(x, f - 1, z, "stone_bricks")
            if (x, z) != (cx, cz):
                S.set(x, f, z, "stone_brick_wall" if abs(x - cx) + abs(z - cz) == 1 else "stone_bricks")
    for x, z in ((cx - 1, cz - 1), (cx + 1, cz + 1)):
        S.set(x, f + 1, z, "spruce_fence")
        S.set(x, f + 2, z, "spruce_fence")
    for x in range(cx - 1, cx + 2):
        for z in range(cz - 1, cz + 2):
            S.set(x, f + 3, z, "spruce_slab[type=bottom,waterlogged=false]")
    S.set(cx, f + 2, cz, HLANTERN)
    S.air(cx - 1, f, cz)   # the well's mouth
    S.air(cx, f, cz)
    S.air(cx, f + 1, cz)
    S.set(cx, f - 1, cz, "spruce_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    # the reliquary under the garden (between the cloister and the hall vault)
    bp.ladder(cx, HALL_F + 15, cz, f - 2, "south")
    S.set(cx, HALL_F + 15, cz - 1, "stone_bricks")
    for x in range(cx - 2, cx + 3):
        for z in range(cz + 1, cz + 5):
            S.set(x, HALL_F + 14, z, "stone_bricks")
            for y in range(HALL_F + 15, HALL_F + 18):
                S.air(x, y, z)
    S.set(cx, HALL_F + 15, cz, with_props("ladder", facing="south", waterlogged=False))
    bp.chest(cx, HALL_F + 15, cz + 4, "north", loot=LOOT + "abbey_reliquary")
    for x in (cx - 2, cx + 2):
        S.set(x, HALL_F + 15, cz + 4, "white_candle[candles=4,lit=true,waterlogged=false]")
        S.set(x, HALL_F + 15, cz + 1, "skeleton_skull[rotation=0]")
    # a scriptorium corner with the cloister chest; lanterns in the galleries
    S.set(ix0 + 1, f, iz1 - 1, "lectern[facing=north,has_book=false,powered=false]")
    S.set(ix0, f, iz1, "bookshelf")
    S.set(ix0, f + 1, iz1, "bookshelf")
    bp.chest(ix0 + 2, f, iz1, "north", loot=LOOT + "abbey_cloister")
    for (x, z) in ((ix0 + 1, iz0 + 1), (ix1 - 1, iz0 + 1), (ix0 + 1, iz1 - 3), (ix1 - 1, iz1 - 1), (ix1 - 1, cz),
                   (ix0 + 1, cz)):
        S.set(x, f, z, LANTERN)
    bp.spawner(gx1 - 1, f, gz0 + 1, "brasshaven:gargoyle")
    # doors: the terrace (east) and the stair tower (north)
    for z in (-3, -2, -1):
        for x in (MV[2] - 1, MV[2]):
            S.set(x, f - 1, z, "polished_andesite")
            for y in range(f, f + 3):
                S.air(x, y, z)
    S.set(MV[2], f + 3, -2, "chiseled_stone_bricks")


def stair_tower(S):
    """Switchback stair in a square tower on the Merveille's north side: cloister 42, hall 22, almonry 12."""
    x0, z0, x1, z1 = STAIR_T
    ix0, iz0, ix1, iz1 = x0 + 1, z0 + 1, x1 - 1, z1 - 1   # -45..-39, -23..-18
    top = CH_F + 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(-1, top + 1):
                S.set(x, y, z, SUPPORT.pick(x, y, z) if y < 4 else ABBEY.pick(x, y, z))
    S.bp.pyramid_roof(x0, z0, x1, z1, top + 1, SLATE_ST, overhang=1, cap="stone_bricks")
    walk = {}
    E, Wx = ix1, ix0
    south = range(iz1 - 2, iz1 + 1)
    north = range(iz0, iz0 + 3)
    landing_e = (42, 32, 22, 12)
    landing_w = (37, 27, 17)
    for h in landing_e:
        for z in range(iz0, iz1 + 1):
            walk.setdefault((E, z), []).append((h, "full", None))
    for h in landing_w:
        for z in range(iz0, iz1 + 1):
            walk.setdefault((Wx, z), []).append((h, "full", None))
    for h in (42, 32, 22):              # east landing -> west landing along the south strip, going down westward
        for k in range(1, 6):
            x = E - k
            for z in south:
                walk.setdefault((x, z), []).append((h - k, "stair", "east"))
    for h in (37, 27, 17):              # west -> east along the north strip
        for k in range(1, 6):
            x = Wx + k
            for z in north:
                walk.setdefault((x, z), []).append((h - k, "stair", "west"))
    for x in range(ix0, ix1 + 1):
        for z in range(iz0, iz1 + 1):
            cells = sorted(walk.get((x, z), []))
            for y in range(ALMONRY_F - 1, top):
                spec = SUPPORT.pick(x, y, z)
                for (fe, kind, fc) in cells:
                    if y == fe - 1:
                        spec = "stone_bricks" if kind == "full" else stair("stone_brick_stairs", fc)
                    elif fe <= y <= fe + 3:
                        spec = "air"
                if cells and y >= cells[-1][0]:
                    spec = "air"
                S.set(x, y, z, spec)
    # doorways from the east landing into the three storeys (through the Merveille's north wall)
    for h in (42, 22, 12):
        for x in (E - 1, E):
            for z in range(z1, MV[1] + 2):
                S.set(x, h - 1, z, "stone_bricks")
                for y in range(h, h + 3):
                    S.air(x, y, z)
    for h in (40, 30, 20, 14):
        S.set(ix0, h, iz0, HLANTERN.replace("true", "false"))
    # slit windows
    for y in range(16, top - 2, 5):
        S.set(x0, y, (z0 + z1) // 2, "glass_pane")
        S.set(x0, y + 1, (z0 + z1) // 2, "glass_pane")


# ------------------------------------------------------------------ the Chatelet gate and the Grand Degre
def chatelet(S):
    bp = S.bp
    xw, xe = -18, -14
    t = S.t.get((-16, 16), 34)
    n = math.floor(t)
    for x in range(xw, xe + 1):
        for z in range(13, 19):
            side = z in (13, 18)
            for y in range(n - 1, n + 12):
                if side:
                    if y < n + 11 or (x + z) % 2 == 0:
                        if not (z == 18 and y <= n + 4 and x not in (xw, xe)):
                            S.set(x, y, z, ABBEY.pick(x, y, z))
                elif y >= n + 5:
                    S.set(x, y, z, ABBEY.pick(x, y, z) if y < n + 10 else "stone_bricks" if y == n + 10 else
                          ("stone_brick_slab[type=bottom,waterlogged=false]" if (x + z) % 2 else "air"))
    # arched mouths on both faces, a raised portcullis
    for x in (xw, xe):
        for z in range(14, 18):
            S.set(x, n + 4, z, stair("stone_brick_stairs", "south" if z == 14 else "north", "top")
                  if z in (14, 17) else "iron_bars")
    # machicolations on the east face and two corbelled turrets
    for z in range(13, 19):
        S.set(xe + 1, n + 8, z, stair("stone_brick_stairs", "west", "top"))
        S.set(xe + 1, n + 9, z, "stone_bricks")
        S.set(xe + 1, n + 10, z, "stone_brick_wall" if z % 2 else "stone_bricks")
    for (cx, cz) in ((xw - 1, 12), (xe + 1, 19)):
        for y in range(n + 5, n + 15):
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    if (x, z) in S.cols and y < S.t[(x, z)] + 6:
                        continue
                    S.set(x, y, z, "stone_bricks" if y > n + 5 else stair("stone_brick_stairs", "north", "top"))
        bp.cone_roof(cx, n + 15, cz, 2, SLATE_ST, cap="lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in (14, 17):
        S.set(xe + 1, n + 3, z, "air")
    for x in (xw, xe):
        S.set(x, n + 5, 16, "chiseled_stone_bricks")
    # walls along the Grand Degre where it leaves the street (the platform holds it further up)
    for z in range(13, 16):
        for x in (-24, -20):
            if (x, z) in S.cols:
                continue
            base = S.t.get((-22, z), 36)
            y = math.floor(base) + 3
            while y >= 0 and (empty(bp.get(x, y, z)) or y >= math.floor(base) - 1):
                S.set(x, y, z, ABBEY.pick(x, y, z))
                y -= 1
                if y < math.floor(base) - 1 and not empty(bp.get(x, y, z)):
                    break


# ------------------------------------------------------------------ the crypt in the rock
def carve_box(S, x0, y0, z0, x1, y1, z1, floor_spec=None, lining=CRYPT):
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, y1 + 2):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and y0 <= y <= y1
                if inside:
                    S.air(x, y, z)
                elif y == y0 - 1 and x0 <= x <= x1 and z0 <= z <= z1:
                    S.set(x, y, z, floor_spec or lining.pick(x, y, z))
                elif S.bp.get(x, y, z) is None or (x, y, z) in S.rock:
                    S.set(x, y, z, lining.pick(x, y, z))


def crypt(S):
    bp = S.bp
    f = CRYPT_F
    # Notre-Dame-sous-Terre: twin naves under a barrel vault, the site of grace before the descent
    carve_box(S, -29, f, -8, -20, f + 5, 8)
    for x in range(-29, -19):
        for z in range(-8, 9):
            S.set(x, f - 1, z, "polished_tuff" if (x + z) % 2 else "tuff_bricks")
            if abs(z) <= 4 and not (abs(z) <= 0):
                S.air(x, f + 6, z)
    for x in range(-29, -19):
        for z in range(-3, 4):
            S.air(x, f + 6, z)
    for x in (-27, -24, -21):
        for y in range(f, f + 7):
            S.set(x, y, 0, "polished_tuff" if y < f + 5 else "tuff_bricks")
        S.set(x, f + 4, -1, stair("tuff_brick_stairs", "south", "top"))
        S.set(x, f + 4, 1, stair("tuff_brick_stairs", "north", "top"))
    for z in (-6, 6):
        S.set(-28, f, z, "chiseled_tuff")
        S.set(-28, f + 1, z, "white_candle[candles=3,lit=true,waterlogged=false]")
    for x in (-25, -23):
        S.set(x, f, 8, "chiseled_tuff_bricks")
        S.set(x, f + 1, 8, "white_candle[candles=2,lit=true,waterlogged=false]")
    S.set(-24, f, 8, "chiseled_tuff_bricks")
    S.set(-24, f + 1, 8, "lantern[hanging=false,waterlogged=false]")
    S.set(-21, f, -6, MOD["waystone"])
    S.set(-22, f, -7, stair("spruce_stairs", "east"))
    for (x, z) in ((-26, -4), (-26, 4), (-22, 4)):
        S.set(x, f + 5, z, HLANTERN)
    # the ossuary off the north side: niches of bones and a flooded basin (the crabs' den)
    carve_box(S, -28, f, -17, -21, f + 4, -10)
    for x in (-25, -24):
        S.set(x, f - 1, -9, "tuff_bricks")
        for y in range(f, f + 3):
            S.air(x, y, -9)
    for x in range(-27, -23):
        for z in range(-16, -12):
            S.set(x, f - 2, z, "tuff_bricks")
            S.set(x, f - 1, z, "water")
    for z in range(-17, -9, 2):
        S.set(-28, f + 1, z, "bone_block[axis=y]")
        S.set(-28, f + 2, z, "skeleton_skull[rotation=4]")
    for x in range(-27, -21, 2):
        S.set(x, f + 2, -17, "bone_block[axis=x]")
    S.set(-22, f, -11, LANTERN)
    bp.spawner(-22, f, -16, "brasshaven:barnacle_crab")
    # the narrow stair down to the arena (compression before the release)
    for z in (-1, 0, 1):
        for y in range(f, f + 3):
            S.air(-19, y, z)
        S.set(-19, f - 1, z, "tuff_bricks")
        for k in range(1, 10):
            x = -19 + k
            fe = f - k
            for y in range(fe - 3, fe):
                S.set(x, y, z, "tuff_bricks")
            S.set(x, fe - 1, z, stair("tuff_brick_stairs", "west"))
            for y in range(fe, fe + 4):
                S.air(x, y, z)
            S.set(x, fe + 4, z, "tuff_bricks")
        for x in (-9, -8):
            S.set(x, ARENA_F - 1, z, "polished_deepslate")
            for y in range(ARENA_F, ARENA_F + 4):
                S.air(x, y, z)
    for k in range(0, 11):
        x = -19 + k
        for z in (-2, 2):
            for y in range(f - k - 1, f - k + 5):
                if S.bp.get(x, y, z) is None or (x, y, z) in S.rock:
                    S.set(x, y, z, "tuff_bricks")
    S.set(-14, f - 5 + 3, -1, "air")
    for x in (-16, -12):
        S.set(x, f - (x + 19) + 3, -2 if x == -16 else 2, "soul_lantern[hanging=false,waterlogged=false]")


def arena(S):
    """The boss arena at the heart of the island: a domed rotunda cut in the rock, eight pillars, sea light falling
    through glazed shafts that end in grates on the cliff, a compass of prismarine on the floor."""
    bp = S.bp
    cx, cz = ARENA_C
    R, F = ARENA_R, ARENA_F
    wall_h = F + 11
    dome = 7

    def inside(x, y, z, extra=0.0):
        d = math.hypot(x - cx, z - cz)
        if y < F or d > R + extra:
            return False
        if y <= wall_h:
            return True
        k = (y - wall_h) / (dome + extra)
        return k < 1 and d <= (R + extra) * math.sqrt(1 - k * k)

    for x in range(cx - R - 3, cx + R + 4):
        for z in range(cz - R - 3, cz + R + 4):
            d = math.hypot(x - cx, z - cz)
            if d > R + 2.5:
                continue
            for y in range(F - 2, wall_h + dome + 3):
                if inside(x, y, z):
                    S.air(x, y, z)
                elif inside(x, y, z, 1.6) or (y in (F - 1, F - 2) and d <= R + 1.6):
                    if y == F - 1 and d <= R:
                        if d < 1.5:
                            spec = "chiseled_deepslate"
                        elif 5.5 <= d < 6.5 or 10.5 <= d < 11.4:
                            spec = "dark_prismarine"
                        elif d < 5.5:
                            spec = "prismarine_bricks" if (x + z) % 2 else "dark_prismarine"
                        else:
                            spec = "polished_deepslate" if (x + z) % 2 else "deepslate_tiles"
                    else:
                        band = (y - F) % 6
                        spec = ("dark_prismarine" if band == 0 else "deepslate_bricks" if hash3(x, y, z) < 0.6
                                else "deepslate_tiles")
                    S.set(x, y, z, spec)
    # sea lanterns in the floor ring and on the wall
    for k in range(8):
        a = math.radians(k * 45)
        S.set(round(cx + 8.5 * math.cos(a)), F - 1, round(cz + 8.5 * math.sin(a)), "sea_lantern")
        wx, wz = round(cx + (R + 1) * math.cos(a + 0.39)), round(cz + (R + 1) * math.sin(a + 0.39))
        S.set(wx, F + 6, wz, "sea_lantern")
    # pillars (part of the fight: cover from the boss' charges)
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        px, pz = round(cx + 11.5 * math.cos(a)), round(cz + 11.5 * math.sin(a))
        for x in range(px - 1, px + 2):
            for z in range(pz - 1, pz + 2):
                for y in range(F, wall_h + dome + 1):
                    if not inside(x, y, z):
                        break
                    corner = abs(x - px) == 1 and abs(z - pz) == 1
                    if corner and F + 1 < y < wall_h - 1:
                        continue
                    S.set(x, y, z, "dark_prismarine" if y in (F, wall_h - 1) else "polished_deepslate")
    # glazed shafts to the cliff (south-west, over the harbour): daylight from the sea, grates outside
    for phi in (214, 232, 250):
        a = math.radians(phi)
        dx, dz = math.sin(a), -math.cos(a)
        cells = []
        hit = False
        t = R - 0.5
        while t < 60:
            x, z = round(cx + dx * t), round(cz + dz * t)
            col = [(x, y, z) for y in (wall_h - 3, wall_h - 2)]
            if all(empty(bp.get(*c)) and c not in S.rock for c in col) and t > R + 2:
                hit = True
                break
            if (x, z) in S.house_cols:
                break
            cells.append(col)
            t += 0.5
        if not hit:
            continue
        for i, col in enumerate(cells):
            for c in col:
                if inside(*c):
                    continue
                S.set(*c, "iron_bars" if i >= len(cells) - 2 else "glass")
    # the boss: seal at the centre of the floor, mist across the only way in
    bp.boss_seal(cx, F - 1, cz, BOSS, 14)
    # the reward vault south, behind sealed bars that open when the boss falls
    vx0, vz0, vx1, vz1 = VAULT
    carve_box(S, vx0, F, vz0, vx1, F + 4, vz1, lining=CRYPT)
    for x in range(vx0, vx1 + 1):
        for z in range(vz0, vz1 + 1):
            S.set(x, F - 1, z, "polished_deepslate" if (x + z) % 2 else "deepslate_tiles")
    for x in (cx - 1, cx, cx + 1):
        for z in range(cz + R - 1, vz0):
            S.set(x, F - 1, z, "deepslate_tiles")
            for y in range(F, F + 3):
                S.air(x, y, z)
            S.set(x, F + 3, z, "deepslate_bricks")
        for y in range(F, F + 3):
            S.set(x, y, cz + R + 2, MOD["vault_bars"])
    for x in (cx - 2, cx + 2):
        for z in range(cz + R - 1, vz0):
            for y in range(F, F + 4):
                if not inside(x, y, z):
                    S.set(x, y, z, "deepslate_bricks")
    bp.chest(vx1 - 1, F, vz1, "north", loot=LOOT + "abbey_vault")
    bp.chest(vx0 + 3, F, vz1, "north", loot=LOOT + "abbey_vault")
    for x in (vx0 + 5, vx0 + 7):
        S.set(x, F, vz1, "gold_block")
        S.set(x, F + 1, vz1, "white_candle[candles=4,lit=true,waterlogged=false]")
    for x in (vx0 + 1, vx1 - 1):
        S.set(x, F + 4, vz0 + 3, HLANTERN)
    # the way out: a tunnel west to the harbour, an iron door opened from inside only (a shortcut to the start)
    for x in range(-34, vx0):
        for z in (24, 25, 26):
            fe = 3 if x > -27 else 2.5 if x > -29 else 2 if x > -31 else 1.5 if x > -33 else 1
            walk_cell(S, x, z, fe, "crypt", 4)
            for y in range(math.floor(fe) - 2, math.floor(fe) + 6):
                for zz in (23, 27):
                    if bp.get(x, y, zz) is None or (x, y, zz) in S.rock:
                        S.set(x, y, zz, "tuff_bricks")
    for z in (24, 26):
        for y in range(1, 4):
            S.set(-35, y, z, "stone_bricks")
    for y in (3, 4):
        S.set(-35, y, 25, "stone_bricks")
    S.air(-35, 1, 25)
    S.air(-35, 2, 25)
    S.set(-35, 0, 25, "stone_bricks")
    bp.door(-35, 1, 25, "west", wood="iron")
    S.set(-34, 2, 24, "lever[face=wall,facing=south,powered=false]")
    for x in (-10, -20, -30):
        S.set(x, 5 if x > -27 else 4, 25, HLANTERN)


def arena_mist(S):
    S.bp.mist(-9, ARENA_F, -1, -9, ARENA_F + 3, 1)


# ------------------------------------------------------------------ the rock-cut parish church on the parvis
def parish_church(S):
    bp = S.bp
    f = 13
    carve_box(S, 6, f, 21, 13, f + 6, 29, lining=WALL)
    for x in range(6, 14):
        for z in range(21, 30):
            S.set(x, f - 1, z, "stone_bricks" if (x + z) % 2 else "polished_andesite")
    # the facade on the square
    for x in range(4, 16):
        for y in range(f - 1, f + 14):
            gable = y - (f + 8) <= 5 - abs(x - 9.5)
            if y <= f + 8 or gable:
                S.set(x, y, 30, ABBEY.pick(x, y, 30))
    for x in (9, 10):
        S.air(x, f, 30)
        S.air(x, f + 1, 30)
        S.air(x, f + 2, 30)
    bp.door(9, f, 30, "south", wood="spruce", hinge="left")
    bp.door(10, f, 30, "south", wood="spruce", hinge="right")
    S.set(9, f + 3, 30, stair("stone_brick_stairs", "east", "top"))
    S.set(10, f + 3, 30, stair("stone_brick_stairs", "west", "top"))
    for y in range(f + 5, f + 8):
        S.set(9, y, 30, "yellow_stained_glass_pane" if y < f + 7 else "stone_bricks")
        S.set(10, y, 30, "yellow_stained_glass_pane" if y < f + 7 else "stone_bricks")
    # bell-cote on the gable
    for x in (8, 11):
        for y in range(f + 14, f + 17):
            S.set(x, y, 30, "stone_bricks")
    for x in range(8, 12):
        S.set(x, f + 17, 30, "stone_brick_slab[type=bottom,waterlogged=false]")
    S.set(9, f + 16, 30, "bell[attachment=ceiling,facing=south,powered=false]")
    S.set(10, f + 16, 30, "stone_bricks")
    # inside: pews, altar, candles
    for z in range(25, 29):
        for x in (7, 8, 11, 12):
            if z % 2 == 0:
                S.set(x, f, z, stair("spruce_stairs", "south"))
    for x in (9, 10):
        S.set(x, f, 21, "chiseled_stone_bricks")
        S.set(x, f + 1, 21, "white_candle[candles=3,lit=true,waterlogged=false]")
    S.set(7, f + 5, 25, HLANTERN)
    S.set(12, f + 5, 25, HLANTERN)


# ------------------------------------------------------------------ the harbour, the causeway
def harbour(S):
    bp = S.bp
    # a basin closed by a breakwater, south of the quay
    for x in range(-54, -39):
        for z in range(34, 45):
            edge = x == -54 or z == 44
            if edge and not (z == 44 and -49 <= x <= -47):
                for y in range(-4, 2):
                    S.set(x, y, z, "cobblestone" if y < 1 else "mossy_cobblestone" if y == 1 and x % 3 else
                          "cobblestone_wall")
            else:
                for y in range(-4, 1):
                    S.set(x, y, z, "water")
                S.set(x, -5, z, "sand" if hash01(x, z, 81) < 0.7 else "gravel")
                S.set(x, -6, z, "stone")
    bp.spawner(-46, -4, 39, "minecraft:drowned")
    S.set(-46, -5, 39, "stone")
    # quay furniture: bollards, barrels, a crane, lamps
    for x in (-46, -41, -37):
        S.set(x, 1, 32, "spruce_fence")
        S.set(x, 2, 32, LANTERN if x == -41 else "air")
    for (x, z) in ((-46, 22), (-45, 22), (-46, 23)):
        bp.barrel(x, 1, z, "up")
    for y in range(1, 6):
        S.set(-38, y, 29, "spruce_fence" if y < 5 else "spruce_planks")
    for x in (-39, -40):
        S.set(x, 5, 29, "spruce_slab[type=top,waterlogged=false]")
    S.set(-40, 4, 29, "iron_chain[axis=y]")
    S.set(-40, 3, 29, "barrel[facing=up,open=false]")
    bp.chest(-47, 1, 30, "east", loot=LOOT + "abbey_ramparts")


def causeway(S):
    bp = S.bp

    def xc(z):
        return round(4 * math.sin(math.pi * (-69 - z) / 58.0))

    for z in range(-127, -68):
        c = xc(z)
        if -82 <= z <= -81 or -116 <= z <= -113:
            deck = -1
        elif -97 <= z <= -83 or -112 <= z <= -105:
            deck = -2
        elif -104 <= z <= -98:
            deck = None
        else:
            deck = 0
        for x in range(c - 6, c + 7):
            dx = abs(x - c)
            if dx <= 3:
                if deck is None:
                    stub = dx >= 2 and (z in (-98, -104) or hash01(x, z, 91) < 0.15)
                    for y in range(-9, 0):
                        S.set(x, y, z, "water")
                    if stub:
                        for y in range(-9, -3 + int(hash01(z, x, 9) * 2)):
                            S.set(x, y, z, "mossy_stone_bricks")
                    S.set(x, -10, z, "gravel" if hash01(x, z, 92) < 0.5 else "cobblestone")
                    S.set(x, -11, z, "stone")
                    continue
                for y in range(-9, deck):
                    S.set(x, y, z, "cobblestone" if y < -4 else "stone_bricks" if hash3(x, y, z) < 0.6
                          else "mossy_stone_bricks")
                if dx == 3:
                    S.set(x, deck, z, "stone_bricks")
                    if z % 7 != 0:
                        S.set(x, deck + 1, z, "stone_brick_wall" if deck >= 0 else "mossy_stone_bricks")
                else:
                    wet = deck < 0
                    h = hash01(x, z, 93)
                    S.set(x, deck, z, ("mossy_stone_bricks" if h < 0.6 else "mossy_cobblestone") if wet else
                          ("stone_bricks" if h < 0.5 else "polished_andesite" if h < 0.7 else "cobblestone"))
                    for y in range(deck + 1, 0):
                        S.set(x, y, z, "seagrass" if y == deck + 1 and h > 0.75 else "water")
                    if deck == 0:
                        for y in range(1, 4 if z < -112 else 2):
                            S.air(x, y, z)
            elif dx <= 5 and deck is not None:
                top = -2 - (dx - 4) * 2 - int(hash01(x, z, 94) * 2)
                for y in range(-9, top + 1):
                    S.set(x, y, z, "cobblestone" if hash3(x, y, z) < 0.5 else "mossy_cobblestone")
    # the shore end: a landing, a wayside cross and the first waystone
    for x in range(-5, 6):
        for z in range(-127, -122):
            S.set(x, 0, z, "stone_bricks" if (x + z) % 3 else "cobblestone")
            for y in range(-6, 0):
                S.set(x, y, z, "cobblestone")
            for y in range(1, 4):
                S.air(x, y, z)
    for y in range(1, 5):
        S.set(4, y, -125, "stone_brick_wall" if y < 4 else "stone_bricks")
    S.set(3, 4, -125, "stone_brick_wall")
    S.set(5, 4, -125, "stone_brick_wall")
    S.set(4, 5, -125, "stone_brick_wall")
    S.set(-4, 1, -125, MOD["waystone"])
    S.set(-4, 1, -123, LANTERN)


# ------------------------------------------------------------------ squares, arches, parapets, lamps
def squares(S):
    bp = S.bp
    # gate court: waystone, a trough, lamps
    S.set(-6, 1, -44, MOD["waystone"])
    for x in range(4, 8):
        S.set(x, 1, -50, "cauldron")
    for (x, z) in ((-9, -51), (9, -51), (-9, -42), (9, -42)):
        S.set(x, 1, z, "stone_brick_wall")
        S.set(x, 2, z, LANTERN)
    # the well square
    wx, wz = round(WELL_SQ[0] + 2), round(WELL_SQ[1] - 1)
    t = S.t.get((wx, wz), 3.5)
    n = math.floor(t)
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            S.set(x, n - 1, z, "stone_bricks")
            S.set(x, n, z, "stone_bricks" if (x, z) != (wx, wz) else "water")
            S.set(x, n - 2, z, "stone_bricks")
            if (x, z) != (wx, wz):
                S.set(x, n + 1, z, "air")
    S.set(wx, n - 1, wz, "water")
    for (x, z) in ((wx - 1, wz - 1), (wx + 1, wz + 1)):
        S.set(x, n + 1, z, "spruce_fence")
        S.set(x, n + 2, z, "spruce_fence")
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            S.set(x, n + 3, z, stair(SLATE_ST, "south" if z == wz - 1 else "north") if z != wz else
                  SLATE_SL + "[type=bottom,waterlogged=false]")
    S.set(wx, n + 2, wz, HLANTERN)
    # the parvis: hub waystone, a stone cross, lamps
    px, pz = round(PARVIS[0]), round(PARVIS[1])
    t = S.t.get((px, pz), 12.5)
    n = math.ceil(t)
    S.set(px - 4, n, pz + 1, MOD["waystone"])
    for y in range(n, n + 3):
        S.set(px + 3, y, pz + 2, "stone_brick_wall")
    S.set(px + 2, n + 2, pz + 2, "stone_brick_wall")
    S.set(px + 4, n + 2, pz + 2, "stone_brick_wall")
    S.set(px + 3, n + 3, pz + 2, "stone_brick_wall")
    for (dx, dz) in ((-5, -3), (5, -3)):
        S.set(px + dx, n, pz + dz, "stone_brick_wall")
        S.set(px + dx, n + 1, pz + dz, LANTERN)
    # the abbey terrace: lamps at the church door
    for z in (-4, 4):
        S.set(-21, CH_F, z, "stone_brick_wall")
        S.set(-21, CH_F + 1, z, LANTERN)


def arch_over(S, phi, r, house=True):
    """A stone arch over the street (a house bridging it on top): the piers take the edge cells."""
    bp = S.bp
    px, pz = P(r, phi)
    a, b = P(r, phi + 1.5), P(r, phi - 1.5)
    tx, tz = a[0] - b[0], a[1] - b[1]
    L = math.hypot(tx, tz)
    nx, nz = -tz / L, tx / L
    cells = []
    for k in range(-3, 4):
        c = (round(px + nx * k), round(pz + nz * k))
        if c not in cells:
            cells.append(c)
    ts = [S.t[c] for c in cells if c in S.t]
    if not ts:
        return
    lintel = math.floor(max(ts)) + 5
    for i, c in enumerate(cells):
        edge = i in (1, len(cells) - 2)
        if c in S.t and edge:
            for y in range(math.ceil(S.t[c]), lintel):
                S.set(c[0], y, c[1], "stone_bricks")
        S.set(c[0], lintel, c[1], "stone_bricks")
        if c in S.t and not edge and i not in (0, len(cells) - 1):
            S.set(c[0], lintel - 1, c[1], "stone_brick_slab[type=top,waterlogged=false]")
        if house:
            for y in range(lintel + 1, lintel + 5):
                S.set(c[0], y, c[1], "calcite" if 0 < i < len(cells) - 1 and y < lintel + 4 else
                      "stripped_dark_oak_log[axis=y]")
            S.set(c[0], lintel + 5, c[1], SLATE)
            S.set(c[0], lintel + 6, c[1], SLATE_SL + "[type=bottom,waterlogged=false]")
    mid = cells[len(cells) // 2]
    S.set(mid[0], lintel - 1, mid[1], HLANTERN)


def parapets(S):
    """Low walls where a walkway's edge drops away, a lantern on every few."""
    bp = S.bp
    n = 0
    for (x, z), t in sorted(S.t.items()):
        pid = S.claims[(x, z)][2]
        if pid in ("gate", "outer_gate", "quay", "barbican"):
            continue
        drop = False
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, z + dz)
            if q in S.t:
                if S.t[q] <= t - 1.5:
                    drop = True
                continue
            y = math.ceil(t) + 1
            while y > -8 and empty(bp.get(q[0], y, q[1])):
                y -= 1
            if y + 1 <= t - 1.5 and not (y <= 0 and t <= 1.5):
                drop = True
        if drop:
            y = math.ceil(t)
            if not empty(bp.get(x, y, z)):
                continue
            S.set(x, y, z, "stone_brick_wall")
            n += 1
            if n % 6 == 0:
                S.set(x, y + 1, z, LANTERN)


# ------------------------------------------------------------------ life: grass on the ledges, the wood, the sea
def greenery(S):
    bp = S.bp
    flowers = ("short_grass", "short_grass", "fern", "poppy", "oxeye_daisy", "short_grass")
    tops = {}
    for (x, y, z) in S.rock:
        if y > tops.get((x, z), -1):
            tops[(x, z)] = y
    for (x, z), y in tops.items():
        if (x, y, z) not in S.rock or not empty(bp.get(x, y + 1, z)):
            continue
        flat = sum(1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if tops.get((x + dx, z + dz), -9) >= y)
        if flat < 3 or y < 2:
            continue
        S.set(x, y, z, "grass_block[snowy=false]" if hash01(x, z, 61) < 0.8 else "moss_block")
        h = hash01(z, x, 62)
        if h < 0.35:
            S.set(x, y + 1, z, flowers[int(h * 100) % len(flowers)])
    # a little wood on the north-west slope
    k = 0
    for (x, z), y in sorted(tops.items()):
        phi = phi_of(x, z)
        if not (285 <= phi <= 350) or not 4 <= y <= 30 or hash01(x, z, 63) > 0.035:
            continue
        if any((x + dx, z + dz) in S.cols or (x + dx, z + dz) in S.house_cols for dx in range(-4, 5)
               for dz in range(-4, 5)):
            continue
        if S.blocked_box(x - 3, y, z - 3, x + 3, y + 12, z + 3):
            continue
        if bp.get(x, y, z) not in ("minecraft:grass_block", "minecraft:moss_block"):
            continue
        if k % 3 == 2:
            spruce(bp, x, y + 1, z, h=8, seed=x * 7 + z)
        else:
            oak(bp, x, y + 1, z, h=5 + k % 2, seed=x * 3 + z)
        k += 1
    # sea grass and kelp on the talus
    for x in range(-70, 71):
        for z in range(-70, 71):
            for y in range(-1, -16, -1):
                b = bp.get(x, y, z)
                if b is None:
                    continue
                if y < -3 and empty(bp.get(x, y + 1, z)) and b in ("minecraft:stone", "minecraft:mossy_cobblestone",
                                                                    "minecraft:andesite", "minecraft:gravel"):
                    h = hash01(x, z, 65)
                    if h < 0.12:
                        n = 2 + int(hash01(z, x, 66) * 6)
                        top = min(y + n, -2)
                        for yy in range(y + 1, top + 1):
                            bp.set(x, yy, z, "kelp_plant" if yy < top else "kelp[age=20]")
                    elif h < 0.4:
                        bp.set(x, y + 1, z, "seagrass")
                break


# ------------------------------------------------------------------ builder
def bailey_ladders(S, phis):
    """Ladders up the inner face of the ring wall out of the little baileys between the rock and the ramparts."""
    bp = S.bp
    for phi0 in phis:
        for dphi in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6):
            phi = phi0 + dphi
            if not in_ramparts(phi):
                continue
            done = False
            for r in (RING0 - 0.6, RING0 - 1.1, RING0 - 1.6):
                x, z = (round(v) for v in P(r, phi))
                ux, uz = (1, 0) if abs(x) >= abs(z) else (0, 1)
                ux, uz = (ux * (1 if x > 0 else -1), 0) if ux else (0, uz * (1 if z > 0 else -1))
                wx, wz = x + ux, z + uz
                if not all(empty(bp.get(x, y, z)) for y in range(1, WALK + 3)):
                    continue
                if empty(bp.get(x, 0, z)) or not all(not empty(bp.get(wx, y, wz)) for y in range(1, WALK + 1)):
                    continue
                if not empty(bp.get(wx, WALK + 1, wz)) or not empty(bp.get(wx, WALK + 2, wz)):
                    continue
                face = facing_to(-ux, -uz)
                bp.ladder(x, 1, z, WALK, face)
                done = True
                break
            if done:
                break


def tidal_abbey(bp):
    S = Site(bp)
    reserve(S)
    terrain(S)
    ramparts(S)
    route(S)
    platform(S)
    church(S)
    merveille(S)
    chatelet(S)
    crypt(S)
    arena(S)
    parish_church(S)
    harbour(S)
    causeway(S)
    town(S)
    for phi, r in ((32, 42.5), (132, 39.6), (190, 26)):
        arch_over(S, phi, r)
    squares(S)
    parapets(S)
    greenery(S)
    bailey_ladders(S, (54, 74, 92, 118, 165))
    arena_mist(S)


# camera spots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("causeway", (0, 1, -78), (0, 45, 0)),
    ("grande_rue", (41, 6, 4), (34, 10, 21)),
    ("parvis", (10, 13, 40), (10, 18, 28)),
    ("nave", (-14, CH_F, 0), (26, CH_F + 12, 0)),
    ("cloister", (-49, CH_F, -13), (-40, CH_F + 2, 2)),
    ("knights_hall", (-48, HALL_F, -12), (-36, HALL_F + 6, 8)),
    ("arena", (-7, ARENA_F, 0), (22, ARENA_F + 8, 0)),
]


register(StructureDef(
    "tidal_abbey", "overworld", ["beach", "stony_shore"],
    [Piece("abbey", tidal_abbey, views=VIEWS)],
    spacing=80, separation=32, heightmap="WORLD_SURFACE_WG", adaptation="none", processors="none", max_distance=116,
    foundation=False, spawns=[("minecraft:drowned", 6, 1, 2), ("brasshaven:skeleton_knight", 2, 1, 1), ("brasshaven:tide_wraith", 5, 1, 2)],
    title_fr="Abbaye des marées", title_en="Tidal Abbey"))

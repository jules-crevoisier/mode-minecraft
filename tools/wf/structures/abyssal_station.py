"""The Abyssal Station (La Station abyssale): a brass-and-glass deep-sea research station on the floor of the deep
ocean, ~180 blocks across. Colossal tier (tools/BUILDING.md §1, §12 concept 29, §10 legacy-dungeon template, §15),
steampunk (tools/STYLE_STEAMPUNK.md: dark iron hulls and footings, brass ribs and bands, glass, amber and sea-lantern
light against the black water).

Silhouette (one noun phrase, §15.1): a cluster of ribbed glass pressure domes on the sea floor round one great dome,
joined by glass tubes, a slender access tower rising out of the waves with a docking deck and a crane, and a lattice
drilling derrick straddling a black trench.

Placement: fit mode ``seabed`` (wf/placement.py), heightmap OCEAN_FLOOR_WG: blueprint y = 0 is the sea floor, the sea
is 22+ deep (deep oceans: 22 to ~40). The access tower's docking deck stands at y 48, above the surface at any of
those depths, and its outer stair tower reaches down to y 12, below it, so a swimmer finds steps at any sea level.
Every walked interior is a sealed air pocket: the pressurised modules are built as one union of volumes whose
boundary (6-connected) becomes the hull, so no interior air cell ever touches the sea; the structure is placed with
``liquid_settings: ignore_waterlogging`` (an interior stair is never filled with the sea that stood there before),
the waterloggable decorations outside are waterlogged by hand below SEA_MIN, and no air is written outside the hull.
Doors are the airlocks (a door holds the sea back); the flooded maintenance tube is water inside its own hull.

Layout (x east, z south; floor y 0, feet 1):
  * the surface access tower (0, 62): the docking deck (y 48) with the expedition camp (waystone), the bathyscaphe
    crane, mooring bollards and the outer stair tower down into the sea; the lantern room on top (searchlight);
  * the access shaft: a helical stair (8 per turn) round the glass casing of the bubble-column lift (shortcut 1: it
    rises from the reception lock to the lantern room), sea windows all the way down;
  * the reception lock (hub, waystone) at the foot of the tower: lockers, diving suits, the decompression gauges;
  * the great dome (0, 0), 40 wide, 28 high: the concourse round the light well (a glass column of glowstone and sea
    lanterns in a pool), two flights up to the observation floor ring (the vista over the whole station);
  * west: the hydroponics dome (grow beds, grow lamps, irrigation pump), north of it the specimen aquarium hall (a
    glass barrel vault on the sea, tanks of kelp and coral, the dissection bench), south of it the crew quarters
    (mess and galley below, bunks and the director's cabin above), whose tube runs back to the lock (loops);
  * east: the reactor / boiler room (reactor core, boilers, catwalk ring, turbines), the whale-fall observation deck
    south of it (a glass bubble over a whale skeleton sliding into the trench) and the flooded maintenance tube back
    to the lock (shortcut 2: doors at both ends, a conduit in a prismarine ring halfway);
  * north-east: the drill control room on the trench lip (consoles over the rig), whose tube west back to the great
    dome ends at a one-way pressure hatch (shortcut 3: an iron door with its lever on the control-room side only);
  * the drill shaft: a glass caisson standing in the trench, a helical stair 43 blocks down to the site of grace
    (waystone) at the trench bottom; a low corridor (compression, the mist) to the drill chamber (boss arena: 34
    wide, under the brass skylight dome in the trench floor, the drill bit hanging from it);
  * the specimen vault behind sealed bars west of the arena (best loot), whose bubble-column lift rises 43 blocks
    through the rock into the reactor room (the way back after the boss);
  * outside: the drilling rig (deck on four lattice legs over the trench, the derrick, the drill string plunging into
    the chamber), the trench itself, two kelp farms with brass frames, searchlights, pipes and the whale fall.
Loot gradient (§15.6): camp, lock tier 1; concourse, hydroponics, crew 1-2; aquarium, boiler, whale deck, tube 2;
control room, observation floor, cabin 2-3; the specimen vault 3+.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_STAIRS, PIPES, TABLE, TREAD,
                       TREAD_SLAB, TREAD_STAIRS, VERD, W, fbm, hash01, hash3)
from ..parts import LOOT, MOD
from .verdant_arboretum import dark_floors, light_map

# the champion of the drill chamber: the Abyssal Diver (tools/wf/mobs/abyss_diver.py, entity/boss/AbyssDiver.java)
BOSS = "brasshaven:abyss_diver"
MOB_MARINE = W + "drowned_marine"
MOB_CRAB = W + "barnacle_crab"
MOB_WRAITH = W + "tide_wraith"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_GUNNER = W + "boiler_gunner"
MOB_CRAWLER = W + "abyss_crawler"
MOB_MITE = W + "rust_mite"

AIR = "minecraft:air"
WATER = "water[level=0]"
GLASS = "glass"
SEA_L = "sea_lantern"
GLOW = "glowstone"
IRON_BR = W + "dark_iron_bricks"
PARQUET = W + "mahogany_parquet"
CHAIR = W + "mahogany_chair"
VALVE = W + "valve_wheel"
COG = W + "wall_cog"
SHELF = W + "wall_shelf"
RAIL = W + "brass_railing"
DSL = "polished_deepslate"
DTILE = "deepslate_tiles"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))

SEA_MIN = 20             # the lowest sea surface (top water block) the fit allows: below it, outside means water
DECK = 48                # docking deck block y (feet 49)
TOWER = (0, 62)          # access tower axis
G = (0, 0, 20, 10, 18)   # great dome: centre x, z, outer radius, drum top, dome rise
OBS = 12                 # observation floor feet (floor block y 11)
H_D = (-46, 0, 11, 5, 10)        # hydroponics
C_D = (-44, 42, 10, 10, 7)       # crew quarters
B_D = (46, 4, 12, 10, 10)        # reactor / boiler room
D_D = (40, -44, 9, 6, 8)         # drill control room
W_D = (40, 52, 7, 2, 7)          # whale-fall observation deck
LOCK = (-9, 9, 38, 54, 8)        # reception lock box x0, x1, z0, z1, roof y
AQ = (-62, -30, -52, -38)        # aquarium hall x0, x1, z0, z1
AQ_SPRING, AQ_R = 3, 7.5
SH = (68, -44)                   # drill shaft axis (square caisson 13 x 13)
SH_TOP, SH_BOT = 1, -42          # shaft feet: top (tube level) and bottom (trench-bottom landing)
AC = (72, -8, 17)                # arena centre and radius
AF = -42                         # arena feet
A_WALL, A_RISE = -31, 7          # arena wall top, dome rise
VAULT = (40, 52, -14, -2)        # vault box x0, x1, z0, z1 (outer)
LIFT2 = (46, -4)                 # vault -> reactor bubble lift
RIG = (58, 86, -20, 4, 10)       # rig deck x0, x1, z0, z1, deck y


def pick(choices, x, y, z, seed):
    tot = sum(w for _, w in choices)
    h = hash3(x, y, z, seed) * tot
    for s, w in choices:
        h -= w
        if h <= 0:
            return s
    return choices[-1][0]


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def rail(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def water_gate(C, x, z, y0, facing):
    """A two-high pair of fence gates in a hull wall between air and water: the closed (dry) gates hold the water
    back like a door (fence gates are force-solid: open or shut, water never flows into them), the player opens
    both and swims through."""
    for y in (y0, y0 + 1):
        C.force(x, y, z, f"spruce_fence_gate[facing={facing},in_wall=false,open=false,powered=false]")


def trench_cx(z):
    return 72 + 3.0 * math.sin(z / 23.0)


def trench_hw(z):
    return 9.0 + (fbm(z * 0.7, 5.0, 9.0, 301) - 0.5) * 3.0


def trench_bottom(x, z):
    """Floor y of the trench at (x, z) (None outside it): a U-shaped cut, deepest along the centre line."""
    if z < -92 or z > 74:
        return None
    w = trench_hw(z)
    dx = abs(x - trench_cx(z))
    if dx >= w:
        return None
    t = dx / w
    end = min(1.0, (z + 92) / 14.0, (74 - z) / 14.0)
    depth = (5 + 22 * (1 - t ** 2.2)) * end + (fbm(x * 0.6, z * 0.6, 5.0, 303) - 0.5) * 3
    return -max(2, int(round(depth)))


# ------------------------------------------------------------------ site state
class Ctx:
    def __init__(self, bp):
        self.bp = bp
        self.V = set()          # every pressurised cell (hull + interior)
        self.owner = {}         # cell -> skin function
        self.shell = set()      # the hull: boundary cells of V
        self.inner = set()      # interior air cells
        self.wet = set()        # flooded maintenance tube interior

    def set(self, x, y, z, spec, data=None):
        p = (x, y, z)
        if p in self.shell and not barrier(spec):
            return
        if spec == AIR and p not in self.inner:
            return
        self.bp.set(x, y, z, spec, data)

    def force(self, x, y, z, spec, data=None):
        self.bp.set(x, y, z, spec, data)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def free(self, x, y, z):
        return (x, y, z) in self.inner and self.bp.get(x, y, z) == AIR

    def put(self, x, y, z, spec):
        """Furniture: only on interior air."""
        if self.free(x, y, z):
            self.bp.set(x, y, z, spec)
            return True
        return False

    def add(self, cells, skin):
        for p in cells:
            self.V.add(p)
            if p not in self.owner:
                self.owner[p] = skin


def barrier(spec):
    """Blocks that keep water out of a neighbouring air cell: full blocks, glass, doors, and the waterloggable blocks
    set dry (flowing water cannot fill them)."""
    s = spec if isinstance(spec, str) else spec[0]
    s = s.split("[")[0].split(":")[-1]
    if s in ("air", "water", "bubble_column", "lever", "torch", "wall_torch", "redstone_wire", "carpet") or \
            s.endswith("_carpet") or s.endswith("_button") or s.endswith("pressure_plate"):
        return False
    return True


# ------------------------------------------------------------------ volumes
def dome_cells(cx, cz, R, dh, H, y0=0):
    out = set()
    r = int(math.ceil(R))
    for x in range(cx - r, cx + r + 1):
        for z in range(cz - r, cz + r + 1):
            d = math.hypot(x - cx, z - cz)
            if d >= R:
                continue
            for y in range(y0, dh + 1):
                out.add((x, y, z))
            y = dh + 1
            while (d / R) ** 2 + ((y - dh) / H) ** 2 < 1.0:
                out.add((x, y, z))
                y += 1
    return out


def box_cells(x0, x1, y0, y1, z0, z1):
    return {(x, y, z) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1) for z in range(z0, z1 + 1)}


def tube_cells(axis, a0, a1, c, y0=0, h=5, chamfer=True):
    """A tube along x (axis 'x', c = z of its centre line) or z: 5 wide, h tall (y0 .. y0+h), top corners cut."""
    out = set()
    for u in range(min(a0, a1), max(a0, a1) + 1):
        for w in range(-2, 3):
            for y in range(y0, y0 + h + 1):
                if chamfer and abs(w) == 2 and y == y0 + h:
                    continue
                out.add((u, y, c + w) if axis == "x" else (c + w, y, u))
    return out


# ------------------------------------------------------------------ skins
def dome_skin(cx, cz, R, dh, H, ribs=8, floor=None, y0=0, windows="band"):
    step = 2 * math.pi / ribs

    def f(x, y, z):
        d = math.hypot(x - cx, z - cz)
        a = math.atan2(z - cz, x - cx)
        if y <= y0:
            if floor:
                return floor(x, z, d)
            return TREAD if d < R - 1.5 else IRON
        rib = abs(((a + step / 2) % step) - step / 2) * max(d, 1.0) < 0.75
        if y <= dh:
            if y == dh:
                return BRASS
            if y == y0 + 1:
                return IRON_BR
            if rib:
                return BRASS
            if windows == "band" and y0 + 3 <= y <= dh - 1:
                return GLASS
            if windows == "port" and y == y0 + (dh - y0) // 2 + 1:
                return GLASS if abs(((a + step / 4) % (step / 2)) - step / 4) * d < 1.1 else IRON
            return IRON if hash3(x, y, z, 11) < 0.9 else COPPER
        t = (y - dh) / H
        if t > 0.86:
            return BRASS
        if rib:
            return VERD if t < 0.25 and hash3(x, y, z, 12) < 0.35 else BRASS
        if y == dh + max(2, int(round(H * 0.45))):
            return BRASS
        return GLASS
    return f


def tube_skin(axis, c):
    def f(x, y, z):
        u, w = (x, z - c) if axis == "x" else (z, x - c)
        if y <= 0:
            return TREAD if abs(w) <= 1 else IRON
        if u % 6 == 0:
            return BRASS
        if y == 1:
            return IRON
        if y >= 5 and abs(w) <= 1 and u % 6 == 3:
            return SEA_L
        return GLASS
    return f


def lock_skin(x, y, z):
    x0, x1, z0, z1, top = LOCK
    if y <= 0:
        return PARQUET if x0 + 2 <= x <= x1 - 2 and z0 + 2 <= z <= z1 - 2 else TREAD
    if y >= top:
        if (x - x0) % 6 == 0 or (z - z0) % 4 == 0:
            return BRASS
        return GLASS if x0 + 2 <= x <= x1 - 2 and z0 + 2 <= z <= z1 - 2 else IRON
    corner = x in (x0, x1) and z in (z0, z1)
    if corner or y == top - 1:
        return BRASS
    if y <= 1:
        return IRON_BR
    if (x - x0) % 4 == 2 and z in (z0, z1) and 3 <= y <= 5:
        return GLASS
    if (z - z0) % 4 == 2 and x in (x0, x1) and 3 <= y <= 5:
        return GLASS
    return IRON


def aq_skin(x, y, z):
    x0, x1, z0, z1 = AQ
    if y <= 0:
        return PARQUET if z0 + 2 <= z <= z1 - 2 else TREAD
    if x in (x0, x1):
        dz = z - (z0 + z1) / 2
        if y >= 3 and abs(dz) <= 3 and y <= 7 and (abs(dz) + (y - 5) ** 2 * 0.6) < 3.5:
            return GLASS
        return BRASS if y % 4 == 0 or abs(dz) > 6 else IRON
    if (x - x0) % 4 == 0:
        return BRASS
    if y <= 2:
        return IRON_BR if y == 1 else IRON
    return GLASS


def aq_cells():
    x0, x1, z0, z1 = AQ
    zc = (z0 + z1) / 2
    out = set()
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            dz = abs(z - zc)
            for y in range(0, AQ_SPRING + 1):
                out.add((x, y, z))
            y = AQ_SPRING + 1
            while dz * dz + (y - AQ_SPRING) ** 2 < AQ_R ** 2:
                out.add((x, y, z))
                y += 1
    return out


def tower_skin(x, y, z):
    cx, cz = TOWER
    d = math.hypot(x - cx, z - cz)
    a = math.atan2(z - cz, x - cx)
    if y <= 0:
        return TREAD
    if y >= DECK:
        # the lantern room: glass between brass mullions, a brass roof
        if y >= DECK + 8:
            return BRASS if hash3(x, y, z, 21) < 0.85 else VERD
        if y == DECK or y == DECK + 7:
            return BRASS
        k = int(((a + math.pi) / (2 * math.pi)) * 16)
        return IRON if k % 4 == 0 else GLASS
    if y % 6 == 0:
        return BRASS
    k = int(((a + math.pi) / (2 * math.pi)) * 12 + y / 3.0) % 4
    if y <= 2:
        return IRON_BR
    return GLASS if k == 0 else (VERD if y < SEA_MIN - 4 and hash3(x, y, z, 22) < 0.3 else IRON)


def tower_cells():
    cx, cz = TOWER
    out = set()
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            d = math.hypot(x - cx, z - cz)
            if d < 6.5:
                for y in range(0, DECK):
                    out.add((x, y, z))
            if d < 8.5:
                for y in range(DECK, DECK + 8):
                    out.add((x, y, z))
                y = DECK + 8
                while (d / 8.5) ** 2 + ((y - DECK - 7) / 4.0) ** 2 < 1.0:
                    out.add((x, y, z))
                    y += 1
    return out


def sh_skin(x, y, z):
    cx, cz = SH
    edge_x, edge_z = abs(x - cx) == 6, abs(z - cz) == 6
    if y <= SH_BOT - 1:
        return TREAD
    tb = trench_bottom(x, z)
    if y >= 8:
        return BRASS if (x + z) % 3 else IRON
    if edge_x and edge_z:
        return IRON
    if (y - SH_BOT) % 6 == 0:
        return BRASS
    under = tb is not None and y < tb + 1
    if tb is None and y <= 0:
        under = True
    if under:
        return IRON_BR if hash3(x, y, z, 31) < 0.6 else DSL
    u = (z - cz) if edge_x else (x - cx)
    return IRON if abs(u) in (3, 6) else GLASS


def arena_skin(x, y, z):
    cx, cz, R = AC
    d = math.hypot(x - cx, z - cz)
    a = math.atan2(z - cz, x - cx)
    if y <= AF - 1:
        ring = int(d)
        if ring in (4, 10, 15):
            return BRASS
        if ring < 4:
            return IRON
        return TREAD if (ring // 2) % 2 == 0 else IRON_BR
    rib = abs(((a + math.pi / 12) % (math.pi / 6)) - math.pi / 12) * max(d, 1.0) < 0.8
    if y <= A_WALL:
        if rib:
            return BRASS
        if y == A_WALL or y == AF + 5:
            return BRASS
        if y <= AF + 1:
            return DSL
        return IRON_BR if hash3(x, y, z, 41) < 0.55 else IRON
    if rib:
        return BRASS
    t = (y - A_WALL) / A_RISE
    return GLASS if t > 0.35 else IRON


def vault_skin(x, y, z):
    if y <= AF - 1:
        return PARQUET
    if y == AF + 5:
        return BRASS
    return IRON if (x + y) % 5 else BRASS


def corridor_skin(axis):
    def f(x, y, z):
        u = x if axis == "x" else z
        if y <= AF - 1:
            return TREAD
        if u % 4 == 0:
            return BRASS
        return IRON_BR if hash3(x, y, z, 51) < 0.6 else DSL
    return f


def floor_great(x, z, d):
    """Great-dome floor: a brass compass rose, tread rings, parquet between."""
    cx, cz = G[0], G[1]
    a = math.atan2(z - cz, x - cx)
    if d < 4.6:
        return IRON
    if 4.6 <= d < 5.6 or 11.5 <= d < 12.5:
        return BRASS
    if d < 11.5:
        arm = abs(((a + math.pi / 8) % (math.pi / 4)) - math.pi / 8) * d
        return BRASS if arm < 0.6 + (11.5 - d) * 0.12 else PARQUET
    if d >= G[2] - 1.5:
        return IRON
    return TREAD


# ------------------------------------------------------------------ the hull
def build_hull(C):
    gx, gz, gr, gdh, gH = G
    C.add(dome_cells(gx, gz, gr, gdh, gH), dome_skin(gx, gz, gr, gdh, gH, ribs=12, floor=floor_great))
    for (cx, cz, R, dh, H), ribs, win in ((B_D, 8, "port"), (H_D, 8, "band"), (C_D, 8, "port"), (D_D, 6, "band"),
                                          (W_D, 6, "band")):
        C.add(dome_cells(cx, cz, R, dh, H), dome_skin(cx, cz, R, dh, H, ribs=ribs, windows=win))
    C.add(tower_cells(), tower_skin)
    x0, x1, z0, z1, top = LOCK
    C.add(box_cells(x0, x1, 0, top, z0, z1), lock_skin)
    C.add(box_cells(-2, 2, 0, 5, 53, 58), lock_skin)                # the lock's door into the tower foot
    C.add(aq_cells(), aq_skin)
    # the tubes: (axis, from, to, centre line)
    tubes = [
        ("z", 18, 39, 0),            # lock -> great dome
        ("x", -38, -18, 0),          # great dome -> hydroponics
        ("z", -40, -9, -46),         # hydroponics -> aquarium
        ("z", 9, 34, -46),           # hydroponics -> crew quarters
        ("x", -36, -8, 46),          # crew quarters -> lock
        ("x", -31, -10, -45),        # aquarium -> (corner)
        ("z", -47, -14, -12),        # (corner) -> great dome
        ("x", 18, 36, 0),            # great dome -> reactor
        ("z", -37, -5, 42),          # reactor -> drill control
        ("z", 14, 47, 42),           # reactor -> whale deck
        ("x", 6, 33, -44),           # drill control -> (corner): the hatch tube
        ("z", -46, -16, 8),          # (corner) -> great dome
        ("x", 47, 63, -44),          # drill control -> drill shaft (over the trench)
    ]
    for axis, a0, a1, c in tubes:
        C.add(tube_cells(axis, a0, a1, c), tube_skin(axis, c))
    # the drill shaft caisson, the corridor to the arena, the arena, the vault and its passage
    sx, sz = SH
    C.add(box_cells(sx - 6, sx + 6, SH_BOT - 1, 9, sz - 6, sz + 6), sh_skin)
    C.add(box_cells(66, 70, AF - 1, AF + 4, -39, -22), corridor_skin("z"))
    ax, az, ar = AC
    C.add(dome_cells(ax, az, ar, A_WALL, A_RISE, y0=AF - 1), arena_skin)
    vx0, vx1, vz0, vz1 = VAULT
    C.add(box_cells(vx0, vx1, AF - 1, AF + 5, vz0, vz1), vault_skin)
    C.add(box_cells(vx1 - 2, 57, AF - 1, AF + 4, -10, -6), corridor_skin("x"))
    # boundary -> hull, the rest -> air
    V = C.V
    for p in V:
        x, y, z = p
        if any((x + dx, y + dy, z + dz) not in V for dx, dy, dz in N6):
            C.shell.add(p)
    for p in V:
        if p in C.shell:
            C.bp.set(*p, C.owner[p](*p))
        else:
            C.bp.set(*p, AIR)
            C.inner.add(p)


def footings(C):
    """Dark iron footings under every module: a solid slab under the floor and a ring wall into the sea floor (the
    hull never hangs over a dip in the sand), piers under the tubes; a sand-and-gravel apron round the bases."""
    bottoms = {}
    for (x, y, z) in C.V:
        if y >= 0 and ((x, z) not in bottoms or y < bottoms[(x, z)]):
            bottoms[(x, z)] = y
    cols = {c for c, y in bottoms.items() if y == 0}
    for (x, z) in cols:
        edge = any((x + dx, z + dz) not in cols for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        pier = (x % 8 == 0 and z % 8 == 0)
        depth = 6 if (edge or pier) else 1
        for y in range(-depth, 0):
            if C.get(x, y, z) is None:
                C.force(x, y, z, IRON_BR if edge and y == -1 else (DTILE if hash3(x, y, z, 61) < 0.5 else DSL))
    # the apron: sand, gravel and clay round the footings
    ring = set()
    for (x, z) in cols:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                q = (x + dx, z + dz)
                if q not in bottoms:
                    ring.add(q)
    for (x, z) in ring:
        if C.get(x, 0, z) is not None:
            continue
        n = fbm(x, z, 6.0, 62)
        C.force(x, 0, z, "gravel" if n < 0.35 else ("clay" if n > 0.72 else "sand"))
        for y in range(-3, 0):
            if C.get(x, y, z) is None:
                C.force(x, y, z, "sand" if y > -2 else "sandstone")


# ------------------------------------------------------------------ stairs
def helix(C, cx, cz, ring, f_top, f_bot, P, start, sgn, lip=True):
    """A helical stair over the ring cells round (cx, cz): feet f_top at angle `start`, going down P per turn in the
    direction sgn (+1 = increasing atan2 angle), to f_bot. Returns {(x, z): [feet...]}."""
    treads = {}
    for (x, z) in ring:
        a = math.atan2(z - cz, x - cx)
        frac = ((a - start) * sgn) % (2 * math.pi) / (2 * math.pi)
        k = 0
        fs = []
        while True:
            f = f_top - k * P - int(frac * P)
            if f <= f_bot:
                break
            fs.append(f)
            k += 1
        treads[(x, z)] = (frac, fs)
    for (x, z), (frac, fs) in treads.items():
        for f in fs:
            fc = None
            for d, (dx, dz) in DIRS.items():
                nb = treads.get((x + dx, z + dz))
                if nb and (f + 1) in nb[1]:
                    fc = d
                    break
            C.set(x, f - 1, z, stair(TREAD_STAIRS, fc) if fc else TREAD)
            if f - 1 - f_bot < 3:
                for yy in range(f_bot, f - 1):
                    C.set(x, yy, z, IRON)
        if lip and frac > 0.8:
            # the seam at the top: a landing lip over the end of the first turn, railed along its cut edge, so
            # nobody walks off the head of the stair into the turn below
            C.set(x, f_top - 1, z, TREAD)
            if frac < 0.84 and C.free(x, f_top, z):
                rail(C, x, f_top, z, "north")
    return treads


# ------------------------------------------------------------------ the access tower and the camp
def tower_interior(C):
    cx, cz = TOWER
    ring = [(x, z) for x in range(cx - 7, cx + 8) for z in range(cz - 7, cz + 8)
            if max(abs(x - cx), abs(z - cz)) > 1 and (x, 10, z) in C.inner]
    rset = set(ring)
    helix(C, cx, cz, ring, DECK + 1, 1, 8, -math.pi / 2, 1)
    # the lantern-room floor round the stair well (the well stays open), a bridge to the lift's top
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            d = math.hypot(x - cx, z - cz)
            if (x, z) not in rset and max(abs(x - cx), abs(z - cz)) > 1 and (x, DECK, z) in C.inner:
                C.set(x, DECK, z, PARQUET if d < 7.5 else TREAD)
    for t in range(2, 6):
        for w in (-1, 0, 1):
            C.set(cx - t, DECK, cz + w, TREAD)
    for z in range(cz - 1, cz + 2):
        for t in (2, 3, 4, 5):
            if abs(z - cz) == 1:
                rail(C, cx - t, DECK + 1, z, "north" if z < cz else "south")
    # the rail round the well
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            if 5.0 <= d < 5.5 + 0.01 and C.get(x, DECK, z) == AIR:
                pass
            if 5.5 <= d < 6.3 and C.get(x, DECK, z) not in (None, AIR) and C.free(x, DECK + 1, z):
                a = math.atan2(z - cz, x - cx)
                frac = ((a + math.pi / 2)) % (2 * math.pi) / (2 * math.pi)
                if 0.04 < frac < 0.96:
                    dx, dz = x - cx, z - cz
                    fc = ("east" if dx < 0 else "west") if abs(dx) > abs(dz) else ("south" if dz < 0 else "north")
                    rail(C, x, DECK + 1, z, fc)
    # the lift: soul sand, a bubble column from the lock floor to the lantern room, a glass casing, a door at the foot
    C.force(cx, -1, cz, "soul_sand")
    C.force(cx, 0, cz, "bubble_column[drag=false]")
    for y in range(1, DECK + 1):
        C.force(cx, y, cz, "bubble_column[drag=false]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx or dz:
                    if y == DECK:
                        C.force(cx + dx, y, cz + dz, BRASS)
                    elif dx and dz:
                        C.force(cx + dx, y, cz + dz, BRASS if y % 6 else SEA_L)
                    else:
                        C.force(cx + dx, y, cz + dz, GLASS if y % 6 else BRASS)
    C.force(cx, 0, cz - 1, BRASS)
    water_gate(C, cx, cz - 1, 1, "north")
    C.force(cx, 3, cz - 1, BRASS)
    # sea lanterns set in the shaft wall every 6 blocks
    for y in range(4, DECK, 6):
        for (dx, dz) in ((6, 0), (-6, 0), (0, 6), (0, -6), (4, 4), (-4, -4), (4, -4), (-4, 4)):
            p = (cx + dx, y, cz + dz)
            if p in C.shell:
                C.set(*p, SEA_L)
    # the lantern room: a map chest, the winch, a brass lamp under the roof, the door onto the deck
    C.set(cx, DECK + 6, cz, CHANDELIER)
    for y in range(DECK + 7, DECK + 12):
        if C.free(cx, y, cz):
            C.set(cx, y, cz, CHAIN)
    C.bp.door(cx + 8, DECK + 1, cz, "east", wood="spruce")
    C.bp.door(cx - 8, DECK + 1, cz, "west", wood="spruce", hinge="right")
    C.bp.chest(cx + 6, DECK + 1, cz + 3, "west", loot=LOOT + "abs_camp")
    C.set(cx + 6, DECK + 1, cz - 3, "lectern[facing=west,has_book=false,powered=false]")
    C.set(cx + 7, DECK + 1, cz - 1, GAUGE)
    C.set(cx + 7, DECK + 1, cz + 1, VALVE)
    C.set(cx - 2, DECK + 1, cz + 6, "cartography_table")
    C.set(cx + 2, DECK + 1, cz + 6, "barrel[facing=up,open=false]")


def deck(C):
    """The docking deck round the lantern room: plank-and-tread ring on brass brackets, rails, bollards, the camp
    (tents, fire, waystone), the bathyscaphe crane, the searchlight and the outer stair tower down into the sea."""
    cx, cz = TOWER
    y = DECK
    for x in range(cx - 15, cx + 16):
        for z in range(cz - 15, cz + 16):
            d = math.hypot(x - cx, z - cz)
            if 8.5 <= d < 14.5:
                C.set(x, y, z, "spruce_planks" if int(d) % 3 else TREAD)
                if d >= 13.5:
                    a = math.atan2(z - cz, x - cx)
                    if not (abs(x - cx) <= 1 and z > cz):       # the gap for the stair tower
                        dx, dz = x - cx, z - cz
                        fc = ("east" if dx > 0 else "west") if abs(dx) > abs(dz) else ("south" if dz > 0 else "north")
                        rail(C, x, y + 1, z, fc)
                    if int((a + math.pi) * 6) % 5 == 0 and hash01(x, z, 71) < 0.5:
                        C.set(x, y - 1, z, IRON_STAIRS + "[facing=%s,half=top,shape=straight,waterlogged=false]" %
                              (("west" if x > cx else "east") if abs(x - cx) > abs(z - cz) else
                               ("north" if z > cz else "south")))
            elif 14.5 <= d < 15.2 and int(math.atan2(z - cz, x - cx) * 8) % 3 == 0:
                C.set(x, y - 1, z, IRON_WALL)
    # brackets under the deck: struts down to the shaft wall
    for k in range(16):
        a = k * math.pi / 8
        for t in range(0, 6):
            x = int(round(cx + math.cos(a) * (13 - t)))
            z = int(round(cz + math.sin(a) * (13 - t)))
            yy = y - 1 - t
            if math.hypot(x - cx, z - cz) >= 6.6 and C.get(x, yy, z) is None:
                C.set(x, yy, z, IRON_WALL if t < 5 else IRON)
    # the camp on the north-west quarter: two canvas tents, the fire, the waystone, crates
    C.set(cx - 9, y + 1, cz - 9, MOD["waystone"])
    C.set(cx - 10, y + 1, cz - 8, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(cx - 6, y, cz - 11, "cobblestone")
    C.set(cx - 6, y + 1, cz - 11, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, fc) in ((cx - 8, cz - 11, "east"), (cx - 4, cz - 11, "west")):
        C.set(x, y + 1, z, stair("spruce_stairs", OPP[fc]))
    for (tx, tz, col) in ((cx - 12, cz - 3, "white_wool"), (cx + 3, cz - 12, "light_gray_wool")):
        horiz = tz == cz - 3
        for k in range(4):
            if horiz:
                C.set(tx - 1, y + 1, tz + k - 2, col)
                C.set(tx + 1, y + 1, tz + k - 2, col)
                C.set(tx, y + 2, tz + k - 2, col)
            else:
                C.set(tx + k - 2, y + 1, tz - 1, col)
                C.set(tx + k - 2, y + 1, tz + 1, col)
                C.set(tx + k - 2, y + 2, tz, col)
    C.set(cx - 12, y + 1, cz - 2, "white_carpet")
    C.set(cx + 2, y + 1, cz - 12, "light_gray_carpet")
    C.bp.barrel(cx - 11, y + 1, cz + 3, "up")
    C.bp.barrel(cx - 11, y + 2, cz + 3, "up")
    C.bp.barrel(cx - 10, y + 1, cz + 4, "up", loot=LOOT + "abs_camp")
    C.set(cx - 12, y + 1, cz + 2, "crafting_table")
    # bollards and coiled lines on the south and east rims
    for (x, z) in ((cx + 12, cz + 5), (cx + 12, cz - 5), (cx - 5, cz + 12), (cx + 5, cz + 12)):
        C.set(x, y + 1, z, IRON_WALL)
        C.set(x, y + 2, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    for (x, z) in ((cx + 10, cz + 8), (cx - 8, cz + 10)):
        C.set(x, y + 1, z, "brown_carpet")
    # deck lamps
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = int(round(cx + math.cos(a) * 12.5)), int(round(cz + math.sin(a) * 12.5))
        if C.get(x, y + 1, z) is None:
            C.set(x, y + 1, z, IRON_WALL)
            C.set(x, y + 2, z, EDISON)
    # the searchlight on the lantern-room roof
    top = max(y for (x, y, z) in C.V if (x, z) == (cx, cz)) + 1
    C.set(cx, top, cz, BRASS)
    C.set(cx, top + 1, cz, IRON_WALL)
    C.set(cx, top + 2, cz, SEA_L)
    C.set(cx + 1, top + 2, cz, "glass")
    C.set(cx - 1, top + 2, cz, BRASS)
    C.set(cx, top + 3, cz, BRASS_SLAB + "[type=bottom,waterlogged=false]")
    C.set(cx, top + 4, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    crane(C)
    stair_tower(C)


def crane(C):
    """The bathyscaphe crane on the east rim: a lattice mast, a jib over the sea, a chain down to the bathyscaphe."""
    cx, cz = TOWER
    mx, mz, y = cx + 11, cz - 6, DECK + 1
    for yy in range(y, y + 10):
        for dx in (0, 1):
            for dz in (0, 1):
                C.set(mx + dx, yy, mz + dz, IRON if (dx + dz + yy) % 2 == 0 or yy % 3 == 0 else IRON_WALL)
    C.set(mx, y, mz - 1, GEAR)
    C.set(mx - 1, y, mz, VALVE)
    jy = y + 10
    for t in range(-3, 16):
        C.set(mx + t, jy, mz, IRON if t % 3 else BRASS)
        if 0 <= t <= 13 and t % 2 == 0:
            C.set(mx + t, jy - 1, mz, IRON_WALL)
    for t in range(-3, 0):
        C.set(mx + t, jy - 1, mz, IRON_BR)                          # the counterweight
    C.set(mx + 1, jy + 1, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the chain and the bathyscaphe (a brass sphere, porthole, a sea lantern inside)
    bx, by, bz = mx + 14, DECK - 14, mz
    for yy in range(by + 3, jy):
        C.set(bx, yy, bz, CHAIN)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            for dz in range(-3, 4):
                r = math.sqrt(dx * dx + (dy * 1.1) ** 2 + dz * dz)
                if r < 3.2:
                    p = (bx + dx, by + dy, bz + dz)
                    if r < 2.0:
                        spec = SEA_L if (dx, dy, dz) == (0, 0, 0) else BRASS
                    elif dx == 3 and abs(dz) <= 1 and abs(dy) <= 1:
                        spec = GLASS
                    else:
                        spec = BRASS if (dy + 3) % 3 else IRON
                    C.set(*p, spec)
    C.set(bx, by + 3, bz, IRON_WALL)
    C.set(bx, by - 3, bz, "lightning_rod[facing=down,powered=false,waterlogged=false]")


def stair_tower(C):
    """The outer stair tower south of the shaft: switchback flights (3 wide, landings) from the deck down to y 12,
    so a swimmer finds steps at any sea level."""
    cx, cz = TOWER
    zA, zB = cz + 17, cz + 20          # the two lanes (centre lines)
    y = DECK
    cells = []
    lane = zA
    a = cx + 1
    direction = 1
    feet = y + 1
    # the head landing joins the deck gap
    for xx in range(cx - 1, cx + 2):
        for zz in range(cz + 13, cz + 17):
            C.set(xx, y, zz, TREAD)
    while feet > 13:
        # a flight of 6 steps down along x, then a landing across both lanes
        start = a if direction > 0 else a + 7
        for k in range(1, 7):
            fx = start + direction * k
            feet -= 1
            for w in (-1, 0, 1):
                cells.append((fx, lane + w, feet, "west" if direction > 0 else "east"))
        for lx in ((a + 7, a + 8) if direction > 0 else (a, a - 1)):
            for zz in range(zA - 1, zB + 2):
                cells.append((lx, zz, feet, None))
        direction = -direction
        lane = zB if lane == zA else zA
    for (fx, fz, f, fc) in cells:
        C.set(fx, f - 1, fz, stair(TREAD_STAIRS, fc) if fc else TREAD)
    xs = [c[0] for c in cells]
    x0, x1 = min(xs) - 1, max(xs) + 1
    # the frame: four corner posts to the sea floor, brass collars, rails on the outer edges
    for (px, pz) in ((x0, zA - 2), (x0, zB + 2), (x1, zA - 2), (x1, zB + 2)):
        for yy in range(0, y + 2):
            if C.get(px, yy, pz) is None:
                C.set(px, yy, pz, BRASS if yy % 8 == 0 else IRON)
    for (fx, fz, f, fc) in cells:
        for zz, fcr in ((zA - 2, "north"), (zB + 2, "south")):
            if fz in (zA - 1, zB + 1) and C.get(fx, f, zz) is None:
                rail(C, fx, f, zz, fcr)
    # brass hand-holds and lamps every landing
    for (fx, fz, f, fc) in cells:
        if fc is None and fz == zB + 1 and hash01(fx, f, 72) < 0.3 and C.get(fx, f + 2, zB + 2) is None:
            C.set(fx, f + 1, zB + 2, IRON_WALL)
            C.set(fx, f + 2, zB + 2, LANT)


# ------------------------------------------------------------------ the reception lock (hub)
def lock_room(C):
    x0, x1, z0, z1, top = LOCK
    f = 1
    C.set(-4, f, 50, MOD["waystone"])
    C.set(-5, f, 50, "candle[candles=2,lit=true,waterlogged=false]")
    # lockers along the west wall, diving suits, benches
    for z in range(z0 + 2, z1 - 1, 2):
        if 44 <= z <= 48:
            continue
        C.put(x0 + 1, f, z, "barrel[facing=east,open=false]")
        C.put(x0 + 1, f + 1, z, "barrel[facing=east,open=false]")
    C.bp.chest(x0 + 1, f, 43, "east", loot=LOOT + "abs_lock")
    for z in (41, 48):
        C.bp.entity(x1 - 1, f, z, {"id": "minecraft:armor_stand", "Rotation": [90.0, 0.0]})
    for x in (-5, -4, 4, 5):
        C.put(x, f, 41, stair(MAHOGANY_STAIRS, "south"))
    # the decompression panel: gauges, valves, pipes on the north wall either side of the tube door
    for x in (-4, -3, 3, 4):
        C.put(x, f + 1, z0 + 1, GAUGE if x % 2 else VALVE)
        C.put(x, f + 2, z0 + 1, PIPES)
    for x in (-6, 6):
        for y in range(f, top):
            C.put(x, y, z0 + 1, PIPES)
    # a rinse basin and a drying rack
    C.put(6, f, 51, "water_cauldron[level=3]")
    C.put(5, f, 51, "smoker[facing=north,lit=false]")
    C.put(7, f, 44, "cauldron")
    # lamps
    for (x, z) in ((-4, 42), (4, 42), (-4, 50), (4, 50)):
        y = top - 1
        if C.free(x, y, z):
            C.set(x, y, z, HANG_LAMP)
    C.put(4, f, 47, TABLE)
    C.put(3, f, 47, CHAIR + "[facing=east]")


# ------------------------------------------------------------------ the great dome
def great_dome(C):
    gx, gz, R, dh, H = G
    fy = OBS - 1
    # the observation floor: an annulus over the concourse, the light well open in the middle
    holes = set()
    for x in range(3, 15):
        for z in range(7, 10):
            holes.add((x, z))
    for x in range(-7, 5):
        for z in range(-16, -13):
            holes.add((x, z))
    landing = {(x, z) for x in (-8, -9) for z in (-16, -15, -14)} | {(x, z) for x in (15, 16) for z in (7, 8, 9)}
    for x in range(gx - R, gx + R + 1):
        for z in range(gz - R, gz + R + 1):
            d = math.hypot(x - gx, z - gz)
            if 8 <= d < 19.6 and (x, z) not in holes and (x, fy, z) in C.inner:
                C.set(x, fy, z, PARQUET if 10 <= d < 16 else TREAD)
                C.set(x, fy - 1, z, IRON_SLAB + "[type=top,waterlogged=false]") if (x + z) % 5 == 0 and \
                    C.free(x, fy - 1, z) else None
    # rails round the well and the stair holes
    for x in range(gx - R, gx + R + 1):
        for z in range(gz - R, gz + R + 1):
            if C.get(x, fy, z) in (None, AIR) or not C.free(x, OBS, z):
                continue
            for d_, (dx, dz) in DIRS.items():
                n = (x + dx, z + dz)
                if C.get(n[0], fy, n[1]) == AIR and (n[0], fy, n[1]) in C.inner and \
                        math.hypot(n[0] - gx, n[1] - gz) < 19.6:
                    if n in holes and (x, z) in landing:
                        continue
                    rail(C, x, OBS, z, d_)
                    break
    # the two flights up (west-ascending on the north side, east-ascending on the south side)
    for k in range(12):
        for z in (-16, -15, -14):
            x = 4 - k
            C.set(x, k, z, stair(TREAD_STAIRS, "west"))
            for yy in range(1, k):
                C.set(x, yy, z, IRON if yy % 4 else BRASS)
            for yy in range(k + 1, k + 4):
                C.set(x, yy, z, AIR)
    for z in (-16, -15, -14):
        for x in (-8, -9):
            C.set(x, fy, z, TREAD)
    for k in range(12):
        for z in (7, 8, 9):
            x = 3 + k
            C.set(x, k, z, stair(TREAD_STAIRS, "east"))
            for yy in range(1, k):
                C.set(x, yy, z, IRON if yy % 4 else BRASS)
            for yy in range(k + 1, k + 4):
                C.set(x, yy, z, AIR)
    for z in (7, 8, 9):
        for x in (15, 16):
            C.set(x, fy, z, TREAD)
    # the light well: a glass column of glowstone and sea lanterns from the pool to the crown
    crown = dh + H
    for y in range(1, crown + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                p = (gx + dx, y, gz + dz)
                if p not in C.inner:
                    continue
                if dx == 0 and dz == 0:
                    C.set(*p, GLOW if y % 3 else SEA_L)
                else:
                    C.set(*p, GLASS if y % 6 else BRASS)
    # the pool round its foot
    for x in range(gx - 5, gx + 6):
        for z in range(gz - 5, gz + 6):
            d = math.hypot(x - gx, z - gz)
            if max(abs(x - gx), abs(z - gz)) <= 1:
                continue
            if d < 3.6:
                C.set(x, 1, z, WATER)
                C.set(x, 0, z, "prismarine_bricks")
            elif d < 4.6:
                C.set(x, 1, z, BRASS)
                if hash01(x, z, 81) < 0.3:
                    C.set(x, 2, z, "potted_fern")
    for (x, z) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        C.set(x, 1, z, "sea_pickle[pickles=3,waterlogged=true]")
    # benches facing the well, kiosk, crates, map table
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = int(round(gx + math.cos(a) * 7)), int(round(gz + math.sin(a) * 7))
        dx, dz = x - gx, z - gz
        fc = ("east" if dx < 0 else "west") if abs(dx) > abs(dz) else ("south" if dz < 0 else "north")
        C.put(x, 1, z, stair(MAHOGANY_STAIRS, OPP[fc]))
    C.put(-10, 1, 6, TABLE)
    C.put(-11, 1, 6, CHAIR + "[facing=east]")
    C.put(-10, 1, 8, "lectern[facing=north,has_book=false,powered=false]")
    for (x, z) in ((-15, -8), (-16, -7), (-15, -7), (15, -6), (16, -5)):
        C.put(x, 1, z, "barrel[facing=up,open=false]")
    C.bp.chest(16, 1, -4, "west", loot=LOOT + "abs_concourse")
    C.bp.chest(-17, 1, 4, "east", loot=LOOT + "abs_concourse")
    # hanging lamps under the observation floor and from its rim
    for k in range(12):
        a = k * math.pi / 6
        x, z = int(round(gx + math.cos(a) * 13)), int(round(gz + math.sin(a) * 13))
        if C.free(x, fy - 1, z) and C.get(x, fy, z) not in (None, AIR):
            C.set(x, fy - 1, z, HANG_LAMP)
    # pipes and gauges on the drum between the doors
    for k in range(24):
        a = k * math.pi / 12
        x, z = int(round(gx + math.cos(a) * 18.6)), int(round(gz + math.sin(a) * 18.6))
        if C.free(x, 1, z) and C.free(x, 2, z) and C.free(x, 3, z) and k % 3 == 1:
            for y in range(1, 6):
                if C.free(x, y, z):
                    C.set(x, y, z, PIPES)
    # the observation floor: telescopes at the glass, armchairs, a chart table, a chest
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        x, z = int(round(gx + math.cos(a) * 17)), int(round(gz + math.sin(a) * 17))
        if C.free(x, OBS, z) and C.free(x, OBS + 1, z) and C.get(x, fy, z) not in (None, AIR):
            C.set(x, OBS, z, IRON_WALL)
            C.set(x, OBS + 1, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for (x, z, fc) in ((-12, 3, "east"), (-12, 5, "east"), (12, -3, "west"), (12, -5, "west")):
        C.put(x, OBS, z, CHAIR + "[facing=%s]" % fc)
    C.put(-11, OBS, 4, TABLE)
    C.put(11, OBS, -4, TABLE)
    C.put(0, OBS, 14, "lectern[facing=north,has_book=false,powered=false]")
    C.bp.chest(0, OBS, -17, "south", loot=LOOT + "abs_observation")
    C.put(1, OBS, -17, "bookshelf")
    C.put(-1, OBS, -17, "bookshelf")
    # the crown: a brass cupola and a searchlight over the dome
    top = max(y for (x, y, z) in C.V if (x, z) == (gx, gz))
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3:
                C.set(gx + dx, top + 1, gz + dz, BRASS if abs(dx) + abs(dz) < 3 else IRON)
    for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        C.set(gx + dx, top + 2, gz + dz, IRON_WALL)
        C.set(gx + dx, top + 3, gz + dz, IRON_WALL)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 2:
                C.set(gx + dx, top + 4, gz + dz, BRASS if abs(dx) + abs(dz) < 2 else VERD)
    C.set(gx, top + 2, gz, SEA_L)
    C.set(gx, top + 3, gz, SEA_L)
    C.set(gx, top + 5, gz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    C.bp.spawner(-9, OBS, -12, MOB_MARINE) if C.free(-9, OBS, -12) else None


# ------------------------------------------------------------------ hydroponics
def hydroponics(C):
    cx, cz, R, dh, H = H_D
    f = 1
    # beds: rows of farmland at y 1 (planter boxes), water channels between, crops on top; aisles on the axes
    crops = ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]")
    for x in range(cx - R + 2, cx + R - 1):
        for z in range(cz - R + 2, cz + R - 1):
            d = math.hypot(x - cx, z - cz)
            if d > R - 2.5 or d < 3.5:
                continue
            if abs(x - cx) <= 1 or abs(z - cz) <= 1:
                continue
            k = (z - cz) % 4
            rim = d > R - 3.5 or d < 4.5 or abs(x - cx) == 2 or abs(z - cz) == 2
            if rim:
                C.set(x, f, z, BRASS_SLAB + "[type=top,waterlogged=false]" if k == 0 else IRON)
                continue
            if k == 0:
                C.set(x, f, z, WATER)
            elif k == 2:
                C.set(x, f, z, TREAD_SLAB + "[type=top,waterlogged=false]")
            else:
                C.set(x, f, z, "farmland[moisture=7]")
                C.set(x, f + 1, z, crops[int(hash01(x // 3, z, 91) * 4)])
    # the irrigation pump in the middle: a copper drum with pipes up to the dome
    for y in range(f, f + 4):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) + abs(dz) <= 1:
                    C.set(cx + dx, y, cz + dz, COPPER if y < f + 3 else BRASS)
    C.set(cx, f + 4, cz, GAUGE)
    for y in range(f + 5, dh + H):
        if C.free(cx, y, cz):
            C.set(cx, y, cz, PIPES)
    for (dx, dz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        C.put(cx + dx, f, cz + dz, VALVE)
    # grow lamps on chains
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = int(round(cx + math.cos(a) * 6.5)), int(round(cz + math.sin(a) * 6.5))
        y = f + 5
        if C.free(x, y, z):
            t = y + 1
            while t < dh + H and C.free(x, t, z):
                t += 1
            for yy in range(y + 1, t):
                C.set(x, yy, z, CHAIN)
            C.set(x, y, z, GLOW)
    # shelves, composters, the gardener's bench
    C.put(cx + 9, f, cz + 3, "composter[level=5]")
    C.put(cx + 9, f, cz - 3, "composter[level=2]")
    C.put(cx - 9, f, cz + 3, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    C.put(cx - 9, f, cz - 3, "barrel[facing=up,open=false]")
    C.bp.chest(cx - 8, f, cz + 5, "east", loot=LOOT + "abs_hydro")
    C.put(cx + 7, f, cz + 6, "potted_red_mushroom")
    C.put(cx + 7, f, cz - 6, "potted_brown_mushroom")
    C.bp.spawner(cx + 5, f, cz + 8, MOB_MITE) if C.free(cx + 5, f, cz + 8) else None


# ------------------------------------------------------------------ the specimen aquarium hall
def tank(C, x0, z0, w, d, h, fill_seed):
    """A glass specimen tank on a brass plinth: water inside, kelp or coral or sea pickles, a glass lid."""
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            C.set(x, 1, z, BRASS)
            for y in range(2, 2 + h):
                edge = x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1)
                C.set(x, y, z, GLASS if edge else WATER)
            C.set(x, 2 + h, z, GLASS if (x + z) % 2 else BRASS)
    inner = [(x, z) for x in range(x0 + 1, x0 + w - 1) for z in range(z0 + 1, z0 + d - 1)]
    kind = fill_seed % 3
    for i, (x, z) in enumerate(inner):
        C.set(x, 2, z, "sand")
        if kind == 0:
            hh = 1 + int(hash01(x, z, fill_seed) * (h - 2))
            for y in range(3, 3 + hh):
                C.set(x, y, z, "kelp_plant")
            C.set(x, 3 + hh, z, "kelp[age=25]")
        elif kind == 1:
            corals = ("tube", "brain", "bubble", "fire", "horn")
            c = corals[int(hash01(x, z, fill_seed) * 5)]
            C.set(x, 2, z, f"{c}_coral_block")
            C.set(x, 3, z, f"{c}_coral[waterlogged=true]")
        else:
            C.set(x, 3, z, f"sea_pickle[pickles={1 + i % 4},waterlogged=true]")


def aquarium(C):
    x0, x1, z0, z1 = AQ
    zc = (z0 + z1) // 2
    # tanks along both sides of the central walk, a big tank at the west end
    for i, x in enumerate(range(x0 + 3, x1 - 3, 5)):
        if abs(x - (-46)) <= 3:
            continue
        tank(C, x, z0 + 2, 4, 4, 4, i * 7 + 1)
        tank(C, x, z1 - 5, 4, 4, 4, i * 7 + 2)
    tank(C, x0 + 1, zc - 2, 3, 5, 5, 3)
    # the dissection bench and the specimen shelves (jars), lamps
    for x in range(-44, -40):
        C.put(x, 1, z0 + 2, TABLE)
    C.put(-42, 1, z0 + 3, CHAIR + "[facing=north]")
    C.put(-48, 1, z0 + 2, "lectern[facing=south,has_book=false,powered=false]")
    C.put(-40, 1, z0 + 2, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    for x in range(x0 + 5, x1 - 2, 4):
        if C.free(x, AQ_SPRING + 5, zc):
            C.set(x, AQ_SPRING + 5, zc, HANG_LAMP)
            t = AQ_SPRING + 6
            while C.free(x, t, zc):
                C.set(x, t, zc, CHAIN)
                t += 1
    C.bp.chest(x1 - 1, 1, zc + 2, "west", loot=LOOT + "abs_aquarium")
    C.put(x1 - 1, 1, zc - 2, "barrel[facing=up,open=false]")
    C.put(x1 - 1, 2, zc - 2, "potted_dead_bush")
    for x in (x0 + 2, x1 - 2):
        C.put(x, 1, zc + 3, "decorated_pot[facing=north,cracked=false,waterlogged=false]")
    C.bp.spawner(-49, 1, z0 + 3, MOB_WRAITH) if C.free(-49, 1, z0 + 3) else None


# ------------------------------------------------------------------ crew quarters
def crew(C):
    cx, cz, R, dh, H = C_D
    f, f2 = 1, 7
    # the upper floor (feet 7), a stair along the south-west wall
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if d < R - 0.5 and (x, f2 - 1, z) in C.inner:
                C.set(x, f2 - 1, z, PARQUET if d < R - 2 else TREAD)
    for k in range(1, 7):
        for x in (cx - 1, cx, cx + 1):
            z = cz + 7 - k
            C.set(x, k, z, stair(MAHOGANY_STAIRS, "north"))
            for yy in range(1, k):
                C.set(x, yy, z, MAHOGANY)
            for y in range(k + 1, k + 5):
                if (x, y, z) in C.inner:
                    C.set(x, y, z, AIR)
    for x in (cx - 1, cx, cx + 1):
        C.set(x, f2 - 1, cz, TREAD)
    for z in range(cz + 1, cz + 7):
        for x in (cx - 2, cx + 2):
            if C.get(x, f2 - 1, z) not in (None, AIR):
                rail(C, x, f2, z, "east" if x > cx else "west")
    # the mess hall below: long table, benches; the galley along the east wall
    for z in range(cz - 6, cz - 1):
        C.put(cx - 4, f, z, TABLE)
        C.put(cx - 5, f, z, stair(MAHOGANY_STAIRS, "east"))
        C.put(cx - 3, f, z, stair(MAHOGANY_STAIRS, "west"))
    for (x, z, b) in ((cx + 7, cz - 3, "smoker[facing=west,lit=true]"), (cx + 7, cz - 2, "furnace[facing=west,lit=false]"),
                      (cx + 7, cz - 1, "barrel[facing=west,open=false]"), (cx + 7, cz + 1, "crafting_table"),
                      (cx + 7, cz + 2, "water_cauldron[level=2]")):
        C.put(x, f, z, b)
    C.bp.chest(cx + 6, f, cz - 5, "west", loot=LOOT + "abs_crew")
    C.put(cx - 7, f, cz + 3, "barrel[facing=up,open=false]")
    C.put(cx - 7, f, cz + 4, "barrel[facing=up,open=false]")
    for (x, z) in ((cx - 4, cz - 4), (cx + 4, cz - 4), (cx - 4, cz + 4), (cx + 4, cz + 4)):
        if C.free(x, f2 - 2, z):
            C.set(x, f2 - 2, z, HANG_LAMP)
    # upstairs: bunks round the wall, the director's cabin (desk, bookshelves, map) behind a partition
    beds = ((cx - 7, cz - 2, "north"), (cx - 7, cz + 1, "north"), (cx - 5, cz + 5, "east"), (cx + 4, cz + 6, "east"),
            (cx + 7, cz + 1, "south"), (cx + 7, cz - 2, "south"))
    for (x, z, fc) in beds:
        dx, dz = DIRS[fc]
        if C.free(x, f2, z) and C.free(x + dx, f2, z + dz):
            C.bp.bed(x, f2, z, fc, color="blue")
    for x in range(cx - 9, cx + 10):
        z = cz - 4
        if C.free(x, f2, z) and x != cx:
            for y in range(f2, f2 + 4):
                if C.free(x, y, z):
                    C.set(x, y, z, MAHOGANY if y < f2 + 3 else IRON)
    C.bp.door(cx, f2, cz - 4, "north", wood="dark_oak")
    C.set(cx, f2 + 2, cz - 4, MAHOGANY)
    C.set(cx, f2 + 3, cz - 4, IRON)
    C.put(cx + 3, f2, cz - 7, TABLE)
    C.put(cx + 3, f2, cz - 6, CHAIR + "[facing=north]")
    C.put(cx - 3, f2, cz - 7, "bookshelf")
    C.put(cx - 2, f2, cz - 7, "bookshelf")
    C.put(cx - 3, f2 + 1, cz - 7, "bookshelf")
    C.bp.chest(cx + 5, f2, cz - 6, "west", loot=LOOT + "abs_cabin")
    C.put(cx, f2, cz - 8, "lectern[facing=south,has_book=false,powered=false]")
    C.put(cx - 4, f2, cz - 6, "potted_fern")
    if C.free(cx, f2 + 4, cz - 6):
        C.set(cx, f2 + 4, cz - 6, LANT_H)
        t = f2 + 5
        while C.free(cx, t, cz - 6):
            C.set(cx, t, cz - 6, CHAIN)
            t += 1
    C.bp.spawner(cx - 5, f2, cz + 2, MOB_MARINE) if C.free(cx - 5, f2, cz + 2) else None


# ------------------------------------------------------------------ reactor / boiler room
def reactor(C):
    cx, cz, R, dh, H = B_D
    f, cat = 1, 8
    # the reactor core: an iron drum with glass windows on a glowing heart, a dome cap, pipes to the hull
    for y in range(f, f + 12):
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                d = math.hypot(x - cx, z - cz)
                if d >= 3.3:
                    continue
                if d < 1.6:
                    spec = "shroomlight" if y % 2 else GLOW
                elif d >= 2.4:
                    a = math.atan2(z - cz, x - cx)
                    spec = GLASS if (3 <= y - f <= 8 and int((a + math.pi) * 4 / math.pi) % 2 == 0) else (
                        BRASS if (y - f) % 4 == 0 else IRON)
                else:
                    spec = "copper_bulb[lit=true,powered=false]" if y % 3 == 0 else COPPER
                C.set(x, y, z, spec)
    for y in range(f + 12, dh + H):
        for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if C.free(cx + dx, y, cz + dz):
                C.set(cx + dx, y, cz + dz, PIPES if (dx, dz) != (0, 0) else IRON)
    # four boilers round it, turbines (gear panels) between, furnaces lit
    for k, (dx, dz) in enumerate(((7, 0), (-7, 0), (0, 7), (0, -7))):
        bx, bz = cx + dx, cz + dz
        if (bx, bz) == (cx, cz - 7) or (bx, bz) == (cx + 7, cz):
            continue
        for y in range(f, f + 5):
            for x in range(bx - 1, bx + 2):
                for z in range(bz - 1, bz + 2):
                    C.set(x, y, z, BRASS if y == f + 4 else (IRON if (x + z) % 2 else COPPER))
        C.set(bx, f + 5, bz, GAUGE)
    for (x, z, fc) in ((cx + 5, cz - 5, "south"), (cx - 5, cz + 5, "north"), (cx + 5, cz + 5, "north")):
        C.put(x, f, z, "blast_furnace[facing=%s,lit=true]" % fc)
    # the catwalk ring at feet 8 and its stair
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if 7.5 <= d < R - 0.5 and (x, cat - 1, z) in C.inner:
                C.set(x, cat - 1, z, TREAD)
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if 7.5 <= d < 8.5 and C.get(x, cat - 1, z) == TREAD and C.free(x, cat, z):
                dx, dz = x - cx, z - cz
                fc = ("west" if dx < 0 else "east") if abs(dx) > abs(dz) else ("north" if dz < 0 else "south")
                rail(C, x, cat, z, OPP[fc])
    # the stair to the catwalk: along the south-east wall, ascending north
    for k in range(1, 8):
        for x in (cx + 7, cx + 8, cx + 9):
            z = cz + 7 - k
            if (x, k, z) in C.inner:
                C.set(x, k, z, stair(TREAD_STAIRS, "north"))
                for yy in range(1, k):
                    C.set(x, yy, z, IRON)
                for y in range(k + 1, k + 5):
                    if (x, y, z) in C.inner and C.get(x, y, z) != AIR:
                        C.set(x, y, z, AIR)
    for x in (cx + 7, cx + 8, cx + 9):
        for z in (cz - 1, cz - 2):
            if (x, cat - 1, z) in C.inner:
                C.set(x, cat - 1, z, TREAD)
    # gauges, valves and the chest on the catwalk; lamps
    C.bp.chest(cx - 9, cat, cz - 3, "east", loot=LOOT + "abs_boiler")
    for k in range(10):
        a = k * math.pi / 5
        x, z = int(round(cx + math.cos(a) * 10.4)), int(round(cz + math.sin(a) * 10.4))
        if C.free(x, cat + 1, z):
            C.set(x, cat + 1, z, GAUGE if k % 2 else VALVE)
        if C.free(x, cat + 4, z) and k % 2 == 0:
            C.set(x, cat + 4, z, EDISON)
    for (x, z) in ((cx - 9, cz + 2), (cx + 2, cz + 9), (cx - 2, cz - 9)):
        C.put(x, f, z, "barrel[facing=up,open=false]")
    C.put(cx - 9, f, cz + 3, "coal_block")
    C.bp.spawner(cx + 4, f, cz + 8, MOB_GUNNER) if C.free(cx + 4, f, cz + 8) else None
    # vent stacks outside (magma glowing at their mouths)
    for (dx, dz, h) in ((-9, -9, 26), (9, -9, 24), (9, 9, 22)):
        x, z = cx + dx, cz + dz
        top = 0
        while (x, top + 1, z) in C.V:
            top += 1
        for y in range(top + 1, h):
            for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if C.get(x + ox, y, z + oz) is None:
                    C.set(x + ox, y, z + oz, BRASS if y % 5 == 0 else IRON_BR)
        for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            C.set(x + ox, h, z + oz, "magma_block")


def lift2(C):
    """The vault's bubble lift: soul sand under the vault floor, a bubble column up through the vault and the rock
    into the reactor room floor; a door on the vault side."""
    lx, lz = LIFT2
    C.force(lx, AF - 2, lz, "soul_sand")
    for y in range(AF - 1, 1):
        C.force(lx, y, lz, "bubble_column[drag=false]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if not (dx or dz):
                    continue
                p = (lx + dx, y, lz + dz)
                if y == 0:
                    if C.get(*p) in (None, AIR):
                        C.force(*p, TREAD)
                    continue
                if p in C.inner:
                    C.force(*p, GLASS if (dx == 0 or dz == 0) and y % 4 else BRASS)
                elif p not in C.shell:
                    C.force(*p, IRON_BR)
    C.force(lx, AF - 1, lz - 1, BRASS)
    water_gate(C, lx, lz - 1, AF, "north")
    C.force(lx, AF + 2, lz - 1, BRASS)
    # the top: rails round the column mouth in the reactor room
    C.put(lx - 1, 1, lz - 1, IRON_WALL)
    C.put(lx + 1, 1, lz - 1, IRON_WALL)


# ------------------------------------------------------------------ the drill control room
def control(C):
    cx, cz, R, dh, H = D_D
    f = 1
    # consoles facing east (the rig and the trench): a curved desk of levers, gauges, lecterns
    for z in range(cz - 4, cz + 5):
        x = cx + 5 - (abs(z - cz) // 3)
        if abs(z - cz) <= 1:
            continue
        C.put(x, f, z, IRON if z % 2 else TREAD_SLAB + "[type=top,waterlogged=false]")
        if C.free(x, f + 1, z):
            C.set(x, f + 1, z, GAUGE if z % 3 == 0 else (
                "lever[face=floor,facing=east,powered=false]" if z % 3 == 1 else "lectern[facing=west,has_book=false,"
                                                                                 "powered=false]"))
    C.put(cx + 3, f, cz - 3, CHAIR + "[facing=east]")
    # the depth gauge column, the seismograph, the chart table
    for y in range(f, dh + 2):
        C.put(cx - 3, y, cz - 4, PIPES if y % 3 else GAUGE)
    C.put(cx - 4, f, cz + 3, TABLE)
    C.put(cx - 5, f, cz + 3, CHAIR + "[facing=east]")
    C.put(cx - 2, f, cz + 5, "note_block[instrument=bass,note=3,powered=false]")
    C.put(cx - 1, f, cz + 5, "jukebox[has_record=false]")
    C.bp.chest(cx - 5, f, cz - 3, "east", loot=LOOT + "abs_control")
    C.set(cx, dh + 3, cz, CHANDELIER) if C.free(cx, dh + 3, cz) else None
    t = dh + 4
    while C.free(cx, t, cz):
        C.set(cx, t, cz, CHAIN)
        t += 1
    C.bp.spawner(cx - 2, f, cz - 6, MOB_DRONE) if C.free(cx - 2, f, cz - 6) else None


def hatch(C):
    """The one-way pressure hatch at the great-dome end of the control room's west tube: a bulkhead across the tube
    with an iron door; its lever only on the control-room (north) side."""
    zb = -20
    for x in (6, 7, 8, 9, 10):
        for y in range(1, 5):
            if (x, y, zb) in C.inner:
                C.set(x, y, zb, IRON_BR if (x + y) % 3 else BRASS)
    C.force(8, 1, zb, "iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    C.force(8, 2, zb, "iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    C.force(9, 2, zb - 1, "lever[face=wall,facing=north,powered=false]")


# ------------------------------------------------------------------ the drill shaft, the grace, the arena, the vault
def shaft(C):
    sx, sz = SH
    ring = [(x, z) for x in range(sx - 5, sx + 6) for z in range(sz - 5, sz + 6)
            if max(abs(x - sx), abs(z - sz)) >= 2]
    # the core: an iron column with lamps
    for y in range(SH_BOT, 9):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                p = (sx + dx, y, sz + dz)
                if p in C.inner:
                    C.set(*p, SEA_L if (dx == 0 and dz == 0) else (BRASS if (y - SH_BOT) % 6 == 0 else IRON))
    helix(C, sx, sz, ring, SH_TOP, SH_BOT, 8, math.pi, -1)
    # the grace: the bottom landing (east and north of the core), the waystone, benches, a chest
    C.set(sx + 4, SH_BOT, sz + 1, MOD["waystone"])
    C.put(sx + 4, SH_BOT, sz + 2, "candle[candles=3,lit=true,waterlogged=false]")
    C.put(sx + 4, SH_BOT, sz - 3, stair(MAHOGANY_STAIRS, "west"))
    C.put(sx + 3, SH_BOT, sz - 4, stair(MAHOGANY_STAIRS, "south"))
    for y in range(SH_BOT + 3, 8, 6):
        for (dx, dz) in ((6, 3), (-6, -3), (3, -6), (-3, 6), (6, -3), (-6, 3), (-3, -6), (3, 6)):
            p = (sx + dx, y, sz + dz)
            if p in C.shell:
                C.set(*p, SEA_L)
    C.bp.chest(sx - 5, SH_BOT, sz - 4, "east", loot=LOOT + "abs_shaft")
    C.bp.spawner(sx, SH_BOT, sz - 5, MOB_CRAWLER) if C.free(sx, SH_BOT, sz - 5) else None
    # the corridor to the arena: ribs, lamps, the mist at its far end
    for z in range(-38, -24, 4):
        for x in (67, 69):
            if C.free(x, AF + 3, z):
                C.set(x, AF + 3, z, EDISON)
    C.bp.mist(67, AF, -24, 69, AF + 3, -23)


def arena(C):
    ax, az, R = AC
    f = AF
    # the drill string: through the skylight dome into the chamber, the bit hanging over the borehole
    top = A_WALL + A_RISE
    for y in range(f + 9, top + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                p = (ax + dx, y, az + dz)
                if p in C.inner or p in C.shell:
                    C.force(*p, BRASS if (y % 4 == 0 and (dx or dz)) else IRON)
    for k, y in enumerate(range(f + 8, f + 4, -1)):
        r = 3.2 - k * 0.8
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if math.hypot(dx, dz) < r and C.free(ax + dx, y, az + dz):
                    C.set(ax + dx, y, az + dz, "polished_blackstone" if (dx + dz + y) % 2 else IRON)
    C.set(ax, f + 4, az, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]") if \
        C.free(ax, f + 4, az) else None
    # the borehole under it: glowing glass over magma
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3:
                C.force(ax + dx, f - 1, az + dz, "magma_block" if (dx + dz) % 2 else "shroomlight")
    # four hydraulic struts from the walls to the drill collar, consoles, ore spoil heaps at the wall
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        for t in range(0, 12):
            x = int(round(ax + math.cos(a) * (15 - t)))
            z = int(round(az + math.sin(a) * (15 - t)))
            y = f + 2 + int(t * 0.55)
            if C.free(x, y, z) and math.hypot(x - ax, z - az) > 4:
                C.set(x, y, z, IRON if t % 3 else BRASS)
    for k in range(10):
        a = k * math.pi / 5 + 0.2
        x, z = int(round(ax + math.cos(a) * 15.2)), int(round(az + math.sin(a) * 15.2))
        if k % 2 == 0:
            for (ox, oz) in ((0, 0), (1, 0), (0, 1)):
                for y in range(f, f + 1 + int(hash01(x + ox, z + oz, 111) * 2)):
                    C.put(x + ox, y, z + oz, pick([("gravel", 3), ("raw_copper_block", 1), ("deepslate_copper_ore", 2),
                                                   ("cobbled_deepslate", 3)], x + ox, y, z + oz, 112))
        elif C.free(x, f + 3, z):
            C.set(x, f + 3, z, SEA_L)
    for y in (f + 7, f + 10):
        for k in range(12):
            a = k * math.pi / 6 + math.pi / 12
            x, z = int(round(ax + math.cos(a) * 16.2)), int(round(az + math.sin(a) * 16.2))
            if C.free(x, y, z):
                C.set(x, y, z, EDISON)
    C.bp.boss_seal(ax + 6, f - 1, az, BOSS, 18)


def vault(C):
    vx0, vx1, vz0, vz1 = VAULT
    f = AF
    # the sealed bars across the passage from the arena
    for z in range(-9, -6):
        for y in range(f, f + 4):
            if (54, y, z) in C.inner:
                C.set(54, y, z, MOD["vault_bars"])
    # specimen jars (glass tanks with sea pickles and coral), the treasure chests, shelves, lamps
    for x in (vx0 + 2, vx0 + 5, vx0 + 8):
        for y in range(f, f + 3):
            C.put(x, y, vz0 + 2, GLASS if y > f else BRASS)
    for x in range(vx0 + 2, vx1 - 3, 2):
        C.put(x, f, vz0 + 1, "bookshelf")
        C.put(x + 1, f, vz0 + 1, "chiseled_bookshelf[facing=south,slot_0_occupied=false,slot_1_occupied=false,"
                                  "slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,"
                                  "slot_5_occupied=false]")
    C.bp.chest(vx0 + 1, f, -8, "east", loot=LOOT + "abs_vault")
    C.bp.chest(vx0 + 1, f, -6, "east", loot=LOOT + "abs_vault")
    C.put(vx0 + 1, f, -7, "gold_block")
    C.put(vx0 + 1, f + 1, -7, "conduit[waterlogged=false]")
    C.put(vx0 + 3, f, -10, TABLE)
    for (x, z) in ((vx0 + 3, -7), (vx1 - 3, -11), (vx1 - 4, -4)):
        if C.free(x, f + 4, z):
            C.set(x, f + 4, z, LANT_H)


# ------------------------------------------------------------------ whale-fall deck, flooded tube
def whale_deck(C):
    cx, cz, R, dh, H = W_D
    f = 1
    for (x, z, fc) in ((cx + 3, cz + 2, "east"), (cx + 3, cz - 2, "east"), (cx - 1, cz + 4, "south"),
                       (cx + 1, cz + 4, "south")):
        C.put(x, f, z, stair(MAHOGANY_STAIRS, OPP[fc]))
    C.put(cx + 4, f, cz, IRON_WALL)
    C.put(cx + 4, f + 1, cz, "lightning_rod[facing=east,powered=false,waterlogged=false]")
    C.bp.chest(cx - 4, f, cz + 2, "east", loot=LOOT + "abs_whale")
    C.put(cx - 4, f, cz - 2, "lectern[facing=east,has_book=false,powered=false]")
    C.put(cx, f + 5, cz, LANT_H) if C.free(cx, f + 5, cz) else None
    t = f + 6
    while C.free(cx, t, cz):
        C.set(cx, t, cz, CHAIN)
        t += 1


def flooded_tube(C):
    """The flooded maintenance tube from the lock (x 9) to the whale deck (x 33) along z 52: its own hull (water
    inside), doors at both ends in the dry hulls, a conduit in a prismarine ring halfway."""
    zc = 52
    x0, x1 = 10, 33
    cells = tube_cells("x", x0, x1, zc, h=4, chamfer=False)
    cells = {p for p in cells if p not in C.V}
    for p in cells:
        x, y, z = p
        bound = any((x + dx, y + dy, z + dz) not in cells and (x + dx, y + dy, z + dz) not in C.V
                    for dx, dy, dz in N6)
        if bound:
            C.force(*p, IRON if (x % 6 == 0 or y <= 1) else (VERD if hash3(x, y, z, 131) < 0.3 else COPPER))
        else:
            C.force(*p, WATER)
            C.wet.add(p)
    # the conduit ring halfway
    xm = (x0 + x1) // 2
    for w in range(-2, 3):
        for y in range(0, 5):
            if abs(w) == 2 or y in (0, 4):
                C.force(xm, y, zc + w, "sea_lantern" if (abs(w) == 2 and y in (0, 4)) else "prismarine_bricks")
    C.force(xm, 2, zc, "conduit[waterlogged=true]")
    # kelp and sea pickles in the tube, a lamp-chain of sea lanterns in its roof
    for x in range(x0 + 2, x1 - 1, 5):
        if abs(x - xm) > 2:
            C.force(x, 1, zc - 1, "sea_pickle[pickles=3,waterlogged=true]")
    # the doors (the dry hulls' walls at x 9 and x 33)
    for x, fc in ((9, "east"), (34, "west")):
        water_gate(C, x, zc, 1, fc)
    C.bp.chest(8, 1, 50, "west", loot=LOOT + "abs_tube")


# ------------------------------------------------------------------ outside: trench, rig, whale, kelp, lights
def trench(C):
    rock = []
    for z in range(-92, 75):
        cx = trench_cx(z)
        for x in range(int(cx - 14), int(cx + 15)):
            b = trench_bottom(x, z)
            if b is None:
                continue
            for y in range(b, 5):
                p = (x, y, z)
                if p in C.V or C.get(*p) is not None:
                    continue
                C.force(x, y, z, WATER)
            # the floor: gravel, magma vents, glowing pickles and dead coral
            fl = (x, b - 1, z)
            if fl not in C.V and C.get(*fl) is None:
                h = hash01(x, z, 141)
                C.force(*fl, "magma_block" if h < 0.03 else ("gravel" if h < 0.55 else "tuff"))
                if 0.55 < h < 0.6 and C.get(x, b, z) == "minecraft:water":
                    C.force(x, b, z, "sea_pickle[pickles=%d,waterlogged=true]" % (1 + int(h * 100) % 4))
                elif 0.6 < h < 0.63 and C.get(x, b, z) == "minecraft:water":
                    C.force(x, b, z, "dead_tube_coral_fan[waterlogged=true]")
            rock.append((x, z, b))
    # the walls: strata of deepslate, tuff and basalt where the cut meets the sea floor
    have = {(x, z) for x, z, _ in rock}
    for (x, z, b) in rock:
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in have:
                continue
            nb = b
            for y in range(nb, 1):
                p = (n[0], y, n[1])
                if p in C.V or C.get(*p) is not None:
                    continue
                yy = y + (fbm(n[0] * 0.5, n[1] * 0.5, 4.0, 145) - 0.5) * 4
                s = ("deepslate", "tuff", "deepslate", "basalt[axis=y]", "cobbled_deepslate")[int(-yy // 4) % 5]
                C.force(*p, s)
                if hash3(*p, 146) < 0.04:
                    C.force(*p, "deepslate_copper_ore")


def rig(C):
    """The drilling rig over the trench: a deck on four lattice legs, the derrick tapering to its crown block, the
    drill string down to the chamber's skylight, the rotary table, pipe racks, searchlights."""
    x0, x1, z0, z1, y = RIG
    ax, az, _ = AC
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if abs(x - ax) <= 1 and abs(z - az) <= 1:
                continue
            C.set(x, y, z, IRON if edge else (TREAD if (x + z) % 4 else BRASS))
            if edge and (x + z) % 2 == 0:
                C.set(x, y + 1, z, IRON_WALL)
    for (lx, lz) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1), (x0, az), (x1, az)):
        b = trench_bottom(lx, lz)
        yb = (b if b is not None else 0)
        for yy in range(yb, y):
            for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                px, pz = lx + (ox if lx == x0 else -ox), lz + (oz if lz == z0 else -oz)
                if (ox + oz) % 2 == 0 or yy % 4 == 0:
                    C.force(px, yy, pz, IRON if yy % 4 else BRASS)
        for yy in range(yb - 3, yb):
            C.force(lx, yy, lz, IRON_BR)
    # the derrick: a square lattice tapering from 13 to 3 between the deck and y 40; the legs step inward with
    # overlapping cells (no diagonal gaps), a girder ring every 5, zig-zag braces between the rings
    ytop = 40

    def hw_at(yy):
        return int(round(6 - 5 * (yy - y) / (ytop - y)))
    prev = 6
    for yy in range(y + 1, ytop + 1):
        hw = hw_at(yy)
        for (sx, sz) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            C.set(ax + sx * hw, yy, az + sz * hw, IRON if yy % 5 else BRASS)
            if hw != prev:
                C.set(ax + sx * prev, yy, az + sz * prev, IRON)
                C.set(ax + sx * hw, yy, az + sz * prev, IRON)
                C.set(ax + sx * prev, yy, az + sz * hw, IRON)
        prev = hw
        if yy % 5 == 0:
            for k in range(-hw, hw + 1):
                for (px, pz) in ((ax + k, az - hw), (ax + k, az + hw), (ax - hw, az + k), (ax + hw, az + k)):
                    C.set(px, yy, pz, IRON_WALL if abs(k) < hw else BRASS)
    for y0 in range(y + 5, ytop - 4, 5):
        h0, h1 = hw_at(y0), hw_at(y0 + 5)
        bay = (y0 - y) // 5
        for side in (-1, 1):
            # one diagonal per face per bay, alternating (a zig-zag lattice that reads open from afar)
            for (a0, a1) in (((-h0, h1),) if (bay + (side > 0)) % 2 else ((h0, -h1),)):
                n = 3 * abs(a1 - a0) + 5
                for t in range(1, n):
                    u = int(round(a0 + (a1 - a0) * t / n))
                    w = int(round(h0 + (h1 - h0) * t / n))
                    yy = y0 + int(round(5 * t / n))
                    C.set(ax + u, yy, az + side * w, IRON_WALL)
                    C.set(ax + side * w, yy, az + u, IRON_WALL)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            C.set(ax + dx, ytop + 1, az + dz, BRASS)
    C.set(ax, ytop + 2, az, GEAR)
    C.set(ax, ytop + 3, az, SEA_L)
    C.set(ax, ytop + 4, az, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the travelling block and the drill string to the chamber
    for yy in range(y + 4, ytop + 1):
        C.set(ax, yy, az, CHAIN)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            C.set(ax + dx, y + 3, az + dz, BRASS if dx or dz else IRON)
    top = A_WALL + A_RISE
    for yy in range(top + 1, y + 3):
        C.set(ax, yy, az, IRON if yy % 6 else BRASS)
        if yy % 6 == 0:
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if C.get(ax + dx, yy, az + dz) in (None, "minecraft:water"):
                    C.force(ax + dx, yy, az + dz, BRASS)
    # the rotary table and the draw-works on the deck, pipe racks, a winch house
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) == 2 or abs(dz) == 2:
                C.set(ax + dx, y + 1, az + dz, GEAR if (dx + dz) % 2 else BRASS)
    for x in range(x0 + 2, x0 + 9):
        for zz in (z0 + 2, z0 + 3):
            C.set(x, y + 1, zz, PIPES)
    for x in range(x1 - 6, x1 - 1):
        for zz in range(z1 - 6, z1 - 1):
            edge = x in (x1 - 6, x1 - 2) or zz in (z1 - 6, z1 - 2)
            for yy in range(y + 1, y + 5):
                if edge:
                    C.set(x, yy, zz, IRON if yy < y + 4 else BRASS)
            C.set(x, y + 5, zz, IRON_SLAB + "[type=bottom,waterlogged=false]")
    for yy in (y + 1, y + 2):
        C.force(x1 - 4, yy, z1 - 6, "spruce_door[facing=north,half=%s,hinge=left,open=false,powered=false]" %
                ("lower" if yy == y + 1 else "upper"))
    # searchlights on the derrick and the deck corners
    for (x, yy, z) in ((x0, y + 2, z0), (x1, y + 2, z0), (x0, y + 2, z1), (x1, y + 2, z1)):
        C.set(x, yy, z, SEA_L)
    for yy in (y + 10, y + 20):
        hw = int(round(6 - 5 * (yy - y) / (ytop - y)))
        C.set(ax + hw, yy, az, SEA_L)
        C.set(ax - hw, yy, az, SEA_L)


def whale(C):
    """The whale fall: a 40-long skeleton on the trench lip, its tail slipping over the edge."""
    z0 = 66
    for x in range(44, 86):
        b = trench_bottom(x, z0)
        ys = 1 if b is None else max(b + 2, 1 - (x - 62) // 2)
        if x > 84:
            ys = 1
        for dz in (0,):
            C.set(x, ys, z0 + dz, "bone_block[axis=x]")
        if x % 3 == 0 and x < 74:
            r = 6 if x < 66 else 4
            for k in range(0, 37):
                a = math.pi * k / 36.0
                dz = int(round(math.cos(a) * r))
                dy = int(round(math.sin(a) * r * 0.8))
                p = (x, ys + dy, z0 + dz)
                if p not in C.V and C.get(*p) in (None, "minecraft:water"):
                    C.set(*p, "bone_block[axis=y]")
    # the skull at the west end and two flippers
    for dx in range(-6, 0):
        for dz in range(-2, 3):
            for dy in range(0, 3):
                if abs(dz) + dy <= 3 - (dx + 6) // 3:
                    C.set(44 + dx, 1 + dy, z0 + dz, "bone_block[axis=x]")
    for (x, dz) in ((52, -7), (52, 7), (53, -8), (53, 8)):
        C.set(x, 1, z0 + dz, "bone_block[axis=z]")
    for x in range(42, 70, 3):
        for dz in (-4, 4):
            if C.get(x, 1, z0 + dz) is None:
                C.set(x, 1, z0 + dz, "sea_pickle[pickles=2,waterlogged=true]")


def kelp_farms(C):
    """Two kelp farms in brass frames: rows on sand beds, posts with sea-lantern caps, a harvester gantry."""
    for (x0, x1, z0, z1) in ((-90, -62, -24, 28), (-34, -16, 58, 84)):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if C.get(x, 0, z) is not None:
                    continue
                row = (x - x0) % 3
                if row == 0:
                    C.force(x, 0, z, "sand")
                    for y in (-1, -2):
                        if C.get(x, y, z) is None:
                            C.force(x, y, z, "sandstone")
                    h = 4 + int(hash01(x, z, 151) * 10)
                    for y in range(1, h):
                        C.force(x, y, z, "kelp_plant")
                    C.force(x, h, z, "kelp[age=25]")
                else:
                    C.force(x, 0, z, "gravel" if row == 1 else "sand")
        for x in range(x0, x1 + 1, 6):
            for z in (z0 - 1, z1 + 1):
                for y in range(0, 7):
                    C.set(x, y, z, IRON if y < 6 else BRASS)
                C.set(x, 7, z, SEA_L)
        for z in range(z0 - 1, z1 + 2):
            for xx in (x0 - 1, x1 + 1):
                C.set(xx, 6, z, IRON if z % 6 else BRASS)
        # the harvester gantry across the middle
        zm = (z0 + z1) // 2
        for x in range(x0 - 1, x1 + 2):
            C.set(x, 16, zm, IRON if x % 4 else BRASS)
        for y in range(0, 16):
            C.set(x0 - 1, y, zm, IRON)
            C.set(x1 + 1, y, zm, IRON)
        C.set((x0 + x1) // 2, 15, zm, GEAR)
        C.set((x0 + x1) // 2, 14, zm, CHAIN)
        C.set((x0 + x1) // 2, 13, zm, "hopper[enabled=true,facing=down]")


def searchlight(C, x, z, h, face):
    """A searchlight on a post: an iron post, a brass housing with its lens turned outward."""
    for y in range(0, h):
        C.set(x, y, z, IRON if y else IRON_BR)
    C.set(x, h, z, BRASS)
    dx, dz = DIRS[face]
    C.set(x + dx, h, z + dz, SEA_L)
    C.set(x - dx, h, z - dz, IRON)
    C.set(x, h + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]")


def outside(C):
    for (x, z, h, fc) in ((-26, 22, 6, "south"), (24, 24, 7, "east"), (-28, -28, 6, "north"), (22, -26, 5, "east"),
                          (-60, 18, 5, "west"), (-70, -46, 6, "north"), (56, 30, 6, "east"), (20, 44, 5, "south"),
                          (-20, 70, 6, "south"), (56, -60, 7, "north"), (-62, 52, 5, "west")):
        if C.get(x, 0, z) is None or C.get(x, 0, z) in ("minecraft:sand", "minecraft:gravel", "minecraft:clay"):
            searchlight(C, x, z, h, fc)
    # pipes along the sea floor between the modules
    for (a, b, c, axis) in ((-34, -20, 8, "x"), (20, 32, -8, "x"), (-40, -16, 60, "z"), (14, 30, 20, "z")):
        for u in range(a, b + 1):
            x, z = (u, c) if axis == "x" else (c, u)
            if C.get(x, 1, z) is None:
                C.set(x, 1, z, PIPES)
                C.set(x, 0, z, IRON) if C.get(x, 0, z) is None else None
    # a cable reel, crates and a spare bathyscaphe on the floor by the lock
    for (x, z) in ((14, 30), (15, 31), (-14, 32)):
        if C.get(x, 1, z) is None:
            C.set(x, 1, z, "barrel[facing=up,open=false]")
    for dx in range(-2, 3):
        for dy in range(0, 4):
            for dz in range(-2, 3):
                r = math.sqrt(dx * dx + (dy - 1.5) ** 2 + dz * dz)
                if r < 2.3:
                    p = (-16 + dx, 1 + dy, 26 + dz)
                    if C.get(*p) is None:
                        C.set(*p, GLASS if (dx == -2 and abs(dz) < 1 and dy in (1, 2)) else BRASS)
    C.set(-16, 5, 26, IRON_WALL)
    # the stair tower's foot: a weighted anchor and chain
    cx, cz = TOWER
    for y in range(1, 4):
        C.set(cx + 18, y, cz + 10, "iron_chain[axis=y,waterlogged=false]")


# ------------------------------------------------------------------ final passes
PLAIN_FLOOR = {TREAD, PARQUET, IRON, IRON_BR, "minecraft:prismarine_bricks"}


def lighting(C, rounds=4):
    """Light 8 on every interior floor: a sea lantern set into the floor (or a lamp hung from a solid ceiling)."""
    bp = C.bp
    for r in range(rounds):
        L, origin, trans = light_map(bp)
        dark = [p for p in dark_floors(bp, L, origin, trans) if p in C.inner]
        if not dark:
            break
        dark.sort()
        placed = []
        for (x, y, z) in dark:
            if any(abs(x - a) + abs(y - b) + abs(z - c) < 5 for (a, b, c) in placed):
                continue
            fb = bp.get(x, y - 1, z)
            if fb in PLAIN_FLOOR:
                bp.set(x, y - 1, z, SEA_L)
                placed.append((x, y, z))
                continue
            t = y + 2
            while t < y + 10 and C.free(x, t, z):
                t += 1
            if bp.get(x, t, z) not in (None, AIR) and t - y >= 4 and C.free(x, t - 1, z):
                for yy in range(y + 3, t):
                    bp.set(x, yy, z, CHAIN)
                bp.set(x, y + 2, z, LANT_H) if C.free(x, y + 2, z) else None
                placed.append((x, y, z))
        if not placed:
            break


def waterlog_outside(C):
    """Outside the hull and below the lowest sea surface, waterloggable decorations are water-filled (the structure
    ignores the world's water when it is placed); never one that touches interior air."""
    B = C.bp.blocks
    for p, (name, props, data) in list(B.items()):
        if props.get("waterlogged") != "false" or p in C.V or p[1] > SEA_MIN:
            continue
        x, y, z = p
        if any((x + dx, y + dy, z + dz) in C.inner for dx, dy, dz in N6):
            continue
        B[p] = (name, dict(props, waterlogged="true"), data)


def drop_outside_air(C):
    for p, b in list(C.bp.blocks.items()):
        if b[0] == AIR and p not in C.inner:
            C.bp.remove(*p)


def abyssal_station(bp):
    C = Ctx(bp)
    build_hull(C)
    footings(C)
    tower_interior(C)
    deck(C)
    lock_room(C)
    great_dome(C)
    hydroponics(C)
    aquarium(C)
    crew(C)
    reactor(C)
    control(C)
    hatch(C)
    shaft(C)
    arena(C)
    vault(C)
    lift2(C)
    whale_deck(C)
    flooded_tube(C)
    trench(C)
    rig(C)
    whale(C)
    kelp_farms(C)
    outside(C)
    lighting(C)
    waterlog_outside(C)
    drop_outside_air(C)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("reception_lock", (0, 1, 52), (0, 3, 40)),
    ("concourse", (0, 1, 15), (0, 12, -10)),
    ("observation_floor", (-14, OBS, 6), (10, OBS + 2, -8)),
    ("hydroponics", (-38, 1, 0), (-50, 4, 0)),
    ("aquarium", (-34, 1, -45), (-58, 4, -45)),
    ("reactor", (36, 1, 0), (46, 5, 4)),
    ("drill_control", (34, 1, -44), (48, 3, -44)),
    ("arena", (72, AF, -22), (72, AF + 3, 6)),
]

_SDEF = StructureDef(
    "abyssal_station", "overworld", ["deep_ocean", "deep_cold_ocean", "deep_lukewarm_ocean"],
    [Piece("station", abyssal_station, views=VIEWS)],
    spacing=80, separation=32, heightmap="OCEAN_FLOOR_WG", adaptation="none", processors="none", max_distance=128,
    foundation=False, spawns=[(MOB_MARINE, 6, 1, 2), (MOB_CRAB, 3, 1, 2), (MOB_WRAITH, 2, 1, 1),
                              (MOB_CRAWLER, 2, 1, 1)],
    title_fr="La Station abyssale", title_en="The Abyssal Station")
# the hull's air pockets stand where the sea was: never fill a dry stair or lantern with that water
_SDEF.liquid_settings = "ignore_waterlogging"
register(_SDEF)

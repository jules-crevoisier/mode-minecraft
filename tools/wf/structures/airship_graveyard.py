"""The Airship Graveyard (Le Cimetière des dirigeables): a crash field ~215 blocks across in savanna or plains, where
a fleet of brass dirigibles came down round a ruined mooring tower. Colossal tier (tools/BUILDING.md §1, §12 concept
21, §10 legacy-dungeon template, §15), steampunk (tools/STYLE_STEAMPUNK.md: dark iron, brass and copper, canvas).

Silhouette (one noun phrase, §15.1): a skeletal lattice mast 90 high with a docking ring at its top, a long brass
dirigible still moored to it by the nose, its tail half deflated and draped over bare ribs, over a field of wrecks.

Layout, ground y = 0 (feet 1), x east, z south. The mast stands at (TX, TZ) on its winch house; the moored ship's
axis runs east from the docking ring at y AY = RW (ship coordinate u = x - NX from the nose, v = z - SZ across).
  * the approach (south-east): the salvagers' camp and its waystone at the field's edge, then the road walks through
    the bare envelope frame of a fallen ship lying like a whale skeleton (ship B), whose ribs frame the mast and the
    moored ship; the buried gondola (ship A) stands nose-down in the field to the east;
  * the shanty town of hull plates, gas-bag tents and propeller windmills, its market square (the hub, site of
    grace) under the moored ship's shadow; a street north to the winch house;
  * the winch house (feet 1 and 9, the mooring winch, the moorings master's office) and the gas works west of it
    (the retort house with its gallery and bridge, two gasometers in their guide frames): two independent ways up
    to the winch house roof (feet 17);
  * the mast: a square newel stair round the cargo-lift shaft, 60 up inside the lattice, a balcony half way (feet
    49), the mooring ring walkway at feet RW round the top, where the moored ship's nose is docked;
  * the moored ship: the docking vestibule in the nose, the nose stair down to the keel landing, the trunk stair
    down into the gondola: the bridge, the companion hall, the cabins (the captain's), the saloon with catwalks to
    the two engine nacelles; the aft stair down to the cargo hold; the climbing shaft (a newel stair) from the hold
    up through the gas cells to the site of grace and a narrow stair (compression) up into the deckhouse, the mist;
  * the boss: the open top deck of the moored ship (42 x 35); behind sealed bars at its west end, the gangway head,
    the stair down to the sealed treasury hold, and the gangway along the envelope's spine to the mast crown, where
    the cargo-lift shaft drops 95 blocks into the sump under the winch house (an iron door that opens from inside).
Optional: the broken ship (C) in two halves to the north-east with its gondola lying beside it (the salvagers'
den), the buried gondola's tilted interior, the mast balcony, the engine nacelles, the rigger's store.
Loot gradient (§15.6): camp, shanties, wrecks tier 1; market, winch house, den 1-2; gas works, mast, cabins, hold 2;
bridge, engines, captain, buried gondola 2-3; treasury 3+.
Height budget: the mast spire tops out at ~104, the deckhouse at ~100; the sump reaches 3 below the ground layer.
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, LEATHER, MAHOGANY, MAHOGANY_STAIRS, PIPES, SMOKE,
                       SMOKE_STAIRS, TABLE, TREAD, TREAD_SLAB, TREAD_STAIRS, VERD, W, fbm, hash01, hash3, lantern_post,
                       vnoise)
from ..parts import LOOT, MOD
from .caldera_ringwall import newel

# the graveyard's own boss: the Corsair Captain, the sky-pirate under her rotor, on the open top deck of the moored ship
BOSS = "brasshaven:corsair_captain"
MOB_RAIDER = W + "sky_raider"
MOB_DRONE = W + "steam_drone"
MOB_BANDIT = W + "bandit_marksman"
MOB_GUNNER = W + "boiler_gunner"
MOB_MITE = W + "rust_mite"

AIR = "minecraft:air"
WATER = "water[level=0]"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
IRON_BR = W + "dark_iron_bricks"
IRON_BR_ST = W + "dark_iron_brick_stairs"
RUST, RUST_BR, RUST_P = W + "rust_rock", W + "rust_rock_bricks", W + "polished_rust_rock"
SOOT = W + "sooty_smokestack_bricks"
PARQUET = W + "mahogany_parquet"
GRILLE = W + "brass_grille"
RAIL = W + "brass_railing"
VALVE = W + "valve_wheel"
COG = W + "wall_cog"
SHELF = W + "wall_shelf"
CHAIR = W + "mahogany_chair"
DOOR = "spruce"
GAS = "light_gray_wool"          # the gas cells filling the intact hull (never seen: rooms are lined)
CANVAS = ("white_wool", "white_wool", "light_gray_wool")
TENT = ("white_wool", "light_gray_wool", "brown_wool", "red_wool", "yellow_wool", "orange_wool")

# ------------------------------------------------------------------ dimensions
TX, TZ = -52, -15         # the mast's centre
TF = 17                   # winch house roof terrace feet: the mast stair starts here
RW = 77                   # mooring ring walkway feet
AY = RW                   # the moored ship's axis y
NX = TX + 12              # nose tip x: u = x - NX
SZ = TZ                   # the ship's axis z: v = z - SZ
R = 16                    # envelope radius
LEN = 140
INTACT = 96               # gas cells up to here; the aft deflated over its ribs
GU0, GU1 = 30, 86         # the gondola (u)
GW = 9                    # gondola outer half width
UPF, LOF = 54, 47         # gondola upper deck feet, cargo hold feet
KF = 67                   # keel landing feet
SH = (64, -4)             # climbing shaft newel origin (u, v), outer 10 x 10
GRF = 87                  # site of grace feet (the shaft's top)
DY = 94                   # top deck floor y (feet 95)
DU0, DU1, DV = 42, 94, 17  # top deck u range, half width
AC = (63, 0)              # arena centre (u, v)
TRF = 85                  # treasury feet
CRF = 93                  # mast crown feet
NAC_V = 20                # engine nacelles at v = +-20
NAC_Y = 56


def X(u):
    return NX + u


def Z(v):
    return SZ + v


class Ctx:
    def __init__(self, bp):
        self.bp = bp
        self.inner = set()     # air written on purpose
        self.gas = set()       # gas-cell fill of the intact hull

    def set(self, x, y, z, spec, data=None):
        self.bp.set(x, y, z, spec, data)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def air(self, x, y, z):
        self.bp.set(x, y, z, AIR)
        self.inner.add((x, y, z))
        self.gas.discard((x, y, z))

    def empty(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR

    def box(self, x0, x1, y0, y1, z0, z1, spec):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(y0, y1 + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, spec(x, y, z) if callable(spec) else spec)

    def clear(self, x0, x1, y0, y1, z0, z1):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(y0, y1 + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.air(x, y, z)


def rail(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def lamp_hang(C, x, y, z, drop=1, spec=HANG_LAMP):
    for k in range(drop):
        C.set(x, y + 1 + k, z, CHAIN)
    C.set(x, y, z, spec)


def door(C, x, y, z, facing, wood=DOOR, hinge="left"):
    C.bp.door(x, y, z, facing, wood=wood, hinge=hinge)


def plate(x, y, z, seed=0):
    """Patchwork hull plates (2 x 2 patches): dark iron, copper, verdigris, rust."""
    n = hash01(x // 2 * 7 + y // 2 * 131, z // 2 * 13 - y // 2, seed)
    if n < 0.42:
        return IRON
    if n < 0.6:
        return COPPER
    if n < 0.72:
        return VERD
    if n < 0.86:
        return RUST
    return IRON_BR


def canvas(x, y, z, low=0.0):
    n = fbm(x * 0.7 + z * 0.3, y * 0.9 + z * 0.2, 6.0, 811)
    if n + low < 0.32:
        return "brown_wool"
    if n + low < 0.48:
        return "light_gray_wool"
    return "white_wool"


# ------------------------------------------------------------------ rigid transforms for the wrecks
class Frame:
    """Local (u forward, v right, h up) <-> world, for a body at ``o`` with yaw (degrees from +x towards +z),
    pitch (nose up, degrees) and roll (degrees)."""

    def __init__(self, o, yaw, pitch=0.0, roll=0.0):
        self.o = o
        a, p, r = math.radians(yaw), math.radians(pitch), math.radians(roll)
        f = (math.cos(a), 0.0, math.sin(a))
        rt = (-math.sin(a), 0.0, math.cos(a))
        up = (0.0, 1.0, 0.0)
        fp = tuple(f[i] * math.cos(p) + up[i] * math.sin(p) for i in range(3))
        upp = tuple(up[i] * math.cos(p) - f[i] * math.sin(p) for i in range(3))
        self.f = fp
        self.r = tuple(rt[i] * math.cos(r) + upp[i] * math.sin(r) for i in range(3))
        self.u = tuple(upp[i] * math.cos(r) - rt[i] * math.sin(r) for i in range(3))

    def world(self, u, v, h):
        return tuple(self.o[i] + u * self.f[i] + v * self.r[i] + h * self.u[i] for i in range(3))

    def local(self, x, y, z):
        d = (x - self.o[0], y - self.o[1], z - self.o[2])
        return (sum(d[i] * self.f[i] for i in range(3)), sum(d[i] * self.r[i] for i in range(3)),
                sum(d[i] * self.u[i] for i in range(3)))

    def iworld(self, u, v, h):
        return tuple(int(round(c)) for c in self.world(u, v, h))


def raster(C, F, box, fn, ymin=0):
    """Write fn(u, v, h, x, y, z) over the world cells covering the local box (u0, u1, v0, v1, h0, h1)."""
    u0, u1, v0, v1, h0, h1 = box
    pts = [F.world(u, v, h) for u in (u0, u1) for v in (v0, v1) for h in (h0, h1)]
    lo = [int(math.floor(min(p[i] for p in pts))) - 1 for i in range(3)]
    hi = [int(math.ceil(max(p[i] for p in pts))) + 1 for i in range(3)]
    for x in range(lo[0], hi[0] + 1):
        for y in range(max(lo[1], ymin), hi[1] + 1):
            for z in range(lo[2], hi[2] + 1):
                u, v, h = F.local(x, y, z)
                if u0 <= u <= u1 and v0 <= v <= v1 and h0 <= h <= h1:
                    s = fn(u, v, h, x, y, z)
                    if s:
                        if s == AIR:
                            C.air(x, y, z)
                        else:
                            C.set(x, y, z, s)


# ------------------------------------------------------------------ the ground
def field_e(x, z):
    return ((x - 3) / 113.0) ** 2 + ((z + 3) / 101.0) ** 2


def ground(C):
    for x in range(-114, 120):
        for z in range(-106, 101):
            e = field_e(x, z)
            if e > 1.0 + (fbm(x, z, 14.0, 21) - 0.5) * 0.14:
                continue
            n = fbm(x, z, 9.0, 23)
            h = hash01(x, z, 24)
            top = ("coarse_dirt" if n > 0.66 else "rooted_dirt" if n < 0.2 and h < 0.3 else
                   "podzol[snowy=false]" if n < 0.26 else "grass_block[snowy=false]")
            C.set(x, 0, z, top)
            C.set(x, -1, z, "dirt")
            if e < 0.8:
                C.set(x, -2, z, "dirt" if h < 0.8 else "coarse_dirt")


def path_line(C, pts, half=1.7, seed=31):
    """A trodden track: dirt path and gravel, slightly wandering, cleared 3 high."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 2))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            w = half + (vnoise(px, pz, 5.0, seed) - 0.5) * 1.0
            for x in range(int(px) - 3, int(px) + 4):
                for z in range(int(pz) - 3, int(pz) + 4):
                    if math.hypot(x - px, z - pz) > w:
                        continue
                    b = C.get(x, 0, z)
                    if b is None or "grass" in b or "dirt" in b or "podzol" in b:
                        hh = hash01(x, z, seed + 1)
                        C.set(x, 0, z, "dirt_path" if hh < 0.62 else "gravel" if hh < 0.8 else "coarse_dirt")
                        for y in (1, 2):
                            if C.get(x, y, z) is None:
                                C.air(x, y, z)


def scar(C, pts, half=4.0, seed=41):
    """A crash furrow: churned earth, gravel and torn plates along the line the wreck slid."""
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, bz - az)
        n = max(1, int(seg * 1.5))
        for i in range(n + 1):
            t = i / n
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            w = half * (0.6 + 0.4 * t) + (vnoise(px, pz, 4.0, seed) - 0.5) * 2
            for x in range(int(px - w) - 1, int(px + w) + 2):
                for z in range(int(pz - w) - 1, int(pz + w) + 2):
                    if math.hypot(x - px, z - pz) > w:
                        continue
                    hh = hash01(x, z, seed + 2)
                    b = C.get(x, 0, z)
                    if b is None or b == AIR or "grass" in b or "podzol" in b or "rooted" in b:
                        C.set(x, 0, z, "coarse_dirt" if hh < 0.45 else "gravel" if hh < 0.7 else
                              "rooted_dirt" if hh < 0.85 else "dirt")
                    if hh > 0.975 and C.get(x, 1, z) is None:
                        C.set(x, 1, z, (IRON_SLAB + "[type=bottom,waterlogged=false]", RUST, COPPER,
                                        BRASS_SLAB + "[type=bottom,waterlogged=false]")[int(hh * 1000) % 4])


def debris(C, cx, cz, r, n, seed):
    """Scattered plates, girders and gas-cell rags round a wreck."""
    for i in range(n):
        a = hash01(i, seed, 51) * math.tau
        d = r * math.sqrt(hash01(i, seed, 52))
        x, z = int(round(cx + math.cos(a) * d)), int(round(cz + math.sin(a) * d))
        if not C.empty(x, 1, z) or C.get(x, 0, z) in (None, AIR):
            continue
        k = int(hash01(i, seed, 53) * 7)
        if k == 0:                       # a girder lying in the grass
            ax = "x" if hash01(i, seed, 54) < 0.5 else "z"
            ln = 3 + int(hash01(i, seed, 55) * 5)
            for j in range(ln):
                xx, zz = (x + j, z) if ax == "x" else (x, z + j)
                if C.empty(xx, 1, zz) and C.get(xx, 0, zz) not in (None, AIR):
                    C.set(xx, 1, zz, IRON_WALL if j % 3 else BRASS)
        elif k == 1:
            C.set(x, 1, z, canvas(x, 1, z) if hash01(i, seed, 56) < 0.5 else "white_carpet")
        elif k == 2:
            C.set(x, 1, z, f"{IRON_STAIRS}[facing={('north', 'south', 'east', 'west')[i % 4]},half=bottom,"
                           f"shape=straight,waterlogged=false]")
        elif k == 3:
            C.set(x, 1, z, RUST)
        elif k == 4:
            C.set(x, 1, z, "iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        elif k == 5:
            C.set(x, 1, z, BRASS_SLAB + "[type=bottom,waterlogged=false]")
        else:
            C.set(x, 1, z, GEAR)


def propeller(C, x, y, z, axis, r=4, blade=BRASS, hub=GEAR, turn=0):
    """A four-bladed propeller in the plane across ``axis`` ("x": blades in the z-y plane)."""
    C.set(x, y, z, hub)
    for k in range(4):
        a = math.radians(45 * (turn % 2) + 90 * k)
        for s in range(1, r + 1):
            du = int(round(math.cos(a) * s))
            dy = int(round(math.sin(a) * s))
            if axis == "x":
                C.set(x, y + dy, z + du, blade if s < r else COPPER)
            else:
                C.set(x + du, y + dy, z, blade if s < r else COPPER)


def windmill(C, x, z, h, facing_axis="x", seed=0):
    """A salvaged propeller on a pole: the shanty town's windmills."""
    for y in range(1, h):
        C.set(x, y, z, IRON_WALL if y % 4 else BRASS)
    C.set(x, h, z, IRON)
    if facing_axis == "x":
        C.set(x + 1, h, z, GEAR)
        propeller(C, x + 2, h, z, "x", r=3, turn=seed)
    else:
        C.set(x, h, z + 1, GEAR)
        propeller(C, x, h, z + 2, "z", r=3, turn=seed)


# ------------------------------------------------------------------ stairs
def write_steps(C, cells, tread=TREAD_STAIRS, floor=TREAD, fill=IRON, clear=4, solid_to=None):
    """cells: {(x, z): (feet, ascending facing or None)}: headroom, treads 2 thick (solid down to ``solid_to``)."""
    for (x, z), (f, fc) in cells.items():
        for y in range(f, f + clear):
            C.air(x, y, z)
    for (x, z), (f, fc) in cells.items():
        C.set(x, f - 1, z, stair(tread, fc) if fc else floor)
        lo = f - 2 if solid_to is None else min(solid_to, f - 2)
        for y in range(lo, f - 1):
            C.set(x, y, z, fill)
            C.gas.discard((x, y, z))
        C.gas.discard((x, f - 1, z))


def run_x(cells, u0, u1, v0, v1, f_of_u, asc):
    """Straight flight along x (ship u): feet per u, ascending towards ``asc`` (east/west); landings where the
    feet do not change."""
    for u in range(u0, u1 + 1):
        f, step = f_of_u(u)
        for v in range(v0, v1 + 1):
            cells[(X(u), Z(v))] = (f, asc if step else None)


def newel_write(C, cells, core, f0, fill=IRON, solid_first=False, rails=None):
    for (x, z), (f, fc, _) in cells.items():
        for y in range(f, f + 4):
            C.air(x, y, z)
    for (x, z), (f, fc, _) in cells.items():
        C.set(x, f - 1, z, stair(TREAD_STAIRS, fc) if fc else TREAD)
        C.gas.discard((x, f - 1, z))
        lo = f0 - 1 if (solid_first and f - 2 - f0 < 4) else f - 2
        for y in range(lo, f - 1):
            C.set(x, y, z, fill)
            C.gas.discard((x, y, z))
        if rails and rails(x, z):
            dx, dz = rails(x, z)
            rail(C, x, f, z, {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(dx, dz)])


def newel_laps(C, x0, z0, k, f0, flights, start, **kw):
    c, f = start, f0
    out = []
    for i in range(0, len(flights), 3):
        cells, core, c, f1 = newel(x0, z0, k, f, flights[i:i + 3], c)
        newel_write(C, cells, core, f0 if i == 0 else f, solid_first=(i == 0 and kw.get("solid_first", False)),
                    rails=kw.get("rails"))
        out.append(cells)
        f = f1
    return out, core, c, f


# ------------------------------------------------------------------ the moored ship: envelope
def env_r(u):
    if u < 0:
        return 0.0
    if u < 24:
        return R * math.sqrt(max(0.0, 1 - ((24 - u) / 24.0) ** 2))
    if u <= INTACT:
        return float(R)
    t = (u - INTACT) / float(LEN - INTACT)
    return R * (1 - 0.6 * t ** 1.3)


def skin_spec(u, v, h, x, y, z):
    """The forward envelope's skin: canvas above, brass plating on the belly, brass longitudinals every 22.5
    degrees, dark iron ring girders every 8, soot below the engine line."""
    th = math.atan2(h, v)
    d = math.hypot(v, h)
    step = math.pi / 8
    arc = d * abs(((th + step / 2) % step) - step / 2)
    if arc < 0.55 and u > 3:
        return BRASS if h > -6 else IRON
    if h < -0.55 * R:
        n = hash01(u * 3 + int(v), int(h), 71)
        return BRASS if n < 0.55 else (COPPER if n < 0.8 else VERD)
    return canvas(x, y, z, low=-0.18 if h < -2 else 0.06)


def hull_intact(C):
    for u in range(0, INTACT + 1):
        r = env_r(u)
        ri = int(math.ceil(r)) + 2
        ring = (u % 8 == 4) and u > 6
        for v in range(-ri, ri + 1):
            for h in range(-ri, ri + 1):
                d = math.hypot(v, h)
                x, y, z = X(u), AY + h, Z(v)
                if ring and r + 0.4 < d <= r + 1.25:
                    C.set(x, y, z, IRON if h < 8 else BRASS)
                    continue
                if d > r + 0.4:
                    continue
                if d > r - 1.0 or u == 0:
                    C.set(x, y, z, skin_spec(u, v, h, x, y, z))
                elif u >= INTACT - 1:
                    # the aft bulkhead of the last gas cell, seen from the deflated tail
                    C.set(x, y, z, IRON if (v % 6 == 0 or h % 6 == 0) else canvas(x, y, z))
                else:
                    C.set(x, y, z, GAS)
                    C.gas.add((x, y, z))


def hull_aft(C):
    """The deflated tail: ring girders (sagging, two broken at the crown), the keel, eight longitudinals, and the
    canvas draped over them in folds, torn open in places, hanging down the flanks in curtains."""
    rings = list(range(INTACT + 8, LEN + 1, 8))
    for u in range(INTACT, LEN + 1):
        r = env_r(u)
        ri = int(math.ceil(r)) + 2
        isring = u in rings
        frac = ((u - INTACT) % 8) / 8.0
        t = (u - INTACT) / float(LEN - INTACT)
        sag = (1.5 + 3.5 * t) * math.sin(math.pi * frac)
        for v in range(-ri, ri + 1):
            for h in range(-ri, ri + 1):
                d = math.hypot(v, h)
                x, y, z = X(u), AY + h, Z(v)
                th = math.atan2(h, v)
                if isring:
                    broken = (u in (INTACT + 24, INTACT + 40) and 1.2 < th < 1.95)
                    if r - 0.6 < d <= r + 0.5 and not broken:
                        C.set(x, y, z, BRASS if h > 0 else IRON)
                        continue
                # keel (a triangular truss) and eight longitudinals
                if abs(v) <= 1 and abs(h + r) < 0.7:
                    C.set(x, y, z, IRON if abs(v) == 1 or u % 4 else BRASS)
                    continue
                step = math.pi / 4
                arc = d * abs(((th + step / 2) % step) - step / 2)
                if arc < 0.5 and r - 0.6 < d <= r + 0.5 and h > -r * 0.7:
                    gap = (hash01(int(th * 10), u // 6, 81) < 0.18)
                    if not gap:
                        C.set(x, y, z, BRASS if h > 4 else IRON)
                        continue
        # the drape: one canvas surface per column, sagging between the rings
        for v in range(-ri - 1, ri + 2):
            av = abs(v)
            x, z = X(u), Z(v)
            if av < r * 0.78:
                top = AY + math.sqrt(max(0.0, r * r - v * v)) - sag * (1.0 - (av / r) ** 2) + 0.6
                y0 = int(round(top))
                tear = fbm(u * 1.3, v * 1.1, 5.0, 83) > 0.70 - 0.25 * max(0.0, t - 0.5)
                if tear and av > 2:
                    continue
                y1 = y0
                # close the surface towards the neighbour column (no gaps on the slopes)
                vn = av + 1
                if vn < r * 0.78:
                    tn = AY + math.sqrt(max(0.0, r * r - vn * vn)) - sag * (1.0 - (vn / r) ** 2) + 0.6
                    y1 = min(y0, int(round(tn)) + 1)
                for y in range(y1, y0 + 1):
                    if C.empty(x, y, z):
                        C.set(x, y, z, canvas(x, y, z, low=0.05))
            elif av <= r + 1.5:
                # the curtain hanging down the flank from the shoulder
                sh = AY + int(round(math.sqrt(max(0.0, r * r - (r * 0.78) ** 2))))
                hem = AY - int(r * 0.15) - int(10 * fbm(u * 0.9, v, 4.0, 85)) - int(6 * t)
                if fbm(u * 1.7, v * 0.5, 3.0, 86) > 0.66:
                    continue
                vv = int(round(math.copysign(r * 0.78 + (sh - hem) * 0.0, v)))
                if av < int(r * 0.78) + 1 or av > int(r * 0.78) + 2:
                    continue
                for y in range(hem, sh + 1):
                    if C.empty(x, y, z):
                        C.set(x, y, z, canvas(x, y, z, low=-0.1))
                del vv


def fins(C):
    """Four tail fins at the end of the frame, canvas on brass frames; the rudder hangs torn."""
    u0, u1 = LEN - 14, LEN + 2
    for u in range(u0, u1 + 1):
        r = env_r(min(u, LEN))
        span = 2 + int((u - u0) * 0.75)
        for k in range(1, span + 1):
            for (dv, dh) in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                d = r + k
                if (dv, dh) == (0, -1) and k > span - 3:
                    continue           # the lower fin is torn short
                x, y, z = X(u), AY + int(round(dh * d)), Z(int(round(dv * d)))
                edge = (k == span or u in (u0, u1))
                C.set(x, y, z, BRASS if edge else canvas(x, y, z))


# ------------------------------------------------------------------ the moored ship: gondola
def g_hw(y):
    gy = y - (LOF - 3)            # 0 at the keel (y 44)
    if gy < 0 or gy > 16:
        return -1
    return (4, 6.5, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 8)[gy]


def g_plan(u):
    if u < GU0 or u > GU1:
        return 0.0
    if u < GU0 + 5:
        return math.sqrt(max(0.0, 1 - ((GU0 + 5 - u) / 5.6) ** 2))
    if u > GU1 - 3:
        return math.sqrt(max(0.0, 1 - ((u - (GU1 - 3)) / 3.6) ** 2))
    return 1.0


def gondola(C):
    """The gondola's shell (dark iron, brass bands at the deck lines, windows along the upper deck, portholes in
    the hold), its two decks, the fairing up to the envelope."""
    y_keel = LOF - 3
    for u in range(GU0, GU1 + 1):
        pl = g_plan(u)
        for y in range(y_keel, UPF + 7):
            hw = g_hw(y) * pl
            if hw < 0.5:
                continue
            for v in range(-GW - 1, GW + 2):
                x, z = X(u), Z(v)
                if abs(v) > hw + 0.3:
                    continue
                shell = abs(v) > hw - 0.9 or y in (y_keel, UPF + 6) or u in (GU0, GU1) or pl < 0.7
                if shell:
                    if y in (LOF - 1, UPF - 1, UPF + 6):
                        spec = BRASS
                    elif y in (UPF + 1, UPF + 2) and u % 3 != 0 and GU0 + 2 < u < GU1 - 2:
                        spec = "glass_pane"
                    elif GU0 <= u < GU0 + 6 and UPF <= y <= UPF + 3 and abs(v) < hw:
                        spec = "glass_pane"      # the bridge's wrap-round windows
                    elif y == LOF + 1 and u % 6 == 3 and GU0 + 4 < u < GU1 - 3:
                        spec = "glass"           # portholes of the hold
                    elif y < LOF - 1:
                        spec = BRASS if (u % 6 == 0) else COPPER if hash01(u, y, 91) < 0.2 else IRON
                    else:
                        spec = IRON_BR if u % 6 == 0 else IRON
                    C.set(x, y, z, spec)
                elif y == LOF - 1 or y == UPF - 1:
                    C.set(x, y, z, PARQUET if y == UPF - 1 and not (u > 62 and u < 75) else TREAD)
                elif y == UPF - 2:
                    C.set(x, y, z, IRON)            # the hold's ceiling under the upper deck
                elif y < LOF - 1:
                    C.set(x, y, z, IRON)
                else:
                    C.air(x, y, z)
    # the fairing between the gondola roof and the envelope
    for u in range(GU0 + 2, GU1 - 1):
        for v in range(-GW + 1, GW):
            x, z = X(u), Z(v)
            for y in range(UPF + 7, AY):
                if C.get(x, y, z) is not None and C.get(x, y, z) != AIR:
                    break
                C.set(x, y, z, IRON if (u + y) % 7 else BRASS)


def nacelles(C):
    """Two engine cars on outriggers either side of the saloon: a pod of dark iron and brass, the engine inside,
    a propeller at the back; catwalks from the saloon's side doors."""
    for sv in (-1, 1):
        cv = sv * NAC_V
        for u in range(74, 88):
            t = 1.0 if u > 76 else math.sqrt(max(0.0, 1 - ((77 - u) / 3.4) ** 2))
            rr = 4.0 * t if u < 86 else 4.0 - (u - 85) * 1.2
            for v in range(cv - 5, cv + 6):
                for y in range(NAC_Y - 5, NAC_Y + 6):
                    d = math.hypot(v - cv, y - NAC_Y)
                    if d > rr + 0.35:
                        continue
                    x, z = X(u), Z(v)
                    inner = d <= rr - 1.0 and 76 <= u <= 84
                    if inner:
                        if y < NAC_Y - 2:
                            C.set(x, y, z, TREAD if y == NAC_Y - 3 else IRON)
                        else:
                            C.air(x, y, z)
                    else:
                        C.set(x, y, z, BRASS if (u % 4 == 0 or y == NAC_Y + 4) else
                              ("glass_pane" if y == NAC_Y and u in (79, 82) else IRON))
        # the engine: cylinders, a flywheel, gauges
        ex = X(82)
        for u in (82, 83, 84):
            C.set(X(u), NAC_Y - 2, Z(cv), COPPER)
            C.set(X(u), NAC_Y - 1, Z(cv), "blast_furnace[facing=west,lit=true]" if u == 82 else COPPER)
        C.set(X(84), NAC_Y, Z(cv), PIPES)
        C.set(ex, NAC_Y + 1, Z(cv + 2 * -sv), GAUGE)
        C.set(X(80), NAC_Y + 2, Z(cv), HANG_LAMP)
        C.bp.chest(X(83), NAC_Y - 2, Z(cv - sv * 2), "west", loot=LOOT + "ag_engine")
        C.set(X(84), NAC_Y - 2, Z(cv + sv * 2), "barrel[facing=up,open=false]")
        # propeller behind the pod
        propeller(C, X(88), NAC_Y, Z(cv), "x", r=5, turn=1 if sv > 0 else 0)
        C.set(X(87), NAC_Y, Z(cv), IRON)
        # the catwalk from the saloon door (v = sv * 9) to the pod door
        vin, vout = sv * (GW + 1), sv * (NAC_V - 4)
        for v in range(min(vin, vout), max(vin, vout) + 1):
            for u in (77, 78, 79):
                x, z = X(u), Z(v)
                C.set(x, UPF - 1, z, TREAD if u == 78 else IRON)
                for y in range(UPF, UPF + 3):
                    C.air(x, y, z)
            rail(C, X(76), UPF, Z(v), "west")
            rail(C, X(80), UPF, Z(v), "east")
            C.set(X(76), UPF - 1, Z(v), IRON)
            C.set(X(80), UPF - 1, Z(v), IRON)
            if v % 3 == 0:
                C.set(X(78), UPF - 2, Z(v), stair(IRON_STAIRS, "south" if sv > 0 else "north", "top"))
        # doors: the saloon's side and the pod's flank
        for u in (77, 78, 79):
            for y in range(UPF, UPF + 3):
                C.air(X(u), y, Z(sv * GW))
                C.air(X(u), y, Z(sv * (NAC_V - 4)))
                C.air(X(u), y, Z(sv * (NAC_V - 3)))
            C.set(X(u), UPF - 1, Z(sv * (NAC_V - 3)), TREAD)
        # struts from the gondola to the pod
        for u in (75, 81):
            for v in range(min(vin, vout), max(vin, vout) + 1):
                C.set(X(u), UPF + 5, Z(v), IRON_WALL)
            C.set(X(u), UPF + 4, Z(sv * (GW + 1)), IRON)


# ------------------------------------------------------------------ the moored ship: rooms carved in the hull
def carve_hull(C):
    """The docking vestibule, the nose stair, the keel landing (rigger's store), the trunk stair down into the
    gondola, the climbing shaft, the site of grace, the narrow stair to the deckhouse, the treasury and its stair."""
    # vestibule u 1..8 (feet RW), the docking door at the nose tip
    for u in range(0, 9):
        for v in (-1, 0, 1):
            for y in range(RW, RW + 3):
                C.air(X(u), y, Z(v))
            C.set(X(u), RW - 1, Z(v), TREAD)
    C.set(X(5), RW + 3, Z(0), HANG_LAMP)
    # nose stair: u 9..14 down to feet 71, landing u 15..16, u 17..20 down to the keel landing (feet KF)
    cells = {}

    def nose(u):
        if u <= 14:
            return RW - (u - 8), True
        if u <= 16:
            return RW - 6, False
        return RW - 6 - (u - 16), True
    run_x(cells, 9, 20, -1, 1, nose, "west")
    write_steps(C, cells, solid_to=None)
    # the keel landing (u 21..29, v -4..4, feet KF, 5 high) and the rigger's store beside it
    C.clear(X(21), X(29), KF, KF + 4, Z(-4), Z(4))
    C.box(X(21), X(29), KF - 1, KF - 1, Z(-4), Z(4), TREAD)
    C.clear(X(22), X(28), KF, KF + 3, Z(5), Z(8))
    C.box(X(22), X(28), KF - 1, KF - 1, Z(5), Z(8), "spruce_planks")
    # the trunk stair down into the gondola: u 30..35 (feet 66..61), landing u 36..37, u 38..44 (feet 60..54)
    cells = {}

    def trunk(u):
        if u <= 35:
            return KF - 1 - (u - 30), True
        if u <= 37:
            return KF - 6, False
        return KF - 6 - (u - 37), True
    run_x(cells, 30, 37, -1, 1, trunk, "west")
    write_steps(C, cells)
    cells = {}
    run_x(cells, 38, 44, -1, 1, trunk, "west")
    write_steps(C, cells, solid_to=UPF - 1)
    # the climbing shaft: a newel stair from the hold (feet LOF) to the site of grace (feet GRF)
    su, sv = SH
    # trunk walls through the gondola
    for u in range(su - 1, su + 11):
        for v in range(sv - 1, sv + 11):
            if u in (su - 1, su + 10) or v in (sv - 1, sv + 10):
                for y in range(LOF - 1, UPF + 6):
                    C.set(X(u), y, Z(v), IRON_BR if (y - LOF) % 7 else BRASS)
    flights = [4] * 10

    def shaft_rail(x, z):
        u, v = x - NX, z - SZ
        if u == su:
            return (-1, 0)
        if u == su + 9:
            return (1, 0)
        if v == sv:
            return (0, -1)
        if v == sv + 9:
            return (0, 1)
        return None
    parts, core, top_c, top_f = newel_laps(C, X(su), Z(sv), 4, LOF, flights, 0, solid_first=True)
    cx0, cz0, cx1, cz1 = core
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            for y in range(LOF - 1, GRF + 4):
                C.set(x, y, z, IRON_BR if (y - LOF) % 8 else BRASS)
                C.gas.discard((x, y, z))
    for f in range(LOF + 2, GRF, 4):
        C.set(cx0 - 0, f + 2, cz0 - 0, EDISON)
        C.set(cx1, f + 2, cz1, EDISON)
    # the door from the hold into the shaft's bottom landing (north face)
    for u in range(su, su + 3):
        for y in range(LOF, LOF + 3):
            C.air(X(u), y, Z(sv - 1))
    # site of grace: u 74..81, v 0..5, feet GRF, 4 high
    C.clear(X(su + 10), X(su + 17), GRF, GRF + 3, Z(0), Z(5))
    C.box(X(su + 10), X(su + 17), GRF - 1, GRF - 1, Z(0), Z(5), PARQUET)
    for v in range(sv + 7, sv + 10):
        for y in range(GRF, GRF + 3):
            C.air(X(su + 10), y, Z(v))
    # the narrow stair (compression) u 82..89, v 1..3, feet 88..95, then the deckhouse landing u 90..92
    cells = {}

    def comp(u):
        if u <= 89:
            return GRF + 1 + (u - 82), True
        return DY + 1, False
    run_x(cells, 82, 92, 1, 3, comp, "east")
    write_steps(C, cells, clear=4)
    # treasury hold: u 15..24, v -4..4, feet TRF, 5 high; its stair u 25..34 (feet 85..94) from the gangway head
    C.clear(X(15), X(24), TRF, TRF + 4, Z(-4), Z(4))
    C.box(X(15), X(24), TRF - 1, TRF - 1, Z(-4), Z(4), PARQUET)
    cells = {}
    run_x(cells, 25, 34, 0, 2, lambda u: (TRF + (u - 24) - 1 if u > 25 else TRF, u > 25), "east")
    write_steps(C, cells, clear=4)


def line_hull(C):
    """Line every carved room in the hull: the gas cells round it become walls, floors and ceilings."""
    for (x, y, z) in list(C.inner):
        if C.get(x, y, z) != AIR:
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
            p = (x + dx, y + dy, z + dz)
            if p not in C.gas:
                continue
            if dy < 0:
                spec = TREAD
            elif dy > 0:
                spec = IRON if (p[0] % 4) else BRASS
            elif y >= TRF - 1:
                spec = MAHOGANY if (p[1] - TRF) % 4 else BRASS
            else:
                spec = IRON_BR if (p[1] + p[0] + p[2]) % 5 else IRON
            C.set(*p, spec)
            C.gas.discard(p)


def hull_rooms(C):
    """Furnish the rooms carved in the hull."""
    # vestibule: the docking collar, two lamps, a ship's bell
    for v in (-2, 2):
        for y in range(RW, RW + 3):
            if C.get(X(1), y, Z(v)) not in (AIR, None):
                C.set(X(1), y, Z(v), BRASS)
    C.set(X(7), RW + 2, Z(-2), EDISON) if C.get(X(7), RW + 2, Z(-2)) not in (AIR, None) else None
    C.set(X(7), RW + 2, Z(2), EDISON) if C.get(X(7), RW + 2, Z(2)) not in (AIR, None) else None
    # nose stair lamps
    for u in (12, 18):
        C.set(X(u), RW - (u - 8) + 4 if u <= 14 else RW - 6 - (u - 16) + 4, Z(-2), EDISON)
    # keel landing: coils of rope, spare girders, the rigger's store
    f = KF
    C.set(X(25), f + 4, Z(0), HANG_LAMP)
    C.set(X(25), f + 5, Z(0), CHAIN)
    for u in (22, 23, 27, 28):
        C.set(X(u), f, Z(-4), "barrel[facing=up,open=false]" if u % 2 else BRASS)
    C.set(X(23), f + 1, Z(-4), "barrel[facing=up,open=false]")
    for u in range(22, 29):
        C.set(X(u), f, Z(8), "white_wool" if u % 3 else "brown_wool")     # folded canvas
    C.set(X(24), f + 1, Z(8), "light_gray_wool")
    C.bp.chest(X(27), f, Z(7), "west", loot=LOOT + "ag_hold")
    C.set(X(25), f + 3, Z(6), HANG_LAMP)
    C.set(X(25), f + 4, Z(6), CHAIN)
    C.set(X(22), f, Z(6), "loom[facing=east]")
    # the trunk stair: a lamp on the landing
    C.set(X(36), KF - 6 + 3, Z(-2), EDISON)
    # the site of grace: waystone, a bench, a chart of the field
    g = GRF
    C.set(X(78), g, Z(3), MOD["waystone"])
    C.set(X(77), g + 3, Z(2), HANG_LAMP)
    C.set(X(80), g, Z(0), stair(MAHOGANY_STAIRS, "south"))
    C.set(X(81), g, Z(0), stair(MAHOGANY_STAIRS, "south"))
    C.set(X(75), g, Z(0), "barrel[facing=up,open=false]")
    C.set(X(81), g + 2, Z(5), EDISON) if C.get(X(81), g + 2, Z(6)) else None
    # compression stair lamps
    C.set(X(84), GRF + 1 + 2 + 3, Z(0), EDISON) if C.get(X(84), GRF + 5, Z(0)) not in (None, AIR) else None
    # the treasury hold: the company's strongboxes, bullion, the ship's papers
    t = TRF
    for (u, v, fc) in ((16, -3, "east"), (16, 3, "east"), (20, -4, "south"), (20, 4, "north")):
        C.bp.chest(X(u), t, Z(v), fc, loot=LOOT + "ag_treasury")
    for u in range(15, 24):
        for v in (-4, 4):
            if C.empty(X(u), t, Z(v)) and hash01(u, v, 101) < 0.55:
                C.set(X(u), t, Z(v), ("gold_block", "raw_gold_block", "iron_block", "raw_copper_block",
                                     BRASS)[int(hash01(u, v, 102) * 5)])
    for v in range(-2, 3):
        if C.empty(X(15), t, Z(v)):
            C.set(X(15), t, Z(v), "barrel[facing=up,open=false]" if v % 2 else "gold_block")
    C.set(X(19), t + 4, Z(0), CHANDELIER)
    C.set(X(22), t, Z(0), TABLE)
    C.set(X(22), t + 1, Z(0), "lantern[hanging=false,waterlogged=false]")


def gondola_rooms(C):
    """Partitions and furnishings of the gondola."""
    f, g = UPF, LOF
    # ---- the bridge u 31..37: wheel, binnacle, chart table, telegraphs, speaking tubes
    for v in range(-8, 9):
        if v in (4, 5, 6):
            continue
        for y in range(f, f + 5):
            C.set(X(38), y, Z(v), MAHOGANY if y < f + 4 else BRASS)
    C.set(X(33), f, Z(0), IRON_WALL)
    C.set(X(33), f + 1, Z(0), f"{VALVE}[facing=west]")
    C.set(X(35), f, Z(0), f"{CHAIR}[facing=west]")
    C.set(X(32), f, Z(-3), IRON)
    C.set(X(32), f + 1, Z(-3), "lever[face=floor,facing=west,powered=false]")
    C.set(X(32), f, Z(3), IRON)
    C.set(X(32), f + 1, Z(3), "lever[face=floor,facing=west,powered=true]")
    C.set(X(36), f, Z(-5), TABLE)
    C.set(X(36), f, Z(-6), "cartography_table")
    C.set(X(36), f, Z(6), "lectern[facing=west,has_book=false,powered=false]")
    C.bp.chest(X(37), f, Z(-7), "east", loot=LOOT + "ag_bridge")
    C.set(X(34), f, Z(7), PIPES)
    C.set(X(34), f + 1, Z(7), GAUGE)
    C.set(X(34), f, Z(-7), PIPES)
    C.set(X(34), f + 1, Z(-7), GAUGE)
    C.set(X(34), f + 4, Z(0), HANG_LAMP)
    # ---- the companion hall u 39..46: the trunk stair lands here; benches, the ladder down to the hold
    C.set(X(42), f + 4, Z(-5), HANG_LAMP)
    C.set(X(42), f + 4, Z(5), HANG_LAMP)
    for u in (40, 41, 42):
        C.set(X(u), f, Z(-8), stair(MAHOGANY_STAIRS, "south"))
    C.bp.barrel(X(39), f, Z(-8))
    # the ladder at u 45, v 8 (hold feet LOF to the upper deck)
    for y in range(g, f):
        C.set(X(45), y, Z(8), "ladder[facing=north,waterlogged=false]")
    C.set(X(45), f - 1, Z(8), "ladder[facing=north,waterlogged=false]")
    C.set(X(45), f - 2, Z(8), "ladder[facing=north,waterlogged=false]")
    rail(C, X(44), f, Z(8), "west")
    rail(C, X(46), f, Z(8), "east")
    # ---- partition at u 47 with the door to the cabins' corridor
    for v in range(-8, 9):
        if abs(v) <= 1:
            continue
        for y in range(f, f + 5):
            C.set(X(47), y, Z(v), MAHOGANY if y < f + 4 else BRASS)
    # corridor walls (v = -2 for u 48..57, v = 2 for u 48..62) and cabin divisions
    for u in range(48, 63):
        for y in range(f, f + 5):
            if u <= 57:
                C.set(X(u), y, Z(-2), MAHOGANY)
            C.set(X(u), y, Z(2), MAHOGANY)
    for (u, v0, v1) in ((52, -8, -3), (53, -8, -3), (57, -8, -3), (52, 3, 8), (57, 3, 8)):
        for v in range(v0, v1 + 1):
            for y in range(f, f + 5):
                C.set(X(u), y, Z(v), MAHOGANY)
    # cabin doors
    for (u, v, fc) in ((50, -2, "south"), (55, -2, "south"), (50, 2, "north"), (55, 2, "north"), (60, 2, "north")):
        door(C, X(u), f, Z(v), fc)
    # cabins: N1 (crew bunks), N2 (navigator), S1 (officer), S2 (purser), S3 (captain)
    C.bp.bed(X(49), f, Z(-7), "east", color="brown")
    C.bp.bed(X(49), f, Z(-4), "east", color="brown")
    C.set(X(51), f, Z(-6), "barrel[facing=up,open=false]")
    C.set(X(50), f + 3, Z(-5), HANG_LAMP)
    C.bp.chest(X(51), f, Z(-3), "west", loot=LOOT + "ag_cabin")
    C.set(X(54), f, Z(-7), TABLE)
    C.set(X(55), f, Z(-7), "cartography_table")
    C.set(X(54), f, Z(-6), f"{CHAIR}[facing=north]")
    C.set(X(56), f, Z(-4), "chiseled_bookshelf[facing=west,slot_0_occupied=false,slot_1_occupied=false,"
                            "slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,"
                            "slot_5_occupied=false]")
    C.set(X(55), f + 3, Z(-5), HANG_LAMP)
    C.bp.bed(X(49), f, Z(7), "east", color="blue")
    C.set(X(51), f, Z(7), TABLE)
    C.set(X(51), f + 1, Z(7), LANT)
    C.bp.chest(X(49), f, Z(4), "east", loot=LOOT + "ag_cabin")
    C.set(X(50), f + 3, Z(5), HANG_LAMP)
    C.set(X(54), f, Z(7), TABLE)
    C.set(X(55), f, Z(7), TABLE)
    C.set(X(54), f, Z(6), f"{CHAIR}[facing=south]")
    C.bp.chest(X(56), f, Z(7), "west", loot=LOOT + "ag_cabin")
    C.set(X(55), f + 3, Z(5), HANG_LAMP)
    C.bp.bed(X(59), f, Z(7), "east", color="red")
    C.set(X(61), f, Z(7), "barrel[facing=up,open=false]")
    C.set(X(62), f, Z(5), TABLE)
    C.set(X(62), f + 1, Z(5), LANT)
    C.set(X(61), f, Z(5), f"{CHAIR}[facing=east]")
    C.bp.chest(X(62), f, Z(3), "west", loot=LOOT + "ag_captain")
    C.set(X(60), f + 3, Z(5), CHANDELIER)
    # lobby lamp, corridor lamps
    C.set(X(60), f + 4, Z(-5), HANG_LAMP)
    for u in (49, 54, 59):
        C.set(X(u), f + 4, Z(0), HANG_LAMP)
    # ---- passages beside the shaft trunk; the saloon u 75..83
    C.set(X(68), f + 4, Z(-7), HANG_LAMP)
    for u in range(78, 83):
        C.set(X(u), f, Z(2), TABLE)
        C.set(X(u), f, Z(1), f"{CHAIR}[facing=south]")
        C.set(X(u), f, Z(3), f"{CHAIR}[facing=north]")
    C.set(X(80), f + 4, Z(2), CHANDELIER)
    for v in range(4, 9):
        C.set(X(84), f, Z(v), MAHOGANY if v != 6 else "barrel[facing=up,open=false]")
    # the aft stair down to the hold: v -4..-2, u 76..82 (feet 53..47), railings round the well
    cells = {}
    run_x(cells, 76, 82, -4, -2, lambda u: (f - 1 - (u - 76), True), "west")
    write_steps(C, cells, clear=4)
    for u in range(76, 84):
        rail(C, X(u), f, Z(-5), "north")
        rail(C, X(u), f, Z(-1), "south")
    for v in (-4, -3, -2):
        if C.empty(X(83), f, Z(v)):
            rail(C, X(83), f, Z(v), "east")
    # ---- the cargo hold (feet LOF): crates, ballast tanks, cargo nets, the ladder up at the fore end
    for (u, v) in ((33, -6), (33, -5), (34, -6), (33, 5), (34, 6), (35, 6), (50, -7), (51, -7), (52, -7),
                   (50, 7), (51, 7), (56, 7), (57, 7), (58, 7), (80, 7), (81, 7), (82, 7), (84, 2), (84, 3)):
        if C.empty(X(u), g, Z(v)):
            C.set(X(u), g, Z(v), "barrel[facing=up,open=false]" if (u + v) % 3 else "spruce_planks")
            if (u + v) % 2 and C.empty(X(u), g + 1, Z(v)):
                C.set(X(u), g + 1, Z(v), "barrel[facing=up,open=false]")
    for u in range(40, 48):
        for v in (-7, 7):
            C.set(X(u), g, Z(v), COPPER if u % 4 else BRASS)                 # ballast tanks
            C.set(X(u), g + 1, Z(v), COPPER if u % 4 else BRASS)
    C.bp.chest(X(54), g, Z(-7), "south", loot=LOOT + "ag_hold")
    C.bp.chest(X(82), g, Z(6), "west", loot=LOOT + "ag_hold")
    for u in (36, 44, 52, 60, 78):
        C.set(X(u), g + 4, Z(0), HANG_LAMP)
    for u in (36, 52):
        C.set(X(u), g + 4, Z(-5), HANG_LAMP)
    C.bp.spawner(X(52), g, Z(3), MOB_RAIDER)
    # cargo hatch in the floor (closed), a cargo hook on a chain
    for u in range(55, 59):
        for v in range(-1, 2):
            C.set(X(u), g - 1, Z(v), "iron_trapdoor[facing=north,half=top,open=false,powered=false,"
                                     "waterlogged=false]")
            C.set(X(u), g - 2, Z(v), IRON)
    C.set(X(57), g + 4, Z(0), CHAIN)
    C.set(X(57), g + 3, Z(0), CHAIN)


# ------------------------------------------------------------------ set dressing: hold, winch house, top deck
CRATES = ("spruce_planks", "stripped_spruce_wood[axis=y]", MAHOGANY, "oak_planks", "dark_oak_planks",
          "stripped_dark_oak_wood[axis=x]")      # crates only: a barrel deep in a stack would be loot out of reach


def put(C, x, y, z, spec):
    """Set only into air written on purpose (never into a wall, a stair or a piece of furniture)."""
    if C.get(x, y, z) == AIR:
        C.set(x, y, z, spec)
        return True
    return False


def crate_stack(C, x0, z0, w, d, y, hmax, seed, lash=True, lamp=False):
    """A block of cargo w x d: crates and barrels 1..hmax high (tallest at the back), lashed with chains."""
    tops = {}
    for i in range(w):
        for j in range(d):
            x, z = x0 + i, z0 + j
            h = 1 + int(hash01(x, z, seed) * hmax)
            h = max(1, min(hmax, h))
            for k in range(h):
                if not put(C, x, y + k, z, CRATES[int(hash3(x, y + k, z, seed + 1) * len(CRATES))]):
                    break
                tops[(x, z)] = y + k
    if lash and w >= 2:
        # a lashing chain over the top row along x
        zt = z0 + d // 2
        yt = min(tops.get((x0 + i, zt), y) for i in range(w)) + 1
        if all(C.get(x0 + i, yt, zt) == AIR for i in range(w)):
            for i in range(w):
                C.set(x0 + i, yt, zt, "iron_chain[axis=x,waterlogged=false]")
    if lamp and tops:
        (x, z), t = max(tops.items(), key=lambda kv: (-kv[1], kv[0]))
        put(C, x, t + 1, z, LANT)
    return tops


def ballast_tank(C, u0, u1, vc, g):
    """A ballast tank lying along the hull: copper, brass bands, rounded shoulders, a valve and a gauge."""
    for u in range(u0, u1 + 1):
        band = u in (u0, u1) or (u - u0) % 3 == 0
        for dv in (-1, 0, 1):
            for dy in (0, 1, 2):
                x, z, y = X(u), Z(vc + dv), g + dy
                if dv and dy == 2:
                    put(C, x, y, z, stair(COPPER_ST, "north" if dv > 0 else "south", "bottom"))
                elif u in (u0, u1):
                    put(C, x, y, z, IRON)
                else:
                    put(C, x, y, z, BRASS if band else COPPER)
    put(C, X(u0 - 1), g + 1, Z(vc), f"{VALVE}[facing=west]")
    put(C, X((u0 + u1) // 2), g + 3, Z(vc), GAUGE)
    for u in (u0 + 1, u1 - 1):
        for y in range(g + 3, UPF - 2):
            put(C, X(u), y, Z(vc), PIPES)


def hold_cargo(C):
    """The cargo hold was a bare iron box: stacks of crates and barrels lashed down along the sides, two ballast
    tanks, cargo nets hung from the deck beams, crates hanging on chains, an overhead crane rail with its trolley
    over the hatch, lanterns on the stacks (feet LOF; the middle of the hold, v -2..2, stays clear)."""
    g = LOF
    # the old low tank lines go: two proper ballast tanks take their place (the ladder at u 45, v 8 stays free)
    for u in range(40, 48):
        for v in (-7, 7):
            for y in (g, g + 1):
                if C.get(X(u), y, Z(v)) in (COPPER, BRASS):
                    C.air(X(u), y, Z(v))
    ballast_tank(C, 39, 47, -7, g)
    ballast_tank(C, 36, 42, 7, g)
    # cargo stacks (u, v, w along u, d along v, max height)
    for i, (u, v, w, d, h) in enumerate(((56, -8, 3, 3, 3), (59, -8, 3, 2, 2), (47, 6, 2, 3, 3),
                                         (59, 6, 4, 3, 3), (77, -8, 4, 2, 2), (49, -8, 1, 1, 2),
                                         (33, -8, 2, 2, 2))):
        crate_stack(C, X(u), Z(v), w, d, g, h, 211 + i, lamp=i in (0, 3, 4))
    # cargo nets hung from the deck beams over the stacks' aisle side
    for (u0, u1, v) in ((56, 61, -5), (59, 62, 5), (47, 48, 5)):
        for u in range(u0, u1 + 1):
            for y in range(g + 3, UPF - 2):
                put(C, X(u), y, Z(v), "iron_bars")
    # crates hanging on chains from the beams (above head height)
    for (u, v) in ((45, -4), (44, 4), (53, -4), (79, -6)):
        if C.get(X(u), UPF - 2, Z(v)) not in (None, AIR) and C.get(X(u), g + 3, Z(v)) == AIR:
            put(C, X(u), UPF - 3, Z(v), CHAIN)
            put(C, X(u), g + 3, Z(v), "stripped_spruce_wood[axis=y]" if u % 2 else "oak_planks")
    # the crane rail along v -3 under the deck beams, its trolley and hook over the hatch
    for u in range(33, 63):
        put(C, X(u), UPF - 3, Z(-3), IRON_SLAB + "[type=top,waterlogged=false]")
    for u in (55, 59):
        put(C, X(u), UPF - 3, Z(-2), IRON_SLAB + "[type=top,waterlogged=false]")
        put(C, X(u), UPF - 3, Z(-1), IRON_SLAB + "[type=top,waterlogged=false]")
    C.set(X(50), UPF - 3, Z(-3), GEAR)                                   # the trolley
    put(C, X(50), g + 3, Z(-3), "stripped_dark_oak_wood[axis=x]")        # a crate on the hook
    # lamps over the south bays (as over the north ones), lanterns in the bays
    for u in (36, 44, 52):
        if C.get(X(u), g + 4, Z(5)) == AIR and C.get(X(u), UPF - 2, Z(5)) not in (None, AIR):
            C.set(X(u), g + 4, Z(5), HANG_LAMP)
    if C.get(X(44), g + 4, Z(-5)) == AIR:
        C.set(X(44), g + 4, Z(-5), HANG_LAMP)
    for (u, v) in ((41, -4), (58, 4), (62, -4), (80, 5)):
        lamp_hang(C, X(u), g + 3, Z(v), drop=1, spec=LANT_H) if C.get(X(u), g + 4, Z(v)) == AIR and \
            C.get(X(u), g + 3, Z(v)) == AIR and C.get(X(u), UPF - 2, Z(v)) not in (None, AIR) else None


def roof_details(C):
    """Mooring cables from the ring to the nose, a mooring line from the tail to a ground anchor, lamps along the
    envelope's equator, the ship's name plate."""
    # ground anchors under the tail and the gondola: vertical mooring chains
    for (u, v) in ((126, 0), (110, -6), (110, 6)):
        r = env_r(u)
        top = AY - int(math.sqrt(max(0.0, r * r - v * v))) - 1
        x, z = X(u), Z(v)
        for y in range(2, top + 1):
            if C.empty(x, y, z):
                C.set(x, y, z, CHAIN)
        C.set(x, 1, z, IRON)
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            C.set(x + dx, 1, z + dz, IRON_SLAB + "[type=bottom,waterlogged=false]")
        C.set(x, 0, z, IRON_BR)
    # the name plate on the bow (brass on dark iron)
    for u in range(30, 44):
        for h in (2, 3, 4):
            v = -int(math.sqrt(max(0.0, R * R - h * h))) - 1
            C.set(X(u), AY + h, Z(v), BRASS if h == 3 and u % 2 else IRON)


# ------------------------------------------------------------------ the moored ship: deck, gangway, crown
def deck(C):
    """The top deck (the arena): planking, a brass ring round the centre, deck plates at the edge, railings, vent
    cowls; the deckhouse over the narrow stair with the mist in its door; the sealed gate at the west end."""
    au, av = AC
    for u in range(DU0, DU1 + 1):
        for v in range(-DV, DV + 1):
            x, z = X(u), Z(v)
            if 84 <= u <= 93 and 0 <= v <= 4:
                continue                  # the deckhouse (built below, over the narrow stair)
            d = math.hypot(u - au, v - av)
            if abs(v) >= DV - 1 or u in (DU0, DU1):
                spec = IRON
            elif 9.5 <= d < 10.5:
                spec = BRASS
            elif d < 2.5:
                spec = GEAR
            elif u % 9 == 0:
                spec = "dark_oak_planks"
            else:
                spec = "spruce_planks"
            C.set(x, DY, z, spec)
            for y in range(DY + 1, DY + 5):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
            # the deck's girder box, down to the skin; its flanks skirt the envelope's shoulder
            vv = min(abs(v), 16)
            bottom = AY + int(math.sqrt(max(0.0, 16.4 ** 2 - vv * vv)))
            for y in range(DY - 1, bottom - 1, -1):
                b = C.get(x, y, z)
                if (x, y, z) in C.inner:
                    continue
                if b is not None and b != AIR and abs(v) <= 13:
                    break
                if abs(v) >= DV - 1:
                    spec = BRASS if y == DY - 1 else ("glass" if y == DY - 3 and u % 5 == 2 else
                                                      IRON_BR if u % 6 == 0 else IRON)
                else:
                    spec = IRON if (u % 6) else BRASS
                C.set(x, y, z, spec)
    # a parapet round the edge (dark iron, brass posts with lamps)
    for u in range(DU0, DU1 + 1):
        for v in (-DV, DV):
            C.set(X(u), DY + 1, Z(v), IRON_WALL)
            C.set(X(u), DY + 2, Z(v), IRON_WALL)   # a chest-high bulwark: nobody steps off onto the skin
            if u % 8 == 2:
                C.set(X(u), DY + 3, Z(v), LANT)
    for v in range(-DV, DV + 1):
        if abs(v) > 2:
            C.set(X(DU0), DY + 1, Z(v), IRON_WALL)
            C.set(X(DU0), DY + 2, Z(v), IRON_WALL)
        # the stern end stands two high: beyond it the deflated envelope sags away under its drape
        C.set(X(DU1), DY + 1, Z(v), IRON_WALL)
        C.set(X(DU1), DY + 2, Z(v), IRON_WALL)
        if v % 8 == 0:
            C.set(X(DU1), DY + 3, Z(v), LANT)
    # vent cowls (low cover), symmetric about the centre line
    for (u, v) in ((51, -11), (51, 11), (75, -11), (75, 11)):
        for du in (0, 1):
            for dv in (0, 1):
                C.set(X(u + du), DY + 1, Z(v + dv), COPPER)
        C.set(X(u), DY + 2, Z(v), stair(COPPER_ST, "east"))
        C.set(X(u + 1), DY + 2, Z(v), stair(COPPER_ST, "west"))
        C.set(X(u), DY + 2, Z(v + 1), GRILLE)
        C.set(X(u + 1), DY + 2, Z(v + 1), GRILLE)
    # the deckhouse: walls u 84..93, v 0..4; door north (v 0) at u 90..92
    for u in range(84, 94):
        for v in range(0, 5):
            edge = u in (84, 93) or v in (0, 4)
            for y in range(DY, DY + 5):
                x, z = X(u), Z(v)
                if edge:
                    if y == DY:
                        C.set(x, y, z, IRON)
                    else:
                        C.set(x, y, z, BRASS if y == DY + 4 or u in (84, 93) and v in (0, 4) else
                              ("glass_pane" if y == DY + 2 and u % 2 else IRON_BR))
                elif y == DY and (u < 85 or u > 92):
                    C.set(x, y, z, TREAD)
            C.set(X(u), DY + 5, Z(v), IRON_SLAB + "[type=bottom,waterlogged=false]" if 84 < u < 93 and 0 < v < 4
                  else IRON)
    for u in range(90, 93):
        for y in range(DY + 1, DY + 4):
            C.air(X(u), y, Z(0))
    C.set(X(91), DY + 4, Z(2), HANG_LAMP) if C.empty(X(91), DY + 4, Z(2)) else None
    C.bp.mist(X(90), DY + 1, Z(0), X(92), DY + 3, Z(0))
    # lookout rail on the deckhouse roof
    for u in range(84, 94):
        rail(C, X(u), DY + 6, Z(0), "north")
        rail(C, X(u), DY + 6, Z(4), "south")
    # the seal
    C.bp.boss_seal(X(au), DY, Z(av), BOSS, 18)
    # the sealed gate at the west end (u 41): bars between two posts
    for v in (-2, 2):
        for y in range(DY + 1, DY + 5):
            C.set(X(41), y, Z(v), IRON if y < DY + 4 else BRASS)
    for v in (-1, 0, 1):
        for y in range(DY + 1, DY + 4):
            C.set(X(41), y, Z(v), MOD["vault_bars"])
        C.set(X(41), DY + 4, Z(v), BRASS)
        C.set(X(41), DY, Z(v), TREAD)


COPPER_ST = W + "copper_plating_stairs"

def deck_dressing(C):
    """Set dressing round the edge of the top deck (the fight floor itself stays open): rigging posts along both
    bulwarks with the stays strung between them overhead, tall vent cowls, two capstans by the sealed gate at the
    bow end, lamp posts in the corners."""
    y = DY + 1
    # rigging posts on the bulwarks' inner side (v +-16), stays strung between their heads (above head height)
    posts = (46, 56, 66, 76, 86)
    for v in (-16, 16):
        for u in posts:
            x, z = X(u), Z(v)
            if not put(C, x, y, z, IRON):
                continue
            for k in (1, 2):
                put(C, x, y + k, z, IRON_WALL)
            put(C, x, y + 3, z, BRASS)
            if C.get(x, y + 4, z) in (None, AIR):
                C.set(x, y + 4, z, LANT)
        for u in range(posts[0] + 1, posts[-1]):
            if u not in posts:
                put(C, X(u), y + 3, Z(v), "iron_chain[axis=x,waterlogged=false]")
    # tall vent cowls at the edge, mouths turned outboard
    for u in (61, 71):
        for v in (-15, 15):
            x, z = X(u), Z(v)
            if put(C, x, y, z, COPPER):
                put(C, x, y + 1, z, PIPES)
                put(C, x, y + 2, z, stair(COPPER_ST, "north" if v > 0 else "south", "bottom"))
    # two capstans by the sealed gate (u 45, v +-7): a drum with its bars, a pawl ring of iron slabs round its foot
    for v in (-7, 7):
        x, z = X(45), Z(v)
        if put(C, x, y, z, IRON):
            put(C, x, y + 1, z, BRASS)
            put(C, x, y + 2, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
            for fc, (dx, dz) in (("east", (1, 0)), ("west", (-1, 0)), ("north", (0, -1)), ("south", (0, 1))):
                put(C, x + dx, y + 1, z + dz, f"lightning_rod[facing={fc},powered=false,waterlogged=false]")
    # lamp posts in the four corners
    for u in (43, 93):
        for v in (-15, 15):
            x, z = X(u), Z(v)
            if C.get(x, y, z) == AIR and C.get(x, y + 3, z) == AIR:
                lantern_post(C.bp, x, y, z, h=3)



def gangway(C):
    """After the boss: the gangway head (u 35..40), the hatch down to the treasury, and the gangway along the
    envelope's spine (v -5..-3) to the mast crown (feet CRF)."""
    # head platform u 35..40, v -5..3 (floor DY)
    for u in range(35, 41):
        for v in range(-5, 4):
            x, z = X(u), Z(v)
            C.set(x, DY, z, TREAD if (u + v) % 5 else BRASS)
            for y in range(DY + 1, DY + 4):
                C.air(x, y, z)
            for y in range(DY - 1, AY, -1):
                b = C.get(x, y, z)
                if b is not None and b != AIR and (x, y, z) not in C.inner:
                    break
                if (x, y, z) in C.inner:
                    continue
                C.set(x, y, z, IRON)
    for u in range(35, 41):
        C.set(X(u), DY + 1, Z(-6), IRON_WALL)
        C.set(X(u), DY + 1, Z(4), IRON_WALL)
    for v in (-2, -1, 3):
        C.set(X(35), DY + 1, Z(v), IRON_WALL)
    C.set(X(40), DY + 2, Z(-6), LANT)
    C.set(X(40), DY + 2, Z(4), LANT)
    # the treasury hatch: railings round the open stair well (u 30..34, v 0..2)
    for u in range(30, 35):
        for v in (-1, 3):
            top = None
            for y in range(DY, AY, -1):
                b = C.get(X(u), y, Z(v))
                if b is not None and b != AIR:
                    top = y
                    break
            if top is not None and C.empty(X(u), top + 1, Z(v)):
                C.set(X(u), top + 1, Z(v), IRON_WALL)
    # two steps down from the head (u 34 feet 95, u 33 feet 94), then flat at feet CRF to the crown
    cells = {}
    feet = {34: CRF + 2, 33: CRF + 1}
    for u in range(-4, 35):
        f = feet.get(u, CRF)
        for v in (-5, -4, -3):
            cells[(X(u), Z(v))] = (f, "east" if u in feet else None)
    write_steps(C, cells, clear=3, floor=TREAD, fill=IRON)
    for u in range(-4, 35):
        for v in (-6, -2):
            if not (v == -2 and 30 <= u):
                C.set(X(u), feet.get(u, CRF), Z(v), IRON_WALL)
        if u % 6 == 0:
            # supports down to the skin
            for y in range(CRF - 3, 0, -1):
                if not C.empty(X(u), y, Z(-4)):
                    break
                C.set(X(u), y, Z(-4), IRON_WALL)
    for u in range(-4, 35, 8):
        C.set(X(u), CRF, Z(-6), IRON_WALL)
        C.set(X(u), CRF + 1, Z(-6), LANT)


# ------------------------------------------------------------------ the mast
def mast_w(y):
    if y <= RW:
        return 10.5 - 4.0 * y / RW
    return 6.5 - 2.5 * (y - RW) / float(CRF - 1 - RW)


def mast(C):
    """The skeletal lattice: four corner legs, a ring girder every 8, X bracing of iron bars in each panel (above
    the winch house), the legs converging on the crown."""
    for y in range(0, CRF):
        w = mast_w(y)
        wi = int(round(w))
        for sx in (-1, 1):
            for sz in (-1, 1):
                for a in (0, 1):
                    for b in (0, 1):
                        C.set(TX + sx * (wi - a), y, TZ + sz * (wi - b), IRON_BR if y % 8 else BRASS)
        if y < TF:
            continue
        band = (y % 8 == 0)
        k = y % 8
        for t in range(-wi + 2, wi - 1):
            for (x, z) in ((TX + wi, TZ + t), (TX - wi, TZ + t), (TX + t, TZ + wi), (TX + t, TZ - wi)):
                if band:
                    C.set(x, y, z, IRON)
                elif y < RW and abs(t) == int(round(wi * abs(k - 4) / 4.0)):
                    C.set(x, y, z, "iron_bars")


def mast_stair(C):
    """The newel stair inside the mast: from the roof terrace (feet TF) to the ring walkway (feet RW), 15 flights
    round the cargo-lift shaft; railings on its outer edge; the balcony half way."""
    x0, z0 = TX - 5, TZ - 5

    def outer(x, z):
        if x == x0:
            return (-1, 0)
        if x == x0 + 9:
            return (1, 0)
        if z == z0:
            return (0, -1)
        if z == z0 + 9:
            return (0, 1)
        return None
    parts, core, top_c, top_f = newel_laps(C, x0, z0, 4, TF, [4] * 15, 2, rails=outer, solid_first=True)
    assert top_f == RW, top_f
    # lamps on the core at the landings
    cx0, cz0, cx1, cz1 = core
    for f in range(TF + 2, RW, 8):
        C.set(cx0, f + 2, cz0, EDISON)
        C.set(cx1, f + 6, cz1, EDISON)
    return core


def lift_shaft(C, core):
    """The cargo lift: the core of the newel, hollow, from the sump under the winch house to the crown; the cage
    lies wrecked at the bottom in the water. An iron door opens it from inside on the ground floor."""
    cx0, cz0, cx1, cz1 = core
    for y in range(-3, CRF + 3):
        for x in range(cx0, cx1 + 1):
            for z in range(cz0, cz1 + 1):
                edge = x in (cx0, cx1) or z in (cz0, cz1)
                if edge:
                    C.set(x, y, z, BRASS if y % 8 == 0 else IRON_BR)
                elif y == -3:
                    C.set(x, y, z, IRON)
                elif x == cx0 + 1:
                    # the west column: a ledge by the door (feet 1), solid above so nobody falls onto it
                    if y <= 0 or y >= 3:
                        C.set(x, y, z, IRON if y <= 0 else IRON_BR)
                    else:
                        C.air(x, y, z)
                elif y <= 0:
                    C.set(x, y, z, WATER)
                elif y < CRF + 3:
                    C.air(x, y, z)
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            C.set(x, CRF + 3, z, IRON)
    # chains down the shaft (the cut lift cables)
    C.set(cx0 + 1, CRF + 2, cz0 + 1, CHAIN)
    # bottom door (west wall, feet 1), the button inside
    C.set(cx0, 0, cz0 + 1, IRON)
    door(C, cx0, 1, cz0 + 1, "west", wood="iron")
    C.set(cx0, 1, cz0 + 2, IRON_BR)
    C.set(cx0 + 1, 2, cz0 + 2, "stone_button[face=wall,facing=north,powered=false]")
    # top door (east wall at the crown): an open doorway onto the drop
    for z in (cz0 + 1, cz0 + 2):
        for y in range(CRF, CRF + 3):
            C.air(cx1, y, z)


def ring_walkway(C):
    """The mooring ring walkway at feet RW round the mast top: an annulus of deck plates (r 6..12), a brass
    docking ring on its rim, railings, the gangplank into the nose (east)."""
    y = RW - 1
    for x in range(TX - 14, TX + 15):
        for z in range(TZ - 14, TZ + 15):
            d = math.hypot(x - TX, z - TZ)
            inside = abs(x - TX) <= 5 and abs(z - TZ) <= 5
            if d > 12.5 or inside:
                continue
            leg = False
            C.set(x, y, z, TREAD if int(d) % 3 else IRON)
            for yy in range(RW, RW + 4):
                b = C.get(x, yy, z)
                if b == "minecraft:iron_bars" or (b and "dark_iron_plating" in b):
                    C.air(x, yy, z)
            del leg
            if 11.5 < d <= 12.5:
                if abs(z - TZ) <= 1 and x > TX:
                    continue
                rail(C, x, RW, z, "north" if abs(z - TZ) > abs(x - TX) and z < TZ else
                     "south" if abs(z - TZ) > abs(x - TX) else ("west" if x < TX else "east"))
            if 12.0 < d <= 12.5 or (11.0 < d <= 12.5 and int(math.degrees(math.atan2(z - TZ, x - TX))) % 30 < 4):
                C.set(x, y - 1, z, BRASS)
    # the legs pass through the walkway: give them back
    w = mast_w(RW)
    wi = int(round(w))
    for sx in (-1, 1):
        for sz in (-1, 1):
            for a in (0, 1):
                for b in (0, 1):
                    for yy in range(RW, RW + 4):
                        C.set(TX + sx * (wi - a), yy, TZ + sz * (wi - b), IRON_BR)
    # the exit from the newel's top landing (NE corner x TX+2..TX+4, z TZ-5..TZ-3) east through the lattice
    for x in range(TX + 5, TX + 8):
        for z in range(TZ - 5, TZ - 2):
            for yy in range(RW, RW + 3):
                if C.get(x, yy, z) and (x, yy, z) not in C.inner:
                    if not (abs(x - TX) >= wi - 1 and abs(z - TZ) >= wi - 1):
                        C.air(x, yy, z)
            C.set(x, RW - 1, z, TREAD)
    # gangplank to the nose door (x TX+12, z TZ-1..TZ+1)
    for x in range(TX + 10, NX + 1):
        for z in range(TZ - 1, TZ + 2):
            C.set(x, RW - 1, z, TREAD)
            for yy in range(RW, RW + 3):
                C.air(x, yy, z)
        for z in (TZ - 2, TZ + 2):
            if C.empty(x, RW, z):
                rail(C, x, RW, z, "north" if z < TZ else "south")
    # mooring winches and lamps on the ring
    for (dx, dz) in ((9, 7), (-9, 7), (-9, -7), (0, 10), (0, -10), (-10, 0)):
        x, z = TX + dx, TZ + dz
        if C.empty(x, RW, z):
            C.set(x, RW, z, IRON)
            C.set(x, RW + 1, z, LANT)
    C.bp.chest(TX - 8, RW, TZ + 9, "north", loot=LOOT + "ag_mast")


def crown(C):
    """The mast crown (feet CRF): a round platform r 8, the docking cone above, the spire and its lamp; the
    gangway lands on its east side; the cargo-lift door."""
    y = CRF - 1
    for x in range(TX - 9, TX + 10):
        for z in range(TZ - 9, TZ + 10):
            d = math.hypot(x - TX, z - TZ)
            if d > 8.4:
                continue
            core = abs(x - TX + 0.5) <= 2 and abs(z - TZ + 0.5) <= 2
            if core:
                continue
            C.set(x, y, z, TREAD if int(d) % 3 else BRASS)
            for yy in range(CRF, CRF + 4):
                if C.get(x, yy, z) is None:
                    C.air(x, yy, z)
            if 7.5 < d <= 8.4 and not (x > TX and -6 <= z - TZ <= -2):
                rail(C, x, CRF, z, "north" if abs(z - TZ) >= abs(x - TX) and z < TZ else
                     "south" if abs(z - TZ) >= abs(x - TX) else ("west" if x < TX else "east"))
    # brackets under the rim
    for a in range(0, 360, 30):
        t = math.radians(a)
        x, z = TX + int(round(math.cos(t) * 7)), TZ + int(round(math.sin(t) * 7))
        C.set(x, y - 1, z, IRON)
        C.set(x, y - 2, z, IRON_WALL)
    # the docking cone over the lift: a brass cone, the spire, the lamp
    for k in range(0, 8):
        rr = 3.2 - k * 0.38
        for x in range(TX - 4, TX + 4):
            for z in range(TZ - 4, TZ + 4):
                if math.hypot(x - TX + 0.5, z - TZ + 0.5) <= rr:
                    C.set(x, CRF + 3 + k, z, BRASS if k % 3 else VERD)
    for yy in range(CRF + 11, CRF + 14):
        C.set(TX, yy, TZ, IRON_WALL)
    C.set(TX, CRF + 14, TZ, "lantern[hanging=false,waterlogged=false]")
    # the mooring arm reaching out east to the nose
    for x in range(TX + 3, TX + 12):
        C.set(x, CRF + 3, TZ, IRON if x % 2 else BRASS)
    for yy in range(RW + 3, CRF + 3):
        if C.empty(TX + 11, yy, TZ):
            C.set(TX + 11, yy, TZ, CHAIN)
    # lamps
    for (dx, dz) in ((-6, 3), (-6, -3), (3, 6)):
        if C.empty(TX + dx, CRF, TZ + dz):
            C.set(TX + dx, CRF, TZ + dz, IRON_WALL)
            C.set(TX + dx, CRF + 1, TZ + dz, LANT)


def balcony(C):
    """Half way up (feet 49): the SE landing opens onto a quarter-ring balcony outside the lattice (a vista)."""
    f = TF + 32
    y = f - 1
    w = mast_w(f)
    wi = int(round(w))
    for x in range(TX + 2, TX + wi + 5):
        for z in range(TZ + 2, TZ + wi + 5):
            dx, dz = x - TX, z - TZ
            if dx <= 4 and dz <= 4:
                continue
            if max(dx, dz) > wi + 3:
                continue
            C.set(x, y, z, TREAD if (dx + dz) % 4 else BRASS)
            for yy in range(f, f + 3):
                if C.get(x, yy, z) in ("minecraft:iron_bars",) or (C.get(x, yy, z) and
                                                                  "dark_iron_plating" == C.get(x, yy, z).split(":")[1]):
                    C.air(x, yy, z)
                elif C.get(x, yy, z) is None:
                    C.air(x, yy, z)
            if max(dx, dz) == wi + 3:
                rail(C, x, f, z, "east" if dx >= dz else "south")
    # the legs stay
    for a in (0, 1):
        for b in (0, 1):
            for yy in range(f, f + 3):
                C.set(TX + wi - a, yy, TZ + wi - b, IRON_BR)
    # the corner landing's outer railing gives way to the balcony
    for (x, z) in ((TX + 4, TZ + 2), (TX + 4, TZ + 3), (TX + 4, TZ + 4), (TX + 2, TZ + 4), (TX + 3, TZ + 4)):
        if C.get(x, f, z) and "railing" in C.get(x, f, z):
            C.air(x, f, z)
    C.bp.chest(TX + wi + 2, f, TZ + wi + 2, "north", loot=LOOT + "ag_mast")
    C.set(TX + wi + 3, f, TZ + 3, IRON_WALL)
    C.set(TX + wi + 3, f + 1, TZ + 3, LANT)
    C.set(TX + 3, f, TZ + wi + 3, IRON_WALL)
    C.set(TX + 3, f + 1, TZ + wi + 3, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    C.bp.spawner(TX + wi + 1, f, TZ + 5, MOB_DRONE)


# ------------------------------------------------------------------ the winch house
WX0, WX1, WZ0, WZ1 = TX - 13, TX + 13, TZ - 13, TZ + 13


def winch_house(C):
    """Two storeys round the foot of the mast (feet 1 and 9) and the roof terrace (feet TF): rust-rock plinth,
    dark iron brick walls grouped in 1-3-1 bays, brass string courses at the floor lines, crenellated parapet."""
    for x in range(WX0, WX1 + 1):
        for z in range(WZ0, WZ1 + 1):
            edge = x in (WX0, WX1) or z in (WZ0, WZ1)
            for y in range(-4, TF + 1):
                if edge:
                    if y > TF - 1:
                        if (x + z) % 2 == 0:
                            C.set(x, y, z, IRON_BR)
                        continue
                    a = (z - WZ0) if x in (WX0, WX1) else (x - WX0)
                    bay = a in (0, 4, 9, 17, 22, 26)
                    if y <= 2:
                        spec = RUST_BR if y > -1 else RUST
                    elif y in (8, 16):
                        spec = BRASS
                    elif bay:
                        spec = IRON
                    elif y in (4, 5, 11, 12, 13) and a % 4 in (1, 2) and 4 < a < 22:
                        spec = "glass_pane"
                    else:
                        spec = IRON_BR
                    C.set(x, y, z, spec)
                else:
                    if y < 0:
                        C.set(x, y, z, RUST)
                    elif y == 0 or y == 8:
                        C.set(x, y, z, TREAD)
                    elif y == 7 or y == 15:
                        C.set(x, y, z, IRON)
                    elif y == 16:
                        C.set(x, y, z, TREAD if (x + z) % 5 else IRON)
                    elif y < 16:
                        C.air(x, y, z)
    # pilasters: buttresses at the bay lines (2 deep), the corner piers
    for a in (4, 9, 17, 22):
        for y in range(0, TF):
            for (x, z, fc) in ((WX0 + a, WZ1 + 1, "s"), (WX0 + a, WZ0 - 1, "n"), (WX0 - 1, WZ0 + a, "w"),
                               (WX1 + 1, WZ0 + a, "e")):
                C.set(x, y, z, IRON if y % 8 else BRASS)
    for (x, z) in ((WX0 - 1, WZ0 - 1), (WX1 + 1, WZ0 - 1), (WX0 - 1, WZ1 + 1), (WX1 + 1, WZ1 + 1)):
        for y in range(-1, TF + 2):
            C.set(x, y, z, RUST_BR if y < 3 else IRON_BR)
    # the main door (south, x TX-1..TX+1) under a brass lintel; the west door to the gas works; the upper west door
    for x in range(TX - 1, TX + 2):
        for y in range(1, 5):
            C.air(x, y, WZ1)
        C.set(x, 5, WZ1, BRASS)
        C.set(x, 0, WZ1 + 1, TREAD)
    C.set(TX, 6, WZ1 + 1, EDISON)
    for z in range(TZ - 1, TZ + 2):
        for y in range(1, 4):
            C.air(WX0, y, z)
        for y in range(9, 12):
            C.air(WX0, y, z)
    # stair 1: ground -> upper floor, x WX0+1..WX0+3, rising north from z TZ+4 (feet 2) to TZ-3 (feet 9)
    cells = {}
    for z in range(TZ - 6, TZ + 5):
        f = 1 + (TZ + 5 - z) if z >= TZ - 3 else 9
        for x in range(WX0 + 1, WX0 + 4):
            cells[(x, z)] = (min(f, 9), "north" if z >= TZ - 3 else None)
    write_steps(C, cells, fill=IRON, solid_to=1)
    for z in range(TZ - 3, TZ + 5):
        rail(C, WX0 + 4, 9, z, "east")
    # stair 2: upper -> roof, x WX1-3..WX1-1, rising south from z TZ-4 (feet 10) to TZ+3 (feet 17)
    cells = {}
    for z in range(TZ - 6, TZ + 7):
        if z <= TZ - 5:
            f, fc = 9, None
        elif z <= TZ + 3:
            f, fc = 10 + (z - (TZ - 4)), "south"
        else:
            f, fc = TF, None
        for x in range(WX1 - 3, WX1):
            cells[(x, z)] = (f, fc)
    write_steps(C, cells, fill=IRON, solid_to=9)
    for z in range(TZ - 4, TZ + 4):
        rail(C, WX1 - 4, TF, z, "west")
    # ground floor: the mooring winch (a drum along x at z TZ-8), its steam engine, chains up into the ceiling
    for x in range(TX - 7, TX + 8):
        for y in range(1, 7):
            for z in range(TZ - 11, TZ - 5):
                d = math.hypot(y - 3.5, z - (TZ - 8))
                if d <= 2.6:
                    end = x in (TX - 7, TX + 7)
                    C.set(x, y, z, BRASS if end or x % 4 == 0 else ("spruce_planks" if d > 1.6 else IRON))
    for x in (TX - 8, TX + 8):
        for y in range(1, 6):
            C.set(x, y, TZ - 8, IRON_WALL if y < 5 else IRON)
    for x in (TX - 5, TX - 1, TX + 3):
        for y in range(6, 7):
            C.set(x, y, TZ - 7, CHAIN)
    # the steam engine at the NE corner: boiler, flywheel, gauges
    for x in range(TX + 9, TX + 12):
        for z in range(TZ - 11, TZ - 8):
            for y in range(1, 5):
                C.set(x, y, z, SMOKE if y < 4 else IRON)
    C.set(TX + 10, 1, TZ - 8, "blast_furnace[facing=south,lit=true]")
    C.set(TX + 9, 3, TZ - 8, GAUGE)
    C.set(TX + 11, 3, TZ - 8, GAUGE)
    for y in range(5, 7):
        C.set(TX + 10, y, TZ - 10, PIPES)
    # the cargo-lift door is on the core's west face; a cage gate rail round the sump
    C.set(TX - 3, 1, TZ - 3, "barrel[facing=up,open=false]")
    C.set(TX - 4, 1, TZ - 3, "barrel[facing=up,open=false]")
    C.set(TX - 4, 2, TZ - 3, "barrel[facing=up,open=false]")
    # lamps
    for (x, z) in ((TX - 6, TZ + 4), (TX + 6, TZ + 4), (TX - 6, TZ - 3), (TX + 6, TZ - 3), (TX, TZ + 8)):
        lamp_hang(C, x, 5, z)
    C.bp.chest(TX + 11, 1, TZ + 10, "west", loot=LOOT + "ag_winch")
    C.bp.spawner(TX + 7, 1, TZ + 8, MOB_MITE)
    for (x, z) in ((TX - 11, TZ + 11), (TX - 10, TZ + 11), (TX - 11, TZ + 10), (TX + 11, TZ + 11)):
        C.set(x, 1, z, "barrel[facing=up,open=false]")
    # upper floor: the moorings master's office (SW), the gear room (N), the bunk room (SE)
    for x in range(WX0 + 5, TX - 3):
        for y in range(9, 15):
            C.set(x, y, TZ + 5, MAHOGANY if y < 14 else BRASS)
    for z in range(TZ + 5, WZ1):
        for y in range(9, 15):
            C.set(TX - 3, y, z, MAHOGANY if y < 14 else BRASS)
    door(C, TX - 6, 9, TZ + 5, "south")
    C.set(TX - 8, 9, TZ + 10, TABLE)
    C.set(TX - 8, 9, TZ + 9, f"{CHAIR}[facing=south]")
    C.set(TX - 8, 10, TZ + 10, LANT)
    C.bp.chest(TX - 11, 9, TZ + 11, "east", loot=LOOT + "ag_winch")
    C.set(TX - 5, 9, TZ + 11, "chiseled_bookshelf[facing=north,slot_0_occupied=false,slot_1_occupied=false,"
                              "slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,"
                              "slot_5_occupied=false]")
    C.set(TX - 7, 13, TZ + 8, HANG_LAMP)
    # gear room: gear panels on the north wall, a control desk with levers
    for x in range(TX - 8, TX + 9):
        for y in range(10, 14):
            C.set(x, y, WZ0, GEAR if (x + y) % 3 else BRASS)
    for x in range(TX - 4, TX + 5):
        C.set(x, 9, TZ - 10, IRON)
        if x % 2 == 0:
            C.set(x, 10, TZ - 10, "lever[face=floor,facing=south,powered=false]")
    # bunk room SE
    for z in (TZ + 8, TZ + 11):
        C.bp.bed(TX + 2, 9, z, "east", color="gray")
    C.set(TX + 5, 9, TZ + 11, "barrel[facing=up,open=false]")
    for (x, z) in ((TX - 6, TZ - 6), (TX + 6, TZ - 6), (TX + 6, TZ + 6)):
        lamp_hang(C, x, 13, z)
    # roof terrace: crates, a lamp at the newel's foot
    C.set(TX + 8, TF, TZ + 9, "barrel[facing=up,open=false]")
    C.set(TX + 9, TF, TZ + 9, "barrel[facing=up,open=false]")
    for (x, z) in ((TX + 7, TZ + 7), (TX - 7, TZ + 7), (TX - 7, TZ - 7), (TX + 7, TZ - 7)):
        C.set(x, TF, z, IRON_WALL)
        C.set(x, TF + 1, z, LANT)


def disk_x(C, x, yc, zc, r, spec, only_air=True):
    """A disc in the plane x (a gear, a flange), centre (yc, zc)."""
    ri = int(math.ceil(r)) + 1
    for y in range(int(yc) - ri, int(yc) + ri + 2):
        for z in range(int(zc) - ri, int(zc) + ri + 2):
            d = math.hypot(y - yc, z - zc)
            if d <= r + 0.3:
                sp = spec(y, z, d) if callable(spec) else spec
                if only_air:
                    put(C, x, y, z, sp)
                else:
                    C.set(x, y, z, sp)


def gear_x(C, x, yc, zc, r, seed=0):
    """A gear wheel in the plane x: a toothed rim (teeth every other cell round the rim), brass spokes, an iron hub."""
    def spec(y, z, d):
        if d < 0.8:
            return IRON
        if d > r - 0.7:
            ang = math.atan2(y - yc, z - zc)
            return GEAR if int(round(ang * r)) % 2 == 0 else BRASS
        dy, dz = abs(y - yc), abs(z - zc)
        return BRASS if dy < 0.6 or dz < 0.6 else None
    ri = int(math.ceil(r)) + 1
    for y in range(int(yc) - ri, int(yc) + ri + 2):
        for z in range(int(zc) - ri, int(zc) + ri + 2):
            d = math.hypot(y - yc, z - zc)
            if d <= r + 0.3:
                sp = spec(y, z, d)
                if sp:
                    put(C, x, y, z, sp)


def winch_room(C):
    """The winch house ground floor was a bare hall round the mast's core: the mooring winch gets flanges and its
    cable spool, a gear train drives the cargo lift on the core's east face, a boiler with its firebox and flue
    stands in the south-west corner, a workbench and tool racks along the south wall, lanterns on the machines."""
    # the winch drum: bigger brass flanges at both ends
    for x in (TX - 8, TX + 8):
        disk_x(C, x, 3.5, TZ - 8, 2.9, lambda y, z, d: BRASS if d > 2.0 else IRON)
    # the cable spool beside it: axis z, two flanges, the reel of cable between them, on iron chocks
    sx, sy = TX + 9, 3.5
    for z in (TZ - 4, TZ):
        for y in range(1, 7):
            for x in range(sx - 3, sx + 4):
                d = math.hypot(x - sx, y - sy)
                if d <= 2.6:
                    put(C, x, y, z, BRASS if d > 1.8 else IRON)
    for z in range(TZ - 3, TZ):
        for y in range(1, 7):
            for x in range(sx - 3, sx + 4):
                d = math.hypot(x - sx, y - sy)
                if d <= 0.8:
                    put(C, x, y, z, IRON)
                elif d <= 1.9:
                    put(C, x, y, z, "iron_chain[axis=x,waterlogged=false]" if (y + z) % 2 else
                        "iron_chain[axis=y,waterlogged=false]")
    # the gear train on the core's east face: the great wheel, an idler and the motor's pinion
    gx = TX + 2
    gear_x(C, gx, 3.5, TZ - 1.5, 2.6)
    gear_x(C, gx, 2.0, TZ + 3.0, 1.6)
    gear_x(C, gx, 5.0, TZ - 5.5, 1.4)
    # the motor driving it: a small steam engine on the floor east of the train
    for (x, z) in ((gx + 1, TZ + 3), (gx + 2, TZ + 3)):
        put(C, x, 1, z, SMOKE)
        put(C, x, 2, z, IRON)
    put(C, gx + 1, 3, TZ + 3, GAUGE)
    put(C, gx + 2, 3, TZ + 3, PIPES)
    for y in range(4, 7):
        put(C, gx + 2, y, TZ + 3, PIPES)
    # the boiler: a horizontal drum on a brick firebox in the south-west corner, its flue up through the ceiling
    bx0, bx1, bz, by = WX0 + 4, WX0 + 9, WZ1 - 5, 3.0
    for x in range(bx0, bx1 + 1):
        for y in range(1, 6):
            for z in range(bz - 2, bz + 3):
                d = math.hypot(y - by, z - bz)
                if x == bx0:
                    if d <= 2.0:
                        put(C, x, y, z, SMOKE if y <= 2 else IRON)
                elif d <= 2.0:
                    put(C, x, y, z, BRASS if x in (bx0 + 1, bx1) or (x - bx0) % 3 == 0 else COPPER)
    for x in range(bx0 + 1, bx1 + 1):
        for z in range(bz - 2, bz + 3):
            put(C, x, 1, z, SMOKE if z in (bz - 2, bz + 2) else IRON)        # the boiler's cradle
    C.set(bx0, 1, bz, "blast_furnace[facing=west,lit=true]") if C.get(bx0, 1, bz) == SMOKE else None
    for y in range(6, 7):
        put(C, bx1 - 1, y, bz, PIPES)
    put(C, bx0 + 2, 5, bz, GAUGE)
    put(C, bx0 + 4, 5, bz, GAUGE)
    put(C, bx1 + 1, 2, bz, f"{VALVE}[facing=east]")
    # the workbench and the tool racks along the south wall, west of the door
    z = WZ1 - 1
    for (x, spec) in ((TX - 9, "smithing_table"), (TX - 8, TABLE), (TX - 7, "anvil[facing=east]"),
                      (TX - 6, "crafting_table"), (TX - 5, "grindstone[face=floor,facing=north]")):
        put(C, x, 1, z, spec)
    for x in range(TX - 9, TX - 4):
        put(C, x, 3, z, f"{SHELF}[facing=north]")
        put(C, x, 4, z, f"{COG}[facing=north]" if x % 2 else f"{SHELF}[facing=north]")
    put(C, TX - 8, 2, z, LANT)
    # a rack of spare chain and hooks hanging from the ceiling by the door
    for x in (TX + 3, TX + 5):
        for y in range(3, 7):
            put(C, x, y, WZ1 - 2, CHAIN)
    # lanterns on the boiler, lamps behind the drum and in the dark corners
    put(C, bx0 + 3, 6, bz, LANT)
    for (x, z) in ((WX0 + 2, WZ0 + 2), (TX - 4, WZ0 + 1), (TX + 4, WZ0 + 1), (WX1 - 2, WZ0 + 2), (WX1 - 1, TZ - 2),
                   (WX0 + 2, WZ1 - 3)):
        if C.get(x, 5, z) == AIR and C.get(x, 6, z) == AIR and C.get(x, 7, z) not in (None, AIR):
            lamp_hang(C, x, 5, z)


# ------------------------------------------------------------------ the gas works
GX0, GX1, GZ0, GZ1 = -100, -71, TZ - 9, TZ + 9
G1 = (-86, -53, 13, 20)       # gasometers: centre x, z, frame radius, bell top y
G2 = (-84, 25, 14, 9)


def gas_works(C):
    """The retort house: a brick hall (ground floor feet 1, open to its trusses), two rows of retort benches, coal
    bunkers, the stair up to the east gallery (feet 9) and the covered bridge to the winch house's upper floor."""
    top = 12
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            edge = x in (GX0, GX1) or z in (GZ0, GZ1)
            for y in range(-3, top + 1):
                if edge:
                    a = (z - GZ0) if x in (GX0, GX1) else (x - GX0)
                    if y <= 1:
                        spec = RUST_BR
                    elif y == top or y == 8:
                        spec = IRON_BR
                    elif a % 6 == 0:
                        spec = IRON_BR
                    elif 3 <= y <= 6 and a % 6 in (2, 3, 4) and z in (GZ0, GZ1):
                        spec = "glass_pane" if y > 3 else SMOKE
                    else:
                        spec = SMOKE if hash01(x, y + z, 121) > 0.12 else SOOT
                    C.set(x, y, z, spec)
                else:
                    if y < 0:
                        C.set(x, y, z, RUST)
                    elif y == 0:
                        C.set(x, y, z, TREAD if (x + z) % 7 else IRON)
                    else:
                        C.air(x, y, z)
    # the gable roof (ridge along x) on dark iron trusses
    for x in range(GX0 - 1, GX1 + 2):
        for k in range(0, 11):
            for z in (GZ0 - 1 + k, GZ1 + 1 - k):
                C.set(x, top + 1 + k, z, stair(SLATE_ST, "south" if z < TZ else "north"))
            for z in range(GZ0 + k, GZ1 + 1 - k):
                if k > 0 and x in (GX0 - 1, GX1 + 1):
                    C.set(x, top + k, z, SMOKE)
        C.set(x, top + 11, TZ, SLATE_SL + "[type=bottom,waterlogged=false]")
        if (x - GX0) % 6 == 0:
            for z in range(GZ0 + 1, GZ1):
                C.set(x, top, z, IRON)
            for k in range(1, 9):
                C.set(x, top + k, TZ, IRON_WALL)
    for z in range(GZ0, GZ1 + 1):
        for k in range(0, 11):
            pass
    # gable ends filled
    for x in (GX0, GX1):
        for k in range(1, 11):
            for z in range(GZ0 + k, GZ1 + 1 - k):
                C.set(x, top + k, z, SMOKE if (k + z) % 5 else IRON_BR)
    # chimneys
    for (cx, cz) in ((-94, GZ0 + 3), (-80, GZ1 - 3)):
        for y in range(top, top + 18):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if dx == 0 and dz == 0 and y > top:
                        C.air(cx, y, cz)
                    else:
                        C.set(cx + dx, y, cz + dz, BRASS if y % 6 == 0 else SOOT)
        C.set(cx, top, cz, "hay_block[axis=y]")
        C.set(cx, top + 1, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # doors: east (to the winch house, ground), south (the yard), the bridge door (east, feet 9)
    for z in range(TZ - 1, TZ + 2):
        for y in range(1, 4):
            C.air(GX1, y, z)
    for x in range(-87, -84):
        for y in range(1, 5):
            C.air(x, y, GZ1)
    for z in range(TZ - 1, TZ + 2):
        for y in range(9, 12):
            C.air(GX1, y, z)
    # the yard between the hall and the winch house: paving
    for x in range(GX1, WX0 + 1):
        for z in range(TZ - 3, TZ + 4):
            C.set(x, 0, z, TREAD if (x + z) % 3 else IRON)
            for y in range(1, 4):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
    # retort benches: two rows of brick ovens, furnace doors facing the aisle
    for (z0, z1, fc) in ((GZ0 + 1, GZ0 + 4, "south"), (GZ1 - 4, GZ1 - 1, "north")):
        for x in range(GX0 + 2, GX1 - 16):
            for z in range(z0, z1 + 1):
                for y in range(1, 6):
                    front = (z == z1 if fc == "south" else z == z0)
                    if front and y in (2, 3) and x % 3 == 0:
                        C.set(x, y, z, f"furnace[facing={fc},lit=true]")
                    else:
                        C.set(x, y, z, SMOKE if y < 5 else IRON)
        for x in range(GX0 + 2, GX1 - 16, 3):
            for y in range(6, top):
                zz = z0 + 1 if fc == "south" else z1 - 1
                C.set(x, y, zz, PIPES)
    # the charging aisle: coal heaps and a charging cart
    for x in (-96, -95, -90):
        C.set(x, 1, TZ - 2, "coal_block")
        C.set(x, 1, TZ + 2, "coal_block")
    C.set(-95, 2, TZ - 2, "coal_block")
    # the gallery at the east end (x GX1-5..GX1-1, feet 9) and its stair (north wall, rising east)
    for x in range(GX1 - 5, GX1):
        for z in range(GZ0 + 1, GZ1):
            C.set(x, 8, z, TREAD)
            C.set(x, 7, z, IRON)
    for z in range(GZ0 + 1, GZ1):
        rail(C, GX1 - 6, 9, z, "west")
    cells = {}
    for x in range(GX1 - 14, GX1 - 5):
        f = 1 + (x - (GX1 - 14)) if x < GX1 - 6 else 9
        for z in range(GZ0 + 5, GZ0 + 8):
            cells[(x, z)] = (min(f, 9), "east" if x < GX1 - 6 else None)
    write_steps(C, cells, fill=SMOKE, solid_to=1)
    for x in range(GX1 - 13, GX1 - 5):
        rail(C, x, 1 + (x - (GX1 - 14)) if x < GX1 - 6 else 9, GZ0 + 8, "south")
    # keep the stair clear of the north bench
    # the valve office on the gallery: a chest, gauges
    C.bp.chest(GX1 - 2, 9, GZ1 - 1, "north", loot=LOOT + "ag_gasworks")
    C.set(GX1 - 1, 10, GZ1 - 2, GAUGE)
    C.set(GX1 - 4, 9, GZ1 - 1, "barrel[facing=up,open=false]")
    for x in range(GX0 + 4, GX1 - 3, 7):
        lamp_hang(C, x, 9, TZ, drop=3)
    C.bp.spawner(-84, 1, TZ, MOB_GUNNER)
    C.bp.chest(GX0 + 1, 1, TZ + 1, "east", loot=LOOT + "ag_gasworks")
    # the covered bridge to the winch house (x GX1+1..WX0-1, feet 9)
    for x in range(GX1 + 1, WX0):
        for z in range(TZ - 2, TZ + 3):
            edge = abs(z - TZ) == 2
            C.set(x, 8, z, IRON if edge else TREAD)
            for y in range(9, 12):
                if edge:
                    C.set(x, y, z, "glass_pane" if y == 10 else IRON)
                else:
                    C.air(x, y, z)
            C.set(x, 12, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if not edge else IRON)
        C.set(x, 7, TZ, stair(IRON_STAIRS, "north", "top"))


SLATE_ST, SLATE_SL = W + "slate_roof_tile_stairs", W + "slate_roof_tile_slab"


def gasometer(C, g, seed):
    """A column-guided gasometer: the brick tank wall, the telescoping bell (solid, riveted, a domed crown) and the
    lattice guide frame of twelve columns with three tiers of ring girders and X bracing."""
    cx, cz, rf, btop = g
    rb = rf - 2
    hf = 32 if rf == 13 else 30
    for x in range(cx - rf - 2, cx + rf + 3):
        for z in range(cz - rf - 2, cz + rf + 3):
            d = math.hypot(x - cx, z - cz)
            # tank wall
            if rb - 0.2 < d <= rb + 1.2:
                for y in range(-2, 4):
                    C.set(x, y, z, RUST_BR if y < 3 else SMOKE_SLAB_B)
            # the bell
            if d <= rb - 0.15:
                for y in range(-2, btop + 1):
                    shell = d > rb - 1.5 or y == btop
                    if shell:
                        spec = IRON_BR if (y % 5 == 0) else (RUST if hash01(x * 3 + y, z, seed) < 0.12 else IRON)
                    else:
                        spec = IRON
                    C.set(x, y, z, spec)
                # the crown dome
                dh = int(round(3.2 * math.sqrt(max(0.0, 1 - (d / (rb - 0.15)) ** 2))))
                for y in range(btop + 1, btop + 1 + dh):
                    C.set(x, y, z, VERD if hash01(x, z, seed + 1) < 0.5 else IRON)
            if d <= rb + 1.2:
                C.set(x, -3, z, RUST)
    # columns and rings
    for k in range(12):
        a = math.radians(k * 30 + 15)
        x, z = cx + int(round(math.cos(a) * rf)), cz + int(round(math.sin(a) * rf))
        for y in range(0, hf + 1):
            C.set(x, y, z, IRON_BR if y % 10 else BRASS)
        C.set(x, hf + 1, z, BRASS)
    for yr in (10, 20, hf):
        for a10 in range(0, 3600, 15):
            a = math.radians(a10 / 10.0)
            x, z = cx + int(round(math.cos(a) * rf)), cz + int(round(math.sin(a) * rf))
            C.set(x, yr, z, IRON)
    # X bracing between columns in each tier (iron bars along the chord)
    for k in range(12):
        a0, a1 = math.radians(k * 30 + 15), math.radians(k * 30 + 45)
        p0 = (cx + math.cos(a0) * rf, cz + math.sin(a0) * rf)
        p1 = (cx + math.cos(a1) * rf, cz + math.sin(a1) * rf)
        for (y0, y1) in ((0, 10), (10, 20), (20, hf)):
            if hash01(k, y0, seed + 3) < 0.15:
                continue                     # a panel lost its bracing
            for i in range(0, 21):
                t = i / 20.0
                for (ya, yb) in ((y0, y1), (y1, y0)):
                    x = int(round(p0[0] + (p1[0] - p0[0]) * t))
                    z = int(round(p0[1] + (p1[1] - p0[1]) * t))
                    y = int(round(ya + (yb - ya) * t))
                    if C.empty(x, y, z):
                        C.set(x, y, z, "iron_bars")


SMOKE_SLAB_B = W + "smokestack_brick_slab[type=bottom,waterlogged=false]"


def gas_pipes(C):
    """Big gas mains on trestles from both gasometers to the retort house."""
    for (x0, z0, x1, z1) in ((-86, -41, -86, GZ0), (-84, 12, -84, GZ1)):
        lo, hi = min(z0, z1), max(z0, z1)
        for z in range(lo, hi + 1):
            for dx in (0, 1):
                for y in (6, 7):
                    if C.empty(x0 + dx, y, z):
                        C.set(x0 + dx, y, z, COPPER if z % 5 else BRASS)
            if z % 6 == 0:
                for y in range(1, 6):
                    if C.empty(x0, y, z):
                        C.set(x0, y, z, IRON_WALL)
                    if C.empty(x0 + 1, y, z):
                        C.set(x0 + 1, y, z, IRON_WALL)
    # a valve house by G1
    for x in range(-79, -74):
        for z in range(-43, -38):
            edge = x in (-79, -75) or z in (-43, -39)
            for y in range(0, 6):
                if y == 0:
                    C.set(x, y, z, TREAD)
                elif y == 5:
                    C.set(x, y, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if not edge else IRON)
                elif edge:
                    C.set(x, y, z, plate(x, y, z, 7))
                else:
                    C.air(x, y, z)
    for y in (1, 2):
        C.air(-77, y, -39)
    door(C, -77, 1, -39, "south")
    C.set(-76, 2, -42, f"{VALVE}[facing=south]")
    C.set(-78, 1, -42, PIPES)
    C.set(-78, 2, -42, GAUGE)
    C.bp.chest(-76, 1, -41, "west", loot=LOOT + "ag_gasworks")
    C.set(-77, 4, -41, HANG_LAMP)


# ------------------------------------------------------------------ the shanty town and the market
MKT = (-20, 31)               # market square centre


def shanty(C, x0, z0, w, d, door_side, roof, seed, loot=None, spawner=None, h=4):
    """A shack of salvaged hull plates: patchwork walls, a door, a porthole, a roof of canvas (a gas-bag tent),
    iron trapdoors (hull plates) or a curved hull section; a bed or crates inside."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 0, z, "spruce_planks" if (x + z) % 4 else "coarse_dirt")
            C.set(x, -1, z, "dirt")
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(1, h + 1):
                if edge:
                    C.set(x, y, z, plate(x, y, z, seed))
                else:
                    C.air(x, y, z)
    # roof
    if roof == "tent":
        col = TENT[seed % len(TENT)]
        if w >= d:
            for x in range(x0 - 1, x1 + 2):
                for k in range(0, (d + 1) // 2 + 1):
                    for z in (z0 - 1 + k, z1 + 1 - k):
                        C.set(x, h + 1 + k, z, col if (x + k) % 5 else "white_wool")
                for zz in range(z0 + (d + 1) // 2 - 0, z1 - (d + 1) // 2 + 1):
                    C.set(x, h + 1 + (d + 1) // 2, zz, col)
            for k in range(1, (d + 1) // 2 + 1):
                for z in range(z0 + k - 1, z1 - k + 2):
                    for x in (x0, x1):
                        if C.empty(x, h + k, z):
                            C.set(x, h + k, z, plate(x, h + k, z, seed))
        else:
            for z in range(z0 - 1, z1 + 2):
                for k in range(0, (w + 1) // 2 + 1):
                    for x in (x0 - 1 + k, x1 + 1 - k):
                        C.set(x, h + 1 + k, z, col if (z + k) % 5 else "white_wool")
            for k in range(1, (w + 1) // 2 + 1):
                for x in range(x0 + k - 1, x1 - k + 2):
                    for z in (z0, z1):
                        if C.empty(x, h + k, z):
                            C.set(x, h + k, z, plate(x, h + k, z, seed))
    elif roof == "plate":
        for x in range(x0 - 1, x1 + 2):
            for z in range(z0 - 1, z1 + 2):
                C.set(x, h + 1, z, IRON_SLAB + "[type=bottom,waterlogged=false]" if hash01(x, z, seed) < 0.7
                      else W + "copper_plating_slab[type=bottom,waterlogged=false]")
    else:   # a curved hull section as a barrel roof (along the long side)
        along_x = w >= d
        span = d if along_x else w
        c0 = (z0 + z1) / 2.0 if along_x else (x0 + x1) / 2.0
        rr = span / 2.0 + 0.6
        for a in range(x0 - 1, x1 + 2) if along_x else range(z0 - 1, z1 + 2):
            for b in range(int(c0 - rr) - 1, int(c0 + rr) + 2):
                dd = abs(b - c0)
                if dd > rr:
                    continue
                y = h + int(round(math.sqrt(max(0.0, rr * rr - dd * dd)) * 0.6))
                x, z = (a, b) if along_x else (b, a)
                C.set(x, y, z, BRASS if a % 4 == 0 else IRON)
                for yy in range(h + 1, y):
                    if (along_x and x in (x0, x1)) or (not along_x and z in (z0, z1)):
                        C.set(x, yy, z, plate(x, yy, z, seed))
                    elif C.get(x, yy, z) is None and min(x - x0, x1 - x, z - z0, z1 - z) >= 0:
                        C.air(x, yy, z)
    # door and porthole
    cxm, czm = (x0 + x1) // 2, (z0 + z1) // 2
    dpos = {"south": (cxm, z1), "north": (cxm, z0), "east": (x1, czm), "west": (x0, czm)}[door_side]
    for y in (1, 2):
        C.air(dpos[0], y, dpos[1])
    door(C, dpos[0], 1, dpos[1], door_side, wood="spruce" if seed % 2 else "dark_oak")
    wpos = {"south": (cxm, z0), "north": (cxm, z1), "east": (x0, czm), "west": (x1, czm)}[door_side]
    C.set(wpos[0], 2, wpos[1], "glass_pane")
    # inside
    ix, iz = x0 + 1, z0 + 1
    if seed % 3 == 0 and w >= 5 and d >= 4:
        C.bp.bed(ix, 1, iz, "east" if w > d else "south", color=("brown", "gray", "red")[seed % 3])
    else:
        C.set(ix, 1, iz, "barrel[facing=up,open=false]")
    if loot:
        C.bp.barrel(x1 - 1, 1, z1 - 1 if door_side != "south" else z0 + 1, loot=LOOT + loot)
    if spawner:
        C.bp.spawner(cxm, 1, czm, spawner)
    else:
        C.set(cxm, h, czm, HANG_LAMP)


def stall(C, x0, z0, w, d, seed, goods):
    """A market stall: fence posts, a canvas awning of gas-bag fabric, a counter of barrels and trapdoors."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    col = TENT[(seed + 3) % len(TENT)]
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(1, 4):
            C.set(x, y, z, "spruce_fence" if y < 3 else "spruce_fence")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            C.set(x, 4, z, col if (x + z + seed) % 3 else "white_wool")
    for x in range(x0 + 1, x1):
        C.set(x, 1, z1, "barrel[facing=up,open=false]" if x % 2 else "spruce_planks")
        C.set(x, 2, z1, goods[(x + seed) % len(goods)])
    C.set(x0 + 1, 3, z0 + 1, LANT_H) if d > 2 else None


def market(C):
    """The market square (the hub): paved with deck plates salvaged from the wrecks, stalls round it, a fountain
    made of a gas-cell tank, propeller windmills, the waystone, lamp posts."""
    mx, mz = MKT
    for x in range(mx - 13, mx + 14):
        for z in range(mz - 10, mz + 11):
            if abs(x - mx) > 12 and abs(z - mz) > 9:
                continue
            h = hash01(x, z, 131)
            C.set(x, 0, z, TREAD if h < 0.45 else IRON if h < 0.6 else "spruce_planks" if h < 0.85 else
                  "coarse_dirt")
            for y in range(1, 4):
                if C.get(x, y, z) is None:
                    C.air(x, y, z)
    # the waystone on a brass plinth at the north side of the square
    C.set(mx, 0, mz - 7, BRASS)
    C.set(mx, 1, mz - 7, MOD["waystone"])
    for (dx, dz) in ((-2, -7), (2, -7)):
        C.set(mx + dx, 1, mz + dz, IRON_WALL)
        C.set(mx + dx, 2, mz + dz, IRON_WALL)
        C.set(mx + dx, 3, mz + dz, EDISON)
    # the tank fountain in the middle: a copper ring with water and an upturned propeller
    for x in range(mx - 2, mx + 3):
        for z in range(mz - 2, mz + 3):
            d = math.hypot(x - mx, z - mz)
            if d <= 2.6:
                C.set(x, 0, z, COPPER)
                C.set(x, -1, z, COPPER)
                if d > 1.6:
                    C.set(x, 1, z, COPPER)
                else:
                    C.set(x, 0, z, WATER)
    C.set(mx, 1, mz, IRON_WALL)
    C.set(mx, 2, mz, IRON_WALL)
    propeller(C, mx, 4, mz, "z", r=2, turn=1)
    C.set(mx, 3, mz, IRON_WALL)
    # stalls round the square
    goods = [GEAR, GAUGE, COPPER, "barrel[facing=up,open=false]", PIPES, BRASS_SLAB +
             "[type=bottom,waterlogged=false]", "lantern[hanging=false,waterlogged=false]", "white_wool"]
    stall(C, mx - 11, mz - 9, 5, 3, 1, goods)
    stall(C, mx + 7, mz - 9, 5, 3, 2, goods)
    stall(C, mx - 12, mz + 6, 5, 3, 3, goods)
    stall(C, mx - 5, mz + 7, 5, 3, 4, goods)
    stall(C, mx + 7, mz + 6, 5, 3, 5, goods)
    C.bp.chest(mx + 9, 1, mz - 8, "south", loot=LOOT + "ag_market")
    C.bp.chest(mx - 9, 1, mz + 7, "north", loot=LOOT + "ag_market")
    # lamp posts at the corners
    for (dx, dz) in ((-12, -1), (12, -1), (-6, 9), (6, -9)):
        C.set(mx + dx, 1, mz + dz, IRON)
        for y in range(2, 4):
            C.set(mx + dx, y, mz + dz, IRON_WALL)
        C.set(mx + dx, 4, mz + dz, EDISON)
    windmill(C, mx + 13, mz + 8, 9, "x", 0)
    windmill(C, mx - 14, mz - 6, 11, "z", 1)


SHANTIES = [
    # x0, z0, w, d, door, roof, seed, loot, spawner
    (-38, 18, 6, 5, "east", "tent", 1, "ag_shanty", None),
    (-40, 26, 7, 6, "east", "hull", 2, None, None),
    (-39, 35, 6, 5, "east", "plate", 3, "ag_shanty", None),
    (-36, 44, 7, 5, "north", "tent", 4, None, MOB_BANDIT),
    (-26, 45, 6, 5, "north", "hull", 5, "ag_shanty", None),
    (-15, 46, 5, 5, "north", "tent", 6, None, None),
    (-4, 19, 6, 6, "west", "plate", 7, "ag_shanty", None),
    (-4, 28, 5, 5, "west", "tent", 8, None, None),
    (-28, 9, 6, 5, "south", "tent", 9, None, None),
    (-17, 8, 7, 5, "south", "hull", 10, "ag_shanty", None),
    (-48, 8, 5, 5, "east", "plate", 11, None, None),
    (-49, 30, 6, 5, "east", "tent", 12, "ag_shanty", None),
    (-58, 20, 6, 6, "east", "hull", 13, None, None),
    (-6, 9, 5, 5, "south", "plate", 14, None, None),
]


def shanty_town(C):
    for (x0, z0, w, d, ds, rf, sd, loot, sp) in SHANTIES:
        shanty(C, x0, z0, w, d, ds, rf, sd, loot=loot, spawner=sp)
    # a big canvas tent: the salvagers' mess, gas-bag fabric over a girder frame
    tx0, tz0, tx1, tz1 = -60, 34, -50, 46
    for x in range(tx0, tx1 + 1):
        for z in range(tz0, tz1 + 1):
            C.set(x, 0, z, "spruce_planks" if (x * z) % 3 else "coarse_dirt")
            for y in range(1, 5):
                C.air(x, y, z)
    cxm = (tx0 + tx1) / 2.0
    for z in range(tz0 - 1, tz1 + 2):
        for x in range(tx0 - 1, tx1 + 2):
            dd = abs(x - cxm)
            y = 1 + int(round(6.5 * math.sqrt(max(0.0, 1 - (dd / 6.6) ** 2))))
            if z in (tz0 - 1, tz1 + 1):
                if abs(x - cxm) < 1.6:
                    continue
                for yy in range(1, y + 1):
                    C.set(x, yy, z, "red_wool" if (x + yy) % 4 else "white_wool")
            else:
                C.set(x, y, z, "red_wool" if (z // 3) % 2 else "white_wool")
                for yy in range(1, y):
                    if C.get(x, yy, z) is None:
                        C.air(x, yy, z)
    for z in range(tz0, tz1 + 1, 4):
        for y in range(1, 7):
            C.set(int(cxm), y, z, IRON_WALL if y < 6 else IRON)
    for z in range(tz0 + 2, tz1 - 1, 3):
        C.set(int(cxm) - 2, 1, z, TABLE)
        C.set(int(cxm) - 3, 1, z, f"{CHAIR}[facing=east]")
        C.set(int(cxm) + 2, 1, z, f"{CHAIR}[facing=west]")
    C.set(int(cxm), 5, tz0 + 6, HANG_LAMP)
    C.set(int(cxm), 4, tz0 + 2, HANG_LAMP)
    C.set(tx1, 1, tz1, "barrel[facing=up,open=false]")
    C.set(tx1 - 1, 1, tz1, "smoker[facing=north,lit=true]")
    C.bp.barrel(tx0 + 1, 1, tz1 - 1, loot=LOOT + "ag_market")
    # propeller windmills over the roofs
    windmill(C, -44, 16, 12, "x", 0)
    windmill(C, -8, 40, 10, "z", 1)
    windmill(C, -52, 52, 9, "x", 1)
    # a salvage heap: girders, plates and a propeller stuck in the ground
    for (x, z) in ((-66, 6), (-64, 8), (-62, 5), (-65, 3)):
        C.set(x, 1, z, plate(x, 1, z, 3))
    propeller(C, -60, 4, 9, "x", r=3)
    C.set(-60, 1, 9, IRON)
    for y in (2, 3):
        C.set(-60, y, 9, IRON_WALL)
    # street lamps along the street to the winch house
    for (x, z) in ((-47, 2), (-40, 12), (-32, 17)):
        C.set(x, 1, z, IRON)
        for y in (2, 3):
            C.set(x, y, z, IRON_WALL)
        C.set(x, 4, z, EDISON)


# ------------------------------------------------------------------ ship B: the whale skeleton
SKB = ((60, 86), (6, 42))


def skeleton(C):
    """An envelope frame lying in the grass, ribs every 6 like a whale's, the keel sunk, the spine broken twice;
    shreds of canvas on its upper ribs; the road walks through it. Its tail fin stands by the camp."""
    (ax, az), (bx, bz) = SKB
    L = math.hypot(bx - ax, bz - az)
    yaw = math.degrees(math.atan2(bz - az, bx - ax))
    F = Frame((ax, 3.0, az), yaw)

    def rr(u):
        t = (u - L / 2) / (L / 2 + 4)
        return 14.0 * math.sqrt(max(0.0, 1 - t * t)) ** 0.6

    def cell(u, v, h, x, y, z):
        r = rr(u)
        d = math.hypot(v, h)
        th = math.atan2(h, v)
        k = round((u - 3) / 6.0)
        if 0 <= k <= int((L - 4) // 6) and abs(u - (3 + 6 * k)) < 0.62 and r - 0.75 < d <= r + 0.45:
            # a rib; two are broken at the crown, the last ones lost their tops
            if (k in (3, 7) and 1.25 < th < 1.85) or (k >= 9 and th > 0.9 and th < 2.2):
                return None
            return BRASS if (h > r * 0.6 and k % 2 == 0) else IRON
        # the spine along the top, broken twice
        if abs(v) < 0.65 and abs(h - r) < 0.7 and 2 < u < 52 and not (20 < u < 27 or 40 < u < 45):
            return IRON_BR
        # two longitudinals at 40 degrees, partly gone
        for s in (-1, 1):
            if abs(th - math.radians(90 - s * 50)) * d < 0.6 and abs(d - r) < 0.6 and 3 < u < 53 and \
                    hash01(int(u // 5), s, 141) > 0.3:
                return IRON
        # canvas shreds hanging on the upper ribs
        if abs(d - r) < 0.45 and 1.0 < th < 2.1 and 3 < u < 50 and fbm(u * 1.2, th * 6, 3.0, 142) > 0.66:
            return canvas(x, y, z)
        return None
    raster(C, F, (0, L, -15, 15, -4, 15), cell, ymin=1)
    # rib feet in the ground
    for k in range(0, int((L - 4) // 6) + 1):
        u = 3 + 6 * k
        r = rr(u)
        for s in (-1, 1):
            vv = s * math.sqrt(max(0.0, r * r - 9))
            x, y, z = F.iworld(u, vv, -3)
            C.set(x, 0, z, IRON_BR)
    # the tail fin by the camp: a tall brass-framed canvas fin standing up out of the ground
    for k in range(0, 9):
        for h in range(0, 12 - k):
            x, y, z = F.iworld(-1 - k, 0, h - 2)
            if y >= 1:
                C.set(x, y, z, BRASS if h == 11 - k or k in (0, 8) else canvas(x, y, z))
    return F, L


# ------------------------------------------------------------------ ship A: the buried gondola
def buried_gondola(C):
    """A gondola driven nose-first into the ground at 38 degrees, its tail 25 up; the salvagers cut a breach in
    its flank and built a plank floor and a scaffold inside; a chest waits up in the tail."""
    F = Frame((80.0, -9.0, 40.0), 135.0 + 180.0, pitch=-47.0)   # forward = into the ground, south-east tail up
    Lg = 36

    def hw(gy):
        if gy < 0 or gy > 14:
            return -1
        return (3, 5, 6.5, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 6)[gy]

    def cell(u, v, h, x, y, z):
        # u from the tail (-Lg) to the nose (0)
        gu = u + Lg
        if gu < 0 or gu > Lg:
            return None
        pl = 1.0
        if gu > Lg - 5:
            pl = math.sqrt(max(0.0, 1 - ((gu - (Lg - 5)) / 5.5) ** 2))
        if gu < 2:
            pl = math.sqrt(max(0.0, 1 - ((2 - gu) / 2.5) ** 2))
        w = hw(int(round(h)))
        if w < 0:
            return None
        w *= pl
        if abs(v) > w + 0.3:
            return None
        shell = abs(v) > w - 1.0 or h < 0.6 or h > 13.4 or gu < 0.8 or pl < 0.65
        if shell:
            hi, gi = int(round(h)), int(round(gu))
            side = abs(v) > w - 1.0 and h > 0.6
            if side and hi in (8, 9) and gi % 3 != 0 and 3 < gu < Lg - 4:
                return "glass_pane"
            if side and hi == 3 and gi % 4 == 2 and 3 < gu < Lg - 4:
                return "glass"
            if hi in (6, 7 + 4, 13) or (hi == 2 and side):
                return BRASS
            if y < 3 or (h < 0.6 and hash3(x, y, z, 151) < 0.35):
                return RUST if hash3(x, y, z, 153) < 0.5 else RUST_BR
            return IRON_BR if gi % 6 == 0 else IRON
        if y <= 0:
            return "coarse_dirt" if hash3(x, y, z, 152) < 0.5 else "gravel"
        return AIR
    raster(C, F, (-Lg, 0, -8, 8, 0, 15), cell, ymin=-9)
    # the torn suspension struts on its roof, the propeller behind its tail
    for gu, dv in ((8, -5), (8, 5), (22, -5), (22, 5)):
        for k in range(0, 14):
            t = k * 0.5
            x, y, z = F.iworld(-Lg + gu + t * 0.35, dv * (1 + t * 0.05), 14 + t)
            if t < 6.5 - (2 if gu == 22 else 0):
                C.set(x, y, z, BRASS if k % 4 else IRON_WALL)
    for k in range(4):
        a = math.radians(90 * k + 20)
        for sgn in range(1, 6):
            x, y, z = F.iworld(-Lg - 1.5, math.cos(a) * sgn, 7 + math.sin(a) * sgn)
            C.set(x, y, z, BRASS if sgn < 5 else COPPER)
    x, y, z = F.iworld(-Lg - 1.5, 0, 7)
    C.set(x, y, z, GEAR)
    x, y, z = F.iworld(-Lg - 0.5, 0, 7)
    C.set(x, y, z, IRON)
    # the earth thrown up round the buried nose
    for x in range(64, 98):
        for z in range(24, 58):
            d = math.hypot(x - 81, z - 39)
            if d < 13 and C.get(x, 1, z) is None and C.get(x, 0, z) not in (None, AIR):
                hgt = 1 + (1 if d < 9 and hash01(x, z, 154) < 0.6 else 0)
                for y in range(1, hgt + 1):
                    if C.get(x, y, z) is None:
                        C.set(x, y, z, "coarse_dirt" if hash01(x, y + z, 155) < 0.6 else "dirt")
    # the plank floor at y 8 across the inside, a scaffold up to it, the breach on the north-west flank
    inside = [p for p in C.inner if 72 <= p[0] <= 110 and 15 <= p[2] <= 70 and p[1] >= 1]
    cols = {}
    for (x, y, z) in inside:
        cols.setdefault((x, z), []).append(y)
    floor8 = []
    for (x, z), ys in cols.items():
        if 8 in ys and 9 in ys and 10 in ys and 7 in ys:
            C.set(x, 8, z, "spruce_planks" if (x + z) % 4 else "spruce_slab[type=top,waterlogged=false]")
            floor8.append((x, z))
    # the scaffold: a column inside at ground level near the breach end, reaching the floor
    best = None
    for (x, z), ys in cols.items():
        if all(yy in ys for yy in range(1, 8)) and (x, z) in floor8:
            k = math.hypot(x - 80, z - 40)
            if best is None or k < best[0]:
                best = (k, x, z)
    if best:
        _, sx, sz = best
        for y in range(1, 9):
            C.set(sx, y, sz, "scaffolding[bottom=false,distance=0,waterlogged=false]")
    # the breach: open the flank at ground level along the low side (cells of the shell at y 1..3 near the
    # scaffold column)
    if best:
        _, sx, sz = best
        u, v, h = F.local(sx, 2, sz)
        for du in range(-2, 3):
            for y in range(1, 4):
                for side in (-1, 1):
                    for dv in range(5, 10):
                        x, _, z = F.iworld(u + du, side * dv, h)
                        b = C.get(x, y, z)
                        if b and (b.endswith("dark_iron_plating") or b.endswith("rust_rock") or
                                  b.endswith("glass_pane") or b.endswith("brass_plating")):
                            C.air(x, y, z)
                    break
    # the chest on the plank floor, highest towards the tail
    if floor8:
        fx, fz = max(floor8, key=lambda p: (p[0] + p[1]))
        C.bp.chest(fx, 9, fz, "north", loot=LOOT + "ag_cache")
        C.set(fx - 1, 9, fz, LANT) if C.empty(fx - 1, 9, fz) else None
    return F


# ------------------------------------------------------------------ ship C: broken in two
def frame_cell_fn(rfun, L, seed, broken_lo=None, broken_hi=None, fins_at=None):
    def cell(u, v, h, x, y, z):
        if u < -2 or u > L + 6:
            return None
        r = rfun(max(0.0, min(L, u)))
        if r <= 0.5:
            return None
        d = math.hypot(v, h)
        th = math.atan2(h, v)
        # broken ends: girders stick out ragged
        lim = None
        if broken_hi is not None:
            lim = broken_hi + 4 * hash01(int(th * 8), 0, seed)
            if u > lim:
                return None
        if broken_lo is not None:
            lo = broken_lo - 4 * hash01(int(th * 8), 1, seed)
            if u < lo:
                return None
        if fins_at is not None and u > fins_at and d > r and abs(v) < 0.6 and h > 0 and d < r + (u - fins_at) * 0.7:
            return BRASS if d > r + (u - fins_at) * 0.7 - 1 else canvas(x, y, z)
        if u < 0 or u > L:
            return None
        ring = abs(((u + 4) % 8) - 4) < 0.6
        if ring and r - 0.9 < d <= r + 0.45:
            return IRON if h < 4 else BRASS
        step = math.pi / 6
        arc = d * abs(((th + step / 2) % step) - step / 2)
        if arc < 0.55 and r - 0.9 < d <= r + 0.45:
            return BRASS if h > 0 else IRON
        if r - 0.6 < d <= r + 0.45 and h > -r * 0.45:
            near_break = ((broken_hi is not None and u > broken_hi - 8) or
                          (broken_lo is not None and u < broken_lo + 8))
            if fbm(u * 0.8, th * 7, 4.0, seed) < (0.42 if near_break else 0.6):
                return canvas(x, y, z, low=-0.12)
        return None
    return cell


def broken_ship(C):
    """Ship C: the fore half lying on its side in the grass, the aft half 14 blocks on, swung and rolled, the
    torn ends ragged with girders; between them a trail of gas cells and plates; its gondola, torn off, lies
    upright beside the fore half: the salvagers' den."""
    rc = 12.0

    def rf(u):
        if u < 18:
            return rc * math.sqrt(max(0.0, 1 - ((18 - u) / 18.0) ** 2))
        return rc

    def ra(u):
        return rc * (1 - 0.55 * (u / 44.0) ** 1.5)
    Ff = Frame((18.0, 10.5, -92.0), 32.0, pitch=4.0, roll=14.0)
    raster(C, Ff, (-2, 46, -14, 14, -14, 14), frame_cell_fn(rf, 46, 161, broken_hi=44), ymin=1)
    Fa = Frame((70.0, 10.5, -58.0), 48.0, pitch=-3.0, roll=-22.0)
    raster(C, Fa, (-6, 50, -18, 18, -14, 24), frame_cell_fn(ra, 44, 162, broken_lo=2, fins_at=34), ymin=1)
    # the trail between the halves
    scar(C, [(52, -70), (62, -64), (72, -58)], half=5.0, seed=163)
    for i, (x, z) in enumerate(((56, -67), (61, -63), (66, -61))):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) + abs(dz) < 2:
                    C.set(x + dx, 1, z + dz, canvas(x + dx, 1, z + dz))
        C.set(x, 2, z, "white_wool")
    propeller(C, 60, 5, -72, "z", r=4, turn=1)
    C.set(60, 1, -72, IRON)
    for y in range(1, 5):
        C.set(60, y, -73, IRON_WALL)
    debris(C, 45, -72, 22, 40, 164)
    # the scavenger's chest inside the fore half (on the ground, in its shade)
    x, y, z = Ff.iworld(28, 0, -9)
    C.bp.chest(x, 1, z, "north", loot=LOOT + "ag_wreck")
    x, y, z = Fa.iworld(20, 0, -8)
    C.bp.chest(x, 1, z, "north", loot=LOOT + "ag_wreck")
    return Ff, Fa


DEN = (24, 54, -66, -55)      # x0, x1, z0, z1 of the den gondola (axis along x)


def den(C):
    """The broken ship's gondola lying upright in the grass, sunk to its upper deck: the salvagers' den (bunks,
    a workbench, a forge, the loot of the field)."""
    x0, x1, z0, z1 = DEN
    zc = (z0 + z1) // 2
    for x in range(x0, x1 + 1):
        t = 1.0
        if x < x0 + 4:
            t = math.sqrt(max(0.0, 1 - ((x0 + 4 - x) / 4.6) ** 2))
        if x > x1 - 3:
            t = math.sqrt(max(0.0, 1 - ((x - (x1 - 3)) / 3.6) ** 2))
        hw = 5.5 * t
        for z in range(z0 - 1, z1 + 2):
            if abs(z - zc) > hw + 0.3:
                continue
            for y in range(-1, 7):
                shell = abs(z - zc) > hw - 0.9 or y in (-1, 6) or x in (x0, x1) or t < 0.7
                if y == 0 and not shell:
                    C.set(x, y, z, PARQUET)
                elif shell:
                    if y in (2, 3) and x % 3 and x0 + 3 < x < x1 - 3:
                        C.set(x, y, z, "glass_pane")
                    elif y == 6 and hash01(x, z, 171) < 0.12:
                        C.air(x, y, z)          # holes in the crushed roof
                    else:
                        C.set(x, y, z, BRASS if y == 5 else (RUST if hash3(x, y, z, 172) < 0.25 else IRON))
                else:
                    C.air(x, y, z)
    # door on the south flank, steps
    zw = zc + 5
    for y in (1, 2, 3):
        C.air(38, y, zw)
        C.air(39, y, zw)
    C.set(38, 0, zw, TREAD)
    C.set(39, 0, zw, TREAD)
    # partition: the bunk room east, the workshop west
    for z in range(z0 + 1, z1):
        if abs(z - zc) <= 1:
            continue
        for y in range(1, 5):
            C.set(46, y, z, plate(46, y, z, 5))
    for z in (z0 + 1, z0 + 3):
        C.bp.bed(48, 1, z, "east", color="brown") if z0 + 3 < zc + 4 else None
    C.bp.bed(48, 1, z1 - 2, "east", color="gray")
    C.set(51, 1, zc, "barrel[facing=up,open=false]")
    C.bp.chest(51, 1, z1 - 1, "west", loot=LOOT + "ag_wreck")
    C.set(30, 1, z0 + 1, "crafting_table")
    C.set(31, 1, z0 + 1, "smithing_table")
    C.set(32, 1, z0 + 1, "blast_furnace[facing=south,lit=true]")
    C.set(33, 1, z0 + 1, "anvil[facing=east]")
    C.set(34, 1, z0 + 1, "barrel[facing=up,open=false]")
    C.bp.chest(28, 1, zc, "east", loot=LOOT + "ag_market")
    for x in (31, 40, 49):
        C.set(x, 4, zc, HANG_LAMP)
    C.bp.spawner(36, 1, zc - 2, MOB_BANDIT)


# ------------------------------------------------------------------ the camp
CAMP = (66, 92)


def camp(C):
    """The salvagers' camp at the edge of the field: a tent of envelope canvas, a fire, crates, the waystone, a
    signpost of a broken propeller blade."""
    cx, cz = CAMP
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 4, cz + 5):
            if C.get(x, 0, z) is not None and math.hypot(x - cx, (z - cz) * 1.3) < 6.5:
                C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 181) < 0.5 else "dirt_path")
    # the tent (ridge along x)
    for x in range(cx + 1, cx + 7):
        for k in range(0, 4):
            for z in (cz - 4 + k, cz + 2 - k):
                C.set(x, 1 + k, z, "light_gray_wool" if (x + k) % 3 else "white_wool")
        C.set(x, 4, cz - 1, "white_wool")
    C.set(cx + 5, 1, cz - 1, "barrel[facing=up,open=false]")
    C.bp.bed(cx + 2, 1, cz - 2, "east", color="brown")
    # fire, crates
    C.set(cx - 2, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((cx - 4, cz - 2), (cx - 4, cz - 3), (cx - 5, cz - 2)):
        C.set(x, 1, z, "barrel[facing=up,open=false]")
    C.bp.chest(cx - 3, 1, cz + 3, "north", loot=LOOT + "ag_camp")
    C.set(cx - 1, 1, cz + 2, MOD["waystone"])
    C.set(cx + 1, 1, cz + 3, IRON_WALL)
    C.set(cx + 1, 2, cz + 3, LANT)


# ------------------------------------------------------------------ the whole site
def airship_graveyard(bp):
    C = Ctx(bp)
    ground(C)
    # paths: camp -> skeleton -> market -> winch house; side tracks
    path_line(C, [CAMP, (60, 84), (48, 74), (33, 62), (18, 51), (6, 42), (-6, 34), MKT])
    path_line(C, [MKT, (-28, 18), (-40, 8), (TX, WZ1 + 2)])
    path_line(C, [MKT, (-46, 38), (-55, 40)], half=1.3)
    path_line(C, [(-6, 34), (30, 22), (60, 30), (70, 34)], half=1.2)
    path_line(C, [(TX, WZ1 + 2), (-70, 2), (-86, GZ1 + 2)], half=1.4)
    path_line(C, [(-20, 4), (5, -20), (24, -48)], half=1.2)
    scar(C, [(40, 72), (60, 54), (77, 41)], half=3.5, seed=191)           # the buried gondola's furrow
    scar(C, [(-10, 92), (20, 70), (40, 58)], half=5.0, seed=192)          # the skeleton slid here
    scar(C, [(-20, -96), (0, -95), (16, -90)], half=4.0, seed=193)
    debris(C, 75, 45, 16, 30, 194)
    debris(C, 25, 66, 24, 30, 195)
    debris(C, 10, -20, 30, 40, 196)
    debris(C, -70, -75, 20, 20, 197)
    # the tower and the gas works
    winch_house(C)
    mast(C)
    core = mast_stair(C)
    lift_shaft(C, core)
    balcony(C)
    winch_room(C)
    gas_works(C)
    gasometer(C, G1, 201)
    gasometer(C, G2, 202)
    gas_pipes(C)
    # the moored ship
    hull_intact(C)
    hull_aft(C)
    fins(C)
    gondola(C)
    carve_hull(C)
    nacelles(C)
    line_hull(C)
    hull_rooms(C)
    gondola_rooms(C)
    hold_cargo(C)
    roof_details(C)
    deck(C)
    deck_dressing(C)
    gangway(C)
    ring_walkway(C)
    crown(C)
    # the wrecks, the town, the camp
    skeleton(C)
    buried_gondola(C)
    broken_ship(C)
    den(C)
    market(C)
    shanty_town(C)
    camp(C)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("market", (MKT[0] + 8, 1, MKT[1] + 5), (MKT[0] - 4, 3, MKT[1] - 7)),
    ("winch_house", (TX + 4, 1, TZ + 9), (TX - 2, 3, TZ - 8)),
    ("gas_works", (GX1 - 8, 1, TZ), (GX0 + 4, 5, TZ)),
    ("mooring_ring", (TX + 6, RW, TZ + 8), (NX + 10, RW + 4, SZ)),
    ("gondola_bridge", (X(42), UPF, Z(5)), (X(31), UPF + 1, Z(0))),
    ("cargo_hold", (X(36), LOF, Z(-3)), (X(60), LOF + 1, Z(2))),
    ("top_deck", (X(88), DY + 1, Z(-12)), (X(50), DY + 3, Z(2))),
]

register(StructureDef(
    "airship_graveyard", "overworld", ["savanna", "savanna_plateau", "plains", "sunflower_plains"],
    [Piece("field", airship_graveyard, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_RAIDER, 6, 1, 2), (MOB_BANDIT, 4, 1, 1), (MOB_MITE, 3, 1, 2)],
    title_fr="Le Cimetière des dirigeables", title_en="The Airship Graveyard"))

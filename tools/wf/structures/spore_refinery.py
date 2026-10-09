"""The Spore Refinery (La Raffinerie de spores): an alchemists' spore works grown into and around three colossal
mushrooms on a mycelium island. Colossal tier (tools/BUILDING.md §1, §12 concept 27, §10 legacy-dungeon template,
§15), steampunk accents (tools/STYLE_STEAMPUNK.md: copper pipes wound round the stems, brass bands and spore vats,
screw presses, copper stills and distillation columns, a cog-driven lift).

Silhouette (one noun phrase, §15.1): three giant mushrooms of rising height, the tallest a 90-high fly agaric with a
68-wide red cap, strapped with brass bands and copper pipes over a cluster of brick halls with green copper roofs.

Layout, ground y = 0 (feet 1), x east, z south.
  * the mushrooms: M1 (red, the dominant) at (0, -38), stem 20 wide, a skirt-ring (annulus) at y 70 under a cap
    rising to a flat top at y 88 (rim r 34); M2 (brown, flat cap at 62, rim r 27) at (-60, 2); M3 (red, dome at 50,
    rim r 20) at (58, 0). Each stem is hollow round an 11 x 11 well with a newel stair (5-step flights, 3 x 3 corner
    landings, +5 a side) round a 5 x 5 core;
  * the approach (south): the spore-gatherers' camp and its waystone, a bending path past mushroom lamps and small
    wild mushrooms, the pipe gate whose copper arch frames M1 (the reveal), the press yard (hub, waystone) round its
    great spore vat;
  * the main route: the press hall (two screw presses under a gantry, the foreman's corner) -> its west passage ->
    the fermentation hall (six oak-and-iron vats, the chute pool) -> M2's stem, up its newel to the drying lofts
    under the brown cap (racks of spore trays, site of grace) -> the rope bridge to M1's stem (feet 46) -> up M1's
    newel to the gills chamber on the annulus (site of grace) under the red cap -> the ramp, the mist in its tunnel
    -> the boss arena on top of the cap (42 wide, fenced, open sky);
  * optional: the distillery (three pot stills, four distillation columns outside) east of the yard -> M3's newel ->
    the alchemists' lab round M3's stem under its cap (benches, library, specimen cases, the transmutation circle)
    -> the brass catwalk on its pylon to M1's stem (feet 31): a loop. The spore cellars beneath M1's roots, down a
    stair from the press hall (vaults, roots through the ceiling, cistern, barrel racks);
  * the treasury: the refined-spore vault inside the cap's central gill-boss, down a stair from the arena behind
    sealed bars;
  * shortcuts (§10.4): the cap lift (the vault's 3 x 3 drop well down M1's core into a pool at the stem's foot; the
    stem's iron door opens only from inside into the press hall), the spore chute (the drying loft's chute drops
    into the fermentation hall's pool), the one-way cellar door (the cellars' iron stair-house door opens only from
    the stair, into the press yard).
Loot gradient (§15.6): camp and yard tier 1; press hall, fermentation, distillery 1-2; cellars, lofts 2; lab 2-3;
gills chamber 3; the vault 3-5.
Height budget: the arena fence stands 91 above the ground layer (mushroom fields lie at sea level).
"""
import math

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, IRON, PIPES, TABLE, TREAD, VERD, W, hash01,
                       hash3, vnoise)
from ..parts import LOOT, MOD
from .cloud_pagoda import Ctx, candle, carpet, carve, hang, railing, slab

# the champion of the cap: the Spore Alchemist (tools/wf/mobs/spore_alchemist.py, entity/boss/SporeAlchemist.java)
BOSS = "brasshaven:spore_alchemist"
MOB_WITCH = "minecraft:witch"
MOB_BOGGED = "minecraft:bogged"
MOB_MITE = W + "rust_mite"
MOB_DRONE = W + "steam_drone"
MOB_SPIDER = W + "clockwork_spider"
MOB_GUNNER = W + "boiler_gunner"
MOB_AUTO = W + "turbine_automaton"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
STEM = "mushroom_stem"
RED, RED_U = "red_mushroom_block", "red_mushroom_block[down=false]"
BROWN, BROWN_U = "brown_mushroom_block", "brown_mushroom_block[down=false]"
MYC = "mycelium[snowy=false]"
SHROOM = "shroomlight"
BRICK, BRICK_ST, BRICK_WALL = "bricks", "brick_stairs", "brick_wall"
MUD, PMUD = "mud_bricks", "packed_mud"
SB, MSB, CSB, SB_ST = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "stone_brick_stairs"
CU, CU_ST, CU_SL = ("waxed_weathered_cut_copper", "waxed_weathered_cut_copper_stairs",
                    "waxed_weathered_cut_copper_slab")
CU2 = "waxed_oxidized_cut_copper"
CUB = "waxed_copper_block"
SP, SP_ST, SP_SL, SP_FENCE = "spruce_planks", "spruce_stairs", "spruce_slab", "spruce_fence"
SP_LOG = "spruce_log[axis=y]"
DO_LOG_X, DO_LOG_Z = "dark_oak_log[axis=x]", "dark_oak_log[axis=z]"
OAK = "oak_planks"
GILD, BTILE, GRILLE = W + "gilded_trim", W + "brass_tiles", W + "brass_grille"
AMBER = "orange_stained_glass_pane"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
CORN = [(-1, -1), (1, -1), (1, 1), (-1, 1)]          # NW, NE, SE, SW (newel corners, clockwise)

# ------------------------------------------------------------------ the three mushrooms
M1 = dict(name="M1", c=(0, -38), ro=10.0, top=70, well_top=69, seed=11, red=True, newel=(1, 14, 3), rim=34)
M2 = dict(name="M2", c=(-60, 2), ro=9.0, top=58, well_top=52, seed=23, red=False, newel=(1, 9, 1), rim=27)
M3 = dict(name="M3", c=(58, 0), ro=9.0, top=46, well_top=37, seed=37, red=True, newel=(1, 6, 3), rim=20)
MUSH = (M1, M2, M3)
PZ = -38                                   # M1 axis z (x = 0)
DECK = 88                                  # M1 cap top (arena floor block; feet 89)
CHAMBER = 70                               # M1 annulus floor (feet 71)
FLAT = 22                                  # M1 flat cap radius
FENCE_R = 21
VAULT_F = 78                               # vault floor block (feet 79)
LOFT_F = 45                                # M2 drying loft floor block (feet 46)
LAB_F = 30                                 # M3 lab floor block (feet 31)
FERM_H = 12                                # fermentation hall ceiling

# site rectangles (x0, z0, x1, z1)
PRESS = (-16, -22, 16, 12)
FERM = (-46, -14, -24, 22)
DIST = (24, 2, 44, 30)
YARD = (-20, 13, 20, 46)
CELLAR = (-14, -26, 14, -8)
HOUSE = (-14, 14, -8, 22)                  # the cellar stair-house in the yard
BUSY = []                                  # rectangles kept free of wild mushrooms


def dist(x, z, M):
    return math.hypot(x - M["c"][0], z - M["c"][1])


def face_of(dx, dz):
    if abs(dz) >= abs(dx):
        return "south" if dz > 0 else "north"
    return "east" if dx > 0 else "west"


def fp(C, x, y, z, spec):
    """Furniture: never on reserved walkway air."""
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


def iron_door(C, x, y, z, facing, lever_dx, lever_dz):
    """An iron door; its lever on the wall block beside it, on the side (lever_dx, lever_dz) points to (the only
    side it opens from)."""
    C.keep.discard((x, y, z))
    C.keep.discard((x, y + 1, z))
    C.bp.door(x, y, z, facing, wood="iron")
    # the wall beside the door (perpendicular to the lever side) carries the lever on its open-side face
    if lever_dx == 0:
        wx, wz = x - 1, z
    else:
        wx, wz = x, z - 1
    lf = face_of(lever_dx, lever_dz)
    C.set(wx, y + 1, wz, BRICK if not C.solid(wx, y + 1, wz) else C.get(wx, y + 1, wz))
    C.set(wx + lever_dx, y + 1, wz + lever_dz, f"lever[face=wall,facing={lf},powered=false]")


def mlamp(C, x, y, z, red=True):
    """A glowing mushroom lamp: a stem post, a shroomlight bulb under a little cap; feet y."""
    for yy in range(y, y + 3):
        C.put(x, yy, z, STEM)
    C.put(x, y + 3, z, SHROOM)
    cap = RED if red else BROWN
    for dx, dz in N4:
        C.put(x + dx, y + 3, z + dz, cap + "[down=false]")
    C.put(x, y + 4, z, cap)


def small_mushroom(C, x, z, h, red, seed):
    """A wild giant mushroom of vanilla size (5-9 high) on the mycelium: a stem and a cap (red dome or brown
    plate)."""
    for y in range(1, h + 1):
        C.put(x, y, z, STEM)
    if red:
        for y, r in ((h + 1, 2), (h - 1, 2), (h, 2)):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if y == h + 1:
                        if abs(dx) == 2 or abs(dz) == 2:
                            continue
                    elif abs(dx) < 2 and abs(dz) < 2:
                        continue
                    elif abs(dx) == 2 and abs(dz) == 2:
                        continue
                    C.put(x + dx, y, z + dz, RED)
    else:
        r = 3
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r and abs(dz) == r:
                    continue
                C.put(x + dx, h + 1, z + dz, BROWN)


# ------------------------------------------------------------------ caps and stems
def cap_profile(M, r):
    """(top, underside) of a cap at radius r, or None outside it."""
    n = M["name"]
    if n == "M1":
        if r <= FLAT:
            yt = DECK
        elif r <= 34:
            yt = DECK - (r - FLAT) ** 2 * 18.0 / 144.0
        elif r <= 35.5:
            return 69, 66
        else:
            return None
        yt = int(round(yt))
        if r <= 7.5:
            yb = 77
        elif r <= FLAT:
            yb = 84
        else:
            yb = yt - 4
        return yt, yb
    if n == "M2":
        if r <= 16:
            yt = 62.0
        elif r <= 27:
            yt = 62 - ((r - 16) / 11.0) ** 2 * 5
        elif r <= 28.5:
            return 57, 54
        else:
            return None
        yt = int(round(yt))
        return yt, yt - 3
    # M3: a red dome
    if r <= 20:
        yt = int(round(50 - (r / 20.0) ** 2 * 10))
        return yt, yt - 3
    if r <= 21.5:
        return 40, 37
    return None


def r_eff(M, x, z):
    """Distance from the cap's axis, stretched by a wavy margin outside the flat crown (no perfect circles)."""
    cx, cz = M["c"]
    r = math.hypot(x - cx, z - cz)
    keep = {"M1": FLAT + 2, "M2": 16, "M3": 8}[M["name"]]
    if r <= keep:
        return r
    a = math.atan2(z - cz, x - cx)
    n = vnoise(math.cos(a) * 7 + 50, math.sin(a) * 7 + 50, 2.2, M["seed"] + 9)
    return keep + (r - keep) * (1 + 0.16 * (n - 0.5))


def spot(x, z, seed):
    """The white warts of a fly agaric's cap."""
    return vnoise(x, z, 2.6, seed) > 0.8


def cap(C, M):
    cx, cz = M["c"]
    R = int(M["rim"] + 5)
    capb, capu = (RED, RED_U) if M["red"] else (BROWN, BROWN_U)
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            r = math.hypot(x - cx, z - cz)
            p = cap_profile(M, r_eff(M, x, z))
            if p is None:
                continue
            yt, yb = p
            for y in range(yb, yt + 1):
                if y == yb:
                    spec = capu
                    if hash3(x, y, z, M["seed"] + 3) < 0.035 and r > M["ro"] + 2:
                        spec = SHROOM                       # glowing spots under the cap
                elif y == yt and M["red"] and spot(x, z, M["seed"]):
                    spec = STEM
                else:
                    spec = capb
                C.set(x, y, z, spec)
    gills(C, M)


def gills(C, M):
    """Radial gill fins of stem flesh under the cap."""
    cx, cz = M["c"]
    rim = M["rim"]
    r_in = 8.0 if M["name"] == "M1" else M["ro"] + 1.5
    nf = int(2 * math.pi * rim / 3.0)
    for x in range(cx - rim - 4, cx + rim + 5):
        for z in range(cz - rim - 4, cz + rim + 5):
            r = math.hypot(x - cx, z - cz)
            if r < r_in or r_eff(M, x, z) > rim - 0.5:
                continue
            a = (math.atan2(z - cz, x - cx) % (2 * math.pi)) / (2 * math.pi) * nf
            if abs(a - round(a)) * (2 * math.pi * r / nf) > 0.5:
                continue
            p = cap_profile(M, r_eff(M, x, z))
            if p is None:
                continue
            yt, yb = p
            if M["name"] == "M1":
                h = 2 if r <= FLAT else 3
            elif M["name"] == "M2":
                h = 2 if r <= 21 else 3
            else:
                h = 1 if r <= 17 else 2
            for y in range(yb - h, yb):
                C.put(x, y, z, STEM)


def stem_r(M, y, ang):
    ro, top, s = M["ro"], M["top"], M["seed"]
    flare = max(0.0, 6.0 - max(y, 0))              # a stepped boot: one ring a layer
    bulge = 2.5 * math.exp(-(top - y) / 3.5)
    noise = (vnoise(ang * 4.0 + s, 0.5 + max(y, 6) * 0.04, 1.0, s) - 0.5) * 1.2
    taper = -0.8 * max(0, y) / top
    return max(8.2, ro + flare + bulge + noise + taper)


def in_well(M, x, z):
    cx, cz = M["c"]
    return abs(x - cx) <= 5 and abs(z - cz) <= 5


def stem(C, M):
    cx, cz = M["c"]
    top, wt = M["top"], M["well_top"]
    for y in range(-3, top + 1):
        R = 16
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                dx, dz = x - cx, z - cz
                d = math.hypot(dx, dz)
                if d > R:
                    continue
                rr = stem_r(M, y, math.atan2(dz, dx))
                if d > rr:
                    continue
                if abs(dx) <= 5 and abs(dz) <= 5 and y >= 0:
                    if y == 0:
                        C.set(x, y, z, SP if (x + z) % 2 else "stripped_spruce_wood[axis=y]")
                    elif y <= wt:
                        C.clear(x, y, z)
                    else:
                        C.set(x, y, z, STEM)
                    continue
                spec = STEM
                if d > rr - 1.2:
                    if y % 16 == 8 or y % 16 == 9 and hash3(x, y, z, 5) < 0.3:
                        spec = BRASS if y % 16 == 8 else IRON
                    elif y <= 1 and hash3(x, y, z, 6) < 0.3:
                        spec = MYC
                C.set(x, y, z, spec)
    roots(C, M)
    pipe_helix(C, M)
    brackets(C, M)


def roots(C, M):
    """Six roots of stem flesh spreading from the foot into the mycelium, away from the halls."""
    cx, cz = M["c"]
    avoid = {"M1": math.pi / 2, "M2": 0.0, "M3": math.pi}[M["name"]]
    k = 0
    for i in range(9):
        a = i * 2 * math.pi / 9 + hash01(i, M["seed"], 7) * 0.4
        da = abs((a - avoid + math.pi) % (2 * math.pi) - math.pi)
        if da < 0.85:
            continue
        k += 1
        L = 12 + hash01(i, M["seed"], 8) * 6
        for s in range(0, 40):
            t = s / 39.0
            px = cx + math.cos(a) * (M["ro"] + 1 + L * t)
            pz = cz + math.sin(a) * (M["ro"] + 1 + L * t)
            py = 1.5 - 5.5 * t
            rad = 2.2 - 1.4 * t
            for x in range(int(px - rad) - 1, int(px + rad) + 2):
                for z in range(int(pz - rad) - 1, int(pz + rad) + 2):
                    for y in range(int(py - rad) - 1, int(py + rad) + 2):
                        if (x - px) ** 2 + (z - pz) ** 2 + ((y - py) * 1.3) ** 2 <= rad * rad:
                            if not in_busy(x, z, 0):
                                C.put(x, y, z, STEM)


def pipe_helix(C, M):
    """A copper pipe wound twice round the stem from the foot to below the cap, on brass brackets."""
    cx, cz = M["c"]
    y0, y1 = 11, M["top"] - 12
    turns = 2.2 if M["name"] == "M1" else 1.6
    last = None
    n = (y1 - y0) * 6
    for s in range(n + 1):
        t = s / n
        y = int(round(y0 + (y1 - y0) * t))
        a = M["seed"] + t * turns * 2 * math.pi
        rr = stem_r(M, y, a) + 1.0
        x, z = int(round(cx + math.cos(a) * rr)), int(round(cz + math.sin(a) * rr))
        if (x, y, z) == last:
            continue
        last = (x, y, z)
        if in_busy(x, z, 0) and y < 26:
            continue
        C.put(x, y, z, PIPES)
        if s % 30 == 0:
            C.put(x, y - 1, z, BRASS)


def brackets(C, M):
    """Bracket fungi (shelf mushrooms) on the stem's outer face."""
    cx, cz = M["c"]
    for i in range(16):
        y = 11 + int(hash01(i, M["seed"], 31) * (M["top"] - 24))
        a = hash01(i, M["seed"], 32) * 2 * math.pi
        rr = stem_r(M, y, a)
        for w in range(-2, 3):
            aa = a + w * 0.06
            for dr in (0.6, 1.6, 2.4):
                if dr > 1.6 and abs(w) > 1:
                    continue
                x = int(round(cx + math.cos(aa) * (rr + dr)))
                z = int(round(cz + math.sin(aa) * (rr + dr)))
                if C.free(x, y, z) and not in_busy(x, z, 0):
                    C.put(x, y, z, BROWN)



def stem_vats(C):
    """Spore vats wrapped round the stems: tall vats on the ground piped into the stem, smaller ones strapped to the
    stem on iron brackets higher up."""
    for M, angs, high in ((M1, (-math.pi / 2, 0.25, math.pi - 0.25, -2.3), (0.8, 2.4, 3.9, 5.5)),
                          (M2, (math.pi, -2.0, 2.1), (1.2, 3.6)),
                          (M3, (0.0, -1.2, 1.3), (2.0, 4.5))):
        cx, cz = M["c"]
        for a in angs:
            rr = stem_r(M, 1, a) + 4.0
            x, z = int(round(cx + math.cos(a) * rr)), int(round(cz + math.sin(a) * rr))
            if in_busy(x, z, 3):
                continue
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    if math.hypot(dx, dz) <= 4.0:
                        C.set(x + dx, 0, z + dz, IRON if math.hypot(dx, dz) > 3.4 else TREAD)
            vat(C, x, z, 1, 11 if M is M1 else 8, r=3.2, seed=x + z)
            C.set(int(round(x - math.cos(a) * 3.5)), 3, int(round(z - math.sin(a) * 3.5)), GAUGE)
            # the feed pipe into the stem at y 8
            for s_ in range(0, 30):
                r2 = rr - 3.0 - s_ * 0.25
                px, pz = int(round(cx + math.cos(a) * r2)), int(round(cz + math.sin(a) * r2))
                if C.solid(px, 10, pz) and C.get(px, 10, pz) == "minecraft:mushroom_stem":
                    break
                C.set(px, 10, pz, PIPES)
            BUSY.append((x - 4, z - 4, x + 4, z + 4))
        for a in high:
            y0 = 17 if M is M1 else 13
            rr = stem_r(M, y0 + 3, a) + 2.2
            x, z = int(round(cx + math.cos(a) * rr)), int(round(cz + math.sin(a) * rr))
            vat(C, x, z, y0, 7, r=2.1, seed=int(a * 10))
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if math.hypot(dx, dz) <= 2.1:
                        C.set(x + dx, y0 - 1, z + dz, IRON)
            # a corbel of iron stairs under the bracket, toward the stem
            for k in range(1, 4):
                C.put(int(round(x - math.cos(a) * k)), y0 - 1 - k, int(round(z - math.sin(a) * k)), IRON)

def cap_vents(C):
    """Copper vent stacks breaking through the caps' slopes (the gills chamber breathes through them) and a brass
    finial with a lightning rod on the small agaric: peaks for the skyline."""
    cx, cz = M1["c"]
    for i, (a, h) in enumerate(((0.35, 9), (1.45, 6), (2.55, 11), (3.85, 7), (5.0, 8))):
        r = 28.0 + (i % 2) * 2
        x0, z0 = int(round(cx + math.cos(a) * r)), int(round(cz + math.sin(a) * r))
        base = cap_profile(M1, r_eff(M1, x0, z0))[0]
        for dx in (0, 1):
            for dz in (0, 1):
                for y in range(base - 1, base + h):
                    C.set(x0 + dx, y, z0 + dz, BRASS if (y - base) % 5 == 4 else COPPER)
                C.set(x0 + dx, base + h, z0 + dz, GRILLE)
                C.set(x0 + dx, base + h + 1, z0 + dz, slab(CU_SL))
    mx, mz = M3["c"]
    top = cap_profile(M3, 0)[0]
    for y in range(top + 1, top + 4):
        C.set(mx, y, mz, BRASS if y < top + 3 else GILD)
    C.set(mx, top + 4, mz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for dx, dz in N4:
        C.set(mx + dx, top + 1, mz + dz, stair(W + "brass_plating_stairs", face_of(-dx, -dz)))


# ------------------------------------------------------------------ the newel stairs
def newel_cells(M):
    """Square newel round the 5 x 5 core: 3 x 3 corner landings, flights of five steps (3 wide) on the sides, +5 a
    side. Returns [(x, z, feet, facing or None)] and {k: (sx, sz, feet)}."""
    cx, cz = M["c"]
    f0, k_end, c0 = M["newel"]
    cells, land = [], {}
    f = f0
    for k in range(k_end + 1):
        sx, sz = CORN[(c0 + k) % 4]
        for d1 in (3, 4, 5):
            for d2 in (3, 4, 5):
                cells.append((cx + sx * d1, cz + sz * d2, f, None))
        land[k] = (sx, sz, f)
        if k == k_end:
            break
        nx, nz = CORN[(c0 + k + 1) % 4]
        if sx != nx:
            d = 1 if nx > sx else -1
            for i, du in enumerate(range(-2 * d, 3 * d, d)):
                for dv in (3, 4, 5):
                    cells.append((cx + du, cz + sz * dv, f + i + 1, "east" if d > 0 else "west"))
        else:
            d = 1 if nz > sz else -1
            for i, dv in enumerate(range(-2 * d, 3 * d, d)):
                for du in (3, 4, 5):
                    cells.append((cx + sx * du, cz + dv, f + i + 1, "south" if d > 0 else "north"))
        f += 5
    return cells, land


def newel(C, M):
    cx, cz = M["c"]
    cells, land = newel_cells(M)
    M["_land"] = land
    M["_cells"] = {}
    for (x, z, f, fc) in cells:
        if fc:
            C.set(x, f - 1, z, stair(SP_ST, fc))
        else:
            C.set(x, f - 1, z, SP if (x + z) % 2 else "stripped_spruce_wood[axis=y]")
        M["_cells"].setdefault((x, z), []).append(f - 1)
        if f - 1 - (M["newel"][0] - 1) <= 6:
            for y in range(M["newel"][0] - 1, f - 1):
                C.set(x, y, z, SP)                        # the first flight sits on a solid plinth
    for (x, z, f, fc) in cells:
        for y in range(f, f + 3):
            if C.get(x, y, z) == AIR:
                C.keep.add((x, y, z))
    # the core: 5 x 5, stem with iron corners, brass bands, gauges facing the landings
    f0 = M["newel"][0]
    ytop = M["well_top"] if M["name"] != "M1" else VAULT_F - 1
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = abs(dx) == 2 or abs(dz) == 2
            for y in range(-4 if M["name"] == "M1" else f0 - 1, ytop + 1):
                if M["name"] == "M1" and not edge:
                    continue                              # the drop well of the cap lift
                spec = STEM
                if abs(dx) == 2 and abs(dz) == 2:
                    spec = IRON
                elif y % 10 == 0:
                    spec = BRASS
                elif not edge:
                    spec = PIPES
                C.set(cx + dx, y, cz + dz, spec)
    # lamps and gauges on the core at every landing; small amber windows in the outer wall at odd landings
    for k, (sx, sz, f) in land.items():
        C.set(cx + sx * 2, f + 1, cz + sz * 2, EDISON)
        if k % 2:
            wx, wz = cx + sx * 6, cz + sz * 4
            for y in (f + 1, f + 2):
                if C.solid(wx, y, wz) and dist(wx + sx, wz, M) < stem_r(M, y, 0) + 3:
                    C.set(wx, y, wz, AMBER)
                    # glaze through to the outside
                    xx = wx + sx
                    while C.solid(xx, y, wz) and abs(xx - cx) < 17:
                        C.set(xx, y, wz, AMBER)
                        xx += sx


def well_floor(C, M, fy):
    """Floor the well at the newel's top landing (floor block fy) except over the last flight (a railed hole), so
    nobody steps off the landing into the shaft."""
    cx, cz = M["c"]
    cells = M["_cells"]
    holes = set()
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            if abs(x - cx) <= 2 and abs(z - cz) <= 2:
                continue
            ys = cells.get((x, z), [])
            if fy in ys:
                continue
            if any(fy - 4 < y < fy for y in ys):
                holes.add((x, z))
                for yy in range(fy, fy + 3):
                    C.clear(x, yy, z)
                continue
            C.set(x, fy, z, SP if (x + z) % 2 else "stripped_spruce_wood[axis=y]")
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            if (x, z) in holes or (abs(x - cx) <= 2 and abs(z - cz) <= 2) or fy in cells.get((x, z), []):
                continue
            for dx, dz in N4:
                if (x + dx, z + dz) in holes:
                    railing(C, x, fy + 1, z, face_of(dx, dz))
                    break



def stem_door(C, M, k, d, floor=SP, head=4):
    """A 3-wide doorway from newel landing k out through the stem wall toward d. Returns the first outside cells
    [(x, z)] (3 of them) and the floor block y."""
    cx, cz = M["c"]
    sx, sz, f = M["_land"][k]
    dx, dz = DV[d]
    if dx:
        lat = [cz + sz * j for j in (3, 4, 5)]
    else:
        lat = [cx + sx * j for j in (3, 4, 5)]
    out = []
    for i in range(6, 24):
        cells = [(cx + dx * i, l) if dx else (l, cz + dz * i) for l in lat]
        inside = False
        for (x, z) in cells:
            a = math.atan2(z - cz, x - cx)
            if dist(x, z, M) <= max(stem_r(M, f, a), stem_r(M, f + head, a)) + 0.5:
                inside = True
        for (x, z) in cells:
            C.set(x, f - 1, z, floor if i % 4 else BRASS)
            for y in range(f, f + head):
                C.clear(x, y, z)
        if not inside:
            out = cells
            break
    return out, f - 1


# ------------------------------------------------------------------ ground and helpers
def in_busy(x, z, m=0):
    for (x0, z0, x1, z1) in BUSY:
        if x0 - m <= x <= x1 + m and z0 - m <= z <= z1 + m:
            return True
    return False


def site_r(x, z):
    a = math.atan2(z, x)
    return 86 + 5 * (vnoise(a * 6.0, 0.0, 1.0, 71) - 0.5)


def ground(C):
    """The mycelium island: two layers (mycelium on dirt) over the site, a rough skirt at its edge, air cleared one
    to two blocks above in the inner part (paths and courts stay clear of terrain bumps)."""
    for x in range(-92, 93):
        for z in range(-80, 96):
            rr = math.hypot(x * 0.98, (z - 6) * 1.04)
            R = site_r(x, z - 6)
            if rr > R:
                continue
            h = hash01(x, z, 81)
            top = MYC if h < 0.9 else ("podzol[snowy=false]" if h < 0.95 else "coarse_dirt")
            C.set(x, 0, z, top)
            C.set(x, -1, z, "dirt")
            if rr > R - 4:
                for y in range(-5, -1):
                    C.set(x, y, z, "dirt" if y > -3 else "stone")


def clear_above(C):
    """Air over the inner island where nothing was built (terrain bumps vanish)."""
    for x in range(-80, 81):
        for z in range(-70, 92):
            if math.hypot(x, z - 6) > 78:
                continue
            for y in (1, 2):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)


def path(C, pts, w, kind="main"):
    hw = w / 2.0
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    for x in range(int(min(xs) - hw - 1), int(max(xs) + hw + 2)):
        for z in range(int(min(zs) - hw - 1), int(max(zs) + hw + 2)):
            dmin = 99
            for i in range(len(pts) - 1):
                (ax, az), (bx, bz) = pts[i], pts[i + 1]
                vx, vz = bx - ax, bz - az
                L2 = vx * vx + vz * vz
                t = 0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / L2))
                dmin = min(dmin, math.hypot(x - ax - vx * t, z - az - vz * t))
            if dmin > hw:
                continue
            h = hash01(x, z, 91)
            if kind == "main":
                spec = "dirt_path" if (dmin < hw - 0.8 and h < 0.75) else ("coarse_dirt" if h < 0.85 else
                                                                            "gravel")
            else:
                spec = "gravel" if h < 0.5 else "coarse_dirt"
            C.set(x, 0, z, spec)
            for y in (1, 2, 3):
                if C.free(x, y, z):
                    C.clear(x, y, z)


def walls_of(C, x0, z0, x1, z1, y0, y1, spec):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                for y in range(y0, y1 + 1):
                    C.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def brick_wall(x, y, z):
    """Hall masonry: dark brick base with mud-brick clusters, packed mud above, iron pilasters added later."""
    h = hash3(x, y, z, 101)
    if y <= 2:
        return "mossy_cobblestone" if (y <= 1 and h < 0.12) else (SB if h < 0.75 else MSB)
    v = vnoise(x + z * 0.7, y * 1.3, 3.0, 102)
    if v < 0.25:
        return MUD
    return BRICK if h < 0.9 else "granite"


def roof(C, x0, z0, x1, z1, y, axis, over=1, gable=BRICK, inner=SP):
    """A pitched roof of weathered copper: stairs stepping in one per block of rise from an eave ``over`` outside the
    walls, solid underneath (no sealed void), brick gables. ``axis`` is the ridge direction."""
    if axis == "z":
        lo, hi = x0 - over, x1 + over
        a0, a1 = z0 - over, z1 + over
    else:
        lo, hi = z0 - over, z1 + over
        a0, a1 = x0 - over, x1 + over
    top = y
    for b in range(lo, hi + 1):
        k = min(b - lo, hi - b)
        yy = y + k
        top = max(top, yy)
        for a in range(a0, a1 + 1):
            x, z = (b, a) if axis == "z" else (a, b)
            if b - lo == hi - b:
                spec = CU
            elif b - lo < hi - b:
                spec = stair(CU_ST, "east" if axis == "z" else "south")
            else:
                spec = stair(CU_ST, "west" if axis == "z" else "north")
            # mycelium creeping over the lower roof
            if k <= 3 and vnoise(x, z, 4.0, 103) > 0.72:
                spec = MYC
                C.set(x, yy, z, spec)
                if hash01(x, z, 104) < 0.4:
                    C.put(x, yy + 1, z, "brown_mushroom" if hash01(x, z, 105) < 0.6 else "red_mushroom")
            else:
                C.set(x, yy, z, spec)
            if x0 <= x <= x1 and z0 <= z <= z1:
                end = (a in (z0, z1)) if axis == "z" else (a in (x0, x1))
                for yf in range(y, yy):
                    C.set(x, yf, z, gable if end else inner)
    return top


def hall_shell(C, rect, h, axis, window_rows=((3, 5),)):
    """A brick hall: stone floor, walls 1..h, iron pilasters every 6, a brass string course under the eaves, amber
    windows between pilasters, interior air, a flat spruce ceiling at h on dark oak beams, a copper roof above."""
    x0, z0, x1, z1 = rect
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, 0, z, (SB if hash01(x, z, 111) < 0.7 else "polished_andesite") if not edge else SB)
            C.set(x, -1, z, "stone")
            for y in range(1, h):
                if edge:
                    C.set(x, y, z, brick_wall(x, y, z))
                else:
                    C.clear(x, y, z)
            if edge:
                C.set(x, h, z, GILD if (x + z) % 2 else BRASS)
            else:
                beam = (z - z0) % 4 == 0 if axis == "x" else (x - x0) % 4 == 0
                C.set(x, h, z, (DO_LOG_X if axis == "z" else DO_LOG_Z) if beam else SP)
    # pilasters and windows
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)):
                continue
            u = (z - z0) if x in (x0, x1) else (x - x0)
            corner = x in (x0, x1) and z in (z0, z1)
            if corner or u % 6 == 0:
                for y in range(1, h):
                    C.set(x, y, z, IRON if y > 2 else SB)
                continue
            if u % 6 in (2, 3, 4):
                for (wa, wb) in window_rows:
                    for y in range(wa, wb + 1):
                        if y < h - 1:
                            C.set(x, y, z, AMBER)
    return roof(C, x0, z0, x1, z1, h + 1, axis)


def doorway(C, cells, y0=1, h=4, sill=SB):
    """Open a doorway through a wall: the cells (x, z) cleared y0 .. y0 + h - 1, a sill below and a brass lintel."""
    for (x, z) in cells:
        C.set(x, y0 - 1, z, sill)
        for y in range(y0, y0 + h):
            C.clear(x, y, z)
        C.set(x, y0 + h, z, GILD)


def passage(C, x0, z0, x1, z1, h=4, axis="x"):
    """A covered brick passage: floor, side walls, a flat roof with a copper cap."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            side = (z in (z0, z1)) if axis == "x" else (x in (x0, x1))
            C.set(x, 0, z, SB if not side else BRICK)
            C.set(x, -1, z, "stone")
            for y in range(1, h + 1):
                if side:
                    C.set(x, y, z, brick_wall(x, y, z) if y < h else IRON)
                else:
                    C.clear(x, y, z)
            C.set(x, h + 1, z, CU)
            C.put(x, h + 2, z, slab(CU_SL) if not side else stair(CU_ST, "north" if z == z1 else "south")
                  if axis == "x" else stair(CU_ST, "west" if x == x1 else "east"))
    # one lamp in the middle
    mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
    C.set(mx, h, mz, EDISON)


def line_walls(C, cells, spec=SB):
    """Line underground air with masonry wherever the template would otherwise leave raw terrain."""
    for (x, y, z) in cells:
        for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
            q = (x + dx, y + dy, z + dz)
            if C.get(*q) is None:
                C.set(*q, spec(*q) if callable(spec) else spec)


def vat(C, cx, cz, y0, h, r=2.6, body=COPPER, band=BRASS, dome=True, seed=0):
    """A spore vat or still: a riveted cylinder with bands, a domed lid, a gauge and a valve."""
    R = int(r) + 1
    for y in range(y0, y0 + h):
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= r:
                    spec = body
                    if (y - y0) % 4 == 0:
                        spec = band
                    elif d > r - 1 and hash3(x, y, z, 120 + seed) < 0.12:
                        spec = VERD
                    C.set(x, y, z, spec)
    if dome:
        rr = r - 0.6
        y = y0 + h
        while rr > 0.4:
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    if math.hypot(x - cx, z - cz) <= rr:
                        C.set(x, y, z, CU2 if rr > 1 else BRASS)
            rr -= 1.2
            y += 1
        C.set(cx, y, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def gantry_light(C, x, y, z):
    hang(C, x, y, z, CHANDELIER, reach=10)


# ------------------------------------------------------------------ the approach: camp, path, gate
def camp(C):
    """The spore-gatherers' camp: three tents, a stew pot on the fire, baskets of gathered mushrooms, a handcart and
    the entrance waystone."""
    cx, cz = 2, 84
    for (tx, tz, col) in ((cx - 10, cz - 3, "brown"), (cx + 5, cz - 5, "white"), (cx - 3, cz + 4, "red")):
        for z in range(tz, tz + 5):
            C.set(tx, 1, z, SP_FENCE)
            C.set(tx + 4, 1, z, SP_FENCE)
            C.set(tx, 2, z, f"{col}_wool")
            C.set(tx + 4, 2, z, f"{col}_wool")
            for x in range(tx + 1, tx + 4):
                C.set(x, 3 if x != tx + 2 else 4, z, f"{col if z % 2 else 'light_gray'}_wool")
            C.set(tx + 1, 3, z, f"{col}_wool")
            C.set(tx + 3, 3, z, f"{col}_wool")
        C.set(tx + 2, 1, tz + 3, f"{col}_bed[facing=south,part=head,occupied=false]")
        C.set(tx + 2, 1, tz + 2, f"{col}_bed[facing=south,part=foot,occupied=false]")
    C.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    C.set(cx, 2, cz, "water_cauldron[level=3]")
    for (x, z, f) in ((cx - 2, cz, "east"), (cx + 2, cz, "west"), (cx, cz - 2, "south")):
        C.set(x, 1, z, stair(SP_ST, f))
    # baskets of mushrooms (composters full of caps), sacks, a handcart
    for i, (x, z) in enumerate(((cx + 6, cz + 3), (cx + 7, cz + 3), (cx + 6, cz + 4), (cx - 7, cz + 4))):
        C.set(x, 1, z, "composter[level=7]")
        C.put(x, 2, z, "red_mushroom" if i % 2 else "brown_mushroom")
    chest(C, cx - 9, 1, cz + 2, "east", "sr_camp")
    barrel(C, cx + 8, 1, cz - 1)
    C.set(cx + 8, 2, cz - 1, BROWN)
    for x in (cx + 10, cx + 12):
        C.set(x, 1, cz + 1, "grindstone[face=floor,facing=north]")
    for x in range(cx + 10, cx + 13):
        C.set(x, 2, cz + 1, slab(SP_SL, "bottom"))
    C.set(cx + 11, 2, cz + 2, SP_FENCE)
    waystone(C, cx - 2, 1, cz - 6)
    C.set(cx - 2, 0, cz - 6, "polished_andesite")
    mlamp(C, cx - 4, 1, cz - 7)
    mlamp(C, cx + 4, 1, cz + 9, red=False)
    BUSY.append((cx - 13, cz - 8, cx + 13, cz + 10))


def gate(C):
    """The pipe gate: two brick towers banded with iron and a copper pipe arch between them; from the path its
    arch frames the great mushroom (the reveal)."""
    zg = 52
    for sx in (-1, 1):
        x0 = sx * 7 - 1
        for x in range(x0, x0 + 3):
            for z in range(zg - 1, zg + 2):
                for y in range(0, 15):
                    edge = x in (x0, x0 + 2) and z in (zg - 1, zg + 1)
                    spec = IRON if edge else brick_wall(x, y, z)
                    if y % 5 == 0 and y > 0:
                        spec = BRASS
                    C.set(x, y, z, spec)
                C.set(x, 15, z, CU)
        C.set(sx * 7, 16, zg, VERD)
        C.set(sx * 7, 17, zg, "lightning_rod[facing=up,powered=false,waterlogged=false]")
        C.set(sx * 7, 12, zg + 2 * 1, GAUGE)
        C.set(sx * 7, 12, zg - 2, GAUGE)
        mlamp(C, sx * 9 + sx, 1, zg + 3)
    # the arch: a semicircle of pipe from tower to tower, with a brass keystone
    for x in range(-6, 7):
        yy = 9 + int(round(math.sqrt(max(0.0, 36 - x * x)) * 0.9))
        for z in (zg - 1, zg, zg + 1):
            C.set(x, yy, z, PIPES if z == zg else COPPER)
        if x == 0:
            C.set(0, yy + 1, zg, GILD)
    for z in (zg, zg - 1, zg + 1):
        for y in range(1, 9):
            for x in range(-5, 6):
                if C.get(x, y, z) is None:
                    C.clear(x, y, z)
    C.set(0, 8, zg + 1, CHAIN)
    C.set(0, 7, zg + 1, LANT_H)
    BUSY.append((-10, zg - 3, 10, zg + 3))


def approach(C):
    path(C, [(0, 78), (4, 72), (6, 64), (2, 58), (0, 52), (0, 46)], 5)
    path(C, [(-10, 84), (-30, 70), (-34, 46), (-46, 26)], 3, kind="side")   # the gatherers' trail round the west
    for (x, z) in ((5, 74), (-4, 66), (9, 62), (-4, 56)):
        mlamp(C, x, 1, z, red=hash01(x, z, 7) < 0.5)
    BUSY.append((-6, 46, 10, 80))


# ------------------------------------------------------------------ the press yard (hub)
def yard(C):
    x0, z0, x1, z1 = YARD
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            r = math.hypot(x, z - 32)
            if 4.5 <= r <= 6.5:
                spec = TREAD
            elif (x + z) % 9 == 0 or (x - z) % 9 == 0:
                spec = BRICK
            else:
                spec = SB if hash01(x, z, 131) < 0.8 else "cracked_stone_bricks"
            C.set(x, 0, z, spec)
            C.set(x, -1, z, "stone")
            for y in range(1, 5):
                C.clear(x, y, z)
    # low walls with pipe runs on top (east, west, south), openings: south gate, east to the distillery
    for z in range(z0 + 3, z1 + 1):
        for x in (x0, x1):
            if x == x1 and 17 <= z <= 21:
                continue
            C.set(x, 1, z, brick_wall(x, 1, z))
            C.set(x, 2, z, BRICK_WALL if z % 6 else IRON)
            if z % 6 == 0:
                C.set(x, 3, z, LANT)
    for x in range(x0, x1 + 1):
        if -3 <= x <= 3:
            continue
        C.set(x, 1, z1, brick_wall(x, 1, z1))
        C.set(x, 2, z1, BRICK_WALL if x % 6 else IRON)
    for z in range(z0 + 3, z1 + 1):
        C.set(x0, 3, z, PIPES) if z % 6 else None
    # the great spore vat (focal point), pipes from it to the press hall wall at y 8
    vat(C, 0, 32, 1, 11, r=3.3, seed=1)
    C.set(0, 4, 28, GAUGE)
    C.set(0, 3, 28, W + "valve_wheel[facing=north]")
    for z in range(13, 29):
        C.set(0, 9, z, PIPES)
    for z in (16, 22):
        for y in range(1, 9):
            C.set(0, y, z, IRON_POST())
    # benches, crates, sacks, a handcart, mushroom lamps at the corners
    for (x, z, f) in ((-8, 30, "east"), (-8, 31, "east"), (-8, 34, "east"), (-8, 35, "east"),
                      (8, 30, "west"), (8, 31, "west"), (8, 34, "west"), (8, 35, "west")):
        C.set(x, 1, z, stair(SP_ST, f))
    for (x, z) in ((-17, 40), (-16, 40), (-17, 41), (16, 26), (17, 26), (17, 27)):
        barrel(C, x, 1, z)
    C.set(-16, 2, 40, BROWN)
    for (x, z) in ((14, 43), (15, 43)):
        C.set(x, 1, z, "brown_wool")
        C.set(x, 2, z, "brown_carpet")
    for (x, z) in ((-18, 44), (18, 44), (-18, 16), (18, 15)):
        mlamp(C, x, 1, z)
    waystone(C, -6, 1, 40)
    C.set(-6, 0, 40, GILD)
    chest(C, 17, 1, 40, "west", "sr_yard")
    BUSY.append((x0 - 1, z0 - 1, x1 + 1, z1 + 1))


def IRON_POST():
    return W + "dark_iron_plating_wall"


# ------------------------------------------------------------------ the press hall
def screw_press(C, cx, cz):
    """A giant screw press: an iron basin of spore mash, a brass platen, a threaded screw through the crosshead of an
    iron gantry, a capstan of spruce arms on top."""
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            edge = abs(x - cx) == 3 or abs(z - cz) == 3
            C.set(x, 1, z, IRON if edge else BROWN)
            if edge:
                C.set(x, 2, z, IRON_POST() if (x + z) % 2 else IRON)
            elif abs(x - cx) <= 2 and abs(z - cz) <= 2:
                C.set(x, 2, z, "brown_carpet" if hash01(x, z, 141) < 0.6 else "red_carpet")
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            C.set(x, 6, z, BRASS if abs(x - cx) < 2 and abs(z - cz) < 2 else W + "brass_plating_slab[type=top]")
    # the screw: an iron core with a copper thread winding up
    th = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    for y in range(7, 19):
        C.set(cx, y, cz, IRON)
        dx, dz = th[y % 4]
        C.set(cx + dx, y, cz + dz, COPPER)
    # the gantry: two 2x2 iron columns and a crosshead beam
    for sx in (-1, 1):
        for x in (cx + sx * 4, cx + sx * 5):
            for z in (cz - 1, cz):
                for y in range(1, 16):
                    C.set(x, y, z, IRON if y % 5 else BRASS)
    for x in range(cx - 5, cx + 6):
        for z in (cz - 1, cz, cz + 1):
            for y in (13, 14):
                if x == cx and z == cz:
                    continue
                if abs(x - cx) <= 1 and abs(z - cz) <= 1 and (x, z) != (cx, cz):
                    if C.get(x, y, z) == "brasshaven:copper_plating":
                        continue
                C.set(x, y, z, BRASS if y == 13 else IRON)
    C.set(cx, 13, cz, GILD)
    # capstan
    for i in range(-3, 4):
        C.set(cx + i, 19, cz, "stripped_spruce_log[axis=x]")
        C.set(cx, 19, cz + i, "stripped_spruce_log[axis=z]")
    C.set(cx, 19, cz, GEAR)
    # a spout of copper from the basin into a collecting tub
    C.set(cx + 3, 2, cz + 4, "cauldron")
    C.set(cx + 3, 3, cz + 3, "waxed_copper_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")


def press_hall(C):
    x0, z0, x1, z1 = PRESS
    top = hall_shell(C, PRESS, 16, "z", window_rows=((3, 6), (10, 13)))
    # the monitor: a glazed clerestory along the ridge under its own copper roof
    for z in range(z0 + 4, z1 - 3):
        for x in range(-3, 4):
            for y in range(top - abs(x) if abs(x) < 3 else top - 3, top + 3):
                if abs(x) == 3:
                    post = (z - z0) % 4 == 0 or z in (z0 + 4, z1 - 4)
                    C.set(x, y, z, IRON if (post or y < top) else AMBER)
                else:
                    C.set(x, y, z, SP)
    for x in range(-3, 4):
        for z in (z0 + 4, z1 - 4):
            for y in range(top - 3, top + 3):
                if C.get(x, y, z) in (None, AIR) or abs(x) < 3:
                    C.set(x, y, z, BRICK)
    roof(C, -3, z0 + 4, 3, z1 - 4, top + 3, "z")
    chimney(C, 18, -19, top + 4)
    chimney(C, 18, 1, top - 2)
    # the gallery over the south door: sacks and crates, a stair along the west wall
    for x in range(x0 + 1, x1):
        for z in range(9, z1):
            C.set(x, 7, z, SP if (x + z) % 3 else "stripped_spruce_wood[axis=y]")
        if not (x0 + 1 <= x <= x0 + 3):
            railing(C, x, 8, 9, "north")
    for x in range(x0 + 1, x1, 5):
        C.set(x, 6, 9, stair(SP_ST, "south", "top"))
    for i in range(7):
        for x in range(x0 + 1, x0 + 4):
            C.set(x, i + 1, 2 + i, stair(SP_ST, "south"))
            for y in range(1, i + 1):
                C.set(x, y, 2 + i, SP)
            for hh in range(1, 4):
                C.clear(x, i + 1 + hh, 2 + i)
    for x in range(x0 + 6, x1 - 1, 2):
        C.set(x, 8, 11, "brown_wool" if x % 4 else "barrel[facing=up,open=false]")
    chest(C, x1 - 2, 8, 11, "north", "sr_gallery")
    # south door from the yard (5 wide, 6 high, a wicket of iron bars above), west door to the fermentation hall
    doorway(C, [(x, z1) for x in range(-2, 3)], h=6)
    doorway(C, [(x0, z) for z in (-6, -5, -4)], h=4)
    screw_press(C, -7, -8)
    screw_press(C, 7, -8)
    # conveyor of spore cake: a row of hay bales on spruce trestles to the tubs, sacks along the east wall
    for x in range(-3, 4):
        C.set(x, 1, -2, SP_FENCE if x % 3 else SP)
        C.set(x, 2, -2, "hay_block[axis=x]" if x % 2 else BROWN)
    for z in range(-18, -12):
        C.set(x1 - 1, 1, z, "brown_wool")
        C.set(x1 - 1, 2, z, "brown_carpet" if z % 2 else "barrel[facing=up,open=false]")
    # the foreman's corner (north-west): a partition, his desk, the order book, a chest
    for x in range(x0 + 1, x0 + 8):
        C.set(x, 1, -14, MUD if x != x0 + 4 else AIR)
        C.set(x, 2, -14, SP_FENCE if x != x0 + 4 else AIR)
    C.set(x0 + 2, 1, -18, TABLE)
    C.set(x0 + 2, 2, -18, "candle[candles=2,lit=true,waterlogged=false]")
    C.set(x0 + 3, 1, -18, W + "mahogany_chair[facing=west]")
    chest(C, x0 + 1, 1, -21, "east", "sr_press")
    C.set(x0 + 1, 2, -16, W + "wall_shelf[facing=east]")
    spawner(C, x0 + 5, 1, -19, MOB_MITE)
    spawner(C, 0, 1, -14, MOB_AUTO)
    # gauge wall on the north, pipes from the presses up into the ceiling
    for x in range(-12, 13, 3):
        C.set(x, 4, z0 + 1, GAUGE)
        for y in range(5, 18):
            C.set(x, y, z0 + 1, PIPES)
    # chandeliers and wall lamps
    for (x, z) in ((-7, -1), (7, -1), (0, 6), (-7, -15), (7, -15)):
        gantry_light(C, x, 12, z)
    for z in (-12, 0, 8):
        C.set(x0 + 1, 4, z, EDISON)
        C.set(x1 - 1, 4, z, EDISON)
    # the cellar stair: a hole by the east wall at x 10..12, z 1..3, railed
    for x in range(9, 14):
        for z in range(0, 4):
            if 10 <= x <= 12 and 1 <= z <= 3:
                continue
            railing(C, x, 1, z, "north" if z == 0 else ("west" if x == 9 else "east"))
    # the M1 base passage on the north side: the iron door from the stem
    BUSY.append((x0 - 1, z0 - 1, x1 + 1, z1 + 1))



def roof_vents(C):
    """Copper cowls on the fermentation hall's ridge, venting the vats."""
    x0, z0, x1, z1 = FERM
    xm = (x0 + x1) // 2
    ytop = FERM_H + 1 + (x1 - x0) // 2 + 1
    for zc in (z0 + 6, (z0 + z1) // 2, z1 - 6):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(ytop - 2, ytop + 2):
                    C.set(xm + dx, y, zc + dz, GRILLE if (dx or dz) and y == ytop else CU2)
                C.set(xm + dx, ytop + 2, zc + dz, stair(CU_ST, face_of(-dx, -dz)) if (dx or dz) else CU)
        C.set(xm, ytop + 3, zc, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def chimney(C, x0, z0, ytop):
    """A 3 x 3 smokestack of sooty brick with brass bands and a signal-fire plume."""
    for x in range(x0, x0 + 3):
        for z in range(z0, z0 + 3):
            for y in range(0, ytop):
                edge = x in (x0, x0 + 2) or z in (z0, z0 + 2)
                if not edge and y > 0:
                    C.set(x, y, z, W + "sooty_smokestack_bricks" if y > ytop - 4 else SB)
                    continue
                spec = W + "smokestack_bricks" if y < ytop - 6 else W + "sooty_smokestack_bricks"
                if y % 9 == 4:
                    spec = BRASS
                C.set(x, y, z, spec)
            C.set(x, ytop, z, IRON if (x + z) % 2 else W + "smokestack_brick_slab[type=bottom,waterlogged=false]")
    C.set(x0 + 1, ytop, z0 + 1, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    C.set(x0 + 1, ytop - 1, z0 + 1, "hay_block[axis=y]")

# ------------------------------------------------------------------ the fermentation hall
def ferm_hall(C):
    x0, z0, x1, z1 = FERM
    hall_shell(C, FERM, FERM_H, "z", window_rows=((3, 5), (7, 9)))
    roof_vents(C)
    doorway(C, [(x1, z) for z in (-6, -5, -4)])
    doorway(C, [(x0, z) for z in (-3, -2, -1)])
    # six vats in two rows (east row x -29, west row x -40 only at the ends), the aisle in the middle
    for (cx, cz) in ((-29, -8), (-29, 4), (-29, 16), (-41, -9), (-41, 16)):
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                if math.hypot(x - cx, z - cz) <= 3.6:
                    C.set(x, 0, z, IRON)
        vat(C, cx, cz, 1, 8, r=3.4, body="stripped_oak_wood[axis=y]", band=IRON, dome=False, seed=cx + cz)
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if math.hypot(x - cx, z - cz) <= 2.4:
                    C.set(x, 9, z, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,"
                                   "waterlogged=false]")
        C.set(cx, 9, cz, CUB)
        # a pipe from each vat up to the ceiling manifold
        for y in range(10, FERM_H):
            C.set(cx + 2, y, cz, PIPES)
        C.set(cx - 4 if cx > -35 else cx + 4, 3, cz, W + "valve_wheel[facing=%s]" % ("west" if cx > -35 else "east"))
    for z in range(z0 + 1, z1):
        C.set(-27, FERM_H - 1, z, PIPES)
        C.set(-39, FERM_H - 1, z, PIPES)
    # the chute pool by the west wall (x -43..-41, z 1..3), fed from the drying loft above
    for x in range(-44, -39):
        for z in range(0, 5):
            edge = x in (-44, -40) or z in (0, 4)
            if edge:
                C.set(x, 0, z, CU)
                C.set(x, 1, z, CU_ST.replace("stairs", "slab") + "[type=bottom,waterlogged=false]")
            else:
                for y in (-2, -1, 0):
                    C.water(x, y, z)
                C.set(x, -3, z, "clay")
    line_walls(C, [(x, y, z) for x in range(-43, -40) for z in range(1, 4) for y in (-2, -1, 0)], SB)
    # bubbling cauldrons and a gauge wall, the brewers' bench
    for z in (-12, -11):
        C.set(-34, 1, z, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    C.set(-35, 1, -12, TABLE)
    C.set(-33, 1, -12, "water_cauldron[level=1]")
    for z in range(-12, 21, 4):
        C.set(x1 - 1, 5, z, GAUGE)
    for (x, z) in ((-35, -8), (-35, 4), (-35, 16)):
        gantry_light(C, x, 10, z)
    for z in (-10, 10):
        C.set(x0 + 1, 4, z, EDISON)
    chest(C, -35, 1, 20, "north", "sr_ferment")
    barrel(C, -26, 1, 21)
    barrel(C, -27, 1, 21)
    spawner(C, -35, 1, 9, MOB_WITCH)
    spawner(C, -42, 1, 8, MOB_BOGGED)
    BUSY.append((x0 - 1, z0 - 1, x1 + 1, z1 + 1))


# ------------------------------------------------------------------ the distillery
def distillery(C):
    x0, z0, x1, z1 = DIST
    hall_shell(C, DIST, 14, "x", window_rows=((3, 6), (9, 11)))
    doorway(C, [(x0, z) for z in (18, 19, 20)])
    doorway(C, [(x1, z) for z in (3, 4, 5)])
    # three pot stills on brick fireboxes, swan necks to a condenser coil each
    for i, (cx, cz) in enumerate(((29, 10), (29, 22), (38, 16))):
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                C.set(x, 1, z, BRICK)
        C.set(cx, 1, cz + 2 if cx < 35 else cz, "blast_furnace[facing=south,lit=true]" if cx < 35 else BRICK)
        rr = 2.6
        for y in range(2, 8):
            k = 1 - abs(y - 4.5) / 4.0
            for x in range(cx - 3, cx + 4):
                for z in range(cz - 3, cz + 4):
                    if math.hypot(x - cx, z - cz) <= rr * (0.55 + 0.45 * k) + 0.4:
                        C.set(x, y, z, COPPER if (y + x) % 5 else BRASS)
        for y in range(8, 11):
            C.set(cx, y, cz, CUB)
        # swan neck to the condenser
        tx = cx + (4 if cx < 35 else -4)
        for x in range(min(cx, tx), max(cx, tx) + 1):
            C.set(x, 11, cz, PIPES)
        for y in range(2, 11):
            C.set(tx, y, cz, PIPES if y % 2 else VERD)
        C.set(tx, 1, cz, "cauldron")
    # barrel racks along the south wall, brewing stands, the stillmaster's ledger
    for x in range(x0 + 2, x1 - 1):
        if x in (33, 34, 35):
            continue
        C.set(x, 1, z1 - 1, SP_FENCE if x % 2 else "barrel[facing=north,open=false]")
        C.set(x, 2, z1 - 1, "barrel[facing=north,open=false]")
        C.set(x, 3, z1 - 1, slab(SP_SL, "bottom"))
    for x in (40, 41):
        C.set(x, 1, 26, TABLE)
        C.set(x, 2, 26, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    chest(C, 42, 1, 24, "west", "sr_distillery")
    spawner(C, 34, 1, 26, MOB_GUNNER)
    for (x, z) in ((33, 9), (33, 22), (38, 26)):
        gantry_light(C, x, 12, z)
    # four distillation columns on the north side, piped into the hall roof and to M3
    for (cx, cz, h) in ((28, -5, 30), (35, -6, 36), (42, -8, 20)):
        vat(C, cx, cz, 1, h, r=2.4, seed=cx)
        for z in range(cz + 3, z0):
            C.set(cx, 9, z, PIPES)
        C.set(cx, 9, z0, PIPES)
        # a ring catwalk halfway up
        yc = h // 2
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                d = math.hypot(x - cx, z - cz)
                if 2.6 < d <= 3.8:
                    C.put(x, yc, z, W + "diamond_plate_slab[type=top,waterlogged=false]")
    BUSY.append((x0 - 1, -12, x1 + 1, z1 + 1))


# ------------------------------------------------------------------ the spore cellars
def cellars(C):
    x0, z0, x1, z1 = CELLAR
    fy = -12
    air = []
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, fy, z, SB if not edge else MSB)
            if not edge and vnoise(x, z, 4.0, 151) > 0.66:
                C.set(x, fy, z, MYC)
            C.set(x, fy - 1, z, "stone")
            for y in range(fy + 1, -4):
                if edge:
                    C.set(x, y, z, MSB if (y < fy + 3 and hash3(x, y, z, 152) < 0.5) else SB)
                else:
                    C.clear(x, y, z)
                    air.append((x, y, z))
            C.set(x, -4, z, SB)
            C.set(x, -3, z, "stone")
    # vault ribs: piers every 7 with arches across the cellar
    for px in (-7, 0, 7):
        for pz in (-20, -14):
            for y in range(fy + 1, -4):
                for dx in (0, 1):
                    for dz in (0, 1):
                        C.set(px + dx, y, pz + dz, SB if y % 4 else "chiseled_stone_bricks")
    for pz in (-20, -14):
        for x in range(x0 + 1, x1):
            C.set(x, -5, pz, SB)
            C.set(x, -5, pz + 1, SB)
    # roots of the great mushroom breaking through the north half
    for i in range(7):
        rx = x0 + 3 + int(hash01(i, 3, 153) * (x1 - x0 - 6))
        rz = z0 + 2 + int(hash01(i, 4, 154) * 9)
        for y in range(fy + 1, -4):
            off = int((y - fy) * 0.25)
            for dx in (0, 1):
                C.set(rx + dx + (off if i % 2 else -off), y, rz, STEM)
        C.set(rx, fy, rz + 1, MYC)
        C.put(rx, fy + 1, rz + 1, "brown_mushroom")
    # barrel racks on the walls, the cistern, the cellar-master's table
    for z in range(z0 + 2, z1 - 1, 2):
        for x in (x0 + 1, x1 - 1):
            if C.get(x, fy + 1, z) == AIR:
                C.set(x, fy + 1, z, "barrel[facing=up,open=false]")
                C.set(x, fy + 2, z, "barrel[facing=up,open=false]" if z % 4 else BROWN)
    for x in range(-4, 3):
        for z in range(-25, -22):
            for y in (fy, fy - 1):
                C.water(x, y, z)
        C.set(x, fy + 1, -22, SB if x % 2 else "stone_brick_wall")
    line_walls(C, [(x, y, z) for x in range(-4, 3) for z in range(-25, -22) for y in (fy, fy - 1)], "clay")
    C.set(-6, fy + 1, -11, TABLE)
    C.set(-6, fy + 2, -11, "candle[candles=3,lit=true,waterlogged=false]")
    chest(C, x0 + 1, fy + 1, -9, "east", "sr_cellar")
    chest(C, x1 - 1, fy + 1, z0 + 1, "west", "sr_cellar")
    spawner(C, -10, fy + 1, -18, MOB_BOGGED)
    spawner(C, 10, fy + 1, -22, MOB_MITE)
    for (x, z) in ((-4, -11), (4, -17), (-10, -24), (10, -11)):
        hang(C, x, -6, z, LANT_H, reach=4)
    # the stair down from the press hall (x 10..12): treads z 3 .. -7, y -1 .. -11
    for i in range(11):
        z, y = 3 - i, -1 - i
        for x in range(10, 13):
            C.set(x, y, z, stair(SB_ST, "south"))
            for hh in range(1, 4):
                C.clear(x, y + hh, z)
                air.append((x, y + hh, z))
            for yy in range(fy, y):
                C.set(x, yy, z, SB)
    for x in range(10, 13):
        C.clear(x, 0, 1)
        C.clear(x, 0, 2)
        C.clear(x, 0, 3)
    # the exit: a corridor south under the hall (x -12..-10), then a stair up into the yard's stair-house
    for z in range(z1 + 1, 6):
        for x in range(-12, -9):
            C.set(x, fy, z, SB)
            for y in range(fy + 1, fy + 5):
                C.clear(x, y, z)
                air.append((x, y, z))
    for x in range(-12, -9):
        for y in range(fy + 1, fy + 5):
            C.clear(x, y, z1)
    for j in range(12):
        z, y = 6 + j, fy + 1 + j
        for x in range(-12, -9):
            C.set(x, y, z, stair(SB_ST, "south"))
            for yy in range(fy, y):
                C.set(x, yy, z, SB)
            for hh in range(1, 4):
                if y + hh <= 4:
                    C.clear(x, y + hh, z)
                    if y + hh < 0:
                        air.append((x, y + hh, z))
    line_walls(C, air)
    # the stair-house in the yard and its one-way iron door (opens only from the stair side)
    hx0, hz0, hx1, hz1 = HOUSE
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            edge = x in (hx0, hx1) or z in (hz0, hz1)
            for y in range(1, 5):
                if edge:
                    C.set(x, y, z, brick_wall(x, y, z) if not (x in (hx0, hx1) and z in (hz0, hz1)) else IRON)
                elif C.get(x, y, z) is None or z >= 18:
                    C.clear(x, y, z)
            if not edge and z >= 18:
                C.set(x, 0, z, SB)
            C.set(x, 5, z, CU)
    for x in range(hx0 - 1, hx1 + 2):
        C.set(x, 6, (hz0 + hz1) // 2, CU)
        for z in range(hz0 - 1, hz1 + 2):
            if C.get(x, 5, z) is None:
                C.set(x, 5, z, slab(CU_SL))
    iron_door(C, -11, 1, hz1, "south", 0, -1)
    C.set(-10, 3, 21, EDISON)


# ------------------------------------------------------------------ M1: base, chamber, arena, vault
def m1_base(C):
    """The stem's foot: the pool of the cap lift inside the core (its exit to the south), the newel's start, the
    passage to the press hall and the iron door that opens only from the stem side."""
    cx, cz = M1["c"]
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for y in (-2, -1, 0):
                C.water(cx + dx, y, cz + dz)
            C.set(cx + dx, -3, cz + dz, "clay")
            for y in range(1, VAULT_F + 1):
                C.clear(cx + dx, y, cz + dz)
    for y in (1, 2):
        C.clear(cx, y, cz + 2)
    C.set(cx, 0, cz + 2, SP)
    out, fy = stem_door(C, M1, 0, "south", head=4)
    # the passage on to the press hall's north wall (z -22)
    zs = out[0][1]
    for z in range(zs, PRESS[1]):
        for x in range(-6, -1):
            side = x in (-6, -2)
            C.set(x, 0, z, SB if not side else BRICK)
            for y in range(1, 5):
                if side:
                    C.set(x, y, z, brick_wall(x, y, z))
                else:
                    C.clear(x, y, z)
            C.set(x, 5, z, CU)
    for x in (-5, -3):
        for y in (1, 2, 3):
            C.set(x, y, PRESS[1], IRON)
    C.clear(-4, 3, PRESS[1])
    C.set(-4, 3, PRESS[1], IRON)
    iron_door(C, -4, 1, PRESS[1], "south", 0, -1)
    C.set(-4, 4, PRESS[1] - 2, EDISON)


def m1_landing_doors(C):
    """The newel's two doors: east at feet 31 (the catwalk), west at feet 46 (the rope bridge). Returns their outer
    end cells."""
    east, _ = stem_door(C, M1, 6, "east", floor=TREAD)
    west, _ = stem_door(C, M1, 9, "west", floor=SP)
    # a niche off landing 11 with the stem's guardian
    cx, cz = M1["c"]
    sx, sz, f = M1["_land"][11]
    for i in range(6, 9):
        for y in range(f, f + 3):
            C.clear(cx + sx * 4, y, cz + sz * i)
        C.set(cx + sx * 4, f - 1, cz + sz * i, TREAD)
    spawner(C, cx + sx * 4, f, cz + sz * 8, MOB_SPIDER)
    C.set(cx + sx * 4, f + 3, cz + sz * 8, EDISON)
    return east, west


def chamber(C):
    """The gills chamber on the annulus: a stem-flesh floor round the well, a brass rim with railings, the skirt
    hanging below, the hanging gill-boss (the vault) over the core's lift head, the grace waystone, benches and the
    ramp to the arena."""
    cx, cz = M1["c"]
    cells = M1["_cells"]
    for x in range(cx - 18, cx + 19):
        for z in range(cz - 18, cz + 19):
            r = math.hypot(x - cx, z - cz)
            if r > 17.5:
                continue
            if abs(x - cx) <= 2 and abs(z - cz) <= 2:
                continue
            if in_well(M1, x, z):
                ys = cells.get((x, z), [])
                if CHAMBER in ys:
                    continue
                if any(CHAMBER - 4 < y < CHAMBER for y in ys):
                    for yy in range(CHAMBER, CHAMBER + 3):
                        C.clear(x, yy, z)                  # over the last flight: the hole
                    continue
            spec = STEM
            if 16.5 < r:
                spec = BRASS
            elif 11 <= r <= 12:
                spec = TREAD
            C.set(x, CHAMBER, z, spec)
            if not in_well(M1, x, z):
                C.set(x, CHAMBER - 1, z, STEM)
                if r > 11.5:
                    for y in range(CHAMBER - 1 - int((r - 11) * 0.6), CHAMBER - 1):
                        C.set(x, y, z, STEM)
    # railings: the rim, and round the hole over the last flight
    for x in range(cx - 18, cx + 19):
        for z in range(cz - 18, cz + 19):
            r = math.hypot(x - cx, z - cz)
            if 16.5 < r <= 17.5 and not (9 <= x <= 13 and z < cz - 9):
                railing(C, x, CHAMBER + 1, z, face_of(x - cx, z - cz))
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            if C.get(x, CHAMBER, z) in (None, AIR):
                continue
            if (x, z) in cells and CHAMBER in cells[(x, z)]:
                continue
            if abs(x - cx) <= 2 and abs(z - cz) <= 2:
                continue
            for dx, dz in N4:
                q = (x + dx, z + dz)
                if in_well(M1, *q) and C.get(q[0], CHAMBER, q[1]) in (None, AIR) and \
                        not (abs(q[0] - cx) <= 2 and abs(q[1] - cz) <= 2):
                    railing(C, x, CHAMBER + 1, z, face_of(dx, dz))
                    break
    # the lift head: the core between floor and the gill-boss, clad with gears and gauges
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) == 2 or abs(dz) == 2:
                for y in range(CHAMBER + 1, VAULT_F):
                    spec = GEAR if (y - CHAMBER) % 3 == 2 else (IRON if abs(dx) == abs(dz) else BRASS)
                    C.set(cx + dx, y, cz + dz, spec)
    for (dx, dz, f) in ((0, -3, "north"), (0, 3, "south"), (-3, 0, "west"), (3, 0, "east")):
        C.set(cx + dx, CHAMBER + 4, cz + dz, W + "wall_cog[facing=%s]" % f)
        C.set(cx + dx, CHAMBER + 2, cz + dz, W + "valve_wheel[facing=%s]" % f)
    # the gill-boss: brass bands and lamps round the hanging cylinder
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 8, cz + 9):
            r = math.hypot(x - cx, z - cz)
            if 6.5 < r <= 7.5:
                C.set(x, 80, z, BRASS)
    for (x, z) in ((cx + 8, cz), (cx - 8, cz), (cx, cz + 8), (cx, cz - 8)):
        hang(C, x, 80, z, LANT_H, reach=5)
    # benches and a reading desk by the rim, spore jars (glass round shroomlight)
    for (x, z, f) in ((-12, cz + 6, "east"), (-12, cz + 7, "east"), (-12, cz - 6, "east"), (-12, cz - 7, "east")):
        fp(C, x, CHAMBER + 1, z, stair(SP_ST, f))
    for (x, z) in ((-9, cz + 12), (-10, cz - 11), (6, cz + 13)):
        fp(C, x, CHAMBER + 1, z, SHROOM)
        fp(C, x, CHAMBER + 2, z, "glass")
    waystone(C, -8, CHAMBER + 1, cz + 8)
    C.set(-8, CHAMBER, cz + 8, GILD)
    fp(C, 0, CHAMBER + 1, cz + 14, TABLE)
    fp(C, 0, CHAMBER + 2, cz + 14, "candle[candles=3,lit=true,waterlogged=false]")
    chest(C, -1, CHAMBER + 1, cz + 15, "north", "sr_gills")
    for (x, z) in ((-13, cz), (12, cz + 8), (-6, cz - 13)):
        hang(C, x, CHAMBER + 7, z, CHANDELIER, reach=12)


def arena_ramp(C):
    """The ramp from the chamber up through the cap (x 10..12, climbing south): open with parapets for six treads,
    then enclosed in a tunnel of stem flesh, the mist at its mouth; it opens into the arena deck."""
    cz = PZ
    for i in range(18):
        z, y = cz - 10 + i, CHAMBER + 1 + i
        for x in range(9, 14):
            side = x in (9, 13)
            if i < 6:
                for yy in range(CHAMBER + 1, y + (2 if side else 0)):
                    C.set(x, yy, z, STEM if yy < y or not side else BRASS)
                if not side:
                    C.set(x, y, z, stair(SP_ST, "south"))
                    for hh in range(1, 5):
                        C.clear(x, y + hh, z)
                continue
            top = 84 if y + 4 < 84 else min(DECK, y + 5)
            for yy in range(CHAMBER + 1, top + 1):
                if not side and y < yy <= y + 4:
                    continue
                if C.get(x, yy, z) in (None, AIR) or yy <= y or side or yy > y + 4:
                    if yy > DECK - 4 and not side and yy > y + 4:
                        continue
                    C.set(x, yy, z, STEM if yy != y or side else stair(SP_ST, "south"))
            if not side:
                C.set(x, y, z, stair(SP_ST, "south"))
                for hh in range(1, 5):
                    if y + hh <= DECK + 3:
                        C.clear(x, y + hh, z)
    # the mist across the tunnel mouth (tread 6)
    zm, ym = cz - 4, CHAMBER + 7
    C.bp.mist(10, ym + 1, zm, 12, ym + 4, zm)
    # railings round the deck opening
    for z in range(cz + 1, cz + 7):
        railing(C, 9, DECK + 1, z, "west")
        railing(C, 13, DECK + 1, z, "east")


def arena(C):
    """The boss arena: the flat top of the cap (r <= 22), fenced at r 21 with brass railings and stem posts crowned
    by mushroom lamps; the seal; the vault stair behind sealed bars."""
    cx, cz = M1["c"]
    for x in range(cx - 23, cx + 24):
        for z in range(cz - 23, cz + 24):
            r = math.hypot(x - cx, z - cz)
            if r > 21.5:
                continue
            if C.get(x, DECK, z) in (None, AIR) or "stairs" in (C.get(x, DECK, z) or ""):
                continue
            if 20.5 < r:
                railing(C, x, DECK + 1, z, face_of(x - cx, z - cz))
    for k in range(12):
        a = k * 2 * math.pi / 12 + 0.13
        x, z = int(round(cx + math.cos(a) * 21)), int(round(cz + math.sin(a) * 21))
        C.set(x, DECK + 1, z, STEM)
        C.set(x, DECK + 2, z, STEM)
        C.set(x, DECK + 3, z, SHROOM)
        C.set(x, DECK + 4, z, RED)
    # a gilded ring inlaid in the cap: the alchemists' circle the champion walks
    for x in range(cx - 15, cx + 16):
        for z in range(cz - 15, cz + 16):
            r = math.hypot(x - cx, z - cz)
            if 13.5 < r <= 14.5 and C.get(x, DECK, z) in ("minecraft:red_mushroom_block", "minecraft:mushroom_stem"):
                C.set(x, DECK, z, GILD)
    C.bp.boss_seal(cx, DECK, cz - 4, BOSS, 19)


def vault(C):
    """The refined-spore vault inside the gill-boss: shelves of spore jars, the chests, the cap lift's drop well in
    the floor; the stair up to the arena behind sealed bars."""
    cx, cz = M1["c"]
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 7, cz + 8):
            r = math.hypot(x - cx, z - cz)
            if r > 6.5:
                continue
            hole = abs(x - cx) <= 1 and abs(z - cz) <= 1
            if hole:
                C.clear(x, VAULT_F, z)
            else:
                C.set(x, VAULT_F, z, BTILE if (x + z) % 2 else GILD)
            for y in range(VAULT_F + 1, VAULT_F + 8):
                C.clear(x, y, z)
    # railings round the drop well, open on the north side
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if max(abs(x - cx), abs(z - cz)) == 2 and not (z == cz - 2 and abs(x - cx) <= 1):
                railing(C, x, VAULT_F + 1, z, face_of(x - cx, z - cz))
    # the stair from the arena: x 3..5, treads z cz+11 .. cz+3 at y 87 .. 79
    for i in range(-1, 9):
        z, y = cz + 11 - i, DECK - 1 - i
        for x in range(2, 7):
            side = x in (2, 6)
            for yy in range(VAULT_F, y + 5):
                if not side and y < yy <= y + 3:
                    C.clear(x, yy, z)
                    continue
                if not side and yy == y:
                    C.set(x, yy, z, stair(BTILE.replace("tiles", "tile_stairs"), "south"))
                    continue
                if yy > DECK:
                    continue
                if math.hypot(x - cx, z - cz) <= 6.5 and yy > y + 3:
                    continue
                if yy < y or side or yy > y + 3:
                    if math.hypot(x - cx, z - cz) <= 6.5 and side and yy > y + 3:
                        continue
                    C.set(x, yy, z, RED if math.hypot(x - cx, z - cz) > 6.5 else STEM)
            if not side:
                for hh in range(1, 4):
                    C.clear(x, y + hh, z)
    for z in range(cz + 9, cz + 12):
        railing(C, 2, DECK + 1, z, "west")
        railing(C, 6, DECK + 1, z, "east")
    for x in range(3, 6):
        for y in range(DECK - 3, DECK):
            C.set(x, y, cz + 8, MOD["vault_bars"])
    # shelves of refined spores and the chests
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            r = math.hypot(x - cx, z - cz)
            if 5.5 < r <= 6.5 and C.get(x, VAULT_F + 1, z) == AIR and not (2 <= x <= 6 and z > cz):
                C.set(x, VAULT_F + 1, z, BTILE if (x + z) % 2 else "glass")
                C.set(x, VAULT_F + 2, z, SHROOM if (x + z) % 2 else "glass")
                C.set(x, VAULT_F + 3, z, "glass")
    chest(C, cx - 4, VAULT_F + 1, cz - 2, "east", "sr_vault")
    chest(C, cx - 4, VAULT_F + 1, cz + 2, "east", "sr_vault")
    chest(C, cx + 1, VAULT_F + 1, cz - 4, "south", "sr_vault")
    hang(C, cx - 3, VAULT_F + 6, cz + 3, CHANDELIER, reach=4)


# ------------------------------------------------------------------ M2: the drying lofts and the spore chute
def loft(C):
    """The drying lofts: a ring floor round the stem under the brown cap, racks of spore trays in sectors, lamps on
    chains from the cap, struts below; the waystone by the door; the chute hole to the fermentation hall."""
    cx, cz = M2["c"]
    f = LOFT_F
    out, _ = stem_door(C, M2, 9, "east")
    for x in range(cx - 21, cx + 22):
        for z in range(cz - 21, cz + 22):
            r = math.hypot(x - cx, z - cz)
            a = math.atan2(z - cz, x - cx)
            if r > 20.5 or r <= stem_r(M2, f, a) - 0.3:
                continue
            spec = SP if hash01(x, z, 181) < 0.85 else "stripped_spruce_wood[axis=y]"
            ad = (a % (math.pi / 4))
            if min(ad, math.pi / 4 - ad) * r < 0.6:
                spec = DO_LOG_X if abs(math.cos(a)) > 0.7 else DO_LOG_Z
            C.set(x, f, z, spec)
            for y in range(f + 1, f + 4):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)
            if 19.5 < r:
                C.set(x, f + 1, z, SP_FENCE)
    # struts from the stem to the outer floor (every 45 degrees)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        for s in range(0, 22):
            t = s / 21.0
            r = M2["ro"] + 0.5 + t * 10
            y = int(round(f - 12 + t * 11))
            x, z = int(round(cx + math.cos(a) * r)), int(round(cz + math.sin(a) * r))
            C.put(x, y, z, "spruce_log[axis=y]" if t > 0.95 else "stripped_spruce_wood[axis=y]")
    # racks of spore trays: arcs at r 12.5 and r 16.5, broken by aisles on the diagonals and at the door/chute
    for x in range(cx - 18, cx + 19):
        for z in range(cz - 18, cz + 19):
            r = math.hypot(x - cx, z - cz)
            a = math.atan2(z - cz, x - cx)
            ring = abs(r - 12.5) < 0.5 or abs(r - 16.5) < 0.5
            if not ring:
                continue
            ad = (a % (math.pi / 2))
            if min(ad, math.pi / 2 - ad) * r < 2.6:
                continue                                    # aisles on the axes
            if (x, f + 1, z) in C.keep:
                continue
            C.set(x, f + 1, z, SP_FENCE)
            C.set(x, f + 2, z, slab(SP_SL, "top"))
            C.set(x, f + 3, z, "brown_carpet" if hash01(x, z, 182) < 0.7 else "red_carpet")
    # lamps on chains from the cap, shroomlight trays
    for k in range(8):
        a = k * math.pi / 4
        for r in (11.0, 18.0):
            x, z = int(round(cx + math.cos(a) * r)), int(round(cz + math.sin(a) * r))
            hang(C, x, f + 4, z, LANT_H, reach=16)
    # the chute: a 3 x 3 hole at x -43..-41, z 1..3 with a copper funnel rim, its shaft down to the hall's roof
    for x in range(-44, -39):
        for z in range(0, 5):
            edge = x in (-44, -40) or z in (0, 4)
            if edge:
                for y in range(FERM_H + 1, f + 1):
                    C.set(x, y, z, CU if y % 6 else BRASS)
                C.set(x, f + 1, z, CU_ST.replace("stairs", "slab") + "[type=bottom,waterlogged=false]")
            else:
                for y in range(FERM_H, f + 3):
                    C.clear(x, y, z)
    waystone(C, out[0][0] + 1, f + 1, cz + 9)
    C.set(out[0][0] + 1, f, cz + 9, GILD)
    chest(C, cx - 15, f + 1, cz + 6, "east", "sr_loft")
    barrel(C, cx - 15, f + 1, cz + 7)
    C.set(cx - 15, f + 2, cz + 7, "hay_block[axis=y]")
    spawner(C, cx - 6, f + 1, cz - 14, MOB_DRONE)
    # a winch for hoisting trays
    C.set(cx + 4, f + 1, cz - 18, SP_LOG)
    C.set(cx + 6, f + 1, cz - 18, SP_LOG)
    C.set(cx + 5, f + 2, cz - 18, "stripped_spruce_log[axis=x]")
    C.set(cx + 5, f + 1, cz - 18, GEAR)


def rope_bridge(C, p0, p1, f0, f1, sag):
    """A sagging rope bridge: spruce slabs at half-block steps, fence rails with rope posts and lanterns."""
    (ax, az), (bx, bz) = p0, p1
    L = math.hypot(bx - ax, bz - az)
    ux, uz = (bx - ax) / L, (bz - az) / L
    cells = {}
    for x in range(int(min(ax, bx)) - 4, int(max(ax, bx)) + 5):
        for z in range(int(min(az, bz)) - 4, int(max(az, bz)) + 5):
            t = ((x - ax) * ux + (z - az) * uz) / L
            if t < -0.02 or t > 1.02:
                continue
            d = abs(-(x - ax) * uz + (z - az) * ux)
            if d <= 1.2:
                cells[(x, z)] = ("deck", min(1, max(0, t)))
            elif d <= 2.25:
                cells[(x, z)] = ("rail", min(1, max(0, t)))
    for (x, z), (kind, t) in sorted(cells.items()):
        h = f0 + (f1 - f0) * t - sag * math.sin(math.pi * t)
        hh = math.floor(h * 2) / 2
        n = math.floor(hh)
        if hh - n > 0.25:
            spec, fy = slab(SP_SL, "bottom"), n + 1
            by = n
        else:
            spec, fy = slab(SP_SL, "top"), n
            by = n - 1
        if kind == "rail":
            if (x, fy, z) in C.keep or (x, by, z) in C.keep:
                continue
            if C.solid(x, fy, z):
                continue
            C.set(x, by, z, spec)
            C.set(x, fy, z, SP_FENCE)
            step = round(t * L)
            if step % 6 == 0 and 0 < step < L - 2:
                C.set(x, fy + 1, z, SP_FENCE)
                if step % 12 == 0:
                    C.set(x, fy + 2, z, LANT)
        else:
            C.set(x, by, z, spec)
            for k in range(3):
                C.clear(x, fy + k, z)


def catwalk(C, p0, p1, fy):
    """A straight brass catwalk (3 wide, tread plate, iron-bar rails) at floor y ``fy`` on a lattice pylon."""
    (ax, az), (bx, bz) = p0, p1
    L = math.hypot(bx - ax, bz - az)
    ux, uz = (bx - ax) / L, (bz - az) / L
    for x in range(int(min(ax, bx)) - 4, int(max(ax, bx)) + 5):
        for z in range(int(min(az, bz)) - 4, int(max(az, bz)) + 5):
            t = ((x - ax) * ux + (z - az) * uz) / L
            if t < -0.03 or t > 1.03:
                continue
            d = abs(-(x - ax) * uz + (z - az) * ux)
            if d <= 1.3:
                if (x, fy, z) in C.keep:
                    continue
                C.set(x, fy, z, TREAD)
                C.set(x, fy - 1, z, IRON if round(t * L) % 4 == 0 else W + "dark_iron_plating_slab[type=top,"
                                                                                "waterlogged=false]")
                for k in range(1, 4):
                    if not C.solid(x, fy + k, z) or (x, fy + k, z) in C.keep:
                        C.clear(x, fy + k, z)
            elif d <= 2.3:
                if C.solid(x, fy, z) or (x, fy + 1, z) in C.keep:
                    continue
                C.set(x, fy, z, IRON)
                C.set(x, fy + 1, z, "iron_bars")
                if round(t * L) % 10 == 5:
                    C.set(x, fy + 2, z, LANT)
    # the pylon at the middle: a 3x3 iron lattice tower from the ground
    mx, mz = int(round((ax + bx) / 2)), int(round((az + bz) / 2))
    for y in range(0, fy - 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                corner = abs(dx) == 1 and abs(dz) == 1
                if corner:
                    C.set(mx + dx, y, mz + dz, IRON if y % 8 else BRASS)
                elif y % 4 == (0 if (dx + dz) % 2 else 2) and (dx or dz):
                    C.set(mx + dx, y, mz + dz, IRON_POST())
    BUSY.append((mx - 2, mz - 2, mx + 2, mz + 2))


# ------------------------------------------------------------------ M3: the alchemists' lab
def lab(C):
    """The alchemists' lab: a ring room round M3's stem under its cap (r 9..16), glass and brass walls, a copper
    roof; four sectors: benches and stills, the library, the specimen cases, the transmutation circle."""
    cx, cz = M3["c"]
    f = LAB_F
    out, _ = stem_door(C, M3, 6, "east")
    for x in range(cx - 17, cx + 18):
        for z in range(cz - 17, cz + 18):
            r = math.hypot(x - cx, z - cz)
            a = math.atan2(z - cz, x - cx)
            if r > 16.5 or r <= stem_r(M3, f, a) - 0.3:
                continue
            wall = r > 15.5
            C.set(x, f, z, (MAHOGANY_P if hash01(x, z, 191) < 0.8 else SP) if not wall else IRON)
            C.set(x, f - 1, z, IRON if r > 15.5 or (x + z) % 4 == 0 else W + "dark_iron_plating_slab[type=top,"
                                                                               "waterlogged=false]")
            for y in range(f + 1, f + 8):
                if wall:
                    ad = (a % (math.pi / 8))
                    post = min(ad, math.pi / 8 - ad) * r < 0.6
                    if y == f + 7 or post:
                        C.set(x, y, z, BRASS if post else GILD)
                    elif y in (f + 1,):
                        C.set(x, y, z, COPPER)
                    else:
                        C.set(x, y, z, "glass_pane" if y > f + 2 else COPPER)
                else:
                    C.bp.set(x, y, z, AIR)
            C.set(x, f + 8, z, CU if r > 9.5 else STEM)
    # sector partitions on the diagonals (bookshelf / brass screens with a 3-wide gap)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        for s in range(0, 40):
            r = 9.5 + s * 0.15
            if r > 15.4:
                break
            if 11.5 < r < 14.5:
                continue
            x, z = int(round(cx + math.cos(a) * r)), int(round(cz + math.sin(a) * r))
            for y in range(f + 1, f + 5):
                if (x, y, z) not in C.keep:
                    C.set(x, y, z, "bookshelf" if k % 2 else GRILLE)
    # east sector: benches with brewing stands and cauldrons, a retort on a brass stand
    for z in range(cz - 4, cz + 5, 2):
        fp(C, cx + 14, f + 1, z, TABLE)
        fp(C, cx + 14, f + 2, z, "brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    fp(C, cx + 12, f + 1, cz + 3, "water_cauldron[level=3]")
    fp(C, cx + 12, f + 1, cz - 3, "cauldron")
    fp(C, cx + 12, f + 2, cz - 3, "iron_bars")
    # north sector: the library
    for x in range(cx - 4, cx + 5):
        fp(C, x, f + 1, cz - 15, "bookshelf")
        fp(C, x, f + 2, cz - 15, "bookshelf" if x % 3 else "chiseled_bookshelf[facing=south,slot_0_occupied=true,"
                                                       "slot_1_occupied=false,slot_2_occupied=true,"
                                                       "slot_3_occupied=false,slot_4_occupied=false,"
                                                       "slot_5_occupied=true]")
    fp(C, cx, f + 1, cz - 12, "lectern[facing=south,has_book=false,powered=false]")
    fp(C, cx - 2, f + 1, cz - 12, W + "mahogany_chair[facing=north]")
    # west sector: specimen cases (glass over potted mushrooms on shelves)
    for z in range(cz - 5, cz + 6, 2):
        fp(C, cx - 14, f + 1, z, SP)
        fp(C, cx - 14, f + 2, z, "potted_red_mushroom" if z % 4 else "potted_brown_mushroom")
        fp(C, cx - 14, f + 3, z, "glass")
    # south sector: the transmutation circle (carpets and a brass core), an enchanting table
    for x in range(cx - 4, cx + 5):
        for z in range(cz + 9, cz + 15):
            r = math.hypot(x - cx, z - (cz + 12))
            if abs(r - 2.5) < 0.6:
                fp(C, x, f + 1, z, "purple_carpet")
            elif r < 0.6:
                fp(C, x, f + 1, z, "enchanting_table")
    chest(C, cx - 10, f + 1, cz + 11, "north", "sr_lab")
    chest(C, cx + 10, f + 1, cz - 11, "south", "sr_lab")
    spawner(C, cx - 11, f + 1, cz - 6, MOB_WITCH)
    for k in range(4):
        a = k * math.pi / 2
        x, z = int(round(cx + math.cos(a) * 12.5)), int(round(cz + math.sin(a) * 12.5))
        C.set(x, f + 7, z, HANG_LAMP_())
    # chains from the cap to the roof's edge (the lab hangs from the cap and rests on brackets)
    for k in range(8):
        a = k * math.pi / 4
        x, z = int(round(cx + math.cos(a) * 16)), int(round(cz + math.sin(a) * 16))
        for y in range(f + 9, f + 14):
            if C.get(x, y, z) is None:
                C.set(x, y, z, CHAIN)
        for s in range(8):
            t = s / 7.0
            r = M3["ro"] + 0.5 + t * 6.5
            y = int(round(f - 7 + t * 6))
            xx, zz = int(round(cx + math.cos(a + 0.2) * r)), int(round(cz + math.sin(a + 0.2) * r))
            C.put(xx, y, zz, IRON)


MAHOGANY_P = W + "mahogany_parquet"


def HANG_LAMP_():
    return W + "hanging_edison_lamp"


def lab_door(C, p):
    """Open the lab's outer wall where the catwalk arrives."""
    cx, cz = M3["c"]
    x, z = p
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            xx, zz = x + dx, z + dz
            if 15.0 < math.hypot(xx - cx, zz - cz) <= 16.6:
                C.set(xx, LAB_F, zz, TREAD)
                for y in range(LAB_F + 1, LAB_F + 4):
                    C.clear(xx, y, zz)


# ------------------------------------------------------------------ wild mushrooms and dressing
def wild(C):
    placed = []
    for i in range(160):
        x = int((hash01(i, 1, 201) - 0.5) * 170)
        z = int((hash01(i, 2, 202) - 0.5) * 160) + 6
        if math.hypot(x, z - 6) > 76:
            continue
        if in_busy(x, z, 4):
            continue
        if any(dist(x, z, M) < stem_r(M, 1, 0) + 6 for M in MUSH):
            continue
        if any(math.hypot(x - px, z - pz) < 9 for (px, pz) in placed):
            continue
        if not C.free(x, 1, z) or C.get(x, 0, z) is None:
            continue
        placed.append((x, z))
        small_mushroom(C, x, z, 5 + int(hash01(x, z, 203) * 4), hash01(x, z, 204) < 0.5, i)
        if len(placed) >= 26:
            break
    # small mushrooms on the mycelium
    for x in range(-80, 81):
        for z in range(-70, 90):
            if hash01(x, z, 205) < 0.02 and C.get(x, 0, z) == "minecraft:mycelium" and C.free(x, 1, z) and \
                    (x, 1, z) not in C.keep:
                C.put(x, 1, z, "red_mushroom" if hash01(x, z, 206) < 0.5 else "brown_mushroom")


# ------------------------------------------------------------------ the builder
def spore_refinery(bp):
    C = Ctx(bp)
    BUSY.clear()
    for r in (PRESS, FERM, DIST, YARD, HOUSE, (-50, -4, -47, 0), (21, 17, 23, 21), (45, 2, 48, 6),
              (-23, -7, -17, -3), (-6, -30, -2, -22)):
        BUSY.append(r)
    ground(C)
    for M in MUSH:
        stem(C, M)
        cap(C, M)
        newel(C, M)
    m1_base(C)
    stem_vats(C)
    cap_vents(C)
    east, west = m1_landing_doors(C)
    # the halls and the yard
    press_hall(C)
    ferm_hall(C)
    distillery(C)
    yard(C)
    passage(C, -23, -7, -17, -3)                      # press hall -> fermentation hall
    passage(C, 21, 17, 23, 21)                        # yard -> distillery
    m2_out, _ = stem_door(C, M2, 0, "east")
    passage(C, m2_out[0][0], -4, FERM[0] - 1, 0) if m2_out[0][0] < FERM[0] else None
    m3_out, _ = stem_door(C, M3, 0, "west")
    passage(C, DIST[2] + 1, 2, m3_out[0][0], 6) if m3_out[0][0] > DIST[2] else None
    cellars(C)
    chamber(C)
    arena_ramp(C)
    arena(C)
    vault(C)
    loft(C)
    lab(C)
    well_floor(C, M2, LOFT_F)
    well_floor(C, M3, LAB_F)
    # the rope bridge (loft -> M1 west door, feet 46) and the catwalk (M1 east door -> lab, feet 31)
    wx = min(p[0] for p in west) - 1
    wz = sum(p[1] for p in west) / 3.0
    for (x, z) in west:
        for dx in (0, -1):
            C.set(x + dx - 1 + 1, LOFT_F, z, SP)
    rope_bridge(C, (-45.0, -11.0), (wx + 0.5, wz), LOFT_F + 1, LOFT_F + 1, 3.0)
    ex = max(p[0] for p in east) + 1
    ez = sum(p[1] for p in east) / 3.0
    lab_door(C, (46, -11))
    catwalk(C, (ex - 0.5, ez), (46.0, -11.0), LAB_F)
    camp(C)
    gate(C)
    approach(C)
    wild(C)
    clear_above(C)


VIEWS = [
    ("press_hall", (2, 1, 9), (-7, 5, -6)),
    ("fermentation_hall", (-35, 1, 19), (-35, 6, -10)),
    ("drying_loft", (-46, 46, -4), (-60, 48, -16)),
    ("distillery", (43, 1, 27), (31, 6, 14)),
    ("alchemists_lab", (51, 31, 9), (60, 32, 13)),
    ("spore_cellars", (3, -11, -9), (3, -8, -24)),
    ("gills_chamber", (-14, 71, -30), (-4, 76, -36)),
    ("boss_arena", (0, 89, -22), (0, 92, -38)),
]

register(StructureDef(
    "spore_refinery", "overworld", ["mushroom_fields", "old_growth_spruce_taiga", "old_growth_pine_taiga"],
    [Piece("refinery", spore_refinery, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_BOGGED, 6, 1, 2), (MOB_WITCH, 3, 1, 1), (MOB_MITE, 3, 1, 2)],
    title_fr="La Raffinerie de spores", title_en="The Spore Refinery"))

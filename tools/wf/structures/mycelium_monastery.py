"""The Mycelium Monastery (Le Monastère du Mycélium): an abbey of steam monks who grafted their faith and their brass
onto living fungi, on a mycelium-crowned rock plateau. Colossal tier (tools/BUILDING.md §1, §12 concept 37, §10
legacy-dungeon template, §15), steampunk accents (tools/STYLE_STEAMPUNK.md: brass bands and copper pipes wound round the
stems, pot stills and column stills in the distillery, a bubble-column spore lift in a glass tube, brass chimneys
smoking through the cap).

Silhouette (one noun phrase, §15.1): one colossal fly agaric, a bulbous white stem 48 wide at its foot and a domed red
cap 69 wide spotted with white warts and pierced by two smoking brass chimneys and a glass cupola, standing on a
cliff-girt mycelium plateau over a cloister, with a small red dome tower, a flat brown tower and a white puffball dome
round it, tied to its stem by sagging rope bridges.

Layout, ground y = 0 (feet 1), x east, z south; the temple's axis is (MX, MZ) = (0, -28).
  * the massif: the plateau (top 16) carries the temple, the cloister, the ranges, the towers and the library; the
    gate terrace (top 6) under its south cliff; a crescent ridge of rock (top ~15) closes the terrace to the south and
    hides it; the pilgrims' camp on the flats south of the ridge (y 0);
  * the approach: from the camp (waystone) along the mushroom wood, north into the gorge through the ridge
    (compression), under the natural rock arch onto the gate terrace (the reveal: the agaric stands over the cliff),
    to the gatehouse between two capped turrets; the closed gate's wicket, the vaulted passage and the stair up
    inside the cliff to the gate hall;
  * the hub: the cloister garth, a meditation garden (sand garden, moss lawn, azaleas, koi pond, the mycelial font,
    waystone) in four arcaded walks. Branches: the south range (gate hall, porter's lodge, infirmary), the east range
    (the spore distillery: three pot stills, two column stills, vats, a gallery), the red tower beyond it (bell and
    drying loft in its cap), the west range (undercroft stair hall, monks' cells, refectory and kitchen), the brown
    tower (the abbot's lodge in its cap), the puffball library (two floors of shelves round the map of the great
    mycelium), the narthex under the west front (rose window) whose inner door into the temple is locked;
  * the main route: the undercroft stair in the west range down to the root catacombs (burial galleries, the monks'
    crypt, the ossuary), the glowing grotto (shroomlights, glow lichen, spore blossoms, a pool), the root heart under
    the temple, its stair up into the nave (the bulb of the stem, 17 high round the light well: pews, altar, the lift
    cage; waystone; the inner portal opens from here); the helix ramps up the stem: the chapter house (L1), the
    sporarium (L2), the gill gallery (L3, site of grace, waystone) and its annulus balcony under the cap; the turret
    stair (compression) up into the cap, the mist in the hatch house's door, the arena under the cap's dome (44 wide,
    gill-ribbed vault, glass oculus, six pore windows);
  * side route: from the distillery up the red tower and over its rope bridge into the chapter house (bypassing the
    catacombs); the brown tower's bridge to the chapter house and the library's bridge to the brown tower (loops);
  * the treasury: the spore reliquary in the cap's core under the arena, down a ladder under sealed bars;
  * shortcuts (§10.4): the reliquary's drop well down the light well into the pool of the lift cage in the nave (its
    iron door opens from inside only), the cage's bubble-column lift up to the gill gallery, the narthex's inner iron
    door (lever on the nave side only).
Loot gradient (§15.6): camp, gate 1; cloister, ranges, distillery 1-2; towers, library, catacombs 2; grotto, root
heart, nave 2-3; chapter house, sporarium 2-3; grace 3; the reliquary 3-5.
Height budget: the cupola's finial stands ~124 above the ground layer (mushroom fields lie at sea level).
"""
import math
import random

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, IRON_SLAB, PIPES,
                       TABLE, TREAD, TREAD_SLAB, VERD, W, fbm, hash01, hash3, out_facing, vnoise)
from ..parts import MOD
from .leviathan_lighthouse import gable as _lv_gable
from .leviathan_lighthouse import (Ctx, WALK, adelta, ang, barrel, blob_cells, box, candle, carve, chest, disk_pts,
                                   fill, fill_down, floor_ok, fput, hang, in_arc, in_rect, iron_door, lamp_post,
                                   lever, rail_at, railing, rails_round, reg, se, slab, spawner, spiral, stair_run,
                                   tent, walkway, waystone, wood_door)

# the champion of the cap's arena: the Mycelium Abbot (tools/BOSSES.md)
BOSS = "brasshaven:mycelium_abbot"
MOB_MONK = W + "bell_monk"
MOB_CRAWLER = W + "crypt_crawler"
MOB_WISP = W + "lantern_wisp"
MOB_KNIGHT = W + "skeleton_knight"
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_INK = W + "ink_wraith"
MOB_MITE = W + "rust_mite"
MOB_WITCH = "minecraft:witch"
MOB_BOGGED = "minecraft:bogged"

# ------------------------------------------------------------------ materials
AIR = "minecraft:air"
WATER = "water[level=0]"
STEM = "mushroom_stem"
RED = "red_mushroom_block"
BROWN = "brown_mushroom_block"
SHROOM = "shroomlight"
MYC = "mycelium[snowy=false]"
PODZOL = "podzol[snowy=false]"
GRASS = "grass_block[snowy=false]"
ENGR = W + "engraved_brass"
GILD = W + "gilded_trim"
BTILE = W + "brass_tiles"
GRILLE = W + "brass_grille"
DIB = W + "dark_iron_bricks"
IRON_WALL = W + "dark_iron_plating_wall"
IRON_ST = W + "dark_iron_plating_stairs"
MAHOG = W + "mahogany_panelling"
PARQ = W + "mahogany_parquet"
VALVE, COG, SHELF, CHAIR = W + "valve_wheel", W + "wall_cog", W + "wall_shelf", W + "mahogany_chair"
TUFB, TUFB_ST, TUFB_SL, TUFB_WALL = "tuff_bricks", "tuff_brick_stairs", "tuff_brick_slab", "tuff_brick_wall"
PTUF, PTUF_ST, PTUF_SL = "polished_tuff", "polished_tuff_stairs", "polished_tuff_slab"
CTUFB = "chiseled_tuff_bricks"
MUD, MUD_ST, MUD_SL, MUD_WALL = "mud_bricks", "mud_brick_stairs", "mud_brick_slab", "mud_brick_wall"
PMUD = "packed_mud"
CALC = "calcite"
SB, MSB, CSB = "stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"
SB_ST, SB_SL, SB_WALL = "stone_brick_stairs", "stone_brick_slab", "stone_brick_wall"
SPR, SPR_ST, SPR_SL, SPR_FENCE = "spruce_planks", "spruce_stairs", "spruce_slab", "spruce_fence"
SPR_LOG = "spruce_log[axis=y]"
DOAK, DOAK_ST, DOAK_SL, DOAK_FENCE = "dark_oak_planks", "dark_oak_stairs", "dark_oak_slab", "dark_oak_fence"
CU_OX, CUT_OX = "waxed_oxidized_copper", "waxed_oxidized_cut_copper"
CUT_OX_ST, CUT_OX_SL = "waxed_oxidized_cut_copper_stairs", "waxed_oxidized_cut_copper_slab"


class _SlabFix:
    """Ctx proxy for leviathan's gable: its ridge slab is named by string replacement, which leaves cut copper as a
    full block carrying slab properties; route those cells to the real slab."""
    def __init__(self, C):
        self._C = C

    def __getattr__(self, k):
        return getattr(self._C, k)

    def set(self, x, y, z, b, *a, **kw):
        if isinstance(b, str) and b.startswith(CUT_OX + "["):
            b = CUT_OX_SL + b[len(CUT_OX):]
        return self._C.set(x, y, z, b, *a, **kw)


def gable(C, *a, **kw):
    return _lv_gable(_SlabFix(C), *a, **kw)
CU_BLOCK, CUT_CU = "waxed_copper_block", "waxed_cut_copper"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
CHAIN_X, CHAIN_Z = "iron_chain[axis=x,waterlogged=false]", "iron_chain[axis=z,waterlogged=false]"
BULB = "waxed_copper_bulb[lit=true,powered=false]"
ROD_U = "lightning_rod[facing=up,powered=false,waterlogged=false]"
GLASS, PANE, AMBER = "glass", "glass_pane", "orange_stained_glass_pane"
GOLD = "gold_block"
BONE = "bone_block[axis=y]"
ROOTS = "mangrove_roots[waterlogged=false]"
HROOTS = "hanging_roots[waterlogged=false]"
ROOTED = "rooted_dirt"
MOSS, MOSS_C = "moss_block", "moss_carpet"
SKULL = "skeleton_skull[rotation={},powered=false]"
DV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# ------------------------------------------------------------------ dimensions
G = 16                               # plateau top block (feet 17)
GT = 6                               # gate terrace top block (feet 7)
MX, MZ = 0, -28                      # the temple's axis
L_FEET = (17, 36, 52, 68)            # stem levels: nave, chapter house, sporarium, gill gallery
L_SLAB = ((34, 35), (50, 51), (66, 67))
L3_CEIL = 77                         # gill gallery ceiling block
VAULT_F = 79                         # reliquary feet (floor 78)
AY = 84                              # arena floor block (feet 85)
AR = 22.0                            # arena floor radius
CAP_R = 34.5
WELL_R = 4.5                         # light well radius
DROP = (MX, MZ - 4)                  # the reliquary's drop column (in the light well)
TUR = (MX, MZ + 17)                  # the gill turret's axis
PLAT_C, PLAT_R = (0, -12), (72.0, 66.0)
GATE_C, GATE_R = (0, 63), (38.0, 11.0)
RIDGE_C, RIDGE_RAD, RIDGE_W = (0, 40), 46.0, 6.5
CAMP = (46, 104)
FLAT_C, FLAT_R = (22, 102), (66.0, 20.0)
GORGE_X = 6
CLO = (-19, 9, 19, 43)               # cloister walks outer rect x0, z0, x1, z1
GARTH = (-14, 14, 14, 38)            # the garth
SRANGE = (-20, 44, 20, 54)           # south range walls
ERANGE = (20, -2, 46, 44)            # east range (distillery) walls
WRANGE = (-40, 0, -20, 44)           # west range walls
NARTHEX = (-11, -8, 11, 6)           # narthex walls (the facade is z 6 .. 8)
TR, TR_R = (56, 2), 8.5              # red tower axis, stem radius
TB, TB_R = (-50, 2), 8.0             # brown tower axis, stem radius
LIB, LIB_R, LIB_Y = (-46, -38), 14.5, 25   # puffball library centre, radius, centre height
HEART_R = 14.0                       # root heart chamber radius (under the temple)
CAT_F = 3                            # catacomb feet (floor 2)
OSS = (-40, -30, -22, -17)           # ossuary walls
CRYPT = (-26, -14, -18, -6)          # monks' crypt walls
GROTTO = (-25, -50, 12.0, 8.5, 9)    # glowing grotto (cx, cz, rx, rz, height)


# ------------------------------------------------------------------ small helpers
def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def polar(r, a, c=(MX, MZ)):
    return c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))


def dm(x, z):
    """Horizontal distance to the temple's axis."""
    return math.hypot(x - MX, z - MZ)


def am(x, z):
    return ang(x - MX, z - MZ)


def rp(r, a, c=(MX, MZ)):
    x, z = polar(r, a, c)
    return round(x), round(z)


def lichen(face):
    """Glow lichen on one face (the face it hangs on: down = floor, up = ceiling, north.. = that wall)."""
    f = {k: "false" for k in ("down", "up", "north", "south", "east", "west")}
    f[face] = "true"
    return "glow_lichen[" + ",".join(f"{k}={v}" for k, v in f.items()) + ",waterlogged=false]"


NO_LAMP = ("chest", "barrel", "spawner", "door", "lamp", "bulb", "glass", "waystone", "seal", "bars", "sign", "bed",
           "water", "ladder", "stairs", "slab", "lantern", "gold", "rod", "vault", "table", "shelf", "lectern", "gauge",
           "valve", "cog", "gear", "pipe", "furnace", "anvil", "redstone", "bone", "grass", "dirt", "sand", "gravel",
           "shroomlight", "trapdoor", "fence", "wall", "mycelium", "moss", "leaves", "air")


def wall_lamp(C, x, y, z, lamp=EDISON):
    """A lamp set flush in a wall block (only into plain solid masonry, never into furniture or fittings)."""
    b = C.get(x, y, z) or ""
    if C.solid(x, y, z) and (x, y, z) not in C.keep and not any(k in b for k in NO_LAMP):
        C.set(x, y, z, lamp)
        return True
    return False


def post_lamp(C, x, y, z, post=SPR_FENCE, lamp=LANT, h=1):
    if floor_ok(C, x, y, z):
        for k in range(h):
            C.set(x, y + k, z, post)
        C.set(x, y + h, z, lamp)
        return True
    return False


def tuff_wall(x, y, z):
    """Monastery masonry: tuff bricks, darker and mossier at the base, a few chiselled and polished blocks."""
    h = hash3(x, y, z, 31)
    if y <= G + 2:
        return MSB if h < 0.25 else (TUFB if h < 0.85 else "cracked_stone_bricks")
    return TUFB if h < 0.82 else (PTUF if h < 0.93 else CTUFB)


def mud_wall(x, y, z):
    h = hash3(x, y, z, 32)
    return MUD if h < 0.85 else (PMUD if h < 0.95 else TUFB)


# ------------------------------------------------------------------ terrain: the plateau, the terrace, the ridge
def gorge_feet(z):
    """Feet height of the gorge path at z (rising north from the flats onto the gate terrace)."""
    if z >= 97:
        return 1.0
    if z <= 76:
        return 7.0
    return 1.0 + (97 - z) * 6.0 / 21.0


def gorge_x(z):
    return GORGE_X + 1.3 * math.sin(z * 0.21)


def natural(x, z):
    """(top block y, kind) of a massif column, or (None, None)."""
    n1 = fbm(x, z, 12.0, 501) - 0.5
    e = se(x, z, PLAT_C, PLAT_R, 2.8) * (1 + 0.06 * n1)
    if e <= 1.0:
        best, kind = float(G), "plat"
    else:
        best, kind = G - (e - 1.0) * 66.0 * 1.7 - 2.0 * (vnoise(x, z, 4.0, 502) - 0.5), "slope"
    e = se(x, z, GATE_C, GATE_R, 4.0) * (1 + 0.04 * n1)
    t = float(GT) if e <= 1.0 else GT - (e - 1.0) * GATE_R[1] * 1.7
    if t > best:
        best, kind = t, ("gate" if e <= 1.0 else "slope")
    if z > 56:
        d = abs(math.hypot(x - RIDGE_C[0], z - RIDGE_C[1]) - RIDGE_RAD)
        w = RIDGE_W + 2.0 * (fbm(x, z, 9.0, 511) - 0.5)
        crest = 12.0 + 6.0 * fbm(x, z, 8.0, 512)
        t = crest - 0.1 * d * d if d <= w else crest - 0.1 * w * w - (d - w) * 1.8
        if t > best:
            best, kind = t, "ridge"
    if se(x, z, FLAT_C, FLAT_R, 2.4) <= 1.0 + 0.08 * n1 and best < 0:
        best, kind = 0.0, "flat"
    if 74 <= z <= 101:
        w = 2.6 + 0.8 * (vnoise(x, z, 5.0, 521) - 0.5) + (1.4 if z > 94 else 0.0)
        if abs(x - gorge_x(z)) <= w:
            f = math.floor(gorge_feet(z)) - 1
            if best > f:
                best, kind = float(f), "gorge"
    if best < -12:
        return None, None
    return int(math.floor(best)), kind


def rock(x, y, z):
    """Plateau rock: jittered strata of stone, tuff and andesite, deepslate low down, mossy at the foot."""
    j = int((hash01(x // 5, z // 5, 541) - 0.5) * 4)
    band = (y + j) % 10
    h = hash3(x, y, z, 542)
    if y <= 1 and h < 0.35:
        return "mossy_cobblestone" if h < 0.15 else "cobblestone"
    if y < -4:
        return "deepslate" if h < 0.6 else "tuff"
    if band in (0, 1):
        return "tuff" if h < 0.8 else "stone"
    if band == 5:
        return "andesite" if h < 0.75 else "stone"
    if band == 8 and y > 6:
        return "dripstone_block" if h < 0.5 else "stone"
    return "stone" if h < 0.88 else ("cobblestone" if h < 0.95 else "andesite")


def ground_top(x, z, t, steep, kind):
    h = hash01(x, z, 551)
    v = vnoise(x, z, 7.0, 552)
    if kind in ("plat", "gate"):
        if v > 0.68:
            return PODZOL if h < 0.7 else "coarse_dirt"
        return MYC if h < 0.9 else ROOTED
    if kind == "gorge":
        return "gravel" if h < 0.4 else (PODZOL if h < 0.7 else "coarse_dirt")
    if kind == "flat":
        if v > 0.62:
            return MYC if h < 0.75 else PODZOL
        return GRASS if h < 0.6 else (PODZOL if h < 0.8 else ("coarse_dirt" if h < 0.92 else MYC))
    if steep >= 3:
        return rock(x, t, z)
    if kind == "ridge":
        return MOSS if v > 0.6 and h < 0.6 else (MYC if h < 0.7 else rock(x, t, z))
    return MYC if h < 0.55 else (ROOTED if h < 0.7 else rock(x, t, z))


def heightfield(C):
    for x in range(-112, 113):
        for z in range(-96, 124):
            t, k = natural(x, z)
            if t is None:
                continue
            C.top[(x, z)] = t
            C.kind[(x, z)] = k


def write_terrain(C):
    """A shell: the crust 4 deep and every cell exposed within two columns, down to 12 below the ground layer at
    the rim; the flats are a thin disc. Two layers of explicit air over the plateau and the terrace."""
    def nb_low(x, z):
        m = 99
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) + abs(dz) > 2 or (dx == 0 and dz == 0):
                    continue
                t = C.top.get((x + dx, z + dz))
                m = min(m, -13 if t is None else t)
        return m
    for (x, z), t in C.top.items():
        k = C.kind[(x, z)]
        m = nb_low(x, z)
        lo = max(-12, min(m + 1, t - 3) - 1)
        if k == "flat":
            lo = -2 if m >= -1 else max(-8, m)
        steep = t - m
        for y in range(lo, t):
            if k in ("plat", "gate", "flat") and y >= t - 2:
                C.set(x, y, z, "dirt" if hash3(x, y, z, 561) < 0.7 else ROOTED)
            else:
                C.set(x, y, z, rock(x, y, z))
        C.set(x, t, z, ground_top(x, z, t, steep, k))
        if k in ("plat", "gate", "gorge", "flat"):
            for y in range(t + 1, t + 3):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)


def seal_caves(C):
    """Wherever a built space (air, water, a partial block) touches the hollow inside of the massif's shell, the
    touching hollow cell becomes rock, so no room or stair leaks into the world under the plateau."""
    full = ("stone", "brick", "andesite", "tuff", "plating", "dirt", "gravel", "cobble", "calcite", "diorite",
            "planks", "grass_block", "deepslate", "_block", "copper", "glass", "log", "terracotta", "granite", "clay",
            "parquet", "plate", "concrete", "wool", "sand", "bone", "mycelium", "podzol", "stem", "moss_block", "mud")
    part = ("slab", "stair", "wall", "fence", "pane", "bars", "chain", "door", "rail", "rod", "lantern", "lamp",
            "carpet", "button", "lever", "sign", "ladder", "torch", "candle", "water", "air", "bed", "head", "plant",
            "grass[", "trapdoor", "roots", "lichen", "vine", "skull", "bubble", "mist")
    for (x, y, z) in list(C.bp.blocks):
        b = C.get(x, y, z)
        if any(k in b for k in full) and not any(k in b for k in part):
            continue
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0)):
            n = (x + dx, y + dy, z + dz)
            if n in C.bp.blocks:
                continue
            t = C.top.get((n[0], n[2]))
            if t is None or n[1] > t or n[1] < -12:
                continue
            C.bp.set(*n, rock(*n))


# ------------------------------------------------------------------ small mushrooms (scenery)
SCENERY = set()                      # columns under the open-air giant mushrooms (not rooms: no light check)


def mushroom(C, x, z, h, red=True, base=None, seed=0):
    """A giant mushroom h high on the ground at (x, z): a white stem (2 x 2 above 7), a red dome cap or a flat brown
    cap, shroomlight under the cap of the tall ones."""
    t = C.top.get((x, z), 0) if base is None else base
    y0 = t + 1
    if base is None:
        rr = int(max(2.5, h * 0.55)) + 2
        SCENERY.update((x + i, z + j) for i in range(-rr, rr + 2) for j in range(-rr, rr + 2))
    fat = h >= 8
    stem = [(x, z)] + ([(x + 1, z), (x, z + 1), (x + 1, z + 1)] if fat else [])
    for (sx, sz) in stem:
        fill_down(C, sx, y0 - 1, sz, lambda a, b, c: rock(a, b, c), ymin=y0 - 6)
        for y in range(y0, y0 + h):
            C.put(sx, y, sz, STEM)
    cx, cz = (x + 0.5, z + 0.5) if fat else (x, z)
    if red:
        r = max(2.0, h * 0.42)
        for (px, pz) in disk_pts(cx, cz, r + 0.5):
            d = math.hypot(px - cx, pz - cz)
            top = y0 + h + int(round(r * 0.55 * math.sqrt(max(0.0, 1 - (d / (r + 0.6)) ** 2))))
            lo = y0 + h - (1 if d > r - 0.8 else 0)
            for y in range(lo, top + 1):
                if y == top or d > r - 1.2 or y == lo:
                    spot = hash3(px, y, pz, 571 + seed) < 0.12 and y == top
                    C.put(px, y, pz, STEM if spot else RED)
        if fat:
            C.put(x, y0 + h - 1, z, SHROOM)
    else:
        r = max(2.5, h * 0.55)
        for (px, pz) in disk_pts(cx, cz, r + 0.5):
            d = math.hypot(px - cx, pz - cz)
            y = y0 + h - (1 if d > r - 0.7 else 0)
            C.put(px, y, pz, BROWN)
        if fat:
            C.put(x, y0 + h - 1, z, SHROOM)


# ------------------------------------------------------------------ the camp and the approach
def camp(C):
    """The pilgrims' camp on the flats: tents round a fire, the waystone, a hand cart of spore sacks, a shrine of
    small mushrooms under a brass lamp, a signpost toward the gorge."""
    cx, cz = CAMP
    for (x, z) in disk_pts(cx, cz, 6.4):
        if C.kind.get((x, z)) == "flat":
            C.set(x, 0, z, "coarse_dirt" if hash01(x, z, 581) < 0.5 else "packed_mud")
    C.set(cx, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz, f) in ((2, 0, "west"), (-2, 0, "east"), (0, 2, "north")):
        C.set(cx + dx, 1, cz + dz, stair(SPR_ST, f))
    waystone(C, cx - 6, 1, cz - 6)
    C.set(cx - 6, 0, cz - 6, PTUF)
    for (dx, dz) in N4:
        C.set(cx - 6 + dx, 0, cz - 6 + dz, TUFB)
    tent(C, cx - 9, cz + 2, 5, "brown_wool")
    tent(C, cx + 9, cz + 1, 5, "red_wool")
    tent(C, cx + 1, cz + 9, 5, "white_wool", axis="x")
    chest(C, cx - 4, 1, cz - 3, "east", "myc_camp")
    barrel(C, cx + 5, 1, cz - 4)
    barrel(C, cx + 5, 2, cz - 4)
    barrel(C, cx + 6, 1, cz - 4, "north")
    C.set(cx + 6, 1, cz - 5, "crafting_table")
    C.set(cx - 4, 1, cz - 2, "lectern[facing=east,has_book=false,powered=false]")
    # a hand cart of spore sacks
    for (dx, dz) in ((-12, -1), (-12, 0), (-11, -1), (-11, 0)):
        C.set(cx + dx, 1, cz + dz, SPR)
    C.set(cx - 12, 2, cz - 1, "brown_wool")
    C.set(cx - 11, 2, cz, "brown_wool")
    C.set(cx - 12, 2, cz, "white_wool")
    C.set(cx - 13, 1, cz - 1, SPR_FENCE)
    C.set(cx - 13, 1, cz, SPR_FENCE)
    # the shrine: small mushrooms round a brass lamp on a tuff plinth
    sx, sz = cx + 4, cz - 9
    C.set(sx, 1, sz, CTUFB)
    C.set(sx, 2, sz, IRON_WALL)
    C.set(sx, 3, sz, EDISON)
    for (dx, dz, m) in ((1, 0, "red_mushroom"), (-1, 0, "brown_mushroom"), (0, 1, "red_mushroom")):
        C.set(sx + dx, 0, sz + dz, MYC)
        C.set(sx + dx, 1, sz + dz, m)
    candle(C, sx, 1, sz - 1, 3, "red")
    C.set(sx, 0, sz - 1, PTUF)
    # signpost toward the gorge
    C.set(cx - 16, 1, cz - 4, SPR_FENCE)
    C.set(cx - 16, 2, cz - 4, SPR_FENCE)
    C.set(cx - 16, 3, cz - 4, LANT)
    for (x, z) in ((cx - 3, cz - 8), (cx + 9, cz - 6), (cx - 13, cz + 6)):
        lamp_post(C, x, 1, z, 2, LANT)


def approach(C):
    """The path from the camp along the mushroom wood, the gorge through the ridge, the natural arch at its head,
    the terrace road to the gatehouse."""
    def path_full(x, z):
        h = hash01(x, z, 591)
        return "gravel" if h < 0.35 else ("coarse_dirt" if h < 0.6 else ("cobblestone" if h < 0.85 else PODZOL))

    def path_half(x, z):
        return "cobblestone_slab"
    walkway(C, [(40.0, 1.0, 100.0), (30.0, 1.0, 103.0), (18.0, 1.0, 101.0), (10.0, 1.0, 98.0),
                (gorge_x(97) + 0.0, 1.0, 97.0)], width=3, full=path_full, half=path_half, rails=False)
    pts = []
    for z in range(97, 74, -3):
        pts.append((gorge_x(z), gorge_feet(z), float(z)))
    pts.append((gorge_x(75), 7.0, 75.0))
    walkway(C, pts, width=3, full=path_full, half=path_half, rails=False, head=5)
    walkway(C, [(gorge_x(75), 7.0, 75.0), (4.0, 7.0, 69.0), (0.0, 7.0, 64.0)], width=3,
            full=lambda x, z: TUFB if hash01(x, z, 592) < 0.7 else "cobblestone", half=lambda x, z: TUFB_SL,
            rails=False)
    # lanterns on roots along the gorge walls
    for z in range(95, 76, -5):
        x = round(gorge_x(z)) + (3 if z % 2 else -3)
        t = C.top.get((x, z))
        if t is not None and C.solid(x, t, z) and C.free(x, t + 1, z):
            C.set(x, t + 1, z, ROOTS)
            C.set(x, t + 2, z, LANT)
    # the natural arch over the gorge's head
    for z in range(77, 81):
        for x in range(round(gorge_x(z)) - 5, round(gorge_x(z)) + 6):
            dx = x - gorge_x(z)
            top = 15 + (1 if abs(dx) < 2 else 0)
            bot = 11 + int(round(0.12 * dx * dx))
            for y in range(bot, top + 1):
                if C.get(x, y, z) is None or not C.solid(x, y, z):
                    C.set(x, y, z, rock(x, y, z) if y < top else (MYC if hash01(x, z, 593) < 0.7 else MOSS))
            if hash01(x, z, 594) < 0.45 and C.free(x, bot - 1, z):
                C.set(x, bot - 1, z, HROOTS)
    # the mushroom wood south of the ridge (scenery, off the path)
    rng = random.Random(595)
    for (x, z, h, red) in ((26, 94, 11, True), (-8, 102, 14, False), (60, 94, 9, True), (-26, 98, 12, True),
                           (70, 110, 13, False), (16, 112, 8, True), (-40, 108, 10, False), (34, 114, 7, True),
                           (-16, 88, 7, True), (78, 98, 10, True)):
        if C.kind.get((x, z)) in ("flat", "slope", "ridge"):
            mushroom(C, x, z, h, red, seed=rng.randint(0, 99))
    for _ in range(70):
        x, z = rng.randint(-60, 90), rng.randint(84, 120)
        t = C.top.get((x, z))
        if t is None or C.kind[(x, z)] not in ("flat",) or (x, z) in WALK:
            continue
        if C.free(x, t + 1, z) and C.solid(x, t, z):
            C.set(x, t + 1, z, "red_mushroom" if rng.random() < 0.5 else "brown_mushroom")


# ------------------------------------------------------------------ the gatehouse
def cap_turret(C, cx, cz, r, y0, y1, cap_r=None, red=True):
    """A round tuff turret from y0 to y1 with arrow loops and a mushroom cap on top (red dome or flat brown); the
    inside is left solid (the caller carves rooms). Returns the cap's top y."""
    for (x, z) in disk_pts(cx, cz, r + 1.0):
        d = math.hypot(x - cx, z - cz)
        for y in range(y0, y1 + 1):
            rr = r + (0.8 if y < y0 + 4 else 0.0)
            if d > rr + 0.01:
                continue
            spec = tuff_wall(x, y, z)
            a = ang(x - cx, z - cz)
            if (y - y0) % 7 == 4 and round(a) % 72 < 8 and d > r - 1.2:
                spec = "iron_bars"
            if y == y1:
                spec = STEM
            C.set(x, y, z, spec)
    cr = cap_r or r + 2.5
    top = y1
    for (x, z) in disk_pts(cx, cz, cr + 0.5):
        d = math.hypot(x - cx, z - cz)
        if red:
            h = int(round(cr * 0.7 * math.sqrt(max(0.0, 1 - (d / (cr + 0.6)) ** 2))))
            lo = y1 + (0 if d > cr - 1.0 else 1)
            for y in range(lo, y1 + 1 + h + 1):
                spot = hash3(x, y, z, 601) < 0.1 and y == y1 + 1 + h
                C.set(x, y, z, STEM if spot else RED)
            top = max(top, y1 + 1 + h)
        else:
            y = y1 + 1 + (0 if d < cr - 1 else -1)
            C.set(x, y, z, BROWN)
            C.set(x, y + 1, z, BROWN) if d < cr - 2 else None
            top = max(top, y + 1)
        if abs(d - (cr - 1.5)) < 0.5 and hash01(x, z, 602) < 0.3:
            C.set(x, y1, z, SHROOM)
    return top


def gatehouse(C):
    """The gatehouse on the terrace under the south cliff: a tuff block with two mushroom-capped turrets, the great
    arch (closed leaves of spruce and iron) with its wicket, the vaulted passage (compression), the stair up inside
    the cliff to the gate hall; guard rooms in the turrets off the passage."""
    x0, x1, z0, z1 = -12, 12, 55, 61
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(GT - 3, 27):
                C.set(x, y, z, tuff_wall(x, y, z) if y != 18 else DIB)
            if x in (x0, x1) or z == z1:
                if (x + z) % 2 == 0:
                    C.set(x, 27, z, TUFB_WALL)
                else:
                    C.set(x, 27, z, AIR)
    for x in range(x0 + 1, x1):
        for z in range(z0, z1):
            C.set(x, 26, z, PTUF)
    # buttresses on the front
    for x in (-5, 5):
        for y in range(GT - 3, 22):
            C.set(x, y, z1 + 1, tuff_wall(x, y, z1 + 1))
        C.set(x, 22, z1 + 1, stair(TUFB_ST, "north"))
    for sx in (-9, 9):
        cap_turret(C, sx, 60, 3.5, GT - 3, 30, cap_r=6.5)
    # the great arch, 7 wide and 12 high, the leaves set back in it, the wicket open
    for x in range(-3, 4):
        top = GT + 12 - (1 if abs(x) == 3 else 0)
        for y in range(GT + 1, top + 1):
            for z in (z1 - 1, z1):
                C.air(x, y, z)
    for x in range(-4, 5):
        C.set(x, GT + 13, z1, ENGR if abs(x) < 4 else DIB)
    C.set(0, GT + 14, z1, GILD)
    for x in range(-3, 4):
        for y in range(GT + 1, GT + 12):
            if abs(x) <= 1 and y <= GT + 4:
                continue
            C.set(x, y, z1 - 1, IRON if (y - GT) % 3 == 0 or abs(x) == 3 else SPR)
    for x in range(-1, 2):
        C.set(x, GT + 5, z1 - 1, BRASS)
    C.set(-4, GT + 8, z1 + 1, LANT)
    C.set(4, GT + 8, z1 + 1, LANT)
    # the passage (x -1..1, feet 7) from the wicket north to the stair foot
    for z in range(z0 - 1, z1 - 1):
        for x in range(-1, 2):
            C.set(x, GT, z, TREAD if x == 0 else PTUF)
            for y in range(GT + 1, GT + 6):
                C.clear(x, y, z)
            reg(x, z, GT + 1)
        for x in (-2, 2):
            for y in range(GT + 1, GT + 6):
                C.set(x, y, z, DIB if y == GT + 1 else tuff_wall(x, y, z))
        for x in range(-2, 3):
            C.set(x, GT + 6, z, TUFB if z % 2 else CTUFB)
    hang(C, 0, GT + 5, 58, LANT_H, reach=3)
    # the stair up to the gate hall, climbing north inside the cliff (treads z 56 .. 47)
    stair_run(C, [(-1, 56), (0, 56), (1, 56)], "north", 10, GT, spec=TUFB_ST, support=TUFB)
    for z in range(46, 58):
        for x in (-2, 2):
            for y in range(GT + 1, G + 6):
                if not C.solid(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, tuff_wall(x, y, z))
        t = GT + max(1, 57 - z)
        for x in range(-1, 2):
            yc = min(t + 5, G + 6)
            if (x, yc, z) not in C.keep and C.get(x, yc, z) in (None, AIR):
                C.set(x, yc, z, TUFB)
        if z % 3 == 0 and z < 55:
            C.set(-2, GT + (57 - z) + 3, z, LANT)
    # guard rooms in the turrets: a corridor from the passage, a round room each
    for sx in (-9, 9):
        for (x, z) in disk_pts(sx, 60, 2.4):
            C.set(x, GT, z, SPR)
            for y in range(GT + 1, GT + 5):
                C.air(x, y, z)
            C.set(x, GT + 5, z, DOAK)
        step = 1 if sx > 0 else -1
        for x in range(2 * step, sx, step):
            for z in range(57, 60):
                C.set(x, GT, z, PTUF)
                for y in range(GT + 1, GT + 4):
                    C.clear(x, y, z)
        hang(C, sx, GT + 4, 60, LANT_H, reach=2)
    C.set(-10, GT + 1, 61, "barrel[facing=up,open=false]")
    C.set(-8, GT + 1, 62, "grindstone[face=floor,facing=north]") if False else None
    chest(C, -10, GT + 1, 59, "east", "myc_gate")
    C.set(-8, GT + 1, 61, stair(SPR_ST, "north"))
    spawner(C, 9, GT + 1, 61, MOB_KNIGHT)
    C.set(10, GT + 1, 59, "smithing_table")
    C.set(11, GT + 1, 60, "barrel[facing=west,open=false]")


# ------------------------------------------------------------------ the south range: gate hall, lodge, infirmary
def south_range(C):
    x0, z0, x1, z1 = SRANGE
    yw = G + 7
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, G, z, (PTUF if (x + z) % 2 else TUFB) if not edge else TUFB)
            for y in range(G + 1, yw + 1):
                if edge:
                    spec = tuff_wall(x, y, z)
                    if y == G + 6:
                        spec = PTUF
                    win = z in (z0, z1) and G + 2 <= y <= G + 4 and abs(x) > 8 and (x % 4 == 2)
                    if win and z == z1:
                        spec = AMBER
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            C.set(x, yw + 1, z, SPR if not edge else TUFB)
    gable(C, x0, z0, x1, z1, yw + 2, "x", CUT_OX_ST, CUT_OX, over=1, gable_wall=tuff_wall)
    for x in range(x0 + 1, x1):
        if x % 5 == 0:
            for z in range(z0 + 1, z1):
                C.set(x, yw, z, stair(DOAK_ST, "south" if z < (z0 + z1) / 2 else "north", "top") if False else DOAK)
    # partitions: x -7 and x 7, doors 1 x 2 (wooden) near the north wall
    for px in (-7, 7):
        for z in range(z0 + 1, z1):
            for y in range(G + 1, yw + 1):
                C.set(px, y, z, tuff_wall(px, y, z))
        wood_door(C, px, G + 1, z0 + 2, "east" if px > 0 else "west", "dark_oak")
    # the gate hall's door to the south walk (3 wide, 4 high) and the stairwell rails
    for x in range(-1, 2):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z0)
        C.set(x, G, z0, PTUF)
    C.set(0, G + 5, z0, ENGR)
    for z in range(z0 + 2, z1):
        for x in (-2, 2):
            if C.solid(x, G, z) and C.free(x, G + 1, z):
                C.set(x, G + 1, z, TUFB_WALL)
    # gate hall: banners of the order, monk statues, benches, the porter's bell
    for (x, f) in ((-5, "east"), (5, "west")):
        for z in (47, 51):
            C.set(x, G + 1, z, CTUFB)
            C.set(x, G + 2, z, PTUF)
            C.set(x, G + 3, z, "carved_pumpkin[facing=%s]" % f if False else CALC)
            C.set(x, G + 4, z, "brown_mushroom_block")
        C.set(x, G + 1, 49, stair(SPR_ST, f))
    hang(C, 0, G + 5, 50, CHANDELIER, reach=3)
    hang(C, -4, G + 5, 45, LANT_H, reach=3)
    hang(C, 4, G + 5, 45, LANT_H, reach=3)
    C.set(-6, G + 1, 53, "bell[attachment=floor,facing=east,powered=false]")
    # porter's lodge (west): bed, desk, key board, the visitors' ledger
    C.set(-18, G + 1, 51, "red_bed[facing=north,part=head,occupied=false]")
    C.set(-18, G + 1, 52, "red_bed[facing=north,part=foot,occupied=false]")
    C.set(-15, G + 1, 53, TABLE)
    C.set(-14, G + 1, 53, "lectern[facing=north,has_book=false,powered=false]")
    C.set(-16, G + 1, 53, CHAIR + "[facing=east]" if False else stair(SPR_ST, "east"))
    for x in (-12, -10):
        C.set(x, G + 3, z0 + 1, "tripwire_hook[attached=false,facing=south,powered=false]")
    chest(C, -19, G + 1, 46, "east", "myc_gate")
    C.set(-10, G + 1, 53, "barrel[facing=up,open=false]")
    C.set(-9, G + 1, 53, "flower_pot")
    hang(C, -13, G + 5, 49, LANT_H, reach=3)
    # infirmary (east): cots, the apothecary's bench of brewing stands, a cauldron, shelves of potted fungi
    for z in (46, 49, 52):
        C.set(18, G + 1, z, "white_bed[facing=east,part=head,occupied=false]")
        C.set(17, G + 1, z, "white_bed[facing=east,part=foot,occupied=false]")
    for x in (10, 12):
        C.set(x, G + 1, 53, TABLE)
        C.set(x, G + 2, 53, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    C.set(11, G + 1, 53, "water_cauldron[level=3]")
    for x in (9, 13):
        C.set(x, G + 1, 53, "barrel[facing=up,open=false]")
        C.set(x, G + 2, 53, "potted_red_mushroom" if x == 9 else "potted_brown_mushroom")
    chest(C, 15, G + 1, 53, "north", "myc_cloister")
    hang(C, 13, G + 5, 49, LANT_H, reach=3)
    spawner(C, 12, G + 1, 47, MOB_MONK)


# ------------------------------------------------------------------ the cloister (hub)
def in_garth(x, z):
    return in_rect(x, z, GARTH)


def cloister(C):
    """Four arcaded walks round the garth: tuff piers every four with arches, a lean-to copper roof over a beamed
    ceiling, lanterns down the middle; the garth is the meditation garden (sand garden, moss lawn with azaleas, spore
    beds, the koi pond) round the mycelial font, the hub waystone beside it."""
    x0, z0, x1, z1 = CLO
    gx0, gz0, gx1, gz1 = GARTH
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if in_garth(x, z):
                continue
            # depth into the walk from the garth edge (0 = arcade line)
            dpt = min(abs(x - gx0 + 1) if x < gx0 else 99, abs(x - gx1 - 1) if x > gx1 else 99,
                      abs(z - gz0 + 1) if z < gz0 else 99, abs(z - gz1 - 1) if z > gz1 else 99)
            if dpt == 99:
                dpt = 0
            C.set(x, G, z, PTUF if (x + z) % 2 else TUFB)
            for y in range(G + 1, G + 7):
                C.air(x, y, z)
            C.set(x, G + 7, z, SPR)
            yr = G + 8 + dpt // 2
            for y in range(G + 8, yr):
                C.set(x, y, z, SPR)
            fac = "east" if x > gx1 else ("west" if x < gx0 else ("south" if z > gz1 else "north"))
            if x0 < x < x1 and z0 < z < z1 or True:
                C.set(x, yr, z, stair(CUT_OX_ST, fac))
            reg(x, z, G + 1)
    # the arcade line: piers every four, arches between, a low parapet except at the openings
    line = []
    for z in range(gz0 - 1, gz1 + 2):
        line += [(gx0 - 1, z), (gx1 + 1, z)]
    for x in range(gx0, gx1 + 1):
        line += [(x, gz0 - 1), (x, gz1 + 1)]
    for (x, z) in line:
        along = z if x in (gx0 - 1, gx1 + 1) and gz0 <= z <= gz1 else x
        corner = x in (gx0 - 1, gx1 + 1) and z in (gz0 - 1, gz1 + 1)
        pier = corner or along % 4 == 2
        if pier:
            for y in range(G + 1, G + 6):
                C.set(x, y, z, PTUF if y < G + 5 else CTUFB)
            C.set(x, G + 6, z, TUFB)
        else:
            C.set(x, G + 6, z, TUFB)
            C.set(x, G + 5, z, stair(TUFB_ST, "north" if x in (gx0 - 1, gx1 + 1) and False else "south", "top")
                  if False else TUFB_SL + "[type=top,waterlogged=false]")
            opening = abs(along) <= 1 or abs(along - 26) <= 1
            if not opening:
                C.set(x, G + 1, z, TUFB_WALL)
    # lanterns down the walks, every four
    for x in range(x0 + 2, x1 - 1, 4):
        for z in ((z0 + z0 + 4) // 2 + 0, z1 - 2):
            if not in_garth(x, z):
                hang(C, x, G + 6, z, LANT_H, reach=2)
    for z in range(z0 + 4, z1 - 1, 4):
        for x in (x0 + 2, x1 - 2):
            hang(C, x, G + 6, z, LANT_H, reach=2)
    garth(C)


def garth(C):
    gx0, gz0, gx1, gz1 = GARTH
    cxg, czg = 0, 26
    for x in range(gx0, gx1 + 1):
        for z in range(gz0, gz1 + 1):
            for y in range(G + 1, G + 8):
                if C.get(x, y, z) is None:
                    C.bp.set(x, y, z, AIR)
            path = abs(x - cxg) <= 1 or abs(z - czg) <= 1
            if path:
                C.set(x, G, z, SB if hash01(x, z, 611) < 0.6 else PTUF)
                reg(x, z, G + 1)
            elif x < 0 and z < czg:
                C.set(x, G, z, "sand")                       # sand garden
            elif x > 0 and z < czg:
                C.set(x, G, z, MOSS)                         # moss lawn
            elif x < 0:
                C.set(x, G, z, MYC if (z % 3) else PODZOL)   # spore beds
            else:
                C.set(x, G, z, GRASS)
            C.set(x, G - 1, z, "dirt")
    # the sand garden: raked gravel lines, three standing stones, a stone lantern
    for x in range(gx0 + 1, -2):
        for z in range(gz0 + 1, czg - 2):
            if (z - gz0) % 3 == 0:
                C.set(x, G, z, "gravel")
    for (x, z, h) in ((-11, 17, 2), (-6, 21, 1), (-9, 22, 1)):
        for k in range(h):
            C.set(x, G + 1 + k, z, "mossy_cobblestone" if k == 0 else "andesite")
    C.set(-4, G + 1, 16, TUFB_WALL)
    C.set(-4, G + 2, 16, LANT)
    C.set(-4, G + 3, 16, TUFB_SL + "[type=bottom,waterlogged=false]")
    # the moss lawn: azaleas, small mushrooms, a bench, a small red mushroom
    for (x, z, b) in ((4, 16, "flowering_azalea"), (12, 17, "azalea"), (9, 22, "flowering_azalea"), (13, 23, "azalea")):
        C.set(x, G + 1, z, b)
    for (x, z) in ((6, 19), (11, 20), (5, 23)):
        C.set(x, G + 1, z, "moss_carpet")
    C.set(8, G + 1, 15, stair(SPR_ST, "south"))
    C.set(9, G + 1, 15, stair(SPR_ST, "south"))
    mushroom(C, 11, 16 + 0, 6, True, base=G, seed=3) if False else mushroom(C, 12, 20, 6, True, base=G, seed=3)
    # the spore beds: rows of red and brown mushrooms on mycelium, composters
    for x in range(gx0 + 1, -2):
        for z in range(czg + 2, gz1):
            if z % 3 != 0 and hash01(x, z, 612) < 0.7:
                C.set(x, G + 1, z, "red_mushroom" if (x + z) % 2 else "brown_mushroom")
    for z in (29, 33, 37):
        C.set(-13, G + 1, z, "composter[level=4]")
    mushroom(C, -10, 35, 5, False, base=G, seed=4)
    # the koi pond: two deep, lily pads, a plank bridge
    pond = set()
    for x in range(3, gx1):
        for z in range(czg + 3, gz1):
            if ((x - 8.5) / 5.6) ** 2 + ((z - 33) / 4.6) ** 2 <= 1.0:
                pond.add((x, z))
                C.set(x, G - 2, z, "clay")
                C.water(x, G - 1, z)
                C.water(x, G, z)
                if hash01(x, z, 613) < 0.15:
                    C.set(x, G + 1, z, "lily_pad")
    for x in range(5, 13):
        if (x, 33) in pond:
            C.set(x, G, 33, SPR_SL + "[type=top,waterlogged=true]")
            C.air(x, G + 1, 33)
    # the mycelial font: a basin round a brass still crowned with a shroomlight, chains to four posts
    for x in range(cxg - 3, cxg + 4):
        for z in range(czg - 3, czg + 4):
            edge = abs(x - cxg) == 3 or abs(z - czg) == 3
            if edge:
                C.set(x, G, z, PTUF)
                C.set(x, G + 1, z, PTUF_SL + "[type=bottom,waterlogged=false]")
            else:
                C.set(x, G - 1, z, TUFB)
                C.water(x, G, z)
    for y in range(G + 1, G + 4):
        C.set(cxg, y, czg, BRASS if y < G + 3 else GEAR)
    C.set(cxg, G, czg, ENGR)
    C.set(cxg, G + 4, czg, CU_BLOCK)
    C.set(cxg, G + 5, czg, SHROOM)
    C.set(cxg, G + 6, czg, ROD_U)
    for (dx, dz) in N4:
        C.set(cxg + dx, G + 4, czg + dz, PIPES)
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        lamp_post(C, cxg + dx, G + 1, czg + dz, 2, LANT)
    waystone(C, cxg - 4, G + 1, czg - 2)
    C.set(cxg - 4, G, czg - 2, ENGR)
    chest(C, cxg + 5, G + 1, czg - 2, "west", "myc_cloister")


# ------------------------------------------------------------------ the east range: the spore distillery
def pot_still(C, cx, cz):
    """A pot still: a brick firebox with a lit blast furnace, a copper pot with a brass band, its neck and swan-neck
    lyne arm running east to a worm tub (a copper coil in a spruce tub) against the east wall."""
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            for y in (G + 1, G + 2):
                C.set(x, y, z, "bricks" if (x + y + z) % 5 else "nether_bricks")
    C.set(cx - 3, G + 1, cz, "blast_furnace[facing=west,lit=true]")
    C.set(cx - 2, G + 1, cz, "blast_furnace[facing=west,lit=true]")
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            for dz in range(-3, 4):
                d = math.sqrt(dx * dx + (dy * 1.15) ** 2 + dz * dz)
                if 1.6 < d <= 2.9:
                    y = G + 5 + dy
                    if y <= G + 2:
                        continue
                    C.set(cx + dx, y, cz + dz, BRASS if y == G + 5 else (CU_BLOCK if (dx + dz + y) % 3 else CUT_CU))
    for y in range(G + 7, G + 10):
        C.set(cx, y, cz, CU_BLOCK if y < G + 9 else BRASS)
    C.set(cx, G + 10, cz, GAUGE)
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            for y in range(G + 3, G + 8):
                if math.sqrt(dx * dx + ((y - G - 5) * 1.15) ** 2 + dz * dz) <= 1.6:
                    C.set(cx + dx, y, cz + dz, CU_BLOCK)
    for x in range(cx + 1, 44):
        C.set(x, G + 6, cz, PIPES)
    for y in range(G + 4, G + 6):
        C.set(43, y, cz, PIPES)
    for y in range(G + 7, G + 9):
        C.set(cx + 1, y, cz, PIPES)
    for (dx, dz) in ((0, -1), (0, 1), (1, -1), (1, 1), (1, 0)):
        for y in range(G + 1, G + 4):
            C.set(43 + dx, y, cz + dz, SPR if (dx, dz) != (1, 0) else "water_cauldron[level=3]")
    C.set(44, G + 1, cz, "water_cauldron[level=3]")
    C.set(43, G + 1, cz, COPPER)
    C.set(43, G + 2, cz, COPPER)
    C.set(43, G + 3, cz, VALVE)


def column_still(C, cx, cz, h=12):
    """A 3 x 3 brass column still with sight glasses, gauges, a valve and a dome on top."""
    for y in range(G + 1, G + h):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    C.set(cx, y, cz, COPPER)
                    continue
                spec = BRASS if (y - G) % 4 else ENGR
                if (y - G) % 4 == 2 and (dx == 0 or dz == 0):
                    spec = "orange_stained_glass"
                C.set(cx + dx, y, cz + dz, spec)
    C.set(cx, G + h, cz, CU_BLOCK)
    C.set(cx, G + h + 1, cz, ROD_U)
    C.set(cx - 2, G + 3, cz, GAUGE)
    C.set(cx - 2, G + 2, cz, VALVE)
    C.set(cx + 2, G + 6, cz, GAUGE)


def distillery(C):
    """The spore distillery (east range): a tall tuff hall with buttresses and lancet windows under a copper monitor
    roof; three pot stills down the middle, two column stills by the west wall, spore vats at the north end, the
    apothecaries' benches, a gallery of drying racks along the east wall, the passage to the red tower."""
    x0, z0, x1, z1 = ERANGE
    yw = G + 13
    xm = (x0 + x1) // 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, G, z, (TREAD if abs(x - xm) <= 1 else (PTUF if (x + z) % 3 else TUFB)) if not edge else TUFB)
            for y in range(G + 1, yw + 1):
                if edge:
                    spec = tuff_wall(x, y, z)
                    if y in (G + 7, yw):
                        spec = PTUF
                    lanc = (x in (x0, x1) and (z - z0) % 6 == 3 and G + 3 <= y <= G + 10) or \
                           (z in (z0, z1) and (x - x0) % 6 == 3 and G + 3 <= y <= G + 10)
                    if lanc and y < G + 10:
                        spec = AMBER
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            # the monitor roof: two slopes up to a clerestory, a small gable on top
            dx = abs(x - xm)
            if dx >= 4:
                yr = yw + 1 + (13 - dx) // 2
                fac = "west" if x > xm else "east"
                C.set(x, yr, z, stair(CUT_OX_ST, fac))
                if not edge or True:
                    C.set(x, yr - 1, z, SPR if yr - 1 > yw else C.get(x, yr - 1, z) or SPR)
                for y in range(yw + 1, yr - 1):
                    if C.get(x, y, z) is None:
                        C.air(x, y, z)
            else:
                ytop = yw + 1 + (13 - 4) // 2
                for y in range(yw + 1, ytop + 3):
                    if dx == 3:
                        C.set(x, y, z, AMBER if (y > ytop and z % 3 and z0 < z < z1) else
                              (tuff_wall(x, y, z) if z in (z0, z1) else SPR))
                    elif z in (z0, z1):
                        C.set(x, y, z, tuff_wall(x, y, z))
                    else:
                        C.air(x, y, z)
                C.set(x, ytop + 3 + (3 - dx) // 2, z, stair(CUT_OX_ST, "west" if x > xm else "east") if dx else
                      CUT_OX_SL + "[type=bottom,waterlogged=false]")
                if dx == 0:
                    C.set(x, ytop + 4, z, CUT_OX)
    # buttresses on the east face
    for z in range(z0 + 6, z1, 6):
        for y in range(G - 2, yw - 1):
            C.set(x1 + 1, y, z, tuff_wall(x1 + 1, y, z))
            C.set(x1 + 2, y, z, tuff_wall(x1 + 2, y, z)) if y < yw - 4 else None
        C.set(x1 + 2, yw - 4, z, stair(TUFB_ST, "west"))
        C.set(x1 + 1, yw - 1, z, stair(TUFB_ST, "west"))
    # doors: west to the east walk (3 x 4), east to the red tower
    for z in range(24, 27):
        for y in range(G + 1, G + 5):
            C.clear(x0, y, z)
        C.set(x0, G, z, PTUF)
    C.set(x0, G + 5, 25, ENGR)
    for z in range(1, 4):
        for x in range(x1, x1 + 5):
            C.set(x, G, z, TREAD)
            for y in range(G + 1, G + 5):
                C.clear(x, y, z)
            reg(x, z, G + 1)
        for x in range(x1 + 1, x1 + 5):
            C.set(x, G + 5, z, TUFB)
    for x in range(x1 + 1, x1 + 5):
        for y in range(G + 1, G + 6):
            for z in (0, 4):
                if not C.solid(x, y, z):
                    C.set(x, y, z, tuff_wall(x, y, z))
    # the stills
    for cz in (8, 20, 32):
        pot_still(C, xm, cz)
    column_still(C, 25, 4)
    column_still(C, 25, 38)
    # spore vats at the north end: spruce tubs of mash with brass hoops
    for vx in (31, 38):
        for (x, z) in disk_pts(vx, 1.5, 2.5):
            d = math.hypot(x - vx, z - 1.5)
            for y in range(G + 1, G + 4):
                if d > 1.6:
                    C.set(x, y, z, BRASS if y == G + 2 else SPR)
                else:
                    C.set(x, y, z, BROWN if y < G + 3 else "brown_carpet")
    # apothecaries' benches along the west wall
    for z in list(range(8, 20, 2)) + list(range(30, 37, 2)):
        if floor_ok(C, x0 + 1, G + 1, z):
            C.set(x0 + 1, G + 1, z, TABLE if z % 4 else "barrel[facing=east,open=false]")
            if z % 4:
                C.set(x0 + 1, G + 2, z, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]"
                      if z % 8 == 2 else ("potted_red_mushroom" if z % 8 == 6 else "potted_brown_mushroom"))
    for z in (12, 33):
        C.set(x0 + 1, G + 3, z, SHELF + "[facing=east]") if False else None
    C.set(x0 + 2, G + 1, 14, "cauldron")
    C.set(x0 + 2, G + 1, 35, "composter[level=6]")
    # the gallery of drying racks along the east wall (floor y 23), its stair up from the south
    for z in range(4, z1 - 4):
        for x in range(x1 - 3, x1):
            C.set(x, G + 7, z, SPR if (x + z) % 4 else DOAK)
            reg(x, z, G + 8)
        if C.free(x1 - 4, G + 8, z):
            railing(C, x1 - 4, G + 8, z, "west")
        if z % 3 == 0:
            C.set(x1 - 1, G + 8, z, SPR_FENCE)
            C.set(x1 - 1, G + 9, z, "spruce_trapdoor[facing=west,half=bottom,open=false,powered=false,"
                                     "waterlogged=false]")
        if z % 6 == 1:
            C.set(x1 - 4, G + 6, z, stair(IRON_ST, "west", "top"))
    stair_run(C, [(x1 - 3, z1 - 1), (x1 - 2, z1 - 1), (x1 - 1, z1 - 1)], "north", 7, G, spec=SPR_ST, support=SPR)
    for x in range(x1 - 3, x1):
        C.set(x, G + 7, z1 - 8, SPR)
        C.set(x, G + 7, z1 - 9, SPR)
    # lamps: chandeliers between the stills, Edison lamps in the walls under the gallery
    for cz in (14, 26, 38):
        hang(C, xm, G + 11, cz, CHANDELIER, reach=12)
    for z in range(3, z1, 6):
        wall_lamp(C, x0, G + 4, z)
    for z in range(6, z1 - 3, 5):
        hang(C, x1 - 2, G + 12, z, HANG_LAMP, reach=6)
        hang(C, x1 - 2, G + 6, z, LANT_H, reach=2)
    chest(C, x0 + 1, G + 1, 1, "east", "myc_distillery")
    chest(C, x1 - 1, G + 8, 36, "west", "myc_distillery")
    spawner(C, 39, G + 1, 14, MOB_SPIDER)
    spawner(C, 28, G + 1, 28, MOB_WITCH)


# ------------------------------------------------------------------ mushroom towers
def tower_stem(C, c, r0, r1, y0, y1, red=True):
    """A hollow mushroom stem (2 thick) from y0 to y1 tapering r0 -> r1: white stem with brass bands and amber
    slits, a solid newel round the axis, a plank floor at y0 - 1."""
    cx, cz = c
    for (x, z) in disk_pts(cx, cz, r0 + 1.2):
        d = math.hypot(x - cx, z - cz)
        a = ang(x - cx, z - cz)
        C.set(x, y0 - 1, z, STEM if d > r0 - 2 else (SPR if (x + z) % 2 else DOAK))
        for y in range(y0 - 4, y0 - 1):
            if d <= r0 + (0.8 if y < y0 - 2 else 0.4):
                C.set(x, y, z, STEM if d > r0 - 1.5 else rock(x, y, z))
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            R = r0 + (r1 - r0) * t + (0.9 if y < y0 + 3 else 0.0)
            if d > R + 0.01:
                continue
            if d > R - 2.0:
                spec = STEM if hash3(x, y, z, 621) < 0.9 else CALC
                if (y - y0) % 9 == 6:
                    spec = BRASS if round(a) % 30 > 4 else ENGR
                if (y - y0) % 9 in (2, 3) and round(a) % 60 < 6 and d > R - 1.0:
                    spec = AMBER
                C.set(x, y, z, spec)
            elif d < 1.6:
                C.set(x, y, z, STEM if (y - y0) % 6 else BRASS)
            else:
                C.air(x, y, z)


def tower_door(C, c, a, feet, r0, r1, floor=SPR):
    """A doorway 3 wide and 4 high through a tower's wall at angle a, from radius r0 to r1."""
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    cells = set()
    for x in range(int(c[0] - r1) - 2, int(c[0] + r1) + 3):
        for z in range(int(c[1] - r1) - 2, int(c[1] + r1) + 3):
            t = (x - c[0]) * ux + (z - c[1]) * uz
            p = -(x - c[0]) * uz + (z - c[1]) * ux
            if r0 <= t <= r1 and abs(p) <= 1.5:
                cells.add((x, z))
    for (x, z) in cells:
        C.set(x, feet - 1, z, floor)
        for y in range(feet, feet + 4):
            C.clear(x, y, z)
        reg(x, z, feet)
    return cells


def rope_bridge(C, a, b, s, sag=2.0):
    """A sagging rope bridge from a to b ((x, z)) at feet s: a plank deck on cross beams, spruce rails, mangrove-root
    'rope' posts with lanterns, rope hangers under the deck."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / 4))
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((a[0] + (b[0] - a[0]) * t, s - sag * 4 * t * (1 - t), a[1] + (b[1] - a[1]) * t))
    cells = walkway(C, pts, width=3, full=lambda x, z: SPR if (x + z) % 3 else DOAK,
                    half=lambda x, z: SPR_SL, rails=True, rail_spec=SPR_FENCE, post=(ROOTS, LANT), lamp_every=5,
                    head=4)
    for (x, z), ss in cells.items():
        if (x + z) % 4 == 0:
            y = math.floor(ss) - 2
            if C.free(x, y, z) and (x, y, z) not in C.keep:
                C.set(x, y, z, HROOTS)
    return cells


def red_tower(C):
    """The red tower east of the distillery: a 17-wide stem with a newel stair, the rope bridge to the temple's
    chapter house at feet 36, the bell and drying loft inside its red dome cap."""
    cx, cz = TR
    tower_stem(C, TR, TR_R, 7.5, G + 1, G + 29)
    cap_floor = G + 30                   # y 46 (feet 47)
    # spiral: from the west door (feet 17) to the bridge landing (feet 36, angle 232) and on into the cap room
    # the cap: a red dome, the room inside (r <= 10.5), pore windows, shroomlights in the ceiling
    for (x, z) in disk_pts(cx, cz, 14.6):
        d = math.hypot(x - cx, z - cz)
        yt = cap_floor + 1 + int(round(13 * math.sqrt(max(0.0, 1 - (d / 14.6) ** 2))))
        for y in range(cap_floor, yt + 1):
            room = d <= 10.5 and cap_floor < y <= yt - 3
            if room:
                C.air(x, y, z)
            elif y == cap_floor:
                C.set(x, y, z, (SPR if (x + z) % 2 else DOAK) if d <= 10.5 else STEM)
            elif y >= yt - 1 or d > 10.5:
                spot = y == yt and hash3(x, y, z, 631) < 0.14
                C.set(x, y, z, STEM if spot else RED)
            else:
                C.set(x, y, z, RED if hash3(x, y, z, 632) < 0.9 else SHROOM)
        if d > 13.6:
            C.set(x, cap_floor - 1, z, STEM)
    for k in range(6):
        a = 30 + 60 * k
        if adelta(a, 232) < 25:
            continue
        for rr in range(105, 150, 5):
            x, z = rp(rr / 10.0, a, TR)
            for y in (cap_floor + 3, cap_floor + 4):
                C.set(x, y, z, PANE if rr >= 140 else AIR)
    segs = [(180, 500, 17, 25), (500, 820, 25, 33), (820, 937, 33, 36), (937, 967, 36, 36), (967, 1300, 36, 47)]
    spiral(C, segs, 4.4, 3.0, TREAD, TREAD_SLAB, IRON, cx=cx, cz=cz, rmax=7, rail_rmin=5.4)
    underfill_segs(C, segs, 4.4, 3.0, cx, cz, STEM)
    tower_door(C, TR, 180, G + 1, 5.0, 10.0, TREAD)
    tower_door(C, TR, 232, 36, 5.2, 9.6, SPR)
    rails_round(C, [(x, z) for (x, z) in disk_pts(cx, cz, 6.0) if C.free(x, cap_floor, z)], cap_floor,
                spec=SPR_FENCE, skip=[k for k, ss in WALK.items() if any(abs(v - cap_floor - 1) < 1.6 for v in ss)])
    # the loft: the great bell on a brass beam, drying racks of spore trays, sacks, the chest
    for x in range(cx - 3, cx + 4):
        C.set(x, cap_floor + 8, cz, BRASS)
    C.set(cx, cap_floor + 7, cz, "bell[attachment=ceiling,facing=north,powered=false]")
    for (a, k) in ((20, 0), (80, 1), (140, 2), (260, 3), (320, 4)):
        x, z = rp(9.0, a, TR)
        if floor_ok(C, x, cap_floor + 1, z):
            C.set(x, cap_floor + 1, z, SPR_FENCE)
            C.set(x, cap_floor + 2, z, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,"
                                       "waterlogged=false]")
            x2, z2 = rp(8.0, a + 8, TR)
            if floor_ok(C, x2, cap_floor + 1, z2):
                C.set(x2, cap_floor + 1, z2, "barrel[facing=up,open=false]" if k % 2 else "brown_wool")
    x, z = rp(9.2, 110, TR)
    chest(C, x, cap_floor + 1, z, out_facing(cx - x, cz - z), "myc_tower")
    x, z = rp(8.0, 300, TR)
    spawner(C, x, cap_floor + 1, z, MOB_DRONE)
    for a in (45, 135, 225, 315):
        x, z = rp(7.0, a, TR)
        hang(C, x, cap_floor + 5, z, LANT_H, reach=6)
    # stair lights: lamps in the wall every few blocks of height
    for y in range(G + 2, cap_floor, 3):
        for a in (0 + y * 25, 120 + y * 25, 240 + y * 25):
            for rr in range(60, 80, 4):
                x, z = rp(rr / 10.0, a, TR)
                if wall_lamp(C, x, y, z):
                    break
    # the base: spore sacks and a lectern by the door
    C.set(cx - 5, G + 1, cz + 3, "barrel[facing=up,open=false]") if floor_ok(C, cx - 5, G + 1, cz + 3) else None
    return polar(9.6, 232, TR)


def brown_tower(C):
    """The brown tower west of the cells: a newel stair from the west range to the library bridge (feet 27) and the
    temple bridge (feet 36), the abbot's lodge inside its flat brown cap."""
    cx, cz = TB
    tower_stem(C, TB, TB_R, 7.0, G + 1, G + 23)
    cf = G + 24                           # cap floor y 40 (feet 41)
    for (x, z) in disk_pts(cx, cz, 16.2):
        d = math.hypot(x - cx, z - cz)
        if d <= 12.5:
            C.set(x, cf, z, PARQ if d <= 12 else STEM)
            for y in range(cf + 1, cf + 7):
                C.air(x, y, z)
            C.set(x, cf + 7, z, BROWN if hash3(x, 0, z, 641) < 0.92 else SHROOM)
            C.set(x, cf + 8, z, BROWN)
            if d < 6:
                C.set(x, cf + 9, z, BROWN)
        elif d <= 14.6:
            for y in range(cf, cf + 9):
                C.set(x, y, z, BROWN if y > cf else STEM)
        else:
            for y in range(cf + 2, cf + 7):
                C.set(x, y, z, BROWN)
    for k in range(8):
        a = 22.5 + 45 * k
        if adelta(a, 300) < 30:
            continue
        for rr in range(125, 150, 5):
            x, z = rp(rr / 10.0, a, TB)
            for y in (cf + 2, cf + 3):
                C.set(x, y, z, PANE if rr >= 145 else AIR)
    segs = [(0, 276, 17, 27), (276, 306, 27, 27), (306, 606, 27, 34.5), (606, 679, 34.5, 36), (679, 709, 36, 36),
            (709, 1009, 36, 41)]
    spiral(C, segs, 4.3, 3.0, TREAD, TREAD_SLAB, IRON, cx=cx, cz=cz, rmax=7, rail_rmin=5.3)
    underfill_segs(C, segs, 4.3, 3.0, cx, cz, STEM)
    tower_door(C, TB, 0, G + 1, 5.0, 10.6, TREAD)
    tower_door(C, TB, 276, 27, 5.0, 9.2, SPR)
    tower_door(C, TB, 319, 36, 5.0, 9.2, SPR)
    rails_round(C, [(x, z) for (x, z) in disk_pts(cx, cz, 6.0) if C.free(x, cf, z)], cf, spec=DOAK_FENCE,
                skip=[k for k, ss in WALK.items() if any(abs(v - cf - 1) < 1.6 for v in ss)])
    # the abbot's lodge: bed, desk and lectern, bookshelves, a prie-dieu, wardrobes, the reliquary chest
    x, z = rp(10.0, 160, TB)
    C.set(x, cf + 1, z, "purple_bed[facing=east,part=head,occupied=false]")
    C.set(x - 1, cf + 1, z, "purple_bed[facing=east,part=foot,occupied=false]") if floor_ok(C, x - 1, cf + 1, z) \
        else None
    for a in range(190, 260, 12):
        x, z = rp(11.6, a, TB)
        for y in (cf + 1, cf + 2, cf + 3):
            if floor_ok(C, x, y, z) or (y > cf + 1 and C.free(x, y, z)):
                C.set(x, y, z, "bookshelf")
    x, z = rp(9.0, 90, TB)
    C.set(x, cf + 1, z, TABLE)
    C.set(x, cf + 2, z, "candle[candles=3,lit=true,waterlogged=false]")
    x2, z2 = rp(9.0, 75, TB)
    C.set(x2, cf + 1, z2, "lectern[facing=south,has_book=false,powered=false]")
    x2, z2 = rp(7.8, 90, TB)
    C.set(x2, cf + 1, z2, stair(SPR_ST, out_facing(x - x2, z - z2)))
    for a in (30, 45):
        x, z = rp(11.0, a, TB)
        if floor_ok(C, x, cf + 1, z):
            C.set(x, cf + 1, z, "barrel[facing=up,open=false]")
            C.set(x, cf + 2, z, "barrel[facing=up,open=false]")
    for (x, z) in disk_pts(cx, cz, 9.0):
        d = math.hypot(x - cx, z - cz)
        if 6.5 < d < 8.5 and C.free(x, cf + 1, z) and (x, cf + 1, z) not in C.keep and hash01(x, z, 642) < 0.5:
            C.set(x, cf + 1, z, "purple_carpet")
    x, z = rp(10.2, 120, TB)
    chest(C, x, cf + 1, z, out_facing(cx - x, cz - z), "myc_abbot")
    x, z = rp(8.5, 200, TB)
    spawner(C, x, cf + 1, z, MOB_MONK)
    hang(C, cx + 8, cf + 5, cz, CHANDELIER, reach=3)
    hang(C, cx - 8, cf + 5, cz, LANT_H, reach=3)
    for y in range(G + 2, cf, 3):
        for a in (90 + y * 25, 210 + y * 25, 330 + y * 25):
            for rr in range(60, 80, 4):
                x, z = rp(rr / 10.0, a, TB)
                if wall_lamp(C, x, y, z):
                    break
    return polar(9.2, 276, TB), polar(9.2, 319, TB)


# ------------------------------------------------------------------ the puffball library
def lib_inner(y):
    v = 12.5 ** 2 - (y - LIB_Y) ** 2
    return math.sqrt(v) if v > 0 else 0.0


def library(C):
    """The library inside a giant puffball: a white shell with warts and a brass equator band, portholes; two floors
    of curved shelves round the map of the great mycelium (a fungal globe in a brass meridian), the gallery on its
    ring, the chandelier from the dome, the door toward the cloister and the bridge door to the brown tower."""
    cx, cz = LIB
    for (x, z) in disk_pts(cx, cz, LIB_R + 1.2):
        d2 = math.hypot(x - cx, z - cz)
        for y in range(G - 2, LIB_Y + 16):
            d3 = math.sqrt(d2 * d2 + (y - LIB_Y) ** 2)
            if d3 > LIB_R + 0.01:
                if d3 <= LIB_R + 1.0 and y > G and hash3(x, y, z, 651) < 0.06:
                    C.set(x, y, z, CALC)                       # warts
                continue
            if d3 > LIB_R - 2.0:
                h = hash3(x, y, z, 652)
                spec = "white_concrete" if h < 0.45 else ("white_terracotta" if h < 0.7 else
                                                          (CALC if h < 0.88 else STEM))
                if y in (LIB_Y - 1, LIB_Y):
                    spec = ENGR if round(ang(x - cx, z - cz)) % 20 < 3 else BRASS
                C.set(x, y, z, spec)
            elif y <= G:
                C.set(x, y, z, PARQ if y == G and (x + z) % 5 else (DOAK if y == G else STEM))
            else:
                C.air(x, y, z)
    # the lower half sits in a skirt of white crust down to the ground (no stooping under the bulge)
    for (x, z) in disk_pts(cx, cz, LIB_R):
        d2 = math.hypot(x - cx, z - cz)
        a = ang(x - cx, z - cz)
        for y in range(G + 1, LIB_Y):
            if math.sqrt(d2 * d2 + (y - LIB_Y) ** 2) <= LIB_R + 0.01:
                continue
            if G + 3 <= y <= G + 7 and any(adelta(a, 22.5 + 45 * k) < 9 for k in range(8)):
                continue
            h = hash3(x, y, z, 656)
            C.set(x, y, z, "white_terracotta" if h < 0.5 else (CALC if h < 0.8 else MYC if y == G + 1 else STEM))
    # gallery ring (floor y 26, r 6.5 .. wall)
    gy = G + 10
    for (x, z) in disk_pts(cx, cz, 13.0):
        d2 = math.hypot(x - cx, z - cz)
        if 6.5 <= d2 <= lib_inner(gy + 1) + 0.3:
            C.set(x, gy, z, SPR if (x + z) % 3 else DOAK)
    # portholes: amber glass in the outer layer, air in the inner
    for k in range(8):
        a = 22.5 + 45 * k
        for (y0, y1) in ((G + 4, G + 6), (gy + 3, gy + 5)):
            if adelta(a, 60) < 20 or adelta(a, 96) < 20:
                continue
            for y in range(y0, y1 + 1):
                for rr in range(100, 152, 3):
                    x, z = rp(rr / 10.0, a, LIB)
                    d3 = math.sqrt(math.hypot(x - cx, z - cz) ** 2 + (y - LIB_Y) ** 2)
                    if LIB_R - 0.9 < d3 <= LIB_R + 0.01:
                        C.set(x, y, z, AMBER)
                    elif LIB_R - 2.0 < d3 <= LIB_R - 0.9:
                        C.air(x, y, z)
    # curved shelves: against the shell on both floors (gaps at the doors and windows)
    for (x, z) in disk_pts(cx, cz, 12.6):
        d2 = math.hypot(x - cx, z - cz)
        a = ang(x - cx, z - cz)
        if adelta(a, 60) < 14 or adelta(a, 96) < 12:
            continue
        for y in list(range(G + 1, G + 9)) + list(range(gy + 1, gy + 5)):
            ri = lib_inner(y)
            if ri - 1.3 < d2 <= ri and C.free(x, y, z):
                win = any(adelta(a, 22.5 + 45 * k) < 6 for k in range(8)) and (G + 4 <= y <= G + 6 or
                                                                                 gy + 3 <= y <= gy + 5)
                if not win:
                    C.set(x, y, z, "bookshelf" if hash3(x, y, z, 653) < 0.85 else "chiseled_bookshelf[facing=north,"
                          "slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=true,"
                          "slot_4_occupied=false,slot_5_occupied=true]" if False else "bookshelf")
    # the ground under the shell's overhang is open air, not a room (no light check there)
    SCENERY.update((x, z) for (x, z) in disk_pts(cx, cz, 15.6) if math.hypot(x - cx, z - cz) > 12.3)
    # doors: toward the cloister (angle 60, ground) and the bridge door (angle 96, gallery)
    cells = tower_door(C, LIB, 60, G + 1, 8.6, 15.6, PARQ)
    for (x, z) in cells:
        C.set(x, G + 5, z, STEM) if C.free(x, G + 5, z) and math.hypot(x - cx, z - cz) > 12 else None
    tower_door(C, LIB, 96, gy + 1, 10.0, 15.6, SPR)
    # the spiral to the gallery
    spiral(C, [(100, 400, G + 1, gy + 1)], 8.2, 3.0, SPR, SPR_SL, SPR, cx=cx, cz=cz, rmax=11, rail_rmin=6.5)
    underfill_segs(C, [(100, 400, G + 1, gy + 1)], 8.2, 3.0, cx, cz, SPR)
    rails_round(C, [(x, z) for (x, z) in disk_pts(cx, cz, 6.4)], gy, spec=None)
    # the map of the great mycelium: a fungal globe on a plinth inside a brass meridian ring
    gyc = G + 6
    for (x, z) in disk_pts(cx, cz, 3.6):
        for y in range(G + 1, G + 11):
            dx, dz = x - cx, z - cz
            d = math.sqrt(dx * dx + dz * dz + (y - gyc) ** 2)
            if d <= 2.4:
                C.set(x, y, z, RED if hash3(x, y, z, 654) < 0.4 else (BROWN if hash3(x, y, z, 655) < 0.6 else MYC))
            elif dz == 0 and 3.0 <= math.sqrt(dx * dx + (y - gyc) ** 2) <= 3.6:
                C.set(x, y, z, BRASS)
    for y in (G + 1, G + 2):
        C.set(cx, y, cz, CTUFB)
    # reading tables, lecterns and chairs round the globe
    for a in (45, 135, 225, 315):
        x, z = rp(6.0, a, LIB)
        C.set(x, G + 1, z, TABLE)
        C.set(x, G + 2, z, "candle[candles=2,lit=true,waterlogged=false]")
        x2, z2 = rp(7.2, a, LIB)
        if floor_ok(C, x2, G + 1, z2):
            C.set(x2, G + 1, z2, stair(SPR_ST, out_facing(x - x2, z - z2)))
    for a in (0, 180):
        x, z = rp(5.0, a, LIB)
        C.set(x, G + 1, z, "lectern[facing=%s,has_book=false,powered=false]" % out_facing(x - cx, z - cz))
    # gallery desks
    for a in (150, 210, 270, 330):
        x, z = rp(9.5, a, LIB)
        if floor_ok(C, x, gy + 1, z):
            C.set(x, gy + 1, z, TABLE)
            C.set(x, gy + 2, z, "candle[candles=1,lit=true,waterlogged=false]")
    hang(C, cx, gy + 3, cz, CHANDELIER, reach=12)
    for a in (30, 150, 270):
        x, z = rp(9.0, a, LIB)
        hang(C, x, gy - 2, z, LANT_H, reach=4)
    x, z = rp(9.6, 300, LIB)
    chest(C, x, G + 1, z, out_facing(cx - x, cz - z), "myc_library")
    x, z = rp(10.5, 240, LIB)
    chest(C, x, gy + 1, z, out_facing(cx - x, cz - z), "myc_library")
    x, z = rp(7.5, 200, LIB)
    spawner(C, x, G + 1, z, MOB_INK)
    return polar(15.2, 96, LIB)


# ------------------------------------------------------------------ the west range: stair hall, cells, refectory
def west_range(C):
    """The monks' range (mud brick on a tuff base, copper roof): the undercroft stair hall (the stair down to the
    catacombs, the cellarer's desk, a candle shrine), eight monk cells off a corridor, each furnished its own way, the
    refectory with its long tables, the reader's pulpit and the kitchen hearth."""
    x0, z0, x1, z1 = WRANGE
    yw = G + 7
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, G, z, SPR if not edge else TUFB)
            for y in range(G + 1, yw + 1):
                if edge:
                    spec = tuff_wall(x, y, z) if y <= G + 2 else mud_wall(x, y, z)
                    if y == G + 3:
                        spec = PTUF
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            C.set(x, yw + 1, z, SPR if not edge else MUD)
    gable(C, x0, z0, x1, z1, yw + 2, "z", CUT_OX_ST, CUT_OX, over=1, gable_wall=mud_wall)
    for z in range(z0 + 3, z1, 5):
        for x in range(x0 + 1, x1):
            C.set(x, yw, z, DOAK)
    # partitions
    def wall_line(cells):
        for (x, z) in cells:
            for y in range(G + 1, yw + 1):
                C.set(x, y, z, mud_wall(x, y, z) if y > G + 1 else TUFB)
    wall_line([(x, 13) for x in range(x0 + 1, x1)])
    wall_line([(x, 33) for x in range(x0 + 1, x1)])
    wall_line([(-33, z) for z in range(14, 33)] + [(-27, z) for z in range(14, 33)])
    for k in range(1, 4):
        zp = 13 + 5 * k
        wall_line([(x, zp) for x in range(x0 + 1, -33)] + [(x, zp) for x in range(-26, x1)])
    for zw in (13, 33):
        for x in range(-31, -28):
            for y in range(G + 1, G + 5):
                C.clear(x, y, zw)
        C.set(-30, G + 5, zw, CTUFB)
    # doors: east to the west walk (stair hall, refectory), north to the garden path, west to the brown tower
    for zc in (6, 38):
        for z in range(zc - 1, zc + 2):
            for y in range(G + 1, G + 5):
                C.clear(x1, y, z)
            C.set(x1, G, z, PTUF)
    for x in range(-26, -23):
        for y in range(G + 1, G + 5):
            C.clear(x, y, z0)
        C.set(x, G, z0, PTUF)
    # the undercroft stair: down to the catacombs (feet 3), arriving at z 10
    stair_run(C, [(-31, -4), (-30, -4), (-29, -4)], "south", 14, CAT_F - 1, spec=SB_ST, support=SB)
    hole = [(x, z) for x in range(-31, -28) for z in range(4, 10) if C.free(x, G, z)]
    rails_round(C, hole, G, spec=SPR_FENCE, skip=[(x, 10) for x in range(-31, -28)])
    for z in range(-5, 10):
        for x in (-32, -28):
            top = CAT_F + max(0, z + 4) + 5
            for y in range(CAT_F, min(top, G)):
                if not C.solid(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, SB if hash3(x, y, z, 661) < 0.8 else MSB)
        for x in range(-31, -28):
            yc = CAT_F + max(0, z + 4) + 4
            if yc < G and C.get(x, yc, z) in (None, AIR) and (x, yc, z) not in C.keep:
                C.set(x, yc, z, SB)
    # stair hall furnishing
    C.set(-38, G + 1, 2, TABLE)
    C.set(-37, G + 1, 2, "lectern[facing=south,has_book=false,powered=false]")
    C.set(-38, G + 2, 2, "candle[candles=3,lit=true,waterlogged=false]")
    C.set(-38, G + 1, 3, stair(SPR_ST, "north"))
    for x in range(-24, -21):
        C.set(x, G + 1, 12, "barrel[facing=up,open=false]")
        C.set(x, G + 2, 12, "barrel[facing=up,open=false]") if x != -23 else None
    for z in (8, 10):
        C.set(-39, G + 1, z, CTUFB)
        candle(C, -39, G + 2, z, 4, "white")
    C.set(-39, G + 3, 9, GEAR)
    C.set(-39, G + 4, 9, SHROOM)
    hang(C, -30, G + 5, 2, LANT_H, reach=3)
    hang(C, -25, G + 5, 8, LANT_H, reach=3)
    hang(C, -35, G + 5, 8, LANT_H, reach=3)
    # the corridor: lanterns
    for z in (16, 21, 26, 31):
        hang(C, -30, G + 5, z, LANT_H, reach=3)
    # the cells
    kinds = {("w", 0): "plain", ("e", 0): "chest", ("w", 1): "illuminator", ("e", 1): "plain",
             ("w", 2): "chest", ("e", 2): "garden", ("w", 3): "ransacked", ("e", 3): "penitent"}
    for k in range(4):
        cz0 = 14 + 5 * k
        for side in ("w", "e"):
            if side == "w":
                cx0, cx1, back, door_x, f_in = -39, -34, x0, -33, "west"
            else:
                cx0, cx1, back, door_x, f_in = -26, -21, x1, -27, "east"
            wood_door(C, door_x, G + 1, cz0 + 1, OPP[f_in], "spruce")
            kind = kinds[(side, k)]
            bx = cx0 if side == "w" else cx1
            bx2 = bx + (1 if side == "w" else -1)
            if kind != "ransacked":
                C.set(bx, G + 1, cz0 + 3, f"brown_bed[facing={f_in},part=head,occupied=false]")
                C.set(bx2, G + 1, cz0 + 3, f"brown_bed[facing={f_in},part=foot,occupied=false]")
            C.set(bx, G + 1, cz0, TABLE)
            candle(C, bx, G + 2, cz0, 3, "white")
            C.set(bx2, G + 1, cz0, stair(SPR_ST, f_in))
            C.set(back, G + 3, cz0 + 2, PANE)
            hang(C, (cx0 + cx1) // 2, G + 5, cz0 + 2, LANT_H, reach=3)
            mid = (cx0 + cx1) // 2
            if kind == "chest":
                chest(C, bx, G + 1, cz0 + 1, OPP[f_in], "myc_cells")
                C.set(mid, G + 1, cz0 + 2, "brown_carpet")
            elif kind == "illuminator":
                for z in range(cz0, cz0 + 4):
                    C.set(cx1 if side == "w" else cx0, G + 2, z, "bookshelf") if False else None
                C.set(mid, G + 1, cz0 + 1, "lectern[facing=%s,has_book=false,powered=false]" % f_in)
                C.set(bx, G + 2, cz0 + 1, "bookshelf") if False else C.set(bx, G + 1, cz0 + 1, "bookshelf")
                C.set(bx, G + 2, cz0 + 1, "bookshelf")
            elif kind == "garden":
                for z in range(cz0, cz0 + 2):
                    C.set(mid + 1, G + 1, z, "potted_red_mushroom" if z % 2 else "potted_brown_mushroom")
                C.set(bx, G + 1, cz0 + 1, "barrel[facing=up,open=false]")
                C.set(bx, G + 2, cz0 + 1, "potted_crimson_fungus")
            elif kind == "ransacked":
                C.set(bx, G + 1, cz0 + 3, "cobweb")
                C.set(mid, G + 2 + 1, cz0 + 1, "cobweb")
                C.set(bx2, G + 1, cz0 + 3, SPR_SL + "[type=bottom,waterlogged=false]")
                C.set(mid, G + 1, cz0 + 2, "barrel[facing=north,open=true]")
            elif kind == "penitent":
                C.set(mid, G + 1, cz0 + 1, "red_carpet")
                C.set(mid, G + 1, cz0 + 2, "red_carpet")
                C.set(bx, G + 2, cz0 + 1, "chain[axis=y,waterlogged=false]".replace("chain", "iron_chain"))
            else:
                C.set(mid, G + 1, cz0 + 1, "light_gray_carpet")
                C.set(bx, G + 1, cz0 + 1, "barrel[facing=up,open=false]")
    # the refectory: two long tables with benches, the reader's pulpit, the kitchen at the west end
    for zt in (36, 40):
        for x in range(-33, -22):
            C.set(x, G + 1, zt, TABLE)
            if x % 2:
                C.set(x, G + 2, zt, "candle[candles=1,lit=true,waterlogged=false]" if x % 4 == 1 else "flower_pot")
            C.set(x, G + 1, zt - 1, stair(SPR_ST, "south"))
            C.set(x, G + 1, zt + 1, stair(SPR_ST, "north"))
    for x in range(-23, -20):
        for z in range(42, 44):
            C.set(x, G + 1, z, SPR_SL + "[type=bottom,waterlogged=false]") if (x, z) != (-21, 43) else None
    C.set(-22, G + 1, 43, SPR)
    C.set(-22, G + 2, 43, "lectern[facing=west,has_book=false,powered=false]")
    # kitchen: hearth with a chimney through the roof, smoker, furnace, cauldron, barrels
    C.set(-39, G + 1, 38, "campfire[facing=east,lit=true,signal_fire=false,waterlogged=false]")
    for z in (37, 39):
        for y in range(G + 1, G + 4):
            C.set(-39, y, z, "bricks")
    C.set(-38, G + 3, 38, "brick_slab[type=top,waterlogged=false]")
    for y in range(G + 2, yw + 14):
        if y >= yw + 1:
            for (dx, dz) in N4:
                if (dx, dz) != (1, 0) or y > yw + 1:
                    C.set(-39 + dx, y, 38 + dz, "bricks")
            C.set(-39 + 1, y, 38, "bricks") if y > yw + 1 else None
        C.air(-39, y, 38)
    C.set(-39, G + 1, 41, "smoker[facing=east,lit=true]")
    C.set(-39, G + 1, 42, "furnace[facing=east,lit=true]")
    C.set(-39, G + 1, 35, "water_cauldron[level=3]")
    for (x, z) in ((-38, 43), (-37, 43), (-38, 34)):
        C.set(x, G + 1, z, "barrel[facing=up,open=false]")
    C.set(-36, G + 1, 43, "crafting_table")
    chest(C, -35, G + 1, 43, "north", "myc_cells")
    hang(C, -28, G + 5, 38, CHANDELIER, reach=3)
    hang(C, -36, G + 5, 38, LANT_H, reach=3)
    hang(C, -22, G + 5, 36, LANT_H, reach=3)
    spawner(C, -28, G + 1, 42, MOB_MONK)


# ------------------------------------------------------------------ the west front and the narthex
def facade(C):
    """The west front grafted onto the stem's foot: a stepped gable of tuff with calcite string courses, two capped
    turrets, the colossal portal (an iron screen with an open wicket), the rose window; behind it the narthex (vault,
    mosaic floor, statues of the founders, stoups, censers) whose inner iron door opens only from the nave."""
    for x in range(-19, 20):
        h = 34 if abs(x) >= 12 else 50 - 2 * (abs(x) // 2)
        for z in (6, 7, 8):
            for y in range(G - 2, h + 1):
                spec = tuff_wall(x, y, z)
                if y in (G + 8, G + 17):
                    spec = CALC
                if y == h and abs(x) >= 12 and (x % 2):
                    spec = TUFB_WALL
                C.set(x, y, z, spec)
            if abs(x) >= 12 and (x % 2 == 0):
                C.air(x, h + 1, z) if False else None
        if abs(x) < 12:
            C.set(x, h + 1, 7, stair(TUFB_ST, "east" if x < 0 else "west") if x else CTUFB)
    for sx in (-17, 17):
        cap_turret(C, sx, 7, 2.0, G - 2, 40, cap_r=4.5)
    C.set(0, 52, 7, ROD_U)
    C.set(0, 51, 7, GILD)
    # the colossal portal: 7 wide, 13 high, an iron screen with an open wicket
    for x in range(-3, 4):
        top = G + 13 - (1 if abs(x) == 3 else 0) - (1 if abs(x) >= 2 else 0)
        for y in range(G + 1, top + 1):
            for z in (6, 7, 8):
                C.air(x, y, z)
            if not (abs(x) <= 1 and y <= G + 4):
                C.set(x, y, 7, "iron_bars")
        C.set(x, top + 1, 6, ENGR)
    for x in range(-1, 2):
        C.set(x, G, 6, PTUF)
        C.set(x, G, 7, PTUF)
        C.set(x, G, 8, PTUF)
        C.set(x, G + 5, 7, BRASS)
        for y in range(G + 1, G + 5):
            for z in (6, 7, 8):
                C.clear(x, y, z)
    for (x, z) in ((-4, 9), (4, 9)):
        C.set(x, G + 1, z, CTUFB)
        C.set(x, G + 2, z, LANT)
    # the door through the west wing onto the garden path
    for x in range(-14, -11):
        for y in range(G + 1, G + 5):
            for z in (6, 7, 8):
                C.clear(x, y, z)
            C.set(x, G, 5, PTUF)
        for z in (6, 7, 8):
            C.set(x, G, z, PTUF)
    # the rose window (centre y 30, r 4.5): stained glass in the outer face, air behind
    ry = G + 14
    for x in range(-5, 6):
        for y in range(ry - 5, ry + 6):
            rr = math.hypot(x, y - ry)
            if rr > 4.6:
                continue
            a = math.degrees(math.atan2(y - ry, x)) % 360
            if rr < 1.2:
                spec = "red_stained_glass"
            elif adelta(a, round(a / 45.0) * 45.0) < 6 or 4.0 < rr:
                spec = GILD if rr > 4.0 else BRASS
            elif rr < 2.8:
                spec = "orange_stained_glass"
            else:
                spec = "yellow_stained_glass" if (round(a / 45.0) % 2) else "red_stained_glass"
            C.set(x, y, 6, spec)
            C.air(x, y, 7)
            C.air(x, y, 8)
    # the narthex
    nx0, nz0, nx1, nz1 = NARTHEX
    top = G + 17
    for x in range(nx0, nx1 + 1):
        for z in range(nz0, nz1 + 1):
            edge = x in (nx0, nx1) or z == nz0
            C.set(x, G, z, ("red_glazed_terracotta[facing=north]" if (x + z) % 4 == 0 else
                            ("brown_glazed_terracotta[facing=east]" if (x * z) % 3 == 0 else PTUF)) if not edge
                  else TUFB)
            vault = top + 2 - int(round(4 * (x / 10.0) ** 2))
            for y in range(G + 1, top + 4):
                if edge:
                    C.set(x, y, z, tuff_wall(x, y, z))
                elif y <= vault:
                    C.air(x, y, z)
                else:
                    C.set(x, y, z, TUFB if (z % 4) else CTUFB)
    gable(C, nx0 - 1, nz0, nx1 + 1, 5, top + 4, "z", CUT_OX_ST, CUT_OX, over=1, gable_wall=tuff_wall)
    # columns and the founders' statues
    for x in (-6, 6):
        for z in (-4, 0, 4):
            for y in range(G + 1, top + 1):
                C.set(x, y, z, PTUF if y < top else CTUFB)
    for (x, f) in ((-10, "east"), (10, "west")):
        for z in (-3, 2):
            C.set(x + (1 if x < 0 else -1), G + 1, z, CTUFB)
            C.set(x + (1 if x < 0 else -1), G + 2, z, CALC)
            C.set(x + (1 if x < 0 else -1), G + 3, z, CALC)
            C.set(x + (1 if x < 0 else -1), G + 4, z, STEM)
            C.set(x + (1 if x < 0 else -1), G + 5, z, RED)
    for x in (-3, 3):
        C.set(x, G + 1, -6, "water_cauldron[level=3]")
    for x in (-8, 8):
        for z in (-6, 4):
            C.set(x, G + 1, z, stair(SPR_ST, "south" if z < 0 else "north"))
    for (x, z) in ((-3, -2), (3, -2), (-3, 3), (3, 3), (0, 1)):
        hang(C, x, G + 10, z, LANT_H, reach=12)
    for z in (-5, 0, 4):
        wall_lamp(C, nx0, G + 5, z)
        wall_lamp(C, nx1, G + 5, z)
    # the inner portal: an iron door in a brass frame, the lever on the nave side only
    for x in range(-2, 3):
        for y in range(G + 1, G + 5):
            C.set(x, y, nz0, DIB if abs(x) >= 1 else C.get(x, y, nz0))
    C.set(0, G + 3, nz0, DIB)
    C.set(0, G + 4, nz0, ENGR)
    for z in (nz0 - 1, nz0 + 1):
        C.set(0, G, z, PTUF)
        C.clear(0, G + 1, z)
        C.clear(0, G + 2, z)
    iron_door(C, 0, G + 1, nz0, "south")
    lever(C, 1, G + 2, nz0 - 1, "north")


# ------------------------------------------------------------------ the temple: the agaric's stem
def stem_R(y):
    """Outer radius of the stem at height y: the bulb at the foot, the waist, the flare under the cap."""
    return 15.5 + 8.5 * math.exp(-((y - 17) / 9.0) ** 2) + 4.5 * smooth((y - 64) / 14.0)


LEVEL_WIN = ((G + 4, G + 13), (39, 47), (55, 63), (70, 74))   # lancet spans per storey (y0, y1)
WIN_SKIP = {0: (90,), 1: (151, 27), 2: (), 3: (0, 240, 300, 90)}
STOREY_FLOOR = (G, 35, 51, 67)       # floor block of each storey


def level_at(y):
    """The storey whose air the height y belongs to (None in the floor slabs)."""
    if G < y < 34:
        return 0
    if 35 < y < 50:
        return 1
    if 51 < y < 66:
        return 2
    if 67 < y < L3_CEIL:
        return 3
    return None


def floor_spec(lvl, x, z, d, a):
    if lvl == 0:      # the nave: rings of tuff and calcite, brass spokes
        if d > 6 and adelta(a, round(a / 30.0) * 30.0) * math.pi / 180.0 * d < 0.6:
            return ENGR if d > 19.0 else BTILE
        return (PTUF, CALC, PTUF, TUFB, STEM, CTUFB)[int(d) % 6]
    if lvl == 1:      # the chapter house: parquet with dark rings
        return PARQ if int(d) % 4 else DOAK
    if lvl == 2:      # the sporarium: moss and mycelium beds, tread rings
        if int(d) % 5 == 0:
            return TREAD
        return MOSS if hash01(x, z, 701) < 0.5 else MYC
    return BTILE if (int(d) + int(a / 20)) % 2 else PARQ


def stem_wall(x, y, z, d, R, a):
    lvl = level_at(y)
    if y in (G + 3, 33, 49, 65) and d > R - 1.0:          # brass bands
        return ENGR if round(a) % 24 < 3 else BRASS
    h = hash3(x, y, z, 711)
    if d <= R - 2.0 and lvl is not None:                   # the inner face
        pil = adelta(a, round(a / 30.0) * 30.0) * math.pi / 180.0 * d < 0.7
        if lvl == 0 and pil:
            return PTUF if y < 32 else CTUFB
        if lvl == 1 and y <= 38:
            return MAHOG
        if lvl == 2 and h < 0.05:
            return SHROOM
        if lvl == 3 and pil:
            return BROWN
    if d > R - 1.0:
        return STEM if h < 0.92 else CALC
    return STEM


def temple_stem(C):
    """The stem from the volva to the cap: walls 3 thick, the nave floor, the three storey slabs round the light
    well, the gill gallery's ceiling; lancets of amber glass on every storey."""
    for x in range(MX - 27, MX + 28):
        for z in range(MZ - 27, MZ + 28):
            d = dm(x, z)
            if d > 26.2:
                continue
            a = am(x, z)
            for y in range(G - 3, L3_CEIL + 1):
                R = stem_R(y)
                vol = R
                if y < G + 4:
                    vol = R + max(0.0, 1.8 * (1 - (y - G + 3) / 7.0) + 0.7 * (hash01(x, z, 712) - 0.5))
                if d > vol + 0.01:
                    continue
                if d > R + 0.01:                                  # the volva's ragged cup
                    h = hash3(x, y, z, 713)
                    C.set(x, y, z, STEM if h < 0.6 else (CALC if h < 0.8 else MYC))
                    continue
                if d > R - 3.0:
                    C.set(x, y, z, stem_wall(x, y, z, d, R, a))
                    continue
                if y < G:
                    C.set(x, y, z, STEM)
                elif y == G:
                    C.set(x, y, z, floor_spec(0, x, z, d, a))
                elif y in (34, 50, 66):
                    C.set(x, y, z, AIR) if d <= WELL_R else C.set(x, y, z, STEM)
                elif y in (35, 51, 67):
                    if d <= WELL_R:
                        C.air(x, y, z)
                    else:
                        C.set(x, y, z, floor_spec((0, 1, 2, 3)[(35, 51, 67).index(y) + 1], x, z, d, a))
                elif y == L3_CEIL:
                    C.set(x, y, z, AIR if (x, z) == DROP else STEM)
                else:
                    C.air(x, y, z)
    # lancets
    for lvl, (y0, y1) in enumerate(LEVEL_WIN):
        n = 12 if lvl == 0 else 10
        off = 15.0 if lvl % 2 else 0.0
        for k in range(n):
            wa = off + 360.0 * k / n
            if any(adelta(wa, s) < 22 for s in WIN_SKIP[lvl]):
                continue
            for y in range(y0, y1 + 1):
                R = stem_R(y)
                hw = 1.05 if y < y1 - 1 else (0.6 if y == y1 - 1 else 0.2)
                for rr10 in range(int((R - 3.0) * 10) + 1, int(R * 10) + 1, 3):
                    for da in (-6, -3, 0, 3, 6):
                        x, z = rp(rr10 / 10.0, wa + da * 60.0 / max(8.0, rr10 / 10.0) / 6.0)
                        d = dm(x, z)
                        if not (R - 3.0 < d <= R + 0.01):
                            continue
                        if adelta(am(x, z), wa) * math.pi / 180.0 * d > hw:
                            continue
                        if d > R - 1.0:
                            C.set(x, y, z, AMBER)
                        else:
                            C.air(x, y, z)
            # a brass sill under each lancet, a hood moulding over it
            x, z = rp(stem_R(y0 - 1) - 0.4, wa)
            C.set(x, y0 - 1, z, BRASS)
            x, z = rp(stem_R(y1 + 1) - 0.4, wa)
            C.set(x, y1 + 1, z, ENGR)


def stem_dressing(C):
    """Outside the stem: two copper pipes wound round it from the volva to the ring, bracket fungi, mycelium and
    roots spreading from the volva over the plateau."""
    for y in range(G + 2, 64):
        R = stem_R(y)
        for base in (0, 180):
            a = base + (y - G) * 9.0
            x, z = rp(R + 0.6, a)
            if C.free(x, y, z) and (x, y, z) not in C.keep:
                C.set(x, y, z, PIPES)
    for (a, y, w) in ((200, 41, 4.5), (320, 53, 3.5), (65, 46, 4.0), (130, 59, 3.0)):
        cx, cz = polar(stem_R(y) + 0.3, a)
        for (x, z) in disk_pts(cx, cz, w):
            if dm(x, z) < stem_R(y) - 0.3:
                continue
            if C.free(x, y, z) and (x, y, z) not in C.keep:
                C.set(x, y, z, BROWN)
            if math.hypot(x - cx, z - cz) < w - 1.6 and C.free(x, y + 1, z) and (x, y + 1, z) not in C.keep:
                C.set(x, y + 1, z, BROWN)
    # mycelium mats and roots round the volva
    for (x, z) in disk_pts(MX, MZ, 31.0):
        d = dm(x, z)
        if d < 24.5 or C.kind.get((x, z)) != "plat":
            continue
        if (x, z) in WALK or not C.solid(x, G, z) or not C.free(x, G + 1, z):
            continue
        h = hash01(x, z, 721)
        if h < 0.5 * (31.0 - d) / 6.5:
            C.set(x, G, z, MYC)
            if h < 0.08:
                C.set(x, G + 1, z, ROOTS)
            elif h < 0.14:
                C.set(x, G + 1, z, "red_mushroom" if h < 0.11 else "brown_mushroom")


# ------------------------------------------------------------------ the lift cage and the drop pool
def cage_lift(C):
    """The pool in the nave's light well under the reliquary's drop; round it a brass cage whose iron door opens
    only from inside; in the cage the glass tube of the bubble-column lift up to the gill gallery."""
    tube = {(x, z) for x in range(-1, 2) for z in range(MZ - 1, MZ + 2)}
    strip = {(x, z) for x in range(-1, 2) for z in range(MZ + 2, MZ + 5)}
    for (x, z) in disk_pts(MX, MZ, 5.7):
        d = dm(x, z)
        if (x, z) in tube:
            continue
        if d > WELL_R:
            for y in range(13, G + 1):
                C.set(x, y, z, TUFB if y < G else BTILE)
            continue
        if (x, z) in strip:
            C.set(x, G, z, TREAD)
            for y in range(13, G):
                C.set(x, y, z, TUFB)
            reg(x, z, G + 1)
            continue
        C.set(x, 13, z, "clay")
        for y in range(14, G + 1):
            C.water(x, y, z)
        if hash01(x, z, 731) < 0.12 and (x, z) != DROP:
            C.set(x, G + 1, z, "lily_pad")
    # the cage: a brass ring with bars, posts, a crown of gears
    for (x, z) in disk_pts(MX, MZ, 5.7):
        d = dm(x, z)
        if not (4.55 < d <= 5.7):
            continue
        a = am(x, z)
        post = adelta(a, round(a / 45.0) * 45.0) * math.pi / 180.0 * d < 0.6 or (abs(x) == 1 and z == MZ + 5)
        for y in range(G + 1, G + 5):
            if y == G + 4:
                C.set(x, y, z, BRASS if post else GRILLE)
            else:
                C.set(x, y, z, BRASS if post else "iron_bars")
        if post:
            C.set(x, G + 5, z, GEAR)
    iron_door(C, 0, G + 1, MZ + 5, "south")
    lever(C, 1, G + 2, MZ + 4, "north")
    # the tube: glass round a bubble column on soul sand
    for (x, z) in tube:
        for y in range(14, 71):
            if (x, z) == (MX, MZ):
                C.set(x, y, z, "bubble_column[drag=false]" if y <= 67 else AIR)
            else:
                C.set(x, y, z, GLASS)
        C.set(x, 71, z, GLASS if (x, z) != (MX, MZ) else BRASS)
        C.set(x, 13, z, "soul_sand" if (x, z) == (MX, MZ) else TUFB)
    for y in (34, 35, 50, 51, 66):
        for (x, z) in tube:
            if (x, z) != (MX, MZ):
                C.set(x, y, z, BRASS)
    # the mouth (signs hold the water) and the exit at the gill gallery
    C.set(0, G + 1, MZ + 1, "spruce_sign[rotation=8,waterlogged=false]")
    C.set(0, G + 2, MZ + 1, "spruce_wall_sign[facing=south,waterlogged=false]")
    C.set(0, G + 3, MZ + 1, BRASS)
    reg(0, MZ + 1, G + 1)
    C.clear(0, 68, MZ + 1)
    C.clear(0, 69, MZ + 1)
    C.set(0, 67, MZ + 1, BTILE)
    for x in range(-1, 2):
        for z in range(MZ + 2, MZ + 6):
            C.set(x, 67, z, BTILE if x == 0 else TREAD)
            C.set(x, 66, z, slab(IRON_SLAB, "top"))
            for y in range(68, 72):
                C.clear(x, y, z)
            reg(x, z, 68)
    for z in range(MZ + 2, MZ + 6):
        for x in (-2, 2):
            if dm(x, z) <= WELL_R + 0.3:
                C.set(x, 67, z, slab(IRON_SLAB, "top"))
                railing(C, x, 68, z, "west" if x < 0 else "east")


def underfill_segs(C, segs, rc, w, cx, cz, spec):
    """``underfill`` segment by segment of a spiral (the merged cells of a spiral keep only the last segment's
    height where segments stack)."""
    R = int(rc + w) + 2
    for (a0, a1, s0, s1) in segs:
        cells = {}
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                if abs(math.hypot(x - cx, z - cz) - rc) > w / 2.0:
                    continue
                a = ang(x - cx, z - cz)
                if in_arc(a, a0 % 360.0, a0 % 360.0 + (a1 - a0)):
                    t = ((a - a0) % 360.0) / (a1 - a0)
                    cells[(x, z)] = round((s0 + (s1 - s0) * t) * 2) / 2.0
        underfill(C, cells, spec)


def underfill(C, cells, spec):
    """Under a ramp's low stretch (less than three blocks over the floor beneath) fill solid, so nobody walks
    stooping under it; the high stretches stay open."""
    for (x, z), s in cells.items():
        n = math.floor(s)
        yb = n - 2
        if "slab" in (C.get(x, yb, z) or ""):
            yb -= 1
        while yb > n - 9 and C.free(x, yb, z):
            yb -= 1
        if yb <= n - 9 or not C.solid(x, yb, z) or (n - 1.5) - (yb + 1) >= 3:
            continue
        for y in range(yb + 1, n - 1):
            b = C.get(x, y, z) or ""
            if (x, y, z) in C.keep or not (C.free(x, y, z) or "slab" in b):
                continue
            C.set(x, y, z, spec)


# ------------------------------------------------------------------ the helix ramps and the stem's doors
HELIX = {}


def helices(C):
    for segs in ([(285, 615, 17, 36)], [(285, 585, 36, 52)], [(255, 555, 52, 68)]):
        HELIX.update(spiral(C, segs, 10.5, 3.0, TREAD, TREAD_SLAB, IRON, cx=MX, cz=MZ, rmax=13, rail_rmin=6.0))
        underfill_segs(C, segs, 10.5, 3.0, MX, MZ, IRON)


def stem_doors(C):
    """The bridge doors of the chapter house (west toward the brown tower, east toward the red tower), the gill
    gallery's three doors onto the ring balcony; the turret's passage."""
    for a in (151, 27):
        tower_door(C, (MX, MZ), a, 36, 10.0, 17.2, PARQ)
    for a in (0, 240, 300):
        tower_door(C, (MX, MZ), a, 68, 12.0, 17.6, BTILE)
    for a in (151, 27):
        x, z = rp(stem_R(40) + 0.2, a)
        C.set(x, 40, z, ENGR)
    # the ring balcony (the agaric's annulus) at feet 68, a white skirt hanging under it
    for (x, z) in disk_pts(MX, MZ, 23.7):
        d = dm(x, z)
        if d < stem_R(70) + 0.2:
            continue
        a = am(x, z)
        if d <= 22.6:
            C.set(x, 67, z, BTILE if int(d) % 3 else TREAD)
            C.set(x, 66, z, STEM)
            for y in range(68, 72):
                if C.free(x, y, z) or (x, y, z) in C.keep:
                    C.air(x, y, z)
            reg(x, z, 68)
            if d > 21.4:
                for y in range(63, 66):
                    if hash3(x, y, z, 741) < 0.85 - 0.25 * (65 - y):
                        C.set(x, y, z, STEM if hash3(x, y, z, 742) < 0.8 else CALC)
        else:
            C.set(x, 67, z, STEM)
            if round(a) % 20 < 3:
                C.set(x, 68, z, SPR_FENCE)
                C.set(x, 69, z, LANT)
            else:
                C.set(x, 68, z, f"{W}brass_railing[facing={out_facing(x - MX, z - MZ)}]")
    # brackets under the balcony
    for k in range(24):
        a = 15 * k
        for rr in (18.5, 19.5, 20.5):
            x, z = rp(rr, a)
            for y in range(int(66 - (rr - 17.5) * 1.5), 66):
                if C.free(x, y, z):
                    C.set(x, y, z, STEM)


# ------------------------------------------------------------------ the cap, the arena and the reliquary
def y_top(r):
    return 80.0 + 32.0 * math.sqrt(max(0.0, 1.0 - (min(r, CAP_R) / CAP_R) ** 2))


def y_under(r):
    return 77.0 if r < 17 else 77.0 - 5.0 * (r - 17.0) / 17.5


def y_ceil(r):
    return AY + 20.0 * math.sqrt(max(0.0, 1.0 - (min(r, 23.5) / 23.5) ** 2))


def wart(x, z):
    """Distance into a white wart of the cap (> 0 inside), on a jittered grid of 7."""
    best = -9.0
    gx, gz = x // 7, z // 7
    for i in (gx - 1, gx, gx + 1):
        for j in (gz - 1, gz, gz + 1):
            if hash01(i, j, 751) > 0.6:
                continue
            px, pz = i * 7 + 7 * hash01(i, j, 752), j * 7 + 7 * hash01(i, j, 753)
            rad = 1.1 + 1.4 * hash01(i, j, 754)
            best = max(best, rad - math.hypot(x - px, z - pz))
    return best


def cap_and_arena(C):
    """The red cap, 69 wide: a skin of red mushroom block with white warts over a hollow; under it the brown gills
    with stem fins and shroomlight rings, a white veil fringe at the rim; inside, the core over the gill gallery,
    the arena under its own dome (gill-ribbed, a glass oculus to the cupola), its wall ring, the floor."""
    for x in range(MX - 36, MX + 37):
        for z in range(MZ - 36, MZ + 37):
            d = dm(x, z)
            if d > CAP_R + 0.3:
                continue
            a = am(x, z)
            yt = int(round(y_top(d)))
            yu = int(round(y_under(d)))
            sl = abs(y_top(d + 0.75) - y_top(max(0.0, d - 0.75))) / 1.5
            lo = max(yu, yt - 3 - int(math.ceil(sl)))
            w = wart(x, z)
            for y in range(lo, yt + 1):
                if d <= 3.2 and y >= 104:
                    continue
                spec = RED
                if w > 0 and y >= yt - 1:
                    spec = STEM
                C.set(x, y, z, spec)
            if w > 0.8 and d < 31:
                C.set(x, yt + 1, z, STEM)
            # the underside: gills
            if d >= 17.0:
                for y in range(yu, min(yu + 3, lo)):
                    if d > stem_R(y):
                        C.set(x, y, z, BROWN)
                if d > stem_R(yu) + 0.5:
                    gill = adelta(a, round(a / 7.5) * 7.5) * math.pi / 180.0 * d < 0.55
                    if gill:
                        for k in range(1, (2 if d > 24 else 1) + 1):
                            C.set(x, yu - k, z, STEM if hash3(x, yu - k, z, 755) < 0.85 else CALC)
                    elif (abs(d - 20.0) < 0.5 or abs(d - 28.0) < 0.5) and hash01(x, z, 756) < 0.55:
                        C.set(x, yu, z, SHROOM)
                if d > 33.4:
                    for k in range(1, 1 + int(4 * hash01(x, z, 757))):
                        C.set(x, yu - k, z, STEM if k < 3 else CALC)
            # the core over the gill gallery
            if d <= 20.0:
                for y in range(max(78, yu), AY):
                    C.set(x, y, z, STEM)
            # the arena floor, its ring wall and its dome
            if d <= AR:
                C.set(x, AY, z, arena_floor(x, z, d, a))
                yc = int(round(y_ceil(d)))
                for y in range(AY + 1, yc):
                    C.air(x, y, z)
                sl2 = abs(y_ceil(d + 0.75) - y_ceil(max(0.0, d - 0.75))) / 1.5
                for y in range(yc, yc + 3 + int(math.ceil(sl2))):
                    if d <= 2.2:
                        continue
                    if d <= 3.2:
                        C.set(x, y, z, BRASS if y == yc else STEM)
                        continue
                    if y == yc:
                        rib = adelta(a, round(a / 15.0) * 15.0) * math.pi / 180.0 * d < 0.6
                        if rib:
                            spec = STEM
                        elif abs(d - 8.0) < 0.5 or abs(d - 16.0) < 0.5:
                            spec = SHROOM if (int(a) // 5) % 2 else BROWN
                        else:
                            spec = BROWN
                    else:
                        spec = STEM
                    C.set(x, y, z, spec)
            elif d <= 24.5:
                for y in range(AY, int(round(y_ceil(d))) + 4):
                    spec = STEM
                    if d <= 23.0 and y in (AY + 1, AY + 5):
                        spec = BRASS
                    C.set(x, y, z, spec)
    # the oculus shaft and its glass, the cupola
    for (x, z) in disk_pts(MX, MZ, 3.3):
        d = dm(x, z)
        if d <= 2.2:
            for y in range(104, 112):
                C.air(x, y, z)
            C.set(x, 112, z, GLASS)
        else:
            for y in range(104, 113):
                C.set(x, y, z, BRASS if y in (104, 112) else STEM)
    for (x, z) in disk_pts(MX, MZ, 3.4):
        d = dm(x, z)
        for y in range(113, 118):
            if d > 2.3:
                a = am(x, z)
                C.set(x, y, z, BRASS if round(a) % 90 < 20 or y == 117 else GLASS)
            elif y == 113:
                C.set(x, y, z, SHROOM if d < 1 else BTILE)
        for (y, r) in ((118, 3.4), (119, 2.4), (120, 1.5)):
            if d <= r:
                C.set(x, y, z, CUT_OX if d > r - 1.0 else CU_OX)
    C.set(MX, 121, MZ, BRASS)
    C.set(MX, 122, MZ, GILD)
    C.set(MX, 123, MZ, ROD_U)
    # two smoking brass chimneys out of the cap (the distillery's flues)
    for a in (200, 335):
        cx, cz = rp(27.5, a)
        base = int(y_top(27.5)) - 4
        for y in range(base, 119):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    edge = abs(dx) + abs(dz) == 2
                    spec = (ENGR if (y % 6 == 0) else BRASS) if edge else (CU_BLOCK if (y % 4) else BRASS)
                    if (dx, dz) == (0, 0):
                        spec = "hay_block[axis=y]" if y == 118 else BRASS
                    C.set(cx + dx, y, cz + dz, spec)
        C.set(cx, 119, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            C.set(cx + dx, 119, cz + dz, "iron_bars")
        for (dx, dz) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            C.set(cx + dx, 119, cz + dz, BRASS)
            C.set(cx + dx, 120, cz + dz, ROD_U)
    # six pore windows: tunnels from the arena through the cap to glazed slots in its flank
    for pa in (0, 50, 130, 180, 230, 310):
        ux, uz = math.cos(math.radians(pa)), math.sin(math.radians(pa))
        cells = {}
        for t10 in range(int(21.5 * 10), int(34.8 * 10), 3):
            t = t10 / 10.0
            for w10 in range(-25, 26, 5):
                wv = w10 / 10.0
                x, z = round(MX + ux * t - uz * wv), round(MZ + uz * t + ux * wv)
                dd = dm(x, z)
                k = 0 if abs(wv) <= 1.2 else 1
                if (x, z) not in cells or cells[(x, z)][0] > k:
                    cells[(x, z)] = (k, dd)
        for (x, z), (k, dd) in cells.items():
            if dd <= AR:
                continue
            ytop = y_top(dd)
            if ytop < AY + 0.5:
                continue
            if k == 0:
                C.set(x, AY, z, BTILE)
                for y in range(AY + 1, AY + 4):
                    if y > ytop:
                        continue
                    C.set(x, y, z, AMBER if dd > 33.0 or ytop - y < 1.5 else AIR)
                if ytop >= AY + 5:
                    C.set(x, AY + 4, z, STEM)
            else:
                for y in range(AY, AY + 5):
                    if y <= ytop + 0.5:
                        C.set(x, y, z, STEM if y < AY + 4 or dd < 33 else RED)
        x, z = rp(26.0, pa)
        hang(C, x, AY + 3, z, LANT_H, reach=2)
    C.bp.boss_seal(MX, AY, MZ, BOSS, 16)


def arena_floor(x, z, d, a):
    if d <= 2.6:
        return GILD if d > 1.4 else GOLD
    if abs(d - 11.0) < 0.5:
        return SHROOM if (int(a) // 6) % 2 else ENGR
    if adelta(a, round(a / 30.0) * 30.0) * math.pi / 180.0 * d < 0.55:
        return ENGR
    if d > 20.5:
        return BRASS
    k = int(d) % 4
    return (BTILE, PARQ, STEM, PARQ)[k] if hash01(x, z, 761) > 0.08 else MYC


def arena_dress(C):
    """The arena's fittings: chandeliers on chains from the dome, braziers of shroomlight round the rim, spore
    censers, banners of the order between the pore windows."""
    for k in range(6):
        a = 30 + 60 * k
        x, z = rp(12.5, a)
        hang(C, x, AY + 9, z, CHANDELIER, reach=14)
    for k in range(12):
        a = 15 + 30 * k
        if adelta(a, 90) < 30:
            continue
        x, z = rp(20.8, a)
        if floor_ok(C, x, AY + 1, z):
            C.set(x, AY + 1, z, IRON)
            C.set(x, AY + 2, z, SHROOM)
            C.set(x, AY + 3, z, ROD_U)
    for (a, r) in ((70, 6.0), (250, 6.0)):
        x, z = rp(r, a)
        hang(C, x, AY + 14, z, HANG_LAMP, reach=10)


def treasury(C):
    """The spore reliquary in the cap's core under the arena: brass-panelled, the reliquary of the first spore on a
    gilded plinth in a glass case, chests, gold; the ladder up to the sealed bars in the arena floor; the drop well's
    trapdoor down the light well into the pool of the lift cage."""
    x0, x1, z0, z1 = -6, 6, MZ - 17, MZ - 3
    F = VAULT_F
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1)
            for y in range(F, AY):
                if edge:
                    C.set(x, y, z, ENGR if y in (F, AY - 1) else (MAHOG if (x + z) % 4 else BRASS))
                else:
                    C.air(x, y, z)
            if not edge:
                C.set(x, F - 1, z, PARQ if (x + z) % 2 else BTILE)
    dx, dz = DROP
    C.set(dx, F - 1, dz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    C.air(dx, F - 2, dz)
    lever(C, dx + 1, F, dz, "east", face="floor")
    # the ladder up to the bars
    lx, lz = 4, MZ - 14
    for y in range(F, AY):
        C.set(lx, y, lz - 1, ENGR)
        C.set(lx, y, lz, "ladder[facing=south,waterlogged=false]")
    C.set(lx, AY, lz, MOD["vault_bars"])
    # the reliquary: a gilded plinth, a glass case round a red mushroom block crowned with a shroomlight
    rx, rz = 0, MZ - 13
    for (ex, ez) in ((rx + i, rz + j) for i in (-1, 0, 1) for j in (-1, 0, 1)):
        C.set(ex, F, ez, GILD if (ex, ez) != (rx, rz) else GOLD)
        if (ex, ez) != (rx, rz):
            C.set(ex, F + 1, ez, "glass_pane")
            C.set(ex, F + 2, ez, "glass_pane")
            C.set(ex, F + 3, ez, BRASS)
    C.set(rx, F + 1, rz, RED)
    C.set(rx, F + 2, rz, SHROOM)
    C.set(rx, F + 3, rz, GILD)
    for (x, z, f) in ((-5, MZ - 15, "east"), (5, MZ - 9, "west"), (-5, MZ - 7, "east")):
        chest(C, x, F, z, f, "myc_vault")
    rng = random.Random(771)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if abs(x) >= 4 and floor_ok(C, x, F, z) and rng.random() < 0.3:
                C.set(x, F, z, rng.choice((GOLD, "raw_gold_block", "honeycomb_block", GOLD, BROWN)))
                if rng.random() < 0.35 and C.free(x, F + 1, z):
                    candle(C, x, F + 1, z, 3, "red")
    for (x, z) in ((-3, MZ - 6), (3, MZ - 6), (-3, MZ - 15), (2, MZ - 16)):
        hang(C, x, AY - 2, z, LANT_H, reach=2)
    for z in (MZ - 13, MZ - 7):
        wall_lamp(C, x0 - 1, F + 2, z, SHROOM)
        wall_lamp(C, x1 + 1, F + 2, z, SHROOM)


def turret(C):
    """The gill turret on the stem's south flank: corbelled out under the ring balcony, it rises through the cap's
    core to the hatch house in the arena; a narrow spiral round a newel (the compression before the arena), the mist
    in the hatch house's door toward the arena's heart."""
    tx, tz = TUR
    for (x, z) in disk_pts(tx, tz, 6.5):
        r = math.hypot(x - tx, z - tz)
        a = ang(x - tx, z - tz)
        for y in range(58, AY + 5):
            if y < 67:
                rr = 6.2 - (66 - y) * 0.75
                if r <= rr and dm(x, z) > stem_R(y) - 0.3:
                    C.set(x, y, z, STEM if (y + int(a / 30)) % 4 else BRASS)
                continue
            if r <= 5.0:
                if y == 67:
                    C.set(x, y, z, DOAK if (x + z) % 2 else SPR)
                elif r < 1.6:
                    C.set(x, y, z, STEM if (y - 67) % 5 else BRASS)
                else:
                    C.air(x, y, z)
            elif r <= 6.25:
                spec = STEM if hash3(x, y, z, 781) < 0.9 else CALC
                if y in (72, 80, AY + 4):
                    spec = BRASS
                if y in (70, 75, 80) and round(a) % 60 < 8 and AY > y and dm(x, z) > 17:
                    spec = AMBER
                C.set(x, y, z, spec)
        # the hatch house's roof: a small red cap under the dome
        for y in range(AY + 5, AY + 10):
            rr = 6.6 - (y - AY - 5) * 1.4
            if r <= rr:
                C.set(x, y, z, RED if r > rr - 1.4 or y == AY + 9 else STEM)
    # the spiral
    tsegs = [(270, 590, 68, 76), (590, 630, 76, 76), (630, 950, 76, AY + 1), (950, 985, AY + 1, AY + 1)]
    spiral(C, tsegs, 3.4, 3.0, SPR, SPR_SL, SPR, cx=tx, cz=tz, rmax=5, rail_rmin=9.0)
    underfill_segs(C, tsegs, 3.4, 3.0, tx, tz, SPR)
    # the passage from the gill gallery
    for z in range(tz - 7, tz - 3):
        for x in range(-1, 2):
            C.set(x, 67, z, DOAK)
            for y in range(68, 72):
                C.clear(x, y, z)
            reg(x, z, 68)
    # the hatch house's door north toward the arena's heart, the mist
    for z in range(tz - 6, tz - 4):
        for x in range(-1, 2):
            C.set(x, AY, z, TREAD)
            for y in range(AY + 1, AY + 4):
                C.clear(x, y, z)
            reg(x, z, AY + 1)
    C.set(0, AY + 4, tz - 6, GILD)
    C.bp.mist(-1, AY + 1, tz - 6, 1, AY + 3, tz - 6)
    for y in range(70, AY, 4):
        for a in (0 + y * 30, 180 + y * 30):
            x, z = rp(5.5, a, TUR)
            wall_lamp(C, x, y, z)
    hang(C, tx, AY + 4, tz + 3, LANT_H, reach=4)


# ------------------------------------------------------------------ the storeys of the stem
def wall_ring(C, y, n, off=0.0, lamp=EDISON, skip=()):
    """Lamps set in the stem's inner face at height y, n round, skipping the angles in ``skip``."""
    R = stem_R(y)
    for k in range(n):
        a = off + 360.0 * k / n
        if any(adelta(a, s) < 12 for s in skip):
            continue
        for rr10 in range(int((R - 3.4) * 10), int(R * 10), 2):
            x, z = rp(rr10 / 10.0, a)
            if dm(x, z) <= R - 3.05:
                continue
            if C.solid(x, y, z):
                wall_lamp(C, x, y, z, lamp)
                break


def spot(C, r, a, y, spec, tries=4):
    """Put ``spec`` on a free floor cell near polar (r, a) round the temple's axis; returns the cell or None."""
    for k in range(tries):
        x, z = rp(r + (0.6 * k if k % 2 else -0.6 * k), a + 4 * k * (1 if k % 2 else -1))
        if floor_ok(C, x, y, z):
            C.set(x, y, z, spec)
            return x, z
    return None


def spot_chest(C, r, a, y, table):
    for k in range(6):
        x, z = rp(r - 0.5 * k, a + 3 * k)
        if floor_ok(C, x, y, z):
            chest(C, x, y, z, out_facing(MX - x, MZ - z), table)
            return x, z
    return None


def spot_spawner(C, r, a, y, mob):
    for k in range(6):
        x, z = rp(r - 0.5 * k, a + 3 * k)
        if floor_ok(C, x, y, z):
            spawner(C, x, y, z, mob)
            return x, z
    return None


def nave(C):
    """The nave in the bulb of the stem: pews facing the altar, the altar under a brass sunburst set in the north
    wall, side altars, the pulpit, stoups by the inner portal, chandeliers under the chapter house's floor; the
    stair up from the root heart; the nave waystone."""
    F = G + 1
    for zr in (MZ + 8, MZ + 11, MZ + 14, MZ + 17):
        for x in range(-19, 20):
            if abs(x) <= 1:
                continue
            d = dm(x, zr)
            if 6.6 <= d <= 19.0:
                fput(C, x, F, zr, stair(SPR_ST, "south"))
    # the altar
    for x in range(-2, 3):
        for z in (MZ - 17, MZ - 16):
            C.set(x, F, z, CTUFB if abs(x) == 2 else (GILD if x == 0 else PTUF))
        C.set(x, F, MZ - 15, slab(PTUF_SL))
    C.set(0, F + 1, MZ - 17, RED)
    C.set(0, F + 2, MZ - 17, SHROOM)
    for x in (-2, 2):
        candle(C, x, F + 1, MZ - 16, 4, "white")
    for x in (-1, 1):
        C.set(x, F + 1, MZ - 17, GOLD)
    # the sunburst in the north wall over the altar
    for y in range(F + 3, F + 16):
        for x in range(-7, 8):
            rr = math.hypot(x, y - (F + 9))
            if rr > 6.5:
                continue
            for z in range(MZ - 10, MZ - 26, -1):
                if dm(x, z) > stem_R(y) - 3.05 and C.solid(x, y, z):
                    aa = math.degrees(math.atan2(y - (F + 9), x)) % 360
                    ray = adelta(aa, round(aa / 22.5) * 22.5) < 6.5
                    if rr < 1.4:
                        C.set(x, y, z, SHROOM)
                    elif rr < 2.6:
                        C.set(x, y, z, GILD)
                    elif ray:
                        C.set(x, y, z, GILD if rr < 4.2 else ENGR)
                    break
    # side altars (west and east) with founders' statues, the pulpit
    for a in (180, 0):
        x, z = rp(18.0, a)
        sx = 1 if a == 180 else -1
        C.set(x, F, z, CTUFB)
        candle(C, x, F + 1, z, 3, "red")
        for dz in (-2, 2):
            C.set(x - sx, F, z + dz, CTUFB)
            C.set(x - sx, F + 1, z + dz, CALC)
            C.set(x - sx, F + 2, z + dz, STEM)
            C.set(x - sx, F + 3, z + dz, RED)
    px, pz = rp(15.0, 215)
    for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        C.set(px + dx, F, pz + dz, SPR)
    C.set(px, F + 1, pz, "lectern[facing=east,has_book=false,powered=false]")
    C.set(px + 1, F + 1, pz + 1, SPR_FENCE)
    C.set(px + 2, F, pz, stair(SPR_ST, "west"))
    # stoups by the inner portal
    for x in (-3, 3):
        C.set(x, F, MZ + 19, "water_cauldron[level=3]")
    # the stair up from the root heart: rails round its well in the floor
    hole = [(x, z) for x in range(15, 18) for z in range(MZ - 8, MZ + 5) if C.free(x, G, z)]
    rails_round(C, hole, G, spec=SPR_FENCE,
                skip=[(x, z) for x in range(14, 19) for z in (MZ - 9, MZ - 10)])
    # lamps: chandeliers under the slab, sconces round the bulb
    for k in range(6):
        x, z = rp(7.5, 30 + 60 * k)
        hang(C, x, F + 12, z, CHANDELIER, reach=8)
    wall_ring(C, F + 3, 20, 9.0, skip=(90,))
    wall_ring(C, F + 10, 12, 0.0)
    waystone(C, -3, F, MZ + 17)
    C.set(-3, G, MZ + 17, ENGR)
    spot_chest(C, 17.0, 260, F, "myc_nave")
    spot_spawner(C, 16.5, 20, F, MOB_MONK)
    spot_spawner(C, 16.5, 160, F, MOB_MONK)


def chapter_house(C):
    """The chapter house (feet 36): the ring of benches round the well, lecterns, the abbot's seat, bookshelves
    along the wall under the helix, a chandelier; the two bridge doors."""
    F = 36
    for k in range(16):
        a = 11.25 + 22.5 * k
        x, z = rp(7.0, a)
        fput(C, x, F, z, stair(SPR_ST, out_facing(x - MX, z - MZ)))
    for a in (45, 135):
        x, z = rp(8.8, a)
        fput(C, x, F, z, "lectern[facing=%s,has_book=false,powered=false]" % out_facing(MX - x, MZ - z))
    x, z = rp(11.0, 90)
    if floor_ok(C, x, F, z):
        C.set(x, F, z, stair(DOAK_ST, "south"))
        for dx in (-1, 1):
            fput(C, x + dx, F, z, DOAK_FENCE)
        C.set(x, F + 1, z + 1, MAHOG) if C.free(x, F + 1, z + 1) else None
    for a in list(range(100, 140, 7)) + list(range(170, 215, 7)):
        x, z = rp(12.1, a)
        for y in (F, F + 1, F + 2):
            if C.free(x, y, z) and (x, y, z) not in C.keep and C.solid(x, y - 1, z):
                C.set(x, y, z, "bookshelf")
    hang(C, MX + 7, F + 9, MZ, CHANDELIER, reach=8)
    hang(C, MX - 7, F + 9, MZ, CHANDELIER, reach=8)
    wall_ring(C, F + 3, 14, 6.0, skip=(151, 27))
    wall_ring(C, F + 9, 10, 18.0)
    spot_chest(C, 11.5, 115, F, "myc_chapter")
    spot_spawner(C, 8.5, 330, F, MOB_MONK)


def sporarium(C):
    """The sporarium (feet 52): racks of potted fungi along the wall, glass terrariums, the spore organ's copper
    pipes, shroomlights in the wall."""
    F = 52
    for a in range(12, 190, 8):
        if adelta(a, 90) < 26:
            continue
        x, z = rp(12.0, a)
        if floor_ok(C, x, F, z):
            C.set(x, F, z, "barrel[facing=up,open=false]")
            pot = ("potted_red_mushroom", "potted_brown_mushroom", "potted_crimson_fungus",
                   "potted_warped_fungus")[(a // 8) % 4]
            C.set(x, F + 1, z, pot) if C.free(x, F + 1, z) else None
    for a in (45, 135, 315):
        cx, cz = rp(7.6, a)
        cells = [(cx + i, cz + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
        if not all(floor_ok(C, x, F, z) and floor_ok(C, x, F + 2, z) for (x, z) in cells):
            continue
        for (x, z) in cells:
            for y in range(F, F + 3):
                if (x, z) == (cx, cz):
                    C.set(x, y, z, MYC if y == F else ("red_mushroom" if (a // 45) % 2 else "brown_mushroom")
                          if y == F + 1 else AIR)
                else:
                    C.set(x, y, z, GLASS if y > F else BRASS)
            C.set(x, F + 3, z, GLASS if (x, z) != (cx, cz) else SHROOM)
    for i, a in enumerate(range(70, 112, 6)):
        x, z = rp(12.1, a)
        if not floor_ok(C, x, F, z):
            continue
        for y in range(F, F + 4 + (i % 3) * 2):
            C.set(x, y, z, PIPES)
        C.set(x, F + 4 + (i % 3) * 2, z, ROD_U)
    x, z = rp(10.0, 90)
    if floor_ok(C, x, F, z):
        C.set(x, F, z, IRON)
        C.set(x, F + 1, z, VALVE)
        fput(C, x, F, z - 1, stair(SPR_ST, "north"))
    hang(C, MX + 7, F + 9, MZ + 2, CHANDELIER, reach=8)
    hang(C, MX - 7, F + 9, MZ - 2, HANG_LAMP, reach=8)
    hang(C, MX, F + 9, MZ - 8, HANG_LAMP, reach=8)
    wall_ring(C, F + 3, 14, 0.0)
    wall_ring(C, F + 9, 10, 18.0)
    spot_chest(C, 11.5, 30, F, "myc_sporarium")
    spot_spawner(C, 8.5, 200, F, MOB_DRONE)


def gill_gallery(C):
    """The gill gallery (feet 68), the site of grace: gill fins hanging from the ceiling, meditation mats and
    candles round the well, the grace waystone, the bridge from the lift's mouth; the doors onto the ring balcony,
    the passage to the turret."""
    F = 68
    for (x, z) in disk_pts(MX, MZ, 13.4):
        d = dm(x, z)
        if d < 5.5 or d > stem_R(76) - 3.0:
            continue
        a = am(x, z)
        if adelta(a, round(a / 15.0) * 15.0) * math.pi / 180.0 * d < 0.55:
            if C.free(x, 76, z):
                C.set(x, 76, z, BROWN)
            if d > 8.5 and C.free(x, 75, z):
                C.set(x, 75, z, BROWN)
    for k in range(12):
        a = 15 + 30 * k
        x, z = rp(7.0, a)
        if fput(C, x, F, z, "red_carpet" if k % 2 else "brown_carpet"):
            if k % 3 == 0:
                x2, z2 = rp(8.0, a)
                if floor_ok(C, x2, F, z2):
                    candle(C, x2, F, z2, 3, "white")
    waystone(C, 5, F, MZ + 9)
    C.set(5, F - 1, MZ + 9, ENGR)
    for k in range(6):
        x, z = rp(8.5, 60 * k)
        hang(C, x, F + 5, z, LANT_H, reach=5)
    wall_ring(C, F + 2, 12, 15.0, skip=(0, 240, 300, 90))
    spot_chest(C, 11.0, 150, F, "myc_grace")


def level_rails(C):
    """Railings round every opening in the storey floors (the light well, the helix's slot), never on a walkway."""
    for yf in (35, 51, 67):
        cells = set()
        for (x, z) in disk_pts(MX, MZ, 13.0):
            if dm(x, z) <= stem_R(yf) - 3.0 and C.free(x, yf, z):
                cells.add((x, z))
        skip = {k for k, ss in WALK.items() if any(abs(s - (yf + 1)) < 1.6 for s in ss)}
        rails_round(C, cells, yf, skip=skip)


# ------------------------------------------------------------------ under the plateau: catacombs, grotto, root heart
def cata_wall(x, y, z):
    h = hash3(x, y, z, 801)
    return SB if h < 0.55 else (MSB if h < 0.75 else (CSB if h < 0.9 else TUFB))


def tunnel(C, pts, w, h, feet, seed, floor=None):
    """A rough rock tunnel along a polyline [(x, z)] at constant feet, w wide and h high."""
    done = set()
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L * 3) + 1
        for i in range(n + 1):
            t = i / n
            px, pz = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for x in range(int(px - w) - 1, int(px + w) + 2):
                for z in range(int(pz - w) - 1, int(pz + w) + 2):
                    if math.hypot(x - px, z - pz) > w / 2.0 + 0.3 * (vnoise(x, z, 3.0, seed) - 0.3):
                        continue
                    if (x, z) in done:
                        continue
                    done.add((x, z))
                    C.set(x, feet - 1, z, floor(x, z) if floor else rock(x, feet - 1, z))
                    for y in range(feet, feet + h):
                        if y < feet + 3:
                            C.clear(x, y, z)
                        else:
                            C.air(x, y, z)
                    reg(x, z, feet)
    return done


def catacombs(C):
    """The root catacombs (feet 3) under the west of the plateau: the burial gallery from the undercroft stair, its
    niches of skulls and candles; the monks' crypt with its sarcophagi; the ossuary of bone pillars and skull walls;
    the tunnel north to the glowing grotto."""
    F = CAT_F
    # the gallery
    for z in range(-16, -4):
        for x in range(-32, -27):
            if x in (-32, -28):
                for y in range(F - 1, F + 5):
                    C.set(x, y, z, cata_wall(x, y, z))
                continue
            C.set(x, F - 1, z, "cobblestone" if hash01(x, z, 802) < 0.3 else SB)
            for y in range(F, F + 4):
                C.clear(x, y, z) if y < F + 3 else C.air(x, y, z)
            C.set(x, F + 4, z, SB if x != -30 else CSB)
            reg(x, z, F)
        if z % 3 == 0:
            for x in (-32, -28):
                h = hash01(x, z, 803)
                C.set(x, F + 1, z, SKULL.format(4 if x < -30 else 12) if h < 0.5 else
                      ("bone_block[axis=z]" if h < 0.7 else "cobweb"))
                C.set(x, F + 2, z, "candle[candles=2,lit=true,waterlogged=false]")
        if z % 3 == 1:
            hang(C, -30, F + 3, z, LANT_H, reach=2)
    # the monks' crypt
    x0, z0, x1, z1 = CRYPT
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, F - 1, z, PTUF if (x + z) % 2 else TUFB)
            for y in range(F, F + 5):
                C.set(x, y, z, cata_wall(x, y, z)) if edge else C.air(x, y, z)
            C.set(x, F + 5, z, TUFB if edge or (z % 2) else CTUFB)
    for x in (-28, -27, -26):
        C.set(x, F - 1, -10, PTUF)
        for y in range(F, F + 3):
            C.clear(x, y, -10)
        reg(x, -10, F)
    for (x, z) in ((-23, -12), (-23, -8), (-20, -12), (-20, -8)):
        C.set(x, F, z, CTUFB)
        C.set(x + 1, F, z, PTUF)
        C.set(x, F + 1, z, slab(PTUF_SL))
        C.set(x + 1, F + 1, z, slab(PTUF_SL))
        candle(C, x, F + 2, z, 1, "white")
    C.set(-19, F, -10, CTUFB)
    C.set(-19, F + 1, -10, SKULL.format(4))
    chest(C, -19, F, -9, "west", "myc_catacombs")
    spawner(C, -21, F, -10, MOB_CRAWLER)
    for (x, z) in ((-22, -10), (-24, -10)):
        hang(C, x, F + 3, z, LANT_H, reach=3)
    hang(C, -20, F + 4, -7, LANT_H, reach=2)
    hang(C, -24, F + 4, -13, LANT_H, reach=2)
    # the ossuary
    x0, z0, x1, z1 = OSS
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            C.set(x, F - 1, z, "gravel" if hash01(x, z, 804) < 0.2 else ("bone_block[axis=y]" if (x * z) % 7 == 0
                                                                          else SB))
            for y in range(F, F + 6):
                if edge:
                    pat = (y + x + z) % 3
                    spec = cata_wall(x, y, z)
                    if F < y < F + 5 and pat == 0:
                        spec = "bone_block[axis=x]" if z in (z0, z1) else "bone_block[axis=z]"
                    C.set(x, y, z, spec)
                else:
                    C.air(x, y, z)
            C.set(x, F + 6, z, "bone_block[axis=x]" if (z - z0) % 4 == 0 and not edge else SB)
    for x in range(-31, -28):
        for z in (z1, z0):
            C.set(x, F - 1, z, SB)
            for y in range(F, F + 3):
                C.clear(x, y, z)
            reg(x, z, F)
    for x in (-36, -25):
        for z in (-26, -21):
            for y in range(F, F + 6):
                C.set(x, y, z, BONE)
            C.set(x, F + 3, z + 1, SKULL.format(0)) if C.free(x, F + 3, z + 1) else None
    for (x, z, f) in ((-39, -24, "east"), (-23, -24, "west")):
        for dz in (-2, 0, 2):
            C.set(x, F + 2, z + dz, SKULL.format(4 if f == "east" else 12))
    for (x, z) in ((-33, -23), (-28, -23), (-30, -27), (-30, -19)):
        hang(C, x, F + 5, z, LANT_H, reach=2)
    hang(C, -36, F + 5, -19, LANT_H, reach=2)
    hang(C, -25, F + 5, -28, LANT_H, reach=2)
    chest(C, -38, F, -28, "east", "myc_catacombs")
    spawner(C, -34, F, -24, MOB_CRAWLER)
    spawner(C, -26, F, -19, MOB_BOGGED)
    # the tunnel north to the grotto
    tunnel(C, [(-30, -30), (-28, -38), (-26, -43)], 3, 4, F, 805)
    for (x, z) in ((-29, -34), (-27, -40)):
        hang(C, x, F + 3, z, LANT_H, reach=3)


def grotto(C):
    """The glowing grotto: a cave of shroomlights and glow lichen, spore blossoms over a still pool with lily pads,
    small giant mushrooms on mycelium; its tunnel east to the root heart."""
    cx, cz, rx, rz, h = GROTTO
    F = CAT_F
    cells = blob_cells(cx, cz, rx, rz, 811)
    tops = {}
    for (x, z, e) in cells:
        top = F + max(3, int(h * math.sqrt(max(0.0, 1.0 - e)) + 2.0 * (fbm(x, z, 4.0, 812) - 0.5))) - 1
        tops[(x, z)] = top
        C.set(x, F - 1, z, MYC if hash01(x, z, 813) < 0.55 else (MOSS if hash01(x, z, 814) < 0.6 else "stone"))
        for y in range(F, top + 1):
            C.air(x, y, z)
        hc = hash01(x, z, 815)
        if hc < 0.1:
            C.set(x, top + 1, z, SHROOM)
        elif hc < 0.4:
            C.set(x, top, z, lichen("up"))
        elif hc < 0.47 and top - F > 4:
            C.set(x, top, z, "spore_blossom")
        reg(x, z, F)
    # the pool
    for (x, z, e) in cells:
        if ((x - cx - 2) / 5.0) ** 2 + ((z - cz - 1) / 3.2) ** 2 <= 1.0:
            C.set(x, F - 2, z, "clay")
            C.water(x, F - 1, z)
            if hash01(x, z, 816) < 0.2:
                C.set(x, F, z, "lily_pad")
    # small giant mushrooms and fungi
    for (x, z, hh, red) in ((cx - 7, cz - 2, 5, True), (cx - 4, cz + 4, 4, False), (cx + 7, cz - 4, 4, True)):
        if (x, z) in tops and tops[(x, z)] - F >= hh + 3:
            mushroom(C, x, z, hh, red, base=F - 1, seed=3)
    rng = random.Random(817)
    for (x, z, e) in cells:
        if floor_ok(C, x, F, z) and (x, F, z) not in C.keep and rng.random() < 0.12:
            C.set(x, F, z, rng.choice(("red_mushroom", "brown_mushroom", "glow_lichen[down=true,up=false,north=false,"
                                       "south=false,east=false,west=false,waterlogged=false]", "moss_carpet")))
    x, z = round(cx + 5), round(cz + 4)
    spawner(C, x, F, z, MOB_WISP)
    chest(C, round(cx - 9), F, round(cz + 2), "east", "myc_grotto")
    tunnel(C, [(-15, -47), (-12, -40), (-11, -34)], 3, 4, F, 818)
    hang(C, -13, F + 3, -42, LANT_H, reach=3)


def root_heart(C):
    """The root heart under the temple: a dome of rooted earth ribbed with the agaric's white roots round the
    central root bundle (veined with shroomlight) that carries the pool above; hanging roots; the stair up into the
    nave."""
    F = CAT_F
    for (x, z) in disk_pts(MX, MZ, HEART_R + 1.4):
        d = dm(x, z)
        a = am(x, z)
        top = F + int(round(8.5 * math.sqrt(max(0.0, 1.0 - (min(d, HEART_R) / HEART_R) ** 2))))
        rib = adelta(a, round(a / 45.0) * 45.0) * math.pi / 180.0 * max(d, 1.0) < 1.0
        if d <= HEART_R:
            C.set(x, F - 1, z, ROOTED if hash01(x, z, 821) < 0.4 else (MYC if hash01(x, z, 822) < 0.6 else "mud"))
            for y in range(F, max(top, F + 3) + 1):
                if d <= 2.6:
                    k = (y * 3 + int(a / 40)) % 9
                    C.set(x, y, z, SHROOM if k == 0 else STEM)
                else:
                    C.air(x, y, z)
            # the shell over the dome
            for y in range(max(top, F + 3) + 1, max(top, F + 3) + 3):
                if d <= 2.6:
                    C.set(x, y, z, STEM)
                else:
                    C.set(x, y, z, STEM if rib else (ROOTED if hash3(x, y, z, 823) < 0.6 else "mud"))
            if d > 2.6 and hash01(x, z, 824) < 0.2:
                C.set(x, max(top, F + 3), z, HROOTS)
            if rib and d > 3.5 and abs(d - 9.0) < 0.6:
                C.set(x, max(top, F + 3) + 1, z, SHROOM)
        else:
            for y in range(F - 1, F + 4):
                C.set(x, y, z, STEM if rib else (ROOTED if hash3(x, y, z, 825) < 0.5 else "mud"))
    # the ribs run down the wall as root buttresses
    for k in range(8):
        a = 45 * k + 22.5
        for rr in (12.6, 13.4):
            x, z = rp(rr, a)
            for y in range(F, F + 3):
                if C.free(x, y, z) and (x, y, z) not in C.keep:
                    C.set(x, y, z, ROOTS)
    # the stair foot corridor and the stair up into the nave
    for x in range(10, 18):
        for z in range(MZ + 5, MZ + 8):
            C.set(x, F - 1, z, ROOTED if hash01(x, z, 826) < 0.5 else "mud")
            for y in range(F, F + 4):
                C.clear(x, y, z) if y < F + 3 else C.air(x, y, z)
            reg(x, z, F)
    stair_run(C, [(15, MZ + 4), (16, MZ + 4), (17, MZ + 4)], "north", 14, F - 1, spec=SB_ST, support=SB)
    for i in range(0, 14, 4):
        x, z = 18, MZ + 4 - i
        wall_lamp(C, x, F + i + 2, z, LANT) if C.solid(x, F + i + 2, z) else None
    for (x, z) in ((-6, MZ - 6), (6, MZ + 6), (-7, MZ + 5), (7, MZ - 6)):
        hang(C, x, F + 5, z, LANT_H, reach=4)
    spawner(C, 8, F, MZ - 4, MOB_CRAWLER)
    spawner(C, -8, F, MZ + 3, MOB_MITE)
    chest(C, -5, F, MZ - 9, "south", "myc_root")


# ------------------------------------------------------------------ the garden path and the plateau's scenery
def mush_lamp(C, x, y, z):
    if not floor_ok(C, x, y, z):
        return False
    for k in range(3):
        C.set(x, y + k, z, STEM)
    C.set(x, y + 3, z, SHROOM)
    for (dx, dz) in N4:
        if C.free(x + dx, y + 3, z + dz) and (x + dx, y + 3, z + dz) not in C.keep:
            C.set(x + dx, y + 3, z + dz, RED)
    C.set(x, y + 4, z, RED) if C.free(x, y + 4, z) else None
    return True


def garden_path(C):
    """The path from the west front's wing door past the west range to the library, lined with mushroom lamps;
    mycelium lawns round it."""
    def gfull(x, z):
        h = hash01(x, z, 831)
        return SB if h < 0.45 else ("mossy_cobblestone" if h < 0.7 else (PTUF if h < 0.9 else MOSS))
    pts = [(-13.0, 17.0, 4.0), (-17.0, 17.0, -2.0), (-25.0, 17.0, -4.5), (-32.0, 17.0, -15.0), (-37.5, 17.0, -23.0)]
    cells = walkway(C, pts, width=3, full=gfull, half=lambda x, z: SB_SL, rails=False)
    cells.update(walkway(C, [(-25.0, 17.0, -1.0), (-25.0, 17.0, -4.0)], width=3, full=gfull,
                         half=lambda x, z: SB_SL, rails=False))
    k = 0
    for (a, b) in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        n = max(1, int(L / 5))
        for i in range(n):
            t = (i + 0.5) / n
            px, pz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            ux, uz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
            s = 1 if k % 2 else -1
            k += 1
            mush_lamp(C, round(px - uz * 3 * s), G + 1, round(pz + ux * 3 * s))


def scenery(C):
    """Giant mushrooms on the plateau and round its foot, small fungi on the open ground."""
    for (x, z, h, red) in ((44, -40, 17, True), (-64, -12, 13, False), (58, -26, 11, True), (-28, -66, 12, True),
                           (32, -66, 14, False), (-62, 30, 11, False), (64, 30, 9, True), (-8, -74, 9, True),
                           (-58, -58, 10, True), (50, -60, 8, True), (34, 40, 7, False), (-46, 46, 8, True)):
        if C.kind.get((x, z)) == "plat" and C.free(x, G + 1, z) and (x, z) not in WALK:
            mushroom(C, x, z, h, red, seed=h)
    rng = random.Random(841)
    for _ in range(260):
        x, z = rng.randint(-70, 70), rng.randint(-76, 50)
        if C.kind.get((x, z)) != "plat" or (x, z) in WALK:
            continue
        if C.solid(x, G, z) and C.free(x, G + 1, z) and (x, G + 1, z) not in C.keep and \
                (C.get(x, G, z) or "").endswith(("mycelium", "podzol", "rooted_dirt")):
            C.set(x, G + 1, z, rng.choice(("red_mushroom", "brown_mushroom", "red_mushroom", ROOTS)))


# ------------------------------------------------------------------ room lighting (hand-placed grids)
def lamp_grid(C, cells, feet, h=3, step=5, lamp=LANT_H, reach=16, post=False):
    """Lamps on a staggered grid over the floor cells ``cells`` at feet: hung on chains h above the floor from the
    first solid block over them (never through a walkway's headroom), or on short iron posts (``post``)."""
    n = 0
    for (x, z) in cells:
        if z % step:
            continue
        if (x + (step // 2 if (z // step) % 2 else 0)) % step:
            continue
        if not (C.free(x, feet, z) and C.free(x, feet + 1, z) and C.solid(x, feet - 1, z)):
            continue
        if post:
            if (x, feet, z) in C.keep or (x, feet + 1, z) in C.keep or not C.free(x, feet + 2, z):
                continue
            C.set(x, feet, z, IRON_WALL)
            C.set(x, feet + 1, z, lamp)
            n += 1
            continue
        y = feet + h
        if not C.free(x, y, z):
            continue
        top = y + 1
        while top < y + reach and C.free(x, top, z):
            top += 1
        if not C.solid(x, top, z) or any((x, yy, z) in C.keep for yy in range(y, top)):
            continue
        for yy in range(y + 1, top):
            C.set(x, yy, z, CHAIN)
        C.set(x, y, z, lamp)
        n += 1
    return n


def rect_cells(x0, z0, x1, z1):
    return [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)]


def room_lights(C):
    """Lamp grids room by room (the light check's fallback only mops up after these)."""
    # the monastery's ranges and halls
    lamp_grid(C, rect_cells(-19, 45, 19, 53), G + 1)
    lamp_grid(C, rect_cells(-39, 1, -21, 43), G + 1)
    lamp_grid(C, rect_cells(21, -1, 45, 43), G + 1, h=3, step=5)
    for z in range(1, 44, 4):
        wall_lamp(C, ERANGE[0], G + 3, z)
        wall_lamp(C, ERANGE[2], G + 3, z)
    for x in range(23, 46, 4):
        wall_lamp(C, x, G + 3, ERANGE[1])
        wall_lamp(C, x, G + 3, ERANGE[3])
    lamp_grid(C, rect_cells(41, 3, 45, 40), G + 8, h=3, step=5)
    lamp_grid(C, [(x, z) for (x, z) in rect_cells(*CLO) if not in_garth(x, z)], G + 1, step=5)
    lamp_grid(C, rect_cells(-10, -7, 10, 5), G + 1, step=5)
    lamp_grid(C, rect_cells(-1, 54, 1, 59), GT + 1, step=3)
    # towers and the library
    lamp_grid(C, disk_pts(LIB[0], LIB[1], 12.0), G + 1)
    for (y, rr) in ((G + 3, lib_inner(G + 3)), (G + 13, lib_inner(G + 13))):
        for k in range(16):
            a = 11.25 + 22.5 * k
            if adelta(a, 60) < 15 or adelta(a, 96) < 15:
                continue
            for r10 in range(int(rr * 10) - 14, int(rr * 10) + 20, 3):
                x, z = rp(r10 / 10.0, a, LIB)
                if C.solid(x, y, z):
                    C.set(x, y, z, EDISON) if "bookshelf" in (C.get(x, y, z) or "") or wall_lamp(C, x, y, z) else None
                    break
    lamp_grid(C, [(x, z) for (x, z) in disk_pts(LIB[0], LIB[1], 12.0)
                  if math.hypot(x - LIB[0], z - LIB[1]) > 6.4], G + 11)
    lamp_grid(C, disk_pts(TR[0], TR[1], 10.0), G + 31)
    lamp_grid(C, disk_pts(TB[0], TB[1], 12.0), G + 25)
    # the temple
    nave_cells = [(x, z) for (x, z) in disk_pts(MX, MZ, 20.0) if dm(x, z) > 6.5 and not (abs(x) <= 1 and z > MZ)]
    lamp_grid(C, nave_cells, G + 1, step=6, lamp=LANT, post=True)
    for feet in (36, 52, 68):
        lamp_grid(C, [(x, z) for (x, z) in disk_pts(MX, MZ, 13.0) if dm(x, z) > 5.4], feet, step=5)
    lamp_grid(C, [(x, z) for (x, z) in disk_pts(MX, MZ, 22.6) if dm(x, z) > 16.6], 68, step=5, reach=8)
    lamp_grid(C, rect_cells(-6, MZ - 17, 6, MZ - 3), VAULT_F, h=3, step=4)
    # under the plateau
    lamp_grid(C, disk_pts(MX, MZ, 13.0), CAT_F, h=3, step=5, reach=8)
    lamp_grid(C, rect_cells(-25, -13, -19, -7), CAT_F, h=3, step=4)
    lamp_grid(C, rect_cells(-39, -29, -23, -18), CAT_F, h=3, step=5)
    gx, gz, rx, rz, _ = GROTTO
    lamp_grid(C, rect_cells(int(gx - rx), int(gz - rz), int(gx + rx), int(gz + rz)), CAT_F, h=3, step=6, reach=8)
    # the arena: a second ring of shroomlights in the floor, braziers round the rim
    for (x, z) in disk_pts(MX, MZ, 18.0):
        d = dm(x, z)
        if abs(d - 17.5) < 0.5 and (int(am(x, z)) // 6) % 2 and C.get(x, AY, z) not in (None, AIR) and \
                C.free(x, AY + 1, z):
            C.set(x, AY, z, SHROOM)


# ------------------------------------------------------------------ lighting check (fallback only)
LIGHT_STATS = {}


def light_pass(C):
    """Every covered floor (a ceiling within 14 blocks over the head) should have block light 8 or more from the
    hand-placed lamps; the few floors that stay dark get a lit copper bulb set in their ceiling (low ceilings) or in
    the floor (tall halls). The count is reported so the hand placement can be tuned."""
    import numpy as np
    from ..blueprint import is_solid
    from .leviathan_lighthouse import LIGHT_EMIT
    blocks = C.bp.blocks
    xs = [p[0] for p in blocks]
    ys = [p[1] for p in blocks]
    zs = [p[2] for p in blocks]
    X0, Y0, Z0 = min(xs) - 1, min(ys) - 1, min(zs) - 1
    SH = (max(xs) - X0 + 2, max(ys) - Y0 + 2, max(zs) - Z0 + 2)
    opaque = np.zeros(SH, bool)
    known = np.zeros(SH, bool)
    L = np.zeros(SH, np.int8)
    wet = np.zeros(SH, bool)
    full = np.zeros(SH, bool)
    for (x, y, z), v in blocks.items():
        n, pr = v[0], v[1] or {}
        sh = n.split(":")[1]
        i = (x - X0, y - Y0, z - Z0)
        known[i] = True
        e = LIGHT_EMIT.get(sh, 0)
        if ("bulb" in sh or "furnace" in sh or sh == "smoker" or sh == "redstone_lamp") and pr.get("lit") != "true":
            e = 0
        if sh == "campfire" and pr.get("lit") != "true":
            e = 0
        if sh.endswith("candle") and pr.get("lit") == "true":
            e = 3 * int(pr.get("candles", 1))
        if sh == "glow_lichen":
            e = 7
        if sh in ("water", "bubble_column") or pr.get("waterlogged") == "true":
            wet[i] = True
        if is_solid(n) and sh not in ("air", "cave_air"):
            full[i] = True
        if e:
            L[i] = e
        elif is_solid(n) and sh not in ("air", "cave_air") and not sh.endswith("_slab") and "glass" not in sh:
            opaque[i] = True
    for lvl in range(15, 1, -1):
        m = (L == lvl)
        if not m.any():
            continue
        for ax in range(3):
            for d in (1, -1):
                upd = np.roll(m, d, axis=ax) & ~opaque & (L < lvl - 1)
                L[upd] = lvl - 1

    def spread(x, y, z, lvl):
        i0 = (x - X0, y - Y0, z - Z0)
        L[i0] = max(L[i0], lvl)
        q = [(i0, lvl)]
        while q:
            nq = []
            for (i, l) in q:
                for ax in range(3):
                    for d in (1, -1):
                        j = list(i)
                        j[ax] += d
                        j = tuple(j)
                        if not (0 <= j[ax] < SH[ax]) or opaque[j] or L[j] >= l - 1:
                            continue
                        L[j] = l - 1
                        if l - 1 > 1:
                            nq.append((j, l - 1))
            q = nq

    air = ~opaque
    stand = np.zeros(SH, bool)
    stand[:, 1:-1, :] = air[:, 1:-1, :] & opaque[:, :-2, :] & air[:, 2:, :] & known[:, :-2, :] & known[:, 1:-1, :]
    cov = np.zeros(SH, bool)
    for k in range(2, 16):
        cov[:, :-k, :] |= opaque[:, k:, :]
    stand[:, 1:-1, :] &= ~full[:, 1:-1, :] & ~full[:, 2:, :]
    stand &= ~wet
    for (x, z) in SCENERY:
        if 0 <= x - X0 < SH[0] and 0 <= z - Z0 < SH[2]:
            stand[x - X0, :, z - Z0] = False
    cells = np.argwhere(stand & cov & (L < 8))
    LIGHT_STATS["dark_before"] = int(len(cells))
    LIGHT_STATS["covered"] = int((stand & cov).sum())
    LIGHT_STATS["dark"] = [(int(a) + X0, int(b) + Y0, int(c) + Z0) for a, b, c in cells]
    order = sorted(((int(a) + X0, int(b) + Y0, int(c) + Z0) for a, b, c in cells),
                   key=lambda p: (0 if (p[0] % 5 == 0 and p[2] % 5 == 0) else 1, p[1], p[0], p[2]))

    def ok_block(x, y, z):
        b = C.get(x, y, z) or ""
        return b and opaque[x - X0, y - Y0, z - Z0] and not any(k in b for k in NO_LAMP) and \
            (x, y, z) not in C.keep

    added = 0
    LIGHT_STATS["where"] = []
    for (x, f, z) in order:
        if L[x - X0, f - Y0, z - Z0] >= 8:
            continue
        cy = f + 2
        while not opaque[x - X0, cy - Y0, z - Z0]:
            cy += 1
        if cy - f <= 5 and ok_block(x, cy, z):
            p = (x, cy, z)
        elif ok_block(x, f - 1, z):
            p = (x, f - 1, z)
        else:
            continue
        C.bp.set(*p, BULB)
        LIGHT_STATS["where"].append(p)
        opaque[p[0] - X0, p[1] - Y0, p[2] - Z0] = False
        spread(*p, 15)
        added += 1
    LIGHT_STATS["bulbs_added"] = added
    print(f"mycelium_monastery: light check: {LIGHT_STATS['covered']} covered floor cells, "
          f"{LIGHT_STATS['dark_before']} below 8 before the fallback, {added} fallback bulbs")


def extra_lamps(C):
    """Hand-placed fixtures for the long dark runs: lanterns hung along the rock tunnels, sconces in the stair
    shafts, lamps on the plateau's open ground by the paths."""
    for pts in ([(-30, -30), (-28, -38), (-26, -43)], [(-15, -47), (-12, -40), (-11, -34)]):
        for a, b in zip(pts, pts[1:]):
            n = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / 4.0))
            for i in range(n):
                t = (i + 0.5) / n
                x, z = round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t)
                if C.free(x, CAT_F + 3, z) and (x, CAT_F + 3, z) not in C.keep:
                    hang(C, x, CAT_F + 3, z, LANT_H, reach=4)
    # the undercroft stair and the gate stair: sconces in their side walls
    for z in range(-3, 10, 3):
        y = CAT_F + (z + 4) + 2
        wall_lamp(C, -32, y, z, LANT) if C.solid(-32, y, z) else None
    for z in range(48, 56, 3):
        y = GT + (57 - z) + 2
        wall_lamp(C, 2, y, z, LANT) if C.solid(2, y, z) else None
    # lamp posts on the open plateau between the buildings
    for (x, z) in ((-16, -14), (16, -6), (24, -12), (-4, 0), (8, 2), (36, -6), (-36, -6), (-44, 18), (30, 48),
                   (-30, 50), (0, 2), (18, 0)):
        if C.kind.get((x, z)) == "plat" and floor_ok(C, x, G + 1, z):
            lamp_post(C, x, G + 1, z, 3, LANT)


# ------------------------------------------------------------------ the whole site
def mycelium_monastery(bp):
    WALK.clear()
    HELIX.clear()
    SCENERY.clear()
    C = Ctx(bp)
    heightfield(C)
    write_terrain(C)
    # the temple
    temple_stem(C)
    facade(C)
    cage_lift(C)
    helices(C)
    stem_doors(C)
    cap_and_arena(C)
    treasury(C)
    turret(C)
    arena_dress(C)
    stem_dressing(C)
    nave(C)
    chapter_house(C)
    sporarium(C)
    gill_gallery(C)
    level_rails(C)
    # under the plateau
    catacombs(C)
    grotto(C)
    root_heart(C)
    # the monastery
    cloister(C)
    south_range(C)
    gatehouse(C)
    distillery(C)
    red_end = red_tower(C)
    west_range(C)
    for x in range(-21, -18):                      # where the west range's roof meets the south range's
        for z in range(43, 46):
            for y in range(G + 8, G + 13):
                if "stairs" in (C.get(x, y, z) or ""):
                    C.set(x, y, z, CUT_OX)
    b_lib, b_temple = brown_tower(C)
    lib_end = library(C)
    rope_bridge(C, b_temple, polar(16.8, 151), 36, sag=2.0)
    rope_bridge(C, red_end, polar(16.8, 27), 36, sag=2.0)
    rope_bridge(C, lib_end, b_lib, 27, sag=1.0)
    # outside
    camp(C)
    approach(C)
    garden_path(C)
    scenery(C)
    seal_caves(C)
    extra_lamps(C)
    room_lights(C)
    light_pass(C)


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("cloister_garth", (-1, 17, 11), (2, 18, 24)),
    ("spore_distillery", (29, 17, 41), (33, 21, 34)),
    ("refectory", (-22, 17, 38), (-34, 18, 38)),
    ("ossuary", (-30, 3, -18), (-30, 5, -28)),
    ("glowing_grotto", (-17, 3, -50), (-28, 5, -50)),
    ("nave", (2, 17, -10), (2, 25, -42)),
    ("puffball_library", (-40, 17, -29), (-46, 22, -36)),
    ("cap_arena", (0, 85, -45), (0, 92, -28)),
]

register(StructureDef(
    "mycelium_monastery", "overworld", ["mushroom_fields", "dark_forest"],
    [Piece("monastery", mycelium_monastery, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", processors="none", max_distance=128, foundation=False,
    spawns=[(MOB_BOGGED, 4, 1, 2), (MOB_MONK, 4, 1, 1), (MOB_WITCH, 2, 1, 1)],
    title_fr="Le Monastère du Mycélium", title_en="The Mycelium Monastery"))

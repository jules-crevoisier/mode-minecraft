"""Forge of the Basalt Titan (La Forge du Titan de basalte): a colossal forge over a Nether lava lake, built into
and around a kneeling titan of basalt and brass, 85 high, bent over a giant anvil. Colossal tier
(tools/BUILDING.md §1, §12 concept 18, §10, §15).

Silhouette (one noun phrase, §15.1): a kneeling black giant with a smoking crest of chimneys on its back, raising a
sledgehammer over an anvil the size of a keep, one arm reaching down to it.

Layout, blueprint y = world y - 30 (template bottom = the lava lake floor, lava surface at y 1 = world 31); x east,
z south. The titan kneels on the forge plinth (x -78..16, top at y 17, feet 18) facing east: the left knee on the
plinth (-22, z -14), the right foot planted forward on the plinth's lobe (z 13), its torso bent forward, its head
over the anvil. The anvil stands in the lava east of it (face x 26..74, z -19..19, feet 36), its horn pointing east.

The route (main path ~500 path blocks):
  * the approach: from the marker on the south-west shore to the forgemasters' outpost (waystone), north along a
    basalt causeway, east through the Toll Arch that frames the titan's back and its raised hammer, past two lava
    falls pouring from crucibles on the plinth into moulds, to the colossal portal (a wicket in its iron leaves);
  * the plinth (feet 4): a compressed passage, then the casting hall (21 x 29, open to its roof 40 high) with
    glass-covered lava channels, a hanging crucible pouring into the pour basin and the ingot moulds; north, the
    bellows chambers with two giant leather bellows feeding the hall's furnaces; the grand stair (two flights) up to
    the plinth top;
  * the crucible terrace (feet 18, the hub, waystone): the north terrace, the east terrace before the titan's knee
    with the third crucible pouring into a mould between the plinth and the anvil, the spine lift's cage;
  * the titan: a door in the left knee, the newel stair up the thigh, the forgemasters' barracks in the pelvis, the
    armoury in the belly, the smelting hall in the back (blast furnaces under the chimneys), the yoke through the
    chest; the left shoulder, the stair down the upper arm to the elbow's winch room (waystone, the crane gear), the
    crane-bridge: a narrow stair down the forearm (compression) into the hand resting on the anvil, the mist;
  * the boss: the arena on the anvil's face (r 17, the hammer's face 30 above), sealed bars on the south balcony; a
    ledge stair down the anvil's side to the vault in its heel, more sealed bars, and the bridge down to the plinth's
    lobe (the shortcut back to the hub).
Shortcuts: the lift in the titan's spine (smelting hall -> hub cage -> plinth lobby; its iron doors open from the
lift side only); the side route along the south shore into the slag mine's adit; the bridge from the vault.
Optional: the slag mine and its hidden drift, the hammer-gallery up the raised right arm to the fist (a balcony over
the arena), the forgemaster's eyrie in the helmet (a ladder from the yoke), the north terrace's ore yard.
Loot gradient (§15.6): outpost, casting hall 1; bellows, barracks 1-2; slag mine, armoury, smelting hall 2; drift,
hammer-gallery 2-3; eyrie 3; vault 3+.
Height budget: the fist tops out at y 87, the chimneys at 88 (world 118, under the bedrock roof).
"""
import math

import numpy as np

from ..arch import Palette, slab, stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, BRASS_STAIRS, COPPER, EDISON, GAUGE, GEAR, IRON, IRON_SLAB, IRON_STAIRS,
                       IRON_WALL, LEATHER, PIPES, SMOKE, SMOKE_STAIRS, SMOKE_WALL, TREAD, TREAD_SLAB, W, fbm, hash01,
                       hash3, vnoise)
from ..parts import LOOT, MOB, MOD
from .caldera_ringwall import newel
from .nether import CHIS, GBS, GILD, LAMP, PB, PBB, PBBS, PBBSL, PBBW, brazier, chandelier

# the forge's own warden: the Anvil Warden (mobs/anvil_warden.py, entity/boss/AnvilWarden.java, tools/BOSSES.md)
BOSS = "brasshaven:anvil_warden"
MOB_GUARD = MOB["basalt_guard"]
MOB_HOUND = "brasshaven:cinder_hound"
MOB_SENTRY = "brasshaven:magma_sentry"
MOB_IMP = "brasshaven:ember_imp"
MOB_CUBE = "minecraft:magma_cube"
MOB_BLAZE = "minecraft:blaze"
MOB_WSKEL = "minecraft:wither_skeleton"

# ------------------------------------------------------------------ levels
LAVA_Y = 1
LOW = 4            # feet in the plinth (floor y 3)
PTOP = 17          # plinth top block
HUB = 18           # feet on the plinth top
BAR = 40           # barracks (pelvis)
ARM = 49           # armoury (belly)
SME = 58           # smelting hall (back)
YOKE = 60          # yoke and left shoulder
RSH = 63           # right shoulder
ELB = 49           # left elbow (winch room, waystone)
AF = 36            # arena feet (anvil face y 35)
VF = 28            # vault feet
AC = (50, 0)       # arena centre
AR = 17            # arena radius

AIR = "minecraft:air"
LAVA = "lava[level=0]"
FALL = "lava[level=8]"
GLASS = "orange_stained_glass"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
SCAF = "scaffolding[bottom=false,distance=0,waterlogged=false]"
HANG_SOUL = "soul_lantern[hanging=true,waterlogged=false]"
HANG_LANT = "lantern[hanging=true,waterlogged=false]"
LANT = "lantern[hanging=false,waterlogged=false]"
COPPER_STAIRS = W + "copper_plating_stairs"
COPPER_SLAB = W + "copper_plating_slab"
RAIL = W + "brass_railing"

FLOOR = Palette({PB: 4, PBB: 3, "polished_basalt[axis=y]": 1}, seed=601, scale=1.8)
PATH = Palette({PBB: 5, CHIS: 1, PB: 2}, seed=602, scale=1.4)
ROCK = Palette({"basalt[axis=y]": 4, "blackstone": 4, "netherrack": 2, "magma_block": 0.4}, seed=603, scale=3.5)
INNER = Palette({PBB: 6, "cracked_polished_blackstone_bricks": 1, PB: 2}, seed=604, scale=2.2)
DECK = Palette({TREAD: 5, IRON: 2}, seed=605, scale=1.6)

# ------------------------------------------------------------------ the numpy grid of the masses
GX0, GX1 = -84, 100
GY0, GY1 = 0, 92
GZ0, GZ1 = -46, 46
SHAPE = (GX1 - GX0 + 1, GY1 - GY0 + 1, GZ1 - GZ0 + 1)

# labels of the solid masses
PLINTH, BODY, ARMOUR, ANVIL, HALL, HAMMER, HANDLE, ROOF, CAGE, HELM, TRIM = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11


def _sl(x0, x1, y0, y1, z0, z1):
    x0, x1 = max(int(math.floor(x0)), GX0), min(int(math.ceil(x1)), GX1)
    y0, y1 = max(int(math.floor(y0)), GY0), min(int(math.ceil(y1)), GY1)
    z0, z1 = max(int(math.floor(z0)), GZ0), min(int(math.ceil(z1)), GZ1)
    if x0 > x1 or y0 > y1 or z0 > z1:
        return None
    sl = (slice(x0 - GX0, x1 - GX0 + 1), slice(y0 - GY0, y1 - GY0 + 1), slice(z0 - GZ0, z1 - GZ0 + 1))
    X = np.arange(x0, x1 + 1, dtype=np.float32)[:, None, None]
    Y = np.arange(y0, y1 + 1, dtype=np.float32)[None, :, None]
    Z = np.arange(z0, z1 + 1, dtype=np.float32)[None, None, :]
    return sl, X, Y, Z


def capsule(p0, p1, r0, r1):
    r = max(r0, r1) + 1
    s = _sl(min(p0[0], p1[0]) - r, max(p0[0], p1[0]) + r, min(p0[1], p1[1]) - r, max(p0[1], p1[1]) + r,
            min(p0[2], p1[2]) - r, max(p0[2], p1[2]) + r)
    sl, X, Y, Z = s
    dx, dy, dz = (p1[i] - p0[i] for i in range(3))
    L2 = dx * dx + dy * dy + dz * dz
    t = np.clip(((X - p0[0]) * dx + (Y - p0[1]) * dy + (Z - p0[2]) * dz) / L2, 0.0, 1.0)
    d2 = (X - p0[0] - t * dx) ** 2 + (Y - p0[1] - t * dy) ** 2 + (Z - p0[2] - t * dz) ** 2
    rr = r0 + (r1 - r0) * t
    return sl, d2 <= (rr + 0.2) ** 2


def ellipsoid_xyz(c, rad):
    s = _sl(c[0] - rad[0] - 1, c[0] + rad[0] + 1, c[1] - rad[1] - 1, c[1] + rad[1] + 1, c[2] - rad[2] - 1,
            c[2] + rad[2] + 1)
    sl, X, Y, Z = s
    v = ((X - c[0]) / (rad[0] + 0.3)) ** 2 + ((Y - c[1]) / (rad[1] + 0.3)) ** 2 + ((Z - c[2]) / (rad[2] + 0.3)) ** 2
    return sl, v <= 1.0, X, Y, Z


def ellipsoid(c, rad):
    sl, m, _, _, _ = ellipsoid_xyz(c, rad)
    return sl, m


def boxm(x0, x1, y0, y1, z0, z1):
    sl, X, Y, Z = _sl(x0, x1, y0, y1, z0, z1)
    return sl, np.ones((X.shape[0], Y.shape[1], Z.shape[2]), bool)


def paint(grid, prim, val=True, where=None):
    sl, m = prim
    if where is not None:
        m = m & where[sl]
    grid[sl][m] = val


def _shift_or(out, a, dx, dy, dz):
    n = a.shape
    out[max(dx, 0):n[0] + min(dx, 0), max(dy, 0):n[1] + min(dy, 0), max(dz, 0):n[2] + min(dz, 0)] |= \
        a[max(-dx, 0):n[0] + min(-dx, 0), max(-dy, 0):n[1] + min(-dy, 0), max(-dz, 0):n[2] + min(-dz, 0)]


def dilate(a, six=False):
    out = a.copy()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dy, dz) == (0, 0, 0) or (six and abs(dx) + abs(dy) + abs(dz) != 1):
                    continue
                _shift_or(out, a, dx, dy, dz)
    return out


def erode(a, six=False):
    return ~dilate(~a, six)


# ------------------------------------------------------------------ the titan's skeleton
L_KNEE = (-22, 23, -14)
R_KNEE = (2, 47, 15)
L_SHOULDER = (-12, 66, -19)
R_SHOULDER = (-12, 66, 20)
L_ELBOW = (8, 52, -26)
R_ELBOW = (4, 77, 27)
L_HAND = (32, 38.5, -15)
FIST = (21, 81, 12)
HEAD = (6, 74, 0)
HAMMER_C = (46, 0)          # the hammer head: an octagonal block over the arena, face at y 66, poll at 83
HAMMER_Y = (66, 83)
HANDLE_P = ((14, 83, 15), (45, 75, 0))


def titan_parts():
    """(primitive, label) list of the statue: limbs as tapered capsules, body as ellipsoids."""
    P = []
    # left leg, kneeling: the shin and the toes lie on the plinth, pointing back
    P.append(capsule((-24, 22, -14), (-50, 21, -14), 6.5, 5.5))
    P.append(capsule((-50, 20, -14), (-62, 19, -14), 5.0, 3.5))
    P.append(ellipsoid(L_KNEE, (7.5, 7.5, 7.5)))
    P.append(capsule((-22, 24, -14), (-32, 42, -10), 7.0, 8.5))
    # right leg: the foot planted forward on the plinth's lobe, the shin up, the thigh back to the hip
    P.append(capsule((-2, 20, 13), (15, 19, 13), 5.0, 4.5))
    P.append(capsule((3, 22, 13), (2, 46, 15), 5.5, 6.5))
    P.append(ellipsoid(R_KNEE, (7.5, 7.5, 7.5)))
    P.append(capsule(R_KNEE, (-30, 43, 10), 7.0, 9.0))
    # pelvis, torso bent over the anvil, the chest
    P.append(ellipsoid((-32, 44, 0), (11, 9, 15)))
    for k in range(21):
        t = k / 20
        c = (-30 + 18 * t, 48 + 16 * t, 0)
        P.append(ellipsoid(c, (10 + 3 * t, 10 + 3 * t, 13 + 6 * t)))
    P.append(ellipsoid((-12, 62, 0), (12, 11, 18)))
    # shoulders, neck, head
    P.append(ellipsoid(L_SHOULDER, (8.5, 8.5, 8.5)))
    P.append(ellipsoid(R_SHOULDER, (8.5, 8.5, 8.5)))
    P.append(capsule((-8, 67, 0), (2, 72, 0), 5.5, 5.0))
    P.append(ellipsoid(HEAD, (7.5, 8.5, 7)))
    P.append(capsule((9, 71, 0), (12, 68, 0), 3.5, 2.5))               # the jaw, bent down over the anvil
    # left arm: reaches down to the anvil (the crane-bridge)
    P.append(capsule((-12, 64, -20), L_ELBOW, 6.0, 5.3))
    P.append(ellipsoid(L_ELBOW, (7.5, 7.5, 7.5)))
    P.append(capsule(L_ELBOW, (28, 39, -18), 5.3, 5.6))
    P.append(ellipsoid(L_HAND, (7, 4, 6.5)))
    for k, dz in enumerate((-4.5, -1.5, 1.5, 4.5)):        # fingers, laid on the anvil face
        P.append(capsule((36, 38, -15 + dz), (41 - abs(dz) * 0.4, 36.5, -15 + dz * 1.1), 1.6, 1.3))
    P.append(capsule((30, 37.5, -10), (35, 36.5, -6.5), 1.8, 1.4))   # the thumb
    # right arm: raised, the fist holding the hammer over the anvil
    P.append(capsule((-12, 66, 20), R_ELBOW, 6.0, 5.2))
    P.append(ellipsoid(R_ELBOW, (6.5, 6.5, 6.5)))
    P.append(capsule(R_ELBOW, (18, 81, 14), 5.2, 5.0))
    P.append(ellipsoid(FIST, (5.5, 5.5, 5.5)))
    return P


def anvil_parts():
    """The giant anvil: stepped foot, waisted body, the face block, the horn to the east."""
    P = []
    for y0, y1, x0, x1, z0, z1 in ((0, 3, 30, 70, -21, 21), (4, 7, 33, 67, -18, 18), (8, 9, 36, 64, -14, 14),
                                   (10, 19, 39, 61, -10, 10), (20, 21, 36, 64, -13, 13), (22, 23, 31, 69, -16, 16),
                                   (24, 35, 26, 74, -19, 19)):
        P.append(boxm(x0, x1, y0, y1, z0, z1))
    # the horn: a cone east of the face, its top flush with the face at the root
    P.append(capsule((74, 31, 0), (96, 33.5, 0), 6.0, 0.6))
    P.append(capsule((74, 29, 0), (90, 31, 0), 6.5, 2.5))
    return P


def plinth_mask2d():
    """2D footprint of the forge plinth (top): a rounded block plus the lobe under the right foot."""
    xs = np.arange(GX0, GX1 + 1)[:, None]
    zs = np.arange(GZ0, GZ1 + 1)[None, :]

    def rrect(x0, x1, z0, z1, r):
        cx = np.clip(xs, x0 + r, x1 - r)
        cz = np.clip(zs, z0 + r, z1 - r)
        return np.hypot(xs - cx, zs - cz) <= r + 0.3
    return rrect(-74, 0, -40, 38, 8) | rrect(-6, 16, 2, 26, 6)


def plinth_parts():
    """The plinth as one column mask: battered (wider at the bottom, one block every 4)."""
    top2d = plinth_mask2d()
    m = np.zeros(SHAPE, bool)
    grow = top2d.copy()
    for y in range(PTOP, -1, -1):
        if (PTOP - y) % 4 == 3:
            g = grow.copy()
            g[1:, :] |= grow[:-1, :]
            g[:-1, :] |= grow[1:, :]
            g[:, 1:] |= grow[:, :-1]
            g[:, :-1] |= grow[:, 1:]
            grow = g
        m[:, y, :] = grow
    return m


# ------------------------------------------------------------------ the masses and the carved rooms
class Masses:
    pass


M = Masses()


def hall_roof_h(x):
    """Top of the casting hall's gable roof (ridge along z at x -56)."""
    return 31 + min(x + 69, -43 - x)


def newel_plan():
    """The newel stair up the left thigh (outer 8 x 8, flights of 2): from the knee hall (feet 18) to the barracks
    (feet 40). Returns (cells, core, top corner index, top feet) from caldera_ringwall.newel, in laps of 3."""
    parts = []
    c, f = 1, HUB
    flights = [2] * 11
    for i in range(0, len(flights), 3):
        cells, core, c, f1 = newel(-31, -16, 2, f, flights[i:i + 3], c, cw=True)
        parts.append((cells, core, f))
        f = f1
    return parts, c, f


NEWEL_X0, NEWEL_Z0 = -31, -16


def corner_box(c):
    cx, cz = {0: (NEWEL_X0, NEWEL_Z0), 1: (NEWEL_X0 + 5, NEWEL_Z0), 2: (NEWEL_X0 + 5, NEWEL_Z0 + 5),
              3: (NEWEL_X0, NEWEL_Z0 + 5)}[c]
    return cx, cx + 2, cz, cz + 2


def arm_axis(p0, p1, x):
    t = (x - p0[0]) / (p1[0] - p0[0])
    return p0[1] + (p1[1] - p0[1]) * t, p0[2] + (p1[2] - p0[2]) * t


def left_arm_path():
    """[(x, z centre, feet)] of the stair down the left upper arm (shoulder -> elbow) and the forearm (elbow ->
    hand)."""
    out = []
    for x in range(-8, 4):                       # upper arm: feet 60 down to 49
        _, zc = arm_axis((-12, 64, -20), L_ELBOW, x)
        out.append((x, int(round(zc)), YOKE - (x + 8)))
    for x in range(12, 25):                      # forearm: 49 down to 36
        _, zc = arm_axis(L_ELBOW, (28, 39, -18), x)
        out.append((x, int(round(zc)), ELB - (x - 11)))
    return out


def right_arm_path():
    """[(x, z centre, feet)] of the hammer-gallery: up the right upper arm (feet 63 -> 75) and along the forearm."""
    out = []
    for x in range(-7, 5):                       # a straight flight (z 23..25) inside the drifting arm
        out.append((x, 24, RSH + 1 + (x + 7)))
    f = 75
    for x in range(9, 19):
        _, zc = arm_axis(R_ELBOW, (18, 81, 14), x)
        if x in (11, 14, 17):
            f += 1
        out.append((x, int(round(zc)), f))
    return out


def build_masses():
    lab = np.zeros(SHAPE, np.uint8)
    plinth = plinth_parts()
    lab[plinth] = PLINTH
    # the casting hall above the plinth: walls to the eaves, then the gable roof (ridge along z)
    paint(lab, boxm(-68, -44, PTOP, 30, -5, 27), HALL)
    for x in range(-69, -42):
        h = hall_roof_h(x)
        paint(lab, boxm(x, x, 31, h, -6, 28), ROOF)
    for prim in anvil_parts():
        paint(lab, prim, ANVIL)
    body = np.zeros(SHAPE, bool)
    for prim in titan_parts():
        paint(body, prim, True)
    # armour shells: one block over the body where the plates are
    arm = np.zeros(SHAPE, bool)
    trim = np.zeros(SHAPE, bool)
    helm = np.zeros(SHAPE, bool)
    for c in (L_SHOULDER, R_SHOULDER):                                          # pauldrons: a cap, a brass rim
        sl, m, X, Y, Z = ellipsoid_xyz(c, (9.4, 9.0, 9.4))
        arm[sl] |= m & (Y >= c[1] + 1)
        trim[sl] |= m & (Y >= c[1] + 1) & (Y <= c[1] + 2)
    for c in (L_KNEE, R_KNEE):                                                 # knee poleyns, front and top
        sl, m, X, Y, Z = ellipsoid_xyz(c, (8.6, 8.6, 8.6))
        arm[sl] |= m & (X >= c[0] - 2) & (Y >= c[1] - 3)
    sl, m, X, Y, Z = ellipsoid_xyz(HEAD, (8.6, 9.6, 8.1))                       # the helm, above the visor line
    helm[sl] |= m & ((Y >= HEAD[1] + 1) | ((X <= HEAD[0] - 2) & (Y >= HEAD[1] - 5)))
    sl, m, X, Y, Z = ellipsoid_xyz((HEAD[0] - 1, HEAD[1] + 7, 0), (8.5, 4.5, 1.6))    # the crest
    helm[sl] |= m & (Y >= HEAD[1] + 4)
    for sz in (-1, 1):                                                           # horns, swept back
        paint(helm, capsule((HEAD[0] - 1, HEAD[1] + 5, 6.5 * sz), (HEAD[0] - 6, HEAD[1] + 12, 10 * sz), 1.9, 0.7))
    for p0, p1, r in ((L_ELBOW, (28, 39, -18), 6.6), (R_ELBOW, (18, 81, 14), 6.3)):   # bracers on the forearms
        a = (p0[0] + (p1[0] - p0[0]) * 0.55, p0[1] + (p1[1] - p0[1]) * 0.55, p0[2] + (p1[2] - p0[2]) * 0.55)
        paint(arm, capsule(a, p1, r, r))
    sl, m = ellipsoid((-32, 45, 0), (12.3, 2.2, 16.3))                          # the belt round the pelvis
    trim[sl] |= m
    sl, m, X, Y, Z = ellipsoid_xyz((-12, 62, 0), (13.2, 12.0, 19.0))            # chest plate (front half)
    arm[sl] |= m & (X >= -8) & (np.abs(Z) <= 15)
    arm &= ~body
    trim &= ~body
    helm &= ~body
    lab[body] = BODY
    lab[arm & (lab == 0)] = ARMOUR
    lab[trim & (lab != PLINTH)] = TRIM
    lab[helm] = HELM
    # the hammer: an octagonal head over the arena, flared at both ends; the haft from the fist
    hx, hz = HAMMER_C
    y0, y1 = HAMMER_Y
    sl, X, Y, Z = _sl(hx - 9, hx + 9, y0, y1, hz - 9, hz + 9)
    flare = np.where(Y <= y0 + 1, 7.5, np.where(Y >= y1 - 1, 6.0, 7.0))     # flared face, chamfered poll
    ax, az = np.abs(X - hx), np.abs(Z - hz)
    head = (np.maximum(ax, az) <= flare) & (ax + az <= flare * 1.45)
    lab[sl][head] = HAMMER
    paint(lab, capsule(*HANDLE_P, 2.0, 2.0), HANDLE)
    M.lab = lab
    M.body = body
    return lab, body


def rooms(lab, body):
    """Interior air: ``air`` gets walls round it (two-block enclosure), ``cut`` does not (rooms inside the solid
    plinth and anvil, openings to the outside)."""
    air = np.zeros(SHAPE, bool)
    cut = np.zeros(SHAPE, bool)
    inner = erode(erode(body))
    shaft_wall = np.zeros(SHAPE, bool)
    paint(shaft_wall, boxm(-23, -17, 0, 60, -3, 3))
    # ---- the plinth (feet 4)
    paint(cut, boxm(-80, -67, LOW, LOW + 3, 9, 11))                     # the gate passage (compression)
    paint(cut, boxm(-66, -46, LOW, 29, -3, 25))                        # the casting hall, open to its roof
    for x in range(-66, -45):
        paint(cut, boxm(x, x, 30, hall_roof_h(x) - 2, -3, 25))
    paint(cut, boxm(-66, -46, LOW, 14, -34, -8))                       # the bellows chambers
    paint(cut, boxm(-58, -56, LOW, LOW + 3, -7, -4))                   # casting hall -> bellows
    paint(cut, boxm(-45, -43, LOW, LOW + 4, -31, -29))                 # bellows -> grand stair
    for i, x in enumerate(range(-42, -35)):                            # grand stair, flight 1 (feet 5..11)
        paint(cut, boxm(x, x, LOW + i, LOW + i + 4, -31, -29))
    paint(cut, boxm(-35, -33, LOW + 6, LOW + 11, -31, -29))            # landing, feet 11
    for i, x in enumerate(range(-32, -25)):                            # flight 2 (feet 12..18)
        paint(cut, boxm(x, x, LOW + 7 + i, LOW + 12 + i, -31, -29))
    paint(cut, boxm(-45, -26, LOW, LOW + 3, -1, 1))                    # casting hall -> lift lobby
    paint(cut, boxm(-24, -16, LOW, LOW + 5, -4, 4))                    # the lift lobby
    paint(cut, boxm(-50, -48, LOW, LOW + 3, 26, 31))                   # casting hall -> slag mine
    paint(cut, boxm(-50, -14, LOW, LOW + 3, 30, 32))                   # the mine drift
    paint(cut, boxm(-32, -30, LOW, LOW + 3, 33, 43))                   # the adit to the south shore
    paint(cut, boxm(-14, 12, LOW, LOW + 8, 8, 29))                     # the slag cavern
    paint(cut, boxm(-6, -6, LOW, LOW + 1, 30, 31))                     # the hidden drift (a 1-wide squeeze)
    paint(cut, boxm(-10, -3, LOW, LOW + 4, 32, 36))
    # ---- the spine lift: shaft from the lobby to the smelting hall floor (walls by enclosure)
    paint(air, boxm(-21, -19, LOW, SME - 1, -1, 1))
    # ---- the titan
    paint(air, boxm(-23, -15, HUB, HUB + 5, -18, -10))                 # the knee hall
    paint(air, boxm(NEWEL_X0, NEWEL_X0 + 7, HUB, BAR + 3, NEWEL_Z0, NEWEL_Z0 + 7))
    parts, c_top, f_top = newel_plan()
    M.newel = (parts, c_top, f_top)
    x0, x1, z0, z1 = corner_box(c_top)
    paint(air, boxm(x0, x1, BAR, BAR + 3, z0, -11))                     # newel top -> barracks
    paint(air, boxm(-40, -24, BAR, BAR + 5, -11, 11), where=inner & ~shaft_wall)       # barracks
    for i, x in enumerate(range(-33, -24)):                             # barracks -> armoury (z 7..9, east)
        paint(air, boxm(x, x, BAR + i, BAR + i + 4, 7, 9))
    paint(air, boxm(-32, -14, ARM, ARM + 6, -11, 11), where=inner & ~shaft_wall)       # armoury
    for i, x in enumerate(range(-18, -27, -1)):                         # armoury -> smelting (z -9..-7, west)
        paint(air, boxm(x, x, ARM + i, ARM + i + 4, -9, -7))
    paint(air, boxm(-31, -13, SME, SME + 11, -12, 12), where=inner)     # smelting hall
    paint(air, boxm(-12, -11, SME, SME + 4, -1, 1))                     # smelting -> yoke (2 steps)
    paint(air, boxm(-10, -7, YOKE, YOKE + 4, -16, 16))                  # the yoke
    paint(air, boxm(-16, -8, YOKE, YOKE + 4, -24, -16))                 # left shoulder
    for i, z in enumerate(range(17, 20)):                               # yoke -> right shoulder (3 up)
        paint(air, boxm(-10, -7, YOKE + i, YOKE + i + 4, z, z))
    paint(air, boxm(-16, -7, RSH, RSH + 4, 20, 24))                     # right shoulder
    paint(air, boxm(-6, -6, YOKE, 71, 0, 0))                            # ladder to the eyrie
    paint(air, boxm(-7, -2, 72, 75, -1, 1))
    paint(air, boxm(-2, 9, 72, 78, -4, 4), where=inner)                 # the eyrie in the helm
    # left arm: stair down to the elbow, the winch room, the crane-bridge down the forearm into the hand
    for (x, zc, f) in left_arm_path():
        paint(air, boxm(x, x, f, f + 3, zc - 1, zc + 1))
    paint(air, boxm(4, 11, ELB, ELB + 4, -29, -23))                     # the winch room
    paint(air, boxm(25, 34, AF, AF + 3, -19, -12))                       # inside the hand
    paint(cut, boxm(31, 33, AF, AF + 3, -11, -8))                        # out between thumb and fingers
    # right arm: the hammer-gallery
    for (x, zc, f) in right_arm_path():
        paint(air, boxm(x, x, f, f + 3, zc - 1, zc + 1))
    paint(air, boxm(3, 9, 75, 78, 21, 30))                               # the elbow trophy room
    paint(air, boxm(18, 23, 78, 81, 10, 14))                             # inside the fist
    paint(cut, boxm(24, 26, 79, 80, 10, 12))                             # the window between the fingers
    # the hammer's haft runs through the fist: keep it
    hm = np.zeros(SHAPE, bool)
    paint(hm, capsule(*HANDLE_P, 2.0, 2.0))
    air &= ~hm
    # ---- the anvil: the vault in the heel, its door onto the south ledge
    paint(cut, boxm(28, 40, VF, VF + 5, 4, 17))
    paint(cut, boxm(30, 32, VF, VF + 3, 18, 19))
    # ---- exterior openings (no enclosure)
    paint(cut, boxm(-15, -12, HUB, HUB + 3, -15, -13))                   # the knee door
    paint(cut, boxm(-18, -18, HUB, HUB + 1, 0, 0))                       # the lift cage door (iron door at x -17)
    return air, cut


# ------------------------------------------------------------------ palettes of the masses
BODY_LADDER = ["smooth_basalt", "basalt[axis=y]", "polished_basalt[axis=y]", PB, "blackstone"]


def body_spec(x, y, z):
    c = vnoise(x * 0.9 + y * 0.55, z * 0.9 - y * 0.45, 4.5, 507)
    if abs(c - 0.5) < 0.022 and hash3(x, y, z, 508) < 0.75:
        return "magma_block"
    n = fbm(x + y * 0.37, z - y * 0.21, 9.0, 501)
    hf = y / 88.0
    i = 1.3 + (n - 0.5) * 3.4 + (0.5 - hf) * 2.8
    return BODY_LADDER[max(0, min(4, int(round(i))))]


def armour_spec(x, y, z):
    """Dark iron plates with brass seams and patches of copper."""
    if y % 6 == 0 and hash3(x, y, z, 511) < 0.9:
        return BRASS
    n = fbm(x * 1.3, z * 1.3 + y, 6.0, 512)
    return COPPER if n < 0.3 else IRON


def helm_spec(x, y, z):
    if y % 5 == 0:
        return IRON
    return BRASS if fbm(x * 1.5, z * 1.5 - y, 5.0, 513) > 0.3 else COPPER


def plinth_outer(x, y, z):
    if y <= 2:
        return ROCK.pick(x, y, z)
    if y == 10:
        return BRASS if (x + z) % 9 else IRON
    if y == PTOP - 1:
        return IRON
    u = (x + z) % 11
    if u in (0, 1):
        return "polished_basalt[axis=y]"
    h = hash3(x, y, z, 521)
    if y < 7:
        return "blackstone" if h < 0.4 else PBB
    return "cracked_polished_blackstone_bricks" if h < 0.12 else PBB


def anvil_outer(x, y, z):
    if y in (9, 23):
        return BRASS
    h = hash3(x, y, z, 531)
    if y < 4:
        return "blackstone" if h < 0.5 else IRON
    return "polished_deepslate" if h < 0.18 else IRON


def hall_outer(x, y, z):
    if x in (-68, -44) and z in (-5, 27):
        return IRON
    if y in (23, 30):
        return BRASS
    if (x in (-68, -44) and (z + 1) % 6 == 0) or (z in (-5, 27) and (x + 2) % 6 == 0):
        return IRON
    return SMOKE if hash3(x, y, z, 541) > 0.1 else "red_nether_bricks"


def write_masses(bp, lab, air, cut):
    enclose = dilate(dilate(air))
    full = ((lab > 0) | enclose) & ~air & ~cut
    occupied = full | air | cut
    outer = full & dilate(~occupied, six=True)
    lining = full & dilate(air | cut, six=True) & ~outer
    M.full, M.air, M.cut = full, air, cut
    # enclosure cells outside every mass take the label of the lift cage (they are walls round passages)
    lab2 = lab.copy()
    lab2[full & (lab == 0)] = CAGE
    pts = np.argwhere(full)
    for ix, iy, iz in pts.tolist():
        x, y, z = ix + GX0, iy + GY0, iz + GZ0
        L = int(lab2[ix, iy, iz])
        o = outer[ix, iy, iz]
        li = lining[ix, iy, iz]
        if o:
            if L == BODY:
                spec = body_spec(x, y, z)
            elif L == ARMOUR:
                spec = armour_spec(x, y, z)
            elif L == HELM:
                spec = helm_spec(x, y, z)
            elif L == TRIM:
                spec = BRASS if (x + z) % 7 else IRON
            elif L == PLINTH:
                spec = PATH.pick(x, y, z) if y == PTOP else plinth_outer(x, y, z)
            elif L == ANVIL:
                spec = anvil_outer(x, y, z)
            elif L == HALL:
                spec = hall_outer(x, y, z)
            elif L == ROOF:
                spec = COPPER if hash3(x, y, z, 545) > 0.2 else BRASS
            elif L == HAMMER:
                if y == HAMMER_Y[0]:
                    spec = "iron_block"
                elif y == HAMMER_Y[1]:
                    spec = BRASS if (x + z) % 3 else GILD
                elif y in (69, 70, 79, 80):
                    spec = BRASS
                else:
                    spec = IRON if hash3(x, y, z, 552) > 0.12 else "polished_deepslate"
            elif L == HANDLE:
                spec = IRON if (x + y) % 5 == 0 else "crimson_hyphae[axis=y]"
            else:
                spec = IRON if (x + y + z) % 5 else BRASS
        elif li:
            if L in (BODY, ARMOUR, CAGE, HELM, TRIM):
                spec = "polished_basalt[axis=y]" if x % 5 == 0 else INNER.pick(x, y, z)
            elif L == ANVIL:
                spec = IRON if hash3(x, y, z, 561) > 0.25 else "polished_deepslate"
            elif L in (HALL, ROOF):
                spec = SMOKE if L == HALL else IRON
            else:
                spec = INNER.pick(x, y, z)
        else:
            spec = "blackstone" if L != ANVIL else IRON
        bp.set(x, y, z, spec)
    for ix, iy, iz in np.argwhere(air | cut).tolist():
        bp.set(ix + GX0, iy + GY0, iz + GZ0, AIR)
    return full


def solid(x, y, z):
    ix, iy, iz = x - GX0, y - GY0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= iz < SHAPE[2]:
        return bool(M.full[ix, iy, iz])
    return False


def label(x, y, z):
    ix, iy, iz = x - GX0, y - GY0, z - GZ0
    if 0 <= ix < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= iz < SHAPE[2]:
        return int(M.lab[ix, iy, iz])
    return 0


# ------------------------------------------------------------------ small parts
def lever(bp, x, y, z, facing):
    bp.set(x, y, z, f"lever[face=wall,facing={facing},powered=false]")


def railing(bp, x, y, z, facing):
    bp.set(x, y, z, f"{RAIL}[facing={facing}]")


def hang(bp, x, y, z, spec=HANG_LANT, drop=1):
    """A lamp hanging under the ceiling: chain of ``drop`` above y."""
    for k in range(1, drop + 1):
        bp.set(x, y + k, z, CHAIN)
    bp.set(x, y, z, spec)


def floor_box(bp, x0, x1, z0, z1, y, pal):
    """Pave the floor cells (y) under open air (y + 1) inside a box."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if bp.get(x, y + 1, z) == AIR and bp.get(x, y, z) not in (None, AIR):
                bp.set(x, y, z, pal(x, z) if callable(pal) else pal.pick(x, y, z))


def stair_x(bp, x, z0, z1, s, facing, spec=PBBS, fill=PBB, low=None):
    """One row of stair blocks (y = s) across z0..z1 with solid fill under it down to ``low``."""
    for z in range(z0, z1 + 1):
        bp.set(x, s, z, stair(spec, facing))
        for y in range(low if low is not None else s - 1, s):
            bp.set(x, y, z, fill)


def stair_z(bp, z, x0, x1, s, facing, spec=PBBS, fill=PBB, low=None):
    for x in range(x0, x1 + 1):
        bp.set(x, s, z, stair(spec, facing))
        for y in range(low if low is not None else s - 1, s):
            bp.set(x, y, z, fill)


def pierce(bp, x, y, z, dx, dz, h=3, w=1, fill="iron_bars", sill=IRON_STAIRS, max_steps=10):
    """A window from a room outwards: walks through solid cells until the outside and opens h x w; the outermost
    cell gets ``fill``, a sill under it."""
    px, pz = (1, 0) if dx == 0 else (0, 1)
    xx, zz = x, z
    steps = 0
    while steps < max_steps and any(solid(xx + px * s, y + dy, zz + pz * s) for s in range(w) for dy in range(h)):
        for s in range(w):
            for dy in range(h):
                bp.set(xx + px * s, y + dy, zz + pz * s, AIR)
        xx, zz = xx + dx, zz + dz
        steps += 1
    xx, zz = xx - dx, zz - dz
    f = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(dx, dz)]
    for s in range(w):
        for dy in range(h):
            bp.set(xx + px * s, y + dy, zz + pz * s, fill)
        if sill and bp.get(xx + dx + px * s, y - 1, zz + dz + pz * s) is None:
            bp.set(xx + dx + px * s, y - 1, zz + dz + pz * s, stair(sill, f, "top"))


def billet(bp, x, y, z):
    """A glowing ingot stack on the anvil."""
    bp.set(x, y, z, "magma_block")


# ------------------------------------------------------------------ the lake and the shore
def lake(bp):
    for x in range(-112, 104):
        for z in range(-82, 83):
            e = ((x + 4) / 106.0) ** 2 + (z / 80.0) ** 2
            e += 0.08 * (vnoise(x, z, 7.0, 571) - 0.5)
            if e > 1.0:
                continue
            bp.set(x, 0, z, "basalt[axis=y]" if hash01(x, z, 572) < 0.45 else "blackstone")
            bp.set(x, LAVA_Y, z, LAVA)
            if e > 0.92:
                bp.set(x, 1, z, ROCK.pick(x, 1, z))
                if hash01(x, z, 573) < 0.55:
                    bp.set(x, 2, z, ROCK.pick(x, 2, z))
    # basalt columns standing in the lake (a delta), away from the paths and the anvil
    for (cx, cz, r, h) in ((-40, 56, 2.4, 9), (-20, 62, 1.6, 6), (-58, -56, 2.6, 12), (-30, -64, 1.8, 7),
                           (30, -52, 2.2, 10), (54, -44, 1.5, 5), (66, 46, 2.5, 13), (40, 58, 1.7, 6),
                           (88, -28, 2.0, 8), (86, 30, 1.6, 6), (-6, -60, 1.5, 5), (14, 54, 2.0, 9)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.3:
                    top = h - int(d * 1.3) + int(hash01(x, z, 574) * 3)
                    for y in range(0, max(2, top)):
                        bp.set(x, y, z, "basalt[axis=y]" if hash3(x, y, z, 575) > 0.2 else "smooth_basalt")
                    if top > 3 and hash01(x, z, 576) < 0.3:
                        bp.set(x, top, z, "magma_block")


def shore(bp):
    """The south-west shore: a rock bank with the outpost; the marker where the approach starts."""
    for x in range(-114, -84):
        for z in range(34, 72):
            n = fbm(x, z, 9.0, 581)
            d = math.hypot((x + 100) / 15.0, (z - 54) / 19.0)
            if d > 1.0 + (n - 0.5) * 0.4:
                continue
            top = 3 if d < 0.85 else 2
            for y in range(0, top + 1):
                bp.set(x, y, z, ROCK.pick(x, y, z) if y < top else ("blackstone" if n > 0.4 else "basalt[axis=y]"))
            for y in range(top + 1, top + 5):
                if bp.get(x, y, z) is None:
                    bp.set(x, y, z, AIR)


def path_cells(bp, x0, x1, z0, z1, y, pal=PATH, rail_n=None, rail_s=None, rail_w=None, rail_e=None):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            bp.set(x, y, z, pal.pick(x, y, z))
            for yy in range(y + 1, y + 5):
                if bp.get(x, yy, z) in (None, LAVA):
                    bp.set(x, yy, z, AIR)


def causeway(bp):
    """Basalt causeway on piers over the lava, deck at y 3 (feet 4), parapets of dark iron, lamps."""
    y = LOW - 1
    # outpost -> north along x -100..-96, then east along z 8..12 to the gate
    segs = [(-100, -96, 10, 42), (-100, -80, 8, 12)]
    for (x0, x1, z0, z1) in segs:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, y, z, PATH.pick(x, y, z))
                for yy in range(0, y):
                    if (x + z) % 2 == 0 or yy == y - 1:
                        bp.set(x, yy, z, "basalt[axis=y]" if hash3(x, yy, z, 591) > 0.3 else "blackstone")
                    else:
                        bp.set(x, yy, z, "blackstone")
                for yy in range(y + 1, y + 6):
                    if bp.get(x, yy, z) in (None, LAVA):
                        bp.set(x, yy, z, AIR)
    # parapets
    for z in range(13, 43):
        for x in (-101, -95):
            bp.set(x, y, z, PBB)
            bp.set(x, y + 1, z, LAMP if z % 8 == 2 else IRON_WALL)
    for x in range(-101, -79):
        if not (-101 <= x <= -95):
            bp.set(x, y, 7, PBB)
            bp.set(x, y + 1, 7, LAMP if x % 8 == 0 else IRON_WALL)
            bp.set(x, y, 13, PBB)
            bp.set(x, y + 1, 13, LAMP if x % 8 == 0 else IRON_WALL)
    for x in range(-101, -94):
        bp.set(x, y, 7, PBB)
        bp.set(x, y + 1, 7, IRON_WALL)
    bp.set(-101, y, 8, PBB)
    for z in range(8, 13):
        bp.set(-101, y, z, PBB)
        bp.set(-101, y + 1, z, IRON_WALL)
    # brackets under the deck edges every 4
    for z in range(14, 42, 4):
        bp.set(-101, y - 1, z, stair(PBBS, "east", "top"))
        bp.set(-95, y - 1, z, stair(PBBS, "west", "top"))
    # the side route: from the outpost east along the south shore of the plinth to the mine adit
    for x in range(-95, -29):
        for z in range(44, 47):
            bp.set(x, y, z, PATH.pick(x, y, z) if z == 45 else PBB)
            for yy in range(0, y):
                bp.set(x, yy, z, "basalt[axis=y]" if (x + yy) % 3 else "blackstone")
            for yy in range(y + 1, y + 5):
                if bp.get(x, yy, z) in (None, LAVA):
                    bp.set(x, yy, z, AIR)
        if x % 10 == 0:
            bp.set(x, y + 1, 47, LAMP)
            bp.set(x, y, 47, PBB)
        else:
            bp.set(x, y, 47, PBB)
            bp.set(x, y + 1, 47, IRON_WALL)
    for z in range(42, 47):
        for x in range(-34, -29):
            bp.set(x, y, z, PATH.pick(x, y, z))
            for yy in range(0, y):
                bp.set(x, yy, z, "blackstone")
            for yy in range(y + 1, y + 5):
                if bp.get(x, yy, z) in (None, LAVA):
                    bp.set(x, yy, z, AIR)


def toll_arch(bp):
    """The Toll Arch over the causeway's turn: two basalt piers and a corbelled arch with a brass lintel; through it
    the titan's back and raised hammer are framed (the reveal)."""
    y = LOW
    for z in (6, 14):
        for x in (-92, -91, -90):
            for yy in range(0, y + 12):
                spec = BRASS if yy in (y + 4, y + 10) else ("polished_basalt[axis=y]" if x == -91 else PBB)
                bp.set(x, yy, z, spec)
            for zz in ((z - 1,) if z == 6 else (z + 1,)):
                for yy in range(0, y + 10):
                    bp.set(x, yy, zz, PBB if yy < y + 9 else stair(PBBS, "north" if z == 6 else "south", "top"))
    for x in (-92, -91, -90):
        for z in range(7, 14):
            k = min(z - 7, 13 - z)
            ya = y + 8 + min(k, 2)
            for yy in range(ya, y + 13):
                bp.set(x, yy, z, GILD if (yy == y + 12 and x == -91) else PBB)
            if k <= 2:
                bp.set(x, ya - 1, z, stair(PBBS, "south" if z < 10 else "north", "top"))
        bp.set(x, y + 13, 10, BRASS)
    for z in range(6, 15):
        bp.set(-91, y + 13, z, GILD if z == 10 else PBBW)
    bp.set(-91, y + 14, 10, LAMP)
    hang(bp, -91, y + 7, 10, HANG_LANT, drop=2)
    # the toll keeper's lectern and a brazier on each side
    brazier(bp, -93, y, 8)
    brazier(bp, -93, y, 12)


def outpost(bp):
    """The forgemasters' outpost on the shore: the first waystone, a weigh-house of brass and basalt, a slag cart,
    the marker of the approach at the far end."""
    f = LOW
    # paving round the waystone
    for x in range(-106, -94):
        for z in range(43, 55):
            if math.hypot(x + 100, z - 49) <= 5.6:
                bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))
                for y in range(f, f + 4):
                    bp.set(x, y, z, AIR)
    bp.set(-100, f - 1, 49, CHIS)
    bp.set(-100, f, 49, MOD["waystone"])
    for (x, z) in ((-103, 46), (-97, 46), (-103, 52), (-97, 52)):
        brazier(bp, x, f, z, soul=(x + z) % 2 == 0)
    # the weigh-house: a little hall x -110..-104, z 44..52
    x0, x1, z0, z1 = -111, -105, 44, 52
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, f - 1, z, DECK.pick(x, f - 1, z))
            for y in range(f, f + 5):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    bp.set(x, y, z, IRON if corner else (BRASS if y == f + 4 else PBB))
                else:
                    bp.set(x, y, z, AIR)
            bp.set(x, f + 5, z, IRON_SLAB if not edge else IRON)
    for z in (47, 48, 49):
        bp.set(x1, f, z, AIR)
        bp.set(x1, f + 1, z, AIR)
        bp.set(x1, f + 2, z, AIR)
    bp.set(x1, f + 3, 48, CHIS)
    for z in (46, 50):
        bp.set(x0, f + 2, z, "iron_bars")
    bp.chest(x0 + 1, f, z0 + 1, "east", loot=LOOT + "tf_outpost")
    bp.barrel_kind = "workshop"
    bp.barrel(x0 + 1, f, z1 - 1, "up")
    bp.barrel(x0 + 2, f, z1 - 1, "up")
    bp.barrel_kind = None
    bp.set(x0 + 1, f, 48, "smithing_table")
    bp.set(x0 + 1, f, 49, "anvil[facing=north]")
    bp.set(x0 + 3, f, z0 + 1, W + "mahogany_table")
    hang(bp, -108, f + 3, 48, HANG_LANT)
    # a slag cart and an ingot stack by the waystone
    for (x, z) in ((-104, 55), (-103, 55)):
        bp.set(x, f, z, IRON)
        bp.set(x, f + 1, z, "magma_block" if x == -104 else "blackstone")
    for (x, z) in ((-96, 54), (-95, 54), (-96, 55)):
        bp.set(x, f, z, "iron_block" if (x + z) % 2 else "gold_block")
    # the marker at the far end of the shore: a brass anvil-post
    for y in range(f - 1, f + 3):
        bp.set(-108, y, 66, IRON if y < f + 2 else BRASS)
    bp.set(-108, f + 3, 66, LAMP)
    for (x, z) in ((-108, 63), (-106, 60), (-104, 57)):
        bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))


# ------------------------------------------------------------------ the gate
def gate(bp):
    """The colossal portal on the plinth's west face: an arch 11 wide and 13 high recessed into the battered wall,
    filled by two iron leaves with the wicket (3 x 4) open in the middle; crucible spouts above on both sides."""
    xf = -77
    for z in range(4, 17):
        k = min(z - 4, 16 - z)
        top = LOW + 9 + min(k, 3)
        for x in range(xf - 2, xf + 1):
            for y in range(LOW, top + 1):
                bp.set(x, y, z, AIR)
        for y in range(LOW, top + 1):
            leaf = not (9 <= z <= 11 and y <= LOW + 3)
            if leaf:
                bp.set(xf + 1, y, z, BRASS if (y - LOW) % 4 == 3 or z in (4, 16) else IRON)
        bp.set(xf - 2, LOW - 1, z, PATH.pick(xf - 2, LOW - 1, z))
        bp.set(xf - 1, LOW - 1, z, PATH.pick(xf - 1, LOW - 1, z))
        bp.set(xf, LOW - 1, z, CHIS)
        # the archivolt
        for x in range(xf - 3, xf + 1):
            bp.set(x, top + 1, z, GILD if x == xf - 3 else PBB)
    for z in (3, 17):
        for y in range(0, LOW + 14):
            for x in range(xf - 4, xf + 1):
                bp.set(x, y, z, "polished_basalt[axis=y]" if x == xf - 4 else PBB)
        bp.set(xf - 4, LOW + 14, z, GILD)
        bp.set(xf - 4, LOW + 15, z, LAMP)
    # the wicket's frame and lamps
    for y in range(LOW, LOW + 4):
        bp.set(xf + 1, y, 8, CHIS)
        bp.set(xf + 1, y, 12, CHIS)
    for z in (8, 9, 10, 11, 12):
        bp.set(xf + 1, LOW + 4, z, GILD)
    hang(bp, xf - 1, LOW + 8, 10, HANG_LANT, drop=1)
    bp.wall_torch(xf - 3, LOW + 2, 5, "west")
    bp.wall_torch(xf - 3, LOW + 2, 15, "west")
    # passage lamps
    for x in (-75, -70):
        bp.set(x, LOW + 3, 10, "lantern[hanging=true,waterlogged=false]")


def crucible(bp, cx, cz, y, out, reach, fall_to):
    """A giant crucible on the plinth's rampart, tipped toward ``out`` (dx, dz): an iron bucket on a gantry, its
    spout a brass trough reaching ``reach`` blocks over the edge; a lava fall from the spout down to ``fall_to``."""
    dx, dz = out
    px, pz = -dz, dx
    # gantry: two posts and a beam across the crucible
    for s in (-4, 4):
        for yy in range(y, y + 9):
            bp.set(cx + px * s, yy, cz + pz * s, IRON if yy < y + 8 else BRASS)
    for s in range(-4, 5):
        bp.set(cx + px * s, y + 9, cz + pz * s, BRASS if s % 2 else IRON)
    # the bucket: a ring of dark iron, lava inside
    for k in range(5):
        r = 2.4 + k * 0.35
        for a in range(-4, 5):
            for b in range(-4, 5):
                d = math.hypot(a, b)
                xx, zz = cx + a, cz + b
                if d <= r + 0.4:
                    if d > r - 0.7:
                        bp.set(xx, y + 1 + k, zz, BRASS if k == 4 else IRON)
                    elif k == 0:
                        bp.set(xx, y + 1, zz, IRON)
                    elif k == 4:
                        bp.set(xx, y + 1 + k, zz, LAVA)
                    else:
                        bp.set(xx, y + 1 + k, zz, "magma_block")
    for a in range(-1, 2):
        for b in range(-1, 2):
            bp.set(cx + a, y, cz + b, IRON)
    # trunnions on the posts
    for s in (-3, 3):
        bp.set(cx + px * s, y + 4, cz + pz * s, GEAR)
    # the trough: from the lip out over the edge, lava in it, the fall from its end
    ty = y + 5
    for i in range(3, reach + 1):
        xx, zz = cx + dx * i, cz + dz * i
        bp.set(xx, ty - 1, zz, IRON)
        bp.set(xx + px, ty, zz + pz, BRASS)
        bp.set(xx - px, ty, zz - pz, BRASS)
        bp.set(xx, ty, zz, LAVA if i < reach else IRON)
        if i % 3 == 0:
            bp.set(xx, ty - 2, zz, stair(IRON_STAIRS, {(1, 0): "west", (-1, 0): "east", (0, 1): "north",
                                                      (0, -1): "south"}[out], "top"))
    fx, fz = cx + dx * (reach + 1), cz + dz * (reach + 1)
    bp.set(fx, ty, fz, LAVA)
    bp.set(fx + dx, ty, fz + dz, IRON)
    bp.set(fx + px, ty, fz + pz, IRON)
    bp.set(fx - px, ty, fz - pz, IRON)
    for yy in range(fall_to, ty):
        bp.set(fx, yy, fz, FALL)
    return fx, fz


def mould(bp, x0, x1, z0, z1, top=8):
    """An ingot mould standing in the lava: a dark iron basin on a blackstone pier, full of lava, a cooled ingot."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for y in range(0, top):
                bp.set(x, y, z, "blackstone" if y < top - 2 else IRON)
            bp.set(x, top, z, (BRASS if (x + z) % 4 == 0 else IRON) if edge else LAVA)
    # a cast ingot cooling in one corner
    bp.set(x0 + 1, top, z0 + 1, "iron_block")
    bp.set(x0 + 2, top, z0 + 1, "iron_block")


def crucibles(bp):
    # two flanking the gate (west), pouring into moulds beside the causeway
    for cz in (-4, 24):
        fx, fz = crucible(bp, -71, cz, PTOP + 1, (-1, 0), 9, 9)
        mould(bp, fx - 4, fx + 3, fz - 4, fz + 4)
    # one on the east terrace, pouring into the mould between the plinth and the anvil (under the crane)
    fx, fz = crucible(bp, -6, -30, PTOP + 1, (1, 0), 8, 9)
    mould(bp, fx - 2, fx + 6, fz - 4, fz + 5)


# ------------------------------------------------------------------ the casting hall
def casting_hall(bp):
    """Feet 4, x -66..-46, z -3..25, open into the roof (ridge at y 42). The pour basin under the hanging crucible
    (west), two glass-covered lava channels running east to the ingot moulds, furnaces fed by the bellows along the
    north wall, tie beams with chains, the clerestory."""
    f = LOW
    bp.barrel_kind = "workshop"
    floor_box(bp, -66, -46, -3, 25, f - 1, FLOOR)
    # lava channels: z 6..7 and z 15..16, from x -62 to -48, lava one below the floor under flush glass
    for zc in (6, 15):
        for x in range(-62, -47):
            for z in (zc, zc + 1):
                bp.set(x, f - 2, z, IRON)
                bp.set(x, f - 1, z, GLASS)
                bp.set(x, f - 2, z, LAVA)
                bp.set(x, f - 3, z, "blackstone")
            for z in (zc - 1, zc + 2):
                bp.set(x, f - 1, z, BRASS if x % 4 == 0 else IRON)
    # the pour basin (west end), x -64..-61, z 4..18: lava under glass, a ring of brass, the crucible above
    for x in range(-65, -60):
        for z in range(4, 19):
            edge = x in (-65, -61) or z in (4, 18)
            bp.set(x, f - 1, z, BRASS if edge else GLASS)
            if not edge:
                bp.set(x, f - 2, z, LAVA)
                bp.set(x, f - 3, z, "blackstone")
    # the glass tube of the pour: lava falls from the crucible lip into the basin (enclosed)
    for y in range(f, 22):
        for (a, b) in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            bp.set(-63 + a, y, 11 + b, GLASS if (a == 0 or b == 0) else IRON)
        bp.set(-63, y, 11, LAVA)
    bp.set(-63, f - 1, 11, LAVA)
    # the crucible: a ring hanging from the roof beams on chains
    cy = 22
    for k in range(5):
        r = 2.2 + k * 0.45
        for a in range(-5, 6):
            for b in range(-5, 6):
                d = math.hypot(a, b)
                if d <= r + 0.4:
                    if d > r - 0.7 or k == 0:
                        bp.set(-63 + a, cy + k, 11 + b, BRASS if k == 4 else IRON)
                    else:
                        bp.set(-63 + a, cy + k, 11 + b, LAVA if k == 3 else "magma_block")
    for (a, b) in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
        for y in range(cy + 5, 34):
            bp.set(-63 + a, y, 11 + b, CHAIN)
    # tie beams across the hall at y 30, with king posts; chandeliers on chains
    for x in (-64, -60, -56, -52, -48):
        for z in range(-3, 26):
            bp.set(x, 30, z, "polished_basalt[axis=z]")
        for y in range(31, hall_roof_h(x) - 1):
            bp.set(x, y, 11, "polished_basalt[axis=y]")
        bp.set(x, 29, -3, stair(PBBS, "south", "top"))
        bp.set(x, 29, 25, stair(PBBS, "north", "top"))
    for x in (-56, -50):
        for z in (4, 18):
            for y in range(24, 30):
                bp.set(x, y, z, CHAIN)
            bp.set(x, 23, z, W + "brass_chandelier")
    # the moulds at the east end: a grid of ingot pits, lava under glass, cooled ingots of iron and gold
    for (x0, z0) in ((-51, 1), (-51, 9), (-51, 18), (-47, 4), (-47, 13), (-47, 21)):
        for x in range(x0, x0 + 2):
            for z in range(z0, z0 + 3):
                if z > 24:
                    continue
                bp.set(x, f - 1, z, GLASS if (x + z) % 3 else ("iron_block" if z % 2 else "gold_block"))
                if bp.get(x, f - 1, z) == GLASS:
                    bp.set(x, f - 2, z, LAVA)
                    bp.set(x, f - 3, z, "blackstone")
    # furnaces along the north wall, fed by the bellows' brass nozzles (pipes through the wall)
    for x in range(-65, -46):
        if x in (-58, -57, -56):
            continue
        bp.set(x, f, -3, "blast_furnace[facing=south,lit=true]" if x % 3 else "furnace[facing=south,lit=true]")
        bp.set(x, f + 1, -3, PIPES if x % 3 == 0 else IRON)
        bp.set(x, f + 2, -3, stair(IRON_STAIRS, "north", "top"))
    for x in (-62, -50):
        bp.set(x, f + 3, -3, GAUGE)
    # work benches, anvils, racks on the south side
    for (x, z, b) in ((-60, 22, "anvil[facing=east]"), (-56, 22, "smithing_table"), (-52, 22, "anvil[facing=west]"),
                      (-48, 24, "grindstone[face=floor,facing=north]"), (-65, 24, "cauldron"),
                      (-64, 24, "lava_cauldron"), (-62, 24, "cauldron")):
        bp.set(x, f, z, b)
    for x in (-58, -54):
        bp.barrel(x, f, 24, "up")
        bp.barrel(x, f + 1, 24, "up")
    bp.chest(-46, f, 24, "west", loot=LOOT + "tf_casting")
    bp.spawner(-55, f, 11, MOB_CUBE)
    for (x, z) in ((-55, 10), (-56, 11), (-54, 11), (-55, 12)):
        bp.set(x, f - 1, z, CHIS)
    # wall lamps
    for z in (2, 10, 20):
        bp.set(-66, f + 4, z, "soul_wall_torch[facing=east]")
        bp.set(-46, f + 4, z, "soul_wall_torch[facing=west]")
    for x in (-62, -50):
        bp.set(x, f + 5, 25, "wall_torch[facing=north]")
    bp.barrel_kind = None
    # the clerestory: lancets in both gable walls (north and south), high up
    for z, dz in ((-5, -1), (27, 1)):
        for x in (-61, -56, -51):
            for y in range(31, 37):
                bp.set(x, y, z - dz, AIR)
                bp.set(x, y, z, "orange_stained_glass_pane" if y < 36 else CHIS)
    # the walls above the plinth: buttresses at the corners of the hall
    for (x, z) in ((-69, -6), (-69, 28), (-43, -6), (-43, 28)):
        for y in range(PTOP + 1, 33):
            bp.set(x, y, z, IRON if y % 5 else BRASS)
    # chimneys on the hall roof (two), smoking
    for (cx, cz) in ((-62, 0), (-50, 22)):
        top = hall_roof_h(cx) + 7
        for y in range(hall_roof_h(cx) - 2, top + 1):
            for x in range(cx - 1, cx + 2):
                for z in range(cz - 1, cz + 2):
                    if x == cx and z == cz:
                        bp.set(x, y, z, AIR if y > hall_roof_h(cx) - 1 else SMOKE)
                    else:
                        bp.set(x, y, z, BRASS if y in (top - 1, top - 5) else SMOKE)
        bp.set(cx, hall_roof_h(cx), cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        bp.set(cx, hall_roof_h(cx) - 1, cz, "hay_block[axis=y]")


def hall_roof(bp):
    """Copper roof tiles: stairs on the slopes of the casting hall, a brass ridge."""
    for x in range(-69, -42):
        h = hall_roof_h(x)
        for z in range(-6, 29):
            if x == -56:
                bp.set(x, h, z, BRASS)
                continue
            bp.set(x, h, z, stair(COPPER_STAIRS, "east" if x < -56 else "west"))
        for z in (-6, 28):           # verge
            bp.set(x, h, z, stair(COPPER_STAIRS, "east" if x < -56 else "west") if x != -56 else BRASS)
    for z in range(-6, 29, 4):
        bp.set(-56, hall_roof_h(-56) + 1, z, IRON_WALL)
    # eaves: a course of iron under the roof edge
    for z in range(-6, 29):
        bp.set(-70, 30, z, stair(IRON_STAIRS, "west", "top"))
        bp.set(-42, 30, z, stair(IRON_STAIRS, "east", "top"))


# ------------------------------------------------------------------ the bellows chambers
def bellows(bp):
    """Feet 4, x -66..-46, z -34..-8: two giant leather bellows (west and east) between dark oak boards, their
    brass nozzles through the south wall to the casting hall's furnaces; the aisle between them; the yokes and the
    great lever beam overhead."""
    f = LOW
    bp.barrel_kind = "workshop"
    floor_box(bp, -66, -46, -34, -8, f - 1, FLOOR)
    for (x0, x1) in ((-65, -60), (-52, -47)):
        # the bellows: a wedge, narrow at the nozzle (south) and tall at the back (north)
        for z in range(-30, -11):
            t = (z + 30) / 18.0                 # 0 at the back, 1 at the nozzle
            h = int(round(7 - 4 * t))
            for x in range(x0, x1 + 1):
                for y in range(f, f + h + 1):
                    edge_x = x in (x0, x1)
                    if y == f or y == f + h:
                        bp.set(x, y, z, "dark_oak_planks" if y == f else "stripped_dark_oak_log[axis=z]")
                    elif edge_x:
                        bp.set(x, y, z, LEATHER if (z % 3) else "brown_wool")
                    else:
                        bp.set(x, y, z, LEATHER)
        # the nozzle and the pipe into the wall
        xc = (x0 + x1) // 2
        for z in range(-11, -7):
            bp.set(xc, f + 2, z, BRASS if z < -9 else PIPES)
            bp.set(xc + 1, f + 2, z, BRASS if z < -9 else PIPES)
        for z in (-8, -7, -6, -5, -4):
            bp.set(xc, f + 2, z, PIPES)
        # the yoke: a beam from the bellows' lid up to the lever, chains
        for y in range(f + 8, 15):
            bp.set(xc, y, -26, CHAIN)
        bp.set(xc, f + 8, -26, IRON)
        # a gauge and a pressure valve at the back
        bp.set(x0, f + 1, -32, GAUGE)
        bp.set(x1, f + 1, -32, GEAR)
    # the great beam across both bellows, on its fulcrum post in the aisle
    for x in range(-65, -46):
        bp.set(x, 14, -26, "stripped_dark_oak_log[axis=x]")
    for y in range(f, 14):
        bp.set(-56, y, -33, IRON if y % 3 else BRASS)
    # crates of charcoal, coal heaps
    for (x, z) in ((-65, -34), (-64, -34), (-65, -33), (-47, -34), (-48, -34)):
        bp.set(x, f, z, "coal_block" if (x + z) % 2 else "blackstone")
    bp.barrel(-58, f, -34, "up")
    bp.barrel(-54, f, -34, "up")
    bp.chest(-46, f, -33, "west", loot=LOOT + "tf_bellows")
    bp.spawner(-56, f, -19, MOB_HOUND)
    for z in (-28, -20, -12):
        hang(bp, -56, 12, z, HANG_LANT, drop=2)
    for z in (-30, -15):
        bp.set(-66, f + 4, z, "soul_wall_torch[facing=east]")
        bp.set(-46, f + 4, z, "soul_wall_torch[facing=west]")
    bp.barrel_kind = None


def grand_stair(bp):
    """Two flights east along z -31..-29 from the bellows (feet 4) to the plinth top (feet 18), a landing at 11;
    a balustrade round the open stairwell on the terrace."""
    for i, x in enumerate(range(-42, -35)):
        stair_x(bp, x, -31, -29, LOW + i, "east", low=LOW - 1)
    for x in range(-35, -32):
        for z in range(-31, -28):
            bp.set(x, LOW + 6, z, PBB)
            for y in range(LOW - 1, LOW + 6):
                bp.set(x, y, z, PBB)
    for i, x in enumerate(range(-32, -25)):
        stair_x(bp, x, -31, -29, LOW + 7 + i, "east", low=LOW + 5)
    for x in range(-45, -42):
        for z in range(-31, -28):
            bp.set(x, LOW - 1, z, CHIS)
    # the stairwell where it breaks through the plinth top: balustrade on its north and south sides
    for x in range(-32, -25):
        for z in (-32, -28):
            if bp.get(x, PTOP + 1, z) in (None, AIR):
                bp.set(x, PTOP + 1, z, PBBW)
    hang(bp, -34, LOW + 10, -30, HANG_LANT, drop=1)
    bp.set(-44, LOW + 3, -32, "soul_wall_torch[facing=south]")


# ------------------------------------------------------------------ the lift (shortcut) and its lobby
def lift(bp):
    """The spine lift: a 3 x 3 shaft from the plinth lobby (feet 4) to the smelting hall floor (y 57), a ladder and a
    scaffolding column; the iron doors at the lobby and at the hub cage open from the lift side only."""
    for y in range(LOW, SME):
        bp.set(-20, y, -1, "ladder[facing=south,waterlogged=false]")
        bp.set(-21, y, 1, SCAF)
    # the hub landing: a ledge inside the cage and the iron door east (lever inside)
    for z in (-1, 0, 1):
        bp.set(-19, PTOP, z, IRON)
    bp.set(-18, PTOP, 0, IRON)
    bp.door(-17, HUB, 0, "west", wood="iron")
    lever(bp, -18, HUB + 1, 1, "west")
    bp.set(-17, HUB + 2, 0, BRASS)
    for z in (-1, 1):
        bp.set(-17, HUB, z, IRON)
        bp.set(-17, HUB + 1, z, IRON)
    bp.set(-16, PTOP, 0, PATH.pick(-16, PTOP, 0))
    # the lobby: the iron door west to the casting hall corridor (lever in the lobby)
    f = LOW
    floor_box(bp, -24, -16, -4, 4, f - 1, FLOOR)
    for z in range(-1, 2):
        for y in range(f, f + 4):
            bp.set(-25, y, z, PBB)
    bp.door(-25, f, 0, "east", wood="iron")
    lever(bp, -24, f + 1, 1, "east")
    bp.set(-25, f + 2, 0, CHIS)
    bp.set(-26, f - 1, 0, CHIS)
    hang(bp, -17, f + 4, -3, HANG_SOUL)
    hang(bp, -17, f + 4, 3, HANG_SOUL)
    bp.set(-16, f, -4, "barrel[facing=up,open=false]")
    bp.set(-16, f, 4, GEAR)
    # the corridor from the casting hall
    floor_box(bp, -45, -26, -1, 1, f - 1, PATH)
    for x in (-40, -32):
        bp.set(x, f + 3, 0, "lantern[hanging=true,waterlogged=false]")
    # the top: a railing round the shaft mouth in the smelting hall, gears and chains of the winding gear
    for x in range(-22, -17):
        for z in (-2, 2):
            if bp.get(x, SME, z) == AIR:
                railing(bp, x, SME, z, "north" if z < 0 else "south")
    for z in range(-1, 2):
        if bp.get(-22, SME, z) == AIR:
            railing(bp, -22, SME, z, "west")
    for y in range(SME + 4, SME + 10):
        bp.set(-20, y, 0, CHAIN)
    bp.set(-20, SME + 10, 0, GEAR)


def lift_cage(bp):
    """The cage of the lift between the titan's legs: glass windows in the iron walls, brass bands."""
    for y in range(PTOP + 3, 48, 1):
        for (x, z) in ((-23, 0), (-17, 0), (-20, -3), (-20, 3)):
            if label(x, y, z) == 0 and solid(x, y, z) and y % 6 not in (0, 1):
                bp.set(x, y, z, "orange_stained_glass_pane")
        if y % 6 == 0:
            for x in range(-23, -16):
                for z in (-3, 3):
                    if label(x, y, z) == 0 and solid(x, y, z):
                        bp.set(x, y, z, BRASS)
            for z in range(-3, 4):
                for x in (-23, -17):
                    if label(x, y, z) == 0 and solid(x, y, z):
                        bp.set(x, y, z, BRASS)


# ------------------------------------------------------------------ the slag mine (optional)
def slag_mine(bp):
    """The drift from the casting hall and the adit from the south shore meet in the slag cavern: heaps of slag,
    ore veins in the walls, a winch over a dump pit (lava under bars), rails; a 1-wide squeeze to the old drift."""
    f = LOW
    bp.barrel_kind = "workshop"
    for (x0, x1, z0, z1) in ((-50, -48, 26, 31), (-50, -14, 30, 32), (-32, -30, 33, 43)):
        floor_box(bp, x0, x1, z0, z1, f - 1, ROCK)
    for x in range(-49, -14):
        bp.set(x, f, 31, f"rail[shape=east_west,waterlogged=false]") if x % 7 else None
    for x in range(-48, -14, 6):
        for z in (30, 32):
            for y in range(f, f + 3):
                bp.set(x, y, z, "stripped_crimson_stem[axis=y]")
        for z in range(30, 33):
            bp.set(x, f + 3, z, "stripped_crimson_stem[axis=z]")
    for x in (-44, -26):
        hang(bp, x, f + 2, 31, HANG_LANT, drop=1)
    floor_box(bp, -14, 12, 8, 29, f - 1, ROCK)
    # slag heaps (blackstone, basalt, magma) along the walls
    for (cx, cz, r) in ((-10, 12, 3.5), (8, 12, 3.0), (8, 26, 3.5), (-9, 26, 2.5)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r:
                    for y in range(f, f + int((r - d) * 1.4) + 1):
                        h = hash3(x, y, z, 611)
                        bp.set(x, y, z, "magma_block" if h < 0.12 else ("blackstone" if h < 0.55 else
                                                                         "basalt[axis=y]"))
    # ore veins in the walls
    for x in range(-15, 14):
        for z in range(7, 31):
            for y in range(f, f + 9):
                b = bp.get(x, y, z)
                if b and b not in (AIR,) and solid(x, y, z) and hash3(x, y, z, 612) < 0.07:
                    near_air = any(bp.get(x + a, y, z + c) == AIR for a, c in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if near_air:
                        bp.set(x, y, z, "nether_gold_ore" if hash3(x, y, z, 613) < 0.7 else "nether_quartz_ore")
    # the dump pit with the winch: lava two below, bars over it
    for x in range(-2, 3):
        for z in range(17, 22):
            edge = x in (-2, 2) or z in (17, 21)
            bp.set(x, f - 1, z, IRON if edge else "iron_bars")
            if not edge:
                bp.set(x, f - 2, z, AIR)
                bp.set(x, f - 3, z, LAVA)
                bp.set(x, f - 4, z, "blackstone")
    for (x, z) in ((-3, 16), (3, 16), (-3, 22), (3, 22)):
        for y in range(f, f + 8):
            bp.set(x, y, z, "stripped_crimson_stem[axis=y]")
    for x in range(-3, 4):
        bp.set(x, f + 8, 16, "stripped_crimson_stem[axis=x]")
        bp.set(x, f + 8, 22, "stripped_crimson_stem[axis=x]")
    for z in range(16, 23):
        bp.set(0, f + 8, z, "stripped_crimson_stem[axis=z]")
    for y in range(f + 3, f + 8):
        bp.set(0, y, 19, CHAIN)
    bp.set(0, f + 2, 19, "lava_cauldron")
    # rails across the cavern, a cart of ore
    for x in range(-12, 11):
        if not (-3 <= x <= 3):
            bp.set(x, f, 14, "rail[shape=east_west,waterlogged=false]")
    bp.chest(10, f, 18, "west", loot=LOOT + "tf_mine")
    bp.barrel(10, f, 20, "up")
    bp.barrel(-13, f, 18, "up")
    bp.spawner(-6, f, 19, MOB_SENTRY)
    for (x, z) in ((-8, 19), (-6, 21), (-6, 17)):
        bp.set(x, f - 1, z, IRON)
    for (x, z) in ((-12, 9), (10, 9), (-12, 28), (10, 28)):
        hang(bp, x, f + 7, z, HANG_LANT, drop=1)
    # the adit: a brass-framed door out to the south shore
    for y in range(f, f + 4):
        bp.set(-33, y, 43, IRON)
        bp.set(-29, y, 43, IRON)
    for x in range(-33, -28):
        bp.set(x, f + 4, 43, BRASS)
    bp.set(-31, f + 3, 42, "lantern[hanging=true,waterlogged=false]")
    # the old drift (secret): reached through a 1-wide squeeze behind a slag heap
    floor_box(bp, -10, -3, 32, 36, f - 1, ROCK)
    bp.chest(-9, f, 34, "east", loot=LOOT + "tf_drift")
    for (x, z) in ((-4, 33), (-4, 35)):
        bp.set(x, f, z, "ancient_debris" if z == 33 else "gilded_blackstone")
    bp.set(-6, f + 3, 34, "lantern[hanging=true,waterlogged=false]")
    bp.set(-6, f + 4, 34, CHAIN)
    bp.barrel_kind = None


# ------------------------------------------------------------------ the plinth top: terraces (hub)
def terraces(bp):
    """The plinth top (feet 18): the north terrace where the grand stair arrives, the east terrace (the hub) before
    the titan's knee with the waystone, the parapet round the plinth's edge; headroom air over the walks."""
    y = PTOP
    top2d = plinth_mask2d()
    for ix, iz in np.argwhere(top2d).tolist():
        x, z = ix + GX0, iz + GZ0
        if bp.get(x, y + 1, z) is None:
            for yy in range(y + 1, y + 5):
                if bp.get(x, yy, z) is None:
                    bp.set(x, yy, z, AIR)
    # parapet round the edge (cells of the top mask with a neighbour outside)
    for ix, iz in np.argwhere(top2d).tolist():
        x, z = ix + GX0, iz + GZ0
        edge = any(not (0 <= ix + a < top2d.shape[0] and 0 <= iz + c < top2d.shape[1]) or
                   not top2d[ix + a, iz + c] for a, c in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and bp.get(x, y + 1, z) == AIR:
            if -10 <= x <= -4 and -34 <= z <= -26:
                continue                      # the crucible spout passes here
            bp.set(x, y + 1, z, LAMP if (x * 3 + z) % 13 == 0 else PBBW)
    # the hub on the east terrace: the waystone on a brass dais, braziers
    wx, wz = -8, -4
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            bp.set(x, y, z, GILD if (x + z) % 2 else CHIS)
    bp.set(wx, y + 1, wz, MOD["waystone"])
    brazier(bp, -4, y + 1, -8)
    brazier(bp, -4, y + 1, 0, soul=True)
    # the north terrace: the ore yard (heaps of ore, a crane post), benches
    for (cx, cz) in ((-48, -36), (-40, -36)):
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 1, cz + 2):
                if bp.get(x, y + 1, z) == AIR and math.hypot(x - cx, (z - cz) * 1.4) <= 2.3:
                    bp.set(x, y + 1, z, "nether_gold_ore" if hash01(x, z, 621) < 0.4 else "blackstone")
    for yy in range(y + 1, y + 10):
        bp.set(-14, yy, -36, IRON if yy < y + 9 else BRASS)
    for x in range(-14, -6):
        bp.set(x, y + 10, -36, IRON if x % 2 else BRASS)
    for yy in range(y + 4, y + 10):
        bp.set(-7, yy, -36, CHAIN)
    bp.set(-7, y + 3, -36, "lava_cauldron")
    bp.barrel(-16, y + 1, -36, "up")
    bp.barrel(-16, y + 1, -37, "up")
    # lamps along the walks
    for (x, z) in ((-36, -34), (-26, -34), (-12, -24), (-12, -12), (-2, 4), (-36, -24)):
        if bp.get(x, y + 1, z) == AIR:
            bp.set(x, y + 1, z, IRON)
            bp.set(x, y + 2, z, IRON_WALL)
            bp.set(x, y + 3, z, LAMP)


def turret(bp, cx, cz, top, r=4):
    """A round corner turret of the plinth, solid, with a corbelled crown and a copper cone."""
    for y in range(0, top + 1):
        rr = r + (1 if y < 4 else 0) + (1 if y >= top - 1 else 0)
        for x in range(cx - rr - 1, cx + rr + 2):
            for z in range(cz - rr - 1, cz + rr + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.35:
                    if y in (10, top - 2):
                        spec = BRASS if d > rr - 1 else "blackstone"
                    elif d > rr - 1:
                        spec = plinth_outer(x, y, z) if y != PTOP - 1 else IRON
                    else:
                        spec = "blackstone"
                    bp.set(x, y, z, spec)
    for k in range(r + 2):
        rr = r + 1 - k
        y = top + 1 + k * 2
        for x in range(cx - rr - 1, cx + rr + 2):
            for z in range(cz - rr - 1, cz + rr + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= rr + 0.35:
                    bp.set(x, y, z, COPPER if d > rr - 1 else IRON)
                    bp.set(x, y + 1, z, COPPER if d > rr - 1.5 else IRON)
    # fill the pockets between the round turret and the battered plinth (no sealed slots)
    R = r + 4

    def bs(x, y, z):
        return bp.get(x, y, z) not in (None, AIR, LAVA)

    for _ in range(2):
        fills = []
        for y in range(0, top + 1):
            for x in range(cx - R, cx + R + 1):
                for z in range(cz - R, cz + R + 1):
                    if bs(x, y, z):
                        continue
                    hits = 0
                    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if any(bs(x + dx * k, y, z + dz * k) for k in range(1, 5)):
                            hits += 1
                    if hits >= 3 and bs(x, y + 1, z) or hits == 4:
                        fills.append((x, y, z))
        for (x, y, z) in fills:
            bp.set(x, y, z, "blackstone" if y < top - 2 else COPPER)
    bp.set(cx, top + 2 * (r + 2) + 1, cz, IRON_WALL)
    bp.set(cx, top + 2 * (r + 2) + 2, cz, LAMP)
    for a in range(0, 360, 45):
        t = math.radians(a)
        x, z = int(round(cx + math.cos(t) * (r + 1))), int(round(cz + math.sin(t) * (r + 1)))
        bp.set(x, top + 1, z, LAMP if a % 90 == 0 else IRON_WALL)


def plinth_buildings(bp):
    """On the plinth top: the coal store (north-west), the engine house and its flywheel (south), corner turrets."""
    y = PTOP
    # ---- the coal store: x -68..-52, z -39..-24, a door east; a flat iron roof with three glazed lanterns
    x0, x1, z0, z1 = -68, -52, -39, -24
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for yy in range(y + 1, y + 9):
                if edge:
                    corner = x in (x0, x1) and z in (z0, z1)
                    pil = (x - x0) % 8 == 0 or (z - z0) % 5 == 0
                    bp.set(x, yy, z, IRON if corner or (pil and yy < y + 8) else
                           (BRASS if yy == y + 8 else (SMOKE if hash3(x, yy, z, 651) > 0.1 else "red_nether_bricks")))
                else:
                    bp.set(x, yy, z, AIR)
            bp.set(x, y + 9, z, IRON)
            if not edge:
                bp.set(x, y, z, FLOOR.pick(x, y, z))
    for (lx, lz) in ((-64, -31), (-60, -31), (-56, -31)):
        for x in range(lx - 1, lx + 2):
            for z in range(lz - 4, lz + 5):
                edge = x in (lx - 1, lx + 1) or z in (lz - 4, lz + 4)
                bp.set(x, y + 9, z, AIR if not edge else IRON)
                bp.set(x, y + 10, z, ("orange_stained_glass_pane" if not (x in (lx - 1, lx + 1) and z in (lz - 4, lz + 4))
                                      else IRON) if edge else AIR)
                bp.set(x, y + 11, z, IRON_SLAB + "[type=bottom,waterlogged=false]")
    for x in range(x0 - 1, x1 + 2):
        for z in (z0 - 1, z1 + 1):
            bp.set(x, y + 8, z, stair(IRON_STAIRS, "south" if z < z0 else "north", "top"))
    for z in range(z0, z1 + 1):
        bp.set(x0 - 1, y + 8, z, stair(IRON_STAIRS, "east", "top"))
        bp.set(x1 + 1, y + 8, z, stair(IRON_STAIRS, "west", "top"))
    for z in (-32, -31, -30):
        for yy in range(y + 1, y + 4):
            bp.set(x1, yy, z, AIR)
    bp.set(x1, y + 4, -31, CHIS)
    bp.barrel_kind = "workshop"
    for (cx, cz) in ((-64, -36), (-57, -36), (-64, -27)):
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                d = math.hypot(x - cx, z - cz)
                if d <= 2.4:
                    for yy in range(y + 1, y + 1 + int((2.6 - d) * 1.2) + 1):
                        bp.set(x, yy, z, "coal_block" if hash3(x, yy, z, 652) > 0.3 else "blackstone")
    for z in (-26, -25):
        bp.barrel(-55, y + 1, z, "up")
        bp.barrel(-54, y + 1, z, "up")
    bp.barrel_kind = None
    for (hx, hz) in ((-60, -27), (-60, -35)):
        hang(bp, hx, y + 6, hz, HANG_LANT, drop=2)
    # ---- the engine house: x -40..-26, z 27..37, open to its gable roof (ridge along x at z 32)
    x0, x1, z0, z1 = -40, -26, 27, 37

    def rh(z):
        return y + 10 + min(z - (z0 - 1), (z1 + 1) - z)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            top = y + 9 if not (x in (x0, x1)) else rh(z) - 1
            for yy in range(y + 1, top + 1):
                if edge:
                    bp.set(x, yy, z, IRON if (x in (x0, x1) and z in (z0, z1)) or (x - x0) % 7 == 0 and z in (z0, z1)
                           else (BRASS if yy == y + 6 else SMOKE))
                else:
                    bp.set(x, yy, z, AIR)
            if not edge:
                bp.set(x, y, z, FLOOR.pick(x, y, z))
                for yy in range(y + 10, rh(z) - 1):
                    bp.set(x, yy, z, AIR)
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            h = rh(z)
            if z == 32:
                bp.set(x, h, z, BRASS)
            else:
                bp.set(x, h, z, stair(COPPER_STAIRS, "south" if z < 32 else "north"))
            if x0 <= x <= x1 and z0 <= z <= z1:
                bp.set(x, h - 1, z, IRON)
    for z in (z0 - 1, z1 + 1):
        for x in range(x0 - 1, x1 + 2):
            bp.set(x, y + 9, z, stair(IRON_STAIRS, "north" if z < z0 else "south", "top"))
    for x in (-34, -33, -32):
        for yy in range(y + 1, y + 5):
            bp.set(x, yy, z0, AIR)
    for x in (-35, -31):
        for yy in range(y + 1, y + 5):
            bp.set(x, yy, z0, BRASS if yy == y + 4 else IRON)
    for x in range(-35, -30):
        bp.set(x, y + 5, z0, GILD)
    # the engine: a copper boiler on saddles, the cylinder and its piston rod, the crank through the east wall
    for x in range(-39, -31):
        for z in range(29, 36):
            for yy in range(y + 1, y + 8):
                if math.hypot(z - 32, yy - (y + 4)) <= 2.6:
                    bp.set(x, yy, z, COPPER if x not in (-39, -32) else BRASS)
        bp.set(x, y + 1, 29, IRON) if x % 3 == 0 else None
    for yy in range(y + 1, y + 6):
        bp.set(-30, yy, 32, IRON)
        bp.set(-29, yy, 32, IRON)
    for x in range(-31, -26):
        bp.set(x, y + 8, 32, IRON if x % 2 else BRASS)
    bp.set(-28, y + 6, 32, GAUGE)
    bp.set(-38, y + 1, 36, "furnace[facing=north,lit=true]")
    bp.set(-36, y + 1, 36, "furnace[facing=north,lit=true]")
    hang(bp, -33, y + 12, 30, HANG_LANT, drop=2)
    hang(bp, -33, y + 12, 34, HANG_LANT, drop=2)
    # the boiler's chimney
    for yy in range(y + 8, y + 26):
        for x in range(-39, -36):
            for z in range(34, 37):
                if (x, z) == (-38, 35):
                    bp.set(x, yy, z, AIR if yy > y + 8 else SMOKE)
                else:
                    bp.set(x, yy, z, BRASS if yy in (y + 20, y + 24) else SMOKE)
    bp.set(-38, y + 8, 35, "hay_block[axis=y]")
    bp.set(-38, y + 9, 35, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # the flywheel: a vertical ring (plane x-y) east of the house, its axle through the wall
    fx, fy, fz = -17, y + 10, 32
    R = 8
    for x in range(fx - R - 1, fx + R + 2):
        for yy in range(fy - R - 1, fy + R + 2):
            d = math.hypot(x - fx, yy - fy)
            ang = math.degrees(math.atan2(yy - fy, x - fx)) % 45
            for z in (fz, fz + 1):
                if R - 1.2 < d <= R + 0.4:
                    bp.set(x, yy, z, IRON if z == fz else BRASS)
                elif d <= 1.5:
                    bp.set(x, yy, z, BRASS)
                elif d < R - 1.2 and (ang < 6 or ang > 39) and z == fz:
                    bp.set(x, yy, z, IRON)
    for x in range(-25, -17):
        bp.set(x, fy, fz, IRON)
    for z in (fz - 1, fz + 2):
        for yy in range(y + 1, fy):
            bp.set(fx, yy, z, IRON if yy % 3 else BRASS)
        bp.set(fx, fy, z, GEAR)
    # ---- corner turrets of the plinth (west corners, north-east)
    turret(bp, -71, -37, 30)
    turret(bp, -71, 35, 28)
    turret(bp, -3, -37, 26, r=3)


# ------------------------------------------------------------------ the titan's interior
def knee_hall(bp):
    f = HUB
    floor_box(bp, -23, -15, -18, -10, f - 1, FLOOR)
    hang(bp, -19, f + 4, -14, HANG_LANT, drop=1)
    # the knee door: a brass frame
    for y in range(f, f + 4):
        for z in (-16, -12):
            bp.set(-13, y, z, BRASS if y == f + 3 else IRON)
    for z in range(-16, -11):
        bp.set(-13, f + 4, z, GILD)
    bp.set(-12, f - 1, -14, CHIS)


def newel_stair(bp):
    parts, c_top, f_top = M.newel
    for cells, core, f0 in parts:
        for (x, z), (f, fc, _) in cells.items():
            if fc:
                bp.set(x, f - 1, z, stair(PBBS, fc))
            else:
                bp.set(x, f - 1, z, PBB if hash01(x, z, 631) < 0.8 else CHIS)
            bp.set(x, f - 2, z, PBB)
            if f - 2 - f0 < 3:
                for y in range(f0 - 1, f - 1):
                    bp.set(x, y, z, PBB)
        cx0, cz0, cx1, cz1 = core
        for x in range(cx0, cx1 + 1):
            for z in range(cz0, cz1 + 1):
                for y in range(f0 - 1, f0 + 12):
                    bp.set(x, y, z, "polished_basalt[axis=y]" if (x + z) % 2 else BRASS)
    # lamps on the core
    for y in range(HUB + 4, BAR + 4, 6):
        bp.set(-27, y, -12, LAMP)


def barracks(bp):
    """The forgemasters' barracks in the pelvis (feet 40): rows of bunks (wool on dark oak), lockers (barrels), the
    mess table under a chandelier, the spine lift's column, the stair up to the armoury."""
    f = BAR
    bp.barrel_kind = "military"
    floor_box(bp, -40, -24, -16, 11, f - 1, FLOOR)
    # bunks along the north and south sides
    for x in range(-38, -27, 3):
        for z in (-9, 4):
            if bp.get(x, f, z) == AIR and bp.get(x, f, z + 1) == AIR:
                bp.set(x, f, z, "dark_oak_planks")
                bp.set(x, f, z + 1, "red_wool")
                if bp.get(x, f + 2, z) == AIR:
                    bp.set(x, f + 2, z, "dark_oak_slab[type=bottom,waterlogged=false]")
                    bp.set(x, f + 2, z + 1, "dark_oak_slab[type=bottom,waterlogged=false]")
                for y in (f, f + 1, f + 2):
                    if bp.get(x - 1, y, z) == AIR:
                        bp.set(x - 1, y, z, "dark_oak_fence")
    # mess table
    for x in range(-37, -31):
        bp.set(x, f, -1, W + "mahogany_table")
        bp.set(x, f, 1, W + "mahogany_table")
    for x in range(-37, -31, 2):
        bp.set(x, f, -2, stair("dark_oak_stairs", "south"))
        bp.set(x, f, 2, stair("dark_oak_stairs", "north"))
    bp.set(-34, f + 1, 0, LANT)
    chandelier(bp, -34, f + 5, 0, drop=1)
    for z in (-6, 6):
        if bp.get(-39, f, z) == AIR:
            bp.barrel(-39, f, z, "east")
    bp.chest(-26, f, -9, "west", loot=LOOT + "tf_barracks")
    bp.spawner(-29, f, 3, MOB_GUARD)
    bp.spawner(-27, f, 5, "brasshaven:slag_golem")
    for (x, z) in ((-38, -4), (-38, 4), (-26, 5)):
        if bp.get(x, f + 3, z) == AIR:
            hang(bp, x, f + 3, z, HANG_LANT, drop=1) if bp.get(x, f + 5, z) not in (None, AIR) else None
    # the stair up to the armoury (z 7..9, east)
    for i, x in enumerate(range(-33, -24)):
        stair_x(bp, x, 7, 9, BAR + i, "east", low=BAR - 1)
    bp.barrel_kind = None


def armoury(bp):
    """The armoury in the belly (feet 49): racks of arms (iron bars and walls), armour stands of blocks, anvils and
    grindstones, the quartermaster's desk, the stair west up into the smelting hall."""
    f = ARM
    bp.barrel_kind = "military"
    floor_box(bp, -32, -14, -11, 11, f - 1, PATH)
    stair_x(bp, -25, 7, 9, f - 1, "east")                 # the top step of the stair from the barracks
    # stairwell railing round the stair from the barracks (x -33..-25, z 7..9)
    for x in range(-30, -24):
        if bp.get(x, f, 6) == AIR:
            railing(bp, x, f, 6, "north")
        if bp.get(x, f, 10) == AIR:
            railing(bp, x, f, 10, "south")
    # weapon racks: along the south wall
    for x in range(-22, -14, 2):
        for z in (9, 10):
            if bp.get(x, f, z) == AIR and bp.get(x, f, z + 1) not in (None, AIR):
                bp.set(x, f, z, IRON_WALL)
                bp.set(x, f + 1, z, "iron_bars")
                bp.set(x, f + 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
                break
    # armour "stands": brass helms on iron posts in the middle
    for (x, z) in ((-27, -2), (-27, 2), (-23, -2), (-23, 2)):
        bp.set(x, f, z, IRON_WALL)
        bp.set(x, f + 1, z, BRASS)
        bp.set(x, f + 2, z, "brasshaven:brass_plating_slab[type=bottom,waterlogged=false]")
    for (x, z, b) in ((-30, -3, "anvil[facing=north]"), (-30, 3, "grindstone[face=floor,facing=north]"),
                      (-17, -4, "smithing_table"), (-17, 4, "fletching_table")):
        if bp.get(x, f, z) == AIR:
            bp.set(x, f, z, b)
    bp.chest(-16, f, 0, "west", loot=LOOT + "tf_armoury")
    bp.spawner(-25, f, -5, MOB_WSKEL)
    for z in (-4, 4):
        if bp.get(-31, f, z) == AIR:
            bp.barrel(-31, f, z, "east")
    chandelier(bp, -25, f + 6, 0, drop=1)
    # the stair west up into the smelting hall (z -9..-7)
    for i, x in enumerate(range(-18, -27, -1)):
        stair_x(bp, x, -9, -7, ARM + i, "west", low=ARM - 1)
    for x in range(-24, -17):
        if bp.get(x, f, -6) == AIR:
            railing(bp, x, f, -6, "south")
    bp.barrel_kind = None


def smelting_hall(bp):
    """The smelting hall in the titan's back (feet 58): a row of blast furnaces under hoods that rise into the three
    chimneys of the back, ore chutes, the slag runnel under glass, the shaft mouth of the spine lift."""
    f = SME
    bp.barrel_kind = "workshop"
    floor_box(bp, -31, -13, -12, 12, f - 1, FLOOR)
    # the slag runnel along the hall (z 4..5), lava under glass
    for x in range(-29, -14):
        for z in (4, 5):
            if bp.get(x, f - 1, z) not in (None, AIR) and bp.get(x, f, z) == AIR:
                bp.set(x, f - 1, z, GLASS)
                bp.set(x, f - 2, z, LAVA)
                bp.set(x, f - 3, z, "blackstone")
    # blast furnaces in a row along the north side, hoods above
    for x in range(-29, -15, 3):
        for z in (-10, -9):
            if bp.get(x, f, z) == AIR:
                bp.set(x, f, z, "blast_furnace[facing=south,lit=true]" if z == -9 else IRON)
                bp.set(x, f + 1, z, IRON if z == -10 else stair(IRON_STAIRS, "north", "top"))
    for x in range(-30, -14):
        for z in (-11, -10):
            if bp.get(x, f + 4, z) == AIR:
                bp.set(x, f + 4, z, stair(IRON_STAIRS, "north", "top") if z == -10 else IRON)
    # ore chutes from the ceiling: copper pipes ending over hoppers
    for x in (-27, -21):
        for y in range(f + 2, f + 10):
            if bp.get(x, y, 9) == AIR:
                bp.set(x, y, 9, PIPES)
        bp.set(x, f + 1, 9, "hopper[enabled=true,facing=down]")
        bp.set(x, f, 9, "barrel[facing=up,open=false]")
    bp.chest(-14, f, 7, "west", loot=LOOT + "tf_smelting")
    bp.spawner(-24, f, 0, MOB_BLAZE)
    for (x, z) in ((-24, -1), (-25, 0), (-23, 0)):
        bp.set(x, f - 1, z, CHIS)
    for x in (-28, -18):
        chandelier(bp, x, f + 8, 2, drop=2) if bp.get(x, f + 9, 2) not in (None, AIR) else None
    for z in (-6, 6):
        if bp.get(-30, f + 3, z) == AIR:
            bp.set(-30, f + 3, z, "soul_wall_torch[facing=east]")
    # the stair to the yoke (2 steps east at z -1..1)
    stair_x(bp, -12, -1, 1, SME, "east", low=SME - 1)
    stair_x(bp, -11, -1, 1, SME + 1, "east", low=SME - 1)
    bp.barrel_kind = None


def yoke(bp):
    """The yoke through the chest (feet 60): the corridor between the shoulders, the ladder up the neck to the eyrie,
    the steps up to the right shoulder."""
    f = YOKE
    floor_box(bp, -10, -7, -16, 16, f - 1, PATH)
    floor_box(bp, -16, -8, -24, -16, f - 1, PATH)
    for i, z in enumerate(range(17, 20)):
        stair_z(bp, z, -10, -7, YOKE + i, "south", low=YOKE - 1)
    floor_box(bp, -16, -7, 20, 24, RSH - 1, PATH)
    for z in (-12, -4, 4, 12):
        if bp.get(-7, f + 3, z) == AIR:
            bp.set(-7, f + 3, z, "soul_wall_torch[facing=west]") if solid(-6, f + 3, z) else None
    for y in range(YOKE, 72):
        bp.set(-6, y, 0, "ladder[facing=west,waterlogged=false]")
    hang(bp, -12, YOKE + 3, -20, HANG_LANT, drop=1) if bp.get(-12, YOKE + 4, -20) == AIR else None
    hang(bp, -12, RSH + 3, 22, HANG_LANT, drop=1) if bp.get(-12, RSH + 4, 22) == AIR else None
    # the left shoulder: the gear of the crane-bridge's winding
    bp.set(-15, YOKE, -23, GEAR)
    bp.set(-15, YOKE + 1, -23, GEAR)
    bp.barrel(-15, YOKE, -17, "up")


def eyrie(bp):
    """The forgemaster's eyrie in the helm (feet 72, optional): the master's desk, a chest, the visor slits looking
    down on the anvil (a vista)."""
    f = 72
    floor_box(bp, -7, 9, -4, 4, f - 1, PATH)
    bp.set(-6, f - 1, 0, "ladder[facing=west,waterlogged=false]")     # the ladder's top rung, not paved over
    bp.chest(3, f, -3, "south", loot=LOOT + "tf_eyrie")
    bp.set(1, f, 3, W + "mahogany_table")
    bp.set(2, f, 3, "lectern[facing=north,has_book=false,powered=false]")
    bp.set(-1, f, 3, stair("dark_oak_stairs", "north"))
    hang(bp, 3, f + 4, 0, HANG_LANT, drop=1) if bp.get(3, f + 5, 0) not in (None, AIR) else \
        bp.set(3, f, 0, LANT)
    # visor slits: through the face, down and forward to the anvil
    for z in (-2, 2):
        pierce(bp, 9, f + 1, z, 1, 0, h=2, w=1, fill="iron_bars", sill=None)
    # the eyes glow from outside: ember lamps beside the slits
    for z in (-3, 3):
        for x in range(9, 14):
            if solid(x, f + 1, z) and not solid(x + 1, f + 1, z):
                bp.set(x, f + 1, z, LAMP)
                break


def left_arm(bp):
    """Stair down the left upper arm (feet 60 -> 49), the winch room (waystone), the crane-bridge stair down the
    forearm (49 -> 36) into the hand on the anvil."""
    path = left_arm_path()
    for (x, zc, f) in path:
        stair_x(bp, x, zc - 1, zc + 1, f - 1, "west", low=f - 2)
    for (x, zc, f) in path[::3]:
        if bp.get(x, f + 3, zc) == AIR and solid(x, f + 4, zc):
            bp.set(x, f + 3, zc, HANG_LANT)
    # the winch room: waystone, the crane's drum and gears
    f = ELB
    floor_box(bp, 4, 11, -29, -23, f - 1, DECK)
    bp.set(7, f - 1, -27, CHIS)
    bp.set(7, f, -27, MOD["waystone"])
    for z in range(-29, -25):
        bp.set(11, f + 1, z, IRON if z % 2 else BRASS)
    bp.set(11, f, -29, GEAR)
    bp.set(11, f, -24, GEAR)
    bp.set(4, f, -29, "brasshaven:brass_plating_slab[type=bottom,waterlogged=false]")
    hang(bp, 7, f + 3, -25, HANG_LANT, drop=1) if bp.get(7, f + 4, -25) not in (None, AIR) else None
    for x in (5, 10):
        if bp.get(x, f + 2, -23) == AIR and solid(x, f + 2, -22):
            bp.set(x, f + 2, -23, "soul_wall_torch[facing=north]")
    # inside the hand: the last landing before the mist
    floor_box(bp, 25, 34, -19, -12, AF - 1, DECK)
    bp.set(29, AF + 2, -18, "soul_wall_torch[facing=south]") if solid(29, AF + 2, -19) else None
    bp.mist(31, AF, -9, 33, AF + 3, -9)
    for y in range(AF, AF + 4):
        for z in (-10, -9):
            for x in (30, 34):
                bp.set(x, y, z, BRASS if y == AF + 3 else IRON)
    for x in range(30, 35):
        bp.set(x, AF + 4, -9, GILD)


def right_arm(bp):
    """The hammer-gallery (optional): up the raised right arm (feet 63 -> 75), the trophy room in the elbow, the
    gallery of hammers along the forearm, the lookout in the fist over the arena."""
    path = right_arm_path()
    floor_box(bp, 3, 9, 21, 30, 74, PATH)
    floor_box(bp, 18, 23, 10, 14, 77, DECK)
    prev = None
    for i, (x, zc, f) in enumerate(path):
        nxt = path[i + 1] if i + 1 < len(path) else None
        if prev is None or f > prev:
            for z in range(zc - 1, zc + 2):
                # a step only where the next row carries on at this z (the band drifts in z up the arm)
                if nxt is None or nxt[0] != x + 1 or abs(z - nxt[1]) <= 1:
                    stair_x(bp, x, z, z, f - 1, "east", low=f - 2)
                else:
                    for y in range(f - 2, f):
                        bp.set(x, y, z, PBB)
        else:
            for z in range(zc - 1, zc + 2):
                bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))
        prev = f
    # trophies: hammers of iron blocks on walls of the elbow room
    for (x, z) in ((4, 29), (7, 29), (4, 25)):
        if bp.get(x, 75, z) == AIR:
            bp.set(x, 75, z, IRON_WALL)
            bp.set(x, 76, z, "iron_block")
    # hammer racks along the gallery (wall posts with heads)
    for (x, zc, f) in path[12:]:
        for z in (zc - 2, zc + 2):
            if solid(x, f + 1, z) and x % 2 == 0 and bp.get(x, f + 1, zc + (1 if z > zc else -1)) == AIR:
                bp.set(x, f + 1, z, "iron_block" if x % 4 == 0 else "anvil[facing=north]")
    bp.chest(19, 78, 13, "east", loot=LOOT + "tf_hammer")
    bp.spawner(6, 75, 26, MOB_IMP)
    bp.set(21, 80, 10, LANT) if bp.get(21, 80, 10) == AIR else None
    bp.set(5, 77, 29, LANT) if bp.get(5, 77, 29) == AIR else None


def windows(bp):
    # the smelting hall looks west over the approach from the titan's back
    for z in (-6, 0, 6):
        pierce(bp, -30, SME + 4, z, -1, 0, h=3, fill="orange_stained_glass_pane")
    # the armoury and the barracks look out to the north and south
    for x in (-28, -20):
        pierce(bp, x, ARM + 2, -10, 0, -1, h=2)
        pierce(bp, x, ARM + 2, 10, 0, 1, h=2)
    for x in (-36, -30):
        pierce(bp, x, BAR + 2, -10, 0, -1, h=2)
    # the winch room looks down on the mould and the crane's ladle
    pierce(bp, 8, ELB + 1, -29, 0, -1, h=2, w=2)


# ------------------------------------------------------------------ the arena, the vault, the descent
def arena(bp):
    """The anvil's face (feet 36): rings of brass and dark iron, the strike mark under the hammer, a parapet round
    the face (gaps where the hand lies), braziers at the corners, the seal; sealed bars on the south balcony."""
    ax, az = AC
    y = AF - 1
    for x in range(26, 75):
        for z in range(-19, 20):
            if bp.get(x, AF, z) not in (AIR, None):
                continue
            d = math.hypot(x - ax, z - az)
            if d <= 2.4:
                spec = "iron_block"
            elif d <= 5.4:
                spec = "magma_block" if int(math.degrees(math.atan2(z, x - ax)) + 360) % 45 < 12 else IRON
            elif 9.5 <= d < 10.5 or 16.5 <= d < 17.5:
                spec = BRASS
            elif d < 17.5:
                spec = TREAD if int(d) % 2 else IRON
            else:
                spec = IRON if (x + z) % 3 else "polished_deepslate"
            bp.set(x, y, z, spec)
    bp.boss_seal(ax, y, az, BOSS, AR - 1)
    # parapet round the face
    for x in range(26, 75):
        for z in (-19, 19):
            if bp.get(x, AF, z) in (None, AIR) and not (z == 19 and 42 <= x <= 44):
                bp.set(x, AF, z, IRON_WALL if (x % 6) else BRASS)
    for z in range(-19, 20):
        for x in (26, 74):
            if bp.get(x, AF, z) in (None, AIR):
                bp.set(x, AF, z, IRON_WALL if (z % 6) else BRASS)
    # corner braziers
    for (x, z) in ((29, 16), (71, -16), (71, 16)):
        brazier(bp, x, AF, z, big=True)
    # the south balcony with sealed bars (opens when the boss falls)
    for x in range(41, 46):
        for z in range(20, 23):
            bp.set(x, y, z, DECK.pick(x, y, z))
            bp.set(x, y - 1, z, stair(IRON_STAIRS, "north", "top") if z == 22 else IRON)
            for yy in range(AF, AF + 4):
                bp.set(x, yy, z, AIR)
    for x in range(42, 45):
        for yy in range(AF, AF + 3):
            bp.set(x, yy, 19, MOD["vault_bars"])
    for yy in range(AF, AF + 4):
        bp.set(41, yy, 19, BRASS if yy == AF + 3 else IRON)
        bp.set(45, yy, 19, BRASS if yy == AF + 3 else IRON)
    for x in range(41, 46):
        bp.set(x, AF + 3, 19, GILD) if 42 <= x <= 44 else None
    # the hammer's striking face gets a glow: a ring of lamps under the head
    for (x, z) in ((44, -6), (56, -6), (44, 6), (56, 6)):
        bp.set(x, 65, z, LAMP)


def descent(bp):
    """After the boss: the ledge stair west down the anvil's south side (feet 36 -> 28) to the vault landing, the
    vault door; sealed bars, then the bridge down to the plinth's lobe (feet 18) -- the way back to the hub."""
    # ledge stair x 40..34 (feet 35..29), z 20..22
    for i, x in enumerate(range(40, 33, -1)):
        f = AF - 1 - i
        for z in range(20, 23):
            bp.set(x, f - 1, z, stair(PBBS, "east"))
            bp.set(x, f - 2, z, PBB)
            for yy in range(f, f + 4):
                bp.set(x, yy, z, AIR)
        bp.set(x, f - 3, 21, stair(PBBS, "north", "top"))
        railing(bp, x, f, 23, "south")
        bp.set(x, f - 1, 23, PBB)
    # the vault landing x 28..33, feet 28
    for x in range(26, 34):
        for z in range(20, 23):
            bp.set(x, VF - 1, z, PATH.pick(x, VF - 1, z))
            bp.set(x, VF - 2, z, PBB)
            for yy in range(VF, VF + 4):
                bp.set(x, yy, z, AIR)
        railing(bp, x, VF, 23, "south")
        bp.set(x, VF - 1, 23, PBB)
    # sealed bars at the head of the bridge (x 25)
    for z in range(20, 23):
        for yy in range(VF, VF + 3):
            bp.set(25, yy, z, MOD["vault_bars"])
        bp.set(25, VF - 1, z, CHIS)
    for yy in range(VF, VF + 4):
        bp.set(25, yy, 19, IRON)
        bp.set(25, yy, 23, IRON)
    for z in range(19, 24):
        bp.set(25, VF + 3, z, BRASS)
    # the bridge: x 24..17 down to feet 20, then flat to the lobe (feet 18 at x <= 16)
    for i, x in enumerate(range(24, 16, -1)):
        f = VF - 1 - i
        f = max(f, HUB)
        for z in range(20, 23):
            if f > HUB:
                bp.set(x, f - 1, z, stair(PBBS, "east"))
            else:
                bp.set(x, f - 1, z, PATH.pick(x, f - 1, z))
            bp.set(x, f - 2, z, PBB)
            for yy in range(f, f + 4):
                bp.set(x, yy, z, AIR)
        railing(bp, x, f, 19, "north")
        railing(bp, x, f, 23, "south")
        bp.set(x, f - 1, 19, PBB)
        bp.set(x, f - 1, 23, PBB)
    # the pier under the bridge
    for x in range(19, 23):
        for z in range(19, 24):
            for yy in range(0, 17):
                bp.set(x, yy, z, PBB if yy % 6 else BRASS)
    bp.set(21, 17, 21, PBB)


def vault(bp):
    """The vault in the anvil's heel (feet 28): the forge's hoard, the master smith's chests, ingots stacked, the
    gold of the wages; a door south to the landing."""
    f = VF
    floor_box(bp, 28, 40, 4, 19, f - 1, DECK)
    bp.chest(29, f, 6, "east", loot=LOOT + "tf_vault")
    bp.chest(39, f, 6, "west", loot=LOOT + "tf_vault")
    bp.chest(34, f, 4, "south", loot=LOOT + "tf_vault")
    for x in range(28, 41):
        for z in range(4, 18):
            if (x in (28, 40) or z == 4) and bp.get(x, f, z) == AIR and hash01(x, z, 641) < 0.5:
                h = 1 + int(hash01(x, z, 642) * 2)
                for yy in range(f, f + h):
                    bp.set(x, yy, z, ("gold_block", "iron_block", "raw_gold_block", "raw_iron_block")[
                        int(hash3(x, yy, z, 643) * 4)])
    for (x, z) in ((33, 12), (35, 12)):
        bp.set(x, f, z, "anvil[facing=north]")
    bp.set(34, f, 12, "smithing_table")
    chandelier(bp, 34, f + 5, 10, drop=1)
    # the door frame on the south face
    for yy in range(f, f + 4):
        bp.set(29, yy, 19, BRASS if yy == f + 3 else IRON)
        bp.set(33, yy, 19, BRASS if yy == f + 3 else IRON)
    for x in range(29, 34):
        bp.set(x, f + 4, 19, GILD)


# ------------------------------------------------------------------ the titan's outside: armour, crest, crane
def titan_details(bp):
    """Chimneys rising from the back (the smelting hall's flues), the spine ridge of brass fins, rivets and pipes,
    the eyes, the crane gear on the left arm, the ladle over the mould, the glowing joints."""
    # three chimneys from the back (start just under the surface, rise to y 88)
    for (cx, cz, top) in ((-27, -6, 86), (-23, 6, 88), (-31, 1, 82)):
        y0 = None
        for y in range(SME + 12, 90):
            if not solid(cx, y, cz):
                y0 = y - 2
                break
        if y0 is None:
            continue
        for y in range(y0, top + 1):
            for x in range(cx - 2, cx + 3):
                for z in range(cz - 2, cz + 3):
                    d = math.hypot(x - cx, z - cz)
                    if d <= 2.4:
                        if d <= 1.0 and y > y0:
                            bp.set(x, y, z, AIR)
                        else:
                            bp.set(x, y, z, BRASS if (top - y) % 6 == 1 else SMOKE)
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                d = math.hypot(x - cx, z - cz)
                if 2.4 < d <= 3.4:
                    bp.set(x, top - 1, z, stair(SMOKE_STAIRS, "south" if z < cz else "north" if z > cz else
                                                ("east" if x < cx else "west"), "top"))
        bp.set(cx, y0, cz, "hay_block[axis=y]")
        bp.set(cx, y0 + 1, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # the spine ridge: brass fins along the top of the back
    for k in range(10):
        t = k / 9.0
        x = int(round(-36 + 22 * t))
        y = None
        for yy in range(90, 30, -1):
            if solid(x, yy, 0):
                y = yy
                break
        if y is None:
            continue
        for dy in range(1, 3 if k % 2 else 4):
            bp.set(x, y + dy, 0, BRASS if dy < 3 else GILD)
    # copper pipes along the back between the chimneys
    for x in range(-34, -17):
        for z in (-3, 3):
            for yy in range(90, 40, -1):
                if solid(x, yy, z):
                    if bp.get(x, yy + 1, z) is None:
                        bp.set(x, yy + 1, z, PIPES)
                    break
    # the eyes: ember lamps in the visor line
    for z in (-3, 3):
        for x in range(16, 3, -1):
            if solid(x, 73, z):
                bp.set(x, 73, z, LAMP)
                bp.set(x, 72, z, "shroomlight")
                break
    # glowing joints: a ring of magma round the knees, the elbows, the neck
    for (c, r) in ((L_KNEE, 7.5), (R_KNEE, 7.5), (L_ELBOW, 7.5), (R_ELBOW, 6.5)):
        cx, cy, cz = c
        for a in range(0, 360, 8):
            t = math.radians(a)
            x = int(round(cx + math.cos(t) * r))
            z = int(round(cz + math.sin(t) * r))
            for y in (int(cy),):
                if solid(x, y, z) and label(x, y, z) in (BODY,):
                    bp.set(x, y, z, "magma_block")
    # the crane-bridge: a girder along the top of the left forearm, a pulley at the wrist, the ladle on its chain
    for x in range(8, 29):
        yc, zc = arm_axis(L_ELBOW, (28, 39, -18), x)
        top = None
        for yy in range(int(yc) + 9, int(yc) - 2, -1):
            if solid(x, yy, int(round(zc))):
                top = yy
                break
        if top is None:
            continue
        bp.set(x, top + 1, int(round(zc)), IRON if x % 3 else BRASS)
        if x % 3 == 0:
            bp.set(x, top + 2, int(round(zc)), IRON_WALL)
    # the pulley on the outside of the forearm and the ladle over the east mould
    for y in range(22, 44):
        for x in (14, 15, 16):
            if not solid(x, y, -31) and (x != 15 or y > 22):
                bp.set(x, y, -31, CHAIN)
    for (x, z) in ((14, -31), (16, -31), (15, -30), (15, -32)):
        bp.set(x, 21, z, IRON)
    bp.set(15, 21, -31, "magma_block")                     # the ladle's glowing charge
    bp.set(15, 20, -31, IRON)
    for x in range(12, 17):
        if not solid(x, 44, -31):
            bp.set(x, 44, -31, IRON if x != 15 else GEAR)


def anvil_details(bp):
    """The hardy hole and pritchel hole on the heel (decorative, barred), brass bands, chains of quench buckets."""
    for x in range(27, 30):
        for z in range(-3, 0):
            if bp.get(x, AF, z) == AIR:
                bp.set(x, AF - 1, z, "iron_bars")
    # quench buckets on chains under the horn
    for (x, z) in ((80, -4), (86, 4)):
        for y in range(17, 30):
            for xx in (x - 1, x + 1):
                if not solid(xx, y, z):
                    bp.set(xx, y, z, CHAIN)
        for y in range(19, 30):
            if not solid(x, y, z):
                bp.set(x, y, z, CHAIN)
        for xx in (x - 1, x + 1):
            bp.set(xx, 16, z, IRON)
        bp.set(x, 16, z, IRON)
        bp.set(x, 17, z, "hopper[enabled=true,facing=down]")    # the bucket


# ------------------------------------------------------------------ the open space the forge needs
ARENA_DOME = (27.0, 40.0, 23.0)     # semi-axes (x, y, z) of the air dome over the anvil face, from (AC, AF)
TERRACE_TOP = 27                    # last air layer over the plinth top (feet 18): the open terraces
GAP = (1, 25, -40, 30)              # x0, x1, z0, z1 of the gap between the plinth and the anvil (crucible, crane)


def open_space():
    """Grid mask of the volumes that must stay open whatever the Nether puts there: the dome over the anvil face
    (the arena under the hammer, the hammer's face, the hand), the air over the plinth's terraces (the crucible
    terrace, the hub, the north terrace) and the gap between the plinth and the anvil at terrace height (the
    crucible's fall, the crane, the bridge back from the vault). The rest of the site stays structure void (the
    lava lake: the terrain the cavern FIT found open). About 100k air entries."""
    X = np.arange(GX0, GX1 + 1)[:, None, None]
    Y = np.arange(GY0, GY1 + 1)[None, :, None]
    Z = np.arange(GZ0, GZ1 + 1)[None, None, :]
    rx, ry, rz = ARENA_DOME
    dome = (((X - AC[0]) / rx) ** 2 + ((Y - AF) / ry) ** 2 + ((Z - AC[1]) / rz) ** 2 <= 1.0) & (Y >= AF)
    terrace = plinth_mask2d()[:, None, :] & (Y > PTOP) & (Y <= TERRACE_TOP)
    gx0, gx1, gz0, gz1 = GAP
    gap = (X >= gx0) & (X <= gx1) & (Z >= gz0) & (Z <= gz1) & (Y > PTOP) & (Y < AF)
    return dome | terrace | gap


def carve_open(bp):
    """Explicit air in the open volumes where nothing is built (the last step: only unset cells), so the natural
    netherrack of the place cannot fill the arena or the terraces."""
    for ix, iy, iz in np.argwhere(open_space()).tolist():
        x, y, z = ix + GX0, iy + GY0, iz + GZ0
        if bp.get(x, y, z) is None:
            bp.set(x, y, z, AIR)


# ------------------------------------------------------------------ the whole site
def titan_forge(bp):
    lake(bp)
    shore(bp)
    lab, body = build_masses()
    air, cut = rooms(lab, body)
    write_masses(bp, lab, air, cut)
    causeway(bp)
    toll_arch(bp)
    outpost(bp)
    gate(bp)
    casting_hall(bp)
    hall_roof(bp)
    bellows(bp)
    grand_stair(bp)
    lift(bp)
    lift_cage(bp)
    slag_mine(bp)
    terraces(bp)
    plinth_buildings(bp)
    crucibles(bp)
    knee_hall(bp)
    newel_stair(bp)
    barracks(bp)
    armoury(bp)
    smelting_hall(bp)
    yoke(bp)
    eyrie(bp)
    left_arm(bp)
    right_arm(bp)
    windows(bp)
    arena(bp)
    descent(bp)
    vault(bp)
    titan_details(bp)
    anvil_details(bp)
    carve_open(bp)


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates (x, y, z)
VIEWS = [
    ("casting_hall", (-64, LOW, 23), (-52, 20, 4)),
    ("bellows", (-56, LOW, -9), (-62, LOW + 4, -28)),
    ("crucible_terrace", (-6, HUB, 2), (0, HUB + 6, -30)),     # the east crucible, its fall into the gap
    ("barracks", (-26, BAR, -6), (-38, BAR + 2, 4)),
    ("smelting_hall", (-15, SME, 0), (-28, SME + 3, -6)),
    ("crane_bridge", (13, ELB - 2, -24), (24, AF + 2, -19)),
    ("arena", (32, AF, 8), (50, 66, -4)),         # the face under the hammer, the hand on the left
]

register(StructureDef(
    "titan_forge", "nether", ["basalt_deltas", "crimson_forest"],
    [Piece("forge", titan_forge, views=VIEWS)],
    spacing=36, separation=12, adaptation="none", height=("absolute", 30), processors="none", max_distance=116,
    ground=AF - 1, foundation=False,
    spawns=[(MOB_GUARD, 8, 1, 2), (MOB_WSKEL, 5, 1, 2), (MOB_CUBE, 4, 1, 2), (MOB_HOUND, 3, 1, 2), ("brasshaven:slag_golem", 3, 1, 1)],
    title_fr="La Forge du Titan de basalte", title_en="Forge of the Basalt Titan"))

"""Kneeling Gate (La Porte agenouillée): two armoured giants of stone, 70 blocks high, kneel face to face across a
mountain pass and hold up a stone lintel between their hands, with a toll town in the road under it. Colossal tier
(tools/BUILDING.md §1, §12 concept 13, §15).

Silhouette (one noun phrase, §15.1): two kneeling knights facing each other across a pass, arms raised, a beam of
stone resting in their gauntlets and a gilded pavilion on its keystone.

Layout, ground y = 0, x east, z south. The pass runs north-south along x = 0; rock flanks rise behind both statues
(|x| > 88) to a crest ~45 high. The west statue kneels on its plinth facing east, the east statue is its mirror image
(world x = -x): the pair is symmetric about the road (§2 deliberate pair). Each figure kneels on its north knee, the
south knee raised; a red-granite cloak falls from the shoulders over the back calf, a tabard with the golden key of the
toll hangs between the thighs, a braided beard over the breastplate, an open helm with a nasal, cheek plates and a
copper-trimmed crest. Pale limestone plate (darker low, calcite at the crown), grey stone mail, waxed bronze-copper edges.

The route (main path, ~600 path blocks):
  * the approach: the road comes in from the south, bends round a rock spur that hides the gate's foot, and opens on
    the toll town between the plinths (reveal: both figures and the lintel framed by the spur and the west outcrop);
  * the toll town under the lintel: the square round a well (it looks down into the hall under the gate), the toll
    gate across the road, the toll office, an inn, a smithy and a stable; the waystone by the well;
  * the west plinth's guard-house (door on the road): guard hall, barracks, storeroom; a square newel stair (3 wide,
    landings every 3 steps) climbs inside the kneeling thigh, past the girdle hall in the hips (feet 31) and the heart
    chamber in the chest (feet 43, windows through the breastplate toward the other giant) to the gorget room under the
    neck (feet 52). A short stair goes up the neck into the helm: the watchers' cell behind the barred eyes;
  * out through the south pauldron onto the arm: a parapeted stair climbs the forearm to the gauntlet and steps onto
    the lintel (feet 63). The lintel walk crosses the pass 63 blocks up (vista both ways), the keystone pavilion in the
    middle holds the hub site of grace and the toll bell, a toll lamp hangs on chains under it over the square;
  * down the east statue's arm, through its gorget (the treasury in its helm: the toll hoard behind the eyes), down
    its newel stair past the heart chamber (the drop well: a one-way shortcut to the girdle hall) to its guard-house,
    whose iron door opens onto the square from inside only (shortcut back to the waystone);
  * from the east guard-house a second newel stair goes down to the keepers' chapel (site of grace, feet -20), a
    narrow passage (compression) and the mist into the hall under the gate: the boss arena (radius 17.5, a shallow
    dome, the well's light falling through a grate in the middle). The vault lies under its floor (sealed bars); the
    west passage leads to the west newel stair up to the west guard-house through an iron door that opens from the
    arena side only (the last shortcut).
Loot gradient (§15.6): town and guard-houses tier 1, girdle halls 1-2, heart chambers, the watchers' cell and the lintel
2, the head treasury 2-3, the vault under the arena 3.
Height budget: the keystone finial stands 78 above the ground layer, the crests and helms ~72, so every mountain-pass
biome fits under the build limit; jagged and frozen peaks are left out like the Pilgrim's Ascent.
"""
import math
import re

import numpy as np

from ..arch import boulder, spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3, is_air
from ..parts import LOOT, MOD

# the gate's own guardian: the Oathbound Gatekeeper (entity/boss/OathboundGatekeeper.java, tools/BOSSES.md section 11)
BOSS = "brasshaven:oathbound_gatekeeper"
MOB_KNIGHT = "brasshaven:skeleton_knight"
MOB_GARGOYLE = "brasshaven:gargoyle"
MOB_STRAY = "minecraft:stray"

# ------------------------------------------------------------------ dimensions
XW = -52                    # local u = 0 of the west statue: world x = XW + u (east statue: x = -XW - u)
P = 8                       # the figures kneel on y = P (plinth top block y = P - 1)
LIN_X = 35                  # the lintel spans |x| <= LIN_X
LIN_V = 7                   # lintel half width: deck |z| <= 6, parapets at |z| = 7
LIN_TOP = 62                # top block of the lintel (walk feet 63)
WALK_F = LIN_TOP + 1
FL_G, FL_GI, FL_H, FL_GO, FL_HEAD = 1, 31, 43, 52, 57   # feet: guard-house, girdle, heart, gorget, helm
SP_C = (-3, -7)             # the newel stair in the body (local u, v)
S0_C = (21, 12)             # the newel stair down from the guard-house to the hall under the gate
UND_F = -20                 # feet in the hall under the gate
AR_R = 17.5                 # arena floor radius
AR_WALL = 19.6
VAULT_F = -27

# local statue grid
U0, U1, Y0, Y1, V0, V1 = -40, 34, -23, 76, -27, 27
NU, NY, NV = U1 - U0 + 1, Y1 - Y0 + 1, V1 - V0 + 1

# part labels
E_, PLINTH, MAIL, PLATE, TRIM, CLOTH, DARK, GOLD, FACE, BEARD, CLOTH_R, PIL, CORNICE, BASE = range(14)

LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
DIRV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ------------------------------------------------------------------ the statue model (local coordinates)
_UU, _YY, _VV = np.meshgrid(np.arange(U0, U1 + 1, dtype=np.float32), np.arange(Y0, Y1 + 1, dtype=np.float32),
                            np.arange(V0, V1 + 1, dtype=np.float32), indexing="ij")


def li(u, y, v):
    return u - U0, y - Y0, v - V0


class Model:
    def __init__(self):
        self.part = np.zeros((NU, NY, NV), np.int8)
        self.carve = np.zeros((NU, NY, NV), bool)
        self.open_ = np.zeros((NU, NY, NV), bool)
        self.eyes = []

    # ---- painting
    def _sub(self, lo, hi):
        a = [max(0, int(math.floor(lo[0])) - U0), max(0, int(math.floor(lo[1])) - Y0),
             max(0, int(math.floor(lo[2])) - V0)]
        b = [min(NU, int(math.ceil(hi[0])) - U0 + 1), min(NY, int(math.ceil(hi[1])) - Y0 + 1),
             min(NV, int(math.ceil(hi[2])) - V0 + 1)]
        sl = (slice(a[0], b[0]), slice(a[1], b[1]), slice(a[2], b[2]))
        return sl, _UU[sl], _YY[sl], _VV[sl]

    def paint(self, sl, mask, lab, only_empty=False):
        sub = self.part[sl]
        if only_empty:
            mask = mask & (sub == 0)
        sub[mask] = lab

    def capsule(self, a, b, ra, rb, lab, t0=0.0, t1=1.0, only_empty=False):
        r = max(ra, rb) + 1
        lo = [min(a[i], b[i]) - r for i in range(3)]
        hi = [max(a[i], b[i]) + r for i in range(3)]
        sl, U, Y, V = self._sub(lo, hi)
        vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L2 = vx * vx + vy * vy + vz * vz
        t = np.clip(((U - a[0]) * vx + (Y - a[1]) * vy + (V - a[2]) * vz) / L2, 0, 1)
        d = np.sqrt((U - a[0] - vx * t) ** 2 + (Y - a[1] - vy * t) ** 2 + (V - a[2] - vz * t) ** 2)
        m = (t >= t0) & (t <= t1) & (d <= ra + (rb - ra) * t + 0.3)
        self.paint(sl, m, lab, only_empty)

    def bands(self, a, b, ra, rb, ts, lab=TRIM, extra=0.9, w=0.7):
        """Raised rings round a limb at the positions ts (0..1): plate edges one block proud."""
        r = max(ra, rb) + extra + 1
        lo = [min(a[i], b[i]) - r for i in range(3)]
        hi = [max(a[i], b[i]) + r for i in range(3)]
        sl, U, Y, V = self._sub(lo, hi)
        vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        L = math.sqrt(vx * vx + vy * vy + vz * vz)
        t = np.clip(((U - a[0]) * vx + (Y - a[1]) * vy + (V - a[2]) * vz) / (L * L), 0, 1)
        d = np.sqrt((U - a[0] - vx * t) ** 2 + (Y - a[1] - vy * t) ** 2 + (V - a[2] - vz * t) ** 2)
        near = np.zeros_like(d, dtype=bool)
        for tb in ts:
            near |= np.abs(t - tb) * L <= w
        m = near & (t > 0) & (t < 1) & (d <= ra + (rb - ra) * t + extra + 0.3)
        self.paint(sl, m, lab)

    def ellipsoid(self, c, r, lab, cond=None, only_empty=False):
        lo = [c[i] - r[i] - 1 for i in range(3)]
        hi = [c[i] + r[i] + 1 for i in range(3)]
        sl, U, Y, V = self._sub(lo, hi)
        m = ((U - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((V - c[2]) / r[2]) ** 2 <= 1.0
        if cond is not None:
            m &= cond(U, Y, V)
        self.paint(sl, m, lab, only_empty)

    def box(self, u0, y0, v0, u1, y1, v1, lab, only_empty=False):
        sl, U, Y, V = self._sub((min(u0, u1), min(y0, y1), min(v0, v1)), (max(u0, u1), max(y0, y1), max(v0, v1)))
        self.paint(sl, np.ones(U.shape, bool), lab, only_empty)

    def setp(self, u, y, v, lab, only_empty=False):
        if U0 <= u <= U1 and Y0 <= y <= Y1 and V0 <= v <= V1:
            if only_empty and self.part[li(u, y, v)]:
                return
            self.part[li(u, y, v)] = lab

    def getp(self, u, y, v):
        if U0 <= u <= U1 and Y0 <= y <= Y1 and V0 <= v <= V1:
            return int(self.part[li(u, y, v)])
        return 0

    # ---- carving
    def carve_box(self, u0, y0, v0, u1, y1, v1, opening=False):
        a = li(min(u0, u1), min(y0, y1), min(v0, v1))
        b = li(max(u0, u1), max(y0, y1), max(v0, v1))
        sl = (slice(max(0, a[0]), b[0] + 1), slice(max(0, a[1]), b[1] + 1), slice(max(0, a[2]), b[2] + 1))
        self.carve[sl] = True
        if opening:
            self.open_[sl] = True

    def front(self, y, v, umin=-40):
        """Outermost body cell along +u at (y, v) (None if the column is empty)."""
        col = self.part[:, y - Y0, v - V0]
        nz = np.flatnonzero(col[umin - U0:])
        return int(nz[-1]) + umin if len(nz) else None

    def finish(self):
        body = self.part > 0
        er = body.copy()
        pad = np.pad(body, 1, constant_values=False)
        for ax in range(3):
            for s in (1, -1):
                er &= np.roll(pad, s, axis=ax)[1:-1, 1:-1, 1:-1]
        self.ceff = self.carve & body & (er | self.open_)
        solid = body & ~self.ceff
        outside = ~body
        pad_o = np.pad(outside, 1, constant_values=True)
        pad_c = np.pad(self.ceff, 1, constant_values=False)
        outer = np.zeros_like(body)
        inner = np.zeros_like(body)
        for ax in range(3):
            for s in (1, -1):
                outer |= np.roll(pad_o, s, axis=ax)[1:-1, 1:-1, 1:-1]
                inner |= np.roll(pad_c, s, axis=ax)[1:-1, 1:-1, 1:-1]
        up_open = np.zeros_like(body)
        up_open[:, :-1, :] = outside[:, 1:, :]
        up_open[:, -1, :] = True
        self.solid, self.outer, self.inner, self.up_open = solid, outer & solid, inner & solid, up_open


# ------------------------------------------------------------------ figure
def torso_dims(y):
    t = min(max((y - 31) / 21.0, 0.0), 1.0)
    cu = -1 + 1.5 * t
    au = 8.5 + 2.5 * math.sin(math.pi * t * 0.85)
    av = 11.5 + 5.0 * t ** 0.8
    if y > 50:
        s = 1 - ((y - 50) / 4.2) ** 2
        if s <= 0:
            return None
        s = math.sqrt(s)
        au, av = au * s, av * s
    return cu, au, av


def plinth(M):
    """The kneeling block: a battered base, pilasters every 8 blocks, a slab cornice; a masonry well under the
    guard-house for the stair down to the hall under the gate."""
    def inside(u, v, grow):
        if not (-34 - grow <= u <= 32 + grow and -22 - grow <= v <= 24 + grow):
            return False
        for cu_, cv_ in ((-34, -22), (-34, 24), (32, -22), (32, 24)):
            if abs(u - cu_) + abs(v - cv_) < 4 - grow:
                return False
        return True
    for u in range(-36, 35):
        for v in range(-24, 27):
            for y in range(-3, P):
                grow = 1 if y <= 0 else 0
                if inside(u, v, grow):
                    M.setp(u, y, v, BASE if y <= 0 else PLINTH)
            # pilasters on the faces (+1 proud), the slab cornice ring
            if inside(u, v, 1) and not inside(u, v, 0):
                edge_u = u in (-35, 33)
                pil = (edge_u and v % 8 == 0) or (not edge_u and u % 8 == 0)
                if pil and not (u == 33 and -3 <= v <= 3):
                    for y in range(1, P - 1):
                        M.setp(u, y, v, PIL)
                M.setp(u, P - 2, v, CORNICE)
    M.box(16, -22, 7, 26, -4, 17, PLINTH)          # masonry well round the down-stair
    # the kneeling stone: a raised step under the knee and the newel stair rising into the thigh
    for u in range(-11, 5):
        for v in range(-15, -1):
            for y in range(P, P + 3):
                if abs(u + 3) + abs(v + 8) <= 12 - (y - P):
                    M.setp(u, y, v, PLINTH)


def legs(M):
    # the north leg kneels: thigh up from the knee on the plinth, shin flat behind, toes curled
    hip, knee, ank, toe = (-2, 30, -8), (-4, 14, -8), (-22, 13, -8), (-28, 10, -8)
    M.capsule(hip, knee, 8.0, 7.0, MAIL)
    M.capsule(hip, knee, 8.5, 7.4, PLATE, 0.2, 0.8)
    M.bands(hip, knee, 8.5, 7.4, (0.78,), extra=0.6)
    M.ellipsoid((-3.5, 14, -8), (6.8, 6.8, 7.2), PLATE)
    M.capsule(knee, ank, 6.2, 4.8, PLATE)
    M.bands(knee, ank, 6.2, 4.8, (0.6,), extra=0.6)
    M.ellipsoid(ank, (4.8, 4.8, 4.8), MAIL)
    M.capsule(ank, toe, 4.6, 3.2, PLATE)
    
    # knee cop fan on the outer side
    for dy in range(-5, 6):
        for du in range(-5, 6):
            if math.hypot(du, dy) <= 4.6 and (du + dy) % 3:
                M.setp(-4 + du, 14 + dy, -16, TRIM if math.hypot(du, dy) > 3.6 else PLATE, only_empty=True)
    # the south leg raised: thigh forward, shin down to the foot flat on the plinth
    hip, knee, ank, toe = (0, 30, 9), (18, 31, 11), (19, 13, 12), (29, 10, 12)
    M.capsule(hip, knee, 8.0, 7.0, MAIL)
    M.capsule(hip, knee, 8.5, 7.5, PLATE, 0.15, 0.85)
    M.bands(hip, knee, 8.5, 7.5, (0.83,), extra=0.6)
    M.ellipsoid((18.5, 31.5, 11), (7.2, 7.2, 7.4), PLATE)
    M.capsule(knee, ank, 6.5, 5.0, PLATE)
    M.bands(knee, ank, 6.5, 5.0, (0.3,), extra=0.6)
    M.ellipsoid((19, 13, 12), (5.0, 5.0, 5.0), MAIL)
    M.capsule((19, 12, 12), toe, 4.8, 3.3, PLATE)
    
    M.ellipsoid((16, 10.5, 12), (3.4, 3.0, 4.2), PLATE)
    for dy in range(-5, 6):
        for du in range(-5, 6):
            if math.hypot(du, dy) <= 4.8 and (du - dy) % 3:
                M.setp(18 + du, 31 + dy, 20, TRIM if math.hypot(du, dy) > 3.8 else PLATE, only_empty=True)


def body(M):
    # pelvis in mail, tassets of plate over the front of the hips
    M.ellipsoid((-1, 29, 0), (10, 7, 14.5), MAIL)
    M.ellipsoid((-1, 29, 0), (11.3, 8.2, 15.8), PLATE,
                cond=lambda U, Y, V: (U > 2) & (Y >= 23) & (Y <= 32), only_empty=True)
    for y in range(31, 56):
        d = torso_dims(y)
        if d is None:
            break
        cu, au, av = d
        sl, U, Y, V = M._sub((cu - au - 1, y, -av - 1), (cu + au + 1, y, av + 1))
        m = ((U - cu) / au) ** 2 + (V / av) ** 2 <= 1.0
        M.paint(sl, m, DARK if y <= 33 else PLATE)
    # shoulders and trapezius, the gorget
    M.ellipsoid((0, 52, 0), (10, 6, 16), PLATE, only_empty=True)
    M.ellipsoid((0.5, 51.5, 0), (8.6, 2.4, 10.2), TRIM, cond=lambda U, Y, V: Y >= 52)
    # breastplate ridge and lames (one proud), belt proud with a gold buckle
    for y in range(31, 51):
        cu, au, av = torso_dims(y)
        for v in range(-int(av), int(av) + 1):
            uf = int(cu + au * math.sqrt(max(0.0, 1 - (v / av) ** 2)))
            if y <= 33:
                M.setp(uf + 1, y, v, DARK, only_empty=True)
                if abs(v) <= 1:
                    M.setp(uf + 2, y, v, GOLD)
            elif v == 0 and y >= 35:
                M.setp(uf + 1, y, v, TRIM, only_empty=True)
            elif y in (35, 39) and abs(v) < av - 1:
                M.setp(uf + 1, y, v, TRIM, only_empty=True)
    # side straps between breast and back plates
    for y in range(36, 50):
        cu, au, av = torso_dims(y)
        for s in (-1, 1):
            M.setp(int(round(cu - 1)), y, s * (int(av) + 1), DARK, only_empty=True)


def cloak(M):
    """A red granite cloak from the shoulders down the back, flaring over the kneeling calf, in vertical folds."""
    for y in range(9, 53):
        if y >= 31:
            cu, au, av = torso_dims(min(y, 50))
            ub = cu - au * 0.92 - 0.6
            cw = av + 0.6
        else:
            ub = -1 - 8.5 - 0.6 - (31 - y) * 0.42
            cw = 12.1 + (31 - y) * 0.15
        if y > 50:
            cw -= (y - 50) * 2.5
        for v in range(-int(cw), int(cw) + 1):
            q = v / cw
            fold = 1.7 * max(0.0, math.cos(v * 2 * math.pi / 6.0 + y * 0.05)) ** 1.5
            uc = ub + 5.5 * q * q - fold
            u0 = int(round(uc))
            lab = CLOTH_R if fold > 1.0 else CLOTH
            M.setp(u0, y, v, lab)
            M.setp(u0 + 1, y, v, CLOTH)
            # fill toward the body so the cloak is a solid drape, not a shell with voids behind it
            for u in range(u0 + 2, u0 + (14 if y < 31 else 9)):
                if M.getp(u, y, v):
                    break
                M.setp(u, y, v, CLOTH)


def tabard(M):
    """The tabard hangs from the belt between the thighs, the golden key of the toll on it."""
    cu, au, av = torso_dims(32)
    ut = int(cu + au) + 1
    for y in range(14, 33):
        for v in range(-5, 6):
            fold = 1 if v % 3 == 0 else 0
            u = ut - (1 if y < 20 else 0) + fold
            M.setp(u, y, v, CLOTH_R if fold else CLOTH, only_empty=True)
            for k in range(1, 6):
                if M.getp(u - k, y, v):
                    break
                M.setp(u - k, y, v, CLOTH)
    # fringe and the key
    for v in range(-5, 6):
        M.setp(ut + (1 if v % 3 == 0 else 0) - 1, 14, v, TRIM)
    key = [(0, y) for y in range(16, 22)] + [(-1, 21), (1, 21), (-1, 23), (1, 23), (-1, 22), (1, 22), (0, 23),
                                             (1, 16), (2, 16), (1, 17)]
    for v, y in key:
        u = ut - (1 if y < 20 else 0) + (1 if v % 3 == 0 else 0)
        M.setp(u + 1, y, v, GOLD)


def arms(M):
    for s in (-1, 1):
        S, E, Wr = (1, 50, 14 * s), (11, 47, 14 * s), (19, 54, 13 * s)
        M.capsule(S, E, 5.6, 5.1, MAIL)
        M.capsule(S, E, 6.0, 5.5, PLATE, 0.3, 0.8)
        M.ellipsoid(E, (5.8, 5.8, 5.8), PLATE)
        M.capsule(E, Wr, 5.2, 4.5, PLATE)
        M.bands(E, Wr, 5.2, 4.5, (0.62,), extra=0.7)
        # couter fan on the outer side of the elbow
        for du in range(-4, 5):
            for dy in range(-4, 5):
                if math.hypot(du, dy) <= 4.2 and (du + dy) % 3:
                    M.setp(11 + du, 47 + dy, s * 20, TRIM if math.hypot(du, dy) > 3.2 else PLATE, only_empty=True)
        # pauldron: three lames, each lower one a block wider, a low notched rim on top
        pc, pr = (0, 52.5, 15 * s), (8, 5.8, 7.5)
        M.ellipsoid(pc, pr, PLATE, cond=lambda U, Y, V: Y >= 47)
        for y0 in (48, 51):
            M.ellipsoid(pc, (pr[0] + 1, pr[1] + 1, pr[2] + 1), TRIM,
                        cond=lambda U, Y, V, y0=y0: Y == y0, only_empty=True)
        for u in range(-5, 5):
            top = max((y for y in range(52, 60) if M.getp(u, y, 15 * s)), default=None)
            if top is not None and u % 3 == 0:
                M.setp(u, top + 1, 15 * s, TRIM)
        # the gauntlet: palm up under the lintel, four fingers forward under it, the thumb up its side
        M.capsule(Wr, (20, 52, 10 * s), 4.0, 3.2, PLATE)
        M.ellipsoid((21.5, 52, 7.5 * s), (3.6, 1.8, 4.6), PLATE)
        for i, vf in enumerate((4.2, 6.2, 8.2, 10.2)):
            n = (5, 6, 5.5, 4)[i]
            a, b, c = (23, 52, vf * s), (23 + n, 52, vf * s), (24 + n, 53, vf * s)
            M.capsule(a, b, 1.1, 1.0, PLATE)
            M.capsule(b, c, 1.0, 0.9, PLATE)
            M.setp(25, 53, int(round(vf * s)), TRIM)
        M.capsule(Wr, (22, 58, 9 * s), 1.7, 1.5, PLATE)
        M.capsule((22, 58, 9 * s), (25, 60.5, 8.6 * s), 1.5, 1.3, PLATE)
        M.setp(22, 58, int(round(9 * s)) + s, TRIM)


def head(M):
    H, R = (2.0, 62.5, 0), (7.5, 9.0, 7.0)
    BRIM = 63
    M.capsule((0.5, 50, 0), (1.5, 57, 0), 5.0, 4.8, MAIL)
    M.ellipsoid(H, R, PLATE, cond=lambda U, Y, V: Y >= BRIM)
    M.ellipsoid(H, R, FACE, cond=lambda U, Y, V: (Y < BRIM) & (U > 3.5) & (np.abs(V) < 5.2))
    M.ellipsoid(H, R, PLATE, cond=lambda U, Y, V: (Y < BRIM), only_empty=True)
    M.ellipsoid((4.0, 56.0, 0), (5.0, 3.6, 5.0), FACE, only_empty=True)          # jaw
    # cheek plates, proud of the face sides, from the brim to the jaw
    for y in range(54, BRIM):
        for u in range(-2, 9):
            for s in (-1, 1):
                for v in range(5, 10):
                    if M.getp(u, y, s * (v - 1)) and not M.getp(u, y, s * v):
                        M.setp(u, y, s * v, PLATE if v < 8 or y % 3 else TRIM)
                        break
    # brim: a proud ring, gold on the brow
    M.ellipsoid(H, (R[0] + 1.2, R[1] + 1.2, R[2] + 1.2), TRIM, cond=lambda U, Y, V: Y == BRIM, only_empty=True)
    for v in (-1, 0, 1):
        uf = M.front(BRIM, v)
        if uf is not None:
            M.setp(uf, BRIM, v, GOLD)
    # crest: a low notched comb along u on the crown, a gold knob at its front
    for u in range(-6, 8):
        top = max((y for y in range(BRIM, 76) if M.getp(u, y, 0)), default=None)
        if top is None:
            continue
        h = 2 if u % 3 else 1
        for y in range(top + 1, min(top + h + 1, Y1 + 1)):
            M.setp(u, y, 0, GOLD if u >= 6 and y == top + h else TRIM)
    # the face: brow ridge, nasal, eyes (barred windows), nose, mouth, moustache
    for v in range(-5, 6):
        uf = M.front(62, v)
        if uf is not None:
            M.setp(uf + 1, 62, v, FACE)
    for y in range(58, 62):
        uf = M.front(y, 0)
        if uf is not None:
            M.setp(uf + 1, y, 0, TRIM)
    for y in (59, 60):
        for v in (-3, -2, 2, 3):
            uf = M.front(y, v)
            if uf is not None and M.getp(uf, y, v) == FACE:
                M.eyes.append((uf, y, v))
    for y in range(56, 58):
        for v in (-1, 0, 1):
            uf = M.front(y, v)
            if uf is not None and (v == 0 or y == 56):
                M.setp(uf + 1, y, v, FACE)
    for v in range(-5, 6):                                                        # moustache
        uf = M.front(55, v)
        if uf is not None and v != 0:
            M.setp(uf + 1, 55, v, BEARD)
    for s in (-1, 1):
        for y in (51, 52, 53, 54):
            uf = M.front(y, 5 * s)
            if uf is not None:
                M.setp(uf + 1, y, 5 * s, BEARD)


def beard(M):
    """The braided beard falls from the jaw over the gorget and the top of the breastplate, gold rings on it."""
    for y in range(40, 55):
        hw = 5.0 - (54 - y) * 0.2
        for v in range(-int(hw), int(hw) + 1):
            uf = M.front(y, v)
            if uf is None:
                continue
            th = 2 if y > 44 else 1
            for k in range(1, th + 1):
                M.setp(uf + k, y, v, GOLD if y in (44, 48) and abs(v) <= 1 else BEARD)


def fill_voids(M):
    """Empty cells sealed inside the figure (between the cloak and the back, under the beard) become mail, so the
    statue has no hidden caves."""
    empty = M.part == 0
    out = np.zeros_like(empty)
    out[0], out[-1], out[:, -1], out[:, :, 0], out[:, :, -1] = empty[0], empty[-1], empty[:, -1], empty[:, :, 0], \
        empty[:, :, -1]
    while True:
        n = out.copy()
        n[1:] |= out[:-1]
        n[:-1] |= out[1:]
        n[:, 1:] |= out[:, :-1]
        n[:, :-1] |= out[:, 1:]
        n[:, :, 1:] |= out[:, :, :-1]
        n[:, :, :-1] |= out[:, :, 1:]
        n &= empty
        if (n == out).all():
            break
        out = n
    M.part[empty & ~out] = MAIL


def statue_model():
    M = Model()
    plinth(M)
    legs(M)
    body(M)
    cloak(M)
    tabard(M)
    arms(M)
    head(M)
    beard(M)
    # the cloak's gathered hem over the north hip (closes a sheltered ledge behind the arm)
    M.ellipsoid((-8.5, 34, -12), (2.6, 3.0, 5.0), CLOTH, only_empty=True)
    fill_voids(M)
    carve_interior(M)
    M.finish()
    # where a stair's headroom grazes the skin, thicken the skin outward (a bulge of mail) instead of piercing it
    for (u, v, f, fc) in SPIRAL + SPIRAL0:
        for y in range(f, f + 3):
            i = li(u, y, v)
            if M.carve[i] and not M.ceff[i] and M.part[i]:
                M.ellipsoid((u, y, v), (2.2, 2.2, 2.2), MAIL, only_empty=True)
    M.finish()
    return M


# ------------------------------------------------------------------ the newel stairs
CORN = [(-1, -1), (1, -1), (1, 1), (-1, 1)]


def spiral(cu, cv, f0, k_end, c0=0):
    """Square newel stair round a 3 x 3 core: (u, v, feet, stair facing or None) per cell and the landings
    {k: (corner, feet)}. 3 x 3 landings at the corners, flights of three steps (3 wide) on the sides: +12 a turn."""
    cells, land = [], {}
    f = f0
    for k in range(k_end + 1):
        ci = (c0 + k) % 4
        sx, sv = CORN[ci]
        for du in (2, 3, 4):
            for dv in (2, 3, 4):
                cells.append((cu + sx * du, cv + sv * dv, f, None))
        land[k] = (ci, f)
        if k == k_end:
            break
        nx, nv = CORN[(ci + 1) % 4]
        if sx != nx:
            d = 1 if nx > sx else -1
            for i, du in enumerate((-d, 0, d)):
                for dv in (2, 3, 4):
                    cells.append((cu + du, cv + sv * dv, f + i + 1, "east" if d > 0 else "west"))
        else:
            d = 1 if nv > sv else -1
            for i, dvv in enumerate((-d, 0, d)):
                for du in (2, 3, 4):
                    cells.append((cu + sx * du, cv + dvv, f + i + 1, "south" if d > 0 else "north"))
        f += 3
    return cells, land


SPIRAL, SP_LAND = spiral(SP_C[0], SP_C[1], FL_G, 17, 0)
SPIRAL0, S0_LAND = spiral(S0_C[0], S0_C[1], UND_F, 7, 2)
assert SP_LAND[17][1] == FL_GO and SP_LAND[10][1] == FL_GI and SP_LAND[14][1] == FL_H
assert S0_LAND[7] == (1, FL_G)

# rooms (local boxes: u0, v0, u1, v1, feet, height)
GUARD = (6, -14, 29, 6, FL_G, 5)
BARRACKS = (6, 8, 15, 18, FL_G, 5)
STORE = (-26, -6, -10, 12, FL_G, 5)
GIRDLE = (-8, -2, 7, 11, FL_GI, 7)
HEART = (-7, -2, 8, 11, FL_H, 8)
GORGET = (-4, -6, 6, 10, FL_GO, 4)
HELM = (-3, -4, 7, 4, FL_HEAD, 9)
NECK_STAIR = [(-3, 53), (-2, 54), (-1, 55), (0, 56), (1, 57)]  # (u, feet) on v -1..1, then the helm floor
TUNNEL_FLAT = [(u, v) for u in range(0, 3) for v in range(11, 15)]
TUNNEL_STEPS = [(3, 53), (4, 54), (5, 55), (6, 55), (7, 55)]   # (u, feet) on v 12..14
ARM_PATH = [(u, 55) for u in range(8, 12)] + [(u, 55 + u - 11) for u in range(12, 20)]
TURN = [(u, v) for u in range(20, 23) for v in range(7, 15)]   # the gauntlet landing (feet WALK_F)
WINDOWS = [(v, y) for v in (5, 6, 7) for y in (45, 46, 47)]
WELL = (3, 6, 5, 8)                                            # east heart: the drop well (u0, v0, u1, v1)


def room_carve(M, r):
    u0, v0, u1, v1, f, h = r
    M.carve_box(u0, f, v0, u1, f + h - 1, v1)


def carve_interior(M):
    for (u, v, f, fc) in SPIRAL:
        M.carve_box(u, f, v, u, f + 4, v)
    for (u, v, f, fc) in SPIRAL0:
        M.carve_box(u, f, v, u, f + 4 if f + 4 < P - 2 else P - 3, v)
    for r in (GUARD, BARRACKS, STORE, GIRDLE, HEART, GORGET):
        room_carve(M, r)
    M.carve_box(GORGET[0] + 6, FL_GO, -11, GORGET[2], FL_GO + 3, -7)         # gorget reaches the stair's last landing
    M.carve_box(HELM[0], FL_HEAD, HELM[1], HELM[2], FL_HEAD + 8, HELM[3])      # the helm chamber
    for u, f in NECK_STAIR:
        M.carve_box(u, f, -1, u, f + 3, 1)
    # guard-house links: front portal and vestibule, the corridor to the newel stair, barracks door, store passage
    M.carve_box(30, 1, -1, 33, 4, 1, opening=True)
    M.carve_box(-7, 1, -14, 5, 4, -12)
    M.carve_box(9, 1, 7, 11, 3, 7)
    M.carve_box(23, 1, 7, 25, 4, 7)                                          # to the down-stair's top landing
    M.carve_box(-9, 1, 1, 5, 4, 3)
    for v in (-10, -5, 4):                                                    # loopholes in the front wall
        M.carve_box(30, 2, v, 33, 3, v, opening=True)
    # the down-stair's foot opens toward the road (local +u) into the passages under the town
    M.carve_box(26, UND_F, 14, 26, UND_F + 3, 16, opening=True)
    # pauldron tunnel and its opening onto the arm
    for (u, v) in TUNNEL_FLAT:
        M.carve_box(u, FL_GO, v, u, FL_GO + 3, v)
    for (u, f) in TUNNEL_STEPS:
        M.carve_box(u, f, 12, u, f + 3, 14, opening=u >= 4)
    M.carve_box(6, 55, 12, 9, 58, 14, opening=True)
    # heart windows through the breastplate, the eyes of the helm
    for v, y in WINDOWS:
        uo = M.front(y, v)
        if uo is not None:
            M.carve_box(HEART[2], y, v, uo, y, v, opening=True)
    for (u, y, v) in M.eyes:
        M.carve_box(HELM[2], y, v, u, y, v, opening=True)


# ------------------------------------------------------------------ materials
def plate_block(u, y, v, seed):
    n = hash3(u // 2, y // 3, v // 2, seed) * 0.6 + hash3(u // 5, y // 5, v // 5, seed + 1) * 0.4
    val = y / 72.0 + (n - 0.5) * 0.32
    return ("polished_andesite" if val < 0.22 else "smooth_stone" if val < 0.5 else
            "polished_diorite" if val < 0.8 else "calcite")


def trim_block(u, y, v, seed):
    n = hash3(u // 2, y // 2, v // 2, seed + 5)
    return "waxed_exposed_cut_copper" if n < 0.7 else "waxed_cut_copper"


def mail_block(u, y, v, seed, up):
    val = y / 58.0 + (0.12 if up else 0.0) + (hash3(u // 2, y // 2, v // 2, seed + 9) - 0.5) * 0.35
    return ("tuff" if val < 0.25 else "andesite" if val < 0.55 else "stone" if val < 0.85 else "polished_andesite")


def masonry(u, y, v, seed):
    h = hash3(u, y, v, seed + 19)
    if (y + int(2 * hash01(u, v, seed))) % 7 == 0:
        return "tuff_bricks"
    if h < 0.1:
        return "cracked_stone_bricks"
    if y < 12 and h < 0.3:
        return "mossy_stone_bricks"
    return "stone_bricks"


def outer_block(lab, u, y, v, seed, up, mossy):
    h = hash3(u, y, v, seed)
    if up and P <= y < 18 and lab not in (GOLD, TRIM, PIL, CORNICE, PLINTH, BASE) and h < mossy * (1 - y / 18.0):
        return "moss_block"
    if lab == PLATE:
        return plate_block(u, y, v, seed)
    if lab == TRIM:
        return trim_block(u, y, v, seed)
    if lab == MAIL:
        return mail_block(u, y, v, seed, up)
    if lab in (CLOTH, CLOTH_R):
        if y < 12:
            return "terracotta" if h < 0.6 else "granite"
        return "polished_granite" if lab == CLOTH_R else ("granite" if h < 0.85 else "polished_granite")
    if lab == DARK:
        return "polished_deepslate" if h < 0.7 else "deepslate_tiles"
    if lab == GOLD:
        return "gold_block"
    if lab == FACE:
        return "smooth_stone" if h < 0.75 else "stone"
    if lab == BEARD:
        return "polished_tuff" if v % 2 == 0 else "tuff_bricks"
    if lab == PIL:
        return "chiseled_stone_bricks" if y == P - 3 else "polished_andesite"
    if lab == CORNICE:
        return "stone_brick_slab[type=top,waterlogged=false]"
    if lab == BASE:
        return "mossy_cobblestone" if h < 0.3 else ("cobblestone" if h < 0.6 else "andesite")
    # plinth faces and top
    if y == P - 1 and up:
        return "polished_andesite" if hash01(u // 3, v // 3, seed) < 0.5 else "stone_bricks"
    if y == 2 and (u % 4 == 0 or v % 4 == 0):
        return "chiseled_stone_bricks"
    if h < 0.12:
        return "cracked_stone_bricks"
    if y < 3 and h < 0.35:
        return "mossy_stone_bricks"
    return "stone_bricks"


# ------------------------------------------------------------------ writing one statue (mirrored for the east)
_FLIP = {"east": "west", "west": "east"}


def mirror_spec(spec):
    if not isinstance(spec, str):
        return spec
    spec = re.sub(r"facing=(east|west)", lambda m: "facing=" + _FLIP[m.group(1)], spec)
    spec = re.sub(r"hinge=(left|right)", lambda m: "hinge=" + ("right" if m.group(1) == "left" else "left"), spec)
    return spec


class Side:
    """Writes local (u, y, v) into the world for one statue: west (s = -1) as is, east (s = +1) mirrored in x.
    Facings are given as for the west statue (+u = east)."""

    def __init__(self, bp, s, M):
        self.bp, self.s, self.M = bp, s, M

    def x(self, u):
        return XW + u if self.s < 0 else -XW - u

    def f(self, facing):
        return _FLIP.get(facing, facing) if self.s > 0 else facing

    def set(self, u, y, v, spec):
        self.bp.set(self.x(u), y, v, mirror_spec(spec) if self.s > 0 else spec)

    def get(self, u, y, v):
        return self.bp.get(self.x(u), y, v)

    def air(self, u, y, v):
        return is_air(self.bp, self.x(u), y, v)

    def carved(self, u, y, v):
        if U0 <= u <= U1 and Y0 <= y <= Y1 and V0 <= v <= V1:
            return bool(self.M.ceff[li(u, y, v)])
        return False

    def stairs(self, u, y, v, block, facing, half="bottom"):
        self.set(u, y, v, stair(block, facing, half))

    def chest(self, u, y, v, facing, loot=None):
        self.bp.chest(self.x(u), y, v, self.f(facing), loot=loot)

    def barrel(self, u, y, v, loot=None):
        self.bp.barrel(self.x(u), y, v, "up", loot=loot)

    def door(self, u, y, v, facing, wood="spruce", hinge="left"):
        if self.s > 0:
            hinge = "right" if hinge == "left" else "left"
        self.bp.door(self.x(u), y, v, self.f(facing), wood=wood, hinge=hinge)

    def ladder(self, u, y0, v, y1, facing):
        self.bp.ladder(self.x(u), y0, v, y1, self.f(facing))

    def spawner(self, u, y, v, mob):
        self.bp.spawner(self.x(u), y, v, mob)

    def hang(self, u, y, v, lamp=LANT_H, reach=14):
        """A lamp hanging on a chain from the first solid block above (u, y, v)."""
        top = y + 1
        while top < y + reach and self.air(u, top, v):
            top += 1
        if self.air(u, top, v):
            return
        for yy in range(y + 1, top):
            self.set(u, yy, v, CHAIN)
        self.set(u, y, v, lamp)


def write_statue(S):
    M, bp, s = S.M, S.bp, S.s
    seed = 3 if s < 0 else 17
    mossy = 0.25 if s < 0 else 0.12
    idx = np.argwhere(M.solid)
    part, outer, inner, up = M.part, M.outer, M.inner, M.up_open
    for i, j, k in idx.tolist():
        u, y, v = i + U0, j + Y0, k + V0
        lab = int(part[i, j, k])
        if outer[i, j, k]:
            spec = outer_block(lab, u, y, v, seed, bool(up[i, j, k]), mossy)
        elif inner[i, j, k]:
            spec = masonry(u, y, v, seed)
        else:
            spec = "stone"
        S.set(u, y, v, spec)
    for i, j, k in np.argwhere(M.ceff).tolist():
        S.set(i + U0, j + Y0, k + V0, "air")


# ------------------------------------------------------------------ interiors (local, both statues)
def floor_main(u, v, seed=0):
    return "polished_andesite" if hash01(u, v, 31 + seed) < 0.55 else "stone_bricks"


def lay_floor(S, u0, v0, u1, v1, f, spec=None):
    for u in range(min(u0, u1), max(u0, u1) + 1):
        for v in range(min(v0, v1), max(v0, v1) + 1):
            if S.carved(u, f, v):
                S.set(u, f - 1, v, spec(u, v) if callable(spec) else (spec or floor_main(u, v)))


def build_spirals(S):
    for cells, land, top_f in ((SPIRAL, SP_LAND, FL_GO), (SPIRAL0, S0_LAND, FL_G)):
        for (u, v, f, fc) in cells:
            if fc:
                S.stairs(u, f - 1, v, "stone_brick_stairs", fc)
            else:
                S.set(u, f - 1, v, "polished_andesite" if (u + v) % 2 else "stone_bricks")
        cu, cv = (SP_C if cells is SPIRAL else S0_C)
        for k, (ci, f) in land.items():
            sx, sv = CORN[ci]
            if k % 2 == 0 and f < top_f:
                S.set(cu + sx * 4, f, cv + sv * 4, LANT)
        # the core: a pillar with a chiseled band every six blocks
        lo = min(f for (_, _, f, _) in cells) - 1
        hi = max(f for (_, _, f, _) in cells) + 4
        for y in range(lo, hi + 1):
            for du in (-1, 0, 1):
                for dv in (-1, 0, 1):
                    if S.carved(cu + du, y, cv + dv):
                        continue
                    if y % 6 == 0 and (du or dv):
                        S.set(cu + du, y, cv + dv, "chiseled_stone_bricks")


def guard_house(S, east):
    f = FL_G
    u0, v0, u1, v1, _, h = GUARD
    lay_floor(S, u0, v0, u1, v1, f, lambda u, v: "polished_andesite" if abs(v + 4) <= 1 else
              ("stone_bricks" if hash01(u, v, 5) < 0.7 else "cracked_stone_bricks"))
    lay_floor(S, 30, -1, 33, 1, f, "polished_andesite")
    lay_floor(S, -7, -14, 5, -12, f)
    lay_floor(S, -9, 1, 5, 3, f)
    lay_floor(S, 9, 7, 11, 7, f)
    lay_floor(S, 23, 7, 25, 7, f)
    # ceiling beams across the short side, pillars
    for u in range(u0 + 2, u1, 5):
        for v in range(v0, v1 + 1):
            if S.carved(u, f + h - 1, v):
                S.set(u, f + h - 1, v, "stripped_spruce_log[axis=z]")
    for (u, v) in ((12, -9), (12, 1), (22, -9), (22, 1)):
        for y in range(f, f + h):
            S.set(u, y, v, "polished_andesite" if y < f + h - 1 else "chiseled_stone_bricks")
        S.set(u + 1, f + 2, v, "wall_torch[facing=east]")
    # the front door: open archway with a spruce door (west), an iron door opened from inside (east: the shortcut)
    for v in (-1, 0, 1):
        S.set(33, f - 1, v, "polished_andesite")
    if east:
        for v in (-1, 1):
            for y in range(f, f + 4):
                S.set(32, y, v, "stone_bricks")
        for y in range(f + 2, f + 4):
            S.set(32, y, 0, "stone_bricks")
        S.door(32, f, 0, "east", wood="iron")
        S.set(31, f + 1, 1, "lever[face=wall,facing=west,powered=false]")
    else:
        for v in (-1, 1):
            for y in range(f, f + 4):
                S.set(32, y, v, "stone_bricks")
        for y in range(f + 2, f + 4):
            S.set(32, y, 0, "stone_bricks")
        S.door(32, f, 0, "east", wood="spruce")
    for v in (-10, -5, 4):
        for y in (f + 1, f + 2):
            S.set(32, y, v, "iron_bars")
            S.set(33, y, v, "air")
    # furniture: tables and benches, weapon racks, the guard captain's chest, banners
    for (u, v) in ((16, -6), (17, -6), (18, -6)):
        S.set(u, f, v, "spruce_planks")
        S.set(u, f + 1, v, "candle[candles=2,lit=true,waterlogged=false]" if u == 17 else "air")
        S.stairs(u, f, v - 1, "spruce_stairs", "south")
        S.stairs(u, f, v + 1, "spruce_stairs", "north")
    for v in range(-13, -9):
        S.barrel(28, f, v)
    S.set(28, f + 1, -13, "lantern[hanging=false,waterlogged=false]")
    S.chest(7, f, -13, "east", loot=LOOT + "kg_guard")
    S.set(7, f, -11, "grindstone[face=floor,facing=east]")
    S.set(7, f, -10, "smithing_table")
    for v in (-3, 0, 3):
        S.set(u0 - 1, f + 2, v, "chiseled_stone_bricks")
    for (u, v) in ((10, -3), (20, -3), (26, 3), (14, 4)):
        S.hang(u, f + 3, v)
    if not east:
        S.spawner(24, f, -6, MOB_KNIGHT)
    # barracks: bunks and footlockers
    bu0, bv0, bu1, bv1, _, _ = BARRACKS
    lay_floor(S, bu0, bv0, bu1, bv1, f, lambda u, v: "spruce_planks")
    for i, u in enumerate(range(bu0, bu1, 3)):
        S.bp.bed(S.x(u), f, bv1 - 1, "north", color="red" if east else "blue")
        S.barrel(u + 1, f, bv1)
    S.chest(bu1, f, bv0 + 2, "west", loot=LOOT + "kg_guard")
    S.hang((bu0 + bu1) // 2, f + 3, (bv0 + bv1) // 2)
    # storeroom under the cloak: crates, sacks, the jailer's cell
    su0, sv0, su1, sv1, _, _ = STORE
    lay_floor(S, su0, sv0, su1, sv1, f, lambda u, v: "cobblestone" if hash01(u, v, 9) < 0.5 else "stone_bricks")
    for u in range(su0, su1 + 1, 2):
        S.barrel(u, f, sv1)
        if hash01(u, 3, 4) < 0.5:
            S.barrel(u, f + 1, sv1)
    for u in range(su0, su0 + 6):
        S.set(u, f, sv0 + 4, "iron_bars")
    S.door(su0 + 6, f, sv0 + 4, "south", wood="iron")
    S.set(su0 + 7, f + 1, sv0 + 5, "lever[face=wall,facing=south,powered=false]")
    S.set(su0 + 7, f + 1, sv0 + 4, "stone_bricks")
    S.set(su0 + 7, f, sv0 + 4, "stone_bricks")
    S.set(su0 + 2, f, sv0, "hay_block[axis=y]")
    S.set(su0 + 1, f, sv0 + 1, "skeleton_skull[rotation=4]")
    S.chest(su1, f, sv0 + 1, "west", loot=LOOT + "kg_guard")
    S.hang(su0 + 8, f + 3, 4)
    S.hang(su1 - 2, f + 3, sv1 - 3)
    if not east:
        S.spawner(su0 + 2, f, sv0 + 2, MOB_STRAY)


def girdle_hall(S, east):
    u0, v0, u1, v1, f, h = GIRDLE
    lay_floor(S, u0, v0, u1, v1, f, lambda u, v: "polished_andesite" if abs(v - 4) <= 1 else floor_main(u, v, 2))
    # two rows of oath-stones (W) / counting tables (E), banners, hanging lamps
    if east:
        for u in (-4, 0, 4):
            S.set(u, f, 8, "spruce_planks")
            S.set(u, f + 1, 8, "candle[candles=3,lit=true,waterlogged=false]")
            S.stairs(u, f, 9, "spruce_stairs", "north")
        S.set(-6, f, 9, "lectern[facing=east,has_book=false,powered=false]")
        S.set(-6, f, 0, "bookshelf")
        S.set(-6, f + 1, 0, "bookshelf")
        S.chest(6, f, 10, "west", loot=LOOT + "kg_girdle")
        S.spawner(-5, f, 5, MOB_STRAY)
    else:
        for u in (-5, -1, 3):
            S.set(u, f, 9, "chiseled_stone_bricks")
            S.set(u, f + 1, 9, "candle[candles=4,lit=true,waterlogged=false]")
        S.set(-7, f, 4, "lectern[facing=east,has_book=false,powered=false]")
        S.chest(6, f, 10, "west", loot=LOOT + "kg_girdle")
        S.spawner(-5, f, 6, MOB_GARGOYLE)
    for (u, v) in ((-3, 3), (3, 3), (0, 8)):
        S.hang(u, f + 4, v)
    S.barrel(6, f, 0)
    S.barrel(6, f + 1, 0)


def heart_chamber(S, east):
    u0, v0, u1, v1, f, h = HEART
    lay_floor(S, u0, v0, u1, v1, f, lambda u, v: "polished_andesite" if u >= 6 else floor_main(u, v, 4))
    for v, y in WINDOWS:
        uo = S.M.front(y, v)
        if uo is not None:
            S.set(uo, y, v, "iron_bars")
    # a step up to the windows (a sill to look out of)
    for v in (5, 6, 7):
        S.set(u1, f, v, "polished_andesite_slab[type=bottom,waterlogged=false]")
    if east:
        # the toll archive: shelves, lectern, the drop well (one-way shortcut to the girdle hall)
        for u in range(-6, 0):
            S.set(u, f, 10, "bookshelf")
            S.set(u, f + 1, 10, "bookshelf")
        S.set(1, f, 10, "lectern[facing=north,has_book=false,powered=false]")
        S.chest(-6, f, 1, "east", loot=LOOT + "kg_heart")
        wu0, wv0, wu1, wv1 = WELL
        for u in range(wu0, wu1 + 1):
            for v in range(wv0, wv1 + 1):
                for y in range(FL_GI + GIRDLE[5], f):
                    S.set(u, y, v, "air")
                S.set(u, FL_GI - 1, v, "water")
                S.set(u, FL_GI - 2, v, "water")
                S.set(u, FL_GI - 3, v, "stone_bricks")
        for u in range(wu0 - 1, wu1 + 2):
            for v in range(wv0 - 1, wv1 + 2):
                if wu0 <= u <= wu1 and wv0 <= v <= wv1:
                    continue
                S.set(u, f, v, "stone_brick_wall")
        S.set(wu0 - 1, f, (wv0 + wv1) // 2, "air")
        S.spawner(-5, f, 6, "brasshaven:oathbound_statue")
    else:
        # the wardens' armoury: armour stands, racks, the captain's bunk
        for u in (-5, -2, 1):
            S.bp.entity(S.x(u), f, 10, {"id": "minecraft:armor_stand"})
        S.set(-6, f, 1, "anvil[facing=east]")
        S.bp.bed(S.x(-4), f, 1, "south", color="blue")
        S.chest(4, f, 10, "west", loot=LOOT + "kg_heart")
        S.spawner(-6, f, 6, MOB_KNIGHT)
    for (u, v) in ((-3, 4), (3, 4), (0, 9)):
        S.hang(u, f + 5, v)
    S.barrel(7, f, 10)


def gorget(S, east):
    u0, v0, u1, v1, f, h = GORGET
    lay_floor(S, u0, v0, u1, v1, f)
    lay_floor(S, 2, -11, u1, -7, f)
    for (u, v) in TUNNEL_FLAT:
        S.set(u, f - 1, v, floor_main(u, v, 6))
    prev = f
    for (u, ff) in TUNNEL_STEPS:
        for v in (12, 13, 14):
            if ff > prev:
                S.stairs(u, ff - 1, v, "stone_brick_stairs", "east")
            else:
                S.set(u, ff - 1, v, floor_main(u, v, 6))
        prev = ff
    # the neck stair up into the helm
    for u, ff in NECK_STAIR:
        for v in (-1, 0, 1):
            S.stairs(u, ff - 1, v, "stone_brick_stairs", "east")
    S.hang(4, f + 2, 2)
    S.hang(1, f + 2, 12)
    S.set(5, f, 9, LANT)


def helm(S, east):
    u0, v0, u1, v1, f, h = HELM
    for u in range(2, u1 + 1):
        for v in range(v0, v1 + 1):
            if S.carved(u, f, v):
                S.set(u, f - 1, v, "polished_andesite" if not east else ("gold_block" if (u + v) % 5 == 0
                                                                          else "polished_andesite"))
    for (u, y, v) in S.M.eyes:
        S.set(u, y, v, "iron_bars")
    # a sill under the eyes to look out of
    for v in (-3, -2, 2, 3):
        S.set(u1, f, v, "polished_andesite_slab[type=bottom,waterlogged=false]")
    if east:
        # the treasury of the toll: chests, coin heaps (gold), barrels of tolls
        S.chest(2, f, -4, "south", loot=LOOT + "kg_treasury")
        S.chest(2, f, 4, "north", loot=LOOT + "kg_treasury")
        S.set(4, f, -4, "gold_block")
        S.set(4, f, 4, "gold_block")
        S.set(3, f, -4, "raw_gold_block")
        S.barrel(5, f, -4)
        S.barrel(5, f, 4)
    else:
        # the watchers' cell: a cot, a lectern, a chest with the watch's pay
        S.bp.bed(S.x(3), f, 3, S.f("east"), color="white")
        S.set(3, f, -4, "lectern[facing=south,has_book=false,powered=false]")
        S.chest(5, f, -4, "south", loot=LOOT + "kg_watch")
        S.barrel(2, f, -4)
    S.hang(3, f + 4, 0, reach=8)


def arm_path(S):
    """The parapeted stair riding the south arm from the pauldron to the gauntlet, then onto the lintel."""
    bp = S.bp

    def deck(u, v, ff, rising):
        for y in range(ff, ff + 4):
            S.set(u, y, v, "air")
        S.set(u, ff - 1, v, stair("stone_brick_stairs", "east") if rising else floor_main(u, v, 8))
        y = ff - 2
        n = 0
        while S.air(u, y, v) and n < 14:
            S.set(u, y, v, plate_block(u, y, v, 3))
            y -= 1
            n += 1

    def parapet(u, v, ff, post=False):
        S.set(u, ff - 1, v, "stone_bricks")
        S.set(u, ff, v, "chiseled_stone_bricks" if post else "stone_brick_wall")
        if post:
            S.set(u, ff + 1, v, LANT)
        y = ff - 2
        n = 0
        while S.air(u, y, v) and n < 14:
            S.set(u, y, v, plate_block(u, y, v, 3) if n else trim_block(u, y, v, 3))
            y -= 1
            n += 1
        for yy in range(ff + (2 if post else 1), ff + 4):
            S.set(u, yy, v, "air")
    prev = 55
    for (u, ff) in ARM_PATH:
        rising = ff > prev
        for v in (12, 13, 14):
            deck(u, v, ff, rising)
        parapet(u, 15, ff, post=(u % 4 == 0))
        parapet(u, 11, ff, post=(u % 4 == 2))
        prev = ff
    for (u, v) in TURN:
        if v <= LIN_V:
            continue
        deck(u, v, WALK_F, False)
    for u in range(20, 24):
        parapet(u, 15, WALK_F, post=(u == 23))
    for v in range(LIN_V + 1, 15):
        parapet(23, v, WALK_F, post=(v == 11))
    for v in (8, 9, 10):
        parapet(19, v, WALK_F)


def write_side(bp, s, M):
    S = Side(bp, s, M)
    write_statue(S)
    east = s > 0
    build_spirals(S)
    guard_house(S, east)
    girdle_hall(S, east)
    heart_chamber(S, east)
    gorget(S, east)
    helm(S, east)
    arm_path(S)
    return S


# ------------------------------------------------------------------ the lintel
def lintel(bp):
    def soffit(x):
        return 54 + round(3 * (1 - (x / LIN_X) ** 2))
    for x in range(-LIN_X, LIN_X + 1):
        yb = soffit(x)
        key = abs(x) <= 3
        if key:
            yb = 50
        for z in range(-LIN_V, LIN_V + 1):
            for y in range(yb, LIN_TOP + 1):
                face = abs(z) == LIN_V
                if y == yb:
                    spec = "polished_andesite" if not key else "chiseled_stone_bricks"
                elif y == LIN_TOP:
                    spec = "polished_andesite" if abs(z) <= 1 else ("stone_bricks" if abs(z) < LIN_V else
                                                                    "chiseled_stone_bricks")
                elif face and y in (58, 59):
                    spec = "chiseled_stone_bricks" if x % 4 == 0 else "polished_andesite"
                elif face and y == yb + 1:
                    spec = trim_block(x, y, z, 2)
                elif face and x % 6 == 0:
                    spec = "polished_andesite" if y < 57 else "chiseled_stone_bricks"
                elif face and y == 57:
                    spec = "stone_bricks" if x % 6 in (2, 3, 4) else "polished_andesite"
                elif face and y == 56 and x % 6 in (1, 5):
                    spec = "polished_andesite"
                elif face:
                    h = hash3(x, y, z, 41)
                    spec = "cracked_deepslate_bricks" if h < 0.1 else "deepslate_bricks"
                else:
                    spec = "stone"
                bp.set(x, y, z, spec)
        # cornice under the parapets
        for zs in (-1, 1):
            bp.set(x, LIN_TOP, zs * (LIN_V + 1), stair("stone_brick_stairs", "north" if zs > 0 else "south", "top"))
    # the keystone: proud on both faces, the golden key of the toll
    for x in range(-3, 4):
        for y in range(50, LIN_TOP):
            for zs in (-1, 1):
                bp.set(x, y, zs * (LIN_V + 1), "polished_diorite" if abs(x) == 3 or y in (50, 61) else "calcite")
    for zs in (-1, 1):
        z = zs * (LIN_V + 2)
        for (x, y) in [(0, yy) for yy in range(52, 59)] + [(-1, 58), (1, 58), (-1, 60), (1, 60), (-1, 59),
                                                           (1, 59), (0, 60), (1, 52), (2, 52), (1, 53)]:
            bp.set(x, y, z, "gold_block")
    # deck parapets with lantern posts, gaps where the arm stairs come up
    gaps = set()
    for sx in (-1, 1):
        for u in range(20, 23):
            gaps.add(XW + u if sx < 0 else -XW - u)
    for x in range(-LIN_X, LIN_X + 1):
        for zs in (-1, 1):
            z = zs * LIN_V
            if zs > 0 and x in gaps:
                continue
            post = x % 6 == 0 and abs(x) > 6
            bp.set(x, WALK_F, z, "chiseled_stone_bricks" if post else "stone_brick_wall")
            if post:
                bp.set(x, WALK_F + 1, z, LANT)
    for z in range(-LIN_V, LIN_V + 1):
        for x in (-LIN_X, LIN_X):
            bp.set(x, WALK_F, z, "stone_brick_wall")
    keystone_pavilion(bp)
    # the toll lamp: chains under the keystone holding a cage of light over the square
    for (x, z) in ((-1, 0), (1, 0)):
        for y in range(41, 50):
            bp.set(x, y, z, CHAIN)
    for x in range(-2, 3):
        for z in range(-2, 3):
            for y in range(36, 41):
                edge = abs(x) == 2 or abs(z) == 2
                if y in (36, 40):
                    bp.set(x, y, z, "dark_oak_slab[type=bottom,waterlogged=false]" if y == 40 and edge else
                           ("waxed_cut_copper" if not edge or y == 36 else "air"))
                elif edge and abs(x) == 2 and abs(z) == 2:
                    bp.set(x, y, z, "waxed_cut_copper")
                elif edge:
                    bp.set(x, y, z, "iron_bars")
                else:
                    bp.set(x, y, z, "glowstone" if y == 38 and x == 0 and z == 0 else "air")
    bp.set(0, 39, 0, LANT_H)
    bp.set(0, 37, 0, LANT)


def keystone_pavilion(bp):
    f = WALK_F
    for (x, z) in ((-4, -4), (-4, 4), (4, -4), (4, 4)):
        for y in range(f, f + 6):
            bp.set(x, y, z, "polished_diorite" if y < f + 5 else "chiseled_stone_bricks")
    for x in range(-5, 6):
        for z in range(-5, 6):
            edge = max(abs(x), abs(z)) == 5
            bp.set(x, f + 6, z, "stone_brick_slab[type=bottom,waterlogged=false]" if edge else "polished_andesite")
    for i in range(5):
        r = 5 - i
        y = f + 7 + i
        for x in range(-r, r + 1):
            for z in range(-r, r + 1):
                if max(abs(x), abs(z)) == r:
                    if abs(x) == r and abs(z) <= r and abs(x) >= abs(z):
                        fc = "east" if x < 0 else "west"
                    else:
                        fc = "south" if z < 0 else "north"
                    bp.set(x, y, z, stair("deepslate_tile_stairs", fc))
                elif i == 4:
                    bp.set(x, y, z, "deepslate_tiles")
    bp.set(0, f + 11, 0, "gold_block")
    bp.set(0, f + 12, 0, "gold_block")
    bp.set(0, f + 13, 0, "lightning_rod")
    bp.set(0, f + 5, 0, "bell[attachment=ceiling,facing=east,powered=false]")
    bp.set(-2, f, 2, MOD["waystone"])
    bp.chest(2, f, -3, "west", loot=LOOT + "kg_lintel")
    for (x, z) in ((-3, -3), (3, 3)):
        bp.set(x, f, z, "candle[candles=3,lit=true,waterlogged=false]")
    # the lintel's own guardian: a gargoyle roost on a parapet post a third of the way across
    bp.spawner(-16, WALK_F, -LIN_V + 1, MOB_GARGOYLE)


# ------------------------------------------------------------------ the hall under the gate
def box_room(bp, x0, z0, x1, z1, f, h, wall="stone_bricks", floor=None, keep_air=True):
    """An underground room: masonry shell (1 thick) round air x0..x1, z0..z1, feet f, h high."""
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 1, f + h + 1):
                inside = x0 <= x <= x1 and z0 <= z <= z1 and f <= y < f + h
                if inside:
                    bp.set(x, y, z, "air")
                elif not keep_air or bp.get(x, y, z) is None:
                    bp.set(x, y, z, wall if y >= f else (floor(x, z) if callable(floor) else (floor or wall)))
    if floor:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                bp.set(x, f - 1, z, floor(x, z) if callable(floor) else floor)


def arena_top(r):
    return -3 - round(3 * (r / AR_R) ** 2)


def undercroft(bp):
    f = UND_F
    for x in range(-21, 22):
        for z in range(-21, 22):
            r = math.hypot(x, z)
            if r > AR_WALL + 0.4:
                continue
            for y in range(f - 2, 0):
                if r <= AR_R:
                    top = arena_top(r)
                    if f <= y <= top:
                        bp.set(x, y, z, "air")
                        continue
                    if y == f - 1:
                        ring = int(r) % 4
                        spec = ("chiseled_tuff" if 5.5 <= r < 6.5 or 12 <= r < 13 else
                                "tuff_bricks" if ring == 0 else "polished_tuff")
                    elif y > top and y == top + 1:
                        spec = "tuff_bricks" if (int(math.degrees(math.atan2(z, x))) // 15) % 2 else "polished_tuff"
                    else:
                        spec = "stone_bricks" if hash3(x, y, z, 5) < 0.85 else "cracked_stone_bricks"
                else:
                    spec = "tuff_bricks" if y in (f + 4, f + 9) else ("stone_bricks" if hash3(x, y, z, 6) < 0.8
                                                                      else "mossy_stone_bricks")
                bp.set(x, y, z, spec)
    # pilasters round the wall, soul lanterns on them; ribs across the dome
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        cx, cz = 16.6 * math.cos(a), 16.6 * math.sin(a)
        for x in range(round(cx) - 1, round(cx) + 1):
            for z in range(round(cz) - 1, round(cz) + 1):
                if math.hypot(x, z) > AR_R:
                    continue
                for y in range(f, arena_top(math.hypot(x, z)) + 1):
                    bp.set(x, y, z, "polished_tuff" if y not in (f, f + 8) else "chiseled_tuff")
        ix, iz = round(14.8 * math.cos(a)), round(14.8 * math.sin(a))
        bp.set(ix, f + 5, iz, "soul_lantern[hanging=false,waterlogged=false]")
        bp.set(ix, f + 4, iz, "polished_tuff")
        bp.set(ix, f, iz, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the grate under the town well: daylight on the fight
    for x in (-1, 0, 1):
        for z in (-1, 0, 1):
            for y in range(arena_top(0) + 1, 0):
                bp.set(x, y, z, "iron_bars" if y == -1 else "air")
    bp.boss_seal(0, f - 1, 0, BOSS, 15)
    # doors east (in) and west (out), mist at both
    for zz in (-1, 0, 1):
        for x in range(17, 21):
            for sx in (-1, 1):
                for y in range(f, f + 4):
                    bp.set(sx * x, y, zz, "air")
                bp.set(sx * x, f - 1, zz, "polished_tuff")
    bp.mist(18, f, -1, 18, f + 3, 1)
    bp.mist(-18, f, -1, -18, f + 3, 1)
    # the vault under the floor: sealed bars over a ladder by the north wall
    vf = VAULT_F
    box_room(bp, -6, -15, 6, -6, vf, 5, wall="tuff_bricks", floor=lambda x, z: "polished_tuff")
    bp.set(0, f - 1, -15, MOD["vault_bars"])
    bp.set(0, f - 2, -15, "air")
    bp.ladder(0, vf, -15, f - 2, "south")
    for y in range(vf, f - 1):
        bp.set(0, y, -16, "tuff_bricks")
    for x in range(-5, 6, 2):
        bp.set(x, vf - 1, -10, "gold_block" if x == -1 else "chiseled_tuff")
    bp.chest(-6, vf, -8, "east", loot=LOOT + "kg_vault")
    bp.chest(6, vf, -8, "west", loot=LOOT + "kg_vault")
    bp.chest(-3, vf, -6, "north", loot=LOOT + "kg_vault")
    for (x, z) in ((-5, -14), (5, -14), (-5, -6), (5, -6)):
        bp.set(x, vf + 4, z, SOUL_H)
    bp.set(3, vf, -14, "smithing_table")
    passages(bp)


def passages(bp):
    """Under the town: the keepers' chapel and the narrow way to the arena (east, in); the same in the west (out),
    closed toward the west stair by an iron door that opens from the arena side."""
    f = UND_F

    def fl(x, z):
        return "polished_andesite" if hash01(x, z, 71) < 0.5 else "stone_bricks"
    for sx in (-1, 1):
        # antechamber at the foot of the plinth stair, passage north, passage west to the arena door
        xa0, xa1 = sorted((sx * 19, sx * 25))
        box_room(bp, xa0, 10, xa1, 18, f, 5, floor=fl)
        xb0, xb1 = sorted((sx * 20, sx * 22))
        box_room(bp, xb0, 2, xb1, 9, f, 4, floor=fl)
        xc0, xc1 = sorted((sx * 19, sx * 22))
        box_room(bp, xc0, -1, xc1, 1, f, 4, floor=fl)
        for z in range(14, 17):                      # link to the stair foot (local u 26 -> |x| 26)
            bp.set(sx * 26, f - 1, z, fl(sx * 26, z))
        for z in (12, 16):
            bp.set(sx * 24, f + 3, z, SOUL_H)
        bp.set(sx * 21, f + 3, 5, SOUL_H)
    # east: the keepers' chapel and its site of grace (the waystone before the boss)
    bp.set(23, f, 17, MOD["waystone"])
    bp.set(20, f, 17, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(20, f, 11, "lectern[facing=east,has_book=false,powered=false]")
    bp.chest(24, f, 11, "north", loot=LOOT + "kg_guard")
    # west: an iron door across the passage, its lever on the arena side
    for x in (-22, -20):
        for y in range(f, f + 4):
            bp.set(x, y, 6, "stone_bricks")
    for y in (f + 2, f + 3):
        bp.set(-21, y, 6, "stone_bricks")
    bp.door(-21, f, 6, "south", wood="iron")
    bp.set(-20, f + 1, 5, "lever[face=wall,facing=north,powered=false]")


# ------------------------------------------------------------------ terrain: the pass
AX0, AX1, AZ0, AZ1 = -124, 124, -124, 124
AY = 64
XS = np.arange(AX0, AX1 + 1)
ZS = np.arange(AZ0, AZ1 + 1)
GX, GZ = np.meshgrid(XS, ZS, indexing="ij")


def _vh(ix, iz, seed):
    n = ((ix * 73856093) ^ (iz * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, z, scale, seed):
    fx, fz = np.asarray(x, float) / scale, np.asarray(z, float) / scale
    ix, iz = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _vh(ix, iz, seed), _vh(ix + 1, iz, seed)
    c, d = _vh(ix, iz + 1, seed), _vh(ix + 1, iz + 1, seed)
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz


def fbm(x, z, scale, seed):
    return 0.6 * vnoise(x, z, scale, seed) + 0.3 * vnoise(x, z, scale / 2.3, seed + 7) + \
        0.1 * vnoise(x, z, scale / 5.1, seed + 13)


# the road: from the south marker round the spur to the town, and on north
ROAD_S = [(10, 124), (12, 108), (-2, 96), (-16, 84), (-15, 70), (-6, 56), (0, 42), (0, 13)]
ROAD_N = [(0, -13), (0, -50), (-4, -80), (-10, -104), (-8, -124)]
SPURS = [(36, 86, 40, 13, 26, 1), (-60, 60, 24, 11, 15, 2), (56, -82, 26, 13, 21, 3), (-52, -98, 28, 13, 17, 4)]


def road_dist():
    d = np.full(GX.shape, 999.0)
    for pts in (ROAD_S, ROAD_N):
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            vx, vz = bx - ax, bz - az
            L2 = vx * vx + vz * vz
            t = np.clip(((GX - ax) * vx + (GZ - az) * vz) / L2, 0, 1)
            d = np.minimum(d, np.hypot(GX - ax - vx * t, GZ - az - vz * t))
    return d


ROAD_D = road_dist()


def heights():
    ax = np.abs(GX).astype(float)
    side = np.where(GX < 0, 0, 50)
    n1 = fbm(GX, GZ, 23.0, 11)
    n2 = fbm(GX, GZ, 7.0, 12)
    nz = fbm(side + 0 * GX, GZ, 26.0, 14)          # varies along the pass, differently on each side
    nc = fbm(side + 0 * GX, GZ, 17.0, 15)
    d = ax - (88 + 14 * nz)
    hf = np.clip(d, 0, None) * (1.4 + 0.9 * nc) * (0.8 + 0.4 * n1)
    crest = 30 + 26 * nc + 6 * n1
    hf = np.minimum(hf, crest)
    hf = hf - np.clip(ax - 114, 0, None) * 2.2
    # rough rock and gullies: ravines down the slope
    hf = hf + (d > 0) * 5 * (n2 - 0.5)
    hf = hf - (d > 0) * 5 * np.clip(np.sin(GZ / 7.5 + 5 * n1) - 0.55, 0, None)
    hf *= 1 - 0.5 * np.clip((np.abs(GZ) - 92) / 32.0, 0, 1)
    h = np.where(d > 0, hf, 0.0)
    for (cx, cz, rx, rz, hh, sd) in SPURS:
        th = np.arctan2(GZ - cz, GX - cx)
        e = ((GX - cx) / rx) ** 2 + ((GZ - cz) / rz) ** 2
        e = e * (0.75 + 0.5 * fbm(th * 6, 0 * th, 3.0, 40 + sd))
        hs = hh * np.clip(1 - e, 0, 1) ** 0.55 + 3.5 * (n2 - 0.5) * (e < 1)
        h = np.maximum(h, hs)
    # the road and its verges stay at the valley floor
    h = np.minimum(h, np.clip((ROAD_D - 4) * 1.3, 0, None))
    return np.clip(h, 0, AY - 2)


def terrain(bp):
    H = heights()
    S = np.zeros((len(XS), AY, len(ZS)), bool)
    for y in range(AY):
        S[:, y, :] = y < np.floor(H)
    air = ~S
    near = air.copy()
    for _ in range(3):
        n = near.copy()
        n[1:, :, :] |= near[:-1, :, :]
        n[:-1, :, :] |= near[1:, :, :]
        n[:, 1:, :] |= near[:, :-1, :]
        n[:, :-1, :] |= near[:, 1:, :]
        n[:, :, 1:] |= near[:, :, :-1]
        n[:, :, :-1] |= near[:, :, 1:]
        near = n
    shell = S & near
    shell[0], shell[-1] = shell[0] | S[0], shell[-1] | S[-1]
    shell[:, :, 0] |= S[:, :, 0]
    shell[:, :, -1] |= S[:, :, -1]
    top = S.copy()
    top[:, :-1, :] &= ~S[:, 1:, :]
    jit = fbm(GX, GZ, 9.0, 31)
    for i, y, k in np.argwhere(shell).tolist():
        x, z = int(XS[i]), int(ZS[k])
        bp.set(x, y, z, rock_block(x, y, z, bool(top[i, y, k]), float(jit[i, k])))
    return H, top


def rock_block(x, y, z, top, jit):
    h = hash3(x, y, z, 7)
    if top:
        if y >= 34 + 8 * jit:
            return "snow_block" if h < 0.8 else "stone"
        if y >= 22 + 10 * jit:
            return "stone" if h < 0.55 else ("andesite" if h < 0.8 else "grass_block[snowy=false]")
        return "grass_block[snowy=false]" if h < 0.82 else ("coarse_dirt" if h < 0.92 else "moss_block")
    s = y + int(4 * jit)
    band = ("stone", "andesite", "stone", "tuff", "stone", "diorite", "andesite", "stone")
    if y < 6 and h < 0.25:
        return "mossy_cobblestone"
    return band[(s // 4) % len(band)]


# ------------------------------------------------------------------ the toll town, road and approach
def road(bp):
    for i, k in np.argwhere(ROAD_D <= 2.4).tolist():
        x, z = int(XS[i]), int(ZS[k])
        if abs(z) <= 13 and abs(x) <= 16:
            continue
        h = hash01(x, z, 51)
        centre = ROAD_D[i, k] <= 1.2
        bp.set(x, 0, z, "dirt_path" if centre and h < 0.75 else ("gravel" if h < 0.45 else
                                                                   ("cobblestone" if h < 0.75 else "dirt_path")))
    # lamp posts along the road every ~14 blocks
    for pts in (ROAD_S, ROAD_N):
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, bz - az)
            nx, nz = -(bz - az) / L, (bx - ax) / L
            for t in np.arange(7, L, 14):
                x = round(ax + (bx - ax) * t / L + nx * 4)
                z = round(az + (bz - az) * t / L + nz * 4)
                if abs(z) < 16:
                    continue
                bp.set(x, 0, z, "cobblestone")
                bp.set(x, 1, z, "cobblestone_wall")
                bp.set(x, 2, z, "spruce_fence")
                bp.set(x, 3, z, "spruce_fence")
                bp.set(x, 4, z, LANT)


def square(bp):
    for x in range(-16, 17):
        for z in range(-13, 14):
            h = hash01(x, z, 61)
            if abs(x) <= 2:
                spec = "polished_andesite" if h < 0.7 else "stone_bricks"
            elif (x * x + z * z) ** 0.5 < 6:
                spec = "stone_bricks" if h < 0.8 else "chiseled_stone_bricks"
            else:
                spec = "cobblestone" if h < 0.45 else ("stone_bricks" if h < 0.8 else "mossy_cobblestone")
            bp.set(x, 0, z, spec)
    # the well: a ring of stone with a roof on posts; it looks down through the grate into the hall under the gate
    for x in range(-2, 3):
        for z in range(-2, 3):
            if max(abs(x), abs(z)) == 2:
                bp.set(x, 0, z, "stone_bricks")
                bp.set(x, 1, z, "stone_brick_wall")
            else:
                bp.set(x, 0, z, "air")
    for (x, z) in ((-2, -2), (2, 2), (-2, 2), (2, -2)):
        for y in range(2, 5):
            bp.set(x, y, z, "spruce_fence")
    for x in range(-3, 4):
        for z in range(-3, 4):
            bp.set(x, 5, z, "spruce_slab[type=bottom,waterlogged=false]" if max(abs(x), abs(z)) == 3 else
                   "spruce_planks")
    bp.set(0, 4, 0, CHAIN)
    bp.set(0, 3, 0, LANT_H)
    # the entrance waystone, market stalls, a cart, braziers at the plinth doors
    bp.set(-7, 1, 4, MOD["waystone"])
    for (x0, z0, wool) in ((-13, -9, "red_wool"), (9, -9, "yellow_wool"), (9, 6, "blue_wool")):
        for (dx, dz) in ((0, 0), (3, 0), (0, 3), (3, 3)):
            for y in range(1, 4):
                bp.set(x0 + dx, y, z0 + dz, "spruce_fence")
        for dx in range(-1, 5):
            for dz in range(0, 4):
                bp.set(x0 + dx, 4, z0 + dz, wool if (dx + dz) % 2 else "white_wool")
        bp.set(x0 + 1, 1, z0 + 1, "barrel[facing=up,open=false]")
        bp.set(x0 + 2, 1, z0 + 1, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x0 + 2, 2, z0 + 1, "candle[candles=2,lit=true,waterlogged=false]")
    bp.chest(-12, 1, -7, "south", loot=LOOT + "kg_town")
    for sx in (-1, 1):
        for z in (-4, 4):
            bp.set(sx * 17, 1, z, "cobblestone_wall")
            bp.set(sx * 17, 2, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for x in (-5, -4):
        bp.set(x, 1, 9, "hay_block[axis=y]")
    bp.set(-5, 2, 9, "hay_block[axis=x]")


def toll_gate(bp):
    """The toll barrier across the road south of the square: two stone booths, a timber gallery over the road."""
    z0, z1 = 13, 16
    for sx in (-1, 1):
        xa, xb = sorted((sx * 4, sx * 8))
        for x in range(xa, xb + 1):
            for z in range(z0, z1 + 1):
                edge = x in (xa, xb) or z in (z0, z1)
                bp.set(x, 0, z, "stone_bricks")
                for y in range(1, 5):
                    bp.set(x, y, z, ("stone_bricks" if y < 4 else "spruce_planks") if edge else "air")
                bp.set(x, 5, z, "spruce_planks")
        door_x = sx * 4
        bp.door(door_x, 1, 14, "west" if sx > 0 else "east", wood="spruce")
        bp.set(sx * 6, 2, z1, "glass_pane")
        bp.set(sx * 6, 2, z0, "glass_pane")
        bp.chest(sx * 7, 1, z0 + 1, "west" if sx > 0 else "east", loot=LOOT + "kg_town" if sx < 0 else None)
        bp.set(sx * 6, 4, 14, LANT_H)
    # the gallery across the road at y 5..6, a pent roof, the raised barrier pole
    for x in range(-8, 9):
        for z in range(z0, z1 + 1):
            bp.set(x, 6, z, "spruce_slab[type=bottom,waterlogged=false]" if z in (z0, z1) else "spruce_planks")
        bp.set(x, 5, z0 + 1, "stripped_spruce_log[axis=x]" if abs(x) < 4 else "spruce_planks")
    for x in range(-3, 4):
        bp.set(x, 5, z0, "air")
        bp.set(x, 5, z1, "air")
    bp.set(0, 4, 14, LANT_H)
    for y in range(1, 5):
        bp.set(3, y, 17, "stripped_spruce_log[axis=y]")
    bp.set(3, 0, 17, "stone_bricks")


def house(bp, x0, z0, x1, z1, door, kind, loot=None, roof_axis="x"):
    """A stone-and-timber house of one tall storey, door (x, z, facing) on the road side."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            bp.set(x, 0, z, "cobblestone" if edge else "spruce_planks")
            for y in range(1, 5):
                if corner or (edge and (x - x0) % 4 == 0 and z in (z0, z1)) or (edge and (z - z0) % 4 == 0 and
                                                                                  x in (x0, x1)):
                    spec = "dark_oak_log[axis=y]"
                elif edge:
                    spec = "cobblestone" if y == 1 else "spruce_planks"
                else:
                    spec = "air"
                bp.set(x, y, z, spec)
            bp.set(x, 5, z, "dark_oak_planks" if edge else "spruce_planks")
    bp.gable_roof(x0, z0, x1, z1, 6, "deepslate_tile_stairs", ridge_axis=roof_axis, overhang=1,
                  fill="spruce_planks")
    # windows
    for x in range(x0 + 2, x1 - 1, 4):
        for z in (z0, z1):
            bp.set(x, 2, z, "glass_pane")
            bp.set(x, 3, z, "glass_pane")
    for z in range(z0 + 2, z1 - 1, 4):
        for x in (x0, x1):
            bp.set(x, 2, z, "glass_pane")
            bp.set(x, 3, z, "glass_pane")
    dx, dz, fc = door
    bp.set(dx, 2, dz, "air")
    bp.door(dx, 1, dz, fc, wood="spruce")
    ox, oz = DIRV[fc]
    bp.set(dx + ox, 0, dz + oz, "cobblestone")
    bp.set(dx - ox, 1, dz - oz, "air")
    bp.set(dx - ox, 2, dz - oz, "air")
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    bp.set(cx, 4, cz, LANT_H)
    ix0, iz0, ix1, iz1 = x0 + 1, z0 + 1, x1 - 1, z1 - 1
    far_x = ix0 if dx >= cx else ix1
    if kind == "office":
        bp.set(far_x, 1, iz0, "lectern[facing=south,has_book=false,powered=false]")
        bp.set(cx, 1, cz, "spruce_planks")
        bp.set(cx, 2, cz, "candle[candles=3,lit=true,waterlogged=false]")
        for z in range(iz0, iz1 + 1, 2):
            bp.set(far_x, 1, z, "bookshelf") if z != iz0 else None
        bp.chest(far_x, 1, iz1, "east" if far_x == ix0 else "west", loot=loot)
    elif kind == "inn":
        bp.bed(far_x, 1, iz0, "south", color="red")
        bp.bed(far_x, 1, iz1 - 1, "south", color="green")
        bp.set(cx, 1, cz, "spruce_planks")
        bp.set(cx, 1, cz + 1, "spruce_planks")
        bp.set(ix0 if far_x == ix1 else ix1, 1, iz1, "smoker[facing=north,lit=false]")
        bp.set(cx, 1, iz1, "barrel[facing=up,open=false]")
        bp.chest(cx + 1, 1, iz0, "south", loot=loot)
    elif kind == "smithy":
        bp.set(far_x, 1, iz0, "blast_furnace[facing=south,lit=false]")
        bp.set(far_x, 1, iz0 + 1, "anvil[facing=east]")
        bp.set(cx, 1, iz1, "grindstone[face=floor,facing=north]")
        bp.set(cx - 1, 1, iz1, "smithing_table")
        bp.chest(far_x, 1, iz1, "east" if far_x == ix0 else "west", loot=loot)
    elif kind == "stable":
        for z in range(iz0, iz1 + 1):
            bp.set(far_x, 1, z, "hay_block[axis=y]" if z % 2 else "air")
        bp.set(cx, 1, iz0, "barrel[facing=up,open=false]")
        bp.set(cx, 1, iz1, "composter[level=3]")
        bp.chest(cx + 1, 1, iz1, "north", loot=loot)
    else:
        bp.bed(far_x, 1, iz0, "south", color="brown")
        bp.set(cx, 1, iz1, "barrel[facing=up,open=false]")
        bp.set(far_x, 1, iz1, "crafting_table")


def town(bp):
    square(bp)
    toll_gate(bp)
    house(bp, -17, 18, -9, 28, (-9, 23, "east"), "office", LOOT + "kg_town", roof_axis="z")
    house(bp, 8, 18, 17, 30, (8, 24, "west"), "inn", LOOT + "kg_town", roof_axis="z")
    house(bp, -17, -28, -9, -18, (-9, -23, "east"), "smithy", LOOT + "kg_town", roof_axis="z")
    house(bp, 8, -30, 17, -18, (8, -24, "west"), "stable", None, roof_axis="z")
    house(bp, -16, 32, -10, 39, (-10, 35, "east"), "home", roof_axis="z")
    house(bp, 9, -42, 15, -35, (9, -38, "west"), "home", roof_axis="z")
    # paved yards in front of the doors (the square already reaches |z| 13)
    for (xa, xb, za, zb) in ((-8, -3, 18, 28), (3, 7, 18, 30), (-8, -3, -28, -18), (3, 7, -30, -18)):
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if bp.get(x, 0, z) is None:
                    bp.set(x, 0, z, "cobblestone" if hash01(x, z, 66) < 0.5 else "gravel")


def approach(bp, H):
    """The marker where the approach begins, a ruined watch post as a satellite, boulders along the way."""
    mx, mz = 6, 120
    bp.set(mx, 0, mz, "stone_bricks")
    for y in range(1, 4):
        bp.set(mx, y, mz, "mossy_stone_bricks" if y == 1 else "stone_bricks")
    bp.set(mx, 4, mz, "chiseled_stone_bricks")
    bp.set(mx, 5, mz, LANT)
    # the ruined watch post (round, broken from the top)
    cx, cz = 22, 108
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.4:
                bp.set(x, 0, z, "cobblestone" if d > 3.4 else "spruce_planks")
            if 3.4 < d <= 4.4:
                top = 3 + int(7 * hash01(x, z, 81) * (1 if x < cx else 0.5))
                for y in range(1, top):
                    bp.set(x, y, z, "stone_bricks" if hash3(x, y, z, 82) < 0.7 else "mossy_stone_bricks")
            elif d <= 3.4:
                for y in range(1, 5):
                    bp.set(x, y, z, "air")
    for y in (1, 2):
        bp.set(cx - 4, y, cz, "air")
    bp.chest(cx + 2, 1, cz - 2, "west", loot=LOOT + "kg_town")
    bp.set(cx - 1, 1, cz + 2, "campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    for i in range(18):
        x = int(-30 + 60 * hash01(i, 1, 91))
        z = int(-118 + 236 * hash01(i, 2, 91))
        if abs(z) < 50 and abs(x) < 30:
            continue
        ii, kk = x - AX0, z - AZ0
        if ROAD_D[ii, kk] < 6 or H[ii, kk] >= 1:
            continue
        boulder(bp, x, 1, z, r=2, seed=i)


def plants(bp, H, top):
    """Spruces on the flanks and spurs, shrubs and flowers on the valley floor away from the road."""
    placed = []
    order = sorted(((int(XS[i]), int(ZS[k])) for i, k in np.argwhere((H >= 3) & (H < 30)).tolist()),
                   key=lambda p: hash01(p[0], p[1], 97))
    for (x, z) in order:
        if len(placed) >= 70:
            break
        ii, kk = x - AX0, z - AZ0
        y = int(np.floor(H[ii, kk]))
        if y < 1 or not top[ii, y - 1, kk]:
            continue
        if any(abs(x - a) < 6 and abs(z - b) < 6 for a, b in placed):
            continue
        if abs(x) < 90 and abs(z) < 40 or abs(x) > 118 or abs(z) > 118:
            continue
        if bp.get(x, y, z) is not None or bp.get(x, y - 1, z) not in ("minecraft:grass_block", "minecraft:moss_block",
                                                                         "minecraft:coarse_dirt"):
            continue
        spruce(bp, x, y, z, h=7 + int(hash01(x, z, 98) * 6), seed=x * 7 + z)
        bp.set(x, y - 1, z, "podzol[snowy=false]")
        placed.append((x, z))
    for i in range(160):
        x = int(-80 + 160 * hash01(i, 5, 99))
        z = int(-120 + 240 * hash01(i, 6, 99))
        ii, kk = x - AX0, z - AZ0
        if ROAD_D[ii, kk] < 4 or (abs(x) < 36 and abs(z) < 44) or H[ii, kk] >= 1:
            continue
        if abs(x) > 18 and abs(z) < 30:
            continue
        if bp.get(x, 0, z) is not None or bp.get(x, 1, z) is not None:
            continue
        h = hash01(i, 7, 99)
        bp.set(x, 0, z, "grass_block[snowy=false]")
        bp.set(x, 1, z, "short_grass" if h < 0.6 else ("cornflower" if h < 0.75 else
                                                        ("oxeye_daisy" if h < 0.9 else "allium")))


def own_foundations(bp, depth=4):
    """The gate carries shallow foundations of its own (foundation=False: the pipeline's 12-deep columns and earth
    skirt round every scattered ground-layer cell of the road, the town and the flank feet would cost ~160k entries):
    every ground-layer column goes down ``depth`` blocks, earth under soil, stone under masonry, stopping on anything
    built. The beard of the jigsaw fills the rest of a dip."""
    cols = [(x, z, v[0]) for (x, y, z), v in bp.blocks.items() if y == 0 and v[0] != "minecraft:air"]
    for x, z, name in cols:
        short = name.split(":")[1]
        soil = short in ("grass_block", "podzol", "dirt", "coarse_dirt", "dirt_path", "gravel", "moss_block",
                         "snow_block")
        for d in range(1, depth + 1):
            if bp.get(x, -d, z) is not None:
                break
            bp.set(x, -d, z, "dirt" if soil and d <= 2 else "stone")


# ------------------------------------------------------------------ builder
_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        _MODEL = statue_model()
    return _MODEL


def kneeling_gate(bp):
    H, top = terrain(bp)
    M = model()
    write_side(bp, -1, M)
    write_side(bp, 1, M)
    lintel(bp)
    undercroft(bp)
    road(bp)
    town(bp)
    approach(bp, H)
    plants(bp, H, top)
    own_foundations(bp)


def _w(s, u):
    return XW + u if s < 0 else -XW - u


# camera spots for the CI focus run: (name, feet, look at), blueprint coordinates
VIEWS = [
    ("guard_hall", (_w(-1, 26), FL_G, -2), (_w(-1, 8), FL_G + 2, -8)),
    ("girdle_hall", (_w(-1, 5), FL_GI, 8), (_w(-1, -6), FL_GI + 2, 2)),
    ("heart_chamber", (_w(1, -4), FL_H, 3), (_w(1, 8), FL_H + 3, 6)),
    ("arm_stair", (_w(-1, 9), 55, 13), (0, WALK_F + 4, 0)),
    ("lintel_walk", (-24, WALK_F, -2), (12, WALK_F + 4, 0)),
    ("treasury", (_w(1, 1), FL_HEAD, 0), (_w(1, 6), FL_HEAD + 2, 0)),
    ("arena", (15, UND_F, 0), (-12, UND_F + 5, 0)),
]


register(StructureDef(
    "kneeling_gate", "overworld",
    ["meadow", "grove", "snowy_slopes", "stony_peaks", "windswept_hills", "windswept_gravelly_hills",
     "windswept_forest"],
    [Piece("gate", kneeling_gate, views=VIEWS)],
    spacing=80, separation=32, adaptation="none", max_distance=128, foundation=False,
    spawns=[("brasshaven:skeleton_knight", 6, 1, 2), ("minecraft:stray", 4, 1, 2), ("brasshaven:oathbound_statue", 3, 1, 1)],
    creatures=[("oathbound_statue", 6)],
    title_fr="La Porte agenouillée", title_en="Kneeling Gate"))

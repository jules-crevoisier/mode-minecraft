"""Fallen Colossus (Colosse abattu): a 155-long statue of an armoured knight, stone under bronze plate, fallen on its
side across a valley floor and half sunk into the earth. Colossal tier (tools/BUILDING.md §1, §12 concept 3, §15).

Silhouette (one noun phrase, §15.1): a giant knight lying on his side, the helmet turned to the sky with its crest,
the right pauldron as the summit, the right knee drawn up into an arch, the right hand reaching out over the grass.

Layout, ground y = 0; the head lies to the west (x < 0), the chest faces south (z > 0), the right side is up:
  * the valley: a soil field with heaped berms along the body (it sank in), a furrow of rubble and bronze plates
    under the breach, the shattered sword lying apart behind the back (north), treasure hunters' camp on the
    approach path (south-east) as the human scale cue;
  * the way in is the broken wrist: the forearm is a tunnel to the elbow chamber, then a stair climbs the upper arm
    and comes out on a balcony high in the rib hall (the release after the compression of the arm);
  * the rib hall: the chest is a 30-high vault of stone ribs, opened to the sky by a breach in the breastplate. A stair
    goes down to its floor (the hub, where the Bronze Sentinel stands guard), the grand stair climbs back up to the gorget dais and its waystone;
  * side routes: the shoulder (a stair from the balcony up into the pauldron loft, a window north over the sword) and
    the hip (the crypt in the pelvis, then a tunnel down the left leg out of the knee: a second way in, a loop);
  * the neck tunnel (compression) leads into the helmet: the boss arena of the Colossus's Heart (radius 14, ceiling
    16) under the visor bars;
    the reward vault is below its floor (sealed bars), with a one-way iron door out through the cheek.
Loot gradient (§15.6): forearm and camp tier 1, hall / crypt / loft tier 2, vault tier 3. One secret: a hatch in a
dark corner of the hall floor opens onto the knight's tomb below.
Palette: bronze (exposed -> weathered -> oxidized copper, darker low, verdigris high), stone mail (tuff, andesite,
stone), masonry inside (stone and tuff bricks), dark straps, gold only at the focal points (brow, buckle, pommel).
"""
import math

from ..arch import big_oak, birch, bush, oak, spruce, stair
from ..defs import Piece, StructureDef, register
from ..megakit import fbm, hash01, hash3
from ..parts import LOOT, MOB, MOD
from .walking_fortress import light_fill

# the colossus' own heart wakes in the helmet (entity/boss/ColossusHeart.java); its old champion, the Bronze
# Sentinel, now stands guard in the rib hall on the way up
BOSS = "brasshaven:colossus_heart"
SENTINEL = "brasshaven:bronze_sentinel"

# ------------------------------------------------------------------ dimensions
YC = 15                                  # body axis height (torso, pelvis): the right flank is up
HELM_C, HELM_R, HELM_IN = (-60, 16, 0), (19, 17, 17), (15, 11, 15)
ARENA_F = 14                             # feet level in the arena
VAULT_F = 3                              # feet level of the reward vault under it
HALL_X0, HALL_X1 = -36, -6               # the rib hall's length (x)
HALL_F = 3                               # feet level on the hall floor
BALC_F = 15                              # balcony and arm landing
LOFT_F = 27                              # pauldron loft
RIBS = (-34, -29, -24, -19, -14, -9)     # transverse ribs (2 thick: x, x + 1)

R_SHOULDER, R_ELBOW, R_WRIST = (-40, 28, 6), (-38, 6, 34), (-38, 5, 61)
R_HIP, R_KNEE, R_ANKLE, R_TOE = (6, 22, 4), (30, 37, 10), (56, 7, 15), (62, 3, 25)
L_HIP, L_KNEE, L_ANKLE, L_TOE = (6, 7, -3), (36, 6, -5), (62, 6, -4), (66, 3, 7)
PAULDRON_C, PAULDRON_R = (-38, 31, 2), (12, 17, 15)
PELVIS_C, PELVIS_R = (2, 14, 0), (13, 16, 13)

GROUND_C, GROUND_R = (-5, 20), (96, 76)  # the valley floor this piece reshapes (ellipse)
SWORD_Z = -36

# entrances / exits on the ground: the berms and the rubble keep clear of them
DOORS = [(-38, 61), (36, 6), (-58, 14)]

FLOOR_MAIN = ("polished_andesite", "andesite", "stone_bricks")
FLOOR_SIDE = ("cobblestone", "mossy_cobblestone", "andesite", "stone_bricks")


# ------------------------------------------------------------------ geometry
def seg(p, a, b):
    """Distance from p to the segment a-b, and the position t (0..1) of the closest point."""
    vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    L2 = vx * vx + vy * vy + vz * vz
    t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy + (p[2] - a[2]) * vz) / L2))
    cx, cy, cz = a[0] + vx * t, a[1] + vy * t, a[2] + vz * t
    return math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2), t


def torso_dims(x):
    """(a, front, back) semi-axes of the torso cross-section at x (a vertical: the body's width), or None."""
    if x < -45 or x > -1:
        return None
    t = (x + 44) / 42.0
    a = 21 - 7 * max(0.0, t) ** 1.5
    bf = 12 + 4 * max(0.0, math.sin(math.pi * t * 1.25))
    bb = 12 - 1.5 * t
    if x < -40:                                       # the shoulder line rounds into the neck
        s = 1 - ((-40 - x) / 4.6) ** 2
        if s <= 0:
            return None
        s = math.sqrt(s)
        a, bf, bb = a * s, bf * s, bb * s
    return a, bf, bb


def torso_rho(x, y, z, shrink=0.0):
    d = torso_dims(x)
    if d is None:
        return 9.0
    a, bf, bb = d
    b = bf if z > 0 else bb
    a, b = a - shrink, b - shrink
    if a <= 0.5 or b <= 0.5:
        return 9.0
    return math.sqrt(((y - YC) / a) ** 2 + (z / b) ** 2)


def ell(p, c, r):
    return ((p[0] - c[0]) / r[0]) ** 2 + ((p[1] - c[1]) / r[1]) ** 2 + ((p[2] - c[2]) / r[2]) ** 2


# ------------------------------------------------------------------ the body (a dict of cells -> part)
class Body:
    def __init__(self):
        self.cells = {}        # (x, y, z) -> part: bronze, cut, mail, dark, gold, rib
        self.carve = set()     # dungeon air
        self.torso = set()     # torso cells (the breach only opens these)

    def put(self, p, part):
        if p[1] >= -3:
            self.cells[p] = part

    def capsule(self, a, b, ra, rb, part, t0=0.0, t1=1.0, ymin=-3):
        r = max(ra, rb) + 1
        L = math.dist(a, b)
        for x in range(int(min(a[0], b[0]) - r), int(max(a[0], b[0]) + r) + 1):
            for y in range(max(ymin, int(min(a[1], b[1]) - r)), int(max(a[1], b[1]) + r) + 1):
                for z in range(int(min(a[2], b[2]) - r), int(max(a[2], b[2]) + r) + 1):
                    d, t = seg((x, y, z), a, b)
                    if t0 <= t <= t1 and d <= ra + (rb - ra) * t + 0.3:
                        if part == "plate":       # armour: rims at both ends of the plate, verdigris between
                            along = t * L
                            edge = along - t0 * L < 1.5 or t1 * L - along < 1.5
                            self.put((x, y, z), "cut" if edge else "bronze")
                        else:
                            self.put((x, y, z), part)

    def bands(self, a, b, ra, rb, ts, part="cut", extra=1.0, w=0.8):
        """Raised rings around a limb at the positions ts (0..1): the plate edges stand one block proud."""
        L = math.dist(a, b)
        r = max(ra, rb) + extra + 1
        for x in range(int(min(a[0], b[0]) - r), int(max(a[0], b[0]) + r) + 1):
            for y in range(max(-3, int(min(a[1], b[1]) - r)), int(max(a[1], b[1]) + r) + 1):
                for z in range(int(min(a[2], b[2]) - r), int(max(a[2], b[2]) + r) + 1):
                    d, t = seg((x, y, z), a, b)
                    if 0 < t < 1 and any(abs(t - tb) * L <= w for tb in ts) and d <= ra + (rb - ra) * t + extra + 0.3:
                        self.put((x, y, z), part)

    def ellipsoid(self, c, r, part, cond=None):
        for x in range(int(c[0] - r[0]) - 1, int(c[0] + r[0]) + 2):
            for y in range(max(-3, int(c[1] - r[1]) - 1), int(c[1] + r[1]) + 2):
                for z in range(int(c[2] - r[2]) - 1, int(c[2] + r[2]) + 2):
                    if ell((x, y, z), c, r) <= 1.0 and (cond is None or cond(x, y, z)):
                        self.put((x, y, z), part(x, y, z) if callable(part) else part)

    def remove(self, p):
        self.cells.pop(p, None)

    def air(self, p):
        self.cells.pop(p, None)
        self.carve.add(p)


# ------------------------------------------------------------------ shapes
def helmet(B):
    """Great helm turned to the sky: a flat face plate on top with a proud cross round the barred T of the visor,
    breathing holes, a gold brow band, a crest fin over the crown (west), broken near the ground."""
    cx, cy, cz = HELM_C
    face = cy + 13                                           # the flat face plate

    def part(x, y, z):
        if abs(x - (cx - 8)) <= 0.5:                        # brow band (the focal point of the whole statue)
            return "gold" if y > cy + 9 and abs(z) <= 10 else "cut"
        if abs(x - (cx + 6)) <= 0.5 or abs(x - (cx + 16)) <= 0.5:
            return "cut"
        return "bronze"
    B.ellipsoid(HELM_C, HELM_R, part, cond=lambda x, y, z: y <= face)
    for x in range(cx - 20, cx + 21):
        for z in range(cz - 18, cz + 19):
            if (x, face, z) not in B.cells:
                continue
            eye = x in (cx - 5, cx - 4) and abs(z) <= 9
            breath = abs(z) <= 1 and cx - 3 <= x <= cx + 9
            frame = ((x in (cx - 6, cx - 3) and abs(z) <= 10) or (abs(z) == 2 and cx - 3 <= x <= cx + 10)
                     or (x == cx + 10 and abs(z) <= 2) or (abs(z) == 10 and cx - 6 <= x <= cx - 3))
            if frame and not eye and not breath:
                B.put((x, face + 1, z), "cut")              # the cross, one block proud of the face
            elif z in (5, 7, 9, -5, -7, -9) and x in (cx + 3, cx + 5, cx + 7):
                B.put((x, face, z), "dark")                 # breathing holes
    # the crest: a fin in the face's plane (z = -1..1), from the brow over the crown down to the nape; broken
    for i in range(0, 170):
        deg = 38 + i * 0.95                                  # angle from straight up (+y) toward the crown (-x)
        if 120 < deg < 142:
            continue                                         # the broken piece lies on the ground (crest_debris)
        phi = math.radians(deg)
        h = 9.0 if deg < 95 else 9.0 - (deg - 95) * 0.08
        notch = 1.5 if int(deg) % 9 < 3 else 0.0            # sculpted plume locks
        for k in range(HELM_R[0] - 4, int(HELM_R[0] + h - notch) + 1):
            x = round(cx - k * math.sin(phi))
            y = round(cy + k * math.cos(phi))
            for z in (-1, 0, 1):
                if y >= -2:
                    B.put((x, y, z), "cut" if (k >= HELM_R[0] + h - notch - 1 or abs(z) == 1 and k % 3 == 0)
                          else "bronze")
    # a stone mail aventail round the open chin, toward the neck
    B.capsule((cx + 15, cy, cz), (cx + 19, YC, cz), 12, 10, "mail")


def neck(B):
    B.capsule((-40, 16, 0), (-48, 16, 0), 9.5, 9.5, "mail")
    B.bands((-40, 16, 0), (-48, 16, 0), 9.5, 9.5, (0.15, 0.45, 0.75), part="cut", extra=0.8)


def torso(B):
    for x in range(-46, 0):
        d = torso_dims(x)
        if d is None:
            continue
        a, bf, bb = d
        for y in range(-3, int(YC + a) + 2):
            for z in range(-int(bb) - 2, int(bf) + 3):
                rho = torso_rho(x, y, z)
                if rho > 1.0:
                    continue
                p = (x, y, z)
                B.torso.add(p)
                if -9 <= x <= -7:
                    B.put(p, "dark")                        # sword belt
                elif x > -7:
                    B.put(p, "mail")                        # mail between belt and tassets
                elif z > 0 and abs(y - YC) <= 0.5 and x > -40:
                    B.put(p, "cut")                         # the breastplate's centre ridge (the tapul)
                elif abs(z + 2) <= 0.5 and y > YC + 6:
                    B.put(p, "dark")                        # side straps between breast and back plates
                elif x in (-26, -14) and z > 0:
                    B.put(p, "cut")                         # plackart lames
                else:
                    B.put(p, "bronze")
    # the ridge and the lames stand one block proud of the breastplate
    for x in range(-40, -9):
        d = torso_dims(x)
        if d is None:
            continue
        zf = int(d[1])
        B.put((x, YC, zf + 1), "cut")
    for x in (-26, -14):
        a, bf, bb = torso_dims(x)
        for y in range(int(YC - a), int(YC + a) + 1):
            dy = (y - YC) / a
            if abs(dy) < 1:
                zf = int(bf * math.sqrt(1 - dy * dy))
                B.put((x, y, zf + 1), "cut")
    # belt one block proud, gold buckle on the front
    for x in (-9, -8, -7):
        a, bf, bb = torso_dims(x)
        for y in range(-3, int(YC + a) + 3):
            for z in range(-int(bb) - 2, int(bf) + 3):
                if torso_rho(x, y, z, shrink=-1.0) <= 1.0 and (x, y, z) not in B.cells:
                    B.put((x, y, z), "dark")
    for x in (-9, -8, -7):
        for y in (YC - 1, YC, YC + 1):
            B.put((x, y, int(torso_dims(x)[1]) + 2), "gold")


def pelvis(B):
    B.ellipsoid(PELVIS_C, PELVIS_R, "mail")
    # tassets: three lames of plate hanging from the belt over the front of the hips, each one proud of the next
    for i, x0 in enumerate((-6, -2, 2)):
        for x in range(x0, x0 + 5):
            for y in range(0, 31):
                for z in range(0, 18):
                    e = ell((x, y, z), PELVIS_C, (PELVIS_R[0] + 1 + i * 0.5, PELVIS_R[1] + 1 + i * 0.5,
                                                  PELVIS_R[2] + 1 + i * 0.5))
                    if e <= 1.0 and z > 2:
                        B.put((x, y, z), "cut" if x == x0 + 4 else "bronze")


def pauldron(B):
    """The summit: a layered shoulder plate (three lames), a comb on top with spikes."""
    cx, cy, cz = PAULDRON_C

    def cond(x, y, z):
        return y >= 22 + int(2 * hash01(x, z, 5))

    def part(x, y, z):
        return "cut" if (y - 22) % 6 == 0 else "bronze"
    B.ellipsoid(PAULDRON_C, PAULDRON_R, part, cond)
    # lames: each lower band is one block wider
    for k, y0 in enumerate((22, 28, 34)):
        r = (PAULDRON_R[0] + 1, PAULDRON_R[1] + 1, PAULDRON_R[2] + 1)
        for x in range(cx - r[0] - 1, cx + r[0] + 2):
            for z in range(cz - r[2] - 1, cz + r[2] + 2):
                for y in (y0, y0 + 1):
                    if ell((x, y, z), PAULDRON_C, r) <= 1.0 and (x, y, z) not in B.cells:
                        B.put((x, y, z), "cut")
    # the comb: a fin along x on the crown, notched, with three spikes
    for x in range(cx - 9, cx + 9):
        top = max((y for y in range(cy, cy + PAULDRON_R[1] + 2) if (x, y, cz) in B.cells), default=None)
        if top is None:
            continue
        h = 3 + (2 if x in (cx - 6, cx, cx + 6) else 0) - (1 if x % 3 == 1 else 0)
        for y in range(top + 1, top + h + 1):
            for z in (cz - 1, cz, cz + 1):
                if abs(z - cz) == 1 and y > top + 2:
                    continue
                B.put((x, y, z), "cut" if y == top + h else "bronze")


def right_arm(B):
    # upper arm (mail with a bronze rerebrace), the elbow cop, the forearm (vambrace), broken at the wrist
    B.capsule(R_SHOULDER, R_ELBOW, 9.0, 8.0, "mail")
    B.capsule(R_SHOULDER, R_ELBOW, 9.6, 8.6, "plate", 0.3, 0.7)
    B.ellipsoid(R_ELBOW, (8.5, 8.5, 8.5), lambda x, y, z: "cut" if abs(z - R_ELBOW[2]) <= 0.5 else "bronze")
    # the couter's fan wing on the outside of the elbow (up)
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            if math.hypot(dx, dz) <= 6.5 and (dx + dz) % 3:
                B.put((R_ELBOW[0] + dx, R_ELBOW[1] + 9, R_ELBOW[2] + dz), "bronze" if math.hypot(dx, dz) < 5.5 else "cut")
    wrist_cut = lambda x, z: R_WRIST[2] - 3 + 2.5 * hash01(x, z // 2, 17)
    for x in range(R_ELBOW[0] - 9, R_ELBOW[0] + 10):
        for y in range(-3, 15):
            for z in range(R_ELBOW[2], R_WRIST[2] + 2):
                if z > wrist_cut(x, y):
                    continue
                d, t = seg((x, y, z), R_ELBOW, R_WRIST)
                r = 7.6 - 1.4 * t
                if d <= r + 0.3:
                    along = t * 27
                    B.put((x, y, z), "cut" if (int(along) % 7 == 0 and d > r - 1.5) else "bronze")
    B.bands(R_ELBOW, R_WRIST, 7.6, 6.2, (0.3, 0.55), part="cut", extra=0.9)


def right_hand(B):
    """The gauntlet lies apart, palm down, fingers curling up: the reaching hand of the silhouette. It rolled away
    from the broken wrist (west of the tunnel mouth)."""
    pc = (-53, 4, 73)
    B.ellipsoid(pc, (9.0, 3.4, 6.0), lambda x, y, z: "cut" if z in (pc[2] + 5, pc[2] - 5) else "bronze")
    for i, fx in enumerate((-60, -55, -50, -45)):
        n = (4, 5, 5, 3)[i]                                 # finger lengths: index, middle, ring, little
        pts = [(fx, 4, 78), (fx, 4, 79 + n), (fx, 7, 83 + n), (fx, 12 + n // 2, 84 + n)]
        for a, b in zip(pts, pts[1:]):
            B.capsule(a, b, 1.9, 1.6, "bronze")
        for p in pts[1:3]:
            B.put((p[0], p[1] + 2, p[2]), "cut")             # knuckle plates
            B.put((p[0], p[1] + 1, p[2]), "cut")
    for a, b in (((-44, 4, 70), (-39, 4, 74)), ((-39, 4, 74), (-36, 8, 78))):
        B.capsule(a, b, 1.8, 1.5, "bronze")                 # the thumb
    # the gauntlet's cuff: a ragged ring open at the wrist end
    for x in range(pc[0] - 8, pc[0] + 9):
        for y in range(-1, 12):
            d = math.hypot(x - pc[0], y - 4)
            if 5.0 <= d <= 7.0 and hash01(x, y, 23) > 0.25:
                for z in (65, 66, 67):
                    B.put((x, y, z), "cut" if z == 65 else "bronze")


def legs(B):
    # right leg (up): drawn-up knee, the arch of the silhouette
    B.capsule(R_HIP, R_KNEE, 9.0, 7.6, "mail")
    B.capsule(R_HIP, R_KNEE, 9.6, 8.2, "plate", 0.3, 0.8)
    B.ellipsoid(R_KNEE, (8.6, 8.6, 8.6), "bronze")
    B.capsule(R_KNEE, R_ANKLE, 7.2, 5.6, "mail")
    B.capsule(R_KNEE, R_ANKLE, 7.8, 6.2, "plate", 0.15, 0.9)
    B.ellipsoid(R_ANKLE, (5.5, 5.5, 5.5), "mail")
    B.capsule(R_ANKLE, R_TOE, 5.5, 3.4, "plate", 0.0, 1.0)
    B.bands(R_ANKLE, R_TOE, 5.5, 3.4, (0.35, 0.6, 0.82), part="cut", extra=0.6)
    # left leg (down), lying on the ground: the shin snapped in two
    B.capsule(L_HIP, L_KNEE, 9.0, 7.6, "mail")
    B.capsule(L_HIP, L_KNEE, 9.6, 8.2, "plate", 0.3, 0.8)
    B.ellipsoid(L_KNEE, (8.6, 8.6, 8.6), "bronze")
    for (a, b, t0, t1) in ((L_KNEE, L_ANKLE, 0.0, 0.40), (L_KNEE, L_ANKLE, 0.58, 1.0)):
        B.capsule(a, b, 7.2, 5.6, "mail", t0, t1)
        B.capsule(a, b, 7.8, 6.2, "plate", max(t0, 0.12), min(t1, 0.9))
    B.ellipsoid(L_ANKLE, (5.5, 5.5, 5.5), "mail")
    B.capsule(L_ANKLE, L_TOE, 5.5, 3.4, "plate", 0.0, 1.0)
    B.bands(L_ANKLE, L_TOE, 5.5, 3.4, (0.35, 0.6, 0.82), part="cut", extra=0.6)
    # knee cops: fan wings on the outer side
    for (kc, s) in ((R_KNEE, 1), (L_KNEE, 1)):
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                if math.hypot(dx, dy) <= 5.5 and (dx - dy) % 3:
                    B.put((kc[0] + dx, kc[1] + dy, kc[2] + s * 9), "cut" if math.hypot(dx, dy) > 4.5 else "bronze")


# ------------------------------------------------------------------ the dungeon (carving)
def profile_climb(start_f, targets, top_f):
    """Monotone feet heights along a climb: +1 per cell at most, following targets, capped at top_f."""
    out, f = [], start_f
    for tgt in targets:
        f = min(f + 1, max(f, int(round(tgt))), top_f)
        out.append(f)
    return out


def arm_axis_y(z):
    return R_ELBOW[1] + (R_SHOULDER[1] - R_ELBOW[1]) * (R_ELBOW[2] - z) / (R_ELBOW[2] - R_SHOULDER[2])


# climbs: (axis, fixed cross coordinates, [(u, feet)], facing of the steps (the climbing direction))
ARM_ZS = list(range(32, 16, -1))
ARM_STAIR = list(zip(ARM_ZS, profile_climb(2, [arm_axis_y(z) - 4.5 for z in ARM_ZS], BALC_F)))
SHOULDER_STAIR = []
_f = BALC_F
for _i, _z in enumerate(range(7, -7, -1)):
    if _i not in (6, 7):                             # a 3-block landing halfway
        _f += 1
    SHOULDER_STAIR.append((_z, min(_f, LOFT_F)))
SHOULDER_STAIR[-1] = (SHOULDER_STAIR[-1][0], LOFT_F)


def descend(top_x, top_f, bottom_f, step, landing_at, landing_len=2):
    """[(x, feet)] from the top step going down along x by `step` (+1 east / -1 west), with one landing."""
    out, f, x = [], top_f, top_x
    while f > bottom_f:
        out.append((x, f))
        if f == landing_at and landing_len:
            for _ in range(landing_len):
                x += step
                out.append((x, f))
            landing_len = 0
        x += step
        f -= 1
    return out


BALC_STAIR = descend(-26, BALC_F, HALL_F, 1, 10)     # down east along the front wall
GRAND_STAIR = descend(-32, ARENA_F, HALL_F, 1, 9)    # down east on the axis (climbed westwards)
BALC_Z = (7, 8, 9)
GRAND_Z = (-2, -1, 0, 1, 2)
PASS_X = (-41, -40, -39)                              # arm landing passage and shoulder stair


def carve_dungeon(B):
    A = B.air
    # forearm tunnel from the broken wrist (open) to the elbow chamber
    for x in range(-40, -35):
        for z in range(38, R_WRIST[2] + 3):
            for y in range(2, 7):
                A((x, y, z))
    # elbow chamber: a domed drum
    ex, _, ez = R_ELBOW
    for x in range(ex - 7, ex + 8):
        for z in range(ez - 7, ez + 8):
            d = math.hypot(x - ex, z - ez)
            for y in range(2, 14):
                if (y <= 8 and d <= 5.6) or math.sqrt(d * d + (y - 8) ** 2) <= 5.6:
                    A((x, y, z))
    # the upper-arm stair, the landing passage, the door onto the balcony
    for z, f in ARM_STAIR:
        for x in PASS_X:
            for y in range(f, f + 4):
                A((x, y, z))
    for z in range(16, 6, -1):
        for x in PASS_X:
            for y in range(BALC_F, BALC_F + 4):
                A((x, y, z))
    for x in (-38, -37):
        for z in (8, 9, 10):
            for y in range(BALC_F, BALC_F + 4):
                A((x, y, z))
    # shoulder stair up into the pauldron loft
    for z, f in SHOULDER_STAIR:
        for x in PASS_X:
            for y in range(f, f + 4):
                A((x, y, z))
    for x in range(-45, -38):
        for z in range(-8, 9):
            for y in range(LOFT_F, LOFT_F + 8):
                A((x, y, z))
    for z in range(-14, -8):                          # the north window (a framed view over the sword)
        for x in (-43, -42, -41):
            for y in range(LOFT_F + 1, LOFT_F + 4):
                if B.cells.get((x, y, z)) is not None or z > -12:
                    A((x, y, z))
    # the rib hall
    for x in range(HALL_X0, HALL_X1 + 1):
        for y in range(HALL_F, 36):
            for z in range(-14, 17):
                if torso_rho(x, y, z, shrink=3.0) <= 1.0:
                    A((x, y, z))
    # the gorget dais (built solid later) stands in the hall; the neck tunnel behind it
    for x in range(-46, -36):
        for z in (-1, 0, 1):
            for y in range(ARENA_F, ARENA_F + 4):
                A((x, y, z))
    # the helmet: the arena (feet ARENA_F), the reward vault below, the ladder shaft, the exit tunnel
    cx, cy, cz = HELM_C
    for x in range(cx - 16, cx + 17):
        for y in range(ARENA_F, cy + 16):
            for z in range(cz - 16, cz + 17):
                if ell((x, y, z), HELM_C, HELM_IN) <= 1.0:
                    A((x, y, z))
    for x in range(-64, -51):
        for z in range(-5, 6):
            for y in range(VAULT_F, VAULT_F + 5):
                A((x, y, z))
    for y in range(VAULT_F, ARENA_F - 1):
        A((-66, y, 0))
    for x in (-66, -65):
        for y in range(VAULT_F, VAULT_F + 3):
            A((x, y, 0))
    for z in range(6, 12):
        for x in (-59, -58, -57):
            for y in range(VAULT_F, VAULT_F + 3):
                A((x, y, z))
    # the hip: waist passage, crypt in the pelvis, tunnel down the left leg, the knee chamber and its crack
    for x in range(-6, -2):
        for z in (-1, 0, 1):
            for y in range(HALL_F, HALL_F + 4):
                A((x, y, z))
    for x in range(-3, 9):
        for z in range(-5, 6):
            for y in range(HALL_F, HALL_F + 6):
                A((x, y, z))
    for x in range(9, 34):
        for z in (-5, -4, -3):
            for y in range(2, 6):
                A((x, y, z))
    kx, _, kz = L_KNEE
    for x in range(kx - 6, kx + 7):
        for z in range(kz - 6, kz + 7):
            d = math.hypot(x - kx, z - kz)
            for y in range(2, 11):
                if (y <= 6 and d <= 4.6) or math.sqrt(d * d + (y - 6) ** 2) <= 4.6:
                    A((x, y, z))
    for x in (35, 36, 37):
        for z in range(-1, 6):
            for y in range(2, 5):
                A((x, y, z))
    # the secret: the knight's tomb under the hall floor
    for x in range(-33, -26):
        for z in range(-4, 3):
            for y in range(-3, 1):
                A((x, y, z))
    for y in range(1, 3):
        A((-30, y, -4))


def ribs(B):
    """Transverse ribs every 5 blocks and a ridge rib along the vault, kept where the breach opens the shell."""
    for p in list(B.carve):
        x, y, z = p
        if not (HALL_X0 <= x <= HALL_X1) or y < HALL_F:
            continue
        rho = torso_rho(x, y, z, shrink=3.0)
        a, bf, bb = torso_dims(x)
        lim = 1.0 - 2.2 / max(4.0, min(a, bb) - 3)
        if rho > 1.0 or rho < lim:
            continue
        if y < HALL_F + 5 and abs(z - 1) <= 4:
            continue                                         # the ribs spring above the aisle, never on it
        if any(x in (r, r + 1) for r in RIBS) and y > HALL_F:
            B.carve.discard(p)
            B.cells[p] = "rib"
        elif y > YC + 4 and abs(z - 1) <= 1:
            B.carve.discard(p)
            B.cells[p] = "rib"
    # the ribs also run through the shell (they show in the breach as the bars of a ribcage)
    for x in range(HALL_X0, HALL_X1 + 1):
        if not any(x in (r, r + 1) for r in RIBS):
            continue
        for y in range(HALL_F, 38):
            for z in range(-16, 19):
                p = (x, y, z)
                if p in B.cells and z > -2 and y > YC + 2 and torso_rho(x, y, z) <= 1.0 and torso_rho(x, y, z, 3.0) > 1.0:
                    B.cells[p] = "rib"


def breach(B):
    """The breastplate is torn open on its upper front: the ribs stand in the hole."""
    for p in list(B.torso):
        x, y, z = p
        if p not in B.cells or B.cells[p] == "rib" or y < 19:
            continue
        theta = math.atan2(y - YC, z)                       # 0 = front, pi/2 = top
        n = fbm(x * 1.7, theta * 20, 4.0, 31) - 0.5
        if ((x + 21) / 12.0) ** 2 + ((theta - 1.0) / 0.68) ** 2 < 1.0 + 0.9 * n:
            B.remove(p)
    # a chip out of the pauldron's front edge and dents on the plates
    for (c, r) in (((-29, 40, 13), 3.2), ((12, 33, 10), 2.4), ((-55, 30, 9), 2.2), ((44, 18, 9), 2.2)):
        for x in range(int(c[0] - r) - 1, int(c[0] + r) + 2):
            for y in range(int(c[1] - r) - 1, int(c[1] + r) + 2):
                for z in range(int(c[2] - r) - 1, int(c[2] + r) + 2):
                    if math.dist((x, y, z), c) <= r + hash3(x, y, z, 4) - 0.5 and (x, y, z) not in B.carve:
                        B.remove((x, y, z))


# ------------------------------------------------------------------ materials
def bronze(x, y, z, up, down, cut=False):
    n = hash3(x // 2, y // 3, z // 2, 11) * 0.65 + hash3(x // 5, y // 5, z // 5, 12) * 0.35
    v = y / 60.0 + (0.12 if up else 0.0) - (0.22 if down else 0.0) + (n - 0.5) * 0.55 - (0.18 if cut else 0.0)
    s = "exposed" if v < 0.24 else ("weathered" if v < 0.62 else "oxidized")
    return f"{s}_cut_copper" if cut else f"{s}_copper"


def mail(x, y, z, up):
    v = y / 36.0 + (0.15 if up else 0.0) + (hash3(x // 2, y // 2, z // 2, 13) - 0.5) * 0.35
    return ("mossy_cobblestone" if v < 0.1 else "tuff" if v < 0.32 else "andesite" if v < 0.6
            else "stone" if v < 0.85 else "polished_andesite")


def masonry(x, y, z, near_breach=False):
    h = hash3(x, y, z, 19)
    if (y <= HALL_F + 2 or near_breach) and h < 0.35:
        return "mossy_stone_bricks"
    if h < 0.13:
        return "cracked_stone_bricks"
    if (y + int(2 * hash01(x, z, 3))) % 8 == 0:
        return "tuff_bricks"                                 # string courses
    return "stone_bricks"


def rib_block(x, y, z):
    h = hash3(x, y, z, 29)
    return "polished_tuff" if h < 0.55 else ("tuff_bricks" if h < 0.85 else "chiseled_tuff")


NB6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def in_hand(x, z):
    return -66 <= x <= -32 and 63 <= z <= 92


def write_body(bp, B):
    cells, carve = B.cells, B.carve
    exterior_top = []
    for p, part in cells.items():
        x, y, z = p
        inner = outer = False
        for d in NB6:
            q = (x + d[0], y + d[1], z + d[2])
            if q in cells:
                continue
            if q in carve:
                inner = True
            else:
                outer = True
        up = (x, y + 1, z) not in cells
        down = (x, y - 1, z) not in cells
        if part == "rib":
            spec = rib_block(x, y, z)
        elif inner and not outer:
            spec = masonry(x, y, z)
        elif not outer:
            spec = "stone"                                   # hidden core
        elif part in ("bronze", "plate"):
            spec = bronze(x, y, z, up, down)
        elif part == "cut":
            spec = bronze(x, y, z, up, down, cut=True)
        elif part == "mail":
            spec = mail(x, y, z, up)
        elif part == "dark":
            spec = "polished_deepslate" if hash3(x, y, z, 2) < 0.7 else "deepslate_tiles"
        elif part == "gold":
            spec = "gold_block"
        else:
            spec = "stone"
        # moss gradient: heavy near the ground, a few patches up to mid height, clean on the crown
        if outer and up and part != "gold" and y >= 0 and not in_hand(x, z):
            m = 0.62 - 0.07 * y
            if hash3(x, y, z, 37) < m:
                spec = "moss_block"
                exterior_top.append((x, y, z))
            elif y < 22 and hash3(x // 3, y // 3, z // 3, 41) < 0.12:
                spec = "moss_block"
                exterior_top.append((x, y, z))
        bp.set(x, y, z, spec)
    return exterior_top


# ------------------------------------------------------------------ terrain
def ground_h(x, z):
    e = ((x - GROUND_C[0]) / GROUND_R[0]) ** 2 + ((z - GROUND_C[1]) / GROUND_R[1]) ** 2
    if e >= 1.0:
        return None
    return 0


def contact_map(B):
    """Columns where the body touches the ground, and a distance map out to 8 blocks around them."""
    touch = {(x, z) for (x, y, z) in B.cells if 0 <= y <= 2}
    dist = {c: 0 for c in touch}
    frontier = list(touch)
    for d in range(1, 9):
        nxt = []
        for (x, z) in frontier:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c = (x + dx, z + dz)
                if c not in dist:
                    dist[c] = d
                    nxt.append(c)
        frontier = nxt
    return dist


def near_door(x, z, r=6):
    return any(math.hypot(x - dx, z - dz) < r for dx, dz in DOORS)


def ground_block(x, z, top, B_near):
    h = hash01(x, z, 7)
    n = fbm(x, z, 11.0, 3)
    if not top:
        return "dirt" if h < 0.8 else "coarse_dirt"
    if B_near is not None and B_near <= 3 and h < 0.45:
        return "moss_block"
    if n > 0.66:
        return "coarse_dirt" if h < 0.5 else "rooted_dirt"
    if n < 0.3 and h < 0.25:
        return "moss_block"
    return "grass_block[snowy=false]"


def terrain(bp, B):
    dist = contact_map(B)
    low, grounded = {}, set()
    for (x, y, z) in B.cells:
        if y >= 1:
            if low.get((x, z), 99) > y:
                low[(x, z)] = y
        else:
            grounded.add((x, z))
    berm = {}
    for x in range(GROUND_C[0] - GROUND_R[0], GROUND_C[0] + GROUND_R[0] + 1):
        for z in range(GROUND_C[1] - GROUND_R[1], GROUND_C[1] + GROUND_R[1] + 1):
            if ground_h(x, z) is None:
                continue
            d = dist.get((x, z))
            h = 0
            if d is not None and d > 0 and not near_door(x, z):
                h = int(round((8 - d) * 0.55 + (fbm(x, z, 6.0, 9) - 0.5) * 2.5))
                h = max(0, min(h, 4))
            # earth heaped under the low flanks: the statue sank into it (no crawl spaces under the bulge)
            lo = low.get((x, z))
            if lo is not None and (x, z) not in grounded and lo <= 7 and not near_door(x, z, 5) \
                    and not (-64 <= x <= -35 and 62 <= z <= 92):
                h = max(h, lo - 1)
            berm[(x, z)] = h
            for y in range(-2, h + 1):
                if (x, y, z) in B.cells or (x, y, z) in B.carve:
                    continue
                bp.set(x, y, z, ground_block(x, z, y == h, d))
    return berm


def plants(bp, B, berm):
    """Grass, ferns and flowers on the field, thicker near the body (moist shade), none on the paths."""
    rng = bp.rng
    flowers = ("poppy", "dandelion", "oxeye_daisy", "cornflower", "azure_bluet")
    for (x, z), h in berm.items():
        top = bp.get(x, h, z)
        if top not in ("minecraft:grass_block", "minecraft:moss_block"):
            continue
        y = h + 1
        if (x, y, z) in B.cells or bp.get(x, y, z) is not None:
            continue
        r = hash01(x, z, 51)
        if r < 0.22:
            bp.set(x, y, z, "short_grass")
        elif r < 0.27:
            bp.set(x, y, z, "fern")
        elif r < 0.30 and bp.get(x, y + 1, z) is None:
            bp.set(x, y, z, "tall_grass[half=lower]")
            bp.set(x, y + 1, z, "tall_grass[half=upper]")
        elif r < 0.33:
            bp.set(x, y, z, flowers[int(hash01(x // 5, z // 5, 52) * len(flowers))])


def approach_path(bp, berm):
    """A worn path from the camp marker (south-east) to the broken wrist, never straight for more than 7."""
    pts = [(46, 88), (30, 84), (18, 80), (4, 76), (-10, 74), (-22, 70), (-32, 66), (-38, 63)]
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(z1 - z0)))
        for i in range(n + 1):
            t = i / max(1, n)
            x = round(x0 + (x1 - x0) * t + (fbm(i, x0, 5.0, 61) - 0.5) * 3)
            z = round(z0 + (z1 - z0) * t)
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c = (x + dx, z + dz)
                    if berm.get(c) == 0 and hash01(c[0], c[1], 62) < 0.85:
                        bp.set(c[0], 0, c[1], "dirt_path" if hash01(c[0], c[1], 63) < 0.8 else "coarse_dirt")
                        if bp.get(c[0], 1, c[1]) in ("minecraft:short_grass", "minecraft:fern", "minecraft:poppy",
                                                     "minecraft:dandelion", "minecraft:oxeye_daisy",
                                                     "minecraft:cornflower", "minecraft:azure_bluet"):
                            bp.remove(c[0], 1, c[1])


# ------------------------------------------------------------------ dungeon fit-out
def floor_spec(x, z, main=True):
    pal = FLOOR_MAIN if main else FLOOR_SIDE
    return pal[int(hash01(x, z, 71) * len(pal))]


def lay_floor(bp, B, xs, zs, f, main=True):
    for x in xs:
        for z in zs:
            if (x, f, z) in B.carve:
                bp.set(x, f - 1, z, floor_spec(x, z, main))


def climb(bp, B, cells, facing, axis, cross, spec="stone_brick_stairs", fill="stone_bricks"):
    """Place a climb [(u, feet)] (u along `axis`) across `cross`: a stair where the feet rise, a floor block where
    flat; masonry fills below down to the first solid block."""
    prev = None
    for u, f in cells:
        for c in cross:
            x, z = (u, c) if axis == "x" else (c, u)
            for y in range(f, f + 4):                             # headroom (cuts through ribs and walls)
                if (x, y, z) in B.cells:
                    B.cells.pop((x, y, z))
                    B.carve.add((x, y, z))
                    bp.set(x, y, z, "air")
            rising = prev is not None and f == prev + 1
            bp.set(x, f - 1, z, stair(spec, facing) if rising else floor_spec(x, z))
            y = f - 2
            while y >= -1 and (bp.get(x, y, z) in (None, "minecraft:air") or (x, y, z) in B.carve):
                bp.set(x, y, z, fill)
                B.carve.discard((x, y, z))
                y -= 1
        prev = f


def rail(bp, x, y, z):
    bp.set(x, y, z, "andesite_wall" if hash01(x, z, 81) < 0.8 else "mossy_cobblestone_wall")


def hang(bp, B, x, y, z, soul=False):
    """A lantern hanging on a chain from the first solid block above (x, y, z)."""
    top = y + 1
    while top < y + 24 and (x, top, z) in B.carve and (x, top, z) not in B.cells:
        top += 1
    if (x, top, z) not in B.cells:
        return
    for yy in range(y + 1, top):
        bp.set(x, yy, z, "iron_chain[axis=y,waterlogged=false]")
    bp.lantern(x, y, z, hanging=True, soul=soul)


def forearm_and_elbow(bp, B):
    lay_floor(bp, B, range(-40, -35), range(38, R_WRIST[2] + 3), 2)
    for x in range(-39, -36):                                    # the step up from the grass into the wrist
        bp.set(x, 1, R_WRIST[2] + 3, stair("stone_brick_stairs", "north"))
        bp.set(x, 0, R_WRIST[2] + 3, "stone_bricks")
    for z in (42, 50, 57):
        hang(bp, B, -38, 6, z)
    ex, _, ez = R_ELBOW
    lay_floor(bp, B, range(ex - 6, ex + 7), range(ez - 6, ez + 7), 2, main=False)
    bp.chest(ex + 4, 2, ez + 1, "west", loot=LOOT + "colossus_arm")
    bp.spawner(ex + 3, 2, ez - 3, MOB["ruin_walker"])
    bp.spawner(ex - 3, 2, ez + 1, "brasshaven:rust_mite_mother")
    hang(bp, B, ex, 10, ez)
    for (dx, dz) in ((-4, 3), (4, 4), (-3, -3)):
        bp.set(ex + dx, 2, ez + dz, "cobblestone" if dx < 0 else "mossy_cobblestone_slab[type=bottom,waterlogged=false]")
    climb(bp, B, ARM_STAIR, "north", "z", PASS_X)
    for i, (z, f) in enumerate(ARM_STAIR):
        if i % 6 == 3:
            hang(bp, B, -40, f + 3, z)
    # landing passage at the balcony level, the door east
    lay_floor(bp, B, PASS_X, range(7, 17), BALC_F)
    lay_floor(bp, B, (-38, -37), BALC_Z, BALC_F)
    hang(bp, B, -40, BALC_F + 3, 12)


def hall(bp, B):
    f = HALL_F
    # floor: a cleaner aisle on the axis, rough and mossy by the walls
    for x in range(HALL_X0, HALL_X1 + 1):
        for z in range(-14, 17):
            if (x, f, z) in B.carve:
                bp.set(x, f - 1, z, floor_spec(x, z, main=abs(z) <= 3))
    # under the breach the rain gets in: grass, moss and an azalea in the light shaft
    for x in range(-27, -12):
        for z in range(-3, 9):
            if (x, f, z) in B.carve and hash01(x, z, 91) < 0.55 - 0.03 * abs(x + 20):
                bp.set(x, f - 1, z, "moss_block" if hash01(x, z, 92) < 0.6 else "grass_block[snowy=false]")
                if hash01(x, z, 93) < 0.4:
                    bp.set(x, f, z, "moss_carpet" if hash01(x, z, 94) < 0.5 else "short_grass")
    bp.set(-16, f - 1, -2, "rooted_dirt")
    for y in range(f, f + 3):
        bp.set(-16, y, -2, "oak_log[axis=y]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in (3, 4):
                if abs(dx) + abs(dz) + (dy - 3) <= 3:
                    bp.set(-16 + dx, f + dy, -2 + dz, "flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]"
                           if hash01(dx, dz + dy, 95) < 0.4 else "azalea_leaves[distance=1,persistent=true,waterlogged=false]")
    # balcony on the front wall, its stair down east, the dais and the grand stair
    for x in range(-36, -26):
        for z in range(6, 12):
            bp.set(x, BALC_F - 1, z, floor_spec(x, z))
            B.carve.discard((x, BALC_F - 1, z))
            for y in range(BALC_F, BALC_F + 4):
                if (x, y, z) not in B.cells:
                    B.carve.add((x, y, z))
        bp.set(x, BALC_F - 2, 6, stair("stone_brick_stairs", "north", "top"))   # corbels
        if x <= -28:
            rail(bp, x, BALC_F, 6)
    for z in (10, 11):
        rail(bp, -26, BALC_F, z)
    climb(bp, B, list(reversed(BALC_STAIR)), "west", "x", BALC_Z)
    for x in range(-36, -32):
        for z in range(-3, 4):
            bp.set(x, ARENA_F - 1, z, "polished_andesite" if abs(z) <= 1 else "stone_bricks")
            for y in range(HALL_F - 1, ARENA_F - 1):
                bp.set(x, y, z, "stone_bricks" if (x + y + z) % 5 else "chiseled_stone_bricks")
                B.carve.discard((x, y, z))
        rail(bp, x, ARENA_F, -3)
        rail(bp, x, ARENA_F, 3)
    climb(bp, B, list(reversed(GRAND_STAIR)), "west", "x", GRAND_Z)
    # the sliver between the head-end wall and the first rib, north of the dais, is walled up (a player who
    # dropped into it from the grand stair could not climb out)
    for x in (-36, -35):
        for z in range(-7, -3):
            for y in range(HALL_F, ARENA_F):
                if bp.get(x, y, z) == "minecraft:air":
                    bp.set(x, y, z, "stone_bricks" if (x + y + z) % 5 else "chiseled_stone_bricks")
                    B.carve.discard((x, y, z))
    bp.set(-36, ARENA_F, -2, MOD["waystone"])
    hang(bp, B, -34, ARENA_F + 3, 0)
    # lanterns on chains from the ribs, candles at the rib feet
    for r in RIBS[1:]:
        hang(bp, B, r, 16, -4)
        hang(bp, B, r + 1, 18, 5)
    for (x, z) in ((-22, -4), (-11, -2), (-30, 6)):
        bp.set(x, f, z, "candle[candles=3,lit=true,waterlogged=false]")
    # loot and the guardian of the hall
    bp.chest(-8, f, -2, "west", loot=LOOT + "colossus_hall")
    bp.spawner(-12, f, -3, "brasshaven:gargoyle")
    bp.spawner(-18, f, 0, "brasshaven:rust_mite_mother")
    bp.boss_seal(-24, f - 1, 1, SENTINEL, 11)                    # the Sentinel wakes under the breach
    # fallen shell plates on the floor under the breach
    for (x, z) in ((-20, 6), (-21, 6), (-24, 7), (-13, 5)):
        if (x, f, z) in B.carve:
            bp.set(x, f, z, "weathered_cut_copper_slab[type=bottom,waterlogged=false]")
    # the secret hatch in the dark corner behind the grand stair, the tomb below
    bp.set(-30, 2, -4, "spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(-30, -3, -4, 1, "south")
    for x in range(-34, -25):
        for z in range(-5, 4):
            for y in range(-4, 2):
                if not (-33 <= x <= -27 and -4 <= z <= 2 and -3 <= y <= 0) and (x, y, z) not in B.carve:
                    bp.set(x, y, z, masonry(x, y, z))
            if -33 <= x <= -27 and -4 <= z <= 2:
                bp.set(x, -4, z, "mossy_stone_bricks" if hash01(x, z, 97) < 0.4 else "stone_bricks")
    bp.set(-30, -4 + 1, -5, "stone_bricks")
    for x in range(-32, -28):                                     # the knight's effigy
        bp.set(x, -3, 0, "smooth_stone_slab[type=double,waterlogged=false]")
        bp.set(x, -2, 0, "smooth_stone_slab[type=bottom,waterlogged=false]" if x != -32 else "skeleton_skull[rotation=4]")
    bp.chest(-27, -3, 2, "north", loot=LOOT + "colossus_armory")
    bp.set(-33, -3, -4, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(-27, -3, -4, "candle[candles=2,lit=true,waterlogged=false]")


def shoulder(bp, B):
    well = {z for z, f in SHOULDER_STAIR if f < LOFT_F}
    for x in range(-45, -38):
        for z in range(-8, 9):
            if not (x in PASS_X and z in well):
                lay_floor(bp, B, (x,), (z,), LOFT_F, main=False)
    climb(bp, B, SHOULDER_STAIR, "north", "z", PASS_X)
    # rails round the stairwell where it comes up through the loft floor
    for z in range(-5, -1):
        rail(bp, -42, LOFT_F, z)
    for x in PASS_X:
        rail(bp, x, LOFT_F, -1)
    # the loft: the knight's reliquary
    bp.chest(-44, LOFT_F, 6, "east", loot=LOOT + "colossus_armory")
    bp.spawner(-40, LOFT_F, 4, "brasshaven:gargoyle")
    bp.set(-44, LOFT_F, 2, "lectern[facing=east,has_book=false,powered=false]")
    for z in (-6, 0, 7):
        hang(bp, B, -42, LOFT_F + 5, z)
    for z in (-3, 3):
        bp.set(-45, LOFT_F, z, "andesite_wall")
        bp.set(-45, LOFT_F + 1, z, "lantern[hanging=false,waterlogged=false]")
    # the north window: a balustrade at the sill
    lay_floor(bp, B, (-43, -42, -41), range(-14, -8), LOFT_F + 1, main=False)
    for z in range(-14, -8):
        for x in (-43, -42, -41):
            if (x, LOFT_F + 1, z) in B.carve:
                bp.set(x, LOFT_F, z, "stone_bricks")
    for x in (-43, -42, -41):
        for z in range(-8, -15, -1):
            if (x, LOFT_F + 1, z) in B.carve and (x, LOFT_F + 1, z - 1) not in B.carve:
                rail(bp, x, LOFT_F + 1, z)
                break
    bp.set(-42, LOFT_F, -8, "stone_brick_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")


def hip(bp, B):
    lay_floor(bp, B, range(-6, -2), (-1, 0, 1), HALL_F, main=False)
    lay_floor(bp, B, range(-3, 9), range(-5, 6), HALL_F, main=False)
    lay_floor(bp, B, range(9, 34), (-5, -4, -3), 2, main=False)
    kx, _, kz = L_KNEE
    lay_floor(bp, B, range(kx - 5, kx + 6), range(kz - 5, kz + 6), 2, main=False)
    lay_floor(bp, B, (35, 36, 37), range(-1, 6), 2, main=False)
    for z in (-5, -4, -3):                                       # step down from the crypt into the leg
        bp.set(8, HALL_F - 1, z, stair("cobblestone_stairs", "west"))
    for x in (35, 36, 37):                                       # step down out of the knee onto the grass
        bp.set(x, 1, 6, stair("cobblestone_stairs", "north"))
        bp.set(x, 0, 6, "cobblestone")
    # the crypt in the pelvis: sarcophagi of the statue's builders
    for (x0, z0) in ((-1, -4), (-1, 3), (5, -4), (5, 3)):
        for dx in range(3):
            bp.set(x0 + dx, HALL_F, z0, "smooth_stone_slab[type=double,waterlogged=false]")
    bp.chest(7, HALL_F, 0, "west", loot=LOOT + "colossus_hall")
    bp.spawner(1, HALL_F, 0, "brasshaven:skeleton_knight")
    hang(bp, B, 2, HALL_F + 4, -1)
    hang(bp, B, 20, 5, -4)
    hang(bp, B, kx, 7, kz)
    for x in range(12, 33, 7):
        bp.set(x, 2, -5, "cobblestone_slab[type=bottom,waterlogged=false]")


def arena_and_vault(bp, B):
    cx, cy, cz = HELM_C
    for x in range(cx - 16, cx + 17):
        for z in range(cz - 16, cz + 17):
            if (x, ARENA_F, z) in B.carve:
                d = math.hypot(x - cx, z - cz)
                spec = ("chiseled_tuff" if 6 <= d < 7 or 12 <= d < 12.9 else
                        "tuff_bricks" if int(d) % 3 == 0 else "polished_tuff")
                bp.set(x, ARENA_F - 1, z, spec)
    # the visor: the T of slits on top of the helm, barred (daylight falls on the fight)
    for (x, y, z), part in list(B.cells.items()):
        if y > cy + 6 and ((x in (cx - 5, cx - 4) and abs(z) <= 9) or (abs(z) <= 1 and cx - 3 <= x <= cx + 9)):
            if any((x, yy, z) in B.carve for yy in range(y - 4, y)):
                bp.set(x, y, z, "iron_bars")
    # lanterns on the wall at head height, braziers of soul fire round the ring
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, z = round(cx + 13.2 * math.cos(a)), round(cz + 13.2 * math.sin(a))
        if (x, ARENA_F, z) in B.carve:
            bp.set(x, ARENA_F, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
                   if k % 2 else "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.boss_seal(cx, ARENA_F - 1, cz, BOSS, 13)
    bp.mist(-44, ARENA_F, -1, -44, ARENA_F + 3, 1)
    lay_floor(bp, B, range(-46, -36), (-1, 0, 1), ARENA_F)
    hang(bp, B, -40, ARENA_F + 3, 0)
    # the reward vault below: sealed bars over a ladder, opened when the boss falls
    bp.set(-66, ARENA_F - 1, 0, MOD["vault_bars"])
    bp.ladder(-66, VAULT_F, 0, ARENA_F - 2, "west")
    bp.set(-67, ARENA_F - 1, 0, "chiseled_tuff")
    lay_floor(bp, B, range(-64, -51), range(-5, 6), VAULT_F, main=True)
    lay_floor(bp, B, (-66, -65), (0,), VAULT_F)
    for x in range(-63, -52, 2):
        bp.set(x, VAULT_F - 1, 0, "gold_block" if x == -57 else "polished_andesite")
    bp.chest(-53, VAULT_F, -2, "west", loot=LOOT + "colossus_vault")
    bp.chest(-53, VAULT_F, 2, "west", loot=LOOT + "colossus_vault")
    for (x, z) in ((-62, -4), (-62, 4), (-54, -4), (-54, 4)):
        bp.set(x, VAULT_F, z, "andesite_wall")
        bp.set(x, VAULT_F + 1, z, "lantern[hanging=false,waterlogged=false]")
    bp.set(-58, VAULT_F, -4, "smithing_table")
    # the way out: a tunnel through the cheek, an iron door that opens only from inside (a lever by it)
    lay_floor(bp, B, (-59, -58, -57), range(6, 12), VAULT_F)
    for y in (VAULT_F, VAULT_F + 1):
        bp.set(-59, y, 11, "stone_bricks")
        bp.set(-57, y, 11, "stone_bricks")
    bp.set(-59, VAULT_F + 2, 11, "stone_bricks")
    bp.set(-58, VAULT_F + 2, 11, "stone_bricks")
    bp.set(-57, VAULT_F + 2, 11, "stone_bricks")
    bp.door(-58, VAULT_F, 11, "south", wood="iron")
    bp.set(-57, VAULT_F + 1, 10, "lever[face=wall,facing=north,powered=false]")
    for x in (-59, -58, -57):                                   # steps down from the door to the grass
        bp.set(x, VAULT_F - 1, 12, stair("stone_brick_stairs", "north"))
        bp.set(x, VAULT_F - 2, 12, "stone_bricks")
        bp.set(x, VAULT_F - 2, 13, stair("stone_brick_stairs", "north"))
        bp.set(x, VAULT_F - 3, 13, "stone_bricks")
        for z, y0 in ((12, VAULT_F), (13, VAULT_F - 1), (14, VAULT_F - 2)):
            for y in range(y0, y0 + 3):
                if bp.get(x, y, z) not in (None, "minecraft:air"):
                    bp.set(x, y, z, "air")
    hang(bp, B, -58, VAULT_F + 2, 0)


# ------------------------------------------------------------------ ornament and ruin
def body_life(bp, B, tops):
    """Plants on the mossy ledges of the body; vines hanging from the lower flanks."""
    for (x, y, z) in tops:
        if (x, y + 1, z) in B.cells or (x, y + 1, z) in B.carve or bp.get(x, y + 1, z) is not None:
            continue
        r = hash01(x * 3 + y, z, 101)
        if r < 0.3:
            bp.set(x, y + 1, z, "short_grass" if r < 0.2 else "fern")
        elif r < 0.34 and y < 10:
            bp.set(x, y + 1, z, "azalea" if r < 0.32 else "flowering_azalea")
    for (x, y, z) in list(B.cells):
        if not (3 <= y <= 26) or hash3(x, y, z, 103) > 0.05 - y * 0.0015 or in_hand(x, z):
            continue
        for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
            q = (x + dx, y, z + dz)
            if q in B.cells or q in B.carve or bp.get(*q) is not None:
                continue
            attach = {"north": "south", "south": "north", "east": "west", "west": "east"}[d]
            for k in range(2 + int(hash01(x, z, 104) * 5)):
                qq = (x + dx, y - k, z + dz)
                if qq in B.cells or qq in B.carve or bp.get(*qq) is not None or (x, y - k, z) not in B.cells:
                    break
                bp.set(*qq, f"vine[{attach}=true]")
            break


def sword(bp):
    """The knight's sword, shattered in three, lying behind his back; its pommel half buried."""
    z0 = SWORD_Z

    def blade(x0, x1, dz=0, lift=0, tip=False):
        for x in range(x0, x1 + 1):
            w = 3
            if tip:
                w = max(0, round(3 * (x1 - x) / max(1, x1 - x0)))
            for z in range(z0 - w, z0 + w + 1):
                zz = z + round(dz * (x - x0) / max(1, x1 - x0))
                edge = abs(z - z0) == w
                for y in range(0, 2 + lift):
                    spec = "smooth_stone" if edge else ("andesite" if z == z0 else "polished_andesite")
                    bp.set(x, y, zz, spec)
    blade(-14, 14)
    blade(19, 36, dz=2, lift=0)
    blade(40, 54, dz=-3, tip=True)
    # crossguard (bronze, gold ends), grip wrapped in dark leather, pommel
    for z in range(z0 - 9, z0 + 10):
        for y in (0, 1, 2):
            for x in (-16, -15):
                bp.set(x, y, z, "gold_block" if abs(z - z0) >= 8 and y == 2 else
                       ("weathered_cut_copper" if abs(z - z0) % 3 == 0 else "weathered_copper"))
    for x in range(-25, -16):
        for z in (z0 - 1, z0, z0 + 1):
            for y in (0, 1):
                bp.set(x, y, z, "polished_deepslate" if x % 2 else "deepslate_tiles")
    for x in range(-30, -25):
        for z in range(z0 - 2, z0 + 3):
            for y in range(0, 3):
                if abs(z - z0) + abs(y - 1) + abs(x + 28) <= 4:
                    bp.set(x, y, z, "gold_block" if (x, y, z) == (-28, 2, z0) else "oxidized_copper")
    # shards between the pieces
    for (x, z, s) in ((16, z0 + 1, "polished_andesite"), (17, z0 - 2, "smooth_stone_slab[type=bottom,waterlogged=false]"),
                      (38, z0 + 3, "andesite"), (37, z0 - 1, "polished_andesite_slab[type=bottom,waterlogged=false]")):
        bp.set(x, 1, z, s)


def crest_debris(bp):
    """The broken piece of the crest lying west of the helm, and its splinters."""
    for k in range(10):
        x = -86 - k
        for z in (-3, -2, -1):
            for y in (1, 2):
                bp.set(x, y if k % 4 else 1, z + (k // 4), "weathered_copper" if y == 1 else "oxidized_cut_copper")
    for (x, z) in ((-82, 4), (-84, -6), (-90, 3), (-79, 7)):
        bp.set(x, 1, z, "oxidized_cut_copper_slab[type=bottom,waterlogged=false]")


def plate_fragment(bp, x0, z0, w, d, tilt, cut_edge=True):
    """A torn armour plate lying on the field, tilted against its debris."""
    for i in range(w):
        for j in range(d):
            y = 1 + (i * tilt) // max(1, w)
            spec = "weathered_cut_copper" if cut_edge and (i in (0, w - 1)) else (
                "oxidized_copper" if hash01(x0 + i, z0 + j, 111) < 0.5 else "weathered_copper")
            bp.set(x0 + i, y, z0 + j, spec)
            for yy in range(1, y):
                bp.set(x0 + i, yy, z0 + j, "cobblestone")


def rubble_field(bp, B, berm):
    rng = bp.rng
    # the debris of the breach on the front, a wide fan of plates and stones
    for (x0, z0, w, d, t) in ((-28, 20, 5, 4, 2), (-17, 23, 6, 3, 3), (-22, 29, 4, 4, 1), (-10, 19, 4, 3, 2),
                              (52, 22, 4, 3, 2), (46, -16, 5, 3, 2), (-72, 26, 4, 4, 2)):
        if berm.get((x0, z0)) == 0:
            plate_fragment(bp, x0, z0, w, d, t)
    for i in range(260):
        a = rng.random() * math.tau
        r = rng.random() ** 0.7
        x = round(GROUND_C[0] + math.cos(a) * GROUND_R[0] * 0.9 * r)
        z = round(GROUND_C[1] + math.sin(a) * GROUND_R[1] * 0.9 * r)
        h = berm.get((x, z))
        if h is None or near_door(x, z, 5) or (x, h + 1, z) in B.cells or bp.get(x, h + 1, z) not in (
                None, "minecraft:short_grass", "minecraft:fern"):
            continue
        breach_side = -34 < x < -6 and 14 < z < 40
        if rng.random() < (0.9 if breach_side else 0.35):
            spec = rng.choice(("cobblestone", "mossy_cobblestone", "andesite", "tuff", "weathered_copper",
                               "oxidized_cut_copper", "stone_bricks", "mossy_stone_bricks"))
            bp.set(x, h + 1, z, spec)
            if rng.random() < 0.35 and bp.get(x + 1, h + 1, z) in (None, "minecraft:short_grass"):
                bp.set(x + 1, h + 1, z, rng.choice(("cobblestone_slab[type=bottom,waterlogged=false]",
                                                    "andesite_slab[type=bottom,waterlogged=false]",
                                                    "weathered_cut_copper_slab[type=bottom,waterlogged=false]")))
    # boulders of the shattered shin
    for (x, z, r) in ((48, -12, 2), (52, 2, 2), (50, -6, 3), (55, -14, 1)):
        h = berm.get((x, z), 0)
        for dx in range(-r, r + 1):
            for dy in range(0, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + (dy * 1.5) ** 2 + dz * dz <= r * r + 0.5 and (x + dx, h + 1 + dy, z + dz) not in B.cells:
                        bp.set(x + dx, h + 1 + dy, z + dz, "weathered_copper" if dy == r - 1 else
                               ("tuff" if hash3(dx, dy, dz, 121) < 0.5 else "andesite"))


def trees(bp, berm):
    for (x, z, kind, h) in ((-84, -30, "big", 11), (58, -46, "oak", 7), (76, 40, "birch", 8), (-88, 58, "oak", 6),
                            (40, -52, "spruce", 11), (-60, -46, "birch", 7), (70, 70, "spruce", 10), (-20, 86, "oak", 6)):
        g = berm.get((x, z))
        if g is None:
            continue
        y = g + 1
        if kind == "big":
            big_oak(bp, x, y, z, h=h, seed=x * 7 + z)
        elif kind == "oak":
            oak(bp, x, y, z, h=h, seed=x + z)
        elif kind == "birch":
            birch(bp, x, y, z, h=h, seed=x - z)
        else:
            spruce(bp, x, y, z, h=h, seed=x)
    for (x, z) in ((-70, -20), (-48, 40), (20, 56), (64, -24), (-6, -24), (30, -26)):
        g = berm.get((x, z))
        if g is not None:
            bush(bp, x, g + 1, z, "oak_leaves", r=1)


def camp(bp, berm):
    """Treasure hunters camped on the approach: a tent, a fire, a barrel of finds, a ladder against a rock."""
    cx, cz = 40, 80
    if berm.get((cx, cz)) is None:
        return
    for z in range(cz - 2, cz + 3):
        bp.set(cx - 2, 1, z, "brown_wool")
        bp.set(cx - 1, 2, z, "brown_wool")
        bp.set(cx, 3, z, "brown_wool")
        bp.set(cx + 1, 2, z, "brown_wool")
        bp.set(cx + 2, 1, z, "brown_wool")
    bp.set(cx + 5, 1, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.barrel(cx + 6, 1, cz + 3, "up", loot=LOOT + "colossus_arm")
    bp.set(cx + 7, 1, cz + 3, "crafting_table")
    bp.set(cx + 4, 1, cz - 3, "lantern[hanging=false,waterlogged=false]")
    # the marker where the path starts: a broken plinth with a bronze finger on it
    for y in range(1, 4):
        bp.set(46, y, 88, "stone_bricks" if y < 3 else "mossy_stone_bricks")
    bp.set(46, 4, 88, "oxidized_copper")
    bp.set(46, 5, 88, "lantern[hanging=false,waterlogged=false]")


# ------------------------------------------------------------------ builder
def fallen_colossus(bp):
    B = Body()
    torso(B)
    pelvis(B)
    legs(B)
    neck(B)
    helmet(B)
    right_arm(B)
    pauldron(B)
    right_hand(B)
    carve_dungeon(B)
    ribs(B)
    breach(B)
    berm = terrain(bp, B)
    tops = write_body(bp, B)
    for p in B.carve:
        if p not in B.cells:
            bp.set(*p, "air")
    forearm_and_elbow(bp, B)
    hall(bp, B)
    shoulder(bp, B)
    hip(bp, B)
    arena_and_vault(bp, B)
    body_life(bp, B, tops)
    plants(bp, B, berm)
    approach_path(bp, berm)
    sword(bp)
    crest_debris(bp)
    rubble_field(bp, B, berm)
    trees(bp, berm)
    camp(bp, berm)
    # quality pass: the tunnels, chambers and the helmet lit to 8+ (lanterns on chains where the vault allows,
    # waxed copper bulbs set in the masonry elsewhere)
    light_fill(bp, ground=0, lamp="waxed_copper_bulb[lit=true,powered=false]",
               hang="lantern[hanging=true,waterlogged=false]", chain="iron_chain[axis=y,waterlogged=false]",
               where=lambda x, y, z: (x, y, z) in B.carve or (x, y - 1, z) in B.carve or y > 1)


# interior shots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("entrance", (-38, 2, 56), (-38, 4, 36)),
    ("balcony", (-33, BALC_F, 9), (-12, 24, -2)),
    ("rib_hall", (-10, HALL_F, 1), (-30, 20, 0)),
    ("hip_crypt", (6, HALL_F, 3), (-2, HALL_F + 2, -3)),
    ("loft", (-42, LOFT_F, 7), (-42, LOFT_F + 2, -6)),
    ("arena", (-47, ARENA_F, 0), (-70, ARENA_F + 4, 0)),
    ("valley", (30, 1, 62), (-25, 22, 0)),
]


register(StructureDef(
    "fallen_colossus", "overworld",
    ["plains", "sunflower_plains", "meadow", "forest", "birch_forest", "savanna", "taiga"],
    [Piece("colossus", fallen_colossus, views=VIEWS)],
    spacing=80, separation=32, adaptation="beard_box", processors="none", max_distance=116,
    title_fr="Colosse abattu", title_en="Fallen Colossus"))

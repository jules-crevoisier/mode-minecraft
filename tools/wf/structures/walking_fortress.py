"""Walking Fortress Wreck (Épave de la forteresse marchante): a brass siege walker frozen mid-stride in a scorched
crater. First colossal build of the 2026 overhaul (tools/BUILDING.md §1 colossal tier, §12 concept 8, §15).

Silhouette: a four-legged riveted hull 70 long carried 55 blocks above the ground, caught in a trot (front-left and
back-right feet planted, front-right lifted, back-left trailing), two smokestacks and a bridge mast reaching y ~130.

Layout, ground y = 0, front (the head) to the north (z < 0):
  * the crater: a 150-wide bowl of scorched earth, basalt and slag with a raised rim, gear rubble, a fallen
    smokestack and a scavengers' camp at the foot of the front-left leg (the human scale cue);
  * the two planted legs are the way up: a breach in the foot, a spiral stair inside the shin (38 up), the knee
    chamber, then a straight stair inside the thigh, which is pitched at exactly 45 degrees so stairs climb it;
  * the hull, three decks: the cargo hold (both hips open into it), the engine room (boiler, flywheels, catwalk),
    the gun deck (broadside cannons, armory, crew bunks);
  * the top deck between the bridge tower and the stacks is the boss arena; the vault is in the bridge tower,
    behind sealed bars that open when the boss falls.
Loot gradient (§15.6): hold tier 1, engine room and gun deck tier 2, vault tier 3.
Style: tools/STYLE_STEAMPUNK.md (60% dark iron and soot, 25% brass and copper, glass, amber light).
"""
import math

from .. import interior as INT
from ..arch import stair, stair_run
from ..defs import Piece, StructureDef, register
from ..megakit import (BARS, BRASS, BRASS_SLAB, BRASS_STAIRS, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, TABLE,
                       IRON_SLAB, IRON_STAIRS, IRON_WALL, MAHOGANY, MAHOGANY_STAIRS, PIPES, SMOKE, TREAD, TREAD_SLAB, VERD, W,
                       chimney, fbm, hash01, hash3, is_air, lantern_post, railing, smoke)
from ..parts import LOOT, MOD

# the boss of the walker comes with the boss pass of the overhaul; until then the arena wakes the Forge King
BOSS = "brasshaven:iron_helmsman"

# ------------------------------------------------------------------ dimensions
CRATER_R = 74          # outer edge of the crater (blends back into the terrain)
RIM_IN, RIM_PEAK = 52, 62
RIM_H = 7

HOLD, ENGINE, GUN, DECK = 60, 68, 80, 89     # feet levels of the decks (floor blocks at L - 1)
KEEL = 52
HULL_Z0, HULL_Z1 = -42, 34                   # bow (north) and stern
HULL_W = 22                                  # half width amidships

# legs: hip, knee, ankle (bottom of the shin), foot centre on the ground
HIP_X, HIP_Y = 20, 62
KNEE_X, KNEE_Y = 40, 42
FRONT_Z, BACK_Z = -24, 20
STAIR_BASE = KNEE_Y - 3                      # the thigh stair's line: step i at y = STAIR_BASE + i, x = knee - s*i
STAIR_START = 4                              # it starts just outside the shin's stairwell (square ring 3)
KNEE_FLOOR = STAIR_BASE + STAIR_START        # feet level in the knee chamber
SHIN_R, THIGH_R, KNEE_R, HIP_R = 7, 6, 9, 8

SIEGE_Y = 73
HEAD_Z = -51                                 # tip of the head (cockpit nose)
ARENA = (0, DECK, 0)
ARENA_R = 15
BRIDGE = (-9, -36, 9, -21)                   # x0, z0, x1, z1 of the bridge tower

IRON_BRICKS = W + "dark_iron_bricks"
GRILLE = W + "brass_grille"
SOOT = W + "sooty_smokestack_bricks"


def plate(x, y, z):
    """Hull and leg plating (STYLE_STEAMPUNK: 60% dark). Dark iron panels 8 long and 6 high with darker brick
    seams; verdigris and copper only as weathering streaks on the upper courses."""
    if y % 6 == 0 or (x + z) % 8 == 0:
        return IRON_BRICKS
    h = hash3(x // 2, y // 5, z // 2, 41)
    if y > 70 and h < 0.10:
        return VERD
    if h < 0.04:
        return COPPER
    return IRON


# ------------------------------------------------------------------ crater
def crater_h(x, z):
    r = math.hypot(x, z)
    if r >= CRATER_R:
        return 0
    n = fbm(x, z, 14.0, 3) - 0.5
    if r < RIM_IN:
        return int(round(n * 1.5 - 1)) if r > 20 else 0
    if r < RIM_PEAK:
        t = (r - RIM_IN) / (RIM_PEAK - RIM_IN)
        return int(round(RIM_H * math.sin(t * math.pi / 2) + n * 3))
    t = (r - RIM_PEAK) / (CRATER_R - RIM_PEAK)
    return int(round(RIM_H * (1 - t) ** 1.5 + n * 2 * (1 - t)))


def ground_block(x, z, top):
    """Scorched ground: basalt, blackstone, tuff and slag gravel, a little burnt earth (stone-themed for placement:
    the crater also sits in deserts and badlands)."""
    h = hash01(x, z, 7)
    r = math.hypot(x, z)
    if r < 40 and h < 0.06:
        return "magma_block"
    if r > RIM_PEAK + 4:                         # the outer slope fades back to earth
        return "coarse_dirt" if h < 0.2 else ("gravel" if h < 0.5 else ("tuff" if h < 0.75 else "andesite"))
    if h < 0.32:
        return "basalt[axis=y]" if top else "blackstone"
    if h < 0.52:
        return "blackstone"
    if h < 0.72:
        return "tuff"
    if h < 0.87:
        return "gravel" if top else "tuff"
    return "coarse_dirt"


def crater(bp):
    for x in range(-CRATER_R, CRATER_R + 1):
        for z in range(-CRATER_R, CRATER_R + 1):
            if math.hypot(x, z) > CRATER_R + 0.4:
                continue
            h = crater_h(x, z)
            for y in range(min(h, 0) - 3, h + 1):
                bp.set(x, y, z, ground_block(x, z, y == h))
            for y in range(h + 1, 1):
                bp.set(x, y, z, "air")       # the bowl is dug below the terrain


# ------------------------------------------------------------------ geometry helpers
def seg_dist(p, a, b):
    """Distance from p to the segment a-b, and the position t (0..1) of the closest point."""
    ax, ay, az = a
    bx, by, bz = b
    vx, vy, vz = bx - ax, by - ay, bz - az
    L2 = vx * vx + vy * vy + vz * vz
    t = max(0.0, min(1.0, ((p[0] - ax) * vx + (p[1] - ay) * vy + (p[2] - az) * vz) / L2))
    cx, cy, cz = ax + vx * t, ay + vy * t, az + vz * t
    return math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2), t


def outside_hull(x, y, z):
    """Leg parts stop at the hull's inner skin, so they never fill the hold."""
    return abs(x) >= HIP_X - 1 or y < HOLD - 1 or y > DECK


def tube(bp, a, b, r, inner=None, spec=plate, bands=None, keep=outside_hull):
    """A plated tube from a to b (radius r); hollow inside `inner` when given. Brass bands near both ends."""
    lo = [min(a[i], b[i]) - r - 1 for i in range(3)]
    hi = [max(a[i], b[i]) + r + 1 for i in range(3)]
    length = math.dist(a, b)
    for x in range(int(lo[0]), int(hi[0]) + 1):
        for y in range(int(lo[1]), int(hi[1]) + 1):
            for z in range(int(lo[2]), int(hi[2]) + 1):
                d, t = seg_dist((x, y, z), a, b)
                if d > r + 0.3 or not keep(x, y, z):
                    continue
                if inner is not None and d < inner:
                    bp.set(x, y, z, "air")
                    continue
                along = t * length
                if bands and (along < 2 or length - along < 2 or int(along) % bands == 0):
                    bp.set(x, y, z, BRASS)
                else:
                    bp.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def ball(bp, c, r, inner=None, spec=plate, keep=outside_hull):
    cx, cy, cz = c
    ri = int(r) + 1
    for x in range(cx - ri, cx + ri + 1):
        for y in range(cy - ri, cy + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if d > r + 0.3 or not keep(x, y, z):
                    continue
                if inner is not None and d < inner:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, spec(x, y, z) if callable(spec) else spec)


def gear_disc(bp, cx, cy, cz, r, axis):
    """A big cog on the outer face of a joint: a ring of gear panels with teeth, a brass hub."""
    for u in range(-r - 1, r + 2):
        for v in range(-r - 1, r + 2):
            d = math.hypot(u, v)
            ang = math.atan2(v, u)
            tooth = d <= r + 1.2 and math.cos(ang * 10) > 0.5
            if d <= 1.5:
                spec = BRASS
            elif r - 1.5 < d <= r + 0.4 or (r + 0.4 < d and tooth):
                spec = GEAR
            elif abs(u) <= 0.5 or abs(v) <= 0.5:
                spec = IRON
            else:
                continue
            p = (cx, cy + v, cz + u) if axis == "x" else (cx + u, cy + v, cz)
            bp.set(*p, spec)


# ------------------------------------------------------------------ hull
def hull_w(y, z):
    """Half width of the hull at height y and position z (0 outside)."""
    if not (KEEL <= y <= DECK - 1 and HULL_Z0 <= z <= HULL_Z1):
        return 0.0
    if z < -26:                      # the bow narrows to the head
        wz = HULL_W - (HULL_W - 11) * ((-26 - z) / (-26 - HULL_Z0)) ** 1.6
    elif z > 22:                     # the stern rounds off
        wz = HULL_W - (HULL_W - 15) * ((z - 22) / (HULL_Z1 - 22)) ** 2
    else:
        wz = HULL_W
    if y < 64:                       # bilge curve down to the keel
        f = math.sqrt(max(0.0, 1 - ((64 - y) / (64 - KEEL + 0.5)) ** 2))
        wz *= 0.35 + 0.65 * f
    # the bow and the stern also curve up from the keel
    if y < 60:
        end = (z - HULL_Z0) if z < 0 else (HULL_Z1 - z)
        if end < (60 - y) * 0.8:
            return 0.0
    return wz


def hull(bp):
    for z in range(HULL_Z0, HULL_Z1 + 1):
        for y in range(KEEL, DECK):
            w = hull_w(y, z)
            if w <= 0:
                continue
            wi = hull_w(y, z) - 2.0 if (HULL_Z0 + 2 <= z <= HULL_Z1 - 2) else 0
            # the inner skin also needs the bow / stern ends 2 blocks in
            if z < HULL_Z0 + 2 or z > HULL_Z1 - 2 or hull_w(y, z - 2) <= 0 or hull_w(y, z + 2) <= 0:
                wi = 0
            for x in range(-int(w), int(w) + 1):
                if abs(x) > w:
                    continue
                inside = abs(x) < wi and HOLD - 1 < y < DECK - 1
                if inside:
                    bp.set(x, y, z, "air")
                elif y < HOLD and abs(x) < wi - 1:
                    bp.set(x, y, z, IRON)        # ballast core under the hold
                else:
                    bp.set(x, y, z, plate(x, y, z))
    # the top deck (y = DECK - 1) and the floors between decks
    for z in range(HULL_Z0, HULL_Z1 + 1):
        w = hull_w(DECK - 1, z)
        for x in range(-int(w), int(w) + 1):
            if abs(x) <= w:
                edge = abs(x) > w - 1.5 or hull_w(DECK - 1, z - 1) <= 0 or hull_w(DECK - 1, z + 1) <= 0
                # dark plated deck, tread walkways along the centre line and both sides
                lane = abs(x) <= 1 or abs(abs(x) - (w - 4)) <= 1
                bp.set(x, DECK - 1, z, BRASS if edge else (TREAD if lane else (IRON_BRICKS if z % 8 == 0 else IRON)))
        for fy in (HOLD - 1, ENGINE - 1, GUN - 1):
            wi = hull_w(fy, z) - 1.5
            for x in range(-int(wi), int(wi) + 1):
                if abs(x) <= wi and bp.get(x, fy, z) in (None, "minecraft:air"):
                    bp.set(x, fy, z, TREAD if fy != HOLD - 1 else "brasshaven:dark_iron_plating")
    # brass belt courses along the sides at each deck, and the deck edge
    for z in range(HULL_Z0, HULL_Z1 + 1):
        for y in (GUN - 1, ENGINE - 1, DECK - 2):
            w = hull_w(y, z)
            if w <= 0:
                continue
            for s in (-1, 1):
                x = s * int(w)
                if bp.get(x, y, z) not in (None, "minecraft:air"):
                    bp.set(x, y, z, BRASS)
    # railing around the top deck
    for z in range(HULL_Z0, HULL_Z1 + 1):
        w = hull_w(DECK - 1, z)
        if w <= 0:
            continue
        for x in range(-int(w), int(w) + 1):
            if abs(x) > w:
                continue
            edge = (abs(x) > w - 1 or hull_w(DECK - 1, z - 1) <= 0 or hull_w(DECK - 1, z + 1) <= 0)
            if edge:
                bp.set(x, DECK, z, IRON_WALL if (x + z) % 6 == 0 else f"{W}brass_railing[facing="
                       f"{'west' if x < 0 else 'east' if abs(x) > w - 1 else ('north' if z < 0 else 'south')}]")


def portholes(bp):
    """Round windows along both sides of the engine room and the gun deck, ribs of brass between them."""
    for z in range(-20, 22, 6):
        for y0 in (ENGINE + 3, GUN + 2):
            w = hull_w(y0, z)
            for s in (-1, 1):
                for dy in range(2):
                    for dz in range(2):
                        for k in range(3):
                            x = s * (int(w) - k)
                            bp.set(x, y0 + dy, z + dz, "glass_pane" if k == 0 else "air")
                for dz in (-1, 2):
                    bp.set(s * int(w), y0 - 1 + 1, z + dz, BRASS)


def hull_details(bp):
    """Depth on the hull sides (BUILDING §4): a cornice under the deck edge and a rub-strake at the engine deck, both
    standing out one block, a pipe bundle along the hold, vent grilles; a ball turret under the belly."""
    for z in range(HULL_Z0 + 3, HULL_Z1 - 2):
        for s in (-1, 1):
            f = "east" if s < 0 else "west"          # upside-down stairs, their back against the hull
            for y, spec in ((DECK - 2, IRON_STAIRS), (ENGINE - 1, BRASS_STAIRS)):
                w = int(hull_w(y, z))
                if w and is_air(bp, s * (w + 1), y, z):
                    bp.set(s * (w + 1), y, z, stair(spec, f, "top"))
            w = int(hull_w(HOLD + 3, z))
            if w and -30 < z < 28 and abs(z - FRONT_Z) > 9 and abs(z - BACK_Z) > 9:
                for dy in (0, 1):
                    if is_air(bp, s * (w + 1), HOLD + 3 + dy, z):
                        bp.set(s * (w + 1), HOLD + 3 + dy, z, W + "copper_pipe[axis=z]")
                if z % 6 == 0:
                    bp.set(s * (w + 1), HOLD + 2, z, stair(BRASS_STAIRS, f, "top"))
            if z % 4 == 0 and -24 < z < 26:
                w = int(hull_w(DECK - 4, z))
                bp.set(s * w, DECK - 4, z, GRILLE)
    # belly turret: a riveted ball under the hull with twin guns pointing forward
    tc = (0, KEEL - 2, -8)
    ball(bp, tc, 4.5, keep=lambda x, y, z: True)
    for x in (-2, 2):
        for k in range(5, 13):
            bp.set(x, tc[1], tc[2] - k, IRON if k % 4 else BRASS)


def companionway(bp):
    """The hut over the stair from the gun deck: players climb into it and walk out south, behind the arena."""
    for x in range(-3, 4):
        for z in range(13, 26):
            wall = x in (-3, 3) or z == 13
            for y in range(DECK, DECK + 5):
                if y == DECK + 4:
                    bp.set(x, y, z, BRASS if wall else IRON)
                elif wall:
                    bp.set(x, y, z, plate(x, y, z) if (y != DECK + 2 or z % 3) else "glass_pane")
                elif bp.get(x, y, z) is not None and "stairs" not in (bp.get(x, y, z) or ""):
                    bp.set(x, y, z, "air")
    bp.set(0, DECK + 3, 23, HANG_LAMP)


# ------------------------------------------------------------------ legs
def foot(bp, cx, cz, y, forward=-1):
    """A clawed foot pad: a rounded slab 20 x 22, three toes forward, a spur behind; its top at y + 5."""
    for x in range(cx - 12, cx + 13):
        for z in range(cz - 16, cz + 17):
            u, v = (x - cx) / 10.0, (z - cz) / 11.0
            d = math.hypot(u, v)
            if d > 1.0:
                continue
            top = y + 5 - int(d * d * 3)
            for yy in range(y, top + 1):
                bp.set(x, yy, z, IRON if yy < top else plate(x, yy, z))
    # toes: three claws pointing forward (z * forward), curling down to the ground
    for i, dx in enumerate((-6, 0, 6)):
        for k in range(10):
            z = cz + forward * (10 + k)
            yt = y + 3 - k // 3
            for x in range(cx + dx - 2, cx + dx + 3):
                for yy in range(y, max(y, yt) + 1):
                    if abs(x - cx - dx) <= 2 - k // 5:
                        bp.set(x, yy, z, plate(x, yy, z))
        # the claw tip
        bp.set(cx + dx, y, cz + forward * 21, BRASS)
        bp.set(cx + dx, y + 1, cz + forward * 20, stair(BRASS_STAIRS, "north" if forward < 0 else "south"))
    # the spur behind
    for k in range(8):
        z = cz - forward * (11 + k)
        for yy in range(y, y + 3 - k // 3):
            bp.set(cx, yy, z, plate(cx, yy, z))


def foot_breach(bp, cx, cz, y, side):
    """A breach torn in the side of a foot pad (3 wide, 4 high) from its edge to the shin shaft."""
    s = 1 if side == "east" else -1
    for x in range(cx + s * 5, cx + s * 13, s):
        for z in range(cz - 1, cz + 2):
            for yy in range(y + 1, y + 5):
                bp.set(x, yy, z, "air")
            bp.set(x, y, z, TREAD)
    for z in (cz - 2, cz + 2):
        bp.set(cx + s * 9, y + 4, z, stair(IRON_STAIRS, "north" if z < cz else "south", "top"))


def spiral(bp, cx, cz, y0, y1, top=None):
    """Blueprint.spiral_stairs (two half slabs per level on the square ring at distance 3), phased so that its last
    slab lands on the ring cell `top`."""
    r = 3
    ring = [(x, z) for x in range(cx - r, cx + r + 1) for z in range(cz - r, cz + r + 1)
            if max(abs(x - cx), abs(z - cz)) == r]
    ring.sort(key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    n = 2 * (y1 - y0 + 1)
    i = (ring.index(top) - (n - 1)) % len(ring) if top else 0
    for y in range(y0, y1 + 1):
        bp.set(cx, y, cz, IRON)
    for y in range(y0, y1 + 1):
        for k in range(2):
            x, z = ring[i % len(ring)]
            bp.slab(x, y, z, TREAD_SLAB, "bottom" if k == 0 else "top")
            i += 1


def shin_shaft(bp, cx, cz, y_bottom, y_top, light=True, top=None):
    """Hollow shin with the spiral stair inside (same carving as wf/dungeon.spiral_down: the steps run on the square
    ring at distance 3, so the corners are carved to 4)."""
    for x in range(cx - SHIN_R - 1, cx + SHIN_R + 2):
        for z in range(cz - SHIN_R - 1, cz + SHIN_R + 2):
            d = math.hypot(x - cx, z - cz)
            sq = max(abs(x - cx), abs(z - cz))
            for y in range(y_bottom - 1, y_top + 1):
                if d > SHIN_R + 0.3:
                    continue
                if (sq <= 4 or d <= 4.6) and y_bottom <= y:
                    bp.set(x, y, z, "air")
                elif y < y_top - 1 and (y >= y_bottom or d > 4.6):
                    band = (y - y_bottom) % 12 == 0
                    bp.set(x, y, z, BRASS if band and d > SHIN_R - 1 else plate(x, y, z))
    spiral(bp, cx, cz, y_bottom, y_top - 1, top)
    for y in range(y_top, y_top + 4):
        bp.set(cx, y, cz, IRON)
    if light:
        for i, y in enumerate(range(y_bottom + 2, y_top - 1, 6)):
            x, z = ((cx + 5, cz), (cx, cz + 5), (cx - 5, cz), (cx, cz - 5))[i % 4]
            bp.set(x, y, z, EDISON)
        # slit windows in the shin, every 9 blocks, so the climb looks out over the crater
        for i, y in enumerate(range(y_bottom + 5, y_top - 2, 9)):
            dx, dz = ((1, 0), (0, 1), (-1, 0), (0, -1))[(i + 1) % 4]
            for k in range(5, SHIN_R + 1):
                for dy in range(2):
                    bp.set(cx + dx * k, y + dy, cz + dz * k, "glass_pane" if k == SHIN_R else "air")


def thigh_stair(bp, s, z):
    """The straight stair inside a 45-degree thigh, from the knee floor up to the hold floor (s = side, -1 west)."""
    face = "east" if s < 0 else "west"          # climbing towards the hull
    kx = s * KNEE_X
    n = KNEE_X - HIP_X + 1                       # steps from x = kx to x = s * HIP_X
    for i in range(STAIR_START, n):
        x = kx - s * i
        y = STAIR_BASE + i
        for dz in (-1, 0, 1):
            bp.set(x, y, z + dz, stair(IRON_STAIRS, face))
            for yy in range(max(y - 6, KNEE_FLOOR - 1), y):    # never below the knee floor (the spiral)
                bp.set(x, yy, z + dz, IRON)
            for c in range(1, 5):
                bp.set(x, y + c, z + dz, "air")
        if i % 6 == 3:
            # lamps on the thigh wall, above the stair's side
            bp.set(x, y + 3, z + 2, EDISON)
            bp.set(x, y + 3, z - 2, EDISON)
    # floor of the hip, at the hold level, from the last step into the hull
    for x in range(s * (HIP_X - 1), -s * 1 + s * (HIP_X - 6), -s):
        for dz in (-1, 0, 1):
            bp.set(x, HOLD - 1, z + dz, TREAD)
            for c in range(0, 4):
                bp.set(x, HOLD + c, z + dz, "air")


def walk_leg(bp, s, z, front):
    """A planted leg the player climbs: foot, hollow shin with the spiral, knee chamber, 45-degree thigh."""
    kx = s * KNEE_X
    hip = (s * HIP_X, HIP_Y, z)
    knee = (kx, KNEE_Y, z)
    foot(bp, kx, z, 0, forward=-1)
    # the thigh tube (plated shell, hollow) and its hydraulic rams on both sides
    tube(bp, knee, hip, THIGH_R, inner=THIGH_R - 2.2, bands=8)
    for dz in (-THIGH_R - 1, THIGH_R + 1):
        a = (kx - s * 2, KNEE_Y + 4, z + dz)
        b = (s * (HIP_X + 4), HIP_Y + 2, z + dz)
        tube(bp, a, b, 1.2, spec=COPPER)
        tube(bp, a, (a[0] - s * 6, a[1] + 6, a[2]), 1.6, spec=BRASS)
    # knee chamber and hip joint: hollow balls
    ball(bp, knee, KNEE_R, inner=KNEE_R - 1.6)
    ball(bp, hip, HIP_R, inner=HIP_R - 1.8)
    gear_disc(bp, kx + s * (KNEE_R + 1), KNEE_Y, z, 6, "x")
    gear_disc(bp, s * (HIP_X + HIP_R + 1), HIP_Y, z, 5, "x")
    # the shin, carved through the bottom of the knee ball, with the spiral stair up to the knee floor
    # (its last slab on the middle of the outer face: the climb's last turn stays on the outer half, the floor covers
    # the inner half of the stairwell, where the thigh stair starts)
    shin_shaft(bp, kx, z, 1, KNEE_FLOOR, top=(kx + 3 * s, z))
    for x in range(kx - 8, kx + 9):
        for zz in range(z - 8, z + 9):
            d = math.hypot(x - kx, zz - z)
            sq = max(abs(x - kx), abs(zz - z))
            if d > KNEE_R - 1.5:
                continue
            for y in range(KNEE_Y - KNEE_R, KNEE_FLOOR - 1):     # the knee ball below the floor is solid
                if d > 7.2 and math.sqrt(d * d + (y - KNEE_Y) ** 2) < KNEE_R - 1.4:
                    bp.set(x, y, zz, IRON)
            if d <= 7.2 and (sq > 3 or s * (x - kx) <= -1):
                bp.set(x, KNEE_FLOOR - 1, zz, TREAD)
    thigh_stair(bp, s, z)
    foot_breach(bp, kx, z, 0, "west" if s > 0 else "east")     # towards the crater centre, under the hull
    # knee chamber dressing: gauges and pipes on the wall, a spawner of clockwork spiders
    for dz in (-5, 5):
        bp.set(kx + s * 5, KNEE_FLOOR, z + dz, GAUGE)
        bp.set(kx + s * 5, KNEE_FLOOR + 1, z + dz, PIPES)
    bp.spawner(kx + s * 6, KNEE_FLOOR, z, W + "clockwork_spider")
    bp.set(kx, KNEE_FLOOR + 6, z, HANG_LAMP)


def dead_leg(bp, s, z, knee, ankle, foot_c):
    """A leg that is not part of the route: solid plated tubes, foot pad (possibly lifted off the ground)."""
    hip = (s * HIP_X, HIP_Y, z)
    tube(bp, knee, hip, THIGH_R, bands=8)
    tube(bp, ankle, knee, SHIN_R - 0.5, bands=12)
    ball(bp, knee, KNEE_R)
    ball(bp, hip, HIP_R)
    gear_disc(bp, knee[0] + s * (KNEE_R + 1), knee[1], knee[2], 6, "x")
    gear_disc(bp, s * (HIP_X + HIP_R + 1), HIP_Y, z, 5, "x")
    for dz in (-THIGH_R - 1, THIGH_R + 1):
        tube(bp, (knee[0] - s * 2, knee[1] + 4, knee[2] + dz), (s * (HIP_X + 4), HIP_Y + 2, z + dz), 1.2, spec=COPPER)
    fx, fy, fz = foot_c
    ball(bp, ankle, 5)
    foot(bp, fx, fz, fy, forward=-1)


# ------------------------------------------------------------------ decks
def hold(bp):
    """Cargo hold: crates, the keel beams, a stair up to the engine room at the back."""
    # keel pillars
    for z in range(-28, 28, 8):
        for x in (-8, 8):
            for y in range(HOLD, ENGINE - 1):
                bp.set(x, y, z, IRON)
            bp.set(x, ENGINE - 2, z + 1, stair(IRON_STAIRS, "north", "top"))
            bp.set(x, ENGINE - 2, z - 1, stair(IRON_STAIRS, "south", "top"))
    # cargo stacks between the pillars, with lanes left free
    rng = bp.rng
    for z0 in (-20, -12, 4, 12):
        for x0 in (-17, 11):
            for x in range(x0, x0 + 5):
                for z in range(z0, z0 + 4):
                    h = 1 + int(hash01(x, z, 3) * 3)
                    for y in range(HOLD, HOLD + h):
                        if hash01(x, z + y, 9) < 0.25 and y == HOLD and (x in (x0, x0 + 4) or z in (z0, z0 + 3)):
                            bp.barrel(x, y, z, "up")
                        else:
                            bp.set(x, y, z, "spruce_planks" if (x + z + y) % 3 else "stripped_spruce_wood[axis=y]")
    # loot of the hold
    bp.chest(-3, HOLD, -26, "south", loot=LOOT + "walker_hold")
    bp.chest(3, HOLD, 26, "north", loot=LOOT + "walker_hold")
    for z in range(-24, 26, 8):
        bp.set(0, ENGINE - 2, z, HANG_LAMP)
        bp.set(-14, ENGINE - 2, z + 4, HANG_LAMP)
        bp.set(14, ENGINE - 2, z + 4, HANG_LAMP)
    bp.spawner(0, HOLD, -4, W + "clockwork_spider")
    # stair up to the engine room, on the centre line at the back, climbing north
    stair_run(bp, -1, HOLD, 24, "north", ENGINE - HOLD, 3, IRON_STAIRS, fill=IRON, clear=4)


def engine_room(bp):
    """Two decks high: the boiler on the centre line, flywheels, a catwalk ring, the stair up to the gun deck."""
    # boiler: a horizontal cylinder along z
    by = ENGINE + 4
    for z in range(-14, 12):
        for x in range(-5, 6):
            for y in range(ENGINE, ENGINE + 10):
                d = math.hypot(x, y - by)
                if d <= 4.4:
                    band = z % 5 == 0
                    bp.set(x, y, z, BRASS if band else (COPPER if d > 3.4 else IRON))
    for x in range(-3, 4):
        for y in range(ENGINE, ENGINE + 3):
            bp.set(x, y, -15, "blast_furnace[facing=north,lit=true]" if (x + y) % 2 else IRON)
    # boiler stand
    for z in range(-14, 12, 4):
        for x in (-4, 4):
            bp.set(x, ENGINE, z, IRON)
    # steam pipes up into the deck and to the stacks
    for x in (-3, 3):
        for y in range(ENGINE + 8, GUN - 1):
            bp.set(x, y, 10, PIPES)
    # flywheels on both sides
    for s in (-1, 1):
        gear_disc(bp, s * 11, ENGINE + 5, -2, 4, "x")
        for x in range(s * 6, s * 11, s):
            bp.set(x, ENGINE + 5, -2, IRON)
    # catwalk ring at mid height, around the boiler (feet ENGINE + 6)
    cy = ENGINE + 5
    for z in range(-18, 16):
        for x in range(-9, 10):
            ring = (7 <= abs(x) <= 9 and -18 <= z <= 15) or (-18 <= z <= -16 and abs(x) <= 9) or (13 <= z <= 15 and abs(x) <= 9)
            if ring:
                bp.set(x, cy, z, TREAD)
    for z in range(-18, 16):
        for x in (-10, 10):
            if not (-4 <= z <= 0):
                railing(bp, x, cy + 1, z, "west" if x < 0 else "east")
    # ladders from the floor up to the catwalk at its four corners (inside the ring, against the railing posts)
    for (x, z, f) in ((-8, 16, "north"), (8, 16, "north"), (-8, -19, "south"), (8, -19, "south")):
        bp.set(x, ENGINE - 1, z, TREAD)
        bp.ladder(x, ENGINE, z, cy + 1, f)
        bp.set(x, cy + 1, z + (1 if f == "north" else -1), "air")
    for z in range(-16, 14, 6):
        bp.set(-12, GUN - 2, z, HANG_LAMP)
        bp.set(12, GUN - 2, z, HANG_LAMP)
    # tier 2 on the catwalk
    bp.chest(-8, cy + 1, -6, "east", loot=LOOT + "walker_engine")
    bp.chest(8, cy + 1, 4, "west", loot=LOOT + "walker_engine")
    bp.spawner(0, ENGINE, 14, W + "steam_drone")
    bp.spawner(-14, ENGINE, -10, W + "steam_drone")
    bp.spawner(12, ENGINE, -4, W + "boiler_gunner")
    # stair up to the gun deck, along the east wall, climbing north
    stair_run(bp, 11, ENGINE, 14, "north", GUN - ENGINE, 3, IRON_STAIRS, fill=IRON, clear=4)


def cannon(bp, x, y, z, s, length=7):
    """A broadside cannon: an iron barrel through a port in the side, its carriage inside."""
    for k in range(length):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dy) + abs(dz) <= 1 or k > length - 2:
                    bp.set(x + s * k, y + dy, z + dz, IRON if k % 3 else BRASS)
    bp.set(x + s * (length - 1), y, z, "black_concrete")
    bp.set(x - s, y, z, BRASS)
    for dz in (-1, 1):
        bp.set(x - s, y - 1, z + dz, stair(IRON_STAIRS, "north" if dz > 0 else "south"))


def gun_deck(bp):
    """Broadside cannons through ports, ammunition barrels, the armory at the bow, bunks at the stern."""
    gy = GUN + 1
    for z in range(-20, 21, 8):
        for s in (-1, 1):
            w = int(hull_w(gy, z))
            cannon(bp, s * (w - 5), gy, z, s, length=8)
            bp.barrel(s * (w - 7), GUN, z + 2, "up", loot=None)
            bp.barrel(s * (w - 7), GUN, z - 2, "up")
    # the two siege guns under the bow
    for x in (-6, 6):
        for k in range(16):
            z = -40 - k
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if abs(dx) + abs(dy) <= 1 or k > 13:
                        bp.set(x + dx, SIEGE_Y + dy, z, BRASS if k % 4 == 0 else IRON)
        bp.set(x, SIEGE_Y, -55, "black_concrete")
    # armory at the bow: racks and the tier 2 chest
    bp.chest(0, GUN, -28, "south", loot=LOOT + "walker_armory")
    for x in (-3, 3):
        bp.set(x, GUN, -27, "smithing_table")
        bp.set(x, GUN + 1, -28, IRON_WALL)
    # crew bunks at the stern
    for i, x in enumerate((-12, -8, 8, 12)):
        bp.bed(x, GUN, 27, "north", color="red" if i % 2 else "brown")
    for z in range(-20, 24, 7):
        bp.set(-6, DECK - 2, z, HANG_LAMP)
        bp.set(6, DECK - 2, z, HANG_LAMP)
    bp.spawner(0, GUN, -6, W + "steam_drone")
    bp.spawner(-6, GUN, 8, W + "boiler_gunner")
    # stair up to the top deck, centre line, climbing south, arriving behind the arena
    stair_run(bp, 1, GUN, 14, "south", DECK - GUN, 3, IRON_STAIRS, fill=IRON, clear=4)   # x = 1..-1


# ------------------------------------------------------------------ top deck
def head(bp):
    """The cockpit nose: a rounded armoured snout ahead of the bow, two round eyes glowing amber, open at the back
    onto the gun deck (a lookout over the crater)."""
    z_tip = HEAD_Z
    for z in range(HULL_Z0 - 2, z_tip - 1, -1):
        t = (HULL_Z0 - 2 - z) / (HULL_Z0 - 2 - z_tip)
        hw = 10 - 3 * t * t
        lo, hi = int(70 + 6 * t), int(DECK - 1 - 3 * t)
        for x in range(-int(hw), int(hw) + 1):
            for y in range(lo, hi + 1):
                inner = (abs(x) < hw - 2 and GUN <= y < hi - 1 and z > z_tip + 1)
                bp.set(x, y, z, "air" if inner else (BRASS if y == hi or abs(x) >= int(hw) and y % 6 == 0
                                                      else plate(x, y, z)))
        for x in range(-int(hw) + 2, int(hw) - 1):
            if bp.get(x, GUN - 1, z) is not None:
                bp.set(x, GUN - 1, z, TREAD)
    # through the bow wall into the gun deck
    for z in range(HULL_Z0 - 2, HULL_Z0 + 4):
        for x in range(-2, 3):
            for y in range(GUN, GUN + 4):
                bp.set(x, y, z, "air")
            bp.set(x, GUN - 1, z, TREAD)
    # the eyes: round windows ringed with brass on the front face
    ey = GUN + 2
    for ex in (-5, 5):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                d = math.hypot(dx, dy)
                if d <= 2.3:
                    bp.set(ex + dx, ey + dy, z_tip, "orange_stained_glass")
                    bp.set(ex + dx, ey + dy, z_tip + 1, "air")
                elif d <= 3.3:
                    bp.set(ex + dx, ey + dy, z_tip, BRASS)
    bp.set(0, GUN + 4, z_tip + 3, HANG_LAMP)
    # a ram plate under the chin
    for x in range(-4, 5):
        for k in range(4):
            bp.set(x, 70 + k, z_tip - 1 + k, BRASS if abs(x) == 4 else IRON)


def bridge_tower(bp):
    """Two storeys on the bow end of the deck: the bridge (helm, charts, the vault behind sealed bars) and, set
    back on its roof, the captain's cabin under a verdigris roof, a balcony around it and the mast."""
    x0, z0, x1, z1 = BRIDGE
    mid = DECK + 7                              # roof of the bridge = balcony floor = cabin floor
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            corner = x in (x0, x1) and z in (z0, z1)
            for y in range(DECK, mid + 1):
                if y == mid:
                    bp.set(x, y, z, BRASS if wall else MAHOGANY)
                elif not wall:
                    bp.set(x, y, z, "air")
                elif corner:
                    bp.set(x, y, z, BRASS)
                elif 2 <= y - DECK <= 4 and (z == z0 or (x + z) % 3):
                    bp.set(x, y, z, "glass_pane")
                else:
                    bp.set(x, y, z, plate(x, y, z))
    # balcony railing on the roof edge
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                railing(bp, x, mid + 1, z, "west" if x == x0 else "east" if x == x1 else
                        ("north" if z == z0 else "south"))
    # door from the arena (south face), 3 wide
    for x in (-1, 0, 1):
        for y in range(DECK, DECK + 3):
            bp.set(x, y, z1, "air")
    # the helm: wheel, chart table, voice pipes
    bp.set(0, DECK, z0 + 2, MAHOGANY)
    bp.set(0, DECK + 1, z0 + 2, GEAR)
    bp.set(-3, DECK, z0 + 2, "cartography_table")
    bp.set(3, DECK, z0 + 2, "lectern[facing=south,has_book=false,powered=false]")
    for x in (-6, 6):
        bp.set(x, DECK, z0 + 1, PIPES)
        bp.set(x, DECK + 1, z0 + 1, GAUGE)
    # the vault behind sealed bars (they open when the boss falls), west side
    vx = x0 + 4
    for z in range(z0 + 5, z1 - 2):
        for y in range(DECK, mid):
            bp.set(vx, y, z, MOD["vault_bars"] if (z0 + 7 <= z <= z0 + 8 and y < DECK + 3) else IRON)
    bp.chest(x0 + 2, DECK, z0 + 7, "east", loot=LOOT + "walker_vault")
    bp.chest(x0 + 2, DECK, z0 + 8, "east", loot=LOOT + "walker_vault")
    bp.set(x0 + 2, DECK + 3, z0 + 9, HANG_LAMP)
    # stair up to the balcony along the east wall, climbing north
    stair_run(bp, x1 - 1, DECK, z1 - 1, "north", mid - DECK + 1, 1, MAHOGANY_STAIRS, fill=MAHOGANY, clear=4)
    # the cabin, set back 2 from the bridge walls
    cx0, cz0, cx1, cz1 = x0 + 2, z0 + 2, x1 - 3, z1 - 3
    top = mid + 6
    for x in range(cx0, cx1 + 1):
        for z in range(cz0, cz1 + 1):
            wall = x in (cx0, cx1) or z in (cz0, cz1)
            for y in range(mid + 1, top):
                if not wall:
                    bp.set(x, y, z, "air")
                elif x in (cx0, cx1) and z in (cz0, cz1):
                    bp.set(x, y, z, BRASS)
                elif y in (mid + 2, mid + 3) and (x + z) % 2:
                    bp.set(x, y, z, "glass_pane")
                else:
                    bp.set(x, y, z, MAHOGANY if y < top - 1 else IRON)
    bp.pyramid_roof(cx0, cz0, cx1, cz1, top, VERD.replace("plating", "plating_stairs"), overhang=1, cap=BRASS)
    # cabin door onto the balcony (east wall), where the stair arrives
    for y in (mid + 1, mid + 2):
        bp.set(cx1, y, cz1 - 2, "air")
    bp.bed(cx0 + 2, mid + 1, cz0 + 1, "south", color="red")
    bp.set(cx0 + 5, mid + 1, cz0 + 1, W + "mahogany_table")
    bp.chest(cx0 + 7, mid + 1, cz0 + 1, "south", loot=LOOT + "walker_armory")
    bp.set((cx0 + cx1) // 2, top - 2, (cz0 + cz1) // 2, HANG_LAMP)
    for (x, z) in ((-4, z0 + 6), (4, z0 + 6)):
        bp.set(x, mid - 1, z, HANG_LAMP)
    # the mast rises from the roof's peak
    mx, mz = (cx0 + cx1) // 2, (cz0 + cz1) // 2
    for y in range(top + 1, top + 26):
        bp.set(mx, y, mz, IRON if y % 6 else BRASS)
    for dx in (-3, -2, -1, 1, 2, 3):
        bp.set(mx + dx, top + 18, mz, IRON_WALL)
    bp.set(mx, top + 26, mz, "lightning_rod")


def arena(bp):
    ax, ay, az = ARENA
    # floor pattern: brass rings on the tread
    for x in range(-ARENA_R, ARENA_R + 1):
        for z in range(az - ARENA_R, az + ARENA_R + 1):
            d = math.hypot(x - ax, z - az)
            if bp.get(x, DECK - 1, z) in (TREAD, IRON):
                if 4.5 <= d < 5.5 or 11 <= d < 11.8:
                    bp.set(x, DECK - 1, z, BRASS)
    # lamp posts and ventilator cowls as cover
    for (x, z) in ((-12, -10), (12, -10), (-12, 12), (12, 12)):
        lantern_post(bp, x, DECK, z, h=4)
    for (x, z) in ((-8, -2), (8, 6)):
        for y in range(DECK, DECK + 3):
            bp.set(x, y, z, COPPER)
        bp.set(x, DECK + 3, z, stair(COPPER.replace("plating", "plating_stairs"), "south"))
    bp.boss_seal(ax, ay - 1, az, BOSS, ARENA_R - 1)
    # mist at the companionway's exit and across the bridge door
    bp.mist(-2, DECK, 26, 2, DECK + 2, 26)
    x0, z0, x1, z1 = BRIDGE
    bp.mist(-1, DECK, z1, 1, DECK + 2, z1)


def stacks(bp):
    for x in (-9, 9):
        top = chimney(bp, x, 27, DECK, 40, r=4, bands=(8,))
        # soot on the crown courses
        for y in range(top - 9, top - 2):
            for xx in range(x - 6, x + 7):
                for zz in range(21, 34):
                    if bp.get(xx, y, zz) == SMOKE and hash01(xx * 3 + y, zz, 5) < 0.6 + (y - top + 9) * 0.06:
                        bp.set(xx, y, zz, SOOT)


# ------------------------------------------------------------------ surroundings
def fallen_stack(bp):
    """A smokestack torn off in the fall, lying across the crater floor."""
    a, b = (-50, 3, 34), (-22, 3, 52)
    tube(bp, a, b, 3.2, spec=SMOKE, bands=7)


def rubble(bp):
    rng = bp.rng
    for i in range(70):
        ang = rng.random() * math.tau
        r = 18 + rng.random() * 34
        x, z = int(math.cos(ang) * r), int(math.sin(ang) * r)
        y = crater_h(x, z) + 1
        if not is_air(bp, x, y, z):
            continue
        spec = rng.choice((IRON, BRASS, GEAR, COPPER, IRON_SLAB, BRASS_SLAB, "blackstone"))
        bp.set(x, y, z, spec)
        if rng.random() < 0.4 and is_air(bp, x + 1, y, z):
            bp.set(x + 1, y, z, IRON_SLAB)
    # smoking vents where the boiler leaked into the ground
    for (x, z) in ((-18, 6), (22, -2), (-6, 34), (10, -40)):
        y = crater_h(x, z)
        bp.set(x, y, z, "magma_block")
        smoke(bp, x, y + 1, z, signal=False)


def scavenger_camp(bp):
    """A small camp at the front-left foot: tent, campfire, ladder crates. The human-scale cue."""
    cx, cz = -24, -42
    y = crater_h(cx, cz) + 1
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            if math.hypot(x - cx, z - cz) <= 4.2:
                bp.set(x, y - 1, z, "coarse_dirt")
                for yy in range(y, y + 4):
                    bp.set(x, yy, z, "air")
    for z in range(cz - 2, cz + 3):
        bp.set(cx - 2, y, z, "white_wool")
        bp.set(cx - 1, y + 1, z, "white_wool")
        bp.set(cx, y + 2, z, "white_wool")
    bp.set(cx + 2, y, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bp.barrel(cx + 3, y, cz + 2, "up", loot=LOOT + "walker_hold")
    bp.set(cx + 3, y, cz - 2, "crafting_table")


def dressing(bp):
    """Light and clutter for the decks (the first in-game shots were dim, bare halls)."""
    # hold: amber lamps flush in the ceiling, cargo chains with lanterns hanging between the pillar rows
    for z in range(-26, 27, 6):
        for x in (-13, -4, 4, 13):
            if not is_air(bp, x, ENGINE - 1, z) and is_air(bp, x, ENGINE - 2, z):
                bp.set(x, ENGINE - 1, z, EDISON)
    for (x, z) in ((-4, -16), (4, -8), (-4, 8), (4, 16), (-14, -24), (14, 0), (-14, 20)):
        bp.set(x, ENGINE - 2, z, "iron_chain[axis=y]")
        bp.set(x, ENGINE - 3, z, "lantern[hanging=true]")
    # loose crates and coal sacks in the lanes
    for (x, z) in ((-6, -22), (6, -14), (-6, 2), (6, 18), (-15, -4), (15, 8)):
        bp.set(x, HOLD, z, "spruce_planks")
        bp.set(x, HOLD + 1, z, "spruce_trapdoor[facing=north,half=bottom,open=false]")
    for (x, z) in ((-5, -10), (5, 6), (-16, 14)):
        bp.set(x, HOLD, z, "coal_block")
    # engine room: more lamps over the catwalk and the furnace glow
    for z in range(-15, 14, 5):
        for x in (-8, 8):
            if is_air(bp, x, GUN - 2, z):
                bp.set(x, GUN - 2, z, HANG_LAMP)
    # gun deck: a red runner down the centre, chart tables, shot racks, more lamps
    for z in range(-26, 13):
        for x in (-1, 0, 1):
            if is_air(bp, x, GUN, z) and not is_air(bp, x, GUN - 1, z):
                bp.set(x, GUN, z, "red_carpet" if x == 0 else "black_carpet")
    for z in (-18, -2):
        for x in (-4, 4):
            bp.set(x, GUN, z, TABLE)
            bp.set(x, GUN + 1, z, "lantern")
    for z in range(-20, 21, 8):
        for s in (-1, 1):
            w = int(hull_w(GUN + 1, z))
            x = s * (w - 7)
            for dz in (-3, 3):
                if is_air(bp, x, GUN, z + dz):
                    bp.set(x, GUN, z + dz, "coal_block")
    for z in range(-20, 24, 7):
        for x in (-14, 14):
            if is_air(bp, x, DECK - 2, z):
                bp.set(x, DECK - 2, z, HANG_LAMP)
    # ceiling beams across the hold and the gun deck (they also hide the arena's brass rings seen from below)
    for (y, x_w) in ((ENGINE - 2, HOLD + 3), (DECK - 2, GUN + 3)):
        for z in range(-27, 30, 6):
            w = int(hull_w(x_w, z))
            for x in range(-w + 1, w):
                if is_air(bp, x, y, z) and not is_air(bp, x, y + 1, z):
                    bp.set(x, y, z, IRON_SLAB + "[type=top]")
    # cockpit: the pilots' console under the eyes, two seats, levers and gauges
    zc = HEAD_Z + 3
    for x in range(-6, 7):
        if is_air(bp, x, GUN, zc):
            bp.set(x, GUN, zc, IRON)
            bp.set(x, GUN + 1, zc, GAUGE if x % 3 == 0 else (BRASS_SLAB if x % 3 == 1 else
                                                            "lever[face=floor,facing=south,powered=false]"))
    for x in (-3, 3):
        bp.set(x, GUN, zc + 2, stair(MAHOGANY_STAIRS, "south"))
    bp.set(0, GUN, zc + 1, MAHOGANY)
    bp.set(0, GUN + 1, zc + 1, GEAR)
    for x in (-6, 6):
        for y in range(GUN, GUN + 4):
            if is_air(bp, x, y, zc + 4):
                bp.set(x, y, zc + 4, PIPES)


def walking_fortress(bp):
    crater(bp)
    hull(bp)
    portholes(bp)
    # planted legs: front-left and back-right (the routes); front-right lifted, back-left trailing
    walk_leg(bp, -1, FRONT_Z, True)
    walk_leg(bp, 1, BACK_Z, False)
    dead_leg(bp, 1, FRONT_Z, (KNEE_X, 48, -34), (KNEE_X, 22, -46), (KNEE_X, 14, -50))
    dead_leg(bp, -1, BACK_Z, (-KNEE_X, 44, 28), (-KNEE_X, 6, 38), (-KNEE_X, 0, 40))
    hold(bp)
    engine_room(bp)
    gun_deck(bp)
    stacks(bp)
    head(bp)
    hull_details(bp)
    companionway(bp)
    bridge_tower(bp)
    arena(bp)
    dressing(bp)
    fallen_stack(bp)
    rubble(bp)
    scavenger_camp(bp)


# interior shots for the CI focus run: (name, feet, look at)
VIEWS = [
    ("knee", (-36, KNEE_FLOOR, -27), (-44, KNEE_FLOOR + 2, -21)),
    ("hold", (6, HOLD, 22), (-3, HOLD + 2, -24)),
    ("engine", (-8, ENGINE + 6, 14), (2, ENGINE + 3, -12)),
    ("gun_deck", (-11, GUN, 23), (5, GUN + 2, -24)),
    ("cockpit", (0, GUN, -38), (0, GUN + 2, -52)),
    ("bridge", (6, DECK, -23), (-6, DECK + 1, -30)),
    ("arena", (13, DECK, 20), (0, DECK + 3, -18)),
]


register(StructureDef(
    "walking_fortress", "overworld",
    ["#minecraft:is_badlands", "savanna", "savanna_plateau", "windswept_savanna", "plains", "desert"],
    [Piece("walker", walking_fortress, views=VIEWS)],
    spacing=80, separation=32, adaptation="beard_box", processors="none", max_distance=100,
    exclusion=("brasshaven:clockwork_citadel", 8),
    title_fr="Forteresse marchante", title_en="Walking Fortress"))

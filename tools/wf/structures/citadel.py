"""The Sunken Citadel: the mod's flagship dungeon and home of the Drowned Warden boss.

It is a single watertight template (a jigsaw layout would leave unsealed doorways whenever a
branch fails to place, flooding the halls). A gothic fortress-cathedral of prismarine sits on
the ocean floor:

  * a lookout tower in the south that breaks the sea surface (waystone in the glass cabin),
    with a full-block spiral stair down to the
  * nave, a tall pointed-vault hall with flying buttresses, opening north into the
  * boss arena, a ribbed glass dome on a windowed drum, the boss seal in the centre and boss mist
    across its three doorways;
    behind it the treasure vault, sealed by bars that fall when the boss dies;
  * six themed halls (three per side) linked by gothic glass tunnels; three variants
    shuffle the themes between the halls.

Watertightness rules followed everywhere: the hull is made of full, non-waterloggable blocks
(glass blocks, never panes), and no waterloggable block (stairs, slabs, walls, chests, lanterns,
chains, ladders...) is placed inside, because template placement waterlogs anything that was
put where the ocean used to be. Light comes from sea lanterns, lithite and froglights; loot sits
in barrels.
"""
import math
import random

from .. import interior as I
from ..arch import Palette, stair
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOD

HULL = Palette({"prismarine_bricks": 8, "prismarine": 3}, seed=3, scale=1.6)
TRIM = "dark_prismarine"
TRIM_S = "dark_prismarine_stairs"
BRICK_S = "prismarine_brick_stairs"
LB = "brasshaven:lithite_bricks"
LC = "brasshaven:lithite_block"
SEA = "sea_lantern"
GLASS = "glass"
AIR = "minecraft:air"

ARENA = (0, -8)       # centre of the domed arena
AR = 14               # arena interior radius
DRUM = 20             # drum height (dome springs here)


def pointed(u, a, k=1.5):
    """Rise of a pointed arch of half-width a at offset u (None outside)."""
    u = abs(u)
    if u > a:
        return None
    r = a * k
    return math.sqrt(max(0.0, r * r - (u + r - a) ** 2))


def pinnacle(bp, x, y, z, h=3):
    """Small gothic pinnacle: dark prismarine shaft, slender wall, end-rod finial."""
    for k in range(h):
        bp.set(x, y + k, z, TRIM)
    bp.set(x, y + h, z, "prismarine_wall")
    bp.set(x, y + h + 1, z, "end_rod[facing=up]")


def spire(bp, cx, cz, y, r, finial=True):
    """Steep pyramid spire of dark prismarine stairs (exterior only)."""
    yy = y
    rr = r
    while rr >= 1:
        for k in range(2):
            for x in range(cx - rr, cx + rr + 1):
                for z in range(cz - rr, cz + rr + 1):
                    edge = max(abs(x - cx), abs(z - cz)) == rr
                    if k == 1 and edge:
                        dx, dz = cx - x, cz - z
                        f = ("east" if dx > 0 else "west") if abs(dx) >= abs(dz) else ("south" if dz > 0 else "north")
                        bp.set(x, yy, z, stair(TRIM_S, f))
                    else:
                        bp.set(x, yy, z, TRIM)
            yy += 1
        rr -= 1
    bp.set(cx, yy, cz, TRIM)
    bp.set(cx, yy + 1, cz, "prismarine_wall")
    if finial:
        bp.set(cx, yy + 2, cz, "end_rod[facing=up]")
    return yy + 2


# ------------------------------------------------------------------ gothic hall
def hall_shell(bp, x0, z0, x1, z1, hw, axis, flying=False, rose=(True, True), lit_ridge=True, avoid=()):
    """Gothic hall on outer walls x0..x1 / z0..z1; ridge along `axis`. Interior floor y=0,
    walls to hw, pointed vault inside, steep dark prismarine roof outside, lancet windows,
    stepped buttresses with pinnacles (detached flying buttresses when flying=True)."""
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    if axis == "z":
        a_lo, a_hi, v_lo, v_hi, ac = x0, x1, z0, z1, cx
    else:
        a_lo, a_hi, v_lo, v_hi, ac = z0, z1, x0, x1, cz
    a_in = (a_hi - a_lo - 1) / 2.0
    n_cols = a_hi - a_lo + 3                    # across cells incl. 1 overhang each side
    centre_e = (n_cols - 1) // 2
    base = hw + 1

    def P(a, v):
        return (a, v) if axis == "z" else (v, a)

    bays = list(range(v_lo + 2, v_hi - 1, 4))

    def clear_of(a, v):
        x, z = P(a, v)
        return not any(r[0] <= x <= r[2] and r[1] <= z <= r[3] for r in avoid)
    # ---------------- masonry, vault and roof, column by column
    for a in range(a_lo - 1, a_hi + 2):
        e = min(a - (a_lo - 1), (a_hi + 1) - a)
        u = a - ac
        top = base + 2 * e                        # full block of the roof surface
        is_ridge = e == centre_e
        for v in range(v_lo - 1, v_hi + 2):
            x, z = P(a, v)
            over = a in (a_lo - 1, a_hi + 1) or v in (v_lo - 1, v_hi + 1)
            if over:
                # overhanging eave: stair surface only, with an upside-down stair below
                if a in (a_lo - 1, a_hi + 1):
                    f = (("east" if a < ac else "west") if axis == "z" else ("south" if a < ac else "north"))
                    bp.set(x, top, z, TRIM)
                    bp.set(x, top + 1, z, stair(TRIM_S, f))
                    bp.set(x, top - 1, z, stair(TRIM_S, {"east": "west", "west": "east", "south": "north",
                                                         "north": "south"}[f], "top"))
                else:
                    # barge course over the gable: just the roof skin, with a shadow stair below
                    bp.set(x, top, z, TRIM)
                    toward = ("south" if v == v_lo - 1 else "north") if axis == "z" else \
                        ("east" if v == v_lo - 1 else "west")
                    bp.set(x, top - 1, z, stair(TRIM_S, toward, "top"))
                    if not is_ridge:
                        f = (("east" if a < ac else "west") if axis == "z" else ("south" if a < ac else "north"))
                        bp.set(x, top + 1, z, stair(TRIM_S, f))
                    else:
                        bp.set(x, top + 1, z, TRIM)
                continue
            wall = a in (a_lo, a_hi) or v in (v_lo, v_hi)
            for y in range(-4, 0):
                bp.set(x, y, z, HULL.pick(x, y, z))
            ceil = None if wall else hw + (pointed(u, a_in) or 0)
            for y in range(0, top + 1):
                if y == 0:
                    if wall:
                        b = LB
                    else:
                        b = TRIM if (abs(u) < 1 or (v - v_lo) % 4 == 2) else "prismarine_bricks"
                    bp.set(x, y, z, b)
                elif ceil is not None and y < ceil:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, HULL.pick(x, y, z) if y < top else TRIM)
            if is_ridge:
                bp.set(x, top + 1, z, SEA if (lit_ridge and (v - v_lo) % 4 == 2) else TRIM)
            else:
                f = (("east" if a < ac else "west") if axis == "z" else ("south" if a < ac else "north"))
                bp.set(x, top + 1, z, stair(TRIM_S, f))
    # ---------------- interior: ribs, ridge lights, wall shafts
    for v in range(v_lo + 1, v_hi):
        for a in range(a_lo + 1, a_hi):
            x, z = P(a, v)
            u = a - ac
            cy = int(math.ceil(hw + (pointed(u, a_in) or 0) - 1e-9))
            if v in bays:
                bp.set(x, cy - 1, z, TRIM)            # transverse rib, one block proud
            if abs(u) < 1:
                bp.set(x, cy, z, LC if (v - v_lo) % 4 == 0 else LB)
    for v in bays:
        for a, d in ((a_lo + 1, 1), (a_hi - 1, -1)):
            x, z = P(a, v)
            for y in range(1, hw):
                bp.set(x, y, z, TRIM if y % 5 else LB)
            bp.set(x, hw - 1, z, SEA)
    # ---------------- exterior walls: plinth course, cornice, lancets, buttresses
    for v in range(v_lo, v_hi + 1):
        for a in (a_lo, a_hi):
            x, z = P(a, v)
            bp.set(x, hw, z, LB)
            bp.set(x, 1, z, LB)
    for a in range(a_lo, a_hi + 1):
        for v in (v_lo, v_hi):
            x, z = P(a, v)
            bp.set(x, 1, z, LB)
    lancets = []
    for b0, b1 in zip([v_lo] + bays, bays + [v_hi]):
        if b1 - b0 >= 3:
            lancets.append((b0 + b1) // 2)
    for vm in lancets:
        for a in (a_lo, a_hi):
            for dv in ((0,) if (vm - v_lo) % 2 else (0, 1)):
                for y in range(3, hw - 1):
                    x, z = P(a, vm + dv)
                    bp.set(x, y, z, GLASS)
            x, z = P(a, vm)
            bp.set(x, hw - 1, z, GLASS)
    for v in bays:
        for a, out in ((a_lo, -1), (a_hi, 1)):
            if not clear_of(a + out, v):
                continue
            for d in (1, 2):
                x, z = P(a + out * d, v)
                h = hw + 1 if d == 1 else hw - 4
                for y in range(-1, h + 1):
                    bp.set(x, y, z, TRIM if d == 1 else HULL.pick(x, y, z))
                f = ("west" if out < 0 else "east") if axis == "z" else ("north" if out < 0 else "south")
                opp = {"west": "east", "east": "west", "north": "south", "south": "north"}[f]
                bp.set(x, h + 1, z, stair(TRIM_S, opp) if d == 2 else TRIM)
            x, z = P(a + out, v)
            pinnacle(bp, x, hw + 2, z, 2)
            if flying:
                # detached pier and a flying arch leaping back to the clerestory
                for k in (4, 5):
                    px, pz = P(a + out * k, v)
                    for y in range(-1, hw - 1):
                        bp.set(px, y, pz, TRIM if k == 4 else HULL.pick(px, y, pz))
                px, pz = P(a + out * 4, v)
                pinnacle(bp, px, hw - 1, pz, 3)
                for k, y in ((3, hw - 2), (2, hw - 1)):
                    qx, qz = P(a + out * k, v)
                    bp.set(qx, y, qz, TRIM)
                    bp.set(qx, y - 1, qz, stair(TRIM_S, opp, "top"))
                qx, qz = P(a + out * 5, v)
                bp.set(qx, hw - 1, qz, stair(TRIM_S, opp))
    # ---------------- corner turrets
    for a, out_a in ((a_lo, -1), (a_hi, 1)):
        for v, out_v in ((v_lo, -1), (v_hi, 1)):
            for da in (0, 1):
                for dv in (0, 1):
                    x, z = P(a + out_a * da, v + out_v * dv)
                    for y in range(-1, hw + 3):
                        bp.set(x, y, z, TRIM if (da + dv) else LB)
            x, z = P(a + out_a, v + out_v)
            pinnacle(bp, x, hw + 3, z, 2)
            x, z = P(a, v)
            pinnacle(bp, x, hw + 3, z, 3)
    # ---------------- rose windows in the gables
    for v, want in ((v_lo, rose[0]), (v_hi, rose[1])):
        if not want:
            continue
        ry = hw + 4
        for a in range(a_lo, a_hi + 1):
            for y in range(ry - 4, ry + 5):
                u = a - ac
                d = math.hypot(u, y - ry)
                x, z = P(a, v)
                if d <= 3.6:
                    bp.set(x, y, z, LC if d < 0.8 else TRIM if (abs(u) < 0.6 or abs(y - ry) < 0.6 or 2.6 < d) else GLASS)
    # ---------------- roof: dormers on both slopes and a fleche on the ridge
    ridge_top = base + 2 * centre_e
    for vm in lancets[1::2]:
        for side in (-1, 1):
            e = 3
            a = (a_lo - 1 + e) if side < 0 else (a_hi + 1 - e)
            y0 = base + 2 * e + 1
            for dv in (-1, 0, 1):
                x, z = P(a, vm + dv)
                for y in range(y0, y0 + 3):
                    bp.set(x, y, z, TRIM if dv else (GLASS if y < y0 + 2 else TRIM))
                if dv:
                    f = ("south" if dv < 0 else "north") if axis == "z" else ("east" if dv < 0 else "west")
                    bp.set(x, y0 + 3, z, stair(TRIM_S, f))
                else:
                    bp.set(x, y0 + 3, z, TRIM)
                    bp.set(x, y0 + 4, z, "prismarine_wall")
    vm = (v_lo + v_hi) // 2
    for a in range(a_lo - 1, a_hi + 2):
        if min(a - (a_lo - 1), (a_hi + 1) - a) == centre_e:
            x, z = P(a, vm)
            for y in range(ridge_top + 1, ridge_top + 4):
                bp.set(x, y, z, TRIM if y < ridge_top + 3 else SEA)
            spire(bp, x, z, ridge_top + 4, 1)
            break
    return bays


# ------------------------------------------------------------------ glass tunnels
def glass_tunnel(bp, p0, p1, axis):
    """Gothic glass tunnel between p0 and p1 (centre line; along x or z). Interior 5 wide,
    pointed glass vault, dark prismarine ribs every 4 blocks, sea lanterns in the floor."""
    (x0, z0), (x1, z1) = p0, p1
    if axis == "x":
        lo, hi, c = min(x0, x1), max(x0, x1), z0
    else:
        lo, hi, c = min(z0, z1), max(z0, z1), x0
    for v in range(lo, hi + 1):
        rib = (v - lo) % 4 == 0
        for u in range(-4, 5):
            x, z = (v, c + u) if axis == "x" else (c + u, v)
            au = abs(u)
            for y in range(-3, 9):
                b = None
                if y <= 0 and au <= 3:
                    b = HULL.pick(x, y, z) if y < 0 or au == 3 else (SEA if (u == 0 and (v - lo) % 4 == 2) else TRIM)
                elif au <= 2 and 1 <= y <= 4 or au <= 1 and y == 5 or au == 0 and y == 6:
                    b = "air"
                elif (au == 3 and 1 <= y <= 4) or (au == 2 and y == 5) or (au == 1 and y == 6) or (au == 0 and y == 7):
                    b = TRIM if rib or y == 1 else GLASS
                elif rib and ((au == 4 and 0 <= y <= 4) or (au == 3 and y == 5) or (au == 2 and y == 6)
                              or (au == 1 and y == 7) or (au == 0 and y == 8)):
                    b = TRIM
                if b:
                    bp.set(x, y, z, b)


def carve_tunnel(bp, p0, p1, axis):
    """Re-open the tunnel profile (after the halls were built) to make the doorways."""
    (x0, z0), (x1, z1) = p0, p1
    if axis == "x":
        lo, hi, c = min(x0, x1), max(x0, x1), z0
    else:
        lo, hi, c = min(z0, z1), max(z0, z1), x0
    for v in range(lo, hi + 1):
        for u in range(-2, 3):
            x, z = (v, c + u) if axis == "x" else (c + u, v)
            for y in range(1, 7):
                if abs(u) <= 2 and y <= 4 or abs(u) <= 1 and y == 5 or u == 0 and y == 6:
                    bp.set(x, y, z, "air")
            bp.set(x, 0, z, TRIM)


# ------------------------------------------------------------------ the arena
def arena(bp):
    ax, az = ARENA
    R = AR
    # drum, floor and dome
    for x in range(ax - R - 3, ax + R + 4):
        for z in range(az - R - 3, az + R + 4):
            d = math.hypot(x - ax, z - az)
            if d > R + 2.0:
                continue
            for y in range(-4, 0):
                bp.set(x, y, z, HULL.pick(x, y, z))
            if d <= R + 0.5:
                if d < 1.6:
                    b = TRIM
                elif 4.5 <= d < 5.5:
                    b = SEA if int(math.degrees(math.atan2(z - az, x - ax)) + 360) % 30 < 15 else LB
                elif 9.3 <= d < 10.3:
                    b = LB
                elif int(round(math.degrees(math.atan2(z - az, x - ax)) / 22.5)) % 2 == 0 and d > 5.5:
                    b = "prismarine_bricks"
                else:
                    b = TRIM
                bp.set(x, 0, z, b)
                for y in range(1, DRUM + 1):
                    bp.set(x, y, z, "air")
            elif d <= R + 2.0:
                for y in range(0, DRUM + 1):
                    bp.set(x, y, z, HULL.pick(x, y, z) if d > R + 1.0 or y in (0, 1, DRUM) else HULL.pick(x, y, z))
    # pointed (ogival) dome springing from the drum: 16 ribs, a glass belt, a ring of sea
    # lanterns and a glazed oculus under the lantern
    Rd, T = R + 0.5, 2.6
    rise_in = pointed(0, Rd)
    for x in range(ax - R - 4, ax + R + 5):
        for z in range(az - R - 4, az + R + 5):
            rho = math.hypot(x - ax, z - az)
            hin, hout = pointed(rho, Rd), pointed(rho, Rd + T)
            if hout is None:
                continue
            ang = math.atan2(z - az, x - ax) % (math.pi / 8)
            rib = min(ang, math.pi / 8 - ang) * max(rho, 1) < 0.95
            for y in range(DRUM + 1, DRUM + int(hout) + 1):
                dy = y - DRUM
                if hin is not None and dy <= hin:
                    bp.set(x, y, z, "air")
                    continue
                f = dy / rise_in
                if rho < 2.3:
                    b = GLASS
                elif f < 0.1:
                    b = LB
                elif rib:
                    b = TRIM
                elif 0.66 <= f < 0.72:
                    b = SEA
                elif 0.12 < f < 0.62:
                    b = GLASS
                else:
                    b = "prismarine_bricks"
                bp.set(x, y, z, b)
    top = DRUM + int(pointed(0, Rd + T))
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = ax + round(math.cos(a) * 3.2), az + round(math.sin(a) * 3.2)
        for y in range(top + 1, top + 7):
            bp.set(x, y, z, TRIM)
        pinnacle(bp, x, top + 7, z, 1)
    for x in range(ax - 3, ax + 4):
        for z in range(az - 3, az + 4):
            if math.hypot(x - ax, z - az) <= 3.0:
                for y in range(top + 1, top + 7):
                    if bp.get(x, y, z) is None:
                        bp.set(x, y, z, SEA if y in (top + 2, top + 5) and math.hypot(x - ax, z - az) < 1.5 else GLASS)
    spire(bp, ax, az, top + 7, 4)
    # drum: 16 inner pilasters with lithite bands, lancet windows between them
    for k in range(16):
        a = math.radians(k * 22.5)
        px, pz = ax + round(math.cos(a) * (R - 0.2)), az + round(math.sin(a) * (R - 0.2))
        for y in range(1, DRUM + 1):
            bp.set(px, y, pz, TRIM if y % 6 else LB)
        bp.set(px, DRUM - 1, pz, SEA)
        wa = math.radians(k * 22.5 + 11.25)
        for rr in (R + 1, R + 1.6):
            wx, wz = ax + round(math.cos(wa) * rr), az + round(math.sin(wa) * rr)
            for y in range(4, 12):
                bp.set(wx, y, wz, GLASS)
            bp.set(wx, 12, wz, GLASS if rr == R + 1 else TRIM)
    # ambulatory columns
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        px, pz = ax + round(math.cos(a) * 10.5), az + round(math.sin(a) * 10.5)
        for y in range(1, DRUM + 1):
            bp.set(px, y, pz, LB if y in (1, 6, 12) else TRIM)
        bp.set(px, DRUM + 1, pz, SEA)
    # the altar dais
    for x in range(ax - 3, ax + 4):
        for z in range(az - 3, az + 4):
            if abs(x - ax) + abs(z - az) <= 5:
                bp.set(x, 1, z, TRIM)
            if abs(x - ax) <= 2 and abs(z - az) <= 2:
                bp.set(x, 1, z, TRIM)
            if abs(x - ax) <= 1 and abs(z - az) <= 1:
                bp.set(x, 2, z, LB)
    for x, z in ((ax - 2, az - 2), (ax + 2, az - 2), (ax - 2, az + 2), (ax + 2, az + 2)):
        bp.set(x, 2, z, "prismarine_bricks")
        bp.set(x, 3, z, TRIM)
        bp.set(x, 4, z, SEA)
    bp.boss_seal(ax, 3, az, "brasshaven:drowned_warden", AR)
    # exterior flying buttresses around the drum
    for deg in (30, 150, 210, 240, 300, 330):
        a = math.radians(deg)
        ux, uz = math.cos(a), math.sin(a)
        # pier
        for r in (21, 22):
            for w in (-0.5, 0.5):
                px = ax + round(ux * r - uz * w)
                pz = az + round(uz * r + ux * w)
                for y in range(-1, 19):
                    bp.set(px, y, pz, TRIM if r == 21 else HULL.pick(px, y, pz))
        px, pz = ax + round(ux * 21), az + round(uz * 21)
        pinnacle(bp, px, 19, pz, 5)
        # flying arch from the pier head up to the top of the drum
        for r in range(16, 21):
            y = DRUM + 1 - int((r - 16) * 0.6)
            qx, qz = ax + round(ux * r), az + round(uz * r)
            bp.set(qx, y, qz, TRIM)
            bp.set(qx, y + 1, qz, "prismarine_bricks")
        # drum buttress pilaster
        for r in (R + 2, R + 3):
            qx, qz = ax + round(ux * r), az + round(uz * r)
            for y in range(-1, DRUM + 3 - (r - R - 2) * 3):
                bp.set(qx, y, qz, TRIM)


def vault(bp):
    """Treasure vault north of the arena, behind the sealed bars."""
    x0, z0, x1, z1 = -7, -39, 7, -26
    hall_shell(bp, x0, z0, x1, z1, 8, "x", rose=(False, False), avoid=((-4, -27, 4, -20),))
    cx = 0
    for x in range(x0 + 2, x1 - 1, 2):
        bp.barrel(x, 1, z0 + 1, "south", LOOT + "citadel_vault" if x % 4 == 1 else None)
    for x, z in ((x0 + 1, z1 - 1), (x0 + 2, z1 - 1), (x0 + 1, z1 - 2)):
        bp.set(x, 1, z, "gold_block")
    bp.set(x0 + 1, 2, z1 - 1, "gold_block")
    for x, z in ((x1 - 1, z1 - 1), (x1 - 2, z1 - 1), (x1 - 1, z1 - 2)):
        bp.set(x, 1, z, "emerald_block")
    bp.set(x1 - 1, 2, z1 - 1, "diamond_block")
    for x in range(cx - 1, cx + 2):
        for z in range(-34, -31):
            bp.set(x, 0, z, "iron_block")
    bp.set(cx, 1, -33, "beacon")
    # a glass lantern straight above the beacon so its beam climbs through the sea
    for y in range(2, 30):
        if bp.get(cx, y, -33) not in (None, AIR):
            bp.set(cx, y, -33, GLASS)
    for x in (cx - 3, cx + 3):
        bp.set(x, 1, -33, LC)
        bp.set(x, 2, -33, "prismarine_bricks")
        bp.set(x, 3, -33, SEA)


def vault_passage(bp):
    """Short passage arena -> vault, filled with sealed bars (removed when the Warden dies)."""
    ax, az = ARENA
    zs, ze = -27, az - AR - 1
    for z in range(zs, ze + 1):
        for x in range(-3, 4):
            for y in range(-1, 7):
                bp.set(x, y, z, HULL.pick(x, y, z) if abs(x) == 3 or y in (-1, 0, 6) else "air")
            bp.set(x, 0, z, TRIM)
        for x in (-2, -1, 0, 1, 2):
            if z == -25:
                for y in range(1, 6):
                    bp.set(x, y, z, MOD["vault_bars"])
    for x in range(-4, 5):
        for y in range(1, 7):
            if abs(x) == 4 or y == 6:
                bp.set(x, y, -24, LB if (x + y) % 2 else TRIM)
    bp.barrel(3 - 1, 1, ze + 2, "up", LOOT + "citadel_arena")


# ------------------------------------------------------------------ the entrance tower
def tower(bp):
    cx, cz = 0, 33
    x0, x1, z0, z1 = -6, 6, 27, 39
    BASE_H = 24
    SHAFT_TOP = 55
    r = 5
    # square base with corner buttresses
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            wall = x in (x0, x1) or z in (z0, z1)
            for y in range(-4, 0):
                bp.set(x, y, z, HULL.pick(x, y, z))
            bp.set(x, 0, z, TRIM if (x + z) % 2 else "prismarine_bricks")
            for y in range(1, BASE_H + 1):
                if wall or y == BASE_H:
                    bp.set(x, y, z, LB if y in (1, 12, BASE_H) else HULL.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
    for sx in (x0, x1):
        for sz in (z0, z1):
            for dx in (0, 1, 2):
                for dz in (0, 1, 2):
                    if dx + dz == 0:
                        continue
                    x = sx + (dx if sx == x1 else -dx)
                    z = sz + (dz if sz == z1 else -dz)
                    if dx and dz:
                        continue
                    h = BASE_H + 2 if max(dx, dz) == 1 else BASE_H - 6
                    for y in range(-1, h + 1):
                        bp.set(x, y, z, TRIM)
            pinnacle(bp, sx, BASE_H + 1, sz, 3)
    # lancet windows in the base faces
    for k in (-3, 3):
        for y in range(4, 11):
            bp.set(cx + k, y, z1, GLASS)
            bp.set(x0, y, cz + k, GLASS)
            bp.set(x1, y, cz + k, GLASS)
        for y in range(14, 21):
            bp.set(cx + k, y, z1, GLASS)
            bp.set(x0, y, cz + k, GLASS)
            bp.set(x1, y, cz + k, GLASS)
    # round shaft
    for y in range(BASE_H, SHAFT_TOP + 1):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= 4.5:
                    bp.set(x, y, z, "air")
                elif d <= r + 0.5:
                    bp.set(x, y, z, LB if y % 8 == 0 else HULL.pick(x, y, z))
    for k in range(8):   # shaft pilasters and slit windows
        a = math.radians(k * 45)
        px, pz = cx + round(math.cos(a) * (r + 1)), cz + round(math.sin(a) * (r + 1))
        for y in range(BASE_H - 2, SHAFT_TOP - 1):
            bp.set(px, y, pz, TRIM)
        wa = math.radians(k * 45 + 22.5)
        wx, wz = cx + round(math.cos(wa) * r), cz + round(math.sin(wa) * r)
        for y in range(BASE_H + 4 + (k % 2) * 6, SHAFT_TOP - 4, 12):
            for dy in range(3):
                bp.set(wx, y + dy, wz, GLASS)
    # flying buttresses from the corner pinnacles of the base up to the shaft
    for sx in (-1, 1):
        for sz in (-1, 1):
            for k, y in ((6, BASE_H + 4), (5, BASE_H + 6), (4, BASE_H + 8)):
                x, z = cx + sx * k, cz + sz * k
                bp.set(x, y, z, TRIM)
                bp.set(x, y - 1, z, stair(TRIM_S, "east" if sx < 0 else "west", "top"))
                bp.set(x, y + 1, z, "prismarine_bricks")
            for y in range(BASE_H + 1, BASE_H + 4):
                bp.set(cx + sx * 7, y, cz + sz * 7, TRIM)
            pinnacle(bp, cx + sx * 7, BASE_H + 4, cz + sz * 7, 2)
    # corbelled gallery under the cabin
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 8, cz + 9):
            d = math.hypot(x - cx, z - cz)
            if 4.5 < d <= 7.4:
                bp.set(x, SHAFT_TOP, z, TRIM)
                if d > 5.5:
                    bp.set(x, SHAFT_TOP - 1, z, stair(TRIM_S, _toward(x, z, cx, cz), "top"))
                if 6.4 < d:
                    bp.set(x, SHAFT_TOP + 1, z, "prismarine_wall")
    # glass lookout cabin above the waves, waystone inside
    cab = SHAFT_TOP + 1
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.5:
                bp.set(x, SHAFT_TOP, z, "dark_prismarine" if d > 2 else "prismarine_bricks")
                for y in range(cab, cab + 4):
                    bp.set(x, y, z, "air" if d <= 3.5 else (TRIM if (x - cx) % 3 == 0 and (z - cz) % 3 == 0 else GLASS))
                bp.set(x, cab + 4, z, TRIM)
    for k in range(8):
        a = math.radians(k * 45)
        px, pz = cx + round(math.cos(a) * 4), cz + round(math.sin(a) * 4)
        for y in range(cab, cab + 4):
            bp.set(px, y, pz, TRIM)
    # door on the north side: the stairwell opening is under the south half of the cabin floor
    bp.door(cx, cab, cz - 4, "north", "dark_oak")
    bp.set(cx + 2, cab, cz - 2, MOD["waystone"])
    bp.set(cx - 2, cab, cz - 2, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(cx, cab + 3, cz, SEA)
    spire(bp, cx, cz, cab + 5, 5)
    # full-block spiral stair from the cabin down to the floor, around a lantern-lit core
    for y in range(1, cab):
        for x in range(cx - 1, cx + 2):
            for z in range(cz - 1, cz + 2):
                if abs(x - cx) + abs(z - cz) <= 1:
                    bp.set(x, y, z, SEA if (y % 6 == 3 and (x, z) != (cx, cz)) else TRIM)
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if not (1.5 < d <= 4.5):
                continue
            k = int((math.degrees(math.atan2(z - cz, x - cx)) % 360) // 22.5)
            y = 1 + k
            while y <= cab - 2:
                bp.set(x, y, z, "prismarine_bricks" if d > 3 else TRIM)
                y += 16
            # opening in the cabin floor over the last steps of the stair
            if cab - 5 <= y - 16 <= cab - 2:
                bp.set(x, SHAFT_TOP, z, "air")
    # doorway into the nave (north face) and a guard post at the foot of the stair
    for x in range(-2, 3):
        for y in range(1, 7):
            if y <= 5 or abs(x) <= 1:
                bp.set(x, y, z0, "air")
    bp.barrel(x1 - 1, 1, z1 - 1, "up", LOOT + "citadel_common")
    for x, z in ((x0 + 1, z1 - 1), (x1 - 1, z0 + 1), (x0 + 1, z0 + 1)):
        bp.set(x, 1, z, SEA)


def _toward(x, z, cx, cz):
    dx, dz = cx - x, cz - z
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


# ------------------------------------------------------------------ room themes
# Each gets the interior bounds (x0, z0, x1, z1), the wall height and the hall axis.
def armory(bp, x0, z0, x1, z1, hw, rng):
    for x in range(x0 + 1, x1, 2):
        for z in (z0 + 1, z1 - 1):
            bp.entity(x, 1, z, {"id": "minecraft:armor_stand", "Rotation": [0.0 if z == z0 + 1 else 180.0, 0.0]})
            bp.set(x, 0, z, "polished_andesite")
    for z in range(z0 + 1, z1, 3):
        for x in (x0, x1):
            bp.set(x + (1 if x == x0 else -1), 3, z, f"cyan_wall_banner[facing={'east' if x == x0 else 'west'}]")
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for x in range(x0 + 3, x1 - 2):
        for z in (cz - 2, cz + 2):
            bp.set(x, 1, z, "dark_prismarine" if x % 3 else "smithing_table")
    for z in (cz - 2, cz + 2):
        bp.set(x0 + 3, 2, z, "hay_block[axis=y]")
        bp.set(x0 + 3, 3, z, "carved_pumpkin[facing=east]")
    bp.set(x1 - 1, 1, cz - 1, "anvil[facing=north]")
    bp.set(x1 - 1, 1, cz + 1, "grindstone[face=floor,facing=west]")
    bp.barrel(x1 - 1, 1, cz, "west", LOOT + "citadel_armory")
    bp.barrel(x0 + 1, 1, cz, "east", LOOT + "citadel_armory")
    bp.spawner(cx, 1, cz, "minecraft:drowned")


def library(bp, x0, z0, x1, z1, hw, rng):
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            if edge and (x + z) % 6:
                for y in range(1, 5):
                    bp.set(x, y, z, "bookshelf" if rng.random() > 0.15 else "chiseled_bookshelf[facing=north,"
                           "slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,"
                           "slot_4_occupied=false,slot_5_occupied=true]")
    for x in range(x0 + 2, x1 - 1, 3):
        for z in range(z0 + 3, z1 - 2):
            if abs(z - cz) > 1:
                for y in (1, 2, 3):
                    bp.set(x, y, z, "bookshelf")
    bp.set(cx, 1, cz, "enchanting_table")
    for x, z in ((cx - 2, cz), (cx + 2, cz)):
        bp.set(x, 1, z, "lectern[facing=north,has_book=false,powered=false]")
    for x in range(cx - 1, cx + 2):
        for z in (cz - 1, cz + 1):
            bp.set(x, 0, z, LB)
    bp.barrel(x1 - 1, 1, z1 - 1, "up", LOOT + "citadel_library")
    bp.set(cx, hw - 1, cz, SEA)


def aquarium(bp, x0, z0, x1, z1, hw, rng):
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    corals = ["brain_coral_block", "tube_coral_block", "bubble_coral_block", "fire_coral_block", "horn_coral_block"]
    tanks = [(x0 + 2, z0 + 2), (x1 - 4, z0 + 2), (x0 + 2, z1 - 4), (x1 - 4, z1 - 4)]
    # the walk around the tanks runs along the wall, where the bay shafts stand: they start above head height
    # here, or a shaft and a tank corner close off the far side of the hall
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x in (x0, x1) or z in (z0, z1):
                for y in (1, 2):
                    if bp.get(x, y, z) not in (None, "minecraft:air"):
                        bp.set(x, y, z, "air")
    for i, (tx, tz) in enumerate(tanks):
        for x in range(tx - 1, tx + 4):
            for z in range(tz - 1, tz + 4):
                for y in range(1, 7):
                    shell = x in (tx - 1, tx + 3) or z in (tz - 1, tz + 3) or y == 6
                    bp.set(x, y, z, (TRIM if (x in (tx - 1, tx + 3) and z in (tz - 1, tz + 3)) or y == 6 else GLASS)
                           if shell else "water")
                bp.set(x, 0, z, "sand" if (x + z) % 3 else "gravel")
        bp.set(tx, 1, tz, corals[i % 5])
        bp.set(tx + 2, 1, tz + 2, corals[(i + 2) % 5])
        bp.set(tx + 2, 1, tz, "sea_pickle[pickles=4,waterlogged=true]")
        for y in range(1, 5):
            bp.set(tx, y + 1, tz + 2, "kelp_plant" if y < 4 else "kelp[age=22]")
        bp.set(tx + 1, 6, tz + 1, SEA)
        bp.entity(tx + 1, 2, tz + 1, {"id": "minecraft:tropical_fish", "PersistenceRequired": 1, "Variant": 65536 * (i + 1)})
    # central round tank with a glow squid
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            d = math.hypot(x - cx, z - cz)
            if d <= 2.6:
                for y in range(1, 8):
                    bp.set(x, y, z, "water" if d <= 1.6 and y < 7 else GLASS if y < 7 else TRIM)
                bp.set(x, 0, z, SEA if d < 1 else "sand")
    bp.entity(cx, 3, cz, {"id": "minecraft:glow_squid", "PersistenceRequired": 1})
    bp.barrel(x1 - 1, 1, cz, "west", LOOT + "citadel_common")


def prison(bp, x0, z0, x1, z1, hw, rng):
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    long_x = (x1 - x0) >= (z1 - z0)
    cells = range(x0 + 1, x1 - 2, 4) if long_x else range(z0 + 1, z1 - 2, 4)
    for side in (0, 1):
        for c in cells:
            for a in range(c, c + 4):
                for b in range(0, 4):
                    if long_x:
                        x, z = a, (z0 + b if side == 0 else z1 - b)
                        front = b == 3
                        sidew = a in (c, c + 3)
                    else:
                        x, z = (x0 + b if side == 0 else x1 - b), a
                        front = b == 3
                        sidew = a in (c, c + 3)
                    for y in range(1, 5):
                        if sidew or front or y == 4:
                            bp.set(x, y, z, TRIM if y != 2 or not front else GLASS)
                        else:
                            bp.set(x, y, z, "air")
            # iron door in the middle of the front
            if long_x:
                dx, dz = c + 1, (z0 + 3 if side == 0 else z1 - 3)
                bp.door(dx, 1, dz, "north" if side == 0 else "south", "iron")
                bp.set(dx + 1, 2, dz + (1 if side == 0 else -1), "stone_button[face=wall,facing=" +
                       ("south" if side == 0 else "north") + ",powered=false]")
                inner = (c + 2, z0 + 1 if side == 0 else z1 - 1)
            else:
                dx, dz = (x0 + 3 if side == 0 else x1 - 3), c + 1
                bp.door(dx, 1, dz, "west" if side == 0 else "east", "iron")
                bp.set(dx + (1 if side == 0 else -1), 2, dz + 1, "stone_button[face=wall,facing=" +
                       ("east" if side == 0 else "west") + ",powered=false]")
                inner = (x0 + 1 if side == 0 else x1 - 1, c + 2)
            bp.set(inner[0], 1, inner[1], rng.choice(["bone_block[axis=y]", "cobweb", "red_carpet", "cobweb"]))
    bp.set(cx, 1, cz, "lectern[facing=south,has_book=false,powered=false]")
    bp.barrel(cx + 1, 1, cz, "up", LOOT + "citadel_common")
    bp.spawner(cx - 1, 1, cz, "minecraft:drowned")
    for x, z in ((cx, cz - 2), (cx, cz + 2)):
        bp.set(x, 1, z, "soul_torch")


def garden(bp, x0, z0, x1, z1, hw, rng):
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if abs(x - cx) <= 1 or abs(z - cz) <= 1:
                bp.set(x, 0, z, "prismarine_bricks")
                continue
            bp.set(x, 0, z, "moss_block")
            r = rng.random()
            if r < 0.15:
                bp.set(x, 1, z, rng.choice(["azalea", "flowering_azalea"]))
            elif r < 0.45:
                bp.set(x, 1, z, rng.choice(["moss_carpet", "fern", "short_grass", "allium", "blue_orchid",
                                            "lily_of_the_valley", "torchflower"]))
    # sunken pond in the middle, flush with the floor
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if abs(x - cx) + abs(z - cz) <= 3:
                bp.set(x, 0, z, "water")
                bp.set(x, -1, z, "mud" if (x + z) % 2 else "clay")
                bp.set(x, 1, z, "air")
    bp.set(cx, 1, cz, "lily_pad")
    bp.set(cx + 1, 1, cz - 1, "lily_pad")
    # glow berries and a spore blossom from the vault
    for x, z in ((x0 + 2, z0 + 2), (x1 - 2, z0 + 2), (x0 + 2, z1 - 2), (x1 - 2, z1 - 2)):
        top = hw + 1
        while bp.get(x, top, z) == AIR:
            top += 1
        for y in range(top - 4, top):
            bp.set(x, y, z, "cave_vines_plant[berries=true]" if y > top - 4 else "cave_vines[age=20,berries=true]")
        bp.set(x, top, z, "shroomlight")
    y = hw
    while bp.get(cx, y + 1, cz) == AIR:
        y += 1
    bp.set(cx, y, cz, "spore_blossom")
    bp.barrel(x1 - 1, 1, z1 - 1, "up", LOOT + "citadel_common")


def shrine(bp, x0, z0, x1, z1, hw, rng):
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    long_x = (x1 - x0) > (z1 - z0)
    # altar dais at the far end with a conduit floating in a sealed water vessel
    if long_x:
        ax, az, fwd = x0 + 3, cz, (1, 0)
    else:
        ax, az, fwd = cx, z0 + 3, (0, 1)
    for x in range(ax - 2, ax + 3):
        for z in range(az - 2, az + 3):
            bp.set(x, 1, z, TRIM)
    for x in range(ax - 1, ax + 2):
        for z in range(az - 1, az + 2):
            for y in range(2, 5):
                edge = abs(x - ax) == 1 or abs(z - az) == 1 or y == 4
                bp.set(x, y, z, (TRIM if abs(x - ax) == 1 and abs(z - az) == 1 else GLASS) if edge else "water")
    bp.set(ax, 3, az, "conduit[waterlogged=true]")
    bp.set(ax, 2, az, "water")
    # guardian-eye pillars
    for s in (-1, 1):
        px, pz = (ax + fwd[1] * 3 * s, az + fwd[0] * 3 * s)
        for y in range(1, hw):
            bp.set(px, y, pz, "prismarine_bricks" if y % 4 else SEA)
    # pews: dark prismarine benches with cyan cushions
    for k in range(5, 12, 2):
        for w in list(range(-4, -1)) + list(range(2, 5)):
            x, z = (ax + fwd[0] * k + fwd[1] * w, az + fwd[1] * k + fwd[0] * w)
            if x0 < x < x1 and z0 < z < z1:
                bp.set(x, 1, z, "dark_prismarine")
                bp.set(x, 2, z, "cyan_carpet")
    bp.barrel(ax + fwd[1] * 2 + fwd[0] * 1, 1, az + fwd[0] * 2 + fwd[1] * 1, "up", LOOT + "citadel_shrine")


THEMES = [armory, library, aquarium, prison, garden, shrine]

# halls: (x0, z0, x1, z1, wall height, ridge axis)
HALLS = {
    "W1": (-34, 8, -20, 26, 12, "z"), "E1": (20, 8, 34, 26, 12, "z"),
    "W2": (-38, -19, -24, -1, 13, "z"), "E2": (24, -19, 38, -1, 13, "z"),
    "W3": (-31, -38, -17, -24, 11, "x"), "E3": (17, -38, 31, -24, 11, "x"),
}
TUNNELS = [  # (p0, p1, axis)
    ((-21, 17), (-6, 17), "x"), ((6, 17), (21, 17), "x"),                # nave <-> W1 / E1
    ((-27, -2), (-27, 9), "z"), ((27, -2), (27, 9), "z"),                # W1 <-> W2, E1 <-> E2
    ((-27, -25), (-27, -18), "z"), ((27, -25), (27, -18), "z"),          # W2 <-> W3, E2 <-> E3
    ((-25, -10), (-12, -10), "x"), ((12, -10), (25, -10), "x"),          # W2 / E2 <-> arena
]

# tunnel corridors (with a margin) where halls must not grow buttresses
AVOID = tuple((min(p0[0], p1[0]), p0[1] - 3, max(p0[0], p1[0]), p0[1] + 3) if ax == "x" else
              (p0[0] - 3, min(p0[1], p1[1]), p0[0] + 3, max(p0[1], p1[1])) for p0, p1, ax in TUNNELS)


def _inner(p0, p1, axis):
    """Tunnel span strictly between the walls it joins (outside every hall and the drum)."""
    i = 0 if axis == "x" else 1
    lo, hi = sorted((p0[i], p1[i]))
    lo, hi = lo + 2, hi - 2
    ax, az = ARENA
    while math.hypot(*((lo - ax, p0[1] - az) if axis == "x" else (p0[0] - ax, lo - az))) <= AR + 2.5:
        lo += 1
    while math.hypot(*((hi - ax, p0[1] - az) if axis == "x" else (p0[0] - ax, hi - az))) <= AR + 2.5:
        hi -= 1
    return ((lo, p0[1]), (hi, p0[1])) if axis == "x" else ((p0[0], lo), (p0[0], hi))


def citadel(variant):
    def build(bp):
        rng = random.Random(f"citadel-{variant}")
        bp.rng.seed(f"citadel-{variant}")
        # glass tunnels first: every hall rebuilt afterwards re-seals its own walls
        for p0, p1, axis in TUNNELS:
            glass_tunnel(bp, p0, p1, axis)
        # the nave, tall with flying buttresses, opening on the tower and the arena
        hall_shell(bp, -7, 7, 7, 27, 16, "z", flying=True, rose=(False, False), avoid=AVOID)
        themes = THEMES[:]
        rng.shuffle(themes)
        bare = []           # halls whose theme fills the floor (cells, tanks): no clutter on top of it
        for theme, key in zip(themes, ["W1", "E1", "W2", "E2", "W3", "E3"]):
            x0, z0, x1, z1, hw, axis = HALLS[key]
            hall_shell(bp, x0, z0, x1, z1, hw, axis, avoid=AVOID)
            theme(bp, x0 + 1, z0 + 1, x1 - 1, z1 - 1, hw, rng)
            if theme in (prison, aquarium):
                bare.append((x0, z0, x1, z1))
        arena(bp)
        vault(bp)
        vault_passage(bp)
        tower(bp)
        nave_interior(bp)
        bell_tower(bp)
        encrust(bp, variant)
        # restore the tunnels' glass between the walls, then open every doorway
        for p0, p1, axis in TUNNELS:
            glass_tunnel(bp, *_inner(p0, p1, axis), axis)
            carve_tunnel(bp, p0, p1, axis)
        # nave <-> arena portal through the drum
        for z in range(4, 9):
            for x in range(-3, 4):
                h = 6 + (pointed(x, 3.5) or 0)
                for y in range(1, 10):
                    if y <= h:
                        bp.set(x, y, z, "air")
                bp.set(x, 0, z, TRIM)
        arena_mist(bp)
        # the drowned halls: crates and barnacled pots in the corners, a few webs of kelp-dust (hall floors only:
        # the tops of the prison cells, tanks and shelves are not rooms, a crate there is a ladder to nowhere)
        I.decorate(bp, dict(I.THEMES["storage"], ceiling=None, density=0.25,
                            floor={"crates": 2, "barrel": 2, "pot": 3, "sea_pickle": 2, "coral": 1}),
                   seed=1, rugs=False, centre=False, rooms=_hall_floors(bp, bare))
    return build


def _hall_floors(bp, bare):
    """Floor-level rooms for the clutter, minus the halls in ``bare`` (prison cells and fish tanks: a crate stacked
    against them is a step up onto their roofs) and the 1-wide strips (a crate there blocks the strip)."""
    # found one half at a time: the whole floor is one connected room centred near the arena, and find_rooms
    # skips a room centred inside the boss seal's reach (the halves still drop the arena itself)
    rooms = [r for region in (((-200, 1, -200), (-1, 1, 200)), ((0, 1, -200), (200, 1, 200)))
             for r in I.find_rooms(bp, region=region) if r.y == 1]
    for r in rooms:
        cells = set(r.cells)
        r.free = {(x, z) for x, z in r.free
                  if not ((x - 1, z) not in cells and (x + 1, z) not in cells)
                  and not ((x, z - 1) not in cells and (x, z + 1) not in cells)
                  and not any(x0 <= x <= x1 and z0 <= z <= z1 for x0, z0, x1, z1 in bare)}
    return rooms


def arena_mist(bp):
    """Boss mist across the three ways into the arena: the nave portal and the two side tunnels."""
    ax, az = ARENA
    bp.mist(-3, 1, az + AR + 1, 3, 10, az + AR + 1)          # nave portal, just outside the drum
    for side in (-1, 1):
        x = ax + side * (AR + 2)
        bp.mist(x, 1, -13, x, 8, -7)                          # W2 / E2 tunnels


def nave_interior(bp):
    """The nave: a processional way of sea lanterns between two colonnades, banners and a
    lithite portal framing the way into the arena."""
    for z in range(8, 27):
        bp.set(0, 0, z, SEA if z % 3 == 0 else LB)
        for x in (-1, 1):
            bp.set(x, 0, z, TRIM)
    for z in (10, 14, 20, 24):
        for x in (-4, 4):
            for y in range(1, 16):
                bp.set(x, y, z, LB if y in (1, 8, 15) else TRIM)
            bp.set(x, 16, z, SEA)
    for z in (11, 15, 19, 23):
        for x, f in ((-6, "east"), (6, "west")):
            bp.set(x, 9, z, f"cyan_wall_banner[facing={f}]")
    for x in range(-5, 6):
        for y in range(1, 15):
            if abs(x) >= 4 or y >= 12:
                if bp.get(x, y, 8) == AIR:
                    bp.set(x, y, 8, LB if (x + y) % 2 else TRIM)
    for x in (-4, 4):
        bp.set(x, 12, 8, LC)


def encrust(bp, seed):
    """Coral and sea life growing on the lower outer walls."""
    rng = random.Random(seed)
    corals = ("brain", "tube", "bubble", "fire", "horn")
    faces = (("north", 0, -1), ("south", 0, 1), ("east", 1, 0), ("west", -1, 0))
    for (x, y, z), (name, props, data) in list(bp.blocks.items()):
        if y > 6 or y < 0 or name not in ("minecraft:prismarine_bricks", "minecraft:prismarine"):
            continue
        open_faces = [(f, dx, dz) for f, dx, dz in faces if (x + dx, y, z + dz) not in bp.blocks]
        if not open_faces:
            continue
        r = rng.random()
        if r < 0.05 * (1 - y / 8):
            bp.set(x, y, z, f"{rng.choice(corals)}_coral_block")
        elif r < 0.09:
            f, dx, dz = rng.choice(open_faces)
            bp.set(x + dx, y, z + dz, f"{rng.choice(corals)}_coral_wall_fan[facing={f},waterlogged=true]")
        elif r < 0.10 and (x, y + 1, z) not in bp.blocks:
            bp.set(x, y + 1, z, f"sea_pickle[pickles={rng.randint(1, 4)},waterlogged=true]")


def bell_tower(bp):
    """A slender solid watch-turret on the north-east corner: breaks the symmetry."""
    cx, cz, r = 40, -21, 3
    for y in range(-4, 44):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.4:
                    edge = d > r - 0.6
                    b = HULL.pick(x, y, z) if not edge else (TRIM if (x + z) % 3 == 0 else HULL.pick(x, y, z))
                    if y % 9 == 0:
                        b = LB
                    if edge and y % 9 in (4, 5, 6) and (x == cx or z == cz):
                        b = GLASS if y < 40 else SEA
                    bp.set(x, y, z, b)
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            if r + 0.4 < math.hypot(x - cx, z - cz) <= r + 1.4:
                bp.set(x, 43, z, TRIM)
                bp.set(x, 42, z, stair(TRIM_S, _toward(x, z, cx, cz), "top"))
    for y in range(40, 43):
        for x, z in ((cx, cz - r), (cx, cz + r), (cx - r, cz), (cx + r, cz)):
            bp.set(x, y, z, SEA)
    spire(bp, cx, cz, 44, r + 1)


register(StructureDef(
    "sunken_citadel", "overworld", ["deep_ocean", "deep_cold_ocean", "deep_lukewarm_ocean",
                                     "deep_frozen_ocean", "ocean", "cold_ocean"],
    [Piece(f"citadel_{v}", citadel(v)) for v in range(3)],
    spacing=48, separation=16, heightmap="OCEAN_FLOOR_WG", adaptation="beard_box", processors="none",
    exclusion=("minecraft:ocean_monuments", 6), max_distance=100,
    spawns=[("brasshaven:barnacle_crab", 8, 1, 2), ("minecraft:drowned", 10, 1, 2)], creatures=[("barnacle_crab", 4)],
    title_fr="Citadelle engloutie", title_en="Sunken Citadel"))

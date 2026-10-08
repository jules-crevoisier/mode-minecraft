"""Lair of the Soul Reaper (La Faucheuse des âmes), the summit of the Soul Tower.

The soul tower ascends instead of descending. Its old roof is replaced by a round arena platform
(radius 13, cantilevered six blocks beyond the tower on corbels and bone struts) with a low parapet,
soul-lantern posts, a crown of outward-leaning spikes and a cage of four bone ribs that meet above the
centre under the bone needle, a soul chandelier hanging from their apex. The seal lies flush in the floor.

The way up (the wake zone of the seal is a 9.6-block square, 10 blocks deep, so the approach stays out
of it until the mist is crossed):
  * floor 40 becomes the chapel of grace (waystone, bench, candles); the central spiral stops there,
  * a south door leads onto a covered bridge under the arena's overhang, into a hanging stair turret
    clinging to the tower, whose helical stair climbs 16 blocks to a door in the parapet: the mist,
  * the reliquary (floor 48) is sealed off from below; once the reaper falls the sealed bars of a hatch in
    the arena floor crumble and a ladder leads down to its reward chests.
The blaze spawner of floor 40 moves down to the alchemy floor (32).
"""
import math

from ..arch import stair, slab
from ..parts import LOOT, MOD

F = 55            # arena floor level (blocks walked on are at y = F, players stand at F + 1)
R = 13            # platform radius
SEAL_R = 12       # seal radius: wake square of 9.6 blocks
TZ = 16           # stair turret centre (x = 0, z = TZ), on the south side
GRACE = 40        # floor of the chapel of grace
RELIQ = 48        # reliquary floor


def _n():
    from . import nether
    return nether


def _ang(x, z):
    """Compass angle of (x, z) around the turret axis: 0 = north (-z), clockwise (east = 90)."""
    return math.degrees(math.atan2(x, -z)) % 360


def build(bp, cx=0, cz=0):
    n = _n()
    _strip_old_summit(bp, cx, cz)
    _seal_upper_floors(bp, n, cx, cz)
    _grace_chapel(bp, n, cx, cz)
    _platform(bp, n, cx, cz)
    _crown(bp, n, cx, cz)
    _bone_cage(bp, n, cx, cz)
    _bridge(bp, n, cx, cz)
    _turret(bp, n, cx, cz + TZ)
    _reliquary(bp, n, cx, cz)
    # the seal, flush in the floor at the centre, and the mist across the stair arrival
    bp.boss_seal(cx, F, cz, "brasshaven:soul_reaper", SEAL_R)
    bp.mist(cx, F + 2, cz + R, cx, F + 3, cz + R)


# ---------------------------------------------------------------- the old roof, the old stair
def _strip_old_summit(bp, cx, cz):
    """Remove the old roof, spike crown and needle (everything above the tower's corbel course)."""
    for (x, y, z) in list(bp.blocks):
        if y > 52 and abs(x - cx) <= 24 and abs(z - cz) <= 24:
            bp.remove(x, y, z)


def _seal_upper_floors(bp, n, cx, cz):
    """The central spiral now ends at the grace floor: no steps above it, the well closed at the reliquary."""
    for y in range(GRACE + 1, 53):
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if (x, z) != (cx, cz):
                    bp.set(x, y, z, "air")
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if (x, z) != (cx, cz):
                bp.set(x, RELIQ, z, n.CHIS if max(abs(x - cx), abs(z - cz)) == 2 else n.PBB)
    # a chandelier of chains and soul lanterns now hangs in the closed well over the grace floor
    for dx, dz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.chain(cx + dx, RELIQ - 3, cz + dz, RELIQ - 1)
        bp.lantern(cx + dx, RELIQ - 4, cz + dz, hanging=True, soul=True)
    # the blaze spawner moves down to the alchemy floor
    bp.set(cx - 3, GRACE + 1, cz + 3, "air")
    bp.set(cx + 3, GRACE + 1, cz - 3, "air")
    bp.spawner(cx - 3, 33, cz - 3, "minecraft:blaze")


# ---------------------------------------------------------------- floor 40: the chapel of grace
def _grace_chapel(bp, n, cx, cz):
    y = GRACE + 1
    bp.set(cx, y, cz - 4, MOD["waystone"])
    for dx in (-1, 1):
        bp.set(cx + dx, y, cz - 4, "candle[candles=4,lit=true,waterlogged=false]")
    bp.set(cx - 2, y, cz - 4, "soul_lantern[hanging=false,waterlogged=false]")
    bp.set(cx + 2, y, cz - 4, "soul_lantern[hanging=false,waterlogged=false]")
    # a bench facing the waystone, a kneeling cushion, a skull and candles on a shelf
    bp.set(cx - 4, y, cz - 1, stair(n.PBBS, "east"))
    bp.set(cx - 4, y, cz, stair(n.PBBS, "east"))
    bp.set(cx + 4, y, cz - 1, stair(n.PBBS, "west"))
    bp.set(cx + 4, y, cz, stair(n.PBBS, "west"))
    bp.set(cx - 3, y, cz - 3, "cyan_carpet")
    bp.set(cx + 3, y, cz - 3, "cyan_carpet")
    bp.set(cx - 4, y, cz + 2, n.CHIS)
    bp.set(cx - 4, y + 1, cz + 2, "skeleton_skull[rotation=4]")
    bp.set(cx + 4, y, cz + 2, n.CHIS)
    bp.set(cx + 4, y + 1, cz + 2, "candle[candles=2,lit=true,waterlogged=false]")


# ---------------------------------------------------------------- the arena platform
def _floor_block(n, x, z, d):
    a = math.degrees(math.atan2(z, x)) % 360
    if d <= 1.6:
        return n.CHIS
    if d <= 2.6:
        return n.GBS if round(a / 45) % 2 == 0 else n.CHIS
    if 3.6 < d <= 4.4 or 9.6 < d <= 10.4:
        return n.PBAS
    if 12.4 < d:
        return n.CHIS
    spoke = abs(((a + 22.5) % 45) - 22.5)          # angular distance to the nearest of 8 spokes
    if 4.4 < d <= 9.6 and spoke * math.pi / 180 * d <= 0.55:
        return "bone_block[axis=x]" if (round(a / 45) % 4) in (0, 2) else "bone_block[axis=z]"
    if 6.6 < d <= 7.4:
        return "polished_deepslate"
    return None


def _platform(bp, n, cx, cz):
    """Three-thick disk of radius 13 over the tower, corbelled underside, struts, patterned floor."""
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            d = math.hypot(x - cx, z - cz)
            if d > R + 0.4:
                continue
            bp.set(x, F - 2, z, n.SOUL.pick(x, F - 2, z))
            bp.set(x, F - 1, z, n.SOUL.pick(x, F - 1, z))
            bp.set(x, F, z, _floor_block(n, x - cx, z - cz, d) or n.FLOOR.pick(x, F, z))
            if d > R - 0.6:   # outer face of the rim: a chiselled band with dark teeth
                bp.set(x, F - 1, z, n.CHIS if (x + z) % 2 == 0 else n.PBB)
            # corbelled underside stepping in toward the tower
            if d > R - 0.6:
                bp.set(x, F - 3, z, stair(n.PBBS, n.toward(cx, cz, x, z), "top"))
            elif d <= R - 0.6:
                bp.set(x, F - 3, z, n.SOUL.pick(x, F - 3, z), keep=True)
    balcony = (310, 50)   # keep the underside clear above the old ghost balcony
    for (x, z) in n.ring_cells(cx, cz, R - 2):
        a = math.degrees(math.atan2(z - cz, x - cx)) % 360
        if abs((a - balcony[0] + 180) % 360 - 180) < balcony[1]:
            continue
        bp.set(x, F - 4, z, stair(n.PBBS, n.toward(cx, cz, x, z), "top"), keep=True)
    # light points: sea-pale lamps at the outer end of every spoke
    for k in range(8):
        a = math.radians(45 * k)
        bp.set(cx + round(math.cos(a) * 10), F, cz + round(math.sin(a) * 10), "sea_lantern")
    # soul lanterns hanging under the overhang
    for i, (x, z) in enumerate(sorted(n.ring_cells(cx, cz, R - 1), key=lambda p: math.atan2(p[1] - cz, p[0] - cx))):
        a = math.degrees(math.atan2(z - cz, x - cx)) % 360
        if i % 5 == 0 and abs((a - balcony[0] + 180) % 360 - 180) >= balcony[1] and not (60 < a < 120):
            bp.chain(x, F - 5, z, F - 4)
            bp.lantern(x, F - 6, z, hanging=True, soul=True)
    # bone struts from the tower flank out to the rim: the platform held up like a cupped hand of bone
    for ang in (25, 150, 210, 260, 350):
        if abs((ang - balcony[0] + 180) % 360 - 180) < balcony[1] + 5:
            continue
        a = math.radians(ang)
        pts = [(6.6, 36), (8.6, 44), (10.6, 49), (12.2, F - 3)]
        for (r0, y0), (r1, y1) in zip(pts, pts[1:]):
            for w in (0, 1):
                p0 = (cx + round(math.cos(a) * r0), y0 + w, cz + round(math.sin(a) * r0))
                p1 = (cx + round(math.cos(a) * r1), y1 + w, cz + round(math.sin(a) * r1))
                bp.line(p0, p1, n.BONE)


# ---------------------------------------------------------------- parapet, posts, crown of spikes
def _crown(bp, n, cx, cz):
    cells = sorted(n.ring_cells(cx, cz, R), key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
    for i, (x, z) in enumerate(cells):
        if z - cz > 10 and abs(x - cx) <= 3:
            continue   # the stair turret
        if i % 6 == 0:
            bp.set(x, F + 1, z, n.CHIS)
            bp.set(x, F + 2, z, n.PBBW)
            bp.set(x, F + 3, z, "soul_lantern[hanging=false,waterlogged=false]")
        else:
            bp.set(x, F + 1, z, n.PBBW)
    # sixteen spikes rising from under the rim and leaning out, tall and short in turn
    for k in range(16):
        ang = 11.25 + 22.5 * k
        if 70 < ang < 110:
            continue
        a = math.radians(ang)
        h = 14 if k % 2 == 0 else 9
        r0, r1 = R - 0.4, R + 4.0
        top = None
        for j in range(h + 1):
            t = j / h
            r = r0 + (r1 - r0) * t * t
            p = (cx + round(math.cos(a) * r), F - 3 + j, cz + round(math.sin(a) * r))
            bp.set(*p, "blackstone" if t < 0.45 else n.PBW)
            top = p
        bp.set(top[0], top[1] + 1, top[2], "end_rod[facing=up]")


# ---------------------------------------------------------------- the bone cage and the needle
def _bone_cage(bp, n, cx, cz):
    apex = F + 15
    for ang in (30, 150, 270):
        a = math.radians(ang)
        prev = None
        steps = 80
        for i in range(steps + 1):
            r = R * (1 - i / steps)
            y = F + 1 + (apex - F - 1) * math.sqrt(max(0.0, 1 - (r / R) ** 2))
            p = (cx + round(math.cos(a) * r), round(y), cz + round(math.sin(a) * r))
            if prev and p != prev:
                bp.line(prev, p, n.BONE)
                if r > R * 0.45:   # doubled toward the foot
                    bp.line((prev[0], prev[1] - 1, prev[2]), (p[0], p[1] - 1, p[2]), n.BONE)
            prev = p
        # the foot of each rib is a post with a skull and a soul brazier
        fx, fz = cx + round(math.cos(a) * R), cz + round(math.sin(a) * R)
        bp.set(fx, F + 1, fz, n.CHIS)
        bx, bz = cx + round(math.cos(a) * (R - 1)), cz + round(math.sin(a) * (R - 1))
        bp.set(bx, F + 1, bz, n.PBBW)
        bp.set(bx, F + 2, bz, n.GBS)
        bp.set(bx, F + 3, bz, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the needle above the meeting of the ribs
    for y in range(apex, apex + 4):
        bp.set(cx, y, cz, n.BONE)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, apex + 1, cz + dz, "bone_block[axis=x]" if dx else "bone_block[axis=z]")
        bp.set(cx + 2 * dx, apex + 2, cz + 2 * dz, n.BONE)
    bp.set(cx, apex + 4, cz, n.CHIS)
    bp.set(cx, apex + 5, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # a chandelier of soul lanterns hanging over the seal
    bp.chain(cx, apex - 4, cz, apex - 1)
    c = apex - 5
    bp.set(cx, c, cz, n.CHIS)
    bp.lantern(cx, c - 1, cz, hanging=True, soul=True)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, c, cz + dz, n.PBBW)
        bp.set(cx + 2 * dx, c, cz + 2 * dz, n.PBBW)
        bp.lantern(cx + 2 * dx, c - 1, cz + 2 * dz, hanging=True, soul=True)


# ---------------------------------------------------------------- the covered bridge to the turret
def _bridge(bp, n, cx, cz):
    y = GRACE
    # door out of the grace floor through the south wall
    for z in range(cz + 4, cz + 8):
        for x in (cx - 1, cx, cx + 1):
            for yy in (y + 1, y + 2, y + 3):
                bp.set(x, yy, z, "air")
            bp.set(x, y, z, n.PBB)
    for x in (cx - 1, cx + 1):
        bp.set(x, y + 3, cz + 6, stair(n.PBBS, "east" if x < cx else "west", "top"))
    bp.set(cx, y + 4, cz + 6, n.CHIS)
    # the bridge deck, railing and the arch under it
    for z in range(cz + 7, cz + TZ - 2):
        for x in range(cx - 2, cx + 3):
            bp.set(x, y, z, n.CHIS if abs(x - cx) == 2 else n.PBB)
            for yy in range(y + 1, y + 4):
                if abs(x - cx) <= 1:
                    bp.set(x, yy, z, "air")
        for x in (cx - 2, cx + 2):
            bp.set(x, y + 1, z, n.PBBW)         # a two-course balustrade: nobody climbs onto it and drops
            bp.set(x, y + 2, z, n.PBBW)         # to the tower's corbel ledges under the overhang
            if (z - cz) % 3 == 0:
                bp.set(x, y + 3, z, "soul_lantern[hanging=false,waterlogged=false]")
        bp.set(cx - 2, y - 1, z, stair(n.PBBS, "east", "top"))
        bp.set(cx + 2, y - 1, z, stair(n.PBBS, "west", "top"))
        bp.set(cx, y - 1, z, n.PBB if (z - cz) % 2 else stair(n.PBBS, "south", "top"))
    bp.chain(cx, y - 3, cz + 10, y - 2)
    bp.lantern(cx, y - 4, cz + 10, hanging=True, soul=True)


# ---------------------------------------------------------------- the hanging stair turret
def _turret(bp, n, tx, tz):
    y0, y_top = GRACE, F + 8           # floor of the turret, top of its wall (a gate tower over the parapet)
    rr = 3                            # outer wall radius
    # hanging base: an inverted cone of corbels ending in a lantern pendant
    for k, y in enumerate(range(y0 - 1, y0 - 5, -1)):
        r = rr - k
        for x in range(tx - rr - 1, tx + rr + 2):
            for z in range(tz - rr - 1, tz + rr + 2):
                d = math.hypot(x - tx, z - tz)
                if d <= r - 0.6:
                    bp.set(x, y, z, n.SOUL.pick(x, y, z))
                elif d <= r + 0.4:
                    bp.set(x, y, z, stair(n.PBBS, n.toward(tx, tz, x, z), "top"))
    bp.set(tx, y0 - 5, tz, n.CHIS)
    bp.chain(tx, y0 - 7, tz, y0 - 6)
    bp.lantern(tx, y0 - 8, tz, hanging=True, soul=True)
    # bone struts tying the turret back into the tower
    for dx in (-2, 2):
        bp.line((tx + dx, y0 - 9, tz - 8), (tx + dx, y0 - 2, tz - 2), n.BONE)
    # shell, interior and floor
    for y in range(y0, y_top + 1):
        for x in range(tx - rr - 1, tx + rr + 2):
            for z in range(tz - rr - 1, tz + rr + 2):
                d = math.hypot(x - tx, z - tz)
                if d > rr + 0.4:
                    continue
                if d > rr - 0.6 or y == y0:
                    band = (y - y0) % 6 == 0
                    bp.set(x, y, z, n.CHIS if band and y > y0 else n.SOUL.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
    # helical stair: 32 half-steps, a full turn per 4 blocks, entering and leaving on the north side
    for i in range(32):
        sector = (1 + i) % 8
        y = y0 + 1 + i // 2
        kind = "bottom" if i % 2 == 0 else "top"
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                d = math.hypot(x - tx, z - tz)
                if d == 0 or d > rr - 0.6:
                    continue
                if int(((_ang(x - tx, z - tz) + 22.5) % 360) // 45) == sector:
                    bp.set(x, y, z, slab(n.PBBSL, kind))
    for y in range(y0 + 1, y0 + 18):
        bp.set(tx, y, tz, n.BONE)
    # doors: the bridge below, the arena above (one step down onto the arena floor)
    for yy in (y0 + 1, y0 + 2):
        bp.set(tx, yy, tz - rr, "air")
    bp.set(tx, F + 1, tz - rr, n.PBB)
    for yy in (F + 2, F + 3):
        bp.set(tx, yy, tz - rr, "air")
    bp.set(tx - 1, F + 4, tz - rr, stair(n.PBBS, "east", "top"))
    bp.set(tx + 1, F + 4, tz - rr, stair(n.PBBS, "west", "top"))
    bp.set(tx, F + 4, tz - rr, n.CHIS)
    # glowing lancet slits on the three outer faces, staggered with the stair
    for k, (dx, dz) in enumerate(((1, 0), (0, 1), (-1, 0))):
        for base in (y0 + 3 + 2 * k, y0 + 9 + 2 * k):
            for dy in range(3):
                bp.set(tx + dx * rr, base + dy, tz + dz * rr, n.SOULGLASS)
    # machicolated top, a cap and a soul-lit spike roof
    for (x, z) in n.ring_cells(tx, tz, rr + 1):
        bp.set(x, y_top, z, stair(n.PBBS, n.toward(tx, tz, x, z), "top"))
        bp.set(x, y_top + 1, z, n.PBB)
    bp.disk(tx, y_top + 1, tz, rr, n.PB)
    for (x, z) in ((tx + rr + 1, tz), (tx - rr - 1, tz), (tx, tz + rr + 1)):
        bp.chain(x, y_top - 2, z, y_top - 1)
        bp.lantern(x, y_top - 3, z, hanging=True, soul=True)
    for i, (x, z) in enumerate(sorted(n.ring_cells(tx, tz, rr + 1), key=lambda p: math.atan2(p[1] - tz, p[0] - tx))):
        if i % 2 == 0:
            bp.set(x, y_top + 2, z, n.PBBW)
    n.spike(bp, tx, tz, y_top + 2, rr, "blackstone", n.BS, steep=2, band=None, lamps=False,
            lamp="soul_lantern[hanging=false,waterlogged=false]", tip=False)
    bp.lantern(tx, F + 4, tz, hanging=True, soul=True)


# ---------------------------------------------------------------- floor 48: the reliquary (the reward)
def _reliquary(bp, n, cx, cz):
    y = RELIQ + 1
    # hatch: sealed bars in the arena floor, a ladder down the wall into the reliquary
    hx, hz = cx - 5, cz
    for yy in (F - 2, F - 1):
        bp.set(hx, yy, hz, "air")
    bp.ladder(hx, y, hz, F - 1, "east")
    bp.set(hx, F, hz, MOD["vault_bars"])
    # reward: the old chest on its altar plus a second chest across the room, candles and skulls
    bp.set(cx, y, cz + 4, n.CHIS)
    bp.chest(cx, y + 1, cz + 4, "north", LOOT + "soul_tower")
    bp.set(cx - 1, y, cz + 4, "wither_skeleton_skull[rotation=8]")
    bp.set(cx + 1, y, cz + 4, "candle[candles=4,lit=true,waterlogged=false]")
    for (x, z) in ((cx + 3, cz - 3), (cx - 3, cz + 3), (cx + 3, cz + 3), (cx - 3, cz - 3)):
        bp.set(x, y, z, "soul_lantern[hanging=false,waterlogged=false]")
    for (x, z) in ((cx + 2, cz - 4), (cx - 2, cz - 4)):
        bp.set(x, y, z, n.CHIS)
        bp.set(x, y + 1, z, "skeleton_skull[rotation=0]")
    bp.set(cx + 4, y, cz + 1, "cobweb")

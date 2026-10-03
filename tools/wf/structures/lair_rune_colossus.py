"""Lair of the Rune Colossus, deep under the Rune Circle.

From the crypt under the dais (y -11) a doorway in the west wall opens on the rune well: a helical stair
winding 19 blocks down around a glowing rune pillar, its walls carved with runes. At the bottom the
gallery of the sleeping guardians runs north (kneeling stone knights in alcoves, two spawners, a barrel,
a stretch where the vault has collapsed), ending in the antechamber, the site of grace (waystone, benches,
candles). Beyond the mist lies the rune vault: a domed hall (floor radius 18, 20 blocks high) with a henge
of standing stones around the edge and an inlaid circle-rune on the floor, the seal at its heart. A
reliquary past the vault holds the reward.

Called at the end of ``overworld_c.rune_circle`` (the crypt floor is at y = -11).
"""
import math
import random

from .. import arch
from ..arch import Palette, slab, stair
from ..parts import LOOT, MOB, MOD

RUNE = "wayfarers:carved_guild_stone"
LAMP = "wayfarers:rune_lamp"
CRYPT_Y = -11
SX, SZ = -14, 0          # the rune well (spiral stair) centre
FLOOR = -30              # gallery, antechamber and vault floor
AX, AZ, AR = 13, -38, 18  # the vault: centre and floor radius

WALL = Palette({"deepslate_bricks": 5, "cracked_deepslate_bricks": 1, "tuff_bricks": 2, "polished_deepslate": 1},
               seed=91, scale=2.5)
FLOOR_PAL = Palette({"deepslate_tiles": 5, "cracked_deepslate_tiles": 1, "polished_deepslate": 2}, seed=92, scale=2.0)
MENHIR = Palette({"stone": 4, "tuff": 3, "andesite": 2, "mossy_cobblestone": 1}, seed=93, scale=2.2)


def _card(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def build(bp):
    rng = random.Random(61)
    rune_well(bp, rng)
    gallery(bp, rng)
    antechamber(bp)
    vault(bp, rng)
    reliquary(bp)
    # the mist across both doorways of the vault (after carving them)
    bp.mist(AX - AR - 2, FLOOR + 1, AZ - 1, AX - AR - 1, FLOOR + 4, AZ + 1)
    bp.mist(AX + AR + 1, FLOOR + 1, AZ - 1, AX + AR + 2, FLOOR + 3, AZ + 1)
    bp.boss_seal(AX, FLOOR, AZ, "wayfarers:rune_colossus", 16)


# -------------------------------------------------------------------- the rune well (helical stair)
def rune_well(bp, rng):
    top, bottom = CRYPT_Y, FLOOR
    drop = top - bottom                      # 19 blocks
    turns = 1.75                             # ends facing north (angle 270)
    per_turn = drop / turns
    # shell and interior
    for x in range(SX - 7, SX + 8):
        for z in range(SZ - 7, SZ + 8):
            d = math.hypot(x - SX, z - SZ)
            for y in range(bottom - 1, top + 5):
                if d <= 4.5:
                    if y == bottom - 1:
                        bp.set(x, y, z, "polished_deepslate")
                    elif y == bottom:
                        bp.set(x, y, z, "deepslate_tiles" if d > 2.2 else "chiseled_deepslate")
                    elif y == top + 4:
                        bp.set(x, y, z, "deepslate_tiles")
                    else:
                        bp.set(x, y, z, "air")
                elif d <= 6.4:
                    a = math.degrees(math.atan2(z - SZ, x - SX)) % 360
                    band = (y - bottom) % 4 == 0
                    b = "polished_deepslate" if band else WALL.pick(x, y, z)
                    if d <= 5.5 and not band and int(a // 20) % 3 == 0 and (y + int(a // 20)) % 3 == 1:
                        b = RUNE                     # runes carved all the way down
                    bp.set(x, y, z, b)
    # the rune pillar
    for y in range(bottom + 1, top + 4):
        for x in range(SX - 2, SX + 3):
            for z in range(SZ - 2, SZ + 3):
                d = math.hypot(x - SX, z - SZ)
                if d <= 1.6:
                    lamp = d > 0.5 and (y - bottom) % 5 == 2 and (x + z + y) % 2 == 0
                    bp.set(x, y, z, LAMP if lamp else ("chiseled_tuff" if d < 0.5 else "polished_tuff"))
    # the helical ramp: stairs climbing against the descent, 2.0 < r <= 4.5
    for x in range(SX - 5, SX + 6):
        for z in range(SZ - 5, SZ + 6):
            d = math.hypot(x - SX, z - SZ)
            if not 1.6 < d <= 4.5:
                continue
            a = math.degrees(math.atan2(z - SZ, x - SX)) % 360
            for k in range(3):
                t = (a + 360 * k) / 360.0
                if t > turns:
                    continue
                hy = round(top - t * per_turn)
                if hy < bottom:
                    continue
                ascent = _card(math.sin(math.radians(a)), -math.cos(math.radians(a)))
                bp.set(x, hy, z, stair("deepslate_brick_stairs", ascent) if hy > bottom else "deepslate_tiles")
                if hy - 1 > bottom and bp.get(x, hy - 1, z) == "minecraft:air":
                    bp.set(x, hy - 1, z, stair("deepslate_tile_stairs", _opp(ascent), "top"))
    # lamps on the outer wall, every quarter turn
    for k in range(int(turns * 4) + 1):
        a = math.radians(k * 90 + 45)
        y = round(top - (k * 90 + 45) / 360.0 * per_turn) + 2
        x, z = SX + round(math.cos(a) * 5), SZ + round(math.sin(a) * 5)
        if bottom < y < top + 4:
            bp.set(x, y, z, LAMP)
    # doorway from the crypt (west wall) to the top of the ramp
    for x in range(-9, -6):
        for z in range(-1, 2):
            for y in range(CRYPT_Y + 1, CRYPT_Y + 4):
                bp.set(x, y, z, "air")
            bp.set(x, CRYPT_Y, z, "polished_deepslate")
        bp.set(x, CRYPT_Y + 4, 0, RUNE)
        for z in (-2, 2):
            for y in range(CRYPT_Y + 1, CRYPT_Y + 4):
                bp.set(x, y, z, "tuff_bricks")
    for z in (-1, 1):
        bp.set(-7, CRYPT_Y + 3, z, stair("deepslate_brick_stairs", "south" if z < 0 else "north", "top"))
    bp.set(-6, CRYPT_Y + 3, -2, LAMP)
    bp.set(-6, CRYPT_Y + 3, 2, LAMP)
    # exit at the bottom, heading north into the gallery
    for z in range(SZ - 7, SZ - 4):
        for x in range(SX - 1, SX + 2):
            for y in range(bottom + 1, bottom + 4):
                bp.set(x, y, z, "air")
            bp.set(x, bottom, z, "deepslate_tiles")


def _opp(f):
    return {"north": "south", "south": "north", "east": "west", "west": "east"}[f]


# -------------------------------------------------------------------- gallery of the sleeping guardians
GX0, GX1, GZ0, GZ1 = -17, -11, -34, -7   # interior


def statue(bp, x, y, z, facing, rng):
    """A stone knight asleep on one knee, sword planted before it, moss on the shoulders."""
    fx, fz = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}[facing]
    sx, sz = -fz, fx                          # sideways
    bp.set(x, y, z, "polished_tuff")
    bp.set(x - fx, y, z - fz, "polished_tuff")
    bp.set(x, y + 1, z, stair("tuff_brick_stairs", _opp(facing)))                 # the bent knee
    bp.set(x - fx, y + 1, z - fz, "tuff_bricks")
    bp.set(x - fx, y + 2, z - fz, "chiseled_tuff_bricks")                          # torso
    bp.set(x - fx, y + 3, z - fz, "tuff_bricks")
    for s in (-1, 1):
        bp.set(x - fx + s * sx, y + 2, z - fz + s * sz, "tuff_brick_wall")         # arms
        bp.set(x - fx + s * sx, y + 3, z - fz + s * sz,
               stair("tuff_brick_stairs", _card(s * sx, s * sz), "top"))           # pauldrons
    bp.set(x - fx, y + 4, z - fz, "chiseled_tuff")                                 # helmed head
    bp.set(x - fx, y + 5, z - fz, slab("tuff_brick_slab"))
    bp.set(x + fx, y, z + fz, "polished_deepslate_wall")                           # the planted sword
    bp.set(x + fx, y + 1, z + fz, "polished_deepslate_wall")
    bp.set(x + fx, y + 2, z + fz, "polished_deepslate_wall")
    bp.set(x + fx, y + 3, z + fz, slab("polished_deepslate_slab"))
    if rng.random() < 0.6:
        bp.set(x - fx + sx, y + 4, z - fz + sz, "moss_carpet")


def gallery(bp, rng):
    y0, y1 = FLOOR, FLOOR + 8
    # shell and the barrel vault
    for x in range(GX0 - 4, GX1 + 5):
        for z in range(GZ0, GZ1 + 2):
            for y in range(y0 - 1, y1 + 2):
                bp.set(x, y, z, WALL.pick(x, y, z))
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            u = abs(x - (GX0 + GX1) / 2)
            ceil = y1 - (1 if u > 2 else 0) - (1 if u > 3 else 0)
            for y in range(y0 + 1, ceil):
                bp.set(x, y, z, "air")
            bp.set(x, y0, z, "polished_tuff" if u < 1 else FLOOR_PAL.pick(x, y0, z))
            if u == 3:
                bp.set(x, ceil - 1, z, stair("deepslate_tile_stairs", "east" if x < -14 else "west", "top"))
            if u == 0 and (z - GZ0) % 6 == 3:
                bp.set(x, y0, z, LAMP)
    # transverse arches and alcoves with the sleeping guardians
    alcoves = list(range(GZ1 - 3, GZ0 + 2, -5))
    for i, z in enumerate(alcoves):
        for x in range(GX0, GX1 + 1):
            bp.set(x, y1 - 1, z - 2, "polished_deepslate")
        for side, xw in ((-1, GX0 - 1), (1, GX1 + 1)):
            for zz in range(z - 1, z + 2):
                for dx in range(0, 3):
                    for y in range(y0 + 1, y0 + 7):
                        bp.set(xw + side * dx, y, zz, "air")
                    bp.set(xw + side * dx, y0, zz, "polished_tuff")
            for y in range(y0 + 1, y0 + 7):
                bp.set(xw, y, z - 2, "tuff_bricks")
                bp.set(xw, y, z + 2, "tuff_bricks")
            bp.set(xw, y0 + 7, z, RUNE)
            kind = (i * 2 + (0 if side < 0 else 1)) % 7
            sx = xw + side * 1
            if kind == 3:
                bp.spawner(sx, y0 + 1, z, MOB["ruin_walker"])
                bp.set(sx + side, y0 + 1, z, "cobweb")
            elif kind == 5:
                bp.barrel(sx + side, y0 + 1, z, "up", LOOT + "rune_circle")
                bp.set(sx, y0 + 1, z, "candle[candles=3,lit=true,waterlogged=false]")
                bp.set(sx + side, y0 + 1, z - 1, "skeleton_skull[rotation=4]")
            else:
                statue(bp, sx, y0 + 1, z, "east" if side < 0 else "west", rng)
            bp.lantern(xw + side * 2, y0 + 6, z + 1, hanging=True, soul=True)
    # the collapsed stretch: rubble slope, a hole in the vault with hanging roots
    for z in range(-23, -17):
        for x in range(GX0, GX1 + 1):
            h = max(0, 2 - abs(z + 20) // 2 - (1 if x in (GX0 + 3, GX0 + 4) else 0))
            for y in range(y0 + 1, y0 + 1 + h):
                bp.set(x, y, z, rng.choice(["cobbled_deepslate", "gravel", "deepslate_bricks", "tuff"]))
            if abs(z + 20) <= 1 and GX0 + 1 <= x <= GX1 - 1:
                for y in range(y1 - 2, y1 + 2):
                    bp.set(x, y, z, "air")
                if rng.random() < 0.5:
                    bp.set(x, y1 + 1, z, "hanging_roots[waterlogged=false]")
    for _ in range(14):
        x, z = rng.randint(GX0, GX1), rng.randint(GZ0, GZ1)
        if bp.get(x, y0 + 1, z) == "minecraft:air" and x != SX:
            bp.set(x, y0 + 1, z, rng.choice(["cobweb", "moss_carpet", "cobbled_deepslate"]))
    # the way in from the rune well
    for z in range(GZ1, SZ - 3):
        for x in range(SX - 1, SX + 2):
            for y in range(y0 + 1, y0 + 4):
                bp.set(x, y, z, "air")
            bp.set(x, y0, z, "deepslate_tiles")
    # keep the central way clear
    for z in range(GZ0, GZ1 + 1):
        for y in range(y0 + 1, y0 + 4):
            if bp.get(-14, y, z) not in ("minecraft:air",) and not (-23 <= z < -17):
                bp.set(-14, y, z, "air")


# -------------------------------------------------------------------- the antechamber: site of grace
def antechamber(bp):
    x0, x1, z0, z1 = -20, -8, -43, -35
    y0 = FLOOR
    bp.room(x0, y0, z0, x1, y0 + 8, z1, "deepslate_bricks", floor="polished_deepslate", ceiling="deepslate_tiles")
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if (x + z) % 2 == 0:
                bp.set(x, y0, z, "deepslate_tiles")
    for (x, z) in ((x0 + 1, z0 + 1), (x0 + 1, z1 - 1), (x1 - 1, z0 + 1), (x1 - 1, z1 - 1)):
        for y in range(y0 + 1, y0 + 8):
            bp.set(x, y, z, "tuff_bricks" if y % 3 else "chiseled_tuff_bricks")
    # opening from the gallery
    for x in range(-16, -11):
        for y in range(y0 + 1, y0 + 6):
            bp.set(x, y, z1, "air")
            bp.set(x, y, z1 + 1, "air")
    # the waystone on a dais, ringed by candles and benches
    wx, wz = -14, -40
    for x in range(wx - 1, wx + 2):
        for z in range(wz - 1, wz + 2):
            bp.set(x, y0, z, "chiseled_tuff")
    bp.set(wx, y0 + 1, wz, MOD["waystone"])
    for (x, z) in ((wx - 2, wz - 2), (wx + 2, wz - 2), (wx - 2, wz + 2), (wx + 2, wz + 2)):
        bp.set(x, y0 + 1, z, "candle[candles=4,lit=true,waterlogged=false]")
    for x in (wx - 1, wx, wx + 1):
        bp.set(x, y0 + 1, z1 - 1, stair("polished_deepslate_stairs", "north"))
    bp.set(x0 + 1, y0 + 1, wz, stair("polished_deepslate_stairs", "west"))
    bp.set(x0 + 1, y0 + 1, wz + 1, stair("polished_deepslate_stairs", "west"))
    arch.hanging_lantern(bp, wx, y0 + 7, wz, chain=3, soul=False)
    for x in (x0 + 3, x1 - 3):
        bp.set(x, y0 + 4, z0, LAMP)
        bp.set(x, y0 + 4, z1, LAMP)
    bp.set(x0 + 2, y0 + 1, z0 + 2, "decorated_pot[facing=south,waterlogged=false,cracked=false]")
    bp.set(x1 - 2, y0 + 1, z0 + 1, "lectern[facing=north,has_book=false,powered=false]")
    # passage east to the vault, flanked by two menhirs with runes
    for x in range(x1, AX - AR):
        for z in range(AZ - 1, AZ + 2):
            for y in range(y0 + 1, y0 + 5):
                bp.set(x, y, z, "air")
            bp.set(x, y0, z, "polished_tuff" if z == AZ else "deepslate_tiles")
        for z in (AZ - 2, AZ + 2):
            for y in range(y0, y0 + 6):
                bp.set(x, y, z, WALL.pick(x, y, z))
        for y in (y0 + 5, y0 + 6):
            for z in range(AZ - 1, AZ + 2):
                bp.set(x, y, z, "deepslate_bricks")
    for z in (AZ - 2, AZ + 2):
        bp.set(x1 + 2, y0 + 3, z, LAMP)


# -------------------------------------------------------------------- the rune vault (arena)
def vault(bp, rng):
    drum_top = FLOOR + 12
    rise = 10
    R_in, R_out = AR + 0.5, AR + 2.5
    for x in range(AX - AR - 4, AX + AR + 5):
        for z in range(AZ - AR - 4, AZ + AR + 5):
            d = math.hypot(x - AX, z - AZ)
            if d > R_out + 0.5:
                continue
            a = math.degrees(math.atan2(z - AZ, x - AX)) % 360
            for y in (FLOOR - 1, FLOOR - 2):
                bp.set(x, y, z, "deepslate_bricks")
            if d <= R_in:
                # ---- floor: the inlaid circle-rune
                if d < 2.0:
                    b = "chiseled_deepslate"
                elif d < 3.0:
                    b = "chiseled_tuff_bricks"
                elif 7.5 <= d < 8.5:
                    b = (LAMP if int(a) % 45 < 4 else RUNE if int(a // 6) % 2 else "polished_tuff")
                elif 12.0 <= d < 13.0:
                    b = "tuff_bricks"
                elif abs((a + 7.5) % 30 - 7.5) < 1.6 * 10 / max(d, 1) and d < 12:
                    b = "polished_deepslate"
                elif d > 16.5:
                    b = "polished_deepslate"
                else:
                    b = FLOOR_PAL.pick(x, FLOOR, z)
                bp.set(x, FLOOR, z, b)
                # ---- interior air: drum then dome
                h_in = drum_top + rise * math.sqrt(max(0.0, 1 - (d / R_in) ** 2))
                for y in range(FLOOR + 1, int(h_in) + 1):
                    bp.set(x, y, z, "air")
                for y in range(int(h_in) + 1, int(h_in) + 3):
                    rib = int((a + 3) // 30) != int((a - 3) // 30)
                    bp.set(x, y, z, "polished_deepslate" if rib else ("deepslate_tiles" if y == int(h_in) + 1 else
                                                                        "deepslate_bricks"))
            else:
                # ---- the drum wall: plinth, rune band, pilasters
                for y in range(FLOOR, drum_top + 3):
                    if y == FLOOR or y == FLOOR + 1:
                        b = "polished_deepslate"
                    elif y == FLOOR + 6:
                        b = RUNE if int(a // 4) % 2 else "chiseled_tuff_bricks"
                    elif int((a + 2) // 15) != int((a - 2) // 15):
                        b = "tuff_bricks"
                    else:
                        b = WALL.pick(x, y, z)
                    bp.set(x, y, z, b)
    # lamps on the drum (soul lanterns hung from the rune band) and a ring at the foot of the dome
    for k in range(24):
        a = math.radians(k * 15 + 7.5)
        x, z = AX + round(math.cos(a) * (AR - 0.2)), AZ + round(math.sin(a) * (AR - 0.2))
        if bp.get(x, FLOOR + 1, z) == "minecraft:air" and abs(z - AZ) > 2 and k % 2 == 1:
            for y in range(FLOOR + 1, FLOOR + 4):
                bp.set(x, y, z, "polished_deepslate_wall")
            bp.lantern(x, FLOOR + 4, z, soul=True)
        xx, zz = AX + round(math.cos(a) * (AR + 0.6)), AZ + round(math.sin(a) * (AR + 0.6))
        if k % 2 == 0:
            bp.set(xx, drum_top - 1, zz, LAMP)
    # the keystone: a cluster of lithite at the apex, chandeliers of soul lanterns
    apex = drum_top + rise
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(AX + dx, apex + 1, AZ + dz, "wayfarers:lithite_block")
    bp.set(AX, apex, AZ, "wayfarers:lithite_block")
    for (dx, dz) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
        y = int(drum_top + rise * math.sqrt(1 - (7 / (AR + 0.5)) ** 2))
        bp.chain(AX + dx, y - 3, AZ + dz, y)
        bp.lantern(AX + dx, y - 4, AZ + dz, hanging=True, soul=True)
    # the henge: 12 standing stones (gaps at the two doorways), four of them capped by lintels
    stones = []
    for k in range(12):
        a = k * 30 + 15
        if min(abs(a - 180), abs(a - 0), abs(a - 360)) < 16:
            continue
        h = 7 + (k * 5) % 4
        stones.append((a, h))
        _menhir(bp, a, 15.6, 1.2, 0.9, FLOOR + 1, FLOOR + h, rng)
    for (a, h), (b, h2) in ((stones[0], stones[1]), (stones[2], stones[3]), (stones[4], stones[5]), (stones[6], stones[7])):
        top = FLOOR + max(h, h2) + 1
        for t in range(0, 11):
            ang = math.radians(a + (b - a) * t / 10)
            x, z = AX + round(math.cos(ang) * 15.6), AZ + round(math.sin(ang) * 15.6)
            bp.set(x, top, z, "tuff_bricks" if t % 4 else "chiseled_tuff_bricks")
    # rubble and fallen pieces at the edge only (the floor inside radius 13 stays clear)
    for _ in range(30):
        a = rng.random() * math.pi * 2
        r = 14.2 + rng.random() * 3.5
        x, z = AX + round(math.cos(a) * r), AZ + round(math.sin(a) * r)
        if bp.get(x, FLOOR + 1, z) == "minecraft:air" and abs(z - AZ) > 2:
            bp.set(x, FLOOR + 1, z, rng.choice(["cobbled_deepslate", "moss_carpet", "tuff", "glow_lichen[down=true,east=false,"
                                                 "north=false,south=false,up=false,waterlogged=false,west=false]"]))
    # doorways through the drum (west from the antechamber, east to the reliquary)
    for x in list(range(AX - AR - 3, AX - AR + 1)) + list(range(AX + AR, AX + AR + 4)):
        for z in range(AZ - 1, AZ + 2):
            h = 4 if x < AX else 3
            for y in range(FLOOR + 1, FLOOR + 1 + h):
                bp.set(x, y, z, "air")
            bp.set(x, FLOOR, z, "polished_tuff")


def _menhir(bp, ang, r, hu, hv, y0, y1, rng):
    """An upright stone at angle/radius around the vault centre, runes and a lamp on its inner face."""
    a = math.radians(ang)
    cx, cz = AX + math.cos(a) * r, AZ + math.sin(a) * r
    inner = None
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        w = hu - 0.25 * t
        for x in range(math.floor(cx - 3), math.ceil(cx + 4)):
            for z in range(math.floor(cz - 3), math.ceil(cz + 4)):
                u = (x - cx) * -math.sin(a) + (z - cz) * math.cos(a)
                v = (x - cx) * math.cos(a) + (z - cz) * math.sin(a)
                if abs(u) <= w + 0.01 and abs(v) <= hv + 0.01:
                    bp.set(x, y, z, MENHIR.pick(x, y, z))
                    if y == y0 + 2 and (inner is None or v < inner[2]):
                        inner = (x, z, v)
    if inner:
        x, z, _ = inner
        bp.set(x, y0 + 2, z, LAMP)
        bp.set(x, y0 + 3, z, RUNE)
        bp.set(x, y0 + 1, z, RUNE)
    if rng.random() < 0.7:
        bp.set(round(cx), y1 + 1, round(cz), "moss_carpet")


# -------------------------------------------------------------------- the reliquary past the vault
def reliquary(bp):
    x0, x1, z0, z1 = AX + AR + 3, AX + AR + 10, AZ - 4, AZ + 4
    bp.room(x0, FLOOR, z0, x1, FLOOR + 6, z1, "deepslate_bricks", floor="polished_tuff", ceiling="deepslate_tiles")
    for z in range(AZ - 1, AZ + 2):
        for y in range(FLOOR + 1, FLOOR + 4):
            bp.set(x0, y, z, "air")
    bp.set(x1 - 1, FLOOR + 1, AZ, "chiseled_tuff_bricks")
    bp.chest(x1 - 2, FLOOR + 1, AZ, "west", LOOT + "rune_circle")
    bp.barrel(x1 - 1, FLOOR + 1, AZ - 2, "up", LOOT + "rune_circle")
    for z in (z0 + 1, z1 - 1):
        bp.set(x1 - 1, FLOOR + 1, z, "candle[candles=3,lit=true,waterlogged=false]")
        bp.set(x0 + 2, FLOOR + 4, z, LAMP)
    bp.set(x1, FLOOR + 3, AZ, RUNE)
    bp.set(x1 - 1, FLOOR + 2, AZ, "amethyst_cluster[facing=up,waterlogged=false]")

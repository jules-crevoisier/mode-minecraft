"""The Void Warden's arena dressing on the Void Nest (called from end.void_nest).

The nest's open arena on the floating rock stays as it is (radius 17, ringed by colossal claws); this adds
what makes it a boss arena:
  * the boss seal on the central dais, in place of the old summoning altar,
  * the Fang Gate: two obsidian fangs arching over the causeway where it leaves the rock, with the boss
    mist across it (the causeway is the only way onto the nest),
  * a site of grace on the approach islet: a waystone between starlight lamps, benches and candles,
  * the reliquary: the hoard behind the arena is caged in sealed bars that fall with the boss.
"""
import math

from ..arch import stair
from ..parts import MOD

GATE_Z = 27          # where the causeway leaves the rock


def seal(bp, ar):
    bp.set(0, 2, 0, "air")
    bp.boss_seal(0, 1, 0, "brasshaven:void_warden", ar)


def fang_gate(bp):
    """Two curved fangs of obsidian, veined with crying obsidian, meeting in a starlight keystone."""
    from .end import STAR, VB, VB_ST, ROD_DOWN
    for sx in (-1, 1):
        for z in (GATE_Z, GATE_Z + 1):
            bp.set(3 * sx, 0, z, VB)
            for y in range(1, 10):
                vein = (y + z) % 3 == 0 or (z == GATE_Z and y in (4, 8))
                bp.set(3 * sx, y, z, "crying_obsidian" if vein else "obsidian")
            # the fang curls inward over the deck and meets its twin
            for (x, y) in ((3, 10), (2, 10), (2, 11), (1, 11), (1, 12)):
                bp.set(x * sx, y, z, "crying_obsidian" if (x, y) == (1, 11) else "obsidian")
            bp.set(2 * sx, 9, z, stair(VB_ST, "east" if sx > 0 else "west", "top"))
        # outer tooth spurs, the base collar in purpur
        for (x, y) in ((4, 7), (4, 8), (5, 9), (5, 10), (6, 11)):
            bp.set(x * sx, y, GATE_Z, "obsidian")
        bp.set(4 * sx, 1, GATE_Z, stair("purpur_stairs", "west" if sx > 0 else "east"))
        bp.set(4 * sx, 1, GATE_Z + 1, stair("purpur_stairs", "west" if sx > 0 else "east"))
    for z in (GATE_Z, GATE_Z + 1):
        bp.set(0, 12, z, STAR)
        bp.set(0, 13, z, "obsidian")
        bp.set(0, 11, z, ROD_DOWN)
    # carve and mist the passage (deck y=0, open y=1..6 between the fangs)
    for x in range(-2, 3):
        for y in range(1, 11):
            if bp.get(x, y, GATE_Z) in (None, "minecraft:air"):
                bp.set(x, y, GATE_Z, "air")
    bp.mist(-2, 1, GATE_Z, 2, 10, GATE_Z)


def grace(bp):
    """Site of grace on the approach islet (top surface y=-2)."""
    from .end import PUR_ST, STAR, star_lamp
    bp.set(0, -2, 42, "crying_obsidian")
    bp.set(0, -1, 42, MOD["waystone"])
    for (x, z) in ((-1, 41), (1, 41), (-1, 43), (1, 43)):
        bp.set(x, -1, z, f"purple_candle[candles={1 + (x + z) % 3},lit=true,waterlogged=false]")
    for x, f in ((-3, "west"), (3, "east")):
        bp.set(x, -1, 42, stair(PUR_ST, f))
        bp.set(x, -1, 43, stair(PUR_ST, f))
    star_lamp(bp, -2, -1, 44, h=2)
    star_lamp(bp, 2, -1, 44, h=2)
    bp.set(0, -2, 38, STAR)


def reliquary(bp, ar):
    """Cage the hoard dais behind the arena in sealed bars (they fall when the Warden dies)."""
    from .end import VB, ring_pts
    cz = -(ar + 4)
    for (x, z) in ring_pts(0, cz, 4.0):
        if bp.get(x, 1, z) in (None, "minecraft:air"):
            continue                   # off the rock
        if bp.get(x, 2, z) in (None, "minecraft:air"):
            bp.set(x, 2, z, VB)
        for y in (3, 4):
            if bp.get(x, y, z) in (None, "minecraft:air"):
                bp.set(x, y, z, MOD["vault_bars"])
        if (x + z) % 4 == 0 and bp.get(x, 4, z) == MOD["vault_bars"]:
            bp.set(x, 5, z, "end_rod[facing=up]")


def build(bp, ar):
    seal(bp, ar)
    fang_gate(bp)
    grace(bp)
    reliquary(bp, ar)

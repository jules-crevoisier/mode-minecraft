"""Painted shapes, part 2: polearms, fists, orbs, hearts, rings, packs, cloth, gears and books (see itemart.py)."""
import math

from .itemart import diag, painted
from .itemart_shapes import L, collar, shaft


# ------------------------------------------------------------------ polearms


@painted("spear")
def spear(a):
    """Spear: long haft, a leaf blade with a bright ridge, an accent collar and a short pennon."""
    shaft(a, 9, grip=(1, 4))
    collar(a, 8, key="A")
    a.stamp([
        "....ls",
        "...lsd",
        "..lsdd",
        ".lsde.",
        ".sde..",
        "..e...",
    ], L("M", None), 10, 0)
    a.px(8, 8, "A", "light")
    a.px(7, 8, "A", "mid")
    a.px(7, 9, "A", "dark")


@painted("crystal_spear")
def crystal_spear(a):
    """Crystal Fang: a bone haft driven into a cluster of jagged crystals, shards splitting off it."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7, key="I")
    a.stamp([
        ".....ls",
        "....lsd",
        "...lsde",
        "..lsde.",
        "lslde..",
        "lldd...",
        ".de....",
    ], L("M", None), 9, 0)
    a.stamp(["ls", "de"], L("M", None), 8, 1)
    a.stamp(["sl", "dd"], L("M", None), 13, 5)
    a.px(7, 3, "a", "shine")
    a.px(15, 8, "a", "shine")


@painted("lance")
def lance(a):
    """Gryphon Lance: a long tapering steel cone, a round vamplate guarding the grip, a gold pommel."""
    bx, by, tx, ty = 4.5, 11.5, 15.7, 0.3
    ax, ay = tx - bx, ty - by
    ll = math.hypot(ax, ay)

    def uv(x, y):
        return ((x - bx) * ax + (y - by) * ay) / (ll * ll), ((x - bx) * ay - (y - by) * ax) / ll

    def cone(x, y):
        t, d = uv(x, y)
        return 0 <= t <= 1 and abs(d) <= 2.7 * (1 - t) + 0.3
    a.paint("M", cone)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.35, 0.2, 0.7))
    # vamplate: a round guard seen three-quarter (an ellipse across the lance)
    a.paint("A", lambda x, y: (uv(x, y)[0] * ll / 1.3) ** 2 + (uv(x, y)[1] / 4.2) ** 2 <= 1.0)
    a.shade_dir("A", 1.0, 1.0)
    a.tone(2, 8, "shine")
    diag(a, "H", 1, 14, 2)
    a.px(0, 15, "B")
    a.px(1, 15, "B", "dark")
    a.px(0, 14, "B", "light")


@painted("trident")
def trident(a):
    """King's Trident: three barbed tines on a crossbar, a bone haft bound in sapphire."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7, key="A")
    a.stamp([
        "....l..l...",
        "...ls.ls..l",
        "..ls.ls..ls",
        ".lsdlsd.lsd",
        ".sdlsd.lsd.",
        "..lsdllsd..",
        "...dlsdd...",
        "....dd.....",
    ], L("M", None), 5, 0)


@painted("horn")
def horn(a):
    """Sculk Horn: a curling bone horn ringed with warden-steel bands, its wide bell glowing with sculk."""
    def bez(t):
        p0, p1, p2 = (2.0, 13.5), (2.5, 5.0), (10.5, 5.0)
        u = 1 - t
        return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])

    def rad(t):
        return 0.7 + 3.2 * t ** 2.6
    n = 48
    for k in range(n + 1):
        x, y = bez(k / n)
        a.disc("H", x, y, rad(k / n))
    for t in (0.35, 0.62):
        for k in range(4):
            x, y = bez(t + k * 0.01)
            a.disc("M", x, y, rad(t + k * 0.01) + 0.15)
    # bell mouth: dark rim, glowing throat
    a.ellipse("K", 12.6, 5.0, 1.6, 3.6)
    a.ellipse("S", 12.9, 5.0, 0.9, 2.6)
    a.px(12, 3, "S", "shine")
    a.px(13, 4, "S", "light")
    a.px(13, 6, "S", "dark")
    a.px(2, 14, "B")
    a.px(1, 14, "B", "dark")


@painted("gauntlet")
def gauntlet(a):
    """Rune Fist: a plated war gauntlet clenched, knuckle studs, a brass cuff with a glowing rune."""
    a.stamp([
        "...MM.MM.MM.....",
        "..MMMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..BBBBBMMMMMMM..",
        "...BBBBBMMMMM...",
        "....MMMMMMMM....",
        "...XXXXXXXXXX...",
        "...XXXXXXXXXX...",
        "...XXXXXXXXXX...",
        "...XXXXXXXXXX...",
        "....XXXXXXXX....",
    ], {"M": "M", "B": "B", "X": "X"}, 0, 1)
    for x in (5, 8, 11):
        for y in (3, 4, 5):
            a.px(x, y, "M", "deep")
    for x in (3, 6, 9, 12):
        a.px(x, 2, "M", "shine")
    a.px(4, 1, "M", "shine")
    for x in range(3, 13):
        a.px(x, 10, "B", "light")
    a.stamp(["..s..", ".sml.", "..m..", ".m.m."], {"s": ("A", "shine"), "m": ("A", "light"), "l": ("A", "mid")},
            6, 11)


@painted("orb_caged")
def orb_caged(a):
    """Ward Orb: a glowing orb held in a brass cage on a claw stand."""
    a.sphere("M", 8.0, 7.5, 4.6)
    a.ring("B", 8.0, 7.5, 4.6, 5.6)
    for y in range(3, 13):
        a.px(8, y, "B", "light" if y < 7 else "dark")
    for x in range(3, 13):
        a.px(x, 7, "B", "light" if x < 8 else "dark")
    a.px(6, 5, "M", "shine")
    a.px(5, 5, "M", "light")
    a.box("B", 7, 0, 8, 1)
    a.stamp([".BBBBB.", "BB...BB"], {"B": "B"}, 4, 13)
    a.px(3, 3, "a", "shine")
    a.px(13, 12, "a", "shine")


@painted("heart")
def heart(a):
    """Void heart: a dark crystal heart, a vein of light cracking through it."""
    a.disc("M", 5.3, 5.8, 3.4)
    a.disc("M", 10.7, 5.8, 3.4)
    a.poly("M", [(1.9, 6.6), (14.1, 6.6), (8.0, 14.4)])
    a.shade_dir("M", 0.8, 1.0, cuts=(-0.55, 0.1, 0.6))
    a.px(4, 4, "M", "shine")
    a.px(3, 5, "M", "shine")
    a.px(4, 3, "M", "light")
    for x, y, t in ((8, 5, "shine"), (8, 6, "shine"), (7, 7, "light"), (7, 8, "shine"), (8, 9, "light"),
                    (9, 10, "shine"), (8, 11, "light"), (6, 9, "mid"), (10, 8, "mid")):
        a.px(x, y, "A", t)


@painted("ring_magnet")
def ring_magnet(a):
    """Magnet ring: a steel band crowned with a red horseshoe magnet, a spark between its poles."""
    a.ring("M", 8.0, 10.5, 2.6, 4.2)
    a.stamp([
        "II...II",
        "II...II",
        "ZZ...ZZ",
        "ZZZ.ZZZ",
        ".ZZZZZ.",
        "..BBB..",
    ], {"I": "I", "Z": "Z", "B": "B"}, 5, 0)
    a.px(8, 1, "Y", "light")
    a.px(8, 2, "Y", "mid")


# ------------------------------------------------------------------ packs, cloth, gears, books


@painted("backpack")
def backpack(a):
    """Travel backpack: leather body, oxblood flap with a buckle, a bedroll strapped on top, front pocket."""
    a.stamp([
        "................",
        "...QQQQQQQQQQ...",
        "..QQQQQQQQQQQQ..",
        "...QQQQQQQQQQ...",
        "...MMMMMMMMMM...",
        "..MLLLLLLLLLLM..",
        "..MLLLLLLLLLLM..",
        "..MLLLLLLLLLLM..",
        "..MMMMMMMMMMMMM.",
        "..MMMMMMMMMMMMM.",
        "..MMNNNNNNNMMMM.",
        "..MMNNNNNNNMMMM.",
        "..MMNNNNNNNMMMM.",
        "..MMMMMMMMMMMMM.",
        "...MMMMMMMMMMM..",
    ], {"Q": "Q", "M": "M", "L": "L", "N": "N"})
    for y in (1, 2, 3):
        a.px(5, y, "X", "mid")
        a.px(10, y, "X", "mid")
    for x in range(3, 13):
        a.px(x, 7, "L", "deep")
    a.stamp(["AA", "Aa"], {"A": ("A", "light"), "a": ("A", "dark")}, 7, 7)
    a.px(8, 9, "A", "dark")
    a.px(3, 3, "Q", "light")
    a.px(12, 3, "Q", "dark")


@painted("backpack_explorer")
def backpack_explorer(a):
    """Explorer's backpack: a bigger pack on a brass frame, a map roll on top and a lantern hung at its side."""
    a.stamp([
        "....CCCCCCCC....",
        "...CQQQQQQQQC...",
        "...CQQQQQQQQC...",
        "..BMMMMMMMMMMB..",
        "..BLLLLLLLLLLB..",
        "..BLLLLLLLLLLB..",
        "..BLLLLLLLLLLB..",
        "..BMMMMMMMMMMB..",
        "..BMMMMMMMMMMB..",
        "..BMMNNNNNNMMB..",
        "..BMMNNNNNNMMB..",
        "..BMMNNNNNNMMB..",
        "..BMMMMMMMMMMB..",
        "..BBBBBBBBBBBB..",
    ], {"Q": "Q", "M": "M", "L": "L", "N": "N", "B": "B", "C": "C"}, 0, 1)
    for x in range(3, 13):
        a.px(x, 7, "L", "deep")
    a.stamp(["AA", "AA"], {"A": "A"}, 7, 7)
    a.px(7, 7, "A", "shine")
    # lantern hanging on the right side
    a.stamp([".X.", "XRX", "RRR", "XRX", ".X."], {"X": "X", "R": "R"}, 13, 8)
    a.px(14, 10, "R", "shine")


@painted("cloth")
def cloth(a):
    """Arcane cloth: a folded bolt of fabric, embroidered with gold stars, one corner draping down."""
    a.stamp([
        "................",
        "................",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMM..",
        "..MMMMMMMMMMMMM.",
        "...MMMMMMMMMMMM.",
        "...........MMM..",
        "............MM..",
    ], {"M": "M"})
    for x in range(3, 15):
        a.px(x, 5, "M", "deep")
        a.px(x, 6, "M", "light")
        a.px(x, 8, "M", "deep")
        a.px(x, 9, "M", "light")
    for y in (5, 8):
        a.px(2, y, "M", "dark")
    for x, y in ((5, 3), (10, 4), (7, 7), (12, 7), (4, 10), (9, 10)):
        a.px(x, y, "B", "shine")
    a.px(3, 2, "M", "shine")


@painted("gear")
def gear(a):
    """Brass gear: eight square teeth, a raised rim, four spokes in a recessed web and a bored hub."""
    cx, cy = 7.5, 7.5
    a.disc("M", cx, cy, 5.0)
    for k in range(8):
        ang = k * math.pi / 4 + math.pi / 8
        ux, uy = math.cos(ang), math.sin(ang)
        a.paint("M", lambda x, y, ux=ux, uy=uy: abs((x - cx) * uy - (y - cy) * ux) <= 1.2
                and 0 < (x - cx) * ux + (y - cy) * uy <= 7.0)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.45, 0.2, 0.7))
    # recessed web: dark, with four lit spokes
    web = [(x, y) for y in range(16) for x in range(16) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= 3.3 ** 2]
    for x, y in web:
        a.tone(x, y, "deep")
    for x, y in web:
        if abs(x + 0.5 - cx) < 0.6 or abs(y + 0.5 - cy) < 0.6:
            a.tone(x, y, "mid")
    a.disc("M", cx, cy, 1.6, "light")
    a.tone(6, 6, "shine")
    a.px(7, 7, "X", "dark")
    for x, y in ((4, 3), (3, 4)):
        a.tone(x, y, "shine")


@painted("grimoire")
def grimoire(a):
    """Forbidden Grimoire: an oxblood book bound in an iron chain, iron corners, an eye opening on its cover."""
    a.box("L", 3, 1, 12, 14)
    a.box("X", 2, 1, 3, 14)
    for y in range(2, 14):
        a.px(13, y, "Q", "light" if y < 8 else "mid")
    a.px(13, 1, "L", "dark")
    a.px(13, 14, "L", "dark")
    for x, y in ((4, 2), (11, 2), (4, 13), (11, 13)):
        a.px(x, y, "I", "light")
    a.px(12, 1, "I", "mid")
    a.px(12, 14, "I", "dark")
    a.stamp([
        "..mmmm..",
        ".msKKsm.",
        "msKddKsm",
        ".msKKsm.",
        "..mmmm..",
    ], {"m": ("A", "mid"), "s": ("A", "light"), "K": ("K", "mid"), "d": ("A", "shine")}, 4, 5)
    for k, (x, y) in enumerate(((1, 11), (2, 10), (3, 11), (4, 10), (5, 11), (6, 10), (7, 11), (8, 10), (9, 11),
                                (10, 10), (11, 11), (12, 10), (13, 11), (14, 10))):
        a.px(x, y, "I", "light" if k % 2 else "dark")

"""Painted shapes, part 3: tools, metal forms and armour pieces (see itemart.py). Parametric in M (metal), H (haft)
and A (accent), so the same shapes serve brass, mithril, zinc, orichalcum, aether and the legacy materials."""
import math

from .itemart import diag, painted
from .itemart_shapes import L, collar


def _haft(a, length, x0=1, y0=14):
    diag(a, "H", x0, y0, length)
    a.px(x0, y0, "H", "dark")


# ------------------------------------------------------------------ tools
@painted("pickaxe")
def pickaxe(a):
    """Pickaxe: a heavy arched head with tapering points, a brass socket on the haft."""
    _haft(a, 10)
    cx, cy, r = 1.0, 15.0, 12.6

    def head(x, y):
        dx, dy = x - cx, y - cy
        ang = math.degrees(math.atan2(-dy, dx))      # 90 = straight up, 0 = right
        if not 9 <= ang <= 81:
            return False
        th = 1.0 + 1.9 * math.sin(math.radians((ang - 9) * 180 / 72))
        d = math.hypot(dx, dy)
        return r - th <= d <= r
    a.paint("M", head)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.6, 0.0, 0.55))
    for x, y in ((6, 3), (7, 3), (8, 3), (12, 7), (12, 8)):
        a.tone(x, y, "shine") if a.m[y][x] == "M" else None
    collar(a, 8, key="B")


@painted("axe")
def axe(a):
    """Axe: a bearded blade flaring from a brass socket, a short iron poll behind the haft."""
    _haft(a, 11)
    sx, sy = 10.4, 5.6
    ux, uy = 0.7071, -0.7071       # along the haft (up-right)
    vx, vy = -0.7071, -0.7071      # perpendicular, towards the blade (up-left)

    def blade(x, y):
        u = (x - sx) * ux + (y - sy) * uy
        v = (x - sx) * vx + (y - sy) * vy
        return 0.6 <= v <= 5.4 and -1.1 - 0.95 * (v - 0.6) <= u <= 1.3 + 0.45 * (v - 0.6)

    def poll(x, y):
        u = (x - sx) * ux + (y - sy) * uy
        v = (x - sx) * vx + (y - sy) * vy
        return -2.6 <= v <= -0.6 and abs(u) <= 0.95
    a.paint("M", blade)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.05, 0.6))
    for y in range(16):
        for x in range(16):
            v = (x + 0.5 - sx) * vx + (y + 0.5 - sy) * vy
            if a.m[y][x] == "M" and v > 4.4:
                a.tone(x, y, "shine")
    a.paint("X", poll)
    a.stamp(["BB", "BB"], {"B": "B"}, 9, 5)
    a.px(9, 5, "B", "light")
    a.px(10, 6, "B", "dark")


@painted("shovel")
def shovel(a):
    """Shovel: a spade blade with a raised spine and a rounded point, socketed in dark iron."""
    _haft(a, 9)
    cx, cy = 10.8, 5.2
    ux, uy = 0.7071, -0.7071

    def blade(x, y):
        u = (x - cx) * ux + (y - cy) * uy
        v = (x - cx) * uy * -1 + (y - cy) * ux
        w = 3.0 if u < 1.0 else 3.0 - (u - 1.0) * 0.85
        return -3.0 <= u <= 4.6 and abs(v) <= w
    a.paint("M", blade)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.45, 0.1, 0.6))
    for k in range(4):
        a.tone(9 + k, 5 - k, "shine")
    a.px(7, 8, "X", "light")
    a.px(8, 8, "X", "mid")
    a.px(8, 7, "X", "mid")
    a.px(9, 8, "X", "dark")


@painted("hoe")
def hoe(a):
    """Hoe: a long haft, a flat head bent down into a broad blade, a brass rivet."""
    _haft(a, 11)
    a.stamp([
        "....lllllllll...",
        "...lmmmmmmmmmmd.",
        "...lmdeeeeeeee..",
        "...lmd..........",
        "...lmd..........",
        "....dd..........",
    ], L("M", None), 0, 1)
    a.px(4, 1, "M", "shine")
    a.px(11, 2, "B", "light")
    a.px(12, 3, "B", "dark")


# ------------------------------------------------------------------ metal forms
@painted("nugget")
def nugget(a):
    """Nuggets: a big lump and a small one, round-shaded with a glint."""
    a.sphere("M", 6.5, 7.5, 3.7)
    a.alias("M2", "M")
    a.sphere("M2", 11.8, 11.8, 2.3)
    a.px(11, 11, "M2", "shine")


@painted("ingot")
def ingot(a):
    """Ingot: a trapezoid bar in three-quarter view, a maker's stamp on its face."""
    a.stamp([
        ".....sllllllll..",
        "....lllllllllld.",
        "...llllllllllldd",
        "..mmmmmmmmmmmdd.",
        "..mmmmmmmmmmmd..",
        "..mmmmmmmmmmd...",
        "..eeeeeeeeeee...",
    ], L("M", None), 0, 5)
    for x, y in ((6, 9), (7, 8), (8, 9), (7, 10)):
        a.px(x, y, "M", "dark")
    a.px(3, 8, "M", "light")


# ------------------------------------------------------------------ armour
@painted("helmet")
def helmet(a):
    """Helmet: a riveted dome with an accent crest band, a dark visor slot and cheek guards."""
    a.stamp([
        ".....MMMMMM.....",
        "...MMMMMMMMMM...",
        "..MMMMMMMMMMMM..",
        "..AAAAAAAAAAAA..",
        "..MMMKKKKKKMMM..",
        "..MMM......MMM..",
        "..MMM......MMM..",
        "...MM......MM...",
    ], {"M": "M", "A": "A", "K": "X"}, 0, 3)
    a.shade_dir("M", 1.0, 0.6, cuts=(-0.6, 0.2, 0.75))
    a.px(5, 4, "M", "shine")
    a.px(6, 4, "M", "shine")
    a.px(4, 5, "M", "shine")
    for x, y in ((3, 8), (12, 8)):
        a.px(x, y, "B", "shine")


@painted("chestplate")
def chestplate(a):
    """Chestplate: shoulder pauldrons, a ridged breastplate, an accent belt with a buckle."""
    a.stamp([
        ".MMMM....MMMM...",
        "MMMMMM..MMMMMM..",
        "MMMMMMMMMMMMMM..",
        "MMMMMMMMMMMMMM..",
        ".MMMMMMMMMMMM...",
        "..MMMMMMMMMM....",
        "..MMMMMMMMMM....",
        "..MMMMMMMMMM....",
        "..AAAAAAAAAA....",
        "..MMMMMMMMMM....",
        "...MMMMMMMM.....",
    ], {"M": "M", "A": "A"}, 1, 2)
    a.shade_dir("M", 1.0, 0.5, cuts=(-0.55, 0.2, 0.75))
    for y in range(4, 10):
        a.px(7, y, "M", "light")
        a.px(8, y, "M", "dark")
    for x, y in ((2, 3), (11, 3)):
        a.px(x, y, "B", "shine")
    a.px(7, 10, "B", "light")
    a.px(8, 10, "B", "dark")
    a.px(2, 2, "M", "shine")
    a.px(3, 2, "M", "shine")


@painted("leggings")
def leggings(a):
    """Leggings: an accent waist band with a buckle, two plated legs with knee cops."""
    a.stamp([
        "AAAAAAAAAA",
        "MMMMMMMMMM",
        "MMMMMMMMMM",
        "MMMM..MMMM",
        "MMMM..MMMM",
        "MMMM..MMMM",
        "MMMM..MMMM",
        "MMMM..MMMM",
        "MMMM..MMMM",
        "MMM....MMM",
    ], {"M": "M", "A": "A"}, 3, 2)
    a.shade_dir("M", 1.0, 0.4, cuts=(-0.6, 0.2, 0.75))
    for x in (4, 5, 10, 11):
        a.px(x, 7, "M", "deep" if x in (5, 11) else "shine")
        a.px(x, 8, "M", "light")
    a.px(7, 2, "B", "light")
    a.px(8, 2, "B", "dark")
    a.px(3, 3, "M", "shine")


@painted("boots")
def boots(a):
    """Boots: a pair seen side-on, toes turned out, accent cuffs, toe caps and dark heeled soles."""
    a.stamp([
        "...AAA..AAA.....",
        "...MMM..MMM.....",
        "...MMM..MMM.....",
        "...MMM..MMM.....",
        "..MMMM..MMMM....",
        ".MMMMM..MMMMM...",
        "MMMMMM..MMMMMM..",
        "XXX.XX..XX.XXX..",
    ], {"M": "M", "A": "A", "X": "X"}, 1, 5)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.2, 0.75))
    for x, y in ((4, 6), (9, 6)):
        a.px(x, y, "M", "shine")
    for x, y in ((2, 10), (1, 11), (13, 10), (14, 11)):
        a.px(x, y, "M", "light" if x < 8 else "dark")


@painted("goggles")
def goggles(a):
    """Brass goggles: two riveted brass eyecups with amber lenses, a bridge and a leather strap."""
    for y in (7, 8):
        for x in range(0, 16):
            a.px(x, y, "N", "mid" if y == 7 else "dark")
    for cx in (4.5, 11.5):
        a.disc("B", cx, 7.5, 3.6)
        a.sphere("R", cx, 7.5, 2.2)
    a.shade_dir("B", 1.0, 1.0, cuts=(-0.5, 0.1, 0.6))
    for cx in (4, 11):
        a.px(cx - 1, 6, "R", "shine")
    a.box("B", 7, 6, 8, 6)
    a.px(7, 6, "B", "light")
    for x, y in ((2, 5), (9, 5)):
        a.px(x, y, "B", "shine")


@painted("hood")
def hood(a):
    """Arcanist's hood: a peaked cloth hood, a shadowed face with two glowing eyes, gold-trimmed hem."""
    a.stamp([
        "......MM........",
        ".....MMMM.......",
        "....MMMMMM......",
        "...MMMMMMMM.....",
        "..MMMMMMMMMM....",
        "..MMMKKKKKMMM...",
        ".MMMKKKKKKKMMM..",
        ".MMMKKKKKKKMMM..",
        ".MMMMKKKKKMMMM..",
        "MMMMMMMMMMMMMMM.",
        "BBBBBBBBBBBBBBB.",
    ], {"M": "M", "K": "K", "B": "B"}, 0, 2)
    a.shade_dir("M", 1.0, 0.7, cuts=(-0.5, 0.15, 0.7))
    a.px(6, 9, "A", "shine")
    a.px(9, 9, "A", "shine")
    a.px(6, 3, "M", "shine")
    a.px(13, 1, "A", "light")


@painted("robe")
def robe(a):
    """Arcanist's robe: wide sleeves, a gold sash, an embroidered star on the chest."""
    a.stamp([
        "...MMM..MMM.....",
        ".MMMMMMMMMMMM...",
        "MMMMMMMMMMMMMM..",
        "MMMMMMMMMMMMMMM.",
        "MMM.MMMMMM.MMMM.",
        "MM..MMMMMM..MM..",
        "....BBBBBB......",
        "....MMMMMM......",
        "...MMMMMMMM.....",
        "...MMMMMMMM.....",
        "..MMMMMMMMMM....",
        "..MMMMMMMMMM....",
    ], {"M": "M", "B": "B"}, 0, 2)
    a.shade_dir("M", 1.0, 0.5, cuts=(-0.5, 0.2, 0.75))
    for y in range(3, 14):
        if a.m[y][7] == "M":
            a.px(7, y, "M", "deep")
    a.px(6, 5, "A", "shine")
    a.px(5, 5, "A", "light")
    a.px(6, 4, "A", "light")
    a.px(6, 6, "A", "light")
    a.px(7, 5, "A", "light")

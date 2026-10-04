"""The painted shapes of itemart.py (one function per shape name, registered with @painted).

Keys: M = item material, H = handle, A = accent, plus the fixed steampunk keys of itemart.STEAM
(B brass, C copper, V verdigris, I steel, X dark iron, W mahogany, T oak, L oxblood, N tan leather, Q cream,
E aether, R amber, F flame, G glass/ice, K ink, P void glow, S sculk glow, Z ruby).
Tones: s shine, l light, m mid, d dark, e deep, o outline.
"""
import math

from .itemart import cube, diag, painted

T = {"s": "shine", "l": "light", "m": "mid", "d": "dark", "e": "deep", "o": "outline"}


def L(key, rows):
    """Legend for a stamp in a single material: letters are tones, '#' is the auto tone."""
    leg = {ch: (key, t) for ch, t in T.items()}
    leg["#"] = key
    return leg


# ------------------------------------------------------------------ shafts
def shaft(a, length=9, x0=1, y0=14, key="H", grip=None, butt="B"):
    """45-degree two-pixel haft from the bottom-left corner; optional leather grip (rows from the bottom)."""
    diag(a, key, x0, y0, length)
    if grip:
        lo, hi = grip
        diag(a, "L", x0 + lo, y0 - lo, hi - lo)
        for i in range(lo, hi, 2):
            a.px(x0 + i, y0 - i, "L", "dark")
    if butt:
        a.px(x0 - 1 if x0 else x0, y0 + 1 if y0 < 15 else y0, butt)
        a.px(x0, y0, butt, "light")
        a.px(x0 + 1, y0, butt, "dark")


def collar(a, i, x0=1, y0=14, key="B"):
    """A metal ring around the haft at step i (a short horizontal bar across the band)."""
    y = y0 - i
    for x in range(x0 + i - 1, x0 + i + 3):
        a.px(x, y, key)
    a.px(x0 + i - 1, y, key, "light")
    a.px(x0 + i + 2, y, key, "dark")


# ------------------------------------------------------------------ staves and wands


@painted("staff_flame")
def staff_flame(a):
    """Fire staff: a brass claw cradling a living flame."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7)
    # claw: two brass prongs curling around the flame
    a.stamp([
        "..........B.....",
        ".........BB.....",
        ".........B......",
        "........BB......",
        "........B....B..",
        ".........B..BB..",
        "..........BBB...",
    ], {"B": "B"}, 0, 3)
    a.stamp([
        "....d..",
        "...dm.d",
        "..dmlmm",
        "..mlsld",
        ".dmlssm",
        ".dmlslm",
        "..dmlm.",
        "...dd..",
    ], L("F", None), 8, 0)
    a.px(10, 2, "F", "dark")


@painted("staff_snow")
def staff_snow(a):
    """Frost staff: a six-armed ice crystal set on a bone haft."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7, key="I")
    a.stamp([
        "....l...l..",
        ".....l.l...",
        "..l..lsl..l",
        "...l.mSm.l.",
        "....mSwSm..",
        ".lllSwwwSll",
        "....mSwSm..",
        "...l.mSm.d.",
        "..l..lsl..d",
        ".....l.d...",
    ], {"l": ("G", "light"), "m": ("G", "mid"), "S": ("G", "shine"), "s": ("G", "shine"),
        "w": ("G", (255, 255, 255)), "d": ("G", "dark")}, 5, 0)


@painted("staff_bolt")
def staff_bolt(a):
    """Thunder staff: a copper lightning rod wound with coils, a bolt leaping from its tip."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 5, key="C")
    collar(a, 7, key="C")
    a.stamp([
        "....ss",
        "...sl.",
        "..sl..",
        ".sslll",
        "...lm.",
        "..lm..",
        ".lm...",
    ], {"s": ("A", "shine"), "l": ("A", "light"), "m": ("A", "mid")}, 9, 0)


@painted("staff_storm")
def staff_storm(a):
    """Storm staff: an open brass ring holding a crackling sapphire orb."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7)
    a.ring("B", 11.5, 4.5, 2.6, 4.0)
    a.sphere("A", 11.5, 4.5, 2.0)
    for x, y in ((8, 1), (15, 2), (15, 8), (7, 6)):
        a.px(x, y, "A", "shine")
    a.px(11, 8, "B", "dark")


@painted("staff_cross")
def staff_cross(a):
    """Healing staff: a glowing cross inside a brass halo."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7)
    a.ring("B", 11.5, 4.5, 3.1, 4.2)
    a.stamp([
        "..ll..",
        "..ls..",
        "llsssl",
        "lsssmm",
        "..sm..",
        "..mm..",
    ], {"l": ("A", "light"), "s": ("A", "shine"), "m": ("A", "mid")}, 9, 2)


@painted("staff_sun")
def staff_sun(a):
    """Light staff: a radiant sun disc with eight rays."""
    shaft(a, 8, grip=(1, 4))
    collar(a, 7)
    cx, cy = 11.5, 4.5
    for k in range(8):
        ang = k * math.pi / 4
        a.seg("A", cx + math.cos(ang) * 2.5, cy + math.sin(ang) * 2.5, cx + math.cos(ang) * 4.3,
              cy + math.sin(ang) * 4.3, 0.5, "light")
    a.sphere("B", cx, cy, 2.6)
    a.px(11, 4, "A", "shine")
    a.px(12, 4, "A", "light")
    a.px(11, 5, "A", "light")
    a.px(12, 5, "A", "mid")


@painted("wand_float")
def wand_float(a):
    """Levitation wand: a short bone wand, a brass fork and a crystal floating above it, motes rising."""
    diag(a, "H", 2, 14, 7)
    a.px(1, 15, "B")
    a.px(2, 14, "B", "light")
    a.px(3, 14, "B", "dark")
    a.stamp([
        "B...B",
        "BB.BB",
        ".BBB.",
    ], {"B": "B"}, 8, 6)
    a.stamp([
        "..l..",
        ".lsm.",
        "lsmmd",
        "lmmdd",
        ".mdd.",
        "..d..",
    ], L("A", None), 8, 0)
    for x, y in ((6, 2), (15, 3), (7, 5)):
        a.px(x, y, "a", "shine")


@painted("wand_build")
def wand_build(a):
    """Builder's wand: a brass-ringed rod with a block hovering over its tip."""
    shaft(a, 7, grip=(1, 4))
    collar(a, 6)
    cube(a, 8, 0, "A")
    a.px(6, 2, "a", "shine")
    a.px(15, 9, "a", "shine")


@painted("wand_master")
def wand_master(a):
    """Master builder's wand: dark rod, two brass rings, a gem block held in a brass bracket."""
    shaft(a, 7, grip=(1, 4))
    collar(a, 3)
    collar(a, 6)
    cube(a, 8, 0, "A")
    for x, y in ((7, 3), (7, 4), (8, 6), (15, 3), (15, 4), (14, 7)):
        a.px(x, y, "B")
    a.px(5, 1, "a", "shine")


@painted("staff_root")
def staff_root(a):
    """Root Mother's staff: a gnarled branch twisting around a seed of living light, leaves sprouting."""
    a.stamp([
        "..........WW.WW.",
        ".........WW...WW",
        ".........W.....W",
        "........WW.....W",
        "........W.....WW",
        ".........W..WWW.",
        "........WWWWW...",
        ".......WWW......",
        "......WWW.......",
        ".....WWW........",
        "....WW..........",
        "...WWW..........",
        "..WW............",
        ".WWW............",
        "WW..............",
    ], {"W": "W"}, 0, 0)
    a.sphere("A", 12.5, 3.5, 2.1)
    a.stamp(["S.", "SS"], {"S": "S"}, 7, 0)
    a.stamp([".S", "SS", "S."], {"S": "S"}, 5, 7)
    a.px(14, 9, "S")
    a.px(15, 9, "S", "dark")


@painted("cane")
def cane(a):
    """Steam cane: dark shaft, copper steam pipe, a brass knob with a valve wheel and a puff of steam."""
    diag(a, "H", 1, 14, 10)
    for i in range(3, 9):
        a.px(1 + i + 2, 14 - i, "C")
    a.sphere("M", 12.0, 3.6, 2.6)
    a.px(9, 6, "B")
    a.px(10, 6, "B")
    a.px(10, 5, "B", "dark")
    a.px(2, 14, "B")
    a.px(1, 15, "B", "dark")
    # valve wheel and steam
    a.px(7, 6, "Z", "mid")
    a.px(6, 5, "Q", (240, 240, 236))
    a.px(5, 4, "Q", (220, 220, 220))
    a.px(6, 3, "Q", (200, 200, 204))
    a.solo("Q")


# ------------------------------------------------------------------ Clockmaker's Pendulum


@painted("pendulum")
def pendulum(a):
    """A clock pendulum turned weapon: dark iron grip, brass rod, a lens bob with a cream dial and aether core;
    an aether arc trails the swing."""
    diag(a, "X", 1, 14, 4)
    a.px(0, 15, "B")
    a.px(1, 15, "B", "dark")
    collar(a, 4)
    # rod (single brass pixel line), a little fork near the bob
    for i in range(5, 9):
        a.px(1 + i, 14 - i, "B", "light")
        a.px(2 + i, 14 - i, "B", "dark")
    # the bob: brass lens, cream dial, aether core and hands
    a.disc("B", 11.0, 5.0, 4.4)
    a.disc("Q", 11.0, 5.0, 3.0)
    for x, y in ((11, 2), (8, 5), (13, 5), (11, 7)):
        a.px(x, y, "K", "mid")
    a.px(10, 4, "K", "dark")
    a.px(11, 4, "K", "dark")
    a.px(11, 3, "K", "dark")
    a.px(10, 5, "E", "light")
    a.px(11, 5, "E", "mid")
    a.tone(8, 2, "light")
    a.tone(9, 1, "shine")
    a.tone(13, 9, "dark")
    # swing trail
    for x, y, t in ((2, 4, "mid"), (3, 2, "light"), (5, 1, "shine"), (2, 6, "dark")):
        a.px(x, y, "E", t)
    a.solo("E")


# ------------------------------------------------------------------ boss weapons


@painted("ladle")
def ladle(a):
    """Crone's Ladle: a long iron ladle, its bowl brimming with a glowing poison brew; bubbles rise."""
    diag(a, "H", 1, 14, 5)
    diag(a, "M", 6, 9, 3)
    a.px(1, 14, "B")
    # bowl: lower half of a disc, open on top, brew surface across it
    a.paint("M", lambda x, y: (x - 11.5) ** 2 + (y - 5.0) ** 2 <= 4.0 ** 2 and y >= 5.0)
    a.paint("A", lambda x, y: (x - 11.5) ** 2 + (y - 5.0) ** 2 <= 2.9 ** 2 and 4.5 <= y <= 6.5)
    a.box("A", 8, 5, 15, 5)
    a.px(8, 5, "M", "light")
    a.px(15, 5, "M", "dark")
    a.px(10, 5, "A", "shine")
    a.px(11, 5, "A", "light")
    # drip and bubbles
    a.px(12, 9, "A", "mid")
    a.px(12, 10, "A", "dark")
    for x, y, t in ((10, 3, "light"), (13, 2, "shine"), (12, 0, "light"), (9, 1, "mid")):
        a.px(x, y, "A", t)
    a.solo("A")


@painted("flail")
def flail(a):
    """Pharaoh's Flail (nekhakha): a gold handle striped with lapis, three strands of beads hanging from a bar."""
    for i in range(9):
        key = "A" if i % 3 == 1 else "M"
        a.px(1 + i, 14 - i, key, "light")
        a.px(2 + i, 14 - i, key, "dark")
    a.box("M", 10, 4, 15, 4)
    a.px(10, 4, "M", "shine")
    a.px(15, 4, "M", "dark")
    for x, end in ((11, 12), (13, 11), (15, 9)):
        for y in range(5, end + 1):
            a.px(x, y, "A" if (y - 5) // 2 % 2 else "M", "light" if y < 7 else "mid")
        a.px(x, end, "M", "dark")


@painted("mace")
def mace(a):
    """Flanged mace: a crowned head of six gold flanges around a ruby, leather grip on a gold haft."""
    shaft(a, 8, grip=(1, 5))
    collar(a, 7)
    a.disc("M", 11.5, 4.5, 3.0)
    for k in range(6):
        ang = k * math.pi / 3 + 0.3
        a.seg("M", 11.5, 4.5, 11.5 + math.cos(ang) * 4.4, 4.5 + math.sin(ang) * 4.4, 0.6)
    a.sphere("A", 11.5, 4.5, 1.5, shine=False)
    a.px(11, 4, "A", "shine")


@painted("bell_hammer")
def bell_hammer(a):
    """Bell Hammer: a gilded hammer head with a bronze bell hung from its end, clapper swinging."""
    shaft(a, 8, grip=(1, 5))
    a.box("M", 3, 2, 13, 5)
    a.shade_dir("M", 0.25, 1.0)
    for y in range(2, 6):
        a.px(2, y, "A", "light" if y < 4 else "mid")
        a.px(14, y, "A", "dark" if y > 3 else "mid")
    for x in (4, 5, 9, 10):
        a.px(x, 2, "M", "shine")
    a.px(8, 6, "A")
    a.px(9, 6, "A", "dark")
    a.stamp([
        "..d..",
        ".lsm.",
        ".lmd.",
        "llmdd",
        "ddddd",
    ], L("C", None), 11, 6)
    a.px(13, 11, "X", "mid")


@painted("forge_hammer")
def forge_hammer(a):
    """Forge King's Hammer: a black anvil-iron head split by molten seams, an ember core glowing through."""
    shaft(a, 8, grip=(1, 5))
    a.box("X", 4, 1, 14, 6)
    a.px(3, 2, "X")
    a.px(3, 3, "X")
    a.px(3, 4, "X")
    a.px(3, 5, "X")
    a.px(15, 2, "X")
    a.px(15, 3, "X")
    a.px(15, 4, "X")
    a.px(15, 5, "X")
    # molten seams
    for x, y in ((6, 2), (7, 3), (7, 4), (8, 5), (12, 2), (11, 3), (12, 4), (12, 5)):
        a.px(x, y, "F", "mid")
    a.px(9, 3, "F", "shine")
    a.px(10, 3, "F", "light")
    a.px(9, 4, "F", "light")
    a.px(10, 4, "F", "mid")
    # brass faces
    for y in range(2, 6):
        a.px(3, y, "B", "dark" if y > 3 else "mid")
        a.px(15, y, "B", "dark" if y > 3 else "mid")
    a.px(9, 7, "B")
    a.px(10, 7, "B", "dark")


@painted("hammer")
def hammer(a):
    """War hammer: a crystal-faced head bound by two brass bands."""
    shaft(a, 8, grip=(1, 5))
    a.box("M", 4, 1, 13, 5)
    a.shade_dir("M", 0.25, 1.0)
    for y in range(1, 6):
        a.px(3, y, "B", "light" if y < 3 else "mid")
        a.px(14, y, "B", "dark" if y > 2 else "mid")
        a.px(8, y, "B", "light" if y < 3 else "dark")
    a.px(3, 1, "B", "shine")
    for x in (5, 6, 10, 11):
        a.px(x, 1, "M", "shine")
    a.px(9, 6, "B")
    a.px(10, 6, "B", "dark")

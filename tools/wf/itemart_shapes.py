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


@painted("anchor")
def anchor(a):
    """Helmsman's Anchor: a ship's anchor turned war-maul. Leather-wrapped iron grip with a brass ring at the butt, a
    short stock across the shank, a heavy shank and the curved crown of two arms ending in barbed flukes; an amber
    rivet glows at the crown."""
    import math as _m
    shaft(a, 6, key="X", grip=(1, 5), butt=None)
    a.disc("B", 1.5, 14.5, 1.6)                       # the ring at the butt
    a.clear(lambda x, y: (x - 1.5) ** 2 + (y - 14.5) ** 2 < 0.5)
    # the stock: a crossbar perpendicular to the shank, brass-capped
    a.seg("M", 3.5, 8.5, 7.5, 12.5, 0.7)
    a.px(3, 8, "B", "light")
    a.px(7, 12, "B", "dark")
    # the shank, two px wide, up to the crown
    diag(a, "M", 6, 9, 6)
    # the crown: an arc of radius 5.2 around (8.6, 6.4), facing up-right, both arms curving back to the grip
    cx, cy, r = 8.4, 6.6, 5.4

    def arm(x, y):
        d = _m.hypot(x - cx, y - cy)
        ang = _m.degrees(_m.atan2(y - cy, x - cx))        # -45 = toward the top-right corner
        off = abs(((ang + 45) + 180) % 360 - 180)
        return r - 1.0 <= d <= r + 0.6 and off <= 78
    a.paint("M", arm)
    # flukes: barbed tips at both ends of the arc
    for sgn in (-1, 1):
        t = _m.radians(-45 + sgn * 78)
        fx, fy = cx + _m.cos(t) * r, cy + _m.sin(t) * r
        a.disc("M", fx, fy, 1.5)
        a.px(fx - 0.5, fy - 0.5, "M", "light")
    a.shade_dir("M", -0.5, 1.0)
    # amber rivet at the crown, a brass band where the shank meets it
    a.px(11, 3, "R", "light")
    a.px(12, 3, "R", "mid")
    a.px(9, 6, "B", "light")
    a.px(10, 6, "B", "dark")


@painted("chain_flail")
def chain_flail(a):
    """Jailer's Burning Chain: a wrapped dark-iron grip with a gold pommel, a chain of alternating links sagging up
    to a spiked blackstone fetter-ball split by glowing ember cracks."""
    shaft(a, 5, key="X", grip=(1, 4), butt="B")
    collar(a, 5, key="B")
    # the chain: links alternating light (flat) and dark (edge-on), sagging along a curve
    for i, (x, y) in enumerate(((7, 8), (8, 8), (9, 7), (9, 6), (10, 6))):
        a.px(x, y, "I", "light" if i % 2 == 0 else "dark")
    # the ball: a dark disc with gilded spikes all round and ember cracks
    cx, cy = 12.0, 4.0
    for k in range(8):
        ang = k * math.pi / 4 + 0.39
        a.seg("B", cx, cy, cx + math.cos(ang) * 3.9, cy + math.sin(ang) * 3.9, 0.5)
    a.sphere("X", cx, cy, 2.7, shine=False)
    a.px(11, 3, "X", "light")
    a.px(12, 3, "F", "shine")
    a.px(13, 4, "F", "light")
    a.px(12, 5, "F", "mid")
    a.px(11, 5, "F", "dark")


@painted("dane_axe")
def dane_axe(a):
    """Bearded Axe of the Frost Jarl: a long dark haft with a gold pommel, a broad bearded crescent of ice whose edge
    shines, an iron spike behind the socket."""
    shaft(a, 12, key="H", grip=(1, 4), butt="B")
    collar(a, 9, key="B")
    sx, sy = 11.0, 4.6
    ux, uy = 0.7071, -0.7071       # along the haft (up-right)
    vx, vy = -0.7071, -0.7071      # perpendicular, towards the blade (up-left)

    def uv(x, y):
        return (x - sx) * ux + (y - sy) * uy, (x - sx) * vx + (y - sy) * vy

    def blade(x, y):
        u, v = uv(x, y)
        if not 0.5 <= v <= 6.4:
            return False
        lo = -1.0 - 1.15 * (v - 0.5) ** 1.15        # the long beard sweeps down the haft
        hi = 1.0 + 0.55 * (v - 0.5)
        return lo <= u <= hi

    def spike(x, y):
        u, v = uv(x, y)
        return -2.8 <= v <= -0.6 and abs(u) <= 0.8 - 0.25 * (-v - 0.6)
    a.paint("M", blade)
    a.shade_dir("M", 1.0, 1.0, cuts=(-0.5, 0.05, 0.6))
    for y in range(16):
        for x in range(16):
            u, v = uv(x + 0.5, y + 0.5)
            if a.m[y][x] == "M" and v > 5.3:
                a.tone(x, y, "shine")
            elif a.m[y][x] == "M" and 2.2 < v < 3.2 and -1.0 < u < 1.0:
                a.px(x, y, "A", "light")                  # a rune in the ice
    a.paint("X", spike)
    a.stamp(["BB", "BB"], {"B": "B"}, 10, 4)
    a.px(10, 4, "B", "light")
    a.px(11, 5, "B", "dark")


@painted("crozier")
def crozier(a):
    """Crozier of the Drowned Abbess: a long dark driftwood staff with verdigris bands, a knop, and a nautilus crook
    curling over at the top with a glowing sea-glass lamp hanging in its curl."""
    shaft(a, 10, key="H", grip=(1, 4), butt="B")
    collar(a, 7, key="V")
    collar(a, 10, key="B")
    cx, cy = 11.6, 3.9
    for k in range(13):
        ang = math.radians(150 - 30 * k)
        r = 3.4 * math.exp(-0.09 * k)
        a.seg("M", cx + r * math.cos(ang), cy - r * math.sin(ang), cx + r * 0.92 * math.cos(ang - 0.5),
              cy - r * 0.92 * math.sin(ang - 0.5), 0.55 if k < 7 else 0.4)
    a.shade_dir("M", -0.6, 1.0)
    a.px(12, 5, "E", "light")
    a.px(12, 6, "E", "mid")


@painted("cutlass")
def cutlass(a):
    """Boarding Cutlass of the Drowned Admiral: a broad steel blade curving up from the bottom-left to a clipped point,
    a brass basket hilt wrapped round a leather grip, a sea-green glint along the blade and barnacles on its back."""
    a.seg("L", 1.5, 14.5, 3.5, 12.5, 0.7)                     # the grip
    a.px(1, 15, "B", "light")                                 # the pommel
    a.px(0, 15, "B", "dark")
    a.seg("B", 2.0, 10.5, 6.5, 14.5, 0.8)                     # the guard across the blade's root
    a.seg("B", 1.0, 12.0, 2.5, 15.5, 0.5)                     # the basket's knuckle bow
    for k in range(10):                                       # the blade, broad and curving back toward its tip
        t = k / 9
        x0, y0 = 4.5 + t * 8.5, 11.5 - t * 9.0 - math.sin(t * math.pi) * 0.9
        a.disc("M", x0, y0, 1.6 - t * 0.6)
    a.seg("M", 12.6, 3.4, 14.4, 1.4, 0.5)                     # the clipped point
    a.shade_dir("M", -0.6, 1.0)
    for (x, y) in ((6, 9), (8, 7), (10, 5)):
        a.px(x, y, "E", "mid")                                # the sea-green glint along the fuller
    a.px(9, 9, "Q", "light")                                  # barnacles on the back of the blade
    a.px(12, 6, "Q", "mid")


@painted("valve_wrench")
def valve_wrench(a):
    """Valve-Wrench of the Turbine Tyrant: a long steel handle with a leather grip and a hot glowing gauge at its
    neck, and an open-ended jaw at the head (a ring split toward the tip), a brass worm screw on its side."""
    shaft(a, 9, key="M", grip=(1, 4), butt="X")
    cx, cy = 12.3, 3.7
    a.disc("M", cx, cy, 3.3)
    a.clear(lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 < 1.7)                  # the jaw's mouth
    a.clear(lambda x, y: ((x - cx) - (cy - y)) / 1.414 > 0.3 and abs((x - cx) + (cy - y)) / 1.414 < 1.2)
    a.disc("R", 9.3, 6.7, 1.0)                                                  # the overheated gauge
    a.px(9, 6, "R", "light")
    a.px(10, 5, "B", "light")                                                   # the worm screw
    a.px(11, 6, "B", "dark")
    a.shade_dir("M", -0.6, 1.0)


@painted("sunstaff")
def sunstaff(a):
    """Sun-Staff of the Solar Hierarch: a gilded haft with brass bands and a leather grip, and at its head a gold
    sun-ring with short rays round a glowing ember orb."""
    shaft(a, 8, key="H", grip=(1, 4), butt="B")
    collar(a, 6, key="B")
    cx, cy = 11.6, 4.4
    for k in range(8):                                        # the rays
        ang = math.radians(22.5 + 45 * k)
        a.seg("B", cx + 2.6 * math.cos(ang), cy - 2.6 * math.sin(ang), cx + 4.0 * math.cos(ang),
              cy - 4.0 * math.sin(ang), 0.45)
    a.ring("M", cx, cy, 1.6, 2.9)                             # the sun ring
    a.disc("A", cx, cy, 1.6)                                  # the ember orb
    a.shade_dir("M", -0.6, 1.0)
    a.px(11, 4, "A", "light")
    a.px(12, 5, "A", "dark")


@painted("scarab_sceptre")
def scarab_sceptre(a):
    """Scarab Sceptre of the Fourth King: a gilded haft with a dark grip and lapis bands, and at its head a lapis
    scarab with gilded wing-cases spread, holding up a glowing sun-disc with a lapis eye."""
    shaft(a, 7, key="M", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "A", "dark")
    cx, cy = 9.6, 6.4                                         # the scarab, tipped along the haft
    a.disc("A", cx, cy, 1.7)
    a.seg("M", cx - 3.0, cy - 0.2, cx - 0.6, cy + 1.6, 0.6)   # the wing-cases
    a.seg("M", cx + 0.2, cy + 3.0, cx + 1.8, cy + 0.6, 0.6)
    a.px(int(cx), int(cy), "A", "light")
    a.disc("E", 12.4, 3.6, 1.9)                               # the glowing sun-disc
    a.ring("M", 12.4, 3.6, 1.9, 2.8)
    a.px(12, 3, "A", "mid")                                   # its lapis eye
    a.px(14, 2, "M", "light")
    a.shade_dir("M", -0.6, 1.0)


@painted("plumb")
def plumb(a):
    """Plumb of the Abyssal Architect: a dark rule for a haft with brass graduations, a brass crossbar at its head, a
    short chain hanging from the bar's end and a great lead plumb-bob capped in brass, a soul-blue line down it."""
    shaft(a, 9, key="H", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "B", "light")
    a.seg("B", 8.0, 3.0, 12.5, 7.5, 0.5)                      # the crossbar across the head
    a.px(8, 3, "B", "light")
    a.px(12, 7, "B", "dark")
    for y in (8, 9):                                          # the chain off the bar's end
        a.px(12, y, "I", "light" if y % 2 == 0 else "dark")
    a.disc("X", 12.5, 11.4, 2.6)                              # the lead bob
    a.seg("X", 12.5, 12.5, 12.5, 15.4, 0.8)                   # its point
    a.shade_dir("X", -0.6, 1.0)
    a.px(11, 10, "B", "light")                                # the brass cap
    a.px(12, 10, "B", "mid")
    a.px(13, 10, "B", "dark")
    a.px(12, 12, "E", "light")                                # the plumb line
    a.px(12, 13, "E", "mid")


@painted("astrolabe_staff")
def astrolabe_staff(a):
    """Astrolabe of the Star-Eater Curator: a dark staff with brass collars and a leather grip, and at its head a brass
    astrolabe disc inside a hoop, a glowing star at its heart and another on top."""
    shaft(a, 8, key="H", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "B", "light")
    cx, cy = 11.4, 4.6
    a.ring("B", cx, cy, 2.6, 3.5)                             # the armillary hoop
    a.disc("M", cx, cy, 2.2)                                  # the mater
    a.shade_dir("M", -0.6, 1.0)
    a.px(11, 4, "P", "light")                                 # the star at its heart
    a.px(10, 3, "A", "mid")
    a.px(12, 6, "A", "mid")
    a.px(13, 3, "A", "light")
    a.px(14, 1, "P", "light")                                 # the star on top


@painted("macuahuitl")
def macuahuitl(a):
    """Jade Macuahuitl of the Strangler Queen: a root-wrapped wooden haft with a leather grip and a gold band, and a
    broad flat jade paddle running up to a rounded tip, both edges set with dark obsidian teeth and a gold sun-mark
    near its root."""
    shaft(a, 6, key="H", grip=(1, 4), butt="B")
    collar(a, 5, key="B")
    for k in range(9):                                        # the paddle, widening a touch toward its tip
        t = k / 8
        a.disc("M", 7.0 + t * 5.8, 8.0 - t * 5.8, 1.5 + t * 0.6)
    a.shade_dir("M", -0.6, 1.0)
    for k in range(5):                                        # the obsidian teeth along both edges
        t = (k + 0.5) / 5
        cx, cy = 7.0 + t * 5.8, 8.0 - t * 5.8
        r = 1.5 + t * 0.6 + 1.0
        a.px(int(round(cx - r * 0.707)), int(round(cy - r * 0.707)), "X", "dark")
        a.px(int(round(cx + r * 0.707)), int(round(cy + r * 0.707)), "X", "mid")
    a.px(8, 7, "A", "light")                                  # the sun-mark
    a.px(9, 6, "A", "mid")
    a.px(11, 4, "S", "light")                                 # a glint of living jade


@painted("gate_key")
def gate_key(a):
    """Key of the Kneeling Gate: a great gold key held like a mace: the ring bow at the butt with a soul-blue gem,
    a banded shaft, and a heavy toothed bit at the head."""
    a.disc("M", 2.6, 13.4, 2.6)
    a.clear(lambda x, y: (x - 2.6) ** 2 + (y - 13.4) ** 2 < 1.1)
    a.px(2, 13, "A", "light")
    a.px(3, 13, "A", "dark")
    diag(a, "M", 4, 11, 9)
    for i in (3, 6):
        a.px(4 + i, 11 - i, "M", "dark")
        a.px(5 + i, 11 - i, "M", "deep")
    # the bit: teeth standing off the shaft's lower side near the head
    a.seg("M", 10.5, 6.5, 13.5, 9.5, 0.6)
    a.seg("M", 12.5, 4.5, 15, 7, 0.6)
    a.px(14, 9, "M", "dark")
    a.px(15, 6, "M", "dark")
    a.px(13, 1, "M", "light")
    a.px(14, 2, "M", "light")
    a.shade_dir("M", -0.5, 1.0)


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


@painted("tongs")
def tongs(a):
    """Searing Tongs of the Anvil Warden: two dark iron reins bound in leather near the butt, a brass rivet at the
    joint, the jaws reaching up to the corner and a white-hot billet held between their tips."""
    a.seg("M", 1.5, 14.5, 9.5, 6.5, 0.55)                     # the near rein, up to the rivet
    a.seg("M", 3.0, 15.0, 10.0, 7.5, 0.55)                    # the far rein
    for i in (1, 3):
        a.px(2 + i, 13 - i, "L", "mid")                       # the leather binding
        a.px(3 + i, 13 - i, "L", "dark")
    a.disc("B", 9.8, 6.8, 1.1)                                # the rivet
    a.seg("M", 10.0, 5.6, 13.2, 2.4, 0.5)                     # the jaws, a little apart
    a.seg("M", 11.2, 6.6, 14.2, 3.6, 0.5)
    a.shade_dir("M", -0.6, 1.0)
    a.disc("F", 13.6, 2.6, 1.3)                               # the billet
    a.px(13, 2, "F", "shine")
    a.px(10, 6, "B", "light")


@painted("tuning_fork")
def tuning_fork(a):
    """Tuning-Fork Baton of the Hollow Cantor: a black-lacquered baton ringed in brass with a leather grip, ending in a
    brass yoke set with an amethyst resonator and two long steel tines with a pale glint."""
    shaft(a, 8, key="H", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "B", "light")
    a.seg("M", 8.2, 4.4, 11.4, 7.6, 0.75)                     # the brass yoke across the haft
    a.shade_dir("M", -0.6, 1.0)
    a.seg("I", 8.6, 4.0, 12.6, 0.4, 0.5)                      # the two tines
    a.seg("I", 11.2, 6.6, 15.0, 2.6, 0.5)
    a.shade_dir("I", -0.5, 1.0)
    a.px(9, 6, "A", "light")                                  # the amethyst resonator
    a.px(10, 6, "A", "mid")
    a.px(12, 1, "E", "light")                                 # a glint of the note on each tine
    a.px(14, 3, "E", "mid")


@painted("harpoon_gun")
def harpoon_gun(a):
    """Harpoon Gun of the Corsair Captain: a mahogany grip at the bottom left, a dark-iron barrel ringed in brass
    running up to the top right, a copper drum over the grip, a red flare canister under the barrel and a barbed steel
    harpoon at the muzzle."""
    a.seg("W", 2.0, 14.0, 4.5, 11.5, 0.8)                    # the grip
    a.seg("X", 4.0, 12.0, 12.0, 4.0, 0.85)                   # the barrel
    a.shade_dir("X", -0.5, 1.0)
    for x, y in ((6, 10), (9, 7), (11, 5)):                   # brass rings
        a.px(x, y, "B", "light")
        a.px(x + 1, y + 1, "B", "dark")
    a.disc("C", 5.0, 11.0, 1.6)                               # the drum
    a.px(4, 10, "C", "light")
    a.seg("F", 7.0, 11.0, 10.0, 8.0, 0.5)                     # the flare canister
    a.px(10, 8, "F", "shine")
    a.seg("I", 12.0, 4.0, 14.5, 1.5, 0.45)                    # the harpoon shaft
    a.px(14, 1, "I", "shine")
    a.px(13, 1, "I", "light")                                 # the barbs
    a.px(14, 2, "I", "light")
    a.px(12, 1, "I", "mid")
    a.px(15, 3, "I", "mid")


@painted("dragon_staff")
def dragon_staff(a):
    """Dragon Staff of the Chime Abbot: a dark lacquered staff banded in bronze with a leather grip, and at its head a
    bronze dragon looking right, a gold horn swept back, a glowing aether eye, and two chime rods hanging from its jaw."""
    shaft(a, 8, key="H", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "C", "light")
    a.disc("M", 10.4, 4.4, 1.9)                               # the skull
    a.seg("M", 11.0, 4.0, 14.6, 3.6, 0.85)                    # the snout
    a.shade_dir("M", -0.6, 1.0)
    a.seg("B", 9.4, 3.0, 7.6, 0.6, 0.45)                      # the horn, swept back
    a.px(11, 3, "E", "light")                                 # the eye
    a.px(14, 3, "B", "light")                                 # the nostril ridge
    a.px(12, 5, "M", "dark")                                  # the jaw
    a.px(13, 5, "M", "dark")
    a.px(12, 6, "B", "light")                                 # the chimes hanging from it
    a.px(12, 7, "B", "mid")
    a.px(14, 6, "B", "light")
    a.px(14, 7, "B", "mid")
    a.px(14, 8, "V", "mid")


@painted("coal_shovel")
def coal_shovel(a):
    """Soul-Fire Shovel of the Stoker: a dark haft bound in iron with a leather wrap and a brass D-grip knob at the
    bottom left, an iron socket, and at the top right a wide sooty scoop heaped with blue soul embers."""
    shaft(a, 8, key="H", grip=(1, 4), butt="B")
    for i in (5, 7):
        a.px(1 + i, 14 - i, "X", "light")
    a.seg("X", 8.4, 7.6, 9.8, 6.2, 0.7)                      # the socket
    for y in range(16):                                      # the scoop: a squared spade along the diagonal
        for x in range(16):
            v = ((x + 0.5 - 9.6) - (y + 0.5 - 6.4)) / 1.414
            u = ((x + 0.5 - 9.6) + (y + 0.5 - 6.4)) / 1.414
            if 0.4 <= v <= 7.2 and abs(u) <= 2.9:
                edge = v > 6.4 or abs(u) > 2.2
                a.px(x, y, "X", "light" if v > 6.4 else ("dark" if edge else "mid"))
                if not edge and 1.2 <= v <= 5.4 and (x * 7 + y * 3) % 5 < 3:
                    a.px(x, y, "A", "light" if (x + y) % 3 == 0 else "mid")      # the soul embers heaped in it
    a.px(14, 1, "a", "shine")                                # a spark


@painted("drillpick")
def drillpick(a):
    """Drill-Pick of the Mine Baron: a mahogany haft bound in leather, an iron head with a gold pick spike reaching
    up-left and a brass-banded drill cone boring down-right, a lit fuse glowing at the collar."""
    shaft(a, 8, grip=(1, 5))
    a.disc("X", 10.0, 5.5, 2.0)                               # the iron boss of the head
    a.seg("M", 9.0, 4.5, 4.0, 0.8, 0.85)                      # the pick spike, up to its point
    a.seg("M", 5.5, 1.6, 3.2, 0.4, 0.45)
    a.shade_dir("M", -0.5, 1.0)
    a.seg("I", 11.0, 6.5, 15.2, 10.4, 1.25)                   # the drill cone, wide at the head
    a.seg("I", 13.0, 8.5, 15.4, 11.0, 0.6)
    a.shade_dir("I", 0.4, 1.0)
    for x, y in ((12, 6), (13, 8), (14, 9)):                  # the brass spiral of the flutes
        a.px(x, y, "B", "light")
        a.px(x - 1, y + 1, "B", "dark")
    a.px(10, 4, "X", "light")
    a.px(9, 6, "B")                                           # the collar
    a.px(8, 7, "B", "dark")
    a.px(11, 4, "a", "shine")                                 # the fuse spark
    a.px(12, 3, "F", "light")


@painted("bone_saw")
def bone_saw(a):
    """Bone-Saw of the Asylum Director: a mahogany handle at the bottom left with a brass guard, a long steel blade
    toothed along one edge running up to the top right, a dark-iron spine, and a brass pocket watch hanging from the
    guard with an aether glint."""
    a.seg("W", 2.0, 14.0, 4.5, 11.5, 0.8)                     # the handle
    a.seg("B", 3.5, 10.5, 6.0, 13.0, 0.6)                     # the brass guard
    a.seg("I", 5.5, 10.5, 13.5, 2.5, 1.1)                     # the blade
    a.shade_dir("I", -0.5, 1.0)
    a.seg("X", 4.8, 9.8, 12.8, 1.8, 0.45)                     # the spine
    for x in (8, 10, 12):                                     # the teeth along the lower edge
        a.px(x, 18 - x, "I", "light")
        a.px(x + 1, 18 - x, "I", "dark")
    a.px(14, 2, "B", "light")                                 # the tip cap
    a.px(6, 12, "B", "dark")                                  # the chain
    a.disc("B", 7.6, 13.6, 1.4)                               # the pocket watch
    a.px(7, 13, "Q", "light")
    a.px(8, 14, "E", "light")


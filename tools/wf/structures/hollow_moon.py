"""The Hollow Moon (La Lune creuse): a clockwork moon 140 across that fell on an outer island of the End. A sphere of end
stone, purpur and tarnished brass plates, its south-upper third shattered open on the concentric works inside: a second
shell, three static orrery rings tilted round a core platform and the glowing heart of the machine. Colossal tier
(tools/BUILDING.md §1, §12 concept 29, §10 legacy-dungeon template, §15), steampunk accents (brass decks and rails,
gauges, a bubble lift, a lens workshop).

Silhouette (one noun phrase, §15.1): a giant plated sphere sunk in a crater, a third of it torn open on nested shells
and tilted golden rings, chained to its island, debris arcs frozen in flight from the breach.

Layout, island y = 0 (feet 1), x east, z south; the moon's centre is (0, 60, 0); azimuths a in degrees from +x toward +z
(90 = south, the breach side).
  * outer shell r 68..70 (lat-long plate grid, a brass belt on the equator), middle shell r 53.5..55 (an orrery cage of
    ribs, panels and windows); the breach cone points south and 20 degrees up (68 / 50 degrees wide, jagged);
  * outside: the island (crater rim of brass wreckage, four giant chains from the belt to bollards), debris arcs and
    floating shards, the astronomers' camp on a shard to the south (waystone), the bridge north into the breach (a
    stair tower down to the crater on the way);
  * the outer galleries (deck A, feet 25, between the shells): the breach landing (south), the gravity gardens
    (west), the Meridian Hall (north: hub, waystone, pendulum, the grand stair up), the escapement gallery (east: the
    stair down to the gear crypt, the pool under the drop);
  * deck B (feet 46): the lens workshop (north, the ring door), the star-chart dome (west), the observation terrace
    (east, the drop to the breach);
  * the gear crypt (feet 9) at the bottom between the shells, the sump inside the middle shell's floor;
  * inward through the rings: ring 1 (r 45) from its low point at the ring door half a turn up to ring 2 (r 35), over
    the top to ring 3 (r 26), down to its low point: the site of grace; through the mist, the core platform (r 17,
    feet 50) under the glowing core; the core reliquary below the platform's north rim behind sealed bars.
  * shortcuts: the reliquary's levitation shaft (a water tube under an iron trapdoor, down to the sump pool), the
    bubble lift from the crypt to the Meridian Hall (iron door, opens from inside), the one-way ring door (iron, lever on
    the grace side) on the spoke from the grace to ring 1, the drop from deck B's east terrace into the breach pool.
Loot gradient (§15.6): camp, landing 1; gardens, galleries, hub 1-2; workshop, star dome, crypt 2; rings 2-3; reliquary 3.
Height budget: the shell's top is 130 above the island, the keel reaches ~35 below it.
"""
import math
import random

from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import (BRASS, BRASS_SLAB, CHANDELIER, COPPER, EDISON, GAUGE, GEAR, HANG_LAMP, IRON, IRON_SLAB, PIPES,
                       TABLE, TREAD, TREAD_SLAB, VERD, W, hash01, hash3, out_facing, vnoise)
from ..parts import LOOT, MOB, MOD
from .end import (ESB, ESB_SL, ESB_ST, ESB_WA, FROG, OUTER_END, PUR, PUR_P, PUR_SL, PUR_ST, ROD_DOWN, ROD_UP, STAR,
                  VB, VB_SL, VB_ST, VB_WA, build_rock, chorus_tree, disk_pts, merge_cols, ring3d, rock_lobe)

# the champion of the core platform: the Moon Warden (tools/wf/mobs/moon_warden.py, entity/boss/MoonWarden.java)
BOSS = "brasshaven:moon_warden"
MOB_ACOLYTE = W + "void_acolyte"
MOB_STALKER = MOB["void_stalker"]
MOB_SPIDER = W + "clockwork_spider"
MOB_DRONE = W + "steam_drone"
MOB_SENTINEL = W + "rift_sentinel"

AIR = "minecraft:air"
GOLD = "gold_block"
OBS = "obsidian"
CRY = "crying_obsidian"
SEA = "sea_lantern"
ENGR = W + "engraved_brass"
BTILE = W + "brass_tiles"
GRILLE = W + "brass_grille"
GILD = W + "gilded_trim"
COPPER_SL = W + "copper_plating_slab"
VERD_SL = W + "verdigris_plating_slab"
TARN = "waxed_weathered_copper"
RAIL = W + "brass_railing"
LANT = "lantern[hanging=false,waterlogged=false]"
LANT_H = "lantern[hanging=true,waterlogged=false]"
SOUL_H = "soul_lantern[hanging=true,waterlogged=false]"
SOUL = "soul_lantern[hanging=false,waterlogged=false]"
CHAIN_Y = "iron_chain[axis=y,waterlogged=false]"
WATER = "water[level=0]"
MIST = "brasshaven:mist_gate[sealed=false]"

# ------------------------------------------------------------------ dimensions
CY = 60                                  # the moon's centre height (x = z = 0)
RO, RI = 70.0, 68.0                      # outer shell: outer / inner face
MO, MI = 55.0, 53.5                      # middle shell
FA, FB = 25, 46                          # deck A / deck B feet (floors at 24 / 45)
FC = 9                                   # crypt and sump feet (floor y 8)
FP, PR = 50, 17                          # platform feet and radius
CORE = (0, 66, 0)
TILT = math.radians(20)
DB = (0.0, math.sin(TILT), math.cos(TILT))   # the breach axis (south, 20 degrees up)
# the rings: s = CY + A x + B z (planes through the centre), radius, half width
RINGS = {1: (45, 0.0, 13.0 / 45.0), 2: (35, 0.0, -0.30), 3: (26, -0.2505, 0.2104)}
ALPHA_G = 320.0                          # the site of grace on ring 3 (its low point)
F_GRACE = 52.0
CAMP = (4, 108)
F_CAMP = 23
TOWER = (-8, 70)
LIFT = (0, -45)                          # the bubble lift's column (crypt -> Meridian Hall)
SHAFT = (3, -9)                          # the levitation shaft (reliquary -> sump)
REL = (-6, -20, 6, -9)                   # the reliquary's interior x0, z0, x1, z1
F_REL = 41


# ------------------------------------------------------------------ small helpers
def ang(x, z):
    return math.degrees(math.atan2(z, x)) % 360.0


def polar(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def in_arc(a, a0, a1):
    return (a - a0) % 360.0 <= (a1 - a0) + 1e-9


def adelta(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def q2(s):
    return round(s * 2) / 2.0


def slab(spec, kind="bottom"):
    return f"{spec}[type={kind},waterlogged=false]"


def d3(x, y, z):
    return math.sqrt(x * x + (y - CY) ** 2 + z * z)


def bang(x, y, z):
    """Angle (degrees) between the cell's direction from the centre and the breach axis."""
    d = d3(x, y, z) or 1.0
    c = (y - CY) * DB[1] / d + z * DB[2] / d
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def psi(x, y, z):
    """Angle round the breach axis (for jagged edges)."""
    v1 = x
    v2 = (y - CY) * DB[2] - z * DB[1]
    return math.atan2(v2, v1)


def theta_out(p):
    return 68 + 4.0 * math.sin(3 * p + 0.7) + 2.5 * math.sin(7 * p + 2.1) + 6 * (vnoise(math.degrees(p), 0.5, 7.0,
                                                                                       5101) - 0.5)


def theta_mid(p):
    return 50 + 3.0 * math.sin(4 * p + 1.3) + 2.0 * math.sin(9 * p + 0.2) + 6 * (vnoise(math.degrees(p), 0.5, 6.0,
                                                                                      5102) - 0.5)


def shell_bottom(rho):
    """y of the outer shell's outer face under the moon at horizontal distance rho."""
    return CY - math.sqrt(max(0.0, RO * RO - rho * rho))


class Ctx:
    """Blueprint wrapper: ``keep`` holds reserved cells (walkways' headroom) that decoration (``put``) never fills."""

    def __init__(self, bp):
        self.bp = bp
        self.keep = set()

    def set(self, x, y, z, spec):
        self.bp.set(x, y, z, spec)
        self.keep.discard((x, y, z))

    def put(self, x, y, z, spec):
        if (x, y, z) not in self.keep:
            self.bp.set(x, y, z, spec)

    def get(self, x, y, z):
        return self.bp.get(x, y, z)

    def clear(self, x, y, z):
        """Explicit air (cuts through existing blocks), reserved."""
        self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def clear_if(self, x, y, z):
        """Air only where something was built; reserved either way (no entries spent on the void)."""
        if self.bp.get(x, y, z) is not None:
            self.bp.set(x, y, z, AIR)
        self.keep.add((x, y, z))

    def solid(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is not None and b != AIR and "water" not in b and "bubble" not in b

    def free(self, x, y, z):
        b = self.bp.get(x, y, z)
        return b is None or b == AIR


WALK = {}                                # (x, z) -> [feet s] of every walkway / ring / stair cell


def reg(x, z, s):
    WALK.setdefault((x, z), []).append(s)


def rail_ok(x, z, s):
    return all(abs(t - s) >= 3.0 for t in WALK.get((x, z), ()))


def surface(C, x, z, s, full, half, under=None):
    """Walking surface at feet s (multiple of 0.5): a full block, or a bottom slab on `under`. Returns the top block y."""
    n = math.floor(s)
    if s - n > 0.25:
        C.set(x, n, z, slab(half))
        C.set(x, n - 1, z, under or full)
        return n
    C.set(x, n - 1, z, full)
    return n - 1


def railing(C, x, y, z, facing):
    C.set(x, y, z, f"{RAIL}[facing={facing}]")


def rail_at(C, x, z, s, facing, under=BRASS_SLAB, post=None):
    """A railing on the edge of a walk at feet s (a top slab carries it where nothing is below)."""
    top = math.ceil(s - 0.01)
    if not rail_ok(x, z, s) or not C.free(x, top, z) or (x, top, z) in C.keep:
        return False
    if C.free(x, top - 1, z):
        C.set(x, top - 1, z, slab(under, "top"))
    if post:
        C.set(x, top, z, post[0])
        C.set(x, top + 1, z, post[1])
    else:
        railing(C, x, top, z, facing)
    return True


def lever(C, x, y, z, facing, face="wall"):
    C.set(x, y, z, f"lever[face={face},facing={facing},powered=false]")


def iron_door(C, x, y, z, facing, hinge="left"):
    for half, dy in (("lower", 0), ("upper", 1)):
        C.set(x, y + dy, z, f"iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")


def candle(C, x, y, z, n=3, color="white"):
    C.put(x, y, z, f"{color}_candle[candles={n},lit=true,waterlogged=false]")


def hang(C, x, y_top, z, n, lamp):
    """A chain of n under the block at y_top (which must be solid), the lamp under it."""
    if not C.solid(x, y_top, z):
        return
    for k in range(1, n + 1):
        C.put(x, y_top - k, z, CHAIN_Y)
    C.put(x, y_top - n - 1, z, lamp)


def line3(C, p0, p1, spec, every=None, alt=None):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 1.3) + 1
    seen = []
    for i in range(n + 1):
        t = i / n
        p = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if p in seen:
            continue
        seen.append(p)
        C.put(*p, alt if (every and alt and len(seen) % every == 0) else spec)
    return seen


def radial_box(a, r0, r1, half_w):
    """Columns within half_w (blocks) of the ray at azimuth a, between radii r0 and r1."""
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    out = []
    R = int(r1) + 2
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            t = x * ux + z * uz
            p = -x * uz + z * ux
            if r0 <= t <= r1 and abs(p) <= half_w:
                out.append((x, z, t, p))
    return out


# ------------------------------------------------------------------ walkways, spirals
def style_mats(style, mid):
    if style == "brass":
        return (BRASS if mid else TREAD), (BRASS_SLAB if mid else TREAD_SLAB), BRASS, BRASS_SLAB
    if style == "copper":
        return (COPPER if mid else VERD), (COPPER_SL if mid else VERD_SL), COPPER, COPPER_SL
    if style == "void":
        return (VB if mid else IRON), (VB_SL if mid else IRON_SLAB), VB, VB_SL
    if style == "rock":
        return "polished_blackstone_bricks", "polished_blackstone_brick_slab", "blackstone", \
            "polished_blackstone_brick_slab"
    return (PUR if mid else ESB), (PUR_SL if mid else ESB_SL), VB, VB_SL


def walkway(C, pts, width=3, style="brass", rails=True, head=3, lamp_every=8):
    """A walkway along a polyline of (x, feet s, z) points, quantised to half blocks (slope <= 0.5 per block).
    Returns {(x, z): s}."""
    hw = width // 2
    deck_c, rail_c = {}, {}
    total = sum(math.hypot(b[0] - a[0], b[2] - a[2]) for a, b in zip(pts, pts[1:])) or 1.0
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        if L < 1e-6:
            continue
        if abs(b[1] - a[1]) / L > 0.52:
            print(f"hollow_moon: walkway segment {a}->{b} too steep ({abs(b[1] - a[1]) / L:.2f})")
        ux, uz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
        px, pz = -uz, ux
        n = int(L * 3) + 1
        for i in range(n + 1):
            t = i / n
            cx, cz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            s = a[1] + (b[1] - a[1]) * t
            tt = (acc + L * t) / total
            for w in range(-hw - 1, hw + 2):
                X, Z = round(cx + px * w), round(cz + pz * w)
                (rail_c if abs(w) == hw + 1 else deck_c).setdefault((X, Z), []).append((abs(w), s, tt))
        acc += L
    out = {}
    for (X, Z), ss in deck_c.items():
        ss.sort()
        s = q2(ss[0][1])
        out[(X, Z)] = s
        reg(X, Z, s)
    for (X, Z), s in out.items():
        full, half, under, uslab = style_mats(style, deck_c[(X, Z)][0][0] == 0)
        y = surface(C, X, Z, s, full, half, under)
        for c in range(1, head + 1):
            C.clear_if(X, y + c, Z)
        if C.free(X, y - 1, Z):
            C.set(X, y - 1, Z, slab(uslab, "top"))
    if rails:
        k = 0
        for (X, Z), ss in sorted(rail_c.items(), key=lambda kv: min(v[2] for v in kv[1])):
            if (X, Z) in deck_c:
                continue
            ss.sort()
            s = q2(ss[0][1])
            nb = min(((x2, z2) for (x2, z2) in ((X + 1, Z), (X - 1, Z), (X, Z + 1), (X, Z - 1)) if (x2, z2) in out),
                     default=None)
            if nb is None:
                continue
            if C.solid(X, math.ceil(s - 0.01) - 1, Z):
                continue                                   # a floor at the same level: no railing
            k += 1
            post = (BRASS, LANT) if lamp_every and k % lamp_every == 0 else None
            rail_at(C, X, Z, s, out_facing(X - nb[0], Z - nb[1]), post=post)
    return out


def spiral(C, segs, rc, w, full, half, fill, base=None, head=4, rails=True, rmax=62, cx=0, cz=0):
    """A stair winding round (cx, cz): segs [(a0, a1, s0, s1)] (a1 > a0, may pass 360), feet s linear in the angle;
    the centre-line radius rc may be a function of s; the band is w wide. Low treads (within 4 of `base`) are filled
    down to it. Returns {(x, z): s}."""
    cells = {}
    R = int(rmax) + 2
    for x in range(cx - R, cx + R + 1):
        for z in range(cz - R, cz + R + 1):
            d = math.hypot(x - cx, z - cz)
            if d > rmax + 1:
                continue
            a = ang(x - cx, z - cz)
            for (a0, a1, s0, s1) in segs:
                if in_arc(a, a0, a1):
                    t = ((a - a0) % 360.0) / (a1 - a0)
                    s = s0 + (s1 - s0) * t
                    c = rc(s) if callable(rc) else rc
                    if abs(d - c) <= w / 2.0:
                        cells[(x, z)] = q2(s)
                    break
    for (x, z), s in cells.items():
        reg(x, z, s)
    for (x, z), s in cells.items():
        y = surface(C, x, z, s, full, half, under=fill)
        for c in range(1, head + 1):
            C.clear_if(x, y + c, z)
        if base is not None and s - base <= 4.0:
            for yy in range(base - 1, y):
                if C.free(x, yy, z):
                    C.set(x, yy, z, fill)
        elif C.free(x, y - 1, z):
            C.set(x, y - 1, z, slab(half, "top"))
    if rails:
        for (x, z), s in cells.items():
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, z + dz)
                if n in cells:
                    continue
                top = math.ceil(s - 0.01)
                if C.solid(n[0], top - 1, n[1]) or C.solid(n[0], top, n[1]):
                    continue
                rail_at(C, n[0], n[1], s, out_facing(dx, dz))
    return cells


def guard(C, cells, y_floor):
    """Railings on a floor (top block y_floor) round the well cut by a stair: on floor cells next to treads that are
    two or more below the floor's feet."""
    for (x, z), s in cells.items():
        if s > y_floor + 1 - 1.5:
            continue
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in cells or not C.solid(n[0], y_floor, n[1]) or not C.free(n[0], y_floor + 1, n[1]):
                continue
            if (n[0], y_floor + 1, n[1]) in C.keep:
                continue
            if not rail_ok(n[0], n[1], y_floor + 1):
                continue
            railing(C, n[0], y_floor + 1, n[1], out_facing(dx, dz))


# ------------------------------------------------------------------ the shells
def shell_cells(r_in, r_out, extra=0.0):
    """(x, y, z, d) of every cell with r_in < d <= r_out (+ extra), by columns."""
    R = r_out + extra
    Ri = int(math.ceil(R)) + 1
    for x in range(-Ri, Ri + 1):
        for z in range(-Ri, Ri + 1):
            rho2 = x * x + z * z
            if rho2 > R * R:
                continue
            hi = math.sqrt(R * R - rho2)
            lo = math.sqrt(r_in * r_in - rho2) if rho2 < r_in * r_in else 0.0
            ys = list(range(math.floor(CY - hi) - 1, math.ceil(CY - lo) + 2))
            ys += [y for y in range(math.floor(CY + lo) - 1, math.ceil(CY + hi) + 2) if y > ys[-1]]
            for y in ys:
                d = math.sqrt(rho2 + (y - CY) ** 2)
                if r_in < d <= R:
                    yield x, y, z, d


OUT_PANELS = [(ESB, 30), ("end_stone", 12), (PUR, 16), (BRASS, 10), (COPPER, 6), (VERD, 10), (TARN, 4), (VB, 6),
              (BTILE, 4)]
MID_PANELS = [(PUR, 40), (VB, 22), (ESB, 14), ("purple_stained_glass", 12), (BTILE, 6), (COPPER, 6)]


def pick_w(table, h):
    tot = sum(w for _, w in table)
    acc = 0.0
    for spec, wt in table:
        acc += wt / tot
        if h < acc:
            return spec
    return table[-1][0]


def outer_shell(C):
    """The moon's plate armour: a latitude-longitude grid of brass seams over patchwork panels, dark iron ribs on the
    inner face, the brass belt on the equator, the breach torn open with scorched, holed edges."""
    for (x, y, z, d) in shell_cells(RI, RO):
        b = bang(x, y, z)
        th = theta_out(psi(x, y, z))
        if b < th:
            continue
        edge = b - th
        rho = math.hypot(x, z)
        lat = math.degrees(math.asin(max(-1.0, min(1.0, (y - CY) / d))))
        lon = ang(x, z)
        h = hash3(x, y, z, 5110)
        if edge < 4.5 and h < 0.22 * (1 - edge / 4.5):
            continue                                   # torn plates along the breach
        sm = abs(((lon + 7.5) % 15) - 7.5) * math.pi / 180 * rho < 0.55
        sp = abs(((lat + 6) % 12) - 6) * math.pi / 180 * d < 0.55
        if d > 69.0:
            if abs(y - CY) <= 1:
                spec = GEAR if round(lon * 2) % 9 == 0 else BRASS
            elif sm and sp:
                spec = ENGR
            elif sm or sp:
                spec = BRASS if not (sm and abs(lat) > 70) else ENGR
            else:
                pid = (int((lon + 7.5) // 15), int((lat + 6) // 12))
                spec = pick_w(OUT_PANELS, hash01(pid[0], pid[1], 5111))
                if spec == ESB and h < 0.12:
                    spec = "end_stone"
                elif spec in (BRASS, COPPER) and h < 0.15:
                    spec = VERD                        # tarnish
        else:
            spec = IRON if (sm or sp) else (VB if h < 0.5 else (ESB if h < 0.8 else PUR))
        # scorch: the breach's lip and the crash contact underneath
        if edge < 5.0 and hash3(x, y, z, 5112) < 0.55 * (1 - edge / 5.0):
            spec = OBS if hash3(x, y, z, 5113) < 0.7 else CRY
        elif y < 10 and hash3(x, y, z, 5114) < (10 - y) / 26.0:
            spec = OBS if hash3(x, y, z, 5115) < 0.75 else "blackstone"
        C.set(x, y, z, spec)
    # the belt stands proud of the shell: a brass band with gear teeth and rivets
    for (x, y, z, d) in shell_cells(RO, RO + 1.4):
        if abs(y - CY) > 1:
            continue
        if bang(x, y, z) < theta_out(psi(x, y, z)) + 2:
            continue
        lon = ang(x, z)
        if y == CY:
            spec = GEAR if round(lon * 3) % 7 == 0 else ENGR
        else:
            spec = stair("brasshaven:brass_plating_stairs", out_facing(-x, -z), "top" if y > CY else "bottom")
        C.set(x, y, z, spec)


def mid_shell(C):
    """The orrery cage: brass ribs every 20 degrees of longitude and 15 of latitude, panels of purpur, void bricks and
    glass; broken open on the breach side."""
    for (x, y, z, d) in shell_cells(MI, MO):
        b = bang(x, y, z)
        th = theta_mid(psi(x, y, z))
        if b < th:
            continue
        edge = b - th
        h = hash3(x, y, z, 5120)
        if edge < 4.0 and h < 0.3 * (1 - edge / 4.0):
            continue
        rho = math.hypot(x, z)
        lat = math.degrees(math.asin(max(-1.0, min(1.0, (y - CY) / d))))
        lon = ang(x, z)
        sm = abs(((lon + 10) % 20) - 10) * math.pi / 180 * rho < 0.6
        sp = abs(((lat + 7.5) % 15) - 7.5) * math.pi / 180 * d < 0.6
        outer = d > 54.25
        if sm or sp:
            spec = (GEAR if (sm and sp) else BRASS) if outer else IRON
        else:
            pid = (int((lon + 10) // 20), int((lat + 7.5) // 15))
            spec = pick_w(MID_PANELS, hash01(pid[0], pid[1], 5121))
            if spec == "purple_stained_glass" and (abs(lat) > 60 or y < 30):
                spec = PUR
        if edge < 4.0 and hash3(x, y, z, 5122) < 0.5 * (1 - edge / 4.0):
            spec = OBS if hash3(x, y, z, 5123) < 0.6 else CRY
        C.set(x, y, z, spec)


# ------------------------------------------------------------------ the island
def island_cols():
    cols = {}
    rng = random.Random(5130)
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    cx, cz, rx, rz = 0, 2, 64.0, 60.0
    for x in range(-72, 73):
        for z in range(-66, 82):
            rho = math.hypot(x, z)
            dx, dz = (x - cx) / rx, (z - cz) / rz
            th = math.atan2(dz, dx)
            rim = 1 + 0.07 * math.sin(3 * th + ph[0]) + 0.05 * math.sin(5 * th + ph[1]) + 0.03 * math.sin(11 * th + ph[2])
            e = math.hypot(dx, dz) / rim
            # the spit under the bridge
            es = math.hypot(x / 15.0, (z - 66) / 12.0)
            if e > 1 and es > 1:
                continue
            ee = min(e, es * 1.1)
            top = 0 - (1 if ee > 0.9 else 0) - (1 if ee > 0.97 else 0)
            # the crater rim: ejecta heaped round the moon
            if 36 <= rho <= 58:
                bump = max(0.0, 1 - ((rho - 44) / 10.0) ** 2)
                top += round(4.5 * bump * (0.7 + 0.6 * vnoise(x, z, 6.0, 5131)))
            if rho < 37:
                top = min(top, math.floor(shell_bottom(rho)) - 1 if rho < 35.8 else top)
            dep = 2 + 10 * max(0.0, 1 - ee * ee) ** 0.9 * (0.75 + 0.5 * vnoise(x, z, 9.0, 5132))
            if rho < 30:
                dep += 12 * (1 - rho / 30.0) ** 1.4
            for (sx, sz, sr, sl) in ((30, 28, 8, 9), (-34, 20, 7, 8), (10, -40, 9, 10), (-2, 66, 6, 8)):
                dd = math.hypot(x - sx, z - sz)
                if dd < sr:
                    dep += sl * (1 - dd / sr) ** 1.6
            cols[(x, z)] = (round(top - dep), top)
    return cols


def island(C):
    cols = island_cols()
    build_rock(C.bp, cols, 5133, surface="end_stone", keep=True)
    return cols


# ------------------------------------------------------------------ decks
def deck_a_gap(x, z, r, a):
    """The breach landing's broken rim (deck A floor missing beyond it), the bridge corridor excepted."""
    if not in_arc(a, 40, 140) or (abs(x) <= 2 and z > 0):
        return False
    return r > 51 + 4.5 * vnoise(a, 0.0, 6.0, 5140)


def deck_b_gap(x, z, r, a):
    return adelta(a, 90) < 55 + 5 * vnoise(r, a / 3.0, 3.0, 5141) - 2


FLOOR_A, FLOOR_B, CRYPT_FLOOR = set(), set(), set()


def decks(C):
    """Deck A (the outer galleries) and deck B: floors spanning the gap between the shells, a lighter tread path along
    each, radial purpur seams, brass bands."""
    for (yf, store, gap, path) in ((FA - 1, FLOOR_A, deck_a_gap, (49.5, 51.5)), (FB - 1, FLOOR_B, deck_b_gap,
                                                                                 (59.5, 61.5))):
        for x in range(-68, 69):
            for z in range(-68, 69):
                d = d3(x, yf, z)
                if not (MO < d <= RI):
                    continue
                r = math.hypot(x, z)
                a = ang(x, z)
                if gap(x, z, r, a):
                    continue
                if path[0] <= r < path[1]:
                    spec = TREAD
                elif abs(((a + 7.5) % 15) - 7.5) * math.pi / 180 * r < 0.6:
                    spec = PUR
                elif d > RI - 1.2:
                    spec = BRASS
                elif yf == FA - 1 and r < 46:
                    spec = VB
                else:
                    spec = ESB if hash01(x, z, 5142 + yf) < 0.85 else VB
                C.set(x, yf, z, spec)
                store.add((x, z))
                reg(x, z, yf + 1)
    # deck B rests on corbels against the outer shell, deck A on brass joists over the void
    for (x, z) in FLOOR_B:
        r = math.hypot(x, z)
        if d3(x, FB - 2, z) > RI - 1.0 and C.free(x, FB - 2, z):
            C.set(x, FB - 2, z, stair("purpur_stairs", out_facing(-x, -z), "top"))
            if C.free(x, FB - 3, z) and not C.free(x, FB - 4, z):
                C.set(x, FB - 3, z, VB)     # no crawl-space pocket under the corbel
    for (x, z) in FLOOR_A:
        a = ang(x, z)
        if abs(((a + 7.5) % 15) - 7.5) * math.pi / 180 * math.hypot(x, z) < 0.6 and C.free(x, FA - 2, z):
            C.set(x, FA - 2, z, IRON)


def edge_rails(C, floor, y_floor, region):
    """Brass railings along the broken edges of a floor (cells with a neighbour that has no floor)."""
    k = 0
    for (x, z) in sorted(floor):
        if not region(x, z):
            continue
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in floor or C.solid(n[0], y_floor, n[1]):
                continue
            if not C.free(x, y_floor + 1, z) or (x, y_floor + 1, z) in C.keep:
                break
            k += 1
            if k % 11 == 0:
                C.set(x, y_floor + 1, z, BRASS)
                C.set(x, y_floor + 2, z, LANT)
            else:
                railing(C, x, y_floor + 1, z, out_facing(dx, dz))
            break


def fill_gaps(C, cols, y_floor, up=True, maxgap=2, spec=VB):
    """Seal the slivers (<= maxgap high) between a floor and the shell above it (up) or below it: no crawl spaces."""
    for (x, z) in cols:
        cells = []
        y = y_floor + 1 if up else y_floor - 1
        while len(cells) <= maxgap and C.free(x, y, z):
            cells.append(y)
            y += 1 if up else -1
        if 0 < len(cells) <= maxgap and C.solid(x, y, z):
            if any((x, yy, z) in C.keep for yy in cells):
                continue
            for yy in cells:
                C.set(x, yy, z, spec)


def radial_wall(C, a, ylo, yhi, door=None, mat=VB, trim=PUR_P, band=None, r_range=(0, 70)):
    """A wall along the ray at azimuth a between the shells (one block thick), y ylo..yhi; door = (r_mid, w, h)."""
    cells = []
    for (x, z, t, p) in radial_box(a, r_range[0], r_range[1], 0.55):
        for y in range(ylo, yhi + 1):
            d = d3(x, y, z)
            if not (MO < d < RI):
                continue
            if door and abs(t - door[0]) <= door[1] / 2.0 and y < ylo + door[2]:
                C.clear(x, y, z)
                continue
            spec = mat
            if round(t) % 6 == 0:
                spec = trim
            if band and y in band:
                spec = BRASS
            if door and abs(t - door[0]) <= door[1] / 2.0 + 1.0 and y == ylo + door[2]:
                spec = GOLD if abs(t - door[0]) < 0.6 else PUR
            C.set(x, y, z, spec)
            cells.append((x, y, z))
    if door:
        for side in (-1, 1):
            tt = door[0] + side * (door[1] / 2.0 + 1.0)
            for (x, z, t, p) in radial_box(a, tt - 0.5, tt + 0.5, 0.55):
                for y in range(ylo, ylo + door[2]):
                    if MO < d3(x, y, z) < RI:
                        C.set(x, y, z, PUR_P)
    return cells


def deck_lights(C):
    """Glow set in the middle shell's face along both decks, lamps hung under deck B, posts on deck B."""
    for k in range(36):
        a = 5 + 10 * k
        for (yy, rr) in ((FA + 3, None), (FB + 4, None)):
            # the first shell cell along the ray at this height
            for r10 in range(300, 560):
                r = r10 / 10.0
                x, z = polar(r, a)
                x, z = round(x), round(z)
                if MO - 0.8 < d3(x, yy, z) <= MO + 0.01 and C.solid(x, yy, z):
                    if not deck_a_gap(x, z, math.hypot(x, z), a) or yy != FA + 3:
                        C.put(x, yy, z, FROG if k % 2 else STAR)
                    break
    for k in range(24):
        a = 7.5 + 15 * k
        x, z = polar(56.5, a)
        x, z = round(x), round(z)
        if (x, z) in FLOOR_A and C.solid(x, FB - 1, z) and C.free(x, FB - 2, z):
            hang(C, x, FB - 1, z, 3, HANG_LAMP)
        x, z = polar(64.5, a + 7.5)
        x, z = round(x), round(z)
        if (x, z) in FLOOR_B and C.free(x, FB, z) and (x, FB, z) not in C.keep:
            C.put(x, FB, z, IRON)
            C.put(x, FB + 1, z, W + "dark_iron_plating_wall")
            C.put(x, FB + 2, z, EDISON)


def columns(C):
    """Brass columns (3 x 3, base and capital) on deck A carrying deck B, every 15 degrees except at the landing and
    the grand stair."""
    for k in range(24):
        a = 7.5 + 15 * k
        if in_arc(a, 36, 144) or in_arc(a, 228, 300):
            continue
        x0, z0 = polar(55.5, a)
        x0, z0 = round(x0), round(z0)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                x, z = x0 + dx, z0 + dz
                if (x, z) not in FLOOR_A:
                    continue
                for y in range(FA, FB - 1):
                    corner = dx != 0 and dz != 0
                    if y in (FA, FB - 2):
                        spec = ENGR
                    elif corner:
                        spec = PUR_P
                    else:
                        spec = BRASS if (y - FA) % 6 else GEAR
                    C.put(x, y, z, spec)


# ------------------------------------------------------------------ the stairs between levels
GRAND = {}
CRYPT_STAIR = {}


def stairs_between(C):
    """The grand stair (Meridian Hall -> deck B) and the conical stair (escapement gallery -> gear crypt)."""
    GRAND.update(spiral(C, [(232, 258, FA, 36), (258, 266, 36, 36), (266, 294, 36, FB)], 56.0, 4.0, PUR, PUR_SL, VB,
                        base=FA))
    guard(C, GRAND, FB - 1)
    CRYPT_STAIR.update(spiral(C, [(330, 352, FA, 17), (352, 358, 17, 17), (358, 382, 17, FC)],
                              lambda s: 40.0 + (s - FC) * 12.0 / 16.0, 3.0, ESB, ESB_SL, VB, base=FC))
    guard(C, CRYPT_STAIR, FA - 1)


# ------------------------------------------------------------------ deck A rooms
def landing(C):
    """The breach landing: rubble from the impact, a fallen planet of the orrery, toppled plates, the way in."""
    rng = random.Random(5150)
    for (x, z) in sorted(FLOOR_A):
        a = ang(x, z)
        if not in_arc(a, 46, 134) or abs(x) <= 2:
            continue
        h = hash01(x, z, 5151)
        if h < 0.05:
            C.put(x, FA, z, slab(ESB_SL) if h < 0.03 else slab(PUR_SL))
        elif h < 0.065:
            C.put(x, FA, z, "end_stone")
    # rubble heaps
    for (a, r) in ((60, 48), (118, 49), (100, 47), (72, 50)):
        x0, z0 = polar(r, a)
        for (x, z) in disk_pts(round(x0), round(z0), 2.6):
            if (x, z) not in FLOOR_A or abs(x) <= 2:
                continue
            hh = 2 - int(math.hypot(x - x0, z - z0))
            for y in range(FA, FA + max(0, hh) + 1):
                C.put(x, y, z, rng.choice((ESB, "end_stone", PUR, VB, OBS)))
    # a fallen planet: a copper sphere cracked open, its brass axle snapped
    px, pz = polar(48, 112)
    px, pz = round(px), round(pz)
    for x in range(px - 4, px + 5):
        for z in range(pz - 4, pz + 5):
            for y in range(FA, FA + 8):
                dd = math.sqrt((x - px) ** 2 + (y - FA - 3) ** 2 + (z - pz) ** 2)
                if dd <= 3.6 and (x, z) in FLOOR_A:
                    if dd > 2.6:
                        C.put(x, y, z, VERD if hash3(x, y, z, 5152) < 0.45 else COPPER)
                    elif hash3(x, y, z, 5153) < 0.3:
                        C.put(x, y, z, "raw_copper_block")
    line3(C, (px, FA + 3, pz), (px + 7, FA + 9, pz - 2), BRASS)
    C.bp.chest(round(polar(46, 70)[0]), FA, round(polar(46, 70)[1]), "south", loot=LOOT + "hm_breach")
    C.bp.spawner(round(polar(50, 120)[0]), FA, round(polar(50, 120)[1]), MOB_STALKER)
    edge_rails(C, FLOOR_A, FA - 1, lambda x, z: in_arc(ang(x, z), 38, 142))


def gardens(C):
    """The gravity gardens: brass planters of chorus on the deck, planters hung on chains over the void, spore
    blossoms under deck B, a brass gravity engine in the middle."""
    rng = random.Random(5160)
    for k, a in enumerate((145, 158, 172, 186, 200, 214)):
        for (rr, hgt) in ((47.5, 4), (54.5, 6)):
            x0, z0 = polar(rr, a + (6 if rr > 50 else 0))
            x0, z0 = round(x0), round(z0)
            if (x0, z0) not in FLOOR_A:
                continue
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    rim = abs(dx) + abs(dz) > 0
                    C.put(x0 + dx, FA, z0 + dz, (BRASS if (dx == 0 or dz == 0) else GEAR) if rim else "end_stone")
            chorus_tree(C.bp, x0, FA + 1, z0, rng.randint(3, hgt), rng, branches=2)
            C.set(x0, FA, z0, "end_stone")
    # hanging planters beyond the deck's outer edge and over the inner void
    for k, a in enumerate((150, 165, 180, 195, 210)):
        x0, z0 = polar(61.5, a)
        x0, z0 = round(x0), round(z0)
        yb = FA + 6 + (k % 3) * 3
        if not C.solid(x0, FB - 1, z0):
            continue
        for y in range(yb + 1, FB - 1):
            C.put(x0, y, z0, CHAIN_Y)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                C.put(x0 + dx, yb, z0 + dz, COPPER if (dx or dz) else "end_stone")
        C.put(x0, yb - 1, z0, ROD_DOWN)
        chorus_tree(C.bp, x0, yb + 1, z0, 2 + k % 3, rng, branches=1)
        C.set(x0, yb, z0, "end_stone")
    for k in range(14):
        a = 140 + 6 * k
        x, z = polar(58 + (k % 3), a)
        x, z = round(x), round(z)
        if C.solid(x, FB - 1, z) and C.free(x, FB - 2, z):
            C.put(x, FB - 2, z, "spore_blossom")
    # the gravity engine: a brass column with a floating cluster of end stone held in a ring
    gx, gz = polar(51, 180)
    gx, gz = round(gx), round(gz)
    for y in range(FA, FA + 3):
        C.put(gx, y, gz, BRASS if y < FA + 2 else GEAR)
    C.put(gx, FA + 3, gz, ROD_UP)
    ring3d(C, (gx, FA + 7, gz), 2.5, (1, 0, 0), (0, math.sin(0.4), math.cos(0.4)), GILD)
    for (dx, dy, dz) in ((0, 7, 0), (1, 8, 0), (0, 6, 1), (-1, 7, 0)):
        C.put(gx + dx, FA + dy, gz + dz, "end_stone" if dy != 7 or dx else "amethyst_block")
    x, z = polar(48, 205)
    C.bp.chest(round(x), FA, round(z), "east", loot=LOOT + "hm_gardens")
    x, z = polar(47, 162)
    C.put(round(x), FA, round(z), "water_cauldron[level=3]")
    x, z = polar(50, 192)
    C.bp.spawner(round(x), FA, round(z), MOB_ACOLYTE)


def hub(C):
    """The Meridian Hall: the waystone, a gold meridian across the floor, the pendulum, map tables, banners and
    chandeliers; the grand stair climbs along the outer wall."""
    for (x, z) in FLOOR_A:
        a = ang(x, z)
        if in_arc(a, 226, 314) and adelta(a, 270) < 0.9 * 57 / max(math.hypot(x, z), 1) and \
                C.get(x, FA - 1, z) != "minecraft:air":
            C.set(x, FA - 1, z, GOLD)
    wx, wz = polar(49, 244)
    wx, wz = round(wx), round(wz)
    C.set(wx, FA, wz, MOD["waystone"])
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        C.set(wx + dx, FA - 1, wz + dz, GOLD)
    # the pendulum, hung from deck B's underside
    px, pz = polar(54, 280)
    px, pz = round(px), round(pz)
    if C.solid(px, FB - 1, pz):
        for y in range(FA + 5, FB - 1):
            C.put(px, y, pz, CHAIN_Y)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                C.put(px + dx, FA + 4, pz + dz, GOLD if (dx == 0 and dz == 0) else ENGR)
                C.put(px + dx, FA + 3, pz + dz, BRASS if abs(dx) + abs(dz) < 2 else slab(BRASS_SLAB, "top"))
        C.put(px, FA + 2, pz, ROD_DOWN)
    # map tables with stools, lecterns, banners on the partition walls
    for a in (252, 286):
        x, z = polar(48.5, a)
        x, z = round(x), round(z)
        C.put(x, FA, z, "cartography_table")
        C.put(x + 1, FA, z, stair("dark_oak_stairs", "west"))
        C.put(x - 1, FA, z, stair("dark_oak_stairs", "east"))
    for a in (262, 300):
        x, z = polar(47, a)
        C.put(round(x), FA, round(z), "lectern[facing=south,has_book=false,powered=false]")
    x, z = polar(47.5, 296)
    C.bp.chest(round(x), FA, round(z), "south", loot=LOOT + "hm_hub")
    for a in (240, 300):
        x, z = polar(50, a)
        x, z = round(x), round(z)
        if C.solid(x, FB - 1, z):
            hang(C, x, FB - 1, z, 4, CHANDELIER)
    for a in (233, 307):
        x, z = polar(47, a)
        C.put(round(x), FA + 6, round(z), "purple_banner[rotation=0]")


def escapement(C):
    """The escapement gallery: a giant escapement wheel against the outer wall, gauges and pipes, the conical stair
    down to the crypt, the pool under deck B's drop."""
    # the escapement wheel: a toothed brass disc in the plane tangent to the wall
    a = 8.0
    cx, cz = polar(57.0, a)
    ux, uz = -math.sin(math.radians(a)), math.cos(math.radians(a))
    for i in range(-9, 10):
        for j in range(-9, 10):
            rr = math.hypot(i, j)
            if rr > 8.6:
                continue
            x, z = round(cx + ux * i), round(cz + uz * i)
            y = FA + 9 + j
            if y < FA + 1:
                continue
            if d3(x, y, z) >= RI - 0.2:
                continue
            th = math.atan2(j, i)
            if rr > 7.4:
                if (int(math.degrees(th) // 15)) % 2 == 0:
                    C.put(x, y, z, GEAR)
            elif rr > 6.0 or rr < 1.6:
                C.put(x, y, z, BRASS)
            elif abs(math.sin(3 * th)) < 0.16:
                C.put(x, y, z, ENGR)
    # the pallet fork above it
    line3(C, (round(cx), FA + 19, round(cz)), (round(cx + ux * 5), FA + 15, round(cz + uz * 5)), IRON)
    line3(C, (round(cx), FA + 19, round(cz)), (round(cx - ux * 5), FA + 15, round(cz - uz * 5)), IRON)
    for k, a2 in enumerate((322, 26)):
        x, z = polar(47, a2)
        x, z = round(x), round(z)
        C.put(x, FA, z, GAUGE if k else PIPES)
        C.put(x, FA + 1, z, PIPES)
        C.put(x, FA + 2, z, GAUGE)
    # the pool under the drop from deck B
    pool = [(x, z) for (x, z) in FLOOR_A if in_arc(ang(x, z), 36, 41) and 53.0 <= math.hypot(x, z) <= 57.4]
    for (x, z) in pool:
        C.set(x, FA - 3, z, VB)
        C.set(x, FA - 2, z, WATER)
        C.set(x, FA - 1, z, WATER)
    for (x, z) in pool:
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in pool:
                continue
            for y in (FA - 2, FA - 1):
                if not C.solid(n[0], y, n[1]):
                    C.set(n[0], y, n[1], VB)
    x, z = polar(48, 300)
    C.bp.spawner(round(x), FA, round(z), MOB_SPIDER)
    x, z = polar(46.5, 20)
    C.bp.barrel(round(x), FA, round(z), "up")


# ------------------------------------------------------------------ deck B rooms
def workshop(C):
    """The lens workshop (deck B, a 238..280): a long room between the shells, roofed at y 55 with skylights; benches
    and lathes on the outer wall, a giant lens in a brass ring, racks of glass, the ring door in the inner wall."""
    a0, a1 = 238, 280
    roof = FB + 9
    for x in range(-68, 69):
        for z in range(-68, 1):
            a = ang(x, z)
            if not in_arc(a, a0, a1):
                continue
            d = d3(x, roof, z)
            if MO < d <= RI:
                r = math.hypot(x, z)
                sky = (round(r) % 4 == 1) and (round(a) % 6 < 2)
                C.set(x, roof, z, "glass" if sky else (VB if hash01(x, z, 5170) < 0.7 else PUR))
    for aw in (a0, a1):
        radial_wall(C, aw, FB, roof - 1, door=(60.5, 3, 4), mat=VB, trim=PUR_P, band=(FB + 5,),
                    r_range=(52, 68))
    # benches along the outer wall
    kinds = ("crafting_table", "smithing_table", "grindstone[face=floor,facing=north]", "anvil[facing=east]",
             "stonecutter[facing=north]", "cartography_table", "fletching_table", "loom[facing=south]")
    k = 0
    for a in range(a0 + 3, a1 - 2, 3):
        x, z = polar(64.5, a)
        x, z = round(x), round(z)
        if (x, z) not in FLOOR_B or not C.free(x, FB, z):
            continue
        C.put(x, FB, z, kinds[k % len(kinds)])
        if k % 3 == 0:
            C.put(x, FB + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
        k += 1
    for a in range(a0 + 4, a1 - 2, 6):
        x, z = polar(66.0, a)
        x, z = round(x), round(z)
        for y in range(FB + 2, FB + 5):
            if C.free(x, y, z) and d3(x, y, z) < RI:
                C.put(x, y, z, "tinted_glass" if y == FB + 3 else GRILLE)
    # the giant lens: a glass disc in a brass ring standing across the room, on a cradle
    la = 251.0
    cx, cz = polar(60.5, la)
    ux, uz = math.cos(math.radians(la)), math.sin(math.radians(la))
    for i in range(-4, 5):
        for j in range(-4, 5):
            rr = math.hypot(i, j)
            if rr > 4.3:
                continue
            x, z = round(cx + ux * i), round(cz + uz * i)
            y = FB + 4 + j
            if y < FB + 1:
                continue
            C.put(x, y, z, BRASS if rr > 3.3 else ("light_blue_stained_glass" if rr > 1.5 else "glass"))
    for dy in (0,):
        for i in (-2, 2):
            C.put(round(cx + ux * i), FB, round(cz + uz * i), BRASS)
    # grinding lathe and a polishing wheel
    for (a, spec) in ((244, GEAR), (258, GEAR)):
        x, z = polar(57, a)
        x, z = round(x), round(z)
        C.put(x, FB, z, IRON)
        C.put(x, FB + 1, z, spec)
        C.put(x, FB + 2, z, "grindstone[face=floor,facing=north]")
    x, z = polar(56.5, 247)
    C.bp.chest(round(x), FB, round(z), "north", loot=LOOT + "hm_workshop")
    for a in (246, 262, 274):
        x, z = polar(60, a)
        x, z = round(x), round(z)
        if C.solid(x, roof, z) and C.get(x, roof, z) != "minecraft:glass":
            hang(C, x, roof, z, 2, HANG_LAMP)
    x, z = polar(63.5, 266)
    C.put(round(x), FB, round(z), TABLE)
    candle(C, round(x), FB + 1, round(z), 2)
    x, z = polar(58, 276)
    C.bp.spawner(round(x), FB, round(z), MOB_DRONE)


def star_dome(C):
    """The star-chart dome (deck B, west): a domed room 13 across, its floor a chart of the sky (void bricks, gold
    rings and starlights), the dome studded with stars, planets on chains."""
    a = 206.0
    cx, cz = polar(59.5, a)
    cx, cz = round(cx), round(cz)
    R = 6.4
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 8, cz + 9):
            dd = math.hypot(x - cx, z - cz)
            if dd > R + 0.5:
                continue
            for y in range(FB, FB + 13):
                h = y - (FB + 5)
                if h <= 0:
                    rad = R
                else:
                    rad = math.sqrt(max(0.0, R * R - (h * 1.15) ** 2))
                if dd > rad + 0.5 or d3(x, y, z) >= RI:
                    continue
                wall = dd > rad - 0.6 or (h > 0 and math.sqrt(dd * dd + (h * 1.15) ** 2) > R - 0.7)
                if wall:
                    if h <= 0:
                        spec = PUR_P if round(math.degrees(math.atan2(z - cz, x - cx))) % 45 < 8 else VB
                        if y == FB + 5:
                            spec = BRASS
                    else:
                        spec = STAR if hash3(x, y, z, 5180) < 0.12 else (GOLD if hash3(x, y, z, 5181) < 0.05 else VB)
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
            if dd <= R - 0.6:
                f = GOLD if 2.5 < dd <= 3.3 or 4.8 < dd <= 5.4 else (STAR if hash01(x, z, 5182) < 0.06 else VB)
                C.set(x, FB - 1, z, f)
    # door on the side toward the workshop (increasing azimuth), 3 wide, 3 high
    tx, tz = -math.sin(math.radians(a)), math.cos(math.radians(a))
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    for w in (-1, 0, 1):
        for t in range(5, 9):
            x, z = round(cx + tx * t + ux * w), round(cz + tz * t + uz * w)
            for y in range(FB, FB + 3):
                C.clear(x, y, z)
            if not C.solid(x, FB - 1, z):
                C.set(x, FB - 1, z, PUR)
            reg(x, z, FB)
    # planets on chains, an orrery in the middle
    C.put(cx, FB, cz, BRASS)
    C.put(cx, FB + 1, cz, GEAR)
    C.put(cx, FB + 2, cz, GOLD)
    for (dx, dz, n, spec) in ((3, 0, 4, "lapis_block"), (-2, 2, 5, "amethyst_block"), (0, -3, 3, "copper_block"),
                              (-3, -1, 6, "redstone_block")):
        top = FB + 12
        while top > FB and not C.solid(cx + dx, top, cz + dz):
            top -= 1
        if top > FB + 6:
            hang(C, cx + dx, top, cz + dz, max(1, top - FB - n), spec)
    x, z = cx + 4, cz
    C.bp.chest(cx + 3, FB, cz + 3, "north", loot=LOOT + "hm_starchart")
    C.put(cx - 4, FB, cz + 2, "lectern[facing=east,has_book=false,powered=false]")


def terrace(C):
    """Deck B's east terrace: a brass telescope aimed through the breach, benches, the girder of the drop."""
    tx, tz = polar(60, 15)
    tx, tz = round(tx), round(tz)
    for y in range(FB, FB + 3):
        C.put(tx, y, tz, BRASS if y < FB + 2 else GEAR)
    d = (0.25, 0.5, 0.83)
    n = math.sqrt(sum(c * c for c in d))
    d = tuple(c / n for c in d)
    for t in range(-3, 9):
        p = (round(tx + d[0] * t), round(FB + 3 + d[1] * t), round(tz + d[2] * t))
        if C.free(*p):
            C.put(*p, GOLD if t in (0, 8) else BRASS)
    for a in (352, 4):
        x, z = polar(63.5, a)
        C.put(round(x), FB, round(z), stair("dark_oak_stairs", "west"))
    # the drop: a girder over the pool, the railing open at its end
    for (x, z) in sorted(FLOOR_B):
        a = ang(x, z)
        if in_arc(a, 31, 36) and 53.5 <= math.hypot(x, z) <= 57.5:
            C.set(x, FB - 1, z, TREAD)
    for t in range(0, 6):
        for w in (0, 1):
            x, z = polar(55 + w, 33 + t * 1.1)
            x, z = round(x), round(z)
            if (x, z) not in FLOOR_B and not C.solid(x, FB - 1, z):
                C.set(x, FB - 1, z, slab(IRON_SLAB, "top"))
                FLOOR_B.add((x, z))
                reg(x, z, FB - 0.5)


# ------------------------------------------------------------------ the bottom: crypt, sump, lift
def crypt(C):
    """The gear crypt between the shells' floors (feet 9): sarcophagi of dead automata under the low curve of the
    middle shell, giant gears lying in state, soul lanterns; walled off at a 250 and 60."""
    yf = FC - 1
    floor = set()
    for x in range(-45, 46):
        for z in range(-45, 46):
            a = ang(x, z)
            if not in_arc(a, 250, 420):
                continue
            d = d3(x, yf, z)
            if not (MO < d < RI):
                continue
            r = math.hypot(x, z)
            spec = TREAD if 34.5 <= r < 36.5 else ("polished_blackstone_bricks" if hash01(x, z, 5190) < 0.8
                                                   else "cracked_polished_blackstone_bricks")
            C.set(x, yf, z, spec)
            floor.add((x, z))
            reg(x, z, FC)
    for aw in (250, 60):
        radial_wall(C, aw, FC, FA - 2, mat="polished_blackstone_bricks", trim="chiseled_polished_blackstone",
                    r_range=(16, 68))
    # tombs under the low ceiling: an iron sarcophagus with a skull, two candles
    for k in range(16):
        a = 254 + 10.5 * k
        if in_arc(a, 312, 328):
            continue                               # the sump tunnel
        x, z = polar(29.5, a)
        x, z = round(x), round(z)
        if (x, z) not in floor or not C.free(x, FC, z) or not C.free(x, FC + 1, z):
            continue
        C.put(x, FC, z, IRON)
        C.put(x, FC + 1, z, "skeleton_skull[rotation=0]" if k % 3 else "wither_skeleton_skull[rotation=4]")
        x2, z2 = polar(28.3, a + 2.5)
        x2, z2 = round(x2), round(z2)
        if C.free(x2, FC, z2) and (x2, z2) in floor:
            candle(C, x2, FC, z2, 1 + k % 3)
    # giant gears lying in state (flat toothed discs on low biers)
    for (a, r, gr) in ((285, 38.5, 3.6), (345, 37.5, 3.2), (40, 38, 3.0)):
        gx, gz = polar(r, a)
        for (x, z) in disk_pts(round(gx), round(gz), gr + 1.0):
            if (x, z) not in floor:
                continue
            dd = math.hypot(x - gx, z - gz)
            th = math.degrees(math.atan2(z - gz, x - gx))
            if dd > gr:
                if int(th // 20) % 2 == 0:
                    C.put(x, FC, z, GEAR)
            elif dd > 1.2:
                C.put(x, FC, z, BRASS if hash01(x, z, 5191) < 0.8 else VERD)
            else:
                C.put(x, FC, z, IRON)
                C.put(x, FC + 1, z, ROD_UP)
    for k in range(12):
        a = 255 + 14 * k
        x, z = polar(41.0, a)
        x, z = round(x), round(z)
        top = FC + 4
        while top < FC + 20 and not C.solid(x, top, z):
            top += 1
        if C.solid(x, top, z) and top - FC >= 6:
            hang(C, x, top, z, top - FC - 5, SOUL_H)
        elif (x, z) in floor and C.free(x, FC, z):
            C.put(x, FC, z, SOUL)
    x, z = polar(36, 300)
    C.bp.chest(round(x), FC, round(z), "east", loot=LOOT + "hm_crypt")
    x, z = polar(37, 10)
    C.bp.chest(round(x), FC, round(z), "west", loot=LOOT + "hm_crypt")
    x, z = polar(36, 20)
    C.bp.spawner(round(x), FC, round(z), MOB_SPIDER)
    x, z = polar(37, 275)
    C.bp.spawner(round(x), FC, round(z), MOB_SENTINEL)
    return floor


def sump(C):
    """The sump at the bottom of the middle shell: a flat floor, the pool under the levitation shaft, the pillar's
    foot among broken cogs; a tunnel through the shell to the crypt."""
    yf = FC - 1
    for (x, z) in disk_pts(0, 0, 12.4):
        for y in (yf - 1, yf):
            if not C.solid(x, y, z) or y == yf:
                C.set(x, y, z, "polished_blackstone_bricks" if y == yf and hash01(x, z, 5200) < 0.85 else VB)
        reg(x, z, FC)
    # the pool (2 deep) under the shaft
    sx, sz = SHAFT
    for x in range(sx - 2, sx + 3):
        for z in range(sz - 2, sz + 3):
            C.set(x, yf - 2, z, VB)
            C.set(x, yf - 1, z, WATER)
            C.set(x, yf, z, WATER)
    # the tunnel at a 320 through the shell (3 wide, 3 high) to the crypt floor
    for (x, z, t, p) in radial_box(ALPHA_G, 11.0, 31.0, 1.5):
        C.set(x, yf, z, "polished_blackstone_bricks" if abs(p) > 0.6 else TREAD)
        reg(x, z, FC)
        for y in range(FC, FC + 3):
            C.clear(x, y, z)
        if C.free(x, FC + 3, z):
            C.set(x, FC + 3, z, VB)
    for (x, z, t, p) in radial_box(ALPHA_G, 11.0, 31.0, 2.6):
        if abs(p) > 1.5:
            for y in range(FC, FC + 4):
                if C.free(x, y, z) and (x, y, z) not in C.keep and d3(x, y, z) > MI - 1.5:
                    C.set(x, y, z, "polished_blackstone_bricks")
    # broken cogs and lamps
    for (x, z, n) in ((-6, 5, 2), (5, 6, 3), (-8, -3, 2)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            C.put(x + dx, FC, z + dz, GEAR if (dx or dz) else IRON)
        C.put(x, FC + 1, z, LANT)
    C.put(-3, FC, -6, LANT)
    C.put(7, FC, -2, LANT)


def pillar_and_platform(C):
    """The core platform (r 17, feet 50) on its drum and cone, the pillar down to the sump; the arena floor, the rim
    rail; the glowing core above with its armillary rings."""
    yf = FP - 1
    for (x, z) in disk_pts(0, 0, PR):
        d = math.hypot(x, z)
        a = ang(x, z)
        if d <= 2.6:
            spec = GOLD if d > 1.4 else STAR
        elif 6.6 < d <= 7.4 or 11.6 < d <= 12.4:
            spec = GOLD if round(a) % 30 < 6 else BRASS
        elif (round(a) % 30) < 2:
            spec = PUR
        elif d > PR - 1.0:
            spec = ENGR
        else:
            spec = VB if (int(d) % 2) else ESB
        C.set(x, yf, z, spec)
        C.set(x, yf - 1, z, VB)
        reg(x, z, FP)
    # the drum: a wall ring and a bottom plate; the cone; the pillar
    for (x, z) in disk_pts(0, 0, PR):
        d = math.hypot(x, z)
        C.set(x, 39, z, VB if d < PR - 1.5 else BRASS)
        if d > PR - 1.6:
            for y in range(40, yf - 1):
                C.set(x, y, z, BRASS if y in (40, 44) else (GEAR if (round(ang(x, z)) % 20 < 4) else IRON))
    for y in range(30, 39):
        rr = 4 + (y - 30) * 13.0 / 9.0
        for (x, z) in disk_pts(0, 0, rr):
            if math.hypot(x, z) > rr - 1.6:
                C.set(x, y, z, VB if (y % 3) else BRASS)
    for y in range(FC, 30):
        for (x, z) in disk_pts(0, 0, 3.0):
            d = math.hypot(x, z)
            C.set(x, y, z, (BRASS if (y % 6 == 0) else (PUR_P if d > 2.4 else VB)))
    # the core: sea lanterns veined with crying obsidian, two armillary rings, rods
    cx, cy, cz = CORE
    for x in range(cx - 5, cx + 6):
        for y in range(cy - 5, cy + 6):
            for z in range(cz - 5, cz + 6):
                dd = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                if dd <= 4.3:
                    h = hash3(x, y, z, 5210)
                    C.set(x, y, z, SEA if h < 0.55 else (CRY if h < 0.8 else (STAR if h < 0.92 else "amethyst_block")))
    ring3d(C, (cx, cy, cz), 6.5, (1, 0, 0), (0, math.sin(math.radians(25)), math.cos(math.radians(25))), GOLD)
    ring3d(C, (cx, cy + 1, cz), 8.0, (0, 0, 1), (math.cos(math.radians(-30)), math.sin(math.radians(-30)), 0), BRASS)
    for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
        for t in range(5, 9):
            p = (cx + dx * t, cy + dy * t, cz + dz * t)
            if C.free(*p):
                fac = {(1, 0, 0): "east", (-1, 0, 0): "west", (0, 0, 1): "south", (0, 0, -1): "north",
                       (0, 1, 0): "up"}[(dx, dy, dz)]
                C.put(*p, f"end_rod[facing={fac}]")


def arena_dress(C):
    """The arena's rim: a brass railing with starlight posts, the bridge mouth and the reliquary kiosk open; the boss
    seal at the centre."""
    k = 0
    for (x, z) in disk_pts(0, 0, PR):
        d = math.hypot(x, z)
        if d <= PR - 0.6:
            continue
        a = ang(x, z)
        if adelta(a, ALPHA_G) * math.pi / 180 * PR < 2.6:
            continue
        if -3 <= x <= 3 and z <= -14:
            continue
        k += 1
        if k % 9 == 0:
            C.set(x, FP, z, PUR_P)
            C.set(x, FP + 1, z, STAR)
            C.set(x, FP + 2, z, ROD_UP)
        else:
            railing(C, x, FP, z, out_facing(x, z))
    for a in (45, 135, 225):
        x, z = polar(PR - 3.5, a)
        x, z = round(x), round(z)
        C.set(x, FP, z, VB)
        C.set(x, FP + 1, z, STAR)
        C.set(x, FP + 2, z, "amethyst_cluster[facing=up,waterlogged=false]")
    C.bp.boss_seal(0, FP - 1, 0, BOSS, PR - 2)


def reliquary(C):
    """The core reliquary: a pod hung under the platform's north rim, reached from the kiosk on the rim (sealed bars
    toward the arena, a ladder down); chests, gold, the heart-shards on a pedestal; the levitation shaft's iron trapdoor
    in its floor (a lever beside it)."""
    x0, z0, x1, z1 = REL
    f = F_REL
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(f - 1, f + 7):
                wall = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1) or y in (f - 1, f + 6)
                if wall:
                    if y == f - 1:
                        spec = GOLD if (x + z) % 5 == 0 else "polished_blackstone_bricks"
                    elif y == f + 6:
                        spec = VB
                    else:
                        spec = BRASS if y == f + 3 else VB
                    C.set(x, y, z, spec)
                else:
                    C.clear(x, y, z)
    # the pod's keel under the part outside the drum
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, -15):
            depth = 2 + int(3 * (1 - abs(x) / 8.0))
            for y in range(f - 1 - depth, f - 1):
                C.put(x, y, z, BRASS if y == f - 2 else IRON)
    # the kiosk on the rim
    for x in range(-2, 3):
        for z in range(-21, -14):
            for y in range(FP - 1, FP + 5):
                wall = x in (-2, 2) or z in (-21, -15) or y in (FP - 1, FP + 4)
                if wall:
                    C.set(x, y, z, ENGR if y == FP + 4 else (BRASS if (x in (-2, 2) and z in (-21, -15)) else VB))
                else:
                    C.clear(x, y, z)
                    reg(x, z, FP)
    for x in range(-1, 2):
        for y in range(FP, FP + 3):
            C.set(x, y, -15, MOD["vault_bars"])
    C.set(0, FP + 3, -15, GOLD)
    C.set(-1, FP + 3, -15, ENGR)
    C.set(1, FP + 3, -15, ENGR)
    # the ladder (kiosk -> pod), against the pod's north wall
    for y in range(f, FP):
        C.set(0, y, z0, "ladder[facing=south,waterlogged=false]")
    C.set(0, FP - 1, z0 - 1, VB)
    C.set(0, FP - 2, z0 - 1, VB)
    for y in (FP - 2, FP - 1):
        for dx in (-1, 1):
            C.set(dx, y, z0, VB)
    C.set(0, FP + 3, -20, SOUL_H.replace("hanging=true", "hanging=true"))
    # contents
    C.bp.chest(x0 + 1, f, z1, "north", loot=LOOT + "hm_reliquary")
    C.bp.chest(x1 - 1, f, z1, "north", loot=LOOT + "hm_reliquary")
    for (x, z) in ((x0, z0 + 2), (x1, z0 + 2), (x0, z1 - 2), (x1, z1 - 2)):
        C.put(x, f, z, GOLD if (x + z) % 2 else "raw_gold_block")
    C.put(x0 + 3, f, z0 + 4, BRASS)
    C.put(x0 + 3, f + 1, z0 + 4, CRY)
    C.put(x0 + 3, f + 2, z0 + 4, SEA)
    C.put(x0 + 3, f + 3, z0 + 4, "amethyst_cluster[facing=up,waterlogged=false]")
    for x in (x0 + 1, x1 - 1):
        hang(C, x, f + 6, z0 + 5, 1, SOUL_H)
    hang(C, 0, f + 6, -13, 2, CHANDELIER)
    # the levitation shaft: iron trapdoor in the floor, a lever on the floor beside it
    sx, sz = SHAFT
    C.set(sx, f - 1, sz, "iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    lever(C, sx + 1, f, sz, "east", face="floor")
    return


def shaft(C):
    """The levitation shaft: a glass-and-brass tube of still water from the reliquary floor down to the sump pool."""
    sx, sz = SHAFT
    top = F_REL - 2
    for y in range(FC, top + 1):
        C.set(sx, y, sz, WATER)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                corner = dx != 0 and dz != 0
                C.set(sx + dx, y, sz + dz, (BRASS if y % 6 else GEAR) if corner else ("glass" if y % 6 else BRASS))


def lift(C):
    """The bubble lift (crypt -> Meridian Hall): a bubble column in a brass tube against the outer wall; signs hold the
    water at its foot, the booth's iron door opens from inside (a lever by the tube)."""
    lx, lz = LIFT
    yb = FC - 1
    C.set(lx, yb, lz, "soul_sand")
    for y in range(FC, FA):
        C.set(lx, y, lz, "bubble_column[drag=false]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                x, z = lx + dx, lz + dz
                if (dx, dz) == (0, 1) and y in (FC, FC + 1):
                    continue
                corner = dx != 0 and dz != 0
                C.set(x, y, z, (BRASS if y % 6 else GEAR) if corner else ("glass" if y % 6 else BRASS))
    C.set(lx, FC, lz + 1, "spruce_sign[rotation=8,waterlogged=false]")
    C.set(lx, FC + 1, lz + 1, "spruce_wall_sign[facing=south,waterlogged=false]")
    C.set(lx, FC + 2, lz + 1, BRASS)
    reg(lx, lz + 1, FC)
    # the booth on the hall floor: the column's top is level with the floor; step off north, iron door further north
    for x in range(lx - 1, lx + 2):
        for z in range(lz - 3, lz + 2):
            for y in range(FA, FA + 4):
                wall = x in (lx - 1, lx + 1) or z in (lz - 3, lz + 1) or y == FA + 3
                if wall:
                    C.set(x, y, z, ("glass" if (y in (FA + 1, FA + 2) and z in (lz - 2, lz - 1) and x != lx) else BRASS))
                else:
                    C.clear(x, y, z)
            if (x, z) != (lx, lz):
                C.set(x, FA - 1, z, BRASS)
    C.set(lx, FA - 1, lz, "bubble_column[drag=false]")
    iron_door(C, lx, FA, lz - 3, "north")
    lever(C, lx, FA + 1, lz - 2, "west")
    C.set(lx, FA + 3, lz - 1, GAUGE)
    reg(lx, lz - 1, FA)
    reg(lx, lz - 2, FA)


# ------------------------------------------------------------------ the rings
def ring(C, n, style, openings=()):
    """A flat band (5 wide) in a plane tilted through the centre: deck, an underside, gear teeth on the outer edge,
    brass railings on both edges (with lantern posts) except at the openings [(a, edge 'in'/'out', half width)]."""
    r, A, B = RINGS[n]
    cells = {}
    R = r + 4
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            d = math.hypot(x, z)
            if r - 2.5 < d <= r + 2.5:
                cells[(x, z)] = q2(CY + A * x + B * z)
    for (x, z), s in cells.items():
        reg(x, z, s)
    k = 0
    for (x, z), s in sorted(cells.items(), key=lambda kv: ang(kv[0][0], kv[0][1])):
        d = math.hypot(x, z)
        a = ang(x, z)
        edge = "out" if d > r + 1.5 else ("in" if d <= r - 1.5 else None)
        full, half, under, uslab = style_mats(style, edge is None and abs(d - r) < 0.5)
        y = surface(C, x, z, s, full, half, under)
        for c in range(1, 4):
            C.keep.add((x, y + c, z))
        if C.free(x, y - 1, z):
            C.set(x, y - 1, z, under)
        if edge == "out" and round(a * r / 57.3) % 3 == 0:
            C.put(x, y - 2, z, GEAR)
        if edge:
            opened = any(e == edge and adelta(a, oa) * math.pi / 180 * d <= hwid for (oa, e, hwid) in openings)
            if opened:
                continue
            top = math.ceil(s - 0.01)
            if not rail_ok(x, z, s + 0.0) and len(WALK.get((x, z), ())) > 1:
                continue
            C.set(x, top - 1, z, under)
            k += 1
            if k % 23 == 0:
                C.set(x, top, z, BRASS)
                C.set(x, top + 1, z, LANT)
            else:
                railing(C, x, top, z, out_facing(x, z) if edge == "out" else out_facing(-x, -z))
    return cells


def ring_s(n, x, z):
    r, A, B = RINGS[n]
    return CY + A * x + B * z


def ring_point(n, rr, a):
    x, z = polar(rr, a)
    return (x, ring_s(n, x, z), z)


def alpha_23():
    """Azimuth where ring 2's inner edge and ring 3's outer edge are level (between 185 and 225)."""
    best = None
    for k in range(185 * 4, 225 * 4):
        a = k / 4.0
        x2, z2 = polar(33.0, a)
        x3, z3 = polar(28.0, a)
        diff = abs(ring_s(2, x2, z2) - ring_s(3, x3, z3))
        if best is None or diff < best[0]:
            best = (diff, a)
    return best[1]


def gimbal_station(C):
    """The gimbal station on the bridge between rings 1 and 2 (a 0): a pad round the bridge with a waystone (half-way
    between the Meridian Hall and the grace), a brazier and a gauge post."""
    pad = [(x, z) for x in range(37, 44) for z in range(-3, 4) if 38.4 <= math.hypot(x, z) <= 42.6]
    for (x, z) in pad:
        reg(x, z, CY)
    for (x, z) in pad:
        C.set(x, CY - 1, z, BRASS if abs(z) <= 1 else TREAD)
        for c in range(0, 3):
            C.clear_if(x, CY + c, z)
        if C.free(x, CY - 2, z):
            C.set(x, CY - 2, z, slab(BRASS_SLAB, "top"))
    for (x, z) in pad:
        for (dx, dz) in ((0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n not in pad and n not in WALK:
                rail_at(C, n[0], n[1], CY, out_facing(dx, dz))
    C.set(40, CY, 3, MOD["waystone"])
    C.set(40, CY - 1, 4, BRASS)
    C.set(40, CY, -3, BRASS)
    C.set(40, CY + 1, -3, GAUGE)
    C.set(40, CY + 2, -3, LANT)


def rings_and_links(C):
    a23 = alpha_23()
    hw = 2.2
    ring(C, 1, "copper", openings=((270, "out", hw), (0, "in", hw), (333.8, "in", hw)))
    ring(C, 2, "brass", openings=((0, "out", hw), (a23, "in", hw)))
    ring(C, 3, "void", openings=((a23, "out", hw), (ALPHA_G, "in", 3.0), (ALPHA_G, "out", 6.0)))
    # deck B (ring door) -> ring 1's low point
    walkway(C, [(0, FB, -54.5), (0, FB, -51), (0, q2(ring_s(1, 0, -46.5)), -46.5)], width=3, style="copper")
    # ring 1 -> ring 2 at a 0, ring 2 -> ring 3 at a23
    walkway(C, [ring_point(1, 43.6, 0), ring_point(2, 36.4, 0)], width=3, style="brass")
    p2, p3 = ring_point(2, 33.6, a23), ring_point(3, 28.4, a23)
    walkway(C, [p2, p3], width=3, style="brass")
    gimbal_station(C)
    # gimbal pins: rings 1 and 2 on the x axis (to the middle shell and to ring 1), ring 3 on ring 2
    for side in (1, -1):
        for (r0, r1) in ((47.5, 53.8), (37.5, 42.5)):
            for t in range(int(r0), int(r1) + 1):
                for (dy, dz) in ((0, 0), (-1, 0), (0, -1), (0, 1), (-1, 1), (-1, -1)):
                    p = (side * t, CY - 2 + dy, dz)
                    if C.free(*p) and p not in C.keep:
                        C.set(*p, GEAR if t in (int(r0), int(r1)) else BRASS)
    for a in (50, 230):
        x3, z3 = polar(28.5, a)
        x2, z2 = polar(32.5, a)
        line3(C, (round(x3), round(ring_s(3, x3, z3)) - 2, round(z3)), (round(x2), round(ring_s(2, x2, z2)) - 2,
                                                                         round(z2)), ENGR)
    # chests on the rings
    for (n, a) in ((1, 300), (2, 110), (3, 260)):
        r = RINGS[n][0]
        x, z = polar(r + 1, a)
        x, z = round(x), round(z)
        s = q2(ring_s(n, x, z))
        y = math.floor(s) if s - math.floor(s) > 0.25 else math.floor(s) - 1
        C.bp.chest(x, y + 1, z, out_facing(-x, -z), loot=LOOT + "hm_rings")
    x, z = polar(35, 250)
    C.bp.spawner(round(x), math.ceil(ring_s(2, round(x), round(z))), round(z), MOB_ACOLYTE)
    return a23


def grace_and_bridge(C):
    """The site of grace: a pad on ring 3's low point (waystone, braziers); the narrow bridge (compression, brass
    arches) to the platform with the mist at its mouth; the spoke east to ring 1 behind the one-way iron door."""
    pad = {}
    for x in range(10, 32):
        for z in range(-28, -6):
            d = math.hypot(x, z)
            a = ang(x, z)
            if 22.6 <= d <= 30.6 and adelta(a, ALPHA_G) <= 9.5:
                pad[(x, z)] = F_GRACE
    for (x, z) in pad:
        reg(x, z, F_GRACE)
    for (x, z), s in pad.items():
        d = math.hypot(x, z)
        y = surface(C, x, z, s, VB, VB_SL, VB)
        for c in range(1, 4):
            C.clear_if(x, y + c, z)
        C.set(x, y - 1, z, IRON)
        if 25.6 < d <= 26.4:
            C.set(x, y, z, GOLD) if s == math.floor(s) else None
    # rails round the pad (ring 3 cells and the bridges stay open)
    for (x, z), s in pad.items():
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, z + dz)
            if n in pad or n in WALK:
                continue
            rail_at(C, n[0], n[1], s, out_facing(dx, dz), under=VB_SL)
    gx, gz = polar(29.3, ALPHA_G + 5)
    C.set(round(gx), math.ceil(F_GRACE), round(gz), MOD["waystone"])
    for da in (-7, 7):
        bx, bz = polar(23.8, ALPHA_G + da)
        bx, bz = round(bx), round(bz)
        C.set(bx, math.ceil(F_GRACE), bz, VB)
        C.set(bx, math.ceil(F_GRACE) + 1, bz, STAR)
        C.set(bx, math.ceil(F_GRACE) + 2, bz, "amethyst_cluster[facing=up,waterlogged=false]")
    # the bridge to the platform
    a = ALPHA_G
    pts = [ring_point(3, 23.2, a), (polar(PR - 0.5, a)[0], FP, polar(PR - 0.5, a)[1])]
    pts[0] = (pts[0][0], F_GRACE, pts[0][2])
    br = walkway(C, pts, width=3, style="void", lamp_every=0)
    # brass arches over it (the compression: 5 high), the mist at the mouth
    for (x, z), s in br.items():
        d = math.hypot(x, z)
        if PR + 0.2 <= d <= PR + 1.2:
            top = math.floor(s)
            for y in range(top, top + 4):
                C.clear(x, y, z)
                C.set(x, y, z, MIST)
    ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
    px, pz = -uz, ux
    for t in (19.0, 21.0):
        cx, cz = t * ux, t * uz
        s = F_GRACE + (FP - F_GRACE) * (23.2 - t) / (23.2 - PR + 0.5)
        base = math.floor(q2(s))
        for w in (-2, 2):
            x, z = round(cx + px * w), round(cz + pz * w)
            for y in range(base - 1, base + 5):
                C.put(x, y, z, BRASS if y < base + 4 else GOLD)
        for w in range(-2, 3):
            x, z = round(cx + px * w), round(cz + pz * w)
            C.put(x, base + 5, z, ENGR)
    # the spoke east along z = -19 to ring 1, the iron door at x 26 (lever on the grace side)
    s1 = ring_s(1, 38.6, -19)
    walkway(C, [(23.5, F_GRACE, -19), (26.5, F_GRACE, -19), (39.5, q2(s1), -19)], width=3, style="void")
    fy = math.ceil(F_GRACE)
    for z in (-20, -18):
        for y in (fy, fy + 1):
            C.set(26, y, z, BRASS)
        C.set(26, fy + 2, z, ENGR)
    C.set(26, fy + 2, -19, ENGR)
    iron_door(C, 26, fy, -19, "east")
    lever(C, 25, fy + 1, -18, "west")
    return pad


# ------------------------------------------------------------------ cuts through the shells
def ring_door(C):
    """The ring door: a 3 x 4 passage through the middle shell from the workshop (deck B, a 270) onto the bridge to
    ring 1, framed in gold."""
    for x in range(-1, 2):
        for z in range(-55, -49):
            C.set(x, FB - 1, z, TREAD if x == 0 else BRASS)
            reg(x, z, FB)
            for y in range(FB, FB + 4):
                C.clear(x, y, z)
    for x in (-2, 2):
        for y in range(FB, FB + 4):
            for z in (-54, -53, -52):
                if d3(x, y, z) > MI - 0.5:
                    C.set(x, y, z, PUR_P)
    for x in range(-2, 3):
        for z in (-54, -53, -52):
            C.set(x, FB + 4, z, GOLD if x == 0 else ENGR)


# ------------------------------------------------------------------ outside: camp, bridge, tower, wreckage, chains
def camp(C):
    """The stranded astronomers' camp on a shard south of the moon: tents, a fire, a brass telescope on a tripod aimed
    at the breach, crates, a chest and the first waystone."""
    cx, cz = CAMP
    cols = rock_lobe(cx, F_CAMP - 1, cz, 14, 11, 13, 5220, spikes=4)
    build_rock(C.bp, cols, 5221, surface="end_stone")
    for (x, z), (b, t) in cols.items():
        reg(x, z, t + 1)
    top = F_CAMP - 1
    # paving round the fire, the waystone by the bridge head
    for (x, z) in disk_pts(cx, cz, 4.4):
        if (x, z) in cols and cols[(x, z)][1] == top:
            C.set(x, top, z, ESB if hash01(x, z, 5222) < 0.7 else PUR)
    C.set(cx, F_CAMP, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    C.set(cx - 3, F_CAMP, cz - 6, MOD["waystone"])
    # two tents (white wool A-frames)
    for (tx, tz) in ((cx - 7, cz + 2), (cx + 6, cz + 3)):
        for dz in range(-2, 3):
            for h in range(0, 3):
                for sgn in (-1, 1):
                    x = tx + sgn * (2 - h)
                    if (x, tz + dz) in cols:
                        C.set(x, F_CAMP + h, tz + dz, "white_wool" if dz != 2 or h == 2 else "white_wool")
            C.set(tx, F_CAMP + 2, tz + dz, "white_wool")
        for dz in range(-1, 2):
            C.set(tx, F_CAMP, tz + dz, "light_blue_carpet")
        for h in range(0, 2):
            C.clear(tx, F_CAMP + h, tz + 2)
    # the telescope
    tx, tz = cx + 2, cz - 5
    C.set(tx, F_CAMP, tz, "spruce_fence")
    C.set(tx, F_CAMP + 1, tz, BRASS)
    for t in range(0, 5):
        C.set(tx, F_CAMP + 2 + (t * 2) // 3, tz - t, GOLD if t == 4 else BRASS)
    # supplies
    C.bp.barrel(cx + 4, F_CAMP, cz - 1, "up")
    C.bp.barrel(cx + 4, F_CAMP + 1, cz - 1, "up")
    C.set(cx + 3, F_CAMP, cz - 2, "crafting_table")
    C.bp.chest(cx - 4, F_CAMP, cz - 2, "east", loot=LOOT + "hm_camp")
    C.set(cx - 4, F_CAMP, cz - 1, "lectern[facing=east,has_book=false,powered=false]")
    for (x, z) in ((cx - 2, cz - 7), (cx + 3, cz - 7), (cx, cz + 6)):
        C.set(x, F_CAMP, z, "spruce_fence")
        C.set(x, F_CAMP + 1, z, LANT)
    return cols


BRIDGE = {}


def bridge_and_tower(C):
    """The bridge from the camp north into the breach (brass deck, iron truss), and the stair tower down to the crater
    on the island's spit."""
    cx, cz = CAMP
    pts = [(0, F_CAMP, cz - 9.5), (0, FA - 0.5, 60), (0, FA, 52)]
    BRIDGE.update(walkway(C, pts, width=3, style="brass", lamp_every=7))
    # a truss under it
    for (x, z), s in BRIDGE.items():
        if abs(x) == 1 and z % 2 == 0:
            y = math.floor(s) - 2
            if C.free(x, y, z):
                C.put(x, y, z, "iron_bars")
    # the stair tower: a helix round a brass mast, from the spit up to the bridge
    tx, tz = TOWER
    s_top = q2(BRIDGE.get((-1, tz), FA - 1))
    base = 2
    for (x, z) in disk_pts(tx, tz, 5.0):
        C.set(x, base - 1, z, ESB)
        for y in range(base - 4, base - 1):
            C.put(x, y, z, "end_stone")
    for y in range(base, int(s_top) + 4):
        C.set(tx, y, tz, BRASS if y % 4 else GEAR)
    rise = s_top - base
    turns = rise / 9.0
    segs = []
    a0 = 0.0
    s0 = float(base)
    # climb with a landing every <= 10 of rise; end facing east toward the bridge
    total_deg = turns * 360.0
    n_land = int(rise // 10)
    per = (total_deg - 30 * n_land) / (n_land + 1)
    dr = rise / (n_land + 1)
    for i in range(n_land + 1):
        segs.append((a0, a0 + per, s0, s0 + dr))
        a0 += per
        s0 += dr
        if i < n_land:
            segs.append((a0, a0 + 30, s0, s0))
            a0 += 30
    # rotate so that the top lands at a 0 (east)
    shift = (360.0 - (a0 % 360.0)) % 360.0
    segs = [(p0 + shift, p1 + shift, q0, q1) for (p0, p1, q0, q1) in segs]
    # split into single turns so in_arc never wraps more than once
    flat = []
    for (p0, p1, q0, q1) in segs:
        while p1 - p0 > 300:
            mid = p0 + 300
            qm = q0 + (q1 - q0) * 300 / (p1 - p0)
            flat.append((p0, mid, q0, qm))
            p0, q0 = mid, qm
        flat.append((p0, p1, q0, q1))
    # a helix of several turns: build each turn separately (same angle range, different heights)
    for i in range(len(flat)):
        spiral(C, [flat[i]], 3.0, 3.0, PUR, PUR_SL, VB, base=base, cx=tx, cz=tz, rmax=5, head=4)
    # the landing toward the bridge
    walkway(C, [(tx + 4.5, s_top, tz), (-1.5, s_top, tz)], width=3, style="brass", rails=False)
    for k in range(8):
        a = 22.5 + 45 * k
        x, z = polar(5.6, a)
        x, z = round(tx + x), round(tz + z)
        for y in range(base, int(s_top) + 3):
            if C.free(x, y, z):
                C.put(x, y, z, PUR_P if y % 8 else BRASS)


def wreckage(C, cols):
    """The crater rim's brass wreckage: torn plates stuck in the ground, half-buried gears, bent pipes."""
    rng = random.Random(5230)
    for k in range(26):
        a = rng.uniform(0, 360)
        if adelta(a, 90) < 10:
            continue
        r = rng.uniform(40, 55)
        x0, z0 = polar(r, a)
        x0, z0 = round(x0), round(z0)
        if (x0, z0) not in cols:
            continue
        t = cols[(x0, z0)][1]
        kind = k % 3
        if kind == 0:                                    # a tilted plate
            w, h = rng.randint(3, 5), rng.randint(3, 6)
            ux, uz = math.cos(math.radians(a + 90)), math.sin(math.radians(a + 90))
            lean = rng.uniform(0.2, 0.7)
            for i in range(-w, w + 1):
                for j in range(h):
                    x = round(x0 + ux * i + math.cos(math.radians(a)) * j * lean)
                    z = round(z0 + uz * i + math.sin(math.radians(a)) * j * lean)
                    C.put(x, t + 1 + j - 1, z, rng.choice((BRASS, BRASS, VERD, COPPER, TARN)))
        elif kind == 1:                                  # a half-buried gear
            gr = rng.uniform(2.5, 4.5)
            ux, uz = math.cos(math.radians(a + 90)), math.sin(math.radians(a + 90))
            for i in range(-6, 7):
                for j in range(-6, 7):
                    rr = math.hypot(i, j)
                    if rr > gr + 1:
                        continue
                    y = t + j
                    if y < t:
                        continue
                    x, z = round(x0 + ux * i), round(z0 + uz * i)
                    th = math.degrees(math.atan2(j, i))
                    if rr > gr:
                        if int(th // 22) % 2 == 0:
                            C.put(x, y, z, GEAR)
                    elif rr > 1.0:
                        C.put(x, y, z, BRASS if hash3(x, y, z, 5231) < 0.75 else VERD)
                    else:
                        C.put(x, y, z, IRON)
        else:                                            # bent pipes
            p0 = (x0, t + 1, z0)
            p1 = (x0 + rng.randint(-4, 4), t + rng.randint(2, 5), z0 + rng.randint(-4, 4))
            p2 = (p1[0] + rng.randint(-3, 3), t + 1, p1[2] + rng.randint(-3, 3))
            line3(C, p0, p1, PIPES)
            line3(C, p1, p2, PIPES)


def big_chain(C, p0, p1):
    """A giant chain from p0 to p1: links 3 x 5 alternating in two perpendicular planes."""
    v = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in v))
    u = [c / L for c in v]
    ref = (0, 1, 0) if abs(u[1]) < 0.9 else (1, 0, 0)
    a = [u[1] * ref[2] - u[2] * ref[1], u[2] * ref[0] - u[0] * ref[2], u[0] * ref[1] - u[1] * ref[0]]
    n = math.sqrt(sum(c * c for c in a))
    a = [c / n for c in a]
    b = [u[1] * a[2] - u[2] * a[1], u[2] * a[0] - u[0] * a[2], u[0] * a[1] - u[1] * a[0]]
    t = 0.0
    k = 0
    while t < L:
        side = a if k % 2 == 0 else b
        c = [p0[i] + u[i] * (t + 2.0) for i in range(3)]
        for j in range(40):
            th = 2 * math.pi * j / 40
            p = [c[i] + u[i] * 2.4 * math.cos(th) + side[i] * 1.2 * math.sin(th) for i in range(3)]
            q = (round(p[0]), round(p[1]), round(p[2]))
            if C.free(*q):
                C.put(*q, IRON if k % 2 else "iron_block")
        t += 3.6
        k += 1


def chains(C, cols):
    """Four giant chains from the brass belt down to bollards on the island."""
    for a in (15, 165, 225, 315):
        x0, z0 = polar(RO + 1.5, a)
        x1, z1 = polar(60, a)
        x1, z1 = round(x1), round(z1)
        t = cols.get((x1, z1), (0, 0))[1]
        # the bollard
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(t + 1, t + 4):
                    C.put(x1 + dx, y, z1 + dz, IRON if y < t + 3 else BRASS)
        C.put(x1, t + 4, z1, GEAR)
        # the eye on the belt
        ex, ez = round(x0), round(z0)
        for dy in (-1, 0, 1):
            C.put(ex, CY + dy, ez, GEAR)
        big_chain(C, (x0, CY - 1, z0), (x1, t + 4, z1))


def debris(C):
    """Debris arcs frozen in flight out of the breach and a few large floating shards round the moon."""
    rng = random.Random(5240)
    for (az, el, spread) in ((65, 35, 1.0), (95, 48, 1.2), (122, 30, 1.0), (80, 12, 0.8)):
        dv = (math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el)),
              math.cos(math.radians(el)) * math.sin(math.radians(az)))
        for i in range(10):
            t = i / 9.0
            dist = 74 + 34 * t * spread
            p = (dv[0] * dist, CY + dv[1] * dist - 18 * t * t, dv[2] * dist)
            if abs(p[0]) > 92 or p[2] > 120 or p[1] > 128:
                continue
            size = 2.8 - 2.0 * t + rng.uniform(-0.3, 0.4)
            for x in range(int(p[0] - 4), int(p[0] + 5)):
                for y in range(int(p[1] - 4), int(p[1] + 5)):
                    for z in range(int(p[2] - 4), int(p[2] + 5)):
                        dd = math.sqrt((x - p[0]) ** 2 + ((y - p[1]) * 1.6) ** 2 + (z - p[2]) ** 2)
                        if dd <= size and hash3(x, y, z, 5241) < 0.85:
                            C.put(x, y, z, rng.choice((ESB, PUR, BRASS, VERD, "end_stone", OBS)))
    for (sx, sy, sz, rx) in ((-84, 44, 30, 6), (82, 70, -20, 5), (-60, 102, 64, 4), (66, 96, 70, 4),
                             (30, 18, -78, 5), (-40, 20, -76, 4)):
        cols = rock_lobe(sx, sy, sz, rx, rx * 0.8, rx * 1.4, 5242 + sx, spikes=2)
        build_rock(C.bp, cols, 5243 + sz, surface="end_stone", deco=0.5)
        # a torn plate riding on it
        for i in range(-2, 3):
            C.put(sx + i, sy + 1, sz, BRASS if i % 2 else VERD)


# ------------------------------------------------------------------ the whole site
def hollow_moon(bp):
    WALK.clear()
    FLOOR_A.clear()
    FLOOR_B.clear()
    CRYPT_FLOOR.clear()
    GRAND.clear()
    CRYPT_STAIR.clear()
    BRIDGE.clear()
    C = Ctx(bp)
    outer_shell(C)
    mid_shell(C)
    cols = island(C)
    decks(C)
    for a in (45, 135, 225, 315):
        radial_wall(C, a, FA, FB - 2, door=(50.5, 3, 4), band=(FA + 9,), r_range=(40, 68))
    CRYPT_FLOOR.update(crypt(C))
    stairs_between(C)
    landing(C)
    gardens(C)
    hub(C)
    lift(C)
    escapement(C)
    columns(C)
    workshop(C)
    star_dome(C)
    terrace(C)
    ring_door(C)
    edge_rails(C, FLOOR_B, FB - 1, lambda x, z: True)
    sump(C)
    pillar_and_platform(C)
    shaft(C)
    reliquary(C)
    rings_and_links(C)
    grace_and_bridge(C)
    arena_dress(C)
    camp(C)
    bridge_and_tower(C)
    wreckage(C, cols)
    chains(C, cols)
    debris(C)
    deck_lights(C)
    fill_gaps(C, FLOOR_A, FA - 1, up=True)
    fill_gaps(C, FLOOR_B, FB - 1, up=True)
    fill_gaps(C, FLOOR_A, FA - 1, up=False, spec=IRON)
    fill_gaps(C, FLOOR_B, FB - 1, up=False, spec=IRON)
    fill_gaps(C, CRYPT_FLOOR, FC - 1, up=True, spec="polished_blackstone_bricks")


# camera spots for the CI focus run: (name, feet (x, y, z), look at (x, y, z)), blueprint coordinates
VIEWS = [
    ("astronomers_camp", (4, 23, 104), (0, 40, 60)),
    ("breach_landing", (0, 25, 55), (0, 62, 0)),
    ("meridian_hall", (-28, 25, -41), (9, 28, -53)),
    ("gravity_gardens", (-41, 25, -29), (-45, 26, -3)),
    ("gear_crypt", (31, 9, -14), (10, 11, -36)),
    ("lens_workshop", (0, 46, -57), (-20, 50, -57)),
    ("orrery_rings", (23, 49, -38), (-10, 60, 0)),
    ("core_arena", (0, 50, 12), (0, 62, -5)),
]

register(StructureDef(
    "hollow_moon", "end", OUTER_END,
    [Piece("moon", hollow_moon, views=VIEWS)],
    spacing=40, separation=14, adaptation="none", height=("uniform", 30, 40), processors="none", max_distance=128,
    ground=0, foundation=False,
    spawns=[("minecraft:enderman", 10, 1, 2), (MOB_STALKER, 5, 1, 2), (MOB_ACOLYTE, 5, 1, 2), (MOB_SPIDER, 4, 1, 2),
            (MOB_DRONE, 3, 1, 1)],
    title_fr="La Lune creuse", title_en="The Hollow Moon"))

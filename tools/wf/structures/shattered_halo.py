"""Shattered Halo (Halo brisé / Shattered Halo): a tilted ring megastructure ~170 across, broken into five arcs that
float over the void of the outer End at different heights and tilts, with a temple on each arc and the boss on a
floating disc at the centre. Colossal tier (tools/BUILDING.md §1, §12 concept 9, §15).

Silhouette: a broken halo. The ring (centreline radius 78, deck 14 wide, a keel up to 11 deep) is tilted about
10 degrees (low in the south-east, high in the north-west), and each of its five arcs is displaced, rolled and
twisted on its own, so the breaks read from far away as steps in a glowing band: purpur sides with a gilded string
course, end-rod crown lights on the outer parapet and a dark obsidian keel hung with rods. Five temples rise from
the arcs, the bell shrine's gilded needle being the dominant peak, the gate's twin pylons the second.

Layout (blueprint coordinates, x east, z south, centre of the halo at (0, 0); angles counter-clockwise from +x
toward +z):
  * arrival: an outer islet at the south-east (78, 66) with the waystone, braziers and a ruined gateway framing the
    halo; a bridge leads onto arc A (the low arc);
  * arc A (72 deg, feet 36): the Observatory, a domed drum with a giant telescope aimed through the dome's slit;
  * light bridge (108 deg) up to arc B (144 deg, feet 41): the Library of the Void, an octagonal tower with a
    gallery round a well that opens straight down onto the void (void stalker spawner);
  * stepping islets (180 deg) up to arc C (216 deg, feet 53): the Reliquary, a Greek cross under a stepped pyramid;
    a trapdoor in the west arm drops by a ladder into a hidden crypt in the plaza's keel (the secret);
  * arched bridge (252 deg) up to arc D (288 deg, feet 60, the highest): the Bell Shrine, an open colonnade round a
    great gilded bell hung between two pylons under a 40-block needle (shulker spawner);
  * light bridge (324 deg) down to arc E (0 deg, feet 46): the Gate, a dark hall straddling the ring with twin
    pylons and a portal facing the centre (enderman spawner); the south end of arc E breaks off into a vista;
  * from the portal the radial bridge runs west over the void to the islet of the site of grace, then through a
    narrow portico (compression, the mist) onto the arena: a disc of radius 16 (feet 44), open to the void with a
    low broken parapet, framed by floating shards of a smaller ring; past the west mist and the sealed bars, the
    reward vault on its own islet.
Loot gradient (§15.6): islet tier 1, observatory tier 1, library / reliquary / bell / gate tier 2, the crypt
tier 2-3, the vault tier 3.
"""
import math

from ..arch import Palette, slab, stair
from ..defs import Piece, StructureDef, register
from ..megakit import hash01, hash3
from ..parts import LOOT, MOB, MOD
from .end import (ESB, ESB_SL, ESB_ST, ESB_WA, FROG, OUTER_END, PUR, PUR_P, PUR_SL, PUR_ST, ROD_DOWN, ROD_UP, STAR,
                  VB, VB_SL, VB_ST, VB_WA, brazier, build_rock, disk_pts, face_in, face_vec, hang_star, ring_pts,
                  rock_lobe, round_windows, tube)

# the halo's own guardian: the Fallen Seraph (entity/boss/FallenSeraph.java, tools/BOSSES.md section 10)
BOSS = "brasshaven:fallen_seraph"

# ------------------------------------------------------------------ geometry
R = 78                      # centreline radius of the ring
HW = 7                      # half width of the deck
HALF = 27                   # half angular span of an arc (degrees): 54 deg of arc, 18 deg gaps
BLEND = 12                  # plaza flattening blends into the sloping deck over this many blocks
TILT = 20.0                 # half the height difference across the ring before it broke (tilt ~14 deg)
ARENA_Y = 44                # feet on the arena disc (floor blocks y 43)
ARENA_R = 16                # arena floor radius (parapet at 17)
GRACE = (36, 0)             # islet of the site of grace on the radial bridge
VAULT = (-35, 0)            # the reward vault islet
ISLET = (78, 66)            # the arrival islet

# the five arcs: centre angle, height offset, twist (extra slope along the arc), roll (radial slope), radial shift,
# plaza radius
ARCS = [
    dict(key="A", name="observatory", tc=72, off=1.0, twist=0.05, roll=0.12, dr=0, pr=13),
    dict(key="B", name="library", tc=144, off=2.0, twist=-0.05, roll=-0.10, dr=2, pr=13),
    dict(key="C", name="reliquary", tc=216, off=-2.0, twist=-0.06, roll=0.15, dr=-2, pr=14),
    dict(key="D", name="bell", tc=288, off=1.0, twist=0.05, roll=-0.12, dr=1, pr=13),
    dict(key="E", name="gate", tc=0, off=-1.0, twist=-0.04, roll=0.10, dr=-3, pr=15),
]

# ------------------------------------------------------------------ materials
GOLD = "gold_block"
OBS = "obsidian"
CRY = "crying_obsidian"
WALL_A = Palette({PUR: 6, PUR_P: 2, ESB: 1}, seed=601, scale=2.4)            # observatory: light purpur drum
WALL_B = Palette({VB: 8, OBS: 1, "polished_blackstone_bricks": 1}, seed=602, scale=2.2)   # library: void bricks
WALL_C = Palette({ESB: 7, "end_stone": 1, PUR: 1}, seed=603, scale=2.0)     # reliquary: end stone bricks
WALL_E = Palette({OBS: 4, VB: 5, CRY: 0.4}, seed=605, scale=2.6)            # gate: dark obsidian and void
FACE = Palette({PUR: 6, PUR_P: 2}, seed=606, scale=2.2)                     # the halo's side faces
PAVE = Palette({ESB: 9, "end_stone": 1}, seed=607, scale=1.8)
KEEL = Palette({OBS: 6, CRY: 1, VB: 2}, seed=608, scale=2.6)
BELL_GOLD = Palette({GOLD: 6, "raw_gold_block": 1}, seed=609, scale=1.6)


def rad(d):
    return math.radians(d)


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def base_h(th):
    """The tilted ring before it broke: feet height along the centreline (low at 90 deg, high at 270 deg)."""
    return 47.0 - TILT * math.sin(rad(th))


def arc_r(arc):
    return R + arc["dr"]


def plaza_c(arc):
    rr = arc_r(arc)
    return round(rr * math.cos(rad(arc["tc"]))), round(rr * math.sin(rad(arc["tc"])))


def plaza_h(arc):
    return round(base_h(arc["tc"]) + arc["off"])


def deck_raw(arc, th, r):
    d = wrap(th - arc["tc"])
    return base_h(th) + arc["off"] + arc["twist"] * arc_r(arc) * rad(d) + arc["roll"] * (r - arc_r(arc))


def deck_s(arc, x, z):
    """Walking surface (feet height, float) of an arc column, flattened round its temple."""
    r = math.hypot(x, z)
    th = math.degrees(math.atan2(z, x))
    s = deck_raw(arc, th, r)
    px, pz = plaza_c(arc)
    d = math.hypot(x - px, z - pz)
    pr = arc["pr"]
    if d <= pr:
        return float(plaza_h(arc))
    if d < pr + BLEND:
        t = (d - pr) / BLEND
        t = t * t * (3 - 2 * t)
        return plaza_h(arc) * (1 - t) + s * t
    return s


def q2(s):
    return round(s * 2) / 2.0


def jag(r, seed):
    """Broken-end jitter (degrees) of an arc end along the radius."""
    return 1.4 * math.sin(r * 0.9 + seed) + 0.7 * math.sin(r * 2.3 + seed * 2.1) + 0.5 * math.sin(r * 4.1 + seed)


def arc_point(arc, th, dr=0.0):
    rr = arc_r(arc) + dr
    x, z = rr * math.cos(rad(th)), rr * math.sin(rad(th))
    return x, q2(deck_s(arc, x, z)), z


# ------------------------------------------------------------------ small helpers
def surface(bp, x, z, s, full, half, under=None):
    """Walking surface at feet height s (multiple of 0.5): a full block, or a bottom slab on `under`."""
    n = math.floor(s)
    if s - n > 0.25:
        bp.set(x, n, z, slab(half))
        bp.set(x, n - 1, z, under or full)
        return n
    bp.set(x, n - 1, z, full)
    return n - 1


def air(bp, x0, y0, z0, x1, y1, z1):
    bp.fill(x0, y0, z0, x1, y1, z1, "air")


def outward(x, z, cx, cz):
    return face_vec(x - cx, z - cz)


def wall_rod(bp, x, y, z, facing):
    bp.set(x, y, z, f"end_rod[facing={facing}]")


def candles(bp, x, y, z, n=3, color="purple"):
    bp.set(x, y, z, f"{color}_candle[candles={n},lit=true,waterlogged=false]")


def door_cut(bp, cx, cz, F, ang, r0, r1, w=3, h=4, frame=PUR_P, lintel=GOLD):
    """A doorway through a round or polygonal wall along the ray at angle `ang` (degrees), framed outside."""
    ux, uz = math.cos(rad(ang)), math.sin(rad(ang))
    px, pz = -uz, ux
    hw = w // 2
    t = r0
    while t <= r1:
        for o in range(-hw, hw + 1):
            x, z = round(cx + ux * t + px * o), round(cz + uz * t + pz * o)
            for y in range(F, F + h):
                bp.set(x, y, z, "air")
        t += 0.3
    for o in (-hw - 1, hw + 1):
        x, z = round(cx + ux * r1 + px * o), round(cz + uz * r1 + pz * o)
        for y in range(F, F + h):
            bp.set(x, y, z, frame)
        bp.set(x, F + h, z, lintel)
    for o in range(-hw, hw + 1):
        x, z = round(cx + ux * r1 + px * o), round(cz + uz * r1 + pz * o)
        bp.set(x, F + h, z, lintel if o == 0 else PUR)


# ------------------------------------------------------------------ the ring
def arc_columns():
    """{(x, z): (arc index, feet s, bottom y, flags)} of every arc column (deck band + plaza)."""
    cols = {}
    for k, arc in enumerate(ARCS):
        rr = arc_r(arc)
        px, pz = plaza_c(arc)
        pr = arc["pr"]
        for x in range(-92, 93):
            for z in range(-92, 93):
                r = math.hypot(x, z)
                th = math.degrees(math.atan2(z, x))
                d = wrap(th - arc["tc"])
                dp = math.hypot(x - px, z - pz)
                in_plaza = dp <= pr + 0.4
                lim = HALF + jag(r, k * 3.7 + (0 if d < 0 else 1.9))
                in_band = abs(r - rr) <= HW + 0.4 and abs(d) <= lim
                if not (in_band or in_plaza):
                    continue
                s = q2(deck_s(arc, x, z))
                e = lim - abs(d)                       # degrees from the break
                u = (r - rr) / (HW + 1.0)
                depth = 4.0 + 10.0 * max(0.0, 1 - u * u) ** 0.8
                if e < 7 and not in_plaza:
                    depth *= 0.45 + 0.55 * e / 7.0
                    depth += 2.5 * hash01(x, z, 611 + k) - 1.0
                if in_plaza:
                    depth = max(depth, 4.0 + 10.0 * (1 - (dp / pr) ** 2))
                bottom = math.floor(s) - 2 - round(depth)
                cols[(x, z)] = (k, s, bottom, e if not in_plaza else 99.0, in_plaza, dp)
    return cols


def build_ring(bp, cols):
    """Bodies of the five arcs: paving with a purpur centre line and segment joints, gilded string course and purpur
    faces on the rims, an obsidian keel hung with end rods; parapets with end-rod posts on the rims."""
    keyset = set(cols)
    for (x, z), (k, s, bottom, e, in_plaza, dp) in cols.items():
        arc = ARCS[k]
        rr = arc_r(arc)
        r = math.hypot(x, z)
        th = math.degrees(math.atan2(z, x))
        a = rad(wrap(th - arc["tc"])) * rr                  # arc length from the temple
        nbs = [(x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)]
        edge = any(n not in keyset for n in nbs)
        outer = r > rr
        joint = math.floor((a - 0.6) / 7.0) != math.floor((a + 0.6) / 7.0) and not in_plaza
        centre = abs(r - rr) < 0.9 and not in_plaza
        broken = e < 1.6
        # paving
        if in_plaza:
            if arc["pr"] - 1.4 < dp <= arc["pr"] + 0.4:
                top, half = PUR, PUR_SL
            elif arc["pr"] - 2.6 < dp <= arc["pr"] - 1.4:
                top, half = (GOLD if (x + z) % 3 == 0 else ESB), ESB_SL
            else:
                top, half = PAVE.pick(x, 0, z), ESB_SL
        elif broken:
            top, half = ("end_stone" if hash01(x, z, 612) < 0.6 else OBS), ESB_SL
        elif centre or joint:
            top, half = (PUR_P if joint else PUR), PUR_SL
        else:
            top, half = PAVE.pick(x, 0, z), ESB_SL
        ytop = surface(bp, x, z, s, top, half, under=ESB)
        n = math.floor(s)
        # body
        for y in range(bottom, ytop):
            hb = y - bottom
            t = ytop - y
            if hb < 2:
                spec = KEEL.pick(x, y, z)
            elif edge:
                if t == 1:
                    spec = GOLD if (outer or in_plaza) else PUR
                elif t == 2 and joint:
                    spec = GOLD
                elif hb < 4:
                    spec = VB
                else:
                    spec = PUR_P if joint else FACE.pick(x, y, z)
            elif t <= 2:
                spec = ESB
            elif hb < 4:
                spec = VB
            else:
                spec = "end_stone"
            bp.set(x, y, z, spec)
        # outer face lights: end rods pointing out of the halo, every third column
        if edge and not broken and hash01(x, z, 613) < 0.34 and ytop - bottom > 6:
            for (nx, nz) in nbs:
                if (nx, nz) not in keyset:
                    f = face_vec(nx - x, nz - z)
                    if bp.get(nx, ytop - 4, nz) is None:
                        wall_rod(bp, nx, ytop - 4, nz, f)
                    break
        # the keel: rods and starlight chains under the lowest cells
        lowest = all(n2 not in cols or cols[n2][2] >= bottom for n2 in nbs)
        if lowest and ytop - bottom > 7:
            h = hash01(x, z, 614)
            if h < 0.45:
                bp.set(x, bottom - 1, z, ROD_DOWN)
            elif h < 0.75:
                ln = 1 + int(hash01(x, z, 615) * 4)
                bp.chain(x, bottom - ln, z, bottom - 1)
                bp.set(x, bottom - ln - 1, z, STAR if h < 0.6 else FROG)
            else:
                bp.set(x, bottom - 1, z, "amethyst_cluster[facing=down,waterlogged=false]")
        elif joint and centre and ytop - bottom > 8:
            bp.set(x, bottom - 1, z, OBS)
            bp.set(x, bottom - 2, z, ROD_DOWN)
        # parapet on the rims (not at the broken ends): end stone brick wall, purpur posts with crown rods
        if edge and not broken and e > 2.5:
            py = n
            if hash01(x, z, 616) < 0.06 and not in_plaza:
                continue                                  # a gap in the parapet: the void looks in
            post = (math.floor(a / 5.0) != math.floor((a - 1.0) / 5.0)) if not in_plaza else \
                (round(math.degrees(math.atan2(z - plaza_c(arc)[1], x - plaza_c(arc)[0]))) % 24 < 4)
            if post:
                bp.set(x, py, z, PUR_P)
                if outer or in_plaza:
                    bp.set(x, py + 1, z, ROD_UP)
            else:
                bp.set(x, py, z, ESB_WA)


def debris(bp):
    """Shards drifting below each break: a few tilted slabs of the ring, purpur and obsidian."""
    for g in range(5):
        th = 36 + 72 * g
        for j, (dr, dy, sz) in enumerate(((8, -9, 3), (-12, -13, 2), (5, -18, 2), (-5, -7, 1))):
            rr = R + dr
            cx, cz = round(rr * math.cos(rad(th + 3 * j - 4))), round(rr * math.sin(rad(th + 3 * j - 4)))
            cy = round(base_h(th) + dy)
            for x in range(cx - sz - 1, cx + sz + 2):
                for z in range(cz - sz - 1, cz + sz + 2):
                    if abs(x - cx) + abs(z - cz) > sz + 1:
                        continue
                    y = cy + round(0.5 * (x - cx) - 0.3 * (z - cz))
                    bp.set(x, y, z, PUR if hash3(x, y, z, 620 + g) < 0.6 else OBS)
                    bp.set(x, y - 1, z, OBS)
                    if (x, z) == (cx, cz):
                        bp.set(x, y - 2, z, ROD_DOWN)
                    if hash3(x, y, z, 621) < 0.25:
                        bp.set(x, y + 1, z, GOLD if j == 0 else slab(ESB_SL))


# ------------------------------------------------------------------ walkways
def walkway(bp, pts, width=3, style="stone", rise=0.0):
    """A walkway along a polyline of (x, feet s, z) points. Surfaces are quantised to half blocks (slab steps), so a
    slope up to 0.5 per block is walked without jumping. style: stone (purpur deck, wall rails, keel), light (a
    glowing deck with rails of end rods), plain (paving, no keel)."""
    hw = width // 2
    deck_c, rail_c = {}, {}
    total = sum(math.hypot(b[0] - a[0], b[2] - a[2]) for a, b in zip(pts, pts[1:]))
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[2] - a[2])
        ux, uz = (b[0] - a[0]) / L, (b[2] - a[2]) / L
        px, pz = -uz, ux
        n = int(L * 3) + 1
        slope = abs(b[1] - a[1]) / L
        if slope > 0.5:
            print(f"shattered_halo: walkway segment {a}->{b} too steep ({slope:.2f})")
        for i in range(n + 1):
            t = i / n
            cx, cz = a[0] + (b[0] - a[0]) * t, a[2] + (b[2] - a[2]) * t
            tt = (acc + L * t) / total
            s = a[1] + (b[1] - a[1]) * t + rise * math.sin(math.pi * tt)
            for w in range(-hw - 1, hw + 2):
                X, Z = round(cx + px * w), round(cz + pz * w)
                tgt = rail_c if abs(w) == hw + 1 else deck_c
                tgt.setdefault((X, Z), []).append((abs(w), s, tt))
        acc += L
    out = {}
    for (X, Z), ss in deck_c.items():
        ss.sort()
        _, s, tt = ss[0]
        s = q2(s)
        out[(X, Z)] = s
        mid = ss[0][0] == 0
        if style == "light":
            full, half = (FROG if mid else PUR), ("smooth_quartz_slab" if mid else PUR_SL)
        elif style == "plain":
            full, half = PAVE.pick(X, 0, Z), ESB_SL
        else:
            full, half = (PUR if mid else ESB), (PUR_SL if mid else ESB_SL)
        y = surface(bp, X, Z, s, full, half, under=(PUR if style == "light" else VB))
        for c in range(1, 4):
            bp.set(X, y + c, Z, "air")
        if style != "light" and bp.get(X, y - 1, Z) is None:
            bp.set(X, y - 1, Z, slab(VB_SL, "top"))
    k = 0
    for (X, Z), ss in sorted(rail_c.items(), key=lambda kv: min(v[2] for v in kv[1])):
        if (X, Z) in deck_c:
            continue
        ss.sort()
        s = ss[0][1]
        top = math.ceil(q2(s) - 0.01)
        if bp.get(X, top - 1, Z) is not None:
            continue                                     # over a surface already (the islet or the arc deck)
        k += 1
        if style == "light":
            bp.set(X, top - 1, Z, slab(PUR_SL, "top"))
            bp.set(X, top, Z, ROD_UP if k % 2 else "purple_stained_glass_pane")
        else:
            bp.set(X, top - 1, Z, VB if style == "stone" else ESB)
            bp.set(X, top - 2, Z, slab(VB_SL, "top"))
            if k % 6 == 0:
                bp.set(X, top, Z, PUR_P)
                bp.set(X, top + 1, Z, ROD_UP)
            else:
                bp.set(X, top, Z, ESB_WA)
    # keel line under stone walkways, a light under the middle of each span
    if style == "stone":
        for (X, Z), s in out.items():
            if deck_c[(X, Z)][0][0] == 0 and bp.get(X, math.floor(s) - 3, Z) is None:
                bp.set(X, math.floor(s) - 2, Z, VB)
                if hash01(X, Z, 630) < 0.12:
                    bp.set(X, math.floor(s) - 3, Z, ROD_DOWN)
    elif style == "light":
        for (X, Z), s in out.items():
            if deck_c[(X, Z)][0][0] == 0 and hash01(X, Z, 631) < 0.3 and bp.get(X, math.floor(s) - 2, Z) is None:
                bp.set(X, math.floor(s) - 2, Z, "purple_stained_glass")
    return out


def islet(bp, cx, cz, feet, r, depth, seed):
    cols = rock_lobe(cx, feet - 1, cz, r, r, depth, seed, spikes=4)
    build_rock(bp, cols, seed, surface="end_stone")
    return cols


def bridges(bp):
    """The crossings over the four gaps of the route (A->B->C->D->E) and the approach from the arrival islet."""
    A, B, C, D, E = ARCS
    # approach: islet -> arc A (a gateway at the islet end)
    pa = arc_point(A, A["tc"] - HALF + 4)
    walkway(bp, [(ISLET[0] - 5, ISLET_FEET, ISLET[1] - 3), (pa[0], pa[1], pa[2])], width=3, style="stone", rise=1.5)
    # A -> B: a light bridge
    p0, p1 = arc_point(A, A["tc"] + HALF - 4), arc_point(B, B["tc"] - HALF + 4)
    walkway(bp, [p0, p1], width=3, style="light", rise=2.0)
    # B -> C: two stepping islets, a zig-zag of short walkways
    p0, p1 = arc_point(B, B["tc"] + HALF - 4), arc_point(C, C["tc"] - HALF + 4)
    mids = []
    for t, side, dy in ((0.36, 4.5, 1.0), (0.68, -4.0, 2.0)):
        x = p0[0] + (p1[0] - p0[0]) * t
        z = p0[2] + (p1[2] - p0[2]) * t
        th = math.atan2(z, x)
        x += math.cos(th) * side
        z += math.sin(th) * side
        s = round(p0[1] + (p1[1] - p0[1]) * t + dy)
        islet(bp, round(x), round(z), s, 4.6, 9, 640 + len(mids))
        mids.append((round(x), float(s), round(z)))
    walkway(bp, [p0, mids[0]], width=3, style="plain", rise=0.5)
    walkway(bp, [mids[0], mids[1]], width=3, style="plain", rise=0.5)
    walkway(bp, [mids[1], p1], width=3, style="plain", rise=0.5)
    for (x, s, z) in mids:
        brazier(bp, x + 2, int(s), z + 2, h=2)
    # C -> D: an arched stone bridge
    p0, p1 = arc_point(C, C["tc"] + HALF - 4), arc_point(D, D["tc"] - HALF + 4)
    walkway(bp, [p0, p1], width=3, style="stone", rise=3.0)
    # D -> E: a light bridge going down
    p0, p1 = arc_point(D, D["tc"] + HALF - 4), arc_point(E, E["tc"] - HALF + 4)
    walkway(bp, [p0, p1], width=3, style="light", rise=1.0)


# ------------------------------------------------------------------ arrival islet
ISLET_FEET = q2(deck_s(ARCS[0], (R) * math.cos(rad(72 - HALF + 4)), R * math.sin(rad(72 - HALF + 4)))) - 1
ISLET_FEET = float(math.floor(ISLET_FEET))


def arrival(bp):
    cx, cz = ISLET
    F = int(ISLET_FEET)
    cols = rock_lobe(cx, F - 1, cz, 7.5, 7.0, 16, 650, spikes=6)
    build_rock(bp, cols, 650, surface="end_stone")
    # paving: a disc of end stone bricks with a purpur ring
    for (x, z) in disk_pts(cx, cz, 5.5):
        if (x, z) in cols:
            d = math.hypot(x - cx, z - cz)
            bp.set(x, F - 1, z, PUR if 4.5 < d <= 5.9 else (GOLD if d < 1.5 else PAVE.pick(x, 0, z)))
    # the waystone on its dais, facing the halo
    bp.set(cx, F, cz, MOD["waystone"])
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, F - 1, cz + dz, GOLD)
    # braziers and lamp posts
    brazier(bp, cx + 4, F, cz + 3, h=2)
    brazier(bp, cx + 3, F, cz - 4, h=2)
    # the ruined gateway at the bridge head, framing the halo: two purpur piers, one broken, a gilded lintel stub
    gx, gz = cx - 5, cz - 3
    for (dx, dz, h) in ((0, -3, 8), (0, 3, 5)):
        x, z = gx + dx, gz + dz
        for y in range(F, F + h):
            bp.set(x, y, z, PUR_P if y < F + h - 1 else PUR)
        bp.set(x, F, z, ESB)
        bp.set(x + 1, F, z, stair(ESB_ST, "west"))
    for dz in (-3, -2, -1):
        bp.set(gx, F + 8, gz + dz, GOLD if dz == -3 else PUR)
    bp.set(gx, F + 8, gz, slab(PUR_SL, "top"))
    bp.set(gx, F + 9, gz - 3, ROD_UP)
    for y in range(F + 5, F + 7):
        bp.set(gx + 1, y, gz + 3, "air")
    # pilgrims' camp: a barrel of supplies, a lectern, lanterns
    bp.barrel(cx + 2, F, cz + 4, "up", loot=LOOT + "halo_islet")
    bp.set(cx + 3, F, cz + 4, "barrel[facing=up,open=false]")
    bp.set(cx - 1, F, cz + 4, "lectern[facing=north,has_book=false,powered=false]")
    bp.lantern(cx + 1, F, cz + 5)
    bp.set(cx - 2, F, cz - 4, "purple_banner[rotation=4]")


# ------------------------------------------------------------------ temple A: the observatory
def observatory(bp, arc):
    cx, cz = plaza_c(arc)
    F = plaza_h(arc)
    tc = arc["tc"]
    inward = tc + 180
    # plinth step and drum
    for (x, z) in ring_pts(cx, cz, 9):
        bp.set(x, F, z, stair(PUR_ST, face_in(x, z, cx, cz)))
    for (x, z) in ring_pts(cx, cz, 8):
        for y in range(F, F + 10):
            bp.set(x, y, z, WALL_A.pick(x, y, z) if y > F else ESB)
        bp.set(x, F + 10, z, GOLD)
    for (x, z) in disk_pts(cx, cz, 7):
        for y in range(F, F + 11):
            bp.set(x, y, z, "air")
    # pilasters
    for k in range(8):
        a = rad(22.5 + 45 * k)
        x, z = cx + round(math.cos(a) * 9), cz + round(math.sin(a) * 9)
        for y in range(F, F + 11):
            bp.set(x, y, z, PUR_P if F < y < F + 10 else (ESB if y == F else GOLD))
        bp.set(x, F + 11, z, ROD_UP)
    # windows between the pilasters (skip the door bays)
    bays = []
    for k in range(8):
        a = 45 * k
        if min(abs(wrap(a - (tc + 90))), abs(wrap(a - (tc - 90)))) < 30:
            continue
        bays.append(rad(a))
    round_windows(bp, cx, cz, 8, bays, F + 3, F + 7, glass="magenta_stained_glass_pane", hood=None, sill=None)
    # cornice
    for (x, z) in ring_pts(cx, cz, 9):
        bp.set(x, F + 10, z, stair(PUR_ST, outward(x, z, cx, cz), "top"))
    # the dome: void brick panels, gilded ribs, a slit toward the halo's centre
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            for y in range(F + 11, F + 20):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2 + (y - F - 11) ** 2 * 1.15)
                if not (d <= 8.4):
                    continue
                ang = math.degrees(math.atan2(z - cz, x - cx))
                if d > 7.4:
                    if abs(wrap(ang - inward)) * math.hypot(x - cx, z - cz) * 0.0175 < 1.6 and y >= F + 12:
                        bp.set(x, y, z, "air")
                        continue
                    rib = (round(ang) % 45) < 4
                    bp.set(x, y, z, GOLD if rib else (VB if hash3(x, y, z, 660) < 0.85 else OBS))
                else:
                    bp.set(x, y, z, "air")
    bp.set(cx, F + 20, cz, GOLD)
    bp.set(cx, F + 21, cz, ROD_UP)
    # star map floor
    for (x, z) in disk_pts(cx, cz, 7):
        d = math.hypot(x - cx, z - cz)
        bp.set(x, F - 1, z, GOLD if 4.5 < d <= 5.4 else (STAR if hash01(x, z, 661) < 0.07 else VB))
    # the telescope: a copper tube on a pier, aimed through the slit
    for y in range(F, F + 4):
        bp.set(cx, y, cz, VB_WA if y < F + 3 else OBS)
    el = rad(48)
    ux, uz = math.cos(rad(inward)), math.sin(rad(inward))
    dvec = (ux * math.cos(el), math.sin(el), uz * math.cos(el))
    tube(bp, (cx + 0.5 * 0, F + 4.5, cz), dvec, 14, 1.3, 1.0, "oxidized_cut_copper", rings=GOLD, ring_every=4,
         back=1.5)
    # lecterns, desks and a chest round the telescope; bookshelves between the windows
    for k, f in ((0, "west"), (2, "north"), (4, "east"), (6, "south")):
        a = rad(tc + 45 + 45 * k)
        x, z = cx + round(math.cos(a) * 5), cz + round(math.sin(a) * 5)
        if bp.get(x, F, z) in (None, "minecraft:air"):
            bp.set(x, F, z, f"lectern[facing={face_in(x, z, cx, cz)},has_book=false,powered=false]")
    a = rad(inward + 60)
    x, z = cx + round(math.cos(a) * 6), cz + round(math.sin(a) * 6)
    bp.chest(x, F, z, face_in(x, z, cx, cz), loot=LOOT + "halo_observatory")
    a = rad(inward - 60)
    x, z = cx + round(math.cos(a) * 6), cz + round(math.sin(a) * 6)
    bp.set(x, F, z, "cartography_table")
    for (x, z) in ring_pts(cx, cz, 7):
        ang = math.degrees(math.atan2(z - cz, x - cx))
        if min(abs(wrap(ang - (tc + 90))), abs(wrap(ang - (tc - 90)))) < 25:
            continue
        if bp.get(x, F, z) in (None, "minecraft:air") and hash01(x, z, 662) < 0.7:
            bp.set(x, F, z, "bookshelf")
    for k in range(4):
        a = rad(tc + 45 + 90 * k)
        x, z = cx + round(math.cos(a) * 7), cz + round(math.sin(a) * 7)
        if bp.get(x, F + 6, z) in (None, "minecraft:air"):
            wall_rod(bp, x, F + 6, z, face_in(x, z, cx, cz))
    hang_star(bp, cx + 3, F + 15, cz - 2, 4)
    hang_star(bp, cx - 3, F + 15, cz + 2, 5)
    # doors toward both ends of the arc
    for da in (90, -90):
        door_cut(bp, cx, cz, F, tc + da, 6.6, 9.4, w=3, h=4)


# ------------------------------------------------------------------ temple B: the library of the void
def _oct(dx, dz, a):
    return max(abs(dx), abs(dz)) <= a and abs(dx) + abs(dz) <= round(a * 1.42)


def library(bp, arc):
    cx, cz = plaza_c(arc)
    F = plaza_h(arc)
    tc = arc["tc"]
    A_OUT, A_IN = 9, 8
    TOP = F + 16
    for dx in range(-A_OUT - 1, A_OUT + 2):
        for dz in range(-A_OUT - 1, A_OUT + 2):
            x, z = cx + dx, cz + dz
            if _oct(dx, dz, A_OUT) and not _oct(dx, dz, A_IN):
                for y in range(F, TOP):
                    if y in (F + 6, TOP - 1):
                        spec = GOLD if y == F + 6 else PUR
                    else:
                        spec = WALL_B.pick(x, y, z)
                    bp.set(x, y, z, spec)
            elif _oct(dx, dz, A_IN):
                for y in range(F, TOP):
                    bp.set(x, y, z, "air")
                bp.set(x, F - 1, z, VB if (dx + dz) % 2 else "polished_blackstone_bricks")
    # corner buttresses of purpur, stepping back
    for k in range(8):
        a = rad(22.5 + 45 * k)
        for rr, h in ((10, 9), (11, 5)):
            x, z = cx + round(math.cos(a) * rr), cz + round(math.sin(a) * rr)
            for y in range(F, F + h + (12 - rr) * 4):
                bp.set(x, y, z, PUR_P)
            bp.set(x, F + h + (12 - rr) * 4, z, stair(PUR_ST, face_in(x, z, cx, cz)))
    # the octagonal spire, steep, with purpur ribs and a gilded finial
    i = 0
    while True:
        a_i = A_OUT + 0.5 - i * 0.55
        if a_i < 0.6:
            break
        y = TOP + i
        ai = int(a_i)
        for dx in range(-ai - 1, ai + 2):
            for dz in range(-ai - 1, ai + 2):
                if _oct(dx, dz, a_i) and not _oct(dx, dz, a_i - 1.2):
                    rib = abs(abs(dx) - abs(dz)) <= 0 or dx == 0 or dz == 0
                    bp.set(cx + dx, y, cz + dz, PUR if rib else (VB if hash3(dx, y, dz, 670) < 0.9 else OBS))
        i += 1
    y_tip = TOP + i
    bp.set(cx, y_tip, cz, GOLD)
    bp.set(cx, y_tip + 1, cz, ROD_UP)
    # lancet windows on the faces at gallery height, small windows below
    for k in range(8):
        a = rad(45 * k)
        dist = 9 if k % 2 == 0 else 6.5
        x, z = cx + round(math.cos(a) * dist), cz + round(math.sin(a) * dist)
        if k % 2 == 1:
            x, z = cx + round(math.cos(a) * 6.4), cz + round(math.sin(a) * 6.4)
            x += (1 if math.cos(a) > 0 else -1)
            z += (1 if math.sin(a) > 0 else -1)
        for y in range(F + 8, F + 14):
            if _oct(x - cx, z - cz, A_OUT) and not _oct(x - cx, z - cz, A_IN):
                bp.set(x, y, z, "purple_stained_glass_pane")
        for y in range(F + 2, F + 4):
            if _oct(x - cx, z - cz, A_OUT) and not _oct(x - cx, z - cz, A_IN):
                bp.set(x, y, z, "purple_stained_glass_pane")
    # the gallery round the well (feet F + 7), its rail, the stair up the east wall
    GY = F + 6
    for dx in range(-A_IN, A_IN + 1):
        for dz in range(-A_IN, A_IN + 1):
            if _oct(dx, dz, A_IN) and not _oct(dx, dz, 4):
                if dx in (6, 7) and -3 <= dz <= 3:
                    continue
                bp.set(cx + dx, GY, cz + dz, VB)
            if _oct(dx, dz, 5) and not _oct(dx, dz, 4):
                if not (dx in (6, 7) and -3 <= dz <= 3):
                    bp.set(cx + dx, GY + 1, cz + dz, ESB_WA)
    for i in range(7):
        for dx in (6, 7):
            z = cz + 3 - i
            bp.set(cx + dx, F + i, z, stair(PUR_ST, "north"))
            for y in range(F, F + i):
                bp.set(cx + dx, y, z, VB)
            for y in range(F + i + 1, F + i + 5):
                if y > GY + 3:
                    break
                bp.set(cx + dx, y, z, "air")
    # the well of the void: a round shaft through the plaza onto the void, with a rail
    for (x, z) in disk_pts(cx, cz, 2.2):
        for y in range(F - 22, F):
            bp.set(x, y, z, "air")
    for (x, z) in ring_pts(cx, cz, 3.2):
        bp.set(x, F, z, ESB_WA)
        bp.set(x, F - 1, z, PUR)
    for (x, z) in ring_pts(cx, cz, 4.4):
        if hash01(x, z, 671) < 0.3:
            bp.set(x, F - 1, z, STAR)
    # shelves: ground floor and gallery, against the inner wall
    for dx in range(-A_IN, A_IN + 1):
        for dz in range(-A_IN, A_IN + 1):
            if _oct(dx, dz, A_IN) and not _oct(dx, dz, A_IN - 1):
                x, z = cx + dx, cz + dz
                if dx in (6, 7) and -4 <= dz <= 4:
                    continue
                for y in list(range(F, GY)) + list(range(GY + 1, GY + 5)):
                    if bp.get(x, y, z) in (None, "minecraft:air"):
                        bp.set(x, y, z, "bookshelf" if hash3(x, y, z, 672) < 0.85 else "chiseled_bookshelf[facing="
                               + face_in(x, z, cx, cz) + ",slot_0_occupied=true,slot_1_occupied=false,"
                               "slot_2_occupied=true,slot_3_occupied=false,slot_4_occupied=true,"
                               "slot_5_occupied=false]")
    # doors toward both ends of the arc (cut after the shelves)
    for da in (90, -90):
        door_cut(bp, cx, cz, F, tc + da, 6.0, 10.4, w=3, h=4)
    # lecterns round the well, candles, a void stalker spawner, the chest on the gallery
    for k in range(4):
        a = rad(45 + 90 * k)
        x, z = cx + round(math.cos(a) * 5), cz + round(math.sin(a) * 5)
        bp.set(x, F, z, f"lectern[facing={face_in(x, z, cx, cz)},has_book=false,powered=false]")
    bp.spawner(cx - 6, F, cz, MOB["void_stalker"])
    bp.chest(cx - 7, GY + 1, cz + 1, "east", loot=LOOT + "halo_library")
    candles(bp, cx - 7, GY + 1, cz - 1, 3)
    # lights: a ring of hanging starlights over the well, rods on the gallery rail
    for k in range(6):
        a = rad(60 * k)
        x, z = cx + round(math.cos(a) * 3), cz + round(math.sin(a) * 3)
        hang_star(bp, x, TOP + 3, z, 6 + k % 3, light=FROG if k % 2 else STAR)
    for (x, z) in ring_pts(cx, cz, 5.2):
        if bp.get(x, GY + 1, z) == "minecraft:end_stone_brick_wall" and hash01(x, z, 673) < 0.25:
            bp.set(x, GY + 2, z, ROD_UP)


# ------------------------------------------------------------------ temple C: the reliquary
def _cross(dx, dz, a, w):
    return (abs(dx) <= w and abs(dz) <= a) or (abs(dz) <= w and abs(dx) <= a)


def reliquary(bp, arc):
    cx, cz = plaza_c(arc)
    F = plaza_h(arc)
    A, W, H = 10, 4, 9
    for dx in range(-A, A + 1):
        for dz in range(-A, A + 1):
            if not _cross(dx, dz, A, W):
                continue
            x, z = cx + dx, cz + dz
            inner = _cross(dx, dz, A - 1, W - 1)
            for y in range(F, F + H):
                if inner:
                    bp.set(x, y, z, "air")
                else:
                    bp.set(x, y, z, GOLD if y == F + H - 1 else (ESB if y == F else WALL_C.pick(x, y, z)))
            if inner:
                bp.set(x, F - 1, z, PUR if (abs(dx) <= 1 or abs(dz) <= 1) else ESB)
    # purpur pilasters at the re-entrant and outer corners
    for (dx, dz) in ((W + 1, W + 1), (-W - 1, W + 1), (W + 1, -W - 1), (-W - 1, -W - 1),
                     (A + 1, W), (A + 1, -W), (-A - 1, W), (-A - 1, -W),
                     (W, A + 1), (-W, A + 1), (W, -A - 1), (-W, -A - 1)):
        x, z = cx + dx, cz + dz
        for y in range(F, F + H + 1):
            bp.set(x, y, z, PUR_P if y < F + H else GOLD)
        bp.set(x, F + H + 1, z, ROD_UP)
    # gable roofs over the four arms
    for (ax, az) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for j in range(W + 2):
            y = F + H + j
            for t in range(W + 1, A + 2):
                for side in (-1, 1):
                    o = side * (W + 1 - j)
                    if ax:
                        x, z = cx + ax * t, cz + o
                        f = "south" if side < 0 else "north"
                    else:
                        x, z = cx + o, cz + az * t
                        f = "east" if side < 0 else "west"
                    if j <= W:
                        bp.set(x, y, z, stair(PUR_ST, f))
                    else:
                        bp.set(x, y, z, PUR)
                # gable end wall
                if t == A:
                    for oo in range(-(W - j), W - j + 1):
                        if ax:
                            bp.set(cx + ax * t, y, cz + oo, WALL_C.pick(t, y, oo))
                        else:
                            bp.set(cx + oo, y, cz + az * t, WALL_C.pick(oo, y, t))
            if j == W + 1:
                for t in range(W + 1, A + 2):
                    if ax:
                        bp.set(cx + ax * t, y, cz, slab(PUR_SL))
                    else:
                        bp.set(cx, y, cz + az * t, slab(PUR_SL))
    # the crossing tower and its stepped pyramid with a gilded capstone
    for dx in range(-W - 1, W + 2):
        for dz in range(-W - 1, W + 2):
            x, z = cx + dx, cz + dz
            ring = max(abs(dx), abs(dz)) == W + 1
            for y in range(F + H, F + H + 6):
                if ring:
                    bp.set(x, y, z, GOLD if y == F + H + 5 else WALL_C.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
    for j in range(W + 2):
        y = F + H + 6 + j
        e = W + 1 - j
        for dx in range(-e, e + 1):
            for dz in range(-e, e + 1):
                if max(abs(dx), abs(dz)) == e:
                    bp.set(cx + dx, y, cz + dz, PUR if j % 2 == 0 else ESB)
                elif j == W + 1:
                    bp.set(cx + dx, y, cz + dz, GOLD)
    bp.set(cx, F + H + 6 + W + 2, cz, GOLD)
    bp.set(cx, F + H + 6 + W + 3, cz, ROD_UP)
    # clerestory slits in the crossing tower
    for (dx, dz) in ((W + 1, 0), (-W - 1, 0), (0, W + 1), (0, -W - 1)):
        for y in range(F + H + 1, F + H + 4):
            bp.set(cx + dx, y, cz + dz, "magenta_stained_glass_pane")
    # four doors at the ends of the arms, framed
    for (ax, az) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for o in range(-1, 2):
            for y in range(F, F + 5):
                if ax:
                    bp.set(cx + ax * A, y, cz + o, "air")
                else:
                    bp.set(cx + o, y, cz + az * A, "air")
        for o in (-2, 2):
            for y in range(F, F + 6):
                if ax:
                    bp.set(cx + ax * (A + 1), y, cz + o, PUR_P if y < F + 5 else GOLD)
                else:
                    bp.set(cx + o, y, cz + az * (A + 1), PUR_P if y < F + 5 else GOLD)
        for o in range(-1, 2):
            if ax:
                bp.set(cx + ax * (A + 1), F + 5, cz + o, GOLD if o == 0 else PUR)
            else:
                bp.set(cx + o, F + 5, cz + az * (A + 1), GOLD if o == 0 else PUR)
    # the reliquary dais: steps, a gilded pedestal, the relic (a dragon's skull) in a glass case
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = max(abs(dx), abs(dz)) == 2
            bp.set(cx + dx, F, cz + dz, stair(PUR_ST, face_in(cx + dx, cz + dz, cx, cz)) if edge and
                   (dx == 0 or dz == 0) else (PUR if edge else GOLD))
    bp.set(cx, F + 1, cz, GOLD)
    bp.set(cx, F + 2, cz, "dragon_head[powered=false,rotation=0]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(cx + dx, F + 2, cz + dz, "glass_pane")
    bp.set(cx, F + 3, cz, slab(PUR_SL))
    for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        candles(bp, cx + dx, F + 1, cz + dz, 4, "white")
    bp.chest(cx, F, cz - 3, "north", loot=LOOT + "halo_reliquary")
    # sarcophagi in the north and south arms, niches with end rods along the arms
    for sz in (-7, 7):
        for dz in (sz - 1, sz, sz + 1):
            for dx in (-2, 2):
                bp.set(cx + dx, F, cz + dz, OBS)
                bp.set(cx + dx, F + 1, cz + dz, slab(PUR_SL))
    for (ax, az) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for t in (6, 8):
            for side in (-1, 1):
                if ax:
                    x, z = cx + ax * t, cz + side * (W - 1)
                    f = "north" if side > 0 else "south"
                else:
                    x, z = cx + side * (W - 1), cz + az * t
                    f = "west" if side > 0 else "east"
                bp.set(x, F + 4, z, f"end_rod[facing={f}]")
    # chandelier in the crossing
    hang_star(bp, cx, F + H + 10, cz, 6, light=FROG)
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        hang_star(bp, cx + dx, F + H + 5, cz + dz, 3, light=STAR)
    # the secret: a trapdoor in the west arm's floor, a ladder down into the crypt in the plaza's keel
    tx, tz = cx - 7, cz + 2
    bp.set(tx, F - 1, tz, "cherry_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
    for y in range(F - 7, F - 1):
        bp.set(tx, y, tz, "ladder[facing=north,waterlogged=false]")
    for y in range(F - 8, F - 1):
        bp.set(tx, y, tz + 1, ESB)
        bp.set(tx - 1, y, tz, ESB)
        bp.set(tx + 1, y, tz, ESB)
    for x in range(cx - 10, cx - 3):
        for z in range(cz - 3, cz + 2):
            bp.set(x, F - 8, z, VB)
            for y in range(F - 7, F - 3):
                bp.set(x, y, z, "air")
            bp.set(x, F - 3, z, VB)
    for x in range(cx - 11, cx - 2):
        for z in range(cz - 4, cz + 3):
            if x in (cx - 11, cx - 3) or z in (cz - 4, cz + 2):
                for y in range(F - 8, F - 2):
                    if (x, z) != (tx, tz) and bp.get(x, y, z) != "minecraft:ladder":
                        bp.set(x, y, z, VB if hash3(x, y, z, 680) < 0.8 else OBS)
    bp.chest(cx - 10, F - 7, cz - 1, "east", loot=LOOT + "halo_crypt")
    for z in (cz - 3, cz):
        bp.set(cx - 6, F - 7, z, OBS)
        bp.set(cx - 6, F - 6, z, slab(PUR_SL))
    bp.set(cx - 6, F - 7, cz - 2, OBS)
    bp.set(cx - 6, F - 6, cz - 2, slab(PUR_SL))
    bp.set(cx - 9, F - 7, cz - 3, "skeleton_skull[powered=false,rotation=2]")
    bp.set(cx - 4, F - 5, cz - 1, "end_rod[facing=west]")
    bp.set(cx - 10, F - 5, cz + 1, "end_rod[facing=east]")


# ------------------------------------------------------------------ temple D: the bell shrine
def bell_shrine(bp, arc):
    cx, cz = plaza_c(arc)
    F = plaza_h(arc)
    tc = arc["tc"]
    # colonnade of twelve pillars and a ring entablature (no roof)
    for k in range(12):
        a = rad(15 + 30 * k)
        x, z = cx + round(math.cos(a) * 9), cz + round(math.sin(a) * 9)
        bp.set(x, F, z, ESB)
        for y in range(F + 1, F + 9):
            bp.set(x, y, z, PUR_P)
        bp.set(x, F + 9, z, GOLD)
    for x in range(cx - 11, cx + 12):
        for z in range(cz - 11, cz + 12):
            d = math.hypot(x - cx, z - cz)
            if 8.1 < d <= 10.4:
                bp.set(x, F + 10, z, GOLD if d > 9.9 else PUR)
                if 9.9 < d <= 10.4:
                    bp.set(x, F + 11, z, stair(PUR_ST, face_in(x, z, cx, cz)) if hash01(x, z, 690) < 0.75
                           else PUR_P)
    # four bell gallows on the plaza, bells within reach: ring them
    for da in (45, 135, 225, 315):
        a = rad(tc + da)
        gx, gz = cx + round(math.cos(a) * 11), cz + round(math.sin(a) * 11)
        ox, oz = (1, 0) if abs(math.sin(a)) > abs(math.cos(a)) else (0, 1)
        for sgn in (-1, 1):
            for y in range(F, F + 3):
                bp.set(gx + ox * sgn, y, gz + oz * sgn, VB_WA)
            bp.set(gx + ox * sgn, F + 3, gz + oz * sgn, slab(PUR_SL))
        bp.set(gx, F + 3, gz, GOLD)
        bp.set(gx, F + 4, gz, ROD_UP)
        bp.set(gx, F + 2, gz, f"bell[attachment=ceiling,facing={'north' if ox else 'east'},powered=false]")
    # two pylons and the beam of the great bell (along the arc's tangent)
    tx, tz = -math.sin(rad(tc)), math.cos(rad(tc))
    pyl = []
    for side in (-1, 1):
        px, pz = cx + round(tx * 6 * side), cz + round(tz * 6 * side)
        pyl.append((px, pz))
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                for y in range(F, F + 19):
                    edge = abs(dx) == 1 and abs(dz) == 1
                    bp.set(px + dx, y, pz + dz, GOLD if y in (F + 6, F + 12) else (PUR_P if edge else PUR))
        bp.set(px, F + 19, pz, GOLD)
        bp.set(px, F + 20, pz, ROD_UP)
    # the beam: a line of purpur between the pylon tops
    (ax, az), (bx, bz) = pyl
    n = 40
    beam = set()
    for i in range(n + 1):
        t = i / n
        x, z = round(ax + (bx - ax) * t), round(az + (bz - az) * t)
        beam.add((x, z))
    for (x, z) in beam:
        bp.set(x, F + 17, z, PUR)
        bp.set(x, F + 18, z, GOLD)
    # the great bell: a hollow gilded bell hung from the beam, open at its mouth (6 high under it)
    for y in range(F + 7, F + 17):
        h = (y - F - 7) / 9.0
        rr = 4.6 - 2.6 * h ** 0.8
        for x in range(cx - 5, cx + 6):
            for z in range(cz - 5, cz + 6):
                d = math.hypot(x - cx, z - cz)
                if rr - 1.0 < d <= rr + 0.3 or (y == F + 16 and d <= rr + 0.3):
                    bp.set(x, y, z, BELL_GOLD.pick(x, y, z) if y != F + 8 else "raw_gold_block")
                elif d <= rr - 1.0:
                    bp.set(x, y, z, "air")
    bp.chain(cx, F + 11, cz, F + 15)
    bp.set(cx, F + 10, cz, GOLD)
    bp.set(cx, F + 9, cz, "iron_chain[axis=y,waterlogged=false]")
    bp.set(cx, F + 8, cz, GOLD)
    # the needle on the beam: a cupola, then a tapering gilded obelisk
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            bp.set(cx + dx, F + 19, cz + dz, PUR if max(abs(dx), abs(dz)) < 2 else stair(PUR_ST, face_in(
                cx + dx, cz + dz, cx, cz)))
    for y in range(F + 20, F + 30):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                bp.set(cx + dx, y, cz + dz, GOLD if (y - F) % 5 == 0 else (PUR_P if abs(dx) + abs(dz) == 2 else PUR))
    for y in range(F + 30, F + 41):
        bp.set(cx, y, cz, GOLD if y > F + 37 or y % 4 == 0 else PUR_P)
        if y < F + 34:
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bp.set(cx + dx, y, cz + dz, stair(PUR_ST, face_vec(-dx, -dz)) if y == F + 33 else PUR)
    bp.set(cx, F + 41, cz, ROD_UP)
    # the chest under the great bell, the spawner beside the colonnade
    bp.chest(cx + round(tz * 2), F, cz - round(tx * 2), face_in(cx + round(tz * 2), cz - round(tx * 2), cx, cz),
             loot=LOOT + "halo_bell")
    bp.spawner(cx - round(tz * 6), F, cz + round(tx * 6), "minecraft:shulker")
    # floor of the shrine: a gilded rose round the bell's mouth
    for (x, z) in disk_pts(cx, cz, 8):
        d = math.hypot(x - cx, z - cz)
        ang = math.degrees(math.atan2(z - cz, x - cx)) % 30
        bp.set(x, F - 1, z, GOLD if 4.2 < d <= 5.0 else (PUR if ang < 4 else ESB))
    for (x, z) in ring_pts(cx, cz, 7):
        if hash01(x, z, 692) < 0.12:
            candles(bp, x, F, z, 2, "white")


# ------------------------------------------------------------------ temple E: the gate
GATE_C = None


def gate(bp, arc):
    cx, cz = plaza_c(arc)
    F = plaza_h(arc)
    X0, X1, Z0, Z1, HH = cx - 8, cx + 8, cz - 8, cz + 8, 16
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            wall = x in (X0, X1) or z in (Z0, Z1)
            for y in range(F, F + HH):
                if wall:
                    bp.set(x, y, z, GOLD if y in (F + 5, F + HH - 1) else WALL_E.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
            bp.set(x, F + HH, z, VB)
            if not wall:
                bp.set(x, F - 1, z, PUR if abs(z - cz) <= 1 or abs(x - cx) <= 1 else
                       ("polished_blackstone_bricks" if (x + z) % 2 else VB))
                if (x - cx) % 4 == 0 and (z - cz) % 4 == 0:
                    bp.set(x, F + HH - 1, z, GOLD)
    # crenellated roof
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            if x in (X0, X1) or z in (Z0, Z1):
                bp.set(x, F + HH + 1, z, VB_WA if (x + z) % 2 else VB)
    # buttresses on the outer (east) face
    for bz in (cz - 6, cz, cz + 6):
        for i, h in enumerate((14, 10, 6)):
            x = X1 + 1 + i
            for z in (bz - 1, bz, bz + 1):
                for y in range(F - 1, F + h):
                    bp.set(x, y, z, OBS if hash3(x, y, z, 700) < 0.6 else VB)
                bp.set(x, F + h, z, stair(VB_ST, "west"))
    # columns inside
    for (dx, dz) in ((-4, -4), (-4, 3), (3, -4), (3, 3)):
        for x in (cx + dx, cx + dx + 1):
            for z in (cz + dz, cz + dz + 1):
                for y in range(F, F + HH):
                    bp.set(x, y, z, GOLD if y in (F, F + HH - 1) else PUR_P)
    # doors north and south (the ring route), 3 wide and 5 high, framed
    for zz, f in ((Z0, "north"), (Z1, "south")):
        for x in range(cx - 1, cx + 2):
            for y in range(F, F + 5):
                bp.set(x, y, zz, "air")
        for x in (cx - 2, cx + 2):
            for y in range(F, F + 6):
                bp.set(x, y, zz, PUR_P if y < F + 5 else GOLD)
        for x in range(cx - 1, cx + 2):
            bp.set(x, F + 5, zz, GOLD if x == cx else PUR)
    # the pylons and the great portal to the west (toward the centre)
    for pz0 in (cz - 9, cz + 5):
        for x in range(X0 - 4, X0 + 1):
            for z in range(pz0, pz0 + 5):
                for y in range(F - 2, F + 30):
                    lvl = y - F
                    shrink = 0 if lvl < 22 else (1 if lvl < 27 else 2)
                    if not (X0 - 4 + shrink <= x <= X0 - shrink and pz0 + shrink <= z <= pz0 + 4 - shrink):
                        continue
                    edge = x in (X0 - 4 + shrink, X0 - shrink) or z in (pz0 + shrink, pz0 + 4 - shrink)
                    bp.set(x, y, z, GOLD if lvl in (6, 14, 21) else (WALL_E.pick(x, y, z) if edge else OBS))
        tx, tz = X0 - 2, pz0 + 2
        bp.set(tx, F + 30, tz, GOLD)
        bp.set(tx, F + 31, tz, ROD_UP)
        for dz in (-1, 1):
            bp.set(tx - 3, F + 12, tz + dz, "end_rod[facing=west]")
    # the portal: 7 wide x 14 high in the west wall, a screen of glass with an open wicket and a gilded eye
    for z in range(cz - 3, cz + 4):
        for y in range(F, F + 14):
            arch_top = F + 14 - (1 if abs(z - cz) == 3 else 0)
            if y >= arch_top:
                continue
            wicket = abs(z - cz) <= 1 and y < F + 4
            bp.set(X0, y, z, "air" if wicket else "purple_stained_glass_pane")
        bp.set(X0 - 1, F + 14, z, GOLD)
    for z in range(cz - 3, cz + 4):
        bp.set(X0, F + 14, z, GOLD)
    for (dz, dy) in ((0, 2), (2, 0), (0, -2), (-2, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        bp.set(X0, F + 9 + dy, cz + dz, GOLD)
    bp.set(X0, F + 9, cz, STAR)
    for z in range(cz - 1, cz + 2):
        bp.set(X0, F + 4, z, GOLD if z == cz else PUR)
    # the passage between the pylons out to the radial bridge
    for x in range(X0 - 4, X0):
        for z in range(cz - 4, cz + 5):
            bp.set(x, F - 1, z, PUR if abs(z - cz) <= 1 else ESB)
            for y in range(F, F + 4):
                bp.set(x, y, z, "air")
    # furnishing: chest guarded by an enderman spawner, banners, rods on the columns, a hanging chandelier
    bp.chest(cx + 6, F, cz + 2, "west", loot=LOOT + "halo_gate")
    bp.spawner(cx + 5, F, cz - 1, "brasshaven:void_acolyte")
    for (dx, dz) in ((-4, -4), (-4, 3), (3, -4), (3, 3)):
        bp.set(cx + dx - 1, F + 8, cz + dz, "end_rod[facing=west]")
        bp.set(cx + dx + 2, F + 8, cz + dz + 1, "end_rod[facing=east]")
    hang_star(bp, cx, F + HH - 1, cz, 5, light=FROG)
    for z in (Z0 + 1, Z1 - 1):
        for x in (X1 - 2, X1 - 5):
            bp.set(x, F + 7, z, f"purple_wall_banner[facing={'south' if z == Z0 + 1 else 'north'}]")
    global GATE_C
    GATE_C = (cx, cz, F, X0)


# ------------------------------------------------------------------ the radial bridge, grace, arena, vault
def radial(bp):
    cx, cz, F, X0 = GATE_C
    gx, gz = GRACE
    GF = ARENA_Y + 1
    # gate -> grace islet
    walkway(bp, [(X0 - 4, float(F), 0), (gx + 5, float(GF), 0)], width=5, style="stone", rise=1.0)
    # the islet of the site of grace
    cols = rock_lobe(gx, GF - 1, gz, 6.5, 6.0, 12, 710, spikes=4)
    build_rock(bp, cols, 710, surface="end_stone")
    for (x, z) in disk_pts(gx, gz, 6):
        if (x, z) in cols:
            d = math.hypot(x - gx, z - gz)
            bp.set(x, GF - 1, z, PUR if abs(z - gz) <= 1 else (GOLD if 5.0 < d <= 5.9 else PAVE.pick(x, 0, z)))
    wx, wz = gx, gz - 4
    bp.set(wx, GF, wz, MOD["waystone"])
    for (dx, dz) in ((1, 0), (-1, 0), (0, -1)):
        bp.set(wx + dx, GF - 1, wz + dz, GOLD)
    for x in (gx - 3, gx + 3):
        brazier(bp, x, GF, gz + 4, h=2)
    bp.set(gx - 1, GF, gz + 4, stair(PUR_ST, "north"))
    bp.set(gx + 1, GF, gz + 4, stair(PUR_ST, "north"))
    # grace -> portico -> arena
    walkway(bp, [(gx - 5, float(GF), 0), (27, float(ARENA_Y), 0)], width=5, style="stone", rise=0.5)
    for x in range(17, 28):
        for z in range(-2, 3):
            bp.set(x, ARENA_Y - 1, z, PUR if z == 0 else ESB)
            bp.set(x, ARENA_Y - 2, z, VB)
            for y in range(ARENA_Y, ARENA_Y + 5):
                bp.set(x, y, z, "air")
    # the portico: 5 wide, 5 high, 8 long, purpur walls with rods, a gilded ridge; the mist at its arena mouth
    for x in range(18, 27):
        for z in (-3, 3):
            for y in range(ARENA_Y - 1, ARENA_Y + 5):
                bp.set(x, y, z, PUR_P if x in (18, 22, 26) else (WALL_A.pick(x, y, z) if y > ARENA_Y - 1 else VB))
            if x in (20, 24):
                bp.set(x, ARENA_Y + 3, z - (1 if z > 0 else -1), f"end_rod[facing={'north' if z > 0 else 'south'}]")
        for z in range(-4, 5):
            if abs(z) == 4:
                bp.set(x, ARENA_Y + 5, z, stair(PUR_ST, "north" if z > 0 else "south", "top"))
                continue
            bp.set(x, ARENA_Y + 5, z, PUR)
            bp.set(x, ARENA_Y + 6, z, GOLD if z == 0 else stair(PUR_ST, "north" if z > 0 else "south"))
    bp.mist(18, ARENA_Y, -2, 18, ARENA_Y + 4, 2)


def arena(bp):
    fy = ARENA_Y - 1
    # the disc: concentric rings, a gilded halo inlay, a sun at the centre; a deep cone underneath
    for x in range(-19, 20):
        for z in range(-19, 20):
            d = math.hypot(x, z)
            if d > ARENA_R + 1.4:
                continue
            ang = math.degrees(math.atan2(z, x)) % 30
            if d <= 1.6:
                spec = GOLD
            elif d <= 2.6:
                spec = STAR
            elif 11.5 < d <= 12.4:
                spec = GOLD
            elif ang < 2.5 and d > 3:
                spec = PUR
            elif d > ARENA_R + 0.4:
                spec = PUR
            else:
                spec = VB if int(d) % 4 == 0 else ESB
            bp.set(x, fy, z, spec)
            depth = 3 + 22 * max(0.0, 1 - d / (ARENA_R + 1.6)) ** 1.3 + 2.0 * hash01(x, z, 720)
            for y in range(fy - round(depth), fy):
                hb = y - (fy - round(depth))
                if d > ARENA_R + 0.4 and y > fy - 3:
                    s2 = GOLD if y == fy - 1 else PUR
                elif hb < 2:
                    s2 = KEEL.pick(x, y, z)
                elif d > ARENA_R - 1:
                    s2 = FACE.pick(x, y, z)
                else:
                    s2 = "end_stone" if hb > 3 else VB
                bp.set(x, y, z, s2)
            if hash01(x, z, 721) < 0.06 and d > 3:
                bp.set(x, fy - round(depth) - 1, z, ROD_DOWN)
    # the spike under the disc
    for y in range(fy - 34, fy - 24):
        r2 = (y - (fy - 34)) / 10 * 2.2
        for (x, z) in disk_pts(0, 0, r2):
            bp.set(x, y, z, OBS if hash3(x, y, z, 722) < 0.7 else CRY)
    bp.chain(0, fy - 40, 0, fy - 35)
    bp.set(0, fy - 41, 0, FROG)
    # the low parapet at r 17, broken in three places, with rod posts; gaps for the two doors
    for (x, z) in ring_pts(0, 0, ARENA_R + 1):
        a = math.degrees(math.atan2(z, x)) % 360
        if abs(z) <= 2:
            continue
        if any(abs(wrap(a - g)) < 6 for g in (62, 205, 300)):
            continue
        post = round(a) % 20 < 3
        bp.set(x, ARENA_Y, z, PUR_P if post else ESB_WA)
        if post:
            bp.set(x, ARENA_Y + 1, z, ROD_UP)
    # the frame: shards of a smaller ring floating round the disc at different heights and tilts
    for k, (a0, span, r0, y0, tilt) in enumerate(((35, 30, 24, 52, 0.18), (85, 34, 26, 60, -0.12),
                                                   (135, 28, 23, 49, 0.22), (225, 32, 25, 57, -0.2),
                                                   (275, 26, 27, 64, 0.15), (322, 24, 23, 50, -0.16))):
        n = int(span * 2)
        for i in range(n + 1):
            a = rad(a0 - span / 2 + span * i / n)
            for dr in (-1, 0, 1, 2):
                rr = r0 + dr
                x, z = round(rr * math.cos(a)), round(rr * math.sin(a))
                yc = y0 + tilt * rr * (a - rad(a0))
                yy = round(yc)
                for y in range(yy - 2, yy + 1):
                    if y == yy:
                        spec = GOLD if dr == 2 else ESB
                    elif y == yy - 2:
                        spec = OBS
                    else:
                        spec = FACE.pick(x, y, z)
                    bp.set(x, y, z, spec)
                if dr == 0 and i % 5 == 0:
                    bp.set(x, yy - 3, z, ROD_DOWN)
                if dr == 2 and i % 4 == 2:
                    bp.set(x, yy + 1, z, ROD_UP)
    # four light pylons on the parapet line, between the shards
    for a in (45, 135, 225, 315):
        x, z = round(18.5 * math.cos(rad(a))), round(18.5 * math.sin(rad(a)))
        for y in range(ARENA_Y - 1, ARENA_Y + 4):
            bp.set(x, y, z, PUR_P if y < ARENA_Y + 3 else GOLD)
        bp.set(x, ARENA_Y + 4, z, ROD_UP)
        for y in range(ARENA_Y - 6, ARENA_Y - 1):
            bp.set(x, y, z, FACE.pick(x, y, z))
    crown(bp)
    bp.boss_seal(0, fy, 0, BOSS, ARENA_R - 1)


def crown(bp):
    """The landmark over the arena: a small tilted halo of gold and purpur floating 34 above the disc, broken in
    three, hung with end rods; it is seen from every arc."""
    cy, rr, tilt = ARENA_Y + 34, 15.0, rad(24)
    u = (1.0, 0.0, 0.0)
    v = (0.0, math.sin(tilt), math.cos(tilt))
    n = int(2 * math.pi * rr * 3)
    for i in range(n):
        t = 2 * math.pi * i / n
        deg = math.degrees(t) % 360
        if any(abs(wrap(deg - g)) < 9 for g in (20, 150, 260)):
            continue
        p = [rr * (math.cos(t) * u[j] + math.sin(t) * v[j]) for j in range(3)]
        x, y, z = round(p[0]), round(cy + p[1]), round(p[2])
        for (dx, dy, dz) in ((0, 0, 0), (0, 1, 0)):
            bp.set(x + dx, y + dy, z + dz, GOLD if dy == 1 else PUR)
        if i % 7 == 0:
            bp.set(x, y - 1, z, ROD_DOWN)
        elif i % 7 == 3:
            bp.set(x, y + 2, z, ROD_UP)


def vault(bp):
    vx, vz = VAULT
    VF = ARENA_Y
    # the west exit: mist at the arena edge, a short bridge
    for x in range(-27, -16):
        for z in range(-1, 2):
            bp.set(x, VF - 1, z, PUR if z == 0 else ESB)
            bp.set(x, VF - 2, z, VB)
            for y in range(VF, VF + 4):
                bp.set(x, y, z, "air")
        for z in (-2, 2):
            bp.set(x, VF - 1, z, VB)
            bp.set(x, VF, z, PUR_P if x in (-18, -27) else ESB_WA)
        if x % 3 == 0:
            bp.set(x, VF - 3, 0, ROD_DOWN)
    for z in (-2, 2):
        for y in range(VF, VF + 5):
            bp.set(-18, y, z, PUR_P if y < VF + 4 else GOLD)
    for z in range(-1, 2):
        bp.set(-18, VF + 4, z, GOLD)
    bp.mist(-18, VF, -1, -18, VF + 3, 1)
    # the islet and its domed treasury, the door barred by sealed bars that open when the boss falls
    cols = rock_lobe(vx, VF - 1, vz, 8.5, 8.0, 14, 730, spikes=5)
    build_rock(bp, cols, 730, surface="end_stone")
    for (x, z) in disk_pts(vx, vz, 7.5):
        if (x, z) in cols:
            bp.set(x, VF - 1, z, PAVE.pick(x, 0, z))
    for (x, z) in ring_pts(vx, vz, 6):
        for y in range(VF, VF + 7):
            bp.set(x, y, z, GOLD if y == VF + 6 else (WALL_A.pick(x, y, z) if y > VF else ESB))
    for (x, z) in disk_pts(vx, vz, 5):
        for y in range(VF, VF + 7):
            bp.set(x, y, z, "air")
        d = math.hypot(x - vx, z - vz)
        bp.set(x, VF - 1, z, GOLD if d < 1.5 or 3.5 < d <= 4.4 else PUR)
    for x in range(vx - 7, vx + 8):
        for z in range(vz - 7, vz + 8):
            for y in range(VF + 7, VF + 14):
                d = math.sqrt((x - vx) ** 2 + (z - vz) ** 2 + ((y - VF - 7) * 1.2) ** 2)
                if 5.2 < d <= 6.4:
                    rib = (round(math.degrees(math.atan2(z - vz, x - vx))) % 60) < 6
                    bp.set(x, y, z, GOLD if rib else PUR)
                elif d <= 5.2:
                    bp.set(x, y, z, "air")
    top = max(y for y in range(VF + 7, VF + 16) if bp.get(vx, y, vz) is not None and bp.get(vx, y, vz) != "minecraft:air")
    bp.set(vx, top + 1, vz, ROD_UP)
    for z in range(vz - 1, vz + 2):
        for y in range(VF, VF + 4):
            bp.set(vx + 6, y, z, MOD["vault_bars"])
    for z in (vz - 2, vz + 2):
        for y in range(VF, VF + 5):
            bp.set(vx + 6, y, z, PUR_P if y < VF + 4 else GOLD)
    for z in range(vz - 1, vz + 2):
        bp.set(vx + 6, VF + 4, z, GOLD)
    # the hoard: two chests, gold, a dragon's head on a gilded plinth, amethyst
    bp.chest(vx - 3, VF, vz - 2, "east", loot=LOOT + "halo_vault")
    bp.chest(vx - 3, VF, vz + 2, "east", loot=LOOT + "halo_vault")
    bp.set(vx - 4, VF, vz, GOLD)
    bp.set(vx - 4, VF + 1, vz, "dragon_head[powered=false,rotation=12]")
    for (x, z) in ((vx - 2, vz - 4), (vx - 2, vz + 4), (vx + 2, vz - 4), (vx + 2, vz + 4), (vx - 4, vz - 2),
                   (vx - 4, vz + 2)):
        if bp.get(x, VF, z) in (None, "minecraft:air"):
            bp.set(x, VF, z, "raw_gold_block" if (x + z) % 2 else "amethyst_block")
            bp.set(x, VF + 1, z, "amethyst_cluster[facing=up,waterlogged=false]")
    hang_star(bp, vx, VF + 11, vz, 4, light=FROG)


# ------------------------------------------------------------------ the whole site
def shattered_halo(bp):
    cols = arc_columns()
    build_ring(bp, cols)
    debris(bp)
    arrival(bp)
    observatory(bp, ARCS[0])
    library(bp, ARCS[1])
    reliquary(bp, ARCS[2])
    bell_shrine(bp, ARCS[3])
    gate(bp, ARCS[4])
    bridges(bp)
    radial(bp)
    arena(bp)
    vault(bp)


def _view_pts():
    A, B, C, D, E = ARCS
    ax, az = plaza_c(A)
    bx, bz = plaza_c(B)
    ex, ez = plaza_c(E)
    p0 = arc_point(A, A["tc"] + HALF - 4)
    p1 = arc_point(B, B["tc"] - HALF + 4)
    mx, my, mz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 2.0, (p0[2] + p1[2]) / 2
    return [
        ("arrival", (ISLET[0] + 2, int(ISLET_FEET), ISLET[1] + 1), (0, ARENA_Y + 10, 0)),
        ("light_bridge", (round(mx), math.ceil(my), round(mz)), (round(p1[0]), round(p1[1]) + 2, round(p1[2]))),
        ("observatory", (ax + round(math.cos(rad(A["tc"] + 90)) * 5), plaza_h(A),
                         az + round(math.sin(rad(A["tc"] + 90)) * 5)), (ax, plaza_h(A) + 6, az)),
        ("library", (bx + 3, plaza_h(B), bz - 5), (bx - 4, plaza_h(B) + 8, bz + 3)),
        ("grace", (GRACE[0] + 4, ARENA_Y + 1, GRACE[1] + 2), (GRACE[0], ARENA_Y + 2, GRACE[1] - 4)),
        ("arena", (16, ARENA_Y, 0), (-10, ARENA_Y + 6, 0)),
        ("gate", (ex + 7, plaza_h(E), ez), (ex - 8, plaza_h(E) + 9, ez)),
    ]


VIEWS = _view_pts()


register(StructureDef(
    "shattered_halo", "end", OUTER_END,
    [Piece("halo", shattered_halo, views=VIEWS)],
    spacing=40, separation=14, adaptation="none", height=("uniform", 30, 40), processors="none", max_distance=116,
    ground=ARENA_Y - 1,
    spawns=[("minecraft:enderman", 10, 1, 2), (MOB["void_stalker"], 5, 1, 2), ("brasshaven:void_acolyte", 6, 1, 2)],
    title_fr="Halo brisé", title_en="Shattered Halo"))

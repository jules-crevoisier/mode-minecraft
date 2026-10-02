"""Overworld structures (group B): world tree, sky archipelago, jungle ziggurat, desert caravanserai,
swamp witch hamlet."""
import math
import random

from .. import arch
from ..arch import Palette, slab, stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import LOOT, MOB, MOD, leaves

TEMPERATE = ["#minecraft:is_forest", "plains", "sunflower_plains", "meadow", "#minecraft:is_taiga",
             "savanna", "cherry_grove"]


# ============================================================ shared helpers
def _card(dx, dz):
    """Cardinal direction closest to the vector (dx, dz)."""
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def _lvs(name):
    return f"{name}[distance=1,persistent=true,waterlogged=false]"


def _is_leaf(bp, x, y, z):
    b = bp.get(x, y, z)
    return b is not None and b.endswith("_leaves")


def _strip_leaves(bp, x0, y0, z0, x1, y1, z1):
    """Remove leaves (back to structure void) inside a box: makes room for decks and houses."""
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                b = bp.get(x, y, z)
                if b and (b.endswith("_leaves") or b.endswith("vine") or b == "minecraft:shroomlight"):
                    bp.remove(x, y, z)


def _limb(bp, p0, p1, r0, r1, block):
    """Thick tapered branch from p0 to p1 (spheres swept along the segment)."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        cx, cy, cz = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
        r = r0 + (r1 - r0) * t
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r + 0.35:
                        bp.set(round(cx) + dx, round(cy) + dy, round(cz) + dz, block)


def _cluster(bp, cx, cy, cz, rx, ry, rz, pal, seed, glow=None, glow_chance=0.025):
    """Lumpy leaf cluster: domed top, flatter underside, coherent leaf mix, glowing heart."""
    rng = random.Random(seed)
    for x in range(cx - rx - 1, cx + rx + 2):
        for y in range(cy - ry - 1, cy + ry + 2):
            for z in range(cz - rz - 1, cz + rz + 2):
                dy = (y - cy) / (ry if y >= cy else ry * 0.65)
                d = ((x - cx) / rx) ** 2 + dy ** 2 + ((z - cz) / rz) ** 2
                lump = 0.22 * math.sin(x * 0.9 + seed) * math.cos(z * 0.8 - y * 0.6) + rng.uniform(-0.1, 0.1)
                if d <= 1 + lump:
                    if glow and d < 0.45 and rng.random() < glow_chance:
                        bp.set(x, y, z, glow, keep=True)
                    else:
                        bp.set(x, y, z, pal.pick(x, y, z), keep=True)


def _hang_under(bp, region, chance, seed, kinds, on=None):
    """Hang strands (vines / hanging moss / glow berries / roots) under blocks in a region.
    `on`: only under blocks whose id contains one of these substrings."""
    rng = random.Random(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    for (x, y, z), b in list(bp.blocks.items()):
        if not (x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1) or b[0] == "minecraft:air":
            continue
        if on and not any(s in b[0] for s in on):
            continue
        if bp.get(x, y - 1, z) is not None or rng.random() > chance:
            continue
        kind = rng.choice(kinds)
        n = rng.randint(2, 6)
        for k in range(1, n + 1):
            if bp.get(x, y - k, z) is not None:
                break
            last = k == n or bp.get(x, y - k - 1, z) is not None
            if kind == "vine":
                bp.set(x, y - k, z, "vine[up=true]" if k == 1 else "vine[north=true]")
            elif kind == "moss":
                bp.set(x, y - k, z, f"pale_hanging_moss[tip={'true' if last else 'false'}]")
            elif kind == "berries":
                if last:
                    bp.set(x, y - k, z, f"cave_vines[age=25,berries={'true' if rng.random() < 0.6 else 'false'}]")
                else:
                    bp.set(x, y - k, z, f"cave_vines_plant[berries={'true' if rng.random() < 0.35 else 'false'}]")
            elif kind == "roots":
                bp.set(x, y - k, z, "hanging_roots[waterlogged=false]")
                break


def _gable(bp, x0, z0, x1, z1, y, stairs, full, gable, axis="x", overhang=1, steep=1, under=None):
    """Gable roof whose slope (stairs/full) and gable ends (`gable`) use different blocks."""
    if axis == "x":
        lo, hi, a0, a1 = z0 - overhang, z1 + overhang, x0 - overhang, x1 + overhang
    else:
        lo, hi, a0, a1 = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang

    def P(a, b, yy):
        return (a, yy, b) if axis == "x" else (b, yy, a)

    up_lo, up_hi = ("south", "north") if axis == "x" else ("east", "west")
    ends = (x0, x1) if axis == "x" else (z0, z1)
    yy, i = y, 0
    while lo + i <= hi - i:
        for k in range(steep):
            for a in range(a0, a1 + 1):
                if lo + i == hi - i:
                    bp.set(*P(a, lo + i, yy), slab(stairs.replace("_stairs", "_slab")) if k == steep - 1 else full)
                else:
                    for b, f in ((lo + i, up_lo), (hi - i, up_hi)):
                        bp.set(*P(a, b, yy), stair(stairs, f) if k == steep - 1 else full)
            for b in range(lo + i + 1, hi - i):
                for a in ends:
                    bp.set(*P(a, b, yy), gable)
            yy += 1
        i += 1
    if under:
        for a in range(a0, a1 + 1):
            bp.set(*P(a, lo, y - 1), stair(under, up_hi, "top"))
            bp.set(*P(a, hi, y - 1), stair(under, up_lo, "top"))
    return yy


def _bridge(bp, a, b, wood, sag=1, width=3, rail="fence", posts=5, clear_leaves=True, slab_block=None,
            edge=None, post=None, under=True, piles=None, soul=False, gaps=0.0, seed=0):
    """Bridge from deck block a to deck block b ((x, y, z)), sagging in the middle. The walking surface
    is quantised to half blocks (bottom/top slabs) so slopes need no jumping. rail: 'fence' or 'chain'."""
    (ax, ay, az), (bx, by, bz) = a, b
    n = max(abs(bx - ax), abs(bz - az), 1)
    along_x = abs(bx - ax) >= abs(bz - az)
    half = width // 2
    sb = slab_block or f"{wood}_slab"
    edge = edge or f"{wood}_planks"
    post = post or f"{wood}_fence"
    rng = random.Random(seed)
    for i in range(n + 1):
        t = i / n
        x = round(ax + (bx - ax) * t)
        z = round(az + (bz - az) * t)
        q = round(((ay + 1) + (by - ay) * t - sag * 4 * t * (1 - t)) * 2) / 2
        if q == int(q):
            y, kind = int(q) - 1, "top"
        else:
            y, kind = int(math.floor(q)), "bottom"
        for w in range(-half - 1, half + 2):
            px, pz = (x, z + w) if along_x else (x + w, z)
            if clear_leaves:
                _strip_leaves(bp, px, y, pz, px, y + 3, pz)
            if abs(w) <= half:
                if gaps and 0 < i < n and rng.random() < gaps:
                    continue                      # rotten plank
                bp.set(px, y, pz, slab(sb, kind))
                continue
            bp.set(px, y, pz, edge)
            if rail == "chain":
                bp.set(px, y + 1, pz, f"iron_chain[axis={'x' if along_x else 'z'},waterlogged=false]")
            else:
                bp.set(px, y + 1, pz, post)
            if 0 < i < n and i % posts == 0:
                bp.set(px, y + 1, pz, post)
                bp.set(px, y + 2, pz, post)
                bp.lantern(px, y + 3, pz, soul=soul)
                if piles:
                    bp.fill(px, y - 4, pz, px, y - 1, pz, piles)
                elif under:
                    bp.chain(px, y - 2, pz, y - 1)
                    bp.lantern(px, y - 3, pz, hanging=True, soul=soul)
    return n


def _cabin(bp, cx, cz, y, w, d, wood, roof_stairs, roof_full, door, *, axis=None, steep=1, seed=0,
           interior=None, loot=None, frame=None):
    """Timber cabin (floor at y) with log frame, framed windows and a steep overhanging roof."""
    rng = random.Random(seed)
    x0, z0 = cx - w // 2, cz - d // 2
    x1, z1 = x0 + w - 1, z0 + d - 1
    planks = f"{wood}_planks"
    frame = frame or f"stripped_{wood}_log"
    axis = axis or ("x" if w >= d else "z")
    roof_h = ((d if axis == "x" else w) + 2) // 2 * steep + 1
    _strip_leaves(bp, x0 - 2, y, z0 - 2, x1 + 2, y + 6 + roof_h, z1 + 2)
    bp.fill(x0, y, z0, x1, y, z1, planks)
    bp.clear(x0 + 1, y + 1, z0 + 1, x1 - 1, y + 4 + roof_h, z1 - 1)
    bp.walls(x0, y + 1, z0, x1, y + 3, z1, planks)
    for x in range(x0, x1 + 1):
        bp.set(x, y + 4, z0, with_props(frame, axis="x"))
        bp.set(x, y + 4, z1, with_props(frame, axis="x"))
    for z in range(z0, z1 + 1):
        bp.set(x0, y + 4, z, with_props(frame, axis="z"))
        bp.set(x1, y + 4, z, with_props(frame, axis="z"))
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        bp.fill(x, y, z, x, y + 4, z, with_props(frame, axis="y"))
    # windows (centre of every wall), with a stair sill outside
    for face, (wx, wz) in (("north", ((x0 + x1) // 2, z0)), ("south", ((x0 + x1) // 2, z1)),
                           ("west", (x0, (z0 + z1) // 2)), ("east", (x1, (z0 + z1) // 2))):
        if face == door:
            continue
        bp.fill(wx, y + 2, wz, wx, y + 3, wz, "glass_pane")
        ox, oz = arch.FACE_VEC[face]
        bp.set(wx + ox, y + 1, wz + oz, stair(f"{wood}_stairs", arch.OPPOSITE[face], "top"))
        if rng.random() < 0.6:
            bp.set(wx + ox, y + 2, wz + oz, rng.choice(["potted_red_mushroom", "potted_fern", "potted_poppy",
                                                         "potted_azure_bluet", "potted_brown_mushroom"]))
    # door + porch lantern
    dx_, dz_ = {"north": ((x0 + x1) // 2, z0), "south": ((x0 + x1) // 2, z1),
                "west": (x0, (z0 + z1) // 2), "east": (x1, (z0 + z1) // 2)}[door]
    bp.door(dx_, y + 1, dz_, door, wood)
    ox, oz = arch.FACE_VEC[door]
    sx, sz = (1, 0) if door in ("north", "south") else (0, 1)
    bp.lantern(dx_ + ox + sx, y + 1, dz_ + oz + sz)
    # roof
    _gable(bp, x0, z0, x1, z1, y + 5, roof_stairs, roof_full, planks, axis=axis, overhang=1, steep=steep,
           under=f"{wood}_stairs")
    bp.lantern((x0 + x1) // 2, y + 4, (z0 + z1) // 2, hanging=True)
    # interior
    ix0, iz0, ix1, iz1 = x0 + 1, z0 + 1, x1 - 1, z1 - 1
    if interior == "bed":
        bp.bed(ix0, y + 1, iz0, "south", rng.choice(["green", "lime", "brown", "red"]))
        bp.set(ix1, y + 1, iz0, "barrel[facing=up,open=false]")
        bp.set(ix1, y + 2, iz0, "candle[candles=2,lit=true,waterlogged=false]")
    elif interior == "study":
        bp.set(ix0, y + 1, iz0, "bookshelf")
        bp.set(ix0, y + 2, iz0, "bookshelf")
        bp.set(ix1, y + 1, iz0, "cartography_table")
        bp.set(ix0, y + 1, iz1, "lectern[facing=east,has_book=false,powered=false]")
    elif interior == "kitchen":
        bp.set(ix0, y + 1, iz0, "smoker[facing=south,lit=false]")
        bp.set(ix0 + 1, y + 1, iz0, "crafting_table")
        bp.set(ix1, y + 1, iz1, "composter[level=4]")
    if loot:
        bp.chest(ix1, y + 1, iz1 if interior != "kitchen" else iz0, "west", loot)
    return x0, z0, x1, z1


# ============================================================ Giant world tree
def _trunk_base(y):
    """Mean trunk radius at height y (flared foot, tapering top)."""
    if y < 8:
        return 6.5 + (8 - y) * 0.38
    if y < 34:
        return 6.5
    return max(4.6, 6.5 - (y - 34) * 0.12)


def _trunk_r(y, a):
    """Radius including the fluted bark ridges (always >= the base radius)."""
    return _trunk_base(y) + 0.75 * (1 + math.sin(5 * a + y * 0.07)) * 0.6 + 0.5 * (1 + math.sin(3 * a + 1.3)) * 0.5


def _in_sector(a, s0, s1):
    a = math.degrees(a) % 360
    s0, s1 = s0 % 360, s1 % 360
    return s0 <= a <= s1 if s0 <= s1 else (a >= s0 or a <= s1)


def _polar(r, deg):
    a = math.radians(deg)
    return round(math.cos(a) * r), round(math.sin(a) * r)


def giant_tree(v):
    """v: variant dict (log, wood, leaves, deck wood, roof tiles)."""

    def build(bp):
        rng = random.Random(v["seed"])
        LOG = f"{v['log']}[axis=y]"
        BARK = f"{v['wood']}[axis=y]"
        bark = Palette({LOG: 5, BARK: 2}, seed=v["seed"], scale=2.5)
        deck = v["deck"]
        TOP = 48            # trunk top: crown deck
        LEVELS = (10, 22, 34)

        # ---------------------------------------------------------------- ground: forest floor
        floor_pal = Palette({"podzol[snowy=false]": 3, "coarse_dirt": 2, "moss_block": 2, "rooted_dirt": 1,
                             "grass_block[snowy=false]": 3}, seed=3, scale=3.0)
        for x in range(-27, 28):
            for z in range(-27, 28):
                d = math.hypot(x, z)
                if d <= 24 + 3 * math.sin(math.atan2(z, x) * 4 + 1):
                    bp.set(x, 0, z, floor_pal.pick(x, 0, z))
                    bp.set(x, -1, z, "dirt")

        # ---------------------------------------------------------------- buttress roots
        root_angles = [195, 228, 262, 296, 330, 4, 38, 63]
        for k, ang in enumerate(root_angles):
            ln = rng.randint(14, 17)
            a = math.radians(ang + rng.uniform(-6, 6))
            s = 0.0
            while s <= ln:
                t = s / ln
                aa = a + 0.18 * math.sin(s * 0.35 + k)
                r = _trunk_base(0) - 1.5 + s
                px, pz = math.cos(aa) * r, math.sin(aa) * r
                h = 8 * (1 - t) ** 2.2 + 0.4
                w = 1.3 * (1 - t) + 0.55
                wi = int(math.ceil(w))
                for dx in range(-wi, wi + 1):
                    for dz in range(-wi, wi + 1):
                        if dx * dx + dz * dz <= w * w:
                            x, z = round(px + dx), round(pz + dz)
                            top = round(h)
                            for y in range(-2, max(0, top) + 1):
                                bp.set(x, y, z, BARK)
                            if top >= 1 and rng.random() < 0.12:
                                bp.set(x, top + 1, z, "moss_carpet", keep=True)
                s += 0.5

        # ---------------------------------------------------------------- hollow fluted trunk
        for y in range(-6, TOP + 1):
            R = _trunk_base(y) + 1.6
            Ri = int(R) + 2
            inner = _trunk_base(y) - 1.8
            for x in range(-Ri, Ri + 1):
                for z in range(-Ri, Ri + 1):
                    d = math.hypot(x, z)
                    a = math.atan2(z, x)
                    if d <= _trunk_r(y, a):
                        if d <= inner and 1 <= y < TOP:
                            bp.set(x, y, z, "air")
                        elif d <= inner and y == 0:
                            bp.set(x, y, z, f"{deck}_planks")
                        else:
                            bp.set(x, y, z, bark.pick(x, y, z))

        # ---------------------------------------------------------------- root cellar (secret)
        bp.room(-4, -7, -4, 4, -1, 4, "rooted_dirt", floor="packed_mud", ceiling=None)
        for x in range(-3, 4):
            for z in range(-3, 4):
                if rng.random() < 0.3:
                    bp.set(x, -2, z, "hanging_roots[waterlogged=false]")
        for x, z in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            bp.fill(x, -6, z, x, -2, z, LOG)
        bp.chest(-3, -6, 0, "east", LOOT + "giant_tree")
        bp.barrel(-3, -6, 1, "up")
        bp.set(-3, -5, 1, "candle[candles=3,lit=true,waterlogged=false]")
        bp.spawner(2, -6, 2, "minecraft:spider")
        bp.set(0, -6, -3, "decorated_pot[facing=south,waterlogged=false,cracked=true]")
        bp.lantern(0, -2, 0, hanging=True, soul=True)
        bp.set(0, -1, 0, LOG)
        # hatch: a trapdoor hidden under the stair column's foot, ladder down
        bp.set(3, 0, -1, f"{deck}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")
        bp.ladder(3, -6, -1, -1, "west")
        bp.fill(4, -6, -1, 4, -1, -1, "rooted_dirt")

        # ---------------------------------------------------------------- interior: spiral stair + floors
        for x in range(-2, 3):
            for z in range(-2, 3):
                if max(abs(x), abs(z)) == 2:
                    bp.set(x, TOP, z, "air")
        bp.spiral_stairs(0, 0, 1, TOP, 2, f"{deck}_slab", center=LOG)
        for y in range(4, TOP, 6):
            bp.set(0, y, 0, "shroomlight")
        for L in LEVELS:
            inner = _trunk_base(L) - 1.8
            for x in range(-8, 9):
                for z in range(-8, 9):
                    if max(abs(x), abs(z)) >= 3 and math.hypot(x, z) <= inner + 0.3:
                        bp.set(x, L, z, f"{deck}_planks")
            # hanging lanterns under each floor
            for ang in (45, 135, 225, 315):
                lx, lz = _polar(3.9, ang)
                bp.chain(lx, L - 1, lz, L - 1)
                bp.lantern(lx, L - 2, lz, hanging=True)
        # ground hall furniture around the wall
        hall = [(20, "crafting_table"), (40, "furnace[facing=west,lit=true]"), (60, "barrel[facing=up,open=false]"),
                (130, "bookshelf"), (145, "bookshelf"), (200, "smithing_table"), (240, "cartography_table"),
                (280, "barrel[facing=up,open=false]"), (300, "composter[level=5]"), (330, "loom[facing=north]")]
        for ang, blk in hall:
            x, z = _polar(5.6, ang)
            bp.set(x, 1, z, blk)
        hx, hz = _polar(5.6, 160)
        bp.chest(hx, 1, hz, "east", LOOT + "giant_tree")
        bp.set(3, 1, -1, "red_carpet")  # the rug hides the cellar hatch
        for ang in (0, 90, 180, 270):
            x, z = _polar(4.6, ang)
            bp.set(x, 1, z, "moss_carpet", keep=True)
        # floor 1: bunk room; floor 2: library; floor 3: map room
        for i, ang in enumerate((200, 250, 300)):
            x, z = _polar(4.3, ang)
            bp.bed(x, LEVELS[0] + 1, z, _card(-x, -z), ["green", "lime", "brown"][i])
        for ang in range(0, 360, 18):
            x, z = _polar(4.8, ang)
            if max(abs(x), abs(z)) >= 3 and not _in_sector(math.radians(ang), 150, 190):
                bp.fill(x, LEVELS[1] + 1, z, x, LEVELS[1] + 2, z, "bookshelf")
        bp.set(3, LEVELS[1] + 1, 3, "lectern[facing=north,has_book=false,powered=false]")
        bp.set(-3, LEVELS[1] + 1, -3, "enchanting_table")
        for ang, blk in ((40, "cartography_table"), (80, "barrel[facing=up,open=false]"),
                         (250, "lectern[facing=east,has_book=false,powered=false]"), (300, "barrel[facing=up,open=false]")):
            x, z = _polar(4.4, ang)
            bp.set(x, LEVELS[2] + 1, z, blk)

        # ---------------------------------------------------------------- limbs and the layered canopy
        lv = Palette({_lvs(v["leaves"]): 6, _lvs(v["leaves2"]): 2, _lvs(v["leaves3"]): 1},
                     seed=v["seed"] + 7, scale=2.2)
        # (angle, start y, end radius, end y, cluster rx, ry)
        limbs = [
            (30, 40, 21, 48, 7, 3), (205, 41, 20, 50, 7, 3),          # limbs carrying the nest houses
            (110, 42, 20, 55, 8, 3), (290, 42, 20, 54, 8, 3),          # middle layer: wide flat pads
            (250, 45, 18, 57, 7, 3), (160, 45, 18, 58, 7, 3), (-25, 45, 19, 56, 7, 3), (68, 44, 18, 57, 7, 3),
            (85, 27, 16, 31, 5, 2), (258, 27, 16, 30, 5, 2), (300, 30, 15, 33, 5, 2),   # low layer
        ]
        ends = []
        for i, (ang, sy, er, ey, rx, ry) in enumerate(limbs):
            sx, sz = _polar(_trunk_base(sy) - 1, ang)
            ex, ez = _polar(er, ang + rng.uniform(-4, 4))
            mx, mz = _polar(er * 0.55, ang + 6)
            my = sy + (ey - sy) * 0.75
            r0 = 2.2 if sy > 35 else 1.6
            _limb(bp, (sx, sy, sz), (mx, round(my), mz), r0, 1.4, BARK)
            _limb(bp, (mx, round(my), mz), (ex, ey, ez), 1.4, 0.8, BARK)
            ends.append((ex, ey, ez, rx, ry, i))
            if 2 <= i < 8:   # lanterns swinging under the great limbs
                hy = round(my) - 2
                bp.chain(mx, hy - 1, mz, hy)
                bp.lantern(mx, hy - 2, mz, hanging=True)
        # central leader up to the crow's nest
        for y in range(TOP - 2, 77):
            for x in range(-1, 2):
                for z in range(-1, 2):
                    bp.set(x, y, z, LOG)
        for (ex, ey, ez, rx, ry, i) in ends:
            if i < 2:
                continue   # nest limbs get their foliage after the houses are placed
            _cluster(bp, ex, ey + 2, ez, rx, ry, rx, lv, seed=i * 31 + v["seed"], glow="shroomlight" if ry > 2 else None)
            # a satellite lump for an irregular silhouette
            ox, oz = rng.randint(-4, 4), rng.randint(-4, 4)
            _cluster(bp, ex + ox, ey + 3, ez + oz, rx - 3, ry - 1 if ry > 2 else 2, rx - 3, lv, seed=i * 97)
        # upper limbs and the crown dome
        for ang in (15, 135, 255):
            ex, ez = _polar(9, ang)
            _limb(bp, (0, 58, 0), (ex, 66, ez), 1.4, 0.8, BARK)
            _cluster(bp, ex, 67, ez, 6, 3, 6, lv, seed=ang + 5, glow="shroomlight")
        _cluster(bp, 0, 72, 0, 10, 5, 10, lv, seed=v["seed"] + 101, glow="shroomlight")

        # ---------------------------------------------------------------- exterior decks around the trunk
        def ring_deck(L, s0, s1, width, door_ang):
            cells = set()
            Rb = _trunk_base(L)
            for x in range(-26, 27):
                for z in range(-26, 27):
                    d = math.hypot(x, z)
                    a = math.atan2(z, x)
                    if _in_sector(a, s0, s1) and _trunk_r(L, a) - 0.6 <= d <= Rb + 1.6 + width:
                        cells.add((x, z))
            _strip_leaves(bp, -26, L, -26, 26, L + 5, 26)
            for (x, z) in cells:
                bp.set(x, L, z, f"{deck}_planks", keep=True)
            rim = []
            for (x, z) in cells:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, z + dz)
                    if n not in cells and bp.get(n[0], L, n[1]) is None:
                        rim.append((x, z))
                        break
            for (x, z) in rim:
                bp.set(x, L + 1, z, f"{deck}_fence")
                bp.set(x, L - 1, z, slab(f"{deck}_slab", "top"))
                if (x * 7 + z * 13) % 11 == 0:
                    bp.set(x, L + 2, z, f"{deck}_fence")
                    bp.lantern(x, L + 3, z)
                elif (x * 5 + z * 3) % 13 == 0:
                    bp.chain(x, L - 2, z, L - 2)
                    bp.lantern(x, L - 3, z, hanging=True)
            # deck life: barrels, pots, benches
            rim_set = set(rim)
            inner = sorted(c for c in cells if c not in rim_set and bp.get(c[0], L + 1, c[1]) is None
                           and bp.get(c[0], L, c[1]) == f"minecraft:{deck}_planks")
            da = math.radians(door_ang)
            props = ["barrel[facing=up,open=false]", "potted_azure_bluet", "potted_red_tulip", "composter[level=6]",
                     "potted_fern", "barrel[facing=up,open=false]", "flowering_azalea", "hay_block[axis=y]"]
            placed = 0
            for (x, z) in rng.sample(inner, min(len(inner), 40)):
                if placed >= 6 or abs(math.atan2(z, x) - da) < 0.35:
                    continue
                if any((x + dx, z + dz) in rim_set for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
                    bp.set(x, L + 1, z, props[placed % len(props)])
                    placed += 1
            # diagonal struts from the bark to the deck rim
            for ang in range(int(s0) + 8, int(s1 if s1 > s0 else s1 + 360) - 4, 22):
                ix, iz = _polar(_trunk_base(L - 7) + 0.5, ang)
                ox, oz = _polar(Rb + width, ang)
                bp.line((ix, L - 7, iz), (ox, L - 1, oz), f"{deck}_log[axis=y]")
            # doorway through the bark
            a = math.radians(door_ang)
            for rr in range(int(_trunk_base(L) - 3), int(_trunk_base(L) + 4)):
                for w in (-1, 0, 1):
                    x = round(math.cos(a) * rr - math.sin(a) * w)
                    z = round(math.sin(a) * rr + math.cos(a) * w)
                    if math.hypot(x, z) > 2.9:
                        bp.set(x, L, z, f"{deck}_planks")
                        bp.clear(x, L + 1, z, x, L + 3, z)
            return cells

        ring_deck(LEVELS[0], 150, 262, 7, 172)
        ring_deck(LEVELS[1], -58, 58, 7, -12)
        ring_deck(LEVELS[2], 108, 212, 6, 128)
        hx, hz = _polar(13.5, 232)
        _cabin(bp, hx, hz, LEVELS[0], 7, 5, deck, v["roof"] + "_stairs", v["roof_full"], "east", steep=2, seed=1,
               interior="kitchen", axis="x")
        hx, hz = _polar(13.5, 20)
        _cabin(bp, hx, hz, LEVELS[1], 5, 7, deck, v["roof"] + "_stairs", v["roof_full"], "west", steep=2, seed=2,
               interior="bed", axis="z")
        bp.barrel(hx + 1, LEVELS[1] + 1, hz + 2, "up", LOOT + "giant_tree")
        hx, hz = _polar(12.5, 190)
        _cabin(bp, hx, hz, LEVELS[2], 5, 5, deck, v["roof"] + "_stairs", v["roof_full"], "north", steep=2, seed=3,
               interior="study")

        # companion tree with a lookout deck, joined to the east deck by a long rope bridge
        cx_, cz_ = _polar(29, -48)
        arch.big_oak(bp, cx_, 1, cz_, h=22, seed=v["seed"], log=v["log"], leaves=_lvs(v["leaves"]), crown=6)
        for k, ang in enumerate(range(0, 360, 60)):
            rx_, rz_ = _polar(4, ang + 15)
            bp.line((cx_, 2, cz_), (cx_ + rx_, 0, cz_ + rz_), BARK)
        for x in range(cx_ - 8, cx_ + 9):
            for z in range(cz_ - 8, cz_ + 9):
                if math.hypot(x - cx_, z - cz_) <= 7.5 + rng.random():
                    bp.set(x, 0, z, floor_pal.pick(x, 0, z), keep=True)
                    bp.set(x, -1, z, "dirt", keep=True)
        CY = LEVELS[1] - 1
        _strip_leaves(bp, cx_ - 6, CY, cz_ - 6, cx_ + 7, CY + 5, cz_ + 7)
        for x in range(cx_ - 5, cx_ + 7):
            for z in range(cz_ - 5, cz_ + 7):
                d = math.hypot(x - cx_ - 0.5, z - cz_ - 0.5)
                if d <= 5.2 and bp.get(x, CY, z) is None or (d <= 5.2 and _is_leaf(bp, x, CY, z)):
                    bp.set(x, CY, z, f"{deck}_planks")
                    if d > 4.3:
                        bp.set(x, CY + 1, z, f"{deck}_fence")
                        bp.set(x, CY - 1, z, slab(f"{deck}_slab", "top"))
        for ang in range(0, 360, 90):
            x, z = _polar(4.6, ang + 45)
            bp.fill(cx_ + x, CY + 1, cz_ + z, cx_ + x, CY + 2, cz_ + z, f"{deck}_fence")
            bp.lantern(cx_ + x, CY + 3, cz_ + z)
            bp.line((cx_, CY - 6, cz_), (cx_ + x, CY - 1, cz_ + z), f"{deck}_log[axis=y]")
        _cluster(bp, cx_, CY + 8, cz_, 7, 3, 7, lv, seed=77, glow="shroomlight")
        bp.fill(cx_, CY + 1, cz_, cx_, CY + 6, cz_, LOG)
        bp.ladder(cx_ - 1, 1, cz_, CY, "west")
        bp.set(cx_ - 1, CY, cz_, "ladder[facing=west,waterlogged=false]")
        bp.barrel(cx_ + 2, CY + 1, cz_ - 2, "up")
        bp.set(cx_ + 2, CY + 1, cz_ + 3, "potted_red_mushroom")
        bx, bz = _polar(_trunk_base(LEVELS[1]) + 8.4, -48)
        ex_, ez_ = _polar(29 - 5.0, -48)
        _bridge(bp, (bx, LEVELS[1], bz), (ex_, CY, ez_), deck, sag=2, posts=4)
        bp.clear(bx - 1, LEVELS[1] + 1, bz - 1, bx + 1, LEVELS[1] + 1, bz + 1)

        # outer staircase from the ground to the first deck
        for i in range(LEVELS[0]):
            ang = math.radians(108 + i * 6.5)
            for rr in (11.6, 12.6):
                x, z = round(math.cos(ang) * rr), round(math.sin(ang) * rr)
                f = _card(-math.sin(ang), math.cos(ang))
                bp.stairs(x, i + 1, z, f"{deck}_stairs", f)
                bp.clear(x, i + 2, z, x, i + 4, z)
            x, z = round(math.cos(ang) * 13.6), round(math.sin(ang) * 13.6)
            bp.set(x, i + 2, z, f"{deck}_fence")
            if i % 3 == 0:
                bp.fill(x, 1, z, x, i + 1, z, f"{deck}_log[axis=y]")
                ix, iz = round(math.cos(ang) * 11.6), round(math.sin(ang) * 11.6)
                bp.fill(ix, 1, iz, ix, i, iz, f"{deck}_log[axis=y]")
        # ---------------------------------------------------------------- crown deck, houses, nests
        _strip_leaves(bp, -11, TOP + 1, -11, 11, TOP + 7, 11)
        crown = set()
        for x in range(-11, 12):
            for z in range(-11, 12):
                d = math.hypot(x, z)
                if d <= 10.4 and max(abs(x), abs(z)) >= 2:
                    crown.add((x, z))
        for (x, z) in crown:
            if max(abs(x), abs(z)) > 2:
                bp.set(x, TOP, z, f"{deck}_planks")
            if 9.6 < math.hypot(x, z) <= 10.4:
                bp.set(x, TOP + 1, z, f"{deck}_fence")
                bp.set(x, TOP - 1, z, slab(f"{deck}_slab", "top"))
        for ang in range(0, 360, 30):
            x, z = _polar(10, ang)
            bp.set(x, TOP + 2, z, f"{deck}_fence")
            bp.lantern(x, TOP + 3, z)
            ix, iz = _polar(_trunk_base(TOP - 8), ang)
            bp.line((ix, TOP - 8, iz), (x, TOP - 1, z), f"{deck}_log[axis=y]")
        hx, hz = _polar(6.3, 120)
        _cabin(bp, hx, hz, TOP, 5, 5, deck, v["roof"] + "_stairs", v["roof_full"], "north", steep=2, seed=4,
               interior="bed", loot=LOOT + "giant_tree_top")
        hx, hz = _polar(6.3, 300)
        _cabin(bp, hx, hz, TOP, 5, 5, deck, v["roof"] + "_stairs", v["roof_full"], "south", steep=2, seed=5,
               interior="kitchen")
        # nests on the two great limbs, linked to the crown deck by sagging bridges
        for idx, (ang, nest_r, ny, loot) in enumerate(((30, 21, 48, LOOT + "giant_tree_top"), (205, 20, 50, None))):
            nx, nz = _polar(nest_r, ang)
            for x in range(nx - 4, nx + 5):
                for z in range(nz - 4, nz + 5):
                    if math.hypot(x - nx, z - nz) <= 4.6:
                        bp.set(x, ny, z, f"{deck}_planks")
                        if math.hypot(x - nx, z - nz) > 3.7:
                            bp.set(x, ny + 1, z, f"{deck}_fence")
            _cabin(bp, nx, nz, ny, 5, 5, deck, v["roof"] + "_stairs", v["roof_full"],
                   _card(-nx, -nz), steep=2, seed=6 + idx, interior="study" if loot else "bed", loot=loot)
            _cluster(bp, nx, ny + 9, nz, 8, 4, 8, lv, seed=300 + idx, glow="shroomlight")
            _cluster(bp, nx, ny - 2, nz, 6, 2, 6, lv, seed=310 + idx)
            ex, ez = _polar(10.4, ang)
            sx, sz = _polar(nest_r - 4.6, ang)
            _bridge(bp, (ex, TOP, ez), (sx, ny, sz), deck, sag=1)
            bp.clear(ex, TOP + 1, ez - 1, ex, TOP + 1, ez + 1)

        # crow's nest above the canopy
        bp.ladder(0, TOP + 1, 2, 77, "south")
        _strip_leaves(bp, -1, TOP + 1, 2, 1, 78, 3)
        for x in range(-3, 4):
            for z in range(-3, 4):
                if math.hypot(x, z) <= 3.3:
                    bp.set(x, 77, z, f"{deck}_planks")
                    if math.hypot(x, z) > 2.4:
                        bp.set(x, 78, z, f"{deck}_fence")
        bp.set(0, 77, 2, "ladder[facing=south,waterlogged=false]")
        bp.set(0, 78, 2, "air")
        bp.barrel(-1, 78, -1, "up")
        bp.set(1, 78, -1, "lectern[facing=south,has_book=false,powered=false]")
        for x, z in ((-2, 2), (2, 2), (-2, -2), (2, -2)):
            bp.fill(x, 78, z, x, 80, z, f"{deck}_fence")
            bp.lantern(x, 81, z)
        bp.set(0, 78, 0, "bell[attachment=floor,facing=north,powered=false]")

        # vines and hanging moss under the canopy
        _hang_under(bp, ((-32, 30, -32), (32, 80, 32)), 0.07, v["seed"], v["hang"], on=("_leaves",))
        arch.vines_on(bp, ((-12, 2, -12), (12, 46, 12)), chance=0.025, seed=v["seed"], max_len=7)

        # ---------------------------------------------------------------- entrance, waystone and forest floor
        # pointed portal: a 2-wide passage inside a deeper 4-wide recess framed by stripped logs
        frame = f"stripped_{v['log']}[axis=y]"
        zf = 4
        while bp.get(0, 3, zf + 1) is not None:
            zf += 1
        for z in range(4, zf + 2):
            for x in range(-2, 2):
                bp.set(x, 0, z, f"{deck}_planks")
            for x in (-1, 0):
                bp.clear(x, 1, z, x, 4, z)
        for z in (zf - 1, zf, zf + 1):
            for x in range(-2, 2):
                bp.clear(x, 1, z, x, 5, z)
            bp.clear(-1, 6, z, 0, 6, z)
        for z in (zf - 1, zf):
            for y in range(1, 6):
                bp.set(-3, y, z, frame)
                bp.set(2, y, z, frame)
            bp.set(-2, 6, z, frame)
            bp.set(1, 6, z, frame)
            bp.set(-1, 7, z, frame)
            bp.set(0, 7, z, frame)
            bp.set(-2, 5, z, stair(f"{deck}_stairs", "east", "top"))
            bp.set(1, 5, z, stair(f"{deck}_stairs", "west", "top"))
        bp.door(-1, 1, zf - 2, "south", deck, hinge="left")
        bp.door(0, 1, zf - 2, "south", deck, hinge="right")
        bp.fill(-1, 3, zf - 2, 0, 4, zf - 2, f"{deck}_planks")
        bp.set(-1, 4, zf - 2, "glass_pane")
        bp.set(0, 4, zf - 2, "glass_pane")
        bp.lantern(0, 5, zf - 1, hanging=True)
        for x in (-4, 3):
            bp.fill(x, 1, zf + 2, x, 2, zf + 2, f"{deck}_fence")
            bp.lantern(x, 3, zf + 2)
        for x in range(-2, 2):
            bp.stairs(x, 0, zf + 2, "mud_brick_stairs", "north")
        # path of mud bricks and moss to a waystone clearing
        for z in range(zf + 3, 25):
            for x in range(-2, 3):
                if rng.random() < 0.85:
                    bp.set(x + (1 if z > 18 else 0), 0, z, rng.choice(["mud_bricks", "packed_mud", "moss_block",
                                                                         "coarse_dirt"]))
        bp.fill(-2, 0, 17, 2, 0, 21, "mossy_stone_bricks")
        bp.set(0, 1, 19, MOD["waystone"])
        for x, z in ((-2, 17), (2, 17), (-2, 21), (2, 21)):
            bp.set(x, 1, z, "mossy_stone_brick_wall")
            bp.set(x, 2, z, f"{deck}_fence")
            bp.lantern(x, 3, z)
        # undergrowth
        for _ in range(420):
            x, z = rng.randint(-26, 26), rng.randint(-26, 26)
            if bp.get(x, 1, z) is not None or bp.get(x, 0, z) is None:
                continue
            if bp.get(x, 0, z) not in ("minecraft:grass_block", "minecraft:podzol", "minecraft:moss_block",
                                       "minecraft:coarse_dirt", "minecraft:rooted_dirt"):
                continue
            r = rng.random()
            if r < 0.3:
                bp.set(x, 1, z, "fern")
            elif r < 0.45:
                bp.set(x, 1, z, "large_fern[half=lower]")
                bp.set(x, 2, z, "large_fern[half=upper]")
            elif r < 0.6:
                bp.set(x, 1, z, rng.choice(["red_mushroom", "brown_mushroom"]))
            elif r < 0.75:
                bp.set(x, 1, z, f"leaf_litter[facing=north,segment_amount={rng.randint(1, 4)}]")
            elif r < 0.85:
                bp.set(x, 1, z, "moss_carpet")
            elif r < 0.9:
                arch.bush(bp, x, 1, z, v["leaves"], r=1)
            else:
                bp.set(x, 1, z, "short_grass")
        for x, z, s in ((-20, 12, 1), (18, -16, 2), (-15, -20, 3), (21, 14, 4)):
            arch.boulder(bp, x, 1, z, r=2, seed=s, blocks=("mossy_cobblestone", "cobblestone", "andesite", "tuff"))

    return build


TREE_VARIANTS = {
    "oak": dict(log="oak_log", wood="oak_wood", leaves="oak_leaves", leaves2="azalea_leaves",
                leaves3="flowering_azalea_leaves", deck="spruce", roof="wayfarers:crimson_roof_tile",
                roof_full="wayfarers:crimson_roof_tiles", hang=("vine",), seed=11),
    "dark_oak": dict(log="dark_oak_log", wood="dark_oak_wood", leaves="dark_oak_leaves", leaves2="dark_oak_leaves",
                     leaves3="azalea_leaves", deck="oak", roof="wayfarers:guild_roof_tile",
                     roof_full="wayfarers:guild_roof_tiles", hang=("vine", "moss", "moss"), seed=23),
}

register(StructureDef(
    "giant_tree", "overworld",
    ["forest", "flower_forest", "dark_forest", "old_growth_birch_forest", "birch_forest",
     "old_growth_pine_taiga", "old_growth_spruce_taiga"],
    [Piece("oak", giant_tree(TREE_VARIANTS["oak"]), 2),
     Piece("dark_oak", giant_tree(TREE_VARIANTS["dark_oak"]), 1)],
    spacing=26, separation=8, processors="none", adaptation="beard_thin",
    title_fr="Arbre-monde creux", title_en="Hollow Giant Tree"))


# ============================================================ Desert oasis caravanserai + tomb
def _palm(bp, x, y, z, h, lean, seed):
    """Date palm: curving trunk, drooping fronds, a few dates."""
    rng = random.Random(seed)
    lx, lz = lean
    px, pz = float(x), float(z)
    for i in range(h):
        t = i / h
        bp.set(round(px), y + i, round(pz), "jungle_log[axis=y]" if i % 3 else "stripped_jungle_log[axis=y]")
        px += lx * t * 0.55
        pz += lz * t * 0.55
    tx, ty, tz = round(px), y + h, round(pz)
    lv = Palette({_lvs("jungle_leaves"): 3, _lvs("oak_leaves"): 1}, seed=seed, scale=1.5)
    bp.set(tx, ty, tz, lv.pick(tx, ty, tz))
    bp.set(tx, ty + 1, tz, lv.pick(tx, ty + 1, tz))
    n = rng.randint(6, 7)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        ln = rng.randint(4, 6)
        for s_ in range(1, ln + 1):
            fx = tx + round(math.cos(a) * s_)
            fz = tz + round(math.sin(a) * s_)
            fy = ty + (1 if s_ == 1 else 0) - (s_ * s_) // 9
            bp.set(fx, fy, fz, lv.pick(fx, fy, fz))


def _desert_tower(bp, cx, cz, h, wall, dome_r=2):
    """Round corner tower: banded shaft, corbelled parapet and a small azure dome (chhatri)."""
    for y in range(-3, h + 1):
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                d = math.hypot(x - cx, z - cz)
                if d <= 3.4:
                    if d > 2.4 or y < 1 or y == h:
                        bp.set(x, y, z, "cut_sandstone" if y % 5 == 0 else wall.pick(x, y, z))
                    else:
                        bp.set(x, y, z, "air")
    for a in range(0, 360, 8):
        x = cx + round(math.cos(math.radians(a)) * 4.2)
        z = cz + round(math.sin(math.radians(a)) * 4.2)
        if math.hypot(x - cx, z - cz) > 3.5:
            bp.set(x, h, z, stair("sandstone_stairs", _card(cx - x, cz - z), "top"))
            bp.set(x, h + 1, z, "sandstone_wall" if (x + z) % 2 else "cut_sandstone")
    bp.disk(cx, h, cz, 3, "smooth_sandstone")
    for k, y in enumerate((4, h - 4)):
        for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            bp.set(cx + dx, y, cz + dz, "orange_stained_glass_pane")
    arch.dome(bp, cx, h + 1, cz, dome_r, "wayfarers:guild_roof_tiles", oculus=False)
    bp.set(cx, h + dome_r + 2, cz, "gold_block")
    bp.set(cx, h + dome_r + 3, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def _stall(bp, x0, z0, face, colors, goods, rng, loot=None):
    """Market stall 5 wide (along the street) x 4 deep, opening toward `face` (east/west)."""
    back = x0 if face == "east" else x0 + 3
    front = x0 + 3 if face == "east" else x0
    step = 1 if face == "east" else -1
    for z in range(z0, z0 + 5):
        bp.set(back, 1, z, "smooth_sandstone")
        bp.set(back, 2, z, "smooth_sandstone" if z in (z0, z0 + 4) else "orange_terracotta")
        for k in range(4):
            x = back + step * k
            bp.set(x, 0, z, "smooth_sandstone" if (x + z) % 2 else "cut_sandstone")
            # striped canopy, sloping down to the street
            bp.set(x, 4 if k < 3 else 3, z, f"{colors[(z - z0) % 2]}_wool")
    for z in (z0, z0 + 4):
        bp.fill(front, 1, z, front, 3, z, "jungle_fence")
        bp.fill(back, 1, z, back, 3, z, "stripped_jungle_log[axis=y]")
    bp.lantern(back + step * 2, 3, z0 + 2, hanging=True)
    for i, z in enumerate(range(z0 + 1, z0 + 4)):
        bp.set(front, 1, z, "barrel[facing=up,open=false]" if i != 1 else "smooth_sandstone_slab[type=double,waterlogged=false]")
        bp.set(front, 2, z, goods[i % len(goods)])
    if loot:
        bp.chest(back + step, 1, z0 + 1, face, loot)
    bp.set(back + step, 1, z0 + 3, rng.choice(["decorated_pot[facing=north,waterlogged=false,cracked=false]",
                                              "hay_block[axis=y]", "loom[facing=north]"]))


def oasis(bp):
    rng = random.Random(5)
    wall = Palette({"sandstone": 3, "smooth_sandstone": 2, "cut_sandstone": 2}, seed=21, scale=2.5)
    TRIM, CHI = "cut_sandstone", "chiseled_sandstone"
    TILE = "light_blue_glazed_terracotta"

    # ---------------------------------------------------------------- desert floor + green oasis ring
    sand = Palette({"sand": 6, "sandstone": 1, "smooth_sandstone": 1}, seed=22, scale=4.0)
    green = Palette({"grass_block[snowy=false]": 4, "coarse_dirt": 2, "podzol[snowy=false]": 1, "sand": 1},
                    seed=23, scale=2.0)
    PX, PZ = 2, 8
    for x in range(-48, 44):
        for z in range(-62, 28):
            if math.hypot((x + 2) / 46, (z + 17) / 45) > 1 + 0.04 * math.sin(x * 0.4 + z * 0.2):
                continue
            d = math.hypot(x - PX, z - PZ)
            bp.set(x, 0, z, green.pick(x, 0, z) if d < 16 + 2 * math.sin(x * 0.5) else sand.pick(x, 0, z))
            bp.set(x, -1, z, "sand")
            bp.set(x, -2, z, "sandstone")
    # the pond
    for x in range(PX - 13, PX + 14):
        for z in range(PZ - 11, PZ + 12):
            a = math.atan2(z - PZ, x - PX)
            rr = 10 + 1.6 * math.sin(3 * a + 1) + 0.8 * math.sin(5 * a)
            d = math.hypot((x - PX) * 0.9, z - PZ)
            if d <= rr:
                bp.set(x, 0, z, "water[level=0]")
                bp.set(x, -1, z, "water[level=0]" if d < rr - 2 else "sand")
                bp.set(x, -2, z, "water[level=0]" if d < rr - 5 else "clay")
                bp.set(x, -3, z, "sand")
                if rng.random() < 0.05:
                    bp.set(x, 1, z, "lily_pad")
            elif d <= rr + 1.3 and rng.random() < 0.35:
                for k in range(1, rng.randint(2, 4)):
                    bp.set(x, k, z, "sugar_cane")
    # palm grove
    for k in range(10):
        a = 2 * math.pi * k / 10 + rng.uniform(-0.15, 0.15)
        r = rng.uniform(13, 16)
        x, z = PX + round(math.cos(a) * r * 1.1), PZ + round(math.sin(a) * r)
        if -22 < z < 26:
            _palm(bp, x, 1, z, rng.randint(7, 11), (round(math.cos(a) * -1), round(math.sin(a) * -1)), k)
    for _ in range(60):
        x, z = rng.randint(PX - 18, PX + 18), rng.randint(PZ - 15, PZ + 16)
        if bp.get(x, 0, z) in ("minecraft:grass_block", "minecraft:coarse_dirt", "minecraft:podzol") and not bp.get(x, 1, z):
            bp.set(x, 1, z, rng.choice(["fern", "short_grass", "short_grass", "firefly_bush", "dead_bush"]))

    # ---------------------------------------------------------------- caravanserai
    X0, X1, ZF, ZB, ZH = -15, 15, -19, -55, -38           # ZH: front wall of the domed hall
    bp.fill(X0 - 1, -4, ZB - 1, X1 + 1, -1, ZF + 1, "sandstone")
    bp.fill(X0, 0, ZB, X1, 0, ZF, "smooth_sandstone")
    bp.clear(X0 + 1, 1, ZB + 1, X1 - 1, 12, ZF - 1)
    # outer facades: courtyard block 8 high, domed hall 11 high
    kw = dict(pilaster_every=4, window_h=2, window_y=3, plinth=CHI, plinth_stairs="sandstone_stairs",
              cornice_stairs="smooth_sandstone_stairs", glass="orange_stained_glass_pane", sill="sandstone_stairs")
    arch.facade(bp, "south", ZF, X0, X1, 0, 8, wall, TRIM, **kw)
    arch.facade(bp, "west", X0, ZH + 1, ZF, 0, 8, wall, TRIM, **kw)
    arch.facade(bp, "east", X1, ZH + 1, ZF, 0, 8, wall, TRIM, **kw)
    arch.facade(bp, "west", X0, ZB, ZH, 0, 11, wall, TRIM, **kw)
    arch.facade(bp, "east", X1, ZB, ZH, 0, 11, wall, TRIM, **kw)
    arch.facade(bp, "north", ZB, X0, X1, 0, 11, wall, TRIM, **kw)
    # crenellated parapets
    for x in range(X0, X1 + 1):
        for z, top in ((ZF, 9), (ZB, 12)):
            if x % 2 == 0:
                bp.set(x, top, z, "sandstone_wall")
    for z in range(ZB, ZF + 1):
        top = 12 if z <= ZH else 9
        for x in (X0, X1):
            if z % 2 == 0:
                bp.set(x, top, z, "sandstone_wall")
    # courtyard wings (rooms + roof terrace at y 6), inner arcades
    CX0, CX1, CZ0, CZ1 = -9, 9, ZH + 1, -25                  # open courtyard
    for x in range(X0 + 1, X1):
        for z in range(ZH + 1, ZF):
            if not (CX0 < x < CX1 and CZ0 <= z < CZ1):
                bp.set(x, 6, z, "smooth_sandstone")
    for face, line, u0, u1 in (("east", CX0, CZ0, CZ1), ("west", CX1, CZ0, CZ1), ("north", CZ1, CX0, CX1)):
        for u in range(u0, u1 + 1):
            for y in range(1, 6):
                x, z = (line, u) if face in ("east", "west") else (u, line)
                bp.set(x, y, z, wall.pick(x, y, z))
            x, z = (line, u) if face in ("east", "west") else (u, line)
            bp.set(x, 7, z, "sandstone_wall")
            bp.set(x, 6, z, TRIM)
        # pointed arches every 3 blocks
        for u in range(u0 + 1, u1 - 1, 3):
            for du, f in ((0, None), (1, None)):
                x, z = (line, u + du) if face in ("east", "west") else (u + du, line)
                bp.clear(x, 1, z, x, 3, z)
            along = "south" if face in ("east", "west") else "east"
            x0_, z0_ = (line, u) if face in ("east", "west") else (u, line)
            x1_, z1_ = (line, u + 1) if face in ("east", "west") else (u + 1, line)
            bp.set(x0_, 4, z0_, stair("smooth_sandstone_stairs", arch.OPPOSITE[along], "top"))
            bp.set(x1_, 4, z1_, stair("smooth_sandstone_stairs", along, "top"))
    # partition walls between the wing rooms
    for z in (-31, -26):
        bp.fill(X0 + 1, 1, z, CX0 - 1, 5, z, wall.pick(0, 1, z))
        bp.fill(CX1 + 1, 1, z, X1 - 1, 5, z, wall.pick(0, 1, z))
        bp.clear(X0 + 3, 1, z, X0 + 3, 2, z)
        bp.clear(X1 - 3, 1, z, X1 - 3, 2, z)
    # the gate: a tall pishtaq with a pointed iwan, flanked by minarets
    for x in range(-6, 7):
        for z in (ZF, ZF + 1, ZF + 2):
            for y in range(0, 15):
                bp.set(x, y, z, wall.pick(x, y, z))
        if x % 2 == 0:
            bp.set(x, 15, ZF + 2, "sandstone_wall")
            bp.set(x, 15, ZF, "sandstone_wall")
    for x in range(-6, 7):
        bp.set(x, 14, ZF + 3, stair("smooth_sandstone_stairs", "north", "top"))
        bp.set(x, 12, ZF + 2, "cyan_terracotta" if x % 2 else "yellow_terracotta")
    for y in range(0, 15):
        bp.set(-6, y, ZF + 3, TRIM)
        bp.set(6, y, ZF + 3, TRIM)
    iw = {y: (3 if y <= 7 else 2 if y == 8 else 1 if y == 9 else 0) for y in range(1, 11)}
    for y, hw in iw.items():
        for x in range(-hw, hw + 1):
            bp.clear(x, y, ZF + 1, x, y, ZF + 2)
        for x in (-hw - 1, hw + 1):
            bp.set(x, y, ZF + 2, TILE + "[facing=south]")
    bp.set(0, 11, ZF + 2, TILE + "[facing=south]")
    bp.set(0, 10, ZF + 2, "gold_block")
    bp.clear(-1, 1, ZF, 1, 4, ZF)
    bp.door(-1, 1, ZF, "south", "jungle", hinge="left")
    bp.door(1, 1, ZF, "south", "jungle", hinge="right")
    bp.door(0, 1, ZF, "south", "jungle", hinge="left", open_=True)
    bp.fill(-2, 5, ZF, 2, 7, ZF, "iron_bars")
    bp.clear(-1, 1, CZ1, 1, 4, ZF - 1)
    bp.lantern(0, 9, ZF + 2, hanging=True)
    for x in (-5, 5):
        bp.lantern(x, 1, ZF + 4)
    for mx in (-8, 8):           # minarets
        mz = ZF + 2
        for y in range(0, 20):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if abs(dx) + abs(dz) < 2 or y < 2:
                        bp.set(mx + dx, y, mz + dz, wall.pick(mx + dx, y, mz + dz))
        for dx in (-2, -1, 0, 1, 2):
            for dz in (-2, -1, 0, 1, 2):
                if abs(dx) + abs(dz) <= 3:
                    bp.set(mx + dx, 16, mz + dz, "smooth_sandstone_slab[type=top,waterlogged=false]")
                    if abs(dx) + abs(dz) == 3 or max(abs(dx), abs(dz)) == 2:
                        bp.set(mx + dx, 17, mz + dz, "sandstone_wall")
        bp.set(mx, 12, mz + 1, "orange_stained_glass_pane")
        bp.set(mx, 19, mz, CHI)
        arch.spire(bp, mx, mz, 20, 1, "wayfarers:guild_roof_tiles", "wayfarers:guild_roof_tile_stairs", steep=2,
                   finial="lightning_rod")
    # corner towers
    for (tx, tz, h) in ((X0, ZF, 13), (X1, ZF, 13), (X0, ZB, 16), (X1, ZB, 16)):
        _desert_tower(bp, tx, tz, h, wall)
    # domed hall: flat roof with a drum and a great azure dome
    DX, DZ, DR = 0, -47, 7
    for x in range(X0 + 1, X1):
        for z in range(ZB + 1, ZH + 1):
            if math.hypot(x - DX, z - DZ) > DR - 0.5:
                bp.set(x, 11, z, "smooth_sandstone")
    for x in range(X0, X1 + 1):
        for y in range(1, 11):
            bp.set(x, y, ZH, wall.pick(x, y, ZH))
    for x in range(-2, 3):
        bp.clear(x, 1, ZH, x, 4 if abs(x) < 2 else 3, ZH)
    for x in (-3, 3):
        bp.fill(x, 1, ZH + 1, x, 5, ZH + 1, TRIM)
    for x in range(-3, 4):
        bp.set(x, 6, ZH + 1, TILE + "[facing=north]")
    DY = 17                                   # dome springing line, on a tall windowed drum
    for y in range(11, DY):
        bp.disk(DX, y, DZ, DR, "cut_sandstone" if y in (11, DY - 1) else wall.pick(0, y, 0), hollow=True)
    for k in range(16):
        a = 2 * math.pi * k / 16
        for y in (13, 14):
            bp.set(DX + round(math.cos(a) * DR), y, DZ + round(math.sin(a) * DR),
                   "orange_stained_glass" if k % 2 else TILE + "[facing=north]")
    for a in range(0, 360, 6):
        x = DX + round(math.cos(math.radians(a)) * (DR + 1))
        z = DZ + round(math.sin(math.radians(a)) * (DR + 1))
        if math.hypot(x - DX, z - DZ) > DR + 0.4:
            bp.set(x, DY - 1, z, stair("smooth_sandstone_stairs", _card(DX - x, DZ - z), "top"))
    arch.dome(bp, DX, DY, DZ, DR, Palette({"wayfarers:guild_roof_tiles": 5, "light_blue_terracotta": 1}, seed=24),
              ribs="smooth_sandstone", oculus=True, rib_count=8)
    bp.set(DX, DY + DR + 1, DZ, "gold_block")
    bp.set(DX, DY + DR + 2, DZ, "gold_block")
    bp.set(DX, DY + DR + 3, DZ, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # hall interior: carpets, fountain under the oculus, chandeliers, cushions
    for x in range(X0 + 1, X1):
        for z in range(ZB + 1, ZH):
            c = ["red", "orange", "red", "blue"][(abs(x) // 2 + abs(z) // 2) % 4]
            if max(abs(x), abs(z - DZ)) % 6 == 0:
                c = "yellow"
            bp.set(x, 1, z, f"{c}_carpet")
    bp.disk(DX, 0, DZ, 3, "water[level=0]")
    bp.disk(DX, 1, DZ, 3, "air")
    bp.disk(DX, 0, DZ, 3, CHI, hollow=True)
    bp.disk(DX, 1, DZ, 3, "smooth_sandstone_slab[type=bottom,waterlogged=false]", hollow=True)
    bp.fill(DX, 0, DZ, DX, 2, DZ, CHI)
    bp.set(DX, 3, DZ, "water[level=0]")
    for (x, z) in ((-8, -42), (8, -42), (-8, -52), (8, -52)):
        bp.fill(x, 1, z, x, 10, z, TRIM)
        bp.set(x, 5, z, CHI)
    for (x, z) in ((-11, -43), (11, -43), (-11, -51), (11, -51)):
        arch.chandelier(bp, x, 10, z)
    for x in range(-13, -9):
        bp.stairs(x, 1, ZB + 1, "smooth_sandstone_stairs", "north")
        bp.stairs(x + 22, 1, ZB + 1, "smooth_sandstone_stairs", "north")
    bp.set(12, 1, -45, "cartography_table")
    bp.set(12, 1, -46, "lectern[facing=west,has_book=false,powered=false]")
    bp.set(-13, 1, -40, "loom[facing=east]")
    bp.set(13, 1, -40, "barrel[facing=up,open=false]")
    # storerooms in the front wing, stables and guest rooms on the sides
    bp.chest(-12, 1, ZF - 1, "north", LOOT + "oasis")
    for x in range(-13, -4, 2):
        bp.barrel(x, 1, ZF - 3, "up")
    for x in range(5, 14, 2):
        bp.set(x, 1, ZF - 1, "hay_block[axis=x]")
        bp.set(x, 2, ZF - 1, "hay_block[axis=z]")
    for z in range(-36, -32, 2):
        bp.bed(X1 - 1, 1, z, "west", "orange")
    for z in range(-36, -32):
        bp.set(X0 + 1, 1, z, "hay_block[axis=y]")
        bp.set(X0 + 2, 1, z, "composter[level=3]")
    for (x, z) in ((-12, -29), (12, -29), (-12, -35), (12, -35), (-8, -22), (8, -22)):
        bp.lantern(x, 5, z, hanging=True)
    # courtyard: well-fountain, palms, camels resting
    bp.disk(0, 0, -31, 2, "water[level=0]")
    bp.disk(0, 0, -31, 3, CHI, hollow=True)
    bp.disk(0, 1, -31, 3, "smooth_sandstone_slab[type=bottom,waterlogged=false]", hollow=True)
    bp.fill(0, 0, -31, 0, 2, -31, TRIM)
    bp.set(0, 3, -31, "water[level=0]")
    for (x, z) in ((-7, -36), (7, -36), (-7, -27), (7, -27)):
        bp.set(x, 0, z, "grass_block[snowy=false]")
        _palm(bp, x, 1, z, 6, (0, 0), x * 3 + z)
    bp.entity(-4, 1, -28, {"id": "minecraft:camel", "PersistenceRequired": 1})
    bp.entity(5, 1, -34, {"id": "minecraft:camel", "PersistenceRequired": 1})
    for (x, z) in ((-3, -28), (6, -35)):
        bp.set(x, 1, z, "hay_block[axis=y]")

    # ---------------------------------------------------------------- plaza with twin obelisks and the waystone
    pav = Palette({"smooth_sandstone": 3, "cut_sandstone": 2, "sandstone": 1}, seed=25)
    for x in range(-13, 14):
        for z in range(ZF + 3, -2):
            if bp.get(x, 0, z) not in ("minecraft:water",) and math.hypot(x / 14, (z + 9) / 9) < 1.15:
                bp.set(x, 0, z, "orange_terracotta" if (x + z) % 7 == 0 else pav.pick(x, 0, z))
    for ox in (-11, 11):
        oz = -7
        bp.fill(ox - 2, 0, oz - 2, ox + 2, 1, oz + 2, TRIM)
        for x in range(ox - 2, ox + 3):
            for z in range(oz - 2, oz + 3):
                if max(abs(x - ox), abs(z - oz)) == 2:
                    bp.set(x, 1, z, stair("sandstone_stairs", _card(ox - x, oz - z) if abs(x - ox) != abs(z - oz)
                                          else ("east" if x < ox else "west")))
        for y in range(2, 23):
            for x in range(ox - 1, ox + 2):
                for z in range(oz - 1, oz + 2):
                    carved = (x == ox or z == oz) and 5 <= y <= 19 and y % 2 == 0
                    bp.set(x, y, z, CHI if carved else ("smooth_sandstone" if y % 7 else TRIM))
        for x in range(ox - 1, ox + 2):
            for z in range(oz - 1, oz + 2):
                if (x, z) != (ox, oz):
                    bp.set(x, 23, z, stair("smooth_sandstone_stairs", _card(ox - x, oz - z) if abs(x - ox) != abs(z - oz)
                                           else ("east" if x < ox else "west")))
        bp.set(ox, 23, oz, "gold_block")
        bp.set(ox, 24, oz, "gold_block")
        bp.set(ox, 25, oz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.fill(-2, 0, -12, 2, 0, -8, CHI)
    bp.set(0, 1, -10, MOD["waystone"])
    for (x, z) in ((-2, -12), (2, -12), (-2, -8), (2, -8)):
        bp.set(x, 1, z, "sandstone_wall")
        bp.set(x, 2, z, "sandstone_wall")
        bp.lantern(x, 3, z)

    # ---------------------------------------------------------------- the bazaar (east of the pond)
    st = Palette({"smooth_sandstone": 2, "sandstone": 2, "sand": 1}, seed=26)
    for x in range(17, 41):
        for z in range(-16, 22):
            bp.set(x, 0, z, st.pick(x, 0, z))
    for x in range(12, 18):
        for z in range(-4, 1):
            if bp.get(x, 0, z) != "minecraft:water":
                bp.set(x, 0, z, st.pick(x, 0, z))
    goods = ["melon", "pumpkin", "potted_cactus", "hay_block[axis=y]", "decorated_pot[facing=east,waterlogged=false,cracked=false]",
             "candle[candles=4,lit=true,waterlogged=false]", "bookshelf", "cake[bites=2]", "potted_dead_bush"]
    palettes = [("red", "white"), ("blue", "white"), ("orange", "yellow"), ("cyan", "white"), ("purple", "magenta"),
                ("green", "lime"), ("red", "orange"), ("light_blue", "white")]
    k = 0
    for z0 in (-15, -9, -3, 9, 15):
        _stall(bp, 18, z0, "east", palettes[k % 8], rng.sample(goods, 3), rng,
               loot=LOOT + "oasis" if z0 == -3 else None)
        k += 1
        _stall(bp, 36, z0, "west", palettes[k % 8], rng.sample(goods, 3), rng)
        k += 1
    bp.barrel(37, 1, 11, "up", LOOT + "oasis")
    # a big shaded tent in the middle of the bazaar
    for x in range(24, 35):
        for z in range(2, 8):
            bp.set(x, 5 if 26 <= x <= 32 else 4, z, "white_wool" if x % 2 else "red_wool")
    bp.set(29, 6, 5, "red_wool")
    for (x, z) in ((24, 2), (34, 2), (24, 7), (34, 7), (29, 2), (29, 7)):
        bp.fill(x, 1, z, x, 3 if x in (24, 34) else 4, z, "jungle_fence")
    for x in range(26, 33, 2):
        bp.lantern(x, 4, 5, hanging=True)
    for (x, z) in ((27, 4), (31, 5)):
        bp.table(x, 1, z, "jungle_pressure_plate", "jungle_fence")
    for (x, z, f) in ((26, 4, "east"), (28, 4, "west"), (30, 5, "east"), (32, 5, "west")):
        bp.stairs(x, 1, z, "jungle_stairs", f)
    for (x, z) in ((20, 20), (38, -18), (40, 4), (22, -18)):
        _palm(bp, x, 1, z, rng.randint(7, 10), (rng.choice((-1, 1)), 0), x + z)
    for z in (-14, 0, 14):
        bp.fill(29, 1, z, 29, 3, z, "jungle_fence")
        bp.lantern(29, 4, z)

    # ---------------------------------------------------------------- the half-buried colossus (west)
    HX, HZ = -33, 4
    FX = HX + 5                                   # face plane, looking east toward the pond
    face = Palette({"smooth_sandstone": 4, "sandstone": 2, "cut_sandstone": 1}, seed=27, scale=2.0)
    for y in range(-3, 18):
        for z in range(HZ - 8, HZ + 9):
            dz = abs(z - HZ)
            for x in range(HX - 7, FX + 1):
                # nemes headdress: domed crown, lappets flaring down beside the face
                if y > 11:
                    if ((x - HX + 1) / 6.5) ** 2 + ((y - 11) / 6.5) ** 2 + (dz / 6.5) ** 2 > 1:
                        continue
                else:
                    if dz > (6 if y > 5 else 7) or x < HX - 7 + max(0, (y - 8) // 3):
                        continue
                lappet = dz >= 5 or y >= 12 or x < FX - 3
                if lappet:
                    if dz >= 5 and x > FX - 1:
                        continue                  # lappets sit just behind the face plane
                    bp.set(x, y, z, "lapis_block" if (y + 30) % 3 == 0 else "yellow_terracotta")
                else:
                    bp.set(x, y, z, face.pick(x, y, z))
    for z in range(HZ - 5, HZ + 6):                # gold brow band
        bp.set(FX, 12, z, "gold_block" if abs(z - HZ) % 2 == 0 else "yellow_terracotta")
    for sz in (-1, 1):                             # kohl-lined eyes and brows
        for k in (2, 3):
            bp.set(FX, 9, HZ + sz * k, "white_terracotta" if k == 2 else "black_terracotta")
        bp.set(FX, 9, HZ + sz * 4, "black_terracotta")
        for k in (2, 3, 4):
            bp.set(FX + 1, 10, HZ + sz * k, stair("sandstone_stairs", "west", "top"))
    bp.fill(FX + 1, 6, HZ, FX + 1, 8, HZ, "smooth_sandstone")      # nose
    bp.set(FX + 2, 6, HZ, stair("smooth_sandstone_stairs", "west"))
    for sz in (-1, 1):
        bp.set(FX + 1, 6, HZ + sz, stair("smooth_sandstone_stairs", "west"))
    bp.fill(FX, 4, HZ - 2, FX, 4, HZ + 2, "orange_terracotta")    # lips
    bp.set(FX + 1, 4, HZ, "orange_terracotta")
    bp.fill(FX + 1, 1, HZ - 1, FX + 1, 2, HZ + 1, "smooth_sandstone")  # chin and braided beard
    for y in range(-3, 1):
        for z in (HZ - 1, HZ, HZ + 1):
            bp.set(FX + 2, y, z, "cut_sandstone" if y % 2 else "sandstone")
            bp.set(FX + 1, y, z, "sandstone")
    bp.fill(FX + 1, 12, HZ, FX + 1, 14, HZ, "gold_block")            # uraeus cobra
    bp.set(FX + 2, 14, HZ, "lapis_block")
    # erosion, a broken crown corner, and the dune that swallows the shoulders
    for (x, y, z), b_ in list(bp.blocks.items()):
        if HX - 8 <= x <= FX + 2 and abs(z - HZ) <= 8:
            if y > 12 and x < HX - 1 and z > HZ + 1:
                bp.remove(x, y, z)
            elif y > 0 and rng.random() < 0.04 and "gold" not in b_[0]:
                bp.set(x, y, z, "sand")
    for x in range(HX - 18, FX + 9):
        for z in range(HZ - 16, HZ + 17):
            d = math.hypot((x - HX + 4) / 1.6, z - HZ)
            h = int(10 - d * 0.7 + 1.5 * math.sin(x * 0.4 + z * 0.2) + (3 if x < HX - 2 else -3 if x > FX else 0))
            if x > FX - 1 and abs(z - HZ) <= 6:
                h = min(h, max(0, (x - FX - 3) // 2))
            elif x > FX:
                h = min(h, 2 + (FX + 8 - x) // 3)
            for y in range(1, h + 1):
                bp.set(x, y, z, "sand", keep=True)
            if 1 <= h <= 7 and rng.random() < 0.05 and bp.get(x, h + 1, z) is None:
                bp.set(x, h + 1, z, rng.choice(["dead_bush", "short_dry_grass", "tall_dry_grass", "cactus"]))
    for (x, z) in ((FX + 4, HZ - 5), (FX + 3, HZ + 6), (HX - 3, HZ - 10)):
        y = 1
        while bp.get(x, y, z) == "minecraft:sand":
            y += 1
        bp.set(x, y - 1, z, "suspicious_sand", {"LootTable": "minecraft:archaeology/desert_pyramid"})

    # ---------------------------------------------------------------- caravan camp (north-west) and dunes
    for (cx, cz, c1, c2) in ((-32, -34, "brown", "white"), (-26, -46, "white", "orange")):
        for i in range(-3, 4):
            for x in range(cx - 2, cx + 3):
                h = 3 - abs(x - cx)
                if h >= 0:
                    bp.set(x, 1 + h, cz + i, f"{c1 if (x + i) % 2 else c2}_wool")
            for x in range(cx - 1, cx + 2):
                bp.set(x, 1, cz + i, "red_carpet" if abs(i) < 3 else "air")
        bp.fill(cx, 1, cz - 4, cx, 4, cz - 4, "jungle_fence")
        bp.fill(cx, 1, cz + 4, cx, 4, cz + 4, "jungle_fence")
        bp.barrel(cx - 1, 1, cz - 2, "up")
        bp.lantern(cx, 3, cz, hanging=True)
    bp.set(-29, 1, -40, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z, f) in ((-29, -38, "north"), (-31, -40, "east"), (-27, -40, "west")):
        bp.stairs(x, 1, z, "jungle_stairs", f)
    for (x, z) in ((-22, -36), (-35, -45)):
        bp.set(x, 1, z, "hay_block[axis=y]")
        bp.set(x + 1, 1, z, "barrel[facing=up,open=false]")
    bp.entity(-24, 1, -40, {"id": "minecraft:camel", "PersistenceRequired": 1})
    bp.entity(-36, 1, -36, {"id": "minecraft:camel", "PersistenceRequired": 1})
    _palm(bp, -38, 1, -27, 8, (1, 0), 77)
    for (dx_, dz_, rr) in ((-40, -50, 7), (18, -48, 8), (38, -40, 6), (-12, 22, 5), (30, 25, 6)):
        for x in range(dx_ - rr - 3, dx_ + rr + 4):
            for z in range(dz_ - rr, dz_ + rr + 1):
                h = int(rr * 0.6 - math.hypot((x - dx_) / 1.5, z - dz_) * 0.6 + 0.8 * math.sin(x * 0.7))
                if bp.get(x, 0, z) == "minecraft:sand":
                    for y in range(1, h + 1):
                        bp.set(x, y, z, "sand", keep=True)

    # ---------------------------------------------------------------- hidden staircase and the tomb
    # the hall's patterned carpet hides a trapdoor; a short ladder drops to a stair diving south
    SX, TY = -5, -15
    bp.set(SX, 0, -48, "jungle_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.clear(SX, -3, -48, SX, -1, -48)
    bp.ladder(SX, -3, -48, -1, "south")
    bp.set(SX, -4, -48, "cut_sandstone")
    bp.fill(SX, -4, -49, SX, -1, -49, "cut_sandstone")
    for i in range(12):
        z, y = -47 + i, -4 - i
        for x in (SX, SX + 1):
            bp.stairs(x, y, z, "sandstone_stairs", "north")
            bp.clear(x, y + 1, z, x, y + 3, z)
            bp.set(x, y + 4, z, "cut_sandstone")
            bp.set(x, y - 1, z, "sandstone")
        for x in (SX - 1, SX + 2):
            bp.fill(x, y - 1, z, x, y + 4, z, "cut_sandstone")
        if i % 4 == 1:
            bp.lantern(SX + 1, y + 3, z, hanging=True)
    bp.room(SX - 1, TY - 1, -36, SX + 2, TY + 3, -34, "cut_sandstone", floor="sandstone", ceiling="cut_sandstone")
    bp.stairs(SX, TY, -36, "sandstone_stairs", "north")
    bp.stairs(SX + 1, TY, -36, "sandstone_stairs", "north")
    # burial chamber
    C0X, C1X, C0Z, C1Z = -10, 10, -34, -16
    bp.room(C0X, TY - 1, C0Z, C1X, TY + 8, C1Z, "sandstone", floor="orange_terracotta", ceiling="cut_sandstone")
    bp.clear(SX, TY, C0Z, SX + 1, TY + 2, C0Z)
    for x in range(C0X + 1, C1X):
        for z in range(C0Z + 1, C1Z):
            if (x + z) % 4 == 0:
                bp.set(x, TY - 1, z, "blue_terracotta")
            elif (x - z) % 4 == 0:
                bp.set(x, TY - 1, z, "yellow_terracotta")
    for y in range(TY, TY + 8):           # painted hieroglyph bands
        for x in range(C0X + 1, C1X):
            if y in (TY + 2, TY + 5):
                for z in (C0Z, C1Z):
                    bp.set(x, y, z, CHI if x % 3 else "orange_glazed_terracotta[facing=north]")
        for z in range(C0Z + 1, C1Z):
            if y in (TY + 2, TY + 5):
                for x in (C0X, C1X):
                    bp.set(x, y, z, CHI if z % 3 else "blue_glazed_terracotta[facing=east]")
    for x in (C0X + 3, C1X - 3):
        for z in (C0Z + 4, C1Z - 4):
            bp.fill(x, TY, z, x, TY + 7, z, "cut_sandstone")
            bp.set(x, TY + 3, z, CHI)
            bp.set(x, TY + 6, z, "orange_terracotta")
    MX, MZ = 0, -25
    bp.fill(MX - 1, TY, MZ - 2, MX + 1, TY, MZ + 2, CHI)
    bp.fill(MX - 1, TY + 1, MZ - 2, MX + 1, TY + 1, MZ + 2, "smooth_sandstone_slab[type=bottom,waterlogged=false]")
    bp.set(MX, TY + 1, MZ - 2, "gold_block")
    bp.set(MX, TY + 1, MZ + 2, "gold_block")
    bp.chest(MX - 4, TY, MZ, "east", LOOT + "desert_tomb")
    bp.chest(MX + 4, TY, MZ, "west", LOOT + "desert_tomb")
    bp.spawner(MX, TY, MZ + 5, "minecraft:husk")
    for (x, z) in ((C0X + 1, C0Z + 1), (C1X - 1, C0Z + 1), (C0X + 1, C1Z - 1), (C1X - 1, C1Z - 1)):
        bp.set(x, TY, z, "decorated_pot[facing=south,waterlogged=false,cracked=false]")
    for (x, z) in ((-5, -29), (5, -29), (-5, -21), (5, -21)):
        bp.chain(x, TY + 6, z, TY + 7)
        bp.lantern(x, TY + 5, z, hanging=True)
    # secret archaeology alcove behind the west wall (break the plain sandstone under the carved eye)
    bp.set(C0X, TY + 3, MZ, "chiseled_red_sandstone")
    bp.room(C0X - 6, TY - 1, MZ - 2, C0X, TY + 3, MZ + 2, "sandstone", floor="sandstone", ceiling="sandstone")
    bp.fill(C0X, TY, MZ - 1, C0X, TY + 2, MZ + 1, "sandstone")
    for z in (MZ - 1, MZ, MZ + 1):
        bp.set(C0X - 5, TY - 1, z, "suspicious_sand", {"LootTable": "minecraft:archaeology/desert_pyramid"})
    bp.chest(C0X - 4, TY, MZ, "east", LOOT + "desert_tomb_secret")
    bp.set(C0X - 3, TY, MZ + 1, "candle[candles=3,lit=true,waterlogged=false]")


register(StructureDef(
    "desert_oasis", "overworld", ["desert"], [Piece("oasis", oasis)],
    spacing=26, separation=9, title_fr="Oasis et tombeau", title_en="Desert Oasis"))


# ============================================================ Swamp witch huts
def stilt_hut(bp, x0, z0, w, d, floor_y, wood, roof, contents):
    x1, z1 = x0 + w - 1, z0 + d - 1
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        bp.fill(x, -5, z, x, floor_y - 1, z, "mangrove_log[axis=y]" if wood == "mangrove" else f"{wood}_log[axis=y]")
    bp.room(x0, floor_y, z0, x1, floor_y + 4, z1, f"{wood}_planks", floor=f"{wood}_planks")
    bp.gable_roof(x0, z0, x1, z1, floor_y + 5, f"{roof}_stairs", ridge_axis="x", overhang=1,
                  fill=f"{wood}_planks")
    bp.fill(x0 + 1, floor_y + 5, z0 + 1, x1 - 1, floor_y + 5, z1 - 1, "air")
    bp.fill(x0 + 2, floor_y + 2, z0, x0 + 2, floor_y + 3, z0, "glass_pane")
    bp.fill(x1 - 2, floor_y + 2, z1, x1 - 2, floor_y + 3, z1, "glass_pane")
    contents(bp, x0, z0, x1, z1, floor_y)


def hang_vines(bp, x0, x1, z0, z1, min_y, count):
    """Drape vines down the outside of walls (vine attaches to the block it hangs from)."""
    tops = {}
    for (x, y, z), b in bp.blocks.items():
        if b[0] != "minecraft:air" and y > tops.get((x, z), -999):
            tops[(x, z)] = y
    for _ in range(count):
        x, z = bp.rng.randint(x0, x1), bp.rng.randint(z0, z1)
        top = tops.get((x, z))
        if top is None or top <= min_y:
            continue
        for d, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
            if not bp.get(x + dx, top - 1, z + dz):
                attach = {"north": "south", "south": "north", "east": "west", "west": "east"}[d]
                for k in range(1, bp.rng.randint(3, 6)):
                    if bp.get(x + dx, top - k, z + dz):
                        break
                    bp.set(x + dx, top - k, z + dz, f"vine[{attach}=true]")
                break


def witch_huts(bp):
    def brewery(bp, x0, z0, x1, z1, fy):
        bp.set(x0 + 1, fy + 1, z0 + 1, "cauldron")
        bp.set(x0 + 2, fy + 1, z0 + 1, "brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
        bp.set(x1 - 1, fy + 1, z0 + 1, "crafting_table")
        for x in range(x0 + 1, x1):
            bp.set(x, fy + 3, z1 - 1, bp.rng.choice(["potted_red_mushroom", "potted_brown_mushroom",
                                                      "potted_fern", "potted_dead_bush"]))
            bp.set(x, fy + 2, z1 - 1, f"spruce_slab[type=top,waterlogged=false]")
        bp.chest(x1 - 1, fy + 1, z1 - 1, "west", LOOT + "witch_hut")
        bp.lantern((x0 + x1) // 2, fy + 4, (z0 + z1) // 2, hanging=True, soul=True)

    def library(bp, x0, z0, x1, z1, fy):
        bp.bookshelf_wall(x0 + 1, fy + 1, z0 + 1, x1 - 1, fy + 2, z0 + 1, 0.2)
        bp.set(x1 - 1, fy + 1, z1 - 1, "lectern[facing=west,has_book=false,powered=false]")
        bp.bed(x0 + 1, fy + 1, z1 - 2, "south", "purple")
        bp.barrel(x0 + 2, fy + 1, z1 - 1, "up", LOOT + "witch_hut")
        bp.lantern((x0 + x1) // 2, fy + 4, (z0 + z1) // 2, hanging=True, soul=True)
        bp.spawner(x1 - 2, fy - 3, (z0 + z1) // 2, "minecraft:witch")
        bp.fill(x1 - 3, fy - 4, (z0 + z1) // 2 - 1, x1 - 1, fy - 4, (z0 + z1) // 2 + 1, "mud_bricks")

    fy = 3
    stilt_hut(bp, 0, 0, 9, 7, fy, "spruce", "dark_oak", brewery)
    stilt_hut(bp, 14, 4, 8, 7, fy + 1, "mangrove", "mangrove", library)
    # rope bridge
    for x in range(9, 14):
        y = fy if x < 12 else fy + 1
        bp.set(x, y, 4, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x, y, 5, "spruce_slab[type=top,waterlogged=false]")
        bp.set(x, y + 1, 3, "spruce_fence")
        bp.set(x, y + 1, 6, "spruce_fence")
    bp.clear(8, fy + 1, 4, 8, fy + 2, 5)
    bp.clear(14, fy + 2, 5, 14, fy + 3, 6)
    # entrance ladder + dock
    bp.clear(4, fy + 1, 6, 4, fy + 2, 6)
    bp.door(4, fy + 1, 6, "south", "spruce")
    for z in range(7, 12):
        bp.set(4, fy, z, "spruce_planks")
        bp.set(3, fy, z, "spruce_slab[type=top,waterlogged=false]")
        bp.set(5, fy, z, "spruce_slab[type=top,waterlogged=false]")
    for y in range(-3, fy):
        bp.set(4, y, 12, "spruce_log[axis=y]")
        if y >= 0:
            bp.set(4, y, 11, "ladder[facing=north,waterlogged=false]")
    bp.lantern(5, fy + 1, 11)
    # vines and swampy details
    hang_vines(bp, -1, 22, -1, 12, fy, 20)


register(StructureDef(
    "witch_huts", "overworld", ["swamp", "mangrove_swamp"], [Piece("huts", witch_huts)],
    spacing=24, separation=8, adaptation="none", processors="none",
    title_fr="Huttes des sorcières", title_en="Swamp Witch Huts"))



# ============================================================ Sky archipelago
def _float_island(bp, cx, cz, top, rx, rz, depth, seed, rock, spikes=3):
    """Floating island: grass cap, soil, rock body tapering to a jagged point. Returns {(x, z): top_y}."""
    rng = random.Random(seed)
    spike_list = [(cx + rng.randint(-rx // 2, rx // 2), cz + rng.randint(-rz // 2, rz // 2),
                   rng.uniform(2.0, 3.2), rng.randint(5, 11)) for _ in range(spikes)]
    tops = {}
    for x in range(cx - rx - 3, cx + rx + 4):
        for z in range(cz - rz - 3, cz + rz + 4):
            a = math.atan2(z - cz, x - cx)
            wob = 1 + 0.11 * math.sin(3 * a + seed) + 0.06 * math.sin(7 * a + seed * 2)
            q = math.hypot((x - cx) / rx, (z - cz) / rz) / wob
            if q > 1:
                continue
            d = depth * (1 - q) ** 0.9 + 1.5 + 1.2 * math.sin(x * 0.7 + seed) * math.cos(z * 0.6)
            for sx, sz, sr, sd in spike_list:
                dd = math.hypot(x - sx, z - sz)
                if dd < sr:
                    d += sd * (1 - dd / sr)
            ty = top + (1 if q < 0.55 and math.sin(x * 0.4 + seed) * math.cos(z * 0.5) > 0.35 else 0)
            bottom = ty - max(2, round(d))
            for y in range(bottom, ty + 1):
                if y == ty:
                    bp.set(x, y, z, "grass_block[snowy=false]")
                elif y >= ty - 2:
                    bp.set(x, y, z, "dirt" if (x + y + z) % 5 else "coarse_dirt")
                else:
                    bp.set(x, y, z, rock.pick(x, y, z))
            tops[(x, z)] = ty
    return tops


def _underside(bp, tops, seed, berries=4):
    """Dress the underside: rooted dirt + hanging roots, moss, amethyst, spore blossoms, glow lichen,
    a few glow-berry vines."""
    rng = random.Random(seed)
    bottoms = {}
    for (x, z) in tops:
        y = tops[(x, z)]
        while bp.get(x, y - 1, z) is not None:
            y -= 1
        bottoms[(x, z)] = y
    cells = sorted(bottoms)
    rng.shuffle(cells)
    nb = 0
    for (x, z) in cells:
        y = bottoms[(x, z)]
        r = rng.random()
        if r < 0.10:
            bp.set(x, y, z, "rooted_dirt")
            bp.set(x, y - 1, z, "hanging_roots[waterlogged=false]")
        elif r < 0.17:
            bp.set(x, y, z, "moss_block")
            for k in range(1, rng.randint(2, 5)):
                bp.set(x, y - k, z, "vine[north=true]" if k > 1 else "vine[up=true]")
        elif r < 0.20:
            bp.set(x, y - 1, z, "amethyst_cluster[facing=down,waterlogged=false]")
            bp.set(x, y, z, "amethyst_block")
        elif r < 0.23:
            bp.set(x, y - 1, z, "spore_blossom")
        elif r < 0.30:
            bp.set(x, y - 1, z, "glow_lichen[down=false,east=false,north=false,south=false,up=true,"
                                "waterlogged=false,west=false]")
        elif r < 0.33 and nb < berries:
            nb += 1
            n = rng.randint(3, 7)
            for k in range(1, n):
                bp.set(x, y - k, z, f"cave_vines_plant[berries={'true' if k % 2 else 'false'}]")
            bp.set(x, y - n, z, "cave_vines[age=25,berries=true]")
        elif r < 0.40:
            bp.set(x, y, z, rng.choice(["iron_ore", "copper_ore", "lapis_ore", "gold_ore", "calcite"]))
    return bottoms


def _edge(tops, cx, cz, dx, dz):
    """Last island cell walking from (cx, cz) along (dx, dz)."""
    x, z = cx, cz
    last = (x, z)
    for i in range(1, 80):
        p = (round(cx + dx * i), round(cz + dz * i))
        if p in tops:
            last = p
        elif i > 3:
            break
    return last


def _helix_stair(bp, cx, cz, y0, y1, r, end, stairs, under, rail, lamp_every=9, lamp="wayfarers:rune_lamp"):
    """Stair spiralling counter-clockwise around (cx, cz), arriving at angle `end` (degrees): two cells
    wide (r, r+1), solid ribbon below, rail outside, headroom cleared (it bores through rock, where lamps
    are set into the tunnel wall). Returns the last step (x, y, z)."""
    step = math.degrees(1.0 / (r + 0.5))
    start = end - (y1 - y0) * step
    pos = None
    for i, y in enumerate(range(y0, y1 + 1)):
        a = math.radians(start + i * step)
        f = _card(-math.sin(a), math.cos(a))
        for rr in (r, r + 1):
            x, z = cx + round(math.cos(a) * rr), cz + round(math.sin(a) * rr)
            bp.set(x, y, z, stair(stairs, f))
            if not (bp.get(x, y - 1, z) or "").endswith("_stairs"):
                bp.set(x, y - 1, z, under)
            bp.clear(x, y + 1, z, x, y + 3, z)
            pos = (x, y, z)
        x, z = cx + round(math.cos(a) * (r + 2)), cz + round(math.sin(a) * (r + 2))
        if bp.get(x, y + 1, z) in (None, "minecraft:air"):
            bp.set(x, y, z, under)
            bp.set(x, y + 1, z, rail)
            if i % lamp_every == 0:
                bp.set(x, y + 2, z, rail)
                bp.lantern(x, y + 3, z)
        elif i % 5 == 0:
            bp.set(x, y + 2, z, lamp)
    return pos


def sky_island(bp):
    rng = random.Random(42)
    Y = 56                                   # main island surface; its underside hangs ~40 above the ground
    rock = Palette({"stone": 5, "andesite": 2, "tuff": 2, "calcite": 1, "cobblestone": 1}, seed=4, scale=3.0)
    wall = Palette({"quartz_bricks": 4, "calcite": 3, "smooth_quartz": 1}, seed=5, scale=2.5)
    ROOF, ROOF_S = "wayfarers:guild_roof_tiles", "wayfarers:guild_roof_tile_stairs"
    TRIM = "quartz_pillar[axis=y]"

    # ---------------------------------------------------------------- the islands
    main = _float_island(bp, 0, 0, Y, 22, 17, 24, 1, rock, spikes=5)
    west = _float_island(bp, -38, 3, Y + 4, 8, 8, 15, 2, rock, spikes=2)      # rotunda + waystone
    east = _float_island(bp, 33, -14, Y - 4, 7, 7, 13, 3, rock, spikes=2)     # broken watchtower
    high = _float_island(bp, 19, 2, Y + 12, 6, 5, 9, 4, rock, spikes=1)       # spring island above the garden
    tiny = _float_island(bp, -18, -24, Y + 9, 3, 3, 6, 5, rock, spikes=1)     # drifting rocks
    tiny2 = _float_island(bp, 30, 14, Y + 3, 3, 2, 5, 6, rock, spikes=1)
    tiny3 = _float_island(bp, -30, -14, Y - 6, 2, 2, 4, 7, rock, spikes=1)
    for k, tops in enumerate((main, west, east, high, tiny, tiny2, tiny3)):
        _underside(bp, tops, len(tops), berries=2 if k == 0 else (1 if k < 3 else 0))

    # ---------------------------------------------------------------- temple plinth and hall
    X0, X1, Z0, Z1, ZP = -12, 8, -10, 2, 8        # hall walls, portico front
    H0, H1 = Y + 3, Y + 13                        # floor, wall top
    fill_pal_ = Palette({"quartz_bricks": 3, "smooth_quartz": 2}, seed=6)
    arch.fill_pal(bp, X0 - 2, Y - 2, Z0 - 2, X1 + 2, H0, ZP, fill_pal_)
    for x in range(X0 - 2, X1 + 3):
        bp.set(x, H0, Z0 - 2, stair("smooth_quartz_stairs", "south"))
        for k, z in enumerate((ZP + 1, ZP + 2, ZP + 3)):
            bp.set(x, H0 - 1 - k, z, stair("quartz_stairs", "north"))
            for yy in range(Y - 2, H0 - 1 - k):
                bp.set(x, yy, z, "quartz_bricks")
    for x in range(X0, X1 + 1):
        for z in range(Z0, ZP + 1):
            bp.set(x, H0, z, "smooth_quartz" if (x + z) % 2 else "calcite")
    for x in range(X0, X1 + 1):
        bp.set(x, H0, Z1 + 1, "chiseled_quartz_block")
    bp.clear(X0 + 1, H0 + 1, Z0 + 1, X1 - 1, H1 + 12, Z1 - 1)
    for face, line, u0, u1 in (("north", Z0, X0, X1), ("south", Z1, X0, X1), ("west", X0, Z0, Z1), ("east", X1, Z0, Z1)):
        arch.facade(bp, face, line, u0, u1, H0, H1, wall, TRIM, pilaster_every=4, window_h=5, window_y=2,
                    plinth="chiseled_quartz_block", cornice_stairs="smooth_quartz_stairs",
                    glass="light_blue_stained_glass_pane", sill="smooth_quartz_stairs")
    arch.arch_door(bp, "south", Z1, -2, H0, width=3, height=5, trim="chiseled_quartz_block",
                   stairs="smooth_quartz_stairs", door="birch")
    # portico: six columns carrying the extended roof
    for x in range(X0, X1 + 1, 4):
        bp.set(x, H0 + 1, ZP, "chiseled_quartz_block")
        bp.fill(x, H0 + 2, ZP, x, H1 - 2, ZP, TRIM)
        bp.set(x, H1 - 1, ZP, "chiseled_quartz_block")
    for x in range(X0 - 1, X1 + 2):
        bp.set(x, H1, ZP, "smooth_quartz")
        bp.set(x, H1, ZP + 1, stair("smooth_quartz_stairs", "north", "top"))
    for z in range(Z1 + 1, ZP + 1):
        bp.set(X0, H1, z, "smooth_quartz")
        bp.set(X1, H1, z, "smooth_quartz")
    for x in (X0 + 2, -2, X1 - 2):
        arch.hanging_lantern(bp, x, H1 - 1, ZP - 3, chain=3)
    _gable(bp, X0, Z0, X1, ZP, H1 + 1, ROOF_S, ROOF, "quartz_bricks", axis="x", overhang=1, steep=1,
           under="smooth_quartz_stairs")
    # rose windows in the pediments
    for x in (X0, X1):
        bp.set(x, H1 + 5, (Z0 + ZP) // 2, "light_blue_stained_glass")
        bp.set(x, H1 + 4, (Z0 + ZP) // 2, "light_blue_stained_glass")
    # ruin: the east end of the roof has fallen in
    for (x, y, z), b in list(bp.blocks.items()):
        if y > H1 and X1 - 7 <= x <= X1 + 1 and Z0 - 1 <= z <= ZP + 1 and "roof_tile" in b[0]:
            if rng.random() < (x - (X1 - 8)) / 7.0:
                bp.remove(x, y, z)
        if H1 - 4 < y <= H1 + 12 and x in (X1, X1 + 1) and Z0 - 1 <= z <= Z1 + 1 and rng.random() < 0.45:
            bp.remove(x, y, z)
    for z in range(Z0, ZP + 1):   # bare rafters where the tiles are gone
        bp.set(X1 - 4, H1 + 1 + min(z - Z0 + 1, ZP - z + 1), z, "stripped_birch_log[axis=y]")
    arch.rubble(bp, X1 - 6, Z0 + 1, X1 - 1, Z1 - 1, H0 + 1, 14, blocks=("calcite", "quartz_bricks", "smooth_quartz_slab",
                                                                        "wayfarers:guild_roof_tiles"), seed=3)

    # ---------------------------------------------------------------- interior: nave, altar, secret vault
    for z in range(Z0 + 3, Z1, 2):
        for x in list(range(X0 + 2, -3)) + list(range(0, X1 - 4)):
            bp.stairs(x, H0 + 1, z, "birch_stairs", "north")
    bp.fill(-4, H0 + 1, Z0 + 1, 0, H0 + 1, Z0 + 2, "smooth_quartz")
    bp.set(-2, H0 + 2, Z0 + 1, "chiseled_quartz_block")
    bp.set(-2, H0 + 3, Z0 + 1, "amethyst_cluster[facing=up,waterlogged=false]")
    bp.chest(-2, H0 + 2, Z0 + 2, "south", LOOT + "sky_island")
    for x in (-4, 0):
        bp.set(x, H0 + 2, Z0 + 1, "end_rod[facing=up]")
        bp.set(x, H0 + 2, Z0 + 2, "candle[candles=3,lit=true,waterlogged=false]")
    for x in (-8, -2, 4):
        arch.chandelier(bp, x, H1 + 3, -4, soul=False)
        bp.chain(x, H1 + 2, -4, H1 + 8)
    for z in (Z0 + 2, -2):
        for x, f in ((X0 + 1, "east"), (X1 - 1, "west")):
            bp.set(x, H0 + 4, z, f"light_blue_wall_banner[facing={f}]")
    bp.set(X0 + 1, H0 + 1, Z0 + 1, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(X0 + 1, H0 + 1, Z1 - 1, "decorated_pot[facing=east,waterlogged=false,cracked=false]")
    # the vault: a slab of the altar dais lifts on a trapdoor; ladder into a crystal room in the rock
    vy = Y - 9
    bp.room(-6, vy, Z0 - 1, 2, vy + 5, Z0 + 5, "calcite", floor="polished_diorite", ceiling="calcite")
    for (x, z) in ((-5, Z0), (1, Z0), (-5, Z0 + 4), (1, Z0 + 4)):
        bp.fill(x, vy + 1, z, x, vy + 4, z, "amethyst_block")
        bp.set(x, vy + 4, z, "wayfarers:lithite_block")
    for x in (-4, -2, 0):
        bp.set(x, vy + 4, Z0 + 2, "amethyst_cluster[facing=down,waterlogged=false]")
    bp.chest(-2, vy + 1, Z0, "south", LOOT + "sky_island")
    bp.spawner(-2, vy + 1, Z0 + 3, MOB["ruin_walker"])
    bp.set(0, H0, Z0 + 3, "birch_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.ladder(0, vy + 1, Z0 + 3, H0 - 1, "south")
    bp.fill(0, vy + 1, Z0 + 2, 0, H0 - 1, Z0 + 2, "calcite")

    # ---------------------------------------------------------------- tall west tower with an azure spire
    TX, TZ = -17, -4
    arch.round_tower(bp, TX, TZ, H0, 26, 4, wall, trim="chiseled_quartz_block", floor="birch_planks",
                     corbel_stairs="smooth_quartz_stairs", crown="spire", roof_block=ROOF, roof_stairs=ROOF_S,
                     windows="light_blue_stained_glass_pane")
    arch.fill_pal(bp, TX - 4, Y - 2, TZ - 4, TX + 4, H0 - 1, TZ + 4, fill_pal_)
    bp.clear(X0 - 1, H0 + 1, TZ, X0, H0 + 3, TZ)
    bp.clear(TX + 3, H0 + 1, TZ, TX + 4, H0 + 3, TZ)
    bp.chest(TX + 2, H0 + 25, TZ, "west", LOOT + "sky_island")
    bp.set(TX - 2, H0 + 25, TZ, "bell[attachment=floor,facing=east,powered=false]")
    bp.set(TX, H0 + 25, TZ + 2, "lectern[facing=north,has_book=false,powered=false]")
    bp.set(TX, H0 + 7, TZ + 2, "cartography_table")
    bp.bed(TX - 2, H0 + 13, TZ, "south", "light_blue")
    # broken east tower
    for x in range(10, 16):
        for z in range(-11, -5):
            if x in (10, 15) or z in (-11, -6):
                hh = 15 - (abs(x - 12) + abs(z + 8)) // 2 - rng.randint(0, 3)
                for y in range(Y - 2, Y + hh):
                    bp.set(x, y, z, wall.pick(x, y, z) if (x, z) not in ((10, -11), (15, -11), (10, -6), (15, -6))
                           else TRIM)
            else:
                bp.set(x, Y, z, "smooth_quartz")
                bp.clear(x, Y + 1, z, x, Y + 14, z)
    bp.fill(12, Y + 5, -6, 13, Y + 8, -6, "light_blue_stained_glass_pane")
    bp.clear(12, Y + 1, -11, 13, Y + 4, -11)

    # ---------------------------------------------------------------- garden, pond and waterfalls
    PX, PZ = 13, 5
    for x in range(PX - 5, PX + 6):
        for z in range(PZ - 5, PZ + 6):
            d = math.hypot(x - PX, z - PZ)
            if d <= 3.6 and (x, z) in main:
                bp.set(x, Y, z, "water[level=0]")
                bp.set(x, Y - 1, z, "water[level=0]" if d < 2.5 else "clay")
                bp.set(x, Y - 2, z, "clay")
            elif d <= 4.6 and (x, z) in main:
                bp.set(x, Y, z, rng.choice(["mossy_cobblestone", "calcite", "moss_block"]))
    bp.set(PX - 1, Y + 1, PZ + 1, "lily_pad")
    bp.set(PX + 1, Y + 1, PZ - 2, "lily_pad")
    # stream to the south rim, then a ribbon of falling water to a plunge pool on the ground
    sx, sz = _edge(main, PX, PZ, 0.15, 1)
    for z in range(PZ + 3, sz + 1):
        x = round(PX + (z - PZ) * 0.15)
        bp.set(x, Y, z, "water[level=0]")
        bp.set(x, Y - 1, z, "stone")
        if (x - 1, z) in main:
            bp.set(x - 1, Y + 1, z, "moss_carpet", keep=True)
    fall_x, fall_z = sx, sz + 1
    for y in range(1, Y + 1):
        bp.set(fall_x, y, fall_z, "water[level=8]")
    # spring on the high island pouring into the pond
    hx, hz = _edge(high, 19, 2, -1, 0)
    for x in range(hx, 21):
        bp.set(x, Y + 12, 2, "water[level=0]")
    for y in range(Y + 1, Y + 12):
        bp.set(hx - 1, y, 2, "water[level=8]")
    # west island cascade off its north rim
    wx, wz = _edge(west, -38, 3, 0, -1)
    bp.set(wx, Y + 4, wz, "water[level=0]")
    bp.set(wx, Y + 4, wz + 1, "water[level=0]")
    for y in range(1, Y + 4):
        bp.set(wx, y, wz - 1, "water[level=8]")
    for x in range(wx - 4, wx + 5):
        for z in range(wz - 6, wz + 3):
            d = math.hypot(x - wx, z - wz + 2)
            if d <= 2.6:
                bp.set(x, 0, z, "water[level=0]")
                bp.set(x, -1, z, "gravel")
            elif d <= 4.2:
                bp.set(x, 0, z, rng.choice(["mossy_cobblestone", "stone", "moss_block", "grass_block[snowy=false]"]))
                bp.fill(x, -3, z, x, -1, z, "dirt", keep=True)
    # glow-berry vine climbing rope from the high island down to the garden
    for y in range(Y + 1, Y + 9):
        bp.set(21, y, 6, "cave_vines_plant[berries=true]" if y % 2 else "cave_vines_plant[berries=false]")
    bp.set(21, Y + 1, 6, "cave_vines[age=25,berries=true]")

    # trees and flowers
    arch.oak(bp, 4, Y + 1, 10, h=6, seed=1, log="cherry_log", leaves="cherry_leaves")
    arch.birch(bp, -8, Y + 1, 12, h=7, seed=2)
    arch.birch(bp, 17, Y + 1, -2, h=6, seed=3)
    arch.oak(bp, 19, Y + 13, 3, h=4, seed=4, log="cherry_log", leaves="cherry_leaves")
    arch.oak(bp, -40, Y + 5, 7, h=5, seed=5, log="cherry_log", leaves="cherry_leaves")
    for tops, sd in ((main, 1), (west, 2), (east, 3), (high, 4), (tiny, 5)):
        r2 = random.Random(sd)
        for (x, z), y in tops.items():
            if bp.get(x, y + 1, z) is None and bp.get(x, y, z) == "minecraft:grass_block" and r2.random() < 0.3:
                bp.set(x, y + 1, z, r2.choice(["short_grass", "short_grass", "oxeye_daisy", "allium", "azure_bluet",
                                                "cornflower", "lily_of_the_valley",
                                                "pink_petals[facing=north,flower_amount=3]"]))

    # ---------------------------------------------------------------- the way up: a quartz stair around a rock spire
    CX, CZ = -9, 11
    for y in range(-4, Y - 3):
        rr = 2.6 + max(0, (8 - y)) * 0.25 + 0.3 * math.sin(y * 0.5)
        for x in range(CX - 5, CX + 6):
            for z in range(CZ - 5, CZ + 6):
                if math.hypot(x - CX, z - CZ) <= rr:
                    bp.set(x, y, z, "calcite" if y % 9 == 0 else rock.pick(x, y, z))
    for x in range(CX - 8, CX + 9):
        for z in range(CZ - 8, CZ + 9):
            if math.hypot(x - CX, z - CZ) <= 7.5 and bp.get(x, 0, z) is None:
                bp.set(x, 0, z, rng.choice(["grass_block[snowy=false]", "grass_block[snowy=false]", "coarse_dirt",
                                            "mossy_cobblestone"]))
                bp.fill(x, -3, z, x, -1, z, "dirt", keep=True)
    last = _helix_stair(bp, CX, CZ, 1, Y, 4, 160, "smooth_quartz_stairs", "smooth_quartz", "birch_fence")
    lx, _, lz = last
    bp.clear(lx - 1, Y + 1, lz - 1, lx + 1, Y + 4, lz + 1)
    arch.vines_on(bp, ((CX - 4, 2, CZ - 4), (CX + 4, Y - 4, CZ + 4)), chance=0.08, seed=9, max_len=6)
    for x, z in ((CX + 6, CZ + 3), (CX - 5, CZ + 6)):
        arch.boulder(bp, x, 1, z, r=2, seed=x, blocks=("stone", "andesite", "tuff", "mossy_cobblestone"))
    # plunge pool under the main waterfall
    for x in range(fall_x - 5, fall_x + 6):
        for z in range(fall_z - 4, fall_z + 7):
            d = math.hypot(x - fall_x, z - fall_z - 1)
            if d <= 3.4:
                bp.set(x, 0, z, "water[level=0]")
                bp.set(x, -1, z, "water[level=0]" if d < 2.4 else "gravel")
                bp.set(x, -2, z, "gravel")
            elif d <= 5.2:
                bp.set(x, 0, z, rng.choice(["mossy_cobblestone", "stone", "moss_block", "grass_block[snowy=false]"]))
                bp.fill(x, -3, z, x, -1, z, "dirt", keep=True)
                if rng.random() < 0.3:
                    bp.set(x, 1, z, rng.choice(["fern", "short_grass", "moss_carpet"]))

    # ---------------------------------------------------------------- bridges
    a = _edge(main, -2, 4, -1, 0)
    b = _edge(west, -38, 4, 1, 0)
    _bridge(bp, (a[0], Y, a[1]), (b[0], Y + 4, b[1]), "spruce", sag=1, rail="chain", posts=4,
            clear_leaves=False, edge="smooth_quartz", post="birch_fence")
    a = _edge(main, 6, -10, 1, 0)
    b = _edge(east, 33, -10, -1, 0)
    _bridge(bp, (a[0], Y, a[1]), (b[0], Y - 4, -10), "spruce", sag=1, rail="chain", posts=4,
            clear_leaves=False, edge="smooth_quartz", post="birch_fence")
    for (px_, pz_, py_) in ((a[0], a[1], Y), (b[0], -10, Y - 4)):
        for dz in (-2, 2):
            bp.fill(px_, py_ + 1, pz_ + dz, px_, py_ + 4, pz_ + dz, TRIM)
            bp.set(px_, py_ + 5, pz_ + dz, "chiseled_quartz_block")
            bp.lantern(px_, py_ + 6, pz_ + dz)

    # ---------------------------------------------------------------- west island: domed rotunda with a waystone
    RX, RZ, RY = -38, 3, Y + 4
    bp.disk(RX, RY, RZ, 5, "smooth_quartz")
    bp.disk(RX, RY, RZ, 5, "chiseled_quartz_block", hollow=True)
    for k in range(8):
        a_ = 2 * math.pi * k / 8
        x, z = RX + round(math.cos(a_) * 4), RZ + round(math.sin(a_) * 4)
        bp.fill(x, RY + 1, z, x, RY + 5, z, TRIM)
        bp.set(x, RY + 6, z, "chiseled_quartz_block")
    bp.disk(RX, RY + 6, RZ, 5, "smooth_quartz")
    bp.disk(RX, RY + 6, RZ, 3, "air")
    arch.dome(bp, RX, RY + 6, RZ, 5, ROOF, ribs="smooth_quartz", oculus=True)
    bp.set(RX, RY + 13, RZ, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(RX, RY + 1, RZ, MOD["waystone"])
    arch.hanging_lantern(bp, RX, RY + 10, RZ, chain=3)
    bp.barrel(RX - 3, RY + 1, RZ + 1, "up")
    # east island: the broken watchtower keeps a beacon lantern burning
    EX, EZ, EY = 33, -14, Y - 4
    for x in range(EX - 3, EX + 4):
        for z in range(EZ - 3, EZ + 4):
            edge_ = x in (EX - 3, EX + 3) or z in (EZ - 3, EZ + 3)
            corner = x in (EX - 3, EX + 3) and z in (EZ - 3, EZ + 3)
            # broken crown: high on the north-west, collapsed toward the south-east
            hh = EY + 14 - (x - EX + 3) - (z - EZ + 3) // 2 + (2 if corner else 0) + (1 if (x * 3 + z) % 4 == 0 else 0)
            for y in range(EY - 1, max(EY + 3, hh)):
                if edge_:
                    bp.set(x, y, z, TRIM if corner else wall.pick(x, y, z))
                elif y > EY:
                    bp.set(x, y, z, "air")
    for (x, z) in ((EX, EZ - 3), (EX - 3, EZ)):
        bp.fill(x, EY + 8, z, x, EY + 10, z, "light_blue_stained_glass_pane")
    arch.rubble(bp, EX + 3, EZ - 2, EX + 6, EZ + 4, EY + 1, 8, blocks=("calcite", "quartz_bricks", "smooth_quartz"),
                seed=8)
    bp.fill(EX - 2, EY, EZ - 2, EX + 2, EY, EZ + 2, "smooth_quartz")
    bp.clear(EX - 3, EY + 1, EZ - 1, EX - 3, EY + 3, EZ + 1)
    bp.fill(EX - 2, EY + 6, EZ - 2, EX + 2, EY + 6, EZ + 2, "birch_planks")
    bp.ladder(EX + 2, EY + 1, EZ, EY + 6, "west")
    bp.set(EX, EY + 7, EZ, "chiseled_quartz_block")
    bp.set(EX, EY + 8, EZ, "soul_lantern[hanging=false,waterlogged=false]")
    bp.barrel(EX - 1, EY + 1, EZ + 2, "up")
    bp.set(EX + 1, EY + 7, EZ - 2, "cartography_table")

    # ---------------------------------------------------------------- ruined parapet along the main rim and paths
    for (x, z), y in main.items():
        rim = any((x + dx, z + dz) not in main for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if rim and bp.get(x, y + 1, z) is None and math.sin(x * 0.35) * math.cos(z * 0.4) > 0.1:
            h = 1 + (1 if (x * 3 + z) % 4 == 0 else 0)
            for k in range(1, h + 1):
                bp.set(x, y + k, z, wall.pick(x, y + k, z))
    for z in range(ZP + 4, 15):
        for x in (-3, -2, -1):
            if (x, z) in main:
                bp.set(x, main[(x, z)], z, "calcite" if (x + z) % 3 else "polished_diorite")
    arch.vines_on(bp, ((X0 - 3, Y, Z0 - 3), (X1 + 3, H1 + 12, ZP + 3)), chance=0.03, seed=7, max_len=5)


register(StructureDef(
    "sky_island", "overworld", ["plains", "meadow", "#minecraft:is_forest", "savanna", "cherry_grove",
                                 "sunflower_plains"],
    [Piece("island", sky_island)], spacing=34, separation=12, adaptation="none", processors="none",
    title_fr="Île céleste", title_en="Sky Island"))


# ============================================================ Jungle ziggurat
def _jungle_tree(bp, x, y, z, h, seed, crown=5):
    """Tall jungle giant: 2x2 trunk with root flare, side branches, layered canopy, cocoa and vines."""
    rng = random.Random(seed)
    L = "jungle_log[axis=y]"
    lv = Palette({_lvs("jungle_leaves"): 5, _lvs("oak_leaves"): 1}, seed=seed, scale=2.0)
    for i in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(x + dx, y + i, z + dz, L)
    for dx, dz in ((-1, 0), (2, 1), (0, -1), (1, 2), (-1, 1), (2, 0)):
        for k in range(rng.randint(1, 3)):
            bp.set(x + dx, y + k, z + dz, "jungle_wood[axis=y]")
    for i in range(3, h - 3, 3):
        if rng.random() < 0.5:
            f = rng.choice(["north", "south", "east", "west"])
            ox, oz = {"north": (0, -1), "south": (0, 2), "west": (-1, 0), "east": (2, 0)}[f]
            bp.set(x + ox, y + i, z + oz, f"cocoa[age=2,facing={arch.OPPOSITE[f]}]")
    top = y + h
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        ex, ez = x + round(math.cos(a) * crown), z + round(math.sin(a) * crown)
        by = top - rng.randint(2, 5)
        bp.line((x, by - 3, z), (ex, by, ez), "jungle_log[axis=y]")
        _cluster(bp, ex, by + 1, ez, crown - 1, 2, crown - 1, lv, seed=seed + k)
    _cluster(bp, x, top + 1, z, crown + 1, 3, crown + 1, lv, seed=seed + 9)
    arch.vines_on(bp, ((x - crown - 3, y + 3, z - crown - 3), (x + crown + 4, top + 4, z + crown + 4)),
                  chance=0.12, seed=seed, max_len=6)


def ziggurat(bp):
    rng = random.Random(7)
    TIERS, B, TH, INSET = 8, 29, 4, 3
    core = Palette({"stone_bricks": 3, "mossy_stone_bricks": 4, "cracked_stone_bricks": 1, "tuff_bricks": 2,
                    "mossy_cobblestone": 1}, seed=11, scale=3.0)
    jade = Palette({"oxidized_cut_copper": 3, "weathered_cut_copper": 1, "oxidized_copper": 1}, seed=12, scale=2.0)
    TRIM = "polished_tuff"
    SUM = TIERS * TH - 1                       # summit top block (y = 31)

    # ---------------------------------------------------------------- the stepped pyramid
    for t in range(TIERS):
        r, y0 = B - INSET * t, TH * t
        lo = -4 if t == 0 else y0
        for x in range(-r, r + 1):
            for z in range(-r, r + 1):
                if abs(x) == r and abs(z) == r:
                    continue            # notched corners
                for y in range(lo, y0 + TH):
                    bp.set(x, y, z, core.pick(x, y, z))
        # facade details on the four faces: sloped skirt, recessed niches, frieze, cornice
        for face in ("north", "south", "east", "west"):
            ox, oz = arch.FACE_VEC[face]
            for u in range(-r + 1, r):
                if face == "south" and abs(u) <= 8:
                    continue            # grand staircase
                wx, wz = (u, r * oz) if face in ("north", "south") else (r * ox, u)
                bp.set(wx, y0, wz, TRIM)
                bp.set(wx + ox, y0, wz + oz, stair("tuff_brick_stairs", arch.OPPOSITE[face]))
                k = (u + r) % 6
                if 2 <= k <= 4 and abs(u) < r - 2:
                    bp.set(wx, y0 + 1, wz, "air")
                    bp.set(wx, y0 + 2, wz, "air")
                    bp.set(wx - ox, y0 + 1, wz - oz, "chiseled_stone_bricks" if k == 3 else "tuff_bricks")
                    bp.set(wx - ox, y0 + 2, wz - oz, "chiseled_tuff" if k == 3 else "tuff_bricks")
                    if k == 3 and rng.random() < 0.25:
                        bp.set(wx, y0 + 1, wz, "decorated_pot[facing=%s,waterlogged=false,cracked=true]" % face)
                else:
                    bp.set(wx, y0 + 2, wz, "chiseled_tuff_bricks" if k == 0 else core.pick(wx, y0 + 2, wz))
                bp.set(wx, y0 + 3, wz, "tuff_bricks")
                bp.set(wx + ox, y0 + 3, wz + oz, stair("tuff_brick_stairs", arch.OPPOSITE[face], "top"))
        # braziers and lanterns on the notched corners of the terrace below
        if t > 0:
            for sx in (-1, 1):
                for sz in (-1, 1):
                    if t % 2 == 0:
                        bp.set(sx * r, y0, sz * r, "chiseled_tuff_bricks")
                        bp.set(sx * r, y0 + 1, sz * r, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
                    else:
                        bp.lantern(sx * r, y0, sz * r)

    # ---------------------------------------------------------------- grand staircase with serpent balustrades
    SZ = 40                                   # z of the first step
    for i in range(SUM + 1):
        z = SZ - i
        for x in range(-5, 6):
            for y in range(-3, i):
                bp.set(x, y, z, core.pick(x, y, z), keep=True)
            bp.stairs(x, i, z, "mossy_stone_brick_stairs" if (x * 7 + i * 3) % 5 == 0 else "stone_brick_stairs",
                      "north")
            bp.clear(x, i + 1, z, x, i + 4, z)
        for x in (-8, -7, -6, 6, 7, 8):
            for y in range(-3, i + 1):
                bp.set(x, y, z, "tuff_bricks" if abs(x) == 6 else core.pick(x, y, z))
            bp.set(x, i + 1, z, stair("tuff_brick_stairs", "north"))
            bp.clear(x, i + 2, z, x, i + 4, z)
        if i % 8 == 6:
            for x in (-7, 7):
                bp.set(x, i + 1, z, "chiseled_tuff_bricks")
                bp.set(x, i + 2, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # feathered-serpent heads at the foot of the balustrades
    for side in (-1, 1):
        xs = [side * k for k in (5, 6, 7, 8)]
        x0, x1 = min(xs), max(xs)
        for x in range(x0, x1 + 1):
            for z in range(SZ + 1, SZ + 5):
                for y in range(-2, 4):
                    bp.set(x, y, z, jade.pick(x, y, z))
            bp.set(x, 0, SZ + 5, "mossy_stone_bricks")
            bp.set(x, 3, SZ + 5, "mossy_stone_bricks")
            bp.set(x, 4, SZ + 2, stair("oxidized_cut_copper_stairs", "north"))
            bp.set(x, 4, SZ + 3, stair("oxidized_cut_copper_stairs", "south"))
        for x in range(x0 + 1, x1):
            bp.clear(x, 1, SZ + 3, x, 2, SZ + 5)
            bp.set(x, 1, SZ + 3, "red_carpet")
            bp.set(x, 2, SZ + 5, "pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
            bp.set(x, 1, SZ + 5, "pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]")
        for x in (x0, x1):
            bp.set(x, 3, SZ + 3, "ochre_froglight[axis=y]")
            bp.set(x, 4, SZ + 1, "verdant_froglight[axis=y]")
        bp.set((x0 + x1) // 2, 4, SZ + 1, stair("oxidized_cut_copper_stairs", "north"))

    # ---------------------------------------------------------------- summit sanctuary
    TY = SUM + 1
    tpal = Palette({"tuff_bricks": 3, "mossy_stone_bricks": 2, "stone_bricks": 1, "chiseled_tuff_bricks": 1}, seed=13)
    TX0, TX1, TZ0, TZ1 = -6, 6, -6, 3
    for x in range(-8, 9):
        for z in range(-8, 9):
            bp.set(x, SUM, z, "polished_tuff" if (x + z) % 2 else "tuff_bricks")
    bp.clear(TX0 + 1, TY, TZ0 + 1, TX1 - 1, TY + 7, TZ1 - 1)
    arch.wall_pal(bp, TX0, TY, TZ0, TX1, TY + 6, TZ1, tpal)
    for x in range(TX0, TX1 + 1):
        for z in (TZ0, TZ1):
            bp.set(x, TY + 5, z, "oxidized_cut_copper" if x % 2 else "chiseled_tuff_bricks")
    for z in range(TZ0, TZ1 + 1):
        for x in (TX0, TX1):
            bp.set(x, TY + 5, z, "oxidized_cut_copper" if z % 2 else "chiseled_tuff_bricks")
    for x0_, x1_ in ((-1, 1), (-4, -4), (4, 4)):
        bp.clear(x0_, TY, TZ1, x1_, TY + (3 if x0_ == -1 else 2), TZ1)
    bp.set(-1, TY + 3, TZ1, stair("tuff_brick_stairs", "east", "top"))
    bp.set(1, TY + 3, TZ1, stair("tuff_brick_stairs", "west", "top"))
    bp.clear(0, TY + 3, TZ1, 0, TY + 3, TZ1)
    for x in range(TX0 - 1, TX1 + 2):
        bp.set(x, TY + 6, TZ0 - 1, stair("tuff_brick_stairs", "south", "top"))
        bp.set(x, TY + 6, TZ1 + 1, stair("tuff_brick_stairs", "north", "top"))
    for z in range(TZ0, TZ1 + 1):
        bp.set(TX0 - 1, TY + 6, z, stair("tuff_brick_stairs", "east", "top"))
        bp.set(TX1 + 1, TY + 6, z, stair("tuff_brick_stairs", "west", "top"))
    bp.fill(TX0, TY + 7, TZ0, TX1, TY + 7, TZ1, "tuff_bricks")
    ridge = bp.pyramid_roof(TX0, TZ0, TX1, TZ1, TY + 8, "wayfarers:crimson_roof_tile_stairs", overhang=1,
                            cap="wayfarers:crimson_roof_tile_slab[type=bottom,waterlogged=false]")
    # roof comb: a tall pierced crest on the ridge
    for x in range(-5, 6):
        for z in (-2, -1):
            for y in range(TY + 10, ridge + 9):
                top_cut = abs(x) > 5 - (y - ridge) // 2 if y > ridge + 2 else False
                if top_cut:
                    continue
                hole = (y - TY) % 3 == 1 and x % 2 == 0 and abs(x) < 5 and y < ridge + 7
                if not hole:
                    bp.set(x, y, z, "wayfarers:crimson_roof_tiles" if (y - TY) % 3 == 0 else tpal.pick(x, y, z))
    bp.set(0, ridge + 9, -2, "chiseled_tuff_bricks")
    bp.set(0, ridge + 9, -1, "chiseled_tuff_bricks")
    bp.set(0, ridge + 10, -1, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # portico of four columns over the stair head
    for x in (-6, -2, 2, 6):
        bp.set(x, TY, 7, "chiseled_tuff_bricks")
        bp.fill(x, TY + 1, 7, x, TY + 4, 7, "polished_tuff")
        bp.set(x, TY + 5, 7, "chiseled_tuff")
    for x in range(-7, 8):
        for z in range(TZ1 + 1, 8):
            bp.set(x, TY + 6, z, "tuff_brick_slab[type=bottom,waterlogged=false]" if z < 7 else "tuff_bricks")
        bp.set(x, TY + 6, 8, stair("tuff_brick_stairs", "north", "top"))
    for x in (-4, 0, 4):
        bp.lantern(x, TY + 5, 5, hanging=True)
    # sanctuary interior: altar, jade mask, braziers
    bp.fill(-2, TY, TZ0 + 1, 2, TY, TZ0 + 2, "chiseled_tuff_bricks")
    bp.set(0, TY + 1, TZ0 + 1, "gold_block")
    bp.chest(0, TY + 1, TZ0 + 2, "south", LOOT + "ziggurat")
    for x in (-2, 2):
        bp.set(x, TY + 1, TZ0 + 1, "soul_campfire[facing=south,lit=true,signal_fire=false,waterlogged=false]")
    for (x, y) in ((-1, 3), (1, 3), (0, 2), (-1, 4), (0, 4), (1, 4)):
        bp.set(x, TY + y, TZ0, "oxidized_copper")
    bp.set(-1, TY + 3, TZ0, "verdant_froglight[axis=y]")
    bp.set(1, TY + 3, TZ0, "verdant_froglight[axis=y]")
    for x in (-4, 4):
        bp.lantern(x, TY + 6, -2, hanging=True)
        bp.set(x, TY, TZ0 + 1, "decorated_pot[facing=south,waterlogged=false,cracked=false]")

    # ---------------------------------------------------------------- inner treasure hall and passages
    HX0, HX1, HZ0, HZ1, HTOP = -10, 10, -10, 8, 12
    bp.room(HX0, 0, HZ0, HX1, HTOP, HZ1, "tuff_bricks", floor="polished_tuff", ceiling="tuff_bricks")
    for x in range(HX0 + 1, HX1):
        for z in range(HZ0 + 1, HZ1):
            if (x + z) % 4 == 0:
                bp.set(x, 0, z, "chiseled_tuff")
    for (px, pz) in ((-6, -6), (5, -6), (-6, 3), (5, 3)):
        for dx in (0, 1):
            for dz in (0, 1):
                bp.fill(px + dx, 1, pz + dz, px + dx, HTOP - 1, pz + dz, "chiseled_stone_bricks")
                bp.set(px + dx, 5, pz + dz, "oxidized_cut_copper")
                bp.set(px + dx, HTOP - 1, pz + dz, "tuff_bricks")
    for x in range(HX0 + 1, HX1):
        bp.set(x, HTOP - 1, HZ0 + 1, stair("tuff_brick_stairs", "north", "top"))
        bp.set(x, HTOP - 1, HZ1 - 1, stair("tuff_brick_stairs", "south", "top"))
    # treasure heaps
    for (x, z) in ((-8, -8), (-7, -8), (-8, -7), (8, -8), (7, -8), (8, 6), (-8, 6)):
        bp.set(x, 1, z, rng.choice(["gold_block", "raw_gold_block", "gold_block"]))
    for (x, z) in ((-7, -7), (7, -7), (-8, 5), (8, 5)):
        bp.set(x, 1, z, "decorated_pot[facing=south,waterlogged=false,cracked=false]")
    bp.chest(-9, 1, -2, "east", LOOT + "ziggurat")
    bp.chest(9, 1, -2, "west", LOOT + "ziggurat")
    bp.spawner(0, 1, -1, MOB["ruin_walker"])
    bp.fill(-1, 0, -2, 1, 0, 0, "mossy_stone_bricks")
    for (x, z) in ((-3, -6), (3, -6), (-3, 4), (3, 4)):
        bp.chain(x, HTOP - 2, z, HTOP - 1)
        bp.lantern(x, HTOP - 3, z, hanging=True, soul=True)
    # summit shaft: the trapdoor behind the altar leads down a ladder into the hall
    bp.set(4, SUM, -4, "jungle_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.fill(4, 1, -5, 4, SUM - 1, -5, "chiseled_stone_bricks")
    bp.ladder(4, 1, -4, SUM - 1, "south")
    # west passage from the forecourt, with a guard alcove
    bp.room(-B - 1, 0, -2, HX0, 5, 2, "tuff_bricks", floor="mossy_stone_bricks", ceiling="tuff_bricks")
    for x in range(-B + 2, HX0, 4):
        bp.lantern(x, 4, 0, hanging=True, soul=True)
        bp.set(x, 3, -2, "chiseled_tuff_bricks")
        bp.set(x, 3, 2, "chiseled_tuff_bricks")
    bp.clear(-19, 1, -4, -17, 3, -2)
    bp.spawner(-18, 1, -4, "minecraft:skeleton")
    bp.set(-20, 1, 1, "cobweb")
    bp.set(-14, 3, -1, "cobweb")
    bp.clear(HX0, 1, -1, HX0, 3, 1)
    # carved west doorway
    for z in range(-3, 4):
        for y in range(0, 6):
            if abs(z) == 3 or y == 5:
                bp.set(-B - 1, y, z, "chiseled_tuff_bricks" if (y + z) % 2 else "polished_tuff")
    bp.clear(-B - 1, 1, -1, -B + 1, 3, 1)
    bp.set(-B - 1, 4, 0, "verdant_froglight[axis=y]")
    # secret tomb behind a cracked panel in the hall's north wall (marked by a jade mask)
    bp.room(-4, 0, -17, 4, 7, HZ0, "tuff_bricks", floor="polished_tuff", ceiling="tuff_bricks")
    bp.set(0, 1, HZ0, "cracked_stone_bricks")
    bp.set(0, 2, HZ0, "cracked_stone_bricks")
    bp.set(0, 3, HZ0, "oxidized_copper")
    bp.set(-1, 3, HZ0, "verdant_froglight[axis=y]")
    bp.set(1, 3, HZ0, "verdant_froglight[axis=y]")
    bp.fill(-1, 1, -15, 1, 1, -12, "oxidized_cut_copper")
    bp.fill(-1, 2, -15, 1, 2, -12, "oxidized_cut_copper_slab[type=bottom,waterlogged=false]")
    bp.set(0, 2, -15, "skeleton_skull[powered=false,rotation=8]")
    bp.chest(-3, 1, -14, "east", LOOT + "ziggurat")
    bp.fill(3, 1, -16, 3, 1, -14, "gold_block")
    for (x, z) in ((-3, -16), (3, -12), (-3, -11)):
        bp.set(x, 1, z, "candle[candles=4,lit=true,waterlogged=false]")

    # ---------------------------------------------------------------- forecourt (west) and ball court (east)
    sac = Palette({"calcite": 3, "polished_diorite": 2, "mossy_cobblestone": 1, "moss_block": 1}, seed=14)
    for x in range(-45, -B - 1):
        for z in range(-3, 4):
            bp.set(x, 0, z, sac.pick(x, 0, z))
            bp.fill(x, -3, z, x, -1, z, "dirt", keep=True)
        if x % 5 == 0:
            for z in (-4, 4):
                bp.set(x, 1, z, "polished_tuff")
                bp.set(x, 2, z, "chiseled_tuff_bricks")
                bp.set(x, 3, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
                       if x % 10 == 0 else "tuff_brick_wall")
    for sz in (-1, 1):           # two stepped shrine platforms flanking the causeway
        cz = sz * 14
        for x in range(-44, -33):
            for z in range(cz - 5, cz + 6):
                for y in range(-3, 3):
                    bp.set(x, y, z, core.pick(x, y, z))
                bp.set(x, 2, z, TRIM if abs(z - cz) == 5 or x in (-44, -34) else core.pick(x, 2, z))
        for x in range(-42, -35):
            for z in range(cz - 3, cz + 4):
                for y in range(3, 5):
                    bp.set(x, y, z, core.pick(x, y, z))
        face = "north" if sz < 0 else "south"
        zA, zB = cz - sz * 5, cz - sz * 3
        for x in range(-41, -36):
            for y, z in ((0, zA - sz * 3), (1, zA - sz * 2), (2, zA - sz), (3, zB - sz * 2), (4, zB - sz)):
                bp.stairs(x, y, z, "stone_brick_stairs", face)
                for yy in range(-3, y):
                    bp.set(x, yy, z, core.pick(x, yy, z))
        bp.set(-39, 5, cz, "chiseled_tuff_bricks")
        bp.set(-39, 6, cz, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        for (x, z) in ((-42, cz - 3), (-36, cz - 3), (-42, cz + 3), (-36, cz + 3)):
            bp.fill(x, 5, z, x, 7, z, "polished_tuff")
            bp.set(x, 8, z, "chiseled_tuff")
        bp.set(-39, 5, cz + sz * 2, "chiseled_tuff_bricks")     # carved stela
        bp.set(-39, 6, cz + sz * 2, "chiseled_tuff")
        bp.set(-39, 7, cz + sz * 2, "oxidized_cut_copper")
    # ball court: two sloped walls with stone rings
    for sz in (-1, 1):
        for x in range(B + 4, 46):
            for d in range(0, 4):
                z = sz * (6 + d)
                for y in range(-3, 4 - (0 if d > 0 else 1)):
                    bp.set(x, y, z, core.pick(x, y, z))
                if d == 0:
                    bp.set(x, 3, z, stair("tuff_brick_stairs", "south" if sz < 0 else "north"))
            bp.set(x, 4, sz * 9, "tuff_brick_wall")
        for (dy, dx) in ((5, 0), (6, -1), (6, 1), (7, 0)):
            bp.set(40 + dx, dy, sz * 7, "chiseled_tuff_bricks")
        bp.fill(40, 4, sz * 7, 40, 4, sz * 7, "polished_tuff")
    court = Palette({"packed_mud": 3, "mud_bricks": 2, "moss_block": 1, "coarse_dirt": 1}, seed=16)
    for x in range(B + 4, 46):
        for z in range(-5, 6):
            bp.set(x, 0, z, court.pick(x, 0, z))
    bp.set(40, 0, 0, "chiseled_tuff")

    # ---------------------------------------------------------------- the jungle reclaims it
    arch.moss_on(bp, ((-50, -4, -50), (50, 60, 50)), chance=0.22, seed=3)
    arch.vines_on(bp, ((-B - 2, 1, -B - 2), (B + 2, SUM + 2, SZ + 6)), chance=0.13, seed=4, max_len=7)
    # terraces carpeted with moss, ferns and bushes
    for t in range(1, TIERS):
        r, rb, y = B - INSET * t, B - INSET * (t - 1), TH * t
        for x in range(-rb, rb + 1):
            for z in range(-rb, rb + 1):
                m = max(abs(x), abs(z))
                if not (r + 2 <= m <= rb) or (z > 0 and abs(x) <= 9) or bp.get(x, y, z) is not None:
                    continue
                if bp.get(x, y - 1, z) is None:
                    continue
                q = rng.random()
                if q < 0.32:
                    bp.set(x, y, z, "moss_carpet")
                elif q < 0.36:
                    bp.set(x, y, z, "fern")
                elif q < 0.38:
                    arch.bush(bp, x, y, z, _lvs("jungle_leaves"), r=1)
                elif q < 0.39:
                    bp.set(x, y, z, "azalea")
    # a strangler fig on the north-east terrace pours its roots down the steps
    fx, fy, fz = 18, TH * 4, -19
    _jungle_tree(bp, fx, fy, fz, 13, 21, crown=6)
    for (ex, ez) in ((31, -22), (27, -33), (19, -32), (32, -12), (24, -27)):
        bp.line((fx, fy + 2, fz), (ex, 0, ez), "jungle_wood[axis=y]")
        bp.line((fx + 1, fy + 1, fz), (ex + 1, 0, ez), "jungle_wood[axis=y]")
    for t in range(1, TIERS):
        r, y0 = B - INSET * t, TH * t
        for _ in range(10 - t):
            face = rng.choice(["north", "south", "east", "west"])
            u = rng.randint(-r + 2, r - 2)
            out = rng.randint(2, 3)
            if face == "south" and abs(u) <= 9:
                continue
            ox, oz = arch.FACE_VEC[face]
            x, z = (u, (r + out) * oz) if face in ("north", "south") else ((r + out) * ox, u)
            if bp.get(x, y0, z) is None:
                if rng.random() < 0.6:
                    arch.bush(bp, x, y0, z, _lvs("jungle_leaves"), r=1)
                else:
                    bp.set(x, y0, z, rng.choice(["fern", "moss_carpet", "large_fern[half=lower]"]))
                    if bp.get(x, y0, z) == "minecraft:large_fern":
                        bp.set(x, y0 + 1, z, "large_fern[half=upper]")
    # ground, trees and undergrowth
    gpal = Palette({"grass_block[snowy=false]": 4, "podzol[snowy=false]": 2, "coarse_dirt": 1, "moss_block": 1},
                   seed=15)
    for x in range(-47, 48):
        for z in range(-44, 50):
            if bp.get(x, 0, z) is None and math.hypot(x / 46.5, (z - 3) / 46) < 1 + 0.04 * math.sin(x * 0.3 + z):
                bp.set(x, 0, z, gpal.pick(x, 0, z))
                bp.set(x, -1, z, "dirt")
    for (tx, tz, h, sd) in ((-39, -27, 24, 1), (-40, 27, 20, 2), (37, -32, 26, 3), (40, 23, 21, 4),
                            (-20, -39, 19, 5), (6, -40, 23, 6), (-30, 39, 18, 7), (39, 36, 22, 8),
                            (40, -17, 19, 10), (-31, -37, 15, 12), (20, 40, 16, 13)):
        _jungle_tree(bp, tx, 1, tz, h, sd, crown=6 if h > 20 else 5)
    for _ in range(700):
        x, z = rng.randint(-47, 47), rng.randint(-44, 49)
        g = bp.get(x, 0, z)
        if g not in ("minecraft:grass_block", "minecraft:podzol", "minecraft:moss_block") or bp.get(x, 1, z):
            continue
        r = rng.random()
        if r < 0.3:
            bp.set(x, 1, z, "fern")
        elif r < 0.45:
            bp.set(x, 1, z, "large_fern[half=lower]")
            bp.set(x, 2, z, "large_fern[half=upper]")
        elif r < 0.55:
            h = rng.randint(3, 7)
            for k in range(1, h + 1):
                bp.set(x, k, z, f"bamboo[age=1,leaves={'large' if k >= h - 1 else 'small' if k == h - 2 else 'none'},stage=0]")
        elif r < 0.62:
            arch.bush(bp, x, 1, z, _lvs("jungle_leaves"), r=1)
        elif r < 0.66:
            bp.set(x, 1, z, "melon")
        else:
            bp.set(x, 1, z, "short_grass")


register(StructureDef(
    "jungle_ziggurat", "overworld", ["jungle", "sparse_jungle", "bamboo_jungle"],
    [Piece("ziggurat", ziggurat)], spacing=30, separation=10,
    spawns=[(MOB["ruin_walker"], 10, 1, 3), ("minecraft:skeleton", 5, 1, 2)],
    title_fr="Ziggourat de la jungle", title_en="Jungle Ziggurat"))

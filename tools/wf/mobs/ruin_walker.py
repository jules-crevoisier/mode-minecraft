"""Ruin Walker (Rôdeur des ruines): a stocky moss-grown stone sentinel, about 2.1 blocks tall.

Silhouette idea: a piece of a ruined temple that got up and walked. A deeply hunched barrel chest of mossy stone
bricks with the broken stump of a fluted column still standing on its back (a fern growing out of the break), a
small lichen-crusted head sunk low between boulder shoulders under heavy moss mantles that sway as it moves,
glowing green eyes and rune channels, a rusted iron collar trailing a broken chain, short pillar legs on slab feet
and long gorilla arms ending in two huge boulder fists that nearly drag on the ground (a heavy two-handed slam).
Moss and lichen are painted in clumps and rosettes, never as scattered texels.
"""
import math

from ..models import Model
from ..texgen import mix, mul

# ------------------------------------------------------------------ palette
STONE = (126, 124, 116)
STONE_L = (156, 154, 144)
STONE_D = (88, 87, 82)
MORTAR = (64, 64, 60)
MOSS = (82, 116, 46)
MOSS_L = (122, 156, 64)
MOSS_D = (50, 78, 32)
LICHEN = (164, 176, 128)
LICHEN_Y = (196, 180, 92)
IRON = (74, 66, 62)
IRON_D = (46, 42, 40)
RUST = (166, 84, 38)
RUST_L = (204, 118, 56)
RUNE = (120, 255, 140)
RUNE_D = (60, 170, 90)
EYE = (190, 255, 150)
VOID = (22, 26, 20)

FACE_N = {"top": 1, "bottom": 2, "front": 3, "back": 4, "left": 5, "right": 6}


def _h(*v):
    """Deterministic hash of integers -> 0..65535."""
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# ------------------------------------------------------------------ paints
def moss_px(x, y, seed=0):
    """A clumpy moss texel: the face is split into small cushions (3 x 2 texel cells), each of one of three greens,
    lit along its top row, with a dark hollow at its lower left corner."""
    cx, cy = (x + (y // 2) % 2) // 3, y // 2
    tone = _h(cx, cy, seed, 11) % 3
    c = (MOSS, mix(MOSS, MOSS_L, 0.45), mix(MOSS, MOSS_D, 0.35))[tone]
    if y % 2 == 0:
        c = mix(c, MOSS_L, 0.35)                                     # the lit top of the cushion
    elif (x + (y // 2) % 2) % 3 == 0:
        c = mix(c, MOSS_D, 0.55)                                     # the hollow between two cushions
    return c


def stone(seed=0, moss=0.0, brick_w=6, brick_h=4, base=STONE, cracks=True):
    """Weathered stone bricks: staggered courses, mortar lines, a lit top edge per brick, chips and cracks,
    and moss that creeps down from the top of the face (``moss`` = 0..1, how far it reaches)."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face in ("top", "bottom"):
            if face == "top" and moss > 0:
                return moss_px(x, y, seed)
            row, yy = y // brick_h, y % brick_h
        else:
            row, yy = y // brick_h, y % brick_h
        off = (row % 2) * (brick_w // 2) + _h(seed, row, fid) % 2
        col = (x + off) // brick_w
        xx = (x + off) % brick_w
        # moss reach: strongest at the top, with drips hanging down some columns
        if moss > 0 and face != "bottom":
            t = y / max(1, h - 1)
            drip = 0.35 if _h(seed, x // 2, fid) % 4 == 0 else 0.0
            v = moss * 1.15 - t + drip + (_h(seed, x // 2, y // 2, fid) % 100) / 500
            if v > 0.25:
                return moss_px(x, y, seed + fid)
            if v > 0.05 and (yy == brick_h - 1 or xx == brick_w - 1):
                return MOSS_D  # moss grows into the mortar first
        if yy == brick_h - 1 or xx == brick_w - 1:
            return MORTAR
        tone = 0.86 + (_h(seed, row, col, fid) % 26) / 100
        c = mul(base, tone)
        if yy == 0:
            c = mix(c, STONE_L, 0.45)          # lit top edge of the brick
        elif yy == brick_h - 2:
            c = mix(c, STONE_D, 0.3)           # shaded underside
        if xx == 0:
            c = mix(c, STONE_L, 0.18)
        if _h(seed, row, col, fid, 5) % 4 == 0 and xx == 1 + _h(seed, row, col, 6) % max(1, brick_w - 3) \
                and yy == 1 + _h(seed, row, col, 7) % max(1, brick_h - 2):
            c = mix(c, STONE_D, 0.6)           # one chip on some bricks
        if cracks and _h(seed, row, col, 9) % 5 == 0 and xx == (yy + _h(seed, row, col) % 3) % (brick_w - 1):
            c = mix(c, (40, 40, 38), 0.7)      # a diagonal crack across this brick
        return c
    return f


def K_lit(seed, fx, fy, fid):
    """Whether a boulder facet catches the light along its upper edge."""
    return _h(seed, fx, fy, fid, 8) % 2 == 0


def boulder(seed=0, moss_top=True):
    """Rough boulder (shoulders, fists): no courses, large lit/shadowed facets and moss on top."""
    def f(face, x, y, w, h):
        fid = FACE_N[face]
        if face == "top" and moss_top:
            return moss_px(x, y, seed)
        if face == "bottom":
            return STONE_D
        if moss_top and y <= (1 if _h(seed, x, fid) % 3 else 2):
            return moss_px(x, y, seed + fid)
        fx, fy = (x + _h(seed, fid) % 3) // 3, (y + _h(seed, fid, 1) % 3) // 3
        c = mul(STONE, 0.86 + (_h(seed, fx, fy, fid) % 28) / 100)
        if (x + _h(seed, fy) % 4) % 5 == 0:
            c = mix(c, STONE_D, 0.35)          # facet edges
        if y == 0 or (fy * 3 - _h(seed, fid, 1) % 3 == y and K_lit(seed, fx, fy, fid)):
            c = mix(c, STONE_L, 0.35)          # the lit upper edge of a facet
        if y < h // 2 and _h(x // 5, y // 5, seed) % 3 == 0:
            return lichen_spot(x, y, seed + fid + 50) or c
        return c
    return f


def mossy_drape(seed=0, depth=3):
    """Moss mantle: green top, sides hanging in ragged clumps (transparent below the drips)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return MOSS_D
        if face == "top":
            if _h(x // 5, y // 5, seed, 3) % 3 == 0:
                return lichen_spot(x, y, seed) or moss_px(x, y, seed)
            return moss_px(x, y, seed)
        cut = h - 1 - (_h(seed, x // 2, FACE_N[face]) % depth)
        if y > cut:
            return None
        c = moss_px(x, y, seed + FACE_N[face])
        if y == cut:
            c = mix(c, MOSS_D, 0.5)
        return c
    return f


def lichen_spot(x, y, seed):
    """Lichen rosettes: one round patch per 5 x 5 cell picked by the seed (pale rim, ochre heart)."""
    cx, cy = x // 5, y // 5
    if _h(cx, cy, seed, 31) % 3:
        return None
    ox, oy = 1 + _h(cx, cy, seed, 1) % 2, 1 + _h(cx, cy, seed, 2) % 2
    d = abs(x % 5 - ox) + abs(y % 5 - oy)
    if d == 0:
        return mul(LICHEN_Y, 0.85)
    if d == 1:
        return LICHEN_Y if _h(cx, cy, seed) % 2 else LICHEN
    if d == 2:
        return mix(LICHEN, (230, 236, 200), 0.25)
    return None


def lichen(seed=0):
    """Lichen crust: grey-green and ochre rosettes over cushions of moss, a ragged lower edge."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return STONE_D
        if face != "top" and y >= h - 1 and _h(seed, x // 2) % 2:
            return None
        return lichen_spot(x, y, seed + FACE_N[face]) or moss_px(x, y, seed)
    return f


def fluted(seed=0):
    """A broken fluted column: pale stone with vertical flutes (a shadow groove every third texel), a lit top row,
    moss climbing up from the bottom and a dark rain stain; the top face is the rough break."""
    def f(face, x, y, w, h):
        if face == "top":
            return mix(STONE_D, STONE, 0.5) if (x + y) % 3 else (60, 60, 56)
        if face == "bottom":
            return STONE_D
        if y >= h - 2 - _h(seed, x // 2, FACE_N[face]) % 3:
            return moss_px(x, y, seed + FACE_N[face])
        c = mix(STONE_L, STONE, 0.3)
        if x % 3 == 2:
            c = mix(c, STONE_D, 0.45)                                 # the flute
        elif x % 3 == 0:
            c = mix(c, (220, 218, 206), 0.25)
        if y == 0:
            c = mix(c, (220, 218, 206), 0.3)
        if _h(x, seed, FACE_N[face]) % 5 == 0 and y < h // 2:
            c = mix(c, (70, 70, 64), 0.25)
        return c
    return f


def rusty(seed=0, rivets=4):
    """Rusted iron band: dark iron, orange rust bleeding down in streaks, a row of rivets."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            return mix(IRON, RUST, 0.35) if face == "top" else IRON_D
        if y == 0:
            return mix(IRON, (120, 110, 100), 0.4)
        if y == h - 1:
            return IRON_D
        if rivets and y == 1 and x % rivets == 1:
            return (138, 124, 112)
        streak = _h(seed, x, FACE_N[face]) % 5
        if streak == 0:
            return RUST_L if y % 2 else RUST
        if streak == 1 and y >= h // 2:
            return mix(IRON, RUST, 0.6)
        r = _h(x, y, seed)
        if r % 7 == 0:
            return mix(IRON, RUST, 0.5)
        return mul(IRON, 0.92 + (r % 15) / 100)
    return f


def framed_lock(face, x, y, w, h):
    if face in ("front", "back") and x == 1 and y == 1:
        return (30, 26, 24)  # keyhole
    return RUST_L if (x + y) % 3 == 0 else (120, 100, 86)


def fern(seed=0):
    """A small fern frond on a transparent plane: a stem with alternating leaflets."""
    def f(face, x, y, w, h):
        mid = w // 2
        if x == mid and y >= 1:
            return (60, 92, 36)
        dy = abs(x - mid)
        if 0 < dy <= 2 and (y + dy + seed) % 2 == 0 and y >= dy - 1 and y < h - 1:
            return MOSS_L if (x + y) % 3 else (88, 132, 52)
        return None
    return f


# ------------------------------------------------------------------ runes
def rune_tree(cx, y0, y1):
    """A carved rune channel: a vertical line with forked branches and a diamond eye at the top."""
    pts = {(cx, y) for y in range(y0 + 2, y1 + 1)}
    pts |= {(cx, y0), (cx - 1, y0 + 1), (cx + 1, y0 + 1), (cx, y0 + 2)}
    for i, by in enumerate(range(y0 + 4, y1, 3)):
        sgn = 1 if i % 2 == 0 else -1
        pts |= {(cx + sgn, by), (cx + 2 * sgn, by - 1), (cx + 3 * sgn, by - 1)}
        pts |= {(cx - sgn, by + 1), (cx - 2 * sgn, by + 2)}
    return pts


def with_runes(base, face_name, pts, colour=RUNE):
    def f(face, x, y, w, h):
        if face == face_name and (x, y) in pts:
            return colour
        return base(face, x, y, w, h)
    return f


def glow_at(face_name, pts, colour=RUNE):
    return {face_name: lambda f_, x, y, w, h: colour if (x, y) in pts else None, "*": None}


# ------------------------------------------------------------------ model
def mirror(x, w):
    return -(x + w)


def wave(anim, part, length, amp, phase=0.0, base=(0, 0, 0), kind="rot", n=8):
    """A seamless sine loop: base + amp * sin(2 pi (t / length + phase))."""
    keys = []
    for i in range(n + 1):
        sn = math.sin(2 * math.pi * (i / n + phase))
        keys.append((round(length * i / n, 4), tuple(round(base[k] + amp[k] * sn, 3) for k in range(3))))
    getattr(anim, kind)(part, *keys)


def build():
    m = Model("ruin_walker", seed=21, shadow=0.9, walk_speed=1.1, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -12, 0))
    m.part("torso", "hips", pivot=(0, -2, 1), rot=(22, 0, 0))
    m.part("head", "torso", pivot=(0, -13.5, -6.5), rot=(-24, 0, 0))
    m.part("jaw", "head", pivot=(0, 0, -1))
    m.part("chain", "torso", pivot=(-4, -13, -8.5), rot=(-22, 0, 0))
    m.part("mantle_r", "torso", pivot=(-6.5, -17, 0))
    m.part("mantle_l", "torso", pivot=(6.5, -17, 0))
    m.part("ruin", "torso", pivot=(3, -16.5, 3), rot=(-14, 0, 16))
    m.part("ruin_fern", "ruin", pivot=(-1, -7, 0), rot=(0, 0, -25))
    m.part("arm_r", "torso", pivot=(-10.5, -13, 0), rot=(-26, 0, 8))
    m.part("forearm_r", "arm_r", pivot=(0, 9, 0), rot=(-8, 0, -4))
    m.part("arm_l", "torso", pivot=(10.5, -13, 0), rot=(-26, 0, -8))
    m.part("forearm_l", "arm_l", pivot=(0, 9, 0), rot=(-8, 0, 4))
    m.part("fern", "arm_l", pivot=(1, -4, 1))
    m.part("leg_r", "bone", pivot=(-4.5, -12, 0))
    m.part("leg_l", "bone", pivot=(4.5, -12, 0))

    # ------------------------------------------------------------------ body
    m.box("hips", -7, -3, -5, 14, 5, 10, stone(seed=1, moss=0.2))
    m.box("hips", -7.5, 1, -5.5, 15, 3, 11, mossy_drape(2, depth=2))             # a moss skirt over the belt
    # barrel chest of stone bricks, a carved rune column down the sternum
    chest_runes = rune_tree(7, 1, 9)
    chest = stone(seed=2, moss=0.1)
    m.box("torso", -8, -15, -6, 16, 11, 11, {"front": with_runes(chest, "front", chest_runes), "*": chest},
          glow=glow_at("front", chest_runes))
    m.box("torso", -6, -5, -5, 12, 6, 9, stone(seed=3, moss=0.0, brick_w=5))
    m.box("torso", -7, -17.5, -1, 14, 4, 7, stone(seed=4, moss=0.6))              # the hump of the back
    # rusted iron collar around the neck, its lock plate and the broken chain hanging from it
    m.box("torso", -5.5, -17.5, -7.5, 11, 4, 10, rusty(7))
    m.box("torso", -1.5, -15, -8.5, 3, 3, 1, framed_lock)
    for i in range(4):
        w_, d_ = (1, 2) if i % 2 else (2, 1)
        m.box("chain", -w_ / 2, i * 2, -d_ / 2, w_, 2, d_, rusty(30 + i, rivets=0))
    m.box("chain", -1.5, 8, -0.5, 3, 1, 1, rusty(34, rivets=0))                    # the snapped link
    # heavy moss mantles on the shoulders (they sway)
    m.box("mantle_r", -3.5, 0, -6, 7, 5, 12, mossy_drape(5))
    m.box("mantle_l", -3.5, 0, -6, 7, 5, 12, mossy_drape(6))
    # the broken stump of a fluted column on its back, a capital ring at its foot, a fern from the break
    m.box("ruin", -2.5, -7, -2.5, 5, 7, 5, fluted(8))
    m.box("ruin", -3.5, -1, -3.5, 7, 2, 7, stone(seed=9, moss=0.5, brick_w=7, brick_h=2, cracks=False))
    m.box("ruin", 0.5, -8, -2.5, 2, 1, 3, fluted(10))                            # a jagged corner left standing
    m.box("ruin_fern", 0, -4, -2.5, 0, 4, 5, {"left": fern(3), "right": fern(3), "*": None})
    m.box("ruin_fern", -2.5, -4, 0, 5, 4, 0, {"front": fern(4), "back": fern(4), "*": None})

    # head: small, sunk low between the shoulders, lichen crusted, heavy brow over deep-set glowing eyes
    eye_pts = {(1, 4), (2, 4), (5, 4), (6, 4)}
    socket_pts = {(1, 3), (2, 3), (5, 3), (6, 3), (0, 4), (3, 4), (4, 4), (7, 4)}

    def face_paint(f_, x, y, w, h):
        if (x, y) in eye_pts:
            return EYE
        if (x, y) in socket_pts:
            return VOID
        if y == 6 and 2 <= x <= 5:
            return (44, 44, 40)
        if y in (0, 1):
            return mix(STONE, STONE_L, 0.3)
        return stone(seed=8, moss=0.0, brick_w=4, brick_h=3, cracks=False)(f_, x, y, w, h)
    m.box("head", -4, -7, -5, 8, 8, 8, {"front": face_paint, "*": stone(seed=8, moss=0.2, brick_w=4, brick_h=3)},
          glow={"front": lambda f_, x, y, w, h: EYE if (x, y) in eye_pts else None, "*": None})
    m.box("head", -5, -9, -6, 10, 2, 10, lichen(9))                               # lichen cap
    m.box("head", 1, -10, -4, 5, 1, 6, lichen(14))
    m.box("head", 4.5, -8, -5, 1, 4, 8, lichen(15))
    m.box("head", -5, -6, -7, 10, 2, 2, boulder(10, moss_top=False))              # brow ridge
    m.box("jaw", -4, 0, -5, 8, 3, 7, stone(seed=12, brick_w=4, brick_h=3))
    m.box("jaw", -3, 3, -5, 6, 2, 1, mossy_drape(13, depth=2))                    # moss beard

    # ------------------------------------------------------------------ arms: long, gorilla-like, boulder fists
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"

        def bx(part, x, y, z, w, h, d, paint, glow=None):
            m.box(part, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        bx(arm, -5, -4, -5, 8, 7, 10, boulder(20 + sx))
        arm_runes = {(x, 3) for x in range(6)}
        up = stone(seed=22 + sx, brick_w=4, brick_h=3)
        rp = {k: with_runes(up, k, arm_runes) for k in ("front", "back", "left", "right")}
        bx(arm, -3, 3, -3, 6, 7, 6, {**rp, "*": up},
           glow={k: (lambda pts: lambda f_, x, y, w, h: RUNE if (x, y) in pts else None)(arm_runes)
                 for k in ("front", "back", "left", "right")})
        fore_runes = {(3 + (y % 4 if y % 4 < 2 else 4 - y % 4) - 1, y) for y in range(0, 8)} | {(2, 3), (5, 3)}
        fp = stone(seed=24 + sx, brick_w=4, brick_h=3, moss=0.1)
        bx(fore, -4, 0, -4, 8, 8, 8, {"front": with_runes(fp, "front", fore_runes), "*": fp},
           glow=glow_at("front", fore_runes))
        bx(fore, -4.5, 8, -4.5, 9, 6, 9, boulder(26 + sx, moss_top=False))
        bx(fore, -4.5, 9, -5.5, 9, 3, 1, lambda f_, x, y, w, h: STONE_L if y == 0 else STONE if x % 3 else STONE_D)
    # a fern grows out of the left shoulder boulder (asymmetry; crossed planes)
    m.box("fern", 0, -5, -2.5, 0, 6, 5, {"left": fern(1), "right": fern(1), "*": None})
    m.box("fern", -2.5, -5, 0, 5, 6, 0, {"front": fern(2), "back": fern(2), "*": None})

    # ------------------------------------------------------------------ legs: short pillars on slab feet
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"

        def bx(x, y, z, w, h, d, paint):
            m.box(leg, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint)
        bx(-3.5, 0, -3.5, 7, 10, 7, stone(seed=40 + sx, brick_w=4, brick_h=3, moss=0.12))
        bx(-4.5, 9, -5.5, 9, 3, 10, boulder(42 + sx, moss_top=False))
        bx(-4.5, 2, -4.5, 9, 2, 9, mossy_drape(44 + sx, depth=2))

    _anims(m)
    return m


def _anims(m):
    sides = (("r", -1), ("l", 1))
    # idle: slow stone breathing, the head scans left and right, the mantles and ferns sway a beat behind, the
    # chain swings, the jaw grinds
    idle = m.anim("idle", 3.2)
    idle.rot("torso", (0, (0, 0, 0)), (1.6, (2.5, 0, 0)), (3.2, (0, 0, 0)))
    idle.pos("torso", (0, (0, 0, 0)), (1.6, (0, 0.5, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (0, 10, 0)), (1.6, (2, 0, 0)), (2.4, (0, -10, 0)), (3.2, (0, 0, 0)))
    wave(idle, "chain", 3.2, (4, 0, 8), 0.0)
    idle.rot("jaw", (0, (0, 0, 0)), (2.2, (0, 0, 0)), (2.5, (10, 0, 0)), (2.7, (6, 0, 0)), (2.9, (10, 0, 0)),
             (3.2, (0, 0, 0)))
    wave(idle, "fern", 3.2, (6, 0, 8), 0.2)
    wave(idle, "ruin_fern", 3.2, (8, 0, -6), 0.35)
    for side, sx in sides:
        wave(idle, f"arm_{side}", 3.2, (-3, 0, 2 * -sx), 0.0)
        wave(idle, f"forearm_{side}", 3.2, (-4, 0, 0), 0.12)
        wave(idle, f"mantle_{side}", 3.2, (0, 0, 3 * sx), 0.15)

    # walk: a heavy stomp; the hips roll over the planted foot, the torso twists against them, the long arms swing
    # with the boulder fists dragging a beat behind, the chain, mantles and ferns bounce after every footfall
    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.8, (-22, 0, 0)), (1.6, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.8, (22, 0, 0)), (1.6, (-22, 0, 0)))
    walk.rot("hips", (0, (0, 0, 4)), (0.8, (0, 0, -4)), (1.6, (0, 0, 4)))
    walk.rot("torso", (0, (0, 6, -2)), (0.8, (0, -6, 2)), (1.6, (0, 6, -2)))
    walk.rot("head", (0, (0, -4, 2)), (0.8, (0, 4, -2)), (1.6, (0, -4, 2)))
    walk.rot("arm_r", (0, (-16, 0, 0)), (0.8, (16, 0, 0)), (1.6, (-16, 0, 0)))
    walk.rot("arm_l", (0, (16, 0, 0)), (0.8, (-16, 0, 0)), (1.6, (16, 0, 0)))
    wave(walk, "forearm_r", 1.6, (-12, 0, 0), 0.32)
    wave(walk, "forearm_l", 1.6, (12, 0, 0), 0.32)
    walk.rot("chain", (0, (-10, 0, 0)), (0.4, (10, 0, 0)), (0.8, (-10, 0, 0)), (1.2, (10, 0, 0)), (1.6, (-10, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.4, (0, 1.2, 0)), (0.8, (0, 0, 0)), (1.2, (0, 1.2, 0)), (1.6, (0, 0, 0)))
    for side, sx in sides:
        walk.rot(f"mantle_{side}", (0, (0, 0, 0)), (0.1, (0, 0, 6 * sx)), (0.4, (0, 0, -2 * sx)), (0.8, (0, 0, 0)),
                 (0.9, (0, 0, 6 * sx)), (1.2, (0, 0, -2 * sx)), (1.6, (0, 0, 0)))
    walk.rot("ruin", (0, (0, 0, 0)), (0.1, (3, 0, 0)), (0.4, (-1, 0, 0)), (0.8, (0, 0, 0)), (0.9, (3, 0, 0)),
             (1.2, (-1, 0, 0)), (1.6, (0, 0, 0)))
    walk.rot("ruin_fern", (0, (0, 0, 0)), (0.15, (14, 0, 0)), (0.5, (-6, 0, 0)), (0.8, (0, 0, 0)), (0.95, (14, 0, 0)),
             (1.3, (-6, 0, 0)), (1.6, (0, 0, 0)))
    wave(walk, "fern", 1.6, (10, 0, 0), 0.3)

    # slam: rears back onto its heels with both fists raised high over the head (telegraph to 0.55 s), smashes them
    # down together at 0.7 s (14 ticks): the whole body drops into the blow, the mantles and the column lurch
    a = m.anim("slam", 1.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (-160, 0, 20)), (0.55, (-172, 0, 18)), (0.7, (-58, 0, -12), "linear"),
          (1.0, (-54, 0, -12)), (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (-160, 0, -20)), (0.55, (-172, 0, -18)), (0.7, (-58, 0, 12), "linear"),
          (1.0, (-54, 0, 12)), (1.4, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.55, (-35, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.55, (-35, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.45, (-22, 0, 0)), (0.55, (-26, 0, 0)), (0.7, (30, 0, 0), "linear"),
          (0.8, (34, 0, 0)), (1.0, (28, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-14, 0, 0)), (0.7, (-14, 0, 0)), (1.0, (-10, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.5, (20, 0, 0)), (0.7, (0, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.55, (0, 1.5, 1.5)), (0.7, (0, -2.5, -2), "linear"), (1.0, (0, -2.5, -2)),
          (1.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.55, (-6, 0, 0)), (0.7, (-18, 0, 4)), (1.0, (-18, 0, 4)), (1.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.55, (6, 0, 0)), (0.7, (12, 0, -4)), (1.0, (12, 0, -4)), (1.4, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.55, (30, 0, 0)), (0.75, (-40, 0, 0)), (1.0, (20, 0, 0)), (1.4, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"mantle_{side}", (0, (0, 0, 0)), (0.55, (0, 0, -6 * sx)), (0.75, (10, 0, 12 * sx)), (0.95, (-4, 0, -4 * sx)),
              (1.4, (0, 0, 0)))
    a.rot("ruin", (0, (0, 0, 0)), (0.55, (-6, 0, 0)), (0.75, (8, 0, 0)), (0.95, (-3, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("ruin_fern", (0, (0, 0, 0)), (0.55, (-20, 0, 0)), (0.78, (30, 0, 0)), (1.0, (-10, 0, 0)), (1.4, (0, 0, 0)))

    # awaken: the dormant sentinel lifts itself, spreads its arms and shakes the moss off (on spotting prey)
    a = m.anim("awaken", 1.8)
    a.rot("torso", (0, (0, 0, 0)), (0.25, (30, 0, 0)), (0.85, (-16, 0, 0)), (1.0, (-14, 0, 4)), (1.15, (-14, 0, -4)),
          (1.3, (-12, 0, 2)), (1.8, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.25, (30, 0, 0)), (0.85, (-28, 0, 0)), (1.3, (-24, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("jaw", (0, (0, 0, 0)), (0.25, (0, 0, 0)), (0.85, (28, 0, 0)), (1.3, (28, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (20, 0, 0)), (0.85, (-40, 0, 42)), (1.3, (-36, 0, 38)), (1.8, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.25, (20, 0, 0)), (0.85, (-40, 0, -42)), (1.3, (-36, 0, -38)), (1.8, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.85, (-40, 0, 0)), (1.3, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.85, (-40, 0, 0)), (1.3, (-40, 0, 0)), (1.8, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.25, (0, -2, 0)), (0.85, (0, 1, 0)), (1.3, (0, 0, 0)), (1.8, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.85, (-30, 0, 0)), (1.0, (0, 0, 20)), (1.15, (0, 0, -20)), (1.8, (0, 0, 0)))
    for side, sx in sides:
        a.rot(f"mantle_{side}", (0, (0, 0, 0)), (0.85, (0, 0, 8 * sx)), (1.0, (0, 0, 18 * sx)), (1.15, (0, 0, -6 * sx)),
              (1.3, (0, 0, 12 * sx)), (1.5, (0, 0, -3 * sx)), (1.8, (0, 0, 0)))
    a.rot("ruin_fern", (0, (0, 0, 0)), (0.85, (-15, 0, 0)), (1.0, (20, 0, 15)), (1.15, (-10, 0, -15)), (1.3, (12, 0, 8)),
          (1.8, (0, 0, 0)))
    a.rot("fern", (0, (0, 0, 0)), (1.0, (0, 0, 20)), (1.15, (0, 0, -20)), (1.3, (0, 0, 10)), (1.8, (0, 0, 0)))

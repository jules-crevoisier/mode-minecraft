"""Ruin Walker (Rôdeur des ruines): a stocky moss-grown stone sentinel, about 2.1 blocks tall.

Silhouette: a hunched barrel chest of mossy stone bricks under a heavy moss mantle, a small lichen-crusted
head sunk between the shoulders, glowing green eyes and rune lines, a rusted iron collar trailing a broken
chain, and two huge boulder fists that nearly drag on the ground (a heavy two-handed slam).
"""
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
    """A clumpy moss texel: mid green with light tufts and dark hollows."""
    r = _h(x, y, seed, 11)
    if r % 6 == 0:
        return MOSS_L
    if r % 7 == 0:
        return MOSS_D
    if (x + y * 2 + seed) % 5 == 0:
        return mix(MOSS, MOSS_L, 0.35)
    return MOSS


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
            v = moss * 1.15 - t + drip + (_h(seed, x, y // 2, fid) % 100) / 400
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
        r = _h(x, y, seed, fid, 5)
        if r % 17 == 0:
            c = mix(c, STONE_D, 0.6)           # pits
        elif r % 23 == 0:
            c = mix(c, STONE_L, 0.4)
        if cracks and _h(seed, row, col, 9) % 5 == 0 and xx == (yy + _h(seed, row, col) % 3) % (brick_w - 1):
            c = mix(c, (40, 40, 38), 0.7)      # a diagonal crack across this brick
        return c
    return f


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
        r = _h(x, y, seed, fid)
        if r % 13 == 0:
            c = mix(c, STONE_L, 0.45)
        elif r % 19 == 0:
            c = mix(c, (52, 52, 48), 0.6)
        if r % 29 == 0:
            c = mix(c, LICHEN, 0.6)
        return c
    return f


def mossy_drape(seed=0, depth=3):
    """Moss mantle: green top, sides hanging in ragged clumps (transparent below the drips)."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return MOSS_D
        if face == "top":
            c = moss_px(x, y, seed)
            if _h(x, y, seed, 3) % 31 == 0:
                return LICHEN_Y
            return c
        cut = h - 1 - (_h(seed, x // 2, FACE_N[face]) % depth)
        if y > cut:
            return None
        c = moss_px(x, y, seed + FACE_N[face])
        if y == cut:
            c = mix(c, MOSS_D, 0.5)
        return c
    return f


def lichen(seed=0):
    """Lichen crust: grey-green rosettes and ochre spots over moss."""
    def f(face, x, y, w, h):
        r = _h(x // 2, y // 2, seed, FACE_N[face])
        if face == "bottom":
            return STONE_D
        if face != "top" and y >= h - 1 and _h(seed, x) % 2:
            return None
        if r % 5 == 0:
            return LICHEN_Y if _h(x, y, seed) % 3 else mul(LICHEN_Y, 0.85)
        if r % 3 == 0:
            return LICHEN if (x + y) % 2 else mix(LICHEN, (230, 236, 200), 0.3)
        return moss_px(x, y, seed)
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


def build():
    m = Model("ruin_walker", seed=21, shadow=0.9, walk_speed=1.1, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("hips", "bone", pivot=(0, -12, 0))
    m.part("torso", "hips", pivot=(0, -2, 0), rot=(12, 0, 0))
    m.part("head", "torso", pivot=(0, -15, -5), rot=(-12, 0, 0))
    m.part("jaw", "head", pivot=(0, 0, -1))
    m.part("chain", "torso", pivot=(-4, -14, -8.5))
    m.part("arm_r", "torso", pivot=(-10.5, -13, 0), rot=(-10, 0, 6))
    m.part("forearm_r", "arm_r", pivot=(0, 10, 0), rot=(-18, 0, -4))
    m.part("arm_l", "torso", pivot=(10.5, -13, 0), rot=(-10, 0, -6))
    m.part("forearm_l", "arm_l", pivot=(0, 10, 0), rot=(-18, 0, 4))
    m.part("leg_r", "bone", pivot=(-4.5, -12, 0))
    m.part("leg_l", "bone", pivot=(4.5, -12, 0))

    # ------------------------------------------------------------------ body
    # pelvis block with a mossy ledge
    m.box("hips", -7, -3, -5, 14, 5, 10, stone(seed=1, moss=0.2))
    # barrel chest of stone bricks, a carved rune column down the sternum
    chest_runes = rune_tree(7, 1, 9)
    chest = stone(seed=2, moss=0.1)
    m.box("torso", -8, -15, -6, 16, 11, 11, {"front": with_runes(chest, "front", chest_runes), "*": chest},
          glow=glow_at("front", chest_runes))
    # narrower belly
    m.box("torso", -6, -5, -5, 12, 6, 9, stone(seed=3, moss=0.0, brick_w=5))
    # back hump with a heavy moss mantle on each shoulder
    m.box("torso", -7, -17, -1, 14, 3, 7, stone(seed=4, moss=0.6))
    m.box("torso", -10, -17, -6, 7, 4, 12, mossy_drape(5))
    m.box("torso", 3, -17, -6, 7, 4, 12, mossy_drape(6))
    # rusted iron collar around the neck
    m.box("torso", -5.5, -17.5, -7.5, 11, 4, 10, rusty(7))
    m.box("torso", -1.5, -15, -8.5, 3, 3, 1, framed_lock)  # the lock plate
    # broken chain hanging from the collar
    for i in range(4):
        w_, d_ = (1, 2) if i % 2 else (2, 1)
        m.box("chain", -w_ / 2, i * 2, -d_ / 2, w_, 2, d_, rusty(30 + i, rivets=0))

    # head: small, sunk between the shoulders, lichen crusted, heavy brow over deep-set glowing eyes
    eye_pts = {(1, 4), (2, 4), (5, 4), (6, 4)}
    socket_pts = {(1, 3), (2, 3), (5, 3), (6, 3), (0, 4), (3, 4), (4, 4), (7, 4)}

    def face_paint(f_, x, y, w, h):
        if (x, y) in eye_pts:
            return EYE
        if (x, y) in socket_pts:
            return VOID
        if y == 6 and 2 <= x <= 5:
            return (44, 44, 40)  # mouth crack
        if y in (0, 1):
            return mix(STONE, STONE_L, 0.3)
        return stone(seed=8, moss=0.0, brick_w=4, brick_h=3, cracks=False)(f_, x, y, w, h)
    m.box("head", -4, -7, -5, 8, 8, 8, {"front": face_paint, "*": stone(seed=8, moss=0.2, brick_w=4, brick_h=3)},
          glow={"front": lambda f_, x, y, w, h: EYE if (x, y) in eye_pts else None, "*": None})
    m.box("head", -5, -9, -6, 10, 2, 10, lichen(9))                 # lichen cap
    m.box("head", 1, -10, -4, 5, 1, 6, lichen(14))                   # lichen spilling over one side
    m.box("head", 4.5, -8, -5, 1, 4, 8, lichen(15))
    m.box("head", -5, -6, -7, 10, 2, 2, boulder(10, moss_top=False))  # brow ridge
    m.box("jaw", -4, 0, -5, 8, 3, 7, {"front": stone(seed=12, brick_w=4, brick_h=3),
                                       "*": stone(seed=12, brick_w=4, brick_h=3)})
    m.box("jaw", -3, 3, -5, 6, 2, 1, mossy_drape(13, depth=2))      # moss beard

    # ------------------------------------------------------------------ arms
    for side, sx in (("r", -1), ("l", 1)):
        arm, fore = f"arm_{side}", f"forearm_{side}"

        def bx(part, x, y, z, w, h, d, paint, glow=None):
            m.box(part, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint, glow=glow)
        # shoulder boulder, mossy on top
        bx(arm, -5, -4, -5, 8, 7, 10, boulder(20 + sx))
        # upper arm column with a rune band
        arm_runes = {(x, 4) for x in range(6)}
        up = stone(seed=22 + sx, brick_w=4, brick_h=3)
        rp = {k: with_runes(up, k, arm_runes) for k in ("front", "back", "left", "right")}
        bx(arm, -3, 3, -3, 6, 8, 6, {**rp, "*": up},
           glow={k: (lambda pts: lambda f_, x, y, w, h: RUNE if (x, y) in pts else None)(arm_runes)
                 for k in ("front", "back", "left", "right")})
        # forearm and a huge boulder fist with knuckles
        fore_runes = {(3 + (y % 4 if y % 4 < 2 else 4 - y % 4) - 1, y) for y in range(0, 7)} | {(2, 3), (5, 3)}
        fp = stone(seed=24 + sx, brick_w=4, brick_h=3, moss=0.1)
        bx(fore, -4, 0, -4, 8, 7, 8, {"front": with_runes(fp, "front", fore_runes), "*": fp},
           glow=glow_at("front", fore_runes))
        bx(fore, -4.5, 7, -4.5, 9, 6, 9, boulder(26 + sx, moss_top=False))
        # knuckle ridge on the front of the fist
        bx(fore, -4.5, 8, -5.5, 9, 3, 1, lambda f_, x, y, w, h: STONE_L if y == 0 else STONE if x % 3 else STONE_D)

    # a fern grows out of the left shoulder boulder (asymmetry; crossed planes)
    m.box("arm_l", 1, -9, -1, 0, 6, 5, {"left": fern(1), "right": fern(1), "*": None})
    m.box("arm_l", -1.5, -9, 1.5, 5, 6, 0, {"front": fern(2), "back": fern(2), "*": None})

    # ------------------------------------------------------------------ legs
    for side, sx in (("r", -1), ("l", 1)):
        leg = f"leg_{side}"

        def bx(x, y, z, w, h, d, paint):
            m.box(leg, x if sx < 0 else mirror(x, w), y, z, w, h, d, paint)
        bx(-3.5, 0, -3.5, 7, 10, 7, stone(seed=40 + sx, brick_w=4, brick_h=3, moss=0.12))
        bx(-4.5, 9, -5.5, 9, 3, 10, boulder(42 + sx, moss_top=False))    # slab foot
        bx(-4.5, 2, -4.5, 9, 2, 9, mossy_drape(44 + sx, depth=2))        # moss garter

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.2)
    idle.rot("torso", (0, (0, 0, 0)), (1.6, (2.5, 0, 0)), (3.2, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (0.8, (0, 8, 0)), (1.6, (2, 0, 0)), (2.4, (0, -8, 0)), (3.2, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.6, (-3, 0, 2)), (3.2, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.6, (-3, 0, -2)), (3.2, (0, 0, 0)))
    idle.rot("chain", (0, (0, 0, 0)), (0.8, (0, 0, 8)), (2.4, (0, 0, -8)), (3.2, (0, 0, 0)))
    idle.rot("jaw", (0, (0, 0, 0)), (2.2, (0, 0, 0)), (2.6, (10, 0, 0)), (3.2, (0, 0, 0)))

    walk = m.anim("walk", 1.6)
    walk.rot("leg_r", (0, (22, 0, 0)), (0.8, (-22, 0, 0)), (1.6, (22, 0, 0)))
    walk.rot("leg_l", (0, (-22, 0, 0)), (0.8, (22, 0, 0)), (1.6, (-22, 0, 0)))
    walk.rot("hips", (0, (0, 0, 4)), (0.8, (0, 0, -4)), (1.6, (0, 0, 4)))
    walk.rot("torso", (0, (0, 6, -2)), (0.8, (0, -6, 2)), (1.6, (0, 6, -2)))
    walk.rot("arm_r", (0, (-14, 0, 0)), (0.8, (14, 0, 0)), (1.6, (-14, 0, 0)))
    walk.rot("arm_l", (0, (14, 0, 0)), (0.8, (-14, 0, 0)), (1.6, (14, 0, 0)))
    walk.rot("chain", (0, (-10, 0, 0)), (0.4, (10, 0, 0)), (0.8, (-10, 0, 0)), (1.2, (10, 0, 0)), (1.6, (-10, 0, 0)))
    walk.pos("bone", (0, (0, 0, 0)), (0.4, (0, 1.2, 0)), (0.8, (0, 0, 0)), (1.2, (0, 1.2, 0)), (1.6, (0, 0, 0)))

    # slam: both fists raised high over the head (telegraph), smashed down together at 0.7 s (14 ticks)
    a = m.anim("slam", 1.4)
    a.rot("arm_r", (0, (0, 0, 0)), (0.55, (-170, 0, 18)), (0.7, (-62, 0, -12), "linear"), (1.0, (-58, 0, -12)),
          (1.4, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.55, (-170, 0, -18)), (0.7, (-62, 0, 12), "linear"), (1.0, (-58, 0, 12)),
          (1.4, (0, 0, 0)))
    a.rot("forearm_r", (0, (0, 0, 0)), (0.55, (-30, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("forearm_l", (0, (0, 0, 0)), (0.55, (-30, 0, 0)), (0.7, (0, 0, 0), "linear"), (1.4, (0, 0, 0)))
    a.rot("torso", (0, (0, 0, 0)), (0.55, (-20, 0, 0)), (0.7, (32, 0, 0), "linear"), (1.0, (28, 0, 0)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.55, (-12, 0, 0)), (0.7, (-14, 0, 0)), (1.0, (-10, 0, 0)), (1.4, (0, 0, 0)))
    a.pos("bone", (0, (0, 0, 0)), (0.55, (0, 1.5, 1.5)), (0.7, (0, -2.5, -2), "linear"), (1.0, (0, -2.5, -2)),
          (1.4, (0, 0, 0)))
    a.rot("leg_r", (0, (0, 0, 0)), (0.55, (-6, 0, 0)), (0.7, (-18, 0, 4)), (1.0, (-18, 0, 4)), (1.4, (0, 0, 0)))
    a.rot("leg_l", (0, (0, 0, 0)), (0.55, (6, 0, 0)), (0.7, (12, 0, -4)), (1.0, (12, 0, -4)), (1.4, (0, 0, 0)))
    a.rot("chain", (0, (0, 0, 0)), (0.55, (30, 0, 0)), (0.75, (-40, 0, 0)), (1.0, (20, 0, 0)), (1.4, (0, 0, 0)))

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
    return m

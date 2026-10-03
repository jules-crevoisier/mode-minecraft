"""The Gryphon Knight (Le Chevalier-griffon): guardian of the sky temple.

A majestic gryphon about 4.5 blocks tall to the plume and 9 blocks of wingspan: eagle head with a
hooked golden beak and a stern brow, white and gold feathers, a tawny lion body and hindquarters, great
wings with slotted gold primaries. It wears a silver-and-azure barding: a plumed chanfron on the head,
lames down the neck, a peytral with a sapphire on the chest, a crupper on the rump and an azure caparison
with the sun-star of the temple.

Rest pose = standing, wings folded along the flanks (bone back, feathers down). Flight is a family of
actions that start and end in the *flight pose* (wings spread, legs tucked):
``takeoff`` (rest -> flight), ``fly`` (one wing beat, flight -> flight, replayed while airborne),
``dive``/``volley``/``hover_gust`` (flight -> flight) and ``land`` (flight -> rest, the gust shockwave).
"""
from ..models import Model
from ..texgen import mix, mul

# ---------------------------------------------------------------- palette
WHITE = (238, 236, 228)
WHITE_D = (200, 196, 188)
WHITE_S = (150, 146, 146)
CREAM = (246, 240, 222)
GOLD_F = (224, 170, 64)
GOLD_FD = (166, 112, 38)
GOLD_FL = (252, 218, 128)
FUR = (206, 150, 80)
FUR_D = (156, 104, 52)
FUR_L = (234, 196, 134)
BELLY = (238, 216, 172)
TUFT = (110, 66, 36)
BEAK = (240, 190, 62)
BEAK_D = (176, 120, 30)
BEAK_TIP = (58, 50, 46)
SILVER = (192, 200, 212)
SILVER_D = (118, 128, 144)
SILVER_L = (238, 242, 248)
AZURE = (44, 92, 182)
AZURE_D = (26, 56, 124)
AZURE_L = (90, 146, 222)
GOLD = (238, 198, 74)
GOLD_D = (164, 116, 34)
TALON = (38, 34, 40)
SCALE = (226, 178, 70)
EYE = (255, 214, 92)
GEM = (120, 210, 255)
WHITE_PX = (255, 255, 255)


# ---------------------------------------------------------------- deterministic noise
def hsh(*a):
    v = 2166136261
    for k in a:
        v = ((v ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    v ^= v >> 13
    v = (v * 0x5BD1E995) & 0xFFFFFFFF
    return v ^ (v >> 15)


def nz(x, y, seed=0):
    """0..1 value noise per texel."""
    return (hsh(x, y, seed) % 1000) / 1000.0


def jit(c, x, y, seed, amt=0.06):
    return mul(c, 1 + (nz(x, y, seed) - 0.5) * 2 * amt)


# ---------------------------------------------------------------- painters
def scales(base, dark, light, seed=0, fw=4, fh=3, tip=None, top=None):
    """Small overlapping feathers (head, neck, chest, trousers): staggered rows of rounded tips with a
    dark gap between tips and a pale highlight at the root of each feather."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            c = top or base
            if face == "bottom":
                c = mix(c, dark, 0.25)
            return jit(c, x, y, seed, 0.05)
        row = y // fh
        u = (x + (row % 2) * (fw // 2)) % fw
        v = y % fh
        c = base
        if v == fh - 1 and (u == 0 or u == fw - 1):
            c = dark
        elif u == 0:
            c = mix(base, dark, 0.45)
        elif v == 0 and u == fw // 2:
            c = light
        if tip is not None and v == fh - 1 and 0 < u < fw - 1:
            c = mix(c, tip, 0.65)
        return jit(c, x, y, seed, 0.04)
    return f


def grad(stops, t):
    """Colour along a gradient: stops = [(t, colour), ...] sorted by t in 0..1."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


def quills(stops, fw=3, seed=0, along="y", base_at_end=True, lengths=None, slot_from=None, rim=None):
    """Long flight feathers side by side on the broad faces of a wing plane.

    ``along`` is the texture axis the feathers run along; ``base_at_end`` puts the feather roots at the
    far end of that axis (wing planes: texture row 0 is the trailing edge). ``lengths(i, n)`` shortens
    feather i (fan shapes); ``slot_from`` (0..1) opens slots between the feathers beyond that fraction
    of their length (an eagle's fingered wingtip). Feather tips are cut to points."""
    def f(face, x, y, w, h):
        if face not in ("top", "bottom"):
            return grad(stops, 0.5) if rim is None else rim
        a_len = h if along == "y" else w
        pos = y if along == "y" else x
        acr = x if along == "y" else y
        a = (a_len - 1 - pos) if base_at_end else pos      # distance from the feather root
        i = acr // fw
        u = acr % fw
        n = ((w if along == "y" else h) + fw - 1) // fw
        L = a_len - (hsh(i, seed) % 3)
        if lengths:
            L = min(a_len, lengths(i, n, a_len))
        mid = (fw - 1) / 2
        point = int(round(abs(u - mid) * 1.6))
        if a > L - 1 - point:
            return None
        if slot_from is not None and u == 0 and a > slot_from * L:
            return None
        t = a / max(1, L - 1)
        c = grad(stops, t)
        if u == 0:
            c = mix(c, (60, 50, 50), 0.35)                 # shadow line between feathers
        elif abs(u - mid) < 0.6 and a < L - 2:
            c = mix(c, WHITE_PX, 0.28)                     # the shaft
        elif (a + u + i) % 4 == 0:
            c = mul(c, 0.93)                               # barbs
        if face == "bottom":
            c = mix(c, WHITE_D, 0.12)
        return jit(c, x, y, seed + i, 0.03)
    return f


def fur(base=FUR, dark=FUR_D, light=FUR_L, belly=BELLY, seed=0):
    """Lion pelt: short vertical brush strokes, lighter on the back, pale belly."""
    def f(face, x, y, w, h):
        if face == "bottom":
            return jit(belly, x, y, seed, 0.04)
        c = base
        s = hsh(x, y // 3, seed) % 9
        if s == 0:
            c = mix(c, dark, 0.5)
        elif s == 1:
            c = mix(c, light, 0.45)
        if face == "top":
            c = mix(c, light, 0.18)
        elif h > 5:
            t = y / (h - 1)
            c = mix(c, light, 0.22 * (1 - t)) if t < 0.5 else mix(c, belly, 0.5 * (t - 0.5))
        return jit(c, x, y, seed, 0.04)
    return f


def plate(base=SILVER, rim=GOLD, seed=0, rivets=True, inlay=None):
    """Polished barding plate: gold (or dark) rim, bevel highlight, vertical sheen, rivets, optional
    inlay function (face, x, y, w, h) -> colour | None painted over the field."""
    def f(face, x, y, w, h):
        edge = x == 0 or y == 0 or x == w - 1 or y == h - 1
        if edge and w > 2 and h > 2:
            c = rim if rim else mul(base, 0.62)
            if y == 0:
                c = mix(c, WHITE_PX, 0.2)
            return c
        if rivets and w > 5 and h > 4 and y in (1, h - 2) and x % 3 == 1:
            return SILVER_L if y == 1 else SILVER_D
        if inlay:
            r = inlay(face, x, y, w, h)
            if r is not None:
                return r
        t = y / max(1, h - 1)
        c = mix(SILVER_L, base, min(1.0, 0.35 + t * 1.2)) if face != "bottom" else mul(base, 0.8)
        if (x + y * 2) % 11 == 0:
            c = mix(c, WHITE_PX, 0.25)                     # sheen streaks
        if x == 1 or y == 1:
            c = mix(c, WHITE_PX, 0.15)
        elif x == w - 2 or y == h - 2:
            c = mul(c, 0.85)
        return jit(c, x, y, seed, 0.025)
    return f


STAR = ["....#....",
        ".#..#..#.",
        "..#.#.#..",
        "...###...",
        "#########",
        "...###...",
        "..#.#.#..",
        ".#..#..#.",
        "....#...."]


def stamp(sprite, cx, cy, colour, edge=None):
    """Pixel-art emblem centred at (cx, cy) on a face; returns a painter overlay."""
    hh, ww = len(sprite), len(sprite[0])

    def f(face, x, y, w, h):
        sx, sy = x - (cx(w) - ww // 2), y - (cy(h) - hh // 2)
        if 0 <= sx < ww and 0 <= sy < hh:
            if sprite[sy][sx] == "#":
                return colour
            if edge is not None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    tx, ty = sx + dx, sy + dy
                    if 0 <= tx < ww and 0 <= ty < hh and sprite[ty][tx] == "#":
                        return edge
        return None
    return f


def caparison(seed=0):
    """Azure cloth: vertical folds, gold trim along the top, a dagged hem with a gold border and the
    silver sun-star of the temple on the flanks."""
    star = stamp(STAR, lambda w: w // 2, lambda h: h // 2 - 1, SILVER_L, edge=GOLD_D)

    def f(face, x, y, w, h):
        if face in ("top", "bottom", "front"):
            return None
        dag = x % 4
        depth = (2, 1, 1, 2)[dag]
        if y >= h - depth:
            return None
        if y == h - depth - 1:
            return GOLD
        if y < 2:
            return GOLD if y == 0 else GOLD_D
        if face in ("left", "right"):
            s = star(face, x, y, w, h)
            if s is not None:
                return s
        fold = (1.0, 1.08, 1.02, 0.92, 0.84, 0.9)[x % 6]
        c = mul(AZURE, fold)
        if y == 2:
            c = AZURE_D
        if (x * 7 + y * 3 + seed) % 23 == 0:
            c = mix(c, AZURE_L, 0.4)
        return jit(c, x, y, seed, 0.03)
    return f


def beak(seed=0, tip_rows=0):
    def f(face, x, y, w, h):
        c = BEAK
        if face == "top":
            c = mix(BEAK, (255, 236, 160), 0.35)
        elif face == "bottom":
            c = BEAK_D
        elif h > 2:
            t = y / (h - 1)
            c = mix(mix(BEAK, (255, 230, 150), 0.3), BEAK_D, t)
        if tip_rows and face != "top" and y >= h - tip_rows:
            c = BEAK_TIP
        if (x + y) % 5 == 0:
            c = mul(c, 0.94)
        return jit(c, x, y, seed, 0.03)
    return f


def talon(face, x, y, w, h):
    return (24, 22, 26) if face in ("front", "bottom") or y >= h - 1 else TALON


def scaled_leg(seed=0):
    """Yellow scaled eagle shank: horizontal scutes."""
    def f(face, x, y, w, h):
        c = SCALE
        if y % 2 == 1:
            c = mul(SCALE, 0.82)
        if (x + (y // 2)) % 3 == 0 and y % 2 == 0:
            c = mix(SCALE, (255, 230, 150), 0.4)
        return jit(c, x, y, seed, 0.04)
    return f


def ruff(seed=0):
    """Feather ruff around the neck base: white scalloped feathers with gold tips and a ragged hem."""
    sc = scales(WHITE, WHITE_S, CREAM, seed, fw=4, fh=3, tip=GOLD_FL)

    def f(face, x, y, w, h):
        if face == "bottom":
            return None
        if face != "top" and y >= h - 1 - (hsh(x, seed) % 3):
            return None
        return sc(face, x, y, w, h)
    return f


# ---------------------------------------------------------------- the model
# rest rotations of the wing segments (folded) and their spread flight pose (all zero)
WING_REST = {"wing_l": (-90, -90, -12), "wing_r": (-90, 90, 12),
             "wingtip_l": (0, -14, -12), "wingtip_r": (0, 14, 12)}
WING_SPREAD = {"wing_l": (0, 0, 0), "wing_r": (0, 0, 0), "wingtip_l": (0, -12, 0), "wingtip_r": (0, 12, 0)}


def build():
    m = Model("gryphon_knight", seed=77, shadow=2.0, walk_speed=1.1, walk_scale=1.0, head="head")
    piv = {}

    def part(name, parent, abs_pivot, rot=(0, 0, 0)):
        pp = piv[parent] if parent else (0, 0, 0)
        m.part(name, parent, pivot=tuple(abs_pivot[i] - pp[i] for i in range(3)), rot=rot)
        piv[name] = abs_pivot

    def ab(p, x0, htop, z0, w, h, d, paint, glow=None, grow=0.0):
        """Box in absolute model space: x0/z0 min corner, htop = top height above the ground (px)."""
        P = piv[p]
        m.box(p, x0 - P[0], (24 - htop) - P[1], z0 - P[2], w, h, d, paint, glow=glow, grow=grow)

    def g(h):
        return 24 - h

    # ------------------------------------------------------------------ skeleton
    part("bone", None, (0, 24, 0))
    part("body", "bone", (0, g(31), 14))                    # hips: rears and pitches around them
    # the neck leans forward; the head undoes it so its own frame is level
    m.part("neck", "body", pivot=(0, g(44) - g(31), -22 - 14), rot=(34, 0, 0))
    m.part("head", "neck", pivot=(0, -15, -1), rot=(-34, 0, 0))
    m.part("jaw", "head", pivot=(0, -3, -11))
    m.part("plume", "head", pivot=(0, -14, 3), rot=(-40, 0, 0))
    for side, sx in (("l", 1), ("r", -1)):
        m.part(f"wing_{side}", "body", pivot=(sx * 12, g(46) - g(31), -20 - 14), rot=WING_REST[f"wing_{side}"])
        m.part(f"wingtip_{side}", f"wing_{side}", pivot=(sx * 24, 0, 0), rot=WING_REST[f"wingtip_{side}"])
    for side, sx in (("l", 1), ("r", -1)):
        part(f"leg_f{side}", "body", (sx * 7.5, g(29), -17))
        part(f"shin_f{side}", f"leg_f{side}", (sx * 7.5, g(15), -17))
        part(f"leg_h{side}", "body", (sx * 6.5, g(33), 19))
        part(f"shin_h{side}", f"leg_h{side}", (sx * 6.5, g(18), 22))
    m.part("tail", "body", pivot=(0, g(38) - g(31), 27 - 14), rot=(-40, 0, 0))
    m.part("tail2", "tail", pivot=(0, 0, 15), rot=(55, 0, 0))

    # ------------------------------------------------------------------ body
    breast = scales(WHITE, WHITE_S, CREAM, 1, tip=GOLD_FL)
    ab("body", -12, 47, -28, 24, 26, 22, {"front": scales(WHITE, WHITE_S, CREAM, 1, tip=WHITE_D), "*": breast})
    ab("body", -9, 31, -31, 18, 11, 6, scales(WHITE, WHITE_S, CREAM, 2, tip=WHITE_D))   # rounded keel
    ab("body", -10.5, 44, -8, 21, 21, 18, fur(seed=2))                                # waist
    ab("body", -9.5, 42, 8, 19, 20, 19, fur(seed=3))                                  # lion hindquarters
    # barding: peytral (chest plate) with the sapphire, wrapping the sides of the breast
    gem = lambda f_, x, y, w, h: GEM if f_ == "front" and abs(x - w // 2) <= 1 and abs(y - h // 2) <= 1 else None

    def peytral_inlay(f_, x, y, w, h):
        if f_ != "front":
            return None
        dx, dy = abs(x - w // 2), abs(y - h // 2)
        if dx <= 1 and dy <= 1:
            return GEM
        if dx + dy <= 4:
            return AZURE if dx + dy <= 3 else GOLD
        if dy == 0 and 4 < dx < w // 2 - 1:
            return GOLD_D                                                             # engraved line
        return None
    ab("body", -13, 42, -31, 26, 14, 3, {"front": plate(inlay=peytral_inlay), "*": plate()}, glow={"front": gem})
    for sx in (-1, 1):
        ab("body", -14 if sx < 0 else 13, 41, -29, 1, 12, 16, plate(rivets=True))
    # caparison skirt hanging under the wings, legs pass through it
    ab("body", -12, 30, -9, 24, 13, 37, caparison(4))
    # crupper on the rump with a gold spine
    ab("body", -10.5, 44, 9, 21, 3, 17, plate(inlay=lambda f_, x, y, w, h: GOLD if f_ == "top" and abs(x - w // 2) < 1 else None))
    ab("body", -1, 46, 11, 2, 2, 13, plate(GOLD, GOLD_D, rivets=False))

    # ------------------------------------------------------------------ neck and head
    m.box("neck", -7, -18, -7, 14, 20, 14, scales(WHITE, WHITE_S, CREAM, 5, fw=4, fh=3))
    m.box("neck", -9, -3, -9, 18, 8, 18, ruff(6))                                     # feather ruff
    for i, y in enumerate((-18, -12, -6)):                                            # lames down the nape
        m.box("neck", -4.5, y, 6, 9, 6, 3, plate(seed=7 + i))
    eye = lambda f_, x, y, w, h: (EYE if f_ in ("left", "right") and y == 7 and
                                   (x in (3, 4) if f_ == "left" else x in (w - 4, w - 5)) else None)
    pupil = lambda f_, x, y, w, h: ((30, 20, 16) if f_ in ("left", "right") and y == 7 and
                                     (x == 3 if f_ == "left" else x == w - 4) else None)
    stripe = lambda f_, x, y, w, h: ((96, 84, 76) if f_ in ("left", "right") and y in (6, 8) and
                                      (x <= 7 if f_ == "left" else x >= w - 8) else None)
    sk = scales(WHITE, WHITE_S, CREAM, 8, fw=3, fh=2)

    def skull(f_, x, y, w, h):
        return pupil(f_, x, y, w, h) or eye(f_, x, y, w, h) or stripe(f_, x, y, w, h) or sk(f_, x, y, w, h)
    m.box("head", -7, -13, -11, 14, 13, 16, skull, glow=eye)
    m.box("head", -8, -12, -12, 16, 3, 8, scales(WHITE_D, WHITE_S, WHITE, 9, fw=3, fh=2))   # stern brow
    m.box("head", -5, -11, -18, 10, 7, 7, beak(10))                                   # cere
    m.box("head", -4, -10, -24, 8, 6, 6, beak(11))                                    # upper beak
    m.box("head", -3, -7, -27, 6, 8, 4, beak(12, tip_rows=3))                         # the hook
    m.box("head", -2, 1, -26, 4, 2, 3, beak(12, tip_rows=2))
    m.box("jaw", -4, 0, -11, 8, 3, 11, beak(13))
    m.box("jaw", -3, -1, -11, 6, 1, 1, (250, 236, 200))
    for sx in (-1, 1):                                                                # ear tufts
        m.box("head", 4 if sx > 0 else -7, -15, 1, 3, 5, 10, scales(WHITE, WHITE_S, GOLD_FL, 14, fw=3, fh=2, tip=GOLD_F))
    # chanfron: silver plate over the crown and the cere, cheek guards behind the eyes
    m.box("head", -6, -14.5, -13, 12, 2, 16, plate(seed=15, inlay=lambda f_, x, y, w, h: GOLD if f_ == "top" and x == w // 2 else None))
    m.box("head", -3.5, -12, -19, 7, 2, 7, plate(seed=16, rivets=False))
    for sx in (-1, 1):
        m.box("head", -8 if sx < 0 else 7, -10, -3, 1, 8, 8, plate(seed=17))
    # plume: gold holder and a tall azure-and-white plume sweeping back
    m.box("plume", -2, -3, -2, 4, 3, 4, plate(GOLD, GOLD_D, rivets=False))
    m.box("plume", -2, -19, -2, 4, 16, 5, quills([(0, AZURE_D), (0.5, AZURE), (0.85, AZURE_L), (1, WHITE)],
                                                   fw=2, seed=18, along="y", base_at_end=True, rim=AZURE))
    m.box("plume", -1, -25, 0, 2, 7, 4, quills([(0, AZURE), (0.6, AZURE_L), (1, WHITE)], fw=2, seed=19,
                                                 along="y", base_at_end=True, rim=AZURE_L))
    m.box("plume", -0.5, -2, -2.5, 1, 1, 1, GEM, glow=GEM)

    # ------------------------------------------------------------------ wings (local frame = spread wing:
    # +x outward along the bone, +z the trailing feathers, the plane is 1 px thick)
    sec = [(0, WHITE), (0.35, CREAM), (0.55, GOLD_FL), (0.62, GOLD_F), (0.72, WHITE), (1, WHITE)]
    prim = [(0, WHITE), (0.3, GOLD_FL), (0.6, GOLD_F), (0.85, GOLD_FD), (1, (110, 76, 36))]

    def prim_len(i, n, a_len):
        k = n - 1 - i                                     # rows counted from the leading edge
        return a_len - (5, 0, 1, 3, 6)[min(k, 4)]
    for side, sx in (("l", 1), ("r", -1)):
        w, t = f"wing_{side}", f"wingtip_{side}"
        x0 = 0 if sx > 0 else -24
        m.box(w, x0, -2.5, -2.5, 24, 5, 5, scales(WHITE, WHITE_S, CREAM, 20, fw=3, fh=2))          # arm
        m.box(w, x0, -1, 1, 24, 2, 7, scales(GOLD_FL, GOLD_FD, WHITE, 21, fw=3, fh=2, tip=GOLD_F))  # coverts
        m.box(w, x0, 0, 2, 24, 1, 17, quills(sec, fw=3, seed=22, along="y", base_at_end=True))     # secondaries
        x1 = 0 if sx > 0 else -14
        m.box(t, x1, -2, -2, 14, 4, 4, scales(WHITE, WHITE_S, CREAM, 23, fw=3, fh=2))              # hand
        m.box(t, x1, -1, 1, 14, 2, 5, scales(GOLD_FL, GOLD_FD, WHITE, 24, fw=3, fh=2, tip=GOLD_F))
        x2 = 0 if sx > 0 else -34
        m.box(t, x2, 0, -1, 34, 1, 15, quills(prim, fw=3, seed=25 + sx, along="x", base_at_end=sx < 0,
                                               lengths=prim_len, slot_from=0.6))                   # primaries

    # ------------------------------------------------------------------ legs
    for side, sx in (("l", 1), ("r", -1)):
        lf, sf, lh, sh = f"leg_f{side}", f"shin_f{side}", f"leg_h{side}", f"shin_h{side}"
        # eagle forelegs: feathered trousers, yellow scaled shank, black talons
        ab(lf, sx * 7.5 - 4.5, 30, -22, 9, 16, 10, scales(WHITE, WHITE_S, CREAM, 30 + sx, fw=3, fh=2, tip=WHITE_D))
        ab(sf, sx * 7.5 - 3, 15, -20, 6, 12, 6, scaled_leg(31 + sx))
        ab(sf, sx * 7.5 - 4, 3, -24, 8, 3, 10, scaled_leg(32 + sx))
        for i, dx in enumerate((-4, -1, 2)):
            ab(sf, sx * 7.5 + dx, 3, -28 + (1 if i != 1 else 0), 2, 3, 5, talon)
        ab(sf, sx * 7.5 - 1, 3, -15, 2, 3, 3, talon)
        # lion hind legs: haunch, shank, paw with pale claws
        ab(lh, sx * 6.5 - 4, 35, 11, 8, 18, 15, fur(seed=33 + sx))
        ab(sh, sx * 6.5 - 3, 18, 19, 6, 13, 6, fur(seed=34 + sx))
        claws = lambda f_, x, y, w, h: (236, 226, 200) if y == h - 1 and x % 2 == 1 else fur(seed=35)(f_, x, y, w, h)
        ab(sh, sx * 6.5 - 4, 5, 16, 8, 5, 10, {"front": claws, "*": fur(seed=35)})
    # tail: drooping then curling up, with a dark tuft
    m.box("tail", -1.5, -1.5, 0, 3, 3, 16, fur(seed=40))
    m.box("tail2", -1, -1, 0, 2, 2, 11, fur(seed=41))
    m.box("tail2", -2.5, -2.5, 9, 5, 5, 7, lambda f_, x, y, w, h: jit(TUFT if (x + y) % 3 else mul(TUFT, 0.75), x, y, 42))

    anims(m)
    return m


# ---------------------------------------------------------------- animations
Z3 = (0, 0, 0)
# flight pose offsets (added to the rest pose): wings spread, legs tucked, tail streaming, neck forward
FLIGHT = {
    **{k: tuple(WING_SPREAD[k][i] - WING_REST[k][i] for i in range(3)) for k in WING_REST},
    "leg_fl": (55, 0, 0), "leg_fr": (55, 0, 0), "shin_fl": (-70, 0, 0), "shin_fr": (-70, 0, 0),
    "leg_hl": (-50, 0, 0), "leg_hr": (-50, 0, 0), "shin_hl": (40, 0, 0), "shin_hr": (40, 0, 0),
    "tail": (30, 0, 0), "tail2": (-40, 0, 0),
    "neck": (-14, 0, 0), "head": (14, 0, 0),
}


def fp(name, extra=Z3):
    base = FLIGHT.get(name, Z3)
    return tuple(base[i] + extra[i] for i in range(3))


def flap(a, t0, t1, up=-38, down=26, tip_up=-18, tip_down=14, n=1):
    """Wing beats between t0 and t1 on top of the flight pose (z roll at the shoulder, tip lags)."""
    step = (t1 - t0) / n
    kl, kr, tl, tr = [], [], [], []
    for k in range(n):
        s = t0 + k * step
        for tt, zz, tz in ((s, 0, 0), (s + step * 0.3, up, tip_up), (s + step * 0.7, down, tip_down)):
            kl.append((tt, fp("wing_l", (0, 0, zz))))
            kr.append((tt, fp("wing_r", (0, 0, -zz))))
            tl.append((tt, fp("wingtip_l", (0, 0, tz))))
            tr.append((tt, fp("wingtip_r", (0, 0, -tz))))
    return kl, kr, tl, tr


def anims(m):
    # ---------------------------------------------------------------- idle: breathing, preening head, tail
    a = m.anim("idle", 4.0)
    a.rot("body", (0, Z3), (2.0, (-1.5, 0, 0)), (4.0, Z3))
    a.rot("neck", (0, Z3), (1.2, (-4, 4, 0)), (2.6, (2, -5, 0)), (4.0, Z3))
    a.rot("head", (0, Z3), (1.2, (3, 8, -4)), (2.0, (0, 10, -6)), (2.6, (-3, -8, 4)), (4.0, Z3))
    a.rot("jaw", (0, Z3), (3.0, Z3), (3.2, (10, 0, 0)), (3.5, Z3), (4.0, Z3))
    a.rot("tail", (0, Z3), (1.0, (0, 14, 0)), (2.0, (5, 0, 0)), (3.0, (0, -14, 0)), (4.0, Z3))
    a.rot("tail2", (0, Z3), (1.0, (0, 20, 0)), (2.0, (-8, 0, 0)), (3.0, (0, -20, 0)), (4.0, Z3))
    a.rot("wing_l", (0, Z3), (2.0, (0, 0, -4)), (4.0, Z3))
    a.rot("wing_r", (0, Z3), (2.0, (0, 0, 4)), (4.0, Z3))
    a.rot("plume", (0, Z3), (2.0, (-5, 0, 3)), (4.0, Z3))

    # ---------------------------------------------------------------- walk: diagonal pairs, head bob
    a = m.anim("walk", 1.2)
    for leg, ph in (("leg_fl", 0), ("leg_hr", 0), ("leg_fr", 1), ("leg_hl", 1)):
        s = 1 if ph == 0 else -1
        a.rot(leg, (0, (28 * s, 0, 0)), (0.6, (-28 * s, 0, 0)), (1.2, (28 * s, 0, 0)))
    for shin, ph in (("shin_fl", 0), ("shin_hr", 0), ("shin_fr", 1), ("shin_hl", 1)):
        a.rot(shin, (0, Z3), (0.3, (-30 if ph == 0 else 0, 0, 0)), (0.6, Z3), (0.9, (-30 if ph else 0, 0, 0)), (1.2, Z3))
    a.rot("neck", (0, Z3), (0.3, (6, 0, 0)), (0.6, Z3), (0.9, (6, 0, 0)), (1.2, Z3))
    a.rot("head", (0, Z3), (0.3, (-6, 0, 0)), (0.6, Z3), (0.9, (-6, 0, 0)), (1.2, Z3))
    a.pos("bone", (0, Z3), (0.3, (0, 1.2, 0)), (0.6, Z3), (0.9, (0, 1.2, 0)), (1.2, Z3))
    a.rot("tail", (0, (0, -10, 0)), (0.6, (0, 10, 0)), (1.2, (0, -10, 0)))

    # ---------------------------------------------------------------- peck: two quick pecks, a heavy third
    # impacts at 0.55 s (11 t), 0.95 s, 1.5 s (heavy)
    a = m.anim("peck", 2.2)
    a.rot("neck", (0, Z3), (0.4, (-30, 0, 0)), (0.55, (40, 0, 0), "linear"), (0.75, (-25, 10, 0)),
          (0.95, (42, 10, 0), "linear"), (1.25, (-45, -8, 0)), (1.5, (55, 0, 0), "linear"), (1.85, (40, 0, 0)), (2.2, Z3))
    a.rot("head", (0, Z3), (0.4, (12, 0, 0)), (0.55, (8, 0, 0)), (0.75, (10, 0, 0)), (0.95, (6, 0, 0)),
          (1.25, (18, 0, 0)), (1.5, (10, 0, 0)), (2.2, Z3))
    a.rot("jaw", (0, Z3), (0.4, (30, 0, 0)), (0.55, Z3, "linear"), (0.75, (30, 0, 0)), (0.95, Z3, "linear"),
          (1.25, (40, 0, 0)), (1.5, Z3, "linear"), (2.2, Z3))
    a.rot("body", (0, Z3), (0.4, (-6, 0, 0)), (0.55, (6, 0, 0)), (1.25, (-10, 0, 0)), (1.5, (10, 0, 0), "linear"),
          (1.85, (8, 0, 0)), (2.2, Z3))
    a.rot("wing_l", (0, Z3), (1.25, (20, 30, -10)), (1.5, (10, 10, 0)), (2.2, Z3))
    a.rot("wing_r", (0, Z3), (1.25, (20, -30, 10)), (1.5, (10, -10, 0)), (2.2, Z3))
    a.pos("bone", (0, Z3), (0.55, (0, 0, -3)), (0.95, (0, 0, -6)), (1.25, (0, 0, -4)), (1.5, (0, 0, -10), "linear"),
          (1.85, (0, 0, -10)), (2.2, Z3))

    # ---------------------------------------------------------------- rake: rears on the hind legs,
    # both talons rake down (impact 0.85 s = 17 t)
    a = m.anim("rake", 1.9)
    a.rot("body", (0, Z3), (0.7, (-38, 0, 0)), (0.85, (8, 0, 0), "linear"), (1.3, (6, 0, 0)), (1.9, Z3))
    a.pos("bone", (0, Z3), (0.7, (0, 0, 4)), (0.85, (0, 0, -8), "linear"), (1.3, (0, 0, -8)), (1.9, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"leg_f{side}", (0, Z3), (0.7, (-95, 0, -10 * sx)), (0.85, (30, 0, 0), "linear"), (1.3, (20, 0, 0)), (1.9, Z3))
        a.rot(f"shin_f{side}", (0, Z3), (0.7, (40, 0, 0)), (0.85, (-20, 0, 0), "linear"), (1.9, Z3))
        a.rot(f"leg_h{side}", (0, Z3), (0.7, (30, 0, 0)), (0.85, (-8, 0, 0)), (1.9, Z3))
        a.rot(f"wing_{side}", (0, Z3), (0.7, (70, 60 * sx, -20 * sx)), (0.85, (60, 70 * sx, 10 * sx), "linear"),
              (1.3, (40, 40 * sx, 0)), (1.9, Z3))
    a.rot("neck", (0, Z3), (0.7, (-10, 0, 0)), (0.85, (20, 0, 0)), (1.9, Z3))
    a.rot("head", (0, Z3), (0.7, (-15, 0, 0)), (0.85, (10, 0, 0)), (1.9, Z3))
    a.rot("jaw", (0, Z3), (0.6, (35, 0, 0)), (0.85, (10, 0, 0)), (1.9, Z3))

    # ---------------------------------------------------------------- pounce: crouch, leap forward with
    # the wings half open, land on the talons (leap at 0.6 s = 12 t)
    a = m.anim("pounce", 1.8)
    a.pos("bone", (0, Z3), (0.6, (0, -4, 4)), (0.9, (0, 14, -10)), (1.15, (0, 0, -16), "linear"), (1.45, (0, 0, -16)), (1.8, Z3))
    a.rot("body", (0, Z3), (0.6, (8, 0, 0)), (0.9, (-14, 0, 0)), (1.15, (10, 0, 0), "linear"), (1.8, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.6, (20, 20 * sx, 0)), (0.9, (80, 80 * sx, -30 * sx)), (1.15, (85, 85 * sx, 20 * sx)),
              (1.45, (40, 40 * sx, 0)), (1.8, Z3))
        a.rot(f"leg_f{side}", (0, Z3), (0.6, (20, 0, 0)), (0.9, (-60, 0, 0)), (1.15, (-10, 0, 0), "linear"), (1.8, Z3))
        a.rot(f"leg_h{side}", (0, Z3), (0.6, (-20, 0, 0)), (0.9, (50, 0, 0)), (1.15, Z3), (1.8, Z3))
    a.rot("neck", (0, Z3), (0.6, (20, 0, 0)), (0.9, (-10, 0, 0)), (1.15, (25, 0, 0)), (1.8, Z3))
    a.rot("jaw", (0, Z3), (0.85, (35, 0, 0)), (1.15, Z3), (1.8, Z3))

    # ---------------------------------------------------------------- gust (ground): rears and beats the
    # wings forward, a cone of wind (impact 0.9 s = 18 t)
    a = m.anim("gust", 1.8)
    a.rot("body", (0, Z3), (0.7, (-28, 0, 0)), (0.9, (-12, 0, 0), "linear"), (1.3, (-10, 0, 0)), (1.8, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.7, fp(f"wing_{side}", (-30, 30 * sx, -50 * sx))),
              (0.9, fp(f"wing_{side}", (0, -40 * sx, 40 * sx)), "linear"), (1.3, fp(f"wing_{side}", (0, -30 * sx, 25 * sx))),
              (1.8, Z3))
        a.rot(f"wingtip_{side}", (0, Z3), (0.7, (0, 0, -20 * sx)), (0.9, (0, -20 * sx, 25 * sx), "linear"), (1.8, Z3))
        a.rot(f"leg_f{side}", (0, Z3), (0.7, (-60, 0, 0)), (0.9, (-40, 0, 0)), (1.8, Z3))
    a.rot("neck", (0, Z3), (0.7, (-20, 0, 0)), (0.9, (15, 0, 0)), (1.8, Z3))
    a.rot("jaw", (0, Z3), (0.7, (40, 0, 0)), (1.3, (30, 0, 0)), (1.8, Z3))

    # ---------------------------------------------------------------- tail sweep: pivots on the forelegs and
    # whips the hindquarters round (impact 0.65 s = 13 t)
    a = m.anim("sweep", 1.5)
    a.rot("bone", (0, Z3), (0.5, (0, -25, 0)), (0.65, (0, 60, 0), "linear"), (0.9, (0, 70, 0)), (1.5, Z3))
    a.rot("tail", (0, Z3), (0.5, (10, -40, 0)), (0.65, (-10, 50, 0), "linear"), (1.5, Z3))
    a.rot("tail2", (0, Z3), (0.5, (0, -30, 0)), (0.65, (0, 40, 0), "linear"), (1.5, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.5, (40, 40 * sx, 0)), (0.65, (50, 50 * sx, -20 * sx)), (1.5, Z3))
    a.rot("leg_hl", (0, Z3), (0.5, (20, 0, 0)), (0.65, (-30, 0, 20)), (1.5, Z3))
    a.rot("leg_hr", (0, Z3), (0.5, (20, 0, 0)), (0.65, (-30, 0, -20)), (1.5, Z3))

    # ---------------------------------------------------------------- takeoff: crouch, spring, wings unfold
    # (leaves the ground at 0.7 s = 14 t, ends in the flight pose)
    a = m.anim("takeoff", 1.4)
    for name in FLIGHT:
        if name.startswith("wing"):
            continue
        a.rot(name, (0, Z3), (0.55, Z3), (1.0, fp(name)), (1.4, fp(name)))
    a.rot("body", (0, Z3), (0.55, (12, 0, 0)), (0.8, (-25, 0, 0)), (1.4, Z3))
    a.pos("bone", (0, Z3), (0.55, (0, -5, 0)), (0.75, (0, 6, 0)), (1.4, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.45, (30, 40 * sx, -10 * sx)), (0.7, fp(f"wing_{side}", (0, 0, -55 * sx))),
              (1.0, fp(f"wing_{side}", (0, 0, 30 * sx))), (1.4, fp(f"wing_{side}")))
        a.rot(f"wingtip_{side}", (0, Z3), (0.7, fp(f"wingtip_{side}", (0, 0, -25 * sx))), (1.0, fp(f"wingtip_{side}", (0, 0, 15 * sx))),
              (1.4, fp(f"wingtip_{side}")))

    # ---------------------------------------------------------------- fly: one wing beat in the flight pose
    a = m.anim("fly", 0.8)
    kl, kr, tl, tr = flap(a, 0.0, 0.8)
    a.rot("wing_l", *kl, (0.8, fp("wing_l")))
    a.rot("wing_r", *kr, (0.8, fp("wing_r")))
    a.rot("wingtip_l", *tl, (0.8, fp("wingtip_l")))
    a.rot("wingtip_r", *tr, (0.8, fp("wingtip_r")))
    for name in FLIGHT:
        if not name.startswith("wing"):
            a.rot(name, (0, fp(name)), (0.4, fp(name, (3 if name.startswith("leg") else 0, 0, 0))), (0.8, fp(name)))
    a.pos("bone", (0, Z3), (0.3, (0, 2, 0)), (0.7, (0, -1.5, 0)), (0.8, Z3))

    # ---------------------------------------------------------------- dive: in the air, rears back and
    # screams (telegraph), folds the wings and stoops talons first (strike 0.9 s = 18 t), pulls up
    a = m.anim("dive", 2.0)
    for name in FLIGHT:
        if name.startswith("wing") or name.startswith("leg") or name.startswith("shin"):
            continue
        a.rot(name, (0, fp(name)), (2.0, fp(name)))
    a.rot("body", (0, Z3), (0.7, (-30, 0, 0)), (0.9, (35, 0, 0), "linear"), (1.3, (20, 0, 0)), (1.6, (-20, 0, 0)), (2.0, Z3))
    a.rot("neck", (0, fp("neck")), (0.7, fp("neck", (-25, 0, 0))), (0.9, fp("neck", (10, 0, 0))), (2.0, fp("neck")))
    a.rot("jaw", (0, Z3), (0.5, (40, 0, 0)), (0.75, (40, 0, 0)), (0.9, Z3), (2.0, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.7, fp(f"wing_{side}", (-20, 0, -60 * sx))),
              (0.9, fp(f"wing_{side}", (-10, -50 * sx, -40 * sx)), "linear"), (1.3, fp(f"wing_{side}", (0, -40 * sx, -30 * sx))),
              (1.6, fp(f"wing_{side}", (0, 0, 30 * sx))), (2.0, fp(f"wing_{side}")))
        a.rot(f"wingtip_{side}", (0, fp(f"wingtip_{side}")), (0.9, fp(f"wingtip_{side}", (0, 30 * sx, 0))), (2.0, fp(f"wingtip_{side}")))
        a.rot(f"leg_f{side}", (0, fp(f"leg_f{side}")), (0.7, fp(f"leg_f{side}")), (0.9, (-70, 0, 0), "linear"),
              (1.3, (-60, 0, 0)), (2.0, fp(f"leg_f{side}")))
        a.rot(f"shin_f{side}", (0, fp(f"shin_f{side}")), (0.7, fp(f"shin_f{side}")), (0.9, (10, 0, 0), "linear"),
              (2.0, fp(f"shin_f{side}")))
        a.rot(f"leg_h{side}", (0, fp(f"leg_h{side}")), (2.0, fp(f"leg_h{side}")))
        a.rot(f"shin_h{side}", (0, fp(f"shin_h{side}")), (2.0, fp(f"shin_h{side}")))

    # ---------------------------------------------------------------- volley: hovering, flares the wings
    # back and flings a fan of quills (release 0.85 s = 17 t)
    a = m.anim("volley", 1.8)
    for name in FLIGHT:
        if not name.startswith("wing"):
            a.rot(name, (0, fp(name)), (1.8, fp(name)))
    a.rot("body", (0, Z3), (0.7, (-25, 0, 0)), (0.85, (10, 0, 0), "linear"), (1.3, (5, 0, 0)), (1.8, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.7, fp(f"wing_{side}", (-10, 45 * sx, -45 * sx))),
              (0.85, fp(f"wing_{side}", (0, -35 * sx, 30 * sx)), "linear"), (1.3, fp(f"wing_{side}", (0, -20 * sx, 15 * sx))),
              (1.8, fp(f"wing_{side}")))
        a.rot(f"wingtip_{side}", (0, fp(f"wingtip_{side}")), (0.7, fp(f"wingtip_{side}", (0, 25 * sx, -20 * sx))),
              (0.85, fp(f"wingtip_{side}", (0, -25 * sx, 20 * sx)), "linear"), (1.8, fp(f"wingtip_{side}")))

    # ---------------------------------------------------------------- land: flare, drop, beat the wings
    # down on touch-down (gust shockwave 0.75 s = 15 t), fold
    a = m.anim("land", 1.8)
    for name in FLIGHT:
        if name.startswith("wing"):
            continue
        a.rot(name, (0, fp(name)), (0.55, fp(name)), (0.75, Z3, "linear"), (1.8, Z3))
    a.rot("body", (0, Z3), (0.55, (-25, 0, 0)), (0.75, (6, 0, 0), "linear"), (1.1, (4, 0, 0)), (1.8, Z3))
    a.pos("bone", (0, Z3), (0.75, (0, -3, 0), "linear"), (1.1, (0, -2, 0)), (1.8, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.55, fp(f"wing_{side}", (0, 0, -60 * sx))),
              (0.75, fp(f"wing_{side}", (0, 0, 40 * sx)), "linear"), (1.1, fp(f"wing_{side}", (0, 0, 30 * sx))),
              (1.8, Z3))
        a.rot(f"wingtip_{side}", (0, fp(f"wingtip_{side}")), (0.55, fp(f"wingtip_{side}", (0, 0, -30 * sx))),
              (0.75, fp(f"wingtip_{side}", (0, 0, 25 * sx)), "linear"), (1.8, Z3))

    # ---------------------------------------------------------------- storm (phase 2 spectacle): rears up,
    # wings raised to the sky, a long scream while the bolts fall (call at 1.0 s = 20 t)
    a = m.anim("storm", 2.6)
    a.rot("body", (0, Z3), (0.6, (-40, 0, 0)), (2.0, (-40, 0, 0)), (2.6, Z3))
    a.pos("bone", (0, Z3), (0.6, (0, 0, 6)), (2.0, (0, 0, 6)), (2.6, Z3))
    a.rot("neck", (0, Z3), (0.6, (-20, 0, 0)), (2.0, (-24, 0, 0)), (2.6, Z3))
    a.rot("head", (0, Z3), (0.6, (-25, 0, 0)), (2.0, (-25, 0, 0)), (2.6, Z3))
    a.rot("jaw", (0, Z3), (0.6, (45, 0, 0)), (2.0, (45, 0, 0)), (2.6, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.6, fp(f"wing_{side}", (0, 0, -65 * sx))), (1.0, fp(f"wing_{side}", (0, 0, -55 * sx))),
              (1.4, fp(f"wing_{side}", (0, 0, -70 * sx))), (2.0, fp(f"wing_{side}", (0, 0, -60 * sx))), (2.6, Z3))
        a.rot(f"leg_f{side}", (0, Z3), (0.6, (-80, 0, 0)), (2.0, (-80, 0, 0)), (2.6, Z3))
        a.rot(f"shin_f{side}", (0, Z3), (0.6, (60, 0, 0)), (2.0, (60, 0, 0)), (2.6, Z3))
        a.rot(f"leg_h{side}", (0, Z3), (0.6, (35, 0, 0)), (2.0, (35, 0, 0)), (2.6, Z3))
    a.rot("tail", (0, Z3), (0.6, (40, 0, 0)), (2.0, (40, 0, 0)), (2.6, Z3))

    # ---------------------------------------------------------------- roar (phase change): rears, spreads
    # everything, screams
    a = m.anim("roar", 2.4)
    a.rot("body", (0, Z3), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, Z3))
    a.rot("neck", (0, Z3), (0.5, (-15, 0, 0)), (1.9, (-15, 0, 0)), (2.4, Z3))
    a.rot("head", (0, Z3), (0.5, (-20, 0, 0)), (1.0, (-10, 15, 0)), (1.5, (-10, -15, 0)), (1.9, (-20, 0, 0)), (2.4, Z3))
    a.rot("jaw", (0, Z3), (0.5, (50, 0, 0)), (1.9, (50, 0, 0)), (2.4, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.5, fp(f"wing_{side}", (0, 0, -35 * sx))), (1.9, fp(f"wing_{side}", (0, 0, -40 * sx))), (2.4, Z3))
        a.rot(f"leg_f{side}", (0, Z3), (0.5, (-50, 0, 0)), (1.9, (-50, 0, 0)), (2.4, Z3))
    a.rot("tail", (0, Z3), (0.5, (35, 0, 0)), (1.9, (35, 0, 0)), (2.4, Z3))

    # ---------------------------------------------------------------- stagger: crashes down, wings askew
    a = m.anim("stagger", 2.4)
    a.pos("bone", (0, Z3), (0.3, (0, -9, 0)), (1.9, (0, -9, 0)), (2.4, Z3))
    a.rot("body", (0, Z3), (0.3, (6, 0, 12)), (1.9, (6, 0, 12)), (2.4, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"leg_f{side}", (0, Z3), (0.3, (-40, 0, 0)), (1.9, (-40, 0, 0)), (2.4, Z3))
        a.rot(f"shin_f{side}", (0, Z3), (0.3, (70, 0, 0)), (1.9, (70, 0, 0)), (2.4, Z3))
        a.rot(f"leg_h{side}", (0, Z3), (0.3, (-55, 0, 0)), (1.9, (-55, 0, 0)), (2.4, Z3))
        a.rot(f"shin_h{side}", (0, Z3), (0.3, (80, 0, 0)), (1.9, (80, 0, 0)), (2.4, Z3))
    a.rot("wing_l", (0, Z3), (0.3, (50, 60, -10)), (1.9, (50, 60, -10)), (2.4, Z3))
    a.rot("wing_r", (0, Z3), (0.3, (20, -10, 20)), (1.9, (20, -10, 20)), (2.4, Z3))
    a.rot("neck", (0, Z3), (0.3, (40, 0, 10)), (1.9, (40, 0, 10)), (2.4, Z3))
    a.rot("head", (0, Z3), (0.3, (10, 20, 20)), (1.9, (10, 20, 20)), (2.4, Z3))

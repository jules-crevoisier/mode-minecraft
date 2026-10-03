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
WHITE_S = (176, 170, 166)
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
    """Small overlapping feathers (head, neck, chest, trousers): staggered rows of soft rounded tips,
    a gentle shadow under each row, a pale sheen at the root and a slight tint per feather."""
    def f(face, x, y, w, h):
        if face in ("top", "bottom"):
            c = top or base
            if face == "bottom":
                c = mix(c, dark, 0.3)
            elif (x + y) % 3 == 0:
                c = mix(c, light, 0.25)
            return jit(c, x, y, seed, 0.03)
        row = y // fh
        shift = (row % 2) * (fw // 2)
        col = (x + shift) // fw
        u = (x + shift) % fw
        v = y % fh
        c = mix(base, light, 0.25) if hsh(col, row, seed) % 4 == 0 else base
        if v == 0:
            c = mix(c, light, 0.35)
        elif v == fh - 1:
            centre = abs(u - (fw - 1) / 2) < 1
            c = mix(c, dark, 0.22 if centre else 0.5)
            if tip is not None and centre:
                c = mix(c, tip, 0.7)
        elif u == 0:
            c = mix(c, dark, 0.22)
        return jit(c, x, y, seed, 0.025)
    return f


def grad(stops, t):
    """Colour along a gradient: stops = [(t, colour), ...] sorted by t in 0..1."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


def quills(stops, fw=3, seed=0, along="y", base_at_end=True, lengths=None, slot_from=None, rim=None,
           edges=("front",)):
    """Long flight feathers side by side on the broad faces of a wing plane.

    ``along`` is the texture axis the feathers run along; ``base_at_end`` puts the feather roots at the
    far end of that axis (wing planes: texture row 0 is the trailing edge). ``lengths(i, n)`` shortens
    feather i (fan shapes); ``slot_from`` (0..1) opens slots between the feathers beyond that fraction
    of their length (an eagle's fingered wingtip). Feather tips are cut to points. Only the side faces in
    ``edges`` are painted ("all" for a solid tuft), so the thin edge of a ragged plane never outlines it."""
    def f(face, x, y, w, h):
        if face not in ("top", "bottom"):
            if edges != "all" and face not in edges:
                return None
            return grad(stops, 0.15) if rim is None else rim
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
            c = mix(c, (70, 60, 60), 0.2)                  # soft shadow line between feathers
        elif abs(u - mid) < 0.6 and a < L - 2:
            c = mix(c, WHITE_PX, 0.22)                     # the shaft
        elif u == fw - 1:
            c = mix(c, WHITE_PX, 0.08)
        elif (a + u + i) % 4 == 0:
            c = mul(c, 0.93)                               # barbs
        if face == "bottom":
            c = mul(c, 1.25)                               # cancels the baked underside shade: the
        return jit(c, x, y, seed + i, 0.03)                # folded wing shows its underside outward
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
# Rest rotations of the wing chain: half-raised (shoulder pitched up so the wrist stands above the back,
# the arm splayed outward, the hand bent back so the primaries fan out past the rump). The flight pose
# is all zero (spread), so the flight offsets below are simply minus these.
WING_REST = {"shoulder_l": (25, 0, 0), "shoulder_r": (25, 0, 0),
             "wing_l": (-90, -70, -30), "wing_r": (-90, 70, 30),
             "wingtip_l": (0, -50, -8), "wingtip_r": (0, 50, 8)}
WING_SPREAD = {"shoulder_l": (0, 0, 0), "shoulder_r": (0, 0, 0), "wing_l": (0, 0, 0), "wing_r": (0, 0, 0),
               "wingtip_l": (0, -12, 0), "wingtip_r": (0, 12, 0)}
BODY_PITCH = 9          # the body leans forward around the hips: chest low, haunches high


def build():
    m = Model("gryphon_knight", seed=77, shadow=2.0, walk_speed=1.1, walk_scale=1.0, head="head")
    piv = {}

    def part(name, parent, abs_pivot, rot=(0, 0, 0)):
        pp = piv[parent] if parent else (0, 0, 0)
        m.part(name, parent, pivot=tuple(abs_pivot[i] - pp[i] for i in range(3)), rot=rot)
        piv[name] = abs_pivot

    def ab(p, x0, htop, z0, w, h, d, paint, glow=None, grow=0.0):
        """Box in the (unpitched) body design frame: x0/z0 min corner, htop = top height above the ground."""
        P = piv[p]
        m.box(p, x0 - P[0], (24 - htop) - P[1], z0 - P[2], w, h, d, paint, glow=glow, grow=grow)

    def g(h):
        return 24 - h

    # ------------------------------------------------------------------ skeleton
    part("bone", None, (0, 24, 0))
    part("body", "bone", (0, g(36), 14), rot=(BODY_PITCH, 0, 0))
    # S-curved neck: the base thrusts forward, the upper neck rises, the head is held level and proud
    m.part("neck", "body", pivot=(0, g(44) - g(36), -27 - 14), rot=(38, 0, 0))
    m.part("neck2", "neck", pivot=(0, -9, -1), rot=(-52, 0, 0))
    m.part("head", "neck2", pivot=(0, -9, 0), rot=(5, 0, 0))
    m.part("jaw", "head", pivot=(0, -3, -12))
    m.part("crest", "head", pivot=(0, -11, 5), rot=(-28, 0, 0))
    m.part("plume", "head", pivot=(0, -16, 0), rot=(-38, 0, 0))
    m.part("plume_l", "plume", pivot=(1.5, 0, 1), rot=(-14, 0, 16))
    m.part("plume_r", "plume", pivot=(-1.5, 0, 1), rot=(-14, 0, -16))
    for side, sx in (("l", 1), ("r", -1)):
        m.part(f"shoulder_{side}", "body", pivot=(sx * 10, g(47) - g(36), -18 - 14), rot=WING_REST[f"shoulder_{side}"])
        m.part(f"wing_{side}", f"shoulder_{side}", pivot=(0, 0, 0), rot=WING_REST[f"wing_{side}"])
        m.part(f"wingtip_{side}", f"wing_{side}", pivot=(sx * 23, 0, 0), rot=WING_REST[f"wingtip_{side}"])
    for side, sx in (("l", 1), ("r", -1)):
        part(f"leg_f{side}", "body", (sx * 8, g(31), -20), rot=(-BODY_PITCH, 0, 0))
        part(f"shin_f{side}", f"leg_f{side}", (sx * 8, g(21), -20))
        part(f"leg_h{side}", "body", (sx * 7, g(39), 19), rot=(-6 - BODY_PITCH, 0, 0))
        part(f"shin_h{side}", f"leg_h{side}", (sx * 7, g(24), 21), rot=(24, 0, 0))
    m.part("tail", "body", pivot=(0, g(42) - g(36), 26 - 14), rot=(-55, 0, 0))
    m.part("tail2", "tail", pivot=(0, 0, 15), rot=(35, 0, 0))
    m.part("tail3", "tail2", pivot=(0, 0, 14), rot=(45, 0, 0))

    # ------------------------------------------------------------------ body: a deep eagle breast, a lean
    # lion waist and powerful haunches
    breast = scales(WHITE, WHITE_S, CREAM, 1, tip=GOLD_FL)
    ab("body", -12, 47, -32, 24, 25, 22, {"front": scales(WHITE, WHITE_S, CREAM, 1, tip=WHITE_D), "*": breast})
    ab("body", -10, 36, -35, 20, 13, 6, scales(WHITE, WHITE_S, CREAM, 2, tip=WHITE_D))   # the keel
    ab("body", -9, 43, -12, 18, 18, 20, fur(seed=2))                                   # waist
    ab("body", -10, 45, 7, 20, 20, 19, fur(seed=3))                                    # rump
    ab("body", -2, 47, 9, 4, 2, 15, fur(FUR_D, (130, 86, 44), FUR, seed=4))            # spine ridge
    # barding: only the chest plate with the sapphire (the feathers dominate)
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
            return GOLD_D
        return None
    ab("body", -10, 41, -36, 20, 11, 2, {"front": plate(inlay=peytral_inlay), "*": plate()}, glow={"front": gem})
    # a narrow azure girth strap with the temple star (a last touch of livery)
    ab("body", -9.5, 43.5, -9, 19, 19, 3, {"top": None, "bottom": None, "front": None, "back": None,
                                            "*": lambda f_, x, y, w, h: GOLD if y in (0, h - 1) else AZURE})

    # ------------------------------------------------------------------ neck, mane and head
    m.box("neck", -8, -11, -7, 16, 13, 14, scales(WHITE, WHITE_S, CREAM, 5, fw=4, fh=3))
    m.box("neck2", -7, -11, -6, 14, 13, 12, scales(WHITE, WHITE_S, CREAM, 6, fw=4, fh=3))
    # the mane: two layered rings of long white feathers tipped gold, wider than the head
    m.box("neck", -13, -6, -11, 26, 10, 22, ruff(61))
    m.box("neck2", -11, -8, -9, 22, 8, 18, ruff(62))
    m.box("neck", -2, -13, 6, 4, 9, 3, plate(seed=7))                                  # one nape lame
    # eagle eye under the heavy brow: glowing gold iris, black pupil, the dark stripe running back

    def eye_px(f_, x, y, w, h):
        if f_ not in ("left", "right"):
            return None
        u = x if f_ == "left" else w - 1 - x
        if y in (6, 7) and u in (3, 4):
            return (24, 18, 14) if (u == 3 and y == 7) else EYE
        return None

    def eye_shade(f_, x, y, w, h):
        if f_ not in ("left", "right"):
            return None
        u = x if f_ == "left" else w - 1 - x
        if (y in (6, 7) and u in (2, 5)) or (y == 8 and 2 <= u <= 11) or (y == 5 and 1 <= u <= 6):
            return (84, 72, 66)
        return None
    sk = scales(WHITE, WHITE_S, CREAM, 8, fw=3, fh=2)

    def skull(f_, x, y, w, h):
        return eye_px(f_, x, y, w, h) or eye_shade(f_, x, y, w, h) or sk(f_, x, y, w, h)
    m.box("head", -8, -14, -11, 16, 14, 17, skull, glow=eye_px)
    # heavy brow ridge jutting over the eyes, in shadow underneath
    m.box("head", -9.5, -14, -14, 19, 5, 11, {"bottom": (96, 88, 84),
                                             "*": scales(WHITE_D, WHITE_S, WHITE, 9, fw=3, fh=2)})
    # the beak: tall cere, long upper bill, a hook curving down and back to a dark point
    m.box("head", -5.5, -12, -19, 11, 10, 8, beak(10))
    m.box("head", -4.5, -11, -26, 9, 8, 7, beak(11))
    m.box("head", -3.5, -10, -31, 7, 11, 5, beak(12, tip_rows=3))
    m.box("head", -2.5, 1, -30, 5, 4, 4, beak(14, tip_rows=4))
    m.box("head", -1.5, 4, -28, 3, 2, 2, BEAK_TIP)
    m.box("jaw", -4.5, 0, -13, 9, 3, 13, beak(13))
    m.box("jaw", -3.5, -1, -13, 7, 1, 1, (250, 236, 200))
    # feather tufts sweeping back from the skull
    tuftq = quills([(0, WHITE), (0.6, CREAM), (0.85, GOLD_FL), (1, GOLD_F)], fw=2, seed=63, along="y",
                   base_at_end=True, rim=WHITE, edges="all")
    for dx in (-7, -2, 3):
        m.box("crest", dx, -3, 0, 4, 4, 13 if dx == -2 else 10, {"top": tuftq, "*": scales(WHITE, WHITE_S, GOLD_FL, 64, fw=3, fh=2, tip=GOLD_F)})
    for sx in (-1, 1):
        m.box("head", 6 if sx > 0 else -10, -12, 1, 4, 8, 9, scales(WHITE, WHITE_S, GOLD_FL, 14, fw=3, fh=2, tip=GOLD_F))
    # the chanfron: a silver crown plate and nasal, carrying the plume
    m.box("head", -5, -16, -12, 10, 2, 13, plate(seed=15, inlay=lambda f_, x, y, w, h: GOLD if f_ == "top" and x == w // 2 else None))
    m.box("head", -3, -13.5, -22, 6, 2, 10, plate(seed=16, rivets=False))
    m.box("plume", -2.5, -3, -2.5, 5, 3, 5, plate(GOLD, GOLD_D, rivets=False))
    plume_main = quills([(0, AZURE_D), (0.45, AZURE), (0.8, AZURE_L), (1, WHITE)], fw=2, seed=18, along="y",
                        base_at_end=True, rim=AZURE, edges="all")
    m.box("plume", -2, -21, -2, 4, 18, 5, plume_main)
    m.box("plume", -1, -27, -1, 2, 7, 4, quills([(0, AZURE), (0.6, AZURE_L), (1, WHITE)], fw=2, seed=19,
                                                  along="y", base_at_end=True, rim=AZURE_L, edges="all"))
    for p_ in ("plume_l", "plume_r"):
        m.box(p_, -1, -15, -1.5, 2, 13, 4, quills([(0, WHITE_D), (0.5, WHITE), (1, AZURE_L)], fw=2, seed=20,
                                                   along="y", base_at_end=True, rim=WHITE, edges="all"))
    m.box("plume", -0.5, -2, -3, 1, 1, 1, GEM, glow=GEM)

    # ------------------------------------------------------------------ wings, in layers stepped along the
    # plane's thickness (local frame = spread wing: +x outward along the bone, +z trailing, -y the top)
    lesser = [(0, GOLD_FL), (0.6, GOLD_F), (1, GOLD_FD)]
    greater = [(0, WHITE), (0.6, CREAM), (0.85, GOLD_FL), (1, GOLD_F)]
    sec = [(0, CREAM), (0.5, WHITE), (0.75, WHITE), (0.88, GOLD_FL), (1, GOLD_F)]
    prim = [(0, WHITE), (0.3, GOLD_FL), (0.62, GOLD_F), (0.88, GOLD_FD), (1, (110, 76, 36))]

    def prim_len(i, n, a_len):
        k = n - 1 - i
        return a_len - (6, 1, 0, 2, 5)[min(k, 4)]
    for side, sx in (("l", 1), ("r", -1)):
        w, t = f"wing_{side}", f"wingtip_{side}"
        x0 = 0 if sx > 0 else -23
        m.box(w, x0, -2, -2, 23, 4, 4, {"bottom": lambda f_, x, y, w_, h_: jit(mul(CREAM, 1.25), x, y, 20, 0.04),
                                          "*": scales(WHITE, WHITE_S, CREAM, 20, fw=3, fh=2)})   # arm
        m.box(w, x0, -2.5, 1, 23, 1, 7, quills(lesser, fw=3, seed=21, along="y", base_at_end=True,
                                               edges=("front",)))                                    # lesser coverts
        m.box(w, x0, -1.5, 1, 23, 1, 11, quills(greater, fw=3, seed=22, along="y", base_at_end=True))  # greater coverts
        m.box(w, x0, -0.5, 2, 23, 1, 18, quills(sec, fw=4, seed=23, along="y", base_at_end=True))      # secondaries
        x1 = 0 if sx > 0 else -13
        m.box(t, x1, -2, -2, 13, 4, 4, scales(WHITE, WHITE_S, CREAM, 24, fw=3, fh=2))              # hand
        m.box(t, x1, -2, 1, 13, 1, 7, quills(lesser, fw=3, seed=25, along="y", base_at_end=True))   # primary coverts
        x2 = 0 if sx > 0 else -34
        m.box(t, x2, -1, -1, 34, 1, 16, quills(prim, fw=3, seed=26 + sx, along="x", base_at_end=sx < 0,
                                                lengths=prim_len, slot_from=0.7,
                                                edges=("front", "right" if sx > 0 else "left")))   # primaries

    # ------------------------------------------------------------------ legs
    for side, sx in (("l", 1), ("r", -1)):
        lf, sf, lh, sh = f"leg_f{side}", f"shin_f{side}", f"leg_h{side}", f"shin_h{side}"
        X = sx * 8
        # eagle forelegs: feathered trousers, scaled yellow shank, a broad foot with spread black talons
        ab(lf, X - 5, 33, -25, 10, 14, 11, scales(WHITE, WHITE_S, CREAM, 30 + sx, fw=3, fh=2, tip=WHITE_D))
        ab(sf, X - 3, 21, -23, 6, 16, 6, scaled_leg(31 + sx))
        ab(sf, X - 4, 6, -25, 8, 3, 9, scaled_leg(32 + sx))                                 # the foot
        for dx, dz, ln in ((-5, -1, 6), (-1.5, 0, 8), (2, -1, 6)):                           # three front toes
            ab(sf, X + dx + (0.5 if dx < 0 else 0), 3, -25 - ln + 2 + dz, 3, 2, ln, scaled_leg(33 + sx))
            ab(sf, X + dx + (0.5 if dx < 0 else 0), 4, -25 - ln + dz, 3, 4, 2, talon)        # hooked talon
        ab(sf, X - 1, 3, -16, 3, 2, 5, scaled_leg(34 + sx))                                  # hind toe
        ab(sf, X - 1, 4, -12, 3, 4, 2, talon)
        # lion hind legs: a heavy haunch, a lean shank with the hock behind, a broad paw with claws
        ab(lh, sx * 7 - 4.5, 41, 11, 9, 19, 15, fur(seed=35 + sx))
        ab(sh, sx * 7 - 3, 24, 18, 6, 22, 7, fur(seed=36 + sx))
        claws = lambda f_, x, y, w, h: (236, 226, 200) if y >= h - 2 and x % 2 == 1 else fur(seed=37)(f_, x, y, w, h)
        ab(sh, sx * 7 - 4.5, 3, 13, 9, 5, 11, {"front": claws, "*": fur(seed=37)})
    # the lion tail: long, drooping, curling up into a dark tuft
    m.box("tail", -2, -2, -1, 4, 4, 16, fur(seed=40))
    m.box("tail2", -1.5, -1.5, -1, 3, 3, 15, fur(seed=41))
    m.box("tail3", -1.5, -1.5, -1, 3, 3, 8, fur(seed=42))

    def tuft(f_, x, y, w, h):
        k = hsh(x, 43) % 4
        c = TUFT if (x + k) % 3 else mix(TUFT, (60, 34, 20), 0.6)
        if f_ in ("front", "back", "left", "right") and y >= h - 1 - k % 2:
            c = mix(c, FUR_D, 0.4)
        return jit(c, x, y, 44, 0.06)
    m.box("tail3", -3, -3, 5, 6, 6, 10, tuft)

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
    for sh_ in ("shoulder_l", "shoulder_r"):
        a.rot(sh_, (0, Z3), (0.7, fp(sh_)), (1.3, fp(sh_)), (1.8, Z3))
    a.rot("body", (0, Z3), (0.7, (-28, 0, 0)), (0.9, (-12, 0, 0), "linear"), (1.3, (-10, 0, 0)), (1.8, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.7, fp(f"wing_{side}", (70, 20 * sx, -40 * sx))),
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
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.7, fp(f"wing_{side}", (70, 0, -45 * sx))),
              (0.9, fp(f"wing_{side}", (0, -65 * sx, -10 * sx)), "linear"), (1.3, fp(f"wing_{side}", (0, -55 * sx, -10 * sx))),
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
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.7, fp(f"wing_{side}", (70, 25 * sx, -35 * sx))),
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
        a.rot(f"wing_{side}", (0, fp(f"wing_{side}")), (0.55, fp(f"wing_{side}", (65, 0, -45 * sx))),
              (0.75, fp(f"wing_{side}", (0, 0, 40 * sx)), "linear"), (1.1, fp(f"wing_{side}", (0, 0, 30 * sx))),
              (1.8, Z3))
        a.rot(f"wingtip_{side}", (0, fp(f"wingtip_{side}")), (0.55, fp(f"wingtip_{side}", (0, 0, -30 * sx))),
              (0.75, fp(f"wingtip_{side}", (0, 0, 25 * sx)), "linear"), (1.8, Z3))

    # ---------------------------------------------------------------- storm (phase 2 spectacle): rears up,
    # wings raised to the sky, a long scream while the bolts fall (call at 1.0 s = 20 t)
    a = m.anim("storm", 2.6)
    for sh_ in ("shoulder_l", "shoulder_r"):
        a.rot(sh_, (0, Z3), (0.6, fp(sh_)), (2.0, fp(sh_)), (2.6, Z3))
    a.rot("body", (0, Z3), (0.6, (-40, 0, 0)), (2.0, (-40, 0, 0)), (2.6, Z3))
    a.pos("bone", (0, Z3), (0.6, (0, 0, 6)), (2.0, (0, 0, 6)), (2.6, Z3))
    a.rot("neck", (0, Z3), (0.6, (-20, 0, 0)), (2.0, (-24, 0, 0)), (2.6, Z3))
    a.rot("head", (0, Z3), (0.6, (-25, 0, 0)), (2.0, (-25, 0, 0)), (2.6, Z3))
    a.rot("jaw", (0, Z3), (0.6, (45, 0, 0)), (2.0, (45, 0, 0)), (2.6, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.6, fp(f"wing_{side}", (75, 0, -55 * sx))), (1.0, fp(f"wing_{side}", (70, 0, -45 * sx))),
              (1.4, fp(f"wing_{side}", (80, 0, -60 * sx))), (2.0, fp(f"wing_{side}", (75, 0, -50 * sx))), (2.6, Z3))
        a.rot(f"leg_f{side}", (0, Z3), (0.6, (-80, 0, 0)), (2.0, (-80, 0, 0)), (2.6, Z3))
        a.rot(f"shin_f{side}", (0, Z3), (0.6, (60, 0, 0)), (2.0, (60, 0, 0)), (2.6, Z3))
        a.rot(f"leg_h{side}", (0, Z3), (0.6, (35, 0, 0)), (2.0, (35, 0, 0)), (2.6, Z3))
    a.rot("tail", (0, Z3), (0.6, (40, 0, 0)), (2.0, (40, 0, 0)), (2.6, Z3))

    # ---------------------------------------------------------------- roar (phase change): rears, spreads
    # everything, screams
    a = m.anim("roar", 2.4)
    for sh_ in ("shoulder_l", "shoulder_r"):
        a.rot(sh_, (0, Z3), (0.5, fp(sh_)), (1.9, fp(sh_)), (2.4, Z3))
    a.rot("body", (0, Z3), (0.5, (-30, 0, 0)), (1.9, (-30, 0, 0)), (2.4, Z3))
    a.rot("neck", (0, Z3), (0.5, (-15, 0, 0)), (1.9, (-15, 0, 0)), (2.4, Z3))
    a.rot("head", (0, Z3), (0.5, (-20, 0, 0)), (1.0, (-10, 15, 0)), (1.5, (-10, -15, 0)), (1.9, (-20, 0, 0)), (2.4, Z3))
    a.rot("jaw", (0, Z3), (0.5, (50, 0, 0)), (1.9, (50, 0, 0)), (2.4, Z3))
    for side, sx in (("l", 1), ("r", -1)):
        a.rot(f"wing_{side}", (0, Z3), (0.5, fp(f"wing_{side}", (70, 0, -30 * sx))), (1.9, fp(f"wing_{side}", (72, 0, -35 * sx))), (2.4, Z3))
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

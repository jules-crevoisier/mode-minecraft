"""Wayfarer quest givers (Guild Agent, Scholar, Tinkerer, Druid, Dwarf Elder): one villager-like body, a texture
variant per role (same order as wf/npcs.py ROLE_ORDER).

Silhouette: the tall villager head with its big nose, a long robe over the legs, free arms (they wave when greeting a
player), and the role's gear: a guild tricorne and a map satchel, a scholar's cap and spectacles, brass goggles and a
tool backpack, a leaf crown and a vine circlet, an iron helm and a long braided beard. Gear another role does not
wear is left transparent (every variant keeps the same cubes).
"""
from ..models import Model
from ..npcs import ROLE_ORDER
from ..texgen import mix, mul


def _h(*v):
    r = 2166136261
    for k in v:
        r = ((r ^ (int(k) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return (r >> 8) & 0xFFFF


# role: palette
PAL = {
    "guild_agent": dict(cloth=(52, 84, 140), cloth2=(40, 64, 108), trim=(206, 164, 72), shirt=(226, 214, 186),
                        skin=(214, 166, 128), hair=(74, 50, 34), eyes=(70, 110, 60), belt=(92, 60, 36),
                        hat=(112, 74, 42), hat2=(84, 54, 30), pack=(130, 88, 50), boots=(70, 48, 30)),
    "scholar": dict(cloth=(122, 34, 52), cloth2=(96, 24, 40), trim=(214, 176, 82), shirt=(236, 232, 220),
                    skin=(226, 186, 150), hair=(160, 160, 168), eyes=(60, 80, 130), belt=(52, 36, 30),
                    hat=(34, 34, 42), hat2=(24, 24, 30), pack=None, boots=(50, 36, 30)),
    "tinkerer": dict(cloth=(176, 112, 60), cloth2=(146, 88, 46), trim=(196, 140, 64), shirt=(210, 196, 170),
                     skin=(200, 150, 112), hair=(170, 84, 40), eyes=(90, 70, 40), belt=(64, 44, 30),
                     hat=None, hat2=None, pack=(184, 120, 60), boots=(60, 42, 30), apron=(98, 66, 42)),
    "druid": dict(cloth=(62, 112, 60), cloth2=(44, 86, 46), trim=(156, 196, 96), shirt=(196, 214, 160),
                  skin=(232, 204, 176), hair=(232, 226, 196), eyes=(110, 170, 90), belt=(98, 72, 44),
                  hat=(70, 140, 54), hat2=(46, 102, 40), pack=None, boots=(88, 64, 40)),
    "dwarf_elder": dict(cloth=(128, 52, 40), cloth2=(100, 40, 32), trim=(214, 170, 64), shirt=(150, 150, 160),
                        skin=(206, 146, 116), hair=(184, 92, 44), eyes=(60, 60, 70), belt=(70, 46, 30),
                        hat=(148, 150, 160), hat2=(104, 106, 116), pack=None, boots=(56, 40, 30)),
}
DARK = (24, 22, 26)


def fabric(base, base2, seed=0, trim=None, trim_rows=(), buttons=None):
    """Woven cloth: a fine twill of two tones, ``trim`` rows (texel y on the side faces) and a button column."""
    def f(face, x, y, w, h):
        c = base if (x + y * 2 + seed) % 5 else base2
        if _h(x, y, seed) % 11 == 0:
            c = mix(c, (255, 255, 255), 0.08)
        if face in ("top", "bottom"):
            return mul(c, 0.92)
        if trim and (y in trim_rows or (y - h) in trim_rows):
            return trim
        if buttons and face == "front" and x == w // 2 and y % 3 == 1:
            return buttons
        return c
    return f


def skin_paint(p):
    def f(face, x, y, w, h):
        return p["skin"] if (x + y) % 7 else mul(p["skin"], 0.95)
    return f


def head_paint(role, p):
    """Villager face: hair on top and at the back, brows, eyes (white and iris); spectacles for the scholar."""
    skin, hair = p["skin"], p["hair"]

    def f(face, x, y, w, h):
        if face == "top":
            return hair if (x * 3 + y) % 6 else mul(hair, 0.85)
        if face == "bottom":
            return mul(skin, 0.85)
        if face == "back":
            return hair if y < 8 or (x + y) % 3 else mul(hair, 0.85)
        if face in ("left", "right"):
            if y < 3 or (y < 7 and (x > w - 4 if face == "left" else x < 3)):
                return hair
            return skin
        # front
        if y < 2:
            return hair
        if y == 3 and x in (1, 2, 5, 6):
            return mul(hair, 0.8)                     # brows
        if y == 4 and x in (1, 6):
            return (240, 240, 236)
        if y == 4 and x in (2, 5):
            return p["eyes"]
        if role == "scholar" and y in (4, 5) and x in (0, 3, 4, 7):
            return (196, 160, 70) if y == 4 else skin  # spectacles: gold rims beside the eyes
        if role == "scholar" and y == 3 and x in (1, 2, 5, 6):
            return (196, 160, 70)
        if role == "dwarf_elder" and y >= 6:
            return hair                               # the beard starts on the cheeks
        return skin if (x + y) % 9 else mul(skin, 0.95)
    return f


def build(variant=None):
    role = variant or ROLE_ORDER[0]
    p = PAL[role]
    m = Model("wayfarer_npc", seed=171, shadow=0.5, variants=ROLE_ORDER, walk_speed=1.0, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2, -12, 0))
    m.part("leg_l", "bone", pivot=(2, -12, 0))
    m.part("body", "bone", pivot=(0, -12, 0))
    m.part("head", "body", pivot=(0, -12, 0))
    m.part("arm_r", "body", pivot=(-6, -11, 0), rot=(0, 0, 4))
    m.part("arm_l", "body", pivot=(6, -11, 0), rot=(0, 0, -4))

    cloth = fabric(p["cloth"], p["cloth2"], seed=1, trim=p["trim"], trim_rows=(0, -1), buttons=p["trim"])
    robe = fabric(p["cloth"], p["cloth2"], seed=2, trim=p["trim"], trim_rows=(-1, -2))
    boots = p["boots"]

    # ------------------------------------------------------------------ legs (the robe hides most of them)
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -2, 0, -2, 4, 12, 4, {"top": p["cloth2"], "*": lambda f_, x, y, w, h: boots if y >= h - 3
                                         else mul(p["cloth2"], 0.9)})

    # ------------------------------------------------------------------ body: tunic, robe, belt
    def tunic(f_, x, y, w, h):
        if f_ == "front" and role == "tinkerer" and x in range(2, 6) and y >= 3:
            return p["apron"] if (x + y) % 4 else mul(p["apron"], 0.9)        # leather apron
        if f_ == "front" and y < 2 and 2 <= x <= 5:
            return p["shirt"]                                                   # collar
        return cloth(f_, x, y, w, h)
    m.box("body", -4, -12, -3, 8, 12, 6, tunic)

    def skirt(f_, x, y, w, h):
        if f_ == "front" and role == "tinkerer" and x in range(2, 7) and y < h - 2:
            return p["apron"] if (x + y) % 4 else mul(p["apron"], 0.9)
        if f_ == "front" and role == "druid" and (x * 2 + y) % 7 == 0:
            return p["trim"]                                                     # embroidered leaves
        return robe(f_, x, y, w, h)
    m.box("body", -4.5, -1, -3.5, 9, 9, 7, skirt)

    def belt(f_, x, y, w, h):
        if f_ == "front" and x in (4,):
            return p["trim"]                                                     # buckle
        return p["belt"]
    m.box("body", -4.5, -2, -3.5, 9, 1, 7, belt)

    # satchel (guild agent: a map case) / tool backpack (tinkerer) on the back
    def pack(f_, x, y, w, h):
        if p.get("pack") is None:
            return None
        c = p["pack"]
        if role == "tinkerer":
            if f_ == "back" and (x - 2) ** 2 + (y - 3) ** 2 <= 2:
                return (210, 170, 80) if (x + y) % 2 else (150, 110, 50)        # a brass gear
            if y == 0:
                return mul(c, 1.15)
        elif f_ == "back" and y == 1:
            return p["trim"]                                                     # the strap's buckle line
        return c if (x + y) % 5 else mul(c, 0.86)
    m.box("body", -3, -10, 3, 6, 7, 3, pack)

    # ------------------------------------------------------------------ head: villager head, nose, gear
    m.box("head", -4, -10, -4, 8, 10, 8, head_paint(role, p))
    m.box("head", -1, -4, -6, 2, 4, 2, {"*": lambda f_, x, y, w, h: mul(p["skin"], 0.94 if f_ != "top" else 1.0)})

    def brim(f_, x, y, w, h):
        if p.get("hat") is None:
            return None
        if role == "druid":                                                     # a crown of leaves
            if f_ in ("top", "bottom"):
                if 1 <= x <= w - 2 and 1 <= y <= w - 2:
                    return None
                return p["hat"] if _h(x, y, 3) % 3 else (230, 120, 160)         # with a few blossoms
            return p["hat"] if (x + y) % 3 else p["hat2"]
        if role == "dwarf_elder":
            return p["hat2"] if f_ != "top" or (x + y) % 4 else p["hat"]
        return p["hat2"] if f_ == "bottom" else p["hat"]
    m.box("head", -5, -11, -5, 10, 1, 10, brim)

    def crown(f_, x, y, w, h):
        if p.get("hat") is None or role == "druid":
            return None
        if role == "guild_agent" and f_ != "top" and y == h - 1:
            return p["trim"]                                                     # the hat band
        if role == "dwarf_elder":
            if f_ == "front" and x in (2, 3) and y >= 1:
                return p["hat2"]                                                 # nose guard ridge
            return p["hat"] if (x + y) % 5 else mul(p["hat"], 1.12)
        return p["hat"] if (x * 2 + y) % 7 else p["hat2"]
    m.box("head", -3, -14, -3, 6, 3, 6, crown)

    def band(f_, x, y, w, h):
        """Brass goggles (tinkerer), a vine circlet (druid)."""
        if f_ in ("top", "bottom"):
            return None
        if role == "tinkerer":
            if f_ == "front" and x in (1, 2, 6, 7):
                return (120, 200, 210) if y == 0 else (180, 130, 50)              # the two lenses
            return (160, 116, 52) if (x + y) % 2 else (196, 150, 70)
        if role == "druid":
            return (70, 120, 50) if (x + y) % 3 else ((236, 230, 120) if x % 5 == 0 else None)
        return None
    m.box("head", -4.5, -8, -4.5, 9, 2, 9, band)

    def beard(f_, x, y, w, h):
        if role != "dwarf_elder":
            return None
        if y == h - 1 and x in (0, w - 1):
            return None
        if y == h - 2 and f_ == "front" and x in (2, 3):
            return p["trim"]                                                     # a gold braid ring
        return p["hair"] if (x + y) % 3 else mul(p["hair"], 0.85)
    m.box("head", -4, -3, -5, 8, 9, 1, beard)

    # ------------------------------------------------------------------ arms: sleeves and hands
    def sleeve(f_, x, y, w, h):
        if f_ == "top":
            return p["cloth"]
        if y >= h - 3:
            return p["skin"]
        if y == h - 4:
            return p["trim"]                                                     # cuff
        return cloth(f_, x, y, w, h)
    for arm in ("arm_r", "arm_l"):
        m.box(arm, -2, -1, -2, 4, 11, 4, sleeve)

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 4.0)
    idle.rot("body", (0, (0, 0, 0)), (2.0, (1.5, 0, 0)), (4.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (2.0, (-3, 0, 2)), (4.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (2.0, (-3, 0, -2)), (4.0, (0, 0, 0)))

    walk = m.anim("walk", 1.2)
    walk.rot("leg_r", (0, (24, 0, 0)), (0.6, (-24, 0, 0)), (1.2, (24, 0, 0)))
    walk.rot("leg_l", (0, (-24, 0, 0)), (0.6, (24, 0, 0)), (1.2, (-24, 0, 0)))
    walk.rot("arm_r", (0, (-20, 0, 0)), (0.6, (20, 0, 0)), (1.2, (-20, 0, 0)))
    walk.rot("arm_l", (0, (20, 0, 0)), (0.6, (-20, 0, 0)), (1.2, (20, 0, 0)))

    # greet: the right arm goes up and waves twice (when a player talks to it)
    a = m.anim("greet", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.3, (-150, 0, 20)), (0.55, (-150, 0, 40)), (0.8, (-150, 0, 10)),
          (1.05, (-150, 0, 40)), (1.3, (-150, 0, 20)), (1.6, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.3, (-3, 0, 0)), (1.3, (-3, 0, 0)), (1.6, (0, 0, 0)))
    # nod: a contract accepted or handed in
    a = m.anim("nod", 0.8)
    a.rot("head", (0, (0, 0, 0)), (0.2, (18, 0, 0)), (0.4, (0, 0, 0)), (0.6, (14, 0, 0)), (0.8, (0, 0, 0)))
    return m

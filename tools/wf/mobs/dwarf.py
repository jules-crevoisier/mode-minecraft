"""Dwarf (Nain): the people of the Deep Dwarven City and the dwarven mines (tools/wf/denizens.py), one texture variant
per role: smith, miner, brewer, gemcutter, guard (same order as denizens.ROLE_ORDER["dwarf"]).

Silhouette idea: a walking anvil. Short and twice as wide as a villager, a barrel chest over stubby legs and huge
boots, a big nose over a beard that reaches the belt (two braids with brass rings), and the role's gear: a smith's
soot-black goggles and forge hammer, a miner's leather cap with a glowing lamp and a pickaxe, a brewer's green cap and
a foaming tankard, a gemcutter's velvet cap, loupe and chisel, a guard's horned helm, round rune shield and axe.
"""
from ..models import Model
from ..texgen import mix, mul
from . import folkkit as K

ROLES = ["smith", "miner", "brewer", "gemcutter", "guard"]

# role: palette
PAL = {
    "smith": dict(tunic=(150, 56, 40), tunic2=(118, 42, 30), trim=(214, 170, 64), skin=(206, 146, 112),
                  beard=(44, 34, 30), beard_l=(84, 66, 56), apron=(96, 64, 40), boots=(58, 40, 28),
                  belt=(64, 44, 30), buckle=(214, 170, 64), sleeve=(150, 56, 40)),
    "miner": dict(tunic=(70, 86, 110), tunic2=(54, 66, 86), trim=(150, 120, 70), skin=(214, 158, 122),
                  beard=(186, 84, 40), beard_l=(226, 128, 70), apron=(120, 82, 48), boots=(70, 48, 30),
                  belt=(92, 60, 36), buckle=(170, 172, 180), sleeve=(70, 86, 110)),
    "brewer": dict(tunic=(70, 112, 58), tunic2=(54, 88, 44), trim=(220, 196, 120), skin=(222, 162, 130),
                   beard=(204, 120, 52), beard_l=(240, 170, 96), apron=(226, 214, 186), boots=(82, 56, 34),
                   belt=(98, 66, 40), buckle=(196, 150, 70), sleeve=(226, 214, 186)),
    "gemcutter": dict(tunic=(92, 52, 128), tunic2=(70, 38, 100), trim=(222, 184, 80), skin=(200, 144, 116),
                      beard=(222, 220, 214), beard_l=(250, 250, 246), apron=(60, 40, 84), boots=(46, 34, 40),
                      belt=(40, 30, 46), buckle=(120, 220, 230), sleeve=(92, 52, 128)),
    "guard": dict(tunic=(120, 34, 36), tunic2=(92, 24, 28), trim=(214, 170, 64), skin=(208, 150, 116),
                  beard=(226, 186, 92), beard_l=(250, 222, 140), apron=(120, 34, 36), boots=(52, 46, 46),
                  belt=(60, 40, 30), buckle=(214, 170, 64), sleeve=(150, 152, 160)),
}
EYE = (40, 44, 60)
WHITE = (236, 234, 228)
GOLD = (220, 176, 70)
GOLD_D = (150, 104, 38)
IRON = (150, 152, 160)
IRON_D = (84, 86, 96)
SOOT = (30, 28, 30)
LAMP = (255, 214, 120)
LAMP_L = (255, 248, 210)
GEM = (90, 220, 230)


def build(variant=None):
    role = variant or ROLES[0]
    p = PAL[role]
    m = Model("dwarf", seed=301, shadow=0.55, variants=ROLES, walk_speed=1.5, walk_scale=1.0)

    # ------------------------------------------------------------------ skeleton (y up is negative)
    m.part("bone", pivot=(0, 24, 0))
    m.part("leg_r", "bone", pivot=(-2.5, -6, 0))
    m.part("leg_l", "bone", pivot=(2.5, -6, 0))
    m.part("body", "bone", pivot=(0, -6, 0))
    m.part("head", "body", pivot=(0, -10, -0.5))
    m.part("beard", "head", pivot=(0, -1, -4.5))
    m.part("arm_r", "body", pivot=(-6, -9, 0), rot=(0, 0, 8))
    m.part("arm_l", "body", pivot=(6, -9, 0), rot=(0, 0, -8))
    m.part("tool", "arm_r", pivot=(-1.5, 7, -0.5), rot=(-70, 0, 0))
    m.part("off", "arm_l", pivot=(1.5, 7, -0.5))

    tunic = K.cloth(p["tunic"], p["tunic2"], seed=1, trim=p["trim"], trim_rows=(-1,))
    boots = K.leather(p["boots"], seed=2)

    # ------------------------------------------------------------------ legs and big boots
    for leg in ("leg_r", "leg_l"):
        m.box(leg, -2, 0, -2, 4, 4, 4, {"top": p["tunic2"], "*": K.cloth(mul(p["tunic2"], 0.9), mul(p["tunic2"], 0.75), 3)})

        def boot(f_, x, y, w, h, base=boots):
            if f_ == "top":
                return mul(p["boots"], 1.1)
            if y == 0:
                return mix(p["boots"], (230, 210, 180), 0.2)          # folded cuff
            if y == h - 1:
                return mul(p["boots"], 0.55)                          # thick sole
            if f_ == "front" and y == 1 and role == "guard":
                return IRON                                          # steel toe cap
            return base(f_, x, y, w, h)
        m.box(leg, -2.5, 3, -3, 5, 3, 6, boot)

    # ------------------------------------------------------------------ barrel chest, belly, belt and kilt
    def torso(f_, x, y, w, h):
        if role == "guard" and f_ in ("front", "back", "left", "right") and 1 <= y <= 6:
            return K.chainmail(seed=4)(f_, x, y, w, h)
        if f_ == "front" and role in ("smith", "brewer") and 2 <= x <= w - 3 and y >= 2:
            c = p["apron"] if (x + y) % 5 else mul(p["apron"], 0.9)     # leather / linen apron
            if role == "smith" and K.h(x, y, 7) % 9 == 0:
                c = mix(c, SOOT, 0.5)                                    # scorch marks
            return c
        if f_ == "front" and role == "gemcutter" and x == w // 2 and y % 2 == 0:
            return p["trim"]                                             # gold buttons
        if f_ == "front" and role == "miner" and x in (2, w - 3):
            return mul(p["apron"], 0.9)                                  # braces
        return tunic(f_, x, y, w, h)
    m.box("body", -5, -10, -3.5, 10, 9, 7, torso)

    def belly(f_, x, y, w, h):
        if f_ != "front":
            return torso(f_, x, y + 4, w, h + 4)
        return torso(f_, x + 1, y + 6, w + 2, h + 6)
    m.box("body", -4, -6, -4.5, 8, 5, 1, belly)

    def belt(f_, x, y, w, h):
        if f_ == "front" and w // 2 - 1 <= x <= w // 2 + 1:
            return p["buckle"] if y == 0 or x != w // 2 else mul(p["buckle"], 0.7)
        if f_ == "front" and role == "gemcutter" and x == 2:
            return GEM                                                   # a cut gem on the belt
        return p["belt"] if (x + y) % 4 else mul(p["belt"], 1.15)
    m.box("body", -5.5, -2, -5, 11, 2, 9, belt)

    def kilt(f_, x, y, w, h):
        if f_ in ("top", "bottom"):
            return None if f_ == "bottom" else mul(p["tunic2"], 0.9)
        if y == h - 1 and x % 2 == 1:
            return None                                                  # notched hem
        if role == "guard" and f_ in ("front", "back"):
            return K.steel(seed=5)(f_, x, y, w, h) if x % 4 != 0 else IRON_D   # tassets
        return K.cloth(p["tunic2"], mul(p["tunic2"], 0.8), seed=6, trim=p["trim"], trim_rows=(-2,))(f_, x, y, w, h)
    m.box("body", -5.5, 0, -4, 11, 3, 8, kilt)

    # pauldrons (guard: steel; the others: a padded shoulder of the tunic colour)
    for sx in (-1, 1):
        def pauldron(f_, x, y, w, h):
            if role == "guard":
                return K.steel(seed=8)(f_, x, y, w, h)
            if role == "miner":
                return K.leather(p["apron"], seed=9)(f_, x, y, w, h)
            return None
        m.box("body", 4 if sx > 0 else -8, -11, -3.5, 4, 3, 7, pauldron)

    # back: the miner's ore sack, the brewer's little keg (others: none)
    def pack(f_, x, y, w, h):
        if role == "miner":
            c = K.leather((132, 100, 64), seed=10)(f_, x, y, w, h)
            if f_ == "top" and (x + y) % 3 == 0:
                return (90, 220, 230) if (x * 7 + y) % 2 else (200, 120, 60)   # ore peeking out
            return c
        if role == "brewer":
            if f_ in ("front", "back") and y % 3 == 1:
                return IRON_D                                                # keg hoops
            return K.wood((150, 100, 56), (104, 66, 36), seed=11)(f_, x, y, w, h)
        return None
    m.box("body", -3.5, -9, 3.5, 7, 6, 3, pack)

    # ------------------------------------------------------------------ head: wide face, big nose, bushy brows
    def face(f_, x, y, w, h):
        sk = p["skin"]
        if f_ == "top":
            if role == "smith":
                return p["beard"] if K.h(x, y, 12) % 4 else p["beard_l"]   # cropped hair
            return mul(sk, 0.9)
        if f_ == "back":
            return K.hair(p["beard"], 13)(f_, x, y, w, h) if y < 6 else sk
        if f_ in ("left", "right"):
            if y < 3 or (y < 6 and (x >= w - 3 if f_ == "left" else x <= 2)):
                return K.hair(p["beard"], 14)(f_, x, y, w, h)
            if y == 3 and (x == 2 if f_ == "left" else x == w - 3):
                return mul(sk, 0.85)                                      # ear
            return K.skin(sk)(f_, x, y, w, h)
        if f_ == "bottom":
            return mul(sk, 0.8)
        # front
        if y == 0:
            return K.hair(p["beard"], 15)(f_, x, y, w, h)
        if y == 2 and x in (1, 2, 5, 6):
            return mul(p["beard"], 0.9)                                   # bushy brows
        if y == 3 and x in (1, 6):
            return WHITE
        if y == 3 and x in (2, 5):
            return EYE
        if y >= 5 and x in (0, w - 1):
            return K.hair(p["beard"], 15)(f_, x, y, w, h)                 # sideburns into the beard
        return K.skin(sk)(f_, x, y, w, h)
    m.box("head", -4, -7, -4, 8, 7, 8, face)
    m.box("head", -1, -4, -5.5, 2, 3, 2, {"*": mul(p["skin"], 0.96), "top": mul(p["skin"], 1.05),
                                           "front": lambda f_, x, y, w, h: mul(p["skin"], 0.88 if y == 2 else 1.0)})

    # beard: a broad fall from the cheeks to the belt, a moustache, two braids with rings
    def beard(f_, x, y, w, h):
        if f_ == "top":
            return None
        if f_ == "front" and y == 0 and x in (3, 4):
            return None                                                  # the mouth line under the nose
        if y == h - 1 and x in (0, w - 1):
            return None                                                  # a rounded tip
        if f_ == "front" and y == 0 and x in (1, 2, 5, 6):
            return mul(p["beard_l"], 0.95)                               # moustache
        return K.hair(p["beard"], 16, streak=p["beard_l"])(f_, x, y, w, h)
    m.box("beard", -4, 0, -1, 8, 7, 2, beard)
    ring = GOLD if role != "miner" else (180, 120, 70)
    for sx in (-1, 1):
        m.box("beard", 1 if sx > 0 else -3, 7, -1, 2, 3, 1, K.braid(p["beard"], ring, seed=17 + sx))

    # ---- headgear (one set of cubes, painted per role)
    def dome(f_, x, y, w, h):
        if role == "guard":
            if f_ == "front" and x == w // 2:
                return IRON_D
            return K.steel(seed=20)(f_, x, y, w, h)
        if role == "miner":
            return K.leather((112, 78, 44), seed=21)(f_, x, y, w, h)
        if role == "brewer":
            return K.cloth((70, 140, 60), (52, 110, 46), seed=22)(f_, x, y, w, h)
        if role == "gemcutter":
            if f_ == "top" and x == w // 2 and y == w // 2:
                return GOLD
            return K.cloth((70, 38, 100), (54, 28, 80), seed=23)(f_, x, y, w, h)
        return None
    m.box("head", -4.5, -9, -4.5, 9, 2, 9, dome)

    def rim(f_, x, y, w, h):
        if role == "guard":
            return K.steel(seed=24, rivets=False)(f_, x, y, w, h) if (x % 3) else GOLD_D
        if role == "miner":
            return mul((112, 78, 44), 0.8)
        if role == "smith":
            # soot goggles pushed up on the forehead: a strap and two dark lenses
            if f_ in ("top", "bottom"):
                return None
            if f_ == "front" and x in (2, 3, 6, 7):
                return (60, 70, 74) if y == 0 else (30, 34, 36)
            return (70, 52, 36)
        if role == "brewer":
            return mul((70, 140, 60), 0.8) if f_ not in ("top", "bottom") else None
        return None
    m.box("head", -5, -7, -5, 10, 1, 10, rim)

    def nasal(f_, x, y, w, h):
        return K.steel(seed=25, rivets=False)(f_, x, y, w, h) if role == "guard" else None
    m.box("head", -0.5, -7, -5.5, 1, 3, 1, nasal)

    def lamp(f_, x, y, w, h):
        if role != "miner":
            return None
        return (180, 140, 70) if f_ != "front" else LAMP
    m.box("head", -1, -10, -5.5, 2, 2, 2, lamp, glow=K.role_only(role, "miner", {"front": LAMP_L, "*": None}))

    def loupe(f_, x, y, w, h):
        if role != "gemcutter":
            return None
        return GOLD if f_ != "front" else (170, 230, 240)
    m.box("head", 1, -4.5, -5, 2, 2, 1, loupe)

    for side, sx in (("r", -1), ("l", 1)):
        m.part(f"horn_{side}", "head", pivot=(4.5 * sx, -8, 0), rot=(0, 0, 35 * sx))

        def horn(f_, x, y, w, h):
            if role != "guard":
                return None
            return mix((236, 226, 196), (150, 130, 96), y / max(1, h - 1)) if f_ != "top" else (240, 232, 210)
        m.box(f"horn_{side}", 0 if sx > 0 else -2, -5, -1, 2, 5, 2, horn)

    # ------------------------------------------------------------------ arms: sleeves, thick wrists, mitts
    def sleeve(f_, x, y, w, h):
        if f_ == "top":
            return p["sleeve"]
        if y >= h - 2:
            return K.skin(p["skin"])(f_, x, y, w, h)
        if y == h - 3:
            return p["trim"] if role != "guard" else IRON_D
        if role == "guard":
            return K.chainmail(seed=26)(f_, x, y, w, h)
        if role == "brewer":
            return K.cloth(p["sleeve"], mul(p["sleeve"], 0.9), seed=27)(f_, x, y, w, h)
        return K.cloth(p["sleeve"], mul(p["sleeve"], 0.82), seed=27)(f_, x, y, w, h)
    for arm, sx in (("arm_r", -1), ("arm_l", 1)):
        m.box(arm, -1.5, -1, -1.5, 3, 8, 3, sleeve)
        m.box(arm, -1.5, 5, -1.5, 3, 3, 3, K.leather((88, 60, 40), seed=28) if role in ("smith", "guard", "miner")
              else K.skin(p["skin"]), grow=0.3)

    # ------------------------------------------------------------------ the tool in the right hand (along -z)
    haft = K.wood((112, 78, 46), (74, 50, 30), seed=30, vertical=False)
    m.box("tool", -0.5, -0.5, -9, 1, 1, 11,
          K.role_only(role, ("smith", "miner", "guard", "gemcutter"),
                      lambda f_, x, y, w, h: GOLD if role == "gemcutter" and f_ in ("left", "right", "top")
                      and x < 4 else haft(f_, x, y, w, h)))

    def hammer_head(f_, x, y, w, h):
        if role != "smith":
            return None
        if f_ in ("front", "back"):
            return mix(IRON, (255, 240, 200), 0.3) if x in (0, w - 1) or y in (0, h - 1) else IRON_D
        return K.steel(seed=31)(f_, x, y, w, h)
    m.box("tool", -2, -1.5, -11, 4, 3, 3, hammer_head)

    def pick_head(f_, x, y, w, h):
        if role != "miner":
            return None
        if f_ in ("top", "bottom"):
            return IRON
        return mix(IRON, IRON_D, abs(y - (h - 1) / 2) / h * 1.6)
    m.box("tool", -0.5, -6, -10, 1, 12, 2, pick_head)

    def axe_head(f_, x, y, w, h):
        if role != "guard":
            return None
        if f_ in ("left", "right") and x == 0:
            return (230, 232, 238)                                        # the honed edge
        if f_ in ("left", "right") and y == h // 2 and x == w - 1:
            return GOLD                                                   # a gold rivet
        return K.steel(seed=32, rivets=False)(f_, x, y, w, h)
    m.box("tool", -0.5, -5, -10, 1, 6, 4, axe_head)

    def mug(f_, x, y, w, h):
        if role != "brewer":
            return None
        if f_ == "top":
            return WHITE if (x + y) % 3 else (240, 220, 150)              # foam
        if y == 0:
            return WHITE
        if y in (2, h - 2):
            return IRON_D                                                 # hoops
        return K.wood((166, 112, 60), (120, 80, 44), seed=33)(f_, x, y, w, h)
    m.box("tool", -1.5, -2.5, -3, 3, 4, 3, mug)

    # ---- off hand: the guard's round shield (outer face to the creature's left), the gemcutter's gem
    def shield(f_, x, y, w, h):
        if role != "guard":
            return None
        if f_ in ("left", "right"):
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if r > 4.6:
                return None
            if r > 3.7:
                return IRON if (x + y) % 2 else IRON_D                    # iron rim
            if r < 1.3:
                return GOLD                                               # boss
            if f_ == "left" and (abs(x - cx) < 0.6 or abs(y - cy) < 0.6):
                return GOLD_D                                             # rune cross
            return K.wood((130, 40, 36), (100, 30, 28), seed=34)(f_, x, y, w, h)
        cx = (w - 1) / 2
        return IRON_D if abs(x - cx) < 4 else None
    m.box("off", 1.5, -6, -5, 1, 10, 10, shield)

    def gem(f_, x, y, w, h):
        if role != "gemcutter":
            return None
        return GEM if (x + y) % 2 else (200, 250, 255)
    m.box("off", -1, -1, -2.5, 2, 2, 2, gem, glow=K.role_only(role, "gemcutter", {"top": (160, 250, 255), "*": None}))

    # ------------------------------------------------------------------ animations
    idle = m.anim("idle", 3.0)
    idle.rot("body", (0, (0, 0, 0)), (1.5, (1.5, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("head", (0, (0, 0, 0)), (1.5, (-2, 0, 0)), (3.0, (0, 0, 0)))
    idle.rot("beard", (0, (0, 0, 0)), (1.0, (3, 0, 1)), (2.0, (2, 0, -1)), (3.0, (0, 0, 0)))
    idle.rot("arm_r", (0, (0, 0, 0)), (1.5, (-3, 0, 2)), (3.0, (0, 0, 0)))
    idle.rot("arm_l", (0, (0, 0, 0)), (1.5, (-3, 0, -2)), (3.0, (0, 0, 0)))

    walk = m.anim("walk", 0.8)
    walk.rot("leg_r", (0, (32, 0, 0)), (0.4, (-32, 0, 0)), (0.8, (32, 0, 0)))
    walk.rot("leg_l", (0, (-32, 0, 0)), (0.4, (32, 0, 0)), (0.8, (-32, 0, 0)))
    walk.rot("arm_r", (0, (-24, 0, 0)), (0.4, (20, 0, 0)), (0.8, (-24, 0, 0)))
    walk.rot("arm_l", (0, (24, 0, 0)), (0.4, (-24, 0, 0)), (0.8, (24, 0, 0)))
    walk.rot("body", (0, (0, 0, -4)), (0.4, (0, 0, 4)), (0.8, (0, 0, -4)))
    walk.pos("body", (0, (0, 0, 0)), (0.2, (0, 0.6, 0)), (0.4, (0, 0, 0)), (0.6, (0, 0.6, 0)), (0.8, (0, 0, 0)))
    walk.rot("beard", (0, (4, 0, 2)), (0.4, (4, 0, -2)), (0.8, (4, 0, 2)))

    # greet: the free left hand goes up and waves (when a player opens the trade screen)
    a = m.anim("greet", 1.4)
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-160, 0, -10)), (0.55, (-160, 0, -30)), (0.8, (-160, 0, 0)),
          (1.05, (-160, 0, -30)), (1.4, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (-8, 0, 6)), (1.1, (-8, 0, 6)), (1.4, (0, 0, 0)))

    # attack: a two-handed overhead chop, wind-up 0.45 s, the blow lands at 0.55 s (11 ticks)
    a = m.anim("attack", 1.0)
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (-165, 0, 10)), (0.55, (-20, 0, 0), "linear"), (0.7, (-10, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (-60, 0, -20)), (0.55, (-20, 0, 0), "linear"), (1.0, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.45, (-12, 0, 0)), (0.55, (14, 0, 0), "linear"), (0.75, (8, 0, 0)), (1.0, (0, 0, 0)))
    a.rot("beard", (0, (0, 0, 0)), (0.45, (12, 0, 0)), (0.6, (-10, 0, 0)), (1.0, (0, 0, 0)))

    # hammer: two strikes on the anvil (the first rings at 0.35 s)
    a = m.anim("hammer", 1.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-110, 0, 0)), (0.35, (-20, 0, 0), "linear"), (0.6, (-110, 0, 0)),
          (0.7, (-20, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.35, (8, 0, 0)), (0.6, (0, 0, 0)), (0.7, (8, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.3, (-40, 0, -10)), (0.9, (-40, 0, -10)), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.3, (14, 0, 0)), (0.9, (14, 0, 0)), (1.2, (0, 0, 0)))

    # dig: a big swing of the pickaxe into the rock face in front of it
    a = m.anim("dig", 1.2)
    a.rot("arm_r", (0, (0, 0, 0)), (0.45, (-175, 0, 0)), (0.6, (-45, 0, 0), "linear"), (0.8, (-50, 0, 0)), (1.2, (0, 0, 0)))
    a.rot("arm_l", (0, (0, 0, 0)), (0.45, (-140, 0, 20)), (0.6, (-45, 0, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("body", (0, (0, 0, 0)), (0.45, (-10, 0, 0)), (0.6, (12, 0, 0), "linear"), (1.2, (0, 0, 0)))

    # brew: stirs a vat with the tankard hand, a taste, a satisfied nod
    a = m.anim("brew", 1.6)
    a.rot("arm_r", (0, (0, 0, 0)), (0.25, (-55, 20, 0)), (0.5, (-55, -20, 0)), (0.75, (-55, 20, 0)), (1.0, (-55, -20, 0)),
          (1.2, (-120, 0, 10)), (1.4, (-120, 0, 10)), (1.6, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.5, (14, 0, 0)), (1.0, (14, 0, 0)), (1.25, (-16, 0, 0)), (1.45, (6, 0, 0)), (1.6, (0, 0, 0)))

    # carve: small taps of the chisel on the gem held up in the other hand
    a = m.anim("carve", 1.2)
    a.rot("arm_l", (0, (0, 0, 0)), (0.2, (-70, 0, 20)), (1.0, (-70, 0, 20)), (1.2, (0, 0, 0)))
    a.rot("arm_r", (0, (0, 0, 0)), (0.2, (-60, -20, 0)), (0.35, (-48, -20, 0), "linear"), (0.5, (-62, -20, 0)),
          (0.65, (-48, -20, 0), "linear"), (0.8, (-62, -20, 0)), (0.95, (-48, -20, 0), "linear"), (1.2, (0, 0, 0)))
    a.rot("head", (0, (0, 0, 0)), (0.2, (18, 0, 0)), (1.0, (18, 0, 0)), (1.2, (0, 0, 0)))
    return m

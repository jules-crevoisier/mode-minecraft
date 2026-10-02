"""Hand-designed 64x64 humanoid skins (zombie model UV layout; left limbs mirror the right ones).

Each skin is painted part by part (head, hat layer, body, arms, legs) with shading so the mobs
look like proper characters rather than noise.
"""
import random

from .png import Canvas
from .texgen import mix, mul

# UV boxes: name -> (u, v, w, h, d)  (standard cube unwrap)
BOXES = {
    "head": (0, 0, 8, 8, 8), "hat": (32, 0, 8, 8, 8),
    "body": (16, 16, 8, 12, 4), "arm": (40, 16, 4, 12, 4), "leg": (0, 16, 4, 12, 4),
}


def faces(box):
    u, v, w, h, d = BOXES[box]
    return {
        "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h), "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h), "back": (u + d + w + d, v + d, w, h),
    }


class Skin:
    def __init__(self, seed):
        self.cv = Canvas(64, 64)
        self.rng = random.Random(seed)

    def paint(self, box, color, var=0.07, shade_sides=True, face_filter=None):
        for name, (x0, y0, w, h) in faces(box).items():
            if face_filter and name not in face_filter:
                continue
            f = {"top": 1.1, "bottom": 0.7, "front": 1.0, "back": 0.85, "left": 0.9, "right": 0.9}[name] \
                if shade_sides else 1.0
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    c = color(x - x0, y - y0, w, h, name) if callable(color) else color
                    if c is None:
                        continue
                    self.cv.set(x, y, mul(c, f * (1 + self.rng.uniform(-var, var))))

    def rows(self, box, bands, faces_=None):
        """Horizontal bands on the side faces: list of (rows, color) from top."""
        def color(x, y, w, h, face):
            if face in ("top", "bottom"):
                return bands[0][1] if face == "top" else bands[-1][1]
            acc = 0
            for n, c in bands:
                acc += n
                if y < acc:
                    return c
            return bands[-1][1]
        self.paint(box, color, face_filter=faces_)

    def front_px(self, box, x, y, color, face="front"):
        fx, fy, w, h = faces(box)[face]
        self.cv.set(fx + x, fy + y, color)


def face(s, eye, pupil=None, mouth=None, brow=None, eye_y=4):
    """Two-pixel eyes on the head front, optional brow and mouth."""
    for ex in (1, 5):
        s.front_px("head", ex, eye_y, eye)
        s.front_px("head", ex + 1, eye_y, pupil or eye)
        if brow:
            s.front_px("head", ex, eye_y - 1, brow)
            s.front_px("head", ex + 1, eye_y - 1, brow)
    if mouth:
        for mx in range(2, 6):
            s.front_px("head", mx, eye_y + 2, mouth)


def ruin_walker():
    """Moss-grown stone sentinel: stone skin, moss patches, glowing green eyes, rusty armour."""
    s = Skin(1)
    stone, moss = (128, 128, 120), (86, 116, 54)

    def mossy(x, y, w, h, f):
        return moss if (x * 7 + y * 3) % 11 < 3 or (f == "top") else mix(stone, (110, 108, 100), (x + y) % 3 / 3)
    s.paint("head", mossy)
    face(s, (170, 255, 120), (230, 255, 200), mouth=(60, 60, 56), brow=(90, 90, 86))
    s.paint("hat", lambda x, y, w, h, f: moss if f == "top" or (f != "bottom" and y < 2 and x % 3) else None)
    s.rows("body", [(2, (110, 84, 60)), (7, (120, 100, 70)), (1, (60, 46, 34)), (2, (96, 80, 58))])
    s.paint("body", lambda x, y, w, h, f: (150, 118, 70) if f == "front" and x in (3, 4) and 2 <= y <= 8 else None)
    s.rows("arm", [(4, (110, 84, 60)), (6, stone), (2, moss)])
    s.rows("leg", [(6, (96, 80, 58)), (3, stone), (3, (70, 64, 58))])
    return s.cv


def map_wraith():
    """Paper ghost wrapped in old maps: parchment body with ink lines, hollow black eyes."""
    s = Skin(2)
    paper, ink = (228, 214, 172), (70, 56, 40)

    def parchment(x, y, w, h, f):
        if (y % 4 == 1 and x % 5 != 0) or ((x + y * 2) % 13 == 0):
            return mix(paper, ink, 0.55)
        return mix(paper, (200, 180, 130), ((x * 3 + y) % 5) / 8)
    for b in ("head", "body", "arm", "leg"):
        s.paint(b, parchment)
    face(s, (10, 8, 6), (10, 8, 6), mouth=(40, 30, 20))
    s.paint("hat", lambda x, y, w, h, f: (196, 176, 128) if f in ("top", "back") or (f != "bottom" and y < 3) else None)
    s.paint("body", lambda x, y, w, h, f: (170, 40, 30) if f == "front" and (x - 3) ** 2 + (y - 5) ** 2 <= 2 else None)
    return s.cv


def basalt_guard():
    """Fortress guard in basalt plate armour with glowing ember seams and a horned helm."""
    s = Skin(3)
    plate, dark, ember = (62, 60, 66), (30, 28, 34), (255, 132, 40)

    def armour(x, y, w, h, f):
        if f in ("front", "back") and (y == 3 or y == 8):
            return ember if x % 3 else mul(ember, 0.7)
        return mix(plate, dark, ((x + y) % 4) / 6)
    s.paint("head", lambda x, y, w, h, f: dark)
    s.paint("hat", armour)
    for ex in (1, 5):
        s.front_px("hat", ex, 4, ember)
        s.front_px("hat", ex + 1, 4, (255, 210, 120))
    s.paint("hat", lambda x, y, w, h, f: (20, 18, 22) if f == "front" and y == 4 and x in (0, 3, 4, 7) else None)
    s.paint("body", armour)
    s.rows("arm", [(3, (90, 86, 94)), (7, plate), (2, ember)])
    s.rows("leg", [(5, plate), (1, ember), (6, dark)])
    return s.cv


def void_stalker():
    """Lanky hunter of the End: deep violet skin speckled with stars, burning magenta eyes."""
    s = Skin(4)
    void = (38, 20, 56)

    def starry(x, y, w, h, f):
        r = (x * 31 + y * 17 + hash(f)) % 23
        return (230, 200, 255) if r == 0 else (150, 100, 220) if r == 1 else mix(void, (60, 30, 90), ((x + y) % 3) / 4)
    for b in ("head", "body", "arm", "leg"):
        s.paint(b, starry)
    face(s, (255, 120, 255), (255, 230, 255))
    s.paint("hat", lambda x, y, w, h, f: (24, 12, 36) if f in ("top", "back", "left", "right") and y < 5 else None)
    return s.cv


def drowned_warden():
    """Giant drowned king: teal skin, kelp robes, barnacles, golden crown and trident sash."""
    s = Skin(5)
    skin, kelp, gold = (70, 150, 140), (40, 96, 50), (240, 200, 70)
    s.paint("head", lambda x, y, w, h, f: mix(skin, (50, 120, 112), (x * y % 4) / 5))
    face(s, (170, 255, 240), (255, 255, 255), mouth=(30, 70, 66), brow=(40, 90, 84))
    s.paint("hat", lambda x, y, w, h, f: gold if f != "bottom" and y < 2 and (f != "top") else
            (255, 120, 120) if f == "front" and y == 2 and x in (3, 4) else None)

    def robe(x, y, w, h, f):
        if f == "front" and x == y % w:
            return gold
        return mix(kelp, (30, 70, 40), ((x * 5 + y) % 7) / 8) if (x + y) % 6 else (200, 200, 190)
    s.paint("body", robe)
    s.rows("arm", [(4, kelp), (6, skin), (2, (50, 120, 112))])
    s.rows("leg", [(8, kelp), (4, skin)])
    return s.cv


def void_warden():
    """End mini-boss: obsidian armour with violet glow, horned helm, starlight core."""
    s = Skin(6)
    obs, glow = (24, 14, 36), (230, 110, 255)

    def armour(x, y, w, h, f):
        if (x + 2 * y) % 7 == 0:
            return mix(obs, glow, 0.45)
        return mix(obs, (40, 24, 60), ((x * y) % 3) / 3)
    for b in ("head", "body", "arm", "leg"):
        s.paint(b, armour)
    s.paint("body", lambda x, y, w, h, f: (255, 230, 255) if f == "front" and x in (3, 4) and y in (4, 5) else
            glow if f == "front" and abs(x - 3.5) <= 1.5 and 3 <= y <= 6 else None)
    face(s, glow, (255, 220, 255))
    s.paint("hat", lambda x, y, w, h, f: (12, 6, 20) if f != "bottom" and (y < 3 or f == "top") else None)
    for hx in (0, 7):
        s.front_px("hat", hx, 0, glow)
        s.front_px("hat", hx, 1, glow)
    return s.cv


SKINS = {
    "ruin_walker": ruin_walker, "map_wraith": map_wraith, "basalt_guard": basalt_guard,
    "void_stalker": void_stalker, "drowned_warden": drowned_warden, "void_warden": void_warden,
}


def front_view(cv, scale=8):
    """Composite front view (head, body, arms, legs) for previewing a skin."""
    out = Canvas(16 * scale, 32 * scale, (30, 32, 40, 255))

    def blit(face_rect, ox, oy, mirror=False):
        x0, y0, w, h = face_rect
        for y in range(h):
            for x in range(w):
                sx = x0 + (w - 1 - x if mirror else x)
                p = cv.get(sx, y0 + y)
                if p[3]:
                    out.rect((ox + x) * scale, (oy + y) * scale, (ox + x + 1) * scale - 1, (oy + y + 1) * scale - 1, p)
    blit(faces("head")["front"], 4, 0)
    blit(faces("hat")["front"], 4, 0)
    blit(faces("body")["front"], 4, 8)
    blit(faces("arm")["front"], 0, 8)
    blit(faces("arm")["front"], 12, 8, mirror=True)
    blit(faces("leg")["front"], 4, 20)
    blit(faces("leg")["front"], 8, 20, mirror=True)
    return out

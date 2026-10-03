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


SKINS = {}


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

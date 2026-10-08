"""Plating, tread plate, shingles and machine tops for wf/blocktex.py: each metal gets its own construction instead
of one riveted-plate mask recoloured (brass lapped courses, copper pillowed 2x2 sheets, verdigris the same sheets
weathered, dark iron a strapped boiler plate, steel tread with diagonal lentils, copper fish-scale shingles).
Light from the top-left, 6-tone hue-shifted ramps, no per-pixel speckle."""
import math

from .png import Canvas
from . import texkit as K

BRASS = (200, 156, 66)
COPPER = (196, 108, 72)
VERDIGRIS = (78, 166, 140)
DARK_IRON = (70, 66, 72)
STEEL = (122, 128, 138)


def ramp(mid, lo=-0.76, hi=0.72):
    return K.ramp(mid, 6, lo, hi)


def fill(c):
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, c)
    return cv


def rivet(cv, x, y, r, shadow=None):
    """1px domed rivet: bright cap, its shadow below-right."""
    cv.set(x, y, r[5])
    cv.set(x + 1, y + 1, shadow if shadow else r[0])
    cv.set(x + 1, y, r[2])
    cv.set(x, y + 1, r[2])


def brass_plating():
    """Lapped brass courses: each plate catches light along its top edge, darkens toward the lap shadow under the
    plate above; butt seams staggered like brickwork, a rivet line along every top band."""
    r = ramp(BRASS, hi=0.84)
    cv = fill(r[3])
    for course, seam in ((0, 11), (8, 4)):
        for dy, t in enumerate((5, 4, 3, 3, 3, 3, 2, 0)):
            for x in range(16):
                cv.set(x, course + dy, r[t])
        for dy in range(7):
            cv.set(seam, course + dy, r[0] if dy else r[1])
            cv.set((seam + 1) % 16, course + dy, r[4] if dy else r[5])
        for x in range(1, 16, 4):
            if abs(x - seam) > 1 and abs(x - seam - 16) > 1:
                rivet(cv, x, course + 2, r)
    # a polished glint where the light hits the top course
    for x, y in ((6, 1), (7, 1), (14, 9)):
        cv.set(x, y, K.mix(r[5], (255, 250, 230), 0.5))
    return cv


def _sheets(r, patina=None):
    """Four pillowed 8x8 sheets: lit top-left rim, shaded bottom-right rim, a diagonal sheen across the face and a
    rivet at each sheet's corners."""
    cv = fill(r[3])
    for oy in (0, 8):
        for ox in (0, 8):
            for y in range(8):
                for x in range(8):
                    if x == 0 or y == 0:
                        t = 5 if (x == 0) != (y == 0) or (x, y) == (0, 0) else 4
                    elif x == 7 or y == 7:
                        t = 0 if x == 7 and y == 7 else 1
                    elif x == 1 or y == 1:
                        t = 4
                    elif x == 6 or y == 6:
                        t = 2
                    else:
                        t = 3
                    if 1 < x < 7 and 1 < y < 7 and (x + y) in (7, 8):  # diagonal sheen
                        t = 4
                    cv.set(ox + x, oy + y, r[t])
            for rx, ry in ((1, 1), (5, 1)):
                cv.set(ox + rx, oy + ry, r[5])
                cv.set(ox + rx + 1, oy + ry + 1, r[1])
    if patina:
        g = ramp(patina, -0.6, 0.6)
        for y in range(16):
            for x in range(16):
                c = cv.get(x, y)[:3]
                t = r.index(c) if c in r else 3
                # verdigris collects in the seams and runs down below each rivet; raised faces keep some copper
                sx, sy = x % 8, y % 8
                seam = sx in (0, 7) or sy in (0, 7)
                drip = (sx in (1, 5) and sy in (3, 4, 5)) or (sx in (2, 6) and sy in (5, 6))
                bare = t == 5 and not seam and sx + sy < 5  # rubbed bright copper on the top-left rims
                if not bare:
                    cv.set(x, y, g[min(5, max(0, t - (1 if seam or drip else 0)))])
    return cv


def copper_plating():
    return _sheets(ramp(COPPER, hi=0.74))


def verdigris_plating():
    return _sheets(ramp(COPPER, hi=0.74), patina=VERDIGRIS)


def dark_iron_plating():
    """Strapped boiler plate: four dark hammered panels held by a raised cross of iron straps, rivets down each
    strap, a bolt boss at the crossing."""
    r = ramp(DARK_IRON, -0.7, 0.7)
    cv = fill(r[2])
    for y in range(16):
        for x in range(16):
            px, py = x % 8, y % 8
            # each panel slightly domed: lighter toward its top-left quarter
            cv.set(x, y, r[3] if px + py < 6 else r[2] if px + py < 11 else r[1])
    strap = set()
    for i in range(16):
        for k in (6, 7, 8, 9):
            strap.add((k, i))
            strap.add((i, k))
    for (x, y) in strap:
        tl = (x, y - 1) not in strap or (x - 1, y) not in strap
        br = (x, y + 1) not in strap or (x + 1, y) not in strap
        cv.set(x, y, r[4] if tl and not br else r[1] if br and not tl else r[3])
    for (x, y) in strap:
        for q in ((x + 1, y), (x, y + 1)):
            if q not in strap and 0 <= q[0] < 16 and 0 <= q[1] < 16:
                cv.set(q[0], q[1], r[0])
    for i in (1, 12):  # rivets down/across the straps
        rivet(cv, 7, i + 1, r)
        rivet(cv, i + 1, 7, r)
    for x, y in ((6, 6), (7, 6), (8, 6), (6, 7), (6, 8)):  # boss at the crossing
        cv.set(x, y, r[5])
    for x, y in ((9, 7), (9, 8), (9, 9), (7, 9), (8, 9)):
        cv.set(x, y, r[0])
    cv.set(7, 7, r[4])
    cv.set(8, 8, r[2])
    cv.set(8, 7, r[3])
    cv.set(7, 8, r[3])
    return cv


def diamond_plate():
    """Steel tread plate: raised 2px diagonal lentils, alternating direction on a 4px grid, each with a lit end and
    a shadow under it."""
    r = ramp(STEEL, -0.72, 0.7)
    cv = fill(r[2])
    for j in range(4):
        for i in range(4):
            ox, oy = i * 4 + 1, j * 4 + 1
            if (i + j) % 2 == 0:  # "/"
                cv.set(ox + 1, oy, r[5])
                cv.set(ox, oy + 1, r[4])
                cv.set(ox + 1, oy + 1, r[1])
                cv.set(ox + 2, oy, r[1])
                cv.set(ox, oy + 2, r[1])
            else:  # "\"
                cv.set(ox, oy, r[5])
                cv.set(ox + 1, oy + 1, r[4])
                cv.set(ox + 1, oy, r[3])
                cv.set(ox + 2, oy + 1, r[1])
                cv.set(ox + 1, oy + 2, r[0])
    return cv

SCALE = ["54444331", "43333221", ".322221.", "..1111.."]


def copper_tiles():
    """Copper fish-scale shingles: rows of rounded scales lit on their upper-left, a dark rim below, each row offset
    by half a scale and laid over the one below it."""
    r = ramp(COPPER, hi=0.74)
    cv = fill(r[0])
    for j in range(4, -1, -1):
        y0 = j * 4 - 1
        off = 4 if j % 2 else 0
        for i in range(-1, 3):
            for y, row in enumerate(SCALE):
                for x, ch in enumerate(row):
                    if ch != ".":
                        cv.set((i * 8 + off + x) % 16, (y0 + y) % 16, r[int(ch)])
    return cv

def _iron_top(r):
    """Dark-iron cap plate with bevel and four corner bolts: the shared start for machine and decor tops."""
    cv = fill(r[2])
    for i in range(16):
        cv.set(i, 0, r[4])
        cv.set(0, i, r[4])
        cv.set(i, 15, r[0])
        cv.set(15, i, r[0])
    for i in range(1, 15):
        cv.set(i, 1, r[3])
        cv.set(1, i, r[3])
        cv.set(i, 14, r[1])
        cv.set(14, i, r[1])
    for x, y in ((2, 2), (12, 2), (2, 12), (12, 12)):
        rivet(cv, x, y, r)
    return cv


def machine_top():
    """Machine top: a round fan vent behind a cross brace."""
    r = ramp(DARK_IRON, -0.7, 0.7)
    cv = _iron_top(r)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if d <= 5.4:
                if d > 4.5:
                    cv.set(x, y, r[0] if x + y < 16 else r[4])  # sunk rim: shadow top-left, lit lip bottom-right
                else:
                    cv.set(x, y, r[0] if (x + y) % 3 == 0 else r[1])  # slotted grille
    for i in range(4, 12):  # brace
        cv.set(i, 7, r[4])
        cv.set(i, 8, r[1])
    cv.set(7, 7, r[5])
    cv.set(8, 7, r[5])
    return cv


def gear_panel_top():
    """Clockwork panel top: a square bearing housing with the arbor sticking up through it."""
    r = ramp(DARK_IRON, -0.7, 0.7)
    b = ramp(BRASS, -0.7, 0.84)
    cv = _iron_top(r)
    for y in range(4, 12):
        for x in range(4, 12):
            edge_tl = x == 4 or y == 4
            edge_br = x == 11 or y == 11
            cv.set(x, y, b[5] if edge_tl and not edge_br else b[1] if edge_br else b[3])
    for x in range(12):
        pass
    for y in range(6, 10):
        for x in range(6, 10):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            cv.set(x, y, b[0] if d > 1.6 else b[4] if x + y < 16 else b[2])
    cv.set(12, 12, r[5])
    return cv


def copper_pipes_top():
    """Copper pipes seen end-on: four pipe mouths, each a lit ring round a dark bore."""
    r = ramp(DARK_IRON, -0.7, 0.7)
    c = ramp(COPPER, hi=0.74)
    cv = _iron_top(r)
    for cx, cy in ((5, 5), (11, 5), (5, 11), (11, 11)):
        for y in range(cy - 3, cy + 3):
            for x in range(cx - 3, cx + 3):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= 2.9:
                    k = (x + 0.5 - cx) + (y + 0.5 - cy)
                    if d > 1.6:
                        cv.set(x, y, c[5] if k < -1.5 else c[4] if k < 0 else c[2] if k < 1.5 else c[1])
                    else:
                        cv.set(x, y, c[0] if k < 0.5 else (40, 22, 18))
    return cv


def pressure_gauge_top():
    """Pressure gauge top: a red spoked valve wheel on a dark iron cap."""
    r = ramp(DARK_IRON, -0.7, 0.7)
    red = ramp((178, 40, 34), -0.6, 0.62)
    cv = _iron_top(r)
    ring = set()
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if 3.6 <= d <= 5.0:
                ring.add((x, y))
    spokes = {(8, y) for y in range(4, 12)} | {(x, 8) for x in range(4, 12)} | {(7, 7), (8, 7), (7, 8)}
    wheel = ring | spokes
    for (x, y) in wheel:
        if (x + 1, y + 1) not in wheel:
            cv.set(x + 1, y + 1, r[0])
    for (x, y) in wheel:
        tl = (x, y - 1) not in wheel or (x - 1, y) not in wheel
        br = (x, y + 1) not in wheel or (x + 1, y) not in wheel
        cv.set(x, y, red[5] if tl and not br else red[1] if br and not tl else red[3])
    for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):  # hub nut
        cv.set(x, y, (200, 200, 206) if (x, y) == (7, 7) else (120, 120, 128) if (x, y) != (8, 8) else (60, 58, 66))
    return cv


FACES = {
    "brass_plating": brass_plating, "copper_plating": copper_plating, "verdigris_plating": verdigris_plating,
    "dark_iron_plating": dark_iron_plating, "diamond_plate": diamond_plate, "copper_tiles": copper_tiles,
    "machine_top": machine_top, "gear_panel_top": gear_panel_top, "copper_pipes_top": copper_pipes_top,
    "pressure_gauge_top": pressure_gauge_top,
}

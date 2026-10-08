"""Textures of the chisel-only decor variants (tools/wf/chisel.py): tiles, engraved brass, grilles, carved bricks,
iron bricks, sooty bricks and parquet. Same 16x16 shaded style as texgen / texgen_steam."""
import math
import random

from .png import Canvas
from .texgen import bricks, mix
from .texkit import tmul as mul  # hue-shifted shading
from .texgen_steam import _base, _bevel, _rivet, soot_bricks


def tiles(base, seed=0, size=8, grout=None, var=0.07):
    """Square tiles with a light top-left and dark bottom-right bevel; grout lines between them."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    grout = grout or mul(base, 0.55)
    for ty in range(0, 16, size):
        for tx in range(0, 16, size):
            tint = 1 + rng.uniform(-var, var)
            for y in range(ty, ty + size):
                for x in range(tx, tx + size):
                    lx, ly = x - tx, y - ty
                    if lx == size - 1 or ly == size - 1:
                        cv.set(x, y, mul(grout, 1 + rng.uniform(-0.04, 0.04)))
                        continue
                    f = tint * (1 + rng.uniform(-0.03, 0.03))
                    if lx == 0 or ly == 0:
                        f *= 1.18
                    elif lx == size - 2 or ly == size - 2:
                        f *= 0.84
                    elif (lx + ly) == size // 2:
                        f *= 1.07  # a faint polished glint across each tile
                    cv.set(x, y, mul(base, f))
    return cv


def engraved(base, seed=0):
    """Polished plate with an engraved filigree: a border line and four scrolls around a central diamond."""
    cv = _base(base, seed, 0.03)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(cv.get(x, y), 1.1 - 0.16 * (x + y) / 30))
    _bevel(cv, base, 1.25, 0.7)
    groove, lit = mul(base, 0.55), mul(base, 1.35)
    for i in range(2, 14):
        for (x, y) in ((i, 2), (i, 13), (2, i), (13, i)):
            cv.set(x, y, groove)
    for i in range(3, 13):
        cv.set(i, 3, lit)
        cv.set(3, i, lit)
    # central diamond
    for i in range(4):
        for (x, y) in ((8 + i, 4 + i), (8 - i - 1, 4 + i), (8 + i, 11 - i), (8 - i - 1, 11 - i)):
            cv.set(x, y, groove)
    cv.set(7, 7, lit)
    cv.set(8, 8, lit)
    # little scrolls in the corners
    for cx, cy, sx, sy in ((5, 5, 1, 1), (10, 5, -1, 1), (5, 10, 1, -1), (10, 10, -1, -1)):
        for a in range(0, 300, 30):
            r = 1.4 - a / 400
            x = cx + round(r * math.cos(math.radians(a)) * sx)
            y = cy + round(r * math.sin(math.radians(a)) * sy)
            cv.set(x, y, groove)
    return cv


def grille(frame_c, back, seed=0):
    """A riveted frame with round vertical bars in front of a dark vent (a solid block)."""
    cv = _base(back, seed, 0.05)
    for x in range(1, 15):
        if x % 3 == 2:
            for y in range(2, 14):
                for dx, f in ((0, 1.25), (1, 0.85)):
                    cv.set(x + dx, y, mul(frame_c, f))
    for i in range(16):
        for d in (0, 1):
            cv.set(i, d, mul(frame_c, 1.2 if d == 0 else 0.95))
            cv.set(i, 15 - d, mul(frame_c, 0.7 if d == 0 else 0.9))
            cv.set(d, i, mul(frame_c, 1.2 if d == 0 else 0.95))
            cv.set(15 - d, i, mul(frame_c, 0.7 if d == 0 else 0.9))
    for x, y in ((1, 1), (13, 1), (1, 13), (13, 13)):
        _rivet(cv, x, y, frame_c)
    return cv


def carved_bricks(base, mortar, motif, glow=None, seed=0):
    """A chiseled panel: two framed bands of brick with a carved motif in the middle band.
    motif: 'crystal' (lithite), 'flame' (ember) or 'star' (void); glow lights the carving."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(base, 1 + rng.uniform(-0.05, 0.05)))
    for x in range(16):
        for y in (0, 3, 12, 15):
            cv.set(x, y, mortar)
        cv.set(x, 1, mul(base, 1.15))
        cv.set(x, 13, mul(base, 1.15))
        cv.set(x, 11, mul(base, 0.75))
        cv.set(x, 4, mul(base, 1.15))
    for y in (1, 2, 13, 14):
        for x in (0, 8):
            cv.set(x, y, mortar)
    for y in range(4, 12):
        cv.set(0, y, mul(base, 1.15))
        cv.set(15, y, mul(base, 0.75))
    shapes = {
        "crystal": ["...#...", "..###..", ".##.##.", "##...##", ".##.##.", "..###..", "...#..."],
        "flame": ["...#...", "..##...", "..###..", ".####..", ".#####.", ".##.##.", "..###.."],
        "star": ["...#...", "...#...", ".#.#.#.", "#######", ".#.#.#.", "...#...", "...#..."],
    }
    carve = mul(base, 0.5)
    light = glow or mul(base, 1.4)
    for dy, row in enumerate(shapes[motif]):
        for dx, ch in enumerate(row):
            if ch == "#":
                x, y = 4 + dx, 4 + dy
                cv.set(x, y, light)
                if 0 <= x + 1 < 16 and shapes[motif][dy][dx + 1:dx + 2] != "#":
                    cv.set(x + 1, y, carve)
    return cv


def iron_bricks(base, seed=0):
    """Large dark iron blocks (two rows) with a rivet in each corner."""
    cv = bricks(base, mul(base, 0.45), seed=seed, rows=2, brick_w=8, var=0.08, bevel=0.2, grain=0.04)
    for r in range(2):
        off = 0 if r % 2 == 0 else 4
        for bx in range(-8, 24, 8):
            for (x, y) in ((bx + off + 1, r * 8 + 1), (bx + off + 5, r * 8 + 5)):
                if 0 <= x < 15 and 0 <= y < 15:
                    _rivet(cv, x, y, base)
    return cv


def sooty_bricks(base, mortar, seed=0):
    """Smokestack bricks blackened by years of soot, with streaks running down."""
    cv = soot_bricks(base, mortar, seed=seed)
    rng = random.Random(seed + 7)
    for _ in range(6):
        x = rng.randrange(16)
        for y in range(rng.randrange(4), 16):
            cv.set(x, y, mix(cv.get(x, y), (26, 22, 22), 0.45 + rng.uniform(0, 0.25)))
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mix(cv.get(x, y), (40, 34, 32), 0.12 + 0.18 * (1 - y / 15)))
    return cv


def parquet(base, seed=0):
    """Basket-weave parquet: 4x4 cells of two boards each, alternating horizontal and vertical."""
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    tints = [0.92 + rng.uniform(0, 0.16) for _ in range(32)]
    for y in range(16):
        for x in range(16):
            cx, cy = x // 4, y // 4
            horizontal = (cx + cy) % 2 == 0
            along, across = (x % 4, y % 4) if horizontal else (y % 4, x % 4)
            board = (cy * 4 + cx) * 2 + across // 2
            f = tints[board] + 0.05 * math.sin((x if horizontal else y) * 1.9 + board) + rng.uniform(-0.02, 0.02)
            if across % 2 == 1:
                f *= 0.66  # gap between the two boards / cells
            elif across % 2 == 0 and along == 0:
                f *= 1.12
            cv.set(x, y, mul(base, f))
    return cv


# ---------------------------------------------------------------- the Chisel Table block
def chisel_table():
    """{texture: canvas} for the Chisel Table: a mahogany bench with brass fittings, a stone block on the top being
    carved, and a drawer with a tool rack in front."""
    from .texgen_steam import BRASS, DARK_IRON, MAHOGANY, planks_panel
    stone = (150, 150, 156)
    steel = (214, 214, 222)
    # top: plank surface, brass rim, a stone block between vice jaws, a chisel lying across a corner
    top = Canvas(16, 16)
    rng = random.Random(80)
    for y in range(16):
        for x in range(16):
            board = y // 4
            f = 1.2 + 0.05 * math.sin(x * 0.8 + board * 2) + rng.uniform(-0.03, 0.03) - (0.3 if y % 4 == 3 else 0)
            top.set(x, y, mul(MAHOGANY, f))
    for i in range(16):
        top.set(i, 0, mul(BRASS, 1.25))
        top.set(0, i, mul(BRASS, 1.25))
        top.set(i, 15, mul(BRASS, 0.75))
        top.set(15, i, mul(BRASS, 0.75))
    for y in range(4, 10):
        for x in range(3, 10):
            f = 1.15 if x == 3 or y == 4 else 0.72 if x == 9 or y == 9 else 1 + rng.uniform(-0.05, 0.05)
            top.set(x, y, mul(stone, f))
    for (x, y) in ((5, 6), (6, 6), (5, 7), (7, 8)):  # fresh carving marks
        top.set(x, y, mul(stone, 0.6))
    for x in range(2, 11):  # vice jaws
        top.set(x, 3, mul(DARK_IRON, 1.7))
        top.set(x, 10, mul(DARK_IRON, 1.7))
    for i in range(6):  # the chisel: grip, brass ferrule, steel blade
        c = mul(MAHOGANY, 0.75) if i < 2 else mul(BRASS, 1.15) if i < 3 else steel
        top.set(9 + i, 14 - i, c)
        top.set(10 + i, 14 - i, mul(c, 0.7))
    # side: mahogany panels, brass top rim and corner brackets, dark iron foot rail
    side = planks_panel(MAHOGANY, seed=81)
    for i in range(16):
        side.set(i, 0, mul(BRASS, 1.25))
        side.set(i, 1, mul(BRASS, 0.85))
        side.set(i, 13, mul(DARK_IRON, 1.6))
        side.set(i, 14, mul(DARK_IRON, 1.25))
        side.set(i, 15, mul(DARK_IRON, 0.9))
    for (x, y) in ((0, 2), (1, 2), (0, 3), (14, 2), (15, 2), (15, 3), (0, 12), (15, 12)):
        side.set(x, y, mul(BRASS, 1.1))
    # front: the same bench with a drawer (brass pull) and a rack holding three chisels
    front = planks_panel(MAHOGANY, seed=82)
    for x in range(16):
        for y in (0, 1, 13, 14, 15):
            front.set(x, y, side.get(x, y))
    for x in range(2, 14):
        front.set(x, 8, mul(MAHOGANY, 0.5))
        front.set(x, 12, mul(MAHOGANY, 0.5))
        for y in range(9, 12):
            front.set(x, y, mul(MAHOGANY, 1.15 if y == 9 else 1.0))
    for y in range(8, 13):
        front.set(2, y, mul(MAHOGANY, 0.5))
        front.set(13, y, mul(MAHOGANY, 0.5))
    for x in range(6, 10):
        front.set(x, 10, mul(BRASS, 1.3 if x in (6, 9) else 0.95))
    for x in range(2, 14):
        front.set(x, 6, mul(DARK_IRON, 1.5))
    for cx in (4, 7, 10):  # rack: blades up, ferrules, grips resting on the iron bar
        front.set(cx, 2, steel)
        front.set(cx + 1, 2, mul(steel, 0.8))
        front.set(cx, 3, mul(steel, 0.9))
        front.set(cx, 4, mul(BRASS, 1.15))
        front.set(cx, 5, mul(MAHOGANY, 1.45))
        front.set(cx + 1, 3, mul(MAHOGANY, 0.6))
    return {"chisel_table_top": top, "chisel_table_side": side, "chisel_table_front": front}

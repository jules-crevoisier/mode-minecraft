"""Procedural underground dungeons, assembled in Python so every layout is guaranteed to connect.

A dungeon is a grid of cells (CELL x CELL blocks) on several levels below a surface entrance:

  * level 0 starts under the entrance (a spiral stair from the surface),
  * each level is a random spanning tree of corridors and rooms (with a few loops), its farthest cell
    holds the spiral stair down to the next level,
  * the deepest level reserves a 2x2-cell boss arena (boss seal + mist) with a reward vault behind it,
    and a "site of grace" (waystone) in front of its door,
  * rooms: halls, ossuaries, crypts, shrines, spawner rooms, treasure rooms, arrow-trap corridors and a
    secret chamber behind cracked bricks.

Several seeds per dungeon give several layouts (template variants), so two dungeons rarely look the same.
Everything is drawn in two passes (shells, then interiors) so neighbouring cells never cut each other.
"""
import math
import random
from collections import deque

from . import nbt
from .blueprint import with_props

CELL = 13          # cell footprint (walls included)
LEVEL_H = 14       # vertical distance between level floors
TOP = -12          # floor of level 0 (blueprint y, the surface is y=0)
DIRS = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}
OPP = {"n": "s", "s": "n", "w": "e", "e": "w"}


class Theme:
    """Blocks and dressing of one dungeon family."""

    def __init__(self, name, wall, floor, trim, pillar, ceiling, cracked, accent, light, candle,
                 bones="bone_block", skull="skeleton_skull", spawners=(), loot="", treasure="", reward="",
                 water=None, banner="black"):
        self.name = name
        self.wall = wall          # list of wall blocks (weighted by repetition)
        self.floor = floor
        self.trim = trim          # stairs/slab-capable trim base, e.g. "deepslate_brick"
        self.pillar = pillar
        self.ceiling = ceiling
        self.cracked = cracked    # breakable block hiding the secret room
        self.accent = accent
        self.light = light        # "lantern" | "soul_lantern" | block id of a light source
        self.candle = candle
        self.bones = bones
        self.skull = skull
        self.spawners = spawners
        self.loot = loot
        self.treasure = treasure
        self.reward = reward
        self.water = water
        self.banner = banner

    def pick(self, rng, palette):
        return rng.choice(palette)


# ------------------------------------------------------------------ layout
class Level:
    def __init__(self, k, gw, gd):
        self.k = k
        self.gw, self.gd = gw, gd
        self.links = {}           # cell -> set of directions
        self.kind = {}            # cell -> room kind
        self.start = None
        self.down = None
        self.arena = None         # top-left cell of the 2x2 arena
        self.reward = None
        self.grace = None
        self.secret = None

    def neighbours(self, c):
        for d, (dx, dz) in DIRS.items():
            n = (c[0] + dx, c[1] + dz)
            if 0 <= n[0] < self.gw and 0 <= n[1] < self.gd:
                yield d, n

    def link(self, a, d):
        dx, dz = DIRS[d]
        b = (a[0] + dx, a[1] + dz)
        self.links.setdefault(a, set()).add(d)
        self.links.setdefault(b, set()).add(OPP[d])
        return b


def _bfs(level, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        c = q.popleft()
        for d in level.links.get(c, ()):
            dx, dz = DIRS[d]
            n = (c[0] + dx, c[1] + dz)
            if n not in dist:
                dist[n] = dist[c] + 1
                q.append(n)
    return dist


def plan(seed, levels=3, gw=5, gd=5):
    """Plan every level: corridors/rooms, stairs, arena. Returns (entrance cell, [Level])."""
    rng = random.Random(seed)
    out = []
    start = (rng.randint(1, gw - 2), rng.randint(1, gd - 2))
    entrance = start
    for k in range(levels):
        lv = Level(k, gw, gd)
        lv.start = start
        blocked = set()
        last = k == levels - 1
        if last:
            # the arena: a 2x2 block in the corner farthest from the stairs, reward vault beyond it
            corners = [(0, 0), (gw - 2, 0), (0, gd - 2), (gw - 2, gd - 2)]
            corners.sort(key=lambda c: -(abs(c[0] + 0.5 - start[0]) + abs(c[1] + 0.5 - start[1])))
            ax, az = corners[0]
            lv.arena = (ax, az)
            blocked |= {(ax, az), (ax + 1, az), (ax, az + 1), (ax + 1, az + 1)}
            # reward vault: outside the arena on the side away from the grid centre if possible
            options = []
            for c in ((ax - 1, az), (ax + 2, az), (ax, az - 1), (ax, az + 2), (ax - 1, az + 1), (ax + 2, az + 1),
                      (ax + 1, az - 1), (ax + 1, az + 2)):
                if 0 <= c[0] < gw and 0 <= c[1] < gd and c not in blocked and c != start:
                    options.append(c)
            lv.reward = rng.choice(options)
            blocked.add(lv.reward)
        # random spanning tree (depth first)
        seen = {start}
        stack = [start]
        while stack:
            c = stack[-1]
            nbrs = [(d, n) for d, n in lv.neighbours(c) if n not in seen and n not in blocked]
            if not nbrs:
                stack.pop()
                continue
            d, n = rng.choice(nbrs)
            lv.link(c, d)
            seen.add(n)
            stack.append(n)
        # a few loops so it is not a pure maze
        for c in list(seen):
            for d, n in lv.neighbours(c):
                if n in seen and d not in lv.links.get(c, set()) and rng.random() < 0.12:
                    lv.link(c, d)
        dist = _bfs(lv, start)
        if last:
            ax, az = lv.arena
            arena_cells = {(ax, az), (ax + 1, az), (ax, az + 1), (ax + 1, az + 1)}
            # the door: the reachable cell next to the arena that is farthest from the stairs
            doors = []
            for c in seen:
                for d, n in lv.neighbours(c):
                    if n in arena_cells:
                        doors.append((dist.get(c, 0), c, d, n))
            doors.sort(reverse=True)
            _, gcell, gdir, acell = doors[0]
            lv.grace = gcell
            lv.arena_door = (gcell, gdir, acell)
            # reward door: from the arena cell touching the reward vault
            for c in arena_cells:
                for d, n in lv.neighbours(c):
                    if n == lv.reward:
                        lv.reward_door = (c, d, n)
        else:
            leaves = sorted((dist[c], c) for c in seen if c != start)
            lv.down = leaves[-1][1]
            start = lv.down
        # room kinds
        for c in seen:
            if c in (lv.start, lv.down) or c == lv.grace:
                continue
            deg = len(lv.links.get(c, ()))
            r = rng.random()
            if deg == 1:
                lv.kind[c] = rng.choice(["treasure", "ossuary", "spawner", "shrine", "crypt", "treasure"])
            elif r < 0.30:
                lv.kind[c] = rng.choice(["hall", "crypt", "ossuary", "shrine"])
            elif r < 0.45:
                lv.kind[c] = "trap"
            else:
                lv.kind[c] = "corridor"
        # a secret chamber: an unused cell next to a room (only on non-final levels with space)
        unused = [(x, z) for x in range(gw) for z in range(gd) if (x, z) not in seen and (x, z) not in blocked]
        rng.shuffle(unused)
        for u in unused:
            for d, n in lv.neighbours(u):
                if lv.kind.get(n) in ("hall", "crypt", "ossuary", "shrine", "treasure", "spawner"):
                    lv.secret = (u, OPP[d], n)
                    break
            if lv.secret:
                break
        out.append(lv)
    return entrance, out


# ------------------------------------------------------------------ drawing helpers
def cell_center(c, gw, gd):
    return (c[0] - gw // 2) * CELL, (c[1] - gd // 2) * CELL


def level_y(k):
    return TOP - k * LEVEL_H


class Painter:
    def __init__(self, bp, theme, seed):
        self.bp = bp
        self.t = theme
        self.rng = random.Random(seed)
        self.shells = []      # (x0, y0, z0, x1, y1, z1)
        self.airs = []        # (x0, y0, z0, x1, y1, z1)
        self.spawner_count = 0

    def shell(self, *box):
        self.shells.append(box)

    def air(self, *box, floor=True):
        self.airs.append((box, floor))

    def flush(self):
        bp, t, rng = self.bp, self.t, self.rng
        for x0, y0, z0, x1, y1, z1 in self.shells:
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    for z in range(z0, z1 + 1):
                        if (x, y, z) not in bp.blocks:
                            bp.set(x, y, z, rng.choice(t.wall))
        carved = set()
        for (x0, y0, z0, x1, y1, z1), floor in self.airs:
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    if floor and (x, y0 - 1, z) not in carved:
                        bp.set(x, y0 - 1, z, rng.choice(t.floor))
                    for y in range(y0, y1 + 1):
                        bp.set(x, y, z, "air")
                        carved.add((x, y, z))
                    if floor and (x, y1 + 1, z) not in carved:
                        bp.set(x, y1 + 1, z, rng.choice(t.ceiling))
        self.carved = carved

    def atmosphere(self, avoid):
        """Cobwebs high in corners, rubble and bones on floors, a few hanging chains."""
        bp, t, rng = self.bp, self.t, self.rng
        for (x, y, z) in sorted(self.carved):
            if any(x0 <= x <= x1 and z0 <= z <= z1 and y0 <= y <= y1 for x0, y0, z0, x1, y1, z1 in avoid):
                continue
            if bp.get(x, y, z) != "minecraft:air":
                continue
            below, above = (x, y - 1, z) not in self.carved, (x, y + 1, z) not in self.carved
            walls = sum((x + dx, y, z + dz) not in self.carved for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            r = rng.random()
            if above and walls >= 2 and r < 0.35:
                bp.set(x, y, z, "cobweb")
            elif above and r < 0.006:
                bp.set(x, y, z, with_props("iron_chain", axis="y"))
            elif below and walls >= 1 and r < 0.025:
                bp.set(x, y, z, rng.choice((t.bones, "cobblestone_slab[type=bottom,waterlogged=false]",
                                            with_props(t.skull, rotation=rng.randint(0, 15)), "tuff_slab[type=bottom,waterlogged=false]")))


def _box(cx, y, cz, hx, h, hz):
    return (cx - hx, y, cz - hz, cx + hx, y + h - 1, cz + hz)


# ------------------------------------------------------------------ pieces
def corridor_cell(p, cx, y, cz, dirs, trap=False):
    """Junction in the middle and 3-wide arms toward each linked side."""
    p.shell(*_grow(_box(cx, y, cz, 3, 6, 3), 0))
    p.air(*_box(cx, y, cz, 2, 4, 2))
    for d in dirs:
        dx, dz = DIRS[d]
        half = CELL // 2
        if dx:
            x0, x1 = sorted((cx + 2 * dx, cx + half * dx))
            p.shell(x0, y - 1, cz - 2, x1, y + 4, cz + 2)
            p.air(x0, y, cz - 1, x1, y + 3, cz + 1)
        else:
            z0, z1 = sorted((cz + 2 * dz, cz + half * dz))
            p.shell(cx - 2, y - 1, z0, cx + 2, y + 4, z1)
            p.air(cx - 1, y, z0, cx + 1, y + 3, z1)


def _grow(box, n):
    x0, y0, z0, x1, y1, z1 = box
    return (x0 - 1 - n, y0 - 1, z0 - 1 - n, x1 + 1 + n, y1 + 1, z1 + 1 + n)


def room_cell(p, cx, y, cz, dirs, height=6):
    """An 11x11 room with 3-wide doors on its linked sides."""
    half = CELL // 2
    p.shell(cx - half, y - 1, cz - half, cx + half, y + height, cz + half)
    p.air(cx - half + 1, y, cz - half + 1, cx + half - 1, y + height - 1, cz + half - 1)
    for d in dirs:
        dx, dz = DIRS[d]
        if dx:
            x = cx + half * dx
            p.air(x, y, cz - 1, x, y + 3, cz + 1)
        else:
            z = cz + half * dz
            p.air(cx - 1, y, z, cx + 1, y + 3, z)


def door_frames(bp, t, cx, y, cz, dirs, half=CELL // 2):
    """Trimmed arches on room doorways."""
    for d in dirs:
        dx, dz = DIRS[d]
        for s in (-2, 2):
            x, z = (cx + half * dx, cz + s) if dx else (cx + s, cz + half * dz)
            for yy in range(y, y + 4):
                bp.set(x, yy, z, t.pillar)
        x, z = (cx + half * dx, cz) if dx else (cx, cz + half * dz)
        for s in (-1, 0, 1):
            xx, zz = (x, z + s) if dx else (x + s, z)
            bp.set(xx, y + 4, zz, t.pillar)


def dress(p, kind, cx, y, cz, level_k, dungeon):
    """Furnish a room by kind."""
    bp, t, rng = p.bp, p.t, p.rng
    h = 6
    if kind == "hall":
        for sx in (-3, 3):
            for sz in (-3, 3):
                for yy in range(y, y + h):
                    bp.set(cx + sx, yy, cz + sz, t.pillar)
        bp.set(cx, y + h - 1, cz, with_props("iron_chain", axis="y"))
        bp.set(cx, y + h - 2, cz, with_props(t.light, hanging=True) if "lantern" in t.light else t.light)
        for sx in (-4, 4):
            bp.set(cx + sx, y, cz, t.accent)
    elif kind == "ossuary":
        for sx in (-5, 5):
            for sz in range(-4, 5):
                if sz % 2 == 0:
                    for yy in range(y, y + 4):
                        bp.set(cx + sx, yy, cz + sz, t.bones if (yy + sz) % 3 else t.pillar)
                else:
                    bp.set(cx + sx, y + 1, cz + sz, with_props(t.skull, rotation=4 if sx < 0 else 12))
        for i in range(6):
            bp.set(cx + rng.randint(-3, 3), y, cz + rng.randint(-3, 3), with_props(t.candle, candles=rng.randint(1, 4), lit=True))
    elif kind == "crypt":
        for sz in (-3, 0, 3):
            for sx in (-3, 3):
                for dz in (0, 1):
                    bp.set(cx + sx, y, cz + sz + dz - 1, t.pillar)
                    bp.set(cx + sx, y + 1, cz + sz + dz - 1, with_props(t.trim + "_slab", type="bottom"))
        bp.set(cx, y, cz - 4, with_props(t.candle, candles=3, lit=True))
        if rng.random() < 0.6:
            bp.barrel(cx, y, cz + 4, "up", dungeon.loot)
    elif kind == "shrine":
        bp.set(cx, y, cz, t.accent)
        bp.set(cx, y + 1, cz, with_props(t.candle, candles=4, lit=True))
        for sx, sz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            bp.set(cx + sx, y, cz + sz, t.pillar)
            bp.set(cx + sx, y + 1, cz + sz, with_props(t.candle, candles=2, lit=True))
        bp.set(cx, y, cz - 4, "lectern[facing=south,has_book=false,powered=false]")
    elif kind == "spawner" and t.spawners and p.spawner_count < 5:
        bp.set(cx, y, cz, t.pillar)
        bp.spawner(cx, y + 1, cz, rng.choice(t.spawners))
        p.spawner_count += 1
        for i in range(5):
            bp.set(cx + rng.randint(-4, 4), y, cz + rng.randint(-4, 4), t.bones)
    elif kind == "treasure":
        bp.set(cx, y, cz - 4, t.accent)
        bp.chest(cx, y + 1, cz - 4, "south", dungeon.treasure if rng.random() < 0.5 else dungeon.loot)
        bp.set(cx - 2, y, cz - 4, with_props(t.candle, candles=2, lit=True))
        bp.set(cx + 2, y, cz - 4, with_props(t.candle, candles=2, lit=True))


def arrow_trap(bp, t, cx, y, cz, d):
    """Tripwire across a corridor arm; the hooks power the wall, a dispenser next to it fires arrows."""
    dx, dz = DIRS[d]
    off = 4
    if dx:
        x = cx + off * dx
        bp.set(x, y, cz - 1, "tripwire_hook[facing=south,attached=true,powered=false]")
        bp.set(x, y, cz, "tripwire[attached=true,disarmed=false,east=false,north=true,powered=false,south=true,west=false]")
        bp.set(x, y, cz + 1, "tripwire_hook[facing=north,attached=true,powered=false]")
        bp.set(x, y, cz - 2, t.wall[0])
        bp.set(x, y + 1, cz - 2, "dispenser[facing=south,triggered=false]", _arrows())
    else:
        z = cz + off * dz
        bp.set(cx - 1, y, z, "tripwire_hook[facing=east,attached=true,powered=false]")
        bp.set(cx, y, z, "tripwire[attached=true,disarmed=false,east=true,north=false,powered=false,south=false,west=true]")
        bp.set(cx + 1, y, z, "tripwire_hook[facing=west,attached=true,powered=false]")
        bp.set(cx - 2, y, z, t.wall[0])
        bp.set(cx - 2, y + 1, z, "dispenser[facing=east,triggered=false]", _arrows())


def _arrows():
    return {"Items": [{"Slot": nbt.Byte(0), "id": nbt.String("minecraft:arrow"), "count": nbt.Int(24)}]}


def spiral_down(p, cx, cz, y_top, y_bottom, open_top=True):
    """A round stairwell (radius 4) from y_top down to y_bottom, built into the shells."""
    bp, t = p.bp, p.t
    r = 4
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = math.hypot(x - cx, z - cz)
            for y in range(y_bottom - 1, y_top + 5):
                if d <= r + 0.6:
                    if d <= r - 0.4:
                        if y_bottom <= y <= y_top + 3:
                            p.air(x, y, z, x, y, z, floor=False)
                    else:
                        p.shell(x, y, z, x, y, z)
    return (cx, cz, y_top, y_bottom)


def draw_stairs(bp, t, cx, cz, y_top, y_bottom):
    """Half-slab spiral around a central pillar, from the lower floor up to the upper one."""
    bp.spiral_stairs(cx, cz, y_bottom, y_top - 1, 3, t.trim + "_slab", center=t.pillar)
    for y in range(y_top, y_top + 4):
        bp.set(cx, y, cz, t.pillar)
    for y in range(y_bottom, y_top + 3, 5):
        bp.set(cx + 3, y + 2, cz + 3, with_props("lantern", hanging=False) if "lantern" in t.light else t.light)


def arena(p, theme, lv, gw, gd, y, boss, dungeon):
    """2x2-cell arena (24x24 inside, 12 high) with seal, pillars, mist on both doors."""
    bp, t, rng = p.bp, p.t, p.rng
    ax, az = lv.arena
    x0, z0 = cell_center((ax, az), gw, gd)
    half = CELL // 2
    xa, za = x0 - half, z0 - half
    xb, zb = x0 + CELL + half, z0 + CELL + half
    H = 12
    p.shell(xa, y - 1, za, xb, y + H, zb)
    p.air(xa + 1, y, za + 1, xb - 1, y + H - 1, zb - 1)
    cx, cz = (xa + xb) // 2, (za + zb) // 2
    return (xa, za, xb, zb, cx, cz, H)


def arena_dress(p, box, theme, boss, lv, gw, gd, y):
    bp, t, rng = p.bp, p.t, p.rng
    xa, za, xb, zb, cx, cz, H = box
    # floor pattern: rings of trim around the seal
    for x in range(xa + 1, xb):
        for z in range(za + 1, zb):
            d = math.hypot(x - cx - 0.5, z - cz - 0.5)
            if 3.5 <= d < 4.5 or 8.5 <= d < 9.3:
                bp.set(x, y - 1, z, t.accent)
    # pillars along the walls, with lights
    for i in range(xa + 3, xb - 1, 5):
        for z in (za + 1, zb - 1):
            for yy in range(y, y + H):
                bp.set(i, yy, z, t.pillar)
            bp.set(i, y + 6, z + (1 if z == za + 1 else -1),
                   with_props(t.light, hanging=False) if "lantern" in t.light else t.light)
    for i in range(za + 3, zb - 1, 5):
        for x in (xa + 1, xb - 1):
            for yy in range(y, y + H):
                bp.set(x, yy, i, t.pillar)
            bp.set(x + (1 if x == xa + 1 else -1), y + 6, i,
                   with_props(t.light, hanging=False) if "lantern" in t.light else t.light)
    # a hanging centrepiece
    for yy in range(y + 8, y + H):
        bp.set(cx, yy, cz, with_props("iron_chain", axis="y"))
    bp.set(cx, y + 7, cz, t.light if "lantern" not in t.light else with_props(t.light, hanging=True))
    radius = max(9, (xb - xa) // 2 - 1)
    bp.boss_seal(cx, y, cz, boss, radius)


def build(bp, theme, seed, boss, dungeon, levels=3, gw=5, gd=5, entrance_fn=None):
    """Draw the whole dungeon into ``bp``. ``entrance_fn(bp, theme, x, z)`` builds the surface entrance
    (blueprint y >= 0) around the stairwell top at (x, z)."""
    entrance, lvls = plan(seed, levels, gw, gd)
    p = Painter(bp, theme, seed)
    stairs = []
    arena_box = None
    trap_spots = []
    rooms = []
    ex, ez = cell_center(entrance, gw, gd)
    stairs.append(spiral_down(p, ex, ez, 0, level_y(0)))
    for lv in lvls:
        y = level_y(lv.k)
        for c, dirs in lv.links.items():
            cx, cz = cell_center(c, gw, gd)
            kind = lv.kind.get(c, "corridor")
            if c in (lv.start, lv.down) or c == lv.grace:
                room_cell(p, cx, y, cz, dirs)
            elif kind in ("corridor", "trap"):
                corridor_cell(p, cx, y, cz, dirs)
                if kind == "trap" and dirs:
                    trap_spots.append((cx, y, cz, sorted(dirs)[0]))
            else:
                room_cell(p, cx, y, cz, dirs)
                rooms.append((lv, c, kind, cx, y, cz, dirs))
        if lv.down is not None:
            dx, dz = cell_center(lv.down, gw, gd)
            stairs.append(spiral_down(p, dx, dz, y, level_y(lv.k + 1), open_top=True))
        if lv.secret:
            u, d, n = lv.secret
            ux, uz = cell_center(u, gw, gd)
            p.shell(ux - 4, y - 1, uz - 4, ux + 4, y + 5, uz + 4)
            p.air(ux - 3, y, uz - 3, ux + 3, y + 3, uz + 3)
            # passage toward the room it hides behind (closed by cracked bricks after flush)
            ddx, ddz = DIRS[d]
            for k in range(4, CELL - 4):
                x, z = ux + ddx * k, uz + ddz * k
                p.air(x, y, z, x, y + 1, z)
            lv.secret_wall = (ux + ddx * (CELL - 6), y, uz + ddz * (CELL - 6), ddx, ddz)
        if lv.arena:
            arena_box = arena(p, theme, lv, gw, gd, y, boss, dungeon)
            gcell, gdir, acell = lv.arena_door
            gx, gz = cell_center(gcell, gw, gd)
            ddx, ddz = DIRS[gdir]
            half = CELL // 2
            for k in range(half, half + 2):
                x, z = gx + ddx * k, gz + ddz * k
                if ddx:
                    p.air(x, y, z - 1, x, y + 3, z + 1)
                else:
                    p.air(x - 1, y, z, x + 1, y + 3, z)
            lv.mist_a = (gx + ddx * (half + 1), gz + ddz * (half + 1), ddx, ddz)
            rcell = lv.reward
            rx, rz = cell_center(rcell, gw, gd)
            p.shell(rx - 4, y - 1, rz - 4, rx + 4, y + 5, rz + 4)
            p.air(rx - 3, y, rz - 3, rx + 3, y + 4, rz + 3)
            c, d, n = lv.reward_door
            cx2, cz2 = cell_center(c, gw, gd)
            ddx, ddz = DIRS[d]
            for k in range(half - 1, CELL - 3):
                x, z = cx2 + ddx * k, cz2 + ddz * k
                if ddx:
                    p.air(x, y, z - 1, x, y + 3, z + 1)
                else:
                    p.air(x - 1, y, z, x + 1, y + 3, z)
            lv.mist_b = (cx2 + ddx * half, cz2 + ddz * half, ddx, ddz)
    p.flush()

    # ---------------------------------------------------------- second pass: dressing
    for top in stairs:
        draw_stairs(bp, theme, *top)
    for lv, c, kind, cx, y, cz, dirs in rooms:
        door_frames(bp, theme, cx, y, cz, dirs)
        dress(p, kind, cx, y, cz, lv.k, dungeon)
    for cx, y, cz, d in trap_spots:
        arrow_trap(bp, theme, cx, y, cz, d)
    for lv in lvls:
        y = level_y(lv.k)
        if getattr(lv, "secret_wall", None):
            x, yy, z, ddx, ddz = lv.secret_wall
            for k in (0, 1):
                bp.set(x + ddx * k, yy, z + ddz * k, theme.cracked)
                bp.set(x + ddx * k, yy + 1, z + ddz * k, theme.cracked)
            u, d, n = lv.secret
            ux, uz = cell_center(u, gw, gd)
            bp.chest(ux, y, uz, "south", dungeon.treasure)
            bp.set(ux + 2, y, uz, theme.bones)
            bp.set(ux - 2, y, uz, with_props(theme.candle, candles=3, lit=True))
        if lv.arena:
            arena_dress(p, arena_box, theme, boss, lv, gw, gd, y)
            # site of grace: a waystone and lights in the cell before the mist
            gx, gz = cell_center(lv.grace, gw, gd)
            bp.set(gx, y, gz, "wayfarers:waystone")
            for sx, sz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
                bp.set(gx + sx, y, gz + sz, with_props(theme.candle, candles=3, lit=True))
            for key in ("mist_a", "mist_b"):
                mx, mz, ddx, ddz = getattr(lv, key)
                if ddx:
                    bp.mist(mx, y, mz - 1, mx, y + 3, mz + 1)
                else:
                    bp.mist(mx - 1, y, mz, mx + 1, y + 3, mz)
            rx, rz = cell_center(lv.reward, gw, gd)
            bp.chest(rx, y, rz - 2, "south", dungeon.reward)
            bp.chest(rx - 2, y, rz - 2, "south", dungeon.treasure)
            for sx in (-2, 2):
                bp.set(rx + sx, y, rz + 2, theme.accent)
                bp.set(rx + sx, y + 1, rz + 2, with_props(theme.candle, candles=4, lit=True))
    avoid = [(sx - 5, sy - 1, sz - 5, sx + 5, top + 5, sz + 5) for sx, sz, top, sy in stairs]
    if arena_box:
        xa, za, xb, zb = arena_box[:4]
        yb = level_y(lvls[-1].k)
        avoid.append((xa - 2, yb - 1, za - 2, xb + 2, yb + 13, zb + 2))
        for lv in lvls:
            if lv.grace:
                gx, gz = cell_center(lv.grace, gw, gd)
                avoid.append((gx - 7, yb - 1, gz - 7, gx + 7, yb + 6, gz + 7))
    p.atmosphere(avoid)
    if entrance_fn:
        entrance_fn(bp, theme, ex, ez)
    return entrance, lvls


class Dungeon:
    """Loot table names used by a dungeon."""

    def __init__(self, loot, treasure, reward):
        self.loot = loot
        self.treasure = treasure
        self.reward = reward

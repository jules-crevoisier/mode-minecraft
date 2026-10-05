"""Clockwork Citadel: a steampunk town around a 70-block clock tower (Lot 6, mega-structures).

Layout, centred on (0, 0), ground y = 0:
  * an octagonal iron plaza (radius 34) ringed by a smokestack-brick wall with four gates,
  * the clock tower (15x15): seven floors around a spiral stair, four clock faces, an open belfry with a bell,
    a verdigris spire and a balcony with brass railings,
  * four workshop halls along the axes (machines, crates, benches, hanging lamps),
  * four smoking chimneys in the corners, linked by pipes.
Style: tools/STYLE_STEAMPUNK.md (dark iron and brick for mass, brass for trims, warm Edison light).
"""
import math

from .. import arch
from .. import interior as INT
from .. import denizens
from ..arch import stair
from ..blueprint import with_props
from ..defs import Piece, StructureDef, register
from ..parts import LOOT
from . import lair_grand_clockmaker

W = "brasshaven:"
BRASS, COPPER, VERD, IRON = W + "brass_plating", W + "copper_plating", W + "verdigris_plating", W + "dark_iron_plating"
TREAD, GEAR, PIPES, GAUGE = W + "diamond_plate", W + "gear_panel", W + "copper_pipes", W + "pressure_gauge"
EDISON, AETHER, MAHOGANY, LEATHER, SMOKE = (W + "edison_lamp", W + "aether_conduit", W + "mahogany_panelling",
                                           W + "leather_padding", W + "smokestack_bricks")
BRASS_STAIRS, SMOKE_STAIRS = W + "brass_plating_stairs", W + "smokestack_brick_stairs"
# real verdigris for roofs and spires: oxidized copper never changes further
OXI, OXI_STAIRS = "oxidized_cut_copper", "oxidized_cut_copper_stairs"
TREAD_SLAB, SMOKE_WALL = W + "diamond_plate_slab", W + "smokestack_brick_wall"

R_PLAZA = 34
T = 7            # tower half-width
FLOORS = [0, 8, 16, 24, 32, 40]
CLOCK_Y = 49
BELFRY = 56
ROOF = 63
SIDES = ("north", "south", "east", "west")


def _face_xz(face, u, out):
    """Point on the tower face: `u` along the face, `out` blocks outside the wall plane."""
    line = T + out
    return {"north": (u, -line), "south": (u, line), "east": (line, u), "west": (-line, u)}[face]


def _local(face, a, b):
    """Hall coordinates: `a` = distance from the centre along `face`, `b` = across (left/right)."""
    return {"north": (b, -a), "south": (-b, a), "east": (a, b), "west": (-a, -b)}[face]


def _octagon(x, z, r):
    return max(abs(x), abs(z), (abs(x) + abs(z)) / 1.42) <= r


# ------------------------------------------------------------------ plaza and wall
def plaza(bp):
    for x in range(-R_PLAZA - 2, R_PLAZA + 3):
        for z in range(-R_PLAZA - 2, R_PLAZA + 3):
            if _octagon(x, z, R_PLAZA + 1):
                ring = not _octagon(x, z, R_PLAZA - 1)
                bp.set(x, 0, z, IRON if ring else (TREAD if (x + z) % 7 else IRON))
                for y in range(1, 26):
                    bp.set(x, y, z, "air")
    # perimeter wall with gates on the axes
    for x in range(-R_PLAZA - 1, R_PLAZA + 2):
        for z in range(-R_PLAZA - 1, R_PLAZA + 2):
            if _octagon(x, z, R_PLAZA + 0.7) and not _octagon(x, z, R_PLAZA - 0.3):
                gate = min(abs(x), abs(z)) <= 3
                if gate:
                    continue
                post = (x + z) % 6 == 0
                bp.set(x, 1, z, SMOKE)
                bp.set(x, 2, z, SMOKE if post else SMOKE_WALL)
                if post:
                    bp.set(x, 3, z, BRASS)
                    bp.lantern(x, 4, z)
    for face in SIDES:
        for b in (-4, 4):
            x, z = _local(face, R_PLAZA, b)
            for y in range(1, 6):
                bp.set(x, y, z, BRASS)
            bp.set(x, 6, z, GEAR)
            bp.lantern(x, 7, z)


# ------------------------------------------------------------------ chimneys
def chimneys(bp):
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * 25, sz * 25
            bp.disk(cx, 0, cz, 4, IRON)
            bp.cylinder(cx, 1, cz, 38, 3, SMOKE)
            for y in (12, 24, 36):
                bp.disk(cx, y, cz, 3, BRASS, hollow=True)
            bp.disk(cx, 39, cz, 4, BRASS, hollow=True)
            bp.disk(cx, 39, cz, 3, SMOKE, hollow=True)
            # a signal-fire campfire on hay inside the top: a tall column of smoke
            bp.set(cx, 37, cz, "hay_block[axis=y]")
            bp.set(cx, 38, cz, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
            # pipe from the chimney base to the nearest hall
            for i in range(5, 12):
                x, z = cx - sx * i, cz
                bp.set(x, 1, z, W + "copper_pipe[axis=x]")
            bp.set(cx - sx * 4, 1, cz, W + "valve_wheel[facing=" + ("west" if sx > 0 else "east") + "]")


# ------------------------------------------------------------------ workshop halls
def hall(bp, face):
    a0, a1, half, h = 12, 29, 5, 6
    for a in range(a0, a1 + 1):
        for b in range(-half, half + 1):
            x, z = _local(face, a, b)
            edge_a, edge_b = a in (a0, a1), abs(b) == half
            bp.set(x, 0, z, MAHOGANY if not (edge_a or edge_b) else IRON)
            for y in range(1, h + 1):
                if edge_a or edge_b:
                    pilaster = (a - a0) % 4 == 0 or (edge_a and edge_b)
                    wall = BRASS if pilaster else (COPPER if y <= 2 else ("glass_pane" if y in (3, 4) and not edge_a else SMOKE))
                    if y == h:
                        wall = BRASS
                    bp.set(x, y, z, wall)
                else:
                    bp.set(x, y, z, "air")
    # roof: verdigris gable along the hall
    for a in range(a0 - 1, a1 + 2):
        for d in range(0, half + 2):
            y = h + 1 + (half + 1 - d)
            for b in (-d, d):
                x, z = _local(face, a, b)
                facing = _outward(face, b) if d else None
                if d == 0:
                    bp.set(x, y, z, OXI)
                else:
                    bp.set(x, y, z, stair(OXI_STAIRS, _opposite_dir(facing)))
                    if a in (a0 - 1, a1 + 1):
                        continue
                    for yy in range(h + 1, y):
                        if a in (a0, a1):
                            bp.set(x, yy, z, SMOKE)
    # gable ends: brick fill with a round window
    # doorways: towards the tower (a0) and towards the gate (a1)
    for a in (a0, a1):
        for b in (-1, 0, 1):
            x, z = _local(face, a, b)
            for y in range(1, 4):
                bp.set(x, y, z, "air")
        x, z = _local(face, a, 0)
        bp.set(x, 4, z, GEAR)
    # interior: two rows of machines and benches, crates, lamps
    machines = [W + "auto_harvester", W + "block_breaker", W + "block_placer", W + "redstone_timer",
                W + "vacuum_hopper", W + "sprinkler", W + "entity_detector", W + "wireless_receiver"]
    for i, a in enumerate(range(a0 + 2, a1 - 1, 3)):
        for side in (-1, 1):
            b = side * (half - 1)
            x, z = _local(face, a, b)
            m = machines[(i * 2 + (side > 0)) % len(machines)]
            facing = _inward(face, side)
            bp.set(x, 1, z, with_props(m, facing=facing, powered=False))
            bp.set(x, 2, z, W + "compacting_crate[facing=" + facing + "]" if i % 2 else GAUGE)
            x2, z2 = _local(face, a + 1, b)
            bp.set(x2, 1, z2, W + "mahogany_table")
        x, z = _local(face, a, 0)
        bp.set(x, h, z, IRON)
        bp.set(x, h - 1, z, W + "hanging_edison_lamp")
    # chests
    for k, a in enumerate((a0 + 1, a1 - 1)):
        x, z = _local(face, a, -(half - 1))
        bp.chest(x, 1, z, _inward(face, -1), loot=LOOT + ("clockwork_workshop" if k == 0 else "clockwork_vault"))
    # pipes along the ridge inside
    for a in range(a0 + 1, a1):
        x, z = _local(face, a, 0)
        bp.set(x, h, z, IRON)


def _outward(face, b):
    """Direction pointing away from the hall's centre line on side b."""
    left = {"north": "west", "south": "east", "east": "north", "west": "south"}[face]
    right = {"north": "east", "south": "west", "east": "south", "west": "north"}[face]
    return right if b > 0 else left


def _inward(face, side):
    return _outward(face, -side)


def _opposite_dir(d):
    return {"north": "south", "south": "north", "east": "west", "west": "east"}[d]


# ------------------------------------------------------------------ the clock tower
def tower(bp):
    top = ROOF
    # shell
    for y in range(0, BELFRY):
        for x in range(-T, T + 1):
            for z in range(-T, T + 1):
                edge = max(abs(x), abs(z)) == T
                corner = abs(x) >= T - 1 and abs(z) >= T - 1
                if y == 0:
                    bp.set(x, 0, z, IRON if edge else TREAD)
                elif edge or corner:
                    band = y % 8 == 0
                    bp.set(x, y, z, BRASS if band else (IRON if corner else SMOKE))
                else:
                    bp.set(x, y, z, "air")
    # corner buttresses
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in range(0, BELFRY + 2):
                bp.set(sx * (T + 1), y, sz * (T + 1), IRON if y % 8 else GEAR)
            bp.set(sx * (T + 1), BELFRY + 2, sz * (T + 1), EDISON)
    # floors (with the stairwell left open) and furnishing
    for i, fy in enumerate(FLOORS[1:], start=1):
        for x in range(-T + 1, T):
            for z in range(-T + 1, T):
                if max(abs(x), abs(z)) > 2:
                    bp.set(x, fy, z, MAHOGANY if i % 2 else TREAD)
    bp.spiral_stairs(0, 0, 1, BELFRY - 1, 2, TREAD_SLAB, center=W + "copper_pipe[axis=y]")
    # landings: make sure each floor connects to the spiral
    for fy in FLOORS[1:]:
        for x, z in ((3, 0), (-3, 0), (0, 3), (0, -3)):
            bp.set(x, fy, z, TREAD)
    # windows on every floor, framed in brass
    for face in SIDES:
        for fy in FLOORS:
            if fy >= 40:
                continue
            for u in (-4, 4):
                for dy in (3, 4):
                    x, z = _face_xz(face, u, 0)
                    bp.set(x, fy + dy, z, "glass_pane")
                xb, zb = _face_xz(face, u, 1)
                bp.set(xb, fy + 2, zb, stair(BRASS_STAIRS, face, "top"))
    # doors at ground level
    for face in SIDES:
        line = {"north": -T, "south": T, "east": T, "west": -T}[face]
        arch.arch_door(bp, face, line, 0, 0, width=3, height=4, trim=BRASS, stairs=BRASS_STAIRS, door="dark_oak")
    # balcony at y 24 all around, with brass railings, opened from the 4th floor
    by = 24
    for x in range(-T - 3, T + 4):
        for z in range(-T - 3, T + 4):
            r = max(abs(x), abs(z))
            if T < r <= T + 3:
                bp.set(x, by, z, TREAD)
                if r == T + 3:
                    facing = ("north" if z < 0 else "south") if abs(z) >= abs(x) else ("west" if x < 0 else "east")
                    bp.set(x, by + 1, z, f"{W}brass_railing[facing={facing}]")
            if T < r <= T + 2 and (x + z) % 4 == 0 and r == T + 1:
                pass
    for face in SIDES:
        for u in (-1, 0, 1):
            x, z = _face_xz(face, u, 0)
            for dy in (1, 2):
                bp.set(x, by + dy, z, "air")
        x, z = _face_xz(face, 0, 0)
        bp.set(x, by + 3, z, GEAR)
        # brackets under the balcony
        for u in (-T - 2, 0, T + 2):
            bx, bz = _face_xz(face, u, 2) if abs(u) < T else _face_xz(face, u, 1)
            bp.set(bx, by - 1, bz, stair(BRASS_STAIRS, _opposite_dir(face), "top"))
    # clock faces
    for face in SIDES:
        clock_face(bp, face)
    # belfry: open arches on four pillars, bell in the middle
    for y in range(BELFRY, top):
        for x in range(-T, T + 1):
            for z in range(-T, T + 1):
                edge = max(abs(x), abs(z)) == T
                pillar = abs(x) >= T - 2 and abs(z) >= T - 2
                if y == BELFRY:
                    bp.set(x, y, z, TREAD)
                elif edge and pillar:
                    bp.set(x, y, z, BRASS)
                elif edge and y >= top - 2:
                    bp.set(x, y, z, SMOKE if y == top - 2 else BRASS)
                elif edge and y == BELFRY + 1:
                    bp.set(x, y, z, W + f"brass_railing[facing={_edge_facing(x, z)}]")
                else:
                    bp.set(x, y, z, "air")
    for x in range(-T, T + 1):
        for z in range(-T, T + 1):
            bp.set(x, top, z, IRON)
    bp.set(0, top - 1, 0, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.set(0, top - 2, 0, "air")
    bp.set(2, top - 1, 2, W + "brass_chandelier")
    bp.set(-2, top - 1, -2, W + "brass_chandelier")
    # verdigris spire with four small pinnacles
    spire(bp, 0, 0, top + 1, T, 20)
    for sx in (-1, 1):
        for sz in (-1, 1):
            spire(bp, sx * (T - 1), sz * (T - 1), top + 1, 1, 6)
    interiors(bp)


def _edge_facing(x, z):
    if abs(z) >= abs(x):
        return "north" if z < 0 else "south"
    return "west" if x < 0 else "east"


def spire(bp, cx, cz, y0, r, h):
    for i in range(h):
        rr = r * (1 - i / h)
        ri = int(round(rr))
        y = y0 + i
        for x in range(cx - ri, cx + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                if max(abs(x - cx), abs(z - cz)) == ri:
                    bp.set(x, y, z, OXI if ri else BRASS)
                elif max(abs(x - cx), abs(z - cz)) < ri:
                    bp.set(x, y, z, "air" if i else OXI)
    bp.set(cx, y0 + h, cz, BRASS)
    bp.set(cx, y0 + h + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")


def clock_face(bp, face):
    """A 13-block brass-rimmed dial standing one block out of the wall, hands at ten past ten."""
    r = 6
    for du in range(-r, r + 1):
        for dv in range(-r, r + 1):
            d = math.hypot(du, dv)
            if d > r + 0.4:
                continue
            x, z = _face_xz(face, du, 1)
            y = CLOCK_Y + dv
            if d > r - 0.6:
                bp.set(x, y, z, BRASS)
            else:
                bp.set(x, y, z, "white_terracotta")
            # back wall stays solid
            bx, bz = _face_xz(face, du, 0)
            bp.set(bx, y, bz, SMOKE if d <= r - 0.6 else BRASS)
    for k in range(12):
        ang = k * math.pi / 6
        du, dv = round(math.sin(ang) * (r - 1.5)), round(math.cos(ang) * (r - 1.5))
        x, z = _face_xz(face, du, 1)
        bp.set(x, CLOCK_Y + dv, z, GEAR if k % 3 == 0 else IRON)
    for (du, dv) in ((0, 1), (0, 2), (0, 3), (0, 4), (-1, 1), (-2, 1), (-3, 2)):
        x, z = _face_xz(face, du, 1)
        bp.set(x, CLOCK_Y + dv, z, IRON)
    x, z = _face_xz(face, 0, 1)
    bp.set(x, CLOCK_Y, z, GAUGE)
    x, z = _face_xz(face, 0, 2)
    bp.set(x, CLOCK_Y, z, BRASS)


def interiors(bp):
    """Each floor has a role: entrance hall, workshop, archive, engine room, balcony salon, clockworks."""
    # ground floor: entrance hall with chandeliers and benches
    for x, z in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
        bp.set(x, 7, z, W + "brass_chandelier")
    for z in (-5, 5):
        for x in (-5, -4, 4, 5):
            bp.set(x, 1, z, f"{W}mahogany_chair[facing={'south' if z < 0 else 'north'}]")
    # floor 1 (y 8): workshop
    for x in (-5, -4, -3):
        bp.set(x, 9, -5, W + "mahogany_table")
    bp.set(-5, 10, -5, "lantern[hanging=false,waterlogged=false]")
    bp.chest(5, 9, -5, "west", loot=LOOT + "clockwork_workshop")
    for z in (-1, 0, 1):
        bp.set(5, 9, z, W + "compacting_crate[facing=west]")
    bp.set(-5, 9, 5, "smithing_table")
    bp.set(-4, 9, 5, "anvil[facing=north]")
    bp.set(4, 15, 4, W + "hanging_edison_lamp")
    bp.set(-4, 15, -4, W + "hanging_edison_lamp")
    # floor 2 (y 16): archive
    for x in range(-6, 7):
        if abs(x) > 2:
            for y in (17, 18):
                bp.set(x, y, -6, "bookshelf")
                bp.set(x, y, 6, "bookshelf")
    bp.set(-5, 17, 0, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(4, 23, 0, W + "brass_chandelier")
    bp.chest(5, 17, 4, "west", loot=LOOT + "clockwork_workshop")
    # floor 3 (y 24): balcony salon
    for x, z, f in ((-5, -5, "south"), (5, 5, "north"), (-5, 5, "north"), (5, -5, "south")):
        bp.set(x, 25, z, f"{W}mahogany_chair[facing={f}]")
    bp.set(0, 25, -5, W + "mahogany_table")
    bp.set(0, 31, 4, W + "brass_chandelier")
    for x in (-6, 6):
        for z in (-3, 3):
            bp.set(x, 25, z, LEATHER)
    # floor 4 (y 32): engine room, pipes and gauges on the walls
    for x in range(-6, 7):
        if abs(x) > 2:
            bp.set(x, 33, -6, PIPES)
            bp.set(x, 34, -6, GAUGE if x % 3 == 0 else PIPES)
    for z in range(-6, 7):
        if abs(z) > 2:
            bp.set(6, 33, z, AETHER if z % 2 else PIPES)
    bp.set(-5, 33, 5, W + "wireless_transmitter[facing=east,powered=false]")
    bp.set(-4, 39, 4, W + "hanging_edison_lamp")
    # floor 5 (y 40): the clockworks behind the dials, and the vault
    for x in range(-6, 7):
        for z in (-6, 6):
            if abs(x) > 2 and (x + z) % 2 == 0:
                bp.set(x, 41, z, GEAR)
    bp.chest(0, 41, -5, "south", loot=LOOT + "clockwork_vault")
    bp.set(5, 47, 5, W + "brass_chandelier")


def gardens(bp):
    """Brass fountains and azalea planters between the halls."""
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * 14, sz * 14
            bp.disk(cx, 0, cz, 3, IRON)
            bp.disk(cx, 1, cz, 3, BRASS, hollow=True)
            bp.disk(cx, 1, cz, 2, "water[level=0]")
            bp.disk(cx, 0, cz, 2, IRON)
            for y in (1, 2, 3):
                bp.set(cx, y, cz, W + "copper_pipe[axis=y]")
            bp.set(cx, 4, cz, BRASS)
            bp.set(cx, 5, cz, "water[level=0]")
            for dx, dz in ((4, 0), (-4, 0), (0, 4), (0, -4)):
                bp.set(cx + dx, 1, cz + dz, SMOKE_STAIRS + f"[facing={'west' if dx > 0 else 'east' if dx < 0 else 'north' if dz > 0 else 'south'},half=bottom,shape=straight,waterlogged=false]")
            for dx, dz in ((5, 5), (-5, 5), (5, -5), (-5, -5)):
                px, pz = cx + dx, cz + dz
                if abs(px) < 8 or abs(pz) < 8:
                    continue
                bp.set(px, 0, pz, "moss_block")
                bp.set(px, 1, pz, "flowering_azalea")
                for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    bp.set(px + ddx, 1, pz + ddz, SMOKE_WALL)


def citadel():
    def build(bp):
        plaza(bp)
        gardens(bp)
        chimneys(bp)
        for face in SIDES:
            hall(bp, face)
        tower(bp)
        # light the plaza
        for face in SIDES:
            for a in (9, 31):
                for b in (-7, 7):
                    x, z = _local(face, a, b)
                    bp.set(x, 1, z, IRON)
                    bp.set(x, 2, z, SMOKE_WALL)
                    bp.set(x, 3, z, EDISON)
        # the stair in the tower hall down to the Gearworks and the Clock Vault (lair_grand_clockmaker.py)
        lair_grand_clockmaker.build(bp)
        # ---- the clockwork citizens (wf/denizens.py) still at work: gearwrights and mechanics in the halls,
        # chronometrists in the clock tower, sentinels and two Brass Golems guarding the plaza
        for i, face in enumerate(SIDES):
            x0, z0 = _local(face, 12, -5)
            x1, z1 = _local(face, 29, 5)
            hall_r = ((min(x0, x1), 1, min(z0, z1)), (max(x0, x1), 6, max(z0, z1)))
            INT.populate(bp, [("gearwright", "mechanic", "mechanic", "gearwright")[i],
                              ("mechanic", "gearwright", "chronometrist", "mechanic")[i]],
                         region=hall_r, vtype="savanna", seed=i, folk="clockwork_citizen")
            if i == 0:
                # the master Tinkerer gives contracts in the first workshop hall (wf/npcs.py)
                INT.quest_npc_in(bp, "tinkerer", region=hall_r, seed=1)
            INT.decorate(bp, "steampunk", seed=i, region=hall_r)
        tower_r = ((-T, 1, -T), (T, CLOCK_Y, T))
        INT.populate(bp, ["chronometrist", "gearwright"], region=tower_r, vtype="savanna", seed=9,
                     bell=(9, 1, 0), guard=("brass", (10, 1, -10)), folk="clockwork_citizen")
        INT.brass_golem(bp, *INT.open_spot(bp, (-10, 1, 10)))
        denizens.guards(bp, "clockwork_citizen", [(-10, 1, -10), (-12, 1, 2)])
        INT.decorate(bp, "steampunk", seed=9, region=tower_r)
        INT.decorate(bp, dict(INT.THEMES["workshop"], ceiling="edison"), seed=10, region=((-60, -60, -60), (60, 0, 60)),
                     density=0.2)
    return build


register(StructureDef(
    "clockwork_citadel", "overworld",
    ["#minecraft:is_badlands", "savanna", "savanna_plateau", "windswept_savanna", "desert", "plains"],
    [Piece("citadel", citadel())],
    spacing=64, separation=24, adaptation="beard_box", processors="none", max_distance=100,
    # the clockmakers live here: no natural monster spawns (the Gearworks below keep their spawner and the
    # Grand Clockmaker; runaway automatons still roam the badlands around)
    peaceful=True,
    title_fr="Citadelle d'horlogerie", title_en="Clockwork Citadel"))

"""Inventor's Manor (Manoir de l'inventeur): a Victorian steampunk mansion on the meadows (mega-structure).

Ground y = 0, house floor y = 1, front (south) facade at z = 9:
  * the main house (27 x 19): red brick with dark-iron pilasters, brass bands and window hoods, two storeys
    under a verdigris copper mansard roof with dormers and iron cresting; two polygonal bay windows, a pillared
    porch with a balcony, a round corner turret with a copper cone, a small north-west turret, an observatory
    tower with a copper dome and a brass telescope, three tall smoking chimneys,
  * inside: the study, the hall with its staircase, the dining room (ground floor), the library, the bedroom and
    the parlour (first floor), the attic storeroom, the observatory,
  * the glass conservatory on the east side: copper ribs, raised beds with a Sprinkler and an Auto-Harvester,
    small trees, azaleas and a fountain,
  * the workshop wing on the west side: the inventor's machines, benches and crates,
  * the secret laboratory under the house: a carpet in the study hides a trapdoor and a ladder down to a lab
    with an aether reactor, a tesla coil, specimen tanks, a brewing bench and the inventor's notes (best loot),
  * a front garden behind brick-and-iron railings: gravel paths, a fountain, topiaries, lamp posts.
"""
import math

from ..arch import Palette, stair, slab
from ..defs import Piece, StructureDef, register
from ..parts import LOOT

W = "wayfarers:"
BRASS, COPPER, VERD, IRON = W + "brass_plating", W + "copper_plating", W + "verdigris_plating", W + "dark_iron_plating"
TREAD, GEAR, PIPES, GAUGE = W + "diamond_plate", W + "gear_panel", W + "copper_pipes", W + "pressure_gauge"
EDISON, AETHER = W + "edison_lamp", W + "aether_conduit"
MAHOG, SMOKE = W + "mahogany_panelling", W + "smokestack_bricks"
MAHOG_ST, BRASS_ST = W + "mahogany_panelling_stairs", W + "brass_plating_stairs"
IRON_WALL = W + "dark_iron_plating_wall"
SMOKE_WALL = W + "smokestack_brick_wall"
ROOF, ROOF_ST, ROOF_SLAB = "weathered_cut_copper", "weathered_cut_copper_stairs", "weathered_cut_copper_slab"
OXI, OXI_ST = "oxidized_cut_copper", "oxidized_cut_copper_stairs"
BRICK = Palette({"bricks": 7, SMOKE: 2, "mud_bricks": 1}, seed=3, scale=2.5)
PLINTH = "polished_andesite"

X0, X1, Z0, Z1 = -14, 12, -9, 9    # main block walls
F0, F1, F2 = 1, 7, 13              # floors
TOP = 13                           # cornice / attic floor


def machine(name, facing="north"):
    return f"{W}{name}[facing={facing},powered=false]"


def _hood(face):
    return {"south": "north", "north": "south", "east": "west", "west": "east"}[face]


# ------------------------------------------------------------------ main block
def shell(bp):
    """Walls, floors, pilasters, windows, bands and cornice of the main block."""
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            edge = x in (X0, X1) or z in (Z0, Z1)
            bp.set(x, 0, z, PLINTH)
            for y in range(1, TOP):
                if edge:
                    if y <= 1:
                        bp.set(x, y, z, PLINTH)
                    else:
                        bp.set(x, y, z, BRICK.pick(x, y, z))
                else:
                    bp.set(x, y, z, "air")
            if not edge:
                bp.set(x, F0, z, "dark_oak_planks" if (x + z) % 2 else "spruce_planks")
                bp.set(x, F1, z, "dark_oak_planks" if (x * 3 + z) % 4 else "stripped_dark_oak_wood[axis=x]")
                bp.set(x, F2, z, "spruce_planks")
    # four faces: pilasters, windows with brass hoods and mahogany sills, copper floor band, brass cornice
    faces = (("south", Z1, X0, X1), ("north", Z0, X0, X1), ("east", X1, Z0, Z1), ("west", X0, Z0, Z1))
    for face, line, u0, u1 in faces:
        for u in range(u0, u1 + 1):
            x, z, ox, oz = _at(face, line, u, 0)
            for y in (F1, TOP - 1):
                bp.set(x, y, z, COPPER if y == F1 else BRASS)
            bp.set(x + ox, TOP, z + oz, stair(MAHOG_ST, _hood(face), "top"))
            bp.set(x + ox, 1, z + oz, stair("polished_andesite_stairs", _hood(face)))
            k = (u - u0) % 4
            corner = u in (u0, u1)
            if corner or k == 0:
                for y in range(2, TOP):
                    bp.set(x, y, z, IRON)
                    if not corner:
                        bp.set(x + ox, y, z + oz, IRON if y not in (F1, TOP - 1) else BRASS)
                continue
            if k == 2:
                for (y0, y1) in ((3, 5), (9, 11)):
                    for y in range(y0, y1 + 1):
                        bp.set(x, y, z, "glass_pane")
                    bp.set(x + ox, y1 + 1, z + oz, stair(BRASS_ST, _hood(face), "top"))
                    bp.set(x + ox, y0 - 1, z + oz, stair(MAHOG_ST, _hood(face), "top"))


def _at(face, line, u, out):
    """World (x, z) of a facade cell plus the outward unit vector."""
    if face == "south":
        return u, line + out, 0, 1
    if face == "north":
        return u, line - out, 0, -1
    if face == "east":
        return line + out, u, 1, 0
    return line - out, u, -1, 0


def mansard(bp):
    """Steep verdigris copper mansard with a flat top, iron cresting and dormers."""
    for y in range(TOP + 1, TOP + 7):
        i = (y - TOP - 1) // 2
        steep = (y - TOP - 1) % 2 == 1
        for x in range(X0 + i, X1 - i + 1):
            for z in range(Z0 + i, Z1 - i + 1):
                edge = x in (X0 + i, X1 - i) or z in (Z0 + i, Z1 - i)
                if not edge:
                    bp.set(x, y, z, "air")
                    continue
                if steep:
                    f = "south" if z == Z0 + i else "north" if z == Z1 - i else "east" if x == X0 + i else "west"
                    bp.set(x, y, z, stair(ROOF_ST, f))
                else:
                    bp.set(x, y, z, ROOF)
    yt = TOP + 7
    i = 3
    for x in range(X0 + i, X1 - i + 1):
        for z in range(Z0 + i, Z1 - i + 1):
            edge = x in (X0 + i, X1 - i) or z in (Z0 + i, Z1 - i)
            bp.set(x, yt - 1, z, OXI if edge else "spruce_planks")
            bp.set(x, yt, z, slab("oxidized_cut_copper_slab"))
            if edge:
                bp.set(x, yt + 1, z, "iron_bars")
    for (x, z) in ((X0 + i, Z0 + i), (X1 - i, Z0 + i), (X0 + i, Z1 - i), (X1 - i, Z1 - i)):
        bp.set(x, yt + 1, z, BRASS)
        bp.set(x, yt + 2, z, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # dormers on the long sides
    for face, line in (("south", Z1), ("north", Z0)):
        for u in (X0 + 4, X0 + 10, X1 - 10, X1 - 4):
            if face == "south" and abs(u - (-1)) <= 2:
                continue
            x, z, ox, oz = _at(face, line, u, 0)
            for du in (-1, 0, 1):
                for y in range(TOP + 1, TOP + 5):
                    glass = du == 0 and y in (TOP + 2, TOP + 3)
                    bp.set(x + du, y, z, "glass_pane" if glass else MAHOG)
                for dz in range(0, 3):
                    bp.set(x + du, TOP + 5, z - oz * dz, stair(ROOF_ST, "east" if du < 0 else "west") if du else ROOF)
            bp.set(x, TOP + 6, z, slab(ROOF_SLAB))
            for dz in range(1, 3):
                for du in (-1, 0, 1):
                    for y in range(TOP + 1, TOP + 5):
                        if bp.get(x + du, y, z - oz * dz) in (None, "minecraft:air"):
                            bp.set(x + du, y, z - oz * dz, MAHOG if abs(du) == 1 else "air")


def bay(bp, xc, floors_top=TOP - 1):
    """A polygonal two-storey bay window on the south facade, capped by a copper cone."""
    z = Z1
    for y in range(1, floors_top + 1):
        for (dx, dz) in ((-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)):
            x = xc + dx
            band = y in (1, F1, floors_top)
            glass = (y in (3, 4, 5, 9, 10, 11))
            bp.set(x, y, z + dz, PLINTH if y == 1 else (BRASS if band else ("glass_pane" if glass and abs(dx) < 2
                                                                               else IRON)))
        for dx in (-1, 0, 1):
            bp.set(xc + dx, y, z + 1, "air" if y not in (1, F1) else ("spruce_planks" if y == F1 else PLINTH))
        bp.set(xc, y, z, "air" if y not in (1, F1, floors_top) else bp.get(xc, y, z))
        for dx in (-1, 1):
            if y not in (1, F1, floors_top):
                bp.set(xc + dx, y, z, "air")
    for dx in (-1, 0, 1):
        bp.set(xc + dx, F0, z, "dark_oak_planks")
        bp.set(xc + dx, F0, z + 1, "dark_oak_planks")
    # cap
    y = floors_top + 1
    for (dx, dz, f) in ((-2, 1, "east"), (2, 1, "west"), (-1, 2, "north"), (0, 2, "north"), (1, 2, "north")):
        bp.set(xc + dx, y, z + dz, stair(OXI_ST, f))
    for dx in (-1, 0, 1):
        bp.set(xc + dx, y, z + 1, OXI)
        bp.set(xc + dx, y + 1, z + 1, stair(OXI_ST, "north"))
    bp.set(xc, y + 2, z + 1, slab("oxidized_cut_copper_slab"))


def porch(bp):
    xc = -1
    for x in range(xc - 4, xc + 5):
        for z in range(Z1 + 1, Z1 + 5):
            bp.set(x, 0, z, PLINTH)
            bp.set(x, 1, z, "polished_andesite" if (x + z) % 2 else "andesite")
        bp.set(x, 1, Z1 + 5, stair("polished_andesite_stairs", "north"))
        bp.set(x, 0, Z1 + 5, PLINTH)
    for (x, z) in ((xc - 4, Z1 + 4), (xc + 4, Z1 + 4), (xc - 4, Z1 + 1), (xc + 4, Z1 + 1)):
        for y in range(2, 6):
            bp.set(x, y, z, IRON_WALL)
        bp.set(x, 6, z, BRASS)
    for x in range(xc - 5, xc + 6):
        for z in range(Z1 + 1, Z1 + 6):
            edge = x in (xc - 5, xc + 5) or z == Z1 + 5
            bp.set(x, 6, z, stair(OXI_ST, "north" if z == Z1 + 5 else ("east" if x == xc - 5 else "west")) if edge
                   else ROOF)
            if not edge:
                bp.set(x, 7, z, slab("spruce_slab"))
                if x in (xc - 4, xc + 4) or z == Z1 + 4:
                    bp.set(x, 8, z, "iron_bars")
    bp.set(xc, 5, Z1 + 3, W + "hanging_edison_lamp")
    # front door with sidelights, balcony door above
    for y in (2, 3):
        bp.set(xc, y, Z1, "air")
    bp.door(xc, 2, Z1, "south", "dark_oak")
    for dx in (-1, 1):
        for y in (2, 3, 4):
            bp.set(xc + dx, y, Z1, "glass_pane" if y < 4 else BRASS)
    bp.set(xc, 4, Z1, GEAR)
    for y in (8, 9):
        bp.set(xc, y, Z1, "air")
    bp.door(xc, 8, Z1, "south", "spruce")
    bp.set(xc, 10, Z1, BRASS)
    bp.set(xc, 6, Z1 + 1, ROOF)


def turret(bp, cx, cz, r, h, cone_h):
    """Round brick turret with brass bands, windows on every floor and a verdigris copper cone."""
    for y in range(0, h + 1):
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.4:
                    if d > r - 0.6:
                        band = y in (F1, TOP - 1, h)
                        bp.set(x, y, z, PLINTH if y <= 1 else (BRASS if band else BRICK.pick(x, y, z)))
                    elif y in (0, F0, F1, TOP, h - 1):
                        bp.set(x, y, z, "spruce_planks" if y else PLINTH)
                    else:
                        bp.set(x, y, z, "air")
    for (y0, y1) in ((3, 5), (9, 11), (TOP + 2, TOP + 4)):
        for a in range(0, 360, 60):
            x, z = cx + round(math.cos(math.radians(a)) * r), cz + round(math.sin(math.radians(a)) * r)
            for y in range(y0, min(y1, h - 1) + 1):
                bp.set(x, y, z, "glass_pane")
    # corbelled eave and the cone
    for a in range(0, 360, 4):
        x, z = cx + round(math.cos(math.radians(a)) * (r + 1)), cz + round(math.sin(math.radians(a)) * (r + 1))
        if math.hypot(x - cx, z - cz) > r + 0.5:
            bp.set(x, h, z, stair(BRASS_ST, _toward(x - cx, z - cz), "top"))
    rr = r + 1
    y = h + 1
    step = cone_h / (r + 1)
    while rr >= 0:
        for x in range(cx - rr - 1, cx + rr + 2):
            for z in range(cz - rr - 1, cz + rr + 2):
                d = math.hypot(x - cx, z - cz)
                if rr - 0.7 < d <= rr + 0.4:
                    for k in range(int(round(step))):
                        last = k == int(round(step)) - 1
                        bp.set(x, y + k, z, stair(OXI_ST, _toward(cx - x, cz - z)) if last else OXI)
                elif d <= rr - 0.7:
                    for k in range(int(round(step))):
                        bp.set(x, y + k, z, OXI if rr < 2 else "air")
        y += int(round(step))
        rr -= 1
    bp.set(cx, y, cz, BRASS)
    bp.set(cx, y + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    return y


def _toward(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


def observatory(bp):
    x0, x1, z0, z1 = -5, 1, -8, -2
    base, top = TOP + 1, TOP + 12
    for y in range(base, top + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                if corner:
                    bp.set(x, y, z, IRON)
                elif edge:
                    win = y in (top - 3, top - 2) and (x + z) % 2 == 0
                    bp.set(x, y, z, BRASS if y in (top, base + 6) else ("glass_pane" if win else BRICK.pick(x, y, z)))
                else:
                    bp.set(x, y, z, "air")
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            bp.set(x, base + 6, z, TREAD)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            if x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1):
                bp.set(x, top, z, stair(BRASS_ST, _toward(cx - x, cz - z), "top") if not (x in (x0 - 1, x1 + 1)
                                                                                         and z in (z0 - 1, z1 + 1))
                       else BRASS)
    R = 4
    for x in range(cx - R - 1, cx + R + 2):
        for z in range(cz - R - 1, cz + R + 2):
            for y in range(top + 1, top + R + 2):
                d = math.sqrt((x - cx) ** 2 + (y - top) ** 2 + (z - cz) ** 2)
                if R - 0.6 < d <= R + 0.4:
                    rib = x == cx or z == cz
                    bp.set(x, y, z, BRASS if rib else OXI)
                elif d <= R - 0.6:
                    bp.set(x, y, z, "air")
    # the slit and the telescope pointing south-east at the sky
    for k in range(0, 6):
        bp.set(cx + k // 2, top + 1 + k // 2 + 1, cz + k // 2, "air")
    for k in range(0, 7):
        bp.set(cx + k // 2, top + 1 + k // 2, cz + (k + 1) // 2, BRASS if k in (0, 6) else COPPER)
    bp.set(cx, base + 7, cz, IRON)
    bp.set(cx - 1, base + 7, cz - 1, "lectern[facing=south,has_book=false,powered=false]")
    bp.set(cx + 1, base + 7, cz + 1, W + "mahogany_chair[facing=north]")
    bp.set(cx, top + R, cz, BRASS)
    bp.set(cx, top + R + 1, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.ladder(x1 - 1, TOP + 1, z1 - 1, base + 6, "north")
    bp.set(x1 - 1, base + 6, z1 - 1, "ladder[facing=north,waterlogged=false]")


def chimney(bp, x, z, top):
    for y in range(1, top + 1):
        for dx in (0, 1):
            for dz in (0, 1):
                bp.set(x + dx, y, z + dz, BRASS if y % 7 == 0 and y > TOP else SMOKE)
    for dx in (-1, 0, 1, 2):
        for dz in (-1, 0, 1, 2):
            if dx in (-1, 2) or dz in (-1, 2):
                bp.set(x + dx, top - 1, z + dz, stair(W + "smokestack_brick_stairs", _toward(-(dx - 0.5), -(dz - 0.5)),
                                                      "top"))
    bp.set(x, top, z, "hay_block[axis=y]")
    bp.set(x, top + 1, z, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    bp.set(x + 1, top, z + 1, SMOKE_WALL)
    bp.set(x + 1, top, z, SMOKE_WALL)
    bp.set(x, top, z + 1, SMOKE_WALL)


# ------------------------------------------------------------------ interiors
def interiors(bp):
    # ground floor partitions: study (west) | hall | dining room (east)
    for z in range(Z0 + 1, Z1):
        for y in range(F0 + 1, F1):
            for x in (-6, 3):
                door = abs(z - 2) <= 0 and y <= F0 + 2
                bp.set(x, y, z, "air" if door else MAHOG)
    for x in (-6, 3):
        bp.door(x, F0 + 1, 2, "east" if x > 0 else "west", "dark_oak")
    # grand staircase in the hall, against the back wall, rising east
    for i in range(6):
        x = -5 + i
        for z in (Z0 + 1, Z0 + 2):
            bp.set(x, F0 + 1 + i, z, stair("dark_oak_stairs", "east"))
            for y in range(F0 + 1, F0 + 1 + i):
                bp.set(x, y, z, "dark_oak_planks")
        for z in (Z0 + 1, Z0 + 2):
            for y in range(F0 + 2 + i, F0 + 5 + i):
                if y >= F1:
                    bp.set(x, y, z, "air")
        bp.set(x, F0 + 2 + i, Z0 + 3, f"{W}brass_railing[facing=south]")
    bp.set(-1, F1 - 1, 3, W + "brass_chandelier")
    bp.set(-1, F0 + 1, 5, "red_carpet")
    for x in (-3, 1):
        bp.set(x, F0 + 1, 7, "potted_fern")
    bp.set(-4, F0 + 1, 5, "wayfarers:mahogany_table")
    # the study: desk, bookshelves, globe, the carpet hiding the trapdoor
    for z in range(Z0 + 1, Z1):
        for y in range(F0 + 1, F0 + 4):
            if z != 2:
                bp.set(X0 + 1, y, z, "bookshelf" if (z + y) % 5 else "chiseled_bookshelf[facing=east]")
    bp.set(-9, F0 + 1, 4, W + "mahogany_table")
    bp.set(-9, F0 + 1, 5, f"{W}mahogany_chair[facing=north]")
    bp.set(-8, F0 + 1, 4, W + "mahogany_table")
    bp.set(-8, F0 + 2, 4, "lantern[hanging=false,waterlogged=false]")
    bp.set(-11, F0 + 1, 7, "cartography_table")
    bp.set(-7, F0 + 1, 7, "lectern[facing=north,has_book=false,powered=false]")
    bp.chest(-7, F0 + 1, Z0 + 1, "south", loot=LOOT + "inventor_manor")
    bp.set(-10, F1 - 1, 1, W + "hanging_edison_lamp")
    tx, tz = -10, -5
    bp.set(tx, F0, tz, "dark_oak_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    bp.set(tx, F0 + 1, tz, "red_carpet")
    for dx in (-1, 1):
        bp.set(tx + dx, F0 + 1, tz, "red_carpet")
        bp.set(tx, F0 + 1, tz + dx, "red_carpet")
    # the dining room
    for x in range(5, 11):
        bp.set(x, F0 + 1, 1, W + "mahogany_table")
        bp.set(x, F0 + 1, 0, f"{W}mahogany_chair[facing=south]")
        bp.set(x, F0 + 1, 2, f"{W}mahogany_chair[facing=north]")
    bp.set(7, F1 - 1, 1, W + "brass_chandelier")
    for x in range(5, 11):
        bp.set(x, F0 + 1, Z0 + 1, "barrel[facing=up,open=false]" if x % 3 == 0 else W + "wall_shelf[facing=south]")
    bp.barrel(10, F0 + 1, Z0 + 1, "up", loot=LOOT + "inventor_manor")
    bp.set(4, F0 + 1, 7, "smoker[facing=east,lit=false]")
    # first floor: library (west), parlour (centre), bedroom (east)
    for z in range(Z0 + 1, Z1):
        for y in range(F1 + 1, TOP):
            for x in (-6, 3):
                door = z == 2 and y <= F1 + 2
                bp.set(x, y, z, "air" if door else MAHOG)
    for x in (-6, 3):
        bp.door(x, F1 + 1, 2, "east" if x > 0 else "west", "spruce")
    for x in range(X0 + 1, -6):
        for y in range(F1 + 1, F1 + 4):
            bp.set(x, y, Z0 + 1, "bookshelf")
            bp.set(x, y, Z1 - 1, "bookshelf" if x % 3 else "chiseled_bookshelf[facing=north]")
    bp.set(-10, F1 + 1, 2, "enchanting_table")
    bp.set(-9, F1 + 1, 0, W + "mahogany_chair[facing=west]")
    bp.chest(-12, F1 + 1, 2, "east", loot=LOOT + "inventor_manor")
    bp.set(-10, TOP - 1, 2, W + "hanging_edison_lamp")
    bp.bed(8, F1 + 1, Z0 + 1, "south", "red")
    bp.set(7, F1 + 1, Z0 + 1, "barrel[facing=up,open=false]")
    bp.set(10, F1 + 1, Z0 + 1, W + "mahogany_table")
    bp.set(10, F1 + 2, Z0 + 1, "lantern[hanging=false,waterlogged=false]")
    bp.set(6, F1 + 1, 6, "red_carpet")
    bp.set(7, F1 + 1, 6, "red_carpet")
    bp.set(9, F1 + 1, 4, W + "mahogany_chair[facing=west]")
    bp.set(7, TOP - 1, 1, W + "hanging_edison_lamp")
    bp.set(-1, F1 + 1, 4, "jukebox[has_record=false]")
    for x in (-3, 1):
        bp.set(x, F1 + 1, 5, W + "mahogany_chair[facing=" + ("east" if x < 0 else "west") + "]")
    bp.set(-1, F1 + 1, 6, "red_carpet")
    bp.set(-1, TOP - 1, 4, W + "brass_chandelier")
    # attic: storeroom with crates and a ladder to the observatory
    for x in range(-11, -6):
        bp.set(x, TOP + 1, 0, W + "compacting_crate[facing=south]" if x % 2 else "barrel[facing=up,open=false]")
    bp.barrel(-11, TOP + 1, 1, "up", loot=LOOT + "inventor_manor")
    bp.set(6, TOP + 1, 0, W + "mahogany_table")
    bp.set(6, TOP + 2, 0, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    # stair from the first floor to the attic, along the north wall
    for i in range(6):
        x = 2 - i
        for z in (Z0 + 1,):
            bp.set(x, F1 + 1 + i, z + 1, stair("spruce_stairs", "west"))
            for y in range(F1 + 2 + i, F1 + 5 + i):
                if y >= TOP:
                    bp.set(x, y, z + 1, "air")


# ------------------------------------------------------------------ conservatory, workshop, lab
def conservatory(bp):
    x0, x1, z0, z1 = X1 + 1, X1 + 17, -7, 4
    h = 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x == x1 or z in (z0, z1)
            bp.set(x, 0, z, PLINTH)
            bp.set(x, 1, z, PLINTH if edge else ("mossy_cobblestone" if (x + z) % 3 == 0 else "moss_block"))
            for y in range(2, h + 1):
                if edge:
                    post = (x - x0) % 4 == 0 and z in (z0, z1) or x == x1 and ((z - z0) % 4 == 0 or z == z1)
                    bp.set(x, y, z, "oxidized_copper" if post else ("glass" if y > 2 else "bricks"))
                elif x != x0 - 1:
                    bp.set(x, y, z, "air")
    # barrel-vault glass roof on copper ribs
    w = (z1 - z0) / 2
    zc = (z0 + z1) / 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            yy = h + round(math.sqrt(max(0.0, w * w - (z - zc) ** 2)) * 0.7)
            for y in range(h + 1, yy + 1):
                bp.set(x, y, z, "air")
            rib = (x - x0) % 4 == 0 or x == x1
            bp.set(x, yy + 1, z, "oxidized_cut_copper" if rib else "glass")
    for x in range(x0, x1 + 1):
        bp.set(x, h + 1 + round(w * 0.7), round(zc), BRASS)
    # raised beds with crops, a sprinkler and an auto-harvester
    for (bx0, bz0) in ((x0 + 2, z0 + 2), (x0 + 9, z0 + 2)):
        for x in range(bx0, bx0 + 5):
            for z in range(bz0, bz0 + 3):
                edge = x in (bx0, bx0 + 4) or z in (bz0, bz0 + 2)
                bp.set(x, 1, z, "spruce_planks" if edge else "farmland[moisture=7]")
                bp.set(x, 2, z, "spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"
                       if edge else ["wheat[age=7]", "carrots[age=7]", "potatoes[age=7]"][(x + bx0) % 3])
        bp.set(bx0 + 2, 2, bz0 + 1, "farmland[moisture=7]")
        bp.set(bx0 + 2, 1, bz0 + 1, "spruce_planks")
        bp.set(bx0 + 2, 2, bz0 + 1, machine("sprinkler", "up") if bx0 == x0 + 2 else machine("auto_harvester", "up"))
    bp.chest(x0 + 13, 2, z0 + 3, "west", loot=LOOT + "inventor_manor")
    # azaleas, ferns, little trees, a fountain
    for (x, z) in ((x0 + 3, z1 - 2), (x0 + 7, z1 - 1), (x0 + 12, z1 - 2), (x1 - 2, z0 + 1)):
        bp.set(x, 1, z, "moss_block")
        bp.set(x, 2, z, "flowering_azalea")
    for (x, z) in ((x0 + 5, z1 - 1), (x0 + 10, z1 - 1), (x0 + 1, z0 + 1), (x1 - 1, z1 - 1)):
        bp.set(x, 1, z, "moss_block")
        bp.set(x, 2, z, "fern")
    for (x, z) in ((x1 - 2, z1 - 2),):
        for y in range(2, 6):
            bp.set(x, y, z, "birch_log[axis=y]")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in (5, 6, 7):
                    if (dx or dz or y == 7) and abs(dx) + abs(dz) + (y - 5) <= 3:
                        bp.set(x + dx, y, z + dz, "birch_leaves[distance=1,persistent=true,waterlogged=false]")
    fx, fz = x0 + 8, z1 - 2
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bp.set(fx + dx, 1, fz + dz, COPPER if (dx or dz) else "water[level=0]")
            bp.set(fx + dx, 0, fz + dz, PLINTH)
    bp.set(fx, 0, fz, "copper_block")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(fx + dx, 1, fz + dz, "water[level=0]")
    bp.set(fx + 1, 1, fz + 1, COPPER)
    for y in (h,):
        for x in (x0 + 4, x0 + 12):
            bp.set(x, h + 3, round(zc), W + "hanging_edison_lamp")
    # the door from the dining room
    for y in (2, 3):
        bp.set(X1, y, 0, "air")
    bp.door(X1, 2, 0, "east", "spruce")


def workshop(bp):
    x0, x1, z0, z1 = X0 - 15, X0 - 2, -6, 6
    h = 6
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            bp.set(x, 0, z, PLINTH)
            bp.set(x, 1, z, PLINTH if edge else TREAD)
            for y in range(2, h + 1):
                if edge:
                    pil = (x - x0) % 4 == 0 or x in (x0, x1) and z in (z0, z1)
                    bp.set(x, y, z, IRON if pil else (BRASS if y == h else BRICK.pick(x, y, z)))
                else:
                    bp.set(x, y, z, "air")
    # gable roof along x, slate-like copper
    for k in range(0, 8):
        y = h + 1 + k
        for x in range(x0 - 1, x1 + 2):
            for z, f in ((z0 - 1 + k, "south"), (z1 + 1 - k, "north")):
                if z0 - 1 + k > z1 + 1 - k:
                    continue
                if z0 - 1 + k == z1 + 1 - k:
                    bp.set(x, y, z, ROOF)
                else:
                    bp.set(x, y, z, stair(ROOF_ST, f))
            if x in (x0, x1):
                for z in range(z0 - 1 + k + 1, z1 + 1 - k):
                    bp.set(x, y, z, BRICK.pick(x, y, z))
            elif x0 < x < x1:
                for z in range(z0 - 1 + k + 1, z1 + 1 - k):
                    bp.set(x, y, z, "air")
    # big doors to the yard and a round window in each gable
    for x in range(x0 + 5, x0 + 9):
        for y in range(2, 6):
            bp.set(x, y, z1, "air")
    for x in range(x0 + 4, x0 + 10):
        bp.set(x, 6, z1, BRASS)
    for y in range(2, 6):
        bp.set(x0 + 4, y, z1, IRON)
        bp.set(x0 + 9, y, z1, IRON)
    for (x, y) in ((x0, h + 3), (x1, h + 3)):
        bp.set(x, y, 0, GEAR)
    # passage to the house
    for x in range(x1, X0 + 1):
        for z in (-1, 0, 1):
            bp.set(x, 1, z, TREAD)
            for y in range(2, 5):
                bp.set(x, y, z, "air")
            bp.set(x, 5, z, COPPER)
        for z in (-2, 2):
            for y in range(1, 5):
                bp.set(x, y, z, BRICK.pick(x, y, z))
            bp.set(x, 5, z, BRASS)
    bp.door(X0, 2, 0, "west", "dark_oak")
    # the machines
    machines = ["block_breaker", "block_placer", "redstone_timer", "vacuum_hopper", "wireless_transmitter",
                "wireless_receiver", "entity_detector"]
    for i, m in enumerate(machines):
        x = x0 + 2 + i * 2 if i < 4 else x0 + 2 + (i - 4) * 3
        z = z0 + 1 if i < 4 else z0 + 4
        bp.set(x, 2, z, machine(m, "south"))
        if i < 4:
            bp.set(x + 1, 2, z, W + "mahogany_table")
    for x in range(x0 + 1, x1):
        if x % 3 == 0:
            bp.set(x, h, 0, IRON)
            bp.set(x, h - 1, 0, W + "hanging_edison_lamp")
    bp.set(x1 - 2, 2, z1 - 1, "anvil[facing=east]")
    bp.set(x1 - 3, 2, z1 - 1, "smithing_table")
    bp.set(x1 - 4, 2, z1 - 1, "crafting_table")
    bp.set(x1 - 1, 2, z0 + 1, W + "compacting_crate[facing=south]")
    bp.set(x1 - 1, 3, z0 + 1, W + "compacting_crate[facing=south]")
    bp.chest(x1 - 1, 2, z0 + 2, "west", loot=LOOT + "inventor_manor")
    bp.set(x0 + 1, 2, z1 - 1, "blast_furnace[facing=east,lit=false]")
    bp.set(x0 + 1, 2, z1 - 2, "grindstone[face=floor,facing=east]")
    for z in range(z0 + 1, z1):
        bp.set(x0 + 1, 4, z, PIPES if z % 2 else GAUGE)


def laboratory(bp):
    x0, x1, z0, z1 = -13, 9, -8, 6
    y0, y1 = -9, -2
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, y1 + 2):
                edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1) or y in (y0 - 1, y1 + 1)
                if edge:
                    bp.set(x, y, z, "deepslate_tiles" if y in (y0 - 1, y1 + 1) else (COPPER if y < y0 + 2 else IRON))
                elif y == y0:
                    bp.set(x, y, z, TREAD if (x + z) % 2 else IRON)
                else:
                    bp.set(x, y, z, "air")
    for x in range(x0, x1 + 1, 4):
        for z in (z0, z1):
            for y in range(y0 + 1, y1 + 1):
                bp.set(x, y, z, BRASS if y == y1 else PIPES)
    # ladder from the study trapdoor
    tx, tz = -10, -5
    for y in range(y0 + 1, F0):
        bp.set(tx, y, tz, "ladder[facing=south,waterlogged=false]")
        bp.set(tx, y, tz - 1, IRON)
    # the aether reactor: a glowing crystal core in a glass tank wrapped in copper
    rx, rz = -2, -1
    for y in range(y0 + 1, y1 + 1):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    bp.set(rx, y, rz, W + "aether_block" if y in (y0 + 3, y0 + 4) else AETHER)
                else:
                    bp.set(rx + dx, y, rz + dz, "glass" if y not in (y0 + 1, y1) else COPPER)
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        bp.set(rx + dx, y0 + 1, rz + dz, GEAR)
        bp.set(rx + dx, y0 + 2, rz + dz, GAUGE)
    # tesla coil
    tcx, tcz = 5, -4
    bp.set(tcx, y0 + 1, tcz, "copper_block")
    bp.set(tcx, y0 + 2, tcz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(tcx, y0 + 3, tcz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    bp.set(tcx, y0 + 4, tcz, "copper_bulb[lit=true,powered=false]")
    bp.set(tcx, y0 + 5, tcz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bp.set(tcx + dx, y0 + 1, tcz + dz, "cut_copper_slab[type=bottom,waterlogged=false]")
    # specimen tanks
    for i, sx in enumerate((x0 + 1, x0 + 3, x0 + 5)):
        sz = z1 - 1
        bp.set(sx, y0 + 1, sz, COPPER)
        for y in (y0 + 2, y0 + 3, y0 + 4):
            bp.set(sx, y, sz, "water[level=0]")
        specimen = ["sea_pickle[pickles=3,waterlogged=true]", "kelp_plant", "tube_coral[waterlogged=true]"][i]
        bp.set(sx, y0 + 2, sz, specimen)
        bp.set(sx, y0 + 5, sz, COPPER)
        for (dx, dz) in ((1, 0), (-1, 0), (0, -1)):
            for y in (y0 + 2, y0 + 3, y0 + 4):
                if bp.get(sx + dx, y, sz + dz) == "minecraft:air":
                    bp.set(sx + dx, y, sz + dz, "glass")
    # benches, brewing, machines, notes
    for x in range(x1 - 6, x1 + 1):
        bp.set(x, y0 + 1, z1, W + "mahogany_table" if x % 2 else "crafting_table")
    bp.set(x1 - 5, y0 + 2, z1, "brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    bp.set(x1 - 3, y0 + 2, z1, "lantern[hanging=false,waterlogged=false]")
    bp.set(x1, y0 + 1, z0 + 2, machine("entity_detector", "west"))
    bp.set(x1, y0 + 1, z0 + 3, machine("wireless_receiver", "west"))
    bp.set(x1, y0 + 1, z0 + 4, machine("vacuum_hopper", "west"))
    bp.set(x1, y0 + 1, z0 + 5, "redstone_block")
    bp.set(x1, y0 + 2, z0 + 5, "redstone_lamp[lit=true]")
    bp.set(x0, y0 + 1, z0 + 2, "lectern[facing=east,has_book=false,powered=false]")
    for z in range(z0 + 3, z0 + 6):
        bp.set(x0, y0 + 3, z, "black_wall_banner[facing=east]")
    bp.chest(x0, y0 + 1, z0 + 4, "east", loot=LOOT + "inventor_lab")
    bp.chest(x1, y0 + 1, z1 - 1, "west", loot=LOOT + "inventor_lab")
    for (x, z) in ((-8, 0), (3, 2), (-2, 4)):
        bp.set(x, y1, z, W + "hanging_edison_lamp")


# ------------------------------------------------------------------ the garden
def garden(bp):
    gx0, gx1, gz0, gz1 = -31, 31, -13, 25
    for x in range(gx0, gx1 + 1):
        for z in range(gz0, gz1 + 1):
            if bp.get(x, 0, z) is None:
                bp.set(x, 0, z, "grass_block[snowy=false]")
    # railings: brick posts and iron bars on the front and the sides
    for x in range(gx0, gx1 + 1):
        post = (x - gx0) % 6 == 0
        if abs(x + 1) <= 2:
            continue
        bp.set(x, 1, gz1, "bricks" if post else PLINTH)
        bp.set(x, 2, gz1, "bricks" if post else "iron_bars")
        if post:
            bp.set(x, 3, gz1, "stone_brick_slab[type=bottom,waterlogged=false]")
    for z in range(gz0, gz1 + 1):
        for x in (gx0, gx1):
            post = (z - gz0) % 6 == 0
            bp.set(x, 1, z, "bricks" if post else PLINTH)
            bp.set(x, 2, z, "bricks" if post else "iron_bars")
    for x in (-4, 2):
        for y in range(1, 5):
            bp.set(x, y, gz1, "bricks" if y < 4 else BRASS)
        bp.set(x, 5, gz1, "lantern[hanging=false,waterlogged=false]")
    for x in (-3, -2, -1, 0, 1):
        bp.set(x, 4, gz1, "iron_bars" if x != -1 else GEAR)
    # gravel paths to the porch, the workshop and the conservatory, a fountain in the middle
    for z in range(Z1 + 6, gz1 + 1):
        for x in range(-3, 2):
            bp.set(x, 0, z, "gravel" if abs(x + 1) < 2 else "polished_andesite")
    fx, fz = -1, 19
    for x in range(fx - 4, fx + 5):
        for z in range(fz - 4, fz + 5):
            d = math.hypot(x - fx, z - fz)
            if d <= 4.4:
                bp.set(x, 0, z, PLINTH if d > 3.4 else "water[level=0]")
                if 3.4 < d:
                    bp.set(x, 1, z, "polished_andesite_slab[type=bottom,waterlogged=false]")
                else:
                    bp.set(x, -1, z, PLINTH)
    bp.set(fx, 0, fz, COPPER)
    bp.set(fx, 1, fz, "water[level=0]")
    for y in (1, 2):
        bp.set(fx, y, fz, VERD)
    bp.set(fx, 3, fz, "water[level=0]")
    bp.set(fx, 2, fz, VERD)
    for z in range(-2, 3):
        for x in range(X0 - 16, X0 - 1):
            if bp.get(x, 0, z + 9) == "minecraft:grass_block":
                bp.set(x, 0, z + 9, "gravel")
    # flower beds, topiaries and lamp posts
    for (x, z) in ((-12, 14), (10, 14), (-12, 21), (10, 21), (-22, 18), (20, 18)):
        bp.set(x, 1, z, "spruce_fence")
        for (dx, dy, dz) in ((0, 2, 0), (1, 2, 0), (-1, 2, 0), (0, 2, 1), (0, 2, -1), (0, 3, 0)):
            bp.set(x + dx, dy, z + dz, "oak_leaves[distance=1,persistent=true,waterlogged=false]")
    flowers = ["red_tulip", "poppy", "rose_bush", "peony", "allium", "cornflower", "oxeye_daisy"]
    for x in range(-28, 29):
        for z in range(11, 24):
            if bp.get(x, 0, z) == "minecraft:grass_block" and bp.get(x, 1, z) is None and abs(x + 1) > 4:
                if (x % 7 in (1, 2)) and z in (12, 13, 22, 23):
                    f = flowers[(x + z) % len(flowers)]
                    if f in ("rose_bush", "peony"):
                        bp.set(x, 1, z, f"{f}[half=lower]")
                        bp.set(x, 2, z, f"{f}[half=upper]")
                    else:
                        bp.set(x, 1, z, f)
                elif (x * 7 + z * 13) % 11 == 0:
                    bp.set(x, 1, z, "short_grass")
    for (x, z) in ((-4, 12), (2, 12), (-4, 16), (2, 16), (-4, 22), (2, 22), (-20, 9), (20, 9)):
        bp.set(x, 1, z, IRON)
        bp.set(x, 2, z, IRON_WALL)
        bp.set(x, 3, z, IRON_WALL)
        bp.set(x, 4, z, EDISON)


def manor(bp):
    shell(bp)
    mansard(bp)
    bay(bp, -9)
    bay(bp, 6)
    porch(bp)
    interiors(bp)
    laboratory(bp)
    turret(bp, X1, Z1, 4, TOP + 6, 9)
    turret(bp, X0, Z0, 3, TOP + 3, 7)
    observatory(bp)
    chimney(bp, X0 + 3, -2, TOP + 12)
    chimney(bp, 9, -6, TOP + 11)
    chimney(bp, -9, 6, TOP + 9)
    conservatory(bp)
    workshop(bp)
    garden(bp)


register(StructureDef(
    "inventor_manor", "overworld",
    ["plains", "sunflower_plains", "meadow", "flower_forest", "cherry_grove"],
    [Piece("manor", manor)],
    spacing=60, separation=22, adaptation="beard_thin", processors="none", max_distance=80,
    title_fr="Manoir de l'inventeur", title_en="Inventor's Manor"))

"""Reusable architectural parts shared by many structures."""
from .blueprint import with_props

LOOT = "brasshaven:chests/"

# Blocks provided by the Java side of the mod. Until the mod registers them the
# generator falls back to vanilla stand-ins so the templates stay loadable.
USE_MOD_BLOCKS = True
_MOD_IDS = {
    "waystone": ("brasshaven:waystone", "minecraft:lodestone"),
    "guardian_altar": ("brasshaven:warden_altar", "minecraft:reinforced_deepslate"),
    "void_altar": ("brasshaven:void_altar", "minecraft:respawn_anchor[charges=4]"),
    "vault_bars": ("brasshaven:sealed_bars", "minecraft:iron_bars"),
}
MOD = {k: (v[0] if USE_MOD_BLOCKS else v[1]) for k, v in _MOD_IDS.items()}

# Creatures for structure spawners (vanilla stand-ins when the Java side is disabled)
_MOBS = {
    "ruin_walker": "minecraft:zombie",
    "map_wraith": "minecraft:husk",
    "basalt_guard": "minecraft:wither_skeleton",
    "void_stalker": "minecraft:enderman",
}
MOB = {k: (f"brasshaven:{k}" if USE_MOD_BLOCKS else v) for k, v in _MOBS.items()}


def timber_house(bp, x0, y0, z0, w, d, floors=2, wood="spruce", frame="dark_oak_log",
                 base="cobblestone", roof="dark_oak", door_side="south", loot=None, interior="home"):
    """Timber-frame house: stone base, plank walls framed by logs, gable roof.

    Footprint is (x0..x0+w-1, z0..z0+d-1). Returns the y of the roof ridge.
    """
    x1, z1 = x0 + w - 1, z0 + d - 1
    fh = 4  # floor height
    top = y0 + floors * fh
    bp.fill(x0, y0, z0, x1, y0, z1, base)
    for f in range(floors):
        fy = y0 + f * fh
        wall = f"{wood}_planks"
        bp.room(x0, fy, z0, x1, fy + fh, z1, wall, floor=(base if f == 0 else f"{wood}_planks"))
        # log frame on corners and every 4 blocks
        for x in range(x0, x1 + 1, 4 if w > 6 else w - 1):
            for z in (z0, z1):
                bp.fill(x, fy + 1, z, x, fy + fh - 1, z, with_props(frame, axis="y"))
        for z in range(z0, z1 + 1, 4 if d > 6 else d - 1):
            for x in (x0, x1):
                bp.fill(x, fy + 1, z, x, fy + fh - 1, z, with_props(frame, axis="y"))
        for x in (x0, x1):
            for z in (z0, z1):
                bp.fill(x, fy + 1, z, x, fy + fh - 1, z, with_props(frame, axis="y"))
        # horizontal beam at floor level
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                bp.set(x, fy + fh, z, with_props(frame, axis="x"))
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                bp.set(x, fy + fh, z, with_props(frame, axis="z"))
        # windows: centred in each bay
        for x in range(x0 + 2, x1 - 1, 4 if w > 6 else 3):
            for z in (z0, z1):
                bp.fill(x, fy + 2, z, x, fy + 3, z, "glass_pane")
        for z in range(z0 + 2, z1 - 1, 4 if d > 6 else 3):
            for x in (x0, x1):
                bp.fill(x, fy + 2, z, x, fy + 3, z, "glass_pane")
        # interior lighting
        bp.lantern((x0 + x1) // 2, fy + fh - 1, (z0 + z1) // 2, hanging=True)
    # stone plinth for the first floor walls
    bp.walls(x0, y0 + 1, z0, x1, y0 + 1, z1, base)
    # door
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    door_pos = {"south": (cx, z1), "north": (cx, z0), "east": (x1, cz), "west": (x0, cz)}[door_side]
    if door_side in ("south", "north"):
        bp.door(door_pos[0], y0 + 1, door_pos[1], door_side, wood)
        step_z = door_pos[1] + (1 if door_side == "south" else -1)
        bp.stairs(door_pos[0], y0, step_z, f"{base}_stairs" if base == "cobblestone" else "stone_brick_stairs",
                  "north" if door_side == "south" else "south")
    else:
        bp.door(door_pos[0], y0 + 1, door_pos[1], door_side, wood)
    # stairs between floors along the back wall
    for f in range(floors - 1):
        fy = y0 + f * fh
        sx = x0 + 1
        for i in range(fh):
            bp.stairs(sx + i, fy + 1 + i, z0 + 1, f"{wood}_stairs", "east")
            if i < fh - 1:
                bp.set(sx + i, fy + fh, z0 + 1, "air")  # stairwell opening
    # roof
    ridge_axis = "x" if w >= d else "z"
    ridge = bp.gable_roof(x0, z0, x1, z1, top + 1, f"{roof}_stairs", ridge_axis=ridge_axis,
                          overhang=1, fill=f"{wood}_planks")
    # attic clear + ceiling
    bp.fill(x0 + 1, top, z0 + 1, x1 - 1, top, z1 - 1, f"{wood}_planks")
    # chimney
    bp.fill(x1 - 1, y0 + 1, z1 - 1, x1 - 1, ridge + 2, z1 - 1, "bricks")
    bp.set(x1 - 1, y0 + 1, z1 - 1, "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]")
    bp.set(x1 - 1, y0 + 2, z1 - 1, "air")
    bp.set(x1 - 1, ridge + 3, z1 - 1, "air")
    _furnish(bp, x0, y0, z0, x1, z1, floors, fh, wood, loot, interior)
    return ridge


def _furnish(bp, x0, y0, z0, x1, z1, floors, fh, wood, loot, interior):
    # ground floor
    bp.set(x1 - 1, y0 + 1, z0 + 1, "crafting_table")
    bp.set(x1 - 2, y0 + 1, z0 + 1, "furnace[facing=south,lit=false]")
    bp.chest(x0 + 1, y0 + 1, z1 - 1, "east", loot)
    bp.barrel(x0 + 1, y0 + 1, z1 - 2, "up")
    bp.table((x0 + x1) // 2 + 1, y0 + 1, (z0 + z1) // 2, f"{wood}_pressure_plate", f"{wood}_fence")
    bp.chair((x0 + x1) // 2, y0 + 1, (z0 + z1) // 2, f"{wood}_stairs", "east")
    bp.set(x1 - 1, y0 + 1, z1 - 2, "red_carpet")
    if floors > 1:
        fy = y0 + fh
        if interior == "home":
            bp.bed(x1 - 1, fy + 1, z1 - 2, "south", "red")
            bp.bed(x1 - 3, fy + 1, z1 - 2, "south", "blue")
            bp.set(x0 + 1, fy + 1, z1 - 1, "bookshelf")
            bp.set(x0 + 2, fy + 1, z1 - 1, "lectern[facing=north,has_book=false,powered=false]")
        elif interior == "map":
            bp.set(x1 - 1, fy + 1, z1 - 1, "cartography_table")
            bp.set(x1 - 2, fy + 1, z1 - 1, "lectern[facing=north,has_book=false,powered=false]")
            bp.bookshelf_wall(x0 + 1, fy + 1, z1 - 1, x0 + 3, fy + 2, z1 - 1)
            bp.bed(x1 - 1, fy + 1, z0 + 2, "south", "light_blue")
        bp.chest(x1 - 1, fy + 1, (z0 + z1) // 2, "west", loot)


def round_tower(bp, cx, y0, cz, r, h, wall="stone_bricks", floor="spruce_planks", roof="dark_oak_stairs",
                windows=True, roof_block="dark_oak_planks", floors_every=6, battlements=False, ladder=True):
    bp.disk(cx, y0, cz, r, wall)
    bp.cylinder(cx, y0 + 1, cz, y0 + h, r, wall)
    for fy in range(y0 + floors_every, y0 + h, floors_every):
        bp.disk(cx, fy, cz, r - 1, floor)
        if windows:
            for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
                bp.fill(cx + dx, fy + 2, cz + dz, cx + dx, fy + 3, cz + dz, "glass_pane")
        bp.lantern(cx, fy - 1, cz, hanging=True)
    if ladder:
        bp.ladder(cx, y0 + 1, cz - r + 1, y0 + h, "south")
        for fy in range(y0 + floors_every, y0 + h + 1, floors_every):
            bp.set(cx, fy, cz - r + 1, "ladder[facing=south,waterlogged=false]")
    top = y0 + h
    if battlements:
        bp.disk(cx, top, cz, r, wall)
        bp.set(cx, top, cz - r + 1, "ladder[facing=south,waterlogged=false]")
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                if bp.get(x, top, z) and ((x + z) % 2 == 0):
                    d = (x - cx) ** 2 + (z - cz) ** 2
                    if d >= (r - 0.6) ** 2:
                        bp.set(x, top + 1, z, wall)
        return top + 1
    return bp.cone_roof(cx, top + 1, cz, r + 1, roof, block=roof_block)


def leaves(spec="oak_leaves"):
    return with_props(spec, persistent=True, distance=1, waterlogged=False)


def tree(bp, x, y, z, log="oak_log", leaf="oak_leaves", h=5, r=2):
    bp.fill(x, y, z, x, y + h - 1, z, with_props(log, axis="y"))
    lv = leaves(leaf)
    for yy in range(y + h - 2, y + h + 1):
        rr = r if yy < y + h else r - 1
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if abs(dx) == rr and abs(dz) == rr and bp.rng.random() < 0.6:
                    continue
                if (dx, dz) != (0, 0) or yy >= y + h:
                    bp.set(x + dx, yy, z + dz, lv, keep=True)
    bp.set(x, y + h, z, lv)


def palm(bp, x, y, z, h=6, lean=(1, 0)):
    log = "jungle_log[axis=y]"
    px, pz = x, z
    for i in range(h):
        if i in (h // 2, h - 2):
            px += lean[0]
            pz += lean[1]
        bp.set(px, y + i, pz, log)
    top = y + h
    lv = leaves("jungle_leaves")
    bp.set(px, top, pz, lv)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(1, 4):
            yy = top if k < 3 else top - 1
            bp.set(px + dx * k, yy, pz + dz * k, lv)
    for dx, dz in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        bp.set(px + dx, top, pz + dz, lv)
        bp.set(px + 2 * dx, top - 1, pz + 2 * dz, lv)
    bp.set(px + 1, top - 1, pz, "cocoa[age=2,facing=west]")


def path(bp, pts, y, spec="dirt_path", width=1):
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            for dx in range(-(width // 2), width - width // 2):
                for dz in range(-(width // 2), width - width // 2):
                    if bp.rng.random() < 0.85:
                        bp.set(x + dx, y, z + dz, spec)


def lamp_post(bp, x, y, z, post="spruce_fence", h=3, soul=False):
    bp.fill(x, y, z, x, y + h - 1, z, post)
    bp.lantern(x, y + h, z, soul=soul)


def banner_pole(bp, x, y, z, color="blue", h=4):
    bp.fill(x, y, z, x, y + h - 1, z, "spruce_fence")
    bp.set(x, y + h, z, f"{color}_banner[rotation=0]")


def crate_stack(bp, x, y, z):
    bp.barrel(x, y, z, "up")
    if bp.rng.random() < 0.6:
        bp.set(x, y + 1, z, "barrel[facing=north,open=false]")


def garden(bp, x0, y, z0, x1, z1, crops=("wheat", "carrots", "potatoes")):
    bp.walls(x0, y, z0, x1, y, z1, "oak_log[axis=y]")
    for x in range(x0 + 1, x1):
        for z in range(z0 + 1, z1):
            if x == (x0 + x1) // 2:
                bp.set(x, y, z, "water")
            else:
                bp.set(x, y, z, "farmland[moisture=7]")
                crop = crops[(x - x0) % len(crops)]
                bp.set(x, y + 1, z, f"{crop}[age={bp.rng.randint(3, 7)}]")

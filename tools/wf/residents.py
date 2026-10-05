"""People in the structures: safety checks (run by gen_structures) and a small lodge for new residents.

A resident is a villager, a quest giver (wayfarers:wayfarer_npc) or a wandering trader saved in a template. The
checks keep them alive and at home once the structure generates:

  check_piece(bp, ctx)        each resident stands on a solid, safe floor with two free blocks of headroom, and no
                              monster spawner is closer than SPAWNER_CLEARANCE blocks
  check_structure(sdef, counts)  a structure with residents is ``peaceful`` (an empty monster spawn override: no monster
                              spawns naturally inside its pieces) and has at least one bed per villager

  lodge(bp, ...)              a one-room timber lodge (wooden door, windows, lantern, bed and job site) for keepers,
                              wardens and other residents of structures that had no house for them
"""
import math

from . import support
from . import interior as I
from .blueprint import OPPOSITE

RESIDENTS = ("minecraft:villager", "wayfarers:wayfarer_npc", "minecraft:wandering_trader")
# a spawner activates when a player is within 14 blocks and puts its mobs within 4 blocks of itself
SPAWNER_CLEARANCE = 12
HARMFUL_FLOOR = ("magma_block", "campfire", "fire", "lava", "cactus", "sweet_berry_bush", "powder_snow",
                 "wither_rose", "pointed_dripstone")


def _short(name):
    return name.split(":", 1)[1]


def residents(bp):
    """[(block position, entity id, nbt)] of the people in ``bp``."""
    out = []
    for (x, y, z), d in bp.entities:
        eid = str(getattr(d.get("id"), "value", d.get("id")))
        if eid in RESIDENTS:
            out.append(((int(math.floor(x)), int(math.floor(y)), int(math.floor(z))), eid, d))
    return out


def check_piece(bp, ctx):
    """[(kind, pos, message)] for unsafe residents of one blueprint (blueprint coordinates)."""
    chk = support.Checker(bp.blocks, ctx)
    spawners = [p for p, b in bp.blocks.items() if b[0] in ("minecraft:spawner", "minecraft:trial_spawner")]
    out = []
    for p, eid, _ in residents(bp):
        x, y, z = p
        who = _short(eid)
        below = (x, y - 1, z)
        if not chk.nonair(below) or chk.fluid(below) or (bp.blocks.get(below) and chk.passable(below)):
            out.append(("residents", p, f"{who} has no floor under it"))
        b = bp.blocks.get(below)
        if b and any(h in _short(b[0]) for h in HARMFUL_FLOOR):
            out.append(("residents", p, f"{who} stands on {_short(b[0])}"))
        for q in (p, (x, y + 1, z)):
            if not chk.passable(q) or chk.fluid(q):
                out.append(("residents", p, f"{who} is stuck in a block or in water"))
                break
        for s in spawners:
            if math.dist(p, s) < SPAWNER_CLEARANCE:
                out.append(("residents", p, f"{who} lives {math.dist(p, s):.1f} blocks from a spawner at {s}"))
    return out


def count(bps):
    """(villagers, quest givers, beds) over blueprints."""
    v = n = beds = 0
    for bp in bps:
        for _, eid, _ in residents(bp):
            v += eid == "minecraft:villager"
            n += eid == "wayfarers:wayfarer_npc"
        beds += sum(1 for b in bp.blocks.values() if b[0].endswith("_bed") and b[1].get("part") == "head")
    return v, n, beds


def check_structure(sdef, counts):
    """[(kind, pos, message)] for a whole structure: ``counts`` = count([bp]) of every piece of every pool."""
    v, n, beds = (sum(c[i] for c in counts) for i in range(3))
    out = []
    if (v or n) and not sdef.peaceful:
        out.append(("residents", (0, 0, 0), f"{v + n} residents but monsters can spawn inside (set peaceful=True)"))
    if v > beds:
        out.append(("residents", (0, 0, 0), f"{v} villagers for {beds} beds"))
    return out


# ====================================================================== a lodge for new residents
def lodge(bp, x0, y, z0, door="south", w=7, d=5, wood="spruce", wall=None, roof=None, residents_=(),
          vtype="plains", npc=None, seed=0, bed_colour=None, clear_above=8):
    """A one-room lodge whose floor is at ``y`` (people walk at y + 1), x0..x0+w-1 by z0..z0+d-1, with a wooden
    door on the ``door`` side, a window on each other side, a hanging lantern and a gable roof. ``residents_``
    (professions or (profession, level)) move in with a bed and their job site each; ``npc`` = (role, facing)
    adds a quest giver beside the door. Clears plants and leaves in the footprint first."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    wall = wall or f"{wood}_planks"
    frame = f"stripped_{wood}_log"
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for yy in range(y + 1, y + clear_above):
                b = bp.blocks.get((x, yy, z))
                if b is not None and (support.is_plant(b[0]) or "_leaves" in b[0] or "vine" in b[0]
                                      or "bamboo" in b[0] or b[0].endswith("_log")):
                    bp.remove(x, yy, z)
    bp.fill(x0, y, z0, x1, y, z1, f"{wood}_planks")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for yy in range(y - 3, y):
                if bp.get(x, yy, z) is None:
                    bp.set(x, yy, z, "cobblestone")
    bp.clear(x0 + 1, y + 1, z0 + 1, x1 - 1, y + 3, z1 - 1)
    bp.walls(x0, y + 1, z0, x1, y + 3, z1, wall)
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        bp.fill(x, y, z, x, y + 3, z, f"{frame}[axis=y]")
    mid = {"north": ((x0 + x1) // 2, z0), "south": ((x0 + x1) // 2, z1),
           "west": (x0, (z0 + z1) // 2), "east": (x1, (z0 + z1) // 2)}
    for face, (wx, wz) in mid.items():
        if face == door:
            bp.door(wx, y + 1, wz, door, wood)
        else:
            bp.set(wx, y + 2, wz, "glass_pane")
    # gable roof along the long side, plank ceiling under it
    bp.fill(x0, y + 4, z0, x1, y + 4, z1, f"{wood}_planks")
    along_x = w >= d
    half = (d if along_x else w) // 2 + 1
    for k in range(half):
        yy = y + 5 + k
        if along_x:
            for x in range(x0 - 1, x1 + 2):
                for z, f in ((z0 - 1 + k, "south"), (z1 + 1 - k, "north")):
                    if z0 - 1 + k <= z1 + 1 - k:
                        bp.set(x, yy, z, f"{wood}_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
        else:
            for z in range(z0 - 1, z1 + 2):
                for x, f in ((x0 - 1 + k, "east"), (x1 + 1 - k, "west")):
                    if x0 - 1 + k <= x1 + 1 - k:
                        bp.set(x, yy, z, f"{wood}_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
    if along_x and d % 2:
        bp.fill(x0 - 1, y + 5 + half - 1, (z0 + z1) // 2, x1 + 1, y + 5 + half - 1, (z0 + z1) // 2, f"{wood}_slab")
    elif not along_x and w % 2:
        bp.fill((x0 + x1) // 2, y + 5 + half - 1, z0 - 1, (x0 + x1) // 2, y + 5 + half - 1, z1 + 1, f"{wood}_slab")
    bp.set((x0 + x1) // 2, y + 3, (z0 + z1) // 2, "lantern[hanging=true,waterlogged=false]")
    # outside: a lantern post by the door and a step
    dx, dz = mid[door]
    ox, oz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[door]
    if bp.get(dx + ox, y, dz + oz) is None:
        bp.set(dx + ox, y, dz + oz, f"{wood}_planks")
    region = ((x0 + 1, y + 1, z0 + 1), (x1 - 1, y + 1, z1 - 1))
    spots = I.populate(bp, list(residents_), region=region, vtype=vtype, seed=seed, bed_colour=bed_colour) \
        if residents_ else []
    if npc:
        role, facing = npc
        ix, iz = dx - ox, dz - oz
        side = (1, 0) if door in ("north", "south") else (0, 1)
        for k in (1, -1, 2, -2):
            nx, nz = ix + side[0] * k, iz + side[1] * k
            if bp.get(nx, y + 1, nz) in (None, "minecraft:air") and bp.get(nx, y + 2, nz) in (None, "minecraft:air") \
                    and (nx, y + 1, nz) not in spots:
                I.quest_npc(bp, nx, y + 1, nz, role, facing=facing or OPPOSITE[door])
                break
    return region


def free_site(bp, area, y, w, d, margin=1, roof=10):
    """The first (x0, z0) in ``area`` (x0, z0, x1, z1) where a w x d footprint (plus ``margin``) has ground set at
    ``y`` and nothing built above it but plants and leaves; None when there is none."""
    ax0, az0, ax1, az1 = area

    def ok(x, z):
        g = bp.blocks.get((x, y, z))
        if g is None or g[0] in support.AIR or g[0] in support.FLUIDS:
            return False
        for yy in range(y + 1, y + roof):
            b = bp.blocks.get((x, yy, z))
            if b is not None and not (support.is_plant(b[0]) or "_leaves" in b[0] or "vine" in b[0]
                                      or b[0] in support.AIR or "bamboo" in b[0]):
                return False
        return True

    for x0 in range(ax0, ax1 - w + 2):
        for z0 in range(az0, az1 - d + 2):
            if all(ok(x, z) for x in range(x0 - margin, x0 + w + margin) for z in range(z0 - margin, z0 + d + margin)):
                return x0, z0
    return None

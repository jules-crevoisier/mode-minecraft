"""Chunked structure templates: a big piece is cut into column templates placed by ONE pool element.

Why: vanilla ``StructureTemplate.placeInWorld`` walks the template's whole block list (one position transform
per entry) for every chunk the piece touches, and ``StructureTemplateManager`` keeps every template it loaded
until the server stops. The crystal cathedral (352k entries, ~56 chunks) cost ~20M position transforms per
generated cathedral and ~20 MB of heap for good.

How: a piece wider than SPLIT_AXIS on x or z, or with more than SPLIT_ENTRIES entries, is cut into full-height
columns of about CELL x CELL blocks (a chunk is a full-height column too, so cutting in y would save nothing).
Each column is its own template ``<sid>/<piece>/x<i>_z<j>``. The template pool references them through a single
``brasshaven:chunked_template`` element (com.brasshaven.world.ChunkedPoolElement) that carries the size of the
whole piece, so the structure is still ONE piece with the same bounding box: start height, terrain adaptation
(the beard is computed per piece box), /place and /locate behave exactly as before. When a chunk generates,
the element only places the columns whose box intersects it, and keeps a bounded number of them loaded.

Cuts never separate the two halves of a bed, a double chest or an extended piston (doors and tall plants are
vertical, and columns are never cut in y). Block entities (loot chests, spawners, boss seals) and entities stay
with the block they belong to.

Sky air: for surface structures projected on the heightmap, air that sits at least SKY_CLEARANCE blocks above
both the ground layer and the highest built block of its own column is dropped. Above the roof line it is
"outside the built shape"; it could only carve a hill rising more than SKY_CLEARANCE blocks above the roofs
(the old template carved a box out of it, the new one leaves the top of the hill and still clears
SKY_CLEARANCE blocks above every roof). Air inside rooms, under roofs and arches, near the ground, and every air
entry of underground / nether / end (explicit height) or underwater structures is kept: there it is the cavern
or the room and carves on purpose.
"""
import bisect
import math
import os

from . import nbt
from .blueprint import template_nbt

ELEMENT_TYPE = "brasshaven:chunked_template"
SPLIT_AXIS = 48         # a piece wider than this on x or z is split ...
SPLIT_ENTRIES = 60000   # ... and so is a piece with more block entries than this
CELL = 32               # nominal column width; every column ends up <= SPLIT_AXIS wide and <= SPLIT_ENTRIES
MAX_NUDGE = 8           # how far a cut may move to keep a bed / double chest in one column
SKY_CLEARANCE = 12
AIR = {"minecraft:air", "minecraft:cave_air"}


def needs_split(size, entries):
    return size[0] > SPLIT_AXIS or size[2] > SPLIT_AXIS or entries > SPLIT_ENTRIES


def cell_ok(size, entries):
    """A template a pool may reference directly (a column, or a piece too small to split)."""
    return size[0] <= SPLIT_AXIS and size[2] <= SPLIT_AXIS and entries <= SPLIT_ENTRIES


# ------------------------------------------------------------------ sky air
def sky_air(blocks, ground):
    """Positions of air entries at least SKY_CLEARANCE above the ground layer and above the highest non-air
    block of their column (normalized coordinates, ``ground`` = ground layer y in the same space)."""
    roof = {}
    for (x, y, z), b in blocks.items():
        if b[0] not in AIR and y > roof.get((x, z), -1):
            roof[(x, z)] = y
    return {p for p, b in blocks.items()
            if b[0] in AIR and p[1] > ground + SKY_CLEARANCE and p[1] > roof.get((p[0], p[2]), -1) + SKY_CLEARANCE}


# ------------------------------------------------------------------ cuts
def _paired(name, props):
    """Blocks made of two horizontal halves that must land in the same column."""
    s = name.split(":", 1)[1]
    if s.endswith("_bed"):
        return True
    if s.endswith("chest") and props.get("type", "single") != "single":
        return True
    if s in ("piston", "sticky_piston"):
        return props.get("extended") == "true"
    return s in ("piston_head", "moving_piston")


def forbidden_cuts(blocks):
    """Cut planes (x = c means a boundary between c - 1 and c) that would separate a paired block."""
    fx, fz = set(), set()
    for (x, y, z), (name, props, _) in blocks.items():
        if not _paired(name, props):
            continue
        for dx, dz in ((1, 0), (0, 1)):
            n = blocks.get((x + dx, y, z + dz))
            if n and _paired(n[0], n[1]):
                (fx if dx else fz).add(x + 1 if dx else z + 1)
    return fx, fz


def plan_cuts(length, forbidden, cell):
    """Boundaries [0, c1, ..., length] of about ``cell`` wide intervals, nudged off forbidden planes."""
    n = max(1, math.ceil(length / cell))
    cuts = [0]
    for i in range(1, n):
        ideal = round(i * length / n)
        for d in sorted(range(-MAX_NUDGE, MAX_NUDGE + 1), key=lambda v: (abs(v), v)):
            c = ideal + d
            if c not in forbidden and cuts[-1] < c < length:
                cuts.append(c)
                break
        else:
            raise ValueError(f"no legal cut near {ideal}")
    cuts.append(length)
    return cuts


class Cell:
    def __init__(self, key, offset, size, blocks, entities):
        self.key = key            # (i, j) column index
        self.offset = offset      # min corner inside the whole piece (normalized coordinates)
        self.size = size
        self.blocks = blocks      # local position -> (name, props, nbt)
        self.entities = entities  # [(local position, nbt)]

    @property
    def name(self):
        return f"x{self.key[0]}_z{self.key[1]}"


def split(size, blocks, entities):
    """Cut normalized ``blocks``/``entities`` into columns; returns [Cell] (empty columns are skipped)."""
    fx, fz = forbidden_cuts(blocks)
    cell = CELL
    while True:
        xs, zs = plan_cuts(size[0], fx, cell), plan_cuts(size[2], fz, cell)
        groups = {}
        for pos, b in blocks.items():
            key = (bisect.bisect_right(xs, pos[0]) - 1, bisect.bisect_right(zs, pos[2]) - 1)
            groups.setdefault(key, ([], []))[0].append((pos, b))
        for pos, d in entities:
            key = (bisect.bisect_right(xs, pos[0]) - 1, bisect.bisect_right(zs, pos[2]) - 1)
            groups.setdefault(key, ([], []))[1].append((pos, d))
        if all(len(bl) <= SPLIT_ENTRIES for bl, _ in groups.values()) or cell <= 8:
            break
        cell -= 8
    cells = []
    for key in sorted(groups):
        bl, en = groups[key]
        pts = [p for p, _ in bl] + [p for p, _ in en]
        lo = tuple(min(p[k] for p in pts) for k in range(3))
        hi = tuple(max(p[k] for p in pts) for k in range(3))
        local = lambda p: (p[0] - lo[0], p[1] - lo[1], p[2] - lo[2])  # noqa: E731
        cells.append(Cell(key, lo, tuple(hi[k] - lo[k] + 1 for k in range(3)),
                          {local(p): b for p, b in bl}, [(local(p), d) for p, d in en]))
    return cells


# ------------------------------------------------------------------ files
def write_cells(directory, location_prefix, cells):
    """Save every column as ``directory/<cell>.nbt`` (stale columns removed); returns the element's cell list."""
    os.makedirs(directory, exist_ok=True)
    keep = {c.name + ".nbt" for c in cells}
    for f in os.listdir(directory):
        if f.endswith(".nbt") and f not in keep:
            os.remove(os.path.join(directory, f))
    out = []
    for c in cells:
        nbt.save(os.path.join(directory, c.name + ".nbt"), template_nbt(c.size, c.blocks, c.entities))
        out.append({"location": f"{location_prefix}/{c.name}", "offset": list(c.offset), "size": list(c.size),
                    "blocks": len(c.blocks)})
    return out


def element(size, cells, projection, processors, ground_level_delta=None, footprint=None):
    el = {
        "element_type": ELEMENT_TYPE,
        "size": list(size),
        "cells": cells,
        "projection": projection,
        "processors": processors,
    }
    if ground_level_delta is not None:
        el["ground_level_delta"] = ground_level_delta  # see wf/placement.py "Terrain fit"
    if footprint is not None:
        el["footprint"] = list(footprint)  # built columns x0, z0, x1, z1 (wf/placement.py "Site selection")
    return el


# ------------------------------------------------------------------ verification
def _canon_nbt(data):
    if data is None:
        return None
    return repr(nbt.loads(nbt.dumps(data)))


def _template_entries(t, offset=(0, 0, 0)):
    """Plain template compound (nbt.load) -> ({global pos: state key, nbt}, [entity keys])."""
    palette = []
    for e in t["palette"]:
        palette.append((e["Name"], tuple(sorted(e.get("Properties", {}).items()))))
    ox, oy, oz = offset
    blocks = {}
    for b in t["blocks"]:
        x, y, z = b["pos"]
        pos = (x + ox, y + oy, z + oz)
        if pos in blocks:
            raise ValueError(f"duplicate entry at {pos}")
        blocks[pos] = (palette[b["state"]], repr(b["nbt"]) if "nbt" in b else None)
    ents = []
    for e in t["entities"]:
        x, y, z = e["blockPos"]
        px, py, pz = e["pos"]
        ents.append(((x + ox, y + oy, z + oz), (px + ox, py + oy, pz + oz), repr(e["nbt"])))
    return blocks, sorted(ents)


def verify(directory, cell_records, size, blocks, entities, dropped=()):
    """Reload the written columns, put them back together and compare entry by entry with the unsplit piece
    (``blocks``/``entities`` normalized, ``dropped`` = the sky-air positions removed on purpose).
    Returns a list of problems (empty when the columns rebuild the piece exactly)."""
    problems = []
    got_blocks, got_ents = {}, []
    footprints = []
    for rec in cell_records:
        path = os.path.join(directory, rec["location"].rsplit("/", 1)[1] + ".nbt")
        t = nbt.load(path)
        if list(t["size"]) != rec["size"]:
            problems.append(f"{path}: size {t['size']} != {rec['size']}")
        if len(t["blocks"]) != rec["blocks"]:
            problems.append(f"{path}: {len(t['blocks'])} entries, element says {rec['blocks']}")
        if not cell_ok(rec["size"], rec["blocks"]):
            problems.append(f"{path}: column {rec['size']} / {rec['blocks']} entries over the threshold")
        o, s = rec["offset"], rec["size"]
        if any(o[k] < 0 or o[k] + s[k] > size[k] for k in range(3)):
            problems.append(f"{path}: column {o}+{s} outside the piece {list(size)}")
        footprints.append((o[0], o[0] + s[0], o[2], o[2] + s[2], path))
        b, e = _template_entries(t, o)
        for pos in b:
            if pos in got_blocks:
                problems.append(f"{path}: {pos} also in another column")
        got_blocks.update(b)
        got_ents += e
    for i, a in enumerate(footprints):
        for c in footprints[i + 1:]:
            if a[0] < c[1] and c[0] < a[1] and a[2] < c[3] and c[2] < a[3]:
                problems.append(f"columns overlap: {a[4]} / {c[4]}")
    want = {}
    for pos, (name, props, data) in blocks.items():
        if pos in dropped:
            if name not in AIR:
                problems.append(f"dropped a non-air block {name} at {pos}")
            continue
        want[pos] = ((name, tuple(sorted(props.items()))), _canon_nbt(data))
    if want != got_blocks:
        missing = [p for p in want if p not in got_blocks]
        extra = [p for p in got_blocks if p not in want]
        diff = [p for p in want if p in got_blocks and want[p] != got_blocks[p]]
        problems.append(f"blocks differ: {len(missing)} missing, {len(extra)} extra, {len(diff)} changed "
                        f"(e.g. {(missing + extra + diff)[:3]})")
    want_ents = sorted(((x, y, z), (x + 0.5, float(y), z + 0.5), _canon_nbt(d)) for (x, y, z), d in entities)
    if want_ents != sorted(got_ents):
        problems.append(f"entities differ: {len(want_ents)} expected, {len(got_ents)} found")
    return problems

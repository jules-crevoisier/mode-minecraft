#!/usr/bin/env python3
"""Generate every Wayfarers structure: .nbt templates + worldgen JSON + biome tags.

Usage:
    python3 tools/gen_structures.py            # write into src/main/resources
    python3 tools/gen_structures.py --preview  # also render isometric previews to build/previews
    python3 tools/gen_structures.py --only guild_outpost --preview
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wf import defs, render, support, foundation, chunking, nbt  # noqa: E402
try:
    from wf import render3d  # noqa: E402  (optional: needs Pillow + minecraft-textures)
except ImportError:
    render3d = None
from wf.blueprint import Blueprint, template_nbt  # noqa: E402
import wf.structures  # noqa: E402,F401  (registers every structure)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "src", "main", "resources", "data", defs.MODID)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def needs_foundation(sdef):
    """Surface structures projected on the terrain (not sky islands, not ocean-floor wrecks)."""
    return sdef.height is None and sdef.heightmap == "WORLD_SURFACE_WG" and sdef.height_offset == 0 \
        and sdef.foundation


def prunes_sky_air(sdef, start):
    """Surface structures projected on the terrain (sky air above them only carves hills, see wf/chunking.py)."""
    return start and sdef.height is None and sdef.heightmap == "WORLD_SURFACE_WG"


def save_piece(sdef, piece, bp, start, report):
    """Write the piece as one template, or as column templates when it is big (wf/chunking.py).
    Returns (size, normalized blocks, origin, number of columns or 0, entries written, biggest template)."""
    bp.resolve_shapes()
    size, blocks, ents, origin = bp.normalized()
    path = os.path.join(DATA, "structure", sdef.id, f"{piece.name}.nbt")
    cell_dir = os.path.join(DATA, "structure", sdef.id, piece.name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    piece.chunks = None
    if not chunking.needs_split(size, len(blocks)):
        nbt.save(path, template_nbt(size, blocks, ents))
        if os.path.isdir(cell_dir):
            shutil.rmtree(cell_dir)
        return size, blocks, origin, 0, len(blocks), len(blocks)
    dropped = chunking.sky_air(blocks, sdef.ground - origin[1]) if prunes_sky_air(sdef, start) else set()
    kept = {p: b for p, b in blocks.items() if p not in dropped}
    cells = chunking.split(size, kept, ents)
    records = chunking.write_cells(cell_dir, defs.rl(f"{sdef.id}/{piece.name}"), cells)
    for msg in chunking.verify(cell_dir, records, size, blocks, ents, dropped):
        report.append((sdef.id, piece.name, "chunks", (0, 0, 0), msg))
    if os.path.exists(path):
        os.remove(path)
    piece.chunks = (size, records)
    return size, blocks, origin, len(cells), len(kept), max(len(c.blocks) for c in cells)


def build_piece(sdef, piece, start=False):
    bp = Blueprint(f"{sdef.id}/{piece.name}")
    piece.builder(bp)
    if start and needs_foundation(sdef):
        foundation.add_foundations(bp, sdef.ground)
    piece.blueprint = bp
    return bp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--no-check", action="store_true", help="skip the survival/door checks")
    args = ap.parse_args()
    report = []
    repairs = {}

    preview_dir = os.path.join(ROOT, "build", "previews")
    used_processors = set()
    summary = []
    for sdef in defs.STRUCTURES:
        if args.only and sdef.id not in args.only:
            continue
        pools = {"start": sdef.pieces}
        pools.update(sdef.extra_pools)
        ground_offset = 0
        for pool_name, pieces in pools.items():
            for piece in pieces:
                bp = build_piece(sdef, piece, start=pool_name == "start")
                ctx = support.context_for(sdef) if pool_name == "start" else support.Context(unset_solid=True)
                bp.resolve_shapes()
                for what, n in support.repair(bp, ctx).items():
                    repairs[what] = repairs.get(what, 0) + n
                size, blocks, (mx, my, mz), ncells, written, biggest = save_piece(sdef, piece, bp, pool_name == "start", report)
                if not args.no_check:
                    for kind, pos, msg in support.check(bp.blocks, ctx):
                        report.append((sdef.id, piece.name, kind, pos, msg))
                if pool_name == "start" and piece is pieces[0]:
                    ground_offset = my - sdef.ground
                summary.append((f"{sdef.id}/{piece.name}", size, len(blocks), ncells, written, biggest))
                if args.preview:
                    os.makedirs(preview_dir, exist_ok=True)
                    stem = os.path.join(preview_dir, f"{sdef.id}__{piece.name}")
                    cut = sdef.ground - my + 2
                    if render3d:
                        render3d.render(blocks, stem + ".png", max_side=1600)
                        render3d.render(blocks, stem + "_back.png", max_side=1600, angle=2)
                        render3d.render(blocks, stem + "_cut.png", max_side=1600, max_y=cut)
                    else:
                        render.render(blocks, stem + ".png", s=5)
                        render.render(blocks, stem + "_cut.png", s=5, max_y=cut)
                used_processors.add(piece.processors or sdef.processors)
            write_json(os.path.join(DATA, "worldgen", "template_pool", sdef.id, f"{pool_name}.json"),
                       defs.template_pool(sdef, pieces, pool_name))
        write_json(os.path.join(DATA, "worldgen", "structure", f"{sdef.id}.json"),
                   defs.structure_json(sdef, ground_offset))
        write_json(os.path.join(DATA, "worldgen", "structure_set", f"{sdef.id}.json"),
                   defs.structure_set_json(sdef))
        write_json(os.path.join(DATA, "tags", "worldgen", "biome", "has_structure", f"{sdef.id}.json"),
                   defs.biome_tag_json(sdef.biomes))
    for kind in sorted(used_processors | {"aging", "ruin", "none"}):
        write_json(os.path.join(DATA, "worldgen", "processor_list", f"{kind}.json"), defs.processor_list(kind))

    for kind in sorted(used_processors | {"aging", "ruin", "none"}):
        for src in support.stair_rules_ok(defs.processor_list(kind)):
            report.append(("processor_list", kind, "processor", (0, 0, 0), f"rule rewrites {src} without its properties"))

    for name, size, n, ncells, written, _ in summary:
        split = f"  -> {ncells} columns, {written} entries ({n - written} sky air dropped)" if ncells else ""
        print(f"{name:45s} {size[0]:3d}x{size[1]:3d}x{size[2]:3d}  {n:6d} blocks{split}")
    files = sum(s[3] or 1 for s in summary)
    biggest = max((s[5] for s in summary), default=0)
    print(f"{len(summary)} pieces in {files} templates, {len({s.split('/')[0] for s, *_ in summary})} structures, "
          f"{sum(1 for s in summary if s[3])} pieces chunked, biggest template {biggest} entries")
    for what, n in sorted(repairs.items()):
        print(f"auto-repair: {what}: {n}")
    if not args.no_check:
        write_report(report)
        if report:
            print(f"{len(report)} survival/door problems (see build/structure_report.txt)")
            sys.exit(1)


def write_report(report):
    """Group problems per structure piece and kind, with a few coordinates (blueprint space)."""
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    groups = {}
    for sid, piece, kind, pos, msg in report:
        key = (sid, piece, kind, msg.split(" (")[0])
        groups.setdefault(key, []).append(pos)
    with open(os.path.join(ROOT, "build", "structure_report.txt"), "w", encoding="utf-8") as f:
        for (sid, piece, kind, msg), positions in sorted(groups.items()):
            pts = " ".join(f"({x},{y},{z})" for x, y, z in sorted(positions)[:6])
            f.write(f"{sid}/{piece} [{kind}] {msg} x{len(positions)}: {pts}\n")


if __name__ == "__main__":
    main()

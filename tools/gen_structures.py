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
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wf import defs, render  # noqa: E402
from wf.blueprint import Blueprint  # noqa: E402
import wf.structures  # noqa: E402,F401  (registers every structure)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "src", "main", "resources", "data", defs.MODID)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_piece(sdef, piece):
    bp = Blueprint(f"{sdef.id}/{piece.name}")
    piece.builder(bp)
    piece.blueprint = bp
    return bp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()

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
                bp = build_piece(sdef, piece)
                path = os.path.join(DATA, "structure", sdef.id, f"{piece.name}.nbt")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                bp.save(path)
                size, blocks, _, (mx, my, mz) = bp.normalized()
                if pool_name == "start" and piece is pieces[0]:
                    ground_offset = my - sdef.ground
                summary.append((f"{sdef.id}/{piece.name}", size, len(blocks)))
                if args.preview:
                    os.makedirs(preview_dir, exist_ok=True)
                    stem = os.path.join(preview_dir, f"{sdef.id}__{piece.name}")
                    render.render(blocks, stem + ".png", s=5)
                    cut = sdef.ground - my + 2
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

    for name, size, n in summary:
        print(f"{name:45s} {size[0]:3d}x{size[1]:3d}x{size[2]:3d}  {n:6d} blocks")
    print(f"{len(summary)} templates, {len({s.split('/')[0] for s, _, _ in summary})} structures")


if __name__ == "__main__":
    main()

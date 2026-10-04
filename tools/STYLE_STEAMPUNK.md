# Wayfarers steampunk style guide

This is the reference for every steampunk texture, model and build (blocks in `wf/texgen_steam.py`, decor in `wf/decor.py`, metals in `wf/metals.py`).

## Palette

| Role | Colour | Hex |
|---|---|---|
| Brass (main metal) | warm yellow | `#B5A642` / `#B08D57` |
| Copper | orange-brown | `#B87333` |
| Verdigris (aged copper) | teal | `#43B3AE` |
| Dark iron (frames, floors) | near-black | `#2B2320` / `#342E2E` |
| Mahogany (interiors) | red-brown | `#6B3F2A` |
| Oxblood leather | deep red | `#6E241E` |
| Cream (dials, paper) | warm white | `#D7C3A1` |
| Amber glow (lamps) | orange | `#FFB347` |
| Aether glow (magic tech) | cyan | `#3FD0FF` / `#2EE6C5` |

## Proportions

60% dark (iron, wood, soot), 25% metal (brass, copper), 10% light (cream, glass), 5% glow (amber, aether).

A build that is mostly brass looks like a toy. Brass should frame and highlight; dark iron and mahogany carry the mass.

## Motifs

- Rivets along every plate edge.
- Cogs, behind glass or in recessed panels.
- Pipe bundles with brass clamps.
- Pressure gauges.
- Smokestacks with soot.
- Glass domes and Edison bulbs.
- Catwalks with tread plate.

Light sources are always visible and warm: amber for steam tech, cyan for aether tech.

## References

- Piltover (polished brass, cream stone, glass) and Zaun (pipes, soot, green-teal glow) from *Arcane*.
- Columbia, from *BioShock Infinite*: sky docks, gilded domes and banners.
- Victorian industrial architecture: brick mills, cast-iron train stations, riveted bridges.

## Item sprites and block faces

- Item sprites are painted in `wf/itemart.py` (+ `itemart_shapes.py`, `itemart_trinkets.py`, `itemart_tools.py`): draw
  the fill only (segments, discs, polygons, ASCII stamps on material keys); the painter adds the 1-px dark outline and
  the top-left light (shine > light > mid > dark > deep). Use the fixed keys for brass, copper, verdigris, dark iron,
  leather, cream and the amber / aether glows; `M`, `H`, `A` are the item's material, handle and accent.
- Every item gets its own silhouette: a boss weapon never shares a shape with another one.
- Glows, sparks and steam (`Y`, `a`) float free of the outline; everything else is outlined.
- Utility, altar and metal block faces live in `wf/blockart.py`.
- Review loop: `python3 tools/gen_textures.py && python3 tools/art_sheet.py` (contact sheets at 8x with 1x/2x copies in
  `build/previews/art_*.png`; `--kind held` renders the 3D in-hand models after `gen_assets.py`).

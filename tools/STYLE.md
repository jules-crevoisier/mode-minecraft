# Wayfarers — architecture style guide

Every structure must look like something a skilled builder spent hours on. Players should stop
and say "wow" from a distance. These rules are mandatory.

## 1. Scale and silhouette
- **Monumental** structures: footprint 50–90 blocks, height 35–80 (towers/spires).
  **Medium**: 25–45 footprint, 15–35 tall. Nothing should read as a box.
- The silhouette must be readable from 100 blocks away. Use towers of different heights,
  spires, chimneys, domes, bell towers, flying buttresses, bridges, overhangs.
- Break symmetry a little: one taller tower, an annex, a collapsed corner, a garden side.
- Compose in **masses**: main hall + secondary wings + towers + small outbuildings, linked by
  walls, bridges, stairs and paths. Vary roof heights between masses.

## 2. Depth: no flat walls, ever
- Every wall has 3 depth layers: plinth/base course, main wall, protruding elements
  (pilasters, buttresses, window frames, cornice). Use `arch.facade(...)`.
- Windows are recessed or framed, with sills (stairs/slabs/trapdoors) and lintels or arches.
- Roofs: steep (`arch.steep_roof`, `steep=2` for gothic), always with overhang and an eave
  shadow line (`under=`). Long roofs get dormers. Ridges get caps. Towers get spires
  (`arch.spire`, `round_tower(crown="spire")`) or corbelled crenellations.
- Add trim lines: floor bands between storeys, corner quoins, corbels under overhangs.

## 3. Materials
- 3–5 materials per structure + 1 accent. Main walls use a **Palette** (2–4 similar blocks with
  coherent noise), never a single flat block. Trim is a contrasting, cleaner block. Roof colour
  contrasts with the walls.
- **Use the Wayfarers blocks** to make the mod unique:

| Theme | Blocks |
|---|---|
| Guild (Overworld) | `wayfarers:guild_bricks` (+ `mossy_`/`cracked_`, `guild_brick_stairs/slab/wall`), `polished_guild_stone` (+`_stairs/_slab`), `carved_guild_stone`, roofs `guild_roof_tiles` (azure), `crimson_roof_tiles`, `slate_roof_tiles` (+`*_roof_tile_stairs/_slab`), light `rune_lamp` |
| Deep | `lithite_bricks` (+`lithite_brick_stairs/slab/wall`), `lithite_block` (glowing crystal) |
| Nether | `ember_bricks` (+`ember_brick_stairs/slab/wall`), `ember_lamp`, `gilded_trim` |
| End | `void_bricks` (+`void_brick_stairs/slab/wall`), `starlight_block` |

  Mix them with vanilla blocks: deepslate, tuff bricks, calcite, copper, dark oak, mud bricks,
  blackstone, purpur, prismarine, quartz…
- Note: templates are stored as 1.20.1, so only vanilla blocks that existed in 1.20.1 are allowed
  (no tuff bricks, chiseled copper, crafter, pale oak, resin…). `validate.py` enforces it.
- Lighting everywhere (lanterns on chains, rune lamps, ember lamps, candles, end rods,
  sea lanterns) — dark corners only where monsters should lurk.

## 4. Ground and nature
- Structures must sit naturally: use `arch.terrain_skirt` under the footprint, steps at doors,
  retaining walls on slopes. Floating islands get a rocky underside with hanging roots/vines.
- Landscaping: paths (gravel/coarse dirt/path blocks), gardens, flowers (`arch.landscape`),
  bushes, boulders, realistic trees (`arch.oak/spruce/big_oak/dark_tree`).
- Age ruins tastefully: `arch.moss_on`, `arch.vines_on`, partial collapse, rubble piles — but the
  original architecture must still be readable.

## 5. Interiors and gameplay (mandatory)
- Every enterable room is furnished (`arch.furnish` kinds + custom details). Chandeliers in big
  halls.
- Keep every loot table name already used by the structure (they exist in `gen_loot.py`); put
  2–6 loot containers per structure, the best one guarded or hidden.
- Danger: 1–4 spawners (`bp.spawner(x, y, z, MOB["ruin_walker"])` etc. from `parts.MOB`, or
  vanilla ids) placed where fights make sense. Monumental structures also declare guards with
  `StructureDef(..., spawns=[("wayfarers:ruin_walker", 10, 1, 3), ...])` (they keep spawning in
  the dark inside the structure).
- At least one **secret**: hidden room, collapsed passage, buried vault, puzzle door.
- Waystones (`MOD["waystone"]`) in hubs: keep the ones that exist, add one where players would
  want to come back.

## 6. Technical constraints
- Coordinates: x east, y up, z south; blueprint y=0 is the ground layer (floor replaces the top
  ground block). Use `ground=` in StructureDef if your ground layer is elsewhere.
- Underwater builds set `bp.underwater = True` so cleared space becomes water.
- Leaves must be persistent (`parts.leaves(...)` / arch helpers do it).
- Single-piece templates: keep each under ~100x100 footprint and ~110 tall.
- Doors need two halves (`bp.door`), beds two parts (`bp.bed`).
- Never use `if False` / dead code; keep builders readable, commented by area.

## 7. The loop (mandatory)
For each structure, iterate at least 3 times:
1. `python3 tools/gen_structures.py --only <id> --preview`
2. Look at `build/previews/<id>__<piece>.png`, `_back.png` (opposite side) and `_cut.png` (ground
   floor plan) with the Read tool.
3. Critique honestly against this guide: flat walls? boring roof? weak silhouette? empty
   interior? floating or buried base? ugly colour mix? Fix and render again.
Finish with `python3 tools/validate.py` (0 errors).

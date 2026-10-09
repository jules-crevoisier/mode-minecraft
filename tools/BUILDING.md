# Brasshaven — building intelligence guide

`STYLE.md` covers materials and the preview loop. This guide covers composition, scale and circulation, and it
overrides STYLE.md §1 on scale. Every rule below can be checked by a script or by reading the preview.
A build that fails a **[CHECK]** rule is not finished.

Units: 1 block = 1 m. The player is 1.8 blocks tall, stands in 2 blocks and jumps 1.25 blocks. Falls of more than
3 blocks hurt. An enderman is 2.9 tall and an iron golem 2.7, which is why walkways get 3 blocks of headroom.

---

## 0. Why the current builds read as "AI-generated"

Seen in `docs/structures/*.png` and in the helper defaults:

1. **Uniform rhythm.** `facade(pilaster_every=4)` makes identical bays all along a wall. Real façades group bays
   (A-B-A, 1-3-1) and give the centre or the ends more weight.
2. **Equal masses.** Towers, wings and hall have similar heights, so no part dominates and the silhouette is a
   comb instead of a pyramid of importance.
3. **Boxes with decoration on top.** Plans are rectangles with towers glued on the corners. Masses do not
   interpenetrate, step back or taper.
4. **Isotropic noise.** `Palette` noise is the same everywhere. Nothing is darker at the base, wetter under eaves
   or cleaner at the crown, so walls look speckled rather than aged.
5. **One scale of detail.** Everything has 1-block detail and nothing at 5–10 blocks, so builds look busy up close
   and flat from far away.
6. **Scale without reference.** A 70-block wall with no human-scale element (a door, a stair, a lamp, a window
   with sills) reads as 20 blocks. Hugeness is only perceived by comparison.
7. **Circulation as an afterthought.** Ladders in every tower, 2-high passages, stairs that hit ceilings and rooms
   reachable only by jumping. Nothing checks paths automatically today; `interior.find_rooms` sees rooms one level
   at a time.
8. **No approach.** The entrance is a door in a wall, with no route, gate sequence, framed view or reveal.
9. **Duplicated helpers.** `pinnacle` is defined 4×, `spire` 4×, `vault` 6×, `bridge` 3× and `flying_buttress`
   2× across `structures/*.py`. Quality varies by file, and fixes do not spread.

---

## 1. Scale tiers

| Tier | Footprint (max side) | Height (top of crown) | Masses | Floor-to-floor | Examples |
|---|---|---|---|---|---|
| Small | 9–24 | 8–20 | 1–2 | 4–5 | hut, shrine, waystone kiosk |
| Medium | 25–49 | 15–40 | 2–4 | 5–6 | manor, watchtower group |
| Monumental | 50–119 | 35–90 | 4–8 | 6–8 (halls 12–30) | cathedral, citadel |
| **Colossal** | **120–250** | **80–200** | **6–15 + terrain** | 6–8 (halls 20–60) | legacy dungeons, wonders |

Real references in blocks (1 m = 1 block): Amiens nave 42 high × 12–15 wide (h:w ≈ 3:1), 133 long, spire 112.
Beauvais choir vault 47. Cologne nave 43. Real buildings already sit in the colossal tier, so a "majestic"
cathedral is 40+ inside, not 20.

Technical budget for colossal builds:
- The piece is chunked automatically (`chunking.py`: split above 48 on x/z or above 60k entries). Keep entries
  under ~450k per piece (the crystal cathedral has 352k).
- Aim for 6–12 % solid fill of the bounding volume. A 180×180×140 colossus is 4.5M cells, so 270k–540k
  entries. Hollow shells with carved interiors, not solid masses.
- `max_distance` in `StructureDef` is ≤116 today. The vanilla jigsaw codec caps `max_distance_from_center` at
  128; check the `brasshaven:fitted_jigsaw` codec before going above it. `ci_smoke` scans r=160.
- Height: build height 320 in the Overworld. A 200-tall colossus needs a height budget (`height=` or a
  surface lift check in `placement.py`), and a mountain base helps by absorbing terrain differences.

---

## 2. Massing and silhouette

**Hierarchy [CHECK]**
- Exactly **one dominant mass** (keep, spire, dome, statue). Its top is ≥ **1.5×** the next-highest mass
  (≥1.3× for medium).
- **2–4 secondary masses**, each 0.45–0.75 of the dominant's height. **Minor masses** are ≤0.4.
- No two masses are within 10 % of each other's height, unless they form a deliberate pair (twin west towers),
  which then must be identical and symmetric about the main axis.
- Volumes step down from the dominant outward, like a mountain or a pyramid of importance.

**Vertical tripartition (base / body / crown)** for every mass taller than 20:
- Base (plinth, batter, rock): 10–25 % of the height. It is the darkest and roughest part and is ≥1 block
  thicker than the body.
- Body: 50–65 %, with rhythm and openings.
- Crown (cornice, machicolations, roof, spire): 15–35 %, and it carries the most complex outline.
- Spires: height:base ratio is 3:1 to 5:1 for gothic. `arch.spire(steep=2)` only gives 2:1, so use `steep=3–4`
  for r≥5.

**Plan shape [CHECK]**
- Plans are ≥3 overlapping primitives (rectangles, circles, polygons) and never a single rectangle.
- Fill ratio (footprint ÷ convex hull area) is 0.45–0.80. Above 0.85 the build reads as a box.
- No straight outer wall longer than **24 blocks** (monumental) or **40** (colossal) without a break: a tower,
  a buttress ≥3 deep, a setback ≥2, a change of height ≥4, or a gatehouse.
- Colossal builds taper: each upper terrace or level is ≤75 % of the footprint below it (setbacks). The
  silhouette should fit a triangle or a stepped mountain, not a rectangle.

**Skyline [CHECK]** (compute the max-height profile per column along each of the 4 elevations)
- At least 3 distinct peaks per elevation (local maxima separated by ≥4 lower blocks), and ≥5 for colossal.
- Highest peak ÷ median roof height ≥ 1.4.
- No flat roofline segment longer than 16 blocks. Break it with chimneys, dormers, pinnacles or crenels every
  4–8 blocks.
- Asymmetry: the two halves of an elevation differ in silhouette area by 5–25 %. Off-centre interest is always
  a feature with a reason (a bell tower, an annex, a collapsed corner), never noise.

---

## 3. Scale cues: making the player feel small

Hugeness is relative. Every colossal element needs a human-scale element right next to it.

- **Scale ladder.** Every façade shows elements at roughly 1, 3, 9 and 27 blocks: a lamp or sill, a door or
  window, a bay or arch, the whole wing. Missing rungs make the build read smaller or as a blank wall.
- **Portal nesting.** A colossal gate is 7–15 wide and 12–30 high and contains a normal door (1–3 × 2–4)
  inside it, a wicket door. The contrast does the work.
- **Repetition with diminution.** A long colonnade, a stair of 40+ steps or a row of 8+ identical statues makes
  distance readable. Repeated elements ≥6, equal spacing, and the end visible from the start.
- **Big supports.** Columns in halls more than 30 high are ≥3×3 (round r≥2) with base and capital. Spans: arches
  up to 24 wide, bridges with piers every 16–30. Thin 1-block pillars under huge masses look fake.
- **Windows scale with the wall but not with the player.** Clerestory windows on a 40-high nave are 3–5 wide and
  8–14 high. Ground-floor windows stay at 1–2 × 2–3 with sills.
- **Vertical voids.** Every colossal structure has at least one interior space whose height is ≥2× its
  width: a shaft, a nave, a light well, a stair hall. The player looks up from the bottom.
- **Viewing distance.** Place the structure so its approach shows the whole silhouette from 1.5–3× its height
  away (§7).

---

## 4. Depth and surface

Depth layers measured from the wall plane (0), positive outward:

| Layer | Offset | Elements | Share of façade area |
|---|---|---|---|
| −2…−1 | recess | window reveals, niches, arcades, loggias | 10–25 % |
| 0 | wall | ashlar, brick | 45–70 % |
| +1 | frame | pilasters, string courses, sills, cornices, quoins | 15–25 % |
| +2…+4 | structure | buttresses, towers, oriels, balconies, chimneys | 5–15 % |
| +5…+12 | colossal only | flying buttresses, bastions, statues, stair towers | per elevation ≥2 |

**[CHECK] Flat-wall rule.** No rectangle larger than **7×7** (small/medium), **9×9** (monumental) or **12×12**
(colossal) of a single layer and a single material family. Scale every offset with the tier: pilasters 1 deep
(small), 2 (monumental), 2–3 (colossal), and buttresses 2 / 3–4 / 5–8.

**Bay rhythm.** Bays are 4–7 wide (medium), 6–9 (monumental) and 9–15 (colossal). Group them in a pattern, for
example A-B-A, A-A-B-A-A or 1-3-1, and mark the main axis with a wider, taller bay: a portal, a rose window or a
tower.

**Depth must be structural** (WesterosCraft): buttresses where vaults push, corbels under overhangs, sills under
windows, eaves on every pitched roof. Depth only for "breaking up the wall" looks arbitrary.

**Roofs.** Every pitched roof has ≥1 overhang with an eave shadow line. The roof colour value differs from the
walls by ≥2 steps on the value ladder (§5). Long roofs (>16) have dormers or a ridge break. Inside, the roof
underside never shows bare roof stairs: use rafters (stairs, fences or a ceiling layer).

---

## 5. Palette and gradients

- 3–5 materials plus 1 accent per structure (as in STYLE.md). For each material family, define a **value
  ladder** of 4–8 blocks, ordered light to dark, with shade first, then hue, then texture.
- Overall proportions: 60 % main, 25–30 % secondary or trim, 10 % accent or light. Steampunk uses
  STYLE_STEAMPUNK's 60/25/10/5.
- **No skipped steps [CHECK]:** ≥90 % of face-adjacent pairs in the same family are ≤1 ladder step apart.
  WesterosCraft calls the failure "splattering".
- **No sandwiching:** a band boundary between ladder steps is never a straight horizontal line. Jitter it by ±2
  blocks with noise. Exception: deliberate string courses in trim material.
- **Directional gradients** replace isotropic noise. Weight the ladder index by:
  - height fraction in the mass: darker and rougher in the bottom 0–20 %, mossy or cracked near the ground;
  - distance to "damage points" (openings, corners, eaves, drips, breaches), which pull toward dark or cracked
    in radiating clusters 3–8 blocks across;
  - exposure: the top of a cornice or ridge is lighter (sun-bleached), the underside of an overhang darker
    (soot or wet).
- Ruin weathering (`moss_on`, `vines_on`, `rubble`) follows the same masks: moss on north faces and near the
  ground, vines from ledges, rubble at the foot of breaches, never sprinkled uniformly.
- Light colours mark focal points: the portal, the boss door, the main axis. Use the brightest ladder step or
  a glow block there, and nowhere else at that scale.

---

## 6. Detail hierarchy (macro / meso / micro)

| Level | Read from | Element size | What | Rules |
|---|---|---|---|---|
| Macro | 60–300 | ≥10 | masses, roofs, spires, terraces, rock base | §2 checks; 2–3 strong colours max |
| Meso | 15–60 | 3–10 | bays, arches, buttresses, balconies, windows, gates | rhythm, grouping, depth layers |
| Micro | 0–15 | 1–2 | sills, lanterns, chains, trapdoors, banners, rivets, furniture | only within 12 blocks of a walkable surface or a framed view |

- Micro detail placed where nobody can see it is wasted entries. Concentrate it along paths, at doors, on
  balconies and in rooms.
- Every view a player can stand at (entrance, courtyard, balcony, boss arena) gets one focal point: a statue,
  fountain, rose window, chandelier, machine or tree.

---

## 7. Terrain, approach and sightlines

**Terrain integration**
- No dirt or air visible under walls on any side [CHECK: `support.py` / `fitcheck`].
- Monumental and colossal builds stand on a **base massif**: rock outcrop, earthwork terraces or a battered
  plinth 4–20 high. `terrain_skirt(depth=6, spread=3)` is too small for colossal. Use spread ≈ 8–12 % of the
  footprint and depth 12–30, with rock faces (not grass) steeper than 45°.
- Organic lines (paths, cliffs, banks, tree lines) have no straight run longer than **7 blocks**. Architecture
  can be straight; terrain cannot.
- Retaining walls are battered (stepped outward 1 every 3–4 blocks at the base) and topped with a coping.

**Approach (Lynch: paths, edges, districts, nodes, landmarks)**
- Every structure from monumental up has a designed **approach path**, ≥40 blocks for monumental and ≥80 for
  colossal, that starts outside the footprint at a marker (a road, a waystone, a bridge, a ruined gate).
- **Denial and reward:** the dominant mass is visible from the far end, hidden by terrain, a gate or a forest
  for at least one stretch, then revealed closer and bigger. At least one designed reveal per structure, ideally
  through a framing arch.
- The main axis aligns the approach, the gate, the courtyard and the dominant. Break the axis once (a bend or
  a ramp switchback) so the full view is earned.
- **Compression → release:** before any major space (hall, courtyard, arena), a passage ≤5 wide and ≤6 high,
  ≥6 long. The space after it has ≥4× the passage's cross-section on each axis.
- **Vistas from inside:** ≥2 balconies or windows in upper levels frame either the dominant or the landscape.
  Players remember places they have looked out from.
- **Landmark for orientation:** inside a colossal structure, the dominant (or a light, a chain or a crystal
  column) is visible from ≥50 % of outdoor walkable cells.

---

## 8. Interior coherence

- **Programme first.** Before drawing, list the rooms with purpose, size and adjacency (kitchen beside the
  hall, armoury beside the gate, chapel at the end of the axis, treasury deep and guarded). Each room has
  furnishing matching its purpose (`interior.decorate`, `arch.furnish`).
- **Room proportions:** plan ratio between 1:1 and 1:3 (galleries up to 1:6). Height: ordinary rooms 4–6, halls
  ≥0.5× their short side and ≥8, great halls and naves 1.5–3× their width.
- **No 2-high rooms** except crawlspaces and secret passages tagged as such.
- **Floors** are ≥2 blocks thick between storeys of monumental and colossal builds: a floor plus a beam or
  ceiling layer. Beams span the short side of the room.
- **Interior and exterior agree:** windows on the façade open into rooms, not into solid fill or between floors.
  Floor bands on the façade line up with interior floors ±1 [CHECK: every glass block on the façade has air
  behind it within 2 blocks].
- **Lighting:** walkable cells on the main path have light level ≥8 except in designated dark zones (mob areas,
  ≤25 % of main path). Light sources are hung, wall-mounted or set in fixtures, never floating.
- **Doors:** standard doors are 1×2 (2 tall). Room-to-room openings are 2–3 wide × 3–4 high. Hall portals are 3–5 ×
  4–7, colossal portals 7–15 × 12–30 with a wicket door. Every door has ≥2 walkable cells in front of it on
  each side.

---

## 9. Circulation rules (automated checker)

Model: a **walk graph** over cells `(x, y, z)`. A cell is *standable* when the block below has a full or upper
top surface (full block, top slab, stairs, farmland, path, also bottom slab, carpet, snow), and the cells at y,
y+1 are passable (air, carpet, plants, open door, ladder, mist gate, light block). *Walkway headroom* = number of
passable cells above the floor before the first collider.

Edges:
- horizontal neighbour, |Δy| = 0, or +0.5 / +1 via stairs or slabs (the player's auto-step is 0.6 blocks);
- +1 onto a full block = "jump edge" (allowed, but counted);
- drop of 1–3 = one-way edge; a drop of 4 or more is allowed only into water ≥2 deep or on optional routes;
- ladders, vines, scaffolding and water columns = vertical edges;
- horizontal jump gaps of 1–3 = "parkour edges" (only on optional routes).

Rules (all **[CHECK]**, reported as errors for the main path and warnings elsewhere):

| # | Rule | Threshold |
|---|---|---|
| C1 | Every room, loot container, spawner room and the boss seal is reachable from the entrance | 100 % |
| C2 | Main path headroom (entrance → waystone → boss door → arena) | ≥3 on ≥95 % of cells, never <2 |
| C3 | Main path width | ≥2 (monumental), ≥3 (colossal); 1-wide only on catwalks ≤8 long |
| C4 | Stairs: headroom measured above each tread | ≥3; no tread with a ceiling at +2 |
| C5 | Stair landings | a landing ≥2×2 every ≤12 blocks of rise; main stairs width ≥3 in colossal |
| C6 | Ladders | ≤12 high per run on main path; main vertical links prefer stairs/ramps; ladders OK in towers and optional routes |
| C7 | Jump edges on main path | ≤3 per 100 path blocks; 0 parkour edges |
| C8 | Return path | every one-way drop on the main path has a way back up within 60 path blocks (or is a deliberate shortcut, §10) |
| C9 | Loops | cyclomatic number (E − V + 1 over the room graph) ≥ 1 per ~1500 m² of walkable floor; colossal ≥4 |
| C10 | Vertical links | colossal: each storey or terrace has ≥2 independent links to the one below |
| C11 | Doors | every door has standable cells on both sides; double doors fully openable; no door opening into a wall |
| C12 | Dead ends | a dead end >15 blocks long ends at a reward, secret, vista or lore point |
| C13 | Waystone (site of grace) | ≤40 path blocks from the boss door, and on the safe side of the mist |
| C14 | Path length | entrance → boss: medium 60–150, monumental 150–400, colossal 400–1200 path blocks |
| C15 | Spawners | not within 6 blocks of the entrance or of a waystone; ≥1 escape direction (no spawner in a dead-end 1-wide corridor) |
| C16 | Arena | boss arena headroom ≥ boss height + 4 (≥12 for big bosses), floor diameter ≥ 24 (≥32 colossal); no fall to death unless designed |
| C17 | Water and lava | no unfenced lava within 1 block of the main path; no water flowing over the main path |

Implementation notes: build the graph with `interior._checker` (full-face tests already exist) and run a BFS
from the entrance cells. Mark the main path by A* between the tagged points (`bp.tags["entrance"]`,
`"waystone"`, `"boss_door"`). Print the metrics (path length, loops, worst headroom, jump edges) in
`--preview` and fail `validate.py` on main-path errors. `support.repair` already fixes doors and supports; the
checker reports and does not repair.

---

## 10. Legacy-dungeon level design (Stormveil, Leyndell, Boletaria, Lordran)

**Structure of a legacy dungeon** (colossal tier, one boss at the end, 1–3 mini-bosses):
1. **Front gate** with a guardian (mini-boss or elite group). An obvious, defended main route and a **side
   route** that bypasses the gate (Stormveil: Gostoc's side path versus the main gate). Both converge on a
   central node (a courtyard or plaza).
2. **Hub node** at mid-height: a courtyard that sees the dominant. From here, 2–4 spokes lead to the ramparts,
   undercroft or sewers, a tower and the keep.
3. **Verticality:** the route goes up and down repeatedly. Rooftops, ramparts and broken walls are walkable
   (§9 C2 still applies on the main path). Undercrofts or catacombs sit 10–30 below the hub. Aim for ≥40 % of
   the main path on slopes or stairs, and vertical span ≥60 % of total height.
4. **Shortcuts:** ≥3 per legacy dungeon, which open backwards toward the entrance or waystone:
   - one-way doors (an iron door with a lever only on the far side, or a door barred from one side with a
     trapdoor or bar that the player breaks or opens);
   - lifts (bubble-column water lifts or a lever-operated piston platform if the mod has it, otherwise a
     scaffolding shaft);
   - drop-downs (one-way C8 edges of 2–3 blocks, or a longer drop into water);
   - a ladder dropped from above (a ladder whose bottom section is missing below a trapdoor ledge).
   After the boss, a final shortcut leads back to the outside or the entrance waystone.
5. **Reveals:** at least 2 framed vistas inside (Leyndell shows the Erdtree from almost every plaza; Stormveil
   opens onto the cliffs). The boss tower, dome or statue is visible from the start and reached last.
6. **Risk/reward:** the best optional loot sits on ledges, rooftops, behind a mini-boss or behind a jump. The
   main path never requires a jump to progress.
7. **Optional space:** 30–45 % of walkable area is optional: side wings, secrets (≥2), lore rooms, a hidden
   undercroft with an optional mini-boss (Stormveil's Basement Grave).
8. **Site-of-grace rhythm:** a waystone at the entrance, a "grace" at the hub (unlocked by a shortcut), and one
   before the boss (C13). Never more than ~250 path blocks between graces.
9. **Encounter shaping:** narrow corridors (3 wide) for single heavy enemies; open plazas for groups; ledges
   where enemies (or players) can be knocked off; flying or ranged enemies above, which teach players to look
   up.
10. **Material as wayfinding:** the main path uses a slightly lighter or cleaner floor, and optional areas
    are rougher. Light (warm lamps) marks the way, and darkness marks danger and optional routes.
11. **Boss arena:** reached by compression (a narrow stair or bridge), then release into an arena bigger than
    any room before it, with the fog or mist at the narrow point. The arena is readable: a symmetric plan,
    pillars only if they are part of the fight, and a view out at the top (sky, void, cavern) to show the
    scale.

**Difficulty scaling for re-runs** (NG+-style, matches the owner's request): the layout tags spawner rooms with
"tier" levels so a re-generated or re-entered dungeon can add elite spawners in the optional wings without
changing the geometry.

---

## 11. Organic versus geometric

- Architecture is geometric: straight walls, regular rhythm, symmetry about the main axis. Nature is organic:
  noise, no straight runs longer than 7 and no repetition. **The tension between the two is the beauty.**
  Ruined or overgrown builds lose geometry from the top and the edges inward, never in the middle of an intact
  wall.
- Rock bases, cliffs and caverns use fbm noise with **two octaves** (shape at 16–40 blocks plus detail at 3–6)
  and strata (horizontal bands of 2–5 materials with ±2 jitter).
- Living elements (trees, roots, vines, waterfalls) are placed where water or soil would collect: at the feet
  of walls, in courtyards, under drips. Never on a vertical face without a ledge.
- Giant trees and roots follow branch tapering (child radius ≈0.7× parent) and never end in a stump of the
  same radius.

---

## 12. New structure concepts (not in `structures/` or `docs/structures/`)

All of these are colossal or monumental and different in kind from the existing set (citadel, cathedral,
clockwork town, foundry, observatory, manor, sky harbour, sky isles, sylvan palace, undercity, dwarven city,
lairs, ruins and small sites).

1. **Caldera Ringwall (legacy dungeon, overworld mountains).** A 200-wide ring of curtain walls and bastions on
   the rim of a crater lake, with the keep on a rock needle in the centre, joined by one long bridge. It follows
   the Stormveil template: a front gate with a guardian, a side route along the outer cliff, a courtyard hub, an
   undercroft cut into the crater wall and the boss at the top of the needle.
2. **Pilgrim's Ascent.** A 180-high natural spire climbed by a switchback stairway of 600+ steps, with 6 shrine
   landings, gates, wind-bridges between pinnacles and a summit temple whose bell can be heard far away. The
   route is the structure. Repetition (gates, lanterns) makes the height readable.
3. **Fallen Colossus.** A 160-long armoured statue fallen across a valley, half-buried. Its body is a dungeon:
   enter at the broken hand, cross the ribcage hall (a 40-high vault of ribs) and reach the boss in the helmet,
   overlooking the valley. Rubble field and moss gradients.
4. **The Great Aqueduct.** A 250-long, three-tier arcade (arches 12 / 8 / 4 wide) crossing a valley. A
   water channel runs on top, and a hidden lock-keepers' town lives inside the piers, with sluice puzzles as
   shortcuts between tiers.
5. **Tidal Abbey (Mont-Saint-Michel).** A rocky tidal island in the ocean with a town spiralling up to a
   gothic abbey with a 90-high spire. A causeway connects it at low ground, ramparts sit at the base, and the
   cloister and crypt are inside the rock. This is a spiral climb, unlike any existing structure.
6. **Rock-cut Necropolis (Petra / Abu Simbel).** A 120-high façade carved into a canyon wall with four 40-high
   seated kings, approached through a narrow slot canyon (compression) that opens onto the façade (release).
   Inside: tomb galleries 3 levels deep. Desert or badlands.
7. **Chained Bastion (Nether).** A fortress hanging under the Nether ceiling from 8 colossal chains (links 3×5),
   above a lava lake. Reached by a broken chain-bridge and climbing a chain, with inverted spires hanging below.
8. **Walking Fortress Wreck (steampunk).** A 120-tall brass siege walker frozen mid-stride, with legs as stair
   towers (4 legs, 60-high), an engine-room hull, a gun deck and the bridge on top. It sits in a scorched
   crater, with gear rubble around it.
9. **Shattered Halo (End).** A tilted ring megastructure 180 in diameter, broken into 5 arcs that float at
   different heights, with temples on each arc joined by end-rod light bridges. The boss is at the centre on a
   floating disc. The silhouette is unique against the void.
10. **Glacier Hall of the Frost Jarls.** A longhouse-cathedral 140 long carved inside a glacier: ice ribs,
    packed-ice columns of 5×5, frozen warriors, a meltwater river below and a crevasse bridge, with the exit
    through the glacier snout.
11. **Mire Stilt-City.** A 200-wide wetland town on piles over a mangrove swamp: boardwalk networks at three
    levels, a sunken quarter, a stilted cathedral and a drowned bell tower. Shortcuts are rope bridges and
    hoists.
12. **Dam of the Drowned Valley.** A 160-wide, 90-high curved dam with turbine halls, spillway tunnels
    (water slides as one-way shortcuts), a drowned village visible through the reservoir glass and a boss in
    the valve chamber at the base.
13. **Kneeling Gate.** Two 70-high statues kneeling face to face across a mountain pass, holding a stone
    lintel bridge between their raised hands. Guard-houses in the plinths, a toll town under the arch, a
    treasury inside one statue's head.
14. **Inverted Spire.** A tower built downward into a 150-deep sinkhole, with balconies, bridges to the shaft
    walls and a floor-by-floor descent ending in an underground lake with an arena on an island. Seen from the
    surface it is just a ring of pinnacles around a void.
15. **Sun-Engine Ziggurat.** A 150-wide, 80-high stepped pyramid in desert or badlands, crowned by a colossal
    brass orrery and a sun-lens that focuses light down a shaft to the sun chamber (the boss arena). A
    processional ramp lined with brass sphinxes climbs one face; inside, sand-flooded lower halls, a hypostyle
    hall of 5×5 columns, the astronomer-priests' quarter, a lens-calibration chamber and a sealed tomb gallery,
    with an elevator shaft through the core as the shortcut back.
16. **Leviathan Dreadnought Wreck.** A 188-long brass-and-iron steam ironclad run aground on an ocean reef and
    broken in two: the stern upright under a bridge tower and tripod mast, one of its three funnels fallen
    across the deck, the bow pitched nose-down and half-submerged with its turrets raising their barrels. Enter
    through the breach from a castaways' islet: crew quarters, officers' mess, the main deck, the officers'
    cabins (hub), the engine room's catwalks and the boss in the boiler hall; the magazine's ammunition hoist
    is the shortcut back. Optional: captain's cabin and stern walk, spotting top, the flooded torpedo deck.
17. **Canopy Temple-City.** A 220-wide lost city in jungle: a 66-high stepped stone temple strangled by roots,
    ringed by five hollow custom-built trunks (16 wide, 56-74 high) that carry platform districts at three
    heights joined by sagging rope bridges and brass zip-line pulleys. Climb the trunks' spiral stairs past
    dwellings to the market and the high ward, cross to the temple's upper terrace, then descend: glyph
    library, site of grace, dart-trap corridor, jade-and-gold sanctum, offering hall, root-choked crypt and
    the flooded cenote with its waterfall, whose spiral ledge climbs back up to the summit arena under a
    broken brass sun-disc. A brass elevator in the east trunk is the shortcut back.
18. **Forge of the Basalt Titan (Nether).** A ~190-wide forge over a lava lake in basalt deltas or crimson
    forest, built into and around an 85-high basalt-and-brass titan kneeling on a forge plinth and bent over a
    giant anvil, its right hand raising a sledgehammer over the anvil, its left arm reaching down to it as a
    crane-bridge. Crucibles on the plinth pour lava falls into moulds in the lake. Enter through the gate in the
    plinth: casting hall with glass-covered lava channels, bellows chambers with giant leather bellows, an
    optional slag mine, the crucible terrace (hub), then up the knee and thigh to the forgemasters' barracks in
    the pelvis, the armoury in the belly and the smelting hall in its back, whose chimneys rise from its spine.
    From the neck (site of grace), the hammer-gallery climbs the raised arm (optional) and the crane-bridge
    descends the other arm to the boss arena on the anvil under the hammer. A lift in the spine is the shortcut
    back; the vault sits in the anvil's heel, with a stair down to the lake.
19. **The Starfall Library (End).** A ~170-wide floating archive over the outer islands: a 125-high spindle
    tower of purpur and brass (plinth, stacks, scriptorium, upper hall, domed lens observatory and a needle
    hung with armillary rings) on a rock island, orbited by three ring-shaped reading galleries at three heights
    held by chain-and-end-rod spokes. A meteorite lies wedged in its south-east flank, having torn through the
    middle gallery and cracked the map room open. Enter by the great door (or the side bridge to the low ring):
    map room with a giant floor star-chart, the bookshelf canyons with rolling ladders and catwalks (hub), the
    copyists' scriptorium, the upper hall, the lens observatory at the top; then outside, ramps down to the high
    and middle rings, across the broken gallery on floating book-platforms over a catch basin onto the
    meteorite, down a corkscrew fissure inside it to the site of grace and the boss arena in the crater chamber
    under the tower. The sealed forbidden-stacks vault behind it has a pneumatic-tube lift back up to the map room.
20. **Rust Mesa Mine-City (badlands).** A ~200-wide boomtown carved into and stacked on a striped terracotta
    butte 56 high, crowned by a timber-and-iron headframe whose giant winding wheel tops out above 100. Main
    Street with false-front saloons leads to a stair up the talus; cliff-dwellings and saloons sit on three
    terraces of the south face, linked by cliff stairs, ladders and trestle bridges over a cleft, while a
    mine-cart railway on tall trestles spirals once round the butte to the summit. From the hoist house (hub,
    site of grace) descend inside: the stepped stamp mill with giant gears, the dynamite store and the
    mine-boss office with its vault, the haulage level, the flooded lower gallery and the collapsed shaft, to
    the boss arena in a vast excavated cavern round a half-dug colossal gold-and-copper vein. A cart-lift is
    the shortcut back to the haulage adit; the main shaft is a drop from the hub with a ladderway up.
21. **The Airship Graveyard (savanna / plains).** A ~200-wide crash field round a ruined mooring tower: a
    90-high skeletal mast with a docking ring at the top, one brass dirigible still moored to it, its aft
    envelope deflated and draped over the bare ribs, and three wrecks around it (a gondola buried nose-first, an
    envelope frame lying like a whale skeleton that the approach road walks through, a ship broken in two). A
    scavengers' shanty town of hull plates, gas-bag tents and propeller windmills holds the market (hub). Route:
    the winch house and the gas works with huge gasometers, the stair up the mast to the docking ring, through
    the moored ship's nose and keel into its gondola (bridge, cabins, saloon, cargo hold, engine nacelles on
    catwalks), up the climbing shaft through the gas cells to the boss arena on the ship's top deck; the sealed
    treasury hold and the gangway back to the mast crown, where the cargo-lift shaft drops to the winch house.
22. **The Echo Cathedral (deep dark / dripstone caves).** A ~180-long gothic cathedral of deepslate and
    tarnished brass built inside a vast cavern 100 blocks down, its flying buttresses anchored into the cave
    walls, its twin west towers and nave roof under dripstone, and behind the apse a giant pipe organ whose
    pipes rise 60 blocks into the cavern ceiling. Sound and silence: sculk (decoration only), bells, amethyst
    and muffled wool. From the pilgrims' camp in a side cave, a low tunnel opens onto the forecourt (reveal);
    the great portal is barred, so enter by the west tower, cross the nave of 7x7 columns (side chapels) and
    climb the tower's newel stair to the choir loft; walk the triforium to the transept and out over a flying
    buttress into the choristers' dormitory in the cave wall, down a rock stair to the flooded crypt of
    sculk-overgrown tombs (site of grace) and up the choir turret to the boss at the organ console in the apse.
    Optional: the bell chamber with its cracked bronze bell, the bellows loft, the cantors' library; behind the
    organ, the sealed reliquary. A bubble lift in a brass organ pipe climbs from the crypt to the crossing; the
    choir grille, the dormitory stair door and the portal's wicket are the other ways back.
23. **The Cloud Pagoda (cherry grove / meadow mountains).** A ~180-wide temple complex on a terraced mountain
    garden: a nine-tiered, 110-high pagoda of cherry wood and white plaster with brass hip ornaments and clockwork
    wind-chimes on every eave, the brass skeleton of a clockwork dragon coiled round its lower tiers, its skull
    enshrined on the north terrace. From the pilgrims' camp, through a moon gate and over koi ponds on zig-zag
    bridges, stairs climb three garden terraces past stone lanterns, the tea house, the bell pavilion, the dragon
    shrine (hub) and the monks' dojo to the pagoda door; inside, each tier is a room of its own (prayer hall,
    scroll library, armoury of practice weapons, meditation hall with a sand garden, mechanical orrery of the
    seasons, abbot's quarters, chime engine, last stair). The boss waits on the open top tier under the spire;
    the counterweight lift in the central pillar drops back to the prayer hall.
24. **The Soul Engine (Nether: soul sand valley / warped forest).** A ~180-wide machine-ossuary on the valley floor
    (fixed height, cavern fit; every open interior volume is explicit air so the netherrack cannot fill it): a
    cathedral-sized engine block of blackstone, soul soil and tarnished brass (105 x 85, 40 high) on a battered
    plinth with buttresses every 13 blocks, fed by two bone conveyors on trestles, crowned by a crankcase whose six
    colossal pistons stand frozen at different heights over the crank trench, four ribbed chimneys venting blue
    flame, warped fungus eating the west and north walls. From the lost pilgrims' camp, the bone road passes under a
    ribcage arch (the reveal) to the bone gate's wicket; the gate tunnel opens into the pressure hall (hub) round its
    pressure vessel. North: the bone hopper hall, the soul-soil bunker, the soul furnace (three soul-fire fireboxes
    open on the east facade, the boiler drum); its stair climbs to the stokers' mess, the governor's control room
    (flyball governor, gauge wall, balcony over the hub) and the valve room, then a newel stair in a disused
    cylinder sleeve (the piston shaft) rises to the site of grace on the crankcase. Through the mist, the boss on
    the crankshaft deck (39 x 39) beside the trench of connecting rods and the flywheel bay; the soul reliquary
    behind sealed bars. Optional: the piston gallery (spare pistons on cradles, catwalk) and the ossuary below
    (bone-ribbed nave, the charnel pit and its bone throne, the builders' crypt, whose stair climbs back into the
    gallery: a loop). Shortcuts: the piston lift (grace -> ossuary stair hall), the bone chute (reliquary -> hay in
    the gallery), the furnace's one-way iron door into the hub.
25. **The Clockwork Asylum (dark forest / pale garden).** A ~185-wide gothic sanatorium turned automaton
    workshop on a steep wooded hill (a 4-thick noise-faced shell, rock outcrops, crooked dark oaks): a 100-high
    clock tower with four cracked dials (glass ring, brass hour marks, iron hands) and a tall spire over a central
    hall, two long ward wings of barred lancet windows ending in pavilions, a chapel, a broken greenhouse and a
    walled cemetery with crooked iron fences and a mausoleum. From the woodcutters' camp at the foot, the
    gatehouse's funicular (powered rails, minecart) climbs the slope to the station yard; the cemetery leads to the
    main hall (hub, gallery, Iron Orderly). West wing: patient cells, the operating theatre with brass surgical
    arms, the conversion ward; east wing: the ward, the records archive, the laundry and its chute; below, the
    hydrotherapy baths and the basement stair back to the hall. The tower flights climb through the clock
    mechanism (great wheel, escapement, pendulum shaft) to the site of grace; through the mist, the boss in the
    35 x 35 clock chamber behind the cracked dial; the director's office behind sealed bars, whose drop shaft
    falls into a pool and back to the mechanism. Shortcuts: the funicular down, the laundry chute to the
    basement, the chapel's one-way iron door.
26. **The Icebound Fleet (frozen ocean / ice spikes / snowy plains).** A ~220-wide polar expedition frozen into the
    pack ice (wetland fit: the sea surface counts as ground, the build lays its own ice field one or two layers
    deep, every walked pocket under it sealed): a colossal 120-long dark-iron paddle icebreaker locked at a list,
    two fat leaning copper funnels, a raked ram bow ridden up on a pressure ridge, paddle wheels half sunk in holes
    of black water; beside it two small timber supply ships (Fulmar, Petrel) joined by a sagging rope bridge, a
    brass ice-drill derrick, pressure ridges, blue packed-ice spires and the spine of a frozen-over whale. From the
    sledge camp, under the whale's ribs and through a gap in the ridge (the reveal) to the drilling camp (hub);
    the Fulmar's frozen hold and chart room, the Petrel's kennels and galley, its ice door (opens from inside) onto
    a snow trench that sinks under the ice into the icebreaker's crushed coal bunker. Inside: the 27-high boiler
    room (four boilers, paddle shaft, galleries), the crew mess, the officers' mess, the captain's cabin; out on
    the boat deck, a newel stair inside the forward funnel and a gantry to the wheelhouse (site of grace), then
    the enclosed bridge stair and the mist to the arena on the forecastle under the bridge front. The expedition
    strongroom below the bow behind sealed bars; shortcuts: the ice slide out of the ram's breach, the crew mess's
    one-way hatch to the side-deck gangway, the cargo crane's jib dropping into a fishing hole by the trench.

---

## 13. Gap analysis: arch.py, megakit.py and STYLE.md against this guide

| Issue | Where | Fix |
|---|---|---|
| Monumental capped at 50–90 / ≤100 footprint, no colossal tier | STYLE.md §1, §6 | Replace with §1 tiers; chunking already allows larger pieces |
| Uniform bays | `facade(pilaster_every=4)` | `bay_pattern="ABA"`, `major_every`, variable widths, central emphasis |
| Isotropic noise, no gradients | `Palette.pick` | `GradientPalette` (below) |
| Spires 2:1 at most | `spire(steep=2)`, citadel/clockwork/overworld_a copies | Parametrise by target ratio, add octagonal, ribbed and lucarne variants in one helper |
| Ladders as the only tower circulation | `round_tower(ladder=True)`, `square_tower` (floors every 6) | `stair_core` option (spiral or newel stair, headroom ≥3) |
| `terrain_skirt` too small, grass on steep faces | depth 6, spread 3 | `massif()` with rock faces, strata, battered retaining walls |
| `dome` is a bare hemisphere | no drum, lantern or pendentives | `dome(drum_h=, lantern=, profile="pointed"|"onion"|"hemi")` |
| No arcades, vaults, flying buttresses or bridges in the kit | redefined per file: overworld_a `arcade`, `flying_buttress`; end `bridge`, `flying_buttress`; 6× `vault`; 4× `pinnacle` | Move into `arch.py` once, with parameters |
| No circulation checks | `interior.find_rooms` is per level, `support` handles doors and supports only | `wf/circulation.py` (§9) wired into `--preview` and `validate.py` |
| No composition checks | none | `wf/composition.py`: skyline peaks, dominance ratio, flat-wall scan, hull fill |
| STYLE says "break symmetry a little" without hierarchy | STYLE.md §1 | One dominant, ratio rules (§2) |
| Interiors read as generic | `furnish` kinds | Room programme per structure (§8) and purpose-based decoration |
| `stair_run(clear=4)` has no landings or width rules | arch.py | `grand_stair()` with landings every ≤12 rise |

**Recommended helpers** (signatures are proposals, all in `arch.py` unless noted):

```python
class GradientPalette(Palette):          # ladder light->dark; index = f(height_frac, damage_dist, exposure) + jittered noise
    def __init__(self, ladder, *, y0, y1, base_dark=0.35, damage=(), cluster_r=6, jitter=2, seed=0): ...
def massing_plan(tier, footprint, seed) -> list[Mass]   # dominant + secondaries with §2 height ratios
def tiered_facade(bp, face, line, u0, u1, y0, y1, *, ladder, trim, bays="A-B-A", bay_w=(6, 9),
                  base_frac=0.18, crown_frac=0.22, depth_scale=1)       # base/body/crown + grouped bays
def arcade(bp, face, line, u0, u1, y0, h, *, span, pier, arch="round"|"pointed", tiers=1)
def rib_vault(bp, x0, z0, x1, z1, y_spring, rise, *, rib, web, bosses=None)
def flying_buttress(bp, wall_pt, pier_pt, *, thick, pinnacle=True)
def pinnacle(bp, x, y, z, *, h, block, cap, finial)                     # one shared version
def spire(..., ratio=4.0, plan="round"|"square"|"octagon", ribs=None, lucarnes=0)
def grand_stair(bp, start, direction, rise, *, width=3, landing_every=10, balustrade=None, flare=0)
def stair_core(bp, cx, cz, y0, y1, *, r=3, kind="spiral"|"newel", headroom=3)
def gatehouse(bp, face, line, u, y, *, gate_w, gate_h, towers=2, wicket=True, portcullis=True)
def curtain_wall(bp, path_pts, y, h, *, thick=3, walk=True, crenels=True, towers_every=24)
def bridge_span(bp, a, b, *, width, arch_span, piers_every, deck_y, rails=True)   # replaces end/sylvan copies
def massif(bp, outline, y_top, *, height, batter=0.25, strata=("stone","andesite","tuff"), seed=0)
def terraces(bp, centre, levels, *, setback=0.25, retaining=True)
def colonnade(bp, a, b, y, *, every, col_r, h, entablature=True)
def statue_colossus(bp, base, pose, height, palette)                   # for concepts 3, 6, 13
def framed_view(bp, eye, target, *, frame="arch"|"window", w, h)       # carve an opening on the line eye->target
# wf/circulation.py
def walk_graph(bp, ground=0, void_solid=False) -> Graph
def check_circulation(bp, tags, tier) -> Report                        # C1–C17 metrics and errors
# wf/composition.py
def skyline_report(bp) -> dict    # peaks per elevation, dominance ratio, longest flat roofline, hull fill
def flat_wall_scan(bp, max_side) -> list[Region]
```

Also add `bp.tags` (named points: `entrance`, `waystone`, `boss_door`, `hub`, `vista`) so the checkers and the
level design can talk to each other.

---

## 14. Review loop additions (on top of STYLE.md §7)

1. Render a **far preview** (orthographic silhouette from 4 sides at about 150 blocks, single colour) and check
   §2 by eye as well as through `skyline_report`.
2. Render the **approach view** from the approach path start marker.
3. Run `check_circulation`. The main path report must have 0 errors. Post its metrics in the commit message.
4. Ask yourself: what is the dominant? Where does the eye go first? Where do I feel small? Where do I look out?
   Where is the shortcut? If any answer is "nowhere", the build is not done.

## 15. Reference mod: When Dungeons Arise (jules, 2026-10-08)

jules pointed to *When Dungeons Arise* (WDA, ~40 structures by Aureljz) as the target level for structures. Its
public pages give names and a philosophy, no sizes; the points marked (seen) come from the CurseForge page and
changelogs, the others are our reading of the mod. Take the principles, never its assets or layouts.

What it does well, and what we copy in spirit:
1. **One readable silhouette per structure** (seen: "imposing", "massive"). Each is identifiable from 200
   blocks: thorn-covered twin towers (Thornborn Towers), a giant stag (Ceryneian Hind), a palace of minarets
   (Shiraz Palace), sky galleons (Heavenly Conqueror / Rider / Challenger), a war galley (Typhon). Our rule:
   name the silhouette in one noun phrase before building (§2), and check it in the far preview (§14).
2. **Variety of kind, not of skin** (seen: temples, palaces, fortresses, cities, ships at sea, airships with no
   port, mines, coliseums, tree houses). Half of WDA is not a "building on the ground": things that sail, fly,
   hang, or are a creature. §12 concepts 3, 7, 8, 9 and 14 go that way; prioritise them over another castle.
3. **Assembled from rooms and passages** (seen: randomised layouts). Big structures are jigsaw kits, so two
   copies differ. Ours are mostly one fixed blueprint; colossal builds should expose variant wings or rooms
   (Python seed per variant, as the dungeon layouts already do) so a second visit is not a replay.
4. **Too big is a real risk** (seen: Thornborn Towers were "a little too big, even for this mod", smaller
   variants added). Keep the §1 colossal budget, and ship a smaller variant of the largest builds.
5. **Broken-bridge terminators** (seen). A passage that ends in a collapse is a cheap way to suggest a larger
   whole and a view out. Use them at kit edges, with a rail so the audit's walk graph stays clean.
6. **Loot gradient** (seen: ship loot from gold nuggets to rare treasure; guides: perimeter chests poor, vault
   best). Map it: entrance and perimeter tier 1, mid-level tier 2, vault behind the boss or the hardest climb
   tier 3. One vault per structure, never loot scattered evenly.
7. **Difficulty by tier, mobs with gear** (seen: late-game dungeons such as Shiraz Palace and Keep Kayra field
   mobs in enchanted diamond; easy windmills and houses). Each structure gets a declared tier (early / mid /
   late) that sets spawner density, mob equipment and loot tables; easy small sites sit between the big ones.
8. **Structures that point to other structures** (seen: passive structures hold explorer maps to dungeons).
   Our small sites (camps, huts, waystones) should carry a map or a journal clue to a colossal neighbour.
9. **Placement in clusters** (seen: structures "usually spawn together"). A colossal build reads bigger with
   one or two small satellites (camp, wreck, watch post) on the approach (§7).

Where Brasshaven must go further than WDA: real bosses with arenas (§10), shortcuts that loop back (C-rules),
and interiors whose rooms make sense (§8). WDA mostly relies on spawner density; we use level design.

Sources: https://www.curseforge.com/minecraft/mc-mods/when-dungeons-arise ,
https://www.minecraft-guides.com/mod/when-dungeons-arise/ , https://craftdownunder.co/guides/mods/when-dungeons-arise

---

## Sources

- WesterosCraft building guides: fundamentals, exteriors, gradients, interiors, layout and foundation —
  https://www.westeroscraft.com/docs/building/fundamentals ,
  https://www.westeroscraft.com/docs/building/fundamentals/exteriors ,
  https://www.westeroscraft.com/docs/building/fundamentals/gradients ,
  https://www.westeroscraft.com/docs/building/fundamentals/interiors ,
  https://www.westeroscraft.com/docs/building/fundamentals/layout-foundation
- Minecraft.net, "Tutorial: tips for landscaping and terraforming" (7-block straight-run rule) —
  https://www.minecraft.net/en-us/article/tutorial--tips-for-landscaping-and-terraforming
- Minecraft.net, "Colossal city" (Octovon's 2000×2000 build: centre-out construction, terraformer role) —
  https://www.minecraft.net/en-us/article/colossal-city
- BlockWorks interview (Byteside) — https://byteside.com/2021/05/blockworks-interview-creating-amazing-worlds-in-minecraft
- "How to be a Better Minecraft Builder" (three viewing distances, false shadows, top-down roofs) —
  https://videohighlight.com/v/WD7Uw-ktI9E
- BuildTheEarth scale rules (1 block = 1 m) — https://bte.readthedocs.io/en/latest/archive/old/buildingrules/
- Stormveil Castle (routes, side path, verticality, Basement Grave) — https://en.wikipedia.org/wiki/Stormveil_Castle
- Leyndell, Royal Capital — https://eldenring.wiki.gg/wiki/Leyndell,_Royal_Capital
- Game Developer, "9 things we can learn about game design from Dark Souls" (shortcuts, vistas, verticality) —
  https://www.gamedeveloper.com/design/9-things-we-can-learn-about-game-design-from-dark-souls
- Game Developer, "Cutting through the fog of Dark Souls" — https://www.gamedeveloper.com/design/cutting-through-the-fog-of-dark-souls-part-one-
- ArchDaily, "How video game architecture is speaking to you" (compression and expansion, light, materials) —
  https://www.archdaily.com/974690/how-video-game-architecture-is-speaking-to-you
- ArchDaily, "The power of scale" (monumental versus human scale) —
  https://www.archdaily.com/1028277/the-power-of-scale-how-proportions-shape-human-experience
- Landmarks in level design (denial and reward, orientation) — https://tancoque.design.blog/
- Kevin Lynch, *The Image of the City* (paths, edges, districts, nodes, landmarks) —
  https://ecampusontario.pressbooks.pub/studioskills/?p=172
- Highest church naves (Beauvais 47 m, Amiens 42.3 m, Cologne 43.35 m) — https://en.wikipedia.org/wiki/List_of_highest_church_naves
- Amiens Cathedral dimensions (Structurae) — https://structurae.net/en/structures/amiens-cathedral

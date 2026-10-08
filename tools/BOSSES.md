# Brasshaven — boss guide (Elden Ring style)

Each great structure ends in a boss fight that players remember. A boss is three things, all made here
without launching the game:

1. a **3D model with animations**: `tools/wf/mobs/<id>.py`, written with the DSL in `tools/wf/models.py`
   and previewed by `tools/wf/model_render.py`;
2. a **moveset**: `src/main/java/com/brasshaven/entity/boss/<Class>.java`, extending
   `com.brasshaven.boss.WayfarerBoss`;
3. a **lair**: the descent and the arena in the structure, written in its own module
   `tools/wf/structures/lair_<id>.py` and called from the structure builder.

The finished example to copy is the Drowned Warden: `tools/wf/mobs/drowned_warden.py` and
`src/main/java/com/brasshaven/entity/DrownedWarden.java`. Its arena is in `tools/wf/structures/citadel.py`,
in `arena()` and `arena_mist()`.

## 0. What you may edit
- **Yours:** `tools/wf/mobs/<id>.py`, `src/main/java/com/brasshaven/entity/boss/<Class>.java`,
  `tools/wf/structures/lair_<id>.py`, plus the few lines in your structure's builder that call your lair.
  The entity is already registered, with its name, spawn egg, loot table and `/brasshaven boss <id>` demo
  command. Its hitbox comes from `WIDTH`/`HEIGHT` in your class.
- **Never edit shared files**, because other builders work in parallel: `ModEntities`, `ModItems`,
  `content.py`, `gen_*.py`, `mobs/__init__.py`, `WayfarerBoss`, `BossAttack`, `BrasshavenClient`, and
  other structures. If the engine lacks something, write a private helper in your boss class (static
  methods, inner `Effect`s) and mention it in your report.

## 1. The model (`tools/wf/mobs/<id>.py`)
Read the docstring of `tools/wf/models.py` first.

**Axes** (Minecraft model space, in pixels, 16 px = 1 block):
- `-y` is up, `-z` is forward (the face), `+x` is the creature's left.
- The root bone sits on the ground: `m.part("bone", pivot=(0, 24, 0))`. Children use negative y.

**Scale:**
- Bosses are huge: 3 to 6 blocks tall (48–96 px), with silhouettes readable from 30 blocks away.
- Set `WIDTH`/`HEIGHT` in the Java class to match the model.
- Typical size is 35–120 cubes and a 256×256 texture.

**Silhouette first.** Give each boss one unmistakable shape idea and exaggerate it:
- the Bell Keeper's bell-hammer;
- the Root Mother's crown of branches;
- the spider's eight crystal legs.

Use asymmetry: a cape, a broken horn, one huge arm. Avoid "a humanoid box with a texture".
Quadrupeds, spiders, serpents, floating wraiths and multi-armed bodies are all fine: build them from
nested parts.

**Painting.** Paint with intent, never plain noise:
- plates with rims (`framed`), bands (`bands`), panel lines, rivets, runes;
- highlights on top edges, darker undersides;
- face details (eyes, teeth, cracks).

Use `glow=` for eyes, runes, lava cracks and crystals. These become an emissive layer that shines in the
dark.

**Animations:**
- **`idle`** is always playing: breathing, swaying, a cape or tail that moves.
- **`walk`** is a walk cycle, driven by speed.
- **One action per move**, plus `roar` (phase change) and `stagger` (posture broken). Every action:
  - **Anticipation:** a long, readable wind-up of 0.5–1.1 s (the telegraph players learn).
  - **Strike:** a fast hit of 0.1–0.25 s, using `"linear"` interpolation for snap.
  - **Recovery:** 0.4–0.8 s, ending exactly at rest. **Every channel's last keyframe must be (0, 0, 0)**
    (scale (1, 1, 1)).
- The **impact time** in seconds × 20 must equal the move's wind-up ticks in Java (Drowned Warden: thrust
  hits at 0.75 s ↔ `timing(15, …)`).
- Max 16 actions.

**The loop is mandatory: at least 4 iterations.**
1. Run `python3 tools/gen_models.py --preview --only <id>`.
2. Read `build/previews/models/<id>.png` (front / side / back, then the poses of every action) and
   `<id>_tex.png` (the painted texture with UV islands).
3. Critique honestly: is the silhouette distinctive? are the proportions right? does every pose read at a
   glance? does any part float or clip? are the textures detailed rather than noisy?
4. Fix, then render again.

## 2. The moveset (`entity/boss/<Class>.java`)
Extend `WayfarerBoss`, following `DrownedWarden.java`. The engine already gives you the following:

**Built into every boss:**
- the boss bar at the bottom of the screen;
- a staged phase 2: an invulnerable roar with a shockwave, then `onPhaseTwo`;
- posture and stagger (+50% damage while staggered);
- the arena reset and leash;
- "ENEMY FELLED" on death.

**Methods to override:**
- **Always:** `attributes()`, `actionTicks()` (return `MobAnims.<Class>.TICKS`), `defineAttacks(...)`,
  `roarAction()`, `staggerAction()`, `barColor()`, `maxPoise()`.
- **Optional:** `phaseTwoAt()`, `preferredRange()`, `bossTick()`, `onPhaseTwo()`, `onDefeated()`.

**Building a move:** `BossAttack.of(name).anim(MobAnims.<Class>.X).timing(windup, active, recovery)`, then:
- `.range(min, max)`, `.cooldown(t)`, `.weight(w)`;
- `.phaseOne()` / `.phaseTwo()`, `.track(bool)`;
- `.start` / `.windup` / `.impact` / `.active` / `.end` steps.

**Helpers on the boss:**
- **Hits:** `hitArc`, `hitLine`, `hitCircle`, `strike`.
- **Telegraphs:** `telegraphRing`, `telegraphArc`.
- **Movement:** `lunge`, `forward`, `ahead`.
- **Combat:** `summon` (minions never hurt the boss), `victims`, `chain` (combos).
- **Timed effects:** `addEffect(WayfarerBoss.wave(...))` (a ring you jump over),
  `addEffect(WayfarerBoss.eruption(...))` (a warned ground burst), or your own `Effect` lambdas.
- **Vanilla projectiles** are welcome: `SmallFireball`, `ShulkerBullet`, `EvokerFangs`, arrows, `LlamaSpit`,
  `WindCharge`… Check their constructors in the stubs before use.

**Design rules (Elden Ring feel):**
- Phase 1 has 4–5 moves; phase 2 adds 2–4 new, faster or longer moves and combos (`chain` in `.end`).
- Every move is readable (wind-up ≥ 10 ticks with an animation **and** a ground telegraph) and leaves a
  punish window (recovery ≥ 8 ticks).
- Mix close, mid and far range so the player cannot just stand back.
- Include at least one gap-closer, one area move, one delayed or tricky move (delayed swing, double
  wave), and one "spectacle" move unique to this boss.
- **Health:** Overworld 320–420, underground 420–520, Nether 520–650, End 700+ (co-op scaling is
  automatic). **Hits:** 8–22. Beatable solo with good diamond gear by learning the patterns.
- Sounds and particles from vanilla, used generously. They are the boss's voice.

**Checking 26.2 APIs.** The game is not available, so check every signature in the stubs before using it:
- stubs: `/tmp/claude-0/-home-user-mode-minecraft/56f1bf77-a458-5793-adc7-375815e90045/scratchpad/stubs/`
  (grep them);
- decompiled sources: `.../scratchpad/mc262/`.

## 3. The lair (`tools/wf/structures/lair_<id>.py`)
The user wants **depth**: the boss waits at the bottom of a descent, not in the courtyard.

- **Descent.** From the existing structure (a crypt, a cellar, the library's secret study…), stairs or a
  secret passage lead **down one or two levels** of catacombs. The rooms are varied (ossuary, flooded
  crypt, collapsed gallery, trap corridor, chapel) and include:
  - 1–2 spawners and some loot;
  - a "site of grace" just before the mist: a waystone (`MOD["waystone"]`), a few lights and a bench.
- **Arena.** A large, memorable, themed room:
  - radius 12–20, ceiling ≥ 10 (≥ 16 for flyers and giants);
  - a clear floor with few obstacles;
  - well lit, with architecture that frames the fight (pillars at the edge, a dais, statues, a broken
    dome).
- **Seal.** `bp.boss_seal(x, y, z, "brasshaven:<id>", radius)` at the centre, on the floor level. The boss
  spawns on top of it when a player walks within 0.8 × radius.
- **Mist.** `bp.mist(x0, y0, z0, x1, y1, z1)` across **every** entrance, called **after** carving the
  doorways (it only fills open cells).
- **Reward.** A reward room or chest past the arena, using the structure's existing loot table names.
- **Exceptions:** sky island (arena on the island top), soul tower (arena at the summit) and void nest
  (existing arena). For these, add the seal and mist to the existing arena.
- **Limits.** Stay within the template limits: under ~100×100 footprint and ~110 tall, underground
  included. The underground part goes below blueprint y=0, and `terrain_skirt`/`beard` handle the rest.
- **Loop.** Iterate with `python3 tools/gen_structures.py --only <structure> --preview`, then read
  `build/previews/<structure>__<piece>{,_back,_cut}.png`. For underground levels, write small cut-render
  scripts in a **private** scratchpad sub-folder named after your agent (never generic file names).

## 4. Done means
- `python3 tools/gen_models.py` and `python3 tools/gen_structures.py --only <structure>` both succeed.
- `python3 tools/validate.py` reports **0 errors**.
- `bash /tmp/claude-0/-home-user-mode-minecraft/56f1bf77-a458-5793-adc7-375815e90045/scratchpad/check.sh`
  reports **0 errors** in your files. Other builders compile in parallel, so ignore errors in files you
  don't own, but report them.
- Your report lists, for each boss:
  - the concept;
  - the moveset (phase 1 / 2, with numbers);
  - the lair (levels, rooms, arena size);
  - the preview paths.

## 5. Champion of the Clockwork Citadel: The Grand Clockmaker (Le Grand Horloger)
Files: `tools/wf/mobs/grand_clockmaker.py` (model, shared steampunk paint in `tools/wf/mobs/brasswork.py`),
`src/main/java/com/brasshaven/entity/boss/GrandClockmaker.java` (moveset),
`tools/wf/structures/lair_grand_clockmaker.py` (lair, called at the end of `clockwork.py`'s citadel builder).
Reward: `remembrance_grand_clockmaker` → **Clockmaker's Pendulum** (`clockmaker_pendulum`, ARC sweep that slows),
plus brass gears, a Clockwork Heart and a clock (`gen_data.py`). Quest: `explorer/boss_grand_clockmaker`.

**Concept.** A 4.4-block Victorian automaton gentleman: stilt legs on cog knees, brass tailcoat, a chest that *is*
a clock face (cream dial, aether hour marks that glow, iron hands that always turn), a brass mask with a waxed
moustache and a glowing monocle under a top hat, two wings of spinning cogs, and a pendulum cane.

**Stats.** 400 health (Overworld range), armour 12, toughness 4, poise 75, yellow bar, phase 2 at 50%.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-2 | 18 / 3 / 13 | 0-6.5 | Pendulum swing over 220°, 15 damage. P2: 35% chains into slam. |
| slam | 1-2 | 20 / 3 / 13 | 0-7 | Cane slam 3.5 ahead (18) + a spark ring to jump (8). P2: second ring, 40% chains into gears. |
| gears | 1-2 | 12 / 4 / 10 | 4-24 | Fan of 3 (P2: 5) brass cogs, 7 damage each (`HotRivetEntity`). |
| summon | 1-2 | 16 / 2 / 14 | any | 2 (P2: 3) Clockwork Spiders, never more than 4 alive; they wind down when he dies. |
| timestop | 1-2 | 24 / 4 / 12 | 0-14 | Hands rewind, a 9-block ring closes; whoever is inside at the chime: Slowness IV + Mining Fatigue III, 2 s. |
| blink | 2 | 10 / 2 / 6 | 6-26 | "Time skip": teleports 2.5 blocks behind the target, then chains a sweep. |
| chime | 2 | 20 / 24 / 12 | 0-20 | Midnight: 12 bells toll in turn on a 6-block circle (11 each), then one under every player (12). |

**Lair (the Clock Vault).** A stair opens in the floor of the clock tower's entrance hall (east side) → level 1,
the **Gearworks** (y -10: machines, wall cogs, a Clockwork Spider spawner, two workshop chests) → a second stair →
the **site of grace** (y -21: waystone on a brass dais, benches, lamps) → mist → the **Clock Vault** arena (radius
13, 12-block walls, dome to 18 blocks): a floor that is a giant clock face stopped at midnight, twelve brass
pilasters with Edison lamps, wall cogs, and a great pendulum hanging high over the seal → mist → the
**Clockmaker's study** (reward chests).

Previews: `python3 tools/gen_models.py --preview --only grand_clockmaker` → `build/previews/models/grand_clockmaker.png`.

## 6. Champion of the Walking Fortress: The Iron Helmsman (Le Timonier de Fer)
Files: `tools/wf/mobs/iron_helmsman.py` (model, shared steampunk paint in `tools/wf/mobs/brasswork.py`),
`src/main/java/com/brasshaven/entity/boss/IronHelmsman.java` (moveset). No lair module: the arena is the walker's
existing top deck, whose seal wakes him (`BOSS` in `tools/wf/structures/walking_fortress.py`).
Reward: `remembrance_iron_helmsman` → **Helmsman's Anchor** (`helmsman_anchor`, heavy LITHITE weapon 8 / -3.4, ERUPT:
a broadside of fiery bursts down a 12-block line), plus brass, map fragments, a Clockwork Heart, diamonds and chains
(`gen_data.py`). Quest: `explorer/boss_iron_helmsman`.

**Concept.** A 5.2-block armoured sea captain fused into a steam harness: barrel chest under a navy captain's coat
of riveted iron plates with brass trim, a sunken visor helm with a peaked brim and a glowing amber slit, a banded
copper boiler on his back with a short smoking stack leaning to his left. Asymmetric silhouette: the right arm is a
banded harpoon-cannon under a great pauldron (a barbed harpoon in the muzzle); the left arm drags a ship's anchor
on a chain, its crown and barbed flukes scraping the deck beside him.

**Stats.** 450 health (a deliberately hard Overworld boss), armour 15, toughness 6, poise 95, knockback resistance
1.0, white bar, phase 2 at 50% (+15% speed).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-2 | 20 / 4 / 14 | 0-7 | Anchor hauled back to his left, swung over 210°, 17 damage. P2: 40% chains into slam. |
| slam | 1-2 | 22 / 3 / 15 | 0-8 | Anchor overhead, crashed 4 ahead (22, r 3.2) + a shockwave ring to jump (10, out to 10). P2: second fire ring (9), 35% chains into harpoon. |
| harpoon | 1-2 | 16 / 4 / 14 | 5-18 | Aim line telegraphed; the first creature on the line takes 10 and is reeled in to 2.8 blocks ahead, then he chains a sweep. |
| vent | 1-2 | 24 / 10 / 12 | 0-5.5 | Boiler hisses, a 6-block steam ring; burst 12 + 3 s fire, then lingering steam (4 every 5 ticks). Punishes hugging. |
| charge | 1-2 | 16 / 14 / 12 | 6-20 | Shoulder ram along a smoke line, 16 once per target. P2: 50% chains into sweep. |
| overload | 2 | 24 / 30 / 14 | 0-14 | Boiler overload: 4 rings (6/10/14/18 bursts at r 3/6/9/12) of smoke-warned fire bursts spreading out, 14 + fire each. |
| whirl | 2 | 14 / 40 / 14 | 0-9 | Anchor spun on its chain for 2 s while he walks the target down: 10 every 6 ticks in r 5.5. |
| broadside | 2 | 20 / 38 / 14 | 0-30 | Spectacle: cannon raised, raid horn; 3 volleys of shells on every player's position (1 s smoke-ring warning, 16, r 2.6) + 6 strays on the deck. Particles and sound only, no block damage. |

**Lair (the top deck).** Up the Walking Fortress: the breach in a planted foot → spiral stair in the shin → knee
chamber → thigh stair → cargo hold → engine room → gun deck → companionway stair arriving behind the arena → mist →
the **top deck** arena (open air, radius 15, ~89 blocks above the crater floor) between the bridge tower and the two
smokestacks → the vault in the bridge tower behind sealed bars that open when he falls.

Previews: `python3 tools/gen_models.py --preview --only iron_helmsman` → `build/previews/models/iron_helmsman.png`.

## 7. Champion of the Fallen Colossus: The Bronze Sentinel (La Sentinelle d'airain)
Files: `tools/wf/mobs/bronze_sentinel.py` (model), `src/main/java/com/brasshaven/entity/boss/BronzeSentinel.java`
(moveset). No lair module: the arena is the toppled statue's helm, whose seal wakes it (`BOSS` in
`tools/wf/structures/fallen_colossus.py`). Reward: `remembrance_bronze_sentinel` → **Greatsword of the Sentinel**
(`sentinel_greatsword`, LITHITE 8 / -3.2, ERUPT: a crack of rune light tears along a 12-block line and throws foes up),
plus copper, map fragments, emeralds, diamonds and moss (`gen_data.py`). Quest: `explorer/boss_bronze_sentinel`.

**Concept.** The statue's living guardian, a 5.6-block knight automaton of stone under bronze plate: verdigris streaks
running down every plate, moss in the knees, elbows, waist and shoulders, a great helm whose cross visor is broken at
the lower corner and glows gold from inside (the crest snapped off behind), a gold rune band across the breastplate
and a torn mossy tabard. Asymmetric silhouette: a tower shield taller than a man on the left arm (gold-lit sun boss,
cracked verdigris field), a long bronze greatsword in the right hand whose point rests on the ground in front of it.

**Stats.** 460 health (a hard Overworld boss), armour 14, toughness 5, poise 100, knockback resistance 1.0, green
bar, phase 2 at 50%: the plates fall away (armour -6, +20% speed).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| bash | 1-2 | 14 / 8 / 12 | 3.5-14 | Shield drawn in (spark line on the path), lunge behind the shield: 12 + big knockback, once per target. P2: 40% chains into cleave. |
| overhead | 1-2 | 22 / 4 / 16 | 0-10 | Greatsword over the helm, crashed 3.5 ahead (22, r 2.6), then a crack runs 12 blocks along the ground (14, warned by gold dots). P2: three cracks in a 50° fan. |
| cleave | 1-2 | 16 / 3 / 14 | 0-7.5 | Blade drawn back to its right, swept over 220°: 18. P2: 35% chains into overhead. |
| shieldwall | 1-2 | 10 / 40 / 10 | 0-12 | Shield planted for 2 s (guarded front outlined in gold): frontal hits clang off (no damage, no posture). Punish from behind; if it blocked anything it answers with a bash. |
| stomp | 1-2 | 18 / 3 / 12 | 0-6 | Right foot raised (3.5 ring), stamped: 12 around + a ring to jump (10, out to 9; P2 12). |
| dance | 2 | 12 / 36 / 14 | 0-9 | Blade held out, three whirling turns while it walks the target down: 11 per turn in r 4.8. |
| topple | 2 | 20 / 20 / 18 | 5-22 | Spectacle: crouch while a gold ring follows the target; leap, the ring locks where the target stood (max 18 blocks), lands sword-first a second later: 22 in r 4 + a ring (9). Long stuck recovery. |
| beams | 2 | 20 / 50 / 14 | 0-30 | Blade raised to the sky and driven into the floor; 3 volleys (0.8 s apart) of 32-block rune-light lines, one through every player plus one stray, warned 0.9 s by gold dots, then flaring (14). Step aside; too tall to jump. |

**Lair (the helm).** In by the broken wrist: forearm tunnel → elbow chamber → arm stair → balcony of the rib hall (30-block
vault opened by a breach) → grand stair to the gorget dais and its waystone (site of grace) → neck tunnel → mist → the
**helm** arena (radius ~14, ceiling ~16, tuff rings on the floor, soul and plain campfires round the wall, daylight
through the visor bars) → the vault under the arena floor behind sealed bars, an iron door out through the cheek.

Previews: `python3 tools/gen_models.py --preview --only bronze_sentinel` → `build/previews/models/bronze_sentinel.png`.

## 8. Champion of the Necropolis of Kings: The Dune King (Le Roi des dunes)
Files: `tools/wf/mobs/dune_king.py` (model), `src/main/java/com/brasshaven/entity/boss/DuneKing.java` (moveset). No
lair module: the arena is the existing L3 arena of the necropolis (`BOSS` in `tools/wf/structures/rock_necropolis.py`).
Reward: `remembrance_dune_king` → **Crook of the Dune King** (`dune_king_crook`, a staff, BEAM: a 16-block beam of
judgement that slows), plus gold, map fragments, emeralds, diamonds and lapis (`gen_data.py`). Quest:
`explorer/boss_dune_king`. (Not a flail: the Sand Pharaoh already drops the Pharaoh's Flail.)

**Concept.** An undead pharaoh-king, 4.6 blocks (5.2 with the crown): staggered strips of mummy wrappings with gilded
bands, a towering double crown (white bulb out of the red crown with its tall back, gold curl, uraeus), a broad usekh
collar of lapis, gold and turquoise beads, a striped false beard and lappets, a pleated kilt with a gold apron,
sunken turquoise eyes. Asymmetry: a vulture-wing gold pauldron on the right shoulder, the crook held upright like a
sceptre in the right hand, a beaded flail in the left, a loose bandage streaming off the left forearm. Four canopic
jars (human, jackal, baboon and falcon lids, turquoise glyphs that glow) orbit him at chest height and bob.

**Stats.** 460 health, armour 10, toughness 3, poise 85, knockback resistance 0.8, yellow bar, phase 2 at 50%: he
rises and floats 1.4 blocks over the floor (no gravity, drifts toward the target between moves; every ground effect
is drawn on the floor under him), +15% speed.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| flail | 1-2 | 14 / 22 / 12 | 0-6.5 | Flail raised behind the shoulder, three lashes 10 ticks apart (past invulnerability frames): 10, 10, then 14 wider with knockback. |
| hook | 1-2 | 16 / 4 / 14 | 4-11 | Crook drawn back (gold line on the ground): the first creature on the line takes 10 and is pulled 2.2 blocks in front of him, then he chains the flail. |
| sandstorm | 1-2 | 20 / 30 / 12 | 0-10 | Arms raised, cone outlined in falling sand; 1.5 s of storm in a 70° cone, 10 long: 3 damage, blindness and slowness II every 10 ticks. |
| summon | 1-2 | 20 / 4 / 16 | any | Crook and flail crossed over the crown (sand churns at 4 points 6 blocks out); husks rise there: 2 (P2 3), never more than 4 alive; they crumble when he dies. |
| jars | 1-2 | 14 / 24 / 12 | 3-24 | Crook pointed (ring under the target); every 6 ticks a jar spits a curse bolt at where the target is then (0.7 blocks/tick, stops on walls): 8 + Wither 3 s. |
| quicksand | 2 | 20 / 40 / 14 | 0-16 | Palms to the floor; 24 quicksand pools burst in three spiral arms spreading out to 14 blocks (12 + Slowness III 3 s), plus one under every player; each warned by falling sand and a ring. |
| scarabs | 2 | 16 / 30 / 12 | 0-14 | Flail cracked on the floor: two low rings of scarabs roll out to 16 blocks, 16 ticks apart (10 each, jump them). |
| judgement | 2 | 24 / 50 / 16 | 0-20 | Spectacle: crook levelled, a line of light marks the start on his left; a low 18-block beam sweeps 200° left to right over 2.5 s (16 + glowing, once per 10 ticks per target, grounded only): jump it as it passes or stand behind him. |

**Lair (the king's arena).** Through the slot canyon to the hidden plaza → portal between the seated kings → hypostyle
hall → L1 (embalming hall, gallery of niches) → L2 (flooded gallery, trap corridor, treasury) → L3 site of grace →
narrow corridor → mist → the **king's arena** (radius 16, 17-18 high, a dais with two seated colossi and jackal
statues) → south mist → reward vault behind sealed bars and the King's Well back up to the vestibule.

Previews: `python3 tools/gen_models.py --preview --only dune_king` → `build/previews/models/dune_king.png`.

## 9. Champion of the Chained Bastion: The Chained Jailer (Le Geôlier enchaîné)
Files: `tools/wf/mobs/chained_jailer.py` (model), `src/main/java/com/brasshaven/entity/boss/ChainedJailer.java`
(moveset). No lair module: the arena is the bastion's existing boss drum (`BOSS` in
`tools/wf/structures/chained_bastion.py`). Reward: `remembrance_chained_jailer` → **Jailer's Burning Chain**
(`jailer_chain`, EMBER 7 / -2.9, a new ability shape **HOOK** in `BossWeaponItem`: a chain thrown 14 blocks along the
look line, the first foe it meets takes 12, is dragged to your feet and set ablaze), plus gold, Ancient Embers,
emeralds, diamonds, chains and gilded blackstone (`gen_data.py`). Quest: `nether/boss_chained_jailer`.

**Concept.** The warden of the hanging prison, a hunched 5.4-block giant of blackstone and gilded iron with lava
cracks glowing through the plates: his head is a locked iron birdcage with a fire burning inside it, his heart a great
gilded padlock with a glowing keyhole, a chain bandolier across the cuirass, a red tabard with three gold bars. Strong
asymmetry: a gibbet post rises from his back and a small cage with a burning skull swings from it; the right fist drags
a long chain ending in a spiked, burning fetter-ball; the left arm ends in an oversized gauntlet with a broken shackle
cuff, its snapped chain dangling; a ring of gold keys at the left hip, broken shackles on both ankles.

**Stats.** 600 health (Nether range), armour 14, toughness 5, poise 100, knockback resistance 1.0, fire immune, red
bar. Three phases: phase 2 at 60% (the base roar, +12% speed); phase 3 at 30%, driven by the class itself (the base
class knows two phases): when he is free between moves he chains `unchain`, then every 12 s (scaled like cooldowns)
`verdict`. `unchain` and `verdict` have range 999 so the normal picker never chooses them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| lash | 1-3 | 18 / 4 / 14 | 0-8 | Chain drawn back to his right (flame arc), the ball swept over 220°: 16 + 3 s fire. P2: 35% chains into hook (P3: 50%, half of them into slam). |
| hook | 1-3 | 16 / 4 / 14 | 5-16 | Chain wound over the shoulder (ember line); the first creature on the line takes 9 + fire and is dragged to 2.6 blocks ahead, then he slams. |
| slam | 1-3 | 22 / 3 / 16 | 0-7 | Both fists overhead, crashed 3.5 ahead (20 + fire, r 3.2) + a fire ring to jump (9, out to 11). P2: a second (soul fire) ring 12 ticks later, 30% chains into lash. |
| shackles | 1-3 | 18 / 20 / 12 | 0-20 | Gauntlet raised, chain rattling; a shackle under every player within 22 blocks plus 2 (P2 4) strays: 0.8 s iron ring, then chains burst up: 8 and held fast 1.5 s (no walking, no jumping; P3 also burns). P2: if someone was caught and the target is 5-16 away, he follows with the hook. |
| kick | 1-3 | 12 / 3 / 10 | 0-3.5 | Foot drawn back, front kick in a 60° arc: 12, big knockback. Punishes hugging. |
| whirl | 2-3 | 14 / 40 / 14 | 0-9 | Chain paid out (flame ring), the ball spun round him for 2 s while he walks the target down: 9 + fire every 6 ticks in r 6.5. |
| pyre | 2-3 | 22 / 30 / 14 | 0-16 | Arms spread, eight ember lines drawn on the floor; fists into the floor: smoke-warned fire bursts run out to 14 blocks along the 4 straight bars, then the 4 diagonal ones (13 + fire, r 1.3). Stand between the bars. |
| unchain | 3 | 30 / 20 / 20 | (auto, at 30%) | Kneels and strains (invulnerable ~2.5 s), tears his chains apart: a fire nova to jump (12, out to 14) + 12 bursts at r 5 (12). Then +20% speed and a burning aura (3 + fire per second within 3 blocks). |
| verdict | 3 | 24 / 40 / 16 | (auto, every 12 s) | Spectacle: the chain whirled overhead and flung into the dark; three volleys a second apart: a shackle on every player (follows for a third of the 0.9 s warning, then locks) plus scaledCount(3) strays: 14, held fast 1.2 s and burnt. |

**Lair (the boss drum).** The landing on the west outcrop (waystone) → chain bridge to the pier → stair up the back of
the anchor chain to the gatehouse → L0 (prison of hanging cages, barracks and secret cell, forge, armoury) → L1
(gallery, chapel, site of grace) → covered bridge → mist → the **boss drum** (radius 14, 16 high, a blackstone ring
round a grate over the lava, chain curtains) → south mist and sealed bars → reward vault.

Previews: `python3 tools/gen_models.py --preview --only chained_jailer` → `build/previews/models/chained_jailer.png`;
held weapon: `python3 tools/art_sheet.py --kind held --only jailer_chain`.

## 10. Champion of the Shattered Halo: The Fallen Seraph (Le Séraphin déchu)
Files: `tools/wf/mobs/fallen_seraph.py` (model), `src/main/java/com/brasshaven/entity/boss/FallenSeraph.java` (moveset).
No lair module: the arena is the existing floating disc at the centre of the halo (radius 16, open to the void, a low
parapet broken in three places; `BOSS` in `tools/wf/structures/shattered_halo.py`, seal radius 15). Reward:
`remembrance_fallen_seraph` → **Glaive of the Broken Halo** (`halo_glaive`, VOID 8 / -2.9, new ability SHARDS: a fan of
five piercing halo-shard lines out to 16 blocks, 12 each, blinds; held model `halo_glaive` in `wf/held3d.py`), plus
void shards, emeralds, diamonds, end crystals, amethyst and a 25% enchanted golden apple (`gen_data.py`). Quest:
`end/boss_fallen_seraph`.

**Concept.** A fallen seraph, 5.4 blocks with the halo, hovering with no feet: a long white robe whose hem is eaten by
the void (dark purple with glowing cracks creeping up), a gold breastplate with a lens of light, a marble face under a
gold blindfold that weeps light, pale hair down her back. Behind her head a great broken halo: 14 gold segments with
two torn out at the upper right and one drifting loose. Asymmetry: the right wing whole, white and gold; the left
burnt to the void, short and ragged with a bare broken bone. A long glaive whose blade is a crescent of halo in the
right hand; the left arm bare marble cracked with light. Six halo shards orbit her waist: her projectiles.

**Stats.** 780 health (End tier), armour 14, toughness 6, poise 110, knockback resistance 1.0, purple bar. Phase 2 at
60% (roar; +12% speed), phase 3 at 25% (the invulnerable **shatter**, 2 s, then the disc cracks).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| glaive | 1-3 | 16 / 4 / 14 | 0-6.5 | Glaive drawn back over the right shoulder (arc outlined in light), one sweep over 210°: 17. P2: 40% chains into thrust. |
| thrust | 1-3 | 14 / 8 / 14 | 4-14 | Line of light marks her path; she glides 1.3 blocks a tick along it point first, 16 once per target. Stops 2.5 blocks short of the edge. P3: 35% chains into glaive. |
| shards | 1-3 | 18 / 24 / 12 | 3.5-26 | Orbit spins up (ring on the target), six shards flung every 4 ticks at the target's position then (0.9 b/t, stop on walls): 9 + glowing. P2: fans of two (±9°). |
| pillars | 1-3 | 20 / 22 / 12 | 0-24 | Hands to the sky: rings under every player + 3 strays (P2 5) with light falling into them, then columns of light: 14, small lift, no push. P2: a second volley on the players' new positions 0.7 s later. |
| blink | 1-3 | 12 / 2 / 6 | 0-30 | Wings fold; portal light rings the destination at the edge of the disc opposite the target (P3: inside the gold ring); she bursts out there facing the target, then 55% shards (P2: 40% beam, 35% shards). |
| beam | 2-3 | 24 / 40 / 16 | 0-22 | Spectacle: she rises, halo blazing; a start line on her left and dots on the safe circle (3.5 blocks) are drawn; a beam from the halo sweeps 160° left to right in 2 s, 3.5-20 blocks out, too tall to jump: 14 + blindness 1.5 s every 10 ticks. Stand under her or behind her. |
| nova | 2-3 | 20 / 36 / 14 | 0-16 | Halo raised (ring at her feet, the disc's edge lit in portal light): a ring of light rolls out (12, jump), 0.8 s later a second rolls back in from 15 blocks toward her (12, jump; pushes inward only). |
| shatter | 3 (once) | 40 / 4 / 16 | scheduled | Invulnerable; six fissures light up from the centre to the rim, she slams down: the disc cracks, a ring rolls out (8, jump). |
| rain | 3 | 22 / 44 / 14 | scheduled | Shattered sky: shards hurled at the sky, 4 volleys 11 ticks apart, each a ring under every player + 3 strays, light falling 0.8 s, then 13. |
| dive | 3 | 30 / 4 / 22 | scheduled | Seraph's fall: a gold ring follows the target for 0.8 s, locks (turns to soul fire) as she appears above it, falls 0.7 s later: 22 in r 3.5 + a ring (9, jump). Long recovery. |

**Phase 3 (the disc cracks).** Particle fissures stay on the floor (no block is broken). Every ~6 s (x cycle speed) two
opposite fissures glow for 1.2 s then flare: 10 + Slowness II 2 s, small lift. Beyond the gold ring (radius
min(12, seal radius - 3)) the disc crumbles: 3 every half second, outlined by purple dust, so the fight closes in.
`rain` and `dive` are never rolled: `bossTick` chains one every (150-210) x `cooldownScale()` ticks when she is idle.

**Fair over the void.** `FallenSeraph.strike` overrides the engine's: every hit (moves, waves, eruptions, the NG+
soul wave) loses the outward part of its knockback within 6 blocks of the rim, and lift is capped there. The phase-2
roar's shove is replaced in `onPhaseTwo` by a gentle one (none near the rim). Lances, rain, beam and fissures never
push. Her own glide stops short of the edge and she teleports back to the centre if she ever leaves the disc.
Co-op and NG+ come from the engine (players-under-rings scale naturally, fissure timer uses `cycleSpeed()`).

Previews: `python3 tools/gen_models.py --preview --only fallen_seraph` → `build/previews/models/fallen_seraph.png`;
held glaive: `python3 tools/art_sheet.py --kind held --only halo_glaive`.

## Difficulty: co-op scaling and NG+ cycles

Applied by `boss/WayfarerBoss` to **every** boss on its first server tick, whatever spawned it (boss seal,
altar, `/brasshaven boss`, spawn egg, a lair placement). Subclasses get it for free; nothing to do per boss.

**Co-op** (players = alive, non-creative, non-spectator players within the arena/leash radius, at least the
count the seal or altar passed to `scaleForPlayers`):

| per extra player | effect |
|---|---|
| health | x (1 + 0.75 per extra player), attribute modifier `brasshaven:coop_health` (multiplicative) |
| damage | +10% on every hit the boss deals (`BossDifficulty`, LivingHurtEvent: moves, waves, melee, projectiles) |
| poise | +25% (`effectiveMaxPoise()` wraps the subclass's `maxPoise()`) |
| cooldowns (2+ players) | -10% per extra player, never below 60% |
| minions | `summon()` adds +1 per 2 extra players; `scaledCount(base)` is public for custom spawns |

Every second the boss recounts the arena: if more players are fighting than it is scaled for, it scales up
once (keeping its health fraction). It never scales down mid-fight. The boss bar shows "· N players".

**NG+ cycles** (`boss/BossCycles`, SavedData in the overworld: `world/data/brasshaven_boss_cycles.dat`, keyed by
entity id, e.g. `brasshaven:iron_helmsman`). Each defeat of a boss type with a player involved adds one; the
cycle is `min(defeats, 7)` and is read when the boss spawns (and again when its fight starts, upward only, for
bosses that waited in their lair). At cycle c:

- health x (1 + 0.35c) (`brasshaven:ng_health`, multiplies with co-op), damage x (1 + 0.15c), armour +2c;
- faster: wind-ups and recoveries x max(0.75, 1 - 0.04c), cooldowns and idle pauses scaled the same way.
  A wind-up never drops below 10 ticks (or its authored length when that is shorter). Compressed wind-ups still
  run every authored wind-up step (`tick == N` checks keep firing), several per tick when needed;
- from cycle 2, phase 2 only, all bosses: an enraged soul shockwave every max(100, 220 - 15c) ticks
  (1 s ring telegraph, then a wave of radius 9 + c, 4 + c damage before multipliers: jump it), and staggers
  last max(34, 50 - 3c) ticks instead of 50;
- boss bar title "Name +c";
- loot: the boss loot table is rolled c extra times (Remembrances excluded, they stay unique), and from cycle 3
  an **Ember of Ascension** drops with chance 15% x (c - 2). On an anvil, boss weapon + Ember = +1 attack damage
  (modifier `brasshaven:ascension`, up to +5, cost 5 + 3 x level levels).

Admin: `/brasshaven boss cycle <boss>` reads the cycle and defeat count, `/brasshaven boss cycle <boss> <n>` sets it
(0..7). `/brasshaven boss <boss>` spawns at the world's current cycle.

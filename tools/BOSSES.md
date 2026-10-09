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
(moveset). No lair module: it stands guard on the rib hall floor of the toppled statue, under the breach, whose seal
wakes it (`SENTINEL` in `tools/wf/structures/fallen_colossus.py`, radius 11, no mist; the helm now belongs to the
Colossus's Heart, section 24). Reward: `remembrance_bronze_sentinel` → **Greatsword of the Sentinel**
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

**Lair (the rib hall).** In by the broken wrist: forearm tunnel → elbow chamber → arm stair → balcony of the rib hall (30-block
vault opened by a breach; the Sentinel's seal is on its floor under the breach) → grand stair to the gorget dais and its waystone (site of grace) → neck tunnel → mist → the
**helm** arena of the Colossus's Heart (section 24) → the vault under the arena floor behind sealed bars, an iron door
out through the cheek.

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

## 11. Champion of the Kneeling Gate: The Oathbound Gatekeeper (Le Gardien du Serment)
Files: `tools/wf/mobs/oathbound_gatekeeper.py` (model, texture variants `oath` and `broken`),
`src/main/java/com/brasshaven/entity/boss/OathboundGatekeeper.java` (moveset). No lair module: the arena is the gate's
existing hall under the town square (radius 17.5, a shallow tuff dome 14-17 high, soul lanterns on eight pilasters, the
well's grate in the middle; `BOSS` in `tools/wf/structures/kneeling_gate.py`, seal radius 15). Reward:
`remembrance_oathbound_gatekeeper` → **Key of the Kneeling Gate** (`gatekeeper_key`, LITHITE 8 / -3.2, new ability
**WARD** in `BossWeaponItem`: stone hands punch up in a ring round you, radius 5, 10 damage and a throw, and you get
Resistance II for 4 s; held model `gate_key` in `wf/held3d.py`), plus gold, map fragments, emeralds, diamonds, calcite and
a 25% bell (`gen_data.py`). Quest: `explorer/boss_oathbound_gatekeeper`. (A duo of twins was considered; the engine's
boss bar, seal and phases are single-entity, so it is one knight with a shield mechanic instead.)

**Concept.** One of the two 70-block statues above the pass come down to fight size, ~6 blocks with the crest: the
statues' own pale limestone plate (calcite on the top edges), grey stone mail, waxed copper trim, a red-granite cloak
to the calves and a red tabard with the gold key of the toll, an open helm with nasal, cheek plates and a copper crest,
a braided stone beard. The oath that binds him shows as soul-blue light in his eyes and in hairline cracks. Asymmetry:
a tower shield taller than a man on the left arm, carved with the gold key between two columns of glowing runes; a
stone greatsword point-down in the right hand; the gate's great gold key on an iron chain at the right hip.

**Stats.** 480 health, armour 14, toughness 5, poise 110, knockback resistance 1.0, blue bar. Phase 2 at 65% (roar, the
bell answers; +10% speed). Phase 3 at 30%, driven by the class (like the Chained Jailer): `kneel`, `broken` and `fury`
have range 999 and are only chained from `bossTick`.

**The oath guard (phases 1-2, until the shield breaks).** While he walks or idles and during `sweep`, `thrust`, `bash`,
`stomp`, `wheel` and `rush`, any hit whose source is in front of his body (dot >= 0.3, about 145°) clangs off the shield:
no damage, no posture, the attacker is nudged back. Flank him: his moves lock his facing from the impact on, so the
punish window is his side and back during recoveries. `keyfall`, `keyswing`, `overhead`, `toll`, staggers and the roar
leave the guard open. Reactions in `bossTick`: 3 blocked hits within 2 s → `bash`; the target staying behind him (within
6 blocks, 1 s x cycle speed) → `wheel` (own 4 s cooldown).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 16 / 4 / 14 | 0-7.5 | Blade drawn back to his right (arc in stone dust), swept over 200°: 16. P2: 35% chains thrust (target > 4) or stomp. |
| thrust | 1-3 | 14 / 8 / 14 | 4-14 | Dust line shows the lunge; he lunges ~7 blocks point first: 15 once per target. Guarded. |
| bash | 1-3 | 12 / 3 / 11 | 0-4.5 | Shield drawn in (spark arc), rammed out over 120°: 10, huge knockback, Slowness II 2 s. Also the answer to shield-beaters. |
| stomp | 1-3 | 18 / 3 / 13 | 0-6 | Foot raised (4-block ring): 13 all round + a ring to jump (9, out to 10; P2 a second ring 10 ticks later). Punishes back-huggers. |
| keyfall | 1-3 | 18 / 20 / 12 | 7-22 | Gold ring follows the target during the wind-up, locks on the throw; the key lands 0.9 s later: 14, Slowness IV 1.5 s; P2 six hands burst round it 0.5 s after (11). Guard open. |
| wheel | 1-3 | 14 / 4 / 14 | 0-5.5 | Ring of crits, one full turn: 14 in r 5.5. Rarely rolled (weight 4); mostly the anti-flank reaction. |
| keyswing | 2-3 | 18 / 4 / 14 | 3-11 | Key whirled on its chain; two gold rings mark the band 3.6-9.8: everyone in the band takes 12 + Slowness II. Hug him or leave. Guard open. |
| overhead | 2-3 | 22 / 4 / 18 | 0-9 | Sword over the helm (ring 3.5 ahead + soul dots on the line): 22 in r 2.8, then 7 hands burst one by one along the line out to 15 blocks (13). Guard open, long recovery: the frontal punish. |
| rush | 2-3 | 16 / 16 / 12 | 6-18 | Shield set (spark line), charge 1 block/tick for 13 ticks (stops on walls): 16 + big knockback once per target. Guarded. 40% chains overhead. |
| toll | 2-3 | 24 / 40 / 16 | 0-30 | Spectacle: sword raised (bell hum), struck on his own shield: the bell tolls and a wall of stone hands sweeps the whole hall from behind him to the far wall, a row every 2 ticks (each row warned 0.9 s by dust), 13 + throw, too tall to jump. One 3.6-block lane (within 10 blocks of his own line) stays open, edged by soul flames. 2.2 s later a second wall sweeps across at 90° with another lane. Guard open. |
| kneel | 3 | 20 / 200 / 24 | scheduled | At 30% (then every 30 s x cooldown scale while the shield holds): he kneels behind his planted shield like the statues. No damage reaches him; every player hit feeds the **Oath Shield** (white notched bar, 60 x (1 + 0.6 per extra player) x (1 + 0.25 x cycle)). The gate heals him 0.8%/s and tolls three sweeps of hands (forward, across, forward) whose open lane passes within 4 blocks of him. Shield broken → `broken`. Survived → he rises healed. |
| broken | 3 | 6 / 4 / 50 | on break | The shield shatters (variant `broken` hides it); he reels for 3 s taking +50% damage. From now on: no guard, +18% speed, soul flames off him. |
| fury | 3 (broken) | 14 / 30 / 16 | scheduled, < 7 | Every ~8.5 s: two-handed sweep (15), backhand 0.6 s later (15, arc re-telegraphed), overhead crash 0.6 s later (20 in r 3, ring of soul fire to jump, 9). After the break the toll also comes every 15 s. |

Co-op and NG+ come from the engine (health, damage, poise, cooldowns, compressed wind-ups, soul wave); the shield's
integrity, the kneel and toll timers scale with players / `cooldownScale()` as above. Resetting the fight (empty
arena) restores the shield and the guard.

Previews: `python3 tools/gen_models.py --preview --only oathbound_gatekeeper` →
`build/previews/models/oathbound_gatekeeper.png` (and `_broken.png`); held key:
`python3 tools/art_sheet.py --kind held --only gatekeeper_key`.

## 12. Champion of the Caldera Ringwall: The Castellan of the Caldera (Le Châtelain de la caldeira)
Files: `tools/wf/mobs/caldera_castellan.py` (model), `src/main/java/com/brasshaven/entity/boss/CalderaCastellan.java`
(moveset). No lair module: the arena is the ringwall's existing summit court on the needle (radius 16, open sky, a
crenellated parapet over the void; `BOSS` in `tools/wf/structures/caldera_ringwall.py`, seal radius 15). Reward:
`remembrance_caldera_castellan` → **Halberd of the Caldera** (`caldera_halberd`, LITHITE 8 / -3.1, a new ability shape
**RIFT** in `BossWeaponItem`: the halberd is driven into the ground and a molten rift runs 12 blocks along the ground
ahead (stops at walls and drops), forking in two 4-block branches at its end; every foe on it takes 11 once, is set
ablaze, slowed and lifted a little; held model `caldera_halberd` in `wf/held3d.py`), plus map fragments, emeralds,
diamonds, obsidian, magma blocks and blaze powder (`gen_data.py`). Quest: `explorer/boss_caldera_castellan`.

**Concept.** The lord of the ringwall, 5.7 blocks with his crown: a towering, upright knight in basalt plate trimmed
with tarnished bronze, split all over by cracks of cooling magma (white-hot core, dull red edges, black crust). His great
helm has a glowing T-slit and is crowned by a ring of jagged obsidian spikes round a small crater that glows from
inside. A long ash-red mantle with a smouldering hem, the ringwall's sigil (a ring with a needle) on his tabard.
Asymmetry: the right pauldron is a small volcano (stacked plates up to a glowing, smoking vent); the left shoulder is a
low plate under a drape of the mantle; a great halberd taller than he is (black haft, obsidian axe blade with a molten
edge, spear point, back spike) in the right hand; a heavy left gauntlet with molten knuckles, the fist that raises walls.

**Stats.** 520 health (a deliberately hard Overworld boss, colossal structure), armour 15, toughness 6, poise 105,
knockback resistance 1.0, fire immune, red bar. Three phases: phase 2 at 60% (base roar, +12% speed); phase 3 at 30%,
driven by the class like the Chained Jailer: when he is free between moves he chains `heat`, then every 10 s (x
`cooldownScale()`) `vents`. `reel`, `heat` and `vents` have range 999 so the picker never rolls them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 18 / 4 / 14 | 0-7.5 | Halberd hauled back over the right shoulder (ember arc), swept over 230°: 17 + 2 s fire. P2: 35% chains into chop (P3: 50%, half of them into reap). |
| chop | 1-3 | 20 / 3 / 15 | 0-8 | Raised in both hands (magma dots on the line), cleaved 7 blocks ahead (20, half-width 1.3) + a magma burst at the tip 8 ticks later (10, r 1.8). P2: 35% chains into charge if the target is > 6 away. |
| charge | 1-3 | 16 / 20 / 14 | 6-22 | Halberd levelled (smoke line 18 blocks), runs 0.95 b/t for 18 ticks: 15 + knockback once per target; stops at solid blocks. Into one of his own walls: the wall shatters (6 to whoever is near) and he chains **reel**. P2: 40% chains into sweep. |
| leap | 1-3 | 24 / 4 / 18 | 7-22 | Crouch, an ember ring follows the target (0.6 s, clamped to 13 blocks from the arena centre and 18 from him); it locks (flame) as he jumps on a fixed 12-tick arc (no gravity, `setPos`), lands at 1.2 s: 20 in r 3.5 + fire, then a lava crack spreads 1 block/tick for 14 blocks toward the target and flares 12 ticks behind its front (12 + fire). P2: three cracks (±28°), 30% chains into sweep. |
| stomp | 1-3 | 14 / 3 / 12 | 0-4.5 | Foot raised (smoke ring), stamped: 12 in r 4.5, big shove. P2: + a heat ring to jump (8, out to 9). |
| rampart | 2-3 | 20 / 6 / 16 | 4-20 | Gauntlet raised (obsidian dust marks the wall lines), driven into the floor: 3-high obsidian walls. Alternates a **corridor** (two 11-block walls 2.6 to each side of the target, along his line; 70% chains charge) and a **pen** (a 9-block wall behind the target + two 4-block side walls, open toward him; 60% chains leap). Anyone on a line: 8 + thrown aside, that column stays open. |
| reap | 2-3 | 16 / 16 / 14 | 0-8 | Forehand sweep at the impact (15), the arc re-drawn, backhand sweep 12 ticks later (15 + fire each). |
| reel | (charge into a wall) | 6 / 2 / 32 | — | Thrown back, sags over the haft; brittle (+30% damage) for 44 ticks. |
| heat | 3 (once, at 30%) | 30 / 20 / 20 | — | Kneels over the planted halberd, invulnerable ~2.6 s (growing smoke ring): a ring of heat to jump (12, out to 14) + 10 magma bursts at r 6 (12). Then +15% speed, smoke and flame round him. |
| vents | 3 (every 10 s) | 20 / 50 / 14 | — | Spectacle: halberd raised to the sky, point driven into the floor; the floor vents round the arena centre erupt in a pattern, each vent warned 1 s by smoke, magma dust and falling lava, then a column of fire (13 + fire, small lift). Patterns in turn: **rings** (r 2.5/7.5/12.5, then 5/10/14.5 1.2 s later), **spiral** (three arms unwinding outward), **checker** (4-block squares, the dark then the light ones 1.3 s later), **hunt** (4 volleys 0.6 s apart under every player + `scaledCount(2)` strays). Afterwards his armour is brittle for 3 s (+30% damage): the punish window. |

**The walls are temporary.** Every obsidian block he places is recorded with its expiry (200 ticks + up to 20, 240 in
phase 3, at most 150 blocks) and only placed into air over a sturdy floor within 15 blocks of the arena centre and not
within 2.5 blocks of himself. They are removed when they expire, when a charge breaks them, as soon as no player is
within 28 blocks of the arena (death, flight, the reset), when the fight resets to phase 1, in `onDefeated`, in
`remove()` for any destroying removal, and positions are saved (`CastellanWalls`) so that a chunk unload mid-fight
clears them on the next tick after reload. Removal only touches blocks that are still obsidian.

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (the vents timer uses `cooldownScale()`),
compressed wind-ups (the leap arc keys off wind-up tick numbers, so it still lands on time), and the hunt pattern's
strays use `scaledCount`. Players under rings and vents scale naturally.

Previews: `python3 tools/gen_models.py --preview --only caldera_castellan` → `build/previews/models/caldera_castellan.png`;
held halberd: `python3 tools/art_sheet.py --kind held --only caldera_halberd`.

## 13. Champion of the Glacier Hall: The Frost Jarl (Le Jarl de givre)
Files: `tools/wf/mobs/frost_jarl.py` (model), `src/main/java/com/brasshaven/entity/boss/FrostJarl.java` (moveset).
No lair module: the arena is the hall's existing domed room in the horn (radius 16, dome 12-20 high, eight ice pillars,
an oculus; `BOSS` in `tools/wf/structures/glacier_hall.py`, seal radius 15), reached by the Jarl's Stair and its site
of grace. Reward: `remembrance_frost_jarl` → **Bearded Axe of the Frost Jarl** (`jarl_axe`, LITHITE 8 / -3.1, new
ability shape **BREATH** in `BossWeaponItem`: a cone of frost 35° each side of the look line out to 9 blocks, 10 to
every foe in it, frozen solid 2 s (Slowness VII + full freeze ticks); held model `dane_axe` in `wf/held3d.py`, sprite
`dane_axe` in `wf/itemart_shapes.py`), plus gold, map fragments, emeralds, diamonds, blue ice and a 35% goat horn
(`gen_data.py`). Quest: `explorer/boss_frost_jarl`.

**Concept.** The dead king of the hall, a 5.7-block Norse giant frozen on his feet: frost-blue skin, white-blue eyes
under an iron helm with a nasal and a crown of ice spikes (the right horn whole, the left snapped), a hoarfrost beard
with a gold-ringed braid and icicles (his jaw drops for the breath), a white wolf pelt with its head on his left
shoulder, a navy cloak with a woven white wolf and a frozen hem, mail under an iron breastplate with a gold knot.
Asymmetry: a bearded Dane axe with a crescent of blue ice and a glowing edge in his right fist; a round quartered
white-and-blue shield with icicles on his left forearm; ice crystals grown out of his right shoulder blade.

**Stats.** 540 health (colossal overworld tier), armour 14, toughness 5, poise 110, knockback resistance 1.0, blue bar.
**Shield:** between moves (and during the bash wind-up) every frontal blow (55° each side, not `BYPASSES_SHIELD`)
loses 65%: hit him during recoveries or from the flanks. Three phases: phase 2 at 65% (roar, +10% speed, a small frost
wave); phase 3 at 30%, driven by the class (like the Jailer): when he is free he chains `winter`, then every 13 s
(scaled by `cooldownScale()`) `blizzard`. `huscarls`, `winter` and `blizzard` have range 999 so the picker never
chooses them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| cleave | 1-3 | 18 / 4 / 14 | 0-7.5 | Axe over the right shoulder (arc in snow), diagonal cut over 130°, 6.8 out: 18 + frost. P2: 35% chains into bash (close) or spikes. |
| bash | 1-3 | 12 / 6 / 12 | 0-5 | Shield raised square (guarded), then a 0.75 b/t shove: 12, knockback 2.6, Slowness III 1.5 s; a raised player shield goes on a 5 s cooldown. P2: 50% chains into cleave. |
| breath | 1-3 | 20 / 30 / 14 | 0-11 | Rears back (cone outlined), then the breath sweeps from his right to his left (±25°, P2 ±32°, P3 ±40°) for 1.5 s: 4 (P3 5) + 45 frozen ticks + Slowness II every 5 ticks to whoever is in the 20° beam, 11 out. |
| spikes | 1-3 | 22 / 24 / 14 | 3-20 | Axe raised (line marked), driven into the floor: spikes every 1.5 blocks out to 18 (P2: three lines at -22/0/22°), each warned (snow ring, white 6 ticks before): 14 + lift. Plus a spike that follows the target for 6 ticks then locks (P2: every player): 12. |
| leap | 1-3 | 20 / 10 / 16 | 7-22 | Crouch; a ring follows the target for 14 ticks then locks (turns blue); he springs on an arc 5 high and lands on the 10th active tick (anim 1.5 s): 20 in r 3.5 + frost wave (9, to r 10, jump). Destination clamped inside the arena. |
| huscarls | 1-3 | 16 / 4 / 16 | scheduled | First 15 s into the fight, then every 32 s × cooldownScale when there is room: rings mark the spots, then skeleton knights (frozen huscarls) rise. Alive at most `scaledCount(2)` (P3 `scaledCount(3)`), at most `scaledCount(2)` per call. Discarded when he dies. |
| rampage | 2-3 | 16 / 30 / 16 | 0-7.5 | Three blows: cleave (active tick 0, anim 0.8 s, 14), backhand (tick 10, 1.3 s, 14), overhead chop down a line (tick 22, 1.9 s, 20 + three spikes beyond). Turns up to 40° toward the target at ticks 3 and 13; each blow re-telegraphed. |
| rimeburst | 2-3 | 22 / 36 / 14 | 0-14 | Axe planted (five rings drawn at r 2.5/5.5/8.5/11.5/14.5): ring k bursts at 4 + 7k ticks, hitting within 1.1 of the ring: 13 + lift. Safe: the gaps (3.6-4.4, 6.6-7.4, 9.6-10.4, 12.6-13.4) and hugging. P3: the rings come back in (44 + 6k, 11). |
| winter | 3 (once) | 30 / 20 / 20 | scheduled | Kneels, invulnerable 2.5 s, axe driven into the floor: frost nova (12, jump) and the hall freezes, +15% speed. |
| blizzard | 3 | 24 / 40 / 16 | scheduled | Axe to the oculus; three volleys 18 ticks apart: a following spike under every player in the arena + `scaledCount(3)` strays: 14 + lift. |

**Phase 3 (Fimbulwinter).** Players who stay on the floor within 0.6 blocks over a quarter second gain 22 frozen ticks
(vanilla thaws 10 in that time): about 3 s standing still freezes you; fully frozen = 3 damage + Slowness III every
second. Every 7 s × `cooldownScale()` the floor whitens round every player for 1.2 s (snowball dust, a ring at each
player's feet, a cue sound), then pulses: 7 + 60 frozen ticks + Slowness II to everyone on the ground: jump it.
Reset: if the fight resets the hall thaws and the speed modifiers are removed.

Co-op and NG+ come from the engine: spikes and rings under every player scale naturally, huscarls use
`scaledCount`, the huscarl, pulse and blizzard timers use `cooldownScale()` (co-op and cycle speed).

Previews: `python3 tools/gen_models.py --preview --only frost_jarl` → `build/previews/models/frost_jarl.png`;
held axe: `python3 tools/art_sheet.py --kind held --only jarl_axe`.

## 14. Champion of Pilgrim's Ascent: The Storm Ascetic (L'Ascète des tempêtes)
Files: `tools/wf/mobs/storm_ascetic.py` (model; `build_illusion()` gives the `storm_illusion` copy),
`src/main/java/com/brasshaven/entity/boss/StormAscetic.java` (moveset), `StormIllusion.java` (the mirror images). No
lair module: the arena is the summit temple's round hall (radius 14.4, 17 high, two doors with mist, the great bell in
the belfry above; `BOSS` in `tools/wf/structures/pilgrims_ascent.py`, seal radius 13), reached by the stairway and the
site of grace at the covered gate. Reward: `remembrance_storm_ascetic` → **Staff of the Storm Ascetic**
(`ascetic_staff`, LITHITE 7 / -2.6, new ability shape **TEMPEST** in `BossWeaponItem`: a gust hurls every foe within 6
blocks away, then visual lightning falls on the three nearest, 10 each; held model `ascetic_staff` in `wf/held3d.py`,
sprite `staff_storm`), plus gold, map fragments, emeralds, diamonds, lightning rods, breeze rods and a 25% bell
(`gen_data.py`). Quest: `explorer/boss_storm_ascetic`.

**Concept.** The hermit of the summit, a gaunt, hunched old monk (4.7 blocks, 5.4 with the staff) who has meditated
under the great bell until the storm answers him: a long gnarled staff taller than himself crowned by an open bronze
ring with four jangling rings and a spike of lightning; a great round straw hat hung flat on his back; nine prayer beads
as big as fists orbiting his chest (his projectiles). Asymmetry: the right shoulder and arm bare, bony and scarred with
a glowing lightning-fern; the saffron robe thrown over the left shoulder only, its huge left sleeve streaming in the
wind; a long white beard and two prayer streamers blown sideways. The illusions are the same model, pale storm-blue and
slightly see-through (the tell).

**Stats.** 580 health (colossal overworld tier), armour 12, toughness 4, poise 100, knockback resistance 1.0, yellow
bar, no fall damage. Three phases: phase 2 at 65% (roar, +10% speed, a gentle shove); phase 3 at 30%, driven by the
class (like the Jailer): when he is free he chains `toll`, then every 15 s (scaled by `cooldownScale()`) `thunder`.
`mirror`, `toll` and `thunder` have range 9999 so the picker never chooses them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| staff | 1-3 | 14 / 14 / 14 | 0-7.5 | Staff back over the right shoulder (arc in cloud), sweep 130° out to 7: 15. Turns up to 40° (active tick 2), line marked, thrust at tick 10 down 9 blocks: 14. P2: 40% chains into vault (far) or spin. |
| vault | 1-3 | 20 / 10 / 16 | 7-22 | Staff planted: a ring follows the target 12 ticks then locks (sparks); arc 5.5 high, lands on active tick 9 (anim 1.45 s): 16 in r 3.2 + wind ring (8, to r 8, jump). Destination clamped 2.5 inside the hall. |
| gust | 1-3 | 18 / 24 / 12 | 0-11 | Palm out; cone (±40°, 12 long) and the **wind wall** ring (radius - 3) drawn. 1.2 s of wind: +0.13 b/t away from him (speed capped 0.6), 5 once. Past the ring - 1.5 the outward push and any outward speed are cancelled. P2: 50% chains into lightning. |
| lightning | 1-3 | 22 / 20 / 14 | 0-26 | Staff to the sky; rings follow every player 12 ticks then lock, + 3 strays (P2 5); visual bolts: 14 in r 1.8, small lift, no push. P2: a second volley on the players' new positions at active tick 14. |
| beads | 1-3 | 16 / 32 / 10 | 4-22 | Beads spin up (ring on the target); 8 (P2 9) flung every 2 ticks in a fan (8°/10° apart) toward the target, 0.8 b/t out to 14 (or a wall), then back to him at 0.9 b/t: 7 out, 7 back. |
| spin | 1-3 | 12 / 4 / 14 | 0-3.5 | Anti-hug: ring at 4.5, one turn of the staff: 13, knockback 0.9. |
| tempest | 2-3 | 16 / 30 / 16 | 0-7.5 | Sweep (tick 0, 14), turn 40°, backhand (tick 10, 13), turn 40°, line + three rings marked, slam (tick 22): 18 within 4, then bolts at 3/6/9 blocks: 12 each. |
| cyclone | 2-3 | 20 / 30 / 14 | 0-10 | Staff whirled overhead (ring at 12); 20 ticks of pull toward him (0.07 b/t, inward only), then a wind ring (12, to r 12, jump). |
| mirror | 2-3 | 20 / 4 / 10 | scheduled | 4.5 s after the roar, then every 26 s × cooldownScale when no illusion lives: three (co-op up to four) cloud rings 6 blocks round the target; he reappears on one, `storm_illusion`s on the others. Illusion: 1 HP, any blow pops it; staff combo (8 + 7) or a single marked bolt (9); fades after 16 s, if he dies, resets or leaves phase 2; never saved. |
| toll | 3 (once) | 40 / 6 / 18 | scheduled | Kneels, invulnerable 3.3 s, staff to the bell; strikes the floor: the bell answers, thunder ring from the hall's centre (8, jump), +12% speed. |
| thunder | 3 | 20 / 40 / 16 | scheduled | Staff raised (rings at his feet and at 14); the bell tolls three times (active 0, 13, 26): three thunder rings from him (11, to r 14, jump). |

**Phase 3 (the great bell).** Every 8 s × `cooldownScale()` the bell tolls on its own, whatever he is doing: 1.2 s of
sparks gathering at the hall's centre and a hum (`BELL_RESONATE`), then a thunder ring rolls from the centre to the walls
(9, jump it). Reset: speed modifiers removed, illusions dispelled.

**Fair on the summit.** `StormAscetic.strike` overrides the engine's (like the Fallen Seraph): every hit (moves, waves,
the NG+ soul wave) loses the outward part of its knockback within 5 blocks of the edge, the rest is halved and lift is
capped at 0.35. The roar's shove is replaced by a tamed one. Bolts and beads barely push; the cyclone only pulls
inward; the gust stops at the wind wall it draws first. His vault lands inside the hall and he teleports back to the
centre if he ever leaves it. Co-op and NG+ come from the engine (rings under every player scale naturally, the mirror
uses `scaledCount`, the bell, thunder and mirror timers use `cooldownScale()`).

Previews: `python3 tools/gen_models.py --preview --only storm_ascetic` → `build/previews/models/storm_ascetic.png`
(`--only storm_illusion` for the copy); held staff: `python3 tools/art_sheet.py --kind held --only ascetic_staff`.

## 15. Champion of the Tidal Abbey: The Abbess of the Tides (L'Abbesse des Marées)
Files: `tools/wf/mobs/tide_abbess.py` (model), `src/main/java/com/brasshaven/entity/boss/TideAbbess.java` (moveset).
No lair module: the arena is the abbey's existing rotunda under the church (radius 16, 11-block walls under a shallow
dome, eight pillars, glazed sea-light shafts, a prismarine compass on the floor; `BOSS` in
`tools/wf/structures/tidal_abbey.py`, seal radius 14). It replaces the reused Drowned Warden. Reward:
`remembrance_tide_abbess` → **Crozier of the Drowned Abbess** (`abbess_crozier`, LITHITE 7 / -2.9, new ability shape
**TIDE** in `BossWeaponItem`: a breaking wave rolls 12 blocks ahead in a 5-block band (stopped by walls), 10 to every
foe in it, swept along and slowed, and the wielder gets Dolphin's Grace for 6 s; held model `tide_crozier` in
`wf/held3d.py`, sprite `crozier` in `wf/itemart_shapes.py`), plus gold, map fragments, emeralds, diamonds, prismarine
crystals, nautilus shells and a 20% heart of the sea (`gen_data.py`). Quest: `explorer/boss_tide_abbess`.

**Concept.** The abbey's drowned saint, 5.4 blocks with her coral crown: a tall, stooped abbess who walked into the sea
at the last high tide. A seamless robe of sea-dark linen to the floor (she glides; the hem is torn into rags and trails
algae and barnacles), a faded crimson chasuble with a tarnished gold orphrey cross crusted with barnacles, a wimple and a
long grey-green veil, a drowned grey-green face with two glowing sea-glass eyes, red, orange and violet coral grown
through the veil. Asymmetry: a tall crozier of black driftwood banded in verdigris in her right hand, its crook a
nautilus spiral with a sea-glass lamp hanging in the curl; a bronze bell-censer swinging from her left hand on a long
chain (brine glows through its pierced lid); barnacles and a starfish on her right shoulder and breast; kelp from her
left hip and right sleeve.

**Stats.** 560 health (colossal overworld tier), armour 12, toughness 4, poise 105, knockback resistance 1.0, water
movement efficiency 1.0, breathes water, green bar. Three phases: phase 2 at 65% (roar, +10% speed, a small water
wave); phase 3 at 30%, driven by the class (like the Chained Jailer): when she is free she chains `flood`, then every
12 s (x `cooldownScale()`) `riptide`. `acolytes`, `flood` and `riptide` have range 999 so the picker never rolls them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 16 / 4 / 14 | 0-7 | Crozier drawn back over the right shoulder (arc in splashes), swept over 200°: 15. P2: 35% chains thurible (close) or surge. |
| censer | 1-3 | 18 / 6 / 14 | 0-6.5 | Censer swung back low, flung round over 140° (6 out): 12 + Slowness II 2 s; three brine clouds stay on the arc 5 s (7 s in the flood): 3 + Slowness every half second. P2: 30% chains surge if the target is far. |
| tidewave | 1-3 | 22 / 40 / 14 | 0-30 | Spectacle: crozier raised; the start line behind her and the edges of the gaps (3.6 wide, sea glass) are drawn across the whole arena. A wall of water 2.6 high rolls from behind her toward the target at 0.6 b/t (0.8 flooded): 13 + swept along, once per wave, too tall to jump. Two gaps (one in phase 3); the first is always within 9 blocks of the target across the wave. P2: a second wave at 90°, 34 ticks later with its own plan drawn. |
| toll | 1-3 | 20 / 20 / 14 | 0-18 | Censer raised over the crown (sea-glass rings close in): rung; for 14 ticks everyone within 20 blocks is drawn toward her (+0.11 b/t, capped 0.6), then the brine bursts at r 5 (14, thrown out). Run against the pull. P2: 50% chains sweep. |
| surge | 1-3 | 14 / 10 / 14 | 5-20 | Line of sea glass 10 blocks (15 flooded); she glides 1.0 b/t (1.5 flooded) ferrule first, 14 once per target, stops on walls. P2: 40% chains sweep. |
| acolytes | 1-3 | 18 / 4 / 14 | scheduled | First after 12 s, then every 30 s x cooldownScale when there is room: bubbling rings, then vanilla drowned rise (minion tag). Alive at most `scaledCount(2)` (`scaledCount(3)` in the flood), at most `scaledCount(2)` per call. Discarded when she dies. |
| baptism | 2-3 | 18 / 30 / 12 | 0-26 | Crozier overhead; a geyser on every player (follows for a third of its 1 s warning, then locks) plus `scaledCount(2)` strays: 14 + thrown up. Two volleys a second apart (three in the flood). |
| thurible | 2-3 | 16 / 16 / 14 | 0-6.5 | Forehand censer swing at the impact, a 35° turn toward the target, the arc re-drawn, backhand 12 ticks later: 12 + brine clouds each. |
| flood | 3 (once, again after a drain) | 30 / 20 / 20 | scheduled | Kneels, invulnerable ~2.6 s, rings the censer three times as rings of water spread; then the crozier strikes: the rotunda floods (see below), a ring of water rolls out (12, jump), +35% speed while the water stands. |
| riptide | 3 | 20 / 40 / 16 | scheduled | Spectacle: bows into the flood; three marks (every player up to three, then random spots, clamped in the arena) follow for 14 ticks, then lock, linked by sea-glass lines; she swims mark to mark in 13 ticks each (up to 1.6 b/t): 14 to whoever is within 2.2, once per leg. |

**The flood is real, temporary water.** `callFlood` places a water source on every open floor cell (air over a sturdy
block) within min(15, seal radius + 1) of the seal, one block deep: players wade (water drag, plus Slowness I every
second while they stand in it); she wades at full speed (`WATER_MOVEMENT_EFFICIENCY` 1, `getFluidJumpThreshold` 2.5 so
the float goal does not bob her, no water path malus) and +35% faster. Before filling, every water cell of the box
(radius + 6, floor -2 to +1) is recorded; the drain removes every `Blocks.WATER` block of that box that was not there
before (the placed sources, their flow and any source the water made by itself at the edges); flow further out dries
once nothing feeds it. The drain runs when no player is within radius + 14 of the arena (death, flight), when the
fight resets to phase 1, in `onDefeated`, in `remove()` for any destroying removal, and after a reload (the flag, box
and pre-existing water are saved as `AbbessFlood`/`AbbessPreWater`). If players come back to a drained phase-3 fight,
she calls the flood again.

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (acolyte and riptide timers use
`cooldownScale()`), compressed wind-ups, the soul wave. Geysers and riptide marks under every player scale naturally;
acolytes and baptism strays use `scaledCount`.

Previews: `python3 tools/gen_models.py --preview --only tide_abbess` → `build/previews/models/tide_abbess.png`;
held crozier: `python3 tools/art_sheet.py --kind held --only abbess_crozier`.

## 16. Champion of the Dam of the Drowned Valley: The Turbine Tyrant (Le Tyran des turbines)
Files: `tools/wf/mobs/turbine_tyrant.py` (model), `src/main/java/com/brasshaven/entity/boss/TurbineTyrant.java`
(moveset). No lair module: the arena is the dam's main turbine chamber (interior 37 x 39, x -18..18, z 12..50, air to
y 24, three generators in north-wall alcoves, the vault behind bars in the south wall, mists on both passages; `BOSS` in
`tools/wf/structures/drowned_dam.py`, seal radius 17), reached by the east tower's newel stair and Generator Hall II's
site of grace. It replaces the reused Grand Clockmaker. `tyrant_floor()` adds to the chamber eight 3 x 3 copper grates
on a ring 12 round the seal (his steam vents) and four 2 x 2 cast-iron columns on the diagonals, 13 high (cover from
the blast). Reward: `remembrance_turbine_tyrant` → **Valve-Wrench of the Turbine Tyrant** (`tyrant_wrench`, LITHITE
8 / -3.0, new ability shape **PRESSURE** in `BossWeaponItem`: a steam blast round the wielder, radius 8, that only
reaches foes in the wielder's line of sight (walls shield them), 12 within 3 blocks falling to half at the edge, hurled
away and set alight, and Speed II 3 s for the wielder; held model `valve_wrench` in `wf/held3d.py`, sprite
`valve_wrench` in `wf/itemart_shapes.py`), plus gold, map fragments, emeralds, diamonds, copper, redstone blocks,
pistons and a 15% heavy core (`gen_data.py`). Quest: `explorer/boss_turbine_tyrant`.

**Concept.** The dam's engineer, fused into the turbine he would not leave when the valley flooded: 5.7 blocks with his
smokestacks. His body is a round scroll-case of riveted gunmetal and brass on two hydraulic legs (piston rods, iron
boots), the turbine's intake glowing amber in his belly with the impeller turning inside; the engineer's soot-black
torso grows from its top (leather apron with brass buckles, an iron pauldron right, a brass one left), a flat cap, amber
goggles, a respirator with a hose into the case. Asymmetry: the right arm ends in a four-bladed turbine rotor that
always spins; the left fist holds a valve-wrench as long as a man, its jaw open on a brass worm screw; a copper outlet
pipe curls out of his left flank, a valve wheel and three gauges sit on the case's right shoulder, the left smokestack
is bent.

**Stats.** 600 health, armour 14, toughness 5, poise 115, knockback resistance 1.0, fire immune, yellow bar. Three
phases: phase 2 at 65% (roar, +10% speed, a steam ring); phase 3 at 30%, driven by the class (like the Jailer): when
he is free he chains `overload`, then every 11 s (x `cooldownScale()`) `dash`. `overload` and `dash` have range 999
so the picker never rolls them. **He places no block**: cracks, steam columns and spark trails are timed effects,
cleared with the rest when the fight resets.

**The vents.** On his first use he scans the floor (the layer under his home) within the arena for copper grates and
groups touching grates into vents, sorted round the chamber. Without grates (spawned by command or egg) he uses
eight virtual 3 x 3 vents on a ring 12 blocks round his spawn point. A vent hisses (white smoke on its grates, a ring of
hot dust for its last 8 ticks), then a steam column bursts up 3.5 blocks: 10 + thrown up, then 3 every 5 ticks while
you stay on it.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| rotor | 1-3 | 22 / 4 / 16 | 0-7.5 | Rotor drawn back right with a rising flute whine (arc in brass dust), swept over 240° out to 7: 16. P2: 35% chains wrench (close) or charge. |
| wrench | 1-3 | 20 / 4 / 16 | 0-12 | Wrench overhead (ring at 4 ahead and the crack line marked in hot dust), slammed: 18 in r 2.8; a crack runs on at 1 b/t to 20 out (stops at a wall or pillar): 12 + lift once; every vent it crosses blows at once (warn 6, column 16). P2: three cracks at -20/0/20°, 40% chains rotor. |
| vents | 1-3 | 18 / 30 / 14 | 0-30 | Cranks his shoulder valve: P1 every other vent (warn 24, column 30), P2 every vent but two opposite ones (marked in brass), column 40 once overloaded. |
| pressure | 1-3 | 46 / 10 / 20 | 0-30 | Spectacle: 2.3 s of build-up (ring of steam at the reach, flute rising, a bell cue 0.6 s before, stacks smoking harder), then a radial blast: 22 + knockback 2 + Slowness II 2 s to everyone within 16 (19 in P2) **whom he can see** (a ray from his chest to the head and to the body of each player, both blocked = safe) and to anyone within 3.5. Hide behind a column or a generator, or out-range him. |
| charge | 1-3 | 16 / 12 / 14 | 6-22 | Shoulders down (path marked 14 out), barrels at 1.15 b/t: 15 once, knockback 1.6; stops dead on a wall. |
| stomp | 1-3 | 12 / 4 / 14 | 0-4 | Anti-hug: ring at 4.5, the leg slams: 13, knockback 1.4. P2: 40% chains rotor. |
| grind | 2-3 | 18 / 30 / 16 | 0-7.5 | Rotor (active 0, anim 0.9 s, 14, ±110°), turn 40°, slam ring + line re-marked, wrench (tick 12, 1.5 s, 16 + a crack to 11), turn 40°, rotor back (tick 24, 2.1 s, 14). |
| vortex | 2-3 | 20 / 30 / 14 | 0-16 | Rotor raised like a fan, rings closing; 24 ticks of pull toward him (0.09 b/t, capped 0.55, inward only) within 14, then a whirl at tick 26 (2.3 s): 16 in r 4.8. |
| cascade | 2-3 | 18 / 30 / 14 | 0-30 | (vents animation) The vents blow one after another round the chamber, 5 ticks apart, from the one nearest the target (warn 16, column 14); overloaded, a second run goes the other way 1 s later. |
| overload | 3 (once) | 30 / 20 / 20 | scheduled | Kneels, invulnerable ~2.6 s, cranks his own heart: spark ring (12, jump), +20% speed. |
| dash | 3 | 20 / 45 / 16 | scheduled | Three marks (every player up to three, then random spots, clamped in the arena) follow 14 ticks then lock, linked by sparks; he runs mark to mark in 15 ticks each (up to 1.8 b/t): 14 within 2.2 once per leg, dropping spark patches every 2 ticks that burn 4 s (3 + 2 s of fire every half second). |

**Phase 3 (overload).** Every 9 s x `cooldownScale()` a third of the vents blow on their own (warn 30, column 30,
a bell cue), whatever he is doing. Reset: overloaded and the speed modifiers are cleared, effects are dropped by the
engine. Co-op and NG+ come from the engine (dash marks and the blast scale naturally with players; the dash and the
passive vent timers use `cooldownScale()`).

Previews: `python3 tools/gen_models.py --preview --only turbine_tyrant` → `build/previews/models/turbine_tyrant.png`;
held wrench: `python3 tools/art_sheet.py --kind held --only tyrant_wrench`.

## 17. Champion of the Great Aqueduct: The Lock-Master (Le Maître des écluses)
Files: `tools/wf/mobs/lock_master.py` (model), `src/main/java/com/brasshaven/entity/boss/LockMaster.java` (moveset).
No lair module: the arena is the aqueduct's existing great cistern under the castellum (`cistern()` in
`tools/wf/structures/great_aqueduct.py`: floor radius 17.5, a dome 17 high at the centre and 9 at the wall, a ring of
eight 2 x 2 columns at radius 12, a water gutter at radius 15-16 and a basin ring round the seal; seal radius 16, `BOSS`
in the same file). It replaces the reused Drowned Warden. Reward: `remembrance_lock_master` → **Pressure-Lance of the
Lock-Master** (`pressure_lance`, LITHITE 8 / -3.0, new ability shape **JET** in `BossWeaponItem`: a high-pressure jet
14 blocks along the aim, stopped by walls, 11 to every foe in it, each hurled to the far end of the jet; the recoil
pushes the wielder back half a block and puts out fire; held model `pressure_lance` in `wf/held3d.py`, sprite `lance`),
plus gold, map fragments, emeralds, diamonds, copper, pistons and a 15% heart of the sea (`gen_data.py`). Quest:
`explorer/boss_lock_master`.

**Concept.** A hulking hydraulic warden, 5.2 blocks: a riveted brass boiler of a body on short piston legs (hydraulic
rams down the thighs), the head sunk low between the shoulders, a round diving helm with one glowing porthole and a
spoked valve wheel bolted on top for a crown. Asymmetry: a whole sluice gate on the left arm (iron frame, wet oak
planks, straps, a valve wheel in its middle, rack teeth down its edge), a pressure-lance longer than he is tall in the
right (brass vamplate, a copper hose coiled down the shaft, a glowing nozzle for a point), a big valve wheel on the
right pauldron, two banded copper tanks on his back with glowing sight glasses. Verdigris everywhere.

**Stats.** 600 health (colossal overworld tier), armour 14, toughness 5, poise 120, knockback resistance 1, yellow bar,
preferred range 6. Three phases: phase 2 at 65% (roar, +10% speed, a small steam wave); phase 3 at 30%, driven by the
class (like the Chained Jailer / Abbess): when he is free he chains `flush`, then again every 22 s (x
`cooldownScale()`, counted from the start of the last flush). `reel` and `flush` have range 999 so the picker never
rolls them. Anyone who stays behind him within 6.5 blocks for 1.2 s gets a `spin` (at most every 8 s).

**The guard.** During the bash wind-up (`guarding`) every frontal hit (source within 78° of his facing, not
`BYPASSES_SHIELD`) under 11 damage is blocked (shield sound, sparks). A frontal hit of 11+ (a crit, an axe, a charged
bow) or any hit from behind (more than 107° off his facing, +25% damage) breaks the guard: he chains `reel` (2 s open,
+30% damage taken for 2 s). A surge that rams one of his own gates also ends in `reel`.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| thrust | 1-3 | 16 / 4 / 14 | 0-10 | Lance drawn back (line of water-light, foam for the last 6 ticks), driven ahead: line 9.5 x 2, 16. P2: 30% chains spin if close. |
| spin | 1-3 | 18 / 4 / 16 | 0-6 | Brass ring r 6.5, then a full turn at knee height: 13 all round. Also the answer to back-stabbers (above). |
| bash | 1-3 | 24 / 8 / 16 | 0-12 | Walks behind the raised gate (guarding, 0.07 b/t, line of brass 7), then rushes 6 ticks at 1.0 b/t (1.2 in P3): 14 once, knockback 1.7. P2: 50% chains thrust. |
| jets | 1-3 | 20 / 40 / 16 | 0-26 | Both sweep edges drawn (stopped where the jet will stop) plus the arc. A jet 18 long (22 in P3) from the nozzle sweeps 100° (P1 once over 2 s; P2+ there and back, 1 s each way); the body turns with it. 10 (11) once per pass, pushed back. `level.clip` per tick: columns and gates stop it. |
| sluice | 1-3 | 20 / 10 / 18 | 0-26 | Marks a 3-tile gate across the line from him on every player (up to 4) plus `scaledCount(1/2/3)` strays (P1/P2/P3), max 7; brass squares on the tiles, drips from the vault above. After the slam each gate drops 10 + 3i ticks later (warning >= 1.5 s): 18 + Slowness II to whoever stands under it (that column stays open), else iron bars 3 high stand 9 s (11 s in P3). |
| skewer | 2-3 | 14 / 24 / 14 | 0-10 | Three thrusts at active 0, 10, 20: 13 each, turning up to 30° toward the target between them. |
| surge | 2-3 | 16 / 14 / 16 | 6-22 | Line 16; rams at 1.15 b/t: 15 once (+Slowness in P3). Into a gate: the gate bursts and he reels. 40% chains thrust. |
| burst | 2-3 | 18 / 4 / 16 | 0-7 | Steam ring r 6, then 14 inside, then a wave to 12 (7, jump it). |
| flush | 3 (scheduled) | 30 / 136 / 20 | scheduled | Invulnerable 1.6 s, foam chevrons show the current's direction (one of 8). Then a current for 6.8 s pushes every player on the floor downstream (+0.07 b/t, capped 0.42) unless a block stands within 3 blocks upstream (columns, gates: the lee). Meanwhile four 34-tick charges: aim 12 ticks at a player (cycling through them, line 16), charge 18 ticks at 1.1 b/t (16 once, stops at walls, bursts gates), rest. First flush: +12% speed and a ring wave (12, jump). |
| reel | any (on guard break) | 6 / 4 / 30 | never rolled | Shield flung aside, open for 2 s. |

**Gates are real, temporary blocks** (`Blocks.IRON_BARS`, at most 150): only placed in air over a sturdy floor, inside
radius 15, never on a creature. Each is remembered with the tick it lifts; `clearGates` removes them when they expire,
when a charge bursts them, at once when no player is within radius + 14, in `onDefeated`, in `remove()` for any
destroying removal, and after a reload (saved as `LockGates`, removed on the first tick). Only blocks still iron bars
are removed.

**Co-op and NG+** come from the engine (health, damage, poise, cooldowns, compressed wind-ups, the soul wave); the gates
scale per player (one each) plus `scaledCount` strays, flush charges cycle through the players, the flush interval and
the back-spin delay use `cooldownScale()`.

Previews: `python3 tools/gen_models.py --preview --only lock_master` → `build/previews/models/lock_master.png`;
held lance: `python3 tools/art_sheet.py --kind held --only pressure_lance`.

## 18. Champion of the Mire Stilt-City: The Bog Hierophant (Le Hiérophante des tourbières)
Files: `tools/wf/mobs/bog_hierophant.py` (model), `src/main/java/com/brasshaven/entity/boss/BogHierophant.java`
(moveset). No lair module: the arena is the stilt-city's existing witch-queen's hall, 34 blocks over the swamp (a round
floor of radius 17.5 under a crooked cone, eight 2x2 posts at radius 12.5 as cover, the throne dais on one side, four
cauldrons on soul campfires, one door with mist; `BOSS` in `tools/wf/structures/mire_stilt_city.py`, seal radius 16),
reached by the High Walk, its site of grace and the grand stair. It replaces the reused Swamp Crone. Reward:
`remembrance_bog_hierophant` → **Lantern-Crozier of the Bog Hierophant** (`hierophant_crozier`, LITHITE 8 / -3.0, new
ability shape **MIRE** in `BossWeaponItem`: the bog opens where you look, up to 12 blocks (short of walls); every foe
within 4 blocks of it takes 9, is dragged toward its heart, held fast (Slowness VII 3 s) and poisoned (Poison II 5 s);
held model `lantern_crozier` in `wf/held3d.py`, sprite `crozier`), plus gold, map fragments, emeralds, diamonds, mud,
slime balls, lanterns and a 30% spore blossom (`gen_data.py`). Quest: `explorer/boss_bog_hierophant`.

**Concept.** The rotting bishop of the swamp, a "bishop on stilts", 5.9 blocks with his mitre: a hunched prelate who
stalks on two long, thin legs bound in mangrove roots like the piles of his own town (root toes splayed in the mud,
leeches on the shins), an open cope of living moss with a dripping hem over a rotted purple chasuble and a tarnished
orphrey gone to verdigris, a mossy hump pierced by vertebrae, a skull-like face of grey-green bog flesh with marsh-light
eyes, a slack jaw and a beard of hanging moss, a tall crooked mitre of mouldy linen with a toadstool on it. Asymmetry: a
tall crozier of twisted black mangrove wood in his right hand, its crook curling over a caged lantern of swamp-fire; a
bare bone-thin left arm with a hooked claw and a rosary of finger bones; a lily pad and brown toadstools on the left
shoulder; a cloud of marsh-flies circling his head (14 specks, four of them glowing).

**Stats.** 600 health (colossal overworld tier, the hardest so far), armour 12, toughness 4, poise 110, knockback
resistance 1.0, no fall damage, green bar. Three phases: phase 2 at 65% (roar, +10% speed, eight bog lanterns kindle round
the hall); phase 3 at 30%, driven by the class like the Chained Jailer: when he is free he chains `kindle`, then every
11 s (x `cooldownScale()`) `firelines`. `leeches`, `kindle` and `firelines` have range 999 so the picker never rolls them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 16 / 4 / 14 | 0-7.5 | Crozier drawn back over the right shoulder (arc in swamp-fire), swept over 200°, 7 out: 16. P2: 35% chains reap (close) or lure (far). |
| slam | 1-3 | 20 / 3 / 16 | 0-9 | Lifted in both hands (mud line 8 long, ring at the tip): 19 down the line (half-width 1.4); a 2.5-radius mud circle opens where the lantern lands. |
| lure | 1-3 | 18 / 10 / 14 | 3-22 | Lantern held out (a thread of swamp-fire to the target): the target is marked (P2: every player in the hall, up to 4). The mark's ring follows for 38 ticks, locks for 12, then blooms: 12 + Poison II 4 s in r 3, and lingers 2 s (2 + poison every half second). Get away from your friends. |
| mire | 1-3 | 20 / 30 / 14 | 0-22 | Crozier planted, claw drawn down: rings of mud dust follow the target (12 ticks) and every other player, plus strays (3 circles, P2 4, P3 5, r 3). At the impact the floor in each circle turns to real mud for 5 s: 8 on opening, Slowness III inside, after 1 s rooted (Slowness VII, motion stopped, 2 a second). P3: each circle bursts in flame when it closes (8 + fire). |
| stomp | 1-3 | 12 / 3 / 12 | 0-4.5 | A stilt raised (mud ring): 12 in r 4.5, shove, Slowness II 2 s. P2: + a mud ring to jump (8, out to 9). |
| stride | 1-3 | 14 / 10 / 12 | 6-18 | Leans in (mud line 10 long), strides 1 b/t for 10 ticks (stops on walls): 15 once per target. P2: 40% chains sweep. |
| leeches | 1-3 | 16 / 4 / 14 | scheduled | First after 13 s, then every 28 s x cooldownScale when there is room: mud rings, then vanilla silverfish drop off his robe (minion tag). Alive at most `scaledCount(2)` (P2 `scaledCount(3)`), at most `scaledCount(2)` per call. Discarded when he dies. |
| reap | 2-3 | 16 / 16 / 14 | 0-7.5 | Forehand sweep at the impact (15), a 35° turn, arc re-drawn, backhand 12 ticks later (15). |
| swarm | 2-3 | 18 / 40 / 14 | 0-16 | Arms spread, jaw open: the marsh-fly swarm hunts the target for 2 s at 0.23 b/t (0.27 kindled; a sprint outruns it): 3 every half second, Poison I 3 s and Hunger II once. With 3+ players a second, slower swarm takes another player. |
| wisp | 2-3 | 18 / 70 / 16 | 0-30 | Spectacle: he burns away into a marsh-light (hidden and untouchable) and flits to three of the eight lanterns (active 0, 15, 30; each flares and chimes). At 44 a ring of swamp-fire, the strike arc and a soul chime mark the spot 2.6 blocks behind the target (locked); at 52 he rises there facing the target; at 60 he strikes over 120°, 4.5 out: 17 + Poison I. Turn round and step aside. |
| kindle | 3 (once) | 30 / 20 / 20 | scheduled | Kneels, invulnerable ~2.6 s, lantern lifted while swamp gas bubbles over the floor; dashed down: a ring of fire (12, jump), +12% speed, flames round him. |
| firelines | 3 | 20 / 50 / 14 | scheduled | Spectacle: lantern swung round his head while the plan is drawn (small flames on the start line, swamp-fire on the gap edges); then burning gas rolls across the hall at 0.5 b/t, 3 high (too tall to jump): 12 + fire 4 s once per line outside the gaps (3.6 wide). Patterns in turn: **volley** (three parallel lines 16 ticks apart, the first gap on the target's side, each next gap shifted 5-8 blocks; a second gap in co-op), **cross** (two lines at 90°, 24 ticks apart, two gaps each, one within 7 blocks of the target), **ring** (a ring closes from the wall to the centre at 0.32 b/t with two radial lanes). Afterwards he is spent for 2.5 s (+25% damage): the punish window. |

**The blocks are temporary.** The mud circles replace only plain full floor blocks with air above them (no block
entities) within the arena, at most 400 at a time; every original block state is recorded with the tick it comes back
and only a block that is still mud is restored. The eight lanterns (vanilla lanterns on the wisp anchors at radius 10
between the posts, pulled in if blocked) are only placed into air over a sturdy floor. Everything is put back when it
expires (checked every tick, so a lost effect cannot leave mud behind), as soon as no player is within radius + 14 of
the arena (death, flight; the lanterns come back when players return in phase 2), when the fight resets to phase 1, in
`onDefeated`, in `remove()` for any destroying removal, and after a reload (mud positions and states and lantern
positions are saved as `HierophantMudPos`/`HierophantMudStates`/`HierophantLanterns` and restored on the first tick).
He never places fire: the fire lines, blooms and swarms are particles and hit checks.

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (leech and fire-line timers use
`cooldownScale()`), compressed wind-ups (the wisp's hops key off active ticks, unchanged), the soul wave. Lure marks and
mire circles land on every player; leeches use `scaledCount`; the second swarm and extra fire-line gaps appear in co-op.

Previews: `python3 tools/gen_models.py --preview --only bog_hierophant` → `build/previews/models/bog_hierophant.png`;
held crozier: `python3 tools/art_sheet.py --kind held --only hierophant_crozier`.

## 19. Champion of the Inverted Spire: The Abyssal Architect (L'Architecte de l'abîme)
Files: `tools/wf/mobs/abyssal_architect.py` (model), `src/main/java/com/brasshaven/entity/boss/AbyssalArchitect.java`
(moveset). No lair module: the arena is the spire's existing island in the underground lake (floor radius 17.5, a low
blackstone wall at 20, eight soul-fire pillars at 18.6, the spire's point 12 blocks over the centre with a soul lantern
at its tip, mist on the north and south causeways; `BOSS` in `tools/wf/structures/inverted_spire.py`, seal radius 15).
It replaces the reused Sculk Spawn. Reward: `remembrance_abyssal_architect` → **Plumb of the Abyssal Architect**
(`architect_plumb`, LITHITE 8 / -3.0, new ability shape **PLUMB** in `BossWeaponItem`: the plumb-bob falls from on
high onto the spot you aim at, up to 16 blocks, 12 to every foe within 2.5 and Slowness IV 2 s (pinned); held model
`architect_plumb` in `wf/held3d.py`, sprite `plumb` in `wf/itemart_shapes.py`), plus gold, map fragments, emeralds,
diamonds, iron chains, echo shards, soul lanterns and a 20% recovery compass (`gen_data.py`). Quest:
`explorer/boss_abyssal_architect`.

**Concept.** The builder-priest who raised the spire downward into the dark, 5.7 blocks (7 with his chains): a gaunt,
stooped marionette of a priest. Three iron chains rise from a harness on his back to broken hooks high over his
pinnacle mitre; a limestone mask with three soul-blue slits; a narrow slate cassock to the floor, its torn hem marked
like a mason's rule, a chalk sketch of the inverted spire on the skirt, a gold-stitched stole with square-and-compass
glyphs, a short hooded ash cape. Four arms: the long upper pair holds a **plumb-bob flail** (right: a long chain and a
great lead bob capped in brass with a glowing plumb line) and a **compass-blade** (left: giant dividers, one leg a steel
blade); the thin lower pair, growing from his ribs, holds a brass set-square and a soul lantern.

**Stats.** 600 health (colossal overworld tier), armour 12, toughness 4, poise 110, knockback resistance 1.0, blue bar,
no fall damage. Three phases: phase 2 at 65% (roar, +10% speed, a small shock ring); phase 3 at 30%, driven by the
class (like the Chained Jailer): when he is free he chains `unmoor`, then every 15 s (x `cooldownScale()`)
`chainswing`. `descend`, `unmoor` and `chainswing` have range 999 so the picker never rolls them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| descend | entrance | 30 / 30 / 16 | scheduled | When the fight starts (and again after a reset) he hangs from the chains under the spire's point (headroom - 6.6, up to 7 up; chains drawn to the tip), a soul ring under him; then lets go: landing 14 within 3.5 + shock ring (8, to r 9, jump). |
| compass | 1-3 | 12 / 4 / 12 | 0-5.5 | Arc chalked (±65°, 4.8): slash 13. P2: 40% chains flail (close) or plummet. |
| flail | 1-3 | 18 / 6 / 14 | 0-9 | Outer ring (8.5, soul) and safe inner ring (2.2, chalk) drawn while the bob whirls overhead: 15 + knockback to everyone between 2.2 and 8.5. Hug him. P2: 35% chains compass if you hugged. |
| plummet | 1-3 | 20 / 14 / 14 | 4-16 | Chalk line 11 long and a soul ring at its end, both turning with him: the bob crashes in the ring (17 + Slowness III 2 s), then at active tick 8 it is reeled back along the line (9 once, dragged toward him). |
| masonry | 1-3 | 22 / 34 / 14 | 0-30 | Dust trickles over the players; at the impact a chalk ring follows each player 10 ticks then locks (+ `scaledCount(3)` strays, 4 in P2), dust falling down a shrinking column: 15 within 2.2 after 26 ticks, and a pile of 1-2 rubble blocks for 8-9.5 s. P2: a second volley 1 s later. |
| swingdrop | 1-3 | 18 / 12 / 16 | 7-26 | Gap-closer: a ring follows the target 12 ticks, locks (chalk); he swings in a 4-block arc on a chain (drawn to the tip) and lands at active tick 9: 16 within 3 + shock ring (7, to r 7, jump). P2: 40% chains compass. |
| scribe | 2-3 | 16 / 20 / 14 | 0-9 | Outer ring 9 (soul) and split 4.5 (chalk): one turn round the planted compass, 14 between 4.5 and 9; the inner disc is marked, then at active tick 14: 14 within 4.5. Stand outside, or step in after the first cut. |
| eclipse | 2-3 | 20 / 48 / 14 | 0-20 | Darkness closes in a ring of ink; the lantern is snuffed: Blindness 3 s and Darkness to every player in the arena, he turns invisible. 30 ticks of stalking toward a point 2.5 behind the target: every 6 ticks an echoing footstep (sound) and a soul-blue footprint ring. Tick 30: the blade snicks open (sound, arc ±80° at 5 shown); tick 40: visible again, slash 16. |
| keystone | 2-3 | 20 / 60 / 14 | 0-30 | A checkerboard of 4-block squares (random offset) over the floor: one half marked with chalk and dust, falls at active tick 24 (14 to anyone in those squares), the other half marked then, falls at tick 48. |
| unmoor | 3 (once) | 30 / 10 / 20 | scheduled | Invulnerable 2.6 s, plumb raised, chains rattling, a closing chalk ring; the bob is driven into the floor: shock ring (12, to r 12, jump), +12% speed, the floor cycle starts. |
| chainswing | 3 | 24 / 100 / 18 | scheduled | Crouch, climb onto a circle under the chains (radius min(11, arena - 3), height headroom - 6.1, 3 to 6.5), chains drawn to the tip. Three 30-tick cycles: swing round (0.07 rad/tick) while a soul ring follows the target 14 ticks then locks (chalk), dive on it in 5 ticks: 16 within 3.2 + shock ring (7, to r 6, jump), rise back. He stays on the floor after the third slam (16 ticks + recovery 18: the punish window). |

**Phase 3: the island breaks up (real, temporary blocks).** A cycle runs while players are in the arena: 1.5 s after the
unmoor, then every 7 s x `cooldownScale()` after the floor reforms, a pattern is picked (rings 3 wide, eight spokes,
3x3 checkers, a four-armed spiral, or halves: the outer ring on one side and the inner ring on the other; random turn
and parity). For 2 s its floor columns are marked with chalk (soul dust and crumbs in the last 0.6 s, gravel cracking
sounds); then each column (the floor block and three below, within min(16, seal radius) of the centre, never within
2.5 of the seal or 3 of him, never a block entity, only where every cell and its neighbours are solid so the water
cannot spread) turns to water: the tiles crumble into the lake. Whoever is in that water is dragged at by the abyss
(3 and Slowness II every half second, pulled down). After 5 s the columns rise again.

**Every changed block is temporary.** Rubble and crumbled columns are recorded with their original block state and a
lifetime; they are restored when the lifetime runs out, at once when no player is within radius + 14 of the arena,
when the fight resets to phase 1, in `onDefeated`, in `remove()` for any destroying removal, and after a reload (the
map is saved as `ArchitectBlocks`, restored on the first tick). Restoring goes deepest first and lifts any creature
standing inside a restored block onto it.

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (the chain swing and floor timers use
`cooldownScale()`), compressed wind-ups, the soul wave. Marks under every player scale naturally; masonry strays use
`scaledCount`. Gravity and visibility always come back when the move that took them ends (stagger, reset, chain).

Previews: `python3 tools/gen_models.py --preview --only abyssal_architect` →
`build/previews/models/abyssal_architect.png`; held plumb: `python3 tools/art_sheet.py --kind held --only architect_plumb`.

## 20. Champion of the Leviathan Dreadnought Wreck: The Drowned Admiral (L'Amiral noyé)
Files: `tools/wf/mobs/drowned_admiral.py` (model), `src/main/java/com/brasshaven/entity/boss/DrownedAdmiral.java`
(moveset). No lair module: the arena is the wreck's existing boiler hall in the stern (hold deck, 40 x 31, 17 high, four
giant boilers at the corners with lit fireboxes facing the centre, side galleries, the funnel uptakes open to the sky,
brass rings on the floor at radius 10 and 17, mist across the stokehold passage; `BOSS` in
`tools/wf/structures/dreadnought_wreck.py`, seal radius 18), reached by the engine room and its site of grace. It
replaces the reused Iron Helmsman. Reward: `remembrance_drowned_admiral` → **Boarding Cutlass of the Drowned Admiral**
(`admiral_cutlass`, LITHITE 7 / -2.4, new ability shape **BROADSIDE** in `BossWeaponItem`: a deck-cannon shell fired
along the look line bursts on the first foe or wall up to 24 blocks, 13 within 1 block of the burst falling to half at
3.5, foes hurled away and set ablaze, the recoil kicks the wielder back; held model `admiral_cutlass` in
`wf/held3d.py`, sprite `cutlass` in `wf/itemart_shapes.py`), plus gold, map fragments, emeralds, diamonds, copper,
gunpowder, nautilus shells, a 35% spyglass and a 15% heart of the sea (`gen_data.py`). Quest:
`explorer/boss_drowned_admiral`.

**Concept.** The last commander of the Leviathan, 5.9 blocks with his hat: "a diving helmet under an admiral's
bicorne". A waterlogged navy greatcoat with crimson lapels and lining, tarnished gold buttons, epaulettes with dripping
bullion fringes and long split tails crusted with salt; sodden white breeches in lead-soled diving boots with brass toe
caps; instead of a head, a round copper-and-brass diving helmet on a riveted corselet, a glowing sea-green front port
and two side ports, an air hose to a copper tank on his back, and a sodden bicorne worn athwart on the dome. Asymmetry:
a broad boarding cutlass with a brass basket hilt in his right hand; his left forearm is a deck cannon (an iron breech
at the elbow, a banded barrel wrapped in chain, a brass muzzle with an ember glow in the bore), a four-pronged boarding
hook hanging under it. Barnacles on boots, shoulders, helmet and coat; kelp hanging from the hem, sleeves and hat.

**Stats.** 620 health (colossal overworld tier), armour 12, toughness 4, poise 115, knockback resistance 1.0, blue bar,
no fall damage, breathes water, wades (water movement efficiency 1, no water path malus). Three phases: phase 2 at 65%
(roar, +10% speed, a splash ring); phase 3 at 30%, driven by the class like the Chained Jailer: when he is free he
chains `scuttle`, then again 12 s (x `cooldownScale()`) after each flood drains. `scuttle` and `reel` have range 999
so the picker never rolls them.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| slash | 1-3 | 14 / 18 / 14 | 0-6.5 | Cutlass drawn back over the right shoulder (rust arc ±65°, 5.5): forehand 14, a 30° turn toward the target, arc re-drawn, backhand 14 at active 10. P2: 35% chains stamp (close) or hook. |
| thrust | 1-3 | 16 / 8 / 14 | 3.5-12 | Point drawn back at the hip (rust line 9 long), lunge 0.9 b/t (1.15 in the flood) for 8 ticks: 16 once per target. |
| cannon | 1-3 | 28 / 6 / 16 | 6-32 | Cannon arm raised: a red aim laser from the muzzle through the aim point to the wall; the aim point slides toward the target's chest at 0.33 b/t (a strafe outruns it) for 20 ticks, then locks (yellow, a click, a ring of r 3.5 where it will burst). The shell bursts on the first creature on the line (+4 direct) or the wall: 18 at the burst falling to 9 at 3.5, hurled away. |
| valves | 1-3 | 24 / 50 / 14 | 0-32 | Cutlass raised as a signal: 2 (P2 3, P3 4) of the boiler fireboxes (lit blast furnaces on the floor within the arena; four virtual valves round the centre if there are none) mark lanes 3 wide toward the players (rust edges following them until wind-up tick 14, then white and locked), up to the first wall (30 max). The chop bursts them: 13 (16 over the flood) and a shove down the lane, too tall to jump (3.5); the steam lingers 2.5 s: 4 and Slowness II every half second. |
| hook | 1-3 | 18 / 14 / 14 | 6-22 | Grapnel whirled under the cannon: a grey chain line to the target and a ring on it (locked at wind-up tick 12, yellow). Flung at 2 b/t up to 22 blocks (walls stop it): the first creature it touches takes 8, Slowness III 1.5 s, and is hauled to 2.5 blocks in front of him over 8 ticks. If someone was hooked: 40% (P2 70%) chains slash. |
| stamp | 1-3 | 12 / 3 / 12 | 0-4.5 | Lead boot raised (rust ring r 4): 12 in r 4, shove, Slowness II 2 s. P2: + a splash ring to jump (8, out to 9). |
| broadside | 2-3 | 24 / 44 / 16 | 8-32 | Three cannon shots (15 each) at active 0, 20, 40; before each the laser tracks for 11 ticks (he turns 12°/tick) and locks for 8. |
| boarding | 2-3 | 16 / 30 / 16 | 0-9 | Forehand 15 at the impact, backhand 15 at active 10, a yellow ring locks on the target at 12, he leaps at 16 (up to 8 blocks) and chops at 24: 18 in r 3 + a splash ring (8, out to 7, jump). |
| charge | 2-3 | 16 / 12 / 14 | 7-22 | Helmet lowered (brine line 14 long), charges 1.0 b/t (1.35 in the flood): 15 once per target. Ramming a boiler or a wall after active tick 2 chains `reel`. |
| reel | 2-3 | 10 / 20 / 10 | chained | Stagger animation, crits over his helmet; for 44 ticks he takes +30% damage. Bait the charge into a boiler. |
| scuttle | 3 (recurring) | 30 / 20 / 20 | scheduled | Kneels and drives the cutlass into the deck, invulnerable 52 ticks (bubbles and falling water over the hall, a closing brine ring, the hull groaning). The sea cocks open: the hall floods knee-deep for 18 s, a splash ring (12, out to 12, jump), +12% speed (once), 2-4 drowned marines board. |

**The flood (real, temporary water).** Every air cell over a sturdy floor at the floor level within 20 of the centre
(a 41 x 41 square cut to radius 24, so the whole rectangular hall) becomes a water source; water that already stood in
the box (the sea outside the hull) is recorded and never touched. While flooded the players wading get Slowness II every
second and he gets +25% speed (`drowned_admiral_wading`, removed when the water goes). The water drains (every water
block in the box at floor level -2..+1 that was not there before, flowing water included; box = radius + 8, enough for
the 7-block spread into the stokehold passage, which the mist stops) when the 18 s run out (a bubbling warning 3 s
before), at once when no player is within radius + 14, when the fight resets to phase 1, in `onDefeated`, in `remove()`
for any destroying removal, and on the first tick after a reload (`AdmiralFlood`/`AdmiralPreWater` saved). It is the
only block he places: the steam, the shells, the laser and the hook are particles and hit checks.

**Drowned marines.** Vanilla drowned in chainmail helmets (no burning under the funnel uptakes) with iron swords or
tridents (drop chance 0), minion-tagged; alive at most 2 solo, 3 with two players, 4 with three or more (each scuttle
tops them up). Discarded on defeat and when the fight resets.

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (the scuttle timer uses `cooldownScale()`),
compressed wind-ups, the soul wave. Steam lanes aim at different players, the marines scale with the player count.

Previews: `python3 tools/gen_models.py --preview --only drowned_admiral` → `build/previews/models/drowned_admiral.png`;
held cutlass: `python3 tools/art_sheet.py --kind held --only admiral_cutlass`.

## 21. Champion of the Sun-Engine Ziggurat: The Solar Hierarch (Le Hiérarque solaire)
Files: `tools/wf/mobs/solar_hierarch.py` (model), `src/main/java/com/brasshaven/entity/boss/SolarHierarch.java`
(moveset). No lair module: the arena is the ziggurat's existing sun chamber under the lens (`BOSS` in
`tools/wf/structures/sun_ziggurat.py`, seal radius 16), reached by the annex and the antechamber's site of grace. It
replaces the placeholder Sand Pharaoh. Reward: `remembrance_solar_hierarch` → **Sun-Staff of the Solar Hierarch**
(`hierarch_sunstaff`, LITHITE 8 / -3.0, new ability shape **PRISM** in `BossWeaponItem`: a sunray along the look line
that glances off block faces like light off a mirror, up to 3 bounces and 24 blocks in all, 10 to every foe it crosses
(once each), +25% per bounce, sets them ablaze; held model `solar_staff` in `wf/held3d.py`, sprite `sunstaff` in
`wf/itemart_shapes.py`), plus gold, map fragments, emeralds, diamonds, chiseled sandstone, glowstone, lapis and a 30%
spyglass (`gen_data.py`). Quest: `explorer/boss_solar_hierarch`.

**Concept.** The last priest of the noon, 5.8 blocks: "a gilded priest-automaton who keeps a dead empire's sun". A gold
mask with amber eyes under a gold-and-lapis striped nemes and a small crown; a pleated linen robe under a gold apron
stamped with a sun, a broad collar and lapis pauldrons; at his back a brass sun-disc halo of twelve rays (spinning in the
spectacle moves) with three little planets on an orbit ring. Asymmetry: a long sun-staff with a glowing amber orb in his
right hand, a polished round mirror-shield on his left forearm. 147 cubes, 256 x 256 texture.

**Stats.** 620 health, armour 12, toughness 4, poise 115, knockback resistance 1.0, yellow bar, no fall damage, fire
immune. Three phases: phase 2 at 65% (roar, +10% speed, ring); phase 3 at 30%, driven by the class like the Chained
Jailer: when he is free he chains `eclipse` once, then `sigils` every 11 s (x `cooldownScale()`). `bash`, `reel`,
`eclipse` and `sigils` have range 999 so the picker never rolls them.

**The mirror guard.** Between moves and during his staff moves (sweep, thrust, combo, bash, flare, descent) the mirror
blocks every frontal hit (within 60° of his facing): the hit is cancelled with a shield clang and fills a guard meter
(heavy hits of 12+ count x1.5). At `guardMax` (50, +25% per extra player) the mirror cracks: the hit lands and he
chains `reel` (2 s) and takes +30% damage for 2.5 s. Three blocks within 2 s while idle chain `bash`. The meter drains
after 3 s without blocks. Projectiles that hit the mirror are deflected back at their shooter (`deflection()`
override). Not guarded: spectacle moves (flash, sunlance, orrery, eclipse, sigils), staggers, reels.

**Gnomons (temporary blocks).** When a player comes within reach he raises six 2 x 2 sandstone gnomons, 4 high
(chiseled, cut, cut, chiseled), at radius clamp(0.6 x floor radius, 6, 9.5), one layer every 4 ticks; only into air
over a sturdy floor, never into a block entity or an entity. They are the room's cover: no light of his passes them
(sunlance rays, orrery arms and the flash all ray-clip against blocks). Every block he places is recorded with the state
it replaced and restored (top first) when no player is within radius + 14, when the fight resets to phase 1, in
`onDefeated`, in `remove()`, and on the first tick after a reload (`HierarchBlocks` saved). They rise again next fight.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 14 / 4 / 14 | 0-6 | Staff cocked over the shoulder (gold arc ±75°, 5.6), swept: 14. P2: 35% chains thrust (far) or combo (close). |
| thrust | 1-3 | 16 / 4 / 14 | 3-9 | Orb drawn to the hip (line 8.5), lunge 0.9: 16 + fire 3 s. P2: 40% chains sweep. |
| combo | 1-3 | 14 / 28 / 16 | 0-6 | Forehand 12, backhand 12 at active 10 after a 35° turn, staff raised and slammed down a line (6 x 1.4) at 22: 17. P2: the slam sends a fire ring (7, out to 6, jump). |
| bash | riposte | 10 / 4 / 12 | chained | Mirror shoved forward: 9 in ±60° r 3.8, knockback, Slowness. |
| reel | guard break | 6 / 4 / 30 | chained | Stagger pose; +30% damage taken for 50 ticks; the meter resets. |
| flash | 1-3 | 18 / 6 / 14 | 0-14 | Mirror raised to the lens (glows): a cone ±35°, 12.5 long, line of sight from the mirror: 8 + fire 2 s; Blindness 2.5 s to those looking at him. |
| sunlance | 1-3 | 30 / 120 / 20 | 0-40 | Blinks to the centre; a column of light falls down the shaft onto the mirror, the reflected ray's spot chases the target at 0.105 b/t (P2 0.13), clipped by blocks: 5 + fire every half second while in it. P2: a second ray hunts another player, or a delayed echo of the first when solo. |
| orrery | 1-3 | 24 / 90 / 20 | 0-40 | Blinks to the centre; planet arms sweep round him from the centre to the walls: P1 2 arms (low/high) at 4°/t; P2 3 arms at 5°/t, reversing at active 45 (blue chevrons from 35). Low arm (11): jump. High arm (14): only a gnomon shadow saves you. Once per arm per pass, with a tangential shove. |
| flare | 2-3 | 20 / 30 / 14 | 0-12 | Staff planted: three fire rings to jump (10, out to 11) at active 0, 12, 24. |
| descent | 2-3 | 18 / 12 / 16 | 6-24 | A ring follows the target for 12 ticks, locks; arc leap, lands at active 9: 18 in r 3 + a ring (8, out to 7). 40% chains sweep. |
| eclipse | 3 (once) | 30 / 20 / 20 | scheduled | Invulnerable 52 ticks; a burst ring (12, out to 12), +12% speed, Darkness on everyone in the arena (refreshed every 2 s), a wandering pillar of light (4 + fire, r 1.4) for the rest of the fight. |
| sigils | 3 (recurring) | 16 / 66 / 24 | scheduled | Six sun-sigils round the floor; he blinks to one at active 0, 22, 44 (the third is the one nearest the target), the next sigil flares from 6 ticks ahead; a corona 8 ticks after landing: 13 in r 4.5 + fire 3 s. |

**Co-op and NG+** come from the engine: health, damage, poise, cooldowns (the sigil timer uses `cooldownScale()`),
compressed wind-ups, the soul wave. The guard meter scales with the player count, the second sun-lance ray picks another
player.

Previews: `python3 tools/gen_models.py --preview --only solar_hierarch` → `build/previews/models/solar_hierarch.png`;
held staff: `python3 tools/art_sheet.py --kind held --only hierarch_sunstaff`.

## 22. Champion of the Canopy Temple-City: The Strangler Fig Queen (La Reine-figuier étrangleur)
Files: `tools/wf/mobs/strangler_queen.py` (model `strangler_queen`, and `build_spirit` → `jaguar_spirit`),
`src/main/java/com/brasshaven/entity/boss/StranglerQueen.java` (moveset), `JaguarSpirit.java` (her adds). No lair
module: the arena is the temple-city's existing summit terrace (floor y 66, a 1-block parapet, the dais on the north
side, braziers, fallen disc pieces, the broken brass sun-disc standing over the dais with its froglight eyes; `BOSS` in
`tools/wf/structures/canopy_city.py`, seal radius 18). She replaces the reused Jade Jaguar. Reward:
`remembrance_strangler_queen` → **Jade Macuahuitl of the Strangler Queen** (`queen_macuahuitl`, LITHITE 8 / -3.0, new
ability shape **CAGE** in `BossWeaponItem`: a root lash runs along your aim up to 14 blocks (stops on walls); the first
foe it meets takes 10, is caged where it stands (motion stopped, Slowness VII 3 s, Weakness II 5 s, a ring of root
particles) and the cage's thorns whip every other foe within 3 blocks of it for half damage, dragging them against the
bars; held model `queen_macuahuitl` in `wf/held3d.py`, sprite `macuahuitl`), plus gold, map fragments, emeralds,
diamonds, cocoa beans, vines, mangrove roots, jungle saplings and a 15% sniffer egg (`gen_data.py`). Quest:
`explorer/boss_strangler_queen`.

**Concept.** The strangler fig that smothered the temple and crowned itself in its place: a towering woman 5.8 blocks
tall, woven from aerial roots and inlaid with the temple's jade. Her skirt is a cascade of root strands that splay into
eight buttress roots on the floor; a jade belt with a gold sun buckle, a jade pectoral and bead collar over a mossy
bark chest, a jade mask with glowing gold eyes, a mane of pale hanging roots and a crown of bromeliad spikes and five
glowing orchids. Asymmetry: her left arm unravels into a five-segment thorned root whip with a barbed tip, longer than
she is; her right hand holds a jade macuahuitl edged with obsidian teeth. Her adds are translucent jade jaguar spirits
(`entityTranslucent`, pulsing glow).

**Stats.** 620 health, armour 12, toughness 4, poise 115, knockback resistance 1.0, no fall damage, green bar. Three
phases: phase 2 at 65% (roar, +10% speed, the canopy comes soon after); phase 3 at 30%, driven by the class like the
Chained Jailer: when she is free she chains `overgrowth` once, then every 12 s (x `cooldownScale()`) `cages`, and
`harvest` when a cage still holds someone. `canopy` is scheduled in phase 2 only (every 800 free ticks x
`cooldownScale()`), `plunge` always follows it. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| lash | 1-3 | 16 / 4 / 14 | 0-12 | Whip drawn back (a green line 11 long): 14 down the line (half-width 1.1) and a pull toward her. |
| combo | 1-3 | 14 / 24 / 14 | 0-6.5 | Macuahuitl cuts at 0.7 s and 1.2 s: 13 each over ±75°, 5.5 out. P2: a thrust at 1.7 s, 6.5 out: 16. |
| rootline | 1-3 | 20 / 20 / 14 | 0-20 | Hands into the floor: 3 root runs (P2 5) fan out toward the target at 1.2 b/t: 12 and a lift. Stand between the lines. |
| rootring | 1-3 | 22 / 30 / 14 | 0-14 | Arms raised: root bands burst at radius 4, 8 and 12, 12 ticks apart (11 each, jump them). P2: a return wave rolls back inward. |
| pollen | 1-3 | 18 / 10 / 14 | 0-22 | Crown shaken: pollen clouds (r 4.5, 8 s) on the target and around. Staying inside builds Slowness I → II → III and Mining Fatigue; after 4 s, Blindness + Nausea + 4. Leave the cloud and it fades. |
| swing | 1-3 | 16 / 12 / 14 | 7-22 | Whip thrown up into the canopy: she swings over 9 ticks to a safe landing next to the target: 15. |
| thorns | 1-3 | 12 / 3 / 12 | 0-4.5 | Anti-hug: thorns burst round her, 11 in r 4.5. P2: a wave to 8 (7). |
| whipstorm | 2-3 | 18 / 16 / 14 | 0-9 | The whip spins round her twice: 14 between 2.5 and 9 blocks at active 0 and 8. Hug her or back off. |
| snare | 2-3 | 18 / 16 / 14 | 3-12 | Whip cast down a 12-block line: the first player hit takes 8 and is reeled in, then a macuahuitl backhand arc (16). |
| canopy | 2 | 20 / 180 / 4 | scheduled | She climbs into the sun-disc (found at runtime from its froglight eyes, so a rotated jigsaw piece still works), invulnerable and weightless. Jaguar spirits drop at tick 10 (`scaledCount(2)`, at most `scaledCount(3)` alive); seed-bomb volleys on marked players at ticks 30, 80 and 130 (marked circle, then 13 in r 2.5). If every spirit dies after tick 50 she drops early and is **exposed** (+30% damage taken and slowed for 4 s). |
| plunge | 2 | 24 / 4 / 22 | chained | A ring follows the target for 14 ticks, then locks; she crashes onto it: 17 in r 3.5, then a root wave out to 10 (8, jump it). |
| overgrowth | 3 (once) | 30 / 20 / 20 | scheduled | Guarded about 2.6 s while roots swell; a growth wave (13), then +12% speed and root dust at her feet. |
| cages | 3 | 24 / 16 / 14 | scheduled | Up to 4 players are marked; each ring follows its player for 12 ticks, then locks. At the impact a cage of real mangrove roots snaps shut on each spot (8-cell ring 3 high plus a roof). A player caught inside takes 6, then 2 a second while strangled. Get out before it closes, or break the roots. |
| harvest | 3 | 20 / 4 / 22 | chained | 50 ticks after a cage closes on someone, she steps up to it and tears it open: 18 in r 2.5. |

**Spirits.** `jaguar_spirit` (22 health, 6 damage, speed 0.34, never saved, no loot, minion tag): it stalks the nearest
player, claws at ≤ 2.8 blocks (hit at tick 8) and pounces from 4-9 blocks (leaps at tick 10, 8 damage once during
ticks 10-20). It never pushes outward. It fades after 45 s, when the Queen dies or leaves, or when the fight resets to
phase 1, and ignores damage from bosses and minions.

**Fair edges.** The summit has a drop on every side, so her `strike` override caps push at 1.4. Beyond 9 blocks from
the centre the outward part of any push is removed and the rest halved, and lift is capped at 0.35. If a probe 2 blocks
along the push finds no floor, the push is zeroed. Lash, snare and the roots pull inward instead of outward.

**The blocks are temporary.** Cages place `minecraft:mangrove_roots` only into air, never inside an entity, at most
320 at a time, each with a 140-tick life. Every original state is recorded and put back:
- when the cage expires or is harvested;
- when no player is within radius + 14 of the arena;
- when the fight resets to phase 1;
- in `onDefeated` and in `remove()`;
- after a reload (positions are saved as `QueenCageBlocks` and restored on the first tick).

Pollen, seed-bombs and root lines are particles and hit checks only.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage, poise, cooldowns (the canopy
and cage timers use `cooldownScale()`) and compressed wind-ups that still play every authored tick. Spirits use
`scaledCount`. Cages and seed-bombs land on every player, up to 4.

Previews: `python3 tools/gen_models.py --preview --only strangler_queen` (and `--only jaguar_spirit`) →
`build/previews/models/strangler_queen.png`, `jaguar_spirit.png`; held macuahuitl:
`python3 tools/art_sheet.py --kind held --only queen_macuahuitl`.

## 23. Champion of the Necropolis of Kings: The Fourth King (Le Quatrième Roi)
Files: `tools/wf/mobs/fourth_king.py` (model `fourth_king`), `src/main/java/com/brasshaven/entity/boss/FourthKing.java`
(moveset, canopic jars, swarms, sealed tomb). No lair module: the arena is the necropolis' existing king's arena at the
bottom (floor y -37, radius 16, 17 high, columns at 15.6, jackals at 13.2, hung lanterns and ochre froglight stars in
the vault, an oculus shaft over the centre; `BOSS` in `tools/wf/structures/rock_necropolis.py`, seal radius 15). He
replaces the reused Dune King there (the Dune King stays in the Rust Mesa Mine-City), and the fourth king of the façade
(x 34) now has his face chiselled away. Reward: `remembrance_fourth_king` → **Scarab Sceptre of the Fourth King**
(`fourth_king_sceptre`, LITHITE 8 / -3.0, new ability shape **SCARAB** in `BossWeaponItem`: a scarab flies along your
aim up to 16 blocks (stops on walls) and bursts into a swarm on the first foe or wall; the swarm bites (9, Poison II
4 s, Hunger II 8 s) and leaps to the nearest unbitten foe within 5 blocks, up to 4 leaps, 20% weaker each leap; the
wielder heals 1 per foe bitten; held model `scarab_sceptre` in `wf/held3d.py`, sprite `scarab_sceptre`), plus gold, map
fragments, emeralds, diamonds, lapis, chiselled sandstone, decorated pots and an 8% enchanted golden apple
(`gen_data.py`). Quest: `explorer/boss_fourth_king`.

**Concept.** The fourth of the seated kings, the one whose face and name were chiselled off the façade, risen as a
gaunt mummified monarch 6 blocks tall: wrapped shins and ribs, a pleated kilt, a gold-and-lapis collar, a lapis-striped
cape, a cracked sandstone-and-lapis mask whose right half is hollowed out with one blue eye burning in the hole, and a
snapped white crown. Right hand: a three-chain flail; left: a scarab sceptre crowned with a glowing sun-disc.

**Stats.** 640 health, armour 12, toughness 4, poise 120, knockback resistance 1.0, no fall damage, blue bar. Phase 2
at 65% (roar, +10% speed, the jars rise again, wider beams, chained follow-ups); phase 3 at 30%, driven by the class
like the Chained Jailer: `seal` once, then the gaze and `verdict` every 15 s (x `cooldownScale()`). `drain` is
scheduled in every phase (every 21 s x `cooldownScale()` when jars stand and he is below 92%). Range 999 / weight 0
keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| flail | 1-3 | 14 / 26 / 14 | 0-6.5 | Lashes at 0.7 s and 1.2 s (12 each, ±70°, 5.5 out), then an overhead smash down a 7-block line (15). P2: 35% chains `smite` or `beam_high`. |
| smite | 1-3 | 20 / 4 / 18 | 0-7 | Sceptre brought down 3.5 ahead: 20 in r 3. P2: a wave to 10 (9). |
| beam_low | 1-3 | 22 / 40 / 16 | 0-16 | Ankle-high beam sweeping from his right to his left over 100° (P2 120°): 15 + Slowness II, grounded players only. Jump it. P2: 40% chains `beam_high`. |
| beam_high | 1-3 | 20 / 30 / 16 | 0-16 | Chest-high beam swinging back and forth over ±40° (P2 ±50°): 16. Nothing to duck under: sidestep out of the fan, or stand within 2.5 blocks. |
| sandfall | 1-3 | 18 / 6 / 14 | 0-24 | Marked circles on the target and `scaledCount(2)` strays (P2: every player and `scaledCount(4)` strays, +1 when sealed); sand pours 30 ticks later (P2 26): 14 in r 2.2 + Slowness II + Blindness. Buries any scarab swarm it lands on. |
| swarm | 1-3 | 16 / 4 / 14 | 0-22 | A scarab swarm rises (at most `scaledCount(1)`, P2 2) and follows one player for 12 s (0.19 b/t, P2 0.23): 3 + Poison + Hunger every 10 ticks within 1.4. |
| procession | 1-3 | 14 / 16 / 14 | 8-24 | He glides toward the target for 8 ticks (12 on contact), then smashes the flail down a line (16). |
| sandburst | 1-3 | 12 / 3 / 12 | 0-4.5 | Anti-hug: 11 in r 4.5. P2: a wave to 8 (7). |
| drain | 1-3 | 20 / 50 / 16 | scheduled | He kneels and draws streams from every standing jar; at the end he heals 3.5% (P2 4.5%) of max health per jar still standing. |
| seal | 3 (once) | 30 / 20 / 20 | scheduled | Guarded 62 ticks. The tomb seals: lanterns go out, froglight/glowstone stars turn blue terracotta, the oculus is stopped with chiselled sandstone, Darkness on every fighter (refreshed every 40 ticks), a wave to 13 (12), +12% speed. Three king spirits appear round the walls. |
| gaze | 3 | 20 warn + 70 sweep | between verdicts | One spirit at a time sweeps a cone (half-angle 11°) across the room: 6, line of sight required (a column or the king blocks it), 10-tick per-target cooldown. |
| verdict | 3 | 24 / 80 / 16 | scheduled | All three spirits' cones turn together (2.4°/tick), reaching from 3 out to the walls and back: 8 + Wither. Stand in the gap between two cones. |

**Canopic jars.** `minecraft:decorated_pot` blocks, 4 + 1 per extra player (at most 6), at radius 9.5 round the centre
(nearest free floor cell), raised at the fight start and again on phase 2. A broken jar is detected each tick and its
dropped pot item removed.

**The blocks are temporary.** Jars, extinguished lanterns, blue stars and the oculus plug are recorded with their
original state and put back (only if the block is still the one placed, top first):
- when no player is within radius + 14 of the arena;
- when the fight resets to phase 1;
- in `onDefeated` and in `remove()`;
- after a reload (positions are saved as `KingBlocks` and restored on the first tick).

Beams, sand, swarms and gazes are particles and hit checks only.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage, poise, cooldowns (the drain
and verdict timers use `cooldownScale()`) and compressed wind-ups that still play every authored tick. Strays, swarms
and jars scale with the party.

Previews: `python3 tools/gen_models.py --preview --only fourth_king` → `build/previews/models/fourth_king.png`; held
sceptre: `python3 tools/art_sheet.py --kind held --only fourth_king_sceptre`.

## 24. Champion of the Fallen Colossus: The Colossus's Heart (Le Cœur du Colosse)
Files: `tools/wf/mobs/colossus_heart.py` (model `colossus_heart`, texture variants `whole`, `burst`, `reforged`),
`src/main/java/com/brasshaven/entity/boss/ColossusHeart.java` (moveset). No lair module: the arena is the statue's helm
(`BOSS` in `tools/wf/structures/fallen_colossus.py`, seal radius 13). It replaces the Bronze Sentinel there; the
Sentinel keeps its fight in the same structure, now sealed under the breach on the rib hall floor
(`SENTINEL`, seal radius 11, no mist), so its quest and Bane of Legends stay reachable. Reward:
`remembrance_colossus_heart` → **Lodeblade of the Colossus's Heart** (`heart_lodeblade`, LITHITE 9 / -3.1, new ability
shape **MAGNET** in `BossWeaponItem`: the heart beats once; every foe the wielder can see within 9 blocks is dragged to
within 1.5 blocks of them, takes 8 plus 0.4 per point of its armour (at most +6) and Slowness II for 2 s, and loose
items and experience orbs in reach fly to the wielder; held model `heart_lodeblade` in `wf/held3d.py`, sprite
`greatsword`), plus gold, map fragments, emeralds, diamonds, copper blocks, iron, a lodestone and a 12% heavy core
(`gen_data.py`). Quest: `explorer/boss_colossus_heart`.

**Concept.** The colossus fell, but its brass engine-heart kept beating in the helm. It drags loose bronze plates and
rubble together into a knight six blocks tall, held by glowing amber tethers: an iron rib cage around the heart (wide
gaps so the beating brass shows), copper pipes, a pressure gauge and a valve wheel, a broad bronze greatsword with a
long reach in the right hand, a round shield-plate on the left forearm, and the empty helm floating a hand above the
shoulders, its visor slit glowing amber. Bronze with verdigris drips, amber only at the seams and the heart. Variant
`burst`: the armour is gone, the bare heart, rib cage and tethers remain, and two rings of plates orbit it. Variant
`reforged`: the armour back on, each plate cracked with a glowing amber seam (plus `Attributes.SCALE` +15%).

**Stats.** 640 health, armour 14, toughness 5, attack 15, poise 120, knockback resistance 1.0, no fall damage, yellow
bar. Three phases. Phase 2 at 65%: the **burst** (the roar animation; the plates fly off at roar tick 30 and the model
switches to `burst`): armour -8 (`colossus_heart_open`), +35% damage taken while open, four plates orbit the heart
(r 1.8-4.2, 6 per touch, 15-tick cooldown per player, not during `rings`). Phase 3 at 30%, driven by the class like the
Chained Jailer: `reforge` once (form `reforged`, open armour modifier removed, +15% scale, +10% speed), then `quake`
every 200 ticks x `cooldownScale()`. Range 999 / weight 0 keeps both out of the picker.

**Three forms on a two-phase picker.** Knight moves (`sweep`, `cleave`, `lunge`, `shieldthrow`) are only legal in
armour (phase 1 and 3), plate moves (`rings`, `platestorm`, `vent`) only while open (phase 2); `rubble` and `magnet`
work in every form. A move rolled in the wrong form hands over at its `start` step (`gate` → `redirect`) to a weighted
pick among the legal moves whose range and own cooldown fit, falling back to `platestorm` (open) or `rubble` (armour).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1, 3 | 18 / 3 / 14 | 0-8.5 | Greatsword drawn back over the right shoulder (arcs drawn in gold), swept over 210° out to 7.5 (x scale): 16. P3: 45% chains into cleave. |
| cleave | 1, 3 | 22 / 4 / 18 | 0-12 | Raised two-handed (ring 4 ahead, the crack's line in gold dots), driven in: 20 in r 2.8, then a crack runs on to 16 blocks (13, thrown up). P3: three cracks at ±22°. |
| lunge | 1, 3 | 16 / 10 / 16 | 5-15 | Blade at the hip (line drawn 12 ahead), a dash of 1.15 b/t for 8 ticks: 15 once per target. P3: 40% chains into sweep. |
| shieldthrow | 1, 3 | 18 / 40 / 12 | 4-20 | Shield-plate drawn across the body (its loop drawn in verdigris), flung: a falling-block plate (never placed) flies a loop out past the target on its right and back on its left: 12 per pass (10-tick cooldown per target). P3: two loops, the second mirrored. |
| rubble | 1-3 | 20 / 24 / 14 | 0-30 | Arms raised: a ring follows every player for 12 ticks (gold), then locks (red); chunks torn from the helm wall (dust at the source) are hurled one every 3 ticks on a 14-tick arc: 13 in r 2.5, lift. |
| magnet | 1-3 | 14 / 34 / 14 | 0-16 | Arms wide, an iron ring closing in: for 1.4 s every player within 16 (P3 18, x1.2 pull) and every dropped item is dragged in, +0.022 b/t per metal armour piece; the clang at active 30: 14 in r 4.5 (16 in r 5 while open), red ring for the last half second. |
| rings | 2 | 20 / 70 / 14 | 0-30 | The heart glides to the arena centre during the wind-up (first bands drawn red). Ticks 0-34: plates sweep bands 2-5.5 and 8.5-11.5; ticks 25-39 amber warning of the next bands; ticks 40-69: bands 0-2, 5.5-8.5 and 11.5-15.5. Each band has a turning 70° gap: 10 per pass, 12-tick cooldown. The first wave's safe bands are the floor's chiselled tuff rings (d 6-7, 12-13). |
| platestorm | 2 | 16 / 30 / 14 | 0-26 | Plates gather in a crown, then 6 shots every 5 ticks, each down a line drawn 8 ticks before toward a player, 1.6 b/t: 9 to the first creature on the line. |
| vent | 2 | 14 / 4 / 14 | 0-6 | Anti-hug: amber ring r 4, the heart bursts: 14 in r 4 (pushed), a steam wave to 9 (8, jump it), rust mites spill out (`scaledCount(2)`, at most `scaledCount(4)` alive). |
| reforge | 3 (once) | 30 / 20 / 20 | scheduled | Invulnerable 54 ticks; a spiral of plates closes on the heart; the armour slams back on: 12 in r 5 and a wave to 14 (12). |
| quake | 3 | 18 / 30 / 14 | scheduled | Sword point-down (ring ahead): 14 in r 2.5. Three marks per player (on them and two within 2-5 blocks, up to 4 players) plus `scaledCount(2)` strays; each warned 10 ticks (ring + dust), then a chunk falls from the ceiling: 14 in r 1.8 + Slowness, and leaves a heap of rubble. |

**Adds.** `rust_mite` from `vent` only (4 health, 2 damage, crumbles after 60 s, minion tag); the live ones are
discarded on death, reset or when the arena empties.

**The blocks are temporary.** Thrown shields, hurled rubble and falling debris are `FallingBlockEntity` visuals with
drops cancelled: they are discarded before landing and never placed. The only placed blocks are the quake's heaps:
`minecraft:tuff` / `minecraft:cobbled_deepslate`, 1-2 high, only into air on solid ground and never inside an entity,
at most 80 at a time, each with a 160-tick life. They are removed (only if still that block):
- when their time is up;
- when no player is within radius + 14 of the arena;
- when the fight resets to phase 1 (`resetForm` also restores the whole form, scale and armour);
- in `onDefeated` and in `remove()`;
- after a reload (positions are saved as `HeartRubble` and removed on the first tick).

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage, poise, cooldowns (the quake
timer uses `cooldownScale()`) and compressed wind-ups. Mites and stray debris use `scaledCount`; rubble, magnet,
platestorm and quake marks land on every player (up to 4 for the marks).

Previews: `python3 tools/gen_models.py --preview --only colossus_heart` → `build/previews/models/colossus_heart.png`,
`colossus_heart_burst.png`, `colossus_heart_reforged.png`; held lodeblade:
`python3 tools/art_sheet.py --kind held --only heart_lodeblade`.

## 25. Champion of the Forge of the Basalt Titan: The Anvil Warden (Le Gardien de l'enclume)
Files: `tools/wf/mobs/anvil_warden.py` (model `anvil_warden`), `src/main/java/com/brasshaven/entity/boss/AnvilWarden.java`
(moveset). No lair module: the arena is the forge's existing anvil face (`arena()` in `tools/wf/structures/titan_forge.py`,
`BOSS` there, seal radius 16): a 49 x 39 slab at feet 36, rimmed by a 1-high iron parapet, 34 blocks over the lava lake;
the titan's left hand and fingers lie on its north-west corner (2-9 blocks high), the root of the anvil's horn rises
1-2 blocks at the east edge (z -3..3) and runs on east as a narrow walkway, braziers stand in three corners, and the
titan's great hammer hangs with its face 30 blocks over the floor (centre 4 blocks west of the seal). It replaces the
reused Forge King. Reward: `remembrance_anvil_warden` → **Searing Tongs of the Anvil Warden** (`warden_tongs`, EMBER
8 / -3.0, fire-resistant, new ability shape **TONGS** in `BossWeaponItem`: the nearest foe in front of you, within 4.5
blocks and 50° of your aim, is seized and hurled up to 10 blocks along your aim (walls stop it); every other foe it
crashes through takes 75% (9), it slams down at the end for 12 and burns 5 s, and every foe within 2.5 blocks of the
impact takes half; bosses and creatures wider than 2 blocks are seared but not moved; no target = no cooldown; held model
`warden_tongs` in `wf/held3d.py`, sprite shape `tongs` in `wf/itemart_shapes.py`), plus gold, Ancient Embers, emeralds,
diamonds, iron and magma blocks, an anvil and a 30% netherite scrap (`gen_data.py`). Quest: `nether/boss_anvil_warden`.

**Concept.** The smith the titan's forge was built for: a hunched golem of columnar basalt 5.6 blocks tall whose every
joint glows with the forge's heat. For a head it wears a graphite crucible banded in brass, its spout jutting forward,
molten metal brimming at the lip and a glowing visor slit. Asymmetry: its heavier right arm (iron pauldron, brass
bracer) carries a forge hammer whose white-hot head nearly drags on the floor; its left arm holds long tongs out in
front of it with a glowing billet in their jaws. A scorched leather apron, a quench bucket on the left hip, three
basalt columns with molten tops jutting from the left shoulder-blade.

**Stats.** 640 health, armour 14, toughness 6, poise 130, knockback resistance 1.0, fire immune, no fall damage, red
bar. Three phases: phase 2 at 65% (roar, +8% speed, the titan's hammer 2 s after the roar); phase 3 at 30%, driven by
the class like the Chained Jailer: when free it chains `overheat` once, then `vent` every 300 ticks of fighting
(x `cooldownScale()`). `titan` is scheduled in every phase: first after 300 fighting ticks, then every 600 (phase 1),
460 (phase 2), 420 (phase 3) ticks x `cooldownScale()`; the scheduled timers count real fighting time and fire at the
next free moment, and never within 100 ticks of each other. Range 999 / weight 0 keeps them out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| slam | 1-3 | 18 / 6 / 16 | 0-8 | Hammer overhead (circle and crack line in embers): 16 in r 2.8 at 3.5 ahead, then a shockwave runs 14 along the anvil at 0.9 b/t (P3 1.15): 10 and a toss, half-width 1.2, dies where the face ends. P2: three lines at -28/0/+28. P2 end: 35% chains quench (close) or charge. |
| combo | 1-3 | 14 / 24 / 14 | 0-6.5 | Hammer forehand and backhand at 0.7 s and 1.2 s: 13 each over ±75°, 5.5 out, 2 s fire. P2: overhead at 1.7 s, 16 down a 6.5 line plus a short shockwave (9). P3 end: 50% chains charge if you are past 7. |
| grab | 1-3 | 16 / 20 / 14 | 0-6 | Tongs thrust (narrow line 5.5): the first player caught takes 8, is lifted and held 12 ticks, then flung (6) toward the anvil's centre to a floor spot at least 3 inside the edge (behind it if it stands in the middle). |
| splash | 1-3 | 20 / 10 / 14 | 3-24 | Crucible tipped: 3 marked tiles (target + two beside it; P2 every player up to 4 + 2 strays, P3 3 strays), following until 0.7 s. Globs fly 10 ticks: 12 in r 2.2, 3 s fire, a burning patch r 2 for 3 s (P3 5 s). |
| quench | 1-3 | 12 / 4 / 12 | 0-5 | Anti-hug: steam burst 11 in r 5, then 2 every 0.5 s for 2 s inside. P2: steam geysers (16-tick warning, 9 in r 1.8) under up to 3 players farther than 6. |
| charge | 1-3 | 16 / 16 / 16 | 7-24 | Path and end ring drawn; it runs to 1.5 short of you in 12 ticks (14 to anyone in the way), then an uppercut at 1.4 s: 12 over ±70°, 4.5 out. The end point is always a safe floor spot inside the face. |
| quake | 2-3 | 20 / 16 / 16 | 0-12 | Hammer slam (14 in r 3) and a ring wave to 12 (10, jump it); 12 ticks later the tongs-fist sends a second ring (P3 faster). |
| billet | 2-3 | 18 / 6 / 14 | 8-26 | A ring follows the target until tick 14, then locks; the billet flies 12 ticks and bursts: 13 in r 2.5, 4 s fire, a patch. P3: it bounces 5 blocks on along the throw (10 in r 2). |
| titan | 1-3 | 40 / 10 / 16 | scheduled | It beats its hammer on the tongs three times (ticks 8, 16, 24: clangs and a flash of the rim). The zone under the titan's hammer (found at runtime: the columns 26-34 above the floor within 14 of the seal that hold blocks, their mean and their area give the centre and radius, 5-9; about 7.7 here) is ringed in red with a shrinking inner ring, ash and falling lava from the hammer's face. Impact: 26 in the zone, 3 s fire; a shockwave rolls from the zone's rim to 17 (8, jump it). Away from the forge the zone (r 6) falls round the target. |
| overheat | 3 (once) | 30 / 20 / 20 | scheduled | Guarded 2.6 s while it drinks the crucible; a fire wave to 13 (12), +18% speed; from then on fire lasts 1 s longer, patches 5 s, a burning trail (r 1.3, 4 s, every 1.2 blocks it moves), red embers over the whole face. |
| vent | 3 | 40 / 6 / 24 | scheduled | Arms locked, crucible boiling over (2 s, the 14 reach ringed in red). A sheet of slag-steam rolls out at 0.8 above the floor: everyone within 14 whose line from it at that height is clear takes 20, 5 s fire and a push. Cover = any solid block on that line: the horn's root (stand on the horn walkway east of it), the titan's fingers and hand, a brazier. The streams are drawn stopping at blocks. |

Burning patches: 3 every 10 ticks to whoever stands in one (|dy| < 1.3) plus 2 s fire; at most 24 at a time.

**Fair edges.** The face drops 34 blocks into lava, so the `strike` override caps push at 1.3; beyond 12 blocks from the
centre the outward part of any push is removed and the rest halved, lift is capped at 0.3; if a probe 2.5 blocks along
the push finds no floor within 2.5 below, the push is cancelled. The grab throw, the charge end, the splash and billet
spots are clamped inside the face (reach 15) and checked for floor; shockwaves die where the floor ends.

**No blocks.** It places nothing: patches, trail, steam and the titan's blow are particles and hit checks. They are
cleared when the fight resets to phase 1, when no player is within radius + 14, on death and on removal.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage, poise, cooldowns (the titan and
vent timers use `cooldownScale()`) and compressed wind-ups. Splash tiles, geysers and the vent hit every player.

Previews: `python3 tools/gen_models.py --preview --only anvil_warden` → `build/previews/models/anvil_warden.png`; held
tongs: `python3 tools/art_sheet.py --kind held --only warden_tongs`.

## 26. Champion of the Starfall Library: The Star-Eater Curator (Le Conservateur dévoreur d'étoiles)
Files: `tools/wf/mobs/star_curator.py` (model), `src/main/java/com/brasshaven/entity/boss/StarCurator.java` (moveset,
with its tomes as a private `ShulkerBullet` subclass). No lair module: the arena is the library's existing crater chamber
under the island (`arena()` in `tools/wf/structures/starfall_library.py`: floor radius 17.4, glassy obsidian walls, a dome
13 high at the wall and 19 at the centre, the oculus shaft overhead, a meteorite fragment in the south-east wall, four
starlight braziers crowned with amethyst clusters at radius 14.9 on the diagonals; seal radius 16, mist on the grace
stair). `BOSS` there is `brasshaven:star_curator` (it replaces the borrowed Archivist). Reward:
`remembrance_star_curator` → **Astrolabe of the Star-Eater Curator** (`curator_astrolabe`, VOID 8 / -3.0, new ability
shape **ZENITH** in `BossWeaponItem`: gravity inverts at the aimed spot, up to 16 blocks short of walls; every foe
within 4 blocks of it takes 10, is drawn toward its heart and hurled up, Levitation III 1.5 s and Glowing 4 s; held model
`curator_astrolabe` in `wf/held3d.py`, sprite `astrolabe_staff` in `wf/itemart_shapes.py`), plus void shards, emeralds,
diamonds, amethyst shards, chiseled bookshelves, books, an end crystal, a 20% enchanted golden apple and a 15% recovery
compass (`gen_data.py`). Quest: `end/boss_star_curator`.

**Concept.** The keeper who catalogued the stars until one fell on his archive, 5.6 blocks: a very tall, narrow scholar
in a floor-length robe of indigo velvet (three flaring tiers, a torn hem, brass edging, a purpur front panel,
constellations stitched in glowing thread), a stiff brass-rimmed purpur mantle and a standing collar, an astrolabe
pectoral. His head is the meteorite: a charred, knobbly rock split open across the face on a starfield (nebula, two
bright stars for eyes, an ember rim), a chip of rock and four motes circling it. Five books orbit at chest height.
Asymmetry: the right hand holds the astrolabe staff (a dark shaft ringed in brass, an astrolabe disc inside two
turning armillary hoops round a white star); the left is raised palm-up with a page and a mote of light on it.

**Stats.** 780 health (End tier), armour 14, toughness 5, poise 125, knockback resistance 1.0, purple bar, no fall
damage. Three phases: phase 2 at 65% (roar, +10% speed); phase 3 at 30%, driven by the class (like the Chained
Jailer): when he is free he chains `invert` once, then every 10 s (x `cooldownScale()`) `blink`, which always chains
`starlance`; the gravity pulses run on their own timer. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| staff | 1-3 | 14 / 24 / 14 | 0-6.5 | Arc drawn (±70°, 5.5): sweeps at active 0 and 10 (13 each). P2: a thrust at active 20 down a 7-block line (16); 35% chains orbit (close) or lance. |
| volley | 1-3 | 18 / 10 / 14 | 5-28 | Books spin in: 3 tomes at the target (P2: 2 per player up to 4 players, + `scaledCount(1)` at the target), 7 (P2 6) and Slowness 1.5 s. Tomes are shulker bullets underneath: they drift after their target (weak homing) and **any hit or arrow shoots one down**; they crumble after 8 s and are never saved. P2: 30% chains lance at range. |
| well | 1-3 | 20 / 40 / 16 | 0-14 | Core ring (r 4) drawn, dust streaming in. For 30 ticks every player within 15 is drawn toward him (0.11-0.16 b/t every other tick: sprinting outward holds), the core flashing faster; at active 30 it implodes: 15 within 4. P2: a ring to 10 (8, jump). |
| starfall | 1-3 | 16 / 50 / 14 | 0-30 | A ring follows each player (up to 4) for 14 ticks, locks, a shard falls 16 ticks (a falling light): 14 within 2.5; `scaledCount(2)` strays. P2: a second volley at active 25. |
| orbit | 1-3 | 12 / 16 / 12 | 0-4.5 | Anti-hug: the books spin out, 11 within 5. P2: a page ring to 9 (7, jump). |
| lance | 1-3 | 16 / 10 / 16 | 6-20 | Gap-closer: the line drawn (to 3 past the target, at most 14, inside the arena); he streaks along it in 6 ticks: 15 within 1.6 of his path. P2: 40% chains staff. |
| pagestorm | 2-3 | 24 / 6 / 14 | 0-30 | Starts a storm effect (not while one runs) and goes on fighting: 1.5 s of warning, then 7 s. Safe circles (r 3, one per player, 2-4) wheel round the centre at radius min(9, reach - 4), 0.016 rad/tick. Outside them: Blindness (refreshed) and 2 a second. |
| constellation | 2-3 | 20 / 30 / 14 | 0-30 | Six stars (one near each player, up to 4, the rest at least 4 apart), joined nearest-first; the lines are drawn for 1 s, then burst one after another every 3 ticks: 13 and a toss within 1 of a line. |
| invert | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks: he rises, robe streaming up, dust rising off the floor; a ring of force (12, to 13, jump), +12% speed, the pulse and blink timers start. |
| blink | 3 | 14 / 4 / 6 | scheduled | A pillar of light over the next node (one with the target within 12 when possible, never his current one); he teleports there, then `starlance`. |
| starlance | 3 | 18 / 6 / 18 | chained | The line to the far wall (2 x reach + 1, at most 30) turns with the target for 10 ticks, then locks: a beam, 16 within 1.3 of the line, players within 4 blocks above the floor included (so floating players are hit). 18 ticks of recovery at the node: the punish window. |

**Crystal nodes.** Found at runtime (so a rotated piece still works): every amethyst cluster 1-3 blocks over the seal's
floor within radius + 3 that stands on a solid block (the brazier crowns; the dome's hanging clusters are too high), each
turned into a standing spot 2.5-4.5 blocks toward the centre (deduplicated within 3). With fewer than 3 (the demo spawn),
four virtual nodes on the diagonals at 0.75 x reach. In phase 3 motes of light rise over the nodes.

**Gravity pulses (phase 3).** Every 8 s (x `cooldownScale()`, at least 4.5 s, plus the warning): 1.5 s of warning (dust
rising off the whole floor; golden anchor rings, r 3.5, round every node except the one he stands at). Then every player
outside an anchor who stands on floor (within 1.5 of it) with 6 free blocks above takes 4 and gets Levitation II for 26
ticks (about 2 blocks up). While afloat, anyone further than reach - 3 from the centre is drawn inward. At tick 56 the
Levitation is removed and Slow Falling (3 s) given, so **every lift ends softly on the floor and never over a drop**. The
same release runs when the fight resets, when he dies and when he is removed.

**No blocks.** He places no blocks at all: tomes, shards, storms, constellations and pulses are particles, hit checks,
effects and short-lived projectiles. Push safety: his `strike` caps pushes at 1.3 and lift at 0.5, and near the wall (or
where a probe 2 blocks along the push finds no floor) the outward part is removed.

**Co-op and NG+** come from the engine: health, damage (tomes deal his damage through `strike`), poise, cooldowns (blink
and pulse timers use `cooldownScale()`), compressed wind-ups, the soul wave. Marks, circles and tomes scale with the
players; strays use `scaledCount`.

Previews: `python3 tools/gen_models.py --preview --only star_curator` → `build/previews/models/star_curator.png`; held
astrolabe: `python3 tools/art_sheet.py --kind held --only curator_astrolabe`.

## 27. Champion of the Rust Mesa Mine-City: The Mine Baron (Le Baron de la mine)
Files:
- `tools/wf/mobs/mine_baron.py`: model `mine_baron`, texture variants `bare`, `gilded`, `cracked`.
- `src/main/java/com/brasshaven/entity/boss/MineBaron.java`: the moveset.

There is no lair module. The arena is the existing cavern round the vein: `BOSS` in
`tools/wf/structures/mesa_minecity.py`, seal radius 20, floor radius about 21, dome about 21 high.

The Mine Baron replaces the Dune King there. The Dune King's quest and Bane of Legends stay reachable: his seal now sits in
the floor of the Necropolis of Kings' hypostyle hall (`DUNE_KING` in `rock_necropolis.py`, `hall()`, seal at (0, F0-1, -46),
radius 12, no mist, like the Sentinel). His `BOSS_HOME` is `rock_necropolis` again.

Reward: `remembrance_mine_baron` forges the **Drill-Pick of the Mine Baron** (`baron_drillpick`, LITHITE 8.5 / -3.0).
- It has a new ability shape, **FUSE**, in `BossWeaponItem`. A bundle of lit dynamite flies along the aim (up to 14
  blocks). It sticks to the first foe it meets, or lies where it lands. Its fuse burns 30 ticks; the pending charges are
  ticked by `item/BlastCharges.java`, a server-tick listener registered on first use. Then it blows, breaking no block:
  - power 12 near the heart, falling to half at 3.5 blocks;
  - set ablaze (flag `fire`) and hurled away;
  - the foe it stuck to takes x1.5.
- Held model `baron_drillpick` in `wf/held3d.py`, sprite `drillpick` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): gold ingots, raw gold, emeralds, diamonds, TNT, lanterns, rails and a 25% gold block.
Quest: `explorer/boss_mine_baron`.

**Concept.** A huge, greedy foreman, 5.6 blocks tall, strapped into a riveted steam exo-rig:
- a smoking boiler on his back, with brass pistons at the hips and knees;
- a pneumatic drill for a right arm and a pickaxe-hammer in his left fist;
- a miner's hard hat with a lantern;
- a waistcoat with a watch chain stretched over the belly.

Variant `gilded`: crusts of gold-veined ore lock over his shoulders, arms, chest and thighs, and four glowing gold geodes
sit on the boiler: the weak spots. Variant `cracked`: half the crust and two geodes remain.

**Stats.**
- 600 health, armour 12, toughness 4, attack 14, poise 130, speed 0.24, knockback resistance 1.0.
- No fall damage, yellow bar.

**Phase 2 at 65%, gold greed.** The roar (`greed` animation) locks the crust on 30 ticks later:
- Chunks = min(6, 3 + extra players).
- While armoured, he takes x0.2 damage. A player hit from behind (dot < -0.25 from the source position) of 3 or more,
  at least 8 ticks after the last chunk, knocks a chunk off and goes through in full.
- The form turns `cracked` at half the chunks. At 0 it turns `bare` and `orebreak` follows (dazed 60 ticks, +30% damage taken).
- Every 520 ticks x `cooldownScale()` without armour, he `regild`s. In its 30-tick wind-up, gold streams in; 60 x
  (1 + 0.25 per extra player) damage breaks it into `orebreak`, otherwise the crust is back.
- The first gilding calls `scaledCount(1) + 1` bandit marksmen (minion tag).

**Phase 3 at 30%, the blackout.** It is driven by the class like the Chained Jailer: `blackout` runs once (guard 74
ticks, bundles thrown at the walls), then `goDark`:
- every light block within radius + 4 (feet -2 to +26) is temporarily set to air; this covers every vanilla
  light-emitting block with no block entity, apart from fluids, `light` and fire;
- the crust is blasted off;
- +12% speed (`mine_baron_dark`).

From then on:
- A `light` block (level 14) follows his helmet lamp.
- The `glare` beam and the burning fuse carry their own moving light.
- Dynamite lights its landing spot (level 11).
- The vein sparks: every max(24, 50 x `cooldownScale()`) ticks, 1 + (players-1)/2 sparks land on exposed ore. Each warns
  12 ticks with a flicker of light, then deals 7 within 3.5.
- `cavein` comes every 260 ticks x `cooldownScale()`.

Scheduled moves (`exhaust`, `orebreak`, `regild`, `blackout`) use range 999 / weight 0 and are chained from `bossTick`.
`glare` only acts in the dark: before that, `gate` redirects it.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| drill | 1-3 | 16 / 14 / 16 | 0-7.5 | A red line 6.5 ahead, then two thrusts (active 0 and 11): 9 each down the line. |
| slam | 1-3 | 20 / 4 / 16 | 0-9 | Gold ring 3.5 ahead: 18 in r 2.6, then ore eruptions at 5.5 / 7.5 / 9.5 (11, staggered 4 ticks). P2: three lines at ±25°. |
| charge | 1-3 | 18 / 16 / 18 | 6-24 | Path drawn 14 ahead, a rush at 1 b/t: 13 once per target and a heavy shove. Jams on rock: three debris marks round him. |
| dynamite | 1-3 | 18 / 24 / 14 | 4-28 | Rings follow the marked players for 12 ticks (gold), then lock (red). Bundles (falling TNT visuals, never placed) fly 12 ticks, fizz 22 / 18 / 16 ticks (P1 / P2 / P3), then blow: 14 in r 3, hurled. |
| exhaust | 1-3 | 14 / 4 / 12 | scheduled | When someone loiters at his back for 26 ticks (40 while armoured), at most once per 100 ticks: 13 in a cone 6 deep behind him (±65°), 6 within 2.6. |
| cavein | 1-3 | 22 / 30 / 14 | 0-30 | Hits the wall: marks on every player plus strays (warned 14 ticks, dust from the ceiling), then a falling stone: 13 in r 1.8 + Slowness. |
| combo | 2-3 | 14 / 30 / 14 | 0-6.5 | Drill jab 10 (line 5), pick backhand 12 (±90°, 5.5), overhead slam 16 in r 2.4 + wave 8 to 7. |
| veinburst | 2-3 | 20 / 20 / 16 | 4-24 | Gold lines toward up to 3 players: ore eruptions every 1.2 blocks out to 18, 12 each. |
| fuseline | 2-3 | 16 / 40 / 14 | 6-26 | Keg lobbed onto a red ring r 5; a spark runs along the fuse (6 + fire to whoever it passes), then the keg blows: 20 in r 5 and 4 eruptions. |
| glare | 3 | 18 / 10 / 12 | 0-20 | Lamp cone ±35°, 18 deep, line of sight from the lamp: Blindness 60, Slowness, 4. Then he charges the first one blinded. |
| orebreak | 2 | 10 / 60 / 10 | scheduled | Last chunk off, or regild broken: on one knee, +30% damage taken. |
| regild | 2 | 30 / 10 / 10 | scheduled | See phase 2. |
| blackout | 3 (once) | 30 / 20 / 20 | scheduled | Guarded; blows the props; see phase 3. |

**The blocks are temporary.**
- The only placed blocks are `minecraft:light` blocks, and only into air.
- The lamps he puts out are recorded with their original state.
- Thrown bundles, kegs and stones are `FallingBlockEntity` visuals with drops cancelled, discarded before landing.
- Every change is restored, and only where the block is still the one he set:
  - when the fight resets to phase 1 (`resetForm`);
  - when no player is within radius + 14;
  - in `onDefeated` and `remove()`;
  - after a reload (saved as `BaronBlocks`, restored on the first tick).
- Bandits are discarded on death, reset or an empty arena.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`). Co-op scaling also adds chunks per extra player,
raises the regild break threshold, and scales bandits and sparks per player. Timers use `cooldownScale()`.

Previews:
- `python3 tools/gen_models.py --preview --only mine_baron` writes `build/previews/models/mine_baron.png`,
  `mine_baron_gilded.png` and `mine_baron_cracked.png`.
- Held drill-pick: `python3 tools/art_sheet.py --kind held --only baron_drillpick`.

## 28. Champion of the Echo Cathedral: The Hollow Cantor (Le Chantre creux)
Files:
- `tools/wf/mobs/hollow_cantor.py`: model `hollow_cantor` (no texture variants).
- `src/main/java/com/brasshaven/entity/boss/HollowCantor.java`: the moveset.

There is no lair module. The arena is the existing choir and apse: `BOSS` in `tools/wf/structures/echo_cathedral.py`
(`organ()`, seal at (0, 8, -60), radius 15, feet 9; the choir floor runs 8 blocks south to the screen and 18 east and
west, the organ plinth closes the north side at about 12). The Hollow Cantor replaces the borrowed Bell Keeper there;
the Bell Keeper keeps his own lair under the Mountain Monastery (`lair_bell_keeper.py`, `BOSS_HOME` unchanged).

Reward: `remembrance_hollow_cantor` forges the **Tuning-Fork Baton of the Hollow Cantor** (`cantor_baton`, LITHITE
8 / -2.8, depths tier: four lithite shards).
- It has a new ability shape, **SHRIEK**, in `BossWeaponItem`: a cone of sound ahead (35 degrees either side, up to 12
  blocks, line of sight from the eye): power 11, knockback, Weakness (flag `weak`). Where the cone's axis meets a wall
  its echo bursts: half the power to every foe within 3 blocks of that spot.
- Held model `cantor_baton` in `wf/held3d.py`, sprite `tuning_fork` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): lithite shards, emeralds, diamonds, amethyst shards, a bell, note blocks, echo shards and a 20%
disc fragment. Quest: `depths/boss_hollow_cantor` (its chapter follows the cathedral's).

**Concept.** A gaunt choirmaster, 3.5 blocks (hitbox 1.4 x 3.6), tarnished brass and deepslate:
- a ragged slate cassock that frays away above the floor (he glides), a brass yoke on bony shoulders, a crimson stole
  stitched with brass notes;
- the ribcage is an organ chest: deepslate ribs bound in brass round a dark cavity where seven small pipes glow with a
  pale echo-light;
- a deep pointed hood with nothing inside but darkness and a ring of light like a sound hole;
- five organ pipes fanning out above the hood (the silhouette);
- a long conductor's baton ending in a tuning fork with an amethyst resonator (right hand); the left hand conducts.

**Stats.**
- 640 health, armour 12, toughness 4, attack 13, poise 115, speed 0.26, knockback resistance 1.0.
- No fall damage, white bar. Phase 2 at 65% (roar, +8% speed); phase 3 at 30%, driven by the class like the Chained
  Jailer: `organ` runs once (guard 64 ticks), then every 240 ticks x `cooldownScale()` (at least 120) `requiem`, and
  the pipe blasts run on their own timer (every 130 ticks x `cooldownScale()`, at least 70).

Scheduled moves (`organ`, `requiem`) use range 999 / weight 0 and are chained from `bossTick`.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| baton | 1-3 | 14 / 18 / 14 | 0-6 | Arc drawn (±65°, 5): the downbeat at active 0 (13), a turn, the backswing at active 10 (11). P2: 35% chains toll (close) or shriek. |
| shriek | 1-3 | 22 / 12 / 14 | 3-16 | Turns slowly toward the target for 14 ticks (6°/tick), ripples running down the cone, red once it locks; then the cone (±30°, 14; P2 ±40°, 17): 14 (P2 16), knockback, Slowness 1.5 s. |
| toll | 1-3 | 18 / 20 / 14 | 0-9 | Ring r 3.5 drawn; 15 inside and a wave to 10 (8, jump). P2: a second wave at active 10 (to 12). |
| cadence | 1-3 | 16 / 12 / 14 | 6-20 | Gap-closer: the line drawn (to 3 past the target, at most 12, inside the arena, only onto floor); he glides along it in 6 ticks: 12 within 1.6 of his path. P2: 40% chains baton. |
| resonance | 1-3 | 24 / 34 / 16 | 0-30 | At its start 3 + (players-1) buds (max 6, 4.5 apart, one 3-5 blocks from each player) grow on the floor, each in a golden ring (r 2.2). 2 s of warning in all (the floor shivers outside the rings, red for the last 6 ticks); at active 16 everyone on the floor outside a ring takes 14 + Slowness II 2 s (airborne players are missed); the buds shatter at active 18. |
| silence | 2-3 | 20 / 6 / 12 | 0-14 | Ring r 8 drawn, ash drifting in. A zone of hush for 7 s (8 s in phase 3) where he stood: players inside get Slowness I, Darkness and their sounds stopped (`ClientboundStopSoundPacket` every second); inside it he is invisible (his glow layer still shows) and sheds a shimmer of ash; a player's hit reveals him for 20 ticks. |
| choir | 2-3 | 22 / 8 / 14 | 0-30 | Soul light rises over the spots (on floor, 4+ from him); bell monks and banshees in turn, `scaledCount(2)`, never more than 2 + players alive (minion tag). |
| fugue | 2-3 | 20 / 40 / 14 | 0-30 | Three voices at active 0, 12, 24: a ring follows each player (up to 4) for 10 ticks, locks red for 10, bursts: 12 in r 2.2; `scaledCount(1)` strays each. |
| organ | 3 (once) | 40 / 20 / 20 | scheduled | Guarded; he rises, the floor hums; a wave to 14 (12, jump), Darkness 2.5 s to every player, +12% speed (`hollow_cantor_organ`), the timers start. |
| requiem | 3 | 20 / 50 / 16 | scheduled | Faces the target; six rows across his facing, 2.5 apart from 2 blocks out, points 1.4 apart (only on floor inside the arena), each row with a 3-point gap that wanders; rows drawn grey in the wind-up, each turns red 14 ticks before it blasts at active 8 + 6k: 13 within 1 of a point, once per row. |

**Pipe blasts (phase 3).** Under each player (up to 4) plus `scaledCount(1)` strays: a ring r 1.6 with rising dust for
24 ticks (red for the last 8), then a column of sound 7 high: 12 within 1.6 and a toss (lift capped at 0.5).

**The blocks are temporary.**
- The only placed blocks are the resonance's `large_amethyst_bud`s, only into air over a solid block (they drop
  nothing without Silk Touch). Spots without room stay virtual (rings and particles only).
- Each is recorded with its original state and put back only where the bud is still there: when the move ends, when it
  is cut short (stagger), when the fight resets, when no player is within radius + 14, in `onDefeated` and `remove()`,
  and after a reload (saved as `CantorBlocks`, restored on the first tick).
- Choristers are discarded on death, reset or an empty arena; the silence ends with them.

**Push safety.** His `strike` caps pushes at 1.2 and lifts at 0.5, and within 3 blocks of the arena's edge the outward
part is removed.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage, poise, cooldowns (the requiem
and pipe-blast timers use `cooldownScale()`), compressed wind-ups. Co-op also adds buds, choristers, fugue strays and
blast strays per player.

Previews:
- `python3 tools/gen_models.py --preview --only hollow_cantor` writes `build/previews/models/hollow_cantor.png`.
- Held baton: `python3 tools/art_sheet.py --kind held --only cantor_baton`.

## 29. Champion of the Airship Graveyard: The Corsair Captain (La Capitaine corsaire)
Files:
- `tools/wf/mobs/corsair_captain.py`: model `corsair_captain` (90 cubes, 256x128, one texture).
- `src/main/java/com/brasshaven/entity/boss/CorsairCaptain.java`: the moveset.

There is no lair module. The arena is the moored ship's open top deck (`deck()` in
`tools/wf/structures/airship_graveyard.py`): 42 x 35 of planking at y `DY`, a two-high iron bulwark all round (sealed bars
at the west end, the deckhouse with the mist to the east), four copper vent cowls as low cover, seal radius 18 at the
deck centre `AC`. `BOSS` there is `brasshaven:corsair_captain` (it replaces the borrowed Gryphon Knight, whose own home,
quest and seal on the sky island are untouched). `BOSS_HOME` is `airship_graveyard`.

Reward: `remembrance_corsair_captain` forges the **Harpoon Gun of the Corsair Captain** (`corsair_harpoon`, LITHITE
7.5 / -2.6).
- It has a new ability shape, **GRAPPLE**, in `BossWeaponItem`: a harpoon fired along the aim (up to 18 blocks, walls stop
  it). The first foe it bites takes 10 (flag `slow`) and the line hauls the wielder to 1.5 blocks short of it; if it bites
  a wall, the line hauls the wielder there. Either way Slow Falling 3 s and the fall distance is reset.
- Held model `corsair_harpoon` in `wf/held3d.py`, sprite `harpoon_gun` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, diamonds, firework rockets, gunpowder, phantom membranes, a spyglass, wind
charges and an 8% enchanted golden apple. Quest: `explorer/boss_corsair_captain`.

**Concept.** The sky-pirate who took the last airship of the fleet, 4.8 blocks: a tall, lean captain in a long teal
greatcoat (two rows of brass buttons, crimson lapels, gold epaulettes, turned-back brass cuffs, tails to her boots that
stream in the wind), buff breeches and tall black boots, a red sash and a bandolier of brass flare cartridges. A black
tricorn edged in brass with aviator goggles (glowing sky-blue lenses) and a white plume, a long auburn braid, a red scarf.
On her back a brass rotor engine (a gauge, a glowing vent, two copper tanks, exhausts) whose mast carries a four-blade
rotor over the hat, always turning. Asymmetry: a basket-hilted cutlass in the right hand, a heavy harpoon gun (drum
magazine, flare canister, a barbed harpoon in the muzzle) in the left.

**Stats.**
- 580 health, armour 10, toughness 3, attack 13, poise 115, speed 0.27, knockback resistance 1.0, step 1.25.
- No fall damage, white bar. Hitbox 1.6 x 4.8.

**Phase 2 at 65%.** The roar; 4 ticks after it ends she chains `muster`: a signal flare and `scaledCount(2)` sky raiders
(the existing `sky_raider` mob, minion tag) appear 3 blocks over the deck at 0.55-0.9 x reach, never more than 4 alive.
The cutlass gains its thrust, the flare shot a second flare; `boarding` and `cyclone` join.

**Phase 3 at 30%, the list.** Driven by the class like the Chained Jailer: `listing` runs once (guard 74 ticks), then
`list()`: a ring to jump (12, out to 13), +10% speed (`corsair_captain_listing`), a list side (random) and the lane timer.
If fewer than 2 raiders are alive, `muster` follows. From then on:
- **Wind lanes** every 74 + max(110, 200 x `cooldownScale()`) ticks (an Effect, she keeps fighting). The deck's cross axis
  is measured once per fight (the shorter span between walls round the centre; demo spawn: the z axis). Four strips 3
  wide run across the deck along it, 7 apart (safe gaps 4 wide, offset randomly by up to 1.5). Each is drawn 30 ticks
  (white edges, red for the last 10, wind streaming toward the list side), then blows 14 ticks: 4 once and a shove
  toward the rail (0.16 a tick, at most 0.8). They fire one after another, 10 ticks apart, sweeping from one end
  (random) to the other.
- **Flare-bombs** (`flarebomb`, chosen like any move once listed; before that `gate` redirects it).

Scheduled moves (`muster`, `listing`) use range 999 / weight 0 and are chained from `bossTick`.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| cutlass | 1-3 | 14 / 26 / 14 | 0-5.5 | Arc drawn (+-70°, 4.8): cuts at active 0 and 10 (10 each). P2+: a red line, then at active 20 a lunging thrust down a 6.5 line (13). |
| harpoon | 1-3 | 18 / 16 / 14 | 6-20 | A red line that turns with the target; the harpoon flies down it (20, walls stop it): the first one within 1 of the line takes 8 and is reeled to 2.2 ahead of her over ticks 1-9; arc drawn ticks 8-11, then a cut at active 12 (9, +-60°, 3.8). |
| gust | 1-3 | 20 / 20 / 14 | 0-12 | Cone drawn (+-40°, 12 deep): 3 at impact, then 20 ticks of wind: a shove away from her (0.11 a tick, at most 0.7: sprinting against it holds). |
| divebomb | 1-3 | 16 / 34 / 18 | 5-22 | A gold ring on the target; take-off at impact (no gravity), rises 10 ticks to 8 over the ring, hovers while it follows the target (to active 14, then red, locked), plunges at 24, lands at active 30: 16 within 3 and a ring to jump (6, out to 7). |
| flareshot | 1-3 | 14 / 10 / 12 | 6-26 | A thin orange line; a flare flies 1.4 a tick from the gun at the target's position at the shot: 9 and alight 3 s on a hit, 6 within 1.5 where it bursts on a wall. P2+: a second at active 6 at another player. |
| boarding | 2-3 | 18 / 14 / 14 | 7-24 | Path drawn 14 ahead; a rush at 1 a tick for 12 ticks: 12 once to each creature in the way. Stops at walls, the arena edge or a drop. |
| cyclone | 2-3 | 16 / 16 / 14 | 0-5 | Red ring r 4.2; two spins at active 0 and 8 (11 each). |
| flarebomb | 3 | 20 / 24 / 14 | 0-30 | Rings follow every player (up to 4, plus strays to 3 and `scaledCount(1) - 1` more, at most 6) for 12 ticks, then lock red; a flare goes up every 4 ticks per ring and falls 18 ticks later: 10 within 2.5 and alight 2 s, then a fire patch. |
| muster | 2 | 20 / 10 / 14 | scheduled | See phase 2. |
| listing | 3 (once) | 30 / 20 / 20 | scheduled | Guarded; see phase 3. |

**Fair edges.** Her `strike` override caps knockback at 1.2 and lift at 0.35 (never over the two-high bulwark), and drops
the push where a probe 1 and 2 blocks along it finds neither a wall nor floor within 3 below. The gust and lane shoves
use the same probe and caps. Nothing kills outright: every hit is a number in the table.

**The blocks are temporary.**
- The only placed blocks are the fire patches: `minecraft:magma_block` swapped for up to five floor blocks in a plus
  (only full, plain blocks with air above, no block entity, never the seal). No fire block is ever placed (the deck is
  wood and wool). Each patch also burns 2 and sets alight every 10 ticks within 1.6.
- Every swap is recorded with its original state and goes back after 100 ticks, only where the block is still magma:
  - when the fight resets to phase 1 (`resetForm`);
  - when no player is within radius + 14;
  - in `onDefeated` and `remove()`;
  - after a reload (saved as `CorsairBlocks`, restored on the first tick).
- Sky raiders are discarded on death, reset or an empty arena; a dive cut short (stagger, reset, reload) gives her
  gravity back.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (flares, lanes and patches deal
her damage), poise, cooldowns (the lane timer uses `cooldownScale()`), compressed wind-ups, the soul wave. Raiders and
flare-bomb rings scale with the players (`scaledCount`).

Previews:
- `python3 tools/gen_models.py --preview --only corsair_captain` writes `build/previews/models/corsair_captain.png`.
- Held harpoon gun: `python3 tools/art_sheet.py --kind held --only corsair_harpoon`.

## 30. Champion of the Cloud Pagoda: The Chime Abbot (L'Abbé des carillons)
Files:
- `tools/wf/mobs/chime_abbot.py`: model `chime_abbot` (142 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/ChimeAbbot.java`: the moveset.

There is no lair module. The arena is the pagoda's open top deck under the ninth roof: `BOSS` in
`tools/wf/structures/cloud_pagoda.py` (`deck()`), seal at (0, 107, -20), radius 16; a 33 x 33 square deck (feet 108),
railing on its rim, the four 3 x 3 roof posts at the corners (±12), 13 blocks of air to the coffered roof, the mist at
the head of the stair from tier 8. The Chime Abbot replaces the borrowed Gryphon Knight there; the Gryphon Knight keeps
its own lair and `BOSS_HOME` (`sky_island`, `lair_gryphon_knight.py`).

Reward: `remembrance_chime_abbot` forges the **Dragon Staff of the Chime Abbot** (`abbot_dragonstaff`, LITHITE 7.5 / -2.6).
- It has a new ability shape, **DRAGON**, in `BossWeaponItem`: the brass dragon's spirit rushes along the aim (up to 14
  blocks, stopped by walls). Every foe within 1.5 of its path is hurt (power 10), flung aside out of the lane (0.8, lift
  0.35) and blinded (flag `blind`); the chimes ring where it ends: Slowness II 3 s within 3.5.
- Held model `abbot_dragonstaff` in `wf/held3d.py`, sprite `dragon_staff` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, cherry saplings, pink petals,
a bell, gold ingots, an 8% enchanted golden apple. Quest: `explorer/boss_chime_abbot`.

**Concept.** An ancient monk fused with clockwork, about 3 blocks tall, floating a hand's breadth over the deck:
- layered robes: a white under-robe, a cherry-red outer robe in flaring tiers open down the front, a gold-edged kasaya
  over the left shoulder with a tail at the left hip, a white obi with a gold cord, a heavy mala with a bell;
- an aged bald head, drooping white brows and a long beard; the right half of the skull is a riveted brass plate with an
  amber lens eye;
- behind his head a brass halo (a turning ring of 16 segments, a gear hub) with seven chime rods hanging from its lower
  arc and bells at its sides;
- wide white-lined sleeves with brass mechanical forearms, and a smaller pair of clockwork arms holding a prayer bell;
- asymmetry: the right hand holds a bronze staff with a brass dragon's head (horns, whiskers, teal eyes, chimes hanging
  from its jaws), the left hand is open for the palm strike.

**Stats.**
- 560 health, armour 12, toughness 4, attack 13, poise 110, speed 0.26, knockback resistance 1.0.
- No fall damage, pink bar.
- Phase 2 at 65% (roar, +10% speed, `chime_abbot_wrath`). Phase 3 at 30%, driven by the class like the Chained Jailer:
  when he is free he chains `awaken` once (guarded 64 ticks), then every 240 ticks x `cooldownScale()` (at least 140)
  `breath`. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| staff | 1-3 | 14 / 26 / 14 | 0-6.5 | Arc drawn in petals (±70°, 5): forehand at active 0 and backhand at 12 after a turn (12 each). P2: a red ring 3 ahead from active 15, slam at 22: 16 in r 2.5 + wave to 6 (7). P2: 30% chains flurry (close) or palm. |
| palm | 1-3 | 18 / 6 / 16 | 0-9 | Cone drawn in white wind (±28°, 9 deep): 14 and a push of 1.1. P2: a wave to 7 (7, jump). |
| chimering | 1-3 | 20 / 44 / 16 | 0-24 | Eight rods on a circle r 6.5 round him. P1: they ring round the circle every 4 ticks; P2: both ways from the first every 5 ticks, then a rod over every player (up to 4). Each rod's zone (r 2.4) is drawn gold, then red, for 12 ticks, then 11 and a small lift. |
| petals | 1-3 | 22 / 30 / 14 | 0-24 | Three gaps (±24°, 120° apart) drawn as white lines; a ring of petals rolls out at 0.55 b/t over the whole deck, too tall to jump: outside a gap, 5, a nudge and Blindness 1.5 s (P2 2 s). P2: a second ring at active 16, gaps turned 60° (drawn in pink from the impact). |
| step | 1-3 | 12 / 4 / 10 | 7-32 | A petal column at the deck corner (one of four spots on the diagonals at min(9, 0.6 x reach), found at runtime) nearest the target and not his own; he teleports there, then chains staff (target within 6.5) or palm. |
| flurry | 2-3 | 14 / 34 / 14 | 0-7 | Thrusts down a red line (6.5, half width 1) at active 0, 8, 16 (10 each, turning up to 25° between them); ring r 4.5 drawn from active 19, spin at 26: 13. |
| bellcrash | 2-3 | 20 / 20 / 18 | 5-24 | A gold ring r 3 follows the target through the wind-up, locks (red) for 10 ticks, then he lands on it (a standing spot found toward the centre): 17 in r 3 + wave to 8 (8, jump). |
| awaken | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks: he rises, brass dust spiralling in; a wave to 12 (11, jump), +12% speed (`chime_abbot_dragon`), the breath timer starts (50 ticks). The dragon's ghost (particles) circles over the deck from then on. |
| breath | 3 | 20 / 40 / 16 | scheduled | 3 lanes (4 with three players or more) across the deck, half width 1.6, at least 5.8 blocks of floor between them, one through the target, the axis alternating each time. All are drawn from the start; the next one turns red with the dragon's head waiting at its end 14 ticks before it fires. Lane i fires at active 6 + 10 i: the head crosses the deck in 8 ticks, 13 and Slowness II 2 s to whoever stands in the lane as it passes (once per lane). |

**No blocks.** He places no blocks at all: rods, petals, the dragon and its breath are particles, hit checks and
effects. Nothing to restore.

**No deaths off the edge.** His `strike` caps pushes at 1.2 and lift at 0.45 (0.2 within 3 blocks of the railing).
In the square metric, a push that points outward is removed on each axis where the target is within 3 blocks of the
railing, and the whole push where a probe 2 blocks along it finds no floor (the stairwells). The engine's phase-2 roar
shove is corrected the same way in `onPhaseTwo`. Teleports (step, bell-crash) only land on floor level with the seal
with 4 blocks of headroom.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the breath timer uses `cooldownScale()`), compressed wind-ups, the soul wave. Phase 2 chime
rods add one per player; breath lanes go from 3 to 4 with `scaledCount`.

Previews:
- `python3 tools/gen_models.py --preview --only chime_abbot` writes `build/previews/models/chime_abbot.png`.
- Held dragon staff: `python3 tools/art_sheet.py --kind held --only abbot_dragonstaff`.

## 31. Champion of the Soul Engine: The Soul Stoker (Le Chauffeur des âmes)
Files:
- `tools/wf/mobs/soul_stoker.py`: model `soul_stoker` (123 cubes, 256x256).
- `src/main/java/com/brasshaven/entity/boss/SoulStoker.java`: the moveset.

There is no lair module. The arena is the crankshaft deck in the crankcase: `BOSS` in
`tools/wf/structures/soul_engine.py` (`arena()`), seal at (0, 41, -7) (blueprint), radius 18; a 39 x 39 deck (feet 42,
x -19..19, z -26..12), 16 blocks of air to the crankcase roof (girders and soul chandeliers at y 58), the railing over
the 9-block crank trench on the north side, the flywheel bay east, the sealed reliquary bars in the west wall, four big
soul braziers at (±16, -23 / 9). The Soul Stoker replaces the borrowed Gryphon Knight there; the Gryphon Knight keeps its
own lair and `BOSS_HOME` (`sky_island`).

Reward: `remembrance_soul_stoker` forges the **Soul-Fire Shovel of the Stoker** (`stoker_shovel`, EMBER 8 / -3.0).
- It has a new ability shape, **STOKE**, in `BossWeaponItem`: five soul embers flung in a fan along the aim (12° apart,
  up to 12 blocks, walls stop them). Each bursts on the first foe within 0.8 of its flight or where it lands (dropped to
  the floor), 1.6 blocks round. A foe caught by k bursts takes one hit of power 12 x min(1.4, 0.6 + 0.2 (k - 1)),
  knockback 0.4, set ablaze (flag `fire`). Cooldown 80.
- Held model `stoker_shovel` in `wf/held3d.py`, sprite `coal_shovel` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): ancient embers, emeralds, experience bottles, golden apples, diamonds, soul lanterns, soul torches,
coal and bone blocks, pistons, a 25% netherite scrap, an 8% enchanted golden apple. Quest: `nether/boss_soul_stoker`.

**Concept.** A hulking furnace-man about 4 blocks tall:
- a squat boiler drum of polished blackstone in brass hoops for a torso, a grated firebox mouth in the belly glowing
  blue (glow layer), a pressure gauge and a valve wheel on the chest, riveted iron pauldrons;
- a furnace-door helmet: an iron door with brass hinges and a latch, a bone-white skull hammered into it whose eye-holes
  and nose burn blue; a latch-bar jaw that drops when he roars or vents;
- two ribbed chimneys on his back joined by a manifold, blue flame over their rims (scaled up in the anims);
- a broad leather belt with a buckle, five bone chains hanging from it, each ending in a soul lantern;
- asymmetry: the right arm ends in a giant coal shovel (iron-bound haft, D-grip knob, a sooty scoop heaped with soul
  embers), the left is a piston arm: a copper cylinder with brass piston rods, a steel sleeve with a gauge and an iron
  fist on a rod that shoots out when he punches.

**Stats.**
- 620 health, armour 14, toughness 5, attack 14, poise 130, speed 0.24, knockback resistance 1.0.
- Fire immune (entity type and class), no fall damage, blue bar.
- Phase 2 at 65% (roar, +10% speed, `soul_stoker_wrath`). Phase 3 at 30%, driven by the class like the Chained Jailer:
  when he is free he chains `overpressure` once (guarded 64 ticks), then every 220 ticks x `cooldownScale()` (at least
  120) `ringblast`. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| shovel | 1-3 | 16 / 20 / 16 | 0-7 | Arc drawn in soul dust (±75°, 5.5): 13, push 0.9. At impact 3 embers (P2 5) fly in a fan ±36° to spots 7-10 ahead (clamped to the deck); each ring (r 1.7) is drawn as it flies, red for the last 8 ticks, and bursts 18 ticks after impact: 8, fire 2 s. P2: 30% chains piston (close) or stoke. |
| piston | 1-3 | 28 / 12 / 18 | 0-14 | A line 14 long (half width 1.3) drawn in soul dust; he turns up to 5°/tick toward the target until wind-up 18, then it locks and turns red (10 ticks). Steam at the fist. Impact: 18 and push 1.2 within 4 of the fist; a shockwave front runs from 4 to 14 at 1.25 b/t: 10 and lift 0.55 (once), stopping where the deck ends. P2: 35% chains shovel if the target is within 6.5. |
| stoke | 1-3 | 40 / 16 / 20 | 0-12 | Scoops of souls into the firebox at wind-up 6, 16, 26; a gauge of 8 dust dots over his head fills blue to red. Cone ±32°, 11 deep (P2 13) drawn from wind-up 12, he turns 3°/tick until 28, then red. Impact: 15 and soul fire 4 s in the cone; flame particles for 12 ticks. |
| vents | 1-3 | 20 / 34 / 14 | 0-30 | 5 vents (P2 7, plus one under each other player up to 3), one under the target, at least 3.5 apart and 2.5 from him, only on floor level with the seal. Rings (r 2) and smoke from the start; vent k erupts at active 6 + 5k, its ring red for the last 10 ticks: 12, lift 0.6, soul fire 3 s. |
| charge | 2-3 | 24 / 16 / 16 | 6-22 | A lane (half width 1.4) through the target, 6-16 long, drawn from the start, red from wind-up 16. Active: he steps 1.1 a tick along it (teleport steps, only onto floor level with the seal with 5 blocks of headroom and inside the deck); 15 and push 1.1 to whoever is within 1.8 (once), then a slam where he stops (r 3, 8). |
| thralls | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 700. Souls at the firebox, then 2 wither skeletons (`summon`, +1 per 2 extra players) unless 3 minions already stand in the arena. |
| overpressure | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks: the gauge fills, rings of soul dust grow round him, steam. Impact: a wave to 12 (10, jump), +12% speed (`soul_stoker_overpressure`), the crank rhythm starts, the ring timer at 100 ticks. |
| ringblast | 3 | 20 / 40 / 16 | scheduled | Three gap angles (the first 50° off the target's bearing, then 25° further the same way each ring) drawn as lines from him (blue, gold, red) from the start; rings at active 0, 12, 24 roll out at 0.5 b/t over the whole deck, too tall to jump: outside the gap (±26°) 10 and soul fire 3 s (once a ring). |

**Crank rhythm (phase 3).** Strips 4 wide run along x (the crankshaft) across the deck. Every 60 ticks the strips of one
parity pulse (the parity alternates each pulse): 40 ticks of warning (their edges in soul dust every 4 ticks, red for the
last 12, small flames from tick 20, a piston sound), then 6 ticks of soul-fire jets: 5 and soul fire 2 s once a pulse to
any player on one. It is paused (and restarts from a full warning) while `ringblast` or `overpressure` runs.

**No blocks.** He places no blocks at all: embers, vents, rings, the crank strips and the gauge are particles, hit checks
and effects. Nothing to restore.

**No deaths off the edge.** His `strike` caps pushes at 1.2 and lift at 0.6 (0.25 within 3 blocks of the rim). In the
square metric, a push that points outward is removed on each axis where the target is within 3 blocks of the rim, and
the whole push where a probe 2 blocks along it finds no floor (the crank trench beyond the railing). The engine's
phase-2 roar shove is corrected the same way in `onPhaseTwo`. The charge stops at the deck's edge, at walls and props.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the ring timer uses `cooldownScale()`), compressed wind-ups. Thralls scale with
`summon`; phase-2 vents add one per extra player.

Previews:
- `python3 tools/gen_models.py --preview --only soul_stoker` writes `build/previews/models/soul_stoker.png`.
- Held shovel: `python3 tools/art_sheet.py --kind held --only stoker_shovel`.

## 32. Champion of the Clockwork Asylum: The Asylum Director (La Directrice de l'asile)
Files:
- `tools/wf/mobs/asylum_director.py`: model `asylum_director` (93 cubes, 128x128, one texture).
- `src/main/java/com/brasshaven/entity/boss/AsylumDirector.java`: the moveset.

There is no lair module. The arena is the clock stage at the top of the tower (`clock_stage()` in
`tools/wf/structures/clockwork_asylum.py`): 35 x 35 inside, 18 high, behind the four dials (the south one cracked), the
floor laid out as a clock face with a glass pendulum window in the middle, seal at (0, FC, TZ), radius 17. The stair from
the winding room comes up through the floor at the west (the mist at its head). `BOSS` there is
`brasshaven:asylum_director` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island are
untouched). `BOSS_HOME` is `clockwork_asylum`.

Reward: `remembrance_asylum_director` forges the **Bone-Saw of the Asylum Director** (`director_bonesaw`, LITHITE
7.5 / -2.6).
- It has a new ability shape, **REWIND**, in `BossWeaponItem`: the saw rips the wielder forward along the aim (up to 8
  blocks, stopped by walls), power 10 to every foe passed (flag `slow`). The start is remembered as a clock ghost
  (`item/Rewinds.java`, ticked from the server tick like `BlastCharges`); 40 ticks later the wielder is snapped back to it
  (not if sneaking, dead, in another level or more than 32 blocks away) and the saw's echo deals half the power within 2.5.
- Held model `director_bonesaw` in `wf/held3d.py`, sprite `bone_saw` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, a clock, glass bottles,
glistering melon slices, gold and iron ingots, an 8% enchanted golden apple. Quest: `explorer/boss_asylum_director`.

**Concept.** The surgeon who turned the sanatorium into an automaton workshop, 3.6 blocks, tall and thin (hitbox 1.2 x
3.7): a long stained white coat (open below the belt, split tails), dark trousers and buttoned boots, black rubber gloves
with long fingers; a brass plague-doctor mask with a curved beak and two glowing green lenses, a white surgical cap over a
grey bun, a head mirror; a high collar and a black cravat; a glass plate in the chest over a ticking clockwork heart
(red-amber glow, it pulses in the idle). On her back a brass harness with a turning cog carries four spindly surgical arms
spread like a spider's legs: scalpel and bone saw high, forceps and syringe low. A pocket watch hangs from her left hand.

**Stats.**
- 600 health, armour 12, toughness 4, attack 13, poise 110, speed 0.27, knockback resistance 1.0, step 1.25.
- No fall damage, white bar.
- Phase 2 at 65% (roar, +10% speed, `asylum_director_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when she is free she chains `midnight` once (guarded 64 ticks), then every 360 ticks x `cooldownScale()` (at
  least 200; the first 50 ticks after midnight) `hands`. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| scalpel | 1-3 | 14 / 8 / 14 | 2.5-11 | Turns toward the target for 10 ticks (white line), then a red line locks (up to 7, only over floor level with the seal, inside the room); she lunges along it in 5 ticks: 13 to each one within 1.4 of her path (once). |
| saw | 1-3 | 16 / 24 / 14 | 0-6 | Arc drawn (+-100°, 5.5): 14. P2: turn (30°) at active 5, arc red 6-13, back sweep at active 14 (11); 30% chains dissect (close) or forceps. |
| syringe | 1-3 | 18 / 12 / 12 | 5-24 | A green line follows the target for 12 ticks, then red; a dart flies 1.5 b/t (24 at most, walls stop it): 8 + Slowness II 3 s. P2: a fan of 3 (+-12°). |
| rewind | 1-3 | 20 / 8 / 14 | 0-28 | At impact a clock ghost marks the target (P2: every player, up to 4) where they stand (on the floor). It runs backward 60 ticks (a tick every 10, chimes at 50 and 55); then the player is teleported back to it if they moved more than a block (no hold, momentum zeroed). Its ring (r 2), drawn all along and red from tick 50, bursts 14 ticks after the snap: 12. |
| pendulum | 1-3 | 24 / 36 / 14 | 0-30 | Lanes through the room's centre (half width 1.5, wall to wall), the first through the target, each next one turned 45° (one way per cast). Swing k at active 12k: the lane is drawn 24 ticks before (brass), red the last 12; the bob crosses in 10 ticks: 14 and a shove out of the lane (1.0). 2 swings, 3 in P2. |
| spiders | 1-3 | 18 / 4 / 14 | 0-30 | 2 (P2 3) clockwork spiders, `scaledCount`, never more than 4 alive (minion tag). |
| forceps | 2-3 | 16 / 22 / 14 | 0-8 | Red line (7, half width 0.9): the first one in it takes 8 and is hauled to 1.6 ahead of her over active 1-6 (velocity, no hold), then let go; arc drawn 6-13, cut at active 14 (+-60°, 3.8): 10. |
| dissect | 2-3 | 16 / 30 / 14 | 0-5 | The four quarters round her facing (r 4.5, +-45°) in a random order, struck at active 0, 8, 16, 24: 9 each. The next quarter is drawn red for the 8 ticks before, the one after it white. |
| timeslip | 2-3 | 12 / 2 / 8 | 7-28 | A clock ghost 2.5 behind the target (following until tick 6, then red, a standing spot); she teleports there, then chains saw. |
| midnight | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; a growing clock face, a bell every 4 ticks; a wave to 14 (11, jump), +12% speed (`asylum_director_midnight`), the hands' timer starts. |
| hands | 3 | 30 / 180 / 16 | scheduled | She teleports to the centre. The minute hand starts 45° clockwise of the target, the hour hand 90° behind it, so the target starts in the gap. Wind-up and active 0-10: both hands drawn red from the centre to the walls, the gap gold, a bell every 10 then 5 ticks. Then both turn clockwise 270° in 170 ticks (1.59°/tick: 0.17 b/t at 6 blocks out); she faces the minute hand. Each hand deals 12 once (half width 0.9, from 0.6 out) and a small shove away from it. Safe: the gap, which moves. |

**No blocks.** She places no blocks at all: the ghosts, lanes, pendulum, darts and hands are particles and hit checks.
The spiders are discarded on death, removal, a reset or an empty arena; a reset also cancels every pending rewind (an
epoch counter), so nobody is snapped back after the fight ends.

**Fair edges.** Her `strike` caps pushes at 1.2 and lift at 0.45 (0.2 within 3 blocks of a wall); in the square metric the
outward part of a push is removed near the walls, and all of it where a probe 1 or 2 blocks along it finds no floor (the
stairwell). The engine's phase-2 roar shove is corrected the same way. Teleports (time-slip, hands) land only on floor
level with the seal with 4 blocks of headroom; the lunge never leaves such floor. The rewind's teleport is the only loss of
control, and only back to where the player stood 3 s earlier inside the room.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the hands' timer uses `cooldownScale()`), compressed wind-ups, the soul wave. Spiders scale
with `scaledCount`; the phase-2 rewind marks every player.

Previews:
- `python3 tools/gen_models.py --preview --only asylum_director` writes `build/previews/models/asylum_director.png`.
- Held bone-saw: `python3 tools/art_sheet.py --kind held --only director_bonesaw`.

## 33. Champion of the Icebound Fleet: The Frozen Commodore (Le Commodore gelé)
Files:
- `tools/wf/mobs/frost_commodore.py`: model `frost_commodore` (103 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/FrostCommodore.java`: the moveset.

There is no lair module. The arena is the icebreaker's forecastle deck (`tools/wf/structures/icebound_fleet.py`, the seal
at the arena centre `AC`, radius 18): about 34 wide, the bridge front aft (the stair from the wheelhouse comes down to
the mist at the arena door), the bow tapering ahead, a two-high bulwark all round, capstans, hatches and the sealed hood
on the deck; the deck lists about 4° to starboard (floor within ±1 block of the seal). `BOSS` there is
`brasshaven:frost_commodore` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island
are untouched). `BOSS_HOME` is `icebound_fleet`. The structure may be rotated: the class finds the bow at runtime as
the axis direction with the longest run of open deck (three parallel probes).

Reward: `remembrance_frost_commodore` forges the **Ice Anchor of the Frozen Commodore** (`commodore_anchor`, LITHITE
8.5 / -3.0).
- It has a new ability shape, **ANCHOR**, in `BossWeaponItem`: the anchor is hurled along the aim on its chain
  (`item/AnchorThrows.java`, ticked from the server tick like `Rewinds`): 2 blocks a tick up to 12 blocks (walls stop
  it). It bites the first foe it meets (full power) or the end of its throw; frost bursts there for half the power
  within 2 blocks. It lies 5 ticks, then the chain drags it back to the wielder at 1.5 blocks a tick: every foe within
  1.3 of its way back takes 70% of the power, is hauled 0.8 toward the wielder and slowed (flag `slow`). Cooldown 80.
- Held model `commodore_anchor` in `wf/held3d.py`, sprite `ice_anchor` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, blue and packed ice, iron
chain, a spyglass, a compass, an 8% enchanted golden apple. Quest: `explorer/boss_frost_commodore`.

**Concept.** The expedition's commander, dead in the ice but kept moving by a frost-rimed brass life-support rig,
3.8 blocks (hitbox 1.8 x 3.8):
- a long navy greatcoat lined and collared with grey fur, double-breasted with brass buttons, gold epaulettes, a ribbon
  bar; patches of ice crust all over, icicles off the hem, the cuffs and the beard;
- an iron hood made like a diving bell on a brass collar ring, frost on its dome, a round porthole visor with guard
  bars, cracked and frosted, glowing pale blue (glow layer); a frozen white beard spills out under it;
- on his back a copper boiler drum in brass hoops (the rig), iced over, a gauge and a glowing pilot window, two vent
  pipes over the shoulders venting cold steam (scaled in the anims), hoses into the hood;
- asymmetry: the right hand grips a huge ice-encrusted anchor by the shank (its stock across, the crown and spade
  flukes near the ground, chain links wound round the forearm); the left hand holds a stubby brass flare pistol with a
  glowing flare in its mouth.

**Stats.**
- 640 health, armour 13, toughness 4, attack 14, poise 120, speed 0.25, knockback resistance 1.0, step 1.5.
- No fall damage, cannot freeze, white bar.
- Phase 2 at 65% (roar, +10% speed, `frost_commodore_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `blizzard` once (guarded 64 ticks), then every 280 ticks x `cooldownScale()` (at
  least 160; the first 140 ticks after the blizzard) `ramshock`. Range 999 / weight 0 keeps the scheduled moves out of
  the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| anchor | 1-3 | 18 / 22 / 14 | 0-6.5 | Arc drawn in frost (±80°, 5.5): forehand at impact, 14, push 1.0. At active 2 he turns up to 30° toward the target and the backhand's arc is drawn red (active 2-11); backhand at active 12: 11, push 0.8. P2: 30% chains breath (within 7) or hurl. |
| throw | 1-3 | 24 / 36 / 14 | 4-18 | A line (half width 1.2) over open deck up to 16, drawn in frost; he turns 4°/tick until wind-up 14, then it locks red. The anchor crosses it in 10 ticks (12, once), bites at the end (8 in r 2; the ring drawn during the flight), lies 6 ticks with the way back drawn red, then is dragged back to his hand in 14 ticks: 10, Slowness II 2 s, frost, hauled 0.7 toward him (once). |
| spikes | 1-3 | 20 / 30 / 14 | 0-24 | 3 lines (P2 5), 25° apart, the middle one at the target, up to 16 over open deck, drawn from the start, red from wind-up 12. At impact spikes burst along each line one point a tick from him outward: 12 and lift 0.5 (once per line). |
| breath | 1-3 | 30 / 24 / 16 | 0-10 | Cone ±30°, 10 deep, drawn from wind-up 8; he turns 3°/tick until 20, then red. Active 0-19: snow and cold cloud; hits at active 0, 5, 10, 15: 4, Slowness II 3 s, frost (no push). |
| hurl | 1-3 | 20 / 12 / 14 | 5-24 | 2 rings (P2 3, r 2): the target (following until wind-up 12), the other players, then open deck 4-7 from the target, at least 4 apart. All red from wind-up 12. Blocks of ice fly 18 ticks from impact: 11, push 0.4 out of the ring, then a 3 x 3 slippery patch of packed ice for 100 ticks. |
| strays | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 700. A signal flare fired straight up; 2 strays (`summon`, +1 per 2 extra players) unless 3 minions already stand in the arena. |
| flare | 2-3 | 16 / 10 / 12 | 6-26 | A line (half width 0.6) up to 24 over open deck drawn in orange; he turns 5°/tick until wind-up 10, then red. The flare flies 1.6 b/t and bursts on the first one it meets or at the end: 9 and fire 2 s in r 2. |
| blizzard | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; rings of frost grow round him, steam. Impact: a wave to 14 (10, jump; it hits only who stands within 0.6 of the floor), +12% speed (`frost_commodore_blizzard`), the blizzard starts (ram timer 140, icicles 40). |
| ramshock | 3 | 30 / 40 / 16 | scheduled | The ship's bell at wind-up 0, 10, 20; the bow end of the deck drawn (frost, red from 18). At impact and at active 20: a wave front across the whole deck rolls from the bow end to the stern end at 0.7 b/t: 9 and a shove of 0.5 sternward to whoever stands on the floor where it passes (once a wave). Jump it. |

**Blizzard (phase 3).** Snow over the deck every 2 ticks, frost dust on it every 10; every 5 ticks each player on the
deck gets frozen ticks up to 120 (the frost overlay, never the 140 that hurts) and every 20 ticks Slowness I for 1.5 s.
No sliding: the deck itself is not changed. Every 60 ticks x `cooldownScale()` (at least 34) a volley of icicles:
`scaledCount(3)` spots plus one over the target and one over each other player (up to 3), on open deck, at least 3.5
apart. Each ring (r 1.6) is drawn for 30 ticks (red for the last 10, the icicle falling from 12 blocks up in that time),
then 10 and Slowness I 2 s. The icicles wait while `ramshock` or `blizzard` runs and while the ram waves roll.

**Temporary blocks.** The slippery patches are the only blocks he places: packed ice over plain full deck blocks (air
above, no block entity, not ice already) in the 3 x 3 under each block of ice. Each goes back after 100 ticks (only
where it is still packed ice), and all of them when the fight resets (phase back to 1), the arena empties, he dies, is
removed, and on the first tick after a reload (saved in `CommodoreBlocks`). His strays are discarded on death and
reset.

**Fair edges.** His `strike` caps pushes at 1.2 and lift at 0.45. A push is dropped entirely when a probe 1.5 or 3
blocks along it finds no open deck (the bulwark, a prop, the arena's edge, a drop), and then the lift is capped at 0.2;
the engine's phase-2 roar shove is corrected the same way. The throw, spikes and flare lines only run over open deck.
The deck's list is handled by measuring every floor height locally (waves hit whoever stands within 0.6 of the floor
under them).

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the ram and icicle timers use `cooldownScale()`), compressed wind-ups. Strays scale with
`summon`; icicles with `scaledCount` and one per player; phase-2 ice blocks land on every player (up to 3).

Previews:
- `python3 tools/gen_models.py --preview --only frost_commodore` writes `build/previews/models/frost_commodore.png`.
- Held anchor: `python3 tools/art_sheet.py --kind held --only commodore_anchor`.

## 34. Champion of the Spore Refinery: The Spore Alchemist (L'Alchimiste des spores)
Files:
- `tools/wf/mobs/spore_alchemist.py`: model `spore_alchemist` (89 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/SporeAlchemist.java`: the moveset.

There is no lair module. The arena is the open-sky top of the giant fly agaric's cap
(`tools/wf/structures/spore_refinery.py`, the seal 4 blocks north of the cap's axis, radius 19): about 42 wide, fenced
at r 21 (from the axis) with brass railings and stem posts crowned by mushroom lamps, a gilded ring inlaid at r 14 round
the axis, and two railed stairwell openings in the floor (the arrival ramp east of the axis, the vault stair south of
it). `BOSS` there is `brasshaven:spore_alchemist` (it replaces the borrowed Gryphon Knight, whose own home, quest and
seal on the sky island are untouched). `BOSS_HOME` is `spore_refinery`. The class finds the gilded ring at runtime
(the `gilded_trim` blocks in the floor layer round the seal: their centroid and mean radius; without at least 24 it uses
the arena centre and 0.7 x radius), and checks the floor is flat (70% of samples within 0.6 of the seal's level: the
floor tolerance is then 0.6, else 1.6), so stair treads one block down count as holes.

Reward: `remembrance_spore_alchemist` forges the **Stirring Staff of the Spore Alchemist** (`alchemist_staff`, LITHITE
7.5 / -2.8).
- It has a new ability shape, **TETHER**, in `BossWeaponItem`: a spore flask flung along the aim
  (`item/SporeTethers.java`, ticked from the server tick like `AnchorThrows`): 1.5 blocks a tick up to 12 blocks
  (walls stop it). It shatters on the first foe it meets or at the end of its flight (dropped to the floor when within
  1.5): every foe within 2.5 takes the full power (flag `poison`). Mycelium threads tether every foe within 4 to the
  spot for 60 ticks (Slowness II for 70 ticks; a foe more than 2.5 from it is dragged back), and when they snap the
  spores burst again: half the power to every tethered foe still within 6. Cooldown 90.
- Held model `alchemist_staff` in `wf/held3d.py`, sprite `spore_staff` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, red and brown mushrooms,
mycelium, glass bottles, fermented spider eyes, an 8% enchanted golden apple. Quest: `explorer/boss_spore_alchemist`.

**Concept.** A hunched alchemist half-consumed by the fungus he refined, 3.5 blocks (hitbox 1.6 x 3.5):
- stooped forward (the chest pitched 26°), a long stained leather apron and bib (test tubes in its pocket) over a plum
  work coat, a belt of vials (two glow), white mycelium threads trailing from the cuffs, the coat tails and the boots;
- a rough hood with a brass respirator faceplate: a grilled snout, two copper filter canisters and two round goggle
  lenses glowing spore-green (glow layer);
- the hump is a fly agaric sprouting from his back (red cap with white warts, gills under it, a pale stalk with its
  ring, two little caps budding beside it; it swells in the anims);
- orange bracket fungi on both shoulders; mottled grey-green hands;
- a brass spore-tank in copper bands on his lower back (a glowing gauge window, a valve with a red wheel), a hose to
  the left hand;
- asymmetry: the right hand leans on a long dark stirring staff (brass ferrule and collars, a small red mushroom on the
  pole, a round flask of glowing green brew at the tip); the left hand holds a brass nozzle-gun with a copper nozzle and
  a glowing spore reservoir.

**Stats.**
- 620 health, armour 11, toughness 3, attack 13, poise 105, speed 0.24, knockback resistance 1.0, step 1.5.
- No fall damage, green bar; Poison, Slowness and Blindness do not take on him (his own clouds).
- Phase 2 at 65% (roar, +10% speed, `spore_alchemist_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `bloom` once (guarded 64 ticks), then every 320 ticks x `cooldownScale()` (at
  least 180; the first 140 ticks after the bloom) `exhale`. Range 999 / weight 0 keeps the scheduled moves out of the
  picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| staff | 1-3 | 16 / 20 / 14 | 0-6 | Arc drawn green (±75°, 5): the sweep at impact, 13, push 0.9. At active 1 he turns up to 30° toward the target and a ring (r 2) 3.5 ahead is drawn red (active 1-11); the flask comes down on it at active 12: 11, lift 0.3, Poison I 2 s. P2: 30% chains spray (within 8) or flask. |
| spray | 1-3 | 24 / 20 / 16 | 0-9.5 | Cone ±28°, 9 deep, drawn from wind-up 6; he turns 3°/tick until 16, then red. Active 0-19: spores; hits at active 0, 5, 10, 15: 3 and Poison I 3 s (no push). At active 19 a lingering cloud (area effect cloud of Poison I, r 2.5 shrinking, 100 ticks, its edge drawn green every 8 ticks) 5 ahead on open cap. |
| flask | 1-3 | 20 / 10 / 14 | 4-24 | 2 rings (P2 3, r 2.2) in the brew's colour (the first always poison, the rest random: green poison, grey slowness, black blindness): the target (following until wind-up 12), the other players, then open cap 4-7 from the target, at least 4 apart; a red ring inside each from wind-up 12. Flights 16 ticks from impact: 8, push 0.3 out of the ring, then Poison II 3 s / Slowness II 3 s / Blindness 2 s. |
| sprout | 1-3 | 18 / 8 / 16 | 0-26 | At impact a ring (r 1.5) under each player (up to 4) plus `scaledCount(2)` (P2 4) open spots within the ring + 4, at least 3 apart; drawn brown for 30 ticks (red for the last 10), then the mushroom bursts: 10, lift 0.5, Poison I 2 s; a stem and a red mushroom block stand there 120 ticks if both blocks are air and no creature is in them. |
| shroud | 2-3 | 20 / 40 / 14 | 0-30 | A cloud grows round him. At impact he hides (invisible, guarded until he comes out) and picks a spot 5-8 from the target, at least 4.5 from every player, the whole ring (r 3) over open cap, 4 blocks clear. The ring is drawn active 0-29 (red from 20); he moves there at active 20 and bursts out at active 30: 11, push 0.6 out of the ring, Poison I 3 s. |
| bogged | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 700. 2 bogged (`summon`, +1 per 2 extra players) unless 3 minions already stand in the arena. |
| bloom | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; rings of spores grow round him. Impact: a wave to 14 (10, jump; it hits only who stands within 0.6 of the floor), +12% speed (`spore_alchemist_bloom`), the cap starts breathing (exhale timer 140, vents 60). |
| exhale | 3 | 50 / 10 / 16 | scheduled | Alternates the outside of the gilded ring (first) and the inside. Wind-up: the ring drawn gold every 2 ticks and 40 spore motes over the side that will breathe out (green, red from 36). Impact: 9 and Poison II 3 s to every player on that side (inside: closer than ring - 1; outside: further than ring + 1; within 3.5 of the floor's level, so jumping does not help). The ring's band is always safe. |

**The cap breathes (phase 3).** Every 80 ticks x `cooldownScale()` (at least 40) `scaledCount(2) + 1` vents spread
round the ring's centre, each as far out as ring + 4 or 2.5 short of the last open cap along its ray, nudged inward
until the whole ring (r 2) lies over open cap; each ring is drawn 30 ticks (red for the last 10), then a geyser: 8,
lift 0.4, Poison I 2 s (no push). The vents wait while `exhale` or `bloom` runs or he is guarded. The mycelium tether
field: every 5 ticks threads are drawn from him to every player within 6 (and a ring of threads every 10), and every
20 ticks they get Slowness I for 1.5 s; walk out of it.

**Temporary blocks.** The sprouted mushrooms are the only blocks he places: a mushroom stem and a red mushroom block
over the open cap floor (both air before, nobody in them, at most 28 at once), set without neighbour shape updates so
the cap's mushroom blocks keep their faces. Each goes back after 120 ticks (only where it is still that block), and
all of them when the fight resets (phase back to 1), the arena empties, he dies, is removed, and on the first tick
after a reload (saved in `AlchemistBlocks`). His bogged are discarded on death and reset; the shroud's invisibility is
lifted when the move is cut short, on reset, death and reload.

**Fair edges.** His `strike` caps pushes at 1.1 and lift at 0.45. A push is dropped entirely when a probe 1.5 or 3
blocks along it finds no open cap (a stairwell, a railing, the fence, the edge), and then the lift is capped at 0.2;
the phase-2 roar shove is corrected the same way. "Open cap" also means no further than ring + 6 from the ring's
centre, short of the fence. Flask, sprout, vent and shroud spots only land on open cap, never over the stairwells.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`/`shove`), poise, cooldowns (the exhale and vent timers use `cooldownScale()`), compressed wind-ups. Bogged
scale with `summon`; sprouts and vents with `scaledCount` and one per player; phase-2 flasks land on every player (up
to 3).

Previews:
- `python3 tools/gen_models.py --preview --only spore_alchemist` writes `build/previews/models/spore_alchemist.png`.
- Held staff: `python3 tools/art_sheet.py --kind held --only alchemist_staff`.

## 35. Champion of the Sunken Arboretum: The Head Gardener (Le Jardinier en chef)
Files:
- `tools/wf/mobs/thorn_gardener.py`: model `thorn_gardener` (89 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/ThornGardener.java`: the moveset.

There is no lair module. The arena is the giant lily pad in the palm house dome (`tools/wf/structures/verdant_arboretum.py`,
`arena()`, the seal at the dome centre on the pad, radius 17): a flat pad of radius 16 (33 across) with a red upturned
rim 2.5 high, on a brass pedestal over the dome's pool, under the hanging sun-lamp (its core about 19 above the pad). The
east and north rib bridges land in notches of the rim. `BOSS` there is `brasshaven:thorn_gardener` (it replaces the
borrowed Gryphon Knight, whose own home, quest and seal on the sky island are untouched). `BOSS_HOME` is
`verdant_arboretum`. "Open pad" in the class means floor within 0.6 of the seal's level with two blocks of air over it,
inside the arena radius: the rim and the water are never open pad.

Reward: `remembrance_thorn_gardener` forges the **Pruning Shears of the Head Gardener** (`gardener_shears`, LITHITE
8.0 / -2.6).
- It has a new ability shape, **PRUNE**, in `BossWeaponItem`: the blades open and snap shut along the aim (up to 7
  blocks, walls stop them, 1.2 to each side). Every foe between them takes the power, 150% under half health; thorns
  burst round each foe cut, snaring it and the foes within 1.5 (Slowness III 1.5 s; flag `slow` adds the usual slow);
  each cut heals the wielder 1 (4 at most). Cooldown 70. Instant, no ticker.
- Held model `gardener_shears` in `wf/held3d.py`, sprite `pruning_shears` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, sweet berries, bone meal,
moss, azaleas, shears, an 8% enchanted golden apple. Quest: `explorer/boss_thorn_gardener`.

**Concept.** A tall brass gardening automaton left to tend the palm house alone until the garden grew into it,
3.8 blocks (hitbox 1.6 x 3.8):
- a barrel-chested riveted copper body, brass seam straps, verdigris toward the waist, a glowing green chlorophyll
  porthole; moss cushions on the shoulders, ivy strands (flat planes) hanging from the seams front, back and sides;
- a glass bell jar for a head (see-through: brass frame, glints and condensation only) on a brass collar, moss inside
  and a magenta-and-gold flower growing in it (glow layer), scaled and swayed in the anims;
- very long arms: brass upper arms, red-lacquered shear-grip forearms, and at each wrist two steel blades on a brass
  pivot bolt that open and snap (`jaw_?a` / `jaw_?b`);
- a verdigris watering can on his back made into a cannon: a brass barrel over his RIGHT shoulder to a sprinkler rose
  (water glints in the glow layer), a ribbed hose looping to his hip;
- piston legs in terracotta flowerpot boots, roots out of the toes and trailing behind, a fan of fine roots flat
  on the ground.

**Stats.**
- 650 health, armour 12, toughness 4, attack 14, poise 115, speed 0.26, knockback resistance 1.0, step 1.5.
- No fall damage, green bar.
- Phase 2 at 65% (roar, +10% speed, `thorn_gardener_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `ignite` once (guarded 64 ticks), then every 320 ticks x `cooldownScale()` (at least
  200; the first 200 ticks after the ignition) `photosynth`. Range 999 / weight 0 keeps the scheduled moves out of the
  picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| snip | 1-3 | 16 / 14 / 14 | 0-6 | Arc drawn green (±70°, 5): right shears at impact, 12, push 0.6. At active 1 he turns up to 25° toward the target and the left arc is drawn red (active 1-7); left shears at active 8: 10, push 0.5. P2: 30% chains spray (within 7) or lunge. |
| lunge | 1-3 | 22 / 12 / 16 | 4-12 | A lane (half width 1.0) over open pad up to 9, plus 3 for the blades, drawn green; he turns 4°/tick until wind-up 14, then it locks red. Active 0-4 he moves down the lane (to 1 short of its end, `move`, collisions kept); at active 4 the blades close on the whole lane from his start to 3 past him: 15, push 0.5. |
| thorns | 1-3 | 20 / 24 / 14 | 0-22 | 3 lines (P2 5), 22° apart, the middle one at the target, up to 15 over open pad, drawn from the start, red from wind-up 12. At impact thorns burst along each line one point a tick: 11, lift 0.4, Slowness I 1 s (once per line). |
| snare | 1-3 | 24 / 10 / 14 | 3-18 | A ring (r 1.6) under the target, following until wind-up 14, then red; a vine creeps to it from his feet. Impact: 6 and a player is rooted 30 ticks (Slowness X, ambient off); it tears at once when that player hits anything (`getLastHurtMobTimestamp` changes) or loses health to anything, and on reset, death, removal, or an empty arena. Mobs get Slowness IV 1.5 s. |
| spray | 1-3 | 26 / 20 / 14 | 0-11 | Cone ±25°, 11 deep, drawn blue from wind-up 6; he turns 3°/tick until 16, then red. Active 0-19: water jet; hits at active 0, 5, 10, 15: 3, a push of 0.35 away (dropped where it would leave the pad), puts out fire. At active 19: 2 patches (P2 3) in the cone, 4-10 out, 3 apart: each ring (r 1.5) drawn 30 ticks (red the last 10), then 7 in it, lift 0.3, and sweet berry bushes (age 2) in the air over the moss cells of the plus round it, for 100 ticks. |
| call | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Dart frog assassins and clockwork spiders alternately, `scaledCount(2)`, at most 3 alive, on open pad 3.5 from him; tagged minions, discarded on death and reset. |
| pollen | 2-3 | 18 / 12 / 14 | 0-24 | Rings (r 2.2) drawn yellow: the target, the other players, then open pad 4-7 from the target, 4 apart; 2 (P3 3, at least one per player up to 4). At impact puffs arc from the bloom in 16 ticks (rings red): 8, Slowness I 2 s. |
| ignite | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; gold rings grow round him, light rains from the lamp. Impact: a ring of light to 14 (10, jump; it hits only who stands within 0.6 of the floor), +12% speed (`thorn_gardener_sun`), the sunbeams start (first volley 50 ticks later). |
| photosynth | 3 | 30 / 50 / 16 | scheduled | A gold ring r 3 round him, a column of light growing down from the lamp. Active pulses at 5, 15, 25, 35, 45: +1% max health unless a player stands within 3 (+ half width) of him, in which case the pulse is lost (smoke over the shading players). No damage at all in this move. |

**Sun-lamp (phase 3).** Light motes drift over the pad. Every 90 ticks x `cooldownScale()` (at least 50) a volley of
sunbeams, `min(4, scaledCount(2))` of them: one across the target, one across each of up to 2 other players, the rest
across random open pad. Each starts 3-5 blocks back from its mark on a random bearing and runs through it to 4 beyond,
clipped to open pad. The ring (r 2) and the path are drawn gold for 30 ticks (red the last 10), then the beam (a column
from the lamp) sweeps the path at 0.22 blocks a tick (slower than walking): 4 and fire 2 s, at most every 10 ticks per
target. New volleys wait while `ignite` or `photosynth` runs.

**Temporary blocks.** The thorn bushes are the only blocks he places: sweet berry bushes in plain air over the pad, only
where a bush can survive (the moss tiles; elsewhere particles only). Each goes back to air after 100 ticks (only where
it is still a sweet berry bush), and all of them when the fight resets (phase back to 1), the arena empties, he dies, is
removed, and on the first tick after a reload (saved in `GardenerBlocks`).

**Fair edges.** His `strike` caps pushes at 1.0 and lift at 0.4. A push is dropped entirely when a probe 1.5 or 3 blocks
along it finds no open pad (the rim, the bridge notches, the water), and then the lift is capped at 0.2; the spray and the
engine's phase-2 roar shove are corrected the same way. Lines, lanes, patches, rings and beams only use open pad. The
snare is short (1.5 s), clearly drawn, and breaks the moment anything hurts the rooted player, so no follow-up lands on
a held player for free. Photosynthesis heals at most 5% and is fully blocked by standing next to him.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the beam and photosynthesis timers use `cooldownScale()`), compressed wind-ups. Adds scale
with `scaledCount`; sunbeams with `scaledCount` and one per player; pollen rings land on every player (up to 4).

Previews:
- `python3 tools/gen_models.py --preview --only thorn_gardener` writes `build/previews/models/thorn_gardener.png`.
- Held shears: `python3 tools/art_sheet.py --kind held --only gardener_shears`.

## 36. Champion of the Abyssal Station: The Abyssal Diver (Le Scaphandrier des abysses)
Files:
- `tools/wf/mobs/abyss_diver.py`: model `abyss_diver` (79 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/AbyssDiver.java`: the moveset.

There is no lair module. The arena is the drill chamber at the bottom of the trench (`tools/wf/structures/abyssal_station.py`,
`arena()`, the seal 6 blocks east of the chamber's middle, radius 18): a round air-filled room 34 wide under the brass
skylight dome, sealed from the sea, the drill string hanging over the borehole (shroomlight and magma) in the middle,
four hydraulic struts rising from the wall to the drill collar, spoil heaps against the wall. `BOSS` there is
`brasshaven:abyss_diver` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island are
untouched). `BOSS_HOME` is `abyssal_station`. The class finds the chamber's middle at runtime (the centroid of the
shroomlight cells in the floor layer round the seal; without at least 4 it uses the seal's spot), and "open floor" means
floor within 0.6 of the seal's level with two blocks of air over it, within 14.5 of the middle (short of the struts'
feet and the heaps; radius - 3 without the borehole).

Reward: `remembrance_abyss_diver` forges the **Drill-Lance of the Abyssal Diver** (`diver_drill_lance`, LITHITE 8.5 / -3.0).
- It has a new ability shape, **BORE**, in `BossWeaponItem`: the drill bores along the aim (up to 8 blocks, walls stop it,
  1.0 to each side). Every foe in the bore takes the power plus half its armour value (at most +6: the pressure cracks
  plating), is drawn in toward a point 2 blocks ahead of the wielder and gets Glowing for 5 s; flag `slow`. Cooldown 80.
  Instant, no ticker.
- Held model `diver_drill_lance` in `wf/held3d.py`, sprite `drill_lance` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, prismarine crystals,
nautilus shells, glow ink sacs, copper ingots, a 15% heart of the sea, an 8% enchanted golden apple. Quest:
`explorer/boss_abyss_diver`.

**Concept.** The station's chief diver fused with his armoured diving suit, 3.8 blocks (hitbox 1.8 x 3.8):
- a huge round brass hard-hat (stacked boxes for roundness, a row of bolts, verdigris), a 10 x 10 front porthole with a
  grille glowing bioluminescent teal (glow layer), two small side ports, a top valve with its wheel, an air elbow behind;
- a riveted brass corselet the helmet sits in, lead chest weights front and back, over a patched, salt-stained canvas suit
  (chest pitched 8° forward: hulking); a leather weight belt with four lead weights;
- two copper pressure tanks in brass hoops on his back with a gauge, ribbed rubber hoses to the helmet and round to the
  drill arm (the tanks swell in the anims);
- asymmetry: the RIGHT arm is a brass motor housing with cooling slots and a giant stepped spiral drill (part `drill`,
  spun about its axis in the anims, ending on a whole turn); the LEFT hand holds a rivet gun (dark iron, brass bands, a
  brass drum magazine) with a barbed harpoon in its barrel;
- lead boots with brass toe caps and straps; barnacle clusters on the helmet, corselet, pauldrons, boots and tanks; kelp
  strands (planes) hanging from the belt, the tanks and the right pauldron.

**Stats.**
- 660 health, armour 13, toughness 4, attack 14, poise 120, speed 0.24, knockback resistance 1.0, step 1.5.
- No fall damage, blue bar, breathes underwater; Blindness and Darkness do not take on him (his own silt).
- Phase 2 at 65% (roar, +10% speed, `abyss_diver_wrath`). Phase 3 at 30%, driven by the class like the Chained Jailer:
  when he is free he chains `groan` once (guarded 64 ticks), then every 360 ticks x `cooldownScale()` (at least 220; the
  first 160 ticks after the groan) `overcharge`. Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| thrust | 1-3 | 22 / 12 / 16 | 4-12 | A lane (half width 1.0) over open floor up to 8, plus 2.5 for the drill, drawn aqua; he turns 4°/tick until wind-up 14, then it locks red. Active 0-4 he moves down the lane (to 1 short of its end, `move`, collisions kept); at active 4 everyone in the lane from his start to 2.5 past him: 14, push 0.6. |
| grind | 1-3 | 16 / 30 / 14 | 0-5.5 | Arc ±40°, 4.5 deep, drawn aqua (red from wind-up 10, turning 3°/tick until then). Active 0-29: sparks, the arc red; bites at active 0, 10, 20: 5 each (no push; 10 ticks apart so hurt frames never eat them). P2: 30% chains slam (within 6) or rivets. |
| rivets | 1-3 | 20 / 24 / 14 | 5-24 | 3 lines (P2 5), 9° apart, from the gun muzzle to the first wall (at most 22), drawn on the floor aqua, following (4°/tick) until wind-up 12, then red. Volleys at active 0, 10, 20 along the same lines: each rivet flies 2 blocks a tick and stops on the first creature within 0.7 of it: 5, push 0.3. |
| slam | 1-3 | 24 / 12 / 16 | 0-8 | A ring r 5 round him drawn aqua (red from 16). Impact: 12, push 0.6, lift 0.4 within the ring; then a wave runs from 5 to 11 (0.5 a tick): 6, jump it (it hits only who stands within 0.6 of the floor). |
| harpoon | 1-3 | 20 / 14 / 14 | 6-18 | A line from the muzzle to the first wall (at most 18), drawn aqua, following (5°/tick) until wind-up 12, then red. At impact the harpoon flies 2 blocks a tick: the first creature it bites takes 6 and is hauled toward him (velocity min(1.2, travel / 6), lift 0.3; travel = distance - 3, at most 7: never closer than 3). P2: 50% chains grind if it bit someone. |
| silt | 2-3 | 18 / 10 / 14 | 0-14 | A ring r 4.5 drawn dark (red from 12), ink rising off him. Impact: 4, push 0.7, lift 0.2 and Blindness 2 s within the ring; a silt cloud stays there 80 ticks (edge drawn every 8 ticks): every 10 ticks whoever is in it gets Blindness 1.5 s. |
| call | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Drowned marines and drowned alternately, `scaledCount(2)`, at most 3 alive, on open floor 3.5 from him; tagged minions, discarded on death and reset. |
| groan | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; aqua rings grow round him, water drips from the dome (particles), the hull creaks. Impact: a wave to 14 (10, jump), the hull starts groaning (spikes 50 ticks later, the first jelly 30). |
| overcharge | 3 | 30 / 10 / 16 | scheduled | A ring r 3.5 drawn yellow (red from 20), sparks. Impact: 8, push 0.8, lift 0.3 within it; then 140 ticks of overcharge: +20% speed (transient `abyss_diver_overcharge`), his hits x1.15, damage taken x1.15. |

**The hull groans (phase 3).** Water drips from the dome and the hull creaks (particles and sounds: nothing is opened or
placed). Pressure spikes: every 70 ticks x `cooldownScale()` (at least 40), `min(5, scaledCount(2) + 1)` circles: under
the target, under up to 2 other players, the rest on random open floor, at least 3 apart; each ring (r 2, an inner ring
r 0.9) drawn aqua 30 ticks (red the last 10), then it bursts: 8, lift 0.5 (no push). Bioluminescent jellies (particles
only): every 100 ticks x `cooldownScale()` (at least 60), while fewer than `min(5, scaledCount(2) + 1)` drift, one
appears on open floor at least 6 from every player at chest height; it drifts 0.05 a tick toward the nearest player
(only over open floor), a ring r 1 drawn under it; a player within 1.4 (and 1.6 in height) lights its fuse: 12 ticks,
its ring r 2 red, then it bursts: 7, push 0.5, lift 0.3, Slowness I 1 s within 2. Each fades harmlessly after 400 ticks.
Spikes and jellies wait while `groan` runs or he is guarded.

**Blocks.** He places and breaks none: the chamber is an air pocket under the sea, so every hazard (silt, spikes,
jellies, drips) is particles, sounds and damage. His drowned are discarded on death and reset; the jellies are cleared on
reset, death, when the chamber empties and on reload; the overcharge modifier is transient (never saved) and removed on
reset and death.

**Fair edges.** His `strike` caps pushes at 1.0 and lift at 0.45. A push is dropped entirely when a probe 1.5 or 3 blocks
along it finds no open floor (the wall, a strut, a spoil heap), and then the lift is capped at 0.2; the engine's phase-2
roar shove is corrected the same way. The harpoon's haul only pulls toward him and stops 3 short. Lanes, spikes, adds
and jellies only use open floor. The silt blinds for 2 s at most and its cloud is drawn.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`/`shove`), poise, cooldowns (the spike, jelly and overcharge timers use `cooldownScale()`), compressed wind-ups.
Adds scale with `scaledCount`; spikes and jellies with `scaledCount` and one spike per player (up to 3).

Previews:
- `python3 tools/gen_models.py --preview --only abyss_diver` writes `build/previews/models/abyss_diver.png`.
- Held drill-lance: `python3 tools/art_sheet.py --kind held --only diver_drill_lance`.

## 37. Champion of the Timber Fortress: The Lumber Jarl (Le Jarl du bois)
Files:
- `tools/wf/mobs/lumber_jarl.py`: model `lumber_jarl` (74 cubes, 256x256).
- `src/main/java/com/brasshaven/entity/boss/LumberJarl.java`: the moveset.

There is no lair module. The arena is the keep's crown (`tools/wf/structures/timber_fortress.py`, `platform()` and
`arena()`, the seal at K(8, 10) on the deck at y 64, radius 20): a 49-wide timber platform railed in brass round the
beam engine (bed plate, flywheel r 7 in the north-south plane 8 north of the keep's axis, cylinder, columns), a gilded
ring inlaid at r 12 round the axis, two stair houses (south-west with the mist, north-east with the sealed bars), the
stave spire and the smokestack in two corners. `BOSS` there is `brasshaven:lumber_jarl` (it replaces the borrowed
Gryphon Knight, whose own home, quest and seal on the sky island are untouched). `BOSS_HOME` is `timber_fortress`. The
class finds the gilded ring at runtime (the `gilded_trim` blocks in the floor layer round the seal; their centroid is
the keep's axis, without at least 24 it uses the arena centre), which places the flywheel. "Open deck" means floor
within 0.6 of the seal's level with two blocks of air over it, inside the arena radius and inside the railing square
(23 from the axis): the engine's bed, the stair houses and their wells, the railing and the drop are never open deck.

Reward: `remembrance_lumber_jarl` forges the **Steam Chainsaw-Axe of the Lumber Jarl** (`jarl_chainaxe`, LITHITE
9.0 / -3.1).
- It has a new ability shape, **FELL**, in `BossWeaponItem`: a chainsaw sweep in front (3.5 blocks, ±70°: the power to
  every foe in it), then the ground splits along the aim (up to 9 blocks, stopped by walls and drops, like the RIFT
  footing): 70% and a throw upward to every foe on the split, 50% more to a foe caught by both. Cooldown 80. Instant,
  no ticker.
- Held model `jarl_chainaxe` in `wf/held3d.py`, sprite `chainsaw_axe` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, spruce logs, stripped
spruce logs, an iron axe, coal, iron chains, an 8% enchanted golden apple. Quest: `explorer/boss_lumber_jarl`.

**Concept.** A giant lumberjack warlord, 4 blocks (hitbox 1.8 x 4.0):
- a horned iron helm under a fur brim (a nose guard, a brass crest knob, two ox horns curving up and out), a fierce
  face, a great red beard with a moustache and two long braids ringed in iron;
- a red-and-black buffalo-check shirt over a barrel chest (the belly bulges), a chainmail mantle over the shoulders
  and upper chest, a fur collar, leather harness straps with brass buckles, a wide belt with a brass buckle;
- plaid trousers, leather bindings, fur cuffs, heavy iron-shod boots;
- a log-carrier harness on his back: an iron frame, two spruce logs across (rings showing at the ends), straps, a
  spare saw blade on each side and a little stack;
- the steam chainsaw-axe in his right hand (both hands in the swings): a long iron-banded ash haft with two leather
  grips, a brass engine at its head with a glowing firebox (glow layer) and a sooty smokestack, a steel bar with its
  toothed chain jutting forward, a bearded axe blade behind.

**Stats.**
- 660 health, armour 13, toughness 4, attack 15, poise 120, speed 0.25, knockback resistance 1.0, step 1.5.
- No fall damage, red bar.
- Phase 2 at 65% (roar, +10% speed, `lumber_jarl_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `overdrive` once (guarded 64 ticks); the engine hazards then run from the class.
  Range 999 / weight 0 keeps the scheduled move out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 18 / 16 / 14 | 0-6.5 | Arc drawn orange (±80°, reach 5.5, P3 7; red from wind-up 12), the engine revving. Bites at active 0, 5, 10, 15: 4 each to whoever is in the arc, push 0.25 (each bite clears the i-frames so all four can land). |
| chop | 1-3 | 24 / 16 / 16 | 0-16 | A line (half width 1.0) over open deck up to 14 and a ring (r 2) 2 ahead, drawn orange; he turns 4°/tick until wind-up 16, then red. Impact: 16 in the ring, push 0.6; the split runs from 2 out one block a tick: 10, lift 0.45 (once), and bursts at its end: 6 within 2.5, push 0.5. P2: 30% chains roll (target past 6) or sweep. |
| blade | 1-3 | 20 / 12 / 16 | 5-20 | A loop drawn gold (red from wind-up 14): out along his facing (to the target + 2, at most 14, over open deck) bulging 3.5 to one side, back on the other. At impact the blade flies it a point a tick (about 2.4 points a block): 9, push 0.3, lift 0.2, again after 12 ticks (out and back). P2: two blades on mirrored loops. |
| timber | 1-3 | 20 / 10 / 16 | 0-30 | At the start a lane (6 x 2, along x or z) under each player (up to 4) and `scaledCount(2)` (P2 3) on open deck 4-9 from the target, 3-3.5 apart, drawn brown; at impact red for 10 ticks, then three spruce logs drop from 12 above (falling-block visuals, removed when they reach the deck); the crash: 11 and Slowness I 1.5 s in the lane. |
| roll | 1-3 | 26 / 10 / 14 | 4-24 | A lane (half width 1.5) over open deck up to 22, drawn brown; he turns 3°/tick until wind-up 16, then red. At impact a log (a weightless falling-block visual) rolls down it at 0.7 a tick: 10, lift 0.3 and a push of 0.7 out of the lane's side (once). |
| call | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 700. Vindicators and bandit marksmen alternately, `scaledCount(2)`, at most 3 alive, on open deck 3.5 from him; tagged minions, discarded on death and reset. |
| overdrive | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; orange rings grow round him, the flywheel smokes and sparks. Impact: a wave to 14 (10, jump; it hits only who stands within 0.6 of the floor), +12% speed (`lumber_jarl_overdrive`), the engine hazards start (sparks 60 ticks later, vents 40), the sweep's reach grows to 7. |

**The engine overdrives (phase 3).** Smoke and sparks pour off the flywheel. Every 140 ticks x `cooldownScale()` (at
least 80) a spark sweep: a wedge (±35°, 22 long) from the ground under the flywheel toward the target, drawn orange for
30 ticks (red the last 10), then a jet of sparks sweeps across it from one edge to the other in 24 ticks (alternately
each way): 6 and fire 2 s, once per sweep, to whoever the jet (1 wide) crosses. Every 100 ticks x `cooldownScale()` (at
least 60) `scaledCount(2) + 1` steam vents (the first within 2 of the target, the rest 3-10 from it, 4 apart, on open
deck): each ring (r 1.8) drawn white for 30 ticks (red the last 10), then 7 and lift 0.4. Both wait while `overdrive`
runs or he is guarded.

**Temporary blocks.** None. The falling and rolling logs are `FallingBlockEntity` visuals (put into an air cell for an
instant and lifted out, `disableDrop`, no item): removed when they reach the deck or end their run, after 60 ticks at
most, when the fight resets (phase back to 1), the arena empties, he dies or is removed, and on the first tick after a
reload (found by the tag `brasshaven_jarl_log`). His crew is discarded on death and reset.

**Fair edges.** His `strike` caps pushes at 1.0 and lift at 0.45. A push is dropped entirely when a probe 1.5 or 3
blocks along it finds no open deck (the railing, a stair house or its well, the engine, the edge), and then the lift is
capped at 0.2; the roll's side push and the engine's phase-2 roar shove are corrected the same way. Lines, lanes, rings
and vents only use open deck. The multi-bite sweep is 16 at most and fully drawn before it starts.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`/`shove`), poise, cooldowns (the spark and vent timers use `cooldownScale()`), compressed wind-ups. The crew
scales with `scaledCount`; timber lanes land on every player (up to 4) plus `scaledCount` more; vents with
`scaledCount`.

Previews:
- `python3 tools/gen_models.py --preview --only lumber_jarl` writes `build/previews/models/lumber_jarl.png`.
- Held axe: `python3 tools/art_sheet.py --kind held --only jarl_chainaxe`.

## 38. Champion of the Hollow Moon: The Moon Warden (La Gardienne de la lune)
Files:
- `tools/wf/mobs/moon_warden.py`: model `moon_warden` (76 cubes, 128x128, five texture variants: the dial's phase).
- `src/main/java/com/brasshaven/entity/boss/MoonWarden.java`: the moveset.

There is no lair module. The arena is the core platform of the Hollow Moon (`tools/wf/structures/hollow_moon.py`,
`pillar_and_platform()` / `arena_dress()`, the seal at the centre, radius 15): a flat disc of radius 17 (34 across, feet
50) ringed by a brass railing over the void, three short amethyst posts at r 13.5, the bridge mouth (ring 3) and the
reliquary kiosk open in the rail; the glowing core (a sphere of sea lanterns and crying obsidian, r 4.3) hangs 16 over
the centre in its armillary rings. `BOSS` there is `brasshaven:moon_warden` (it replaces the borrowed Gryphon Knight,
whose own home, quest and seal on the sky island are untouched). `BOSS_HOME` is `hollow_moon`. "Open platform" in the
class means floor within 0.6 of the seal's level (1.6 if the floor round the seal is rough: a command spawn) with two
blocks of air over it, inside the arena radius: the rail, the posts and the void are never open platform.

Reward: `remembrance_moon_warden` forges the **Astrolabe Blade of the Moon Warden** (`moon_astroblade`, VOID 9.0 / -2.6).
- It has a new ability shape, **ORBIT**, in `BossWeaponItem`: three brass planets fly out from the wielder along spiral
  arms (out to 10 blocks, 120° apart, each winding 9° a step so that one of them ends on the aim; blocks stop an arm).
  Every foe a planet passes is hit for the power (once per arm; flag `slow` adds the usual slow) and drawn 0.35 toward
  the wielder; where the arm on the aim ends a small gravity well pulls the foes within 3 to its centre. Cooldown 80.
  Instant, no ticker.
- Held model `moon_astroblade` in `wf/held3d.py`, sprite `astro_blade` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): void shards, emeralds, experience bottles, golden apples, diamonds, end rods, amethyst shards,
chorus fruit, ender pearls, a clock, a 15% enchanted golden apple. Quest: `explorer/boss_moon_warden`.

**Concept.** An elegant celestial automaton that kept the moon machine turning after its astronomers left, 3.6 blocks
(hitbox 1.4 x 3.6), levitating:
- a slender porcelain-white body in gold inlay, a narrow waist, a glowing moonstone in the bodice, gold-capped shoulders;
- a round moon-phase dial for a face (gold bezel, night sky, the moon disc lit to the phase), crown points, and behind
  it a gold halo (r 10) and two orrery hubs whose brass arms carry four small planets, turning in the idle loop
  (`halo`, `orrery`, `orrery2`);
- very long porcelain arms in gold rings, a pierced gold astrolabe at each wrist and a long pale blade under it
  (`blade_?`);
- a cloak of starfield (glowing stars) with gold edges from the shoulders (`cape`, `cape_lo`), a skirt of starfield over
  purpur flaring in three tiers to a gold hem that never touches the floor; four end-rod thrusters under it (END_ROD
  particles under her in game).
- Texture variants (`modelVariant()` = synched `DATA_MOON`): 0 full, 1 waning, 2 new, 3 waxing, 4 eclipse (a black disc
  in a gold corona).

**Stats.**
- 720 health, armour 12, toughness 5, attack 15, poise 120, speed 0.27, knockback resistance 1.0, step 1.5.
- No fall damage, purple bar.
- Phase 2 at 65% (roar, +10% speed, `moon_warden_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when she is free she chains `eclipse` once (guarded 64 ticks). Range 999 / weight 0 keeps the scheduled moves
  (`shade`, `radiance`, `eclipse`) out of the picker.
- **Moon cycle** (phases 1-2): every 220 ticks x `cooldownScale()` (at least 120) of fighting while she is free, the
  dial turns full -> waning -> new -> waxing -> full (she starts waxing). Turning to the new moon chains `shade`, to the
  full moon `radiance`; in the crescents (waxing, waning) the second blade of `sweep` throws a crescent. The cycle stops
  at the eclipse (dial variant 4).

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| sweep | 1-3 | 18 / 14 / 14 | 0-6.5 | Arc drawn silver (±80°, 5.5): right blade at impact, 13, push 0.5. At active 1 she turns up to 25° and the arc is drawn red (active 1-7); left blade at active 8: 11, push 0.4. Crescent phases: at active 8 a crescent (±40°) flies out from 2 to 13 at 0.55 a tick: 7 once. P2: 30% chains flip (within 8) or orbit. |
| orbit | 1-3 | 24 / 30 / 14 | 0-20 | 3 spirals (P2 5) spread evenly round her facing, 1.8 + 0.7 a point, 11° of turn a point, clipped to open platform within radius - 0.5; drawn gold from the start, red from wind-up 16. At impact a planet runs each spiral one point a tick: 9 (once a spiral), lift 0.1. |
| well | 1-3 | 28 / 20 / 14 | 0-18 | A point at the target moved inside radius - 5; inner ring r 2.5 violet (red from wind-up 18), reach r 7 dotted. Active 0-15: everyone within 7 gets +0.045 a tick toward it (horizontal speed capped at 0.3, slower than walking away). Active 16: 10 and lift 0.35 in the inner ring. |
| flip | 1-3 | 22 / 10 / 16 | 0-20 | Rings r 2.5 under the target and up to 2 other players (P2 +1 near the target), kept inside radius - 3, 4 apart; they follow their players until wind-up 12, then red. Impact: 7, no push, horizontal speed zeroed, Levitation II 20 ticks and Slow Falling 80 ticks. |
| shade | 1-2 (new moon) | 24 / 40 / 14 | scheduled | Lines (2, `scaledCount`, +1 in P2, at most 4) through the target, other players, random platform, up to 9 each way, inside radius - 1.5; drawn in shadow, red from wind-up 14. At impact the shades run them one after another (6 ticks apart) at 0.9 a tick: 9 and Slowness I 1 s (once a line). |
| radiance | 1-2 (full moon) | 30 / 30 / 14 | scheduled | Gold rings converge on her. Impact: a ring of moonlight runs out to the arena radius at 0.5 a tick: 10, lift 0.3, only to who stands within 0.6 of the floor (jump it). P2: a second ring at active 14. |
| comet | 2-3 | 30 / 10 / 18 | 5-18 | No gravity; she rises 0.12 a tick for 24 ticks. A ring r 3 at the target (inside radius - 3) follows until wind-up 20, then red. Active 0-4 she moves onto it (`move`, collisions kept); active 5: gravity back, 13 and lift 0.3 in r 3. Gravity is also restored by `bossTick` whenever no comet runs. |
| summon | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Void larvae and star motes alternately, `scaledCount(2)`, at most 3 alive, 3.5 from her; tagged minions, discarded on death and reset. |
| eclipse | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; dark rings converge, a corona round the core. Impact: the core's sea lanterns become tinted glass, Darkness 2 s on the fighters, a dark ring runs to the arena radius (10, lift 0.3, jump it), +10% speed (`moon_warden_eclipse`), dial variant 4; the hazards start. |

**Eclipse (phase 3).** Dark motes drift, a corona flickers round the core.
- *Gravity sweep*: first 80 ticks after the eclipse, then every 300 ticks x `cooldownScale()` (at least 200, counted
  between sweeps). Three beams 120° apart, radial lines from 2.5 out to the arena radius, a line of particles down from
  the core to each. Drawn 40 ticks (violet, red the last 10, gold arrows beside each beam showing the way it will turn;
  Darkness 1.5 s at the start), then they turn for 140 ticks at 0.75° a tick (0.2 blocks a tick at the rim, less than
  walking; the direction alternates every sweep): 5 and Slowness I 1 s to whoever is within 0.8 (+ half width) of a beam,
  at most every 10 ticks. Walk with the gap; the centre (r < 2.5) is never swept.
- *Meteors*: every 110 ticks x `cooldownScale()` (at least 60), only between sweeps: `min(4, scaledCount(2))` circles
  (r 2.2): the target, up to 2 other players (inside radius - 2), the rest random platform, 3 apart. Drawn 30 ticks
  (red the last 10), the meteor falls in the last 12: 8 and lift 0.3.
- Both wait while `eclipse` runs.

**Temporary blocks.** The only blocks she changes are the core's sea lanterns (within 6 of the point 16 over the
arena centre), turned to tinted glass at the eclipse. They go back (only where still tinted glass) when the fight
resets (phase back to 1), the arena empties, she dies, is removed, and on the first tick after a reload (saved in
`MoonBlocks`; a reload mid-eclipse dims the core again at once).

**Fair edges (the void).** Her `strike` caps pushes at 0.8 and lift at 0.4. A push is kept only when open platform lies
1.5 and 3 blocks along it within radius - 1.5 of the centre; otherwise it becomes a pull toward the centre (at most 0.5)
and the lift is capped at 0.2. Almost every move pushes nothing at all (only the two sweeps do); the engine's phase-2
roar shove is cut to 30% and corrected the same way. The flip lifts straight up and gives Slow Falling, its rings sit
inside radius - 3; the well and the comet target points pulled inside the rim; lines, spirals and beams only use open
platform.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the moon, sweep and meteor timers use `cooldownScale()`), compressed wind-ups. Adds,
shades and meteors scale with `scaledCount`; flip rings and meteors land on every player (up to 3).

Previews:
- `python3 tools/gen_models.py --preview --only moon_warden` writes `build/previews/models/moon_warden.png` (and one
  sheet per dial variant).
- Held blade: `python3 tools/art_sheet.py --kind held --only moon_astroblade`.

## 39. Champion of the Crimson Colosseum: The Gilded Champion (Le Champion doré)
Files:
- `tools/wf/mobs/gilded_champion.py`: model `gilded_champion` (114 cubes, 256x256, two texture variants: `plain` and
  `gilded`).
- `src/main/java/com/brasshaven/entity/boss/GildedChampion.java`: the moveset.

There is no lair module. The arena is the sand floor of the colosseum (`tools/wf/structures/crimson_colosseum.py`,
`arena()`, the seal at the centre at y 5, radius 20): an oval of sand and red sand 44 x 34 (semi-axes 22 x 17) ringed by
the podium wall (its walk at feet 15) and the stands, a gilded ring (11 x 8.5) round the centre, the four 3 x 3 iron
trapdoors of the beast lifts at (+-14, 0) and (0, +-9), the Gate of Life to the south. `BOSS` there is
`brasshaven:gilded_champion` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island
are untouched). `BOSS_HOME` is `crimson_colosseum`. The class finds the **grates** at runtime (clusters of at least 4
iron trapdoors in the floor layer within the arena radius; without two of them, four points 9/7 from the centre). "Open
sand" means floor within 0.6 of the seal's level with two blocks of air over it, inside the arena radius: the podium
wall, the stands and the gate passages are never open sand.

Reward: `remembrance_gilded_champion` forges the **Gilded Gladius of the Champion** (`champion_gladius`, EMBER
9.0 / -2.4).
- It has a new ability shape, **TRIUMPH**, in `BossWeaponItem`: a gladiator's thrust along the aim (up to 7 blocks,
  walls stop it, 1.0 to each side): every foe in it takes the power and a push; a foe under 30% health takes the
  finishing blow for 50% more. The crowd roars for every foe struck: Absorption for 10 s (I, II or III for 1, 2, 3+
  foes). Cooldown 70. Instant, no ticker.
- Held model `champion_gladius` in `wf/held3d.py`, sprite `gladius` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): ancient embers, emeralds, experience bottles, golden apples, diamonds, gold blocks, gilded
blackstone, netherite scrap, a golden sword, iron chains, a 12% enchanted golden apple. Quest:
`nether/boss_gilded_champion`.

**Concept.** The undefeated piglin gladiator, 4 blocks (hitbox 1.8 x 4.0):
- a crested gladiator's helmet of gold (bowl, brim, cheek guards, brow plate, a tall crimson horsehair crest front to
  back and its tail down the nape) over a piglin head: flat snout, heavy jaw, floppy ears (`ear_?`) hanging out under
  the cheek guards, two tusks capped in gold;
- a gilded muscle cuirass over a crimson tunic, a gorget, layered pauldrons with crimson tufts, belly lames, a gold
  manica down the sword arm, a gold arm ring and leather bracer on the shield arm, gilded greaves and knee cops,
  netherite sabatons with gold toes;
- a skirt of crimson pteruges tipped in gold under a studded gold belt, chains of trophies (`trophies`: two little
  skulls, gold coins, a looted helmet);
- a crimson cape (`cape`, `cape_lo`);
- the gladius (`gladius`): crimson-wrapped grip, gold pommel and guard, a netherite blade edged in gold; the round
  shield (`shield`, a disc r 10 of crimson and gold rays in a gold rim) with a hoglin skull boss.
- Texture variants (`modelVariant()` = synched `DATA_GILDED`): `plain`; `gilded` (phase 3): brighter gold with a
  glowing layer on the plate's edges, ember eyes, the shield's cubes painted empty (cast aside) and the second gladius
  (`gladius2`, in the left hand, painted empty in `plain`) shown.

**Stats.**
- 700 health, armour 14, toughness 5, attack 15, poise 130, speed 0.26, knockback resistance 1.0, step 1.5.
- No fall damage, yellow bar.
- Phase 2 at 65% (roar, +10% speed, `gilded_champion_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `favour` once (guarded 64 ticks); the lava jets then run from the class. Range
  999 / weight 0 keeps the scheduled moves (`riposte`, `favour`) out of the picker. Once gilded, `bash` and `block`
  turn into `combo` when picked.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| combo | 1-3 | 16 / 18 / 14 | 0-6.5 | Arc drawn gold (+-75 deg, 5): forehand cut at impact, 12, push 0.4. At active 1 he turns up to 20 deg, the arc drawn red (active 1-7); backhand at active 8: 11. P2: a line (6, half width 1) drawn red active 9-15, thrust at active 16: 13, push 0.6 along it. Gilded: instead an arc (+-80, 5.5) drawn red, both blades crossing at active 16: 13. P2 (not gilded): 25% chains bash within 5. |
| bash | 1-3 | 14 / 8 / 16 | 0-4.5 | Arc (+-50, 4) drawn gold, red from wind-up 8. Impact: 9, push 0.9, lift 0.2, Slowness II 1 s. |
| block | 1-3 | 12 / 40 / 12 | 0-10 | Cooldown 220. A wall of motes (+-70 at 1.6) in front of him from the start. Active 40: he turns 2.5 deg/tick toward the target; a blow whose source lies within +-70 deg of his facing is turned aside (no damage, a clang, a small push back to a melee attacker within 5); flank and back blows hurt 30% more. If at least one blow was turned aside, he chains riposte. |
| riposte | 1-3 (after a block) | 10 / 6 / 14 | scheduled | Faces the target; a line (6, half width 1.1) drawn red the whole wind-up. Impact: he steps 1.2 forward, 13 and a push 0.6 along the line. |
| charge | 1-3 | 24 / 16 / 14 | 6-24 | A lane (half width 1.2) over open sand up to 20, drawn gold; he turns 3 deg/tick until wind-up 16, then red. Active: he runs it at lane / 12 a tick (0.6-1.6), stopping 1 short of its end: 14, lift 0.35 and a push 0.8 out of the lane's side (once each). |
| net | 1-3 | 20 / 10 / 16 | 4-20 | A ring r 2.6 on the target follows until wind-up 12, then red. Impact: the net flies 6 ticks, lands: 4 and Slowness III 3 s in the ring; it lies there 60 ticks more (a gold grid; Slowness II 0.6 s every 10 ticks to whoever stands in it). P2: a second net on another player (or 6 from the first). |
| crowd | 1-3 | 22 / 30 / 16 | 0-30 | Cooldown 260. Circles r 2 under each player (up to 4) plus `scaledCount(2)` (P2 3, gilded +1) open sand 3.5-9.5 from the target, 3.5 apart, drawn gold (orange for fire charges). At impact each is red while its debris arcs in from the stands behind it, landing 8 + 4i ticks later: 8 and lift 0.3; P2 every second one is a fire charge: 7, lift 0.2, fire 3 s. |
| gates | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 700. The grates marked gold. Piglin brutes and hoglins alternately (immune to zombification), `scaledCount(2)`, at most 3 alive, at the grates farthest from the target; tagged minions, discarded on death, reset and after a reload. |
| favour | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; gold rings converge, the crowd roars. Impact: a gold ring runs out to 14 (10, jump it: it hits only who stands within 0.6 of the floor), +12% speed (`gilded_champion_favour`), variant `gilded`, the lava jets start (the first 60 ticks later). |

**The emperor's favour (phase 3).** Gold motes and small flames stream off him; the grates smoke. Every 120 ticks x
`cooldownScale()` (at least 70) `min(4, scaledCount(1) + 1)` grates (the nearest to the target, then random ones) fire a
lava jet toward the target: a ring r 1.8 on the grate and a line (half width 1.0, up to 16 over open sand) drawn orange
for 30 ticks (red the last 10), then flame and lava particles erupt along it from the grate out, 2 blocks a tick: 7,
lift 0.3 and fire 3 s, once per jet. They wait while `favour` runs or he is guarded. No lava block is ever placed.

**Temporary blocks.** None: he places and breaks no block (the debris, the nets and the lava jets are particles). His
beasts are discarded on death and reset, and tagged piglin/hoglin minions he no longer tracks are discarded on the
first tick after a reload.

**Fair edges.** His `strike` caps pushes at 1.0 and lift at 0.45. A push is dropped entirely when a probe 1.5 or 3
blocks along it finds no open sand (the podium wall, a gate passage), and then the lift is capped at 0.2; the charge's
side push, the block's push back and the phase-2 roar shove are corrected the same way. Lanes, lines, rings and
circles only use open sand. The block is shown before it starts and the riposte only follows a blow he turned aside.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`/`shove`), poise, cooldowns (the jet timer uses `cooldownScale()`), compressed wind-ups. Beasts, debris circles
and jets scale with `scaledCount`; debris lands under every player (up to 4).

Previews:
- `python3 tools/gen_models.py --preview --only gilded_champion` writes `build/previews/models/gilded_champion.png` (and
  `gilded_champion_gilded.png`).
- Held gladius: `python3 tools/art_sheet.py --kind held --only champion_gladius`.

## 40. Champion of the Clockwork Carnival: The Clockwork Ringmaster (Le Monsieur Loyal mécanique)
Files:
- `tools/wf/mobs/ringmaster.py`: model `ringmaster` (53 cubes, 128x128).
- `src/main/java/com/brasshaven/entity/boss/Ringmaster.java`: the moveset.

There is no lair module. The arena is the circus ring of the big top (`tools/wf/structures/clockwork_carnival.py`,
`big_top()`, the seal at the tent's centre (0, 0, -56), radius 22): a sawdust ring of radius 17.5 (36 wide, feet 1) with
a star of froglights in it, a red-and-white curb to 19 with the four king poles in it (±13, ±13), six tiers of benches
rising round it, the front tunnel (south, mist) and the performers' gate (north, sealed bars), the east and west aisles
up to the gallery, 25+ blocks of air to the chandeliers (the great one at 24 over the centre). `BOSS` there is
`brasshaven:ringmaster` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island are
untouched). `BOSS_HOME` is `clockwork_carnival`. "Open ring" in the class means floor within 0.6 of the seal's level
(1.6 if the floor round the seal is rough: a command spawn) with two blocks of air over it, within 17.5 of the centre
(`ringR()`): the curb's poles, the benches and the tunnel mouths are never open ring.

Reward: `remembrance_ringmaster` forges the **Showman's Cane of the Clockwork Ringmaster** (`ringmaster_cane`, LITHITE
8.0 / -2.4).
- It has a new ability shape, **JUGGLE**, in `BossWeaponItem`: three brass juggling bombs lobbed in arcs along the aim,
  landing at 40%, 70% and 100% of the throw (up to 12 blocks over the ground, cut short by walls and drops, like the
  RIFT footing). Each bursts in confetti (particle FIREWORK): the power to every foe within 2.5 and a small toss up; a
  foe caught by more than one burst takes 25% more from each burst after the first. Cooldown 80. Instant, no ticker.
- Held model `ringmaster_cane` in `wf/held3d.py`, sprite `ringmaster_cane` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, firework rockets, a cake,
gold ingots, lanterns, a bell, an 8% enchanted golden apple. Quest: `explorer/boss_ringmaster`.

**Concept.** A tall, thin brass showman of the abandoned steam carnival, 3.6 blocks (hitbox 1.2 x 3.6) plus his hat:
- a towering black silk top hat with a red band, a brass buckle, a cog on its side and a steam whistle on the crown
  (steam puffs from it in game), lifted and thrown in his moves (`hat`);
- a grinning lacquered brass face: arched brows, rosy cheeks, a wide white grin, a curled handlebar moustache, an amber
  monocle on a chain (glow layer, with his left eye);
- a high collar, a black bow tie over a white shirt front, a gold brocade waistcoat with brass buttons, a watch chain
  and fob; a scarlet tailcoat piped in gold with lapels and long swallow tails (`tails`), brass cog epaulettes fringed in
  gold; a wind-up key turning in his back (`key`, idle loop);
- long legs in black-and-grey striped trousers, white spats over black boots;
- asymmetry: the right white-gloved hand holds a black telescoping cane with a gold knob and brass ferrule (scaled to
  1.9x in the cane whip), the left a brass juggling bomb with a lit fuse (glow), tossed in the idle loop.

**Stats.**
- 640 health, armour 11, toughness 4, attack 14, poise 115, speed 0.28, knockback resistance 1.0, step 1.5.
- No fall damage, red bar.
- Phase 2 at 65% (roar, +10% speed, `ringmaster_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `finale` once (guarded 64 ticks). Range 999 / weight 0 keeps it out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| cane | 1-3 | 14 / 16 / 14 | 0-6.5 | Arc drawn gold (±75°, 5.5; red from wind-up 9) as the cane telescopes out. Impact: whip sweep, 12, push 0.6. Active 1 he turns up to 20°, a red line (7, half width 0.9) is drawn active 1-7; active 8 the crack: 10, lift 0.25. P2: 30% chains flourish (target past 6) or juggle. |
| juggle | 1-3 | 20 / 20 / 14 | 4-22 | `scaledCount(3)` bombs (+2 in P2, at most 6): circles r 2.2 on the target, the other players, then 3-7 round the target, 3.5 apart, on open ring, drawn gold from the start. At impact one bomb leaves every 5 ticks and flies 16 (its circle red for the last 10): 9, push 0.3, lift 0.3. |
| hat | 1-3 | 18 / 30 / 14 | 3-18 | A line (half width 1.2) along his facing over open ring to the target + 2 (at most 12), drawn white, red from wind-up 12. At impact the hat sails out at 0.8 a tick and back: 8 and Slowness I 1 s, once per pass. |
| flourish | 1-3 | 16 / 8 / 16 | 6-16 | A lane (half width 1.2) over open ring with 4 blocks of headroom to the target + 2 (at most 12), drawn gold while he turns 4°/tick until wind-up 10, then red. Active 0-5 he lunges down it (`move`, collisions kept): 13, push 0.7, lift 0.2 to whoever is within 1.6 of him (once). |
| performers | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Clockwork spiders and rust mites alternately, `scaledCount(2)`, at most 3 alive, on open ring 3.5 from him; tagged minions, discarded on death, removal and reset. |
| carousel | 2-3 | 24 / 80 / 16 | 0-30 | Cooldown 420. Six fire posts (eight in phase 3) on a circle of 12 (at most ringR - 3) round the ring's centre, drawn as gold rings r 1.5 with arrows the way they will turn (red from wind-up 16; the direction alternates). Active: they turn at 1.2°/tick (0.25 blocks a tick): 6, fire 2 s, lift 0.1 within 1.5 of a post, at most every 15 ticks. Inside r 10.5 and outside r 13.5 are safe. |
| finale | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; confetti rings converge on him, the hat rises on steam. Impact: a confetti ring runs to the ring's edge (10, lift 0.3, jump it: it hits only who stands within 0.6 of the floor), +12% speed (`ringmaster_finale`), the hazards start (spotlight 40 ticks later, confetti 60). |

**The Grand Finale (phase 3).** Confetti drifts down over the ring.
- *Spotlight*: every 240 ticks x `cooldownScale()` (at least 140, counted from the end of the last one) a spotlight
  picks the next player in turn and starts 7 blocks from them toward the centre (or at the centre): a white circle
  (r 2) under a beam of particles from the great chandelier (23 over the centre). For 100 ticks it follows its player at
  0.17 blocks a tick (slower than walking) over open ring within ringR - 1; from tick 20, every 20 ticks it flashes:
  4 and Glowing 2 s to whoever stands in it. Then it holds for 20 ticks drawn red and blasts: 9 and lift 0.3. If its
  player leaves or dies it holds and blasts where it is.
- *Confetti charges*: every 100 ticks x `cooldownScale()` (at least 60), `min(5, scaledCount(2) + 1)` circles (r 2): one
  under the target, the rest 3-9 from it, 3.5 apart, on open ring. Drawn 30 ticks (red the last 10, sparks rising, a
  fuse hiss at 20), then 7 and lift 0.3.
- Both wait while `finale` runs or he is guarded; the posts of the carousel become eight.

**Temporary blocks.** The only blocks he places are the spotlight's light blocks (`minecraft:light`, level 15): one at
a time, in the air cell over the spot (only where it is air), moved with the beam (the old one put back, only where
it is still a light block). They go back when the spotlight ends, when the fight resets (phase back to 1), the arena
empties, he dies or is removed, and on the first tick after a reload (saved in `RingmasterLights`). His performers are
discarded on death, removal and reset.

**Fair edges.** The ring is walled by the curb and the benches (no drop). His `strike` caps pushes at 1.0 and lift at
0.45; a push is dropped when a probe 1.5 blocks along it finds no open ring (a king pole, the benches, a tunnel), and
then the lift is capped at 0.2. Bombs, the hat's line, the lane, the posts, the spotlight and the charges only use open
ring. Every hit is drawn on the floor first; the largest single hit is 13 (the flourish).

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the spotlight and confetti timers use `cooldownScale()`), compressed wind-ups. Bombs,
performers and confetti charges scale with `scaledCount`; bombs land on every player too; the spotlight takes the
players in turn.

Previews:
- `python3 tools/gen_models.py --preview --only ringmaster` writes `build/previews/models/ringmaster.png`.
- Held cane: `python3 tools/art_sheet.py --kind held --only ringmaster_cane`.

## 41. Champion of the Storm Spire: The Tesla Archon (L'Archonte Tesla)
Files:
- `tools/wf/mobs/tesla_archon.py`: model `tesla_archon` (98 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/TeslaArchon.java`: the moveset.

There is no lair module. The arena is the open crown platform on top of the 110-high spire: `BOSS` in
`tools/wf/structures/storm_spire.py` (`arena()`), seal at (0, 110, -8), radius 15; a disc of radius 16.4 (feet 111),
a brass railing on its rim with copper posts and lightning rods every 7th cell, open only at the grace turret's door
(south), the vault hatch (sealed bars) 6 north of the centre, the corona ring of rods and end rods 17-20 overhead on
six legs. The Tesla Archon replaces the borrowed Gryphon Knight there; the Gryphon Knight keeps its own lair and
`BOSS_HOME` (`sky_island`). `BOSS_HOME` is `storm_spire`. "Open platform" in the class means floor within 0.6 of the
seal's level (1.6 if the floor round the seal is rough: a command spawn) with two blocks of air over it, inside the
arena radius.

Reward: `remembrance_tesla_archon` forges the **Coil-Staff of the Tesla Archon** (`tesla_coilstaff`, LITHITE 8 / -2.8).
- It has a new ability shape, **TESLA**, in `BossWeaponItem`: a bolt runs along the aim (up to 14 blocks, walls stop
  it) to the first foe within 1 of its path; a visual-only lightning bolt falls on that foe (no fire, no block touched);
  then the arc jumps on to up to 3 more foes, each the nearest within 5 of the last, every jump for 80% of the one
  before (power 10, knockback 0.2, flag `slow`). Cooldown 80. Instant, no ticker.
- Held model `tesla_coilstaff` in `wf/held3d.py`, sprite `coil_staff` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, copper blocks, lightning
rods, redstone, glowstone dust, end rods, an 8% enchanted golden apple. Quest: `explorer/boss_tesla_archon`.

**Concept.** A mad electrical engineer who climbed into his own coil suit and never came out, 3.4 blocks (hitbox
1.4 x 3.4):
- a riveted copper cuirass with a glowing aether coil-core in the chest, a gauge, a small chest coil, a brass gorget;
  the scorched tails of a white lab coat behind; copper greaves in brass bands, iron boots on rubber soles;
- a pale gaunt head with a manic grin, a bushy grey moustache, brass goggles with glowing lenses and wild white hair
  standing up from the static (`hair`, scaled up when he charges);
- a tesla coil on his back (`pack`, `coil`): an iron frame, two capacitor jars, a fat copper winding on an insulator
  foot, a brass toroid (`torus`, turning in the idle loop, spun and scaled up in the big moves) with a spark ball;
  two small coils on the shoulders (`pcoil_?`);
- asymmetry: the RIGHT arm is a massive copper gauntlet, the forearm wound with coil, three glowing electrode prongs on
  the knuckles and a black cable into it; the LEFT hand holds the coil-staff (iron shaft, copper winding, insulator
  discs, brass prongs round a glowing orb).

**Stats.**
- 700 health, armour 12, toughness 5, attack 14, poise 120, speed 0.27, knockback resistance 1.0, step 1.5.
- No fall damage, blue bar.
- Phase 2 at 65% (roar, +10% speed, `tesla_archon_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `overload` once (guarded 64 ticks), then every 260 ticks x `cooldownScale()` (at
  least 160, the first 60 after the overload) `arcsweep`. Range 999 / weight 0 keeps the scheduled moves out of the
  picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| arcpunch | 1-3 | 14 / 10 / 14 | 0-5.5 | Arc drawn blue (±50°, 4.5): 12, push 0.6. The nearest struck becomes the chain's head; the arc picks the nearest other victim within 6 (P2: a second jump from that one). Active 0-7: a crackling line between them and a ring (r 1, red from 4) under the next; jump i fires at active 7 + i: 7 (P2 9), no push, only if the next is still within 6 (step away). P2: 25% chains magnet (close) or arcline. |
| orb | 1-3 | 20 / 6 / 14 | 4-24 | One orb (P2 two, ±25°) leaves at chest height, drifting 0.13 a tick toward the target (turning up to 4° a tick), turned back inside radius - 1; its circle (r 2.2) drawn under it. Within 1.8 of a victim (or after 140 ticks) it stops, the circle is red for 12 ticks, then it bursts: 9 in r 2.2, lift 0.2. |
| coilslam | 1-3 | 22 / 8 / 16 | 0-7 | Circle r 3.5 round him (red from wind-up 14). Impact: 14 in r 3.5 (push 0.8, lift 0.3) and a wave to 8 (P2 11): 7, jump it. |
| arcline | 1-3 | 24 / 12 / 14 | 3-20 | A line 18 long (half width 1.2); he turns 6°/tick toward the target until wind-up 14, then it locks red. Impact: 13, push 0.3. P2: two side lines at ±30° drawn red from the lock, discharging at active 6: 10. |
| corona | 2-3 | 30 / 40 / 16 | 0-30 | Circles (r 2) where the target and up to 2 other players stand (fixed, inside radius - 2), the rest random open platform, 3.5 apart, `min(7, 3 + scaledCount(1))` in all; gold from the start, the corona ring overhead charging (sparks running round it, sparks rising from his coil). Circle k strikes at active 4 + 6 k (red the last 10 ticks): a visual-only lightning bolt and 10 in r 2, lift 0.25, no push. |
| magnet | 2-3 | 20 / 36 / 16 | 0-14 | Copper rings close on him in the wind-up. Active 0-27: everyone within 12 (not within 1.5) gets +0.04 a tick toward him, horizontal speed capped at 0.28 (they can walk out); circle r 3.5 round him, red from active 16. Active 28: 12 in r 3.5, lift 0.3, no push. |
| overload | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks: arcs spiral in, rings grow round him. Impact: a wave to 12 (10, jump it), +10% speed (`tesla_archon_overload`), a visual bolt on him, the sweep timer at 60. Sparks crackle off him from then on. |
| arcsweep | 3 | 30 / 120 / 20 | scheduled | No gravity; during the wind-up he floats (smoothstep) to 2.5 over the centre and holds there through the active frames. `min(4, 2 + scaledCount(1))` beams, evenly spread from a random bearing, radial from 1 out to the radius at ankle height, drawn from the start (red from wind-up 20, gold marks beside them on the side they will turn to); the direction alternates every sweep. Active 0-119 they turn at 3° a tick (0.26 blocks a tick at r 5, 0.8 at the rim): 7 and lift 0.25, at most every 10 ticks, to whoever is within 0.6 (+ half width) of a beam with feet within 0.6 of the floor: jump them. Gravity back at active 119 (he drops in the recovery). |

**No blocks.** He places and breaks no blocks. The lightning is visual only (`setVisualOnly`, no fire, no vanilla
damage) and always lands on floor spots, never on a rod; orbs, beams, the corona and the chain are particles and hit
checks. Nothing to restore. His gravity comes back whenever no arc sweep runs (`bossTick`: a stagger, a reset, a
reload), on death and on reload.

**No deaths off the crown.** His `strike` caps pushes at 0.8 and lift at 0.4. A push is kept only when open platform
lies 1.5 and 3 blocks along it within radius - 1.5 of the centre; otherwise it becomes a push toward the centre (at
most 0.5) and the lift is capped at 0.2. The corona, magnet, beams, orbs and chain push nothing; the engine's phase-2
roar shove is cut to 30% and corrected the same way. The magnet's pull draws toward him, never outward.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the sweep timer uses `cooldownScale()`), compressed wind-ups. Corona circles and sweep
beams scale with `scaledCount`; the corona marks every player (up to 3); the arc punch's chain only exists with a
second fighter.

Previews:
- `python3 tools/gen_models.py --preview --only tesla_archon` writes `build/previews/models/tesla_archon.png`.
- Held coil-staff: `python3 tools/art_sheet.py --kind held --only tesla_coilstaff`.

## 42. Champion of the Leviathan Lighthouse: The Drowned Lightkeeper (Le Gardien noyé du phare)
Files:
- `tools/wf/mobs/drowned_keeper.py`: model `drowned_keeper` (53 cubes, 128x128).
- `src/main/java/com/brasshaven/entity/boss/DrownedKeeper.java`: the moveset.

There is no lair module. The arena is the lantern room at the top of the tower (`tools/wf/structures/
leviathan_lighthouse.py`, `arena()`, seal at (0, 113, 6), radius 16): a deck of radius 16.5 (feet 114) inside the
glazing (16.5-17.5, brass astragals), about 14 blocks of air up to the cupola's spring and the great lamp hung ~17 over
the centre; two glazed doorways (north and south) open onto the lamp gallery outside (to 20.5, a railing on its rim);
the hatch house (the mist) on the north rim, the sealed bars of the hoard in the deck. `BOSS` there is
`brasshaven:drowned_keeper` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island
are untouched). `BOSS_HOME` is `leviathan_lighthouse`. "Open deck" in the class means floor within 0.6 of the seal's
level (1.6 if the floor round the seal is rough: a command spawn) with two blocks of air over it, within 16 of the
centre (`roomR()`): the glazing, the hatch house and the gallery are never open deck.

Reward: `remembrance_drowned_keeper` forges the **Lightkeeper's Harpoon** (`lightkeeper_harpoon`, LITHITE 8.5 / -2.8).
- It has a new ability shape, **LANTERN**, in `BossWeaponItem`: the harpoon hurled along the aim on its chain (up to
  14 blocks, walls stop it) bites the first foe for the power (10) and hauls it back toward the wielder; where it bit
  the lantern flares (particle END_ROD): every other foe within 4 takes half the power, and all of them get Blindness
  3 s and Glowing 5 s (flag `blind`). Cooldown 80. Instant, no ticker.
- Held model `lightkeeper_harpoon` in `wf/held3d.py`, sprite `lightkeeper_harpoon` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, prismarine crystals, sea
lanterns, nautilus shells, iron chains, lanterns, a 10% heart of the sea, an 8% enchanted golden apple. Quest:
`explorer/boss_drowned_keeper`.

**Concept.** The old keeper of the light, drowned in a storm and brought back fused with the great clockwork lens,
3.4 blocks (hitbox 1.3 x 3.4):
- a long faded-mustard oilskin coat streaked with weed, a shoulder cape and a turned-up collar, the front skirts and
  the back panel swinging (`skirt_f`, `skirt_b`), kelp hanging from the hem and the sleeves; oilskin trousers into
  barnacled rubber sea boots;
- the coat hangs open on a ribcage of barnacled bone, and in it, for a heart, a brass storm lantern burning amber
  (`heart`, glow layer, pulsing in the idle loop, flaring in the big moves);
- a drowned grey-green face with deep sockets and pale glowing eyes (glow), a long white beard threaded with kelp, a
  sou'wester with its long back flap;
- the great Fresnel lens on his back (`lens`): a brass-ringed disc of concentric glass prisms (glow) on a clockwork
  drive, rising behind his head like a halo and turning in the idle loop; it tears up off his back in the overload;
- asymmetry: the right hand holds a long whaling harpoon (ash shaft, a chain wound on, a barbed iron head), the left a
  whale's curved jawbone worn as a club (`jaw`).

**Stats.**
- 680 health, armour 12, toughness 4, attack 14, poise 120, speed 0.27, knockback resistance 1.0, step 1.5.
- No fall damage, yellow bar.
- Phase 2 at 65% (roar, +10% speed, `drowned_keeper_wrath`; the engine's roar shove is cut to 30% and dropped where it
  would leave open deck). Phase 3 at 30%, driven by the class like the Chained Jailer: when he is free he chains
  `overload` once (guarded 64 ticks), then `slam` every 160 ticks x `cooldownScale()` (at least 100, the first 80 after
  the overload, never while a flash is being warned). Range 999 / weight 0 keeps the scheduled moves out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| thrust | 1-3 | 14 / 6 / 14 | 0-6.5 | He turns 8°/tick until wind-up 9; a line ahead (6, half width 1.0) drawn gold, red from 9. Impact: 12, push 0.5 along the line. P2: 30% chains throw (target past 6) or whirl. |
| throw | 1-3 | 18 / 20 / 14 | 5-16 | A line (half width 1.0) along his facing over open deck to the glazing (at most 16), drawn white while he turns 5°/tick until wind-up 12, then red. Impact: the harpoon runs down it at 1.2 blocks a tick, its chain drawn to his hand; the first player within reach takes 9 and Slowness I 1 s and is hauled in at 0.6 a tick (at most 14 ticks) until 2.5 from him. |
| whirl | 1-3 | 18 / 16 / 14 | 0-7 | A ring r 6.5 round him drawn gold (red from wind-up 12), the inner circle r 2 white. Active 0-15 the harpoon turns once round him on its chain (22.5°/tick): 10, push 0.6, once, to whoever stands between r 2 and 6.5 within ±15° of it. |
| sweep | 1-3 | 24 / 40 / 16 | 0-30 | Cooldown 200. The half of the room centred on the target is drawn: its edge (a line through the centre), arcs at r 5, 10 and the rim, arrows the way the beam will turn (direction random), gold, red from wind-up 16. Active: the lamp's beam (particles from the lamp to the deck) turns through it at 4.5°/tick: 8 and Blindness 1.5 s, once, to each player it crosses (hit by angle progress, so it cannot skip anyone). The other half and the circle r 1.5 under the lamp are safe. |
| surge | 2-3 | 22 / 40 / 16 | 0-30 | Cooldown 320. The edge of the room opposite the target (a chord) drawn sea blue with foam arrows toward the target, red from wind-up 14. Impact: three waves 14 ticks apart roll across the room at 0.7 a tick: 8, push 0.4 along, lift 0.3, once per wave, to whoever stands within 0.8 of the front with feet within 0.6 of the floor (jump them). |
| call | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Drowned marines and tide wraiths alternately, `scaledCount(2)`, at most 3 alive, on open deck 3.5 from him; tagged minions, discarded on death, removal and reset. |
| overload | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks: rings of light converge on him, the lens blazes over his head. Impact: a ring of light runs out to the rim (10, lift 0.3, jump it), +8% speed (`drowned_keeper_overload`), the Lamp Overload starts (first flash 60 ticks later). |
| slam | 3 | 22 / 10 / 18 | scheduled | A circle r 3.5, 3.5 ahead of him on open deck, drawn gold while he turns 4°/tick until wind-up 12, red from 14, with a white ring r 9 for the shockwave. Impact: 15, push 0.6, lift 0.4 inside, then a ring runs out to 9 (6, lift 0.3, jump it). |

**The Lamp Overload (phase 3).** Every 40 ticks everyone near the room gets Darkness 3.5 s (no particles). The lamp
shines in three lit sectors of 60° with 60° of shadow between them, turning all the time at 0.8°/tick (0.2 blocks a
tick at 14 from the centre, slower further in; the direction flips after every flash); the circle r 2 under the lamp
is always lit. Their edges are drawn faintly (every 6 ticks). Every 150 ticks x `cooldownScale()` (at least 100) a
flash is warned for 30 ticks: edges drawn densely gold with light across the sectors, red for the last 10 (a chime at
20); then the lamp flashes: 9 and Blindness 1.5 s to every player in the light. The timer waits while the overload
runs or he is guarded.

**No blocks.** He places and breaks no blocks; the beam, the waves, the sectors and the chain are particles and hit
checks. Nothing to restore. His crew is discarded on death, removal and reset.

**Fair edges.** The deck is walled by the glazing; the doorways lead to the gallery and its rail. His `strike` caps
pushes at 1.0 and lift at 0.45; a push is dropped when a probe 1.5 blocks along it finds no open deck (the glass, the
hatch house, the gallery), and then the lift is capped at 0.2. The haul pulls toward him (always inside). Every hit is
drawn first; the largest single hit is 15 (the slam). Blindness lasts at most 1.5 s from his moves.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the flash and slam timers use `cooldownScale()`), compressed wind-ups. His crew scales
with `scaledCount`; the sweep, waves and flashes reach every player.

Previews:
- `python3 tools/gen_models.py --preview --only drowned_keeper` writes `build/previews/models/drowned_keeper.png`.
- Held harpoon: `python3 tools/art_sheet.py --kind held --only lightkeeper_harpoon`.

## 43. Champion of the Brass Caravanserai: The Brass Merchant Prince (Le Prince marchand de laiton)
Files:
- `tools/wf/mobs/merchant_prince.py`: model `merchant_prince` (85 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/MerchantPrince.java`: the moveset.

There is no lair module. The arena is the sunken auction pit under the great dome (`tools/wf/structures/
brass_caravanserai.py`, `pit()`, seal at (0, -9, -16), radius 15): a flat floor of radius 17.5 (feet -8) of brass,
azure and polished stone, two tiers of bidders' steps (17.5-19 at +1, 19-20.5 at +2), the pit wall to 22.6 with iron
grilles on its rim, the north aisle (the mist, the auctioneer's lectern and the bell podium beside it) and the south
aisle to the treasury's sealed bars, 80 blocks of headroom; the dome's eight piers stand at radius 24 on 22.5° + 45° k.
`BOSS` there is `brasshaven:merchant_prince` (it replaces the borrowed Gryphon Knight, whose own home, quest and seal
on the sky island are untouched). `BOSS_HOME` is `brass_caravanserai`. "Open floor" in the class means floor within 0.6
of the seal's level (1.6 if the floor round the seal is rough: a command spawn) with two blocks of air over it, within
`pitR()` (seal radius + 2, between 14 and 17: 17 here) of the centre: the steps, the aisles and the podium never are.

Reward: `remembrance_merchant_prince` forges **The Merchant Prince's Scimitar** (`prince_scimitar`, LITHITE 8.5 / -2.4).
- It has a new ability shape, **CRESCENT**, in `BossWeaponItem`: a gilded crescent flies along the flat aim (up to 12
  blocks, walls stop it), hitting every foe within 1.8 of its path once for the power (10, knockback 0.4); then the
  appraisal: the struck foe with the most health left takes a gold-bar slam for half the power. Flag `weak`, particle
  WAX_ON, cooldown 80. Instant, no ticker.
- Held model `prince_scimitar` in `wf/held3d.py`, sprite `prince_scimitar` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, gold ingots, gold blocks,
raw gold, golden horse armour, orange carpets, an 8% enchanted golden apple. Quest: `explorer/boss_merchant_prince`.

**Concept.** The decadent prince who bought the city, carried on his own clockwork palanquin, 3.6 blocks (hitbox
1.6 x 3.6) plus the plume:
- the palanquin (`car`): a brass-bound mahogany coffer heaped with gold coins, a crimson cushion with a gold fringe,
  gilded finials with rubies at its corners, a lens lock plate; it scuttles on four splayed brass legs (`thigh_*`,
  `shin_*`: cog hip joints, rod shins, iron feet);
- the prince sits cross-legged on the cushion: azure silks plated with rows of brass scales, a crimson sash round a
  full belly, a jewelled collar (ruby, sapphire, emerald), brass pauldrons, gold slippers;
- a heavy-browed face with kohl-dark eyes glinting gold (glow), a hooked nose, a curled moustache, an oiled black
  beard trimmed to a point with a gold bead, gold earrings; a towering cream turban wound with gold bands, a great ruby
  in a gold setting (glow) and a white plume;
- asymmetry: a broad steel scimitar with a gold back, a sapphire pommel and a gold crossguard in the right hand;
  jewelled rings on the left hand; behind him a great brass mechanical arm on a mast from the coffer (`mast`,
  `mech_up` with a piston, `mech_fore`, `claw`), its three-fingered claw clutching a gold bar over his left shoulder
  (turned slowly in the idle loop).

**Stats.**
- 660 health, armour 11, toughness 4, attack 14, poise 115, speed 0.27, knockback resistance 1.0, step 1.5.
- No fall damage, yellow bar.
- Phase 2 at 65% (roar, +10% speed, `merchant_prince_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `auction` once (guarded 64 ticks); `dash` is chained from `bossTick` too. Range
  999 / weight 0 keeps both out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| slash | 1-3 | 14 / 12 / 16 | 0-6.5 | Arc drawn gold (±70°, 5.5; red from wind-up 9). Impact: sweep, 12, push 0.6. Active 0 he turns up to 20°, a red line (13, half width 1.2) is drawn active 0-5; active 6 a gold crescent flies down it at 0.9 a tick: 8, lift 0.25, once each. P2: 30% chains charge (target past 6) or coins. |
| coins | 1-3 | 18 / 16 / 14 | 3-18 | Seven lanes (±40°, 14 long) fanned on his facing at the start, drawn gold, red from wind-up 12. Active 0, 5, 10 a fan of coins (one per lane, 0.8 a tick, stopped by walls): 5 to the first one each meets. P2: a fourth fan at active 15 down the six lanes between, drawn white beforehand. |
| bid | 1-3 | 16 / 40 / 14 | 3-24 | `min(3, scaledCount(1))` marks: the target, then other players. A circle (r 2.5) on each, white in the wind-up; active 0-27 it follows its player at 0.16 a tick over open floor (gold, a coin column climbing, a pling rising in pitch); 28-38 it holds red (the bar falls from 32); 39 the gold bar: 14, lift 0.35. |
| charge | 1-3 | 16 / 8 / 16 | 6-16 | A lane (half width 1.3) over open floor with 4 blocks of headroom to the target + 2 (at most 12), drawn gold while he turns 4°/tick until wind-up 10, then red. Active 0-5 he runs down it (`move`, collisions kept): 13, push 0.7, lift 0.2 to whoever is within 1.6 (once). |
| hire | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Bandit marksmen, `scaledCount(2)`, at most 3 alive, on open floor 5-9 from him; tagged minions, discarded on death, removal and reset. |
| sandstorm | 2-3 | 24 / 6 / 16 | 0-30 | Cooldown 460. The eye (r 2) on the target's spot (open floor within pitR - 3) drawn sand, red from wind-up 16, the reach (r 7) dotted. Impact: a vortex lives 140 ticks, drifting after the nearest player at 0.06 a tick; every 4 ticks a push of 0.04 in and 0.06 round to whoever is within 7 (dropped where open floor does not lie 1.5 along it; walking beats it); every 20 ticks in the eye: 3 and Slowness I 1 s. Ends if the fight resets. |
| auction | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; rings of gold and azure converge on him, the arm beats the coffer like a gavel. Impact: a gold ring runs to the pit's edge (10, lift 0.3, jump it: it hits only who stands within 0.6 of the floor), +12% speed (`merchant_prince_auction`), the hazards start (sectors 40 ticks later, dash 120). |
| dash | 3 | 16 / 46 / 14 | scheduled | Every 260 ticks x `cooldownScale()` (at least 160) when he is free. A lane (half width 1.3) over open floor to the foot of one of the eight piers (r 15 at 22.5° + 45° k; not the last one, at least 6 away, the one passing nearest the target), drawn gold, red from wind-up 10. Active 0-5, 20-25, 40-45 he runs down a lane (11, push 0.7, lift 0.2, once per dash); 6-19 and 26-39 the next lane is drawn (red from 14 / 34). |

**The Final Auction (phase 3).** Gold dust drifts down over the pit.
- *Gilded sectors*: every 180 ticks x `cooldownScale()` (at least 110, counted from the last blast) the pit is cut
  into eight 45° sectors (offset 0 or 22.5° at random); `min(4, scaledCount(2) + 1)` are chosen: the target's first,
  then others, not side by side when it can be helped. Ticks 0-19 their edges are drawn gold; at 20 their floor is
  gold-plated (temporary gold blocks) and glitters, the edges red from 40 (a fuse hiss); at 50 they detonate: 9 and
  lift 0.4 to whoever stands in a plated sector (outside r 1 of the centre), and the floor goes back.
- *Pier dash*: see `dash` above.
- Both wait while `auction` runs or he is guarded.

**Temporary blocks.** The only blocks he places are the gold blocks of the plated sectors: only on the floor layer
under the seal's level, between r 1.5 and `pitR()`, only over full plain blocks (no block entity; the seal itself is
never touched) with air above. They go back right after the blast, when the fight resets (phase back to 1), the arena
empties, he dies or is removed, and on the first tick after a reload (saved in `MerchantPrinceGold`). A block goes back
where it is still gold or was mined out during the fight. His mercenaries are discarded on death, removal and reset.

**Fair edges.** The pit is walled by the steps and the pit wall (no drop). His `strike` caps pushes at 1.0 and lift
at 0.45; a push is dropped when a probe 1.5 blocks along it finds no open floor (the steps, an aisle, the podium), and
then the lift is capped at 0.2; the vortex's drag is checked the same way. Bids, lanes, the vortex and the sectors only
use open floor. Every hit is drawn on the floor first; the largest single hit is 14 (the bid's bar).

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the sector and dash timers use `cooldownScale()`), compressed wind-ups. Bids, mercenaries
and sectors scale with `scaledCount`; the vortex follows the nearest player.

Previews:
- `python3 tools/gen_models.py --preview --only merchant_prince` writes `build/previews/models/merchant_prince.png`.
- Held scimitar: `python3 tools/art_sheet.py --kind held --only prince_scimitar`.

## 44. Champion of the Mycelium Monastery: The Mycelium Abbot (L'Abbé du Mycélium)
Files:
- `tools/wf/mobs/mycelium_abbot.py`: model `mycelium_abbot` (87 cubes, 256x128).
- `src/main/java/com/brasshaven/entity/boss/MyceliumAbbot.java`: the moveset.

There is no lair module. The arena is the round hall under the cap's dome (`tools/wf/structures/mycelium_monastery.py`,
`cap_and_arena()`, seal at (0, 84, -28), radius 16): a flat floor of radius 22 (feet 85) of brass, parquet, stem and
mycelium round a gilded centre, a shroomlight ring at 11, braziers at 20.8, the brass ring wall to 24.5, six pore
windows, a gill-ribbed vault with the glass oculus at its crown. `BOSS` there is `brasshaven:mycelium_abbot` (it
replaces the borrowed Gryphon Knight, whose own home, quest and seal on the sky island are untouched). `BOSS_HOME` is
`mycelium_monastery`. "Open floor" in the class means floor within 0.6 of the seal's level (1.6 if the floor round the
seal is rough: a command spawn) with two blocks of air over it, within `floorR()` (seal radius + 3, between 12 and 19:
19 here) of the centre: the braziers and the ring wall never are. Distinct from the Spore Alchemist (red agaric,
green flasks, bogged): brown cap, violet spores and cyan bioluminescence, censer clouds, rooting tendrils, bell monks.

Reward: `remembrance_mycelium_abbot` forges **The Abbot's Crozier** (`abbot_crozier`, LITHITE 8 / -2.8).
- It has a new ability shape, **MYCELIUM**, in `BossWeaponItem`: three mycelium tendrils race along the ground in a
  fan round the flat aim (±20°, up to 9 blocks, walls stop each); every foe a tendril touches is hit once for the power
  (9, no knockback) and rooted (Slowness IV 2 s); the wielder heals 1 per foe rooted (at most 4). Flag `poison`,
  particle SPORE_BLOSSOM_AIR, cooldown 80. Instant, no ticker.
- Held model `abbot_crozier` in `wf/held3d.py`, sprite `abbot_crozier` in `wf/itemart_shapes.py`.

Loot (`gen_data.py`): map fragments, emeralds, experience bottles, golden apples, diamonds, mycelium, shroomlights,
brown and red mushrooms, spore blossoms, iron chains, an 8% enchanted golden apple. Quest: `explorer/boss_mycelium_abbot`.

**Concept.** A steam monk grown into the fungal network, 3.4 blocks (hitbox 1.4 x 3.4) plus the crozier:
- an umber habit (weave and folds) with a brass-trimmed band, its skirt eaten into mycelium at the hem, threads to the
  floor and a `trail` of felt tendrils behind him; a hempen rope belt with tails, a dark scapular with a brass sigil;
- a capelet of violet-white mycelium felt, three little glowing cyan mushrooms sprouting from it; brass censer chains
  crossed over the chest (`sash`) with a clasp; on his back a brass reliquary-boiler with a cyan lens and a chimney
  (white steam in the ambience);
- a gaunt grey-green face, glowing cyan eyes (glow), a mycelium beard with caught spores (glow), a felted cowl; the
  hood grown into a broad brown mushroom cap (`cap`, 18 wide, stepped dome, cream specks) whose gills glow cyan at the
  rim (glow);
- asymmetry: the crozier in the right hand (dark wood, brass bands and knop, the `crook` curling forward with a thread
  off its tip, a glowing cyan mushroom on its crown); the brass censer on its `chain` from the left hand, spore-light in
  its vents (turned in the idle loop).

**Stats.**
- 650 health, armour 10, toughness 4, attack 13, poise 110, speed 0.25, knockback resistance 1.0, step 1.25.
- No fall damage, purple bar.
- Phase 2 at 65% (roar, +10% speed, `mycelium_abbot_wrath`). Phase 3 at 30%, driven by the class like the Chained
  Jailer: when he is free he chains `communion` once (guarded 64 ticks); `burrow` is chained from `bossTick` too. Range
  999 / weight 0 keeps both out of the picker.

| Move | Phase | Wind-up / active / recovery | Range | What it does |
|---|---|---|---|---|
| crozier | 1-3 | 14 / 14 / 16 | 0-6.5 | Arc drawn in spores (±70°, 5.5; red from wind-up 9). Impact: sweep, 12, push 0.6. Active 0 he turns up to 20°; a red line (7.5, half width 1.2) is drawn active 0-9; active 10 the overhead slam down it: 13, lift 0.35. P2: 30% chains crook (target past 5) or censer. |
| censer | 1-3 | 18 / 16 / 14 | 0-9 | An arc (±60°, 7.5) on his facing at the start, drawn in spores, red from wind-up 12. Active 0-14 every 2 ticks the censer sweeps across (+60° to -60°) and leaves spore clouds (r 1.7) on open floor at 2.5 and 5 along the swing; each hangs 40 ticks (P2 60): every 10 ticks inside, 2, Nausea 3 s, Poison I 2.5 s. |
| tendrils | 1-3 | 26 / 10 / 14 | 0-24 | A circle (r 2) on open floor under each player at the start (at most 4), plus 2 near them in P2 (3 apart), drawn in spores, red from wind-up 16. Impact: 10, lift 0.3 and Slowness IV 1.5 s (rooted) to whoever stands in one. |
| crook | 1-3 | 16 / 8 / 16 | 3.5-10 | A line (9, half width 1) drawn in spores while he turns 4°/tick until wind-up 10, then red. Impact: 7, lift 0.1, and a pull toward him of 0.18 per block beyond 2 (at most 1.0; dropped where open floor does not lie 1.5 along it). |
| pods | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 360. `min(4, scaledCount(2) + 1)` spots on open floor 4-9 from a player, never within 2.5 of one, 3 apart: a cyan circle (r 1) and the burst's reach (r 3.5) dotted. Impact: a red mushroom block in each air cell (nobody in it). Each pod: its reach drawn every 10 ticks (every 4, red, the last 30) with a swelling hiss; at 100 ticks it bursts (8, push 0.4, lift 0.3, Poison I 3 s within 3.5) and goes. Broken earlier, it fizzles. |
| monks | 2-3 | 20 / 10 / 16 | 0-30 | Cooldown 600. Bell monks, `scaledCount(2)`, at most 3 alive, on open floor 5-9 from him; tagged minions, discarded on death, removal and reset. |
| communion | 3 (once) | 40 / 20 / 20 | scheduled | Guarded 64 ticks; rings of spores and cyan close in on him. Impact: a ring of mushrooms blooms out to the floor's edge (10, lift 0.3, jump it: it hits only who stands within 0.6 of the floor), +12% speed (`mycelium_abbot_communion`), the hazards start (fairy rings 60 ticks later, burrow 100). |
| burrow | 3 | 20 / 40 / 16 | scheduled | Every 240 ticks x `cooldownScale()` (at least 150) when he is free and no fairy ring runs. Guarded from the start; he sinks (wind-up), hidden (invisible, untouchable) from wind-up 19. A ring (r 2.5) on open floor at the target's spot hunts it at 0.18 a tick active 0-19 (spores), holds red 20-29; active 30 he bursts up in it: 14, push 0.8, lift 0.5, and a mushroom ring blooms from there (to 9, 0.45 a tick, 7, jump it); active 38 a second one. Never stays hidden outside the move. |

**Communion (phase 3).** Spore blossoms drift down from the dome.
- *Fairy rings*: every 220 ticks x `cooldownScale()` (at least 120, counted from the last ring) a ring gathers at the
  arena's centre for 30 ticks (cyan, red the last 10), then three mushroom rings bloom out to the floor's edge 12 ticks
  apart (0.4 a tick, 7 each, jump them). They wait while `communion` or `burrow` runs or he is guarded.
- *Burrow*: see above.

**Temporary blocks.** The only blocks he places are the pods: red mushroom blocks, only in air cells on open floor
with nobody in them (the floor itself is never touched). A pod goes when it bursts, when a player breaks it, when the
fight resets (phase back to 1), the arena empties, he dies or is removed, and on the first tick after a reload (saved in
`MyceliumAbbotPods`). A cell is cleared only where it is still a red mushroom block. His monks are discarded on death,
removal and reset.

**Fair edges.** The floor is walled by the ring wall (no drop). His `strike` caps pushes at 1.0 and lift at 0.5; a
push is dropped when a probe 1.5 blocks along it finds no open floor, and then the lift is capped at 0.2; the crook's
pull is checked the same way. Marks, clouds, pods and the hunting ring only use open floor. Every hit is drawn on the
floor first; the largest single hit is 14 (the burrow's emergence). Nausea lasts 3 s at most and is refreshed only
while standing in a cloud.

**Co-op and NG+** come from the engine (`BossDifficulty`, `BossCycles`): health, damage (every hit goes through
`strike`), poise, cooldowns (the burrow and fairy-ring timers use `cooldownScale()`), compressed wind-ups. Pods and monks
scale with `scaledCount`; tendrils mark every player.

Previews:
- `python3 tools/gen_models.py --preview --only mycelium_abbot` writes `build/previews/models/mycelium_abbot.png`.
- Held crozier: `python3 tools/art_sheet.py --kind held --only abbot_crozier`.

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

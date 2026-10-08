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

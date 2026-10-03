# Wayfarers — boss guide (Elden Ring style)

Each great structure ends in a boss fight that players remember. A boss is three things, all made here
without launching the game:

1. a **3D model with animations**: `tools/wf/mobs/<id>.py`, written with the DSL in `tools/wf/models.py`
   and previewed by `tools/wf/model_render.py`;
2. a **moveset**: `src/main/java/com/wayfarers/entity/boss/<Class>.java`, extending
   `com.wayfarers.boss.WayfarerBoss`;
3. a **lair**: the descent and the arena in the structure, written in its own module
   `tools/wf/structures/lair_<id>.py` and called from the structure builder.

The finished example to copy is the Drowned Warden: `tools/wf/mobs/drowned_warden.py` and
`src/main/java/com/wayfarers/entity/DrownedWarden.java`. Its arena is in `tools/wf/structures/citadel.py`,
in `arena()` and `arena_mist()`.

## 0. What you may edit
- **Yours:** `tools/wf/mobs/<id>.py`, `src/main/java/com/wayfarers/entity/boss/<Class>.java`,
  `tools/wf/structures/lair_<id>.py`, plus the few lines in your structure's builder that call your lair.
  The entity is already registered, with its name, spawn egg, loot table and `/wayfarers boss <id>` demo
  command. Its hitbox comes from `WIDTH`/`HEIGHT` in your class.
- **Never edit shared files**, because other builders work in parallel: `ModEntities`, `ModItems`,
  `content.py`, `gen_*.py`, `mobs/__init__.py`, `WayfarerBoss`, `BossAttack`, `WayfarersClient`, and
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
- **Seal.** `bp.boss_seal(x, y, z, "wayfarers:<id>", radius)` at the centre, on the floor level. The boss
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

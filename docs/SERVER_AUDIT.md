# Wayfarers — server-readiness audit

Scope: every client → server packet, every server action a player can trigger (blocks, items, menus, commands),
duplication paths, multiplayer sync, server-thread hot paths, memory, config, stability. Target: a public server
with many players, Minecraft 26.2, Forge 65.1.0.

Severity: **High** = exploitable by any player to harm the server or other players (crash/kick loops, lag, grief at
a distance, theft). **Medium** = exploitable with effort, or a server-wide cost a crowd can trigger. **Low** = bug,
leak or hardening with little impact.

The server options mentioned below live in `config/wayfarers-common.toml` and are described for admins (in French)
in [SERVER_ADMIN.md](SERVER_ADMIN.md).

## 1. Security and exploits

| # | Sev. | Issue | Fix | Files |
|---|---|---|---|---|
| S1 | High | **Backpack ⇄ shulker box nesting without end.** A backpack holds shulker boxes and a shulker box accepted backpacks, so a backpack of shulkers of backpacks… grew without limit: one item could exceed what a packet or a chunk can carry ("NBT bomb": kick loops for whoever holds or sees it, chunk that no longer saves). | Backpacks no longer fit in container items (`canFitInsideContainerItems() = false`: shulker boxes, bundles, our own checks) and a backpack refuses a container item that already holds a backpack (for items made before the fix). Nesting depth is now bounded (backpack → shulker → items). | `item/TravelBackpackItem.java` |
| S2 | High | **Wireless Redstone reached the whole dimension on 16 shared channels.** Anyone's transmitter switched every receiver of the same colour anywhere in the dimension (doors, breakers of other bases). | Receivers only hear transmitters within `machines.wirelessRange` (128 blocks by default, 0 = old behaviour). The screen counts only machines in range. | `block/MachineBlockEntity.java` |
| S3 | High | **Block Breaker / Block Placer ignored spawn protection and claim mods** (they act without a player, so protection mods never heard of them): a breaker against someone's wall ate it. | Machines record their owner (the player who placed them; a machine placed by a Placer inherits its owner). Breaker and Placer act as that owner: spawn protection, world border, adventure mode and Forge's `BreakEvent` / `EntityPlaceEvent` (what claim mods cancel) are asked before each block. While the owner is offline they wait. `machines.breakerEnabled`, `machines.placerEnabled`, `machines.actAsOwner`. Machines placed before the update have no owner and keep the old behaviour. | `block/MachineBlockEntity.java`, `block/MachineBlock.java`, `util/ServerGuard.java` |
| S4 | High | **Structure / Airship Compass ran an uncached structure search on the server thread.** `findNearestMapStructure` over 100 chunks (it may compute structure starts of ungenerated chunks) every 3 s per player, cached only for the exact chunk: a crowd of players walking with compasses stalled the server. | Answers shared by 4 × 4-chunk cells (search from the cell centre) and a server-wide budget of new searches (`compass.searchesPerMinute`, 30 by default); when it is used up the compass answers "still turning" instead of searching. Operator commands are not budgeted. | `util/StructureLocator.java`, `item/StructureCompassItem.java`, `item/AirshipCompassItem.java` |
| S5 | High | **Map waypoint actions were unthrottled and expensive.** Each add/edit/delete serialised every waypoint of the server (up to 10 000) to JSON on the server thread, and a change to a shared waypoint resent the whole list (up to 600 KB) to every online player. A modified client looping edits saturated CPU and bandwidth. | Token bucket per player (6 burst, 1/s), shared-waypoint broadcasts coalesced to one per second, the file is written by the map worker at most every 30 s and at each world save. | `map/MapServer.java`, `network/MapActionMsg.java` |
| S6 | Med. | **No rate limit on any client action.** A terminal click walks the whole storage network; quick-stack walks every block entity within 9 blocks; quest/skill requests rebuild snapshots; relay clicks follow up to 64 relays. | `ServerGuard.allow`: per-player token buckets on every serverbound packet and on the vanilla menu clicks that walk a network (terminal grid clicks and shift-clicks 15/s, machine buttons 10/s, store-all 1/s, container buttons 3/s, waystones 2/s, map requests 10/s, pings 1 per 2 s, skills 5/s, quests 2/s, wand mode 4/s) and on storage relay lookups. | `util/ServerGuard.java`, `network/*Msg.java`, `menu/TerminalMenu.java`, `menu/MachineMenu.java`, `block/StorageRelayBlock.java` |
| S7 | Med. | **Actions accepted from dead, spectating or disconnecting players** (warp, terminal, wand, container buttons). | `ServerGuard.canAct`: connected, alive, not a spectator. | `network/*Msg.java` |
| S8 | Med. | **Unbounded strings in serverbound packets** (`readUtf()` = 32 767 chars) in `WaystoneActionMsg` and `SkillActionMsg`. | Ids bounded to 16 / 64 chars at decode time (longer = malformed packet). `MapActionMsg` was already bounded (8 KB, 64 requests). | `network/WaystoneActionMsg.java`, `network/SkillActionMsg.java` |
| S9 | Med. | **Anyone could rename or pin every waystone** of the server (they are shared) from any waystone. | Only the waystone you stand at, unless `waystones.renameOnlyHere = false`; operators always can. | `util/Waystones.java` |
| S10 | Med. | **Waystone travel had no cooldown**: teleport spam loads chunks all over the world. | `waystones.cooldownSeconds` (5), optional `waystones.costLevels` (×2 across dimensions), `waystones.crossDimension`. Operators are exempt. | `util/Waystones.java` |
| S11 | Med. | **Waystone names and count unbounded.** A waystone item renamed by a command or another mod could carry a name longer than the 64 chars the list packet allows: an encoder exception for everyone opening the list. The list itself grew without limit. | Names cleaned (no control/formatting characters) and cut to 32; `waystones.maxTotal` (1000). | `data/WayfarersData.java`, `util/Waystones.java` |
| S12 | Med. | **Graves could be emptied by anyone.** | `graves.ownerOnlyMinutes`: only the owner (and operators) open a grave, for N minutes or always (-1, default). A grave without a recorded owner stays open to all; with a time limit, graves made before the update (no creation time) are open. | `block/GraveBlock.java`, `block/GraveBlockEntity.java` |
| S13 | Med. | **Storm Staff called real lightning**: fire, and damage to players (whatever the PvP setting), pets and villagers, also inside spawn protection. | Default: a visual bolt that hurts only monsters (same rule as every other ability, `Targets.foe`) and starts no fire. `items.stormStaffRealLightning = true` restores real lightning, refused inside spawn protection. | `item/StormStaffItem.java` |
| S14 | Med. | **Builder's Wand bypassed claims**, and its undo could remove blocks placed since by other players, at any distance. | Every placement is announced to protection mods (one refusal cancels the use); undo only within 96 blocks and where the player may break. | `item/BuilderWandItem.java` |
| S15 | Med. | **Right-click harvest ignored claims, spawn protection and adventure mode.** | Same checks as breaking the crop by hand. | `event/QolEvents.java` |
| S16 | Low | Brass Wrench sneak-use changed other players' machine settings without the protection check its other uses have. | Same `canEdit` check. | `item/BrassWrenchItem.java` |
| S17 | Low | Quick-stack deposits into any nearby chest. | `storage.quickStackRange` (8; 0 turns the button off). | `util/ContainerActions.java` |
| S18 | Low | Magnet reach fixed. | `items.magnetRange` (7; 0 disables). Known limit: the magnet also moves items dropped for another player (vanilla keeps the pick-up for them; there is no public API to read an item's target). | `item/MagnetRingItem.java` |

Checked and found sound (no change): every serverbound handler is registered with `addMain` (Forge runs it on the
server thread); menus validate with `stillValid` (vanilla re-checks it every tick, closes the menu, and refuses
clicks on an invalid menu — a broken terminal, machine or chisel table closes its screen); machine settings are
bounds-checked server-side (`MachineBlockEntity.applySetting`); talent unlocks are validated (points, parents);
operator commands are gated (`LEVEL_GAMEMASTERS`); the chisel families never mix shapes (no slab → block
conversion); graves, seals and altars are unbreakable.

## 2. Duplication audit

| # | Sev. | Path | Finding / fix | Files |
|---|---|---|---|---|
| D1 | Med. | Guild Terminal, shift-click a stack to the inventory | `Inventory.add` returns true when only part fits: the rest was neither stored back nor dropped (item loss, not a dupe). Now whatever is left goes back to the network or to the floor. | `network/TerminalClickMsg.java` |
| D2 | Med. | Sort buttons on modded containers | Sorting merged stacks without checking the container's slot limit or that the sorted list fits the slots: items could vanish in containers with small slots. Now refused when anything would not fit. | `util/ContainerActions.java` |
| D3 | Low | Insertion into containers with a lower slot limit (terminal, quick-stack, crates, machines) | `InventoryUtil.insert` now honours `Container#getMaxStackSize`. | `util/InventoryUtil.java` |
| D4 | Low | Death with more than 160 stacks (other mods' extra slots) | The grave silently dropped the rest; now it falls on the ground. | `event/GraveEvents.java`, `block/GraveBlockEntity.java` |
| D5 | Low | Vacuum Hopper experience | Clamped (no integer overflow). | `block/MachineBlockEntity.java` |

Checked without finding a dupe: terminal take/store from two players at once (all on the server thread, every
operation reads the live containers); a container broken or unloaded since the last scan (`Link.valid()` checks
`isRemoved`, which chunk unloading sets); shift-click into the network; backpack opened in hand then dropped,
swapped, thrown or moved (identity checks in the menu and `stillValid`: a dropped backpack is split off the hand, the
menu becomes invalid and refuses clicks); backpack inside itself (blocked); machine buffers and hoppers; breaking a
machine while open (`stillValidBlockEntity`); Breaker on shulker boxes / chests (drops computed once, contents spill
once); Placer (the item is consumed by the placement); chisel table (variant slots never give items; input returned
on close by the server copy only); compacting crate (one kind only, atomic take); crate insert double-click; Builder's
Wand undo (refunds only what was paid, only blocks still of the same kind and worth); quest rewards (vanilla
advancement rewards, granted once per player); waystones (no item cost to dupe); grave take (atomic swap).
Quest note: with `quests.catchUpOnJoin = true` (the co-op default) a new account receives the rewards of every quest
step already reached — on a public server, set it to false (see SERVER_ADMIN.md).

## 3. Multiplayer correctness and bandwidth

| # | Sev. | What | Before | After | Files |
|---|---|---|---|---|---|
| M1 | Med. | Shared waypoint changes | full POINTS list to every player per edit | coalesced, at most one broadcast per second; owner gets it at once | `map/MapServer.java` |
| M2 | Low | Player positions on the map | every second, to every player of the dimension, even when nothing moved | identical payloads skipped (resent every 3 s: the client forgets positions after 5 s) | `map/MapServer.java` |
| M3 | Low | Waypoint file | written (JSON of every waypoint built on the server thread) on each edit | every 30 s if changed, and at world save / stop | `map/MapServer.java` |
| M4 | Low | Guild Terminal contents | each open screen counted the whole network every half second | one shared snapshot per terminal per half second, invalidated by takes/stores | `block/GuildTerminalBlockEntity.java`, `menu/TerminalMenu.java` |

What each player receives (unchanged, verified): map regions only on request, deflated, under a per-player byte
budget (12 KB/tick on a dedicated server, 1.5 MB outbox cap); freshly scanned chunks only to players subscribed to
that region (asked in the last 40 s); POINTS on login and on change; PLAYERS once a second for their own
dimension; pings only to the dimension; terminal contents only to its viewers, under 600 KB; waystone list on demand
(bounded by `waystones.maxTotal`); quest snapshots on progress; skill sync when mana changes. Nothing is broadcast
every tick to every player.

## 4. Server performance

| # | Sev. | Hot path | Fix | Files |
|---|---|---|---|---|
| P1 | High | Structure compass search (see S4) | cell cache + budget | `util/StructureLocator.java` |
| P2 | Med. | Machines and sorting chests loaded together (server start, a chunk) all ran their scans on the same tick (their counters all started at 0): periodic spikes | each one's counter starts at an offset from its position | `block/MachineBlockEntity.java`, `block/SortingChestBlockEntity.java` |
| P3 | Med. | Harvesters (243 blocks every 2 s) and Vacuum Hoppers (entity search every 5 ticks) worked at full rate when idle | idle back-off up to 4× slower, full speed again on any work or setting change | `block/MachineBlockEntity.java` |
| P4 | Med. | Unlimited machines per chunk | `machines.maxPerChunk` (32), enforced on hand placement and by Placers | `util/ServerGuard.java`, `block/MachineBlockEntity.java` |
| P5 | Med. | Natural spawning of mod creatures had no limit | `spawns.natural`, `spawns.maxLoadedPerType` (60 per kind per dimension; counted every 5 s) | `util/SpawnCaps.java`, `registry/ModEntities.java` |
| P6 | Low | Void-rescue position stored every tick per player | every 5 ticks, with its dimension (it could rescue to a spot of another dimension) | `event/EquipmentEvents.java` |

Memory leaks fixed (maps keyed by player UUID never cleared): `DangerEvents.SHOWN_LEVEL`,
`EquipmentEvents.LAST_SAFE`, `BuilderWandItem.UNDO`, `CrateBlock.LAST_INSERT`, plus the new rate-limit buckets and
waystone cooldowns — all dropped on logout (`ServerGuard.forget`). Static caches already cleared on server stop:
map server, wireless index, structure locator, spawn caps. Machines never force-load chunks; storage scans use
`getChunkNow` (never load or generate). Entity AI checked: path recalculation every 5–10 ticks in every custom goal,
boss arena and gargoyle gaze checks walk the player list (`NearbyPlayers`), not large entity boxes; ocean creatures
do constant work per tick and despawn like vanilla water animals; per-player tick handlers run every 10–200 ticks
except the glider (a map lookup).

**CI performance check** (`tools/ci_smoke.py`, phase "server performance"): on the flat test world, a 96 × 96
ripe wheat field with 96 machines (24 harvesters, 16 sprinklers, 16 vacuum hoppers, 16 detectors, 8 timers,
8 transmitters, 8 receivers) and 60 automatons fighting (20 brass golems, 20 clockwork spiders, 20 steam drones).
`/tick sprint 600` gives the mean time per tick (real work, no sleep), `/tick query` after 30 s at 20 TPS gives
average and P50/P95/P99. Fails above 25 ms per tick. The numbers, with a baseline of the empty area, are written to
`wayfarers-ci-smoke.txt`.

## 5. Stability

* Client-only code: every `com.wayfarers.client` / `net.minecraft.client` reference from common code sits behind
  `FMLEnvironment.dist == Dist.CLIENT` (packet handlers, manual, atlas) and the client package is only initialised
  from `WayfarersClient.init` under the same check. Generated models are only used by client renderers. Nothing to
  fix.
* Threads: all packet handlers run on the main thread (`addMain`); the map worker only touches its own copies and
  hands results back through a queue drained on the server thread.
* Disconnect mid-action: map requests finishing after a logout write into a dropped session (harmless); grappling
  hook / boomerang owners are null-checked; actions from disconnecting players are refused (`canAct`).
* Dimension change: the player object is kept by 26.2, levels are read from the player at use time; the void
  rescue no longer mixes dimensions.

## 6. Remaining risks

* The permission probes (`ServerGuard.mayBreak` / `mayPlace`) post Forge break/place events that did not physically
  happen: block-logging mods may record them. Our own listeners ignore probes (`ServerGuard.probing()`).
* Breakers/Placers now wait while their owner is offline (with `machines.actAsOwner`, the default). Farms built
  with them stop when the owner logs off; admins can turn the option off.
* Quest sharing defaults are unchanged (co-op design); public servers should set `quests.catchUpOnJoin = false`.
* Not tested in game here (no Java 25 locally): CI runs the smoke test, the perf check and the client test.
* Not changed (design): talent points from lifetime levels; Brass Golems are not capped per player (costly to
  build, persistent).

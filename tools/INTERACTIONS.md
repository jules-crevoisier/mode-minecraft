# Interaction checklist

Every block and item of the mod must react visibly when a player uses it: a screen, a message, a sound or particles. Re-check this list whenever an interaction changes.

| Block / item | Right-click | Feedback |
|---|---|---|
| Waystone | Opens the travel screen (search, favourites, rename). Travel is only allowed while standing at a waystone; the server checks it. | Screen. On discovery: server message, chime, particles, tip card |
| Sorting Chest | Opens a 54-slot chest. Sneak with an empty hand: sort it now. | Screen |
| Guild Terminal | Storage screen for every container within 12 blocks. Sneak: sort all of them. | Screen; message, sound and particles |
| Grave | Gives the items back (anyone can open it). | Message, sound, particles |
| Warden / Void altar | Right offering (in either hand): summons the boss. Wrong item: "needs X". Boss already awake nearby: "already awake". | Message, sound, particles |
| Boss Seal / Mist Gate / Sealed Bars | No right-click; they react to players entering the arena. | Ambient particles |
| Machines (9) | See `wf/machines.py`. Machines with slots open a menu; the others change their setting or show it. | Message above the hotbar and a click, or a screen |
| Furniture (9) | Decoration; no right-click. | — |
| Travel Backpack | Opens 27 slots. The open backpack can't be moved, and backpacks can't go inside backpacks. | Screen, sound |
| Magnet Ring | Toggles the magnet. | Message, sound, glint |
| Recall Scroll | Teleports to the nearest waystone; says so when there is none. | Particles, sound, message |
| Wayfarer's Atlas | Quest journal. | Screen, sound |
| Wayfarer's Manual | Guide (client). Hold W over an item: opens its page. | Screen, sound |
| Structure Compass | Distance and direction to the nearest structure. Sneak: change the target. | Message, particle trail, sound |
| Builder's Wands | Extend a face. Sneak in the air: undo. Refuses doors, beds and tall plants. A double slab costs 2 slabs. No water copied. Respects spawn protection and adventure mode. | Sound; message above the hotbar |
| Spell staves (7) | Cast for mana. | Particles, sound; "low mana" |
| Boss weapons, Cartographer's Blade, Hammer, Storm Staff, Void Spear, Light Staff, Boomerang | Ability with a cooldown. No cooldown when the ability fails ("Nothing in reach"). Never hits players, pets, villagers, golems or farm animals; beams stop at walls. | Particles, sound |
| Vial of Oblivion | Resets talents; refuses when there is nothing to forget. | Message, sound |
| Brass Wrench | Turns the clicked block (facing, axis or sign rotation), before the block's own right-click; sneak: the other way. Sneak on a Wayfarers machine: its own sneak-click (setting). Sneak on Wayfarers decoration or furniture: back to the inventory (double slab = 2). Leaves doors, beds, tall plants, double chests, extended pistons, portals and unbreakable blocks alone; a block only takes a direction it survives in. Needs build rights (spawn protection, adventure mode). Blocks with nothing to turn keep their own right-click. | Sound, wax particles; "Nothing to turn" / "You can't change blocks here" above the hotbar |
| Grappling Hook | Fires the claw (32 blocks, no entity hits). On a block: the owner's client reels them in (smooth in multiplayer), small hop at the end. Released by sneak, re-use, arrival, 3 s, switching item or distance; cooldown starts when the chain is back. No fall damage while reeled in and for 3 s after. | Chain drawn to the hand, chain/clank sounds, block particles |
| Brass Glider | Held while falling for real (not on a jump, not in water, not with an elytra or creative flight): sink capped at 0.08 block/tick, drift where you look. Server: no fall damage, 1 durability per 2 s. | Flap sound, cloud trails at the wing tips (seen by everyone) |
| Rivet Gun | Fires a rivet (5 damage): Rivets first, then iron nuggets; free in creative. Never hits the shooter or their pets. 0.7 s cooldown. | Shot and piston hiss, muzzle smoke, smoking rivet; "Out of rivets" + click |
| Pocket Watch | Time (hh:mm, Overworld clock), day number, moon phase, biome. Its hand follows the sun (spins outside the Overworld). | Above the hotbar, tick sound |
| Airship Compass | Nearest Sky Harbour (Void Ship Wreck in the End); stores it as a lodestone target so the needle points there. Nothing found: says so and the needle spins. | Message, spark trail, lodestone sound |

Commands: `/wayfarers warp` is for game masters only. Players travel through the waystone screen.

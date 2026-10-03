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

Commands: `/wayfarers warp` is for game masters only. Players travel through the waystone screen.

"""The Wayfarer's Manual: in-game guide pages (FR/EN), one per system.

Each page has an id, a category, an icon item, a title, short paragraphs and the items it is about
(their tooltips get "Hold [W]: manual page"). gen_java bakes the structure into GeneratedGuide.java and
gen_assets writes the text into the lang files as guide.wayfarers.<page>.title / .p<n>.
Keep paragraphs short: 1-3 sentences, say what to do, not how it works inside.
"""

CATEGORIES = [
    ("start", "minecraft:compass", ("Getting started", "Premiers pas")),
    ("talents", "minecraft:enchanted_book", ("Talents & magic", "Talents et magie")),
    ("travel", "wayfarers:waystone", ("Travel", "Voyage")),
    ("storage", "wayfarers:sorting_chest", ("Storage", "Rangement")),
    ("danger", "minecraft:iron_sword", ("Danger & bosses", "Danger et boss")),
    ("automatons", "wayfarers:clockwork_heart", ("Automatons", "Automates")),
    ("gear", "wayfarers:lithite_shard", ("Gear & materials", "Équipement et matériaux")),
    ("machines", "wayfarers:auto_harvester", ("Machines & redstone", "Machines et redstone")),
    ("gadgets", "wayfarers:brass_wrench", ("Steam gadgets", "Gadgets à vapeur")),
]

# (id, category, icon, (title en, title fr), [(en, fr), ...paragraphs], [related item ids])
PAGES = [
    ("welcome", "start", "wayfarers:wayfarer_atlas", ("Welcome, Wayfarer", "Bienvenue, Voyageur"), [
        ("This world hides dozens of hand-built structures, dungeons and bosses. Your group explores it together: "
         "quests, waystones and discoveries are shared by everyone.",
         "Ce monde cache des dizaines de structures, de donjons et de boss. Ton groupe l'explore ensemble : quêtes, "
         "pierres de voyage et découvertes sont partagées par tous."),
        ("Press J (or use the Atlas) to open the quest journal, and follow the first chapter: it walks you "
         "through everything in this manual.",
         "Appuie sur J (ou utilise l'Atlas) pour ouvrir le journal de quêtes et suis le premier chapitre : il te "
         "fait découvrir tout ce manuel pas à pas."),
        ("Hover any Wayfarers item in your inventory and hold W to jump to its page here.",
         "Survole un objet Wayfarers dans ton inventaire et maintiens W pour ouvrir sa page ici."),
    ], ["wayfarers:wayfarer_atlas"]),
    ("quests", "start", "minecraft:writable_book", ("Quests & journal", "Quêtes et journal"), [
        ("The journal (J) lists five chapters. Each quest shows its objective, your progress and its rewards.",
         "Le journal (J) contient cinq chapitres. Chaque quête affiche son objectif, ta progression et ses récompenses."),
        ("Click Track to pin a quest to the top-right of your screen. When it is done, the tracker moves on to "
         "the next quest by itself.",
         "Clique sur Suivre pour épingler une quête en haut à droite de l'écran. Une fois terminée, le suivi passe "
         "tout seul à la quête suivante."),
        ("Progress is shared: when a friend completes a step, it counts for the whole group, even offline players.",
         "La progression est partagée : quand un ami réussit une étape, elle compte pour tout le groupe, même pour "
         "les absents."),
    ], []),
    ("keys", "start", "minecraft:oak_sign", ("Keys", "Touches"), [
        ("J: quest journal.  K: talent tree.  V: active talent.  R: sort your inventory.  M: magnet ring.  "
         "G: Builder's Wand symmetry.",
         "J : journal de quêtes.  K : arbre de talents.  V : talent actif.  R : trier l'inventaire.  M : aimant.  "
         "G : symétrie de la baguette."),
        ("All keys can be changed in Options > Controls > Wayfarers.",
         "Toutes les touches se changent dans Options > Commandes > Wayfarers."),
    ], []),
    ("compass", "start", "wayfarers:structure_compass", ("Structure Compass", "Boussole des structures"), [
        ("Use it to point to the nearest Wayfarers structure you have not explored yet.",
         "Utilise-la pour pointer vers la structure Wayfarers la plus proche que tu n'as pas encore explorée."),
        ("Sneak-use to switch the kind of structure it looks for.",
         "Accroupi + clic droit pour changer le type de structure recherché."),
    ], ["wayfarers:structure_compass"]),

    ("talents", "talents", "minecraft:enchanted_book", ("Talent tree", "Arbre de talents"), [
        ("Press K to open your talent tree: Warrior, Explorer, Arcanist and Engineer. Each talent costs points and "
         "needs one of the talents linked above it.",
         "Appuie sur K pour ouvrir ton arbre de talents : Guerrier, Explorateur, Arcaniste et Mécaniste. Chaque "
         "talent coûte des points et demande un des talents reliés au-dessus."),
        ("You earn 1 point per quest, 3 per boss quest and 1 every 10 experience levels gained.",
         "Tu gagnes 1 point par quête, 3 par quête de boss et 1 tous les 10 niveaux d'expérience gagnés."),
        ("The last talent of each branch is an active power: click it once unlocked to equip it, then press V to "
         "use it. A Vial of Oblivion gives every point back.",
         "Le dernier talent de chaque branche est un pouvoir actif : clique dessus une fois débloqué pour l'équiper, "
         "puis appuie sur V. Une Fiole d'oubli rend tous les points."),
    ], ["wayfarers:oblivion_vial"]),
    ("magic", "talents", "wayfarers:fire_staff", ("Magic", "Magie"), [
        ("Magic is simple: each staff holds one spell. Right-click to cast it. Spells cost mana, shown in the blue "
         "bar above your experience; it refills by itself.",
         "La magie est simple : chaque bâton contient un sort. Clic droit pour le lancer. Les sorts coûtent du mana, "
         "affiché dans la barre bleue au-dessus de l'expérience ; il se recharge tout seul."),
        ("Fire bolt, frost nova, Tesla lightning, mending, levitation, ward and steam blast: craft them with "
         "amethyst. The Arcanist talents give more mana, faster regeneration and stronger, cheaper spells.",
         "Trait de feu, nova de givre, éclair Tesla, soin, lévitation, protection et jet de vapeur : fabrique-les avec "
         "de l'améthyste. Les talents d'Arcaniste donnent plus de mana, une recharge plus rapide et des sorts plus "
         "forts et moins chers."),
        ("Carry an Arcane Ring (+50 mana) or a Mana Amulet (faster regeneration): no slot needed.",
         "Garde sur toi un Anneau arcanique (+50 mana) ou une Amulette de mana (recharge plus rapide) : aucune case "
         "spéciale nécessaire."),
    ], ["wayfarers:fire_staff", "wayfarers:frost_staff", "wayfarers:thunder_staff", "wayfarers:healing_staff",
        "wayfarers:levitation_wand", "wayfarers:ward_orb", "wayfarers:steam_cane", "wayfarers:arcane_ring",
        "wayfarers:mana_amulet"]),
    ("waystones", "travel", "wayfarers:waystone", ("Waystones", "Pierres de voyage"), [
        ("Right-click a waystone to discover it for the whole group and open the travel map.",
         "Clic droit sur une pierre pour la découvrir pour tout le groupe et ouvrir la carte de voyage."),
        ("In the map, click a destination then Travel (or double-click it). Pin your favourites with the star and "
         "rename them with the quill.",
         "Dans la carte, choisis une destination puis Voyager (ou double-clic). Épingle tes favorites avec l'étoile "
         "et renomme-les."),
        ("You can craft and place your own waystones at home, at your farms or at a dungeon entrance.",
         "Tu peux fabriquer et poser tes propres pierres : à la base, aux fermes ou à l'entrée d'un donjon."),
    ], ["wayfarers:waystone"]),
    ("wonders", "travel", "wayfarers:structure_compass", ("Wonders of the world", "Merveilles du monde"), [
        ("Giant places wait to be found. The Clockwork Citadel: a steampunk town around a 75-block clock "
         "tower, in badlands, savannas, deserts and plains.",
         "Des lieux gigantesques attendent d'être trouvés. La Citadelle d'horlogerie : une ville steampunk autour "
         "d'une tour-horloge de 75 blocs, dans les badlands, savanes, déserts et plaines."),
        ("The Sky Harbour: an airship moored to an iron tower, seen from far away above the plains. The Undercity: a "
         "town on stilts in a vast cavern 12 to 30 blocks underground, around a glowing lake.",
         "Le Port céleste : un dirigeable amarré à une tour de fer, visible de loin au-dessus des plaines. Les "
         "Bas-fonds : une ville sur pilotis dans une immense caverne, de 12 à 30 blocs sous terre, autour d'un lac "
         "luminescent."),
        ("The Deep Dwarven City: a lost kingdom carved 40 to 50 blocks underground, behind a gate guarded by two "
         "giant dwarf kings, with forges, rivers of lava, a throne room and a hidden treasure vault.",
         "La Cité naine des profondeurs : un royaume perdu taillé de 40 à 50 blocs sous terre, derrière une porte "
         "gardée par deux rois nains géants, avec ses forges, ses rivières de lave, sa salle du trône et un trésor caché."),
        ("The Sylvan Palace: an elven palace grown around a colossal silver tree in the dark and ancient forests. The "
         "Inventor's Manor: a Victorian steampunk mansion on the meadows, with a conservatory and a secret laboratory.",
         "Le Palais sylvain : un palais elfique bâti autour d'un arbre d'argent colossal, dans les forêts sombres et "
         "anciennes. Le Manoir de l'inventeur : une demeure victorienne steampunk dans les prairies, avec sa serre et "
         "son laboratoire secret."),
        ("The Sky Isles: an archipelago floating 200 blocks high above the oceans and plains, linked by rope "
         "bridges, with waterfalls and a ruined shrine. Bring blocks to climb, or a way to fly.",
         "Les Îles célestes : un archipel flottant à 200 blocs de haut au-dessus des océans et des plaines, relié par "
         "des ponts de corde, avec des cascades et un sanctuaire en ruine. Prévois des blocs pour grimper, ou de quoi voler."),
        ("Sneak-use the Structure Compass to pick one of them, then use it to see the distance and direction.",
         "Accroupi + clic droit sur la boussole des structures pour en choisir une, puis clic droit pour voir la "
         "distance et la direction."),
    ], ["wayfarers:structure_compass"]),
    ("recall", "travel", "wayfarers:recall_scroll", ("Recall Scroll", "Parchemin de rappel"), [
        ("Use it to return instantly to the nearest waystone of your dimension. Elites sometimes drop them.",
         "Utilise-le pour revenir aussitôt à la pierre de voyage la plus proche de ta dimension. Les élites en "
         "lâchent parfois."),
    ], ["wayfarers:recall_scroll"]),

    ("sorting_chest", "storage", "wayfarers:sorting_chest", ("Sorting Chest", "Coffre de tri"), [
        ("A big 54-slot chest that sorts itself when nobody is looking inside, and vacuums items dropped "
         "within 6 blocks.",
         "Un grand coffre de 54 cases qui se trie tout seul quand personne ne regarde dedans, et aspire les objets "
         "lâchés à 6 blocs."),
        ("Sneak-right-click to sort it right now. Put one next to your mob farm or your mine entrance.",
         "Accroupi + clic droit pour le trier tout de suite. Pose-en un près de ta ferme ou de l'entrée de ta mine."),
    ], ["wayfarers:sorting_chest"]),
    ("crate", "storage", "wayfarers:compacting_crate", ("Compacting Crate", "Caisse compacte"), [
        ("A crate holds 32 stacks of a single item and shows it on its front with the count. Right-click with an "
         "item to put it in; right-click twice quickly to put in every one you carry.",
         "Une caisse contient 32 piles d'un seul objet, affiché en façade avec le total. Clic droit avec l'objet pour "
         "le ranger ; deux clics rapides rangent tous ceux que tu portes."),
        ("Left-click takes a stack (sneak: a single item). Hoppers, the Guild Terminal and quick-stack treat crates "
         "like chests that accept only their item.",
         "Clic gauche : prendre une pile (accroupi : un seul objet). Les entonnoirs, le terminal de guilde et le "
         "rangement rapide voient la caisse comme un coffre qui n'accepte que son objet."),
    ], ["wayfarers:compacting_crate"]),
    ("guild_terminal", "storage", "wayfarers:guild_terminal", ("Guild Terminal", "Terminal de guilde"), [
        ("Place it in your storage room: it shows everything stored in the chests within 12 blocks as one grid, "
         "with a search box. No cables, no power.",
         "Pose-le dans ta salle de stockage : il affiche tout le contenu des coffres à 12 blocs dans une seule "
         "grille, avec une recherche. Ni câble, ni énergie."),
        ("Click an item to take a stack (right-click: half, middle-click: one, shift-click: straight into your "
         "inventory). Click the grid with an item, or shift-click your inventory, to store it. Store all and Store "
         "matching empty your inventory in one click.",
         "Clic sur un objet : une pile (clic droit : la moitié, molette : un seul, Maj : directement dans "
         "l'inventaire). Clic sur la grille avec un objet, ou Maj + clic dans ton inventaire, pour le ranger. "
         "« Tout ranger » et « Ranger identiques » vident ton inventaire d'un clic."),
        ("Sneak-right-click the terminal to sort every chest around it at once.",
         "Accroupi + clic droit sur le terminal pour trier d'un coup tous les coffres autour."),
    ], ["wayfarers:guild_terminal"]),
    ("backpack", "storage", "wayfarers:travel_backpack", ("Travel Backpack", "Sac du Voyageur"), [
        ("Right-click to open 27 extra slots that travel with you. Keep it in your hand to use it.",
         "Clic droit pour ouvrir 27 cases en plus qui voyagent avec toi."),
    ], ["wayfarers:travel_backpack"]),
    ("magnet", "storage", "wayfarers:magnet_ring", ("Magnet Ring", "Anneau aimanté"), [
        ("While it is in your inventory and switched on (it glows), items and experience within 7 blocks fly to you.",
         "Tant qu'il est dans ton inventaire et allumé (il brille), objets et expérience à 7 blocs volent vers toi."),
        ("Right-click it or press M to switch it on or off.", "Clic droit ou touche M pour l'allumer ou l'éteindre."),
    ], ["wayfarers:magnet_ring"]),
    ("storage_buttons", "storage", "minecraft:barrel", ("Storage buttons", "Boutons de rangement"), [
        ("Every chest, barrel or backpack shows small brass buttons above it: Sort, Take everything, Deposit the "
         "items it already holds, and Quick-stack into the chests around you.",
         "Chaque coffre, tonneau ou sac affiche de petits boutons en laiton : Trier, Tout prendre, Déposer les objets "
         "qu'il contient déjà, et Ranger dans les coffres autour de toi."),
        ("Type in the search box to light up the matching slots. Middle-click any slot to sort its inventory.",
         "Écris dans la barre de recherche pour faire ressortir les cases correspondantes. Clic molette sur une case "
         "pour trier son inventaire."),
    ], []),
    ("refill", "storage", "minecraft:cobblestone", ("Hotbar refill", "Recharge de la barre"), [
        ("When the stack in your hand runs out (last block placed, last food eaten, tool broken), the next stack of "
         "the same item from your inventory takes its place by itself.",
         "Quand la pile en main est épuisée (dernier bloc posé, dernier aliment mangé, outil cassé), la pile suivante "
         "du même objet prend sa place toute seule."),
    ], []),
    ("harvest", "start", "minecraft:wheat", ("Right-click harvest", "Récolte au clic droit"), [
        ("Right-click a ripe crop (wheat, carrots, potatoes, beetroots, nether wart, cocoa...) to harvest it and "
         "replant it in one go.",
         "Clic droit sur une culture mûre (blé, carottes, pommes de terre, betteraves, verrues, cacao...) pour la "
         "récolter et la replanter d'un coup."),
    ], []),
    ("sorting", "storage", "minecraft:chest", ("Sorting your inventory", "Trier l'inventaire"), [
        ("Press R to sort your main inventory (not the hotbar or armour): stacks are merged and grouped.",
         "Appuie sur R pour trier ton inventaire principal (ni la barre d'action ni l'armure) : les piles sont "
         "fusionnées et regroupées."),
    ], []),
    ("grave", "storage", "wayfarers:grave", ("Graves", "Tombes"), [
        ("When you die, your belongings are kept in a grave where you fell. Its coordinates are sent in the chat.",
         "Quand tu meurs, tes affaires sont gardées dans une tombe là où tu es tombé. Ses coordonnées s'affichent "
         "dans le chat."),
        ("Right-click the grave to get everything back. A friend can also recover it for you.",
         "Clic droit sur la tombe pour tout récupérer. Un ami peut aussi la récupérer pour toi."),
    ], ["wayfarers:grave"]),

    ("danger", "danger", "minecraft:skeleton_skull", ("Danger levels", "Niveaux de danger"), [
        ("Monsters get stronger the further you travel from spawn, below sea level, in the Nether and in the End. "
         "The current level shows above your hotbar when it changes.",
         "Les monstres deviennent plus forts en s'éloignant du point d'apparition, sous le niveau de la mer, dans le "
         "Nether et dans l'End. Le niveau s'affiche au-dessus de ta barre quand il change."),
        ("Elites have a gold name and a gold frame on their health bar. They hit hard but drop materials, "
         "emeralds and sometimes a Recall Scroll.",
         "Les élites ont un nom doré et un cadre doré sur leur barre de vie. Ils frappent fort mais lâchent des "
         "matériaux, des émeraudes et parfois un parchemin de rappel."),
    ], []),
    ("blood_moon", "danger", "minecraft:redstone", ("Blood Moon", "Lune de sang"), [
        ("Every few nights a Blood Moon rises: monsters are much stronger and elites much more common. Stay "
         "together, light your base and wait for dawn.",
         "Toutes les quelques nuits, une Lune de sang se lève : les monstres sont bien plus forts et les élites bien "
         "plus nombreux. Restez groupés, éclairez la base et attendez l'aube."),
    ], []),
    ("bosses", "danger", "wayfarers:boss_seal", ("Bosses", "Boss"), [
        ("The big structures hide a boss arena behind a wall of mist. Walk through the mist to wake the boss: the "
         "mist seals until the fight ends.",
         "Les grandes structures cachent une arène derrière un mur de brume. Traverse la brume pour réveiller le "
         "boss : elle se referme jusqu'à la fin du combat."),
        ("Watch the wind-ups: every attack is announced by an animation or a circle on the ground. Hit it after "
         "a big attack, and break its poise to stagger it.",
         "Observe les préparations : chaque attaque est annoncée par une animation ou un cercle au sol. Frappe après "
         "une grosse attaque, et brise sa posture pour l'étourdir."),
        ("If everyone leaves the arena, the boss heals and goes back to sleep.",
         "Si tout le monde quitte l'arène, le boss se soigne et se rendort."),
    ], ["wayfarers:boss_seal", "wayfarers:mist_gate"]),
    ("remembrance", "danger", "minecraft:nether_star", ("Remembrances & boss weapons", "Souvenirs et armes de boss"), [
        ("Every boss drops its Remembrance. Craft it with four materials of its region and two diamonds to forge its "
         "unique weapon, with a special right-click power.",
         "Chaque boss lâche son Souvenir. Fabrique-le avec quatre matériaux de sa région et deux diamants pour forger "
         "son arme unique, avec un pouvoir au clic droit."),
    ], []),

    ("brass_golem", "automatons", "wayfarers:clockwork_heart", ("Brass Golem", "Golem de laiton"), [
        ("Stack two Blocks of Brass and use a Clockwork Heart on them: a Brass Golem wakes up and follows you.",
         "Empile deux blocs de laiton et utilise un cœur mécanique dessus : un golem de laiton se réveille et te suit."),
        ("Heart: a brass gear, two brass ingots, a block of redstone and a clock.",
         "Cœur : un engrenage, deux lingots de laiton, un bloc de redstone et une horloge."),
    ], ["wayfarers:clockwork_heart", "wayfarers:brass_golem_spawn_egg"]),
    ("brass_golem_orders", "automatons", "wayfarers:brass_ingot", ("Golem orders", "Ordres du golem"), [
        ("It punches every monster but creepers, and never hurts players, villagers or pets.",
         "Il frappe tous les monstres sauf les creepers, et ne blesse jamais joueurs, villageois ni animaux."),
        ("Sneak-use, empty hand: guard here / follow. Brass ingots repair it. Destroyed, it drops its heart.",
         "Accroupi + clic droit main vide : garder ici / suivre. Le laiton le répare. Détruit, il rend son cœur."),
    ], ["wayfarers:brass_ingot", "wayfarers:brass_block"]),
    ("clockwork_spider", "automatons", "wayfarers:brass_gear", ("Clockwork Spider", "Araignée-horloge"), [
        ("Packs of them roam the Rustlands, the Cogwork Valley and the Clockwork Citadel. They climb walls.",
         "Elles rôdent en bande dans les Terres rouillées, la Vallée des engrenages et la Citadelle d'horlogerie."),
        ("When one stops and its key whirs, it is about to leap. They drop brass and gears.",
         "Quand l'une s'arrête et que sa clé s'emballe, elle va bondir. Elles lâchent laiton et engrenages."),
    ], ["wayfarers:brass_gear", "wayfarers:clockwork_spider_spawn_egg"]),
    ("steam_drone", "automatons", "wayfarers:brass_nugget", ("Steam Drone", "Drone à vapeur"), [
        ("They fly at night over the steampunk lands and in the Undercity, circling and firing hot rivets.",
         "Ils volent la nuit sur les terres steampunk et dans les Bas-fonds, et tirent des rivets brûlants."),
        ("When one rears up, it is about to dive at you: step aside. A bow brings them down.",
         "Quand l'un se cabre, il va plonger sur toi : écarte-toi. Un arc les abat facilement."),
    ], ["wayfarers:steam_drone_spawn_egg"]),
    ("grand_clockmaker", "automatons", "wayfarers:remembrance_grand_clockmaker",
     ("The Grand Clockmaker", "Le Grand Horloger"), [
        ("Under the Clockwork Citadel's tower, a stair leads to the Clock Vault, where its maker keeps time.",
         "Sous la tour de la Citadelle d'horlogerie, un escalier mène au Caveau où veille son créateur."),
        ("His hands rewind and a ring closes: get out of it or be frozen in time. Jump his rings of sparks.",
         "Ses aiguilles reculent, un cercle se referme : sors-en ou sois figé. Saute ses anneaux d'étincelles."),
    ], ["wayfarers:remembrance_grand_clockmaker", "wayfarers:clockmaker_pendulum"]),
    ("grand_clockmaker_midnight", "automatons", "minecraft:clock", ("Midnight", "Minuit"), [
        ("Wounded, he skips through time behind you, then tolls midnight: twelve bells around him, one under you.",
         "Blessé, il saute dans le temps derrière toi, puis sonne minuit : douze cloches, puis une sous tes pieds."),
        ("His Remembrance forges the Clockmaker's Pendulum.", "Son Souvenir forge le Pendule du Grand Horloger."),
    ], []),

    ("materials", "gear", "wayfarers:lithite_shard", ("Materials", "Matériaux"), [
        ("Map Fragments come from Overworld ruins, Lithite from deep ores, Ancient Embers from the Nether and Void "
         "Shards from the End. They repair and craft the gear of each region.",
         "Les fragments de carte viennent des ruines de la Surface, la lithite des minerais profonds, les braises "
         "anciennes du Nether et les éclats du vide de l'End. Ils réparent et fabriquent l'équipement de chaque "
         "région."),
    ], ["wayfarers:map_fragment", "wayfarers:lithite_shard", "wayfarers:ancient_ember", "wayfarers:void_shard"]),
    ("armor", "gear", "wayfarers:explorer_chestplate", ("Armour sets", "Ensembles d'armure"), [
        ("Wear all four pieces of a set to get its bonus: Explorer (speed, soft landings, night vision underground), "
         "Ember (fire immunity) and Void (slow fall, saved from the void).",
         "Porte les quatre pièces d'un ensemble pour son bonus : Explorateur (vitesse, chutes douces, vision "
         "nocturne sous terre), Braise (immunité au feu) et Vide (chute lente, sauvé du vide)."),
    ], ["wayfarers:explorer_chestplate", "wayfarers:ember_chestplate", "wayfarers:void_chestplate"]),
    ("ores", "gear", "wayfarers:zinc_ingot", ("New ores & brass", "Nouveaux minerais et laiton"), [
        ("Zinc is common in stone (y -16 to 96). Craft 3 copper ingots + 1 zinc ingot into 4 brass ingots: brass "
         "tools are faster than iron and enchant well.",
         "Le zinc est courant dans la pierre (y -16 à 96). Fabrique 3 lingots de cuivre + 1 lingot de zinc pour "
         "obtenir 4 lingots de laiton : les outils en laiton sont plus rapides que le fer et s'enchantent bien."),
        ("Mithril hides deep in deepslate (below y -8, iron pickaxe). Aether crystals glow faintly between y -48 and "
         "32. Orichalcum is found in the Nether. Smelt raw ores like iron.",
         "Le mithril se cache dans l'ardoise des abîmes (sous y -8, pioche en fer). Les cristaux d'éther luisent "
         "faiblement entre y -48 et 32. L'orichalque se trouve dans le Nether. Les minerais bruts se cuisent comme le "
         "fer."),
    ], ["wayfarers:zinc_ingot", "wayfarers:brass_ingot", "wayfarers:mithril_ingot", "wayfarers:aether_crystal",
        "wayfarers:orichalcum_ingot"]),
    ("metal_armor", "gear", "wayfarers:brass_helmet", ("Brass, mithril & arcane gear", "Laiton, mithril et arcanes"), [
        ("Brass set: night vision and faster mining. Mithril set: +4 health and +10% speed. Aether set: +75 mana, "
         "mana refills twice as fast, no fall damage.",
         "Ensemble en laiton : vision nocturne et minage plus rapide. Mithril : +4 points de vie et +10 % de vitesse. "
         "Éther : +75 de mana, recharge deux fois plus rapide, aucun dégât de chute."),
        ("Arcanist robes are woven from Arcane Cloth (purple wool, string and an aether crystal): +100 mana and spells 25% "
         "stronger.",
         "Les robes d'arcaniste se tissent en étoffe arcanique (laine violette, ficelle et cristal d'éther) : +100 de mana et "
         "sorts 25 % plus puissants."),
    ], ["wayfarers:brass_helmet", "wayfarers:mithril_chestplate", "wayfarers:aether_chestplate",
        "wayfarers:arcane_chestplate"]),
    ("steam_blocks", "gear", "wayfarers:gear_panel", ("Steampunk blocks", "Blocs steampunk"), [
        ("Brass, copper and dark iron plating, clockwork and gauge panels, pipe bundles, Edison lamps, aether "
         "conduits, mahogany panelling, tufted leather and smokestack bricks. Most plates also come as stairs and "
         "slabs.",
         "Placages en laiton, cuivre et fer sombre, panneaux d'horlogerie et à manomètre, faisceaux de tuyaux, lampes "
         "Edison, conduits d'éther, lambris d'acajou, capitonnage en cuir et briques de cheminée. La plupart des "
         "plaques existent aussi en escaliers et dalles."),
        ("Tip: keep brass for the trims and let dark iron and mahogany carry the mass; light it with Edison lamps.",
         "Astuce : garde le laiton pour les finitions, laisse le fer sombre et l'acajou porter la masse, et éclaire "
         "avec des lampes Edison."),
    ], ["wayfarers:brass_plating", "wayfarers:gear_panel", "wayfarers:copper_pipes", "wayfarers:edison_lamp",
        "wayfarers:aether_conduit", "wayfarers:mahogany_panelling"]),
    ("wand", "gear", "wayfarers:builder_wand", ("Builder's Wand", "Baguette du bâtisseur"), [
        ("Hold the wand and look at a block: gold outlines show where copies will go. Right-click to extend that face "
         "with blocks of the same kind from your inventory (16 at a time, 64 with the Master wand).",
         "Tiens la baguette et regarde un bloc : des contours dorés montrent où iront les copies. Clic droit pour "
         "prolonger la face avec des blocs du même type pris dans ton inventaire (16 à la fois, 64 avec la baguette "
         "du maître)."),
        ("Made a mistake? Sneak-right-click in the air to undo the last use: the blocks come back to you.",
         "Une erreur ? Accroupi + clic droit dans le vide pour annuler : les blocs te reviennent."),
    ], ["wayfarers:builder_wand", "wayfarers:master_builder_wand"]),
    ("symmetry", "gear", "wayfarers:master_builder_wand", ("Wand symmetry", "Symétrie de la baguette"), [
        ("1. Sneak-right-click a block with the wand: it becomes the mirror centre (sparks show the plane) and "
         "mirror X turns on.",
         "1. Accroupi + clic droit sur un bloc avec la baguette : il devient le centre du miroir (des étincelles "
         "montrent le plan) et le miroir X s'active."),
        ("2. Press G (or sneak-click the centre again) to switch: off, mirror X (east/west), mirror Z "
         "(north/south), mirror X + Z (4 ways).",
         "2. Appuie sur G (ou accroupi + clic sur le centre) pour changer : désactivée, miroir X (est/ouest), "
         "miroir Z (nord/sud), miroir X + Z (4 côtés)."),
        ("3. Build as usual: gold outlines are your blocks, blue ones their mirrored copies (stairs turn the right "
         "way). Each copy costs a block; undo removes them all.",
         "3. Construis comme d'habitude : contours dorés pour tes blocs, bleus pour leurs copies en miroir (les "
         "escaliers sont retournés). Chaque copie coûte un bloc ; annuler les retire toutes."),
    ], ["wayfarers:builder_wand", "wayfarers:master_builder_wand"]),
    ("chisel", "gear", "wayfarers:chisel", ("Engraver's Chisel", "Burin du graveur"), [
        ("Right-click a block to carve it into the next variant of its family: stone, bricks, mossy, cracked, "
         "chiseled... Sneak-right-click goes back. Each cut uses one durability.",
         "Clic droit sur un bloc pour le tailler en la variante suivante de sa famille : pierre, briques, moussues, "
         "fissurées, sculptées... Accroupi : retour en arrière. Chaque taille use le burin d'un point."),
        ("Stairs, slabs and walls keep their shape; copper keeps its age and wax. Works on vanilla stone, deepslate, "
         "tuff, sandstone, quartz, prismarine, blackstone, terracotta, copper and the Wayfarers blocks.",
         "Escaliers, dalles et murets gardent leur forme ; le cuivre garde son oxydation et sa cire. Marche sur la "
         "pierre, l'ardoise des abîmes, le tuf, le grès, le quartz, la prismarine, la pierre noire, la terre cuite, "
         "le cuivre et les blocs Wayfarers."),
        ("Some steampunk variants only exist through the chisel: brass tiles, engraved brass, brass grille, copper "
         "tiles, dark iron bricks, mahogany parquet...",
         "Certaines variantes steampunk n'existent que par le burin : carreaux et grille en laiton, laiton gravé, "
         "carreaux de cuivre, briques de fer sombre, parquet d'acajou..."),
    ], ["wayfarers:chisel", "wayfarers:engraved_brass", "wayfarers:brass_tiles", "wayfarers:dark_iron_bricks",
        "wayfarers:mahogany_parquet"]),
    ("chisel_table", "gear", "wayfarers:chisel_table", ("Chisel Table", "Table de taille"), [
        ("Right-click the table and put a whole stack of blocks in its slot: every variant of the family appears "
         "on the right.",
         "Clic droit sur la table et pose une pile entière de blocs dans sa case : toutes les variantes de la "
         "famille apparaissent à droite."),
        ("Click a variant to turn the whole stack into it. It is free and the table never wears out.",
         "Clique une variante pour y transformer toute la pile. C'est gratuit et la table ne s'use jamais."),
    ], ["wayfarers:chisel_table", "wayfarers:chisel"]),
    ("tools", "gear", "wayfarers:excavator_pickaxe", ("Special tools", "Outils spéciaux"), [
        ("The Excavator Pickaxe mines 3x3 and the Lumber Axe fells whole trees. Sneak to break a single block.",
         "La pioche d'excavation mine en 3x3 et la hache de bûcheron abat l'arbre entier. Accroupi : un seul bloc."),
    ], ["wayfarers:excavator_pickaxe", "wayfarers:lumber_axe"]),
]

# Shown once per player, the first time something happens: (id, icon, (en, fr), manual page)
TIPS = [
    ("waystone", "wayfarers:waystone", ("Waystone discovered! Right-click it any time to travel.",
                                        "Pierre découverte ! Clic droit dessus pour voyager à tout moment."), "waystones"),
    ("grave", "wayfarers:grave", ("Your belongings wait in a grave where you fell. Right-click it to get them back.",
                                  "Tes affaires t'attendent dans une tombe là où tu es tombé. Clic droit dessus pour "
                                  "les récupérer."), "grave"),
    ("sorting_chest", "wayfarers:sorting_chest", ("Sorting chest: it sorts itself and pulls in nearby drops.",
                                                  "Coffre de tri : il se trie seul et aspire les objets proches."),
     "sorting_chest"),
    ("guild_terminal", "wayfarers:guild_terminal", ("Terminal: every chest within 12 blocks in one searchable grid.",
                                                    "Terminal : tous les coffres à 12 blocs dans une seule grille, "
                                                    "avec recherche."), "guild_terminal"),
    ("elite", "minecraft:gold_ingot", ("An Elite! Gold name, hits hard, drops good loot.",
                                       "Un élite ! Nom doré, frappe fort, bon butin."), "danger"),
    ("blood_moon", "minecraft:redstone", ("A Blood Moon rises: monsters are much stronger tonight.",
                                          "Une Lune de sang se lève : les monstres sont bien plus forts cette nuit."),
     "blood_moon"),
    ("boss_mist", "wayfarers:mist_gate", ("Boss mist: walk through it to start the fight. It seals behind you.",
                                          "Brume de boss : traverse-la pour lancer le combat. Elle se referme "
                                          "derrière toi."), "bosses"),
    ("danger", "minecraft:skeleton_skull", ("The danger level rose: monsters here are stronger.",
                                            "Le niveau de danger augmente : les monstres sont plus forts ici."),
     "danger"),
]


def lang():
    en, fr = {}, {}
    for cid, _icon, (ten, tfr) in CATEGORIES:
        en[f"guide.wayfarers.cat.{cid}"], fr[f"guide.wayfarers.cat.{cid}"] = ten, tfr
    for pid, _cat, _icon, (ten, tfr), paras, _items in PAGES:
        en[f"guide.wayfarers.{pid}.title"], fr[f"guide.wayfarers.{pid}.title"] = ten, tfr
        for i, (pe, pf) in enumerate(paras):
            en[f"guide.wayfarers.{pid}.p{i}"], fr[f"guide.wayfarers.{pid}.p{i}"] = pe, pf
    for tid, _icon, (te, tf), _page in TIPS:
        en[f"tip.wayfarers.{tid}"], fr[f"tip.wayfarers.{tid}"] = te, tf
    return en, fr


def _machine_pages():
    from .machines import GUIDE
    return [(pid, "machines", icon, title, paras, items) for pid, icon, title, paras, items in GUIDE]


PAGES += _machine_pages()


def _gadget_pages():
    from .gadgets import guide_pages
    return guide_pages()


PAGES += _gadget_pages()

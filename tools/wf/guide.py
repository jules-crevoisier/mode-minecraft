"""The Wayfarer's Manual: in-game guide pages (FR/EN), one per system.

Each page has an id, a category, an icon item, a title, short paragraphs and the items it is about
(their tooltips get "Hold [W]: manual page"). gen_java bakes the structure into GeneratedGuide.java and
gen_assets writes the text into the lang files as guide.brasshaven.<page>.title / .p<n>.
Keep paragraphs short: 1-3 sentences, say what to do, not how it works inside.
"""

from . import worldbiomes as _WB  # the Brasshaven biome pages take their text from there (the wiki does too)

CATEGORIES = [
    ("start", "minecraft:compass", ("Getting started", "Premiers pas")),
    ("talents", "minecraft:enchanted_book", ("Talents & magic", "Talents et magie")),
    ("travel", "brasshaven:waystone", ("Travel", "Voyage")),
    ("wonders", "minecraft:clock", ("Wonders", "Merveilles du monde")),
    ("storage", "brasshaven:sorting_chest", ("Storage", "Rangement")),
    ("danger", "minecraft:iron_sword", ("Danger & bosses", "Danger et boss")),
    ("automatons", "brasshaven:clockwork_heart", ("Automatons", "Automates")),
    ("gear", "brasshaven:lithite_shard", ("Gear & materials", "Équipement")),
    ("building", "brasshaven:builder_wand", ("Building tools", "Construction")),
    ("machines", "brasshaven:auto_harvester", ("Redstone machines", "Mécanismes")),
    ("gadgets", "brasshaven:brass_wrench", ("Steam gadgets", "Gadgets à vapeur")),
    ("oceans", "brasshaven:diving_helmet", ("Living oceans", "Océans vivants")),
]

# (id, category, icon, (title en, title fr), [(en, fr), ...paragraphs], [related item ids])
# Write each system as: what it is, how to get it, how to use it. Long pages are fine (the screen splits them into
# continuation sheets), but validate.py warns when a page needs more than two sheets.
PAGES = [
    # ------------------------------------------------------------------ getting started
    ("welcome", "start", "brasshaven:wayfarer_atlas", ("Welcome, Wayfarer", "Bienvenue, Voyageur"), [
        ("This world hides dozens of hand-built structures, dungeons, bosses and giant wonders. Your group explores "
         "it together: quests, waystones and discoveries are shared by everyone.",
         "Ce monde cache des dizaines de structures, de donjons, de boss et de merveilles géantes. Ton groupe "
         "l'explore ensemble : quêtes, pierres de voyage et découvertes sont partagées par tous."),
        ("To begin, follow the card at the top-right: it always shows your next step. First, meet a Guild Agent: "
         "the nearest Guild Outpost is marked on your map (M). The rest is earned: see \"The road ahead\".",
         "Pour commencer, suis la carte en haut à droite : elle montre toujours ta prochaine étape. D'abord, "
         "rencontre un agent de la Guilde : l'avant-poste le plus proche est marqué sur ta carte (M). Le reste se "
         "mérite : voir « La route du voyageur »."),
        ("This manual explains every system. Click a page in the contents on the left; turn pages with the arrows, "
         "the mouse wheel or the arrow keys. When a page goes on, the button reads \"More >\".",
         "Ce manuel explique chaque système. Clique une page dans le sommaire à gauche ; tourne les pages avec les "
         "flèches, la molette ou les touches fléchées. Quand une page continue, le bouton affiche « Suite > »."),
        ("Shortcut: hover a Brasshaven item in your inventory and hold the manual key (W, or the key its tooltip "
         "shows; Controls to change it) to open its page. Lost the manual? Craft a book and a feather.",
         "Raccourci : survole un objet Brasshaven dans ton inventaire et maintiens la touche du manuel (Z sur un "
         "clavier AZERTY, celle qu'indique l'infobulle ; réglable dans Commandes) pour ouvrir sa page. Manuel "
         "perdu ? Un livre et une plume."),
    ], ["brasshaven:wayfarer_atlas", "brasshaven:wayfarer_manual"]),
    # the progression ladder (wf/progression.py), in words; docs/PROGRESSION.md has the full table
    ("path", "start", "brasshaven:structure_compass", ("The road ahead", "La route du voyageur"), [
        ("1. Meet a Guild Agent: the nearest Guild Outpost is marked on your map (a village's Guild Post works "
         "too). Lost the mark? Use the Atlas: it shows the way again until you get there.",
         "1. Rencontre un agent de la Guilde : l'avant-poste le plus proche est marqué sur ta carte (le Relais de "
         "la Guilde d'un village convient aussi). Repère perdu ? Utilise l'Atlas : il redonne la direction tant que "
         "tu n'y es pas allé."),
        ("2. His first contract: bring 12 bread. 3. The second: survey a Ruined Watchtower (he marks one on your "
         "map). Your reward: the Structure Compass, to find every other structure.",
         "2. Son premier contrat : apporter 12 pains. 3. Le deuxième : inspecter une tour de guet en ruine (il en "
         "marque une sur ta carte). Ta récompense : la boussole des structures, pour trouver toutes les autres."),
        ("4. With Map Fragments from structures: a waystone, a backpack, the Cartographer's Blade and the Explorer "
         "set. 5. Below y = 0, Lithite: its gear, and more compasses. 6. The Nether, then the End.",
         "4. Avec les fragments de carte des structures : pierre de voyage, sac, lame du Cartographe et tenue "
         "d'explorateur. 5. Sous y = 0, la lithite : son équipement, et d'autres boussoles. 6. Le Nether, puis l'End."),
        ("Each player earns the compass from the contracts for themselves, even on a server where the others went "
         "far ahead.",
         "Chaque joueur gagne la boussole par les contrats pour lui-même, même sur un serveur où les autres sont "
         "déjà loin."),
    ], ["brasshaven:structure_compass", "brasshaven:map_fragment"]),
    ("quests", "start", "minecraft:writable_book", ("Quests & journal", "Quêtes et journal"), [
        ("Open the journal with J or by using the Wayfarer's Atlas. Five chapters lead you from the first Guild "
         "Outpost to the End; each quest shows its objective, your progress and its rewards.",
         "Ouvre le journal avec J ou en utilisant l'Atlas du Voyageur. Cinq chapitres te mènent du premier "
         "avant-poste de la Guilde jusqu'à l'End ; chaque quête affiche son objectif, ta progression et ses "
         "récompenses."),
        ("The card at the top-right of your screen follows the road ahead: the next step you have not done, quests "
         "and contracts alike. Click Track to pin another quest instead; when it is done, the card goes back to "
         "the next step by itself.",
         "La carte en haut à droite de l'écran suit la route du voyageur : la prochaine étape que tu n'as pas faite, "
         "quête ou contrat. Clique sur Suivre pour épingler une autre quête ; une fois terminée, la carte revient "
         "toute seule à l'étape suivante."),
        ("Progress is shared: when a friend completes a step, it counts for the whole group, even offline players. "
         "Every quest also gives talent points.",
         "La progression est partagée : quand un ami réussit une étape, elle compte pour tout le groupe, même pour "
         "les absents. Chaque quête rapporte aussi des points de talent."),
    ], []),
    ("contracts", "start", "minecraft:emerald", ("Quest givers & contracts", "Donneurs de quêtes et contrats"), [
        ("People with a name tag hand out contracts: Guild Agents (villages, Guild Outposts), Scholars (village "
         "inns, the Forgotten Library), Tinkerers (village workshops, the Clockwork Citadel), Druids (the Hollow "
         "Giant Tree) and Dwarf Elders (the Deep Dwarven City).",
         "Des personnages au nom affiché proposent des contrats : agents de la Guilde (villages, avant-postes de la "
         "Guilde), érudites (auberges des villages, Bibliothèque oubliée), bricoleurs (ateliers des villages, "
         "Citadelle d'horlogerie), druidesses (Arbre-monde creux) et anciens nains (Cité naine des profondeurs)."),
        ("Right-click one to talk. \"!\" marks a new contract, \"?\" one you can hand in. Pick it, read what they "
         "ask, then Accept. Track pins it to the top-right of your screen.",
         "Clic droit pour leur parler. « ! » signale un nouveau contrat, « ? » un contrat à rendre. Choisis-le, lis "
         "ce qu'on te demande, puis Accepter. Suivre l'épingle en haut à droite de l'écran."),
    ], ["minecraft:emerald"]),
    ("contracts_kinds", "start", "minecraft:paper", ("Contracts: kinds & rewards", "Contrats : sortes et récompenses"), [
        ("Four kinds: bring items (they are taken when you hand them in), hunt creatures (kills after accepting "
         "count), find a structure (the nearest one is marked on your map when you accept; just walk into it), and "
         "deliver a sealed parcel to another quest giver.",
         "Quatre sortes : apporter des objets (ils sont pris quand tu les rends), chasser des créatures (les "
         "victimes après avoir accepté comptent), trouver une structure (la plus proche est marquée sur ta carte "
         "quand tu acceptes ; il suffit d'y entrer), et livrer un colis scellé à un autre donneur de quêtes."),
        ("Come back to the giver and press Turn in (Hand over for a parcel) for emeralds, experience and gear. "
         "Lost a parcel? Its giver hands you another. Each player has their own contracts; finishing one unlocks "
         "the next. The journal (J) lists them in its Contracts tab.",
         "Reviens voir le commanditaire et appuie sur Rendre (Remettre pour un colis) : émeraudes, expérience et "
         "équipement. Colis perdu ? Son expéditeur t'en donne un autre. Chaque joueur a ses propres contrats ; en "
         "finir un débloque le suivant. Le journal (J) les liste dans l'onglet Contrats."),
        ("Quest givers stay at their post, cannot be hurt and never leave. Villagers and quest givers live in the "
         "Guild Outposts, the monastery, the library, the lighthouse, the World Tree, the oasis, the observatories, "
         "the rune circle and the ziggurat's keepers' lodge, and in most wonders: no monster spawns inside those.",
         "Les donneurs de quêtes restent à leur poste, sont invulnérables et ne partent jamais. Villageois et "
         "donneurs de quêtes habitent les avant-postes de la Guilde, le monastère, la bibliothèque, le phare, "
         "l'Arbre-monde, l'oasis, les observatoires, le cercle runique, la loge des gardiens de la ziggourat et la "
         "plupart des merveilles : aucun monstre n'apparaît à l'intérieur."),
    ], []),
    ("keys", "start", "minecraft:oak_sign", ("Keys", "Touches"), [
        ("J: quest journal\nK: talent tree\nV: use your active talent\nR: sort your inventory\nM: world map\n"
         "H: show/hide the minimap\nShift + H: minimap size\nZ: minimap zoom\nB: ping the spot you look at\nN: magnet ring on/off\n"
         "G: Builder's Wand symmetry\nW (held over an item): its manual page\n"
         "In an inventory, over an item: R its recipes, U its uses\nI (in an inventory): show/hide the item list",
         "J : journal de quêtes\nK : arbre de talents\nV : utiliser le talent actif\nR : trier l'inventaire\n"
         "M : carte du monde\nH : afficher/masquer la mini-carte\nMaj + H : taille de la mini-carte\n"
         "Z : zoom de la mini-carte\nB : signaler l'endroit visé\n"
         "N : allumer/éteindre l'aimant\nG : symétrie de la baguette\nW (maintenu sur un objet) : sa page du manuel\n"
         "Dans un inventaire, sur un objet : R ses recettes, U ses utilisations\n"
         "I (dans un inventaire) : afficher/masquer la liste des objets"),
        ("These are the keys of a QWERTY keyboard: Options > Controls, Brasshaven section, shows yours and changes "
         "them. Display settings (health bars, damage numbers, tracker, tips, and the minimap's size, corner, shape, "
         "rotation, coordinates and opacity): Config button of Brasshaven in the mods list. The minimap's exact size "
         "(a slider) and the maps' relief: M, then the gear button.",
         "Ce sont les touches d'un clavier QWERTY (en AZERTY : W devient Z, Z devient W et M devient la virgule) : "
         "Options > Commandes, rubrique Brasshaven, montre les tiennes et les change. Réglages d'affichage (barres de "
         "vie, chiffres de dégâts, suivi, astuces, et taille, coin, forme, rotation, coordonnées et opacité de "
         "la mini-carte) : bouton Config de Brasshaven dans la liste des mods. Taille exacte de la mini-carte (un "
         "curseur) et relief des cartes : M, puis le bouton engrenage."),
    ], []),
    # the built-in recipe viewer (com.brasshaven.client.recipes)
    ("recipes", "start", "minecraft:crafting_table", ("Recipe viewer", "Livre de recettes"), [
        ("Beside every inventory sits the list of all items, Brasshaven's first. Search a name, @mod or #tag; the "
         "wheel turns its pages. I shows or hides it.",
         "À côté de chaque inventaire se tient la liste de tous les objets, ceux de Brasshaven d'abord. Cherche un "
         "nom, @mod ou #tag ; la molette tourne ses pages. I l'affiche ou la masque."),
        ("Over an item, in a slot or the list: R shows how to make it, U what it is used for (in the list: left or "
         "right click). One tab per way of making: crafting, furnaces, stonecutter, Chisel Table...",
         "Sur un objet, dans une case ou la liste : R montre comment le fabriquer, U à quoi il sert (dans la liste : "
         "clic gauche ou droit). Un onglet par façon de fabriquer : établi, fours, tailleur, table de taille..."),
        ("Click an ingredient for its own recipes; Backspace goes back. The book button opens the item's manual page.",
         "Clique un ingrédient pour ses propres recettes ; Retour arrière revient. Le bouton livre ouvre sa page du "
         "manuel."),
        ("From a crafting table, your inventory or a furnace, the + button moves the ingredients into the grid (Shift: "
         "as many as possible). What you lack is red.",
         "Depuis un établi, ton inventaire ou un four, le bouton + met les ingrédients dans la grille (Maj : le plus "
         "possible). Ce qui manque est en rouge."),
    ], []),
    ("compass", "start", "brasshaven:structure_compass", ("Structure Compass", "Boussole des structures"), [
        ("It finds Brasshaven structures. The Guild Agent gives you one for the contract \"Survey the Watchtower\" "
         "(after \"Provisions for the Road\"). Craft more later: a compass, three Map Fragments and a Lithite Shard.",
         "Elle trouve les structures Brasshaven. L'agent de la Guilde t'en confie une pour le contrat « Inspecter "
         "la tour de guet » (après « Des vivres pour la route »). Plus tard, fabrique-en d'autres : une boussole, "
         "trois fragments de carte et un éclat de lithite."),
        ("Right-click: the chat shows the nearest one (name, distance, direction and coordinates) and sparks show "
         "the way.",
         "Clic droit : le chat affiche la plus proche (nom, distance, direction et coordonnées) et des étincelles "
         "montrent le chemin."),
        ("Sneak-right-click: choose which structure to look for, one kind at a time, or \"any structure\". The "
         "wonders come at the end of the list.",
         "Accroupi + clic droit : choisis le type de structure recherché, un à la fois, ou « n'importe quelle "
         "structure ». Les merveilles sont à la fin de la liste."),
    ], ["brasshaven:structure_compass"]),
    ("harvest", "start", "minecraft:wheat", ("Right-click harvest", "Récolte au clic droit"), [
        ("Right-click a ripe crop (wheat, carrots, potatoes, beetroots, nether wart, cocoa...) to harvest it and "
         "replant it in one go.",
         "Clic droit sur une culture mûre (blé, carottes, pommes de terre, betteraves, verrues, cacao...) pour la "
         "récolter et la replanter d'un coup."),
    ], []),

    # ------------------------------------------------------------------ talents & magic
    ("talents", "talents", "minecraft:enchanted_book", ("Talent tree", "Arbre de talents"), [
        ("Press K to open your talent tree: four branches, Warrior, Explorer, Arcanist and Engineer. Each talent "
         "costs points and needs one of the talents linked above it.",
         "Appuie sur K pour ouvrir ton arbre de talents : quatre branches, Guerrier, Explorateur, Arcaniste et "
         "Mécaniste. Chaque talent coûte des points et demande un des talents reliés au-dessus."),
        ("Points: 1 per quest (3 for a boss quest) and 1 every 10 experience levels gained.",
         "Points : 1 par quête (3 pour une quête de boss) et 1 tous les 10 niveaux d'expérience gagnés."),
        ("The last talent of each branch is an active power: once unlocked, click it to equip it, then press V to "
         "use it.",
         "Le dernier talent de chaque branche est un pouvoir actif : une fois débloqué, clique dessus pour "
         "l'équiper, puis appuie sur V pour l'utiliser."),
        ("Changed your mind? Drink a Vial of Oblivion to get every point back (glass bottle, ghast tear and "
         "amethyst shard).",
         "Envie de changer ? Bois une Fiole d'oubli pour récupérer tous tes points (fiole, larme de ghast et éclat "
         "d'améthyste)."),
    ], ["brasshaven:oblivion_vial"]),
    ("magic", "talents", "brasshaven:fire_staff", ("Magic", "Magie"), [
        ("Each staff holds one spell: hold it and right-click to cast. Spells cost mana, shown in the blue bar above "
         "your experience; it refills by itself.",
         "Chaque bâton contient un sort : tiens-le et fais clic droit pour le lancer. Les sorts coûtent du mana, "
         "affiché dans la barre bleue au-dessus de l'expérience ; il se recharge tout seul."),
        ("Spells: fire bolt, frost nova, Tesla lightning, mending, levitation, ward and steam blast. Each staff is "
         "crafted upright: an amethyst shard between two of its element (blaze powder, packed ice, copper...) on "
         "top, a collar, a stick.",
         "Sorts : trait de feu, nova de givre, éclair Tesla, soin, lévitation, protection et jet de vapeur. Chaque "
         "bâton se fabrique debout : un éclat d'améthyste entre deux ingrédients de son élément (poudre de blaze, "
         "glace compactée, cuivre...) en haut, une bague, un bâton."),
        ("More mana: an Arcane Ring (+50 mana, ring slot) or a Mana Amulet (faster regeneration, amulet slot) work "
         "while worn in the accessory slots next to your armour. Arcanist talents and robes make spells stronger.",
         "Plus de mana : un Anneau arcanique (+50 mana, emplacement d'anneau) ou une Amulette de mana (recharge plus "
         "rapide, emplacement d'amulette) agissent portés dans les emplacements d'accessoires, à côté de l'armure. "
         "Les talents et les robes d'arcaniste renforcent les sorts."),
    ], ["brasshaven:fire_staff", "brasshaven:frost_staff", "brasshaven:thunder_staff", "brasshaven:healing_staff",
        "brasshaven:levitation_wand", "brasshaven:ward_orb", "brasshaven:steam_cane", "brasshaven:arcane_ring",
        "brasshaven:mana_amulet"]),

    # ------------------------------------------------------------------ travel
    ("waystones", "travel", "brasshaven:waystone", ("Waystones", "Pierres de voyage"), [
        ("Waystones link the world. Right-click one to discover it for the whole group and open the travel map.",
         "Les pierres de voyage relient le monde. Clic droit sur une pierre pour la découvrir pour tout le groupe "
         "et ouvrir la carte de voyage."),
        ("In the map, click a destination then Travel (or double-click it). Pin your favourites with the star and "
         "rename them.",
         "Dans la carte, choisis une destination puis Voyager (ou double-clic). Épingle tes favorites avec l'étoile "
         "et renomme-les."),
        ("Craft your own for your base, your farms or a dungeon entrance: an ender pearl, two Map Fragments, a "
         "compass and three stone bricks.",
         "Fabrique les tiennes pour ta base, tes fermes ou l'entrée d'un donjon : une perle de l'Ender, deux "
         "fragments de carte, une boussole et trois briques de pierre."),
    ], ["brasshaven:waystone"]),
    ("map", "travel", "minecraft:filled_map", ("Map and minimap", "Carte et mini-carte"), [
        ("The minimap in the corner shows the land around you, where you face, and the nearby waystones, waypoints, "
         "players, pings, graves and your last death. H hides it, Shift + H: size, Z: zoom.",
         "La mini-carte montre le terrain autour de toi, ta direction, les pierres de voyage, repères, joueurs, "
         "signaux, tombes et ta dernière mort. H la masque, Maj + H : taille, Z : zoom."),
        ("M (or the Wayfarer's Atlas, sneaking) opens the world map. Drag to move it, wheel to zoom, Space to come "
         "back to you. Click a marker for its card.",
         "M (ou l'Atlas du Voyageur, accroupi) ouvre la carte du monde. Glisse pour la déplacer, molette pour "
         "zoomer, Espace pour revenir sur toi. Clique un repère pour sa fiche."),
        ("On a server the map is shared: what anyone explores appears on everyone's map. Underground, the map shows "
         "the cave around you instead of the surface.",
         "Sur un serveur, la carte est partagée : ce qu'un joueur explore apparaît chez tous. Sous terre, elle "
         "montre la grotte autour de toi."),
        ("Right-click the map: add a waypoint (name, colour, icon, private or shared). Its card lets you edit, share "
         "or delete it.",
         "Clic droit sur la carte : poser un repère (nom, couleur, icône, privé ou partagé). Sa fiche permet de le "
         "modifier, partager ou supprimer."),
        ("Middle-click the map, or press B while looking at a spot, to ping it: everyone sees it for a minute.",
         "Clic molette sur la carte, ou B en visant un endroit : un signal que tous voient une minute."),
        ("The cube button tilts the world map into a 3D view. The gear button: minimap size (48 to 160 px, shown "
         "live), corner, shape, opacity, radar, relief and contour lines.",
         "Le bouton cube incline la carte en vue 3D. L'engrenage : taille de la mini-carte (48 à 160 px, en "
         "direct), coin, forme, opacité, radar, relief et courbes de niveau."),
    ], ["brasshaven:wayfarer_atlas"]),
    ("radar", "travel", "minecraft:spyglass", ("Minimap radar", "Radar de la mini-carte"), [
        ("The creatures around you show on the minimap (and on the world map zoomed in): their face, or a dot "
         "- red hostile, green animal, yellow neutral; villagers and NPCs a badge, bosses a purple crowned skull. A "
         "small tick: far above or below. Other players: their head and where they look, gold for companions.",
         "Les créatures autour de toi s'affichent sur la mini-carte (et sur la carte zoomée) : leur tête, ou "
         "un point - rouge hostile, vert animal, jaune neutre ; villageois et PNJ un badge, boss un crâne violet "
         "couronné. Une petite flèche : loin au-dessus ou en dessous. Les autres joueurs : leur tête et où ils "
         "regardent, en doré pour tes compagnons."),
        ("The radar's options are in the gear panel (Radar column) or Mods > Brasshaven > Config, Radar tab: on or "
         "off, faces or dots, and which kinds to show (hostile, animals, NPCs, players, items).",
         "Ses options sont dans le panneau de l'engrenage (colonne Radar) ou Mods > Brasshaven > Config, onglet "
         "Radar : activé ou non, têtes ou points, et quels genres montrer (hostiles, animaux, PNJ, joueurs, objets)."),
    ], []),
    ("recall", "travel", "brasshaven:recall_scroll", ("Recall Scroll", "Parchemin de rappel"), [
        ("Use it to return instantly to the nearest waystone of your dimension. It is used up.",
         "Utilise-le pour revenir aussitôt à la pierre de voyage la plus proche de ta dimension. Il est consommé."),
        ("Elites sometimes drop one. Craft 2 with paper, a Map Fragment and an ender pearl.",
         "Les élites en lâchent parfois. Fabrique-en 2 avec du papier, un fragment de carte et une perle de l'Ender."),
    ], ["brasshaven:recall_scroll"]),
    ("villages", "travel", "minecraft:bell", ("Villages", "Villages"), [
        ("Every kind of village (plains, desert, savanna, snow, taiga) grows new buildings in its own style: an inn "
         "with rooms, a tinkerer's workshop, a watchtower, a market, an orchard, cottages, manors and wells.",
         "Tous les villages (plaines, désert, savane, neige, taïga) ont de nouveaux bâtiments dans leur style : "
         "une auberge avec des chambres, l'atelier du bricoleur, une tour de guet, un marché, un verger, des "
         "cottages, des manoirs et des puits."),
        ("About one village in four is built around a square with a waystone: right-click it to put the village "
         "on the travel map. The notice board and the meeting bell stand beside it.",
         "Environ un village sur quatre se forme autour d'une place avec une pierre de voyage : clic droit pour "
         "mettre le village sur la carte de voyage. Le tableau d'annonces et la cloche sont à côté."),
        ("Quest givers live there too: a Guild Agent in the Guild Post and by the square's notice board, a Scholar "
         "in the inn's tavern, a Tinkerer in the workshop. Right-click them for contracts.",
         "Des donneurs de quêtes y vivent aussi : un agent de la Guilde au Relais de la Guilde et près du tableau "
         "d'annonces de la place, une érudite dans la taverne de l'auberge, un bricoleur dans l'atelier. Clic droit "
         "pour leurs contrats."),
        ("Streets get brass lamps, signposts and planters. Pillager outposts now field steam ballistas and spiked "
         "barricades.",
         "Les rues ont des lampes en laiton, des panneaux et des jardinières. Les avant-postes pillards ont des "
         "balistes à vapeur et des barricades hérissées."),
    ], ["brasshaven:waystone", "brasshaven:edison_lamp", "minecraft:bell"]),
    ("biomes", "travel", "minecraft:crimson_nylium", ("Brasshaven biomes", "Biomes Brasshaven"), [
        ("New worlds of the Default type get three biomes of their own, carved out of vanilla climates on "
         "Minecraft's usual terrain: the Crimson Mire, the Volcanic Highlands and the Pale Dunes. Each has its "
         "colours, its ground and its natural objects.",
         "Les nouveaux mondes de type « Par défaut » ont trois biomes à eux, taillés dans des climats vanilla sur le "
         "relief habituel de Minecraft : le Marais pourpre, les Hautes terres volcaniques et les Dunes pâles. "
         "Chacun a ses couleurs, son sol et ses objets naturels."),
        ("To find one: /locate biome brasshaven:crimson_mire (or volcanic_highlands, pale_dunes). Villages, "
         "temples and Brasshaven structures of the climate they replace appear there too.",
         "Pour en trouver un : /locate biome brasshaven:crimson_mire (ou volcanic_highlands, pale_dunes). Les "
         "villages, temples et structures Brasshaven du climat qu'ils remplacent y apparaissent aussi."),
        ("Superflat, Amplified and Large Biomes worlds, and worlds created before, keep vanilla's biomes. A server "
         "can turn them off for new worlds (option world.customBiomes).",
         "Les mondes Superplat, Amplifié et Grands biomes, et les mondes déjà créés, gardent les biomes vanilla. Un "
         "serveur peut les couper pour les nouveaux mondes (option world.customBiomes)."),
    ], []),
    ('crimson_mire', "travel", 'minecraft:crimson_roots', (_WB.BIOMES['crimson_mire']["en"], _WB.BIOMES['crimson_mire']["fr"]), [
        (_WB.BIOMES['crimson_mire']["text_en"], _WB.BIOMES['crimson_mire']["text_fr"]),
        ("Where: " + _WB.BIOMES['crimson_mire']["where_en"], "Où : " + _WB.BIOMES['crimson_mire']["where_fr"]),
    ], []),
    ('volcanic_highlands', "travel", 'minecraft:magma_block', (_WB.BIOMES['volcanic_highlands']["en"], _WB.BIOMES['volcanic_highlands']["fr"]), [
        (_WB.BIOMES['volcanic_highlands']["text_en"], _WB.BIOMES['volcanic_highlands']["text_fr"]),
        ("Where: " + _WB.BIOMES['volcanic_highlands']["where_en"], "Où : " + _WB.BIOMES['volcanic_highlands']["where_fr"]),
    ], []),
    ('pale_dunes', "travel", 'minecraft:orange_terracotta', (_WB.BIOMES['pale_dunes']["en"], _WB.BIOMES['pale_dunes']["fr"]), [
        (_WB.BIOMES['pale_dunes']["text_en"], _WB.BIOMES['pale_dunes']["text_fr"]),
        ("Where: " + _WB.BIOMES['pale_dunes']["where_en"], "Où : " + _WB.BIOMES['pale_dunes']["where_fr"]),
    ], []),
    ("terrain_touches", "travel", "minecraft:mossy_cobblestone", ("Wilder landscapes", "Paysages plus sauvages"), [
        ("The vanilla biomes get a few natural touches: mossy boulders in plains, meadows, forests and taigas, "
         "fallen logs in dark forests, savannas and cherry groves, wildflower patches, moss carpets under old "
         "trees, small rock spires on stony peaks and windswept hills, and hot-spring terraces in the savanna "
         "highlands.",
         "Les biomes vanilla gagnent quelques touches naturelles : rochers moussus dans les plaines, prairies, "
         "forêts et taïgas, troncs tombés dans les forêts noires, savanes et cerisaies, tapis de fleurs sauvages, "
         "tapis de mousse sous les vieux arbres, petites aiguilles rocheuses sur les pics pierreux et les collines "
         "venteuses, et sources chaudes en terrasses sur les hautes savanes."),
        ("Each can be switched off on a server (options world.terrain.*); new chunks only.",
         "Chacune peut être coupée sur un serveur (options world.terrain.*) ; seulement pour les nouveaux chunks."),
    ], []),

    # ------------------------------------------------------------------ wonders
    ("wonders", "wonders", "brasshaven:structure_compass", ("How to find them", "Où les trouver"), [
        ("Wonders are giant places, far bigger than other structures: towns, palaces, a volcano, caverns, islands "
         "in the sky... Each one has its page in this chapter, and finding it completes a quest.",
         "Les merveilles sont des lieux gigantesques, bien plus grands que les autres structures : villes, palais, "
         "volcan, cavernes, îles dans le ciel... Chacune a sa page dans ce chapitre, et la découvrir valide une "
         "quête."),
        ("The ten wonders: Clockwork Citadel, Sky Harbour, The Undercity, Deep Dwarven City, Sylvan Palace, "
         "Inventor's Manor, Sky Isles, Geothermal Foundry, Tesla Observatory and Crystal Cathedral.",
         "Les dix merveilles : Citadelle d'horlogerie, Port céleste, Bas-fonds, Cité naine des profondeurs, Palais "
         "sylvain, Manoir de l'inventeur, Îles célestes, Fonderie géothermique, Observatoire Tesla et Cathédrale de "
         "cristal."),
        ("They are rare, often one or two thousand blocks apart. Sneak-right-click the Structure Compass until it "
         "names the one you want (wonders are at the end of the list), then right-click it for the distance and "
         "direction.",
         "Elles sont rares, souvent à un ou deux milliers de blocs les unes des autres. Accroupi + clic droit sur la "
         "boussole des structures jusqu'à ce qu'elle nomme celle que tu veux (les merveilles sont à la fin de la "
         "liste), puis clic droit pour la distance et la direction."),
        ("Underground wonders lie under any biome: dig down to the depth given on their page.",
         "Les merveilles souterraines se cachent sous n'importe quel biome : creuse jusqu'à la profondeur indiquée "
         "sur leur page."),
        ("Most barrels hold a few supplies that fit the room; the real loot stays in the chests.",
         "La plupart des tonneaux gardent quelques provisions selon la pièce ; le vrai butin reste dans les coffres."),
    ], []),
    ("clockwork_citadel", "wonders", "minecraft:clock", ("Clockwork Citadel", "Citadelle d'horlogerie"), [
        ("A walled steampunk town around a clock tower over 70 blocks tall, with workshops and smoking chimneys.",
         "Une ville steampunk fortifiée autour d'une tour-horloge de plus de 70 blocs, avec ateliers et cheminées "
         "fumantes."),
        ("Where: badlands, savannas, deserts and plains.",
         "Où : badlands, savanes, déserts et plaines."),
        ("Its clockmakers still work in the halls, guarded by Brass Golems; a Tinkerer gives contracts in the first "
         "workshop. A stair in the tower's entrance hall leads down to the Gearworks, where Clockwork Spiders "
         "swarm, and the Clock Vault, lair of the Grand Clockmaker (see Automatons).",
         "Ses horlogers travaillent encore dans les halles, gardés par des golems de laiton ; un bricoleur propose "
         "des contrats dans le premier atelier. Un escalier dans le hall de la tour descend aux Rouages, où "
         "grouillent les araignées-horloges, puis au Caveau de l'horloge, l'antre du Grand Horloger (voir "
         "Automates)."),
    ], []),
    ("sky_harbour", "wonders", "brasshaven:airship_compass", ("Sky Harbour", "Port céleste"), [
        ("A steam airship moored at the top of a 44-block iron tower, seen from far away.",
         "Un dirigeable à vapeur amarré au sommet d'une tour de fer de 44 blocs, visible de très loin."),
        ("Where: plains, meadows, savannas and hills. The Airship Compass points to the nearest one.",
         "Où : plaines, prairies, savanes et collines. La boussole de dirigeable pointe vers le plus proche."),
        ("Climb the tower to the docking arm to board the ship: deck, cabin, propeller and engines. Bring the "
         "Grappling Hook and the Brass Glider.",
         "Grimpe la tour jusqu'au bras d'amarrage pour monter à bord : pont, cabine, hélice et moteurs. Le grappin "
         "et le planeur sont parfaits ici."),
    ], []),
    ("undercity", "wonders", "minecraft:copper_lantern", ("The Undercity", "Les Bas-fonds"), [
        ("A town on stilts clinging to the walls of a vast cavern, around a central pillar and a toxic green lake, "
         "joined by catwalks and lit by lamps.",
         "Une ville sur pilotis accrochée aux parois d'une immense caverne, autour d'un pilier central et d'un lac "
         "vert toxique, reliée par des passerelles et éclairée de lampes."),
        ("Where: under any biome, deep down: its lake lies around y -15.",
         "Où : sous n'importe quel biome, en profondeur : son lac est vers y -15."),
        ("A family lives in every stilt house and no monster spawns in the cavern. Climb the pillar's ladders to "
         "reach the upper levels and the vault.",
         "Une famille vit dans chaque maison sur pilotis et aucun monstre n'apparaît dans la caverne. Grimpe les "
         "échelles du pilier pour atteindre les niveaux supérieurs et le coffre-fort."),
    ], []),
    ("dwarven_city", "wonders", "brasshaven:mithril_block", ("Deep Dwarven City", "Cité naine des profondeurs"), [
        ("A lost dwarf kingdom carved in the rock: a great cavern with a lava hearth, forges, a tavern, terraces of "
         "houses and a mine-cart line. A waystone waits by the hearth.",
         "Un royaume nain perdu, taillé dans la roche : une grande caverne avec un foyer de lave, des forges, une "
         "taverne, des terrasses d'habitations et une ligne de wagonnets. Une pierre de voyage attend près du foyer."),
        ("Where: under any biome, at the bottom of the world (floor around y -48).",
         "Où : sous n'importe quel biome, tout au fond du monde (sol vers y -48)."),
        ("Behind the great gate and its two 22-block dwarf statues: the Great Hall, the Throne Room and, under a "
         "carpet behind the throne, a trapdoor to the treasure vault, still guarded by skeleton knights. Dwarves "
         "live in the forges and houses; the Dwarf Elder gives contracts by the tavern hearth.",
         "Derrière la grande porte et ses deux statues naines de 22 blocs : la grande salle, la salle du trône et, "
         "sous un tapis derrière le trône, une trappe vers la salle du trésor, toujours gardée par des chevaliers "
         "squelettes. Des nains vivent dans les forges et les maisons ; l'ancien nain propose des contrats près du "
         "foyer de la taverne."),
    ], []),
    ("sylvan_palace", "wonders", "minecraft:flowering_azalea_leaves", ("Sylvan Palace", "Palais sylvain"), [
        ("An elven palace grown around a colossal silver tree 70 blocks tall. A spiral stair climbs around the trunk "
         "to three terraces and their pavilions.",
         "Un palais elfique bâti autour d'un arbre d'argent colossal de 70 blocs. Un escalier en spirale monte "
         "autour du tronc vers trois terrasses et leurs pavillons."),
        ("Where: dark forests, old-growth taigas, old-growth birch forests and flower forests.",
         "Où : forêts sombres, vieilles taïgas, vieilles forêts de bouleaux et forêts de fleurs."),
        ("Inside the trunk: the throne hall and the royal treasury. Up in the leaves: the library and, at the very "
         "top, the Moon Lantern. Rope bridges lead to three tree houses. The sylvan court lives in the pavilions: "
         "a healer, librarians, a weaver, a cook, a gardener and the royal cartographer.",
         "Dans le tronc : la salle du trône et le trésor royal. Dans les feuilles : la bibliothèque et, tout en "
         "haut, la Lanterne de lune. Des ponts de corde mènent à trois cabanes. La cour sylvaine habite les "
         "pavillons : une guérisseuse, des bibliothécaires, une tisserande, un cuisinier, un jardinier et le cartographe royal."),
    ], []),
    ("inventor_manor", "wonders", "brasshaven:redstone_timer", ("Inventor's Manor", "Manoir de l'inventeur"), [
        ("A Victorian steampunk mansion: turrets, a copper roof, an observatory with a telescope, a glass "
         "conservatory and a workshop wing.",
         "Une demeure victorienne steampunk : tourelles, toit de cuivre, observatoire avec télescope, serre en verre "
         "et aile d'atelier."),
        ("Where: plains, meadows, flower forests and cherry groves.",
         "Où : plaines, prairies, forêts de fleurs et cerisaies."),
        ("Secret: in the study, a carpet hides a trapdoor down to the inventor's laboratory, which keeps the best "
         "loot.",
         "Secret : dans le bureau, un tapis cache une trappe vers le laboratoire de l'inventeur, où se trouve le "
         "meilleur butin."),
    ], []),
    ("sky_isles", "wonders", "brasshaven:aether_crystal", ("Sky Isles", "Îles célestes"), [
        ("An archipelago of floating islands linked by rope bridges: waterfalls, a giant cherry tree, a ruined "
         "watchtower, aether crystals and a ruined shrine with the treasure altar.",
         "Un archipel d'îles flottantes reliées par des ponts de corde : cascades, cerisier géant, tour de guet en "
         "ruine, cristaux d'éther et un sanctuaire en ruine qui garde l'autel au trésor."),
        ("Where: high above oceans, plains and meadows (from about y 170 to y 230).",
         "Où : très haut au-dessus des océans, plaines et prairies (d'environ y 170 à y 230)."),
        ("To get up: pillar up with blocks, use the Grappling Hook or a levitation wand. The Brass Glider brings you "
         "back down safely. Beware the gargoyle in the tower.",
         "Pour monter : empile des blocs, utilise le grappin ou la baguette de lévitation. Le planeur en laiton te "
         "ramène en bas sans dégâts. Méfie-toi de la gargouille de la tour."),
    ], []),
    ("geothermal_foundry", "wonders", "minecraft:magma_block", ("Geothermal Foundry", "Fonderie géothermique"), [
        ("Steampunk ironworks built into a smoking volcano: a lava caldera under a bridge crane, casting halls and "
         "four 55-block chimneys.",
         "Des forges steampunk bâties dans un volcan fumant : une caldeira de lave sous un pont roulant, des halles "
         "de coulée et quatre cheminées de 55 blocs."),
        ("Where: badlands, savanna plateaus and windswept savannas.",
         "Où : badlands, plateaux de savane et savanes battues par les vents."),
        ("Inside the mountain lies the Forge of the Deep: steam hammers, blast furnaces and, at the back, the Heart "
         "around a lava well. Fire resistance helps.",
         "Dans la montagne se cache la Forge des Profondeurs : marteaux-pilons, hauts fourneaux et, au fond, le "
         "Cœur autour d'un puits de lave. Une potion de résistance au feu aide."),
    ], []),
    ("walking_fortress", "wonders", "brasshaven:gear_panel", ("Walking Fortress", "Forteresse marchante"), [
        ("The wreck of a brass siege walker frozen mid-stride in a scorched crater: four 60-block legs, a riveted "
         "hull carried 55 blocks up, smokestacks and a mast reaching y 130.",
         "L'épave d'un marcheur de siège en laiton figé en plein pas dans un cratère brûlé : quatre jambes de 60 "
         "blocs, une coque rivetée portée à 55 blocs du sol, des cheminées et un mât qui montent à 130."),
        ("Where: badlands, savannas, plains and deserts.",
         "Où : badlands, savanes, plaines et déserts."),
        ("The way in is a breach in a planted foot: climb the spiral inside the leg, cross the knee, take the stair "
         "up the thigh into the hold. The boss waits on the top deck; the vault is in the bridge tower.",
         "On entre par la brèche d'un pied posé : l'escalier en colimaçon de la jambe, la salle du genou, puis "
         "l'escalier de la cuisse jusqu'à la cale. Le boss attend sur le pont supérieur ; la salle forte est dans "
         "la tour de commandement."),
    ], []),
    ("rock_necropolis", "wonders", "minecraft:chiseled_red_sandstone", ("Necropolis of Kings", "Nécropole des rois"), [
        ("A rose-red sandstone massif carved like Petra and Abu Simbel: a winding slot canyon opens on a hidden "
         "court where four 42-block seated kings flank an 18-block portal.",
         "Un massif de grès rose taillé comme à Pétra et Abou Simbel : un canyon étroit et sinueux débouche sur une "
         "place cachée où quatre rois assis de 42 blocs encadrent un portail de 18 blocs."),
        ("Where: deserts and badlands.",
         "Où : déserts et badlands."),
        ("Behind the hypostyle hall, three levels of tombs go down: embalming rooms, a flooded gallery, a trapped "
         "corridor (mind the pressure plates) and the treasury. A site of grace waits before the king's arena; the "
         "King's Well climbs from the vault back to the hall.",
         "Derrière la salle hypostyle, trois niveaux de tombeaux descendent : salles d'embaumement, galerie inondée, "
         "couloir piégé (attention aux plaques de pression) et trésor. Un lieu de grâce précède l'arène du roi ; le "
         "puits du roi remonte de la salle forte jusqu'à la salle hypostyle."),
    ], []),
    ("fallen_colossus", "wonders", "minecraft:oxidized_copper", ("Fallen Colossus", "Colosse abattu"), [
        ("A 155-block statue of an armoured knight, stone under verdigris bronze plate, fallen on its side across a "
         "valley: the helm turned to the sky, a bent knee, the hand reaching out and the sword shattered behind him.",
         "La statue de 155 blocs d'un chevalier en armure, pierre sous plates de bronze vert-de-gris, tombée sur le "
         "flanc en travers d'une vallée : le heaume tourné vers le ciel, un genou replié, la main tendue et l'épée "
         "brisée derrière lui."),
        ("Where: plains, meadows, forests, savannas and taiga valleys.",
         "Où : plaines, prairies, forêts, savanes et vallées de taïga."),
        ("The way in is the broken wrist: the forearm leads to the elbow, a stair climbs the arm onto a balcony of "
         "the rib hall, a 30-block vault opened by a breach. The shoulder and the hip hide side rooms (the leg comes "
         "out at the knee); the neck leads to the boss in the helm, and the vault is under the arena floor.",
         "On entre par le poignet brisé : l'avant-bras mène au coude, un escalier monte dans le bras jusqu'au balcon "
         "de la salle des côtes, une voûte de 30 blocs ouverte par une brèche. L'épaule et la hanche cachent des "
         "salles (la jambe ressort au genou) ; le cou mène au boss dans le heaume, et la salle forte est sous le sol "
         "de l'arène."),
    ], []),
    ("chained_bastion", "wonders", "minecraft:gilded_blackstone", ("Chained Bastion", "Bastion enchaîné"), [
        ("A blackstone and gilded fortress hanging under the Nether ceiling from eight giant chains, over a lava "
         "lake: a stepped keel, a forest of inverted spires and broken chains dangling toward the lava.",
         "Une forteresse de pierre noire et d'or suspendue sous le plafond du Nether par huit chaînes géantes, "
         "au-dessus d'un lac de lave : une quille en gradins, une forêt de flèches inversées et des chaînes brisées "
         "qui pendent vers la lave."),
        ("Where: Nether wastes, basalt deltas, crimson forests and soul sand valleys, in big lava caverns.",
         "Où : désolations du Nether, deltas de basalte, forêts carmin et vallées des âmes, dans les grandes "
         "cavernes de lave."),
        ("The way in starts on a rock landing: a chain bridge to a pier, then a stair up the back of the anchor "
         "chain to the gate (a fall means the lava: bring fire resistance). Inside, the prison of hanging cages, the "
         "barracks (look under the floor), the forge, the chapel and a site of grace before the boss drum; the "
         "vault lies past the arena.",
         "On entre par un débarcadère rocheux : un pont de chaînes jusqu'à une pile, puis un escalier sur le dos de "
         "la chaîne d'ancrage jusqu'à la porte (une chute, c'est la lave : prends de la résistance au feu). Dedans, "
         "la prison des cages suspendues, la caserne (regarde sous le plancher), la forge, la chapelle et un lieu de "
         "grâce avant le tambour du boss ; la salle du trésor est au-delà de l'arène."),
    ], []),
    ("pilgrims_ascent", "wonders", "minecraft:bell", ("Pilgrim's Ascent", "L'Ascension du pèlerin"), [
        ("A 124-block fang of rock with a sheer north face over a plunge pool; up its south flank a switchback "
         "stairway of almost 500 steps, sixteen red gates and a lantern on every landing, to a bell temple on the "
         "summit.",
         "Un croc de roche de 124 blocs, à-pic au nord au-dessus d'un bassin ; sur son flanc sud, un escalier en "
         "lacets de près de 500 marches, seize portiques rouges et une lanterne à chaque palier, jusqu'au temple de "
         "la cloche au sommet."),
        ("Where: meadows, groves, snowy slopes, stony peaks and windswept hills.",
         "Où : prairies, bosquets, pentes enneigées, pics rocheux et collines venteuses."),
        ("Shrines on the way: prayer wheels, a waterfall, the bell cave (waystone), the wind-bridge to a needle "
         "pinnacle, the hermit's cell (look under the floor). A site of grace waits before the temple; the hall is "
         "the arena and the reward hangs over the cliff behind it. The way down: jump from its balcony into the pool.",
         "Des sanctuaires en chemin : les moulins à prières, la cascade, la grotte de la cloche (pierre de passage), "
         "le pont du vent vers une aiguille, la cellule de l'ermite (regarde sous le plancher). Un lieu de grâce "
         "précède le temple ; la salle est l'arène et le trésor est suspendu au-dessus de la falaise derrière elle. "
         "Pour redescendre : saute de son balcon dans le bassin."),
    ], []),
    ("caldera_ringwall", "wonders", "minecraft:lodestone", ("Caldera Ringwall", "Le Rempart de la caldeira"), [
        ("A dead volcano 250 blocks across whose crater rim carries a sixteen-sided curtain wall with red-roofed "
         "towers; in the crater lake a needle of rock rises, crowned by a keep with a copper spire.",
         "Un volcan éteint de 250 blocs de large dont la crête porte une enceinte à seize pans et des tours à toits "
         "rouges ; au milieu du lac de cratère se dresse une aiguille de roche couronnée d'un donjon à flèche de "
         "cuivre."),
        ("Where: meadows, groves, snowy slopes, stony peaks and windswept hills.",
         "Où : prairies, bosquets, pentes enneigées, pics rocheux et collines venteuses."),
        ("From the camp (waystone) the road reaches the barbican and the gatehouse, whose grand stair climbs to the "
         "gate court and its site of grace. Walk the ramparts from tower to tower (armoury bastion, barracks) to the "
         "north court (site of grace, great hall), then go down into the undercroft: cistern, prison (a secret below "
         "the last cell) and the arcade where a bridge crosses the lake to the needle. Its stair climbs to the keep "
         "(site of grace) and the arena on the summit; the vault lies behind sealed bars, and the way down is a leap "
         "into the lake. Shortcuts: one-way iron doors in the towers, a ladder under a hatch, the water gate.",
         "Depuis le camp (pierre de passage), la route mène à la barbacane et au châtelet, dont le grand escalier "
         "monte à la cour de la porte et à son lieu de grâce. Suis le chemin de ronde de tour en tour (bastion de "
         "l'arsenal, caserne) jusqu'à la cour du nord (lieu de grâce, grande salle), puis descends aux souterrains : "
         "la citerne, la prison (un secret sous la dernière cellule) et la galerie d'où un pont franchit le lac "
         "jusqu'à l'aiguille. Son escalier monte au donjon (lieu de grâce) et à l'arène au sommet ; le caveau est "
         "derrière des barreaux scellés, et pour redescendre on saute dans le lac. Raccourcis : portes de fer à sens "
         "unique dans les tours, une échelle sous une trappe, la poterne d'eau."),
    ], []),
    ("tidal_abbey", "wonders", "minecraft:prismarine_bricks", ("Tidal Abbey", "Abbaye des marées"), [
        ("A rocky tidal island off the shore: ring walls with seven towers and a sea gate, a town of stone houses "
         "with slate roofs spiralling up the rock, and on the summit a gothic abbey whose spire tops out at 130 "
         "blocks. A stone causeway leads there, half drowned and broken in the middle.",
         "Une île rocheuse cernée par la marée : des remparts à sept tours et une porte sur la mer, une ville de "
         "maisons de pierre aux toits d'ardoise qui monte en spirale autour du rocher, et au sommet une abbaye "
         "gothique dont la flèche culmine à 130 blocs. Une chaussée de pierre y mène, à demi noyée et rompue en son "
         "milieu."),
        ("Where: beaches and stony shores, with the sea on one side.",
         "Où : plages et rivages rocheux, la mer d'un côté."),
        ("Follow the Grande Rue from the King's Gate (waystone in the court) past the well square and the parish "
         "church to the Chatelet and the Grand Degre. Up top: the nave, the treasury behind the altar, the cloister "
         "(look down the well), the knights' hall. The stair tower goes down to the crypt and its site of grace; "
         "beyond is the tidal hall, the arena, then the vault and a tunnel out to the harbour.",
         "Suis la Grande Rue depuis la porte du Roi (pierre de passage dans la cour), par la place du puits et "
         "l'église paroissiale, jusqu'au Châtelet et au Grand Degré. En haut : la nef, le trésor derrière l'autel, "
         "le cloître (regarde au fond du puits), la salle des chevaliers. La tour d'escalier descend à la crypte et "
         "à son lieu de grâce ; au-delà, la salle des marées, l'arène, puis le caveau et un tunnel qui ressort au "
         "port."),
    ], []),
    ("inverted_spire", "wonders", "minecraft:iron_chain", ("Inverted Spire", "La Flèche renversée"), [
        ("A gothic tower built downward into a 110-block sinkhole. From the surface: a crowned ring of pinnacles round "
         "a black hole, four giant chains and a copper lantern spire. Where: plains, meadows, forests, taiga, savanna.",
         "Une tour gothique bâtie vers le bas dans un gouffre de 110 blocs. En surface : un anneau de pinacles autour "
         "d'un trou noir, quatre chaînes géantes et une flèche-lanterne de cuivre. Où : plaines, prairies, forêts, "
         "taïga, savane."),
        ("Cross to the crown court (waystone) and take the spiral ramp down: each landing leads through a ring room "
         "(library, refectory, inverted chapel, root crypt, the unmaking, the tip sanctum). Bridges reach the shaft "
         "wall: the quarry stair back to the rim, the ossuary (site of grace), the reliquary. At the bottom, a lake, "
         "the arena on its island and the vault; bubble lifts carry you back up.",
         "Passe le pont jusqu'à la cour de la couronne (pierre de passage) et descends la rampe en spirale : chaque "
         "palier traverse une salle en anneau (bibliothèque, réfectoire, chapelle renversée, crypte des racines, la "
         "défaite, le sanctuaire de la pointe). Des ponts mènent à la paroi : l'escalier de la carrière vers le "
         "rebord, l'ossuaire (lieu de grâce), le reliquaire. Au fond, un lac, l'arène sur son île et le caveau ; des "
         "ascenseurs à bulles te remontent."),
    ], []),
    ("dreadnought_wreck", "wonders", "brasshaven:dark_iron_plating",
     ("The Leviathan Dreadnought Wreck", "L'Épave du cuirassé Léviathan"), [
        ("A 180-block brass-and-iron steam ironclad lies aground on an ocean reef, broken in two: the bow tilted "
         "and half-drowned, the stern upright with its bridge tower, tripod mast, three funnels (one toppled) and "
         "four great turrets. Where: deep and warm oceans.",
         "Un cuirassé à vapeur de laiton et de fer de 180 blocs gît sur un récif, brisé en deux : la proue inclinée "
         "et à demi noyée, la poupe droite avec sa passerelle, son mât tripode, trois cheminées (dont une couchée) "
         "et quatre grandes tourelles. Où : océans profonds et chauds."),
        ("From the castaways' camp on the reef islet (waystone), cross the plank bridge over the breach. Enter "
         "the stern through the hull breach: crew quarters, officers' mess, the magazine and its hoist. Climb "
         "through the engine room (site of grace) and the upper-deck cabins (site of grace) to the captain's "
         "cabin; the drowned torpedo deck waits in the bow. Past the mist, the boiler hall is the boss arena; "
         "behind sealed bars, the strongroom, and the ammunition hoist ladder whose iron door leads back to the deck.",
         "Depuis le campement des naufragés sur l'îlot (pierre de passage), franchis la brèche par la passerelle de "
         "planches. On entre dans la poupe par la déchirure de la coque : poste d'équipage, carré des officiers, "
         "soute à munitions et son monte-charge. On traverse la salle des machines (lieu de grâce) et les cabines "
         "du pont supérieur (lieu de grâce) jusqu'à la cabine du capitaine ; le pont des torpilles noyé attend "
         "dans la proue. Passé la brume, la chaufferie est l'arène du boss ; derrière des barreaux scellés, la "
         "chambre forte, et l'échelle du monte-charge dont la porte de fer ramène au pont."),
    ], []),
    ("great_aqueduct", "wonders", "minecraft:cut_sandstone", ("The Great Aqueduct", "Le Grand Aqueduc"), [
        ("A 240-block sandstone aqueduct crosses a river valley on three tiers of arches (12, 8 and 4 wide), "
         "the water channel on top and a castellum on the eastern ridge. Where: plains, meadows, savannas.",
         "Un aqueduc de grès de 240 blocs franchit une vallée sur trois rangs d'arcades (12, 8 et 4 blocs), le "
         "canal au sommet et un castellum sur la crête est. Où : plaines, prairies, savanes."),
        ("From the valley waystone, the ridge road climbs to the spring house (site of grace). Follow the towpath "
         "to the breach and the sluice-keeper's house, climb into the maintenance gallery inside the piers (lamp "
         "room: site of grace) and on to the castellum. A stair descends to the antechamber and the arena in the "
         "great cistern; behind sealed bars, the vault, and a drain tunnel back to the valley.",
         "Depuis la pierre de la vallée, la route de la crête monte à la maison de la source (lieu de grâce). Le "
         "chemin de halage mène à la brèche et à la maison du gardien des vannes ; on monte dans la galerie "
         "d'entretien des piles (salle des lampes : lieu de grâce) jusqu'au castellum. Un escalier descend à "
         "l'antichambre et à l'arène de la grande citerne ; derrière des barreaux scellés, le caveau, et un tunnel "
         "de vidange qui ramène à la vallée."),
    ], []),
    ("sun_ziggurat", "wonders", "minecraft:sunflower", ("Sun-Engine Ziggurat", "La Ziggourat du Moteur solaire"), [
        ("A seven-stepped sandstone pyramid 140 blocks wide, crowned by a colossal brass orrery whose amber "
         "sun-lens focuses daylight down a shaft through the core. Where: open desert.",
         "Une pyramide de grès à sept degrés, large de 140 blocs, couronnée d'un colossal planétaire de laiton dont "
         "la lentille d'ambre concentre le jour dans un puits au cœur. Où : désert ouvert."),
        ("From the waystone camp, an avenue of sphinxes leads to the processional ramp and the pylon gate. The "
         "hypostyle hall of 25 columns is a site of grace; the sand-flooded lower halls lie below. Climb through "
         "the astronomer-priests' quarter and the terraces to the lens-calibration chamber, pass the sealed tomb "
         "gallery, and descend the annex to the antechamber (site of grace). Through the mist, the sun chamber "
         "under the lens is the arena; behind sealed bars, the vault and a lift down the core back to the halls.",
         "Depuis le campement et sa pierre, une allée de sphinx mène à la rampe processionnelle et au pylône. La "
         "salle hypostyle de 25 colonnes est un lieu de grâce ; les salles basses ensablées sont dessous. On monte "
         "par le quartier des prêtres-astronomes et les terrasses jusqu'à la chambre de calibrage de la lentille, "
         "on passe la galerie des tombeaux scellés et l'on descend l'annexe jusqu'à l'antichambre (lieu de grâce). "
         "Passé la brume, la chambre du soleil sous la lentille est l'arène ; derrière des barreaux scellés, le "
         "caveau et un ascenseur qui redescend par le cœur jusqu'aux salles basses."),
    ], []),
    ("kneeling_gate", "wonders", "minecraft:bell", ("Kneeling Gate", "La Porte agenouillée"), [
        ("Two 70-block stone knights kneel across a mountain pass, a stone lintel held between their gauntlets "
         "over a toll town. Where: meadows, groves, snowy slopes, stony peaks, windswept hills.",
         "Deux chevaliers de pierre de 70 blocs agenouillés de part et d'autre d'un col portent un linteau au-dessus "
         "d'un bourg de péage. Où : prairies, bosquets, pentes enneigées, pics pierreux, collines venteuses."),
        ("From the west guard-house a stair climbs the body (girdle hall, heart chamber, helm) and out along the "
         "arm onto the lintel: site of grace in the keystone pavilion. Down the east knight: treasury, drop well, "
         "an iron door to the square, and a stair to the arena under the gate and its sealed vault.",
         "Depuis le corps de garde ouest, un escalier monte dans le corps (ceinture, cœur, heaume) puis par le "
         "bras jusqu'au linteau : lieu de grâce dans le pavillon. Dans le chevalier est : trésor, puits, porte de "
         "fer sur la place, et l'escalier de l'arène sous la porte et de son caveau scellé."),
    ], []),
    ("drowned_dam", "wonders", "brasshaven:valve_wheel", ("Dam of the Drowned Valley", "Barrage de la vallée engloutie"), [
        ("A curved stone-and-brass arch dam 170 blocks long and 66 high closes a horseshoe of rock; behind it a lake "
         "has drowned a village whose bell tower still breaks the surface. Where: meadows, windswept hills, taigas, "
         "forests.",
         "Un barrage-voûte de pierre et de laiton long de 170 blocs et haut de 66 ferme un fer à cheval de roche ; "
         "derrière lui un lac a noyé un village dont le clocher perce encore la surface. Où : prairies, collines "
         "venteuses, taïgas, forêts."),
        ("From the works yard, Generator Hall I and the west tower's stair lead to the berm, the valve house and "
         "its drowned gallery, then the control tower (site of grace at the crest). Along the crest to the east "
         "tower, down to Generator Hall II (site of grace) and the turbine chamber: the arena and its sealed vault. "
         "Shortcuts: the lift shaft, the spillway drop, one-way iron doors.",
         "Depuis la cour des travaux, la salle des génératrices I et l'escalier de la tour ouest mènent à la "
         "risberme, à la maison des vannes et sa galerie noyée, puis à la tour de contrôle (lieu de grâce au "
         "sommet). Par le couronnement jusqu'à la tour est, on redescend à la salle II (lieu de grâce) et à la "
         "salle des turbines : l'arène et son caveau scellé. Raccourcis : le puits d'ascenseur, le déversoir, "
         "les portes de fer à sens unique."),
    ], []),
    ("glacier_hall", "wonders", "minecraft:packed_ice", ("Glacier Hall of the Frost Jarls", "Halle glaciaire des jarls"), [
        ("A glacier tongue 200 blocks long whose snout is carved into a facade: a frieze, the Jarl's eye, two "
         "34-block jarl statues and an arched gate under a longhouse roof ridge breaking through the ice, with a "
         "126-block rock horn rising on the east side.",
         "Une langue de glacier longue de 200 blocs dont le front est taillé en façade : une frise, l'œil du jarl, "
         "deux statues de jarls de 34 blocs et une porte en arc sous l'arête d'un toit de longhouse qui perce la "
         "glace ; à l'est se dresse une corne de roche de 126 blocs."),
        ("Where: snowy plains, ice spikes, snowy taiga, groves and snowy slopes.",
         "Où : plaines enneigées, pics de glace, taïga enneigée, bosquets et pentes enneigées."),
        ("Through the gate (waystone on the terrace) lies the ice nave with its ribs and frozen warriors; the "
         "crossing has a second waystone. Side rooms: guard room, mead store, armoury, kitchens, the skald's "
         "library, the frozen warriors' hall and the huscarls' sleeping hall. Past the throne apse a bridge crosses "
         "the crevasse (it is broken: jump the gap or drop to the lake), then the Jarl's stair climbs into the horn "
         "to the site of grace and the arena. Beyond: the vault, and the Jarl's Leap, a 47-block plunge into the "
         "spring that the meltwater river carries out through an ice cave in the snout.",
         "Passé la porte (pierre de passage sur la terrasse), la nef de glace, ses côtes et ses guerriers gelés ; "
         "la croisée a une seconde pierre de passage. Autour : la salle des gardes, la cave à hydromel, "
         "l'armurerie, les cuisines, la bibliothèque du scalde, la salle des guerriers gelés et le dortoir des "
         "huscarls. Après l'abside du trône, un pont franchit la crevasse (il est rompu : saute la brèche ou tombe "
         "dans le lac), puis l'escalier du jarl monte dans la corne jusqu'au lieu de grâce et à l'arène. Au-delà : "
         "le caveau, et le Saut du jarl, 47 blocs de chute dans la source que la rivière de fonte emporte jusqu'à "
         "une grotte de glace au front du glacier."),
    ], []),
    ("canopy_city", "wonders", "minecraft:jungle_log", ("Canopy Temple-City", "La Cité-temple de la canopée"), [
        ("A lost city 220 blocks across: a 66-high stepped temple strangled by roots, ringed by five colossal hollow "
         "trunks whose platform districts are joined by rope bridges and brass zip-lines. Where: jungles.",
         "Une cité perdue de 220 blocs : un temple à degrés de 66 blocs étranglé par les racines, entouré de cinq "
         "troncs colossaux et creux dont les quartiers sont reliés par des ponts de corde et des tyroliennes de "
         "laiton. Où : jungles."),
        ("From the explorers' camp and its waystone, climb the trunks' spiral stairs to the market (site of grace) "
         "and the high ward, and cross to the temple's upper terrace. Inside, descend through the glyph library, "
         "the dart-trap corridor, the jade-and-gold sanctum (site of grace), the offering hall and the "
         "root-choked crypt to the flooded cenote and its waterfall; its spiral ledge climbs back to a site of "
         "grace (iron door to the library) and the summit stair. Through the mist, the arena under the broken brass sun-disc; behind sealed bars, the "
         "vault. A one-way iron door leads to the east trunk, whose brass elevator is the shortcut down.",
         "Depuis le campement et sa pierre, on monte par les escaliers en spirale des troncs jusqu'au marché (lieu "
         "de grâce) et au quartier haut, puis on passe sur la terrasse supérieure du temple. Dedans, on descend "
         "par la bibliothèque des glyphes, le couloir des fléchettes, le sanctuaire de jade et d'or (lieu de "
         "grâce), la salle des offrandes et la crypte envahie de racines jusqu'au cénote noyé et à sa cascade ; sa "
         "corniche en spirale remonte à un lieu de grâce (porte de fer vers la bibliothèque) et à l'escalier du "
         "sommet. Passé la brume, l'arène sous le disque "
         "solaire de laiton brisé ; derrière des barreaux scellés, le caveau. Une porte de fer à sens unique mène "
         "au tronc est, dont l'ascenseur de laiton est le raccourci vers le sol."),
    ], []),
    ("mire_stilt_city", "wonders", "minecraft:mangrove_roots", ("Mire Stilt-City", "La Cité des pilotis"), [
        ("A timber town on piles over a mangrove swamp, 200 blocks across: boardwalks on three levels, rope "
         "bridges, fishers' huts, a smoking smokehouse, a drowned bell tower, and the witch-queen's round hall raised "
         "34 blocks on a forest of stilts under a crooked witch's-hat roof that tops out at 100 blocks.",
         "Une ville de bois sur pilotis de 200 blocs au-dessus d'une mangrove : des passerelles sur trois niveaux, "
         "des ponts de corde, des huttes de pêcheurs, un fumoir qui fume, un clocher noyé, et la salle ronde de la "
         "reine-sorcière, haute de 34 blocs sur une forêt de pilotis, sous un toit en chapeau de sorcière tordu qui "
         "culmine à 100 blocs."),
        ("Where: swamps and mangrove swamps.", "Où : marais et mangroves."),
        ("From the islet (waystone) take the causeway through the palisade gate, cross the Eel Market and climb the "
         "Ladderhouse to the market square (waystone). West: the drowned bell tower, its belfry and the sunken "
         "undercroft (a hidden hoard, a tunnel out through a one-way iron door). East: the smokehouse and its stair to "
         "the High Walk, which leads round to the landing (site of grace) and the covered grand stair. Past the mist: "
         "the queen's hall, the vault behind the throne, and a trapdoor that drops 33 blocks into the queen's pool.",
         "Depuis l'îlot (pierre de passage), prends la chaussée, passe la porte de la palissade, traverse le marché "
         "aux anguilles et monte par la maison de l'escalier jusqu'à la place du marché (pierre de passage). À "
         "l'ouest : le clocher noyé, son beffroi et la crypte engloutie (un trésor caché, un tunnel qui ressort par "
         "une porte de fer à sens unique). À l'est : le fumoir et son escalier vers le chemin haut, qui mène au "
         "palier (lieu de grâce) et au grand escalier couvert. Passé la brume : la salle de la reine, le caveau "
         "derrière le trône, et une trappe qui plonge de 33 blocs dans le bassin de la reine."),
    ], []),
    ("shattered_halo", "wonders", "minecraft:end_crystal", ("Shattered Halo", "Halo brisé"), [
        ("A tilted ring of purpur, end stone bricks and gold, 170 blocks across, broken into five arcs floating at "
         "different heights over the void of the End, with a temple on each arc and the boss on a disc at the centre.",
         "Un anneau incliné de purpur, de briques de pierre de l'End et d'or, large de 170 blocs, brisé en cinq arcs "
         "qui flottent à des hauteurs différentes au-dessus du vide de l'End, avec un temple sur chaque arc et le "
         "boss sur un disque au centre."),
        ("Where: the outer islands of the End (highlands, midlands, barrens, small islands), over open void.",
         "Où : les îles extérieures de l'End (hautes terres, terres moyennes, terres arides, petites îles), "
         "au-dessus du vide."),
        ("Arrive on the outer islet (waystone); the bridges set the order: the Observatory, a light bridge to the "
         "Library of the Void, stepping islets to the Reliquary (a trapdoor hides a crypt), an arched bridge to the "
         "Bell Shrine, a light bridge down to the Gate. The radial bridge leads to a site of grace, then to the arena. "
         "A fall off a walkway means the void: bring ender pearls and slow falling.",
         "On arrive sur l'îlot extérieur (pierre de passage) ; les ponts imposent l'ordre : l'Observatoire, un pont "
         "de lumière jusqu'à la Bibliothèque du vide, des îlots-gués jusqu'au Reliquaire (une trappe cache une "
         "crypte), un pont en arc jusqu'au Sanctuaire des cloches, un pont de lumière qui descend à la Porte. Le pont "
         "rayonnant mène à un lieu de grâce, puis à l'arène. Une chute, c'est le vide : prends des perles de l'Ender "
         "et de la chute lente."),
    ], []),
    ("iron_helmsman", "wonders", "brasshaven:remembrance_iron_helmsman", ("The Iron Helmsman", "Le Timonier de Fer"), [
        ("The pilot of the Walking Fortress waits on its open top deck (450 health, armour 15): a hulking captain "
         "fused into a steam harness, a harpoon-cannon for an arm and an anchor dragged on a chain. Bring your best "
         "gear: he is the hardest boss of the Overworld.",
         "Le pilote de la Forteresse marchante attend sur son pont supérieur à ciel ouvert (450 PV, armure 15) : un "
         "capitaine colossal soudé à un harnais à vapeur, un canon-harpon pour bras et une ancre traînée au bout "
         "d'une chaîne. Viens avec ton meilleur équipement : c'est le boss le plus dur de la Surface."),
        ("He sweeps and slams the anchor (jump the shockwave), fires a harpoon that reels you in before a sweep, "
         "charges, and when his boiler hisses and a ring of steam appears, get out of it: the steam scalds.",
         "Il balaie et abat son ancre (saute l'onde de choc), tire un harpon qui te ramène vers lui avant un "
         "balayage, charge, et quand sa chaudière siffle et qu'un cercle de vapeur apparaît, sors-en : la vapeur "
         "brûle."),
    ], ["brasshaven:remembrance_iron_helmsman", "brasshaven:helmsman_anchor"]),
    ("iron_helmsman_broadside", "wonders", "minecraft:tnt", ("Helmsman: broadside", "Timonier : bordée"), [
        ("At half health he goes full steam: his boiler overloads (rings of fire burst out of the deck), he whirls "
         "the anchor on its chain while walking you down, and he raises his cannon to call the walker's guns: "
         "shells land where you stand. Move as soon as a ring of smoke appears under you.",
         "À mi-vie, il passe à toute vapeur : sa chaudière surchauffe (des anneaux de feu jaillissent du pont), il "
         "fait tournoyer l'ancre au bout de sa chaîne en marchant sur toi, et il lève son canon pour appeler les "
         "pièces du marcheur : les obus tombent là où tu te tiens. Bouge dès qu'un cercle de fumée apparaît sous toi."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Helmsman's Anchor, a heavy weapon whose "
         "right-click sends a broadside of fiery bursts down the line ahead.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent l'Ancre du Timonier, une arme lourde dont "
         "le clic droit envoie une bordée d'explosions enflammées sur la ligne devant toi."),
    ], []),
    ("bronze_sentinel", "wonders", "brasshaven:remembrance_bronze_sentinel", ("The Bronze Sentinel", "La Sentinelle d'airain"), [
        ("The living guardian of the Fallen Colossus waits inside the statue's helm (460 health, armour 14): a "
         "knight automaton of stone and verdigris bronze, a tower shield on one arm and a long greatsword in the "
         "other, its broken visor glowing gold.",
         "Le gardien vivant du Colosse abattu attend dans le heaume de la statue (460 PV, armure 14) : un "
         "chevalier-automate de pierre et de bronze vert-de-gris, un pavois à un bras et un long espadon à l'autre, "
         "sa visière brisée luisant d'or."),
        ("It bashes with the shield, brings the greatsword down (a crack runs on along the ground), sweeps wide and "
         "stamps (jump the ring). When it plants its shield, frontal blows bounce off: walk round and strike its back.",
         "Il frappe du pavois, abat l'espadon (une fissure court ensuite au sol), fauche large et piétine (saute "
         "l'onde). Quand il plante son pavois, les coups de face rebondissent : contourne-le et frappe dans le dos."),
    ], ["brasshaven:remembrance_bronze_sentinel", "brasshaven:sentinel_greatsword"]),
    ("bronze_sentinel_unplated", "wonders", "minecraft:oxidized_copper", ("Sentinel: plates fallen", "Sentinelle : plaques tombées"), [
        ("At half health its plates fall away and it gets faster: a whirling blade dance, a leap that lands on the "
         "golden circle marked where you stood, and lines of rune light drawn across the floor (step aside before "
         "they flare).",
         "À mi-vie, ses plaques tombent et il accélère : une danse des lames tournoyante, un bond qui retombe sur le "
         "cercle doré tracé là où tu étais, et des lignes de lumière runique dessinées au sol (fais un pas de côté "
         "avant qu'elles flamboient)."),
        ("Its Remembrance, four Map Fragments and two diamonds forge the Greatsword of the Sentinel, whose "
         "right-click tears a crack of rune light along the line ahead.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent l'Espadon de la Sentinelle, dont le clic "
         "droit déchire une fissure de lumière runique sur la ligne devant toi."),
    ], []),
    ("dune_king", "wonders", "brasshaven:remembrance_dune_king", ("The Dune King", "Le Roi des dunes"), [
        ("At the bottom of the Necropolis of Kings, the undead pharaoh waits in his arena (460 health): a mummy "
         "king under a double crown, crook and flail in hand, four canopic jars circling him.",
         "Tout en bas de la Nécropole des rois, le pharaon mort-vivant attend dans son arène (460 PV) : un roi "
         "momifié sous la double couronne, la crosse et le fléau en main, quatre vases canopes tournant autour de lui."),
        ("He lashes with the flail, hooks you in with the crook, blows a cone of blinding sand, raises husks from "
         "the floor and makes his jars spit curse bolts: keep moving sideways.",
         "Il frappe du fléau, t'attire avec sa crosse, souffle un cône de sable aveuglant, fait sortir des husks du "
         "sol et fait cracher à ses vases des traits de malédiction : déplace-toi de côté."),
    ], ["brasshaven:remembrance_dune_king", "brasshaven:dune_king_crook"]),
    ("dune_king_risen", "wonders", "minecraft:sand", ("Dune King: risen", "Roi des dunes : l'élévation"), [
        ("At half health he rises and floats: pools of quicksand open in spirals across the floor, rings of "
         "scarabs roll out (jump them) and a low beam of judgement sweeps the arena from his left to his right: "
         "jump it as it passes or get behind him.",
         "À mi-vie, il s'élève et flotte : des fosses de sable mouvant s'ouvrent en spirales, des anneaux de "
         "scarabées roulent vers toi (saute-les) et un rayon bas de jugement balaie l'arène de sa gauche à sa "
         "droite : saute-le quand il passe ou mets-toi dans son dos."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Crook of the Dune King, a staff whose "
         "right-click lances a beam of judgement that slows foes.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Crosse du Roi des dunes, un bâton dont "
         "le clic droit lance un rayon de jugement qui ralentit les ennemis."),
    ], []),
    ("fallen_seraph", "wonders", "brasshaven:remembrance_fallen_seraph", ("The Fallen Seraph", "Le Séraphin déchu"), [
        ("At the centre of the Shattered Halo, on the disc floating over the void, the fallen seraph waits (780 "
         "health, armour 14): an angel hovering under a broken golden halo, one wing white and gold, the other burnt "
         "to the void, a glaive with a crescent blade, six halo shards circling her.",
         "Au centre du Halo brisé, sur le disque suspendu au-dessus du vide, attend la séraphine déchue (780 PV, "
         "armure 14) : un ange qui flotte sous un halo d'or brisé, une aile blanche et dorée, l'autre brûlée par le "
         "vide, un glaive à lame en croissant, six éclats de halo qui tournent autour d'elle."),
        ("She sweeps with the glaive, glides along a line of light, flings her shards one by one, drops lances of "
         "light into rings under you and vanishes to reappear at the edge of the disc (watch for the violet ring). "
         "None of her blows throws you toward the void near the rim.",
         "Elle balaie de son glaive, glisse le long d'une ligne de lumière, lance ses éclats un à un, fait tomber des "
         "lances de lumière dans des cercles sous toi et disparaît pour surgir au bord du disque (guette l'anneau "
         "violet). Aucun de ses coups ne te projette vers le vide près du bord."),
    ], ["brasshaven:remembrance_fallen_seraph", "brasshaven:halo_glaive"]),
    ("fallen_seraph_shattered", "wonders", "minecraft:end_crystal", ("Seraph: the disc breaks", "Séraphin : le disque se brise"), [
        ("At 60% her halo blazes: a blinding beam sweeps from her left to her right (stay under her or behind her) "
         "and rings of light roll out and back (jump both). At 25% she shatters the disc: fissures flare in turn, "
         "the rim beyond the gold ring crumbles, shards rain from the sky and she dives on the gold ring that "
         "follows you.",
         "À 60 %, son halo flamboie : un rayon aveuglant balaie de sa gauche à sa droite (reste sous elle ou dans "
         "son dos) et des anneaux de lumière roulent aller et retour (saute les deux). À 25 %, elle brise le "
         "disque : les fissures jaillissent tour à tour, le bord au-delà de l'anneau d'or s'effrite, des éclats "
         "tombent du ciel et elle plonge sur le cercle doré qui te suit."),
        ("Her Remembrance, four Void Shards and two diamonds forge the Glaive of the Broken Halo, whose right-click "
         "flings a fan of five piercing halo shards that blind foes.",
         "Son Souvenir, quatre éclats du vide et deux diamants forgent le Glaive du Halo brisé, dont le clic droit "
         "lance un éventail de cinq éclats de halo perçants qui aveuglent les ennemis."),
    ], []),
    ("chained_jailer", "wonders", "brasshaven:remembrance_chained_jailer", ("The Chained Jailer", "Le Geôlier enchaîné"), [
        ("The warden of the Chained Bastion waits in the boss drum over the lava (600 health, armour 14): a hunched "
         "giant of blackstone and gilded iron, his head a locked cage full of fire, a padlock for a heart, a burning "
         "fetter-ball dragged on a chain. Bring fire resistance.",
         "Le geôlier du Bastion enchaîné attend dans le tambour au-dessus de la lave (600 PV, armure 14) : un géant "
         "voûté de pierre noire et de fer doré, la tête dans une cage verrouillée pleine de feu, un cadenas pour "
         "cœur, un boulet enflammé traîné au bout d'une chaîne. Prends de la résistance au feu."),
        ("He lashes the ball across his front, hurls his chain to drag you in, slams both fists (jump the ring of "
         "fire), kicks huggers away and makes chains burst from the floor under you: step out of the iron rings.",
         "Il balaie devant lui avec le boulet, lance sa chaîne pour te traîner, frappe des deux poings (saute "
         "l'anneau de feu), repousse qui le colle d'un coup de pied et fait jaillir des chaînes du sol sous toi : "
         "sors des cercles de fer."),
    ], ["brasshaven:remembrance_chained_jailer", "brasshaven:jailer_chain"]),
    ("chained_jailer_unchained", "wonders", "minecraft:iron_chain", ("Jailer: unchained", "Geôlier : libéré"), [
        ("At 60% he spins the ball round him and drives his fists into the floor: fire runs out along eight bars, "
         "stand between them. At 30% he kneels, tears his own chains apart (a ring of fire to jump) and from then "
         "on burns whoever stays close and casts the verdict: three volleys of chains on every player.",
         "À 60 %, il fait tourner le boulet autour de lui et plante ses poings dans le sol : le feu court le long de "
         "huit barreaux, tiens-toi entre eux. À 30 %, il s'agenouille, brise ses propres chaînes (un anneau de feu "
         "à sauter), puis brûle qui reste près de lui et lance le verdict : trois salves de chaînes sur chaque "
         "joueur."),
        ("His Remembrance, four Ancient Embers and two diamonds forge the Jailer's Burning Chain, whose right-click "
         "hurls a chain that drags the first foe to your feet and sets it ablaze.",
         "Son Souvenir, quatre braises anciennes et deux diamants forgent la Chaîne ardente du Geôlier, dont le clic "
         "droit lance une chaîne qui traîne le premier ennemi à tes pieds et l'embrase."),
    ], []),
    ("caldera_castellan", "wonders", "brasshaven:remembrance_caldera_castellan", ("The Castellan of the Caldera", "Le Châtelain de la caldeira"), [
        ("The lord of the Caldera Ringwall waits in the open court on the summit of the needle in the crater lake (520 "
         "health, armour 15): a towering lord in basalt plate split by cracks of cooling magma, a crater of obsidian "
         "spikes on his helm, a smoking volcano for a right pauldron and a great halberd.",
         "Le seigneur du Rempart de la caldeira attend dans la cour à ciel ouvert, au sommet de l'aiguille du lac de "
         "cratère (520 PV, armure 15) : un seigneur immense en armure de basalte fendue de magma qui refroidit, un "
         "cratère de pointes d'obsidienne sur le heaume, un volcan fumant pour épaulière droite et une grande hallebarde."),
        ("He sweeps the halberd across his front, cleaves down a glowing line, charges with the halberd levelled, "
         "leaps onto the ring of embers that follows you (a lava crack runs on from the landing: step off its line) "
         "and stamps when you hug him.",
         "Il balaie devant lui avec la hallebarde, fend le sol le long d'une ligne ardente, charge hallebarde baissée, "
         "bondit sur le cercle de braises qui te suit (une faille de lave court ensuite depuis l'impact : écarte-toi "
         "de sa ligne) et piétine qui le colle."),
    ], ["brasshaven:remembrance_caldera_castellan", "brasshaven:caldera_halberd"]),
    ("caldera_castellan_heat", "wonders", "minecraft:magma_block", ("Castellan: walls and vents", "Châtelain : murs et cheminées"), [
        ("At 60% he raises walls of obsidian from the floor, a corridor round you (he charges down it) or a pen (he "
         "leaps in): get out through the open side. A charge into his own wall breaks it and leaves him reeling. At "
         "30% he draws the volcano's heat, and every ten seconds the floor vents erupt in patterns (rings, spirals, a "
         "checker, vents under your feet), each warned by smoke and dripping lava. After venting, his armour is "
         "brittle for three seconds: strike then. The walls always crumble.",
         "À 60 %, il fait surgir du sol des murs d'obsidienne, un couloir autour de toi (il le charge) ou un enclos (il "
         "bondit dedans) : sors par le côté ouvert. Une charge dans son propre mur le brise et le laisse sonné. À "
         "30 %, il puise la chaleur du volcan, et toutes les dix secondes les cheminées du sol entrent en éruption en "
         "motifs (anneaux, spirales, damier, sous tes pieds), chacune annoncée par de la fumée et des gouttes de lave. "
         "Après l'éruption, son armure est fragile trois secondes : frappe alors. Les murs s'effondrent toujours."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Halberd of the Caldera, whose right-click "
         "opens a molten rift that runs ahead and forks, searing and slowing every foe on it.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Hallebarde de la caldeira, dont le clic "
         "droit ouvre une faille de magma qui court devant toi et se divise, brûlant et ralentissant tous les ennemis "
         "dessus."),
    ], []),
    ("frost_jarl", "wonders", "brasshaven:remembrance_frost_jarl", ("The Frost Jarl", "Le Jarl de givre"), [
        ("At the top of the Jarl's Stair in the horn behind the Glacier Hall, the dead king waits under the dome (540 "
         "health, armour 14): a Norse giant frozen on his feet, a bearded axe of blue ice in his right hand, a round "
         "shield crusted with frost on his left arm, a beard of hoarfrost. His shield turns blows that come from in "
         "front while he walks: strike during his recoveries or from the side.",
         "En haut de l'escalier du Jarl, dans la corne derrière la Halle glaciaire, le roi mort attend sous le dôme "
         "(540 PV, armure 14) : un géant nordique gelé debout, une hache barbue de glace bleue dans la main droite, "
         "un bouclier rond couvert de givre au bras gauche, une barbe de frimas. Son bouclier pare les coups portés "
         "de face quand il marche : frappe pendant qu'il se reprend, ou par le flanc."),
        ("He cleaves across his front, bashes with the shield (it knocks a raised shield aside), sweeps a cone of ice "
         "breath from his right to his left, drives his axe into the floor so ice spikes run out along a line, leaps "
         "onto the ring that follows you (jump the frost wave) and calls up his frozen huscarls.",
         "Il fend devant lui, frappe du bouclier (il écarte un bouclier levé), balaie un cône de souffle de glace de "
         "sa droite vers sa gauche, plante sa hache dans le sol pour faire courir une ligne de pics de glace, bondit "
         "sur le cercle qui te suit (saute l'onde de givre) et appelle ses huscarls gelés."),
    ], ["brasshaven:remembrance_frost_jarl", "brasshaven:jarl_axe"]),
    ("frost_jarl_winter", "wonders", "minecraft:blue_ice", ("Jarl: Fimbulwinter", "Jarl : Fimbulvetr"), [
        ("At 65% he strikes three times in a row and makes rings of spikes burst out from his axe: stand in a gap "
         "between the rings. At 30% he kneels and freezes the hall: keep moving (standing still freezes you), jump "
         "when the floor whitens, and every 13 s a blizzard rains ice spikes on everyone.",
         "À 65 %, il frappe trois fois de suite et fait jaillir des anneaux de pics autour de sa hache : tiens-toi "
         "entre deux anneaux. À 30 %, il s'agenouille et gèle la salle : ne reste pas immobile (le froid te saisit), "
         "saute quand le sol blanchit, et toutes les 13 s un blizzard fait pleuvoir des pics de glace sur tous."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Bearded Axe of the Frost Jarl, whose "
         "right-click breathes a cone of frost that freezes foes solid.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Hache barbue du Jarl de givre, dont le "
         "clic droit souffle un cône de givre qui gèle les ennemis sur place."),
    ], []),
    ("tide_abbess", "wonders", "brasshaven:remembrance_tide_abbess", ("The Abbess of the Tides", "L'Abbesse des Marées"), [
        ("Down the narrow stair under the Tidal Abbey's church, in the rotunda lit by shafts of sea light, the drowned "
         "abbess waits (560 health, armour 12): a tall saint in a barnacled chasuble and a veil crowned with coral, a "
         "nautilus crozier in her right hand and a bell-censer swinging from her left.",
         "En bas de l'escalier étroit sous l'église de l'Abbaye des marées, dans la rotonde éclairée de puits de "
         "lumière marine, attend l'abbesse noyée (560 PV, armure 12) : une sainte élancée en chasuble couverte de "
         "bernacles, un voile couronné de corail, une crosse-nautile dans la main droite et un encensoir-cloche "
         "balancé dans la gauche."),
        ("She sweeps with the crozier, swings the censer (its brine smoke lingers: leave it), glides down a line of "
         "bubbles, tolls the bell to draw everyone in before the brine bursts round her (run against the pull), and "
         "strikes the floor to send a wall of water across the whole rotunda: it is too tall to jump, so stand in one "
         "of the gaps marked in sea glass. Her drowned acolytes rise every half minute.",
         "Elle balaie de sa crosse, lance l'encensoir (sa fumée de saumure reste : sors-en), glisse le long d'une "
         "ligne de bulles, sonne la cloche pour attirer tout le monde avant que la saumure n'éclate autour d'elle "
         "(cours contre l'attraction), et frappe le sol pour lancer un mur d'eau à travers toute la rotonde : trop "
         "haut pour être sauté, tiens-toi dans une des brèches marquées de verre marin. Ses acolytes noyés se lèvent "
         "toutes les trente secondes."),
    ], ["brasshaven:remembrance_tide_abbess", "brasshaven:abbess_crozier"]),
    ("tide_abbess_flood", "wonders", "minecraft:heart_of_the_sea", ("Abbess: the Flood", "Abbesse : le Déluge"), [
        ("At 65% a second wave crosses the first, geysers burst under every player and she swings the censer twice. "
         "At 30% she kneels and floods the rotunda: you wade, she swims, and every 12 s she dives into the riptide "
         "and swims through three marks. The water drains when she falls.",
         "À 65 %, une seconde vague croise la première, des geysers jaillissent sous chaque joueur et elle frappe "
         "deux fois de l'encensoir. À 30 %, elle s'agenouille et inonde la rotonde : tu patauges, elle nage, et "
         "toutes les 12 s elle plonge dans la lame de fond et traverse trois marques. L'eau se retire à sa chute."),
        ("Her Remembrance, four Map Fragments and two diamonds forge the Crozier of the Drowned Abbess, whose "
         "right-click sends a breaking wave ahead that sweeps foes along.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Crosse de l'Abbesse noyée, dont le clic "
         "droit lance une vague qui emporte les ennemis."),
    ], []),
    ("abyssal_architect", "wonders", "brasshaven:remembrance_abyssal_architect", ("The Abyssal Architect",
                                                                                  "L'Architecte de l'abîme"), [
        ("At the bottom of the Inverted Spire, on the island in the underground lake, the builder of the spire hangs "
         "from chains under its point and drops onto the island when you come (600 health, armour 12): a gaunt, "
         "four-armed priest in a slate cassock, a limestone mask with three soul-blue slits, a plumb-bob flail in one "
         "hand and a compass-blade in another.",
         "Au fond de la Flèche renversée, sur l'île du lac souterrain, le bâtisseur de la flèche pend à des chaînes "
         "sous sa pointe et se laisse tomber sur l'île à ton arrivée (600 PV, armure 12) : un prêtre décharné à "
         "quatre bras en soutane d'ardoise, un masque de calcaire fendu de trois fentes bleu d'âme, un fléau à fil à "
         "plomb dans une main et une lame-compas dans une autre."),
        ("His flail circles out to 8 blocks: hug him, the chalk ring at his feet is safe. The plumb-bob is hurled "
         "down a chalk line and reeled back along it (step off the line), stones fall from the vault on marks that "
         "follow you and leave rubble for a few seconds, and he swings across the arena on a chain to land on a "
         "ring.",
         "Son fléau tournoie jusqu'à 8 blocs : colle-toi à lui, l'anneau de craie à ses pieds est sûr. Le plomb est "
         "lancé le long d'une ligne de craie puis ramené le long de celle-ci (quitte la ligne), des pierres tombent de "
         "la voûte sur des marques qui te suivent et laissent des gravats quelques secondes, et il traverse l'arène "
         "pendu à une chaîne pour retomber sur un anneau."),
    ], ["brasshaven:remembrance_abyssal_architect", "brasshaven:architect_plumb"]),
    ("abyssal_architect_unmoored", "wonders", "minecraft:iron_chain", ("Architect: the Unmooring", "Architecte : le Désamarrage"), [
        ("At 65% he scribes a circle round his compass (outer ring first, then the inner disc), snuffs his lantern "
         "to blind everyone for 3 s (listen for his echoing steps and watch for soul-blue footprints, then roll when "
         "the blade snicks open) and drops a checkerboard of the vault in two halves. At 30% the island breaks up: "
         "tiles marked by cracks crumble into the lake for 5 s and rise again, and every 15 s he swings round the "
         "arena on the ceiling chains and dives three times. The island is whole again when he falls.",
         "À 65 %, il trace un cercle autour de son compas (l'anneau extérieur, puis le disque intérieur), souffle sa "
         "lanterne pour aveugler tout le monde 3 s (écoute ses pas qui résonnent, guette les empreintes bleu d'âme, "
         "puis roule quand la lame s'ouvre) et fait tomber un damier de la voûte en deux moitiés. À 30 %, l'île se "
         "disloque : les dalles marquées de fissures s'effondrent dans le lac 5 s puis remontent, et toutes les 15 s "
         "il tourne autour de l'arène pendu aux chaînes du plafond et plonge trois fois. L'île redevient entière à sa "
         "chute."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Plumb of the Abyssal Architect, whose "
         "right-click lets the plumb-bob fall on the spot you aim at, crushing and pinning foes.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Fil à plomb de l'Architecte de l'abîme, "
         "dont le clic droit laisse tomber le plomb sur le point visé, écrasant et clouant les ennemis."),
    ], []),
    ("lock_master", "wonders", "brasshaven:remembrance_lock_master", ("The Lock-Master", "Le Maître des écluses"), [
        ("Down the stair under the Great Aqueduct's castellum, in the great cistern under its dome of columns, the "
         "Lock-Master waits (600 health, armour 14): a hulking hydraulic warden in riveted brass, a whole sluice gate "
         "on his left arm and a pressure-lance longer than he is tall in his right.",
         "En bas de l'escalier sous le castellum du Grand Aqueduc, dans la grande citerne sous sa coupole à colonnes, "
         "attend le Maître des écluses (600 PV, armure 14) : un gardien hydraulique massif en laiton riveté, une "
         "vanne entière au bras gauche et une lance à pression plus longue que lui dans la droite."),
        ("His lance thrusts reach 9 blocks; anyone who lingers behind him gets the spin. When he walks behind his "
         "gate it blocks every frontal hit: break it with a heavy blow or strike his back, and he reels open. His "
         "jets sweep in front of him (hide behind a column), and gates of iron bars drop from the dome on the tiles "
         "marked in brass round every player.",
         "Ses coups de lance portent à 9 blocs ; qui s'attarde dans son dos prend le moulinet. Quand il avance "
         "derrière sa vanne, elle pare tout coup de face : brise-la d'un coup lourd ou frappe-le dans le dos, et il "
         "chancelle, ouvert. Ses jets balaient devant lui (cache-toi derrière une colonne), et des grilles de fer "
         "tombent de la coupole sur les dalles marquées de laiton autour de chaque joueur."),
    ], ["brasshaven:remembrance_lock_master", "brasshaven:pressure_lance"]),
    ("lock_master_flush", "wonders", "minecraft:piston", ("Lock-Master: the Flush", "Maître des écluses : la Chasse d'eau"), [
        ("At 65% his jets sweep there and back, he thrusts three times, rams down a line (bait him into a gate: he "
         "reels) and slams steam round him. At 30% he opens the sluices: a current sweeps the floor (the lee of a "
         "column or a gate shelters you) while he charges four times down the arena, again every 22 s.",
         "À 65 %, ses jets balaient aller et retour, il frappe trois fois d'estoc, fonce le long d'une ligne (attire-le "
         "contre une grille : il chancelle) et fait jaillir la vapeur autour de lui. À 30 %, il ouvre les vannes : un "
         "courant balaie le sol (l'abri d'une colonne ou d'une grille te protège) pendant qu'il charge quatre fois à "
         "travers l'arène, puis toutes les 22 s."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Pressure-Lance of the Lock-Master, whose "
         "right-click shoots a jet of water that hurls foes to its far end.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Lance à pression du Maître des écluses, "
         "dont le clic droit tire un jet d'eau qui projette les ennemis au bout."),
    ], []),
    ("turbine_tyrant", "wonders", "brasshaven:remembrance_turbine_tyrant", ("The Turbine Tyrant", "Le Tyran des turbines"), [
        ("Past Generator Hall II at the foot of the Dam of the Drowned Valley, in the main turbine chamber, the dam's "
         "engineer waits (600 health, armour 14), fused into his turbine: a walking scroll-case on hydraulic legs, a "
         "turbine rotor for a right arm and a valve-wrench as long as a man in his left fist.",
         "Au-delà de la salle des générateurs II, au pied du Barrage de la vallée engloutie, dans la grande salle des "
         "turbines, attend l'ingénieur du barrage (600 PV, armure 14), soudé à sa turbine : une volute qui marche sur "
         "des jambes hydrauliques, un rotor de turbine pour bras droit et une clé à vanne grande comme un homme dans "
         "le poing gauche."),
        ("Hear the rotor whine before it sweeps; step off the line his wrench marks, the crack runs on and blows any "
         "grate it crosses. When he cranks his valve, get off the hissing copper grates. When he swells and the gauges "
         "climb, break his line of sight: a pillar or a generator in its alcove, or simply get out of range. Only "
         "those he can see take the blast.",
         "Écoute le rotor siffler avant le balayage ; écarte-toi de la ligne que marque sa clé, la fissure court et "
         "fait sauter les grilles qu'elle croise. Quand il tourne sa vanne, quitte les grilles de cuivre qui sifflent. "
         "Quand il gonfle et que les manomètres montent, coupe sa ligne de vue : un pilier, un générateur dans son "
         "alcôve, ou sors de sa portée. Seuls ceux qu'il voit prennent l'explosion."),
    ], ["brasshaven:remembrance_turbine_tyrant", "brasshaven:tyrant_wrench"]),
    ("turbine_tyrant_overload", "wonders", "minecraft:redstone_block", ("Tyrant: the Overload", "Tyran : la Surchauffe"), [
        ("At 65% he combos rotor, wrench and rotor, draws everyone in with his spinning rotor before he whirls, blows "
         "the grates one after another round the chamber, and his blast reaches 19 blocks. At 30% he kneels and "
         "overloads: faster, the grates blow on their own, and every 11 s he dashes across the chamber through three "
         "marks, leaving sparks that burn.",
         "À 65 %, il enchaîne rotor, clé et rotor, aspire tout le monde avec son rotor avant de tournoyer, fait sauter "
         "les grilles l'une après l'autre autour de la salle, et son explosion porte à 19 blocs. À 30 %, il "
         "s'agenouille et surchauffe : plus rapide, les grilles sautent d'elles-mêmes, et toutes les 11 s il fonce à "
         "travers la salle par trois marques en laissant des étincelles qui brûlent."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Valve-Wrench of the Turbine Tyrant, whose "
         "right-click vents a blast of steam at every foe you can see around you.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Clé à vanne du Tyran des turbines, dont "
         "le clic droit lâche un jet de vapeur sur tous les ennemis que tu vois autour de toi."),
    ], []),
    ("bog_hierophant", "wonders", "brasshaven:remembrance_bog_hierophant", ("The Bog Hierophant", "Le Hiérophante des tourbières"), [
        ("At the top of the Mire Stilt-City, up the grand stair from the High Walk, the rotting bishop holds court in the "
         "witch-queen's hall (600 health, armour 12): a hunched prelate on two stilt legs bound in mangrove roots, a "
         "mantle of living moss, a crooked mitre, a lantern-crozier of black wood and a cloud of marsh-flies.",
         "Au sommet de la Cité des pilotis, en haut du grand escalier depuis la Haute Promenade, l'évêque pourrissant "
         "tient sa cour dans la salle de la reine-sorcière (600 PV, armure 12) : un prélat voûté sur deux jambes "
         "d'échassier liées de racines, un manteau de mousse vivante, une mitre de travers, une crosse-lanterne de bois "
         "noir et un nuage de mouches des marais."),
        ("He sweeps with the crozier, slams the lantern down a line, strides through you on his long legs and stamps "
         "if you hug him. His lantern marks you: 2.5 s later a poison bloom bursts where you stand, so step away from "
         "your friends. He opens circles of real mud that slow, then root you: get out within a second. Leeches drop "
         "off his robe every half minute.",
         "Il balaie de sa crosse, abat la lanterne le long d'une ligne, te traverse sur ses longues jambes et piétine "
         "si tu restes collé. Sa lanterne te marque : 2,5 s plus tard une floraison de poison éclate où tu te tiens, "
         "éloigne-toi des autres. Il ouvre des cercles de vraie boue qui ralentissent puis retiennent : sors-en en "
         "moins d'une seconde. Des sangsues tombent de sa robe toutes les trente secondes."),
    ], ["brasshaven:remembrance_bog_hierophant", "brasshaven:hierophant_crozier"]),
    ("bog_hierophant_fire", "wonders", "minecraft:lantern", ("Hierophant: the Swamp Fire", "Hiérophante : le Feu des marais"), [
        ("At 65% eight lanterns kindle round the hall and he burns away into a will-o'-wisp that flits from lantern to "
         "lantern, then rises behind you: a ring and a chime mark the spot, turn round and step aside. A swarm of "
         "marsh-flies hunts you. At 30% the swamp gas ignites: every 11 s lines of fire roll across the hall, too tall "
         "to jump, so cross through the gaps; afterwards he is spent and takes more damage.",
         "À 65 %, huit lanternes s'allument autour de la salle et il se consume en feu follet qui saute de lanterne en "
         "lanterne, puis se relève derrière toi : un cercle et un tintement marquent l'endroit, retourne-toi et "
         "écarte-toi. Un essaim de mouches te poursuit. À 30 %, le gaz des marais s'embrase : toutes les 11 s, des "
         "lignes de feu roulent à travers la salle, trop hautes pour être sautées, passe par les brèches ; ensuite il "
         "est épuisé et encaisse davantage."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Lantern-Crozier of the Bog Hierophant, whose "
         "right-click opens a sinking bog where you look that drags foes in, holds them fast and poisons them.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Crosse-lanterne du Hiérophante, dont le "
         "clic droit ouvre une tourbière là où tu regardes : elle attire les ennemis, les retient et les empoisonne."),
    ], []),
    ("strangler_queen", "wonders", "brasshaven:remembrance_strangler_queen", ("The Strangler Fig Queen", "La Reine-figuier étrangleur"), [
        ("On the summit terrace of the Canopy Temple-City, through the mist under the broken brass sun-disc, the fig "
         "that strangled the temple has crowned itself (620 health, armour 12): a towering woman of woven roots and "
         "jade, an orchid crown, a jade mask with golden eyes, a thorned root-whip for a left arm and a jade "
         "macuahuitl in her right hand.",
         "Sur la terrasse au sommet de la Cité-temple de la canopée, passé la brume, sous le disque solaire de laiton "
         "brisé, le figuier qui a étranglé le temple s'est couronné (620 PV, armure 12) : une femme immense de racines "
         "tressées et de jade, une couronne d'orchidées, un masque de jade aux yeux d'or, un fouet de racine épineux "
         "pour bras gauche et un macuahuitl de jade dans la main droite."),
        ("Her whip lashes 11 blocks down a green line and drags you in; her macuahuitl cuts twice in front of her. "
         "Roots burst from the floor in lines (stand between them) and in rings that roll outward (jump them). Her "
         "pollen clouds slow you more and more, then blind you: leave them. She swings on a vine to whoever runs "
         "away, and thorns burst round her if you hug her. Near the terrace edge her blows never throw you over.",
         "Son fouet claque à 11 blocs le long d'une ligne verte et te ramène ; son macuahuitl taille deux fois devant "
         "elle. Des racines jaillissent du sol en lignes (place-toi entre elles) et en anneaux qui s'élargissent "
         "(saute-les). Ses nuages de pollen te ralentissent de plus en plus puis t'aveuglent : sors-en. Elle se "
         "balance sur une liane jusqu'à qui s'enfuit, et des épines jaillissent si tu restes collé. Près du bord de "
         "la terrasse, ses coups ne te jettent jamais dans le vide."),
    ], ["brasshaven:remembrance_strangler_queen", "brasshaven:queen_macuahuitl"]),
    ("strangler_queen_canopy", "wonders", "minecraft:mangrove_roots", ("Queen: Canopy and Cages", "Reine : Canopée et cages"), [
        ("At 65% she climbs into the sun-disc where you cannot reach her: jaguar spirits drop to hunt you (more in a "
         "larger party) and seed-bombs fall on marked players, so step out of the circles. Kill every spirit and she "
         "falls early, exposed. She plunges onto a circle that follows her target and then locks. At 30% she "
         "blooms once, then every 12 s root cages snap shut round marked players: get out of the circle before it "
         "closes, or break the roots from inside before she comes to harvest the cage.",
         "À 65 %, elle grimpe dans le disque solaire, hors d'atteinte : des esprits-jaguars tombent te chasser (plus "
         "nombreux en groupe) et des graines-bombes tombent sur les joueurs marqués, sors des cercles. Tue tous les "
         "esprits et elle chute plus tôt, exposée. Elle s'écrase sur un cercle qui suit sa cible puis se fige. À "
         "30 %, elle fleurit une fois, puis toutes les 12 s des cages de racines se referment sur les joueurs "
         "marqués : sors du cercle avant qu'il se ferme, ou casse les racines de l'intérieur avant qu'elle vienne "
         "moissonner la cage."),
        ("Her Remembrance, four Map Fragments and two diamonds forge the Jade Macuahuitl of the Strangler Queen, whose "
         "right-click cracks a root lash along your aim: the first foe it meets is caged where it stands and the "
         "cage's thorns whip the foes beside it.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Macuahuitl de jade de la Reine-figuier, "
         "dont le clic droit fait claquer un fouet de racine dans ta visée : le premier ennemi touché est mis en cage "
         "sur place et les épines de la cage fouettent ceux qui l'entourent."),
    ], []),
    ("solar_hierarch", "wonders", "brasshaven:remembrance_solar_hierarch", ("The Solar Hierarch", "Le Hiérarque solaire"), [
        ("In the sun chamber under the lens of the Sun-Engine Ziggurat, past the antechamber and the mist, the last "
         "priest of the noon keeps watch (620 health, armour 12): a tall gilded automaton in a striped headdress, a brass "
         "sun-disc halo at his back with three little planets wheeling round it, a sun-staff in his right hand and a "
         "mirror-shield on his left arm. When the fight starts six sandstone gnomons rise round the floor: they are your "
         "cover, because no light of his passes through them.",
         "Dans la chambre du soleil sous la lentille de la Ziggourat du Moteur solaire, passé l'antichambre et la brume, "
         "le dernier prêtre du midi monte la garde (620 PV, armure 12) : un grand automate doré coiffé d'un némès rayé, "
         "un halo-disque de laiton dans le dos où tournent trois petites planètes, un bâton solaire en main droite et un "
         "bouclier-miroir au bras gauche. Au début du combat, six gnomons de grès se dressent autour de la salle : ce "
         "sont tes abris, car aucune de ses lumières ne les traverse."),
        ("His mirror guards his front against blows and throws arrows back at the archer: hit him from the side or "
         "behind, or keep hitting the mirror until it cracks and he reels (he then takes more damage). Strike the mirror "
         "three times quickly and he bashes you away with it. He sweeps, thrusts with fire and chains a three-hit combo "
         "that ends in a slam. When the mirror flares, look away or stand behind a gnomon: the flash blinds.",
         "Son miroir garde son front contre les coups et renvoie les flèches au tireur : frappe-le de côté ou de dos, "
         "ou frappe le miroir jusqu'à ce qu'il se fende et qu'il chancelle (il encaisse alors davantage). Frappe le "
         "miroir trois fois de suite et il te repousse d'un coup de bouclier. Il balaie, perce d'une estocade de feu et "
         "enchaîne un combo en trois coups qui finit en frappe au sol. Quand le miroir s'embrase, détourne le regard ou "
         "mets-toi derrière un gnomon : l'éclair aveugle."),
    ], ["brasshaven:remembrance_solar_hierarch", "brasshaven:hierarch_sunstaff"]),
    ("solar_hierarch_sun", "wonders", "minecraft:sunflower", ("Hierarch: Sun and Planets", "Hiérarque : Soleil et planètes"), [
        ("He calls down the sun-lance: a beam falls down the shaft, bounces off his mirror and crawls after you; a "
         "gnomon stops it. He spins his planets in rings round the room: jump the low ring, duck behind a gnomon for "
         "the high one. Below 65% he leaps onto you, sends rings of fire and adds a second beam and a third ring whose "
         "turn reverses (blue chevrons warn you).",
         "Il appelle la lance solaire : un rayon tombe du puits, rebondit sur son miroir et rampe vers toi ; un gnomon "
         "l'arrête. Il fait tourner ses planètes en anneaux autour de la salle : saute l'anneau bas, cache-toi derrière "
         "un gnomon pour l'anneau haut. Sous 65 %, il bondit sur toi, lance des anneaux de feu et ajoute un second "
         "rayon et un troisième anneau qui change de sens (des chevrons bleus préviennent)."),
    ], []),
    ("solar_hierarch_eclipse", "wonders", "minecraft:clock", ("Hierarch: the Eclipse", "Hiérarque : l'Éclipse"), [
        ("At 30% he calls the eclipse: the room goes dark (only his halo and the beam stay lit), a burst knocks you "
         "back and he grows faster. Six sun-sigils light up round the floor; every few seconds he blinks between "
         "them, and the next one to flare is the one he lands on: a corona of fire bursts round him there, so keep "
         "away from the bright sigil. A lone pillar of light wanders the room all the while.",
         "À 30 %, il appelle l'éclipse : la salle s'assombrit (seuls son halo et le rayon restent allumés), une onde te "
         "repousse et il accélère. Six sceaux solaires s'allument au sol ; toutes les quelques secondes il saute de l'un "
         "à l'autre, et le prochain à s'embraser est celui où il apparaît : une couronne de feu éclate autour de lui, "
         "alors éloigne-toi du sceau brillant. Une colonne de lumière erre dans la salle tout ce temps."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Sun-Staff of the Solar Hierarch, whose "
         "right-click looses a ray of sunlight that glances off walls up to three times and burns every foe it crosses.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Bâton solaire du Hiérarque, dont le clic "
         "droit décoche un rayon de soleil qui ricoche jusqu'à trois fois sur les murs et brûle chaque ennemi traversé."),
    ], []),
    ("drowned_admiral", "wonders", "brasshaven:remembrance_drowned_admiral", ("The Drowned Admiral", "L'Amiral noyé"), [
        ("Deep in the stern of the Leviathan Dreadnought Wreck, past the engine room and the mist of the stokehold, the "
         "last admiral of the ship holds the boiler hall (620 health, armour 12): a towering naval officer in a "
         "waterlogged greatcoat, a brass diving helmet under a bicorne, a boarding cutlass in his right hand and a deck "
         "cannon for a left forearm.",
         "Au fond de la poupe de l'Épave du cuirassé Léviathan, passé la salle des machines et la brume de la "
         "chaufferie, le dernier amiral du navire tient la salle des chaudières (620 PV, armure 12) : un officier de "
         "marine immense en redingote gorgée d'eau, un casque de scaphandre de laiton sous un bicorne, un sabre "
         "d'abordage dans la main droite et un canon de pont pour avant-bras gauche."),
        ("He cuts forehand and backhand, lunges point first and stamps if you hug him. His cannon's red laser follows "
         "you a little slower than a sidestep, then turns yellow and locks: step across before the shell bursts. He "
         "flings a boarding hook down a grey chain line (whoever it catches is dragged to his feet) and bursts the "
         "boiler valves: lanes of scalding steam run from the fireboxes toward each player and linger.",
         "Il frappe en coup droit et en revers, fend la pointe en avant et piétine si tu restes collé. Le laser rouge "
         "de son canon te suit un peu moins vite qu'un pas de côté, puis vire au jaune et se fige : passe en travers "
         "avant l'obus. Il lance un grappin d'abordage le long d'une chaîne grise (qui est pris est traîné à ses "
         "pieds) et fait sauter les vannes des chaudières : des couloirs de vapeur brûlante partent des foyers vers "
         "chaque joueur et y restent."),
    ], ["brasshaven:remembrance_drowned_admiral", "brasshaven:admiral_cutlass"]),
    ("drowned_admiral_scuttle", "wonders", "minecraft:nautilus_shell", ("Admiral: the Scuttling", "Amiral : le Sabordage"), [
        ("At 65% he fires broadsides of three shots, chains cuts into a leaping chop and charges helmet first: bait the "
         "charge into a boiler or a wall and he reels for two seconds. At 30% he scuttles his ship: seawater floods the "
         "hall knee-deep for 18 s (real water, drained afterwards), you wade while he moves at full speed, and two to "
         "four drowned marines board, more with more players. He scuttles again 12 s after each ebb.",
         "À 65 %, il tire des bordées de trois coups, enchaîne ses coups de sabre en un bond écrasant et charge casque "
         "baissé : attire la charge contre une chaudière ou un mur et il chancelle deux secondes. À 30 %, il saborde "
         "son navire : la mer envahit la salle jusqu'aux genoux pendant 18 s (de la vraie eau, retirée ensuite), tu "
         "patauges pendant qu'il avance à pleine vitesse, et deux à quatre marins noyés montent à l'abordage, plus "
         "s'il y a plus de joueurs. Il recommence 12 s après chaque décrue."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Boarding Cutlass of the Drowned Admiral, whose "
         "right-click fires a deck-cannon shell along your aim that bursts on the first foe or wall with splash damage.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Sabre d'abordage de l'Amiral noyé, dont "
         "le clic droit tire un obus de canon de pont dans ta visée : il éclate sur le premier ennemi ou mur, avec des "
         "dégâts de zone."),
    ], []),
    ("storm_ascetic", "wonders", "brasshaven:remembrance_storm_ascetic", ("The Storm Ascetic", "L'Ascète des tempêtes"), [
        ("In the bell temple on the summit of Pilgrim's Ascent, the hermit waits under the great bell (580 health, armour "
         "12): a gaunt old monk with a staff taller than himself, a straw hat on his back and nine prayer beads circling "
         "him. The storm answers him.",
         "Dans le temple de la cloche, au sommet de l'Ascension du pèlerin, l'ermite attend sous la grande cloche (580 PV, "
         "armure 12) : un vieux moine décharné, un bâton plus grand que lui, un chapeau de paille dans le dos et neuf "
         "grains de chapelet qui tournent autour de lui. L'orage lui répond."),
        ("His staff reaches far: a sweep, then a thrust down a marked line. He vaults onto the ring that follows you "
         "(jump the wind), flings his beads out and back, calls lightning on the rings under your feet and whirls the "
         "staff if you hug him. His gust pushes you toward the walls, but never past the ring of cloud it draws.",
         "Son bâton porte loin : un balayage, puis un coup d'estoc le long d'une ligne marquée. Il saute à la perche sur "
         "le cercle qui te suit (saute le vent), lance ses grains qui reviennent vers lui, appelle la foudre sur les "
         "cercles sous tes pieds et fait tournoyer le bâton si tu le colles. Sa rafale te pousse vers les murs, jamais "
         "au-delà de l'anneau de nuages qu'elle trace."),
    ], ["brasshaven:remembrance_storm_ascetic", "brasshaven:ascetic_staff"]),
    ("storm_ascetic_bell", "wonders", "minecraft:bell", ("Ascetic: the great bell", "Ascète : la grande cloche"), [
        ("At 65% he splits into three: two mirror images that die to any blow, the real one among them. He strikes three "
         "times (the last blow calls lightning down a line) and draws you in before a ring of wind. At 30% he kneels and "
         "the great bell answers: from then on it tolls by itself every eight seconds, a ring of thunder you must jump, "
         "and he rings it three times in a row.",
         "À 65 %, il se dédouble : deux reflets qui meurent au moindre coup, le vrai parmi eux. Il frappe trois fois (le "
         "dernier coup appelle la foudre le long d'une ligne) et t'attire avant un anneau de vent. À 30 %, il "
         "s'agenouille et la grande cloche répond : dès lors elle sonne seule toutes les huit secondes, un anneau de "
         "tonnerre à sauter, et il la fait sonner trois fois de suite."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Staff of the Storm Ascetic, whose right-click "
         "hurls foes away with a gust and calls lightning on the three nearest.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Bâton de l'Ascète des tempêtes, dont le "
         "clic droit repousse les ennemis d'une rafale et appelle la foudre sur les trois plus proches."),
    ], []),
    ("oathbound_gatekeeper", "wonders", "brasshaven:remembrance_oathbound_gatekeeper",
     ("The Oathbound Gatekeeper", "Le Gardien du Serment"), [
        ("Under the Kneeling Gate, in the domed hall beneath the town square, the gate's own knight waits (480 health, "
         "armour 14): a living statue of pale limestone with a red granite cloak, a tower shield carved with the gold "
         "key of the toll, a stone greatsword and the gate's great key on a chain.",
         "Sous la Porte agenouillée, dans la salle voûtée sous la place, attend le chevalier de la porte (480 PV, "
         "armure 14) : une statue vivante de calcaire pâle au manteau de granit rouge, un pavois gravé de la clé d'or "
         "du péage, un espadon de pierre et la grande clé de la porte au bout d'une chaîne."),
        ("His shield blocks every blow from the front: walk round him and strike his sides and back while he "
         "recovers. Beat on the shield and he bashes you; stay behind him too long and he wheels round; hug his back "
         "and he stomps (jump the ring). His key falls on the gold ring that follows you.",
         "Son pavois bloque tous les coups venus de face : tourne autour de lui et frappe ses flancs et son dos "
         "pendant qu'il se remet. Frappe le bouclier et il te charge de l'épaule ; reste trop longtemps dans son dos "
         "et il pivote ; colle-toi à lui et il piétine (saute l'onde). Sa clé tombe sur le cercle doré qui te suit."),
    ], ["brasshaven:remembrance_oathbound_gatekeeper", "brasshaven:gatekeeper_key"]),
    ("oathbound_gatekeeper_oath", "wonders", "minecraft:bell", ("Gatekeeper: the oath", "Gardien : le serment"), [
        ("At 65% the gate's bell answers him: he strikes his shield and walls of stone hands sweep the whole hall, "
         "each with one open lane between two lines of soul flame: run to the lane. At 30% he kneels behind his "
         "shield like the statues above and the gate heals him: no blow reaches him, every hit goes to the Oath "
         "Shield. Break it in 10 s and he reels, his guard gone for good; fail and he rises and kneels again later.",
         "À 65 %, la cloche de la porte lui répond : il frappe son pavois et des murs de mains de pierre balaient "
         "toute la salle, chacun avec un seul passage ouvert entre deux lignes de flammes d'âme : cours-y. À 30 %, il "
         "s'agenouille derrière son pavois comme les statues et la porte le soigne : aucun coup ne l'atteint, tout va "
         "au Bouclier du Serment. Brise-le en 10 s et il chancelle, sans garde pour de bon ; sinon il se relève et "
         "s'agenouillera de nouveau."),
        ("His Remembrance, four map fragments and two diamonds forge the Key of the Kneeling Gate, whose right-click "
         "makes stone hands punch up all around you and wards you with Resistance II.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent la Clé de la Porte agenouillée, dont le "
         "clic droit fait jaillir des mains de pierre tout autour de toi et te protège (Résistance II)."),
    ], []),
    ("tesla_observatory", "wonders", "minecraft:lightning_rod", ("Tesla Observatory", "Observatoire Tesla"), [
        ("A science campus on a rocky crag: a copper dome with a 30-block telescope, a 70-block Tesla tower and an "
         "orrery under a glass dome.",
         "Un campus scientifique sur un piton rocheux : une coupole de cuivre et son télescope de 30 blocs, une tour "
         "Tesla de 70 blocs et un planétarium sous un dôme de verre."),
        ("Where: on mountain tops and windswept hills.",
         "Où : au sommet des montagnes et des collines venteuses."),
        ("Between the buildings: the library, the laboratory and the star-chart hall. Bring blocks to climb the "
         "crag.",
         "Entre les bâtiments : la bibliothèque, le laboratoire et la salle des cartes du ciel. Prévois des blocs "
         "pour escalader le piton."),
    ], []),
    ("crystal_cathedral", "wonders", "minecraft:amethyst_block", ("Crystal Cathedral", "Cathédrale de cristal"), [
        ("A gothic cathedral of calcite, quartz and amethyst inside a giant geode, with a rose window, spires and "
         "crystal pillars.",
         "Une cathédrale gothique de calcite, de quartz et d'améthyste au cœur d'une géode géante, avec rosace, "
         "flèches et piliers de cristal."),
        ("Where: under any biome, deep down (floor around y -30).",
         "Où : sous n'importe quel biome, en profondeur (sol vers y -30)."),
        ("In the north transept, a stair goes down to the crypt, where the reliquary waits behind iron bars.",
         "Dans le transept nord, un escalier descend à la crypte, où le reliquaire attend derrière des grilles."),
    ], []),

    # ------------------------------------------------------------------ storage
    ("sorting_chest", "storage", "brasshaven:sorting_chest", ("Sorting Chest", "Coffre de tri"), [
        ("A big 54-slot chest that sorts itself when nobody is looking inside, and vacuums items dropped "
         "within 6 blocks.",
         "Un grand coffre de 54 cases qui se trie tout seul quand personne ne regarde dedans, et aspire les objets "
         "lâchés à 6 blocs."),
        ("Sneak-right-click to sort it right now. Put one next to your mob farm or your mine entrance.",
         "Accroupi + clic droit pour le trier tout de suite. Pose-en un près de ta ferme ou de l'entrée de ta mine."),
        ("Craft: a chest, a hopper and seven planks.", "Fabrication : un coffre, un entonnoir et sept planches."),
    ], ["brasshaven:sorting_chest"]),
    ("crate", "storage", "brasshaven:compacting_crate", ("Compacting Crate", "Caisse compacte"), [
        ("A crate holds 32 stacks of a single item and shows it on its front with the count. Right-click with an "
         "item to put it in; right-click twice quickly to put in every one you carry.",
         "Une caisse contient 32 piles d'un seul objet, affiché en façade avec le total. Clic droit avec l'objet pour "
         "le ranger ; deux clics rapides rangent tous ceux que tu portes."),
        ("Left-click takes a stack (sneak: a single item). Hoppers, the Guild Terminal and quick-stack treat crates "
         "like chests that accept only their item.",
         "Clic gauche : prendre une pile (accroupi : un seul objet). Les entonnoirs, le terminal de guilde et le "
         "rangement rapide voient la caisse comme un coffre qui n'accepte que son objet."),
        ("Craft: a barrel, four iron ingots and four planks.",
         "Fabrication : un tonneau, quatre lingots de fer et quatre planches."),
    ], ["brasshaven:compacting_crate"]),
    ("guild_terminal", "storage", "brasshaven:guild_terminal", ("Guild Terminal", "Terminal de guilde"), [
        ("One screen for every chest of your base. The terminal links every chest, barrel, shulker box, sorting chest "
         "and compacting crate up to 48 blocks around it (32 up and down). No cables, no power.",
         "Un seul écran pour tous les coffres de ta base. Le terminal relie chaque coffre, tonneau, boîte de shulker, "
         "coffre de tri et caisse compacte jusqu'à 48 blocs autour de lui (32 en haut et en bas). Ni câble, ni énergie."),
        ("Craft: a chest, two gold ingots, a Map Fragment, redstone and four planks. Bigger base? Add Storage Relays "
         "instead of more terminals.",
         "Fabrication : un coffre, deux lingots d'or, un fragment de carte, une redstone et quatre planches. Base plus "
         "grande ? Ajoute des relais de stockage plutôt que d'autres terminaux."),
        ("Take: click an item for a stack (right-click: half, middle-click: one, shift: straight into your "
         "inventory). Store: click the grid with an item, or shift-click it in your inventory. Store all and Store "
         "matching empty your inventory in one click.",
         "Prendre : clic sur un objet pour une pile (clic droit : la moitié, molette : un seul, Maj : directement "
         "dans l'inventaire). Ranger : clic sur la grille avec un objet, ou Maj + clic dans ton inventaire. "
         "« Tout ranger » et « Ranger identiques » vident ton inventaire d'un clic."),
        ("Sneak-right-click the terminal to sort every linked chest at once. Chests in unloaded chunks, unopened loot "
         "chests, hoppers and machines are never linked.",
         "Accroupi + clic droit sur le terminal pour trier d'un coup tous les coffres reliés. Les coffres des chunks "
         "non chargés, les coffres de butin jamais ouverts, les entonnoirs et les machines ne sont jamais reliés."),
    ], ["brasshaven:guild_terminal"]),
    ("terminal_network", "storage", "brasshaven:guild_terminal", ("Terminal: network & sorting",
                                                                 "Terminal : réseau et tri"), [
        ("Items go first into a chest that already holds the same item, then into sorting chests, then into any free "
         "slot. Search by name (@name: by mod); the sort button cycles count, name and mod.",
         "Les objets vont d'abord dans un coffre qui contient déjà le même objet, puis dans les coffres de tri, puis "
         "dans n'importe quelle place libre. Recherche par nom (@nom : par mod) ; le bouton de tri alterne quantité, "
         "nom et mod."),
        ("The chest-network button (top right) lists the linked containers by type. Click one to exclude it, like a "
         "trash chest or a furnace input chest; click again to link it back. \"Show in world\" outlines them all "
         "for 10 seconds: gold linked, red excluded.",
         "Le bouton réseau (en haut à droite) liste les conteneurs reliés par type. Clique sur l'un d'eux pour "
         "l'exclure, comme un coffre poubelle ou le coffre d'entrée d'un four ; reclique pour le relier. « Montrer » "
         "les encadre tous pendant 10 secondes : en or s'ils sont reliés, en rouge s'ils sont exclus."),
    ], []),
    ("storage_relay", "storage", "brasshaven:storage_relay", ("Storage Relay", "Relais de stockage"), [
        ("A small brass beacon that stretches a Guild Terminal's reach: every chest up to 32 blocks around the relay "
         "joins the terminal's network. One terminal can then reach the whole base, even several buildings.",
         "Une petite balise en laiton qui étend la portée d'un terminal de guilde : chaque coffre jusqu'à 32 blocs "
         "autour du relais rejoint le réseau du terminal. Un seul terminal atteint alors toute la base, même plusieurs "
         "bâtiments."),
        ("Craft (makes two): an ender pearl, four brass ingots, a redstone and a copper ingot.",
         "Fabrication (en donne deux) : une perle de l'Ender, quatre lingots de laiton, une redstone et un lingot de "
         "cuivre."),
        ("Place it within 48 blocks of the terminal, or within 32 blocks of another linked relay: relays chain, so "
         "you can reach a far storage hall step by step. Right-click a relay to check that it is linked.",
         "Pose-le à moins de 48 blocs du terminal, ou à moins de 32 blocs d'un autre relais relié : les relais "
         "s'enchaînent, pour atteindre pas à pas une réserve lointaine. Clic droit sur un relais pour vérifier qu'il "
         "est relié."),
    ], ["brasshaven:storage_relay"]),
    ("backpack", "storage", "brasshaven:travel_backpack", ("Backpacks", "Sacs"), [
        ("Travel Backpack: hold it and right-click to open 27 extra slots that travel with you. Craft: a chest, a "
         "string and seven leather.",
         "Sac du Voyageur : tiens-le et fais clic droit pour ouvrir 27 cases en plus qui voyagent avec toi. "
         "Fabrication : un coffre, une ficelle et sept cuirs."),
        ("Explorer's Backpack: 54 slots. Craft your Travel Backpack with a brass ingot: nothing inside is lost.",
         "Sac de l'Explorateur : 54 cases. Fabrique-le avec ton Sac du Voyageur et un lingot de laiton : rien de son "
         "contenu n'est perdu."),
    ], ["brasshaven:travel_backpack", "brasshaven:explorer_backpack"]),
    ("magnet", "storage", "brasshaven:magnet_ring", ("Magnet Ring", "Anneau aimanté"), [
        ("Wear it in a ring slot (next to your armour in the inventory). Switched on (it glows), it makes items and "
         "experience within 7 blocks fly to you.",
         "Porte-le dans un emplacement d'anneau (à côté de l'armure, dans l'inventaire). Allumé (il brille), il fait "
         "voler vers toi objets et expérience à 7 blocs."),
        ("Right-click it in hand, or press N even while it is worn, to switch it on or off.",
         "Clic droit en main, ou touche N même quand il est porté, pour l'allumer ou l'éteindre."),
        ("Craft: two Map Fragments, a redstone and three iron ingots.",
         "Fabrication : deux fragments de carte, une redstone et trois lingots de fer."),
    ], ["brasshaven:magnet_ring"]),
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
    ("sorting", "storage", "minecraft:chest", ("Inventory sorting", "Trier l'inventaire"), [
        ("Press R to sort your main inventory (not the hotbar or armour): stacks are merged and grouped.",
         "Appuie sur R pour trier ton inventaire principal (ni la barre d'action ni l'armure) : les piles sont "
         "fusionnées et regroupées."),
    ], []),
    ("grave", "storage", "brasshaven:grave", ("Graves", "Tombes"), [
        ("When you die, your belongings are kept in a grave where you fell. Its coordinates are sent in the chat.",
         "Quand tu meurs, tes affaires sont gardées dans une tombe là où tu es tombé. Ses coordonnées s'affichent "
         "dans le chat."),
        ("Right-click the grave to get everything back. A friend can also open it: the items then go into their "
         "inventory.",
         "Clic droit sur la tombe pour tout récupérer. Un ami peut aussi l'ouvrir : les objets vont alors dans son "
         "inventaire."),
    ], ["brasshaven:grave"]),

    # ------------------------------------------------------------------ danger
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
    ("bosses", "danger", "brasshaven:boss_seal", ("Bosses", "Boss"), [
        ("The big structures hide a boss arena behind a wall of mist; the journal gives each boss its quest. Walk "
         "through the mist to wake the boss: the mist seals until the fight ends.",
         "Les grandes structures cachent une arène derrière un mur de brume ; le journal donne une quête pour chaque "
         "boss. Traverse la brume pour réveiller le boss : elle se referme jusqu'à la fin du combat."),
        ("Watch the wind-ups: every attack is announced by an animation or a circle on the ground. Hit it after "
         "a big attack, and break its poise to stagger it.",
         "Observe les préparations : chaque attaque est annoncée par une animation ou un cercle au sol. Frappe après "
         "une grosse attaque, et brise sa posture pour l'étourdir."),
        ("If everyone leaves the arena, the boss heals and goes back to sleep.",
         "Si tout le monde quitte l'arène, le boss se soigne et se rendort."),
    ], ["brasshaven:boss_seal", "brasshaven:mist_gate"]),
    ("remembrance", "danger", "minecraft:nether_star", ("Boss weapons", "Armes de boss"), [
        ("Every boss drops its Remembrance. Craft it with four materials of its region (Map Fragments, Lithite, "
         "Ancient Embers or Void Shards) and two diamonds to forge its unique weapon, with a special right-click "
         "power.",
         "Chaque boss lâche son Souvenir. Fabrique-le avec quatre matériaux de sa région (fragments de carte, "
         "lithite, braises anciennes ou éclats du vide) et deux diamants pour forger son arme unique, avec un "
         "pouvoir au clic droit."),
    ], []),

    # ------------------------------------------------------------------ automatons
    ("brass_golem", "automatons", "brasshaven:clockwork_heart", ("Brass Golem", "Golem de laiton"), [
        ("A clockwork companion: it follows you and fights monsters with a 12-damage piston punch, and slams the "
         "ground when they crowd it. 80 health, 10 armour.",
         "Un compagnon mécanique : il te suit et combat les monstres avec un coup de piston de 12 dégâts, et frappe "
         "le sol quand ils l'encerclent. 80 points de vie, 10 d'armure."),
        ("To build it: stack two Blocks of Brass one on the other, then right-click them with a Clockwork Heart. It "
         "wakes up and follows whoever built it.",
         "Pour le construire : empile deux blocs de laiton l'un sur l'autre, puis fais clic droit dessus avec un "
         "cœur mécanique. Il se réveille et suit celui qui l'a construit."),
        ("Clockwork Heart: a brass gear, two brass ingots, a block of redstone and a clock. Brass gears: a brass "
         "ingot surrounded by four brass nuggets (makes 2). Block of Brass: nine ingots.",
         "Cœur mécanique : un engrenage en laiton, deux lingots de laiton, un bloc de redstone et une horloge. "
         "Engrenages : un lingot de laiton entouré de quatre pépites de laiton (en donne 2). Bloc de laiton : neuf "
         "lingots."),
    ], ["brasshaven:clockwork_heart", "brasshaven:brass_gear", "brasshaven:brass_golem_spawn_egg"]),
    ("brass_golem_orders", "automatons", "brasshaven:brass_ingot", ("Golem orders", "Ordres du golem"), [
        ("Sneak-right-click it with an empty hand: \"guard here\" (it stays and defends the spot) or \"follow me\". "
         "If it falls 28 blocks behind, it catches up by itself.",
         "Accroupi + clic droit main vide : « garde ici » (il reste et défend l'endroit) ou « suis-moi ». S'il est "
         "à plus de 28 blocs, il te rejoint tout seul."),
        ("It attacks every monster within 16 blocks except creepers, and never hurts players, villagers or pets.",
         "Il attaque tous les monstres à 16 blocs sauf les creepers, et ne blesse jamais joueurs, villageois ni "
         "animaux apprivoisés."),
        ("Repair: right-click it with a brass ingot (+20 health) or a brass nugget (+3). Destroyed, it drops its "
         "heart and some brass, so you can rebuild it.",
         "Réparation : clic droit avec un lingot de laiton (+20 PV) ou une pépite (+3). Détruit, il lâche son cœur "
         "et du laiton : tu peux le reconstruire."),
    ], ["brasshaven:brass_block"]),
    ("clockwork_spider", "automatons", "brasshaven:brass_gear", ("Clockwork Spider", "Araignée-horloge"), [
        ("Hostile clockwork spiders that roam in packs at night in the badlands and the savanna highlands, and in "
         "the Clockwork Citadel and the Undercity. They climb walls.",
         "Des araignées mécaniques hostiles qui rôdent en bande la nuit dans les badlands et les hautes savanes, "
         "ainsi que dans la Citadelle d'horlogerie et les Bas-fonds. Elles grimpent aux murs."),
        ("When one stops and its key whirs, it is about to leap: step aside. They drop brass nuggets, redstone and "
         "sometimes a brass gear.",
         "Quand l'une s'arrête et que sa clé s'emballe, elle va bondir : écarte-toi. Elles lâchent des pépites de "
         "laiton, de la redstone et parfois un engrenage."),
    ], ["brasshaven:clockwork_spider_spawn_egg"]),
    ("steam_drone", "automatons", "brasshaven:brass_nugget", ("Steam Drone", "Drone à vapeur"), [
        ("Hostile flying drones: at night over the steampunk lands, and in the Undercity. They circle and fire hot "
         "rivets.",
         "Des drones volants hostiles : la nuit au-dessus des terres steampunk, et dans les Bas-fonds. Ils tournent "
         "autour de toi et tirent des rivets brûlants."),
        ("When one rears up, it is about to dive at you: step aside. A bow brings them down. They drop brass "
         "nuggets, copper and sometimes a brass gear.",
         "Quand l'un se cabre, il va plonger sur toi : écarte-toi. Un arc les abat facilement. Ils lâchent des "
         "pépites de laiton, du cuivre et parfois un engrenage."),
    ], ["brasshaven:steam_drone_spawn_egg"]),
    ("grand_clockmaker", "automatons", "brasshaven:remembrance_grand_clockmaker",
     ("The Grand Clockmaker", "Le Grand Horloger"), [
        ("The boss of the Clockwork Citadel (400 health). A stair in the tower's entrance hall goes down through the "
         "gearworks to a waiting room with a waystone, before the mist of the Clock Vault.",
         "Le boss de la Citadelle d'horlogerie (400 PV). Un escalier dans le hall de la tour descend par la salle des "
         "engrenages jusqu'à une salle d'attente avec une pierre de voyage, devant la brume du Caveau de l'horloge."),
        ("He sweeps his pendulum cane, slams it (jump the ring of sparks), throws cogs and winds up spiders. When "
         "his hands rewind and a ring closes around him, get out of it or be frozen in time.",
         "Il balaie avec sa canne-pendule, l'abat au sol (saute l'anneau d'étincelles), lance des engrenages et "
         "remonte des araignées. Quand ses aiguilles reculent et qu'un cercle se referme, sors-en ou tu seras figé."),
    ], ["brasshaven:remembrance_grand_clockmaker", "brasshaven:clockmaker_pendulum"]),
    ("grand_clockmaker_midnight", "automatons", "minecraft:clock", ("Clockmaker: midnight", "Horloger : minuit"), [
        ("At half health he gets faster: he skips through time to reappear behind you, then tolls midnight: twelve "
         "bells burst around him, then a thirteenth under your feet. Move as soon as you see a glint.",
         "À mi-vie, il accélère : il saute dans le temps pour réapparaître derrière toi, puis sonne minuit : douze "
         "cloches éclatent autour de lui, puis une treizième sous tes pieds. Bouge dès que tu vois un reflet."),
        ("His Remembrance, four Map Fragments and two diamonds forge the Clockmaker's Pendulum, which slows foes.",
         "Son Souvenir, quatre fragments de carte et deux diamants forgent le Pendule du Grand Horloger, qui ralentit "
         "les ennemis."),
    ], []),

    # ------------------------------------------------------------------ gear & materials
    ("materials", "gear", "brasshaven:lithite_shard", ("Materials", "Matériaux"), [
        ("Map Fragments come from Overworld ruins, Lithite from deep ores, Ancient Embers from the Nether and Void "
         "Shards from the End. They repair and craft the gear of each region.",
         "Les fragments de carte viennent des ruines de la Surface, la lithite des minerais profonds, les braises "
         "anciennes du Nether et les éclats du vide de l'End. Ils réparent et fabriquent l'équipement de chaque "
         "région."),
    ], ["brasshaven:map_fragment", "brasshaven:lithite_shard", "brasshaven:ancient_ember", "brasshaven:void_shard"]),
    ("armor", "gear", "brasshaven:explorer_chestplate", ("Armour sets", "Ensembles d'armure"), [
        ("Wear all four pieces of a set to get its bonus: Explorer (speed, soft landings, night vision underground), "
         "Ember (fire immunity) and Void (slow fall, saved from the void).",
         "Porte les quatre pièces d'un ensemble pour son bonus : Explorateur (vitesse, chutes douces, vision "
         "nocturne sous terre), Braise (immunité au feu) et Vide (chute lente, sauvé du vide)."),
        ("Craft them like iron armour: Explorer from leather and Map Fragments, Ember from Ancient Embers, Void from "
         "Void Shards.",
         "Fabrique-les comme une armure en fer : Explorateur avec du cuir et des fragments de carte, Braise avec des "
         "braises anciennes, Vide avec des éclats du vide."),
    ], ["brasshaven:explorer_chestplate", "brasshaven:ember_chestplate", "brasshaven:void_chestplate"]),
    ("ores", "gear", "brasshaven:zinc_ingot", ("Ores & brass", "Minerais et laiton"), [
        ("Zinc is common in stone (y -16 to 96). Craft 3 copper ingots + 1 zinc ingot into 4 brass ingots: brass "
         "tools are faster than iron and enchant well.",
         "Le zinc est courant dans la pierre (y -16 à 96). Fabrique 3 lingots de cuivre + 1 lingot de zinc pour "
         "obtenir 4 lingots de laiton : les outils en laiton sont plus rapides que le fer et s'enchantent bien."),
        ("Mithril hides deep in deepslate (below y -8, iron pickaxe). Aether crystals glow faintly between y -48 and "
         "32. Orichalcum is found in the Nether. Smelt raw ores like iron.",
         "Le mithril se cache dans l'ardoise des abîmes (sous y -8, pioche en fer). Les cristaux d'éther luisent "
         "faiblement entre y -48 et 32. L'orichalque se trouve dans le Nether. Les minerais bruts se cuisent comme le "
         "fer."),
    ], ["brasshaven:zinc_ingot", "brasshaven:brass_ingot", "brasshaven:mithril_ingot", "brasshaven:aether_crystal",
        "brasshaven:orichalcum_ingot"]),
    ("metal_armor", "gear", "brasshaven:brass_helmet", ("Advanced armour", "Armures avancées"), [
        ("Brass set: night vision and faster mining. Mithril set: +4 health and +10% speed. Aether set: +75 mana, "
         "mana refills twice as fast, no fall damage.",
         "Ensemble en laiton : vision nocturne et minage plus rapide. Mithril : +4 points de vie et +10 % de vitesse. "
         "Éther : +75 de mana, recharge deux fois plus rapide, aucun dégât de chute."),
        ("Arcanist robes are woven from Arcane Cloth (purple wool, string and an aether crystal): +100 mana and spells "
         "25% stronger.",
         "Les robes d'arcaniste se tissent en étoffe arcanique (laine violette, ficelle et cristal d'éther) : +100 de "
         "mana et sorts 25 % plus puissants."),
        ("Craft each piece like iron armour, from brass or mithril ingots, aether crystals or Arcane Cloth.",
         "Chaque pièce se fabrique comme une armure en fer, avec des lingots de laiton ou de mithril, des cristaux "
         "d'éther ou de l'étoffe arcanique."),
    ], ["brasshaven:brass_helmet", "brasshaven:mithril_chestplate", "brasshaven:aether_chestplate",
        "brasshaven:arcane_chestplate"]),
    ("steam_blocks", "gear", "brasshaven:gear_panel", ("Steampunk blocks", "Blocs steampunk"), [
        ("Brass, copper and dark iron plating, clockwork and gauge panels, pipe bundles, Edison lamps, aether "
         "conduits, mahogany panelling, tufted leather and smokestack bricks. Most plates also come as stairs and "
         "slabs.",
         "Placages en laiton, cuivre et fer sombre, panneaux d'horlogerie et à manomètre, faisceaux de tuyaux, lampes "
         "Edison, conduits d'éther, lambris d'acajou, capitonnage en cuir et briques de cheminée. La plupart des "
         "plaques existent aussi en escaliers et dalles."),
        ("Tip: keep brass for the trims and let dark iron and mahogany carry the mass; light it with Edison lamps. "
         "The Engraver's Chisel unlocks more variants.",
         "Astuce : garde le laiton pour les finitions, laisse le fer sombre et l'acajou porter la masse, et éclaire "
         "avec des lampes Edison. Le burin du graveur débloque d'autres variantes."),
    ], ["brasshaven:brass_plating", "brasshaven:gear_panel", "brasshaven:copper_pipes", "brasshaven:edison_lamp",
        "brasshaven:aether_conduit", "brasshaven:mahogany_panelling"]),
    ("world_woods", "gear", "brasshaven:glowwood_sapling", ("Glowwood and Rustwood", "Bois-lueur et bois rouillé"), [
        ("Two woods to grow yourself. Glowwood: pale trunks under teal leaves that glow at night. Rustwood: dark red "
         "bark and rust-orange leaves on forked trees.",
         "Deux bois à faire pousser soi-même. Le bois-lueur : troncs pâles sous des feuilles turquoise qui luisent "
         "la nuit. Le bois rouillé : écorce rouge sombre et feuilles couleur de rouille sur des arbres fourchus."),
        ("Craft a sapling: an oak sapling, glow berries and glowstone dust (Glowwood); an acacia sapling and raw iron "
         "(Rustwood). Elven and forest ruins hide Glowwood saplings in their chests, steampunk workshops Rustwood "
         "ones.",
         "Fabrique une pousse : une pousse de chêne, des baies lumineuses et de la poudre de pierre lumineuse "
         "(bois-lueur) ; une pousse d'acacia et du fer brut (bois rouillé). Les ruines elfiques et forestières "
         "cachent des pousses de bois-lueur dans leurs coffres, les ateliers steampunk des pousses de bois rouillé."),
        ("Each gives a full set like oak: logs, bark, planks, stairs, slabs, fences, gates, doors, trapdoors, buttons "
         "and pressure plates. An axe strips the logs; the leaves drop saplings that grow the same tree.",
         "Chacun donne un ensemble complet comme le chêne : bûches, écorce, planches, escaliers, dalles, barrières, "
         "portillons, portes, trappes, boutons et plaques de pression. La hache écorce les bûches ; les feuilles "
         "donnent des pousses qui font repousser le même arbre."),
    ], ["brasshaven:glowwood_sapling", "brasshaven:rustwood_sapling", "brasshaven:glowwood_log", "brasshaven:rustwood_log",
        "brasshaven:glowwood_planks", "brasshaven:rustwood_planks", "brasshaven:glowwood_leaves",
        "brasshaven:rustwood_leaves"]),
    ("world_stones", "gear", "brasshaven:marble_pillar", ("Marble, rust rock, blue slate", "Marbre, roche rouillée, ardoise bleue"), [
        ("Three stones, found in big veins like granite: marble in the mountains (from y 32 up), rust rock in the "
         "badlands and the savanna highlands, blue slate deep down in the deepslate (below y 0).",
         "Trois pierres, en grosses veines comme le granite : le marbre dans les montagnes (dès y 32), la roche "
         "rouillée dans les badlands et les hautes savanes, l'ardoise bleue tout en bas dans l'ardoise des abîmes "
         "(sous y 0)."),
        ("Polished, bricks, pillar, tiles, stairs, slabs and walls come from the stonecutter, and the Engraver's "
         "Chisel switches between them.",
         "Poli, briques, pilier, carreaux, escaliers, dalles et murets sortent du tailleur de pierre, et le burin du "
         "graveur passe de l'un à l'autre."),
        ("Or craft them: two calcite and two diorite make 4 marble; four granite around an iron nugget, 4 rust rock; "
         "four cobbled deepslate around a lapis lazuli, 4 blue slate.",
         "Ou fabrique-les : deux calcites et deux diorites donnent 4 marbres ; quatre granites autour d'une pépite de "
         "fer, 4 roches rouillées ; quatre pierres des abîmes taillées autour d'un lapis-lazuli, 4 ardoises bleues."),
    ], ["brasshaven:marble", "brasshaven:marble_pillar", "brasshaven:chiseled_marble", "brasshaven:rust_rock",
        "brasshaven:rust_rock_bricks", "brasshaven:blue_slate", "brasshaven:blue_slate_tiles"]),
    ("tools", "gear", "brasshaven:excavator_pickaxe", ("Special tools", "Outils spéciaux"), [
        ("The Excavator Pickaxe mines 3x3 and the Lumber Axe fells whole trees. Sneak to break a single block.",
         "La pioche d'excavation mine en 3x3 et la hache de bûcheron abat l'arbre entier. Accroupi : un seul bloc."),
        ("Craft each with three Lithite shards and two sticks, shaped like a pickaxe or an axe.",
         "Fabrique-les avec trois éclats de lithite et deux bâtons, en forme de pioche ou de hache."),
    ], ["brasshaven:excavator_pickaxe", "brasshaven:lumber_axe"]),

    # ------------------------------------------------------------------ building tools
    ("wand", "building", "brasshaven:builder_wand", ("Builder's Wand", "Baguette du bâtisseur"), [
        ("It lays whole rows of blocks at once. Hold it and look at a block: gold outlines show where the copies "
         "will go. Right-click to extend that face with blocks of the same kind from your inventory (16 at a time, "
         "64 with the Master wand).",
         "Elle pose des rangées entières de blocs d'un coup. Tiens-la et regarde un bloc : des contours dorés "
         "montrent où iront les copies. Clic droit pour prolonger la face avec des blocs du même type pris dans ton "
         "inventaire (16 à la fois, 64 avec la baguette du maître)."),
        ("Made a mistake? Sneak-right-click in the air to undo the last use: the blocks come back to you.",
         "Une erreur ? Accroupi + clic droit dans le vide pour annuler : les blocs te reviennent."),
        ("Craft, in a column: an amethyst shard, a gold ingot, a stick. Master wand: the wand between two Lithite "
         "shards, a diamond above it.",
         "Fabrication, en colonne : un éclat d'améthyste, un lingot d'or, un bâton. Baguette du maître : la baguette "
         "entre deux éclats de lithite, un diamant au-dessus."),
    ], ["brasshaven:builder_wand", "brasshaven:master_builder_wand"]),
    ("symmetry", "building", "brasshaven:master_builder_wand", ("Wand symmetry", "Symétrie de la baguette"), [
        ("Build in mirror: every block the wand places is copied on the other side of a plane.",
         "Construis en miroir : chaque bloc posé par la baguette est copié de l'autre côté d'un plan."),
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
    ], []),
    ("chisel", "building", "brasshaven:chisel", ("Engraver's Chisel", "Burin du graveur"), [
        ("It carves a placed block into another variant of its family. Craft, in a column: an iron ingot, a brass "
         "ingot, a stick.",
         "Il taille un bloc posé en une autre variante de sa famille. Fabrication, en colonne : un lingot de fer, un "
         "lingot de laiton, un bâton."),
        ("Right-click a block: next variant (stone, bricks, mossy, cracked, chiseled...). Sneak-right-click: the "
         "previous one. Each cut uses one durability.",
         "Clic droit sur un bloc : variante suivante (pierre, briques, moussues, fissurées, sculptées...). Accroupi + "
         "clic droit : la précédente. Chaque taille use le burin d'un point."),
        ("Stairs, slabs and walls keep their shape; copper keeps its age and wax. Works on stone, deepslate, tuff, "
         "sandstone, quartz, prismarine, blackstone, terracotta, copper and the Brasshaven blocks.",
         "Escaliers, dalles et murets gardent leur forme ; le cuivre garde son oxydation et sa cire. Marche sur la "
         "pierre, l'ardoise des abîmes, le tuf, le grès, le quartz, la prismarine, la pierre noire, la terre cuite, "
         "le cuivre et les blocs Brasshaven."),
        ("Some steampunk variants only exist through the chisel: brass tiles, engraved brass, brass grille, copper "
         "tiles, dark iron bricks, mahogany parquet...",
         "Certaines variantes steampunk n'existent que par le burin : carreaux et grille en laiton, laiton gravé, "
         "carreaux de cuivre, briques de fer sombre, parquet d'acajou..."),
    ], ["brasshaven:chisel", "brasshaven:engraved_brass", "brasshaven:brass_tiles", "brasshaven:dark_iron_bricks",
        "brasshaven:mahogany_parquet"]),
    ("chisel_table", "building", "brasshaven:chisel_table", ("Chisel Table", "Table de taille"), [
        ("It carves a whole stack at once. Craft: two brass ingots, a chisel and five planks.",
         "Elle taille une pile entière d'un coup. Fabrication : deux lingots de laiton, un burin et cinq planches."),
        ("Right-click the table and put a stack of blocks in its slot: every variant of the family appears on the "
         "right. Click one to turn the whole stack into it.",
         "Clic droit sur la table et pose une pile de blocs dans sa case : toutes les variantes de la famille "
         "apparaissent à droite. Clique sur l'une d'elles pour y transformer toute la pile."),
        ("It is free and the table never wears out.", "C'est gratuit et la table ne s'use jamais."),
    ], ["brasshaven:chisel_table"]),
]

# Shown once per player, the first time something happens: (id, icon, (en, fr), manual page)
TIPS = [
    ("waystone", "brasshaven:waystone", ("Waystone discovered! Right-click it any time to travel.",
                                        "Pierre découverte ! Clic droit dessus pour voyager à tout moment."), "waystones"),
    ("grave", "brasshaven:grave", ("Your belongings wait in a grave where you fell. Right-click it to get them back.",
                                  "Tes affaires t'attendent dans une tombe là où tu es tombé. Clic droit dessus pour "
                                  "les récupérer."), "grave"),
    ("sorting_chest", "brasshaven:sorting_chest", ("Sorting chest: it sorts itself and pulls in nearby drops.",
                                                  "Coffre de tri : il se trie seul et aspire les objets proches."),
     "sorting_chest"),
    ("guild_terminal", "brasshaven:guild_terminal", ("Terminal: every chest of your base (48 blocks around) in one grid.",
                                                    "Terminal : tous les coffres de ta base (48 blocs autour) dans "
                                                    "une seule grille."), "guild_terminal"),
    ("elite", "minecraft:gold_ingot", ("An Elite! Gold name, hits hard, drops good loot.",
                                       "Un élite ! Nom doré, frappe fort, bon butin."), "danger"),
    ("blood_moon", "minecraft:redstone", ("A Blood Moon rises: monsters are much stronger tonight.",
                                          "Une Lune de sang se lève : les monstres sont bien plus forts cette nuit."),
     "blood_moon"),
    ("boss_mist", "brasshaven:mist_gate", ("Boss mist: walk through it to start the fight. It seals behind you.",
                                          "Brume de boss : traverse-la pour lancer le combat. Elle se referme "
                                          "derrière toi."), "bosses"),
    ("danger", "minecraft:skeleton_skull", ("The danger level rose: monsters here are stronger.",
                                            "Le niveau de danger augmente : les monstres sont plus forts ici."),
     "danger"),
    ("npc", "minecraft:emerald", ("A quest giver! Pick a contract, Accept it, then come back to hand it in.",
                                   "Un donneur de quêtes ! Choisis un contrat, accepte-le, puis reviens le rendre."),
     "contracts"),
    # the Guild Agent's survey contract (the progression ladder's compass step) was just handed in
    ("compass", "brasshaven:structure_compass", ("The Guild trusts you with a Structure Compass! Right-click: the "
                                                 "nearest structure. Sneak: choose which kind.",
                                                 "La Guilde te confie une boussole des structures ! Clic droit : la "
                                                 "structure la plus proche. Accroupi : choisis le type."), "compass"),
    # first login: the minimap has just appeared in the corner
    ("map", "minecraft:filled_map", ("The minimap shows the land around you. M: world map, H: hide it, Shift + H: its "
                                     "size, Z: zoom, B: ping the spot you look at.",
                                     "La mini-carte montre les alentours. M : carte du monde, H : la masquer, "
                                     "Maj + H : sa taille, Z : zoom, B : signaler l'endroit visé."), "map"),
]


# Words used by the manual screen itself (GuideScreen.java)
UI = {
    "guide.brasshaven.continued": ("(continued)", "(suite)"),
    "guide.brasshaven.more": ("More >", "Suite >"),
}


def lang():
    en, fr = dict((k, v[0]) for k, v in UI.items()), dict((k, v[1]) for k, v in UI.items())
    for cid, _icon, (ten, tfr) in CATEGORIES:
        en[f"guide.brasshaven.cat.{cid}"], fr[f"guide.brasshaven.cat.{cid}"] = ten, tfr
    for pid, _cat, _icon, (ten, tfr), paras, _items in PAGES:
        en[f"guide.brasshaven.{pid}.title"], fr[f"guide.brasshaven.{pid}.title"] = ten, tfr
        for i, (pe, pf) in enumerate(paras):
            en[f"guide.brasshaven.{pid}.p{i}"], fr[f"guide.brasshaven.{pid}.p{i}"] = pe, pf
    for tid, _icon, (te, tf), _page in TIPS:
        en[f"tip.brasshaven.{tid}"], fr[f"tip.brasshaven.{tid}"] = te, tf
    return en, fr


def _machine_pages():
    from .machines import GUIDE
    return [(pid, "machines", icon, title, paras, items) for pid, icon, title, paras, items in GUIDE]


PAGES += _machine_pages()


def _gadget_pages():
    from .gadgets import guide_pages
    return guide_pages()


PAGES += _gadget_pages()


def _ocean_pages():
    from .ocean import guide_pages
    return guide_pages()


PAGES += _ocean_pages()


def _social():
    """Multiplayer features (wf/social.py): their own category, pages and tip cards."""
    from . import social
    CATEGORIES.append(social.CATEGORY)
    TIPS.extend(social.TIPS)
    return social.guide_pages()


PAGES += _social()


def _denizens():
    """The peoples and creatures of the places (wf/denizens.py): their own category."""
    from . import denizens
    CATEGORIES.append(denizens.CATEGORY)
    return denizens.guide_pages()


PAGES += _denizens()


# ------------------------------------------------------------------ page layout estimate (validate.py, gen_gui.py)
# GuideScreen.java lays the pages out with the real font and splits a page that does not fit into continuation
# sheets, so nothing is ever cut. This mirrors that layout with Minecraft's default-font advances (glyph width
# + 1 px), at the smallest book size (384 x 232), so authors can see how many sheets a page needs.
_ADVANCE = {}
for _w, _chars in ((2, "!,.:;|'i¡"), (3, "l`í"), (4, " It[]îïì"), (5, "fk<>(){}\"*"), (7, "@~")):
    for _c in _chars:
        _ADVANCE[_c] = _w

BOOK_H = 232            # GuideScreen.MIN_H
TEXT_W = 384 - 156 - 14  # pageW() - 14
TEXT_LINE, PARA_GAP, ITEMS_ROW = 9, 5, 22


def char_width(c, bold=False):
    """Advance of a glyph of Minecraft's font; bold glyphs are 1 px wider (WfGui.bold titles)."""
    return _ADVANCE.get(c, 6) + (1 if bold else 0)


def text_width(s, bold=False):
    return sum(char_width(c, bold) for c in s)


def wrap(text, width, bold=False):
    """Line-wrap like Minecraft's StringSplitter: breaks at spaces and newlines, cuts words longer than a line."""
    lines = []
    space = char_width(" ", bold)
    for raw in text.split("\n"):
        line, w = "", 0
        for word in raw.split(" "):
            ww = text_width(word, bold)
            if line and w + space + ww > width:
                lines.append(line)
                line, w = "", 0
            if not line and ww > width:  # a word wider than the line is cut
                part, pw = "", 0
                for c in word:
                    if pw + char_width(c, bold) > width:
                        lines.append(part)
                        part, pw = "", 0
                    part, pw = part + c, pw + char_width(c, bold)
                line, w = part, pw
                continue
            line, w = (line + " " + word, w + space + ww) if line else (word, ww)
        lines.append(line)
    return lines


def _split(title, paras, has_items, compact_first, book_h, lang):
    card_bottom = book_h - 36

    def body(part, compact):
        t = title if part == 0 else title + " " + UI["guide.brasshaven.continued"][lang]
        tl = len(wrap(t, TEXT_W - 38 if compact else TEXT_W + 2, bold=True))  # GuideScreen titles are bold
        top = 25 + max(1, tl) * 10 + 6 if compact else 60 + tl * 10 + 4
        return top, card_bottom - 4 - (ITEMS_ROW if part == 0 and has_items else 0)

    sheets, cur = [], []
    y, bottom = body(0, compact_first)
    for para in paras:
        lines = wrap(para, TEXT_W)
        if cur:
            cur.append(None)
            y += PARA_GAP
        if cur and y + len(lines) * TEXT_LINE > bottom and len(lines) <= 3:
            cur.pop()
            sheets.append(cur)
            cur = []
            y, bottom = body(1, True)
        for line in lines:
            if y + TEXT_LINE > bottom and cur:
                if cur[-1] is None:
                    cur.pop()
                sheets.append(cur)
                cur = []
                y, bottom = body(1, True)
            cur.append(line)
            y += TEXT_LINE
    if cur or not sheets:
        sheets.append(cur)
    return sheets


def layout(title, paras, has_items, book_h=BOOK_H, lang=1, with_header=False):
    """Sheets of one page, as GuideScreen.paginate() builds them: a list of sheets, each a list of lines
    (None = paragraph gap). A page that only fits on one sheet with the compact header (small icon beside the
    title) uses it. lang: 0 English, 1 French (for the "(continued)" title suffix). with_header: also return
    whether the first sheet uses the compact header."""
    sheets, compact = _split(title, paras, has_items, False, book_h, lang), False
    if len(sheets) > 1:
        tight = _split(title, paras, has_items, True, book_h, lang)
        if len(tight) == 1:
            sheets, compact = tight, True
    return (sheets, compact) if with_header else sheets


def sheet_counts():
    """{page id: (sheets in English, sheets in French)} at the smallest book size."""
    out = {}
    for pid, _cat, _icon, (ten, tfr), paras, items in PAGES:
        out[pid] = (len(layout(ten, [p[0] for p in paras], bool(items), lang=0)),
                    len(layout(tfr, [p[1] for p in paras], bool(items), lang=1)))
    return out

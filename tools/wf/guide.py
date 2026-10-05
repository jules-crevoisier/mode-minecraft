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
    ("wonders", "minecraft:clock", ("Wonders", "Merveilles du monde")),
    ("storage", "wayfarers:sorting_chest", ("Storage", "Rangement")),
    ("danger", "minecraft:iron_sword", ("Danger & bosses", "Danger et boss")),
    ("automatons", "wayfarers:clockwork_heart", ("Automatons", "Automates")),
    ("gear", "wayfarers:lithite_shard", ("Gear & materials", "Équipement")),
    ("building", "wayfarers:builder_wand", ("Building tools", "Construction")),
    ("machines", "wayfarers:auto_harvester", ("Redstone machines", "Mécanismes")),
    ("gadgets", "wayfarers:brass_wrench", ("Steam gadgets", "Gadgets à vapeur")),
    ("oceans", "wayfarers:diving_helmet", ("Living oceans", "Océans vivants")),
]

# (id, category, icon, (title en, title fr), [(en, fr), ...paragraphs], [related item ids])
# Write each system as: what it is, how to get it, how to use it. Long pages are fine (the screen splits them into
# continuation sheets), but validate.py warns when a page needs more than two sheets.
PAGES = [
    # ------------------------------------------------------------------ getting started
    ("welcome", "start", "wayfarers:wayfarer_atlas", ("Welcome, Wayfarer", "Bienvenue, Voyageur"), [
        ("This world hides dozens of hand-built structures, dungeons, bosses and giant wonders. Your group explores "
         "it together: quests, waystones and discoveries are shared by everyone.",
         "Ce monde cache des dizaines de structures, de donjons, de boss et de merveilles géantes. Ton groupe "
         "l'explore ensemble : quêtes, pierres de voyage et découvertes sont partagées par tous."),
        ("To begin, press J (or use the Wayfarer's Atlas) and follow the first chapter of quests.",
         "Pour commencer, appuie sur J (ou utilise l'Atlas du Voyageur) et suis le premier chapitre de quêtes."),
        ("This manual explains every system. Click a page in the contents on the left; turn pages with the arrows, "
         "the mouse wheel or the arrow keys. When a page goes on, the button reads \"More >\".",
         "Ce manuel explique chaque système. Clique une page dans le sommaire à gauche ; tourne les pages avec les "
         "flèches, la molette ou les touches fléchées. Quand une page continue, le bouton affiche « Suite > »."),
        ("Shortcut: hover a Wayfarers item in your inventory and hold the manual key (W, or the key its tooltip "
         "shows; Controls to change it) to open its page. Lost the manual? Craft a book and a feather.",
         "Raccourci : survole un objet Wayfarers dans ton inventaire et maintiens la touche du manuel (Z sur un "
         "clavier AZERTY, celle qu'indique l'infobulle ; réglable dans Commandes) pour ouvrir sa page. Manuel "
         "perdu ? Un livre et une plume."),
    ], ["wayfarers:wayfarer_atlas", "wayfarers:wayfarer_manual"]),
    ("quests", "start", "minecraft:writable_book", ("Quests & journal", "Quêtes et journal"), [
        ("Open the journal with J or by using the Wayfarer's Atlas. Five chapters lead you from the first Guild "
         "Outpost to the End; each quest shows its objective, your progress and its rewards.",
         "Ouvre le journal avec J ou en utilisant l'Atlas du Voyageur. Cinq chapitres te mènent du premier "
         "avant-poste de la Guilde jusqu'à l'End ; chaque quête affiche son objectif, ta progression et ses "
         "récompenses."),
        ("Click Track to pin a quest to the top-right of your screen. When it is done, the tracker moves on to "
         "the next quest by itself.",
         "Clique sur Suivre pour épingler une quête en haut à droite de l'écran. Une fois terminée, le suivi passe "
         "tout seul à la quête suivante."),
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
         "count), find a structure (just walk into it), and deliver a sealed parcel to another quest giver.",
         "Quatre sortes : apporter des objets (ils sont pris quand tu les rends), chasser des créatures (les "
         "victimes après avoir accepté comptent), trouver une structure (il suffit d'y entrer), et livrer un colis "
         "scellé à un autre donneur de quêtes."),
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
         "G: Builder's Wand symmetry\nW (held over an item): its manual page",
         "J : journal de quêtes\nK : arbre de talents\nV : utiliser le talent actif\nR : trier l'inventaire\n"
         "M : carte du monde\nH : afficher/masquer la mini-carte\nMaj + H : taille de la mini-carte\n"
         "Z : zoom de la mini-carte\nB : signaler l'endroit visé\n"
         "N : allumer/éteindre l'aimant\nG : symétrie de la baguette\nW (maintenu sur un objet) : sa page du manuel"),
        ("These are the keys of a QWERTY keyboard: Options > Controls, Wayfarers section, shows yours and changes "
         "them. Display settings (health bars, damage numbers, tracker, tips, and the minimap's size, corner, shape, "
         "rotation, coordinates and opacity): Config button of Wayfarers in the mods list.",
         "Ce sont les touches d'un clavier QWERTY (en AZERTY : W devient Z, Z devient W et M devient la virgule) : "
         "Options > Commandes, rubrique Wayfarers, montre les tiennes et les change. Réglages d'affichage (barres de "
         "vie, chiffres de dégâts, suivi, astuces, et taille, coin, forme, rotation, coordonnées et opacité de "
         "la mini-carte) : bouton Config de Wayfarers dans la liste des mods."),
    ], []),
    ("compass", "start", "wayfarers:structure_compass", ("Structure Compass", "Boussole des structures"), [
        ("It finds Wayfarers structures. You get one when you first arrive; craft more with a compass surrounded by "
         "four Map Fragments.",
         "Elle trouve les structures Wayfarers. Tu en reçois une à ton arrivée ; fabrique-en d'autres avec une "
         "boussole entourée de quatre fragments de carte."),
        ("Right-click: the chat shows the nearest one (name, distance, direction and coordinates) and sparks show "
         "the way.",
         "Clic droit : le chat affiche la plus proche (nom, distance, direction et coordonnées) et des étincelles "
         "montrent le chemin."),
        ("Sneak-right-click: choose which structure to look for, one kind at a time, or \"any structure\". The "
         "wonders come at the end of the list.",
         "Accroupi + clic droit : choisis le type de structure recherché, un à la fois, ou « n'importe quelle "
         "structure ». Les merveilles sont à la fin de la liste."),
    ], ["wayfarers:structure_compass"]),
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
    ], ["wayfarers:oblivion_vial"]),
    ("magic", "talents", "wayfarers:fire_staff", ("Magic", "Magie"), [
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
        ("More mana: an Arcane Ring (+50 mana) or a Mana Amulet (faster regeneration) work just by being in your "
         "inventory. Arcanist talents and robes make spells stronger.",
         "Plus de mana : un Anneau arcanique (+50 mana) ou une Amulette de mana (recharge plus rapide) agissent "
         "simplement en étant dans ton inventaire. Les talents et les robes d'arcaniste renforcent les sorts."),
    ], ["wayfarers:fire_staff", "wayfarers:frost_staff", "wayfarers:thunder_staff", "wayfarers:healing_staff",
        "wayfarers:levitation_wand", "wayfarers:ward_orb", "wayfarers:steam_cane", "wayfarers:arcane_ring",
        "wayfarers:mana_amulet"]),

    # ------------------------------------------------------------------ travel
    ("waystones", "travel", "wayfarers:waystone", ("Waystones", "Pierres de voyage"), [
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
    ], ["wayfarers:waystone"]),
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
        ("More settings: Mods > Wayfarers > Config, Minimap tab.",
         "Autres réglages : Mods > Wayfarers > Config, onglet Mini-carte."),
    ], ["wayfarers:wayfarer_atlas"]),
    ("recall", "travel", "wayfarers:recall_scroll", ("Recall Scroll", "Parchemin de rappel"), [
        ("Use it to return instantly to the nearest waystone of your dimension. It is used up.",
         "Utilise-le pour revenir aussitôt à la pierre de voyage la plus proche de ta dimension. Il est consommé."),
        ("Elites sometimes drop one. Craft 2 with paper, a Map Fragment and an ender pearl.",
         "Les élites en lâchent parfois. Fabrique-en 2 avec du papier, un fragment de carte et une perle de l'Ender."),
    ], ["wayfarers:recall_scroll"]),
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
    ], ["wayfarers:waystone", "wayfarers:edison_lamp", "minecraft:bell"]),

    # ------------------------------------------------------------------ wonders
    ("wonders", "wonders", "wayfarers:structure_compass", ("How to find them", "Où les trouver"), [
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
    ("sky_harbour", "wonders", "wayfarers:airship_compass", ("Sky Harbour", "Port céleste"), [
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
    ("dwarven_city", "wonders", "wayfarers:mithril_block", ("Deep Dwarven City", "Cité naine des profondeurs"), [
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
    ("inventor_manor", "wonders", "wayfarers:redstone_timer", ("Inventor's Manor", "Manoir de l'inventeur"), [
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
    ("sky_isles", "wonders", "wayfarers:aether_crystal", ("Sky Isles", "Îles célestes"), [
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
    ("sorting_chest", "storage", "wayfarers:sorting_chest", ("Sorting Chest", "Coffre de tri"), [
        ("A big 54-slot chest that sorts itself when nobody is looking inside, and vacuums items dropped "
         "within 6 blocks.",
         "Un grand coffre de 54 cases qui se trie tout seul quand personne ne regarde dedans, et aspire les objets "
         "lâchés à 6 blocs."),
        ("Sneak-right-click to sort it right now. Put one next to your mob farm or your mine entrance.",
         "Accroupi + clic droit pour le trier tout de suite. Pose-en un près de ta ferme ou de l'entrée de ta mine."),
        ("Craft: a chest, a hopper and seven planks.", "Fabrication : un coffre, un entonnoir et sept planches."),
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
        ("Craft: a barrel, four iron ingots and four planks.",
         "Fabrication : un tonneau, quatre lingots de fer et quatre planches."),
    ], ["wayfarers:compacting_crate"]),
    ("guild_terminal", "storage", "wayfarers:guild_terminal", ("Guild Terminal", "Terminal de guilde"), [
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
    ], ["wayfarers:guild_terminal"]),
    ("terminal_network", "storage", "wayfarers:guild_terminal", ("Terminal: network & sorting",
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
    ("storage_relay", "storage", "wayfarers:storage_relay", ("Storage Relay", "Relais de stockage"), [
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
    ], ["wayfarers:storage_relay"]),
    ("backpack", "storage", "wayfarers:travel_backpack", ("Backpacks", "Sacs"), [
        ("Travel Backpack: hold it and right-click to open 27 extra slots that travel with you. Craft: a chest, a "
         "string and seven leather.",
         "Sac du Voyageur : tiens-le et fais clic droit pour ouvrir 27 cases en plus qui voyagent avec toi. "
         "Fabrication : un coffre, une ficelle et sept cuirs."),
        ("Explorer's Backpack: 54 slots. Craft your Travel Backpack with a brass ingot: nothing inside is lost.",
         "Sac de l'Explorateur : 54 cases. Fabrique-le avec ton Sac du Voyageur et un lingot de laiton : rien de son "
         "contenu n'est perdu."),
    ], ["wayfarers:travel_backpack", "wayfarers:explorer_backpack"]),
    ("magnet", "storage", "wayfarers:magnet_ring", ("Magnet Ring", "Anneau aimanté"), [
        ("While it is in your inventory and switched on (it glows), items and experience within 7 blocks fly to you.",
         "Tant qu'il est dans ton inventaire et allumé (il brille), objets et expérience à 7 blocs volent vers toi."),
        ("Right-click it or press N to switch it on or off.", "Clic droit ou touche N pour l'allumer ou l'éteindre."),
        ("Craft: two Map Fragments, a redstone and three iron ingots.",
         "Fabrication : deux fragments de carte, une redstone et trois lingots de fer."),
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
    ("sorting", "storage", "minecraft:chest", ("Inventory sorting", "Trier l'inventaire"), [
        ("Press R to sort your main inventory (not the hotbar or armour): stacks are merged and grouped.",
         "Appuie sur R pour trier ton inventaire principal (ni la barre d'action ni l'armure) : les piles sont "
         "fusionnées et regroupées."),
    ], []),
    ("grave", "storage", "wayfarers:grave", ("Graves", "Tombes"), [
        ("When you die, your belongings are kept in a grave where you fell. Its coordinates are sent in the chat.",
         "Quand tu meurs, tes affaires sont gardées dans une tombe là où tu es tombé. Ses coordonnées s'affichent "
         "dans le chat."),
        ("Right-click the grave to get everything back. A friend can also open it: the items then go into their "
         "inventory.",
         "Clic droit sur la tombe pour tout récupérer. Un ami peut aussi l'ouvrir : les objets vont alors dans son "
         "inventaire."),
    ], ["wayfarers:grave"]),

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
    ("bosses", "danger", "wayfarers:boss_seal", ("Bosses", "Boss"), [
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
    ], ["wayfarers:boss_seal", "wayfarers:mist_gate"]),
    ("remembrance", "danger", "minecraft:nether_star", ("Boss weapons", "Armes de boss"), [
        ("Every boss drops its Remembrance. Craft it with four materials of its region (Map Fragments, Lithite, "
         "Ancient Embers or Void Shards) and two diamonds to forge its unique weapon, with a special right-click "
         "power.",
         "Chaque boss lâche son Souvenir. Fabrique-le avec quatre matériaux de sa région (fragments de carte, "
         "lithite, braises anciennes ou éclats du vide) et deux diamants pour forger son arme unique, avec un "
         "pouvoir au clic droit."),
    ], []),

    # ------------------------------------------------------------------ automatons
    ("brass_golem", "automatons", "wayfarers:clockwork_heart", ("Brass Golem", "Golem de laiton"), [
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
    ], ["wayfarers:clockwork_heart", "wayfarers:brass_gear", "wayfarers:brass_golem_spawn_egg"]),
    ("brass_golem_orders", "automatons", "wayfarers:brass_ingot", ("Golem orders", "Ordres du golem"), [
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
    ], ["wayfarers:brass_block"]),
    ("clockwork_spider", "automatons", "wayfarers:brass_gear", ("Clockwork Spider", "Araignée-horloge"), [
        ("Hostile clockwork spiders that roam in packs at night in the badlands and the savanna highlands, and in "
         "the Clockwork Citadel and the Undercity. They climb walls.",
         "Des araignées mécaniques hostiles qui rôdent en bande la nuit dans les badlands et les hautes savanes, "
         "ainsi que dans la Citadelle d'horlogerie et les Bas-fonds. Elles grimpent aux murs."),
        ("When one stops and its key whirs, it is about to leap: step aside. They drop brass nuggets, redstone and "
         "sometimes a brass gear.",
         "Quand l'une s'arrête et que sa clé s'emballe, elle va bondir : écarte-toi. Elles lâchent des pépites de "
         "laiton, de la redstone et parfois un engrenage."),
    ], ["wayfarers:clockwork_spider_spawn_egg"]),
    ("steam_drone", "automatons", "wayfarers:brass_nugget", ("Steam Drone", "Drone à vapeur"), [
        ("Hostile flying drones: at night over the steampunk lands, and in the Undercity. They circle and fire hot "
         "rivets.",
         "Des drones volants hostiles : la nuit au-dessus des terres steampunk, et dans les Bas-fonds. Ils tournent "
         "autour de toi et tirent des rivets brûlants."),
        ("When one rears up, it is about to dive at you: step aside. A bow brings them down. They drop brass "
         "nuggets, copper and sometimes a brass gear.",
         "Quand l'un se cabre, il va plonger sur toi : écarte-toi. Un arc les abat facilement. Ils lâchent des "
         "pépites de laiton, du cuivre et parfois un engrenage."),
    ], ["wayfarers:steam_drone_spawn_egg"]),
    ("grand_clockmaker", "automatons", "wayfarers:remembrance_grand_clockmaker",
     ("The Grand Clockmaker", "Le Grand Horloger"), [
        ("The boss of the Clockwork Citadel (400 health). A stair in the tower's entrance hall goes down through the "
         "gearworks to a waiting room with a waystone, before the mist of the Clock Vault.",
         "Le boss de la Citadelle d'horlogerie (400 PV). Un escalier dans le hall de la tour descend par la salle des "
         "engrenages jusqu'à une salle d'attente avec une pierre de voyage, devant la brume du Caveau de l'horloge."),
        ("He sweeps his pendulum cane, slams it (jump the ring of sparks), throws cogs and winds up spiders. When "
         "his hands rewind and a ring closes around him, get out of it or be frozen in time.",
         "Il balaie avec sa canne-pendule, l'abat au sol (saute l'anneau d'étincelles), lance des engrenages et "
         "remonte des araignées. Quand ses aiguilles reculent et qu'un cercle se referme, sors-en ou tu seras figé."),
    ], ["wayfarers:remembrance_grand_clockmaker", "wayfarers:clockmaker_pendulum"]),
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
        ("Craft them like iron armour: Explorer from leather and Map Fragments, Ember from Ancient Embers, Void from "
         "Void Shards.",
         "Fabrique-les comme une armure en fer : Explorateur avec du cuir et des fragments de carte, Braise avec des "
         "braises anciennes, Vide avec des éclats du vide."),
    ], ["wayfarers:explorer_chestplate", "wayfarers:ember_chestplate", "wayfarers:void_chestplate"]),
    ("ores", "gear", "wayfarers:zinc_ingot", ("Ores & brass", "Minerais et laiton"), [
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
    ("metal_armor", "gear", "wayfarers:brass_helmet", ("Advanced armour", "Armures avancées"), [
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
    ], ["wayfarers:brass_helmet", "wayfarers:mithril_chestplate", "wayfarers:aether_chestplate",
        "wayfarers:arcane_chestplate"]),
    ("steam_blocks", "gear", "wayfarers:gear_panel", ("Steampunk blocks", "Blocs steampunk"), [
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
    ], ["wayfarers:brass_plating", "wayfarers:gear_panel", "wayfarers:copper_pipes", "wayfarers:edison_lamp",
        "wayfarers:aether_conduit", "wayfarers:mahogany_panelling"]),
    ("world_woods", "gear", "wayfarers:glowwood_sapling", ("Glowwood and Rustwood", "Bois-lueur et bois rouillé"), [
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
    ], ["wayfarers:glowwood_sapling", "wayfarers:rustwood_sapling", "wayfarers:glowwood_log", "wayfarers:rustwood_log",
        "wayfarers:glowwood_planks", "wayfarers:rustwood_planks", "wayfarers:glowwood_leaves",
        "wayfarers:rustwood_leaves"]),
    ("world_stones", "gear", "wayfarers:marble_pillar", ("Marble, rust rock, blue slate", "Marbre, roche rouillée, ardoise bleue"), [
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
    ], ["wayfarers:marble", "wayfarers:marble_pillar", "wayfarers:chiseled_marble", "wayfarers:rust_rock",
        "wayfarers:rust_rock_bricks", "wayfarers:blue_slate", "wayfarers:blue_slate_tiles"]),
    ("tools", "gear", "wayfarers:excavator_pickaxe", ("Special tools", "Outils spéciaux"), [
        ("The Excavator Pickaxe mines 3x3 and the Lumber Axe fells whole trees. Sneak to break a single block.",
         "La pioche d'excavation mine en 3x3 et la hache de bûcheron abat l'arbre entier. Accroupi : un seul bloc."),
        ("Craft each with three Lithite shards and two sticks, shaped like a pickaxe or an axe.",
         "Fabrique-les avec trois éclats de lithite et deux bâtons, en forme de pioche ou de hache."),
    ], ["wayfarers:excavator_pickaxe", "wayfarers:lumber_axe"]),

    # ------------------------------------------------------------------ building tools
    ("wand", "building", "wayfarers:builder_wand", ("Builder's Wand", "Baguette du bâtisseur"), [
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
    ], ["wayfarers:builder_wand", "wayfarers:master_builder_wand"]),
    ("symmetry", "building", "wayfarers:master_builder_wand", ("Wand symmetry", "Symétrie de la baguette"), [
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
    ("chisel", "building", "wayfarers:chisel", ("Engraver's Chisel", "Burin du graveur"), [
        ("It carves a placed block into another variant of its family. Craft, in a column: an iron ingot, a brass "
         "ingot, a stick.",
         "Il taille un bloc posé en une autre variante de sa famille. Fabrication, en colonne : un lingot de fer, un "
         "lingot de laiton, un bâton."),
        ("Right-click a block: next variant (stone, bricks, mossy, cracked, chiseled...). Sneak-right-click: the "
         "previous one. Each cut uses one durability.",
         "Clic droit sur un bloc : variante suivante (pierre, briques, moussues, fissurées, sculptées...). Accroupi + "
         "clic droit : la précédente. Chaque taille use le burin d'un point."),
        ("Stairs, slabs and walls keep their shape; copper keeps its age and wax. Works on stone, deepslate, tuff, "
         "sandstone, quartz, prismarine, blackstone, terracotta, copper and the Wayfarers blocks.",
         "Escaliers, dalles et murets gardent leur forme ; le cuivre garde son oxydation et sa cire. Marche sur la "
         "pierre, l'ardoise des abîmes, le tuf, le grès, le quartz, la prismarine, la pierre noire, la terre cuite, "
         "le cuivre et les blocs Wayfarers."),
        ("Some steampunk variants only exist through the chisel: brass tiles, engraved brass, brass grille, copper "
         "tiles, dark iron bricks, mahogany parquet...",
         "Certaines variantes steampunk n'existent que par le burin : carreaux et grille en laiton, laiton gravé, "
         "carreaux de cuivre, briques de fer sombre, parquet d'acajou..."),
    ], ["wayfarers:chisel", "wayfarers:engraved_brass", "wayfarers:brass_tiles", "wayfarers:dark_iron_bricks",
        "wayfarers:mahogany_parquet"]),
    ("chisel_table", "building", "wayfarers:chisel_table", ("Chisel Table", "Table de taille"), [
        ("It carves a whole stack at once. Craft: two brass ingots, a chisel and five planks.",
         "Elle taille une pile entière d'un coup. Fabrication : deux lingots de laiton, un burin et cinq planches."),
        ("Right-click the table and put a stack of blocks in its slot: every variant of the family appears on the "
         "right. Click one to turn the whole stack into it.",
         "Clic droit sur la table et pose une pile de blocs dans sa case : toutes les variantes de la famille "
         "apparaissent à droite. Clique sur l'une d'elles pour y transformer toute la pile."),
        ("It is free and the table never wears out.", "C'est gratuit et la table ne s'use jamais."),
    ], ["wayfarers:chisel_table"]),
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
    ("guild_terminal", "wayfarers:guild_terminal", ("Terminal: every chest of your base (48 blocks around) in one grid.",
                                                    "Terminal : tous les coffres de ta base (48 blocs autour) dans "
                                                    "une seule grille."), "guild_terminal"),
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
    ("npc", "minecraft:emerald", ("A quest giver! Pick a contract, Accept it, then come back to hand it in.",
                                   "Un donneur de quêtes ! Choisis un contrat, accepte-le, puis reviens le rendre."),
     "contracts"),
    # first login: the minimap has just appeared in the corner
    ("map", "minecraft:filled_map", ("The minimap shows the land around you. M: world map, H: hide it, Shift + H: its "
                                     "size, Z: zoom, B: ping the spot you look at.",
                                     "La mini-carte montre les alentours. M : carte du monde, H : la masquer, "
                                     "Maj + H : sa taille, Z : zoom, B : signaler l'endroit visé."), "map"),
]


# Words used by the manual screen itself (GuideScreen.java)
UI = {
    "guide.wayfarers.continued": ("(continued)", "(suite)"),
    "guide.wayfarers.more": ("More >", "Suite >"),
}


def lang():
    en, fr = dict((k, v[0]) for k, v in UI.items()), dict((k, v[1]) for k, v in UI.items())
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


def _ocean_pages():
    from .ocean import guide_pages
    return guide_pages()


PAGES += _ocean_pages()


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
        t = title if part == 0 else title + " " + UI["guide.wayfarers.continued"][lang]
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

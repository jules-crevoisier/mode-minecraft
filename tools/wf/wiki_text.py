"""French editorial text for the illustrated wiki (tools/gen_wiki.py).

Everything else in the wiki comes from the data tables (content, guide, machines, metals, skills, biomes,
structures, recipes, loot...). This file only adds the plain-language explanations that the data does not
carry. Every table is optional: an id missing here still gets a card, with an automatic description.
"""

TAGLINE = ("Un mod d'exploration à plusieurs pour Minecraft 26.2 : des dizaines de structures géantes, des boss "
           "façon Elden Ring, un monde neuf, de la magie, des machines simples et tout le confort pour ranger "
           "moins et explorer plus.")

# "Par où commencer" : (titre, texte, [ids d'objets illustrés])
FIRST_HOUR = [
    ("Ouvre le Manuel", "Tu le reçois à la première connexion. Une page par système, avec sommaire. Astuce : survole "
     "n'importe quel objet du mod dans ton inventaire et maintiens W pour ouvrir directement sa page.",
     ["wayfarer_manual"]),
    ("Suis les quêtes (touche J)", "Le journal de quêtes te guide pas à pas. Clique sur « Suivre » : l'objectif "
     "s'affiche en haut à droite de l'écran. La progression est commune à tout le groupe.",
     ["wayfarer_atlas"]),
    ("Trouve un Avant-poste de la Guilde", "C'est la première structure à chercher : on y trouve des fragments de "
     "carte (le matériau de base du mod) et souvent une pierre de voyage. La boussole des structures aide à la "
     "trouver.", ["map_fragment", "structure_compass"]),
    ("Active les pierres de voyage", "Clic droit sur une pierre : elle est découverte pour tout le groupe. Ensuite, "
     "depuis n'importe quelle pierre, tu voyages vers toutes les autres. Fabrique-en une pour ta base.",
     ["waystone", "recall_scroll"]),
    ("Fabrique ton sac et ton coffre de tri", "Le Sac du Voyageur ajoute 27 cases qui te suivent. Le coffre de tri "
     "range tout seul et aspire ce qui traîne autour. Dans chaque coffre, des boutons en laiton trient et rangent "
     "pour toi.", ["travel_backpack", "sorting_chest"]),
    ("Fonds ton premier laiton", "Le zinc est courant dans la pierre. 3 lingots de cuivre + 1 lingot de zinc = 4 "
     "lingots de laiton. Le laiton sert à presque toutes les machines.", ["zinc_ingot", "brass_ingot"]),
    ("Pose ta première machine", "Un arroseur au milieu d'un champ, une moissonneuse au bord avec un coffre collé : "
     "ta ferme tourne toute seule. Aucun câble, aucune énergie.", ["sprinkler", "auto_harvester"]),
    ("Dépense tes talents (touche K)", "Chaque quête donne des points. Choisis une branche (Guerrier, Explorateur, "
     "Arcaniste, Mécaniste) ; le dernier talent de chaque branche est un pouvoir à lancer avec V.",
     ["oblivion_vial"]),
]

KEY_TEXT = {
    "J": "Journal de quêtes",
    "K": "Arbre de talents",
    "V": "Lancer le talent actif (le pouvoir équipé)",
    "R": "Trier l'inventaire principal (la barre d'action n'est pas touchée)",
    "M": "Allumer / éteindre l'anneau aimanté",
    "W": "Maintenir sur un objet du mod : ouvrir sa page du Manuel",
    "Clic molette": "Sur une case d'un coffre : trier ce coffre",
}

COMMANDS = {
    "atlas": ("tous", "Affiche le résumé de la guilde (utilisé par l'Atlas)."),
    "waystones": ("tous", "Liste les pierres de voyage découvertes."),
    "sort": ("tous", "Trie ton inventaire (comme la touche R)."),
    "magnet": ("tous", "Bascule l'anneau aimanté (comme la touche M)."),
    "warp": ("op", "Téléporte directement vers une pierre de voyage."),
    "kit": ("op", "Donne un kit d'équipement par palier : starter, explorer, depths, nether, end."),
    "demo": ("op", "Donne tout le contenu du mod d'un coup (idéal pour tester ou filmer)."),
    "locate": ("op", "Indique où se trouve la structure demandée."),
    "tp": ("op", "Téléporte vers la structure demandée (la génère si besoin)."),
    "boss": ("op", "Fait apparaître un boss devant toi, pour le tester."),
    "worldmap": ("op", "Écrit une carte des biomes autour de toi (images PNG dans le dossier du monde)."),
    "progress": ("op", "reset : remet la quête à zéro ; complete : accorde toutes les quêtes."),
}

CONFIG_FR = {
    "world.overhaul": "Les nouveaux mondes utilisent le relief, les grottes et les 41 biomes de Wayfarers.",
    "danger.enabled": "Les monstres deviennent plus forts en s'éloignant du spawn, et dans le Nether et l'End.",
    "danger.blocksPerLevel": "Nombre de blocs depuis le spawn pour gagner un niveau de danger.",
    "danger.maxLevel": "Niveau de danger maximal.",
    "danger.healthPerLevel": "Vie en plus par niveau (0.15 = +15 %).",
    "danger.damagePerLevel": "Dégâts en plus par niveau (0.12 = +12 %).",
    "elite.baseChance": "Chance de base qu'un monstre soit un élite (+2 % par niveau).",
    "bloodMoon.enabled": "Active les lunes de sang.",
    "bloodMoon.interval": "Une lune de sang toutes les N nuits.",
    "quests.tracked": "Quête suivie à l'écran (réglée depuis le journal).",
    "quests.showTracker": "Affiche la quête suivie en haut à droite.",
    "hud.healthBars": "Barres de vie au-dessus des créatures : ALWAYS (toujours), DAMAGED (blessées ou ciblées), NEVER.",
    "hud.damageNumbers": "Chiffres de dégâts flottants quand tu frappes.",
    "hud.tips": "Cartes d'astuce la première fois que tu découvres un système.",
}

# Confort de jeu qui n'a pas d'objet : (titre, texte)
QOL = [
    ("Récolte au clic droit", "Clic droit sur une culture mûre : elle est récoltée et replantée d'un coup."),
    ("Recharge de la barre", "Quand la pile en main est épuisée, la suivante du même objet prend sa place."),
    ("Boutons de rangement", "Dans chaque coffre, tonneau ou sac : Trier, Tout prendre, Déposer les identiques, "
     "Ranger dans les coffres proches (8 blocs), et une barre de recherche qui allume les cases."),
    ("Barres de vie et dégâts", "Une barre de vie apparaît au-dessus des créatures blessées, avec les dégâts "
     "infligés en chiffres flottants. Les élites ont un cadre doré. Réglable dans la config client."),
    ("Tombes", "À ta mort, tes affaires sont gardées dans une tombe ; ses coordonnées s'affichent dans le chat. "
     "N'importe quel membre du groupe peut la vider."),
    ("Cartes d'astuce", "La première fois que tu rencontres un système (pierre, élite, lune de sang...), une petite "
     "carte l'explique en une phrase."),
    ("Danger et élites", "Plus tu t'éloignes du spawn (+1 niveau tous les 900 blocs), plus les monstres ont de vie "
     "et de dégâts. Les élites (nom doré) lâchent un meilleur butin. Une lune de sang tous les 7 nuits."),
]

DIMENSIONS = {"overworld": "Surface", "nether": "Nether", "end": "End"}

# Merveilles (méga-structures) : affichées en grand, avec rotation 360° et vue en coupe.
WONDERS = ["clockwork_citadel", "sky_harbour", "undercity", "sunken_citadel"]

STRUCTURES = {
    "guild_outpost": "Fort de la Guilde avec rempart, châtelet, grande salle et tour des cartes de 46 blocs. "
                     "Première structure à trouver : fragments de carte et pierre de voyage. Trois variantes.",
    "mountain_monastery": "Église gothique à arcs-boutants avec clocher de 46 blocs, cloître et bibliothèque. Sous la "
                          "crypte secrète, la chambre de la cloche du Sonneur de glas.",
    "forgotten_library": "Nef gothique, tours jumelles et rotonde effondrée. Derrière un cabinet secret, les archives "
                         "interdites de l'Archiviste.",
    "coastal_lighthouse": "Phare de 52 blocs sur un cap, avec quai et grotte marine.",
    "giant_tree": "Tronc creux de 15 blocs de large, trois terrasses de cabanes reliées par des ponts de corde. La "
                  "Mère-Racine attend dans la caverne des racines.",
    "desert_oasis": "Caravansérail à coupoles et minarets, bazar et colosse de pharaon à moitié enseveli. Le tombeau "
                    "caché mène à la salle funéraire du Pharaon ensablé.",
    "witch_huts": "Maisons tordues sur pilotis, tour au chapeau pointu et cercle rituel. Sous le marais, la grotte "
                  "inondée de la Grand-Mère du marais.",
    "sky_island": "Temple de quartz flottant à 40 blocs du sol, îlots reliés par des ponts et cascades. Le "
                  "Chevalier-griffon combat sur l'esplanade.",
    "jungle_ziggurat": "Pyramide à 8 gradins, têtes de serpent à plumes, jeu de balle. Sous la pyramide, le cénote "
                       "sacré du Jaguar de jade.",
    "ruined_watchtower": "Tour de guet : une version en ruine au sommet effondré, une version intacte avec flèche. "
                         "Cave secrète.",
    "bandit_camp": "Palissade, tours de guet et tente du chef, gardés par des pillards.",
    "rune_circle": "Trilithes de 13 blocs autour d'un autel. La crypte mène à la voûte des runes du Colosse runique.",
    "ice_observatory": "Dôme de neige, télescope de cuivre et laboratoire en sous-sol.",
    "galleon_wreck": "Galion à trois ponts couché au fond de l'eau, château arrière et mât brisé.",
    "sunken_temple": "Sanctuaire à coupole sous l'océan, obélisques, conduit actif et caveau secret.",
    "dwarven_mine": "Chevalement de 20 blocs, village à flanc de colline, quatre galeries et une salle forte scellée.",
    "dwarven_forge": "Salle souterraine de 63 × 31 blocs à piliers de lithite, statues de rois nains de 25 blocs, "
                     "chutes de lave. Le Roi-Forgeron garde son creuset.",
    "crystal_grotto": "Géode géante avec gouffre, flèches de cristal, atelier de taille et ponts. Au fond du nid : la "
                      "Matriarche de cristal.",
    "sealed_lab": "Sas, salle de contrôle en dôme et huit cellules de confinement, dont une brèche de sculk. Au "
                  "cœur : le Rejeton du sculk.",
    "sunken_citadel": "Cathédrale gothique de prismarine au fond de l'océan : tour de 76 blocs qui sort de l'eau, "
                      "six salles reliées par des tunnels de verre, arène du Gardien englouti sous un dôme de 40 blocs.",
    "basalt_fortress": "Citadelle noire de 89 blocs, douves de lave, tours de 48 blocs et pont-levis. Le Seigneur des "
                       "Cendres siège sur son trône.",
    "chain_bridge": "Tablier de 60 blocs suspendu à des maillons géants entre deux tours-portes, au-dessus de la lave.",
    "piglin_sanctuary": "Ziggourat surmontée d'une idole d'or de 34 blocs. Le Roi piglin doré garde son trésor.",
    "lava_foundry": "Usine sur pilotis au-dessus de la lave : cheminées, creusets et grue.",
    "soul_tower": "Tour de 72 blocs enlacée de contreforts d'os. La Faucheuse des âmes attend au sommet.",
    "piglin_market": "Bazar fortifié aux auvents rayés autour d'une tour centrale, avec des marchands piglins.",
    "void_observatory": "Observatoire perché sur les îles extérieures de l'End.",
    "chorus_garden": "Jardin flottant de plantes de chorus, terrasses et bassins suspendus.",
    "end_archive": "Bibliothèque de l'End gardée par des traqueurs du vide.",
    "void_ship": "Épave d'un vaisseau échoué entre les îles de l'End.",
    "void_nest": "Le repaire final : l'arène du Gardien du vide, sur les îles extérieures de l'End.",
    "forgotten_catacombs": "Donjon : un mausolée en surface mène à 2 ou 3 niveaux de cryptes et d'ossuaires tirés au "
                           "hasard. Au fond, le Chevalier des tombes.",
    "sand_hypogeum": "Donjon : un temple ensablé mène à des galeries funéraires et des pièges. Au fond, la Matriarche "
                     "d'os.",
    "lithite_well": "Donjon : une tête de puits dans les montagnes plonge vers des galeries hantées. Au fond, la Dame "
                    "en pleurs.",
    "void_crypt": "Donjon de l'End : un cercle d'obélisques mène à une crypte grouillante de larves. Au fond, la "
                  "Mère-Larve.",
    "clockwork_citadel": "Une ville steampunk de 71 × 71 blocs autour d'une tour-horloge de 75 blocs : quatre cadrans, "
                         "beffroi, flèche de cuivre oxydé, sept étages meublés, quatre ateliers et quatre cheminées "
                         "fumantes reliées par des tuyaux.",
    "sky_harbour": "Une tour d'amarrage en fer de 44 blocs, avec un dirigeable à vapeur accosté à son sommet : coque "
                   "en acajou, hublots, cabine, hélice et enveloppe rayée. Visible de très loin au-dessus des plaines.",
    "undercity": "Une ville suspendue dans une immense caverne creusée sous terre (12 à 30 blocs de profondeur) : lac "
                 "toxique et luminescent, pilier central à trois niveaux de plateformes, maisons sur pilotis "
                 "accrochées aux parois, passerelles, tuyaux et lampes Edison.",
}

# Bestiaire : description en français (le moteur ajoute vie, dégâts, lieux et butin depuis les données)
MOBS = {
    "ruin_walker": "Golem de pierre moussue des ruines de la Surface. Lent mais solide : il se réveille en se "
                   "secouant, puis frappe des deux mains, et ses coups affaiblissent.",
    "map_wraith": "Fantôme de parchemin rapide qui hante bibliothèques et avant-postes. Ses griffes de plume "
                  "aveuglent ; il brûle au soleil.",
    "basalt_guard": "Garde en armure des forteresses de basalte, avec une longue hache dorée. Un coup sur trois "
                    "balaie large, et ses coups flétrissent.",
    "void_stalker": "Chasseur filiforme des îles de l'End : si tu t'éloignes, il se téléporte juste à côté de toi.",
    "skeleton_knight": "Chevalier squelette au bouclier : il bloque 80 % des coups de face. Contourne-le, et "
                       "méfie-toi de sa charge au bouclier.",
    "crypt_crawler": "Araignée d'os qui grimpe aux murs et bondit sur sa proie. Sa morsure ralentit.",
    "banshee": "Femme spectrale qui flotte dans le Puits de lithite. Son cri, annoncé par un cône au sol, ralentit, "
               "affaiblit et repousse.",
    "gargoyle": "Statue tant que tu la regardes, elle attaque dès que tu tournes le dos. Garde-la dans ton champ "
                "de vision.",
    "ember_imp": "Petit diable du Nether qui garde ses distances et lance des boules de feu, fuit quand il est "
                 "blessé, puis revient.",
    "void_larva": "Larve de l'End qui s'enfouit et ressort sous tes pieds. En mourant, elle libère des endermites.",
    "drowned_warden": "Roi noyé au trident géant. Estocades, balayages, et un coup au sol qui lance un anneau de "
                      "marée à sauter. En phase 2, un tourbillon t'aspire.",
    "void_warden": "Le boss final : un chevalier du vide à la grande lame courbe. Combos, téléportation dans ton dos, "
                   "puits de gravité ; en phase 2, piqué aérien et pluie d'étoiles.",
    "bell_keeper": "Moine-chevalier de cinq blocs qui fait tournoyer une énorme cloche au bout d'une chaîne. Chaque "
                   "glas envoie un anneau sonore à sauter.",
    "archivist": "Érudit spectral d'encre et de parchemin qui flotte à distance : volées de pages, flaques d'encre "
                 "aveuglantes, et en phase 2 des doubles d'encre (trouve le vrai).",
    "sand_pharaoh": "Pharaon ensablé au fléau et à la crosse : piliers de sable, nuée de scarabées, il s'enfouit et "
                    "ressort sous toi. En phase 2, malédiction et sarcophage qui tombe du ciel.",
    "jade_jaguar": "Félin de jade rapide qui ne te laisse jamais souffler : bonds, griffes, et il se perche en "
                   "hauteur pour plonger sur ton ombre.",
    "root_mother": "Matriarche-arbre couronnée de branches : racines qui jaillissent sous chaque joueur, épines, et "
                   "elle s'abat comme un arbre qu'on abat (punis-la ensuite).",
    "swamp_crone": "Sorcière géante au chaudron sur le dos : potions lancées, maléfice qui te suit, saut de grenouille "
                   "et geysers bouillants en phase 2.",
    "gryphon_knight": "Griffon-chevalier qui combat au sol puis s'envole : piqués, volées de plumes, et l'orage en "
                      "phase 2.",
    "rune_colossus": "Colosse de pierre lent mais dévastateur : onde de choc runique, rochers lancés, rayon depuis la "
                     "tête, et son avant-bras qu'il projette au bout d'une chaîne de runes.",
    "forge_king": "Roi nain colossal au marteau chauffé à blanc et au bouclier-enclume : anneaux de métal en fusion, "
                  "enclumes qui tombent du plafond, aura de feu en phase 2.",
    "crystal_spider": "Araignée énorme à la carapace d'améthyste : toile qui ralentit, pics de cristal en ligne, "
                      "tempête d'éclats en phase 2.",
    "sculk_spawn": "Abomination aveugle née du sculk : elle chasse au bruit (accroupis-toi !). Fouet, souffle sonique "
                   "qui traverse l'armure, impulsions d'obscurité.",
    "ash_lord": "Chevalier de 4,7 blocs à l'espadon enflammé : combos dont les derniers coups peuvent ne pas venir, "
                "anneaux de colonnes de feu, pluie de météores en phase 2.",
    "piglin_king": "Roi piglin massif à la masse dorée : charge, onde de choc dorée, pluie de pièces sur des zones "
                   "marquées ; enragé en phase 2.",
    "soul_reaper": "Faucheuse flottante de 4,5 blocs à la faux géante et à la lanterne d'âmes : faux lancée qui "
                   "revient, téléportation, et elle t'attrape pour drainer ta vie.",
    "grave_knight": "Champion des Catacombes : seigneur squelette couronné à l'espadon de feu d'âme. Lignes "
                    "d'éruptions, anneaux à sauter, et il relève des chevaliers squelettes.",
    "bone_matriarch": "Championne de l'Hypogée : reine scorpion-araignée d'os. Pinces, dard empoisonné, elle s'enfouit "
                      "et ressort sous toi.",
    "weeping_lady": "Championne du Puits de lithite : banshee voilée qui pleure des larmes de cristal. Cri en cône, "
                    "éruptions de lithite, voile aveuglant.",
    "larva_mother": "Championne de la Crypte du vide : reine-larve au sac d'œufs lumineux. Morsure, acide, elle "
                    "s'enfouit, puis roule à travers l'arène.",
}

BIOMES = {
    "glacial_sea": "Mer gelée semée d'icebergs.",
    "slate_sea": "Mer froide aux fonds de gravier et d'argile.",
    "azure_ocean": "Grand océan bleu profond, forêts de varech.",
    "coral_lagoon": "Lagon tiède et turquoise, coraux et cornichons de mer.",
    "glowcap_isles": "Îles de mycélium couvertes de champignons géants qui brillent. Aucun monstre n'y apparaît.",
    "golden_beach": "Plage de sable doré bordée de palmiers.",
    "frost_shore": "Rivage enneigé et rochers givrés.",
    "basalt_cliffs": "Côte de colonnes de basalte noir et d'aiguilles marines.",
    "crystal_river": "Rivière claire aux roseaux et aux cristaux.",
    "ice_river": "Rivière gelée.",
    "aurora_tundra": "Plaine enneigée sous les aurores, quelques sapins isolés.",
    "shattered_glacier": "Glace bleue brisée en flèches et en blocs.",
    "frostpine_forest": "Forêt de pins givrés et de buissons à baies.",
    "snowcap_slopes": "Pentes de neige poudreuse sous les sommets.",
    "majestic_peaks": "Les plus hauts sommets du monde, jusque vers y 300, coiffés de glace.",
    "stone_spires": "Aiguilles de pierre nue veinées de calcite.",
    "verdant_meadows": "Prairies douces, fleurs et chênes solitaires : un bon endroit pour s'installer.",
    "wildflower_fields": "Champs de fleurs sauvages et arbres à abeilles.",
    "highland_meadow": "Alpage d'altitude, fleurs et rochers.",
    "enchanted_forest": "Forêt aux feuillages turquoise, arbres lumineux et lucioles.",
    "elderwood": "Vieille forêt de grands chênes.",
    "silver_birch_wood": "Bois de grands bouleaux argentés.",
    "crystal_woods": "Bouleaux et cristaux qui sortent du sol.",
    "shadow_woods": "Bois sombre et brumeux plein de champignons.",
    "pine_highlands": "Hautes terres de pins et de podzol.",
    "giant_sylvan": "Sylve de conifères géants, fougères et rochers moussus.",
    "sakura_valley": "Vallée de grands cerisiers en fleurs et de pétales roses.",
    "windswept_crags": "Escarpements venteux, gravier et épicéas tordus.",
    "glowing_marsh": "Marais boueux aux lichens luisants et aux lucioles.",
    "ashen_savanna": "Savane sèche d'acacias et d'herbes rases.",
    "rustlands": "Terres rouillées : terre cuite rouge, évents de vapeur et épaves steampunk à moitié enterrées.",
    "emerald_jungle": "Jungle dense aux arbres géants et aux melons.",
    "dune_sea": "Mer de dunes, cactus et os fossiles.",
    "painted_canyon": "Canyon de terre cuite aux couches colorées.",
    "cogwork_valley": "Vallée de sable rouge et de grès, épaves d'engrenages géants et évents de vapeur.",
    "crystal_caverns": "Cavernes de calcite et de cristaux, géodes d'améthyste.",
    "underground_jungle": "Grottes luxuriantes de mousse et de lianes.",
    "deep_abyss": "Abîme de sculk tout au fond du monde.",
    "thermal_caves": "Grottes chaudes de magma et de colonnes de basalte.",
    "fungal_grotto": "Grotte de mycélium et de champignons géants lumineux.",
    "mithril_hollows": "Creux d'ardoise des abîmes veinés de mithril, le meilleur endroit pour en miner.",
}

DECOR = {
    "acacias": "acacias", "amethyst_geodes": "géodes d'améthyste", "basalt_columns": "colonnes de basalte",
    "basalt_columns_cave": "colonnes de basalte", "beach_grass": "herbes de plage", "bee_trees": "arbres à abeilles",
    "berry_bushes": "buissons à baies", "blue_ice_chunks": "blocs de glace bleue", "boulders": "rochers",
    "calcite_veins": "veines de calcite", "canyon_cacti": "cactus", "cave_crystals": "cristaux",
    "cave_magma_pools": "mares de magma", "dead_bushes": "buissons morts", "dry_grass": "herbes sèches",
    "dune_cacti": "cactus", "ferns": "fougères", "forest_floor": "sous-bois", "fossil_bones": "os fossiles",
    "frost_pines": "pins givrés", "frost_pines_sparse": "pins givrés épars", "frost_rocks": "rochers givrés",
    "giant_glowcaps": "champignons géants lumineux", "giant_trees": "conifères géants", "glow_flowers": "fleurs lumineuses",
    "glow_lichen": "lichen luisant", "glowwood_trees": "arbres lumineux", "great_cherries": "grands cerisiers",
    "great_oaks": "grands chênes", "ice_spires": "flèches de glace", "ice_spires_small": "petites flèches de glace",
    "icebergs": "icebergs", "jungle_floor": "sous-bois de jungle", "jungle_giants": "arbres géants",
    "kelp": "varech", "kelp_cold": "varech", "lily_pads": "nénuphars", "lone_oaks": "chênes isolés",
    "lush_cave_vegetation": "végétation luxuriante", "marsh_trees": "arbres de marais", "meadow_flowers": "fleurs",
    "melons": "melons", "mithril_veins": "veines de mithril", "mossy_boulders": "rochers moussus",
    "mushrooms_dense": "champignons", "ocean_floor": "fonds marins", "ocean_floor_cold": "fonds marins froids",
    "palms": "palmiers", "pines": "pins", "pink_petals": "pétales roses", "reeds": "roseaux",
    "river_crystals": "cristaux de rivière", "river_reeds": "roseaux", "rusted_wrecks": "épaves rouillées",
    "sculk_growth": "sculk", "sea_pickles": "cornichons de mer", "sea_stacks": "aiguilles marines",
    "seagrass": "herbes marines", "seagrass_deep": "herbes marines", "seagrass_warm": "herbes marines",
    "shadow_oaks": "chênes sombres", "snowy_spruces_sparse": "épicéas enneigés", "steam_vents": "évents de vapeur",
    "surface_crystals": "cristaux", "tall_birches": "grands bouleaux", "tall_grass": "hautes herbes",
    "warm_ocean_vegetation": "coraux", "wildflowers": "fleurs sauvages", "windswept_spruces": "épicéas tordus",
}

BIOME_GROUPS = [
    ("ocean", "Océans et côtes"), ("cold", "Terres froides"), ("temperate", "Terres tempérées"),
    ("warm", "Terres chaudes et sèches"), ("cave", "Biomes de grottes"),
]

RECIPE_TYPES = {
    "minecraft:crafting_shaped": "Établi", "minecraft:crafting_shapeless": "Établi (sans forme)",
    "minecraft:crafting_transmute": "Établi (amélioration)", "minecraft:smelting": "Four",
    "minecraft:blasting": "Haut fourneau", "minecraft:smoking": "Fumoir", "minecraft:stonecutting": "Tailleur de pierre",
    "minecraft:smithing_transform": "Table de forgeron", "minecraft:campfire_cooking": "Feu de camp",
}
RECIPE_CATEGORIES = {"equipment": "Équipement", "building": "Construction", "misc": "Divers", "redstone": "Redstone",
                     "blocks": "Blocs", "food": "Nourriture"}

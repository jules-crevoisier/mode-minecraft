"""French editorial text for the illustrated wiki (tools/gen_wiki.py).

Everything else in the wiki comes from the data tables (content, guide, machines, metals, skills, structures,
recipes, loot...). This file only adds the plain-language explanations that the data does not
carry. Every table is optional: an id missing here still gets a card, with an automatic description.
"""

TAGLINE = ("Un mod d'exploration à plusieurs pour Minecraft 26.2 : des dizaines de structures géantes, des boss "
           "façon Elden Ring, des océans vivants, de la magie, des machines simples et tout le confort pour ranger "
           "moins et explorer plus.")

# "Par où commencer" : (titre, texte, [ids d'objets illustrés])
FIRST_HOUR = [
    ("Ouvre le Manuel", "Tu le reçois à la première connexion. Une page par système, avec sommaire. Astuce : survole "
     "n'importe quel objet du mod dans ton inventaire et maintiens la touche du manuel (Z sur un clavier AZERTY, réglable dans Commandes) pour ouvrir directement sa page.",
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
    "M": "Carte du monde (partagée sur un serveur : repères, signaux, pierres de voyage, joueurs)",
    "N": "Allumer / éteindre l'anneau aimanté",
    "H": "Afficher / masquer la mini-carte",
    "Maj + H": "Changer la taille de la mini-carte (petite, moyenne, grande, énorme)",
    "Z": "Changer le zoom de la mini-carte",
    "B": "Signaler l'endroit visé à tous les joueurs (visible une minute sur les cartes)",
    "W": "Maintenir sur un objet du mod : ouvrir sa page du Manuel",
    "G": "Baguette du bâtisseur : changer de symétrie (désactivée, miroir X, miroir Z, X + Z)",
    "Clic molette": "Sur une case d'un coffre : trier ce coffre",
}
# Touches dont la lettre change sur un clavier AZERTY (Minecraft garde la position de la touche, pas la lettre)
KEY_AZERTY = {"W": "Z", "Z": "W", "M": ","}
KEYS_NOTE = ("Les lettres ci-dessus sont celles d'un clavier QWERTY. Minecraft retient l'emplacement de la touche : en "
             "AZERTY, la touche du Manuel (W) est donc sur Z, le zoom de la mini-carte (Z) sur W et la carte (M) sur la "
             "virgule. Toutes se changent dans Options → Commandes → rubrique Wayfarers, ou depuis Mods → Wayfarers → "
             "Config → Touches.")

COMMANDS = {
    "atlas": ("tous", "Affiche le résumé de la guilde (utilisé par l'Atlas)."),
    "waystones": ("tous", "Liste les pierres de voyage découvertes."),
    "sort": ("tous", "Trie ton inventaire (comme la touche R)."),
    "magnet": ("tous", "Bascule l'anneau aimanté (comme la touche N)."),
    "warp": ("op", "Téléporte directement vers une pierre de voyage."),
    "kit": ("op", "Donne un kit d'équipement par palier : starter, explorer, depths, nether, end."),
    "demo": ("op", "Donne tout le contenu du mod d'un coup (idéal pour tester ou filmer)."),
    "locate": ("op", "Indique où se trouve la structure demandée."),
    "tp": ("op", "Téléporte vers la structure demandée (la génère si besoin)."),
    "boss": ("op", "Fait apparaître un boss devant toi, pour le tester."),
    "fitcheck": ("op", "Trouve chaque structure de la Surface, la génère et mesure comment elle se pose sur le relief (rapport et images PNG dans le dossier du serveur). Sert aux tests ; prend plusieurs minutes."),
    "progress": ("op", "reset : remet la quête à zéro ; complete : accorde toutes les quêtes."),
    "npc": ("op", "Donneurs de quêtes : spawn <rôle> en pose un à tes pieds (guild_agent, scholar, tinkerer, druid, "
                  "dwarf_elder), move amène le plus proche (8 blocs) à ta place et en fait son nouveau poste, role "
                  "<rôle> change son métier, remove le retire."),
    "contracts": ("op", "reset [joueur] : efface les contrats acceptés et terminés d'un joueur."),
}

CONFIG_FR = {
    "world.structureFit": "Les structures du mod ne démarrent que là où le terrain leur convient : sol assez plat et "
                          "sec pour les bâtiments, un rivage pour le phare, un fond marin dégagé pour les épaves. Sur "
                          "false, elles apparaissent partout où la grille le dit.",
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
    "hud.healthBarRange": "Distance (en blocs) jusqu'à laquelle on dessine barres de vie et chiffres de dégâts. "
                          "Baisse-la dans les fermes à monstres ou les grosses batailles pour gagner des images par seconde.",
    "storage.terminalRange": "Portée du terminal de guilde autour de lui, à l'horizontale : chaque coffre, tonneau, "
                             "boîte de shulker, coffre de tri et caisse compacte de ce carré rejoint son réseau.",
    "storage.terminalHeight": "Portée du terminal et des relais vers le haut et vers le bas (384 = toute la hauteur du "
                              "monde).",
    "storage.relayRange": "Portée d'un relais de stockage autour de lui. Un relais rejoint le réseau s'il est à portée "
                          "du terminal ou d'un autre relais relié.",
    "storage.maxContainers": "Nombre maximal de conteneurs dans un réseau de terminal (protège le serveur sur les "
                             "bases géantes).",
    "map.sharedExploration": "Carte du monde partagée : chacun voit ce que tous ont exploré. Sur false, chaque joueur "
                             "ne voit que ce qu'il a vu lui-même (le serveur garde les deux, on peut changer à tout moment).",
    "map.showPlayers": "Montre les autres joueurs sur la mini-carte et la carte du monde (même dimension).",
    "map.minimap": "Affiche la mini-carte (touche H en jeu ; Maj + H change sa taille).",
    "map.corner": "Coin de l'écran de la mini-carte : TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT ou BOTTOM_RIGHT.",
    "map.size": "Taille de la mini-carte à l'écran, cadre compris : SMALL (56 px), MEDIUM (68 px), LARGE (96 px) ou "
                "XLARGE (128 px). En jeu : Maj + H, ou Mods → Wayfarers → Config, onglet Mini-carte.",
    "map.opacity": "Opacité du terrain de la mini-carte, en pourcentage (30 à 100) : baisse-la pour voir le monde à "
                   "travers.",
    "map.shape": "Forme : ROUND (hublot de laiton) ou SQUARE (cadre carré).",
    "map.rotate": "La mini-carte tourne avec toi (ta direction toujours en haut). Sur false : le nord est en haut.",
    "map.zoom": "Zoom de la mini-carte, de 0 (le plus large) à 3 (le plus proche). Touche Z en jeu.",
    "map.showCoordinates": "Affiche tes coordonnées et le biome sous la mini-carte.",
    "map.caveMode": "Sous terre, la carte dessine la grotte autour de toi (une tranche à ta hauteur) au lieu de la "
                    "surface.",
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

# Merveilles (méga-structures) : affichées en grand, avec rotation 360° et vue en coupe. Le générateur y ajoute
# toute structure citée dans les pages « wonders* » du Manuel (tools/wf/guide.py) ; l'ordre ci-dessous passe en premier.
WONDERS = ["clockwork_citadel", "sky_harbour", "undercity", "sunken_citadel"]

STRUCTURES = {
    "guild_outpost": "Fort de la Guilde avec rempart, châtelet, grande salle et tour des cartes de 46 blocs. "
                     "Première structure à trouver : fragments de carte et pierre de voyage. Trois variantes. Une "
                     "garnison de villageois y vit, et l'agent de la Guilde propose des contrats dans la grande salle.",
    "mountain_monastery": "Église gothique à arcs-boutants avec clocher de 46 blocs, cloître et bibliothèque. Sous la "
                          "crypte secrète, la chambre de la cloche du Sonneur de glas.",
    "forgotten_library": "Nef gothique, tours jumelles et rotonde effondrée. Les derniers bibliothécaires vivent dans "
                         "la grande salle avec une érudite qui propose des contrats ; les spectres hantent l'aile en "
                         "ruine. Derrière un cabinet secret, les archives interdites de l'Archiviste.",
    "coastal_lighthouse": "Phare de 52 blocs sur un cap, avec quai et grotte marine. Le gardien du phare et un "
                          "pêcheur vivent dans la maison au pied de la tour.",
    "giant_tree": "Tronc creux de 15 blocs de large, trois terrasses de cabanes reliées par des ponts de corde. Un "
                  "peuple de la forêt en robe verte y vit (archer, fermier, bibliothécaire, cartographe, guérisseuse, "
                  "tisserand) et une druidesse propose des contrats à l'étage des couchettes. La Mère-Racine attend "
                  "dans la caverne des racines.",
    "desert_oasis": "Caravansérail à coupoles et minarets, bazar et colosse de pharaon à moitié enseveli. Le tombeau "
                    "caché mène à la salle funéraire du Pharaon ensablé.",
    "witch_huts": "Maisons tordues sur pilotis, tour au chapeau pointu et cercle rituel. Sous le marais, la grotte "
                  "inondée de la Grand-Mère du marais.",
    "sky_island": "Temple de quartz flottant à 40 blocs du sol, îlots reliés par des ponts et cascades. Le "
                  "Chevalier-griffon combat sur l'esplanade.",
    "jungle_ziggurat": "Pyramide à 8 gradins, têtes de serpent à plumes, jeu de balle. Les gardiens du temple (un "
                       "prêtre et un tailleur de pierre) vivent dans une loge de la clairière ; le temple, lui, reste "
                       "hanté. Sous la pyramide, le cénote sacré du Jaguar de jade.",
    "ruined_watchtower": "Tour de guet : une version en ruine au sommet effondré, une version intacte avec flèche. "
                         "Cave secrète.",
    "bandit_camp": "Palissade, tours de guet et tente du chef, gardés par des pillards.",
    "rune_circle": "Trilithes de 13 blocs autour d'un autel. Deux gardiens des runes vivent dans une loge sur la "
                   "prairie. La crypte mène à la voûte des runes du Colosse runique.",
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
                         "fumantes reliées par des tuyaux. Ses horlogers y travaillent encore, gardés par des golems de laiton, "
                         "et un bricoleur propose des contrats dans le premier atelier. Dans "
                         "le hall d'entrée de la tour (côté est), un escalier s'enfonce vers la Salle des engrenages, "
                         "un lieu de grâce, puis le Caveau de l'horloge où attend le Grand Horloger.",
    "geothermal_foundry": "Des forges steampunk bâties dans le flanc d'un petit volcan fumant (cratère de lave, coulées "
                          "de magma, évents de vapeur). Devant, une caldeira de lave enjambée par un pont roulant qui "
                          "porte une louche géante, deux halles de coulée aux toits en dents de scie, quatre cheminées "
                          "de 55 blocs et une gare de wagonnets. Dans la montagne : la Forge des Profondeurs, une nef "
                          "voûtée à colonnes de fer avec deux marteaux-pilons au-dessus d'un canal de lave, et au fond "
                          "le Cœur, une salle en coupole autour d'un puits de lave.",
    "tesla_observatory": "Un campus scientifique perché sur un piton de montagne. À l'ouest, le Grand Observatoire : "
                         "un tambour de pierre crème sous une coupole de cuivre vert-de-gris, fendue pour un télescope "
                         "de laiton de 30 blocs. Au nord-est, la Tour Tesla : 70 blocs de treillis autour d'une bobine "
                         "de cuivre, coiffés d'un anneau hérissé de paratonnerres. Au sud-est, la Rotonde du "
                         "planétarium, ses planètes sur des bras de laiton autour d'un soleil lumineux. Entre les deux, "
                         "bibliothèque, laboratoire et une cour avec cadran solaire.",
    "crystal_cathedral": "Une cathédrale gothique de calcite, de quartz et d'améthyste au fond d'une géode géante "
                         "(88 × 46 × 112 blocs), très loin sous terre : le sol est entre y −44 et y −34. Nef voûtée de "
                         "50 blocs, arcs-boutants à pinacles d'améthyste, deux tours à flèche, une rosace de vitraux et "
                         "une flèche qui se change en pilier de cristal jusqu'à la voûte. Dans le chœur, l'autel du "
                         "Cœur-Cristal ; du transept nord, un escalier descend à la crypte, où le reliquaire attend "
                         "derrière des barreaux.",
    "dwarven_city": "Un royaume nain perdu, taillé de 40 à 50 blocs sous terre. La ville basse remplit une caverne de "
                    "69 × 37 blocs : au centre le Foyer, un brasier de 14 blocs nourri par deux rivières de lave qui "
                    "tombent des parois ; à l'ouest les forges et la fonderie, à l'est la taverne et la salle des "
                    "tailleurs de gemmes ; trois étages de maisons creusées dans les murs et une voie de wagonnets. Au "
                    "nord, une porte de 13 blocs gardée par deux rois nains de pierre de 22 blocs mène à la Grande Salle "
                    "puis à la salle du trône. Le trésor ? Une trappe cachée sous le tapis, derrière le trône. Des "
                    "nains y vivent encore ; l'ancien nain propose des contrats près du foyer de la taverne.",
    "sylvan_palace": "Un palais elfique qui pousse dans et autour d'un arbre d'argent colossal : tronc de 11 blocs, 70 "
                     "blocs de haut, huit racines en arche et une canopée de 46 blocs piquée de fruits lumineux. Un "
                     "escalier en spirale fait le tour du tronc jusqu'à trois terrasses à pavillons (invités, musique "
                     "et banquet, chambre de la reine, bibliothèque dans les feuilles). Dans le tronc : la source du "
                     "Cœur, la salle du trône, le trésor royal et une échelle jusqu'à la Lanterne de lune, un "
                     "observatoire de verre au-dessus de la cime. Trois cabanes reliées par des ponts de corde et le "
                     "Bassin de lune au pied de l'arbre.",
    "inventor_manor": "Une demeure victorienne steampunk dans les prairies : briques rouges, fer sombre, toit mansardé "
                      "en cuivre vert-de-gris, tourelles, tour d'observation à télescope et trois cheminées qui "
                      "fument. Dedans : bureau, salle à manger, bibliothèque, chambre, salon et grenier. À l'est, une "
                      "serre de verre où un arroseur et une moissonneuse tournent tout seuls ; à l'ouest, l'atelier "
                      "de l'inventeur. Le secret : un tapis du bureau cache une trappe vers le laboratoire souterrain "
                      "(réacteur d'éther, bobine Tesla, cuves à spécimens) et le meilleur butin.",
    "sky_isles": "Un archipel qui flotte vers 200 blocs d'altitude au-dessus des océans et des plaines. L'île de la "
                 "Couronne porte une prairie, un étang qui tombe en cascade et le Sanctuaire céleste, un temple rond "
                 "en ruine au dôme effondré, avec l'autel du trésor. Autour : l'île du Cerisier (la plus haute, et "
                 "sa tour de guet hantée par une gargouille), l'île du Bassin, l'île de Cristal (améthyste et minerai "
                 "d'éther) et l'île de la Cloche, reliées par des ponts de corde. Pour monter : des blocs, ou le "
                 "grappin et le planeur.",
    "sky_harbour": "Une tour d'amarrage en fer de 44 blocs, avec un dirigeable à vapeur accosté à son sommet : coque "
                   "en acajou, hublots, cabine, hélice et enveloppe rayée. Visible de très loin au-dessus des plaines.",
    "undercity": "Une ville suspendue dans une immense caverne creusée sous terre (12 à 30 blocs de profondeur) : lac "
                 "toxique et luminescent, pilier central à trois niveaux de plateformes, maisons sur pilotis "
                 "accrochées aux parois, passerelles, tuyaux et lampes Edison. Une famille vit dans chaque "
                 "maison ; aucun monstre n'apparaît dans la caverne.",
    "sunken_submarine": "Un sous-marin steampunk couché sur le sable, la coque de fer sombre cerclée de laiton, une "
                        "brèche dans le flanc. Salle de commandes (table des cartes et coffre du capitaine) et salle "
                        "des machines inondées, kiosque à hublot et périscope.",
    "diving_bell": "Une cloche de plongée en cuivre et laiton posée sur quatre pieds : on y entre par le dessous, et "
                   "l'intérieur est plein d'air. Un refuge pour respirer, avec les tonneaux du plongeur.",
    "coral_shrine": "Un petit sanctuaire de prismarine dans les mers chaudes : six colonnes, un dôme à moitié écroulé, "
                    "un autel couronné de corail et son coffre d'offrandes, le tout envahi de coraux et d'anémones.",
    "shipwreck_debris": "Ce qui reste d'un navire, éparpillé sur le sable : membrures de la coque, mât tombé et voile "
                        "déchirée, canon, ancre et chaîne, cargaison répandue et coffre du capitaine à demi enfoui.",
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
    "clockwork_spider": "Petit automate de laiton à clé de remontage, qui chasse en bande et grimpe aux murs. Faible "
                        "seule mais rapide : morsure de près, et quand elle s'arrête en faisant ronronner sa clé, elle "
                        "va bondir (3 à 8 blocs, coup plus fort). Elle lâche du laiton et des engrenages.",
    "steam_drone": "Chaudière volante à deux rotors, armée d'un pistolet à rivets. Elle tourne à 3 à 5 blocs "
                   "au-dessus de toi et tire des rivets brûlants ; quand elle se cabre, elle va plonger sur toi : "
                   "écarte-toi. Un arc ou le pistolet à rivets l'abat vite. Sort la nuit.",
    "brass_golem": "Ton compagnon : un golem de laiton que tu construis toi-même (deux blocs de laiton + un cœur "
                   "mécanique). Il te suit, cogne les monstres d'un coup de piston qui les projette, et frappe le sol "
                   "quand il est encerclé. Jamais les creepers, jamais les joueurs, villageois ni animaux.",
    "grand_clockmaker": "Champion de la Citadelle d'horlogerie : un gentleman-automate de 4,4 blocs, le torse en "
                        "cadran d'horloge, le monocle qui luit, des ailes d'engrenages et une canne-pendule. Il arrête "
                        "le temps, appelle des araignées-horloges et, blessé, sonne minuit.",
    "glow_jellyfish": "Une cloche translucide qui pulse et dérive dans toutes les mers, en rose, azur, ambre ou "
                      "violet ; elle brille la nuit. La toucher pique un peu (poison). Sa gelée donne une lampe ou la "
                      "vision nocturne.",
    "reef_fish": "Petits poissons des mers chaudes qui nagent en bancs de dix : soleil, clown ou azur. Ils "
                 "s'attrapent au seau.",
    "manta_ray": "Une raie géante et paisible de 3,5 blocs d'envergure ; ses ailes battent en vague, et près de la "
                 "surface elle saute hors de l'eau.",
    "sea_serpent": "Mini-boss des eaux profondes : la nuit, il monte sous les bateaux et les nageurs. Morsure, charge "
                   "qui brise les bateaux, tourbillon qui renverse les passagers. Ses écailles font le casque de "
                   "scaphandre.",
    "whale": "Une baleine à bosse de dix blocs, rare, dans les océans profonds : elle remonte souffler à la surface "
             "et chante de très loin. Paisible.",
}

# Créatures amies (bestiaire : groupe « Compagnons »)
COMPANIONS = ["brass_golem"]

# Attaques détaillées des boss : (nom, phase, ce qu'il faut faire). Affichées dans le bestiaire et les Automates.
BOSS_MOVES = {
    "grand_clockmaker": [
        ("Balancier", "1 et 2", "Un grand coup de canne-pendule sur 220° devant lui (15 dégâts, portée 6,5 blocs). "
                                "Recule ou passe dans son dos. En phase 2, il enchaîne souvent sur le coup de canne."),
        ("Coup de canne", "1 et 2", "Il frappe le sol 3,5 blocs devant lui (18) et un anneau d'étincelles roule vers "
                                    "l'extérieur (8) : saute par-dessus. En phase 2, deux anneaux, puis parfois les "
                                    "engrenages."),
        ("Éventail d'engrenages", "1 et 2", "À distance (4 à 24 blocs), il lance 3 engrenages de laiton en éventail "
                                            "(7 chacun), 5 en phase 2. Déplace-toi de côté."),
        ("Remontage", "1 et 2", "Il remonte 2 araignées-horloges (3 en phase 2), jamais plus de 4 en même temps. "
                                "Elles s'arrêtent net à sa mort."),
        ("Arrêt du temps", "1 et 2", "Ses aiguilles reculent pendant 1,2 s et un cercle de 9 blocs se referme autour "
                                     "de lui. Qui est encore dedans au carillon est figé 2 s (Lenteur IV, Fatigue). "
                                     "Sors du cercle !"),
        ("Saut dans le temps", "2", "Il disparaît et réapparaît 2,5 blocs dans ton dos, puis balaie. Retourne-toi "
                                    "et recule."),
        ("Minuit", "2", "Douze cloches sonnent l'une après l'autre sur un cercle de 6 blocs autour de lui (11 "
                        "chacune, un reflet prévient), puis une treizième sous chaque joueur (12) : ne reste pas "
                        "immobile."),
    ],
}
BOSS_FACTS = {
    "grand_clockmaker": "400 PV, armure 12, barre jaune. Phase 2 à mi-vie : il rugit, des étincelles crépitent sur "
                        "lui, il accélère et enchaîne ses coups.",
}

# Descente vers un repaire : étapes dans l'ordre
LAIRS = {
    "grand_clockmaker": [
        ("Citadelle d'horlogerie", "Entre dans la grande tour-horloge. Dans le hall d'entrée, côté est, un escalier "
                                   "s'ouvre dans le sol."),
        ("La Salle des engrenages", "Premier niveau (y −10 sous la place) : les machines qui font tourner l'horloge, "
                                    "des engrenages muraux, un générateur d'araignées-horloges et deux coffres "
                                    "d'atelier."),
        ("Le lieu de grâce", "Un second escalier descend (y −21) vers une petite salle de laiton : pierre de voyage "
                             "sur une estrade, bancs et lampes. Active la pierre : tu reviendras ici après une mort."),
        ("Le Caveau de l'horloge", "Derrière la brume : une arène ronde de 13 blocs de rayon dont le sol est un "
                                   "cadran géant arrêté à minuit, douze pilastres de laiton et un grand pendule "
                                   "qui se balance sous le dôme."),
        ("Le cabinet de l'Horloger", "À l'ouest de l'arène, derrière une seconde brume qui tombe à sa mort : les "
                                     "coffres de récompense."),
    ],
}

# ------------------------------------------------------------------ sections ajoutées
# Gadgets à vapeur : une astuce par gadget (le reste vient de tools/wf/gadgets.py : nom, infobulle, recette, Manuel)
GADGETS_INTRO = ("Six objets de laiton à fabriquer à l'établi, sans talent ni mana. Ils servent tous les jours : "
                 "orienter un bloc, grimper, planer, tirer, lire l'heure, trouver le Port céleste. La clé, le grappin, "
                 "le planeur et le pistolet s'usent ; ils se réparent avec un lingot de laiton sur une enclume.")
GADGET_TIPS = {
    "brass_wrench": "Pour orienter un escalier ou un meuble après coup, ou récupérer un bloc déco mal placé sans le "
                    "casser.",
    "grappling_hook": "Vise un rebord en hauteur : tours de la Citadelle, falaises, Îles célestes. La griffe ne "
                      "touche pas les créatures.",
    "brass_glider": "Le combo du mod : grappin pour monter, planeur pour redescendre de l'autre côté.",
    "rivet_gun": "Une arme à distance sans arc, rapide et presque droite : parfaite contre les drones à vapeur.",
    "rivet": "Garde-en une pile sur toi ; sans rivets, le pistolet prend tes pépites de fer.",
    "pocket_watch": "Pour voir venir la nuit et la lune de sang, et savoir dans quel biome tu te trouves.",
    "airship_compass": "Le plus simple pour trouver le Port céleste. Dans l'End, elle mène à l'Épave du vide.",
}

CONSTRUCTION_INTRO = ("Trois outils pour bâtir vite et joli : le burin taille un bloc en ses variantes, la table de "
                      "taille transforme une pile entière d'un coup, et la baguette du bâtisseur pose des rangées de "
                      "blocs, en miroir si tu veux.")
CHISEL_ONLY_TEXT = ("Ces blocs n'ont pas de recette : on les obtient seulement au burin ou à la table de taille, à "
                    "partir d'un bloc de la même famille (placage de laiton, briques de lithite, lambris d'acajou…).")
SYMMETRY_MODES = [
    ("off", "Désactivée", "La baguette pose seulement tes blocs."),
    ("x", "Miroir X", "Copie de l'autre côté du plan est/ouest."),
    ("z", "Miroir Z", "Copie de l'autre côté du plan nord/sud."),
    ("xz", "Miroir X + Z", "Quatre copies, une par quart : idéal pour une tour ou une fontaine."),
]

AUTOMATONS_INTRO = ("Les automates de laiton : deux ennemis des terres steampunk, un compagnon à construire soi-même "
                    "et leur créateur, le Grand Horloger, caché sous la Citadelle d'horlogerie.")
GOLEM_STEPS = [
    ("Fabrique un cœur mécanique", "À l'établi : un engrenage en laiton, deux lingots de laiton, un bloc de redstone "
                                   "et une horloge. Les engrenages se fabriquent avec du laiton, ou se ramassent sur les "
                                   "araignées-horloges."),
    ("Empile deux blocs de laiton", "Pose un bloc de laiton (9 lingots) et un second dessus, comme une petite "
                                    "colonne."),
    ("Utilise le cœur dessus", "Clic droit avec le cœur sur un des deux blocs : les blocs et le cœur disparaissent, "
                               "le golem se réveille en sifflant et te suit."),
]
GOLEM_ORDERS = [
    ("Suivre / garder", "Accroupi + clic droit main vide sur le golem : il garde l'endroit où il est, ou recommence "
                        "à te suivre. S'il est à plus de 28 blocs, il te rejoint tout seul."),
    ("Combat", "Il attaque les monstres à 16 blocs (jamais les creepers) et défend son maître et les villageois. Coup "
               "de piston : 12 dégâts, l'ennemi s'envole. Encerclé par trois monstres : il frappe le sol (9 autour)."),
    ("Réparer", "Donne-lui du laiton : un lingot rend 20 PV, une pépite 3. 80 PV et 10 d'armure."),
    ("S'il est détruit", "Il lâche son cœur mécanique et un peu de laiton : il suffit de le reconstruire."),
]

# Nouveautés de la nuit (section en haut de page). Le générateur ajoute aussi la liste complète des objets, blocs,
# créatures et structures apparus depuis le commit NEW_SINCE (lu avec git, si disponible).
NEW_SINCE = "420854b"
NEW_TITLE = "Nouveautés de cette nuit"
NEW_INTRO = ("Tout ce qui est arrivé dans le mod cette nuit, rangé par thème. Chaque carte mène à sa section "
             "détaillée ; la check-list « Tester en jeu » juste en dessous donne les commandes pour tout essayer en "
             "quelques minutes.")
# Thèmes : (titre, phrase, [(titre, texte, ancre, vignette)]). Vignette : "mob:<id>", "struct:<id>",
# "items:<id>,<id>,..." ou "img:<chemin>" (une capture d'écran publiée avec le wiki).
# Le thème dont le titre commence par « Merveilles » s'affiche en grandes cartes.
NEW_GROUPS = [
    ("Carte, écrans et rangement", "Se repérer à plusieurs, régler chaque machine sans deviner, et toute la base "
     "dans un seul écran.", [
        ("Carte du monde partagée", "Touche M : tout ce qu'un joueur explore apparaît chez tous. Repères privés ou "
         "partagés, signaux, pierres de voyage, joueurs, vue des grottes.", "carte", "img:img/gui/worldmap.webp"),
        ("Mini-carte", "Un hublot de laiton dans un coin de l'écran : terrain, direction, repères, coordonnées et "
         "biome. H la masque, Z zoome, B envoie un signal.", "mini-carte", "img:img/gui/minimap.webp"),
        ("Un vrai écran pour chaque machine", "Les neuf machines s'ouvrent au clic : zone, sortie, filtre, mode "
         "redstone, réglés avec des boutons et des infobulles.", "ecrans-machines",
         "img:img/gui/machine_harvester.webp"),
        ("Réglages et touches", "Mods → Wayfarers → Config : barres de vie, chiffres de dégâts, suivi, astuces. La "
         "touche du Manuel se change (W, donc Z en AZERTY).", "touches", "img:img/gui/settings.webp"),
        ("Terminal de guilde pour toute la base", "Il relie tous les coffres à 48 blocs. Des relais de stockage "
         "étendent la portée, une page réseau exclut un coffre, « Montrer » les encadre dans le monde.", "terminal",
         "items:guild_terminal,storage_relay,sorting_chest,compacting_crate"),
    ]),
    ("Océans vivants", "Les mers se remplissent : créatures, fonds marins, épaves et équipement de plongée.", [
        ("Méduses, poissons, raies et baleines", "Quatre créatures paisibles : méduses lumineuses, bancs de "
         "poissons de récif, raies manta qui sautent, baleines à bosse au large.", "oceans", "mob:manta_ray"),
        ("Le serpent de mer", "Un mini-boss qui monte la nuit sous les bateaux, au-dessus des eaux profondes. Ses "
         "écailles font le casque de scaphandre.", "b-sea_serpent", "mob:sea_serpent"),
        ("Fonds marins", "Forêts de varech, récifs de corail géants, huîtres perlières, anémones lumineuses et "
         "cheminées à bulles pour remonter respirer.", "fonds-marins",
         "items:pearl_oyster,pearl,glow_anemone,jelly_lamp,glow_jelly"),
        ("Épaves et refuges sous l'eau", "Sous-marin englouti, cloche de plongée pleine d'air, sanctuaire de corail "
         "et débris de naufrage, chacun avec son butin.", "epaves", "struct:sunken_submarine"),
        ("Casque de scaphandre et palmes", "Respirer, voir clair et miner à pleine vitesse sous l'eau ; nager bien "
         "plus vite.", "plongee", "items:diving_helmet,flippers,serpent_scale"),
    ]),
    ("Nouveaux matériaux", "De quoi construire, à récolter ou à faire pousser.", [
        ("Bois-lueur et bois rouillé", "Deux essences complètes (bûches, planches, portes, trappes…) à faire "
         "pousser à partir d'une pousse fabriquée ou trouvée dans un coffre.", "bois",
         "items:glowwood_log,glowwood_planks,glowwood_leaves,rustwood_log,rustwood_planks,rustwood_leaves"),
        ("Marbre, roche rouillée, ardoise bleue", "Trois pierres de construction en grosses veines dans le monde, "
         "avec leurs versions polie, en briques, en pilier ou en carreaux.", "pierres",
         "items:marble,marble_pillar,chiseled_marble,rust_rock_bricks,blue_slate,blue_slate_tiles"),
        ("Nouveaux dessins et modèles 3D", "Beaucoup d'objets redessinés et 14 nouveaux modèles 3D tenus en main : "
         "outils de laiton et de mithril, pioche excavatrice, hache de bûcheron…", "armes3d",
         "items:excavator_pickaxe,lumber_axe,brass_pickaxe,mithril_axe,bell_hammer,magnet_ring"),
        ("Serveur et performances", "Moins de calculs à chaque tick, boussoles plus rapides, HUD plus léger ; et "
         "les options utiles pour un serveur.", "performances", "items:minecraft:comparator,minecraft:clock"),
    ]),
    ("Villages enrichis", "Les cinq villages du jeu (plaines, désert, savane, neige, taïga) grandissent : de "
     "nouveaux bâtiments dans leur propre style, avec une touche de laiton et de vapeur.", [
        ("Place à pierre de voyage", "Un village sur quatre se forme autour d'une place : pierre de voyage sur un "
         "socle de laiton, tableau d'annonces, cloche, lampes, bancs et massifs fleuris.", "m-villages",
         "items:waystone,edison_lamp,minecraft:bell"),
        ("Auberge des Voyageurs", "Taverne avec comptoir, cheminée, lustres de laiton, aubergiste et voyageur de "
         "passage ; chambres à l'étage, balcon et enseignes suspendues.", "m-villages",
         "items:mahogany_table,mahogany_chair,brass_chandelier"),
        ("Atelier, tour de guet, marché, verger", "L'atelier du bricoleur et sa chaudière, la tour de guet et sa "
         "cloche d'alarme, des étals rayés avec leurs marchands, un verger clos ; plus des cottages, des manoirs et "
         "des coins de puits.", "m-villages", "items:gear_panel,pressure_gauge,copper_pipes,smokestack_bricks"),
        ("Rues et avant-postes", "Lampes de laiton, panneaux et jardinières le long des rues. Les avant-postes "
         "pillards ont des balistes à vapeur et des barricades hérissées.", "m-villages",
         "items:brass_railing,dark_iron_plating,minecraft:crossbow"),
    ]),
    ("Habitants et contrats", "Les structures se peuplent : des villageois chez eux, avec un lit et un métier, et "
     "des donneurs de quêtes qui proposent des contrats.", [
        ("Donneurs de quêtes", "Agent de la Guilde, érudite, bricoleur, druidesse et ancien nain : clic droit pour "
         "leurs contrats (apporter, chasser, explorer, livrer un colis), suivis dans le journal et à l'écran.",
         "m-contracts", "items:minecraft:emerald,minecraft:paper,map_fragment,brass_gear"),
        ("L'Arbre-monde habité", "Un peuple de la forêt en robe verte vit sur les étages du tronc creux et sur la "
         "cime, avec la druidesse.", "s-giant_tree", "struct:giant_tree"),
        ("Gardiens et ermites", "Une loge pour les gardiens de la ziggourat et pour ceux du cercle runique, le "
         "gardien du phare, la cour du Palais sylvain.", "s-jungle_ziggurat", "struct:jungle_ziggurat"),
        ("Relais de la Guilde", "Un nouveau bâtiment dans les villages : l'agent de la Guilde derrière son comptoir. "
         "Une érudite à l'auberge, un bricoleur à l'atelier.", "m-villages", "items:minecraft:bell,minecraft:lectern"),
        ("Des lieux sûrs", "Aucun monstre n'apparaît plus là où des gens vivent ; les antres et les donjons restent "
         "dangereux.", "m-contracts", "items:minecraft:red_bed,minecraft:oak_door"),
    ]),
    ("Laiton et vapeur", "Des outils de tous les jours et de quoi bâtir vite.", [
        ("Gadgets à vapeur", "Clé à molette, grappin, planeur, pistolet à rivets, montre à gousset et boussole de "
         "dirigeable : six objets de laiton pour grimper, planer, tirer et s'orienter.", "gadgets",
         "items:brass_wrench,grappling_hook,brass_glider,rivet_gun,pocket_watch,airship_compass"),
        ("Burin et table de taille", "Le burin taille un bloc en sa variante suivante (pierre, briques, moussues, "
         "sculptées…) ; la table transforme une pile entière, gratuitement. Avec 11 blocs qu'on n'obtient qu'au "
         "burin.", "construction",
         "items:chisel,chisel_table,engraved_brass,brass_grille,chiseled_lithite_bricks,mahogany_parquet"),
        ("Symétrie de la baguette", "Accroupi + clic sur un bloc pour poser le centre du miroir, touche G pour "
         "choisir miroir X, Z ou les deux : tes constructions se copient en miroir.", "symetrie",
         "items:builder_wand,master_builder_wand"),
    ]),
    ("Automates", "La mécanique vivante : un compagnon, deux ennemis et un boss.", [
        ("Le golem de laiton", "Un compagnon à construire : deux blocs de laiton et un cœur mécanique. Il te suit et "
         "cogne les monstres.", "golem", "mob:brass_golem"),
        ("Araignées-horloges et drones", "Deux automates ennemis la nuit dans les badlands et les hautes "
         "savanes, et dans la Citadelle et les Bas-fonds.", "automates", "mob:clockwork_spider"),
        ("Le Grand Horloger", "Un nouveau boss sous la Citadelle d'horlogerie, avec arrêt du temps et sonnerie de "
         "minuit. Son Souvenir forge le Pendule du Grand Horloger.", "horloger", "mob:grand_clockmaker"),
    ]),
    ("Merveilles à explorer", "Sept méga-structures, de 200 blocs d'altitude au fond du monde.", [
        ("Cité naine des profondeurs", "Un royaume nain taillé à 40-50 blocs sous terre, rivières de lave et salle "
         "du trône.", "s-dwarven_city", "struct:dwarven_city"),
        ("Cathédrale de cristal", "Une cathédrale gothique dans une géode géante, tout au fond du monde.",
         "s-crystal_cathedral", "struct:crystal_cathedral"),
        ("Palais sylvain", "Un palais elfique autour d'un arbre d'argent de 70 blocs.", "s-sylvan_palace",
         "struct:sylvan_palace"),
        ("Manoir de l'inventeur", "Une demeure victorienne steampunk, sa serre et son laboratoire secret.",
         "s-inventor_manor", "struct:inventor_manor"),
        ("Îles célestes", "Un archipel flottant à 200 blocs d'altitude, relié par des ponts de corde.",
         "s-sky_isles", "struct:sky_isles"),
        ("Fonderie géothermique", "Des forges bâties dans un volcan fumant, avec pont roulant et caldeira de lave.",
         "s-geothermal_foundry", "struct:geothermal_foundry"),
        ("Observatoire Tesla", "Coupole, télescope géant, bobine Tesla de 70 blocs et planétarium sur un piton.",
         "s-tesla_observatory", "struct:tesla_observatory"),
    ]),
]

# « Tester en jeu » : (titre, [commandes], ce qu'on doit voir). Les commandes /wayfarers sont vérifiées par le
# générateur contre WayfarersCommand.java ; les ids d'objets, d'entités et de structures contre les données du mod.
TEST_INTRO = ("Une partie en créatif (ou avec les droits d'opérateur), un monde neuf, et ces commandes dans le chat. "
              "Coche au fur et à mesure : la liste se souvient de tes coches sur cet appareil.")
TEST_CHECKLIST = [
    ("Tout recevoir d'un coup", ["/gamemode creative", "/wayfarers demo"],
     "Tous les objets du mod arrivent dans l'inventaire (le surplus tombe au sol)."),
    ("Clé à molette", ["/give @s wayfarers:brass_wrench", "/give @s minecraft:oak_stairs 8"],
     "Pose un escalier, clic droit avec la clé : il tourne. Accroupi : dans l'autre sens. Accroupi sur un bloc déco "
     "Wayfarers (placage de laiton…) : il revient dans l'inventaire."),
    ("Grappin et planeur", ["/give @s wayfarers:grappling_hook", "/give @s wayfarers:brass_glider"],
     "Vise un mur à moins de 32 blocs : la chaîne te tire jusqu'au rebord. En survie (/gamemode survival), saute "
     "d'en haut avec le planeur en main : tu descends doucement, sans dégâts."),
    ("Pistolet à rivets", ["/give @s wayfarers:rivet_gun", "/give @s wayfarers:rivet 64",
                           "/summon minecraft:zombie ~ ~ ~5"],
     "Clic droit : un rivet fumant part tout droit (5 dégâts). Sans rivets ni pépites de fer : « Plus de rivets »."),
    ("Montre et boussole", ["/give @s wayfarers:pocket_watch", "/give @s wayfarers:airship_compass"],
     "La montre affiche l'heure, le jour, la lune et le biome. La boussole cherche le Port céleste le plus proche et "
     "son aiguille pointe vers lui (sinon elle le dit et tourne)."),
    ("Burin", ["/give @s wayfarers:chisel", "/give @s minecraft:stone_bricks 16",
               "/give @s minecraft:stone_brick_stairs 8"],
     "Clic droit sur des briques de pierre : moussues, fissurées, sculptées… Le nom de la variante et sa place "
     "dans la famille (ex. 3/6) s'affichent au-dessus de la barre. Sur un escalier, l'orientation est gardée."),
    ("Table de taille", ["/give @s wayfarers:chisel_table", "/give @s wayfarers:brass_plating 64"],
     "Pose la table, mets la pile de placage de laiton dans la case : clique « Laiton gravé » ou « Grille en "
     "laiton », toute la pile change."),
    ("Symétrie de la baguette", ["/give @s wayfarers:builder_wand", "/give @s minecraft:stone_bricks 64"],
     "Accroupi + clic droit sur un bloc : centre du miroir (étincelles). G : miroir X, Z, X + Z. Clic droit sur "
     "un mur : contours dorés pour tes blocs, bleus pour les copies. Accroupi dans le vide : tout s'annule."),
    ("Golem de laiton", ["/give @s wayfarers:brass_block 2", "/give @s wayfarers:clockwork_heart"],
     "Empile les deux blocs, clic droit avec le cœur : le golem apparaît et te suit. Accroupi + clic droit main "
     "vide : « garde ici »."),
    ("Automates ennemis", ["/time set night", "/summon wayfarers:clockwork_spider ~ ~ ~6",
                           "/summon wayfarers:steam_drone ~ ~4 ~6"],
     "L'araignée s'arrête, sa clé ronronne, puis elle bondit. Le drone tourne au-dessus de toi, tire des rivets et "
     "se cabre avant de plonger."),
    ("Donneurs de quêtes", ["/wayfarers npc spawn guild_agent", "/give @s minecraft:bread 12"],
     "Un agent de la Guilde apparaît à tes pieds, son nom au-dessus de la tête ; il reste à son poste et ne prend "
     "aucun dégât. Clic droit : il salue, ses contrats s'affichent. Accepte « Des vivres pour la route », clique "
     "Rendre : les pains partent, émeraudes et fragments de carte arrivent. Le contrat apparaît dans le journal "
     "(J), onglet Contrats."),
    ("Habitants des structures", ["/wayfarers tp giant_tree", "/wayfarers tp jungle_ziggurat",
                                  "/wayfarers tp clockwork_citadel"],
     "Dans l'Arbre-monde, des villageois en robe verte vivent sur les étages du tronc (lit et métier chacun) et une "
     "druidesse attend à l'étage des couchettes. Près de la ziggourat, la loge des gardiens ; dans la Citadelle, "
     "le bricoleur du premier atelier. La nuit, aucun monstre n'apparaît chez eux."),
    ("Le Grand Horloger", ["/wayfarers boss grand_clockmaker"],
     "Il apparaît à 6 blocs (arène de 20 blocs autour de toi). Guette l'arrêt du temps (cercle qui se referme) et, "
     "à mi-vie, le rugissement puis minuit. Pour le vrai repaire : /wayfarers tp clockwork_citadel."),
    ("Merveilles en surface", ["/wayfarers tp inventor_manor", "/wayfarers tp sylvan_palace",
                               "/wayfarers tp geothermal_foundry", "/wayfarers tp tesla_observatory",
                               "/wayfarers tp sky_isles"],
     "Téléportation à la plus proche (générée si besoin, quelques secondes ; si aucune n'est assez près, le "
     "message le dit). Les Îles célestes flottent vers y 170-230 : tu arrives dessus ou dessous ; en dessous, "
     "passe en /gamemode spectator pour monter."),
    ("Merveilles souterraines", ["/wayfarers locate dwarven_city", "/wayfarers locate crystal_cathedral",
                                 "/locate structure wayfarers:dwarven_city", "/gamemode spectator"],
     "locate donne les coordonnées ; tp t'amène à la surface juste au-dessus. En spectateur, descends à travers la "
     "roche : la cité est vers y −50, le sol de la cathédrale vers y −40."),
    ("Carte du monde et mini-carte", ["/gamemode spectator", "/give @s wayfarers:wayfarer_atlas"],
     "La mini-carte est en haut à gauche ; H la masque, Z change son zoom (W en AZERTY). Vole un peu puis ouvre la "
     "carte avec M (la virgule en AZERTY) ou l'Atlas accroupi : le terrain vu est dessiné. Glisse, molette pour "
     "zoomer, Espace pour revenir sur toi."),
    ("Repères et signaux", ["/gamemode creative"],
     "Sur la carte, clic droit : « Poser un repère ici » (nom, couleur, icône, Partager). Clic sur le repère : sa "
     "fiche (Modifier, Privé/Partager, Supprimer). Clic molette ou B en visant un bloc : un signal visible une "
     "minute. À deux sur un serveur, l'autre joueur voit tes repères partagés, tes signaux et ce que tu as exploré."),
    ("Vue des grottes", ["/gamemode spectator", "/tp @s ~ 20 ~"],
     "Sous terre, la mini-carte et la carte montrent la grotte à ta hauteur (« Vue des grottes ») au lieu de la "
     "surface. Le bouton à droite de la carte l'active ou la coupe."),
    ("Écrans des machines", ["/give @s wayfarers:auto_harvester", "/give @s wayfarers:redstone_timer",
                             "/give @s wayfarers:entity_detector", "/give @s wayfarers:vacuum_hopper"],
     "Pose chaque machine et fais clic droit : un écran de laiton avec la zone, la sortie, le mode redstone… "
     "Survole un bouton pour son infobulle. Le minuteur affiche son intervalle, le détecteur sa cible et sa portée."),
    ("Terminal de guilde et relais", ["/give @s wayfarers:guild_terminal", "/give @s wayfarers:storage_relay 2",
                                      "/give @s minecraft:chest 8"],
     "Pose des coffres jusqu'à 48 blocs du terminal, ouvre-le : tous leurs objets sont dans une seule grille. Pose "
     "un coffre à 70 blocs : absent ; un relais entre les deux : il apparaît. Bouton réseau en haut à droite : "
     "clique un coffre pour l'exclure, « Montrer » les encadre (or relié, rouge exclu)."),
    ("Créatures marines", ["/wayfarers tp sunken_submarine", "/time set night",
                           "/summon wayfarers:glow_jellyfish ~ ~-3 ~4", "/summon wayfarers:reef_fish ~ ~-3 ~4",
                           "/summon wayfarers:manta_ray ~ ~-4 ~8", "/summon wayfarers:whale ~ ~-8 ~16"],
     "Tu arrives à la surface de la mer. La méduse pulse et brille la nuit (la toucher pique), les poissons "
     "nagent en banc, la raie bat des ailes et saute, la baleine remonte souffler."),
    ("Serpent de mer", ["/time set night", "/give @s minecraft:oak_boat", "/summon wayfarers:sea_serpent ~ ~-4 ~10"],
     "Une barre de boss apparaît. Il mord, charge (ton bateau se brise) et lève un tourbillon qui t'aspire. Il "
     "lâche des écailles de serpent de mer."),
    ("Épaves sous l'eau", ["/wayfarers tp sunken_submarine", "/wayfarers tp diving_bell",
                           "/wayfarers tp coral_shrine", "/wayfarers tp shipwreck_debris"],
     "Tu arrives à la surface juste au-dessus : plonge. Le sous-marin a une brèche dans le flanc et deux coffres ; "
     "dans la cloche de plongée, on respire."),
    ("Plongée et fonds marins", ["/give @s wayfarers:diving_helmet", "/give @s wayfarers:flippers",
                                 "/give @s wayfarers:pearl_oyster 2", "/give @s wayfarers:glow_anemone 4"],
     "Avec le casque, la tête sous l'eau : force de conduit (respiration, vue dégagée, minage normal). Avec les "
     "palmes, tu nages bien plus vite. Pose l'huître sous l'eau, clic droit quand elle est entrouverte : une perle."),
    ("Bois et pierres", ["/give @s wayfarers:glowwood_sapling", "/give @s minecraft:bone_meal 8",
                         "/give @s wayfarers:marble 16", "/locate biome minecraft:badlands"],
     "Plante la pousse et donne-lui de la poudre d'os : un arbre de bois-lueur aux feuilles qui luisent la nuit. "
     "Mets le marbre dans un tailleur de pierre : poli, briques, pilier, sculpté. Dans les badlands, creuse une "
     "falaise : des veines de roche rouillée."),
    ("Villages enrichis", ["/place structure minecraft:village_plains", "/place structure minecraft:village_desert",
                           "/place structure minecraft:village_snowy", "/place structure minecraft:pillager_outpost"],
     "Recommence quelques fois (chaque village est tiré au sort) : auberge, atelier à cheminée, tour de guet, "
     "marché, verger, cottages et manoirs dans le style du village, lampes en laiton dans les rues ; parfois une "
     "place avec une pierre de voyage. Les avant-postes ont des balistes à vapeur et des barricades."),
]

RECIPE_TYPES = {
    "minecraft:crafting_shaped": "Établi", "minecraft:crafting_shapeless": "Établi (sans forme)",
    "minecraft:crafting_transmute": "Établi (amélioration)", "minecraft:smelting": "Four",
    "minecraft:blasting": "Haut fourneau", "minecraft:smoking": "Fumoir", "minecraft:stonecutting": "Tailleur de pierre",
    "minecraft:smithing_transform": "Table de forgeron", "minecraft:campfire_cooking": "Feu de camp",
}
RECIPE_CATEGORIES = {"equipment": "Équipement", "building": "Construction", "misc": "Divers", "redstone": "Redstone",
                     "blocks": "Blocs", "food": "Nourriture"}

# ------------------------------------------------------------------ carte du monde et mini-carte
MAP_INTRO = ("Une carte qui se dessine toute seule pendant que tu explores, comme un carnet de cartographe. Sur un "
             "serveur, elle est commune : ce que découvre un joueur apparaît sur la carte de tous. Rien à fabriquer, "
             "elle marche dès la première connexion.")
# (titre, texte) : ce qu'est la carte du monde, comment l'ouvrir, comment s'en servir
MAP_WHAT = [
    ("C'est quoi", "La carte du monde montre en vue du ciel tout ce qui a été exploré, avec les pierres de voyage, "
                   "les repères, les joueurs, les signaux, ta tombe, ta dernière mort, le point d'apparition et les "
                   "structures trouvées à la boussole. À droite : la légende (clique une ligne pour masquer ce type de "
                   "marqueur) et la liste de tes repères avec leur distance."),
    ("Comment l'ouvrir", "Touche M, ou l'Atlas du Voyageur en main : accroupi + clic droit. Sur un clavier AZERTY, la "
                         "touche M de Minecraft est la virgule (réglable dans Options → Commandes)."),
    ("Comment s'en servir", "Glisse pour déplacer la carte, molette (ou + et −) pour zoomer, Espace pour revenir sur "
                            "toi. Clique un marqueur pour ouvrir sa fiche. En bas, les coordonnées et le biome sous ta "
                            "souris."),
]
# (geste, effet) : commandes de l'écran de la carte
MAP_CONTROLS = [
    ("Glisser", "déplacer la carte"),
    ("Molette, + ou −", "zoomer, dézoomer"),
    ("Espace", "recentrer sur toi"),
    ("Clic sur un marqueur", "sa fiche : nom, coordonnées, distance"),
    ("Clic droit", "poser un repère, signaler l'endroit, copier les coordonnées"),
    ("Clic molette", "envoyer un signal à tous"),
    ("M ou Échap", "fermer la carte"),
]
# (ancre, titre, texte, icône) : les fonctions de la carte
MAP_FEATURES = [
    ("carte-partagee", "Exploration partagée", "Le serveur dessine les chunks autour de chaque joueur et garde la "
     "carte de chaque dimension. Ce que ton ami a exploré pendant ton absence est déjà sur ta carte. Un serveur qui "
     "préfère des cartes personnelles met map.sharedExploration à false : chacun ne voit alors que ce qu'il a vu "
     "lui-même (le serveur garde les deux, on peut basculer à tout moment).", "wayfarers:wayfarer_atlas"),
    ("reperes", "Repères privés ou partagés", "Clic droit sur la carte, « Poser un repère ici » : un nom, une "
     "couleur, une icône (maison, pioche, étoile…) et la case « Partager avec tout le monde ». Un repère privé n'est "
     "visible que par toi ; un repère partagé apparaît chez tous, avec le nom de celui qui l'a posé. Sa fiche permet "
     "de le modifier, de le rendre privé ou de le supprimer.", "minecraft:red_banner"),
    ("signaux", "Signaux", "Touche B en visant un endroit, ou clic molette sur la carte : un point d'exclamation "
     "orange apparaît sur la mini-carte et la carte de tous les joueurs pendant une minute. Parfait pour « viens voir "
     "ici » ou « le boss est là ».", "minecraft:bell"),
    ("vue-grottes", "Vue des grottes", "Sous terre, la mini-carte et la carte dessinent la grotte à ta hauteur (une "
     "tranche du monde) au lieu de la surface loin au-dessus ; les parois sont en sombre. Le bouton sur le côté de la "
     "carte l'active ou la coupe (option map.caveMode).", "minecraft:lantern"),
]
MINIMAP_TEXT = [
    "La mini-carte est un hublot de laiton dans un coin de l'écran (en haut à gauche au départ). Elle montre le "
    "terrain autour de toi, la flèche de ta direction, et les pierres de voyage, repères, joueurs, signaux, tombes "
    "et ta dernière mort. En dessous : tes coordonnées et le biome où tu es.",
    "H la masque ou la réaffiche, Maj + H change sa taille (petite, moyenne par défaut, grande, énorme : 56 à "
    "128 px). Z change son zoom (4 niveaux) ; en AZERTY c'est la touche W. Taille, coin de l'écran, forme (ronde "
    "ou carrée), rotation, coordonnées et opacité se règlent aussi dans Mods → Wayfarers → Config, onglet "
    "Mini-carte (ou config/wayfarers-client.toml).",
]

# ------------------------------------------------------------------ machines : écrans
MACHINE_SCREENS_INTRO = ("Clic droit sur une machine : un écran de laiton s'ouvre. En haut, ce qu'elle fait et son "
                         "état en une ligne ; au milieu, ses réglages en boutons (survole-les pour une infobulle) ; "
                         "à droite, ses cases quand elle en a. Les images ci-dessous sont dessinées avec les vraies "
                         "textures du jeu ; touche une image pour l'agrandir.")
SETTINGS_TEXT = ("Mods → Wayfarers → Config ouvre les réglages du mod dans le même style : barres de vie (toujours, "
                 "blessées, jamais), chiffres de dégâts, suivi de quête, cartes d'astuce, et un bouton vers les "
                 "touches. La touche du Manuel (maintenue sur un objet pour ouvrir sa page) se change maintenant : W "
                 "par défaut, c'est-à-dire Z sur un clavier AZERTY.")

# ------------------------------------------------------------------ terminal de guilde
TERMINAL_INTRO = ("Un seul écran pour tous les coffres de ta base, sans câble ni énergie. Le terminal voit chaque "
                  "conteneur à 48 blocs autour de lui ; des relais de stockage prolongent sa portée, 32 blocs par "
                  "32 blocs, jusqu'à la réserve la plus lointaine.")
TERMINAL_DIAGRAM = ("Vue du dessus : le carré doré est la portée du terminal (48 blocs de chaque côté, 32 en haut et "
                    "en bas). Un relais posé dans cette zone ajoute son propre carré de 32 blocs, et un relais posé "
                    "dans le carré d'un autre relais s'enchaîne à son tour. Les coffres hors de toute zone (en gris) "
                    "ne sont pas reliés.")

# ------------------------------------------------------------------ océans vivants
OCEANS_INTRO = ("Les mers ne sont plus vides : créatures, récifs, forêts de varech, huîtres perlières, cheminées à "
                "bulles et petites épaves à fouiller, dans tous les océans de Minecraft, dans les régions jamais "
                "générées.")
OCEANS_WHERE = ("Partout en mer : méduses, anémones, cheminées à bulles, arches rocheuses et ruines. Mers froides "
                "et tempérées : grandes forêts de varech. Mers tempérées et chaudes : prairies d'herbes marines et "
                "bancs d'huîtres. Mers chaudes : poissons de récif, jardins de corail et coraux géants. Au large, dans les océans profonds : baleines et serpent de mer.")
# (titre, texte, icône, où)
OCEAN_FLOOR = [
    ("Forêts de varech", "Le varech pousse en bosquets serrés qui montent jusqu'à la surface : on s'y perd "
     "facilement, et les poissons s'y cachent.", "minecraft:kelp", "mers froides et tempérées"),
    ("Prairies marines", "De larges tapis d'herbes marines sur le sable, entre les récifs.", "minecraft:seagrass",
     "mers tempérées et chaudes"),
    ("Récifs et coraux géants", "Des jardins de corail bien plus denses, et de grandes formes en blocs de corail : "
     "tours, éventails, arches, cerveaux.", "minecraft:brain_coral_block", "mers chaudes"),
    ("Anémones lumineuses", "Elles éclairent le fond la nuit, en trois couleurs. Casse-les pour les ramasser : de "
     "quoi décorer un aquarium.", "wayfarers:glow_anemone", "toutes les mers"),
    ("Huîtres perlières", "Clic droit sur une coquille entrouverte pour prendre sa perle ; sous l'eau, elle en refait "
     "une avec le temps. Quatre perles valent une émeraude à l'établi.", "wayfarers:pearl_oyster",
     "mers tempérées et chaudes"),
    ("Cheminées à bulles", "Des cheminées de basalte sur du magma soufflent une colonne de bulles jusqu'à la "
     "surface : entre dedans pour remonter d'un coup et reprendre ton souffle.", "minecraft:magma_block",
     "toutes les mers (rares)"),
    ("Arches et aiguilles", "Arches de pierre, piliers et anneaux rocheux posés sur le fond.", "minecraft:stone",
     "toutes les mers"),
    ("Ruines englouties", "Colonnades brisées, statue tombée, escalier et tas d'amphores.",
     "minecraft:chiseled_stone_bricks", "toutes les mers"),
]
OCEAN_STRUCTS = ["sunken_submarine", "diving_bell", "coral_shrine", "shipwreck_debris"]
DIVING_TEXT = {
    "diving_helmet": ("Un dôme de laiton à hublot. La tête sous l'eau, il donne la force de conduit : tu respires, "
                      "tu vois clair et tu mines à pleine vitesse. Deux recettes : avec quatre écailles du serpent de "
                      "mer, ou sans combat avec trois blocs de cuivre. Il se répare avec une écaille ou un lingot de "
                      "laiton."),
    "flippers": ("Aux pieds, tu nages bien plus vite, comme avec Agilité aquatique II. Deux cuirs et deux blocs "
                 "d'algues séchées."),
}
# où vit chaque créature, quand les données ne le disent pas simplement
MOB_WHERE = {
    "glow_jellyfish": "Toutes les mers, par groupes de 2 à 4.",
    "reef_fish": "Mers chaudes et tièdes, en bancs.",
    "manta_ray": "Océans tempérés et chauds, près de la surface.",
    "whale": "Océans profonds, seule. Rare.",
    "sea_serpent": "La nuit, au-dessus des eaux profondes, attiré par un bateau ou un nageur. Replonge à l'aube.",
}
MOB_HP = {"reef_fish": 3}  # vie par défaut de Minecraft, quand la classe ne la fixe pas
MOB_BADGE = {"sea_serpent": "Mini-boss"}

# ------------------------------------------------------------------ blocs du monde
WORLDBLOCKS_INTRO = ("Deux bois et trois pierres propres au mod, chacun décliné en ensemble complet pour construire. "
                     "Les bois se font pousser à partir d'une pousse ; les pierres se minent en veines ou se "
                     "fabriquent à partir de pierres ordinaires.")
# bois -> (où, texte)
WOODS = {
    "glowwood": ("Pousse à fabriquer ; coffres de l'Arbre géant et du Palais sylvain.",
                 "Troncs pâles et feuilles turquoise piquées de points lumineux qui luisent la nuit, sur de grands "
                 "arbres touffus."),
    "rustwood": ("Pousse à fabriquer ; coffres de la Citadelle d'horlogerie, du Port céleste, des Bas-fonds et de "
                 "la Fonderie géothermique.",
                 "Écorce rouge sombre et feuilles couleur de rouille, sur des arbres fourchus."),
}
WOOD_HOW = ("Un ensemble complet, comme le chêne : bûches, écorce, planches, escaliers, dalles, barrières, "
            "portillons, portes, trappes, boutons et plaques de pression. La hache écorce les bûches ; les feuilles "
            "donnent des pousses qui font repousser le même arbre.")
# pierre -> (où, texte)
STONES = {
    "marble": ("Veines dans les montagnes et les collines battues par les vents, de y 32 aux sommets.",
               "Blanc veiné de gris, en grosses poches dans la roche des montagnes."),
    "rust_rock": ("Veines dans les badlands, les plateaux de savane et les savanes battues par les vents (y 32 à 160).",
                  "Une roche rouge et orangée, en grosses poches sous les terres rouges."),
    "blue_slate": ("Veines dans l'ardoise des abîmes, sous y 0, partout.",
                   "Ardoise d'un bleu profond, en grosses poches tout au fond du monde."),
}
STONE_HOW = ("Le tailleur de pierre transforme la pierre brute en version polie, briques, pilier, carreaux ou "
             "sculptée, avec leurs escaliers, dalles et murets ; le burin du graveur passe de l'une à l'autre.")

# ------------------------------------------------------------------ serveur et performances
PERF_INTRO = ("Ce qui a été allégé pour qu'un serveur à plusieurs reste fluide, même avec de grandes bases et "
              "beaucoup de monstres, et les quelques options utiles à connaître.")
# (titre, [points])
PERF_POINTS = [
    ("Côté serveur", [
        "Les arènes de boss, les sceaux et les gargouilles ne parcourent plus toutes les créatures autour d'eux à "
        "chaque tick : ils regardent seulement la liste des joueurs.",
        "La boussole des structures, la boussole de dirigeable et /wayfarers locate gardent leur réponse en "
        "mémoire (même « rien trouvé », la recherche la plus lente).",
        "Le mana, les bonus d'ensemble d'armure et les anneaux aimantés se calculent moins souvent, et les anneaux "
        "de tous les joueurs ne tombent plus sur le même tick.",
        "La carte partagée lit quelques chunks par tick (environ une milliseconde au plus) et écrit ses fichiers sur "
        "un fil à part ; chaque joueur a un débit limité, ouvrir la carte ne sature pas la connexion.",
    ]),
    ("Côté joueur", [
        "Barres de vie : des tests rapides avant de chercher la créature, et plus rien du tout quand barres et "
        "chiffres de dégâts sont coupés.",
        "Le suivi de quête et les cartes d'astuce préparent leur texte une fois au lieu de le refaire à chaque "
        "image ; la recherche de la page du Manuel derrière chaque infobulle est mémorisée.",
    ]),
    ("Génération du monde", [
        "Les structures vérifient d'abord le biome, puis quelques colonnes de terrain, avant d'assembler quoi que "
        "ce soit : un emplacement qui ne convient pas coûte très peu.",
    ]),
]
# (option, conseil)
PERF_OPTIONS = [
    ("storage.terminalRange", "Portée du terminal. Baisse-la si les bases sont énormes et serrées."),
    ("storage.terminalHeight", "Portée en hauteur du terminal et des relais."),
    ("storage.relayRange", "Portée de chaque relais."),
    ("storage.maxContainers", "Plafond de conteneurs par réseau : la vraie sécurité pour le serveur."),
    ("map.sharedExploration", "Carte commune (true) ou personnelle (false). Ne change pas le coût : le serveur "
                              "garde les deux."),
    ("hud.healthBarRange", "Chez chaque joueur : distance des barres de vie. Baisse-la dans les fermes à monstres."),
    ("world.structureFit", "Les structures ne se posent que là où le terrain leur convient. Sur false, elles "
                           "apparaissent partout où la grille le dit."),
]

# « En jeu » : les vraies captures d'écran du client de test (CI), juste après les nouveautés.
INGAME_TITLE = "En jeu"
INGAME_INTRO = ("Ces images ne sont pas des maquettes : ce sont de vraies captures du jeu. À chaque compilation, le "
                "serveur de test lance le vrai Minecraft avec le mod, ouvre chaque écran, pose des machines et des "
                "créatures, puis prend la photo tout seul. Clique une image pour l'agrandir.")
INGAME_NOTE = ("Le client de test tourne en anglais : dans ta partie en français, les textes des écrans sont "
               "traduits. Les images se mettent à jour à chaque nouvelle compilation.")
# (nom de la capture, titre, légende, ancre de la section liée). L'ordre est celui de la galerie ; la première
# capture s'affiche en grand.
INGAME_SHOTS = [
    ("hud_minimap", "La mini-carte", "Le hublot de laiton en haut à gauche : le terrain autour de toi, ta direction, "
     "tes coordonnées et le nom du biome.", "mini-carte"),
    ("world_map", "La carte du monde", "Touche M. À droite la légende et tes repères, sur le bord les boutons de "
     "zoom, de vue des grottes et de liste.", "carte"),
    ("quest_journal", "Le journal de quêtes", "Touche J. Les cinq chapitres à gauche, leurs étapes au milieu, et "
     "à droite l'objectif et les récompenses de la quête choisie.", "quetes"),
    ("talent_tree", "L'arbre de talents", "Touche K. Les quatre branches : Guerrier, Explorateur, Arcaniste et "
     "Mécaniste. Le talent du bas de chaque branche est un pouvoir actif.", "talents"),
    ("manual_welcome", "Le Manuel du Voyageur", "La page d'accueil. Le sommaire à gauche range les 81 pages par "
     "thème.", "manuel"),
    ("manual_machines", "Le Manuel, page machines", "Chaque système a sa page, avec les objets concernés en bas.",
     "manuel"),
    ("machine_harvester", "L'écran d'une machine", "La moissonneuse automatique : ce qu'elle fait en ce moment, sa "
     "zone, la replantation, la sortie et le mode redstone.", "ecrans-machines"),
    ("guild_terminal", "Le terminal de guilde", "Le contenu de tous les coffres reliés dans une seule grille, avec "
     "la recherche et les boutons pour tout ranger.", "terminal"),
    ("waystone", "Une pierre de voyage", "La liste des pierres découvertes ; à droite, la destination choisie et "
     "les boutons Voyager, Épingler et Renommer.", "m-waystones"),
    ("creative_tab", "L'onglet créatif", "Tous les objets du mod dans leur onglet. L'infobulle rappelle la touche "
     "qui ouvre la page du Manuel.", "objets"),
    ("creatures", "Automates sur la scène de test", "Le golem de laiton au centre, une araignée-horloge devant, le "
     "bassin de verre d'une méduse lumineuse à gauche ; le Grand Horloger se tient au fond, à droite.",
     "automates"),
    ("mega_structure", "La Citadelle d'horlogerie", "Une merveille posée par le serveur de test et vue du ciel : la "
     "tour-horloge, ses toits de cuivre et ses cheminées.", "s-clockwork_citadel"),
]

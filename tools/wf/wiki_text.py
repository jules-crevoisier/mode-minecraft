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
    ("Ouvre le Manuel", "Tu le reçois à la première connexion, avec l'Atlas : c'est tout, le reste se gagne en route. Une page par système, avec sommaire. Astuce : survole "
     "n'importe quel objet du mod dans ton inventaire et maintiens la touche du manuel (Z sur un clavier AZERTY, réglable dans Commandes) pour ouvrir directement sa page.",
     ["wayfarer_manual"]),
    ("Suis la carte en haut à droite", "Le suivi de quête montre toujours ta prochaine étape, quête ou contrat, et "
     "passe tout seul à la suivante. Le journal (touche J) détaille chaque chapitre ; « Suivre » épingle une autre "
     "quête. Les quêtes sont communes à tout le groupe.", ["wayfarer_atlas"]),
    ("Rencontre l'agent de la Guilde", "À ton arrivée, l'avant-poste de la Guilde le plus proche est marqué sur ta "
     "carte (M) et sa direction s'affiche dans le chat ; un agent tient aussi le Relais de la Guilde de nombreux "
     "villages. L'Atlas redonne la direction tant que tu n'y es pas allé.", ["map_fragment", "wayfarer_atlas"]),
    ("Gagne ta boussole des structures", "Deux contrats de l'agent : apporter 12 pains, puis inspecter une tour de "
     "guet en ruine (il la marque sur ta carte). Ta récompense : la boussole qui trouve toutes les autres "
     "structures. Les contrats sont personnels : chaque joueur gagne la sienne. Plus tard, d'autres se fabriquent "
     "avec un éclat de lithite.", ["structure_compass"]),
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
    "Maj + H": "Passer à la taille suivante de la mini-carte (56, 68, 96, 128 px) ; au pixel près : options de la "
               "carte (M, puis l'engrenage)",
    "Z": "Changer le zoom de la mini-carte",
    "B": "Signaler l'endroit visé à tous les joueurs (visible une minute sur les cartes)",
    "W": "Maintenir sur un objet du mod : ouvrir sa page du Manuel",
    # the recipe viewer's keys only work in an inventory: they share letters with keys that only work in game
    "key.brasshaven.recipes": "Dans un inventaire, sur un objet (case ou liste) : ses recettes (le livre de recettes)",
    "key.brasshaven.uses": "Dans un inventaire, sur un objet : ses utilisations",
    "key.brasshaven.recipe_panel": "Dans un inventaire : afficher / masquer la liste des objets à côté de la fenêtre",
    "G": "Baguette du bâtisseur : changer de symétrie (désactivée, miroir X, miroir Z, X + Z)",
    "Clic molette": "Sur une case d'un coffre : trier ce coffre",
}
# Touches dont la lettre change sur un clavier AZERTY (Minecraft garde la position de la touche, pas la lettre)
KEY_AZERTY = {"W": "Z", "Z": "W", "M": ","}
KEYS_NOTE = ("Les lettres ci-dessus sont celles d'un clavier QWERTY. Minecraft retient l'emplacement de la touche : en "
             "AZERTY, la touche du Manuel (W) est donc sur Z, le zoom de la mini-carte (Z) sur W et la carte (M) sur la "
             "virgule. Toutes se changent dans Options → Commandes → rubrique Brasshaven, ou depuis Mods → Brasshaven → "
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
    "boss": ("op", "Fait apparaître un boss devant toi, pour le tester (à son cycle NG+ du monde). "
                   "cycle <boss> [n] : lit ou règle le cycle d'un boss (0 à 7)."),
    "fitcheck": ("op", "Trouve chaque structure de la Surface, la génère et mesure comment elle se pose sur le relief (rapport et images PNG dans le dossier du serveur). Sert aux tests ; prend plusieurs minutes."),
    "progress": ("op", "reset : remet la quête à zéro ; complete : accorde toutes les quêtes."),
    "npc": ("op", "Donneurs de quêtes : spawn <rôle> en pose un à tes pieds (guild_agent, scholar, tinkerer, druid, "
                  "dwarf_elder), move amène le plus proche (8 blocs) à ta place et en fait son nouveau poste, role "
                  "<rôle> change son métier, remove le retire."),
    "contracts": ("op", "reset [joueur] : efface les contrats acceptés et terminés d'un joueur ; complete <contrat> "
                        "[joueur] : rend un contrat pour lui, récompenses comprises."),
    "guide": ("tous", "Remet sur la carte le repère de l'avant-poste de la Guilde le plus proche, avec sa direction."),
    "progression": ("op", "selftest : vérifie les règles de la progression (kit d'arrivée, boussole gagnée par "
                          "contrat, recette)."),
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
    "compat.requireSameVersion": "Refuse les joueurs dont la version de Brasshaven diffère de celle du serveur, avec un "
                                 "message qui donne les deux versions et la page de téléchargement. Sur false : seuls "
                                 "un protocole réseau incompatible ou des blocs/objets manquants les refusent.",
    "compat.downloadUrl": "Page de téléchargement donnée aux joueurs refusés (la page de ton modpack, par exemple). "
                          "Vide : la page du mod.",
    "updates.checkForUpdates": "Cherche une version plus récente de Brasshaven (GitHub, en arrière-plan) : un message "
                               "avec le lien du changelog en jeu, une ligne dans le journal du serveur. Rien n'est "
                               "jamais téléchargé.",
    "map.minimap": "Affiche la mini-carte (touche H en jeu ; Maj + H change sa taille).",
    "map.corner": "Coin de l'écran de la mini-carte : TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT ou BOTTOM_RIGHT.",
    "map.size": "Préréglage de taille de la mini-carte, cadre compris : SMALL (56 px), MEDIUM (68 px), LARGE (96 px) "
                "ou XLARGE (128 px). En jeu : Maj + H, ou Mods → Brasshaven → Config, onglet Mini-carte. Sert quand "
                "map.sizePixels vaut 0 (les anciens fichiers de réglages gardent ainsi leur taille).",
    "map.sizePixels": "Taille exacte de la mini-carte à l'écran, cadre compris, de 48 à 160 px (0 : le préréglage "
                      "map.size). En jeu : le curseur des options de la carte (M, puis le bouton engrenage), par pas "
                      "de 4 px ; un préréglage la règle aussi.",
    "map.relief": "Relief des cartes, calculé à partir des hauteurs explorées : FLAT (couleurs simples), NORMAL "
                  "(pentes éclairées du nord-ouest, vallées plus sombres, hauteurs plus pâles) ou STRONG (plus "
                  "marqué). L'eau fonce avec la profondeur dans tous les cas.",
    "map.contours": "Courbes de niveau sur les cartes : une ligne fine tous les 16 blocs de hauteur, une plus "
                    "marquée tous les 64 (pas sur la cime des arbres).",
    "map.worldMap3d": "La carte du monde s'ouvre en vue 3D inclinée (le terrain exploré en relief, chaque colonne à "
                      "sa hauteur) au lieu de la vue du ciel. Le bouton cube de la carte bascule entre les deux.",
    "map.opacity": "Opacité du terrain de la mini-carte, en pourcentage (30 à 100) : baisse-la pour voir le monde à "
                   "travers.",
    "map.shape": "Forme : ROUND (hublot de laiton) ou SQUARE (cadre carré).",
    "map.rotate": "La mini-carte tourne avec toi (ta direction toujours en haut). Sur false : le nord est en haut.",
    "map.zoom": "Zoom de la mini-carte, de 0 (le plus large) à 3 (le plus proche). Touche Z en jeu.",
    "map.showCoordinates": "Affiche tes coordonnées et le biome sous la mini-carte.",
    "map.caveMode": "Sous terre, la carte dessine la grotte autour de toi (une tranche à ta hauteur) au lieu de la "
                    "surface.",
    "map.radar": "Radar : les créatures autour de toi en petites icônes sur la mini-carte (et sur la carte du monde "
                 "zoomée près de toi). Tout se passe dans ton jeu : le serveur n'envoie rien de plus.",
    "map.radarIcons": "Icônes du radar : HEADS (la tête de la créature quand elle est connue, sinon un point) ou DOTS "
                      "(un point coloré selon le genre).",
    "map.radarHostile": "Radar : les créatures hostiles (en rouge). Les boss s'affichent toujours tant que le radar "
                        "est activé.",
    "map.radarPassive": "Radar : les animaux (en vert) et les créatures neutres (en jaune, en rouge une fois en "
                        "colère).",
    "map.radarNpcs": "Radar : villageois, marchands ambulants et personnages du mod.",
    "map.radarItems": "Radar : les objets posés au sol (petits points gris).",
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
    ("Emplacements d'accessoires", "À gauche de l'armure, l'inventaire a cinq cases d'accessoires : un dos (planeur "
     "en laiton), deux anneaux (anneau aimanté, anneau arcanique), une amulette (amulette de mana) et une ceinture "
     "(montre à gousset). Un accessoire n'agit que porté ; Maj + clic pour l'équiper. En créatif, les cases sont à "
     "droite de l'armure. À la mort, ils suivent la règle keepInventory (sinon, direction la tombe)."),
    ("Infobulles claires", "Chaque objet du mod a la même infobulle : son nom, une phrase d'ambiance en italique, "
     "puis les règles en clair avec les vrais chiffres (dégâts, recharge, mana, emplacement, bonus d'ensemble). "
     "Quand il y a plus à dire : « Maj enfoncée : plus de détails »."),
    ("Danger et élites", "Plus tu t'éloignes du spawn (+1 niveau tous les 900 blocs), plus les monstres ont de vie "
     "et de dégâts. Les élites (nom doré) lâchent un meilleur butin. Une lune de sang tous les 7 nuits."),
]

DIMENSIONS = {"overworld": "Surface", "nether": "Nether", "end": "End"}

# Merveilles (méga-structures) : affichées en grand, avec rotation 360° et vue en coupe. Le générateur y ajoute
# toute structure citée dans les pages « wonders* » du Manuel (tools/wf/guide.py) ; l'ordre ci-dessous passe en premier.
WONDERS = ["clockwork_citadel", "sky_harbour", "undercity", "sunken_citadel"]

# Les tonneaux des pièces (tools/wf/barrels.py), en une phrase sous le titre des structures
BARRELS_NOTE = ("Les tonneaux des pièces ne sont plus vides : environ deux sur trois gardent quelques provisions "
                "selon le lieu (vivres dans les cuisines et réserves, pépites et charbon dans les forges, papier et "
                "encre dans les bibliothèques, flèches dans les casernes, poisson et ficelle sur les quais, minerai "
                "dans les mines). Le vrai butin reste dans les coffres.")

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
    "walking_fortress": "L'épave d'un marcheur de siège en laiton, figé en plein pas au milieu d'un cratère brûlé : "
                        "quatre jambes de 60 blocs, une coque rivetée de 70 blocs portée à 55 blocs du sol, deux "
                        "cheminées et un mât qui montent à 130. On entre par la brèche d'un pied, on monte l'escalier en "
                        "colimaçon de la jambe, la salle du genou puis l'escalier de la cuisse jusqu'à la cale. Au-dessus : "
                        "la salle des machines, le pont des canons, et sur le pont supérieur l'arène du boss devant la "
                        "tour de commandement et sa salle forte.",
    "rock_necropolis": "Un massif de grès rose de 170 blocs, taillé comme à Pétra et Abou Simbel. Un canyon étroit et "
                       "sinueux, aux parois de 50 blocs, débouche sur une place cachée où quatre rois assis de 42 blocs "
                       "encadrent un portail de 18 blocs, sous une frise de babouins et un étage à tholos. Dedans : la "
                       "salle hypostyle aux piliers osiriaques, la galerie des couronnes avec son balcon, puis trois "
                       "niveaux de tombeaux : salle d'embaumement, galerie des niches, galerie inondée, couloir piégé, "
                       "trésor et sa cachette secrète, un lieu de grâce, l'arène du roi et sa salle forte, d'où le "
                       "puits du roi remonte jusqu'à la salle hypostyle.",
    "fallen_colossus": "La statue de 155 blocs d'un chevalier en armure, pierre sous plates de bronze vert-de-gris, "
                       "tombée sur le flanc en travers d'une vallée et à demi enfoncée dans la terre : le heaume tourné "
                       "vers le ciel avec son cimier, l'épaulière à 50 blocs, un genou replié en arche, la main tendue "
                       "dans l'herbe et l'épée brisée en trois derrière son dos. On entre par le poignet brisé : le "
                       "tunnel de l'avant-bras, la salle du coude, l'escalier du bras jusqu'au balcon de la salle des "
                       "côtes, une voûte de 30 blocs ouverte sur le ciel par une brèche de la cuirasse. Côté épaule, "
                       "le reliquaire sous l'épaulière ; côté hanche, la crypte du bassin et le tunnel de la jambe qui "
                       "ressort par le genou. Par le tunnel du cou, l'arène du boss dans le heaume, sous les barreaux "
                       "de la visière, et sous son sol la salle forte, avec une porte de fer qui ne s'ouvre que de "
                       "l'intérieur.",
    "chained_bastion": "Une forteresse de pierre noire et d'or de 120 blocs suspendue sous le plafond du Nether par "
                       "huit chaînes géantes, au-dessus d'un lac de lave : une quille en gradins, une forêt de flèches "
                       "inversées et des chaînes brisées qui pendent vers la lave. Depuis l'éperon rocheux du "
                       "débarcadère, un pont de chaînes mène à une pile ; au-delà, le pont est rompu, et il faut "
                       "gravir l'escalier posé sur le dos de la chaîne d'ancrage jusqu'au porche. Dedans : la prison "
                       "des cages suspendues au-dessus d'un puits ouvert sur la lave, la caserne et sa cellule secrète, "
                       "la halle de la forge, la chapelle, la salle du lieu de grâce, puis une passerelle couverte "
                       "jusqu'au tambour du boss, au sol de grilles, et la salle du trésor.",
    "pilgrims_ascent": "Un croc de roche de 124 blocs, à-pic au nord au-dessus d'un bassin, et sur son flanc sud un "
                       "escalier en lacets de près de 500 marches taillé dans la falaise : six rampes, seize portiques "
                       "rouges et des lanternes à chaque palier. Au pied, le grand torii, le bassin de purification et "
                       "une pierre de passage ; puis les sanctuaires : les moulins à prières sur l'épaule, la cascade "
                       "qui tombe d'une gargouille de pierre, la grotte de la cloche (gargouilles, pierre de passage), "
                       "le pont du vent qui rejoint une aiguille voisine et son pavillon, la cellule de l'ermite et sa "
                       "cave secrète. Au sommet, une porte couverte, le lieu de grâce, puis le temple : sa salle ronde "
                       "est l'arène, sous le beffroi de la grande cloche de bronze. Derrière, le sanctuaire suspendu "
                       "au-dessus du vide garde le trésor, et son balcon offre la descente la plus rapide : le saut "
                       "dans le bassin, 120 blocs plus bas.",
    "glacier_hall": "Une langue de glacier longue de 200 blocs, au front taillé en façade : une frise, l'œil du jarl, "
                    "deux statues de jarls de 34 blocs et une porte en arc, sous l'arête d'un toit de longhouse qui "
                    "perce la glace ; à l'est, une corne de roche de 126 blocs. Devant, la moraine, des pierres levées "
                    "et le camp des jarls. Dedans, la halle-cathédrale : une nef de glace à côtes et à colonnes de "
                    "glace tassée, des bas-côtés aux guerriers gelés, des tribunes, la croisée et sa pierre de "
                    "passage, la salle du trône dans l'abside, puis la salle des gardes, la cave à hydromel, "
                    "l'armurerie, les cuisines, la bibliothèque du scalde, la salle des guerriers gelés et le dortoir "
                    "des huscarls. Au nord, un pont franchit la crevasse (rompu en son milieu) ; l'escalier du jarl "
                    "monte dans la corne jusqu'au lieu de grâce et à l'arène sous un dôme ouvert sur le ciel. Derrière, "
                    "le caveau du trésor, et le Saut du jarl : 47 blocs de chute dans la source, d'où la rivière de "
                    "fonte ressort par une grotte de glace au front du glacier.",
    "caldera_ringwall": "Un ancien volcan de 250 blocs de large dont le cratère porte une enceinte circulaire : seize "
                        "pans de courtine crénelée sur la crête, des tours à toits rouges et, au milieu du lac de "
                        "cratère, une aiguille de roche couronnée d'un donjon à flèche de cuivre. Au pied, le camp et "
                        "sa pierre de passage, puis la route jusqu'à la barbacane et le châtelet : un grand escalier de "
                        "trois volées monte dans sa salle jusqu'à la cour de la porte (lieu de grâce, écuries). On "
                        "suit le chemin de ronde de tour en tour (tourelles, bastion de l'arsenal, caserne) jusqu'à la "
                        "cour du nord (lieu de grâce, grande salle, cuisines), puis on descend dans les souterrains : "
                        "la citerne, la prison et son ossuaire secret, la galerie à arcades d'où un pont sur piles "
                        "franchit le lac jusqu'à l'aiguille. Un escalier à noyau monte dans la roche jusqu'au donjon "
                        "(lieu de grâce), puis la brume ouvre l'arène au sommet ; derrière des barreaux scellés, le "
                        "caveau, et le saut dans le lac. Raccourcis : portes de fer à sens unique dans les tours, une "
                        "échelle sous une trappe, la poterne d'eau qui ramène de la grève à la cour de la porte.",
    "dreadnought_wreck": "Un cuirassé à vapeur de laiton et de fer long de 180 blocs, échoué sur un récif et brisé en deux : la proue inclinée à demi noyée, la poupe droite avec sa tour de passerelle, son mât tripode, trois cheminées (dont une couchée sur le pont) et quatre tourelles aux canons énormes. Sur un îlot de récif, un campement de naufragés et une pierre de passage ; une passerelle de planches franchit la brèche. Dans la poupe : le poste d'équipage, le carré des officiers, le puits de la soute à munitions et son monte-charge, la salle des machines (cylindres, bielles, passerelles ; lieu de grâce), les cabines du pont supérieur (lieu de grâce) et la cabine du capitaine sous les fenêtres de poupe. Dans la proue noyée, le pont des torpilles. Passé la brume, la chaufferie des chaudières : l'arène du boss ; derrière des barreaux scellés, la chambre forte, et le monte-charge à échelle dont la porte de fer ramène au pont.",
    "great_aqueduct": "Un aqueduc de grès de 240 blocs qui franchit une vallée sur trois rangs d'arcades (arches de "
                      "12, 8 et 4 blocs), le canal en eau au sommet. Au fond de la vallée, une rivière, un pont de "
                      "dalles et une pierre de passage au pied de la tour d'escalier ouest. La route de la crête "
                      "monte à la maison de la source (lieu de grâce) où l'eau sort de la colline : salle voûtée, "
                      "vanne, cascade et une grotte secrète derrière. On suit le chemin de halage le long du canal "
                      "jusqu'à la brèche : une section effondrée où la maison du gardien des vannes s'est bâtie "
                      "sur le tablier, avec son jardin et sa grue ; une trappe cache une salle dans une pile. Un "
                      "escalier de gravats remonte dans la galerie d'entretien percée dans les piles : magasins, "
                      "dortoir, atelier, salle des lampes (lieu de grâce), archives, salle des jauges. Au bout, le "
                      "castellum sur son plateau : la salle des vannes, la salle de distribution, le logis du "
                      "gardien, le beffroi et sa tourelle. Une seconde tour descend à l'antichambre (lieu de grâce) "
                      "puis, passé la brume, dans la grande citerne voûtée sous le castellum : l'arène du boss ; "
                      "derrière des barreaux scellés, le caveau, et le tunnel de vidange dont la porte de fer ramène "
                      "dans la vallée. Raccourcis : portes de fer à sens unique dans les tours, l'escalier de la brèche.",
    "sun_ziggurat": "Une pyramide de grès à sept degrés, large de 140 blocs et haute de 70, posée sur le sable "
                    "du désert et couronnée d'un colossal planétaire de laiton : quatre jambes arquées, deux "
                    "anneaux portant les planètes et un soleil de pierre lumineuse. Sous lui, une lentille d'ambre "
                    "concentre le jour dans un puits qui traverse le cœur. Depuis le campement et sa pierre de "
                    "passage, une allée de sphinx et d'obélisques mène à la rampe processionnelle bordée de sphinx "
                    "de laiton, puis au pylône et à ses portes de laiton. Derrière la salle des offrandes, la salle "
                    "hypostyle de 5 × 5 colonnes à chapiteaux de lotus (lieu de grâce) ; dessous, les salles basses "
                    "envahies de sable : grenier, citerne sèche, salle des machines, sanctuaire du soleil enfoui et "
                    "un vestibule effondré. On monte par le quartier des prêtres-astronomes (réfectoire, dortoir, "
                    "salle des étoiles, scriptorium) et les escaliers des terrasses jusqu'à la chambre de calibrage "
                    "de la lentille, autour du tambour de verre du puits. La galerie des tombeaux scellés s'ouvre "
                    "par la brèche des pilleurs. L'annexe au dôme de cuivre descend à l'antichambre (lieu de "
                    "grâce) ; passé la brume, la chambre du soleil sous la lentille est l'arène du boss. Derrière "
                    "des barreaux scellés, le caveau, et un ascenseur à colonne de bulles qui redescend par le cœur "
                    "jusqu'aux salles basses. Raccourcis : portes de fer vers la rampe, les terrasses et la galerie "
                    "des tombeaux, et un escalier en colimaçon des salles basses à la salle hypostyle.",
    "drowned_dam": "Un barrage-voûte de pierre et de laiton long de 170 blocs et haut de 66 ferme un fer à cheval "
                   "de roche ; derrière lui, un lac a englouti un village dont le clocher perce encore la surface. "
                   "Depuis le camp des arpenteurs (pierre de passage), le chemin contourne un éperon rocheux jusqu'à "
                   "la cour des travaux. Par la salle des génératrices I, l'escalier à noyau de la tour ouest monte "
                   "à la risberme ; la maison des vannes et sa galerie noyée (fenêtres sur le village sous l'eau), "
                   "puis la tour de contrôle et sa salle des cadrans (lieu de grâce) au sommet. On suit le "
                   "couronnement jusqu'à la tour est, on redescend 66 marches jusqu'à la salle des génératrices II "
                   "(lieu de grâce) et la grande salle des turbines (arène), le caveau derrière des barreaux "
                   "scellés. Raccourcis : le puits d'ascenseur depuis le chevalement, le puits du déversoir, les "
                   "portes de fer à sens unique ; des échelles descendent la face amont pour nager jusqu'au village.",
    "kneeling_gate": "Deux chevaliers de pierre de 70 blocs agenouillés face à face de part et d'autre d'un col de "
                     "montagne, qui portent entre leurs gantelets un linteau de pierre et le pavillon doré de sa "
                     "clef de voûte. Sous le linteau, le bourg du péage : la place et son puits, la barrière, le "
                     "bureau du péage, l'auberge, la forge et l'écurie, une pierre de passage. Dans le socle de la "
                     "statue ouest, le corps de garde ; un escalier à noyau monte dans la cuisse jusqu'à la salle de "
                     "la ceinture, la chambre du cœur (fenêtres à travers la cuirasse), la gorgerette et la cellule "
                     "des guetteurs derrière les yeux du heaume. Par l'épaulière on sort sur le bras, on gravit "
                     "l'avant-bras jusqu'au gantelet et l'on traverse le linteau à 63 blocs de haut (lieu de grâce et "
                     "cloche du péage dans le pavillon). On redescend dans la statue est : le trésor du péage dans son "
                     "heaume, le puits de la chambre du cœur (raccourci à sens unique), son corps de garde dont la "
                     "porte de fer s'ouvre sur la place. De là, un second escalier descend à la chapelle des gardiens "
                     "(lieu de grâce) et, passé la brume, dans la salle sous la porte : l'arène du boss, sous la grille "
                     "du puits ; derrière des barreaux scellés, le caveau, et une porte de fer qui ramène au corps de "
                     "garde ouest.",
    "inverted_spire": "Une tour gothique bâtie à l'envers dans un gouffre de 110 blocs : en surface, on ne voit qu'un "
                      "anneau de pinacles autour d'un trou noir, quatre chaînes géantes et la flèche de cuivre de la "
                      "lanterne au milieu. Depuis le camp des pèlerins, la route mène à la porte du rebord ; un pont "
                      "file jusqu'à la cour de la couronne (pierre de passage). Une rampe en spirale descend autour de "
                      "la tour, six tours complets ; à chaque palier on traverse la salle en anneau autour du puits "
                      "de lumière : la bibliothèque du chapitre, le réfectoire (pont vers la carrière et son escalier "
                      "jusqu'au rebord, porte de fer à sens unique), la chapelle renversée (bancs au plafond, autel "
                      "suspendu ; pont vers l'ossuaire et son lieu de grâce), la crypte des racines (pont rompu), la "
                      "défaite (améthyste, murs qui se défont dans le vide, pont de cristal vers le reliquaire) et le "
                      "sanctuaire de la pointe. Un long couloir et un escalier taillé descendent au lac souterrain "
                      "(lieu de grâce) ; passé la brume, l'arène sur une île, sous la pointe de la flèche. Derrière, "
                      "le caveau aux barreaux scellés. Pour remonter : deux ascenseurs à bulles dans des tubes de "
                      "verre, de la grève à l'ossuaire et de la grève sud jusqu'au rebord.",
    "mesa_minecity": "Une ville-champignon de 200 blocs taillée dans une butte rayée des badlands, haute de 56 "
                     "blocs : au sommet, un chevalement de bois et de fer porte une roue de 19 blocs ; sur les trois "
                     "terrasses, des saloons à fausse façade, un dortoir, une forge et le bureau du télégraphe, "
                     "reliés par des escaliers taillés, des ponts sur tréteaux et des échelles ; une voie de "
                     "wagonnets s'enroule autour de la butte jusqu'au sommet. Depuis le relais de diligence et sa "
                     "pierre de passage, on suit la grand-rue et on grimpe jusqu'à la salle des treuils (lieu de "
                     "grâce). Dedans, on descend : le bocard et ses dix pilons, ses engrenages géants et son volant, "
                     "le niveau 15 (dépôt de dynamite, bureau du patron et son coffre-fort), le niveau de roulage "
                     "(lieu de grâce, galerie vers la sortie est), la galerie noyée sous une passerelle, le puits "
                     "effondré autour de la cage tombée et l'antichambre (lieu de grâce). Passé la brume, une "
                     "caverne de 42 blocs autour d'un filon colossal d'or et de cuivre à moitié exploité ; derrière "
                     "des barreaux scellés, la chambre forte et le monte-wagon à bulles qui remonte au niveau de "
                     "roulage.",
    "canopy_city": "Une cité perdue de 220 blocs dans la jungle : au centre, un temple de pierre à six degrés haut "
                   "de 66 blocs, étranglé par les racines ; autour, cinq troncs colossaux et creux, larges de 16 "
                   "blocs, portent des plates-formes sur trois hauteurs reliées par des ponts de corde et des "
                   "tyroliennes à poulies de laiton. Depuis le campement des explorateurs et sa pierre de passage, "
                   "on monte par les escaliers en spirale des troncs (logis, entrepôts, atelier de tissage) jusqu'au "
                   "marché (lieu de grâce) et au quartier haut, puis un pont mène à la terrasse supérieure du "
                   "temple. Dedans, on descend : la bibliothèque des glyphes, le couloir des fléchettes et ses "
                   "fosses à pointes, le sanctuaire de jade et d'or (lieu de grâce), la salle des offrandes et la "
                   "crypte envahie de racines, d'où un passage mène au fond du cénote noyé et à sa cascade ; un "
                   "tunnel immergé y cache une grotte. La corniche en spirale du cénote remonte au lieu de grâce "
                   "(porte de fer vers la bibliothèque) et à l'escalier du sommet : passé la brume, l'arène sous le "
                   "disque solaire de laiton brisé ; "
                   "derrière des barreaux scellés, le caveau. Une porte de fer à sens unique ouvre l'escalier de la "
                   "terrasse est et le pont du tronc est, dont l'ascenseur de laiton ramène au sol.",
    "echo_cathedral": "Une cathédrale gothique de deepslate et de laiton terni (110 × 82 × 165 blocs) dans une "
                      "immense caverne sous l'abîme profond et les grottes de spéléothèmes ; le sol de la nef est "
                      "vers y −43. On arrive par le camp des pèlerins (pierre de passage) et un tunnel jusqu'au "
                      "parvis des choristes de pierre. Le portail est barré : son guichet ne s'ouvre que de "
                      "l'intérieur, on entre par les loges des tours. Nef de colonnes de 7 × 7, chapelles "
                      "latérales (du Silence, des Diapasons, de l'Hymne noyé…), tribune et triforium par les "
                      "escaliers à vis, clocher et sa cloche de bronze fêlée, soufflerie de l'orgue, dortoir des "
                      "choristes et bibliothèque. Sous le chœur, la crypte inondée aux tombeaux envahis de sculk "
                      "(lieu de grâce). Passé la brume, l'arène devant la console du grand orgue, dont les tuyaux "
                      "montent de 60 blocs dans la voûte de la caverne ; derrière des barreaux scellés, le "
                      "reliquaire. L'ascenseur du puits d'orgue ramène de la crypte à la croisée (lieu de grâce). "
                      "Les capteurs de sculk ne sont qu'un décor : ni gardien ni hurleur.",
    "titan_forge": "Une forge colossale de 217 blocs sur un lac de lave du Nether (deltas de basalte, forêt carmin), bâtie dans et autour d'un titan de basalte et de laiton agenouillé, haut de 85 blocs, penché sur une enclume grande comme un donjon, le marteau levé. Depuis l'avant-poste des forgerons et sa pierre de passage, une chaussée de basalte et l'Arche du péage mènent au portail du socle, entre deux cascades de lave versées par des creusets dans des moules. Dans le socle : la halle de coulée et ses canaux de lave sous verre, les chambres des soufflets de cuir géants, le grand escalier jusqu'à la terrasse des creusets (pierre de passage). Dans le titan : une porte dans le genou, l'escalier en colimaçon de la cuisse, le casernement des forgerons, l'armurerie, la halle de fusion dans le dos sous les cheminées, le joug ; puis le bras gauche descend jusqu'à la salle du treuil (pierre de passage) et le pont-grue de l'avant-bras mène dans la main posée sur l'enclume. Passé la brume, l'arène sur la table de l'enclume, sous le marteau. Derrière des barreaux scellés, le caveau dans le talon de l'enclume. En option : la mine de scories et sa galerie cachée, la galerie des marteaux dans le bras levé, le nid du maître de forge dans le heaume. Pour revenir : l'ascenseur dans la colonne vertébrale du titan.",
    "soul_engine": "Une machine-ossuaire monstrueuse de 178 × 195 blocs au fond d'une vallée de sable des âmes du "
                   "Nether : un bloc moteur grand comme une cathédrale, de pierre noire, de terre des âmes et de "
                   "laiton terni, nourri par deux convoyeurs d'os, coiffé d'un carter où six pistons colossaux sont "
                   "figés à des hauteurs différentes, flanqué de quatre cheminées nervurées qui crachent une flamme "
                   "bleue, ses murs extérieurs dévorés par les champignons biscornus. Depuis le camp des pèlerins "
                   "perdus (pierre de passage), la route d'os passe sous l'arche en cage thoracique jusqu'à la porte "
                   "d'os et son guichet. Le couloir de la porte débouche dans la salle des pressions (pierre de "
                   "passage) et sa cuve géante ; au nord, la salle des trémies où les os tombent des convoyeurs, la "
                   "soute à terre des âmes, puis la fournaise des âmes et ses trois foyers ouverts sur la façade est. "
                   "Le grand escalier monte au balcon des chauffeurs : le réfectoire, la salle de contrôle du "
                   "gouverneur et son régulateur à boules, la salle des vannes, puis le puits de piston, un "
                   "escalier à noyau dans une chemise de cylindre désaffectée, jusqu'au lieu de grâce sur le carter. "
                   "Passé la brume, l'arène sur le pont du vilebrequin, au cœur du moteur, devant la tranchée des "
                   "bielles et le volant d'inertie. Derrière des barreaux scellés, le reliquaire des âmes. En "
                   "option : la galerie des pistons et sa passerelle, et sous le moteur l'ossuaire : la nef des "
                   "voûtes d'os, la fosse aux charniers et son trône d'os, la crypte des bâtisseurs, dont l'escalier "
                   "remonte dans la galerie. Pour revenir : l'ascenseur à piston du lieu de grâce, la goulotte d'os "
                   "du reliquaire et la porte de la fournaise, qui ne s'ouvre que d'un côté.",
    "mire_stilt_city": "Une ville de bois sur pilotis de 200 blocs au-dessus d'une mangrove : des passerelles sur trois "
                       "niveaux, des ponts de corde et des huttes de pêcheurs. On arrive par une chaussée depuis un "
                       "îlot (pierre de passage), on franchit la palissade et ses deux tours de garde (brisée à "
                       "l'ouest : le chemin de traverse), puis le marché aux anguilles et les ruelles basses mènent à "
                       "la maison de l'escalier. Au deuxième niveau, la place du marché autour de l'arbre (lieu de "
                       "grâce) ; un pont de corde mène à l'ouest au clocher noyé (escalier vers le beffroi et vers la "
                       "crypte engloutie, son trésor caché et un tunnel qui ressort dans une hutte par une porte de "
                       "fer), un autre à l'est au fumoir, sa salle des foyers et son escalier jusqu'à la galerie. Le "
                       "chemin haut fait le tour par l'est et le nord jusqu'au palier (lieu de grâce) et au grand "
                       "escalier couvert ; passé la brume, la grande salle ronde de la reine-sorcière, haute de 34 "
                       "blocs sur sa forêt de pilotis, sous un toit en chapeau de sorcière tordu qui culmine à 100 "
                       "blocs. Derrière le trône, le caveau scellé et une trappe qui plonge de 33 blocs dans le "
                       "bassin de la reine. Raccourcis : la porte de fer de la crypte, le monte-charge en "
                       "échafaudage, l'échelle de la place au palier, la trappe du caveau.",
    "tidal_abbey": "Une île rocheuse cernée par la marée, reliée au rivage par une chaussée de pierre à demi noyée "
                   "et rompue en son milieu. Au pied, les remparts à tours, la barbacane et la porte du Roi ; puis la "
                   "Grande Rue monte en spirale autour du rocher entre des maisons de pierre aux toits d'ardoise, sous "
                   "des arches, par des lacets, des escaliers, la place du puits et le parvis de l'église paroissiale, "
                   "jusqu'au Châtelet et au Grand Degré. Au sommet, l'abbatiale gothique (nef de 27 blocs) et sa flèche "
                   "dont la pointe dorée culmine à 130 blocs ; à l'ouest, la Merveille : l'aumônerie, la salle des "
                   "chevaliers et le cloître suspendu, dont le puits cache un reliquaire. Sous le rocher, la crypte "
                   "(lieu de grâce) mène à la salle des marées, l'arène du boss éclairée par la mer à travers des "
                   "grilles, puis au caveau du trésor et au tunnel qui ressort au port.",
    "airship_graveyard": "Un champ d'épaves de 228 blocs dans la savane ou la plaine, autour d'un mât d'amarrage "
                         "squelettique haut de 90 blocs : un dirigeable y est encore amarré, son enveloppe à demi "
                         "dégonflée drapée sur les membrures ; autour, une nacelle plantée le nez dans la terre, la "
                         "carcasse d'une enveloppe qu'on traverse comme un squelette de baleine, un navire brisé en "
                         "deux et le bidonville des ferrailleurs (tôles de coque, tentes en ballonnets, hélices). "
                         "Depuis le camp (pierre de passage), le marché des ferrailleurs (pierre de passage), la salle "
                         "du treuil au pied du mât et l'usine à gaz et ses gazomètres ; l'escalier du mât monte à "
                         "l'anneau d'amarrage, d'où la passerelle entre dans le nez du dirigeable. Dans la nacelle : "
                         "la passerelle de commandement, les cabines, la cale, et les nacelles moteurs par les "
                         "coursives ; on remonte par la quille jusqu'au lieu de grâce. Passé la brume, l'arène sur "
                         "le pont supérieur ; derrière des barreaux scellés, la soute au trésor. L'ascenseur à "
                         "marchandises du mât ramène à la salle du treuil.",
    "cloud_pagoda": "Un temple de 130 × 180 blocs dans un bosquet de cerisiers ou une prairie de montagne : une "
                    "pagode à neuf toits de cerisier, de plâtre blanc et d'ardoise bleue (le fleuron est à 148 "
                    "blocs du sol), ornée de laiton et de carillons mécaniques, sur trois terrasses de jardin. Le "
                    "squelette de laiton d'un dragon mécanique s'enroule autour des étages inférieurs. On arrive "
                    "par le camp des pèlerins (pierre de passage), la porte de lune et le pont en zigzag de "
                    "l'étang aux carpes ; sur les terrasses : le pavillon de la cloche, le sanctuaire du dragon "
                    "(lieu de grâce) devant son crâne, le dojo des moines, la maison de thé et, cachée derrière "
                    "les bambous, la grotte de l'ermite. Dans la pagode, un étage par salle : salle de prière, "
                    "bibliothèque des rouleaux, armurerie d'entraînement, salle de méditation au jardin de sable "
                    "(lieu de grâce), orrery mécanique des saisons, appartements de l'abbé, moteur des carillons "
                    "et la dernière salle (lieu de grâce). Passé la brume, l'arène sur le toit ouvert sous la "
                    "flèche ; derrière des barreaux scellés, le caveau, d'où le puits du contrepoids ramène à "
                    "la salle de prière.",
    "icebound_fleet": "Une expédition polaire de 220 × 200 blocs prise dans la banquise, sur une mer gelée, une "
                      "plaine enneigée ou parmi les pics de glace : un brise-glace colossal à roues à aubes, coque "
                      "de fer sombre longue de 120 blocs, gîtant sur tribord, ses deux cheminées de cuivre penchées "
                      "et son étrave en éperon montée sur une crête de pression ; à côté, deux petits navires "
                      "ravitailleurs en bois, un derrick de forage en laiton, des aiguilles de glace bleue et le "
                      "squelette d'une baleine pris dans la glace. On arrive par le camp des traîneaux (pierre de "
                      "passage), sous l'échine de la baleine, jusqu'au camp de forage (pierre de passage) ; sur le "
                      "Fulmar : la cale gelée sous la glace et la salle des cartes, puis le pont de cordes vers le "
                      "Pétrel : chenil, cuisine (pierre de passage) et la porte de glace qui ne s'ouvre que de "
                      "l'intérieur, sur la tranchée de neige. Elle mène à la brèche de la soute à charbon du "
                      "brise-glace : salle des chaudières haute de 27 blocs, carré de l'équipage (pierre de "
                      "passage), carré des officiers, cabine du capitaine ; puis l'escalier en colimaçon dans la "
                      "cheminée avant, la passerelle et la timonerie (lieu de grâce). Passé la brume, l'arène sur "
                      "le gaillard d'avant, sous la passerelle ; derrière des barreaux scellés, la chambre forte de "
                      "l'expédition, d'où la glissade de glace ramène au camp de forage. Raccourcis : l'écoutille "
                      "à sens unique du carré vers le pont latéral, la porte de glace du Pétrel et la flèche de la "
                      "grue de chargement, qui plonge dans un trou de pêche près de la tranchée.",
    "clockwork_asylum": "Un sanatorium gothique de 185 blocs au sommet d'une colline de forêt sombre ou de jardin "
                        "pâle, devenu atelier d'automates : une tour de l'horloge haute de 100 blocs aux quatre "
                        "cadrans fêlés, deux longues ailes de salles aux fenêtres grillagées, une chapelle, une serre "
                        "brisée et un cimetière clos aux grilles de fer tordues. On arrive par le camp des bûcherons "
                        "(pierre de passage), le funiculaire de la conciergerie et le cimetière jusqu'au grand hall "
                        "(pierre de passage). Dans les ailes : les cellules, l'amphithéâtre opératoire aux bras "
                        "chirurgicaux de laiton, les bains d'hydrothérapie, la salle des archives, la buanderie ; en "
                        "option la chapelle et la serre. Le mécanisme de l'horloge (engrenages, puits du balancier) "
                        "mène au lieu de grâce ; passé la brume, l'arène dans la chambre de l'horloge derrière le "
                        "cadran fêlé ; derrière des barreaux scellés, le bureau du directeur. Raccourcis : le "
                        "funiculaire, la goulotte de la buanderie vers le sous-sol, la porte à sens unique de la "
                        "chapelle.",
    "verdant_arboretum": "Un complexe de recherche botanique de 155 × 185 blocs au fond d'une immense grotte "
                         "luxuriante, 40 à 60 blocs sous la surface : une serre-palmarium de laiton et de verre "
                         "dont la coupole de 50 blocs soutient la voûte de ses nervures, éclairée de baies "
                         "lumineuses et de fleurs à spores, une cascade artificielle qui nourrit un lac de "
                         "nénuphars et d'îlots de grandes feuilles tombantes, des serres en terrasses, des "
                         "aqueducs d'irrigation et une lampe-soleil mécanique suspendue à la voûte. On arrive par "
                         "le camp des botanistes dans un tunnel latéral (pierre de passage), puis la station du "
                         "rivage (pierre de passage) ; de là : les serres de multiplication, la grainothèque, le "
                         "laboratoire des spécimens et ses bocaux, la salle des pompes et son balancier, le "
                         "labyrinthe d'azalées. On monte par les passerelles des nervures jusqu'à la corniche de "
                         "la coupole (lieu de grâce) ; passé la brume, l'arène sur l'île-nénuphar sous la "
                         "lampe-soleil ; derrière des barreaux scellés, le coffre de l'herbier. Raccourcis : la "
                         "chute par les grandes feuilles dans le lac, l'ascenseur à eau de la salle des pompes, "
                         "la porte de serre qui ne s'ouvre que de l'intérieur.",
    "abyssal_station": "Une station de recherche de 180 blocs au fond d'un océan profond : des dômes pressurisés de "
                       "laiton et de verre (le grand dôme fait 40 blocs de large) reliés par des tubes de verre, une "
                       "tour d'accès qui crève la surface avec un quai et une grue à bathyscaphe, une plate-forme de "
                       "forage au-dessus d'une fosse, des champs de varech, des projecteurs et le pont d'observation "
                       "d'une carcasse de baleine. Chaque salle est une poche d'air scellée. On arrive par le camp de "
                       "la tour (pierre de passage), on descend le puits d'accès jusqu'au sas d'accueil (pierre de "
                       "passage) ; de là : le grand dôme et son puits de lumière, l'hydroponie, la halle des "
                       "spécimens aux parois de verre, les quartiers de l'équipage, le réacteur à chaudières et la "
                       "salle de contrôle du forage. Le puits de forage descend dans la fosse (lieu de grâce) ; "
                       "passé la brume, l'arène au fond de la fosse ; derrière des barreaux scellés, le coffre des "
                       "spécimens. Raccourcis : l'ascenseur à colonne de bulles, le tube de maintenance noyé (un "
                       "conduit l'éclaire) et l'écoutille de pression qui ne s'ouvre que d'un côté.",
    "timber_fortress": "Un fort de bûcherons à vapeur de 200 blocs dans une boucle de rivière de la taïga : une "
                       "palissade de troncs d'épicéa et ses tours, une scierie à vapeur avec sa roue à aubes et ses "
                       "cheminées, un flottage à bois sur tréteaux qui descend d'une colline aux arbres géants "
                       "abattus, des fours à charbon, une voie ferrée sur pilotis et sa locomotive, et un donjon de "
                       "bois haut de 70 blocs aux étages en encorbellement et aux toits en bardeaux, une machine à "
                       "balancier de laiton à son sommet. On arrive par le camp des trappeurs (pierre de passage) "
                       "et la porterie jusqu'au parc à bois (pierre de passage) ; de là : la scierie, la tête du "
                       "flottage, le réfectoire, la loge du contremaître et les fours ; puis les étages du donjon : "
                       "l'armurerie, la grande salle aux lustres de bois de cerf, la salle des cartes (lieu de "
                       "grâce). Passé la brume, l'arène au sommet du donjon autour de la machine ; derrière des "
                       "barreaux scellés, la chambre forte de la guilde. Raccourcis : la descente du flottage, "
                       "l'ascenseur à contrepoids et la poterne qui ne s'ouvre que d'un côté.",
    "spore_refinery": "Une raffinerie d'alchimistes de 180 blocs sur une île de mycélium (ou, à défaut, dans une "
                      "vieille taïga), poussée dans et autour de trois champignons colossaux : une amanite rouge "
                      "haute de 90 blocs au chapeau large de 68, un bolet brun au chapeau plat et une petite "
                      "amanite, leurs pieds creusés en tours à escalier, cerclés de laiton et enroulés de tuyaux "
                      "de cuivre et de cuves à spores. On arrive par le camp des cueilleurs (pierre de passage) et "
                      "la porte aux tuyaux jusqu'à la cour des presses (pierre de passage) ; de là : la halle des "
                      "presses à vis géantes, la halle de fermentation et ses cuves, l'escalier du bolet jusqu'aux "
                      "séchoirs sous le chapeau brun (lieu de grâce), puis le pont de corde vers la grande amanite. "
                      "En option : la distillerie et ses colonnes, le laboratoire des alchimistes sous la petite "
                      "amanite et sa passerelle, les caves à spores sous les racines. On monte le pied de "
                      "l'amanite jusqu'à la chambre des lamelles (lieu de grâce) ; passé la brume, l'arène au "
                      "sommet du chapeau ; derrière des barreaux scellés, le coffre des spores raffinées. "
                      "Raccourcis : l'ascenseur du chapeau (un puits jusqu'au pied, porte de fer qui ne s'ouvre "
                      "que de l'intérieur), la goulotte à spores des séchoirs et la porte à sens unique des caves.",
    "starfall_library": "Une archive flottante de 170 blocs sur les îles extérieures de l'End : une tour-fuseau de "
                        "purpur et de laiton haute de 125 blocs, coiffée d'un dôme d'astrolabe, entourée de trois "
                        "galeries de lecture en anneau suspendues à trois hauteurs par des rayons de chaînes et de "
                        "barres de l'End. Une météorite tombée s'est fichée dans son flanc et a fendu les "
                        "rayonnages. Depuis l'îlot d'arrivée, un pont mène à la grande porte : la salle des cartes et "
                        "sa carte du ciel au sol, puis les canyons de rayonnages (pierre de passage), avec échelles "
                        "roulantes et passerelles, l'escalier mural jusqu'au scriptorium des copistes, la terrasse, "
                        "la grande salle à l'armillaire (pierre de passage) et l'observatoire à lentille sous le dôme. "
                        "Une rampe redescend vers les galeries ; la galerie brisée se traverse sur des livres ouverts "
                        "flottants (un bassin de laiton rattrape les chutes) jusqu'au dos de la météorite. Un escalier "
                        "en vrille descend dans la roche jusqu'au lieu de grâce, puis à l'arène dans la chambre du "
                        "cratère. Derrière des barreaux scellés, la réserve interdite ; son tube pneumatique remonte "
                        "à la salle des cartes.",
    "hollow_moon": "Une lune mécanique de 140 blocs écrasée sur une île extérieure de l'End : une sphère de pierre "
                   "de l'End, de purpur et de plaques de laiton terni, dont un tiers a volé en éclats et révèle "
                   "une coque intérieure en cage et trois anneaux d'orrery figés autour d'un noyau lumineux. Des "
                   "chaînes l'amarrent à l'île, un cratère d'épaves de laiton l'entoure, des arcs de débris et "
                   "des éclats flottent autour. Depuis le camp des astronomes sur un éclat (pierre de passage), "
                   "un pont entre par la brèche dans les galeries de la coque : la salle du méridien et son "
                   "pendule (pierre de passage), les jardins de gravité (chorus dans des jardinières de laiton), "
                   "la crypte des engrenages, le dôme des cartes du ciel et l'atelier des lentilles. Le grand "
                   "escalier monte au pont supérieur ; on franchit les anneaux par des passerelles jusqu'à la "
                   "station du cardan (pierre de passage) puis au lieu de grâce ; passé la brume, l'arène sur la "
                   "plateforme du noyau. Derrière des barreaux scellés, le reliquaire du noyau. Raccourcis : le "
                   "puits d'eau du reliquaire jusqu'au puisard, l'ascenseur à colonne de bulles de la crypte "
                   "vers la salle du méridien, la porte à sens unique de l'anneau et le saut vers la brèche.",
    "shattered_halo": "Un anneau colossal de purpur, de briques de pierre de l'End et d'or, large de 170 blocs et "
                      "incliné au-dessus du vide de l'End, brisé en cinq arcs qui flottent chacun à sa hauteur. On "
                      "arrive sur un îlot extérieur (pierre de passage), puis les ponts imposent l'ordre : "
                      "l'Observatoire et son télescope géant, un pont de lumière jusqu'à la Bibliothèque du vide et "
                      "son puits ouvert sur le néant, des îlots-gués jusqu'au Reliquaire (une trappe y cache une "
                      "crypte), un pont en arc jusqu'au Sanctuaire des cloches sous son aiguille dorée, un dernier pont "
                      "de lumière jusqu'à la Porte. De là, un pont rayonnant mène à l'îlot du lieu de grâce, puis "
                      "à l'arène : un disque flottant au centre de l'anneau, ouvert sur le vide, cerné d'éclats d'un "
                      "plus petit halo. La salle du trésor est au-delà.",
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
    "iron_helmsman": "Champion de la Forteresse marchante : le pilote du marcheur, un capitaine colossal de 5 blocs "
                     "soudé à un harnais à vapeur. Chaudière fumante sur le dos, canon-harpon au bras droit, ancre "
                     "de navire traînée au bout d'une chaîne, heaume à visière fendue d'ambre. Le boss le plus dur "
                     "de la Surface.",
    "bronze_sentinel": "Champion du Colosse abattu : le gardien vivant de la statue, un chevalier-automate de 5,6 "
                       "blocs, pierre sous plates de bronze vert-de-gris, mousse dans les jointures. Son heaume à "
                       "visière en croix, brisé à un coin, luit d'or de l'intérieur ; il porte un pavois plus grand "
                       "qu'un homme et un long espadon.",
    "dune_king": "Champion de la Nécropole des rois : un pharaon mort-vivant de 4,6 blocs sous la haute double "
                 "couronne, bandelettes dorées, collier de lapis et d'or, la crosse et le fléau en main. Quatre vases "
                 "canopes tournent autour de lui et ses yeux brûlent de turquoise.",
    "fallen_seraph": "Champion du Halo brisé : une séraphine déchue de 5,4 blocs qui flotte sans pieds au-dessus du "
                     "disque, un grand halo d'or brisé derrière la tête, une aile blanche et dorée, l'autre brûlée par "
                     "le vide. Un bandeau d'or sur les yeux, un glaive dont la lame est un croissant de halo, et six "
                     "éclats de halo qui tournent autour d'elle. Le boss le plus dur de l'End.",
    "chained_jailer": "Champion du Bastion enchaîné : le geôlier de la prison suspendue, un colosse voûté de 5,4 blocs "
                      "en pierre noire et fer doré. Sa tête est une cage verrouillée pleine de feu, son cœur un grand "
                      "cadenas à la serrure ardente ; un gibet se dresse sur son dos, il traîne un boulet de fers "
                      "enflammé au bout d'une chaîne et porte un gantelet entravé. Le boss le plus dur du Nether.",
    "oathbound_gatekeeper": "Champion de la Porte agenouillée : l'une des deux statues du col descendue à taille de "
                            "combat, un chevalier de calcaire pâle de 6 blocs au manteau de granit rouge, heaume ouvert "
                            "et barbe tressée de pierre, les yeux pleins d'une lumière d'âme. Un pavois gravé de la clé "
                            "d'or du péage, un espadon de pierre, et la grande clé de la porte au bout d'une chaîne.",
    "caldera_castellan": "Champion du Rempart de la caldeira : le seigneur du château, un géant de 5,7 blocs en armure "
                         "de basalte fendue de magma qui refroidit. Une couronne de pointes d'obsidienne autour d'un "
                         "petit cratère ardent sur le heaume, un volcan fumant pour épaulière droite, un long manteau "
                         "rouge cendre et une grande hallebarde à lame d'obsidienne. Le boss le plus dur de la Surface.",
    "frost_jarl": "Champion de la Halle glaciaire des jarls : le roi mort, un géant nordique de 5,7 blocs gelé debout. "
                  "Peau bleuie de givre, casque à nasal couronné de pics de glace (une corne entière, l'autre brisée), "
                  "barbe de frimas qui s'ouvre pour son souffle, peau de loup sur les épaules. Une hache barbue de glace "
                  "bleue dans la main droite, un bouclier rond givré au bras gauche, des cristaux de glace qui lui "
                  "poussent dans le dos.",
    "tide_abbess": "Championne de l'Abbaye des marées : l'abbesse noyée, une sainte de 5,4 blocs revenue de la mer. "
                   "Robe de lin sombre jusqu'au sol, chasuble cramoisie couverte de bernacles, voile couronné de corail, "
                   "visage gris-vert aux yeux de verre marin. Une crosse dont la volute est un nautile dans la main "
                   "droite, un encensoir-cloche au bout d'une chaîne dans la gauche.",
    "lock_master": "Champion du Grand Aqueduc : le gardien de la grande citerne, un colosse hydraulique de 5,2 blocs "
                   "en laiton riveté, verdi par l'eau. Un casque de scaphandre à hublot lumineux couronné d'un volant "
                   "de vanne, deux réservoirs de cuivre dans le dos, une vanne d'écluse entière au bras gauche pour "
                   "bouclier et une lance à pression plus longue que lui dans la droite.",
    "bog_hierophant": "Champion de la Cité des pilotis : un évêque pourrissant de 5,9 blocs, perché sur deux jambes "
                      "d'échassier liées de racines de palétuvier, comme les pilotis de sa ville. Un manteau de mousse "
                      "vivante, une mitre de lin moisi de travers, un visage de tourbe aux yeux de feu follet, une barbe "
                      "de mousse. Une crosse de palétuvier noir dont la volute porte une lanterne de feu des marais dans "
                      "la main droite, un bras d'os griffu dans la gauche, et un nuage de mouches des marais autour de "
                      "la tête.",
    "star_curator": "Champion de la Bibliothèque de la chute d'étoile : le Conservateur dévoreur d'étoiles, un érudit "
                    "de 5,6 blocs en longue robe d'indigo bordée de laiton, brodée de constellations lumineuses, sous "
                    "une pèlerine raide et un haut col. À la place de la tête, la météorite qui a ruiné sa "
                    "bibliothèque : une roche calcinée fendue sur un ciel étoilé, deux étoiles pour yeux, un éclat qui "
                    "flotte à côté. Cinq livres tournent autour de lui ; un bâton-astrolabe dans la main droite, la "
                    "gauche levée paume ouverte.",
    "chime_abbot": "Champion de la Pagode des nuages : l'Abbé des carillons, un vieux moine d'environ 3 blocs à moitié "
                   "changé en mécanique, qui flotte un peu au-dessus du sol. Des robes superposées rouge cerise et "
                   "blanches, un kasaya bordé d'or, un grand chapelet de perles de laiton, un crâne chauve dont la "
                   "moitié droite est une plaque de laiton à l'œil d'ambre, de longs sourcils et une barbe blanche. "
                   "Derrière sa tête, un halo de laiton d'où pendent des tiges de carillon ; dans sa main droite un "
                   "bâton de bronze à tête de dragon, sous ses manches des bras mécaniques.",
    "mine_baron": "Champion de la Ville minière de la Mesa rouille : le Baron de la mine, un contremaître énorme et "
                  "avide de 5,6 blocs sanglé dans un exosquelette à vapeur riveté, chaudière fumante sur le dos. Un "
                  "bras-foreuse pneumatique à droite, un pic-marteau à gauche, un casque de mineur à lanterne, un "
                  "gilet à chaîne de montre tendu sur la bedaine. Blessé, il se cuirasse de minerai d'or.",
    "corsair_captain": "Championne du Cimetière des dirigeables : la Capitaine corsaire, une pirate du ciel de 4,8 "
                       "blocs en longue redingote sarcelle à deux rangées de boutons de laiton, épaulettes d'or et "
                       "basques jusqu'aux bottes. Un tricorne de cuir noir bordé de laiton, des lunettes d'aviatrice "
                       "aux verres bleu ciel, une longue tresse rousse et une écharpe rouge au vent ; sur le dos, un "
                       "moteur à rotor dont le mât porte une hélice à quatre pales au-dessus du chapeau. Un sabre "
                       "d'abordage dans la main droite, un lourd fusil-harpon à barillet dans la gauche.",
    "hollow_cantor": "Champion de la Cathédrale de l'Écho : le Chantre creux, un maître de chœur décharné de 3,5 "
                     "blocs, de laiton terni et de deepslate. Sa cage thoracique est un buffet d'orgue où luisent "
                     "sept petits tuyaux, un éventail de tuyaux d'orgue s'ouvre derrière sa capuche vide et sans "
                     "visage, et il dirige d'une longue baguette terminée par un diapason. Le son contre le silence.",
    "soul_stoker": "Champion du Moteur des âmes : le Chauffeur des âmes, un homme-fourneau massif d'environ 4 blocs. "
                   "Son torse est une chaudière de blackstone cerclée de laiton, au ventre une gueule de foyer grillagée "
                   "où brûle un feu d'âmes bleu, un manomètre sur la poitrine ; sa tête, une porte de four au visage de "
                   "crâne dont les orbites brûlent en bleu ; deux cheminées dans le dos crachent des flammes bleues. "
                   "Le bras droit finit en pelle à charbon géante, le gauche en poing monté sur piston ; à sa ceinture "
                   "pendent des chaînes d'os et des lanternes d'âmes.",
    "asylum_director": "Championne de l'Asile mécanique : la Directrice de l'asile, une chirurgienne grande et "
                       "maigre d'environ 3,6 blocs, en longue blouse blanche tachée. Un masque de médecin de peste en "
                       "laiton au long bec et aux verres verts lumineux cache son visage, sous un calot blanc et un "
                       "miroir frontal ; derrière une plaque de verre, un cœur mécanique bat dans sa poitrine ; quatre "
                       "bras chirurgicaux de laiton (scalpel, scie à os, seringue, pince) se déploient dans son dos "
                       "comme des pattes d'araignée, et une montre de gousset pend de sa main gauche. Le temps et le "
                       "scalpel.",
    "spore_alchemist": "Champion de la Raffinerie de spores : l'Alchimiste des spores, un alchimiste voûté de 3,5 "
                       "blocs à moitié dévoré par le champignon qu'il raffinait. Un tablier de cuir sur une blouse "
                       "prune, un masque respiratoire de laiton aux verres d'un vert luisant, une bosse qui est une "
                       "amanite tue-mouches poussée dans son dos, des fils de mycélium qui pendent de ses manches et des "
                       "polypores sur ses épaules. Dans son dos, une cuve à spores de laiton dont les tuyaux nourrissent "
                       "le pistolet à buse de sa main gauche ; dans la droite, un long bâton-mélangeur coiffé d'une fiole.",
    "lumber_jarl": "Champion de la Forteresse du bois : le Jarl du bois, un bûcheron seigneur de guerre géant de 4 "
                   "blocs. Un casque cornu de fer sous un bord de fourrure, un nasal, une grande barbe rousse aux "
                   "tresses cerclées de fer ; une chemise à carreaux rouges et noirs sous un camail de mailles et un "
                   "col de fourrure sur un torse en tonneau, des bottes ferrées ; dans les deux mains une "
                   "hache-tronçonneuse à vapeur (un petit moteur fumant, une barre d'acier à chaîne dentée, une lame "
                   "barbue), et sur le dos un porte-bûches chargé de deux troncs et de lames de scie de rechange.",
    "thorn_gardener": "Champion de l'Arboretum englouti : le Jardinier en chef, un grand automate jardinier de laiton "
                      "de 3,8 blocs que le jardin a envahi. Un corps de cuivre riveté d'où la mousse et le lierre "
                      "débordent par chaque jointure, une cloche de verre pour tête où pousse une fleur lumineuse, de "
                      "très longs bras terminés en sécateurs, un arrosoir changé en canon sur le dos avec son tuyau, et "
                      "des racines qui traînent derrière ses bottes-pots de fleurs.",
    "abyss_diver": "Champion de la Station abyssale : le Scaphandrier des abysses, le chef plongeur de la station "
                   "soudé à son scaphandre, une masse de laiton de 3,8 blocs. Un énorme casque rond dont le hublot luit "
                   "d'un turquoise bioluminescent, un plastron riveté lesté de plomb sur une toile rapiécée et blanchie "
                   "de sel, deux bouteilles de cuivre dans le dos d'où serpentent les tuyaux d'air. Le bras droit est "
                   "une foreuse géante, la main gauche tient un pistolet à rivets armé d'un harpon ; bottes de plomb, "
                   "bernacles et varech accrochés partout.",
    "moon_warden": "Championne de la Lune creuse : la Gardienne de la lune, un automate céleste élégant de 3,6 "
                   "blocs qui lévite sur des propulseurs. Un corps svelte de porcelaine et d'or, un visage qui est un "
                   "cadran des phases de la lune, un halo de petites planètes de laiton en orbite, de longs bras "
                   "terminés en lames-astrolabes et une cape de pourpre et de ciel étoilé.",
    "frost_commodore": "Champion de la Flotte prise dans les glaces : le Commodore gelé, le chef de l'expédition, "
                       "mort mais maintenu debout par un appareil de survie en laiton couvert de givre. Une silhouette "
                       "massive de 3,8 blocs en capote doublée de fourrure croûtée de glace, une barbe gelée, une "
                       "capuche de fer en cloche de scaphandre dont la visière fêlée et givrée luit d'un bleu pâle, "
                       "une chaudière dans le dos qui crache une vapeur froide. Dans sa main droite, une ancre prise "
                       "dans la glace au bout de sa chaîne ; dans la gauche, un pistolet de signalisation.",
    "strangler_queen": "Championne de la Cité-temple de la canopée : la Reine-figuier étrangleur, une femme immense "
                       "de 5,8 blocs tissée de racines aériennes et de jade, qui a étouffé le temple et s'est couronnée "
                       "à sa place. Une jupe de racines-contreforts qui s'étalent sur le sol, un masque de jade aux "
                       "yeux d'or, une chevelure de racines pâles et une couronne de broméliacées et d'orchidées "
                       "lumineuses. Le bras gauche est un fouet de racine épineux plus long qu'elle, la main droite "
                       "tient un macuahuitl de jade aux dents d'obsidienne.",
    "solar_hierarch": "Champion de la Ziggourat du Moteur solaire : le dernier prêtre du midi, un grand automate "
                      "doré de 5,8 blocs. Un némès rayé d'or et de lapis, un masque d'or aux yeux d'ambre, une robe de "
                      "lin plissée sous un tablier d'or frappé du soleil ; dans le dos, un halo-disque de laiton à "
                      "douze rayons où tournent trois petites planètes. Un bâton solaire à l'orbe d'ambre dans la main "
                      "droite et un bouclier-miroir d'argent poli au bras gauche.",
    "drowned_admiral": "Champion de l'Épave du cuirassé Léviathan : le dernier amiral du navire, un officier de marine "
                       "de 5,9 blocs revenu du fond. Une redingote bleu marine gorgée d'eau à revers cramoisis, des "
                       "épaulettes d'or qui dégouttent, des bottes de scaphandre à semelles de plomb ; à la place de la "
                       "tête, un casque de scaphandre de laiton au hublot vert d'eau, coiffé d'un bicorne détrempé. Un "
                       "sabre d'abordage à garde-panier dans la main droite, et pour avant-bras gauche un canon de pont, "
                       "un grappin d'abordage enroulé dessous. Des bernacles et du varech partout.",
    "fourth_king": "Champion de la Nécropole des rois : le Quatrième Roi, celui dont on a ciselé le visage sur la "
                   "façade, relevé en monarque momifié décharné de 6 blocs. Un masque de grès et de lapis fendu, "
                   "la moitié droite creusée au ciseau avec un œil bleu qui brûle au fond, une couronne blanche "
                   "brisée, un collier d'or et de lapis, un fléau à trois chaînes dans la main droite et un sceptre "
                   "au scarabée surmonté d'un disque solaire dans la gauche.",
    "colossus_heart": "Champion du Colosse abattu : le Cœur du Colosse, un cœur-moteur de laiton qui bat encore "
                      "dans le heaume et qui anime un chevalier de 6 blocs fait de plaques de bronze et de gravats "
                      "tenus ensemble par des attaches d'ambre. Un espadon à la longue allonge, une plaque-bouclier "
                      "qu'il lance comme un boomerang, un heaume qui flotte au-dessus des épaules ; à 65 % l'armure "
                      "vole en éclats et tourne autour du cœur à nu.",
    "turbine_tyrant": "Champion du Barrage de la vallée engloutie : l'ingénieur du barrage, soudé à la turbine qu'il "
                      "n'a pas voulu quitter quand la vallée fut noyée. Une volute de fonte et de laiton de 5,7 blocs "
                      "sur deux jambes hydrauliques, l'ouïe de la turbine qui rougeoie dans son ventre, deux cheminées "
                      "dans le dos ; un rotor à quatre pales pour bras droit, une clé à vanne grande comme un homme dans "
                      "le poing gauche, une casquette et des lunettes ambrées.",
    "anvil_warden": "Champion de la Forge du Titan de basalte : le forgeron pour qui la forge fut bâtie, un golem "
                    "voûté de 5,6 blocs en basalte prismatique dont chaque joint rougeoie de la chaleur du four. Pour "
                    "tête, un creuset de graphite cerclé de laiton qui déborde de métal en fusion, une fente "
                    "lumineuse pour visière ; un marteau de forge à la face chauffée à blanc dans la main droite, une "
                    "longue pince tenant un lingot ardent dans la gauche, un tablier de cuir roussi, un seau de trempe "
                    "à la hanche et trois colonnes de basalte en fusion qui lui sortent de l'omoplate.",
    "storm_ascetic": "Champion de l'Ascension du pèlerin : l'ermite du sommet, un vieux moine décharné de 4,7 blocs "
                     "penché sur un bâton plus grand que lui, coiffé d'un anneau de bronze à grelots qui crépite "
                     "d'éclairs. Un grand chapeau de paille dans le dos, neuf grains de chapelet qui tournent autour de "
                     "sa poitrine, l'épaule droite nue et marquée d'une cicatrice de foudre, la robe safran jetée sur "
                     "l'épaule gauche, une longue barbe blanche soufflée par le vent.",
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
    "iron_helmsman": [
        ("Balayage d'ancre", "1 et 2", "Il ramène l'ancre loin sur sa gauche pendant 1 s, puis la balance sur 210° "
                                       "devant lui (17 dégâts, portée 7 blocs). Recule hors de l'arc ou passe dans "
                                       "son dos. En phase 2, il enchaîne souvent sur l'ancre abattue."),
        ("Ancre abattue", "1 et 2", "Il soulève l'ancre au-dessus de sa tête (1,1 s) et l'abat 4 blocs devant lui "
                                    "(22) ; une onde de choc roule ensuite vers l'extérieur (10) : saute-la. En "
                                    "phase 2, une seconde onde de feu suit, puis parfois le harpon."),
        ("Harpon", "1 et 2", "Il lève son bras-canon et vise (une ligne d'étincelles au sol montre le tir, 0,8 s), "
                             "puis tire jusqu'à 18 blocs. Touché : 10 dégâts et tu es ramené à 3 blocs de lui, juste "
                             "à portée du balayage qui suit. Écarte-toi de la ligne."),
        ("Purge de vapeur", "1 et 2", "Il se voûte, sa chaudière enfle et siffle 1,2 s pendant qu'un cercle de "
                                      "vapeur de 6 blocs se dessine : la vapeur brûlante jaillit (12 dégâts, en feu) "
                                      "et reste une demi-seconde. Ne reste pas collé à lui."),
        ("Charge", "1 et 2", "Épaule baissée derrière sa spalière (une ligne de fumée montre le trajet, 0,8 s), il "
                             "fonce sur 12 à 15 blocs (16). Pas de côté. En phase 2, souvent suivie d'un balayage."),
        ("Surchauffe", "2", "Sa chaudière rougeoie 1,2 s, puis quatre anneaux de jets de feu sortent du pont l'un "
                            "après l'autre en s'éloignant de lui (14 chacun, en feu). Chaque jet est annoncé par de "
                            "la fumée : passe entre eux ou recule vite."),
        ("Moulinet d'ancre", "2", "Il déroule la chaîne et fait tournoyer l'ancre autour de lui pendant 2 s en "
                                  "marchant sur toi (10 par coup, rayon 5,5). Recule et frappe quand il s'arrête."),
        ("Bordée", "2", "Il lève son canon vers le ciel et sonne la corne : les canons du marcheur tirent trois "
                        "salves d'obus sur chaque joueur (16, un cercle de fumée prévient 1 s avant) et des obus "
                        "perdus tombent sur le pont. Ne reste jamais immobile."),
    ],
    "bronze_sentinel": [
        ("Coup de pavois", "1 et 2", "Il ramène son bouclier contre lui (0,7 s, une ligne d'étincelles montre sa "
                                     "course), puis fonce derrière lui sur 8 à 10 blocs (12, gros recul). Pas de "
                                     "côté. En phase 2, souvent suivi d'un fauchage."),
        ("Coup d'espadon", "1 et 2", "Il hisse l'espadon au-dessus du heaume (1,1 s) et l'abat 3,5 blocs devant lui "
                                     "(22) ; une fissure court ensuite 12 blocs dans l'axe (14), annoncée par des "
                                     "étincelles dorées. En phase 2, trois fissures en éventail."),
        ("Fauchage", "1 et 2", "L'espadon ramené loin sur sa droite (0,8 s, l'arc est tracé au sol), puis balayé sur "
                               "220° (18, portée 7,5). Recule ou passe dans son dos."),
        ("Mur de pavois", "1 et 2", "Il plante son pavois devant lui pendant 2 s : tout coup de face rebondit. "
                                    "Contourne-le et frappe dans le dos ; s'il a paré quelque chose, il riposte d'un "
                                    "coup de pavois."),
        ("Piétinement", "1 et 2", "Le pied droit levé haut (0,9 s, un cercle de 3,5 blocs), puis abattu : 12 autour "
                                  "de lui et une onde à sauter (10)."),
        ("Danse des lames", "2", "Lame tendue sur le côté (0,6 s), il tourne trois fois sur lui-même en marchant "
                                 "sur toi (11 à chaque tour, rayon 4,8). Recule et frappe à la fin."),
        ("Chute du colosse", "2", "Accroupi, lame levée, pendant qu'un cercle doré te suit (1 s) ; il bondit, le "
                                  "cercle se fige là où tu étais et il retombe dessus l'épée la première une seconde "
                                  "plus tard (22, puis une onde). Sors du cercle."),
        ("Rayons runiques", "2", "Il lève l'espadon vers le ciel et le plante dans le sol : trois salves de lignes "
                                 "de lumière se dessinent sur le sol, une sous chaque joueur (0,9 s), puis "
                                 "flamboient (14). Un pas de côté suffit ; on ne peut pas les sauter."),
    ],
    "dune_king": [
        ("Fléau", "1 et 2", "Le fléau levé derrière l'épaule (0,7 s, l'arc est tracé), puis trois coups à une "
                            "demi-seconde d'écart (10, 10, puis 14 plus large). Recule après le deuxième."),
        ("Crosse", "1 et 2", "Il pointe sa crosse et la ramène en arrière (0,8 s, une ligne dorée montre sa portée "
                             "de 11 blocs) : touché, tu prends 10 et tu es tiré devant lui, et le fléau suit. "
                             "Écarte-toi de la ligne."),
        ("Tempête de sable", "1 et 2", "Bras levés, il rassemble le sable (1 s, le cône est tracé), puis souffle 1,5 s "
                                       "sur un cône de 70° et 10 blocs : cécité, lenteur et petits dégâts. Passe sur "
                                       "le côté ou derrière lui."),
        ("Les morts se lèvent", "1 et 2", "Crosse et fléau croisés au-dessus de la couronne (1 s, le sable remue à "
                                          "quatre endroits), puis des momies (husks) sortent du sol : 2 (3 en phase "
                                          "2), jamais plus de 4."),
        ("Vases canopes", "1 et 2", "Crosse pointée sur toi (0,7 s, un cercle sous tes pieds), puis chaque vase "
                                    "crache un trait de malédiction là où tu te trouves (8 et flétrissement). "
                                    "Bouge en arc de cercle."),
        ("Sables mouvants", "2", "Il flotte, paumes vers le sol (1 s) : des fosses de sable mouvant s'ouvrent en "
                                 "trois bras de spirale qui s'éloignent de lui, et une sous chaque joueur (12 et "
                                 "lenteur), chacune annoncée par du sable qui tombe."),
        ("Nuée de scarabées", "2", "Le fléau levé haut (0,8 s) puis claqué au sol : deux anneaux bas de scarabées "
                                   "roulent jusqu'au bord de l'arène (10). Saute chacun."),
        ("Jugement", "2", "Crosse tendue, yeux flamboyants (1,2 s, une ligne de lumière sur sa gauche montre le "
                          "départ) : un rayon bas balaie 200° de sa gauche à sa droite en 2,5 s (16). Saute-le quand "
                          "il passe, ou mets-toi dans son dos."),
    ],
    "fallen_seraph": [
        ("Glaive", "1 à 3", "Le glaive ramené par-dessus l'épaule droite (0,8 s, l'arc est tracé en lumière), puis un "
                            "balayage sur 210° (17). Recule hors de l'arc."),
        ("Estoc", "1 à 3", "Glaive pointé, une ligne de lumière marque sa trajectoire (0,7 s), puis elle glisse le long "
                           "de la ligne (16). Écarte-toi de la ligne ; elle s'arrête avant le bord du disque."),
        ("Éclats de halo", "1 à 3", "Main levée, ses éclats tournent plus vite (0,9 s, un cercle sous toi), puis six "
                                    "éclats partent l'un après l'autre là où tu te trouves (9 chacun ; par paires en "
                                    "phase 2). Bouge en arc de cercle."),
        ("Lances de lumière", "1 à 3", "Mains au ciel (1 s) : un cercle sous chaque joueur et quelques autres, la "
                                       "lumière y tombe, puis des colonnes frappent (14). En phase 2, une deuxième "
                                       "salve suit là où tu es allé. Sors du cercle."),
        ("Transport", "1 à 3", "Ses ailes se referment (0,6 s) pendant qu'un anneau violet marque l'endroit où elle "
                               "va apparaître, au bord du disque ; elle y surgit et enchaîne souvent les éclats."),
        ("Balayage aveuglant", "2 et 3", "Elle s'élève, le halo flamboie (1,2 s : une ligne de lumière sur sa gauche, "
                                         "des points dorés sur le cercle sûr) : un rayon part du halo et balaie 160° "
                                         "de sa gauche à sa droite en 2 s (14 et cécité). Trop haut pour sauter : "
                                         "colle-toi sous elle ou passe dans son dos."),
        ("Nova", "2 et 3", "Le halo levé au-dessus de la tête (1 s), un anneau de lumière roule vers le bord (12, saute-"
                           "le), puis un second revient du bord vers elle (12, saute encore)."),
        ("Le disque se brise", "3", "À 25 % de vie, elle se recroqueville, invulnérable (2 s), puis frappe : six "
                                    "fissures fendent le disque et une onde roule (8, saute-la). Ensuite les fissures "
                                    "s'illuminent tour à tour avant de jaillir (10 et lenteur), et au-delà de l'anneau "
                                    "d'or le disque s'effrite (3 par demi-seconde) : reste au centre."),
        ("Ciel brisé", "3", "Elle lance ses éclats vers le ciel (1,1 s) : quatre salves retombent, chacune annoncée par "
                            "un cercle sous chaque joueur (13). Change de place à chaque salve."),
        ("Chute du séraphin", "3", "Un cercle doré te suit 0,8 s puis se fige (il devient bleu) pendant qu'elle "
                                   "apparaît haut au-dessus : 0,7 s plus tard, elle s'abat dessus (22) et une onde "
                                   "roule (9). Sors du cercle, puis frappe pendant qu'elle se relève."),
    ],
    "chained_jailer": [
        ("Fouet de chaîne", "1 à 3", "La chaîne ramenée en arrière sur sa droite (0,9 s, l'arc est tracé en flammes), "
                                     "puis le boulet balaie 220° devant lui (16 et feu). Recule hors de l'arc."),
        ("Grappin", "1 à 3", "La chaîne enroulée au-dessus de l'épaule (0,8 s, une ligne de braises montre le jet "
                             "de 16 blocs) : touché, tu prends 9, tu es traîné à ses pieds et il frappe des deux poings. "
                             "Écarte-toi de la ligne."),
        ("Frappe ardente", "1 à 3", "Les deux poings levés (1,1 s, un cercle de feu devant lui), puis abattus (20) : "
                                    "un anneau de feu roule (9), deux en phase 2. Saute-le."),
        ("Entraves", "1 à 3", "Le gantelet levé, sa chaîne cliquette (0,9 s), puis balayé vers le sol : sous chaque "
                              "joueur un cercle de fer prévient (0,8 s) avant que des chaînes jaillissent (8, tenu "
                              "1,5 s sur place). Sors du cercle."),
        ("Coup de pied", "1 à 3", "Le pied ramené (0,6 s) puis un coup de pied qui repousse loin (12). Ne reste pas "
                                  "collé à lui."),
        ("Tourbillon", "2 et 3", "La chaîne déroulée sur le côté (0,7 s, un cercle de flammes), puis le boulet tourne "
                                 "autour de lui 2 s pendant qu'il marche sur toi (9 et feu à chaque tour, rayon 6,5)."),
        ("Bûcher", "2 et 3", "Bras en croix (1,1 s, huit lignes de braises au sol), puis poings plantés : le feu court "
                             "le long des quatre barreaux droits, puis des quatre diagonaux (13 et feu). Tiens-toi "
                             "entre les barreaux."),
        ("Libération", "3", "À 30 % de vie, il s'agenouille et tire sur ses chaînes (1,5 s, invulnérable), puis les "
                            "brise : une onde de feu (12, saute-la) et un cercle d'explosions. Il est ensuite plus "
                            "rapide et brûle qui reste au contact."),
        ("Verdict", "3", "Toutes les 12 s : la chaîne tournoie au-dessus de lui (1,2 s) et part dans le noir ; trois "
                         "salves de chaînes tombent sur chaque joueur, chacune annoncée 0,9 s par un cercle (14, tenu "
                         "et brûlé). Change de place à chaque salve."),
    ],
    "oathbound_gatekeeper": [
        ("Garde du serment", "1 et 2", "Son pavois bloque tout coup venu de face (environ 145°), quand il marche et "
                                       "pendant ses coups d'épée et de bouclier. Frappe ses flancs et son dos pendant "
                                       "qu'il se remet ; trois coups sur le bouclier et il charge de l'épaule."),
        ("Balayage", "1 à 3", "L'espadon ramené sur sa droite (0,8 s, l'arc est tracé), puis un balayage sur 200° "
                              "(16). Recule hors de l'arc."),
        ("Estoc", "1 à 3", "Une ligne de poussière montre la fente (0,7 s), puis il fonce pointe en avant sur 7 blocs "
                           "(15). Écarte-toi de la ligne."),
        ("Coup de pavois", "1 à 3", "Le pavois ramené contre lui (0,6 s), puis projeté devant lui (10, te repousse "
                                    "loin et te ralentit)."),
        ("Piétinement", "1 à 3", "Le pied levé (0,9 s, un cercle autour de lui), puis frappé : 13 autour de lui et "
                                 "une onde à sauter (deux en phase 2). Ne reste pas collé à son dos."),
        ("Chute de la clé", "1 à 3", "Un cercle doré te suit (0,9 s) puis se fige quand il lance la clé : elle tombe "
                                     "0,9 s plus tard (14, tenu sur place). Sa garde est ouverte."),
        ("Pivot", "1 à 3", "Si tu restes dans son dos, il plante ses pieds (0,7 s, un cercle) et tourne sur lui-même "
                           "lame tendue (14, rayon 5,5)."),
        ("Fronde de la clé", "2 et 3", "La clé tournoie au bout de sa chaîne (0,9 s, deux cercles dorés) : tout ce qui "
                                       "est entre 3,6 et 9,8 blocs prend 12. Colle-toi à lui ou éloigne-toi."),
        ("Coup d'en haut", "2 et 3", "L'espadon levé au-dessus du heaume (1,1 s), abattu devant lui (22), puis des "
                                     "mains de pierre jaillissent une à une sur sa ligne jusqu'à 15 blocs (13). Sa "
                                     "garde reste ouverte : frappe de face pendant qu'il se relève."),
        ("Charge", "2 et 3", "Le pavois en avant (0,8 s, une ligne d'étincelles), puis il charge (16, te projette)."),
        ("Le glas", "2 et 3", "L'espadon levé (1,2 s), frappé sur son propre pavois : la cloche sonne et un mur de "
                              "mains de pierre balaie toute la salle rangée après rangée (13, trop haut pour sauter). "
                              "Un seul passage reste ouvert, bordé de flammes d'âme : cours-y. 2,2 s plus tard, un "
                              "second mur balaie en travers."),
        ("Le serment", "3", "À 30 % de vie, il s'agenouille derrière son pavois comme les statues (10 s) : aucun coup "
                            "ne l'atteint, la porte le soigne et sonne trois balayages de mains. Chaque coup va au "
                            "Bouclier du Serment (sa propre barre). Brise-le : il chancelle 3 s (+50 % de dégâts) et "
                            "perd sa garde pour de bon. Sinon il se relève et recommence 30 s plus tard."),
        ("Furie", "3", "Bouclier brisé, l'espadon à deux mains : balayage, revers 0,6 s plus tard, puis coup d'en haut "
                       "et onde à sauter. Le glas revient toutes les 15 s."),
    ],
    "caldera_castellan": [
        ("Balayage", "1 à 3", "La hallebarde ramenée par-dessus l'épaule droite (0,9 s, l'arc est tracé en braises), puis "
                              "un balayage sur 230° (17 et feu). Recule hors de l'arc."),
        ("Taille", "1 à 3", "La hallebarde levée à deux mains (1 s, une ligne ardente au sol), puis abattue : 7 blocs "
                            "devant lui (20) et une gerbe de magma au bout (10). Écarte-toi de la ligne."),
        ("Charge", "1 à 3", "Hallebarde baissée comme une lance (0,8 s, une ligne de fumée), puis une course d'une "
                            "seconde (15). S'il charge dans un de ses murs, il le brise et reste sonné : frappe."),
        ("Bond", "1 à 3", "Accroupi, un cercle de braises te suit (0,6 s), se fige et s'enflamme quand il saute : il "
                          "retombe dessus à 1,2 s (20), puis une faille de lave court depuis l'impact vers toi (12 et "
                          "feu ; trois failles en éventail en phase 2). Sors du cercle, puis de la ligne."),
        ("Piétinement", "1 à 3", "Le pied droit levé haut (0,7 s, un cercle à ses pieds), puis frappé (12, repousse) ; en "
                                 "phase 2 une onde de chaleur roule (8, saute-la)."),
        ("Rempart", "2 et 3", "Le gantelet gauche levé, le magma coule (1 s, des lignes de fumée au sol), puis enfoncé "
                              "dans le sol : des murs d'obsidienne de 3 blocs jaillissent, un couloir autour de toi (il "
                              "le charge) ou un enclos (il bondit dedans). Qui est sur une ligne est projeté (8). Les "
                              "murs s'effondrent au bout de 10 s."),
        ("Moisson", "2 et 3", "La hallebarde ramenée à droite (0,8 s), un balayage, puis 0,6 s plus tard un revers "
                              "(15 chacun). Reste hors de portée jusqu'au second."),
        ("Chaleur du volcan", "3", "À 30 % de vie, il plante la hallebarde et s'agenouille (1,5 s, invulnérable), puis se "
                                   "relève : une onde (12, saute-la) et un cercle d'explosions. Il est ensuite plus "
                                   "rapide."),
        ("Cheminées", "3", "Toutes les 10 s environ : hallebarde levée au ciel (1 s) puis plantée ; les cheminées du "
                           "sol entrent en éruption en motifs (anneaux, spirales, damier, sous chaque joueur), chacune "
                           "annoncée 1 s par de la fumée et des gouttes de lave (13 et feu). Ensuite, son armure est "
                           "fragile 3 s (+30 % de dégâts) : c'est le moment de frapper."),
    ],
    "tide_abbess": [
        ("Balayage de crosse", "1 à 3", "La crosse tirée sur l'épaule droite (0,8 s, l'arc tracé d'écume), puis balayée "
                                        "sur 200° (15). Recule hors de l'arc."),
        ("Encensoir", "1 à 3", "L'encensoir ramené bas derrière elle (0,9 s), puis lancé en arc devant (12, ralenti) ; "
                               "trois nuages de saumure restent 5 s (3 et ralenti chaque demi-seconde)."),
        ("Vague de marée", "1 à 3", "La crosse levée (1,1 s) : la ligne de départ derrière elle et les brèches sont "
                                    "tracées au sol. Un mur d'eau traverse toute la rotonde (13, emporté), trop haut "
                                    "pour être sauté : tiens-toi dans une brèche. Phase 2 : une seconde vague en travers."),
        ("Glas", "1 à 3", "L'encensoir levé au-dessus de la couronne (1 s) : la marée attire tout le monde à 20 blocs "
                          "pendant 0,7 s, puis la saumure éclate autour d'elle (14, rayon 5). Cours contre le courant."),
        ("Ruée", "1 à 3", "Penchée dans le courant (0,7 s, une ligne de bulles), elle glisse le long de la ligne (14). "
                          "Dans l'inondation, la ruée va moitié plus loin."),
        ("Acolytes noyés", "1 à 3", "Toutes les 30 s : des noyés se lèvent des anneaux de bulles (deux au plus, plus "
                                    "à plusieurs)."),
        ("Baptême", "2 et 3", "La crosse levée (0,9 s), des cercles se referment sur chaque joueur : des geysers "
                              "jaillissent (14, projeté), deux salves (trois inondée)."),
        ("Encensoir double", "2 et 3", "Coup droit puis revers 0,6 s plus tard, chacun annoncé ; chacun laisse de la "
                                       "saumure."),
        ("Déluge", "3", "À 30 %, agenouillée (invulnérable 2,5 s), elle sonne trois fois : la rotonde s'inonde, une "
                        "onde roule (12, saute-la). Tu patauges, elle nage vite."),
        ("Lame de fond", "3", "Toutes les 12 s : trois marques (sur les joueurs) reliées de verre marin, puis elle "
                              "nage de l'une à l'autre en 2 s (14). Écarte-toi des lignes."),
    ],
    "lock_master": [
        ("Estoc", "1 à 3", "La lance ramenée le long du flanc (0,8 s, une ligne de lumière marque sa portée), puis "
                           "plongée droit devant : 9,5 blocs (16). Écarte-toi de la ligne."),
        ("Moulinet", "1 à 3", "La lance ramenée en travers (0,9 s, un anneau de laiton), puis balayée tout autour de lui "
                              "(13, rayon 6,5). Il le lance aussi sur qui s'attarde dans son dos."),
        ("Coup de vanne", "1 à 3", "Il avance 1,2 s derrière sa vanne levée : elle pare tout coup de face. Un coup "
                                   "lourd (11 et plus) ou un coup dans le dos brise sa garde : il chancelle 2 s (+30 % "
                                   "de dégâts). Sinon il fonce (14)."),
        ("Jets sous pression", "1 à 3", "La lance braquée à la hanche (1 s, les bords du balayage tracés), puis un jet "
                                        "d'eau balaie 100° devant lui (10, repoussé). Les colonnes et les grilles "
                                        "l'arrêtent. Phase 2 : aller et retour."),
        ("Vannes", "1 à 3", "La lance levée vers la coupole (1 s) : des dalles marquées de laiton sur et autour de "
                            "chaque joueur, l'eau goutte de la voûte au-dessus. Des grilles de fer tombent dessus "
                            "(18) et restent 9 s comme des murs."),
        ("Brochette", "2 et 3", "Trois estocs à 0,5 s d'écart (13 chacun), il se tourne vers toi entre chaque."),
        ("Bélier", "2 et 3", "Accroupi (0,8 s, une ligne de 16 blocs), il fonce propulsé par ses réservoirs (15). "
                             "Contre une grille il la brise et chancelle."),
        ("Vapeur", "2 et 3", "La vanne levée (0,9 s, un anneau de vapeur) puis plantée : la vapeur jaillit autour de "
                             "lui (14, rayon 6), puis une onde roule jusqu'à 12 (7, saute-la)."),
        ("Chasse d'eau", "3", "À 30 %, puis toutes les 22 s : il tourne son volant (invulnérable 1,5 s, des chevrons "
                              "d'écume montrent le sens), un courant balaie le sol 6,8 s (l'abri d'une colonne ou "
                              "d'une grille te protège) et il charge quatre fois (16)."),
    ],
    "bog_hierophant": [
        ("Balayage de crosse", "1 à 3", "La crosse tirée sur l'épaule droite (0,8 s, l'arc tracé de feu des marais), "
                                        "balayée sur 200° (16)."),
        ("Lanterne abattue", "1 à 3", "La crosse levée à deux mains (1 s, une ligne de boue) puis abattue : 19 sur la "
                                      "ligne, et la tourbière s'ouvre là où la lanterne tombe."),
        ("Leurre", "1 à 3", "Il tend la lanterne (0,9 s) : le feu follet te marque. 2,5 s plus tard, une floraison de "
                            "poison éclate où tu te tiens (12, poison) : éloigne-toi des autres. Phase 2 : il marque "
                            "tout le monde."),
        ("Boue engloutissante", "1 à 3", "Crosse plantée (1 s) : des cercles de vraie boue s'ouvrent sur toi et autour "
                                         "(8). Dedans, tu ralentis, puis au bout d'une seconde tu es pris (2 par seconde). "
                                         "La boue disparaît après 5 s."),
        ("Piétinement", "1 à 3", "Une échasse levée (0,6 s) puis abattue autour de lui (12, rayon 4,5). Phase 2 : un "
                                 "anneau de boue à sauter."),
        ("Enjambée", "1 à 3", "Penché sur ses longues jambes (0,7 s, une ligne de boue), il traverse 10 blocs (15)."),
        ("Sangsues", "1 à 3", "Toutes les 28 s : des sangsues (poissons d'argent) tombent de sa robe, deux au plus."),
        ("Moisson", "2 et 3", "Coup droit puis revers 0,6 s plus tard (15 chacun)."),
        ("Essaim", "2 et 3", "Bras écartés (0,9 s) : les mouches des marais te poursuivent 2 s, un peu moins vite qu'un "
                             "sprint (3 par demi-seconde, poison, faim). Cours."),
        ("Feu follet", "2 et 3", "Huit lanternes s'allument autour de la salle. Il se consume en feu follet, invisible et "
                                 "intouchable, saute de lanterne en lanterne, puis un cercle et un tintement marquent "
                                 "l'endroit derrière toi (0,8 s) : il s'y relève et frappe (17). Retourne-toi et "
                                 "écarte-toi."),
        ("Embrasement", "3", "À 30 %, agenouillé (invulnérable 2,5 s), il fracasse la lanterne : le gaz des marais "
                             "s'enflamme, une onde de feu (12, saute-la)."),
        ("Lignes de feu", "3", "Toutes les 11 s : des lignes de gaz en feu roulent à travers la salle (12, brûlure), trop "
                               "hautes pour être sautées : passe par les brèches. Trois lignes parallèles, deux en "
                               "croix, ou un anneau qui se referme avec deux couloirs. Après, il est épuisé 2,5 s "
                               "(+25 % de dégâts)."),
    ],
    "star_curator": [
        ("Bâton", "1 à 3", "L'astrolabe ramené sur l'épaule (0,7 s, l'arc tracé), deux balayages devant lui à 0,7 et "
                           "1,2 s (13 chacun). Phase 2 : un estoc à 1,7 s qui porte à 7 blocs (16)."),
        ("Volée de livres", "1 à 3", "Main levée (0,9 s) : trois livres (en phase 2, deux par joueur) te poursuivent "
                                     "lentement (7, puis 6). Une flèche ou un coup en abat un."),
        ("Puits de gravité", "1 à 3", "Bâton planté (1 s) : pendant 1,5 s tout le monde à 15 blocs est attiré vers "
                                      "lui (sprinte vers l'extérieur), puis le puits implose (15, rayon 4). Phase 2 : "
                                      "une onde jusqu'à 10 blocs (8, saute-la)."),
        ("Chute d'étoiles", "1 à 3", "L'astrolabe levé vers le dôme (0,8 s) : un cercle suit chaque joueur 0,7 s puis "
                                     "se fige, un éclat tombe 0,8 s plus tard (14, rayon 2,5) ; d'autres tombent au "
                                     "hasard. Phase 2 : une seconde volée."),
        ("Orbite", "1 à 3", "Quand tu restes collé : les livres tournoient jusqu'à 5 blocs (11). Phase 2 : une onde "
                            "jusqu'à 9 (7)."),
        ("Lance", "1 à 3", "Bâton pointé (0,8 s, une ligne tracée) : il fond sur toi le long de la ligne (15)."),
        ("Tempête de pages", "2 et 3", "Bras levés (1,2 s) : 1,5 s d'alerte, puis 7 s de tempête. Hors des cercles "
                                       "dorés qui tournent dans le cratère, tu es aveuglé et coupé (2 par seconde). "
                                       "Il continue d'attaquer."),
        ("Constellation", "2 et 3", "Il trace six étoiles au sol (1 s, une près de chaque joueur), puis les lignes "
                                    "qui les relient éclatent l'une après l'autre (13). Sors des lignes."),
        ("Inversion", "3", "À 30 %, une fois (invulnérable 3 s) : il s'élève, une onde (12, saute-la), puis il "
                           "accélère et la gravité du cratère s'inverse."),
        ("Pulsations", "3", "Toutes les 8 s : 1,5 s d'alerte (des anneaux dorés autour des brasiers de cristal, sauf "
                            "celui où il se tient), puis tout joueur hors d'un anneau est soulevé (4, lévitation "
                            "1,3 s), puis redescend en chute lente."),
        ("Lance d'étoiles", "3", "Toutes les 10 s : il se téléporte sur un brasier de cristal, vise (0,9 s, la ligne "
                                 "te suit puis se fige) et tire un rayon à travers le cratère (16), qui touche aussi "
                                 "les joueurs en l'air."),
    ],
    "chime_abbot": [
        ("Bâton-dragon", "1 à 3", "Le bâton ramené sur l'épaule (0,7 s, l'arc tracé en pétales) : un balayage, puis "
                                  "un revers 0,6 s plus tard (12 chacun). Phase 2 : il abat le bâton sur un cercle "
                                  "rouge devant lui à 1,8 s (16, une onde jusqu'à 6, saute-la)."),
        ("Paume", "1 à 3", "La paume gauche ramenée à la hanche (0,9 s, le cône de vent tracé en blanc) : un souffle "
                           "dans un cône de 9 blocs (14, repoussé). Phase 2 : une onde jusqu'à 7 en plus (7)."),
        ("Cercle de carillons", "1 à 3", "Bras écartés, le halo brille (1 s) : huit tiges volent du halo et pendent en "
                                         "cercle à 6,5 blocs autour de lui. Elles sonnent l'une après l'autre ; chaque "
                                         "tige marque sa zone au sol (doré puis rouge) 0,6 s avant de frapper (11, "
                                         "rayon 2,4). Phase 2 : elles sonnent dans les deux sens, puis une tige "
                                         "au-dessus de chaque joueur."),
        ("Tempête de pétales", "1 à 3", "Le bâton tournoie au-dessus de sa tête (1,1 s) ; trois brèches tracées en "
                                        "lignes de vent blanc partent de lui. Un anneau de pétales trop haut pour être "
                                        "sauté balaie tout le pont : hors d'une brèche, tu es aveuglé 1,5 s (2 s en "
                                        "phase 2) et coupé (5). Phase 2 : un second anneau 0,8 s plus tard, brèches "
                                        "tournées (tracées en rose)."),
        ("Pas du vent", "1 à 3", "De loin (7 blocs et plus) : il se replie dans ses manches (0,6 s, une colonne de "
                                 "pétales tourne au coin du pont le plus proche de toi), disparaît et réapparaît là, "
                                 "puis enchaîne bâton ou paume."),
        ("Rafale", "2 et 3", "Trois estocs du bâton le long d'une ligne rouge (0,7, 1,1 et 1,5 s, 10 chacun), il se "
                             "tourne vers toi entre chacun, puis une toupie à 2 s (13, rayon 4,5, cercle tracé)."),
        ("Chute de cloche", "2 et 3", "Il s'envole (1 s) pendant qu'un cercle doré te suit, le cercle se fige et "
                                      "rougit (0,5 s), puis il s'abat dessus (17, rayon 3) et une onde roule jusqu'à "
                                      "8 (8, saute-la)."),
        ("Éveil du dragon", "3", "À 30 %, une fois (invulnérable 3 s) : il s'élève, le halo tournoie, puis le fantôme "
                                 "du dragon d'airain s'arrache du bâton : une onde (11, saute-la), il accélère, le "
                                 "dragon tourne au-dessus du pont."),
        ("Souffle du dragon", "3", "Toutes les 12 s : il pointe le bâton (1 s) ; trois couloirs (quatre à trois "
                                   "joueurs et plus) sont tracés à travers le pont, l'un passe par toi. Le prochain "
                                   "rougit, la tête du dragon attend à son bout, puis le dragon le traverse en "
                                   "soufflant (13, ralenti 2 s), couloir après couloir, toutes les 0,5 s. Reste entre "
                                   "les couloirs ; l'axe change à chaque fois."),
    ],
    "mine_baron": [
        ("Foreuse", "1 à 3", "La foreuse armée (0,8 s, une ligne rouge de 6,5 blocs devant lui), puis deux poussées "
                             "(9 chacune, à 0,55 s d'écart). Fais un pas de côté."),
        ("Coup de pic", "1 à 3", "Le pic-marteau levé (1 s, un cercle doré devant lui) : 18 dans le cercle, puis "
                                 "trois gerbes d'or jaillissent en ligne jusqu'à 9,5 blocs (11). Phase 2 : trois "
                                 "lignes en éventail."),
        ("Charge de forage", "1 à 3", "De loin (6 à 24 blocs) : accroupi derrière la foreuse (0,9 s, le chemin tracé "
                                      "en rouge sur 14 blocs), il fonce (13, gros recul). S'il percute la roche, la "
                                      "foreuse se coince et trois pierres tombent autour de lui."),
        ("Dynamite", "1 à 3", "Il allume des fagots sur la lanterne de son casque (0,9 s) : des cercles dorés te "
                              "suivent puis rougissent et se figent ; les fagots tombent et leur mèche brûle 1,1 s "
                              "(0,9 en phase 2, 0,8 en phase 3), puis sautent (14, rayon 3, projeté). Aucun bloc "
                              "n'est détruit."),
        ("Échappement", "1 à 3", "Si tu restes dans son dos : un sifflement (0,7 s, le cône de vapeur tracé derrière "
                                 "lui), puis la chaudière purge (13 dans un cône de 6 blocs derrière lui, 6 tout "
                                 "autour). Frappe le dos par à-coups, sans t'y installer."),
        ("Éboulement", "1 à 3", "Il frappe la paroi (1,1 s) : des cercles sous chaque joueur et ailleurs, de la "
                                "poussière qui tombe, puis des rochers (13, rayon 1,8, ralenti). En phase 3, il en "
                                "appelle un toutes les 13 s."),
        ("Enchaînement", "2 et 3", "Foreuse, pic en arc, puis le pic planté (10, 12 et 16, une onde au sol de 8) en "
                                   "1,5 s. Recule dès le premier coup."),
        ("Filon éclaté", "2 et 3", "Il frappe le sol (1 s) : des lignes d'éruptions d'or filent vers trois joueurs "
                                   "au plus (12 chacune). Sors de la ligne."),
        ("Mèche", "2 et 3", "Il lance un tonneau de poudre au loin ; une étincelle court le long de la mèche tracée "
                            "au sol (6 et enflamme si tu es dessus), puis le tonneau saute (20, rayon 5) et quatre "
                            "gerbes jaillissent autour. Va loin du tonneau, saute la mèche."),
        ("Cuirasse d'or", "2", "Au rugissement, le minerai monte sur lui : il ne prend plus qu'un cinquième des "
                               "dégâts. Des géodes d'or luisent sur sa chaudière (3, plus une par joueur, 6 au "
                               "plus) : chaque coup de 3 ou plus porté dans son dos en fait sauter une et passe en "
                               "entier. Sans géode, il chancelle 3 s (+30 % de dégâts). Toutes les 26 s, il se "
                               "recuirasse : 1,5 s d'alerte (l'or afflue vers lui), casse le flot à 60 dégâts pour "
                               "le faire chanceler. Des tireurs bandits arrivent la première fois."),
        ("Coup de grisou", "3", "À 30 %, il fait sauter les étais : toutes les lampes de la caverne s'éteignent "
                                "(elles reviennent à la fin), seule sa lanterne et les mèches éclairent. Le filon "
                                "crépite : une étincelle toutes les 1,2 à 2,5 s (alerte, puis 7 à 3,5 blocs)."),
        ("Coup de lanterne", "3", "Il braque sa lanterne (0,9 s, le cône tracé) : dans son faisceau, à vue, tu es "
                                  "aveuglé 3 s et ralenti (4), puis il charge le premier aveuglé. Coupe sa ligne de "
                                  "vue derrière un étai ou sors du cône."),
    ],
    "corsair_captain": [
        ("Sabre", "1 à 3", "Le sabre ramené sur l'épaule (0,7 s, l'arc tracé en rouge), une taille et un revers à "
                           "0,5 s d'écart (10 chacun). Phase 2 : un estoc fendu 0,5 s plus tard, sur 6,5 blocs (13)."),
        ("Harpon", "1 à 3", "Le fusil braqué sur toi (0,9 s, une ligne rouge qui te suit) : le harpon file le long de "
                            "la ligne (8), te ramène à elle et elle te taille aussitôt (9). Fais un pas de côté."),
        ("Bourrasque", "1 à 3", "Pieds plantés, le rotor incliné (1 s, le cône tracé en blanc) : 3, puis pendant 1 s "
                                "le vent te pousse vers le bastingage. Sprinte contre lui ou sors du cône."),
        ("Piqué", "1 à 3", "Accroupie sous le rotor (0,8 s), elle s'envole ; un cercle te suit 0,7 s puis se fige, "
                           "et elle s'abat dessus (16, rayon 3), suivie d'une onde (6, saute-la)."),
        ("Fusée", "1 à 3", "Le fusil levé (0,7 s, une fine ligne orange) : une fusée éclairante file vers toi (9, "
                           "brûlure). Phase 2 : une seconde fusée vers un autre joueur."),
        ("Abordage", "2 et 3", "Accroupie, le sabre pointé (0,9 s, le chemin tracé sur 14 blocs) : elle fonce sur "
                               "le rotor (12, recul). Écarte-toi du chemin."),
        ("Cyclone", "2 et 3", "Si tu restes collé : un cercle rouge (0,8 s), puis deux tours complets du sabre "
                              "(11 chacun, rayon 4,2). Recule."),
        ("Abordeurs", "2", "Après le rugissement, une fusée de signal : deux pillards du ciel montent à bord (un de "
                           "plus par deux joueurs en plus)."),
        ("Gîte", "3", "À 30 %, une fois (invulnérable 3,5 s) : le navire gîte, elle plante son sabre dans le pont, "
                      "une onde (12, saute-la), puis elle accélère."),
        ("Couloirs de vent", "3", "Toutes les 10 s environ : quatre couloirs de 3 blocs traversent le pont, tracés "
                                  "1,5 s à l'avance (blancs, puis rouges) ; ils soufflent l'un après l'autre (4, "
                                  "poussée vers le bastingage). Reste dans les intervalles."),
        ("Bombes éclairantes", "3", "Le fusil levé au ciel (1 s) : des cercles te suivent puis se figent, les "
                                    "fusées retombent 0,9 s plus tard (10, rayon 2,5) et laissent 5 s de feu sur le "
                                    "pont (2 toutes les 0,5 s). Sors des cercles et du feu."),
    ],
    "hollow_cantor": [
        ("Baguette", "1 à 3", "La levée par-dessus l'épaule droite (0,7 s, l'arc tracé en lueur d'écho), le temps "
                              "fort (13), puis un revers 0,5 s plus tard (11) après s'être tourné vers toi."),
        ("Cri", "1 à 3", "La capuche rejetée en arrière, les tuyaux qui gonflent (1,1 s) : des rides courent au sol "
                         "dans le cône, de plus en plus serrées, et rougissent quand il ne tourne plus. Puis le cri "
                         "(14, repoussé, ralenti ; cône de 14 blocs, plus large et plus long en phase 2 : 16). Sors "
                         "du cône sur le côté."),
        ("Glas", "1 à 3", "Le diapason levé à deux mains (0,9 s, un cercle autour de lui), planté dans le sol : 15 "
                          "dans le cercle et une onde à sauter (8). Phase 2 : une seconde onde 0,5 s plus tard."),
        ("Cadence", "1 à 3", "De loin (6 à 20 blocs) : il se penche, la baguette pointée (0,8 s, la ligne tracée), "
                             "puis glisse le long de la ligne (12 à qui se trouve sur son chemin)."),
        ("Résonance", "1 à 3", "Des bourgeons d'améthyste poussent au sol, chacun dans un cercle doré, pendant qu'il "
                               "frappe son diapason (1,2 s) ; la note enfle encore 0,8 s, le sol frémit hors des "
                               "cercles, puis tout le sol sonne : 14 et ralenti à qui est hors d'un cercle doré "
                               "(sauter au bon moment marche aussi). Les bourgeons éclatent ensuite et disparaissent."),
        ("Silence", "2 et 3", "Un long doigt sur la capuche vide (1 s, le bord de la zone tracé autour de lui) : 7 s "
                              "de silence dans un rayon de 8. Dedans, tu es ralenti, tes sons sont coupés et ta vue "
                              "s'assombrit, et lui s'efface en un miroitement de cendre (ses yeux de lumière restent "
                              "visibles) ; un coup le révèle une seconde."),
        ("Chœur", "2 et 3", "Les deux bras levés vers son chœur invisible (1,1 s, une lueur d'âme monte là où ils "
                            "vont paraître) : des choristes de l'écho, moines-sonneurs et banshees (2, plus un tous "
                            "les deux joueurs de plus ; jamais plus de 2 + le nombre de joueurs)."),
        ("Fugue", "2 et 3", "La baguette trace la phrase (1 s), puis trois temps à 0,6 s d'écart : à chaque fois, un "
                            "cercle te suit 0,5 s, se fige en rouge, et éclate 0,5 s plus tard (12)."),
        ("L'orgue", "3", "À 30 % : il s'élève, bras écartés (2 s, invulnérable), puis le grand accord : une onde à "
                         "sauter (12), un voile d'obscurité, il accélère. Désormais des souffles de tuyau jaillissent "
                         "du sol sous chaque joueur toutes les 6,5 s environ (un cercle et de la poussière qui monte "
                         "1,2 s avant, rouge à la fin : 12 et projeté)."),
        ("Requiem", "3", "Toutes les 12 s : il joue l'air comme un clavier (1 s, six rangées tracées en gris au sol, "
                         "chacune avec une brèche), puis les rangées de souffles s'éloignent de lui l'une après "
                         "l'autre, toutes les 0,3 s, chacune rougissant 0,7 s avant (13). Tiens-toi dans les brèches."),
    ],
    "soul_stoker": [
        ("Pelletée", "1 à 3", "La pelle ramenée en travers du corps (0,8 s, l'arc tracé en poussière bleue) : un "
                              "balayage (13), puis les braises qu'elle projette volent devant lui et retombent sur des "
                              "cercles marqués dès leur départ, rouges à la fin (0,9 s plus tard : 8 et embrasé ; trois "
                              "braises, cinq en phase 2)."),
        ("Coup de piston", "1 à 3", "Les pieds plantés, le poing armé loin derrière, la vapeur qui siffle (1,4 s) : une "
                                    "ligne de 14 blocs tracée au sol le suit lentement, puis se fige et rougit 0,5 s "
                                    "avant. Le poing (18 à 4 blocs), puis une onde de choc qui court le long de la "
                                    "ligne (10 et projeté). Sors de la ligne sur le côté."),
        ("Attiser", "1 à 3", "Trois pelletées d'âmes dans son foyer (0,3, 0,8 et 1,3 s) pendant qu'une jauge de "
                             "poussière monte au-dessus de sa tête, du bleu au rouge ; le cône (11 blocs, 13 en phase 2) "
                             "est tracé dès 0,6 s, te suit lentement, rougit et se fige 0,6 s avant. À 2 s, un cône de "
                             "flammes bleues jaillit du foyer : 15 et embrasé 4 s."),
        ("Évents", "1 à 3", "La pelle levée haut (1 s) puis plantée dans le pont. Des évents sont marqués au sol dès "
                            "le début (cinq, sept en phase 2, un sous toi ; en phase 2 un sous chaque joueur) : des "
                            "cercles bleus sur de la fumée. Ils s'ouvrent l'un après l'autre, toutes les 0,25 s, chaque "
                            "cercle rougissant 0,5 s avant : 12, projeté et embrasé 3 s."),
        ("Charge", "2 et 3", "De loin (6 blocs et plus) : il se ramasse, les cheminées rugissent (1,2 s, un couloir "
                             "tracé de lui jusqu'à toi et au-delà, rouge à la fin), puis il le dévale comme une "
                             "locomotive folle (15 et bousculé) et s'arrête net au bout ou contre un obstacle (8 "
                             "autour de lui)."),
        ("Serviteurs", "2 et 3", "Il ouvre son foyer (1 s) : deux squelettes wither (plus un tous les deux joueurs de "
                                 "plus) sortent du feu d'âmes, sauf si trois de ses serviteurs sont déjà sur le pont."),
        ("Surpression", "3", "À 30 %, une fois (invulnérable 3 s) : il étreint sa chaudière, tremble, la jauge monte "
                             "(2 s), puis les soupapes sautent : une onde à sauter (10), il accélère. Désormais le pont "
                             "suit le rythme du vilebrequin : des bandes de 4 blocs à travers le pont (le long du "
                             "vilebrequin) brûlent en alternance toutes les 3 s, chaque pulsation tracée 2 s avant "
                             "(rouge la dernière 0,6 s) : 5 et embrasé. Change de bande à chaque pulsation."),
        ("Souffle des soupapes", "3", "Toutes les 11 s : il frappe sa chaudière (1 s) ; trois brèches sont tracées en "
                                      "lignes depuis lui (bleue, dorée, rouge). Trois anneaux de flammes bleues, trop "
                                      "hauts pour être sautés, partent de lui à 0,6 s d'écart, chacun avec sa brèche, "
                                      "tournée de 25° à chaque anneau (10 et embrasé). Le rythme du pont s'arrête "
                                      "pendant ce temps."),
    ],
    "asylum_director": [
        ("Scalpel", "1 à 3", "Le bras-scalpel ramené par-dessus l'épaule (0,7 s) : elle se tourne vers toi, puis une "
                             "ligne rouge se fige (7 blocs au plus, seulement sur le sol) et elle fond le long d'elle "
                             "(13 à qui se trouve sur son chemin). Fais un pas de côté."),
        ("Scie", "1 à 3", "Le bras-scie levé haut à sa gauche (0,8 s, un arc très large tracé) : un balayage devant "
                          "elle (14). Phase 2 : elle se tourne et revient en sens inverse 0,7 s plus tard (11)."),
        ("Seringue", "1 à 3", "Le bras-seringue vise par-dessus son épaule (0,9 s, une ligne verte te suit puis "
                              "rougit) : une fléchette (8 et ralenti 3 s), arrêtée par les murs. Phase 2 : un éventail "
                              "de trois."),
        ("Retour en arrière", "1 à 3", "Elle remonte sa montre (1 s) : un fantôme d'horloge se forme à tes pieds (à "
                                       "ceux de chaque joueur en phase 2) et tourne à rebours 3 s, puis te ramène à "
                                       "lui ; son cercle, tracé tout du long et rouge à la fin, éclate 0,7 s après "
                                       "(12). Sors-en dès que tu reviens."),
        ("Pendule", "1 à 3", "La montre levée haut (1,2 s) pendant que le couloir du grand pendule est tracé à "
                             "travers le centre de la salle, rouge 0,6 s avant : il le traverse en 0,5 s (14, rejeté "
                             "hors du couloir). Le couloir suivant tourne de 45° ; deux passages, trois en phase 2."),
        ("Araignées", "1 à 3", "Elle frappe le sol de ses quatre bras (0,9 s, des étincelles) : deux araignées "
                               "mécaniques (trois en phase 2, une de plus tous les deux joueurs), jamais plus de "
                               "quatre."),
        ("Pince", "2 et 3", "Le bras-pince jaillit le long d'une ligne rouge (0,8 s, 7 blocs) : la première cible "
                            "est saisie (8), ramenée devant elle et lâchée, puis l'arc de la scie est tracé et elle "
                            "taille 0,7 s plus tard (10)."),
        ("Dissection", "2 et 3", "Les quatre bras levés (0,8 s) : les quatre quarts autour d'elle (4,5 blocs) sont "
                                 "frappés l'un après l'autre toutes les 0,4 s (9) ; le prochain est tracé en rouge, "
                                 "le suivant en blanc. Passe d'un quart à l'autre."),
        ("Glissement", "2 et 3", "Elle remonte sa montre et s'amincit (0,6 s, un fantôme d'horloge 2,5 blocs "
                                 "derrière toi), disparaît et reparaît là, puis balaie de sa scie."),
        ("Minuit", "3", "À 30 % : elle s'élève, bras écartés comme des aiguilles (2 s, invulnérable, douze coups de "
                        "cloche), puis la grande horloge sonne : une onde à sauter (11), elle accélère."),
        ("Les aiguilles", "3", "Toutes les 18 s environ : elle gagne le centre du cadran et tend les bras (1,5 s, les "
                               "deux aiguilles tracées en rouge jusqu'aux murs, la brèche entre elles en or, un coup "
                               "de cloche toutes les 0,5 s), puis les aiguilles font les trois quarts d'un tour en "
                               "8,5 s, à un quart l'une de l'autre (12 par aiguille qui te traverse). Reste dans la "
                               "brèche et suis-la."),
    ],
    "spore_alchemist": [
        ("Bâton", "1 à 3", "Le bâton ramené par-dessus l'épaule (0,8 s, un arc tracé en vert) : un balayage devant lui "
                           "(13). Il se tourne, un cercle rouge s'allume 3,5 blocs devant lui et la fiole s'y abat "
                           "0,6 s plus tard (11 et poison). Phase 2 : il enchaîne parfois pulvérisation ou fioles."),
        ("Pulvérisation", "1 à 3", "Le pistolet braqué (1,2 s, un cône vert qui te suit puis rougit) : des spores "
                                   "pendant 1 s (3 et poison, quatre fois si tu restes dedans), puis un nuage de spores "
                                   "persiste 5 s à 5 blocs devant lui. Contourne-le."),
        ("Fioles", "1 à 3", "Deux fioles (trois en phase 2) visent des cercles tracés de la couleur de leur breuvage : "
                            "vert poison, gris lenteur, noir cécité ; la première te suit, un cercle rouge s'allume "
                            "dedans à la fin. Elles éclatent 0,8 s après le lancer (8 et l'effet)."),
        ("Pousse", "1 à 3", "Le bâton planté dans le chapeau (0,9 s) : un cercle brun sous chaque joueur et sur deux "
                            "autres points (quatre en phase 2), rouge à la fin ; 1,5 s plus tard un champignon en jaillit "
                            "(10, soulevé, poison) et reste debout 6 s, sauf là où quelqu'un se tient."),
        ("Voile de spores", "2 et 3", "La vanne de la cuve ouverte (1 s), il disparaît dans un nuage (invulnérable) ; un "
                                      "cercle vert, rouge à la fin, marque l'endroit où il ressort, près de toi mais "
                                      "jamais sur quelqu'un : 1,5 s plus tard il en jaillit (11, repoussé, poison)."),
        ("Bogged", "2 et 3", "Il remue le chapeau de son bâton (1 s) : deux bogged (un de plus tous les deux joueurs) "
                             "sortent du mycélium, jamais plus de trois."),
        ("Floraison", "3", "À 30 % : sa bosse enfle (2 s, invulnérable), il frappe le chapeau : une onde à sauter (10), "
                           "il accélère. Le chapeau respire : des évents près du bord crachent des spores sur des "
                           "cercles marqués toutes les 4 s (8 et poison), et un champ de fils de mycélium ralentit "
                           "quiconque reste à moins de 6 blocs de lui."),
        ("Expiration", "3", "Toutes les 16 s environ : le chapeau inspire (2,5 s), l'anneau doré s'embrase et un côté "
                            "de l'anneau (l'extérieur, puis l'intérieur, à tour de rôle) se remplit de spores, rouges à "
                            "la fin ; puis il expire : 9 et poison II pour qui est de ce côté. L'anneau lui-même est "
                            "toujours sûr ; sauter ne sert à rien, traverse l'anneau."),
    ],
    "lumber_jarl": [
        ("Balayage à la tronçonneuse", "1 à 3", "La hache armée sur l'épaule, le moteur qui monte (0,9 s, un arc orange "
                                                 "puis rouge, ±80°, 5,5 blocs, 7 en phase 3) : la chaîne traverse "
                                                 "l'arc pendant 0,8 s et mord quatre fois (4 chaque fois). Sors de l'arc."),
        ("Coup de hache", "1 à 3", "La hache levée à deux mains (1,2 s) : une ligne te suit lentement puis rougit et se "
                                   "fige. Elle s'abat devant lui (16), puis le pont se fend le long de la ligne, un bloc "
                                   "par tick (10, soulevé) et éclate au bout (6). Phase 2 : il enchaîne parfois le "
                                   "tronc roulant ou le balayage."),
        ("Lame de scie", "1 à 3", "Il arrache une lame de rechange à son harnais (1 s) : sa boucle est tracée en or jusqu'à "
                                  "toi et retour, rouge à la fin ; la lame suit la boucle et revient (9, elle peut "
                                  "toucher à l'aller et au retour). Phase 2 : deux lames sur des boucles en miroir."),
        ("Timber !", "1 à 3", "Il lève la hache et hurle (1 s) : un couloir de 6 × 2 sous chaque joueur et deux autres "
                              "(trois en phase 2) près de la cible, rouges 0,5 s plus tard, puis des troncs s'y "
                              "écrasent (11, ralenti 1,5 s). Les troncs ne restent pas."),
        ("Tronc roulant", "1 à 3", "Il arrache un tronc à son harnais (1,3 s) : un couloir de 3 blocs tracé à travers le "
                                   "pont te suit puis rougit ; le tronc roule (0,7 bloc par tick) : 10, soulevé et "
                                   "poussé hors du couloir."),
        ("Appel de l'équipe", "2 et 3", "Le manche frappé trois fois sur le pont (1 s) : deux vindicateurs et tireurs "
                                        "bandits (un de plus tous les deux joueurs), jamais plus de trois."),
        ("Surrégime", "3", "À 30 % : la hache levée vers la machine (2 s, invulnérable), une onde à sauter (10), il "
                           "accélère. Puis le volant lance des étincelles : un secteur de 70° tracé 1,5 s, puis une "
                           "gerbe le balaie d'un bord à l'autre (6, enflammé) ; des bouches de vapeur marquées en "
                           "blanc éclatent 1,5 s plus tard (7, soulevé)."),
    ],
    "thorn_gardener": [
        ("Coups de sécateur", "1 à 3", "Les deux sécateurs grands ouverts (0,8 s, un arc tracé en vert) : le droit se "
                                       "referme devant lui (12). Il se tourne, l'arc du gauche est tracé en rouge et se "
                                       "referme 0,4 s plus tard (10). Phase 2 : il enchaîne parfois l'arrosage ou la fente."),
        ("Fente", "1 à 3", "Accroupi, le sécateur droit ouvert en arrière (1,1 s) : un couloir vert te suit puis rougit "
                           "et se fige ; il bondit le long du couloir et les lames se referment au bout (15 jusqu'à 3 "
                           "blocs au-delà). Sors du couloir."),
        ("Lignes d'épines", "1 à 3", "Les sécateurs plantés dans la feuille (1 s) : trois lignes (cinq en phase 2) "
                                     "marquées depuis lui, l'une vers toi, rouges à la fin ; les épines jaillissent le "
                                     "long de chacune (11, soulevé, ralenti 1 s)."),
        ("Liane", "1 à 3", "Le sécateur gauche planté à ses pieds (1,2 s) : un cercle vert sous toi te suit puis se fige "
                           "en rouge, une liane rampe vers lui. Elle se referme : 6 et enraciné 1,5 s. Frappe n'importe "
                           "quoi, ou prends un coup, et elle se déchire aussitôt."),
        ("Arrosage", "1 à 3", "Le canon-arrosoir braqué par-dessus l'épaule (1,3 s, un cône bleu qui te suit puis rougit) : "
                              "un jet d'eau pendant 1 s, 3 et une petite poussée quatre fois, jamais hors de la feuille. "
                              "Deux plaques fertilisées (trois en phase 2) sont marquées 1,5 s, puis des buissons "
                              "d'épines y poussent (7) et restent 5 s."),
        ("Appel du jardin", "2 et 3", "Les sécateurs claqués au-dessus de sa tête (1 s) : deux grenouilles "
                                      "dards et araignées-horloges (une de plus tous les deux joueurs), jamais plus de trois."),
        ("Pollen", "2 et 3", "Il secoue sa cloche (0,9 s) : des cercles jaunes sous toi et les autres joueurs ; la fleur "
                             "éclate et le pollen y retombe 0,8 s plus tard (8, ralenti 2 s)."),
        ("Lampe solaire", "3", "À 30 % : les sécateurs levés vers la lampe (2 s, invulnérable), une onde à sauter (10), il "
                               "accélère. Des rayons de soleil balaient ensuite la feuille : un cercle doré et son "
                               "chemin tracés 1,5 s (rouges à la fin), puis le rayon suit le chemin lentement : 4 et "
                               "enflammé toutes les 0,5 s si tu restes dedans."),
        ("Photosynthèse", "3", "Toutes les 16 s environ : il plante ses sécateurs et lève la tête vers la lampe dans un "
                               "cercle de lumière (rayon 3) ; pendant 2,5 s il regagne 1 % de sa vie toutes les 0,5 s, "
                               "sauf si un joueur se tient dans le cercle pour lui faire de l'ombre. Il ne frappe pas : "
                               "c'est le moment de taper."),
    ],
    "abyss_diver": [
        ("Percée", "1 à 3", "La foreuse ramenée en arrière (1,1 s) : un couloir turquoise te suit puis rougit et se "
                            "fige ; il fonce le long du couloir, foreuse en avant (14, jusqu'à 2,5 blocs au-delà). "
                            "Sors du couloir."),
        ("Broyage", "1 à 3", "La foreuse levée qui hurle (0,8 s, un arc turquoise puis rouge) : il la tient devant lui "
                             "1,5 s, 5 trois fois si tu restes dans l'arc. Phase 2 : il enchaîne parfois choc ou rivets."),
        ("Rivets", "1 à 3", "Le pistolet braqué (1 s) : trois lignes (cinq en phase 2) tracées vers toi, rouges à la "
                            "fin ; trois salves de rivets les suivent en 1 s (5 par rivet). Un pas de côté suffit."),
        ("Choc de pression", "1 à 3", "Les bras levés (1,2 s), un cercle de 5 blocs autour de lui, rouge à la fin : "
                                      "il frappe le sol (12, soulevé), puis une onde court jusqu'à 11 blocs (6, saute-la)."),
        ("Harpon", "1 à 3", "Le pistolet braqué (1 s, une ligne qui te suit puis se fige en rouge) : le harpon file le "
                            "long de la ligne ; s'il te mord, 6 et il te tire jusqu'à 7 blocs vers lui (jamais à moins "
                            "de 3). Phase 2 : un broyage peut suivre, tracé comme d'habitude."),
        ("Nuage de vase", "2 et 3", "Penché sur ses vannes (0,9 s, un cercle sombre de 4,5 blocs, rouge à la fin) : la "
                                    "vase jaillit du scaphandre (4, repoussé, aveuglé 2 s) et le nuage reste 4 s, "
                                    "aveuglant 1,5 s qui y entre. Contourne-le."),
        ("Appel de l'équipage", "2 et 3", "Il cogne trois fois son casque : des marins noyés et des noyés (un de plus "
                                          "tous les deux joueurs) sortent de la brume du forage, jamais plus de trois."),
        ("La coque gémit", "3", "À 30 % : la foreuse plantée dans le sol (2 s, invulnérable), une onde à sauter (10). "
                                "Ensuite des pics de pression éclatent sur des cercles marqués 1,5 s (rouges à la fin : "
                                "8, soulevé), et des méduses lumineuses dérivent vers vous : à leur contact elles "
                                "rougissent et éclatent 0,6 s plus tard (7 dans 2 blocs). Aucune eau n'entre jamais."),
        ("Surcharge", "3", "Toutes les 18 s environ : bras écartés, hublot ardent (1,5 s, un cercle jaune de 3,5 blocs, "
                           "rouge à la fin), la surcharge éclate (8, repoussé) ; pendant 7 s il va 20 % plus vite et "
                           "frappe 15 % plus fort, mais encaisse 15 % de plus."),
    ],
    "moon_warden": [
        ("Balayage d'astrolabe", "1 à 3", "La lame droite ramenée en travers du corps (0,9 s, un arc tracé en argent) : "
                                          "elle balaie devant elle (13). Elle se tourne, l'arc rougit et la lame gauche "
                                          "balaie en retour 0,4 s plus tard (11). Aux phases de croissant, ce second coup "
                                          "lance un croissant de lumière qui file jusqu'à 13 blocs (7)."),
        ("Orbite", "1 à 3", "Bras écartés, l'orrery s'emballe (1,2 s) : trois spirales (cinq en phase 2) marquées en or, "
                            "rouges à la fin ; ses planètes filent le long de chacune (9)."),
        ("Puits de gravité", "1 à 3", "Ses lames pointées vers un point marqué loin du bord (1,4 s, un cercle violet de "
                                      "rayon 2,5 et la portée de 7 en pointillés) : pendant 0,8 s, tout le monde est "
                                      "attiré doucement (moins vite que la marche), puis le puits éclate (10)."),
        ("Bascule", "1 à 3", "Elle lève ses lames (1,1 s) : des cercles sous les joueurs les suivent puis se figent en "
                             "rouge ; la gravité bascule dedans : 7, tu flottes 1 s tout droit puis redescends en "
                             "chute lente, là où tu étais."),
        ("Nouvelle lune", "1 et 2", "Quand son cadran devient noir : des lignes d'ombre à travers la plateforme, une "
                                    "par joueur, rouges à la fin ; ses ombres foncent le long de chacune l'une après "
                                    "l'autre (9, ralenti 1 s)."),
        ("Pleine lune", "1 et 2", "Quand son cadran est plein : elle s'élève (1,5 s), puis un anneau radieux court sur "
                                  "la plateforme (10, saute-le) ; en phase 2, un second suit."),
        ("Comète", "2 et 3", "Elle s'élève, lames levées (1,5 s) : un cercle sous toi te suit puis rougit ; elle plonge "
                             "dessus (13)."),
        ("Appel du vide", "2 et 3", "Une lame levée vers le cœur (1 s) : larves du vide et poussières d'astre (deux, une de "
                                    "plus tous les deux joueurs), jamais plus de trois."),
        ("Éclipse", "3", "À 30 % : elle s'élève, bras croisés (2 s, invulnérable) ; le cœur s'assombrit, l'obscurité "
                         "tombe et un anneau sombre court (10, saute-le). Ensuite, trois rayons de gravité partent du "
                         "cœur et tournent lentement autour de la plateforme (tracés 2 s, des flèches montrent le sens) : "
                         "marche avec l'espace entre eux (5 au passage). Entre deux balayages, des météores tombent sur "
                         "des cercles marqués (8)."),
    ],
    "frost_commodore": [
        ("Ancre", "1 à 3", "L'ancre ramenée par-dessus l'épaule (0,9 s, un arc tracé en givre) : un coup en arc "
                           "devant lui (14). Il se tourne aussitôt, l'arc du revers est tracé en rouge, et il revient "
                           "en sens inverse 0,6 s plus tard (11). Phase 2 : il enchaîne parfois souffle ou jet de glace."),
        ("Lancer d'ancre", "1 à 3", "L'ancre tourne au-dessus de sa tête (1,2 s) ; une ligne de givre te suit puis "
                                    "rougit et se fige. L'ancre file le long d'elle (12), mord au bout (8 dans un "
                                    "cercle tracé pendant son vol), puis la chaîne la ramène le long de la même ligne, "
                                    "tracée en rouge : 10, ralenti et tiré vers lui. Sors de la ligne et n'y reviens pas."),
        ("Pics de glace", "1 à 3", "L'ancre levée haut puis plantée dans le pont (1 s) : trois lignes (cinq en "
                                   "phase 2) marquées depuis lui, l'une vers toi, rouges à la fin ; les pics jaillissent "
                                   "le long de chacune, un bloc par tick (12 et soulevé)."),
        ("Souffle glacial", "1 à 3", "Il renverse la tête, l'appareil le remplit de froid (1,5 s, un cône tracé qui "
                                     "te suit puis rougit), puis souffle par sa visière fêlée pendant 1 s : 4, ralenti "
                                     "et givre, quatre fois si tu restes dedans."),
        ("Blocs de glace", "1 à 3", "Il traîne l'ancre dans la glace puis la relève (1 s) : deux blocs (trois en "
                                    "phase 2) volent vers des cercles tracés, le premier sous toi ; ils éclatent "
                                    "(11) et laissent 5 s une plaque glissante de glace compactée."),
        ("Équipage gelé", "2 et 3", "Le pistolet levé (1 s), une fusée de détresse : deux vagabonds (une de plus "
                                   "tous les deux joueurs) montent sur le pont, jamais plus de trois."),
        ("Fusée", "2 et 3", "Le pistolet braqué sur toi (0,8 s, une ligne orange puis rouge) : une fusée file le "
                            "long d'elle et éclate sur le premier touché ou au bout (9 et enflammé)."),
        ("Blizzard", "3", "À 30 % : il ouvre en grand les soupapes de l'appareil (2 s, invulnérable) et frappe le "
                          "pont : une onde à sauter (10), il accélère. Le pont se couvre de neige et de givre "
                          "(léger ralentissement, pas de glissade) et des stalactites tombent du gréement toutes les "
                          "3 s sur des cercles marqués (rouges à la fin) : 10."),
        ("Coup de bélier", "3", "Toutes les 14 s environ : il plante l'ancre, la cloche du navire sonne trois fois "
                                "(1,5 s, le bout du pont côté proue tracé en rouge), puis le navire éperonne la "
                                "banquise : deux vagues roulent sur tout le pont de la proue à la poupe, à 1 s "
                                "d'écart (9 et poussé vers la poupe). Saute-les. Les stalactites attendent."),
    ],
    "strangler_queen": [
        ("Coup de fouet", "1 à 3", "Le fouet ramené en arrière (0,8 s, une ligne verte de 11 blocs), puis claqué "
                                   "droit devant (14) : il te ramène vers elle."),
        ("Combo de macuahuitl", "1 à 3", "Deux taillades en arc devant elle à 0,7 et 1,2 s (13 puis 13). Phase 2 : un "
                                         "estoc final à 1,7 s qui porte à 6,5 blocs (16)."),
        ("Racines en ligne", "1 à 3", "Mains plongées dans le sol (1 s) : trois lignes de racines (cinq en phase 2) "
                                      "jaillissent vers toi en éventail (12, projeté en l'air). Mets-toi entre deux "
                                      "lignes."),
        ("Anneaux de racines", "1 à 3", "Bras levés (1,1 s) : trois anneaux de racines jaillissent l'un après l'autre "
                                        "à 4, 8 puis 12 blocs (11). Phase 2 : une vague revient de l'extérieur vers elle."),
        ("Pollen", "1 à 3", "Elle secoue sa couronne (0,9 s) : des nuages de pollen doré (rayon 4,5) restent 8 s. "
                            "Dedans, la lenteur monte (I, II, III), puis au bout de 4 s tu es aveuglé et nauséeux (4). "
                            "Sors du nuage."),
        ("Liane", "1 à 3", "Fouet lancé vers une branche (0,8 s) : elle se balance jusqu'à toi (7 à 22 blocs) et "
                           "retombe (15)."),
        ("Épines", "1 à 3", "Quand tu restes collé à elle : des épines jaillissent autour d'elle (11, rayon 4,5). "
                            "Phase 2 : une onde jusqu'à 8 blocs (7)."),
        ("Tempête de fouet", "2 et 3", "Le fouet tourne autour d'elle (0,9 s) : deux tours (14) entre 2,5 et 9 blocs. "
                                       "Colle-toi à elle ou recule hors de portée."),
        ("Collet", "2 et 3", "Le fouet lancé en ligne (12 blocs, 0,9 s) : le premier pris est ramené à elle (8), puis "
                             "un revers de macuahuitl (16)."),
        ("Canopée", "2", "À 65 % puis environ toutes les 40 s de combat : elle grimpe dans le disque solaire, intouchable. "
                              "Des esprits-jaguars tombent (deux, plus en groupe), et des graines-bombes tombent sur "
                              "les joueurs marqués (13, rayon 2,5). Tue tous les esprits : elle chute plus tôt, "
                              "exposée (+30 % de dégâts 4 s)."),
        ("Chute", "2", "Après la canopée : un cercle suit sa cible puis se fige ; elle s'écrase dessus (17, rayon "
                            "3,5) et une onde roule (8, saute-la)."),
        ("Floraison", "3", "À 30 %, une fois (invulnérable 2,6 s) : une onde de croissance (13), puis elle accélère."),
        ("Cages de racines", "3", "Toutes les 12 s : jusqu'à quatre joueurs marqués, un cercle les suit 0,6 s puis "
                                  "se fige. Sors-en avant que la cage se referme (1,2 s). Pris, tu subis 6 puis 2 "
                                  "par seconde : casse les racines (vraies racines de palétuvier, retirées après "
                                  "7 s). Sinon elle vient moissonner la cage (18)."),
    ],
    "solar_hierarch": [
        ("Garde du miroir", "1 à 3", "Entre ses attaques (et pendant ses coups de bâton), le miroir pare tout coup de "
                                     "face et renvoie les projectiles au tireur. Frappe de côté ou de dos ; ou frappe "
                                     "le miroir : chaque coup paré le fend (les coups lourds davantage, plus il y a de "
                                     "joueurs plus il tient), et brisé il chancelle 1,5 s puis encaisse +30 % 2,5 s."),
        ("Riposte", "1 à 3", "Trois coups parés en 2 s : il te repousse d'un coup de bouclier (0,5 s, 9, lenteur)."),
        ("Balayage solaire", "1 à 3", "Le bâton armé sur l'épaule (0,7 s, l'arc tracé) puis balayé sur 150° (14). "
                                      "Phase 2 : il enchaîne une estocade ou le combo."),
        ("Estocade ardente", "1 à 3", "L'orbe ramené à la hanche (0,8 s, une ligne de 8,5 blocs) puis il fend à travers "
                                      "toi (16, feu)."),
        ("Combo du midi", "1 à 3", "Coup droit (0,7 s, 12), revers en se tournant vers toi (12), puis le bâton levé au "
                                   "ciel et abattu en ligne (17). Phase 2 : la frappe au sol lâche un anneau de feu."),
        ("Éclat du miroir", "1 à 3", "Le miroir levé vers la lentille (0,9 s, il s'embrase) : un cône de lumière de 12 "
                                     "blocs (8, feu). Si tu le regardes, tu es aveuglé 2,5 s. Un gnomon t'abrite."),
        ("Lance solaire", "1 à 3", "Il saute au centre et lève le miroir (1,5 s, la colonne du puits s'allume) : le "
                                   "rayon renvoyé par son miroir rampe vers toi un peu moins vite que tu ne marches "
                                   "pendant 6 s (5 par demi-seconde, feu). Un gnomon l'arrête. Phase 2 : un second "
                                   "rayon chasse un autre joueur, ou suit ta trace en écho si tu es seul."),
        ("Planétaire", "1 à 3", "Il saute au centre, le bâton au ciel (1,2 s) : ses planètes tracent des rayons qui "
                                "tournent autour de lui 4,5 s. L'anneau bas se saute (11), l'anneau haut ne se saute "
                                "pas : abrite-toi derrière un gnomon (14). Phase 2 : trois rayons, et à mi-course "
                                "le sens s'inverse (chevrons bleus pour prévenir)."),
        ("Éruption solaire", "2 et 3", "Le bâton planté (1 s) : trois anneaux de feu de 11 blocs à sauter (10 "
                                       "chacun)."),
        ("Descente", "2 et 3", "Il se ramasse (0,9 s) : un cercle te suit puis se fige, il bondit et retombe dessus "
                               "(18, rayon 3) avec une onde à sauter (8)."),
        ("Éclipse", "3", "À 30 %, invulnérable 2,5 s : la salle s'assombrit (ténèbres), une onde te repousse (12) et "
                         "il accélère. Une colonne de lumière erre dans la salle (4, feu)."),
        ("Sceaux solaires", "3", "Toutes les 11 s : six sceaux s'allument au sol et il saute de l'un à l'autre trois "
                                 "fois ; le prochain à s'embraser est celui où il apparaît, et une couronne de feu y "
                                 "éclate 0,4 s plus tard (13, rayon 4,5). Le troisième est le plus proche de toi."),
    ],
    "drowned_admiral": [
        ("Coups de sabre", "1 à 3", "Le sabre tiré sur l'épaule droite (0,7 s, l'arc tracé de rouille) : un coup droit, "
                                    "il se tourne vers toi, un revers 0,5 s plus tard (14 chacun)."),
        ("Estocade", "1 à 3", "Pieds plantés, la pointe ramenée à la hanche (0,8 s, une ligne de 9 blocs), puis il fend "
                              "à travers toi (16)."),
        ("Canon de pont", "1 à 3", "Le bras-canon levé (1,4 s) : un laser rouge te suit un peu moins vite qu'un pas de "
                                   "côté, puis se fige en jaune (déclic). L'obus éclate sur le premier joueur ou mur "
                                   "touché : 18 au centre, moitié à 3,5 blocs, projeté. Déplace-toi en travers."),
        ("Vannes des chaudières", "1 à 3", "Le sabre levé comme un signal (1,2 s) : des couloirs partent des foyers des "
                                           "chaudières vers les joueurs (ils te suivent puis se figent en blanc). Les "
                                           "vannes sautent : 13 et repoussé, puis la vapeur reste 2,5 s (4 par "
                                           "demi-seconde, ralenti). Deux couloirs, trois en phase 2, quatre en phase 3."),
        ("Grappin d'abordage", "1 à 3", "Le grappin tourne sous le canon (0,9 s, une chaîne grise vers toi, un cercle "
                                        "qui se fige) puis part en ligne droite : s'il te prend, 8 et tu es traîné à "
                                        "ses pieds, souvent suivi des coups de sabre. Sors de la ligne."),
        ("Botte de plomb", "1 à 3", "Une botte levée (0,6 s) puis abattue autour de lui (12, rayon 4). Phase 2 : un "
                                    "anneau d'eau à sauter."),
        ("Bordée", "2 et 3", "Trois tirs de canon visés à une seconde d'écart (15 chacun), le laser se refige avant "
                             "chacun."),
        ("Abordage", "2 et 3", "Coup droit, revers, puis il bondit sur l'endroit marqué en jaune et l'écrase (18, rayon "
                               "3) ; un anneau d'eau à sauter."),
        ("Charge", "2 et 3", "Casque baissé (0,8 s, une ligne de 14 blocs) il fonce (15). S'il heurte une chaudière ou "
                             "un mur, il chancelle 2 s (+30 % de dégâts) : place-toi devant une chaudière."),
        ("Sabordage", "3", "À 30 %, agenouillé (invulnérable 2,5 s), il plante le sabre dans le pont : la mer envahit "
                           "la chaufferie jusqu'aux genoux pendant 18 s (de la vraie eau, retirée ensuite). Tu pataug"
                           "es et ralentis, lui avance à pleine vitesse ; 2 à 4 marins noyés montent à l'abordage "
                           "selon le nombre de joueurs. Il recommence 12 s après chaque décrue."),
    ],
    "frost_jarl": [
        ("Bouclier", "1 à 3", "Entre deux attaques, son bouclier te fait face : les coups portés de face perdent 65 %. "
                              "Frappe pendant qu'il se reprend, ou par le flanc."),
        ("Taille", "1 à 3", "La hache levée sur l'épaule droite (0,9 s, l'arc est tracé de neige), puis une taille en "
                            "diagonale sur 130° (18 et givre). Recule hors de l'arc."),
        ("Coup de bouclier", "1 à 3", "Le bouclier levé droit devant (0,6 s), puis il pousse (12, projeté loin, "
                                      "ralenti) ; un bouclier levé est écarté 5 s. Ne reste pas collé à lui."),
        ("Souffle de glace", "1 à 3", "Il se cambre, la poitrine gonfle (1 s, le cône est tracé au sol), puis son "
                                      "souffle balaie de sa droite vers sa gauche 1,5 s : 4 tous les quarts de seconde "
                                      "et le froid te gagne. Passe dans son dos ou sors du cône par sa droite."),
        ("Pics de glace", "1 à 3", "La hache levée (1,1 s, la ligne marquée au sol), puis plantée : des pics jaillissent "
                                   "le long de la ligne (14), trois lignes en phase 2, et un pic sous toi (sous chaque "
                                   "joueur en phase 2) annoncé par un cercle qui te suit puis se fige."),
        ("Bond du jarl", "1 à 3", "Accroupi 1 s, un cercle te suit puis se fige ; il bondit et s'abat dessus 0,5 s plus "
                                  "tard (20) et une onde de givre roule (9). Sors du cercle, saute l'onde."),
        ("Huscarls gelés", "1 à 3", "Toutes les 32 s environ, la hache brandie au ciel : deux chevaliers squelettes "
                                    "sortent de la glace (trois en phase 3, plus à plusieurs), jamais plus à la fois."),
        ("Furie", "2 et 3", "Trois coups de suite, chacun annoncé : une taille (0,8 s), un revers 0,5 s plus tard, puis "
                            "un coup vertical en ligne 0,6 s après (20) qui fait jaillir trois pics. Il se tourne vers "
                            "toi entre les coups."),
        ("Givre éclaté", "2 et 3", "La hache plantée droite (1,1 s, cinq anneaux tracés au sol) : les anneaux de pics "
                                   "jaillissent l'un après l'autre vers l'extérieur (13), puis reviennent en phase 3. "
                                   "Tiens-toi entre deux anneaux."),
        ("Fimbulvetr", "3", "À 30 %, il s'agenouille (invulnérable) et plante sa hache : une onde de givre (12, saute-la) "
                            "et la salle gèle. Rester immobile te gèle (3 par seconde une fois gelé), et toutes les 7 s "
                            "le sol blanchit 1,2 s avant une pulsation (7) : saute à ce moment."),
        ("Blizzard", "3", "Toutes les 13 s : la hache tendue vers l'oculus (1,2 s), puis trois salves de pics tombent, "
                          "chacune annoncée par un cercle sous chaque joueur (14). Change de place à chaque salve."),
    ],
    "fourth_king": [
        ("Fléau", "1 à 3", "Trois coups de fléau devant lui : deux balayages en arc à 0,7 et 1,2 s (12 chacun), "
                           "puis un fracas en ligne à 1,7 s qui porte à 7 blocs (15). Phase 2 : il enchaîne parfois "
                           "un coup de sceptre ou le rayon haut."),
        ("Sceptre", "1 à 3", "Sceptre levé haut (1 s), puis abattu (20, rayon 3 devant lui). Phase 2 : une onde "
                             "jusqu'à 10 blocs (9)."),
        ("Rayon bas", "1 à 3", "Le disque s'allume (1,1 s), puis un rayon au ras du sol balaie l'arène de sa droite "
                               "vers sa gauche sur 100° (120° en phase 2) pendant 2 s (15, lenteur II). Saute-le "
                               "quand il passe : en l'air, il ne te touche pas."),
        ("Rayon haut", "1 à 3", "Le sceptre levé à hauteur de tête (1 s) : le rayon oscille à hauteur de poitrine sur "
                                "40° (50° en phase 2) pendant 1,5 s (16). Rien sous quoi se baisser : fais un pas "
                                "de côté hors de l'éventail, ou colle-toi à lui (moins de 2,5 blocs)."),
        ("Pluie de sable", "1 à 3", "Il lève les bras vers le plafond (0,9 s) : des cercles de sable marquent le "
                                    "sol sous toi et ailleurs, et le sable tombe 1,5 s plus tard (14, rayon 2,2, "
                                    "lenteur II et cécité). Phase 2 : un cercle sur chaque joueur et plus de cercles "
                                    "perdus. Le sable enterre les essaims de scarabées qu'il touche."),
        ("Essaim de scarabées", "1 à 3", "Il tend le sceptre (0,8 s) : un essaim noir et vert sort du sol et suit "
                                          "un joueur pendant 12 s (3 toutes les demi-secondes, poison et faim). Plus "
                                          "rapide en phase 2, deux à la fois. Attire-le sous une pluie de sable pour "
                                          "l'enterrer."),
        ("Procession", "1 à 3", "Quand tu t'éloignes (8 à 24 blocs) : il glisse vers toi sans marcher (12 au contact), "
                                "puis abat le fléau en ligne devant lui (16)."),
        ("Bourrasque de sable", "1 à 3", "Quand tu restes collé : il frappe le sol, le sable jaillit autour de lui "
                                          "(11, rayon 4,5). Phase 2 : une onde jusqu'à 8 blocs (7)."),
        ("Vases canopes", "1 à 3", "Quatre vases canopes (un de plus par joueur, six au plus) se dressent autour "
                                   "de l'arène. Toutes les 21 s environ, s'il est blessé, il s'agenouille et les "
                                   "draine pendant 2,5 s : chaque vase encore debout lui rend 3,5 % de ses PV (4,5 % "
                                   "en phase 2). Casse-les (un coup suffit). Ils reviennent à 65 %."),
        ("Le Tombeau scellé", "3", "À 30 %, il plante le sceptre (invulnérable 3 s) : les lanternes s'éteignent, les "
                                   "étoiles du plafond deviennent bleues, l'oculus se ferme et le noir tombe sur "
                                   "l'arène (obscurité), puis une onde jusqu'à 13 blocs (12, saute-la). Les esprits "
                                   "des trois autres rois apparaissent au bord de la salle, et il devient plus rapide."),
        ("Regards des rois", "3", "Les esprits balaient la salle de leur regard : un cône bleu à la fois entre deux "
                                  "jugements (6, coupe sa ligne de vue derrière une colonne ou le roi). Toutes les "
                                  "15 s, le Verdict : les trois esprits regardent en même temps et leurs cônes "
                                  "tournent dans la salle pendant 4 s (8, flétrissement). Reste dans l'angle mort "
                                  "entre deux cônes."),
    ],
    "colossus_heart": [
        ("Fauchage", "1 et 3", "L'espadon ramené par-dessus l'épaule droite (0,9 s, l'arc tracé en or), puis balayé "
                               "sur 210° jusqu'à 7,5 blocs (16). Recule hors de l'arc. Phase 3 : plus large, et "
                               "souvent suivi d'un coup d'espadon."),
        ("Coup d'espadon", "1 et 3", "L'espadon levé à deux mains (1,1 s, un cercle à 4 blocs devant lui et la ligne de "
                                     "la fissure en points d'or), planté dans le sol (20, rayon 2,8) ; une fissure "
                                     "court ensuite jusqu'à 16 blocs (13, projeté). Phase 3 : trois fissures en "
                                     "éventail."),
        ("Fente", "1 et 3", "Quand tu t'éloignes (5 à 15 blocs) : la lame ramenée à la hanche (0,8 s, la ligne tracée "
                            "sur 12 blocs), puis une fente qui le porte 9 blocs en avant (15). Pas de côté. Phase 3 : "
                            "souvent suivie d'un fauchage."),
        ("Plaque-bouclier", "1 et 3", "Il ramène la plaque-bouclier contre lui (0,9 s, sa boucle tracée en vert-de-gris "
                                      "au sol), puis la lance : elle file en boucle jusqu'à toi et revient (2 s, 12 à "
                                      "chaque passage). Sors de la boucle tracée. Phase 3 : deux boucles, la seconde "
                                      "en miroir."),
        ("Gravats", "1 à 3", "Les bras levés, le cœur qui flamboie (1 s) : des blocs s'arrachent aux murs du heaume au-"
                             "dessus de cercles qui suivent leurs joueurs 0,6 s puis se figent (ils rougissent) ; les "
                             "blocs sont lancés l'un après l'autre (13, rayon 2,5, projeté). Bouge dès que le cercle "
                             "rougit."),
        ("Aimant", "1 à 3", "Bras ouverts, le cœur qui enfle (0,7 s, un anneau de fer se resserre) : pendant 1,4 s, tout "
                            "joueur à 16 blocs (18 en phase 3) et tout objet au sol est attiré vers lui, plus fort pour "
                            "chaque pièce d'armure de métal portée ; puis tout se referme d'un coup (14 à 4,5 blocs, 16 "
                            "à 5 blocs quand ce sont les plaques). Cours à contre-sens, ou retire une pièce de fer."),
        ("L'éclatement", "2", "À 65 %, il rugit et son armure vole en éclats (invulnérable 1,5 s) : le cœur est à nu "
                              "(armure −8, il prend 35 % de dégâts en plus). Quatre plaques tournent autour de lui "
                              "entre 1,8 et 4,2 blocs (6 au contact) : frappe entre deux plaques."),
        ("Anneaux", "2", "Le cœur s'élève et glisse au centre du heaume (1 s, les deux premières bandes tracées en "
                         "rouge) : les plaques balaient les bandes de 2 à 5,5 et de 8,5 à 11,5 blocs pendant 1,75 s, "
                         "puis (0,7 s d'avertissement ambre) celles de 0 à 2, de 5,5 à 8,5 et au-delà de 11,5 pendant "
                         "1,5 s (10 par passage). Chaque anneau a une brèche de 70° qui tourne. Tiens-toi sur les "
                         "anneaux de tuf ciselé du sol pour la première vague, puis change de bande."),
        ("Pluie de plaques", "2", "Les plaques forment une couronne au-dessus du cœur (0,8 s), puis six plaques "
                                  "partent un quart de seconde l'une après l'autre, chacune le long d'une ligne tracée "
                                  "0,4 s avant vers un joueur (9 au premier touché). Fais un pas de côté à chaque "
                                  "ligne."),
        ("Purge", "2", "Quand tu restes collé : le cœur se contracte (0,7 s, un cercle ambre de 4 blocs), puis éclate "
                       "(14, repoussé), une onde de vapeur jusqu'à 9 blocs (8, saute-la) et des mites de rouille "
                       "sortent des fissures (2, plus en groupe, 4 au plus)."),
        ("La Reforge", "3", "À 30 %, les anneaux se referment sur le cœur (1,5 s, invulnérable) : l'armure se ressoude, "
                            "plus grande de 15 % et plus rapide, des fissures d'ambre sur chaque plaque ; un choc "
                            "autour de lui (12 à 5 blocs) et une onde à sauter (12, jusqu'à 14 blocs)."),
        ("Le heaume s'effondre", "3", "Toutes les 10 s environ, il plante l'espadon pointe en bas (0,9 s, 14 à 2,5 "
                                      "blocs devant lui) : le plafond lâche des blocs sur trois cercles autour de "
                                      "chaque joueur (un sur lui, deux près) et quelques cercles perdus, une demi-"
                                      "seconde plus tard (14, rayon 1,8, lenteur). Chaque chute laisse un tas de "
                                      "gravats 8 s, retiré ensuite et à la fin du combat."),
    ],
    "turbine_tyrant": [
        ("Balayage du rotor", "1 à 3", "Le rotor ramené à droite pendant qu'il siffle de plus en plus aigu (1,1 s, l'arc "
                                        "tracé de laiton), puis balayé sur 240° (16). Recule hors de l'arc."),
        ("Coup de clé", "1 à 3", "La clé hissée sur l'épaule (1 s, la ligne marquée), abattue devant lui (18) ; une "
                                 "fissure court sur 16 blocs (12, projeté) et fait sauter les grilles qu'elle croise. "
                                 "Trois fissures en phase 2."),
        ("Vapeur", "1 à 3", "Il tourne sa vanne (0,9 s) : les grilles du sol sifflent 1,2 s puis crachent 1,5 s (10, "
                            "puis 3 chaque quart de seconde). Une grille sur deux en phase 1, toutes sauf deux en phase 2."),
        ("Surpression", "1 à 3", "Il gonfle 2,3 s (la portée tracée de vapeur, les manomètres montent), puis tout "
                                 "explose autour de lui sur 16 blocs (19 en phase 2) : 22 et projeté. Cache-toi "
                                 "derrière un pilier ou un générateur, ou sors de la portée : seuls ceux qu'il voit "
                                 "sont touchés."),
        ("Bélier", "1 à 3", "Épaules baissées (0,8 s, sa course marquée), il charge 13 blocs (15)."),
        ("Piétinement", "1 à 3", "Si tu le colles : une jambe levée (0,6 s, un cercle de vapeur), puis un coup au sol "
                                 "(13, rayon 4,5)."),
        ("Broyeur", "2 et 3", "Rotor (14), coup de clé 0,6 s plus tard (16, une courte fissure), puis rotor dans "
                              "l'autre sens (14) ; il se tourne vers toi entre les coups."),
        ("Tourbillon", "2 et 3", "Le rotor levé comme un ventilateur (1 s) : il aspire tout le monde à 14 blocs pendant "
                                 "1,2 s, puis tournoie (16, rayon 4,8). Cours contre l'aspiration."),
        ("Cascade", "2 et 3", "Les grilles sautent l'une après l'autre autour de la salle, à partir de la plus proche "
                              "de toi ; en phase 3, une seconde vague repart dans l'autre sens."),
        ("Surchauffe", "3", "À 30 %, il s'agenouille (invulnérable 2,5 s) et tourne sa propre vanne : un anneau "
                            "d'étincelles roule (12, saute-le), il accélère et les grilles sautent seules toutes les 9 s."),
        ("Ruée", "3", "Toutes les 11 s : trois marques (sur les joueurs) reliées d'étincelles, puis il fonce de l'une "
                      "à l'autre en 2,25 s (14) et laisse des étincelles qui brûlent 4 s (3 et feu)."),
    ],
    "anvil_warden": [
        ("Frappe", "1 à 3", "Le marteau hissé sur l'épaule (0,9 s, le cercle et la ligne tracés de braises), abattu "
                            "devant lui (16, rayon 2,8) ; une onde de choc court sur l'enclume (10, projeté). Trois "
                            "ondes en éventail en phase 2."),
        ("Combo du marteau", "1 à 3", "Coup droit à 0,7 s puis revers à 1,2 s (13 chacun, feu). Phase 2 : un coup "
                                      "vertical en ligne à 1,7 s (16) qui fend l'enclume devant lui."),
        ("Pince", "1 à 3", "La pince ouverte et tendue (0,8 s, une ligne étroite de 5,5 blocs) : le premier pris "
                           "subit 8, est soulevé 0,6 s puis jeté (6) vers le milieu de l'enclume, jamais vers le bord."),
        ("Éclaboussure", "1 à 3", "Le creuset penché (1 s) : des dalles marquées (sur toi et à côté ; en phase 2 sur "
                                  "chaque joueur, plus des dalles au hasard) reçoivent du métal en fusion (12, feu) "
                                  "qui laisse une flaque brûlante 3 s (3 par demi-seconde)."),
        ("Trempe", "1 à 3", "Si tu le colles : le lingot plongé dans le seau (0,6 s), la vapeur jaillit (11, rayon 5) "
                            "et brûle 2 s. Phase 2 : des geysers sous les joueurs éloignés (9)."),
        ("Charge", "1 à 3", "Tête baissée (0,8 s, la course marquée), il fonce jusqu'à toi (14) puis remonte le "
                            "marteau (12, projeté)."),
        ("Séisme", "2 et 3", "Marteau et pince levés (1 s) : deux anneaux de choc à 0,6 s d'écart (10 chacun) : "
                             "saute-les tous les deux."),
        ("Lingot", "2 et 3", "Un cercle suit sa cible puis se fige (0,9 s) ; le lingot ardent y éclate (13, feu, une "
                             "flaque). En phase 3, il rebondit 5 blocs plus loin."),
        ("Marteau du titan", "1 à 3", "Quelques fois par phase : il lève le marteau vers le titan et frappe trois fois "
                                      "sa pince (2 s). La zone sous le marteau géant est cerclée de rouge, des scories "
                                      "en tombent ; puis le marteau s'abat (26, feu) et une onde roule depuis le bord "
                                      "jusqu'à 17 blocs (8, saute-la). Loin de la forge, la zone se pose autour de sa "
                                      "cible."),
        ("Surchauffe", "3", "À 30 %, une fois (invulnérable 2,6 s) : il boit son creuset, l'enclume rougit, une onde "
                            "de feu (12) ; il accélère et laisse une traînée de flaques brûlantes."),
        ("Purge", "3", "Toutes les 15 s environ : bras croisés, le creuset déborde (2 s, la portée de 14 blocs "
                       "cerclée de rouge), puis une nappe de vapeur et de scories rase l'enclume (20, feu). Abrite-toi "
                       "derrière la racine de la bigorne, les doigts du titan ou un brasero, ou sors de la portée."),
    ],
    "storm_ascetic": [
        ("Combo du bâton", "1 à 3", "Le bâton ramené sur l'épaule droite (0,7 s, l'arc tracé de vent), un large "
                                    "balayage (15), puis il se tourne vers toi et porte un long coup d'estoc le long "
                                    "d'une ligne marquée (14, 9 blocs). Recule hors de l'arc, puis écarte-toi de la ligne."),
        ("Saut à la perche", "1 à 3", "Il plante le bâton (1 s) : un cercle te suit puis se fige, il saute et retombe "
                                      "dessus (16), et un anneau de vent roule (8). Sors du cercle, saute l'anneau."),
        ("Rafale", "1 à 3", "La paume tendue (0,9 s : le cône est tracé, et un anneau de nuages près des murs), puis le "
                            "vent souffle 1,2 s et te pousse loin de lui (5). Il ne te pousse jamais au-delà de l'anneau."),
        ("Appel de la foudre", "1 à 3", "Le bâton levé au ciel (1,1 s) : des cercles suivent chaque joueur puis se "
                                        "figent ; la foudre tombe dessus (14). En phase 2, une seconde salve 0,7 s plus "
                                        "tard là où tu es allé."),
        ("Chapelet", "1 à 3", "Les grains tournent plus vite (0,8 s), puis il les lance en éventail vers toi ; chacun va "
                              "à 14 blocs et revient vers lui (7 à l'aller, 7 au retour)."),
        ("Moulinet", "1 à 3", "Si tu le colles : un cercle à 4,5 blocs (0,6 s), puis un tour complet du bâton (13)."),
        ("Reflets", "2 et 3", "Il tourbillonne (1 s) pendant que trois cercles de nuages se tracent autour de toi ; il "
                              "réapparaît sur l'un d'eux, deux reflets sur les autres. Un reflet meurt au moindre "
                              "coup ; ils frappent moins fort et disparaissent après 16 s."),
        ("Tempête", "2 et 3", "Trois coups : un balayage (14), un revers (13), puis le bâton abattu le long d'une ligne "
                              "marquée (18) qui appelle trois éclairs (12)."),
        ("Cyclone", "2 et 3", "Le bâton tournoie au-dessus de sa tête (1 s) : le vent t'attire vers lui 1 s, puis un "
                              "anneau de vent roule (12). Saute-le."),
        ("La grande cloche", "3", "À 30 %, il s'agenouille (invulnérable) et frappe le sol : la cloche répond, un anneau "
                                  "de tonnerre roule depuis le centre (8). Ensuite elle sonne seule toutes les 8 s "
                                  "environ (annoncée par des étincelles au centre) : saute chaque anneau (9)."),
        ("Tonnerre", "3", "Toutes les 15 s environ : le bâton levé (1 s), puis la cloche sonne trois fois et trois "
                          "anneaux roulent depuis lui (11)."),
    ],
}
# Difficulté des boss (bestiaire) : coop et cycles NG+ (boss/WayfarerBoss, tools/BOSSES.md)
BOSS_DIFFICULTY = ("Plus on est, plus ils sont durs : chaque joueur de plus dans l'arène donne au boss +75 % de vie, "
                   "+10 % de dégâts et +25 % de posture ; à plusieurs il attaque plus souvent et appelle plus "
                   "d'acolytes. Si quelqu'un rejoint le combat en cours, le boss se renforce (jamais l'inverse). "
                   "Chaque boss vaincu revient plus fort dans ce monde : c'est son cycle, affiché « +1 », « +2 »… "
                   "jusqu'à +7 dans sa barre de vie. À chaque cycle : +35 % de vie, +15 % de dégâts, +2 d'armure et des "
                   "attaques plus vives (toujours annoncées). Dès +2, en phase 2, il lâche régulièrement une onde "
                   "d'âmes à sauter. En échange, son butin est tiré une fois de plus par cycle, et dès +3 il peut "
                   "lâcher une Braise d'ascension : posée sur une enclume avec une arme de boss, elle lui donne +1 de "
                   "dégâts (jusqu'à +5).")

BOSS_FACTS = {
    "grand_clockmaker": "400 PV, armure 12, barre jaune. Phase 2 à mi-vie : il rugit, des étincelles crépitent sur "
                        "lui, il accélère et enchaîne ses coups.",
    "iron_helmsman": "450 PV, armure 15, posture 95, barre blanche. Phase 2 à mi-vie : la corne sonne, il fume et "
                     "flambe, accélère et enchaîne ses coups.",
    "bronze_sentinel": "460 PV, armure 14, posture 100, barre verte. Phase 2 à mi-vie : ses plaques tombent "
                       "(armure −6), il accélère de 20 % et enchaîne ses coups.",
    "dune_king": "460 PV, armure 10, posture 85, barre jaune. Phase 2 à mi-vie : il s'élève et flotte au-dessus du "
                 "sol, accélère et ouvre les sables.",
    "fallen_seraph": "780 PV, armure 14, posture 110, barre violette. Phase 2 à 60 % : elle rugit, s'élève et "
                     "accélère. Phase 3 à 25 % : le disque se fissure, son bord s'effrite et le ciel tombe. Aucun "
                     "coup ne te projette vers le vide près du bord.",
    "chained_jailer": "600 PV, armure 14, posture 100, barre rouge. Phase 2 à 60 % : il rugit, accélère et enchaîne "
                      "ses coups. Phase 3 à 30 % : il brise ses chaînes, va encore plus vite, brûle au contact et "
                      "lance le verdict.",
    "oathbound_gatekeeper": "480 PV, armure 14, posture 110, barre bleue. Son pavois bloque les coups de face : "
                            "contourne-le. Phase 2 à 65 % : la cloche de la porte sonne, il accélère et appelle les "
                            "mains de pierre. Phase 3 à 30 % : il s'agenouille ; brise son Bouclier du Serment.",
    "caldera_castellan": "520 PV, armure 15, posture 105, barre rouge. Phase 2 à 60 % : il rugit, accélère, enchaîne "
                         "ses coups et dresse des murs d'obsidienne (toujours temporaires). Phase 3 à 30 % : il puise "
                         "la chaleur du volcan et fait entrer les cheminées du sol en éruption ; après chaque éruption "
                         "son armure est fragile 3 s.",
    "tide_abbess": "560 PV, armure 12, posture 105, barre verte. Phase 2 à 65 % : elle rugit, accélère, double ses "
                   "vagues et fait jaillir des geysers. Phase 3 à 30 % : elle inonde la rotonde (de la vraie eau, "
                   "retirée à la fin du combat) et nage beaucoup plus vite que toi.",
    "lock_master": "600 PV, armure 14, posture 120, barre jaune. Sa vanne pare les coups de face quand il avance "
                   "derrière : un coup lourd ou un coup dans le dos la brise. Phase 2 à 65 % : il rugit, accélère et "
                   "enchaîne. Phase 3 à 30 % : il ouvre les vannes, un courant balaie la citerne et il charge. Ses "
                   "grilles sont toujours temporaires.",
    "bog_hierophant": "600 PV, armure 12, posture 110, barre verte. Phase 2 à 65 % : il rugit, allume huit "
                      "lanternes et se change en feu follet pour frapper dans le dos. Phase 3 à 30 % : le gaz des "
                      "marais s'embrase en lignes de feu. La boue et les lanternes qu'il pose sont retirées à la fin "
                      "du combat.",
    "star_curator": "780 PV, armure 14, posture 125, barre violette. Phase 2 à 65 % : il rugit, accélère, enchaîne, "
                    "déchaîne la tempête de pages et trace des constellations. Phase 3 à 30 % : la gravité du cratère "
                    "s'inverse, des pulsations soulèvent ceux qui ne sont pas près d'un brasier de cristal et il saute "
                    "de brasier en brasier. Il ne pose aucun bloc ; chaque lévitation finit en chute lente au-dessus "
                    "du sol.",
    "chime_abbot": "560 PV, armure 12, posture 110, barre rose. Phase 2 à 65 % : il rugit, accélère, enchaîne, "
                   "ajoute la rafale et la chute de cloche, et ses carillons sonnent dans les deux sens. Phase 3 à "
                   "30 % : il éveille le dragon d'airain de la pagode, dont le fantôme souffle des couloirs à travers "
                   "le pont. Il ne pose aucun bloc, et près de la balustrade ses coups ne te poussent jamais vers le "
                   "vide.",
    "mine_baron": "600 PV, armure 12, posture 130, barre jaune. Phase 2 à 65 % : il rugit et se cuirasse de "
                  "minerai (un cinquième des dégâts) ; frappe les géodes d'or de son dos pour la briser. Phase 3 à "
                  "30 % : il fait sauter les étais, la caverne s'éteint, il accélère et le filon crépite. Les lampes "
                  "éteintes et les lumières de sa lanterne et des mèches sont temporaires : tout revient à la fin "
                  "du combat, à sa mort ou si tout le monde s'en va. La dynamite ne casse aucun bloc.",
    "corsair_captain": "580 PV, armure 10, posture 115, barre blanche. Phase 2 à 65 % : elle rugit, appelle des "
                       "pillards du ciel, ajoute l'abordage et le cyclone. Phase 3 à 30 % : le navire gîte, des "
                       "couloirs de vent balaient le pont et ses bombes éclairantes laissent du feu. Ses poussées "
                       "ne te jettent jamais par-dessus le bastingage. Le feu est fait de blocs de magma temporaires, "
                       "remis en planches au bout de 5 s, à la fin du combat ou si tout le monde s'en va.",
    "hollow_cantor": "640 PV, armure 12, posture 115, barre blanche. Phase 2 à 65 % : il rugit, accélère un peu et "
                     "ajoute silence, chœur et fugue. Phase 3 à 30 % : l'orgue se réveille, les souffles de tuyau "
                     "et le requiem. Les bourgeons d'améthyste de la résonance sont temporaires (ils ne lâchent rien) "
                     "et retirés à la fin du coup, du combat, à sa mort ou si tout le monde s'en va ; les choristes "
                     "aussi.",
    "soul_stoker": "620 PV, armure 14, posture 130, barre bleue, insensible au feu. Phase 2 à 65 % : il rugit, "
                   "accélère, ajoute la charge et ses serviteurs squelettes wither, projette plus de braises et "
                   "ouvre plus d'évents. Phase 3 à 30 % : la surpression, le rythme du vilebrequin sur le pont et "
                   "les anneaux des soupapes. Il ne pose aucun bloc, et près du bord et de la tranchée ses coups ne "
                   "te poussent jamais dans le vide.",
    "asylum_director": "600 PV, armure 12, posture 110, barre blanche. Phase 2 à 65 % : elle rugit, accélère et "
                       "ajoute pince, dissection et glissement. Phase 3 à 30 % : minuit, puis les aiguilles de la "
                       "grande horloge. Elle ne pose aucun bloc ; ses araignées disparaissent à sa mort, si le combat "
                       "repart ou si tout le monde s'en va, et un retour en arrière en attente est annulé.",
    "spore_alchemist": "620 PV, armure 11, posture 105, barre verte. Phase 2 à 65 % : il rugit, accélère, ajoute le "
                       "voile de spores et ses bogged, plus de fioles et de pousses. Phase 3 à 30 % : la floraison, les "
                       "évents, le champ de mycélium et l'expiration. Ses seuls blocs sont les champignons des pousses, "
                       "retirés au bout de 6 s, à sa mort, si le combat repart ou si tout le monde s'en va ; ses coups "
                       "ne te poussent jamais vers une cage d'escalier ni vers le bord du chapeau.",
    "lumber_jarl": "660 PV, armure 13, posture 120, barre rouge. Phase 2 à 65 % : il rugit, accélère, appelle son "
                   "équipe, lance deux lames et fait tomber plus de troncs. Phase 3 à 30 % : la machine à balancier "
                   "s'emballe, étincelles du volant et jets de vapeur, et sa tronçonneuse porte plus loin. Il ne pose "
                   "aucun bloc (les troncs qui tombent et roulent disparaissent) ; ses coups ne te poussent jamais "
                   "contre le garde-corps ni par-dessus.",
    "thorn_gardener": "650 PV, armure 12, posture 115, barre verte. Phase 2 à 65 % : il rugit, accélère, ajoute "
                      "l'appel du jardin et le pollen. Phase 3 à 30 % : la lampe solaire s'allume, ses rayons balaient "
                      "la feuille et il se nourrit de lumière. Ses seuls blocs sont les buissons d'épines, retirés au "
                      "bout de 5 s, à sa mort, si le combat repart ou si tout le monde s'en va ; ses coups ne te "
                      "poussent jamais contre le rebord ni dans l'eau.",
    "abyss_diver": "660 PV, armure 13, posture 120, barre bleue. Phase 2 à 65 % : il rugit, accélère, ajoute le nuage "
                   "de vase et l'appel de l'équipage, plus de rivets. Phase 3 à 30 % : la coque gémit, les pics de "
                   "pression, les méduses lumineuses et la surcharge. Il ne pose ni ne casse aucun bloc (la salle est "
                   "une poche d'air sous la mer) ; ses noyés disparaissent à sa mort ou si le combat repart, et ses "
                   "coups ne te poussent jamais contre le mur, les vérins ou les tas de déblais.",
    "moon_warden": "720 PV, armure 12, posture 120, barre violette. Phase 2 à 65 % : elle rugit, accélère, ajoute la "
                   "comète et l'appel du vide. Phase 3 à 30 % : l'éclipse, les rayons de gravité tournants et les "
                   "météores. Ses seuls blocs sont les lanternes du cœur, assombries pendant l'éclipse et rallumées "
                   "à sa mort, si le combat repart ou si tout le monde s'en va ; autour du vide, ses coups ne te "
                   "repoussent jamais vers le bord : ils t'attirent vers le centre.",
    "frost_commodore": "640 PV, armure 13, posture 120, barre blanche. Phase 2 à 65 % : il rugit, accélère, "
                       "ajoute la fusée et son équipage gelé, plus de pics et de blocs de glace. Phase 3 à 30 % : le "
                       "blizzard, les stalactites et le coup de bélier. Ses seuls blocs sont les plaques de glace "
                       "compactée, remises en place au bout de 5 s, à sa mort, si le combat repart ou si tout le monde "
                       "s'en va ; ses coups ne te poussent jamais contre le bastingage ni par-dessus.",
    "strangler_queen": "620 PV, armure 12, posture 115, barre verte. Phase 2 à 65 % : elle rugit, accélère, ajoute "
                       "fouet tournant et collet et grimpe dans le disque solaire d'où tombent esprits-jaguars et "
                       "graines-bombes. Phase 3 à 30 % : la floraison, puis des cages de racines se referment sur les "
                       "joueurs marqués. Ses reculs près du bord de la terrasse sont plafonnés. Les racines de ses "
                       "cages sont temporaires et retirées à la fin du combat ou si tout le monde s'en va.",
    "solar_hierarch": "620 PV, armure 12, posture 115, barre jaune. Son miroir pare les coups de face et renvoie "
                      "les projectiles tant qu'il n'est pas brisé. Phase 2 à 65 % : il rugit, accélère, enchaîne, "
                      "bondit et double ses rayons. Phase 3 à 30 % : l'éclipse, la salle s'assombrit et il saute de "
                      "sceau en sceau. Les six gnomons de grès qu'il dresse sont temporaires et retirés à la fin du "
                      "combat ou si tout le monde s'en va.",
    "drowned_admiral": "620 PV, armure 12, posture 115, barre bleue. Phase 2 à 65 % : il rugit, accélère, enchaîne "
                       "ses coups, tire des bordées et charge. Phase 3 à 30 % : il saborde le navire, la chaufferie "
                       "s'inonde à hauteur de genou (eau temporaire, retirée à chaque décrue et à la fin du combat) et "
                       "des marins noyés montent à bord.",
    "frost_jarl": "540 PV, armure 14, posture 110, barre bleue. Son bouclier pare les coups de face entre ses "
                  "attaques. Phase 2 à 65 % : il rugit, accélère et enchaîne ses coups. Phase 3 à 30 % : il gèle la "
                  "salle, le sol pulse et le blizzard tombe.",
    "fourth_king": "640 PV, armure 12, posture 120, barre bleue. Phase 2 à 65 % : il rugit, accélère, les vases "
                   "reviennent, les rayons s'élargissent et les coups s'enchaînent. Phase 3 à 30 % : le tombeau se "
                   "scelle dans l'obscurité et les esprits des trois autres rois balaient la salle de leur regard. "
                   "Les vases, le noir des lanternes, les étoiles bleues et l'oculus fermé sont temporaires et "
                   "restaurés à la fin du combat ou si tout le monde s'en va.",
    "colossus_heart": "640 PV, armure 14, posture 120, barre jaune. Phase 2 à 65 % : l'armure éclate, le cœur est à "
                      "nu (armure −8, +35 % de dégâts reçus) et les plaques tournent autour de lui. Phase 3 à 30 % : "
                      "l'armure se ressoude, plus grande et plus rapide, et le heaume s'effondre sur les joueurs. Les "
                      "tas de gravats sont temporaires (8 s) et retirés à la fin du combat ou si tout le monde s'en va ; "
                      "les blocs lancés ne se posent jamais.",
    "turbine_tyrant": "600 PV, armure 14, posture 115, barre jaune. Phase 2 à 65 % : il rugit, accélère, enchaîne "
                      "ses coups et son explosion porte plus loin. Phase 3 à 30 % : il surchauffe, les grilles "
                      "sautent seules et il fonce à travers la salle. Il ne pose aucun bloc.",
    "anvil_warden": "640 PV, armure 14, posture 130, barre rouge, insensible au feu. Phase 2 à 65 % : il rugit, "
                    "accélère, triple ses ondes et ajoute séisme, lingot et geysers ; le marteau du titan tombe plus "
                    "souvent. Phase 3 à 30 % : il surchauffe, laisse des flaques de feu et purge l'enclume. Près du "
                    "bord, ses coups ne te jettent jamais dans la lave. Il ne pose aucun bloc.",
    "storm_ascetic": "580 PV, armure 12, posture 100, barre jaune. Phase 2 à 65 % : il rugit, accélère et se "
                     "dédouble en reflets. Phase 3 à 30 % : la grande cloche répond et sonne seule, anneau après "
                     "anneau. Aucun coup ne te projette dehors près du bord : l'arène est un sommet.",
}

# Descente vers un repaire : étapes dans l'ordre
LAIRS = {
    "star_curator": [
        ("La Bibliothèque de la chute d'étoile", "Traverse la galerie brisée sur les livres flottants jusqu'au dos de "
                                                 "la météorite."),
        ("La vrille", "Un escalier en vrille descend 36 blocs dans la météorite (géode d'améthyste au deuxième "
                      "tour), puis un tunnel passe sous la place jusqu'au lieu de grâce."),
        ("Le cratère", "L'arène : une chambre de 17 blocs de rayon sous un dôme de 13 à 19 blocs, quatre braseros "
                       "de lumière stellaire couronnés d'améthyste (les nœuds de cristal), un éclat de météorite dans "
                       "le mur sud-est, l'oculus au-dessus. Le Conservateur se réveille quand tu approches du sceau."),
        ("La réserve interdite", "Derrière des barreaux scellés à l'ouest ; son tube pneumatique remonte à la salle "
                                 "des cartes."),
    ],
    "chime_abbot": [
        ("Les jardins", "Du camp des pèlerins (pierre de passage), la porte de lune et le pont des carpes mènent aux "
                        "terrasses ; le sanctuaire du dragon est le lieu de grâce."),
        ("La pagode", "Huit étages, une salle par étage : prière, rouleaux, armurerie, méditation (lieu de grâce), "
                      "orrery, appartements de l'abbé, moteur des carillons, puis le dernier escalier (lieu de "
                      "grâce)."),
        ("Le pont du neuvième toit", "L'arène : un pont ouvert de 33 blocs de côté sous le neuvième toit, une "
                                     "balustrade tout autour, quatre piliers aux coins. Passé la brume en haut de "
                                     "l'escalier, l'Abbé se réveille quand tu approches du sceau au centre."),
        ("Le caveau", "Derrière des barreaux scellés, l'escalier descend au caveau ; le puits du contrepoids ramène "
                      "à la salle de prière."),
    ],
    "mine_baron": [
        ("La ville", "Depuis le relais de diligence (pierre de passage), monte la grand-rue et les terrasses jusqu'à "
                     "la salle des treuils au sommet (lieu de grâce)."),
        ("La descente", "Le bocard, le niveau 15 (dynamite, bureau du patron), le niveau de roulage (pierre), la "
                        "galerie noyée et le puits effondré jusqu'à l'antichambre (pierre)."),
        ("La caverne du filon", "L'arène : une caverne d'environ 21 blocs de rayon sous un dôme de 21 blocs, un filon "
                                "d'or et de cuivre penché au milieu, des échafaudages, un derrick et des étais tout "
                                "autour, huit lanternes suspendues. Passé la brume, le Baron se réveille quand tu "
                                "approches du sceau."),
        ("La chambre forte", "À l'est, derrière des barreaux scellés qui s'ouvrent à sa mort ; le monte-wagon ramène "
                             "en haut."),
    ],
    "corsair_captain": [
        ("Le camp et le marché", "Depuis le camp des ferrailleurs (pierre de passage), traverse l'épave en squelette de "
                                 "baleine jusqu'au marché (pierre), puis la salle du treuil au pied du mât."),
        ("Le mât", "L'escalier du mât monte à l'anneau d'amarrage ; la passerelle entre dans le nez du dirigeable."),
        ("La nacelle", "Passerelle de commandement, cabines, cale ; le puits d'escalade remonte à travers les "
                       "ballonnets jusqu'au lieu de grâce, puis un escalier étroit jusqu'au rouf et à la brume."),
        ("Le pont supérieur", "L'arène : le pont à ciel ouvert du dirigeable amarré (42 x 35), un bastingage de deux "
                              "blocs tout autour, quatre manches à air pour s'abriter. La Capitaine se réveille quand "
                              "tu approches du sceau."),
        ("La soute au trésor", "À l'ouest, derrière des barreaux scellés ; la passerelle sur l'échine de l'enveloppe "
                               "mène à l'ascenseur du mât, qui redescend à la salle du treuil."),
    ],
    "hollow_cantor": [
        ("La cathédrale", "Depuis le camp des pèlerins (pierre de passage), le parvis, la loge de la tour, la nef et "
                          "la croisée (lieu de grâce)."),
        ("La descente", "Le triforium est, le pont d'arc-boutant vers le dortoir des choristes, l'escalier de roche, "
                        "le couloir et la crypte inondée (pierre), puis l'escalier de la tourelle du chœur."),
        ("Le chœur et l'abside", "L'arène : le sol du chœur et de l'abside (rayon 15 autour du sceau, devant la "
                                 "console), des rides de laiton dans le sol, les tuyaux de l'orgue qui montent de 60 "
                                 "blocs derrière. Passé la brume, le Chantre se réveille quand tu approches du sceau."),
        ("Le reliquaire", "Derrière l'orgue, au bout du passage sous les grands tuyaux, derrière des barreaux scellés "
                          "qui s'ouvrent à sa mort ; la grille du chœur ouvre le raccourci vers la croisée."),
    ],
    "soul_stoker": [
        ("Le Moteur des âmes", "Depuis le camp des pèlerins perdus (pierre de passage) sur le sable des âmes, la route "
                               "d'os et la porte d'os jusqu'au hall de pression (pierre de passage)."),
        ("Les entrailles", "La trémie à os, le bunker de terre des âmes, le hall des fourneaux d'âmes, le grand "
                           "escalier jusqu'au balcon des chauffeurs, la salle du régulateur, puis l'escalier en "
                           "vis dans une chemise de piston jusqu'au lieu de grâce sur le carter."),
        ("Le pont du vilebrequin", "L'arène : 39 blocs de côté sous le toit du carter (16 blocs de haut), la "
                                   "tranchée du vilebrequin et ses six bielles au nord derrière une balustrade, la "
                                   "baie du volant à l'est. Passé la brume, le Chauffeur se réveille quand tu "
                                   "approches du sceau au centre."),
        ("Le reliquaire", "Derrière des barreaux scellés dans le mur ouest, ouverts à sa mort ; la chute d'os ramène "
                          "au hall de pression."),
    ],
    "asylum_director": [
        ("L'asile", "Du camp des bûcherons (pierre de passage), la grille, le cimetière, le grand escalier et le "
                    "grand hall (pierre de passage) ; l'aile ouest, le théâtre opératoire et la salle de conversion "
                    "ramènent à la galerie du hall."),
        ("La tour de l'horloge", "Cinq étages de mécanisme autour du puits du pendule : salle de remontage du bas, "
                                 "échappement, rouages, grande roue, puis la salle de remontage (lieu de grâce)."),
        ("L'étage de l'horloge", "L'arène : une salle de 35 blocs de côté et 18 de haut derrière les quatre cadrans, "
                                 "le sud fendu, un sol dessiné en cadran. Passé la brume en haut du dernier escalier, "
                                 "la Directrice se réveille quand tu approches du sceau au centre."),
        ("Le bureau de la directrice", "Dans l'oriel nord, derrière des barreaux scellés ; son puits privé "
                                       "redescend vers la salle de remontage du bas."),
    ],
    "spore_alchemist": [
        ("Le sommet de l'amanite", "L'arène : le dessus plat du chapeau de la grande amanite, environ 42 blocs de "
                                   "large, ciel ouvert, une clôture de laiton et des lampes-champignons tout autour, "
                                   "un anneau doré incrusté au milieu et deux ouvertures d'escalier bordées de garde-"
                                   "corps (la rampe d'arrivée et l'escalier du coffre). Passé la brume au sommet de la "
                                   "rampe, l'Alchimiste se réveille quand tu approches du sceau."),
    ],
    "lumber_jarl": [
        ("Le sommet du donjon", "L'arène : la plate-forme de bois de 49 blocs au sommet du donjon, bordée d'un "
                                "garde-corps de laiton, autour de la machine à balancier (son volant, son cylindre, ses "
                                "colonnes), avec deux cages d'escalier, une flèche et une cheminée aux angles. Passé "
                                "la brume de la cage d'escalier sud-ouest, le Jarl se réveille quand tu approches du "
                                "sceau."),
    ],
    "thorn_gardener": [
        ("La feuille de nénuphar", "L'arène : un nénuphar géant de 33 blocs de large au rebord rouge relevé, sur un "
                                   "pilier de laiton au milieu du bassin de la serre, sous la lampe solaire suspendue "
                                   "à la couronne du dôme. Passé la brume de la porte de la corniche et le pont de la "
                                   "nervure, le Jardinier se réveille quand tu approches du sceau."),
    ],
    "abyss_diver": [
        ("La chambre de forage", "L'arène : au fond de la tranchée, sous le dôme-verrière de laiton, une salle ronde de "
                                 "34 blocs, le train de tiges du derrick suspendu au-dessus du puits de forage "
                                 "rougeoyant, quatre vérins hydrauliques et des tas de déblais contre le mur. Passé la "
                                 "brume du couloir de compression, le Scaphandrier se réveille quand tu approches du "
                                 "sceau."),
    ],
    "moon_warden": [
        ("La plateforme du cœur", "L'arène : la plateforme du cœur de la Lune creuse (34 blocs de large, une rambarde de "
                                  "laiton sur le vide), sous le cœur lumineux de la machine. Passé l'anneau 3 et la "
                                  "brume, la Gardienne s'éveille quand tu approches du sceau."),
    ],
    "frost_commodore": [
        ("Le gaillard d'avant", "L'arène : le pont du gaillard du brise-glace, environ 34 blocs de large, la "
                                "passerelle à l'arrière, la proue devant, un bastingage de deux blocs tout autour ; le "
                                "pont gîte un peu sur tribord. Passé la brume au pied de l'escalier de la passerelle, "
                                "le Commodore se réveille quand tu approches du sceau."),
    ],
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
    "iron_helmsman": [
        ("Le cratère", "Entre par la brèche d'un des deux pieds posés de la Forteresse marchante."),
        ("La jambe", "L'escalier en colimaçon monte dans le tibia jusqu'à la salle du genou, puis l'escalier de la "
                     "cuisse mène à la cale."),
        ("Les ponts", "La salle des machines, puis le pont des canons et son armurerie ; l'escalier central monte "
                      "derrière l'arène."),
        ("Le pont supérieur", "Derrière la brume : une arène à ciel ouvert de 15 blocs de rayon, à près de 90 blocs "
                              "au-dessus du cratère, entre la tour de commandement et les deux cheminées. Le "
                              "Timonier se réveille quand tu approches du sceau."),
        ("La salle forte", "Dans la tour de commandement, derrière des barreaux scellés qui s'ouvrent à sa mort."),
    ],
    "bronze_sentinel": [
        ("Le poignet brisé", "Entre par la main tendue du Colosse abattu : le tunnel de l'avant-bras mène à la salle "
                             "du coude, puis l'escalier du bras monte au balcon de la salle des côtes."),
        ("La salle des côtes", "Une voûte de 30 blocs ouverte sur le ciel. Descends l'escalier jusqu'au sol : sous la "
                               "brèche, la Sentinelle se réveille quand tu approches de son sceau (pas de brume : "
                               "elle se rendort si tout le monde s'éloigne)."),
        ("Le gorgerin", "Le grand escalier remonte au gorgerin et à sa pierre de voyage (le lieu de grâce) ; au-delà, "
                        "le cou mène au heaume du Cœur du Colosse."),
    ],
    "colossus_heart": [
        ("Le poignet brisé", "Entre par la main tendue du Colosse abattu : le tunnel de l'avant-bras mène à la salle "
                             "du coude, puis l'escalier du bras monte au balcon de la salle des côtes."),
        ("La salle des côtes", "Une voûte de 30 blocs ouverte sur le ciel, gardée par la Sentinelle d'airain. Le "
                               "grand escalier remonte au gorgerin et à sa pierre de voyage (le lieu de grâce)."),
        ("Le cou", "Un tunnel étroit mène dans le heaume, derrière la brume."),
        ("Le heaume", "L'arène : une salle ronde d'environ 14 blocs de rayon et 13 de haut au centre sous les "
                      "barreaux de la visière, deux anneaux de tuf ciselé au sol, braseros autour. Le Cœur se "
                      "réveille quand tu approches du sceau."),
        ("La salle forte", "Sous le sol de l'arène, derrière des barreaux scellés qui s'ouvrent à sa mort ; une "
                           "porte de fer ressort par la joue."),
    ],
    "fourth_king": [
        ("La place cachée", "Au bout du canyon, passe le portail entre les quatre rois assis : la salle hypostyle."),
        ("Les tombeaux", "Trois niveaux descendent : salle d'embaumement et galerie des niches, puis galerie "
                         "inondée, couloir piégé et trésor."),
        ("Le lieu de grâce", "Tout en bas (y −37) : pierre de voyage, puis un couloir étroit et la brume."),
        ("L'arène du roi", "Une salle ronde de 16 blocs de rayon et 18 de haut, une estrade avec deux colosses "
                           "assis et des statues de chacals. Le Quatrième Roi se réveille quand tu approches du sceau."),
        ("La salle forte", "Derrière la brume sud et des barreaux scellés ; le puits du roi remonte jusqu'au "
                           "vestibule."),
    ],
    "fallen_seraph": [
        ("L'îlot d'arrivée", "Au sud-est : pierre de voyage, puis les ponts imposent l'ordre des cinq arcs et de "
                             "leurs temples."),
        ("La Porte", "Sur l'arc est : la salle sombre entre deux pylônes, et son portail tourné vers le centre."),
        ("Le lieu de grâce", "Le pont rayonnant mène à l'îlot du lieu de grâce, puis à un portique étroit et à la "
                             "brume."),
        ("Le disque", "L'arène : un disque de 16 blocs de rayon suspendu au-dessus du vide, un parapet bas brisé en "
                      "trois endroits, des éclats d'anneau qui flottent autour. La Séraphine se réveille quand tu "
                      "approches du sceau. Prends des perles de l'Ender et la chute lente."),
        ("La salle forte", "Au-delà de la brume ouest et des barreaux scellés, sur son propre îlot."),
    ],
    "chained_jailer": [
        ("Le débarcadère", "Sur l'éperon rocheux à l'ouest : pierre de voyage, poste de garde, puis le pont de chaînes "
                           "jusqu'à la pile dans la lave."),
        ("La chaîne d'ancrage", "Un escalier posé sur le dos de la chaîne géante monte jusqu'au porche de la "
                                "porterie (une chute, c'est la lave)."),
        ("La prison", "Niveau bas : porterie, prison des cages suspendues, caserne et sa cellule secrète, forge, "
                      "armurerie et l'escalier principal."),
        ("Le lieu de grâce", "Niveau haut : galerie, chapelle, puis la salle du lieu de grâce et un pont couvert "
                             "étroit jusqu'à la brume."),
        ("Le tambour", "L'arène : un anneau de pierre noire de 14 blocs de rayon autour d'une grille qui donne sur "
                       "la lave, 16 de haut, des rideaux de chaînes. Le Geôlier se réveille quand tu approches du "
                       "sceau."),
        ("La salle forte", "Au-delà de la brume sud et des barreaux scellés qui s'ouvrent à sa mort."),
    ],
    "oathbound_gatekeeper": [
        ("La ville du péage", "Sous le linteau, entre les deux géants agenouillés : la place, le puits et la pierre de "
                              "voyage."),
        ("Le géant est", "Par la maison de garde est, un escalier descend sous la ville jusqu'à la chapelle des "
                         "gardiens (le lieu de grâce), puis un passage étroit et la brume."),
        ("La salle sous la porte", "L'arène : une salle ronde de 17 blocs et demi de rayon sous un dôme bas de tuf, des "
                                   "lanternes d'âme sur huit pilastres, la lumière du puits qui tombe par la grille. "
                                   "Le Gardien se réveille quand tu approches du sceau."),
        ("La salle forte", "Sous le sol de l'arène, derrière des barreaux scellés qui s'ouvrent à sa mort ; le passage "
                           "ouest remonte au géant ouest par une porte de fer."),
    ],
    "caldera_castellan": [
        ("La porterie", "Au pied du massif, le camp et sa pierre de voyage, puis la route jusqu'à la barbacane, la "
                        "salle de garde et le grand escalier jusqu'à la cour de la porte, sur le bord du cratère."),
        ("Le chemin de ronde", "Par la tour sud-est, le chemin de ronde et le bastion est jusqu'au moyeu nord : grande "
                               "tour, grande salle, lieu de grâce."),
        ("Le souterrain", "Sous le moyeu, creusé dans la paroi du cratère : citerne, prison, galerie du pont, puis le "
                          "long pont jusqu'à la porte de l'aiguille."),
        ("L'aiguille", "Un escalier à vis monte 45 blocs dans le rocher jusqu'au donjon ; sa grande salle est le lieu "
                       "de grâce, un passage couvert mène à la brume."),
        ("La cour du sommet", "L'arène : une cour à ciel ouvert de 16 blocs de rayon sur des encorbellements "
                              "au-dessus du vide, un parapet crénelé et quatre tourelles. Le Châtelain se réveille "
                              "quand tu approches du sceau."),
        ("La salle forte", "La tourelle sud, derrière des barreaux scellés qui s'ouvrent à sa mort ; son balcon "
                           "permet de sauter dans le lac."),
    ],
    "frost_jarl": [
        ("La terrasse", "Le grand escalier monte au pied de la falaise de glace : pierre de voyage sur la terrasse, "
                        "puis le guichet de la porte entre les deux jarls de glace."),
        ("La grande salle", "La nef sous la voûte de glace, les foyers et les tables du festin ; à la croisée, "
                            "l'escalier du scalde (transept ouest) monte aux galeries."),
        ("Le pont de la crevasse", "Par le déambulatoire et la porte nord, un pont à ciel ouvert franchit la crevasse "
                                   "(une brèche dans le garde-corps : la chute dans le lac)."),
        ("L'escalier du Jarl", "Dans la corne, deux longues volées taillées dans la glace montent de 20 blocs jusqu'au "
                               "lieu de grâce (pierre de voyage, braseros)."),
        ("La salle du jarl", "Derrière la brume : une salle ronde de 16 blocs de rayon sous un dôme, huit piliers de "
                             "glace, un oculus. Le Jarl se réveille quand tu approches du sceau."),
        ("La salle forte et le saut", "Au nord, la salle forte, puis le Saut du Jarl : un puits de 47 blocs jusqu'au "
                                      "bassin de la source, et la rivière qui ramène dehors."),
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
    "brass_glider": "Le combo du mod : grappin pour monter, planeur pour redescendre de l'autre côté. Porte-le "
                    "dans la case du dos : il s'ouvre tout seul quand tu tombes, les mains restent libres.",
    "rivet_gun": "Une arme à distance sans arc, rapide et presque droite : parfaite contre les drones à vapeur.",
    "rivet": "Garde-en une pile sur toi ; sans rivets, le pistolet prend tes pépites de fer.",
    "pocket_watch": "Pour voir venir la nuit et la lune de sang, et savoir dans quel biome tu te trouves. À la "
                    "ceinture (case d'accessoire), elle sonne au crépuscule et à l'aube.",
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
    ("Peuples et créatures des lieux", "Les grands lieux ont leurs habitants, et les lieux hostiles leurs propres "
     "monstres.", [
        ("Les nains de la Cité naine", "Forgerons, mineurs, brasseurs et lapidaires qui travaillent et commercent ; "
         "des gardes au casque à cornes défendent les salles.", "b-dwarf", "mob:dwarf"),
        ("Sylvains, citoyens mécaniques, moines", "Le Palais sylvain et l'Arbre-monde, la Citadelle d'horlogerie et "
         "le Monastère ont aussi leur peuple, leurs métiers et leurs offres.", "bestiaire-folk", "mob:sylvan"),
        ("Six créatures à ruse", "Tireur bandit, pillard du ciel, crabe à bernacles, feu follet, molosse de cendre et "
         "sentinelle de la faille : chacune a son truc, et sa parade.", "bestiaire-creature", "mob:sky_raider"),
    ]),
    ("Carte, écrans et rangement", "Se repérer à plusieurs, régler chaque machine sans deviner, et toute la base "
     "dans un seul écran.", [
        ("Carte du monde partagée", "Touche M : tout ce qu'un joueur explore apparaît chez tous. Repères privés ou "
         "partagés, signaux, pierres de voyage, joueurs, vue des grottes.", "carte", "img:img/gui/worldmap.webp"),
        ("Mini-carte", "Un hublot de laiton dans un coin de l'écran : terrain, direction, repères, coordonnées et "
         "biome. H la masque, Z zoome, B envoie un signal.", "mini-carte", "img:img/gui/minimap.webp"),
        ("Un vrai écran pour chaque machine", "Les neuf machines s'ouvrent au clic : zone, sortie, filtre, mode "
         "redstone, réglés avec des boutons et des infobulles.", "ecrans-machines",
         "img:img/gui/machine_harvester.webp"),
        ("Réglages et touches", "Mods → Brasshaven → Config : barres de vie, chiffres de dégâts, suivi, astuces. La "
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
        ("Forteresse marchante", "Un marcheur de siège géant figé dans un cratère : on monte par ses jambes.",
         "s-walking_fortress", "struct:walking_fortress"),
        ("Nécropole des rois", "Un massif taillé comme à Pétra : quatre rois assis de 42 blocs au bout d'un canyon.",
         "s-rock_necropolis", "struct:rock_necropolis"),
        ("Colosse abattu", "Un chevalier de pierre et de bronze de 155 blocs couché dans une vallée : on entre par "
         "sa main.", "s-fallen_colossus", "struct:fallen_colossus"),
        ("Bastion enchaîné", "Une forteresse de pierre noire et d'or suspendue sous le plafond du Nether par des "
         "chaînes géantes, au-dessus d'un lac de lave.", "s-chained_bastion", "struct:chained_bastion"),
        ("Halo brisé", "Un anneau de 170 blocs brisé en cinq arcs flottants au-dessus du vide de l'End, un temple "
         "sur chaque arc et le boss sur un disque au centre.", "s-shattered_halo", "struct:shattered_halo"),
        ("L'Ascension du pèlerin", "Un croc de roche de 124 blocs gravi par un escalier en lacets jusqu'au temple "
         "de la grande cloche.", "s-pilgrims_ascent", "struct:pilgrims_ascent"),
        ("Halle glaciaire des jarls", "Une halle-cathédrale taillée dans une langue de glacier : une façade à "
         "statues, une nef de glace, un pont sur la crevasse et une arène dans une corne de roche.", "s-glacier_hall",
         "struct:glacier_hall"),
        ("Rempart de la caldeira", "Un cratère de volcan ceint d'une enceinte à seize pans, un lac et une aiguille "
         "de roche portant un donjon et l'arène du boss.", "s-caldera_ringwall", "struct:caldera_ringwall"),
        ("L'Épave du cuirassé Léviathan", "Un cuirassé à vapeur de 180 blocs échoué et brisé en deux sur un récif océanique : salle des machines, pont des torpilles noyé, soute à munitions et une arène dans la chaufferie.", "s-dreadnought_wreck", "struct:dreadnought_wreck"),
        ("Le Grand Aqueduc", "Un aqueduc de 240 blocs sur trois rangs d'arcades au-dessus d'une vallée : la "
         "maison de la source, une brèche habitée, une galerie dans les piles, le castellum et une arène dans sa "
         "citerne.", "s-great_aqueduct", "struct:great_aqueduct"),
        ("La Ziggourat du Moteur solaire", "Une pyramide à degrés de 140 blocs dans le désert, couronnée d'un "
         "planétaire de laiton dont la lentille éclaire l'arène de la chambre du soleil.", "s-sun_ziggurat",
         "struct:sun_ziggurat"),
        ("La Porte agenouillée", "Deux chevaliers de pierre de 70 blocs agenouillés de part et d'autre d'un col, "
         "un linteau entre leurs mains, des salles dans leurs corps et une arène sous la porte.", "s-kneeling_gate",
         "struct:kneeling_gate"),
        ("Barrage de la vallée engloutie", "Un barrage-voûte de pierre et de laiton de 170 blocs sur un lac qui a "
         "noyé un village, des salles des turbines à son pied.", "s-drowned_dam", "struct:drowned_dam"),
        ("La Flèche renversée", "Une tour bâtie vers le bas dans un gouffre de 110 blocs : une rampe en spirale, "
         "des niveaux de plus en plus étranges et l'arène sur une île du lac souterrain.", "s-inverted_spire",
         "struct:inverted_spire"),
        ("Abbaye des marées", "Un mont rocheux cerné par la marée : remparts, une ville en spirale et une abbaye "
         "gothique à flèche de 130 blocs, une arène dans la crypte.", "s-tidal_abbey", "struct:tidal_abbey"),
        ("La Cité des pilotis", "Une ville de bois sur pilotis au-dessus d'une mangrove : passerelles sur trois "
         "niveaux, ponts de corde, un fumoir, un clocher noyé et la salle de la reine-sorcière sous un chapeau "
         "tordu.", "s-mire_stilt_city", "struct:mire_stilt_city"),
        ("La Cité-temple de la canopée", "Une cité perdue dans la jungle : un temple à degrés étranglé par les "
         "racines, cinq troncs colossaux portant des quartiers reliés par des ponts de corde, un cénote noyé et "
         "une arène sous un disque solaire de laiton brisé.", "s-canopy_city", "struct:canopy_city"),
        ("La Ville minière de la Mesa rouille", "Une ville-champignon taillée dans une butte rayée des badlands : "
         "un chevalement à roue géante, des saloons sur les terrasses, une voie de wagonnets sur tréteaux, un "
         "bocard et une arène autour d'un filon d'or et de cuivre.", "s-mesa_minecity", "struct:mesa_minecity"),
        ("La Cathédrale de l'Écho", "Une cathédrale gothique de deepslate et de laiton terni dans une immense "
         "caverne profonde : nef de colonnes, clocher à la cloche fêlée, crypte inondée envahie de sculk, et une "
         "arène devant un orgue dont les tuyaux montent de 60 blocs dans la voûte.", "s-echo_cathedral",
         "struct:echo_cathedral"),
        ("La Forge du Titan de basalte", "Une forge colossale sur un lac de lave du Nether, bâtie dans un titan "
         "de basalte et de laiton agenouillé sur une enclume géante : halle de coulée, soufflets de cuir, mine de "
         "scories, et une arène sur l'enclume, sous le marteau levé.", "s-titan_forge", "struct:titan_forge"),
        ("Le Moteur des âmes", "Une machine-ossuaire de pierre noire et de laiton terni au fond d'une vallée de "
         "sable des âmes du Nether, nourrie par des convoyeurs d'os, six pistons colossaux sur son carter : salle "
         "des pressions, fournaise des âmes, ossuaire de voûtes d'os, et une arène sur le pont du vilebrequin.",
         "s-soul_engine", "struct:soul_engine"),
        ("La Bibliothèque de la chute d'étoile", "Une archive flottante de l'End autour d'une tour-fuseau de purpur "
         "et de laiton, trois galeries en anneau et une météorite fichée dans son flanc : canyons de rayonnages, "
         "scriptorium, observatoire, et une arène dans la chambre du cratère.", "s-starfall_library",
         "struct:starfall_library"),
        ("La Lune creuse", "Une lune mécanique écrasée sur une île de l'End, coque de laiton et de purpur "
         "fendue sur un tiers : galeries de la coque, jardins de gravité, crypte des engrenages, anneaux d'orrery "
         "figés, et une arène sur la plateforme du noyau lumineux.", "s-hollow_moon", "struct:hollow_moon"),
        ("La Pagode des nuages", "Une pagode à neuf toits de cerisier et de plâtre blanc sur un jardin en "
         "terrasses, étangs aux carpes et porte de lune, enlacée par le squelette de laiton d'un dragon "
         "mécanique : un étage par salle, un ascenseur à contrepoids, et une arène sur le toit ouvert.",
         "s-cloud_pagoda", "struct:cloud_pagoda"),
        ("La Flotte prise dans les glaces", "Un brise-glace colossal à roues à aubes figé dans la banquise, "
         "gîtant, ses cheminées de cuivre penchées, avec deux navires ravitailleurs, un derrick de forage en laiton "
         "et une baleine prise dans la glace : salle des chaudières, carrés, cabine du capitaine, et une arène sur "
         "le gaillard d'avant.", "s-icebound_fleet", "struct:icebound_fleet"),
        ("L'Asile mécanique", "Un sanatorium gothique sur une colline de forêt sombre, devenu atelier "
         "d'automates : une tour de l'horloge aux cadrans fêlés, des ailes de cellules grillagées, un amphithéâtre "
         "opératoire, des bains d'hydrothérapie, un funiculaire, et une arène derrière le cadran de l'horloge.",
         "s-clockwork_asylum", "struct:clockwork_asylum"),
        ("L'Arboretum englouti", "Un arboretum de laiton et de verre au fond d'une grotte luxuriante : une "
         "coupole de 50 blocs dont les nervures portent la voûte, un lac de nénuphars nourri par une cascade, "
         "serres en terrasses, grainothèque, laboratoire des spécimens, labyrinthe d'azalées, et une arène sur "
         "une île-nénuphar sous la lampe-soleil.", "s-verdant_arboretum", "struct:verdant_arboretum"),
        ("La Raffinerie de spores", "Une raffinerie d'alchimistes poussée dans trois champignons colossaux sur "
         "une île de mycélium : presses à vis, cuves de fermentation, distillerie, séchoirs sous le chapeau brun, "
         "ponts de corde, et une arène au sommet de la grande amanite.", "s-spore_refinery",
         "struct:spore_refinery"),
        ("La Forteresse du bois", "Un fort de bûcherons à vapeur dans une boucle de rivière de la taïga : "
         "palissade de troncs, scierie à roue à aubes, flottage sur tréteaux, fours à charbon, locomotive sur "
         "pilotis, et une arène au sommet d'un donjon de bois haut de 70 blocs.", "s-timber_fortress",
         "struct:timber_fortress"),
        ("La Station abyssale", "Une station de recherche au fond de l'océan profond : dômes pressurisés de "
         "laiton et de verre reliés par des tubes, tour d'accès et grue à bathyscaphe, plate-forme de forage "
         "au-dessus d'une fosse, champs de varech, et une arène au fond de la fosse.", "s-abyssal_station",
         "struct:abyssal_station"),
        ("Le Cimetière des dirigeables", "Un champ d'épaves dans la savane autour d'un mât d'amarrage haut de 90 "
         "blocs : un dirigeable encore amarré sous son enveloppe dégonflée, des épaves écrasées, le bidonville des "
         "ferrailleurs, une usine à gaz, et une arène sur le pont supérieur du dirigeable.", "s-airship_graveyard",
         "struct:airship_graveyard"),
    ]),
]

# « Tester en jeu » : (titre, [commandes], ce qu'on doit voir). Les commandes /brasshaven sont vérifiées par le
# générateur contre BrasshavenCommand.java ; les ids d'objets, d'entités et de structures contre les données du mod.
TEST_INTRO = ("Une partie en créatif (ou avec les droits d'opérateur), un monde neuf, et ces commandes dans le chat. "
              "Coche au fur et à mesure : la liste se souvient de tes coches sur cet appareil.")
TEST_CHECKLIST = [
    ("Tout recevoir d'un coup", ["/gamemode creative", "/brasshaven demo"],
     "Tous les objets du mod arrivent dans l'inventaire (le surplus tombe au sol)."),
    ("Clé à molette", ["/give @s brasshaven:brass_wrench", "/give @s minecraft:oak_stairs 8"],
     "Pose un escalier, clic droit avec la clé : il tourne. Accroupi : dans l'autre sens. Accroupi sur un bloc déco "
     "Brasshaven (placage de laiton…) : il revient dans l'inventaire."),
    ("Grappin et planeur", ["/give @s brasshaven:grappling_hook", "/give @s brasshaven:brass_glider"],
     "Vise un mur à moins de 32 blocs : la chaîne te tire jusqu'au rebord. En survie (/gamemode survival), saute "
     "d'en haut avec le planeur en main ou porté dans la case du dos : tu descends doucement, sans dégâts."),
    ("Accessoires", ["/gamemode survival", "/give @s brasshaven:magnet_ring", "/give @s brasshaven:arcane_ring",
                     "/give @s brasshaven:mana_amulet", "/give @s brasshaven:brass_glider"],
     "Ouvre l'inventaire (E) : une colonne de cinq cases grises à gauche de l'armure (dos, deux anneaux, amulette, "
     "ceinture). Maj + clic sur chaque objet : il va dans sa case. L'anneau arcanique donne +50 de mana max "
     "seulement porté ; l'anneau aimanté (touche N pour l'allumer) attire les objets seulement porté."),
    ("Pistolet à rivets", ["/give @s brasshaven:rivet_gun", "/give @s brasshaven:rivet 64",
                           "/summon minecraft:zombie ~ ~ ~5"],
     "Clic droit : un rivet fumant part tout droit (5 dégâts). Sans rivets ni pépites de fer : « Plus de rivets »."),
    ("Montre et boussole", ["/give @s brasshaven:pocket_watch", "/give @s brasshaven:airship_compass"],
     "La montre affiche l'heure, le jour, la lune et le biome. La boussole cherche le Port céleste le plus proche et "
     "son aiguille pointe vers lui (sinon elle le dit et tourne)."),
    ("Burin", ["/give @s brasshaven:chisel", "/give @s minecraft:stone_bricks 16",
               "/give @s minecraft:stone_brick_stairs 8"],
     "Clic droit sur des briques de pierre : moussues, fissurées, sculptées… Le nom de la variante et sa place "
     "dans la famille (ex. 3/6) s'affichent au-dessus de la barre. Sur un escalier, l'orientation est gardée."),
    ("Table de taille", ["/give @s brasshaven:chisel_table", "/give @s brasshaven:brass_plating 64"],
     "Pose la table, mets la pile de placage de laiton dans la case : clique « Laiton gravé » ou « Grille en "
     "laiton », toute la pile change."),
    ("Symétrie de la baguette", ["/give @s brasshaven:builder_wand", "/give @s minecraft:stone_bricks 64"],
     "Accroupi + clic droit sur un bloc : centre du miroir (étincelles). G : miroir X, Z, X + Z. Clic droit sur "
     "un mur : contours dorés pour tes blocs, bleus pour les copies. Accroupi dans le vide : tout s'annule."),
    ("Golem de laiton", ["/give @s brasshaven:brass_block 2", "/give @s brasshaven:clockwork_heart"],
     "Empile les deux blocs, clic droit avec le cœur : le golem apparaît et te suit. Accroupi + clic droit main "
     "vide : « garde ici »."),
    ("Automates ennemis", ["/time set night", "/summon brasshaven:clockwork_spider ~ ~ ~6",
                           "/summon brasshaven:steam_drone ~ ~4 ~6"],
     "L'araignée s'arrête, sa clé ronronne, puis elle bondit. Le drone tourne au-dessus de toi, tire des rivets et "
     "se cabre avant de plonger."),
    ("Donneurs de quêtes", ["/brasshaven npc spawn guild_agent", "/give @s minecraft:bread 12"],
     "Un agent de la Guilde apparaît à tes pieds, son nom au-dessus de la tête ; il reste à son poste et ne prend "
     "aucun dégât. Clic droit : il salue, ses contrats s'affichent. Accepte « Des vivres pour la route », clique "
     "Rendre : les pains partent, émeraudes et fragments de carte arrivent. Le contrat apparaît dans le journal "
     "(J), onglet Contrats."),
    ("Habitants des structures", ["/brasshaven tp giant_tree", "/brasshaven tp jungle_ziggurat",
                                  "/brasshaven tp clockwork_citadel"],
     "Dans l'Arbre-monde, des villageois en robe verte vivent sur les étages du tronc (lit et métier chacun) et une "
     "druidesse attend à l'étage des couchettes. Près de la ziggourat, la loge des gardiens ; dans la Citadelle, "
     "le bricoleur du premier atelier. La nuit, aucun monstre n'apparaît chez eux."),
    ("Le Grand Horloger", ["/brasshaven boss grand_clockmaker"],
     "Il apparaît à 6 blocs (arène de 20 blocs autour de toi). Guette l'arrêt du temps (cercle qui se referme) et, "
     "à mi-vie, le rugissement puis minuit. Pour le vrai repaire : /brasshaven tp clockwork_citadel."),
    ("Le Timonier de Fer", ["/brasshaven boss iron_helmsman"],
     "Il apparaît à 6 blocs. Saute l'onde de l'ancre abattue, écarte-toi de la ligne du harpon, sors du cercle de "
     "vapeur ; à mi-vie, la corne sonne puis la bordée tombe sur toi. Pour le vrai repaire : /brasshaven tp "
     "walking_fortress (le pont supérieur)."),
    ("La Sentinelle d'airain", ["/brasshaven boss bronze_sentinel"],
     "Elle apparaît à 6 blocs. Contourne le mur de pavois, saute l'onde du piétinement, écarte-toi de la fissure ; à "
     "mi-vie, ses plaques tombent, puis sors du cercle doré de la chute. Pour le vrai repaire : /brasshaven tp "
     "fallen_colossus (le sol de la salle des côtes)."),
    ("Le Roi des dunes", ["/brasshaven boss dune_king"],
     "Il apparaît à 6 blocs. Évite la ligne de la crosse et le cône de sable ; à mi-vie, il flotte : saute les "
     "scarabées et le rayon du jugement. Pour le vrai repaire : /brasshaven tp rock_necropolis (la salle "
     "hypostyle, au fond)."),
    ("Le Séraphin déchu", ["/brasshaven boss fallen_seraph"],
     "Elle apparaît à 6 blocs. Écarte-toi de la ligne de l'estoc, sors des cercles de lumière ; à 60 %, colle-toi "
     "sous elle pendant le balayage et saute les deux anneaux de la nova ; à 25 %, le disque se brise : reste "
     "dans l'anneau d'or et sors du cercle de sa chute. Pour le vrai repaire : /brasshaven tp shattered_halo (le "
     "disque au centre)."),
    ("Le Geôlier enchaîné", ["/brasshaven boss chained_jailer"],
     "Il apparaît à 6 blocs (prends de la résistance au feu). Écarte-toi de la ligne du grappin, sors des cercles "
     "d'entraves, saute l'anneau de feu ; à 60 %, tiens-toi entre les barreaux du bûcher ; à 30 %, il brise ses "
     "chaînes et le verdict tombe sur toi. Pour le vrai repaire : /brasshaven tp chained_bastion (le tambour)."),
    ("Le Gardien du Serment", ["/brasshaven boss oathbound_gatekeeper"],
     "Il apparaît à 6 blocs. Tourne autour de son pavois et frappe son dos, saute l'onde du piétinement, sors du cercle "
     "doré de la clé ; à 65 %, cours au passage entre les flammes d'âme quand le glas sonne ; à 30 %, il "
     "s'agenouille : brise le Bouclier du Serment en 10 s. Pour le vrai repaire : /brasshaven tp kneeling_gate (la "
     "salle sous la porte)."),
    ("Le Châtelain de la caldeira", ["/brasshaven boss caldera_castellan"],
     "Il apparaît à 6 blocs. Recule hors du balayage, écarte-toi de la ligne de la taille, sors du cercle de braises du "
     "bond puis de la faille ; à 60 %, sors des murs d'obsidienne par le côté ouvert (ils disparaissent après 10 s) ; à "
     "30 %, lis la fumée des cheminées et frappe pendant que son armure est fragile. Pour le vrai repaire : "
     "/brasshaven tp caldera_ringwall (la cour du sommet de l'aiguille)."),
    ("Le Jarl de givre", ["/brasshaven boss frost_jarl"],
     "Il apparaît à 6 blocs. Frappe-le de flanc ou pendant qu'il se reprend (son bouclier pare de face), sors du cône "
     "du souffle et des cercles de pics ; à 65 %, tiens-toi entre les anneaux du givre éclaté ; à 30 %, bouge sans "
     "cesse et saute quand le sol blanchit. Pour le vrai repaire : /brasshaven tp glacier_hall (dans la corne)."),
    ("L'Ascète des tempêtes", ["/brasshaven boss storm_ascetic"],
     "Il apparaît à 6 blocs. Recule hors de l'arc du bâton puis de la ligne d'estoc, sors des cercles de foudre ; sa "
     "rafale s'arrête à l'anneau de nuages. À 65 %, frappe les reflets (un coup suffit) ; à 30 %, saute chaque anneau "
     "de la cloche. Pour le vrai repaire : /brasshaven tp pilgrims_ascent (le temple du sommet)."),
    ("L'Abbesse des Marées", ["/brasshaven boss tide_abbess"],
     "Elle apparaît à 6 blocs. Sors des nuages de saumure, tiens-toi dans les brèches des vagues, cours contre le "
     "glas ; à 30 %, la rotonde s'inonde (vraie eau, retirée quand elle tombe ou quand le combat se réinitialise). "
     "Pour le vrai repaire : /brasshaven tp tidal_abbey (sous l'église)."),
    ("Le Maître des écluses", ["/brasshaven boss lock_master"],
     "Il apparaît à 6 blocs. Écarte-toi de la ligne d'estoc, ne reste pas dans son dos, frappe sa vanne d'un coup "
     "lourd ou contourne-la ; cache-toi derrière une colonne quand le jet balaie, sors des dalles marquées ; à 30 %, "
     "abrite-toi du courant dans le sillage d'une colonne. Pour le vrai repaire : /brasshaven tp great_aqueduct (la "
     "grande citerne sous le castellum)."),
    ("Le Hiérophante des tourbières", ["/brasshaven boss bog_hierophant"],
     "Il apparaît à 6 blocs. Recule hors de l'arc de la crosse, sors des cercles de boue avant d'être pris, éloigne-toi "
     "des autres quand tu es marqué ; à 65 %, guette le tintement derrière toi ; à 30 %, passe par les brèches des "
     "lignes de feu. Pour le vrai repaire : /brasshaven tp mire_stilt_city (la salle de la reine-sorcière, en haut)."),
    ("Le Conservateur dévoreur d'étoiles", ["/brasshaven boss star_curator"],
     "Il apparaît à 6 blocs (sans brasiers, quatre nœuds virtuels sur les diagonales). Abats ses livres à l'arc, "
     "sprinte contre le puits de gravité, sors des cercles d'étoiles ; à 65 %, reste dans les cercles dorés pendant la "
     "tempête de pages ; à 30 %, tiens-toi dans un anneau doré à chaque pulsation et vérifie que tu redescends "
     "toujours en chute lente, même s'il meurt pendant que tu flottes. Pour le vrai repaire : /brasshaven tp "
     "starfall_library (la chambre du cratère sous la tour)."),
    ("L'Abbé des carillons", ["/brasshaven boss chime_abbot"],
     "Il apparaît à 6 blocs (sans pont, les coins sont pris en diagonale autour de lui). Fais un pas de côté pour le "
     "bâton, sors du cône de la paume, quitte chaque zone de carillon quand elle rougit, place-toi dans une brèche "
     "pendant la tempête de pétales ; à 65 %, sors du cercle de la chute de cloche ; à 30 %, reste entre les couloirs "
     "du dragon. Près de la balustrade, vérifie qu'aucun coup ne te jette dehors. Pour le vrai repaire : "
     "/brasshaven tp cloud_pagoda (le pont sous le neuvième toit)."),
    ("Le Baron de la mine", ["/brasshaven boss mine_baron"],
     "Il apparaît à 6 blocs (sans lampes autour, le coup de grisou n'éteint rien). Pas de côté pour la foreuse, sors "
     "des cercles de dynamite quand ils rougissent, ne reste pas dans son dos ; à 65 %, frappe les géodes d'or de "
     "sa chaudière par derrière jusqu'à le faire chanceler, et casse le flot d'or quand il se recuirasse ; à 30 %, "
     "vérifie que les lampes s'éteignent puis reviennent à sa mort, et coupe le faisceau de la lanterne. Pour le "
     "vrai repaire : /brasshaven tp mesa_minecity (la caverne du filon)."),
    ("La Capitaine corsaire", ["/brasshaven boss corsair_captain"],
     "Elle apparaît à 6 blocs (sans bastingage, les couloirs de vent suivent l'axe nord-sud). Écarte-toi de la ligne "
     "du harpon, sprinte contre la bourrasque, sors du cercle du piqué quand il se fige ; à 65 %, tue les pillards du "
     "ciel ; à 30 %, reste entre les couloirs de vent et vérifie que les plaques de magma redeviennent des planches "
     "au bout de 5 s et à sa mort. Pour le vrai repaire : /brasshaven tp airship_graveyard (le pont supérieur du "
     "dirigeable amarré)."),
    ("Le Chantre creux", ["/brasshaven boss hollow_cantor"],
     "Il apparaît à 6 blocs. Sors du cône du cri sur le côté, saute l'onde du glas, mets-toi dans un cercle doré "
     "avant que le sol sonne et vérifie que les bourgeons d'améthyste disparaissent ; à 65 %, entre dans le silence "
     "et frappe-le pour le révéler ; à 30 %, esquive les souffles de tuyau et tiens-toi dans les brèches du requiem. "
     "Pour le vrai repaire : /brasshaven tp echo_cathedral (le chœur et l'abside, devant l'orgue)."),
    ("Le Chauffeur des âmes", ["/brasshaven boss soul_stoker"],
     "Il apparaît à 6 blocs. Pas de côté pour la pelletée puis sors des cercles des braises, quitte la ligne du piston "
     "avant qu'elle rougisse, sors du cône quand il attise, quitte chaque évent avant qu'il rougisse ; à 65 %, "
     "écarte-toi du couloir de la charge et tue les squelettes wither ; à 30 %, change de bande à chaque pulsation "
     "du pont et tiens-toi dans les brèches des anneaux. Vérifie qu'aucun coup ne te jette dans la tranchée. Pour le "
     "vrai repaire : /brasshaven tp soul_engine (le pont du vilebrequin, dans le carter)."),
    ("La Directrice de l'asile", ["/brasshaven boss asylum_director"],
     "Elle apparaît à 6 blocs. Fais un pas de côté hors de la ligne du scalpel, recule hors de l'arc de la scie, "
     "esquive la fléchette ; quand un fantôme d'horloge se forme à tes pieds, éloigne-toi puis sors de son cercle dès "
     "que tu y es ramené ; sors des couloirs du pendule et tue les araignées ; à 65 %, passe d'un quart à l'autre "
     "pendant la dissection ; à 30 %, saute l'onde de minuit et suis la brèche dorée entre les aiguilles. Pour le "
     "vrai repaire : /brasshaven tp clockwork_asylum (l'étage de l'horloge, en haut de la tour)."),
    ("L'Alchimiste des spores", ["/brasshaven boss spore_alchemist"],
     "Il apparaît à 6 blocs. Recule hors de l'arc du bâton puis du cercle rouge de la fiole, sors du cône de la "
     "pulvérisation et contourne le nuage qu'elle laisse, quitte les cercles colorés des fioles, sors des cercles bruns "
     "des pousses et vérifie que les champignons disparaissent après 6 s ; à 65 %, attends qu'il ressorte du voile sur "
     "son cercle et tue les bogged ; à 30 %, saute l'onde de la floraison, évite les évents, éloigne-toi de lui contre "
     "le mycélium et traverse l'anneau doré à chaque expiration. Pour le vrai repaire : /brasshaven tp spore_refinery "
     "(le sommet de la grande amanite)."),
    ("Le Jarl du bois", ["/brasshaven boss lumber_jarl"],
     "Il apparaît à 6 blocs. Sors de l'arc de la tronçonneuse avant les morsures, quitte la ligne du coup de hache, "
     "suis la boucle tracée de la lame et reste hors d'elle au retour, sors des couloirs de « Timber ! » et vérifie que "
     "les troncs disparaissent, écarte-toi du couloir du tronc roulant ; à 65 %, tue son équipe ; à 30 %, saute l'onde, "
     "sors des secteurs d'étincelles et des cercles de vapeur. Pour le vrai repaire : /brasshaven tp timber_fortress "
     "(le sommet du donjon)."),
    ("Le Jardinier en chef", ["/brasshaven boss thorn_gardener"],
     "Il apparaît à 6 blocs. Recule hors des deux arcs du sécateur, sors du couloir de la fente, glisse-toi entre les "
     "lignes d'épines, sors du cercle de la liane (ou frappe pour te libérer), quitte le cône de l'arrosage et vérifie "
     "que les buissons d'épines disparaissent ; à 65 %, tue les grenouilles et araignées et sors des cercles de pollen ; "
     "à 30 %, saute l'onde, esquive les rayons et entre dans son cercle de lumière pour l'empêcher de guérir. Pour le "
     "vrai repaire : /brasshaven tp verdant_arboretum (le nénuphar sous le dôme)."),
    ("Le Scaphandrier des abysses", ["/brasshaven boss abyss_diver"],
     "Il apparaît à 6 blocs. Sors du couloir de la percée, recule hors de l'arc du broyage, fais un pas de côté hors des "
     "lignes des rivets, sors du cercle du choc puis saute son onde, quitte la ligne du harpon (ou laisse-toi tirer et "
     "vérifie que tu t'arrêtes à 3 blocs) ; à 65 %, sors du cercle de vase et contourne le nuage, tue les noyés ; à 30 %, "
     "saute l'onde, sors des cercles de pression, éloigne-toi des méduses quand elles rougissent, et frappe-le pendant "
     "sa surcharge. Vérifie qu'aucun bloc de la salle ne bouge. Pour le vrai repaire : /brasshaven tp abyssal_station "
     "(la chambre de forage au fond de la tranchée)."),
    ("La Gardienne de la lune", ["/brasshaven boss moon_warden"],
     "Elle apparaît à 6 blocs. Recule hors des deux arcs du balayage, glisse-toi entre les spirales de l'orbite, sors du "
     "puits de gravité en marchant, quitte les cercles de la bascule, regarde son cadran : esquive les ombres à la "
     "nouvelle lune et saute l'anneau à la pleine lune ; à 65 %, sors du cercle de la comète et tue les larves ; à 30 %, "
     "saute l'anneau sombre, marche avec l'espace entre les rayons de gravité, quitte les cercles des météores et "
     "vérifie que le cœur se rallume à la fin. Pour le vrai repaire : /brasshaven tp hollow_moon (la plateforme du cœur)."),
    ("Le Commodore gelé", ["/brasshaven boss frost_commodore"],
     "Il apparaît à 6 blocs. Recule hors de l'arc de l'ancre puis du revers rouge, quitte la ligne du lancer et reste "
     "hors d'elle pendant le retour de l'ancre, glisse-toi entre les lignes de pics, sors du cône du souffle, quitte "
     "les cercles des blocs de glace et vérifie que les plaques glissantes disparaissent ; à 65 %, esquive la fusée et "
     "tue les vagabonds ; à 30 %, saute l'onde du blizzard, sors des cercles des stalactites et saute les deux vagues "
     "du coup de bélier. Pour le vrai repaire : /brasshaven tp icebound_fleet (le gaillard d'avant du brise-glace)."),
    ("La Reine-figuier étrangleur", ["/brasshaven boss strangler_queen"],
     "Elle apparaît à 6 blocs. Écarte-toi de la ligne du fouet, glisse-toi entre les lignes de racines, saute les "
     "anneaux, sors du pollen ; à 65 %, tue les esprits-jaguars pour la faire chuter et sors des cercles des "
     "graines ; à 30 %, sors du cercle avant que la cage se referme, ou casse-la. Vérifie que les racines "
     "disparaissent quand elle tombe. Pour le vrai repaire : /brasshaven tp canopy_city (la terrasse au sommet du "
     "temple, sous le disque solaire)."),
    ("Le Hiérarque solaire", ["/brasshaven boss solar_hierarch"],
     "Il apparaît à 6 blocs et dresse six gnomons de grès autour de lui (retirés à sa mort). Frappe-le de côté ou de "
     "dos, ou brise le miroir ; tire une flèche de face : elle doit revenir. Cache-toi derrière un gnomon pour l'éclat, "
     "la lance solaire et l'anneau haut, saute l'anneau bas ; à 30 %, éloigne-toi du sceau qui s'embrase. Pour le "
     "vrai repaire : /brasshaven tp sun_ziggurat (la chambre du soleil sous la lentille)."),
    ("L'Amiral noyé", ["/brasshaven boss drowned_admiral"],
     "Il apparaît à 6 blocs (sans chaudières, quatre vannes virtuelles autour de lui). Pas de côté quand le laser du "
     "canon se fige, sors de la ligne du grappin et des couloirs de vapeur ; à 65 %, attire sa charge contre un mur ; "
     "à 30 %, reste mobile dans l'eau et occupe-toi des marins. Pour le vrai repaire : /brasshaven tp dreadnought_wreck "
     "(la chaufferie, à la poupe)."),
    ("Le Quatrième Roi", ["/brasshaven boss fourth_king"],
     "Il apparaît à 6 blocs et dresse quatre vases canopes autour de lui (retirés à sa mort). Casse les vases avant "
     "qu'il ne les draine ; saute le rayon bas, fais un pas de côté pour le rayon haut, sors des cercles de sable et "
     "attire l'essaim dessous ; à 30 %, vérifie que les lanternes s'éteignent puis reviennent à sa mort, et cache-toi "
     "des regards des esprits. Pour le vrai repaire : /brasshaven tp rock_necropolis (tout en bas)."),
    ("Le Cœur du Colosse", ["/brasshaven boss colossus_heart"],
     "Il apparaît à 6 blocs. Sors de l'arc du fauchage et de la boucle de la plaque-bouclier, bouge quand les cercles "
     "de gravats rougissent, cours à contre-sens de l'aimant ; à 65 %, l'armure éclate : frappe le cœur entre les "
     "plaques, reste sur les bandes sûres des anneaux ; à 30 %, il se ressoude plus grand : vérifie que les tas de "
     "gravats disparaissent après 8 s et à sa mort. Pour le vrai repaire : /brasshaven tp fallen_colossus (le heaume)."),
    ("Le Tyran des turbines", ["/brasshaven boss turbine_tyrant"],
     "Il apparaît à 6 blocs (sans grilles, il crée huit évents virtuels autour de lui). Recule hors du rotor, écarte-toi "
     "des fissures, quitte les grilles qui sifflent ; pendant la surpression, coupe sa ligne de vue ou sors de la "
     "portée. Pour le vrai repaire : /brasshaven tp drowned_dam (la salle des turbines)."),
    ("Le Gardien de l'enclume", ["/brasshaven boss anvil_warden"],
     "Il apparaît à 6 blocs (prends de la résistance au feu). Écarte-toi de la ligne de l'onde, sors des dalles "
     "marquées et des flaques, ne reste pas devant la pince ; quand il frappe trois fois sa pince, sors de la zone "
     "rouge puis saute l'onde ; à 30 %, cache-toi derrière un obstacle ou sors de la portée pendant la purge. Pour le "
     "vrai repaire : /brasshaven tp titan_forge (l'arène sur l'enclume, sous le marteau du titan)."),
    ("Merveilles en surface", ["/brasshaven tp inventor_manor", "/brasshaven tp sylvan_palace",
                               "/brasshaven tp geothermal_foundry", "/brasshaven tp tesla_observatory",
                               "/brasshaven tp sky_isles"],
     "Téléportation à la plus proche (générée si besoin, quelques secondes ; si aucune n'est assez près, le "
     "message le dit). Les Îles célestes flottent vers y 170-230 : tu arrives dessus ou dessous ; en dessous, "
     "passe en /gamemode spectator pour monter."),
    ("Merveilles souterraines", ["/brasshaven locate dwarven_city", "/brasshaven locate crystal_cathedral",
                                 "/brasshaven locate echo_cathedral", "/locate structure brasshaven:dwarven_city", "/gamemode spectator"],
     "locate donne les coordonnées ; tp t'amène à la surface juste au-dessus. En spectateur, descends à travers la "
     "roche : la cité est vers y −50, le sol de la cathédrale vers y −40."),
    ("Carte du monde et mini-carte", ["/gamemode spectator", "/give @s brasshaven:wayfarer_atlas"],
     "La mini-carte est en haut à gauche ; H la masque, Z change son zoom (W en AZERTY). Vole un peu puis ouvre la "
     "carte avec M (la virgule en AZERTY) ou l'Atlas accroupi : le terrain vu est dessiné, en relief. Glisse, molette "
     "pour zoomer, Espace pour revenir sur toi. Le bouton cube incline la carte en 3D ; l'engrenage ouvre les "
     "options : fais glisser le curseur de taille, la mini-carte grandit en direct dans son coin."),
    ("Radar de la mini-carte", ["/summon minecraft:zombie ~6 ~ ~", "/summon minecraft:cow ~-5 ~ ~4",
                                "/summon minecraft:villager ~3 ~ ~-6"],
     "Les trois créatures apparaissent sur la mini-carte : la tête du zombie cerclée de rouge, la vache cerclée de "
     "vert, le villageois cerclé de crème. Options de la carte, colonne Radar : « Points » les change en points "
     "colorés ; décoche « Animaux » et la vache disparaît. Zoome la carte du monde près de toi : elles y sont aussi, "
     "avec leur nom au survol."),
    ("Repères et signaux", ["/gamemode creative"],
     "Sur la carte, clic droit : « Poser un repère ici » (nom, couleur, icône, Partager). Clic sur le repère : sa "
     "fiche (Modifier, Privé/Partager, Supprimer). Clic molette ou B en visant un bloc : un signal visible une "
     "minute. À deux sur un serveur, l'autre joueur voit tes repères partagés, tes signaux et ce que tu as exploré."),
    ("Vue des grottes", ["/gamemode spectator", "/tp @s ~ 20 ~"],
     "Sous terre, la mini-carte et la carte montrent la grotte à ta hauteur (« Vue des grottes ») au lieu de la "
     "surface. Le bouton à droite de la carte l'active ou la coupe."),
    ("Écrans des machines", ["/give @s brasshaven:auto_harvester", "/give @s brasshaven:redstone_timer",
                             "/give @s brasshaven:entity_detector", "/give @s brasshaven:vacuum_hopper"],
     "Pose chaque machine et fais clic droit : un écran de laiton avec la zone, la sortie, le mode redstone… "
     "Survole un bouton pour son infobulle. Le minuteur affiche son intervalle, le détecteur sa cible et sa portée."),
    ("Terminal de guilde et relais", ["/give @s brasshaven:guild_terminal", "/give @s brasshaven:storage_relay 2",
                                      "/give @s minecraft:chest 8"],
     "Pose des coffres jusqu'à 48 blocs du terminal, ouvre-le : tous leurs objets sont dans une seule grille. Pose "
     "un coffre à 70 blocs : absent ; un relais entre les deux : il apparaît. Bouton réseau en haut à droite : "
     "clique un coffre pour l'exclure, « Montrer » les encadre (or relié, rouge exclu)."),
    ("Créatures marines", ["/brasshaven tp sunken_submarine", "/time set night",
                           "/summon brasshaven:glow_jellyfish ~ ~-3 ~4", "/summon brasshaven:reef_fish ~ ~-3 ~4",
                           "/summon brasshaven:manta_ray ~ ~-4 ~8", "/summon brasshaven:whale ~ ~-8 ~16"],
     "Tu arrives à la surface de la mer. La méduse pulse et brille la nuit (la toucher pique), les poissons "
     "nagent en banc, la raie bat des ailes et saute, la baleine remonte souffler."),
    ("Serpent de mer", ["/time set night", "/give @s minecraft:oak_boat", "/summon brasshaven:sea_serpent ~ ~-4 ~10"],
     "Une barre de boss apparaît. Il mord, charge (ton bateau se brise) et lève un tourbillon qui t'aspire. Il "
     "lâche des écailles de serpent de mer."),
    ("Épaves sous l'eau", ["/brasshaven tp sunken_submarine", "/brasshaven tp diving_bell",
                           "/brasshaven tp coral_shrine", "/brasshaven tp shipwreck_debris"],
     "Tu arrives à la surface juste au-dessus : plonge. Le sous-marin a une brèche dans le flanc et deux coffres ; "
     "dans la cloche de plongée, on respire."),
    ("Plongée et fonds marins", ["/give @s brasshaven:diving_helmet", "/give @s brasshaven:flippers",
                                 "/give @s brasshaven:pearl_oyster 2", "/give @s brasshaven:glow_anemone 4"],
     "Avec le casque, la tête sous l'eau : force de conduit (respiration, vue dégagée, minage normal). Avec les "
     "palmes, tu nages bien plus vite. Pose l'huître sous l'eau, clic droit quand elle est entrouverte : une perle."),
    ("Bois et pierres", ["/give @s brasshaven:glowwood_sapling", "/give @s minecraft:bone_meal 8",
                         "/give @s brasshaven:marble 16", "/locate biome minecraft:badlands"],
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
                            "souris. Sur le bord, le bouton cube incline la carte en vue 3D et l'engrenage ouvre les "
                            "options (taille de la mini-carte, relief)."),
]
# (geste, effet) : commandes de l'écran de la carte
MAP_CONTROLS = [
    ("Glisser", "déplacer la carte"),
    ("Molette, + ou −", "zoomer, dézoomer"),
    ("Espace", "recentrer sur toi"),
    ("Clic sur un marqueur", "sa fiche : nom, coordonnées, distance"),
    ("Clic droit", "poser un repère, signaler l'endroit, copier les coordonnées"),
    ("Clic molette", "envoyer un signal à tous"),
    ("Bouton cube", "vue 3D inclinée : le terrain en relief, à sa hauteur"),
    ("Bouton engrenage", "options : taille exacte de la mini-carte, coin, forme, opacité, radar, relief, courbes de "
                         "niveau"),
    ("M ou Échap", "fermer la carte"),
]
# (ancre, titre, texte, icône) : les fonctions de la carte
MAP_FEATURES = [
    ("carte-partagee", "Exploration partagée", "Le serveur dessine les chunks autour de chaque joueur et garde la "
     "carte de chaque dimension. Ce que ton ami a exploré pendant ton absence est déjà sur ta carte. Un serveur qui "
     "préfère des cartes personnelles met map.sharedExploration à false : chacun ne voit alors que ce qu'il a vu "
     "lui-même (le serveur garde les deux, on peut basculer à tout moment).", "brasshaven:wayfarer_atlas"),
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
    ("relief", "Relief et vue 3D", "Les cartes sont ombrées à partir des hauteurs explorées : pentes éclairées du "
     "nord-ouest, vallées plus sombres, sommets plus pâles, eau de plus en plus foncée avec la profondeur et fond "
     "marin qui transparaît près des côtes. Le bouton cube de la carte du monde l'incline en vue 3D : chaque colonne "
     "monte à sa hauteur, falaises et pentes en relief, comme une maquette. Les options règlent le relief (plat, "
     "normal, fort) et ajoutent des courbes de niveau.", "minecraft:spyglass"),
    ("options-carte", "Options de la carte", "Le bouton engrenage de la carte du monde ouvre un panneau : taille "
     "exacte de la mini-carte (un curseur de 48 à 160 px, par pas de 4, ou les préréglages 56, 68, 96 et 128), "
     "coin, forme, rotation, coordonnées et opacité, et à droite la colonne du radar. Tant qu'il est ouvert, la "
     "mini-carte s'affiche dans son coin et change en direct. Tout est enregistré aussitôt.", "minecraft:compass"),
    ("radar", "Radar des créatures", "Comme les mini-cartes connues, la mini-carte montre les créatures autour de "
     "toi : leur tête pour les créatures vanilla courantes (zombie, squelette, creeper, araignée, enderman, vache, "
     "cochon, mouton, poule, loup, villageois…), sinon un point coloré : rouge hostile, vert animal, jaune neutre "
     "(rouge une fois en colère), gris pour un objet au sol. Villageois et PNJ du mod ont un badge, les boss un "
     "crâne violet couronné. Une petite flèche au-dessus ou en dessous d'une icône : la créature est loin plus haut "
     "ou plus bas que toi. Zoomée près de toi, la carte du monde les montre aussi, avec leur nom au survol. Les autres "
     "joueurs gardent leur tête, une pointe vers où ils regardent, un cadre doré pour tes compagnons, et restent sur "
     "le bord de la mini-carte quand ils sont plus loin. Tout se passe dans ton jeu, rien de plus ne passe par le "
     "réseau. Réglages : colonne Radar des options de la carte, ou onglet Radar de Mods → Brasshaven → Config "
     "(activé, têtes ou points, hostiles, animaux, PNJ, joueurs, objets).", "minecraft:spyglass"),
]
MINIMAP_TEXT = [
    "La mini-carte est un hublot de laiton dans un coin de l'écran (en haut à gauche au départ). Elle montre le "
    "terrain autour de toi, la flèche de ta direction, et les pierres de voyage, repères, joueurs, signaux, tombes "
    "et ta dernière mort. En dessous : tes coordonnées et le biome où tu es. Son radar ajoute les créatures autour "
    "de toi (leur tête ou un point coloré, voir « Radar des créatures »).",
    "H la masque ou la réaffiche, Maj + H passe à la taille suivante (56, 68 par défaut, 96 ou 128 px). Au "
    "pixel près, de 48 à 160 px : le curseur des options de la carte (M, puis l'engrenage), la mini-carte change en "
    "direct. La flèche et les marqueurs suivent sa taille : petits sur une petite mini-carte. Z change son zoom "
    "(4 niveaux) ; en AZERTY c'est la touche W. Coin de l'écran, forme (ronde ou carrée), rotation, coordonnées "
    "et opacité se règlent aussi dans ces options ou dans Mods → Brasshaven → Config, onglet Mini-carte (ou "
    "config/brasshaven-client.toml).",
]

# ------------------------------------------------------------------ machines : écrans
MACHINE_SCREENS_INTRO = ("Clic droit sur une machine : un écran de laiton s'ouvre. En haut, ce qu'elle fait et son "
                         "état en une ligne ; au milieu, ses réglages en boutons (survole-les pour une infobulle) ; "
                         "à droite, ses cases quand elle en a. Les images ci-dessous sont dessinées avec les vraies "
                         "textures du jeu ; touche une image pour l'agrandir.")
SETTINGS_TEXT = ("Mods → Brasshaven → Config ouvre les réglages du mod dans le même style : barres de vie (toujours, "
                 "blessées, jamais), chiffres de dégâts, suivi de quête, cartes d'astuce, et un bouton vers les "
                 "touches ; l'onglet Mini-carte règle la mini-carte, l'onglet Radar les créatures et joueurs qu'elle "
                 "montre. La touche du Manuel (maintenue sur un objet pour ouvrir sa page) se change maintenant : W "
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
     "quoi décorer un aquarium.", "brasshaven:glow_anemone", "toutes les mers"),
    ("Huîtres perlières", "Clic droit sur une coquille entrouverte pour prendre sa perle ; sous l'eau, elle en refait "
     "une avec le temps. Quatre perles valent une émeraude à l'établi.", "brasshaven:pearl_oyster",
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
        "La boussole des structures, la boussole de dirigeable et /brasshaven locate gardent leur réponse en "
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
     "zoom, de vue des grottes, de liste, de vue 3D et d'options.", "carte"),
    ("world_map_options", "Les options de la carte", "Le bouton engrenage : taille exacte de la mini-carte, coin, "
     "forme, opacité et relief ; la mini-carte s'affiche en direct dans son coin.", "options-carte"),
    ("world_map_3d", "La carte en vue 3D", "Le bouton cube incline la carte : le terrain exploré en relief, chaque "
     "colonne à sa hauteur.", "relief"),
    ("quest_journal", "Le journal de quêtes", "Touche J. Les cinq chapitres à gauche, leurs étapes au milieu, et "
     "à droite l'objectif et les récompenses de la quête choisie.", "quetes"),
    ("talent_tree", "L'arbre de talents", "Touche K. Les quatre branches : Guerrier, Explorateur, Arcaniste et "
     "Mécaniste. Le talent du bas de chaque branche est un pouvoir actif.", "talents"),
    ("manual_welcome", "Le Manuel du Voyageur", "La page d'accueil. Le sommaire à gauche range les 85 pages par "
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
    ("health_bars", "Les barres de vie", "Quatre créatures de près : pleine vie (vert), une qui vient d'être "
     "frappée (la traînée jaune des dégâts et le chiffre qui s'envole), 40 % (jaune) et 15 % (rouge).", ""),
    ("minimap_radar", "Le radar de la mini-carte", "Treize créatures autour du joueur : têtes des monstres et des "
     "animaux, points colorés pour les créatures du mod, badge des PNJ, crâne couronné du boss, et la poule loin "
     "au-dessus avec sa petite flèche.", "radar"),
    ("peoples", "Les peuples des grands lieux", "De gauche à droite : un forgeron et un garde nains, un jardinier et un "
     "gardien sylvains, un engrenier et une sentinelle mécaniques, un copiste et un gardien du monastère.",
     "bestiaire-folk"),
    ("creatures_places", "Les créatures des lieux hostiles", "Le tireur bandit, le pillard du ciel, le crabe à "
     "bernacles, le feu follet, le molosse de cendre et la sentinelle de la faille.", "bestiaire-creature"),
    ("folk_trade", "Commercer avec un nain", "Clic droit sur un forgeron nain : l'écran d'échange de Minecraft, avec "
     "ses outils, ses armures et le charbon qu'il rachète.", "bestiaire-folk"),
    ("mega_structure", "La Citadelle d'horlogerie", "Une merveille posée par le serveur de test et vue du ciel : la "
     "tour-horloge, ses toits de cuivre et ses cheminées.", "s-clockwork_citadel"),
]


# ------------------------------------------------------------------ Brasshaven biomes (gen_wiki section_biomes; the
# biome texts themselves are in wf/worldbiomes.py, shared with the in-game manual)
BIOMES_INTRO = ("Trois biomes propres au mod, taillés dans des climats vanilla : le relief reste celui de Minecraft, "
                "mais le sol, les couleurs, le ciel, les particules et les objets naturels changent. Ils apparaissent "
                "dans les nouveaux mondes de type « Par défaut ».")
TOUCHES_INTRO = ("Les biomes vanilla gagnent quelques touches naturelles, rares et légères : chacune a son option "
                 "côté serveur (lue au démarrage, pour les nouveaux chunks seulement).")
BIOMES_NOTE = ("Option world.customBiomes (vrai par défaut) : un pack de données intégré, « brasshaven:custom_biomes », "
               "remplace le type de monde « Par défaut » par le même avec ces trois biomes. Minecraft affiche alors son "
               "avertissement « paramètres expérimentaux » à la création du monde : c'est normal. Les mondes "
               "Superplat, Amplifié, Grands biomes et les mondes existants ne changent pas. La génération reste au "
               "moins aussi rapide que la vanilla : la CI la mesure à chaque build (monde avec et sans les biomes, "
               "mêmes zones, échec au-delà de +5 %).")

# ------------------------------------------------------------------ multijoueur (tools/wf/social.py, section #multijoueur)
SOCIAL_INTRO = ("Pour les serveurs à plusieurs : une Compagnie pour partir ensemble, l'échange sécurisé en face à face, "
                "la poste pneumatique qui livre même les absents, les contrats de guilde avec récompense en dépôt, des "
                "gestes que tout le monde voit et des duels où personne ne meurt. Chaque fonction se coupe côté serveur.")
SOCIAL_CARD = ("Accroupi + clic droit sur un joueur (main vide), ou vise-le et appuie sur U : sa fiche s'ouvre, avec sa "
               "compagnie, ses duels gagnés et perdus, et les boutons Échanger, Duel, Inviter, Saluer.")
# ce que le serveur garantit, fonction par fonction
SOCIAL_SAFETY = [
    ("Rien n'est jamais dupliqué", "Un objet quitte un inventaire et arrive ailleurs dans le même tick du serveur. "
     "Les objets d'un échange, d'un colis ou d'une récompense sont tenus par le serveur, jamais par le client."),
    ("Rien n'est jamais perdu", "Fermer un écran, s'éloigner, mourir, se déconnecter, arrêter le serveur : les objets "
     "reviennent dans le sac, et ce qui ne rentre pas part dans la boîte de la poste pneumatique, jamais par terre."),
    ("Le client ne fait que demander", "Il n'envoie que l'action voulue et l'identifiant de ce qu'on lui a montré : "
     "jamais d'objet, de quantité possédée ou de position. Le serveur vérifie l'écran ouvert, la distance, le rang "
     "dans la compagnie et l'interrupteur de la fonction."),
    ("Anti-abus", "Budget de 30 paquets par seconde et par joueur, délais entre deux invitations, défis, envois de "
     "lettres (6 par minute) ou gestes, 6 demandes en attente au plus, textes nettoyés et limités en longueur."),
    ("Léger pour le réseau", "La santé et la position des compagnons partent au plus une fois par seconde, et "
     "seulement quand elles changent ; la boîte et le tableau seulement quand on les ouvre."),
]
SOCIAL_COMMANDS = [
    ("/brasshaven company create|invite|leave|kick|promote|rename|friendlyfire|sharexp|chat|join", "tous",
     "Tout ce que fait l'écran de Compagnie, en commande."),
    ("/cc <message>", "tous", "Écrit à ta compagnie seulement."),
    ("/brasshaven trade <joueur>", "tous", "Propose un échange (à moins de 8 blocs)."),
    ("/brasshaven duel <joueur>", "tous", "Lance un défi en duel."),
    ("/brasshaven emote <geste>", "tous", "wave, bow, cheer, clap, point, laugh, thanks ou rally."),
    ("/brasshaven social accept|decline <type> <joueur>", "tous",
     "Répond à une demande (les boutons du chat l'écrivent pour toi)."),
    ("/brasshaven social status", "op", "Joueurs connus, compagnies, colis en attente, contrats ouverts."),
    ("/brasshaven social demo", "op", "Remplit ta compagnie, ta boîte et le tableau avec des exemples (pour tester ou filmer)."),
    ("/brasshaven social selftest", "op", "Vérifie les règles du serveur (sauvegarde, échange, contrats, XP partagée...) "
     "sans joueur ; utilisé par le test automatique du serveur."),
]
KEY_TEXT.update({
    "O": "Écran de la Compagnie (ton groupe : membres, vie, interrupteurs, rejoindre un compagnon)",
    "Y": "Roue des gestes (saluer, s'incliner, acclamer, applaudir, montrer, rire, remercier, rallier)",
    "U": "Fiche du joueur visé (échanger, duel, inviter)",
})
CONFIG_FR.update({
    "social.company.enabled": "Compagnies : invitations, chat de compagnie, tirs amis et XP partagée, compagnons à "
                              "l'écran et sur les cartes, voyage vers un compagnon depuis une pierre.",
    "social.company.maxSize": "Nombre maximal de membres d'une compagnie (de 2 à 100 ; 8 par défaut). Avec une grande guilde, le HUD des compagnons montre les plus proches et « +N » pour les autres.",
    "social.company.xpShareRange": "L'expérience partagée va aux compagnons à moins de ce nombre de blocs (même dimension).",
    "social.company.joinCostLevels": "Niveaux d'expérience payés pour rejoindre un compagnon depuis une pierre (gratuit en créatif).",
    "social.company.joinCooldownSeconds": "Secondes entre deux voyages vers un compagnon.",
    "social.trade.enabled": "Échange sécurisé : les deux acceptent, 3 s de compte à rebours, puis tout change de mains d'un coup.",
    "social.trade.maxDistance": "Distance maximale entre les deux joueurs pendant un échange.",
    "social.post.enabled": "Poste pneumatique : lettres et colis vers tout joueur déjà venu, même absent.",
    "social.post.postageItem": "Objet payé pour l'affranchissement (identifiant ; vide = poste gratuite).",
    "social.post.postageBase": "Affranchissement de chaque lettre ou colis.",
    "social.post.postagePerStack": "Affranchissement en plus pour chaque pile d'objets du colis.",
    "social.post.inboxLimit": "Lettres en attente dans une boîte avant que la poste refuse (les livraisons de contrat et "
                              "les objets rendus passent toujours).",
    "social.post.sendsPerMinute": "Lettres qu'un joueur peut envoyer par minute.",
    "social.contracts.enabled": "Contrats de guilde sur le tableau des contrats.",
    "social.contracts.maxPerPlayer": "Contrats ouverts par joueur.",
    "social.contracts.expiryDays": "Jours (temps réel) avant qu'un contrat expire ; sa récompense revient par la poste.",
    "social.emotes.enabled": "Gestes vus par les joueurs autour.",
    "social.emotes.cooldownTicks": "Ticks entre deux gestes d'un joueur (20 ticks = 1 s).",
    "social.duels.enabled": "Duels : défi, acceptation, compte à rebours, personne ne meurt et rien n'est perdu.",
    "social.duels.radius": "Rayon du cercle de duel ; en sortir fait perdre.",
    "social.duels.maxSeconds": "Durée maximale d'un duel, en secondes (ensuite, match nul).",
    "social.duels.announce": "Annonce le vainqueur de chaque duel à tout le serveur.",
})
INGAME_SHOTS += [
    ("company", "L'écran de la Compagnie", "Touche O. Les membres à gauche (le chef porte la couronne), à droite les "
     "interrupteurs, l'invitation par nom et les boutons pour rejoindre, nommer chef ou renvoyer un compagnon.",
     "multijoueur"),
    ("player_card", "La fiche d'un joueur", "Accroupi + clic droit sur un joueur : sa compagnie, ses duels, et les "
     "boutons Échanger, Duel, Inviter.", "multijoueur"),
    ("emote_wheel", "La roue des gestes", "Touche Y : huit gestes, un clic ou une touche de 1 à 8.", "multijoueur"),
    ("pneumatic_post", "La poste pneumatique", "La boîte de réception : lettres, colis et livraisons de contrat ; la "
     "lettre choisie se lit sur le parchemin, ses objets en dessous.", "multijoueur"),
    ("contract_board", "Le tableau des contrats", "Les contrats ouverts du serveur, les tiens en doré ; à droite ce qui "
     "est demandé, la récompense en dépôt et le temps restant.", "multijoueur"),
    ("trade", "L'échange sécurisé", "Ton offre à gauche, celle de l'autre à droite (on regarde, on ne touche pas), les "
     "deux voyants d'accord au milieu.", "multijoueur"),
]
TEST_CHECKLIST += [
    ("Multijoueur (seul)", ["/brasshaven social demo", "/give @s brasshaven:pneumatic_post", "/give @s brasshaven:contract_board"],
     "Touche O : ta compagnie « Brass Owls » avec Ada. Pose la borne et le tableau : la boîte contient trois envois, le "
     "tableau trois contrats. Touche Y : la roue des gestes."),
    ("Multijoueur (à deux)", ["/brasshaven trade <ami>", "/brasshaven duel <ami>", "/brasshaven company invite <ami>"],
     "L'ami accepte dans le chat. Échange : mettez un objet, acceptez tous les deux, 3 s plus tard les objets changent "
     "de mains. Duel : le coup fatal laisse un demi-cœur. Compagnie : vos cadres dorés sur la carte, /cc pour vous écrire."),
]


def _denizen_texts():
    """Bestiary texts of the peoples and creatures of the places (wf/denizens.py)."""
    from . import denizens
    for pid in denizens.PEOPLES:
        MOBS[pid] = denizens.wiki_folk_text(pid)
    for cid, c in denizens.CREATURES.items():
        MOBS[cid] = c["wiki"]


_denizen_texts()


# Le livre de recettes intégré (client/recipes ; section « livre-recettes » du wiki)
RECIPE_VIEWER_INTRO = ("Pas besoin de JEI : le mod a son propre livre de recettes, aux couleurs du laiton. La liste de "
                       "tous les objets se tient à côté de chaque inventaire, R montre comment fabriquer un objet, U à quoi "
                       "il sert, et le bouton + remplit l'établi tout seul. Il connaît toutes les recettes du serveur : "
                       "Minecraft, Brasshaven et les packs de données.")
RECIPE_KEYS = [
    ("R", "Sur un objet, dans un inventaire : ses recettes (ou clic gauche dans la liste)"),
    ("U", "Ses utilisations (ou clic droit dans la liste)"),
    ("I", "Afficher / masquer la liste des objets"),
    ("Retour arrière", "Revenir à l'objet précédent"),
]
INGAME_SHOTS += [
    ("recipe_panel", "La liste des objets", "À côté de l'établi : tous les objets, ceux du mod d'abord, avec une "
     "recherche par nom, @mod ou #tag.", "livre-recettes"),
    ("recipe_view", "Une recette", "R sur la clé à molette en laiton : sa recette sur la grille de l'établi, avec le "
     "bouton + pour la remplir.", "livre-recettes"),
    ("recipe_uses", "Les utilisations", "U sur le lingot de laiton : toutes les recettes qui l'utilisent, page par "
     "page.", "livre-recettes"),
    ("recipe_fill", "Le bouton +", "Les ingrédients passent de l'inventaire à la grille de l'établi, déplacés par le "
     "serveur comme avec le livre de recettes de Minecraft.", "livre-recettes"),
]

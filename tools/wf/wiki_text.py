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
    "G": "Baguette du bâtisseur : changer de symétrie (désactivée, miroir X, miroir Z, X + Z)",
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

# Merveilles (méga-structures) : affichées en grand, avec rotation 360° et vue en coupe. Le générateur y ajoute
# toute structure citée dans les pages « wonders* » du Manuel (tools/wf/guide.py) ; l'ordre ci-dessous passe en premier.
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
                         "fumantes reliées par des tuyaux. Des araignées-horloges et des drones à vapeur y rôdent. Dans "
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
                    "puis à la salle du trône. Le trésor ? Une trappe cachée sous le tapis, derrière le trône.",
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
                 "accrochées aux parois, passerelles, tuyaux et lampes Edison.",
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
NEW_INTRO = ("Tout ce qui est arrivé dans le mod cette nuit, en un coup d'œil. Chaque carte mène à sa section "
             "détaillée ; la liste « Tester en jeu » juste en dessous donne les commandes pour tout essayer en "
             "quelques minutes.")
# (titre, texte, ancre, vignette) — vignette : "mob:<id>", "struct:<id>" ou "items:<id>,<id>,..."
NEW_TONIGHT = [
    ("Gadgets à vapeur", "Clé à molette, grappin, planeur, pistolet à rivets, montre à gousset et boussole de "
     "dirigeable : six objets de laiton pour grimper, planer, tirer et s'orienter.", "gadgets",
     "items:brass_wrench,grappling_hook,brass_glider,rivet_gun,pocket_watch,airship_compass"),
    ("Burin et table de taille", "Le burin taille un bloc en sa variante suivante (pierre, briques, moussues, "
     "sculptées…) ; la table transforme une pile entière, gratuitement. Avec 11 blocs qu'on n'obtient qu'au burin.",
     "construction", "items:chisel,chisel_table,engraved_brass,brass_grille,chiseled_lithite_bricks,mahogany_parquet"),
    ("Symétrie de la baguette", "Accroupi + clic sur un bloc pour poser le centre du miroir, touche G pour choisir "
     "miroir X, Z ou les deux : tes constructions se copient en miroir.", "symetrie",
     "items:builder_wand,master_builder_wand"),
    ("Le golem de laiton", "Un compagnon à construire : deux blocs de laiton et un cœur mécanique. Il te suit et "
     "cogne les monstres.", "golem", "mob:brass_golem"),
    ("Araignées-horloges et drones", "Deux automates ennemis dans les Terres rouillées, la Vallée des engrenages, "
     "la Citadelle et les Bas-fonds.", "automates", "mob:clockwork_spider"),
    ("Le Grand Horloger", "Un nouveau boss sous la Citadelle d'horlogerie, avec arrêt du temps et sonnerie de "
     "minuit. Son Souvenir forge le Pendule du Grand Horloger.", "horloger", "mob:grand_clockmaker"),
    ("Cité naine des profondeurs", "Un royaume nain taillé à 40-50 blocs sous terre, rivières de lave et salle du "
     "trône.", "s-dwarven_city", "struct:dwarven_city"),
    ("Cathédrale de cristal", "Une cathédrale gothique dans une géode géante, tout au fond du monde.",
     "s-crystal_cathedral", "struct:crystal_cathedral"),
    ("Palais sylvain", "Un palais elfique autour d'un arbre d'argent de 70 blocs.", "s-sylvan_palace",
     "struct:sylvan_palace"),
    ("Manoir de l'inventeur", "Une demeure victorienne steampunk, sa serre et son laboratoire secret.",
     "s-inventor_manor", "struct:inventor_manor"),
    ("Îles célestes", "Un archipel flottant à 200 blocs d'altitude, relié par des ponts de corde.", "s-sky_isles",
     "struct:sky_isles"),
    ("Fonderie géothermique", "Des forges bâties dans un volcan fumant, avec pont roulant et caldeira de lave.",
     "s-geothermal_foundry", "struct:geothermal_foundry"),
    ("Observatoire Tesla", "Coupole, télescope géant, bobine Tesla de 70 blocs et planétarium sur un piton.",
     "s-tesla_observatory", "struct:tesla_observatory"),
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
    ("Le Grand Horloger", ["/wayfarers boss grand_clockmaker"],
     "Il apparaît à 6 blocs (arène de 20 blocs autour de toi). Guette l'arrêt du temps (cercle qui se referme) et, "
     "à mi-vie, le rugissement puis minuit. Pour le vrai repaire : /wayfarers tp clockwork_citadel."),
    ("Merveilles en surface", ["/wayfarers tp inventor_manor", "/wayfarers tp sylvan_palace",
                               "/wayfarers tp geothermal_foundry", "/wayfarers tp tesla_observatory",
                               "/wayfarers tp sky_isles"],
     "Téléportation à la plus proche (générée si besoin, quelques secondes ; si aucune n'est assez près, le "
     "message le dit). Les Îles célestes flottent vers y 160-225 : tu arrives dessus ou dessous ; en dessous, "
     "passe en /gamemode spectator pour monter."),
    ("Merveilles souterraines", ["/wayfarers locate dwarven_city", "/wayfarers locate crystal_cathedral",
                                 "/locate structure wayfarers:dwarven_city", "/gamemode spectator"],
     "locate donne les coordonnées ; tp t'amène à la surface juste au-dessus. En spectateur, descends à travers la "
     "roche : la cité est vers y −50, le sol de la cathédrale vers y −40."),
]

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

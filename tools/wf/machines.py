"""Simple machines: one block each, no power network. One table drives Java registration, textures, models,
blockstates, recipes, loot, tags, translations and the manual page (like decor.py / metals.py)."""
from . import texgen_steam as S

# id -> dict(kind (MachineBlock.Kind), glyph (texgen_steam.MACHINE_GLYPHS), en, fr, desc: [(en, fr)] (3 lines max),
#            recipe: (pattern, key, count), color (MapColor), light)
MACHINES = {
    "auto_harvester": dict(
        kind="HARVESTER", glyph="harvester", en="Auto-Harvester", fr="Moissonneuse automatique", color="GOLD",
        desc=[("Harvests ripe crops around it and replants them.", "Récolte les cultures mûres autour d'elle et replante."),
              ("The harvest goes into a chest next to it.", "La récolte va dans un coffre collé à elle."),
              ("Click it: area, replanting, output side, redstone mode.", "Clic : zone, replantation, côté de sortie, mode redstone.")],
        recipe=(["BHB", "BCB", "BRB"], {"B": "brasshaven:brass_ingot", "H": "iron_hoe", "C": "chest", "R": "redstone"}, 1)),
    "sprinkler": dict(
        kind="SPRINKLER", glyph="sprinkler", en="Sprinkler", fr="Arroseur", color="COLOR_ORANGE",
        desc=[("Place it among your crops: plants below grow faster.", "Pose-le au milieu des cultures : les plantes dessous poussent plus vite."),
              ("Keeps farmland wet, no water needed.", "Garde la terre labourée humide, sans eau."),
              ("Click it: area (3x3 to 7x7) and redstone mode.", "Clic : zone (3x3 à 7x7) et mode redstone.")],
        recipe=([" C ", "CWC", " C "], {"C": "copper_ingot", "W": "water_bucket"}, 1)),
    "vacuum_hopper": dict(
        kind="VACUUM", glyph="vacuum", en="Vacuum Hopper", fr="Trémie aspirante", color="COLOR_CYAN",
        desc=[("Pulls in items and experience nearby.", "Aspire les objets et l'expérience autour."),
              ("Feeds the chest below it.", "Remplit le coffre en dessous."),
              ("Click it: range, item filter, stored XP, redstone mode.", "Clic : portée, filtre d'objets, XP stockée, mode redstone.")],
        recipe=(["BEB", "BHB", " B "], {"B": "brasshaven:brass_ingot", "E": "ender_pearl", "H": "hopper"}, 1)),
    "block_breaker": dict(
        kind="BREAKER", glyph="breaker", en="Block Breaker", fr="Casseur de blocs", color="COLOR_GRAY",
        desc=[("On a redstone pulse, breaks the block in front.", "Sur une impulsion de redstone, casse le bloc devant."),
              ("Drops go into the chest behind it.", "Les objets vont dans le coffre derrière."),
              ("Click it to see what it breaks next.", "Clic : voir ce qu'il cassera ensuite.")],
        recipe=(["BBB", "BPB", "BRB"], {"B": "brasshaven:brass_ingot", "P": "iron_pickaxe", "R": "redstone"}, 1)),
    "block_placer": dict(
        kind="PLACER", glyph="placer", en="Block Placer", fr="Poseur de blocs", color="COLOR_GRAY",
        desc=[("On a redstone pulse, places a block in front.", "Sur une impulsion de redstone, pose un bloc devant."),
              ("Takes blocks from the chest behind, or its own slots.", "Prend les blocs dans le coffre derrière, ou dans ses cases."),
              ("Click it to see which block it places next.", "Clic : voir quel bloc il posera ensuite.")],
        recipe=(["BBB", "BDB", "BRB"], {"B": "brasshaven:brass_ingot", "D": "dispenser", "R": "redstone"}, 1)),
    "redstone_timer": dict(
        kind="TIMER", glyph="timer", en="Redstone Timer", fr="Minuteur de redstone", color="COLOR_RED",
        desc=[("Sends a short redstone pulse every few seconds.", "Envoie une courte impulsion de redstone toutes les quelques secondes."),
              ("Click it: interval (0.5 s to 1 min), pulse length, redstone mode.", "Clic : intervalle (0,5 s à 1 min), durée d'impulsion, mode redstone."),
              ("No clock circuit to build!", "Plus besoin de construire une horloge !")],
        recipe=([" R ", "RCR", " R "], {"R": "redstone", "C": "clock"}, 1)),
    "wireless_transmitter": dict(
        kind="TRANSMITTER", glyph="transmitter", en="Wireless Transmitter", fr="Émetteur sans fil", color="COLOR_CYAN",
        desc=[("Sends the redstone signal it receives through the air.", "Envoie par les airs le signal de redstone qu'il reçoit."),
              ("Click it to pick its channel colour (or use a dye on it).", "Clic : choisir la couleur du canal (ou une teinture dessus)."),
              ("Receivers of the same colour turn on.", "Les récepteurs de la même couleur s'allument.")],
        recipe=([" A ", "BRB", "BBB"], {"A": "lightning_rod", "B": "brasshaven:brass_ingot", "R": "redstone_block"}, 1)),
    "wireless_receiver": dict(
        kind="RECEIVER", glyph="receiver", en="Wireless Receiver", fr="Récepteur sans fil", color="COLOR_CYAN",
        desc=[("Outputs redstone while a transmitter of its colour is on.", "Émet de la redstone tant qu'un émetteur de sa couleur est allumé."),
              ("Click it to pick its channel colour (or use a dye on it).", "Clic : choisir la couleur du canal (ou une teinture dessus)."),
              ("Works anywhere in the same dimension (chunks loaded).", "Marche partout dans la même dimension (chunks chargés).")],
        recipe=(["B B", "BRB", "BBB"], {"B": "brasshaven:brass_ingot", "R": "redstone"}, 1)),
    "entity_detector": dict(
        kind="DETECTOR", glyph="detector", en="Entity Detector", fr="Détecteur de créatures", color="COLOR_RED",
        desc=[("Outputs redstone while something is near (1 per creature, max 15).", "Émet de la redstone quand quelque chose approche (1 par créature, max 15)."),
              ("Click it: target (players, monsters, animals, items, all).", "Clic : cible (joueurs, monstres, animaux, objets, tous)."),
              ("Range 2 to 16 blocks; the output can be inverted.", "Portée de 2 à 16 blocs ; la sortie peut être inversée.")],
        recipe=(["BBB", "BEB", "BRB"], {"B": "brasshaven:brass_ingot", "E": "ender_eye", "R": "redstone"}, 1)),
}

GUIDE = [
    ("machines", "brasshaven:auto_harvester", ("Farm machines", "Machines de ferme"), [
        ("No cables, no power: each machine is one block that does one job. Click a machine to open its screen: "
         "what it does, what it is doing right now, and its settings. The Brass Wrench turns it; sneak + wrench "
         "changes its main setting without opening the screen.",
         "Ni câbles ni énergie : chaque machine est un bloc qui fait une seule chose. Clique sur une machine pour "
         "ouvrir son écran : ce qu'elle fait, ce qu'elle fait en ce moment, et ses réglages. La clé à molette la "
         "tourne ; accroupi + clé change son réglage principal sans ouvrir l'écran."),
        ("A simple farm: Sprinkler in the middle of the field, Auto-Harvester at the edge with a chest against it. "
         "Wheat, carrots, potatoes, beetroots, nether wart, cocoa, melons, pumpkins, sugar cane, cactus and bamboo "
         "all work.",
         "Une ferme simple : un arroseur au milieu du champ, une moissonneuse au bord avec un coffre collé. Blé, "
         "carottes, pommes de terre, betteraves, verrues du Nether, cacao, melons, citrouilles, canne à sucre, "
         "cactus et bambou marchent tous."),
        ("Vacuum Hopper above a chest: it collects everything dropped around it, even experience.",
         "Trémie aspirante au-dessus d'un coffre : elle ramasse tout ce qui tombe autour, même l'expérience."),
        ("Craft: most machines use brass ingots and redstone around the tool of their job (hoe, pickaxe, dispenser, "
         "hopper...); the Sprinkler is four copper ingots around a water bucket.",
         "Fabrication : la plupart des machines demandent des lingots de laiton et de la redstone autour de l'outil "
         "de leur métier (houe, pioche, distributeur, entonnoir...) ; l'arroseur, quatre lingots de cuivre autour "
         "d'un seau d'eau."),
    ], ["brasshaven:auto_harvester", "brasshaven:sprinkler", "brasshaven:vacuum_hopper"]),
    ("machine_screens", "brasshaven:brass_wrench", ("Machine screens", "Écrans des machines"), [
        ("Top of the screen: the machine and a status line with a lamp. Green: working. Amber: waiting (no ripe "
         "crops, no redstone signal...). Red: stuck (output full, nothing to place). Hover anything for a tip.",
         "En haut : la machine et une ligne d'état avec un voyant. Vert : elle travaille. Orange : elle attend "
         "(pas de culture mûre, pas de signal...). Rouge : bloquée (sortie pleine, rien à poser). Survole n'importe "
         "quoi pour une astuce."),
        ("Area machines (Harvester, Sprinkler, Vacuum, Detector): pick the size, and the box button draws the work "
         "area in the world until you switch it off.",
         "Machines à zone (moissonneuse, arroseur, trémie, détecteur) : choisis la taille ; le bouton cadre dessine "
         "la zone de travail dans le monde jusqu'à ce que tu l'éteignes."),
        ("Redstone mode (Harvester, Sprinkler, Vacuum, Timer): always on, only with a signal (lit torch) or only "
         "without one (unlit torch). The little lamp next to it shows the signal the machine receives.",
         "Mode redstone (moissonneuse, arroseur, trémie, minuteur) : toujours actif, seulement avec un signal "
         "(torche allumée) ou seulement sans (torche éteinte). La petite lampe à côté montre le signal reçu."),
        ("Harvester: replanting and output side (a green dot marks the sides with a container). Vacuum: 5 filter "
         "items (only these, or all but these) and a button to take the stored experience. Shift-click fills or "
         "empties their slots.",
         "Moissonneuse : replantation et côté de sortie (un point vert marque les côtés avec un conteneur). Trémie : "
         "5 objets filtrés (seulement eux, ou tout sauf eux) et un bouton pour récupérer l'expérience. Maj + clic "
         "remplit ou vide leurs cases."),
    ], ["brasshaven:auto_harvester", "brasshaven:vacuum_hopper", "brasshaven:brass_wrench"]),
    ("redstone_easy", "brasshaven:redstone_timer", ("Easy redstone", "Redstone facile"), [
        ("Redstone Timer: a ready-made clock. Its screen has a slider for the interval (0.5 s to 1 minute), the "
         "pulse length, a redstone mode to pause it, and a bar counting down to the next pulse.",
         "Minuteur de redstone : une horloge toute faite. Son écran a un curseur pour l'intervalle (0,5 s à "
         "1 minute), la durée de l'impulsion, un mode redstone pour le mettre en pause et une barre qui décompte "
         "jusqu'à la prochaine impulsion."),
        ("Tree farm in 3 blocks: Timer -> Block Breaker facing the trunk -> Block Placer with saplings below it. "
         "Their screens show the block they will break or place next, and where the items go.",
         "Ferme à arbres en 3 blocs : minuteur -> casseur de blocs face au tronc -> poseur avec des pousses. Leurs "
         "écrans montrent le prochain bloc cassé ou posé, et où vont les objets."),
        ("Wireless Transmitter and Receiver: pick the same colour among the 16 swatches of their screens (or use a "
         "dye on them) and the signal travels without wires; the screen counts the transmitters and receivers on "
         "that channel.",
         "Émetteur et récepteur sans fil : choisis la même couleur parmi les 16 pastilles de leur écran (ou une "
         "teinture dessus) et le signal passe sans fil ; l'écran compte les émetteurs et récepteurs du canal."),
        ("Entity Detector: pick what it looks for (players, monsters, animals, items or all creatures) and how far; "
         "it outputs 1 per creature (max 15), or the opposite when inverted: on while nothing is near.",
         "Détecteur de créatures : choisis ce qu'il cherche (joueurs, monstres, animaux, objets ou toutes les "
         "créatures) et à quelle distance ; il émet 1 par créature (max 15), ou l'inverse quand il est inversé : "
         "allumé tant que rien n'approche."),
    ], ["brasshaven:redstone_timer", "brasshaven:block_breaker", "brasshaven:block_placer",
        "brasshaven:wireless_transmitter", "brasshaven:wireless_receiver", "brasshaven:entity_detector"]),
]

# ---------------------------------------------------------------- machine screens (client/gui/MachineScreen.java)
# kind -> (what it does, how to set it up): the header line under the name, and its tooltip
WHAT = {
    "harvester": (("Harvests ripe crops around it, replants and stores the harvest.",
                   "Récolte les cultures mûres autour d'elle, replante et range tout."),
                  ("Put a chest against it, or let it fill its own slots.",
                   "Colle un coffre contre elle, ou laisse-la remplir ses cases.")),
    "sprinkler": (("Keeps farmland wet and makes the plants in its area grow faster.",
                   "Garde la terre humide et fait pousser plus vite les plantes de sa zone."),
                  ("Put it in the middle of the field, above the crops.",
                   "Pose-le au milieu du champ, au-dessus des cultures.")),
    "vacuum": (("Pulls in items and experience nearby, then feeds the container below.",
                "Aspire objets et expérience autour, puis remplit le conteneur dessous."),
               ("Put a chest or a hopper under it.", "Pose un coffre ou un entonnoir dessous.")),
    "breaker": (("Breaks the block in front of it on each redstone pulse.",
                 "Casse le bloc devant lui à chaque impulsion de redstone."),
                ("Drops go into the container behind it. Pair it with a Redstone Timer.",
                 "Les objets vont dans le conteneur derrière. Associe-le à un minuteur.")),
    "placer": (("Places a block in front of it on each redstone pulse.",
                "Pose un bloc devant lui à chaque impulsion de redstone."),
               ("Takes blocks from the container behind it, then from its own slots.",
                "Prend les blocs dans le conteneur derrière, puis dans ses cases.")),
    "timer": (("Sends a redstone pulse at a steady pace: a clock with nothing to build.",
               "Une impulsion de redstone à rythme régulier : une horloge toute faite."),
              ("Its signal goes out on every side, like a redstone block.",
               "Son signal sort de tous les côtés, comme un bloc de redstone.")),
    "transmitter": (("Sends the redstone signal it receives to the receivers of its colour.",
                     "Envoie le signal de redstone qu'il reçoit aux récepteurs de sa couleur."),
                    ("Works anywhere in the same dimension (chunks loaded).",
                     "Marche partout dans la même dimension (chunks chargés).")),
    "receiver": (("Outputs redstone while a transmitter of its colour is powered.",
                  "Émet de la redstone tant qu'un émetteur de sa couleur est alimenté."),
                 ("Works anywhere in the same dimension (chunks loaded).",
                  "Marche partout dans la même dimension (chunks chargés).")),
    "detector": (("Outputs redstone when something comes near: 1 per creature, up to 15.",
                  "Émet de la redstone quand on approche : 1 par créature, max 15."),
                 ("Opens doors, lights lamps, rings bells...", "Ouvre des portes, allume des lampes, sonne des cloches...")),
}

# Row labels (52 px at most, checked by check_gui) and their tooltips.
LABELS = {
    "area": (("Area", "Zone"), ("Size of the square it works on, centred on the machine.",
                                "Taille du carré où elle travaille, centré sur la machine.")),
    "range": (("Range", "Portée"), ("How far it reaches, in blocks, in every direction.",
                                    "Jusqu'où elle porte, en blocs, dans toutes les directions.")),
    "replant": (("Replant", "Replanter"), ("Replant each crop it harvests (it keeps one seed for that).",
                                           "Replanter chaque culture récoltée (elle garde une graine pour ça).")),
    "output": (("Output", "Sortie"), ("Where the harvest goes. Whatever does not fit stays in its own slots.",
                                      "Où va la récolte. Ce qui ne rentre pas reste dans ses cases.")),
    "redstone": (("Redstone", "Redstone"), ("When it may work, depending on the redstone signal it receives.",
                                            "Quand elle peut travailler, selon le signal de redstone reçu.")),
    "xp": (("XP", "XP"), ("Collect experience orbs, and take what is stored.",
                          "Ramasser les orbes d'expérience, et récupérer le stock.")),
    "filter": (("Filter", "Filtre"), ("Put an item in a box to filter it (a copy: your item stays with you). "
                                      "Empty filter: it takes everything.",
                                      "Pose un objet dans une case pour le filtrer (une copie : ton objet reste à toi). "
                                      "Filtre vide : elle prend tout.")),
    "front": (("In front", "Devant"), ("The block it will break on the next redstone pulse.",
                                       "Le bloc qu'il cassera à la prochaine impulsion de redstone.")),
    "drops": (("Output", "Sortie"), ("Drops go into the container behind it, else into its own slots, else on the ground.",
                                     "Les objets vont dans le conteneur derrière, sinon dans ses cases, sinon par terre.")),
    "next": (("Next", "Suivant"), ("The block it will place on the next redstone pulse.",
                                   "Le bloc qu'il posera à la prochaine impulsion de redstone.")),
    "source": (("Source", "Source"), ("It takes blocks from the container behind it first, then from its own slots.",
                                      "Il prend d'abord les blocs du conteneur derrière, puis ceux de ses cases.")),
    "facing": (("Facing", "Direction"), ("The side it works on. Turn it with the Brass Wrench.",
                                         "Le côté où il travaille. Tourne-le avec la clé à molette.")),
    "interval": (("Interval", "Intervalle"), ("Time between two pulses. Drag the knob, or Tab to it and use the arrow keys.",
                                              "Temps entre deux impulsions. Fais glisser, ou Tab puis les flèches.")),
    "pulse": (("Pulse", "Impulsion"), ("How long each pulse stays on.", "Combien de temps chaque impulsion reste allumée.")),
    "next_pulse": (("Next", "Prochaine"), ("Time left before the next pulse.", "Temps restant avant la prochaine impulsion.")),
    "channel": (("Channel", "Canal"), ("Transmitters and receivers of the same colour are linked.",
                                       "Les émetteurs et récepteurs de même couleur sont reliés.")),
    "target": (("Target", "Cible"), ("What it counts.", "Ce qu'il compte.")),
    "signal": (("Signal", "Signal"), ("Normal: 1 per creature (max 15). Inverted: 15 while nothing is near, else 0.",
                                      "Normal : 1 par créature (max 15). Inversé : 15 tant que rien n'est proche, sinon 0.")),
}

STATUS = {
    "harvesting": ("Harvesting: %s ripe crops in range", "Récolte : %s cultures mûres"),
    "no_ripe_crops": ("Waiting: no ripe crops in range", "En attente : rien de mûr"),
    "watering": ("Watering %s plants and farmland", "Arrose %s plantes et terres"),
    "no_plants": ("Idle: no crops or farmland in range", "Inactif : ni culture ni terre"),
    "collecting": ("Collecting items", "Aspire les objets"),
    "waiting_items": ("Waiting for items to collect", "En attente d'objets"),
    "output_full": ("Stopped: output full", "Bloquée : sortie pleine"),
    "needs_signal": ("Waiting for a redstone signal", "Attend un signal de redstone"),
    "stopped_by_signal": ("Paused by a redstone signal", "En pause : signal de redstone"),
    "ready_break": ("Ready: breaks %s on the next pulse", "Prêt : cassera %s"),
    "nothing_to_break": ("Waiting: nothing in front to break", "En attente : rien devant"),
    "cant_break": ("Can't break %s", "Ne peut pas casser %s"),
    "ready_place": ("Ready: places %s on the next pulse", "Prêt : posera %s"),
    "front_blocked": ("Stuck: the space in front is taken", "Bloqué : la place devant est prise"),
    "no_blocks": ("Stuck: no blocks to place", "Bloqué : aucun bloc à poser"),
    "countdown": ("Next pulse in %s", "Prochaine impulsion dans %s"),
    "pulse": ("Pulse!", "Impulsion !"),
    "broadcasting": ("Broadcasting: signal on", "Émet : signal allumé"),
    "silent": ("No redstone input: receivers off", "Aucun signal reçu : récepteurs éteints"),
    "receiving": ("Receiving: signal on", "Reçoit : signal allumé"),
    "no_transmitter": ("No transmitter of this colour is on", "Aucun émetteur de cette couleur allumé"),
    "detected": ("%s in range", "%s à portée"),
    "nothing_near": ("Nothing in range", "Rien à portée"),
}

GUI = {
    "status.tip": ("What the machine is doing right now. Green: working, amber: waiting, red: stuck.",
                   "Ce que fait la machine en ce moment. Vert : au travail, orange : en attente, rouge : bloquée."),
    "area.tip": ("Works on a %sx%s area", "Travaille sur une zone de %sx%s"),
    "range.tip": ("Reaches %s blocks around it", "Porte à %s blocs autour"),
    "show_area": ("Show area", "Montrer la zone"),
    "show_area.tip": ("Show the work area in the world (stays on after closing; click again to hide it).",
                      "Montrer la zone de travail dans le monde (reste affichée après fermeture ; reclique pour la cacher)."),
    "redstone.always": ("Always on", "Toujours actif"),
    "redstone.always.tip": ("Always on: ignores redstone.", "Toujours actif : ignore la redstone."),
    "redstone.high": ("With a signal", "Avec un signal"),
    "redstone.high.tip": ("Works only while it receives a redstone signal.",
                          "Travaille seulement quand il reçoit un signal de redstone."),
    "redstone.low": ("Without a signal", "Sans signal"),
    "redstone.low.tip": ("Works only while it receives no redstone signal (a lever pauses it).",
                         "Travaille seulement sans signal de redstone (un levier le met en pause)."),
    "input_on": ("Signal received", "Signal reçu"),
    "input_off": ("No signal", "Aucun signal"),
    "input.tip": ("The redstone signal this machine receives right now.",
                  "Le signal de redstone que cette machine reçoit en ce moment."),
    "on": ("On", "Oui"),
    "off": ("Off", "Non"),
    "output.auto": ("Any container", "Tout conteneur"),
    "output.auto.tip": ("Any container: below first, then the sides, then above.",
                        "Tout conteneur : dessous d'abord, puis les côtés, puis dessus."),
    "output.down": ("Below", "Dessous"),
    "output.down.tip": ("Only the container below it.", "Seulement le conteneur en dessous."),
    "output.up": ("Above", "Dessus"),
    "output.up.tip": ("Only the container above it.", "Seulement le conteneur au-dessus."),
    "output.north": ("North", "Nord"),
    "output.north.letter": ("N", "N"),
    "output.north.tip": ("Only the container on its north side.", "Seulement le conteneur au nord."),
    "output.south": ("South", "Sud"),
    "output.south.letter": ("S", "S"),
    "output.south.tip": ("Only the container on its south side.", "Seulement le conteneur au sud."),
    "output.west": ("West", "Ouest"),
    "output.west.letter": ("W", "O"),
    "output.west.tip": ("Only the container on its west side.", "Seulement le conteneur à l'ouest."),
    "output.east": ("East", "Est"),
    "output.east.letter": ("E", "E"),
    "output.east.tip": ("Only the container on its east side.", "Seulement le conteneur à l'est."),
    "output.keep": ("Keep", "Garder"),
    "output.keep.tip": ("Keep the harvest in its own 9 slots.", "Garder la récolte dans ses 9 cases."),
    "output.container": ("A container is there.", "Un conteneur est là."),
    "output.nothing": ("No container on that side.", "Pas de conteneur de ce côté."),
    "collect_xp.tip": ("Collect experience orbs around it.", "Ramasser les orbes d'expérience autour."),
    "take_xp.tip": ("Take the stored experience.", "Récupérer l'expérience stockée."),
    "filter.allow": ("Allow only these", "Seulement ceux-ci"),
    "filter.allow.tip": ("Allow list: collects only the items in the filter. Click: switch to block list.",
                         "Liste blanche : n'aspire que les objets du filtre. Clic : passer en liste noire."),
    "filter.deny": ("Block these", "Tout sauf ceux-ci"),
    "filter.deny.tip": ("Block list: collects everything except the items in the filter. Click: switch to allow list.",
                        "Liste noire : aspire tout sauf les objets du filtre. Clic : passer en liste blanche."),
    "filter.slot.tip": ("Click with an item to filter it (a copy is shown, your item stays with you); "
                        "click with an empty hand to clear.",
                        "Clique avec un objet pour le filtrer (une copie s'affiche, ton objet reste à toi) ; "
                        "main vide pour vider."),
    "pulse.tip": ("Each pulse stays on %s", "Chaque impulsion dure %s"),
    "pulse_now": ("now", "maintenant"),
    "seconds": ("%s s", "%s s"),
    "decimal": (".", ","),
    "channel.tip": ("Channel: %s", "Canal : %s"),
    "channel.shared": ("Linked: %s transmitters, %s receivers", "Reliés : %s émetteurs, %s récepteurs"),
    "target.players.tip": ("Players (not spectators)", "Joueurs (pas les spectateurs)"),
    "target.monsters.tip": ("Monsters", "Monstres"),
    "target.animals.tip": ("Animals", "Animaux"),
    "target.items.tip": ("Items lying on the ground", "Objets posés par terre"),
    "target.living.tip": ("Every creature, players included", "Toutes les créatures, joueurs compris"),
    "normal": ("Normal", "Normal"),
    "normal.tip": ("On while something is near: 1 per creature, up to 15.",
                   "Allumé quand quelque chose approche : 1 par créature, max 15."),
    "inverted": ("Inverted", "Inversé"),
    "inverted.tip": ("On (15) while nothing is near; off as soon as something comes.",
                     "Allumé (15) tant que rien n'approche ; éteint dès que quelque chose arrive."),
    "signal_strength": ("Signal %s", "Signal %s"),
    "stored": ("Stored", "Stock"),
    "take_all": ("Take all", "Tout prendre"),
    "take_all.tip": ("Take everything into your inventory (middle-click a slot: sort).",
                     "Tout prendre dans ton inventaire (clic molette sur une case : trier)."),
    "the_block": ("the block", "le bloc"),
    "front.empty": ("nothing", "rien"),
    "next.none": ("no block", "aucun bloc"),
    "drops.chest": ("chest behind", "coffre derrière"),
    "drops.self": ("its own slots", "ses cases"),
    "source.chest": ("chest behind", "coffre derrière"),
    "source.self": ("its own slots", "ses cases"),
    "dir.north": ("North", "Nord"),
    "dir.south": ("South", "Sud"),
    "dir.west": ("West", "Ouest"),
    "dir.east": ("East", "Est"),
    "dir.up": ("Up", "Haut"),
    "dir.down": ("Down", "Bas"),
}


def gui_lang():
    en, fr = {}, {}
    k = "gui.brasshaven.machine."
    for kind, ((we, wf), (he, hf)) in WHAT.items():
        en[k + "what." + kind], fr[k + "what." + kind] = we, wf
        en[k + "howto." + kind], fr[k + "howto." + kind] = he, hf
    for key, ((le, lf), (te, tf)) in LABELS.items():
        en[k + "label." + key], fr[k + "label." + key] = le, lf
        en[k + "label." + key + ".tip"], fr[k + "label." + key + ".tip"] = te, tf
    for key, (e, f) in STATUS.items():
        en[k + "status." + key], fr[k + "status." + key] = e, f
    for key, (e, f) in GUI.items():
        en[k + key], fr[k + key] = e, f
    return en, fr


def check_gui():
    """Texts that must fit their place in MachineScreen (Minecraft glyph advances): returns error strings."""
    from .guide import text_width, wrap
    errors = []
    for li, lang in ((0, "en"), (1, "fr")):
        for kind, (what, _how) in WHAT.items():
            if len(wrap(what[li], 252 - 36 - 10)) > 2:
                errors.append(f"machine screen ({lang}): the description of {kind} needs more than 2 lines")
        for key, (label, _tip) in LABELS.items():
            if text_width(label[li]) > 52:
                errors.append(f"machine screen ({lang}): row label {key!r} is wider than 52 px")
        for key, text in STATUS.items():
            sample = text[li].replace("%s", "12")
            if text_width(sample) > 252 - 20 - 22:
                errors.append(f"machine screen ({lang}): status {key!r} is wider than the status line")
        for key in ("front.empty", "next.none", "drops.chest", "drops.self", "source.chest", "source.self"):
            if text_width(GUI[key][li]) > 114:
                errors.append(f"machine screen ({lang}): {key!r} is wider than its row")
        if text_width(GUI["stored"][li]) > 40:
            errors.append(f"machine screen ({lang}): 'stored' caption is wider than 40 px")
        if text_width(GUI["channel.shared"][li].replace("%s", "12")) > 232:
            errors.append(f"machine screen ({lang}): 'channel.shared' is wider than the window")
    return errors


def textures():
    """{texture path under textures/: canvas}."""
    out = {"block/machine_side": S.machine_side(60), "block/machine_top": S.machine_top(61),
           "block/machine_front_frame": S.machine_front_frame(62)}
    for mid, m in MACHINES.items():
        out[f"block/{mid}_front"] = S.machine_face(m["glyph"], False, 62)
        out[f"block/{mid}_front_on"] = S.machine_face(m["glyph"], True, 62)
    return out


def block_model(mid, on):
    """Block model of a machine, off or on (the ``powered`` state: running, receiving or sending a signal).

    The casing is a cube whose front (north, turned by the blockstate) is the frame with its window cut out; the glyph
    window sits one pixel deeper, framed by four thin recess walls (so no angle looks through the block). On, the
    window element is emissive (light_emission 15, unshaded): the lit glyph glows even in a dark cave."""
    ns = "brasshaven"
    win = {"uv": [3, 3, 13, 13], "texture": "#window", "cullface": "north"}
    window = {"from": [3, 3, 1], "to": [13, 13, 1], "faces": {"north": win}}
    if on:
        window.update(shade=False, light_emission=15)
    walls = [  # (from, to, face, uv on the frame: its shadowed / lit inner bevel)
        ([2, 3, 0], [3, 13, 1], "east", [13, 3, 14, 13]),
        ([13, 3, 0], [14, 13, 1], "west", [2, 3, 3, 13]),
        ([3, 13, 0], [13, 14, 1], "down", [3, 2, 13, 3]),
        ([3, 2, 0], [13, 3, 1], "up", [3, 13, 13, 14]),
    ]
    elements = [
        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": {
            "down": {"texture": "#top", "cullface": "down"}, "up": {"texture": "#top", "cullface": "up"},
            "north": {"texture": "#frame", "cullface": "north"}, "south": {"texture": "#side", "cullface": "south"},
            "west": {"texture": "#side", "cullface": "west"}, "east": {"texture": "#side", "cullface": "east"}}},
        window,
    ] + [{"from": f, "to": t, "faces": {face: {"uv": uv, "texture": "#frame", "cullface": "north"}}}
         for f, t, face, uv in walls]
    suffix = "_on" if on else ""
    return {"parent": "minecraft:block/block", "render_type": "minecraft:cutout",
            "textures": {"particle": f"{ns}:block/{mid}_front", "top": f"{ns}:block/machine_top",
                         "side": f"{ns}:block/machine_side", "frame": f"{ns}:block/machine_front_frame",
                         "window": f"{ns}:block/{mid}_front{suffix}"},
            "elements": elements}


def lang():
    en, fr = {}, {}
    for mid, m in MACHINES.items():
        en[f"block.brasshaven.{mid}"], fr[f"block.brasshaven.{mid}"] = m["en"], m["fr"]
        for i, (e, f) in enumerate(m["desc"]):
            suffix = "" if i == 0 else str(i + 1)
            en[f"block.brasshaven.{mid}.desc{suffix}"], fr[f"block.brasshaven.{mid}.desc{suffix}"] = e, f
    msgs = {
        "message.brasshaven.machine.area": ("Area: %sx%s", "Zone : %sx%s"),
        "message.brasshaven.machine.interval": ("Pulse every %s s", "Impulsion toutes les %s s"),
        "message.brasshaven.machine.channel": ("Channel: %s", "Canal : %s"),
        "message.brasshaven.machine.xp": ("+%s experience collected", "+%s d'expérience récupérée"),
        "message.brasshaven.machine.detector": ("Detects %s within %s blocks", "Détecte : %s à %s blocs"),
        "message.brasshaven.machine.detector.players": ("players", "joueurs"),
        "message.brasshaven.machine.detector.monsters": ("monsters", "monstres"),
        "message.brasshaven.machine.detector.animals": ("animals", "animaux"),
        "message.brasshaven.machine.detector.items": ("items", "objets"),
        "message.brasshaven.machine.detector.living": ("all creatures", "toutes les créatures"),
    }
    for k, (e, f) in msgs.items():
        en[k], fr[k] = e, f
    g_en, g_fr = gui_lang()
    en.update(g_en)
    fr.update(g_fr)
    return en, fr


def java():
    L = [
        "package com.brasshaven.generated;",
        "",
        "import com.brasshaven.block.MachineBlock;",
        "import com.brasshaven.item.TooltipBlockItem;",
        "import com.brasshaven.registry.ModBlocks;",
        "import com.brasshaven.registry.ModItems;",
        "import net.minecraft.world.item.Item;",
        "import net.minecraft.world.level.block.Block;",
        "import net.minecraft.world.level.block.SoundType;",
        "import net.minecraft.world.level.block.state.BlockBehaviour;",
        "import net.minecraft.world.level.material.MapColor;",
        "import net.minecraftforge.registries.RegistryObject;",
        "",
        "import java.util.ArrayList;",
        "import java.util.List;",
        "",
        "/** GENERATED by tools/gen_java.py from tools/wf/machines.py — do not edit by hand. */",
        "public final class GeneratedMachines {",
        "    public static final List<RegistryObject<Block>> ALL = new ArrayList<>();",
        "",
    ]
    for mid, m in MACHINES.items():
        L.append(f'    public static final RegistryObject<Block> {mid.upper()} = machine("{mid}", MachineBlock.Kind.{m["kind"]}, '
                 f'MapColor.{m["color"]});')
    L += [
        "",
        "    private GeneratedMachines() {}",
        "",
        "    /** Forces class initialisation so every block/item is queued on the deferred registers. */",
        "    public static void init() {}",
        "",
        "    public static Block[] blocks() {",
        "        return ALL.stream().map(RegistryObject::get).toArray(Block[]::new);",
        "    }",
        "",
        "    private static RegistryObject<Block> machine(String name, MachineBlock.Kind kind, MapColor color) {",
        "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> new MachineBlock(BlockBehaviour.Properties.of()",
        "                .mapColor(color).strength(3.0F, 6.0F).sound(SoundType.METAL).requiresCorrectToolForDrops()",
        "                .setId(ModBlocks.BLOCKS.key(name)), kind));",
        "        ModItems.ALL.add(ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),",
        "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
        "        ALL.add(block);",
        "        return block;",
        "    }",
        "}",
        "",
    ]
    return "\n".join(L)

# Brasshaven — performances (serveur public, génération du monde)

Objectif : sur un serveur multijoueur public où beaucoup de joueurs explorent, le mod doit coûter le moins possible
par rapport à Minecraft sans mod — surtout pendant la génération des chunks. Ce document dit ce qui est mesuré
(par la CI, puisque le jeu ne tourne qu'avec Java 25), ce qui a été optimisé, et comment régler un serveur.

Voir aussi [SERVER_ADMIN.md](SERVER_ADMIN.md) (installation, options du mod) et [SERVER_AUDIT.md](SERVER_AUDIT.md)
(audit de sécurité et des chemins chauds du serveur).

## 1. Ce que la CI mesure

Les résumés sont publiés à chaque push sur la pré-release `previews-<branche>` (fichiers `brasshaven-ci-*.txt`) ;
les enregistrements Java Flight Recorder (`.jfr`) sont des artefacts GitHub Actions (`jfr-world`, `jfr-smoke`).

### Le mod complet face à Minecraft sans le mod (`world-test`, `brasshaven-ci-world.txt`)

Le même serveur Forge 26.2 démarre deux fois sur la même graine, dans un monde neuf : **avec** le jar Brasshaven
(tout par défaut : biomes, retouches du relief, ~49 structures, villages vanilla avec nos pièces, minerais,
créatures) puis **sans** le jar (Forge seul = Minecraft vanilla). Les mêmes zones neuves sont générées des deux
côtés avec la commande vanilla `/forceload add` (Forge sans le mod n'a pas `/brasshaven genbench`) : une zone
d'échauffement de 8 × 8 chunks, puis 4 zones de 16 × 16 chunks (1024 chunks). Mesuré de l'extérieur
(`tools/ci_perf.py`, sans rien demander au mod) :

| Mesure | Comment |
|---|---|
| démarrage | du lancement du processus au `Done`, et le `Done (…s)` affiché par le serveur |
| génération, temps réel | ms par chunk (le thread serveur attend chaque chunk, les workers le génèrent) |
| génération, CPU | ms de CPU par chunk, par groupe de threads (`/proc`) : thread serveur (= temps de tick qu'un joueur ressent pendant que des chunks se génèrent), workers de génération (bruit, structures, décorations), IO, JIT, et le GC détaillé (pauses, marquage concurrent, raffinement, thread VM) |
| mémoire | tas utilisé juste après un GC complet (`jcmd GC.run` + `GC.heap_info`) au repos après le démarrage, puis avec les 1088 chunks chargés ; RSS du processus ; **classes qui pèsent plus** dans le tas du mod que dans celui de vanilla (`jcmd GC.class_histogram`, au repos et chargé) |
| MSPT | `/tick sprint 600` avec les zones chargées, après 200 ticks pour laisser s'écouler les ticks ponctuels des chunks neufs (fluides) |
| entités | recensement des entités chargées par type (`/execute if entity`), mod et vanilla, et l'identité d'un échantillon des objets tombés au sol |

Un troisième serveur tourne avec le mod mais **sans les biomes ni les retouches du relief Brasshaven** (même
recensement, même MSPT) : ce qui reste de l'écart face à vanilla vient des structures, des décorations et des
créatures, le reste des biomes (végétation, eau, animaux). Il enregistre aussi son **démarrage** sous JFR (ce que
coûte le chargement du mod avant que l'horloge `Done (…)` du serveur ne démarre).

Le tableau donne les deux colonnes et leur rapport (`RATIO full mod / vanilla`). Il n'est pas bloquant : le mod
ajoute du contenu, il coûte forcément un peu. Ce qui est bloquant (déjà avant) : la paire **avec / sans biomes
Brasshaven** (même jar, `world.customBiomes` et `world.terrain.*` on/off) doit rester sous 1,05.

### Profils Java Flight Recorder (`brasshaven-ci-profile.txt`)

* **Génération** (`world-test`) : après les mesures (pour ne pas les fausser), chaque serveur (mod et vanilla)
  génère deux zones neuves de plus et fait 200 ticks sous JFR (`settings=profile`, piles de 256 appels).
* **Monde chargé seul** (`world-test`) : 600 ticks avec les 1088 chunks chargés, sans génération, sous JFR (le profil
  de génération mélangeait les deux).
* **Base chargée** (`smoke-test`) : la base de test de MSPT (96 machines sur un champ de blé, 60 automates qui se
  battent) refait un `/tick sprint 3000` sous JFR, après le sprint mesuré (600 ticks ne donnaient que 105
  échantillons, trop peu pour conclure).

`tools/jfr_report.py` résume chaque enregistrement : échantillons par groupe de threads, méthodes les plus chaudes
(temps propre et temps total), par paquet, le thread serveur seul, puis **la part de `com.brasshaven`** (méthodes du
mod en temps propre, en temps total, et « attribué à la méthode du mod la plus proche » = ce que le code du mod coûte,
code Minecraft appelé compris), les allocations (par classe, par site, part du mod) et les pauses du GC. Les deux
profils de génération côte à côte montrent ce que le mod ajoute. Il donne aussi les **piles d'appels** les plus
lourdes : du thread serveur, de chaque grand site d'allocation (qui appelle `DirectMethodHandle.allocateInstance`,
`DensityFunctions$Mapped.create`…) et des chemins qui passent par le code du mod. Les piles d'allocation sont lues sur
toute leur profondeur (256 appels) : à 64, la génération du monde coupait les méthodes du mod.

Sur sa machine : `python3 tools/jfr_report.py brasshaven-ci-gen-mod.jfr` (il faut le `jfr` d'un JDK), ou ouvrir le
fichier dans JDK Mission Control.

### Ce qui existait déjà

* `smoke-test` : MSPT de la base chargée (bloquant au-delà de 25 ms par tick), `brasshaven-ci-smoke.txt`.
* `world-test` : ms/chunk avec / sans les biomes Brasshaven (`/brasshaven genbench area`), coût d'un
  `getBaseHeight` et d'un échantillon de climat (`/brasshaven genbench noise`).
* `fit-test` : statistiques de placement des structures (`/brasshaven fitcheck`).

Tous les serveurs de test tournent maintenant avec les options JVM du pack serveur (`serverpack/jvm_args.txt`, sauf
la taille du tas, le pré-remplissage et `PerfDisableSharedMem`) : le jeu est testé avec ce qu'on livre.

## 2. Ce qui a été optimisé

### Génération du monde

**Vérification du terrain des structures** (`world/SiteFit`, appelée par `FittedJigsawStructure` pour chaque case
de la grille de chaque structure). C'est le seul calcul lourd que le mod ajoute à la génération : il lit le relief
« avant » les chunks avec `ChunkGenerator.getBaseHeight`, et un seul `getBaseHeight` coûte ~2,5 ms (il construit un
morceau de bruit d'une colonne et évalue tout le routeur de densité à chaque coin de cellule, sur toute la hauteur).

* Chaque point demandait deux hauteurs (surface avec l'eau, puis sol) = deux colonnes de bruit. Maintenant une seule
  colonne (`getBaseColumn`) donne les deux, en lisant exactement les mêmes blocs du haut vers le bas : mêmes
  hauteurs, **moitié prix** pour le pré-test (5 points par décalage) et pour la vérification complète (jusqu'à 7 × 7
  points, 2 fois par case). Les modes « ciel » et « souterrain » ne demandent plus que la hauteur qu'ils lisent.
* La vérification complète échantillonne d'abord les coins, le centre et le milieu des bords, et **s'arrête dès que
  le rejet est certain** (trop d'eau, pas assez, dénivelé trop grand, relief trop haut sous une île volante, pas
  assez de roche au-dessus d'une structure enterrée). Ces conditions ne peuvent qu'empirer avec plus de points :
  la grille complète aurait rejeté aussi. Verdicts, positions des structures et `/locate` sont identiques ; seule
  la raison notée pour `/brasshaven fitcheck` peut citer un autre défaut (même catégorie). La plupart des cases sont
  rejetées : c'est là que le gain est le plus grand.
  Le dénivelé (pente la plus raide entre deux points voisins) fait aussi partie de ces conditions : chaque nouveau
  point vérifie les paires qu'il complète.

Déjà en place (vérifié) : décision mémorisée par case (le chunk qui génère la structure après `/locate` ne refait pas
le calcul), au plus 2 assemblages jigsaw par case, pré-test à 5 points avant tout assemblage ; gabarits découpés en
colonnes (`ChunkedPoolElement` : chaque chunk ne pose que ses colonnes, cache des gabarits borné à ~1 M de blocs) ;
`clear_of_structures` ne lit que les références du chunk décoré ; `curated_spread` sans allocation ; biomes et
retouches du relief mesurés à coût nul par la CI (rapport ≈ 1,0).

### Serveur

* **Carte : fichiers d'exploration** encodés et compressés sur le thread de la carte au lieu du thread serveur. À
  chaque sauvegarde du monde, tous les joueurs connectés étaient compressés dans le même tick (pic visible sur un
  serveur chargé) ; le thread serveur ne fait plus qu'une copie de tableaux.
* Déjà en place (audit précédent, voir SERVER_AUDIT.md §4) : machines décalées et ralenties au repos, plafond de
  machines par chunk, plafond de créatures du mod, recherches de structures des boussoles en cache et budgétées,
  carte avec budget de temps et d'octets par joueur, gestionnaires par joueur espacés (10 à 200 ticks), recherches
  d'entités en boîtes serrées.

* **Automates et créatures** : les tests de ligne de vue des buts de combat (drone à vapeur, araignée mécanique,
  rampeur des cryptes, banshee, diablotin de braise, gargouille) passent par le `Sensing` du mob, comme les buts
  vanilla : un seul lancer de rayon par cible et par tick, déjà fait par le but de ciblage, au lieu d'un de plus à
  chaque tick (même résultat : le cache est vidé au début de chaque tick de l'IA). Le golem de laiton ne compte plus
  toute la foule autour de lui à chaque tick pour savoir s'il frappe le sol : la recherche s'arrête au troisième
  ennemi trouvé (même décision).
* **Redstone sans fil** : chaque récepteur, toutes les 5 ticks, reconstruisait trois fois la clé de son canal,
  vérifiait chaque émetteur du canal puis les reparcourait. La clé est gardée par machine et une seule passe fait le
  tri et la réponse (mêmes réponses). Sur un serveur où beaucoup de bases partagent les 16 canaux, le coût était
  récepteurs × émetteurs toutes les 5 ticks.

### JVM

* `-XX:+UseCompactObjectHeaders` ajouté au pack serveur (option produit de Java 25, JEP 519) : en-têtes d'objets de 8
  octets au lieu de 12. Minecraft garde des millions de petits objets : environ 10 à 20 % de tas en moins et moins
  de travail pour le GC. Si un autre mod pose problème avec, retire la ligne.

## 3. Réglages conseillés pour un serveur public

### Pré-générer le monde (le plus important)

Générer un chunk coûte des dizaines de millisecondes de CPU (Minecraft seul ; voir `brasshaven-ci-world.txt` pour le
surcoût du mod). Quand dix joueurs partent chacun dans une direction, la génération occupe tous les cœurs et le
serveur rame. **Pré-générer** fait ce travail une fois, avant l'ouverture, sans joueurs :

```text
/chunky radius 6000
/chunky start
```

(mod **Chunky**, voir §4 ; 6000 blocs de rayon ≈ 560 000 chunks, quelques heures selon la machine). Les structures
Brasshaven et leur vérification de terrain se font pendant cette génération. Ensuite, une **bordure du monde**
(`/worldborder set 12000`) garde les joueurs dans la zone déjà générée.

### `server.properties`

| Option | Conseil |
|---|---|
| `view-distance` | 8 à 10 (chaque cran de plus = beaucoup plus de chunks à générer, envoyer et garder) |
| `simulation-distance` | 6 à 8 (c'est ce qui pèse le plus sur le tick) |
| `sync-chunk-writes` | `false` sur SSD |
| `entity-broadcast-range-percentage` | 75 à 100 |
| `max-tick-time` | défaut (60000) |

### Options JVM (Java 25)

Le pack serveur les met dans `jvm_args.txt` (lu par `start.sh` / `start.bat`) : G1 réglé pour Minecraft (options dites
« d'Aikar »), `-Xms` = `-Xmx`, `-XX:+AlwaysPreTouch`, et `-XX:+UseCompactObjectHeaders`. La CI vérifie qu'elles sont
acceptées par Java 25 et fait tourner tous ses serveurs de test avec.

* **Mémoire** : 6 Go jusqu'à 10 joueurs, 8 Go jusqu'à 30, 10 à 12 Go au-delà. Plus n'est pas mieux : un tas énorme
  allonge les pauses.
* **G1 ou ZGC** : G1 (défaut du pack) est le bon choix jusqu'à ~12 Go. Avec 16 Go ou plus et des cœurs libres, le ZGC
  de Java 25 (toujours générationnel depuis Java 23 ; l'option `-XX:+ZGenerational` n'existe plus) fait des pauses
  de moins d'une milliseconde, contre un peu plus de CPU et de mémoire : remplace toute la partie G1 par
  `-XX:+UseZGC -XX:+AlwaysPreTouch -XX:+DisableExplicitGC`. La CI ne teste pas ZGC (ni ZGC avec les en-têtes
  compacts).
* `-XX:G1RSetUpdatingPauseTimePercent` (souvent copié d'anciens guides) ne sert plus au G1 des Java récents : le
  pack ne l'utilise pas.

### Diagnostiquer

**spark** (voir §4) : `/spark profiler start --timeout 120` pendant un ralentissement, puis le lien donné ; `/spark
tps` et `/spark health`. Le profil montre la méthode, l'entité ou le chunk qui coûte. Côté mod :
`compass.searchesPerMinute`, `machines.maxPerChunk`, `spawns.maxLoadedPerType` (voir SERVER_ADMIN.md).

## 4. Mods compagnons pour Forge 26.2

Vérifié le 5 octobre 2026 sur les listes publiques (CurseForge, Modrinth) ; revérifie avec le filtre « Forge » +
« 26.2 » de CurseForge avant d'installer.

| Mod | Forge 26.2 | Rôle | Conseil |
|---|---|---|---|
| **spark** | oui (spark 1.10.173, fichier « Forge 26.2 ») | profileur (CPU, tick, mémoire) | **à installer** sur le serveur |
| **Chunky** (Forge/NeoForge) | oui (chunky-forge 1.5.x listé pour 26.2) | pré-génération | **à installer**, pré-générer avant l'ouverture |
| ModernFix | non : la branche Forge s'arrête à 1.20.1 ; 26.x = NeoForge / Fabric | démarrage, mémoire, correctifs | pas disponible pour Forge 26.2 |
| FerriteCore | non : Forge s'arrête à 1.20.1 ; 26.2 = NeoForge / Fabric | mémoire des états de blocs | pas disponible pour Forge 26.2 |
| Sodium, Lithium, C2ME, ImmediatelyFast | non (Fabric / NeoForge) | rendu, tick, génération | pas pour Forge |
| Embeddium (portage Forge de Sodium) | non : dernière version pour 1.21.1, projet arrêté | rendu client | pas pour 26.x |

En résumé : sur Forge 26.2, **spark + Chunky** côté serveur ; côté client, pas d'équivalent de Sodium aujourd'hui —
baisser la distance de rendu et les particules reste le levier principal. Le gain mémoire de FerriteCore est en
partie couvert par `-XX:+UseCompactObjectHeaders`.

## 5. Ce que la CI a montré et la suite

### Run 37388245497

Le mod complet face à Forge sans le mod, sur les mêmes 1024 chunks neufs :

| | mod | vanilla | rapport |
|---|---|---|---|
| génération, temps réel | 54,8 ms/chunk | 51,2 ms/chunk | 1,07 |
| génération, CPU total | 152,8 ms/chunk | 142,2 ms/chunk | 1,08 |
| CPU du GC et de la VM | 15,6 ms/chunk | 9,4 ms/chunk | 1,66 |
| CPU du thread serveur | 5,1 ms/chunk | 5,3 ms/chunk | 0,97 |
| MSPT, 1088 chunks forcés, aucun joueur | 28,2 ms | 21,8 ms | 1,29 |
| tas après GC au repos | 138 Mo | 119 Mo | 1,16 |
| démarrage (`Done`) | 4,98 s | 4,97 s | 1,00 |

* Le code du mod ne pèse que **2 %** des échantillons CPU de la génération (vérification de terrain des structures :
  `FittedJigsawStructure` 1,8 %, dont `SiteFit.sample` 1,2 %). Le surcoût vient surtout de ce que le mod fait faire
  à Minecraft : plus d'objets alloués (d'où le GC à 1,66×), plus de structures et de décorations à poser.
* Le profil de la base chargée était trop court (105 échantillons). Ce qu'il montrait sous `BrassGolem.tick()`
  (34 %), c'est surtout du code vanilla appelé par `super.tick()` (déplacement : `Entity.move` → collisions de blocs →
  fusion de formes, et recherche de chemin) : le golem n'ajoute rien dans `tick()`, il n'est que le cadre du mod le
  plus proche dans la pile. Un golem de fer (même taille) coûte pareil. Les buts de combat du golem et du drone, eux,
  ont été allégés (§2).
* Le MSPT avec chunks forcés était mesuré tout de suite après la génération (ticks ponctuels des fluides) et sans
  savoir quelles entités étaient chargées : la CI recense maintenant les entités par type et profile le monde chargé
  seul.

### Run 37401499009 (version 0.9.1-beta)

| | mod | vanilla | rapport |
|---|---|---|---|
| génération, temps réel | 43,4 ms/chunk | 40,9 ms/chunk | 1,06 |
| génération, CPU total | 120,8 ms/chunk | 109,8 ms/chunk | 1,10 |
| CPU du GC et de la VM | 13,0 ms/chunk | 7,8 ms/chunk | 1,67 |
| CPU du JIT | 13,2 ms/chunk | 10,9 ms/chunk | 1,21 |
| MSPT, après 200 ticks de décantation, 1088 chunks | 4,68 ms | 3,92 ms | 1,19 |
| tas après GC au repos / chargé | 138 / 567 Mo | 119 / 527 Mo | 1,16 / 1,08 |

* Les 29 % de MSPT du run précédent étaient surtout l'écoulement des fluides des chunks neufs : il reste **+0,76 ms
  par tick** pour 1088 chunks chargés sans joueur.
* Dans ce monde chargé, le code du mod ne tourne **jamais** (0 échantillon sous `com.brasshaven`). L'écart vient du
  contenu : chez le mod, `ItemEntity.tick()` (des objets posés au sol qui tombent et glissent) fait **29,5 %** du
  thread serveur, contre presque rien chez vanilla (qui a pourtant 194 objets au sol dans les mêmes zones). Le
  prochain run dira lesquels (échantillon d'identifiants) et si les biomes en sont la cause (troisième serveur).
* Génération : le code du mod fait 2,0 % des échantillons (vérification de terrain des structures), les allocations
  sont à +10 % (31,1 contre 28,4 Go) et les collections du GC en même nombre ; l'écart de CPU du GC vient donc
  surtout du tas vivant plus gros (marquage concurrent), ce que le détail par thread du GC confirmera.
* `ChunkedPoolElement.place` (pose des gabarits, processeur `aging` compris) : 0,2 % des échantillons — rien à gagner
  là pour l'instant.
* Le recensement des entités affichait 0 : 26.2 répond `Test passed. Count: 475` (et non plus `count:`) ; corrigé.

Corrigé dans ce passage : la vérification de terrain s'arrête aussi au premier dénivelé trop raide (même verdict,
vérifié sur 200 000 grilles aléatoires), et les récepteurs sans fil vérifient leur canal en une seule passe (§2).

### Contenu : à décider (non changé, effet visible possible)

* **172 supports d'armure décoratifs** (114 dans la forteresse de basalte du Nether, 36 dans la citadelle engloutie) :
  ce sont des entités vivantes qui calculent leur chute et leurs collisions à chaque tick. Avec `NoGravity:1b` dans le
  gabarit, ils ne calculent plus rien (vanilla saute leur physique) ; la seule différence visible : un support resterait
  en l'air si un joueur casse le sol dessous. Gain : leur part du tick là où ces structures sont chargées.
* **146 villageois** dans les gabarits (70 dans nos pièces de village, 24 dans l'avant-poste de la guilde, les autres
  dans les observatoires, bibliothèques, cités…) : ce sont des marchands voulus (métiers fixés, persistants). Un
  villageois est l'entité vanilla la plus chère (cerveau, recherche de points d'intérêt). À garder sauf si le jeu peut
  s'en passer dans certaines structures.
* Les objets au sol (ci-dessus) : selon ce que montrera l'échantillon (pousses et bâtons = feuilles qui se décomposent
  là où un gabarit a coupé un arbre voisin ; graines et fleurs = eau qui coule sur l'herbe ; blocs = sable/gravier qui
  tombe), la correction se fera dans les générateurs de `tools/`.

### À lire dans le prochain `brasshaven-ci-profile.txt`

1. **Monde chargé** : recensement mod / vanilla / mod sans biomes et identité des objets au sol.
2. **Tas** : les classes qui pèsent plus chez le mod (au repos : registres, données ; chargé : entités, blocs à entités).
3. **Démarrage** : le profil JFR du démarrage avec le mod (chargement des classes, des données, des registres).
4. **GC** : quel thread du GC fait l'écart (pauses = allocation, marquage concurrent = tas vivant).
5. Si les **décalages de site** pèsent (chaque décalage refait la projection jigsaw = 1 colonne de bruit, même quand le
   biome ne convient pas) : tester le biome avant la projection n'est pas strictement équivalent (biomes 3D) — à
   décider avec mesure à l'appui.
6. Client (non mesuré) : FPS avec minimap + HUD actifs ou non dans une scène chargée.

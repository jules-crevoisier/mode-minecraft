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
| génération, CPU | ms de CPU par chunk, par groupe de threads (`/proc`) : thread serveur (= temps de tick qu'un joueur ressent pendant que des chunks se génèrent), workers de génération (bruit, structures, décorations), IO, GC, JIT |
| mémoire | tas utilisé juste après un GC complet (`jcmd GC.run` + `GC.heap_info`) au repos après le démarrage, puis avec les 1088 chunks chargés ; RSS du processus |
| MSPT | `/tick sprint 200` avec les zones chargées |

Le tableau donne les deux colonnes et leur rapport (`RATIO full mod / vanilla`). Il n'est pas bloquant : le mod
ajoute du contenu, il coûte forcément un peu. Ce qui est bloquant (déjà avant) : la paire **avec / sans biomes
Brasshaven** (même jar, `world.customBiomes` et `world.terrain.*` on/off) doit rester sous 1,05.

### Profils Java Flight Recorder (`brasshaven-ci-profile.txt`)

* **Génération** (`world-test`) : après les mesures (pour ne pas les fausser), chaque serveur (mod et vanilla)
  génère deux zones neuves de plus et fait 200 ticks sous JFR (`settings=profile`, piles de 256 appels).
* **Base chargée** (`smoke-test`) : la base de test de MSPT (96 machines sur un champ de blé, 60 automates qui se
  battent) refait un `/tick sprint 600` sous JFR, après le sprint mesuré.

`tools/jfr_report.py` résume chaque enregistrement : échantillons par groupe de threads, méthodes les plus chaudes
(temps propre et temps total), par paquet, le thread serveur seul, puis **la part de `com.brasshaven`** (méthodes du
mod en temps propre, en temps total, et « attribué à la méthode du mod la plus proche » = ce que le code du mod coûte,
code Minecraft appelé compris), les allocations (par classe, par site, part du mod) et les pauses du GC. Les deux
profils de génération côte à côte montrent ce que le mod ajoute.

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

## 5. Phase 2 (une fois les profils de la CI disponibles)

À lire dans `brasshaven-ci-profile.txt` :

1. **Profil de génération, mod vs vanilla** : la part des échantillons sous `com.brasshaven` sur les workers
   (attendu : `SiteFit` / `FittedJigsawStructure`, `ChunkedPoolElement.place`, nos décorations océaniques), et les
   paquets Minecraft dont la part grimpe par rapport au profil vanilla (par ex. `levelgen.structure.templatesystem`
   = pose des gabarits et processeurs, `levelgen.feature` = minerais ajoutés).
2. Si les **décalages de site** pèsent (chaque décalage refait la projection jigsaw = 1 colonne de bruit, même quand le
   biome ne convient pas) : tester le biome avant la projection n'est pas strictement équivalent (biomes 3D) — à
   décider avec mesure à l'appui.
3. **Processeur `aging`** (89 règles appliquées à chaque bloc de 20 gabarits, air compris) : si
   `RuleProcessor.processBlock` ressort, découper la liste par bloc d'entrée dans le générateur (`tools/`) en gardant
   le même ordre de tirage.
4. **Thread serveur pendant la génération** (ligne « CPU, server thread » du tableau) : chargement des entités et blocs
   à entités des structures (PNJ, coffres), éclairage.
5. **Profil de la base chargée** : méthodes du mod en tête du thread serveur (IA des automates, machines).
6. Mémoire : écart de tas après GC mod / vanilla au repos (registres, gabarits en cache, modèles) et avec 1088 chunks.
7. Client (non mesuré) : FPS avec minimap + HUD actifs ou non dans une scène chargée.

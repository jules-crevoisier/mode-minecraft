# Brasshaven — guide de l'administrateur de serveur

Ce guide explique comment installer et régler un serveur public (beaucoup de joueurs) avec Brasshaven :
Java, mémoire, distances, options anti-grief et anti-abus du mod, sauvegardes et mises à jour.
Le détail technique de l'audit (failles trouvées et corrigées) est dans [SERVER_AUDIT.md](SERVER_AUDIT.md).

| Cible | Version |
|---|---|
| Minecraft | 26.2 |
| Forge | 65.1.0 |
| Java | 25 (obligatoire) |

## 1. Installation

1. Installe **Java 25** (Temurin conseillé : `java -version` doit afficher `25`).
2. Télécharge l'installeur Forge 26.2-65.1.0 et lance `java -jar forge-26.2-65.1.0-installer.jar --installServer`.
3. Dépose `brasshaven-1.0.0.jar` dans `mods/`.
4. Lance une première fois, accepte l'EULA (`eula.txt` → `eula=true`), puis arrête le serveur : les fichiers de
   configuration sont créés.
5. **Chaque joueur doit avoir exactement le même `.jar`** que le serveur : la version du protocole réseau du mod
   doit être identique, sinon la connexion est refusée.

Les structures du mod n'apparaissent que dans les chunks **jamais générés** : pour un nouveau serveur, crée un
nouveau monde.

## 2. Java 25 : mémoire et options

Mets les options dans `user_jvm_args.txt` (lu par `run.sh` / `run.bat`).

| Joueurs en même temps | Mémoire (`-Xms` = `-Xmx`) |
|---|---|
| jusqu'à 10 | 6 Go |
| 10 à 30 | 8 Go |
| 30 à 60 | 10–12 Go |
| plus de 60 | 12–16 Go, et une machine avec de bons cœurs (le tick du serveur tourne sur un seul cœur) |

Ne donne pas plus de mémoire que nécessaire : un tas énorme rend les pauses du ramasse-miettes plus longues.

Options conseillées (G1, éprouvé pour Minecraft) :

```text
-Xms10G
-Xmx10G
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+DisableExplicitGC
-XX:+AlwaysPreTouch
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1HeapWastePercent=5
-XX:G1MixedGCCountTarget=4
-XX:InitiatingHeapOccupancyPercent=15
-XX:G1MixedGCLiveThresholdPercent=90
-XX:SurvivorRatio=32
-XX:+PerfDisableSharedMem
-XX:MaxTenuringThreshold=1
-XX:+UseCompactObjectHeaders
```

Ce sont les options du pack serveur (`jvm_args.txt`), avec lesquelles la CI fait tourner ses serveurs de test.
`-XX:+UseCompactObjectHeaders` (Java 25) réduit la mémoire prise par les objets de 10 à 20 %. Détails, mesures et
pré-génération : [PERFORMANCE.md](PERFORMANCE.md).

Avec 16 Go ou plus, remplace la partie G1 par le ZGC générationnel de Java 25, qui fait des pauses de moins
d'une milliseconde : `-XX:+UseZGC -XX:+AlwaysPreTouch -XX:+DisableExplicitGC` (garde `-Xms` = `-Xmx`).

## 3. `server.properties`

| Option | Conseil | Pourquoi |
|---|---|---|
| `view-distance` | 8 à 10 | Ce que les joueurs voient. Au-delà, chaque joueur coûte beaucoup plus cher (mémoire, réseau, génération). |
| `simulation-distance` | 6 à 8 | Zone où les entités, machines et cultures travaillent. C'est le réglage qui pèse le plus sur le tick. |
| `entity-broadcast-range-percentage` | 75 à 100 | Distance à laquelle les créatures sont envoyées aux joueurs. |
| `network-compression-threshold` | 256 | Valeur par défaut, bonne pour la plupart des serveurs. |
| `max-tick-time` | 60000 (défaut) | Laisse le watchdog relancer un serveur vraiment bloqué. |
| `sync-chunk-writes` | `false` sur un bon disque (SSD) | Écritures de chunks moins bloquantes. |
| `spawn-protection` | 16 ou plus | Le mod respecte la protection du spawn (baguette, casseur et poseur de blocs, récolte, bâton de tempête…). |
| `allow-flight` | `true` | Le planeur et le grappin du mod donnent des mouvements que l'anti-triche vanilla peut prendre pour du vol. |
| `enforce-secure-profile` / `online-mode` | `true` | Comptes vérifiés. |

**Pré-générer le monde** (avec un mod comme Chunky) dans un rayon de 5 000 à 10 000 blocs avant l'ouverture évite
les gros ralentissements quand plusieurs joueurs explorent en même temps. Le placement des structures Brasshaven
(vérification du terrain) se fait pendant cette génération.

## 4. Options du mod pour un serveur public

Fichier : `config/brasshaven-common.toml` (un seul fichier pour tout le serveur). Les valeurs par défaut des options
ci-dessous sont **déjà celles d'un serveur public** ; un petit groupe d'amis peut les assouplir. Forge relit le
fichier quand il change ; en cas de doute, redémarre le serveur.

### Pierres de voyage

| Option | Défaut | Effet |
|---|---|---|
| `waystones.crossDimension` | `true` | Voyager vers une pierre d'une autre dimension (Nether, End). `false` : seulement dans la même dimension. |
| `waystones.cooldownSeconds` | `5` | Attente entre deux voyages (chaque voyage charge les chunks à l'arrivée). Les opérateurs n'attendent pas. |
| `waystones.costLevels` | `0` | Niveaux d'expérience par voyage (le double vers une autre dimension). |
| `waystones.maxTotal` | `1000` | Nombre maximum de pierres connues du serveur (la liste est envoyée à tout le monde). |
| `waystones.renameOnlyHere` | `true` | On ne renomme / épingle que la pierre où l'on se trouve (les pierres sont communes à tout le serveur). |

### Machines

| Option | Défaut | Effet |
|---|---|---|
| `machines.breakerEnabled` | `true` | Le casseur de blocs fonctionne. |
| `machines.placerEnabled` | `true` | Le poseur de blocs fonctionne. |
| `machines.actAsOwner` | `true` | Le casseur et le poseur agissent au nom du joueur qui les a posés : protection du spawn et mods de protection de zones (claims) s'appliquent, et ils attendent quand ce joueur est hors ligne. Les machines posées avant la mise à jour n'ont pas de propriétaire et fonctionnent comme avant. |
| `machines.wirelessRange` | `128` | Portée de la redstone sans fil, en blocs (0 = toute la dimension). Empêche un émetteur d'actionner les récepteurs des autres bases. |
| `machines.maxPerChunk` | `32` | Nombre maximum de machines Brasshaven par chunk (0 = sans limite). |

### Objets, stockage, tombes

| Option | Défaut | Effet |
|---|---|---|
| `items.magnetRange` | `7.0` | Portée de l'anneau aimant (0 = désactivé). |
| `items.stormStaffRealLightning` | `false` | `false` : la foudre du bâton de tempête ne frappe que les monstres et n'allume aucun feu. `true` : vraie foudre (feu, joueurs, animaux). |
| `storage.quickStackRange` | `8` | Portée du bouton « ranger dans les coffres proches » (0 = bouton désactivé). |
| `storage.terminalRange` / `terminalHeight` / `relayRange` / `maxContainers` | `48` / `32` / `32` / `2048` | Taille d'un réseau de terminal de guilde. Baisse `maxContainers` si des bases énormes ralentissent. |
| `graves.ownerOnlyMinutes` | `-1` | Qui peut ouvrir une tombe : -1 = seulement son propriétaire (et les opérateurs), N = le propriétaire pendant N minutes puis tout le monde, 0 = tout le monde. |

### Quêtes

| Option | Défaut | Effet |
|---|---|---|
| `quests.shareProgress` | `true` | Une étape réussie par un joueur l'est pour tous les joueurs connectés (chacun reçoit une fois la récompense). |
| `quests.catchUpOnJoin` | `true` | À la connexion, un joueur reçoit les étapes déjà réussies par le serveur (avec les récompenses). **Sur un serveur public, mets `false`** : sinon un nouveau compte (ou un compte secondaire) récupère toutes les récompenses d'un coup. |

Ces deux options ne touchent que les quêtes (progrès). Les **contrats** des donneurs de quêtes sont toujours propres à
chaque joueur : la **boussole des structures** se gagne au contrat « Inspecter la tour de guet » de l'agent de la
Guilde, joueur par joueur, même pour un nouveau venu sur un vieux serveur. À sa première connexion, chaque joueur
reçoit le Manuel et l'Atlas et un repère privé vers l'avant-poste de la Guilde le plus proche. L'échelle complète :
[PROGRESSION.md](PROGRESSION.md). Boussole perdue : `/brasshaven contracts complete guild_survey <joueur>` ne marche
qu'une fois par joueur ; sinon `/give`.

### Créatures et boussoles

| Option | Défaut | Effet |
|---|---|---|
| `spawns.natural` | `true` | Apparition naturelle des créatures du mod (monstres, vie marine, serpent de mer). Les structures, autels et générateurs ne sont pas concernés. |
| `spawns.maxLoadedPerType` | `60` | Nombre maximum de créatures chargées d'une même espèce par dimension avant que leur apparition naturelle s'arrête. |
| `compass.searchesPerMinute` | `30` | Recherches de structure (boussole de structure, boussole d'aéronef) que tout le serveur peut lancer par minute. Les réponses sont mémorisées : réutiliser une boussole au même endroit ne coûte rien. |

### Difficulté et carte (inchangé)

`danger.*`, `elite.baseChance`, `bloodMoon.*` (voir le README), `map.sharedExploration` (tout le monde voit ce que
les autres ont exploré) et `map.showPlayers` (les joueurs se voient sur la carte : mets `false` sur un serveur PvP).

## 5. Ce que le mod fait déjà pour protéger le serveur

* Chaque action envoyée par un client est vérifiée par le serveur (joueur vivant et connecté, distance, menu
  ouvert, valeurs bornées) et limitée en fréquence : un client modifié ne peut pas inonder le serveur.
* Les machines ne chargent jamais de chunks ; le terminal de guilde ne lit que les chunks déjà chargés.
* La carte du monde est construite en arrière-plan avec un budget de temps par tick et un budget réseau par joueur.
* Les sacs à dos ne peuvent plus être imbriqués sans fin dans des boîtes de Shulker.

## 6. Sauvegardes

À sauvegarder : le dossier du monde (`world/`, qui contient aussi `world/data/brasshaven_map/` : carte partagée et
repères, et les données du mod : pierres de voyage, quêtes), le dossier `config/`, `server.properties`, et la liste
des mods.

Sauvegarde à chaud (sans arrêter le serveur), depuis la console ou un script RCON :

```text
save-off
save-all flush
# copier / compresser le dossier world/ (tar, rsync, restic, borg…)
save-on
```

* Fais une sauvegarde **automatique au moins une fois par jour** (toutes les heures sur un gros serveur) et garde
  plusieurs générations (par exemple 24 horaires, 7 quotidiennes, 4 hebdomadaires).
* Garde une copie **hors de la machine** du serveur.
* Teste une restauration de temps en temps sur un serveur de test.

## 7. Mettre à jour le mod

1. Annonce la mise à jour : tous les joueurs devront installer le nouveau `.jar`.
2. Arrête le serveur proprement (`stop`) et fais une **sauvegarde complète**.
3. Remplace l'ancien `brasshaven-*.jar` de `mods/` par le nouveau (ne garde jamais deux versions).
4. Démarre le serveur : les nouvelles options sont ajoutées automatiquement à `config/brasshaven-common.toml` avec
   leur valeur par défaut ; relis-les (section 4).
5. Vérifie `logs/latest.log` (aucune ligne `ERROR` liée à `brasshaven`), connecte-toi, teste une pierre de voyage,
   un terminal de guilde et la carte.
6. En cas de problème : arrête, remets l'ancien `.jar` et la sauvegarde.

Les nouvelles structures n'apparaissent que dans les chunks pas encore générés.

## 8. Diagnostiquer un ralentissement

* `/tick query` : temps moyen par tick (au-dessus de 50 ms le serveur prend du retard) et percentiles.
* `/debug start` puis `/debug stop` : rapport de profilage dans `debug/`.
* Un mod de profilage (spark) montre quelle entité, quel bloc ou quel chunk coûte cher.
* Leviers dans Brasshaven : `machines.maxPerChunk`, `spawns.maxLoadedPerType`, `storage.maxContainers`,
  `compass.searchesPerMinute` ; côté serveur, `simulation-distance` d'abord.

Le test automatique du dépôt (`tools/ci_smoke.py`) mesure à chaque modification le temps par tick avec 96 machines
et 60 automates : le résultat est dans `brasshaven-ci-smoke.txt` (publié avec les aperçus de chaque build).

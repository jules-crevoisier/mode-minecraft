# Wayfarers — mod d'exploration coop pour Minecraft 26.2 (Forge 65.1.0)

**Wayfarers** transforme une survie entre potes en grande expédition. On y trouve :

- **31 structures** construites à la main, réparties dans toutes les dimensions ;
- **une quête en 5 chapitres partagée par tout le serveur**, qui fait découvrir le monde étape par étape ;
- des **outils de confort** pour passer moins de temps à ranger et plus de temps à explorer : pierres de voyage, coffre de tri, terminal de guilde, tombes, sac à dos, aimant ;
- **8 armes à capacité**, **2 outils de zone**, **3 ensembles d'armure** ;
- **4 créatures** et **2 boss** ;
- **15 blocs de construction exclusifs** (briques de la Guilde, tuiles de toit, lampes runiques, briques de braise, briques du vide…), utilisés dans les structures et fabricables ;
- **une vraie difficulté** : plus on s'éloigne du spawn, plus les monstres sont forts, avec des monstres d'élite et des lunes de sang.

| Cible | Version |
|---|---|
| Minecraft | **26.2** |
| Forge | **65.1.0** (MDK `forge-26.2-65.1.0-mdk.zip`) |
| Java | **25** |

---

## Installation (CurseForge)

1. Dans CurseForge, crée un profil **Minecraft 26.2** avec **Forge 65.1.0**.
2. Compile le mod (voir plus bas) ou récupère le fichier `wayfarers-1.0.0.jar`.
3. Ouvre le dossier du profil (`…` → *Open Folder*) et dépose `wayfarers-1.0.0.jar` dans `mods/`.
4. Le mod est autonome : aucune autre bibliothèque n'est nécessaire.

**En multijoueur**, le même `.jar` doit être installé **sur le serveur et chez chaque joueur**.

**Les structures n'apparaissent que dans les régions jamais générées.** Le plus simple est de créer un nouveau monde.

## Compiler le `.jar`

```bash
./gradlew build          # nécessite un JDK 25 (Gradle peut le télécharger tout seul)
# → build/libs/wayfarers-1.0.0.jar
./gradlew runClient      # lancer le jeu en développement
./gradlew runServer      # serveur de test
```

---

## Le contenu

### Les structures (31)

Ce sont des constructions monumentales : 50 à 100 blocs de large, avec des tours qui montent jusqu'à 70 blocs et des intérieurs meublés. Les aperçus isométriques de chaque structure sont dans [`docs/structures/`](docs/structures).

| | | |
|---|---|---|
| ![Forteresse de basalte](docs/structures/basalt_fortress.png) | ![Monastère des cimes](docs/structures/mountain_monastery.png) | ![Île céleste](docs/structures/sky_island.png) |
| Forteresse de basalte | Monastère des cimes | Île céleste |
| ![Avant-poste de la Guilde](docs/structures/guild_outpost.png) | ![Sanctuaire piglin](docs/structures/piglin_sanctuary.png) | ![Arbre-monde](docs/structures/giant_tree.png) |
| Avant-poste de la Guilde | Sanctuaire piglin | Arbre-monde |

| Dimension | Structures |
|---|---|
| **Surface** | **Avant-poste de la Guilde** : 3 variantes, rempart, châtelet, grande salle, tour des cartes de 46 blocs, pierre de voyage. · **Tour de guet** : une version en ruine, dont le sommet s'est effondré, et une version intacte avec flèche ; cave secrète. · **Monastère des cimes** : église gothique à arcs-boutants, clocher de 46 blocs, cloître, bibliothèque, crypte secrète. · **Oasis du désert** : caravansérail à coupoles et minarets, bazar, colosse de pharaon à moitié enseveli, tombeau caché (archéologie). · **Temple englouti** : sanctuaire à coupole, obélisques, conduit actif, caveau secret. · **Huttes des sorcières** : maisons tordues sur pilotis, tour au toit en chapeau de sorcière, cercle rituel. · **Arbre-monde** : tronc creux de 15 blocs, 3 terrasses à cabanes, ponts de corde, nid de vigie. · **Île céleste** : temple de quartz à 40 blocs du sol, îlots reliés par des ponts, cascades, escalier en spirale. · **Bibliothèque oubliée** : nef gothique, tours jumelles, rotonde effondrée, cabinet secret. · **Mine naine** : chevalement de 20 blocs, village à flanc de colline, 4 galeries, salle forte scellée. · **Campement de bandits** : palissade, tours de guet, tente du chef. · **Phare côtier** : phare de 52 blocs sur un cap, quai, grotte marine. · **Ziggourat de la jungle** : 8 gradins, têtes de serpent à plumes, jeu de balle, tombeau secret. · **Observatoire polaire** : dôme de neige, télescope de cuivre, laboratoire en sous-sol. · **Cercle runique** : trilithes de 13 blocs, crypte sous l'autel. · **Épave de galion** : 3 ponts, château arrière, mât brisé au fond de l'eau. |
| **Souterrain** | **Forge naine** : salle de 63×31 blocs à piliers de lithite, statues de rois nains de 25 blocs, chutes de lave, chambre forte. · **Grotte de cristal** : géode géante avec gouffre, flèches de cristal, atelier de taille, ponts. · **Laboratoire scellé** : sas, salle de contrôle en dôme, 8 cellules de confinement, dont une brèche de sculk. |
| **Grande structure** | **Citadelle engloutie** : cathédrale gothique de prismarine au fond de l'océan. Elle comprend une tour de 76 blocs qui sort de l'eau, une nef et 6 salles à thème reliées par des tunnels de verre, une arène du boss sous un dôme de 40 blocs, et une salle du trésor scellée. Elle existe en 3 variantes. |
| **Nether** | **Forteresse de basalte** : citadelle noire de 89 blocs, douves de lave, tours de 48 blocs, pont-levis, donjon. · **Pont de chaînes** : tablier de 60 blocs suspendu à des maillons géants entre deux tours-portes. · **Sanctuaire piglin** : ziggourat surmontée d'une idole d'or de 34 blocs. · **Fonderie de lave** : usine sur pilotis, cheminées, creusets, grue. · **Tour des âmes** : tour de 72 blocs enlacée de contreforts d'os. · **Marché piglin** : bazar fortifié, auvents rayés, tour centrale, marchands piglins. |
| **End** (îles extérieures) | Observatoire du vide · Jardin flottant de chorus · Archive de l'End · Épave du vide · Nid du Gardien du vide |

Chaque structure a :
- ses propres tables de butin ;
- un générateur de monstres ou une rencontre ;
- souvent un secret.

Plusieurs structures contiennent une **pierre de voyage**.

### La quête : l'Atlas du Voyageur (5 chapitres, 59 étapes)

La quête est un onglet de progrès (touche **L**). Clic droit avec l'**Atlas** pour voir le résumé de la guilde.

1. **Premiers pas** : trouver un avant-poste de la Guilde, récupérer des fragments de carte, fabriquer pierre de voyage, coffre de tri, sac et lame.
2. **Explorateur de la Surface** : découvrir chaque structure de la Surface.
3. **Les profondeurs** : trouver la lithite, les structures souterraines, la Citadelle, et **vaincre le Gardien englouti**.
4. **Le Nether** : les 6 structures, les braises anciennes, l'armure de braise.
5. **L'End** : les éclats du vide, le **Gardien du vide**, et le défi final *Légende des Voyageurs* (toutes les structures).

**La progression est commune** : chaque étape franchie par un joueur est accordée à tout le monde, y compris aux joueurs hors ligne quand ils se reconnectent.

**Chaque palier d'équipement demande le matériau de sa dimension**, ce qui oblige à explorer dans l'ordre :

| Palier | Matériau | Dimension |
|---|---|---|
| 1 | Fragment de carte | Surface |
| 2 | Lithite | Sous terre (minerai sous y=8, ou butin) |
| 3 | Braise ancienne | Nether |
| 4 | Éclat du vide | End |

### Confort et coop

| Objet / bloc | Effet |
|---|---|
| **Pierre de voyage** | Clic droit : liste cliquable de toutes les pierres découvertes, dans toutes les dimensions. Une pierre découverte l'est **pour tout le monde**. |
| **Coffre de tri** | 54 emplacements. Il aspire les objets au sol dans un rayon de 6 blocs et se trie tout seul quand personne ne regarde dedans. |
| **Terminal de guilde** | Clic droit : range ton inventaire dans les coffres autour (10 blocs) qui contiennent déjà ces objets. Accroupi : trie tous les coffres. |
| **Tombe** | À la mort, tes objets sont rangés dans une tombe, et ses coordonnées s'affichent dans le chat. N'importe quel membre du groupe peut les récupérer. |
| **Sac du Voyageur** | 27 emplacements qui voyagent avec toi. |
| **Anneau aimanté** | Attire objets et expérience. Se bascule au clic droit ou avec la touche **M**. |
| **Boussole des structures** | Indique la structure la plus proche (distance + direction). Accroupi : choisir le type de structure. |
| **Parchemin de rappel** | Téléporte à la pierre de voyage la plus proche. |
| **Touche R** | Trie l'inventaire principal (la barre d'action n'est pas touchée). |

### Armes et outils

| Arme / outil | Capacité |
|---|---|
| Lame du Cartographe | Ruée vers l'avant. |
| Marteau tellurique | Onde de choc. |
| Lame de givre | Ralentit ; gèle au 3e coup. |
| Boomerang | Revient à son lanceur. |
| Bâton de l'aube | Repousse les monstres et soigne les alliés. |
| Faux de braise | Met le feu, et soigne dans le Nether. |
| Bâton des tempêtes | Appelle la foudre. |
| Lance du vide | Téléportation dans le dos de la cible. |
| Pioche d'excavation | Mine en 3x3. |
| Hache de bûcheron | Abat l'arbre entier. |

Pour la pioche et la hache, s'accroupir désactive l'effet de zone.

### Armures (bonus d'ensemble complet)

| Ensemble | Bonus |
|---|---|
| **Explorateur** | Vitesse, aucun dégât de chute sous 8 blocs, vision nocturne sous terre. |
| **Braise** | Immunité au feu, rapide dans la lave. |
| **Vide** | Chute lente ; le vide de l'End te ramène au lieu de te tuer. |

### Créatures et boss

| Créature | Où on la trouve | Particularité |
|---|---|---|
| Rôdeur des ruines | Ruines de la Surface | Ses coups affaiblissent. |
| Spectre des cartes | Bibliothèques | Aveugle et donne la nausée ; brûle au soleil. |
| Garde de basalte | Forteresses du Nether | — |
| Traqueur du vide | End | Se téléporte près de sa proie. |

**Les boss** :

- **Gardien englouti** (Citadelle) : 320 PV et 3 phases.
  1. Il appelle des noyés.
  2. Il frappe le sol d'une onde de marée.
  3. Enragé, il crée un tourbillon qui attire les joueurs.

  À sa mort, les barreaux scellés de la salle du trésor tombent.
- **Gardien du vide** (Nid de l'End) : il se téléporte, fait léviter les joueurs et invoque des traqueurs.

Les deux boss se réveillent en déposant une offrande sur leur autel :

| Boss | Offrande |
|---|---|
| Gardien englouti | Fragment de carte |
| Gardien du vide | Éclat du vide |

### Difficulté : le monde devient dangereux

Le **niveau de danger** dépend de l'endroit où un monstre apparaît. Il s'affiche dans la barre d'action quand il change.

| Source | Effet sur le niveau |
|---|---|
| Distance au spawn | +1 tous les 900 blocs |
| Nether | Les distances comptent ×8, et +2 |
| End | +3 |
| Sous y = 0 | +1 |
| Lune de sang | +2 |

- **Effet par niveau** : +15 % de vie et +12 % de dégâts pour chaque monstre. Le niveau est plafonné à 7, « Légendaire ».
- **Monstres d'élite** :
  - Leur nom est doré. Ils ont +100 % de vie, +50 % de dégâts, plus de vitesse et résistent au recul.
  - Leur chance d'apparition est de 3 % de base, plus 2 % par niveau de danger.
  - Ils lâchent le matériau de la dimension, des émeraudes, de l'expérience et parfois un parchemin de rappel.
- **Lune de sang** :
  - Elle arrive toutes les 7 nuits dans la Surface.
  - Le danger augmente et les élites sont 3 fois plus fréquents. Mieux vaut avoir une base solide.
- **Monstres dans les structures** : les grandes structures continuent de faire apparaître leurs gardiens dans le noir, comme les forteresses vanilla. Les générateurs fonctionnent même dans les pièces éclairées.
- **Boss** : leur vie augmente de 60 % par joueur supplémentaire présent dans un rayon de 48 blocs.

Tout se règle dans `config/wayfarers-common.toml` :

| Option | Défaut |
|---|---|
| `danger.enabled` | `true` |
| `danger.blocksPerLevel` | `900` |
| `danger.maxLevel` | `7` |
| `danger.healthPerLevel` | `0.15` |
| `danger.damagePerLevel` | `0.12` |
| `elite.baseChance` | `0.03` |
| `bloodMoon.enabled` | `true` |
| `bloodMoon.interval` | `7` |

### Blocs de construction exclusifs

Les structures sont bâties avec des blocs propres au mod, qu'on peut aussi utiliser pour construire sa base. Ils se trouvent dans l'onglet créatif, et chaque famille de briques a ses escaliers, dalles et murets.

| Thème | Blocs |
|---|---|
| Guilde (Surface) | Briques de la Guilde (normales, moussues, fissurées) · Pierre de la Guilde polie et gravée · Tuiles d'azur, de terre cuite et d'ardoise · Lampe runique |
| Profondeurs | Briques de lithite · Bloc de cristal de lithite (lumineux) |
| Nether | Briques de braise · Lampe de braise · Frise dorée |
| End | Briques du vide · Bloc de lumière stellaire |

---

## Commandes

| Commande | Qui | Effet |
|---|---|---|
| `/wayfarers atlas` · `waystones` · `warp <id>` · `sort` · `magnet` | tous | Utilisées par l'Atlas, les pierres de voyage et les touches. |
| `/wayfarers demo` | op | Donne tout le contenu du mod (idéal pour une vidéo). |
| `/wayfarers kit <starter\|explorer\|depths\|nether\|end>` | op | Kits par palier. |
| `/wayfarers locate <structure>` · `/wayfarers tp <structure>` | op | Trouver ou visiter une structure. |
| `/wayfarers progress reset\|complete` | op | Réinitialiser ou terminer la quête. |

L'onglet créatif **Wayfarers** contient tous les objets, blocs et œufs d'apparition.

---

## Pour les développeurs

Le contenu est généré par des scripts Python sans aucune dépendance, rangés dans `tools/` :

```bash
python3 tools/generate_all.py            # régénère tout puis valide
python3 tools/generate_all.py --preview  # + aperçus isométriques des structures dans build/previews/
```

| Script | Ce qu'il génère |
|---|---|
| `gen_structures.py` + `wf/structures/*.py` | Les plans des 31 structures (éditeur de blocs en Python) → modèles `.nbt`, pools, ensembles de structures, tags de biomes |
| `gen_loot.py`, `gen_quests.py`, `gen_data.py` | Butin, quêtes (progrès), recettes, tags, minerai |
| `gen_textures.py`, `gen_assets.py` | Textures pixel-art, modèles, traductions fr/en |
| `gen_java.py` | Le catalogue Java partagé (`GeneratedContent.java`) |
| `validate.py` | Vérifie tous les identifiants de blocs, objets, entités et biomes contre les données de 26.1. Il contrôle aussi chaque référence croisée : butin, quêtes, traductions, modèles et textures. |

Le code Java vit dans `src/main/java/com/wayfarers` :

| Paquet | Contenu |
|---|---|
| `registry` | Registres |
| `block` | Blocs |
| `item` | Objets |
| `entity` | Créatures |
| `event` | Coop, tombes, équipement |
| `command` | Commande `/wayfarers` |
| `client` | Rendu et touches |

### État de la vérification

**Ce qui a été vérifié :**
- Le code Java a été vérifié par `javac` contre les signatures exactes de l'API **Minecraft 26.2 + Forge 65.1** : **0 erreur**.
- Toutes les ressources passent `validate.py` : **0 erreur**.

**Ce qui n'a pas pu l'être :** l'environnement de développement n'avait pas accès aux dépôts Maven de Forge. Le `./gradlew build` officiel et une partie en jeu n'ont donc **pas encore été lancés**.

À tester au premier lancement :
- [ ] `./gradlew build` réussit et produit `build/libs/wayfarers-1.0.0.jar`.
- [ ] Le jeu démarre sans erreur de données (structures, butin, quêtes) dans `logs/latest.log`.
- [ ] `/wayfarers tp guild_outpost` puis `/wayfarers tp sunken_citadel` : les structures sont bien posées au sol ou au fond de l'eau.
- [ ] Une pierre de voyage : la liste cliquable s'affiche et la téléportation fonctionne.
- [ ] Une mort : une tombe apparaît et rend les objets.
- [ ] L'autel de la Citadelle : le boss apparaît et les barreaux tombent à sa mort.

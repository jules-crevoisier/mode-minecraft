# La progression : la route du voyageur

Un nouveau joueur ne reçoit plus tout d'un coup. À la première connexion il a **le Manuel et l'Atlas**, rien
d'autre ; la carte en haut à droite de l'écran (le suivi de quête) lui montre **toujours sa prochaine étape**, et
chaque outil puissant se gagne en route. La **boussole des structures**, en particulier, est la récompense d'un
contrat de l'agent de la Guilde.

Source unique de cette échelle : `tools/wf/progression.py` (le suivi, `/brasshaven atlas` et les tests la lisent ;
`tools/validate.py` vérifie que ce document nomme chaque étape).

## L'échelle

| # | Étape (id) | Objectif | Récompense / déblocage | Où c'est expliqué |
|---|---|---|---|---|
| 0 | Arrivée | — | **Manuel du Voyageur** + **Atlas du Voyageur**. L'avant-poste de la Guilde le plus proche est **marqué sur la carte** (repère privé doré) et sa distance, sa direction et ses coordonnées s'affichent dans le chat (s'il n'y en a pas à portée : le village le plus proche). | Message de bienvenue, page du Manuel « Bienvenue, Voyageur » et « La route du voyageur » |
| 1 | I. L'avant-poste de la Guilde (`first_steps/guild_outpost`) | Entrer dans un avant-poste de la Guilde **ou** parler à n'importe quel agent de la Guilde (Relais de la Guilde ou place d'un village). | 3 fragments de carte, 50 xp, 1 point de talent ; les contrats de l'agent | Suivi, journal (J), Manuel « La route du voyageur » ; l'Atlas (et `/brasshaven guide`) redonne la direction tant que l'étape n'est pas faite |
| 2 | Contrat « Des vivres pour la route » (`npc/guild_provisions`) | Apporter 12 pains à un agent de la Guilde. | 6 émeraudes, 2 fragments de carte, 30 xp | Écran de l'agent, suivi, onglet Contrats du journal |
| 3 | Contrat « Inspecter la tour de guet » (`npc/guild_survey`) | Accepter, puis entrer dans une tour de guet en ruine : **la plus proche est marquée sur la carte** à l'acceptation. Revenir voir un agent. | **Boussole des structures**, 3 fragments de carte, 5 émeraudes, 50 xp ; une carte d'astuce explique la boussole | Écran de l'agent, suivi, Manuel « Boussole des structures » |
| 4 | Morceaux de carte (`first_steps/map_fragment`) | Avoir un fragment de carte (déjà fait en général). | 20 xp | Journal |
| 5 | Voyager léger (`first_steps/backpack`) | Fabriquer un Sac du Voyageur. | 27 cases qui te suivent | Manuel « Sacs » |
| 6 | Plus jamais à pied (`first_steps/waystone`) | Fabriquer une pierre de voyage (perle de l'Ender, boussole, 2 fragments, briques). | 2 fragments ; ta propre pierre de voyage. Les **parchemins de rappel** se fabriquent dès lors (papier, fragment, perle) | Manuel « Pierres de voyage », « Parchemin de rappel » |
| 7 | Épées tirées, cartes tracées (`first_steps/blade`) | Forger la lame du Cartographe. | Ruée vers l'avant | Journal, Manuel |
| 8 | Paré pour la route (`first_steps/explorer_armor`) | Porter l'ensemble d'explorateur. | Bonus d'ensemble | Journal, Manuel |
| 9 | III. Dans les profondeurs (`depths/lithite`) | Trouver de la lithite (sous y = 0). | Équipement de lithite ; **d'autres boussoles des structures** se fabriquent (boussole + 3 fragments + 1 éclat de lithite) | Manuel « Boussole des structures », journal |
| 10 | La Citadelle engloutie (`depths/sunken_citadel`) | Trouver la citadelle (tour qui sort d'un océan profond). | 2 fragments, 80 xp ; le Gardien englouti | Journal |
| 11 | IV. Dans les flammes (`nether/enter`) | Entrer dans le Nether. | — | Journal |
| 12 | Braise ancienne (`nether/ancient_ember`) | Récupérer une braise ancienne. | Équipement de braise | Journal |
| 13 | V. Au-delà du vide (`end/enter`) | Atteindre l'End. | — | Journal |
| 14 | Éclats de néant (`end/void_shard`) | Récupérer un éclat du vide. | Équipement du vide | Journal |
| 15 | Cœur du vide (`end/void_warden`) | Vaincre le Gardien du vide. | Cœur du vide, 4 éclats | Journal |

Le suivi passe tout seul à l'étape suivante. Si le joueur épingle une autre quête (bouton **Suivre**), elle reste
affichée jusqu'à ce qu'elle soit faite, puis le suivi revient sur la route. **Ne plus suivre** vide le suivi jusqu'à
la prochaine connexion ; le réglage « suivi de quête » (Config du mod) le cache complètement. Une fois l'échelle
terminée, le suivi reprend l'ancien comportement : la quête suivante du même chapitre.

## Les objets de confort sur l'échelle

| Objet | Avant | Maintenant | Pourquoi |
|---|---|---|---|
| Manuel du Voyageur | donné à l'arrivée | **donné à l'arrivée** | Il explique tout ; perdu ? un livre et une plume |
| Atlas du Voyageur | donné à l'arrivée | **donné à l'arrivée** | C'est le journal de quêtes et la carte (J et M marchent sans lui) : il guide, il ne remplace pas l'exploration. Tant que l'étape 1 n'est pas faite, l'utiliser remet le repère de l'avant-poste |
| Boussole des structures | donnée à l'arrivée, et au premier avant-poste | **étape 3** (contrat de l'agent) ; fabrication à l'**étape 9** (lithite) ; aussi « Maître cartographe », « Seigneur des enfers » et, rarement, dans les coffres de structures | Elle trouve tout : c'est la récompense qui ouvre l'exploration, pas un point de départ |
| Pierre de voyage | — | les avant-postes et un village sur quatre en ont une ; à fabriquer à l'**étape 6** | Demande une perle de l'Ender et des fragments |
| Parchemins de rappel | — | fabrication après l'étape 6 (perle de l'Ender) ; contrats « Prime : les bandits » (agent) et « Un présent pour la Guilde » (druidesse) | Inutiles sans pierre de voyage |
| Anneau aimanté | — | fabrication avec 2 fragments (après l'étape 1) ; contrat « Cartes déchirées » (érudite), « Maître cartographe » | Confort, pas d'avantage d'exploration |
| Sac du Voyageur / de l'Explorateur | — | étape 5 / un lingot de laiton | Le grand sac demande le laiton |
| Boussole de dirigeable | — | cristal d'éther (Îles célestes) + laiton | Milieu de partie |
| Lettre pour les druides (contrat de l'agent) | donnait une boussole | 12 émeraudes, 4 fragments, 4 fioles d'expérience | La boussole est maintenant à l'étape 3 |

## Multijoueur

- Les **quêtes** (avancements) suivent `quests.shareProgress` et `quests.catchUpOnJoin`
  ([SERVER_ADMIN.md](SERVER_ADMIN.md)) : partagées par défaut, l'étape 1 réussie par un joueur l'est pour les autres.
- Les **contrats** sont **toujours personnels** : chaque joueur fait « Des vivres pour la route » puis « Inspecter
  la tour de guet » pour **sa** boussole. Un nouveau venu sur un vieux serveur (rattrapage ou non) la gagne donc
  lui-même ; le suivi lui montre ces contrats même si le groupe a fini les premiers chapitres.
- Chaque nouveau joueur reçoit à sa première connexion son propre repère vers l'avant-poste le plus proche **de
  l'endroit où il apparaît**. Les repères posés par le mod sont privés ; le joueur peut les modifier ou les supprimer.
- Recherches : le repère de bienvenue utilise la même recherche que la boussole (réponses mémorisées par zone) ;
  l'Atlas et `/brasshaven guide` consomment le budget `compass.searchesPerMinute`.

## Mondes existants

Aucun identifiant n'est retiré. Les joueurs déjà accueillis gardent ce qu'ils ont (boussole comprise) et ne
reçoivent rien de nouveau ; l'étape 1 déjà faite reste faite. Les nouveaux joueurs suivent la nouvelle échelle. Les
anciennes boussoles restent utilisables ; seule la recette change (il faut un éclat de lithite).

## Commandes (op)

| Commande | Effet |
|---|---|
| `/brasshaven guide` (tous) | Remet le repère et la direction de l'avant-poste de la Guilde le plus proche. |
| `/brasshaven contracts complete <contrat> [joueur]` | Rend un contrat pour le joueur, récompenses comprises (boussole perdue, test). |
| `/brasshaven contracts reset [joueur]` | Efface ses contrats. |
| `/brasshaven progression selftest` | Vérifie les règles de l'échelle sur le serveur (lancé par le test CI du serveur). |

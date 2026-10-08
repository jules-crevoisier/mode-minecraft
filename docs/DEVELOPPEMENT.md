# Développer Brasshaven : le process complet

Ce document décrit comment on travaille sur le mod, de l'idée à la release. Il est tenu à jour pendant la refonte
(octobre 2026) : chaque fois qu'un outil ou une étape change, cette page change avec.

En bref, une modification de structure se fait en cinq temps :

```bash
# 1. modifier le générateur Python      tools/wf/structures/<structure>.py (ou un helper de tools/wf/)
# 2. vérifier les chemins (≈ 10 s par structure)
python3 tools/audit_structures.py --only <structure> --cache build/audit/cache
# 3. régénérer les templates du jeu
python3 tools/gen_structures.py --only <structure>
# 4. compiler et regarder en jeu, avec captures
./gradlew build
python3 tools/ci_client.py --focus structure:<structure>
# 5. commit + push : le CI rejoue les tests rapides
```

---

## 1. Où vit quoi

| Quoi | Où |
|---|---|
| Code Java du mod (Forge 65.1.0, Minecraft 26.2, Java 25) | `src/main/java/com/brasshaven/` |
| Ressources générées (structures `.nbt`, worldgen, loot, recettes, textures, modèles…) | `src/main/resources/` — **ne pas éditer à la main**, elles sortent des scripts |
| Générateurs Python | `tools/gen_*.py`, `tools/generate_all.py` (tout régénérer puis valider) |
| Bibliothèque de construction | `tools/wf/` (`blueprint.py`, `arch.py`, `interior.py`, `dungeon.py`, `support.py`…) |
| Une structure = un module | `tools/wf/structures/*.py` (liste et réglages : `tools/wf/defs.py`) |
| Règles de style et de construction | `tools/STYLE.md` (matériaux), `tools/BUILDING.md` (échelle, composition, circulation) |
| Audit des structures | `tools/audit_structures.py`, dernier rapport dans `docs/audit/structures.txt` |
| Test en jeu (client réel, captures) | `tools/ci_client.py`, pilote en jeu `client/CiDriver.java` |
| Versions et publication | `gradle.properties`, `docs/PUBLISHING.md`, notes dans `docs/releases/` |

Une seule branche de travail : `ccr-127dc262-tsdn10` (c'est aussi la branche par défaut). Pas de pull request :
on commit et on pousse directement dessus, après avoir testé.

## 2. Les structures

### 2.1 Construire

Chaque structure est une fonction Python qui pose des blocs dans un `Blueprint` (coordonnées relatives, y = 0 au
niveau du sol). `tools/gen_structures.py` l'exécute, répare ce qui n'a qu'une seule bonne réponse
(`wf/support.py` : lanternes sans chaîne, plantes en l'air, portes à moitié…) puis écrit les templates `.nbt`
(découpés en colonnes quand c'est grand, `wf/chunking.py`) et les fichiers de worldgen.

Avant de construire ou de reprendre une structure, relire `tools/BUILDING.md` : hiérarchie des masses, rythme
des façades, échelle humaine, et surtout les règles de circulation **C1 à C17** (largeur des passages, hauteur
sous plafond, escaliers, paliers, échelles). Un bâtiment qui casse une règle **[CHECK]** n'est pas fini.

Contrainte technique pour les constructions géantes : le placement passe par un jigsaw (`brasshaven:fitted_jigsaw`),
donc l'emprise maximale est d'environ 250 × 250 blocs, et il faut garder de la marge sous la limite de hauteur
de l'Overworld (320).

### 2.2 Auditer : est-ce qu'un joueur peut vraiment tout parcourir ?

`tools/audit_structures.py` reconstruit chaque structure exactement comme le jeu la recevra, puis la parcourt
comme un joueur de 1,8 bloc qui marche, saute 1,25 bloc, monte les escaliers et les échelles, ouvre portes et
trappes, et tombe d'au plus 22 blocs. Il signale :

- les **pièces meublées où personne ne peut entrer** (tour sans porte, cave scellée, trappe couverte d'un tapis) ;
- les **endroits où l'on tombe sans pouvoir remonter** (`one-way`) ;
- les **passages bloqués** : trou d'un seul bloc de haut, marche de 1,5 ou 2 blocs sans escalier ;
- les **boss qu'on ne peut pas réveiller** (aucune place accessible dans le rayon du sceau) ;
- les **coffres et tonneaux inaccessibles** ou dont le couvercle est bloqué ;
- les **escaliers** qui cognent la tête, qui finissent dans un mur ou dans le vide, les **échelles** sans palier ;
- ce que `support.py` trouve encore (blocs flottants, lits coupés en deux…).

```bash
python3 tools/audit_structures.py                                   # tout (long : plusieurs minutes)
python3 tools/audit_structures.py --only giant_tree basalt_fortress  # seulement celles-là
python3 tools/audit_structures.py --only villages                    # les pièces de village
python3 tools/audit_structures.py --only giant_tree --cache build/audit/cache   # garde les plans construits
```

Le rapport lisible est écrit dans `build/audit/structures.txt` (et `.json`) : une ligne de résumé par pièce, puis
les problèmes du plus grave au moins grave. Chaque problème donne la position (coordonnées du plan Python) et
**la ligne du générateur qui a posé le bloc fautif** (`[nether.round_tower:204 < nether.basalt_fortress:718]`) :
on va droit au bon endroit du code.

Avec `--cache`, supprimer les fichiers `build/audit/cache/<structure>__*.pkl` des structures modifiées, sinon
l'audit relit l'ancienne version.

Objectif : **0 erreur** (`ERROR`) sur chaque structure. Les `WARN` se lisent au cas par cas (une poche de deux
blocs sous un escalier extérieur n'est pas un défaut de conception).

Pour comprendre un problème, un outil simple aide beaucoup : imprimer une tranche du plan en ASCII (une couche
`y`, ou une coupe verticale) à partir du cache `.pkl` : voir la section 6.

### 2.3 Régénérer

```bash
python3 tools/gen_structures.py --only <structure>             # templates + worldgen de cette structure
python3 tools/gen_structures.py --only <structure> --preview   # + images isométriques dans build/previews
python3 tools/generate_all.py                                  # tout le mod, puis validate.py
```

`generate_all.py` fixe `PYTHONHASHSEED=0` pour que les donjons sortent identiques d'un run à l'autre. Après une
modification de structure, commiter les `.nbt` régénérés avec le code Python.

## 3. Tester

On ne teste pas tout à chaque fois : on teste ce qu'on vient de changer, en jeu, avec des captures. La suite
complète ne tourne qu'avant une release.

### 3.1 Sur la machine de travail (environnement cloud du projet)

L'environnement cloud du projet a accès aux serveurs de Forge et de Mojang : on compile et on lance le vrai jeu
directement, sans attendre GitHub.

```bash
./gradlew build                                         # ≈ 5 min à froid, beaucoup moins ensuite
python3 tools/ci_client.py --focus structure:clockwork_citadel
python3 tools/ci_client.py --focus structure:giant_tree,entity:grand_clockmaker,step:quest_journal
```

`ci_client.py` lance Minecraft sans écran (Xvfb + rendu logiciel), crée un monde créatif, joue les étapes
demandées puis quitte. Pour une structure : elle est posée avec `/place structure` et photographiée sous quatre
angles (`nw`, `ne`, `se`, `sw`), au sol à hauteur d'yeux (`ground`) et du dessus (`top`). Pour une créature :
`front` et `side`. `step:<nom>` rejoue une étape nommée de la visite complète (`client/CiDriver.java`).

Résultats dans `build/ci-client/` : `brasshaven-shot-<nom>.png`, le rapport `ci-client-report.txt` (PASS/FAIL par
étape) et `ci-client-summary.md` (verdict + erreurs du log). Le test échoue sur une étape ratée, une capture
manquante, une erreur ou un modèle/texture manquant venant du mod, ou un crash.

Le premier lancement télécharge les ressources de Minecraft (≈ 9 min en tout) ; les suivants sont plus rapides.

### 3.2 Sur GitHub Actions

À chaque push, le CI compile et lance les tests rapides (serveur dédié, tests de démarrage). Les runs plus lourds
se lancent à la main (« Run workflow ») :

| Entrée | Effet |
|---|---|
| `focus` | test ciblé, comme `--focus` en local (≈ 4 min, les tests serveur sont sautés) |
| `perf` | mesures de performance poussées (mod contre vanilla, profils JFR) |
| `showcase` | film de la visite pour les vidéos de présentation (≈ 40 min) |
| `release` | publie la release `v<mod_version>` depuis ce commit |

Les captures d'un run ciblé sont publiées sur la pré-release `previews-ccr-127dc262-tsdn10`.

### 3.3 Montrer le résultat

Les captures en jeu sont la preuve qu'une modification marche. Elles sont partagées dans le projet (dossier
`screens/<date>/` des fichiers du projet) avec un mot sur ce qui a changé.

## 4. Publier

Résumé de `docs/PUBLISHING.md` :

1. `gradle.properties` : `mod_version` = la version à publier ; notes dans `docs/releases/<version>.md` (seulement ce
   qui a changé depuis la précédente, en français, pour les joueurs).
2. Tag `v<version>` poussé (ou « Run workflow » avec `release`) : le CI compile, teste et publie la release GitHub
   (puis CurseForge et Modrinth quand les comptes seront branchés).
3. Monter `mod_version` à la suivante juste après.

## 5. La refonte en cours (octobre 2026)

Priorités, dans l'ordre :

1. **Structures** : audit de circulation à 0 erreur, puis reconstruction à une échelle colossale en suivant
   `tools/BUILDING.md`, et de nouveaux types de structures vraiment différents.
2. **Boss** : vraie difficulté, adaptation au nombre de joueurs pour tous les boss, cycles « NG+ » (un boss
   rebattu revient plus fort, avec un meilleur butin).
3. **Textures** : minerais, blocs, objets (aujourd'hui trop proches du vanilla).
4. **Modèles 3D, animations, rendu des objets en main.**
5. **Interfaces** : infobulles, rendu dans l'inventaire, emplacements d'accessoires à côté de l'armure (planeur,
   anneaux…).
6. **Biomes fantastiques démesurés** : dans un mod séparé, optionnel, à côté de Brasshaven.

Journal de la refonte :

- **8 oct.** `tools/BUILDING.md` (recherche sur les builders, règles chiffrées), test ciblé en CI, audit des
  structures (316 erreurs au premier passage). Compilation et test en jeu sur la machine de travail.
  Donjons (catacombes, hypogée, puits de lithite, crypte du vide) ramenés à 0 erreur : l'escalier en colimaçon
  heurtait le mur à chaque coin (on ne remontait plus), les ossuaires bouchaient des portes, la sortie de
  l'hypogée passait au-dessus du puits. Tapis et meubles ne recouvrent plus les trappes. Les tours de la
  Forteresse de basalte ont enfin des portes.

## 6. Petits outils de débogage

Coupe ASCII d'un plan en cache (un caractère par bloc : `#` plein, `.` air, `s`/`S` dalle basse/haute, `^v<>`
escaliers, `H` échelle, `d` porte, `t` trappe, `$` coffre/tonneau) :

```python
import pickle
blocks = pickle.load(open("build/audit/cache/sand_hypogeum__layout_0.pkl", "rb"))["blocks"]
y = 1
for z in range(-26, -3):
    print(f"{z:4d} " + "".join("." if (b := blocks.get((x, y, z))) and b[0].endswith(":air")
                               else "#" if b else " " for x in range(-24, -1)))
```

Le dictionnaire `trace` du même fichier donne, pour chaque bloc, la ligne du générateur qui l'a posé.

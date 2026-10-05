# Publier et mettre à jour Wayfarers

Ce guide explique comment publier Wayfarers sur CurseForge (et Modrinth), comment une version part toute seule
une fois les comptes branchés, et comment joueurs et admins mettent à jour **sans perdre leur monde**.

En bref, une fois la configuration faite (sections 2 à 4) :

```bash
# 1. gradle.properties : mod_version=0.9.1-beta   (la version à publier)
git commit -am "Version 0.9.1-beta"
git tag v0.9.1-beta
git push origin main v0.9.1-beta
# 2. GitHub Actions compile, teste, publie la release GitHub, CurseForge et Modrinth.
# 3. gradle.properties : mod_version=0.9.2-beta   (la suivante), commit.
```

---

## 1. Les versions

| Quoi | Où | Exemple |
|---|---|---|
| Version publique | `mod_version` dans `gradle.properties` | `0.9.0-beta` |
| Build de développement (chaque push) | `mod_version` + `+build.<n° du run CI>` | `0.9.0-beta+build.84` |
| Build sur ta machine | `mod_version` + `+build.local` | `0.9.0-beta+build.local` |
| Nom du jar | `+` remplacé par `-` (un `+` casse les liens de téléchargement) | `wayfarers-0.9.0-beta-build.84.jar` |
| Protocole réseau | `network_protocol` dans `gradle.properties` | `1` |

- On suit le [versionnage sémantique](https://semver.org/lang/fr/) : `0.9.0-beta` < `0.9.0-rc.1` < `0.9.0` < `0.9.1-beta`.
  La partie `+build.84` ne compte pas dans l'ordre : c'est la même version, compilée par le CI.
- La version publiée est **exactement** `mod_version` : le CI refuse un tag `v0.9.1-beta` si `gradle.properties` dit
  autre chose. Après une release, passe `mod_version` à la version suivante (`0.9.2-beta`) pour que les builds de
  développement ne portent pas le numéro d'une version déjà publiée.
- Cette version est écrite dans `mods.toml` (ce que Forge affiche et compare), dans le nom du jar, et dans
  `META-INF/wayfarers/build.properties` (lu par le mod).
- **Protocole réseau** : n'augmente `network_protocol` que si un message réseau est ajouté, retiré ou change de
  format (`src/main/java/com/wayfarers/network`). Pas à chaque version.
- **Type de release** sur CurseForge/Modrinth : déduit de la version. `-alpha` donne alpha, `-beta` ou `-rc` donne
  beta, rien donne release. `0.9.x-beta` part donc en **beta**.

### Même version partout

Un joueur dont la version diffère de celle du serveur est refusé avec un message clair, en français ou en anglais,
qui donne les deux versions et le lien de téléchargement (`mod_download_url` dans `gradle.properties`, ou
`compat.downloadUrl` dans la config du serveur). Avec `compat.requireSameVersion = false`
(`config/wayfarers-common.toml`), le serveur laisse entrer les versions compatibles : même protocole et mêmes blocs
et objets. Le joueur voit alors seulement un avertissement dans le chat.

---

## 2. Créer le projet CurseForge

1. Va sur <https://authors.curseforge.com/> et connecte-toi (ou crée un compte CurseForge).
2. **Create Project**. Jeu **Minecraft**, classe **Mods**.
3. Remplis le formulaire :
   - **Name** : `Wayfarers` (si le nom est pris : `Wayfarers Guild`). Le *slug* devient l'adresse de la page,
     par exemple `curseforge.com/minecraft/mc-mods/wayfarers`.
   - **Summary** (une phrase, en anglais pour toucher tout le monde) : *Exploration-first co-op survival:
     45 hand-built structures, Elden Ring style bosses, shared quests, steampunk machines, maps and storage.*
   - **Description** : reprends le haut du `README.md`, soit la liste des fonctionnalités et le tableau des
     versions. L'éditeur accepte le Markdown. Ajoute les images de `docs/structures/` et `docs/bestiary/`.
   - **Main category** : *Adventure and RPG*. **Additional categories** (jusqu'à 4 ou 5) : *Structures*,
     *Mobs*, *Armor, Tools, and Weapons*, *Storage*, *Map and Information*, *Magic*.
   - **License** : **MIT License** (celle de `mods.toml`).
   - **Logo / avatar** : CurseForge veut une image carrée d'au moins 400 × 400 px. `src/main/resources/logo.png`
     fait 480 × 192 : recadre-la au carré, ou fais un carré à partir de `pack.png`.
   - **Source** : `https://github.com/jules-crevoisier/mode-minecraft`.
     **Issues** : `https://github.com/jules-crevoisier/mode-minecraft/issues`.
4. **Images (onglet *Images*)** : envoie 6 à 10 captures. Les meilleures sources :
   - `docs/structures/*.png` (vues isométriques de chaque structure) ;
   - `docs/bestiary/*.png` (créatures et boss) ;
   - les captures du vrai client, sur la pré-release GitHub `previews-<branche>` (`wayfarers-shot-*.png` :
     écrans, HUD, Citadelle) ;
   - les rendus en place `wayfarers-fit-*.png` de cette même pré-release.
5. Enregistre. **Le premier fichier peut être envoyé tout de suite** : la première version part en modération, et
   le projet devient public après validation par CurseForge (en général quelques jours).
6. Note le **Project ID** : c'est un nombre, affiché sur la page du projet dans le cadre *About Project*.

Après la création, mets l'adresse de la page dans `gradle.properties` :

```properties
mod_download_url=https://www.curseforge.com/minecraft/mc-mods/wayfarers
```

C'est le lien donné aux joueurs refusés pour version différente. Commit, puis fais une release.

### Modrinth (facultatif)

1. <https://modrinth.com/dashboard/projects>, **Create a project** : nom `Wayfarers`, type *Mod*, visibilité au choix.
2. Remplis la description, les catégories (*Adventure*, *Worldgen*, *Mobs*, *Equipment*, *Storage*, *Magic*),
   la licence MIT, le lien source et la galerie (mêmes images que pour CurseForge).
3. Note l'**ID** du projet (page du projet, menu ⋯, *Copy ID*) ou son *slug* (`wayfarers`). Les deux fonctionnent.

---

## 3. Les jetons d'API et les réglages GitHub

### Jeton CurseForge

1. Sur CurseForge, menu de ton compte, **API Tokens** (adresse directe :
   <https://legacy.curseforge.com/account/api-tokens>). Si CurseForge a déplacé la page, cherche « API token »
   dans les réglages du compte auteur.
2. Crée un jeton nommé `GitHub Wayfarers` et copie-le : il ne s'affiche qu'une fois.

### Jeton Modrinth

<https://modrinth.com/settings/pats>, **Create a PAT**, nom `GitHub Wayfarers`, droits **Create versions**,
**Read projects** et **Read versions**. Mets l'expiration la plus longue possible et note la date pour le
renouveler.

### Dans GitHub

Dépôt `jules-crevoisier/mode-minecraft`, **Settings**, **Secrets and variables**, **Actions** :

| Onglet | Nom | Valeur |
|---|---|---|
| *Secrets* | `CURSEFORGE_TOKEN` | le jeton CurseForge |
| *Variables* | `CURSEFORGE_PROJECT_ID` | le Project ID (nombre) |
| *Secrets* | `MODRINTH_TOKEN` | le jeton Modrinth (facultatif) |
| *Variables* | `MODRINTH_PROJECT_ID` | l'ID ou le slug Modrinth (facultatif) |

- Sans `CURSEFORGE_PROJECT_ID`, le job `curseforge` est sauté. Sans `CURSEFORGE_TOKEN`, il ne fait rien et
  l'indique dans le journal du job. La release GitHub, elle, part dans tous les cas. Même règle pour Modrinth.
- Ne mets jamais un jeton dans un fichier du dépôt.

---

## 4. Comment une release part

1. Vérifie que le dernier build de `main` est vert (onglet **Actions**).
2. Dans `gradle.properties`, mets `mod_version` à la version à publier, par exemple `0.9.1-beta`, puis commit.
3. Crée et pousse le tag `v` + version :
   ```bash
   git tag v0.9.1-beta
   git push origin v0.9.1-beta
   ```
   Tu peux aussi passer par GitHub : **Releases**, **Draft a new release**, tag `v0.9.1-beta` à créer sur `main`,
   **Publish**. Le CI complète alors cette release.
4. Le workflow `.github/workflows/build.yml` enchaîne :
   - **build** : vérifie que le tag correspond à `mod_version` et qu'aucun id de bloc ou d'objet n'a disparu (voir
     section 6), compile le jar, construit le pack serveur et le modpack, et teste les options JVM du pack serveur
     sur Java 25 ;
   - **smoke-test** et **fit-test** : le jar tourne sur un vrai serveur Forge (structures, créatures, objets,
     butins). Si un test échoue, rien n'est publié ;
   - **github-release** : release GitHub `v0.9.1-beta`, marquée *Latest*. Son texte vient de
     `tools/changelog.py`, qui liste les commits depuis le tag `v*` précédent. Elle contient le jar, le pack
     serveur `wayfarers-server-*.zip` et le modpack `wayfarers-modpack-*.zip` ;
   - **curseforge** : envoie le jar sur CurseForge en *beta*, pour Minecraft 26.2, Forge et Java 25, avec le même
     changelog. Il ajoute ensuite à la release `wayfarers-modpack-*-curseforge.zip`, qui référence le fichier
     CurseForge ;
   - **modrinth** : envoie le jar sur Modrinth en *beta*, pour Minecraft 26.2 et Forge.
5. Passe `mod_version` à la version suivante (`0.9.2-beta`) et commit.

**Si un envoi échoue**, par exemple parce que CurseForge ne connaît pas encore Minecraft 26.2 ou qu'un jeton a
expiré : corrige le problème, puis **Actions**, le run du tag, **Re-run failed jobs**. Ne recrée pas le tag.

**Chaque push sur une branche** produit aussi un build de développement sur la pré-release `dev-<branche>`, avec le
jar, le pack serveur et le modpack. Ces builds ne sont pas proposés comme mise à jour aux joueurs.

### Les outils, à la main

```bash
python3 tools/changelog.py --version 0.9.1-beta                # changelog depuis le dernier tag v*
python3 tools/make_modpack.py configs                          # régénère les configs recommandées
python3 tools/make_modpack.py serverpack --jar build/libs/wayfarers-0.9.1-beta.jar
python3 tools/make_modpack.py modpack --jar build/libs/wayfarers-0.9.1-beta.jar [--project-id N --file-id N]
python3 tools/publish.py curseforge --jar build/libs/wayfarers-0.9.1-beta.jar --dry-run
```

---

## 5. Le modpack et le pack serveur

- `modpack/manifest.json` est le modèle de modpack CurseForge (Minecraft 26.2, Forge 65.1.0).
  `modpack/overrides/config/` contient les configs recommandées. `tools/make_modpack.py configs` les écrit à partir
  des classes de config du mod, et `tools/validate.py` vérifie qu'elles restent à jour.
- `wayfarers-modpack-<version>.zip` contient le jar. Les joueurs l'importent dans l'app CurseForge : **Create
  Custom Profile**, **Import**. Il marche avant même que le projet CurseForge existe.
- `wayfarers-modpack-<version>-curseforge.zip` référence le fichier CurseForge du mod (ids remplis par le CI). Pour
  publier un **modpack** sur CurseForge, crée un second projet de classe **Modpacks** et envoie-lui ce zip.
- `wayfarers-server-<version>.zip` est le serveur prêt à lancer : le jar, `start.sh` / `start.bat`, les options JVM
  (`jvm_args.txt`, 6 Go par défaut), `server.properties` et la config recommandée. Au premier lancement, le script
  installe Forge et demande d'accepter le CLUF de Minecraft. Voir `serverpack/LISEZMOI.txt`.

---

## 6. Ne jamais casser un monde existant

- **Ids de registre.** `tools/data/registry_ids.json` liste tous les ids que le mod a publiés : blocs, objets,
  créatures, block entities et menus. `tools/validate.py` y ajoute tout seul les nouveaux ids, et refuse un id qui
  disparaît sans explication. Pour **renommer** un id, ajoute une entrée dans `aliases` :
  ```json
  "aliases": { "item": { "ancien_id": "nouvel_id" } }
  ```
  Dans les anciens mondes, les blocs posés, les objets dans les coffres et les créatures deviennent alors le nouvel
  id (`MissingMappingsEvent` de Forge, `release/RegistryRemap.java`). Pour **supprimer** un id pour de bon, ajoute
  `"removed": { "block": { "ancien_id": "pourquoi" } }`. Le monde l'efface alors sans ouvrir l'écran
  « missing entries ».
- **Données sauvegardées.** Les données du mod portent un `data_version` : pierres de voyage et quêtes partagées
  (`wayfarers_guild.dat`), carte partagée (`data/wayfarers_map/format.json`), réglages du terminal de guilde. Si un
  format change, augmente la constante dans `data/DataVersions.java` et ajoute une étape de migration depuis
  l'ancienne version. Les étapes s'enchaînent, donc un monde qui a plusieurs versions de retard se met à jour en un
  seul chargement.

---

## 7. Mettre à jour : joueurs

1. **Sauvegarde ton monde solo** : *Solo*, choisis le monde, **Modifier**, **Faire une sauvegarde**. Tu peux aussi
   copier le dossier `saves/<monde>`.
2. Mets la nouvelle version :
   - **installée par CurseForge** : l'app propose la mise à jour, clique **Update** ;
   - **à la main** : dans le dossier `mods` du profil, supprime l'ancien `wayfarers-*.jar` et dépose le nouveau.
     Il ne doit jamais y en avoir deux.
3. Lance le jeu et ouvre le monde : il est conservé. Les nouvelles structures n'apparaissent que dans les zones
   encore jamais explorées.
4. Pour un serveur, prends **exactement la version du serveur**. Sinon, le message de refus donne les deux versions
   et le lien.

Le mod vérifie lui-même s'il existe une nouvelle version, avec un message sur l'écran titre et une ligne dans le chat
avec le lien du changelog. Il ne télécharge jamais rien. Pour couper cette vérification :
`updates.checkForUpdates = false` dans `config/wayfarers-client.toml`.

## 8. Mettre à jour : admins de serveur

1. Préviens les joueurs de la version et de l'heure.
2. **Arrête le serveur** (`stop`).
3. **Sauvegarde le monde** : copie le dossier `world/`. Le `start.sh` / `start.bat` du pack serveur le fait aussi
   tout seul dans `backups/` au premier démarrage d'une nouvelle version.
4. Remplace le jar : décompresse le nouveau `wayfarers-server-*.zip` **par-dessus** l'ancien dossier, ou remplace
   seulement `mods/wayfarers-*.jar`. Tes réglages (`server.properties`, `config/`) ne sont jamais écrasés, et
   l'ancien jar part dans `old-mods/`.
5. Relance le serveur. Le journal indique si les données du monde ont été mises à jour (`upgraded the ... data`).
6. **En cas de problème** : arrête le serveur, remets l'ancien jar et restaure la sauvegarde.

Au démarrage, le serveur écrit dans son journal si une nouvelle version existe. Pour couper ce message :
`updates.checkForUpdates = false` dans `config/wayfarers-common.toml`. Avec un hébergeur (Pterodactyl, etc.),
installe Forge 65.1.0 depuis le panneau, envoie `mods/` et `config/`, et mets les options de `jvm_args.txt` dans le
champ des arguments JVM.

> La vérification des mises à jour lit les releases `v*` de GitHub. Elle ne fonctionne que si le dépôt est public.
> Sinon, elle échoue en silence.

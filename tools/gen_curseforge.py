#!/usr/bin/env python3
"""The CurseForge / Modrinth project page: section banners, the gallery and the description (English and French).

    python3 tools/gen_curseforge.py      # docs/curseforge/{img/*, description_en.md, description_fr.md}

Banners are drawn in the mod's brass style from the structure renders of the wiki (build/wiki/img/s, run
tools/gen_wiki.py first); the gallery pictures are the real client screenshots of the CI (previews release) and the
biome renders. The descriptions link the pictures by their raw GitHub URL, so they can be pasted as they are in the
CurseForge description editor (Markdown mode); the same files can also be uploaded by hand.
"""
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont

from gen_logo import BRASS, BRASS_DARK, INK
from gen_promo import SERIF, SANS, backdrop, cutout, frame, glow

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "curseforge")
IMG = os.path.join(OUT, "img")
CACHE = os.path.join(ROOT, "build", "curseforge")
PREVIEWS = "https://github.com/jules-crevoisier/mode-minecraft/releases/download/previews-ccr-127dc262-tsdn10/"
RAW = "https://raw.githubusercontent.com/jules-crevoisier/mode-minecraft/ccr-127dc262-tsdn10/docs/curseforge/img/"
RELEASES = "https://github.com/jules-crevoisier/mode-minecraft/releases"
WIKI = "https://claude.ai/artifact/TbrbkEJuQNFhMAYHZ9e7x8"

# section id -> (English title, French title, English subtitle, French subtitle, structure render for the art)
SECTIONS = [
    ("structures", "Mega-Structures", "Méga-structures", "Hand-built wonders in every dimension",
     "Des merveilles bâties à la main, dans toutes les dimensions", "clockwork_citadel"),
    ("peoples", "Peoples & Creatures", "Peuples et créatures", "Dwarves, sylvans, clockwork citizens, monks",
     "Nains, sylvains, citoyens mécaniques, moines", "dwarven_city"),
    ("bosses", "Bosses", "Boss", "Twenty fights in the Elden Ring style", "Vingt combats façon Elden Ring",
     "sunken_citadel"),
    ("quests", "Quests & Progression", "Quêtes et progression", "Earn your tools, contract by contract",
     "Gagne tes outils, contrat après contrat", "guild_outpost"),
    ("maps", "Maps & Travel", "Cartes et voyages", "Shared world map, minimap radar, waystones",
     "Carte partagée, radar, pierres de voyage", "sky_harbour"),
    ("magic", "Talents & Magic", "Talents et magie", "A skill tree and simple spells",
     "Un arbre de talents et une magie simple", "crystal_cathedral"),
    ("machines", "Machines & Storage", "Machines et stockage", "Simple automation, no power cables",
     "De l'automatisation simple, sans câble ni énergie", "geothermal_foundry"),
    ("recipes", "Recipe Viewer", "Livre de recettes", "Built in: search, recipes, uses, one-click fill",
     "Intégré : recherche, recettes, utilisations, remplissage en un clic", "inventor_manor"),
    ("together", "Play Together", "Jouer ensemble", "Companies, trading, mail, contracts, duels",
     "Compagnies, échanges, poste, contrats, duels", "sylvan_palace"),
    ("biomes", "Biomes", "Biomes", "Three new biomes on Minecraft's own terrain",
     "Trois nouveaux biomes sur le relief de Minecraft", "tesla_observatory"),
    ("install", "Install & Servers", "Installation et serveurs", "Forge 26.2, one jar, ready-made server pack",
     "Forge 26.2, un seul jar, pack serveur prêt", "dwarven_forge"),
]

SHOTS = ["mega_structure", "peoples", "creatures_places", "health_bars", "folk_trade", "quest_journal", "world_map_3d",
         "minimap_radar", "waystone", "talent_tree", "machine_harvester", "guild_terminal", "recipe_view",
         "recipe_fill", "company", "trade", "pneumatic_post", "contract_board", "creatures"]
BIOMES = ["crimson_mire", "volcanic_highlands", "pale_dunes"]
RENDERS = ["clockwork_citadel", "sylvan_palace", "sunken_citadel", "dwarven_city", "sky_harbour", "basalt_fortress"]


def section_banner(sid, title, sub, render, w=1200, h=200):
    img = backdrop((w, h))
    img = glow(img, [w * 0.55, -h * 0.2, w * 1.1, h * 1.3], blur=60)
    try:
        c = cutout(render, int(h * 1.35))
        img.alpha_composite(c, (int(w - c.width * 0.85), int(h * 0.02)))
    except (FileNotFoundError, OSError):
        pass
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for x in range(int(w * 0.62)):
        sd.line([(x, 0), (x, h)], fill=(12, 10, 10, int(215 * (1 - x / (w * 0.62)) ** 1.2)))
    img = Image.alpha_composite(img, shade)
    d = ImageDraw.Draw(img)
    tf = ImageFont.truetype(SERIF, 64)
    sf = ImageFont.truetype(SANS, 26)
    d.text((44, 38), title, font=tf, fill=INK)
    d.text((40, 34), title, font=tf, fill=BRASS)
    d.line([(42, 116), (42 + min(560, d.textlength(title, font=tf)), 116)], fill=BRASS_DARK, width=3)
    d.text((42, 128), sub, font=sf, fill=(232, 214, 180))
    frame(img, 5)
    img.convert("RGB").save(os.path.join(IMG, f"banner_{sid}.png"), optimize=True)


def fetch(name, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        try:
            urllib.request.urlretrieve(url, path)
        except OSError as e:
            print(f"skip {name}: {e}")
            return None
    return path


def gallery():
    for n in SHOTS:
        p = fetch(f"shot-{n}.png", PREVIEWS + f"brasshaven-shot-{n}.png")
        if p:
            Image.open(p).convert("RGB").save(os.path.join(IMG, f"shot_{n}.jpg"), quality=86, optimize=True)
    for b in BIOMES:
        p = fetch(f"biome-{b}.png", PREVIEWS + f"brasshaven-biome-{b}.png") or \
            fetch(f"biome-{b}-old.png", PREVIEWS + f"wayfarers-biome-{b}.png")
        if p:
            im = Image.open(p).convert("RGBA")
            bg = Image.new("RGBA", im.size, (24, 20, 18, 255))
            Image.alpha_composite(bg, im).convert("RGB").save(os.path.join(IMG, f"biome_{b}.jpg"), quality=88)
    for r in RENDERS:
        src = os.path.join(ROOT, "build", "wiki", "img", "s", f"{r}.webp")
        if os.path.exists(src):
            Image.open(src).convert("RGB").save(os.path.join(IMG, f"render_{r}.jpg"), quality=88, optimize=True)


def img(name, alt):
    return f"![{alt}]({RAW}{name})"


def banner(sid, lang):
    s = next(x for x in SECTIONS if x[0] == sid)
    return img(f"banner_{sid}.png", s[1] if lang == "en" else s[2])


def row(*cells):
    return " ".join(img(f, a) for f, a in cells)


def description_en():
    L = [img("hero.png", "Brasshaven"), "",
         "# Brasshaven — a steampunk adventure for Minecraft",
         "",
         "**Brasshaven** turns survival with friends into a great expedition: giant hand-built structures to explore, "
         "peoples to trade with, Elden Ring-style bosses, simple machines, a shared world map, talents and magic — "
         "all in a brass, copper and steam style, and as light on the server as vanilla.",
         "",
         "**Minecraft 26.2 · Forge 65.1.0 · Java 25** · client and server · one jar, no library needed",
         "",
         banner("structures", "en"), "",
         "- **35 structures** across the Overworld, the depths, the Nether and the End, 50 to 100 blocks wide, towers "
         "up to 75 blocks, furnished interiors and secrets.",
         "- The **Clockwork Citadel**: a 71×71 city with a 75-block clock tower, seven floors and four workshops.",
         "- The **Sylvan Palace**, the **World Tree**, the **Sky Harbour**, the **Dwarven City**, the **Sunken "
         "Citadel**, the **Basalt Fortress**, the **Undercity**…",
         "- Barrels full of supplies that fit the room, chests with real rewards, waystones in many places.",
         "",
         row(("render_clockwork_citadel.jpg", "Clockwork Citadel"), ("render_sylvan_palace.jpg", "Sylvan Palace")),
         row(("render_sunken_citadel.jpg", "Sunken Citadel"), ("render_basalt_fortress.jpg", "Basalt Fortress")),
         img("shot_mega_structure.jpg", "The Clockwork Citadel in game"), "",
         banner("peoples", "en"), "",
         "- **Peoples with their own look and trades**: **dwarves** (smiths, miners, brewers, gem cutters, guards), "
         "**sylvans** (gardeners, herbalists, woodwrights, archers), **clockwork citizens** and **monks**. Their guards "
         "defend the place.",
         "- **Creatures of the hostile places**, each with a trick: the Bandit Marksman, the Sky Raider that lifts you "
         "and drops you, the Barnacle Crab, the Lantern Wisp that puts out the lights, the Cinder Hound pack, the Rift "
         "Sentinel.",
         "- **Health bars** above monsters, with the damage trail and numbers.",
         "",
         row(("shot_peoples.jpg", "The peoples"), ("shot_creatures_places.jpg", "Creatures of the places")),
         row(("shot_folk_trade.jpg", "Trading with a dwarf"), ("shot_health_bars.jpg", "Health bars")),
         "",
         banner("bosses", "en"), "",
         "- **20 bosses** (16 great bosses and 4 dungeon champions), each at the bottom of a descent, behind a mist "
         "gate, with a site of grace before it.",
         "- Telegraphed attacks, a second phase at half health, posture breaks, a long boss bar with its own music.",
         "- Boss weapons with active abilities, three armour sets with full-set bonuses.",
         "",
         banner("quests", "en"), "",
         "- A **linear progression**: you start with the Manual and the Atlas, the nearest Guild Outpost is marked on "
         "your map, and the tracker always shows the next step.",
         "- **Quest givers** (Guild Agent, Scholar, Tinkerer, Druid, Dwarf Elder) with **20 contracts**: fetch, hunt, "
         "explore, deliver. The **Structure Compass** is earned, not given.",
         "- A server-wide quest in 5 chapters, from the first steps to the Void Warden.",
         "",
         img("shot_quest_journal.jpg", "Quest journal"), "",
         banner("maps", "en"), "",
         "- A **world map shared by the whole server** (M) with relief shading and a **3D view**, waypoints, pings.",
         "- A **minimap** with a size in pixels, and a **radar** in the style of Xaero's: mob heads, NPCs, bosses and "
         "players.",
         "- **Waystones**: discovered for everyone, travel across dimensions.",
         "",
         row(("shot_world_map_3d.jpg", "World map, 3D view"), ("shot_minimap_radar.jpg", "Minimap radar")),
         img("shot_waystone.jpg", "Waystones"), "",
         banner("magic", "en"), "",
         "- A **talent tree** of 36 talents (K) in four branches, an active ability (V), mana and 7 spell staves.",
         "",
         img("shot_talent_tree.jpg", "Talent tree"), "",
         banner("machines", "en"), "",
         "- **9 simple machines** — harvester, sprinkler, vacuum hopper, block breaker and placer, timer, wireless "
         "redstone, entity detector — one block, one screen, no energy network. Their window lights up when they work.",
         "- The **Guild Terminal**: every chest of your base in one searchable grid; sorting chests, "
         "backpack, magnet ring, graves.",
         "- Brass, zinc, mithril and aether; 13 decorative blocks and 9 3D furniture pieces.",
         "",
         row(("shot_machine_harvester.jpg", "Harvester"), ("shot_guild_terminal.jpg", "Guild Terminal")),
         "",
         banner("recipes", "en"), "",
         "- A **built-in recipe viewer** in the mod's style, without JEI: an item list beside every inventory with "
         "search (I), **R** for recipes, **U** for uses, and a **+** button that fills the crafting grid for you "
         "(server-side, no duplication). It steps aside if JEI is installed.",
         "",
         row(("shot_recipe_view.jpg", "Recipe viewer"), ("shot_recipe_fill.jpg", "One-click fill")),
         "",
         banner("together", "en"), "",
         "- **Companies** (O) of up to 8 players by default (configurable up to 100), shared XP, company chat, "
         "companions on the map.",
         "- **Secure trading**, the **Pneumatic Post** (mail and parcels, even to offline players), the **Contract "
         "Board**, **emotes** (Y) and **duels** where nobody dies.",
         "",
         row(("shot_company.jpg", "Company"), ("shot_trade.jpg", "Secure trade")),
         row(("shot_pneumatic_post.jpg", "Pneumatic Post"), ("shot_contract_board.jpg", "Contract Board")),
         "",
         banner("biomes", "en"), "",
         "- **Crimson Mire**, **Volcanic Highlands** and **Pale Dunes** on Minecraft's own terrain, plus small natural "
         "touches in vanilla biomes (boulders, fallen logs, hot springs…). Each can be switched off.",
         "",
         row(("biome_crimson_mire.jpg", "Crimson Mire"), ("biome_volcanic_highlands.jpg", "Volcanic Highlands"),
             ("biome_pale_dunes.jpg", "Pale Dunes")),
         "",
         banner("install", "en"), "",
         "- **Players**: install Forge 26.2-65.1.0 and put the Brasshaven jar in `mods/` — or import the modpack zip "
         "in the CurseForge app.",
         "- **Servers**: the server pack starts with `start.sh` / `start.bat` (Java 25) and ships tuned JVM flags; the "
         "same jar goes on the server and every player. Admin guide and performance tips (pre-generate with Chunky) are "
         "in the repository's docs.",
         "- **Performance**: measured on every build against Forge without the mod — chunk generation as fast as "
         "vanilla, server tick within a few percent.",
         "- **Start a new world**: the structures only appear in chunks that were never generated.",
         "",
         f"**Links**: [Downloads and changelogs]({RELEASES}) · [Illustrated wiki (French)]({WIKI})",
         ""]
    return "\n".join(L)


def description_fr():
    L = [img("hero.png", "Brasshaven"), "",
         "# Brasshaven — une aventure steampunk pour Minecraft",
         "",
         "**Brasshaven** transforme une survie entre amis en grande expédition : des structures géantes bâties à la "
         "main, des peuples avec qui commercer, des boss façon Elden Ring, des machines simples, une carte du monde "
         "partagée, des talents et de la magie. Le tout en laiton, cuivre et vapeur, et aussi léger pour le serveur "
         "que Minecraft sans mod.",
         "",
         "**Minecraft 26.2 · Forge 65.1.0 · Java 25** · client et serveur · un seul jar, aucune bibliothèque",
         "",
         banner("structures", "fr"), "",
         "- **35 structures** dans l'Overworld, les profondeurs, le Nether et l'End : 50 à 100 blocs de large, des "
         "tours jusqu'à 75 blocs, des intérieurs meublés et des secrets.",
         "- La **Citadelle d'horlogerie** : une ville de 71×71 blocs, une tour-horloge de 75 blocs, sept étages, quatre "
         "ateliers.",
         "- Le **Palais sylvain**, l'**Arbre-Monde**, le **Port céleste**, la **Cité naine**, la **Citadelle "
         "engloutie**, la **Forteresse de basalte**, la **Ville basse**…",
         "- Des barils remplis selon la pièce, des coffres aux vraies récompenses, des pierres de voyage.",
         "",
         row(("render_clockwork_citadel.jpg", "Citadelle d'horlogerie"), ("render_sylvan_palace.jpg", "Palais sylvain")),
         row(("render_sunken_citadel.jpg", "Citadelle engloutie"), ("render_basalt_fortress.jpg", "Forteresse de basalte")),
         img("shot_mega_structure.jpg", "La Citadelle en jeu"), "",
         banner("peoples", "fr"), "",
         "- **Des peuples avec leur allure et leurs échanges** : **nains** (forgerons, mineurs, brasseurs, tailleurs de "
         "gemmes, gardes), **sylvains** (jardiniers, herboristes, menuisiers, archers), **citoyens mécaniques** et "
         "**moines**. Leurs gardes défendent le lieu.",
         "- **Les créatures des lieux hostiles**, chacune avec son tour : tireur bandit, pillard du ciel qui soulève "
         "et lâche, crabe à bernacles, feu follet qui éteint les lumières, meute de molosses de cendre, sentinelle de la "
         "faille.",
         "- **Barres de vie** au-dessus des monstres, avec traînée et chiffres de dégâts.",
         "",
         row(("shot_peoples.jpg", "Les peuples"), ("shot_creatures_places.jpg", "Les créatures des lieux")),
         row(("shot_folk_trade.jpg", "Commercer avec un nain"), ("shot_health_bars.jpg", "Barres de vie")),
         "",
         banner("bosses", "fr"), "",
         "- **20 boss** (16 grands boss et 4 champions de donjon), chacun au fond d'une descente, derrière une brume, "
         "avec un lieu de grâce avant.",
         "- Attaques télégraphiées, deuxième phase à mi-vie, posture, longue barre de vie et musique de combat.",
         "- Armes de boss à capacité, trois ensembles d'armure avec bonus.",
         "",
         banner("quests", "fr"), "",
         "- **Une progression linéaire** : on démarre avec le Manuel et l'Atlas, le poste de Guilde le plus proche est "
         "marqué sur la carte, et le suivi indique toujours l'étape suivante.",
         "- **Donneurs de quêtes** (Agent de guilde, Érudit, Bricoleur, Druide, Ancien nain) et **20 contrats** : "
         "apporter, chasser, explorer, livrer. La **boussole des structures** se gagne.",
         "- Une grande quête partagée par le serveur, en 5 chapitres.",
         "",
         img("shot_quest_journal.jpg", "Journal de quêtes"), "",
         banner("maps", "fr"), "",
         "- **Carte du monde partagée par tout le serveur** (M), relief ombré et **vue 3D**, repères, signaux.",
         "- **Mini-carte** à la taille en pixels près et **radar** façon Xaero : têtes des mobs, PNJ, boss, joueurs.",
         "- **Pierres de voyage** découvertes pour tout le monde, voyage entre dimensions.",
         "",
         row(("shot_world_map_3d.jpg", "Carte du monde en 3D"), ("shot_minimap_radar.jpg", "Radar de la mini-carte")),
         img("shot_waystone.jpg", "Pierres de voyage"), "",
         banner("magic", "fr"), "",
         "- **Arbre de 36 talents** (K) en quatre branches, capacité active (V), mana et 7 bâtons de sort.",
         "",
         img("shot_talent_tree.jpg", "Arbre de talents"), "",
         banner("machines", "fr"), "",
         "- **9 machines simples** — moissonneuse, arroseur, aspirateur, casseur et poseur de blocs, minuteur, redstone "
         "sans fil, détecteur — un bloc, un écran, pas de réseau d'énergie. Leur vitre s'allume quand elles travaillent.",
         "- Le **Terminal de guilde** : tous les coffres de la base dans une grille avec recherche ; "
         "coffres de tri, sac, anneau aimanté, tombes.",
         "- Laiton, zinc, mithril et éther ; 13 blocs décoratifs et 9 meubles en 3D.",
         "",
         row(("shot_machine_harvester.jpg", "Moissonneuse"), ("shot_guild_terminal.jpg", "Terminal de guilde")),
         "",
         banner("recipes", "fr"), "",
         "- **Un livre de recettes intégré**, au style du mod, sans JEI : liste d'objets à côté de chaque inventaire "
         "avec recherche (I), **R** pour les recettes, **U** pour les utilisations, et un bouton **+** qui remplit la "
         "grille de craft (côté serveur, aucune duplication). Il s'efface si JEI est installé.",
         "",
         row(("shot_recipe_view.jpg", "Livre de recettes"), ("shot_recipe_fill.jpg", "Remplissage en un clic")),
         "",
         banner("together", "fr"), "",
         "- **Compagnies** (O) de 8 joueurs par défaut, réglable jusqu'à 100 : XP partagée, chat, compagnons sur la "
         "carte.",
         "- **Échange sécurisé**, **poste pneumatique** (lettres et colis, même aux absents), **tableau des contrats**, "
         "**gestes** (Y) et **duels** sans mort.",
         "",
         row(("shot_company.jpg", "Compagnie"), ("shot_trade.jpg", "Échange sécurisé")),
         row(("shot_pneumatic_post.jpg", "Poste pneumatique"), ("shot_contract_board.jpg", "Tableau des contrats")),
         "",
         banner("biomes", "fr"), "",
         "- **Marais pourpre**, **Hautes terres volcaniques** et **Dunes pâles** sur le relief de Minecraft, et de "
         "petites touches naturelles dans les biomes vanilla (rochers, troncs tombés, sources chaudes…). Tout se "
         "désactive.",
         "",
         row(("biome_crimson_mire.jpg", "Marais pourpre"), ("biome_volcanic_highlands.jpg", "Hautes terres volcaniques"),
             ("biome_pale_dunes.jpg", "Dunes pâles")),
         "",
         banner("install", "fr"), "",
         "- **Joueurs** : installe Forge 26.2-65.1.0 et mets le jar Brasshaven dans `mods/`, ou importe le modpack "
         "dans l'app CurseForge.",
         "- **Serveurs** : le pack serveur démarre avec `start.sh` / `start.bat` (Java 25) avec des options JVM réglées ; "
         "même jar sur le serveur et chez chaque joueur. Guide d'administration et conseils de performance "
         "(pré-génération avec Chunky) dans la doc du dépôt.",
         "- **Performances** : mesurées à chaque build face à Forge sans le mod — génération aussi rapide que vanilla, "
         "tick serveur à quelques pour cent près.",
         "- **Crée un nouveau monde** : les structures n'apparaissent que dans les zones jamais générées.",
         "",
         f"**Liens** : [Téléchargements et nouveautés]({RELEASES}) · [Wiki illustré]({WIKI})",
         ""]
    return "\n".join(L)


def main():
    os.makedirs(IMG, exist_ok=True)
    hero = os.path.join(ROOT, "build", "promo", "banner_1920x640.png")
    if os.path.exists(hero):
        Image.open(hero).convert("RGB").save(os.path.join(IMG, "hero.png"), optimize=True)
    for sid, en, _fr, sub_en, _sub_fr, render in SECTIONS:
        section_banner(sid, en, sub_en, render)
    for sid, _en, fr, _sub_en, sub_fr, render in SECTIONS:
        section_banner(sid + "_fr", fr, sub_fr, render)
    gallery()
    with open(os.path.join(OUT, "description_en.md"), "w", encoding="utf-8") as f:
        f.write(description_en())
    fr = description_fr()
    for sid, *_ in SECTIONS:  # the French page uses the French banners
        fr = fr.replace(f"banner_{sid}.png", f"banner_{sid}_fr.png")
    with open(os.path.join(OUT, "description_fr.md"), "w", encoding="utf-8") as f:
        f.write(fr)
    print(f"wrote {OUT}: {len(os.listdir(IMG))} images, description_en.md, description_fr.md")


if __name__ == "__main__":
    main()

"""The people and the creatures of the places: one table for names, roles, trades, loot, eggs, manual pages and wiki
texts (like ocean.py and gadgets.py).

Peoples (friendly residents, com.brasshaven.entity.folk.Resident): each people is one entity type whose roles are
texture variants of its model (tools/wf/mobs/<people>.py). A role is
  * a TRADER or a WORKER: right-click opens the vanilla trading screen with the role's themed offers; a worker walks
    between the job blocks around its home and plays its work animation there, a trader keeps to its stall,
  * a GUARD: attacks monsters near its home and anyone who hurts a resident; no trades, a few words instead.
Residents never despawn, stay within their home radius, flee monsters (guards excepted), heal slowly and refuse to
trade with a player who just hurt one of them.

Creatures (hostile, com.brasshaven.entity.mob): one per kind of hostile place, each with its own trick.

Outputs: content names and spawn eggs (content.py), loot tables (gen_data.py), egg colours (gen_textures.py),
translations (gen_assets.py), GeneratedFolk.java (gen_java.py), manual pages (guide.py), wiki texts (wiki_text.py /
gen_wiki.py), template helpers for the structure builders (resident(), creature(), settle()).
"""
NS = "brasshaven"
W = NS + ":"


# ====================================================================== trades
def T(cost, result, uses=12, xp=2, cost2=None):
    """A trade: ``cost`` (and ``cost2``) for ``result``; items as "id" or "id*count", "potion:<name>" for a potion.
    Ids without a namespace are vanilla; mod items are written "brasshaven:<id>"."""
    def parse(s):
        if s is None:
            return None
        iid, _, n = s.partition("*")
        if not iid.startswith("potion:") and ":" not in iid:
            iid = "minecraft:" + iid
        return iid, int(n or 1)
    return dict(a=parse(cost), b=parse(cost2), r=parse(result), uses=uses, xp=xp)


def buy(item, emeralds=1, uses=16):
    """The resident buys ``item`` ("id*count") for emeralds."""
    return T(item, f"emerald*{emeralds}", uses=uses, xp=2)


def sell(emeralds, item, uses=12, cost2=None):
    return T(f"emerald*{emeralds}", item, uses=uses, xp=3, cost2=cost2)


# ====================================================================== peoples
# role: (id, english name, french name, kind, work animation, work style, job blocks, trades)
#   kind: trader (keeps to its stall), worker (walks between job blocks), guard (defends, no trades)
#   work style (Java effects): hammer, dig, brew, carve, tend, tinker, wind, scribe
#   job blocks: block ids ("minecraft:anvil"), "*_suffix" or "prefix_*" patterns; the resident scans its home for
#   them now and then and walks to one to work
def R(rid, en, fr, kind, work, style, jobs, trades=()):
    return dict(id=rid, en=en, fr=fr, kind=kind, work=work, style=style, jobs=list(jobs), trades=list(trades))


PEOPLES = {
    "dwarf": dict(
        en="Dwarf", fr="Nain", plural=("Dwarves", "Nains"), egg=((120, 70, 44), (214, 170, 64)), size=(0.8, 1.4),
        homes=["dwarven_city", "dwarven_mine"],
        roles=[
            R("smith", "Dwarven Smith", "Forgeron nain", "worker", "hammer", "hammer",
              ["anvil", "chipped_anvil", "damaged_anvil", "blast_furnace", "smithing_table", "grindstone", "furnace"],
              [buy("coal*15"), buy("iron_ingot*4"), sell(5, "iron_pickaxe"), sell(5, "iron_axe"), sell(4, "shield"),
               sell(12, "iron_chestplate", uses=4), sell(8, W + "brass_pickaxe", uses=4),
               sell(16, W + "mithril_pickaxe", uses=3, cost2=W + "raw_mithril*2")]),
            R("miner", "Dwarven Miner", "Mineur nain", "worker", "dig", "dig",
              ["stonecutter", "*_ore", "raw_iron_block", "raw_copper_block", "chest", "barrel", "rail"],
              [sell(1, "torch*16", uses=16), sell(2, "raw_iron*5"), sell(3, "raw_gold*3"), sell(2, W + "raw_zinc*5"),
               sell(5, W + "raw_mithril*2", uses=6), sell(4, W + "lithite_shard*2", uses=6), sell(2, "rail*16"),
               buy("bread*6")]),
            R("brewer", "Dwarven Brewer", "Brasseur nain", "trader", "brew", "brew",
              ["barrel", "smoker", "cauldron", "water_cauldron", "brewing_stand", "campfire"],
              [sell(1, "bread*6", uses=16), sell(1, "cooked_mutton*4", uses=16), sell(1, "mushroom_stew"),
               sell(1, "honey_bottle*2"), sell(3, "potion:fire_resistance", uses=6), sell(4, "potion:strength", uses=6),
               buy("wheat*20"), buy("sweet_berries*20")]),
            R("gemcutter", "Dwarven Gemcutter", "Lapidaire nain", "trader", "carve", "carve",
              ["grindstone", "stonecutter", "amethyst_block", "budding_amethyst", "lectern", "chest"],
              [sell(1, "amethyst_shard*4"), sell(1, "lapis_lazuli*6"), sell(2, "quartz*8"), sell(2, "redstone*10"),
               sell(3, "gold_ingot*2"), sell(5, W + "lithite_shard*3", uses=6), buy("diamond", emeralds=3, uses=8),
               buy("raw_copper*12")]),
            R("guard", "Dwarven Guard", "Garde nain", "guard", "attack", "hammer", []),
        ],
        lines=[("Mind your step, surface-dweller.", "Attention où tu marches, homme de la surface."),
               ("The forges never sleep, and neither do I.", "Les forges ne dorment jamais, et moi non plus."),
               ("Trouble in the halls? Point me at it.", "Des ennuis dans les salles ? Montre-moi."),
               ("Stone remembers. So do we.", "La pierre se souvient. Nous aussi.")],
        text=("Short, broad and stubborn, the dwarves keep the Deep Dwarven City and the dwarven mines alive. Smiths "
              "ring their anvils, miners dig the rock faces, brewers stir their vats and gemcutters tap their stones: "
              "each one sells what it makes. Guards in horned helms keep the halls safe.",
              "Petits, larges et têtus, les nains font vivre la Cité naine des profondeurs et les mines naines. Les "
              "forgerons font chanter leurs enclumes, les mineurs creusent la roche, les brasseurs remuent leurs cuves "
              "et les lapidaires taillent leurs pierres : chacun vend ce qu'il fabrique. Des gardes au casque à "
              "cornes veillent sur les salles."),
    ),
    "sylvan": dict(
        en="Sylvan", fr="Sylvain", plural=("Sylvans", "Sylvains"), egg=((84, 152, 70), (220, 255, 240)), size=(0.6, 2.05),
        homes=["sylvan_palace", "giant_tree"],
        roles=[
            R("gardener", "Sylvan Gardener", "Jardinier sylvain", "worker", "tend", "tend",
              ["composter", "potted_*", "*_sapling", "flowering_azalea", "azalea", "*_leaves"],
              [sell(2, W + "glowwood_sapling", uses=6), sell(1, "cherry_sapling"), sell(1, "birch_sapling*2"),
               sell(1, "lily_of_the_valley*4"), sell(1, "glow_berries*6"), sell(1, "moss_block*6"),
               sell(4, "spore_blossom", uses=4), buy("bone_meal*24")]),
            R("herbalist", "Sylvan Herbalist", "Herboriste sylvain", "trader", "brew", "brew",
              ["brewing_stand", "cauldron", "water_cauldron", "lectern", "composter"],
              [sell(4, "potion:healing", uses=6), sell(5, "potion:regeneration", uses=6),
               sell(3, "potion:night_vision", uses=6), sell(4, "potion:swiftness", uses=6), sell(2, "golden_carrot*3"),
               sell(1, "honey_bottle*2"), buy("sweet_berries*24"), buy("glow_berries*16")]),
            R("woodwright", "Sylvan Woodwright", "Boisier sylvain", "worker", "carve", "carve",
              ["fletching_table", "crafting_table", "loom", "barrel", "chest", "stripped_*_log"],
              [sell(2, W + "glowwood_log*8"), sell(2, W + "glowwood_planks*24"), sell(1, "arrow*16", uses=16),
               sell(3, "bow", uses=6), sell(1, W + "glowwood_leaves*8"), sell(3, "crossbow", uses=4),
               buy("stick*32"), buy("string*12"), buy("feather*10")]),
            R("warden", "Sylvan Warden", "Gardien sylvain", "guard", "attack", "tend", []),
        ],
        lines=[("The trees told me you were coming.", "Les arbres m'ont dit que tu venais."),
               ("Walk softly. The roots are listening.", "Marche doucement. Les racines écoutent."),
               ("My arrows fly for the forest.", "Mes flèches volent pour la forêt."),
               ("Leave nothing but footprints.", "Ne laisse que des traces de pas.")],
        text=("Tall, slender and long-eared, the sylvans tend the Sylvan Palace and the Hollow Giant Tree. Gardeners "
              "kneel at their flower beds, herbalists brew healing potions, woodwrights carve glowwood: each sells "
              "the fruit of its craft. Wardens with longbows watch over them.",
              "Grands, élancés et aux longues oreilles, les sylvains prennent soin du Palais sylvain et de l'Arbre-monde "
              "creux. Les jardiniers s'agenouillent dans leurs massifs, les herboristes préparent des potions de soin, "
              "les boisiers taillent le bois-lueur : chacun vend le fruit de son art. Des gardiens armés d'arcs longs "
              "veillent sur eux."),
    ),
    "clockwork_citizen": dict(
        en="Clockwork Citizen", fr="Citoyen mécanique", plural=("Clockwork Citizens", "Citoyens mécaniques"), egg=((190, 150, 70), (232, 220, 190)), size=(0.7, 1.95),
        homes=["clockwork_citadel"],
        roles=[
            R("gearwright", "Clockwork Gearwright", "Engrenier mécanique", "trader", "tinker", "tinker",
              ["smithing_table", "anvil", "crafting_table", "brasshaven:wall_cog", "brasshaven:gear_panel"],
              [sell(2, W + "brass_gear*2"), sell(3, W + "brass_ingot*4"), sell(1, W + "brass_nugget*9"),
               sell(1, W + "wall_cog*4"), sell(1, W + "gear_panel*4"), sell(2, W + "brass_plating*8"),
               buy("copper_ingot*10"), buy(W + "raw_zinc*8")]),
            R("mechanic", "Clockwork Mechanic", "Mécanicien mécanique", "worker", "tinker", "tinker",
              ["piston", "sticky_piston", "observer", "dispenser", "redstone_lamp", "blast_furnace", "furnace",
               "brasshaven:copper_pipes", "brasshaven:valve_wheel", "brasshaven:pressure_gauge", "brasshaven:*_lamp"],
              [sell(1, "redstone*10"), sell(2, "piston*2"), sell(3, "sticky_piston*2"), sell(2, "observer"),
               sell(1, W + "copper_pipe*4"), sell(2, W + "valve_wheel"), sell(3, W + "pressure_gauge", uses=6),
               sell(2, W + "rivet*16"), buy("iron_ingot*5")]),
            R("chronometrist", "Clockwork Chronometrist", "Chronométreur mécanique", "trader", "wind", "wind",
              ["lectern", "cartography_table", "bell", "brasshaven:edison_lamp", "brasshaven:hanging_edison_lamp"],
              [sell(3, "clock"), sell(2, "compass"), sell(10, W + "pocket_watch", uses=3),
               sell(14, W + "structure_compass", uses=2, cost2=W + "map_fragment*4"), sell(2, W + "edison_lamp*2"),
               sell(5, W + "recall_scroll", uses=4), buy("gold_ingot*3"), buy(W + "map_fragment*2")]),
            R("sentinel", "Clockwork Sentinel", "Sentinelle mécanique", "guard", "attack", "tinker", []),
        ],
        lines=[("Tick. Tock. All is in order.", "Tic. Tac. Tout est en ordre."),
               ("Citizen, your gears appear to be in working condition.", "Citoyen, vos rouages semblent en état de marche."),
               ("Unauthorised disassembly is forbidden.", "Tout démontage non autorisé est interdit."),
               ("Patrol cycle 4 096. No anomalies.", "Cycle de patrouille 4 096. Aucune anomalie.")],
        text=("The wound-up townsfolk of the Clockwork Citadel: gearwrights sell cogs and brass, mechanics tinker with "
              "pistons and pipes, chronometrists wind their keys and sell clocks, compasses and pocket watches. "
              "Sentinels with piston fists keep the peace.",
              "Les habitants remontés de la Citadelle d'horlogerie : les engreniers vendent rouages et laiton, les "
              "mécaniciens bricolent pistons et tuyaux, les chronométreurs remontent leur clé et vendent horloges, "
              "boussoles et montres de poche. Des sentinelles aux poings-pistons font régner l'ordre."),
    ),
    "monk": dict(
        en="Monk", fr="Moine", plural=("Monks", "Moines"), egg=((118, 80, 52), (200, 170, 110)), size=(0.6, 1.95),
        homes=["mountain_monastery"],
        roles=[
            R("scribe", "Monk Scribe", "Copiste du monastère", "trader", "scribe", "scribe",
              ["lectern", "bookshelf", "chiseled_bookshelf", "cartography_table"],
              [sell(1, "paper*16", uses=16), sell(2, "book*2"), sell(3, "writable_book"), sell(1, "lantern"),
               sell(4, W + "map_fragment", uses=6), sell(5, "experience_bottle*3", uses=6), buy("paper*24"),
               buy("feather*12"), buy("ink_sac*5")]),
            R("healer", "Monk Healer", "Guérisseur du monastère", "trader", "brew", "brew",
              ["brewing_stand", "cauldron", "water_cauldron", "*candle", "lectern"],
              [sell(4, "potion:healing", uses=6), sell(5, "potion:regeneration", uses=6), sell(10, "golden_apple", uses=3),
               sell(2, "glistering_melon_slice*2"), sell(1, "honey_bottle*2"), buy("glow_berries*16"),
               buy("sweet_berries*20")]),
            R("cook", "Monk Cook", "Cuisinier du monastère", "worker", "tend", "tend",
              ["composter", "smoker", "barrel", "hay_block", "furnace", "cauldron", "campfire"],
              [sell(1, "bread*6", uses=16), sell(1, "baked_potato*8", uses=16), sell(1, "pumpkin_pie*3"),
               sell(1, "cookie*12"), sell(1, "beetroot_soup"), buy("wheat*20"), buy("potato*26"), buy("carrot*22")]),
            R("warden", "Monk Warden", "Gardien du monastère", "guard", "attack", "scribe", []),
        ],
        lines=[("Peace be upon this mountain.", "Que la paix règne sur cette montagne."),
               ("The staff is for the wolves. Mostly.", "Le bâton est pour les loups. Surtout."),
               ("Breathe. The snow teaches patience.", "Respire. La neige enseigne la patience."),
               ("Our doors are open to the honest.", "Nos portes sont ouvertes aux gens honnêtes.")],
        text=("The brothers and sisters of the Mountain Monastery: scribes sell paper, books and map fragments, healers "
              "brew potions, cooks sell bread and pies. Wardens with iron-shod staves keep the wolves, and the worse, "
              "away.",
              "Les frères et sœurs du Monastère de montagne : les copistes vendent papier, livres et fragments de carte, "
              "les guérisseurs préparent des potions, les cuisiniers vendent pain et tartes. Des gardiens au bâton "
              "ferré tiennent à distance les loups, et pire encore."),
    ),
}

# ====================================================================== creatures
# id: names, egg colours, structures (for the docs), loot [(item, min, max, chance)], texts
CREATURES = {
    "bandit_marksman": dict(
        en="Bandit Marksman", fr="Tireur bandit", egg=((140, 36, 34), (204, 160, 72)),
        homes=["bandit_camp", "ruined_watchtower"],
        loot=[("arrow", 1, 4, None), ("leather", 0, 1, None), ("emerald", 1, 1, 0.3), ("gunpowder", 0, 2, None),
              (W + "map_fragment", 1, 1, 0.15)],
        manual=("A hooded archer who keeps its distance and shoots well-aimed arrows. Get close and it throws a brass "
                "smoke bomb at its feet (blindness), leaps back and starts again. Corner it: up close, it can only kick. "
                "Found in bandit camps and ruined watchtowers.",
                "Un archer encapuchonné qui garde ses distances et tire des flèches bien ajustées. Approche-toi et il "
                "jette une bombe fumigène de laiton à ses pieds (cécité), bondit en arrière et recommence. Coince-le : de "
                "près, il ne peut que donner des coups de pied. Dans les camps de bandits et les tours de guet en ruine."),
        wiki="Archer encapuchonné qui garde ses distances et vise juste. Si tu t'approches, bombe fumigène (cécité) et "
             "bond en arrière : coince-le contre un mur. Camps de bandits et tours de guet en ruine."),
    "sky_raider": dict(
        en="Sky Raider", fr="Pillard du ciel", egg=((104, 70, 44), (214, 196, 160)),
        homes=["sky_isles", "sky_island"],
        loot=[("feather", 1, 3, None), ("phantom_membrane", 0, 1, None), (W + "brass_nugget", 1, 4, None),
              (W + "brass_gear", 1, 1, 0.12)],
        manual=("A wind pirate on clockwork wings. It circles above you, shrieks, then dives to snatch you in its "
                "talons and carry you up before letting go. Hit it while it holds you and it drops you at once; sneak to "
                "break free. If its dive misses, it crashes and stays stunned: punish it. Found on the Sky Isles.",
                "Un pirate du vent aux ailes mécaniques. Il tourne au-dessus de toi, pousse un cri, puis plonge pour "
                "t'attraper dans ses serres et t'emporter avant de te lâcher. Frappe-le pendant qu'il te tient et il te "
                "lâche aussitôt ; accroupis-toi pour te libérer. S'il rate son piqué, il s'écrase, sonné : punis-le. "
                "Sur les îles célestes."),
        wiki="Pirate du vent aux ailes mécaniques : il crie, plonge, t'attrape dans ses serres et t'emporte avant de te "
             "lâcher. Frappe-le (ou accroupis-toi) pour te libérer ; s'il rate son piqué, il reste sonné au sol."),
    "barnacle_crab": dict(
        en="Barnacle Crab", fr="Crabe à bernacles", egg=((170, 70, 52), (226, 222, 210)),
        homes=["sunken_temple", "sunken_citadel", "galleon_wreck", "shipwreck_debris", "sunken_submarine"],
        loot=[("prismarine_shard", 0, 2, None), ("cod", 0, 1, None), (W + "pearl", 1, 1, 0.25),
              ("nautilus_shell", 1, 1, 0.06)],
        manual=("A crab crusted with barnacles that climbs the walls of sunken ruins. Its great claw gapes (a clear "
                "warning), then clamps shut: caught, you cannot move and take damage until you hit it. Badly hurt, it "
                "hides in its shell for a few seconds (arrows bounce off): wait it out. Found in sunken temples, "
                "citadels and wrecks.",
                "Un crabe couvert de bernacles qui grimpe aux murs des ruines englouties. Sa grande pince s'ouvre (un "
                "avertissement clair), puis se referme : attrapé, tu ne peux plus bouger et tu prends des dégâts jusqu'à "
                "ce que tu le frappes. Très blessé, il se cache dans sa carapace quelques secondes (les flèches "
                "rebondissent) : attends qu'il ressorte. Temples, citadelles et épaves englouties."),
        wiki="Crabe couvert de bernacles qui grimpe aux murs sous l'eau. Sa grande pince s'ouvre puis t'attrape : frappe-le "
             "pour te libérer. Très blessé, il se cache dans sa carapace. Temples, citadelles et épaves englouties."),
    "lantern_wisp": dict(
        en="Lantern Wisp", fr="Feu follet", egg=((70, 64, 62), (90, 210, 230)),
        homes=["forgotten_catacombs", "sand_hypogeum"],
        loot=[("glowstone_dust", 1, 2, None), ("candle", 0, 1, None), ("soul_torch", 1, 1, 0.3)],
        manual=("A flame trapped in an old iron lantern. It drinks the light: candles and campfires around it go out, "
                "and with each stolen flame it shines brighter and hits harder, then sends out waves of darkness. "
                "It shies away from a player holding a torch or a lantern. Kill it and every flame it stole comes back. "
                "Found in the catacombs and the sand tombs.",
                "Une flamme prisonnière d'une vieille lanterne de fer. Elle boit la lumière : les bougies et les feux de "
                "camp autour d'elle s'éteignent, et à chaque flamme volée elle brille plus fort et frappe plus dur, puis "
                "lance des vagues de ténèbres. Elle fuit un joueur qui tient une torche ou une lanterne. Tue-la et "
                "chaque flamme volée se rallume. Dans les catacombes et les tombeaux des sables."),
        wiki="Flamme prisonnière d'une lanterne : elle éteint bougies et feux de camp pour devenir plus forte, puis lance "
             "des vagues de ténèbres. Elle fuit les torches tenues en main ; morte, elle rallume tout ce qu'elle a volé."),
    "cinder_hound": dict(
        en="Cinder Hound", fr="Molosse de cendre", egg=((52, 50, 56), (255, 120, 30)),
        homes=["basalt_fortress", "lava_foundry", "chain_bridge"],
        loot=[("bone", 0, 2, None), ("magma_cream", 0, 1, None), ("blaze_powder", 1, 1, 0.25),
              (W + "ancient_ember", 1, 1, 0.1)],
        manual=("A hound of basalt and magma that hunts in packs. When it spots you it howls and the whole pack runs "
                "faster for a while. It crouches, then charges in a straight line and leaves a trail of fire behind it: "
                "step aside. Its bite sets you on fire. Found in the Nether fortresses, foundries and chain bridges.",
                "Un molosse de basalte et de magma qui chasse en meute. Quand il te repère, il hurle et toute la meute "
                "court plus vite un moment. Il se ramasse, puis charge en ligne droite en laissant une traînée de feu : "
                "écarte-toi. Sa morsure enflamme. Dans les forteresses, fonderies et ponts de chaînes du Nether."),
        wiki="Molosse de basalte et de magma qui chasse en meute : son hurlement accélère la meute, sa charge en ligne "
             "laisse une traînée de feu et sa morsure enflamme. Forteresses, fonderies et ponts du Nether."),
    "rift_sentinel": dict(
        en="Rift Sentinel", fr="Sentinelle de la faille", egg=((34, 26, 48), (220, 110, 255)),
        homes=["end_archive", "void_observatory", "void_ship", "chorus_garden"],
        loot=[("ender_pearl", 0, 1, None), ("popped_chorus_fruit", 0, 2, None), (W + "void_shard", 1, 1, 0.25)],
        manual=("A floating obsidian obelisk with a single violet eye. Its rune tablets lock in front of the eye while a "
                "dotted line points at you: then the beam hits and drags you toward it, so never fight it on a ledge. "
                "Stay out of the line of sight to dodge. Hit it a few times and it blinks away. Found in the End "
                "archives, observatories, wrecks and gardens.",
                "Un obélisque d'obsidienne flottant à l'œil violet unique. Ses tablettes runiques se placent devant "
                "l'œil pendant qu'une ligne pointillée te vise : puis le rayon frappe et t'attire vers lui, alors ne le "
                "combats jamais au bord du vide. Sors de sa ligne de vue pour l'esquiver. Frappe-le quelques fois et il "
                "se téléporte. Dans les archives, observatoires, épaves et jardins de l'End."),
        wiki="Obélisque flottant de l'End : une ligne pointillée te vise, puis son rayon frappe et t'attire vers lui (gare "
             "au vide !). Casse sa ligne de vue pour esquiver ; touché plusieurs fois, il se téléporte."),
    "frozen_huscarl": dict(
        en="Frozen Huscarl", fr="Huscarl gelé", egg=((126, 132, 142), (150, 214, 244)),
        homes=["glacier_hall"],
        loot=[("iron_nugget", 1, 3, None), ("snowball", 0, 2, None), ("packed_ice", 1, 1, 0.25),
              ("blue_ice", 1, 1, 0.08)],
        manual=("A dead house-guard frozen at his post, a round shield on his arm and a frost axe in his fist. Blows from "
                "the front glance off the shield: circle round him and hit his back or sides, or split his guard with an "
                "axe (he reels for a few seconds). He raises his axe high before chopping, draws the shield to his chest "
                "before punching with it, and turns away with the axe out behind him before a wide freezing sweep. Found "
                "in the Glacier Hall.",
                "Un garde de la maison mort et gelé à son poste, un bouclier rond au bras et une hache de givre au poing. "
                "Les coups de face glissent sur le bouclier : tourne autour de lui pour frapper son dos ou ses flancs, ou "
                "brise sa garde d'un coup de hache (il chancelle quelques secondes). Il lève sa hache bien haut avant de "
                "frapper, ramène le bouclier contre lui avant de cogner avec, et se détourne la hache tendue derrière lui "
                "avant un large coup glacial. Dans la Halle glaciaire."),
        wiki="Garde gelé au bouclier rond : les coups de face glissent dessus, frappe-le de côté ou dans le dos, ou brise "
             "sa garde à la hache. Coup de hache, coup de bouclier et large balayage glacial. Halle glaciaire."),
    "magma_sentry": dict(
        en="Magma-forged Sentry", fr="Sentinelle de magma", egg=((46, 42, 48), (255, 118, 26)),
        homes=["caldera_ringwall"],
        loot=[("iron_nugget", 1, 3, None), ("magma_cream", 0, 1, None), (W + "orichalcum_nugget", 1, 2, 0.3),
              (W + "ancient_ember", 1, 1, 0.08)],
        manual=("A suit of blackstone plate with a molten heart, standing guard with a halberd taller than itself. It keeps "
                "its distance: it levels the halberd and draws it back, then thrusts four blocks out; it raises it high "
                "over its helm, then brings it down and a line of fire runs along the ground in front of it (step off "
                "the line). Get too close and it shoves you away with the haft. Immune to fire. Found on the Caldera "
                "Ringwall.",
                "Une armure de pierre noire au cœur de magma, qui monte la garde avec une hallebarde plus haute qu'elle. "
                "Elle garde ses distances : elle abaisse la hallebarde et la ramène en arrière, puis frappe d'estoc à "
                "quatre blocs ; elle la lève au-dessus de son heaume, puis l'abat et une ligne de feu court au sol devant "
                "elle (sors de la ligne). Approche-toi trop et elle te repousse d'un coup de hampe. Insensible au feu. "
                "Sur le Rempart de la caldeira."),
        wiki="Armure de pierre noire au cœur de magma armée d'une hallebarde : estoc à quatre blocs, coup vertical qui "
             "ouvre une ligne de feu au sol, coup de hampe de près. Insensible au feu. Rempart de la caldeira."),
    "oathbound_statue": dict(
        en="Oathbound Statue-Knight", fr="Chevalier-statue du serment", egg=((150, 148, 140), (255, 196, 84)),
        homes=["kneeling_gate"],
        loot=[("cobblestone", 1, 3, None), ("gold_nugget", 1, 3, None), (W + "marble", 1, 2, 0.3),
              (W + "lithite_shard", 1, 1, 0.15)],
        manual=("A stone knight kneeling on its sword, bound by an old oath to guard the gate. While it sleeps, blows "
                "barely scratch it; come within a few steps (or strike it) and its cracks light up with gold as it rises. "
                "It is slow but hits very hard: it raises its greatsword high before a crushing blow that shakes the "
                "ground around, swings it far out to the side before a wide sweep, and levels the point at its hip "
                "before striding forward four blocks. Found at the Kneeling Gate.",
                "Un chevalier de pierre agenouillé sur son épée, lié par un vieux serment à la garde de la porte. Tant "
                "qu'il dort, les coups l'égratignent à peine ; approche-toi à quelques pas (ou frappe-le) et ses fissures "
                "s'illuminent d'or tandis qu'il se relève. Il est lent mais frappe très fort : il lève son espadon bien "
                "haut avant un coup écrasant qui ébranle le sol autour, l'écarte loin sur le côté avant un large balayage, "
                "et pointe la lame à la hanche avant de foncer de quatre blocs. À la Porte agenouillée."),
        wiki="Chevalier de pierre agenouillé qui s'éveille quand on approche (fissures dorées). Lent : coup écrasant qui "
             "ébranle le sol, large balayage et charge de quatre blocs pointe en avant. Porte agenouillée."),
    "tide_wraith": dict(
        en="Tide Wraith", fr="Spectre des marées", egg=((58, 132, 128), (196, 250, 236)),
        homes=["tidal_abbey"],
        loot=[("prismarine_crystals", 0, 2, None), ("kelp", 0, 2, None), (W + "pearl", 1, 1, 0.15),
              ("nautilus_shell", 1, 1, 0.04)],
        manual=("A drowned sailor's ghost floating over the flooded abbey, a gaff and chain round its wrist. It glides "
                "through water as easily as air, and while it is in water arrows and blows pass through it: fight it on "
                "dry stone. It rakes with its claws; it spreads both arms and gapes before lunging to hook you, then drags "
                "you toward the nearest water (hit it to break free). It can sink into water and rise again right behind "
                "you. Found in the Tidal Abbey.",
                "Le fantôme d'un marin noyé qui flotte au-dessus de l'abbaye inondée, une gaffe et une chaîne au poignet. "
                "Il glisse dans l'eau aussi bien que dans l'air, et tant qu'il est dans l'eau flèches et coups le "
                "traversent : combats-le sur la pierre sèche. Il griffe ; il écarte les bras en ouvrant la mâchoire avant "
                "de bondir pour t'accrocher, puis t'entraîne vers l'eau la plus proche (frappe-le pour te libérer). Il "
                "peut s'enfoncer dans l'eau et resurgir juste derrière toi. Dans l'Abbaye des marées."),
        wiki="Fantôme de marin noyé : dans l'eau, les coups le traversent. Griffes, harpon qui t'accroche et t'entraîne "
             "vers l'eau (frappe-le pour te libérer), plongée et retour dans ton dos. Abbaye des marées."),
    "bell_monk": dict(
        en="Bell Monk", fr="Moine des cloches", egg=((124, 118, 108), (196, 138, 58)),
        homes=["pilgrims_ascent"],
        loot=[("paper", 0, 2, None), ("candle", 0, 1, None), (W + "brass_nugget", 1, 3, None),
              ("bell", 1, 1, 0.03)],
        manual=("A blindfolded monk under a vow of silence who lets his bells speak. He lifts his handbell and holds it "
                "trembling, then strikes: a ring of sound runs out along the ground; jump over it as it reaches you. "
                "Up close he swings the bell at your head. When he raises it over his cowl with both hands and shakes it "
                "harder and harder, get away or cover your ears: the knell blinds and pushes back everyone around. "
                "Found on Pilgrim's Ascent.",
                "Un moine aux yeux bandés, tenu au silence, qui laisse parler ses cloches. Il lève sa clochette et la "
                "tient tremblante, puis frappe : un anneau de son court au sol ; saute par-dessus quand il t'atteint. De "
                "près, il te balance la cloche à la tête. Quand il la lève au-dessus de sa capuche à deux mains en la "
                "secouant de plus en plus fort, éloigne-toi : le glas aveugle et repousse tout le monde alentour. Sur "
                "l'Ascension du pèlerin."),
        wiki="Moine aux yeux bandés : sa cloche lance un anneau de son au sol (saute par-dessus), cogne de près, et son "
             "glas aveugle et repousse tout le monde autour. Ascension du pèlerin."),
    "void_acolyte": dict(
        en="Void Acolyte", fr="Acolyte du vide", egg=((40, 28, 56), (190, 110, 255)),
        homes=["shattered_halo"],
        loot=[("ender_pearl", 0, 1, None), ("amethyst_shard", 0, 2, None), (W + "void_shard", 1, 1, 0.2)],
        manual=("A masked cultist of the Shattered Halo, a broken halo floating behind its head. It draws an orb of void "
                "light to its chest and lets it swell, then throws it: the orb drifts after you and lifts you off the "
                "ground; dodge it or break the line with a block. It blinks a few blocks away to flank you: the spot it "
                "will land on flickers first. Corner it and it stabs with its dagger. Found on the Shattered Halo.",
                "Un adepte masqué du Halo brisé, un halo cassé flottant derrière sa tête. Il ramène une orbe de lumière "
                "du vide contre lui et la laisse grossir, puis la lance : l'orbe te suit et te soulève du sol ; esquive-la "
                "ou coupe sa route avec un bloc. Il se téléporte à quelques blocs pour te prendre de flanc : l'endroit où "
                "il va apparaître scintille d'abord. Coincé, il frappe de sa dague. Sur le Halo brisé."),
        wiki="Adepte masqué au halo brisé : orbe du vide qui te suit et te soulève, téléportation de flanc (le point "
             "d'arrivée scintille d'abord), coup de dague de près. Halo brisé."),
    # ---- second pack: the creatures of the colossal structures that had none of their own
    "sluice_drowned": dict(
        en="Sluice Drowned", fr="Noyé de l'écluse", egg=((64, 80, 96), (176, 146, 58)),
        homes=["great_aqueduct"],
        loot=[("rotten_flesh", 0, 2, None), ("copper_ingot", 0, 1, None), ("string", 0, 2, None),
              ("tripwire_hook", 1, 1, 0.12)],
        manual=("The drowned lock-keeper of the Great Aqueduct, in a sou'wester and waders, a boat-hook taller than "
                "himself in his fist. He raises the hook and whirls it over his hat before casting it at you from up to "
                "seven blocks away: it hooks you and hauls you to his feet, so break his line of sight or step aside. "
                "Up close he draws the pole back along his arm before jabbing with the spike, and swings it out wide "
                "behind him before a low sweep that knocks you off your feet. He swims and breathes under water. Found "
                "in the Great Aqueduct.",
                "Le gardien d'écluse noyé du Grand Aqueduc, en suroît et cuissardes, une gaffe plus haute que lui au "
                "poing. Il lève la gaffe et la fait tournoyer au-dessus de son chapeau avant de la lancer sur toi jusqu'à "
                "sept blocs : elle t'accroche et te ramène à ses pieds, alors coupe sa ligne de vue ou écarte-toi. De "
                "près, il ramène la perche le long de son bras avant de piquer de la pointe, et la balance loin derrière "
                "lui avant un balayage bas qui te fauche. Il nage et respire sous l'eau. Dans le Grand Aqueduc."),
        wiki="Gardien d'écluse noyé armé d'une gaffe : il la fait tournoyer puis la lance à sept blocs pour t'attirer à "
             "lui, pique de la pointe et fauche bas. Nage et respire sous l'eau. Grand Aqueduc."),
    "turbine_automaton": dict(
        en="Turbine Automaton", fr="Automate à turbine", egg=((186, 112, 58), (78, 156, 138)),
        homes=["drowned_dam"],
        loot=[(W + "brass_nugget", 1, 3, None), ("copper_ingot", 0, 2, None), ("redstone", 0, 2, None),
              (W + "brass_gear", 1, 1, 0.2)],
        manual=("A barrel-chested maintenance machine of the drowned dam, green with verdigris, a rotor turning in its "
                "chest. When it crouches and its rotor spins faster and faster while steam screams from its stacks, it "
                "is about to dash in a straight line: step out of the way and it skids past. Up close it raises both "
                "paddle hands over its head before slamming them down, and sinks onto its haunches with arms thrown wide "
                "before venting a scalding cloud around it. When it breaks, its boiler bursts: do not stand next to it. "
                "Found in the Dam of the Drowned Valley.",
                "Une machine d'entretien trapue du barrage noyé, verte de vert-de-gris, un rotor tournant dans la "
                "poitrine. Quand elle s'accroupit et que son rotor tourne de plus en plus vite pendant que la vapeur "
                "hurle de ses cheminées, elle va foncer en ligne droite : écarte-toi et elle passe en dérapant. De près, "
                "elle lève ses deux pales au-dessus de sa tête avant de les abattre, et s'affaisse bras écartés avant "
                "de lâcher un nuage brûlant autour d'elle. Quand elle se brise, sa chaudière éclate : ne reste pas à "
                "côté. Dans le Barrage de la vallée noyée."),
        wiki="Machine à turbine du barrage : son rotor s'emballe avant une charge en ligne droite, coup double des "
             "pales, nuage de vapeur brûlante ; sa chaudière éclate à sa mort. Barrage de la vallée noyée."),
    "bog_leech_man": dict(
        en="Bog Leech-Man", fr="Homme-sangsue", egg=((66, 72, 44), (176, 70, 84)),
        homes=["mire_stilt_city"],
        loot=[("slime_ball", 0, 2, None), ("rotten_flesh", 0, 1, None), ("lily_pad", 0, 1, None),
              ("spider_eye", 1, 1, 0.2)],
        manual=("A hunched thing of the bog with a round lamprey mouth for a face, lurking in the water under the "
                "stilt-city. It sinks low on its frog legs and flares its mouth before it leaps, from the water or the "
                "boards, up to eight blocks: if it reaches you it latches on and drinks your blood, healing itself, until "
                "you hit it twice or it has drunk for three seconds. It draws its claw back over its shoulder before a "
                "raking swipe. It swims fast; fight it away from the water. Found in the Mire Stilt-City.",
                "Une créature voûtée des tourbières, une bouche ronde de lamproie en guise de visage, tapie dans l'eau "
                "sous la cité sur pilotis. Elle se ramasse sur ses pattes de grenouille et ouvre grand la bouche avant "
                "de bondir, de l'eau ou des planches, jusqu'à huit blocs : si elle t'atteint, elle s'accroche et boit "
                "ton sang en se soignant, jusqu'à ce que tu la frappes deux fois ou qu'elle ait bu trois secondes. Elle "
                "ramène sa griffe par-dessus l'épaule avant de lacérer. Elle nage vite : combats-la loin de l'eau. Dans "
                "la Cité des marais sur pilotis."),
        wiki="Créature des tourbières à bouche de lamproie : elle bondit hors de l'eau, s'accroche et boit ton sang "
             "(frappe-la deux fois pour t'en défaire), lacère de ses griffes. Cité des marais sur pilotis."),
    "abyss_crawler": dict(
        en="Abyss Crawler", fr="Rampant de l'abîme", egg=((214, 210, 200), (90, 170, 255)),
        homes=["inverted_spire"],
        loot=[("string", 0, 2, None), ("bone", 0, 2, None), ("ink_sac", 0, 1, None), ("echo_shard", 1, 1, 0.03)],
        manual=("A long, pale, eyeless crawler on six spindly legs, blue lights along its spine. It walks up walls and "
                "waits clinging under ceilings; when you pass beneath it curls up tight and grit trickles down, then it "
                "drops onto you: look up, and step aside when the grit falls. On the ground it rears and lifts its "
                "forelegs before raking you, and rears up high while its four-way jaw peels open before a screech that "
                "blinds you with darkness. Found in the Inverted Spire.",
                "Un long rampant pâle et aveugle sur six pattes grêles, des lueurs bleues le long de l'échine. Il marche "
                "sur les murs et attend accroché sous les plafonds ; quand tu passes dessous, il se roule en boule et du "
                "gravier tombe, puis il se laisse choir sur toi : lève les yeux et écarte-toi quand le gravier tombe. Au "
                "sol, il se cabre et lève ses pattes avant de te lacérer, et se dresse pendant que sa mâchoire en quatre "
                "s'ouvre avant un cri qui t'aveugle de ténèbres. Dans la Flèche inversée."),
        wiki="Rampant pâle et aveugle qui marche sur les murs et se laisse tomber des plafonds (du gravier tombe "
             "d'abord) ; lacère de ses pattes et pousse un cri qui plonge dans les ténèbres. Flèche inversée."),
    "rust_mite_mother": dict(
        en="Rust Mite Swarm-Mother", fr="Mère des mites de rouille", egg=((156, 78, 38), (255, 140, 50)),
        homes=["fallen_colossus"],
        loot=[("iron_nugget", 1, 4, None), ("copper_ingot", 0, 1, None), (W + "rust_rock", 1, 2, 0.3),
              ("raw_iron", 1, 1, 0.1)],
        manual=("A tick with an enormous swollen abdomen of flaking rust, nesting in the Fallen Colossus. Its bite "
                "corrodes your armour. Its abdomen pumps three times while it rears before it spits a gobbet of rust "
                "that slows and weakens you. Once, it plants its legs while its abdomen swells and shudders, its pores "
                "glowing: kill it fast or step back, for its brood bursts out, two or three tiny rust mites. Found in "
                "the Fallen Colossus.",
                "Une tique à l'énorme abdomen gonflé de rouille écailleuse, nichée dans le Colosse abattu. Sa morsure "
                "ronge ton armure. Son abdomen palpite trois fois pendant qu'elle se cabre avant de cracher un paquet de "
                "rouille qui ralentit et affaiblit. Une fois, elle se plante sur ses pattes pendant que son abdomen "
                "enfle et tremble, ses pores luisants : tue-la vite ou recule, car sa couvée éclate, deux ou trois "
                "minuscules mites de rouille. Dans le Colosse abattu."),
        wiki="Tique de rouille au gros abdomen : morsure qui ronge l'armure, crachat de rouille qui ralentit, et une "
             "fois sa couvée éclate en deux ou trois mites. Colosse abattu."),
    "rust_mite": dict(
        en="Rust Mite", fr="Mite de rouille", egg=((206, 120, 62), (62, 56, 56)),
        homes=["fallen_colossus"],
        loot=[("iron_nugget", 0, 1, None)],
        manual=("The brood of the Rust Mite Swarm-Mother: a flake of rust on six needle legs. Tiny, fast and frail; it "
                "rears and spreads its mandibles before it bites, and crumbles away after a minute. Found in the Fallen "
                "Colossus.",
                "La couvée de la Mère des mites de rouille : un éclat de rouille sur six pattes en aiguille. Minuscule, "
                "rapide et fragile ; elle se cabre et écarte ses mandibules avant de mordre, et s'effrite au bout d'une "
                "minute. Dans le Colosse abattu."),
        wiki="Couvée minuscule de la Mère des mites de rouille : rapide, fragile, mord et s'effrite au bout d'une "
             "minute. Colosse abattu."),
    "boiler_gunner": dict(
        en="Boiler Gunner", fr="Canonnier-chaudière", egg=((66, 64, 68), (190, 150, 70)),
        homes=["walking_fortress"],
        loot=[("gunpowder", 1, 3, None), ("coal", 0, 2, None), (W + "brass_nugget", 1, 3, None),
              (W + "brass_gear", 1, 1, 0.15)],
        manual=("A walking boiler whose right arm is a flak cannon, left aboard the Walking Fortress Wreck. It is slow "
                "but shoots from far: it plants its feet and raises the cannon while the gauge on its head climbs into "
                "the red and a trail of smoke marks where it aims; the aim locks a quarter of a second before the shot, "
                "and the shell bursts in a cloud of flak there: keep moving. Get close and it swings its firebox door "
                "open before belching fire, or lifts a foot high before stamping a shockwave. Found in the Walking "
                "Fortress Wreck.",
                "Une chaudière ambulante dont le bras droit est un canon de DCA, restée à bord de l'épave de la "
                "Forteresse marchante. Lente mais elle tire de loin : elle se campe et lève le canon pendant que la "
                "jauge de sa tête monte dans le rouge et qu'une traînée de fumée marque sa visée ; la visée se fige un "
                "quart de seconde avant le tir et l'obus éclate là en une gerbe d'éclats : reste en mouvement. De près, "
                "elle ouvre la porte de son foyer avant de cracher du feu, ou lève un pied bien haut avant de frapper "
                "le sol d'une onde de choc. Dans l'épave de la Forteresse marchante."),
        wiki="Chaudière ambulante au bras-canon : visée signalée par la fumée puis obus à éclats, jet de feu de son "
             "foyer et coup de pied qui ébranle le sol. Lente. Forteresse marchante."),
}

FOLK_IDS = list(PEOPLES)
CREATURE_IDS = list(CREATURES)
ALL_IDS = FOLK_IDS + CREATURE_IDS
ROLE_ORDER = {pid: [r["id"] for r in p["roles"]] for pid, p in PEOPLES.items()}
EGGS = {**{k: v["egg"] for k, v in PEOPLES.items()}, **{k: v["egg"] for k, v in CREATURES.items()}}

MESSAGES = {
    "folk.brasshaven.refuse": ("<%s> I don't trade with brutes. Come back when you've cooled down.",
                               "<%s> Je ne commerce pas avec les brutes. Reviens quand tu seras calmé."),
    "folk.brasshaven.says": ("<%s> %s", "<%s> %s"),
}


def role(people, rid):
    return next(r for r in PEOPLES[people]["roles"] if r["id"] == rid)


# ====================================================================== content.py, gen_assets.py
def register_content(items, entities, spawn_eggs):
    for pid, p in PEOPLES.items():
        entities[pid] = (p["en"], p["fr"])
    for cid, c in CREATURES.items():
        entities[cid] = (c["en"], c["fr"])
    for eid in ALL_IDS:
        if eid not in spawn_eggs:
            spawn_eggs.append(eid)


def lang():
    en, fr = {}, {}
    for pid, p in PEOPLES.items():
        for r in p["roles"]:
            en[f"entity.{NS}.{pid}.{r['id']}"], fr[f"entity.{NS}.{pid}.{r['id']}"] = r["en"], r["fr"]
        for i, (le, lf) in enumerate(p["lines"]):
            en[f"folk.{NS}.{pid}.line{i}"], fr[f"folk.{NS}.{pid}.line{i}"] = le, lf
    for key, (e, f) in MESSAGES.items():
        en[key], fr[key] = e, f
    return en, fr


# ====================================================================== gen_data.py: loot
def loot(write):
    def pool(name, lo, hi, chance):
        e = {"type": "minecraft:item", "name": name if ":" in name else f"minecraft:{name}"}
        fns = []
        if (lo, hi) != (1, 1):
            fns.append({"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi},
                        "add": False})
        fns.append({"function": "minecraft:enchanted_count_increase", "enchantment": "minecraft:looting",
                    "count": {"type": "minecraft:uniform", "min": 0, "max": 1}})
        e["functions"] = fns
        p = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [e]}
        if chance is not None:
            p["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance}]
        return p
    for cid, c in CREATURES.items():
        write(f"{NS}/loot_table/entities/{cid}.json", {
            "type": "minecraft:entity", "pools": [pool(*e) for e in c["loot"]],
            "random_sequence": f"{NS}:entities/{cid}"})
    for pid in PEOPLES:
        # residents drop nothing (like villagers): there is no reason to hunt them
        write(f"{NS}/loot_table/entities/{pid}.json", {"type": "minecraft:entity", "pools": [],
                                                       "random_sequence": f"{NS}:entities/{pid}"})


# ====================================================================== gen_java.py: GeneratedFolk
def _action_index(people, name):
    import importlib
    mod = importlib.import_module(f"wf.mobs.{people}")
    if list(mod.ROLES) != ROLE_ORDER[people]:
        raise ValueError(f"{people}: model roles {mod.ROLES} != denizens roles {ROLE_ORDER[people]}")
    m = mod.build()
    names = [a.name for a in m.actions]
    if name not in names:
        raise ValueError(f"{people}: no '{name}' animation in its model ({names})")
    return names.index(name)


def _jstr(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def java():
    out = ["package com.brasshaven.generated;", "", "import java.util.List;", "import java.util.Map;", "",
           "/** GENERATED by tools/gen_java.py from tools/wf/denizens.py: the peoples, their roles and trades. Do not edit. */",
           "public final class GeneratedFolk {",
           "    public enum Kind { TRADER, WORKER, GUARD }", "",
           "    /** A trade: costA (+ costB) for result; item ids, or \"potion:<id>\" for a potion. */",
           "    public record Trade(String costA, int countA, String costB, int countB, String result, int countR, "
           "int maxUses, int xp) {}", "",
           "    /** A role: its work animation index (MobAnims) and style (effects), the job blocks it walks to. */",
           "    public record Role(String id, Kind kind, int workAction, String style, List<String> jobs, List<Trade> trades) {}",
           "",
           "    public record People(String id, List<Role> roles, int greetAction, int attackAction, int lines) {",
           "        public Role role(int i) {",
           "            return roles.get(Math.floorMod(i, roles.size()));",
           "        }",
           "",
           "        public int indexOf(String role) {",
           "            for (int i = 0; i < roles.size(); i++) {",
           "                if (roles.get(i).id().equals(role)) {",
           "                    return i;",
           "                }",
           "            }",
           "            return -1;",
           "        }",
           "    }", ""]
    names = []
    for pid, p in PEOPLES.items():
        roles = []
        for r in p["roles"]:
            trades = []
            for t in r["trades"]:
                a, b, res = t["a"], t["b"], t["r"]
                bj = _jstr(b[0]) if b else '""'
                trades.append(f"new Trade({_jstr(a[0])}, {a[1]}, {bj}, {b[1] if b else 0}, "
                              f"{_jstr(res[0])}, {res[1]}, {t['uses']}, {t['xp']})")
            jobs = ", ".join(_jstr(j if ":" in j or "*" in j else "minecraft:" + j) for j in r["jobs"])
            kind = r["kind"].upper()
            roles.append(f"                new Role({_jstr(r['id'])}, Kind.{kind}, {_action_index(pid, r['work'])}, "
                         f"{_jstr(r['style'])}, List.of({jobs}),\n                        List.of("
                         + (",\n                                ".join(trades)) + "))")
        const = pid.upper()
        names.append((pid, const))
        out.append(f"    public static final People {const} = new People({_jstr(pid)}, List.of(\n"
                   + ",\n".join(roles) + f"),\n            {_action_index(pid, 'greet')}, {_action_index(pid, 'attack')}, "
                   f"{len(p['lines'])});")
        out.append("")
    out.append("    public static final Map<String, People> PEOPLES = Map.of("
               + ", ".join(f"{_jstr(pid)}, {c}" for pid, c in names) + ");")
    out += ["", "    private GeneratedFolk() {}", "}", ""]
    return "\n".join(out)


# ====================================================================== guide.py: manual pages
CATEGORY = ("peoples", "minecraft:emerald", ("Peoples & creatures", "Peuples et créatures"))


def guide_pages():
    pages = [("peoples", "peoples", "minecraft:emerald", ("Living places", "Des lieux habités"), [
        ("The great places are not empty any more: dwarves, sylvans, clockwork citizens and monks live in them, and "
         "each hostile place has its own creature, with its own trick.",
         "Les grands lieux ne sont plus vides : nains, sylvains, citoyens mécaniques et moines y vivent, et chaque "
         "lieu hostile a sa propre créature, avec sa propre ruse."),
        ("Trading: right-click a resident to open the trading screen. Each trade has its stock; it comes back after a "
         "while. Guards do not trade: they answer with a few words.",
         "Commerce : clic droit sur un habitant pour ouvrir l'écran d'échange. Chaque offre a son stock, qui revient "
         "au bout d'un moment. Les gardes ne commercent pas : ils répondent quelques mots."),
        ("Guards attack the monsters that come near their home, and anyone who hurts a resident: hit one and the "
         "guards around turn on you, and nobody will trade with you for a few minutes.",
         "Les gardes attaquent les monstres qui s'approchent de chez eux, et quiconque blesse un habitant : frappe-en "
         "un et les gardes alentour se retournent contre toi, et plus personne ne commerce avec toi pendant quelques "
         "minutes."),
        ("Residents stay home, never despawn and heal slowly. They flee from monsters. No monster spawns on its own "
         "inside their homes.",
         "Les habitants restent chez eux, ne disparaissent jamais et guérissent lentement. Ils fuient les monstres. "
         "Aucun monstre n'apparaît de lui-même chez eux."),
    ], ["minecraft:emerald"])]
    for pid, p in PEOPLES.items():
        roles_en = ", ".join(r["en"].split(" ", 1)[1].lower() for r in p["roles"])
        roles_fr = ", ".join(r["fr"].split(" ", 1)[0].lower() for r in p["roles"])
        sells_en = "; ".join(f"{r['en'].split(' ', 1)[1].lower()}: {_trade_summary(r, 0)}"
                             for r in p["roles"] if r["trades"])
        sells_fr = " ; ".join(f"{r['fr'].split(' ', 1)[0].lower()} : {_trade_summary(r, 1)}"
                              for r in p["roles"] if r["trades"])
        pages.append((pid, "peoples", f"{W}{pid}_spawn_egg", p["plural"], [
            p["text"],
            (f"Roles: {roles_en}.", f"Rôles : {roles_fr}."),
            (f"They sell, among other things: {sells_en}.", f"Ils vendent entre autres : {sells_fr}."),
        ], [f"{W}{pid}_spawn_egg"]))
    for cid, c in CREATURES.items():
        pages.append((cid, "peoples", f"{W}{cid}_spawn_egg", (c["en"], c["fr"]), [c["manual"]], [f"{W}{cid}_spawn_egg"]))
    return pages


# a few words for the items the manual lists in trade summaries
ITEM_WORDS = {
    "iron_pickaxe": ("iron tools", "outils de fer"), "iron_chestplate": ("armour", "armures"),
    "brass_pickaxe": ("brass picks", "pioches de laiton"), "raw_iron": ("raw ores", "minerais bruts"),
    "lithite_shard": ("lithite", "lithite"), "torch": ("torches", "torches"),
    "bread": ("bread", "pain"), "potion:fire_resistance": ("potions", "potions"),
    "amethyst_shard": ("gems", "gemmes"), "gold_ingot": ("gold", "or"), "redstone": ("redstone", "redstone"),
    "glowwood_sapling": ("glowwood saplings", "pousses de bois-lueur"), "lily_of_the_valley": ("flowers", "fleurs"),
    "glow_berries": ("glow berries", "baies lumineuses"), "potion:healing": ("healing potions", "potions de soin"),
    "golden_carrot": ("golden carrots", "carottes dorées"), "glowwood_log": ("glowwood", "bois-lueur"),
    "bow": ("bows", "arcs"), "arrow": ("arrows", "flèches"), "brass_gear": ("gears", "rouages"),
    "brass_ingot": ("brass", "laiton"), "piston": ("pistons", "pistons"), "copper_pipe": ("pipes", "tuyaux"),
    "pocket_watch": ("pocket watches", "montres de poche"), "clock": ("clocks", "horloges"),
    "compass": ("compasses", "boussoles"), "paper": ("paper", "papier"), "book": ("books", "livres"),
    "map_fragment": ("map fragments", "fragments de carte"), "golden_apple": ("golden apples", "pommes dorées"),
    "pumpkin_pie": ("pies", "tartes"),
}


def _trade_summary(r, lang):
    words = []
    for t in r["trades"]:
        iid = t["r"][0].split(":", 1)[1] if not t["r"][0].startswith("potion:") else t["r"][0]
        w = ITEM_WORDS.get(iid)
        if w and w[lang] not in words:
            words.append(w[lang])
    return ", ".join(words[:4]) or ("emeralds" if lang == 0 else "émeraudes")


# ====================================================================== wiki (gen_wiki.py)
def wiki_folk_text(pid):
    p = PEOPLES[pid]
    roles = ", ".join(r["fr"] for r in p["roles"])
    return p["text"][1] + f" Rôles : {roles}."


def wiki_trades(pid):
    """[(role name fr, [(cost ids/counts, result id/count)])] for the wiki's trade tables."""
    out = []
    for r in PEOPLES[pid]["roles"]:
        if r["trades"]:
            out.append((r["fr"], [(t["a"], t["b"], t["r"]) for t in r["trades"]]))
    return out


# ====================================================================== structure templates
YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": 270.0}


def resident(bp, x, y, z, people, role_id, facing=None):
    """A resident of ``people`` with role ``role_id`` (template entity). It takes the spot it lands on as its home."""
    from . import nbt
    if role_id not in ROLE_ORDER[people]:
        raise ValueError(f"unknown {people} role {role_id}")
    bp.entity(x, y, z, {"id": f"{W}{people}", "Role": role_id, "PersistenceRequired": True,
                        "Rotation": nbt.List([nbt.Float(YAW.get(facing, 0.0)), nbt.Float(0.0)], nbt.Float)})
    log = getattr(bp, "npcs", None)
    if log is None:
        log = bp.npcs = []
    log.append(f"{people}:{role_id}")


def creature(bp, x, y, z, cid, yaw=0.0):
    """A hostile creature waiting in the template (it never despawns: the place keeps its guardians)."""
    from . import nbt
    if cid not in CREATURES:
        raise ValueError(f"unknown creature {cid}")
    bp.entity(x, y, z, {"id": f"{W}{cid}", "PersistenceRequired": True,
                        "Rotation": nbt.List([nbt.Float(float(yaw)), nbt.Float(0.0)], nbt.Float)})


def guards(bp, people, spots, ground=0, void_solid=False, role_id=None):
    """Guards of ``people`` on the nearest open floor to each of ``spots`` [(x, y, z)]."""
    from . import interior as I
    rid = role_id or next(r["id"] for r in PEOPLES[people]["roles"] if r["kind"] == "guard")
    for i, at in enumerate(spots):
        x, y, z = I.open_spot(bp, at, ground=ground, void_solid=void_solid)
        resident(bp, x, y, z, people, rid, facing=("north", "east", "south", "west")[i % 4])


def scatter(bp, cid, count, region=None, seed=0, ground=0, void_solid=False):
    """``count`` creatures on free floor cells of the rooms of ``region`` (interior.crowd)."""
    from . import interior as I
    if cid not in CREATURES:
        raise ValueError(f"unknown creature {cid}")
    return I.crowd(bp, {"id": f"{W}{cid}", "PersistenceRequired": True}, count, region=region, seed=seed,
                   ground=ground, void_solid=void_solid, label=cid)


# a villager profession whose job block a role takes in interior.populate(folk=...) (its first job block)
JOB_PROFESSION = {
    ("dwarf", "smith"): "armorer", ("dwarf", "miner"): "mason", ("dwarf", "brewer"): "butcher",
    ("dwarf", "gemcutter"): "mason",
    ("sylvan", "gardener"): "farmer", ("sylvan", "herbalist"): "cleric", ("sylvan", "woodwright"): "fletcher",
    ("clockwork_citizen", "gearwright"): "toolsmith", ("clockwork_citizen", "mechanic"): "armorer",
    ("clockwork_citizen", "chronometrist"): "cartographer",
    ("monk", "scribe"): "librarian", ("monk", "healer"): "cleric", ("monk", "cook"): "butcher",
}


def check_trades(known_items):
    """[messages] for trades naming items that do not exist (validate.py)."""
    out = []
    for pid, p in PEOPLES.items():
        for r in p["roles"]:
            if r["kind"] == "guard" and r["trades"]:
                out.append(f"{pid}/{r['id']}: guards do not trade")
            if r["kind"] != "guard" and not r["trades"]:
                out.append(f"{pid}/{r['id']}: no trades")
            for t in r["trades"]:
                for spec in (t["a"], t["b"], t["r"]):
                    if spec and not spec[0].startswith("potion:") and spec[0] not in known_items:
                        out.append(f"{pid}/{r['id']}: trade item {spec[0]} unknown")
                    if spec and not 1 <= spec[1] <= 64:
                        out.append(f"{pid}/{r['id']}: trade count {spec[1]} out of range")
    return out


# blocks of headroom each creature needs where it waits in a template
CREATURE_HEIGHT = {"bandit_marksman": 2, "sky_raider": 2, "barnacle_crab": 1, "lantern_wisp": 2, "cinder_hound": 1,
                   "rift_sentinel": 3, "frozen_huscarl": 2, "magma_sentry": 3, "oathbound_statue": 3,
                   "tide_wraith": 2, "bell_monk": 2, "void_acolyte": 2}
CREATURE_HEIGHT.update({"sluice_drowned": 2, "turbine_automaton": 2, "bog_leech_man": 2, "abyss_crawler": 1,
                        "rust_mite_mother": 1, "rust_mite": 1, "boiler_gunner": 3})
_AIR = ("minecraft:air", "minecraft:cave_air")
_BAD_FLOOR = ("magma_block", "campfire", "fire", "lava", "cactus", "leaves", "powder_snow", "mist_gate", "spawner",
              "boss_seal", "_bed", "chest", "barrel", "scaffolding", "_slab", "_stairs", "carpet", "_fence", "_wall")


def place_creatures(bp, creatures, seed=0, underground=False, ground=0):
    """Template creatures of a hostile place (StructureDef.creatures = [(creature id, count)]): each waits on a free,
    sturdy floor cell with headroom (in water for an underwater template), spread at least 6 blocks apart, never in a
    boss arena (24 blocks around a boss seal) nor next to a mist gate. Returns [(x, y, z, id)]."""
    import math
    import random
    from .blueprint import is_solid
    if not creatures:
        return []
    water = getattr(bp, "underwater", False)
    blocks = bp.blocks
    seals = [p for p, b in blocks.items() if b[0] == "brasshaven:boss_seal"]
    gates = [p for p, b in blocks.items() if b[0] == "brasshaven:mist_gate"]

    def free(p):
        b = blocks.get(p)
        if b is None:
            return water or (not underground and p[1] > ground)
        name = b[0]
        return name == "minecraft:water" if water else name in _AIR

    def floor(p):
        b = blocks.get(p)
        if b is None:
            return False
        short = b[0].split(":", 1)[1]
        return b[0] not in _AIR and b[0] != "minecraft:water" and is_solid(b[0]) and \
            not any(h in short for h in _BAD_FLOOR)

    floors = sorted(p for p, b in blocks.items() if floor(p))
    rng = random.Random(f"{bp.name}:creatures:{seed}")
    out = []
    for cid, count in creatures:
        if cid not in CREATURES:
            raise ValueError(f"unknown creature {cid}")
        tall = CREATURE_HEIGHT[cid]
        cells = []
        for (x, y, z) in floors:
            if all(free((x, y + 1 + k, z)) for k in range(tall + 1)) and \
                    all(math.dist((x, y, z), s) > 24 for s in seals) and \
                    all(math.dist((x, y, z), g) > 4 for g in gates):
                cells.append((x, y + 1, z))
        rng.shuffle(cells)
        placed = 0
        for c in cells:
            if placed >= count:
                break
            if any(math.dist(c, o[:3]) < 6 for o in out):
                continue
            creature(bp, *c, cid, yaw=rng.choice((0.0, 90.0, 180.0, 270.0)))
            out.append((*c, cid))
            placed += 1
    return out

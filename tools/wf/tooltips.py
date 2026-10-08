"""Tooltip conventions of every Brasshaven item (drawn by com.brasshaven.item.BrassTooltip).

    Name                                   (the item's name, vanilla colour / rarity)
    A one-line flavour, in italics         item.brasshaven.<id>.flavor          (this file, FLAVOR)
    What it does, in plain words           item.brasshaven.<id>.desc, .desc2, .desc3 (content.py, gadgets.py...)
    Numbers: ability, cooldown, mana,      computed in Java from the item itself (damage, cooldown, slot...)
    accessory slot, set bonus
    Hold Shift for details                 when the rules are longer than a few lines

Write the rules as short sentences that start with the action ("Use: ...", "Worn: ...", "Set: ..."), with the real
numbers. Flavour is one short sentence, no rules in it. Both languages go side by side (en, fr).
"""

NS = "brasshaven"

# the shapes of the boss weapon abilities (BossWeaponItem.Ability), with "radius" or "range" for their size
ABILITIES = {
    "wave": ("Shockwave", "Onde de choc", "radius"),
    "beam": ("Beam", "Rayon", "range"),
    "dash": ("Dash", "Ruée", "range"),
    "erupt": ("Eruptions", "Éruptions", "range"),
    "root": ("Grasping roots", "Racines", "radius"),
    "cloud": ("Poison cloud", "Nuage toxique", "radius"),
    "leap": ("Leap", "Bond", "radius"),
    "arc": ("Sweep", "Balayage", "radius"),
    "blink": ("Blink", "Clignement", "range"),
    "hook": ("Chain hook", "Chaîne-grappin", "range"),
    "shards": ("Halo shards", "Éclats de halo", "range"),
    "ward": ("Oath ward", "Garde du serment", "radius"),
    "rift": ("Molten rift", "Faille de magma", "range"),
    "breath": ("Frost breath", "Souffle de givre", "range"),
    "tempest": ("Tempest", "Tempête", "radius"),
    "tide": ("Breaking tide", "Lame de fond", "range"),
}
# BossWeaponItem flags, in bit order
ABILITY_EFFECTS = {
    "fire": ("sets foes ablaze", "enflamme"),
    "slow": ("slows", "ralentit"),
    "weak": ("weakens", "affaiblit"),
    "blind": ("blinds", "aveugle"),
    "poison": ("poisons", "empoisonne"),
    "lift": ("hurls foes into the air", "projette en l'air"),
    "lifesteal": ("heals you for 25% of the damage", "te soigne de 25 % des dégâts"),
}

STRINGS = {
    "shift": ("Hold Shift for details", "Maj enfoncée : plus de détails"),
    "set_bonus": ("Full set bonus (4 pieces):", "Bonus d'ensemble (4 pièces) :"),
    "cooldown": ("Cooldown: %s s", "Recharge : %s s"),
    "spell": ("Spell: %s mana · cooldown %s s", "Sort : %s mana · recharge %s s"),
    "ability": ("Ability (right-click): %s", "Capacité (clic droit) : %s"),
    "ability.stats": ("%s damage · %s · cooldown %s s", "%s dégâts · %s · recharge %s s"),
    "ability.radius": ("radius %s blocks", "rayon %s blocs"),
    "ability.range": ("range %s blocks", "portée %s blocs"),
    "ability.effects": ("Also %s.", "En plus : %s."),
    "ability.foes": ("Only hurts creatures, never players.", "Ne blesse que les créatures, jamais les joueurs."),
}

_REMEMBRANCE = ("The last memory of a fallen boss, still warm.", "Le dernier souvenir d'un boss vaincu, encore tiède.")

# id -> (english flavour, french flavour)
FLAVOR = {
    # accessories
    "brass_glider": ("Leather wings on a brass frame: the sky's own staircase.",
                     "Des ailes de cuir sur un cadre de laiton : l'escalier du ciel."),
    "magnet_ring": ("Lodestone set in brass. Loose things find their way home.",
                    "Une magnétite sertie de laiton. Ce qui traîne revient à toi."),
    "arcane_ring": ("A band of violet light that hums against the skin.",
                    "Un anneau de lumière violette qui vibre contre la peau."),
    "mana_amulet": ("A crystal that drinks the ambient magic.", "Un cristal qui boit la magie ambiante."),
    "pocket_watch": ("Wound once, it never loses a minute.", "Remontée une fois, elle ne perd jamais une minute."),
    # gadgets
    "brass_wrench": ("Every guild engineer swears by it, and at it.", "Tout ingénieur de la guilde jure par elle."),
    "grappling_hook": ("A claw, a chain and a lot of nerve.", "Une griffe, une chaîne et beaucoup de cran."),
    "rivet_gun": ("Built for hulls, used for everything else.", "Conçu pour les coques, utilisé pour tout le reste."),
    "airship_compass": ("Its needle dreams of mooring masts.", "Son aiguille rêve de mâts d'amarrage."),
    # explorer utilities
    "wayfarer_atlas": ("Every road you walk, inked as you go.", "Chaque route parcourue, encrée à mesure."),
    "wayfarer_manual": ("Dog-eared by generations of wayfarers.", "Corné par des générations de voyageurs."),
    "structure_compass": ("It points at old stones, not at the north.", "Elle montre les vieilles pierres, pas le nord."),
    "travel_backpack": ("Stitched leather, brass buckles, room for one more.",
                        "Cuir cousu, boucles de laiton, toujours de la place."),
    "explorer_backpack": ("Twice the room, the same straps.", "Deux fois plus de place, les mêmes sangles."),
    "recall_scroll": ("Read it aloud and the waystone answers.", "Lis-le à voix haute et la pierre répond."),
    "clockwork_heart": ("It ticks in your palm, waiting for a body.", "Il bat dans ta paume, en attente d'un corps."),
    "oblivion_vial": ("One sip and the lessons are gone.", "Une gorgée et les leçons s'effacent."),
    "builder_wand": ("For walls that would take all day.", "Pour les murs qui prendraient la journée."),
    "master_builder_wand": ("For walls that would take all week.", "Pour les murs qui prendraient la semaine."),
    "chisel": ("Stone remembers every shape it could have had.", "La pierre se souvient de toutes ses formes."),
    # magic
    "fire_staff": ("The tip never quite stops smoking.", "Le bout ne cesse jamais tout à fait de fumer."),
    "frost_staff": ("Frost creeps along the haft on summer days.", "Le givre gagne la hampe même en été."),
    "thunder_staff": ("Copper coils and a very short temper.", "Des bobines de cuivre et un caractère vif."),
    "healing_staff": ("Warm to the touch, like a hand on the shoulder.", "Tiède au toucher, comme une main sur l'épaule."),
    "levitation_wand": ("Light as a feather, and so is its target.", "Légère comme une plume, et sa cible aussi."),
    "ward_orb": ("A storm held in glass, facing outward.", "Une tempête dans du verre, tournée vers l'extérieur."),
    "steam_cane": ("A gentleman's cane with a boiler inside.", "Une canne de gentleman avec une chaudière dedans."),
    # weapons and tools
    "cartographer_blade": ("Engraved with the coastlines it has crossed.", "Gravée des côtes qu'elle a franchies."),
    "telluric_hammer": ("Lithite rings like a bell when it strikes.", "La lithite sonne comme une cloche à l'impact."),
    "frost_blade": ("Its edge is always rimed with ice.", "Son tranchant est toujours couvert de givre."),
    "boomerang": ("What goes around comes around.", "Tout ce qui part revient."),
    "ember_scythe": ("Forged in the Nether, homesick ever since.", "Forgée dans le Nether, nostalgique depuis."),
    "storm_staff": ("The clouds lean closer when it is raised.", "Les nuages s'approchent quand on le lève."),
    "void_spear": ("Its point is never quite where you see it.", "Sa pointe n'est jamais tout à fait là où on la voit."),
    "light_staff": ("A sunrise kept for the darkest corridors.", "Une aube gardée pour les couloirs les plus noirs."),
    "excavator_pickaxe": ("Why dig one block when you can dig nine?", "Pourquoi creuser un bloc quand on peut en creuser neuf ?"),
    "lumber_axe": ("The forest hears it coming.", "La forêt l'entend venir."),
    # ocean gear
    "diving_helmet": ("Brass, glass and a serpent's scales.", "Du laiton, du verre et des écailles de serpent."),
    "flippers": ("Ugly on land, glorious in the sea.", "Moches sur terre, glorieuses en mer."),
    # boss weapons
    "kings_trident": ("The drowned king's sceptre, still dripping.", "Le sceptre du roi englouti, encore ruisselant."),
    "bell_hammer": ("Every swing tolls for someone.", "Chaque coup sonne le glas de quelqu'un."),
    "forbidden_grimoire": ("Some pages read you back.", "Certaines pages te lisent en retour."),
    "pharaoh_flail": ("The desert obeys whoever holds it.", "Le désert obéit à qui le tient."),
    "jade_fang": ("Swift as the jungle's last hunter.", "Rapide comme le dernier chasseur de la jungle."),
    "rootmother_staff": ("Roots still curl around your fingers.", "Des racines s'enroulent encore autour des doigts."),
    "crone_ladle": ("Stirred a thousand foul brews.", "Elle a touillé mille breuvages infâmes."),
    "gryphon_lance": ("It remembers the wind under great wings.", "Elle se souvient du vent sous de grandes ailes."),
    "rune_fist": ("A colossus's knuckle, runes still glowing.", "Un poing de colosse aux runes encore vives."),
    "forge_king_hammer": ("Its head never cools.", "Sa tête ne refroidit jamais."),
    "crystal_fang": ("A spider's fang grown into a crystal blade.", "Un crochet d'araignée devenu lame de cristal."),
    "sculk_horn": ("It hears you before you blow it.", "Elle t'entend avant que tu souffles."),
    "ash_greatsword": ("Ash falls from it like snow.", "La cendre en tombe comme de la neige."),
    "golden_mace": ("Heavy with a king's greed.", "Lourde de la cupidité d'un roi."),
    "soul_scythe": ("It whispers the names it has reaped.", "Elle murmure les noms qu'elle a fauchés."),
    "void_greatblade": ("Cut from the dark between the stars.", "Taillée dans le noir entre les étoiles."),
    "clockmaker_pendulum": ("Tick. Tock. Your turn is over.", "Tic. Tac. Ton tour est passé."),
    "helmsman_anchor": ("It sank a fleet; now it sinks foes.", "Elle a coulé une flotte ; elle coule tes ennemis."),
    "sentinel_greatsword": ("Bronze that kept a gate for a thousand years.",
                            "Un bronze qui a gardé une porte mille ans."),
    "dune_king_crook": ("The dunes still bow to it.", "Les dunes s'inclinent encore devant lui."),
    "jailer_chain": ("No prisoner ever outran it.", "Aucun prisonnier ne l'a jamais distancée."),
    "halo_glaive": ("A crescent torn from a broken heaven.", "Un croissant arraché à un ciel brisé."),
    "gatekeeper_key": ("It opened the pass for a thousand years; now it opens skulls.",
                       "Elle a ouvert le col mille ans durant ; elle ouvre désormais les crânes."),
    "caldera_halberd": ("Forged in the throat of a dead volcano.", "Forgée dans la gorge d'un volcan éteint."),
    "jarl_axe": ("The winter he swore to bring never ended.", "L'hiver qu'il avait juré d'apporter n'a jamais fini."),
    "ascetic_staff": ("Its rings still ring with the storm he prayed to.", "Ses anneaux tintent encore de l'orage qu'il priait."),
    "abbess_crozier": ("She led her flock into the sea; the sea still follows her staff.",
                       "Elle a mené son troupeau dans la mer ; la mer suit encore sa crosse."),
}

# armour sets: one flavour per set prefix (all four pieces)
SET_FLAVOR = {
    "explorer": ("Worn soft by a hundred roads.", "Usée par cent routes."),
    "ember": ("Still glowing from the Nether's forges.", "Encore rougeoyante des forges du Nether."),
    "void": ("It weighs nothing, and neither do you.", "Elle ne pèse rien, et toi non plus."),
    "brass": ("Polished by guild apprentices every morning.", "Astiquée chaque matin par les apprentis de la guilde."),
    "mithril": ("Light as silk, hard as a mountain.", "Légère comme la soie, dure comme la montagne."),
    "aether": ("Crystal plates that drift a hair above the skin.", "Des plaques de cristal qui flottent sur la peau."),
    "arcane": ("Embroidered with runes that rearrange themselves.", "Brodée de runes qui changent de place."),
}
PIECES = ("helmet", "chestplate", "leggings", "boots")


def flavors():
    out = dict(FLAVOR)
    for prefix, txt in SET_FLAVOR.items():
        for piece in PIECES:
            out.setdefault(f"{prefix}_{piece}", txt)
    from .bossgear import BOSS_GEAR, remembrance_id
    for row in BOSS_GEAR:
        out.setdefault(remembrance_id(row[0]), _REMEMBRANCE)
    return out


def lang():
    en, fr = {}, {}
    for key, (e, f) in STRINGS.items():
        en[f"tooltip.{NS}.{key}"], fr[f"tooltip.{NS}.{key}"] = e, f
    for key, (e, f, _size) in ABILITIES.items():
        en[f"tooltip.{NS}.ability.{key}"], fr[f"tooltip.{NS}.ability.{key}"] = e, f
    for key, (e, f) in ABILITY_EFFECTS.items():
        en[f"tooltip.{NS}.ability.effect.{key}"], fr[f"tooltip.{NS}.ability.effect.{key}"] = e, f
    for iid, (e, f) in flavors().items():
        en[f"item.{NS}.{iid}.flavor"], fr[f"item.{NS}.{iid}.flavor"] = e, f
    return en, fr


def check(err, root, en_table, fr_table, item_ids):
    """validate.py: the Java enums match these tables, every flavour belongs to a real item, and every Brasshaven item
    has at least one tooltip line besides its name (flavour or rules) in both languages."""
    import os
    import re
    java = open(os.path.join(root, "src", "main", "java", "com", "brasshaven", "item", "BossWeaponItem.java"),
                encoding="utf-8").read()
    m = re.search(r"enum Ability \{([^}]*)\}", java)
    shapes = [s.strip().lower() for s in m.group(1).split(",")] if m else []
    if sorted(shapes) != sorted(ABILITIES):
        err(f"tooltips.py ABILITIES {sorted(ABILITIES)} != BossWeaponItem.Ability {sorted(shapes)}")
    flags = re.findall(r"public static final int ([A-Z]+) = (\d+);", java)
    if [f.lower() for f, _ in sorted(flags, key=lambda t: int(t[1]))] != list(ABILITY_EFFECTS):
        err("tooltips.py ABILITY_EFFECTS out of order with the BossWeaponItem flags")
    for iid in flavors():
        if iid not in item_ids:
            err(f"tooltips.py: flavour for unknown item {iid}")
    for table, name in ((en_table, "en_us"), (fr_table, "fr_fr")):
        for k in [k for k in table if k.startswith(f"tooltip.{NS}.ability")]:
            if not table[k]:
                err(f"{name}: empty {k}")

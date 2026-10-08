"""Vault gear of the six colossal structures of the last two batches: six armour sets with a 2-piece and a 4-piece set
bonus each, and six weapons / tools with a small right-click or passive identity, found only in the deep chests and
vaults of the Great Aqueduct, the Dam of the Drowned Valley, the Mire Stilt-City, the Sun-Engine Ziggurat, the
Leviathan Dreadnought Wreck and the Canopy Temple-City (loot-only, like the relics of wf/relics.py).

One table per kind drives everything:
  * content.py (names, first tooltip line), lang() (flavours, set-bonus lines, structure names),
  * Java: com.brasshaven.colossal.ColossalGear (registration: armor(...), weapon(...)) declares the same ids;
    ColossalEvents holds the set bonuses and the weapon passives, ColossalWeaponItem the right-click abilities,
  * gen_textures (sprites, armour layers, 3D palettes: wf/colossal_art.py), gen_assets (equipment assets, 3D held
    models via held3d), gen_data (repair and armour / weapon tags), gen_loot (one pool per deep structure chest).
"""

NS = "brasshaven"
PIECES = ("helmet", "chestplate", "leggings", "boots")

# ------------------------------------------------------------------ armour sets
# prefix -> structure key, set name (en, fr), 2-piece and 4-piece bonus (en, fr), flavour, piece names, sprite
# material / accent (wf/colossal_art.py)
SETS = {
    "lockkeeper": {
        "structure": "ga", "name": ("Lock-Keeper's Brass", "Laiton de l'éclusier"),
        "two": ("breathe underwater.", "tu respires sous l'eau."),
        "four": ("swim like a dolphin, and mine underwater as fast as on land.",
                 "tu nages comme un dauphin, et mines sous l'eau aussi vite qu'à l'air libre."),
        "flavor": ("Riveted for the men who walked the channel bed when the sluices were shut.",
                   "Rivetée pour ceux qui marchaient au fond du canal, vannes fermées."),
        "pieces": {"helmet": ("Lock-Keeper's Diving Helm", "Casque de plongée de l'éclusier"),
                   "chestplate": ("Lock-Keeper's Brass Cuirass", "Cuirasse de laiton de l'éclusier"),
                   "leggings": ("Lock-Keeper's Wading Greaves", "Jambières de gué de l'éclusier"),
                   "boots": ("Lock-Keeper's Weighted Boots", "Bottes lestées de l'éclusier")},
        "mat": "lockbrass", "accent": "aether",
    },
    "turbine_engineer": {
        "structure": "dd", "name": ("Turbine Engineer's Rig", "Harnais de l'ingénieur des turbines"),
        "two": ("+10% speed.", "+10 % de vitesse."),
        "four": ("a sprint-jump vents your back boiler: a steam dash forward (every 4 s).",
                 "un saut en sprintant vide ta chaudière dorsale : une ruée de vapeur vers l'avant (toutes les 4 s)."),
        "flavor": ("Gauges on the wrists, a boiler on the back, nerves of cast iron.",
                   "Des manomètres aux poignets, une chaudière dans le dos, des nerfs de fonte."),
        "pieces": {"helmet": ("Turbine Engineer's Goggled Cap", "Casquette à lunettes de l'ingénieur"),
                   "chestplate": ("Turbine Engineer's Boiler Rig", "Harnais-chaudière de l'ingénieur"),
                   "leggings": ("Turbine Engineer's Piston Trousers", "Pantalon à pistons de l'ingénieur"),
                   "boots": ("Turbine Engineer's Hobnail Boots", "Bottes cloutées de l'ingénieur")},
        "mat": "engineer", "accent": "ember",
    },
    "bog_pilgrim": {
        "structure": "mire", "name": ("Bog Pilgrim's Wraps", "Bandes du pèlerin des tourbières"),
        "two": ("poison never takes hold of you.", "le poison n'a plus prise sur toi."),
        "four": ("Slowness never takes hold either, and soul sand, honey and sucking mud no longer slow you.",
                 "la Lenteur non plus, et le sable des âmes, le miel et la boue ne te ralentissent plus."),
        "flavor": ("Waxed reed and gator hide: the bog takes everything but the pilgrim.",
                   "Roseau ciré et cuir de caïman : la tourbière prend tout, sauf le pèlerin."),
        "pieces": {"helmet": ("Bog Pilgrim's Reed Hat", "Chapeau de roseau du pèlerin"),
                   "chestplate": ("Bog Pilgrim's Waxed Coat", "Manteau ciré du pèlerin"),
                   "leggings": ("Bog Pilgrim's Wrapped Leggings", "Jambières bandées du pèlerin"),
                   "boots": ("Bog Pilgrim's Stilt Boots", "Bottes à échasses du pèlerin")},
        "mat": "bogreed", "accent": "emerald",
    },
    "sun_priest": {
        "structure": "sz", "name": ("Sun-Priest's Regalia", "Parure du prêtre du soleil"),
        "two": ("fire never burns you (Fire Resistance).", "le feu ne te brûle plus (Résistance au feu)."),
        "four": ("in daylight under the open sky, your critical hits call down a sun-ray: a third more damage and the "
                 "foe bursts into flame.",
                 "en plein jour sous le ciel, tes coups critiques appellent un rayon de soleil : un tiers de dégâts en "
                 "plus et l'ennemi s'embrase."),
        "flavor": ("Polished each dawn so the engine's god would know its servant.",
                   "Polie chaque aube pour que le dieu du moteur reconnaisse son serviteur."),
        "pieces": {"helmet": ("Sun-Priest's Disc Crown", "Couronne-disque du prêtre du soleil"),
                   "chestplate": ("Sun-Priest's Pectoral", "Pectoral du prêtre du soleil"),
                   "leggings": ("Sun-Priest's Pleated Kilt", "Pagne plissé du prêtre du soleil"),
                   "boots": ("Sun-Priest's Gilded Sandals", "Sandales dorées du prêtre du soleil")},
        "mat": "sungold", "accent": "sapphire",
    },
    "ironclad": {
        "structure": "dw", "name": ("Ironclad Officer's Plate", "Armure de l'officier cuirassé"),
        "two": ("+30% knockback resistance.", "+30 % de résistance au recul."),
        "four": ("explosions deal half damage to you and no longer throw you about.",
                 "les explosions ne t'infligent que la moitié des dégâts et ne te projettent plus."),
        "flavor": ("Armour plate cut from the ship's own belt, buttons from her brass.",
                   "Des plaques taillées dans la ceinture blindée du navire, des boutons dans son laiton."),
        "pieces": {"helmet": ("Ironclad Officer's Peaked Helm", "Casque à visière de l'officier"),
                   "chestplate": ("Ironclad Officer's Armoured Coat", "Vareuse blindée de l'officier"),
                   "leggings": ("Ironclad Officer's Plated Trousers", "Pantalon blindé de l'officier"),
                   "boots": ("Ironclad Officer's Deck Boots", "Bottes de pont de l'officier")},
        "mat": "navyiron", "accent": "gold",
    },
    "canopy_stalker": {
        "structure": "cc", "name": ("Canopy Stalker's Leathers", "Cuirs du traqueur de la canopée"),
        "two": ("4 more blocks before falls hurt, and a third less fall damage.",
                "4 blocs de plus avant que les chutes ne blessent, et un tiers de dégâts de chute en moins."),
        "four": ("walk into leaves to climb them like a ladder (sneak to hold on).",
                 "marche contre des feuilles pour y grimper comme à une échelle (accroupis-toi pour t'y tenir)."),
        "flavor": ("The temple's hunters never touched the ground between two kills.",
                   "Les chasseurs du temple ne touchaient jamais le sol entre deux proies."),
        "pieces": {"helmet": ("Canopy Stalker's Feathered Mask", "Masque à plumes du traqueur"),
                   "chestplate": ("Canopy Stalker's Leaf Jerkin", "Pourpoint de feuilles du traqueur"),
                   "leggings": ("Canopy Stalker's Vine Leggings", "Jambières de lianes du traqueur"),
                   "boots": ("Canopy Stalker's Climbing Wraps", "Bandes d'escalade du traqueur")},
        "mat": "stalker", "accent": "emerald",
    },
}
# repair material of each set (item tag brasshaven:<prefix>_repair, read by ColossalGear)
REPAIR = {"lockkeeper": [f"{NS}:brass_ingot", "minecraft:prismarine_crystals"],
          "turbine_engineer": [f"{NS}:brass_ingot", "minecraft:copper_ingot"],
          "bog_pilgrim": ["minecraft:leather", "minecraft:slime_ball"],
          "sun_priest": ["minecraft:gold_ingot"],
          "ironclad": ["minecraft:iron_ingot"],
          "canopy_stalker": ["minecraft:leather", "minecraft:vine"]}

# ------------------------------------------------------------------ weapons and tools
# id -> structure, (en, fr), first tooltip line (en, fr), flavour, sprite (material, handle, accent), 3D archetype
WEAPONS = {
    "sluice_hook": {
        "structure": "ga", "name": ("Sluice-Hook Spear", "Lance-croc de l'écluse"),
        "rule": ("Use: cast the hook up to 14 blocks: it drags the first foe to your feet, or, if it bites stone, hauls "
                 "you there. Hits on foes standing in water deal 3 more damage.",
                 "Clic droit : lance le croc jusqu'à 14 blocs : il ramène à tes pieds le premier ennemi, ou, s'il mord "
                 "la pierre, t'y hisse. Tes coups sur un ennemi dans l'eau font 3 dégâts de plus."),
        "flavor": ("Made to pull drowned logs from the sluice grates. It is not fussy about what it pulls.",
                   "Fait pour tirer les troncs noyés des grilles d'écluse. Il n'est pas difficile sur ce qu'il tire."),
        "sprite": ("lockbrass", "wood", "aether"), "held": "colossal_sluice_hook",
    },
    "rivet_cannon": {
        "structure": "dd", "name": ("Dam-Wright's Rivet Cannon", "Canon à rivets du bâtisseur"),
        "rule": ("Use: a blast of five red-hot rivets in a fan ahead (4 damage each), no ammunition needed; the recoil "
                 "nudges you back.",
                 "Clic droit : une gerbe de cinq rivets chauffés au rouge en éventail (4 dégâts chacun), sans munitions ; "
                 "le recul te repousse un peu."),
        "flavor": ("It closed the dam's seams under forty fathoms of water. Flesh gives way more easily.",
                   "Il a fermé les joints du barrage sous quarante brasses d'eau. La chair cède plus vite."),
        "sprite": ("engineer", "wood", "ember"), "held": "colossal_rivet_cannon",
    },
    "bog_lantern_flail": {
        "structure": "mire", "name": ("Bog-Lantern Flail", "Fléau-lanterne des tourbières"),
        "rule": ("Your hits poison foes for 3 s. Use: the lantern flares, revealing every foe within 6 blocks (Glowing, "
                 "10 s) and choking them in marsh gas; you see in the dark for 30 s.",
                 "Tes coups empoisonnent 3 s. Clic droit : la lanterne s'embrase et révèle tous les ennemis à 6 blocs "
                 "(Surbrillance, 10 s) en les étouffant de gaz des marais ; tu vois dans le noir 30 s."),
        "flavor": ("The marsh light that leads pilgrims astray, caught in a cage and swung back at the bog.",
                   "Le feu follet qui égare les pèlerins, mis en cage et renvoyé contre la tourbière."),
        "sprite": ("bogreed", "dark", "emerald"), "held": "colossal_bog_flail",
    },
    "solar_khopesh": {
        "structure": "sz", "name": ("Solar Khopesh", "Khépesh solaire"),
        "rule": ("In daylight under the open sky, your hits set foes ablaze, and undead take 3 more damage. Use: flash "
                 "the blade at the sun to blind the foes ahead (8 blocks); undead among them burn.",
                 "En plein jour sous le ciel, tes coups embrasent les ennemis, et les morts-vivants prennent 3 dégâts de "
                 "plus. Clic droit : fais miroiter la lame au soleil pour aveugler les ennemis devant toi (8 blocs) ; "
                 "les morts-vivants parmi eux brûlent."),
        "flavor": ("Its edge was ground on the lens of the sun-engine itself.",
                   "Son fil a été aiguisé sur la lentille même du moteur solaire."),
        "sprite": ("sungold", "wood", "sapphire"), "held": "colossal_khopesh",
    },
    "boarding_axe": {
        "structure": "dw", "name": ("Boarding Axe", "Hache d'abordage"),
        "rule": ("Chops wood like an axe and knocks shields aside. Use: a boarding rush 6 blocks ahead, hacking every foe "
                 "on the way (7 damage) and bracing you (Resistance I, 3 s).",
                 "Coupe le bois comme une hache et écarte les boucliers. Clic droit : une ruée d'abordage de 6 blocs qui "
                 "taille tous les ennemis sur le chemin (7 dégâts) et t'arc-boute (Résistance I, 3 s)."),
        "flavor": ("Standard issue for cutting rigging, doors and, when it came to it, the enemy.",
                   "Réglementaire pour trancher le gréement, les portes et, le moment venu, l'ennemi."),
        "sprite": ("navyiron", "wood", "gold"), "held": "colossal_boarding_axe",
    },
    "jade_blowpipe": {
        "structure": "cc", "name": ("Jade Blowpipe", "Sarbacane de jade"),
        "rule": ("Use: a silent poisoned dart (Poison II, 4 s, and Slowness, 3 s), no ammunition needed, once a second.",
                 "Clic droit : une fléchette empoisonnée silencieuse (Poison II, 4 s, et Lenteur, 3 s), sans munitions, "
                 "une par seconde."),
        "flavor": ("Carved from one piece of jade; the frog that tipped its darts is carved on the mouthpiece.",
                   "Taillée d'un seul bloc de jade ; la grenouille qui empoisonnait ses fléchettes est gravée sur "
                   "l'embout."),
        "sprite": ("jade", "wood", "gold"), "held": "colossal_blowpipe",
    },
}

# the structure each item comes from (tooltip.brasshaven.relic.<key>, "Relic of the Great Aqueduct")
STRUCTURE_NAMES = {
    "ga": ("Great Aqueduct", "Grand Aqueduc"),
    "dd": ("Dam of the Drowned Valley", "Barrage de la vallée engloutie"),
    "mire": ("Mire Stilt-City", "Cité des pilotis"),
    "sz": ("Sun-Engine Ziggurat", "Ziggourat du moteur solaire"),
    "dw": ("Leviathan Dreadnought", "Cuirassé Léviathan"),
    "cc": ("Canopy Temple-City", "Cité-temple de la canopée"),
}


def armor_ids():
    return [f"{p}_{piece}" for p in SETS for piece in PIECES]


def all_ids():
    return armor_ids() + list(WEAPONS)


# ------------------------------------------------------------------ content.py (names, first tooltip line)
def register_content(items):
    for prefix, s in SETS.items():
        for piece in PIECES:
            en, fr = s["pieces"][piece]
            items[f"{prefix}_{piece}"] = (en, fr, f"One of the four pieces of the {s['name'][0]}.",
                                          f"L'une des quatre pièces : {s['name'][1]}.")
    for wid, w in WEAPONS.items():
        items[wid] = (w["name"][0], w["name"][1], w["rule"][0], w["rule"][1])


def lang():
    """Flavour lines, the set-bonus lines read by ColossalArmorItem and the structure names of the tooltip."""
    en, fr = {}, {}
    for prefix, s in SETS.items():
        for piece in PIECES:
            en[f"item.{NS}.{prefix}_{piece}.flavor"], fr[f"item.{NS}.{prefix}_{piece}.flavor"] = s["flavor"]
        for n in ("two", "four"):
            e, f = s[n]
            en[f"tooltip.{NS}.colossal.{prefix}.{n}"] = e[0].upper() + e[1:]
            fr[f"tooltip.{NS}.colossal.{prefix}.{n}"] = f[0].upper() + f[1:]
    for wid, w in WEAPONS.items():
        en[f"item.{NS}.{wid}.flavor"], fr[f"item.{NS}.{wid}.flavor"] = w["flavor"]
    en[f"tooltip.{NS}.colossal.set"] = "Set bonus (%s/4 worn):"
    fr[f"tooltip.{NS}.colossal.set"] = "Bonus d'ensemble (%s/4 portées) :"
    en[f"tooltip.{NS}.colossal.two"] = "2 pieces: %s"
    fr[f"tooltip.{NS}.colossal.two"] = "2 pièces : %s"
    en[f"tooltip.{NS}.colossal.four"] = "4 pieces: %s"
    fr[f"tooltip.{NS}.colossal.four"] = "4 pièces : %s"
    for key, (e, f) in STRUCTURE_NAMES.items():
        en[f"tooltip.{NS}.relic.{key}"], fr[f"tooltip.{NS}.relic.{key}"] = e, f
    return en, fr


# ------------------------------------------------------------------ gen_data (tags)
def tags(write):
    """Writes the repair tags; returns {tag file: values} to merge into the shared vanilla tags."""
    for prefix, values in REPAIR.items():
        write(f"{NS}/tags/item/{prefix}_repair.json", {"values": values})
    out = {}
    for slot, piece in (("head", "helmet"), ("chest", "chestplate"), ("leg", "leggings"), ("foot", "boots")):
        out[f"minecraft/tags/item/{slot}_armor.json"] = [f"{NS}:{p}_{piece}" for p in SETS]
    out["minecraft/tags/item/swords.json"] = [f"{NS}:{w}" for w in ("sluice_hook", "bog_lantern_flail", "solar_khopesh")]
    out["minecraft/tags/item/axes.json"] = [f"{NS}:boarding_axe"]
    out["minecraft/tags/item/enchantable/durability.json"] = [f"{NS}:rivet_cannon", f"{NS}:jade_blowpipe"]
    return out


# ------------------------------------------------------------------ gen_loot (deep chests only)
# what each structure hides, with the depth it starts to appear at (2 inner halls, 3 hoard / secret)
STRUCTURE_GEAR = {s: [(f"{p}_boots", 2), (f"{p}_helmet", 2), (f"{p}_leggings", 3), (f"{p}_chestplate", 3)]
                  for p, d in SETS.items() for s in [d["structure"]]}
for _wid, _w in WEAPONS.items():
    STRUCTURE_GEAR[_w["structure"]].append((_wid, 3))
# chest table -> (structure, depth): 2 the deep halls (the tables with real treasure), 3 the hoard / secret rooms,
# 4 the vault behind the boss; the camps, outer rooms and towns hold none of it
TABLE_DEPTH = {
    "ga_valve": ("ga", 2), "ga_belfry": ("ga", 2), "ga_secret": ("ga", 3), "ga_vault": ("ga", 4),
    "dd_turbine": ("dd", 2), "dd_hoard": ("dd", 3), "dd_vault": ("dd", 4),
    "mire_undercroft": ("mire", 2), "mire_queen": ("mire", 2), "mire_hoard": ("mire", 3), "mire_vault": ("mire", 4),
    "sz_tomb": ("sz", 2), "sz_lens": ("sz", 2), "sz_summit": ("sz", 3), "sz_crypt": ("sz", 3), "sz_vault": ("sz", 4),
    "dw_torpedo": ("dw", 2), "dw_captain": ("dw", 2), "dw_top": ("dw", 3), "dw_magazine": ("dw", 3),
    "dw_vault": ("dw", 4),
    "cc_traps": ("cc", 2), "cc_sanctum": ("cc", 2), "cc_offering": ("cc", 2), "cc_crypt": ("cc", 3),
    "cc_cenote": ("cc", 3), "cc_vault": ("cc", 4),
}
# depth -> (rolls, weight of "nothing")
DEPTH_POOL = {2: ((1, 1), 60), 3: ((1, 1), 22), 4: ((1, 2), 4)}
# how common an item of a given depth is among the entries (the deepest gear stays the rarest)
ITEM_WEIGHT = {2: 10, 3: 5}


def loot_pools(table):
    """Extra pools for a deep structure chest table (gen_loot.table() appends them), or [] for other tables."""
    spec = TABLE_DEPTH.get(table)
    if not spec:
        return []
    structure, depth = spec
    rolls, empty = DEPTH_POOL[depth]
    entries = []
    for iid, d in STRUCTURE_GEAR[structure]:
        if d > depth:
            continue
        e = {"type": "minecraft:item", "name": f"{NS}:{iid}",
             "weight": ITEM_WEIGHT[d] * (2 if depth == 4 and d == 3 else 1)}
        if depth >= 3:
            e["functions"] = [{"function": "minecraft:enchant_with_levels",
                               "levels": {"type": "minecraft:uniform", "min": 10, "max": 25},
                               "conditions": [{"condition": "minecraft:random_chance", "chance": 0.3}]}]
        entries.append(e)
    entries.append({"type": "minecraft:empty", "weight": empty})
    return [{"rolls": {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]}, "bonus_rolls": 0.0,
             "entries": entries}]


# ------------------------------------------------------------------ gen_assets
def assets(write):
    """Equipment assets of the six sets (the layer textures come from colossal_art.textures())."""
    for prefix in SETS:
        write(f"equipment/{prefix}.json", {"layers": {
            "humanoid": [{"texture": f"{NS}:{prefix}"}],
            "humanoid_leggings": [{"texture": f"{NS}:{prefix}"}],
        }})


def held():
    """id -> held3d entry (archetype, material, handle, accent) for the weapons with a 3D model in hand."""
    return {wid: (w["held"], w["sprite"][0], w["sprite"][1], w["sprite"][2]) for wid, w in WEAPONS.items()}


def handheld():
    return set(WEAPONS)

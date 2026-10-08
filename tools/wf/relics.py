"""Relic gear of the colossal structures: four armour sets, eight weapons and six accessories, found only in the
chests of the Caldera Ringwall, the Glacier Hall, the Kneeling Gate, the Tidal Abbey, Pilgrim's Ascent and the
Shattered Halo (loot-only: no recipes, the reason to climb all the way up).

One table per kind drives everything:
  * content.py (names, rules), tooltips (flavour, written here by lang()),
  * Java: com.brasshaven.relic.RelicGear (registration: weapon(...), armor(...), accessory(...)) must declare the same
    ids, numbers and abilities; RelicEvents holds the set bonuses and the worn effects,
  * gen_textures (sprites in wf/relicart.py, armour layers, 3D palettes), gen_assets (equipment assets, 3D held models
    via held3d), gen_data (tags), gen_loot (one relic pool per structure chest, rarer gear deeper in),
  * accessories.py (the slot tags).
"""

NS = "brasshaven"

# ------------------------------------------------------------------ armour sets
# prefix -> structure, (set name en, fr), set bonus (en, fr), flavour (en, fr), piece names {piece: (en, fr)},
#           sprite material, accent, 3D/handle-free
SETS = {
    "frostplate": {
        "structure": "glacier",
        "bonus": ("Set: you never freeze, melee attackers are slowed for 3 s, and Resistance I in cold lands.",
                  "Ensemble : tu ne gèles jamais, qui te frappe au corps à corps est ralenti 3 s, et Résistance I "
                  "dans les terres froides."),
        "flavor": ("Forged in the glacier's heart, quenched in meltwater.",
                   "Forgée au cœur du glacier, trempée dans l'eau de fonte."),
        "pieces": {"helmet": ("Jarl's Horned Helm", "Heaume cornu du jarl"),
                   "chestplate": ("Jarl's Frostplate", "Cuirasse de givre du jarl"),
                   "leggings": ("Jarl's Frost Greaves", "Grèves de givre du jarl"),
                   "boots": ("Jarl's Frost Sabatons", "Solerets de givre du jarl")},
        "mat": "glacier", "accent": "ice",
    },
    "magmaguard": {
        "structure": "caldera",
        "bonus": ("Set: magma blocks never burn you, melee attackers catch fire for 4 s, and Strength I while you "
                  "stand in fire or lava.",
                  "Ensemble : les blocs de magma ne te brûlent plus, qui te frappe au corps à corps prend feu 4 s, et "
                  "Force I tant que tu es dans le feu ou la lave."),
        "flavor": ("Basalt plates bolted over a heart of slow magma.",
                   "Des plaques de basalte boulonnées sur un cœur de magma lent."),
        "pieces": {"helmet": ("Caldera Magmaguard Helm", "Heaume de la garde de magma"),
                   "chestplate": ("Caldera Magmaguard Cuirass", "Cuirasse de la garde de magma"),
                   "leggings": ("Caldera Magmaguard Tassets", "Tassettes de la garde de magma"),
                   "boots": ("Caldera Magmaguard Boots", "Bottes de la garde de magma")},
        "mat": "magma", "accent": "ember",
    },
    "tidewarden": {
        "structure": "abbey",
        "bonus": ("Set: breathe underwater, swim faster, and heal half a heart every 4 s while wet (water or rain).",
                  "Ensemble : tu respires sous l'eau, nages plus vite, et regagnes un demi-cœur toutes les 4 s quand "
                  "tu es mouillé (eau ou pluie)."),
        "flavor": ("The abbey's wardens walked the causeway at high tide.",
                   "Les gardiens de l'abbaye traversaient la chaussée à marée haute."),
        "pieces": {"helmet": ("Tidewarden Sallet", "Salade du gardien des marées"),
                   "chestplate": ("Tidewarden Hauberk", "Haubert du gardien des marées"),
                   "leggings": ("Tidewarden Chausses", "Chausses du gardien des marées"),
                   "boots": ("Tidewarden Wading Boots", "Bottes de gué du gardien des marées")},
        "mat": "tide", "accent": "sapphire",
    },
    "windrobe": {
        "structure": "ascent",
        "bonus": ("Set: +10% speed, Jump Boost I, and no fall damage from below 12 blocks (halved above).",
                  "Ensemble : +10 % de vitesse, Saut amélioré I, et aucun dégât de chute sous 12 blocs (moitié "
                  "au-delà)."),
        "flavor": ("Woven light enough for the wind to carry a pilgrim the last steps.",
                   "Tissée si légère que le vent porte le pèlerin sur les dernières marches."),
        "pieces": {"helmet": ("Pilgrim's Wind Hood", "Capuche du pèlerin des vents"),
                   "chestplate": ("Pilgrim's Windrobe", "Robe du pèlerin des vents"),
                   "leggings": ("Pilgrim's Wind Trousers", "Chausses du pèlerin des vents"),
                   "boots": ("Pilgrim's Wind Sandals", "Sandales du pèlerin des vents")},
        "mat": "wind", "accent": "red",
    },
}
PIECES = ("helmet", "chestplate", "leggings", "boots")
# repair material of each set (item tag brasshaven:<prefix>_repair, read by RelicGear)
REPAIR = {"frostplate": ["minecraft:blue_ice"], "magmaguard": ["minecraft:magma_cream"],
          "tidewarden": [f"{NS}:pearl", "minecraft:prismarine_crystals"], "windrobe": ["minecraft:phantom_membrane"]}

# ------------------------------------------------------------------ weapons
# id -> structure, (en, fr), rule (en, fr), flavour (en, fr), ability (BossWeaponItem.Ability), power, size, cooldown,
#       particle, flags, signature (what RelicWeaponItem adds), sprite (material, handle, accent), 3D archetype or None
WEAPONS = {
    "magma_maul": {
        "structure": "caldera", "name": ("Caldera Magma Maul", "Masse de magma de la caldeira"),
        "rule": ("Use: magma bursts from the ground along a line and sets foes ablaze; you shrug off fire for 6 s.",
                 "Clic droit : le magma jaillit du sol en ligne et embrase les ennemis ; le feu ne te touche plus "
                 "pendant 6 s."),
        "flavor": ("Quarried from the crater wall while the stone was still soft.",
                   "Taillée dans la paroi du cratère quand la pierre était encore molle."),
        "ability": "ERUPT", "power": 11, "size": 10, "cooldown": 90, "particle": "FLAME", "flags": "fire",
        "sprite": ("magma", "dark", "ember"), "held": "relic_magma_maul",
    },
    "bastion_cannon": {
        "structure": "caldera", "name": ("Bastion Hand-Cannon", "Couleuvrine du bastion"),
        "rule": ("Use: a blast that tears through everything ahead and hurls foes off their feet; the recoil throws "
                 "you back a few steps.",
                 "Clic droit : une décharge qui traverse tout devant toi et renverse les ennemis ; le recul te projette "
                 "quelques pas en arrière."),
        "flavor": ("The east bastion's gunners never ran out of powder, only of walls.",
                   "Les canonniers du bastion est n'ont jamais manqué de poudre, seulement de murs."),
        "ability": "BEAM", "power": 12, "size": 18, "cooldown": 80, "particle": "LARGE_SMOKE", "flags": "lift",
        "sprite": ("brass", "wood", "ember"), "held": "relic_cannon",
    },
    "rimefang_spear": {
        "structure": "glacier", "name": ("Rimefang Spear", "Lance Croc-de-givre"),
        "rule": ("Use: the ice seizes every foe around you, slows them to a crawl and freezes them stiff.",
                 "Clic droit : la glace saisit les ennemis autour de toi, les ralentit presque à l'arrêt et les gèle."),
        "flavor": ("The skalds sang that it was cut from the jarl's own frozen tear.",
                   "Les scaldes chantaient qu'elle fut taillée dans une larme gelée du jarl."),
        "ability": "ROOT", "power": 8, "size": 6, "cooldown": 90, "particle": "SNOWFLAKE", "flags": "slow",
        "sprite": ("glacier", "dark", "ice"), "held": "relic_rime_spear",
    },
    "oathbreaker": {
        "structure": "kg", "name": ("Oathbreaker", "Brise-serment"),
        "rule": ("Use: leap forward and crash down, weakening foes; the broken oath fuels you (Strength I, 5 s).",
                 "Clic droit : bondis et retombe sur les ennemis en les affaiblissant ; le serment brisé te galvanise "
                 "(Force I, 5 s)."),
        "flavor": ("The giants knelt to swear. This is what they swore on.",
                   "Les géants se sont agenouillés pour jurer. Voici sur quoi ils ont juré."),
        "ability": "LEAP", "power": 11, "size": 4.5, "cooldown": 70, "particle": "ENCHANTED_HIT", "flags": "weak",
        "sprite": ("stone", "dark", "gold"), "held": "relic_oath_greatsword",
    },
    "toll_billhook": {
        "structure": "kg", "name": ("Toll-Warden's Billhook", "Vouge du péager"),
        "rule": ("Use: the hook drags the first foe ahead to your feet and you take your toll of its life; the toll "
                 "shields you (Absorption I, 6 s).",
                 "Clic droit : le croc ramène à tes pieds le premier ennemi devant toi et tu prélèves ton péage sur sa "
                 "vie ; le péage te protège (Absorption I, 6 s)."),
        "flavor": ("Every traveller paid. The ones who did not are still in the hall below.",
                   "Tout voyageur payait. Ceux qui refusaient sont encore dans la salle du dessous."),
        "ability": "HOOK", "power": 8, "size": 14, "cooldown": 70, "particle": "WAX_ON", "flags": "lifesteal",
        "sprite": ("iron", "wood", "gold"), "held": "relic_billhook",
    },
    "undertow_glaive": {
        "structure": "abbey", "name": ("Undertow Glaive", "Glaive du ressac"),
        "rule": ("Use: ride a wave forward through your foes and slow them; then breathe and swim like a dolphin "
                 "for 10 s.",
                 "Clic droit : file sur une vague à travers les ennemis et ralentis-les ; ensuite tu respires et nages "
                 "comme un dauphin pendant 10 s."),
        "flavor": ("The tide comes in faster than a horse can gallop.",
                   "La marée monte plus vite qu'un cheval au galop."),
        "ability": "DASH", "power": 9, "size": 9, "cooldown": 60, "particle": "SPLASH", "flags": "slow",
        "sprite": ("tide", "bone", "sapphire"), "held": "relic_glaive",
    },
    "gale_staff": {
        "structure": "ascent", "name": ("Pilgrim's Gale Staff", "Bâton des bourrasques"),
        "rule": ("Use: step ahead on a gust, hurling the foes where you land into the air; then drift down slowly "
                 "and jump higher for 5 s.",
                 "Clic droit : avance d'un pas sur une bourrasque et projette en l'air les ennemis à l'arrivée ; "
                 "ensuite tu descends lentement et sautes plus haut pendant 5 s."),
        "flavor": ("Its bell rang at every gate of the climb.", "Sa clochette a sonné à chaque porte de l'ascension."),
        "ability": "BLINK", "power": 7, "size": 10, "cooldown": 50, "particle": "CLOUD", "flags": "lift",
        "sprite": ("wood", "wood", "red"), "held": "relic_gale_staff",
    },
    "starfall_lance": {
        "structure": "halo", "name": ("Starfall Lance", "Lance des étoiles filantes"),
        "rule": ("Use: stars fall in a ring around you, hurting and blinding every foe; you move swiftly for 5 s.",
                 "Clic droit : des étoiles tombent en cercle autour de toi, blessent et aveuglent les ennemis ; tu te "
                 "déplaces vite pendant 5 s."),
        "flavor": ("A spoke of the broken halo, still falling.", "Un rayon du halo brisé, qui tombe encore."),
        "ability": "WAVE", "power": 10, "size": 6.5, "cooldown": 75, "particle": "END_ROD", "flags": "blind",
        "sprite": ("halo", "purpur", "gold"), "held": "relic_star_lance",
    },
}

# ------------------------------------------------------------------ accessories
# id -> slot, structure, (en, fr), rule (en, fr), flavour (en, fr), sprite (material, accent)
ACCESSORIES = {
    "jarl_mantle": {
        "slot": "back", "structure": "glacier", "name": ("Jarl's Bear Mantle", "Manteau d'ours du jarl"),
        "rule": ("Worn: you never freeze, and Resistance I in cold lands.",
                 "Porté : tu ne gèles jamais, et Résistance I dans les terres froides."),
        "flavor": ("The bear lost; the cold never won either.", "L'ours a perdu ; le froid non plus n'a jamais gagné."),
        "sprite": ("leather", "ice"),
    },
    "ember_signet": {
        "slot": "ring", "structure": "caldera", "name": ("Castellan's Ember Signet", "Chevalière de braise du châtelain"),
        "rule": ("Worn: your melee hits set foes ablaze for 3 s.",
                 "Portée : tes coups au corps à corps enflamment les ennemis pendant 3 s."),
        "flavor": ("Its seal still glows on every order it signed.", "Son sceau rougeoie encore sur chaque ordre signé."),
        "sprite": ("gold", "ember"),
    },
    "pilgrim_band": {
        "slot": "ring", "structure": "ascent", "name": ("Pilgrim's Wind Band", "Anneau des vents du pèlerin"),
        "rule": ("Worn: +10% speed, and a third less fall damage.",
                 "Porté : +10 % de vitesse, et un tiers de dégâts de chute en moins."),
        "flavor": ("Worn thin by a thousand steps.", "Usé par mille marches."),
        "sprite": ("brass", "aether"),
    },
    "tide_pendant": {
        "slot": "amulet", "structure": "abbey", "name": ("Abbey Tide Pendant", "Pendentif des marées"),
        "rule": ("Worn: underwater, you breathe freely and gain Conduit Power.",
                 "Porté : sous l'eau, tu respires librement et gagnes la Force de conduit."),
        "flavor": ("A pearl that still rises and falls with the tide.", "Une perle qui monte et descend avec la marée."),
        "sprite": ("tide", "sapphire"),
    },
    "halo_locket": {
        "slot": "amulet", "structure": "halo", "name": ("Halo Locket", "Médaillon du halo"),
        "rule": ("Worn: when a blow leaves you under 3 hearts, Regeneration II and Absorption II for 8 s (once every "
                 "90 s).",
                 "Porté : quand un coup te laisse sous 3 cœurs, Régénération II et Absorption II pendant 8 s (une fois "
                 "toutes les 90 s)."),
        "flavor": ("A sliver of the halo, kept against the last fall.", "Un éclat du halo, gardé pour la dernière chute."),
        "sprite": ("halo", "gold"),
    },
    "oath_girdle": {
        "slot": "belt", "structure": "kg", "name": ("Oathbound Girdle", "Ceinturon du serment"),
        "rule": ("Worn: +2 hearts of max health and 30% knockback resistance.",
                 "Porté : +2 cœurs de vie max et 30 % de résistance au recul."),
        "flavor": ("Buckled with the golden key of the toll.", "Bouclé par la clé d'or du péage."),
        "sprite": ("leather", "gold"),
    },
}


def accessory_slots():
    """slot -> ids (accessories.py adds them to its slot tags)."""
    out = {}
    for iid, a in ACCESSORIES.items():
        out.setdefault(a["slot"], []).append(iid)
    return out


def armor_ids():
    return [f"{p}_{piece}" for p in SETS for piece in PIECES]


def all_ids():
    return armor_ids() + list(WEAPONS) + list(ACCESSORIES)


# ------------------------------------------------------------------ content.py (names and rules)
def register_content(items):
    for prefix, s in SETS.items():
        for piece in PIECES:
            en, fr = s["pieces"][piece]
            items[f"{prefix}_{piece}"] = (en, fr, s["bonus"][0], s["bonus"][1])
    for wid, w in WEAPONS.items():
        items[wid] = (w["name"][0], w["name"][1], w["rule"][0], w["rule"][1])
    for aid, a in ACCESSORIES.items():
        items[aid] = (a["name"][0], a["name"][1], a["rule"][0], a["rule"][1])


def lang():
    """Flavour lines (BrassTooltip reads item.brasshaven.<id>.flavor) and the strings of RelicWeaponItem."""
    en, fr = {}, {}
    for prefix, s in SETS.items():
        for piece in PIECES:
            en[f"item.{NS}.{prefix}_{piece}.flavor"], fr[f"item.{NS}.{prefix}_{piece}.flavor"] = s["flavor"]
    for iid, d in list(WEAPONS.items()) + list(ACCESSORIES.items()):
        en[f"item.{NS}.{iid}.flavor"], fr[f"item.{NS}.{iid}.flavor"] = d["flavor"]
    en[f"tooltip.{NS}.relic"] = "Relic of the %s"
    fr[f"tooltip.{NS}.relic"] = "Relique : %s"
    for key, (e, f) in STRUCTURE_NAMES.items():
        en[f"tooltip.{NS}.relic.{key}"], fr[f"tooltip.{NS}.relic.{key}"] = e, f
    en[f"tooltip.{NS}.relic.self"] = "Then grants you %s (%s s)."
    fr[f"tooltip.{NS}.relic.self"] = "Puis te donne %s (%s s)."
    en[f"tooltip.{NS}.relic.freeze"] = "Freezes the foes it hits."
    fr[f"tooltip.{NS}.relic.freeze"] = "Gèle les ennemis touchés."
    en[f"message.{NS}.relic.halo_locket"] = "The halo locket flares: you hold on."
    fr[f"message.{NS}.relic.halo_locket"] = "Le médaillon du halo s'embrase : tu tiens bon."
    return en, fr


# the structure each relic comes from (shown in the tooltip, "Relic of the Glacier Hall")
STRUCTURE_NAMES = {
    "caldera": ("Caldera Ringwall", "Rempart de la caldeira"),
    "glacier": ("Glacier Hall", "Halle glaciaire"),
    "kg": ("Kneeling Gate", "Porte agenouillée"),
    "abbey": ("Tidal Abbey", "Abbaye des marées"),
    "ascent": ("Pilgrim's Ascent", "Ascension du pèlerin"),
    "halo": ("Shattered Halo", "Halo brisé"),
}


def structure_of(iid):
    for prefix, s in SETS.items():
        if iid.startswith(prefix + "_"):
            return s["structure"]
    d = WEAPONS.get(iid) or ACCESSORIES.get(iid)
    return d["structure"] if d else None


# ------------------------------------------------------------------ gen_data (tags)
def tags(write):
    """Writes the repair tags; returns {tag file: values} to merge into shared vanilla tags."""
    for prefix, values in REPAIR.items():
        write(f"{NS}/tags/item/{prefix}_repair.json", {"values": values})
    out = {}
    for slot, piece in (("head", "helmet"), ("chest", "chestplate"), ("leg", "leggings"), ("foot", "boots")):
        out[f"minecraft/tags/item/{slot}_armor.json"] = [f"{NS}:{p}_{piece}" for p in SETS]
    out["minecraft/tags/item/swords.json"] = [f"{NS}:{w}" for w in WEAPONS if w != "gale_staff"]
    out["minecraft/tags/item/enchantable/durability.json"] = [f"{NS}:gale_staff"]
    return out


# ------------------------------------------------------------------ gen_loot (one relic pool per structure chest)
# what each structure hides, with the depth it starts to appear at (1 outer rooms, 2 inner halls, 3 hoard / vault)
STRUCTURE_GEAR = {
    "caldera": [("magmaguard_boots", 1), ("magmaguard_helmet", 1), ("magmaguard_leggings", 2),
                ("magmaguard_chestplate", 2), ("bastion_cannon", 2), ("ember_signet", 2), ("magma_maul", 3)],
    "glacier": [("frostplate_boots", 1), ("frostplate_helmet", 1), ("frostplate_leggings", 2),
                ("frostplate_chestplate", 2), ("jarl_mantle", 2), ("rimefang_spear", 3)],
    "kg": [("oath_girdle", 1), ("toll_billhook", 2), ("oathbreaker", 3)],
    "abbey": [("tidewarden_boots", 1), ("tidewarden_helmet", 1), ("tidewarden_leggings", 2),
              ("tidewarden_chestplate", 2), ("tide_pendant", 2), ("undertow_glaive", 3)],
    "ascent": [("windrobe_boots", 1), ("windrobe_helmet", 1), ("windrobe_leggings", 2), ("windrobe_chestplate", 2),
               ("pilgrim_band", 2), ("gale_staff", 3)],
    "halo": [("halo_locket", 2), ("starfall_lance", 3)],
}
# chest table -> (structure, depth); depth 0 tables (camps, towns at the foot) hold no relic
TABLE_DEPTH = {
    "caldera_ramparts": ("caldera", 1), "caldera_barracks": ("caldera", 1), "caldera_hall": ("caldera", 1),
    "caldera_armory": ("caldera", 2), "caldera_undercroft": ("caldera", 2), "caldera_needle": ("caldera", 2),
    "caldera_keep": ("caldera", 2), "caldera_hoard": ("caldera", 3), "caldera_vault": ("caldera", 4),
    "glacier_hall": ("glacier", 1), "glacier_skald": ("glacier", 1), "glacier_armory": ("glacier", 2),
    "glacier_crypt": ("glacier", 2), "glacier_hoard": ("glacier", 3), "glacier_vault": ("glacier", 4),
    "kg_guard": ("kg", 1), "kg_girdle": ("kg", 1), "kg_heart": ("kg", 2), "kg_watch": ("kg", 2),
    "kg_lintel": ("kg", 2), "kg_treasury": ("kg", 3), "kg_vault": ("kg", 4),
    "abbey_ramparts": ("abbey", 1), "abbey_cloister": ("abbey", 1), "abbey_knights": ("abbey", 2),
    "abbey_treasury": ("abbey", 2), "abbey_reliquary": ("abbey", 3), "abbey_vault": ("abbey", 4),
    "ascent_shrine": ("ascent", 1), "ascent_pinnacle": ("ascent", 2), "ascent_hermit": ("ascent", 3),
    "ascent_vault": ("ascent", 4),
    "halo_observatory": ("halo", 1), "halo_library": ("halo", 1), "halo_bell": ("halo", 2), "halo_gate": ("halo", 2),
    "halo_reliquary": ("halo", 2), "halo_crypt": ("halo", 3), "halo_vault": ("halo", 4),
}
# depth -> (rolls, weight of "nothing"); depth 4 is the vault behind the boss (3 = its hoard / secret)
DEPTH_POOL = {1: ((1, 1), 75), 2: ((1, 1), 45), 3: ((1, 1), 18), 4: ((1, 2), 6)}
# how common an item of a given depth is among the relic entries (the deepest gear stays the rarest)
ITEM_WEIGHT = {1: 10, 2: 6, 3: 3}


def loot_pools(table):
    """Extra pools for a structure chest table (gen_loot.table() appends them), or [] for other tables."""
    spec = TABLE_DEPTH.get(table)
    if not spec:
        return []
    structure, depth = spec
    rolls, empty = DEPTH_POOL[depth]
    entries = []
    for iid, d in STRUCTURE_GEAR[structure]:
        if d > depth:
            continue
        w = ITEM_WEIGHT[d] * (2 if depth == 4 and d == 3 else 1)
        e = {"type": "minecraft:item", "name": f"{NS}:{iid}", "weight": w}
        if depth >= 3 and iid not in ACCESSORIES:
            e["functions"] = [{"function": "minecraft:enchant_with_levels",
                               "levels": {"type": "minecraft:uniform", "min": 8, "max": 22},
                               "conditions": [{"condition": "minecraft:random_chance", "chance": 0.35}]}]
        entries.append(e)
    if not entries:
        return []
    entries.append({"type": "minecraft:empty", "weight": empty})
    return [{"rolls": {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]}, "bonus_rolls": 0.0,
             "entries": entries}]


# ------------------------------------------------------------------ gen_assets
def assets(write):
    """Equipment assets of the four sets (the layer textures come from relicart.textures())."""
    for prefix in SETS:
        write(f"equipment/{prefix}.json", {"layers": {
            "humanoid": [{"texture": f"{NS}:{prefix}"}],
            "humanoid_leggings": [{"texture": f"{NS}:{prefix}"}],
        }})


def held():
    """id -> held3d entry (archetype, material, handle, accent) for the weapons with a 3D model in hand."""
    return {wid: (w["held"], w["sprite"][0], w["sprite"][1], w["sprite"][2]) for wid, w in WEAPONS.items() if w["held"]}


def handheld():
    return set(WEAPONS)

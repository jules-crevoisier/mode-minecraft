"""Boss rewards: every great boss drops its Remembrance ("Souvenir"), which crafts into a unique weapon.

One row per boss, used by gen_java (registration), content (names), gen_textures (sprites),
gen_data (recipes, boss loot, tags) and gen_quests (the Legends chapter).

ability: WAVE (ring around you), BEAM (line ahead), DASH (rush through enemies), ERUPT (bursts along
a line), ROOT (snare around you), CLOUD (poison cloud where you look), LEAP (bound forward), ARC (wide
sweep), BLINK (teleport ahead and strike). flags: fire, slow, weak, blind, poison, lift, lifesteal.
"""

TIER_MATERIAL = {"overworld": "map_fragment", "depths": "lithite_shard", "nether": "ancient_ember", "end": "void_shard"}

# boss, tier, weapon id, weapon (en, fr), tooltip (en, fr), remembrance (en, fr),
# melee (tool material | None for staves, damage, speed), ability, power, size, cooldown, particle, flags,
# weapon sprite (shape, material, handle, accent), remembrance sprite material/accent
BOSS_GEAR = [
    ("drowned_warden", "depths", "kings_trident", ("Drowned King's Trident", "Trident du roi noyé"),
     ("Use: a tidal ring that slows every foe around you.", "Clic droit : un anneau de marée qui ralentit tous les ennemis autour."),
     ("Remembrance of the Drowned Warden", "Souvenir du Gardien englouti"),
     ("LITHITE", 6.0, -2.6), "WAVE", 9.0, 6.0, 80, "SPLASH", "slow", ("trident", "warden", "bone", "sapphire"), ("warden", "sapphire")),
    ("bell_keeper", "overworld", "bell_hammer", ("Bell Hammer", "Marteau-cloche"),
     ("Use: toll a ring of sound that staggers foes.", "Clic droit : un glas qui étourdit les ennemis autour."),
     ("Remembrance of the Bell Keeper", "Souvenir du Sonneur de glas"),
     ("LITHITE", 7.0, -3.2), "WAVE", 8.0, 7.0, 90, "CRIT", "slow", ("hammer", "gold", "dark", "gold"), ("gold", "gold")),
    ("archivist", "overworld", "forbidden_grimoire", ("Forbidden Grimoire", "Grimoire interdit"),
     ("Use: a beam of searing ink that blinds.", "Clic droit : un rayon d'encre brûlante qui aveugle."),
     ("Remembrance of the Archivist", "Souvenir de l'Archiviste"),
     None, "BEAM", 10.0, 16.0, 60, "ENCHANT", "blind", ("book", "map", "dark", "ink"), ("map", "ink")),
    ("sand_pharaoh", "overworld", "pharaoh_flail", ("Pharaoh's Flail", "Fléau du pharaon"),
     ("Use: sand pillars burst along a line and weaken foes.", "Clic droit : des piliers de sable jaillissent en ligne et affaiblissent."),
     ("Remembrance of the Sand Pharaoh", "Souvenir du Pharaon ensablé"),
     ("LITHITE", 6.0, -2.8), "ERUPT", 8.0, 10.0, 80, "POOF", "weak", ("mace", "gold", "gold", "sapphire"), ("gold", "sapphire")),
    ("jade_jaguar", "overworld", "jade_fang", ("Jade Fang", "Croc de jade"),
     ("Use: pounce forward, tearing through every foe.", "Clic droit : bondis en avant à travers les ennemis."),
     ("Remembrance of the Jade Jaguar", "Souvenir du Jaguar de jade"),
     ("LITHITE", 4.0, -1.8), "DASH", 8.0, 8.0, 50, "HAPPY_VILLAGER", "", ("blade", "lithite", "gold", "emerald"), ("lithite", "emerald")),
    ("root_mother", "overworld", "rootmother_staff", ("Root Mother's Staff", "Bâton de la Mère-Racine"),
     ("Use: roots seize and crush every foe around you.", "Clic droit : des racines saisissent et broient les ennemis autour."),
     ("Remembrance of the Root Mother", "Souvenir de la Mère-Racine"),
     None, "ROOT", 6.0, 6.0, 100, "SPORE_BLOSSOM_AIR", "slow", ("staff", "leather", "wood", "emerald"), ("leather", "emerald")),
    ("swamp_crone", "overworld", "crone_ladle", ("Crone's Ladle", "Louche de la sorcière"),
     ("Use: splash a lingering poison brew where you look.", "Clic droit : répand un brouet empoisonné là où tu regardes."),
     ("Remembrance of the Swamp Crone", "Souvenir de la Grand-Mère du marais"),
     ("CARTOGRAPHER", 4.0, -2.4), "CLOUD", 4.0, 4.0, 100, "WITCH", "poison", ("mace", "iron", "dark", "amethyst"), ("iron", "amethyst")),
    ("gryphon_knight", "overworld", "gryphon_lance", ("Gryphon Lance", "Lance du griffon"),
     ("Use: bound forward on the wind, scattering foes.", "Clic droit : bondis porté par le vent en dispersant les ennemis."),
     ("Remembrance of the Gryphon Knight", "Souvenir du Chevalier-griffon"),
     ("LITHITE", 5.0, -2.6), "LEAP", 8.0, 4.0, 70, "CLOUD", "", ("lance", "iron", "gold", "sapphire"), ("iron", "sapphire")),
    ("rune_colossus", "overworld", "rune_fist", ("Rune Fist", "Poing runique"),
     ("Use: a huge rune shockwave.", "Clic droit : une immense onde de choc runique."),
     ("Remembrance of the Rune Colossus", "Souvenir du Colosse runique"),
     ("LITHITE", 7.0, -3.4), "WAVE", 10.0, 8.0, 110, "GLOW", "lift", ("fist", "lithite", "dark", "sapphire"), ("lithite", "sapphire")),
    ("forge_king", "depths", "forge_king_hammer", ("Forge King's Hammer", "Marteau du Roi-Forgeron"),
     ("Use: a molten shockwave that sets foes ablaze.", "Clic droit : une onde de métal en fusion qui embrase les ennemis."),
     ("Remembrance of the Forge King", "Souvenir du Roi-Forgeron"),
     ("EMBER", 7.0, -3.2), "WAVE", 11.0, 6.0, 90, "FLAME", "fire", ("hammer", "ember", "dark", "gold"), ("ember", "gold")),
    ("crystal_spider", "depths", "crystal_fang", ("Crystal Fang", "Croc de cristal"),
     ("Use: crystal spikes burst along a line.", "Clic droit : des pics de cristal jaillissent en ligne."),
     ("Remembrance of the Crystal Matriarch", "Souvenir de la Matriarche de cristal"),
     ("LITHITE", 5.0, -2.4), "ERUPT", 10.0, 10.0, 80, "ELECTRIC_SPARK", "", ("spear", "void", "bone", "amethyst"), ("void", "amethyst")),
    ("sculk_spawn", "depths", "sculk_horn", ("Sculk Horn", "Corne du sculk"),
     ("Use: a sonic blast that pierces everything ahead.", "Clic droit : une déflagration sonique qui transperce tout devant toi."),
     ("Remembrance of the Sculk Spawn", "Souvenir du Rejeton du sculk"),
     None, "BEAM", 14.0, 20.0, 120, "SONIC_BOOM", "", ("horn", "warden", "bone", "sapphire"), ("warden", "sapphire")),
    ("ash_lord", "nether", "ash_greatsword", ("Ash Greatsword", "Espadon des Cendres"),
     ("Use: a wide flaming sweep.", "Clic droit : un large balayage enflammé."),
     ("Remembrance of the Ash Lord", "Souvenir du Seigneur des Cendres"),
     ("EMBER", 8.0, -3.0), "ARC", 12.0, 6.0, 70, "FLAME", "fire", ("greatsword", "ember", "dark", "ember"), ("ember", "ember")),
    ("piglin_king", "nether", "golden_mace", ("Golden Mace", "Masse dorée"),
     ("Use: a golden quake that hurls foes into the air.", "Clic droit : un séisme doré qui projette les ennemis en l'air."),
     ("Remembrance of the Golden Piglin King", "Souvenir du Roi piglin doré"),
     ("EMBER", 8.0, -3.4), "WAVE", 12.0, 6.0, 90, "WAX_ON", "lift", ("mace", "gold", "gold", "ruby"), ("gold", "ruby")),
    ("soul_reaper", "nether", "soul_scythe", ("Soul Scythe", "Faux des âmes"),
     ("Use: reap souls in a wide arc and drink their life.", "Clic droit : fauche les âmes en arc large et draine leur vie."),
     ("Remembrance of the Soul Reaper", "Souvenir de la Faucheuse des âmes"),
     ("EMBER", 7.0, -2.8), "ARC", 11.0, 6.0, 60, "SOUL_FIRE_FLAME", "lifesteal", ("scythe", "void", "bone", "ice"), ("void", "ice")),
    ("void_warden", "end", "void_greatblade", ("Void Greatblade", "Grande lame du vide"),
     ("Use: blink ahead and cleave everything around you.", "Clic droit : téléporte-toi en avant et fends tout autour de toi."),
     ("Remembrance of the Void Warden", "Souvenir du Gardien du vide"),
     ("VOID", 9.0, -3.0), "BLINK", 14.0, 12.0, 80, "REVERSE_PORTAL", "", ("greatsword", "void", "purpur", "amethyst"), ("void", "amethyst")),
    ("grand_clockmaker", "overworld", "clockmaker_pendulum", ("Clockmaker's Pendulum", "Pendule du Grand Horloger"),
     ("Use: a pendulum sweep that slows foes as if time stood still.",
      "Clic droit : un balancier qui ralentit les ennemis comme si le temps s'arrêtait."),
     ("Remembrance of the Grand Clockmaker", "Souvenir du Grand Horloger"),
     ("LITHITE", 6.0, -2.6), "ARC", 10.0, 6.0, 70, "ELECTRIC_SPARK", "slow", ("cane", "brass", "dark", "aether"),
     ("brass", "aether")),
]


def remembrance_id(boss):
    return f"remembrance_{boss}"

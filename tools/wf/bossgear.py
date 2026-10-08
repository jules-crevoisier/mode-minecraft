"""Boss rewards: every great boss drops its Remembrance ("Souvenir"), which crafts into a unique weapon.

One row per boss, used by gen_java (registration), content (names), gen_textures (sprites),
gen_data (recipes, boss loot, tags) and gen_quests (the Legends chapter).

ability: WAVE (ring around you), BEAM (line ahead), DASH (rush through enemies), ERUPT (bursts along
a line), ROOT (snare around you), CLOUD (poison cloud where you look), LEAP (bound forward), ARC (wide
sweep), BLINK (teleport ahead and strike), HOOK (a chain
thrown ahead drags the first foe to you), SHARDS (a fan of piercing shards ahead), BREATH (a cone of frost
breath ahead that freezes foes solid), TIDE (a breaking wave ahead that sweeps foes along), PRESSURE (a
steam blast round you that only reaches foes in your line of sight, stronger up close), BROADSIDE (a cannon
shell along your aim that bursts with splash damage on the first foe or wall), PRISM (a sunray along your aim
that glances off block faces up to 3 times), CAGE (a root lash along your aim that cages the first foe and
whips the foes beside it). flags: fire, slow, weak, blind, poison, lift, lifesteal.
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
     ("LITHITE", 7.0, -3.2), "WAVE", 8.0, 7.0, 90, "CRIT", "slow", ("bell_hammer", "gold", "dark", "gold"), ("gold", "gold")),
    ("archivist", "overworld", "forbidden_grimoire", ("Forbidden Grimoire", "Grimoire interdit"),
     ("Use: a beam of searing ink that blinds.", "Clic droit : un rayon d'encre brûlante qui aveugle."),
     ("Remembrance of the Archivist", "Souvenir de l'Archiviste"),
     None, "BEAM", 10.0, 16.0, 60, "ENCHANT", "blind", ("grimoire", "map", "dark", "amethyst"), ("map", "ink")),
    ("sand_pharaoh", "overworld", "pharaoh_flail", ("Pharaoh's Flail", "Fléau du pharaon"),
     ("Use: sand pillars burst along a line and weaken foes.", "Clic droit : des piliers de sable jaillissent en ligne et affaiblissent."),
     ("Remembrance of the Sand Pharaoh", "Souvenir du Pharaon ensablé"),
     ("LITHITE", 6.0, -2.8), "ERUPT", 8.0, 10.0, 80, "POOF", "weak", ("flail", "gold", "gold", "sapphire"), ("gold", "sapphire")),
    ("jade_jaguar", "overworld", "jade_fang", ("Jade Fang", "Croc de jade"),
     ("Use: pounce forward, tearing through every foe.", "Clic droit : bondis en avant à travers les ennemis."),
     ("Remembrance of the Jade Jaguar", "Souvenir du Jaguar de jade"),
     ("LITHITE", 4.0, -1.8), "DASH", 8.0, 8.0, 50, "HAPPY_VILLAGER", "", ("blade", "lithite", "gold", "emerald"), ("lithite", "emerald")),
    ("root_mother", "overworld", "rootmother_staff", ("Root Mother's Staff", "Bâton de la Mère-Racine"),
     ("Use: roots seize and crush every foe around you.", "Clic droit : des racines saisissent et broient les ennemis autour."),
     ("Remembrance of the Root Mother", "Souvenir de la Mère-Racine"),
     None, "ROOT", 6.0, 6.0, 100, "SPORE_BLOSSOM_AIR", "slow", ("staff_root", "leather", "wood", "emerald"), ("leather", "emerald")),
    ("swamp_crone", "overworld", "crone_ladle", ("Crone's Ladle", "Louche de la sorcière"),
     ("Use: splash a lingering poison brew where you look.", "Clic droit : répand un brouet empoisonné là où tu regardes."),
     ("Remembrance of the Swamp Crone", "Souvenir de la Grand-Mère du marais"),
     ("CARTOGRAPHER", 4.0, -2.4), "CLOUD", 4.0, 4.0, 100, "WITCH", "poison", ("ladle", "iron", "dark", "amethyst"), ("iron", "amethyst")),
    ("gryphon_knight", "overworld", "gryphon_lance", ("Gryphon Lance", "Lance du griffon"),
     ("Use: bound forward on the wind, scattering foes.", "Clic droit : bondis porté par le vent en dispersant les ennemis."),
     ("Remembrance of the Gryphon Knight", "Souvenir du Chevalier-griffon"),
     ("LITHITE", 5.0, -2.6), "LEAP", 8.0, 4.0, 70, "CLOUD", "", ("lance", "iron", "gold", "sapphire"), ("iron", "sapphire")),
    ("rune_colossus", "overworld", "rune_fist", ("Rune Fist", "Poing runique"),
     ("Use: a huge rune shockwave.", "Clic droit : une immense onde de choc runique."),
     ("Remembrance of the Rune Colossus", "Souvenir du Colosse runique"),
     ("LITHITE", 7.0, -3.4), "WAVE", 10.0, 8.0, 110, "GLOW", "lift", ("gauntlet", "lithite", "dark", "sapphire"), ("lithite", "sapphire")),
    ("forge_king", "depths", "forge_king_hammer", ("Forge King's Hammer", "Marteau du Roi-Forgeron"),
     ("Use: a molten shockwave that sets foes ablaze.", "Clic droit : une onde de métal en fusion qui embrase les ennemis."),
     ("Remembrance of the Forge King", "Souvenir du Roi-Forgeron"),
     ("EMBER", 7.0, -3.2), "WAVE", 11.0, 6.0, 90, "FLAME", "fire", ("forge_hammer", "ember", "dark", "gold"), ("ember", "gold")),
    ("crystal_spider", "depths", "crystal_fang", ("Crystal Fang", "Croc de cristal"),
     ("Use: crystal spikes burst along a line.", "Clic droit : des pics de cristal jaillissent en ligne."),
     ("Remembrance of the Crystal Matriarch", "Souvenir de la Matriarche de cristal"),
     ("LITHITE", 5.0, -2.4), "ERUPT", 10.0, 10.0, 80, "ELECTRIC_SPARK", "", ("crystal_spear", "void", "bone", "amethyst"), ("void", "amethyst")),
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
     ("LITHITE", 6.0, -2.6), "ARC", 10.0, 6.0, 70, "ELECTRIC_SPARK", "slow", ("pendulum", "brass", "dark", "aether"),
     ("brass", "aether")),
    ("iron_helmsman", "overworld", "helmsman_anchor", ("Helmsman's Anchor", "Ancre du Timonier"),
     ("Use: the anchor crashes down and a broadside of bursts tears along the line ahead, setting foes ablaze.",
      "Clic droit : l'ancre s'abat et une bordée d'explosions déchire la ligne devant toi, embrasant les ennemis."),
     ("Remembrance of the Iron Helmsman", "Souvenir du Timonier de Fer"),
     ("LITHITE", 8.0, -3.4), "ERUPT", 11.0, 12.0, 90, "LARGE_SMOKE", "fire", ("anchor", "iron", "dark", "ember"),
     ("iron", "ember")),
    ("bronze_sentinel", "overworld", "sentinel_greatsword", ("Greatsword of the Sentinel", "Espadon de la Sentinelle"),
     ("Use: the greatsword cleaves the ground and a crack of rune light tears along the line ahead, hurling foes up.",
      "Clic droit : l'espadon fend le sol et une fissure de lumière runique déchire la ligne devant toi en projetant les ennemis."),
     ("Remembrance of the Bronze Sentinel", "Souvenir de la Sentinelle d'airain"),
     ("LITHITE", 8.0, -3.2), "ERUPT", 11.0, 12.0, 80, "WAX_ON", "lift", ("greatsword", "copper", "dark", "emerald"),
     ("copper", "emerald")),
    ("dune_king", "overworld", "dune_king_crook", ("Crook of the Dune King", "Crosse du Roi des dunes"),
     ("Use: a low beam of judgement lances ahead, burning foes and dragging their steps.",
      "Clic droit : un rayon de jugement file devant toi, brûle les ennemis et alourdit leurs pas."),
     ("Remembrance of the Dune King", "Souvenir du Roi des dunes"),
     None, "BEAM", 12.0, 16.0, 90, "END_ROD", "slow", ("cane", "gold", "gold", "sapphire"), ("gold", "sapphire")),
    ("chained_jailer", "nether", "jailer_chain", ("Jailer's Burning Chain", "Chaîne ardente du Geôlier"),
     ("Use: hurl the chain ahead; the first foe it catches is dragged to your feet and set ablaze.",
      "Clic droit : lance la chaîne devant toi ; le premier ennemi qu'elle attrape est traîné à tes pieds et embrasé."),
     ("Remembrance of the Chained Jailer", "Souvenir du Geôlier enchaîné"),
     ("EMBER", 7.0, -2.9), "HOOK", 12.0, 14.0, 80, "FLAME", "fire", ("chain_flail", "ember", "dark", "ember"),
     ("ember", "ember")),
    ("oathbound_gatekeeper", "overworld", "gatekeeper_key", ("Key of the Kneeling Gate", "Clé de la Porte agenouillée"),
     ("Use: turn the key in the floor; stone hands punch up all around you, hurling foes into the air, and the oath "
      "wards you (Resistance II, 4 s).",
      "Clic droit : tourne la clé dans le sol ; des mains de pierre jaillissent tout autour de toi et projettent les "
      "ennemis en l'air, et le serment te protège (Résistance II, 4 s)."),
     ("Remembrance of the Oathbound Gatekeeper", "Souvenir du Gardien du Serment"),
     ("LITHITE", 8.0, -3.2), "WARD", 10.0, 5.0, 100, "SOUL_FIRE_FLAME", "lift", ("gate_key", "gold", "dark", "aether"),
     ("gold", "aether")),
    ("fallen_seraph", "end", "halo_glaive", ("Glaive of the Broken Halo", "Glaive du Halo brisé"),
     ("Use: fling a fan of five halo shards ahead; they pierce every foe in their path and blind it.",
      "Clic droit : lance un éventail de cinq éclats de halo ; ils transpercent tous les ennemis sur leur passage et les aveuglent."),
     ("Remembrance of the Fallen Seraph", "Souvenir du Séraphin déchu"),
     ("VOID", 8.0, -2.9), "SHARDS", 12.0, 16.0, 80, "END_ROD", "blind", ("scythe", "light", "purpur", "gold"),
     ("light", "amethyst")),
    ("caldera_castellan", "overworld", "caldera_halberd", ("Halberd of the Caldera", "Hallebarde de la caldeira"),
     ("Use: drive the halberd into the ground; a molten rift runs along it and forks, searing every foe on it.",
      "Clic droit : plante la hallebarde dans le sol ; une faille de magma court devant toi et se divise, brûlant tous les ennemis dessus."),
     ("Remembrance of the Castellan", "Souvenir du Châtelain"),
     ("LITHITE", 8.0, -3.1), "RIFT", 11.0, 12.0, 85, "FLAME", "fire,slow", ("halberd", "obsidian", "dark", "ember"),
     ("obsidian", "ember")),
    ("frost_jarl", "overworld", "jarl_axe", ("Bearded Axe of the Frost Jarl", "Hache barbue du Jarl de givre"),
     ("Use: breathe the jarl's winter; a cone of frost ahead hurts every foe in it and freezes it solid for 2 s.",
      "Clic droit : souffle l'hiver du jarl ; un cône de givre blesse tous les ennemis devant toi et les gèle sur place 2 s."),
     ("Remembrance of the Frost Jarl", "Souvenir du Jarl de givre"),
     ("LITHITE", 8.0, -3.1), "BREATH", 10.0, 9.0, 90, "SNOWFLAKE", "slow", ("dane_axe", "frost", "dark", "ice"),
     ("frost", "ice")),
    ("storm_ascetic", "overworld", "ascetic_staff", ("Staff of the Storm Ascetic", "Bâton de l'Ascète des tempêtes"),
     ("Use: strike the staff on the ground; a gust hurls every foe around you away and lightning falls on the three "
      "nearest.",
      "Clic droit : frappe le sol du bâton ; une rafale repousse tous les ennemis autour de toi et la foudre tombe sur "
      "les trois plus proches."),
     ("Remembrance of the Storm Ascetic", "Souvenir de l'Ascète des tempêtes"),
     ("LITHITE", 7.0, -2.6), "TEMPEST", 10.0, 6.0, 90, "ELECTRIC_SPARK", "", ("staff_storm", "storm", "wood", "ice"),
     ("storm", "ice")),
    ("tide_abbess", "overworld", "abbess_crozier", ("Crozier of the Drowned Abbess", "Crosse de l'Abbesse noyée"),
     ("Use: strike the crozier down; a breaking wave rolls ahead and sweeps every foe in it along, and the sea "
      "carries you (Dolphin's Grace, 6 s).",
      "Clic droit : frappe le sol de la crosse ; une vague déferle devant toi et emporte tous les ennemis sur son "
      "passage, et la mer te porte (Grâce du dauphin, 6 s)."),
     ("Remembrance of the Abbess", "Souvenir de l'Abbesse"),
     ("LITHITE", 7.0, -2.9), "TIDE", 10.0, 12.0, 90, "SPLASH", "slow", ("crozier", "warden", "dark", "aether"),
     ("warden", "aether")),
    ("abyssal_architect", "overworld", "architect_plumb", ("Plumb of the Abyssal Architect", "Fil à plomb de l'Architecte de l'abîme"),
     ("Use: let the plumb-bob fall from on high onto the spot you aim at (up to 16 blocks); it crushes every foe "
      "within 2.5 blocks of it and pins them to the ground for 2 s.",
      "Clic droit : laisse tomber le plomb de très haut sur le point visé (jusqu'à 16 blocs) ; il écrase tous les "
      "ennemis à 2,5 blocs et les cloue au sol 2 s."),
     ("Remembrance of the Architect", "Souvenir de l'Architecte"),
     ("LITHITE", 8.0, -3.0), "PLUMB", 12.0, 16.0, 90, "SOUL", "slow", ("plumb", "iron", "dark", "aether"),
     ("iron", "aether")),
    ("lock_master", "overworld", "pressure_lance", ("Pressure-Lance of the Lock-Master", "Lance à pression du Maître des écluses"),
     ("Use: open the nozzle; a high-pressure jet of water shoots 14 blocks along your aim (walls stop it), hurts every "
      "foe in it and hurls it to the far end; the recoil pushes you a step back and puts out fire.",
      "Clic droit : ouvre la buse ; un jet d'eau sous pression file sur 14 blocs dans ta visée (les murs l'arrêtent), "
      "blesse tous les ennemis sur son passage et les projette au bout ; le recul te repousse d'un pas et t'éteint."),
     ("Remembrance of the Lock-Master", "Souvenir du Maître des écluses"),
     ("LITHITE", 8.0, -3.0), "JET", 11.0, 14.0, 80, "SPLASH", "", ("lance", "brass", "dark", "aether"),
     ("brass", "aether")),
    ("bog_hierophant", "overworld", "hierophant_crozier", ("Lantern-Crozier of the Bog Hierophant",
                                                          "Crosse-lanterne du Hiérophante des tourbières"),
     ("Use: swing the lantern toward a spot up to 12 blocks away; the bog opens there, drags every foe within 4 blocks "
      "into its heart, holds them fast for 3 s and a poison bloom bursts on them.",
      "Clic droit : balance la lanterne vers un point jusqu'à 12 blocs ; la tourbière s'y ouvre, attire tous les "
      "ennemis à 4 blocs en son cœur, les retient 3 s et une floraison de poison éclate sur eux."),
     ("Remembrance of the Hierophant", "Souvenir du Hiérophante"),
     ("LITHITE", 8.0, -3.0), "MIRE", 9.0, 12.0, 100, "SPORE_BLOSSOM_AIR", "poison,slow", ("crozier", "leather", "dark", "emerald"),
     ("leather", "emerald")),
    ("strangler_queen", "overworld", "queen_macuahuitl", ("Jade Macuahuitl of the Strangler Queen",
                                                         "Macuahuitl de jade de la Reine-figuier"),
     ("Use: crack a lash of living root along your aim (up to 14 blocks); the first foe it meets is caged where it "
      "stands, held fast for 3 s and weakened, and the cage's thorns whip every other foe within 3 blocks, dragging "
      "them against the bars for half damage.",
      "Clic droit : fais claquer un fouet de racine vivante dans ta visée (jusqu'à 14 blocs) ; le premier ennemi "
      "touché est mis en cage sur place, retenu 3 s et affaibli, et les épines de la cage fouettent tous les autres "
      "ennemis à 3 blocs, les plaquant contre les barreaux pour moitié moins de dégâts."),
     ("Remembrance of the Strangler Queen", "Souvenir de la Reine-figuier"),
     ("LITHITE", 8.0, -3.0), "CAGE", 10.0, 14.0, 90, "HAPPY_VILLAGER", "", ("macuahuitl", "lithite", "wood", "gold"),
     ("lithite", "emerald")),
    ("solar_hierarch", "overworld", "hierarch_sunstaff", ("Sun-Staff of the Solar Hierarch", "Bâton solaire du Hiérarque"),
     ("Use: loose a ray of focused sunlight along your aim; it glances off walls, floors and ceilings like light off a "
      "mirror (up to 3 bounces, 24 blocks in all), burns every foe it crosses once and grows a quarter hotter with "
      "each bounce.",
      "Clic droit : décoche un rayon de soleil concentré dans ta visée ; il ricoche sur les murs, sols et plafonds "
      "comme la lumière sur un miroir (jusqu'à 3 rebonds, 24 blocs en tout), brûle une fois chaque ennemi traversé "
      "et chauffe d'un quart de plus à chaque rebond."),
     ("Remembrance of the Hierarch", "Souvenir du Hiérarque"),
     ("LITHITE", 8.0, -3.0), "PRISM", 10.0, 24.0, 90, "END_ROD", "fire", ("sunstaff", "gold", "gold", "ember"),
     ("gold", "ember")),
    ("drowned_admiral", "overworld", "admiral_cutlass", ("Boarding Cutlass of the Drowned Admiral",
                                                         "Sabre d'abordage de l'Amiral noyé"),
     ("Use: fire the deck cannon along your aim; the shell bursts on the first foe or wall it meets (up to 24 blocks): "
      "full damage within 1 block of the burst, half at 3.5, foes hurled away and set ablaze; the recoil kicks you a "
      "step back.",
      "Clic droit : tire au canon de pont dans ta visée ; l'obus éclate sur le premier ennemi ou mur rencontré (jusqu'à "
      "24 blocs) : pleins dégâts à 1 bloc de l'explosion, moitié à 3,5, ennemis projetés et enflammés ; le recul te "
      "repousse d'un pas."),
     ("Remembrance of the Admiral", "Souvenir de l'Amiral"),
     ("LITHITE", 7.0, -2.4), "BROADSIDE", 13.0, 24.0, 100, "LARGE_SMOKE", "fire", ("cutlass", "iron", "dark", "aether"),
     ("brass", "aether")),
    ("turbine_tyrant", "overworld", "tyrant_wrench", ("Valve-Wrench of the Turbine Tyrant", "Clé à vanne du Tyran des turbines"),
     ("Use: open the valve; a blast of scalding steam bursts from you and hurls away every foe you can see within 8 "
      "blocks (walls shield them), full force up close, half at the edge, and the overload speeds you up for 3 s.",
      "Clic droit : ouvre la vanne ; un jet de vapeur brûlante jaillit de toi et repousse tous les ennemis que tu vois "
      "à 8 blocs (les murs les protègent), pleine force de près, moitié au bord, et la surpression t'accélère 3 s."),
     ("Remembrance of the Turbine Tyrant", "Souvenir du Tyran des turbines"),
     ("LITHITE", 8.0, -3.0), "PRESSURE", 12.0, 8.0, 100, "CLOUD", "fire", ("valve_wrench", "iron", "dark", "ember"),
     ("brass", "ember")),
]


def remembrance_id(boss):
    return f"remembrance_{boss}"

"""Talent tree: 4 branches of RPG talents, baked into GeneratedSkills.java and the lang files.

Each skill: (id, branch, (col, row), cost, [required ids], icon item, (name en, fr), (desc en, fr), effect)
effect kinds:
  ("attr", "<Attributes field>", amount, "add" | "base_mult" | "total_mult")   passive attribute bonus
  ("mana", amount)        +max mana          ("regen", fraction)   +mana regeneration
  ("power", fraction)     +spell power       ("thrift", fraction)  -spell cost
  ("lifesteal", fraction) heal on melee hit  ("repair", seconds)   slowly repairs the held item
  ("active", "<ability>") capstone: an ability used with the V key
Points come from quests (1 each), bosses (3) and every 10 experience levels earned.
"""

BRANCHES = [
    ("warrior", "minecraft:iron_sword", 0xFFE0483B, ("Warrior", "Guerrier")),
    ("explorer", "minecraft:compass", 0xFF5BD14A, ("Explorer", "Explorateur")),
    ("arcanist", "minecraft:amethyst_shard", 0xFFB98BE8, ("Arcanist", "Arcaniste")),
    ("engineer", "minecraft:copper_ingot", 0xFFF6C343, ("Engineer", "Mécaniste")),
]

SKILLS = [
    # ------------------------------------------------------------------ warrior
    ("w_vigor_1", "warrior", (1, 0), 1, [], "minecraft:apple", ("Vigour I", "Vigueur I"),
     ("+2 max health.", "+2 points de vie max."), ("attr", "MAX_HEALTH", 2.0, "add")),
    ("w_might_1", "warrior", (0, 1), 1, ["w_vigor_1"], "minecraft:iron_sword", ("Might I", "Puissance I"),
     ("+1 melee damage.", "+1 dégât au corps à corps."), ("attr", "ATTACK_DAMAGE", 1.0, "add")),
    ("w_guard_1", "warrior", (2, 1), 1, ["w_vigor_1"], "minecraft:shield", ("Guard", "Garde"),
     ("+2 armour.", "+2 points d'armure."), ("attr", "ARMOR", 2.0, "add")),
    ("w_vigor_2", "warrior", (1, 2), 2, ["w_might_1", "w_guard_1"], "minecraft:golden_apple", ("Vigour II", "Vigueur II"),
     ("+4 max health.", "+4 points de vie max."), ("attr", "MAX_HEALTH", 4.0, "add")),
    ("w_might_2", "warrior", (0, 3), 2, ["w_vigor_2"], "minecraft:diamond_sword", ("Might II", "Puissance II"),
     ("+2 melee damage.", "+2 dégâts au corps à corps."), ("attr", "ATTACK_DAMAGE", 2.0, "add")),
    ("w_bulwark", "warrior", (2, 3), 2, ["w_vigor_2"], "minecraft:iron_chestplate", ("Bulwark", "Rempart"),
     ("+2 armour toughness and +20% knockback resistance.", "+2 de robustesse et +20 % de résistance au recul."),
     ("attr", "ARMOR_TOUGHNESS", 2.0, "add")),
    ("w_lifesteal", "warrior", (0, 4), 3, ["w_might_2"], "minecraft:redstone", ("Bloodthirst", "Soif de sang"),
     ("Melee hits heal you for 8% of the damage dealt.", "Tes coups au corps à corps te soignent de 8 % des dégâts."),
     ("lifesteal", 0.08)),
    ("w_haste", "warrior", (2, 4), 2, ["w_bulwark"], "minecraft:feather", ("Swift Blade", "Lame vive"),
     ("+10% attack speed.", "+10 % de vitesse d'attaque."), ("attr", "ATTACK_SPEED", 0.10, "base_mult")),
    ("w_fury", "warrior", (1, 5), 4, ["w_lifesteal", "w_haste"], "minecraft:blaze_powder", ("Fury", "Fureur"),
     ("Active (V): 10 seconds of Strength II and Speed. Cooldown 60s.",
      "Actif (V) : 10 secondes de Force II et de Vitesse. Recharge 60 s."), ("active", "fury")),

    # ------------------------------------------------------------------ explorer
    ("e_swift_1", "explorer", (1, 0), 1, [], "minecraft:sugar", ("Light Step I", "Pas léger I"),
     ("+5% movement speed.", "+5 % de vitesse de déplacement."), ("attr", "MOVEMENT_SPEED", 0.05, "base_mult")),
    ("e_feather", "explorer", (0, 1), 1, ["e_swift_1"], "minecraft:feather", ("Feather Fall", "Chute de plume"),
     ("+4 blocks before taking fall damage.", "+4 blocs avant de subir des dégâts de chute."),
     ("attr", "SAFE_FALL_DISTANCE", 4.0, "add")),
    ("e_lungs", "explorer", (2, 1), 1, ["e_swift_1"], "minecraft:turtle_scute", ("Deep Breath", "Grande inspiration"),
     ("Hold your breath much longer underwater.", "Retiens ton souffle bien plus longtemps sous l'eau."),
     ("attr", "OXYGEN_BONUS", 2.0, "add")),
    ("e_swift_2", "explorer", (1, 2), 2, ["e_feather", "e_lungs"], "minecraft:rabbit_foot", ("Light Step II", "Pas léger II"),
     ("+7% movement speed and higher jumps.", "+7 % de vitesse et des sauts plus hauts."),
     ("attr", "MOVEMENT_SPEED", 0.07, "base_mult")),
    ("e_reach", "explorer", (0, 3), 2, ["e_swift_2"], "minecraft:spyglass", ("Long Arms", "Bras longs"),
     ("+1.5 block reach.", "+1,5 bloc de portée."), ("attr", "BLOCK_INTERACTION_RANGE", 1.5, "add")),
    ("e_luck", "explorer", (2, 3), 2, ["e_swift_2"], "minecraft:emerald", ("Treasure Hunter", "Chasseur de trésors"),
     ("+2 luck: better loot in chests.", "+2 de chance : meilleur butin dans les coffres."), ("attr", "LUCK", 2.0, "add")),
    ("e_climber", "explorer", (0, 4), 2, ["e_reach"], "minecraft:scaffolding", ("Climber", "Grimpeur"),
     ("Step up full blocks without jumping.", "Monte les marches d'un bloc sans sauter."), ("attr", "STEP_HEIGHT", 0.5, "add")),
    ("e_water", "explorer", (2, 4), 2, ["e_luck"], "minecraft:heart_of_the_sea", ("Swimmer", "Nageur"),
     ("Move much faster in water.", "Déplace-toi bien plus vite dans l'eau."),
     ("attr", "WATER_MOVEMENT_EFFICIENCY", 0.5, "add")),
    ("e_dash", "explorer", (1, 5), 4, ["e_climber", "e_water"], "minecraft:wind_charge", ("Dash", "Ruée"),
     ("Active (V): dash forward 8 blocks. Cooldown 8s.", "Actif (V) : ruée de 8 blocs vers l'avant. Recharge 8 s."),
     ("active", "dash")),

    # ------------------------------------------------------------------ arcanist
    ("a_mana_1", "arcanist", (1, 0), 1, [], "minecraft:lapis_lazuli", ("Mana Well I", "Puits de mana I"),
     ("+25 max mana.", "+25 de mana max."), ("mana", 25)),
    ("a_regen_1", "arcanist", (0, 1), 1, ["a_mana_1"], "minecraft:glow_berries", ("Flow I", "Flux I"),
     ("Mana regenerates 30% faster.", "Le mana se régénère 30 % plus vite."), ("regen", 0.30)),
    ("a_power_1", "arcanist", (2, 1), 1, ["a_mana_1"], "minecraft:blaze_rod", ("Spellpower I", "Puissance magique I"),
     ("Spells deal and heal 15% more.", "Les sorts infligent et soignent 15 % de plus."), ("power", 0.15)),
    ("a_mana_2", "arcanist", (1, 2), 2, ["a_regen_1", "a_power_1"], "minecraft:amethyst_shard", ("Mana Well II", "Puits de mana II"),
     ("+50 max mana.", "+50 de mana max."), ("mana", 50)),
    ("a_thrift", "arcanist", (0, 3), 2, ["a_mana_2"], "minecraft:glass_bottle", ("Thrift", "Économie"),
     ("Spells cost 20% less mana.", "Les sorts coûtent 20 % de mana en moins."), ("thrift", 0.20)),
    ("a_power_2", "arcanist", (2, 3), 2, ["a_mana_2"], "minecraft:fire_charge", ("Spellpower II", "Puissance magique II"),
     ("Spells deal and heal 25% more.", "Les sorts infligent et soignent 25 % de plus."), ("power", 0.25)),
    ("a_regen_2", "arcanist", (0, 4), 2, ["a_thrift"], "minecraft:experience_bottle", ("Flow II", "Flux II"),
     ("Mana regenerates 50% faster.", "Le mana se régénère 50 % plus vite."), ("regen", 0.50)),
    ("a_mana_3", "arcanist", (2, 4), 3, ["a_power_2"], "minecraft:end_crystal", ("Mana Well III", "Puits de mana III"),
     ("+75 max mana.", "+75 de mana max."), ("mana", 75)),
    ("a_shield", "arcanist", (1, 5), 4, ["a_regen_2", "a_mana_3"], "minecraft:totem_of_undying", ("Arcane Shield", "Bouclier arcanique"),
     ("Active (V): absorb 12 damage for 15 seconds. Cooldown 45s.",
      "Actif (V) : absorbe 12 dégâts pendant 15 secondes. Recharge 45 s."), ("active", "shield")),

    # ------------------------------------------------------------------ engineer
    ("m_miner_1", "engineer", (1, 0), 1, [], "minecraft:iron_pickaxe", ("Efficient I", "Efficace I"),
     ("Mine 15% faster.", "Mine 15 % plus vite."), ("attr", "BLOCK_BREAK_SPEED", 0.15, "base_mult")),
    ("m_plating", "engineer", (0, 1), 1, ["m_miner_1"], "minecraft:copper_ingot", ("Riveted Plates", "Plaques rivetées"),
     ("+2 armour.", "+2 points d'armure."), ("attr", "ARMOR", 2.0, "add")),
    ("m_tinker", "engineer", (2, 1), 1, ["m_miner_1"], "minecraft:anvil", ("Tinkerer", "Bricoleur"),
     ("The item in your hand slowly repairs itself (1 point every 20s).",
      "L'objet en main se répare tout seul (1 point toutes les 20 s)."), ("repair", 20)),
    ("m_miner_2", "engineer", (1, 2), 2, ["m_plating", "m_tinker"], "minecraft:diamond_pickaxe", ("Efficient II", "Efficace II"),
     ("Mine 25% faster.", "Mine 25 % plus vite."), ("attr", "BLOCK_BREAK_SPEED", 0.25, "base_mult")),
    ("m_tough", "engineer", (0, 3), 2, ["m_miner_2"], "minecraft:netherite_scrap", ("Hardened", "Endurci"),
     ("+2 armour toughness.", "+2 de robustesse d'armure."), ("attr", "ARMOR_TOUGHNESS", 2.0, "add")),
    ("m_reach", "engineer", (2, 3), 2, ["m_miner_2"], "minecraft:piston", ("Extended Arm", "Bras télescopique"),
     ("+1 block and creature reach.", "+1 bloc de portée sur les blocs et les créatures."),
     ("attr", "ENTITY_INTERACTION_RANGE", 1.0, "add")),
    ("m_tinker_2", "engineer", (0, 4), 2, ["m_tough"], "minecraft:smithing_table", ("Master Tinkerer", "Maître bricoleur"),
     ("The item in your hand repairs faster (1 point every 6s).",
      "L'objet en main se répare plus vite (1 point toutes les 6 s)."), ("repair", 6)),
    ("m_knock", "engineer", (2, 4), 2, ["m_reach"], "minecraft:iron_block", ("Steady", "Stable"),
     ("+40% knockback resistance.", "+40 % de résistance au recul."), ("attr", "KNOCKBACK_RESISTANCE", 0.4, "add")),
    ("m_overdrive", "engineer", (1, 5), 4, ["m_tinker_2", "m_knock"], "minecraft:redstone_block", ("Overdrive", "Surcharge"),
     ("Active (V): 15 seconds of Haste III and Resistance. Cooldown 60s.",
      "Actif (V) : 15 secondes de Célérité III et de Résistance. Recharge 60 s."), ("active", "overdrive")),
]


def lang():
    en, fr = {}, {}
    for bid, _icon, _color, (ben, bfr) in BRANCHES:
        en[f"skill.brasshaven.branch.{bid}"], fr[f"skill.brasshaven.branch.{bid}"] = ben, bfr
    for sid, _b, _p, _c, _r, _i, (nen, nfr), (den, dfr), _e in SKILLS:
        en[f"skill.brasshaven.{sid}"], fr[f"skill.brasshaven.{sid}"] = nen, nfr
        en[f"skill.brasshaven.{sid}.desc"], fr[f"skill.brasshaven.{sid}.desc"] = den, dfr
    return en, fr


def java():
    ops = {"add": "ADD_VALUE", "base_mult": "ADD_MULTIPLIED_BASE", "total_mult": "ADD_MULTIPLIED_TOTAL"}
    lines = ["package com.brasshaven.generated;", "", "import java.util.List;", "",
             "/** GENERATED by tools/gen_java.py from tools/wf/skills.py — do not edit by hand. */",
             "public final class GeneratedSkills {",
             "    public record Branch(String id, String icon, int color) {}",
             "    /** kind: attr/mana/regen/power/thrift/lifesteal/repair/active; attribute + operation only for attr. */",
             "    public record Skill(String id, String branch, int col, int row, int cost, List<String> requires, String icon,",
             "                        String kind, String attribute, double amount, String operation, String ability) {}", "",
             "    public static final List<Branch> BRANCHES = List.of("]
    lines.append(",\n".join(f'            new Branch("{b}", "{i}", 0x{c:08X})' for b, i, c, _ in BRANCHES))
    lines += ["    );", "", "    public static final List<Skill> SKILLS = List.of("]
    rows = []
    for sid, branch, (col, row), cost, req, icon, _n, _d, eff in SKILLS:
        kind = eff[0]
        attr, amount, op, ability = "", 0.0, "", ""
        if kind == "attr":
            attr, amount, op = eff[1], eff[2], ops[eff[3]]
        elif kind == "active":
            ability = eff[1]
        else:
            amount = float(eff[1])
        reqs = ", ".join(f'"{r}"' for r in req)
        rows.append(f'            new Skill("{sid}", "{branch}", {col}, {row}, {cost}, List.of({reqs}), "{icon}", '
                    f'"{kind}", "{attr}", {amount}, "{op}", "{ability}")')
    lines.append(",\n".join(rows))
    lines += ["    );", "", "    private GeneratedSkills() {}", "}", ""]
    return "\n".join(lines)

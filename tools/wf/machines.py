"""Simple machines: one block each, no power network. One table drives Java registration, textures, models,
blockstates, recipes, loot, tags, translations and the manual page (like decor.py / metals.py)."""
from . import texgen_steam as S

# id -> dict(kind (MachineBlock.Kind), glyph (texgen_steam.MACHINE_GLYPHS), en, fr, desc: [(en, fr)] (3 lines max),
#            recipe: (pattern, key, count), color (MapColor), light)
MACHINES = {
    "auto_harvester": dict(
        kind="HARVESTER", glyph="harvester", en="Auto-Harvester", fr="Moissonneuse automatique", color="GOLD",
        desc=[("Harvests ripe crops around it and replants them.", "Récolte les cultures mûres autour d'elle et replante."),
              ("The harvest goes into a chest next to it.", "La récolte va dans un coffre collé à elle."),
              ("Sneak-click: change the area (5x5 to 9x9).", "Accroupi + clic : change la zone (5x5 à 9x9).")],
        recipe=(["BHB", "BCB", "BRB"], {"B": "wayfarers:brass_ingot", "H": "iron_hoe", "C": "chest", "R": "redstone"}, 1)),
    "sprinkler": dict(
        kind="SPRINKLER", glyph="sprinkler", en="Sprinkler", fr="Arroseur", color="COLOR_ORANGE",
        desc=[("Place it among your crops: plants below grow faster.", "Pose-le au milieu des cultures : les plantes dessous poussent plus vite."),
              ("Keeps farmland wet, no water needed.", "Garde la terre labourée humide, sans eau."),
              ("Click: change the area (3x3 to 7x7).", "Clic : change la zone (3x3 à 7x7).")],
        recipe=([" C ", "CWC", " C "], {"C": "copper_ingot", "W": "water_bucket"}, 1)),
    "vacuum_hopper": dict(
        kind="VACUUM", glyph="vacuum", en="Vacuum Hopper", fr="Trémie aspirante", color="COLOR_CYAN",
        desc=[("Pulls in items and experience nearby.", "Aspire les objets et l'expérience autour."),
              ("Feeds the chest below it; click it to take the XP.", "Remplit le coffre en dessous ; clic pour récupérer l'XP."),
              ("Sneak-click: change the range (3 to 8 blocks).", "Accroupi + clic : change la portée (3 à 8 blocs).")],
        recipe=(["BEB", "BHB", " B "], {"B": "wayfarers:brass_ingot", "E": "ender_pearl", "H": "hopper"}, 1)),
    "block_breaker": dict(
        kind="BREAKER", glyph="breaker", en="Block Breaker", fr="Casseur de blocs", color="COLOR_GRAY",
        desc=[("On a redstone pulse, breaks the block in front.", "Sur une impulsion de redstone, casse le bloc devant."),
              ("Drops go into the chest behind it.", "Les objets vont dans le coffre derrière."),
              ("Pair it with a Redstone Timer for tree and stone farms.", "Associe-le à un minuteur pour les fermes à arbres ou à pierre.")],
        recipe=(["BPB", "BRB", "BBB"], {"B": "wayfarers:brass_ingot", "P": "iron_pickaxe", "R": "redstone"}, 1)),
    "block_placer": dict(
        kind="PLACER", glyph="placer", en="Block Placer", fr="Poseur de blocs", color="COLOR_GRAY",
        desc=[("On a redstone pulse, places a block in front.", "Sur une impulsion de redstone, pose un bloc devant."),
              ("Takes blocks from the chest behind, or its own slots.", "Prend les blocs dans le coffre derrière, ou dans ses cases."),
              ("Great for replanting saplings automatically.", "Parfait pour replanter les pousses automatiquement.")],
        recipe=(["BDB", "BRB", "BBB"], {"B": "wayfarers:brass_ingot", "D": "dispenser", "R": "redstone"}, 1)),
    "redstone_timer": dict(
        kind="TIMER", glyph="timer", en="Redstone Timer", fr="Minuteur de redstone", color="COLOR_RED",
        desc=[("Sends a short redstone pulse every few seconds.", "Envoie une courte impulsion de redstone toutes les quelques secondes."),
              ("Click: 1, 2, 5, 10, 30 or 60 seconds.", "Clic : 1, 2, 5, 10, 30 ou 60 secondes."),
              ("No clock circuit to build!", "Plus besoin de construire une horloge !")],
        recipe=([" R ", "RCR", " R "], {"R": "redstone", "C": "clock"}, 1)),
    "wireless_transmitter": dict(
        kind="TRANSMITTER", glyph="transmitter", en="Wireless Transmitter", fr="Émetteur sans fil", color="COLOR_CYAN",
        desc=[("Sends the redstone signal it receives through the air.", "Envoie par les airs le signal de redstone qu'il reçoit."),
              ("Right-click with a dye to pick its channel colour.", "Clic droit avec une teinture pour choisir la couleur du canal."),
              ("Receivers of the same colour turn on.", "Les récepteurs de la même couleur s'allument.")],
        recipe=([" A ", "BRB", "BBB"], {"A": "lightning_rod", "B": "wayfarers:brass_ingot", "R": "redstone_block"}, 1)),
    "wireless_receiver": dict(
        kind="RECEIVER", glyph="receiver", en="Wireless Receiver", fr="Récepteur sans fil", color="COLOR_CYAN",
        desc=[("Outputs redstone while a transmitter of its colour is on.", "Émet de la redstone tant qu'un émetteur de sa couleur est allumé."),
              ("Right-click with a dye to pick its channel colour.", "Clic droit avec une teinture pour choisir la couleur du canal."),
              ("Works anywhere in the same dimension (chunks loaded).", "Marche partout dans la même dimension (chunks chargés).")],
        recipe=(["B B", "BRB", "BBB"], {"B": "wayfarers:brass_ingot", "R": "redstone"}, 1)),
    "entity_detector": dict(
        kind="DETECTOR", glyph="detector", en="Entity Detector", fr="Détecteur de créatures", color="COLOR_RED",
        desc=[("Outputs redstone while something is near (1 per creature, max 15).", "Émet de la redstone quand quelque chose approche (1 par créature, max 15)."),
              ("Click: range 2 to 16 blocks.", "Clic : portée de 2 à 16 blocs."),
              ("Sneak-click: players, monsters, animals, items or all living.", "Accroupi + clic : joueurs, monstres, animaux, objets ou tous les vivants.")],
        recipe=(["BEB", "BRB", "BBB"], {"B": "wayfarers:brass_ingot", "E": "ender_eye", "R": "redstone"}, 1)),
}

GUIDE = [
    ("machines", "wayfarers:auto_harvester", ("Farm machines", "Machines de ferme"), [
        ("No cables, no power: each machine is one block that does one job. Hover a machine in your inventory to "
         "read what it does.",
         "Ni câbles ni énergie : chaque machine est un bloc qui fait une seule chose. Survole une machine dans ton "
         "inventaire pour lire ce qu'elle fait."),
        ("A simple farm: Sprinkler in the middle of the field, Auto-Harvester at the edge with a chest against it. "
         "Wheat, carrots, potatoes, beetroots, nether wart, cocoa, melons, pumpkins, sugar cane, cactus and bamboo "
         "all work.",
         "Une ferme simple : un arroseur au milieu du champ, une moissonneuse au bord avec un coffre collé. Blé, "
         "carottes, pommes de terre, betteraves, verrues du Nether, cacao, melons, citrouilles, canne à sucre, "
         "cactus et bambou marchent tous."),
        ("Vacuum Hopper above a chest: it collects everything dropped around it, even experience.",
         "Trémie aspirante au-dessus d'un coffre : elle ramasse tout ce qui tombe autour, même l'expérience."),
    ], ["wayfarers:auto_harvester", "wayfarers:sprinkler", "wayfarers:vacuum_hopper"]),
    ("redstone_easy", "wayfarers:redstone_timer", ("Easy redstone", "Redstone facile"), [
        ("Redstone Timer: a ready-made clock. Click it to pick the delay.",
         "Minuteur de redstone : une horloge toute faite. Clique dessus pour choisir le délai."),
        ("Tree farm in 3 blocks: Timer -> Block Breaker facing the trunk -> Block Placer with saplings below it.",
         "Ferme à arbres en 3 blocs : minuteur -> casseur de blocs face au tronc -> poseur avec des pousses."),
        ("Wireless Transmitter and Receiver: dye both the same colour and the signal travels without wires. "
         "Entity Detector: opens doors or lights lamps when someone comes near.",
         "Émetteur et récepteur sans fil : teins-les de la même couleur et le signal passe sans fil. Détecteur de "
         "créatures : ouvre une porte ou allume des lampes quand quelqu'un approche."),
    ], ["wayfarers:redstone_timer", "wayfarers:block_breaker", "wayfarers:block_placer",
        "wayfarers:wireless_transmitter", "wayfarers:wireless_receiver", "wayfarers:entity_detector"]),
]


def textures():
    """{texture path under textures/: canvas}."""
    out = {"block/machine_side": S.machine_side(60), "block/machine_top": S.machine_top(61)}
    for mid, m in MACHINES.items():
        out[f"block/{mid}_front"] = S.machine_face(m["glyph"], False, 62)
        out[f"block/{mid}_front_on"] = S.machine_face(m["glyph"], True, 62)
    return out


def lang():
    en, fr = {}, {}
    for mid, m in MACHINES.items():
        en[f"block.wayfarers.{mid}"], fr[f"block.wayfarers.{mid}"] = m["en"], m["fr"]
        for i, (e, f) in enumerate(m["desc"]):
            suffix = "" if i == 0 else str(i + 1)
            en[f"block.wayfarers.{mid}.desc{suffix}"], fr[f"block.wayfarers.{mid}.desc{suffix}"] = e, f
    msgs = {
        "message.wayfarers.machine.area": ("Area: %sx%s", "Zone : %sx%s"),
        "message.wayfarers.machine.interval": ("Pulse every %s s", "Impulsion toutes les %s s"),
        "message.wayfarers.machine.channel": ("Channel: %s", "Canal : %s"),
        "message.wayfarers.machine.xp": ("+%s experience collected", "+%s d'expérience récupérée"),
        "message.wayfarers.machine.detector": ("Detects %s within %s blocks", "Détecte : %s à %s blocs"),
        "message.wayfarers.machine.detector.players": ("players", "joueurs"),
        "message.wayfarers.machine.detector.monsters": ("monsters", "monstres"),
        "message.wayfarers.machine.detector.animals": ("animals", "animaux"),
        "message.wayfarers.machine.detector.items": ("items", "objets"),
        "message.wayfarers.machine.detector.living": ("all creatures", "toutes les créatures"),
    }
    for k, (e, f) in msgs.items():
        en[k], fr[k] = e, f
    return en, fr


def java():
    L = [
        "package com.wayfarers.generated;",
        "",
        "import com.wayfarers.block.MachineBlock;",
        "import com.wayfarers.item.TooltipBlockItem;",
        "import com.wayfarers.registry.ModBlocks;",
        "import com.wayfarers.registry.ModItems;",
        "import net.minecraft.world.item.Item;",
        "import net.minecraft.world.level.block.Block;",
        "import net.minecraft.world.level.block.SoundType;",
        "import net.minecraft.world.level.block.state.BlockBehaviour;",
        "import net.minecraft.world.level.material.MapColor;",
        "import net.minecraftforge.registries.RegistryObject;",
        "",
        "import java.util.ArrayList;",
        "import java.util.List;",
        "",
        "/** GENERATED by tools/gen_java.py from tools/wf/machines.py — do not edit by hand. */",
        "public final class GeneratedMachines {",
        "    public static final List<RegistryObject<Block>> ALL = new ArrayList<>();",
        "",
    ]
    for mid, m in MACHINES.items():
        L.append(f'    public static final RegistryObject<Block> {mid.upper()} = machine("{mid}", MachineBlock.Kind.{m["kind"]}, '
                 f'MapColor.{m["color"]});')
    L += [
        "",
        "    private GeneratedMachines() {}",
        "",
        "    /** Forces class initialisation so every block/item is queued on the deferred registers. */",
        "    public static void init() {}",
        "",
        "    public static Block[] blocks() {",
        "        return ALL.stream().map(RegistryObject::get).toArray(Block[]::new);",
        "    }",
        "",
        "    private static RegistryObject<Block> machine(String name, MachineBlock.Kind kind, MapColor color) {",
        "        RegistryObject<Block> block = ModBlocks.BLOCKS.register(name, () -> new MachineBlock(BlockBehaviour.Properties.of()",
        "                .mapColor(color).strength(3.0F, 6.0F).sound(SoundType.METAL).requiresCorrectToolForDrops()",
        "                .setId(ModBlocks.BLOCKS.key(name)), kind));",
        "        ModItems.ALL.add(ModItems.ITEMS.register(name, () -> new TooltipBlockItem(block.get(),",
        "                new Item.Properties().setId(ModItems.ITEMS.key(name)).useBlockDescriptionPrefix())));",
        "        ALL.add(block);",
        "        return block;",
        "    }",
        "}",
        "",
    ]
    return "\n".join(L)

"""Wayfarers decorative blocks: one table drives textures, Java registration, models, data and lang."""
from . import texgen as T
from . import texgen_steam as S

# id -> dict(en, fr, tex: {face: callable}, light, color(map color), sound, strength, variants,
#            tool: "pickaxe" (default, needs it to drop) | "axe" | None)
# faces: "all" or "top"/"side"
SANDSTONE_WARM = (222, 196, 146)
GUILD = (206, 182, 140)
GUILD_MORTAR = (132, 112, 84)
AZURE = (52, 120, 150)
CRIMSON = (156, 58, 44)
LITHITE = (84, 196, 182)
LITHITE_STONE = (92, 104, 110)
EMBER_STONE = (52, 46, 50)
EMBER_GLOW = (255, 140, 40)
VOID_STONE = (46, 30, 64)
STAR = (230, 200, 255)
GOLD = (236, 190, 64)


def _guild_bricks():
    return T.bricks(GUILD, GUILD_MORTAR, seed=1)


DECOR = {
    "guild_bricks": dict(en="Guild Bricks", fr="Briques de la Guilde", tex={"all": _guild_bricks},
                         color="SAND", sound="STONE", strength=2.0, variants=("stairs", "slab", "wall")),
    "mossy_guild_bricks": dict(en="Mossy Guild Bricks", fr="Briques de la Guilde moussues",
                               tex={"all": lambda: T.overlay_moss(T.bricks(GUILD, GUILD_MORTAR, seed=2), seed=3)},
                               color="SAND", sound="STONE", strength=2.0, variants=("stairs", "slab", "wall")),
    "cracked_guild_bricks": dict(en="Cracked Guild Bricks", fr="Briques de la Guilde fissurées",
                                 tex={"all": lambda: T.overlay_cracks(T.bricks(GUILD, GUILD_MORTAR, seed=4),
                                                                      T.mul(GUILD_MORTAR, 0.7), seed=5)},
                                 color="SAND", sound="STONE", strength=2.0, variants=()),
    "polished_guild_stone": dict(en="Polished Guild Stone", fr="Pierre de la Guilde polie",
                                 tex={"all": lambda: T.polished(T.mul(GUILD, 1.05), seed=6)},
                                 color="SAND", sound="STONE", strength=2.0, variants=("stairs", "slab")),
    "carved_guild_stone": dict(en="Carved Guild Stone", fr="Pierre de la Guilde gravée",
                               tex={"top": lambda: T.polished(T.mul(GUILD, 1.05), seed=7),
                                    "side": lambda: T.emblem(T.polished(T.mul(GUILD, 1.0), seed=8),
                                                             T.mul(GUILD_MORTAR, 0.85), T.mul(GUILD, 1.18))},
                               color="SAND", sound="STONE", strength=2.0, variants=()),
    "guild_roof_tiles": dict(en="Azure Roof Tiles", fr="Tuiles d'azur", tex={"all": lambda: T.scales(AZURE, seed=9)},
                             color="COLOR_CYAN", sound="STONE", strength=1.5, variants=("stairs", "slab")),
    "crimson_roof_tiles": dict(en="Terracotta Roof Tiles", fr="Tuiles de terre cuite",
                               tex={"all": lambda: T.scales(CRIMSON, seed=10)},
                               color="COLOR_RED", sound="STONE", strength=1.5, variants=("stairs", "slab")),
    "slate_roof_tiles": dict(en="Slate Roof Tiles", fr="Tuiles d'ardoise",
                             tex={"all": lambda: T.scales((70, 76, 92), seed=11)},
                             color="COLOR_GRAY", sound="STONE", strength=1.5, variants=("stairs", "slab")),
    "rune_lamp": dict(en="Rune Lamp", fr="Lampe runique",
                      tex={"all": lambda: T.runes(T.frame(T.polished(T.mul(GUILD, 0.9), seed=12),
                                                          T.mul(GUILD, 1.1), T.mul(GUILD, 0.6)),
                                                  (120, 230, 255), (230, 255, 255), seed=13)},
                      color="COLOR_LIGHT_BLUE", sound="STONE", strength=2.0, light=15, variants=()),
    "lithite_block": dict(en="Lithite Crystal Block", fr="Bloc de cristal de lithite",
                          tex={"all": lambda: T.crystal((150, 240, 220), (60, 168, 160), (22, 92, 98), seed=14)},
                          color="COLOR_CYAN", sound="AMETHYST", strength=3.0, light=12, variants=()),
    "lithite_bricks": dict(en="Lithite Bricks", fr="Briques de lithite",
                           tex={"all": lambda: T.overlay_cracks(T.bricks(LITHITE_STONE, (56, 62, 66), seed=15),
                                                                (110, 230, 210), seed=16, n=2)},
                           color="COLOR_GRAY", sound="DEEPSLATE_BRICKS", strength=3.0, light=3,
                           variants=("stairs", "slab", "wall")),
    "ember_bricks": dict(en="Ember Bricks", fr="Briques de braise",
                         tex={"all": lambda: T.overlay_cracks(T.bricks(EMBER_STONE, (24, 20, 24), seed=17),
                                                              EMBER_GLOW, seed=18, n=3, glow=(160, 70, 30))},
                         color="COLOR_BLACK", sound="NETHER_BRICKS", strength=3.0, light=5,
                         variants=("stairs", "slab", "wall")),
    "ember_lamp": dict(en="Ember Lamp", fr="Lampe de braise",
                       tex={"all": lambda: T.lamp(EMBER_STONE, (255, 120, 30), (255, 230, 150), seed=19)},
                       color="COLOR_ORANGE", sound="NETHER_BRICKS", strength=2.5, light=15, variants=()),
    "gilded_trim": dict(en="Gilded Trim", fr="Frise dorée",
                        tex={"top": lambda: T.polished(EMBER_STONE, seed=20),
                             "side": lambda: T.trim(EMBER_STONE, GOLD, seed=21)},
                        color="GOLD", sound="STONE", strength=3.0, variants=()),
    "void_bricks": dict(en="Void Bricks", fr="Briques du vide",
                        tex={"all": lambda: T.stars(T.bricks(VOID_STONE, (22, 14, 32), seed=22),
                                                    [STAR, (180, 140, 255), (255, 255, 255)], seed=23, n=6)},
                        color="COLOR_PURPLE", sound="STONE", strength=3.0, light=2,
                        variants=("stairs", "slab", "wall")),
    "starlight_block": dict(en="Starlight Block", fr="Bloc de lumière stellaire",
                            tex={"all": lambda: T.crystal((255, 245, 255), (210, 180, 255), (140, 100, 220), seed=24)},
                            color="COLOR_MAGENTA", sound="AMETHYST", strength=2.0, light=15, variants=()),
    # ---------------------------------------------------------------- steampunk (tools/STYLE_STEAMPUNK.md)
    "brass_plating": dict(en="Riveted Brass Plating", fr="Placage en laiton riveté",
                          tex={"all": lambda: S.riveted_plate(S.BRASS, seed=40)},
                          color="GOLD", sound="METAL", strength=4.0, variants=("stairs", "slab")),
    "copper_plating": dict(en="Riveted Copper Plating", fr="Placage en cuivre riveté",
                           tex={"all": lambda: S.riveted_plate(S.COPPER, seed=41)},
                           color="COLOR_ORANGE", sound="COPPER", strength=4.0, variants=("stairs", "slab")),
    "verdigris_plating": dict(en="Verdigris Copper Plating", fr="Placage en cuivre vert-de-gris",
                              tex={"all": lambda: S.riveted_plate(S.COPPER, seed=42, patina=S.VERDIGRIS,
                                                                  patina_amount=0.8)},
                              color="WARPED_WART_BLOCK", sound="COPPER", strength=4.0, variants=("stairs", "slab")),
    "dark_iron_plating": dict(en="Dark Iron Plating", fr="Placage en fer sombre",
                              tex={"all": lambda: S.riveted_plate(S.DARK_IRON, seed=43)},
                              color="COLOR_BLACK", sound="METAL", strength=5.0, variants=("stairs", "slab", "wall")),
    "diamond_plate": dict(en="Iron Tread Plate", fr="Tôle striée",
                          tex={"all": lambda: S.grate((92, 92, 96), seed=44)},
                          color="METAL", sound="METAL", strength=5.0, variants=("stairs", "slab")),
    "gear_panel": dict(en="Clockwork Panel", fr="Panneau d'horlogerie",
                       tex={"top": lambda: S.riveted_plate(S.DARK_IRON, seed=45),
                            "side": lambda: S.gear_panel(S.DARK_IRON, S.BRASS, seed=46)},
                       color="COLOR_BLACK", sound="METAL", strength=4.0, variants=()),
    "copper_pipes": dict(en="Copper Pipe Bundle", fr="Faisceau de tuyaux en cuivre",
                         tex={"top": lambda: S.riveted_plate(S.COPPER, seed=47),
                              "side": lambda: S.pipe_casing(S.COPPER, S.BRASS, seed=48)},
                         color="COLOR_ORANGE", sound="COPPER", strength=3.0, variants=()),
    "pressure_gauge": dict(en="Pressure Gauge Panel", fr="Panneau à manomètre",
                           tex={"top": lambda: S.riveted_plate(S.DARK_IRON, seed=49),
                                "side": lambda: S.gauge(S.BRASS, S.CREAM, (170, 30, 30), seed=50)},
                           color="COLOR_BLACK", sound="METAL", strength=3.0, variants=()),
    "edison_lamp": dict(en="Edison Lamp", fr="Lampe Edison",
                        tex={"all": lambda: S.edison_lamp(S.DARK_IRON, S.AMBER, (255, 250, 220), seed=51)},
                        color="COLOR_ORANGE", sound="GLASS", strength=1.5, light=15, tool=None, variants=()),
    "aether_conduit": dict(en="Aether Conduit", fr="Conduit d'éther",
                           tex={"all": lambda: S.aether_conduit(S.DARK_IRON, S.AETHER, seed=52)},
                           color="COLOR_CYAN", sound="METAL", strength=4.0, light=10, variants=()),
    "mahogany_panelling": dict(en="Mahogany Panelling", fr="Lambris d'acajou",
                               tex={"all": lambda: S.planks_panel(S.MAHOGANY, seed=53)},
                               color="COLOR_BROWN", sound="WOOD", strength=2.0, tool="axe", variants=("stairs", "slab")),
    "leather_padding": dict(en="Tufted Leather", fr="Capitonnage en cuir",
                            tex={"all": lambda: S.tufted_leather(S.LEATHER, S.BRASS, seed=54)},
                            color="COLOR_RED", sound="WOOL", strength=0.8, tool=None, variants=("slab",)),
    "smokestack_bricks": dict(en="Smokestack Bricks", fr="Briques de cheminée",
                              tex={"all": lambda: S.soot_bricks((140, 62, 48), (60, 50, 46), seed=55)},
                              color="COLOR_RED", sound="STONE", strength=2.0, variants=("stairs", "slab", "wall")),
}


def all_block_ids():
    ids = []
    for bid, d in DECOR.items():
        ids.append(bid)
        for v in d["variants"]:
            ids.append(f"{bid.replace('_bricks', '_brick').replace('_tiles', '_tile')}_{v}"
                       if bid.endswith(("_bricks", "_tiles")) else f"{bid}_{v}")
    return ids


def variant_id(bid, v):
    if bid.endswith("_bricks"):
        return bid[:-1] + "_" + v  # guild_brick_stairs (vanilla style)
    if bid.endswith("_tiles"):
        return bid[:-1] + "_" + v  # guild_roof_tile_stairs
    return f"{bid}_{v}"


def texture_names(bid):
    tex = DECOR[bid]["tex"]
    if "all" in tex:
        return {"all": bid}
    return {"top": bid + "_top", "side": bid + "_side"}

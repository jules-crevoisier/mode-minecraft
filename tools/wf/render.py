"""Isometric preview renderer for blueprints (used to eyeball structures)."""
from .png import Canvas

COLORS = [
    ("quartz", (235, 230, 225)), ("target", (230, 200, 190)), ("pumpkin", (220, 130, 30)),
    ("cherry_leaves", (235, 160, 190)), ("leaves", (60, 120, 40)), ("cocoa", (140, 90, 40)),
    ("sugar_cane", (130, 190, 90)), ("lily_pad", (40, 110, 30)), ("decorated_pot", (150, 80, 60)),
    ("candle", (230, 220, 180)), ("smoker", (90, 80, 70)), ("cornflower", (90, 110, 230)),
    ("azure", (220, 230, 240)), ("lily_of", (240, 240, 240)), ("kelp", (60, 120, 50)),
    ("coral", (210, 90, 140)), ("rail", (120, 110, 90)), ("cobweb", (230, 230, 230)),
    # (substring, rgb) — first match wins
    ("water", (52, 95, 218)), ("lava", (234, 112, 16)), ("magma", (150, 60, 20)),
    ("glowstone", (250, 215, 120)), ("shroomlight", (240, 150, 70)), ("sea_lantern", (190, 225, 220)),
    ("lantern", (250, 200, 90)), ("torch", (255, 210, 80)), ("campfire", (230, 120, 40)),
    ("end_rod", (240, 235, 220)), ("amethyst", (150, 100, 200)), ("crying_obsidian", (70, 20, 120)),
    ("obsidian", (30, 22, 45)), ("purpur", (170, 125, 170)), ("end_stone", (220, 222, 160)),
    ("chorus", (140, 90, 140)), ("prismarine", (90, 160, 150)), ("dark_prismarine", (50, 95, 80)),
    ("gold", (240, 200, 60)), ("diamond", (100, 230, 225)), ("emerald", (60, 200, 100)),
    ("copper", (190, 110, 80)), ("iron", (200, 200, 200)), ("chain", (70, 70, 80)),
    ("crimson", (140, 40, 60)), ("warped", (40, 130, 130)), ("nether_wart", (120, 10, 10)),
    ("red_nether", (90, 15, 15)), ("nether_brick", (50, 25, 30)), ("netherrack", (110, 50, 50)),
    ("soul", (85, 65, 50)), ("basalt", (75, 75, 82)), ("blackstone", (42, 36, 42)),
    ("deepslate", (75, 75, 80)), ("tuff", (110, 112, 105)), ("calcite", (225, 225, 220)),
    ("sculk", (15, 40, 50)), ("mossy", (100, 120, 85)), ("moss", (90, 130, 45)),
    ("cracked", (115, 115, 115)), ("stone_brick", (125, 125, 125)), ("cobble", (110, 110, 110)),
    ("andesite", (135, 135, 135)), ("diorite", (190, 190, 190)), ("granite", (150, 105, 85)),
    ("smooth_stone", (160, 160, 160)), ("red_sandstone", (180, 95, 35)), ("sandstone", (215, 200, 145)),
    ("sand", (220, 210, 160)), ("terracotta", (160, 90, 65)), ("mud_brick", (140, 105, 80)),
    ("brick", (150, 85, 70)), ("packed_ice", (140, 170, 230)), ("blue_ice", (115, 160, 240)),
    ("ice", (160, 190, 250)), ("snow", (245, 250, 250)), ("quartz", (235, 230, 225)),
    ("glass", (190, 220, 235)), ("bars", (110, 110, 115)), ("bookshelf", (120, 80, 50)),
    ("dark_oak", (65, 45, 25)), ("spruce", (110, 80, 50)), ("birch", (200, 185, 130)),
    ("jungle", (160, 115, 80)), ("acacia", (170, 90, 50)), ("mangrove", (120, 50, 45)),
    ("cherry", (225, 180, 175)), ("bamboo", (195, 175, 85)), ("oak", (160, 130, 80)),
    ("leaves", (60, 120, 40)), ("vine", (50, 100, 30)), ("grass_block", (95, 150, 60)),
    ("grass", (90, 150, 50)), ("fern", (80, 130, 50)), ("flower", (220, 80, 120)),
    ("poppy", (200, 30, 30)), ("dandelion", (240, 220, 40)), ("path", (150, 125, 70)),
    ("podzol", (100, 70, 40)), ("coarse_dirt", (110, 80, 55)), ("dirt", (125, 90, 60)), ("gravel", (130, 125, 120)), ("clay", (160, 165, 175)),
    ("hay", (200, 170, 40)), ("wool", (220, 220, 220)), ("carpet", (180, 50, 50)),
    ("red_bed", (180, 30, 30)), ("bed", (150, 60, 60)), ("chest", (170, 120, 50)),
    ("barrel", (130, 95, 55)), ("spawner", (30, 40, 60)), ("anvil", (60, 60, 60)),
    ("bell", (230, 190, 50)), ("lectern", (150, 110, 60)), ("cauldron", (60, 60, 60)),
    ("carrots", (70, 140, 40)), ("potatoes", (70, 140, 40)), ("wheat", (180, 170, 60)),
    ("beetroots", (90, 130, 40)), ("farmland", (95, 60, 35)), ("table", (140, 100, 60)),
    ("furnace", (100, 100, 100)), ("smoker", (90, 80, 70)), ("ladder", (150, 115, 60)),
    ("loom", (170, 140, 100)), ("composter", (120, 90, 50)), ("lodestone", (150, 150, 150)),
    ("stone", (125, 125, 125)), ("jigsaw", (255, 0, 255)),
    ("white_", (235, 235, 235)), ("red_", (170, 40, 40)), ("blue_", (50, 60, 160)),
    ("green_", (80, 110, 30)), ("yellow_", (230, 200, 50)), ("black_", (30, 30, 30)),
    ("purple_", (120, 50, 160)), ("orange_", (230, 120, 30)), ("cyan_", (30, 130, 140)),
    ("light_blue", (90, 160, 210)), ("magenta_", (180, 70, 170)), ("gray_", (80, 80, 80)),
    ("brown_", (110, 75, 45)), ("lime_", (110, 190, 30)), ("pink_", (230, 140, 170)),
]
_cache = {}


DYES = {
    "white": (235, 235, 235), "orange": (230, 120, 30), "magenta": (180, 70, 170),
    "light_blue": (90, 160, 210), "yellow": (230, 200, 50), "lime": (110, 190, 30),
    "pink": (230, 140, 170), "gray": (80, 80, 80), "light_gray": (150, 150, 150), "cyan": (30, 130, 140),
    "purple": (120, 50, 160), "blue": (50, 60, 160), "brown": (110, 75, 45), "green": (80, 110, 30),
    "red": (170, 40, 40), "black": (30, 30, 30),
}
DYED = ("_wool", "_carpet", "_concrete", "_banner", "_bed", "_stained_glass", "_stained_glass_pane",
        "_terracotta", "_candle", "_glazed_terracotta")


def color_for(name):
    if name in _cache:
        return _cache[name]
    short = name.split(":")[1]
    for suffix in DYED:
        if short.endswith(suffix):
            dye = short[: -len(suffix)]
            if dye in DYES:
                c = DYES[dye]
                if "glass" in suffix:
                    c = tuple(int(v * 0.6 + 255 * 0.4) for v in c)
                _cache[name] = c
                return c
    for key, c in COLORS:
        if key in short:
            _cache[name] = c
            return c
    _cache[name] = (200, 0, 200)
    return _cache[name]


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _sprite(s):
    mask = []
    for py in range(2 * s):
        row = []
        for px in range(2 * s):
            x, y = px + 0.5, py + 0.5
            top = abs(x - s) / s + abs(y - s / 2) / (s / 2) <= 1
            inside = abs(x - s) / 2 <= y <= 2 * s - abs(x - s) / 2
            if top:
                row.append("t")
            elif inside:
                row.append("l" if x < s else "r")
            else:
                row.append(None)
        mask.append(row)
    return mask


def render(blocks, path, s=4, max_y=None, bg=(30, 32, 40, 255)):
    """blocks: dict (x,y,z) -> (name, props, nbt) in normalized coordinates."""
    hidden = ("minecraft:air", "minecraft:water", "minecraft:structure_void")
    vis = {p: b[0] for p, b in blocks.items() if b[0] not in hidden and (max_y is None or p[1] <= max_y)}
    if not vis:
        return
    xs = [p[0] for p in vis]
    ys = [p[1] for p in vis]
    zs = [p[2] for p in vis]
    X, Y, Z = max(xs) + 1, max(ys) + 1, max(zs) + 1
    w = (X + Z) * s + 2 * s
    h = (X + Z) * s // 2 + Y * s + 2 * s
    cv = Canvas(w, h, bg)
    mask = _sprite(s)
    ox = Z * s
    oy = Y * s
    order = sorted(vis, key=lambda p: (p[0] + p[1] + p[2], p[1]))
    for (x, y, z) in order:
        # skip fully hidden blocks
        if (x + 1, y, z) in vis and (x, y + 1, z) in vis and (x, y, z + 1) in vis:
            continue
        c = color_for(vis[(x, y, z)])
        sx = ox + (x - z) * s
        sy = oy + (x + z) * s // 2 - y * s
        cols = {"t": _shade(c, 1.12), "l": _shade(c, 0.82), "r": _shade(c, 0.64)}
        for py, row in enumerate(mask):
            for px, kind in enumerate(row):
                if kind:
                    cv.set(sx + px, sy + py, cols[kind])
    cv.save(path)

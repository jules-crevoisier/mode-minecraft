#!/usr/bin/env python3
"""Generate every Brasshaven texture: item sprites, block faces, armor layers, mob skins.

Everything is procedural / hand-drawn ASCII so the repository needs no binary art
sources. Run with --sheet to also write a contact sheet to build/previews.
"""
import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wf.png import Canvas  # noqa: E402
from wf.sprites import ACCENTS, HANDLES, MATERIALS, SHAPES  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "brasshaven", "textures")

# item id -> (shape, material, handle, accent)
ITEMS = {
    # progression materials
    "map_fragment": ("fragment", "map", "wood", "ink"),
    "lithite_shard": ("shard", "lithite", "wood", "emerald"),
    "ancient_ember": ("ember", "ember", "wood", "ember"),
    "void_shard": ("shard", "void", "wood", "amethyst"),
    "warden_scale": ("scale", "warden", "wood", "sapphire"),
    "void_heart": ("heart", "void", "wood", "amethyst"),
    "ember_of_ascension": ("ember", "ember", "wood", "gold"),
    # explorer utilities
    "wayfarer_atlas": ("book", "leather", "gold", "gold"),
    "wayfarer_manual": ("book", "map", "gold", "sapphire"),
    "structure_compass": ("compass", "gold", "dark", "ruby"),
    "travel_backpack": ("backpack", "leather", "dark", "gold"),
    "explorer_backpack": ("backpack_explorer", "leather", "dark", "sapphire"),
    "magnet_ring": ("ring_magnet", "iron", "wood", "ruby"),
    "recall_scroll": ("scroll", "map", "wood", "sapphire"),
    "builder_wand": ("wand_build", "gold", "wood", "emerald"),
    "chisel": ("chisel", "iron", "wood", "gold"),
    "fire_staff": ("staff_flame", "ember", "dark", "ember"),
    "frost_staff": ("staff_snow", "frost", "bone", "ice"),
    "thunder_staff": ("staff_bolt", "storm", "dark", "gold"),
    "healing_staff": ("staff_cross", "light", "wood", "emerald"),
    "levitation_wand": ("wand_float", "void", "bone", "amethyst"),
    "ward_orb": ("orb_caged", "void", "gold", "amethyst"),
    "steam_cane": ("cane", "gold", "dark", "gold"),
    "arcane_ring": ("ring", "gold", "wood", "amethyst"),
    "mana_amulet": ("amulet", "lithite", "gold", "sapphire"),
    "oblivion_vial": ("vial", "frost", "wood", "amethyst"),
    "master_builder_wand": ("wand_master", "lithite", "dark", "amethyst"),
    # weapons
    "cartographer_blade": ("sword", "cartographer", "wood", "emerald"),
    "telluric_hammer": ("hammer", "lithite", "wood", "emerald"),
    "storm_staff": ("staff_storm", "storm", "dark", "sapphire"),
    "ember_scythe": ("scythe", "ember", "blaze", "ember"),
    "void_spear": ("spear", "void", "purpur", "amethyst"),
    "boomerang": ("boomerang", "leather", "wood", "gold"),
    "frost_blade": ("blade", "frost", "bone", "ice"),
    "light_staff": ("staff_sun", "light", "gold", "gold"),
    # tools
    "excavator_pickaxe": ("pickaxe", "lithite", "wood", "emerald"),
    "lumber_axe": ("axe", "iron", "wood", "gold"),
    # automatons
    "brass_gear": ("gear", "brass", "dark", "gold"),
    "clockwork_heart": ("clockwork_heart", "copper", "dark", "aether"),
}
from wf.bossgear import BOSS_GEAR, remembrance_id  # noqa: E402
for _row in BOSS_GEAR:
    ITEMS[_row[2]] = _row[13]
    ITEMS[remembrance_id(_row[0])] = ("orb", _row[14][0], "gold", _row[14][1])
for prefix, mat, acc in (("explorer", "map", "emerald"), ("ember", "ember", "gold"), ("void", "void", "amethyst")):
    for piece in ("helmet", "chestplate", "leggings", "boots"):
        ITEMS[f"{prefix}_{piece}"] = (piece, mat, "wood", acc)

# spawn eggs: (base colour, spot colour)
EGGS = {
    "ruin_walker": ((120, 116, 100), (70, 110, 60)),
    "map_wraith": ((226, 214, 170), (90, 70, 40)),
    "basalt_guard": ((60, 58, 64), (230, 110, 40)),
    "void_stalker": ((40, 20, 60), (190, 110, 240)),
    "drowned_warden": ((40, 120, 120), (120, 230, 210)),
    "void_warden": ((24, 12, 40), (250, 120, 255)),
    "skeleton_knight": ((200, 196, 180), (90, 96, 110)),
    "crypt_crawler": ((220, 214, 196), (120, 30, 30)),
    "banshee": ((190, 220, 230), (60, 80, 120)),
    "gargoyle": ((110, 110, 118), (230, 80, 60)),
    "ember_imp": ((120, 30, 20), (255, 160, 40)),
    "void_larva": ((60, 30, 90), (210, 150, 255)),
    "grave_knight": ((60, 60, 66), (200, 196, 180)),
    "bone_matriarch": ((230, 220, 190), (150, 40, 40)),
    "weeping_lady": ((200, 230, 240), (40, 200, 200)),
    "larva_mother": ((50, 25, 80), (230, 170, 255)),
    "bell_keeper": ((90, 90, 100), (220, 190, 90)),
    "archivist": ((226, 214, 170), (60, 40, 90)),
    "sand_pharaoh": ((210, 180, 110), (40, 90, 170)),
    "jade_jaguar": ((60, 150, 100), (220, 190, 60)),
    "root_mother": ((90, 70, 45), (80, 150, 60)),
    "swamp_crone": ((70, 90, 60), (170, 80, 170)),
    "gryphon_knight": ((230, 225, 210), (70, 120, 200)),
    "rune_colossus": ((120, 120, 115), (110, 230, 255)),
    "forge_king": ((80, 70, 70), (250, 150, 40)),
    "crystal_spider": ((60, 40, 90), (180, 130, 255)),
    "sculk_spawn": ((20, 40, 50), (40, 220, 220)),
    "ash_lord": ((50, 45, 50), (250, 110, 30)),
    "piglin_king": ((220, 160, 140), (250, 200, 60)),
    "soul_reaper": ((40, 35, 30), (90, 230, 255)),
    "clockwork_spider": ((200, 158, 70), (255, 70, 46)),
    "steam_drone": ((186, 112, 58), (255, 70, 46)),
    "brass_golem": ((200, 158, 70), (70, 214, 255)),
    "grand_clockmaker": ((124, 90, 40), (222, 204, 168)),
    "iron_helmsman": ((58, 52, 52), (255, 178, 70)),
    "bronze_sentinel": ((150, 104, 56), (86, 168, 146)),
    "dune_king": ((206, 188, 146), (40, 72, 166)),
    "fallen_seraph": ((238, 234, 226), (150, 90, 220)),
    "chained_jailer": ((46, 40, 48), (255, 124, 32)),
    "caldera_castellan": ((56, 50, 58), (255, 116, 26)),
    "oathbound_gatekeeper": ((204, 196, 174), (110, 232, 236)),
    "frost_jarl": ((46, 64, 108), (160, 226, 250)),
    "storm_ascetic": ((214, 138, 46), (176, 226, 255)),
    "tide_abbess": ((40, 84, 90), (110, 238, 214)),
    "abyssal_architect": ((54, 56, 64), (96, 226, 246)),
    "lock_master": ((192, 150, 68), (70, 196, 236)),
    "bog_hierophant": ((78, 106, 46), (196, 244, 96)),
    "strangler_queen": ((86, 62, 40), (96, 214, 150)),
    "solar_hierarch": ((214, 170, 72), (255, 178, 70)),
    "drowned_admiral": ((38, 46, 74), (96, 236, 196)),
    "turbine_tyrant": ((104, 98, 94), (255, 178, 70)),
    "anvil_warden": ((58, 54, 62), (255, 120, 28)),
    "fourth_king": ((176, 160, 128), (40, 66, 160)),
    "colossus_heart": ((150, 104, 58), (255, 176, 64)),
    "star_curator": ((46, 34, 84), (190, 220, 255)),
    "mine_baron": ((120, 84, 56), (255, 206, 80)),
    "chime_abbot": ((176, 36, 50), (240, 206, 120)),
    "corsair_captain": ((38, 74, 86), (236, 190, 84)),
    "hollow_cantor": ((44, 46, 58), (150, 236, 230)),
    "soul_stoker": ((44, 38, 46), (60, 210, 240)),
    "asylum_director": ((226, 222, 206), (120, 236, 150)),
    "frost_commodore": ((70, 92, 120), (170, 226, 255)),
    "spore_alchemist": ((196, 38, 34), (120, 236, 96)),
    "lumber_jarl": ((178, 38, 34), (226, 214, 184)),
    "thorn_gardener": ((176, 112, 58), (236, 86, 170)),
    "abyss_diver": ((190, 150, 70), (80, 255, 214)),
    "moon_warden": ((236, 232, 226), (176, 206, 255)),
}


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def render_sprite(shape, mat, handle, accent):
    from wf import itemart
    painted = itemart.sprite(shape, {"M": MATERIALS[mat], "H": itemart.two_tone(*HANDLES[handle]),
                                     "A": itemart.two_tone(*ACCENTS[accent])})
    if painted is not None:
        return painted
    light, mid, dark, outline = MATERIALS[mat]
    hl, hd = HANDLES[handle]
    gl, gd = ACCENTS[accent]
    pal = {"o": outline, "a": light, "b": mid, "c": dark, "h": hl, "H": hd, "g": gl, "G": gd,
           "w": (255, 255, 255)}
    cv = Canvas(16, 16)
    rows = SHAPES[shape].strip("\n").split("\n")
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.set(x, y, pal[ch])
    return cv


# 5x5 emblems drawn on each boss Remembrance orb, so the 16 relics are told apart at a glance
EMBLEMS = {
    "drowned_warden": [".#.#.", "#.#.#", ".....", ".#.#.", "#.#.#"],   # waves
    "bell_keeper": ["..#..", ".###.", ".###.", "#####", "..#.."],     # bell
    "archivist": ["##.##", "#####", "#####", "#####", "##.##"],       # open book
    "sand_pharaoh": ["#.#.#", ".###.", "##.##", ".###.", "#.#.#"],    # sun
    "jade_jaguar": ["#...#", "#...#", "##.##", ".#.#.", ".#.#."],     # fangs
    "root_mother": ["..#..", ".###.", "#####", "..#..", ".#.#."],     # leaf and roots
    "swamp_crone": ["#...#", "#####", "#####", "#####", ".###."],     # cauldron
    "gryphon_knight": ["....#", "...##", "..##.", ".##..", "#...."],  # feather
    "rune_colossus": ["###..", "#.#..", "###..", "#..#.", "#...#"],   # rune
    "forge_king": ["#####", ".###.", "..#..", ".###.", "#####"],      # anvil
    "crystal_spider": ["#.#.#", ".###.", "#####", ".###.", "#.#.#"],  # web
    "sculk_spawn": [".###.", "#...#", "#.#.#", "#...#", ".###."],     # eye
    "ash_lord": ["..#..", ".##..", ".###.", "#####", ".###."],        # flame
    "piglin_king": ["#.#.#", "#####", "#####", ".....", "....."],     # crown
    "soul_reaper": [".###.", "#.#.#", "#####", ".#.#.", "....."],     # skull
    "void_warden": ["..#..", "..#..", "#####", "..#..", "..#.."],     # star
    "grand_clockmaker": [".###.", "#.#.#", "#.###", "#...#", ".###."],  # clock face
    "iron_helmsman": ["..#..", "#####", "..#..", "#.#.#", ".###."],     # anchor
    "bronze_sentinel": ["#####", "#.#.#", "#####", "#####", ".###."],   # tower shield with a cross
    "dune_king": ["#...#", "##.##", "#.#.#", "#####", "#####"],         # double crown
    "fallen_seraph": [".##..", "#...#", "#...#", "#...#", ".###."],     # broken halo
    "chained_jailer": [".###.", "#...#", "#####", "##.##", "#####"],    # padlock
    "caldera_castellan": ["#.#.#", "#####", "#...#", "#.#.#", "#####"],  # crater crown round a needle
    "oathbound_gatekeeper": [".###.", ".#.#.", ".###.", "..#..", "..##."],  # the gate's key
    "frost_jarl": ["#.#.#", "#####", ".###.", ".###.", "..#.."],        # ice crown over a beard
    "storm_ascetic": ["..##.", ".##..", "####.", "..##.", ".##.."],    # a bolt of lightning
    "tide_abbess": [".###.", "#...#", "#.#.#", "#..#.", "#...."],       # the crozier's spiral
    "abyssal_architect": ["..#..", "..#..", ".###.", "#####", ".###."],  # a plumb-bob on its line
    "lock_master": ["#####", "#.#.#", "#####", "#.#.#", "#####"],       # a sluice gate in its frame
    "bog_hierophant": ["..#..", ".###.", "#####", ".#.#.", "#.#.#"],    # a mitre over stilts
    "strangler_queen": ["#.#.#", ".###.", "..#..", ".###.", "#.#.#"],   # an orchid crown over roots
    "solar_hierarch": ["#.#.#", ".###.", "##.##", ".###.", "#.#.#"],    # a rayed sun-disc
    "drowned_admiral": ["#####", ".###.", "#...#", "#...#", ".###."],   # a bicorne over a diving helmet
    "turbine_tyrant": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],    # a four-bladed rotor
    "anvil_warden": ["#####", ".###.", "..#..", ".###.", "#####"],     # an anvil seen from the side
    "fourth_king": ["#.#.#", "#####", "##.#.", "##...", ".#..."],    # a crown over a half-chiselled face
    "colossus_heart": [".#.#.", "#####", "#####", ".###.", "..#.."],    # the engine-heart
    "star_curator": ["#...#", ".###.", "##.##", ".###.", "#...#"],      # a cracked star in its orbit
    "mine_baron": ["#####", ".###.", "..#..", "..#..", ".#.#."],       # a pickaxe over a nugget
    "chime_abbot": [".###.", "#...#", "#.#.#", "#...#", "#.#.#"],      # a halo of hanging chimes
    "corsair_captain": ["#.#.#", ".###.", "##.##", ".###.", "#.#.#"],  # a rotor turning on its hub
    "hollow_cantor": ["#...#", "#...#", ".###.", "..#..", "..#.."],    # a tuning fork
    "soul_stoker": [".#.#.", "#####", "#.#.#", "#####", ".###."],      # a furnace door with a grate
    "asylum_director": [".###.", "#.#.#", "#.##.", "#...#", ".###."],  # a pocket watch
    "frost_commodore": ["..#..", ".###.", "..#..", "#.#.#", ".###."],  # an anchor
    "spore_alchemist": [".###.", "#####", "#.#.#", "..#..", ".###."],  # a toadstool over a flask
    "lumber_jarl": ["#...#", "#.#.#", ".###.", "..#..", "..#.."],      # a horned helm over an axe haft
    "thorn_gardener": ["#...#", ".#.#.", "..#..", ".#.#.", "##.##"],   # open pruning shears
    "abyss_diver": [".###.", "#...#", "#.#.#", "#...#", ".###."],      # a diving helmet's porthole
    "moon_warden": [".##..", "#....", "#....", "#....", ".##.."],      # a crescent moon
}


def emblem(cv, mask, color):
    for y, row in enumerate(mask):
        for x, ch in enumerate(row):
            if ch == "#":
                cv.set(5 + x, 5 + y, color)


def egg(base, spots):
    cv = Canvas(16, 16)
    rows = SHAPES["egg"].strip("\n").split("\n")
    pal = {"o": shade(base, 0.4), "a": shade(base, 1.2), "b": base, "c": shade(base, 0.7),
           "g": spots, "G": shade(spots, 0.7)}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.set(x, y, pal.get(ch, base))
    return cv


# ------------------------------------------------------------------ block textures
def noise_tile(base, var=14, seed=0, size=16):
    rng = random.Random(seed)
    cv = Canvas(size, size)
    for y in range(size):
        for x in range(size):
            d = rng.randint(-var, var)
            cv.set(x, y, tuple(max(0, min(255, v + d)) for v in base))
    return cv


def frame(cv, c, inset=0):
    for i in range(inset, 16 - inset):
        cv.set(i, inset, c)
        cv.set(i, 15 - inset, c)
        cv.set(inset, i, c)
        cv.set(15 - inset, i, c)


def block_textures():
    out = {}
    from wf import texgen_chisel
    out.update(texgen_chisel.chisel_table())
    from wf import blockart as BA
    for name in ("waystone_side", "waystone_top", "sorting_chest_side", "sorting_chest_top", "guild_terminal_front",
                 "guild_terminal_side", "compacting_crate_side", "compacting_crate_front", "grave", "sealed_bars",
                 "warden_altar_side", "warden_altar_top", "void_altar_side", "void_altar_top", "boss_seal_side",
                 "boss_seal_top"):
        out[name] = getattr(BA, name)()
    # storage relay: a brass housing with copper coils and an ender-pearl lens on top
    brass, brass_dk, copper = (196, 150, 70), (112, 78, 34), (190, 104, 64)
    pearl = ((22, 64, 58), (40, 120, 104), (98, 204, 170), (190, 255, 228))
    rs = noise_tile(brass, 9, 41)
    frame(rs, brass_dk)
    for y in range(2, 14):
        for x in (3, 4, 11, 12):
            rs.set(x, y, copper if y % 2 == 0 else (150, 78, 44))
    for y in range(5, 11):
        for x in range(6, 10):
            rs.set(x, y, pearl[1] if 6 < y < 10 and 6 < x < 9 else pearl[0])
    rs.set(7, 7, pearl[3])
    for x in range(16):
        rs.set(x, 1, (226, 186, 96))
        rs.set(x, 14, brass_dk)
    out["storage_relay_side"] = rs
    rt = noise_tile(brass, 9, 42)
    frame(rt, brass_dk)
    frame(rt, (226, 186, 96), 1)
    for y in range(16):
        for x in range(16):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d <= 5.5 ** 2:
                rt.set(x, y, pearl[0] if d > 4.5 ** 2 else pearl[1] if d > 2.5 ** 2 else pearl[2])
    rt.set(6, 6, pearl[3])
    rt.set(7, 6, pearl[3])
    rt.set(6, 7, pearl[3])
    out["storage_relay_top"] = rt
    # boss mist: pale, swirling and translucent
    mist = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            v = 0.5 + 0.5 * math.sin((x * 0.7 + y * 0.35) + math.sin(y * 0.6) * 1.6)
            a = int(70 + 70 * v)
            mist.set(x, y, (int(205 + 40 * v), int(215 + 35 * v), 255, a))
    out["mist_gate"] = mist
    # ores: lithite crystals in stone and deepslate
    from wf import texore
    out["lithite_ore"] = texore.ore("lithite", "stone", 14)
    out["deepslate_lithite_ore"] = texore.ore("lithite", "deepslate", 15)
    return out


# ------------------------------------------------------------------ armor layers (64x32 humanoid UVs)
def armor_layer(mat, accent, legs=False):
    light, mid, dark, outline = MATERIALS[mat]
    gl, gd = ACCENTS[accent]
    cv = Canvas(64, 32)
    rng = random.Random(f"{mat}{legs}")

    def box(u, v, w, h, d, base):
        # unfolded cube: top/bottom row then 4 sides
        for (x0, y0, ww, hh) in ((u + d, v, w, d), (u + d + w, v, w, d), (u, v + d, d, h),
                                 (u + d, v + d, w, h), (u + d + w, v + d, d, h), (u + d + w + d, v + d, w, h)):
            for y in range(y0, y0 + hh):
                for x in range(x0, x0 + ww):
                    f = 1.0 + rng.uniform(-0.06, 0.06)
                    edge = x in (x0, x0 + ww - 1) or y in (y0, y0 + hh - 1)
                    cv.set(x, y, shade(dark if edge else base, f))

    if legs:
        box(0, 16, 4, 12, 4, mid)      # legs
        box(16, 16, 8, 12, 4, mid)     # waist (body region)
        for x in range(20, 28):
            cv.set(x, 20, gl)
    else:
        box(0, 0, 8, 8, 8, mid)        # head
        box(16, 16, 8, 12, 4, light)   # body
        box(40, 16, 4, 12, 4, mid)     # arms
        box(0, 16, 4, 12, 4, mid)      # boots / legs
        for x in range(8, 16):
            cv.set(x, 8, gl)          # helmet band
        for y in range(21, 27):
            cv.set(23, y, gd)
            cv.set(24, y, gl)
        # visor gap on the helmet front
        for x in range(10, 14):
            cv.set(x, 12, (0, 0, 0, 0))
    return cv


# ------------------------------------------------------------------ metals (wf/metals.py)
GEAR_ACCENT = {"brass": "ember", "mithril": "sapphire", "aether": "ice", "arcane": "amethyst", "zinc": "gold",
               "orichalcum": "ruby"}


# armour pieces with their own silhouette: the Brass Goggles, the Arcanist's hood and robe
ARMOR_SHAPES = {("brass", "helmet"): "goggles", ("arcane", "helmet"): "hood", ("arcane", "chestplate"): "robe"}


def metal_textures():
    from wf import blockart, metals, texore
    out = {}
    for mid, m in metals.METALS.items():
        pal = metals.PALETTES[m["palette"]]
        MATERIALS.setdefault(mid, pal)
        accent = GEAR_ACCENT.get(mid, "gold")
        for bid, (kind, host, _label) in metals.block_ids(mid).items():
            if kind == "ore":
                out[f"block/{bid}"] = texore.ore(mid, host, len(bid))  # hand-pixelled ore stamps (wf/texore.py)
            elif kind == "storage":
                out[f"block/{bid}"] = blockart.storage_block(pal, mid, sum(map(ord, mid)))
            else:
                out[f"block/{bid}"] = blockart.raw_block(pal, len(mid))
        for iid, (form, _label) in metals.item_ids(mid).items():
            out[f"item/{iid}"] = render_sprite(form, mid, "wood", accent)
        for gid, (kind, what, _label) in metals.gear_ids(mid).items():
            handle = "dark" if mid in ("mithril", "aether") else "wood"
            if mid == "arcane":
                handle = "gold"
            out[f"item/{gid}"] = render_sprite(ARMOR_SHAPES.get((mid, what), what), mid, handle, accent)
        if m.get("armor"):
            out[f"entity/equipment/humanoid/{mid}"] = armor_layer(mid, accent)
            out[f"entity/equipment/humanoid_leggings/{mid}"] = armor_layer(mid, accent, legs=True)
    return out


# ------------------------------------------------------------------ mob skins
def humanoid_skin(w, h, skin, cloth, accent, eyes, seed, hat=None):
    """Fills the standard player-style UV layout (works for zombie/drowned 64x64, skeleton 64x32)."""
    rng = random.Random(seed)
    cv = Canvas(w, h)

    def region(x0, y0, x1, y1, c, var=10):
        for y in range(y0, min(y1, h)):
            for x in range(x0, min(x1, w)):
                d = rng.randint(-var, var)
                cv.set(x, y, tuple(max(0, min(255, v + d)) for v in c))

    region(0, 0, 32, 16, skin)          # head
    region(16, 16, 40, 32, cloth)       # body
    region(40, 16, 56, 32, skin)        # right arm
    region(0, 16, 16, 32, cloth)        # right leg
    if h >= 64:
        region(16, 48, 32, 64, cloth)   # left leg
        region(32, 48, 48, 64, skin)    # left arm
    # face on head front (8..15, 8..15)
    for x in (9, 10):
        cv.set(x, 12, eyes)
    for x in (13, 14):
        cv.set(x, 12, eyes)
    for x in range(10, 14):
        cv.set(x, 14, shade(skin, 0.5))
    # belt / trim
    for x in range(16, 40):
        cv.set(x, 26, accent)
    if hat:
        region(32, 0, 64, 8, hat, 6)
        region(40, 8, 48, 10, hat, 6)
    return cv


def mob_textures():
    from wf import skins
    return {f"entity/{name}": fn() for name, fn in skins.SKINS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()
    written = {}
    for name, (shape, mat, handle, accent) in ITEMS.items():
        written[f"item/{name}"] = render_sprite(shape, mat, handle, accent)
    for row in BOSS_GEAR:
        cv = written[f"item/{remembrance_id(row[0])}"]
        light, mid, dark, outline = MATERIALS[row[14][0]]
        bright = sum(mid[:3]) / 3 > 150
        emblem(cv, EMBLEMS[row[0]], outline if bright else (255, 250, 230))
    from wf import ocean
    EGGS.update(ocean.EGGS)
    from wf import denizens
    EGGS.update(denizens.EGGS)
    for mob, (base, spots) in EGGS.items():
        written[f"item/{mob}_spawn_egg"] = egg(base, spots)
    for name, cv in block_textures().items():
        written[f"block/{name}"] = cv
    for prefix, mat, acc in (("explorer", "map", "emerald"), ("ember", "ember", "gold"), ("void", "void", "amethyst")):
        written[f"entity/equipment/humanoid/{prefix}"] = armor_layer(mat, acc)
        written[f"entity/equipment/humanoid_leggings/{prefix}"] = armor_layer(mat, acc, legs=True)
    written.update(mob_textures())
    written.update(metal_textures())
    from wf import machines
    written.update(machines.textures())
    from wf import furniture
    written.update(furniture.textures())
    from wf import held3d
    written.update(held3d.textures())
    written.update(__import__("wf.relicart", fromlist=["textures"]).textures())  # relic gear (wf/relics.py)
    written.update(__import__("wf.colossal_art", fromlist=["textures"]).textures())  # vault gear (wf/colossal_gear.py)
    from wf import gadgets
    written.update(gadgets.textures())
    from wf import worldblocks
    written.update(worldblocks.textures())
    written.update(ocean.textures())
    written.update(__import__("wf.social", fromlist=["textures"]).textures())  # multiplayer blocks
    from wf import decor
    for bid, d in decor.DECOR.items():
        names = decor.texture_names(bid)
        for face, fn in d["tex"].items():
            written[f"block/{names[face]}"] = fn()
    written.update(__import__("wf.blocktex", fromlist=["textures"]).textures(written))  # block-face overhaul, repaints only
    for rel, cv in written.items():
        path = os.path.join(TEX, rel + ".png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cv.save(path)
    print(f"{len(written)} textures written")
    if args.sheet:
        icons = [cv for rel, cv in written.items() if cv.w == 16]
        cols = 12
        sheet = Canvas(cols * 36, ((len(icons) + cols - 1) // cols) * 36, (40, 42, 50, 255))
        for i, cv in enumerate(icons):
            ox, oy = (i % cols) * 36 + 2, (i // cols) * 36 + 2
            for y in range(16):
                for x in range(16):
                    p = cv.get(x, y)
                    if p[3]:
                        sheet.rect(ox + x * 2, oy + y * 2, ox + x * 2 + 1, oy + y * 2 + 1, p)
        os.makedirs(os.path.join(ROOT, "build", "previews"), exist_ok=True)
        sheet.save(os.path.join(ROOT, "build", "previews", "textures_sheet.png"))


if __name__ == "__main__":
    main()

"""3D models for weapons and staves held in hand (the inventory keeps the 2D sprite).

Each model is built from cuboids by an archetype function and textured from a small per-item palette texture
(textures/item/3d/<id>.png): 4x4 cells of flat colours (handle, metal light/mid/dark, accent, glow...), each face
sampling the centre of its cell. The item definition switches on the display context: gui, ground, fixed and
on_shelf show the sprite, everything else the 3D model.

Coordinates are model pixels; the grip sits around y 6-10 (the model centre), so hands hold the handle.
"""
from .png import Canvas
from .sprites import ACCENTS, HANDLES, MATERIALS

CELLS = ["handle", "handle_dark", "light", "mid", "dark", "outline", "accent", "accent_dark", "glow", "wrap"]


def _cell_uv(key):
    i = CELLS.index(key)
    cx, cy = i % 4, i // 4
    return [cx * 4 + 1, cy * 4 + 1, cx * 4 + 3, cy * 4 + 3]


def palette(material, handle, accent, glow=None):
    light, mid, dark, outline = MATERIALS[material]
    hl, hd = HANDLES[handle]
    gl, gd = ACCENTS[accent]
    colors = {"handle": hl, "handle_dark": hd, "light": light, "mid": mid, "dark": dark, "outline": outline,
              "accent": gl, "accent_dark": gd, "glow": glow or tuple(min(255, int(c * 0.55 + 255 * 0.45)) for c in gl[:3]), "wrap": tuple(int(c * 0.55) for c in hd)}
    cv = Canvas(16, 16)
    for key, c in colors.items():
        i = CELLS.index(key)
        cx, cy = i % 4, i // 4
        for y in range(cy * 4, cy * 4 + 4):
            for x in range(cx * 4, cx * 4 + 4):
                edge = x in (cx * 4, cx * 4 + 3) or y in (cy * 4, cy * 4 + 3)
                cv.set(x, y, tuple(max(0, min(255, int(v * (0.92 if edge else 1.0)))) for v in c[:3]))
    return cv


def box(x0, y0, z0, x1, y1, z1, key, shade=True):
    return (x0, y0, z0, x1, y1, z1, key)


# ------------------------------------------------------------------ archetypes (centred on x = z = 8)
def _shaft(y0, y1, w=1.5, key="handle"):
    a = 8 - w / 2
    return [box(a, y0, a, a + w, y1, a + w, key)]


def _grip(y0, y1, w=2.0):
    a = 8 - w / 2
    return [box(a, y0, a, a + w, y1, a + w, "wrap")]


def sword(length=20, width=3.0, guard=7):
    a = 8 - width / 2
    out = _grip(3, 8) + [box(7, 1.5, 7, 9, 3, 9, "accent")]  # pommel
    out += [box(8 - guard / 2, 8, 6.5, 8 + guard / 2, 9.5, 9.5, "accent_dark"), box(7, 8.5, 6, 9, 9, 10, "accent")]
    out += [box(a, 9.5, 7.25, a + width, 9.5 + length, 8.75, "mid"),
            box(7.5, 9.5, 7, 8.5, 9.5 + length, 9, "light"),
            box(a + 0.5, 9.5 + length, 7.4, a + width - 0.5, 11 + length, 8.6, "light")]
    return out


def greatsword():
    return sword(length=22, width=4.0, guard=9)


def blade():
    out = _grip(3, 8) + [box(6.5, 8, 6.5, 9.5, 9, 9.5, "accent")]
    out += [box(6.8, 9, 7.4, 9.2, 22, 8.6, "mid"), box(7.4, 22, 7.5, 9.0, 24, 8.5, "light"), box(8.6, 9, 7.6, 9.6, 21, 8.4, "light")]
    return out


def spear(head="spear"):
    out = _shaft(-2, 22) + _grip(5, 10, 2.2)
    out += [box(6.5, 22, 7.25, 9.5, 23, 8.75, "accent_dark"),
            box(7, 23, 7.5, 9, 28, 8.5, "mid"), box(7.5, 28, 7.6, 8.5, 30, 8.4, "light")]
    if head == "trident":
        out += [box(5, 23, 7.5, 6, 27, 8.5, "mid"), box(10, 23, 7.5, 11, 27, 8.5, "mid"),
                box(5, 23, 7.5, 11, 24, 8.5, "dark")]
    if head == "lance":
        out += [box(6, 12, 6, 10, 14, 10, "accent"), box(6.5, 23, 6.5, 9.5, 26, 9.5, "mid")]
    return out


def hammer(head_w=8, head_h=5):
    out = _shaft(-2, 18) + _grip(4, 10, 2.2)
    a, b = 8 - head_w / 2, 8 + head_w / 2
    out += [box(a, 18, 5.5, b, 18 + head_h, 10.5, "mid"),
            box(a - 0.5, 18.5, 5, a, 17.5 + head_h, 11, "dark"), box(b, 18.5, 5, b + 0.5, 17.5 + head_h, 11, "dark"),
            box(7, 18 + head_h, 7, 9, 19 + head_h, 9, "accent"), box(6.5, 17, 6.5, 9.5, 18, 9.5, "accent_dark")]
    return out


def mace():
    out = _shaft(-2, 18) + _grip(4, 10, 2.2)
    out += [box(5.5, 18, 5.5, 10.5, 23, 10.5, "mid"), box(7, 23, 7, 9, 25, 9, "light")]
    for (x, z) in ((4.5, 7.5), (10.5, 7.5), (7.5, 4.5), (7.5, 10.5)):
        out.append(box(x, 19.5, z, x + 1, 21.5, z + 1, "accent"))
    return out


def staff(orb="glow", crown="accent"):
    out = _shaft(-4, 22, 1.5) + _grip(5, 10, 2.0)
    out += [box(6.5, 21, 6.5, 9.5, 22, 9.5, crown),
            box(5.5, 22, 7.5, 6.5, 25, 8.5, crown), box(9.5, 22, 7.5, 10.5, 25, 8.5, crown),
            box(7.5, 22, 5.5, 8.5, 25, 6.5, crown), box(7.5, 22, 9.5, 8.5, 25, 10.5, crown),
            box(6.5, 22.5, 6.5, 9.5, 25.5, 9.5, orb), box(7.25, 25.5, 7.25, 8.75, 27, 8.75, orb)]
    return out


def cane():
    out = _shaft(-4, 20, 1.5) + _grip(5, 10, 2.0)
    out += [box(6.5, 20, 6.5, 9.5, 23, 9.5, "mid"), box(7, 23, 7, 9, 24, 9, "accent"),
            box(9.5, 21, 7.25, 11, 22, 8.75, "dark"), box(6, 18, 6, 10, 19, 10, "accent_dark")]
    return out


def scythe():
    out = _shaft(-4, 24, 1.5) + _grip(4, 9, 2.0) + _grip(14, 17, 2.0)
    out += [box(7, 22, 7.25, 9, 24, 8.75, "accent_dark"),
            box(1, 22.5, 7.5, 7, 24, 8.5, "mid"), box(-2, 20.5, 7.5, 1, 23, 8.5, "mid"), box(-3, 18, 7.6, -1, 21, 8.4, "light"),
            box(1, 22, 7.6, 7, 22.5, 8.4, "light")]
    return out


def book():
    return [box(4, 4, 6, 12, 14, 10, "mid"), box(4.5, 4.5, 5.5, 11.5, 13.5, 6, "dark"),
            box(4.5, 4.5, 10, 11.5, 13.5, 10.5, "dark"), box(11.5, 4.5, 6.2, 12, 13.5, 9.8, "light"),
            box(7, 8, 5.2, 9, 10, 5.5, "glow"), box(7, 8, 10.5, 9, 10, 10.8, "glow")]


def fist():
    return [box(4, 2, 4, 12, 9, 12, "mid"), box(4.5, 9, 4.5, 11.5, 13, 11.5, "light"),
            box(5, 13, 5, 7, 15, 7, "dark"), box(9, 13, 5, 11, 15, 7, "dark"), box(5, 13, 9, 7, 15, 11, "dark"),
            box(9, 13, 9, 11, 15, 11, "dark"), box(7, 6, 3.5, 9, 8, 4, "glow")]


def horn():
    return [box(6, 4, 6, 10, 9, 10, "mid"), box(6.5, 9, 6.5, 9.5, 13, 9.5, "light"),
            box(7, 13, 7, 9, 17, 9, "light"), box(7.5, 17, 7.5, 8.5, 20, 8.5, "glow"), box(5.5, 3, 5.5, 10.5, 4, 10.5, "accent")]


def wand():
    out = _shaft(-2, 18, 1.2) + _grip(5, 9, 1.6)
    out += [box(7, 18, 7, 9, 20, 9, "accent"), box(7.25, 20, 7.25, 8.75, 22, 8.75, "glow")]
    return out


def orb():
    return [box(5, 5, 5, 11, 11, 11, "glow"), box(4.5, 7, 7, 11.5, 9, 9, "accent"), box(7, 4, 7, 9, 5, 9, "accent_dark")]


ARCHETYPES = {"sword": sword, "greatsword": greatsword, "blade": blade, "spear": spear,
              "trident": lambda: spear("trident"), "lance": lambda: spear("lance"), "hammer": hammer,
              "mace": mace, "staff": staff, "cane": cane, "scythe": scythe, "book": book, "fist": fist,
              "horn": horn, "wand": wand, "orb": orb}

# item id -> (archetype, material, handle, accent)
HELD = {
    "kings_trident": ("trident", "warden", "bone", "sapphire"),
    "bell_hammer": ("hammer", "gold", "dark", "gold"),
    "forbidden_grimoire": ("book", "map", "dark", "amethyst"),
    "pharaoh_flail": ("mace", "gold", "gold", "sapphire"),
    "jade_fang": ("blade", "lithite", "gold", "emerald"),
    "rootmother_staff": ("staff", "leather", "wood", "emerald"),
    "crone_ladle": ("mace", "iron", "dark", "amethyst"),
    "gryphon_lance": ("lance", "iron", "gold", "sapphire"),
    "rune_fist": ("fist", "lithite", "dark", "sapphire"),
    "forge_king_hammer": ("hammer", "ember", "dark", "gold"),
    "crystal_fang": ("spear", "void", "bone", "amethyst"),
    "sculk_horn": ("horn", "warden", "bone", "sapphire"),
    "ash_greatsword": ("greatsword", "ember", "dark", "ember"),
    "golden_mace": ("mace", "gold", "gold", "ruby"),
    "soul_scythe": ("scythe", "void", "bone", "ice"),
    "void_greatblade": ("greatsword", "void", "purpur", "amethyst"),
    "clockmaker_pendulum": ("cane", "brass", "dark", "aether"),
    "cartographer_blade": ("sword", "cartographer", "wood", "emerald"),
    "telluric_hammer": ("hammer", "lithite", "wood", "emerald"),
    "storm_staff": ("staff", "storm", "dark", "sapphire"),
    "ember_scythe": ("scythe", "ember", "blaze", "ember"),
    "void_spear": ("spear", "void", "purpur", "amethyst"),
    "frost_blade": ("blade", "frost", "bone", "ice"),
    "light_staff": ("staff", "light", "gold", "gold"),
    "fire_staff": ("staff", "ember", "dark", "ruby"),
    "frost_staff": ("staff", "frost", "bone", "ice"),
    "thunder_staff": ("staff", "storm", "dark", "sapphire"),
    "healing_staff": ("staff", "light", "wood", "emerald"),
    "levitation_wand": ("wand", "void", "bone", "amethyst"),
    "steam_cane": ("cane", "iron", "dark", "gold"),
    "builder_wand": ("wand", "gold", "wood", "emerald"),
    "master_builder_wand": ("wand", "lithite", "dark", "amethyst"),
    "ward_orb": ("orb", "void", "gold", "amethyst"),
}

DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "firstperson_righthand": {"rotation": [0, -90, 20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "firstperson_lefthand": {"rotation": [0, 90, -20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
}


def model(item_id):
    arch, *_ = HELD[item_id]
    tex = f"wayfarers:item/3d/{item_id}"
    elements = []
    for x0, y0, z0, x1, y1, z1, key in ARCHETYPES[arch]():
        uv = _cell_uv(key)
        elements.append({"from": [x0, y0, z0], "to": [x1, y1, z1],
                         "faces": {f: {"uv": uv, "texture": "#t"} for f in ("north", "south", "east", "west", "up", "down")}})
    return {"textures": {"t": tex, "particle": tex}, "elements": elements, "display": DISPLAY}


def item_definition(item_id):
    flat = {"type": "minecraft:model", "model": f"wayfarers:item/{item_id}"}
    return {"model": {"type": "minecraft:select", "property": "minecraft:display_context",
                      "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": flat}],
                      "fallback": {"type": "minecraft:model", "model": f"wayfarers:item/{item_id}_3d"}}}


def textures():
    out = {}
    for item_id, (arch, mat, handle, accent) in HELD.items():
        out[f"item/3d/{item_id}"] = palette(mat, handle, accent)
    return out

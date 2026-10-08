"""3D models for weapons and staves held in hand (the inventory keeps the 2D sprite).

Each model is built from cuboids by an archetype function and textured from a small per-item palette texture
(textures/item/3d/<id>.png): 4x4 cells of flat colours (handle, metal light/mid/dark, accent, glow, plus the fixed
steampunk brass, cream, ink and steel), each face sampling the centre of its cell. The item definition switches on the display context: gui, ground, fixed and
on_shelf show the sprite, everything else the 3D model.

Coordinates are model pixels; the grip sits around y 6-10 (the model centre), so hands hold the handle.
"""
from .png import Canvas
from .sprites import ACCENTS, HANDLES, MATERIALS

CELLS = ["handle", "handle_dark", "light", "mid", "dark", "outline", "accent", "accent_dark", "glow", "wrap",
         "brass", "brass_dark", "cream", "ink", "steel", "iron_dark"]
# fixed steampunk cells (STYLE_STEAMPUNK.md)
FIXED = {"brass": (214, 172, 80), "brass_dark": (150, 108, 44), "cream": (232, 218, 186), "ink": (40, 32, 30),
         "steel": (176, 176, 188), "iron_dark": (58, 52, 54)}


def _cell_uv(key):
    i = CELLS.index(key)
    cx, cy = i % 4, i // 4
    return [cx * 4 + 1, cy * 4 + 1, cx * 4 + 3, cy * 4 + 3]


def palette(material, handle, accent, glow=None):
    from .metals import PALETTES
    light, mid, dark, outline = MATERIALS.get(material) or PALETTES[material]
    hl, hd = HANDLES[handle]
    gl, gd = ACCENTS[accent]
    colors = {"handle": hl, "handle_dark": hd, "light": light, "mid": mid, "dark": dark, "outline": outline,
              "accent": gl, "accent_dark": gd, "glow": glow or tuple(min(255, int(c * 0.55 + 255 * 0.45)) for c in gl[:3]),
              "wrap": tuple(int(c * 0.55) for c in hd), **FIXED}
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


def staff(orb="glow", crown="accent", head="orb"):
    out = _shaft(-4, 22, 1.5) + _grip(5, 10, 2.0) + [box(6.75, -5, 6.75, 9.25, -4, 9.25, "brass")]
    if head == "flame":
        # brass claw cradling a flame: glow blocks narrowing upwards, accent tongues around them
        out += [box(6.5, 20.5, 6.5, 9.5, 22, 9.5, "brass"),
                box(5.5, 22, 7.5, 6.5, 25, 8.5, "brass"), box(9.5, 22, 7.5, 10.5, 25, 8.5, "brass"),
                box(7.5, 22, 5.5, 8.5, 25, 6.5, "brass_dark"), box(7.5, 22, 9.5, 8.5, 25, 10.5, "brass_dark"),
                box(6, 22, 6, 10, 26, 10, "accent_dark"), box(6.5, 26, 6.5, 9.5, 28.5, 9.5, "accent"),
                box(7.25, 28.5, 7.25, 8.75, 31, 8.75, "glow"), box(5, 24, 7.5, 6, 27.5, 8.5, "accent_dark"),
                box(10, 24.5, 7.5, 11, 28.5, 8.5, "accent"), box(7.5, 25, 5, 8.5, 28, 6, "accent")]
    elif head == "snow":
        # six-armed ice crystal
        out += [box(6.75, 21, 6.75, 9.25, 22, 9.25, "steel"),
                box(7, 22, 7, 9, 30, 9, "light"), box(3.5, 25, 7.25, 12.5, 27, 8.75, "mid"),
                box(7.25, 25, 3.5, 8.75, 27, 12.5, "mid"), box(6.5, 25, 6.5, 9.5, 27, 9.5, "glow"),
                box(4, 24.5, 7.5, 5, 27.5, 8.5, "light"), box(11, 24.5, 7.5, 12, 27.5, 8.5, "light")]
    elif head == "bolt":
        # copper lightning rod: coils, a brass sphere, a bolt leaping off it
        out += [box(6.5, 19, 6.5, 9.5, 20, 9.5, "accent_dark"), box(6.5, 21, 6.5, 9.5, 22, 9.5, "accent_dark"),
                box(7.25, 22, 7.25, 8.75, 25, 8.75, "steel"), box(6.5, 25, 6.5, 9.5, 28, 9.5, "brass"),
                box(9.5, 27, 7.75, 11, 28, 8.25, "glow"), box(10.5, 28, 7.75, 11.5, 30, 8.25, "glow"),
                box(11, 29.5, 7.75, 13, 30.5, 8.25, "glow")]
    elif head == "cross":
        # brass halo around a glowing cross
        out += [box(6.5, 21, 6.5, 9.5, 22, 9.5, "brass"),
                box(3.5, 22, 7.5, 4.5, 30, 8.5, "brass"), box(11.5, 22, 7.5, 12.5, 30, 8.5, "brass"),
                box(4.5, 30, 7.5, 11.5, 31, 8.5, "brass"), box(4.5, 22, 7.5, 11.5, 23, 8.5, "brass_dark"),
                box(7, 23, 7, 9, 30, 9, "glow"), box(5, 25.5, 7, 11, 27.5, 9, "glow")]
    elif head == "sun":
        # radiant disc with rays
        out += [box(6.5, 21, 6.5, 9.5, 22, 9.5, "brass"), box(5, 22.5, 7, 11, 28.5, 9, "accent"),
                box(6, 23.5, 6.6, 10, 27.5, 9.4, "glow"),
                box(7.5, 28.5, 7.5, 8.5, 31, 8.5, "light"), box(2.5, 25, 7.5, 5, 26, 8.5, "light"),
                box(11, 25, 7.5, 13.5, 26, 8.5, "light"), box(3.5, 28, 7.5, 5, 29.5, 8.5, "mid"),
                box(11, 28, 7.5, 12.5, 29.5, 8.5, "mid"), box(3.5, 21.5, 7.5, 5, 23, 8.5, "mid"),
                box(11, 21.5, 7.5, 12.5, 23, 8.5, "mid")]
    elif head == "root":
        # gnarled branch curling around a seed of light, leaves
        out += [box(6, 20, 7, 7.5, 27, 8.5, "handle"), box(9, 21, 7.5, 10.5, 28, 9, "handle_dark"),
                box(7, 27, 7, 10, 28.5, 8.5, "handle"), box(6.75, 22.5, 6.75, 9.25, 25, 9.25, "glow"),
                box(4, 25, 7.5, 6, 26, 8.5, "accent"), box(10.5, 23, 7.5, 12.5, 24, 8.5, "accent_dark"),
                box(8, 28.5, 7.5, 9, 30, 8.5, "accent")]
    else:
        out += [box(6.5, 21, 6.5, 9.5, 22, 9.5, crown),
                box(5.5, 22, 7.5, 6.5, 25, 8.5, crown), box(9.5, 22, 7.5, 10.5, 25, 8.5, crown),
                box(7.5, 22, 5.5, 8.5, 25, 6.5, crown), box(7.5, 22, 9.5, 8.5, 25, 10.5, crown),
                box(6.5, 22.5, 6.5, 9.5, 25.5, 9.5, orb), box(7.25, 25.5, 7.25, 8.75, 27, 8.75, orb)]
    return out


def pendulum():
    """Clockmaker's Pendulum: dark iron grip, brass rod, a lens bob with a cream dial and an aether core."""
    out = [box(7, 2, 7, 9, 9, 9, "iron_dark"), box(6.5, 0.5, 6.5, 9.5, 2, 9.5, "brass"),
           box(6.5, 9, 6.5, 9.5, 10.5, 9.5, "brass"), box(7.5, 10.5, 7.5, 8.5, 19.5, 8.5, "brass"),
           box(7, 13, 7, 9, 14, 9, "brass_dark")]
    # the bob: stacked slabs make a disc (radius ~5) in the x-y plane, 2.4 px thick
    for x0, y0, x1, y1 in ((3, 21.5, 13, 27.5), (4, 20, 12, 29), (5.5, 19, 10.5, 30)):
        out.append(box(x0, y0, 6.8, x1, y1, 9.2, "brass"))
    for z0, z1, h0, h1 in ((6.5, 6.8, 6.3, 6.5), (9.2, 9.5, 9.5, 9.7)):
        out += [box(4.5, 22, z0, 11.5, 27, z1, "cream"), box(5.5, 21, z0, 10.5, 28, z1, "cream"),
                box(7.75, 24.5, h0, 8.25, 27.5, h1, "ink"), box(8.25, 24.25, h0, 10, 24.75, h1, "ink")]
    out += [box(7, 23.75, 6.2, 9, 25.25, 9.8, "glow"), box(7.5, 30, 7.5, 8.5, 31, 8.5, "accent")]
    return out


def anchor():
    """Helmsman's Anchor: a wrapped grip with a brass ring at the butt, a stock across the shank, a heavy iron shank
    and the crown: two curved arms with barbed flukes, an amber rivet glowing at the middle."""
    out = _shaft(-2, 12, 2.0, "iron_dark") + _grip(0, 8, 2.4)
    out += [box(6.5, -4, 7.5, 9.5, -2, 8.5, "brass"), box(6, -3.5, 7.5, 6.8, -1.2, 8.5, "brass"),
            box(9.2, -3.5, 7.5, 10, -1.2, 8.5, "brass"),                          # the ring
            box(2.5, 10, 7, 13.5, 11.5, 9, "brass_dark"), box(2, 9.8, 6.8, 3, 11.7, 9.2, "brass"),
            box(13, 9.8, 6.8, 14, 11.7, 9.2, "brass"),                            # the stock
            box(6.8, 11.5, 6.8, 9.2, 26, 9.2, "mid"), box(6.5, 18, 6.5, 9.5, 19, 9.5, "brass")]
    # the crown: stacked segments along an arc (radius ~7) under the shank's tip, curving back up
    for x0, y0, x1, y1, k in ((5.5, 25, 10.5, 28, "dark"), (3, 24, 5.5, 27, "mid"), (10.5, 24, 13, 27, "mid"),
                              (1.5, 21.5, 3.5, 25, "mid"), (12.5, 21.5, 14.5, 25, "mid"),
                              (0.5, 19, 2.5, 22, "light"), (13.5, 19, 15.5, 22, "light")):
        out.append(box(x0, y0, 7, x1, y1, 9, k))
    out += [box(-0.5, 17, 6.5, 3, 19.5, 9.5, "dark"), box(13, 17, 6.5, 16.5, 19.5, 9.5, "dark"),   # flukes
            box(7, 27.6, 6.6, 9, 29, 9.4, "glow"), box(7.25, 25.5, 6.4, 8.75, 27, 9.6, "accent")]
    return out


def ladle():
    """Crone's Ladle: a long dark handle, an iron neck and a deep bowl brimming with glowing brew."""
    out = _shaft(-4, 15, 1.6, "handle") + _grip(4, 10, 2.1)
    out += [box(7.4, 15, 7.4, 8.6, 20, 8.6, "mid"), box(7, 19, 6, 9, 20, 8.6, "mid"),
            box(4.5, 19, 2.5, 11.5, 23, 9.5, "mid"), box(4, 22, 2, 12, 23.5, 10, "light"),
            box(5, 22.6, 3, 11, 23.7, 9, "glow"), box(6, 23.7, 4.5, 7, 24.7, 5.5, "accent"),
            box(9, 23.7, 6.5, 10, 25.2, 7.5, "glow"), box(5, 18.5, 3, 11, 19, 9, "dark")]
    return out


def flail():
    """Pharaoh's Flail: a gold handle banded with lapis, three bead strands hanging from its crook."""
    out = []
    for i, y in enumerate(range(-3, 17, 2)):
        out.append(box(7.1, y, 7.1, 8.9, y + 2, 8.9, "accent" if i % 3 == 1 else "mid"))
    out += [box(6.5, 17, 6.5, 9.5, 18.5, 9.5, "light"), box(7, 18.5, 7, 9, 19.5, 9, "accent")]
    for sx, sz, n in ((4.5, 8, 7), (8, 10.5, 6), (11, 8, 7)):
        for k in range(n):
            y = 16.5 - k * 1.3
            out.append(box(sx - 0.6, y - 1.1, sz - 0.6, sx + 0.6, y, sz + 0.6, "accent" if k % 2 else "light"))
    out += [box(4.5, 17, 7.5, 11.5, 18, 8.5, "mid"), box(7.5, 17, 8.5, 8.5, 18, 11, "mid")]
    return out


def bell_hammer():
    """Bell Hammer: a gilded hammer head, a bronze bell hung from one end."""
    out = hammer()
    out += [box(10.5, 15.5, 7.5, 11.5, 18, 8.5, "ink"),
            box(9.5, 13.5, 6.5, 12.5, 15.5, 9.5, "brass"), box(9, 11.5, 6, 13, 13.5, 10, "brass"),
            box(8.5, 10.5, 5.5, 13.5, 11.5, 10.5, "brass_dark"), box(10.5, 9.5, 7.5, 11.5, 10.5, 8.5, "ink")]
    return out


def forge_hammer():
    """Forge King's Hammer: a black anvil-iron head split by molten seams, brass faces."""
    out = _shaft(-2, 18) + _grip(4, 10, 2.2)
    out += [box(3.5, 18, 5, 12.5, 24, 11, "iron_dark"), box(2.5, 18.5, 5.5, 3.5, 23.5, 10.5, "brass"),
            box(12.5, 18.5, 5.5, 13.5, 23.5, 10.5, "brass"), box(6.5, 17, 6.5, 9.5, 18, 9.5, "brass_dark"),
            box(6, 18.5, 4.8, 6.8, 23.5, 5, "glow"), box(9.2, 18.5, 4.8, 10, 23.5, 5, "glow"),
            box(6, 18.5, 11, 6.8, 23.5, 11.2, "glow"), box(9.2, 18.5, 11, 10, 23.5, 11.2, "glow"),
            box(6, 24, 6, 10, 24.2, 10, "accent"), box(7, 24.2, 7, 9, 24.6, 9, "glow")]
    return out


def crystal_spear():
    """Crystal Fang: a bone haft driven into a cluster of jagged crystals."""
    out = _shaft(-2, 22) + _grip(5, 10, 2.2) + [box(6.75, 21, 6.75, 9.25, 22.5, 9.25, "steel")]
    out += [box(7, 22.5, 7, 9, 29, 9, "mid"), box(7.5, 29, 7.5, 8.5, 31, 8.5, "light"),
            box(5, 22, 7.5, 6.75, 26.5, 8.5, "light"), box(9.25, 22, 7.5, 11, 25.5, 8.5, "dark"),
            box(7.5, 22, 9.25, 8.5, 25, 11, "light"), box(7.5, 22, 5, 8.5, 24.5, 6.75, "dark"),
            box(4.5, 26.5, 7.75, 5.5, 27.5, 8.25, "glow")]
    return out


def axe():
    """Axe: a broad blade flaring from a brass socket, an iron poll behind."""
    out = _shaft(-3, 19) + _grip(3, 9, 2.1)
    out += [box(6.5, 15, 6.5, 9.5, 19, 9.5, "brass"), box(2.5, 13.5, 7.4, 6.5, 20.5, 8.6, "mid"),
            box(1, 12.5, 7.5, 2.5, 21.5, 8.5, "light"), box(2.5, 20.5, 7.5, 5, 21.5, 8.5, "dark"),
            box(9.5, 15.5, 7, 12, 18.5, 9, "iron_dark")]
    return out


def pickaxe():
    """Pickaxe: an arched head of two tapering points on a brass socket."""
    out = _shaft(-3, 19) + _grip(3, 9, 2.1)
    out += [box(6.5, 16.5, 6.5, 9.5, 19.5, 9.5, "brass"), box(1.5, 17, 7.25, 14.5, 19.5, 8.75, "mid"),
            box(-1, 15.5, 7.4, 1.5, 18.5, 8.6, "light"), box(-2, 14, 7.6, -1, 16, 8.4, "light"),
            box(14.5, 15.5, 7.4, 17, 18.5, 8.6, "dark"), box(17, 14, 7.6, 18, 16, 8.4, "dark"),
            box(3, 19.5, 7.5, 13, 20, 8.5, "light")]
    return out


def shovel():
    """Shovel: a spade blade with a raised spine on a dark iron socket."""
    out = _shaft(-3, 16) + _grip(3, 9, 2.1)
    out += [box(6.75, 15, 6.75, 9.25, 17, 9.25, "iron_dark"), box(5, 17, 7.4, 11, 24, 8.6, "mid"),
            box(6, 24, 7.5, 10, 25.5, 8.5, "light"), box(7.5, 17, 8.6, 8.5, 23, 9, "light"),
            box(5, 17, 7.3, 11, 18, 8.7, "dark")]
    return out


def hoe():
    """Hoe: a long haft, the flat head bent down into a broad blade."""
    out = _shaft(-3, 20) + _grip(3, 9, 2.1)
    out += [box(6.5, 18, 7, 13, 20, 9, "mid"), box(11, 14, 7.2, 13.5, 18, 8.8, "light"),
            box(6.75, 17, 6.75, 9.25, 18, 9.25, "brass")]
    return out


def wand_block():
    """Builder's wands: a rod with brass rings, a block hovering over the tip."""
    out = _shaft(-2, 18, 1.2) + _grip(5, 9, 1.6)
    out += [box(7, 17, 7, 9, 18, 9, "brass"), box(6.75, 11, 6.75, 9.25, 12, 9.25, "brass"),
            box(5.5, 20, 5.5, 10.5, 25, 10.5, "accent"), box(6, 25, 6, 10, 25.3, 10, "glow"),
            box(5.2, 19.5, 5.2, 6.2, 20.5, 6.2, "brass"), box(9.8, 19.5, 9.8, 10.8, 20.5, 10.8, "brass")]
    return out


def caged_orb():
    """Ward Orb: a glowing orb inside a brass cage."""
    return orb() + [box(4, 4.5, 7.6, 4.6, 11.5, 8.4, "brass"), box(11.4, 4.5, 7.6, 12, 11.5, 8.4, "brass"),
                    box(7.6, 11, 7.6, 8.4, 12.5, 8.4, "brass"), box(5.5, 11, 5.5, 10.5, 11.6, 10.5, "brass_dark"),
                    box(5.5, 4.4, 5.5, 10.5, 5, 10.5, "brass_dark"), box(6, 3, 6, 10, 4.4, 10, "brass")]


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


def chisel():
    """Engraver's Chisel: wooden grip with a struck brass cap, brass ferrule, steel shank, flat blade."""
    out = [box(6.8, -3, 6.8, 9.2, 9, 9.2, "handle"), box(7.0, -2.5, 9.0, 9.0, 8.5, 9.3, "handle_dark"),
           box(6.5, -4.5, 6.5, 9.5, -3, 9.5, "accent"), box(6.5, 9, 6.5, 9.5, 11, 9.5, "accent"),
           box(6.7, 10.5, 6.7, 9.3, 11.5, 9.3, "accent_dark"),
           box(7.4, 11.5, 7.4, 8.6, 16, 8.6, "mid"),
           box(6.6, 16, 7.5, 9.4, 21, 8.5, "light"), box(6.6, 16, 8.5, 9.4, 20, 8.7, "dark"),
           box(6.6, 21, 7.75, 9.4, 21.6, 8.25, "light")]
    return out


def orb():
    return [box(5, 5, 5, 11, 11, 11, "glow"), box(4.5, 7, 7, 11.5, 9, 9, "accent"), box(7, 4, 7, 9, 5, 9, "accent_dark")]


# ------------------------------------------------------------------ reworked and boss archetypes
def _disc(cx, cy, z0, z1, r, key, axis="z"):
    """A round disc (radius ~r) of stacked slabs, in the x-y plane between z0 and z1."""
    out = []
    for k, (wf, hf) in enumerate(((1.0, 0.55), (0.82, 0.82), (0.55, 1.0))):
        out.append(box(cx - r * wf, cy - r * hf, z0, cx + r * wf, cy + r * hf, z1, key))
    return out


def _ball(cx, cy, cz, r, key):
    """A rough sphere: three crossed slabs."""
    a, b = r, r * 0.62
    return [box(cx - a, cy - b, cz - b, cx + a, cy + b, cz + b, key),
            box(cx - b, cy - a, cz - b, cx + b, cy + a, cz + b, key),
            box(cx - b, cy - b, cz - a, cx + b, cy + b, cz + a, key)]


def broadsword(length=17, width=4.0, guard=10):
    """A knightly sword: a ridged blade with a darker fuller, bevelled edges, a ricasso, a winged guard and a
    wheel pommel."""
    a = 8 - width / 2
    top = 10 + length
    out = _grip(3, 8.5) + [box(6.75, 1, 6.75, 9.25, 3, 9.25, "accent"), box(7.25, 0.5, 7.25, 8.75, 1, 8.75, "accent_dark")]
    out += [box(8 - guard / 2, 8.5, 6.75, 8 + guard / 2, 10, 9.25, "accent_dark"),
            box(8 - guard / 2 - 1, 9, 7, 8 - guard / 2, 11, 9, "accent"),
            box(8 + guard / 2, 9, 7, 8 + guard / 2 + 1, 11, 9, "accent"),
            box(7, 10, 7.1, 9, 11.5, 8.9, "accent")]                                     # the ricasso collar
    out += [box(a, 10, 7.3, a + width, top, 8.7, "mid"),
            box(a - 0.4, 11, 7.55, a, top - 1, 8.45, "light"),                            # bevelled edges
            box(a + width, 11, 7.55, a + width + 0.4, top - 1, 8.45, "light"),
            box(7.6, 11.5, 7.1, 8.4, top - 2, 8.9, "dark"),                               # the fuller
            box(a + 0.5, top, 7.45, a + width - 0.5, top + 1.5, 8.55, "light"),
            box(7.25, top + 1.5, 7.6, 8.75, top + 2.5, 8.4, "light")]
    return out


def sentinel_greatsword():
    """Sentinel's Greatsword: the Bronze Sentinel's blade cut down to a man's size: a broad tarnished-bronze blade
    with a verdigris fuller set with glowing gold runes, a wide crossguard ending in down-turned quillons, a leather
    grip and a heavy disc pommel."""
    out = _grip(2, 8.5, 2.2) + [box(6.5, 0, 6.5, 9.5, 2, 9.5, "brass"), box(7, -0.8, 7, 9, 0, 9, "brass_dark")]
    out += [box(2, 8.5, 6.6, 14, 10.2, 9.4, "brass_dark"), box(1, 7, 6.9, 2.6, 10.2, 9.1, "brass"),
            box(13.4, 7, 6.9, 15, 10.2, 9.1, "brass"), box(6.5, 10.2, 6.9, 9.5, 11.6, 9.1, "brass")]
    out += [box(5.5, 11.6, 7.25, 10.5, 29.5, 8.75, "mid"),
            box(5.1, 12.5, 7.5, 5.5, 29, 8.5, "light"), box(10.5, 12.5, 7.5, 10.9, 29, 8.5, "light"),
            box(7.4, 12, 7.1, 8.6, 27.5, 8.9, "accent_dark")]
    for y in (13.5, 16.5, 19.5, 22.5, 25.5):
        out.append(box(7.6, y, 7.0, 8.4, y + 1.2, 9.0, "glow"))                            # gold runes in the fuller
    out += [box(6.5, 29.5, 7.4, 9.5, 31, 8.6, "light"), box(7.4, 31, 7.6, 8.6, 32, 8.4, "light")]
    return out


def crook():
    """Dune King's Crook: a gold-and-lapis banded staff ending in a tight shepherd's hook, a jewelled cobra rearing
    where the hook springs from the shaft."""
    out = []
    for i, y in enumerate(range(-4, 20, 2)):
        out.append(box(7.1, y, 7.1, 8.9, y + 2, 8.9, "accent" if i % 3 == 2 else "mid"))
    out += [box(6.6, -5, 6.6, 9.4, -4, 9.4, "light"), box(6.7, 19.5, 6.7, 9.3, 21, 9.3, "light")]
    # the hook: up, over and down in square segments
    out += [box(7.1, 21, 7.1, 8.9, 27, 8.9, "mid"), box(7.3, 27, 7.1, 9.5, 29.5, 8.9, "mid"),
            box(9.3, 28.5, 7.1, 12.5, 30.5, 8.9, "light"), box(12, 27, 7.1, 14.2, 30, 8.9, "mid"),
            box(13, 23.5, 7.1, 14.8, 27.2, 8.9, "mid"), box(12.4, 21.6, 7.1, 14.4, 23.6, 8.9, "accent"),
            box(7.25, 25, 7.0, 8.9, 26, 9.0, "accent")]
    # the cobra: a hood flaring behind the head, a ruby eye
    out += [box(5.2, 21.5, 7.6, 7.1, 25.5, 8.4, "accent_dark"), box(4.6, 22, 7.7, 5.2, 25, 8.3, "accent"),
            box(5.4, 25.5, 7.4, 7.2, 26.6, 8.6, "mid"), box(5.0, 25.7, 7.3, 5.6, 26.3, 8.7, "glow")]
    return out


def chain_flail():
    """Jailer's Burning Chain: a wrapped iron grip with a gilded pommel and collar, a ring, a short chain of
    alternating links and a spiked blackstone fetter-ball split by glowing cracks."""
    out = [box(7, -1, 7, 9, 9, 9, "wrap"), box(6.5, -2.5, 6.5, 9.5, -1, 9.5, "brass"),
           box(6.6, 9, 6.6, 9.4, 13, 9.4, "iron_dark"), box(6.2, 11, 6.2, 9.8, 12, 9.8, "brass"),
           box(7, 13, 7.6, 9, 15, 8.4, "brass")]                                           # the ring
    # the chain: links alternating flat and edge-on, leaning out to one side
    for k, (x, y) in enumerate(((8, 14.5), (8.6, 16.6), (9.3, 18.6), (10.0, 20.6))):
        if k % 2 == 0:
            out.append(box(x - 1, y, 7.6, x + 1, y + 2.6, 8.4, "steel"))
        else:
            out.append(box(x - 0.4, y, 7, x + 0.4, y + 2.6, 9, "steel"))
    # the ball: a rough sphere with a gold band, spikes and ember cracks
    cx, cy, cz = 10.8, 26.0, 8.0
    out += [box(cx - 3, cy - 2.2, cz - 2.2, cx + 3, cy + 2.2, cz + 2.2, "iron_dark"),
            box(cx - 2.2, cy - 3, cz - 2.2, cx + 2.2, cy + 3, cz + 2.2, "iron_dark"),
            box(cx - 2.2, cy - 2.2, cz - 3, cx + 2.2, cy + 2.2, cz + 3, "dark"),
            box(cx - 3.2, cy - 0.5, cz - 3.2, cx + 3.2, cy + 0.5, cz + 3.2, "brass"),
            box(cx - 0.6, cy + 0.8, cz - 3.1, cx + 0.4, cy + 2.4, cz - 2.9, "glow"),
            box(cx + 2.9, cy - 2.2, cz - 0.5, cx + 3.1, cy - 0.6, cz + 0.6, "glow"),
            box(cx - 1.2, cy - 2.6, cz + 2.9, cx - 0.2, cy - 1.0, cz + 3.1, "glow")]
    for dx, dy, dz in ((0, 4, 0), (4, 0, 0), (-4, 0, 0), (0, 0, 4), (0, 0, -4), (0, -4, 0)):
        out.append(box(cx + dx * 0.88 - 0.8, cy + dy * 0.88 - 0.8, cz + dz * 0.88 - 0.8,
                       cx + dx * 0.88 + 0.8, cy + dy * 0.88 + 0.8, cz + dz * 0.88 + 0.8, "brass"))
    return out


def trident_big():
    """A great trident: a long haft with a gold collar, a broad crossbar and three barbed prongs, the middle one
    longest."""
    out = _shaft(-3, 20, 1.6) + _grip(4, 10, 2.2)
    out += [box(6.6, 19, 6.6, 9.4, 21, 9.4, "accent_dark"), box(3.5, 21, 7.2, 12.5, 22.5, 8.8, "mid"),
            box(7, 22.5, 7.25, 9, 30, 8.75, "mid"), box(7.4, 30, 7.4, 8.6, 32, 8.6, "light"),
            box(3.5, 22.5, 7.3, 5, 28, 8.7, "mid"), box(11, 22.5, 7.3, 12.5, 28, 8.7, "mid"),
            box(3.7, 28, 7.5, 4.8, 29.5, 8.5, "light"), box(11.2, 28, 7.5, 12.3, 29.5, 8.5, "light"),
            box(2.6, 26, 7.6, 3.5, 27.5, 8.4, "light"), box(12.5, 26, 7.6, 13.4, 27.5, 8.4, "light"),
            box(6.2, 27.5, 7.6, 7, 29, 8.4, "light"), box(9, 27.5, 7.6, 9.8, 29, 8.4, "light"),
            box(7.5, 21.2, 6.9, 8.5, 22.3, 9.1, "glow")]
    return out


def fang():
    """Jade Fang: a curved fang of jade bound to a gold hilt, a thin glowing seam of jade light along its edge."""
    out = _grip(3, 8.5) + [box(6.75, 1.5, 6.75, 9.25, 3, 9.25, "accent"), box(5.5, 8.5, 6.8, 10.5, 10, 9.2, "accent_dark")]
    for i, (x0, y0, x1, y1) in enumerate(((6.4, 10, 9.8, 14), (6.8, 14, 10.4, 18), (7.4, 18, 10.6, 21.5),
                                          (8.2, 21.5, 10.4, 24.5), (9, 24.5, 10.2, 26.5))):
        out.append(box(x0, y0, 7.35, x1, y1, 8.65, "mid"))
        out.append(box(x0 - 0.35, y0, 7.6, x0, y1 - 0.5, 8.4, "glow" if i < 4 else "light"))   # the cutting edge
    out.append(box(9.2, 11, 7.2, 9.8, 20, 8.8, "dark"))                                         # the spine groove
    return out


def grimoire():
    """Forbidden Grimoire: a heavy tome held shut by a brass clasp, a leather cover with raised bands on the spine,
    cream page edges, a glowing eye sigil on the cover."""
    return [box(4, 3, 6, 12, 14, 10, "mid"), box(4.4, 3.5, 6.4, 11.6, 13.5, 9.6, "cream"),
            box(3.6, 2.6, 5.6, 12.4, 14.4, 6.2, "dark"), box(3.6, 2.6, 9.8, 12.4, 14.4, 10.4, "dark"),
            box(3.2, 2.6, 5.6, 4, 14.4, 10.4, "dark"),                                   # the spine
            box(3, 4.5, 5.5, 4.2, 5.3, 10.5, "brass"), box(3, 11.7, 5.5, 4.2, 12.5, 10.5, "brass"),
            box(11.6, 7.5, 5.3, 12.8, 9.5, 10.7, "brass"),                              # the clasp
            box(6.5, 7, 5.3, 9.5, 10, 5.6, "accent_dark"), box(7.25, 8, 5.1, 8.75, 9, 5.4, "glow"),
            box(5, 12.5, 5.4, 6, 13.5, 5.6, "brass"), box(10, 3.5, 5.4, 11, 4.5, 5.6, "brass")]


def gauntlet():
    """Rune Fist: a stone gauntlet: a flared cuff, a broad back-of-hand plate with a glowing rune, four knuckle
    plates and a thumb."""
    out = [box(4.5, 0, 4.5, 11.5, 6, 11.5, "dark"), box(4, 5, 4, 12, 6.5, 12, "mid"),
           box(4.8, 6.5, 4.8, 11.2, 12, 11.2, "mid"), box(4.5, 7.5, 3.8, 11.5, 11, 4.8, "light"),
           box(6.5, 8.3, 3.5, 9.5, 10.3, 3.8, "glow"), box(11.2, 7, 6, 12.6, 10.5, 9, "light")]
    for i, x in enumerate((4.9, 6.5, 8.1, 9.7)):
        out += [box(x, 12, 4.6, x + 1.5, 14.5, 9.5, "mid"), box(x, 14.5, 4.6, x + 1.5, 15.5, 7.5, "light")]
    out.append(box(5, 2, 4.2, 11, 3, 4.5, "glow"))
    return out


def horn_curved():
    """Sculk Horn: a war horn curling like a ram's horn: a wide flared bell with a glowing sculk throat, ribbed
    segments sweeping up and around, a bone mouthpiece at the tip."""
    out = [box(3, 9.5, 5.5, 7.5, 14.5, 10.5, "mid"), box(2.4, 9, 5, 3, 15, 11, "accent_dark"),         # the bell
           box(2.3, 10.2, 6.2, 2.5, 13.8, 9.8, "glow"),
           box(7.5, 10, 6.2, 10.8, 13.5, 9.8, "light"), box(10.5, 8.5, 6.5, 12.8, 12.5, 9.5, "mid"),
           box(12, 6, 6.5, 14, 10, 9.5, "light"), box(11, 3.5, 6.8, 13.5, 6.5, 9.2, "mid"),
           box(8.5, 2.5, 7, 11.5, 5, 9, "light"), box(7, 3.5, 7.2, 9, 6, 8.8, "handle"),
           box(10.4, 9.5, 6.0, 10.9, 13.7, 10.0, "accent_dark"), box(11.9, 5.8, 6.3, 14.1, 6.3, 9.7, "accent_dark")]
    return out


def ward_orb():
    """Ward Orb: a round glowing orb caged in brass hoops on a brass stand."""
    out = _ball(8, 8, 8, 3.2, "glow")
    out += [box(4.2, 4.5, 7.5, 4.9, 11.5, 8.5, "brass"), box(11.1, 4.5, 7.5, 11.8, 11.5, 8.5, "brass"),
            box(7.5, 4.5, 4.2, 8.5, 11.5, 4.9, "brass_dark"), box(7.5, 4.5, 11.1, 8.5, 11.5, 11.8, "brass_dark"),
            box(4.9, 11.2, 7.5, 11.1, 11.9, 8.5, "brass"), box(7.5, 11.2, 4.9, 8.5, 11.9, 11.1, "brass"),
            box(7.4, 11.9, 7.4, 8.6, 13, 8.6, "accent"),
            box(5.5, 3.5, 5.5, 10.5, 4.5, 10.5, "brass"), box(6.5, 2, 6.5, 9.5, 3.5, 9.5, "brass_dark")]
    return out


def halo_glaive():
    """Glaive of the Broken Halo: a long pale haft banded with gold, a gold collar, and for a blade a crescent of halo
    (a broken ring of gold segments with an inner edge of light) pierced by a spike."""
    import math
    out = _shaft(-6, 21, 1.6, "light") + _grip(3, 9, 2.2)
    out += [box(6.8, -7, 6.8, 9.2, -6, 9.2, "accent_dark"), box(7.1, 14, 7.1, 8.9, 15, 8.9, "accent"),
            box(6.4, 20, 6.4, 9.6, 21.5, 9.6, "accent"), box(6.9, 21.5, 6.9, 9.1, 22.5, 9.1, "accent_dark")]
    cx, cy, r = 8.0, 25.4, 5.4
    for a in range(-40, 221, 20):
        if 70 <= a <= 90:
            continue                                                   # the break in the ring
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        out.append(box(x - 1.1, y - 1.1, 7.3, x + 1.1, y + 1.1, 8.7, "accent"))
        if 0 <= a <= 180:                                              # the honed outer edge
            xo, yo = cx + (r + 1.2) * math.cos(math.radians(a)), cy + (r + 1.2) * math.sin(math.radians(a))
            yo = min(yo, 31.4)
            out.append(box(xo - 0.7, yo - 0.6, 7.7, xo + 0.7, yo + 0.6, 8.3, "light"))
        if -20 <= a <= 200 and a % 40 == 0:
            xi, yi = cx + (r - 1.3) * math.cos(math.radians(a)), cy + (r - 1.3) * math.sin(math.radians(a))
            out.append(box(xi - 0.5, yi - 0.5, 7.6, xi + 0.5, yi + 0.5, 8.4, "glow"))
    out += [box(7.5, 22.5, 7.5, 8.5, 30, 8.5, "glow"), box(7.7, 30, 7.7, 8.3, 31, 8.3, "light")]
    return out


ARCHETYPES = {"sword": broadsword, "greatsword": lambda: broadsword(length=19, width=5.0, guard=11), "blade": blade, "spear": spear,
              "trident": lambda: spear("trident"), "lance": lambda: spear("lance"), "hammer": hammer,
              "mace": mace, "staff": staff, "cane": cane, "scythe": scythe, "book": book, "fist": fist,
              "horn": horn, "wand": wand, "orb": orb, "chisel": chisel,
              "staff_flame": lambda: staff(head="flame"), "staff_snow": lambda: staff(head="snow"),
              "staff_bolt": lambda: staff(head="bolt"), "staff_cross": lambda: staff(head="cross"),
              "staff_sun": lambda: staff(head="sun"), "staff_root": lambda: staff(head="root"),
              "pendulum": pendulum, "anchor": anchor, "ladle": ladle, "flail": flail, "bell_hammer": bell_hammer,
              "forge_hammer": forge_hammer, "crystal_spear": crystal_spear, "axe": axe, "pickaxe": pickaxe,
              "shovel": shovel, "hoe": hoe, "wand_block": wand_block, "caged_orb": caged_orb,
              "broadsword": broadsword, "sentinel_greatsword": sentinel_greatsword, "crook": crook, "chain_flail": chain_flail, "halo_glaive": halo_glaive,
              "trident_big": trident_big, "fang": fang, "grimoire": grimoire, "gauntlet": gauntlet,
              "horn_curved": horn_curved, "ward_orb": ward_orb}

# item id -> (archetype, material, handle, accent)
HELD = {
    "kings_trident": ("trident_big", "warden", "bone", "sapphire"),
    "bell_hammer": ("bell_hammer", "gold", "dark", "gold"),
    "forbidden_grimoire": ("grimoire", "map", "dark", "amethyst"),
    "pharaoh_flail": ("flail", "gold", "gold", "sapphire"),
    "jade_fang": ("fang", "lithite", "gold", "emerald"),
    "rootmother_staff": ("staff_root", "leather", "wood", "emerald"),
    "crone_ladle": ("ladle", "iron", "dark", "amethyst"),
    "gryphon_lance": ("lance", "iron", "gold", "sapphire"),
    "rune_fist": ("gauntlet", "lithite", "dark", "sapphire"),
    "forge_king_hammer": ("forge_hammer", "ember", "dark", "gold"),
    "crystal_fang": ("crystal_spear", "void", "bone", "amethyst"),
    "sculk_horn": ("horn_curved", "warden", "bone", "sapphire"),
    "ash_greatsword": ("greatsword", "ember", "dark", "ember"),
    "golden_mace": ("mace", "gold", "gold", "ruby"),
    "soul_scythe": ("scythe", "void", "bone", "ice"),
    "void_greatblade": ("greatsword", "void", "purpur", "amethyst"),
    "clockmaker_pendulum": ("pendulum", "brass", "dark", "aether"),
    "helmsman_anchor": ("anchor", "iron", "dark", "ember"),
    "sentinel_greatsword": ("sentinel_greatsword", "copper", "dark", "emerald"),
    "dune_king_crook": ("crook", "gold", "gold", "sapphire"),
    "jailer_chain": ("chain_flail", "ember", "dark", "ember"),
    "halo_glaive": ("halo_glaive", "light", "purpur", "gold"),
    "cartographer_blade": ("sword", "cartographer", "wood", "emerald"),
    "telluric_hammer": ("hammer", "lithite", "wood", "emerald"),
    "storm_staff": ("staff", "storm", "dark", "sapphire"),
    "ember_scythe": ("scythe", "ember", "blaze", "ember"),
    "void_spear": ("spear", "void", "purpur", "amethyst"),
    "frost_blade": ("blade", "frost", "bone", "ice"),
    "light_staff": ("staff_sun", "light", "gold", "gold"),
    "fire_staff": ("staff_flame", "ember", "dark", "ember"),
    "frost_staff": ("staff_snow", "frost", "bone", "ice"),
    "thunder_staff": ("staff_bolt", "storm", "dark", "gold"),
    "healing_staff": ("staff_cross", "light", "wood", "emerald"),
    "levitation_wand": ("wand", "void", "bone", "amethyst"),
    "steam_cane": ("cane", "iron", "dark", "gold"),
    "builder_wand": ("wand_block", "gold", "wood", "emerald"),
    "master_builder_wand": ("wand_block", "lithite", "dark", "amethyst"),
    "ward_orb": ("ward_orb", "void", "gold", "amethyst"),
    "chisel": ("chisel", "iron", "wood", "gold"),
    "excavator_pickaxe": ("pickaxe", "lithite", "wood", "emerald"),
    "lumber_axe": ("axe", "iron", "wood", "gold"),
}
# metal tools (wf/metals.py): brass on oak, mithril on dark wood
for _mid, _handle in (("brass", "wood"), ("mithril", "dark")):
    for _kind in ("sword", "pickaxe", "axe", "shovel", "hoe"):
        HELD[f"{_mid}_{_kind}"] = ("broadsword" if _kind == "sword" else _kind, _mid, _handle,
                                   "gold" if _mid == "brass" else "sapphire")

DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "firstperson_righthand": {"rotation": [0, -90, 20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "firstperson_lefthand": {"rotation": [0, 90, -20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
}


# everyday tools are held smaller than the boss weapons and staves (a vanilla sword spans about 1.2 blocks in hand)
SMALL = {"broadsword", "sword", "blade", "axe", "pickaxe", "shovel", "hoe", "chisel", "wand", "wand_block", "cane"}
# short, hand-sized things (a book, a gauntlet, a horn, an orb): held upright in the palm, not like a blade
COMPACT = {"book", "grimoire", "fist", "gauntlet", "horn", "horn_curved", "orb", "caged_orb", "ward_orb"}


def display(arch):
    """Display transforms of an archetype: DISPLAY scaled down for the small tools; compact items held upright in
    front of the palm and a little bigger, tilted toward the camera in first person."""
    d = {k: {kk: list(vv) for kk, vv in v.items()} for k, v in DISPLAY.items()}
    if arch in SMALL:
        for k in ("thirdperson_righthand", "thirdperson_lefthand"):
            d[k]["scale"] = [0.68, 0.68, 0.68]
            d[k]["translation"] = [0, 3.5, 0.5]
        for k in ("firstperson_righthand", "firstperson_lefthand"):
            d[k]["scale"] = [0.54, 0.54, 0.54]
            d[k]["translation"] = [1.13, 3.0, 0.8]
    elif arch in COMPACT:
        for k, sgn in (("thirdperson_righthand", 1), ("thirdperson_lefthand", -1)):
            d[k] = {"rotation": [75, 45 * sgn, 0], "translation": [0, 2.5, 1.5], "scale": [0.6, 0.6, 0.6]}
        for k, sgn in (("firstperson_righthand", 1), ("firstperson_lefthand", -1)):
            d[k] = {"rotation": [10, -45 * sgn, 0], "translation": [1.13, 4.5, 0.8], "scale": [0.6, 0.6, 0.6]}
    return d


def model(item_id):
    arch, *_ = HELD[item_id]
    tex = f"brasshaven:item/3d/{item_id}"
    elements = []
    for x0, y0, z0, x1, y1, z1, key in ARCHETYPES[arch]():
        uv = _cell_uv(key)
        el = {"from": [x0, y0, z0], "to": [x1, y1, z1],
              "faces": {f: {"uv": uv, "texture": "#t"} for f in ("north", "south", "east", "west", "up", "down")}}
        if key == "glow":
            el["light_emission"] = 12        # gems, runes and lenses shine even in a dark cave
        elements.append(el)
    return {"textures": {"t": tex, "particle": tex}, "elements": elements, "display": display(arch)}


def item_definition(item_id):
    flat = {"type": "minecraft:model", "model": f"brasshaven:item/{item_id}"}
    return {"model": {"type": "minecraft:select", "property": "minecraft:display_context",
                      "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": flat}],
                      "fallback": {"type": "minecraft:model", "model": f"brasshaven:item/{item_id}_3d"}}}


def textures():
    out = {}
    for item_id, (arch, mat, handle, accent) in HELD.items():
        out[f"item/3d/{item_id}"] = palette(mat, handle, accent)
    return out

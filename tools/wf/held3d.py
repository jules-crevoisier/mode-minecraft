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


def dane_axe():
    """Bearded Axe of the Frost Jarl: a long dark haft with a gold pommel and collars, and for a head a bearded
    crescent of blue ice with a glowing edge, an iron spike behind."""
    out = _shaft(-6, 26, 1.6, "handle") + _grip(2, 9, 2.2)
    out += [box(6.8, -7, 6.8, 9.2, -6, 9.2, "accent_dark"), box(6.6, 13, 6.6, 9.4, 14, 9.4, "brass"),
            box(6.6, 19, 6.6, 9.4, 20, 9.4, "brass"), box(7.1, 26, 7.1, 8.9, 27.5, 8.9, "accent")]
    out += [box(5, 20.5, 7.4, 7.2, 24.5, 8.6, "dark"),                         # the neck
            box(2, 18.5, 7.5, 5, 26.5, 8.5, "dark"),                           # the body
            box(-0.5, 16, 7.5, 2, 29, 8.5, "mid"),                             # the outer blade
            box(0, 29, 7.6, 1.5, 30.5, 8.4, "light"),                          # the upper horn
            box(0, 13, 7.6, 2.2, 16, 8.4, "mid"),                              # the beard's hook
            box(-1.6, 15, 7.6, -0.5, 29.5, 8.4, "glow"),                       # the frost edge
            box(3, 21, 7.3, 4, 24, 8.7, "accent"),                             # a rune in the ice
            box(9.2, 21, 7.5, 11.6, 23, 8.5, "iron_dark")]                     # back spike
    return out


def caldera_halberd():
    """Halberd of the Caldera: a long black haft banded with bronze, a leather grip, a bronze socket; an obsidian axe
    blade with a molten edge and a glowing crack, a long spear point and a back spike."""
    out = _shaft(-6, 22, 1.6, "handle") + _grip(3, 9, 2.2)
    out += [box(6.8, -7, 6.8, 9.2, -6, 9.2, "brass_dark"), box(7.1, 13, 7.1, 8.9, 14, 8.9, "brass"),
            box(6.6, 20.5, 6.6, 9.4, 23.5, 9.4, "brass"), box(6.9, 23.5, 6.9, 9.1, 24.5, 9.1, "brass_dark")]
    # the axe blade, widening outward (-x), its molten edge and a crack of magma through it
    out += [box(5.0, 18.5, 7.3, 7.2, 25.5, 8.7, "dark"), box(3.4, 17.5, 7.35, 5.0, 26.5, 8.65, "mid"),
            box(1.6, 16.0, 7.4, 3.4, 28.0, 8.6, "mid"), box(0.6, 15.2, 7.45, 1.6, 28.8, 8.55, "accent_dark"),
            box(2.6, 21.5, 7.25, 6.4, 22.3, 8.75, "accent_dark"), box(2.6, 17.8, 7.3, 3.4, 18.8, 8.7, "light"),
            box(2.6, 25.2, 7.3, 3.4, 26.2, 8.7, "light")]
    # the spear point and the back spike
    out += [box(7.2, 24.5, 7.4, 8.8, 30, 8.6, "mid"), box(7.6, 30, 7.6, 8.4, 32, 8.4, "light"),
            box(7.8, 25, 7.3, 8.2, 29.5, 8.7, "accent_dark"),
            box(9.2, 21.2, 7.5, 11.5, 22.6, 8.5, "dark"), box(11.5, 21.5, 7.6, 13, 22.3, 8.4, "light")]
    return out


def gate_key():
    """Key of the Kneeling Gate: the gate's great key wielded as a mace: a broad gold ring bow for a pommel with a
    soul-blue gem in it, a wrapped grip, a thick banded gold shaft set with glowing runes and a heavy toothed bit."""
    out = [box(4, -8, 7.2, 12, -6.4, 8.8, "light"), box(4, -1.6, 7.2, 12, 0, 8.8, "dark"),          # the bow ring
           box(3.4, -7, 7.2, 5, -0.6, 8.8, "mid"), box(11, -7, 7.2, 12.6, -0.6, 8.8, "mid"),
           box(7, -5, 7.5, 9, -2.6, 8.5, "accent"), box(7.5, -4.5, 7.3, 8.5, -3.1, 8.7, "glow")]
    out += [box(6.8, 0, 6.8, 9.2, 8, 9.2, "handle"), box(6.6, 8, 6.6, 9.4, 9.5, 9.4, "dark")]
    out += [box(6.6, 9.5, 6.6, 9.4, 29, 9.4, "mid")]                                            # the shaft
    for y in (14, 20, 26):
        out.append(box(6.3, y, 6.3, 9.7, y + 1.2, 9.7, "dark"))
    for y in (11.5, 16.5, 22.5):
        out.append(box(7.4, y, 6.4, 8.6, y + 1.6, 9.6, "glow"))
    out += [box(9.4, 19, 7, 14, 22, 9, "light"), box(9.4, 23, 7, 15, 26, 9, "mid"),                 # the bit's teeth
            box(9.4, 27, 7, 13, 29.5, 9, "light"), box(13, 22, 7, 14, 23, 9, "dark"),
            box(6.3, 29, 6.3, 9.7, 31.5, 9.7, "light")]
    return out


def tide_crozier():
    """Crozier of the Drowned Abbess: a long black driftwood staff banded in verdigris, a knop, and for a crook a
    nautilus spiral of teal shell curling over forward, a sea-glass lamp hanging in its curl."""
    import math
    out = _shaft(-6, 22, 1.6, "handle") + _grip(3, 9, 2.2)
    out += [box(6.8, -7, 6.8, 9.2, -6, 9.2, "brass_dark"), box(7.1, 13, 7.1, 8.9, 14, 8.9, "accent_dark"),
            box(6.6, 21, 6.6, 9.4, 23, 9.4, "brass"), box(6.9, 23, 6.9, 9.1, 24, 9.1, "brass_dark")]
    cx, cy = 4.6, 25.4                                                   # the spiral turns round this point
    for k in range(13):
        a = math.radians(-60 + 30 * k)
        r = 5.6 * math.exp(-0.07 * k)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        h = 0.95 if k < 5 else (0.75 if k < 9 else 0.55)
        out.append(box(x - h, y - h, 8 - h, x + h, y + h, 8 + h, "light" if k % 3 == 0 else "mid"))
    out += [box(4.3, 23.4, 7.7, 4.9, 25.6, 8.3, "brass_dark"),              # the lamp's chain
            box(3.7, 21.6, 7.1, 5.5, 23.4, 8.9, "glow")]                  # the sea-glass lamp
    return out



def valve_wrench():
    """Valve-Wrench of the Turbine Tyrant: a long riveted steel handle with a leather grip and an iron pommel, a
    brass collar with a glowing pressure gauge at the neck, and a heavy adjustable head: a fixed jaw and a sliding
    jaw held open by a brass worm screw, the hot glow of the turbine in the throat between them."""
    out = [box(7.1, -7, 7.1, 8.9, 21, 8.9, "steel"), box(6.8, -8.5, 6.8, 9.2, -6.5, 9.2, "iron_dark"),
           box(6.7, 2, 6.7, 9.3, 9, 9.3, "wrap")]
    for y in (-3, 12, 17):                                                  # rivets / bands down the handle
        out.append(box(6.9, y, 6.9, 9.1, y + 0.8, 9.1, "iron_dark"))
    out += [box(6.6, 19, 6.6, 9.4, 21, 9.4, "brass"),                      # the collar
            box(9.2, 19.4, 7.4, 10.6, 20.8, 8.6, "glow")]                  # the gauge
    out += [box(3.5, 21, 6.6, 12.5, 25, 9.4, "mid"),                       # the head
            box(3.5, 25, 6.6, 6.0, 31, 9.4, "light"),                      # fixed jaw
            box(10.0, 25, 6.6, 12.5, 29.5, 9.4, "mid"),                    # sliding jaw
            box(6.0, 25, 7.4, 10.0, 26, 8.6, "accent"),                    # the hot throat
            box(6.6, 22, 6.2, 9.4, 24, 6.6, "brass"), box(6.6, 22, 9.4, 9.4, 24, 9.8, "brass_dark"),   # worm screw
            box(3.2, 30, 6.8, 6.2, 31.4, 9.2, "outline")]
    return out


def lantern_crozier():
    """Lantern-Crozier of the Bog Hierophant: a tall staff of twisted black mangrove wood wrapped in moss, a knop of
    bone, a crook curling over forward and a caged lantern of swamp-fire hanging from its tip."""
    import math
    out = [box(7.2, -7, 7.2, 8.8, 22, 8.8, "handle"), box(6.9, -8, 6.9, 9.1, -6.5, 9.1, "iron_dark"),
           box(6.8, 3, 6.8, 9.2, 9, 9.2, "wrap")]
    for y, dx in ((-3, 0.35), (1, -0.35), (12, 0.35), (16, -0.35)):     # the twist of the wood
        out.append(box(7.0 + dx, y, 7.0, 9.0 + dx, y + 1.4, 9.0, "handle_dark"))
    out += [box(6.7, 13.5, 6.7, 9.3, 15.5, 9.3, "accent_dark"),            # moss grown round the staff
            box(6.5, 21, 6.5, 9.5, 23.5, 9.5, "cream"), box(6.8, 22, 6.8, 9.2, 22.6, 9.2, "brass_dark")]  # bone knop
    cx, cy, r = 4.4, 25.4, 3.8                                             # the crook curls over toward -x
    for k in range(9):
        a = math.radians(-12 + 24 * k)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        h = 0.95 if k < 5 else 0.8
        out.append(box(x - h, y - h, 8 - h, x + h, y + h, 8 + h, "handle" if k % 2 else "handle_dark"))
    lx = cx - r                                                          # under the crook's tip
    out += [box(lx - 0.25, 21.6, 7.75, lx + 0.25, 24.6, 8.25, "iron_dark"),        # the lantern's chain
            box(lx - 1.6, 20.8, 6.4, lx + 1.6, 21.6, 9.6, "iron_dark"),            # lid
            box(lx - 1.2, 17.0, 6.8, lx + 1.2, 20.8, 9.2, "glow"),                 # the swamp-fire
            box(lx - 1.3, 18.6, 6.7, lx + 1.3, 19.1, 9.3, "iron_dark"),            # a cage bar
            box(lx - 1.6, 16.2, 6.4, lx + 1.6, 17.0, 9.6, "iron_dark")]
    return out



def pressure_lance():
    """Pressure-Lance of the Lock-Master: an iron lance with a brass vamplate cone over the grip, a copper hose coiled
    down the shaft to a small pressure tank at the butt, a gauge by the grip, and for a point a brass nozzle glowing
    with the water behind it, a steel spike through it."""
    out = [box(7.1, -7, 7.1, 8.9, 24, 8.9, "iron_dark"), box(7.6, -6, 6.95, 8.4, 23, 7.1, "steel"),  # the shaft
           box(6.6, -9, 6.6, 9.4, -4.5, 9.4, "accent_dark"), box(6.9, -9.6, 6.9, 9.1, -9, 9.1, "brass_dark")]   # tank
    out += _grip(-3, 4, 2.2)
    out += [box(5.0, 4, 5.0, 11.0, 5, 11.0, "mid"), box(5.6, 5, 5.6, 10.4, 6.5, 10.4, "light"),       # vamplate
            box(6.2, 6.5, 6.2, 9.8, 8, 9.8, "mid"), box(6.8, 8, 6.8, 9.2, 9.5, 9.2, "dark")]
    out += [box(9.2, 1, 7.4, 10.4, 2.4, 8.6, "cream")]                    # the gauge
    for y in (11, 14, 17, 20):                                            # the coiled copper hose
        out.append(box(6.9, y, 6.9, 9.1, y + 1.1, 9.1, "brass" if y % 2 else "brass_dark"))
    out += [box(6.6, 23.5, 6.6, 9.4, 26.5, 9.4, "light"), box(6.9, 26.5, 6.9, 9.1, 27.2, 9.1, "glow"),  # nozzle
            box(7.5, 27.2, 7.5, 8.5, 31.5, 8.5, "steel"), box(7.7, 31.5, 7.7, 8.3, 32, 8.3, "cream")]
    return out


def architect_plumb():
    """Plumb of the Abyssal Architect: a mason's rule for a haft (dark wood, brass graduations, a wrapped grip), a
    long brass crossbar at its head like a gallows, and from its far end a short chain with a great lead plumb-bob
    capped in brass, a soul-blue plumb line glowing down its side."""
    out = _shaft(-6, 22, 1.8, "handle") + _grip(2, 9, 2.3)
    out += [box(6.8, -7, 6.8, 9.2, -6, 9.2, "brass_dark")]
    for y in (11, 13.5, 16, 18.5):                                         # brass graduations on the rule
        out.append(box(6.9, y, 6.9, 9.1, y + 0.6, 9.1, "brass"))
    out += [box(6.4, 22, 7.2, 16.5, 23.6, 8.8, "brass"),                   # the crossbar, out to one side
            box(16.0, 21.2, 7.4, 17.0, 23.8, 8.6, "brass_dark"),
            box(7.2, 23.6, 7.2, 8.8, 24.8, 8.8, "iron_dark"),
            box(8.6, 19.5, 7.6, 10.6, 22, 8.4, "brass_dark")]               # a brace under it
    for k, y in enumerate((22.0, 20.2, 18.4)):                             # the chain
        if k % 2 == 0:
            out.append(box(15.0, y - 1.8, 7.6, 16.2, y, 8.4, "steel"))
        else:
            out.append(box(15.3, y - 1.8, 7.2, 15.9, y, 8.8, "steel"))
    cx, top = 15.6, 16.6
    out += [box(cx - 1.8, top - 1.2, 6.2, cx + 1.8, top, 9.8, "brass"),                 # the cap
            box(cx - 3.0, top - 5.0, 5.0, cx + 3.0, top - 1.2, 11.0, "mid"),          # the lead body
            box(cx - 2.2, top - 7.4, 5.8, cx + 2.2, top - 5.0, 10.2, "dark"),
            box(cx - 1.2, top - 9.2, 6.8, cx + 1.2, top - 7.4, 9.2, "dark"),
            box(cx - 0.5, top - 10.6, 7.5, cx + 0.5, top - 9.2, 8.5, "brass"),         # the point
            box(cx - 3.2, top - 2.4, 4.8, cx + 3.2, top - 1.8, 11.2, "brass_dark"),    # a girdle
            box(cx - 0.35, top - 7.4, 4.8, cx + 0.35, top - 1.2, 5.0, "glow")]        # the plumb line
    return out


def ascetic_staff():
    """Staff of the Storm Ascetic: a long gnarled haft with a bronze ferrule, a string of prayer beads wound under the
    grip, and at the top an open bronze ring (a pilgrim's ringed staff) hung with four jangling rings and pierced by a
    spike of lightning."""
    import math
    out = [box(7.2, -7, 7.2, 8.8, 23, 8.8, "handle"), box(6.9, -8, 6.9, 9.1, -6.5, 9.1, "brass_dark"),
           box(6.8, 3, 6.8, 9.2, 9, 9.2, "wrap")]
    for y, dx in ((-2, 0.4), (6, -0.4), (14, 0.3), (19, -0.3)):            # knots in the wood
        out.append(box(7.0 + dx, y, 7.0, 9.0 + dx, y + 1.2, 9.0, "handle_dark"))
    for k in range(10):                                                    # a loop of prayer beads round the haft
        a = math.radians(k * 36)
        x, z, y = 8 + 1.6 * math.cos(a), 8 + 1.6 * math.sin(a), 11.5 - 1.6 * math.sin(a)
        out.append(box(x - 0.55, y - 0.55, z - 0.55, x + 0.55, y + 0.55, z + 0.55, "accent" if k == 7 else "cream"))
    out += [box(7.6, 8.4, 6.0, 8.4, 9.9, 6.8, "accent_dark")]             # the tassel under the guru bead
    out += [box(6.8, 23, 6.8, 9.2, 24.5, 9.2, "brass")]
    cx, cy, r = 8.0, 27.2, 3.9
    for a in range(0, 360, 30):
        x, y = cx + r * math.sin(math.radians(a)), cy + r * math.cos(math.radians(a))
        out.append(box(x - 0.7, y - 0.7, 7.4, x + 0.7, y + 0.7, 8.6, "brass" if a % 60 else "brass_dark"))
    for x, y in ((4.0, 25.4), (12.0, 25.4), (5.2, 23.6), (10.8, 23.6)):   # the jangling rings
        out.append(box(x - 0.5, y - 1.2, 7.6, x + 0.5, y + 0.2, 8.4, "steel"))
    out += [box(7.6, 24.5, 7.6, 8.4, 31.2, 8.4, "glow"),                  # the spike of lightning
            box(8.4, 28.4, 7.7, 9.4, 29.0, 8.3, "glow"), box(6.6, 26.0, 7.7, 7.6, 26.6, 8.3, "glow")]
    return out


def solar_staff():
    """Sun-Staff of the Solar Hierarch: a long gilded staff banded in brass with a wrapped grip and a gold butt-cap,
    a flared collar, and at its head an open sun-disc: a ring of gold set with twelve short rays round a glowing
    ember orb, a lapis-dark band behind the orb like the lens of the Sun-Engine."""
    import math
    out = [box(7.2, -7, 7.2, 8.8, 22, 8.8, "mid"), box(6.8, -8.5, 6.8, 9.2, -6.5, 9.2, "light"),
           box(6.8, 3, 6.8, 9.2, 9, 9.2, "wrap")]
    for y in (-3, 12, 16.5):                                               # brass bands down the staff
        out.append(box(6.9, y, 6.9, 9.1, y + 1.0, 9.1, "brass_dark"))
    out += [box(6.6, 20, 6.6, 9.4, 21.4, 9.4, "light"), box(6.2, 21.4, 6.2, 9.8, 22.6, 9.8, "brass")]  # the collar
    cx, cy, r = 8.0, 26.2, 3.8
    for a in range(0, 360, 30):                                            # the sun ring
        x, y = cx + r * math.sin(math.radians(a)), cy + r * math.cos(math.radians(a))
        out.append(box(x - 0.8, y - 0.8, 7.3, x + 0.8, y + 0.8, 8.7, "light" if a % 60 else "mid"))
    for a in range(15, 360, 30):                                           # twelve short rays
        if 150 < a < 210:
            continue                                                       # none down into the collar
        x, y = cx + 5.0 * math.sin(math.radians(a)), cy + 5.0 * math.cos(math.radians(a))
        out.append(box(x - 0.45, y - 0.45, 7.6, x + 0.45, y + 0.45, 8.4, "brass"))
    out += [box(5.8, 24.0, 7.6, 10.2, 28.4, 8.4, "accent_dark"),            # the dark lens behind the orb
            box(6.5, 24.7, 6.9, 9.5, 27.7, 9.1, "glow"),                   # the ember orb
            box(7.2, 22.6, 7.4, 8.8, 23.4, 8.6, "brass_dark")]
    return out


def admiral_cutlass():
    """Boarding Cutlass of the Drowned Admiral: a broad, slightly curved naval blade (a bright edge, a dark spine, a
    sea-green glow along the fuller), a brass basket hilt whose shell wraps the knuckles, a leather grip and a lion-head
    pommel, barnacles crusting the back of the blade."""
    out = _grip(2.5, 8.5, 2.2) + [box(6.6, 0.8, 6.6, 9.4, 2.5, 9.4, "brass"), box(7.1, 0, 7.1, 8.9, 0.8, 8.9, "brass_dark")]
    out += [box(4.6, 8.5, 6.2, 11.4, 10, 9.8, "brass"),                        # the guard plate
            box(4.6, 2.5, 5.6, 11.4, 8.5, 6.2, "brass_dark"),                  # the basket's shell over the knuckles
            box(4.6, 2.5, 6.2, 5.4, 8.5, 8.4, "brass"), box(10.6, 2.5, 6.2, 11.4, 8.5, 8.4, "brass"),
            box(7.4, 1.6, 5.6, 8.6, 2.5, 6.4, "brass"),                        # the knuckle bow joins the pommel
            box(5.6, 4.5, 5.4, 6.4, 6.5, 5.6, "accent"), box(9.6, 4.5, 5.4, 10.4, 6.5, 5.6, "accent")]  # verdigris
    x = 5.8
    for k in range(9):                                                        # the blade, curving toward +x
        y0 = 10 + k * 2.1
        w = 4.2 if k < 7 else (3.2 if k == 7 else 2.2)
        out += [box(x, y0, 7.3, x + w, y0 + 2.2, 8.7, "mid"),
                box(x - 0.4, y0, 7.55, x, y0 + 2.2, 8.45, "light"),            # the edge
                box(x + w, y0, 7.45, x + w + 0.3, y0 + 2.2, 8.55, "dark")]     # the spine
        if 1 <= k <= 6:
            out.append(box(x + w * 0.55, y0 + 0.2, 7.2, x + w * 0.75, y0 + 1.9, 8.8, "glow"))   # sea-glow fuller
        x += 0.1 * k
    out += [box(x - 0.2, 28.9, 7.6, x + 1.2, 30.2, 8.4, "light")]              # the clipped point
    for (bx, by) in ((9.6, 13), (10.4, 19.5), (10.9, 23)):                    # barnacles on the spine
        out.append(box(bx, by, 7.0, bx + 1.0, by + 1.0, 9.0, "cream"))
    return out


def queen_macuahuitl():
    """Jade Macuahuitl of the Strangler Queen: a haft of dark fig wood wound with living root and a wrapped grip, a
    gold sun-band at its throat, and a broad flat paddle of jade with a rounded tip, both edges set with a row of dark
    obsidian teeth, a glowing green vein running up its face and a moss tuft at the root."""
    out = [box(7.2, -6, 7.2, 8.8, 11, 8.8, "handle"), box(6.9, -7, 6.9, 9.1, -5.6, 9.1, "brass_dark")]
    out += _grip(-1, 6, 2.2)
    for y, dx in ((6.5, 0.35), (8.6, -0.35)):                             # roots wound round the haft
        out.append(box(6.9 + dx, y, 6.9, 9.1 + dx, y + 1.0, 9.1, "handle_dark"))
    out += [box(6.6, 10.4, 6.6, 9.4, 11.6, 9.4, "brass"),                  # the gold sun-band
            box(6.9, 11.0, 6.4, 9.1, 12.2, 6.6, "accent")]
    out += [box(5.6, 11.6, 7.3, 10.4, 25.0, 8.7, "mid"),                   # the jade paddle
            box(6.2, 25.0, 7.35, 9.8, 26.4, 8.65, "mid"), box(7.0, 26.4, 7.4, 9.0, 27.0, 8.6, "light"),
            box(6.0, 12.0, 7.2, 6.8, 24.6, 8.8, "light"),                  # a bevel along one edge
            box(9.4, 12.0, 7.2, 10.2, 24.6, 8.8, "dark"),                  # and the shade on the other
            box(7.7, 13.0, 7.15, 8.3, 23.5, 8.85, "glow"),                 # the living vein
            box(6.6, 11.6, 7.0, 9.4, 12.6, 9.0, "accent_dark")]            # moss at the root
    for y in (13.0, 15.4, 17.8, 20.2, 22.6):                              # obsidian teeth on both edges
        out += [box(4.5, y, 7.6, 5.6, y + 1.4, 8.4, "iron_dark"), box(10.4, y, 7.6, 11.5, y + 1.4, 8.4, "iron_dark")]
    return out


def scarab_sceptre():
    """Scarab Sceptre of the Fourth King: a long gilded sceptre with a dark wrapped grip, lapis bands and a gold
    butt-knob, a flared lotus collar, and at its head a lapis scarab with gilded wing-cases spread wide, its forelegs
    raising a glowing sun-disc above it; a broken notch in the disc's rim."""
    import math
    out = [box(7.25, -8, 7.25, 8.75, 18, 8.75, "mid"), box(6.8, -9.5, 6.8, 9.2, -7.5, 9.2, "light"),
           box(6.9, -2, 6.9, 9.1, 4.5, 9.1, "wrap")]
    for y in (-6.5, 6, 10, 14):                                            # lapis bands down the sceptre
        out.append(box(6.95, y, 6.95, 9.05, y + 1.0, 9.05, "accent_dark" if y < 0 else "accent"))
    out += [box(6.6, 17, 6.6, 9.4, 18.2, 9.4, "dark"),                    # the lotus collar
            box(6.0, 18.2, 6.0, 10.0, 19.4, 10.0, "light"),
            box(5.6, 19.4, 6.4, 6.6, 20.6, 9.6, "mid"), box(9.4, 19.4, 6.4, 10.4, 20.6, 9.6, "mid")]
    out += [box(6.4, 19.4, 6.4, 9.6, 23.4, 9.6, "accent_dark"),           # the scarab's body
            box(6.8, 23.4, 6.8, 9.2, 24.6, 9.2, "accent"),                 # its head
            box(7.6, 19.6, 6.2, 8.4, 23.2, 6.4, "glow")]                   # the gilt seam down its back
    for side in (-1, 1):                                                   # gilded wing-cases spread wide
        for k in range(4):
            x0 = 8 + side * (1.6 + k * 1.0)
            y0 = 20.0 + k * 1.1
            xa, xb = (x0, x0 + 1.4) if side > 0 else (x0 - 1.4, x0)
            out.append(box(xa, y0, 7.1, xb, y0 + 2.4 - k * 0.3, 8.9, "light" if k % 2 else "mid"))
        out.append(box(8 + side * 1.4 - 0.4, 24.4, 7.6, 8 + side * 1.4 + 0.4, 26.4, 8.4, "dark"))  # the forelegs
    cx, cy, r = 8.0, 28.4, 2.8
    for a in range(0, 360, 30):                                            # the sun-disc's gold rim
        if a == 60:
            continue                                                       # the notch the chisel left
        x, y = cx + r * math.sin(math.radians(a)), cy + r * math.cos(math.radians(a))
        out.append(box(x - 0.7, y - 0.7, 7.3, x + 0.7, y + 0.7, 8.7, "light" if a % 60 else "mid"))
    out += [box(6.1, 26.5, 7.5, 9.9, 30.3, 8.5, "glow"),                  # the glowing disc
            box(6.9, 27.3, 7.2, 9.1, 29.5, 8.8, "accent")]                 # its lapis eye
    return out


def warden_tongs():
    """Searing Tongs of the Anvil Warden: a smith's tongs as long as a sword, two dark iron reins bound in leather at
    the grip and spreading a little toward their ends, a brass rivet at the joint, long jaws heat-tinted toward their
    tips and a white-hot billet held between them."""
    out = []
    for k in range(8):                                                     # the reins, spreading toward the butt
        y0 = -6 + k * 2.0
        spread = 1.9 - k * 0.12
        out += [box(8 - spread - 0.6, y0, 7.4, 8 - spread + 0.6, y0 + 2.0, 8.6, "mid"),
                box(8 + spread - 0.6, y0, 7.4, 8 + spread + 0.6, y0 + 2.0, 8.6, "dark")]
    out += [box(6.0, 0, 7.1, 10.0, 5.5, 8.9, "wrap"),                      # the leather grip round both reins
            box(6.3, -7.2, 7.3, 7.6, -6, 8.7, "iron_dark"), box(8.4, -7.2, 7.3, 9.7, -6, 8.7, "iron_dark")]
    out += [box(6.4, 10, 6.6, 9.6, 12.4, 9.4, "brass"),                    # the rivet at the joint
            box(7.4, 10.6, 6.2, 8.6, 11.8, 6.6, "brass_dark")]
    for k in range(7):                                                     # the jaws, closing on the billet
        y0 = 12.4 + k * 2.0
        gap = 1.1 + (0.4 if k >= 5 else 0.0)
        key = "dark" if k < 4 else "accent_dark"
        out += [box(8 - gap - 0.9, y0, 7.45, 8 - gap, y0 + 2.0, 8.55, "light" if k < 4 else key),
                box(8 + gap, y0, 7.45, 8 + gap + 0.9, y0 + 2.0, 8.55, key)]
    out += [box(6.6, 22.4, 6.2, 9.4, 27.2, 9.8, "accent"),                 # the white-hot billet
            box(6.9, 23.0, 6.0, 9.1, 26.6, 10.0, "glow")]
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
              "broadsword": broadsword, "sentinel_greatsword": sentinel_greatsword, "crook": crook, "chain_flail": chain_flail, "gate_key": gate_key, "halo_glaive": halo_glaive, "caldera_halberd": caldera_halberd,
              "dane_axe": dane_axe, "tide_crozier": tide_crozier, "architect_plumb": architect_plumb, "pressure_lance": pressure_lance, "lantern_crozier": lantern_crozier, "ascetic_staff": ascetic_staff,
              "valve_wrench": valve_wrench, "admiral_cutlass": admiral_cutlass, "solar_staff": solar_staff,
              "trident_big": trident_big, "fang": fang, "grimoire": grimoire, "gauntlet": gauntlet,
              "horn_curved": horn_curved, "ward_orb": ward_orb}
ARCHETYPES["queen_macuahuitl"] = queen_macuahuitl
ARCHETYPES["warden_tongs"] = warden_tongs
ARCHETYPES["scarab_sceptre"] = scarab_sceptre


def heart_lodeblade():
    """Lodeblade of the Colossus's Heart: a broad greatsword of loose bronze plates held apart by a glowing amber
    tether (gaps between the plates show the light), a guard of bent copper pipe with valve-wheel ends, and a small
    brass engine-heart caged at the throat of the blade, its amber seam glowing; an iron rib for a grip and a gauge
    pommel."""
    out = _grip(1.5, 8.5, 2.2) + [box(6.4, -0.6, 6.6, 9.6, 1.5, 9.4, "brass"),              # the gauge pommel
                                   box(7.2, -0.2, 6.4, 8.8, 1.1, 6.6, "cream")]
    out += [box(2.5, 8.5, 7.0, 13.5, 9.8, 9.0, "accent_dark"),                             # copper-pipe guard
            box(1.4, 7.4, 6.8, 2.8, 10.6, 9.2, "brass_dark"), box(13.2, 7.4, 6.8, 14.6, 10.6, 9.2, "brass_dark")]
    out += [box(6.2, 9.8, 6.4, 9.8, 12.6, 9.6, "brass"),                                   # the caged heart
            box(7.4, 10.3, 6.2, 8.6, 12.2, 9.8, "glow"),
            box(5.8, 10.1, 7.2, 6.2, 12.4, 8.8, "iron_dark"), box(9.8, 10.1, 7.2, 10.2, 12.4, 8.8, "iron_dark")]
    out += [box(7.0, 12.6, 7.6, 9.0, 29.0, 8.4, "accent")]                                   # the amber tether
    y = 12.9
    for k, h in enumerate((2.4, 2.3, 2.2, 2.1, 2.0, 1.8)):                                 # loose plates, gaps between
        w = 6.0 - k * 0.3
        a0 = 8 - w / 2 + (0.2 if k % 2 else -0.2)                                       # each sits a little askew
        out += [box(a0, y, 7.45, a0 + w, y + h, 8.55, "mid"),
                box(a0 - 0.4, y + 0.3, 7.6, a0, y + h - 0.3, 8.4, "light"),               # the edge
                box(a0 + w, y + 0.3, 7.6, a0 + w + 0.4, y + h - 0.3, 8.4, "light"),
                box(a0 + 0.6, y + h - 0.5, 7.35, a0 + w - 0.6, y + h, 8.65, "dark")]      # the lip of the plate
        y += h + 0.6
    out += [box(6.6, y, 7.5, 9.4, y + 1.4, 8.5, "light"), box(7.4, y + 1.4, 7.6, 8.6, y + 2.4, 8.4, "light")]
    return out


ARCHETYPES["heart_lodeblade"] = heart_lodeblade

def curator_astrolabe():
    """Astrolabe of the Star-Eater Curator: a tall dark staff ringed with brass collars, a wrapped grip and a brass
    spike at its foot; at its head a brass astrolabe disc engraved with a glowing star map, held inside two crossed
    armillary hoops that circle a white star, and a chip of meteorite riding on the outer hoop."""
    import math
    out = [box(7.25, -10, 7.25, 8.75, 17.5, 8.75, "handle"), box(7.6, -12, 7.6, 8.4, -10, 8.4, "brass_dark")]
    out += _grip(-2, 5, 2.2)
    for y in (-8, 7, 11, 14.5):                                             # brass collars down the staff
        out.append(box(6.95, y, 6.95, 9.05, y + 0.8, 9.05, "brass"))
    out += [box(6.6, 16.9, 6.6, 9.4, 18.1, 9.4, "brass_dark")]            # the throne under the disc
    cx, cy, r = 8.0, 23.5, 5.0
    out += [box(4.6, 20.1, 7.6, 11.4, 26.9, 8.4, "brass_dark"),           # the mater
            box(5.4, 20.9, 7.5, 10.6, 26.1, 8.5, "accent_dark"),          # its engraved star map
            box(7.4, 22.9, 7.3, 8.6, 24.1, 8.7, "glow")]                  # the pin
    for a in range(0, 360, 45):                                           # the rete's glowing pointers
        x, y = cx + 2.0 * math.sin(math.radians(a)), cy + 2.0 * math.cos(math.radians(a))
        out.append(box(x - 0.3, y - 0.3, 7.4, x + 0.3, y + 0.3, 8.6, "accent"))
    for a in range(0, 360, 30):                                           # hoop one, in the disc's plane
        x, y = cx + r * math.sin(math.radians(a)), cy + r * math.cos(math.radians(a))
        out.append(box(x - 0.6, y - 0.6, 7.5, x + 0.6, y + 0.6, 8.5, "brass"))
    for a in range(0, 360, 30):                                           # hoop two, across it
        z, y = 8.0 + r * math.sin(math.radians(a)), cy + r * math.cos(math.radians(a))
        if abs(z - 8.0) < 1.0 and abs(y - cy) < 4.0:
            continue
        out.append(box(7.5, y - 0.6, z - 0.6, 8.5, y + 0.6, z + 0.6, "light"))
    out += [box(7.1, 29.0, 7.1, 8.9, 30.8, 8.9, "glow"),                  # the white star on top
            box(11.4, 26.8, 7.2, 13.0, 28.4, 8.8, "iron_dark")]           # the meteorite chip on the hoop
    return out


ARCHETYPES["curator_astrolabe"] = curator_astrolabe


def baron_drillpick():
    """Drill-Pick of the Mine Baron: a long mahogany haft bound in leather with an iron butt cap and brass collars,
    two sticks of dynamite strapped below the head with a lit fuse; the head is a riveted iron block with a gold pick
    spike tapering out on one side and a fluted steel drill cone banded in brass boring out on the other."""
    out = [box(7.2, -8, 7.2, 8.8, 18, 8.8, "handle"), box(6.9, -9.4, 6.9, 9.1, -8, 9.1, "iron_dark")]
    out += _grip(-3, 4, 2.3)
    for y in (5.0, 16.4):                                                   # brass collars
        out.append(box(6.8, y, 6.8, 9.2, y + 0.9, 9.2, "brass"))
    out += [box(8.8, 10.5, 7.0, 10.4, 15.5, 8.6, "accent"),                # two sticks of dynamite on the haft
            box(8.8, 10.5, 8.6, 10.4, 15.0, 10.2, "accent_dark"),
            box(8.6, 12.4, 6.8, 10.6, 13.2, 10.4, "wrap"),                  # their strap
            box(9.4, 15.5, 7.6, 9.8, 16.6, 8.0, "ink"), box(9.3, 16.6, 7.5, 9.9, 17.2, 8.1, "glow")]  # the lit fuse
    out += [box(5.6, 17.6, 6.0, 10.4, 22.4, 10.0, "iron_dark"),            # the riveted head block
            box(5.3, 18.2, 6.6, 5.6, 21.8, 9.4, "brass_dark"), box(10.4, 18.2, 6.6, 10.7, 21.8, 9.4, "brass_dark")]
    for x, y in ((6.4, 21.8), (9.6, 21.8), (6.4, 17.8), (9.6, 17.8)):
        out.append(box(x - 0.4, y, 5.8, x + 0.4, y + 0.6, 6.0, "brass"))
    for k, (w, h) in enumerate(((3.6, 3.6), (3.0, 3.0), (2.4, 2.4), (1.8, 1.8), (1.2, 1.2), (0.7, 0.7))):
        x1 = 5.3 - k * 1.2                                                  # the gold pick spike, tapering out
        out.append(box(x1 - 1.2, 20.0 - h / 2 + k * 0.25, 8 - w / 2, x1, 20.0 + h / 2 + k * 0.25, 8 + w / 2,
                       "light" if k % 2 else "mid"))
    for k in range(7):                                                      # the drill cone, fluted and banded
        w = 4.0 - k * 0.55
        x0 = 10.7 + k * 1.0
        out.append(box(x0, 20.0 - w / 2, 8 - w / 2, x0 + 1.0, 20.0 + w / 2, 8 + w / 2,
                       "brass" if k == 0 else ("steel" if k % 2 == 0 else "outline")))
    out.append(box(17.7, 19.7, 7.7, 18.5, 20.3, 8.3, "steel"))              # the drill point
    return out


ARCHETYPES["baron_drillpick"] = baron_drillpick


def abbot_dragonstaff():
    """Dragon Staff of the Chime Abbot: a tall staff of dark lacquered wood banded in bronze, a wrapped grip and a
    bronze foot; at its head a bronze dragon looking out to one side, a gold mane crest, horns swept back, glowing
    eyes, and a ring of three chime rods hanging from its jaws."""
    out = [box(7.25, -10, 7.25, 8.75, 18, 8.75, "handle"), box(6.9, -11.6, 6.9, 9.1, -10, 9.1, "dark")]
    out += _grip(-3, 4, 2.2)
    for y in (-7, 6, 10.5, 14.5):                                           # bronze bands
        out.append(box(6.9, y, 6.9, 9.1, y + 0.8, 9.1, "mid"))
    out += [box(6.6, 17.6, 6.6, 9.4, 19.4, 9.4, "dark"),                   # the collar under the head
            box(5.4, 19.2, 6.2, 10.6, 23.8, 9.8, "mid"),                    # the skull
            box(10.6, 19.6, 6.6, 15.0, 22.6, 9.4, "mid"),                   # the snout
            box(14.6, 21.6, 7.0, 15.6, 22.6, 9.0, "light"),                 # the nostril ridge
            box(10.6, 18.4, 6.8, 14.4, 19.4, 9.2, "dark"),                  # the lower jaw, open a little
            box(11.0, 19.4, 6.8, 11.6, 20.0, 7.2, "cream"), box(11.0, 19.4, 8.8, 11.6, 20.0, 9.2, "cream"),
            box(5.8, 23.8, 7.4, 10.2, 24.6, 8.6, "brass"),                  # the gold mane crest
            box(9.4, 22.0, 6.0, 10.4, 23.0, 6.2, "glow"), box(9.4, 22.0, 9.8, 10.4, 23.0, 10.0, "glow")]   # eyes
    for k in range(4):                                                      # the horns, swept back and up
        out += [box(5.4 - k * 0.9, 23.4 + k * 0.9, 6.4, 6.4 - k * 0.9, 24.4 + k * 0.9, 7.2, "brass"),
                box(5.4 - k * 0.9, 23.4 + k * 0.9, 8.8, 6.4 - k * 0.9, 24.4 + k * 0.9, 9.6, "brass")]
    for k in range(3):                                                      # whiskers trailing down
        out += [box(13.4 - k * 0.6, 19.6 - k * 1.0, 6.0, 14.0 - k * 0.6, 20.6 - k * 1.0, 6.6, "light")]
    out += [box(11.4, 17.0, 7.6, 14.6, 17.6, 8.4, "brass")]                 # the ring of chimes in its jaws
    for x, h in ((11.6, 3.2), (12.8, 4.0), (14.0, 3.2)):
        out += [box(x, 17.0 - h, 7.7, x + 0.6, 17.0, 8.3, "light"), box(x, 17.0 - h, 7.65, x + 0.6, 16.4 - h, 8.35, "accent")]
    return out


ARCHETYPES["abbot_dragonstaff"] = abbot_dragonstaff


def corsair_harpoon():
    """Harpoon Gun of the Corsair Captain: a mahogany pistol grip and short stock, a long dark-iron barrel ringed in
    brass, a copper drum magazine over the trigger, a red flare canister slung under the barrel with a glowing cap, and
    a barbed steel harpoon standing out of the muzzle with a coil of line."""
    out = [box(7.2, -6, 7.0, 8.8, 2, 9.0, "handle"), box(7.0, -7, 6.8, 9.0, -6, 9.2, "brass_dark")]
    out += _grip(-5, 0, 2.2)
    out += [box(6.6, 2, 6.6, 9.4, 4.5, 9.4, "brass_dark"),                   # the trigger block
            box(5.6, 3.5, 5.6, 10.4, 8.5, 10.4, "accent_dark"),               # the drum magazine
            box(5.4, 4.5, 7.4, 10.6, 7.5, 8.6, "brass")]
    out += [box(7.0, 4.5, 7.0, 9.0, 24, 9.0, "iron_dark")]                  # the barrel
    for y in (9.0, 14.0, 19.0, 23.0):
        out.append(box(6.7, y, 6.7, 9.3, y + 0.9, 9.3, "brass"))
    out += [box(7.3, 9.5, 9.0, 8.7, 17.5, 10.4, "accent"),                  # the flare canister
            box(7.3, 17.5, 9.0, 8.7, 18.3, 10.4, "glow")]
    out += [box(7.6, 24, 7.6, 8.4, 28.5, 8.4, "steel"),                      # the harpoon shaft
            box(6.6, 28.5, 7.4, 9.4, 29.5, 8.6, "steel"),                    # the barbs
            box(7.1, 29.5, 7.4, 8.9, 30.5, 8.6, "light"), box(7.6, 30.5, 7.6, 8.4, 31.5, 8.4, "light")]
    out += [box(9.0, 12.0, 6.6, 10.2, 15.0, 9.4, "wrap")]                   # a coil of line
    return out


ARCHETYPES["corsair_harpoon"] = corsair_harpoon


def cantor_baton():
    """Tuning-Fork Baton of the Hollow Cantor: a long black-lacquered baton ringed with brass collars, a wrapped grip
    and a little brass bell for a pommel; at its head a brass yoke holding an amethyst resonator, and two long steel
    tines rising from it, a pale glint near their tips."""
    out = [box(7.4, -8, 7.4, 8.6, 19, 8.6, "handle"), box(7.0, -10.5, 7.0, 9.0, -8.5, 9.0, "brass"),
           box(7.3, -11.2, 7.3, 8.7, -10.5, 8.7, "brass_dark")]
    out += _grip(-3, 4, 2.0)
    for y in (6.0, 11.0, 16.0):                                             # brass collars
        out.append(box(7.0, y, 7.0, 9.0, y + 0.7, 9.0, "brass"))
    out += [box(4.6, 19.0, 7.2, 11.4, 20.6, 8.8, "brass"),                 # the yoke
            box(5.0, 18.4, 7.4, 11.0, 19.0, 8.6, "brass_dark"),
            box(7.0, 19.2, 6.6, 9.0, 21.2, 9.4, "accent"),                  # the amethyst resonator
            box(7.4, 21.2, 7.0, 8.6, 21.6, 9.0, "accent_dark")]
    for x in (4.6, 10.2):                                                   # the two tines
        out += [box(x, 20.6, 7.4, x + 1.2, 31.5, 8.6, "steel"),
                box(x, 28.5, 7.3, x + 1.2, 29.3, 8.7, "glow")]
    return out


ARCHETYPES["cantor_baton"] = cantor_baton


def stoker_shovel():
    """Soul-Fire Shovel of the Stoker: a long dark haft bound in iron, a leather-wrapped grip and a brass D-grip knob at
    the butt, an iron socket, and a wide black-iron scoop with turned-up sides, heaped with glowing soul embers."""
    out = [box(7.25, -10, 7.25, 8.75, 19, 8.75, "handle"), box(6.6, -12.4, 6.6, 9.4, -10.4, 9.4, "brass"),
           box(7.1, -10.6, 7.1, 8.9, -10.0, 8.9, "brass_dark")]
    out += _grip(-4, 3, 2.2)
    for y in (6.0, 11.0, 16.0):                                             # iron bands
        out.append(box(6.9, y, 6.9, 9.1, y + 0.8, 9.1, "iron_dark"))
    out += [box(6.6, 18.6, 6.6, 9.4, 21.0, 9.4, "iron_dark"),              # the socket
            box(3.0, 21.0, 8.4, 13.0, 31.0, 9.4, "iron_dark"),              # the scoop's back
            box(2.4, 21.0, 6.4, 3.4, 30.0, 9.4, "outline"),                 # its turned-up sides
            box(12.6, 21.0, 6.4, 13.6, 30.0, 9.4, "outline"),
            box(3.0, 30.4, 8.2, 13.0, 31.4, 9.4, "dark"),                  # the worn cutting edge
            box(3.4, 22.0, 6.8, 12.6, 27.0, 8.4, "accent_dark"),            # the heap of embers
            box(4.4, 23.0, 6.4, 11.6, 26.0, 7.0, "accent"),
            box(6.0, 24.0, 6.1, 7.4, 25.4, 6.5, "glow"), box(9.0, 23.2, 6.1, 10.2, 24.4, 6.5, "glow")]
    return out


ARCHETYPES["stoker_shovel"] = stoker_shovel


def director_bonesaw():
    """Bone-Saw of the Asylum Director: a mahogany pistol handle with a brass guard, a long steel blade toothed along its
    front edge and stiffened by a dark-iron spine, a brass cap at the tip; a brass pocket watch (cream face, an aether
    glint) hangs from the guard on a short chain."""
    out = [box(7.2, -6, 7.2, 8.8, 6, 8.8, "handle"), box(6.8, -7.4, 6.8, 9.2, -6, 9.2, "brass"),
           box(6.4, 6, 6.6, 12.6, 7.6, 9.4, "brass"), box(6.4, 5.6, 6.6, 7.2, 6, 9.4, "brass_dark")]
    out += _grip(-4, 4, 1.9)
    out += [box(7.0, 7.6, 7.3, 8.2, 27.0, 8.7, "iron_dark"),                # the spine
            box(8.2, 7.6, 7.6, 12.0, 26.0, 8.4, "steel"),                   # the blade
            box(8.2, 7.6, 7.55, 9.0, 26.0, 8.45, "light"),
            box(6.8, 26.4, 7.1, 9.0, 27.8, 8.9, "brass")]                   # the tip cap
    for y in range(8, 26, 2):                                               # the teeth
        out.append(box(12.0, y, 7.7, 12.8, y + 1, 8.3, "mid"))
    for y in (4.6, 3.6):                                                    # the watch's chain
        out.append(box(6.0, y, 7.75, 6.5, y + 0.8, 8.25, "brass_dark"))
    out += [box(4.0, 0.4, 7.4, 7.6, 3.6, 8.6, "brass"),                     # the pocket watch
            box(4.4, 0.8, 7.2, 7.2, 3.2, 7.4, "cream"),
            box(5.5, 1.8, 7.0, 6.1, 2.4, 7.2, "glow")]
    return out


ARCHETYPES["director_bonesaw"] = director_bonesaw

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
    "gatekeeper_key": ("gate_key", "gold", "wood", "aether"),
    "caldera_halberd": ("caldera_halberd", "obsidian", "dark", "ember"),
    "jarl_axe": ("dane_axe", "frost", "dark", "ice"),
    "ascetic_staff": ("ascetic_staff", "storm", "wood", "sapphire"),
    "abbess_crozier": ("tide_crozier", "warden", "dark", "aether"),
    "architect_plumb": ("architect_plumb", "iron", "dark", "aether"),
    "pressure_lance": ("pressure_lance", "brass", "dark", "aether"),
    "hierophant_crozier": ("lantern_crozier", "leather", "dark", "emerald"),
    "queen_macuahuitl": ("queen_macuahuitl", "lithite", "dark", "emerald"),
    "hierarch_sunstaff": ("solar_staff", "gold", "gold", "ember"),
    "admiral_cutlass": ("admiral_cutlass", "iron", "dark", "aether"),
    "tyrant_wrench": ("valve_wrench", "iron", "dark", "ember"),
    "warden_tongs": ("warden_tongs", "iron", "dark", "ember"),
    "fourth_king_sceptre": ("scarab_sceptre", "gold", "dark", "sapphire"),
    "heart_lodeblade": ("heart_lodeblade", "copper", "dark", "ember"),
    "curator_astrolabe": ("curator_astrolabe", "void", "purpur", "amethyst"),
    "baron_drillpick": ("baron_drillpick", "gold", "dark", "ember"),
    "abbot_dragonstaff": ("abbot_dragonstaff", "copper", "dark", "ruby"),
    "corsair_harpoon": ("corsair_harpoon", "brass", "dark", "ember"),
    "cantor_baton": ("cantor_baton", "brass", "dark", "amethyst"),
    "stoker_shovel": ("stoker_shovel", "iron", "dark", "aether"),
    "director_bonesaw": ("director_bonesaw", "iron", "dark", "aether"),
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


# the relic weapons of the colossal structures (wf/relics.py, archetypes in wf/relicart.py)
from . import relicart as _relicart  # noqa: E402
_relicart.register_held(ARCHETYPES, HELD)

# the vault weapons of the colossal structures (wf/colossal_gear.py, archetypes in wf/colossal_art.py)
from . import colossal_art as _colossal_art  # noqa: E402
_colossal_art.register_held(ARCHETYPES, HELD)

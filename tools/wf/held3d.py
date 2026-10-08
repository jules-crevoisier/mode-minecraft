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


def sword(length=20, width=3.0, guard=7):
    a = 8 - width / 2
    out = _grip(3, 8) + [box(7, 1.5, 7, 9, 3, 9, "accent")]  # pommel
    out += [box(8 - guard / 2, 8, 6.5, 8 + guard / 2, 9.5, 9.5, "accent_dark"), box(7, 8.5, 6, 9, 9, 10, "accent")]
    out += [box(a, 9.5, 7.25, a + width, 9.5 + length, 8.75, "mid"),
            box(7.5, 9.5, 7, 8.5, 9.5 + length, 9, "light"),
            box(a + 0.5, 9.5 + length, 7.4, a + width - 0.5, 11 + length, 8.6, "light")]
    return out


def greatsword():
    return sword(length=21, width=4.0, guard=9)  # the blade tip must stay under y 32 (model bounds)


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


ARCHETYPES = {"sword": sword, "greatsword": greatsword, "blade": blade, "spear": spear,
              "trident": lambda: spear("trident"), "lance": lambda: spear("lance"), "hammer": hammer,
              "mace": mace, "staff": staff, "cane": cane, "scythe": scythe, "book": book, "fist": fist,
              "horn": horn, "wand": wand, "orb": orb, "chisel": chisel,
              "staff_flame": lambda: staff(head="flame"), "staff_snow": lambda: staff(head="snow"),
              "staff_bolt": lambda: staff(head="bolt"), "staff_cross": lambda: staff(head="cross"),
              "staff_sun": lambda: staff(head="sun"), "staff_root": lambda: staff(head="root"),
              "pendulum": pendulum, "anchor": anchor, "ladle": ladle, "flail": flail, "bell_hammer": bell_hammer,
              "forge_hammer": forge_hammer, "crystal_spear": crystal_spear, "axe": axe, "pickaxe": pickaxe,
              "shovel": shovel, "hoe": hoe, "wand_block": wand_block, "caged_orb": caged_orb}

# item id -> (archetype, material, handle, accent)
HELD = {
    "kings_trident": ("trident", "warden", "bone", "sapphire"),
    "bell_hammer": ("bell_hammer", "gold", "dark", "gold"),
    "forbidden_grimoire": ("book", "map", "dark", "amethyst"),
    "pharaoh_flail": ("flail", "gold", "gold", "sapphire"),
    "jade_fang": ("blade", "lithite", "gold", "emerald"),
    "rootmother_staff": ("staff_root", "leather", "wood", "emerald"),
    "crone_ladle": ("ladle", "iron", "dark", "amethyst"),
    "gryphon_lance": ("lance", "iron", "gold", "sapphire"),
    "rune_fist": ("fist", "lithite", "dark", "sapphire"),
    "forge_king_hammer": ("forge_hammer", "ember", "dark", "gold"),
    "crystal_fang": ("crystal_spear", "void", "bone", "amethyst"),
    "sculk_horn": ("horn", "warden", "bone", "sapphire"),
    "ash_greatsword": ("greatsword", "ember", "dark", "ember"),
    "golden_mace": ("mace", "gold", "gold", "ruby"),
    "soul_scythe": ("scythe", "void", "bone", "ice"),
    "void_greatblade": ("greatsword", "void", "purpur", "amethyst"),
    "clockmaker_pendulum": ("pendulum", "brass", "dark", "aether"),
    "helmsman_anchor": ("anchor", "iron", "dark", "ember"),
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
    "ward_orb": ("caged_orb", "void", "gold", "amethyst"),
    "chisel": ("chisel", "iron", "wood", "gold"),
    "excavator_pickaxe": ("pickaxe", "lithite", "wood", "emerald"),
    "lumber_axe": ("axe", "iron", "wood", "gold"),
}
# metal tools (wf/metals.py): brass on oak, mithril on dark wood
for _mid, _handle in (("brass", "wood"), ("mithril", "dark")):
    for _kind in ("sword", "pickaxe", "axe", "shovel", "hoe"):
        HELD[f"{_mid}_{_kind}"] = (_kind, _mid, _handle, "gold" if _mid == "brass" else "sapphire")

DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 0.5], "scale": [0.8, 0.8, 0.8]},
    "firstperson_righthand": {"rotation": [0, -90, 20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "firstperson_lefthand": {"rotation": [0, 90, -20], "translation": [1.13, 2.2, 0.8], "scale": [0.62, 0.62, 0.62]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
}


def model(item_id):
    arch, *_ = HELD[item_id]
    tex = f"brasshaven:item/3d/{item_id}"
    elements = []
    for x0, y0, z0, x1, y1, z1, key in ARCHETYPES[arch]():
        uv = _cell_uv(key)
        elements.append({"from": [x0, y0, z0], "to": [x1, y1, z1],
                         "faces": {f: {"uv": uv, "texture": "#t"} for f in ("north", "south", "east", "west", "up", "down")}})
    return {"textures": {"t": tex, "particle": tex}, "elements": elements, "display": DISPLAY}


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

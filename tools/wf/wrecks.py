"""Small steampunk wrecks scattered by the world overhaul (template features) in the Rustlands and the
Cogwork Valley: a half-buried giant cog, a burst pipe with its valve, an overturned boiler, a chimney stump and
the remains of an automaton. Saved as data/wayfarers/structure/wrecks/*.nbt (mod data, always loaded).
y = 0 is one block below the ground surface, so every wreck sits partly buried.
"""
import math
import os

from .blueprint import Blueprint

W = "wayfarers:"
BRASS, COPPER, VERD, IRON = W + "brass_plating", W + "copper_plating", W + "verdigris_plating", W + "dark_iron_plating"
GEAR, SMOKE = W + "gear_panel", W + "smokestack_bricks"


def cog(bp):
    r = 5
    for x in range(-r - 1, r + 2):
        for y in range(-r - 1, r + 2):
            d = math.hypot(x, y)
            a = math.atan2(y, x)
            tooth = math.cos(a * 10) > 0.3
            if d <= r - 0.5 or (d <= r + 1.0 and tooth):
                if d < 1.2:
                    bp.set(x, y + 2, 0, IRON)
                elif d < r * 0.45:
                    bp.set(x, y + 2, 0, GEAR)
                else:
                    bp.set(x, y + 2, 0, VERD if (x * 3 + y) % 5 == 0 else BRASS)
    # keep only what is above the buried line
    for (x, y, z) in list(bp.blocks):
        if y < 0:
            bp.remove(x, y, z)


def pipe(bp):
    for x in range(-4, 5):
        if x == 1:
            continue
        bp.set(x, 1, 0, W + "copper_pipe[axis=x]")
    bp.set(-5, 1, 0, COPPER)
    bp.set(-5, 2, 0, W + "valve_wheel[facing=west]")
    bp.set(5, 0, 0, COPPER)
    bp.set(5, 1, 0, W + "copper_pipe[axis=y]")
    bp.set(5, 2, 0, W + "copper_pipe[axis=y]")
    bp.set(2, 1, 1, "cobweb")


def boiler(bp):
    for z in range(-3, 4):
        for x in range(-2, 3):
            for y in range(0, 5):
                d = math.hypot(x, y - 2)
                if 1.2 < d <= 2.4:
                    bp.set(x, y, z, VERD if (x + z) % 3 == 0 else COPPER)
                elif d <= 1.2:
                    bp.set(x, y, z, "air")
    for x in range(-2, 3):
        for y in range(0, 5):
            if math.hypot(x, y - 2) <= 2.4:
                bp.set(x, y, -4, BRASS)
    bp.set(0, 2, -5, W + "pressure_gauge")
    bp.set(0, 2, 4, "air")
    bp.set(1, 1, 2, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def stump(bp):
    for y in range(0, 6):
        for x in range(-2, 3):
            for z in range(-2, 3):
                d = math.hypot(x, z)
                if 1.0 < d <= 2.3 and not (y > 3 and (x + z + y) % 3 == 0):
                    bp.set(x, y, z, BRASS if y == 2 else SMOKE)
                elif d <= 1.0:
                    bp.set(x, y, z, "air")
    bp.set(0, 1, 0, "hay_block[axis=y]")
    bp.set(0, 2, 0, "campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")


def automaton(bp):
    # torso lying on its back, an arm, the head with a lit eye
    for x in range(-1, 2):
        for z in range(-2, 3):
            bp.set(x, 1, z, IRON if (x + z) % 2 else BRASS)
    bp.set(0, 2, 0, GEAR)
    bp.set(0, 1, 3, BRASS)
    bp.set(0, 1, 4, W + "edison_lamp")
    for z in range(-1, 3):
        bp.set(3, 1, z, W + "copper_pipe[axis=z]")
    bp.set(-3, 1, -3, IRON)
    bp.set(-3, 2, -3, W + "wall_cog[facing=north]")


WRECKS = {"cog": cog, "pipe": pipe, "boiler": boiler, "stump": stump, "automaton": automaton}


def write(root):
    out = os.path.join(root, "src", "main", "resources", "data", "wayfarers", "structure", "wrecks")
    os.makedirs(out, exist_ok=True)
    for name, fn in WRECKS.items():
        bp = Blueprint(f"wrecks/{name}")
        fn(bp)
        bp.save(os.path.join(out, f"{name}.nbt"))
    return list(WRECKS)

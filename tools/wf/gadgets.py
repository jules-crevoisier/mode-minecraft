"""Steam gadgets (Lot 4): Brass Wrench, Grappling Hook, Brass Glider, Rivet Gun (+ Rivets), Pocket Watch and Airship
Compass. One table drives names, tooltips, sprites, 3D in-hand models, animated item models, recipes and manual
pages, like metals.py and machines.py. Java behaviour lives in com.wayfarers.item.* (one class per gadget).

Sprites are painted from simple shapes (circles, segments, boxes) on a 16x16 material grid, then shaded and outlined
automatically, so every gadget has the same light (top-left) and the steampunk palette of STYLE_STEAMPUNK.md.
"""
import math

from .png import Canvas

NS = "wayfarers"

# id -> (english, french, [tooltip lines en], [tooltip lines fr])
GADGETS = {
    "brass_wrench": ("Brass Wrench", "Clé à molette en laiton",
                     ["Use on a block: turn it (stairs, logs, chests, machines...).",
                      "Sneak-use on a Wayfarers machine: change its setting.",
                      "Sneak-use on Wayfarers decoration or furniture: pick it up."],
                     ["Clic droit sur un bloc : le tourne (escaliers, bûches, coffres...).",
                      "Accroupi sur une machine Wayfarers : change son réglage.",
                      "Accroupi sur un bloc déco ou un meuble Wayfarers : le ramasse."]),
    "grappling_hook": ("Grappling Hook", "Grappin",
                       ["Use: fire the claw (32 blocks); it reels you in.",
                        "Sneak or use again: let go.",
                        "No fall damage while reeled in."],
                       ["Clic droit : lance la griffe (32 blocs) qui te tire à elle.",
                        "Accroupi ou clic droit à nouveau : lâcher.",
                        "Aucun dégât de chute pendant la traction."]),
    "brass_glider": ("Brass Glider", "Planeur en laiton",
                     ["Hold it while falling: it opens, you sink slowly",
                      "and glide where you look. No fall damage."],
                     ["Tiens-le en main pendant une chute : il s'ouvre,",
                      "tu planes là où tu regardes. Aucun dégât de chute."]),
    "rivet_gun": ("Rivet Gun", "Pistolet à rivets",
                  ["Use: fire a hot rivet (5 damage).",
                   "Ammo: Rivets, or iron nuggets."],
                  ["Clic droit : tire un rivet brûlant (5 dégâts).",
                   "Munitions : rivets, ou pépites de fer."]),
    "rivet": ("Rivets", "Rivets",
              ["Ammunition for the Rivet Gun."],
              ["Munitions du pistolet à rivets."]),
    "pocket_watch": ("Pocket Watch", "Montre à gousset",
                     ["Its hand follows the sun.",
                      "Use: time, day, moon phase and biome."],
                     ["Son aiguille suit le soleil.",
                      "Clic droit : heure, jour, phase de lune et biome."]),
    "airship_compass": ("Airship Compass", "Boussole de dirigeable",
                        ["Use: find the nearest Sky Harbour.",
                         "In the End: the Void Ship Wreck.",
                         "Its needle then keeps pointing there."],
                        ["Clic droit : trouve le Port céleste le plus proche.",
                         "Dans l'End : l'Épave du vide.",
                         "Son aiguille pointe ensuite vers lui."]),
}

# entity names (merged into content.ENTITIES)
ENTITIES = {"grappling_hook": ("Grappling Claw", "Griffe de grappin"), "rivet": ("Rivet", "Rivet")}

MESSAGES = {
    "message.wayfarers.wrench.cannot": ("Nothing to turn on this block.", "Rien à tourner sur ce bloc."),
    "message.wayfarers.wrench.protected": ("You can't change blocks here.", "Tu ne peux pas modifier les blocs ici."),
    "message.wayfarers.rivet_gun.empty": ("Out of rivets (Rivets or iron nuggets).", "Plus de rivets (rivets ou pépites de fer)."),
    "message.wayfarers.watch": ("%s - day %s - %s - %s", "%s - jour %s - %s - %s"),
    "message.wayfarers.watch.moon.full_moon": ("full moon", "pleine lune"),
    "message.wayfarers.watch.moon.waning_gibbous": ("waning gibbous", "gibbeuse décroissante"),
    "message.wayfarers.watch.moon.third_quarter": ("last quarter", "dernier quartier"),
    "message.wayfarers.watch.moon.waning_crescent": ("waning crescent", "dernier croissant"),
    "message.wayfarers.watch.moon.new_moon": ("new moon", "nouvelle lune"),
    "message.wayfarers.watch.moon.waxing_crescent": ("waxing crescent", "premier croissant"),
    "message.wayfarers.watch.moon.first_quarter": ("first quarter", "premier quartier"),
    "message.wayfarers.watch.moon.waxing_gibbous": ("waxing gibbous", "gibbeuse croissante"),
}


def register_content(items):
    """Adds the gadgets to content.ITEMS (first tooltip line; the others are written by lang())."""
    for gid, (en, fr, ten, tfr) in GADGETS.items():
        items[gid] = (en, fr, ten[0], tfr[0])


def lang():
    en, fr = {}, {}
    for gid, (_en, _fr, ten, tfr) in GADGETS.items():
        for i in range(1, len(ten)):
            en[f"item.{NS}.{gid}.desc{i + 1}"], fr[f"item.{NS}.{gid}.desc{i + 1}"] = ten[i], tfr[i]
    for key, (e, f) in MESSAGES.items():
        en[key], fr[key] = e, f
    return en, fr


# ------------------------------------------------------------------ recipes (gen_data.py)
def recipes(shaped, shapeless):
    shaped("brass_wrench", ["B B", " B ", " I "], {"B": "brass_ingot", "I": "iron_ingot"}, category="equipment")
    shaped("grappling_hook", ["  T", " C ", "BB "], {"T": "tripwire_hook", "C": "iron_chain", "B": "brass_ingot"},
           category="equipment")
    shaped("brass_glider", ["BBB", "LML", "L L"], {"B": "brass_ingot", "L": "leather", "M": "phantom_membrane"},
           category="equipment")
    shaped("rivet_gun", ["BBB", "CP ", "W  "], {"B": "brass_ingot", "C": "copper_ingot", "P": "piston", "W": "#planks"},
           category="equipment")
    shapeless("rivet", ["iron_ingot", "copper_ingot", "zinc_nugget"], count=12, category="equipment")
    shaped("pocket_watch", [" N ", "BRB", " B "], {"N": "brass_nugget", "B": "brass_ingot", "R": "redstone"},
           category="equipment")
    shaped("airship_compass", [" A ", "BCB", " B "], {"A": "aether_crystal", "B": "brass_ingot", "C": "compass"},
           category="equipment")


MOD_ITEMS = set(GADGETS) | {"brass_ingot", "brass_nugget", "zinc_nugget", "aether_crystal"}


def tags(write):
    write(f"{NS}/tags/item/gadget_repair_materials.json", {"values": [f"{NS}:brass_ingot"]})


# ------------------------------------------------------------------ manual (guide.py)
PAGES = [
    ("wrench", "wayfarers:brass_wrench", ("Brass Wrench", "Clé à molette en laiton"), [
        ("Right-click a block to turn it: stairs, logs, chests, hoppers, signs, machines, furniture. Sneak: the other "
         "way. Doors, beds and double chests stay put.",
         "Clic droit sur un bloc pour le tourner : escaliers, bûches, coffres, entonnoirs, panneaux, machines, "
         "meubles. Accroupi : dans l'autre sens. Portes, lits et coffres doubles ne bougent pas."),
        ("Sneak-right-click: a Wayfarers machine changes its setting; Wayfarers decoration or furniture comes back to "
         "your inventory.",
         "Accroupi + clic droit : une machine Wayfarers change de réglage ; un bloc déco ou un meuble Wayfarers "
         "revient dans ton inventaire."),
        ("Craft: three brass ingots and an iron ingot.", "Fabrication : trois lingots de laiton et un lingot de fer."),
    ], ["wayfarers:brass_wrench"]),
    ("grapple", "wayfarers:grappling_hook", ("Grappling Hook", "Grappin"), [
        ("Right-click to fire the claw up to 32 blocks. When it bites a block, the chain reels you in; a small hop at "
         "the end lifts you onto the ledge.",
         "Clic droit pour lancer la griffe jusqu'à 32 blocs. Quand elle mord un bloc, la chaîne te tire ; un petit "
         "bond à l'arrivée te hisse sur le rebord."),
        ("Sneak or right-click again to let go. No fall damage while reeled in, nor just after.",
         "Accroupi ou clic droit à nouveau pour lâcher. Aucun dégât de chute pendant la traction, ni juste après."),
        ("Craft: a tripwire hook, an iron chain and two brass ingots.",
         "Fabrication : un crochet, une chaîne en fer et deux lingots de laiton."),
    ], ["wayfarers:grappling_hook"]),
    ("glider", "wayfarers:brass_glider", ("Brass Glider", "Planeur en laiton"), [
        ("Hold it in either hand and jump from somewhere high: it opens by itself. You sink slowly and glide where "
         "you look, and landing never hurts.",
         "Tiens-le en main et saute d'un endroit élevé : il s'ouvre tout seul. Tu descends doucement vers là où tu "
         "regardes, sans dégâts à l'atterrissage."),
        ("With the Grappling Hook: climb a tower, then glide to the next one. It wears in flight; repair it with "
         "brass.",
         "Avec le grappin : grimpe sur une tour, puis plane jusqu'à la suivante. Il s'use en vol ; répare-le avec du "
         "laiton."),
        ("Craft: three brass ingots, four leather and a phantom membrane.",
         "Fabrication : trois lingots de laiton, quatre cuirs et une membrane de phantom."),
    ], ["wayfarers:brass_glider"]),
    ("rivet_gun", "wayfarers:rivet_gun", ("Rivet Gun", "Pistolet à rivets"), [
        ("Right-click to fire a hot rivet: 5 damage, fast and nearly straight. Ammo: Rivets from your inventory, or "
         "iron nuggets.",
         "Clic droit : tire un rivet brûlant (5 dégâts), rapide et presque droit. Munitions : les rivets de ton "
         "inventaire, sinon des pépites de fer."),
        ("Craft: three brass ingots, a copper ingot, a piston and a plank. 12 Rivets: an iron ingot, a copper ingot "
         "and a zinc nugget.",
         "Fabrication : trois lingots de laiton, un lingot de cuivre, un piston et une planche. 12 rivets : un lingot "
         "de fer, un lingot de cuivre et une pépite de zinc."),
    ], ["wayfarers:rivet_gun", "wayfarers:rivet"]),
    ("watch", "wayfarers:pocket_watch", ("Pocket Watch", "Montre à gousset"), [
        ("Its hand follows the sun, and a little window shows the sun by day and the moon by night.",
         "Son aiguille suit le soleil, et une petite fenêtre montre le soleil le jour et la lune la nuit."),
        ("Right-click: time, day number, moon phase and the biome you stand in.",
         "Clic droit : heure, numéro du jour, phase de lune et biome où tu te trouves."),
        ("Craft: a brass nugget, three brass ingots and a redstone.",
         "Fabrication : une pépite de laiton, trois lingots de laiton et une redstone."),
    ], ["wayfarers:pocket_watch"]),
    ("airship_compass", "wayfarers:airship_compass", ("Airship Compass", "Boussole de dirigeable"), [
        ("Right-click to find the nearest Sky Harbour (in the End: the Void Ship Wreck). Its aether needle then keeps "
         "pointing there.",
         "Clic droit pour trouver le Port céleste le plus proche (dans l'End : l'Épave du vide). Son aiguille "
         "d'éther pointe ensuite vers lui."),
        ("Craft: a compass, an aether crystal and three brass ingots.",
         "Fabrication : une boussole, un cristal d'éther et trois lingots de laiton."),
    ], ["wayfarers:airship_compass"]),
]


def guide_pages():
    """Pages of the "gadgets" manual category (declared in guide.CATEGORIES)."""
    return [(pid, "gadgets", icon, title, paras, items) for pid, icon, title, paras, items in PAGES]


# ------------------------------------------------------------------ sprite painter
# material -> (light, mid, dark)
MATS = {
    "B": ((250, 222, 130), (204, 162, 72), (140, 100, 40)),     # brass
    "C": ((240, 166, 104), (186, 112, 52), (122, 64, 30)),      # copper
    "I": ((228, 228, 236), (164, 164, 176), (98, 98, 112)),     # iron
    "X": ((96, 88, 90), (62, 56, 58), (38, 34, 36)),            # dark iron
    "W": ((160, 100, 64), (110, 64, 42), (74, 40, 26)),         # mahogany
    "L": ((166, 68, 54), (114, 38, 32), (76, 22, 20)),          # oxblood leather
    "Q": ((248, 240, 218), (228, 214, 182), (196, 178, 146)),   # cream dial
    "A": ((196, 252, 255), (70, 212, 255), (30, 132, 196)),     # aether glass
    "M": ((255, 226, 150), (255, 180, 72), (214, 122, 30)),     # amber
    "V": ((242, 232, 202), (216, 200, 162), (172, 152, 116)),   # canvas
    "R": ((236, 90, 66), (184, 44, 34), (122, 24, 20)),         # red
    "G": ((126, 224, 214), (67, 179, 174), (38, 118, 116)),     # verdigris
    "K": ((52, 44, 42), (40, 32, 30), (30, 24, 22)),            # ink (watch hands)
}
FLAT = {"K"}  # drawn without shading (thin lines)


class Grid:
    """16x16 grid of material letters (None = empty); shapes are tested at pixel centres."""

    def __init__(self, size=16):
        self.n = size
        self.m = [[None] * size for _ in range(size)]
        self.force = {}  # (x, y) -> "light" | "mid" | "dark" | rgb

    def paint(self, mat, test):
        for y in range(self.n):
            for x in range(self.n):
                if test(x + 0.5, y + 0.5):
                    self.m[y][x] = mat

    def clear(self, test):
        self.paint(None, test)

    def px(self, x, y, mat, tone=None):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.m[y][x] = mat
            if tone:
                self.force[(x, y)] = tone
            else:
                self.force.pop((x, y), None)

    def disc(self, mat, cx, cy, r):
        self.paint(mat, lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r)

    def ring(self, mat, cx, cy, r0, r1):
        self.paint(mat, lambda x, y: r0 * r0 < (x - cx) ** 2 + (y - cy) ** 2 <= r1 * r1)

    def seg(self, mat, x0, y0, x1, y1, w):
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy

        def t(x, y):
            u = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / ll)) if ll else 0.0
            px, py = x0 + u * dx, y0 + u * dy
            return (x - px) ** 2 + (y - py) ** 2 <= w * w
        self.paint(mat, t)

    def box(self, mat, x0, y0, x1, y1):
        """Inclusive pixel box."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, mat)

    def render(self, outline=True):
        n = self.n
        cv = Canvas(n, n)

        def filled(x, y):
            return 0 <= x < n and 0 <= y < n and self.m[y][x] is not None

        for y in range(n):
            for x in range(n):
                mat = self.m[y][x]
                if mat is None:
                    continue
                light, mid, dark = MATS[mat]
                tone = self.force.get((x, y))
                if isinstance(tone, tuple):
                    cv.set(x, y, tone)
                    continue
                if tone is None:
                    if mat in FLAT:
                        tone = "mid"
                    else:
                        up = filled(x, y - 1) and self.m[y - 1][x] == mat
                        left = filled(x - 1, y) and self.m[y][x - 1] == mat
                        down = filled(x, y + 1) and self.m[y + 1][x] == mat
                        right = filled(x + 1, y) and self.m[y][x + 1] == mat
                        if not up or not left:
                            tone = "light" if (down and right) or not (up or left) else "mid"
                        elif not down or not right:
                            tone = "dark"
                        else:
                            tone = "mid"
                cv.set(x, y, {"light": light, "mid": mid, "dark": dark}[tone])
        if outline:
            for y in range(n):
                for x in range(n):
                    if self.m[y][x] is not None:
                        continue
                    near = [self.m[yy][xx] for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if filled(xx, yy)]
                    if near:
                        d = MATS[near[0]][2]
                        cv.set(x, y, tuple(int(c * 0.38) for c in d))
        return cv


def _along(x0, y0, x1, y1, t):
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t


def _wrench():
    g = Grid()
    a, b = (3.2, 12.8), (10.4, 5.6)
    g.seg("B", *a, *b, 1.3)
    # leather-wrapped grip between two brass collars
    g.seg("L", *_along(*a, *b, 0.12), *_along(*a, *b, 0.5), 1.4)
    for t in (0.1, 0.52):
        cx, cy = _along(*a, *b, t)
        g.seg("B", cx - 1.25, cy - 1.25, cx + 1.25, cy + 1.25, 0.5)
    # adjustable head: a wide disc with a deep slot towards the top-right (fixed and sliding jaws)
    cx, cy = 11.3, 4.7
    g.disc("B", cx, cy, 4.1)
    ux, uy = 0.7071, -0.7071
    g.clear(lambda x, y: ((x - cx) * ux + (y - cy) * uy) > -0.9 and abs((x - cx) * uy - (y - cy) * ux) < 1.45)
    # knurled worm screw (iron) across the neck
    g.seg("I", 8.0, 6.6, 9.6, 8.2, 0.75)
    g.px(9, 8, "I", "dark")
    # rounded pommel
    g.disc("B", 2.6, 13.4, 1.9)
    return g.render()


def _grappling_hook():
    g = Grid()
    # barrel (brass) pointing right
    g.box("B", 3, 5, 10, 7)
    g.box("X", 4, 4, 9, 4)          # dark rail on top
    g.box("I", 11, 5, 11, 7)         # muzzle ring
    # three-prong claw at the muzzle
    g.box("I", 12, 6, 13, 6)
    g.seg("I", 12.5, 6.5, 14.6, 2.6, 0.6)
    g.seg("I", 12.5, 6.5, 14.8, 10.2, 0.6)
    g.px(14, 1, "I", "light")
    g.px(15, 10, "I", "dark")
    g.px(14, 6, "I")
    g.px(15, 6, "I", "light")
    # chain drum (copper) under the barrel
    g.disc("C", 7.5, 9.5, 2.1)
    g.px(7, 9, "X")
    # wooden grip, raked back
    g.seg("W", 4.6, 8.4, 2.4, 13.4, 1.25)
    g.box("B", 3, 8, 5, 8)
    # trigger
    g.px(6, 10, "X")
    # chain trailing from the drum to the claw
    for x, y in ((9, 10), (10, 9), (11, 9)):
        g.px(x, y, "X")
    return g.render()


def _glider():
    g = Grid()
    # canvas wing: wide arc, scalloped trailing edge
    g.paint("V", lambda x, y: (x - 8) ** 2 / 64.0 + (y - 9.5) ** 2 / 30.0 <= 1.0 and 2.0 <= y <= 9.5)
    for sx in (2.0, 6.0, 10.0, 14.0):
        g.clear(lambda x, y, sx=sx: (x - sx) ** 2 + (y - 10.4) ** 2 <= 2.6)
    # brass ribs from the hub
    hub = (8.0, 3.2)
    for tx, ty in ((0.6, 8.0), (4.0, 8.6), (8.0, 9.2), (12.0, 8.6), (15.4, 8.0)):
        g.seg("B", hub[0], hub[1], tx, ty, 0.45)
    # leading edge spar
    g.paint("B", lambda x, y: abs((x - 8) ** 2 / 64.0 + (y - 9.5) ** 2 / 30.0 - 1.0) < 0.12 and y < 8.5)
    # hub and the handle bar hanging under it
    g.disc("C", 8.0, 3.2, 1.3)
    g.seg("X", 8.0, 4.0, 8.0, 12.5, 0.5)
    g.box("L", 6, 12, 10, 13)
    g.px(5, 12, "B")
    g.px(11, 12, "B")
    return g.render()


def _rivet_gun():
    g = Grid()
    # verdigris air tank (a capsule) above the barrel
    g.seg("G", 3.6, 4.6, 9.4, 4.6, 1.7)
    for x in (5, 8):
        for y in range(3, 7):
            g.px(x, y, "B", "dark" if y == 6 else "mid")
    # barrel and its flared bell
    g.box("B", 4, 7, 11, 9)
    g.paint("B", lambda x, y: 11.5 <= x <= 15.5 and abs(y - 8.0) <= 1.5 + (x - 11.5) * 0.55)
    g.clear(lambda x, y: x > 14.0 and abs(y - 8.0) < 1.1)
    g.px(14, 8, "M", (255, 208, 110))
    g.px(15, 8, "M", (255, 160, 60))
    # pressure gauge on the back of the tank
    g.disc("Q", 11.8, 3.8, 1.8)
    g.px(12, 3, "R", "mid")
    g.px(11, 4, "K")
    # wooden grip, trigger guard
    g.seg("W", 5.2, 10.2, 3.2, 14.2, 1.35)
    g.box("X", 7, 10, 7, 11)
    g.px(6, 12, "X")
    return g.render()


def _rivets():
    g = Grid()
    for hx, hy, mat in ((3, 2, "C"), (9, 5, "I"), (4, 9, "I")):
        # domed head (3 wide, 2 tall) and a shank below it
        g.box(mat, hx, hy + 1, hx + 4, hy + 2)
        g.box(mat, hx + 1, hy, hx + 3, hy)
        g.box(mat, hx + 2, hy + 3, hx + 2, hy + 5)
        g.px(hx + 1, hy, mat, "light")
        g.px(hx + 4, hy + 2, mat, "dark")
    return g.render()


def _dial(g, cx, cy, r):
    """Cream dial, lit from the top-left."""
    for y in range(16):
        for x in range(16):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                d = (x + 0.5 - cx) + (y + 0.5 - cy)
                g.px(x, y, "Q", "light" if d < -3.5 else "dark" if d > 4.5 else "mid")


def _watch(frame, frames=16):
    """Brass case, cream dial, hour hand at (frame / frames) of a turn per half day; noon at the top."""
    g = Grid()
    cx, cy = 8.0, 9.0
    g.disc("B", cx, cy, 6.5)
    _dial(g, cx, cy, 5.1)
    # crown and bow
    g.box("B", 7, 1, 8, 2)
    g.ring("B", 8.0, 1.4, 0.7, 1.9)
    g.clear(lambda x, y: y < 0.9)
    # hour marks at 12, 3, 6 and 9
    for x, y in ((7, 4), (8, 4), (12, 8), (12, 9), (3, 8), (3, 9)):
        g.px(x, y, "B", "dark")
    # the hour hand: sun angle v in [0, 1) (0 = noon), two turns a day
    v = frame / frames
    a = 2 * math.pi * (2 * v)
    for i in range(1, 5):
        r = i * 0.9
        g.px(int(math.floor(cx + math.sin(a) * r)), int(math.floor(cy - math.cos(a) * r)), "K")
    # day / night window under the pin: amber sun or pale moon
    day = v < 0.25 or v >= 0.75
    for x in (7, 8):
        g.px(x, 12, "M" if day else "A", (255, 190, 70) if day else (190, 214, 255))
    g.px(7, 8, "B", "light")
    g.px(8, 8, "B", "mid")
    g.px(7, 9, "B", "mid")
    g.px(8, 9, "B", "dark")
    return g.render()


def _airship_compass(frame, frames=16):
    """Octagonal brass case with corner rivets, aether glass and a needle at (frame / frames) of a turn, clockwise."""
    g = Grid()
    cx, cy = 8.0, 8.5
    g.paint("B", lambda x, y: abs(x - cx) <= 6.6 and abs(y - cy) <= 6.6 and abs(x - cx) + abs(y - cy) <= 9.2)
    g.paint("X", lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= 4.9 ** 2)
    g.paint("A", lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= 4.2 ** 2)
    for x, y in ((3, 4), (12, 4), (3, 13), (12, 13)):
        g.px(x, y, "I")
    # tiny balloon on top
    g.disc("C", 8.0, 1.4, 1.3)
    a = 2 * math.pi * frame / frames
    for i in range(-2, 5):
        r = i * 0.85
        x = int(math.floor(cx + math.sin(a) * r))
        y = int(math.floor(cy - math.cos(a) * r))
        g.px(x, y, "R" if i > 0 else "I", "mid" if i > 0 else "light")
    g.px(int(cx), int(cy), "B", "light")
    return g.render()


def sprites():
    out = {
        "item/brass_wrench": _wrench(),
        "item/grappling_hook": _grappling_hook(),
        "item/brass_glider": _glider(),
        "item/rivet_gun": _rivet_gun(),
        "item/rivet": _rivets(),
    }
    for f in range(WATCH_FRAMES):
        out[f"item/pocket_watch_{f:02d}"] = _watch(f, WATCH_FRAMES)
    for f in range(COMPASS_FRAMES):
        out[f"item/airship_compass_{f:02d}"] = _airship_compass(f, COMPASS_FRAMES)
    out["item/pocket_watch"] = out["item/pocket_watch_00"]
    out["item/airship_compass"] = out["item/airship_compass_00"]
    return out


WATCH_FRAMES = 16
COMPASS_FRAMES = 16


# ------------------------------------------------------------------ 3D in-hand models
# One shared 16x16 palette texture (textures/item/3d/gadgets.png): 4x4 cells of flat colours, each face samples
# the centre of its cell (same trick as held3d.py).
CELLS = ["brass", "brass_light", "brass_dark", "copper", "iron", "iron_dark", "dark", "wood", "leather", "canvas",
         "canvas_dark", "cream", "glass", "amber", "verdigris", "red"]
CELL_COLORS = {
    "brass": MATS["B"][1], "brass_light": MATS["B"][0], "brass_dark": MATS["B"][2], "copper": MATS["C"][1],
    "iron": MATS["I"][1], "iron_dark": MATS["I"][2], "dark": MATS["X"][1], "wood": MATS["W"][1],
    "leather": MATS["L"][1], "canvas": MATS["V"][0], "canvas_dark": MATS["V"][2], "cream": MATS["Q"][1],
    "glass": MATS["A"][1], "amber": MATS["M"][1], "verdigris": MATS["G"][1], "red": MATS["R"][1],
}
PALETTE_TEXTURE = "item/3d/gadgets"


def palette_texture():
    cv = Canvas(16, 16)
    for i, key in enumerate(CELLS):
        cx, cy = i % 4, i // 4
        c = CELL_COLORS[key]
        for y in range(cy * 4, cy * 4 + 4):
            for x in range(cx * 4, cx * 4 + 4):
                edge = x in (cx * 4, cx * 4 + 3) or y in (cy * 4, cy * 4 + 3)
                cv.set(x, y, tuple(int(v * (0.9 if edge else 1.0)) for v in c))
    return cv


def _uv(key):
    i = CELLS.index(key)
    cx, cy = i % 4, i // 4
    return [cx * 4 + 1, cy * 4 + 1, cx * 4 + 3, cy * 4 + 3]


def box(x0, y0, z0, x1, y1, z1, key):
    return (x0, y0, z0, x1, y1, z1, key)


def _wrench_3d():
    """Upright like a sword (grip around y 2-9), the jaw on top."""
    return [box(7, -1, 7, 9, 1, 9, "brass_light"),                       # pommel
            box(7.25, 1, 7.25, 8.75, 12, 8.75, "brass"),                  # shaft
            box(6.75, 2, 6.75, 9.25, 9, 9.25, "leather"),                 # grip
            box(6.5, 1.5, 6.5, 9.5, 2.5, 9.5, "brass_dark"), box(6.5, 9, 6.5, 9.5, 10, 9.5, "brass_dark"),
            box(6.5, 12, 7, 11.5, 15, 9, "brass"),                        # head
            box(6.5, 15, 7, 8.5, 20, 9, "brass_light"),                   # fixed jaw
            box(10, 15, 7, 12, 19, 9, "brass"),                           # sliding jaw
            box(8.5, 12.5, 6.5, 12.5, 14, 9.5, "iron"),                   # worm screw
            box(12.5, 12.75, 7.25, 13, 13.75, 8.75, "iron_dark")]


def _gun_body(barrel="brass"):
    """Shared pistol layout: forward is -z, up is +y, grip around (8, 2-8, 9-11.5)."""
    return [box(7, 9, 1, 9, 11, 12, barrel),                             # barrel
            box(7.25, 11, 3, 8.75, 11.5, 11, "dark"),                    # top rail
            box(6.75, 8, 8, 9.25, 10, 13, barrel),                       # breech
            box(7, 2, 9, 9, 8, 11.5, "wood"),                            # grip
            box(6.75, 1.5, 8.75, 9.25, 2.5, 11.75, "brass_dark"),        # grip cap
            box(7.75, 6.5, 7.5, 8.25, 8, 8, "dark"),                     # trigger
            box(7.5, 6, 6.5, 8.5, 6.5, 8.5, "dark")]                     # trigger guard


def _grappling_hook_3d():
    return _gun_body() + [
        box(6.5, 8.5, 0, 9.5, 11.5, 1, "iron"),                          # muzzle ring
        box(6.5, 5.5, 4, 9.5, 8.5, 7.5, "copper"),                       # chain drum
        box(6, 6.5, 5, 6.5, 7.5, 6.5, "iron_dark"), box(9.5, 6.5, 5, 10, 7.5, 6.5, "iron_dark"),
        box(7.5, 9.5, -2, 8.5, 10.5, 0, "iron"),                         # loaded claw: shank
        box(7.5, 10.5, -3, 8.5, 12.5, -2, "iron"), box(7.5, 7.5, -3, 8.5, 9.5, -2, "iron"),
        box(5.5, 9.5, -3, 7.5, 10.5, -2, "iron"), box(8.5, 9.5, -3, 10.5, 10.5, -2, "iron"),
        box(7.5, 12, -4, 8.5, 12.5, -3, "iron_dark"), box(7.5, 7.5, -4, 8.5, 8, -3, "iron_dark"),
        box(5.5, 9.5, -4, 6, 10.5, -3, "iron_dark"), box(10, 9.5, -4, 10.5, 10.5, -3, "iron_dark")]


def _claw_3d():
    """The flying claw, pointing to +x (turned along its flight like an arrow)."""
    out = [box(2, 7.5, 7.5, 10, 8.5, 8.5, "iron"),                       # shank
           box(1, 7, 7, 2.5, 9, 9, "brass"),                             # chain eye
           box(9, 7, 7, 11, 9, 9, "brass"),                              # hub
           box(11, 7.5, 7.5, 13, 8.5, 8.5, "iron_dark")]                 # point
    # four arms going out 3 px from the hub, their tips bent forward
    out += [box(10, 9, 7.5, 11, 12, 8.5, "iron"), box(11, 11, 7.5, 13, 12, 8.5, "iron_dark"),
            box(10, 4, 7.5, 11, 7, 8.5, "iron"), box(11, 4, 7.5, 13, 5, 8.5, "iron_dark"),
            box(10, 7.5, 9, 11, 8.5, 12, "iron"), box(11, 7.5, 11, 13, 8.5, 12, "iron_dark"),
            box(10, 7.5, 4, 11, 8.5, 7, "iron"), box(11, 7.5, 4, 13, 8.5, 5, "iron_dark")]
    return out


def _rivet_gun_3d():
    return _gun_body() + [
        box(6, 8, -2, 10, 12, 1, "brass_light"),                         # flared bell
        box(6.5, 8.5, -2.25, 9.5, 11.5, -2, "dark"),                     # bore
        box(7.5, 9.5, -2.5, 8.5, 10.5, -2.25, "amber"),                  # hot rivet
        box(6.5, 11.5, 2, 9.5, 14.5, 10, "verdigris"),                   # air tank
        box(6.25, 11.25, 4, 9.75, 14.75, 5, "brass_dark"), box(6.25, 11.25, 7, 9.75, 14.75, 8, "brass_dark"),
        box(9.5, 12, 10, 10.5, 14, 12, "brass"),                         # pressure gauge
        box(10.5, 12.25, 10.25, 10.75, 13.75, 11.75, "cream"),
        box(10.75, 13, 10.75, 11, 13.5, 11.25, "red")]


def _glider_3d():
    """Handle bar in the hand, the canvas wing above the head. Forward is -z, up is +y."""
    out = [box(2, 6, 7.5, 14, 7, 8.5, "leather"),                        # handle bar
           box(1.5, 5.5, 7, 2.5, 7.5, 9, "brass"), box(13.5, 5.5, 7, 14.5, 7.5, 9, "brass"),
           box(2, 7, 7.75, 2.5, 24, 8.25, "dark"), box(13.5, 7, 7.75, 14, 24, 8.25, "dark"),   # struts
           box(-8, 24, -2, 24, 24.5, 14, "canvas"),                      # wing
           box(-8, 24.5, -2.5, 24, 25.5, -1.5, "brass"),                 # leading edge spar
           box(7.5, 24.5, -2, 8.5, 25.5, 14, "brass_dark"),              # keel
           box(-8, 23.5, 12, 24, 24, 14, "canvas_dark")]                 # trailing hem
    for x in (-4, 2, 13, 19):
        out.append(box(x, 24.5, -1.5, x + 1, 25, 13, "brass"))          # ribs
    return out


MODELS_3D = {"brass_wrench": _wrench_3d, "grappling_hook": _grappling_hook_3d, "rivet_gun": _rivet_gun_3d,
             "brass_glider": _glider_3d}

# Guns and glider are modelled forward = -z, up = +y. Third person: the hand's frame has +y forward and +z up,
# hence the 90 degree turn around x; first person: the camera looks along -z, so no turn is needed.
GUN_DISPLAY = {
    "thirdperson_righthand": {"rotation": [90, 0, 0], "translation": [0, 1.5, 1.5], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [90, 0, 0], "translation": [0, 1.5, 1.5], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, 6, 0], "translation": [0, 3, 1], "scale": [0.7, 0.7, 0.7]},
    "firstperson_lefthand": {"rotation": [0, 6, 0], "translation": [0, 3, 1], "scale": [0.7, 0.7, 0.7]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
}
GLIDER_DISPLAY = {
    "thirdperson_righthand": {"rotation": [90, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [90, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [20, -15, 0], "translation": [1, 0, -2], "scale": [0.45, 0.45, 0.45]},
    "firstperson_lefthand": {"rotation": [20, -15, 0], "translation": [1, 0, -2], "scale": [0.45, 0.45, 0.45]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
}


def _display(gid):
    if gid == "brass_wrench":
        from .held3d import DISPLAY
        return DISPLAY
    return GLIDER_DISPLAY if gid == "brass_glider" else GUN_DISPLAY


def model_json(boxes, display=None):
    tex = f"{NS}:{PALETTE_TEXTURE}"
    elements = []
    for x0, y0, z0, x1, y1, z1, key in boxes:
        uv = _uv(key)
        elements.append({"from": [x0, y0, z0], "to": [x1, y1, z1],
                         "faces": {f: {"uv": uv, "texture": "#t"} for f in ("north", "south", "east", "west", "up", "down")}})
    out = {"textures": {"t": tex, "particle": tex}, "elements": elements}
    if display:
        out["display"] = display
    return out


# ------------------------------------------------------------------ assets (gen_assets.py)
def _flat(name):
    return {"type": "minecraft:model", "model": f"{NS}:item/{name}"}


def _held(gid):
    return {"type": "minecraft:select", "property": "minecraft:display_context",
            "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": _flat(gid)}],
            "fallback": _flat(f"{gid}_3d")}


def _frames(gid, n):
    """range_dispatch entries centred on each frame; frame 0 also closes the turn."""
    entries = [{"threshold": 0.0, "model": _flat(f"{gid}_00")}]
    entries += [{"threshold": k - 0.5, "model": _flat(f"{gid}_{k:02d}")} for k in range(1, n)]
    entries.append({"threshold": n - 0.5, "model": _flat(f"{gid}_00")})
    return entries


def item_definitions():
    defs = {gid: {"model": _held(gid)} for gid in MODELS_3D}
    # the flying claw renders the hook item tagged "claw" (GrapplingHookEntity.clawStack)
    defs["grappling_hook"] = {"model": {
        "type": "minecraft:select", "property": "minecraft:custom_model_data", "index": 0,
        "cases": [{"when": "claw", "model": _flat("grappling_hook_claw")}],
        "fallback": _held("grappling_hook")}}

    def clock(source):
        return {"type": "minecraft:range_dispatch", "property": "minecraft:time", "source": source,
                "scale": float(WATCH_FRAMES), "entries": _frames("pocket_watch", WATCH_FRAMES)}
    # like the vanilla clock: follows the sun in the Overworld, spins elsewhere
    defs["pocket_watch"] = {"model": {
        "type": "minecraft:select", "property": "minecraft:context_dimension",
        "cases": [{"when": "minecraft:overworld", "model": clock("daytime")}], "fallback": clock("random")}}
    # like a lodestone compass: points to the stored target, spins without one
    defs["airship_compass"] = {"model": {
        "type": "minecraft:range_dispatch", "property": "minecraft:compass", "target": "lodestone",
        "scale": float(COMPASS_FRAMES), "entries": _frames("airship_compass", COMPASS_FRAMES)}}
    return defs


def item_models():
    """models/item/<name>.json for the 3D models and animation frames (base sprites come from content.ITEMS)."""
    out = {}
    for gid, fn in MODELS_3D.items():
        out[f"{gid}_3d"] = model_json(fn(), _display(gid))
    out["grappling_hook_claw"] = model_json(_claw_3d())
    for gid, n in (("pocket_watch", WATCH_FRAMES), ("airship_compass", COMPASS_FRAMES)):
        for k in range(n):
            out[f"{gid}_{k:02d}"] = {"parent": "minecraft:item/generated", "textures": {"layer0": f"{NS}:item/{gid}_{k:02d}"}}
    return out


HANDHELD = {"brass_wrench"}


def textures():
    out = sprites()
    out[PALETTE_TEXTURE] = palette_texture()
    return out

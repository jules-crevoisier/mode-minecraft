"""The recipe viewer (com.brasshaven.client.recipes): its GUI sprites and the --mockup previews.

Called from tools/gen_gui.py with that module as ``G``. The mockups mirror the layout constants of ItemGrid.java,
RecipePanel.java and RecipeScreen.java (keep them in sync) and draw text on Minecraft's glyph advances, so what fits
here fits in game: build/previews/gui/recipes_panel.png (a crafting table with the item list and a search),
recipes_view.png (the recipes of the Brass Ingot, opened from the crafting table: "+" buttons, a missing ingredient
in red), recipes_uses.png (its uses) and recipes_furnace.png, plus _en copies.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
TEX = os.path.join(RES, "assets", "brasshaven", "textures")

# ---- layout: keep in sync with ItemGrid.java / RecipePanel.java / RecipeScreen.java --------------------------
SLOT = 18
PAD = 6
HEADER = 14
SEARCH = 14
W, H = 300, 214  # RecipeScreen
CARD_X, CARD_Y, CARD_W, CARD_H = 10, 62, 280, 124
TAB = 22
CELLS = {"crafting": (136, 62), "smelting": (136, 40), "stonecutting": (90, 26), "smithing": (136, 26), "chisel": (276, 44)}


def box_w(cols):
    return cols * SLOT + 2 * PAD


def box_h(rows):
    return rows * SLOT + PAD + HEADER + 3 + SEARCH + PAD - 1


def cols_for(w):
    return (w - 2 * PAD) // SLOT


def rows_for(h):
    return (h - (PAD + HEADER + 3 + SEARCH + PAD - 1)) // SLOT


# ---- sprites ------------------------------------------------------------------------------------------------
LEFT = [
    "..........",
    "....k.....",
    "...kk.....",
    "..kkkkkkk.",
    ".kkkkkkkk.",
    ".kkkkkkkk.",
    "..kkkkkkk.",
    "...kk.....",
    "....k.....",
    "..........",
]
PLUS = [
    "..........",
    "....kk....",
    "....kk....",
    "....kk....",
    ".kkkkkkkk.",
    ".kkkkkkkk.",
    "....kk....",
    "....kk....",
    "....kk....",
    "..........",
]
BACK = [
    "..........",
    "...k......",
    "..kk......",
    ".kkkkkkk..",
    "..kk....k.",
    "...k....k.",
    "........k.",
    "....kkkk..",
    "..........",
    "..........",
]
BOOK = [
    "..........",
    ".kkk..kkk.",
    "k...kk...k",
    "k.kk..kk.k",
    "k...kk...k",
    "k.kk..kk.k",
    "k...kk...k",
    "kkkkkkkkkk",
    "....kk....",
    "..........",
]
COG = [
    "....kk....",
    ".k.kkkk.k.",
    "..kkkkkk..",
    ".kkk..kkk.",
    "kkk....kkk",
    "kkk....kkk",
    ".kkk..kkk.",
    "..kkkkkk..",
    ".k.kkkk.k.",
    "....kk....",
]
GRID = [
    "..........",
    ".kk.kk.kk.",
    ".kk.kk.kk.",
    "..........",
    ".kk.kk.kk.",
    ".kk.kk.kk.",
    "..........",
    ".kk.kk.kk.",
    ".kk.kk.kk.",
    "..........",
]
RECIPES = [
    "kkkkkkk...",
    "k.k.k.k...",
    "kkkkkkk...",
    "k.k.k.k.k.",
    "kkkkkkk.kk",
    "k.k.k.k.k.",
    "kkkkkkk...",
    "..........",
    "..........",
    "..........",
]
FLAME = [
    "......o.......",
    ".....oao......",
    ".....oao......",
    "....oaaao.....",
    "...oaayaao....",
    "...oayyyao..o.",
    "..oaayyyaao.oo",
    "..oayyyyyaooao",
    ".oaayywyyaaoao",
    ".oayywwwyyaaao",
    ".oayywwwyyyaao",
    "..oayywwyyyao.",
    "...ooaaaaaoo..",
    ".....ooooo....",
]
SHAPELESS = [
    "kkk......kkk",
    "kk........kk",
    "k.k......k.k",
    "...k....k...",
    "....k..k....",
    ".....kk.....",
    ".....kk.....",
    "....k..k....",
    "...k....k...",
    "k.k......k.k",
    "kk........kk",
    "kkk......kkk",
]


def _glyph(G, name, art, color):
    g = G.Sprite(len(art[0]), len(art))
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch == "k":
                g.set(x, y, color)
    g.save(name)


def sprites(G):
    hexc, mix = G.hexc, G.mix
    ink = hexc("2B1B0C")
    # the item list's plate: soot outline, a riveted brass band, then the dark iron of the wells (border 6)
    s = G.Sprite(32, 32)
    base = hexc("221B18")
    import random
    rng = random.Random(11)
    for y in range(32):
        for x in range(32):
            n = rng.random()
            s.set(x, y, base if n > 0.1 else mix(base, G.IRON_LT if n > 0.05 else G.IRON_DK, 0.35))
    s.frame(0, 0, 31, 31, G.SOOT)
    G.brass_band(s, 1, 1, 30, 30, 3)
    s.frame(4, 4, 27, 27, G.IRON_DK)
    s.bevel(5, 5, 26, 26, G.SOOT, G.IRON_LT)
    for x, y in ((2, 2), (28, 2), (2, 28), (28, 28)):
        s.rivet(x, y)
    s.save("item_panel", nine=6)
    # an 18 px slot well (and the 26 px result well with a brass rim), one blit each
    for name, size in (("recipe/slot", 18), ("recipe/slot_big", 26)):
        w = G.Sprite(size, size)
        w.rect(0, 0, size - 1, size - 1, hexc("1B1512"))
        w.bevel(0, 0, size - 1, size - 1, G.SOOT, hexc("5A4632"))
        w.bevel(1, 1, size - 2, size - 2, hexc("120E0C"), hexc("2E2521"))
        if size > 18:
            w.frame(0, 0, size - 1, size - 1, G.BRASS_DK)
            w.bevel(1, 1, size - 2, size - 2, G.BRASS_LT, G.BRASS_SH)
            w.bevel(2, 2, size - 3, size - 3, G.SOOT, hexc("3E3430"))
            for x, y in ((1, 1), (size - 3, 1), (1, size - 3), (size - 3, size - 3)):
                w.rivet(x, y)
        w.save(name)
    # the arrow between ingredients and result: brass, soot outline, lit from above
    a = G.Sprite(22, 15)
    inside = set()
    for y in range(15):
        for x in range(22):
            shaft = 1 <= x <= 12 and 5 <= y <= 9
            head = 12 <= x <= 20 and abs(y - 7) <= (20 - x) * 7 / 8 + 0.01
            if shaft or head:
                inside.add((x, y))
    for (x, y) in inside:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in inside:
                a.set(x + dx, y + dy, G.SOOT)
    for (x, y) in inside:
        a.set(x, y, mix(G.BRASS_HI, G.BRASS_DK, y / 14))
    a.save("recipe/arrow")
    # the furnace flame (amber, yellow heart, white core)
    f = G.Sprite(14, 14)
    cols = {"o": hexc("8E2A10"), "a": hexc("FFB347"), "y": hexc("FFE07A"), "w": hexc("FFF8E0")}
    for y, row in enumerate(FLAME):
        for x, ch in enumerate(row):
            if ch in cols:
                f.set(x, y, cols[ch])
    f.save("recipe/flame")
    _glyph(G, "recipe/shapeless", SHAPELESS, hexc("4A3520"))
    # 10 px glyphs on the small brass buttons
    for name, art in (("left", LEFT), ("right", [r[::-1] for r in LEFT]), ("plus", PLUS), ("back", BACK), ("book", BOOK),
                      ("filter_mod", COG), ("filter_all", GRID), ("recipes", RECIPES)):
        _glyph(G, "glyph/" + name, art, ink)
    _glyph(G, "glyph/plus_missing", PLUS, hexc("9E1A12"))
    # a greyed small button (page arrows at the first / last page)
    b = G.Sprite(12, 12)
    for y in range(12):
        c = mix(hexc("6B625A"), hexc("3A332E"), y / 11)
        for x in range(12):
            b.set(x, y, c)
    b.frame(0, 0, 11, 11, G.SOOT)
    b.bevel(1, 1, 10, 10, hexc("857A70"), hexc("2A2420"))
    b.save("button_small_disabled", nine=3)


# ---- mockups ------------------------------------------------------------------------------------------------
SW, SH = 427, 240  # 1280 x 720 at GUI scale 3
TAG_ICONS = {"minecraft:planks": "minecraft:oak_planks", "minecraft:logs": "minecraft:oak_log",
             "minecraft:wooden_slabs": "minecraft:oak_slab", "minecraft:wool": "minecraft:white_wool",
             "minecraft:stone_tool_materials": "minecraft:cobblestone", "minecraft:coals": "minecraft:coal"}
_ICONS = {}
_LANG = {}


def _lang(li):
    if li not in _LANG:
        name = "fr_fr" if li else "en_us"
        _LANG[li] = json.load(open(os.path.join(RES, "assets", "brasshaven", "lang", name + ".json"), encoding="utf-8"))
    return _LANG[li]


def _name(rid, li):
    ns, n = rid.split(":")
    t = _lang(li)
    for k in (f"item.{ns}.{n}", f"block.{ns}.{n}"):
        if k in t:
            return t[k]
    return n.replace("_", " ").capitalize()


def _icon(G, rid):
    """The item's 16 x 16 icon: the mod's own texture, else the scratch vanilla pack (wf.gui_machines._mc)."""
    rid = TAG_ICONS.get(rid.lstrip("#"), rid.lstrip("#"))
    if rid in _ICONS:
        return _ICONS[rid]
    ns, name = rid.split(":")
    im = None
    if ns == "brasshaven":
        # the item's sprite, else a face of its block (machines and tables have no flat item texture)
        for p in [os.path.join(TEX, "item", name + ".png")] + [os.path.join(TEX, "block", name + sfx + ".png")
                                                              for sfx in ("", "_front", "_top", "_side")]:
            if os.path.exists(p):
                im = G.Image.open(p).convert("RGBA").crop((0, 0, 16, 16))
                break
    else:
        from .gui_machines import _mc
        im = _mc(name)
    _ICONS[rid] = im
    return im


def _recipe(rid):
    """A recipe file of the mod as the viewer shows it: (category, width, height, inputs, result id, count, cook)."""
    r = json.load(open(os.path.join(RES, "data", "brasshaven", "recipe", rid + ".json"), encoding="utf-8"))
    t = r["type"].split(":")[1]
    res = r["result"]
    if t == "crafting_shaped":
        pat = r["pattern"]
        w, h = max(len(p) for p in pat), len(pat)
        ins = [r["key"].get(ch) if ch != " " else None for row in pat for ch in row.ljust(w)]
        return "crafting", w, h, ins, res["id"], res.get("count", 1), None
    if t == "crafting_shapeless":
        return "crafting", 0, 0, list(r["ingredients"]), res["id"], res.get("count", 1), None
    if t in ("smelting", "blasting", "smoking", "campfire_cooking"):
        return t, 0, 0, [r["ingredient"]], res["id"], res.get("count", 1), (r.get("cookingtime", 200), r.get("experience", 0))
    return t, 0, 0, [r.get("ingredient")], res["id"], res.get("count", 1), None


class Shot:
    """A 427 x 240 GUI (1280 x 720 at scale 3) behind a dimmed world, with the texts in one language."""

    def __init__(self, G, li):
        self.G, self.li = G, li
        from . import guide
        self.guide = guide
        self.m = G.Mock(SW, SH)
        im = self.m.im
        for y in range(SH):  # a dusky landscape, then the screen's dark veil
            for x in range(SW):
                c = (52 + (x * 7 + y * 3) % 11, 70 + (x * 5 + y * 11) % 13, 44) if y > 120 else \
                    (70 + y // 4, 92 + y // 5, 120 + y // 6)
                im.putpixel((x, y), tuple(int(v * 0.42) for v in c) + (255,))

    def t(self, key, *args):
        from . import recipe_viewer
        return recipe_viewer.text(key, self.li, *args)

    def text(self, s, x, y, c, shadow=True, center=False, right=False, bold=False):
        self.m.text(s, x, y, c, shadow=shadow, center=center, right=right, bold=bold)

    def clip(self, s, width):
        if self.guide.text_width(s) <= width:
            return s
        while s and self.guide.text_width(s + "...") > width:
            s = s[:-1]
        return s + "..."

    def item(self, rid, x, y, count=1):
        im = _icon(self.G, rid) if rid else None
        if im is not None:
            self.m.im.alpha_composite(im, (x, y))
        elif rid:
            self.m.d.rectangle((x + 2, y + 2, x + 13, y + 13), outline=(150, 130, 100, 255))
        if count > 1:
            s = str(count)
            self.text(s, x + 17 - self.guide.text_width(s), y + 9, self.G.hexc("FFFFFF"))

    def sprite(self, name, x, y):
        self.m.im.alpha_composite(self.G.Image.open(self.G.sp(name)).convert("RGBA"), (x, y))

    def small(self, x, y, glyph, hover=False, disabled=False):
        self.m.nine("button_small_disabled" if disabled else "button_small_hover" if hover else "button_small", x, y, 12, 12, 3)
        self.sprite("glyph/" + glyph, x + 1, y + 1)

    def button(self, x, y, w, h, label, on=False, hover=False, disabled=False, glyph=None):
        G = self.G
        self.m.nine(("button_on_hover" if hover else "button_on") if on else "button_disabled" if disabled else
                    "button_hover" if hover else "button", x, y, w, h, 4)
        if glyph:
            self.sprite("glyph/" + glyph, x + (w - 10) // 2, y + (h - 10) // 2)
        if label:
            c = G.GOLD if on else G.hexc("C9C0B4") if disabled else G.hexc("FFFFFF")
            self.text(label, x + (w - self.guide.text_width(label) + 1) // 2, y + (h - 8) // 2, c)

    def veil(self, x, y, w, h, rgba):
        self.m.im.alpha_composite(self.G.Image.new("RGBA", (w, h), rgba), (x, y))

    def tooltip(self, mx, my, lines):
        """Vanilla tooltip box right of the mouse (left of it when it would leave the screen). lines: (text, colour)."""
        w = max(self.guide.text_width(s) for s, _c in lines) + 6
        h = len(lines) * 10 + (2 if len(lines) > 1 else 0) + 4
        x, y = mx + 12, my - 12
        if x + w > SW - 2:
            x = max(4, mx - 16 - w)
        y = max(2, min(y, SH - h - 2))
        d = self.m.d
        d.rectangle((x - 1, y, x + w, y + h - 1), fill=(16, 0, 16, 240))
        d.rectangle((x, y - 1, x + w - 1, y + h), fill=(16, 0, 16, 240))
        d.rectangle((x, y, x + w - 1, y + h - 1), outline=(80, 0, 255, 120))
        for i, (s, c) in enumerate(lines):
            self.text(s, x + 3, y + 3 + i * 10 + (2 if i else 0), c)

    def save(self, name):
        self.m.save(name)


# ---- a vanilla crafting table window (gray, bevelled), as the game draws it ----------------------------------
GRAY, LIGHT, DARK, SLOT_BG = (198, 198, 198, 255), (255, 255, 255, 255), (85, 85, 85, 255), (139, 139, 139, 255)


def _vanilla_slot(d, x, y, size=18):
    d.rectangle((x, y, x + size - 1, y + size - 1), fill=SLOT_BG)
    d.line((x, y, x + size - 2, y), fill=(55, 55, 55, 255))
    d.line((x, y, x, y + size - 2), fill=(55, 55, 55, 255))
    d.line((x + 1, y + size - 1, x + size - 1, y + size - 1), fill=LIGHT)
    d.line((x + size - 1, y + 1, x + size - 1, y + size - 1), fill=LIGHT)


def _crafting_table(s, left, top, grid=(), inv=()):
    d = s.m.d
    d.rectangle((left + 1, top + 1, left + 174, top + 164), fill=GRAY)
    d.rectangle((left, top + 2, left + 175, top + 163), fill=GRAY)
    d.line((left + 1, top + 1, left + 174, top + 1), fill=LIGHT)
    d.line((left + 1, top + 1, left + 1, top + 164), fill=LIGHT)
    d.line((left + 2, top + 165, left + 175, top + 165), fill=DARK)
    d.line((left + 175, top + 2, left + 175, top + 165), fill=DARK)
    d.rectangle((left - 1, top + 3, left - 1, top + 162), fill=(0, 0, 0, 255))
    d.rectangle((left + 3, top - 1, left + 172, top - 1), fill=(0, 0, 0, 255))
    d.rectangle((left + 176, top + 3, left + 176, top + 162), fill=(0, 0, 0, 255))
    d.rectangle((left + 3, top + 166, left + 172, top + 166), fill=(0, 0, 0, 255))
    for i in range(9):
        _vanilla_slot(d, left + 29 + (i % 3) * 18, top + 16 + (i // 3) * 18)
    _vanilla_slot(d, left + 119, top + 30, 26)
    d.rectangle((left + 90, top + 38, left + 103, top + 42), fill=(139, 139, 139, 255))
    d.polygon([(left + 104, top + 33), (left + 112, top + 40), (left + 104, top + 47)], fill=(139, 139, 139, 255))
    for r in range(3):
        for c in range(9):
            _vanilla_slot(d, left + 7 + c * 18, top + 83 + r * 18)
    for c in range(9):
        _vanilla_slot(d, left + 7 + c * 18, top + 141)
    d.rectangle((left + 5, top + 34, left + 24, top + 51), fill=(64, 110, 52, 255), outline=(30, 50, 25, 255))
    s.text("Fabrication" if s.li else "Crafting", left + 28, top + 6, (64, 64, 64, 255), shadow=False)
    s.text("Inventaire" if s.li else "Inventory", left + 8, top + 72, (64, 64, 64, 255), shadow=False)
    for i, rid in enumerate(grid):
        if rid:
            s.item(rid, left + 30 + (i % 3) * 18, top + 17 + (i // 3) * 18)
    for i, (rid, n) in enumerate(inv):
        if rid:
            row, col = divmod(i, 9)
            yy = top + 142 if row == 3 else top + 84 + row * 18
            s.item(rid, left + 8 + col * 18, yy, n)


def _container_buttons(s, left, top, w):
    """ContainerButtons over a window with five slots or more: search box and Sort / Take / Deposit / Nearby."""
    G = s.G
    y = max(15, top) - 14
    for i, g in enumerate(("sort", "take", "deposit", "nearby")):
        s.m.nine("button_small", left + w - 14 - i * 13, y, 12, 12, 3)
        s.sprite("glyph/" + g, left + w - 13 - i * 13, y + 1)
    sw = max(40, w - 4 * 13 - 8)
    s.m.d.rectangle((left + 2, y + 1, left + 2 + sw - 1, y + 11), fill=(0, 0, 0, 255), outline=(160, 160, 160, 255))
    s.text("Rechercher..." if s.li else "Search...", left + 6, y + 3, G.hexc("707070"))


def _panel(s, gui_right, query, items, page, pages, hover=None):
    """RecipePanel beside a window ending at ``gui_right``: returns the box and the slot of each shown item."""
    G = s.G
    x0, x1 = gui_right + 4, SW - 4
    cols, rows = min(9, cols_for(x1 - x0)), min(16, rows_for(SH - 8))
    bw, bh = box_w(cols), box_h(rows)
    bx, by = x1 - bw, (SH - bh) // 2
    s.m.nine("item_panel", bx, by, bw, bh, 6)
    s.small(bx + PAD, by + PAD - 1, "left", disabled=page == 0)
    s.small(bx + bw - PAD - 12, by + PAD - 1, "right", disabled=page == pages - 1)
    s.text(f"{page + 1} / {pages}", bx + bw // 2, by + PAD + 1, G.CREAM_SOFT, shadow=True, center=True)
    gx, gy = bx + PAD, by + PAD + HEADER - 1
    spots = {}
    for i in range(cols * rows):
        sx, sy = gx + (i % cols) * SLOT, gy + (i // cols) * SLOT
        s.sprite("recipe/slot", sx, sy)
        if i < len(items):
            s.item(items[i], sx + 1, sy + 1)
            spots[items[i]] = (sx, sy)
            if items[i] == hover:
                s.veil(sx + 1, sy + 1, 16, 16, (255, 245, 220, 96))
    s.m.nine("inset", bx + PAD, by + bh - PAD - SEARCH, bw - 2 * PAD - 14, SEARCH, 4)
    if query:
        s.text(query, bx + PAD + 3, by + bh - PAD - SEARCH + 4, G.CREAM, shadow=True)
    else:
        s.text(s.t("gui.brasshaven.recipes.search"), bx + PAD + 3, by + bh - PAD - SEARCH + 4, G.MUTED, shadow=True)
    s.small(bx + bw - PAD - 12, by + bh - PAD - SEARCH + 1, "filter_all")
    return (bx, by, bw, bh, cols, rows), spots


def _mod_items():
    """The mod's items in its creative tab order (ModItems.java registration order), as ids."""
    import re
    src = open(os.path.join(ROOT, "src", "main", "java", "com", "brasshaven", "registry", "ModItems.java"), encoding="utf-8").read()
    ids = []
    for m in re.finditer(r'(?:register|block|simple|item)\w*\("([a-z0-9_]+)"', src):
        rid = "brasshaven:" + m.group(1)
        if rid not in ids:
            ids.append(rid)
    for k in _lang(0):  # then the other blocks and items of the mod (decorations, metals...)
        parts = k.split(".")
        if len(parts) == 3 and parts[0] in ("item", "block") and parts[1] == "brasshaven":
            rid = "brasshaven:" + parts[2]
            if rid not in ids:
                ids.append(rid)
    return ids


def _fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def mockup_panel(G, li):
    s = Shot(G, li)
    left, top = (SW - 176) // 2, (SH - 166) // 2
    inv = [("brasshaven:brass_ingot", 12), ("minecraft:iron_ingot", 5), ("brasshaven:zinc_ingot", 3),
           ("minecraft:copper_ingot", 20), ("minecraft:oak_planks", 32), ("minecraft:stick", 9)] + [(None, 0)] * 21 + \
          [("brasshaven:brass_wrench", 1), ("minecraft:torch", 24)] + [(None, 0)] * 7
    _crafting_table(s, left, top, inv=inv)
    _container_buttons(s, left, top, 176)
    query = "laiton" if li else "brass"
    found = [i for i in _mod_items() if query in _fold(_name(i, li)) and _icon(G, i) is not None]
    box, spots = _panel(s, left + 176, query, found[:box_cells()], 0, max(1, -(-len(found) // box_cells())),
                        hover="brasshaven:brass_wrench")
    sx, sy = spots.get("brasshaven:brass_wrench", (box[0] + 20, box[1] + 30))
    s.tooltip(sx + 9, sy + 8, [(_name("brasshaven:brass_wrench", li), G.hexc("FFFFFF")),
                              (("Maintiens Z : page du manuel" if li else "Hold W: manual page"), G.hexc("00AAAA")),
                              (s.t("gui.brasshaven.recipes.tooltip", "R", "U"), G.hexc("AAAAAA"))])
    s.save("recipes_panel" + ("" if li else "_en"))


def box_cells():
    left = (SW - 176) // 2
    return min(9, cols_for(SW - 4 - (left + 176 + 4))) * min(16, rows_for(SH - 8))


def _window(s, title):
    G = s.G
    left, top = (SW - W) // 2, (SH - H - 5 - 13) // 2 + 5
    s.m.nine("panel", left, top, W, H, 9)
    tw = max(90, s.guide.text_width(title, True) + 24)
    s.m.nine("title_plate", left + (W - tw) // 2, top - 5, tw, 18, 6)
    s.text(title, left + W // 2, top, G.PLATE_INK, shadow=False, center=True, bold=True)
    return left, top


def _header(s, left, top, rid, other_label, other_count, tabs, sel, tab_text, manual=True, back=False):
    G = s.G
    s.m.nine("inset", left + 10, top + 14, 20, 20, 4)
    s.item(rid, left + 12, top + 16)
    bw = max(60, s.guide.text_width(other_label) + 12)
    bx = left + W - 10 - 18 - 2 - 18 - 4 - bw
    name_w = bx - (left + 35) - 4
    s.text(s.clip(_name(rid, s.li), name_w), left + 35, top + 15, G.INK, shadow=False)
    s.text(s.clip("Brasshaven" if rid.startswith("brasshaven") else "Minecraft", name_w), left + 35, top + 25, G.INK_SOFT,
           shadow=False)
    s.button(bx, top + 15, bw, 18, other_label, disabled=other_count == 0)
    s.button(left + W - 10 - 18 - 2 - 18, top + 15, 18, 18, None, glyph="book", disabled=not manual)
    s.button(left + W - 10 - 18, top + 15, 18, 18, None, glyph="back", disabled=not back)
    for i, station in enumerate(tabs):
        tx = left + 10 + i * (TAB + 2)
        s.m.nine("button_on" if i == sel else "button", tx, top + 38, TAB, 20, 4)
        s.item(station, tx + 3, top + 40)
    tx = left + 10 + len(tabs) * (TAB + 2) + 4
    s.text(s.clip(tab_text, left + W - 10 - tx), tx, top + 44, G.INK, shadow=False)
    s.m.nine("card", left + CARD_X - 2, top + CARD_Y - 2, CARD_W + 4, CARD_H + 4, 4)


def _cells(left, top, cat, n):
    cw, ch = CELLS[cat]
    cols, rows = max(1, CARD_W // cw), max(1, CARD_H // ch)
    ox = left + CARD_X + (CARD_W - cols * cw) // 2
    oy = top + CARD_Y + (CARD_H - rows * ch) // 2
    return [(ox + (i % cols) * cw, oy + (i // cols) * ch) for i in range(min(n, cols * rows))], cols * rows


def _slot(s, x, y, rid, red=False, hover=False):
    s.sprite("recipe/slot", x, y)
    if rid:
        s.item(rid, x + 1, y + 1)
    if red:
        s.veil(x + 1, y + 1, 16, 16, (0xE0, 0x48, 0x3B, 0x80))
    if hover:
        s.veil(x + 1, y + 1, 16, 16, (255, 245, 220, 80))


def _draw_recipe(s, cat, x, y, r, missing=(), plus=None, plus_hover=False):
    """One recipe cell like RecipeScreen.drawRecipe; plus: None (no button), True / False (all there / some missing)."""
    _c, w, h, ins, out, count, cook = r
    if cat == "crafting":
        for i in range(9):
            col, row = i % 3, i // 3
            if w:
                k = row * w + col if col < w and row < h else -1
            else:
                k = i if i < len(ins) else -1
            _slot(s, x + 4 + col * 18, y + 4 + row * 18, ins[k] if k >= 0 else None, red=k in missing)
        s.sprite("recipe/arrow", x + 62, y + 23)
        if not w:
            s.sprite("recipe/shapeless", x + 67, y + 8)
        s.sprite("recipe/slot_big", x + 90, y + 18)
        s.item(out, x + 95, y + 23, count)
        if plus is not None:
            s.m.nine("button_small_hover" if plus_hover else "button_small", x + 120, y + 25, 12, 12, 3)
            s.sprite("glyph/plus" if plus else "glyph/plus_missing", x + 121, y + 26)
    else:
        _slot(s, x + 4, y + 2, ins[0], red=0 in missing)
        s.sprite("recipe/flame", x + 6, y + 22)
        s.sprite("recipe/arrow", x + 28, y + 8)
        s.sprite("recipe/slot_big", x + 56, y + 3)
        s.item(out, x + 61, y + 8, count)
        secs, xp = cook
        sec = str(secs // 20) if secs % 20 == 0 else f"{secs / 20:.1f}"
        xps = f"{xp:.2f}".rstrip("0").rstrip(".")
        if s.li:
            sec, xps = sec.replace(".", ","), xps.replace(".", ",")
        s.text(s.t("gui.brasshaven.recipes.cook", sec, xps), x + 26, y + 29, s.G.INK_SOFT, shadow=False)
        if plus is not None:
            s.m.nine("button_small", x + 86, y + 10, 12, 12, 3)
            s.sprite("glyph/plus" if plus else "glyph/plus_missing", x + 87, y + 11)


def _footer(s, left, top, page, pages):
    G = s.G
    s.button(left + 10, top + H - 24, 40, 16, "<", disabled=page == 0)
    s.button(left + W - 50, top + H - 24, 40, 16, ">", disabled=page >= pages - 1)
    s.text(s.t("gui.brasshaven.recipes.page", page + 1, pages), left + W // 2, top + H - 20, G.INK_SOFT, shadow=False, center=True)
    s.text(s.t("gui.brasshaven.recipes.keys", "R", "U"), left + W // 2, top + H + 4, G.CREAM, center=True)


def mockup_view(G, li):
    """The Brass Ingot's recipes, opened from a crafting table (the "+" buttons), the zinc missing."""
    s = Shot(G, li)
    left, top = _window(s, s.t("gui.brasshaven.recipes.recipes"))
    rs = [_recipe(r) for r in ("brass_ingot_from_alloy", "brass_ingot_from_block", "brass_ingot_from_nuggets")]
    _header(s, left, top, "brasshaven:brass_ingot", s.t("gui.brasshaven.recipes.to_uses", 40), 40, ["minecraft:crafting_table"], 0,
            s.t("gui.brasshaven.recipes.tab", s.t("gui.brasshaven.recipes.cat.crafting"), len(rs)))
    spots, _per = _cells(left, top, "crafting", len(rs))
    missing = [{3}, {0}, set()]  # no zinc; no brass block; nuggets: all there
    for (x, y), r, m in zip(spots, rs, missing):
        _draw_recipe(s, "crafting", x, y, r, missing=m, plus=not m, plus_hover=r is rs[0])
    _footer(s, left, top, 0, 1)
    x, y = spots[0]
    s.tooltip(x + 126, y + 31, [(s.t("gui.brasshaven.recipes.fill"), G.hexc("FFFFFF")),
                                (s.t("gui.brasshaven.recipes.fill.tip"), G.hexc("AAAAAA")),
                                (s.t("gui.brasshaven.recipes.fill.max"), G.hexc("AAAAAA")),
                                (s.t("gui.brasshaven.recipes.fill.missing"), G.hexc("FF5555")),
                                ("- " + _name("brasshaven:zinc_ingot", li), G.hexc("FF5555")),
                                (s.t("gui.brasshaven.recipes.fill.ghost"), G.hexc("AAAAAA"))])
    s.save("recipes_view" + ("" if li else "_en"))


def mockup_uses(G, li):
    """What the Brass Ingot is used for: a page of crafting recipes, back to the previous item possible."""
    s = Shot(G, li)
    left, top = _window(s, s.t("gui.brasshaven.recipes.uses"))
    rs = [_recipe(n) for n in ("brass_wrench", "auto_harvester", "brass_axe", "chisel_table")]
    _header(s, left, top, "brasshaven:brass_ingot", s.t("gui.brasshaven.recipes.to_recipes", 3), 3,
            ["minecraft:crafting_table"], 0, s.t("gui.brasshaven.recipes.tab", s.t("gui.brasshaven.recipes.cat.crafting"), 37),
            back=True)
    spots, _per = _cells(left, top, "crafting", len(rs))
    for (x, y), r in zip(spots, rs):
        _draw_recipe(s, "crafting", x, y, r)
    _footer(s, left, top, 0, 10)
    s.save("recipes_uses" + ("" if li else "_en"))


def mockup_furnace(G, li):
    """The Zinc Ingot's recipes on the furnace tab: input, flame, arrow, result, time and experience."""
    s = Shot(G, li)
    left, top = _window(s, s.t("gui.brasshaven.recipes.recipes"))
    rs = [_recipe(n) for n in ("zinc_ingot_from_smelting", "zinc_ingot_from_zinc_ore_from_smelting",
                               "zinc_ingot_from_deepslate_zinc_ore_from_smelting")]
    _header(s, left, top, "brasshaven:zinc_ingot", s.t("gui.brasshaven.recipes.to_uses", 6), 6,
            ["minecraft:crafting_table", "minecraft:furnace", "minecraft:blast_furnace"], 1,
            s.t("gui.brasshaven.recipes.tab", s.t("gui.brasshaven.recipes.cat.smelting"), len(rs)))
    spots, _per = _cells(left, top, "smelting", len(rs))
    for (x, y), r in zip(spots, rs):
        _draw_recipe(s, "smelting", x, y, r)
    _footer(s, left, top, 0, 1)
    s.save("recipes_furnace" + ("" if li else "_en"))


def mockups(G):
    for li in (1, 0):
        mockup_panel(G, li)
        mockup_view(G, li)
        mockup_uses(G, li)
        mockup_furnace(G, li)

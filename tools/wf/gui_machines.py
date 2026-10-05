"""Machine screens (com.brasshaven.client.gui.MachineScreen): their GUI sprites and the --mockup previews.

Called from tools/gen_gui.py with that module as ``G`` (Sprite, palette, nine-slice and mockup helpers), so the
machine widgets share the brass / iron / parchment theme. The mockups mirror MachineMenu / MachineScreen's layout
constants and draw text on Minecraft's glyph advances (wf.guide.text_width), so what fits here fits in game.
"""
import math
import os

# ---- layout: keep in sync with MachineMenu.java / MachineScreen.java ------------------------------------------
W = 252
STATUS_Y = 36
ROW_Y0 = 55
ROW_H = 20
CX = 66
BUF_X = W - 10 - 54
BUF_Y = 67
INV_X = (W - 162) // 2
FILTER_X = CX + 22
ROWS = {"HARVESTER": 4, "VACUUM": 4, "TIMER": 4, "SPRINKLER": 2}
HAS_INV = {"HARVESTER", "VACUUM", "BREAKER", "PLACER"}


def rows(kind):
    return ROWS.get(kind, 3)


def row_y(i):
    return ROW_Y0 + i * ROW_H


def content_bottom(kind):
    r = row_y(rows(kind))
    return max(r, BUF_Y + 54) if kind in HAS_INV else r


def inv_y(kind):
    return content_bottom(kind) + 8


def height(kind):
    return inv_y(kind) + 76 + 7 if kind in HAS_INV else content_bottom(kind) + 5


# ---- sprites ------------------------------------------------------------------------------------------------
def _mask_icon(G, name, mask, fill, outline=None, size=12, extra=None):
    """Icon from a set of (x, y) -> colour, with a 1 px soot outline around the shape (4-neighbourhood)."""
    s = G.Sprite(size, size)
    outline = outline or G.SOOT
    for (x, y) in list(mask):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in mask and 0 <= p[0] < size and 0 <= p[1] < size:
                s.set(p[0], p[1], outline)
    for (x, y), c in mask.items():
        s.set(x, y, c if c is not None else fill)
    for (x, y), c in (extra or {}).items():
        s.set(x, y, c)
    s.save(name)


def _art(G, name, rows_, colors, size=12):
    s = G.Sprite(size, size)
    for y, row in enumerate(rows_):
        for x, ch in enumerate(row):
            if ch in colors:
                s.set(x, y, colors[ch])
    s.save(name)


def buttons(G):
    """Selected (lit) and hovered-selected option buttons: dark iron plate with a gold rim. 40x20, border 4."""
    for name, rim, top, bottom in (("button_on", G.hexc("F6C343"), G.IRON_LT, G.IRON),
                                   ("button_on_hover", G.hexc("FFE08A"), G.hexc("4A3F38"), G.IRON_LT)):
        s = G.Sprite(40, 20)
        for y in range(20):
            c = G.mix(top, bottom, y / 19)
            for x in range(40):
                s.set(x, y, c)
        s.frame(0, 0, 39, 19, G.SOOT)
        s.frame(1, 1, 38, 18, rim)
        s.bevel(2, 2, 37, 17, G.SOOT, G.mix(bottom, rim, 0.25))
        s.save(name, nine=4)


def toggles(G):
    """Brass lever switch 26x14: knob left and a dark lamp (off), knob right on a lit green groove (on)."""
    for name, on, hover in (("toggle_off", False, False), ("toggle_off_hover", False, True),
                            ("toggle_on", True, False), ("toggle_on_hover", True, True)):
        s = G.Sprite(26, 14)
        s.rect(0, 0, 25, 13, G.SOOT)
        groove_hi, groove_lo = (G.hexc("7CE35A"), G.hexc("2F8A2A")) if on else (G.IRON_LT, G.IRON_DK)
        for y in range(1, 13):
            c = G.mix(groove_lo, groove_hi, 0.35 + 0.4 * (y / 12)) if on else G.mix(G.IRON_DK, G.IRON, y / 12)
            for x in range(1, 25):
                s.set(x, y, c)
        s.bevel(1, 1, 24, 12, G.SOOT, G.mix(groove_hi, G.IRON_LT, 0.5))
        kx = 13 if on else 1
        hi = G.BRASS_HI if hover else G.mix(G.BRASS_HI, G.BRASS_LT, 0.5)
        for y in range(1, 13):
            c = G.mix(hi, G.BRASS_DK, (y - 1) / 11)
            for x in range(kx, kx + 12):
                s.set(x, y, c)
        s.frame(kx, 1, kx + 11, 12, G.SOOT)
        s.bevel(kx + 1, 2, kx + 10, 11, G.mix(hi, (255, 255, 255, 255), 0.3), G.BRASS_SH)
        for gx in (kx + 4, kx + 7):  # grip
            for gy in range(4, 10):
                s.set(gx, gy, G.BRASS_DK)
        lamp = 5 if on else 19
        lc = G.hexc("D8FFC8") if on else G.hexc("5A1E1A")
        s.rect(lamp, 5, lamp + 2, 8, lc)
        if on:
            s.set(lamp + 1, 6, (255, 255, 255, 255))
        s.save(name)


def slider(G):
    t = G.Sprite(16, 6)
    t.rect(0, 0, 15, 5, G.IRON_DK)
    t.bevel(0, 0, 15, 5, G.SOOT, G.IRON_LT)
    t.rect(1, 2, 14, 3, G.hexc("1F1915"))
    t.save("slider_track", nine=2)
    for name, hi in (("slider_knob", G.BRASS_LT), ("slider_knob_hover", G.BRASS_HI)):
        k = G.Sprite(8, 14)
        for y in range(14):
            c = G.mix(hi, G.BRASS_DK, y / 13)
            for x in range(8):
                k.set(x, y, c)
        k.frame(0, 0, 7, 13, G.SOOT)
        k.bevel(1, 1, 6, 12, G.mix(hi, (255, 255, 255, 255), 0.35), G.BRASS_SH)
        for y in (5, 7, 9):
            k.set(3, y, G.BRASS_SH)
            k.set(4, y, G.BRASS_SH)
        k.save(name)


def swatch(G):
    """Frame drawn over a 16x16 dye colour fill: soot rim, glass highlight top-left, shade bottom-right."""
    s = G.Sprite(16, 16)
    s.frame(0, 0, 15, 15, G.SOOT)
    s.bevel(1, 1, 14, 14, (255, 255, 255, 90), (0, 0, 0, 90))
    s.set(3, 3, (255, 255, 255, 150))
    s.set(4, 3, (255, 255, 255, 110))
    s.set(3, 4, (255, 255, 255, 110))
    s.save("swatch_frame")


def lamps(G):
    for name, core, rim in (("lamp_green", "A6F07A", "2F8A2A"), ("lamp_amber", "FFD27A", "B07D1A"),
                            ("lamp_red", "FF7A6A", "8E1E1E"), ("lamp_off", "6B625A", "2B2320")):
        s = G.Sprite(7, 7)
        c, r = G.hexc(core), G.hexc(rim)
        for y in range(7):
            for x in range(7):
                d = math.hypot(x - 3, y - 3)
                if d <= 3.2:
                    s.set(x, y, r if d > 2.2 else c)
        s.set(2, 2, (255, 255, 255, 230))
        s.rect(0, 0, 0, 0, (0, 0, 0, 0))
        s.save(name)


def icons(G):
    o = G.SOOT
    cream = G.hexc("F3E3C0")
    gold = G.hexc("F6C343")
    # show area: gold corner brackets of a box, like a structure block outline
    m = {}
    for (x0, y0, dx, dy) in ((1, 1, 1, 1), (10, 1, -1, 1), (1, 10, 1, -1), (10, 10, -1, -1)):
        for i in range(3):
            m[(x0 + dx * i, y0)] = gold
            m[(x0, y0 + dy * i)] = gold
    m[(5, 5)] = m[(6, 5)] = m[(5, 6)] = m[(6, 6)] = G.hexc("FFF4B0")
    _mask_icon(G, "machine/show_area", m, gold)
    # redstone modes: power symbol (always), lit torch (with signal), unlit torch (without signal)
    m = {}
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - 5.5, y - 6.5)
            if 3.3 <= d <= 4.6 and not (abs(x - 5.5) <= 1.5 and y < 6):
                m[(x, y)] = cream
    for y in range(1, 7):
        m[(5, y)] = m[(6, y)] = cream
    _mask_icon(G, "machine/rs_always", m, cream)
    for name, lit in (("machine/rs_high", True), ("machine/rs_low", False)):
        m = {}
        for y in range(5, 11):
            m[(5, y)] = G.hexc("8A6236")
            m[(6, y)] = G.hexc("6B4A26")
        head = (G.hexc("FF3B2E"), G.hexc("B3120C")) if lit else (G.hexc("5A2A26"), G.hexc("3A1A18"))
        for y in range(2, 5):
            for x in range(4, 8):
                m[(x, y)] = head[0] if (x + y) % 3 else head[1]
        if lit:
            m[(5, 2)] = G.hexc("FFD0B0")
        extra = {}
        if lit:
            for (x, y) in ((2, 1), (9, 1), (1, 4), (10, 4), (5, 0), (6, 0)):
                extra[(x, y)] = G.hexc("FF6A4A", 170)
        _mask_icon(G, name, m, cream, extra=extra)
    # output directions
    arrow = ["....oo....", "...owwo...", "..owwwwo..", ".owwwwwwo.", "oooowwoooo", "...owwo...",
             "...owwo...", "...owwo...", "...owwo...", "...oooo..."]
    up = ["." + r + "." for r in arrow] + ["." * 12, "." * 12]
    _art(G, "machine/dir_up", [r for r in up], {"o": o, "w": cream})
    down = ["." * 12] + ["." + r + "." for r in reversed(arrow)] + ["." * 12]
    _art(G, "machine/dir_down", down, {"o": o, "w": cream})
    _art(G, "machine/dir_auto", [
        ".....oo.....",
        "....owwo....",
        "...owwwwo...",
        "..o.owwo.o..",
        ".owo.oo.owo.",
        "owwwo..owwwo",
        "owwwo..owwwo",
        ".owo.oo.owo.",
        "..o.owwo.o..",
        "...owwwwo...",
        "....owwo....",
        ".....oo.....",
    ], {"o": o, "w": cream})
    _art(G, "machine/dir_keep", [
        "............",
        ".oooooooooo.",
        ".obbbbbbbbo.",
        ".obhhhhhhbo.",
        ".oooooooooo.",
        ".obbbggbbbo.",
        ".obbbggbbbo.",
        ".obbbbbbbbo.",
        ".obbbbbbbbo.",
        ".odddddddddo"[:12],
        ".oooooooooo.",
        "............",
    ], {"o": o, "b": G.BRASS, "h": G.BRASS_HI, "d": G.BRASS_DK, "g": G.hexc("2B1B0C")})
    # filter modes
    _art(G, "machine/filter_allow", [
        "............",
        "..........o.",
        ".........ogo",
        "........ogdo",
        ".o.....ogdo.",
        "ogo...ogdo..",
        "odgo.ogdo...",
        ".odgogdo....",
        "..odgdo.....",
        "...odo......",
        "....o.......",
        "............",
    ], {"o": o, "g": G.hexc("7CE35A"), "d": G.hexc("2F8A2A")})
    m = {}
    for y in range(12):
        for x in range(12):
            d = math.hypot(x - 5.5, y - 5.5)
            if 3.4 <= d <= 5.0:
                m[(x, y)] = G.hexc("E0483B")
    for i in range(2, 10):
        m[(i, i)] = G.hexc("E0483B")
        m[(i + 1, i)] = G.hexc("B3120C")
    _mask_icon(G, "machine/filter_deny", m, G.hexc("E0483B"))
    # detector targets
    _art(G, "machine/target_players", [
        "............",
        ".oooooooooo.",
        ".ohhhhhhhho.",
        ".ohhhhhhhho.",
        ".ohssssssho.",
        ".osssssssso.",
        ".owbsssswbo.",
        ".osssnnssso.",
        ".ossmmmmsso.",
        ".osssssssso.",
        ".oooooooooo.",
        "............",
    ], {"o": o, "h": G.hexc("4A2F1A"), "s": G.hexc("C99A72"), "w": G.hexc("F4F1E8"), "b": G.hexc("4A60B0"),
        "n": G.hexc("9A6A4A"), "m": G.hexc("6B3A2A")})
    _art(G, "machine/target_monsters", [
        "............",
        ".oooooooooo.",
        ".oggGggGggo.",
        ".oGggggggGo.",
        ".okkggggkko.",
        ".okkgGggkko.",
        ".ogggkkgggo.",
        ".oggkkkkggo.",
        ".oggkkkkggo.",
        ".oGgkggkgGo.",
        ".oooooooooo.",
        "............",
    ], {"o": o, "g": G.hexc("5FBF4A"), "G": G.hexc("3E8A30"), "k": G.hexc("101010")})
    _art(G, "machine/target_animals", [
        "............",
        ".oooooooooo.",
        ".oppppppppo.",
        ".oppppppppo.",
        ".okwppppwko.",
        ".oppppppppo.",
        ".oppnnnnppo.",
        ".oppndndppo.",
        ".oppnnnnppo.",
        ".oppppppppo.",
        ".oooooooooo.",
        "............",
    ], {"o": o, "p": G.hexc("F0A3A3"), "n": G.hexc("E07A86"), "d": G.hexc("8E3A46"), "k": G.hexc("101010"),
        "w": G.hexc("F4F1E8")})
    _art(G, "machine/target_items", [
        "............",
        "....oooo....",
        "...ohhcco...",
        "..ohhccccо..".replace("о", "o"),
        ".oohcccccoo.",
        ".ocooooooco.",
        "..occcccdo..",
        "...occcdo...",
        "....ocdo....",
        ".....oo.....",
        "............",
        "............",
    ], {"o": o, "h": G.hexc("E8FFFF"), "c": G.hexc("5FE0D8"), "d": G.hexc("2A8A86")})
    _art(G, "machine/target_living", [
        "............",
        "............",
        "..ooo..ooo..",
        ".ohhrooorro.",
        ".ohrrrrrrro.",
        ".orrrrrrrdo.",
        "..orrrrrdo..",
        "...orrrdo...",
        "....ordo....",
        ".....oo.....",
        "............",
        "............",
    ], {"o": o, "h": G.hexc("FFB0A8"), "r": G.hexc("E0483B"), "d": G.hexc("8E1E1E")})


def sprites(G):
    buttons(G)
    toggles(G)
    slider(G)
    swatch(G)
    lamps(G)
    icons(G)


# ---- mockups ------------------------------------------------------------------------------------------------


class Texts:
    """The texts of wf.machines in one language (li 0 = en, 1 = fr)."""

    def __init__(self, li):
        from . import machines
        self.M, self.li = machines, li

    def gui(self, key, *args):
        s = self.M.GUI[key][self.li]
        return s % args if args else s

    def lab(self, key):
        return self.M.LABELS[key][0][self.li]

    def stat(self, key, *args):
        s = self.M.STATUS[key][self.li]
        return s % args if args else s

    def secs(self, ticks):
        n = str(ticks // 20) if ticks % 20 == 0 else f"{ticks / 20:.1f}".replace(".", self.gui("decimal"))
        return self.gui("seconds", n)

    def clip(self, s, width):
        from .guide import text_width
        if text_width(s) <= width:
            return s
        while s and text_width(s + "...") > width:
            s = s[:-1]
        return s + "..."


# ---- mockups ------------------------------------------------------------------------------------------------
DYES = ["F9FFFE", "F9801D", "C74EBD", "3AB3DA", "FED83D", "80C71F", "F38BAA", "474F52", "9D9D97", "169C9C",
        "8932B8", "3C44AA", "835432", "5E7C16", "B02E26", "1D1D21"]
INK_SOFT = (0x4A, 0x35, 0x20, 255)  # WfGui.INK_SOFT


class Screen:
    """One machine screen at GUI scale 1, upscaled 3x, with the texts of wf.machines in one language (li 0 = en,
    1 = fr), drawn on Minecraft's glyph advances like MachineScreen.java."""

    def __init__(self, G, kind, li, status, lamp, icon=None):
        status = status(Texts(li)) if callable(status) else status
        from . import guide, machines
        self.G, self.guide, self.M, self.kind, self.li = G, guide, machines, kind, li
        key = kind.lower()
        mid = [k for k, m in machines.MACHINES.items() if m["kind"] == kind][0]
        title = machines.MACHINES[mid]["fr" if li else "en"]
        self.h = height(kind)
        self.m = G.Mock(W + 40, self.h + 40)
        self.ox, self.oy = 20, 22
        self.texts = []
        m, ox, oy = self.m, self.ox, self.oy
        m.nine("panel", ox, oy, W, self.h, 9)
        tw = max(90, guide.text_width(title, True) + 24)
        m.nine("title_plate", ox + (W - tw) // 2, oy - 5, tw, 18, 6)
        self.text(title, W // 2 - guide.text_width(title, True) // 2, 0, G.PLATE_INK, False, bold=True)
        m.nine("inset", ox + 10, oy + 14, 20, 20, 4)
        self.item(icon or _tex(mid + "_front"), 12, 16)
        desc = machines.WHAT[key][0][li]
        lines = guide.wrap(desc, W - 36 - 10)[:2]
        y = 16 if len(lines) > 1 else 20
        for line in lines:
            self.text(line, 36, y, G.INK, False)
            y += 9
        m.nine("inset", ox + 10, oy + STATUS_Y, W - 20, 14, 4)
        self.icon("lamp_" + lamp, 15, STATUS_Y + 4)
        self.text(self.clip(status, W - 20 - 22), 25, STATUS_Y + 3, G.CREAM, True)
        if kind in HAS_INV:
            self.text(self.clip(self.gui("stored"), 40), BUF_X, ROW_Y0 + 1, INK_SOFT, False)
            self.button(BUF_X + 54 - 12, ROW_Y0 - 1, 12, 12, icon="glyph/take")
            for i in range(9):
                self.slot(BUF_X + (i % 3) * 18, BUF_Y + (i // 3) * 18)
            iy = inv_y(kind)
            m.d.line((ox + 10, oy + iy - 5, ox + W - 11, oy + iy - 5), fill=G.hexc("B79C6C"))
            m.d.line((ox + 10, oy + iy - 4, ox + W - 11, oy + iy - 4), fill=G.hexc("F0E2C0"))
            for r in range(3):
                for c in range(9):
                    self.slot(INV_X + c * 18, iy + r * 18)
            for c in range(9):
                self.slot(INV_X + c * 18, iy + 58)

    # texts of wf.machines in this screen's language
    def gui(self, key, *args):
        s = self.M.GUI[key][self.li]
        return s % args if args else s

    def lab(self, key):
        return self.M.LABELS[key][0][self.li]

    def stat(self, key, *args):
        s = self.M.STATUS[key][self.li]
        return s % args if args else s

    def secs(self, ticks):
        n = str(ticks // 20) if ticks % 20 == 0 else f"{ticks / 20:.1f}".replace(".", self.gui("decimal"))
        return self.gui("seconds", n)

    def clip(self, s, width):
        if self.guide.text_width(s) <= width:
            return s
        while s and self.guide.text_width(s + "...") > width:
            s = s[:-1]
        return s + "..."

    def text(self, s, x, y, c, shadow=True, bold=False):
        self.texts.append((self.ox + x, self.oy + y, s, c, shadow, bold))

    def label(self, row, key):
        self.text(self.clip(self.lab(key), CX - 10 - 4), 10, row_y(row) + 5, self.G.INK, False)

    def slot(self, x, y, item=None):
        self.m.nine("inset", self.ox + x, self.oy + y, 18, 18, 4)
        if item is not None:
            self.item(item, x + 1, y + 1)

    def item(self, src, x, y):
        G = self.G
        if src is None:
            return
        if isinstance(src, str):
            if not os.path.exists(src):
                return
            src = G.Image.open(src).convert("RGBA").crop((0, 0, 16, 16))
        self.m.im.alpha_composite(src, (self.ox + x, self.oy + y))

    def button(self, x, y, w, h, label=None, icon=None, on=False, hover=False, disabled=False, icon_size=None):
        G = self.G
        sprite = ("button_on_hover" if hover else "button_on") if on else "button_disabled" if disabled else \
            "button_hover" if hover else "button"
        self.m.nine(sprite, self.ox + x, self.oy + y, w, h, 4)
        iw = 0
        if icon:
            im = G.Image.open(G.sp(icon)).convert("RGBA")
            if icon_size and im.width != icon_size:
                im = im.resize((icon_size, icon_size), G.Image.NEAREST)
            iw = im.width
        tw = self.guide.text_width(label) if label else 0
        cw = iw + (2 if iw and label else 0) + tw
        cx = x + (w - cw + 1) // 2
        if icon:
            self.m.im.alpha_composite(im, (self.ox + cx, self.oy + y + (h - im.height) // 2))
            cx += iw + 2
        if label:
            c = G.hexc("F6C343") if on else G.hexc("C9C0B4") if disabled else G.hexc("FFFFFF")
            self.text(label, cx, y + (h - 8) // 2, c, True)
        return x + w

    def toggle(self, x, y, on, hover=False):
        self.icon(("toggle_on" if on else "toggle_off") + ("_hover" if hover else ""), x, y)

    def icon(self, name, x, y):
        G = self.G
        self.m.im.alpha_composite(G.Image.open(G.sp(name)).convert("RGBA"), (self.ox + x, self.oy + y))

    def well_lamp(self, row, on):
        x = CX + 3 * 20 + 2
        self.m.nine("inset", self.ox + x, self.oy + row_y(row), 18, 18, 4)
        self.icon("lamp_red" if on else "lamp_off", x + 5, row_y(row) + 5)
        if self.kind not in HAS_INV:
            self.text(self.gui("input_on" if on else "input_off"), x + 22, row_y(row) + 5, INK_SOFT, False)

    def tooltip(self, x, y, lines):
        """Vanilla-style tooltip box (near-black with a violet rim), first line white."""
        G = self.G
        w = max(self.guide.text_width(s) for s in lines) + 6
        h = len(lines) * 10 + 4
        X, Y = self.ox + x, self.oy + y
        d = self.m.d
        d.rectangle((X - 1, Y, X + w, Y + h - 1), fill=(16, 0, 16, 240))
        d.rectangle((X, Y - 1, X + w - 1, Y + h), fill=(16, 0, 16, 240))
        d.rectangle((X, Y, X + w - 1, Y + h - 1), outline=(80, 0, 255, 120))
        for i, s in enumerate(lines):
            self.text(s, x + 3, y + 3 + i * 10, G.hexc("FFFFFF") if i == 0 else G.hexc("A8A8A8"), True)

    def save(self, name):
        G = self.G
        os.makedirs(G.PREVIEW, exist_ok=True)
        G.render_texts(self.m.im, self.texts, 3).save(os.path.join(G.PREVIEW, name + ".png"))


def _tex(name):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    p = os.path.join(root, "src/main/resources/assets/brasshaven/textures/block", name + ".png")
    return p if os.path.exists(p) else None


def _segments(sc, row, labels, selected, x=CX, icons=False, disabled=()):
    """Option buttons like MachineScreen.choice(): text ones as wide as their label + 10, 2 px apart."""
    y = row_y(row)
    for i, lab in enumerate(labels):
        w = 18 if icons else max(18, sc.guide.text_width(lab) + 10)
        sc.button(x, y, w, 18, None if icons else lab, lab if icons else None, on=i == selected, disabled=i in disabled)
        x += w + 2
    return x


def _redstone(sc, row, mode, signal):
    sc.label(row, "redstone")
    _segments(sc, row, ["machine/rs_always", "machine/rs_high", "machine/rs_low"], mode, icons=True)
    sc.well_lamp(row, signal)


def _area(sc, row, key, labels, selected, shown):
    sc.label(row, key)
    x = _segments(sc, row, labels, selected)
    sc.button(x + 4, row_y(row), 18, 18, icon="machine/show_area", on=shown)
    return x + 4


def mockups(G, li=1):
    sfx = "" if li else "_en"

    def bag(sc, items):
        for i, it in enumerate(items):
            sc.item(_mc(it), BUF_X + 1 + (i % 3) * 18, BUF_Y + 1 + (i // 3) * 18)

    # Auto-Harvester: area 7x7 shown, replant on, output below (container there), always on
    sc = Screen(G, "HARVESTER", li, lambda t: t.stat("harvesting", 6), "green")
    _area(sc, 0, "area", ["5x5", "7x7", "9x9"], 1, True)
    sc.label(1, "replant")
    sc.toggle(CX, row_y(1) + 2, True)
    sc.text(sc.gui("on"), CX + 30, row_y(1) + 5, G.INK, False)
    sc.label(2, "output")
    x = CX
    letters = [sc.gui(f"output.{d}.letter") for d in ("north", "south", "west", "east")]
    for i, lab in enumerate(["machine/dir_auto", "machine/dir_down", "machine/dir_up"] + letters + ["machine/dir_keep"]):
        ic = lab.startswith("machine/")
        sc.button(x, row_y(2), 14, 18, None if ic else lab, lab if ic else None, on=i == 1)
        if i == 1:  # a chest below: green dot
            X, Y = sc.ox + x + 14, sc.oy + row_y(2)
            sc.m.d.rectangle((X - 5, Y + 1, X - 2, Y + 4), fill=G.SOOT)
            sc.m.d.rectangle((X - 4, Y + 2, X - 3, Y + 3), fill=G.hexc("7CE35A"))
        x += 14
    _redstone(sc, 3, 0, False)
    bag(sc, ["wheat", "wheat", "carrot", "potato", "wheat_seeds"])
    sc.tooltip(CX + 18, row_y(2) + 20, [sc.M.GUI["output.down.tip"][li], sc.gui("output.container")])
    sc.save("machine_harvester" + sfx)

    # Vacuum Hopper: range 5, xp on with 125 stored, allow-list filter, needs a signal (and has one)
    sc = Screen(G, "VACUUM", li, lambda t: t.stat("collecting"), "green")
    _area(sc, 0, "range", ["3", "5", "8"], 1, False)
    sc.label(1, "xp")
    sc.toggle(CX, row_y(1) + 2, True)
    sc.button(CX + 30, row_y(1), BUF_X - 8 - (CX + 30), 18, "125", "icon/xp")
    sc.label(2, "filter")
    sc.button(CX, row_y(2), 18, 18, icon="machine/filter_allow")
    for i in range(5):
        sc.slot(FILTER_X + i * 18, row_y(2), _mc("cobblestone") if i == 0 else _mc("rotten_flesh") if i == 1 else None)
    _redstone(sc, 3, 1, True)
    bag(sc, ["cobblestone", "rotten_flesh", "bone", "string"])
    sc.tooltip(FILTER_X + 40, row_y(2) + 18, [sc.clip(sc.gui("filter.slot.tip"), 200)])
    sc.save("machine_vacuum" + sfx)

    # Block Breaker: oak log in front, chest behind
    log = _mc("oak_log")
    name = "Bûche de chêne" if li else "Oak Log"
    sc = Screen(G, "BREAKER", li, lambda t: t.stat("ready_break", name), "green")
    sc.label(0, "front")
    sc.slot(CX, row_y(0), log)
    sc.text(name, CX + 22, row_y(0) + 5, G.INK, False)
    sc.label(1, "drops")
    sc.text(sc.gui("drops.chest"), CX, row_y(1) + 5, G.INK_GREEN, False)
    sc.label(2, "facing")
    sc.text(sc.gui("dir.north"), CX, row_y(2) + 5, G.INK, False)
    bag(sc, ["oak_log", "oak_sapling", "stick"])
    sc.tooltip(14, row_y(2) + 16, [sc.lab("facing"), sc.M.LABELS["facing"][1][li]])
    sc.save("machine_breaker" + sfx)

    # Block Placer: nothing to place
    sc = Screen(G, "PLACER", li, lambda t: t.stat("no_blocks"), "red")
    sc.label(0, "next")
    sc.slot(CX, row_y(0))
    sc.text(sc.gui("next.none"), CX + 22, row_y(0) + 5, INK_SOFT, False)
    sc.label(1, "source")
    sc.text(sc.gui("source.self"), CX, row_y(1) + 5, INK_SOFT, False)
    sc.label(2, "facing")
    sc.text(sc.gui("dir.east"), CX, row_y(2) + 5, G.INK, False)
    sc.save("machine_placer" + sfx)

    # Sprinkler: 7x7, works without a signal, hovering "show area"
    sc = Screen(G, "SPRINKLER", li, lambda t: t.stat("watering", 14), "green")
    x = _area(sc, 0, "area", ["3x3", "5x5", "7x7"], 2, False)
    sc.button(x, row_y(0), 18, 18, icon="machine/show_area", hover=True)
    _redstone(sc, 1, 2, False)
    sc.tooltip(x - 60, row_y(0) - 22, [sc.gui("show_area"), sc.clip(sc.gui("show_area.tip"), 200)])
    sc.save("machine_sprinkler" + sfx)

    # Redstone Timer: 5 s, 0.2 s pulses, runs with a signal (has one), 3.2 s left
    sc = Screen(G, "TIMER", li, lambda t: t.stat("countdown", t.secs(64)), "green")
    sc.label(0, "interval")
    sw, steps, step = 120, 9, 4
    sc.m.nine("slider_track", sc.ox + CX, sc.oy + row_y(0) + 6, sw, 6, 2)
    for i in range(steps):
        tx = CX + 4 + round(i * (sw - 8) / (steps - 1))
        col = G.hexc("F6C343") if i == step else G.BRASS_DK
        sc.m.d.rectangle((sc.ox + tx, sc.oy + row_y(0) + 14, sc.ox + tx, sc.oy + row_y(0) + 15), fill=col)
    sc.icon("slider_knob", CX + round(step / (steps - 1) * (sw - 8)), row_y(0) + 2)
    sc.text(sc.secs(100), CX + 126, row_y(0) + 5, G.INK, False)
    sc.label(1, "pulse")
    _segments(sc, 1, [sc.secs(t) for t in (2, 4, 10, 20)], 1)
    _redstone(sc, 2, 1, True)
    sc.label(3, "next_pulse")
    bw = W - 10 - CX - 40
    sc.m.nine("bar_back", sc.ox + CX, sc.oy + row_y(3) + 6, bw, 6, 2)
    sc.m.nine("bar_fill", sc.ox + CX + 1, sc.oy + row_y(3) + 7, (bw - 2) * 36 // 100, 4, 1)
    sc.text(sc.secs(64), W - 10 - 34, row_y(3) + 5, G.INK, False)
    sc.save("machine_timer" + sfx)

    # Wireless Transmitter / Receiver on the red channel
    for kind, st, lamp in (("TRANSMITTER", "broadcasting", "green"), ("RECEIVER", "no_transmitter", "amber")):
        sc = Screen(G, kind, li, lambda t: t.stat(st), lamp)
        sel = 14
        sc.label(0, "channel")
        sc.text("Rouge" if li else "Red", 10, row_y(1) + 5, G.INK, False)
        for i in range(16):
            x = CX + (i % 8) * 18
            y = row_y(i // 8) + 1
            X, Y = sc.ox + x, sc.oy + y
            if i == sel:
                sc.m.d.rectangle((X - 2, Y - 2, X + 17, Y + 17), fill=G.hexc("F6C343"))
                sc.m.d.rectangle((X - 1, Y - 1, X + 16, Y + 16), fill=G.hexc("2B1B0C"))
            sc.m.d.rectangle((X, Y, X + 15, Y + 15), fill=G.hexc(DYES[i]))
            sc.icon("swatch_frame", x, y)
        sc.text(sc.gui("channel.shared", 2, 3), 10, row_y(2) + 5, INK_SOFT, False)
        sc.save("machine_" + kind.lower() + sfx)

    # Entity Detector: monsters within 8, normal output, 3 detected
    sc = Screen(G, "DETECTOR", li, lambda t: t.stat("detected", 3), "green")
    sc.label(0, "target")
    _segments(sc, 0, ["machine/target_" + t for t in ("players", "monsters", "animals", "items", "living")], 1, icons=True)
    _area(sc, 1, "range", ["2", "4", "8", "16"], 2, True)
    sc.label(2, "signal")
    x = _segments(sc, 2, [sc.gui("normal"), sc.gui("inverted")], 0)
    sc.icon("lamp_red", x + 2, row_y(2) + 6)
    sc.text(sc.gui("signal_strength", 3), x + 12, row_y(2) + 5, INK_SOFT, False)
    sc.save("machine_detector" + sfx)


_MC = {}


def _mc(name):
    """A vanilla inventory icon (32x32 render, shown at 16x16) from the scratch texture pack, when present (mockups only)."""
    if not _MC:
        import base64
        import io
        import json
        from PIL import Image
        path = ("/tmp/claude-0/-home-user-mode-minecraft/56f1bf77-a458-5793-adc7-375815e90045/scratchpad/mctex/package/dist/"
                "textures/json/26.2.id.json")
        _MC["_"] = None
        if os.path.exists(path):
            for k, v in json.load(open(path))["items"].items():
                data = v.get("texture", "")
                if data.startswith("data:image/png;base64,"):
                    _MC[k.split(":")[1]] = (data, Image, io, base64)
    entry = _MC.get(name)
    if not entry:
        return None
    data, Image, io, base64 = entry
    im = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGBA")
    return im.resize((16, 16), Image.LANCZOS)


def mockup_settings(G, li=1):
    """SettingsScreen.java (Mods > Brasshaven > Config): same window, tabs, rows and controls. settings.png is the
    Display tab, settings_minimap.png the Minimap tab (French; ``li=0`` adds _en versions)."""
    from . import content, guide, machines
    k = "gui.brasshaven.settings."

    def tr(key):
        return content.MESSAGES[key][li]

    # SettingsScreen constants
    w_, row_h, rows_n, first, hint, cx = 360, 20, 7, 42, 12, 124
    h_ = first + rows_n * row_h + hint + 28
    for tab in (0, 1):
        m = G.Mock(w_ + 40, h_ + 40)
        ox, oy = 20, 22
        m.nine("panel", ox, oy, w_, h_, 9)
        title = tr(k + "title")
        tw = max(90, guide.text_width(title, True) + 24)
        m.nine("title_plate", ox + (w_ - tw) // 2, oy - 5, tw, 18, 6)
        m.text(title, ox + w_ // 2, oy, G.PLATE_INK, shadow=False, center=True, bold=True)

        def row_y(i):
            return oy + first + i * row_h

        def choice(x, y, w, h, label, on, icon=None):
            m.nine("button_on" if on else "button", x, y, w, h, 4)
            if icon:
                m.im.alpha_composite(G.Image.open(G.sp(icon)).convert("RGBA"), (x + (w - 12 + 1) // 2, y + (h - 12) // 2))
            else:
                m.text(label, x + (w - guide.text_width(label) + 1) // 2, y + (h - 8) // 2, G.GOLD if on else G.hexc("FFFFFF"))
            return x + w

        def toggle(i, on):
            m.im.alpha_composite(G.Image.open(G.sp("toggle_on" if on else "toggle_off")).convert("RGBA"), (ox + cx, row_y(i) + 2))
            m.text(machines.GUI["on" if on else "off"][li], ox + cx + 30, row_y(i) + 5, G.INK_SOFT, shadow=False)

        tabs = [tr(k + "tab.display"), tr(k + "tab.minimap")]
        tbw = max(80, max(guide.text_width(t) + 16 for t in tabs))
        for i, t in enumerate(tabs):
            choice(ox + w_ // 2 - tbw - 2 + i * (tbw + 4), oy + 17, tbw, 16, t, i == tab)
        names = (["health_bars", "damage_numbers", "quest_tracker", "tips", "keys"] if tab == 0 else
                 ["minimap", "minimap_size", "minimap_corner", "minimap_shape", "minimap_rotate", "minimap_coords",
                  "minimap_opacity"])
        for i, key in enumerate(names):
            m.text(tr(k + key), ox + 12, row_y(i) + 5, G.INK, shadow=False)
        if tab == 0:
            x = ox + cx
            for j, mode in enumerate(["always", "damaged", "never"]):
                lab = tr(k + "health_bars." + mode)
                x = choice(x, row_y(0), max(18, guide.text_width(lab) + 10), 18, lab, j == 1) + 2
            for i, on in ((1, True), (2, True), (3, False)):
                toggle(i, on)
            kb = tr(k + "keys.button")
            choice(ox + cx, row_y(4), max(60, guide.text_width(kb) + 16), 18, kb, False)
        else:
            toggle(0, True)
            x = ox + cx
            for j, size in enumerate(["small", "medium", "large", "xlarge"]):
                lab = tr(k + "minimap_size." + size)
                x = choice(x, row_y(1), max(18, guide.text_width(lab) + 10), 18, lab, j == 1) + 2
            if x + 2 + guide.text_width("160 px") <= ox + w_ - 8:  # the exact size, when there is room
                m.text("68 px", x + 2, row_y(1) + 5, G.INK_SOFT, shadow=False)
            x = ox + cx
            for j, corner in enumerate(["top_left", "top_right", "bottom_left", "bottom_right"]):
                x = choice(x, row_y(2), 22, 18, "", j == 0, icon="glyph/corner_" + corner) + 2
            x = ox + cx
            for j, shape in enumerate(["round", "square"]):
                lab = tr(k + "minimap_shape." + shape)
                x = choice(x, row_y(3), max(18, guide.text_width(lab) + 10), 18, lab, j == 0) + 2
            toggle(4, False)
            toggle(5, True)
            # the stepped slider (WfWidgets.Stepper), 8 steps, at 100 %
            sx, sy, sw = ox + cx, row_y(6), 112
            m.nine("slider_track", sx, sy + 6, sw, 6, 2)
            for s in range(8):
                tx = sx + 4 + round(s * (sw - 8) / 7)
                m.d.rectangle((tx, sy + 14, tx, sy + 15), fill=G.GOLD if s == 7 else G.BRASS_DK)
            m.im.alpha_composite(G.Image.open(G.sp("slider_knob")).convert("RGBA"), (sx + sw - 8, sy + 2))
            m.text("100 %", ox + cx + 118, row_y(6) + 5, G.INK_SOFT, shadow=False)
            keys = tr(k + "minimap.keys").replace("%1$s", "H").replace("%s", "H", 1).replace("%s", "Z" if li == 0 else "W")
            m.text(keys, ox + w_ // 2, row_y(rows_n) + 2, G.INK_SOFT, shadow=False, center=True)
        done = "Terminé" if li else "Done"
        choice(ox + w_ // 2 - 50, oy + h_ - 26, 100, 20, done, False)
        m.save("settings" + ("" if tab == 0 else "_minimap") + ("" if li else "_en"))

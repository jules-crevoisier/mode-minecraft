"""Accessory slots (back, two rings, amulet, belt) shown next to the armour in the player's inventory.

One table drives the item tags (data/brasshaven/tags/item/accessory/<slot>.json, read by
com.brasshaven.accessory.AccessorySlotType), the slot names (fr/en), the empty-slot silhouettes and the side panel
drawn by client/AccessoryClient (GUI-atlas sprites under textures/gui/sprites/accessory/, made by gen_gui.py).

An accessory only works while it is worn in its slot: what it does is written in its tooltip ("Worn: ...").
"""

NS = "brasshaven"

# slot id -> (english, french, how many slots of that kind, items that fit)
SLOTS = {
    "back": ("Back", "Dos", 1, ["brass_glider"]),
    "ring": ("Ring", "Anneau", 2, ["magnet_ring", "arcane_ring"]),
    "amulet": ("Amulet", "Amulette", 1, ["mana_amulet"]),
    "belt": ("Belt", "Ceinture", 1, ["pocket_watch"]),
}

# the order of the slots in the panel (top to bottom), the same as AccessorySlotType.LAYOUT in Java
LAYOUT = ["back", "ring", "ring", "amulet", "belt"]


def slot_of(item_id):
    for sid, (_en, _fr, _n, items) in SLOTS.items():
        if item_id in items:
            return sid
    return None


def tags(write):
    for sid, (_en, _fr, _n, items) in SLOTS.items():
        write(f"{NS}/tags/item/accessory/{sid}.json", {"values": [f"{NS}:{i}" for i in items]})
    # every accessory, whatever its slot (handy for other mods and for /give checks)
    write(f"{NS}/tags/item/accessories.json",
          {"values": [f"#{NS}:accessory/{sid}" for sid in SLOTS]})


def lang():
    en, fr = {}, {}
    for sid, (e, f, _n, _items) in SLOTS.items():
        en[f"tooltip.{NS}.accessory.slot.{sid}"], fr[f"tooltip.{NS}.accessory.slot.{sid}"] = e, f
    en.update({
        f"tooltip.{NS}.accessory": "Accessory · %s slot",
        f"tooltip.{NS}.accessory.worn": "Works only while worn in that slot (next to your armour).",
        f"tooltip.{NS}.accessory.no_stack": "Two identical rings do not add up.",
        f"gui.{NS}.accessory.title": "Accessories",
        f"gui.{NS}.accessory.empty": "%s slot (empty)",
        f"message.{NS}.watch.dusk": "Your pocket watch chimes: night falls soon.",
        f"message.{NS}.watch.dawn": "Your pocket watch chimes: a new day begins.",
    })
    fr.update({
        f"tooltip.{NS}.accessory": "Accessoire · emplacement %s",
        f"tooltip.{NS}.accessory.worn": "N'agit que porté dans cet emplacement (à côté de l'armure).",
        f"tooltip.{NS}.accessory.no_stack": "Deux anneaux identiques ne se cumulent pas.",
        f"gui.{NS}.accessory.title": "Accessoires",
        f"gui.{NS}.accessory.empty": "Emplacement %s (vide)",
        f"message.{NS}.watch.dusk": "Ta montre sonne : la nuit va tomber.",
        f"message.{NS}.watch.dawn": "Ta montre sonne : un nouveau jour se lève.",
    })
    # French slot names inside "emplacement %s" read lower-case
    for sid, (_e, f, _n, _items) in SLOTS.items():
        fr[f"tooltip.{NS}.accessory.slot.{sid}"] = f.lower()
    return en, fr


# ------------------------------------------------------------------ GUI sprites (gen_gui.py calls sprites())
# 16x16 silhouettes for the empty slots, drawn like vanilla's empty armour slots: a soft grey ghost of the item.
SILHOUETTES = {
    "back": [  # the glider seen from behind: a wing on a spine, its harness and control bar
        "................",
        "................",
        ".......oo.......",
        "......offo......",
        ".....offffo.....",
        "....offooffo....",
        "...offfoofffo...",
        "..offffooffffo..",
        ".offfffoofffffo.",
        "oooooooooooooooo",
        "......o..o......",
        "......o..o......",
        "....oooooooo....",
        "................",
        "................",
        "................",
    ],
    "ring": [
        "................",
        "................",
        "......oooo......",
        ".....offffo.....",
        "......oooo......",
        ".....oo..oo.....",
        "....oo....oo....",
        "...oo......oo...",
        "...o........o...",
        "...o........o...",
        "...oo......oo...",
        "....oo....oo....",
        ".....oooooo.....",
        "................",
        "................",
        "................",
    ],
    "amulet": [
        "................",
        "..oo........oo..",
        "...oo......oo...",
        "....oo....oo....",
        ".....oo..oo.....",
        "......oooo......",
        "......offo......",
        ".....offffo.....",
        "....offffffo....",
        "....offffffo....",
        "....offffffo....",
        ".....offffo.....",
        "......offo......",
        ".......oo.......",
        "................",
        "................",
    ],
    "belt": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "oooooooooooooooo",
        "fffffoooooofffff",
        "ffffoffffffoffff",
        "ffffofoooofoffff",
        "ffffoffffffoffff",
        "fffffoooooofffff",
        "oooooooooooooooo",
        "................",
        "................",
        "................",
        "................",
    ],
}


def sprites(g):
    ghost = {"o": (55, 55, 55, 150), "f": (55, 55, 55, 90)}
    for sid, art in SILHOUETTES.items():
        s = g.Sprite(16, 16)
        for y, row in enumerate(art):
            for x, ch in enumerate(row):
                if ch in ghost:
                    s.set(x, y, ghost[ch])
        s.save(f"accessory/{sid}")
    # the vanilla-looking side panel (light grey, bevelled, round black outline) and one 18x18 slot well
    p = g.Sprite(16, 16)
    grey, hi, lo, black = (198, 198, 198, 255), (255, 255, 255, 255), (85, 85, 85, 255), (0, 0, 0, 255)
    p.rect(1, 1, 14, 14, grey)
    for i in range(1, 15):
        p.set(i, 0, black)
        p.set(i, 15, black)
        p.set(0, i, black)
        p.set(15, i, black)
    for i in range(1, 14):
        p.set(i, 1, hi)
        p.set(1, i, hi)
        p.set(i + 1, 14, lo)
        p.set(14, i + 1, lo)
    p.set(2, 2, hi)
    p.set(13, 13, lo)
    p.save("accessory/panel", nine=4)
    s = g.Sprite(18, 18)
    s.rect(0, 0, 17, 17, (139, 139, 139, 255))
    for i in range(0, 17):
        s.set(i, 0, (55, 55, 55, 255))
        s.set(0, i, (55, 55, 55, 255))
    for i in range(1, 18):
        s.set(i, 17, (255, 255, 255, 255))
        s.set(17, i, (255, 255, 255, 255))
    s.save("accessory/slot")


# ------------------------------------------------------------------ manual page (gadgets.guide_pages() adds it)
def guide_page():
    return ("accessories", "brasshaven:magnet_ring", ("Accessories", "Accessoires"), [
        ("Next to your armour, the inventory has five accessory slots: one back, two rings, one amulet and one belt. "
         "Their grey outline shows what goes where. Shift-click an accessory to wear it.",
         "À côté de l'armure, l'inventaire a cinq emplacements d'accessoires : un dos, deux anneaux, une amulette et "
         "une ceinture. Leur silhouette grise montre ce qui va où. Maj + clic sur un accessoire pour le porter."),
        ("An accessory only works while it is worn: back, the Brass Glider; rings, the Magnet Ring and the Arcane Ring "
         "(two identical rings do not add up); amulet, the Mana Amulet; belt, the Pocket Watch (it chimes at dusk and "
         "dawn). Each tooltip names its slot.",
         "Un accessoire n'agit que s'il est porté : dos, le planeur en laiton ; anneaux, l'anneau aimanté et l'anneau "
         "arcanique (deux anneaux identiques ne se cumulent pas) ; amulette, l'amulette de mana ; ceinture, la montre "
         "à gousset (elle sonne au crépuscule et à l'aube). Chaque info-bulle indique son emplacement."),
        ("Worn accessories follow the inventory rules: kept on death with keepInventory, otherwise they go to your "
         "grave with everything else.",
         "Les accessoires portés suivent les règles de l'inventaire : gardés à la mort avec keepInventory, sinon ils "
         "vont dans ta tombe avec le reste."),
    ], ["brasshaven:brass_glider", "brasshaven:magnet_ring", "brasshaven:arcane_ring", "brasshaven:mana_amulet",
        "brasshaven:pocket_watch"])

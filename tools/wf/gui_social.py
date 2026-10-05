"""GUI icons of the multiplayer features (gen_gui.py calls sprites()): company, post, contracts, duels and the eight
emotes of the emote wheel. 16x16 character maps in the theme's palette (soot outline, brass, parchment)."""


def _rows(art):
    return [(r + "." * 16)[:16] for r in art] + ["." * 16] * (16 - len(art))


CROWN = [
    "................",
    "................",
    "................",
    "..o....o....o...",
    ".oyo..oyo..oyo..",
    ".oyyo.oyo.oyyo..",
    ".oyyyooyoooyyo..",
    ".oyyyyyyyyyyyo..",
    ".oyrryyhyyrryo..",
    ".oyyyyyyyyyyyo..",
    ".odddddddddddo..",
    ".ooooooooooooo..",
]
MAIL = [
    "................",
    "................",
    "................",
    ".oooooooooooooo.",
    ".owwwwwwwwwwwwo.",
    ".oowwwwwwwwwwoo.",
    ".owowwwwwwwwowo.",
    ".owwowwwwwwowwo.",
    ".owwwowwwwowwwo.",
    ".owwwwoorrowwwo.",
    ".owwwwwwrrwwwwo.",
    ".owwwwwwwwwwwwo.",
    ".oooooooooooooo.",
]
PARCEL = [
    "................",
    "................",
    "....oooooooo....",
    "...obbbssbbbo...",
    "..obbbbssbbbbo..",
    "..oooooooooooo..",
    "..obbbbssbbbbo..",
    "..obbbbssbbbbo..",
    "..ossssssssss o.",
    "..obbbbssbbbbo..",
    "..obbbbssbbbbo..",
    "..obbbbssbbbbo..",
    "..oooooooooooo..",
]
CONTRACT = [
    "................",
    "..oooooooooooo..",
    ".odppppppppppdo.",
    "..opkkkkkkkkpo..",
    "..oppppppppppo..",
    "..opkkkkkkkppo..",
    "..oppppppppppo..",
    "..opkkkkkkkkpo..",
    "..oppppppppppo..",
    "..opkkkkpprrpo..",
    "..oppppprrrrro..",
    ".odpppppprrrdo..",
    "..oooooooooooo..",
]
DUEL = [
    "................",
    ".o............o.",
    ".oso........oso.",
    "..oso......oso..",
    "...oso....oso...",
    "....oso..oso....",
    ".....osoosoo....",
    "......osso......",
    "......osso......",
    ".....oosoosoo...",
    "...ohhoo..oohho.",
    "...obho....ohbo.",
    "..obbo......obbo",
    "..ooo........ooo",
]
WAVE = [
    "......o.o.o.....",
    ".....oyoyoyo....",
    ".....oyoyoyo.o..",
    ".....oyoyoyooyo.",
    "..o..oyyyyyoyo..",
    ".oyo.oyyyyyyyo..",
    "..oyooyyyyyyyo..",
    "...oyyyyyyyyo...",
    "....oyyyyyyyo...",
    ".....oyyyyyo....",
    "......occco.....",
    "......occco.....",
    "......ooooo.....",
]
BOW = [
    "................",
    ".......oo.......",
    "......ohho......",
    "......ohho......",
    ".......oo.......",
    "......occoooo...",
    "......occcccco..",
    ".......oooooccoo",
    "...........occo.",
    "..........occo..",
    "..........obbo..",
    "..........obbo..",
    "..........obbo..",
    ".........oo.oo..",
]
CHEER = [
    "..g..........g..",
    ".gyg..oo....gyg.",
    "..g..ohho....g..",
    ".o...ohho...o...",
    ".oho..oo...oho..",
    "..ohoocco.oho...",
    "...ohccccoho....",
    ".....occco......",
    ".....occco......",
    ".....obbbo......",
    "....obo.obo.....",
    "....obo.obo.....",
    "....oo...oo.....",
]
CLAP = [
    "................",
    "..g...........g.",
    ".gyg..o...o..gyg",
    "..g..oyo.oyo..g.",
    ".....oyo.oyo....",
    "....oyyooyyo....",
    "....oyyyyyyo....",
    "...oyyyyyyyyo...",
    "...oyyyyyyyyo...",
    "....oyyyyyyo....",
    ".....occcco.....",
    ".....occcco.....",
    ".....oooooo.....",
]
POINT = [
    "................",
    "................",
    "................",
    "....oooooooo....",
    "...oyyyyyyyyooo.",
    "..oyyoooooyyyyyo",
    "..oyyyyyo.oooooo",
    "..oyyyyyo.......",
    "..oyyyyyo.......",
    "..oyyyyo........",
    ".occcoo.........",
    ".occco..........",
    ".ooooo..........",
]
LAUGH = [
    "................",
    ".....oooooo.....",
    "...ooyyyyyyoo...",
    "..oyyyyyyyyyyo..",
    "..oyyoyyyyoyyo..",
    ".oyyoyoyyoyoyyo.",
    ".oyyyyyyyyyyyyo.",
    ".oyyoooooooyyyo.",
    ".oyyowwwwwwoyyo.",
    "..oyyorrrroyyo..",
    "..oyyyoooooyyo..",
    "...ooyyyyyyoo...",
    ".....oooooo.....",
]
THANKS = [
    "................",
    "................",
    "...ooo....ooo...",
    "..ohhro..orrro..",
    ".ohhrrroorrrrro.",
    ".ohrrrrrrrrrrro.",
    ".orrrrrrrrrrrro.",
    "..orrrrrrrrrro..",
    "...orrrrrrrro...",
    "....orrrrrro....",
    ".....orrrro.....",
    "......orro......",
    ".......oo.......",
]
RALLY = [
    "..w.....w.......",
    ".www...www..w...",
    "..w..w..w..www..",
    "....www.....w...",
    ".....w..........",
    "......oooo......",
    ".....oyyyyo.....",
    ".....obbbbo.....",
    "......oyyo......",
    "......oyyo......",
    ".....oyyyyo.....",
    "....oyhhhhyo....",
    "....oyyyyyyo....",
    "....oddddddo....",
    ".....oooooo.....",
]


def sprites(g):
    hexc = g.hexc
    soot = g.SOOT
    brass = {"o": soot, "y": hexc("D9B25E"), "h": hexc("F1D48A"), "d": hexc("7C5A2B"), "b": hexc("B58A45"),
             "r": hexc("E0483B"), "c": hexc("6B3F2A"), "g": hexc("FFF4B0"), "w": hexc("E8EEF2")}
    skin = dict(brass, y=hexc("E8B98A"), h=hexc("F4D2B0"), c=hexc("3F6FB0"), b=hexc("4E3819"))
    g.icon("social_crown", _rows(CROWN), dict(brass, y=hexc("F6C343"), h=hexc("9FE6FF")))
    g.icon("social_mail", _rows(MAIL), {"o": soot, "w": hexc("EBDDBE"), "r": hexc("B0281F")})
    g.icon("social_parcel", _rows([r.replace(" ", "s") for r in PARCEL]), {"o": soot, "b": hexc("A8794A"), "s": hexc("E6D2A0")})
    g.icon("social_contract", _rows(CONTRACT), {"o": soot, "p": hexc("EBDDBE"), "d": hexc("A88D5E"), "k": hexc("6B5638"),
                                                 "r": hexc("B0281F")})
    g.icon("social_duel", _rows(DUEL), {"o": soot, "s": hexc("DCE3EA"), "h": hexc("B58A45"), "b": hexc("6B3F2A")})
    g.icon("emote_wave", _rows(WAVE), skin)
    g.icon("emote_bow", _rows(BOW), skin)
    g.icon("emote_cheer", _rows(CHEER), skin)
    g.icon("emote_clap", _rows(CLAP), skin)
    g.icon("emote_point", _rows(POINT), skin)
    g.icon("emote_laugh", _rows(LAUGH), dict(brass, y=hexc("F6C343"), w=hexc("FFFFFF")))
    g.icon("emote_thanks", _rows(THANKS), {"o": soot, "r": hexc("E0483B"), "h": hexc("FF9A8A")})
    g.icon("emote_rally", _rows(RALLY), dict(brass, w=hexc("F4F1E8")))

"""Multiplayer features (Java: com.wayfarers.social, client.social, registry/ModSocial.java): the Company (parties),
secure trade, the Pneumatic Post, guild contracts, emotes and duels.

One table for the two blocks (names, tooltips, 3D models, textures, recipes, loot, mining tags), the manual pages
and tip cards (guide.py adds them), and every translation of the screens and messages (EN / FR).
"""
from . import texgen_steam as S
from .png import Canvas
from .texgen import mix, mul

NS = "wayfarers"
H4 = ["north", "south", "east", "west"]

# id -> (english, french, tooltip en, tooltip fr)
BLOCKS = {
    "pneumatic_post": ("Pneumatic Post", "Borne pneumatique",
                       "Letters and parcels to any player, even offline. Every post box opens your own inbox.",
                       "Lettres et colis vers n'importe quel joueur, même absent. Chaque borne ouvre ta boîte."),
    "contract_board": ("Contract Board", "Tableau des contrats",
                       "Post a request with an escrowed reward, or deliver goods and get paid at once.",
                       "Publie une demande avec sa récompense en dépôt, ou livre et sois payé aussitôt."),
}
# block-state properties, for validate.py (structure templates)
MOD_STATES = {bid: {"facing": H4} for bid in BLOCKS}
MOD_ITEMS = set(BLOCKS) | {"brass_ingot", "brass_nugget"}

# ------------------------------------------------------------------ textures (gen_textures.py)
PAPER = (232, 218, 184)
INK = (70, 52, 36)
SEAL = (170, 40, 34)
CORK = (150, 108, 66)


def _paper(seed, seal=False, lines=6):
    cv = S.wax(PAPER, seed=seed)
    for i in range(lines):
        y = 3 + i * 2
        x1 = 13 - (seed + i * 3) % 5
        for x in range(3, x1):
            if (x * 7 + i + seed) % 9:
                cv.set(x, y, mix(cv.get(x, y), INK, 0.55))
    for i in range(16):
        cv.set(i, 0, mul(PAPER, 0.85))
        cv.set(0, i, mul(PAPER, 0.9))
        cv.set(15, i, mul(PAPER, 0.8))
        cv.set(i, 15, mul(PAPER, 0.78))
    if seal:
        for y in range(10, 15):
            for x in range(9, 14):
                if (x - 11) ** 2 + (y - 12) ** 2 <= 5:
                    cv.set(x, y, mul(SEAL, 1.1 if (x + y) % 3 else 0.8))
        cv.set(10, 11, mul(SEAL, 1.5))
    return cv


def _cork(seed=91):
    import random
    rng = random.Random(seed)
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            cv.set(x, y, mul(CORK, 1 + rng.uniform(-0.12, 0.12)))
    return cv


def _hatch(seed=92):
    """Copper hatch of the post box: a riveted plate with the dark mail slot and a brass handle."""
    cv = S.smooth_metal(S.COPPER, seed=seed)
    for x in range(3, 13):
        cv.set(x, 5, (24, 18, 16, 255))
        cv.set(x, 6, (40, 30, 26, 255))
        cv.set(x, 4, mul(S.COPPER, 0.6))
        cv.set(x, 7, mul(S.COPPER, 1.3))
    for x in range(6, 10):
        cv.set(x, 11, mul(S.BRASS, 1.3))
        cv.set(x, 12, mul(S.BRASS, 0.8))
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        cv.set(x, y, mul(S.COPPER, 1.5))
        cv.set(x + (1 if x < 8 else -1), y, mul(S.COPPER, 0.6))
    return cv


def _tube(seed=93):
    """Glass of the pneumatic tube, with a brass capsule inside."""
    cv = Canvas(16, 16)
    glass = (170, 220, 230)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            cv.set(x, y, (*mul(glass, 0.7 if edge else 1.0), 150))
    for y in range(5, 11):
        for x in range(4, 12):
            cv.set(x, y, mul(S.BRASS, 1.2 if y == 5 else 0.8 if y == 10 else 1.0))
    for x in range(2, 4):
        cv.set(x, 2, (255, 255, 255, 200))
    return cv


TEXTURES = {
    "social_paper": lambda: _paper(41),
    "social_paper_seal": lambda: _paper(57, seal=True, lines=4),
    "social_cork": _cork,
    "social_hatch": _hatch,
    "social_tube": _tube,
    "social_brass": lambda: S.smooth_metal(S.BRASS, seed=94),
    "social_iron": lambda: S.smooth_metal(S.DARK_IRON, seed=95),
    "social_wood": lambda: S.plain_wood(S.MAHOGANY, seed=96),
}


def textures():
    return {f"block/{name}": fn() for name, fn in TEXTURES.items()}


# ------------------------------------------------------------------ models (gen_assets.py)
# boxes (x0, y0, z0, x1, y1, z1, texture) drawn for a block facing north (its front towards the player at z = 0)
MODELS = {
    "pneumatic_post": [
        (2, 0, 2, 14, 2, 14, "social_iron"),            # plinth
        (4, 2, 4, 12, 13, 12, "social_brass"),          # column
        (4.5, 5, 3.5, 11.5, 11, 4, "social_hatch"),     # the hatch on the front
        (3.5, 12, 3.5, 12.5, 13, 12.5, "social_iron"),  # collar
        (5, 13, 5, 11, 16, 11, "social_tube"),          # glass tube with a capsule
        (12, 7, 7, 14, 9, 9, "social_brass"),           # side pipe
        (13, 2, 7, 15, 9, 9, "social_brass"),
    ],
    "contract_board": [
        (1, 0, 7, 3, 16, 9, "social_wood"),             # posts
        (13, 0, 7, 15, 16, 9, "social_wood"),
        (0, 4, 6.5, 16, 15, 8.5, "social_cork"),        # the board
        (0, 15, 6, 16, 16, 9, "social_brass"),          # brass rail on top
        (2, 9, 6, 7, 14, 6.5, "social_paper"),          # notices
        (8, 8, 6, 14, 14, 6.5, "social_paper_seal"),
        (3, 5, 6, 8, 8.5, 6.5, "social_paper"),
        (9.5, 5, 6, 13, 7.5, 6.5, "social_paper"),
    ],
}


def model(bid):
    boxes = MODELS[bid]
    used = sorted({b[6] for b in boxes})
    elements = [{"from": [x0, y0, z0], "to": [x1, y1, z1],
                 "faces": {f: {"texture": f"#{t}"} for f in ("north", "south", "east", "west", "up", "down")}}
                for x0, y0, z0, x1, y1, z1, t in boxes]
    model_ = {"parent": "minecraft:block/block", "render_type": "minecraft:cutout", "ambientocclusion": False,
              "textures": {"particle": f"{NS}:block/{used[0]}", **{t: f"{NS}:block/{t}" for t in used}},
              "elements": elements}
    if bid == "pneumatic_post":
        model_["render_type"] = "minecraft:translucent"
    return model_


def assets(write):
    rot = {"north": 0, "east": 90, "south": 180, "west": 270}
    for bid in BLOCKS:
        write(f"models/block/{bid}.json", model(bid))
        write(f"blockstates/{bid}.json", {"variants": {
            f"facing={d}": {"model": f"{NS}:block/{bid}", **({"y": r} if r else {})} for d, r in rot.items()}})
        write(f"items/{bid}.json", {"model": {"type": "minecraft:model", "model": f"{NS}:block/{bid}"}})


# ------------------------------------------------------------------ recipes, loot, tags (gen_data.py)
def recipes(shaped, shapeless, write):
    shaped("pneumatic_post", ["BGB", "CHC", "BBB"], {"B": "brass_ingot", "G": "glass", "C": "copper_ingot", "H": "chest"})
    shaped("contract_board", ["PPP", "NWN", "S S"], {"P": "paper", "N": "brass_nugget", "W": "#planks", "S": "stick"})


def loot(write):
    for bid in BLOCKS:
        write(f"{NS}/loot_table/blocks/{bid}.json", {
            "type": "minecraft:block",
            "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": f"{NS}:{bid}"}]}],
            "random_sequence": f"{NS}:blocks/{bid}",
        })


def tags():
    """Values to merge into vanilla tag files."""
    return {"minecraft/tags/block/mineable/pickaxe.json": [f"{NS}:pneumatic_post"],
            "minecraft/tags/block/mineable/axe.json": [f"{NS}:contract_board"]}


# ------------------------------------------------------------------ manual (guide.py)
CATEGORY = ("multiplayer", "wayfarers:pneumatic_post", ("Multiplayer", "Multijoueur"))

# (id, category, icon, (title en, title fr), [(en, fr) paragraphs], [related items])
PAGES = [
    ("multiplayer", "multiplayer", "minecraft:player_head", ("Playing together", "Jouer ensemble"), [
        ("On a server, the Guild is more than a word: form a Company with your friends, trade face to face, send "
         "letters and parcels by Pneumatic Post, post contracts for the goods you need, greet people with emotes and "
         "settle disputes in a duel.",
         "Sur un serveur, la Guilde n'est pas qu'un mot : forme une Compagnie avec tes amis, échange en face à face, "
         "envoie lettres et colis par la poste pneumatique, publie des contrats pour ce qu'il te manque, salue avec "
         "des gestes et règle les différends en duel."),
        ("Keys: O company, Y emote wheel, U card of the player you look at (or sneak + right-click them with an "
         "empty hand). Change them in Options > Controls, Wayfarers: multiplayer.",
         "Touches : O compagnie, Y roue des gestes, U fiche du joueur visé (ou accroupi + clic droit sur lui, main "
         "vide). Elles se changent dans Options > Commandes, Wayfarers : multijoueur."),
        ("Everything is checked by the server, and an admin can switch off each feature in wayfarers-common.toml "
         "(section social).",
         "Tout est vérifié par le serveur, et un admin peut couper chaque fonction dans wayfarers-common.toml "
         "(section social)."),
    ], ["wayfarers:pneumatic_post", "wayfarers:contract_board"]),
    ("company", "multiplayer", "minecraft:white_banner", ("The Company", "La Compagnie"), [
        ("A Company is your party: up to 8 players. Invite someone from their card (sneak + right-click them) or "
         "from the Company screen (O); with no company yet, inviting founds one. They accept from the chat or "
         "their own Company screen.",
         "Une Compagnie, c'est ton groupe : jusqu'à 8 joueurs. Invite quelqu'un depuis sa fiche (accroupi + clic "
         "droit sur lui) ou l'écran de Compagnie (O) ; sans compagnie, inviter en fonde une. Il accepte depuis le "
         "chat ou son propre écran de Compagnie."),
        ("Companions appear at the left of the screen with their health and the way to them, and gold-framed on the "
         "minimap and world map.",
         "Tes compagnons s'affichent à gauche de l'écran avec leur vie et la direction où ils sont, et dans un cadre "
         "doré sur la mini-carte et la carte du monde."),
        ("The leader sets two switches: friendly fire (off by default: companions cannot hurt each other, arrows "
         "and potions included) and shared experience (orbs you pick up are split with the companions within "
         "48 blocks).",
         "Le chef règle deux interrupteurs : tirs amis (coupés par défaut : les compagnons ne peuvent pas se "
         "blesser, flèches et potions comprises) et expérience partagée (les orbes ramassées sont partagées avec "
         "les compagnons à moins de 48 blocs)."),
        ("Company chat: /cc your message, or the Company chat switch that sends all your chat to the company.",
         "Chat de compagnie : /cc ton message, ou l'interrupteur Chat de compagnie qui envoie tout ton chat à la "
         "compagnie."),
    ], []),
    ("company_travel", "multiplayer", "wayfarers:waystone", ("Joining a companion", "Rejoindre un compagnon"), [
        ("Standing at a waystone, select a companion in the Company screen and click Join. They get a request; once "
         "they accept, you pay 2 experience levels and appear beside them.",
         "Près d'une pierre de voyage, choisis un compagnon dans l'écran de Compagnie et clique sur Rejoindre. Il "
         "reçoit une demande ; dès qu'il accepte, tu paies 2 niveaux d'expérience et tu apparais à côté de lui."),
        ("It refuses when they fly, fall, swim in lava, fight a duel or stand near a boss, and it can only be used "
         "every 2 minutes.",
         "C'est refusé s'il vole, tombe, nage dans la lave, se bat en duel ou se trouve près d'un boss, et on ne "
         "peut le faire que toutes les 2 minutes."),
    ], ["wayfarers:waystone"]),
    ("trade", "multiplayer", "minecraft:emerald", ("Secure trade", "Échange sécurisé"), [
        ("Open a player's card (sneak + right-click them) and click Trade. When they accept, a trade screen opens "
         "for both: put what you give in your 9 slots, watch their offer on the right.",
         "Ouvre la fiche d'un joueur (accroupi + clic droit sur lui) et clique sur Échanger. S'il accepte, un écran "
         "d'échange s'ouvre chez les deux : mets ce que tu donnes dans tes 9 cases, regarde son offre à droite."),
        ("When both press Accept, a 3-second countdown starts. Any change to either offer cancels both acceptances, "
         "so nobody can swap an item at the last moment. At zero the items change hands at once.",
         "Quand les deux cliquent sur Accepter, un compte à rebours de 3 secondes démarre. Toute modification d'une "
         "offre annule les deux accords : impossible de glisser un autre objet à la dernière seconde. À zéro, les "
         "objets changent de mains d'un coup."),
        ("Stay within 8 blocks. Walking away, closing the screen or logging out gives each offer back to its owner; "
         "what no longer fits goes to your Pneumatic Post inbox, never on the ground.",
         "Restez à moins de 8 blocs. S'éloigner, fermer l'écran ou se déconnecter rend chaque offre à son "
         "propriétaire ; ce qui ne rentre plus va dans ta boîte de la poste pneumatique, jamais par terre."),
    ], []),
    ("pneumatic_post", "multiplayer", "wayfarers:pneumatic_post", ("Pneumatic Post", "Poste pneumatique"), [
        ("Every Pneumatic Post opens your own inbox: letters and parcels from other players, contract deliveries "
         "and items given back. Select one to read it; Take items puts in your bag what fits and leaves the rest.",
         "Chaque borne pneumatique ouvre ta propre boîte : lettres et colis des autres joueurs, livraisons de "
         "contrats et objets rendus. Choisis-en un pour le lire ; Prendre met dans ton sac ce qui rentre et laisse "
         "le reste."),
        ("Write tab: type the name of any player who ever joined (Tab completes it), a letter, and up to 6 stacks "
         "in the parcel slots. Postage: 1 brass nugget, plus 1 per stack. The parcel arrives at once, even if they "
         "are offline.",
         "Onglet Écrire : le nom de n'importe quel joueur déjà venu (Tab le complète), une lettre, et jusqu'à 6 "
         "piles dans les cases du colis. Affranchissement : 1 pépite de laiton, plus 1 par pile. Le colis arrive "
         "aussitôt, même s'il est absent."),
        ("Craft: brass ingots around glass, two copper ingots and a chest.",
         "Fabrication : des lingots de laiton autour d'un verre, deux lingots de cuivre et un coffre."),
    ], ["wayfarers:pneumatic_post", "wayfarers:brass_nugget"]),
    ("contract_board", "multiplayer", "wayfarers:contract_board", ("Guild contracts", "Contrats de guilde"), [
        ("Post tab of a Contract Board: click the sample slot with the item you want (a copy, it stays yours), set "
         "how many, put the reward in the reward slots and post. The reward is held by the contract until someone "
         "delivers.",
         "Onglet Publier d'un tableau des contrats : clique la case modèle avec l'objet voulu (une copie, il reste à "
         "toi), choisis la quantité, mets la récompense dans ses cases et publie. La récompense est gardée par le "
         "contrat jusqu'à la livraison."),
        ("Anyone with the goods in their bag clicks Deliver: the goods go to your Pneumatic Post inbox and the "
         "reward to them, at the same moment. Tools must be undamaged.",
         "Quiconque a la marchandise dans son sac clique sur Livrer : elle part dans ta boîte de la poste "
         "pneumatique et la récompense dans son sac, au même instant. Les outils doivent être intacts."),
        ("Cancel your own contract to get the reward back. Unfulfilled contracts expire after 7 days and the reward "
         "comes back by post. Craft: three paper, two brass nuggets, planks and two sticks.",
         "Annule ton contrat pour récupérer la récompense. Un contrat non rempli expire après 7 jours et la "
         "récompense revient par la poste. Fabrication : trois papiers, deux pépites de laiton, des planches et "
         "deux bâtons."),
    ], ["wayfarers:contract_board"]),
    ("emotes", "multiplayer", "minecraft:note_block", ("Emotes", "Gestes"), [
        ("Press Y for the emote wheel: wave, bow, cheer, clap, point, laugh, thank and rally. Click one or press its "
         "number; everyone within 24 blocks sees your arms move, the sparks and the words above their hotbar.",
         "Appuie sur Y pour la roue des gestes : saluer, s'incliner, acclamer, applaudir, montrer, rire, remercier "
         "et rallier. Clique un geste ou tape son numéro ; tout le monde à moins de 24 blocs voit tes bras bouger, "
         "les étincelles et la phrase au-dessus de sa barre d'action."),
        ("Point draws a line of light where you look; Rally blows a steam whistle to gather the company.",
         "Montrer trace un trait de lumière là où tu regardes ; Rallier fait siffler la vapeur pour rassembler la "
         "compagnie."),
    ], []),
    ("duels", "multiplayer", "minecraft:iron_sword", ("Duels", "Duels"), [
        ("Challenge a player from their card. If they accept, a red ring marks the arena around you and a 3-2-1 "
         "countdown runs: no hit counts before \"Fight!\".",
         "Défie un joueur depuis sa fiche. S'il accepte, un cercle rouge marque l'arène autour de vous et un compte "
         "à rebours 3-2-1 démarre : aucun coup ne compte avant « Combat ! »."),
        ("Nobody dies: the blow that would kill leaves half a heart and ends the duel. Leaving the ring or logging "
         "out forfeits; after 3 minutes it is a draw. Outsiders cannot hit duelists and duelists cannot hit them.",
         "Personne ne meurt : le coup fatal laisse un demi-cœur et termine le duel. Sortir du cercle ou se "
         "déconnecter fait perdre ; après 3 minutes, c'est un match nul. Les autres ne peuvent pas frapper les "
         "duellistes, ni l'inverse."),
        ("Wins and losses are kept on the player card, and the server hears who won.",
         "Victoires et défaites s'affichent sur la fiche du joueur, et tout le serveur apprend qui a gagné."),
    ], []),
]

# tip cards: (id, icon, (en, fr), manual page); shown by util/Tips.show from the Java side
TIPS = [
    ("company", "minecraft:white_banner", ("Your Company: companions on screen and on the map. O: company screen, /cc: "
                                           "company chat.",
                                           "Ta Compagnie : tes compagnons à l'écran et sur la carte. O : écran de "
                                           "compagnie, /cc : chat de compagnie."), "company"),
    ("trade", "minecraft:emerald", ("Trade: both accept, then 3 seconds pass. Any change cancels the acceptances.",
                                    "Échange : les deux acceptent, puis 3 secondes passent. Tout changement annule "
                                    "les accords."), "trade"),
    ("pneumatic_post", "wayfarers:pneumatic_post", ("Pneumatic Post: your inbox at every post box. Write to anyone, "
                                                    "even offline.",
                                                    "Poste pneumatique : ta boîte dans chaque borne. Écris à qui tu "
                                                    "veux, même absent."), "pneumatic_post"),
    ("contract_board", "wayfarers:contract_board", ("Contracts: the reward is held until someone delivers; the goods "
                                                    "arrive by post.",
                                                    "Contrats : la récompense est gardée jusqu'à la livraison ; la "
                                                    "marchandise arrive par la poste."), "contract_board"),
    ("duel", "minecraft:iron_sword", ("Duel: stay in the red ring. Nobody dies; the last blow leaves half a heart.",
                                      "Duel : reste dans le cercle rouge. Personne ne meurt ; le dernier coup laisse "
                                      "un demi-cœur."), "duels"),
    ("emotes", "minecraft:note_block", ("Emotes: Y opens the wheel, keys 1 to 8 play them.",
                                        "Gestes : Y ouvre la roue, les touches 1 à 8 les jouent."), "emotes"),
]


def guide_pages():
    return PAGES


# ------------------------------------------------------------------ translations (gen_assets.py)
EMOTES = {
    "wave": (("Wave", "Saluer"), ("%s waves", "%s salue de la main")),
    "bow": (("Bow", "S'incliner"), ("%s bows", "%s s'incline")),
    "cheer": (("Cheer", "Acclamer"), ("%s cheers!", "%s acclame !")),
    "clap": (("Clap", "Applaudir"), ("%s claps", "%s applaudit")),
    "point": (("Point", "Montrer"), ("%s points over there", "%s montre du doigt")),
    "laugh": (("Laugh", "Rire"), ("%s laughs", "%s éclate de rire")),
    "thanks": (("Thank", "Remercier"), ("%s says thank you", "%s remercie")),
    "rally": (("Rally", "Rallier"), ("%s calls everyone together!", "%s sonne le rassemblement !")),
}

LANG = {
    "key.category.wayfarers.social": ("Wayfarers: multiplayer", "Wayfarers : multijoueur"),
    "key.wayfarers.company": ("Company screen", "Écran de compagnie"),
    "key.wayfarers.emotes": ("Emote wheel", "Roue des gestes"),
    "key.wayfarers.player_card": ("Card of the player you look at", "Fiche du joueur visé"),
    # ---- shared
    "message.wayfarers.social.disabled": ("The server has switched this off.", "Le serveur a désactivé cette fonction."),
    "message.wayfarers.social.accept": ("Accept", "Accepter"),
    "message.wayfarers.social.decline": ("Decline", "Refuser"),
    "message.wayfarers.social.declined": ("%s said no.", "%s a refusé."),
    "message.wayfarers.social.no_request": ("That request has expired.", "Cette demande a expiré."),
    "message.wayfarers.social.not_online": ("That player is not online.", "Ce joueur n'est pas connecté."),
    "message.wayfarers.social.request_sent": ("Request sent to %s (it expires in a minute).",
                                              "Demande envoyée à %s (elle expire dans une minute)."),
    "message.wayfarers.social.slow_down": ("Not so fast: try again in a moment.", "Pas si vite : réessaie dans un instant."),
    "message.wayfarers.social.too_many_requests": ("You already have too many requests waiting.",
                                                   "Tu as déjà trop de demandes en attente."),
    "message.wayfarers.social.mailed_back": ("Your bag was full: the rest waits in your Pneumatic Post inbox.",
                                             "Ton sac était plein : le reste t'attend dans ta boîte de la poste pneumatique."),
    # ---- company
    "message.wayfarers.company.already": ("You are already in a company.", "Tu fais déjà partie d'une compagnie."),
    "message.wayfarers.company.none": ("You are not in a company.", "Tu n'as pas de compagnie."),
    "message.wayfarers.company.created": ("You founded %s.", "Tu as fondé %s."),
    "message.wayfarers.company.invited": ("%s invites you to join %s.", "%s t'invite à rejoindre %s."),
    "message.wayfarers.company.joined": ("%s joined %s.", "%s a rejoint %s."),
    "message.wayfarers.company.left": ("%s left the company.", "%s a quitté la compagnie."),
    "message.wayfarers.company.left_you": ("You left the company.", "Tu as quitté la compagnie."),
    "message.wayfarers.company.kicked": ("%s is no longer in the company.", "%s ne fait plus partie de la compagnie."),
    "message.wayfarers.company.kicked_you": ("You were removed from %s.", "Tu as été renvoyé de %s."),
    "message.wayfarers.company.new_leader": ("%s now leads the company.", "%s dirige maintenant la compagnie."),
    "message.wayfarers.company.leader_only": ("Only the company leader can do that.", "Seul le chef de la compagnie peut faire ça."),
    "message.wayfarers.company.full": ("The company is full.", "La compagnie est complète."),
    "message.wayfarers.company.target_taken": ("%s is already in a company.", "%s fait déjà partie d'une compagnie."),
    "message.wayfarers.company.friendly_fire": ("%s turned friendly fire %s.", "%s a réglé les tirs amis sur %s."),
    "message.wayfarers.company.share_xp": ("%s turned shared experience %s.", "%s a réglé l'expérience partagée sur %s."),
    "message.wayfarers.company.renamed": ("%s renamed the company: %s.", "%s a renommé la compagnie : %s."),
    "message.wayfarers.company.chat_on": ("Your chat now goes to your company only (/cc works too).",
                                          "Ton chat va maintenant à ta compagnie seulement (/cc marche aussi)."),
    "message.wayfarers.company.chat_off": ("Your chat goes to everyone again.", "Ton chat va de nouveau à tout le monde."),
    "message.wayfarers.company.join_request": ("%s wants to travel to you from a waystone.",
                                               "%s veut te rejoindre depuis une pierre de voyage."),
    "message.wayfarers.company.join_waystone": ("Stand at a waystone to travel to a companion.",
                                                "Tiens-toi près d'une pierre de voyage pour rejoindre un compagnon."),
    "message.wayfarers.company.join_levels": ("You need %s experience levels to travel.",
                                              "Il te faut %s niveaux d'expérience pour voyager."),
    "message.wayfarers.company.join_busy": ("Not during a trade or a duel.", "Pas pendant un échange ou un duel."),
    "message.wayfarers.company.join_unsafe": ("Your companion is not standing somewhere safe right now.",
                                              "Ton compagnon n'est pas dans un endroit sûr en ce moment."),
    "message.wayfarers.company.join_boss": ("A boss fight rages there: no travelling in.",
                                            "Un combat de boss fait rage là-bas : impossible d'y voyager."),
    "message.wayfarers.company.join_cooldown": ("The waystones need %s more seconds to recover.",
                                                "Les pierres ont besoin de %s secondes de plus pour récupérer."),
    "message.wayfarers.company.join_failed": ("%s could not travel to you.", "%s n'a pas pu te rejoindre."),
    "message.wayfarers.company.joined_mate": ("You travelled to %s.", "Tu as rejoint %s."),
    "message.wayfarers.company.mate_arrived": ("%s arrived beside you.", "%s est arrivé à côté de toi."),
    # ---- trade
    "message.wayfarers.trade.request": ("%s wants to trade with you.", "%s veut échanger avec toi."),
    "message.wayfarers.trade.too_far": ("Stand closer to %s to trade.", "Approche-toi de %s pour échanger."),
    "message.wayfarers.trade.busy": ("One of you is busy (trading, in a duel...).", "L'un de vous est occupé (échange, duel...)."),
    "message.wayfarers.trade.cancel_closed": ("Trade with %s cancelled: items returned.", "Échange avec %s annulé : objets rendus."),
    "message.wayfarers.trade.cancel_far": ("Trade with %s cancelled: too far apart.", "Échange avec %s annulé : trop loin l'un de l'autre."),
    "message.wayfarers.trade.cancel_left": ("Trade with %s cancelled.", "Échange avec %s annulé."),
    "message.wayfarers.trade.no_room_you": ("Not enough room in your bag: make space, then accept again.",
                                            "Pas assez de place dans ton sac : fais de la place, puis accepte à nouveau."),
    "message.wayfarers.trade.no_room_them": ("%s has no room for your offer.", "%s n'a pas de place pour ton offre."),
    "message.wayfarers.trade.done": ("Trade with %s done.", "Échange avec %s conclu."),
    "gui.wayfarers.trade.title": ("Trade with %s", "Échange avec %s"),
    "gui.wayfarers.trade.yours": ("Your offer", "Ton offre"),
    "gui.wayfarers.trade.accept": ("Accept", "Accepter"),
    "gui.wayfarers.trade.accepted": ("Accepted", "Accepté"),
    "gui.wayfarers.trade.accept.tip": ("Both accept, then a 3 s countdown. Any change to an offer cancels both "
                                       "acceptances. Click again to take yours back.",
                                       "Les deux acceptent, puis 3 s de compte à rebours. Toute modification d'une "
                                       "offre annule les deux accords. Reclique pour retirer le tien."),
    "gui.wayfarers.trade.cancel": ("Cancel", "Annuler"),
    "gui.wayfarers.trade.hint": ("Put what you give on the left, then Accept.", "Mets ce que tu donnes à gauche, puis Accepter."),
    "gui.wayfarers.trade.waiting": ("Waiting for the other side...", "En attente de l'autre..."),
    "gui.wayfarers.trade.they_accepted": ("They accepted: check their offer, then Accept.",
                                          "L'autre a accepté : vérifie son offre, puis Accepter."),
    "gui.wayfarers.trade.countdown": ("Exchange in %s...", "Échange dans %s..."),
    "gui.wayfarers.trade.no_room_you": ("Your bag is too full for their offer.", "Ton sac est trop plein pour son offre."),
    "gui.wayfarers.trade.no_room_them": ("Their bag is too full for your offer.", "Son sac est trop plein pour ton offre."),
    # ---- post
    "message.wayfarers.post.waiting": ("%s letters or parcels wait for you at any Pneumatic Post.",
                                       "%s lettres ou colis t'attendent à n'importe quelle borne pneumatique."),
    "message.wayfarers.post.unknown": ("Nobody called %s ever came here.", "Personne du nom de %s n'est jamais venu ici."),
    "message.wayfarers.post.self": ("You cannot write to yourself.", "Tu ne peux pas t'écrire à toi-même."),
    "message.wayfarers.post.empty": ("Write a letter or add items first.", "Écris une lettre ou ajoute des objets d'abord."),
    "message.wayfarers.post.full": ("%s's inbox is full.", "La boîte de %s est pleine."),
    "message.wayfarers.post.postage": ("Postage: %s × %s needed.", "Affranchissement : il faut %s × %s."),
    "message.wayfarers.post.sent": ("Your parcel whooshes off to %s.", "Ton colis file vers %s dans un souffle."),
    "message.wayfarers.post.arrived": ("New letter from %s at the Pneumatic Post.", "Nouvelle lettre de %s à la poste pneumatique."),
    "message.wayfarers.post.arrived_system": ("A parcel arrived at the Pneumatic Post.", "Un colis est arrivé à la poste pneumatique."),
    "message.wayfarers.post.no_room": ("Your bag is full: the rest stays in the parcel.", "Ton sac est plein : le reste reste dans le colis."),
    "message.wayfarers.post.not_empty": ("Take the items out first.", "Retire d'abord les objets."),
    "gui.wayfarers.post.inbox": ("Inbox", "Boîte"),
    "gui.wayfarers.post.inbox.tip": ("Letters and parcels waiting for you.", "Lettres et colis qui t'attendent."),
    "gui.wayfarers.post.write": ("Write", "Écrire"),
    "gui.wayfarers.post.write.tip": ("Send a letter or a parcel to any player.", "Envoyer une lettre ou un colis à un joueur."),
    "gui.wayfarers.post.to": ("To", "À"),
    "gui.wayfarers.post.to_hint": ("Player name (Tab completes)", "Nom du joueur (Tab complète)"),
    "gui.wayfarers.post.letter": ("Letter", "Lettre"),
    "gui.wayfarers.post.letter_hint": ("Your letter (256 characters)...", "Ta lettre (256 caractères)..."),
    "gui.wayfarers.post.send": ("Send", "Envoyer"),
    "gui.wayfarers.post.send_cost": ("Send (%s × %s)", "Envoyer (%s × %s)"),
    "gui.wayfarers.post.send.tip": ("Postage is taken from your bag; the parcel arrives at once, even offline.",
                                    "L'affranchissement est pris dans ton sac ; le colis arrive aussitôt, même absent."),
    "gui.wayfarers.post.take": ("Take items", "Prendre"),
    "gui.wayfarers.post.discard": ("Throw away", "Jeter"),
    "gui.wayfarers.post.discard.tip": ("Throw away a read letter (only once it holds no items).",
                                       "Jeter une lettre lue (seulement quand elle ne contient plus d'objet)."),
    "gui.wayfarers.post.parcel": ("Parcel", "Colis"),
    "gui.wayfarers.post.parcel_hint": ("Up to 6 stacks. They come back to you if you close without sending.",
                                       "Jusqu'à 6 piles. Elles te reviennent si tu fermes sans envoyer."),
    "gui.wayfarers.post.empty": ("Select a letter to read it.", "Choisis une lettre pour la lire."),
    "gui.wayfarers.post.empty_list": ("Your inbox is empty.", "Ta boîte est vide."),
    "gui.wayfarers.post.loading": ("Opening the tubes...", "Ouverture des tubes..."),
    "gui.wayfarers.post.from": ("From %s", "De %s"),
    "gui.wayfarers.post.stacks": ("Parcel (%s)", "Colis (%s)"),
    "gui.wayfarers.post.just_now": ("just now", "à l'instant"),
    "gui.wayfarers.post.minutes": ("%s min ago", "il y a %s min"),
    "gui.wayfarers.post.hours": ("%s h ago", "il y a %s h"),
    "gui.wayfarers.post.days": ("%s days ago", "il y a %s jours"),
    "gui.wayfarers.post.kind.delivery": ("Contract delivery", "Livraison de contrat"),
    "gui.wayfarers.post.kind.reward": ("Contract reward", "Récompense de contrat"),
    "gui.wayfarers.post.kind.refund": ("Contract refund", "Remboursement de contrat"),
    "gui.wayfarers.post.kind.returned": ("Items given back", "Objets rendus"),
    "gui.wayfarers.post.body.delivery": ("%s delivered the goods of your contract.", "%s a livré la marchandise de ton contrat."),
    "gui.wayfarers.post.body.reward": ("Your reward did not fit in your bag.", "Ta récompense ne rentrait pas dans ton sac."),
    "gui.wayfarers.post.body.refund": ("The reward of your cancelled or expired contract.",
                                       "La récompense de ton contrat annulé ou expiré."),
    "gui.wayfarers.post.body.returned": ("Items that could not go back into your bag.", "Des objets qui ne rentraient plus dans ton sac."),
    # ---- contracts
    "message.wayfarers.contract.no_sample": ("Click the sample slot with the item you want.", "Clique la case modèle avec l'objet voulu."),
    "message.wayfarers.contract.no_reward": ("Put a reward in the reward slots.", "Mets une récompense dans ses cases."),
    "message.wayfarers.contract.amount": ("Ask for 1 to %s items.", "Demande de 1 à %s objets."),
    "message.wayfarers.contract.too_many": ("You already have %s open contracts.", "Tu as déjà %s contrats ouverts."),
    "message.wayfarers.contract.posted": ("%s posted a contract: %s × %s wanted.", "%s a publié un contrat : %s × %s demandés."),
    "message.wayfarers.contract.gone": ("That contract was already taken.", "Ce contrat a déjà été rempli."),
    "message.wayfarers.contract.own": ("That is your own contract.", "C'est ton propre contrat."),
    "message.wayfarers.contract.missing": ("You still need %s × %s (undamaged).", "Il te manque encore %s × %s (intacts)."),
    "message.wayfarers.contract.delivered": ("Delivered! The goods are on their way to %s.", "Livré ! La marchandise part vers %s."),
    "message.wayfarers.contract.fulfilled": ("%s delivered %s × %s: collect them at a Pneumatic Post.",
                                             "%s a livré %s × %s : récupère-les à une borne pneumatique."),
    "message.wayfarers.contract.not_yours": ("Only its poster can cancel this contract.", "Seul son auteur peut annuler ce contrat."),
    "message.wayfarers.contract.cancelled": ("Contract cancelled.", "Contrat annulé."),
    "gui.wayfarers.contract.board": ("Board", "Tableau"),
    "gui.wayfarers.contract.board.tip": ("Every open contract on the server.", "Tous les contrats ouverts du serveur."),
    "gui.wayfarers.contract.post": ("Post", "Publier"),
    "gui.wayfarers.contract.post.tip": ("Ask for something and pay a reward.", "Demander quelque chose contre une récompense."),
    "gui.wayfarers.contract.wanted": ("Wanted", "Demandé"),
    "gui.wayfarers.contract.reward": ("Reward", "Récompense"),
    "gui.wayfarers.contract.amount": ("Amount", "Quantité"),
    "gui.wayfarers.contract.step": ("Shift: 16 at a time", "Maj : 16 à la fois"),
    "gui.wayfarers.contract.note": ("Note", "Note"),
    "gui.wayfarers.contract.note_hint": ("A note (optional)", "Une note (facultatif)"),
    "gui.wayfarers.contract.post_help": ("Click the gold slot with the item you want (a copy, it stays yours), choose "
                                         "how many, put the reward in the 6 slots, then Post.",
                                         "Clique la case dorée avec l'objet voulu (une copie, il reste à toi), choisis "
                                         "la quantité, mets la récompense dans les 6 cases, puis Publier."),
    "gui.wayfarers.contract.sample_hint": ("Click with an item", "Clique avec un objet"),
    "gui.wayfarers.contract.post_button": ("Post the contract", "Publier le contrat"),
    "gui.wayfarers.contract.post_button.tip": ("The reward leaves your hands now and is held by the contract. It "
                                               "expires after %s days (reward back by post).",
                                               "La récompense quitte tes mains maintenant et reste en dépôt. Le "
                                               "contrat expire après %s jours (récompense rendue par la poste)."),
    "gui.wayfarers.contract.deliver": ("Deliver", "Livrer"),
    "gui.wayfarers.contract.deliver.tip": ("Hand over the goods from your bag and get the reward at once.",
                                           "Remettre la marchandise de ton sac et recevoir aussitôt la récompense."),
    "gui.wayfarers.contract.cancel": ("Cancel my contract", "Annuler mon contrat"),
    "gui.wayfarers.contract.cancel.tip": ("Take the contract down and get the reward back.",
                                          "Retirer le contrat et récupérer la récompense."),
    "gui.wayfarers.contract.empty": ("Select a contract.", "Choisis un contrat."),
    "gui.wayfarers.contract.empty_list": ("No open contract. Be the first: Post tab.", "Aucun contrat ouvert. Sois le premier : onglet Publier."),
    "gui.wayfarers.contract.by": ("by %s", "par %s"),
    "gui.wayfarers.contract.days_left": ("%s days left", "encore %s jours"),
    "gui.wayfarers.contract.hours_left": ("%s h left", "encore %s h"),
    # ---- duels
    "message.wayfarers.duel.request": ("%s challenges you to a duel. Nobody dies, nothing is lost.",
                                       "%s te défie en duel. Personne ne meurt, rien n'est perdu."),
    "message.wayfarers.duel.too_far": ("Stand closer to %s to start a duel.", "Approche-toi de %s pour lancer un duel."),
    "message.wayfarers.duel.busy": ("One of you is busy (trading, already in a duel...).",
                                    "L'un de vous est occupé (échange, déjà en duel...)."),
    "message.wayfarers.duel.boss": ("Not here: a boss is too close.", "Pas ici : un boss est trop proche."),
    "message.wayfarers.duel.started": ("Duel against %s! Stay within %s blocks of the centre.",
                                       "Duel contre %s ! Reste à moins de %s blocs du centre."),
    "message.wayfarers.duel.fight": ("Fight!", "Combat !"),
    "message.wayfarers.duel.vs": ("against %s", "contre %s"),
    "message.wayfarers.duel.won": ("%s won the duel against %s.", "%s a gagné le duel contre %s."),
    "message.wayfarers.duel.won_fell": ("%s won the duel: %s fell.", "%s a gagné le duel : %s est tombé."),
    "message.wayfarers.duel.won_left": ("%s won the duel: %s left.", "%s a gagné le duel : %s est parti."),
    "message.wayfarers.duel.won_ring": ("%s won the duel: %s left the ring.", "%s a gagné le duel : %s est sorti du cercle."),
    "message.wayfarers.duel.draw": ("The duel between %s and %s is a draw.", "Le duel entre %s et %s se termine par un match nul."),
    "message.wayfarers.duel.title_win": ("Victory!", "Victoire !"),
    "message.wayfarers.duel.title_loss": ("Defeat", "Défaite"),
    "message.wayfarers.duel.title_draw": ("Draw", "Match nul"),
    # ---- company screen
    "gui.wayfarers.company.title": ("Company", "Compagnie"),
    "gui.wayfarers.company.default_name": ("%s's Company", "Compagnie de %s"),
    "gui.wayfarers.company.none": ("You travel alone. Found a company, or accept an invitation on the left.",
                                   "Tu voyages seul. Fonde une compagnie, ou accepte une invitation à gauche."),
    "gui.wayfarers.company.name_hint": ("Company name", "Nom de la compagnie"),
    "gui.wayfarers.company.player_hint": ("Player or new name", "Joueur ou nouveau nom"),
    "gui.wayfarers.company.found": ("Found a company", "Fonder une compagnie"),
    "gui.wayfarers.company.found.tip": ("You lead it; invite players from their card or with the field above.",
                                        "Tu la diriges ; invite des joueurs depuis leur fiche ou avec le champ ci-dessus."),
    "gui.wayfarers.company.invites": ("Invitations", "Invitations"),
    "gui.wayfarers.company.no_invites": ("No invitation. A player invites you from your card (sneak + right-click "
                                         "you) or by name.",
                                         "Aucune invitation. Un joueur t'invite depuis ta fiche (accroupi + clic droit "
                                         "sur toi) ou par ton nom."),
    "gui.wayfarers.company.invited_by": ("invited by %s", "invité par %s"),
    "gui.wayfarers.company.accept": ("Accept", "Accepter"),
    "gui.wayfarers.company.decline": ("Decline", "Refuser"),
    "gui.wayfarers.company.friendly_fire": ("Friendly fire", "Tirs amis"),
    "gui.wayfarers.company.friendly_fire.tip": ("On: companions can hurt each other. Off: no hit, arrow or potion "
                                                "between companions does anything. Leader only.",
                                                "Activés : les compagnons peuvent se blesser. Coupés : aucun coup, "
                                                "flèche ou potion entre compagnons. Chef seulement."),
    "gui.wayfarers.company.share_xp": ("Share XP", "XP partagée"),
    "gui.wayfarers.company.share_xp.tip": ("Experience orbs you pick up are split evenly with the companions within "
                                           "48 blocks. Leader only.",
                                           "Les orbes ramassées sont partagées à parts égales avec les compagnons à "
                                           "moins de 48 blocs. Chef seulement."),
    "gui.wayfarers.company.chat": ("Company chat", "Chat compagnie"),
    "gui.wayfarers.company.chat.tip": ("On: everything you type in the chat goes to your company only. /cc sends one "
                                       "message to the company at any time.",
                                       "Activé : tout ce que tu écris dans le chat va à ta compagnie seulement. /cc "
                                       "envoie un message à la compagnie à tout moment."),
    "gui.wayfarers.company.hud": ("Show on screen", "Voir à l'écran"),
    "gui.wayfarers.company.hud.tip": ("Your online companions at the left of the screen: health, distance, direction.",
                                      "Tes compagnons connectés à gauche de l'écran : vie, distance, direction."),
    "gui.wayfarers.company.invite": ("Invite", "Inviter"),
    "gui.wayfarers.company.invite.tip": ("Invite the online player named in the field (leader only).",
                                         "Inviter le joueur connecté nommé dans le champ (chef seulement)."),
    "gui.wayfarers.company.rename": ("Rename", "Renommer"),
    "gui.wayfarers.company.rename.tip": ("Give the company the name typed in the field (leader only).",
                                         "Donner à la compagnie le nom écrit dans le champ (chef seulement)."),
    "gui.wayfarers.company.join": ("Join", "Rejoindre"),
    "gui.wayfarers.company.join.tip": ("Standing at a waystone: travel to the selected companion once they accept "
                                       "(%s levels).",
                                       "Près d'une pierre de voyage : rejoindre le compagnon choisi dès qu'il accepte "
                                       "(%s niveaux)."),
    "gui.wayfarers.company.promote": ("Lead", "Chef"),
    "gui.wayfarers.company.promote.tip": ("Make the selected companion the leader.", "Faire du compagnon choisi le chef."),
    "gui.wayfarers.company.kick": ("Remove", "Renvoyer"),
    "gui.wayfarers.company.kick.tip": ("Remove the selected companion from the company.", "Retirer le compagnon choisi de la compagnie."),
    "gui.wayfarers.company.leave": ("Leave the company", "Quitter la compagnie"),
    "gui.wayfarers.company.offline": ("offline", "absent"),
    "gui.wayfarers.company.size": ("%s / %s members", "%s / %s membres"),
    "gui.wayfarers.company.hint": ("%s: close  -  /cc <message>: company chat", "%s : fermer  -  /cc <message> : chat de compagnie"),
    # ---- player card
    "gui.wayfarers.card.title": ("Wayfarer", "Voyageur"),
    "gui.wayfarers.card.company": ("Company: %s", "Compagnie : %s"),
    "gui.wayfarers.card.no_company": ("No company", "Sans compagnie"),
    "gui.wayfarers.card.companion": ("Your companion", "Ton compagnon"),
    "gui.wayfarers.card.record": ("Duels: %s won, %s lost, %s drawn", "Duels : %s gagnés, %s perdus, %s nuls"),
    "gui.wayfarers.card.trade": ("Trade", "Échanger"),
    "gui.wayfarers.card.trade.tip": ("Ask for a secure trade (stand within 8 blocks).", "Proposer un échange sécurisé (à moins de 8 blocs)."),
    "gui.wayfarers.card.duel": ("Duel", "Duel"),
    "gui.wayfarers.card.duel.tip": ("Challenge them: nobody dies, nothing is lost.", "Le défier : personne ne meurt, rien n'est perdu."),
    "gui.wayfarers.card.invite": ("Invite", "Inviter"),
    "gui.wayfarers.card.invite.tip": ("Invite them to your company (founds one if you have none).",
                                      "L'inviter dans ta compagnie (en fonde une si tu n'en as pas)."),
    "gui.wayfarers.card.invite.same": ("Already your companion.", "Déjà ton compagnon."),
    "gui.wayfarers.card.invite.no": ("They are in another company, or only your leader can invite.",
                                     "Il est dans une autre compagnie, ou seul ton chef peut inviter."),
    "gui.wayfarers.card.hint": ("Sneak + right-click a player, or look at them and press %s",
                                "Accroupi + clic droit sur un joueur, ou vise-le et appuie sur %s"),
    "gui.wayfarers.card.look": ("Look at a player to open their card.", "Vise un joueur pour ouvrir sa fiche."),
    # ---- emotes
    "gui.wayfarers.emote.title": ("Emotes", "Gestes"),
    "gui.wayfarers.emote.hint": ("click or 1-8", "clic ou 1-8"),
}


def lang():
    en, fr = {}, {}
    for bid, (e, f, te, tf) in BLOCKS.items():
        en[f"block.{NS}.{bid}"], fr[f"block.{NS}.{bid}"] = e, f
        en[f"block.{NS}.{bid}.desc"], fr[f"block.{NS}.{bid}.desc"] = te, tf
    for key, (e, f) in LANG.items():
        en[key], fr[key] = e, f
    for eid, ((ne, nf), (me, mf)) in EMOTES.items():
        en[f"gui.{NS}.emote.{eid}"], fr[f"gui.{NS}.emote.{eid}"] = ne, nf
        en[f"message.{NS}.emote.{eid}"], fr[f"message.{NS}.emote.{eid}"] = me, mf
    return en, fr

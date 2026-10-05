"""Quest-giver NPCs (brasshaven:wayfarer_npc) and the contracts they hand out.

One source of truth for:
  * tools/gen_quests.py   translations (roles, names, dialogue, quest titles and objectives) + the journal rewards
  * tools/gen_java.py     com.brasshaven.generated.GeneratedNpcs (roles and quest definitions read by the server)
  * tools/wf/interior.py  quest_npc(): the template entity a structure places
  * tools/wf/mobs/wayfarer_npc.py   one texture variant per role (same order as ROLES)
  * guide / wiki texts

A contract is accepted from its giver, followed in the quest journal (Contracts tab) and on the HUD tracker, and
turned in to the giver (or, for a delivery, to an NPC of the ``to`` role) for its rewards:
  fetch    bring ``count`` x ``target`` (item id); the items are taken on turn-in
  hunt     kill ``count`` x ``target`` (entity id) after accepting
  explore  enter a ``target`` structure (structure id) after accepting
  deliver  the giver hands over a sealed parcel; give it to any NPC of role ``to``
``after``: the contract the same player must have finished first (its giver offers this one only then).
"""

# role id: (english title, french title, [given names], structure homes (for the texts))
ROLES = {
    "guild_agent": ("Guild Agent", "Agent de la Guilde",
                    ["Mira", "Aldo", "Sasha", "Bertrand", "Elise", "Tomas", "Noor", "Gaspard"]),
    # (the French titles are gendered: the given names match them)
    "scholar": ("Scholar", "Érudite",
                ["Ysolde", "Livia", "Maud", "Clémence", "Irène", "Ophélie"]),
    "tinkerer": ("Tinkerer", "Bricoleur",
                 ["Barnaby", "Ferris", "Ambroise", "Gustave", "Anatole", "Rivet"]),
    "druid": ("Druid", "Druidesse",
              ["Sylwen", "Brenna", "Elowen", "Morwen", "Aelis", "Nimue"]),
    "dwarf_elder": ("Dwarf Elder", "Ancien nain",
                    ["Thrain", "Grimald", "Orsik", "Brokk", "Haldor", "Torvin"]),
}
ROLE_ORDER = list(ROLES)

# where each role lives (for the manual and the wiki)
HOMES = {
    "guild_agent": (["guild_outpost"], "villages: the Guild Post and the plaza", "villages : le Relais de la Guilde et la place"),
    "scholar": (["forgotten_library"], "villages: the Brasshaven' Inn", "villages : l'auberge des Voyageurs"),
    "tinkerer": (["clockwork_citadel"], "villages: the tinkerer's workshop", "villages : l'atelier du bricoleur"),
    "druid": (["giant_tree"], "", ""),
    "dwarf_elder": (["dwarven_city"], "", ""),
}

# role: (greeting en, greeting fr, nothing-left en, nothing-left fr)
TALK = {
    "guild_agent": ("The Guild always needs a hand. Here is what is pinned on my board today.",
                    "La Guilde a toujours besoin de bras. Voici ce qui est épinglé sur mon tableau aujourd'hui.",
                    "No more contracts for you today, wayfarer. The roads are safer thanks to you.",
                    "Plus de contrats pour toi aujourd'hui, voyageur. Les routes sont plus sûres grâce à toi."),
    "scholar": ("Ah, a traveller! Knowledge hides in dangerous places. Will you help me fetch some?",
                "Ah, une voyageuse ! Le savoir se cache dans des endroits dangereux. Tu m'aides à en rapporter ?",
                "My notes are complete, for now. Come back when the world has new secrets.",
                "Mes notes sont complètes, pour l'instant. Reviens quand le monde aura de nouveaux secrets."),
    "tinkerer": ("Mind the gears! I always need parts, and someone brave enough to test my contraptions.",
                 "Attention aux rouages ! J'ai toujours besoin de pièces, et de quelqu'un d'assez brave pour tester mes machines.",
                 "Every gear is in its place. Tick, tock, perfect.",
                 "Chaque rouage est à sa place. Tic, tac, parfait."),
    "druid": ("The World Tree listens to those who care for the forest. What will you do for it?",
              "L'Arbre-monde écoute ceux qui prennent soin de la forêt. Que feras-tu pour lui ?",
              "The forest is at peace. Walk softly, friend.",
              "La forêt est en paix. Marche doucement, ami."),
    "dwarf_elder": ("Hmph. Surface folk. Prove your worth and the deep halls will remember your name.",
                    "Hmpf. Des gens de la surface. Prouve ta valeur et les salles profondes se souviendront de ton nom.",
                    "You have done the clans proud. The forges sing your name.",
                    "Tu as fait honneur aux clans. Les forges chantent ton nom."),
}


class Q:
    """One contract. Rewards: [(item id, count)] + xp."""

    def __init__(self, qid, giver, kind, target, count, title, desc, story, rewards, xp, to=None, after=None,
                 icon=None):
        self.id = qid
        self.giver = giver
        self.kind = kind
        self.target = target if ":" in (target or "") or kind == "deliver" else f"minecraft:{target}"
        self.count = count
        self.title = title      # (en, fr)
        self.desc = desc        # (en, fr): the objective, shown in the journal and the tracker
        self.story = story      # (en, fr): what the giver says when offering it
        self.rewards = [(i if ":" in i else f"minecraft:{i}", c) for i, c in rewards]
        self.xp = xp
        self.to = to
        self.after = after
        self.icon = icon or (self.target if kind == "fetch" else {"hunt": "minecraft:iron_sword",
                                                                    "explore": "minecraft:compass",
                                                                    "deliver": "minecraft:paper"}[kind])


W = "brasshaven:"
QUESTS = [
    # ---------------------------------------------------------------- the Guild Agent (villages, guild outposts)
    Q("guild_provisions", "guild_agent", "fetch", "bread", 12,
      ("Provisions for the Road", "Des vivres pour la route"),
      ("Bring 12 Bread to a Guild Agent.", "Apporte 12 pains à un agent de la Guilde."),
      ("Our scouts leave at dawn with empty bags. Twelve loaves would keep them going for a week.",
       "Nos éclaireurs partent à l'aube les sacs vides. Douze pains les nourriraient une semaine."),
      [("emerald", 6), (W + "map_fragment", 2)], 30),
    Q("guild_roads", "guild_agent", "hunt", "zombie", 10,
      ("Clear the Roads", "Dégager les routes"),
      ("Defeat 10 Zombies, then report to a Guild Agent.", "Vaincs 10 zombies, puis fais ton rapport à un agent de la Guilde."),
      ("The dead walk the trade roads at night. Thin them out and the caravans will thank you.",
       "Les morts arpentent les routes marchandes la nuit. Éclaircis leurs rangs et les caravanes te remercieront."),
      [("emerald", 8), ("bread", 6)], 40),
    Q("guild_survey", "guild_agent", "explore", W + "ruined_watchtower", 1,
      ("Survey the Watchtower", "Inspecter la tour de guet"),
      ("Find a Ruined Watchtower, then report to a Guild Agent.",
       "Trouve une tour de guet en ruine, puis fais ton rapport à un agent de la Guilde."),
      ("One of our old watchtowers went silent. Find one and tell me what is left of it.",
       "Une de nos vieilles tours de guet ne répond plus. Trouves-en une et dis-moi ce qu'il en reste."),
      [(W + "map_fragment", 3), ("emerald", 5)], 50, after="guild_provisions"),
    Q("guild_bandits", "guild_agent", "hunt", "pillager", 8,
      ("Bounty: Bandits", "Prime : les bandits"),
      ("Defeat 8 Pillagers, then report to a Guild Agent.", "Vaincs 8 pillards, puis fais ton rapport à un agent de la Guilde."),
      ("Bandits camp along the plains and rob our couriers. The Guild pays well for every one of them.",
       "Des bandits campent dans les plaines et détroussent nos coursiers. La Guilde paie bien pour chacun d'eux."),
      [("emerald", 14), (W + "recall_scroll", 2)], 80, after="guild_roads"),
    Q("guild_letter", "guild_agent", "deliver", None, 1,
      ("A Letter for the Druids", "Une lettre pour les druides"),
      ("Carry the Guild's sealed letter to a Druid of the World Tree.",
       "Porte la lettre scellée de la Guilde à une druidesse de l'Arbre-monde."),
      ("The druids of the Hollow Giant Tree have not answered our letters. Bring this one to them in person.",
       "Les druides de l'Arbre-monde creux ne répondent plus à nos lettres. Porte-leur celle-ci en main propre."),
      [("emerald", 12), (W + "structure_compass", 1)], 80, to="druid", after="guild_survey"),
    # ---------------------------------------------------------------- the Scholar (village inns, Forgotten Library)
    Q("scholar_books", "scholar", "fetch", "book", 6,
      ("Blank Pages", "Des pages blanches"),
      ("Bring 6 Books to a Scholar.", "Apporte 6 livres à une érudite."),
      ("I filled my last notebook last night. Six books, and I can write down everything you will find.",
       "J'ai rempli mon dernier carnet hier soir. Six livres, et je pourrai noter tout ce que tu trouveras."),
      [("experience_bottle", 6), ("emerald", 4)], 30),
    Q("scholar_library", "scholar", "explore", W + "forgotten_library", 1,
      ("The Forgotten Library", "La bibliothèque oubliée"),
      ("Find a Forgotten Library, then come back to a Scholar.",
       "Trouve une bibliothèque oubliée, puis reviens voir une érudite."),
      ("Somewhere a whole library sank under moss and ink. Find it, and tell me if the shelves still stand.",
       "Quelque part, une bibliothèque entière a sombré sous la mousse et l'encre. Trouve-la et dis-moi si les rayonnages tiennent encore."),
      [(W + "map_fragment", 3), ("experience_bottle", 8)], 60, after="scholar_books"),
    Q("scholar_wraiths", "scholar", "hunt", W + "map_wraith", 4,
      ("Torn Maps", "Cartes déchirées"),
      ("Defeat 4 Map Wraiths, then come back to a Scholar.", "Vaincs 4 spectres des cartes, puis reviens voir une érudite."),
      ("Map Wraiths shred every chart they touch. Put a few of them to rest and our maps will stay whole.",
       "Les spectres des cartes déchirent tout ce qu'ils touchent. Fais-en reposer quelques-uns et nos cartes resteront entières."),
      [("emerald", 10), (W + "magnet_ring", 1)], 90, after="scholar_library"),
    Q("scholar_notes", "scholar", "deliver", None, 1,
      ("Notes for the Tinkerer", "Des notes pour le bricoleur"),
      ("Bring the Scholar's notes to a Tinkerer.", "Apporte les notes de l'érudite à un bricoleur."),
      ("These are drawings of an old clockwork. The tinkerers of the Clockwork Citadel will know what to make of them.",
       "Voici les croquis d'un vieux mécanisme. Les bricoleurs de la Citadelle d'horlogerie sauront quoi en faire."),
      [("emerald", 10), ("experience_bottle", 6)], 70, to="tinkerer", after="scholar_books"),
    # ---------------------------------------------------------------- the Tinkerer (village workshops, Clockwork Citadel)
    Q("tinker_copper", "tinkerer", "fetch", "copper_ingot", 24,
      ("Copper for the Boilers", "Du cuivre pour les chaudières"),
      ("Bring 24 Copper Ingots to a Tinkerer.", "Apporte 24 lingots de cuivre à un bricoleur."),
      ("My boilers leak like sieves. Twenty-four copper ingots and they will hold the steam again.",
       "Mes chaudières fuient comme des passoires. Vingt-quatre lingots de cuivre et elles retiendront de nouveau la vapeur."),
      [(W + "brass_gear", 4), ("emerald", 6)], 30),
    Q("tinker_spiders", "tinkerer", "hunt", W + "clockwork_spider", 6,
      ("Runaway Spiders", "Araignées en fuite"),
      ("Defeat 6 Clockwork Spiders, then come back to a Tinkerer.",
       "Vaincs 6 araignées-horloges, puis reviens voir un bricoleur."),
      ("Some of my clockwork spiders ran off and went feral. Bring them down before they bite someone.",
       "Quelques-unes de mes araignées-horloges se sont enfuies et sont devenues sauvages. Arrête-les avant qu'elles ne mordent quelqu'un."),
      [("emerald", 10), (W + "pocket_watch", 1)], 70, after="tinker_copper"),
    Q("tinker_foundry", "tinkerer", "explore", W + "geothermal_foundry", 1,
      ("Heat of the Earth", "La chaleur de la terre"),
      ("Find a Geothermal Foundry, then come back to a Tinkerer.",
       "Trouve une fonderie géothermique, puis reviens voir un bricoleur."),
      ("They say a foundry was built on the flank of a volcano. I must know how they tame that heat!",
       "On dit qu'une fonderie a été bâtie au flanc d'un volcan. Je dois savoir comment ils domptent cette chaleur !"),
      [(W + "brass_gear", 6), (W + "map_fragment", 2)], 70, after="tinker_copper"),
    Q("tinker_parts", "tinkerer", "deliver", None, 1,
      ("Spare Parts for the Deep", "Pièces pour les profondeurs"),
      ("Bring the Tinkerer's crate of parts to a Dwarf Elder.", "Apporte la caisse de pièces du bricoleur à un ancien nain."),
      ("The dwarves of the deep city ordered pistons for their rails. Mind the stairs, it is heavy.",
       "Les nains de la cité profonde ont commandé des pistons pour leurs rails. Attention aux escaliers, c'est lourd."),
      [("emerald", 12), (W + "brass_gear", 4)], 90, to="dwarf_elder", after="tinker_spiders"),
    # ---------------------------------------------------------------- the Druid (World Tree)
    Q("druid_saplings", "druid", "fetch", "oak_sapling", 8,
      ("Seeds of the Forest", "Les graines de la forêt"),
      ("Bring 8 Oak Saplings to a Druid.", "Apporte 8 pousses de chêne à une druidesse."),
      ("Every tree cut must be given back. Eight oak saplings, and the forest forgives.",
       "Chaque arbre coupé doit être rendu. Huit pousses de chêne, et la forêt pardonne."),
      [("golden_carrot", 6), ("emerald", 4)], 30),
    Q("druid_spiders", "druid", "hunt", "spider", 10,
      ("Webs in the Branches", "Des toiles dans les branches"),
      ("Defeat 10 Spiders, then come back to a Druid.", "Vaincs 10 araignées, puis reviens voir une druidesse."),
      ("Spiders weave over our nests and smother the young leaves. Drive them out of the canopy.",
       "Les araignées tissent sur nos nids et étouffent les jeunes feuilles. Chasse-les de la canopée."),
      [("emerald", 8), ("golden_apple", 1)], 60, after="druid_saplings"),
    Q("druid_palace", "druid", "explore", W + "sylvan_palace", 1,
      ("The Sylvan Court", "La cour sylvaine"),
      ("Find the Sylvan Palace, then come back to a Druid.", "Trouve le Palais sylvain, puis reviens voir une druidesse."),
      ("Our sisters of the Sylvan Palace sing under a pale tree. Find them and bring me news of their court.",
       "Nos sœurs du Palais sylvain chantent sous un arbre pâle. Trouve-les et rapporte-moi des nouvelles de leur cour."),
      [("emerald", 12), ("experience_bottle", 8)], 90, after="druid_saplings"),
    Q("druid_gift", "druid", "deliver", None, 1,
      ("A Gift for the Guild", "Un présent pour la Guilde"),
      ("Bring the Druid's seed pouch to a Guild Agent.", "Apporte la bourse de graines de la druidesse à un agent de la Guilde."),
      ("The Guild feeds many mouths. Take them these seeds from the World Tree; they grow anywhere.",
       "La Guilde nourrit beaucoup de bouches. Porte-leur ces graines de l'Arbre-monde : elles poussent partout."),
      [("emerald", 10), (W + "recall_scroll", 2)], 70, to="guild_agent", after="druid_spiders"),
    # ---------------------------------------------------------------- the Dwarf Elder (Deep Dwarven City)
    Q("elder_iron", "dwarf_elder", "fetch", "iron_ingot", 20,
      ("Iron for the Forges", "Du fer pour les forges"),
      ("Bring 20 Iron Ingots to a Dwarf Elder.", "Apporte 20 lingots de fer à un ancien nain."),
      ("The mines run dry and the forges starve. Twenty ingots of iron, surface dweller.",
       "Les mines s'épuisent et les forges ont faim. Vingt lingots de fer, gens de la surface."),
      [("emerald", 8), (W + "lithite_shard", 2)], 40),
    Q("elder_skeletons", "dwarf_elder", "hunt", "skeleton", 12,
      ("Bones in the Halls", "Des os dans les salles"),
      ("Defeat 12 Skeletons, then come back to a Dwarf Elder.", "Vaincs 12 squelettes, puis reviens voir un ancien nain."),
      ("The old dead rise in the lower halls and shoot at our miners. Break their bones.",
       "Les anciens morts se relèvent dans les salles basses et tirent sur nos mineurs. Brise-leur les os."),
      [("emerald", 12), ("diamond", 1)], 80, after="elder_iron"),
    Q("elder_forge", "dwarf_elder", "explore", W + "dwarven_forge", 1,
      ("The Lost Forge", "La forge perdue"),
      ("Find a Dwarven Forge, then come back to a Dwarf Elder.", "Trouve une forge naine, puis reviens voir un ancien nain."),
      ("Our ancestors had a forge deeper than this city. Find it and tell me if the anvils still ring.",
       "Nos ancêtres avaient une forge plus profonde que cette cité. Trouve-la et dis-moi si les enclumes résonnent encore."),
      [(W + "lithite_shard", 4), ("emerald", 10)], 100, after="elder_iron"),
    Q("elder_runes", "dwarf_elder", "deliver", None, 1,
      ("Runes for the Scholar", "Des runes pour l'érudite"),
      ("Bring the Elder's rune tablet to a Scholar.", "Apporte la tablette runique de l'ancien à une érudite."),
      ("These runes are older than my clan. Let one of your surface scholars try to read them.",
       "Ces runes sont plus vieilles que mon clan. Qu'une de vos érudites de la surface essaie de les lire."),
      [("emerald", 12), ("experience_bottle", 10)], 90, to="scholar", after="elder_skeletons"),
]
BY_ID = {q.id: q for q in QUESTS}

# parcel names for the deliveries (the sealed item the giver hands over)
PARCELS = {
    "guild_letter": ("Sealed Guild Letter", "Lettre scellée de la Guilde"),
    "scholar_notes": ("Scholar's Notes", "Notes de l'érudite"),
    "tinker_parts": ("Crate of Spare Parts", "Caisse de pièces détachées"),
    "druid_gift": ("Pouch of World Tree Seeds", "Bourse de graines de l'Arbre-monde"),
    "elder_runes": ("Rune Tablet", "Tablette runique"),
}

# GUI and message strings of the NPC screen and the contracts
TEXT = {
    "entity.brasshaven.wayfarer_npc": ("Wayfarer Quest Giver", "Donneur de contrats"),
    "chapter.brasshaven.contracts": ("Contracts", "Contrats"),
    "npc.brasshaven.display": ("%s, %s", "%s, %s"),
    "gui.brasshaven.npc.contracts": ("Contracts", "Contrats"),
    "gui.brasshaven.npc.accept": ("Accept", "Accepter"),
    "gui.brasshaven.npc.turn_in": ("Turn in", "Rendre"),
    "gui.brasshaven.npc.deliver": ("Hand over", "Remettre"),
    "gui.brasshaven.npc.track": ("Track", "Suivre"),
    "gui.brasshaven.npc.untrack": ("Stop tracking", "Ne plus suivre"),
    "gui.brasshaven.npc.parcel": ("Ask for the parcel again", "Redemander le colis"),
    "gui.brasshaven.npc.close": ("Goodbye", "Au revoir"),
    "gui.brasshaven.npc.state.available": ("New", "Nouveau"),
    "gui.brasshaven.npc.state.active": ("In progress", "En cours"),
    "gui.brasshaven.npc.state.ready": ("Ready to turn in", "Prêt à rendre"),
    "gui.brasshaven.npc.state.done": ("Completed", "Terminé"),
    "gui.brasshaven.npc.state.locked": ("Later", "Plus tard"),
    "gui.brasshaven.npc.state.delivery": ("Delivery for me", "Livraison pour moi"),
    "gui.brasshaven.npc.progress": ("Progress: %s / %s", "Progression : %s / %s"),
    "gui.brasshaven.npc.from": ("From: %s", "De : %s"),
    "gui.brasshaven.npc.to": ("Deliver to: %s", "À livrer à : %s"),
    "gui.brasshaven.npc.none": ("Nothing to offer right now.", "Rien à proposer pour l'instant."),
    "gui.brasshaven.npc.after": ("First finish: %s", "Termine d'abord : %s"),
    "gui.brasshaven.quests.contracts": ("Contracts", "Contrats"),
    "gui.brasshaven.quests.contracts.empty": ("No contract yet. Talk to a Guild Agent, a Scholar, a Tinkerer, a Druid or a Dwarf Elder.",
                                             "Aucun contrat. Parle à un agent de la Guilde, une érudite, un bricoleur, une druidesse ou un ancien nain."),
    "message.brasshaven.npc.accepted": ("Contract accepted: %s", "Contrat accepté : %s"),
    "message.brasshaven.npc.completed": ("Contract completed: %s", "Contrat rempli : %s"),
    "message.brasshaven.npc.progress": ("%s: %s / %s", "%s : %s / %s"),
    "message.brasshaven.npc.explored": ("%s: done! Go back to the giver.", "%s : fait ! Retourne voir le commanditaire."),
    "message.brasshaven.npc.missing": ("You do not have everything yet.", "Il te manque encore quelque chose."),
    "message.brasshaven.npc.parcel": ("You received: %s", "Tu as reçu : %s"),
    "message.brasshaven.npc.too_far": ("Too far away.", "Trop loin."),
    "message.brasshaven.npc.removed": ("Removed %s NPC(s).", "%s PNJ retiré(s)."),
    "message.brasshaven.npc.moved": ("%s moved here.", "%s a été déplacé ici."),
    "message.brasshaven.npc.spawned": ("%s placed here.", "%s placé ici."),
    "message.brasshaven.npc.none_near": ("No NPC within 8 blocks.", "Aucun PNJ à moins de 8 blocs."),
    "message.brasshaven.npc.reset": ("Contracts of %s reset.", "Contrats de %s remis à zéro."),
    "message.brasshaven.npc.parcel.lore": ("Deliver to: %s", "À livrer à : %s"),
}


def title_key(qid):
    return f"npcquest.brasshaven.{qid}.title"


def lang():
    """(en, fr) translation dicts for the NPCs and their contracts."""
    en, fr = {}, {}
    for k, (e, f) in TEXT.items():
        en[k], fr[k] = e, f
    for r, (e, f, names) in ROLES.items():
        en[f"npc.brasshaven.role.{r}"], fr[f"npc.brasshaven.role.{r}"] = e, f
        te, tf, ne, nf = TALK[r]
        en[f"npc.brasshaven.greet.{r}"], fr[f"npc.brasshaven.greet.{r}"] = te, tf
        en[f"npc.brasshaven.idle.{r}"], fr[f"npc.brasshaven.idle.{r}"] = ne, nf
    for q in QUESTS:
        base = f"npcquest.brasshaven.{q.id}"
        en[base + ".title"], fr[base + ".title"] = q.title
        en[base + ".description"], fr[base + ".description"] = q.desc
        en[base + ".story"], fr[base + ".story"] = q.story
    for qid, (e, f) in PARCELS.items():
        en[f"npcquest.brasshaven.{qid}.parcel"], fr[f"npcquest.brasshaven.{qid}.parcel"] = e, f
    return en, fr


def journal_rewards():
    """quest_info.json entries for the journal (keys "npc/<id>"), same shape as the advancement quests."""
    return {f"npc/{q.id}": {"xp": q.xp, "items": q.rewards} for q in QUESTS}


def check():
    """Sanity of the contract table (raises ValueError)."""
    for q in QUESTS:
        if q.giver not in ROLES:
            raise ValueError(f"{q.id}: unknown giver {q.giver}")
        if q.kind not in ("fetch", "hunt", "explore", "deliver"):
            raise ValueError(f"{q.id}: unknown kind {q.kind}")
        if q.kind == "deliver" and (q.to not in ROLES or q.to == q.giver or q.id not in PARCELS):
            raise ValueError(f"{q.id}: a delivery needs another role to deliver to and a parcel name")
        if q.after and (q.after not in BY_ID or BY_ID[q.after].giver != q.giver):
            raise ValueError(f"{q.id}: 'after' must name a contract of the same giver")
        if q.count < 1:
            raise ValueError(f"{q.id}: count must be >= 1")


def java():
    """Source of com.brasshaven.generated.GeneratedNpcs."""
    check()
    roles = ", ".join(f'"{r}"' for r in ROLE_ORDER)
    names = ",\n            ".join("List.of(" + ", ".join(f'"{n}"' for n in ROLES[r][2]) + ")" for r in ROLE_ORDER)
    qs = []
    for q in QUESTS:
        rewards = ", ".join(f'new Reward("{i}", {c})' for i, c in q.rewards)
        qs.append(f'            new Quest("{q.id}", "{q.giver}", Kind.{q.kind.upper()}, "{q.target or ""}", {q.count}, '
                  f'"{q.to or ""}", "{q.after or ""}", "{q.icon}", {q.xp}, List.of({rewards}))')
    return f"""package com.brasshaven.generated;

import java.util.List;

/** GENERATED by tools/gen_java.py from tools/wf/npcs.py: quest-giver roles and their contracts. Do not edit. */
public final class GeneratedNpcs {{
    public enum Kind {{ FETCH, HUNT, EXPLORE, DELIVER }}

    public record Reward(String item, int count) {{}}

    /**
     * A contract: {{@code target}} is an item (fetch), an entity type (hunt) or a structure (explore); {{@code to}} the
     * role a delivery goes to; {{@code after}} the contract of the same giver to finish first ("" for none).
     */
    public record Quest(String id, String giver, Kind kind, String target, int count, String to, String after,
                        String icon, int xp, List<Reward> rewards) {{}}

    /** Role ids, in the order of the model's texture variants (tools/wf/mobs/wayfarer_npc.py). */
    public static final List<String> ROLES = List.of({roles});

    /** Given names of each role (same order as ROLES). */
    public static final List<List<String>> NAMES = List.of(
            {names});

    public static final List<Quest> QUESTS = List.of(
{(","+chr(10)).join(qs)}
    );

    private GeneratedNpcs() {{}}
}}
"""

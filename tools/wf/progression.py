"""The progression ladder: the order in which a newcomer is guided through the game, one step at a time.

One source of truth for:
  * tools/gen_java.py   GeneratedContent.LADDER (the HUD tracker follows it, /brasshaven atlas names its next step)
                        and GeneratedContent.STARTER_KIT (what a player receives on first join)
  * tools/validate.py   every step names a real quest (advancement) or a quest giver's contract, the compass is
                        not handed out before its step, its recipe needs a later material
  * docs/PROGRESSION.md the same ladder written out for players and admins (kept by hand, checked by validate.py)

A step is either an advancement quest ("first_steps/guild_outpost", shared by the group when quests.shareProgress is
on) or a contract "npc/<id>" (always per player: each player earns its rewards for themselves, so a newcomer on an
old server still earns the Structure Compass). The tracker shows the first step the player has not done yet.
"""

# what a player receives on first join (item ids, without namespace): the manual, and the Atlas (quest journal and
# world map, the very things that guide them). Everything else is earned along the ladder.
STARTER_KIT = ["wayfarer_manual", "wayfarer_atlas"]

# the contract whose reward is the Structure Compass, and the Guild Agent contracts before it
COMPASS_CONTRACT = "guild_survey"

# (step, what unlocks there, for the docs). Order matters: the tracker always shows the first unfinished step.
LADDER = [
    ("first_steps/guild_outpost", "map fragments; the Guild Agent's contracts"),
    ("npc/guild_provisions", "emeralds, map fragments"),
    ("npc/" + COMPASS_CONTRACT, "the Structure Compass"),
    ("first_steps/map_fragment", ""),
    ("first_steps/backpack", "Travel Backpack"),
    ("first_steps/waystone", "a waystone of your own (travel between waystones)"),
    ("first_steps/blade", "Cartographer's Blade"),
    ("first_steps/explorer_armor", "Explorer set"),
    ("depths/lithite", "lithite gear; more Structure Compasses can be crafted"),
    ("depths/sunken_citadel", ""),
    ("nether/enter", ""),
    ("nether/ancient_ember", "ember gear"),
    ("end/enter", ""),
    ("end/void_shard", "void gear"),
    ("end/void_warden", ""),
]


def steps():
    return [s for s, _u in LADDER]

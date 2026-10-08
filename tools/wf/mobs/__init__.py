"""Custom-model creatures: each module exposes build() -> wf.models.Model."""
from . import drowned_warden
from . import bell_keeper
from . import archivist
from . import sand_pharaoh
from . import jade_jaguar
from . import root_mother
from . import swamp_crone
from . import gryphon_knight
from . import rune_colossus
from . import forge_king
from . import crystal_spider
from . import sculk_spawn
from . import ash_lord
from . import piglin_king
from . import soul_reaper
from . import void_warden
from . import skeleton_knight
from . import crypt_crawler
from . import banshee
from . import gargoyle
from . import ember_imp
from . import void_larva
from . import grave_knight
from . import bone_matriarch
from . import weeping_lady
from . import larva_mother
from . import ruin_walker
from . import map_wraith
from . import basalt_guard
from . import void_stalker
from . import clockwork_spider
from . import steam_drone
from . import brass_golem
from . import grand_clockmaker
from . import iron_helmsman
# living oceans
from . import glow_jellyfish
from . import reef_fish
from . import manta_ray
from . import sea_serpent
from . import whale
# quest givers
from . import wayfarer_npc
# peoples and creatures of the places (wf/denizens.py)
from . import dwarf
from . import sylvan
from . import clockwork_citizen
from . import monk
from . import bandit_marksman
from . import sky_raider
from . import barnacle_crab
from . import lantern_wisp
from . import cinder_hound
from . import rift_sentinel

MODELS = [
    drowned_warden.build,
    bell_keeper.build,
    archivist.build,
    sand_pharaoh.build,
    jade_jaguar.build,
    root_mother.build,
    swamp_crone.build,
    gryphon_knight.build,
    rune_colossus.build,
    forge_king.build,
    crystal_spider.build,
    sculk_spawn.build,
    ash_lord.build,
    piglin_king.build,
    soul_reaper.build,
    void_warden.build,
    skeleton_knight.build,
    crypt_crawler.build,
    banshee.build,
    gargoyle.build,
    ember_imp.build,
    void_larva.build,
    grave_knight.build,
    bone_matriarch.build,
    weeping_lady.build,
    larva_mother.build,
    ruin_walker.build,
    map_wraith.build,
    basalt_guard.build,
    void_stalker.build,
    clockwork_spider.build,
    steam_drone.build,
    brass_golem.build,
    grand_clockmaker.build,
    iron_helmsman.build,
    glow_jellyfish.build,
    reef_fish.build,
    manta_ray.build,
    sea_serpent.build,
    whale.build,
    wayfarer_npc.build,
    dwarf.build,
    sylvan.build,
    clockwork_citizen.build,
    monk.build,
    bandit_marksman.build,
    sky_raider.build,
    barnacle_crab.build,
    lantern_wisp.build,
    cinder_hound.build,
    rift_sentinel.build,
]

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
from . import bronze_sentinel
from . import dune_king
from . import fallen_seraph
from . import chained_jailer
from . import frost_jarl
from . import caldera_castellan
from . import oathbound_gatekeeper
from . import storm_ascetic
from . import tide_abbess
from . import abyssal_architect
from . import lock_master
from . import bog_hierophant
from . import strangler_queen
from . import solar_hierarch
from . import drowned_admiral
from . import turbine_tyrant
from . import anvil_warden
from . import colossus_heart
from . import fourth_king
from . import star_curator
from . import mine_baron
from . import chime_abbot
from . import corsair_captain
from . import hollow_cantor
from . import soul_stoker
from . import asylum_director
from . import frost_commodore
from . import spore_alchemist
from . import thorn_gardener
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
from . import frozen_huscarl
from . import magma_sentry
from . import oathbound_statue
from . import tide_wraith
from . import bell_monk
from . import void_acolyte
# second pack of creatures of the colossal structures
from . import sluice_drowned
from . import turbine_automaton
from . import bog_leech_man
from . import abyss_crawler
from . import rust_mite_mother
from . import rust_mite
from . import boiler_gunner
# third pack of creatures of the colossal structures
from . import slag_golem
from . import ink_wraith
from . import star_mote_caller
from . import star_mote
from . import sun_scarab
from . import dart_frog_assassin
from . import drowned_marine

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
    bronze_sentinel.build,
    dune_king.build,
    fallen_seraph.build,
    chained_jailer.build,
    frost_jarl.build,
    caldera_castellan.build,
    oathbound_gatekeeper.build,
    storm_ascetic.build,
    storm_ascetic.build_illusion,
    tide_abbess.build,
    abyssal_architect.build,
    lock_master.build,
    bog_hierophant.build,
    strangler_queen.build,
    strangler_queen.build_spirit,
    solar_hierarch.build,
    drowned_admiral.build,
    turbine_tyrant.build,
    anvil_warden.build,
    colossus_heart.build,
    fourth_king.build,
    star_curator.build,
    mine_baron.build,
    chime_abbot.build,
    corsair_captain.build,
    hollow_cantor.build,
    soul_stoker.build,
    asylum_director.build,
    frost_commodore.build,
    spore_alchemist.build,
    thorn_gardener.build,
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
    frozen_huscarl.build,
    magma_sentry.build,
    oathbound_statue.build,
    tide_wraith.build,
    bell_monk.build,
    void_acolyte.build,
    sluice_drowned.build,
    turbine_automaton.build,
    bog_leech_man.build,
    abyss_crawler.build,
    rust_mite_mother.build,
    rust_mite.build,
    boiler_gunner.build,
    slag_golem.build,
    ink_wraith.build,
    star_mote_caller.build,
    star_mote.build,
    sun_scarab.build,
    dart_frog_assassin.build,
    drowned_marine.build,
]

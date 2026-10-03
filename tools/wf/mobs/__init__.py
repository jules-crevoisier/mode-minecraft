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
]

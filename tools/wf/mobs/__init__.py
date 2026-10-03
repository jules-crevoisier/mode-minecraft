"""Custom-model creatures: each module exposes build() -> wf.models.Model."""
from . import drowned_warden

MODELS = [
    drowned_warden.build,
]

"""Structure definitions registry + worldgen JSON emission."""
import hashlib

MODID = "wayfarers"
STRUCTURES = []


class Piece:
    def __init__(self, name, builder, weight=1, processors=None, projection="rigid"):
        self.name = name
        self.builder = builder
        self.weight = weight
        self.processors = processors
        self.projection = projection
        self.blueprint = None


class StructureDef:
    def __init__(self, sid, dimension, biomes, pieces, spacing=32, separation=10,
                 step="surface_structures", adaptation="beard_thin", heightmap="WORLD_SURFACE_WG",
                 height_offset=0, height=None, size=1, extra_pools=None, processors="aging",
                 max_distance=80, exclusion=None, title_fr="", title_en="", ground=0):
        self.id = sid
        self.dimension = dimension
        self.biomes = biomes
        self.pieces = pieces  # start pool pieces
        self.extra_pools = extra_pools or {}  # pool name -> [Piece]
        self.spacing = spacing
        self.separation = separation
        self.step = step
        self.adaptation = adaptation
        self.heightmap = heightmap
        self.height_offset = height_offset  # extra blocks above the ground (sky islands...)
        self.height = height  # explicit start_height (no heightmap), e.g. ("uniform", -40, 0)
        self.size = size
        self.processors = processors
        self.max_distance = max_distance
        self.exclusion = exclusion
        self.title_fr = title_fr
        self.title_en = title_en
        self.ground = ground  # blueprint y that must sit on the ground surface

    @property
    def salt(self):
        return int(hashlib.sha1(self.id.encode()).hexdigest()[:7], 16)


def register(sdef):
    STRUCTURES.append(sdef)
    return sdef


def rl(path):
    return f"{MODID}:{path}"


# ------------------------------------------------------------------ JSON builders

def processor_list(kind):
    rules = {
        "aging": [
            ("minecraft:stone_bricks", 0.22, "minecraft:cracked_stone_bricks"),
            ("minecraft:stone_bricks", 0.18, "minecraft:mossy_stone_bricks"),
            ("minecraft:cobblestone", 0.25, "minecraft:mossy_cobblestone"),
            ("minecraft:stone_brick_stairs", 0.15, "minecraft:mossy_stone_brick_stairs"),
            ("minecraft:polished_blackstone_bricks", 0.2, "minecraft:cracked_polished_blackstone_bricks"),
            ("minecraft:nether_bricks", 0.15, "minecraft:cracked_nether_bricks"),
            ("minecraft:deepslate_bricks", 0.2, "minecraft:cracked_deepslate_bricks"),
            ("minecraft:deepslate_tiles", 0.15, "minecraft:cracked_deepslate_tiles"),
            ("minecraft:end_stone_bricks", 0.15, "minecraft:end_stone"),
            ("minecraft:sandstone", 0.12, "minecraft:smooth_sandstone"),
        ],
        "ruin": [
            ("minecraft:stone_bricks", 0.3, "minecraft:cracked_stone_bricks"),
            ("minecraft:stone_bricks", 0.3, "minecraft:mossy_stone_bricks"),
            ("minecraft:cobblestone", 0.4, "minecraft:mossy_cobblestone"),
            ("minecraft:stone_bricks", 0.06, "minecraft:air"),
            ("minecraft:cobblestone", 0.06, "minecraft:air"),
        ],
        "none": [],
    }[kind]
    processors = [{
        "processor_type": "minecraft:protected_blocks",
        "value": "#minecraft:features_cannot_replace",
    }]
    if rules:
        processors.insert(0, {
            "processor_type": "minecraft:rule",
            "rules": [{
                "input_predicate": {"predicate_type": "minecraft:random_block_match", "block": b, "probability": p},
                "location_predicate": {"predicate_type": "minecraft:always_true"},
                "output_state": {"Name": out},
            } for b, p, out in rules],
        })
    return {"processors": processors}


def template_pool(sdef, pieces, pool_name):
    return {
        "fallback": "minecraft:empty",
        "elements": [{
            "weight": p.weight,
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": rl(f"{sdef.id}/{p.name}"),
                "projection": p.projection,
                "processors": rl(p.processors or sdef.processors),
            },
        } for p in pieces],
    }


def structure_json(sdef, ground_offset):
    js = {
        "type": "minecraft:jigsaw",
        "biomes": f"#{rl('has_structure/' + sdef.id)}",
        "step": sdef.step,
        "spawn_overrides": {},
        "terrain_adaptation": sdef.adaptation,
        "start_pool": rl(f"{sdef.id}/start"),
        "size": sdef.size,
        "max_distance_from_center": sdef.max_distance,
        "use_expansion_hack": False,
    }
    if sdef.height is not None:
        kind = sdef.height[0]
        if kind == "absolute":
            js["start_height"] = {"absolute": sdef.height[1]}
        else:
            js["start_height"] = {"type": "minecraft:uniform",
                                  "min_inclusive": {"absolute": sdef.height[1]},
                                  "max_inclusive": {"absolute": sdef.height[2]}}
    else:
        js["start_height"] = {"absolute": ground_offset + sdef.height_offset}
        js["project_start_to_heightmap"] = sdef.heightmap
    return js


def structure_set_json(sdef):
    placement = {
        "type": "minecraft:random_spread",
        "salt": sdef.salt,
        "spacing": sdef.spacing,
        "separation": sdef.separation,
    }
    if sdef.exclusion:
        placement["exclusion_zone"] = {"other_set": sdef.exclusion[0], "chunk_count": sdef.exclusion[1]}
    return {"structures": [{"structure": rl(sdef.id), "weight": 1}], "placement": placement}


def biome_tag_json(biomes):
    values = []
    for b in biomes:
        if b.startswith("#"):
            values.append({"id": b, "required": False})
        else:
            values.append({"id": b if ":" in b else "minecraft:" + b, "required": False})
    return {"replace": False, "values": values}

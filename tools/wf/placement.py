"""Where structures generate: families of structures sharing one structure set, their spacing, the zones they keep
away from, and the terrain-fit overrides. The ONE place to tune placement (gen_structures.py applies it; the
``spacing``/``separation`` arguments of ``StructureDef`` are only a fallback for a structure missing here).

Families
    Similar structures share one structure set with weighted entries, like vanilla villages: the set's grid
    yields at most one start per cell, the game picks a member by weight among those whose biome fits (it tries
    the others when the first pick's biome does not), so a family never stacks two of its members and the
    members alternate instead of repeating. In a biome where k members fit with total weight W_b, one member of
    weight w comes back about every ``spacing * sqrt(W_b / w)`` chunks; alone in its biome, every ``spacing``.

Placement type
    ``wayfarers:curated_spread`` (com.wayfarers.world.CuratedSpreadPlacement) is vanilla ``random_spread`` plus
    ``avoid`` (several exclusion zones instead of vanilla's single ``exclusion_zone``) and ``min_spawn_distance``.
    Like vanilla exclusion zones, ``avoid`` tests the other set's grid positions without looking at biomes, so
    each zone costs a family about ``(2r+1)^2 / spacing_other^2`` of its cells; radii stay modest for that reason.
    The avoid graph must stay acyclic (checked): a family only avoids families declared before it.

Terrain fit
    Surface templates carry foundations, skirts and cellars below their ground layer. Vanilla elements tell the
    jigsaw "ground = lowest layer + 1", which is where the beardifier flattens the terrain; for our templates that
    was up to 12 blocks under the real ground, so beard_thin dug a moat around every structure (the "castle
    floating over a crater"). gen_structures now writes every start piece of a heightmap-projected structure as a
    ``wayfarers:chunked_template`` element (one column when small) with ``ground_level_delta`` = depth of the
    ground layer + 1, and the structure's start height no longer subtracts that depth.
    ``carve_limit`` then drops template air that would only carve hills: air above the ground layer in columns with
    nothing built, and air more than ``KEEP_AIR`` blocks above the highest built block of its column.

Site selection (FIT)
    Every structure is a ``wayfarers:fitted_jigsaw`` (com.wayfarers.world.FittedJigsawStructure): a vanilla jigsaw
    whose start is first checked against the real terrain, sampled with ``ChunkGenerator.getBaseHeight``
    (WORLD_SURFACE_WG and OCEAN_FLOOR_WG) on a grid over the structure's footprint (corners, edges, centre, up to
    7 x 7 points). A site that does not fit is rejected like a cell with the wrong biome: the grid cell stays empty
    and ``/locate`` moves on to the next one, so nothing has to know about it. Modes (see ``FIT`` below):

    land       dry ground: height spread <= ``spread``, steepest step between two neighbouring samples <= ``slope``
               (rise over run), at most ``wet`` of the samples under water. The start is moved to the median ground
               height of the footprint (never more than ``drop`` above its lowest sample, which the foundations
               reach), instead of the height of its centre column.
    wetland    land where water counts as ground (swamp huts on stilts): heights are the water surface, and at least
               ``min_wet`` of the samples must be water (a template pond on dry land is a square pool).
    coast      the template's ``sea_side`` (after rotation) must be water (>= ``wet`` of the samples there) and the
               opposite side land (>= ``land``), the shore at most ``spread`` above the sea; the ground layer lands
               one block above the sea surface.
    seabed     under water (>= ``wet`` of the samples, median depth >= ``depth``), flat enough sea floor.
    sky        fixed absolute height; the terrain under the footprint must stay ``clearance`` blocks below the
               structure's underside (it may rise by up to ``lift`` blocks to get there).
    underground  fixed height; at least ``cover`` blocks of rock between its top and the lowest ground (or sea
               floor) above it (it may sink by up to ``lift``).
    cavern     Nether: at least ``open`` of the samples are open (air or lava) just above the deck.
"""
import hashlib
import json
import math
import os

from . import defs

AIR = {"minecraft:air", "minecraft:cave_air"}
KEEP_AIR = 4          # headroom of air kept above the highest built block of a column (doors, yards, paths)
WONDER_RADIUS = 10    # chunks: nothing else starts this close to a wonder


class Family:
    def __init__(self, sid, cls, spacing, separation, members, avoid=(), min_spawn=0, note=""):
        self.id = sid
        self.cls = cls
        self.spacing = spacing
        self.separation = separation
        self.members = dict(members)  # structure id -> weight
        self.avoid = list(avoid)      # (structure set id, chunks)
        self.min_spawn = min_spawn    # chunks from 0,0
        self.note = note

    @property
    def salt(self):
        return int(hashlib.sha1(("set/" + self.id).encode()).hexdigest()[:7], 16)

    @property
    def rl(self):
        return defs.rl(self.id)


# class -> (minimum set spacing, minimum per-type spacing in chunks, worst biome)
CLASSES = {
    "small": (40, 40),
    "medium": (56, 56),
    "dungeon": (56, 56),
    "coast": (40, 40),
    "wonder": (120, 120),
    "deep": (40, 40),
    "deep_wonder": (72, 120),
    "ocean_small": (32, 36),
    "ocean_large": (56, 56),
    "nether": (30, 30),
    "end": (32, 32),
}

V = "minecraft:"
W = defs.rl("wonders")
DW = defs.rl("deep_wonders")
L = defs.rl("landmarks")
D = defs.rl("dungeons")
C = defs.rl("coast")
OR = defs.rl("ocean_ruins")
NL = defs.rl("nether_large")
EL = defs.rl("end_large")

# Declaration order = avoid order: a family only avoids vanilla sets and families above it.
FAMILIES = [
    Family("wonders", "wonder", 120, 40, {
        "clockwork_citadel": 1, "sky_harbour": 1, "sylvan_palace": 1, "inventor_manor": 1, "sky_isles": 1,
        "geothermal_foundry": 1, "tesla_observatory": 1,
    }, avoid=[(V + "villages", 10), (V + "pillager_outposts", 6), (V + "woodland_mansions", 8)], min_spawn=32,
        note="surface wonders; at least 40 chunks between two of them, none within 512 blocks of 0,0"),
    Family("deep_wonders", "deep_wonder", 72, 28, {
        "undercity": 1, "dwarven_city": 1, "crystal_cathedral": 1,
    }, avoid=[(V + "ancient_cities", 8), (V + "trial_chambers", 4)], min_spawn=32,
        note="underground wonders"),
    Family("landmarks", "medium", 60, 24, {
        "guild_outpost": 3, "forgotten_library": 2, "mountain_monastery": 2, "ice_observatory": 2,
        "jungle_ziggurat": 2, "sky_island": 2, "dwarven_mine": 2,
    }, avoid=[(W, WONDER_RADIUS), (V + "villages", 6), (V + "woodland_mansions", 6)],
        note="medium buildings"),
    Family("dungeons", "dungeon", 60, 24, {
        "forgotten_catacombs": 1, "sand_hypogeum": 1, "lithite_well": 1,
    }, avoid=[(W, WONDER_RADIUS), (DW, 8), (V + "villages", 4), (L, 6)],
        note="surface entrance, random layout among three"),
    Family("coast", "coast", 44, 16, {
        "coastal_lighthouse": 1,
    }, avoid=[(W, WONDER_RADIUS), (V + "villages", 4), (L, 6)],
        note="beaches only: real spacing is several times the grid"),
    Family("wayside", "small", 40, 16, {
        "ruined_watchtower": 3, "rune_circle": 2, "bandit_camp": 2, "giant_tree": 2, "witch_huts": 2,
        "desert_oasis": 2,
    }, avoid=[(W, WONDER_RADIUS), (V + "villages", 4), (L, 6), (D, 5), (C, 3)],
        note="small sights along the way"),
    Family("ocean_ruins", "ocean_large", 60, 24, {
        "sunken_temple": 2, "sunken_citadel": 1,
    }, avoid=[(W, WONDER_RADIUS), (V + "ocean_monuments", 8)]),
    Family("ocean_wrecks", "ocean_small", 32, 12, {
        "galleon_wreck": 3, "shipwreck_debris": 3, "diving_bell": 2, "sunken_submarine": 2, "coral_shrine": 2,
    }, avoid=[(W, WONDER_RADIUS), (OR, 5), (V + "ocean_monuments", 4), (C, 3)]),
    Family("caverns", "deep", 40, 14, {
        "crystal_grotto": 3, "dwarven_forge": 2, "sealed_lab": 2,
    }, avoid=[(DW, WONDER_RADIUS), (V + "ancient_cities", 4), (D, 5)]),
    Family("nether_large", "nether", 36, 12, {
        "basalt_fortress": 2, "piglin_sanctuary": 2, "piglin_market": 2, "lava_foundry": 2,
    }, avoid=[(V + "nether_complexes", 4)]),
    Family("nether_small", "nether", 30, 10, {
        "chain_bridge": 2, "soul_tower": 2,
    }, avoid=[(NL, 5), (V + "nether_complexes", 3)]),
    Family("end_large", "end", 40, 14, {
        "end_archive": 2, "void_crypt": 2, "void_nest": 1,
    }, avoid=[(V + "end_cities", 4)]),
    Family("end_small", "end", 32, 10, {
        "chorus_garden": 3, "void_observatory": 2, "void_ship": 2,
    }, avoid=[(EL, 5), (V + "end_cities", 3)]),
]

# Terrain adaptation overrides (structure id -> terrain_adaptation). Surface structures default to beard_thin;
# beard_box carves the whole box (towers included) out of any hill, so it is kept for underwater temples only.
ADAPTATION = {
    "clockwork_citadel": "beard_thin",   # was beard_box: cut a canyon the height of its towers through mesas
    "coastal_lighthouse": "none",        # sits on the shore as is: a beard would fill the sea around its cape
    "sky_island": "beard_thin",          # its ground shrine and waterfall pool blend in; the islands float above
}

# Biome list overrides (structure id -> biomes), applied before the tags are written. Kept here so the whole
# "where does it go" decision is in one file; validate.py checks the theme rules (check_fit).
BIOMES = {
    # grass-topped hillside settlement: mountains, hills and taiga, not the red mesas (badlands have the citadel,
    # the foundry and the hypogeum)
    "dwarven_mine": ["#minecraft:is_mountain", "#minecraft:is_hill", "windswept_hills", "windswept_gravelly_hills",
                     "#minecraft:is_taiga"],
}

# ------------------------------------------------------------------ site fit (see "Site selection" above)
FIT_MODES = ("land", "wetland", "coast", "seabed", "sky", "underground", "cavern")
FOUNDATION_DEPTH = 12   # wf/foundation.py: how far the foundations reach below the ground layer
DEFAULT_DROP = 10       # land: the start never sits more than this above the lowest sample (foundations reach it)


def _f(mode, **kw):
    return dict(mode=mode, **kw)


FIT = {
    # ---- overworld land: spread (blocks), slope (rise/run between neighbouring samples), wet (max water share)
    "guild_outpost": _f("land", spread=13, slope=1.0, wet=0.12),
    "mountain_monastery": _f("land", spread=26, slope=1.3, wet=0.12),   # rock plinth 30 deep: made for slopes
    "forgotten_library": _f("land", spread=16, slope=1.0, wet=0.12),
    "giant_tree": _f("land", spread=19, slope=1.2, wet=0.12),           # roots reach down on their own
    "desert_oasis": _f("land", spread=13, slope=0.9, wet=0.12),
    "witch_huts": _f("wetland", spread=5, slope=0.5, wet=0.9, min_wet=0.2),  # stilts over a real marsh
    "sky_island": _f("land", spread=22, slope=1.1, wet=0.12),            # ground shrine + pool under the islands
    "jungle_ziggurat": _f("land", spread=19, slope=1.1, wet=0.12),
    "ruined_watchtower": _f("land", spread=16, slope=1.2, wet=0.12),
    "bandit_camp": _f("land", spread=13, slope=1.0, wet=0.12),
    "rune_circle": _f("land", spread=13, slope=0.9, wet=0.12),
    "ice_observatory": _f("land", spread=16, slope=1.1, wet=0.12),
    "dwarven_mine": _f("land", spread=35, slope=1.6, wet=0.12),         # a hillside settlement: wants a slope
    "forgotten_catacombs": _f("land", spread=12, slope=0.9, wet=0.04),    # footprint = the mausoleum on top
    "sand_hypogeum": _f("land", spread=12, slope=0.9, wet=0.04),
    "lithite_well": _f("land", spread=13, slope=1.2, wet=0.04),
    "clockwork_citadel": _f("land", spread=22, slope=0.8, wet=0.12),
    "sky_harbour": _f("land", spread=19, slope=1.1, wet=0.12),
    "sylvan_palace": _f("land", spread=22, slope=1.0, wet=0.12),
    "inventor_manor": _f("land", spread=16, slope=0.9, wet=0.12),
    "geothermal_foundry": _f("land", spread=26, slope=1.0, wet=0.12),
    "tesla_observatory": _f("land", spread=32, slope=1.3, wet=0.12),    # terraced mountain campus
    # ---- coast: the dock side (template +z = south) in the sea, the cape on land, shore near sea level
    "coastal_lighthouse": _f("coast", sea_side="south", wet=0.5, land=0.5, spread=8, slope=1.0),
    # ---- sea floor: wet share, median water depth, floor spread
    "galleon_wreck": _f("seabed", wet=0.7, depth=4, spread=8, slope=0.6),
    "sunken_temple": _f("seabed", wet=0.95, depth=6, spread=10, slope=0.6),
    "sunken_citadel": _f("seabed", wet=0.95, depth=10, spread=12, slope=0.6),
    "sunken_submarine": _f("seabed", wet=0.95, depth=6, spread=5, slope=0.6),
    "diving_bell": _f("seabed", wet=0.95, depth=6, spread=4, slope=0.6),
    "coral_shrine": _f("seabed", wet=0.95, depth=4, spread=4, slope=0.6),
    "shipwreck_debris": _f("seabed", wet=0.6, depth=2, spread=4, slope=0.7),
    # ---- sky: fixed height, the terrain stays this far below the underside
    "sky_isles": _f("sky", clearance=24, lift=0),
    # ---- underground: rock cover above the top
    "dwarven_forge": _f("underground", cover=8, lift=4),
    "crystal_grotto": _f("underground", cover=8, lift=4),
    "sealed_lab": _f("underground", cover=8, lift=4),
    "undercity": _f("underground", cover=10, lift=6),
    "dwarven_city": _f("underground", cover=10, lift=2),
    "crystal_cathedral": _f("underground", cover=10, lift=6),
    # ---- Nether: open air (or the lava sea) above the deck
    "basalt_fortress": _f("cavern", open=0.3),
    "chain_bridge": _f("cavern", open=0.6),
    "piglin_sanctuary": _f("cavern", open=0.3),
    "lava_foundry": _f("cavern", open=0.5),
    "soul_tower": _f("cavern", open=0.3),
    "piglin_market": _f("cavern", open=0.3),
    # ---- End: monuments floating over the void beside the outer islands; they rise above an island in the way
    "void_observatory": _f("sky", clearance=4, lift=32),
    "chorus_garden": _f("sky", clearance=4, lift=32),
    "end_archive": _f("sky", clearance=4, lift=32),
    "void_ship": _f("sky", clearance=4, lift=32),
    "void_nest": _f("sky", clearance=4, lift=32),
    "void_crypt": _f("land", spread=6, slope=0.7, wet=0.0),            # mausoleum on an End island
}

# Biome groups for the theme checks
ARID = {"desert", "badlands", "eroded_badlands", "wooded_badlands"}
PEAKS = {"frozen_peaks", "jagged_peaks", "stony_peaks"}
COLD = {"snowy_plains", "ice_spikes", "snowy_taiga", "grove", "snowy_slopes", "frozen_peaks", "jagged_peaks",
        "snowy_beach", "frozen_river", "frozen_ocean", "deep_frozen_ocean"}
WATERY = {"ocean", "deep_ocean", "cold_ocean", "deep_cold_ocean", "lukewarm_ocean", "deep_lukewarm_ocean",
          "warm_ocean", "frozen_ocean", "deep_frozen_ocean", "river", "frozen_river"}
SHORE = {"beach", "snowy_beach", "stony_shore"}
GRASSY = {"grass_block", "podzol", "moss_block", "coarse_dirt", "dirt_path", "mycelium", "rooted_dirt", "dirt"}
SANDY = {"sand", "red_sand", "sandstone", "smooth_sandstone", "cut_sandstone", "red_sandstone"}
SNOWY = {"snow_block", "powder_snow", "packed_ice", "ice", "blue_ice"}
# Hidden foundations (wf/foundation.py) switched off: the lighthouse cape already reaches 6 blocks down, and
# its dock would otherwise stand on a solid wall of cobblestone instead of piles.
FOUNDATION = {
    "coastal_lighthouse": False,
}

VANILLA_SETS = {"villages", "desert_pyramids", "igloos", "jungle_temples", "swamp_huts", "pillager_outposts",
                "ocean_monuments", "woodland_mansions", "buried_treasures", "mineshafts", "ruined_portals",
                "shipwrecks", "ocean_ruins", "nether_complexes", "nether_fossils", "end_cities", "ancient_cities",
                "strongholds", "trail_ruins", "trial_chambers"}


# ------------------------------------------------------------------ families
def families():
    """FAMILIES plus a one-member fallback family for any registered structure missing from the table."""
    out = list(FAMILIES)
    known = {s for f in FAMILIES for s in f.members}
    for sdef in defs.STRUCTURES:
        if sdef.id not in known:
            sp = max(sdef.spacing, 40)
            out.append(Family(sdef.id, "small", sp, min(sdef.separation, sp // 2), {sdef.id: 1},
                              avoid=[(W, WONDER_RADIUS)] if sdef.dimension == "overworld" else [],
                              note="fallback: add it to tools/wf/placement.py"))
    return out


def unassigned():
    known = {s for f in FAMILIES for s in f.members}
    return [s.id for s in defs.STRUCTURES if s.id not in known]


def apply_overrides():
    for sdef in defs.STRUCTURES:
        if sdef.id in ADAPTATION:
            sdef.adaptation = ADAPTATION[sdef.id]
        if sdef.id in FOUNDATION:
            sdef.foundation = FOUNDATION[sdef.id]
        if sdef.id in BIOMES:
            sdef.biomes = list(BIOMES[sdef.id])


# ------------------------------------------------------------------ site fit
def fit_params(sid):
    """FIT entry with every key filled (the defaults the Java codec uses too)."""
    p = dict(spread=8, slope=0.8, wet=0.05, min_wet=0.0, land=0.5, drop=DEFAULT_DROP, depth=0, clearance=0, cover=0, lift=0,
             open=0.0)
    p.update(FIT.get(sid, {"mode": "land"}))
    return p


def ground_info(blocks, ground):
    """From a start template (normalized blocks, ground layer y): the built footprint (x0, z0, x1, z1: columns with
    anything at or above the ground layer), the share of that footprint the template floods itself (ponds,
    fountains, a moat) and the ground theme (grass / sand / snow / stone) for the biome checks."""
    cols = {}
    for (x, y, z), b in blocks.items():
        if y >= ground and b[0] not in AIR:
            cols.setdefault((x, z), []).append((y, b[0]))
    if not cols:
        return None, 0.0, "stone"
    xs = [c[0] for c in cols]
    zs = [c[1] for c in cols]
    fp = (min(xs), min(zs), max(xs), max(zs))
    area = (fp[2] - fp[0] + 1) * (fp[3] - fp[1] + 1)
    wet = sum(1 for c in cols.values() if any(n == "minecraft:water" and y <= ground + 1 for y, n in c))
    top = {}
    for (x, y, z), b in blocks.items():
        if y == ground and b[0] not in AIR:
            s = b[0].split(":")[1]
            kind = "grass" if s in GRASSY else "sand" if s in SANDY else "snow" if s in SNOWY else "stone"
            top[kind] = top.get(kind, 0) + 1
    n = sum(top.values()) or 1
    theme = "stone"
    for kind in ("sand", "snow", "grass"):
        if top.get(kind, 0) >= 0.25 * n:
            theme = kind
            break
    return fp, round(wet / area, 3), theme


def fit_json(sdef, info):
    """The ``fit`` object of a fitted_jigsaw structure. ``info``: {"pond", "ground", "theme"} from gen_structures
    (the footprint of each start template goes on its pool element, ChunkedPoolElement ``footprint``)."""
    p = fit_params(sdef.id)
    js = {"mode": p["mode"]}
    for k in ("spread", "slope", "wet", "min_wet", "land", "drop", "depth", "clearance", "cover", "lift", "open"):
        js[k] = p[k]
    if p.get("sea_side"):
        js["sea_side"] = p["sea_side"]
    if info:
        js["ground"] = info["ground"]
        js["pond"] = info.get("pond", 0.0)
        js["theme"] = info.get("theme", "stone")  # documentation only (validate.py); the game ignores it
    return js


def structure_set_json(fam):
    placement = {
        "type": defs.rl("curated_spread"),
        "salt": fam.salt,
        "spacing": fam.spacing,
        "separation": fam.separation,
    }
    if fam.avoid:
        placement["avoid"] = [{"set": s, "chunks": r} for s, r in fam.avoid]
    if fam.min_spawn:
        placement["min_spawn_distance"] = fam.min_spawn
    return {"structures": [{"structure": defs.rl(sid), "weight": w} for sid, w in fam.members.items()],
            "placement": placement}


def write_sets(ns_dir, write_json):
    """Write every family's structure set and remove the stale ones (the old one-set-per-structure files)."""
    out_dir = os.path.join(ns_dir, "worldgen", "structure_set")
    os.makedirs(out_dir, exist_ok=True)
    keep = set()
    for fam in families():
        write_json(os.path.join(out_dir, fam.id + ".json"), structure_set_json(fam))
        keep.add(fam.id + ".json")
    for f in os.listdir(out_dir):
        if f.endswith(".json") and f not in keep:
            os.remove(os.path.join(out_dir, f))


# ------------------------------------------------------------------ terrain fit
def carve_limit(blocks, ground, keep=KEEP_AIR):
    """Air entries of a surface template that would only carve the terrain around the building: above the ground
    layer, and either in a column with nothing built at or above the ground, or more than ``keep`` blocks above
    the highest built block of the column (normalized coordinates, ``ground`` = ground layer y)."""
    top = {}
    for (x, y, z), b in blocks.items():
        if b[0] not in AIR and y >= ground and y > top.get((x, z), -10 ** 9):
            top[(x, z)] = y
    out = set()
    for p, b in blocks.items():
        if b[0] not in AIR or p[1] <= ground:
            continue
        t = top.get((p[0], p[2]))
        if t is None or p[1] > t + keep:
            out.add(p)
    return out


# ------------------------------------------------------------------ biomes (estimates and checks)
_TAGS = None


def _vanilla_tags():
    global _TAGS
    if _TAGS is None:
        _TAGS = json.load(open(os.path.join(os.path.dirname(__file__), "vanilla_biome_tags.json")))
    return _TAGS


def biome_set(sdef):
    """Vanilla biome ids a structure may start in (tags expanded)."""
    def tag_biomes(name, seen=()):
        tag = _vanilla_tags().get(name)
        if not tag or name in seen:
            return set()
        got = set(tag["biomes"])
        for sub in tag.get("tags", ()):
            got |= tag_biomes(sub.split(":")[-1].lstrip("#"), seen + (name,))
        return got

    out = set()
    for b in sdef.biomes:
        if b.startswith("#"):
            out |= tag_biomes(b.split(":")[-1])
        else:
            out.add(b.split(":")[-1])
    return out


def per_type_spacing(fam, sid):
    """{vanilla biome: chunks between two starts of ``sid`` in that biome} (grid spacing x sqrt(W_b / w))."""
    by_id = {s.id: s for s in defs.STRUCTURES}
    biomes = {m: biome_set(by_id[m]) for m in fam.members if m in by_id}
    out = {}
    for b in biomes.get(sid, ()):
        wb = sum(w for m, w in fam.members.items() if b in biomes.get(m, ()))
        out[b] = fam.spacing * math.sqrt(wb / fam.members[sid])
    return out


def check(data_dir):
    """Placement rules, read back from the written structure sets. Returns a list of error strings."""
    apply_overrides()
    errors = []
    sets = {}
    set_dir = os.path.join(data_dir, defs.MODID, "worldgen", "structure_set")
    for f in sorted(os.listdir(set_dir)):
        if f.endswith(".json"):
            sets[defs.rl(f[:-5])] = json.load(open(os.path.join(set_dir, f)))
    fams = {f.rl: f for f in families()}
    owner = {}
    for rl, js in sets.items():
        for e in js["structures"]:
            if e["structure"] in owner:
                errors.append(f"structure {e['structure']} in two structure sets: {owner[e['structure']]} / {rl}")
            owner[e["structure"]] = rl
    struct_dir = os.path.join(data_dir, defs.MODID, "worldgen", "structure")
    for f in sorted(os.listdir(struct_dir)):
        if f.endswith(".json") and defs.rl(f[:-5]) not in owner:
            errors.append(f"structure {defs.rl(f[:-5])} is in no structure set (it would never generate)")
    # spacing minima
    for rl, js in sets.items():
        p = js["placement"]
        fam = fams.get(rl)
        if fam is None:
            errors.append(f"structure set {rl} is not produced by tools/wf/placement.py (stale file?)")
            continue
        min_set, min_type = CLASSES[fam.cls]
        if p["spacing"] < min_set:
            errors.append(f"structure set {rl}: spacing {p['spacing']} < {min_set} (minimum for {fam.cls})")
        if not 0 < p["separation"] < p["spacing"]:
            errors.append(f"structure set {rl}: separation {p['separation']} must be in 1..spacing-1")
        for sid in fam.members:
            per = per_type_spacing(fam, sid)
            if per and min(per.values()) < min_type:
                b = min(per, key=per.get)
                errors.append(f"{sid}: {per[b]:.0f} chunks between two of them in {b} < {min_type} ({fam.cls})")
    # avoid graph: known targets, no cycle
    graph = {}
    for rl, js in sets.items():
        targets = [a["set"] for a in js["placement"].get("avoid", [])]
        ex = js["placement"].get("exclusion_zone")
        if ex:
            targets.append(ex["other_set"])
        for t in targets:
            ns, name = t.split(":")
            if (ns == "minecraft" and name not in VANILLA_SETS) or (ns == defs.MODID and t not in sets):
                errors.append(f"structure set {rl} avoids unknown set {t}")
        graph[rl] = [t for t in targets if t in sets]
        for a in js["placement"].get("avoid", []):
            if not 1 <= a["chunks"] <= 32:
                errors.append(f"structure set {rl}: avoid radius {a['chunks']} outside 1..32")
    state = {}

    def visit(n, path):
        if state.get(n) == 1:
            errors.append("avoid cycle (the game would recurse forever): " + " -> ".join(path + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for t in graph.get(n, ()):
            visit(t, path + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])
    # wonders: away from spawn, from villages, and nothing else within WONDER_RADIUS
    by_id = {s.id: s for s in defs.STRUCTURES}
    for rl, js in sets.items():
        fam = fams.get(rl)
        if not fam or fam.cls not in ("wonder", "deep_wonder"):
            continue
        p = js["placement"]
        if p.get("min_spawn_distance", 0) < 32:
            errors.append(f"wonder set {rl}: min_spawn_distance {p.get('min_spawn_distance', 0)} < 32 chunks")
        if not p.get("avoid"):
            errors.append(f"wonder set {rl}: no exclusion zone")
        layer = "surface" if fam.cls == "wonder" else "underground"
        for other_rl, other in sets.items():
            ofam = fams.get(other_rl)
            if other_rl == rl or not ofam or ofam.cls in ("wonder", "deep_wonder"):
                continue
            dims = {by_id[s].dimension for s in ofam.members if s in by_id}
            if dims != {"overworld"}:
                continue
            under = all(by_id[s].step == "underground_structures" for s in ofam.members if s in by_id)
            if (layer == "underground") != under:
                continue
            r = {a["set"]: a["chunks"] for a in other["placement"].get("avoid", [])}.get(rl, 0)
            if r < WONDER_RADIUS:
                errors.append(f"structure set {other_rl} may start {r} chunks from a wonder of {rl} "
                              f"(needs avoid {rl} >= {WONDER_RADIUS})")
    return errors


def check_fit(data_dir):
    """Site-fit rules, read back from the written structures (wayfarers:fitted_jigsaw): every structure has a fit
    mode that matches how it is placed, sane tolerances, a footprint inside its templates, a terrain adaptation that
    suits the mode, and biomes that suit its ground (no desert template on snowy peaks, no land building in the
    sea...). Returns a list of error strings."""
    apply_overrides()
    errors = []
    by_id = {s.id: s for s in defs.STRUCTURES}
    for sid in sorted(by_id):
        if sid not in FIT:
            errors.append(f"{sid}: no site-fit entry in tools/wf/placement.py FIT")
    struct_dir = os.path.join(data_dir, defs.MODID, "worldgen", "structure")
    for f in sorted(os.listdir(struct_dir)):
        if not f.endswith(".json"):
            continue
        sid = f[:-5]
        js = json.load(open(os.path.join(struct_dir, f)))
        sdef = by_id.get(sid)
        if js.get("type") != defs.rl("fitted_jigsaw"):
            errors.append(f"{sid}: type {js.get('type')} (every structure is a {defs.rl('fitted_jigsaw')})")
            continue
        fit = js.get("fit")
        if not isinstance(fit, dict) or fit.get("mode") not in FIT_MODES:
            errors.append(f"{sid}: fit.mode must be one of {FIT_MODES}")
            continue
        mode = fit["mode"]
        proj = js.get("project_start_to_heightmap")
        adapt = js.get("terrain_adaptation", "none")
        dim = sdef.dimension if sdef else "overworld"
        want_proj = {"land": "WORLD_SURFACE_WG", "wetland": "WORLD_SURFACE_WG", "coast": "WORLD_SURFACE_WG",
                     "seabed": "OCEAN_FLOOR_WG"}.get(mode)
        if proj != want_proj:
            errors.append(f"{sid}: fit mode {mode} needs project_start_to_heightmap {want_proj}, has {proj}")
        if mode == "cavern" and dim != "nether":
            errors.append(f"{sid}: fit mode cavern is for the Nether")
        if dim == "nether" and mode != "cavern":
            errors.append(f"{sid}: Nether structures use fit mode cavern (the surface heightmap is the roof)")
        if mode == "underground" and (dim != "overworld" or js.get("step") != "underground_structures"):
            errors.append(f"{sid}: fit mode underground needs the overworld and step underground_structures")
        if mode == "sky" and dim not in ("overworld", "end"):
            errors.append(f"{sid}: fit mode sky is for the overworld and the End")
        # tolerances
        rng = {"spread": (1, 40), "slope": (0.1, 3.0), "wet": (0.0, 1.0), "min_wet": (0.0, 1.0), "land": (0.0, 1.0),
               "open": (0.0, 1.0),
               "drop": (0, FOUNDATION_DEPTH - 1), "depth": (0, 40), "clearance": (0, 64), "cover": (0, 64),
               "lift": (0, 64)}
        for k, (lo, hi) in rng.items():
            v = fit.get(k)
            if not isinstance(v, (int, float)) or not lo <= v <= hi:
                errors.append(f"{sid}: fit.{k} = {v} outside {lo}..{hi}")
        if mode == "underground" and fit.get("cover", 0) < 4:
            errors.append(f"{sid}: an underground structure needs cover >= 4 (it would open onto the surface)")
        if mode == "sky" and fit.get("clearance", 0) < 1:
            errors.append(f"{sid}: a sky structure needs clearance >= 1")
        if fit.get("min_wet", 0) > fit.get("wet", 1):
            errors.append(f"{sid}: fit.min_wet {fit.get('min_wet')} above fit.wet {fit.get('wet')}")
        if mode in ("land", "wetland") and fit.get("wet", 1) > (0.95 if mode == "wetland" else 0.25):
            errors.append(f"{sid}: fit.wet {fit.get('wet')} lets a land structure start in the water")
        if mode == "seabed" and (fit.get("wet", 0) < 0.5 or fit.get("depth", 0) < 2):
            errors.append(f"{sid}: a sea-floor structure needs wet >= 0.5 and depth >= 2")
        if mode == "coast":
            if fit.get("sea_side") not in ("north", "south", "east", "west"):
                errors.append(f"{sid}: coast fit needs sea_side north/south/east/west (template frame)")
            if fit.get("wet", 0) < 0.3 or fit.get("land", 0) < 0.3:
                errors.append(f"{sid}: coast fit needs water on one side and land on the other (wet, land >= 0.3)")
        # adaptation that suits the mode
        ok_adapt = {"land": ("beard_thin", "beard_box", "bury"), "wetland": ("none", "beard_thin"),
                    "coast": ("none",), "seabed": ("none", "beard_box", "beard_thin"), "sky": ("none",),
                    "underground": ("none", "encapsulate", "bury"), "cavern": ("none", "beard_box")}[mode]
        if adapt not in ok_adapt:
            errors.append(f"{sid}: terrain_adaptation {adapt} does not suit fit mode {mode} (use {ok_adapt})")
        # heights and the footprint against the start templates
        pool = json.load(open(os.path.join(data_dir, defs.MODID, "worldgen", "template_pool", sid, "start.json")))
        sizes = [e["element"].get("size") for e in pool["elements"] if e["element"].get("size")]
        if want_proj:
            for e in pool["elements"]:
                fp, size = e["element"].get("footprint"), e["element"].get("size")
                if not fp or len(fp) != 4 or not size:
                    errors.append(f"{sid}: projected start piece without a footprint (the site check would test "
                                  f"its whole box)")
                elif not (0 <= fp[0] <= fp[2] < size[0] and 0 <= fp[1] <= fp[3] < size[2]):
                    errors.append(f"{sid}: footprint {fp} outside its template {size}")
                gd = e["element"].get("ground_level_delta")
                if gd is not None and fit.get("ground") != gd - 1:
                    errors.append(f"{sid}: fit.ground {fit.get('ground')} != ground_level_delta - 1 ({gd - 1})")
        else:
            sh = js.get("start_height", {})
            lo_y = sh.get("min_inclusive", sh).get("absolute")
            hi_y = sh.get("max_inclusive", sh).get("absolute")
            tall = max((s[1] for s in sizes), default=0)
            top = {"overworld": 320, "end": 256, "nether": 128}[dim]
            if lo_y is None or hi_y is None:
                errors.append(f"{sid}: fixed-height structure without an absolute start_height")
            elif mode == "sky" and hi_y + fit.get("lift", 0) + tall > top:
                errors.append(f"{sid}: lifted by {fit.get('lift')} it would reach y {hi_y + fit.get('lift', 0) + tall} "
                              f"(top of the {dim}: {top})")
            elif mode == "underground" and lo_y - fit.get("lift", 0) < -63:
                errors.append(f"{sid}: sunk by {fit.get('lift')} it would reach under the bedrock floor")
        # biomes that suit the ground
        if not sdef:
            continue
        biomes = biome_set(sdef)
        theme = fit.get("theme", "stone")
        if mode in ("land", "wetland", "coast") and dim == "overworld" and biomes & WATERY:
            errors.append(f"{sid}: land structure listed in water biomes {sorted(biomes & WATERY)}")
        if mode == "seabed" and biomes - WATERY - SHORE:
            errors.append(f"{sid}: sea-floor structure listed in dry biomes {sorted(biomes - WATERY - SHORE)}")
        if mode == "coast" and not biomes & SHORE:
            errors.append(f"{sid}: coast structure without any shore biome")
        if mode in ("land", "wetland", "coast", "sky") and biomes & ARID and biomes & PEAKS:
            errors.append(f"{sid}: listed in deserts and on mountain peaks at once ({sorted(biomes & ARID)} / "
                          f"{sorted(biomes & PEAKS)})")
        if mode in ("land", "wetland") and dim == "overworld":
            if theme == "sand" and biomes - ARID - SHORE:
                errors.append(f"{sid}: sandy template in non-arid biomes {sorted(biomes - ARID - SHORE)}")
            if theme == "snow" and biomes - COLD:
                errors.append(f"{sid}: snowy template in warm biomes {sorted(biomes - COLD)}")
            if theme == "grass" and biomes & ARID:
                errors.append(f"{sid}: grass-topped template in arid biomes {sorted(biomes & ARID)}")
        if mode == "sky" and dim == "overworld" and biomes & (PEAKS | {"snowy_slopes", "meadow", "grove"}):
            errors.append(f"{sid}: a fixed-height sky structure listed in mountain biomes")
    return errors


def fit_rows():
    """Rows for the per-structure fit table: id, dimension, family, placement, adaptation, fit summary, biomes."""
    apply_overrides()
    fam = {s: f.id for f in FAMILIES for s in f.members}
    rows = []
    for s in defs.STRUCTURES:
        p = fit_params(s.id)
        m = p["mode"]
        if m in ("land", "wetland"):
            summary = f"spread<={p['spread']} slope<={p['slope']} water<={p['wet']:.0%} drop<={p['drop']}"
        elif m == "coast":
            summary = f"{p['sea_side']} side sea>={p['wet']:.0%}, land>={p['land']:.0%}, shore<=sea+{p['spread']}"
        elif m == "seabed":
            summary = f"water>={p['wet']:.0%} depth>={p['depth']} spread<={p['spread']}"
        elif m == "sky":
            summary = f"clearance>={p['clearance']} lift<={p['lift']}"
        elif m == "underground":
            summary = f"cover>={p['cover']} sink<={p['lift']}"
        else:
            summary = f"open>={p['open']:.0%}"
        height = (f"{s.height[0]} {s.height[1]}" + (f"..{s.height[2]}" if len(s.height) > 2 else "")
                  if s.height else f"projected {s.heightmap}")
        rows.append((s.id, s.dimension, fam.get(s.id, "-"), height, s.adaptation, m, summary, s.biomes))
    return rows


# ------------------------------------------------------------------ report
def table(old=None):
    """Rows for the placement report: structure, family, old spacing/sep, new set spacing/sep, weight,
    chunks between two of the same (min - max over its biomes), biomes."""
    by_id = {s.id: s for s in defs.STRUCTURES}
    rows = []
    for fam in families():
        for sid, w in fam.members.items():
            s = by_id.get(sid)
            if not s:
                continue
            per = per_type_spacing(fam, sid)
            lo, hi = (min(per.values()), max(per.values())) if per else (fam.spacing, fam.spacing)
            o = (old or {}).get(sid, (s.spacing, s.separation))
            rows.append((sid, fam.id, o[0], o[1], fam.spacing, fam.separation, w, lo, hi, s.biomes))
    return rows

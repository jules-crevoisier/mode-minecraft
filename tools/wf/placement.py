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
}
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
    """Vanilla biome ids a structure may start in (tags expanded, our biomes mapped back to the vanilla ones)."""
    from .biomes import VANILLA_TO_OURS
    ours = {}
    for v, o in VANILLA_TO_OURS.items():
        ours.setdefault(o, set()).add(v)
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
        elif b.startswith(defs.MODID + ":"):
            out |= ours.get(b.split(":")[1], set())
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

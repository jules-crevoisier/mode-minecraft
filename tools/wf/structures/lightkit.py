"""Themed interior light fill shared by a few colossal builds (sun ziggurat, canopy city, inverted spire, stilt city,
dreadnought wreck, titan forge, starfall library).

The builders hand-place their own lamps first; `light_fill` then floods the block light of every source through the
blueprint and, wherever a covered walkable floor (a ceiling within 14 blocks) that a player can reach is still under
light 8, adds one fixture of the build's theme:
  * a low ceiling (2-4 over the feet): a glow block set into the ceiling (`ceil`);
  * a ceiling 5-14 over the feet: a lamp hung on a chain, three blocks over the floor (`hang`, `chain`);
  * otherwise (open above, or a ceiling that cannot hold anything): a glow block set into the floor (`floor`).
Cells are visited on a coarse lattice first so the added fixtures fall in a regular pattern. Sealed voids (casings,
roof spaces) stay dark: only cells joined to the outside through open cells count."""
import numpy as np

from ..blueprint import is_solid

EMIT = {"lantern": 15, "soul_lantern": 10, "campfire": 15, "soul_campfire": 10, "shroomlight": 15, "glowstone": 15,
        "sea_lantern": 15, "ochre_froglight": 15, "verdant_froglight": 15, "pearlescent_froglight": 15,
        "ember_lamp": 15, "edison_lamp": 15, "hanging_edison_lamp": 15, "brass_chandelier": 15, "torch": 14,
        "wall_torch": 14, "soul_torch": 10, "soul_wall_torch": 10, "lava": 15, "fire": 15, "soul_fire": 10,
        "end_rod": 14, "glow_lichen": 7, "crying_obsidian": 10, "beacon": 15, "conduit": 15, "lithite_block": 12,
        "jack_o_lantern": 15, "starlight_block": 15, "rune_lamp": 15, "aether_conduit": 10, "lantern_post": 15,
        "magma_block": 3, "amethyst_cluster": 5, "enchanting_table": 7, "chiseled_ember_bricks": 7, "ember_bricks": 5}
# blocks never swapped for a glow block (function, loot, fixtures, see-through, falling blocks)
FALLING = ("sand", "red_sand", "suspicious_sand", "gravel", "suspicious_gravel")
NO_SWAP = ("chest", "barrel", "spawner", "door", "lamp", "bulb", "glass", "waystone", "seal", "bars", "sign", "bed",
           "water", "lava", "ladder", "stairs", "slab", "lantern", "rod", "vault", "table", "shelf", "lectern", "gauge",
           "valve", "cog", "gear", "pipe", "furnace", "anvil", "redstone", "leaves", "log", "wood", "trapdoor",
           "carpet", "mist", "bubble", "concrete_powder", "scaffold", "ice", "magma", "soul_sand",
           "chandelier", "light", "froglight", "glowstone", "shroomlight", "candle", "cauldron", "crafting",
           "smoker", "loom", "stonecutter", "grindstone", "anvil", "head", "skull", "banner", "pot", "chain",
           "starlight", "obsidian", "farmland", "dirt_path", "fence", "wall", "pane", "button", "lever", "plate",
           "torch", "campfire", "hopper", "dropper", "dispenser", "jukebox", "note_block", "beacon", "conduit",
           "honey", "slime", "sponge", "tnt", "cake", "bell", "brewing", "comparator", "repeater", "observer")


def _emit(name, props):
    sh = name.split(":")[1]
    props = props or {}
    if sh.endswith("candle"):
        return 3 * int(props.get("candles", 1)) if props.get("lit") == "true" else 0
    if sh in ("campfire", "soul_campfire") and props.get("lit") == "false":
        return 0
    if sh in ("furnace", "blast_furnace", "smoker"):
        return 13 if props.get("lit") == "true" else 0
    if "copper_bulb" in sh:
        return (4 if "oxidized" in sh else 15) if props.get("lit") == "true" else 0
    return EMIT.get(sh, 0)


def _opaque(name):
    sh = name.split(":")[1]
    if sh in ("air", "cave_air", "water", "lava") or sh.endswith(("_slab", "_stairs")) or "glass" in sh:
        return False
    return is_solid(name)


def light_fill(bp, ceil="glowstone", hang="lantern[hanging=true,waterlogged=false]",
               chain="iron_chain[axis=y,waterlogged=false]", floor="shroomlight", unset_solid_below=None,
               box=None, lattice=6, hang_drop=3, protect=()):
    """Light every reachable covered floor of bp to 8+ (see the module doc). unset_solid_below: unset cells at or
    below this y are ground (a land build); None: every unset cell is open air (sky and End builds). box: optional
    (x0, y0, z0, x1, y1, z1) limiting where fixtures go. protect: positions never changed. Returns the count of
    fixtures added."""
    B = bp.blocks
    xs = [p[0] for p in B]
    ys = [p[1] for p in B]
    zs = [p[2] for p in B]
    X0, Y0, Z0 = min(xs) - 2, min(ys) - 2, min(zs) - 2
    SH = (max(xs) - X0 + 3, max(ys) - Y0 + 3, max(zs) - Z0 + 3)
    known = np.zeros(SH, bool)
    opq = np.zeros(SH, bool)      # blocks light
    sol = np.zeros(SH, bool)      # any collider (a ceiling, a floor)
    wet = np.zeros(SH, bool)
    obst = np.zeros(SH, bool)     # anything with a shape (the audit's obstacle)
    fence = np.zeros(SH, bool)
    floorok = np.zeros(SH, bool)  # a surface one can stand on
    L = np.zeros(SH, np.int8)
    for (x, y, z), v in B.items():
        i = (x - X0, y - Y0, z - Z0)
        n = v[0]
        sh = n.split(":")[1]
        known[i] = True
        e = _emit(n, v[1])
        if e:
            L[i] = e
        o = _opaque(n) and not e
        opq[i] = o
        if sh not in ("air", "cave_air", "water", "lava", "bubble_column") and is_solid(n):
            sol[i] = True
        if sh in ("water", "lava", "bubble_column"):
            wet[i] = True
        elif sh not in ("air", "cave_air", "light", "structure_void"):
            obst[i] = True
        if sh.endswith(("_fence", "_wall")):
            fence[i] = True
        if sh not in ("air", "cave_air", "water", "lava", "bubble_column") and (
                o or sh.endswith(("_slab", "_stairs")) or "glass" in sh or "trapdoor" in sh):
            floorok[i] = True
    if unset_solid_below is not None:
        g = unset_solid_below - Y0
        if g >= 0:
            opq[:, :g + 1, :] |= ~known[:, :g + 1, :]
            sol[:, :g + 1, :] |= ~known[:, :g + 1, :]
            obst[:, :g + 1, :] |= ~known[:, :g + 1, :]
    # light flood (the litcheck model: 6-neighbour, -1 per step, opaque blocks stop it)
    for lvl in range(15, 1, -1):
        m = L == lvl
        if not m.any():
            continue
        for ax in range(3):
            for d in (1, -1):
                sm = np.zeros_like(m)
                a = [slice(None)] * 3
                b = [slice(None)] * 3
                if d > 0:
                    a[ax], b[ax] = slice(0, -1), slice(1, None)
                else:
                    a[ax], b[ax] = slice(1, None), slice(0, -1)
                sm[tuple(b)] = m[tuple(a)]
                L[sm & ~opq & (L < lvl - 1)] = lvl - 1

    def spread(i0, lvl):
        L[i0] = max(L[i0], lvl)
        q = [(i0, lvl)]
        while q:
            nq = []
            for (i, l) in q:
                for ax in range(3):
                    for d in (1, -1):
                        j = list(i)
                        j[ax] += d
                        if not (0 <= j[ax] < SH[ax]):
                            continue
                        j = tuple(j)
                        if opq[j] or L[j] >= l - 1:
                            continue
                        L[j] = l - 1
                        if l - 1 > 1:
                            nq.append((j, l - 1))
            q = nq

    # reachable open cells: flood from the outside (unset open cells) through every non-collider cell
    openc = ~sol
    outside = ~known & openc
    kopen = known & openc
    seed = np.zeros(SH, bool)
    for ax in range(3):
        for d in (1, -1):
            seed |= np.roll(outside, d, axis=ax)
    seed &= kopen
    NXs, NYs, NZs = SH
    flat_open = bytearray(kopen.ravel().tobytes())
    seen = bytearray(len(flat_open))
    offs = (1, -1, NZs, -NZs, NYs * NZs, -NYs * NZs)
    stack = np.flatnonzero(seed.ravel()).tolist()
    for c in stack:
        seen[c] = 1
    nmax = len(flat_open)
    while stack:
        v = stack.pop()
        for o in offs:
            w = v + o
            if 0 <= w < nmax and flat_open[w] and not seen[w]:
                seen[w] = 1
                stack.append(w)
    reach = np.frombuffer(bytes(seen), dtype=np.uint8).reshape(SH).astype(bool) | outside
    # standable feet cells: a surface below, two clear cells (feet may be shallow water)
    stand = np.zeros(SH, bool)
    stand[:, 1:-1, :] = (floorok[:, :-2, :] & ~sol[:, 1:-1, :] & ~fence[:, 1:-1, :] & ~sol[:, 2:, :]
                         & ~wet[:, 2:, :] & known[:, :-2, :])
    cov = np.zeros(SH, bool)
    for k in range(2, 15):
        cov[:, :-k, :] |= obst[:, k:, :]
    # enclosed (a room, not the open space under a deck or an arch): at head height, at least three of the four
    # axis rays meet something within 24 blocks
    hit = np.zeros(SH, np.int8)
    for ax in (0, 2):
        for d in (1, -1):
            h = np.zeros(SH, bool)
            for k in range(1, 25):
                h |= np.roll(obst, -d * k, axis=ax)
            hit += h
    enc = np.zeros(SH, bool)
    enc[:, :-1, :] = hit[:, 1:, :] >= 3
    target = stand & cov & reach & known & enc
    if box is not None:
        bx0, by0, bz0, bx1, by1, bz1 = box
        mb = np.zeros(SH, bool)
        mb[bx0 - X0:bx1 - X0 + 1, by0 - Y0:by1 - Y0 + 1, bz0 - Z0:bz1 - Z0 + 1] = True
        target &= mb
    cells = np.argwhere(target & (L < 8))
    pts = [(int(a) + X0, int(b) + Y0, int(c) + Z0) for a, b, c in cells]
    pts.sort(key=lambda p: (0 if (p[0] % lattice == 0 and p[2] % lattice == 0) else
                            1 if (p[0] % 3 == 0 and p[2] % 3 == 0) else 2, p[1], p[0], p[2]))
    prot = set(protect)

    def swappable(x, y, z):
        v = B.get((x, y, z))
        if v is None or (x, y, z) in prot:
            return False
        n = v[0]
        if not _opaque(n) or _emit(n, v[1]):
            return False
        sh = n.split(":")[1]
        return sh not in FALLING and not any(k in sh for k in NO_SWAP)

    added = 0
    for (x, f, z) in pts:
        i = (x - X0, f - Y0, z - Z0)
        if L[i] >= 8:
            continue
        cy = f + 2
        while cy - f <= 14 and not sol[x - X0, cy - Y0, z - Z0]:
            cy += 1
        d = cy - f
        placed = None
        if d <= 4:
            if swappable(x, cy, z):
                bp.set(x, cy, z, ceil)
                placed = [((x, cy, z), 15)]
        elif d <= 14:
            col = [B.get((x, y, z)) for y in range(f, cy)]
            if all(c is not None and c[0] == "minecraft:air" for c in col) and swappable(x, cy, z) or \
                    all(c is not None and c[0] == "minecraft:air" for c in col) and B.get((x, cy, z)) is not None \
                    and is_solid(B[(x, cy, z)][0]) and "glass" not in B[(x, cy, z)][0] \
                    and "leaves" not in B[(x, cy, z)][0]:
                ly = f + hang_drop
                for y in range(ly + 1, cy):
                    bp.set(x, y, z, chain)
                bp.set(x, ly, z, hang)
                placed = [((x, ly, z), 15 if "soul" not in hang else 10)]
        if placed is None and swappable(x, f - 1, z):
            bp.set(x, f - 1, z, floor)
            placed = [((x, f - 1, z), 15)]
        if placed:
            for (p, lv) in placed:
                j = (p[0] - X0, p[1] - Y0, p[2] - Z0)
                opq[j] = False
                spread(j, lv)
            added += 1
    return added

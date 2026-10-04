"""Crystal Cathedral: a gothic cathedral of calcite, quartz and amethyst in a vast geode cavern (Lot 7, mega-structures).

The template carves its own cavern (a half-ellipsoid 88 x 46 x 112) deep underground. Origin y = 0 is the cavern floor
and the nave floor:
  * a cathedral 50 blocks long: nave with pointed rib vault, side aisles, transept, apse, flying buttresses with
    amethyst pinnacles, twin west towers with spires, a stained-glass rose window over the portal and a crossing
    spire that grows into a crystal pillar joining the cavern roof,
  * inside: the glowing nave (froglight bosses, crystal chandeliers), pews, the altar of the Heart-Crystal in the apse,
    a scriptorium in the south transept, and a stair from the north transept down to the crypt,
  * the crypt: a low vaulted hall of tombs with the reliquary vault behind iron bars,
  * the geode: crystal spires hanging from the ceiling and growing from the floor, glowing pools, a processional way.
"""
import math

from .. import interior as INT
from ..arch import stair
from ..defs import Piece, StructureDef, register
from ..megakit import fbm, hash01, hash3, out_facing, vnoise
from ..parts import LOOT

CAL, QZ, QZB, SQZ, CHQ = "calcite", "quartz_block", "quartz_bricks", "smooth_quartz", "chiseled_quartz_block"
QZP = "quartz_pillar[axis=y]"
QZ_ST, SQZ_ST, QZ_SL, SQZ_SL = "quartz_stairs", "smooth_quartz_stairs", "quartz_slab", "smooth_quartz_slab"
AME, TINT, BUD = "amethyst_block", "tinted_glass", "budding_amethyst"
DS, DST, DSB = "polished_deepslate", "deepslate_tiles", "deepslate_bricks"
DS_ST, DS_SL, DS_W = "polished_deepslate_stairs", "polished_deepslate_slab", "polished_deepslate_wall"
FROG, SEA = "pearlescent_froglight[axis=y]", "sea_lantern"
GLASS = ["purple_stained_glass_pane", "magenta_stained_glass_pane", "light_blue_stained_glass_pane",
         "blue_stained_glass_pane", "pink_stained_glass_pane"]

RX, RY, RZ = 44, 56, 56
# cathedral plan
NW = 8            # nave wall at x = +-8 (inner nave -7..7)
AW = 14           # aisle outer wall
Z_FRONT, Z_APSE = 26, -26
TZ0, TZ1 = -20, -10   # transept walls (inner -19..-11)
TW = 22           # transept end walls x = +-22
AISLE_H, WALL_H, VAULT_RISE = 12, 20, 8
ROOF_BASE = WALL_H + 1
BAYS = [z for z in range(Z_APSE + 2, Z_FRONT - 1, 6)]   # pier lines


def ceil_y(x, z):
    v = 1 - (x / RX) ** 2 - (z / RZ) ** 2
    return RY * math.sqrt(v) if v > 0 else 0


def cluster(facing):
    return f"amethyst_cluster[facing={facing},waterlogged=false]"


# ------------------------------------------------------------------ the geode
def cavern(bp):
    for x in range(-RX - 2, RX + 3):
        for z in range(-RZ - 2, RZ + 3):
            for y in range(-1, RY + 3):
                d = (x / RX) ** 2 + (y / RY) ** 2 + (z / RZ) ** 2
                if y == -1:
                    if d <= 1.0:
                        bp.set(x, y, z, "deepslate")
                    continue
                if d <= 1.0:
                    if y == 0:
                        bp.set(x, 0, z, floor_spec(x, z))
                    else:
                        bp.set(x, y, z, "air")
                elif d <= 1.1:
                    bp.set(x, y, z, shell_spec(x, y, z, d))
    # amethyst crust patches on the walls with clusters growing inwards
    for x in range(-RX - 2, RX + 3):
        for z in range(-RZ - 2, RZ + 3):
            for y in range(1, RY + 3):
                if bp.get(x, y, z) != "minecraft:amethyst_block":
                    continue
                # inward neighbour
                for (dx, dy, dz, f) in ((0, -1, 0, "down"), (1, 0, 0, "east"), (-1, 0, 0, "west"), (0, 0, 1, "south"),
                                        (0, 0, -1, "north")):
                    n = bp.get(x + dx, y + dy, z + dz)
                    if n == "minecraft:air" and hash3(x, y, z, 51) < 0.22:
                        bp.set(x + dx, y + dy, z + dz, cluster(f) if hash3(x, y, z, 52) < 0.6 else
                               f"large_amethyst_bud[facing={f},waterlogged=false]")
                        break


def shell_spec(x, y, z, d):
    n = vnoise(x * 0.8 + y * 0.3, z * 0.8 - y * 0.5, 5.0, 81)
    if d < 1.035:
        # the inner skin of the geode: calcite with amethyst crust patches
        m = vnoise(x + y, z - y, 4.0, 83)
        if m < 0.3:
            return AME
        return CAL if m < 0.75 else "smooth_basalt"
    return "deepslate" if n < 0.5 else ("tuff" if n < 0.8 else "smooth_basalt")


def floor_spec(x, z):
    n = vnoise(x, z, 7.0, 85)
    m = vnoise(x, z, 2.5, 86)
    if n < 0.22:
        return "smooth_basalt"
    if n < 0.6:
        return CAL if m < 0.82 else AME
    if n < 0.82:
        return "tuff" if m < 0.6 else CAL
    return "deepslate" if m < 0.6 else "cobbled_deepslate"


def stalactite(bp, cx, cz, length, r, kind="amethyst"):
    """Crystal spire hanging from the cavern roof: wide at the root, a glowing core, a cluster at the tip."""
    top = int(ceil_y(cx, cz)) + 1
    bottom = top - length
    for y in range(bottom, top + 1):
        t = (y - bottom) / max(1, length)          # 0 at the tip, 1 at the root
        rr = r * t ** 0.8
        ri = int(math.ceil(rr)) + 1
        for x in range(cx - ri, cx + ri + 1):
            for z in range(cz - ri, cz + ri + 1):
                d = math.hypot(x - cx, z - cz)
                if d > rr + 0.3:
                    continue
                if kind == "amethyst":
                    if d < rr - 1.2:
                        spec = SEA if (y % 5 == 0 and d < 0.8) else AME
                    else:
                        spec = AME if hash3(x, y, z, 7) < 0.55 else ("purple_stained_glass" if hash3(x, y, z, 8) < 0.6
                                                                  else TINT)
                else:
                    spec = QZ if d < rr - 1.2 else (CAL if hash3(x, y, z, 9) < 0.5 else "white_stained_glass")
                bp.set(x, y, z, spec)
    bp.set(cx, bottom - 1, cz, cluster("down"))


def crystal(bp, cx, cz, h, r, lean=(0.0, 0.0), kind="amethyst", y0=1):
    """A hexagonal crystal prism growing from the floor, leaning, with a faceted point and a cluster on the tip.
    Amethyst: solid amethyst with a glowing froglight heart and one facet of stained glass; quartz: quartz and calcite
    with a sea-lantern heart."""
    point = max(3, int(r * 2.2))
    shaft = h - point
    for k in range(h):
        y = y0 + k
        rr = r if k < shaft else r * (h - k) / (point + 0.5)
        ox, oz = cx + lean[0] * k, cz + lean[1] * k
        ri = int(math.ceil(rr)) + 1
        for x in range(int(ox) - ri, int(ox) + ri + 2):
            for z in range(int(oz) - ri, int(oz) + ri + 2):
                dx, dz = x - ox, z - oz
                hexd = max(abs(dx) * 0.866 + abs(dz) * 0.5, abs(dz))
                if hexd > rr + 0.35:
                    continue
                core = hexd < rr - 0.9
                facet = dx > 0.4 and dz > -0.4 and not core
                if kind == "amethyst":
                    spec = (FROG if k % 5 == 2 else AME) if core else ("purple_stained_glass" if facet else AME)
                else:
                    spec = (SEA if k % 5 == 2 else QZ) if core else ("white_stained_glass" if facet else CAL)
                bp.set(x, y, z, spec)
    tx, tz = round(cx + lean[0] * (h - 1)), round(cz + lean[1] * (h - 1))
    bp.set(tx, y0 + h, tz, AME if kind == "amethyst" else QZ)
    bp.set(tx, y0 + h + 1, tz, cluster("up"))


def geode_crystals(bp):
    # hanging spires, clear of the cathedral roofs
    hang = [(-30, -20, 18, 4), (-26, 18, 14, 3), (30, -6, 20, 4), (24, 30, 12, 3), (-12, 40, 10, 3), (14, 44, 9, 2),
            (-34, 4, 12, 3), (34, 18, 10, 3), (-18, -40, 12, 3), (16, -42, 14, 3), (0, -46, 8, 2), (-36, -30, 7, 2),
            (36, -28, 8, 2), (-20, 30, 9, 2), (0, 36, 10, 3), (20, 10, 8, 2), (-20, -6, 8, 2)]
    for i, (x, z, L, r) in enumerate(hang):
        c = ceil_y(x, z)
        roof = 38 if (abs(x) <= TW + 2 and Z_APSE - 12 <= z <= Z_FRONT + 2) else 2
        L = int(min(L, c - roof - 4))
        if L > 3:
            stalactite(bp, x, z, L, r, "amethyst" if i % 3 else "quartz")
    # crystal groves on the floor
    groves = [(-30, 8, 3), (30, 0, 3), (-28, -30, 2), (28, -32, 2), (-24, 38, 3), (24, 40, 2), (0, -42, 2),
              (-36, -10, 2), (36, 24, 2)]
    for gi, (gx, gz, n) in enumerate(groves):
        for k in range(n + 2):
            a = k * 2.4 + gi
            dist = 0 if k == 0 else 2 + k * 1.3
            x, z = gx + round(math.cos(a) * dist), gz + round(math.sin(a) * dist)
            h = int(22 + hash01(x, z, 3) * 6) if k == 0 else int(15 - k * 1.5 + hash01(x, z, 4) * 5)
            r = 2.4 if k == 0 else 1.5
            lean = (math.cos(a) * 0.18 * (k > 0), math.sin(a) * 0.18 * (k > 0))
            if h > 3 and ceil_y(x, z) > h + 4:
                crystal(bp, x, z, h, r, lean, "amethyst" if (gi + k) % 3 else "quartz")
    # glowing pools
    for (px, pz, pr) in ((-20, 46, 3), (22, 26, 2), (-32, -18, 2), (12, -40, 2)):
        for x in range(px - pr - 1, px + pr + 2):
            for z in range(pz - pr - 1, pz + pr + 2):
                d = math.hypot(x - px, z - pz)
                if d <= pr + 0.3:
                    bp.set(x, -1, z, CAL)
                    bp.set(x, -2, z, "deepslate")
                    bp.set(x, 0, z, "water[level=0]")
                    if hash01(x, z, 8) < 0.3:
                        bp.set(x, -1, z, SEA)
                elif d <= pr + 1.3:
                    bp.set(x, 0, z, CAL)
                    bp.set(x, -1, z, CAL)
        bp.set(px, 0, pz, "sea_pickle[pickles=4,waterlogged=true]")
        bp.set(px, -1, pz, CAL)


# ------------------------------------------------------------------ the cathedral shell
def in_plan(x, z):
    """Inside the cathedral outer walls (footprint), excluding buttresses."""
    if Z_APSE <= z <= Z_FRONT and abs(x) <= AW:
        return True
    if TZ0 <= z <= TZ1 and abs(x) <= TW:
        return True
    if z < Z_APSE and math.hypot(x, z - Z_APSE) <= NW + 0.4:
        return True
    return False


def vault_top(x):
    """Intrados of the nave vault above the floor, for |x| <= NW - 1."""
    u = abs(x) / NW
    return WALL_H + int(round(VAULT_RISE * (1 - u ** 1.8)))


def roof_h(x):
    """Exterior steep roof surface over the nave at offset x."""
    return ROOF_BASE + int((NW + 1 - abs(x)) * 1.5)


def floors(bp):
    for x in range(-TW, TW + 1):
        for z in range(Z_APSE - NW - 1, Z_FRONT + 1):
            if not in_plan(x, z):
                continue
            if abs(x) < NW and Z_APSE < z < Z_FRONT:
                spec = CAL if (x + z) % 2 else DS          # checkerboard nave
                if x == 0:
                    spec = SQZ
            else:
                spec = DST if (x + z) % 3 else DS
            bp.set(x, 0, z, spec)
            bp.set(x, -1, z, DSB)


def nave(bp):
    """Nave walls (arcade + clerestory), the pointed rib vault and the steep amethyst roof."""
    zs = range(Z_APSE, Z_FRONT + 1)
    for z in zs:
        in_transept = TZ0 < z < TZ1
        pier = z in BAYS
        for x in range(-NW, NW + 1):
            ax = abs(x)
            if ax < NW:
                top = vault_top(x)
                for y in range(1, top + 1):
                    bp.set(x, y, z, "air")
                # vault shell
                rib = pier or z in (TZ0, TZ1)
                bp.set(x, top + 1, z, QZB if rib else CAL)
                bp.set(x, top + 2, z, QZB if rib else CAL)
                if rib and x == 0:
                    bp.set(0, top + 1, z, FROG)
                continue
            # nave wall line x = +-NW
            if in_transept:
                # crossing: open to the transept up to the vault springing
                for y in range(1, WALL_H + 1):
                    bp.set(x, y, z, "air")
                bp.set(x, WALL_H + 1, z, QZB)
                continue
            for y in range(1, WALL_H + 2):
                if pier:
                    spec = QZP if y < WALL_H else CHQ
                elif y <= 10:
                    spec = "air"               # arcade opening into the aisle (arch heads added below)
                elif y in (11, 12):
                    spec = QZB if y == 12 else CAL
                elif 14 <= y <= WALL_H - 1:
                    spec = window_glass(z, y)
                else:
                    spec = CAL
                bp.set(x, y, z, spec)
    # pointed arcade arch heads between piers
    for side in (-1, 1):
        x = side * NW
        for a, b in zip(BAYS, BAYS[1:]):
            if TZ0 <= a <= TZ1 or TZ0 <= b <= TZ1:
                continue
            mid = (a + b) / 2
            half = (b - a) / 2
            for z in range(a + 1, b):
                u = abs(z - mid) / half
                spring = 7 + int(round(3 * (1 - u ** 1.5)))
                for y in range(spring + 1, 11):
                    bp.set(x, y, z, CAL)
                bp.set(x, spring, z, stair(QZ_ST, "south" if z < mid else "north", "top") if u > 0.3 else QZB)
    # roof over the nave, apse end handled in apse()
    for z in range(Z_APSE, Z_FRONT + 2):
        for x in range(-NW - 1, NW + 2):
            yr = roof_h(x)
            if TZ0 < z < TZ1 and abs(x) <= NW:
                yr = roof_h(x)
            for y in range(ROOF_BASE, yr + 1):
                edge = y == yr
                if edge or abs(x) == NW + 1:
                    if (z - Z_APSE - 2) % 6 == 0:
                        spec = QZB
                    else:
                        spec = AME if edge else CAL
                    bp.set(x, y, z, spec)
        bp.set(0, roof_h(0) + 1, z, QZ_SL + "[type=bottom,waterlogged=false]" if z % 2 else CHQ)
    # eaves cornice
    for z in range(Z_APSE, Z_FRONT + 2):
        for side in (-1, 1):
            bp.set(side * (NW + 2), ROOF_BASE, z, stair(QZ_ST, "west" if side > 0 else "east", "top"))


def window_glass(z, y):
    """Clerestory/aisle lancet: stained glass in vertical bands, quartz mullion in the middle."""
    return GLASS[(z + y // 3) % len(GLASS)]


def aisles(bp):
    for side in (-1, 1):
        xo = side * AW
        for z in range(Z_APSE, Z_FRONT + 1):
            if TZ0 < z < TZ1:
                continue
            pier = z in BAYS or z in (Z_APSE, Z_FRONT, TZ0, TZ1)
            for x in range(side * (NW + 1), xo, side):
                for y in range(1, AISLE_H):
                    bp.set(x, y, z, "air")
                bp.set(x, AISLE_H, z, CAL if not pier else QZB)
            for y in range(1, AISLE_H + 1):
                if pier:
                    spec = QZP if y < AISLE_H else CHQ
                elif 3 <= y <= 9:
                    spec = window_glass(z, y) if y < 9 else CAL
                else:
                    spec = CAL
                bp.set(xo, y, z, spec)
            # lean-to roof from the aisle wall up to the clerestory
            for i, x in enumerate(range(xo + side, side * NW, -side)):
                yr = AISLE_H + 1 + i // 2 + (1 if i % 2 else 0) - 1
                bp.set(x, yr, z, AME if (z - Z_APSE - 2) % 6 else QZB)
                if i % 2 == 0:
                    bp.set(x, yr + 1, z, stair(QZ_ST, "east" if side > 0 else "west") if (z - Z_APSE - 2) % 6 else QZB)
            # lancet head: pointed tip above the window
            if not pier and (z - 1) not in BAYS and (z + 1) not in BAYS:
                bp.set(xo, 9, z, window_glass(z, 9))
                bp.set(xo, 10, z, window_glass(z, 10))


def buttresses(bp):
    """Flying buttresses: outer piers with amethyst pinnacles, arches leaping to the clerestory."""
    for z in BAYS:
        if TZ0 - 1 <= z <= TZ1 + 1 or z > Z_FRONT - 9:
            continue   # the transept and the west towers stand there
        for side in (-1, 1):
            px = side * (AW + 3)
            # pier
            for y in range(0, 23):
                for x in (px, px + side):
                    bp.set(x, y, z, QZP if y > 0 and x == px else (CAL if y > 0 else DS))
            for y in range(1, 15, 7):
                bp.set(px + side * 2, y, z, stair(QZ_ST, "east" if side < 0 else "west"))
            pinnacle(bp, px, 23, z)
            pinnacle(bp, px + side, 23, z, small=True)
            # the flying arch: a sloping beam with a curved underside
            for x in range(side * (NW + 1), px, side):
                d = abs(x) - NW - 1                       # 0 at the nave wall
                span = AW + 3 - NW - 1
                ytop = WALL_H - int(d * 0.45)
                ybot = ytop - 1 - int(round(5 * (d / span) ** 2.2))
                for y in range(ybot, ytop + 1):
                    bp.set(x, y, z, CAL if y < ytop else QZB)
                bp.set(x, ytop + 1, z, stair(QZ_ST, "east" if side < 0 else "west"))
            # tie the arch into the pier
            bp.set(px, 22, z, CHQ)


def pinnacle(bp, x, y, z, small=False):
    h = 2 if small else 4
    for k in range(h):
        bp.set(x, y + k, z, QZP if k < h - 1 else AME)
    bp.set(x, y + h, z, cluster("up"))
    if not small:
        for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            if bp.get(x + dx, y, z + dz) in (None, "minecraft:air"):
                bp.set(x + dx, y, z + dz, stair(QZ_ST, OPP[f], "bottom"))


OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def transept(bp):
    """Transept arms with gable rose windows; the crossing tower and its spire that becomes a crystal pillar."""
    for z in range(TZ0, TZ1 + 1):
        for x in range(-TW, TW + 1):
            if abs(x) < NW:
                continue
            end = abs(x) == TW
            wall = z in (TZ0, TZ1)
            inside = not end and not wall
            if inside:
                top = vault_top(0) if abs(x) <= NW else WALL_H + int(round(VAULT_RISE * (1 - (abs(z - (TZ0 + TZ1) / 2) / 5) ** 1.8)))
                for y in range(1, top + 1):
                    bp.set(x, y, z, "air")
                bp.set(x, top + 1, z, CAL if (abs(x) - NW) % 4 else QZB)
                bp.set(x, top + 2, z, CAL)
            else:
                for y in range(1, WALL_H + 2):
                    corner = end and wall
                    if corner or (wall and (abs(x) - NW) % 4 == 0):
                        spec = QZP if y <= WALL_H else CHQ
                    elif wall and 3 <= y <= 16 and (abs(x) - NW) % 4 == 2:
                        spec = window_glass(x, y)
                    else:
                        spec = CAL
                    bp.set(x, y, z, spec)
        # transept roof: ridge along x
    mz = (TZ0 + TZ1) / 2
    for x in range(-TW - 1, TW + 2):
        if abs(x) <= NW:
            continue
        for z in range(TZ0 - 1, TZ1 + 2):
            yr = ROOF_BASE + int((5.5 - abs(z - mz)) * 1.6)
            for y in range(ROOF_BASE, yr + 1):
                if y == yr or z in (TZ0 - 1, TZ1 + 1):
                    bp.set(x, y, z, QZB if abs(x) % 4 == 0 else AME)
        bp.set(x, ROOF_BASE + int(5.5 * 1.6) + 1, int(mz), QZ_SL + "[type=bottom,waterlogged=false]")
    # gable ends with rose windows
    for side in (-1, 1):
        x = side * TW
        for z in range(TZ0, TZ1 + 1):
            yr = ROOF_BASE + int((5.5 - abs(z - mz)) * 1.6)
            for y in range(WALL_H + 1, yr + 1):
                bp.set(x, y, z, CAL)
        rose(bp, x, 12, int(mz), 4, axis="x")
        # doors: a side portal on each transept end
        for z in range(int(mz) - 1, int(mz) + 2):
            for y in range(1, 6):
                bp.set(x, y, z, "air")
        for z in (int(mz) - 2, int(mz) + 2):
            for y in range(1, 7):
                bp.set(x, y, z, QZP)
        for z in range(int(mz) - 1, int(mz) + 2):
            bp.set(x, 6, z, CHQ if z == int(mz) else stair(QZ_ST, "south" if z < mz else "north", "top"))
    crossing_tower(bp)


def crossing_tower(bp):
    cz = (TZ0 + TZ1) // 2
    r = 5
    base = roof_h(0) - 2
    top = base + 7
    for y in range(base, top + 1):
        for x in range(-r, r + 1):
            for z in range(cz - r, cz + r + 1):
                m = max(abs(x), abs(z - cz))
                if m == r:
                    corner = abs(x) == r and abs(z - cz) == r
                    lancet = (abs(x) == 0 or abs(z - cz) == 0) and base + 2 <= y <= top - 2
                    bp.set(x, y, z, QZP if corner else (GLASS[(x + z + y) % 5] if lancet else CAL))
                elif m < r:
                    bp.set(x, y, z, "air" if y > base else CAL)
    for x in range(-r - 1, r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            if max(abs(x), abs(z - cz)) == r + 1:
                bp.set(x, top, z, stair(QZ_ST, out_facing(-x, cz - z), "top"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            pinnacle(bp, sx * r, top + 1, cz + sz * r)
    # the octagonal spire, faceted in amethyst with quartz ribs
    h = 12
    for k in range(h):
        y = top + 1 + k
        rr = (r - 0.3) * (1 - k / h)
        for x in range(-r, r + 1):
            for z in range(cz - r, cz + r + 1):
                dx, dz = abs(x), abs(z - cz)
                octd = max(dx, dz, (dx + dz) / 1.42)
                if rr - 1.0 < octd <= rr + 0.3:
                    rib = dx == 0 or dz == 0 or dx == dz
                    bp.set(x, y, z, QZB if rib else AME)
    # the crystal pillar: the spire turns into a column of crystal that joins the cavern roof
    y0 = top + 1 + h
    yc = int(ceil_y(0, cz)) + 1
    for y in range(y0, yc + 1):
        t = (y - y0) / max(1, yc - y0)
        rr = 0.6 + 2.6 * t ** 2
        for x in range(-4, 5):
            for z in range(cz - 4, cz + 5):
                d = math.hypot(x, z - cz)
                if d <= rr + 0.3:
                    bp.set(x, y, z, SEA if d < 0.6 and y % 3 == 0 else (AME if d < rr - 0.6 else "purple_stained_glass"))
    for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        bp.set(dx, y0, cz + dz, f"end_rod[facing={f}]")


def rose(bp, cx_or_x, cy, c2, r, axis="z", depth_out=None):
    """Rose window of radius r: concentric rings of coloured glass, twelve quartz tracery spokes, a froglight eye.
    axis='z': the window lies in the plane z = c2 (centre x = cx_or_x); axis='x': in the plane x = cx_or_x."""
    for u in range(-r - 1, r + 2):
        for v in range(-r - 1, r + 2):
            d = math.hypot(u, v)
            if d > r + 0.4:
                continue
            ang = math.degrees(math.atan2(v, u)) % 360
            spoke = min(abs((ang - k * 30 + 180) % 360 - 180) for k in range(12)) * math.pi / 180 * d < 0.55
            if d > r - 0.6:
                spec = CHQ
            elif d < 1.0:
                spec = FROG
            elif spoke and d > 1.5:
                spec = QZB
            elif abs(d - r * 0.55) < 0.5:
                spec = QZB
            else:
                ring = int(d * 1.6) % 4
                spec = ["magenta_stained_glass", "purple_stained_glass", "light_blue_stained_glass",
                        "blue_stained_glass"][ring]
            if axis == "z":
                bp.set(cx_or_x + u, cy + v, c2, spec)
            else:
                bp.set(cx_or_x, cy + v, c2 + u, spec)


def facade(bp):
    """West front: twin towers with spires over the aisles, a deep portal and the great rose window."""
    z = Z_FRONT
    # gable wall of the nave
    for x in range(-NW, NW + 1):
        for y in range(1, roof_h(x) + 1):
            bp.set(x, y, z, CAL if (x + y) % 7 else QZB)
            bp.set(x, y, z + 1, CAL)
    for x in range(-NW - 1, NW + 2):
        yy = roof_h(x) + 1
        bp.set(x, yy, z + 1, stair(QZ_ST, "west" if x > 0 else "east") if x else CHQ)
    bp.set(0, roof_h(0) + 2, z + 1, AME)
    bp.set(0, roof_h(0) + 3, z + 1, cluster("up"))
    # the great rose
    rose(bp, 0, 18, z + 1, 6, axis="z")
    for x in range(-7, 8):
        for y in range(11, 26):
            if bp.get(x, y, z) and math.hypot(x, y - 18) <= 6.4:
                bp.set(x, y, z, "air")
    # portal: pointed arch 5 wide, 9 high, with three receding orders of archivolts
    for order in range(3):
        hw = 2 + order
        zz = z + 1 - (0 if order == 0 else 0) + order
        for x in range(-hw - 1, hw + 2):
            ax = abs(x)
            top = 9 + order - int(round(((ax / (hw + 1)) ** 2) * 4))
            for y in range(1, top + 1):
                if ax <= hw:
                    bp.set(x, y, zz, "air")
            if ax <= hw + 1:
                spec = QZB if order != 1 else AME
                bp.set(x, top + 1 if ax <= hw else min(top + 1, 7 + order), zz, spec)
                if ax == hw + 1:
                    for y in range(1, 7 + order):
                        bp.set(x, y, zz, QZP)
    for zz in range(z - 1, z + 3):
        for x in range(-2, 3):
            for y in range(1, 9):
                if bp.get(x, y, zz) not in (None,) and abs(x) <= 2 and y <= 9 - int(round(((abs(x) / 3) ** 2) * 4)):
                    bp.set(x, y, zz, "air")
            bp.set(x, 0, zz, DS)
    # trumeau with the guardian statue niche and iron-bound doors
    for y in range(1, 6):
        bp.set(0, y, z, QZP)
    bp.set(0, 6, z, CHQ)
    bp.set(0, 7, z, AME)
    bp.door(-1, 1, z, "south", "dark_oak", hinge="left")
    bp.door(1, 1, z, "south", "dark_oak", hinge="right")
    for x in (-2, 2):
        for y in (1, 2):
            bp.set(x, y, z, "air")
    bp.door(-2, 1, z, "south", "dark_oak", hinge="right")
    bp.door(2, 1, z, "south", "dark_oak", hinge="left")
    # porch steps
    for x in range(-6, 7):
        bp.set(x, 0, z + 4, stair(DS_ST, "north") if abs(x) < 6 else DS)
        bp.set(x, 0, z + 3, DS)
        bp.set(x, 0, z + 2, DS)
    # twin towers over the aisles
    for side in (-1, 1):
        tower(bp, side * 12, z - 3)


def tower(bp, cx, cz):
    r = 4
    top = 30
    for y in range(0, top + 1):
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                m = max(abs(x - cx), abs(z - cz))
                if m == r:
                    corner = abs(x - cx) == r and abs(z - cz) == r
                    mid = abs(x - cx) == 0 or abs(z - cz) == 0
                    belfry = 21 <= y <= 27 and abs(x - cx) <= 1 and abs(z - cz) == r or \
                        21 <= y <= 27 and abs(z - cz) <= 1 and abs(x - cx) == r
                    lancet = 5 <= y <= 14 and abs(x - cx) + abs(z - cz) - r <= 0 and mid
                    if y == 0:
                        spec = DS
                    elif corner:
                        spec = QZP
                    elif belfry:
                        spec = "air" if y < 27 else QZB
                    elif lancet:
                        spec = GLASS[(y + cx) % 5]
                    elif y in (17, 28):
                        spec = QZB
                    else:
                        spec = CAL
                    bp.set(x, y, z, spec)
                elif y > 0 and y not in (16, top):
                    bp.set(x, y, z, "air")
                elif y in (16, top):
                    bp.set(x, y, z, CAL)
    # corner buttresses, stepped
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = cx + sx * (r + 1), cz + sz * (r + 1)
            for y in range(0, 22):
                bp.set(x, y, z, QZP if y else DS)
            pinnacle(bp, x, 22, z)
    # spire
    h = 12
    for k in range(h):
        y = top + 1 + k
        rr = (r + 0.5) * (1 - k / h) ** 1.2
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                dx, dz = abs(x - cx), abs(z - cz)
                octd = max(dx, dz, (dx + dz) / 1.42)
                if rr - 1.0 < octd <= rr + 0.3:
                    rib = dx == 0 or dz == 0 or dx == dz
                    bp.set(x, y, z, QZB if rib else AME)
    bp.set(cx, top + h + 1, cz, AME)
    bp.set(cx, top + h + 2, cz, cluster("up"))
    # bell in the belfry
    for x in range(cx - r + 1, cx + r):
        for z in range(cz - r + 1, cz + r):
            bp.set(x, 20, z, CAL)
            bp.set(x, 28, z, CAL)
    bp.set(cx, 26, cz, "bell[attachment=ceiling,facing=north,powered=false]")
    bp.set(cx, 27, cz, QZB)
    # gallery of arches across the west front, between the towers
    for x in range(-NW + 1, NW):
        bp.set(x, 12, Z_FRONT + 2, stair(QZ_ST, "north", "top"))
        if x % 2 == 0 and abs(x) > 1:
            bp.set(x, 10, Z_FRONT + 2, QZP)
            bp.set(x, 11, Z_FRONT + 2, QZP)


def apse(bp):
    """Semicircular apse with tall lancets, a half-dome vault, and the altar of the Heart-Crystal."""
    cz = Z_APSE
    for x in range(-NW - 2, NW + 3):
        for z in range(cz - NW - 2, cz):
            d = math.hypot(x, z - cz)
            if d > NW + 0.4:
                continue
            if d > NW - 0.6:
                ang = math.degrees(math.atan2(z - cz, x))
                lancet = int(round(ang / 22.5)) % 2 == 0
                for y in range(1, WALL_H + 2):
                    if lancet and 4 <= y <= 17 and abs(ang - round(ang / 22.5) * 22.5) < 6:
                        spec = GLASS[(y // 3 + int(ang)) % 5]
                    elif y > WALL_H:
                        spec = QZB
                    else:
                        spec = CAL if (int(ang) // 12) % 3 else QZP
                    bp.set(x, y, z, spec)
            else:
                # half dome
                top = WALL_H + int(math.sqrt(max(0.0, (NW - 0.5) ** 2 - d * d)) * VAULT_RISE / NW)
                for y in range(1, top + 1):
                    bp.set(x, y, z, "air")
                bp.set(x, top + 1, z, QZB if (x + z) % 3 == 0 else CAL)
                bp.set(x, top + 2, z, CAL)
            # conical roof
            ry = ROOF_BASE + int((NW + 1 - d) * 1.5)
            if d <= NW + 1.4:
                bp.set(x, ry, z, AME if (x + z) % 4 else QZB)
    # radiating buttresses
    for ang in (-150, -120, -90, -60, -30):
        a = math.radians(ang)
        for k in range(NW + 1, NW + 4):
            x, z = round(math.cos(a) * k), cz + round(math.sin(a) * k)
            for y in range(0, 20 - (k - NW) * 3):
                bp.set(x, y, z, QZP if y else DS)
        x, z = round(math.cos(a) * (NW + 3)), cz + round(math.sin(a) * (NW + 3))
        pinnacle(bp, x, 20 - 9, z)
    # the altar
    for x in range(-4, 5):
        for z in range(cz - 6, cz + 1):
            d = math.hypot(x, z - cz)
            if d <= 5.4:
                bp.set(x, 1, z, SQZ if d > 3.6 else QZB)
            if d <= 3.4:
                bp.set(x, 2, z, SQZ)
    for x in range(-3, 4):
        bp.set(x, 1, cz + 1, stair(SQZ_ST, "north"))
        bp.set(x, 2, cz - 1, stair(SQZ_ST, "north")) if abs(x) <= 2 else None
    bp.set(0, 3, cz - 2, CHQ)
    bp.set(-1, 3, cz - 2, stair(QZ_ST, "east", "top"))
    bp.set(1, 3, cz - 2, stair(QZ_ST, "west", "top"))
    for x in (-2, 2):
        bp.set(x, 3, cz - 2, "candle[candles=4,lit=true,waterlogged=false]")
    # the Heart-Crystal behind the altar
    crystal(bp, 0, cz - 4, 13, 2.2, kind="amethyst", y0=3)
    for (dx, dz) in ((-3, -3), (3, -3), (-2, -5), (2, -5)):
        crystal(bp, dx, cz + dz, 5, 1.0, lean=(dx * 0.08, 0), kind="quartz", y0=3)


def interior(bp):
    """Pews, crystal chandeliers, the glowing floor lights and the scriptorium."""
    for z in range(-6, Z_FRONT - 3, 2):
        for x in list(range(-6, -1)) + list(range(2, 7)):
            bp.set(x, 1, z, stair("dark_oak_stairs", "south"))
        for x in (-6, 6):
            bp.set(x, 1, z, stair("dark_oak_stairs", "south"))
    # floor lights down the aisles
    for z in range(Z_APSE + 2, Z_FRONT, 4):
        for x in (-11, 11):
            if not (TZ0 <= z <= TZ1):
                bp.set(x, 0, z, SEA)
    # crystal chandeliers hanging from the vault on chains
    for z in (-2, 10, 20):
        top = vault_top(0)
        for y in range(15, top + 1):
            bp.set(0, y, z, "iron_chain[axis=y,waterlogged=false]")
        bp.set(0, 14, z, AME)
        bp.set(0, 13, z, cluster("down"))
        for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
            bp.set(dx, 14, z + dz, f"end_rod[facing={f}]")
    cz = (TZ0 + TZ1) // 2
    for y in range(17, vault_top(0) + 1):
        bp.set(0, y, cz, "iron_chain[axis=y,waterlogged=false]")
    for x in range(-2, 3):
        for z in range(cz - 2, cz + 3):
            if abs(x) + abs(z - cz) <= 2:
                bp.set(x, 16, z, AME if (x, z) != (0, cz) else FROG)
    for (dx, dz, f) in ((3, 0, "east"), (-3, 0, "west"), (0, 3, "south"), (0, -3, "north")):
        bp.set(dx, 16, cz + dz, f"end_rod[facing={f}]")
    bp.set(0, 15, cz, cluster("down"))
    # south transept: the scriptorium
    for z in range(TZ0 + 1, TZ1):
        bp.set(TW - 1, 1, z, "bookshelf")
        bp.set(TW - 1, 2, z, "bookshelf")
        bp.set(TW - 1, 3, z, "chiseled_bookshelf[facing=west,slot_0_occupied=true,slot_1_occupied=true,"
                             "slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    for z in (TZ0 + 2, TZ1 - 2):
        bp.set(TW - 4, 1, z, "lectern[facing=east,has_book=false,powered=false]")
    bp.set(TW - 6, 1, cz, "enchanting_table")
    for (dx, dz) in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
        bp.set(TW - 6 + dx * 2, 1, cz + dz * 2, "bookshelf")
    bp.chest(TW - 1, 1, TZ1 - 1, "west", loot=LOOT + "crystal_cathedral")
    bp.chest(TW - 1, 1, TZ0 + 1, "west", loot=LOOT + "crystal_cathedral")
    # candles on the side altars of the aisles
    for z in (Z_APSE + 1,):
        for x in (-11, 11):
            bp.set(x, 1, z, SQZ)
            bp.set(x, 2, z, "candle[candles=3,lit=true,waterlogged=false]")


def crypt(bp):
    """Under the choir: a vaulted hall of tombs and the reliquary vault, reached from the north transept."""
    x0, x1, z0, z1, y0 = -11, 11, -34, -8, -9
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 1, z1 + 2):
            for y in range(y0 - 1, 0):
                edge = x in (x0 - 1, x1 + 1) or z in (z0 - 1, z1 + 1) or y == y0 - 1
                if edge:
                    bp.set(x, y, z, DSB if y > y0 - 1 else DST)
                else:
                    # low cross vault: columns every 4, arches between them
                    cx, cz = (x - x0) % 4, (z - z0) % 4
                    col = cx == 0 and cz == 0
                    arch = (cx == 0 or cz == 0) and y >= -3
                    if col:
                        bp.set(x, y, z, DS if y > y0 + 1 else DSB)
                    elif y == -1:
                        bp.set(x, y, z, DSB)
                    elif arch and y == -2:
                        bp.set(x, y, z, stair(DS_ST, "north", "top") if cz == 0 and cx else DS)
                    elif y == y0:
                        bp.set(x, y, z, DST if (x + z) % 2 else DS)
                    else:
                        bp.set(x, y, z, "air")
    # tombs between the columns
    for x in range(x0 + 2, x1, 4):
        for z in range(z0 + 2, z1 - 1, 4):
            if abs(x) <= 2 and z > z1 - 8:
                continue
            bp.set(x, y0 + 1, z, DS)
            bp.set(x, y0 + 1, z + 1, DS)
            bp.set(x, y0 + 2, z, SQZ_SL + "[type=bottom,waterlogged=false]")
            bp.set(x, y0 + 2, z + 1, SQZ_SL + "[type=bottom,waterlogged=false]")
            bp.set(x, y0 + 1, z - 1, "candle[candles=2,lit=true,waterlogged=false]")
            bp.set(x, y0, z - 1, DS)
    # soul lanterns hanging from the vault
    for x in range(x0 + 2, x1, 4):
        for z in range(z0 + 2, z1, 8):
            bp.set(x, -3, z, "soul_lantern[hanging=true,waterlogged=false]")
            bp.set(x, -2, z, DS)
    # the reliquary behind iron bars at the east end
    for x in range(-3, 4):
        bp.set(x, y0 + 1, z0 + 4, "iron_bars" if abs(x) < 3 else DS)
        bp.set(x, y0 + 2, z0 + 4, "iron_bars" if abs(x) < 3 else DS)
        bp.set(x, y0 + 3, z0 + 4, DS)
    bp.door(0, y0 + 1, z0 + 4, "south", "iron")
    bp.set(0, y0 + 1, z0 + 5, "air")
    bp.set(0, y0 + 2, z0 + 5, "air")
    bp.set(0, y0 + 1, z0 + 3, "air")
    bp.set(0, y0 + 2, z0 + 3, "air")
    bp.set(1, y0 + 1, z0 + 5, "stone_pressure_plate[powered=false]") if False else None
    for x in (-2, 2):
        bp.chest(x, y0 + 1, z0 + 1, "south", loot=LOOT + "crystal_cathedral_vault")
    bp.set(0, y0 + 1, z0 + 1, AME)
    bp.set(0, y0 + 2, z0 + 1, cluster("up"))
    for x in (-1, 1):
        bp.set(x, y0 + 1, z0 + 1, "candle[candles=4,lit=true,waterlogged=false]") if False else None
    bp.set(-3, y0 + 1, z0 + 1, SEA)
    bp.set(3, y0 + 1, z0 + 1, SEA)
    # the stair down from the north transept (x = -15..-13 going down towards -z)
    sx = -12
    for i in range(abs(y0)):
        z = TZ1 - 1 - i
        y = -1 - i
        for x in (sx - 1, sx, sx + 1):
            bp.set(x, y, z, stair(DS_ST, "south"))
            for yy in range(y + 1, y + 4):
                bp.set(x, yy, z, "air")
    # stairwell walls and the landing in the crypt
    for i in range(abs(y0) + 1):
        z = TZ1 - 1 - i
        for x in (sx - 2, sx + 2):
            for yy in range(-1 - i, 1 - i + 3):
                if bp.get(x, yy, z) in (None, "minecraft:air") or yy < 0:
                    if yy < 0:
                        bp.set(x, yy, z, DSB)
    for x in range(sx - 1, sx + 2):
        z = TZ1 - 1 - abs(y0)
        bp.set(x, y0, z, DS)
        for yy in range(y0 + 1, y0 + 4):
            bp.set(x, yy, z, "air")
    for x in range(sx - 1, sx + 2):
        bp.set(x, 0, TZ1 - 1, "air")


def processional(bp):
    """The pilgrims' way from the cavern's south wall to the portal, lit by crystal lamps."""
    for z in range(Z_FRONT + 5, RZ - 2):
        for x in range(-2, 3):
            if ceil_y(x, z) > 4:
                bp.set(x, 0, z, SQZ if abs(x) < 2 else QZB)
        if z % 6 == 0:
            for x in (-3, 3):
                if ceil_y(x, z) > 6:
                    bp.set(x, 1, z, QZP)
                    bp.set(x, 2, z, QZP)
                    bp.set(x, 3, z, FROG)
                    bp.set(x, 4, z, cluster("up"))


def cathedral(bp):
    cavern(bp)
    floors(bp)
    aisles(bp)
    nave(bp)
    transept(bp)
    apse(bp)
    buttresses(bp)
    facade(bp)
    interior(bp)
    crypt(bp)
    geode_crystals(bp)
    processional(bp)
    # two clerics keep the candles lit; chapels and sacristies get their furniture
    INT.populate(bp, [("cleric", 4), ("cleric", 2)], seed=1, void_solid=True, beds=True)
    INT.decorate(bp, dict(INT.THEMES["chapel"], ceiling=None), seed=1, void_solid=True, density=0.25, rugs=False,
                 centre=False)


register(StructureDef(
    "crystal_cathedral", "overworld", ["#minecraft:is_overworld"],
    [Piece("cathedral", cathedral)],
    spacing=80, separation=32, adaptation="none", height=("uniform", -44, -34), processors="none",
    step="underground_structures", max_distance=116, foundation=False,
    exclusion=("minecraft:ancient_cities", 6),
    title_fr="Cathédrale de cristal", title_en="Crystal Cathedral"))

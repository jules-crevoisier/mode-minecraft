"""Wayfarers terrain: the density functions of the world overhaul (written by tools/gen_world.py).

Everything here is plain JSON built in Python, checked against the 26.2 codecs (DensityFunctions, CubicSpline,
NoiseRouter, DimensionType). tools/world_preview.py evaluates the very same JSON with numpy to draw the maps.

Shape of the land, from the coast inland (heights are surface y, sea level 63):
  * oceans as in vanilla, warm oceans scattered with archipelagos of small islands;
  * cold coasts are fjords: sea inlets cut between cliffs 60-80 blocks high;
  * lowlands (high erosion) are rolling hills, 65-100;
  * an escarpment (a cliff band following an erosion contour) climbs to the plateaus, 110-170, cut by deep canyons
    whose floors hold the rivers (the river biome sits in the canyon floor: |weirdness| < 0.05);
  * mountain ranges (low erosion) run along the weirdness "peaks" contours, 160-260, with jagged crests to y 280-330;
  * hot and dry regions (badlands, rust lands, savanna plateaus) are terraced into mesas, with stone hoodoos;
  * warm stony peaks bristle with tall stone spires;
  * temperate humid regions have rare floating skylands between y 170 and 260;
  * warm wet lowlands sink into mires (Crimson Mire, Glowing Marsh) a few blocks above the sea, with puddles.
Continents are 1.6x larger than vanilla's (the continentalness noise is sampled at 0.15 instead of 0.25), weirdness
is at half vanilla's scale (fewer, wider rivers: they run along its zero lines), temperature and humidity are our own
smooth noises remapped so each climate band gets a set share of the world (TEMP_CDF, VEG_CDF; wf/biomes.py LAYOUT
places the biomes in those bands). Erosion keeps vanilla's scale.

The world is 448 blocks tall (y -64 to 383, minecraft:dimension_type/overworld is overridden by the pack) so the
peaks have room; the density gradient keeps vanilla's slope (3/384 per block) all the way up.

Units: "terrain value" tv is the height in 128-block units above y 64 (vanilla's offset spline value): y = 64 + 128 tv.
offset = tv - 0.50375, depth = gradient(y) + offset (0 at the surface).
"""

NS = "wayfarers"
DF = f"{NS}:overworld/"

MIN_Y = -64
HEIGHT = 448                 # world height: y -64 .. 383
TOP_Y = MIN_Y + HEIGHT       # 384 (exclusive)
SEA_LEVEL = 63
GLOBAL_OFFSET = -0.50375
# depth gradient: vanilla's 1.5 at y -64 to -1.5 at y 320 (slope 3/384 per block), extended to the new top
GRAD_TOP_VALUE = 1.5 - 3.0 * HEIGHT / 384.0


def y_of(tv):
    return 64 + 128 * tv


def tv_of(y):
    return (y - 64) / 128.0


# ------------------------------------------------------------------ JSON builders
def _r(v):
    """Round floats so the JSON stays readable (and the same on every run)."""
    if isinstance(v, float):
        r = round(v, 6)
        return 0.0 if r == 0 else r
    return v


def add(a, b):
    return {"type": "minecraft:add", "argument1": _r(a), "argument2": _r(b)}


def mul(a, b):
    return {"type": "minecraft:mul", "argument1": _r(a), "argument2": _r(b)}


def dmin(a, b):
    return {"type": "minecraft:min", "argument1": _r(a), "argument2": _r(b)}


def dmax(a, b):
    return {"type": "minecraft:max", "argument1": _r(a), "argument2": _r(b)}


def unary(kind, a):
    return {"type": f"minecraft:{kind}", "argument": _r(a)}


def flat(a):
    """A 2D value computed once per column (like vanilla's offset/factor)."""
    return unary("flat_cache", unary("cache_2d", a))


def clamp(a, lo, hi):
    return {"type": "minecraft:clamp", "input": a, "min": _r(float(lo)), "max": _r(float(hi))}


def noise(nid, xz=1.0, y=1.0):
    return {"type": "minecraft:noise", "noise": nid, "xz_scale": _r(float(xz)), "y_scale": _r(float(y))}


def shifted(nid, xz):
    return {"type": "minecraft:shifted_noise", "noise": nid, "xz_scale": _r(float(xz)), "y_scale": 0.0,
            "shift_x": "minecraft:shift_x", "shift_y": 0.0, "shift_z": "minecraft:shift_z"}


def ygrad(y0, y1, v0, v1):
    return {"type": "minecraft:y_clamped_gradient", "from_y": int(y0), "to_y": int(y1), "from_value": _r(float(v0)),
            "to_value": _r(float(v1))}


Y = ygrad(-1024, 1024, -1024.0, 1024.0)  # the block y itself


def range_choice(inp, lo, hi, yes, no):
    return {"type": "minecraft:range_choice", "input": inp, "min_inclusive": _r(float(lo)),
            "max_exclusive": _r(float(hi)), "when_in_range": _r(yes), "when_out_of_range": _r(no)}


def lerp_const(t, k, v):
    """DensityFunctions.lerp(t, k, v) with a constant k: k + t * (v - k)."""
    return add(mul(t, add(v, -k)), k)


def lerp(t, a, b):
    """a + t * (b - a), t in [0, 1] (t should be cheap or cached: it is read twice)."""
    return add(a, mul(t, add(b, mul(-1.0, a))))


class Spline:
    """A CubicSpline (minecraft:spline): points must be added in ascending order."""

    def __init__(self, coord):
        self.coord = coord
        self.points = []

    def add(self, loc, value, deriv=0.0):
        loc = round(float(loc), 6)
        if self.points and loc <= self.points[-1][0]:
            raise ValueError(f"spline points out of order: {loc} after {self.points[-1][0]}")
        self.points.append((loc, value, float(deriv)))
        return self

    def json(self):
        return {"coordinate": self.coord, "points": [
            {"location": loc, "value": v.json() if isinstance(v, Spline) else _r(float(v)), "derivative": _r(d)}
            for loc, v, d in self.points]}

    def df(self):
        return {"type": "minecraft:spline", "spline": self.json()}


def spline_df(coord, pts):
    s = Spline(coord)
    for p in pts:
        s.add(*p)
    return s.df()


def lerp_f(t, a, b):
    return a + t * (b - a)


# ------------------------------------------------------------------ climate inputs
CONT = DF + "continents"
EROS = "minecraft:overworld/erosion"
WEIRD = DF + "ridges"                           # weirdness
PV = DF + "ridges_folded"                       # peaks and valleys: -1 in valleys (|w| = 0), 1 on the crests
TEMP = DF + "temperature"
VEG = DF + "vegetation"
CONTINENT_SCALE = 0.15                           # vanilla 0.25
MUSHROOM_C = -0.85                               # the mushroom isles' continentalness (vanilla -1.05)
GLOWCAP_W = 0.55                                 # ...and their archipelagos in the temperate seas (weirdness)
# Climate. Vanilla's temperature has a ~4 km wavelength (one climate around spawn) and its humidity ~250-block
# patches; ours are smooth fractal noises (wayfarers:temperature / wayfarers:humidity, 3 octaves) with wavelengths
# of ~1.8 and ~1.5 km, so a walk of 2-3 km crosses several climates while each biome patch stays hundreds of blocks
# wide. Weirdness is vanilla's ridge noise at half its scale: its zero lines are the rivers (and its crests the
# ranges), so there are half as many rivers, wider ones, and the land between them reads as larger masses.
TEMP_SCALE = 0.28
VEG_SCALE = 0.34
RIDGE_SCALE = 0.125
# Both climate noises are near-normal (deviations measured with tools/wf/dfeval.py over 4 seeds); they are remapped
# (quantile splines) so each climate band gets a chosen share of the world instead of vanilla's (8% hot, 7% arid).
# Targets: (cumulative share, value) at the band edges of the biome layout (wf/biomes.py T_EDGES, H_EDGES).
TEMP_SIGMA, VEG_SIGMA = 0.237, 0.254
TEMP_CDF = [(0.005, -1.0), (0.15, -0.45), (0.35, -0.15), (0.59, 0.2), (0.80, 0.55), (0.995, 1.0)]
VEG_CDF = [(0.005, -1.0), (0.18, -0.35), (0.38, -0.1), (0.59, 0.1), (0.80, 0.3), (0.995, 1.0)]


def peaks_and_valleys(w):
    return -(abs(abs(w) - 0.6666667) - 0.33333334) * 3.0


def quantile_spline(coord, sigma, cdf):
    """A monotone spline taking a normal noise (deviation `sigma`) to the values of `cdf` at its quantiles."""
    from statistics import NormalDist
    nd = NormalDist(0.0, sigma)
    pts = [(nd.inv_cdf(q), v) for q, v in cdf]
    sec = [(pts[i + 1][1] - pts[i][1]) / (pts[i + 1][0] - pts[i][0]) for i in range(len(pts) - 1)]
    der = [sec[0]] + [2.0 / (1.0 / sec[i - 1] + 1.0 / sec[i]) for i in range(1, len(sec))] + [sec[-1]]
    s = Spline(coord)
    for (x, v), d in zip(pts, der):
        s.add(x, v, d)
    return s.df()


# ------------------------------------------------------------------ offset (2D height), adapted from TerrainProvider
def _mountain_cont(ridge, modulation, allow_rivers_below=-0.7):
    slope = 1.0 - (1.0 - modulation) * 0.5
    intersect = 0.5 * (1.0 - modulation)
    c = (ridge + 1.17) * 0.46082947 * slope - intersect
    return max(c, -0.2222) if ridge < allow_rivers_below else max(c, 0.0)


def _ridge_zero(modulation):
    slope = 1.0 - (1.0 - modulation) * 0.5
    intersect = 0.5 * (1.0 - modulation)
    return intersect / (0.46082947 * slope) - 1.17


def mountain_ridge(modulation, saddle, crest=1.0):
    """Vanilla's buildMountainRidgeSplineWithPoints, with a convex crest: the slope steepens toward the ridge line
    (start 0.55x, end 1.65x the mean slope) so ranges end in sharp ridges instead of domes. `crest` scales the top."""
    s = Spline(PV)
    top = _mountain_cont(1.0, modulation) * crest
    zero = _ridge_zero(modulation)
    if -0.65 < zero < 1.0:
        lo = _mountain_cont(-1.0, modulation)
        before = _mountain_cont(-0.75, modulation)
        after = _mountain_cont(-0.65, modulation)
        s.add(-1.0, lo, (before - lo) / 0.25)
        s.add(-0.75, before)
        s.add(-0.65, after)
        zv = _mountain_cont(zero, modulation)
        mean = (top - zv) / (1.0 - zero)
        s.add(zero - 0.01, zv)
        s.add(zero, zv, mean * 0.55)
        s.add(1.0, top, mean * 1.65)
    else:
        lo = _mountain_cont(-1.0, modulation)
        mean = (top - lo) / 2.0
        if saddle:
            s.add(-1.0, max(0.2, lo))
            s.add(0.0, lerp_f(0.5, lo, top), mean * 0.7)
        else:
            s.add(-1.0, lo, mean * 0.55)
        s.add(1.0, top, mean * 1.65)
    return s


RIVER_BANK_PV = -0.93       # river channels: below sea level only while |weirdness| < 0.023 (vanilla: ~0.08)


def ridge_spline(valley, low, mid, high, peaks, min_valley_steepness):
    d2 = 5.0 * (mid - low)
    s = Spline(PV)
    if valley < -0.01 and low > 0.0:
        # a river channel cut in the valley floor: steep banks just above sea level, then the valley slope
        bank = min(0.012, low)
        s.add(-1.0, valley, 0.0).add(RIVER_BANK_PV, bank, (bank - valley) / (1.0 + RIVER_BANK_PV) * 0.5)
        d1 = (low - bank) / (-0.4 - RIVER_BANK_PV)
        s.add(-0.4, low, min(d1, d2) if d2 > 0 else d1)
    else:
        d1 = max(0.5 * (low - valley), min_valley_steepness)
        s.add(-1.0, valley, d1).add(-0.4, low, min(d1, d2))
    return s.add(0.0, mid, d2).add(0.4, high, 2.0 * (high - mid)).add(1.0, peaks, 0.7 * (peaks - high))


def canyon_plateau(floor, top, mid, high, peaks):
    """A plateau cut by a canyon along the river line: flat floor while |weirdness| < 0.05 (the river biome),
    near-vertical walls up to |weirdness| 0.1, then the plateau top."""
    return (Spline(PV).add(-1.0, floor).add(-0.9, floor + 0.01).add(-0.85, 0.02)
            .add(-0.72, top * 0.92).add(-0.4, top, 0.25 * (mid - top) / 0.4)
            .add(0.0, mid, (high - top) / 0.8).add(0.4, high, (peaks - mid) / 1.0)
            .add(1.0, peaks, 0.5 * (peaks - high)))


def erosion_offset(low_valley, hill, tall_hill, mf, plain, swamp, inland):
    """buildErosionOffsetSpline, Wayfarers version. `inland` adds the extreme (windswept) hills, the plateaus with
    canyons and the escarpment between the plateaus and the lowlands."""
    very_low = mountain_ridge(lerp_f(mf, 0.95, 1.85), inland)
    low = mountain_ridge(lerp_f(mf, 0.8, 1.45), inland)
    mountains = mountain_ridge(mf * 1.1, inland)
    plains = ridge_spline(low_valley, plain, plain, hill, tall_hill, 0.5)
    swamps = ridge_spline(-0.02, swamp, swamp, hill, tall_hill, 0.0)
    s = Spline(EROS)
    if inland:
        # mountains from erosion -0.31 down (vanilla: -0.4), cores below -0.55 (vanilla's peak slice, below -0.78,
        # covers ~1% of the map): ranges are wider and much taller
        s.add(-0.55, very_low).add(-0.42, low).add(-0.31, mountains)
        floor = -0.05                           # canyon floor y ~58: a river 5 blocks deep
        wide = canyon_plateau(floor, 0.62 * mf, 0.66 * mf, 0.72 * mf, 0.86 * mf)
        narrow = canyon_plateau(floor, 0.5 * mf, 0.53 * mf, 0.6 * mf, 0.72 * mf)
        hills = ridge_spline(low_valley, plain + 0.04, hill + 0.08, tall_hill + 0.1, tall_hill + 0.2, 0.5)
        extreme = (Spline(PV).add(-1.0, low_valley).add(-0.4, plains)
                   .add(0.0, tall_hill + 0.22).add(1.0, tall_hill + 0.48, 0.3))
        s.add(-0.26, wide).add(-0.14, narrow)
        s.add(-0.11, narrow)                   # escarpment: plateau -> hills over 0.06 of erosion
        s.add(-0.05, hills).add(0.2, plains)
        s.add(0.4, plains).add(0.45, extreme).add(0.55, extreme).add(0.58, plains)
    else:
        s.add(-0.85, very_low).add(-0.7, low).add(-0.4, mountains)
        narrow = ridge_spline(low_valley, plain * mf, hill * mf, 0.5 * mf, 0.6 * mf, 0.5)
        wide = ridge_spline(low_valley - 0.15, 0.5 * mf, 0.5 * mf, 0.5 * mf, 0.6 * mf, 0.5)
        s.add(-0.35, wide).add(-0.1, narrow).add(0.2, plains)
    s.add(0.7, swamps)
    return s


def offset_spline():
    """overworldOffset, Wayfarers version: the continentalness bands (ocean, coast, near/mid/far inland)."""
    # swamp flats (the last value, erosion > 0.62) a block or two above the sea, not flooded (vanilla: -0.03):
    # the mires add their own puddles where it is wet
    beach = erosion_offset(-0.15, 0.0, 0.0, 0.1, 0.0, -0.03, False)
    low = erosion_offset(-0.1, 0.03, 0.1, 0.1, 0.01, 0.002, False)
    mid = erosion_offset(-0.1, 0.05, 0.16, 0.8, 0.02, 0.006, True)
    high = erosion_offset(-0.05, 0.06, 0.2, 1.0, 0.03, 0.01, True)
    # mushroom isles below MUSHROOM_C (vanilla -1.05: too rare to be found by /locate with the larger continents)
    return (Spline(CONT).add(MUSHROOM_C - 0.05, 0.044).add(MUSHROOM_C + 0.03, -0.2222).add(-0.51, -0.2222)
            .add(-0.44, -0.12)
            .add(-0.18, -0.12).add(-0.16, beach).add(-0.15, beach).add(-0.1, low).add(0.2, mid).add(0.6, high))


# ------------------------------------------------------------------ factor and jaggedness (TerrainProvider ports)
def erosion_factor(base, shattered):
    base_s = Spline(WEIRD).add(-0.2, 6.3).add(0.2, base)
    s = (Spline(EROS).add(-0.6, base_s)
         .add(-0.5, Spline(WEIRD).add(-0.05, 6.3).add(0.05, 2.67))
         .add(-0.35, base_s).add(-0.25, base_s)
         .add(-0.1, Spline(WEIRD).add(-0.05, 2.67).add(0.05, 6.3))
         .add(0.03, base_s))
    if shattered:
        weird_sh = Spline(WEIRD).add(0.0, base).add(0.1, 0.625)
        ridges_sh = Spline(PV).add(-0.9, base).add(-0.69, weird_sh)
        s.add(0.35, base).add(0.45, ridges_sh).add(0.55, ridges_sh).add(0.62, base)
    else:
        extreme = Spline(PV).add(-0.7, base_s).add(-0.15, 1.37)
        peaks_only = Spline(PV).add(0.45, base_s).add(0.7, 1.56)
        s.add(0.05, peaks_only).add(0.4, peaks_only).add(0.45, extreme).add(0.55, extreme).add(0.58, base)
    return s


def factor_spline():
    return (Spline(CONT).add(-0.19, 3.95).add(-0.15, erosion_factor(6.25, True)).add(-0.1, erosion_factor(5.47, True))
            .add(0.03, erosion_factor(5.08, True)).add(0.06, erosion_factor(4.69, False)))


JAGGED_SCALE = 1.25


def _weird_jag(f):
    return Spline(WEIRD).add(-0.01, 0.63 * f * JAGGED_SCALE).add(0.01, 0.3 * f * JAGGED_SCALE)


def _ridge_jag(peak, high):
    hs, he = peaks_and_valleys(0.4), peaks_and_valleys(0.56666666)
    s = Spline(PV).add(hs, 0.0)
    s.add((hs + he) / 2.0, _weird_jag(high) if high > 0 else 0.0)
    s.add(1.0, _weird_jag(peak) if peak > 0 else 0.0)
    return s


def _erosion_jag(p0, p1, h0, h1):
    e1 = _ridge_jag(p1, h1)
    # vanilla's breakpoints (-1, -0.78, -0.5775, -0.375) moved up with the mountains
    return Spline(EROS).add(-0.62, _ridge_jag(p0, h0)).add(-0.5, e1).add(-0.4, e1).add(-0.28, 0.0)


def jaggedness_spline():
    return (Spline(CONT).add(-0.11, 0.0).add(0.03, _erosion_jag(1.0, 0.5, 0.0, 0.0))
            .add(0.65, _erosion_jag(1.0, 1.0, 1.0, 0.25)))


# ------------------------------------------------------------------ regional features (2D, in terrain value units)
NOISES = {
    # name: (firstOctave, amplitudes)
    "temperature": (-9, [0.7, 1.0, 0.35]),
    "mire": (-5, [1.0, 0.5]),
    "humidity": (-9, [0.8, 1.0, 0.4]),
    "mega_caverns": (-8, [1.0, 1.0, 0.5]),
    "hills": (-8, [1.0, 0.6, 0.3]),
    "terrace_jitter": (-6, [1.0]),
    "islands": (-7, [1.0, 0.7, 0.35]),
    "dunes": (-7, [1.0, 0.3]),
    "fjords": (-8, [1.0, 0.5]),
    "spires": (-5, [1.0, 0.25]),
    "spire_height": (-6, [1.0, 0.5]),
    "skylands": (-9, [1.0, 0.5]),
    "skyland_shape": (-7, [1.0, 0.6, 0.3]),
    "skyland_height": (-8, [1.0, 0.5]),
    "skyland_rock": (-4, [1.0, 0.5]),
    "underground_rivers": (-7, [1.0, 0.4]),
    "underground_river_height": (-8, [1.0]),
    # surface-rule noises (2D: vertical stripes on cliffs)
    "striation": (-3, [1.0, 0.5]),
    "moss_streak": (-4, [1.0, 0.5]),
}


def N(name):
    return f"{NS}:{name}"


def _band(coord, pts):
    return spline_df(coord, [(x, v) for x, v in pts])


def hot_dry():
    """1 in the hot lands but the wet ones (temperature > 0.55, humidity < 0.3: Pale Dunes, Painted Canyon, Ashen
    Wastes, Volcanic Highlands, Cogwork Valley) and in the warm arid ones (Dune Sea, Rustlands), 0 elsewhere."""
    hot = mul(_band(TEMP, [(0.5, 0.0), (0.6, 1.0)]), _band(VEG, [(0.25, 1.0), (0.33, 0.0)]))
    arid = mul(_band(TEMP, [(0.15, 0.0), (0.25, 1.0)]), _band(VEG, [(-0.4, 1.0), (-0.3, 0.0)]))
    return dmax(hot, arid)


def features():
    """The 2D regional features, as named density functions."""
    out = {}
    # gentle rolling hills on the lowlands (not on rivers, coasts or swamps): +-12 blocks over ~250, so most of
    # the lowland stays buildable
    hill_mask = mul(mul(_band(EROS, [(-0.25, 0.0), (-0.05, 1.0), (0.42, 1.0), (0.62, 0.0)]),
                        _band(CONT, [(-0.14, 0.0), (0.02, 1.0)])),
                    _band(PV, [(-0.85, 0.0), (-0.55, 1.0)]))
    rolling = mul(hill_mask, add(mul(0.09, noise(N("hills"), 1.0, 0.0)), 0.03))
    # dunes on the hot dry lowlands: long ridged swells (1 - |n|)^2, up to ~8 blocks
    out["hot_dry"] = flat(hot_dry())
    dune_mask = mul(DF + "hot_dry", mul(_band(EROS, [(-0.1, 0.0), (0.05, 1.0)]), _band(CONT, [(-0.12, 0.0), (0.0, 1.0)])))
    dunes = mul(dune_mask, mul(0.06, unary("square", add(1.0, mul(-1.0, unary("abs", noise(N("dunes"), 1.0, 0.0)))))))
    out["hills"] = flat(add(rolling, dunes))

    # the base height: TerrainProvider's offset (Wayfarers version) plus the hills
    out["terrain_base"] = flat(add(offset_spline().df(), DF + "hills"))
    base = DF + "terrain_base"

    # terraces in hot dry lands: 14-block mesa steps from y ~96 with near-vertical risers (each step: a flat tread,
    # then the riser over the last 28% of the step); the low dunes below stay smooth swells
    t = Spline(base).add(-0.2, -0.2, 1.0).add(0.24, 0.24, 1.0)
    lv = 0.25
    while lv < 1.6:
        step = 14.0 / 128.0
        t.add(lv + 0.004, lv + 0.004, 0.0)
        t.add(lv + step * 0.72, lv + 0.012, 0.0)
        lv += step
    t.add(lv + 0.004, lv + 0.004, 1.0)
    terraced = add(t.df(), mul(0.012, noise(N("terrace_jitter"), 1.0, 0.0)))
    # (each stage is a named, cached function: lerp/dmin read their inputs twice, inlining them would copy the
    # whole spline tree)
    out["terrain_terraced"] = flat(lerp(DF + "hot_dry", base, terraced))
    with_terraces = DF + "terrain_terraced"

    # mires: the warm wet lowlands (Crimson Mire, Glowing Marsh, the wet Emerald Jungle) sink to a few blocks
    # above sea level, the hills squashed (x 0.15), with puddles and channels where the mire noise dips
    out["mire_mask"] = flat(mul(mul(_band(TEMP, [(0.15, 0.0), (0.25, 1.0)]), _band(VEG, [(0.24, 0.0), (0.32, 1.0)])),
                                mul(_band(CONT, [(-0.15, 0.0), (-0.08, 1.0)]),
                                    dmax(_band(EROS, [(-0.22, 0.0), (-0.08, 1.0)]),     # lowlands, and near the coast
                                         mul(_band(CONT, [(0.0, 1.0), (0.06, 0.0)]),    # all but the mountains
                                             _band(EROS, [(-0.34, 0.0), (-0.28, 1.0)]))))))
    marsh = add(add(mul(0.15, unary("abs", with_terraces)), mul(0.04, noise(N("mire"), 1.0, 0.0))), 0.002)
    out["terrain_mire"] = flat(lerp(DF + "mire_mask", with_terraces, dmin(with_terraces, marsh)))
    with_terraces = DF + "terrain_mire"

    # fjords: cold coasts become 60-80 block high cliffs cut by sea inlets
    # (the Rimefrost Fjords biome: temperature < -0.15, continentalness < 0.03, weirdness < 0, wf/biomes.py)
    cold = _band(TEMP, [(-0.22, 1.0), (-0.12, 0.0)])
    coast = _band(CONT, [(-0.32, 0.0), (-0.2, 1.0), (0.0, 1.0), (0.07, 0.0)])
    r = unary("abs", noise(N("fjords"), 1.0, 0.0))
    channel = spline_df(r, [(0.035, -0.3), (0.11, 4.0)])
    cliffs = spline_df(r, [(0.0, -0.25), (0.04, -0.2), (0.1, 0.3), (0.25, 0.46), (0.6, 0.56)])
    side = _band(WEIRD, [(-0.05, 1.0), (0.0, 0.0)])
    out["fjord_mask"] = flat(mul(mul(cold, coast), side))
    fjord = dmax(dmin(with_terraces, channel), cliffs)
    with_fjords = lerp(DF + "fjord_mask", with_terraces, fjord)

    # archipelagos in the shallow warm oceans (Tidebrass Archipelago: temperature > 0.55, -0.455 < c < -0.19) and
    # in the temperate ones where the weirdness is high (Glowcap Isles: weirdness > GLOWCAP_W, wf/biomes.py)
    warm = _band(TEMP, [(0.45, 0.0), (0.6, 1.0)])
    glow = mul(_band(TEMP, [(-0.22, 0.0), (-0.1, 1.0), (0.12, 1.0), (0.25, 0.0)]),
               _band(WEIRD, [(GLOWCAP_W - 0.08, 0.0), (GLOWCAP_W + 0.04, 1.0)]))
    sea = _band(CONT, [(-0.62, 0.0), (-0.48, 1.0), (-0.3, 1.0), (-0.22, 0.0)])
    isl = spline_df(noise(N("islands"), 1.0, 0.0),
                    [(0.22, -0.6), (0.38, -0.04), (0.46, 0.035), (0.62, 0.16), (0.9, 0.36, 0.6)])
    islands = add(mul(mul(dmax(warm, glow), sea), add(isl, 1.0)), -1.0)
    # capped at y ~301 (jagged crests add up to ~45 more; the top slide starts at y 360)
    out["terrain"] = flat(clamp(dmax(with_fjords, islands), -1.5, 1.85))

    out["offset"] = flat(add(DF + "terrain", GLOBAL_OFFSET))
    out["factor"] = flat(factor_spline().df())
    out["jaggedness"] = flat(mul(jaggedness_spline().df(),
                                 unary("half_negative", noise("minecraft:jagged", 1500.0, 0.0))))
    out["depth"] = add(ygrad(MIN_Y, TOP_Y, 1.5, GRAD_TOP_VALUE), DF + "offset")
    initial = mul(4.0, unary("quarter_negative", mul(add(DF + "depth", DF + "jaggedness"), DF + "factor")))
    out["sloped_cheese"] = add(initial, "minecraft:overworld/base_3d_noise")
    return out


# ------------------------------------------------------------------ extra terrain above the surface
def height_above_surface():
    """Blocks above the 2D surface estimate (depth is 0 there and falls 3/384 per block)."""
    return mul(-128.0, DF + "depth")


def spires():
    """Stone spires and hoodoos: tapered pillars rising from the ground. Positive inside a pillar.
    In a pillar region the noise peaks (> 0.36) become columns; the column is solid while
    core > h / H, core = clamp(10 (n - 0.36), -1, 1) (h: height above ground, H: the pillar's height), so it
    narrows to a point at H. Only on land."""
    # stone pinnacles on the hot mountain flanks (Volcanic Highlands: their cliffs take the ochre bands); not on
    # the dunes and plateaus, which have their own hoodoo objects
    hoodoos = mul(DF + "hot_dry", _band(EROS, [(-0.62, 0.0), (-0.48, 1.0), (-0.36, 1.0), (-0.29, 0.0)]))
    # the Stone Spires biome: the warm mountains (wf/biomes.py LAYOUT)
    stony = mul(_band(TEMP, [(0.12, 0.0), (0.22, 1.0), (0.5, 1.0), (0.6, 0.0)]),
                _band(EROS, [(-0.45, 1.0), (-0.33, 0.0)]))
    land = _band(CONT, [(-0.1, 0.0), (0.0, 1.0)])
    out = {}
    out["spire_region"] = flat(mul(land, dmax(mul(0.55, hoodoos), stony)))
    n = noise(N("spires"), 1.0, 0.0)
    height = add(18.0, mul(90.0, mul(DF + "spire_region",
                                     clamp(add(0.6, noise(N("spire_height"), 1.0, 0.0)), 0.2, 1.2))))
    out["spire_height"] = flat(height)
    core = flat(clamp(mul(10.0, add(n, -0.36)), -1.0, 1.0))
    pillar = add(core, mul(-1.0, mul(height_above_surface(), unary("invert", DF + "spire_height"))))
    out["spires"] = range_choice(DF + "spire_region", 0.05, 2.0, pillar, -1.0)
    return out


SKY_MIN, SKY_MAX = 160, 270


def skylands():
    """Floating islands between y 170 and 260 above temperate humid lands: flat grassy tops, tapered rocky
    undersides. Solid where top - thickness < y < top."""
    temperate = _band(TEMP, [(-0.25, 0.0), (-0.1, 1.0), (0.45, 1.0), (0.6, 0.0)])
    humid = _band(VEG, [(0.05, 0.0), (0.2, 1.0)])
    rare = _band(noise(N("skylands"), 1.0, 0.0), [(0.25, 0.0), (0.4, 1.0)])
    lowland = _band(DF + "terrain", [(0.35, 1.0), (0.6, 0.0)])
    out = {}
    out["skyland_region"] = flat(mul(mul(temperate, humid), mul(rare, lowland)))
    shape = add(noise(N("skyland_shape"), 1.0, 0.0), -0.2)
    out["skyland_thickness"] = flat(mul(clamp(mul(DF + "skyland_region", 3.0), 0.0, 1.0), mul(140.0, shape)))
    out["skyland_top"] = flat(add(212.0, mul(34.0, noise(N("skyland_height"), 1.0, 0.0))))
    top = DF + "skyland_top"
    below_top = add(top, mul(-1.0, Y))                                  # top - y
    above_bottom = add(add(Y, mul(-1.0, top)), DF + "skyland_thickness")  # y - (top - thickness)
    rock = mul(6.0, noise(N("skyland_rock"), 1.0, 1.0))
    body = dmin(mul(0.12, below_top), mul(0.07, add(above_bottom, rock)))
    gated = range_choice(DF + "skyland_region", 0.02, 10.0, range_choice(DF + "skyland_thickness", 1.0, 1000.0, body, -1.0), -1.0)
    out["skylands"] = range_choice(Y, SKY_MIN, SKY_MAX, gated, -1.0)
    return out


# ------------------------------------------------------------------ caves
RIVER_Y = 6           # underground river floor (y 6..24: the aquifer cell 0..40 gives water levels 14..26)


def caves():
    out = {}
    # mega caverns: a regional 2D noise lowers the cheese threshold in a band between y -40 and 10
    band = dmin(ygrad(-56, -40, 0.0, 1.0), ygrad(10, 26, 1.0, 0.0))
    region = flat(clamp(mul(noise(N("mega_caverns"), 1.0, 0.0), 1.7), 0.0, 1.0))
    out["mega_caverns"] = mul(mul(band, region), -0.3)
    # underground rivers: winding tunnels along the zero lines of a 2D noise, 16-20 blocks high, floor y ~6
    r = flat(unary("abs", noise(N("underground_rivers"), 1.0, 0.0)))
    out["underground_river_line"] = r
    yy = add(Y, flat(mul(6.0, noise(N("underground_river_height"), 1.0, 0.0))))
    profile = spline_df(yy, [(RIVER_Y - 6, 0.6), (RIVER_Y, 0.0), (RIVER_Y + 3, -0.3), (RIVER_Y + 14, -0.3),
                             (RIVER_Y + 20, 0.0), (RIVER_Y + 26, 0.6)])
    tunnel = add(mul(9.0, DF + "underground_river_line"), add(profile, -0.12))
    out["underground_rivers"] = range_choice(Y, RIVER_Y - 8, RIVER_Y + 28,
                                             range_choice(DF + "underground_river_line", 0.0, 0.06, tunnel, 1.0), 1.0)
    # their aquifer: partially flooded (0.4 < floodedness < 0.8): the water level is picked per 16x40x16 cell
    out["underground_river_flood"] = range_choice(Y, RIVER_Y - 4, RIVER_Y + 26,
                                                  range_choice(DF + "underground_river_line", 0.0, 0.07, 0.7, -1.0), -1.0)
    return out


def underground(sloped):
    layer = mul(4.0, unary("square", noise("minecraft:cave_layer", 1.0, 8.0)))
    cheese = noise("minecraft:cave_cheese", 1.0, 0.6666666666666666)
    solid = add(clamp(add(add(0.27, DF + "mega_caverns"), cheese), -1.0, 1.0),
                clamp(add(1.5, mul(-0.64, sloped)), 0.0, 0.5))
    base = add(layer, solid)
    subtract = dmin(dmin(base, "minecraft:overworld/caves/entrances"),
                    add("minecraft:overworld/caves/spaghetti_2d", "minecraft:overworld/caves/spaghetti_roughness_function"))
    subtract = dmin(subtract, DF + "underground_rivers")
    pillars = range_choice("minecraft:overworld/caves/pillars", -1000000.0, 0.03, -1000000.0,
                           "minecraft:overworld/caves/pillars")
    return dmax(subtract, pillars)


def slide(fn):
    """NoiseRouterData.slideOverworld for the taller world: fades to air from y TOP-24 to TOP, to rock near the floor."""
    top = ygrad(TOP_Y - 24, TOP_Y, 1.0, 0.0)
    fn = lerp_const(top, -0.078125, fn)
    bottom = ygrad(MIN_Y, MIN_Y + 24, 0.0, 1.0)
    return lerp_const(bottom, 0.1171875, fn)


def density_functions():
    out = {}
    out["continents"] = unary("flat_cache", shifted("minecraft:continentalness", CONTINENT_SCALE))
    out["temperature_noise"] = unary("flat_cache", shifted(N("temperature"), TEMP_SCALE))
    out["vegetation_noise"] = unary("flat_cache", shifted(N("humidity"), VEG_SCALE))
    out["temperature"] = unary("flat_cache", quantile_spline(DF + "temperature_noise", TEMP_SIGMA, TEMP_CDF))
    out["vegetation"] = unary("flat_cache", quantile_spline(DF + "vegetation_noise", VEG_SIGMA, VEG_CDF))
    out["ridges"] = unary("flat_cache", shifted("minecraft:ridge", RIDGE_SCALE))
    out["ridges_folded"] = unary("flat_cache", mul(add(unary("abs", add(unary("abs", WEIRD), -0.6666667)),
                                                       -0.33333334), -3.0))
    out.update(features())
    out.update(spires())
    out.update(skylands())
    out.update(caves())
    # land above the surface: spires and skylands
    out["extra_terrain"] = dmax(DF + "spires", DF + "skylands")
    return out


def noise_router():
    sloped = unary("cache_once", DF + "sloped_cheese")
    surface = dmax(dmin(sloped, mul(5.0, "minecraft:overworld/caves/entrances")), DF + "extra_terrain")
    caves_ = range_choice(sloped, -1000000.0, 1.5625, surface, underground(sloped))
    post = unary("squeeze", unary("interpolated", mul(unary("blend_density", slide(caves_)), 0.64)))
    final = dmin(post, "minecraft:overworld/caves/noodle")

    factor = unary("cache_2d", DF + "factor")
    offset = unary("cache_2d", DF + "offset")
    # vanilla's remap(0.2734375 / factor - offset, 1.5, -1.5, -64, 320): the y where the base density reaches 0
    upper = add(mul(add(mul(0.2734375, unary("invert", factor)), mul(-1.0, offset)), -128.0), 128.0)
    upper = clamp(upper, -40.0, TOP_Y - 1)
    gradient = mul(4.0, unary("quarter_negative", mul(add(ygrad(MIN_Y, TOP_Y, 1.5, GRAD_TOP_VALUE), offset), factor)))
    surface_density = add(slide(clamp(add(gradient, -0.703125), -64.0, 64.0)), -0.390625)
    preliminary = {"type": "minecraft:find_top_surface", "density": surface_density, "upper_bound": upper,
                   "lower_bound": MIN_Y, "cell_height": 8}

    def vein(n):
        return unary("interpolated", range_choice(Y, -60, 51, noise(n, 4.0, 4.0), 0.0))
    return {
        "barrier": noise("minecraft:aquifer_barrier", 1.0, 0.5),
        "fluid_level_floodedness": dmax(noise("minecraft:aquifer_fluid_level_floodedness", 1.0, 0.67),
                                        DF + "underground_river_flood"),
        "fluid_level_spread": noise("minecraft:aquifer_fluid_level_spread", 1.0, 0.7142857142857143),
        "lava": noise("minecraft:aquifer_lava"),
        "temperature": DF + "temperature",
        "vegetation": DF + "vegetation",
        "continents": CONT,
        "erosion": EROS,
        "depth": DF + "depth",
        "ridges": WEIRD,
        "preliminary_surface_level": preliminary,
        "final_density": final,
        "vein_toggle": unary("interpolated", range_choice(Y, -60, 51, noise("minecraft:ore_veininess", 1.5, 1.5), 0.0)),
        "vein_ridged": add(-0.07999999821186066, dmax(unary("abs", vein("minecraft:ore_vein_a")),
                                                      unary("abs", vein("minecraft:ore_vein_b")))),
        "vein_gap": noise("minecraft:ore_gap"),
    }


def noise_json():
    return {name: {"firstOctave": o, "amplitudes": a} for name, (o, a) in NOISES.items()}


def dimension_type():
    """minecraft:dimension_type/overworld, 448 blocks tall (vanilla's values otherwise, DimensionTypes.bootstrap)."""
    return {
        "has_skylight": True, "has_ceiling": False, "has_ender_dragon_fight": False, "coordinate_scale": 1.0,
        "min_y": MIN_Y, "height": HEIGHT, "logical_height": HEIGHT,
        "infiniburn": "#minecraft:infiniburn_overworld", "ambient_light": 0.0,
        "monster_spawn_light_level": {"type": "minecraft:uniform", "min_inclusive": 0, "max_inclusive": 7},
        "monster_spawn_block_light_limit": 0,
        "attributes": {
            "minecraft:visual/fog_color": "#c0d8ff",
            "minecraft:visual/sky_color": "#78a7ff",
            "minecraft:visual/ambient_light_color": "#0a0a0a",
            "minecraft:visual/cloud_color": "#ccffffff",
            "minecraft:visual/cloud_height": 192.33,
            "minecraft:audio/background_music": {
                "default": {"sound": "minecraft:music.game", "min_delay": 12000, "max_delay": 24000},
                "creative": {"sound": "minecraft:music.creative", "min_delay": 12000, "max_delay": 24000}},
            "minecraft:gameplay/bed_rule": {"can_sleep": "when_dark", "can_set_spawn": "always",
                                            "error_message": {"translate": "block.minecraft.bed.no_sleep"}},
            "minecraft:gameplay/respawn_anchor_works": False,
            "minecraft:gameplay/nether_portal_spawns_piglin": True,
            "minecraft:audio/ambient_sounds": {"mood": {"sound": "minecraft:ambient.cave", "tick_delay": 6000,
                                                         "block_search_extent": 8, "offset": 2.0}},
        },
        "timelines": "#minecraft:in_overworld",
        "default_clock": "minecraft:overworld",
    }

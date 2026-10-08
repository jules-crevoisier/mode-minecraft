"""Ore faces drawn as hand-pixelled stamps on a clustered host stone (texkit.host).

Every metal gets its own mineral shape so the ores read apart at a glance, not as recoloured speckles:
  zinc       - flat angular platelets stacked like slate flakes, cool silver with a bright top edge
  mithril    - thin branching veins with star glints where they cross
  orichalcum - fat rounded nuggets with a molten core glowing through the netherrack
  aether     - upright hexagonal prisms with a soft cyan glow in the stone around them
  lithite    - shards bursting diagonally from a geode pocket

Stamp legend: '.' keep the host, 's' cast shadow / socket (darkest host tone), 'h' lit host rim, '1'..'5' the
mineral ramp (dark -> light), 'g' a near-white glint, 'o' glow halo blended into the host.
"""
from . import texkit as K

STAMPS = {
    "zinc_a": """
....455g.
..445554.
.3444332s
.22333s1s
..2211s..
...sss...
""",
    "zinc_b": """
..4g5.
.44552
.3332s
..21s.
...s..
""",
    "zinc_c": """
.45g..
45554.
233343s
.1122s.
..sss..
""",
    "ori_a": """
.o455o
o45552s
o45443s
.33432s
..1222s
...sss.
""",
    "ori_b": """
.o45o
o4553s
.4432s
..12ss
..ss.
""",
    "aether_a": """
....g...
...o5o..
..o454.5
..o453o4
..34532o
..2453424
..2453323
...12312s
...ssssss
""",
    "aether_b": """
..g.
.o5o
o454
o453
o342s
.232s
.ss..
""",
    "lithite_a": """
...g...
..554..
.55433.
5554333s
.44322s.
..422s.
...2s..
""",
    "lithite_b": """
..g..
.543.
54433s
.432s.
..2s..
""",
    "lithite_c": """
.5.
5433
.2s.
""",
}

# (stamp, x, y, mirror) per ore design and host; deepslate variants are laid out differently so the two blocks
# are not one image recoloured
LAYOUTS = {
    ("zinc", "stone"): [("zinc_a", 1, 1, False), ("zinc_b", 10, 3, False), ("zinc_c", 3, 9, False),
                        ("zinc_b", 10, 11, True)],
    ("zinc", "deepslate"): [("zinc_c", 8, 1, True), ("zinc_a", 0, 6, True), ("zinc_b", 9, 9, False),
                            ("zinc_b", 2, 12, True)],
    ("mithril", "deepslate"): [],
    ("orichalcum", "netherrack"): [("ori_a", 1, 1, False), ("ori_b", 10, 2, False), ("ori_b", 3, 9, True),
                                   ("ori_a", 9, 9, True)],
    ("aether", "stone"): [("aether_a", 1, 2, False), ("aether_b", 11, 1, False), ("aether_b", 10, 9, True)],
    ("aether", "deepslate"): [("aether_a", 7, 6, True), ("aether_b", 2, 1, False), ("aether_b", 1, 9, True)],
    ("lithite", "stone"): [("lithite_a", 1, 1, False), ("lithite_b", 10, 3, False), ("lithite_c", 6, 9, False),
                           ("lithite_a", 8, 8, False), ("lithite_c", 1, 11, False)],
    ("lithite", "deepslate"): [("lithite_a", 8, 1, False), ("lithite_b", 1, 3, False), ("lithite_a", 2, 8, False),
                               ("lithite_c", 11, 10, False), ("lithite_c", 13, 13, False)],
}

# mineral base colours (the ramp is hue-shifted around them); the glint and glow colours
MINERALS = {
    "zinc": dict(base=(150, 166, 184), glint=(244, 250, 255), glow=None, span=(-0.72, 0.72)),
    "mithril": dict(base=(140, 196, 236), glint=(240, 252, 255), glow=None, span=(-0.6, 0.78)),
    "orichalcum": dict(base=(232, 128, 62), glint=(255, 244, 196), glow=(255, 150, 60), span=(-0.62, 0.66)),
    "aether": dict(base=(64, 214, 228), glint=(236, 255, 255), glow=(90, 230, 255), span=(-0.6, 0.72)),
    "lithite": dict(base=(58, 198, 166), glint=(230, 255, 240), glow=(110, 240, 200), span=(-0.62, 0.7)),
}


def _rows(stamp, mirror):
    rows = STAMPS[stamp].strip("\n").split("\n")
    if mirror:
        w = max(len(r) for r in rows)
        flip = {"s": "s"}
        rows = ["".join(flip.get(c, c) for c in reversed(r.ljust(w, "."))) for r in rows]
    return rows


# mithril: a lumpy seam that leaves the right edge at the height it enters the left one, so neighbouring blocks
# join up into one long vein; a thin branch climbs from it and two loose nodules sit in the rock
MITHRIL_SEAM_Y = [10, 10, 9, 9, 8, 8, 8, 7, 7, 7, 8, 8, 9, 10, 10, 10]
MITHRIL_SEAM_T = [2, 2, 2, 3, 2, 2, 1, 2, 3, 2, 2, 2, 1, 2, 2, 2]
MITHRIL_BRANCH = [(9, 6), (10, 5), (10, 4), (11, 3), (12, 2)]
MITHRIL_NODULES = [(3, 2.6, 1.6), (12.5, 13.5, 1.7), (8.5, 7.5, 1.9)]
MITHRIL_GLINTS = [(8, 6), (3, 7), (12, 12), (12, 2)]


def _mithril(cv, ht, tones, glint):
    occ = {}
    for x in range(16):
        y0, t = MITHRIL_SEAM_Y[x], MITHRIL_SEAM_T[x]
        for k in range(t):
            occ[(x, y0 + k)] = 4 if k == 0 else 1 if k == t - 1 else 2
    for x, y in MITHRIL_BRANCH:
        occ.setdefault((x, y), 3)
    for cx, cy, r in MITHRIL_NODULES:
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                if dx * dx + dy * dy <= r * r:
                    k = (dx + dy) / (r * 1.41)
                    occ[(x, y)] = 4 if k < -0.35 else 3 if k < 0.2 else 2 if k < 0.55 else 1
    for (x, y), t in occ.items():
        for sx, sy in ((x, y + 1), (x + 1, y + 1)):
            if (sx % 16, sy % 16) not in occ:
                cv.set(sx % 16, sy % 16, ht[0])
    for (x, y), t in occ.items():
        cv.set(x % 16, y % 16, tones[t])
    for x, y in MITHRIL_GLINTS:
        cv.set(x, y, glint)


def ore(metal, host_name, seed=0):
    m = MINERALS[metal]
    cv, ht = K.host(host_name, f"{metal}{seed}")
    tones = K.ramp(m["base"], 5, *m["span"])
    if metal == "mithril":
        _mithril(cv, ht, tones, m["glint"])
    for stamp, ox, oy, mirror in LAYOUTS[(metal, host_name)]:
        rows = _rows(stamp, mirror)
        if mirror:
            # mirrored stamps keep the light on the top-left: swap the lit/shaded columns of each row
            rows = [_relight(r) for r in rows]
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                px, py = ox + x, oy + y
                if ch == "." or not (0 <= px < 16 and 0 <= py < 16):
                    continue
                if ch == "s":
                    cv.set(px, py, ht[0])
                elif ch == "h":
                    cv.set(px, py, ht[4])
                elif ch == "g":
                    cv.set(px, py, m["glint"])
                elif ch == "o":
                    if m["glow"]:
                        cv.set(px, py, K.mix(cv.get(px, py), m["glow"], 0.42))
                else:
                    cv.set(px, py, tones[int(ch) - 1])
    return cv


def _relight(row):
    """After a horizontal flip a shape's lit edge ends up on the right: walk each run of mineral pixels and give
    its leftmost pixel the run's brightest tone and its rightmost the darkest, so light stays top-left."""
    out = list(row)
    i = 0
    while i < len(out):
        if out[i] in "12345":
            j = i
            while j < len(out) and out[j] in "12345":
                j += 1
            run = sorted(out[i:j], reverse=True)
            out[i:j] = run
            # the shadow socket follows to the right of the run
            if i > 0 and out[i - 1] == "s" and (j >= len(out) or out[j] == "."):
                out[i - 1] = "."
                if j < len(out):
                    out[j] = "s"
            i = j
        else:
            i += 1
    return "".join(out)

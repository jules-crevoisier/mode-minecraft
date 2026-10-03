"""Static "would it survive in game?" checks for structure blueprints.

Jigsaw pieces are placed without shape updates, so an unsupported torch, lantern, vine or door stays
floating until a neighbour update makes it pop off as an item. These checks apply the vanilla 26.2
survival rules to every block of a blueprint, plus door usability, floating debris and foundations.

Unset cells (structure void) keep whatever terrain is there. ``Context`` says how to treat them:
below ``ground`` (or everywhere when ``unset_solid``) they count as solid terrain, else as air.
"""
from .blueprint import DIRS, HORIZONTAL, OPPOSITE, CCW, CW, is_solid

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:structure_void"}
FLUIDS = {"minecraft:water", "minecraft:lava", "minecraft:bubble_column"}
SOIL = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "mud", "muddy_mangrove_roots",
        "farmland", "mycelium", "pale_moss_block", "dirt_path", "clay", "sand", "red_sand", "suspicious_sand",
        "soul_sand", "soul_soil", "crimson_nylium", "warped_nylium", "netherrack", "end_stone", "gravel",
        "snow_block", "terracotta", "packed_mud"}
PLANTS = ("_flower", "poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", "_tulip", "oxeye_daisy",
          "cornflower", "lily_of_the_valley", "wither_rose", "torchflower", "pink_petals", "wildflowers",
          "short_grass", "tall_grass", "fern", "large_fern", "_sapling", "bush", "dead_bush", "sweet_berry",
          "sunflower", "lilac", "rose_bush", "peony", "pitcher_plant", "leaf_litter", "firefly_bush",
          "short_dry_grass", "tall_dry_grass", "closed_eyeblossom", "open_eyeblossom", "cactus_flower",
          "_roots", "_fungus", "nether_sprouts", "propagule", "azalea", "big_dripleaf", "small_dripleaf",
          "bamboo", "sugar_cane", "cactus")
NOT_PLANTS = ("_roots_block", "hanging_roots", "mangrove_roots", "azalea_leaves", "_leaves", "potted_",
              "flower_pot", "bamboo_planks", "bamboo_block", "bamboo_mosaic", "bamboo_stairs", "bamboo_slab",
              "bamboo_fence", "bamboo_door", "bamboo_trapdoor", "bamboo_button", "bamboo_pressure_plate",
              "bamboo_sign", "bamboo_wall_sign", "bamboo_hanging_sign", "bamboo_raft", "stripped_bamboo",
              "rooted_dirt", "_pot")
GRAVITY = ("sand", "red_sand", "gravel", "_concrete_powder", "anvil", "chipped_anvil", "damaged_anvil",
           "suspicious_sand", "suspicious_gravel", "dragon_egg", "scaffolding")
CENTER_BELOW = ("torch", "lantern", "candle", "pressure_plate", "end_rod", "lightning_rod", "brewing_stand")
RIGID_BELOW = ("rail", "redstone_wire", "repeater", "comparator")
ANY_BELOW = ("carpet", "snow", "moss_carpet", "pale_moss_carpet")
# blocks whose collision shape is a full cube but that are still not "sturdy" for torches etc.
NOT_STURDY = {"minecraft:barrier"}
LEAVES = "_leaves"
CENTER_SUPPORT = ("_fence", "_wall", "iron_chain", "chain", "iron_bars", "glass_pane", "_bars", "end_rod",
                  "lightning_rod", "_fence_gate")
PASSABLE_HINTS = ("torch", "carpet", "pressure_plate", "button", "lever", "rail", "redstone_wire", "sign",
                  "banner", "vine", "ladder", "flower", "grass", "fern", "sapling", "bush", "petals", "lantern",
                  "candle", "mist_gate", "cobweb", "snow", "leaf_litter", "dead_bush", "seagrass", "kelp",
                  "lily_pad", "sculk_vein", "glow_lichen", "head", "skull", "light")


class Context:
    def __init__(self, ground=None, unset_solid=False, sky=False):
        self.ground = ground          # unset cells at y <= ground are terrain
        self.unset_solid = unset_solid  # underground structure: every unset cell is terrain
        self.sky = sky                # floating structure: nothing anchors it to terrain


def short(name):
    return name.split(":", 1)[1]


def is_plant(name):
    s = short(name)
    return any(h in s for h in PLANTS) and not any(h in s for h in NOT_PLANTS)


class Checker:
    def __init__(self, blocks, ctx):
        self.blocks = blocks  # (x, y, z) -> (name, props, data)
        self.ctx = ctx
        self.issues = []

    # ------------------------------------------------------------ cell classification
    def terrain(self, p):
        if p in self.blocks:
            return False
        if self.ctx.unset_solid:
            return True
        return self.ctx.ground is not None and p[1] <= self.ctx.ground

    def at(self, p):
        return self.blocks.get(p)

    def empty(self, p):
        """Air or something you can walk/fall through."""
        b = self.at(p)
        if b is None:
            return not self.terrain(p)
        return b[0] in AIR

    def fluid(self, p):
        b = self.at(p)
        return b is not None and b[0] in FLUIDS

    def full(self, p, face):
        """Is the face of block ``p`` that points ``face`` (towards the dependent block) sturdy?"""
        b = self.at(p)
        if b is None:
            return self.terrain(p)
        name, props = b[0], b[1]
        if name in AIR or name in FLUIDS or name in NOT_STURDY:
            return False
        s = short(name)
        if LEAVES in s:
            return False
        if s.endswith("_slab"):
            t = props.get("type", "bottom")
            return t == "double" or (t == "top" and face == "up") or (t == "bottom" and face == "down")
        if s.endswith("_stairs"):
            half = props.get("half", "bottom")
            if face == "down":
                return half == "bottom"
            if face == "up":
                return half == "top"
            return props.get("facing") == face  # the tall back of the stair
        if s.endswith("_trapdoor"):
            return props.get("open") == "false" and ((face == "up" and props.get("half") == "top")
                                                     or (face == "down" and props.get("half") == "bottom"))
        return is_solid(name) and "glass_pane" not in s

    def center(self, p, face):
        """Can it hold a torch/lantern on its ``face`` (vanilla canSupportCenter)?"""
        if self.full(p, face):
            return True
        b = self.at(p)
        if b is None:
            return False
        s = short(b[0])
        if face in ("up", "down") and any(h in s for h in CENTER_SUPPORT):
            if "chain" in s:
                return b[1].get("axis", "y") == "y"
            return True
        if face == "up" and s.endswith("_stairs"):
            return False
        return False

    def nonair(self, p):
        b = self.at(p)
        if b is None:
            return self.terrain(p)
        return b[0] not in AIR and b[0] not in FLUIDS

    def passable(self, p):
        b = self.at(p)
        if b is None:
            return not self.terrain(p)
        if b[0] in AIR:
            return True
        s = short(b[0])
        if s.endswith("_door") or s.endswith("_fence_gate"):
            return True
        if s.endswith("_trapdoor"):
            return b[1].get("open") == "true"
        return any(h in s for h in PASSABLE_HINTS) and not s.endswith("_block") and "lantern" not in s

    def walkable(self, p):
        x, y, z = p
        if not self.passable((x, y + 1, z)):
            return False
        b = self.at(p)
        if b is not None and (short(b[0]).endswith("_slab") or short(b[0]).endswith("_stairs")):
            return b[1].get("type", b[1].get("half")) in ("bottom",) or short(b[0]).endswith("_stairs")
        return self.passable(p) and self.nonair((x, y - 1, z)) and not self.fluid((x, y - 1, z))

    # ------------------------------------------------------------ helpers
    def add(self, kind, p, msg):
        self.issues.append((kind, p, msg))

    @staticmethod
    def step(p, d, n=1):
        dx, dy, dz = DIRS[d]
        return (p[0] + dx * n, p[1] + dy * n, p[2] + dz * n)

    # ------------------------------------------------------------ rules
    def check_block(self, p, name, props):
        s = short(name)
        below, above = self.step(p, "down"), self.step(p, "up")

        if s.endswith("_door"):
            return self.check_door(p, name, props)
        if s.endswith("wall_torch") or s.endswith("_wall_banner") or s.endswith("_wall_sign") or s == "ladder":
            f = props.get("facing")
            if f and not self.full(self.step(p, OPPOSITE[f]), f):
                self.add("support", p, f"{s} facing {f} has nothing solid behind it")
            return
        if s.endswith("_button") or s == "lever" or s.endswith("grindstone"):
            face = props.get("face", "wall")
            if face == "floor" and not self.full(below, "up"):
                self.add("support", p, f"{s} on the floor over nothing")
            elif face == "ceiling" and not self.full(above, "down"):
                self.add("support", p, f"{s} on the ceiling under nothing")
            elif face == "wall":
                f = props.get("facing")
                if f and not self.full(self.step(p, OPPOSITE[f]), f):
                    self.add("support", p, f"{s} on a wall of nothing")
            return
        if s in ("lantern", "soul_lantern", "copper_lantern") or s.endswith("_lantern"):
            if props.get("hanging") == "true":
                if not self.center(above, "down"):
                    self.add("support", p, f"hanging {s} with nothing above")
            elif not self.center(below, "up"):
                self.add("support", p, f"standing {s} over nothing")
            return
        if s == "bell":
            att = props.get("attachment", "floor")
            if att == "ceiling" and not self.center(above, "down"):
                self.add("support", p, "ceiling bell with nothing above")
            elif att == "floor" and not self.full(below, "up"):
                self.add("support", p, "floor bell over nothing")
            return
        if s.endswith("hanging_sign") and "wall" not in s:
            if not self.nonair(above):
                self.add("support", p, f"{s} with nothing above")
            return
        if s in ("hanging_roots", "spore_blossom", "pale_hanging_moss", "weeping_vines", "weeping_vines_plant",
                 "cave_vines", "cave_vines_plant"):
            if not self.nonair(above):
                self.add("support", p, f"{s} with nothing above")
            return
        if s in ("pointed_dripstone",):
            d = "down" if props.get("vertical_direction") == "down" else "up"
            anchor = above if d == "down" else below
            if not self.nonair(anchor):
                self.add("support", p, "dripstone attached to nothing")
            return
        if s.endswith("amethyst_cluster") or s.endswith("amethyst_bud"):
            f = props.get("facing", "up")
            if not self.full(self.step(p, OPPOSITE[f]), f):
                self.add("support", p, f"{s} attached to nothing")
            return
        if s == "vine":
            return self.check_vine(p, props)
        if s == "cocoa":
            f = props.get("facing")
            b = self.at(self.step(p, f)) if f else None
            if not b or "jungle" not in b[0]:
                self.add("support", p, "cocoa not on a jungle log")
            return
        if any(s.endswith(h) or s == h for h in CENTER_BELOW) and "wall" not in s:
            if not self.center(below, "up"):
                self.add("support", p, f"{s} over nothing")
            return
        if s.endswith("_sign") or (s.endswith("_banner") and "wall" not in s):
            if not self.nonair(below):
                self.add("support", p, f"{s} over nothing")
            return
        if any(s.endswith(h) for h in RIGID_BELOW):
            if not self.full(below, "up"):
                self.add("support", p, f"{s} over nothing")
            return
        if any(s.endswith(h) for h in ANY_BELOW) and s != "snow_block":
            if not self.nonair(below):
                self.add("support", p, f"{s} over nothing")
            return
        if s in GRAVITY or any(s.endswith(g) for g in GRAVITY if g.startswith("_")):
            if not self.nonair(below):
                self.add("gravity", p, f"{s} will fall")
            return
        if is_plant(name):
            if props.get("half") == "upper":
                b = self.at(below)
                if not b or b[0] != name:
                    self.add("support", p, f"upper {s} without its lower half")
                return
            if s in ("sugar_cane", "bamboo", "cactus"):
                b = self.at(below)
                if b and b[0] == name:
                    return
            if s in ("big_dripleaf",):
                return
            b = self.at(below)
            if b is None:
                if not self.terrain(below):
                    self.add("support", p, f"{s} floating over nothing")
            elif short(b[0]) not in SOIL and not any(short(b[0]).endswith(x) for x in ("_terracotta", "_nylium")):
                if "mushroom" not in s and "fungus" not in s and "roots" not in s:
                    self.add("support", p, f"{s} planted on {short(b[0])}")

    def check_vine(self, p, props):
        faces = [d for d in HORIZONTAL if props.get(d) == "true"]
        if props.get("up") == "true":
            faces.append("up")
        if not faces:
            self.add("support", p, "vine with no faces")
            return
        ok = 0
        for d in faces:
            nb = self.step(p, d)
            b = self.at(nb)
            if b is not None and LEAVES in short(b[0]):
                ok += 1  # leaves have a full collision face: vines cling to them
                continue
            if self.full(nb, OPPOSITE[d]):
                ok += 1
                continue
            if d != "up":
                above = self.at(self.step(p, "up"))
                if above and short(above[0]) == "vine" and above[1].get(d) == "true":
                    ok += 1
        if ok == 0:
            self.add("support", p, "vine clinging to nothing")

    def check_door(self, p, name, props):
        if props.get("half") == "upper":
            b = self.at(self.step(p, "down"))
            if not b or b[0] != name or b[1].get("half") != "lower":
                self.add("door", p, "upper door half without its lower half")
            return
        up = self.at(self.step(p, "up"))
        if not up or up[0] != name or up[1].get("half") != "upper":
            self.add("door", p, "lower door half without its upper half")
        elif any(up[1].get(k) != props.get(k) for k in ("facing", "hinge", "open")):
            self.add("door", p, "door halves disagree (facing/hinge/open)")
        if not self.full(self.step(p, "down"), "up"):
            self.add("door", p, "door standing on nothing")
        if props.get("open") == "true":
            self.add("door", p, "door left open")
        f = props.get("facing")
        if not f:
            return
        for side in (f, OPPOSITE[f]):
            front = self.step(p, side)
            if not (self.passable(front) and self.passable(self.step(front, "up"))):
                self.add("door", p, f"door blocked on its {side} side")
                continue
            if self.walk_area(front) < 3:
                self.add("door", p, f"door opens onto a drop on its {side} side")
        # double doors: neighbours on the wall line
        for d, want in ((CCW[f], "right"), (CW[f], "left")):
            nb = self.at(self.step(p, d))
            if nb and short(nb[0]).endswith("_door") and nb[1].get("half") == "lower" and nb[1].get("facing") == f:
                if props.get("hinge") != want:
                    self.add("door", p, f"double door hinge should be {want} (vanilla pairing)")
            gap, far = self.at(self.step(p, d)), self.at(self.step(p, d, 2))
            if (gap is None or gap[0] in AIR) and far and short(far[0]).endswith("_door") \
                    and far[1].get("facing") == f and far[1].get("half") == "lower":
                self.add("door", p, "door - gap - door: double door with a hole in the middle")

    def walk_area(self, start, limit=3):
        """Walkable cells reachable from ``start`` within ``limit`` steps (flat or one step up/down)."""
        if not self.walkable(start) and not self.fluid(start):
            # no floor directly in front: maybe stairs going down
            down = self.step(start, "down")
            if not self.walkable(down):
                return 0
            start = down
        seen = {start}
        frontier = [start]
        for _ in range(limit):
            nxt = []
            for c in frontier:
                for d in HORIZONTAL:
                    n = self.step(c, d)
                    for cand in (n, self.step(n, "up"), self.step(n, "down")):
                        if cand not in seen and (self.walkable(cand) or self.fluid(cand)):
                            seen.add(cand)
                            nxt.append(cand)
                            break
            frontier = nxt
        return len(seen)

    def check_islands(self):
        """Clumps of blocks that touch neither the main mass nor terrain."""
        solid = {p for p, b in self.blocks.items() if b[0] not in AIR}
        comps = []
        seen = set()
        for start in solid:
            if start in seen:
                continue
            comp, stack, anchored = [], [start], False
            seen.add(start)
            while stack:
                c = stack.pop()
                comp.append(c)
                for d in DIRS:
                    n = self.step(c, d)
                    if n in solid:
                        if n not in seen:
                            seen.add(n)
                            stack.append(n)
                    elif self.terrain(n):
                        anchored = True
            comps.append((comp, anchored))
        if not comps:
            return
        biggest = max(len(c) for c, _ in comps)
        for comp, anchored in comps:
            if anchored or len(comp) == biggest:
                continue
            if self.ctx.sky and len(comp) >= 40:
                continue  # separate floating rocks of a sky/End structure are part of the design
            p = min(comp)
            names = sorted({short(self.blocks[c][0]) for c in comp})[:4]
            self.add("island", p, f"{len(comp)} floating block(s) ({', '.join(names)})")

    def run(self):
        for p, (name, props, _) in self.blocks.items():
            if name in AIR:
                continue
            self.check_block(p, name, props)
        self.check_islands()
        return self.issues


def check(blocks, ctx):
    return Checker(blocks, ctx).run()


def context_for(sdef):
    if sdef.height is None:
        return Context(ground=sdef.ground, sky=sdef.height_offset > 0)
    top = sdef.height[-1]
    if sdef.dimension == "overworld" and top < 0:
        return Context(unset_solid=True)
    if sdef.adaptation.startswith("beard") or sdef.adaptation == "bury":
        return Context(ground=sdef.ground)
    return Context(sky=True)


def stair_rules_ok(processors):
    """Processor rules must keep the properties of stairs/slabs/doors they rewrite."""
    bad = []
    for proc in processors.get("processors", []):
        for rule in proc.get("rules", []):
            src = rule["input_predicate"].get("block") or rule["input_predicate"].get("block_state", {}).get("Name", "")
            out = rule["output_state"]
            if any(src.endswith(s) for s in ("_stairs", "_slab", "_door", "_trapdoor", "_wall", "_fence")) \
                    and not out.get("Properties"):
                bad.append(src)
    return bad

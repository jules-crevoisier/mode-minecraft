"""Vanilla 26.2 village and pillager-outpost template pools, as the game's data generator writes them.

In 26.2 these pools are built in code (``PlainVillagePools``, ``DesertVillagePools``, ..., ``PillagerOutpostPools``
in ``net.minecraft.data.worldgen``), so there is no JSON to copy: ``extract`` reads those classes and rebuilds the
pool JSON, and the result is kept in ``vanilla_village_pools.json`` next to this file. ``wf/village.py`` overrides
the vanilla pools with copies of these that keep every vanilla element and weight and add ours.

Refresh after a Minecraft update (path = the decompiled common sources, the folder that holds ``net/``):
    python3 tools/wf/vanilla_pools.py <sources>
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "vanilla_village_pools.json")
FILES = ["PlainVillagePools", "DesertVillagePools", "SavannaVillagePools", "SnowyVillagePools", "TaigaVillagePools",
         "PillagerOutpostPools"]

TOKEN = re.compile(r'\s*(?:(?P<str>"(?:[^"\\]|\\.)*")|(?P<num>-?\d+)|(?P<name>new\s+[\w.]+|[\w.]+)|(?P<sym>[(),]))')


def _tokens(text):
    pos, out = 0, []
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"cannot parse near: {text[pos:pos + 60]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def _parse(tokens, i=0):
    """expr := STR | NUM | NAME [ '(' expr {',' expr} ')' ] -> (node, next index). Calls are ('call', name, args)."""
    kind, val = tokens[i]
    if kind == "str":
        return ("str", json.loads(val)), i + 1
    if kind == "num":
        return ("num", int(val)), i + 1
    if kind != "name":
        raise ValueError(f"unexpected {val}")
    name = val.replace("new ", "new:").strip()
    i += 1
    if i < len(tokens) and tokens[i] == ("sym", "("):
        args = []
        i += 1
        while tokens[i] != ("sym", ")"):
            node, i = _parse(tokens, i)
            args.append(node)
            if tokens[i] == ("sym", ","):
                i += 1
        return ("call", name, args), i + 1
    return ("name", name), i


def _balanced(text, start):
    """Text of the parenthesised group opening at ``start`` (the '(' itself), without the parentheses."""
    depth, i, in_str = 0, start, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    raise ValueError("unbalanced parentheses")


def _keys(path, pattern):
    """CONST -> "id" for ``CONST = <pattern>("id")`` in a Java file."""
    text = open(path, encoding="utf-8").read()
    return {m.group(1): m.group(2) for m in re.finditer(r'\b([A-Z_0-9]+)\s*=\s*' + pattern + r'\("([a-z0-9_/]+)"\)', text)}


def extract(src):
    wg = os.path.join(src, "net", "minecraft", "data", "worldgen")
    procs = {k: "minecraft:" + v for k, v in _keys(os.path.join(wg, "ProcessorLists.java"), r"createKey").items()}
    feats = {k: "minecraft:" + v for k, v in
             _keys(os.path.join(wg, "placement", "VillagePlacements.java"), r"PlacementUtils\.createKey").items()}
    pools = {}
    for cls in FILES:
        text = open(os.path.join(wg, cls + ".java"), encoding="utf-8").read()
        keys = {k: "minecraft:" + v for k, v in _keys(os.path.join(wg, cls + ".java"), r"Pools\.createKey").items()}
        keys["Pools.EMPTY"] = "minecraft:empty"
        holders = {}
        for m in re.finditer(r'Holder<(\w+)>\s+(\w+)\s*=\s*\w+\.getOrThrow\(([\w.]+)\)', text):
            kind, var, const = m.groups()
            short = const.split(".")[-1]
            if kind == "PlacedFeature":
                holders[var] = feats[short]
            elif kind == "StructureProcessorList":
                holders[var] = procs[short]
            else:
                holders[var] = keys.get(const) or keys[short]

        def element(node, projection):
            _, fn, args = node
            fn = fn.split(".")[-1]
            if fn == "empty":
                return {"element_type": "minecraft:empty_pool_element"}
            if fn == "legacy":
                loc = args[0][1]
                return {"element_type": "minecraft:legacy_single_pool_element",
                        "location": loc if ":" in loc else "minecraft:" + loc,
                        "processors": holders[args[1][1]] if len(args) > 1 else {"processors": []},
                        "projection": projection}
            if fn == "feature":
                return {"element_type": "minecraft:feature_pool_element", "feature": holders[args[0][1]],
                        "projection": projection}
            if fn == "list":
                inner = args[0][2]  # ImmutableList.of(...)
                return {"element_type": "minecraft:list_pool_element",
                        "elements": [element(e, projection) for e in inner], "projection": projection}
            raise ValueError(f"{cls}: unknown pool element factory {fn}")

        for m in re.finditer(r'(Pools\.register|context\.register)\s*\(', text):
            body = _balanced(text, m.end() - 1)
            args = _parse(_tokens("f(" + body + ")"))[0][2]
            if m.group(1) == "Pools.register":
                pid, pool = "minecraft:" + args[1][1], args[2]
            else:
                pid, pool = keys[args[0][1]], args[1]
            fallback, elements, projection = pool[2]
            proj = projection[1].split(".")[-1].lower()
            pools[pid] = {
                "fallback": holders[fallback[1]],
                "elements": [{"weight": pair[2][1][1], "element": element(pair[2][0], proj)}
                             for pair in elements[2]],
            }
    return pools


def load():
    with open(SNAPSHOT, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    data = extract(sys.argv[1])
    with open(SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{len(data)} pools -> {SNAPSHOT}")

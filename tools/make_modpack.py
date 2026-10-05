#!/usr/bin/env python3
"""Player and server packs of Wayfarers (docs/PUBLISHING.md).

    python3 tools/make_modpack.py configs
        Rewrites the recommended configs (modpack/overrides/config/*.toml) from the config classes of the mod
        (src/main/java/com/wayfarers/config), keeping the values already set in them. validate.py checks they match.

    python3 tools/make_modpack.py modpack --jar build/libs/wayfarers-X.jar [--project-id N --file-id N] [--out DIR]
        CurseForge modpack zip: manifest.json (modpack/manifest.json filled in), modlist.html and overrides/ (the
        recommended configs). With the CurseForge project and file ids of the mod (CI passes the ids of the file it
        just uploaded) the manifest references the mod, which is what a modpack published on CurseForge needs.
        Without them (no CurseForge project yet) the jar itself goes into overrides/mods: the zip still imports in
        the CurseForge app (Create custom profile > Import), it just cannot be published on CurseForge as is.

    python3 tools/make_modpack.py serverpack --jar build/libs/wayfarers-X.jar [--out DIR]
        Server pack zip: the jar, start scripts for Linux/macOS and Windows (they install Forge on the first run,
        ask for the EULA, back the world up when the mod version changes, and start with tuned JVM flags), the
        recommended server config and server.properties (copied only when missing, so an update never overwrites
        the admin's settings).
"""
import argparse
import json
import os
import re
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_JAVA = os.path.join(ROOT, "src", "main", "java", "com", "wayfarers", "config")
MODPACK = os.path.join(ROOT, "modpack")
SERVERPACK = os.path.join(ROOT, "serverpack")
CONFIG_OUT = os.path.join(MODPACK, "overrides", "config")
# config file -> Java class (Forge names the files <modid>-<type>.toml)
CONFIGS = {"wayfarers-client.toml": "WayfarersClientConfig.java", "wayfarers-common.toml": "WayfarersConfig.java"}
# values that differ from the mod's defaults in the recommended configs (none yet: the defaults are the recommended
# play; a public server sets compat.downloadUrl to its own modpack page)
RECOMMENDED = {"wayfarers-client.toml": {}, "wayfarers-common.toml": {}}
JSTR = r'"(?:[^"\\]|\\.)*"'


def gradle_properties():
    out = {}
    for line in open(os.path.join(ROOT, "gradle.properties"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ------------------------------------------------------------------ configs
def _java_string(s):
    return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")


def java_config(java_file):
    """[{key, kind, default (TOML text), comments [lines], range (min, max) or None, values [enum] or None}]."""
    src = open(os.path.join(CONFIG_JAVA, java_file), encoding="utf-8").read()
    enums = {}
    for m in re.finditer(r"enum\s+(\w+)\s*\{([^}]*)\}", src):
        body = m.group(2).split(";")[0]
        enums[m.group(1)] = re.findall(r"\b([A-Z][A-Z0-9_]*)\b\s*(?:\(|,|$)", body.strip())
    out = []
    for m in re.finditer(r'(?:\.comment\(((?:' + JSTR + r'\s*,?\s*)+)\)\s*)?\.define(\w*)\("([\w.]+)",\s*([^;]+?)\);', src):
        comments = [_java_string(x) for x in re.findall(JSTR, m.group(1) or "")]
        kind, key = m.group(2) or "", m.group(3)
        args = [a.strip() for a in re.split(r",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", m.group(4))]
        entry = {"key": key, "kind": kind, "comments": comments, "range": None, "values": None}
        default = args[0]
        if kind == "Enum":
            enum, _, value = default.rpartition(".")
            entry["values"] = enums.get(enum)
            entry["default"] = json.dumps(value)
        elif kind == "InRange":
            entry["range"] = (args[1], args[2])
            entry["default"] = default.rstrip("dDfFL")
        elif default.startswith('"'):
            entry["default"] = json.dumps(_java_string(default))
        else:
            entry["default"] = default
        out.append(entry)
    return out


def read_toml_values(path):
    """{dotted key: TOML value text} of a flat Forge config file (one level of [sections])."""
    values, section = {}, ""
    if not os.path.isfile(path):
        return values
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[([\w.]+)\]$", s)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"^([\w]+)\s*=\s*(.+)$", s)
        if m:
            values[(section + "." if section else "") + m.group(1)] = m.group(2).strip()
    return values


def render_toml(name, entries, values):
    lines = [f"# Wayfarers recommended {name} (tools/make_modpack.py configs from the mod's config classes).",
             "# Forge reads it from the config folder; every value is the mod's default unless noted below.", ""]
    section = None
    for e in entries:
        sec, _, leaf = e["key"].rpartition(".")
        if sec != section:
            if section is not None:
                lines.append("")
            lines.append(f"[{sec}]")
            section = sec
        for c in e["comments"]:
            lines.append(f"\t#{c}")
        if e["range"]:
            lines.append(f"\t#Range: {e['range'][0]} ~ {e['range'][1]}")
        if e["values"]:
            lines.append(f"\t#Allowed Values: {', '.join(e['values'])}")
        lines.append(f"\t{leaf} = {values.get(e['key'], e['default'])}")
    return "\n".join(lines) + "\n"


def write_configs():
    os.makedirs(CONFIG_OUT, exist_ok=True)
    for name, java in CONFIGS.items():
        path = os.path.join(CONFIG_OUT, name)
        entries = java_config(java)
        keys = {e["key"] for e in entries}
        values = {k: v for k, v in read_toml_values(path).items() if k in keys}
        values.update(RECOMMENDED[name])
        text = render_toml(name, entries, values)
        old = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
        if text != old:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("wrote", os.path.relpath(path, ROOT))


def check_configs():
    """Problems of the committed recommended configs against the config classes (for validate.py)."""
    problems = []
    for name, java in CONFIGS.items():
        path = os.path.join(CONFIG_OUT, name)
        if not os.path.isfile(path):
            problems.append(f"{os.path.relpath(path, ROOT)} is missing: python3 tools/make_modpack.py configs")
            continue
        keys = {e["key"] for e in java_config(java)}
        have = set(read_toml_values(path))
        for k in sorted(keys - have):
            problems.append(f"{name}: no '{k}' (new config value): python3 tools/make_modpack.py configs")
        for k in sorted(have - keys):
            problems.append(f"{name}: '{k}' is not a config value of the mod any more: python3 tools/make_modpack.py configs")
    return problems


# ------------------------------------------------------------------ packs
def _jar_version(jar):
    """(file-name version, mod version): wayfarers-0.9.0-beta-build.84.jar is the mod's 0.9.0-beta+build.84."""
    m = re.match(r"wayfarers-(.+)\.jar$", os.path.basename(jar))
    if not m:
        sys.exit(f"not a Wayfarers jar name: {jar}")
    return m.group(1), re.sub(r"-build\.(\w+)$", r"+build.\1", m.group(1))


def _add_tree(z, src_dir, arc_dir, subst=None):
    for base, _dirs, files in os.walk(src_dir):
        for f in sorted(files):
            path = os.path.join(base, f)
            arc = os.path.join(arc_dir, os.path.relpath(path, src_dir)).replace(os.sep, "/")
            if subst and f.endswith((".sh", ".bat", ".txt", ".md")):
                text = open(path, encoding="utf-8").read()
                for k, v in subst.items():
                    text = text.replace(k, v)
                if f.endswith(".bat"):
                    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
                info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
                info.external_attr = (0o755 if f.endswith(".sh") else 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, text)
            else:
                z.write(path, arc)


def build_modpack(jar, out_dir, project_id=None, file_id=None):
    props = gradle_properties()
    file_version, version = _jar_version(jar)
    manifest = json.load(open(os.path.join(MODPACK, "manifest.json"), encoding="utf-8"))
    manifest["version"] = version
    manifest["minecraft"]["version"] = props["minecraft_version"]
    manifest["minecraft"]["modLoaders"] = [{"id": f"forge-{props['forge_version']}", "primary": True}]
    embed = not (project_id and file_id)
    manifest["files"] = [] if embed else [{"projectID": int(project_id), "fileID": int(file_id), "required": True}]
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"wayfarers-modpack-{file_version}{'' if embed else '-curseforge'}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        z.writestr("modlist.html", "<ul>\n<li><a href=\"%s\">Wayfarers %s</a></li>\n</ul>\n"
                   % (props.get("mod_download_url", ""), version))
        _add_tree(z, os.path.join(MODPACK, "overrides"), "overrides")
        if embed:
            z.write(jar, "overrides/mods/" + os.path.basename(jar))
    print("modpack:", os.path.relpath(out, ROOT) if out.startswith(ROOT) else out,
          "(jar embedded: no CurseForge ids)" if embed else f"(CurseForge project {project_id}, file {file_id})")
    return out


def build_serverpack(jar, out_dir):
    props = gradle_properties()
    file_version, version = _jar_version(jar)
    forge = f"{props['minecraft_version']}-{props['forge_version']}"
    subst = {"@VERSION@": version, "@JAR@": os.path.basename(jar), "@FORGE@": forge,
             "@MINECRAFT@": props["minecraft_version"], "@DOWNLOAD@": props.get("mod_download_url", "")}
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"wayfarers-server-{file_version}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        _add_tree(z, SERVERPACK, "", subst)
        z.write(os.path.join(CONFIG_OUT, "wayfarers-common.toml"), "defaults/config/wayfarers-common.toml")
        z.write(jar, "mods/" + os.path.basename(jar))
    print("server pack:", os.path.relpath(out, ROOT) if out.startswith(ROOT) else out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("configs")
    for name in ("modpack", "serverpack"):
        p = sub.add_parser(name)
        p.add_argument("--jar", required=True)
        p.add_argument("--out", default=os.path.join(ROOT, "build", "packs"))
        if name == "modpack":
            p.add_argument("--project-id", default=os.environ.get("CURSEFORGE_PROJECT_ID") or None)
            p.add_argument("--file-id", default=None)
    a = ap.parse_args()
    if a.cmd == "configs":
        write_configs()
    elif a.cmd == "modpack":
        build_modpack(a.jar, a.out, a.project_id, a.file_id)
    else:
        build_serverpack(a.jar, a.out)


if __name__ == "__main__":
    main()

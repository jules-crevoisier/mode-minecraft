#!/usr/bin/env python3
"""Changelog of a release, from the git commits since the previous release tag (v*).

    python3 tools/changelog.py --version 0.9.1-beta [--to HEAD] [--out build/changelog.md]

Merge commits and pure regeneration/CI commits are left out. CI needs the full history (checkout fetch-depth: 0).
"""
import argparse
import datetime
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# subjects that say nothing to a player
NOISE = re.compile(r"^(Merge |Regenerate\b|Revert \"Regenerate|WIP\b|wip\b|CI:|ci:|Bump version)", re.I)


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True).stdout.strip()


def previous_tag(to):
    """The last v* tag before `to` (the tag on `to` itself does not count)."""
    return git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", f"{to}^") or None


def gradle_props():
    out = {}
    for line in open(os.path.join(ROOT, "gradle.properties"), encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def changelog(version, to="HEAD"):
    props = gradle_props()
    prev = previous_tag(to)
    rng = f"{prev}..{to}" if prev else to
    lines = git("log", rng, "--no-merges", "--pretty=format:%s (%h)", "-n", "300").splitlines()
    changes = [line for line in lines if line and not NOISE.match(line)]
    today = datetime.date.today().isoformat()
    out = [f"## Brasshaven {version} ({today})", "",
           f"Minecraft {props.get('minecraft_version')} · Forge {props.get('forge_version')} · Java 25", "",
           "**Update / Mise à jour:** back up your world, then put the same jar on the server and on every player "
           "(the world is kept). / Sauvegarde le monde, puis mets le même jar sur le serveur et chez chaque joueur "
           "(le monde est conservé).", "",
           f"### Changes since {prev}" if prev else "### Changes", ""]
    if not prev and len(changes) > 60:
        # first release: the whole history would bury the page
        changes = changes[:60] + [f"... and {len(changes) - 60} earlier changes (first public release)"]
    out += [f"- {c}" for c in changes] or ["- Maintenance release."]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True)
    ap.add_argument("--to", default="HEAD")
    ap.add_argument("--out")
    a = ap.parse_args()
    text = changelog(a.version, a.to)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()

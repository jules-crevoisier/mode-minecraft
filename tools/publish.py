#!/usr/bin/env python3
"""Uploads a release jar to CurseForge or Modrinth through their official APIs (docs/PUBLISHING.md).

    python3 tools/publish.py curseforge --jar build/libs/brasshaven-0.9.1-beta.jar --changelog build/changelog.md
    python3 tools/publish.py modrinth   --jar build/libs/brasshaven-0.9.1-beta.jar --changelog build/changelog.md

Settings come from the environment (GitHub secrets and variables in CI):
    CurseForge: CURSEFORGE_TOKEN (secret, https://legacy.curseforge.com/account/api-tokens), CURSEFORGE_PROJECT_ID
    Modrinth:   MODRINTH_TOKEN (secret, scope "Create versions"), MODRINTH_PROJECT_ID (project id or slug)
Without them the upload is skipped (exit 0), so the release still succeeds before the projects exist.

CurseForge: POST https://minecraft.curseforge.com/api/projects/{id}/upload-file (multipart "metadata" + "file",
header X-Api-Token); game version ids come from /api/game/versions and /api/game/version-types.
Modrinth: POST https://api.modrinth.com/v2/version (multipart "data" + "file", header Authorization).
Only the Python standard library is used. --dry-run prints what would be sent.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
USER_AGENT = "jules-crevoisier/mode-minecraft (Brasshaven release CI)"
CURSEFORGE = "https://minecraft.curseforge.com"
MODRINTH = "https://api.modrinth.com/v2"


def gradle_props():
    out = {}
    for line in open(os.path.join(ROOT, "gradle.properties"), encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def jar_version(jar):
    m = re.match(r"brasshaven-(.+)\.jar$", os.path.basename(jar))
    if not m:
        sys.exit(f"not a Brasshaven jar name: {jar}")
    return re.sub(r"-build\.(\w+)$", r"+build.\1", m.group(1))


def release_type(version, override=None):
    """alpha / beta / release from the version (0.9.0-beta -> beta), unless set explicitly."""
    if override:
        return override
    pre = version.split("+")[0].partition("-")[2].lower()
    if not pre:
        return "release"
    return "alpha" if "alpha" in pre else "beta"


def notice(msg):
    print(f"::notice::{msg}" if os.environ.get("GITHUB_ACTIONS") else msg)


def set_output(key, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def multipart(fields, files):
    """(body, content type) for urllib: fields {name: str}, files {name: path}."""
    boundary = "----brasshaven" + uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
                     + value.encode("utf-8") + b"\r\n")
    for name, path in files.items():
        with open(path, "rb") as f:
            data = f.read()
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                      f'filename="{os.path.basename(path)}"\r\nContent-Type: application/java-archive\r\n\r\n').encode()
                     + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def request(method, url, headers, body=None):
    req = urllib.request.Request(url, data=body, method=method, headers={"User-Agent": USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:2000]
        sys.exit(f"{method} {url}: HTTP {e.code}\n{detail}")


# ------------------------------------------------------------------ CurseForge
def curseforge_versions(token, mc, loader="Forge", java="Java 25"):
    """Game version ids: the Minecraft version, the loader, the Java version and both environments."""
    h = {"X-Api-Token": token}
    types = {t["id"]: t.get("slug", "") for t in request("GET", f"{CURSEFORGE}/api/game/version-types", h)}
    versions = request("GET", f"{CURSEFORGE}/api/game/versions", h)

    def pick(name, type_test):
        return [v["id"] for v in versions if v.get("name") == name and type_test(types.get(v.get("gameVersionTypeID"), ""))]

    mc_ids = pick(mc, lambda s: s.startswith("minecraft"))
    if not mc_ids:
        near = sorted({v["name"] for v in versions if v.get("name", "").startswith(mc.split(".")[0] + ".")})
        sys.exit(f"CurseForge does not list Minecraft {mc} yet (close names: {', '.join(near) or 'none'}). "
                 "Retry the job once it does.")
    ids = mc_ids + pick(loader, lambda s: s == "modloader")
    java_ids = pick(java, lambda s: s == "java")
    if not java_ids:
        notice(f"CurseForge has no '{java}' tag; the file is uploaded without a Java version")
    ids += java_ids + pick("Client", lambda s: s == "environment") + pick("Server", lambda s: s == "environment")
    return ids


def curseforge(a):
    token, project = os.environ.get("CURSEFORGE_TOKEN", ""), os.environ.get("CURSEFORGE_PROJECT_ID", "")
    if not token or not project:
        notice("CurseForge upload skipped: CURSEFORGE_TOKEN secret or CURSEFORGE_PROJECT_ID variable not set")
        return
    props, version = gradle_props(), jar_version(a.jar)
    metadata = {
        "changelog": open(a.changelog, encoding="utf-8").read() if a.changelog else f"Brasshaven {version}",
        "changelogType": "markdown",
        "displayName": f"Brasshaven {version}",
        "releaseType": release_type(version, a.release_type),
    }
    if a.dry_run:
        print(json.dumps({"project": project, "metadata": metadata, "file": a.jar}, indent=2))
        return
    metadata["gameVersions"] = curseforge_versions(token, props["minecraft_version"])
    body, ctype = multipart({"metadata": json.dumps(metadata)}, {"file": a.jar})
    r = request("POST", f"{CURSEFORGE}/api/projects/{project}/upload-file",
                {"X-Api-Token": token, "Content-Type": ctype}, body)
    file_id = (r or {}).get("id")
    print(f"CurseForge: uploaded {os.path.basename(a.jar)} to project {project} as file {file_id}")
    set_output("file_id", file_id or "")


# ------------------------------------------------------------------ Modrinth
def modrinth(a):
    token, project = os.environ.get("MODRINTH_TOKEN", ""), os.environ.get("MODRINTH_PROJECT_ID", "")
    if not token or not project:
        notice("Modrinth upload skipped: MODRINTH_TOKEN secret or MODRINTH_PROJECT_ID variable not set")
        return
    props, version = gradle_props(), jar_version(a.jar)
    h = {"Authorization": token}
    data = {
        "name": f"Brasshaven {version}",
        "version_number": version,
        "changelog": open(a.changelog, encoding="utf-8").read() if a.changelog else f"Brasshaven {version}",
        "dependencies": [],
        "game_versions": [props["minecraft_version"]],
        "version_type": release_type(version, a.release_type),
        "loaders": ["forge"],
        "featured": True,
        "status": "listed",
        "project_id": project,
        "file_parts": ["file"],
        "primary_file": "file",
    }
    if a.dry_run:
        print(json.dumps({"data": data, "file": a.jar}, indent=2))
        return
    proj = request("GET", f"{MODRINTH}/project/{project}", h)
    data["project_id"] = proj["id"]  # the API wants the id, the variable may hold the slug
    if any(v.get("version_number") == version for v in request("GET", f"{MODRINTH}/project/{proj['id']}/version", h) or []):
        notice(f"Modrinth already has Brasshaven {version}: nothing to upload")
        return
    tags = {t.get("version") for t in request("GET", f"{MODRINTH}/tag/game_version", {}) or []}
    if props["minecraft_version"] not in tags:
        sys.exit(f"Modrinth does not list Minecraft {props['minecraft_version']} yet. Retry the job once it does.")
    body, ctype = multipart({"data": json.dumps(data)}, {"file": a.jar})
    r = request("POST", f"{MODRINTH}/version", {**h, "Content-Type": ctype}, body)
    print(f"Modrinth: uploaded {os.path.basename(a.jar)} as version {(r or {}).get('id')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", choices=["curseforge", "modrinth"])
    ap.add_argument("--jar", required=True)
    ap.add_argument("--changelog")
    ap.add_argument("--release-type", choices=["alpha", "beta", "release"], default=os.environ.get("RELEASE_TYPE") or None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    (curseforge if a.site == "curseforge" else modrinth)(a)


if __name__ == "__main__":
    main()

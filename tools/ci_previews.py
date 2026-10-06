#!/usr/bin/env python3
"""Publish the CI previews (test summaries, profiles, renders, screenshots, clips) on the branch's pre-release.

    python3 tools/ci_previews.py --tag previews-<branch> --title "..." --notes-file notes.md --sha <commit> previews/*

Why not softprops/action-gh-release: it deletes and uploads every asset at once (240+ files, two requests each), which
trips GitHub's secondary rate limit; the run then fails half way with some files deleted and never uploaded (the
test summaries of run 37388245497 kept their previous version). Here the files go up one at a time with `gh release
upload --clobber`, small and important ones first (summaries, profiles, reports), with a short pause between
uploads and a growing wait and retry when GitHub pushes back. Needs GH_TOKEN and the gh CLI (both on the runners).
Exits 1 when a file could not be uploaded after its retries (listed at the end).
"""
import argparse
import os
import subprocess
import sys
import time

PAUSE = 0.8                      # seconds between uploads (content-creating requests are limited per minute)
RETRY_WAITS = [20, 60, 120, 240]  # seconds before each retry of a failed upload


def gh(*args, check=False):
    res = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {res.stderr.strip()[-500:]}")
    return res


def priority(path):
    """Text reports first, then images, then videos (the summaries matter most if the run is cut short)."""
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    if name.startswith("brasshaven-ci-"):
        return 0
    if ext in (".txt", ".md", ".json"):
        return 1
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return 2
    return 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--notes-file", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("files", nargs="*")
    args = ap.parse_args()
    files = sorted((f for f in args.files if os.path.isfile(f)), key=lambda f: (priority(f), os.path.basename(f)))
    if not files:
        print("no preview files")
        return
    if gh("release", "view", args.tag).returncode != 0:
        gh("release", "create", args.tag, "--prerelease", "--latest=false", "--target", args.sha,
           "--title", args.title, "--notes-file", args.notes_file, check=True)
        print(f"created release {args.tag}")
    else:
        gh("release", "edit", args.tag, "--prerelease", "--latest=false", "--title", args.title,
           "--notes-file", args.notes_file, check=True)
    failed = []
    for i, path in enumerate(files):
        for attempt in range(len(RETRY_WAITS) + 1):
            res = gh("release", "upload", args.tag, path, "--clobber")
            if res.returncode == 0:
                print(f"[{i + 1}/{len(files)}] uploaded {os.path.basename(path)}", flush=True)
                break
            msg = (res.stderr or res.stdout).strip().splitlines()[-1:] or ["?"]
            if attempt == len(RETRY_WAITS):
                print(f"[{i + 1}/{len(files)}] FAILED {os.path.basename(path)}: {msg[0]}", flush=True)
                failed.append(os.path.basename(path))
                break
            wait = RETRY_WAITS[attempt]
            print(f"[{i + 1}/{len(files)}] {os.path.basename(path)}: {msg[0]} - retry in {wait} s", flush=True)
            time.sleep(wait)
        time.sleep(PAUSE)
    if failed:
        print(f"::error::{len(failed)} preview file(s) not uploaded: {', '.join(failed)}")
        sys.exit(1)
    print(f"{len(files)} preview files uploaded to {args.tag}")


if __name__ == "__main__":
    main()

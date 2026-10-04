#!/usr/bin/env python3
"""Run the real Minecraft client with the mod, headless, take in-game screenshots and fail on client-side errors.

Used by the `client-test` job of .github/workflows/build.yml:
    python3 tools/ci_client.py [--timeout SECONDS] [--game-timeout SECONDS] [--early-window] [--strict]

How it works
------------
1. Display. The client needs a window and OpenGL >= 3.2 core. On a CI runner there is no GPU and no screen, so
   the script re-runs itself under `xvfb-run` (a virtual X server, 1920x1080x24) when $DISPLAY is not set, and
   points Mesa at its software renderer: LIBGL_ALWAYS_SOFTWARE=1, GALLIUM_DRIVER=llvmpipe,
   MESA_GL_VERSION_OVERRIDE=4.5 / MESA_GLSL_VERSION_OVERRIDE=450. ALSOFT_DRIVERS=null gives OpenAL a silent
   output device, so the sound engine starts instead of logging errors.
2. Launch. `./gradlew runClient -Pwayfarers.ci=true` (ForgeGradle's client run, see build.gradle). That property
   adds `-Dwayfarers.ci=true` to the game JVM and `--width 1280 --height 720 --graphicsBackend opengl` to the
   game arguments. Minecraft's assets come from Mojang's servers on the first run. The FML early loading window
   is turned off (run/config/fml.toml) unless --early-window: one less OpenGL context to go wrong.
3. In game. With -Dwayfarers.ci=true, com.wayfarers.client.CiDriver waits for the title screen, creates a
   fresh creative world ("wayfarers-ci", normal terrain, no structures), lets it settle, then plays scripted
   steps on client ticks: HUD + minimap, world map, quest journal, talent tree, two Manual pages, a stage in the
   sky with the Auto Harvester, Guild Terminal and waystone screens (opened by right-clicking the placed
   blocks), the creative tab, creatures (Grand Clockmaker, Brass Golem, Clockwork Spider, a jellyfish in a
   water tank) with their health bars, and the Clockwork Citadel placed with /place structure and framed
   from its bounding box. Each step saves run/screenshots/ci/<name>.png with the vanilla screenshot code. An
   exception or timeout in a step is logged as an ERROR and the next step runs anyway. At the end the driver
   writes run/ci-client-report.txt (PASS/FAIL/SKIP per step, SHOT per screenshot) and quits. Its own global
   timeout (--game-timeout, default 18 min) and a watchdog thread end the game if it gets stuck.
4. Watching. This script streams Gradle's output (also saved to run/ci-client-console.log) and kills the whole
   process tree after --timeout seconds (default 25 min, Gradle setup included).
5. Verdict. The run fails on:
     * a step marked FAIL (or SKIP) in the report, a missing report or a missing screenshot;
     * in run/logs/latest.log: ERROR/FATAL lines from com.wayfarers or mentioning wayfarers, any stack trace
       going through com.wayfarers, warnings about wayfarers: resources (missing models/textures/blockstates,
       "Unable to load model", "Missing texture", "Exception loading blockstate"...), crashes ("Reported
       exception thrown", crash reports in run/crash-reports, a JVM crash);
     * a non-zero exit code of the game.
   Other ERROR lines are listed but do not fail the run (--strict makes them fail), and headless noise is
   ignored outright: OpenAL/sound devices, the narrator, telemetry, Realms, Mojang account services, GLFW and
   Mesa chatter.
6. Output. build/ci-client/ gets wayfarers-shot-<name>.png for each screenshot, the report and the scan
   summary; the workflow uploads it as an artifact and attaches the images to the previews-<branch> release.
"""
import argparse
import glob
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUN = os.path.join(ROOT, "run")
OUT = os.path.join(ROOT, "build", "ci-client")
CONSOLE = os.path.join(RUN, "ci-client-console.log")
REPORT = os.path.join(RUN, "ci-client-report.txt")
SHOTS = os.path.join(RUN, "screenshots", "ci")

# keep in step with CiDriver.buildSteps()
EXPECTED_SHOTS = [
    "hud_minimap", "world_map", "quest_journal", "talent_tree", "manual_welcome", "manual_machines",
    "machine_harvester", "guild_terminal", "waystone", "creative_tab", "creatures", "mega_structure",
]

DONE_MARK = "[wayfarers-ci] DONE"
EXIT_GRACE = 180  # seconds for the game to save and quit once the driver is done

ENTRY = re.compile(r"^\[(?P<time>[^\]]+)\] \[(?P<thread>[^\]]*?)/(?P<level>[A-Z]+)\] \[(?P<logger>[^\]]*?)/(?P<marker>[^\]]*)\]: (?P<msg>.*)$")

# headless CI noise that says nothing about the mod (never applied to an entry that mentions wayfarers)
BENIGN = re.compile("|".join((
    r"OpenAL", r"\bALC\b", r"SoundSystem", r"[Ss]ound [Ee]ngine", r"Sound Library", r"audio device",
    r"[Nn]arrator", r"Text2Speech", r"flite",
    r"[Tt]elemetry", r"[Rr]ealms", r"Yggdrasil", r"authlib", r"[Pp]rofile key", r"key ?pair", r"user properties",
    r"minecraftservices", r"sessionserver", r"[Aa]uthentication", r"access token", r"UnknownHost",
    r"Failed to fetch", r"Failed to retrieve profile", r"[Ff]riends?\b", r"[Bb]locklist", r"[Pp]resence",
    r"GLFW", r"window icon", r"[Cc]lipboard", r"[Mm]esa", r"libEGL", r"[Gg]amepad", r"[Jj]oystick",
    r"Detected unexpected shutdown",
)))
CRASH = re.compile(r"Reported exception thrown|Unreported exception thrown|Minecraft Crash Report|"
                   r"This crash report has been saved|Game crashed|Preparing crash report")
RESOURCE_TROUBLE = re.compile(r"(?i)missing|unable to|couldn't|could not|failed|exception|invalid|unknown|"
                              r"not found|no such|unbound|unreferenced")
JVM_CRASH = re.compile(r"A fatal error has been detected by the Java Runtime|hs_err_pid")


def log(msg):
    print(f"[ci-client] {msg}", flush=True)


# ------------------------------------------------------------------ launch

def ensure_display(argv):
    """Re-runs this script under xvfb-run when there is no X display."""
    if os.environ.get("DISPLAY") or os.environ.get("WAYFARERS_CI_NO_XVFB"):
        return
    xvfb = shutil.which("xvfb-run")
    if not xvfb:
        sys.exit("no $DISPLAY and no xvfb-run: install xvfb (apt-get install xvfb) or run under a display")
    os.environ["WAYFARERS_CI_NO_XVFB"] = "1"
    cmd = [xvfb, "-a", "-s", "-screen 0 1920x1080x24", sys.executable, os.path.abspath(__file__)] + argv
    log("no display: re-running under " + " ".join(cmd))
    os.execv(xvfb, cmd)


def prepare(early_window):
    os.makedirs(os.path.join(RUN, "config"), exist_ok=True)
    # no tutorial toast over the screenshots, no cloud layer between the viewpoint and the wonders
    with open(os.path.join(RUN, "options.txt"), "w") as f:
        f.write("tutorialStep:none\nrenderClouds:\"false\"\nonboardAccessibility:false\nskipMultiplayerWarning:true\n")
    fml = os.path.join(RUN, "config", "fml.toml")
    if not early_window and not os.path.exists(fml):
        # FML fills in every other key with its default (and logs a warning about it)
        with open(fml, "w") as f:
            f.write("earlyWindowControl = false\n")
    for path in [REPORT, CONSOLE, SHOTS, os.path.join(RUN, "crash-reports"), OUT]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    for world in glob.glob(os.path.join(RUN, "saves", "wayfarers-ci*")):
        shutil.rmtree(world, ignore_errors=True)
    for hs in glob.glob(os.path.join(RUN, "hs_err_pid*.log")):
        os.remove(hs)
    os.makedirs(OUT, exist_ok=True)


def game_env():
    env = dict(os.environ)
    for key, value in {
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GALLIUM_DRIVER": "llvmpipe",
        "MESA_GL_VERSION_OVERRIDE": "4.5",
        "MESA_GLSL_VERSION_OVERRIDE": "450",
        "ALSOFT_DRIVERS": "null",
    }.items():
        env.setdefault(key, value)
    return env


def kill_tree(proc):
    """Gradle forks a daemon which forks the game: kill the whole process group, then any stray game JVM."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=15)
            break
        except subprocess.TimeoutExpired:
            continue
    for pid in os.listdir("/proc") if os.path.isdir("/proc") else []:
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if b"-Dwayfarers.ci=true" in f.read():
                    os.kill(int(pid), signal.SIGKILL)
                    log(f"killed stray game process {pid}")
        except (OSError, ValueError):
            pass


def run_game(args):
    cmd = [os.path.join(ROOT, "gradlew"), "runClient", "-Pwayfarers.ci=true",
           f"-Pwayfarers.ci.timeout={args.game_timeout}", "--no-daemon", "--stacktrace", "--console=plain"]
    log("running " + " ".join(cmd))
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=ROOT, env=game_env(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace",
                            start_new_session=True)
    state = {"done_at": None, "lines": [], "killed_after_done": False}

    def reader():
        with open(CONSOLE, "w", encoding="utf-8") as out:
            for line in proc.stdout:
                line = line.rstrip("\n")
                state["lines"].append(line)
                out.write(line + "\n")
                out.flush()
                print(line, flush=True)
                if DONE_MARK in line and state["done_at"] is None:
                    state["done_at"] = time.time()

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    notes = []
    while proc.poll() is None:
        time.sleep(1)
        now = time.time()
        if now - start > args.timeout:
            notes.append(f"FAIL hard timeout: the client was still running after {args.timeout}s; killed")
            log(notes[-1])
            kill_tree(proc)
            break
        if state["done_at"] and now - state["done_at"] > EXIT_GRACE:
            notes.append(f"NOTE the game did not exit within {EXIT_GRACE}s after the driver finished; killed")
            log(notes[-1])
            state["killed_after_done"] = True
            kill_tree(proc)
            break
    t.join(timeout=30)
    code = proc.poll()
    log(f"gradle exited with {code} after {time.time() - start:.0f}s")
    return code, state, notes


# ------------------------------------------------------------------ log scan

def read_entries(path):
    """latest.log as entries: the first line plus whatever follows it (stack traces) until the next entry."""
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.rstrip("\n")
            m = ENTRY.match(raw)
            if m:
                entries.append({"level": m["level"], "logger": m["logger"], "thread": m["thread"],
                                "msg": m["msg"], "head": raw, "more": []})
            elif entries:
                entries[-1]["more"].append(raw)
    return entries


def classify(entry):
    """None (fine) or one of: crash, wayfarers, resources, other."""
    level = entry["level"]
    # the checkout path may well contain "wayfarers": take it out before looking for the mod's name
    text = (entry["head"] + "\n" + "\n".join(entry["more"])).replace(ROOT, "<root>")
    mentions_mod = "wayfarers" in text.lower()
    if CRASH.search(text) or level == "FATAL":
        if not mentions_mod and BENIGN.search(entry["head"]):
            return None
        return "crash"
    if "at com.wayfarers." in text and level in ("WARN", "ERROR"):
        return "wayfarers"
    if level == "ERROR" and (entry["logger"].startswith("com.wayfarers") or mentions_mod):
        return "wayfarers"
    if level in ("WARN", "ERROR") and "wayfarers:" in text and RESOURCE_TROUBLE.search(text):
        return "resources"
    if level == "ERROR":
        return None if BENIGN.search(text) else "other"
    return None


def scan_log(strict):
    path = os.path.join(RUN, "logs", "latest.log")
    found = {"crash": [], "wayfarers": [], "resources": [], "other": []}
    entries = read_entries(path)
    if not entries:
        return found, [f"FAIL no game log at {path}"]
    for e in entries:
        kind = classify(e)
        if kind:
            found[kind].append(e)
    failing = ["crash", "wayfarers", "resources"] + (["other"] if strict else [])
    problems = []
    for kind in failing:
        if found[kind]:
            problems.append(f"FAIL {len(found[kind])} {kind} log entries")
    return found, problems


# ------------------------------------------------------------------ verdict

def read_report():
    if not os.path.exists(REPORT):
        return None
    with open(REPORT, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f]


def collect_shots():
    saved = []
    for name in EXPECTED_SHOTS + sorted(set(os.path.splitext(os.path.basename(p))[0]
                                            for p in glob.glob(os.path.join(SHOTS, "*.png"))) - set(EXPECTED_SHOTS)):
        src = os.path.join(SHOTS, name + ".png")
        if os.path.exists(src) and os.path.getsize(src) > 0:
            shutil.copyfile(src, os.path.join(OUT, f"wayfarers-shot-{name}.png"))
            saved.append(name)
    return saved


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--timeout", type=int, default=25 * 60, help="hard limit for the whole gradle run, seconds")
    ap.add_argument("--game-timeout", type=int, default=18 * 60, help="in-game limit (CiDriver), seconds")
    ap.add_argument("--early-window", action="store_true", help="keep FML's early loading window")
    ap.add_argument("--strict", action="store_true", help="also fail on ERROR lines that do not mention the mod")
    args = ap.parse_args()
    ensure_display(sys.argv[1:])
    log(f"display {os.environ.get('DISPLAY')}")
    prepare(args.early_window)

    code, state, notes = run_game(args)
    failures = [n for n in notes if n.startswith("FAIL")]
    remarks = [n for n in notes if not n.startswith("FAIL")]

    report = read_report()
    if report is None:
        failures.append("FAIL no ci-client-report.txt: the driver never finished (see the console log)")
        report = []
    for line in report:
        if line.startswith(("FAIL", "SKIP")):
            failures.append(line)
    saved = collect_shots()
    for name in EXPECTED_SHOTS:
        if name not in saved:
            failures.append(f"FAIL screenshot {name} missing")

    found, problems = scan_log(args.strict)
    failures += problems
    crashes = glob.glob(os.path.join(RUN, "crash-reports", "*"))
    if crashes:
        failures.append(f"FAIL crash reports: {[os.path.basename(c) for c in crashes]}")
    if any(JVM_CRASH.search(l) for l in state["lines"]) or glob.glob(os.path.join(RUN, "hs_err_pid*.log")):
        failures.append("FAIL the JVM crashed (hs_err_pid log)")
    if code not in (0, None) and not state["killed_after_done"] and not any(n.startswith("FAIL hard timeout") for n in notes):
        if state["done_at"] is None:
            failures.append(f"FAIL the game exited with code {code} before the driver finished")
        else:
            failures.append(f"FAIL the game exited with code {code}")

    summary = ["# Wayfarers client test", ""]
    summary += ["## Steps", "```"] + (report or ["(no report)"]) + ["```", ""]
    summary += ["## Screenshots", ", ".join(saved) if saved else "none", ""]
    for kind in ("crash", "wayfarers", "resources", "other"):
        if found[kind]:
            summary += [f"## Log: {kind} ({len(found[kind])})", "```"]
            for e in found[kind][:40]:
                summary.append(e["head"])
                summary += e["more"][:12]
            summary += ["```", ""]
    summary += ["## Verdict", ""] + [f"- {f}" for f in failures] + [f"- {r}" for r in remarks]
    summary.append("**FAILED**" if failures else "**OK**")
    text = "\n".join(summary) + "\n"
    with open(os.path.join(OUT, "ci-client-summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    for path in (REPORT, CONSOLE):
        if os.path.exists(path):
            shutil.copyfile(path, os.path.join(OUT, os.path.basename(path)))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)

    print(text, flush=True)
    log("client test: " + ("FAILED" if failures else "OK"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

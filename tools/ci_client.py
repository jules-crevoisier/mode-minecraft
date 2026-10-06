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
2. Launch. `./gradlew runClient -Pbrasshaven.ci=true` (ForgeGradle's client run, see build.gradle). That property
   adds `-Dbrasshaven.ci=true` to the game JVM and `--width 1280 --height 720 --graphicsBackend opengl` to the
   game arguments. Minecraft's assets come from Mojang's servers on the first run. The FML early loading window
   is turned off (run/config/fml.toml) unless --early-window: one less OpenGL context to go wrong.
3. In game. With -Dbrasshaven.ci=true, com.brasshaven.client.CiDriver waits for the title screen, creates a
   fresh creative world ("brasshaven-ci", normal terrain, no structures), lets it settle, then plays scripted
   steps on client ticks: the first join (only the Manual and the Atlas, directions to a Guild Agent, the tracker
   on the progression ladder's first step, the Structure Compass earned through /brasshaven contracts complete),
   HUD + minimap, world map, quest journal, talent tree, two Manual pages, a stage in the
   sky with the Auto Harvester, Guild Terminal and waystone screens (opened by right-clicking the placed
   blocks), the multiplayer screens (company, player card, emote wheel, Pneumatic Post and Contract Board filled by
   /brasshaven social demo, a client-side preview of the trade screen), the creative tab, creatures (Grand Clockmaker, Brass Golem, Clockwork Spider, a jellyfish in a
   water tank) with their health bars, four creatures at full, hit, 40 % and 15 % health up close (health_bars:
   the coloured fill, the damage trail and number), thirteen creatures of every kind around the player on a 96 px
   minimap (minimap_radar: the entity radar), and the Clockwork Citadel placed with /place structure and framed
   from its bounding box. Each step saves run/screenshots/ci/<name>.png with the vanilla screenshot code. An
   exception or timeout in a step is logged as an ERROR and the next step runs anyway. At the end the driver
   writes run/ci-client-report.txt (PASS/FAIL/SKIP per step, SHOT per screenshot) and quits. Its own global
   timeout (--game-timeout, default 18 min) and a watchdog thread end the game if it gets stuck.
4. Watching. This script streams Gradle's output (also saved to run/ci-client-console.log) and kills the whole
   process tree after --timeout seconds (default 25 min, Gradle setup included).
5. Verdict. The run fails on:
     * a step marked FAIL (or SKIP) in the report, a missing report or a missing screenshot;
     * in run/logs/latest.log: ERROR/FATAL lines from com.brasshaven or mentioning brasshaven, any stack trace
       going through com.brasshaven, warnings about brasshaven: resources (missing models/textures/blockstates,
       "Unable to load model", "Missing texture", "Exception loading blockstate"...), crashes ("Reported
       exception thrown", crash reports in run/crash-reports, a JVM crash);
     * a non-zero exit code of the game.
   Other ERROR lines are listed but do not fail the run (--strict makes them fail), and headless noise is
   ignored outright: OpenAL/sound devices, the narrator, telemetry, Realms, Mojang account services, GLFW and
   Mesa chatter.
6. Output. build/ci-client/ gets brasshaven-shot-<name>.png for each screenshot, the report and the scan
   summary; the workflow uploads it as an artifact and attaches the images to the previews-<branch> release.

Showcase mode (--showcase, the `showcase` job): the same game, but client/CiShowcase plays a filmed tour (French
client, structures orbited by the camera, screens used with a cursor, machines, creatures, a boss, the biomes)
instead of the test. The Xvfb screen is the size of the window (--size, 1280x720) and ffmpeg's x11grab records it
from the moment the driver starts. The driver writes run/showcase/scenes.json: each scene's wall-clock begin and end
(the clock x11grab stamps its frames with), its slow-motion factor k (the game runs k times slower under /tick rate
so that software rendering still gives smooth footage) and the cursor track. Afterwards each scene is cut from the
recording and sped up by k into build/ci-client/showcase/brasshaven-showcase-<scene>.mp4 (30 fps, no sound), with
a poster frame (.jpg) and brasshaven-showcase-scenes.json (clip durations and cursor tracks in clip seconds), which
tools/make_video.py uses. The run only fails when no clip at all comes out; errors in the log are listed.
"""
import argparse
import glob
import json
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
SHOWCASE = os.path.join(RUN, "showcase")
SHOWCASE_OUT = os.path.join(OUT, "showcase")
RECORDING = os.path.join(SHOWCASE, "recording.mkv")
RECORDER_LOG = os.path.join(SHOWCASE, "ffmpeg-x11grab.log")
DRIVER_MARK = "client test driver active"

# keep in step with CiDriver.buildSteps()
EXPECTED_SHOTS = [
    "hud_minimap", "world_map", "world_map_options", "world_map_3d", "quest_journal", "talent_tree", "manual_welcome", "manual_machines",
    "machine_harvester", "guild_terminal", "waystone", "recipe_panel", "recipe_view", "recipe_uses", "recipe_fill",
    "company", "player_card", "emote_wheel", "pneumatic_post", "contract_board", "trade",
    "creative_tab", "creatures", "health_bars", "minimap_radar", "peoples", "creatures_places", "folk_trade",
    "mega_structure",
]

DONE_MARK = "[brasshaven-ci] DONE"
EXIT_GRACE = 180  # seconds for the game to save and quit once the driver is done

ENTRY = re.compile(r"^\[(?P<time>[^\]]+)\] \[(?P<thread>[^\]]*?)/(?P<level>[A-Z]+)\] \[(?P<logger>[^\]]*?)/(?P<marker>[^\]]*)\]: (?P<msg>.*)$")

# headless CI noise that says nothing about the mod (never applied to an entry that mentions brasshaven)
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

def ensure_display(argv, screen="1920x1080"):
    """Re-runs this script under xvfb-run when there is no X display."""
    if os.environ.get("DISPLAY") or os.environ.get("BRASSHAVEN_CI_NO_XVFB"):
        return
    xvfb = shutil.which("xvfb-run")
    if not xvfb:
        sys.exit("no $DISPLAY and no xvfb-run: install xvfb (apt-get install xvfb) or run under a display")
    os.environ["BRASSHAVEN_CI_NO_XVFB"] = "1"
    cmd = [xvfb, "-a", "-s", f"-screen 0 {screen}x24", sys.executable, os.path.abspath(__file__)] + argv
    log("no display: re-running under " + " ".join(cmd))
    os.execv(xvfb, cmd)


def prepare(early_window, showcase=False):
    os.makedirs(os.path.join(RUN, "config"), exist_ok=True)
    # no tutorial toast over the screenshots, no cloud layer between the viewpoint and the wonders
    with open(os.path.join(RUN, "options.txt"), "w") as f:
        f.write("tutorialStep:none\nrenderClouds:\"false\"\nonboardAccessibility:false\nskipMultiplayerWarning:true\n")
        if showcase:
            # the presentation videos are in French: the game too
            f.write("lang:fr_fr\n")
    fml = os.path.join(RUN, "config", "fml.toml")
    if not early_window and not os.path.exists(fml):
        # FML fills in every other key with its default (and logs a warning about it)
        with open(fml, "w") as f:
            f.write("earlyWindowControl = false\n")
    for path in [REPORT, CONSOLE, SHOTS, SHOWCASE, os.path.join(RUN, "crash-reports"), OUT]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    for world in glob.glob(os.path.join(RUN, "saves", "brasshaven-ci*")):
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
                if b"-Dbrasshaven.ci=true" in f.read():
                    os.kill(int(pid), signal.SIGKILL)
                    log(f"killed stray game process {pid}")
        except (OSError, ValueError):
            pass


def run_game(args):
    cmd = [os.path.join(ROOT, "gradlew"), "runClient", "-Pbrasshaven.ci=true",
           f"-Pbrasshaven.ci.timeout={args.game_timeout}", "--no-daemon", "--stacktrace", "--console=plain"]
    if args.showcase:
        cmd[3:3] = ["-Pbrasshaven.showcase=true", f"-Pbrasshaven.ci.size={args.size}",
                    f"-Pbrasshaven.showcase.slowmo={args.slowmo}"]
    log("running " + " ".join(cmd))
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=ROOT, env=game_env(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace",
                            start_new_session=True)
    state = {"done_at": None, "lines": [], "killed_after_done": False, "recorder": None}

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
                if args.showcase and DRIVER_MARK in line and state["recorder"] is None:
                    state["recorder"] = start_recorder(args.size)

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
    if state["recorder"] is not None:
        stop_recorder(state["recorder"])
    code = proc.poll()
    log(f"gradle exited with {code} after {time.time() - start:.0f}s")
    return code, state, notes


# ------------------------------------------------------------------ showcase: recording and clips

def start_recorder(size):
    """ffmpeg x11grab on the whole Xvfb screen (the game window fills it), no cursor (the composer draws one)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        log("no ffmpeg: the showcase cannot be recorded (apt-get install ffmpeg)")
        return None
    os.makedirs(SHOWCASE, exist_ok=True)
    display = os.environ.get("DISPLAY", ":0")
    source = (display if "." in display.split(":")[-1] else display + ".0") + "+0,0"
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "info", "-f", "x11grab", "-draw_mouse", "0", "-framerate", "30",
           "-video_size", size, "-i", source, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16",
           "-pix_fmt", "yuv420p", "-g", "60", RECORDING]
    log("recording: " + " ".join(cmd))
    logf = open(RECORDER_LOG, "w")
    spawned = time.time()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    return {"proc": proc, "log": logf, "spawned": spawned}


def stop_recorder(rec):
    if rec is None:
        return
    proc = rec["proc"]
    try:
        proc.stdin.write(b"q")
        proc.stdin.flush()
        proc.stdin.close()
    except OSError:
        pass
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
    rec["log"].close()
    log(f"recording stopped ({os.path.getsize(RECORDING) / 1e6:.0f} MB)" if os.path.exists(RECORDING) else "no recording")


def recording_start(fallback):
    """Wall-clock time of the recording's first frame: x11grab stamps its frames with the system clock."""
    try:
        with open(RECORDER_LOG, encoding="utf-8", errors="replace") as f:
            m = re.search(r"start: (\d{9,}\.\d+)", f.read())
        if m:
            return float(m.group(1)), "x11grab start"
    except OSError:
        pass
    return fallback, "spawn time (no start stamp in the ffmpeg log)"


def cut_clips(spawned):
    """One clip per filmed scene, sped back up to real time, plus a poster frame and the scene log for make_video.py."""
    path = os.path.join(SHOWCASE, "scenes.json")
    if not os.path.exists(path):
        return [], ["FAIL no run/showcase/scenes.json: the tour never started"]
    if not os.path.exists(RECORDING):
        return [], ["FAIL no recording"]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    start, how = recording_start(spawned + 0.3)
    log(f"recording starts at {start:.3f} ({how})")
    os.makedirs(SHOWCASE_OUT, exist_ok=True)
    out = {"window": data.get("window"), "gui_scale": data.get("gui_scale"), "language": data.get("language"),
           "measured_fps": data.get("measured_fps"), "slowmo": data.get("slowmo"), "recording_start": how, "scenes": []}
    made, notes = [], []
    for sc in data.get("scenes", []):
        name, k = sc["name"], float(sc.get("slowmo") or 1.0)
        begin, end = sc.get("begin_ms", 0) / 1000.0, sc.get("end_ms", 0) / 1000.0
        if sc.get("calibration") or end <= begin:
            continue
        clip = f"brasshaven-showcase-{name}.mp4"
        dst = os.path.join(SHOWCASE_OUT, clip)
        ss, dur = max(0.0, begin - start), end - begin
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.3f}", "-t", f"{dur:.3f}", "-i", RECORDING,
               "-vf", f"setpts=(PTS-STARTPTS)/{k},fps=30", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(dst):
            notes.append(f"NOTE clip {name} could not be cut: {r.stderr.strip()[-300:]}")
            continue
        length = dur / k
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{length / 2:.2f}", "-i", dst,
                        "-frames:v", "1", "-q:v", "3", dst[:-4] + ".jpg"], capture_output=True)
        out["scenes"].append({"name": name, "clip": clip, "duration": round(length, 3), "slowmo": k,
                              "fps": sc.get("fps"), "status": sc.get("status"), "error": sc.get("error"),
                              "cursor": sc.get("cursor", [])})
        made.append(name)
        log(f"clip {clip}: {length:.1f} s (filmed {dur:.0f} s at x{k:g}, {sc.get('fps')} fps, {sc.get('status')})")
    with open(os.path.join(SHOWCASE_OUT, "brasshaven-showcase-scenes.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    if not made:
        notes.append("FAIL no scene was filmed")
    return made, notes


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
    """None (fine) or one of: crash, brasshaven, resources, other."""
    level = entry["level"]
    # the checkout path may well contain "brasshaven": take it out before looking for the mod's name
    text = (entry["head"] + "\n" + "\n".join(entry["more"])).replace(ROOT, "<root>")
    mentions_mod = "brasshaven" in text.lower()
    if CRASH.search(text) or level == "FATAL":
        if not mentions_mod and BENIGN.search(entry["head"]):
            return None
        return "crash"
    if "at com.brasshaven." in text and level in ("WARN", "ERROR"):
        return "brasshaven"
    if level == "ERROR" and (entry["logger"].startswith("com.brasshaven") or mentions_mod):
        return "brasshaven"
    if level in ("WARN", "ERROR") and "brasshaven:" in text and RESOURCE_TROUBLE.search(text):
        return "resources"
    if level == "ERROR":
        return None if BENIGN.search(text) else "other"
    return None


def scan_log(strict):
    path = os.path.join(RUN, "logs", "latest.log")
    found = {"crash": [], "brasshaven": [], "resources": [], "other": []}
    entries = read_entries(path)
    if not entries:
        return found, [f"FAIL no game log at {path}"]
    for e in entries:
        kind = classify(e)
        if kind:
            found[kind].append(e)
    failing = ["crash", "brasshaven", "resources"] + (["other"] if strict else [])
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
            shutil.copyfile(src, os.path.join(OUT, f"brasshaven-shot-{name}.png"))
            saved.append(name)
    return saved


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--timeout", type=int, default=25 * 60, help="hard limit for the whole gradle run, seconds")
    ap.add_argument("--game-timeout", type=int, default=18 * 60, help="in-game limit (CiDriver), seconds")
    ap.add_argument("--early-window", action="store_true", help="keep FML's early loading window")
    ap.add_argument("--strict", action="store_true", help="also fail on ERROR lines that do not mention the mod")
    ap.add_argument("--showcase", action="store_true", help="film the showcase tour (client/CiShowcase) with ffmpeg")
    ap.add_argument("--size", default="1280x720", help="window and Xvfb screen size in showcase mode, WxH")
    ap.add_argument("--slowmo", default="0", help="showcase slow-motion factor (0: picked from the measured fps)")
    args = ap.parse_args()
    if args.showcase:
        if args.timeout == 25 * 60:
            args.timeout = 70 * 60
        if args.game_timeout == 18 * 60:
            args.game_timeout = 58 * 60
    ensure_display(sys.argv[1:], args.size if args.showcase else "1920x1080")
    log(f"display {os.environ.get('DISPLAY')}")
    prepare(args.early_window, args.showcase)

    code, state, notes = run_game(args)
    if args.showcase:
        return showcase_verdict(args, code, state, notes)
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

    summary = ["# Brasshaven client test", ""]
    summary += ["## Steps", "```"] + (report or ["(no report)"]) + ["```", ""]
    summary += ["## Screenshots", ", ".join(saved) if saved else "none", ""]
    for kind in ("crash", "brasshaven", "resources", "other"):
        if found[kind]:
            summary += [f"## Log: {kind} ({len(found[kind])})", "```"]
            for e in found[kind][:40]:
                summary.append(e["head"])
                summary += e["more"][:12]
            summary += ["```", ""]
    summary += crash_excerpts(crashes)
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


def crash_excerpts(paths):
    """The part of each crash report that names the cause: the description, the exception with its first frames, every
    'Caused by' and the mod frames, so the summary shows what broke without downloading the logs."""
    out = []
    for path in paths[:2]:
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        keep, frames = [], 0
        start = next((i for i, l in enumerate(lines) if l.startswith("Description:")), 0)
        keep += lines[start:start + 6]  # the description and the exception line, whatever its wording
        for i, line in enumerate(lines[start + 6:400]):
            if line.startswith("Description:") or line.startswith("Caused by") or "Exception" in line.split(":")[0]:
                keep.append(line)
                frames = 8
            elif frames and line.lstrip().startswith("at "):
                keep.append(line)
                frames -= 1
            elif "com.brasshaven" in line and line.lstrip().startswith("at "):
                keep.append(line)
            elif line.startswith("-- ") and keep:
                break
        out += [f"## Crash report {os.path.basename(path)}", "```"] + keep[:80] + ["```", ""]
    return out


def showcase_verdict(args, code, state, notes):
    """The tour is footage, not a test: only a run without any clip fails. Log problems are listed for the record."""
    rec = state.get("recorder")
    made, cut_notes = cut_clips(rec["spawned"] if rec else time.time())
    notes = notes + cut_notes
    report = read_report() or ["(no report)"]
    found, problems = scan_log(args.strict)
    summary = ["# Brasshaven showcase", "", "## Steps", "```"] + report + ["```", "",
               "## Clips", ", ".join(made) if made else "none", ""]
    for kind in ("crash", "brasshaven", "resources"):
        if found[kind]:
            summary += [f"## Log: {kind} ({len(found[kind])})", "```"]
            for e in found[kind][:30]:
                summary.append(e["head"])
                summary += e["more"][:8]
            summary += ["```", ""]
    failures = [n for n in notes if n.startswith("FAIL")]
    summary += ["## Notes", ""] + [f"- {n}" for n in notes + problems] + [f"- game exit code {code}"]
    summary.append("**FAILED**" if failures else "**OK**")
    text = "\n".join(summary) + "\n"
    os.makedirs(SHOWCASE_OUT, exist_ok=True)
    with open(os.path.join(SHOWCASE_OUT, "showcase-summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    for path in (REPORT, CONSOLE, RECORDER_LOG, os.path.join(SHOWCASE, "scenes.json")):
        if os.path.exists(path):
            shutil.copyfile(path, os.path.join(SHOWCASE_OUT, os.path.basename(path)))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text)
    print(text, flush=True)
    log("showcase: " + ("FAILED" if failures else f"OK, {len(made)} clips"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

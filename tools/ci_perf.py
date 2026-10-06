#!/usr/bin/env python3
"""Measuring a running Minecraft server from the outside, for the CI performance reports (tools/ci_smoke.py).

Everything here works the same on a Forge server with or without the Brasshaven jar (the vanilla comparison of the
world test has no mod command to ask), using only Linux /proc and the JDK's own tools:
  * java_pid: the server JVM under the run.sh process the test started;
  * cpu_snapshot / cpu_delta: CPU time per thread group (server thread, world generation workers, IO, GC, JIT,
    other) from /proc/<pid>/task/*/stat, plus the whole process from /proc/<pid>/stat (threads that ended between
    two snapshots still count there);
  * heap_after_gc: heap in use right after a full collection (jcmd GC.run, then GC.heap_info), and rss_mb;
  * jfr_start / jfr_stop: a Java Flight Recorder recording around one phase (jcmd JFR.start / JFR.stop), summarised by
    tools/jfr_report.py.
JVM flags for CI servers come from serverpack/jvm_args.txt (server_jvm_flags), so the tests run the flags the
server pack ships.
"""
import os
import re
import shutil
import subprocess
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLK_TCK = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
# server pack flags left out on CI: the heap size is the test's own, pre-touching 4 GB slows every start, and
# PerfDisableSharedMem hides the JVM from the JDK tools the reports use
CI_SKIPPED_FLAGS = ("-Xms", "-Xmx", "-XX:+AlwaysPreTouch", "-XX:+PerfDisableSharedMem")
# JFR keeps 64 frames per stack by default: world generation (density functions call each other deeply) needs more
# for the outer frames (which structure, which feature) to survive. Costs nothing while no recording runs.
JFR_FLAGS = ["-XX:FlightRecorderOptions=stackdepth=256"]


def server_jvm_flags():
    """The server pack's JVM flags (serverpack/jvm_args.txt) minus CI_SKIPPED_FLAGS."""
    path = os.path.join(ROOT, "serverpack", "jvm_args.txt")
    flags = []
    if not os.path.exists(path):
        return flags
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if any(line.startswith(s) for s in CI_SKIPPED_FLAGS):
            continue
        flags.append(line)
    return flags


def jdk_tool(name):
    home = os.environ.get("JAVA_HOME")
    if home and os.path.exists(os.path.join(home, "bin", name)):
        return os.path.join(home, "bin", name)
    found = shutil.which(name)
    if found:
        return found
    java = shutil.which("java")
    if java:
        candidate = os.path.join(os.path.dirname(os.path.realpath(java)), name)
        if os.path.exists(candidate):
            return candidate
    return None


def _children(pid):
    out = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as f:
                stat = f.read()
            ppid = int(stat[stat.rindex(")") + 2:].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        if ppid == pid:
            out.append(int(entry))
    return out


def _cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""


def java_pid(root_pid):
    """The java process at or under root_pid (run.sh starts java as a child), or None."""
    todo = [root_pid]
    seen = set()
    while todo:
        pid = todo.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        cmd = _cmdline(pid)
        if cmd.split(" ")[0].endswith("java"):
            return pid
        todo += _children(pid)
    return None


def thread_group(comm):
    if comm == "Server thread":
        return "server thread"
    if comm.startswith("Worker-Main"):
        return "worldgen workers"
    if comm.startswith("IO-Worker") or comm.startswith("Chunk") or "IO" in comm and not comm.startswith("Netty"):
        return "io"
    # the collector's threads by kind: a gap here says whether it is young collections (allocation), concurrent
    # marking (live heap size) or card refinement (old-to-young writes), or VM operations (safepoints, deopt)
    if comm.startswith("GC Thread"):
        return "gc: pause workers"
    if comm.startswith(("G1 Conc", "G1 Main Marker", "G1 Service")):
        return "gc: concurrent marking"
    if comm.startswith("G1 Refine"):
        return "gc: refinement"
    if comm.startswith("G1 "):
        return "gc: other G1"
    if comm.startswith(("ZGC", "Z ")):
        return "gc: zgc"
    if comm.startswith(("VM Thread", "VM Periodic")):
        return "vm thread"
    if "CompilerThre" in comm or comm.startswith("C1 ") or comm.startswith("C2 "):
        return "jit"
    return "other"


def cpu_snapshot(pid):
    """{'process': ms, 'threads': {tid: (group, ms)}} or None when the process is gone."""
    def ms(stat):
        fields = stat[stat.rindex(")") + 2:].split()
        return (int(fields[11]) + int(fields[12])) * 1000.0 / CLK_TCK  # utime + stime

    try:
        with open(f"/proc/{pid}/stat") as f:
            process = ms(f.read())
    except (OSError, ValueError):
        return None
    threads = {}
    try:
        tids = os.listdir(f"/proc/{pid}/task")
    except OSError:
        tids = []
    for tid in tids:
        try:
            with open(f"/proc/{pid}/task/{tid}/comm") as f:
                comm = f.read().strip()
            with open(f"/proc/{pid}/task/{tid}/stat") as f:
                threads[tid] = (thread_group(comm), ms(f.read()))
        except (OSError, ValueError):
            continue
    return {"process": process, "threads": threads}


def cpu_delta(before, after):
    """CPU milliseconds per thread group between two snapshots, plus 'process' (the whole JVM)."""
    out = Counter()
    if not before or not after:
        return out
    for tid, (group, ms) in after["threads"].items():
        prev = before["threads"].get(tid)
        out[group] += ms - (prev[1] if prev else 0.0)
    out["process"] = after["process"] - before["process"]
    return out


def jcmd(pid, *args, timeout=180):
    """jcmd's output, or None when it failed."""
    tool = jdk_tool("jcmd")
    if not tool or not pid:
        return None
    try:
        res = subprocess.run([tool, str(pid)] + list(args), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        print(f"[perf] jcmd {' '.join(args)} failed: {res.stdout[-300:]} {res.stderr[-300:]}", flush=True)
        return None
    return res.stdout


def heap_after_gc(pid):
    """MB of heap in use right after a full GC, or None."""
    if jcmd(pid, "GC.run") is None:
        return None
    info = jcmd(pid, "GC.heap_info") or ""
    m = re.search(r"used (\d+)K", info)
    return int(m.group(1)) / 1024.0 if m else None


def class_histogram(pid):
    """{class name: bytes} of the live heap (jcmd GC.class_histogram runs a full GC first), or {}."""
    out = jcmd(pid, "GC.class_histogram", timeout=300) or ""
    hist = {}
    for line in out.splitlines():
        m = re.match(r"\s*\d+:\s+(\d+)\s+(\d+)\s+(\S+)", line)
        if m:
            hist[m.group(3)] = hist.get(m.group(3), 0) + int(m.group(2))
    return hist


def histogram_diff(a, b, top=25):
    """Lines: the classes whose live bytes grew most from b to a (MB, a and b)."""
    rows = sorted(((a.get(k, 0) - b.get(k, 0), k) for k in set(a) | set(b)), reverse=True)[:top]
    return [f"    {d / 1024 ** 2:+8.1f} MB  {a.get(k, 0) / 1024 ** 2:8.1f} {b.get(k, 0) / 1024 ** 2:8.1f}  {k[:100]}"
            for d, k in rows if d > 0]


def rss_mb(pid):
    try:
        for line in open(f"/proc/{pid}/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except (OSError, ValueError, IndexError):
        pass
    return None


def jfr_start(pid, name, path, settings="profile"):
    out = jcmd(pid, "JFR.start", f"name={name}", f"settings={settings}", f"filename={os.path.abspath(path)}")
    return out is not None


def jfr_stop(pid, name):
    """Stops the recording; its file (given at start) is written now."""
    return jcmd(pid, "JFR.stop", f"name={name}", timeout=600) is not None

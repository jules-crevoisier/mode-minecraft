#!/usr/bin/env python3
"""Summarise a Java Flight Recorder file into a short text report: where the CPU goes, what allocates, GC pauses.

Used by CI (tools/ci_smoke.py records the server with JFR during the world generation benchmark and the server
performance check) and by hand:

    python3 tools/jfr_report.py recording.jfr [--title "..."] [--out report.txt] [--top 30]

It needs the JDK's `jfr` tool (next to `java`, or in $JAVA_HOME/bin) and reads the recording with
`jfr print --events <event> --stack-depth N` (streamed, so a large recording does not need much memory).

Sections:
  * CPU (jdk.ExecutionSample): samples per thread group; hottest frames by self samples (the method running) and by
    total samples (the method anywhere on the stack); self samples by package; the server thread on its own (what
    costs tick time); and com.brasshaven alone: samples with a mod frame on the stack, per thread group, mod methods
    by self and total samples, and the samples attributed to the mod frame nearest to the running method (what the
    mod's code ends up costing, Minecraft code it calls included).
  * Allocation (jdk.ObjectAllocationSample, weighted): by class, by allocating frame, and the mod's share and sites.
  * GC (jdk.GarbageCollection): collections, total and longest pause per collector.
  * CPU load (jdk.CPULoad): average JVM and machine load.
Frames are "package.Class.method(argument types)" without line numbers.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict

MOD = "com.brasshaven."
STACK_DEPTH = 256
DURATION_RX = re.compile(r"([\d.]+)\s*(ns|us|ms|s|min|h)\b")
SIZE_RX = re.compile(r"([\d.]+)\s*(bytes|byte|kB|KB|MB|GB|TB)\b")
UNITS = {"ns": 1e-6, "us": 1e-3, "ms": 1.0, "s": 1e3, "min": 60e3, "h": 3600e3}
SIZES = {"bytes": 1, "byte": 1, "kB": 1024, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4}


def jfr_tool():
    """Path of the JDK's jfr tool, or None."""
    for home in (os.environ.get("JAVA_HOME"),):
        if home and os.path.exists(os.path.join(home, "bin", "jfr")):
            return os.path.join(home, "bin", "jfr")
    found = shutil.which("jfr")
    if found:
        return found
    java = shutil.which("java")
    if java:
        candidate = os.path.join(os.path.dirname(os.path.realpath(java)), "jfr")
        if os.path.exists(candidate):
            return candidate
    return None


def millis(text):
    m = DURATION_RX.search(text or "")
    return float(m.group(1)) * UNITS[m.group(2)] if m else 0.0


def size_bytes(text):
    m = SIZE_RX.search(text or "")
    return float(m.group(1)) * SIZES[m.group(2)] if m else 0.0


def events(path, event, depth=STACK_DEPTH):
    """Yields each event of a type as a dict of its top-level fields ('stack': list of frames, leaf first)."""
    tool = jfr_tool()
    if not tool:
        raise RuntimeError("no jfr tool (JDK bin) found")
    proc = subprocess.Popen([tool, "print", "--events", event, "--stack-depth", str(depth), path],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                            errors="replace", bufsize=1 << 20)
    current = None
    in_stack = False
    for line in proc.stdout:
        if line.startswith(event + " {"):
            current = {"stack": []}
            in_stack = False
            continue
        if current is None:
            continue
        stripped = line.strip()
        if in_stack:
            if stripped == "]":
                in_stack = False
            elif stripped and stripped != "...":
                current["stack"].append(re.sub(r"\s+line:\s*\d+.*$", "", stripped))
            continue
        if line.startswith("}"):
            yield current
            current = None
            continue
        if line.startswith("  ") and not line.startswith("   ") and " = " in line:
            key, _, value = stripped.partition(" = ")
            if key == "stackTrace":
                in_stack = value.strip() == "["
            else:
                current[key] = value
    proc.wait()


def thread_name(value):
    m = re.match(r'"([^"]*)"', value or "")
    return m.group(1) if m else (value or "?")


def thread_group(name):
    if name == "Server thread":
        return "server thread"
    if name.startswith("Worker-Main"):
        return "worldgen workers (Worker-Main)"
    if name.startswith("IO-Worker") or "IO" in name and "Netty" not in name:
        return "io"
    if name.startswith("Netty"):
        return "network"
    return "other"


def package(frame, parts=5):
    method = frame.split("(")[0]
    names = method.split(".")
    cls = names[:-1]
    # keep the package (lower-case parts) and at most `parts` components
    pkg = [p for p in cls if p[:1].islower()] or cls[:1]
    return ".".join(pkg[:parts])


def pct(n, total):
    return f"{100.0 * n / total:5.1f}%" if total else "  n/a"


def table(counter, total, top, width=110):
    out = []
    for frame, n in counter.most_common(top):
        out.append(f"    {pct(n, total)} {n:8d}  {frame[:width]}")
    return out or ["    (none)"]


def cpu_section(path, top):
    total = 0
    groups = Counter()
    self_all = Counter()
    total_all = Counter()
    packages = Counter()
    server_self = Counter()
    server_total = Counter()
    server_n = 0
    mod_n = 0
    mod_groups = Counter()
    mod_self = Counter()
    mod_total = Counter()
    mod_nearest = Counter()
    mod_nearest_server = Counter()
    truncated = 0
    for ev in events(path, "jdk.ExecutionSample"):
        stack = ev["stack"]
        if not stack:
            continue
        total += 1
        name = thread_name(ev.get("sampledThread"))
        group = thread_group(name)
        groups[group] += 1
        leaf = stack[0]
        self_all[leaf] += 1
        packages[package(leaf)] += 1
        seen = set(stack)
        for f in seen:
            total_all[f] += 1
        if len(stack) >= STACK_DEPTH:
            truncated += 1
        if group == "server thread":
            server_n += 1
            server_self[leaf] += 1
            for f in seen:
                server_total[f] += 1
        mods = [f for f in stack if f.startswith(MOD)]
        if mods:
            mod_n += 1
            mod_groups[group] += 1
            if leaf.startswith(MOD):
                mod_self[leaf] += 1
            for f in set(mods):
                mod_total[f] += 1
            mod_nearest[mods[0]] += 1
            if group == "server thread":
                mod_nearest_server[mods[0]] += 1
    lines = ["", "CPU (jdk.ExecutionSample, percentages of all samples):", f"  samples: {total}"
             + (f" ({truncated} stacks deeper than {STACK_DEPTH} frames: their outermost frames are missing)" if truncated else "")]
    if not total:
        return lines + ["  no execution samples in this recording"]
    lines += ["  by thread group:"] + [f"    {pct(n, total)} {n:8d}  {g}" for g, n in groups.most_common()]
    lines += ["", f"  top {top} frames by self samples (the method running):"] + table(self_all, total, top)
    lines += ["", f"  top {top} frames by total samples (anywhere on the stack):"] + table(total_all, total, top)
    lines += ["", "  self samples by package:"] + table(packages, total, 20)
    lines += ["", f"  server thread ({server_n} samples, {pct(server_n, total).strip()} of all; this is tick time):",
              f"    top {top} self:"] + table(server_self, total, top)
    lines += [f"    top {top} total:"] + table(server_total, total, top)
    lines += ["", f"  com.brasshaven: {mod_n} samples with a mod frame on the stack ({pct(mod_n, total).strip()} of all samples)"]
    lines += [f"    {pct(n, total)} {n:8d}  {g}" + (f"  ({pct(n, groups[g]).strip()} of that group)" if groups[g] else "")
              for g, n in mod_groups.most_common()]
    lines += ["", f"  com.brasshaven self (mod code itself running, top {top}):"] + table(mod_self, total, top)
    lines += ["", f"  com.brasshaven total (mod method anywhere on the stack, top {top}):"] + table(mod_total, total, top)
    lines += ["", f"  samples attributed to the mod frame nearest the running method (mod code + what it calls, top {top}):"] \
        + table(mod_nearest, total, top)
    lines += ["", "  same, server thread only:"] + table(mod_nearest_server, total, top)
    return lines


def alloc_section(path, top):
    total = 0.0
    by_class = Counter()
    by_site = Counter()
    by_group = Counter()
    mod_total = 0.0
    mod_sites = Counter()
    mod_classes = Counter()
    for ev in events(path, "jdk.ObjectAllocationSample", 64):
        w = size_bytes(ev.get("weight"))
        total += w
        cls = re.sub(r"\s*\(classLoader.*$", "", ev.get("objectClass", "?"))
        by_class[cls] += w
        stack = ev["stack"]
        site = stack[0] if stack else "?"
        by_site[site] += w
        by_group[thread_group(thread_name(ev.get("eventThread")))] += w
        mods = [f for f in stack if f.startswith(MOD)]
        if mods:
            mod_total += w
            mod_sites[mods[0]] += w
            mod_classes[cls] += w

    def mb_table(counter, n):
        return [f"    {pct(v, total)} {v / 1024 ** 2:10.1f} MB  {k[:110]}" for k, v in counter.most_common(n)] or ["    (none)"]

    lines = ["", "Allocation (jdk.ObjectAllocationSample, sampled weights: an estimate of the bytes allocated):",
             f"  total {total / 1024 ** 2:.1f} MB"]
    if not total:
        return lines
    lines += ["  by thread group:"] + mb_table(by_group, 10)
    lines += ["", f"  top {top} classes:"] + mb_table(by_class, top)
    lines += ["", f"  top {top} allocating frames:"] + mb_table(by_site, top)
    lines += ["", f"  com.brasshaven on the stack: {mod_total / 1024 ** 2:.1f} MB ({pct(mod_total, total).strip()})",
              f"  by the mod frame nearest the allocation (top {top}):"] + mb_table(mod_sites, top)
    lines += ["  classes allocated under mod code:"] + mb_table(mod_classes, 15)
    return lines


def gc_section(path):
    per = defaultdict(lambda: [0, 0.0, 0.0])
    for ev in events(path, "jdk.GarbageCollection", 1):
        name = (ev.get("name") or "?").strip('"')
        p = per[name]
        p[0] += 1
        p[1] += millis(ev.get("sumOfPauses"))
        p[2] = max(p[2], millis(ev.get("longestPause")))
    lines = ["", "GC (jdk.GarbageCollection):"]
    if not per:
        return lines + ["  no collection in this recording"]
    for name, (n, total, longest) in sorted(per.items(), key=lambda kv: -kv[1][1]):
        lines.append(f"  {name:28s} {n:6d} collections, pauses {total:9.1f} ms in total, longest {longest:7.1f} ms")
    return lines


def load_section(path):
    jvm = []
    machine = []
    for ev in events(path, "jdk.CPULoad", 1):
        try:
            jvm.append(float(ev.get("jvmUser", "0%").rstrip("%")) + float(ev.get("jvmSystem", "0%").rstrip("%")))
            machine.append(float(ev.get("machineTotal", "0%").rstrip("%")))
        except ValueError:
            continue
    if not jvm:
        return []
    return ["", f"CPU load (jdk.CPULoad, {len(jvm)} readings): JVM {sum(jvm) / len(jvm):.1f}% on average "
                f"(peak {max(jvm):.1f}%), machine {sum(machine) / len(machine):.1f}%"]


def report(path, title=None, top=30):
    """The report's lines (raises RuntimeError when the jfr tool is missing)."""
    size = os.path.getsize(path) / 1024 ** 2 if os.path.exists(path) else 0
    lines = [title or f"JFR report: {os.path.basename(path)}", f"recording: {os.path.basename(path)} ({size:.1f} MB)"]
    lines += cpu_section(path, top)
    lines += alloc_section(path, min(top, 25))
    lines += gc_section(path)
    lines += load_section(path)
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jfr")
    ap.add_argument("--title")
    ap.add_argument("--out")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()
    lines = report(args.jfr, args.title, args.top)
    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

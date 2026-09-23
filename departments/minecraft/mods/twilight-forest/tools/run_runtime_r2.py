#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import queue
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


ARRIVAL_MARKER = "KNEEKURA_R2_ARRIVED"
FIXTURE_MARKER = "KNEEKURA_R2_FIXTURE_READY"
DEBUG_MARKER = "KNEEKURA_R2_DEBUG_READY"
TWILIGHT_DIMENSION = "twilightforest:twilight_forest"


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def capture(cmd, cwd=None):
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {"command": cmd, "exit_code": p.returncode, "output": p.stdout.strip()}


def git_head(repo):
    result = capture(["git", "rev-parse", "HEAD"], repo)
    if result["exit_code"] != 0:
        raise RuntimeError("git rev-parse failed: " + result["output"])
    return result["output"].splitlines()[-1].strip()


def total_ram_bytes():
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        s = MEMORYSTATUSEX()
        s.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):
            return int(s.ullTotalPhys)
    except Exception:
        pass
    return None


def gradle_jvmargs(repo):
    props = repo / "gradle.properties"
    if not props.exists():
        return None
    for line in props.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("org.gradle.jvmargs="):
            return line.split("=", 1)[1].strip()
    return None


def gpu_record():
    result = capture([
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | ConvertTo-Json -Compress",
    ])
    if result["exit_code"] != 0 or not result["output"]:
        return {"applicable": False, "reason": "not required for dedicated-server R2", "query": result}
    try:
        devices = json.loads(result["output"])
    except json.JSONDecodeError:
        devices = result["output"]
    return {
        "applicable": False,
        "reason": "captured for machine identity; not used by dedicated-server R2",
        "devices": devices,
    }


def build_gradle_command(repo, gradle_task):
    return [
        "cmd.exe", "/d", "/s", "/c", str(repo / "gradlew.bat"),
        gradle_task, "--no-daemon", "--console=plain",
    ]


def build_portal_fixture_commands():
    return [
        "gamerule doMobSpawning false",
        "difficulty peaceful",
        "time set day",
        "weather clear",
        "fill -1 159 -1 2 159 2 minecraft:dirt",
        "fill -1 160 -1 2 160 2 minecraft:dirt",
        "fill -1 161 -1 2 161 2 minecraft:fern",
        "fill 0 161 0 1 161 1 minecraft:air",
        "fill 0 160 0 1 160 1 twilightforest:twilight_portal",
        f"say {FIXTURE_MARKER}",
    ]


def summon_probe_command():
    return (
        'summon minecraft:pig 0.5 160.1 0.5 '
        '{NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,Tags:["kneekura_r2_probe"]}'
    )


def arrival_poll_command():
    return (
        f"execute in {TWILIGHT_DIMENSION} "
        f"if entity @e[tag=kneekura_r2_probe,limit=1] run say {ARRIVAL_MARKER}"
    )


def position_query_command():
    return (
        f"execute in {TWILIGHT_DIMENSION} "
        "run data get entity @e[tag=kneekura_r2_probe,limit=1] Pos"
    )


def kill_tree(proc):
    if proc.poll() is not None:
        return "already_exited"
    subprocess.run(
        ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return "forced_taskkill_tree"


def reader(stream, q):
    try:
        for line in iter(stream.readline, ""):
            q.put(line)
    finally:
        q.put(None)


def send_command(proc, command):
    proc.stdin.write(command + "\n")
    proc.stdin.flush()


def parse_keepup_warning(line):
    m = re.search(
        r"Can't keep up!.*?Running\s+([0-9.]+)ms.*?([0-9]+)\s+ticks behind",
        line,
        re.I,
    )
    if not m:
        return None
    return {"delay_ms": float(m.group(1)), "ticks_behind": int(m.group(2))}


def parse_position(line):
    m = re.search(
        r"\[\s*(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*,\s*"
        r"(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*,\s*"
        r"(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*\]",
        line,
    )
    if not m:
        return None
    return [float(m.group(1)), float(m.group(2)), float(m.group(3))]


def parse_debug_summary(line):
    m = re.search(
        r"(?:Stopped (?:the )?debug profiler after|Stopped profiling after)\s+"
        r"([0-9.]+)\s+seconds?.*?([0-9]+)\s+ticks?.*?\(([0-9.]+)\s+ticks per second\)",
        line,
        re.I,
    )
    if not m:
        return None
    return {
        "duration_seconds": float(m.group(1)),
        "ticks": int(m.group(2)),
        "ticks_per_second": float(m.group(3)),
    }


def region_chunk_coordinates(region_path):
    m = re.fullmatch(r"r\.(-?\d+)\.(-?\d+)\.mca", region_path.name)
    if not m:
        return []
    rx, rz = int(m.group(1)), int(m.group(2))
    data = region_path.read_bytes()[:4096]
    if len(data) < 4096:
        return []
    out = []
    for index in range(1024):
        entry = data[index * 4:(index + 1) * 4]
        offset = int.from_bytes(entry[:3], "big")
        sectors = entry[3]
        if offset == 0 or sectors == 0:
            continue
        lx = index % 32
        lz = index // 32
        out.append([rx * 32 + lx, rz * 32 + lz])
    return out


def inspect_twilight_regions(world_dir):
    region_dirs = []
    if world_dir.exists():
        for p in world_dir.rglob("region"):
            if not p.is_dir():
                continue
            low = p.as_posix().lower()
            if "twilightforest" in low and "twilight_forest" in low:
                region_dirs.append(p)
    chunks = set()
    files = []
    for region_dir in sorted(region_dirs):
        for region in sorted(region_dir.glob("r.*.*.mca")):
            coords = region_chunk_coordinates(region)
            chunks.update((x, z) for x, z in coords)
            files.append({
                "path": region.relative_to(world_dir).as_posix(),
                "sha256": sha256(region),
                "chunk_count": len(coords),
            })
    ordered = sorted(chunks)
    return {
        "region_dirs": [p.relative_to(world_dir).as_posix() for p in region_dirs],
        "region_files": files,
        "saved_chunk_count": len(ordered),
        "saved_chunks": [[x, z] for x, z in ordered],
    }


def copy_profiler_files(run_dir, profiler_dir):
    copied = []
    debug_dir = run_dir / "debug"
    if not debug_dir.exists():
        return copied
    for source in debug_dir.rglob("*"):
        if not source.is_file():
            continue
        rel = source.relative_to(debug_dir)
        target = profiler_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["anchor", "frontier"], required=True)
    ap.add_argument("--repo-dir", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--minecraft-version", required=True)
    ap.add_argument("--loader-name", required=True)
    ap.add_argument("--loader-version", required=True)
    ap.add_argument("--gradle-task", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--startup-timeout-seconds", type=int, default=2400)
    ap.add_argument("--entry-timeout-seconds", type=int, default=1800)
    ap.add_argument("--shutdown-seconds", type=int, default=90)
    ap.add_argument("--world-seed", default="20260923")
    ap.add_argument("--view-distance", type=int, default=10)
    ap.add_argument("--simulation-distance", type=int, default=10)
    args = ap.parse_args()

    repo = args.repo_dir.resolve()
    out = args.output_dir.resolve()
    logs = out / "logs"
    profiler = out / "profiler"
    logs.mkdir(parents=True, exist_ok=True)
    profiler.mkdir(parents=True, exist_ok=True)

    actual = git_head(repo)
    if actual.lower() != args.source_commit.lower():
        raise RuntimeError(f"source mismatch: expected {args.source_commit}, got {actual}")

    run_dir = repo / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    level_name = f"kneekura-r2-{args.track}"
    world_dir = run_dir / level_name
    if world_dir.exists():
        shutil.rmtree(world_dir)

    (run_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (run_dir / "server.properties").write_text(
        "\n".join([
            f"level-name={level_name}",
            f"level-seed={args.world_seed}",
            f"view-distance={args.view_distance}",
            f"simulation-distance={args.simulation_distance}",
            "online-mode=false",
            "enable-query=false",
            "enable-rcon=false",
            "spawn-protection=0",
            "difficulty=peaceful",
            "motd=Twilight Forest Runtime Evidence R2",
            "",
        ]),
        encoding="utf-8",
    )

    java = capture(["java", "-version"])
    environment = {
        "record_version": "1.0",
        "captured_at_utc": utc_now(),
        "scenario": "R2-first-twilight-entry",
        "track": args.track,
        "source": {
            "repository": "TeamTwilight/twilightforest",
            "expected_commit": args.source_commit,
            "actual_commit": actual,
        },
        "minecraft_version": args.minecraft_version,
        "loader": {"name": args.loader_name, "version": args.loader_version},
        "java": {"java_home": os.environ.get("JAVA_HOME"), "version": java},
        "jvm": {"gradle_jvmargs": gradle_jvmargs(repo)},
        "machine": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "cpu": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER"),
            "logical_cpu_count": os.cpu_count(),
            "ram_bytes": total_ram_bytes(),
            "gpu": gpu_record(),
        },
        "world": {
            "seed": args.world_seed,
            "level_name": level_name,
            "server_view_distance": args.view_distance,
            "simulation_distance": args.simulation_distance,
            "fresh_world_required": True,
        },
        "profiler": {
            "tool": "vanilla debug command when available",
            "allocation_profiler": None,
            "allocation_note": "R2 does not claim allocation bytes without an unambiguous allocation profiler.",
        },
    }
    scenario = {
        "record_version": "1.0",
        "scenario_id": "R2",
        "name": "first_twilight_dimension_entry",
        "mode": "headless dedicated-server portal fixture",
        "track": args.track,
        "startup_timeout_seconds": args.startup_timeout_seconds,
        "entry_timeout_seconds": args.entry_timeout_seconds,
        "shutdown_seconds": args.shutdown_seconds,
        "world_seed": args.world_seed,
        "source_portal_origin": [0, 160, 0],
        "source_portal_size": [2, 1, 2],
        "probe_entity": "minecraft:pig",
        "probe_entity_tag": "kneekura_r2_probe",
        "destination_dimension": TWILIGHT_DIMENSION,
        "fixture_commands": build_portal_fixture_commands(),
        "boundary": "R2 only; R3-R9 and overall performance comparisons are not measured.",
    }
    (out / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
    (out / "scenario.json").write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")

    command = build_gradle_command(repo, args.gradle_task)
    ready_re = re.compile(r'Done \([0-9.]+s\)!.*(?:help|For help)', re.I)
    prepare_start_re = re.compile(r"Did not find existing portal, making a new one", re.I)
    portal_ready_re = re.compile(
        r"Found (?:ideal|okay|fallback) portal spot|just making a (?:fallback|random) one",
        re.I,
    )

    start_wall = utc_now()
    process_start = time.perf_counter()
    proc = subprocess.Popen(
        command,
        cwd=str(repo),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    q = queue.Queue()
    threading.Thread(target=reader, args=(proc.stdout, q), daemon=True).start()

    startup_ready_elapsed = None
    fixture_ready_elapsed = None
    debug_ready_elapsed = None
    trigger_perf = None
    arrival_elapsed = None
    destination_prepare_start = None
    destination_portal_ready = None
    arrival_position = None
    arrival_position_raw = None
    debug_summary = None
    keepup_warnings = []
    structure_markers = []
    position_query_sent_at = None
    entry_timed_out = False
    startup_timed_out = False
    stop_sent = False
    shutdown = "process_exit"
    output_closed = False
    last_poll = 0.0
    arrival_actions_at = None
    log_path = logs / "console.log"

    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        while True:
            now = time.perf_counter()
            elapsed = now - process_start

            if startup_ready_elapsed is None and elapsed > args.startup_timeout_seconds:
                startup_timed_out = True
                shutdown = kill_tree(proc)
                break
            if trigger_perf is not None and arrival_elapsed is None and now - trigger_perf > args.entry_timeout_seconds:
                entry_timed_out = True
                shutdown = kill_tree(proc)
                break

            if trigger_perf is not None and arrival_elapsed is None and now - last_poll >= 0.5:
                try:
                    send_command(proc, arrival_poll_command())
                    last_poll = now
                except Exception:
                    shutdown = "arrival_poll_pipe_failed"
                    kill_tree(proc)
                    break

            if arrival_actions_at is not None and not stop_sent and now - arrival_actions_at >= 5.0:
                try:
                    send_command(proc, "stop")
                    stop_sent = True
                    shutdown = "graceful_stop_command"
                except Exception:
                    shutdown = "arrival_but_stop_pipe_failed"
                    kill_tree(proc)
                    break

            try:
                line = q.get(timeout=0.25)
            except queue.Empty:
                line = ""

            if line is None:
                output_closed = True
            elif line:
                log.write(f"[+{elapsed:.3f}s] {line}")
                log.flush()

                if startup_ready_elapsed is None and ready_re.search(line):
                    startup_ready_elapsed = elapsed
                    for cmd in build_portal_fixture_commands():
                        send_command(proc, cmd)

                if startup_ready_elapsed is not None and fixture_ready_elapsed is None and FIXTURE_MARKER in line:
                    fixture_ready_elapsed = elapsed
                    send_command(proc, "debug start")
                    send_command(proc, f"say {DEBUG_MARKER}")

                if fixture_ready_elapsed is not None and debug_ready_elapsed is None and DEBUG_MARKER in line:
                    debug_ready_elapsed = elapsed
                    trigger_perf = time.perf_counter()
                    last_poll = trigger_perf
                    send_command(proc, summon_probe_command())

                if trigger_perf is not None:
                    trigger_elapsed = now - trigger_perf
                    if destination_prepare_start is None and prepare_start_re.search(line):
                        destination_prepare_start = trigger_elapsed
                    if destination_portal_ready is None and portal_ready_re.search(line):
                        destination_portal_ready = trigger_elapsed

                    warning = parse_keepup_warning(line)
                    if warning:
                        warning["elapsed_seconds"] = trigger_elapsed
                        keepup_warnings.append(warning)

                    if len(structure_markers) < 100 and re.search(r"(twilightforest.*(?:structure|landmark)|(?:structure|landmark).*twilightforest)", line, re.I):
                        structure_markers.append({
                            "elapsed_seconds": round(trigger_elapsed, 6),
                            "line": line.strip()[:1000],
                        })

                if trigger_perf is not None and arrival_elapsed is None and ARRIVAL_MARKER in line:
                    arrival_elapsed = now - trigger_perf
                    send_command(proc, position_query_command())
                    position_query_sent_at = now
                    send_command(proc, "debug stop")
                    send_command(proc, "save-all flush")
                    send_command(
                        proc,
                        f"execute in {TWILIGHT_DIMENSION} run kill @e[tag=kneekura_r2_probe]",
                    )
                    arrival_actions_at = now

                if position_query_sent_at is not None and arrival_position is None and now - position_query_sent_at < 10:
                    pos = parse_position(line)
                    if pos is not None:
                        arrival_position = pos
                        arrival_position_raw = line.strip()[:1000]

                if debug_summary is None:
                    parsed = parse_debug_summary(line)
                    if parsed:
                        debug_summary = parsed

            if proc.poll() is not None and output_closed:
                break
            if stop_sent and proc.poll() is None and arrival_actions_at is not None:
                if now - arrival_actions_at > args.shutdown_seconds:
                    shutdown = kill_tree(proc)
                    break

    try:
        exit_code = proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        shutdown = kill_tree(proc)
        exit_code = proc.wait(timeout=5)

    total = time.perf_counter() - process_start
    profiler_files = copy_profiler_files(run_dir, profiler)
    world_inspection = inspect_twilight_regions(world_dir)
    world_inspection_path = out / "world-inspection.json"
    world_inspection_path.write_text(json.dumps(world_inspection, indent=2) + "\n", encoding="utf-8")

    max_warning = None
    if keepup_warnings:
        max_warning = max(keepup_warnings, key=lambda x: x["delay_ms"])

    success = arrival_elapsed is not None and not entry_timed_out and not startup_timed_out
    destination_prepare_elapsed = None
    if destination_prepare_start is not None and destination_portal_ready is not None:
        destination_prepare_elapsed = max(0.0, destination_portal_ready - destination_prepare_start)

    metrics = {
        "record_version": "1.0",
        "scenario_id": "R2",
        "track": args.track,
        "process_start_utc": start_wall,
        "startup_ready_elapsed_seconds": round(startup_ready_elapsed, 6) if startup_ready_elapsed is not None else None,
        "fixture_ready_elapsed_seconds": round(fixture_ready_elapsed, 6) if fixture_ready_elapsed is not None else None,
        "entry_success": success,
        "entry_command_elapsed_seconds": round(arrival_elapsed, 6) if arrival_elapsed is not None else None,
        "destination_prepare_start_elapsed_seconds": round(destination_prepare_start, 6) if destination_prepare_start is not None else None,
        "destination_portal_ready_elapsed_seconds": round(destination_portal_ready, 6) if destination_portal_ready is not None else None,
        "destination_prepare_elapsed_seconds": round(destination_prepare_elapsed, 6) if destination_prepare_elapsed is not None else None,
        "arrival_position": arrival_position,
        "arrival_position_raw": arrival_position_raw,
        "generated_twilight_chunk_count": world_inspection["saved_chunk_count"],
        "generated_twilight_chunks_sample": world_inspection["saved_chunks"][:64],
        "debug_profiler": debug_summary,
        "tick_spike_warning_count": len(keepup_warnings),
        "max_tick_spike_warning": max_warning,
        "structure_log_marker_count": len(structure_markers),
        "structure_log_markers": structure_markers,
        "allocation_bytes": None,
        "allocation_note": "not measured; no unambiguous allocation profiler is enabled in R2",
        "startup_timed_out": startup_timed_out,
        "entry_timed_out": entry_timed_out,
        "process_exit_code": exit_code,
        "stop_command_sent": stop_sent,
        "shutdown_method": shutdown,
        "total_probe_elapsed_seconds": round(total, 6),
        "limitations": [
            "R2 is one deterministic first-entry fixture, not a general performance comparison.",
            "First destination preparation includes chunk loading/search/portal placement and is not a pure per-chunk timing distribution.",
            "Absence of a Can't keep up warning does not prove absence of all tick spikes.",
            "Structure activity is promoted only when source-emitted logs are unambiguous.",
        ],
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    summary = "\n".join([
        f"# Twilight Forest Runtime Evidence — R2 {args.track}",
        "",
        f"- source commit: {actual}",
        f"- first Twilight entry observed: **{'yes' if success else 'no'}**",
        f"- trigger → Twilight arrival: **{f'{arrival_elapsed:.3f} s' if arrival_elapsed is not None else 'not observed'}**",
        f"- saved Twilight chunks after entry: **{world_inspection['saved_chunk_count']}**",
        f"- tick-spike warnings: **{len(keepup_warnings)}**",
        f"- process exit code: {exit_code}",
        f"- shutdown: {shutdown}",
        f"- raw console SHA-256: {sha256(log_path)}",
        "",
        "R2 measures one deterministic headless first-entry fixture only. It does not establish R3-R9 results or an overall ANCHOR-vs-FRONTIER performance ranking.",
        "",
    ])
    (out / "evidence-summary.md").write_text(summary, encoding="utf-8")

    manifest = {
        "record_version": "1.0",
        "scenario_id": "R2",
        "track": args.track,
        "raw_artifacts": {
            "logs/console.log": {"sha256": sha256(log_path), "committed": False},
            "world-inspection.json": {"sha256": sha256(world_inspection_path), "committed": False},
        },
        "compact_files": {},
    }
    for p in profiler_files:
        manifest["raw_artifacts"][f"profiler/{p.relative_to(profiler).as_posix()}"] = {
            "sha256": sha256(p),
            "committed": False,
        }
    for name in ["environment.json", "scenario.json", "metrics.json", "evidence-summary.md"]:
        manifest["compact_files"][name] = {"sha256": sha256(out / name), "committed": True}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if success else 2)


if __name__ == "__main__":
    main()
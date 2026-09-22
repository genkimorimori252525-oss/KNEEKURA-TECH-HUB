#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import queue
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


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
        return {"applicable": False, "reason": "not required for dedicated-server R1", "query": result}
    try:
        devices = json.loads(result["output"])
    except json.JSONDecodeError:
        devices = result["output"]
    return {
        "applicable": False,
        "reason": "captured for machine identity; not used by dedicated-server R1",
        "devices": devices,
    }


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["anchor", "frontier"], required=True)
    ap.add_argument("--repo-dir", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--minecraft-version", required=True)
    ap.add_argument("--loader-name", required=True)
    ap.add_argument("--loader-version", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout-seconds", type=int, default=2400)
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
    (run_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    (run_dir / "server.properties").write_text(
        "\n".join([
            f"level-seed={args.world_seed}",
            f"view-distance={args.view_distance}",
            f"simulation-distance={args.simulation_distance}",
            "online-mode=false",
            "enable-query=false",
            "enable-rcon=false",
            "motd=Twilight Forest Runtime Evidence R1",
            "",
        ]),
        encoding="utf-8",
    )

    java = capture(["java", "-version"])
    jvmargs = gradle_jvmargs(repo)
    environment = {
        "record_version": "1.0",
        "captured_at_utc": utc_now(),
        "scenario": "R1-startup",
        "track": args.track,
        "source": {
            "repository": "TeamTwilight/twilightforest",
            "expected_commit": args.source_commit,
            "actual_commit": actual,
        },
        "minecraft_version": args.minecraft_version,
        "loader": {"name": args.loader_name, "version": args.loader_version},
        "java": {"java_home": os.environ.get("JAVA_HOME"), "version": java},
        "jvm": {"gradle_jvmargs": jvmargs},
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
            "render_distance": None,
            "render_distance_note": "not applicable to dedicated-server R1",
            "server_view_distance": args.view_distance,
            "simulation_distance": args.simulation_distance,
        },
        "installed_mods": {
            "mode": "development run configuration from pinned source",
            "note": "Raw startup logs are retained as workflow artifact; exact loaded-mod list is not promoted unless emitted unambiguously by the loader.",
        },
        "profiler": {"tool": "none", "reason": "R1 startup baseline"},
    }
    scenario = {
        "record_version": "1.0",
        "scenario_id": "R1",
        "name": "startup",
        "mode": "dedicated-server development run",
        "track": args.track,
        "timeout_seconds": args.timeout_seconds,
        "shutdown_seconds": args.shutdown_seconds,
        "world_seed": args.world_seed,
        "server_view_distance": args.view_distance,
        "simulation_distance": args.simulation_distance,
    }
    (out / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
    (out / "scenario.json").write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")

    command = [
        "cmd.exe", "/d", "/s", "/c", str(repo / "gradlew.bat"),
        "runServer", "--no-daemon", "--console=plain",
    ]
    ready_re = re.compile(r'Done \([0-9.]+s\)!.*(?:help|For help)', re.I)
    construct_re = re.compile(r'\bCONSTRUCT\b|constructing mod|mod construction', re.I)
    load_re = re.compile(r'Preparing level|Loaded \d+ advancements|loading complete|server started', re.I)

    start_wall = utc_now()
    start = time.perf_counter()
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

    ready = None
    construct = None
    load = None
    timed_out = False
    stop_sent = False
    shutdown = "process_exit"
    output_closed = False
    log_path = logs / "console.log"

    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        while True:
            elapsed = time.perf_counter() - start
            if ready is None and elapsed > args.timeout_seconds:
                timed_out = True
                shutdown = kill_tree(proc)
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
                if construct is None and construct_re.search(line):
                    construct = elapsed
                if load is None and load_re.search(line):
                    load = elapsed
                if ready is None and ready_re.search(line):
                    ready = elapsed
                    try:
                        proc.stdin.write("stop\n")
                        proc.stdin.flush()
                        stop_sent = True
                        shutdown = "graceful_stop_command"
                    except Exception:
                        shutdown = "ready_but_stop_pipe_failed"
            if proc.poll() is not None and output_closed:
                break
            if ready is not None and stop_sent and elapsed - ready > args.shutdown_seconds and proc.poll() is None:
                shutdown = kill_tree(proc)
                break

    try:
        exit_code = proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        shutdown = kill_tree(proc)
        exit_code = proc.wait(timeout=5)

    total = time.perf_counter() - start
    success = ready is not None and not timed_out
    metrics = {
        "record_version": "1.0",
        "scenario_id": "R1",
        "track": args.track,
        "process_start_utc": start_wall,
        "startup_success": success,
        "startup_ready_elapsed_seconds": round(ready, 6) if ready is not None else None,
        "mod_construction_marker_elapsed_seconds": round(construct, 6) if construct is not None else None,
        "load_marker_elapsed_seconds": round(load, 6) if load is not None else None,
        "total_probe_elapsed_seconds": round(total, 6),
        "timed_out": timed_out,
        "process_exit_code": exit_code,
        "stop_command_sent": stop_sent,
        "shutdown_method": shutdown,
        "class_transformation_time": None,
        "class_transformation_note": "not separately observable in R1 probe",
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    log_hash = sha256(log_path)
    summary = "\n".join([
        f"# Twilight Forest Runtime Evidence — R1 {args.track}",
        "",
        f"- source commit: \`{actual}\`",
        f"- startup ready observed: **{'yes' if success else 'no'}**",
        f"- process → dedicated-server ready: **{f'{ready:.3f} s' if ready is not None else 'not observed'}**",
        f"- total probe elapsed: **{total:.3f} s**",
        f"- process exit code: \`{exit_code}\`",
        f"- shutdown: \`{shutdown}\`",
        f"- raw console SHA-256: \`{log_hash}\`",
        "",
        "This result is R1 dedicated-server startup evidence only. R2–R9, client rendering, boss tick cost, networking throughput, and any overall performance score are not measured here.",
        "",
    ])
    (out / "evidence-summary.md").write_text(summary, encoding="utf-8")
    manifest = {
        "record_version": "1.0",
        "scenario_id": "R1",
        "track": args.track,
        "raw_artifacts": {"logs/console.log": {"sha256": log_hash, "committed": False}},
        "compact_files": {},
    }
    for name in ["environment.json", "scenario.json", "metrics.json", "evidence-summary.md"]:
        manifest["compact_files"][name] = {"sha256": sha256(out / name), "committed": True}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if success else 2)


if __name__ == "__main__":
    main()

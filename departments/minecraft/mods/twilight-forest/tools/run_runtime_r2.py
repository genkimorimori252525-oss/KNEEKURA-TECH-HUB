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
import socket
import struct
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


TWILIGHT_DIMENSION = "twilightforest:twilight_forest"
RCON_PASSWORD = "kneekura-r2-local"
RCON_DEFAULT_PORT = 25575


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
        "forceload add 7 7 10 10",
        "difficulty peaceful",
        "time set day",
        "weather clear",
        "fill 7 159 7 10 159 10 minecraft:dirt",
        "fill 7 160 7 10 160 10 minecraft:dirt",
        "fill 7 161 7 10 161 10 minecraft:fern",
        "fill 8 161 8 9 161 9 minecraft:air",
        "fill 8 160 8 9 160 9 twilightforest:twilight_portal",
    ]


def fixture_verify_command():
    return (
        "execute if block 8 160 8 twilightforest:twilight_portal "
        "if block 9 160 9 twilightforest:twilight_portal run seed"
    )


def summon_probe_command():
    return (
        'summon minecraft:pig 8.5 160.1 8.5 '
        '{NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,Tags:["kneekura_r2_probe"]}'
    )


def arrival_poll_command():
    return (
        f"execute in {TWILIGHT_DIMENSION} "
        "if entity @e[tag=kneekura_r2_probe,limit=1] "
        "run data get entity @e[tag=kneekura_r2_probe,limit=1] Pos"
    )


def origin_poll_command():
    return (
        "execute in minecraft:overworld "
        "if entity @e[tag=kneekura_r2_probe,limit=1] "
        "run data get entity @e[tag=kneekura_r2_probe,limit=1] Pos"
    )


def kill_probe_command():
    return f"execute in {TWILIGHT_DIMENSION} run kill @e[tag=kneekura_r2_probe]"


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


def parse_keepup_warning(line):
    m = re.search(
        r"Can't keep up!.*?Running\s+([0-9.]+)ms.*?([0-9]+)\s+ticks behind",
        line,
        re.I,
    )
    if not m:
        return None
    return {"delay_ms": float(m.group(1)), "ticks_behind": int(m.group(2))}


def parse_position(text):
    m = re.search(
        r"\[\s*(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*,\s*"
        r"(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*,\s*"
        r"(-?[0-9]+(?:\.[0-9]+)?)[dDfF]?\s*\]",
        text,
    )
    if not m:
        return None
    return [float(m.group(1)), float(m.group(2)), float(m.group(3))]


def parse_debug_summary(text):
    m = re.search(
        r"(?:Stopped (?:the )?debug profiler after|Stopped profiling after)\s+"
        r"([0-9.]+)\s+seconds?.*?([0-9]+)\s+ticks?.*?\(([0-9.]+)\s+ticks per second\)",
        text,
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
    all_regions = []
    if world_dir.exists():
        for p in sorted(world_dir.rglob("region")):
            if not p.is_dir():
                continue
            rel = p.relative_to(world_dir).as_posix()
            files = []
            chunks = set()
            for region in sorted(p.glob("r.*.*.mca")):
                coords = region_chunk_coordinates(region)
                chunks.update((x, z) for x, z in coords)
                files.append({
                    "path": region.relative_to(world_dir).as_posix(),
                    "sha256": sha256(region),
                    "chunk_count": len(coords),
                })
            all_regions.append({
                "path": rel,
                "chunk_count": len(chunks),
                "chunks": [[x, z] for x, z in sorted(chunks)],
                "files": files,
            })

    explicit = [
        item for item in all_regions
        if "twilightforest" in item["path"].lower()
        and "twilight_forest" in item["path"].lower()
    ]
    vanilla_paths = {"region", "dim-1/region", "dim1/region"}
    non_vanilla = [
        item for item in all_regions
        if item["path"].lower() not in vanilla_paths
    ]

    selected = None
    classification = None
    if len(explicit) == 1:
        selected = explicit[0]
        classification = "namespace_path"
    elif len(explicit) > 1:
        classification = "ambiguous_namespace_paths"
    elif len(non_vanilla) == 1:
        selected = non_vanilla[0]
        classification = "single_non_vanilla_region_dir"
    elif len(non_vanilla) > 1:
        classification = "ambiguous_non_vanilla_region_dirs"
    else:
        classification = "no_custom_region_dir_found"

    return {
        "classification": classification,
        "selected_region_dir": selected["path"] if selected else None,
        "all_region_dirs": all_regions,
        "saved_chunk_count": selected["chunk_count"] if selected else None,
        "saved_chunks": selected["chunks"] if selected else [],
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


def build_rcon_packet(request_id, packet_type, payload):
    encoded = payload.encode("utf-8")
    body = struct.pack("<ii", request_id, packet_type) + encoded + b"\x00\x00"
    return struct.pack("<i", len(body)) + body


def recv_exact(sock, length):
    chunks = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("RCON socket closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_rcon_packet(sock):
    length = struct.unpack("<i", recv_exact(sock, 4))[0]
    if length < 10 or length > 1024 * 1024:
        raise ValueError(f"invalid RCON packet length: {length}")
    body = recv_exact(sock, length)
    request_id, packet_type = struct.unpack("<ii", body[:8])
    payload = body[8:-2].decode("utf-8", errors="replace")
    return request_id, packet_type, payload


class RconClient:
    def __init__(self, sock):
        self.sock = sock
        self.next_id = 100

    @classmethod
    def connect(cls, host, port, password, socket_timeout=15.0):
        sock = socket.create_connection((host, port), timeout=socket_timeout)
        sock.settimeout(socket_timeout)
        client = cls(sock)
        auth_id = 99
        sock.sendall(build_rcon_packet(auth_id, 3, password))
        for _ in range(3):
            request_id, packet_type, payload = recv_rcon_packet(sock)
            if request_id == -1:
                sock.close()
                raise PermissionError("RCON authentication failed")
            if request_id == auth_id and packet_type == 2:
                return client
        sock.close()
        raise RuntimeError("RCON authentication response not observed")

    def command(self, command):
        request_id = self.next_id
        self.next_id += 1
        self.sock.sendall(build_rcon_packet(request_id, 2, command))
        for _ in range(4):
            response_id, packet_type, payload = recv_rcon_packet(self.sock)
            if response_id == request_id:
                return payload
        raise RuntimeError("RCON response id mismatch")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def connect_rcon_with_retry(host, port, password, timeout_seconds, transcript):
    deadline = time.perf_counter() + timeout_seconds
    last_error = None
    while time.perf_counter() < deadline:
        try:
            client = RconClient.connect(host, port, password)
            transcript.append({"stage": "rcon_connect", "ok": True, "at_utc": utc_now()})
            return client
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(1)
    transcript.append({
        "stage": "rcon_connect",
        "ok": False,
        "at_utc": utc_now(),
        "error": last_error,
    })
    raise TimeoutError(f"RCON connection not established within {timeout_seconds}s: {last_error}")


def run_rcon_command(client, transcript, stage, command):
    started = time.perf_counter()
    response = client.command(command)
    transcript.append({
        "stage": stage,
        "command": command,
        "response": response,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    })
    return response


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
    ap.add_argument("--control-timeout-seconds", type=int, default=120)
    ap.add_argument("--entry-timeout-seconds", type=int, default=1800)
    ap.add_argument("--shutdown-seconds", type=int, default=90)
    ap.add_argument("--rcon-port", type=int, default=RCON_DEFAULT_PORT)
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
            "server-ip=127.0.0.1",
            "online-mode=false",
            "enable-query=false",
            "enable-rcon=true",
            f"rcon.port={args.rcon_port}",
            f"rcon.password={RCON_PASSWORD}",
            "broadcast-rcon-to-ops=false",
            "spawn-protection=0",
            "difficulty=peaceful",
            "motd=Twilight Forest Runtime Evidence R2",
            "",
        ]),
        encoding="utf-8",
    )

    java = capture(["java", "-version"])
    environment = {
        "record_version": "1.1",
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
        "control": {
            "transport": "localhost_rcon",
            "host": "127.0.0.1",
            "port": args.rcon_port,
            "password_committed": False,
            "control_timeout_seconds": args.control_timeout_seconds,
        },
        "profiler": {
            "tool": "vanilla debug command when available",
            "allocation_profiler": None,
            "allocation_note": "R2 does not claim allocation bytes without an unambiguous allocation profiler.",
        },
    }
    scenario = {
        "record_version": "1.1",
        "scenario_id": "R2",
        "name": "first_twilight_dimension_entry",
        "mode": "headless dedicated-server portal fixture",
        "track": args.track,
        "startup_timeout_seconds": args.startup_timeout_seconds,
        "control_timeout_seconds": args.control_timeout_seconds,
        "entry_timeout_seconds": args.entry_timeout_seconds,
        "shutdown_seconds": args.shutdown_seconds,
        "world_seed": args.world_seed,
        "source_portal_origin": [8, 160, 8],
        "source_portal_size": [2, 1, 2],
        "probe_entity": "minecraft:pig",
        "probe_entity_tag": "kneekura_r2_probe",
        "destination_dimension": TWILIGHT_DIMENSION,
        "fixture_commands": build_portal_fixture_commands(),
        "fixture_verify_command": fixture_verify_command(),
        "control_transport": "localhost_rcon",
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
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    q = queue.Queue()
    threading.Thread(target=reader, args=(proc.stdout, q), daemon=True).start()

    transcript = []
    rcon = None
    startup_ready_elapsed = None
    rcon_connected_elapsed = None
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
    startup_timed_out = False
    control_timed_out = False
    entry_timed_out = False
    failure_stage = None
    failure_reason = None
    stop_sent = False
    shutdown = "process_exit"
    output_closed = False
    log_path = logs / "console.log"

    def observe_line(line, elapsed):
        nonlocal destination_prepare_start, destination_portal_ready, debug_summary
        if trigger_perf is not None:
            trigger_elapsed = max(0.0, time.perf_counter() - trigger_perf)
            if destination_prepare_start is None and prepare_start_re.search(line):
                destination_prepare_start = trigger_elapsed
            if destination_portal_ready is None and portal_ready_re.search(line):
                destination_portal_ready = trigger_elapsed
            warning = parse_keepup_warning(line)
            if warning:
                warning["elapsed_seconds"] = round(trigger_elapsed, 6)
                keepup_warnings.append(warning)
            if len(structure_markers) < 100 and re.search(
                r"(twilightforest.*(?:structure|landmark)|(?:structure|landmark).*twilightforest)",
                line,
                re.I,
            ):
                structure_markers.append({
                    "elapsed_seconds": round(trigger_elapsed, 6),
                    "line": line.strip()[:1000],
                })
        if debug_summary is None:
            parsed = parse_debug_summary(line)
            if parsed:
                debug_summary = parsed

    def drain_logs(log, block_timeout=0.0):
        nonlocal output_closed
        first = True
        while True:
            try:
                line = q.get(timeout=block_timeout if first else 0)
            except queue.Empty:
                return
            first = False
            if line is None:
                output_closed = True
                return
            elapsed = time.perf_counter() - process_start
            log.write(f"[+{elapsed:.3f}s] {line}")
            log.flush()
            observe_line(line, elapsed)

    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        # Stage 1: dedicated server ready.
        while startup_ready_elapsed is None:
            elapsed = time.perf_counter() - process_start
            if elapsed > args.startup_timeout_seconds:
                startup_timed_out = True
                failure_stage = "startup"
                failure_reason = f"server ready not observed within {args.startup_timeout_seconds}s"
                shutdown = kill_tree(proc)
                break
            if proc.poll() is not None:
                failure_stage = "startup"
                failure_reason = f"server process exited before ready with code {proc.returncode}"
                break
            try:
                line = q.get(timeout=0.25)
            except queue.Empty:
                continue
            if line is None:
                output_closed = True
                continue
            log.write(f"[+{elapsed:.3f}s] {line}")
            log.flush()
            observe_line(line, elapsed)
            if ready_re.search(line):
                startup_ready_elapsed = elapsed

        # Stage 2: establish localhost RCON.
        if startup_ready_elapsed is not None and failure_stage is None:
            try:
                rcon = connect_rcon_with_retry(
                    "127.0.0.1",
                    args.rcon_port,
                    RCON_PASSWORD,
                    args.control_timeout_seconds,
                    transcript,
                )
                rcon_connected_elapsed = time.perf_counter() - process_start
            except Exception as exc:
                control_timed_out = isinstance(exc, TimeoutError)
                failure_stage = "rcon_connect"
                failure_reason = f"{type(exc).__name__}: {exc}"

        # Stage 3: construct and verify fixture.
        if rcon is not None and failure_stage is None:
            deadline = time.perf_counter() + args.control_timeout_seconds
            try:
                for command_text in build_portal_fixture_commands():
                    if time.perf_counter() > deadline:
                        raise TimeoutError("fixture setup deadline exceeded")
                    run_rcon_command(rcon, transcript, "fixture", command_text)
                    drain_logs(log)
                verify = run_rcon_command(rcon, transcript, "fixture_verify", fixture_verify_command())
                if "seed" not in verify.lower():
                    raise RuntimeError(f"fixture verification did not return seed: {verify!r}")
                fixture_ready_elapsed = time.perf_counter() - process_start
            except Exception as exc:
                control_timed_out = isinstance(exc, TimeoutError)
                failure_stage = "fixture"
                failure_reason = f"{type(exc).__name__}: {exc}"

        # Stage 4: start profiler and trigger real portal entry.
        if rcon is not None and failure_stage is None:
            try:
                debug_response = run_rcon_command(rcon, transcript, "debug_start", "debug start")
                debug_ready_elapsed = time.perf_counter() - process_start
                trigger_perf = time.perf_counter()
                run_rcon_command(rcon, transcript, "entry_trigger", summon_probe_command())
                transcript.append({"stage": "debug_start_response", "response": debug_response})
                time.sleep(0.05)
            except Exception as exc:
                failure_stage = "debug_or_trigger"
                failure_reason = f"{type(exc).__name__}: {exc}"

        # Stage 5: poll actual entity presence in the Twilight dimension.
        if rcon is not None and trigger_perf is not None and failure_stage is None:
            deadline = trigger_perf + args.entry_timeout_seconds
            while arrival_elapsed is None:
                if time.perf_counter() > deadline:
                    entry_timed_out = True
                    failure_stage = "entry"
                    failure_reason = f"Twilight arrival not observed within {args.entry_timeout_seconds}s"
                    break
                if proc.poll() is not None:
                    failure_stage = "entry"
                    failure_reason = f"server process exited during entry with code {proc.returncode}"
                    break
                drain_logs(log)
                try:
                    response = run_rcon_command(rcon, transcript, "arrival_poll", arrival_poll_command())
                except Exception as exc:
                    failure_stage = "arrival_poll"
                    failure_reason = f"{type(exc).__name__}: {exc}"
                    break
                pos = parse_position(response)
                if pos is not None:
                    origin_response = run_rcon_command(
                        rcon, transcript, "origin_absence_poll", origin_poll_command()
                    )
                    origin_pos = parse_position(origin_response)
                    if origin_pos is not None:
                        failure_stage = "arrival_verification"
                        failure_reason = (
                            "probe selector resolved in both Twilight and Overworld; "
                            "dimension-scoped arrival could not be proven"
                        )
                        break
                    arrival_elapsed = time.perf_counter() - trigger_perf
                    arrival_position = pos
                    arrival_position_raw = response[:1000]
                    break
                time.sleep(0.5)

        # Stage 6: collect profiler/save evidence and stop.
        if rcon is not None and arrival_elapsed is not None:
            try:
                response = run_rcon_command(rcon, transcript, "debug_stop", "debug stop")
                parsed = parse_debug_summary(response)
                if parsed:
                    debug_summary = parsed
            except Exception as exc:
                transcript.append({"stage": "debug_stop", "error": f"{type(exc).__name__}: {exc}"})
            try:
                run_rcon_command(rcon, transcript, "save", "save-all flush")
            except Exception as exc:
                transcript.append({"stage": "save", "error": f"{type(exc).__name__}: {exc}"})
            try:
                run_rcon_command(rcon, transcript, "cleanup", kill_probe_command())
            except Exception as exc:
                transcript.append({"stage": "cleanup", "error": f"{type(exc).__name__}: {exc}"})
            try:
                run_rcon_command(rcon, transcript, "shutdown", "stop")
                stop_sent = True
                shutdown = "rcon_stop_command"
            except Exception as exc:
                # Minecraft may close RCON before replying to stop.
                transcript.append({"stage": "shutdown", "error": f"{type(exc).__name__}: {exc}"})
                stop_sent = True
                shutdown = "rcon_stop_disconnect"

        # Any failed stage still gets bounded shutdown.
        if failure_stage is not None and proc.poll() is None:
            if rcon is not None:
                try:
                    run_rcon_command(rcon, transcript, "failure_shutdown", "stop")
                    stop_sent = True
                    shutdown = "rcon_stop_after_failure"
                except Exception as exc:
                    transcript.append({"stage": "failure_shutdown", "error": f"{type(exc).__name__}: {exc}"})
            deadline = time.perf_counter() + min(args.shutdown_seconds, 30)
            while proc.poll() is None and time.perf_counter() < deadline:
                drain_logs(log, 0.25)
            if proc.poll() is None:
                shutdown = kill_tree(proc)

        # Successful stop is also bounded.
        if arrival_elapsed is not None and proc.poll() is None:
            deadline = time.perf_counter() + args.shutdown_seconds
            while proc.poll() is None and time.perf_counter() < deadline:
                drain_logs(log, 0.25)
            if proc.poll() is None:
                shutdown = kill_tree(proc)

        if rcon is not None:
            rcon.close()
        try:
            exit_code = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            shutdown = kill_tree(proc)
            exit_code = proc.wait(timeout=5)

        # Drain remaining process output after exit/kill.
        for _ in range(10000):
            if output_closed:
                break
            before = output_closed
            drain_logs(log, 0.01)
            if output_closed or before == output_closed and q.empty():
                break

    total = time.perf_counter() - process_start
    transcript_path = logs / "rcon-transcript.json"
    transcript_path.write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
    profiler_files = copy_profiler_files(run_dir, profiler)
    world_inspection = inspect_twilight_regions(world_dir)
    world_inspection_path = out / "world-inspection.json"
    world_inspection_path.write_text(json.dumps(world_inspection, indent=2) + "\n", encoding="utf-8")

    max_warning = max(keepup_warnings, key=lambda x: x["delay_ms"]) if keepup_warnings else None
    success = arrival_elapsed is not None and failure_stage is None
    destination_prepare_elapsed = None
    if destination_prepare_start is not None and destination_portal_ready is not None:
        destination_prepare_elapsed = max(0.0, destination_portal_ready - destination_prepare_start)

    metrics = {
        "record_version": "1.1",
        "scenario_id": "R2",
        "track": args.track,
        "process_start_utc": start_wall,
        "startup_ready_elapsed_seconds": round(startup_ready_elapsed, 6) if startup_ready_elapsed is not None else None,
        "rcon_connected_elapsed_seconds": round(rcon_connected_elapsed, 6) if rcon_connected_elapsed is not None else None,
        "fixture_ready_elapsed_seconds": round(fixture_ready_elapsed, 6) if fixture_ready_elapsed is not None else None,
        "debug_ready_elapsed_seconds": round(debug_ready_elapsed, 6) if debug_ready_elapsed is not None else None,
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
        "control_timed_out": control_timed_out,
        "entry_timed_out": entry_timed_out,
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
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
        f"- failure stage: **{failure_stage or 'none'}**",
        f"- failure reason: **{failure_reason or 'none'}**",
        f"- saved Twilight chunks after entry: **{world_inspection['saved_chunk_count'] if world_inspection['saved_chunk_count'] is not None else 'unresolved'}**",
        f"- tick-spike warnings: **{len(keepup_warnings)}**",
        f"- process exit code: {exit_code}",
        f"- shutdown: {shutdown}",
        f"- raw console SHA-256: {sha256(log_path)}",
        f"- RCON transcript SHA-256: {sha256(transcript_path)}",
        "",
        "R2 measures one deterministic headless first-entry fixture only. It does not establish R3-R9 results or an overall ANCHOR-vs-FRONTIER performance ranking.",
        "",
    ])
    (out / "evidence-summary.md").write_text(summary, encoding="utf-8")

    manifest = {
        "record_version": "1.1",
        "scenario_id": "R2",
        "track": args.track,
        "raw_artifacts": {
            "logs/console.log": {"sha256": sha256(log_path), "committed": False},
            "logs/rcon-transcript.json": {"sha256": sha256(transcript_path), "committed": False},
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
#!/usr/bin/env python3
"""Compare one Warfare Wings microkernel trace against one real Minecraft runtime trace.

The comparator is intentionally threshold-free at this stage. It measures drift and phase
differences without converting them into PASS/FAIL until repeated same-artifact runtime variance
has been measured.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable

TRACE_VERSION = "ww.physics.trace.v1"
CALIBRATION_VERSION = "ww.physics.calibration.v1"
AI_VIEW_VERSION = "ww.physics.ai-view.v1"

COLUMNS = [
    "schema_version", "source", "scenario_id", "aircraft_id", "tick", "game_time",
    "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
    "speed_bps", "horizontal_speed_bps", "yaw_deg", "pitch_deg", "roll_deg",
    "engine_target", "engine_power", "fuel_utilization",
    "raw_x", "raw_y", "raw_z", "smooth_x", "smooth_y", "smooth_z",
]

NUMERIC = [
    "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
    "speed_bps", "horizontal_speed_bps", "yaw_deg", "pitch_deg", "roll_deg",
    "engine_target", "engine_power", "fuel_utilization",
    "raw_x", "raw_y", "raw_z", "smooth_x", "smooth_y", "smooth_z",
]

CHECKPOINT_TICKS = (20, 100, 200, 400)


def _finite(value: str, field: str, tick: int) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"tick {tick}: {field} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"tick {tick}: {field} is not finite")
    return number


def load_trace(path: Path, expected_source: str) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path}: trace header mismatch")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: empty trace")

    scenario = rows[0]["scenario_id"]
    aircraft = rows[0]["aircraft_id"]
    parsed = []
    for index, row in enumerate(rows):
        if row["schema_version"] != TRACE_VERSION:
            raise ValueError(f"{path}: unsupported schema {row['schema_version']}")
        if row["source"] != expected_source:
            raise ValueError(f"{path}: expected source={expected_source}, got {row['source']}")
        if row["scenario_id"] != scenario or row["aircraft_id"] != aircraft:
            raise ValueError(f"{path}: mixed scenario or aircraft identities")
        tick = int(row["tick"])
        if tick != index:
            raise ValueError(f"{path}: expected contiguous tick {index}, got {tick}")
        item = dict(row)
        item["tick"] = tick
        item["game_time"] = None if row["game_time"] == "" else int(row["game_time"])
        for field in NUMERIC:
            item[field] = _finite(row[field], field, tick)
        parsed.append(item)
    return parsed


def _wrapped_abs(a: float, b: float) -> float:
    value = (a - b + 180.0) % 360.0 - 180.0
    return abs(value)


def _norm3(ax: float, ay: float, az: float) -> float:
    return math.sqrt(ax * ax + ay * ay + az * az)


def _stats(values: list[float], ticks: list[int]) -> dict:
    if not values:
        raise ValueError("metric has no samples")
    checkpoints = {
        str(tick): values[ticks.index(tick)]
        for tick in CHECKPOINT_TICKS
        if tick in ticks
    }
    return {
        "rmse": math.sqrt(sum(v * v for v in values) / len(values)),
        "mean_abs": sum(abs(v) for v in values) / len(values),
        "max_abs": max(abs(v) for v in values),
        "max_abs_tick": ticks[max(range(len(values)), key=lambda i: abs(values[i]))],
        "final_abs": abs(values[-1]),
        "checkpoints": checkpoints,
    }


def _first_tick(rows: list[dict], field: str, threshold: float) -> int | None:
    for row in rows:
        if row[field] >= threshold:
            return row["tick"]
    return None


def _phase_events(micro: list[dict], runtime: list[dict]) -> dict:
    def pair(field: str, threshold: float) -> dict:
        a = _first_tick(micro, field, threshold)
        b = _first_tick(runtime, field, threshold)
        return {
            "microkernel_tick": a,
            "runtime_tick": b,
            "delta_ticks": None if a is None or b is None else b - a,
        }

    micro_final_speed = micro[-1]["speed_bps"]
    runtime_final_speed = runtime[-1]["speed_bps"]
    return {
        "engine_power_50pct": pair("engine_power", 0.50),
        "engine_power_90pct": pair("engine_power", 0.90),
        "speed_90pct_of_own_final": {
            "microkernel_tick": _first_tick(micro, "speed_bps", micro_final_speed * 0.90),
            "runtime_tick": _first_tick(runtime, "speed_bps", runtime_final_speed * 0.90),
        },
        "peak_speed": {
            "microkernel_bps": max(row["speed_bps"] for row in micro),
            "microkernel_tick": max(micro, key=lambda row: row["speed_bps"])["tick"],
            "runtime_bps": max(row["speed_bps"] for row in runtime),
            "runtime_tick": max(runtime, key=lambda row: row["speed_bps"])["tick"],
        },
    }


def compare(micro_path: Path, runtime_path: Path, output_dir: Path, runtime_metadata: Path | None = None) -> dict:
    micro = load_trace(micro_path, "microkernel")
    runtime = load_trace(runtime_path, "minecraft_runtime")
    if len(micro) != len(runtime):
        raise ValueError(f"sample count mismatch: {len(micro)} vs {len(runtime)}")
    if micro[0]["scenario_id"] != runtime[0]["scenario_id"]:
        raise ValueError("scenario mismatch")
    if micro[0]["aircraft_id"] != runtime[0]["aircraft_id"]:
        raise ValueError("aircraft mismatch")

    output_dir.mkdir(parents=True, exist_ok=True)
    ticks = [row["tick"] for row in micro]

    metric_series: dict[str, list[float]] = {
        "position_error_blocks": [],
        "velocity_error_bpt": [],
        "speed_error_bps": [],
        "horizontal_speed_error_bps": [],
        "yaw_error_deg": [],
        "pitch_error_deg": [],
        "roll_error_deg": [],
        "engine_target_error": [],
        "engine_power_error": [],
        "fuel_utilization_error": [],
        "smooth_x_error": [],
        "smooth_y_error": [],
        "smooth_z_error": [],
    }

    diff_rows = []
    ai_series = []
    for a, b in zip(micro, runtime):
        if a["tick"] != b["tick"]:
            raise ValueError("tick mismatch")
        dx = b["pos_x"] - a["pos_x"]
        dy = b["pos_y"] - a["pos_y"]
        dz = b["pos_z"] - a["pos_z"]
        dvx = b["vel_x"] - a["vel_x"]
        dvy = b["vel_y"] - a["vel_y"]
        dvz = b["vel_z"] - a["vel_z"]

        errors = {
            "position_error_blocks": _norm3(dx, dy, dz),
            "velocity_error_bpt": _norm3(dvx, dvy, dvz),
            "speed_error_bps": abs(b["speed_bps"] - a["speed_bps"]),
            "horizontal_speed_error_bps": abs(b["horizontal_speed_bps"] - a["horizontal_speed_bps"]),
            "yaw_error_deg": _wrapped_abs(b["yaw_deg"], a["yaw_deg"]),
            "pitch_error_deg": _wrapped_abs(b["pitch_deg"], a["pitch_deg"]),
            "roll_error_deg": _wrapped_abs(b["roll_deg"], a["roll_deg"]),
            "engine_target_error": abs(b["engine_target"] - a["engine_target"]),
            "engine_power_error": abs(b["engine_power"] - a["engine_power"]),
            "fuel_utilization_error": abs(b["fuel_utilization"] - a["fuel_utilization"]),
            "smooth_x_error": abs(b["smooth_x"] - a["smooth_x"]),
            "smooth_y_error": abs(b["smooth_y"] - a["smooth_y"]),
            "smooth_z_error": abs(b["smooth_z"] - a["smooth_z"]),
        }
        for name, value in errors.items():
            metric_series[name].append(value)

        diff_rows.append({
            "tick": a["tick"],
            "time_s": a["tick"] / 20.0,
            "runtime_game_time": "" if b["game_time"] is None else b["game_time"],
            **errors,
            "micro_speed_bps": a["speed_bps"],
            "runtime_speed_bps": b["speed_bps"],
            "micro_engine_power": a["engine_power"],
            "runtime_engine_power": b["engine_power"],
            "micro_pos_x": a["pos_x"],
            "micro_pos_y": a["pos_y"],
            "micro_pos_z": a["pos_z"],
            "runtime_pos_x": b["pos_x"],
            "runtime_pos_y": b["pos_y"],
            "runtime_pos_z": b["pos_z"],
        })
        ai_series.append({
            "tick": a["tick"],
            "time_s": a["tick"] / 20.0,
            "micro_speed_bps": a["speed_bps"],
            "runtime_speed_bps": b["speed_bps"],
            "micro_engine_power": a["engine_power"],
            "runtime_engine_power": b["engine_power"],
            "position_error_blocks": errors["position_error_blocks"],
            "velocity_error_bpt": errors["velocity_error_bpt"],
            "speed_error_bps": errors["speed_error_bps"],
            "yaw_error_deg": errors["yaw_error_deg"],
            "pitch_error_deg": errors["pitch_error_deg"],
        })

    metrics = {name: _stats(values, ticks) for name, values in metric_series.items()}
    metadata = None
    if runtime_metadata is not None:
        metadata = json.loads(runtime_metadata.read_text(encoding="utf-8"))

    summary = {
        "schema_version": CALIBRATION_VERSION,
        "status": "CALIBRATION_ONLY_NO_ACCEPTANCE_THRESHOLD",
        "scenario_id": micro[0]["scenario_id"],
        "aircraft_id": micro[0]["aircraft_id"],
        "samples": len(micro),
        "tick_rate_hz": 20,
        "microkernel_trace": str(micro_path),
        "runtime_trace": str(runtime_path),
        "runtime_metadata": metadata,
        "metrics": metrics,
        "phase_events": _phase_events(micro, runtime),
        "boundaries": [
            "No PASS/FAIL physics threshold is assigned until repeated same-artifact runtime variance is measured.",
            "Comparator equality proves trace agreement only for this scenario and sampled fields.",
            "Causal attribution still requires source/runtime evidence; the comparator reports drift, not its cause.",
        ],
    }

    diff_path = output_dir / "calibration-diff.csv"
    with diff_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(diff_rows[0].keys()))
        writer.writeheader()
        writer.writerows(diff_rows)

    (output_dir / "calibration-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ai_view = {
        "schema_version": AI_VIEW_VERSION,
        "scenario_id": summary["scenario_id"],
        "aircraft_id": summary["aircraft_id"],
        "status": summary["status"],
        "metric_summary": metrics,
        "phase_events": summary["phase_events"],
        "series": ai_series,
    }
    (output_dir / "calibration-ai-view.json").write_text(
        json.dumps(ai_view, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "calibration-summary.md").write_text(_markdown(summary), encoding="utf-8")
    return summary


def _markdown(summary: dict) -> str:
    def row(name: str, label: str, unit: str) -> str:
        m = summary["metrics"][name]
        return f"| {label} | {m['rmse']:.6f} | {m['max_abs']:.6f} @ t={m['max_abs_tick']} | {m['final_abs']:.6f} | {unit} |"

    lines = [
        f"# Calibration — {summary['aircraft_id']} / {summary['scenario_id']}",
        "",
        f"Status: **{summary['status']}**",
        "",
        f"Samples: {summary['samples']} at {summary['tick_rate_hz']} Hz.",
        "",
        "## Drift summary",
        "",
        "| Metric | RMSE | Maximum | Final | Unit |",
        "|---|---:|---:|---:|---|",
        row("position_error_blocks", "Position", "blocks"),
        row("velocity_error_bpt", "Velocity vector", "blocks/tick"),
        row("speed_error_bps", "Total speed", "blocks/s"),
        row("horizontal_speed_error_bps", "Horizontal speed", "blocks/s"),
        row("yaw_error_deg", "Yaw", "degrees"),
        row("pitch_error_deg", "Pitch", "degrees"),
        row("engine_power_error", "Engine power", "normalized"),
        "",
        "## Checkpoints",
        "",
        "| Tick | Time | Position error | Speed error | Engine-power error |",
        "|---:|---:|---:|---:|---:|",
    ]
    for tick in CHECKPOINT_TICKS:
        p = summary["metrics"]["position_error_blocks"]["checkpoints"].get(str(tick))
        s = summary["metrics"]["speed_error_bps"]["checkpoints"].get(str(tick))
        e = summary["metrics"]["engine_power_error"]["checkpoints"].get(str(tick))
        if p is not None:
            lines.append(f"| {tick} | {tick/20:.1f}s | {p:.6f} | {s:.6f} | {e:.6f} |")

    lines += ["", "## Phase events", ""]
    for name, value in summary["phase_events"].items():
        lines.append(f"- **{name}**: `{json.dumps(value, ensure_ascii=False)}`")

    speed = summary["metrics"]["speed_error_bps"]
    engine = summary["metrics"]["engine_power_error"]
    position = summary["metrics"]["position_error_blocks"]
    lines += [
        "",
        "## AI reading hints",
        "",
        f"- Largest speed divergence: {speed['max_abs']:.6f} blocks/s at tick {speed['max_abs_tick']}.",
        f"- Largest engine-power divergence: {engine['max_abs']:.6f} at tick {engine['max_abs_tick']}.",
        f"- Final accumulated position drift: {position['final_abs']:.6f} blocks.",
        "- Use `calibration-ai-view.json` for full ordered time-series inspection or chart generation.",
        "- Do not tune constants solely to reduce one metric until the same-artifact runtime identity and repeated-run variance are established.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--microkernel", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-metadata", type=Path)
    args = parser.parse_args(argv)
    summary = compare(args.microkernel, args.runtime, args.output_dir, args.runtime_metadata)
    print(json.dumps({
        "status": summary["status"],
        "scenario_id": summary["scenario_id"],
        "aircraft_id": summary["aircraft_id"],
        "samples": summary["samples"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from compare_traces import COLUMNS, TRACE_VERSION, compare


def write_trace(path: Path, source: str, perturb: bool = False) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for tick in range(5):
            vel_z = 0.50 + tick * 0.05
            if perturb and tick == 2:
                vel_z += 0.10
            speed = vel_z * 20.0
            row = {
                "schema_version": TRACE_VERSION,
                "source": source,
                "scenario_id": "selftest",
                "aircraft_id": "warfare_wings:a6m",
                "tick": tick,
                "game_time": "" if source == "microkernel" else 1000 + tick,
                "pos_x": 0.0,
                "pos_y": 200.0,
                "pos_z": tick * 0.5 + (0.1 if perturb and tick >= 2 else 0.0),
                "vel_x": 0.0,
                "vel_y": 0.0,
                "vel_z": vel_z,
                "speed_bps": speed,
                "horizontal_speed_bps": speed,
                "yaw_deg": 0.0,
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "engine_target": 1.0,
                "engine_power": tick / 4.0,
                "fuel_utilization": 1.0,
                "raw_x": 0.0,
                "raw_y": 0.0,
                "raw_z": 0.0,
                "smooth_x": 0.0,
                "smooth_y": 0.0,
                "smooth_z": 0.0,
            }
            writer.writerow(row)


def require(value: bool, detail: str) -> None:
    if not value:
        raise AssertionError(detail)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ww-trace-compare-") as td:
        root = Path(td)
        micro = root / "micro.csv"
        runtime = root / "runtime.csv"
        out = root / "out"

        write_trace(micro, "microkernel")
        write_trace(runtime, "minecraft_runtime")
        zero = compare(micro, runtime, out)
        require(zero["metrics"]["position_error_blocks"]["rmse"] == 0.0, "zero position")
        require(zero["metrics"]["speed_error_bps"]["max_abs"] == 0.0, "zero speed")
        require(zero["phase_events"]["engine_power_50pct"]["delta_ticks"] == 0, "zero engine phase")
        ai = json.loads((out / "calibration-ai-view.json").read_text(encoding="utf-8"))
        require(len(ai["series"]) == 5, "all samples retained")

        write_trace(runtime, "minecraft_runtime", perturb=True)
        drift = compare(micro, runtime, out)
        require(drift["metrics"]["position_error_blocks"]["max_abs"] > 0.0, "position drift detected")
        require(drift["metrics"]["velocity_error_bpt"]["max_abs"] > 0.0, "velocity drift detected")
        require(drift["metrics"]["speed_error_bps"]["max_abs"] > 0.0, "speed drift detected")
        require((out / "calibration-diff.csv").is_file(), "diff csv")
        require((out / "calibration-summary.md").is_file(), "summary markdown")

    print("Trace comparator self-test passed")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from compare_traces import COLUMNS, TRACE_VERSION, compare, load_trace


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

        # Reproduce actual owner-runner Windows PowerShell 5.1 UTF-8 BOM.
        metadata = root / "runtime-metadata.json"
        metadata.write_text('{"schema_version":"ww.physics.runtime-metadata.v1",'
                            '"scenario_id":"selftest","aircraft_id":"warfare_wings:a6m"}',
                            encoding="utf-8-sig")
        with_bom = compare(micro, runtime, out, metadata)
        require(with_bom["runtime_metadata"]["schema_version"]
                == "ww.physics.runtime-metadata.v1",
                "owner-runner PowerShell BOM metadata accepted without schema drift")

        # Different GameTest template origins are not dynamical drift.
        with runtime.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            shifted = list(reader)
        for row in shifted:
            row["pos_x"] = str(float(row["pos_x"]) + 140)
            row["pos_y"] = str(float(row["pos_y"]) - 40)
        with runtime.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(shifted)
        shifted_cmp = compare(micro, runtime, out)
        require(shifted_cmp["metrics"]["position_error_blocks"]["rmse"] > 100,
                "raw world layout offset is not ignored")
        require(shifted_cmp["metrics"]["position_origin_aligned_drift_blocks"]["rmse"] < 0.2,
                "origin-aligned metric isolates real relative movement")

        # Simulate old observed 401-tick A6M case: world clock advanced but
        # aircraft position, velocity, yaw and engine froze outside loaded chunks.
        frozen = root / "frozen.csv"
        for row in shifted:
            row["scenario_id"] = "a6m-throttle-step-v1"
        for i in range(2, len(shifted)):
            for f in ("pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
                      "engine_power", "yaw_deg", "pitch_deg"):
                shifted[i][f] = shifted[1][f]
        with frozen.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(shifted)
        rejected = False
        try:
            load_trace(frozen, "minecraft_runtime")
        except ValueError as error:
            rejected = "NON_TICKING_REAL_AIRCRAFT" in str(error)
        require(rejected, "stale aircraft physics must fail closed despite server time advancing")

    print("Trace comparator self-test passed")


if __name__ == "__main__":
    main()
